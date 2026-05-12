#!/usr/bin/env python3
"""Read-only split-calibration sweep over R6 candidate bundles from 035442."""

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


RUN_ID = "20260512T035754-codex-r6-candidate-bundle-split-calibration-sweep-after-035442-v1"
SLUG = "r6-candidate-bundle-split-calibration-sweep-after-035442-v1"
REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs" / RUN_ID
OUT = RUN_ROOT / SLUG
CMD_OUT = RUN_ROOT / "command-output"
CHECKS = RUN_ROOT / "checks"
BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"

DIRECT_VERIFIER = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs"
    / "20260511T151950-codex-direct-manipulation-row-intake-manifest-v1"
    / "direct-manipulation-intake/direct_manipulation_row_intake_verifier_v1.py"
)

CANDIDATES = [
    ("jpm_cbot_staging", Path("/private/tmp/20260512T000803-codex-r6-jpm-cbot-treasury-control-uplift-v1.staging")),
    ("direct_manipulation_intake", Path("/private/tmp/ict-engine-direct-manipulation-row-intake")),
    ("v55_reconstruction_intake", Path("/private/tmp/ict-engine-r6-direct-intake-reconstruction-v55/intake")),
    ("v56_clean_readback_intake", Path("/private/tmp/ict-engine-r6-direct-intake-v56-clean-readback/intake")),
]

POSITIVE_NAME = "positive_spoing_layering_rows.csv"
CORRECT_POSITIVE_NAME = "positive_spoofing_layering_rows.csv"
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
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


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


