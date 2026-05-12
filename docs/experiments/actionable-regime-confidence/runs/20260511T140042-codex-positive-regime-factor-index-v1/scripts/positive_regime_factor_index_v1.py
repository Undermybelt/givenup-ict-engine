#!/usr/bin/env python3
"""Build the positive MainRegimeV2 factor supply index from accepted artifacts."""

from __future__ import annotations

import csv
import hashlib
import json
import math
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[6]
RUN_ID = "20260511T140042+0800-codex-positive-regime-factor-index-v1"
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T140042-codex-positive-regime-factor-index-v1"
OUT_DIR = RUN_ROOT / "positive-factor-index"
CHECK_DIR = RUN_ROOT / "checks"

BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"
ROOT_GATE = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T125122-codex-stock-market-regimes-parent-root-abstain/"
    "parent-root-abstain/stock_market_regimes_parent_root_abstain.json"
)
AXISWISE_SUMMARY = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T131922-codex-source-consensus-axiswise-timeframe-gate-v1/"
    "source-consensus-axiswise/source_consensus_axiswise_timeframe_gate_v1_summary.csv"
)
INTRADAY_SLOTS = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T134756-codex-daily-to-intraday-source-attachment-v1/"
    "daily-intraday-attachment/daily_to_intraday_source_attachment_v1_slots.csv"
)
CROSSWALK_SLOTS = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T135932-codex-es-nq-source-crosswalk-calibration-v1/"
    "crosswalk-calibration/es_nq_source_crosswalk_calibration_v1_slots.csv"
)
DIRECT_MATRIX = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T131311-codex-direct-manipulation-variety-matrix-v1/"
    "direct-manipulation/direct_manipulation_variety_matrix_v1.json"
)
LOCAL_EXPORT_CHECK = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T134038-codex-local-row-export-acquisition-check-v1/"
    "acquisition-check/local_row_export_acquisition_check_v1.json"
)

ROOTS = ["Bull", "Bear", "Sideways", "Crisis"]
MIN_LCB = 0.95


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def wilson_lcb(pos: int, n: int, z: float = 1.959963984540054) -> float:
    if n <= 0:
        return 0.0
    p = pos / n
    denom = 1 + z * z / n
    center = p + z * z / (2 * n)
    radius = z * math.sqrt((p * (1 - p) + z * z / (4 * n)) / n)
    return (center - radius) / denom


def min_all_success_support_for_lcb(target: float) -> int:
    n = 1
    while wilson_lcb(n, n) < target:
        n += 1
    return n


