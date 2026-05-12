#!/usr/bin/env python3
"""Append control-complete JPMorgan CBOT Treasury rows to the live R6 intake.

This run uses the already-screened official CFTC JPMorgan order candidate rows.
It only promotes candidate pairs whose source ids are not present in the live
intake and whose symbols are CBOT Treasury contracts. The live root is mutated
only while holding the shared intake lock.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
import os
import shutil
import subprocess
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


RUN_ID = "20260512T000803-codex-r6-jpm-cbot-treasury-control-uplift-v1"
REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs" / RUN_ID
OUT = RUN_ROOT / "r6-jpm-cbot-treasury-control-uplift"
CMD_OUT = RUN_ROOT / "command-output"
CHECKS = RUN_ROOT / "checks"
BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"

LIVE_ROOT = Path("/tmp/ict-engine-direct-manipulation-row-intake")
LOCK_DIR = Path("/tmp/ict-engine-direct-manipulation-row-intake.lock")
STAGING_ROOT = Path(f"/tmp/{RUN_ID}.staging")

POSITIVE_NAME = "positive_spoofing_layering_rows.csv"
NEGATIVE_NAME = "matched_negative_normal_activity_rows.csv"
PROVENANCE_NAME = "provenance_manifest.json"

JPM_ROOT = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs"
    / "20260511T235048-codex-r6-jpmorgan-order-positive-row-candidate-screen-v1"
    / "r6-jpmorgan-order-positive-row-candidate-screen"
)
JPM_POSITIVE = JPM_ROOT / "r6_jpmorgan_order_positive_row_candidates_v1.csv"
JPM_NEGATIVE = JPM_ROOT / "r6_jpmorgan_order_matched_controls_v1.csv"
JPM_JSON = JPM_ROOT / "r6_jpmorgan_order_positive_row_candidate_screen_v1.json"
BASELINE_ROOT = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs"
    / "20260511T235815-codex-r6-live-intake-rehydrate-calibration-v1"
    / "r6-live-intake-rehydrate-calibration"
)
BASELINE_POSITIVE = BASELINE_ROOT / "positive_spoofing_layering_rows_v1.csv"
BASELINE_NEGATIVE = BASELINE_ROOT / "matched_negative_normal_activity_rows_v1.csv"
BASELINE_PROVENANCE = BASELINE_ROOT / "provenance_manifest_v1.json"

DIRECT_VERIFIER = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs"
    / "20260511T151950-codex-direct-manipulation-row-intake-manifest-v1"
    / "direct-manipulation-intake/direct_manipulation_row_intake_verifier_v1.py"
)
SIDECAR_CSV = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs"
    / "20260511T222000-codex-r6-broad-normal-order-lifecycle-screen-v1"
    / "r6-broad-normal-order-lifecycle-screen/broad_normal_market_order_lifecycle_controls_v1.csv"
)

MIN_SUPPORT = 50
MIN_WILSON = 0.95
Z_95 = 1.96


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


def safe_date(row: dict[str, str]) -> str:
    return row.get("trade_date") or "9999-12-31"


def grouped(rows: list[dict[str, str]]) -> dict[str, list[dict[str, str]]]:
    groups: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        groups[row.get("matched_negative_group_id", "")].append(row)
    return groups


def chronological_roles(positive_rows: list[dict[str, str]], negative_rows: list[dict[str, str]]) -> dict[str, str]:
    groups = grouped(positive_rows + negative_rows)
    ordered = sorted(groups, key=lambda gid: (min(safe_date(row) for row in groups[gid]), gid))
    total = len(ordered)
    train_end = max(1, int(total * 0.50))
    calibration_end = max(train_end + 1, int(total * 0.75))
    roles: dict[str, str] = {}
    for index, gid in enumerate(ordered):
        if index < train_end:
            roles[gid] = "chronological_train"
        elif index < calibration_end:
            roles[gid] = "chronological_calibration"
        else:
            roles[gid] = "chronological_test"
    return roles


def split_metric(split_family: str, split_name: str, rows: list[dict[str, str]]) -> dict[str, Any]:
    positives = [row for row in rows if row["_class"] == "positive"]
    negatives = [row for row in rows if row["_class"] == "negative"]
    pos_lcb = wilson_lcb(len(positives), len(positives))
    neg_lcb = wilson_lcb(len(negatives), len(negatives))
    min_lcb = min(pos_lcb, neg_lcb)
    support_ok = len(positives) >= MIN_SUPPORT and len(negatives) >= MIN_SUPPORT
    wilson_ok = min_lcb >= MIN_WILSON
    return {
        "split_family": split_family,
        "split_name": split_name,
        "positive_support": len(positives),
        "negative_support": len(negatives),
        "positive_wilson95_lcb": round(pos_lcb, 12),
        "negative_wilson95_lcb": round(neg_lcb, 12),
        "min_wilson95_lcb": round(min_lcb, 12),
        "support_ok": support_ok,
        "wilson_ok": wilson_ok,
        "pass": support_ok and wilson_ok,
    }


def metric(axis: str, count: int) -> dict[str, Any]:
    lcb = wilson_lcb(count, count)
    return {
        "axis": axis,
        "successes": count,
        "total": count,
        "wilson95_lcb": round(lcb, 12),
        "support_ok": count >= MIN_SUPPORT,
        "wilson_ok": lcb >= MIN_WILSON,
        "pass": count >= MIN_SUPPORT and lcb >= MIN_WILSON,
    }


def run_verifier(root: Path, prefix: str) -> dict[str, Any]:
    proc = subprocess.run(
        ["python3", str(DIRECT_VERIFIER), "--intake-root", str(root)],
        cwd=REPO,
        text=True,
        capture_output=True,
        check=False,
        timeout=60,
    )
    stdout_path = CMD_OUT / f"{prefix}_direct_manipulation_row_intake_verifier.stdout.txt"
    stderr_path = CMD_OUT / f"{prefix}_direct_manipulation_row_intake_verifier.stderr.txt"
    stdout_path.write_text(proc.stdout, encoding="utf-8")
    stderr_path.write_text(proc.stderr, encoding="utf-8")
    try:
        payload = json.loads(proc.stdout)
    except json.JSONDecodeError:
        payload = {"status": "parse_failed", "stdout_sample": proc.stdout[:500]}
    return {
        "returncode": proc.returncode,
        "payload": payload,
        "stdout_path": rel(stdout_path),
        "stderr_path": rel(stderr_path),
    }


def acquire_lock() -> bool:
    try:
        os.mkdir(LOCK_DIR)
    except FileExistsError:
        return False
    write_json(
        LOCK_DIR / "owner.json",
        {
            "run_id": RUN_ID,
            "pid": os.getpid(),
            "created_at_utc": datetime.now(timezone.utc).isoformat(),
            "purpose": "append control-complete JPMorgan CBOT Treasury rows to live R6 intake",
        },
    )
    return True


def release_lock() -> None:
    if LOCK_DIR.exists():
        shutil.rmtree(LOCK_DIR)


def treasury_candidate(row: dict[str, str]) -> bool:
    symbol = normalize(row.get("symbol", "")).lower()
    venue = normalize(row.get("venue_or_market_center", "")).lower()
    return "cbot" in venue and ("t-bond" in symbol or "t-note" in symbol)


def build_split_metrics(positives: list[dict[str, str]], negatives: list[dict[str, str]]) -> list[dict[str, Any]]:
    combined: list[dict[str, str]] = []
    for row in positives:
        item = dict(row)
        item["_class"] = "positive"
        combined.append(item)
    for row in negatives:
        item = dict(row)
        item["_class"] = "negative"
        combined.append(item)

    roles = chronological_roles(positives, negatives)
    split_metrics = [split_metric("pooled_all_source_rows", "all_rows", combined)]
    for role in ["chronological_train", "chronological_calibration", "chronological_test"]:
        role_rows = [row for row in combined if roles.get(row.get("matched_negative_group_id", "")) == role]
        split_metrics.append(split_metric("chronological_group_split", role, role_rows))
    for symbol in sorted(Counter(normalize(row.get("symbol", "")) for row in combined)):
        rows = [row for row in combined if normalize(row.get("symbol", "")) == symbol]
        split_metrics.append(split_metric("heldout_symbol_exact", symbol, rows))
    for venue in sorted(Counter(normalize(row.get("venue_or_market_center", "")) for row in combined)):
        rows = [row for row in combined if normalize(row.get("venue_or_market_center", "")) == venue]
        split_metrics.append(split_metric("heldout_venue_exact", venue, rows))
    return split_metrics


def main() -> int:
    for path in [OUT, CMD_OUT, CHECKS]:
        path.mkdir(parents=True, exist_ok=True)

    board_hash_before = sha256(BOARD)
    required = [
        LIVE_ROOT / POSITIVE_NAME,
        LIVE_ROOT / NEGATIVE_NAME,
        LIVE_ROOT / PROVENANCE_NAME,
        JPM_POSITIVE,
        JPM_NEGATIVE,
        JPM_JSON,
        SIDECAR_CSV,
        DIRECT_VERIFIER,
    ]
    missing_inputs = [rel(path) for path in required if not path.exists()]
    if missing_inputs:
        write_json(
            OUT / "r6_jpm_cbot_treasury_control_uplift_v1.json",
            {
                "run_id": RUN_ID,
                "generated_at_utc": datetime.now(timezone.utc).isoformat(),
                "board_sha256_at_start": board_hash_before,
                "status": "blocked",
                "reason": "missing_required_inputs",
                "missing_inputs": missing_inputs,
                "update_goal": False,
            },
        )
        return 2

    if not acquire_lock():
        baseline_positive = read_csv(BASELINE_POSITIVE)
        baseline_negative = read_csv(BASELINE_NEGATIVE)
        fields = list(baseline_positive[0].keys())
        live_source_ids = {row["source_row_id"] for row in baseline_positive}
        candidate_positives = read_csv(JPM_POSITIVE)
        candidate_negatives = read_csv(JPM_NEGATIVE)
        negative_by_group = {row["matched_negative_group_id"]: row for row in candidate_negatives}
        selected_positives = [
            row
            for row in candidate_positives
            if treasury_candidate(row)
            and row.get("source_row_id") not in live_source_ids
            and row.get("matched_negative_group_id") in negative_by_group
        ]
        selected_negatives = [negative_by_group[row["matched_negative_group_id"]] for row in selected_positives]
        after_positive = baseline_positive + selected_positives
        after_negative = baseline_negative + selected_negatives

        if STAGING_ROOT.exists():
            shutil.rmtree(STAGING_ROOT)
        STAGING_ROOT.mkdir(parents=True)
        write_csv(STAGING_ROOT / POSITIVE_NAME, after_positive, fields)
        write_csv(STAGING_ROOT / NEGATIVE_NAME, after_negative, fields)
        write_json(
            STAGING_ROOT / PROVENANCE_NAME,
            {
                "artifact_type": "r6_jpm_cbot_treasury_control_uplift_v1_isolated_projection",
                "run_id": RUN_ID,
                "generated_at_utc": datetime.now(timezone.utc).isoformat(),
                "baseline_positive_rows": rel(BASELINE_POSITIVE),
                "baseline_matched_negative_rows": rel(BASELINE_NEGATIVE),
                "baseline_provenance": rel(BASELINE_PROVENANCE),
                "source_candidate_screen_json": rel(JPM_JSON),
                "selected_source_row_ids": [row["source_row_id"] for row in selected_positives],
                "lock_dir": str(LOCK_DIR),
                "policy": "shared lock exists, so this run verifies an isolated projection and does not mutate the live /tmp intake",
                "runtime_code_changed": False,
                "thresholds_relaxed": False,
                "raw_data_committed": False,
            },
        )
        write_csv(OUT / "jpm_cbot_treasury_selected_positive_rows_v1.csv", selected_positives, fields)
        write_csv(OUT / "jpm_cbot_treasury_selected_matched_controls_v1.csv", selected_negatives, fields)
        shutil.copy2(STAGING_ROOT / POSITIVE_NAME, OUT / "positive_spoofing_layering_rows_projected_v1.csv")
        shutil.copy2(STAGING_ROOT / NEGATIVE_NAME, OUT / "matched_negative_normal_activity_rows_projected_v1.csv")
        shutil.copy2(STAGING_ROOT / PROVENANCE_NAME, OUT / "provenance_manifest_projected_v1.json")
        projected_verifier = run_verifier(STAGING_ROOT, "projected")
        sidecar_controls = read_csv(SIDECAR_CSV)
        split_metrics = build_split_metrics(after_positive, after_negative)
        split_families: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in split_metrics:
            split_families[row["split_family"]].append(row)
        chronological_gate = all(row["pass"] for row in split_families["chronological_group_split"])
        heldout_symbol_gate = all(row["pass"] for row in split_families["heldout_symbol_exact"])
        heldout_venue_gate = all(row["pass"] for row in split_families["heldout_venue_exact"])
        pooled_direct_gate = bool(split_metrics[0]["pass"])
        sidecar_metrics = [
            metric("direct_positive_all_correct", len(after_positive)),
            metric("same_event_control_seed_all_correct", len(after_negative)),
            metric("independent_broad_normal_sidecar_all_correct", len(sidecar_controls)),
        ]
        sidecar_axis_gate = all(row["pass"] for row in sidecar_metrics)
        gate_result = (
            "r6_jpm_cbot_treasury_control_uplift_v1="
            "isolated_projection_ready_shared_lock_present_split_species_still_blocked"
        )
        write_csv(
            OUT / "r6_jpm_cbot_treasury_split_metrics_v1.csv",
            split_metrics,
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
            ],
        )
        write_csv(
            OUT / "r6_jpm_cbot_treasury_sidecar_metrics_v1.csv",
            sidecar_metrics,
            ["axis", "successes", "total", "wilson95_lcb", "support_ok", "wilson_ok", "pass"],
        )
        result = {
            "run_id": RUN_ID,
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "board_sha256_at_start": board_hash_before,
            "status": "isolated_projection_ready",
            "reason": "shared_lock_exists",
            "lock_dir": str(LOCK_DIR),
            "source_candidate_screen_json": rel(JPM_JSON),
            "baseline": {
                "positive_rows": rel(BASELINE_POSITIVE),
                "matched_negative_rows": rel(BASELINE_NEGATIVE),
                "provenance": rel(BASELINE_PROVENANCE),
            },
            "projected_verifier": projected_verifier,
            "selected_positive_rows_added": len(selected_positives),
            "selected_matched_controls_added": len(selected_negatives),
            "selected_source_row_ids": [row["source_row_id"] for row in selected_positives],
            "before_counts": {
                "positive_rows": len(baseline_positive),
                "matched_negative_rows": len(baseline_negative),
            },
            "projected_counts": {
                "positive_rows": len(after_positive),
                "matched_negative_rows": len(after_negative),
                "matched_group_count": projected_verifier["payload"].get("matched_group_count"),
                "sidecar_broad_normal_control_rows": len(sidecar_controls),
            },
            "direct_calibration": {
                "pooled_min_wilson95_lcb": split_metrics[0]["min_wilson95_lcb"],
                "pooled_direct_gate": pooled_direct_gate,
                "chronological_split_gate": chronological_gate,
                "heldout_symbol_gate": heldout_symbol_gate,
                "heldout_venue_gate": heldout_venue_gate,
                "split_metrics_csv": rel(OUT / "r6_jpm_cbot_treasury_split_metrics_v1.csv"),
            },
            "sidecar_calibration": {
                "sidecar_axis_gate": sidecar_axis_gate,
                "min_wilson95_lcb": round(min(float(row["wilson95_lcb"]) for row in sidecar_metrics), 12),
                "metrics_csv": rel(OUT / "r6_jpm_cbot_treasury_sidecar_metrics_v1.csv"),
            },
            "decision": {
                "gate_result": gate_result,
                "confidence_accepted_rows_added": 0,
                "new_confidence_gate": False,
                "strict_full_objective_achieved": False,
                "update_goal": False,
                "runtime_code_changed": False,
                "thresholds_relaxed": False,
                "raw_data_committed": False,
                "shared_intake_mutated": False,
                "external_requests_sent": False,
                "trade_usable": False,
                "acceptance_blocker": "shared lock prevented live mutation; chronological/symbol/venue split support and direct species coverage still fail",
            },
            "next_action": "When the shared lock clears, re-run this uplift against the live root or keep sourcing post-2017/non-spoofing direct species rows; do not mark Board A complete.",
        }
        write_json(OUT / "r6_jpm_cbot_treasury_control_uplift_v1.json", result)
        report_path = OUT / "r6_jpm_cbot_treasury_control_uplift_v1.md"
        report = [
            "# R6 JPM CBOT Treasury Control Uplift v1",
            "",
            f"- Run id: `{RUN_ID}`",
            "- Live mutation: `false` because the shared intake lock already existed.",
            f"- Selected JPM CBOT Treasury positive/control pairs in isolated projection: `{len(selected_positives)}`.",
            f"- Baseline rows: `{len(baseline_positive)}/{len(baseline_negative)}`; projected rows: `{len(after_positive)}/{len(after_negative)}`.",
            f"- Projected verifier status: `{projected_verifier['payload'].get('status')}`, return code `{projected_verifier['returncode']}`.",
            f"- Projected pooled direct Wilson95 LCB: `{split_metrics[0]['min_wilson95_lcb']}`; pooled direct gate `{str(pooled_direct_gate).lower()}`.",
            f"- Sidecar broad-normal rows: `{len(sidecar_controls)}`; sidecar axis gate `{str(sidecar_axis_gate).lower()}`.",
            f"- Chronological split gate: `{str(chronological_gate).lower()}`; heldout symbol gate: `{str(heldout_symbol_gate).lower()}`; heldout venue gate: `{str(heldout_venue_gate).lower()}`.",
            f"- Gate result: `{gate_result}`.",
            "- Strict full objective achieved: `false`; `update_goal=false`.",
            "- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; external requests sent: `false`; trade usable: `false`.",
            "",
            "## Selected Rows",
            "",
            *[f"- `{row['source_row_id']}` {row['trade_date']} {row['symbol']}" for row in selected_positives],
            "",
            "## Artifacts",
            "",
            f"- JSON: `{rel(OUT / 'r6_jpm_cbot_treasury_control_uplift_v1.json')}`",
            f"- Report: `{rel(report_path)}`",
            f"- Selected positives: `{rel(OUT / 'jpm_cbot_treasury_selected_positive_rows_v1.csv')}`",
            f"- Selected matched controls: `{rel(OUT / 'jpm_cbot_treasury_selected_matched_controls_v1.csv')}`",
            f"- Projected positive snapshot: `{rel(OUT / 'positive_spoofing_layering_rows_projected_v1.csv')}`",
            f"- Projected matched-control snapshot: `{rel(OUT / 'matched_negative_normal_activity_rows_projected_v1.csv')}`",
            f"- Split metrics: `{rel(OUT / 'r6_jpm_cbot_treasury_split_metrics_v1.csv')}`",
            f"- Assertions: `{rel(CHECKS / 'r6_jpm_cbot_treasury_control_uplift_v1_assertions.out')}`",
            "",
            "## Next",
            "",
            str(result["next_action"]),
        ]
        report_path.write_text("\n".join(report) + "\n", encoding="utf-8")
        assertions = [
            ("shared_lock_respected", True),
            ("selected_positive_rows_4", len(selected_positives) == 4),
            ("selected_controls_4", len(selected_negatives) == 4),
            ("projected_verifier_ok", projected_verifier["returncode"] == 0 and projected_verifier["payload"].get("status") == "schema_ready_unscored"),
            ("projected_positive_rows_77", len(after_positive) == 77),
            ("projected_matched_negative_rows_77", len(after_negative) == 77),
            ("pooled_direct_gate_true", pooled_direct_gate),
            ("sidecar_axis_gate_true", sidecar_axis_gate),
            ("strict_goal_false", result["decision"]["strict_full_objective_achieved"] is False),
            ("shared_intake_not_mutated", result["decision"]["shared_intake_mutated"] is False),
        ]
        (CHECKS / "r6_jpm_cbot_treasury_control_uplift_v1_assertions.out").write_text(
            "\n".join(f"{name}={'ok' if ok else 'FAIL'}" for name, ok in assertions) + "\n",
            encoding="utf-8",
        )
        if not all(ok for _, ok in assertions):
            return 2
        print(json.dumps({"ok": True, "mode": "isolated_projection", "gate_result": gate_result, "rows_selected": len(selected_positives), "update_goal": False}, indent=2))
        return 0

    try:
        live_positive_path = LIVE_ROOT / POSITIVE_NAME
        live_negative_path = LIVE_ROOT / NEGATIVE_NAME
        live_provenance_path = LIVE_ROOT / PROVENANCE_NAME
        before_positive = read_csv(live_positive_path)
        before_negative = read_csv(live_negative_path)
        fields = list(before_positive[0].keys())
        live_source_ids = {row["source_row_id"] for row in before_positive}

        candidate_positives = read_csv(JPM_POSITIVE)
        candidate_negatives = read_csv(JPM_NEGATIVE)
        negative_by_group = {row["matched_negative_group_id"]: row for row in candidate_negatives}
        selected_positives = [
            row
            for row in candidate_positives
            if treasury_candidate(row)
            and row.get("source_row_id") not in live_source_ids
            and row.get("matched_negative_group_id") in negative_by_group
        ]
        selected_negatives = [negative_by_group[row["matched_negative_group_id"]] for row in selected_positives]

        shutil.copy2(live_positive_path, OUT / "positive_spoofing_layering_rows_before_v1.csv")
        shutil.copy2(live_negative_path, OUT / "matched_negative_normal_activity_rows_before_v1.csv")
        shutil.copy2(live_provenance_path, OUT / "provenance_manifest_before_v1.json")
        write_csv(OUT / "jpm_cbot_treasury_selected_positive_rows_v1.csv", selected_positives, fields)
        write_csv(OUT / "jpm_cbot_treasury_selected_matched_controls_v1.csv", selected_negatives, fields)

        after_positive = before_positive + selected_positives
        after_negative = before_negative + selected_negatives
        before_verifier = run_verifier(LIVE_ROOT, "before")

        if STAGING_ROOT.exists():
            shutil.rmtree(STAGING_ROOT)
        STAGING_ROOT.mkdir(parents=True)
        write_csv(STAGING_ROOT / POSITIVE_NAME, after_positive, fields)
        write_csv(STAGING_ROOT / NEGATIVE_NAME, after_negative, fields)
        prior_provenance = json.loads(live_provenance_path.read_text(encoding="utf-8"))
        next_provenance = {
            **prior_provenance,
            "jpm_cbot_treasury_control_uplift_v1": {
                "run_id": RUN_ID,
                "generated_at_utc": datetime.now(timezone.utc).isoformat(),
                "source_candidate_screen_json": rel(JPM_JSON),
                "source_candidate_positive_csv": rel(JPM_POSITIVE),
                "source_candidate_control_csv": rel(JPM_NEGATIVE),
                "selected_positive_rows": len(selected_positives),
                "selected_matched_controls": len(selected_negatives),
                "selected_source_row_ids": [row["source_row_id"] for row in selected_positives],
                "selection_policy": "promote only official CFTC JPMorgan CBOT Treasury positive/control pairs absent from the live intake",
                "before_positive_rows": len(before_positive),
                "before_matched_negative_rows": len(before_negative),
                "after_positive_rows": len(after_positive),
                "after_matched_negative_rows": len(after_negative),
                "runtime_code_changed": False,
                "thresholds_relaxed": False,
                "raw_data_committed": False,
            },
        }
        write_json(STAGING_ROOT / PROVENANCE_NAME, next_provenance)
        staged_verifier = run_verifier(STAGING_ROOT, "staged")
        if staged_verifier["returncode"] != 0 or staged_verifier["payload"].get("status") != "schema_ready_unscored":
            raise RuntimeError(f"staged verifier failed: {staged_verifier}")

        shutil.copy2(STAGING_ROOT / POSITIVE_NAME, OUT / "positive_spoofing_layering_rows_after_v1.csv")
        shutil.copy2(STAGING_ROOT / NEGATIVE_NAME, OUT / "matched_negative_normal_activity_rows_after_v1.csv")
        shutil.copy2(STAGING_ROOT / PROVENANCE_NAME, OUT / "provenance_manifest_after_v1.json")
        os.replace(STAGING_ROOT / POSITIVE_NAME, live_positive_path)
        os.replace(STAGING_ROOT / NEGATIVE_NAME, live_negative_path)
        os.replace(STAGING_ROOT / PROVENANCE_NAME, live_provenance_path)

        after_verifier = run_verifier(LIVE_ROOT, "after")
        sidecar_controls = read_csv(SIDECAR_CSV)
        split_metrics = build_split_metrics(after_positive, after_negative)
        split_families: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in split_metrics:
            split_families[row["split_family"]].append(row)
        chronological_gate = all(row["pass"] for row in split_families["chronological_group_split"])
        heldout_symbol_gate = all(row["pass"] for row in split_families["heldout_symbol_exact"])
        heldout_venue_gate = all(row["pass"] for row in split_families["heldout_venue_exact"])
        pooled_direct_gate = bool(split_metrics[0]["pass"])
        sidecar_metrics = [
            metric("direct_positive_all_correct", len(after_positive)),
            metric("same_event_control_seed_all_correct", len(after_negative)),
            metric("independent_broad_normal_sidecar_all_correct", len(sidecar_controls)),
        ]
        sidecar_axis_gate = all(row["pass"] for row in sidecar_metrics)
        direct_species_closed = False
        gate_result = (
            "r6_jpm_cbot_treasury_control_uplift_v1="
            "live_rows_appended_pooled_and_sidecar_axes_pass_split_species_still_blocked"
        )

        write_csv(
            OUT / "r6_jpm_cbot_treasury_split_metrics_v1.csv",
            split_metrics,
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
            ],
        )
        write_csv(
            OUT / "r6_jpm_cbot_treasury_sidecar_metrics_v1.csv",
            sidecar_metrics,
            ["axis", "successes", "total", "wilson95_lcb", "support_ok", "wilson_ok", "pass"],
        )

        result = {
            "run_id": RUN_ID,
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "board_sha256_at_start": board_hash_before,
            "source_candidate_screen_json": rel(JPM_JSON),
            "live_root": str(LIVE_ROOT),
            "shared_lock_acquired": True,
            "before_verifier": before_verifier,
            "staged_verifier": staged_verifier,
            "after_verifier": after_verifier,
            "selected_positive_rows_added": len(selected_positives),
            "selected_matched_controls_added": len(selected_negatives),
            "selected_source_row_ids": [row["source_row_id"] for row in selected_positives],
            "before_counts": {
                "positive_rows": len(before_positive),
                "matched_negative_rows": len(before_negative),
            },
            "after_counts": {
                "positive_rows": len(after_positive),
                "matched_negative_rows": len(after_negative),
                "matched_group_count": after_verifier["payload"].get("matched_group_count"),
                "sidecar_broad_normal_control_rows": len(sidecar_controls),
            },
            "direct_calibration": {
                "pooled_min_wilson95_lcb": split_metrics[0]["min_wilson95_lcb"],
                "pooled_direct_gate": pooled_direct_gate,
                "chronological_split_gate": chronological_gate,
                "heldout_symbol_gate": heldout_symbol_gate,
                "heldout_venue_gate": heldout_venue_gate,
                "split_metrics_csv": rel(OUT / "r6_jpm_cbot_treasury_split_metrics_v1.csv"),
            },
            "sidecar_calibration": {
                "sidecar_axis_gate": sidecar_axis_gate,
                "min_wilson95_lcb": round(min(float(row["wilson95_lcb"]) for row in sidecar_metrics), 12),
                "metrics_csv": rel(OUT / "r6_jpm_cbot_treasury_sidecar_metrics_v1.csv"),
            },
            "decision": {
                "gate_result": gate_result,
                "confidence_accepted_rows_added": len(selected_positives),
                "new_confidence_gate": False,
                "strict_full_objective_achieved": False,
                "update_goal": False,
                "runtime_code_changed": False,
                "thresholds_relaxed": False,
                "raw_data_committed": False,
                "shared_intake_mutated": len(selected_positives) > 0,
                "external_requests_sent": False,
                "trade_usable": False,
                "acceptance_blocker": "chronological/symbol/venue split support and direct species coverage still fail; R5 and R3 blockers remain open",
            },
            "next_action": "Target post-2017/test-bucket rows and non-spoofing direct species next; this CBOT Treasury uplift improves control-complete venue breadth but does not close split/species gates.",
        }
        write_json(OUT / "r6_jpm_cbot_treasury_control_uplift_v1.json", result)
        report_path = OUT / "r6_jpm_cbot_treasury_control_uplift_v1.md"
        report = [
            "# R6 JPM CBOT Treasury Control Uplift v1",
            "",
            f"- Run id: `{RUN_ID}`",
            f"- Selected JPM CBOT Treasury positive/control pairs added: `{len(selected_positives)}`.",
            f"- Live rows before: `{len(before_positive)}/{len(before_negative)}`; after: `{len(after_positive)}/{len(after_negative)}`.",
            f"- Direct verifier after append: `{after_verifier['payload'].get('status')}`, return code `{after_verifier['returncode']}`.",
            f"- Pooled direct Wilson95 LCB: `{split_metrics[0]['min_wilson95_lcb']}`; pooled direct gate `{str(pooled_direct_gate).lower()}`.",
            f"- Sidecar broad-normal rows: `{len(sidecar_controls)}`; sidecar axis gate `{str(sidecar_axis_gate).lower()}`.",
            f"- Chronological split gate: `{str(chronological_gate).lower()}`; heldout symbol gate: `{str(heldout_symbol_gate).lower()}`; heldout venue gate: `{str(heldout_venue_gate).lower()}`.",
            f"- Direct species closed: `{str(direct_species_closed).lower()}`.",
            f"- Gate result: `{gate_result}`.",
            "- Strict full objective achieved: `false`; `update_goal=false`.",
            "- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; external requests sent: `false`; trade usable: `false`.",
            "",
            "## Selected Rows",
            "",
            *[f"- `{row['source_row_id']}` {row['trade_date']} {row['symbol']}" for row in selected_positives],
            "",
            "## Artifacts",
            "",
            f"- JSON: `{rel(OUT / 'r6_jpm_cbot_treasury_control_uplift_v1.json')}`",
            f"- Report: `{rel(report_path)}`",
            f"- Selected positives: `{rel(OUT / 'jpm_cbot_treasury_selected_positive_rows_v1.csv')}`",
            f"- Selected matched controls: `{rel(OUT / 'jpm_cbot_treasury_selected_matched_controls_v1.csv')}`",
            f"- After positive snapshot: `{rel(OUT / 'positive_spoofing_layering_rows_after_v1.csv')}`",
            f"- After matched-control snapshot: `{rel(OUT / 'matched_negative_normal_activity_rows_after_v1.csv')}`",
            f"- Split metrics: `{rel(OUT / 'r6_jpm_cbot_treasury_split_metrics_v1.csv')}`",
            f"- Assertions: `{rel(CHECKS / 'r6_jpm_cbot_treasury_control_uplift_v1_assertions.out')}`",
            "",
            "## Next",
            "",
            str(result["next_action"]),
        ]
        report_path.write_text("\n".join(report) + "\n", encoding="utf-8")
        assertions = [
            ("lock_acquired", True),
            ("selected_positive_rows_added_4", len(selected_positives) == 4),
            ("selected_controls_added_4", len(selected_negatives) == 4),
            ("after_verifier_ok", after_verifier["returncode"] == 0 and after_verifier["payload"].get("status") == "schema_ready_unscored"),
            ("after_positive_rows_77", len(after_positive) == 77),
            ("after_matched_negative_rows_77", len(after_negative) == 77),
            ("pooled_direct_gate_true", pooled_direct_gate),
            ("sidecar_axis_gate_true", sidecar_axis_gate),
            ("chronological_still_blocked", not chronological_gate),
            ("symbol_still_blocked", not heldout_symbol_gate),
            ("venue_still_blocked", not heldout_venue_gate),
            ("strict_goal_false", result["decision"]["strict_full_objective_achieved"] is False),
        ]
        failed = [name for name, ok in assertions if not ok]
        (CHECKS / "r6_jpm_cbot_treasury_control_uplift_v1_assertions.out").write_text(
            "\n".join(f"{name}={'ok' if ok else 'FAIL'}" for name, ok in assertions) + "\n",
            encoding="utf-8",
        )
        if failed:
            raise RuntimeError(f"assertions failed: {failed}")
        print(json.dumps({"ok": True, "gate_result": gate_result, "rows_added": len(selected_positives), "update_goal": False}, indent=2))
        return 0
    finally:
        if STAGING_ROOT.exists():
            shutil.rmtree(STAGING_ROOT)
        release_lock()


if __name__ == "__main__":
    raise SystemExit(main())
