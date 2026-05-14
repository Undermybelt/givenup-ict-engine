#!/usr/bin/env python3
"""Decompose why source-label equivalence confidence remains below 95%."""

from __future__ import annotations

import csv
import hashlib
import json
import math
import re
from pathlib import Path
from typing import Any


RUN_ID = "20260512T011529-codex-source-label-confidence-gap-decomposition-v1"
BASE = Path("docs/experiments/actionable-regime-confidence/runs")
BOARD = Path("docs/plans/2026-05-10-actionable-regime-confidence-todo.md")

SOURCE_RUN = BASE / "20260512T010053-codex-source-label-equivalence-reconstruction-v1"
SOURCE_DIR = SOURCE_RUN / "source-label-equivalence-reconstruction"
SOURCE_JSON = SOURCE_DIR / "source_label_equivalence_reconstruction_v1.json"
LABEL_SPLIT_CSV = SOURCE_DIR / "source_label_equivalence_reconstruction_label_split_v1.csv"
OWNER_CSV = SOURCE_DIR / "source_label_equivalence_reconstruction_owner_v1.csv"
MARKET_CSV = SOURCE_DIR / "source_label_equivalence_reconstruction_market_v1.csv"
GATES_CSV = SOURCE_DIR / "source_label_equivalence_reconstruction_gates_v1.csv"

ROOT_PRESENCE_RUN = BASE / "20260512T010855-codex-source-root-presence-readback-v1"
ACCESS_RUN = BASE / "20260512T010212-codex-r6-owner-export-access-route-preflight-v1"

OUT_ROOT = BASE / RUN_ID
OUT_DIR = OUT_ROOT / "source-label-confidence-gap-decomposition-v1"
CHECK_DIR = OUT_ROOT / "checks"

CONFIDENCE_THRESHOLD = 0.95
WILSON_THRESHOLD = 0.95
Z95 = 1.959963984540054
ROOT_LABELS = ["Bear", "Bull", "Crisis", "Sideways"]
REQUIRED_SPLITS = ["calibration", "heldout_market", "heldout_time", "test"]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def board_cursor_and_hash() -> tuple[str, str]:
    raw = BOARD.read_bytes()
    text = raw.decode("utf-8")
    match = re.search(r"\| last_loop_id \| ([^|]+) \|", text)
    cursor = match.group(1).strip() if match else "missing"
    return cursor, hashlib.sha256(raw).hexdigest()


def wilson_lcb(successes: int, total: int) -> float:
    if total <= 0:
        return 0.0
    p = successes / total
    denom = 1 + Z95 * Z95 / total
    center = p + Z95 * Z95 / (2 * total)
    radius = Z95 * math.sqrt((p * (1 - p) + Z95 * Z95 / (4 * total)) / total)
    return (center - radius) / denom


def successes_needed_within_support(total: int) -> int | None:
    if total <= 0:
        return None
    lo, hi = 0, total
    answer: int | None = None
    while lo <= hi:
        mid = (lo + hi) // 2
        if wilson_lcb(mid, total) >= WILSON_THRESHOLD:
            answer = mid
            hi = mid - 1
        else:
            lo = mid + 1
    return answer


def added_high_conf_rows_needed(successes: int, total: int) -> int:
    if wilson_lcb(successes, total) >= WILSON_THRESHOLD:
        return 0
    lo, hi = 0, 1
    while wilson_lcb(successes + hi, total + hi) < WILSON_THRESHOLD:
        hi *= 2
    while lo < hi:
        mid = (lo + hi) // 2
        if wilson_lcb(successes + mid, total + mid) >= WILSON_THRESHOLD:
            hi = mid
        else:
            lo = mid + 1
    return lo


