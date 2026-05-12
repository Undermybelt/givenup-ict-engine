#!/usr/bin/env python3
"""Attachability audit for primary source windows against the current gap matrix."""

from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = Path(__file__).resolve().parents[1]
BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"
SEED_CSV = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T120900-codex-exportable-source-scan/"
    "source-scan/source_window_seed_v1.csv"
)
MISSING_CSV = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T081715-codex-source-label-acquisition-package-v2/"
    "acquisition-package/missing_root_label_slots_acquisition_request_v2.csv"
)
OUT_DIR = RUN_ROOT / "source-window-attachability"
CHECK_DIR = RUN_ROOT / "checks"
OUT_JSON = OUT_DIR / "source_window_attachability_v1.json"
OUT_MD = OUT_DIR / "source_window_attachability_v1.md"
OUT_CSV = OUT_DIR / "source_window_attachability_candidates_v1.csv"
ASSERTIONS = CHECK_DIR / "source_window_attachability_v1_assertions.out"
RUN_ID = "20260511T122709+0800-codex-source-window-attachability-v1"


SPX_FAMILY_EXACT_OR_DERIVATIVE = {"^GSPC", "SPY", "ES=F"}
US_RISK_CONTEXT_INSTRUMENTS = {
    "^GSPC",
    "SPY",
    "ES=F",
    "^DJI",
    "DIA",
    "YM=F",
    "QQQ",
    "^NDX",
    "NQ=F",
    "^VIX",
}
SUPPORTED_PROJECTION_TIMEFRAMES = {"1m", "5m", "15m", "30m", "1h", "4h", "1d", "1w", "1mo"}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as f:
        return list(csv.DictReader(f))


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def source_windows_for_root(windows: list[dict[str, str]], root: str) -> list[dict[str, str]]:
    return [row for row in windows if row["root"] == root]


def classify_slot(slot: dict[str, str], windows: list[dict[str, str]]) -> dict[str, str]:
    root = slot["root"]
    instrument = slot["instrument"]
    timeframe = slot["timeframe"]
    root_windows = source_windows_for_root(windows, root)
    base = {
        "provider": slot["provider"],
        "instrument": instrument,
        "timeframe": timeframe,
        "root": root,
        "missing_or_rejected_reason": slot["missing_or_rejected_reason"],
        "candidate_window_count": str(len(root_windows)),
        "source_ids": ";".join(sorted({row["source_id"] for row in root_windows})),
    }
    if not root_windows:
        return {
            **base,
            "attachability_status": "blocked_no_source_window",
            "crosswalk_policy": "none",
            "approval_required": "true",
            "reason": "No dated source-window seed exists for this root.",
        }

    if root in {"Bull", "Bear"}:
        if instrument == "^GSPC" and timeframe == "1d":
            return {
                **base,
                "attachability_status": "attachable_exact_native_if_slot_requested",
                "crosswalk_policy": "native_sp500_index_day_window",
                "approval_required": "false",
                "reason": "Yardeni windows are native S&P 500 day-level windows.",
            }
        if instrument in SPX_FAMILY_EXACT_OR_DERIVATIVE and timeframe in SUPPORTED_PROJECTION_TIMEFRAMES:
            return {
                **base,
                "attachability_status": "candidate_requires_owner_projection_crosswalk",
                "crosswalk_policy": "sp500_window_to_spx_family_instrument_timeframe",
                "approval_required": "true",
                "reason": "SPY/ES/Finer-timeframe projection from S&P 500 source windows is plausible but not owner-approved.",
            }
        return {
            **base,
            "attachability_status": "blocked_outside_native_or_spx_family_scope",
            "crosswalk_policy": "rejected_by_scope",
            "approval_required": "true",
            "reason": "Bull/Bear source windows are S&P 500 native; no approved projection to this instrument.",
        }

    if root == "Crisis":
        if instrument in US_RISK_CONTEXT_INSTRUMENTS and timeframe in SUPPORTED_PROJECTION_TIMEFRAMES:
            return {
                **base,
                "attachability_status": "candidate_requires_owner_projection_crosswalk",
                "crosswalk_policy": "nber_us_contraction_to_us_risk_context",
                "approval_required": "true",
                "reason": "NBER contraction is a macro source window; instrument/timeframe projection requires explicit approval.",
            }
        return {
            **base,
            "attachability_status": "blocked_outside_us_risk_context_scope",
            "crosswalk_policy": "rejected_by_scope",
            "approval_required": "true",
            "reason": "NBER contraction was not projected to this non-US-risk instrument/context.",
        }

    return {
        **base,
        "attachability_status": "blocked_no_approved_policy",
        "crosswalk_policy": "none",
        "approval_required": "true",
        "reason": "No attachability policy exists for this root.",
    }


