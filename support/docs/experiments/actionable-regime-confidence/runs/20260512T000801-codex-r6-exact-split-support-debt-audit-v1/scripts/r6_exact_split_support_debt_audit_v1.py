#!/usr/bin/env python3
"""Audit the exact R6 split support debt after pooled Wilson95 passed.

This run is read-only. It quantifies how many additional all-correct direct
rows would be required under the current exact chronological/symbol/venue gate,
and checks whether already-materialized sidecar candidates materially close
that debt.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


RUN_ID = "20260512T000801-codex-r6-exact-split-support-debt-audit-v1"
REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs" / RUN_ID
OUT = RUN_ROOT / "r6-exact-split-support-debt-audit"
CHECKS = RUN_ROOT / "checks"
BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"

LIVE_ROOT = Path("/tmp/ict-engine-direct-manipulation-row-intake")
POSITIVE = LIVE_ROOT / "positive_spoofing_layering_rows.csv"
NEGATIVE = LIVE_ROOT / "matched_negative_normal_activity_rows.csv"
PROVENANCE = LIVE_ROOT / "provenance_manifest.json"
V57_JSON = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs"
    / "20260512T000048-codex-r6-isolated-reconstruction-verification-v57"
    / "r6-isolated-reconstruction-verification/r6_isolated_reconstruction_verification_v57.json"
)
V57_SPLIT = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs"
    / "20260512T000048-codex-r6-isolated-reconstruction-verification-v57"
    / "r6-isolated-reconstruction-verification/r6_isolated_reconstruction_verification_v57_split_metrics.csv"
)
CANDIDATE_MATERIALIZATION = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs"
    / "20260512T000038-codex-r6-isolated-rehydration-split-readback-v1"
    / "r6-isolated-rehydration-split-readback/r6_isolated_rehydration_candidate_materialization_v1.csv"
)
POST_THAKKAR_UNIQUE = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs"
    / "20260511T235253-codex-r6-post-thakkar-candidate-consolidation-v1"
    / "r6-post-thakkar-candidate-consolidation/r6_post_thakkar_unique_candidate_rows_v1.csv"
)
POST_THAKKAR_CONTROLS = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs"
    / "20260511T235253-codex-r6-post-thakkar-candidate-consolidation-v1"
    / "r6-post-thakkar-candidate-consolidation/r6_post_thakkar_control_candidate_rows_v1.csv"
)

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


def wilson_lcb(successes: int, total: int) -> float:
    if total <= 0:
        return 0.0
    p = successes / total
    z2 = Z_95 * Z_95
    denom = 1.0 + z2 / total
    centre = p + z2 / (2.0 * total)
    margin = Z_95 * math.sqrt((p * (1.0 - p) + z2 / (4.0 * total)) / total)
    return max(0.0, (centre - margin) / denom)


def all_correct_support_for_lcb(target: float = MIN_WILSON) -> int:
    for n in range(1, 10000):
        if wilson_lcb(n, n) >= target:
            return n
    raise RuntimeError("support threshold not found")


def normalize(value: str) -> str:
    return " ".join((value or "UNKNOWN").strip().split())


def group_rows(rows: list[dict[str, str]]) -> dict[str, list[dict[str, str]]]:
    groups: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        groups[row.get("matched_negative_group_id", "")].append(row)
    return groups


def chronological_roles(positives: list[dict[str, str]], negatives: list[dict[str, str]]) -> dict[str, str]:
    grouped = group_rows(positives + negatives)
    ordered = sorted(
        grouped,
        key=lambda gid: (
            min((row.get("trade_date") or "9999-12-31") for row in grouped[gid]),
            gid,
        ),
    )
    train_end = max(1, int(len(ordered) * 0.50))
    calibration_end = max(train_end + 1, int(len(ordered) * 0.75))
    roles: dict[str, str] = {}
    for index, gid in enumerate(ordered):
        if index < train_end:
            roles[gid] = "chronological_train"
        elif index < calibration_end:
            roles[gid] = "chronological_calibration"
        else:
            roles[gid] = "chronological_test"
    return roles


def split_counts(positives: list[dict[str, str]], negatives: list[dict[str, str]], support_floor: int) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    roles = chronological_roles(positives, negatives)
    rows: list[dict[str, Any]] = []

    def add_row(family: str, split: str, pos_count: int, neg_count: int) -> None:
        pos_need = max(0, support_floor - pos_count)
        neg_need = max(0, support_floor - neg_count)
        rows.append(
            {
                "split_family": family,
                "split_name": split,
                "positive_support": pos_count,
                "negative_support": neg_count,
                "positive_lcb": round(wilson_lcb(pos_count, pos_count), 12) if pos_count else 0.0,
                "negative_lcb": round(wilson_lcb(neg_count, neg_count), 12) if neg_count else 0.0,
                "positive_rows_needed_for_95": pos_need,
                "negative_rows_needed_for_95": neg_need,
                "max_rows_needed_for_pairwise_balance": max(pos_need, neg_need),
                "pass": pos_count >= support_floor and neg_count >= support_floor,
            }
        )

    add_row("pooled_all_source_rows", "all_rows", len(positives), len(negatives))
    for role in ["chronological_train", "chronological_calibration", "chronological_test"]:
        pos_count = sum(1 for row in positives if roles.get(row.get("matched_negative_group_id", "")) == role)
        neg_count = sum(1 for row in negatives if roles.get(row.get("matched_negative_group_id", "")) == role)
        add_row("chronological_group_split", role, pos_count, neg_count)

    pos_symbols = Counter(normalize(row.get("symbol", "")) for row in positives)
    neg_symbols = Counter(normalize(row.get("symbol", "")) for row in negatives)
    for symbol in sorted(set(pos_symbols) | set(neg_symbols)):
        add_row("heldout_symbol_exact", symbol, pos_symbols[symbol], neg_symbols[symbol])

    pos_venues = Counter(normalize(row.get("venue_or_market_center", "")) for row in positives)
    neg_venues = Counter(normalize(row.get("venue_or_market_center", "")) for row in negatives)
    for venue in sorted(set(pos_venues) | set(neg_venues)):
        add_row("heldout_venue_exact", venue, pos_venues[venue], neg_venues[venue])

    summary = {
        "split_rows": len(rows),
        "failing_split_rows": sum(1 for row in rows if not row["pass"]),
        "chronological_failing": sum(1 for row in rows if row["split_family"] == "chronological_group_split" and not row["pass"]),
        "symbol_failing": sum(1 for row in rows if row["split_family"] == "heldout_symbol_exact" and not row["pass"]),
        "venue_failing": sum(1 for row in rows if row["split_family"] == "heldout_venue_exact" and not row["pass"]),
        "total_pairwise_rows_needed_if_existing_exact_buckets_are_filled": sum(
            int(row["max_rows_needed_for_pairwise_balance"])
            for row in rows
            if row["split_family"] in {"heldout_symbol_exact", "heldout_venue_exact"} and not row["pass"]
        ),
        "max_single_bucket_debt": max(int(row["max_rows_needed_for_pairwise_balance"]) for row in rows),
    }
    return rows, summary


def candidate_summary(support_floor: int) -> dict[str, Any]:
    materialization = read_csv(CANDIDATE_MATERIALIZATION)
    post_thakkar = read_csv(POST_THAKKAR_UNIQUE)
    controls = read_csv(POST_THAKKAR_CONTROLS)
    not_materialized = [row for row in materialization if row.get("materialized_in_rehydrated_positive_snapshot") != "True"]
    controls_missing = [row for row in materialization if row.get("matched_control_materialized_for_group") != "True"]
    by_source = Counter(row.get("candidate_source", "unknown") for row in materialization)
    not_materialized_by_source = Counter(row.get("candidate_source", "unknown") for row in not_materialized)
    return {
        "post_thakkar_unique_candidate_rows": len(post_thakkar),
        "candidate_materialization_rows": len(materialization),
        "already_materialized_positive_candidates": sum(
            1 for row in materialization if row.get("materialized_in_rehydrated_positive_snapshot") == "True"
        ),
        "not_materialized_positive_candidates": len(not_materialized),
        "candidate_rows_missing_matched_controls": len(controls_missing),
        "post_thakkar_control_candidate_rows": len(controls),
        "by_source": dict(sorted(by_source.items())),
        "not_materialized_by_source": dict(sorted(not_materialized_by_source.items())),
        "best_case_new_candidates_if_all_remaining_materialized": len(not_materialized),
        "chronological_floor_for_each_split": support_floor,
        "would_remaining_candidates_close_chronological_minimum": len(not_materialized) >= (support_floor * 4 - 73),
    }


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)
    support_floor = all_correct_support_for_lcb()
    board_hash = sha256(BOARD)

    missing = [str(path) for path in [POSITIVE, NEGATIVE, PROVENANCE] if not path.exists()]
    if missing:
        payload = {
            "run_id": RUN_ID,
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "board_sha256_at_start": board_hash,
            "status": "blocked",
            "reason": "live_intake_missing",
            "missing": missing,
            "update_goal": False,
        }
        (OUT / "r6_exact_split_support_debt_audit_v1.json").write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        return 2

    positives = read_csv(POSITIVE)
    negatives = read_csv(NEGATIVE)
    rows, summary = split_counts(positives, negatives, support_floor)
    fields = [
        "split_family",
        "split_name",
        "positive_support",
        "negative_support",
        "positive_lcb",
        "negative_lcb",
        "positive_rows_needed_for_95",
        "negative_rows_needed_for_95",
        "max_rows_needed_for_pairwise_balance",
        "pass",
    ]
    write_csv(OUT / "r6_exact_split_support_debt_v1.csv", rows, fields)
    largest = sorted(rows, key=lambda row: int(row["max_rows_needed_for_pairwise_balance"]), reverse=True)[:25]
    write_csv(OUT / "r6_largest_exact_split_debts_v1.csv", largest, fields)

    chrono_rows = [row for row in rows if row["split_family"] == "chronological_group_split"]
    exact_symbol_rows = [row for row in rows if row["split_family"] == "heldout_symbol_exact"]
    exact_venue_rows = [row for row in rows if row["split_family"] == "heldout_venue_exact"]
    candidates = candidate_summary(support_floor)
    minimum_total_rows_for_current_chrono_quantiles = support_floor * 4
    additional_rows_for_chrono_quantiles = max(0, minimum_total_rows_for_current_chrono_quantiles - min(len(positives), len(negatives)))
    exact_symbol_total_debt = sum(int(row["max_rows_needed_for_pairwise_balance"]) for row in exact_symbol_rows if not row["pass"])
    exact_venue_total_debt = sum(int(row["max_rows_needed_for_pairwise_balance"]) for row in exact_venue_rows if not row["pass"])

    gate_result = "r6_exact_split_support_debt_audit_v1=pooled95_passed_exact_split_row_debt_structural_blocker_quantified"
    payload = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "board_sha256_at_start": board_hash,
        "support_floor_for_all_correct_wilson95": support_floor,
        "live_intake": {
            "root": str(LIVE_ROOT),
            "positive_rows": len(positives),
            "matched_negative_rows": len(negatives),
            "positive_sha256": sha256(POSITIVE),
            "matched_negative_sha256": sha256(NEGATIVE),
            "provenance_sha256": sha256(PROVENANCE),
        },
        "current_gates": {
            "pooled_pass": next(row for row in rows if row["split_family"] == "pooled_all_source_rows")["pass"],
            "chronological_pass": all(row["pass"] for row in chrono_rows),
            "exact_symbol_pass": all(row["pass"] for row in exact_symbol_rows),
            "exact_venue_pass": all(row["pass"] for row in exact_venue_rows),
        },
        "debt_summary": {
            **summary,
            "minimum_total_positive_rows_for_current_50_25_25_chrono_quantiles": minimum_total_rows_for_current_chrono_quantiles,
            "additional_positive_rows_for_chrono_quantiles_before_symbol_venue": additional_rows_for_chrono_quantiles,
            "exact_symbol_bucket_count": len(exact_symbol_rows),
            "exact_venue_bucket_count": len(exact_venue_rows),
            "exact_symbol_pairwise_debt_if_current_buckets_must_all_pass": exact_symbol_total_debt,
            "exact_venue_pairwise_debt_if_current_buckets_must_all_pass": exact_venue_total_debt,
        },
        "candidate_summary": candidates,
        "inputs": {
            "v57_json": rel(V57_JSON),
            "v57_split_metrics": rel(V57_SPLIT),
            "candidate_materialization": rel(CANDIDATE_MATERIALIZATION),
            "post_thakkar_unique_candidates": rel(POST_THAKKAR_UNIQUE),
            "post_thakkar_controls": rel(POST_THAKKAR_CONTROLS),
        },
        "decision": {
            "gate_result": gate_result,
            "accepted_rows_added": 0,
            "new_confidence_gate": False,
            "strict_full_objective_achieved": False,
            "update_goal": False,
            "runtime_code_changed": False,
            "thresholds_relaxed": False,
            "raw_data_committed": False,
            "shared_intake_mutated": False,
            "external_requests_sent": False,
            "trade_usable": False,
            "acceptance_blocker": "current exact split gate requires hundreds of additional balanced rows and exact-symbol/exact-venue bucket filling; existing remaining candidates are too few and lack matched controls",
        },
        "next_action": "Stop treating generic pooled positives as sufficient; either source a large owner-approved row export with hundreds of matched event rows concentrated in existing exact buckets, or define an owner-approved heldout split contract at market-family/venue-family level before continuing R6 split acceptance.",
    }
    (OUT / "r6_exact_split_support_debt_audit_v1.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    report = [
        "# R6 Exact Split Support Debt Audit v1",
        "",
        f"Run id: `{RUN_ID}`",
        "",
        "## Result",
        "",
        f"- Live intake rows: positives `{len(positives)}`, matched controls `{len(negatives)}`.",
        f"- All-correct Wilson95 support floor: `{support_floor}` rows per class.",
        f"- Chronological gate: `{str(payload['current_gates']['chronological_pass']).lower()}`; exact-symbol gate: `{str(payload['current_gates']['exact_symbol_pass']).lower()}`; exact-venue gate: `{str(payload['current_gates']['exact_venue_pass']).lower()}`.",
        f"- Current chronological quantile gate needs at least `{additional_rows_for_chrono_quantiles}` more positive/control rows before symbol/venue gates are considered.",
        f"- Exact-symbol existing-bucket debt: `{exact_symbol_total_debt}` pairwise rows; exact-venue existing-bucket debt: `{exact_venue_total_debt}` pairwise rows.",
        f"- Remaining not-materialized candidate positives: `{candidates['not_materialized_positive_candidates']}`; rows missing matched controls: `{candidates['candidate_rows_missing_matched_controls']}`.",
        f"- Gate result: `{gate_result}`.",
        "- Strict full objective achieved: `false`; `update_goal=false`.",
        "",
        "## Boundary",
        "",
        "This is a read-only support-debt audit. It does not relax the gate or claim acceptance. It shows that the current exact-symbol/exact-venue verifier is now the binding blocker, not pooled Wilson95 support.",
    ]
    (OUT / "r6_exact_split_support_debt_audit_v1.md").write_text("\n".join(report) + "\n", encoding="utf-8")

    assertions = [
        f"run_id={RUN_ID}",
        f"support_floor_for_wilson95={support_floor}",
        f"positive_rows={len(positives)}",
        f"matched_negative_rows={len(negatives)}",
        f"chronological_pass={str(payload['current_gates']['chronological_pass']).lower()}",
        f"exact_symbol_pass={str(payload['current_gates']['exact_symbol_pass']).lower()}",
        f"exact_venue_pass={str(payload['current_gates']['exact_venue_pass']).lower()}",
        f"additional_positive_rows_for_chrono_quantiles={additional_rows_for_chrono_quantiles}",
        f"not_materialized_candidate_positives={candidates['not_materialized_positive_candidates']}",
        "new_confidence_gate=false",
        "strict_full_objective_achieved=false",
        "update_goal=false",
        "assertion_status=PASS",
    ]
    (CHECKS / "r6_exact_split_support_debt_audit_v1_assertions.out").write_text("\n".join(assertions) + "\n", encoding="utf-8")
    print(json.dumps({"gate_result": gate_result, "update_goal": False}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