def split_gap_rows(label_split_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in label_split_rows:
        label = row["label"]
        split = row["split_role"]
        support = int(row["support"])
        successes = int(row["rows_at_or_above_0_95"])
        current_wilson = float(row["wilson95_lcb"])
        needed_within = successes_needed_within_support(support)
        if needed_within is None:
            additional_existing_successes_needed = ""
            needed_share_within_support = ""
        else:
            additional_existing_successes_needed = max(0, needed_within - successes)
            needed_share_within_support = round(needed_within / support, 10)
        rows.append(
            {
                "label": label,
                "split_role": split,
                "support": support,
                "rows_at_or_above_0_95": successes,
                "share_at_or_above_0_95": row["share_at_or_above_0_95"],
                "wilson95_lcb": row["wilson95_lcb"],
                "confidence_median": row["confidence_median"],
                "confidence_mean": row["confidence_mean"],
                "passes_wilson95": str(current_wilson >= WILSON_THRESHOLD).lower(),
                "successes_needed_within_current_support": needed_within if needed_within is not None else "",
                "additional_existing_successes_needed": additional_existing_successes_needed,
                "needed_share_within_current_support": needed_share_within_support,
                "new_perfect_rows_needed_if_added": added_high_conf_rows_needed(successes, support),
                "blocker": "" if current_wilson >= WILSON_THRESHOLD else "source_confidence_wilson95_below_0.95",
            }
        )
    return rows


def label_summary_rows(gap_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for label in ROOT_LABELS:
        subset = [row for row in gap_rows if row["label"] == label]
        worst = min(subset, key=lambda row: float(row["wilson95_lcb"]))
        total_support = sum(int(row["support"]) for row in subset)
        total_successes = sum(int(row["rows_at_or_above_0_95"]) for row in subset)
        max_wilson = max(float(row["wilson95_lcb"]) for row in subset)
        rows.append(
            {
                "label": label,
                "accepted_source_confidence_95": "false",
                "total_support_across_required_splits": total_support,
                "total_rows_at_or_above_0_95": total_successes,
                "worst_split": worst["split_role"],
                "worst_wilson95_lcb": worst["wilson95_lcb"],
                "best_wilson95_lcb": round(max_wilson, 10),
                "blocking_splits": ";".join(row["split_role"] for row in subset if row["blocker"]),
                "largest_per_split_new_perfect_rows_needed": max(int(row["new_perfect_rows_needed_if_added"]) for row in subset),
                "diagnosis": "confidence_quality_blocked_not_support_blocked",
            }
        )
    return rows


def weakest_owner_market_rows(owner_rows: list[dict[str, str]], market_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for source, input_rows in [("owner", owner_rows), ("market_family", market_rows)]:
        for row in input_rows:
            support = int(row["support"])
            successes = int(row["rows_at_or_above_0_95"])
            rows.append(
                {
                    "axis": source,
                    "label": row["label"],
                    "source_owner": row.get("source_owner", ""),
                    "market_family": row.get("market_family", ""),
                    "support": support,
                    "rows_at_or_above_0_95": successes,
                    "share_at_or_above_0_95": row["share_at_or_above_0_95"],
                    "wilson95_lcb": row["wilson95_lcb"],
                    "confidence_median": row["confidence_median"],
                    "confidence_mean": row["confidence_mean"],
                    "new_perfect_rows_needed_if_added": added_high_conf_rows_needed(successes, support),
                }
            )
    return rows


def md_table(rows: list[dict[str, Any]], fields: list[str]) -> str:
    lines = [
        "| " + " | ".join(fields) + " |",
        "| " + " | ".join(["---"] * len(fields)) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(row.get(field, "")).replace("|", "/") for field in fields) + " |")
    return "\n".join(lines)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)

    source = json.loads(SOURCE_JSON.read_text(encoding="utf-8"))
    gates = read_csv(GATES_CSV)
    label_split = read_csv(LABEL_SPLIT_CSV)
    owner_rows = read_csv(OWNER_CSV)
    market_rows = read_csv(MARKET_CSV)
    cursor, board_sha = board_cursor_and_hash()

    gap_rows = split_gap_rows(label_split)
    summary_rows = label_summary_rows(gap_rows)
    owner_market_rows = weakest_owner_market_rows(owner_rows, market_rows)

    write_csv(
        OUT_DIR / "source_label_confidence_gap_by_label_split_v1.csv",
        gap_rows,
        [
            "label",
            "split_role",
            "support",
            "rows_at_or_above_0_95",
            "share_at_or_above_0_95",
            "wilson95_lcb",
            "confidence_median",
            "confidence_mean",
            "passes_wilson95",
            "successes_needed_within_current_support",
            "additional_existing_successes_needed",
            "needed_share_within_current_support",
            "new_perfect_rows_needed_if_added",
            "blocker",
        ],
    )
    write_csv(
        OUT_DIR / "source_label_confidence_gap_by_label_v1.csv",
        summary_rows,
        [
            "label",
            "accepted_source_confidence_95",
            "total_support_across_required_splits",
            "total_rows_at_or_above_0_95",
            "worst_split",
            "worst_wilson95_lcb",
            "best_wilson95_lcb",
            "blocking_splits",
            "largest_per_split_new_perfect_rows_needed",
            "diagnosis",
        ],
    )
    write_csv(
        OUT_DIR / "source_label_confidence_gap_by_owner_market_v1.csv",
        owner_market_rows,
        [
            "axis",
            "label",
            "source_owner",
            "market_family",
            "support",
            "rows_at_or_above_0_95",
            "share_at_or_above_0_95",
            "wilson95_lcb",
            "confidence_median",
            "confidence_mean",
            "new_perfect_rows_needed_if_added",
        ],
    )

    accepted_labels = source["calibration"]["accepted_source_confidence_95_labels"]
    all_splits_have_support = all(int(row["support"]) >= 50 for row in gap_rows)
    all_splits_fail_wilson = all(row["passes_wilson95"] == "false" for row in gap_rows)
    gate_result = "source_label_confidence_gap_decomposition_v1=all_roots_confidence_quality_blocked_no_acceptance"
    summary = {
        "run_id": RUN_ID,
        "board": str(BOARD),
        "board_sha256_at_run": board_sha,
        "current_cursor_observed": cursor,
        "source_reconstruction_run": str(SOURCE_RUN),
        "source_root_presence_run": str(ROOT_PRESENCE_RUN),
        "r6_access_route_run": str(ACCESS_RUN),
        "gate_result": gate_result,
        "source_reconstruction_decision": source["decision"],
        "source_label_row_count": source["profile"]["row_count"],
        "source_label_accepted_labels": accepted_labels,
        "accepted_source_confidence_label_count": len(accepted_labels),
        "root_labels_checked": ROOT_LABELS,
        "required_splits": REQUIRED_SPLITS,
        "all_splits_have_min_support": all_splits_have_support,
        "all_label_splits_fail_wilson95": all_splits_fail_wilson,
        "label_summary": summary_rows,
        "new_confidence_gate": False,
        "accepted_rows_added": 0,
        "canonical_merge_allowed": False,
        "downstream_chain_rerun_allowed": False,
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "shared_intake_mutated": False,
        "r6_owner_export_root_mutated": False,
        "external_requests_sent": False,
        "trade_usable": False,
    }
    (OUT_DIR / "source_label_confidence_gap_decomposition_v1.json").write_text(
        json.dumps(summary, indent=2) + "\n",
        encoding="utf-8",
    )

    (OUT_DIR / "source_label_confidence_gap_decomposition_v1.md").write_text(
        f"""# Source-Label Confidence Gap Decomposition v1

- Run id: `{RUN_ID}`.
- Gate result: `{gate_result}`.
- Board cursor observed: `{cursor}`.
- Source reconstruction run: `{SOURCE_RUN}`.
- Source rows checked: `{source['profile']['row_count']}`.
- Accepted source-confidence labels before this decomposition: `{accepted_labels}`.
- New confidence gate: false. Accepted rows added: `0`.
- Thresholds relaxed: false. Runtime code changed: false. Shared intake mutated: false. Raw data committed: false.
- Downstream provider/Auto-Quant/pre-Bayes/BBN/CatBoost/execution-tree rerun allowed: false.

## Label Summary

{md_table(summary_rows, ['label', 'accepted_source_confidence_95', 'total_support_across_required_splits', 'total_rows_at_or_above_0_95', 'worst_split', 'worst_wilson95_lcb', 'best_wilson95_lcb', 'blocking_splits', 'largest_per_split_new_perfect_rows_needed', 'diagnosis'])}

## Diagnosis

All `16` label/split cells have enough support (`>=50`) but fail the Wilson95 lower-bound gate for rows whose source confidence is at least `0.95`. This is a source-confidence-quality blocker, not a support-count blocker. The current source-label equivalence root is schema-ready, but it cannot be promoted to the user's 95% cross-market/cross-period requirement without stronger source-owned confidence flags or additional high-confidence source rows.

R6 owner controls, R3 native sub-hour rows, and R5 post-`2026-01-30` recency-extension rows remain separate blockers. This packet does not unlock downstream promotion.
""",
        encoding="utf-8",
    )

    checks = [
        ("board_present", BOARD.exists()),
        ("current_cursor_010127", "20260512T010127" in cursor),
        ("source_json_present", SOURCE_JSON.exists()),
        ("source_decision_no_acceptance", source["decision"].endswith("no_acceptance")),
        ("accepted_source_confidence_labels_zero", len(accepted_labels) == 0),
        ("label_split_rows_16", len(gap_rows) == 16),
        ("all_splits_have_min_support", all_splits_have_support),
        ("all_label_splits_fail_wilson95", all_splits_fail_wilson),
        ("new_confidence_gate_false", not summary["new_confidence_gate"]),
        ("accepted_rows_added_zero", summary["accepted_rows_added"] == 0),
        ("downstream_chain_rerun_allowed_false", not summary["downstream_chain_rerun_allowed"]),
        ("strict_full_objective_achieved_false", not summary["strict_full_objective_achieved"]),
        ("update_goal_false", not summary["update_goal"]),
        ("runtime_code_changed_false", not summary["runtime_code_changed"]),
        ("thresholds_relaxed_false", not summary["thresholds_relaxed"]),
        ("shared_intake_mutated_false", not summary["shared_intake_mutated"]),
        ("external_requests_sent_false", not summary["external_requests_sent"]),
    ]
    assertion_text = "\n".join(f"{name}={'PASS' if ok else 'FAIL'}" for name, ok in checks) + "\n"
    (CHECK_DIR / "source_label_confidence_gap_decomposition_v1_assertions.out").write_text(
        assertion_text,
        encoding="utf-8",
    )
    failed = [name for name, ok in checks if not ok]
    if failed:
        raise SystemExit("failed checks: " + ", ".join(failed))


if __name__ == "__main__":
    main()