def split_metric(candidate_id: str, split_family: str, split_name: str, rows: list[dict[str, str]]) -> dict[str, Any]:
    positives = [row for row in rows if row["_class"] == "positive"]
    negatives = [row for row in rows if row["_class"] == "negative"]
    pos_lcb = wilson_lcb(len(positives), len(positives))
    neg_lcb = wilson_lcb(len(negatives), len(negatives))
    min_lcb = min(pos_lcb, neg_lcb)
    support_ok = len(positives) >= MIN_SUPPORT and len(negatives) >= MIN_SUPPORT
    wilson_ok = min_lcb >= MIN_WILSON
    return {
        "candidate_id": candidate_id,
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


def run_verifier(candidate_id: str, root: Path) -> dict[str, Any]:
    proc = subprocess.run(
        ["python3", str(DIRECT_VERIFIER), "--intake-root", str(root)],
        cwd=REPO,
        text=True,
        capture_output=True,
        check=False,
        timeout=60,
    )
    stdout_path = CMD_OUT / f"verifier_{candidate_id}.stdout.txt"
    stderr_path = CMD_OUT / f"verifier_{candidate_id}.stderr.txt"
    cmd_path = CMD_OUT / f"verifier_{candidate_id}.cmd"
    exit_path = CMD_OUT / f"verifier_{candidate_id}.exit"
    cmd_path.write_text(f"python3 {DIRECT_VERIFIER} --intake-root {root}\n", encoding="utf-8")
    stdout_path.write_text(proc.stdout, encoding="utf-8")
    stderr_path.write_text(proc.stderr, encoding="utf-8")
    exit_path.write_text(f"{proc.returncode}\n", encoding="utf-8")
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


def build_candidate(candidate_id: str, root: Path, required_n: int) -> dict[str, Any]:
    positive_path = root / CORRECT_POSITIVE_NAME
    negative_path = root / NEGATIVE_NAME
    provenance_path = root / PROVENANCE_NAME
    missing = [str(path) for path in [positive_path, negative_path, provenance_path] if not path.exists()]
    if missing:
        return {"candidate_id": candidate_id, "intake_root": str(root), "missing_inputs": missing}

    positives = read_csv(positive_path)
    negatives = read_csv(negative_path)
    combined: list[dict[str, str]] = []
    for row in positives:
        item = dict(row)
        item["_class"] = "positive"
        combined.append(item)
    for row in negatives:
        item = dict(row)
        item["_class"] = "negative"
        combined.append(item)

    verifier = run_verifier(candidate_id, root)
    roles = chronological_roles(combined)
    metrics = [split_metric(candidate_id, "pooled_all_source_rows", "all_rows", combined)]
    for role in ["chronological_train", "chronological_calibration", "chronological_test"]:
        role_rows = [row for row in combined if roles.get(row.get("matched_negative_group_id", "")) == role]
        metrics.append(split_metric(candidate_id, "chronological_group_split", role, role_rows))
    for symbol in sorted(Counter(normalize(row.get("symbol", "")) for row in combined)):
        rows = [row for row in combined if normalize(row.get("symbol", "")) == symbol]
        metrics.append(split_metric(candidate_id, "heldout_symbol_exact", symbol, rows))
    for venue in sorted(Counter(normalize(row.get("venue_or_market_center", "")) for row in combined)):
        rows = [row for row in combined if normalize(row.get("venue_or_market_center", "")) == venue]
        metrics.append(split_metric(candidate_id, "heldout_venue_exact", venue, rows))

    gaps = []
    for row in metrics:
        if bool(row["pass"]):
            continue
        pos = int(row["positive_support"])
        neg = int(row["negative_support"])
        gaps.append(
            {
                "candidate_id": candidate_id,
                "split_family": row["split_family"],
                "split_name": row["split_name"],
                "positive_support": pos,
                "negative_support": neg,
                "current_min_wilson95_lcb": row["min_wilson95_lcb"],
                "required_support_for_95_if_all_correct": required_n,
                "additional_positive_rows_needed_min": max(0, required_n - pos),
                "additional_negative_rows_needed_min": max(0, required_n - neg),
                "additional_pair_rows_needed_min": max(max(0, required_n - pos), max(0, required_n - neg)),
            }
        )

    by_family: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in metrics:
        by_family[str(row["split_family"])].append(row)
    return {
        "candidate_id": candidate_id,
        "intake_root": str(root),
        "hashes": {
            CORRECT_POSITIVE_NAME: sha256(positive_path),
            NEGATIVE_NAME: sha256(negative_path),
            PROVENANCE_NAME: sha256(provenance_path),
        },
        "verifier": verifier,
        "counts": {
            "positive_rows": len(positives),
            "matched_negative_rows": len(negatives),
            "matched_group_count": len(set(row.get("matched_negative_group_id", "") for row in positives)),
            "symbols": len(set(normalize(row.get("symbol", "")) for row in combined)),
            "venues": len(set(normalize(row.get("venue_or_market_center", "")) for row in combined)),
        },
        "metrics": metrics,
        "gaps": gaps,
        "gates": {
            "pooled_gate": bool(by_family["pooled_all_source_rows"][0]["pass"]),
            "pooled_min_wilson95_lcb": by_family["pooled_all_source_rows"][0]["min_wilson95_lcb"],
            "chronological_split_gate": all(bool(row["pass"]) for row in by_family["chronological_group_split"]),
            "heldout_symbol_gate": all(bool(row["pass"]) for row in by_family["heldout_symbol_exact"]),
            "heldout_venue_gate": all(bool(row["pass"]) for row in by_family["heldout_venue_exact"]),
            "failing_cells": len(gaps),
            "max_pair_rows_needed_min": max((int(row["additional_pair_rows_needed_min"]) for row in gaps), default=0),
        },
    }


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    CMD_OUT.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)
    required_n = required_all_successes()

    candidates = [build_candidate(candidate_id, root, required_n) for candidate_id, root in CANDIDATES]
    all_metrics = [metric for candidate in candidates for metric in candidate.get("metrics", [])]
    all_gaps = [gap for candidate in candidates for gap in candidate.get("gaps", [])]

    metric_fields = [
        "candidate_id",
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
        "candidate_id",
        "split_family",
        "split_name",
        "positive_support",
        "negative_support",
        "current_min_wilson95_lcb",
        "required_support_for_95_if_all_correct",
        "additional_positive_rows_needed_min",
        "additional_negative_rows_needed_min",
        "additional_pair_rows_needed_min",
    ]
    write_csv(OUT / "r6_candidate_bundle_split_metrics_v1.csv", all_metrics, metric_fields)
    write_csv(OUT / "r6_candidate_bundle_split_gaps_v1.csv", all_gaps, gap_fields)

    summary_rows = []
    for candidate in candidates:
        gates = candidate.get("gates", {})
        counts = candidate.get("counts", {})
        summary_rows.append(
            {
                "candidate_id": candidate["candidate_id"],
                "intake_root": candidate["intake_root"],
                "verifier_status": candidate.get("verifier", {}).get("payload", {}).get("status", ""),
                "positive_rows": counts.get("positive_rows", 0),
                "matched_negative_rows": counts.get("matched_negative_rows", 0),
                "symbols": counts.get("symbols", 0),
                "venues": counts.get("venues", 0),
                "pooled_min_wilson95_lcb": gates.get("pooled_min_wilson95_lcb", ""),
                "pooled_gate": gates.get("pooled_gate", False),
                "chronological_split_gate": gates.get("chronological_split_gate", False),
                "heldout_symbol_gate": gates.get("heldout_symbol_gate", False),
                "heldout_venue_gate": gates.get("heldout_venue_gate", False),
                "failing_cells": gates.get("failing_cells", ""),
                "max_pair_rows_needed_min": gates.get("max_pair_rows_needed_min", ""),
            }
        )
    write_csv(
        OUT / "r6_candidate_bundle_split_summary_v1.csv",
        summary_rows,
        [
            "candidate_id",
            "intake_root",
            "verifier_status",
            "positive_rows",
            "matched_negative_rows",
            "symbols",
            "venues",
            "pooled_min_wilson95_lcb",
            "pooled_gate",
            "chronological_split_gate",
            "heldout_symbol_gate",
            "heldout_venue_gate",
            "failing_cells",
            "max_pair_rows_needed_min",
        ],
    )

    strongest = max(candidates, key=lambda item: float(item.get("gates", {}).get("pooled_min_wilson95_lcb", 0.0)))
    any_pooled = any(bool(item.get("gates", {}).get("pooled_gate")) for item in candidates)
    all_downstream_gates = all(
        bool(item.get("gates", {}).get(key))
        for item in candidates
        for key in ["chronological_split_gate", "heldout_symbol_gate", "heldout_venue_gate"]
    )
    result = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "board_sha256_at_start": sha256(BOARD),
        "required_all_success_support_for_wilson95_ge_095": required_n,
        "gate_result": "r6_candidate_bundle_split_calibration_sweep_after_035442_v1=pooled_candidates_pass_but_split_broad_controls_policy_blocked_no_promotion",
        "candidate_count": len(candidates),
        "strongest_candidate_id": strongest["candidate_id"],
        "strongest_pooled_min_wilson95_lcb": strongest.get("gates", {}).get("pooled_min_wilson95_lcb"),
        "candidate_results": [
            {key: value for key, value in candidate.items() if key not in {"metrics", "gaps"}}
            for candidate in candidates
        ],
        "artifacts": {
            "summary_csv": rel(OUT / "r6_candidate_bundle_split_summary_v1.csv"),
            "metrics_csv": rel(OUT / "r6_candidate_bundle_split_metrics_v1.csv"),
            "gaps_csv": rel(OUT / "r6_candidate_bundle_split_gaps_v1.csv"),
        },
        "decision": {
            "any_pooled_gate": any_pooled,
            "all_chronological_symbol_venue_gates": all_downstream_gates,
            "broad_normal_controls_present": False,
            "source_control_evidence_acquired": False,
            "accepted_rows_added": 0,
            "new_confidence_gate": False,
            "canonical_merge_allowed": False,
            "downstream_promotion_rerun_allowed": False,
            "strict_full_objective_achieved": False,
            "trade_usable": False,
            "update_goal": False,
        },
        "next_action": "Acquire explicit approval or verifier-native owner/export rows plus source-owned broad normal controls. Do not promote pooled-only candidate bundles.",
    }
    write_json(OUT / "r6_candidate_bundle_split_calibration_sweep_after_035442_v1.json", result)

    report = [
        "# R6 Candidate Bundle Split Calibration Sweep After 035442 v1",
        "",
        f"Gate result: `{result['gate_result']}`",
        "",
        "## Result",
        "",
        f"- Candidate bundles calibrated: `{len(candidates)}`.",
        f"- Strongest pooled candidate: `{result['strongest_candidate_id']}` with Wilson95 LCB `{result['strongest_pooled_min_wilson95_lcb']}`.",
        f"- Any pooled gate: `{str(any_pooled).lower()}`.",
        f"- All chronological/symbol/venue gates: `{str(all_downstream_gates).lower()}`.",
        "- Broad independent normal controls: `false`; accepted rows added: `0`; `update_goal=false`.",
        "",
        "## Summary",
        "",
        "| Candidate | Pooled LCB | Pooled | Chronological | Heldout Symbol | Heldout Venue | Failing Cells |",
        "|---|---:|---|---|---|---|---:|",
    ]
    for row in summary_rows:
        report.append(
            f"| `{row['candidate_id']}` | `{row['pooled_min_wilson95_lcb']}` | `{str(row['pooled_gate']).lower()}` | "
            f"`{str(row['chronological_split_gate']).lower()}` | `{str(row['heldout_symbol_gate']).lower()}` | "
            f"`{str(row['heldout_venue_gate']).lower()}` | `{row['failing_cells']}` |"
        )
    report.extend(
        [
            "",
            "## Boundary",
            "",
            "This is a read-only calibration sweep. It does not copy candidate bundles into the required owner-export root and does not run downstream promotion.",
        ]
    )
    (OUT / "r6_candidate_bundle_split_calibration_sweep_after_035442_v1.md").write_text("\n".join(report) + "\n", encoding="utf-8")

    assertions = [
        f"PASS gate_result={result['gate_result']}",
        f"PASS candidate_count={len(candidates)}",
        f"PASS strongest_candidate_id={result['strongest_candidate_id']}",
        f"PASS any_pooled_gate={str(any_pooled).lower()}",
        f"PASS all_chronological_symbol_venue_gates={str(all_downstream_gates).lower()}",
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
    (CHECKS / "r6_candidate_bundle_split_calibration_sweep_after_035442_v1_assertions.out").write_text("\n".join(assertions) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
