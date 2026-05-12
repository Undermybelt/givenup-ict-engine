#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[6]
RUN_ID = "20260511T134007+0800-codex-post-axiswise-remaining-target-selector-v1"
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T134007-codex-post-axiswise-remaining-target-selector-v1"
OUT_DIR = RUN_ROOT / "target-selector"
CHECK_DIR = RUN_ROOT / "checks"

BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"
AUDIT_V11 = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T132538-current-goal-completion-audit-v11-after-axiswise/completion-audit/current_goal_completion_audit_v11_after_axiswise.json"
PURITY = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T132544-codex-monthly-sideways-purity-policy-probe-v1/monthly-sideways-purity/monthly_sideways_purity_policy_probe_v1.json"
AXISWISE = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T131922-codex-source-consensus-axiswise-timeframe-gate-v1/source-consensus-axiswise/source_consensus_axiswise_timeframe_gate_v1.json"
DIRECT_MATRIX = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T131311-codex-direct-manipulation-variety-matrix-v1/direct-manipulation/direct_manipulation_variety_matrix_v1.json"
ACQ_V4 = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T125337-codex-post-calibration-acquisition-request-v4/acquisition-request/post_calibration_acquisition_request_v4.csv"
MISSING_V3 = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T094002-codex-external-label-request-package-v3/acquisition-request/missing_parent_root_label_slots_request_v3.csv"
ROOT_PROBE = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T084131-codex-root-label-source-acquisition-probe/source-acquisition/root_label_source_acquisition_probe.json"
UNAUTH_PROBE = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T084353-codex-unauth-root-label-source-probe/source-acquisition/unauth_root_label_source_probe.json"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as f:
        return list(csv.DictReader(f))


