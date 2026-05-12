#!/usr/bin/env python3
"""Quantify strict 1h near-miss source-extension requirements.

This is a planning/evidence artifact, not a new confidence gate. It preserves
the fixed 2024/2025 split result from exact_1h_source_universe_expansion_v1 and
computes which blocked ticker/root rows would need source-owned post-2025 label
extension before an unchanged future gate is worth rerunning.
"""

from __future__ import annotations

import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


RUN_ID = "20260511T184151+0800-codex-strict-1h-near-miss-extension-requirements-v1"
REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T184151-codex-strict-1h-near-miss-extension-requirements-v1"
)
OUT_DIR = RUN_ROOT / "strict-1h-extension-requirements"
CHECK_DIR = RUN_ROOT / "checks"

ROWS_CSV = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T141910-codex-exact-1h-source-universe-expansion-v1/"
    "exact-1h-universe/exact_1h_source_universe_expansion_v1_rows.csv"
)
TRIAGE_JSON = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T181859-codex-strict-1h-gap-triage-v1/"
    "strict-1h-gap-triage/strict_1h_gap_triage_v1.json"
)

MIN_SUPPORT = 73
MIN_WILSON = 0.95
ROOTS = ["Bull", "Bear", "Sideways", "Crisis"]


def as_int(value: str) -> int:
    return int(float(value)) if value else 0


def as_float(value: str) -> float:
    return float(value) if value else 0.0