def main() -> None:
    windows = read_csv(SEED_CSV)
    missing = read_csv(MISSING_CSV)
    rows = [classify_slot(slot, windows) for slot in missing]
    status_counts = Counter(row["attachability_status"] for row in rows)
    by_root_status = Counter((row["root"], row["attachability_status"]) for row in rows)
    candidate_rows = [
        row
        for row in rows
        if row["attachability_status"] == "candidate_requires_owner_projection_crosswalk"
    ]
    exact_rows = [
        row
        for row in rows
        if row["attachability_status"] == "attachable_exact_native_if_slot_requested"
    ]

    report = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "board": str(BOARD.relative_to(REPO)),
        "board_sha256_at_audit": sha256(BOARD),
        "objective": "Apply source_window_seed_v1 to the current missing-slot matrix with fail-closed crosswalk accounting.",
        "inputs": {
            "source_window_seed_csv": str(SEED_CSV.relative_to(REPO)),
            "missing_slot_csv": str(MISSING_CSV.relative_to(REPO)),
        },
        "source_window_counts_by_root": dict(Counter(row["root"] for row in windows)),
        "slot_counts": {
            "total_missing_or_rejected_slots": len(missing),
            "exact_native_attachable_slots_in_current_missing_matrix": len(exact_rows),
            "candidate_projection_slots_requiring_owner_approval": len(candidate_rows),
            "blocked_slots": len(rows) - len(exact_rows) - len(candidate_rows),
        },
        "status_counts": dict(status_counts),
        "root_status_counts": {
            f"{root}:{status}": count for (root, status), count in sorted(by_root_status.items())
        },
        "candidate_projection_summary": {
            "by_policy": dict(Counter(row["crosswalk_policy"] for row in candidate_rows)),
            "by_root": dict(Counter(row["root"] for row in candidate_rows)),
            "by_instrument": dict(Counter(row["instrument"] for row in candidate_rows)),
            "by_timeframe": dict(Counter(row["timeframe"] for row in candidate_rows)),
        },
        "decision": {
            "accepted_parent_root_slots_added": 0,
            "accepted_direct_manipulation_rows_added": 0,
            "full_objective_achieved": False,
            "gate_result": "source_window_attachability_v1_candidates_require_owner_crosswalk",
            "why_not_complete": [
                "No exact-native source-window slot is currently missing for S&P 500 day-level Bull/Bear.",
                "All useful Bull/Bear/Crisis slot attachments require explicit owner-approved projection/crosswalk.",
                "Sideways still has zero dated source windows in source_window_seed_v1.",
                "Manipulation is outside this price-root source-window lane and remains direct-evidence only.",
            ],
            "runtime_code_changed": False,
            "thresholds_relaxed": False,
            "raw_data_committed": False,
            "trade_usable": False,
        },
        "artifacts": {
            "json": str(OUT_JSON.relative_to(REPO)),
            "md": str(OUT_MD.relative_to(REPO)),
            "candidate_csv": str(OUT_CSV.relative_to(REPO)),
            "assertions": str(ASSERTIONS.relative_to(REPO)),
            "script": str(Path(__file__).resolve().relative_to(REPO)),
        },
        "next_action": "Owner decision required: approve/reject SPX-family and NBER-to-US-risk projection crosswalks; separately supply a dated Sideways source/adjudication protocol.",
    }

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")

    fieldnames = [
        "provider",
        "instrument",
        "timeframe",
        "root",
        "missing_or_rejected_reason",
        "attachability_status",
        "crosswalk_policy",
        "approval_required",
        "candidate_window_count",
        "source_ids",
        "reason",
    ]
    with OUT_CSV.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)

    md = [
        "# Source Window Attachability v1",
        "",
        f"Run ID: `{RUN_ID}`",
        "",
        "## Result",
        "",
        f"- Current missing/rejected slots inspected: `{len(missing)}`.",
        f"- Exact-native attachable slots currently missing: `{len(exact_rows)}`.",
        f"- Candidate projection slots requiring owner approval: `{len(candidate_rows)}`.",
        "- Accepted parent-root slots added: `0`.",
        "- Full objective achieved: `false`.",
        f"- Gate result: `{report['decision']['gate_result']}`.",
        "",
        "## Candidate Projection Slots",
        "",
        "| Root | Candidates |",
        "|---|---:|",
    ]
    for root, count in sorted(Counter(row["root"] for row in candidate_rows).items()):
        md.append(f"| `{root}` | `{count}` |")
    md.extend(
        [
            "",
            "## Blockers",
            "",
            "- SPX-family and NBER macro projections are now enumerated, but not accepted without owner approval.",
            "- `Sideways` still has no dated source window in `source_window_seed_v1.csv`.",
            "- Direct `Manipulation` remains separate direct-event/order-flow evidence; this price-root source-window lane does not alter it.",
            "",
            "## Artifacts",
            "",
            f"- JSON: `{report['artifacts']['json']}`",
            f"- Candidate CSV: `{report['artifacts']['candidate_csv']}`",
            f"- Assertions: `{report['artifacts']['assertions']}`",
        ]
    )
    OUT_MD.write_text("\n".join(md) + "\n")

    checks = [
        ("inspected_current_missing_slots", len(missing) == 564),
        ("candidate_projection_slots_positive", len(candidate_rows) > 0),
        ("sideways_blocked_no_source_window", by_root_status[("Sideways", "blocked_no_source_window")] == 141),
        ("accepted_parent_root_slots_zero_without_owner_crosswalk", report["decision"]["accepted_parent_root_slots_added"] == 0),
        ("full_objective_false", not report["decision"]["full_objective_achieved"]),
        ("thresholds_relaxed_false", not report["decision"]["thresholds_relaxed"]),
        ("runtime_code_changed_false", not report["decision"]["runtime_code_changed"]),
        ("raw_data_committed_false", not report["decision"]["raw_data_committed"]),
        ("trade_usable_false", not report["decision"]["trade_usable"]),
    ]
    ASSERTIONS.write_text(
        "".join(f"{'PASS' if ok else 'FAIL'} {name}={ok}\n" for name, ok in checks)
    )
    if not all(ok for _, ok in checks):
        raise SystemExit("source-window attachability assertions failed")


if __name__ == "__main__":
    main()