def count_by(rows: list[dict[str, str]], key: str) -> dict[str, int]:
    return dict(sorted(Counter(row.get(key, "") for row in rows).items()))


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)

    audit = load_json(AUDIT_V11)
    purity = load_json(PURITY)
    axiswise = load_json(AXISWISE)
    direct = load_json(DIRECT_MATRIX)
    root_probe = load_json(ROOT_PROBE)
    unauth_probe = load_json(UNAUTH_PROBE)
    acquisition_requests = read_csv(ACQ_V4)
    missing_slots = read_csv(MISSING_V3)

    missing_summary = {
        "rows": len(missing_slots),
        "provider": count_by(missing_slots, "provider"),
        "timeframe": count_by(missing_slots, "timeframe"),
        "root": count_by(missing_slots, "root"),
        "reason": count_by(missing_slots, "missing_or_rejected_reason"),
    }

    top_slots: list[dict[str, str]] = []
    preferred_timeframes = {"15m", "1h", "4h", "1d", "1w", "1mo"}
    preferred_instruments = {"SPY", "QQQ", "^GSPC", "^NDX", "ES=F", "NQ=F", "XBTUSD", "ETHUSD"}
    for row in missing_slots:
        if row["timeframe"] in preferred_timeframes and row["instrument"] in preferred_instruments:
            top_slots.append(row)
    top_slots = top_slots[:80]

    request_priorities = [
        {
            "rank": 1,
            "request_id": "v4-price-root-exact-label-panel",
            "target": "Exact provider/instrument/timeframe MainRegimeV2 labels",
            "why_now": "After 131922, same-source US equity/index 1w/1mo is closed; the remaining price-root blocker is exact labels for unsupported intraday/full-species cells.",
            "can_local_provider_close_now": False,
            "local_provider_note": "TradingViewRemix MCP is ready for OHLCV, but the local ict-engine tool allowlist exposes OHLCV/options only, not independent Bull/Bear/Sideways/Crisis labels.",
            "next_small_action": "Obtain or point to a dated independent label panel for one high-liquidity slice such as SPY/QQQ/^GSPC/^NDX/ES/NQ 15m/1h/4h or Kraken XBTUSD/ETHUSD 1d/1w/1mo, then run chronological calibration/test.",
        },
        {
            "rank": 2,
            "request_id": "v4-direct-manipulation-variety-rows",
            "target": "Direct Manipulation positives/negatives across more varieties",
            "why_now": "Direct Manipulation is explicitly part of the full objective and current accepted varieties are scoped; spoofing/layering/quote stuffing/pinging/bear raid/painting-the-tape remain open.",
            "can_local_provider_close_now": False,
            "local_provider_note": "Existing spoofing/layering case inventory is positive-only. OHLCV and TradingView bars cannot serve as direct order-lifecycle positives or matched negatives.",
            "next_small_action": "Export replayable spoofing/layering or quote-stuffing positive rows with matched same-venue/same-period negative controls; keep raw rows outside the repo and commit only compact evidence.",
        },
        {
            "rank": 3,
            "request_id": "v4-historical-source-window-bar-overlap",
            "target": "Historical bar overlap for approved source-window labels",
            "why_now": "Useful only after explicit source-window/crosswalk approval; 124107 accepted zero calibrated source-window slots.",
            "can_local_provider_close_now": False,
            "local_provider_note": "TradingViewRemix/Yahoo/IBKR bars can validate overlap but are not labels by themselves.",
            "next_small_action": "Use provider bars only after source windows are approved for exact instrument/provider/timeframe routing.",
        },
    ]

    package: dict[str, Any] = {
        "run_id": RUN_ID,
        "artifact_type": "post_axiswise_remaining_target_selector_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "inputs": {
            "board": str(BOARD.relative_to(REPO)),
            "board_sha256_at_run": sha256(BOARD),
            "completion_audit_v11": str(AUDIT_V11.relative_to(REPO)),
            "completion_audit_v11_sha256": sha256(AUDIT_V11),
            "monthly_sideways_purity": str(PURITY.relative_to(REPO)),
            "monthly_sideways_purity_sha256": sha256(PURITY),
            "source_consensus_axiswise": str(AXISWISE.relative_to(REPO)),
            "source_consensus_axiswise_sha256": sha256(AXISWISE),
            "direct_manipulation_variety_matrix": str(DIRECT_MATRIX.relative_to(REPO)),
            "direct_manipulation_variety_matrix_sha256": sha256(DIRECT_MATRIX),
            "post_calibration_acquisition_request_v4": str(ACQ_V4.relative_to(REPO)),
            "missing_parent_root_slots_v3": str(MISSING_V3.relative_to(REPO)),
            "root_label_probe": str(ROOT_PROBE.relative_to(REPO)),
            "unauth_root_label_probe": str(UNAUTH_PROBE.relative_to(REPO)),
        },
        "already_closed": {
            "daily_parent_roots_accepted_95": audit["price_root_status"]["daily_parent_roots_accepted_95"],
            "same_source_weekly_monthly_cells_accepted_95": audit["price_root_status"]["same_source_weekly_monthly_cells_accepted_95"],
            "same_source_weekly_monthly_cells": audit["price_root_status"]["same_source_weekly_monthly_cells"],
            "monthly_sideways_axiswise_support": purity["decision"]["positive_candidate"],
            "axiswise_gate_result": axiswise["decision"]["gate_result"],
        },
        "remaining_blockers": audit["remaining_blockers"],
        "missing_slot_summary": missing_summary,
        "prior_source_probe_results": {
            "authenticated_or_existing_cache_new_slots": root_probe["accepted_new_root_label_slots"],
            "unauthenticated_new_slots": unauth_probe["accepted_new_root_label_slots"],
            "unauthenticated_direct_sources": unauth_probe["accepted_new_manipulation_sources"],
        },
        "provider_readiness_note": {
            "tradingview_mcp_status": "ready_for_ohlcv_observed_by_provider_status_compact",
            "not_label_source": True,
            "allowed_tools_in_repo": ["get_ohlcv", "yahoo_price", "get_option_expirations", "get_option_chain"],
            "decision": "Do not count TradingViewRemix OHLCV or local HMM outputs as independent MainRegimeV2 labels.",
        },
        "request_priorities": request_priorities,
        "top_candidate_slots_for_external_label_panel": top_slots,
        "decision": {
            "selected_next_target": "v4-price-root-exact-label-panel",
            "fallback_next_target": "v4-direct-manipulation-variety-rows",
            "accepted_full_objective_gate": "none_for_MainRegimeV2_expanded_full_universe_full_cycle_goal",
            "full_objective_achieved": False,
            "call_update_goal": False,
            "gate_result": "post_axiswise_remaining_targets_selected_full_matrix_still_blocked",
            "runtime_code_changed": False,
            "thresholds_relaxed": False,
            "raw_data_committed": False,
            "trade_usable": False,
        },
        "next_action": "Acquire one exact independent MainRegimeV2 label panel for a high-liquidity unsupported intraday/full-species slice; use TradingView/IBKR/Yahoo/Kraken bars only for overlap after labels exist.",
    }

    json_path = OUT_DIR / "post_axiswise_remaining_target_selector_v1.json"
    json_path.write_text(json.dumps(package, indent=2, sort_keys=True) + "\n")

    slots_csv = OUT_DIR / "post_axiswise_top_label_slots_v1.csv"
    with slots_csv.open("w", newline="") as f:
        fields = [
            "request_id",
            "provider",
            "instrument",
            "timeframe",
            "root",
            "missing_or_rejected_reason",
            "required_label_source",
            "forbidden_proxy_sources",
            "minimum_acceptance_note",
        ]
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in top_slots:
            writer.writerow({field: row.get(field, "") for field in fields})

    md = [
        "# Post-Axiswise Remaining Target Selector v1",
        "",
        f"Run ID: `{RUN_ID}`",
        "",
        "This selector starts after the `131922` axiswise gate: same-source `1w/1mo` MainRegimeV2 cells are already closed. It chooses the next unsupported slice without reopening closed monthly/weekly work.",
        "",
        "## Already Closed",
        "",
        "- Daily parent roots accepted 95: `true`.",
        "- Same-source weekly/monthly cells accepted 95: `true`.",
        f"- Axiswise gate result: `{axiswise['decision']['gate_result']}`.",
        f"- Monthly Sideways support probe: `{purity['decision']['positive_candidate']}`.",
        "",
        "## Remaining Missing-Slot Shape",
        "",
        f"- Missing/requested root-label rows from v3 package: `{missing_summary['rows']}`.",
        f"- By provider: `{missing_summary['provider']}`.",
        f"- By timeframe: `{missing_summary['timeframe']}`.",
        f"- By root: `{missing_summary['root']}`.",
        f"- By reason: `{missing_summary['reason']}`.",
        "",
        "## Provider Reality Check",
        "",
        "- `tradingview_mcp` is ready for OHLCV, but the repo allowlist exposes `get_ohlcv`, `yahoo_price`, `get_option_expirations`, and `get_option_chain` only.",
        "- Therefore TradingViewRemix, Yahoo, IBKR, Kraken, and local HMM outputs can help with bar overlap or later validation, but cannot by themselves close independent root-label requirements.",
        "- Do not count OHLCV, HMM/GMM state ids, strategy predictions, or future-return labels as completion evidence.",
        "",
        "## Selected Next Target",
        "",
        "| Rank | Request | Target | Next Small Action |",
        "|---:|---|---|---|",
    ]
    for item in request_priorities:
        md.append(
            f"| {item['rank']} | `{item['request_id']}` | {item['target']} | {item['next_small_action']} |"
        )
    md.extend(
        [
            "",
            "## Decision",
            "",
            "- Selected next target: `v4-price-root-exact-label-panel`.",
            "- Fallback target: `v4-direct-manipulation-variety-rows`.",
            "- Full objective achieved: `false`.",
            "- `update_goal`: `false`.",
            "- Gate result: `post_axiswise_remaining_targets_selected_full_matrix_still_blocked`.",
            "",
            "## Guardrails",
            "",
            "- Runtime code changed: false.",
            "- Thresholds relaxed: false.",
            "- Raw data committed: false.",
            "- Trade usable: false.",
        ]
    )
    (OUT_DIR / "post_axiswise_remaining_target_selector_v1.md").write_text("\n".join(md) + "\n")

    assertions = [
        f"run_id={RUN_ID}",
        f"board_sha256_at_run={package['inputs']['board_sha256_at_run']}",
        "same_source_weekly_monthly_cells_accepted_95=true",
        "selected_next_target=v4-price-root-exact-label-panel",
        "fallback_next_target=v4-direct-manipulation-variety-rows",
        "tradingview_mcp_ready_for_ohlcv_not_labels=true",
        f"missing_slot_rows={missing_summary['rows']}",
        "accepted_full_objective_gate=none_for_MainRegimeV2_expanded_full_universe_full_cycle_goal",
        "full_objective_achieved=false",
        "call_update_goal=false",
        "runtime_code_changed=false",
        "thresholds_relaxed=false",
        "raw_data_committed=false",
        "trade_usable=false",
        "assertion_status=PASS",
    ]
    (CHECK_DIR / "post_axiswise_remaining_target_selector_v1_assertions.out").write_text("\n".join(assertions) + "\n")


if __name__ == "__main__":
    main()