def read_rows() -> list[dict[str, str]]:
    with ROWS_CSV.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def extra_needed_for_split(support: int, lcb: float) -> int:
    if support >= MIN_SUPPORT and lcb >= MIN_WILSON:
        return 0
    # In these exact-source positive-context rows precision is 1.0; the Wilson
    # lower bound crosses 0.95 at n=73, matching the explicit support gate.
    return max(0, MIN_SUPPORT - support)


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)

    rows = read_rows()
    triage = json.loads(TRIAGE_JSON.read_text(encoding="utf-8"))
    blocked = [row for row in rows if row["accepted_95_strict_ticker_root_attachment"] != "True"]
    accepted = [row for row in rows if row["accepted_95_strict_ticker_root_attachment"] == "True"]

    candidates: list[dict[str, Any]] = []
    non_salvageable_current: list[dict[str, Any]] = []
    root_counter: Counter[str] = Counter()
    one_split_counter = 0
    post_extension_candidate_counter = 0

    for row in blocked:
        cal_support = as_int(row["calibration_2024_support"])
        heldout_support = as_int(row["heldout_time_2025_support"])
        cal_lcb = as_float(row["calibration_2024_wilson95_lcb"])
        heldout_lcb = as_float(row["heldout_time_2025_wilson95_lcb"])
        cal_passes = cal_support >= MIN_SUPPORT and cal_lcb >= MIN_WILSON
        heldout_passes = heldout_support >= MIN_SUPPORT and heldout_lcb >= MIN_WILSON
        cal_extra = extra_needed_for_split(cal_support, cal_lcb)
        heldout_extra = extra_needed_for_split(heldout_support, heldout_lcb)
        total_extra_to_make_both_splits_pass = cal_extra + heldout_extra
        one_split_passes = cal_passes or heldout_passes
        if one_split_passes:
            one_split_counter += 1
        if one_split_passes and total_extra_to_make_both_splits_pass <= 20:
            post_extension_candidate_counter += 1
        out = {
            "instrument": row["instrument"],
            "root": row["root"],
            "current_acceptance": "blocked",
            "calibration_2024_support": cal_support,
            "calibration_2024_wilson95_lcb": f"{cal_lcb:.10f}",
            "heldout_time_2025_support": heldout_support,
            "heldout_time_2025_wilson95_lcb": f"{heldout_lcb:.10f}",
            "calibration_split_passes": str(cal_passes).lower(),
            "heldout_split_passes": str(heldout_passes).lower(),
            "one_split_passes": str(one_split_passes).lower(),
            "extra_2024_source_sessions_to_pass_fixed_split": cal_extra,
            "extra_2025_source_sessions_to_pass_fixed_split": heldout_extra,
            "total_extra_sessions_to_make_fixed_splits_pass": total_extra_to_make_both_splits_pass,
            "post_2025_extension_use": (
                "rerun_new_chronological_gate_only"
                if one_split_passes and total_extra_to_make_both_splits_pass <= 20
                else "low_priority_or_requires_both_split_repair"
            ),
            "blocker": row["blocker"],
        }
        non_salvageable_current.append(out)
        if out["post_2025_extension_use"] == "rerun_new_chronological_gate_only":
            candidates.append(out)
            root_counter[row["root"]] += 1

    candidates.sort(
        key=lambda item: (
            int(item["total_extra_sessions_to_make_fixed_splits_pass"]),
            int(item["extra_2025_source_sessions_to_pass_fixed_split"]),
            item["root"],
            item["instrument"],
        )
    )
    non_salvageable_current.sort(
        key=lambda item: (
            int(item["total_extra_sessions_to_make_fixed_splits_pass"]),
            item["root"],
            item["instrument"],
        )
    )

    payload = {
        "run_id": RUN_ID,
        "artifact_type": "strict_1h_near_miss_extension_requirements_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_rows": str(ROWS_CSV.relative_to(REPO)),
        "source_triage": str(TRIAGE_JSON.relative_to(REPO)),
        "fixed_gate": {
            "calibration_split": "2024",
            "heldout_split": "2025",
            "min_support": MIN_SUPPORT,
            "min_wilson95_lcb": MIN_WILSON,
        },
        "counts": {
            "strict_slots": len(rows),
            "accepted_current_strict_rows": len(accepted),
            "blocked_current_strict_rows": len(blocked),
            "one_split_passes_blocked_rows": one_split_counter,
            "post_2025_extension_candidate_rows": post_extension_candidate_counter,
            "top_candidate_count": len(candidates),
            "accepted_rows_added": 0,
        },
        "candidates_by_root": dict(root_counter),
        "top_candidates": candidates[:20],
        "decision": {
            "gate_result": "strict_1h_near_miss_extension_requirements_v1=ready_source_extension_targets_no_current_acceptance",
            "accepted_rows_added": 0,
            "new_confidence_gate": False,
            "full_objective_achieved": False,
            "update_goal": False,
            "runtime_code_changed": False,
            "thresholds_relaxed": False,
            "raw_data_committed": False,
            "trade_usable": False,
        },
        "guardrail": (
            "No blocked row is accepted under the current fixed 2024/2025 gate. "
            "Post-2025 source rows may only justify a future chronological gate, "
            "not retroactive acceptance."
        ),
        "next_action": (
            "If source-owned post-2025 labels are acquired, start with the candidate CSV rows where "
            "one fixed split already passes and <=20 additional source sessions would make both fixed "
            "splits pass; otherwise keep strict 1h support at 41/156."
        ),
    }

    json_path = OUT_DIR / "strict_1h_near_miss_extension_requirements_v1.json"
    md_path = OUT_DIR / "strict_1h_near_miss_extension_requirements_v1.md"
    candidates_path = OUT_DIR / "strict_1h_near_miss_extension_candidates_v1.csv"
    blocked_path = OUT_DIR / "strict_1h_all_blocked_extension_requirements_v1.csv"
    assertions_path = CHECK_DIR / "strict_1h_near_miss_extension_requirements_v1_assertions.out"

    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    fields = [
        "instrument",
        "root",
        "current_acceptance",
        "calibration_2024_support",
        "calibration_2024_wilson95_lcb",
        "heldout_time_2025_support",
        "heldout_time_2025_wilson95_lcb",
        "calibration_split_passes",
        "heldout_split_passes",
        "one_split_passes",
        "extra_2024_source_sessions_to_pass_fixed_split",
        "extra_2025_source_sessions_to_pass_fixed_split",
        "total_extra_sessions_to_make_fixed_splits_pass",
        "post_2025_extension_use",
        "blocker",
    ]
    write_csv(candidates_path, candidates, fields)
    write_csv(blocked_path, non_salvageable_current, fields)

    lines = [
        "# Strict 1h Near-Miss Extension Requirements v1",
        "",
        f"Run ID: `{RUN_ID}`",
        "",
        "## Decision",
        "",
        "- Current strict exact `1h` accepted rows remain `41/156`.",
        "- Current accepted rows added: `0`; new confidence gate: `false`.",
        "- No blocked row is promoted under the fixed 2024/2025 gate.",
        f"- Blocked rows with one split already passing: `{one_split_counter}`.",
        f"- Post-2025 extension candidates with <=20 missing source sessions: `{post_extension_candidate_counter}`.",
        "- Gate result: `strict_1h_near_miss_extension_requirements_v1=ready_source_extension_targets_no_current_acceptance`.",
        "- Full objective achieved: false. `update_goal=false`.",
        "",
        "## Top Extension Candidates",
        "",
        "| Instrument | Root | 2024 extra | 2025 extra | Total extra | Current blocker |",
        "|---|---|---:|---:|---:|---|",
    ]
    for row in candidates[:20]:
        lines.append(
            "| {instrument} | {root} | {extra_2024_source_sessions_to_pass_fixed_split} | "
            "{extra_2025_source_sessions_to_pass_fixed_split} | "
            "{total_extra_sessions_to_make_fixed_splits_pass} | `{blocker}` |".format(**row)
        )
    lines.extend(["", "## Guardrail", "", payload["guardrail"], "", "## Next", "", payload["next_action"]])
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    assertion_lines = [
        f"run_id={RUN_ID}",
        f"strict_slots={len(rows)}",
        f"accepted_current_strict_rows={len(accepted)}",
        f"blocked_current_strict_rows={len(blocked)}",
        f"one_split_passes_blocked_rows={one_split_counter}",
        f"post_2025_extension_candidate_rows={post_extension_candidate_counter}",
        "accepted_rows_added=0",
        "new_confidence_gate=false",
        "full_objective_achieved=false",
        "update_goal=false",
        "runtime_code_changed=false",
        "thresholds_relaxed=false",
        "raw_data_committed=false",
        "trade_usable=false",
    ]
    assertion_status = (
        "PASS"
        if len(rows) == 156
        and len(accepted) == 41
        and len(blocked) == 115
        and post_extension_candidate_counter > 0
        else "FAIL"
    )
    assertion_lines.append(f"assertion_status={assertion_status}")
    assertions_path.write_text("\n".join(assertion_lines) + "\n", encoding="utf-8")
    return 0 if assertion_status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
