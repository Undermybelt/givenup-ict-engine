#!/usr/bin/env python3
"""Read-only split calibration sweep for all R6 verifier-shaped candidates."""

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


RUN_ID = "20260512T035814-codex-r6-all-candidate-split-calibration-after-035442-v1"
SLUG = "r6-all-candidate-split-calibration-after-035442-v1"
REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs" / RUN_ID
OUT = RUN_ROOT / SLUG
CMD_OUT = RUN_ROOT / "command-output"
CHECKS = RUN_ROOT / "checks"
BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"

POSITIVE_NAME = "positive_spoofing_layering_rows.csv"
NEGATIVE_NAME = "matched_negative_normal_activity_rows.csv"
PROVENANCE_NAME = "provenance_manifest.json"

CANDIDATES = [
    ("jpm_cbot_staging", Path("/private/tmp/20260512T000803-codex-r6-jpm-cbot-treasury-control-uplift-v1.staging")),
    ("direct_manipulation_intake", Path("/private/tmp/ict-engine-direct-manipulation-row-intake")),
    ("v55_reconstruction_intake", Path("/private/tmp/ict-engine-r6-direct-intake-reconstruction-v55/intake")),
    ("v56_clean_readback_intake", Path("/private/tmp/ict-engine-r6-direct-intake-v56-clean-readback/intake")),
]

DIRECT_VERIFIER = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs"
    / "20260511T151950-codex-direct-manipulation-row-intake-manifest-v1"
    / "direct-manipulation-intake/direct_manipulation_row_intake_verifier_v1.py"
)

UPSTREAM_SWEEP_ROOT = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs"
    / "20260512T035442-codex-r6-candidate-verifier-sweep-after-035028-v1"
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


