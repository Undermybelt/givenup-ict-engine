#!/usr/bin/env python3
"""Isolated R6 direct Manipulation rehydration and split-gate readback.

This run deliberately does not mutate the shared
`/tmp/ict-engine-direct-manipulation-row-intake` root. It copies the durable
v55 73/73 snapshot into this run root, reruns the fail-closed verifier and the
split/sidecar gates, and records a fresh provider/downstream command readback.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
import shutil
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


RUN_ID = "20260512T000038-codex-r6-isolated-rehydration-split-readback-v1"
RUN_ID_WITH_TZ = "20260512T000038+0800-codex-r6-isolated-rehydration-split-readback-v1"
REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs" / RUN_ID
OUT = RUN_ROOT / "r6-isolated-rehydration-split-readback"
CHECKS = RUN_ROOT / "checks"
COMMAND_OUT = RUN_ROOT / "command-output"
INTAKE = OUT / "isolated-direct-intake"
STATE_DIR = Path("/tmp/ict-engine-board-a-r6-rehydration-chain-v1")
AUTOQUANT_STATE_DIR = Path("/tmp/ict-engine-board-a-r6-rehydration-autoquant-v1")
SHARED_INTAKE = Path("/tmp/ict-engine-direct-manipulation-row-intake")

BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"
BIN = REPO / "target/debug/ict-engine"
DIRECT_VERIFIER = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs"
    / "20260511T151950-codex-direct-manipulation-row-intake-manifest-v1"
    / "direct-manipulation-intake/direct_manipulation_row_intake_verifier_v1.py"
)
V55_SNAPSHOT = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs"
    / "20260511T234414-codex-r6-direct-intake-reconstruction-v55"
    / "r6-direct-intake-reconstruction-v55"
)
V55_POSITIVE = V55_SNAPSHOT / "positive_spoofing_layering_rows_v55.csv"
V55_NEGATIVE = V55_SNAPSHOT / "matched_negative_normal_activity_rows_v55.csv"
V55_JSON = V55_SNAPSHOT / "r6_direct_intake_reconstruction_v55.json"
V55_SPLIT = V55_SNAPSHOT / "r6_direct_intake_reconstruction_v55_split_metrics.csv"
CURRENT_CURSOR_ROOT = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs"
    / "20260511T235303-codex-r6-direct-intake-reconstruction-preflight-v1"
)
POST_THAKKAR_UNIQUE = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs"
    / "20260511T235253-codex-r6-post-thakkar-candidate-consolidation-v1"
    / "r6-post-thakkar-candidate-consolidation"
    / "r6_post_thakkar_unique_candidate_rows_v1.csv"
)
POST_THAKKAR_CONTROL = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs"
    / "20260511T235253-codex-r6-post-thakkar-candidate-consolidation-v1"
    / "r6-post-thakkar-candidate-consolidation"
    / "r6_post_thakkar_control_candidate_rows_v1.csv"
)
BROAD_NORMAL_CONTROLS = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs"
    / "20260511T222000-codex-r6-broad-normal-order-lifecycle-screen-v1"
    / "r6-broad-normal-order-lifecycle-screen"
    / "broad_normal_market_order_lifecycle_controls_v1.csv"
)

FIELDS = [
    "label",
    "source_report",
    "source_section",
    "trade_date",
    "symbol",
    "venue_or_market_center",
    "participant_type_code",
    "participant_identifier",
    "side",
    "earliest_order_received_time",
    "latest_order_received_time",
    "order_count",
    "total_order_quantity",
    "activity_description",
    "matched_negative_group_id",
    "session_bucket",
    "source_row_id",
]
MIN_SUPPORT = 50
MIN_WILSON = 0.95
Z_95 = 1.96
MISSING_DIRECT_SPECIES = [
    "quote_stuffing",
    "pinging",
    "bear_raid_or_painting_tape",
    "pump_dump_social_text_or_twitter",
    "independent_non_spoofing_direct_species",
]


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO))
    except ValueError:
        return str(path)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def board_current_run_root() -> Path | None:
    if not BOARD.exists():
        return None
    for line in BOARD.read_text(encoding="utf-8").splitlines():
        if not line.startswith("| current_run_root |"):
            continue
        parts = [part.strip() for part in line.strip().strip("|").split("|")]
        if len(parts) < 2:
            return None
        value = parts[1].strip("`")
        if not value:
            return None
        path = Path(value)
        return path if path.is_absolute() else REPO / path
    return None


def wilson_lcb(successes: int, total: int) -> float:
    if total <= 0:
        return 0.0
    p = successes / total
    z2 = Z_95 * Z_95
    denom = 1.0 + z2 / total
    centre = p + z2 / (2.0 * total)
    margin = Z_95 * math.sqrt((p * (1.0 - p) + z2 / (4.0 * total)) / total)
    return max(0.0, (centre - margin) / denom)


def normalize(value: str) -> str:
    return " ".join((value or "UNKNOWN").strip().split())


def group_rows(rows: list[dict[str, str]]) -> dict[str, list[dict[str, str]]]:
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[row.get("matched_negative_group_id", "")].append(row)
    return grouped


def chronological_split_ids(rows: list[dict[str, str]]) -> dict[str, str]:
    grouped = group_rows(rows)
    ordered = sorted(
        grouped,
        key=lambda gid: (
            min(row.get("trade_date", "9999-12-31") or "9999-12-31" for row in grouped[gid]),
            gid,
        ),
    )
    train_end = max(1, int(len(ordered) * 0.50))
    calibration_end = max(train_end + 1, int(len(ordered) * 0.75))
    result: dict[str, str] = {}
    for index, gid in enumerate(ordered):
        if index < train_end:
            role = "chronological_train"
        elif index < calibration_end:
            role = "chronological_calibration"
        else:
            role = "chronological_test"
        result[gid] = role
    return result


def split_metric(
    split_family: str,
    split_name: str,
    rows: list[dict[str, str]],
    required_support: int = MIN_SUPPORT,
) -> dict[str, Any]:
    positives = [row for row in rows if row["_class"] == "positive"]
    negatives = [row for row in rows if row["_class"] == "negative"]
    positive_lcb = wilson_lcb(len(positives), len(positives))
    negative_lcb = wilson_lcb(len(negatives), len(negatives))
    min_lcb = min(positive_lcb, negative_lcb)
    support_ok = len(positives) >= required_support and len(negatives) >= required_support
    wilson_ok = min_lcb >= MIN_WILSON
    return {
        "split_family": split_family,
        "split_name": split_name,
        "positive_support": len(positives),
        "negative_support": len(negatives),
        "positive_wilson95_lcb": round(positive_lcb, 12),
        "negative_wilson95_lcb": round(negative_lcb, 12),
        "min_wilson95_lcb": round(min_lcb, 12),
        "support_ok": support_ok,
        "wilson_ok": wilson_ok,
        "pass": support_ok and wilson_ok,
        "blocker": ";".join(
            item
            for item in [
                "support_below_50" if not support_ok else "",
                "wilson95_below_0.95" if not wilson_ok else "",
            ]
            if item
        )
        or "none",
    }


def compute_direct_metrics(positives: list[dict[str, str]], negatives: list[dict[str, str]]) -> list[dict[str, Any]]:
    combined: list[dict[str, str]] = []
    for row in positives:
        item = dict(row)
        item["_class"] = "positive"
        combined.append(item)
    for row in negatives:
        item = dict(row)
        item["_class"] = "negative"
        combined.append(item)

    metrics = [split_metric("pooled_all_source_rows", "all_rows", combined)]
    split_ids = chronological_split_ids(combined)
    for role in ["chronological_train", "chronological_calibration", "chronological_test"]:
        rows = [row for row in combined if split_ids.get(row.get("matched_negative_group_id", "")) == role]
        metrics.append(split_metric("chronological_group_split", role, rows))
    for symbol in sorted({normalize(row.get("symbol", "")) for row in combined}):
        metrics.append(
            split_metric(
                "heldout_symbol_exact",
                symbol,
                [row for row in combined if normalize(row.get("symbol", "")) == symbol],
            )
        )
    for venue in sorted({normalize(row.get("venue_or_market_center", "")) for row in combined}):
        metrics.append(
            split_metric(
                "heldout_venue_exact",
                venue,
                [row for row in combined if normalize(row.get("venue_or_market_center", "")) == venue],
            )
        )
    return metrics


def positive_chronological_metrics(positives: list[dict[str, str]]) -> list[dict[str, Any]]:
    groups = group_rows(positives)
    ordered = sorted(
        groups,
        key=lambda gid: (
            min(row.get("trade_date", "9999-12-31") or "9999-12-31" for row in groups[gid]),
            gid,
        ),
    )
    train_end = max(1, int(len(ordered) * 0.50))
    calibration_end = max(train_end + 1, int(len(ordered) * 0.75))
    buckets = {"chronological_train": [], "chronological_calibration": [], "chronological_test": []}
    for index, gid in enumerate(ordered):
        if index < train_end:
            role = "chronological_train"
        elif index < calibration_end:
            role = "chronological_calibration"
        else:
            role = "chronological_test"
        buckets[role].extend(groups[gid])
    metrics: list[dict[str, Any]] = []
    for role, rows in buckets.items():
        lcb = wilson_lcb(len(rows), len(rows))
        metrics.append(
            {
                "split": role,
                "positive_support": len(rows),
                "positive_wilson95_lcb": round(lcb, 12),
                "support_ok": len(rows) >= MIN_SUPPORT,
                "wilson_ok": lcb >= MIN_WILSON,
                "pass": len(rows) >= MIN_SUPPORT and lcb >= MIN_WILSON,
            }
        )
    return metrics


def run_command(name: str, args: list[str], timeout_seconds: int = 90) -> dict[str, Any]:
    COMMAND_OUT.mkdir(parents=True, exist_ok=True)
    try:
        proc = subprocess.run(
            args,
            cwd=REPO,
            text=True,
            capture_output=True,
            timeout=timeout_seconds,
            check=False,
        )
        stdout = proc.stdout
        stderr = proc.stderr
        returncode = proc.returncode
        timed_out = False
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout or ""
        stderr = (exc.stderr or "") + f"\nTIMEOUT after {timeout_seconds}s\n"
        returncode = 124
        timed_out = True
    stdout_path = COMMAND_OUT / f"{name}.stdout.txt"
    stderr_path = COMMAND_OUT / f"{name}.stderr.txt"
    exit_path = COMMAND_OUT / f"{name}.exit"
    stdout_path.write_text(stdout, encoding="utf-8")
    stderr_path.write_text(stderr, encoding="utf-8")
    exit_path.write_text(f"{returncode}\n", encoding="utf-8")
    try:
        parsed = json.loads(stdout)
    except json.JSONDecodeError:
        parsed = None
    return {
        "name": name,
        "cmd": " ".join(args),
        "returncode": returncode,
        "timed_out": timed_out,
        "stdout_path": rel(stdout_path),
        "stderr_path": rel(stderr_path),
        "exit_path": rel(exit_path),
        "parsed": parsed,
    }


def provider_summary(payload: dict[str, Any] | None, provider_id: str) -> dict[str, Any]:
    if not payload:
        return {"provider_id": provider_id, "observed": False, "ready": False, "status": "unparsed", "reason": ""}
    matches = [row for row in payload.get("providers", []) if row.get("provider_id") == provider_id]
    if not matches:
        return {"provider_id": provider_id, "observed": False, "ready": False, "status": "not_listed", "reason": ""}
    return {
        "provider_id": provider_id,
        "observed": True,
        "ready": any(bool(row.get("ready")) for row in matches),
        "domains": sorted({str(row.get("domain", "")) for row in matches}),
        "status": ";".join(sorted({str(row.get("status", "")) for row in matches})),
        "reason": ";".join(sorted({str(row.get("reason", "")) for row in matches})),
    }


def write_materialization_rows(
    unique_candidates: list[dict[str, str]],
    positives: list[dict[str, str]],
    negatives: list[dict[str, str]],
) -> list[dict[str, Any]]:
    positive_ids = {row.get("source_row_id", "") for row in positives}
    negative_groups = {row.get("matched_negative_group_id", "") for row in negatives}
    rows: list[dict[str, Any]] = []
    for row in unique_candidates:
        source_id = row.get("source_row_id", "")
        group_id = row.get("matched_negative_group_id", "")
        materialized = source_id in positive_ids
        rows.append(
            {
                "candidate_source": row.get("candidate_source", ""),
                "source_row_id": source_id,
                "matched_negative_group_id": group_id,
                "materialized_in_rehydrated_positive_snapshot": materialized,
                "matched_control_materialized_for_group": group_id in negative_groups,
                "candidate_row_status": row.get("candidate_row_status", ""),
            }
        )
    write_csv(
        OUT / "r6_isolated_rehydration_candidate_materialization_v1.csv",
        rows,
        [
            "candidate_source",
            "source_row_id",
            "matched_negative_group_id",
            "materialized_in_rehydrated_positive_snapshot",
            "matched_control_materialized_for_group",
            "candidate_row_status",
        ],
    )
    return rows


def main() -> int:
    for path in [OUT, CHECKS, COMMAND_OUT, INTAKE, STATE_DIR, AUTOQUANT_STATE_DIR]:
        path.mkdir(parents=True, exist_ok=True)

    board_hash_before = sha256(BOARD)
    active_board_run_root = board_current_run_root()
    shared_intake_exists_at_start = SHARED_INTAKE.exists()
    positive_target = INTAKE / "positive_spoofing_layering_rows.csv"
    negative_target = INTAKE / "matched_negative_normal_activity_rows.csv"
    provenance_target = INTAKE / "provenance_manifest.json"
    shutil.copyfile(V55_POSITIVE, positive_target)
    shutil.copyfile(V55_NEGATIVE, negative_target)

    positives = read_csv(positive_target)
    negatives = read_csv(negative_target)
    unique_candidates = read_csv(POST_THAKKAR_UNIQUE)
    control_candidates = read_csv(POST_THAKKAR_CONTROL)
    broad_controls = read_csv(BROAD_NORMAL_CONTROLS)

    candidate_materialization = write_materialization_rows(unique_candidates, positives, negatives)
    source_counts = Counter(row["candidate_source"] for row in candidate_materialization)
    materialized_counts = Counter(
        row["candidate_source"]
        for row in candidate_materialization
        if row["materialized_in_rehydrated_positive_snapshot"]
    )
    unresolved_counts = Counter(
        row["candidate_source"]
        for row in candidate_materialization
        if not row["materialized_in_rehydrated_positive_snapshot"]
    )

    provenance = {
        "artifact_type": "r6_isolated_rehydration_split_readback_v1",
        "run_id": RUN_ID_WITH_TZ,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "board_sha256_at_start": board_hash_before,
        "source_snapshot_paths": {
            "positive_rows": rel(V55_POSITIVE),
            "matched_negative_rows": rel(V55_NEGATIVE),
            "v55_json": rel(V55_JSON),
            "v55_split_metrics": rel(V55_SPLIT),
        },
        "source_snapshot_hashes": {
            "positive_rows": sha256(V55_POSITIVE),
            "matched_negative_rows": sha256(V55_NEGATIVE),
            "v55_json": sha256(V55_JSON),
            "v55_split_metrics": sha256(V55_SPLIT),
        },
        "current_cursor_root": rel(CURRENT_CURSOR_ROOT),
        "current_cursor_root_exists": CURRENT_CURSOR_ROOT.exists(),
        "board_current_run_root": rel(active_board_run_root) if active_board_run_root else "",
        "board_current_run_root_exists": bool(active_board_run_root and active_board_run_root.exists()),
        "shared_intake_root": str(SHARED_INTAKE),
        "shared_intake_exists_at_start": shared_intake_exists_at_start,
        "policy": "isolated rehydration only; does not mutate canonical shared /tmp intake",
        "post_thakkar_unique_candidate_rows": len(unique_candidates),
        "post_thakkar_control_candidate_rows": len(control_candidates),
    }
    write_json(provenance_target, provenance)

    direct_verifier_cmd = run_command(
        "direct_manipulation_row_intake_verifier_isolated",
        [sys.executable, str(DIRECT_VERIFIER), "--intake-root", str(INTAKE)],
    )
    direct_verifier = direct_verifier_cmd["parsed"] if isinstance(direct_verifier_cmd["parsed"], dict) else {}

    direct_metrics = compute_direct_metrics(positives, negatives)
    direct_metrics_path = OUT / "r6_isolated_rehydration_direct_split_metrics_v1.csv"
    write_csv(
        direct_metrics_path,
        direct_metrics,
        [
            "split_family",
            "split_name",
            "positive_support",
            "negative_support",
            "positive_wilson95_lcb",
            "negative_wilson95_lcb",
            "min_wilson95_lcb",
            "support_ok",
            "wilson_ok",
            "pass",
            "blocker",
        ],
    )

    broad_labels = sorted({row.get("label", "") for row in broad_controls})
    broad_source_gate = (
        len(broad_controls) >= MIN_SUPPORT
        and broad_labels == ["independent_broad_normal_order_lifecycle_control"]
        and all("ITCH" in row.get("source_report", "") for row in broad_controls)
    )
    positive_lcb = wilson_lcb(len(positives), len(positives))
    negative_lcb = wilson_lcb(len(negatives), len(negatives))
    broad_lcb = wilson_lcb(len(broad_controls), len(broad_controls))
    pooled_min_lcb = min(positive_lcb, negative_lcb)
    sidecar_min_lcb = min(positive_lcb, broad_lcb)
    positive_split_metrics = positive_chronological_metrics(positives)
    positive_split_gate = all(row["pass"] for row in positive_split_metrics)
    write_csv(
        OUT / "r6_isolated_rehydration_positive_sidecar_split_metrics_v1.csv",
        positive_split_metrics,
        ["split", "positive_support", "positive_wilson95_lcb", "support_ok", "wilson_ok", "pass"],
    )

    grouped = group_rows([dict(row, _class="positive") for row in positives] + [dict(row, _class="negative") for row in negatives])
    unmatched_groups = [
        gid
        for gid, rows in grouped.items()
        if not any(row.get("_class") == "positive" for row in rows)
        or not any(row.get("_class") == "negative" for row in rows)
    ]

    direct_split_gate = all(
        row["pass"]
        for row in direct_metrics
        if row["split_family"]
        in {"pooled_all_source_rows", "chronological_group_split", "heldout_symbol_exact", "heldout_venue_exact"}
    )
    direct_species_closed = False
    pooled_wilson_gate = (
        len(positives) >= MIN_SUPPORT
        and len(negatives) >= MIN_SUPPORT
        and pooled_min_lcb >= MIN_WILSON
    )
    sidecar_broad_normal_gate = (
        len(positives) >= MIN_SUPPORT
        and len(broad_controls) >= MIN_SUPPORT
        and sidecar_min_lcb >= MIN_WILSON
        and broad_source_gate
    )
    accepted_gate = (
        direct_verifier.get("status") == "schema_ready_unscored"
        and pooled_wilson_gate
        and direct_split_gate
        and sidecar_broad_normal_gate
        and positive_split_gate
        and direct_species_closed
        and not unmatched_groups
    )

    provider_commands: list[dict[str, Any]] = [
        run_command("provider_status_agent", [str(BIN), "provider-status", "--agent"]),
    ]
    for provider in ["ibkr", "tradingview_mcp", "yfinance", "kraken_public", "kraken_cli"]:
        provider_commands.append(
            run_command(
                f"provider_status_{provider}_agent",
                [str(BIN), "provider-status", "--provider", provider, "--agent"],
            )
        )
    provider_payload = provider_commands[0]["parsed"] if isinstance(provider_commands[0]["parsed"], dict) else None
    providers = [
        provider_summary(provider_payload, provider)
        for provider in ["ibkr", "tradingview_mcp", "yfinance", "kraken_public", "kraken_cli"]
    ]

    chain_commands = [
        run_command(
            "auto_quant_status",
            [str(BIN), "auto-quant-status", "--state-dir", str(AUTOQUANT_STATE_DIR), "--output-format", "json"],
        ),
        run_command(
            "analyze_live_nq_yfinance",
            [
                str(BIN),
                "analyze-live",
                "--symbol",
                "NQ",
                "--futures-symbol",
                "NQ=F",
                "--spot-symbol",
                "QQQ",
                "--options-symbol",
                "QQQ",
                "--options-volatility-proxy-symbol",
                "^VIX",
                "--futures-backend",
                "yfinance",
                "--aux-backend",
                "yfinance",
                "--state-dir",
                str(STATE_DIR),
                "--output-format",
                "json",
            ],
            timeout_seconds=150,
        ),
        run_command("pre_bayes_status", [str(BIN), "pre-bayes-status", "--symbol", "NQ", "--state-dir", str(STATE_DIR), "--refresh"]),
        run_command("policy_training_status", [str(BIN), "policy-training-status", "--symbol", "NQ", "--state-dir", str(STATE_DIR), "--output-format", "json"]),
        run_command("workflow_status_execution_candidate", [str(BIN), "workflow-status", "--symbol", "NQ", "--state-dir", str(STATE_DIR), "--phase", "execution-candidate", "--agent"]),
        run_command("export_structural_path_ranking_target", [str(BIN), "export-structural-path-ranking-target", "--symbol", "NQ", "--state-dir", str(STATE_DIR)]),
    ]
    commands = [direct_verifier_cmd] + provider_commands + chain_commands

    decision = "r6_isolated_rehydration_split_readback_v1=durable_v55_rehydrated_pooled95_pass_split_species_still_blocked"
    cursor_note = (
        "the active board cursor root was present during this readback"
        if active_board_run_root and active_board_run_root.exists()
        else "the active board cursor root was absent during this readback"
    )
    result = {
        "run_id": RUN_ID_WITH_TZ,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "board_sha256_at_start": board_hash_before,
        "decision": decision,
        "current_cursor_root_exists": CURRENT_CURSOR_ROOT.exists(),
        "board_current_run_root": rel(active_board_run_root) if active_board_run_root else "",
        "board_current_run_root_exists": bool(active_board_run_root and active_board_run_root.exists()),
        "shared_intake_exists_at_start": shared_intake_exists_at_start,
        "shared_intake_exists_at_end": SHARED_INTAKE.exists(),
        "current_cursor_root": rel(CURRENT_CURSOR_ROOT),
        "source_snapshot_root": rel(V55_SNAPSHOT),
        "isolated_intake_root": rel(INTAKE),
        "isolated_files": {
            "positive_rows": rel(positive_target),
            "matched_negative_rows": rel(negative_target),
            "provenance_manifest": rel(provenance_target),
        },
        "input_hashes": {
            "positive_rows": sha256(positive_target),
            "matched_negative_rows": sha256(negative_target),
            "provenance_manifest": sha256(provenance_target),
            "broad_normal_controls": sha256(BROAD_NORMAL_CONTROLS),
        },
        "direct_verifier": direct_verifier,
        "positive_rows": len(positives),
        "matched_negative_rows": len(negatives),
        "matched_group_count": direct_verifier.get("matched_group_count"),
        "broad_normal_sidecar_rows": len(broad_controls),
        "positive_wilson95_lcb": round(positive_lcb, 12),
        "matched_negative_wilson95_lcb": round(negative_lcb, 12),
        "pooled_min_wilson95_lcb": round(pooled_min_lcb, 12),
        "pooled_wilson_gate": pooled_wilson_gate,
        "broad_normal_wilson95_lcb": round(broad_lcb, 12),
        "sidecar_broad_normal_gate": sidecar_broad_normal_gate,
        "sidecar_broad_normal_min_wilson95_lcb": round(sidecar_min_lcb, 12),
        "direct_split_gate": direct_split_gate,
        "positive_chronological_split_gate": positive_split_gate,
        "direct_species_closed": direct_species_closed,
        "missing_direct_species": MISSING_DIRECT_SPECIES,
        "unmatched_group_count": len(unmatched_groups),
        "post_thakkar_unique_candidate_rows": len(unique_candidates),
        "post_thakkar_materialized_candidate_rows": sum(
            1 for row in candidate_materialization if row["materialized_in_rehydrated_positive_snapshot"]
        ),
        "post_thakkar_unmaterialized_candidate_rows": sum(
            1 for row in candidate_materialization if not row["materialized_in_rehydrated_positive_snapshot"]
        ),
        "post_thakkar_control_candidate_rows": len(control_candidates),
        "candidate_source_counts": dict(sorted(source_counts.items())),
        "candidate_materialized_counts": dict(sorted(materialized_counts.items())),
        "candidate_unresolved_counts": dict(sorted(unresolved_counts.items())),
        "providers": providers,
        "commands": [{key: value for key, value in row.items() if key != "parsed"} for row in commands],
        "chain_readback": {
            "auto_quant_status_exit": chain_commands[0]["returncode"],
            "analyze_live_nq_yfinance_exit": chain_commands[1]["returncode"],
            "pre_bayes_status_exit": chain_commands[2]["returncode"],
            "policy_training_status_exit": chain_commands[3]["returncode"],
            "workflow_status_execution_candidate_exit": chain_commands[4]["returncode"],
            "export_structural_path_ranking_target_exit": chain_commands[5]["returncode"],
        },
        "accepted_gate": accepted_gate,
        "accepted_rows_added": 0,
        "new_confidence_gate": False,
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "shared_intake_mutated": False,
        "external_requests_sent": True,
        "trade_usable": False,
        "blocker": (
            "The durable isolated v55 snapshot passes pooled Wilson95 and broad-normal sidecar Wilson95, "
            "but chronological/symbol/venue split gates and direct species coverage remain fail-closed; "
            f"{cursor_note}."
        ),
        "next_action": (
            "Materialize source-owned matched controls and split support for the unrehydrated sidecar positives, "
            "then rerun chronological/symbol/venue gates while keeping R5 blocked."
        ),
    }

    json_path = OUT / "r6_isolated_rehydration_split_readback_v1.json"
    report_path = OUT / "r6_isolated_rehydration_split_readback_v1.md"
    assertions_path = CHECKS / "r6_isolated_rehydration_split_readback_v1_assertions.out"
    write_json(json_path, result)

    lines = [
        "# R6 Isolated Rehydration Split Readback v1",
        "",
        f"- Run id: `{RUN_ID_WITH_TZ}`",
        f"- Decision: `{decision}`.",
        f"- Active board cursor root exists: `{str(bool(active_board_run_root and active_board_run_root.exists())).lower()}`.",
        f"- Referenced preflight root exists: `{str(CURRENT_CURSOR_ROOT.exists()).lower()}`.",
        f"- Isolated verifier status: `{direct_verifier.get('status', 'unparsed')}`.",
        f"- Durable rehydrated rows: positives `{len(positives)}`, matched controls `{len(negatives)}`, matched groups `{direct_verifier.get('matched_group_count')}`.",
        f"- Pooled Wilson95 min LCB: `{pooled_min_lcb:.12f}`; pooled gate `{str(pooled_wilson_gate).lower()}`.",
        f"- Broad-normal sidecar rows: `{len(broad_controls)}`; sidecar min LCB `{sidecar_min_lcb:.12f}`; sidecar gate `{str(sidecar_broad_normal_gate).lower()}`.",
        f"- Direct split gate: `{str(direct_split_gate).lower()}`; positive chronological split gate `{str(positive_split_gate).lower()}`; direct species closed `{str(direct_species_closed).lower()}`.",
        f"- Post-Thakkar candidates materialized in this snapshot: `{result['post_thakkar_materialized_candidate_rows']}/{len(unique_candidates)}`; controls listed in latest consolidation: `{len(control_candidates)}`.",
        "- Accepted rows added to shared intake: `0`; new confidence gate: `false`; strict full objective achieved: `false`; `update_goal=false`.",
        "- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; shared intake mutated: `false`; trade usable: `false`.",
        "",
        "## Provider / Chain Readback",
        "",
        "| Provider | Ready | Status | Reason |",
        "|---|---:|---|---|",
    ]
    for provider in providers:
        lines.append(f"| `{provider['provider_id']}` | `{str(provider['ready']).lower()}` | `{provider['status']}` | `{provider['reason']}` |")
    lines.extend(["", "| Command | Exit | Output | Error |", "|---|---:|---|---|"])
    for command in commands:
        lines.append(f"| `{command['name']}` | `{command['returncode']}` | `{command['stdout_path']}` | `{command['stderr_path']}` |")
    lines.extend(
        [
            "",
            "## Artifacts",
            "",
            f"- JSON: `{rel(json_path)}`",
            f"- Isolated positive rows: `{rel(positive_target)}`",
            f"- Isolated matched controls: `{rel(negative_target)}`",
            f"- Isolated provenance: `{rel(provenance_target)}`",
            f"- Direct split metrics: `{rel(direct_metrics_path)}`",
            f"- Candidate materialization: `{rel(OUT / 'r6_isolated_rehydration_candidate_materialization_v1.csv')}`",
            f"- Assertions: `{rel(assertions_path)}`",
            "",
            "## Next",
            result["next_action"],
        ]
    )
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    assertions = {
        "board_current_run_root_observed": active_board_run_root is not None,
        "isolated_verifier_schema_ready": direct_verifier.get("status") == "schema_ready_unscored",
        "pooled_wilson_gate_passed": pooled_wilson_gate,
        "sidecar_broad_normal_gate_passed": sidecar_broad_normal_gate,
        "direct_split_gate_fail_closed": not direct_split_gate,
        "direct_species_fail_closed": not direct_species_closed,
        "shared_intake_write_not_attempted": result["shared_intake_mutated"] is False,
        "strict_full_objective_not_complete": result["strict_full_objective_achieved"] is False,
        "update_goal_false": result["update_goal"] is False,
    }
    assertions_path.write_text(
        "\n".join(f"{name}={'ok' if passed else 'FAIL'}" for name, passed in assertions.items()) + "\n",
        encoding="utf-8",
    )
    if not all(assertions.values()):
        raise SystemExit(2)
    print(json.dumps({"decision": decision, "positive_rows": len(positives), "matched_negative_rows": len(negatives)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
