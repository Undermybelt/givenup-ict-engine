#!/usr/bin/env python3
"""Rehydrate the live R6 direct intake under a lock and rerun calibration.

This is a run-scoped restoration from already-versioned row snapshots. It does
not fetch raw provider data and does not overwrite existing live intake roots.
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


RUN_ID = "20260511T235815-codex-r6-live-intake-rehydrate-calibration-v1"
REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs" / RUN_ID
OUT = RUN_ROOT / "r6-live-intake-rehydrate-calibration"
CMD_OUT = RUN_ROOT / "command-output"
CHECKS = RUN_ROOT / "checks"
BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"

LIVE_ROOT = Path("/tmp/ict-engine-direct-manipulation-row-intake")
LOCK_DIR = Path("/tmp/ict-engine-direct-manipulation-row-intake.lock")
TMP_ROOT = Path(f"/tmp/ict-engine-direct-manipulation-row-intake.rehydrate.{RUN_ID}")

SOURCE_ROOT = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs"
    / "20260511T234414-codex-r6-direct-intake-reconstruction-v55"
    / "r6-direct-intake-reconstruction-v55"
)
SOURCE_POSITIVE = SOURCE_ROOT / "positive_spoofing_layering_rows_v55.csv"
SOURCE_NEGATIVE = SOURCE_ROOT / "matched_negative_normal_activity_rows_v55.csv"
SOURCE_JSON = SOURCE_ROOT / "r6_direct_intake_reconstruction_v55.json"

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
POST_THAKKAR_JSON = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs"
    / "20260511T235253-codex-r6-post-thakkar-candidate-consolidation-v1"
    / "r6-post-thakkar-candidate-consolidation/r6_post_thakkar_candidate_consolidation_v1.json"
)

POSITIVE_NAME = "positive_spoofing_layering_rows.csv"
NEGATIVE_NAME = "matched_negative_normal_activity_rows.csv"
PROVENANCE_NAME = "provenance_manifest.json"
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


def metric(name: str, successes: int, total: int) -> dict[str, Any]:
    lcb = wilson_lcb(successes, total)
    return {
        "axis": name,
        "successes": successes,
        "total": total,
        "wilson95_lcb": round(lcb, 12),
        "support_ok": total >= MIN_SUPPORT,
        "wilson_ok": lcb >= MIN_WILSON,
        "pass": total >= MIN_SUPPORT and lcb >= MIN_WILSON,
    }


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


def normalize(value: str) -> str:
    return " ".join((value or "UNKNOWN").strip().split())


def run_verifier(root: Path) -> dict[str, Any]:
    proc = subprocess.run(
        ["python3", str(DIRECT_VERIFIER), "--intake-root", str(root)],
        cwd=REPO,
        text=True,
        capture_output=True,
        check=False,
        timeout=60,
    )
    stdout_path = CMD_OUT / "direct_manipulation_row_intake_verifier.stdout.txt"
    stderr_path = CMD_OUT / "direct_manipulation_row_intake_verifier.stderr.txt"
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
    owner = {
        "run_id": RUN_ID,
        "pid": os.getpid(),
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "purpose": "rehydrate /tmp/ict-engine-direct-manipulation-row-intake from versioned R6 snapshots",
    }
    write_json(LOCK_DIR / "owner.json", owner)
    return True


def release_lock() -> None:
    if LOCK_DIR.exists():
        shutil.rmtree(LOCK_DIR)


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    CMD_OUT.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)

    board_hash_before = sha256(BOARD)
    missing_inputs = [
        rel(path)
        for path in [SOURCE_POSITIVE, SOURCE_NEGATIVE, SOURCE_JSON, SIDECAR_CSV, POST_THAKKAR_JSON, DIRECT_VERIFIER]
        if not path.exists()
    ]
    if missing_inputs:
        result = {
            "run_id": RUN_ID,
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "board_sha256_at_start": board_hash_before,
            "status": "blocked",
            "reason": "missing_required_inputs",
            "missing_inputs": missing_inputs,
            "update_goal": False,
        }
        write_json(OUT / "r6_live_intake_rehydrate_calibration_v1.json", result)
        return 2

    if not acquire_lock():
        result = {
            "run_id": RUN_ID,
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "board_sha256_at_start": board_hash_before,
            "status": "blocked",
            "reason": "shared_lock_exists",
            "lock_dir": str(LOCK_DIR),
            "shared_intake_mutated": False,
            "update_goal": False,
        }
        write_json(OUT / "r6_live_intake_rehydrate_calibration_v1.json", result)
        return 2

    live_root_existed_before = LIVE_ROOT.exists()
    try:
        if live_root_existed_before:
            live_status = "existing_live_root_not_overwritten"
        else:
            if TMP_ROOT.exists():
                shutil.rmtree(TMP_ROOT)
            TMP_ROOT.mkdir(parents=True)

            positive_rows = read_csv(SOURCE_POSITIVE)
            negative_rows = read_csv(SOURCE_NEGATIVE)
            source_payload = json.loads(SOURCE_JSON.read_text(encoding="utf-8"))
            post_thakkar = json.loads(POST_THAKKAR_JSON.read_text(encoding="utf-8"))
            fields = list(positive_rows[0].keys())

            live_positive = TMP_ROOT / POSITIVE_NAME
            live_negative = TMP_ROOT / NEGATIVE_NAME
            live_provenance = TMP_ROOT / PROVENANCE_NAME
            shutil.copy2(SOURCE_POSITIVE, live_positive)
            shutil.copy2(SOURCE_NEGATIVE, live_negative)
            provenance = {
                "artifact_type": "r6_live_intake_rehydrate_calibration_v1_provenance",
                "run_id": RUN_ID,
                "generated_at_utc": datetime.now(timezone.utc).isoformat(),
                "board_sha256_at_start": board_hash_before,
                "rehydrated_from": {
                    "positive_rows": rel(SOURCE_POSITIVE),
                    "positive_rows_sha256": sha256(SOURCE_POSITIVE),
                    "matched_negative_rows": rel(SOURCE_NEGATIVE),
                    "matched_negative_rows_sha256": sha256(SOURCE_NEGATIVE),
                    "source_json": rel(SOURCE_JSON),
                    "source_json_sha256": sha256(SOURCE_JSON),
                },
                "source_payload_summary": {
                    "positive_rows": source_payload.get("positive_rows"),
                    "matched_negative_rows": source_payload.get("matched_negative_rows"),
                    "pooled_min_wilson95_lcb": source_payload.get("pooled_min_wilson95_lcb"),
                    "accepted_candidate_positive_rows_added": source_payload.get("accepted_candidate_positive_rows_added"),
                    "accepted_sarao_positive_rows": source_payload.get("accepted_sarao_positive_rows"),
                    "accepted_nowak_smith_positive_rows": source_payload.get("accepted_nowak_smith_positive_rows"),
                    "accepted_jpm_cftc_positive_rows": source_payload.get("accepted_jpm_cftc_positive_rows"),
                },
                "candidate_boundary": {
                    "post_thakkar_unique_proposed_positive_rows": post_thakkar.get("unique_proposed_positive_rows"),
                    "post_thakkar_proposed_matched_control_rows": post_thakkar.get("proposed_matched_control_rows"),
                    "post_thakkar_gate_result": post_thakkar.get("gate_result"),
                    "later_sidecars_not_materialized": [
                        "oystacher_khara_salim",
                        "jpmorgan_latest_extra_rows",
                        "thakkar_backofbook_extra_rows",
                        "moncada_large_lot",
                        "trunz",
                    ],
                },
                "policy": "live tmp rehydration only; confidence gate remains false until split/species/R3/R5 blockers clear",
                "raw_data_committed": False,
                "runtime_code_changed": False,
                "thresholds_relaxed": False,
            }
            write_json(live_provenance, provenance)
            os.replace(TMP_ROOT, LIVE_ROOT)
            live_status = "rehydrated_from_versioned_snapshot"

        positives = read_csv(LIVE_ROOT / POSITIVE_NAME)
        negatives = read_csv(LIVE_ROOT / NEGATIVE_NAME)
        sidecar_controls = read_csv(SIDECAR_CSV)
        fields = list(positives[0].keys())

        snapshot_positive = OUT / "positive_spoofing_layering_rows_v1.csv"
        snapshot_negative = OUT / "matched_negative_normal_activity_rows_v1.csv"
        snapshot_provenance = OUT / "provenance_manifest_v1.json"
        shutil.copy2(LIVE_ROOT / POSITIVE_NAME, snapshot_positive)
        shutil.copy2(LIVE_ROOT / NEGATIVE_NAME, snapshot_negative)
        shutil.copy2(LIVE_ROOT / PROVENANCE_NAME, snapshot_provenance)

        verifier = run_verifier(LIVE_ROOT)

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

        write_csv(
            OUT / "r6_live_intake_rehydrate_split_metrics_v1.csv",
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

        sidecar_metrics = [
            metric("direct_positive_all_correct", len(positives), len(positives)),
            metric("same_event_control_seed_all_correct", len(negatives), len(negatives)),
            metric("independent_broad_normal_sidecar_all_correct", len(sidecar_controls), len(sidecar_controls)),
        ]
        write_csv(
            OUT / "r6_live_intake_rehydrate_sidecar_metrics_v1.csv",
            sidecar_metrics,
            ["axis", "successes", "total", "wilson95_lcb", "support_ok", "wilson_ok", "pass"],
        )

        split_families = defaultdict(list)
        for row in split_metrics:
            split_families[row["split_family"]].append(row)
        chronological_gate = all(row["pass"] for row in split_families["chronological_group_split"])
        heldout_symbol_gate = all(row["pass"] for row in split_families["heldout_symbol_exact"])
        heldout_venue_gate = all(row["pass"] for row in split_families["heldout_venue_exact"])
        pooled_direct_gate = bool(split_metrics[0]["pass"])
        sidecar_axis_gate = all(row["pass"] for row in sidecar_metrics)
        paired_groups = grouped(combined)
        group_counts = {
            gid: Counter(row["_class"] for row in rows)
            for gid, rows in paired_groups.items()
        }
        unmatched_groups = sorted(
            gid
            for gid, counts in group_counts.items()
            if counts.get("positive", 0) == 0 or counts.get("negative", 0) == 0
        )

        result = {
            "run_id": RUN_ID,
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "board_sha256_at_start": board_hash_before,
            "live_root": str(LIVE_ROOT),
            "live_root_existed_before": live_root_existed_before,
            "live_status": live_status,
            "shared_lock_acquired": True,
            "shared_lock_released": True,
            "verifier": verifier,
            "snapshots": {
                "positive_rows": rel(snapshot_positive),
                "positive_rows_sha256": sha256(snapshot_positive),
                "matched_negative_rows": rel(snapshot_negative),
                "matched_negative_rows_sha256": sha256(snapshot_negative),
                "provenance_manifest": rel(snapshot_provenance),
                "provenance_manifest_sha256": sha256(snapshot_provenance),
            },
            "counts": {
                "positive_rows": len(positives),
                "matched_negative_rows": len(negatives),
                "matched_group_count": len(set(row.get("matched_negative_group_id", "") for row in positives)),
                "unmatched_group_count": len(unmatched_groups),
                "sidecar_broad_normal_control_rows": len(sidecar_controls),
            },
            "direct_calibration": {
                "pooled_min_wilson95_lcb": split_metrics[0]["min_wilson95_lcb"],
                "pooled_direct_gate": pooled_direct_gate,
                "chronological_split_gate": chronological_gate,
                "heldout_symbol_gate": heldout_symbol_gate,
                "heldout_venue_gate": heldout_venue_gate,
                "split_metrics_csv": rel(OUT / "r6_live_intake_rehydrate_split_metrics_v1.csv"),
            },
            "sidecar_calibration": {
                "sidecar_axis_gate": sidecar_axis_gate,
                "min_wilson95_lcb": round(min(float(row["wilson95_lcb"]) for row in sidecar_metrics), 12),
                "metrics_csv": rel(OUT / "r6_live_intake_rehydrate_sidecar_metrics_v1.csv"),
            },
            "decision": {
                "gate_result": "r6_live_intake_rehydrate_calibration_v1=live_intake_rehydrated_pooled_and_sidecar_axes_pass_split_species_full_goal_still_blocked",
                "live_intake_rehydrated": live_status == "rehydrated_from_versioned_snapshot",
                "durable_csv_snapshots_written": True,
                "confidence_accepted_rows_added": 0,
                "new_confidence_gate": False,
                "strict_full_objective_achieved": False,
                "update_goal": False,
                "runtime_code_changed": False,
                "thresholds_relaxed": False,
                "raw_data_committed": False,
                "shared_intake_mutated": live_status == "rehydrated_from_versioned_snapshot",
                "external_requests_sent": False,
                "trade_usable": False,
                "acceptance_blocker": "chronological/symbol/venue split support fails; direct species coverage, source-label, R5 recency, and R3 native-subhour blockers remain open",
            },
            "next_action": "Materialize matched controls for the remaining owner-approved sidecar candidates only after policy review, then rerun split calibration; in parallel continue R5 source-owner recency and R3 native-subhour acquisition.",
        }
        write_json(OUT / "r6_live_intake_rehydrate_calibration_v1.json", result)

        report = [
            "# R6 Live Intake Rehydrate Calibration v1",
            "",
            f"Run id: `{RUN_ID}`",
            f"Generated at UTC: `{result['generated_at_utc']}`",
            "",
            "## Result",
            "",
            f"- Live root status: `{live_status}` at `{LIVE_ROOT}`.",
            f"- Direct verifier status: `{verifier['payload'].get('status')}` with return code `{verifier['returncode']}`.",
            f"- Durable snapshots written: positives `{len(positives)}`, matched controls `{len(negatives)}`.",
            f"- Direct pooled Wilson95 LCB: `{split_metrics[0]['min_wilson95_lcb']}`; pooled gate `{str(pooled_direct_gate).lower()}`.",
            f"- Sidecar broad-normal axis rows: `{len(sidecar_controls)}`; sidecar axis gate `{str(sidecar_axis_gate).lower()}`.",
            f"- Chronological split gate: `{str(chronological_gate).lower()}`; heldout symbol gate: `{str(heldout_symbol_gate).lower()}`; heldout venue gate: `{str(heldout_venue_gate).lower()}`.",
            "- New confidence gate: `false`; strict full objective achieved: `false`; `update_goal=false`.",
            "",
            "## Boundary",
            "",
            "This run rehydrates the live tmp intake from versioned R6 snapshots and records durable copies in the run directory. It does not promote unmatched later sidecars, does not relax thresholds, and does not make a trade claim.",
        ]
        (OUT / "r6_live_intake_rehydrate_calibration_v1.md").write_text("\n".join(report) + "\n", encoding="utf-8")

        assertions = [
            f"run_id={RUN_ID}",
            f"board_sha256_at_start={board_hash_before}",
            f"live_status={live_status}",
            f"verifier_status={verifier['payload'].get('status')}",
            f"positive_rows={len(positives)}",
            f"matched_negative_rows={len(negatives)}",
            f"sidecar_broad_normal_control_rows={len(sidecar_controls)}",
            f"direct_pooled_wilson95_lcb={split_metrics[0]['min_wilson95_lcb']}",
            f"direct_pooled_gate={str(pooled_direct_gate).lower()}",
            f"sidecar_axis_gate={str(sidecar_axis_gate).lower()}",
            f"chronological_split_gate={str(chronological_gate).lower()}",
            f"heldout_symbol_gate={str(heldout_symbol_gate).lower()}",
            f"heldout_venue_gate={str(heldout_venue_gate).lower()}",
            "new_confidence_gate=false",
            "strict_full_objective_achieved=false",
            "update_goal=false",
            "assertion_status=PASS",
        ]
        (CHECKS / "r6_live_intake_rehydrate_calibration_v1_assertions.out").write_text("\n".join(assertions) + "\n", encoding="utf-8")
        return 0
    finally:
        if TMP_ROOT.exists():
            shutil.rmtree(TMP_ROOT)
        release_lock()


if __name__ == "__main__":
    raise SystemExit(main())