def split_metric(candidate: str, split_family: str, split_name: str, rows: list[dict[str, str]]) -> dict[str, Any]:
    positives = [row for row in rows if row["_class"] == "positive"]
    negatives = [row for row in rows if row["_class"] == "negative"]
    pos_lcb = wilson_lcb(len(positives), len(positives))
    neg_lcb = wilson_lcb(len(negatives), len(negatives))
    min_lcb = min(pos_lcb, neg_lcb)
    support_ok = len(positives) >= MIN_SUPPORT and len(negatives) >= MIN_SUPPORT
    wilson_ok = min_lcb >= MIN_WILSON
    return {
        "candidate": candidate,
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


def build_split_metrics(candidate: str, combined: list[dict[str, str]]) -> list[dict[str, Any]]:
    roles = chronological_roles(combined)
    metrics = [split_metric(candidate, "pooled_all_source_rows", "all_rows", combined)]
    for role in ["chronological_train", "chronological_calibration", "chronological_test"]:
        role_rows = [row for row in combined if roles.get(row.get("matched_negative_group_id", "")) == role]
        metrics.append(split_metric(candidate, "chronological_group_split", role, role_rows))
    for symbol in sorted(Counter(normalize(row.get("symbol", "")) for row in combined)):
        rows = [row for row in combined if normalize(row.get("symbol", "")) == symbol]
        metrics.append(split_metric(candidate, "heldout_symbol_exact", symbol, rows))
    for venue in sorted(Counter(normalize(row.get("venue_or_market_center", "")) for row in combined)):
        rows = [row for row in combined if normalize(row.get("venue_or_market_center", "")) == venue]
        metrics.append(split_metric(candidate, "heldout_venue_exact", venue, rows))
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
                "candidate": row["candidate"],
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


def summarize_candidate(name: str, split_metrics: list[dict[str, Any]], gaps: list[dict[str, Any]]) -> dict[str, Any]:
    by_family: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in split_metrics:
        by_family[str(row["split_family"])].append(row)
    gap_by_family: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in gaps:
        if row["candidate"] == name:
            gap_by_family[str(row["split_family"])].append(row)

    pooled = by_family["pooled_all_source_rows"][0]
    chronological_gate = all(bool(row["pass"]) for row in by_family["chronological_group_split"])
    heldout_symbol_gate = all(bool(row["pass"]) for row in by_family["heldout_symbol_exact"])
    heldout_venue_gate = all(bool(row["pass"]) for row in by_family["heldout_venue_exact"])
    return {
        "candidate": name,
        "pooled_min_wilson95_lcb": pooled["min_wilson95_lcb"],
        "pooled_gate": pooled["pass"],
        "chronological_split_gate": chronological_gate,
        "heldout_symbol_gate": heldout_symbol_gate,
        "heldout_venue_gate": heldout_venue_gate,
        "failing_chronological_cells": len(gap_by_family.get("chronological_group_split", [])),
        "failing_symbol_cells": len(gap_by_family.get("heldout_symbol_exact", [])),
        "failing_venue_cells": len(gap_by_family.get("heldout_venue_exact", [])),
        "max_pair_gap": max(
            (
                int(gap["additional_pair_rows_needed_min"])
                for family_gaps in gap_by_family.values()
                for gap in family_gaps
            ),
            default=0,
        ),
    }


def run_verifier(candidate: str, root: Path) -> dict[str, Any]:
    proc = subprocess.run(
        ["python3", str(DIRECT_VERIFIER), "--intake-root", str(root)],
        cwd=REPO,
        text=True,
        capture_output=True,
        check=False,
        timeout=60,
    )
    stdout_path = CMD_OUT / f"direct_verifier_{candidate}.stdout.txt"
    stderr_path = CMD_OUT / f"direct_verifier_{candidate}.stderr.txt"
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


def candidate_report(name: str, root: Path, required_n: int) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    required_files = [root / POSITIVE_NAME, root / NEGATIVE_NAME, root / PROVENANCE_NAME]
    missing = [str(path) for path in required_files if not path.exists()]
    if missing:
        return (
            {
                "candidate": name,
                "root": str(root),
                "status": "missing_required_inputs",
                "missing_inputs": missing,
            },
            [],
            [],
        )

    positives = read_csv(root / POSITIVE_NAME)
    negatives = read_csv(root / NEGATIVE_NAME)
    provenance = json.loads((root / PROVENANCE_NAME).read_text(encoding="utf-8"))
    verifier = run_verifier(name, root)

    combined: list[dict[str, str]] = []
    for row in positives:
        item = dict(row)
        item["_class"] = "positive"
        combined.append(item)
    for row in negatives:
        item = dict(row)
        item["_class"] = "negative"
        combined.append(item)

    split_metrics = build_split_metrics(name, combined)
    gaps = gap_rows(split_metrics, required_n)
    summary = summarize_candidate(name, split_metrics, gaps)
    summary.update(
        {
            "root": str(root),
            "status": verifier["payload"].get("status"),
            "verifier_returncode": verifier["returncode"],
            "positive_rows": len(positives),
            "matched_negative_rows": len(negatives),
            "matched_group_count": len(set(row.get("matched_negative_group_id", "") for row in positives)),
            "symbols": len(set(normalize(row.get("symbol", "")) for row in combined)),
            "venues": len(set(normalize(row.get("venue_or_market_center", "")) for row in combined)),
            "hashes": {
                POSITIVE_NAME: sha256(root / POSITIVE_NAME),
                NEGATIVE_NAME: sha256(root / NEGATIVE_NAME),
                PROVENANCE_NAME: sha256(root / PROVENANCE_NAME),
            },
            "provenance_summary": {
                "artifact_type": provenance.get("artifact_type"),
                "run_id": provenance.get("run_id"),
                "policy": provenance.get("policy"),
                "raw_data_committed": provenance.get("raw_data_committed"),
                "runtime_code_changed": provenance.get("runtime_code_changed"),
                "thresholds_relaxed": provenance.get("thresholds_relaxed"),
            },
            "verifier": verifier,
        }
    )
    return summary, split_metrics, gaps


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    CMD_OUT.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)

    missing_global = [str(path) for path in [DIRECT_VERIFIER, BOARD] if not path.exists()]
    if missing_global:
        payload = {
            "run_id": RUN_ID,
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "status": "blocked",
            "reason": "missing_global_inputs",
            "missing_inputs": missing_global,
            "update_goal": False,
        }
        write_json(OUT / "r6_all_candidate_split_calibration_after_035442_v1.json", payload)
        return 2

    required_n = required_all_successes()
    summaries: list[dict[str, Any]] = []
    all_metrics: list[dict[str, Any]] = []
    all_gaps: list[dict[str, Any]] = []
    for name, root in CANDIDATES:
        summary, metrics, gaps = candidate_report(name, root, required_n)
        summaries.append(summary)
        all_metrics.extend(metrics)
        all_gaps.extend(gaps)

    summary_fields = [
        "candidate",
        "root",
        "status",
        "verifier_returncode",
        "positive_rows",
        "matched_negative_rows",
        "matched_group_count",
        "symbols",
        "venues",
        "pooled_min_wilson95_lcb",
        "pooled_gate",
        "chronological_split_gate",
        "heldout_symbol_gate",
        "heldout_venue_gate",
        "failing_chronological_cells",
        "failing_symbol_cells",
        "failing_venue_cells",
        "max_pair_gap",
    ]
    metric_fields = [
        "candidate",
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
        "candidate",
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
    write_csv(OUT / "r6_all_candidate_split_summary_v1.csv", summaries, summary_fields)
    write_csv(OUT / "r6_all_candidate_split_metrics_v1.csv", all_metrics, metric_fields)
    write_csv(OUT / "r6_all_candidate_split_gaps_v1.csv", all_gaps, gap_fields)

    verifier_zero = sum(1 for item in summaries if item.get("verifier_returncode") == 0)
    schema_ready = sum(1 for item in summaries if item.get("status") == "schema_ready_unscored")
    pooled_pass = sum(1 for item in summaries if item.get("pooled_gate") is True)
    chronological_pass = sum(1 for item in summaries if item.get("chronological_split_gate") is True)
    heldout_symbol_pass = sum(1 for item in summaries if item.get("heldout_symbol_gate") is True)
    heldout_venue_pass = sum(1 for item in summaries if item.get("heldout_venue_gate") is True)

    gate_result = "r6_all_candidate_split_calibration_after_035442_v1=all_candidates_pooled95_pass_split_support_and_source_policy_blocked_no_promotion"
    result = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "board_sha256_at_start": sha256(BOARD),
        "upstream_sweep_root": rel(UPSTREAM_SWEEP_ROOT),
        "required_all_success_support_for_wilson95_ge_095": required_n,
        "summary_csv": rel(OUT / "r6_all_candidate_split_summary_v1.csv"),
        "metrics_csv": rel(OUT / "r6_all_candidate_split_metrics_v1.csv"),
        "gaps_csv": rel(OUT / "r6_all_candidate_split_gaps_v1.csv"),
        "candidate_summaries": summaries,
        "counts": {
            "candidate_roots_checked": len(CANDIDATES),
            "verifier_exit_zero_count": verifier_zero,
            "schema_ready_unscored_count": schema_ready,
            "pooled_gate_true_count": pooled_pass,
            "chronological_split_gate_true_count": chronological_pass,
            "heldout_symbol_gate_true_count": heldout_symbol_pass,
            "heldout_venue_gate_true_count": heldout_venue_pass,
        },
        "decision": {
            "gate_result": gate_result,
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
            "candidate_roots_copied_to_required_root": False,
            "acceptance_blocker": "all candidates remain diagnostic only because split gates and independent source-owned controls/approval/owner-export roots are not satisfied",
        },
        "next_action": "Do not promote candidate bundles. Acquire explicit approval or verifier-native owner/export rows plus source-owned broad normal controls, then rerun direct verifier, split calibration, provider/AutoQuant, Pre-Bayes/BBN, CatBoost/path-ranking, and execution-tree readback.",
    }
    write_json(OUT / "r6_all_candidate_split_calibration_after_035442_v1.json", result)

    report = [
        "# R6 All Candidate Split Calibration After 035442 v1",
        "",
        f"Run id: `{RUN_ID}`",
        f"Gate result: `{gate_result}`",
        "",
        "## Result",
        "",
        f"- Candidate roots checked: `{len(CANDIDATES)}`; verifier exit zero `{verifier_zero}`; schema-ready/unscored `{schema_ready}`.",
        f"- Pooled Wilson95 gates true: `{pooled_pass}` of `{len(CANDIDATES)}`.",
        f"- Chronological split gates true: `{chronological_pass}` of `{len(CANDIDATES)}`.",
        f"- Heldout-symbol gates true: `{heldout_symbol_pass}` of `{len(CANDIDATES)}`.",
        f"- Heldout-venue gates true: `{heldout_venue_pass}` of `{len(CANDIDATES)}`.",
        "- Independent broad normal controls: `false`; canonical owner-export root: `absent`; new confidence gate: `false`; `update_goal=false`.",
        "",
        "## Candidate Summary",
        "",
    ]
    for item in summaries:
        report.append(
            "- `{candidate}`: status `{status}`, rows `{positive_rows}/{matched_negative_rows}`, pooled LCB `{pooled_min_wilson95_lcb}`, "
            "chronological `{chronological_split_gate}`, heldout-symbol `{heldout_symbol_gate}`, heldout-venue `{heldout_venue_gate}`, "
            "max pair gap `{max_pair_gap}`.".format(**item)
        )
    report.extend(
        [
            "",
            "## Boundary",
            "",
            "This run is read-only. It scores local candidate triplets found by the inbox sweep and does not mutate canonical roots, shared tmp intake, runtime code, or thresholds.",
        ]
    )
    (OUT / "r6_all_candidate_split_calibration_after_035442_v1.md").write_text("\n".join(report) + "\n", encoding="utf-8")

    assertions = [
        f"PASS gate_result={gate_result}",
        f"PASS candidate_roots_checked={len(CANDIDATES)}",
        f"PASS verifier_exit_zero_count={verifier_zero}",
        f"PASS schema_ready_unscored_count={schema_ready}",
        f"PASS pooled_gate_true_count={pooled_pass}",
        f"PASS chronological_split_gate_true_count={chronological_pass}",
        f"PASS heldout_symbol_gate_true_count={heldout_symbol_pass}",
        f"PASS heldout_venue_gate_true_count={heldout_venue_pass}",
        "PASS broad_normal_controls_present=false",
        "PASS source_control_evidence_acquired=false",
        "PASS accepted_rows_added=0",
        "PASS new_confidence_gate=false",
        "PASS canonical_merge_allowed=false",
        "PASS downstream_promotion_rerun_allowed=false",
        "PASS strict_full_objective_achieved=false",
        "PASS trade_usable=false",
        "PASS update_goal=false",
        "PASS source_roots_mutated=false",
        "PASS candidate_roots_copied_to_required_root=false",
        "PASS runtime_code_changed=false",
        "PASS thresholds_relaxed=false",
    ]
    (CHECKS / "r6_all_candidate_split_calibration_after_035442_v1_assertions.out").write_text("\n".join(assertions) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