def fmt(value: Any) -> str:
    if isinstance(value, float):
        return f"{value:.6f}"
    return str(value)


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)

    root_gate = load_json(ROOT_GATE)
    direct_matrix = load_json(DIRECT_MATRIX)
    local_export = load_json(LOCAL_EXPORT_CHECK)
    axiswise_rows = read_csv(AXISWISE_SUMMARY)
    intraday_rows = read_csv(INTRADAY_SLOTS)
    crosswalk_rows = read_csv(CROSSWALK_SLOTS) if CROSSWALK_SLOTS.exists() else []
    min_support = min_all_success_support_for_lcb(MIN_LCB)

    factor_rows: list[dict[str, Any]] = []
    for gate in root_gate["gates"]:
        stats = gate["stats"]
        min_split_lcb = min(
            stats["calibration"]["wilson95_lcb"],
            stats["heldout_time"]["wilson95_lcb"],
            stats["heldout_ticker"]["wilson95_lcb"],
        )
        factor_rows.append(
            {
                "regime": gate["regime"],
                "taxonomy_role": "MainRegimeV2_price_root",
                "evidence_layer": "daily_parent_root_factor",
                "scope": "daily_us_equity_index_source_panel_after_252d_warmup",
                "gate_or_variety": gate["gate_id"],
                "rule_or_signal": gate["rule"],
                "calibration_support": stats["calibration"]["support"],
                "calibration_wilson95_lcb": stats["calibration"]["wilson95_lcb"],
                "heldout_time_support": stats["heldout_time"]["support"],
                "heldout_time_wilson95_lcb": stats["heldout_time"]["wilson95_lcb"],
                "heldout_context_support": stats["heldout_ticker"]["support"],
                "heldout_context_wilson95_lcb": stats["heldout_ticker"]["wilson95_lcb"],
                "min_split_wilson95_lcb": min_split_lcb,
                "accepted_95": gate["accepted_95_scoped_parent_root_gate"],
                "limitations": "Scoped parent-root factor, not full-universe/full-timeframe completion.",
                "artifact": str(ROOT_GATE.relative_to(REPO)),
            }
        )

    for row in axiswise_rows:
        factor_rows.append(
            {
                "regime": row["regime"],
                "taxonomy_role": "MainRegimeV2_price_root",
                "evidence_layer": f"{row['timeframe']}_source_consensus_context",
                "scope": "same_source_weekly_monthly_axiswise_context",
                "gate_or_variety": f"{row['timeframe']}:{row['regime']}",
                "rule_or_signal": "emit only when label_share >= 0.95; validate daily source-label agreement in emitted window",
                "calibration_support": row["cal_daily_support"],
                "calibration_wilson95_lcb": row["cal_lcb"],
                "heldout_time_support": row["heldout_time_axis_daily_support"],
                "heldout_time_wilson95_lcb": row["heldout_time_axis_lcb"],
                "heldout_context_support": row["heldout_ticker_axis_daily_support"],
                "heldout_context_wilson95_lcb": row["heldout_ticker_axis_lcb"],
                "min_split_wilson95_lcb": min(
                    float(row["cal_lcb"]),
                    float(row["heldout_time_axis_lcb"]),
                    float(row["heldout_ticker_axis_lcb"]),
                ),
                "accepted_95": row["accepted_95"],
                "limitations": "Same-source timeframe context; not an intraday micro-regime.",
                "artifact": str(AXISWISE_SUMMARY.relative_to(REPO)),
            }
        )

    intraday_by_root: dict[str, list[dict[str, str]]] = {root: [] for root in ROOTS}
    for row in intraday_rows:
        if row["accepted_95_source_label_attachment"] == "True":
            intraday_by_root[row["root"]].append(row)
    for root, rows in intraday_by_root.items():
        if not rows:
            continue
        first = rows[0]
        factor_rows.append(
            {
                "regime": root,
                "taxonomy_role": "MainRegimeV2_price_root",
                "evidence_layer": "intraday_parent_day_context_attachment",
                "scope": "exact_yfinance_intraday_same_source_^GSPC_^DJI",
                "gate_or_variety": f"exact_intraday_{root}_accepted_{len(rows)}_rows",
                "rule_or_signal": "same ticker daily MainRegimeV2 root attached to intraday session date as parent-day context",
                "calibration_support": first["calibration_support"],
                "calibration_wilson95_lcb": first["calibration_wilson95_lcb"],
                "heldout_time_support": first["heldout_time_support"],
                "heldout_time_wilson95_lcb": first["heldout_time_wilson95_lcb"],
                "heldout_context_support": first["heldout_ticker_support"],
                "heldout_context_wilson95_lcb": first["heldout_ticker_wilson95_lcb"],
                "min_split_wilson95_lcb": min(
                    float(first["calibration_wilson95_lcb"]),
                    float(first["heldout_time_wilson95_lcb"]),
                    float(first["heldout_ticker_wilson95_lcb"]),
                ),
                "accepted_95": True,
                "limitations": "Parent-day context only; not an intraday transition timing signal.",
                "artifact": str(INTRADAY_SLOTS.relative_to(REPO)),
            }
        )

    accepted_direct = []
    for item in direct_matrix["coverage_matrix"]:
        if item["state"].startswith("accepted_95"):
            accepted_direct.append(item)
            factor_rows.append(
                {
                    "regime": "Manipulation",
                    "taxonomy_role": "direct_event_or_overlay",
                    "evidence_layer": "direct_manipulation_scoped_variety",
                    "scope": item["state"],
                    "gate_or_variety": item["variety"],
                    "rule_or_signal": item["gate_summary"],
                    "calibration_support": "",
                    "calibration_wilson95_lcb": "",
                    "heldout_time_support": "",
                    "heldout_time_wilson95_lcb": "",
                    "heldout_context_support": "",
                    "heldout_context_wilson95_lcb": "",
                    "min_split_wilson95_lcb": "",
                    "accepted_95": True,
                    "limitations": item["remaining_gap"],
                    "artifact": item.get("primary_artifact") or str(DIRECT_MATRIX.relative_to(REPO)),
                }
            )

    crisis_blockers = [
        row for row in intraday_rows
        if row["root"] == "Crisis" and row["accepted_95_source_label_attachment"] != "True"
    ]
    crosswalk_counts = Counter(row.get("accepted_95_source_label_crosswalk_attachment", "") for row in crosswalk_rows)
    do_not_repeat = [
        {
            "lane": "exact_^GSPC_^DJI_intraday_Crisis",
            "reason": "mathematically_support_short_under_current_split",
            "evidence": (
                f"all-success Wilson95 needs at least {min_support} observations per split; "
                f"current calibration={crisis_blockers[0]['calibration_support']} and "
                f"heldout_time={crisis_blockers[0]['heldout_time_support']}."
                if crisis_blockers
                else f"all-success Wilson95 needs at least {min_support} observations per split."
            ),
            "allowed_next": "add broader exact-source Crisis dates or a new independent source-label panel; do not tune OHLCV.",
        },
        {
            "lane": "ES_NQ_15m_1h_crosswalk_without_new_source_relation",
            "reason": "recent crosswalk package already accepted only scoped ES Bull rows",
            "evidence": f"135932 crosswalk states={dict(crosswalk_counts)}; unresolved NQ source relation and support-short roots remain.",
            "allowed_next": "obtain Nasdaq-100-grade source labels or explicit owner-approved relation before any NQ promotion.",
        },
        {
            "lane": "local_filename_export_search_for_FINRA_or_native_labels",
            "reason": "bounded local export checks already found no attachable rows",
            "evidence": local_export["decision"]["gate_result"],
            "allowed_next": "use authenticated/user-provided row exports with positives and matched negatives.",
        },
        {
            "lane": "OHLCV_HMM_generated_labels_for_Manipulation",
            "reason": "forbidden_by_MainRegimeV2_taxonomy",
            "evidence": "Manipulation requires direct timestamped event/order-flow/order-lifecycle/social/on-chain rows plus controls.",
            "allowed_next": "only direct rows or classified event feeds can be evaluated.",
        },
    ]

    accepted_price_roots = sorted(
        {
            row["regime"]
            for row in factor_rows
            if row["taxonomy_role"] == "MainRegimeV2_price_root"
            and row["evidence_layer"] == "daily_parent_root_factor"
            and str(row["accepted_95"]).lower() == "true"
        }
    )
    axiswise_accepted = [row for row in axiswise_rows if row["accepted_95"] == "True"]
    intraday_accepted = sum(1 for row in intraday_rows if row["accepted_95_source_label_attachment"] == "True")

    result = {
        "run_id": RUN_ID,
        "artifact_type": "positive_regime_factor_index_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "board": str(BOARD.relative_to(REPO)),
        "board_sha256_at_run": sha256(BOARD),
        "inputs": {
            "root_gate": str(ROOT_GATE.relative_to(REPO)),
            "axiswise_summary": str(AXISWISE_SUMMARY.relative_to(REPO)),
            "intraday_slots": str(INTRADAY_SLOTS.relative_to(REPO)),
            "crosswalk_slots": str(CROSSWALK_SLOTS.relative_to(REPO)),
            "direct_matrix": str(DIRECT_MATRIX.relative_to(REPO)),
            "local_export_check": str(LOCAL_EXPORT_CHECK.relative_to(REPO)),
        },
        "support_algebra": {
            "wilson95_lcb_threshold": MIN_LCB,
            "minimum_all_success_support": min_support,
            "why_it_matters": "Any split below this support cannot pass 95 even if every observed row is correct.",
        },
        "positive_supply": {
            "daily_parent_price_roots_accepted": accepted_price_roots,
            "daily_parent_price_roots_accepted_count": len(accepted_price_roots),
            "same_source_weekly_monthly_cells_accepted_count": len(axiswise_accepted),
            "exact_intraday_parent_context_rows_accepted": intraday_accepted,
            "exact_intraday_parent_context_roots_accepted": sorted(
                root for root, rows in intraday_by_root.items() if rows
            ),
            "direct_manipulation_scoped_varieties_accepted": [item["variety"] for item in accepted_direct],
            "direct_manipulation_scoped_varieties_accepted_count": len(accepted_direct),
        },
        "decision": {
            "per_price_root_factor_supply_present": set(accepted_price_roots) == set(ROOTS),
            "manipulation_has_direct_scoped_supply": bool(accepted_direct),
            "full_direct_manipulation_variety_coverage": direct_matrix["rollup"]["full_direct_manipulation_variety_coverage"],
            "accepted_full_objective_gate": "none_for_MainRegimeV2_expanded_full_universe_full_cycle_goal",
            "full_objective_achieved": False,
            "gate_result": "positive_regime_factor_index_v1_per_root_supply_present_full_goal_still_blocked",
            "runtime_code_changed": False,
            "thresholds_relaxed": False,
            "raw_data_committed": False,
            "trade_usable": False,
            "call_update_goal": False,
        },
        "next_action": (
            "Use this positive index as the Board A factor-supply map; do not run more provider-bar proxy scans. "
            "Further Board A completion requires new independent source-label panels or direct positive/negative manipulation rows."
        ),
    }

    fields = [
        "regime",
        "taxonomy_role",
        "evidence_layer",
        "scope",
        "gate_or_variety",
        "rule_or_signal",
        "calibration_support",
        "calibration_wilson95_lcb",
        "heldout_time_support",
        "heldout_time_wilson95_lcb",
        "heldout_context_support",
        "heldout_context_wilson95_lcb",
        "min_split_wilson95_lcb",
        "accepted_95",
        "limitations",
        "artifact",
    ]
    write_csv(OUT_DIR / "positive_regime_factor_index_v1.csv", factor_rows, fields)
    write_csv(OUT_DIR / "do_not_repeat_negative_lanes_v1.csv", do_not_repeat, ["lane", "reason", "evidence", "allowed_next"])
    (OUT_DIR / "positive_regime_factor_index_v1.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    lines = [
        "# Positive Regime Factor Index v1",
        "",
        f"Run ID: `{RUN_ID}`",
        "",
        "This artifact is a positive supply index, not another negative source scan. It says which MainRegimeV2 factors are already accepted at 95, and which doomed lanes should not be repeated.",
        "",
        "## Accepted Supply",
        "",
        f"- Price roots with accepted daily parent-root factors: `{', '.join(accepted_price_roots)}` (`{len(accepted_price_roots)}/4`).",
        f"- Same-source weekly/monthly source-consensus cells accepted: `{len(axiswise_accepted)}/8`.",
        f"- Exact intraday parent-day context rows accepted: `{intraday_accepted}/48`.",
        f"- Direct `Manipulation` scoped varieties accepted: `{len(accepted_direct)}` (`{', '.join(item['variety'] for item in accepted_direct)}`).",
        "",
        "## Support Algebra",
        "",
        f"- Wilson95 lower bound `>= 0.95` needs at least `{min_support}` all-correct observations in a split.",
        "- Exact `^GSPC/^DJI` intraday `Crisis` has only `28` calibration source-days and `2` heldout-time source-days, so more tuning in that lane cannot pass.",
        "- ES/NQ crosswalk already proved the support/policy bottleneck: accepted only scoped ES Bull rows; NQ needs a Nasdaq-100-grade source relation before promotion.",
        "",
        "## Do Not Repeat",
        "",
        "- Do not run more OHLCV/HMM/generated-label searches for direct `Manipulation`.",
        "- Do not rerun local filename searches for FINRA/native labels without a new row-export location.",
        "- Do not treat provider bars as labels; use them only for session/date overlap after source labels exist.",
        "",
        "## Decision",
        "",
        "- Per price-root factor supply is present for `Bull`, `Bear`, `Sideways`, and `Crisis` in the scoped daily source panel.",
        "- `Manipulation` has scoped direct-event/order-lifecycle/on-chain accepted supply, but full variety coverage is still incomplete.",
        "- Full objective achieved: `false`.",
        "- Gate result: `positive_regime_factor_index_v1_per_root_supply_present_full_goal_still_blocked`.",
        "- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; trade usable: `false`.",
        "",
        "## Next",
        "",
        "Use this index as the Board A factor-supply map. Further Board A completion requires new independent source-label panels or direct positive/negative manipulation rows, not more provider-bar proxy scans.",
    ]
    (OUT_DIR / "positive_regime_factor_index_v1.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    assertions = [
        f"run_id={RUN_ID}",
        f"board_sha256_at_run={result['board_sha256_at_run']}",
        f"minimum_all_success_support={min_support}",
        f"daily_parent_price_roots_accepted_count={len(accepted_price_roots)}",
        f"same_source_weekly_monthly_cells_accepted_count={len(axiswise_accepted)}",
        f"exact_intraday_parent_context_rows_accepted={intraday_accepted}",
        f"direct_manipulation_scoped_varieties_accepted_count={len(accepted_direct)}",
        "full_objective_achieved=false",
        "runtime_code_changed=false",
        "thresholds_relaxed=false",
        "raw_data_committed=false",
        "trade_usable=false",
    ]
    checks_ok = (
        set(accepted_price_roots) == set(ROOTS)
        and len(axiswise_accepted) == 8
        and intraday_accepted == 36
        and len(accepted_direct) >= 1
        and min_support == 73
        and not result["decision"]["full_objective_achieved"]
    )
    assertions.append(f"assertion_status={'PASS' if checks_ok else 'FAIL'}")
    (CHECK_DIR / "positive_regime_factor_index_v1_assertions.out").write_text(
        "\n".join(assertions) + "\n",
        encoding="utf-8",
    )
    return 0 if checks_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
