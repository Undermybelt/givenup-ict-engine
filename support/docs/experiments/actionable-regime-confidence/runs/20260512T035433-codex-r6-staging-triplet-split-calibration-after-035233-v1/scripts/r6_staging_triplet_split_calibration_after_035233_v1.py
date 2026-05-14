#!/usr/bin/env python3
"""Read-only split calibration for the R6 staging triplet found after 035049."""

from __future__ import annotations

import csv
import hashlib
import json
import math
import subprocess
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


RUN_ID = "20260512T035433-codex-r6-staging-triplet-split-calibration-after-035233-v1"
SLUG = "r6-staging-triplet-split-calibration-after-035233-v1"
REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs" / RUN_ID
OUT = RUN_ROOT / SLUG
CMD_OUT = RUN_ROOT / "command-output"
CHECKS = RUN_ROOT / "checks"
BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"

STAGING_ROOT = Path("/private/tmp/20260512T000803-codex-r6-jpm-cbot-treasury-control-uplift-v1.staging")
POSITIVE_NAME = "positive_spoofing_layering_rows.csv"
NEGATIVE_NAME = "matched_negative_normal_activity_rows.csv"
PROVENANCE_NAME = "provenance_manifest.json"

DIRECT_VERIFIER = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs"
    / "20260511T151950-codex-direct-manipulation-row-intake-manifest-v1"
    / "direct-manipulation-intake/direct_manipulation_row_intake_verifier_v1.py"
)

UPSTREAM_READBACK_ROOT = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs"
    / "20260512T035233-codex-r6-staging-triplet-readonly-verifier-after-035049-v1"
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


def required_all_successes() -> int:
    n = max(1, MIN_SUPPORT)
    while wilson_lcb(n, n) < MIN_WILSON:
        n += 1
    return n


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


def metric(axis: str, successes: int, total: int) -> dict[str, Any]:
    lcb = wilson_lcb(successes, total)
    return {
        "axis": axis,
        "successes": successes,
        "total": total,
        "wilson95_lcb": round(lcb, 12),
        "support_ok": total >= MIN_SUPPORT,
        "wilson_ok": lcb >= MIN_WILSON,
        "pass": total >= MIN_SUPPORT and lcb >= MIN_WILSON,
    }


def normalize(value: str) -> str:
    return " ".join((value or "UNKNOWN").strip().split())


def safe_date(row: dict[str, str]) -> str:
    return row.get("trade_date") or "9999-12-31"


def grouped(rows: list[dict[str, str]]) -> dict[str, list[dict[str, str]]]:
    groups: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        groups[row.get("matched_negative_group_id", "")].append(row)
    return groups


def chronological_roles(rows: list[dict[str, str]]) -> dict[str, str]:
    groups = grouped(rows)
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


def run_verifier() -> dict[str, Any]:
    proc = subprocess.run(
        ["python3", str(DIRECT_VERIFIER), "--intake-root", str(STAGING_ROOT)],
        cwd=REPO,
        text=True,
        capture_output=True,
        check=False,
        timeout=60,
    )
    stdout_path = CMD_OUT / "direct_verifier_staging_candidate.stdout.txt"
    stderr_path = CMD_OUT / "direct_verifier_staging_candidate.stderr.txt"
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


def build_split_metrics(combined: list[dict[str, str]]) -> list[dict[str, Any]]:
    roles = chronological_roles(combined)
    metrics = [split_metric("pooled_all_source_rows", "all_rows", combined)]
    for role in ["chronological_train", "chronological_calibration", "chronological_test"]:
        role_rows = [row for row in combined if roles.get(row.get("matched_negative_group_id", "")) == role]
        metrics.append(split_metric("chronological_group_split", role, role_rows))
    for symbol in sorted(Counter(normalize(row.get("symbol", "")) for row in combined)):
        rows = [row for row in combined if normalize(row.get("symbol", "")) == symbol]
        metrics.append(split_metric("heldout_symbol_exact", symbol, rows))
    for venue in sorted(Counter(normalize(row.get("venue_or_market_center", "")) for row in combined)):
        rows = [row for row in combined if normalize(row.get("venue_or_market_center", "")) == venue]
        metrics.append(split_metric("heldout_venue_exact", venue, rows))
    return metrics


def gap_rows(split_metrics: list[dict[str, Any]], required_n: int) -> list[dict[str, Any]]:
    rows = []
    for row in split_metrics:
        if bool(row["pass"]):
            continue
        pos = int(row["positive_support"])
        neg = int(row["negative_support"])
        rows.append(
            {
                "split_family": row["split_family"],
                "split_name": row["split_name"],
                "positive_support": pos,
                "negative_support": neg,
                "current_min_wilson95_lcb": row["min_wilson95_lcb"],
                "required_positive_support_for_95_if_all_correct": required_n,
                "required_negative_support_for_95_if_all_correct": required_n,
                "additional_positive_rows_needed_min": max(0, required_n - pos),
                "additional_negative_rows_needed_min": max(0, required_n - neg),
                "additional_pair_rows_needed_min": max(max(0, required_n - pos), max(0, required_n - neg)),
            }
        )
    return rows


