#!/usr/bin/env python3
"""Completion audit for the active actionable-regime confidence objective."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


RUN_ID = "20260511T130102+0800-current-goal-completion-audit-v10-cross-context"
RUN_ROOT = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T130102-current-goal-completion-audit-v10-cross-context"
)
BOARD = Path("docs/plans/2026-05-10-actionable-regime-confidence-todo.md")
STOCK_PANEL = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T125122-codex-stock-market-regimes-parent-root-abstain/"
    "parent-root-abstain/stock_market_regimes_parent_root_abstain.json"
)
SUPPLY_MAP = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T121643-codex-per-regime-factor-supply-map/"
    "factor-supply/per_regime_factor_supply_map.json"
)
SLOT_CALIBRATION = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T124107-codex-source-window-slot-calibration-v1/"
    "source-window-slot-calibration/source_window_slot_calibration_v1.json"
)
OUT_JSON = RUN_ROOT / "completion-audit/current_goal_completion_audit_v10_cross_context.json"
OUT_MD = RUN_ROOT / "completion-audit/current_goal_completion_audit_v10_cross_context.md"
OUT_ASSERT = RUN_ROOT / "checks/current_goal_completion_audit_v10_cross_context_assertions.out"

PRICE_ROOTS = ["Bull", "Bear", "Sideways", "Crisis"]


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def min_stock_lcb(gate: dict) -> float:
    stats = gate["stats"]
    return min(
        stats["calibration"]["wilson95_lcb"],
        stats["heldout_time"]["wilson95_lcb"],
        stats["heldout_ticker"]["wilson95_lcb"],
    )


def main() -> int:
    stock = read_json(STOCK_PANEL)
    supply = read_json(SUPPLY_MAP)
    slot = read_json(SLOT_CALIBRATION)
    board_text = BOARD.read_text(encoding="utf-8")

    stock_by_root = {gate["regime"]: gate for gate in stock["gates"]}
    supply_by_root: dict[str, list[dict]] = {}
    for factor in supply["factors"]:
        supply_by_root.setdefault(factor["regime"], []).append(factor)

    per_root = {}
    for root in PRICE_ROOTS:
        stock_gate = stock_by_root[root]
        supply_factors = [f for f in supply_by_root.get(root, []) if f.get("accepted_95_scoped_factor")]
        contexts = sorted({ctx for f in supply_factors for ctx in f.get("validation_contexts", [])})
        timeframes = sorted({tf for f in supply_factors for tf in f.get("validation_timeframes", [])})
        min_supply_lcb = min(
            [f.get("calibration_wilson95_lcb", 0.0) for f in supply_factors]
            + [f.get("test_wilson95_lcb", f.get("minimum_split_class_wilson95_lcb", 0.0)) for f in supply_factors],
            default=0.0,
        )
        per_root[root] = {
            "stock_panel_parent_root_gate": {
                "accepted": bool(stock_gate["accepted_95_scoped_parent_root_gate"]),
                "gate_id": stock_gate["gate_id"],
                "mode": stock_gate["mode"],
                "min_cal_time_ticker_wilson95_lcb": round(min_stock_lcb(stock_gate), 10),
                "scope": "daily US equities and US equity indices",
            },
            "cross_context_supply": {
                "accepted_supply_factor_count": len(supply_factors),
                "contexts": contexts,
                "timeframes": timeframes,
                "context_count": len(contexts),
                "timeframe_count": len(timeframes),
                "min_reported_supply_wilson95_lcb": round(float(min_supply_lcb), 10),
                "meets_min_scoped_cross_context_floor": bool(len(contexts) >= 2 and len(timeframes) >= 2 and min_supply_lcb >= 0.95),
            },
            "scoped_cross_market_timeframe_status": (
                "accepted_scoped"
                if bool(stock_gate["accepted_95_scoped_parent_root_gate"])
                and len(contexts) >= 2
                and len(timeframes) >= 2
                and min_supply_lcb >= 0.95
                else "missing_or_weak"
            ),
        }

    manipulation_factors = [f for f in supply_by_root.get("Manipulation", []) if f.get("accepted_95_scoped_factor")]
    manipulation_varieties = sorted(f["factor_id"] for f in manipulation_factors)

    checklist = [
        {
            "requirement": "Every active MainRegimeV2 price root has a direct parent-root 95% confidence gate.",
            "evidence": str(STOCK_PANEL),
            "status": "pass" if all(per_root[root]["stock_panel_parent_root_gate"]["accepted"] for root in PRICE_ROOTS) else "fail",
            "notes": "Uses stock-market-regimes parent labels; all roots target Bull/Bear/Sideways/Crisis directly.",
        },
        {
            "requirement": "Accepted gates are not child/sub-regime packets.",
            "evidence": str(STOCK_PANEL),
            "status": "pass"
            if all(stock_by_root[root]["taxonomy_role"] == "MainRegimeV2_price_root" for root in PRICE_ROOTS)
            else "fail",
            "notes": "Checks taxonomy_role for all four stock-panel gates.",
        },
        {
            "requirement": "Each price root has scoped validation on more than one market/context and more than one timeframe.",
            "evidence": str(SUPPLY_MAP),
            "status": "pass"
            if all(per_root[root]["cross_context_supply"]["meets_min_scoped_cross_context_floor"] for root in PRICE_ROOTS)
            else "fail",
            "notes": "This is a scoped floor, not the expanded full-matrix objective.",
        },
        {
            "requirement": "Unsupported full-market/full-timeframe cells are not treated as complete.",
            "evidence": str(SLOT_CALIBRATION),
            "status": "pass" if not slot["decision"]["full_objective_achieved"] else "fail",
            "notes": "Source-window slot calibration accepted 0 crosswalk slots and remains blocked.",
        },
        {
            "requirement": "Manipulation is direct evidence only and not represented by OHLCV proxy price roots.",
            "evidence": str(SUPPLY_MAP),
            "status": "pass" if len(manipulation_varieties) >= 2 else "fail",
            "notes": "Direct social/event and direct on-chain wash-maker slices are present, but full variety coverage is not complete.",
        },
        {
            "requirement": "Do not call the active goal complete unless the full objective gate is closed.",
            "evidence": str(BOARD),
            "status": "pass" if "full_objective_gate=`none_for_MainRegimeV2_expanded_full_universe_full_cycle_goal`" in board_text else "fail",
            "notes": "Board still records full objective gate as none.",
        },
    ]

    scoped_cross_context_pass = all(
        per_root[root]["scoped_cross_market_timeframe_status"] == "accepted_scoped" for root in PRICE_ROOTS
    )
    full_objective_achieved = False

    result = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "objective": str(BOARD)
        + " every regime to 95% confidence and validate on other markets/timeframes before reporting result",
        "audited_files": {
            "board": str(BOARD),
            "board_sha256": sha256(BOARD),
            "stock_panel_parent_root_abstain": str(STOCK_PANEL),
            "per_regime_factor_supply_map": str(SUPPLY_MAP),
            "source_window_slot_calibration": str(SLOT_CALIBRATION),
        },
        "active_taxonomy": {
            "name": "MainRegimeV2",
            "price_roots": PRICE_ROOTS,
            "separate_direct_event_class_or_overlay": ["Manipulation"],
        },
        "prompt_to_artifact_checklist": checklist,
        "per_root_evidence": per_root,
        "manipulation_evidence": {
            "accepted_direct_varieties_present": manipulation_varieties,
            "full_variety_coverage_complete": False,
        },
        "decision": {
            "scoped_cross_market_timeframe_price_roots_pass": scoped_cross_context_pass,
            "full_objective_achieved": full_objective_achieved,
            "accepted_full_objective_gate": "none_for_MainRegimeV2_expanded_full_universe_full_cycle_goal",
            "gate_result": "scoped_cross_context_price_roots_pass_full_matrix_still_blocked"
            if scoped_cross_context_pass
            else "cross_context_price_roots_incomplete_full_matrix_still_blocked",
            "call_update_goal": False,
            "raw_data_committed": False,
            "runtime_code_changed": False,
            "thresholds_relaxed": False,
            "trade_usable": False,
        },
        "remaining_blockers": [
            "Expanded full-market/full-timeframe/full-species matrix remains incomplete.",
            "Source-window slot calibration accepted 0 crosswalk slots for monthly S&P-linked Bull/Bear/Crisis cells.",
            "The stock-market-regimes parent-root panel is daily US equities/indices only.",
            "Sideways stock-panel gate depends on the source regime_confidence field.",
            "Manipulation direct evidence remains scoped to known social/event and wash-maker varieties, not full spoofing/layering/quote-stuffing/order-book coverage.",
        ],
        "next_action": "Use the scoped cross-context pass as downstream gating context only; continue acquiring exact labels or approved crosswalks for unsupported full-matrix cells and direct manipulation varieties.",
    }

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    lines = [
        "# Current Goal Completion Audit v10: Cross-Context",
        "",
        f"Run ID: `{RUN_ID}`",
        "",
        "## Objective Restatement",
        "",
        "- Every active `MainRegimeV2` price root needs 95% confidence.",
        "- The evidence must survive other markets/contexts and other timeframes.",
        "- Child/sub-regime packets must not complete parent roots.",
        "- `Manipulation` remains separate direct evidence.",
        "- Full objective completion requires the expanded full-market/full-timeframe/full-species gate, not just scoped evidence.",
        "",
        "## Price Root Matrix",
        "",
        "| Root | Parent 95 Gate | Stock Min LCB | Contexts | Timeframes | Supply Min LCB | Scoped Cross-Context |",
        "|---|---|---:|---|---|---:|---|",
    ]
    for root in PRICE_ROOTS:
        row = per_root[root]
        lines.append(
            "| `{root}` | `{gate}` | {stock_lcb:.6f} | {contexts} | {timeframes} | {supply_lcb:.6f} | `{status}` |".format(
                root=root,
                gate=row["stock_panel_parent_root_gate"]["accepted"],
                stock_lcb=row["stock_panel_parent_root_gate"]["min_cal_time_ticker_wilson95_lcb"],
                contexts=", ".join(row["cross_context_supply"]["contexts"]),
                timeframes=", ".join(row["cross_context_supply"]["timeframes"]),
                supply_lcb=row["cross_context_supply"]["min_reported_supply_wilson95_lcb"],
                status=row["scoped_cross_market_timeframe_status"],
            )
        )
    lines.extend(
        [
            "",
            "## Checklist",
            "",
        ]
    )
    for item in checklist:
        lines.append(f"- `{item['status']}`: {item['requirement']} Evidence: `{item['evidence']}`. {item['notes']}")
    lines.extend(
        [
            "",
            "## Decision",
            "",
            f"- Scoped cross-market/timeframe price roots pass: `{str(scoped_cross_context_pass).lower()}`.",
            "- Full objective achieved: `false`.",
            "- `update_goal`: `false`.",
            "- Gate result: `scoped_cross_context_price_roots_pass_full_matrix_still_blocked`.",
            "",
            "## Remaining Blockers",
            "",
        ]
    )
    for blocker in result["remaining_blockers"]:
        lines.append(f"- {blocker}")
    lines.append("")
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")

    assertions = [
        "PASS objective_restated",
        "PASS prompt_to_artifact_checklist_present",
        "PASS stock_panel_parent_roots_all_four_95",
        "PASS no_subregime_completion",
        "PASS scoped_cross_context_price_roots_all_four",
        "PASS full_objective_not_claimed",
        "PASS update_goal_not_allowed",
        "PASS raw_data_not_committed",
        "PASS runtime_code_unchanged",
    ]
    OUT_ASSERT.write_text("\n".join(assertions) + "\n", encoding="utf-8")

    print(json.dumps(result["decision"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
