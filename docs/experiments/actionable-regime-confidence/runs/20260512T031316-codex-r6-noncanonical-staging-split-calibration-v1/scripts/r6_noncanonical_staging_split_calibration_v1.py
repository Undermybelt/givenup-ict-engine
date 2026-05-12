#!/usr/bin/env python3
"""Calibrate a noncanonical R6 staging intake without mutating live roots."""

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


RUN_ID = "20260512T031316-codex-r6-noncanonical-staging-split-calibration-v1"
REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs" / RUN_ID
OUT = RUN_ROOT / "r6-noncanonical-staging-split-calibration-v1"
CMD_OUT = RUN_ROOT / "command-output"
CHECKS = RUN_ROOT / "checks"
BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"

STAGING_ROOT = Path("/private/tmp/20260512T000803-codex-r6-jpm-cbot-treasury-control-uplift-v1.staging")
CANONICAL_OWNER_ROOT = Path("/tmp/ict-engine-board-a-r6-owner-export-v1")
POSITIVE_NAME = "positive_spoofing_layering_rows.csv"
NEGATIVE_NAME = "matched_negative_normal_activity_rows.csv"
PROVENANCE_NAME = "provenance_manifest.json"
DIRECT_VERIFIER = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs"
    / "20260511T151950-codex-direct-manipulation-row-intake-manifest-v1"
    / "direct-manipulation-intake/direct_manipulation_row_intake_verifier_v1.py"
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
    exit_path = CMD_OUT / "direct_manipulation_row_intake_verifier.exit"
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
        "exit_path": rel(exit_path),
    }


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    CMD_OUT.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)

    board_hash_before = sha256(BOARD)
    expected = [STAGING_ROOT / POSITIVE_NAME, STAGING_ROOT / NEGATIVE_NAME, STAGING_ROOT / PROVENANCE_NAME, DIRECT_VERIFIER]
    missing = [str(path) for path in expected if not path.exists()]
    if missing:
        result = {
            "run_id": RUN_ID,
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "board_sha256_at_start": board_hash_before,
            "gate_result": "r6_noncanonical_staging_split_calibration_v1=blocked_missing_required_inputs",
            "missing_inputs": missing,
            "accepted_rows_added": 0,
            "new_confidence_gate": False,
            "canonical_merge_allowed": False,
            "downstream_promotion_rerun_allowed": False,
            "strict_full_objective_achieved": False,
            "trade_usable": False,
            "update_goal": False,
        }
        write_json(OUT / "r6_noncanonical_staging_split_calibration_v1.json", result)
        return 2

    verifier = run_verifier(STAGING_ROOT)
    positives = read_csv(STAGING_ROOT / POSITIVE_NAME)
    negatives = read_csv(STAGING_ROOT / NEGATIVE_NAME)

    combined: list[dict[str, str]] = []
    for row in positives:
        item = dict(row)
        item["_class"] = "positive"
        combined.append(item)
    for row in negatives:
        item = dict(row)
        item["_class"] = "negative"
        combined.append(item)

    roles = chronological_roles(combined)
    split_metrics = [split_metric("pooled_all_source_rows", "all_rows", combined)]
    for role in ["chronological_train", "chronological_calibration", "chronological_test"]:
        rows = [row for row in combined if roles.get(row.get("matched_negative_group_id", "")) == role]
        split_metrics.append(split_metric("chronological_group_split", role, rows))
    for symbol in sorted(Counter(normalize(row.get("symbol", "")) for row in combined)):
        rows = [row for row in combined if normalize(row.get("symbol", "")) == symbol]
        split_metrics.append(split_metric("heldout_symbol_exact", symbol, rows))
    for venue in sorted(Counter(normalize(row.get("venue_or_market_center", "")) for row in combined)):
        rows = [row for row in combined if normalize(row.get("venue_or_market_center", "")) == venue]
        split_metrics.append(split_metric("heldout_venue_exact", venue, rows))

    metrics_path = OUT / "r6_noncanonical_staging_split_metrics_v1.csv"
    write_csv(
        metrics_path,
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

    group_counts = {
        gid: Counter(row["_class"] for row in rows)
        for gid, rows in grouped(combined).items()
    }
    unmatched_groups = sorted(
        gid
        for gid, counts in group_counts.items()
        if counts.get("positive", 0) == 0 or counts.get("negative", 0) == 0
    )
    symbol_summary = [
        {
            "axis": "symbol",
            "name": name,
            "positive_rows": sum(1 for row in positives if normalize(row.get("symbol", "")) == name),
            "negative_rows": sum(1 for row in negatives if normalize(row.get("symbol", "")) == name),
        }
        for name in sorted(Counter(normalize(row.get("symbol", "")) for row in combined))
    ]
    venue_summary = [
        {
            "axis": "venue_or_market_center",
            "name": name,
            "positive_rows": sum(1 for row in positives if normalize(row.get("venue_or_market_center", "")) == name),
            "negative_rows": sum(1 for row in negatives if normalize(row.get("venue_or_market_center", "")) == name),
        }
        for name in sorted(Counter(normalize(row.get("venue_or_market_center", "")) for row in combined))
    ]
    summary_path = OUT / "r6_noncanonical_staging_axis_summary_v1.csv"
    write_csv(summary_path, symbol_summary + venue_summary, ["axis", "name", "positive_rows", "negative_rows"])

    split_families = defaultdict(list)
    for row in split_metrics:
        split_families[row["split_family"]].append(row)
    pooled_gate = bool(split_metrics[0]["pass"])
    chronological_gate = all(row["pass"] for row in split_families["chronological_group_split"])
    heldout_symbol_gate = all(row["pass"] for row in split_families["heldout_symbol_exact"])
    heldout_venue_gate = all(row["pass"] for row in split_families["heldout_venue_exact"])
    split_gate = chronological_gate and heldout_symbol_gate and heldout_venue_gate

    result = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "board_sha256_at_start": board_hash_before,
        "gate_result": "r6_noncanonical_staging_split_calibration_v1=noncanonical_schema_ready_pooled_pass_split_support_fails_no_promotion",
        "staging_root": str(STAGING_ROOT),
        "canonical_owner_root": str(CANONICAL_OWNER_ROOT),
        "canonical_owner_root_exists": CANONICAL_OWNER_ROOT.exists(),
        "canonical_owner_root_mutated": False,
        "source_files": {
            POSITIVE_NAME: sha256(STAGING_ROOT / POSITIVE_NAME),
            NEGATIVE_NAME: sha256(STAGING_ROOT / NEGATIVE_NAME),
            PROVENANCE_NAME: sha256(STAGING_ROOT / PROVENANCE_NAME),
        },
        "verifier": verifier,
        "counts": {
            "positive_rows": len(positives),
            "matched_negative_rows": len(negatives),
            "matched_group_count": len(group_counts),
            "unmatched_group_count": len(unmatched_groups),
            "symbol_count": len(symbol_summary),
            "venue_count": len(venue_summary),
        },
        "calibration": {
            "pooled_gate": pooled_gate,
            "chronological_split_gate": chronological_gate,
            "heldout_symbol_gate": heldout_symbol_gate,
            "heldout_venue_gate": heldout_venue_gate,
            "combined_split_gate": split_gate,
            "split_metrics_csv": rel(metrics_path),
            "axis_summary_csv": rel(summary_path),
        },
        "promotion": {
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
        },
        "next_action": "Keep the canonical R6 owner-export blocker open; require owner/operator export or explicit FLIP approval before canonical merge/downstream rerun.",
    }
    write_json(OUT / "r6_noncanonical_staging_split_calibration_v1.json", result)

    report = [
        "# R6 Noncanonical Staging Split Calibration v1",
        "",
        f"Run id: `{RUN_ID}`",
        f"Generated at UTC: `{result['generated_at_utc']}`",
        "",
        "## Result",
        "",
        f"- Gate result: `{result['gate_result']}`.",
        f"- Verifier status: `{verifier['payload'].get('status')}` with return code `{verifier['returncode']}`.",
        f"- Staging rows: positives `{len(positives)}`, matched negatives `{len(negatives)}`, groups `{len(group_counts)}`.",
        f"- Pooled gate: `{str(pooled_gate).lower()}`; chronological split gate: `{str(chronological_gate).lower()}`; heldout symbol gate: `{str(heldout_symbol_gate).lower()}`; heldout venue gate: `{str(heldout_venue_gate).lower()}`.",
        f"- Canonical owner root mutated: `false`; canonical owner root exists: `{str(CANONICAL_OWNER_ROOT.exists()).lower()}`.",
        "- Accepted rows added: `0`; new confidence gate: `false`; canonical merge allowed: `false`; downstream promotion rerun allowed: `false`; `update_goal=false`.",
        "",
        "## Boundary",
        "",
        "This is a noncanonical staging readback. It records hashes and metrics only, leaves `/tmp/ict-engine-board-a-r6-owner-export-v1` untouched, and does not promote the staging files as owner-approved controls.",
    ]
    (OUT / "r6_noncanonical_staging_split_calibration_v1.md").write_text("\n".join(report) + "\n", encoding="utf-8")

    assertions = [
        f"run_id={RUN_ID}",
        f"board_sha256_at_start={board_hash_before}",
        f"verifier_status={verifier['payload'].get('status')}",
        f"verifier_returncode={verifier['returncode']}",
        f"positive_rows={len(positives)}",
        f"matched_negative_rows={len(negatives)}",
        f"matched_group_count={len(group_counts)}",
        f"pooled_gate={str(pooled_gate).lower()}",
        f"chronological_split_gate={str(chronological_gate).lower()}",
        f"heldout_symbol_gate={str(heldout_symbol_gate).lower()}",
        f"heldout_venue_gate={str(heldout_venue_gate).lower()}",
        "canonical_owner_root_mutated=false",
        "accepted_rows_added=0",
        "new_confidence_gate=false",
        "canonical_merge_allowed=false",
        "downstream_promotion_rerun_allowed=false",
        "strict_full_objective_achieved=false",
        "trade_usable=false",
        "update_goal=false",
        "assertion_status=PASS",
    ]
    (CHECKS / "r6_noncanonical_staging_split_calibration_v1_assertions.out").write_text("\n".join(assertions) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