def family_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_family: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_family[str(row["split_family"])].append(row)
    return {
        family: {
            "failing_cells": len(items),
            "max_pair_rows_needed_min": max(int(item["additional_pair_rows_needed_min"]) for item in items),
            "sum_pair_rows_needed_min_if_exact_cells_must_all_pass": sum(
                int(item["additional_pair_rows_needed_min"]) for item in items
            ),
            "worst_cells": sorted(items, key=lambda item: int(item["additional_pair_rows_needed_min"]), reverse=True)[:10],
        }
        for family, items in sorted(by_family.items())
    }


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    CMD_OUT.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)

    required_files = [STAGING_ROOT / POSITIVE_NAME, STAGING_ROOT / NEGATIVE_NAME, STAGING_ROOT / PROVENANCE_NAME, DIRECT_VERIFIER, BOARD]
    missing = [str(path) for path in required_files if not path.exists()]
    if missing:
        payload = {
            "run_id": RUN_ID,
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "status": "blocked",
            "reason": "missing_required_inputs",
            "missing_inputs": missing,
            "update_goal": False,
        }
        write_json(OUT / "r6_staging_triplet_split_calibration_after_035233_v1.json", payload)
        return 2

    positives = read_csv(STAGING_ROOT / POSITIVE_NAME)
    negatives = read_csv(STAGING_ROOT / NEGATIVE_NAME)
    provenance = json.loads((STAGING_ROOT / PROVENANCE_NAME).read_text(encoding="utf-8"))
    verifier = run_verifier()

    combined: list[dict[str, str]] = []
    for row in positives:
        item = dict(row)
        item["_class"] = "positive"
        combined.append(item)
    for row in negatives:
        item = dict(row)
        item["_class"] = "negative"
        combined.append(item)

    required_n = required_all_successes()
    split_metrics = build_split_metrics(combined)
    split_gaps = gap_rows(split_metrics, required_n)
    sidecar_metrics = [
        metric("staging_positive_all_correct", len(positives), len(positives)),
        metric("staging_same_event_control_seed_all_correct", len(negatives), len(negatives)),
    ]

    split_fields = [
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
    ]
    gap_fields = [
        "split_family",
        "split_name",
        "positive_support",
        "negative_support",
        "current_min_wilson95_lcb",
        "required_positive_support_for_95_if_all_correct",
        "required_negative_support_for_95_if_all_correct",
        "additional_positive_rows_needed_min",
        "additional_negative_rows_needed_min",
        "additional_pair_rows_needed_min",
    ]
    write_csv(OUT / "r6_staging_triplet_split_metrics_v1.csv", split_metrics, split_fields)
    write_csv(OUT / "r6_staging_triplet_split_gaps_v1.csv", split_gaps, gap_fields)
    write_csv(OUT / "r6_staging_triplet_sidecar_metrics_v1.csv", sidecar_metrics, ["axis", "successes", "total", "wilson95_lcb", "support_ok", "wilson_ok", "pass"])

    split_families: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in split_metrics:
        split_families[str(row["split_family"])].append(row)
    pooled_gate = bool(split_metrics[0]["pass"])
    chronological_gate = all(bool(row["pass"]) for row in split_families["chronological_group_split"])
    heldout_symbol_gate = all(bool(row["pass"]) for row in split_families["heldout_symbol_exact"])
    heldout_venue_gate = all(bool(row["pass"]) for row in split_families["heldout_venue_exact"])
    same_event_axis_gate = all(bool(row["pass"]) for row in sidecar_metrics)

    result = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "board_sha256_at_start": sha256(BOARD),
        "staging_root": str(STAGING_ROOT),
        "upstream_readback_root": rel(UPSTREAM_READBACK_ROOT),
        "verifier": verifier,
        "staging_hashes": {
            POSITIVE_NAME: sha256(STAGING_ROOT / POSITIVE_NAME),
            NEGATIVE_NAME: sha256(STAGING_ROOT / NEGATIVE_NAME),
            PROVENANCE_NAME: sha256(STAGING_ROOT / PROVENANCE_NAME),
        },
        "counts": {
            "positive_rows": len(positives),
            "matched_negative_rows": len(negatives),
            "matched_group_count": len(set(row.get("matched_negative_group_id", "") for row in positives)),
            "symbols": len(set(normalize(row.get("symbol", "")) for row in combined)),
            "venues": len(set(normalize(row.get("venue_or_market_center", "")) for row in combined)),
        },
        "provenance_summary": {
            "artifact_type": provenance.get("artifact_type"),
            "run_id": provenance.get("run_id"),
            "policy": provenance.get("policy"),
            "raw_data_committed": provenance.get("raw_data_committed"),
            "runtime_code_changed": provenance.get("runtime_code_changed"),
            "thresholds_relaxed": provenance.get("thresholds_relaxed"),
            "selected_source_row_ids": provenance.get("selected_source_row_ids", []),
        },
        "calibration": {
            "required_all_success_support_for_wilson95_ge_095": required_n,
            "pooled_min_wilson95_lcb": split_metrics[0]["min_wilson95_lcb"],
            "pooled_gate": pooled_gate,
            "same_event_control_seed_axis_gate": same_event_axis_gate,
            "chronological_split_gate": chronological_gate,
            "heldout_symbol_gate": heldout_symbol_gate,
            "heldout_venue_gate": heldout_venue_gate,
            "broad_normal_controls_present": False,
            "split_metrics_csv": rel(OUT / "r6_staging_triplet_split_metrics_v1.csv"),
            "split_gaps_csv": rel(OUT / "r6_staging_triplet_split_gaps_v1.csv"),
            "sidecar_metrics_csv": rel(OUT / "r6_staging_triplet_sidecar_metrics_v1.csv"),
            "gap_summary": family_summary(split_gaps),
        },
        "decision": {
            "gate_result": "r6_staging_triplet_split_calibration_after_035233_v1=staging_pooled95_pass_split_support_broad_controls_and_policy_blocked_no_promotion",
            "source_control_evidence_acquired": False,
            "accepted_rows_added": 0,
            "new_confidence_gate": False,
            "canonical_merge_allowed": False,
            "downstream_promotion_rerun_allowed": False,
            "strict_full_objective_achieved": False,
            "trade_usable": False,
            "update_goal": False,
            "runtime_code_changed": False,
            "thresholds_relaxed": False,
            "raw_data_committed": False,
            "source_roots_mutated": False,
            "shared_intake_mutated": False,
            "acceptance_blocker": "staging evidence is schema-ready and pooled95-pass, but chronological/heldout support, independent broad normal controls, explicit approval/canonical owner-export root, R3, and R5 remain blocked",
        },
        "next_action": "Do not promote this staging triplet. Acquire explicit approval or verifier-native owner/export rows plus source-owned broad normal controls, then rerun direct verifier, split calibration, provider/AutoQuant, Pre-Bayes/BBN, CatBoost/path-ranking, and execution-tree readback.",
    }
    write_json(OUT / "r6_staging_triplet_split_calibration_after_035233_v1.json", result)

    report = [
        "# R6 Staging Triplet Split Calibration After 035233 v1",
        "",
        f"Run id: `{RUN_ID}`",
        f"Gate result: `{result['decision']['gate_result']}`",
        "",
        "## Result",
        "",
        f"- Direct verifier status: `{verifier['payload'].get('status')}` with return code `{verifier['returncode']}`.",
        f"- Rows: positives `{len(positives)}`, matched controls `{len(negatives)}`, symbols `{result['counts']['symbols']}`, venues `{result['counts']['venues']}`.",
        f"- Pooled Wilson95 LCB: `{split_metrics[0]['min_wilson95_lcb']}`; pooled gate `{str(pooled_gate).lower()}`.",
        f"- Chronological gate `{str(chronological_gate).lower()}`, heldout-symbol gate `{str(heldout_symbol_gate).lower()}`, heldout-venue gate `{str(heldout_venue_gate).lower()}`.",
        "- Independent broad normal controls: `false`; canonical owner-export root: `absent`; new confidence gate: `false`; `update_goal=false`.",
        "",
        "## Boundary",
        "",
        "This run is read-only. It scores the staging triplet found by the inbox/readback loop and does not mutate canonical roots or shared tmp intake.",
    ]
    (OUT / "r6_staging_triplet_split_calibration_after_035233_v1.md").write_text("\n".join(report) + "\n", encoding="utf-8")

    assertions = [
        f"PASS gate_result={result['decision']['gate_result']}",
        f"PASS verifier_status={verifier['payload'].get('status')}",
        f"PASS positive_rows={len(positives)}",
        f"PASS matched_negative_rows={len(negatives)}",
        f"PASS pooled_gate={str(pooled_gate).lower()}",
        f"PASS chronological_split_gate={str(chronological_gate).lower()}",
        f"PASS heldout_symbol_gate={str(heldout_symbol_gate).lower()}",
        f"PASS heldout_venue_gate={str(heldout_venue_gate).lower()}",
        "PASS broad_normal_controls_present=false",
        "PASS source_control_evidence_acquired=false",
        "PASS accepted_rows_added=0",
        "PASS new_confidence_gate=false",
        "PASS canonical_merge_allowed=false",
        "PASS downstream_promotion_rerun_allowed=false",
        "PASS strict_full_objective_achieved=false",
        "PASS trade_usable=false",
        "PASS update_goal=false",
    ]
    (CHECKS / "r6_staging_triplet_split_calibration_after_035233_v1_assertions.out").write_text("\n".join(assertions) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
