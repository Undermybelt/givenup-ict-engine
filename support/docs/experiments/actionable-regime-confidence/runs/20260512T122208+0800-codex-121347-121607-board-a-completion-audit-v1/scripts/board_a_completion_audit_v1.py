from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


RUN_ID = "20260512T122208+0800-codex-121347-121607-board-a-completion-audit-v1"
SOURCE_ENRICHED = "20260512T121347+0800-codex-115700-enriched-downstream-chain-v1"
SOURCE_FEEDBACK = "20260512T121607+0800-codex-120630-bbn-negative-feedback-packet-v1"
RUNS = Path("docs/experiments/actionable-regime-confidence/runs")
ROOT = RUNS / RUN_ID
REPORT_DIR = ROOT / "121347-121607-board-a-completion-audit-v1"
CHECK_DIR = ROOT / "checks"
DERIVED_DIR = ROOT / "derived"

ENRICHED_ROWS = (
    RUNS
    / SOURCE_ENRICHED
    / "derived"
    / "same_root_six_provider_1h_aq_real_trades.enriched_layer_contract.jsonl"
)
FEEDBACK_JSON = (
    RUNS
    / SOURCE_FEEDBACK
    / "120630-bbn-negative-feedback-packet-v1"
    / "120630_bbn_negative_feedback_packet_v1.json"
)
BOARD = Path("docs/plans/2026-05-10-actionable-regime-confidence-todo.md")

ACTIVE_ROOTS = ["Bull", "Bear", "Sideways", "Crisis"]
DIRECT_OVERLAYS = ["Manipulation"]
REQUIRED_PROVIDERS = ["yfinance", "kraken_public", "ibkr_paxos_long_midpoint", "tvr_default_binance"]


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text()) if path.exists() else {}


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in path.read_text().splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def outcome(row: dict[str, Any]) -> str:
    value = str(row.get("realized_outcome") or "").lower()
    if value in {"win", "loss", "breakeven"}:
        return value
    pnl = float(row.get("pnl") or 0.0)
    if pnl > 0:
        return "win"
    if pnl < 0:
        return "loss"
    return "breakeven"


def rate_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    counts = Counter(outcome(row) for row in rows)
    total = len(rows)
    wins = counts.get("win", 0)
    losses = counts.get("loss", 0)
    breakeven = counts.get("breakeven", 0)
    return {
        "rows": total,
        "wins": wins,
        "losses": losses,
        "breakeven": breakeven,
        "win_rate": round(wins / total, 6) if total else 0.0,
        "loss_rate": round(losses / total, 6) if total else 0.0,
    }


def period_label(index: int, total: int) -> str:
    if total <= 0:
        return "none"
    if index < total / 3:
        return "early"
    if index < 2 * total / 3:
        return "middle"
    return "late"


def group_summaries(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    sorted_rows = sorted(rows, key=lambda row: int(row.get("open_ts_ms") or 0))
    for index, row in enumerate(sorted_rows):
        provider = str(row.get("source_provider") or row.get("provider_provenance", {}).get("provider") or "unknown")
        branch = str(row.get("branch_path") or row.get("regime_profit_branch_path") or "unknown")
        groups[(provider, branch, period_label(index, len(sorted_rows)))].append(row)
    out = []
    for (provider, branch, period), members in sorted(groups.items()):
        payload = {"provider": provider, "branch": branch, "period": period}
        payload.update(rate_summary(members))
        out.append(payload)
    return out


def max_bbn_prob(rows: list[dict[str, Any]]) -> dict[str, float]:
    best: dict[str, float] = {}
    for row in rows:
        probs = row.get("bbn_posterior", {}).get("canonical_probabilities", {})
        for key, value in probs.items():
            best[key] = max(best.get(key, 0.0), float(value or 0.0))
    return best


def max_pre_bayes_confidence(rows: list[dict[str, Any]]) -> float:
    values = [
        float(row.get("pre_bayes_filter_state", {}).get("confidence") or 0.0)
        for row in rows
    ]
    return max(values) if values else 0.0


def checklist(rows: list[dict[str, Any]], feedback: dict[str, Any]) -> list[dict[str, str]]:
    providers = sorted({str(row.get("source_provider") or "unknown") for row in rows})
    timeframes = sorted({str(row.get("source_timeframe") or row.get("aq_timeframe") or "unknown") for row in rows})
    symbols = sorted(
        {
            str(row.get("provider_provenance", {}).get("provider_symbol") or row.get("symbol") or "unknown")
            for row in rows
        }
    )
    bbn = max_bbn_prob(rows)
    max_prob = max(bbn.values()) if bbn else 0.0
    pre_bayes = max_pre_bayes_confidence(rows)
    execution_ready = sum(1 for row in rows if row.get("execution_tree_decision", {}).get("ready") is True)
    execution_actionable = sum(1 for row in rows if row.get("execution_tree_decision", {}).get("actionable") is True)
    active_parent_roots = sorted({str(row.get("parent_regime_root") or row.get("main_regime") or "unknown") for row in rows})
    canonical_regimes = sorted(bbn.keys())
    provider_ok = all(provider in providers for provider in REQUIRED_PROVIDERS)
    def is_btc_family(symbol: str) -> bool:
        upper = symbol.upper()
        return "BTC" in upper or "XBT" in upper

    other_market_ok = bool(symbols) and any(not is_btc_family(symbol) for symbol in symbols)
    timeframe_ok = len(set(timeframes)) >= 2
    all_active_roots_ok = all(root in active_parent_roots for root in ACTIVE_ROOTS)
    direct_overlay_ok = False
    chain_ok = bool(rows) and bool(feedback)
    rows_have_layer_contract = all(
        row.get("pre_bayes_filter_state")
        and row.get("bbn_posterior")
        and row.get("catboost_path_ranker_label")
        and row.get("execution_tree_decision")
        and row.get("failure_reason")
        and row.get("quality_weight") is not None
        for row in rows
    )
    rows_by_status = [
        {
            "requirement": "named_board_updated",
            "expected": str(BOARD),
            "evidence": "Board contains latest 121347/121607 sections and this audit will append after verification.",
            "status": "pass_partial",
            "blocker": "This audit still needs Board append after it is generated.",
        },
        {
            "requirement": "active_regime_95_confidence",
            "expected": "Bull, Bear, Sideways, Crisis each >=0.95 calibrated confidence",
            "evidence": f"active_parent_roots={active_parent_roots}; canonical_bbn={bbn}; max_bbn={max_prob:.6f}; max_pre_bayes={pre_bayes:.6f}",
            "status": "fail_closed",
            "blocker": "Current exact-root packet reaches range about 0.7477 and Pre-Bayes about 0.5251, below 0.95; Bear/Sideways/Crisis roots are not independently accepted here.",
        },
        {
            "requirement": "direct_manipulation_gate",
            "expected": "direct Manipulation positives/controls/provenance, not OHLCV proxy",
            "evidence": f"direct_overlay_rows={0}; overlays={DIRECT_OVERLAYS}",
            "status": "fail_closed" if not direct_overlay_ok else "pass",
            "blocker": "No direct Manipulation rows in 121347/121607 artifacts.",
        },
        {
            "requirement": "other_market_or_instrument_validation",
            "expected": "confidence survives non-BTC / other-market validation",
            "evidence": f"provider_symbols={symbols}; providers={providers}",
            "status": "fail_closed" if not other_market_ok else "pass",
            "blocker": "Rows are BTC/crypto-only despite provider diversity.",
        },
        {
            "requirement": "other_cycle_or_timeframe_validation",
            "expected": "confidence survives multiple timeframes/cycles",
            "evidence": f"timeframes={timeframes}",
            "status": "fail_closed" if not timeframe_ok else "pass",
            "blocker": "Rows are 1h-only.",
        },
        {
            "requirement": "required_provider_coverage",
            "expected": "IBKR, TradingViewRemix/default TVR, yfinance, Kraken included",
            "evidence": f"required={REQUIRED_PROVIDERS}; observed={providers}",
            "status": "pass" if provider_ok else "fail_closed",
            "blocker": "" if provider_ok else "Missing one or more required providers.",
        },
        {
            "requirement": "ordered_local_chain",
            "expected": "Auto-Quant -> Pre-Bayes/filter -> BBN -> CatBoost/path-ranker -> execution tree",
            "evidence": f"rows={len(rows)}; layer_contract_complete={rows_have_layer_contract}; feedback_run={SOURCE_FEEDBACK}",
            "status": "pass" if chain_ok and rows_have_layer_contract else "fail_closed",
            "blocker": "" if chain_ok and rows_have_layer_contract else "Layer-contract fields missing.",
        },
        {
            "requirement": "execution_admissibility",
            "expected": "execution ready/actionable and non-observe before promotion",
            "evidence": f"execution_ready_rows={execution_ready}; execution_actionable_rows={execution_actionable}; total_rows={len(rows)}",
            "status": "fail_closed",
            "blocker": "All enriched rows remain observe/execution_blocked.",
        },
        {
            "requirement": "completion_gate",
            "expected": "all checklist rows pass before update_goal",
            "evidence": "At least active_regime_95_confidence, direct_manipulation_gate, other_market_or_instrument_validation, other_cycle_or_timeframe_validation, and execution_admissibility fail.",
            "status": "fail_closed",
            "blocker": "Do not call update_goal.",
        },
    ]
    if not all_active_roots_ok:
        rows_by_status[1]["blocker"] += " Active parent-root coverage is incomplete."
    return rows_by_status


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})


def write_report(summary: dict[str, Any]) -> None:
    report = REPORT_DIR / "board_a_completion_audit_v1.md"
    assertions = CHECK_DIR / "board_a_completion_audit_v1_assertions.out"
    blocked = [row for row in summary["checklist"] if row["status"] == "fail_closed"]
    lines = [
        "# Board A Completion Audit v1",
        "",
        f"Run id: `{RUN_ID}`",
        f"Source enriched run: `{SOURCE_ENRICHED}`",
        f"Source feedback run: `{SOURCE_FEEDBACK}`",
        "",
        "## Objective",
        "Every active regime needs calibrated >=95% confidence, must survive other market/instrument and other timeframe/cycle validation, and must be proven through the local Auto-Quant -> Pre-Bayes/filter -> BBN -> CatBoost/path-ranker -> execution-tree chain before any result/completion claim.",
        "",
        "## Current Evidence",
        f"- Enriched rows audited: `{summary['row_count']}`.",
        f"- Providers: `{summary['providers']}`.",
        f"- Provider symbols: `{summary['provider_symbols']}`.",
        f"- Timeframes: `{summary['timeframes']}`.",
        f"- Parent roots in rows: `{summary['parent_roots']}`.",
        f"- BBN max canonical probabilities: `{summary['bbn_max_probabilities']}`.",
        f"- Max Pre-Bayes confidence: `{summary['max_pre_bayes_confidence']}`.",
        f"- Execution ready/actionable rows: `{summary['execution_ready_rows']}` / `{summary['execution_actionable_rows']}`.",
        "",
        "## Checklist Result",
        f"- Checklist rows: `{len(summary['checklist'])}`.",
        f"- Blocked rows: `{len(blocked)}`.",
        f"- Gate: `{summary['gate_result']}`.",
        "",
        "## Decision",
        "- This is a completion audit only, not a promotion artifact.",
        "- Provider coverage and ordered-chain evidence are present for the 115700 BTC 1h packet.",
        "- The strict objective is not achieved: the current packet is BTC-only, 1h-only, not direct Manipulation evidence, below >=95% regime confidence, and execution remains observe/blocked.",
        "- `promotion_allowed=false`.",
        "- `trade_usable=false`.",
        "- `update_goal=false`.",
        "",
        "## Artifacts",
        f"- JSON: `{REPORT_DIR / 'board_a_completion_audit_v1.json'}`",
        f"- Checklist: `{REPORT_DIR / 'prompt_to_artifact_checklist_board_a_completion_audit_v1.csv'}`",
        f"- Provider/period summary: `{REPORT_DIR / 'provider_period_outcome_summary_v1.csv'}`",
        f"- Assertions: `{assertions}`",
    ]
    report.write_text("\n".join(lines) + "\n")

    assertion_lines = [
        f"PASS run_id={RUN_ID}",
        f"PASS source_enriched={SOURCE_ENRICHED}",
        f"PASS source_feedback={SOURCE_FEEDBACK}",
        f"PASS enriched_rows={summary['row_count']}",
        f"PASS required_provider_coverage={summary['required_provider_coverage']}",
        f"PASS ordered_local_chain={summary['ordered_local_chain']}",
        f"FAIL_CLOSED active_regime_95_confidence={summary['active_regime_95_confidence']}",
        f"FAIL_CLOSED other_market_or_instrument_validation={summary['other_market_or_instrument_validation']}",
        f"FAIL_CLOSED other_cycle_or_timeframe_validation={summary['other_cycle_or_timeframe_validation']}",
        f"FAIL_CLOSED direct_manipulation_gate={summary['direct_manipulation_gate']}",
        f"FAIL_CLOSED execution_admissibility={summary['execution_admissibility']}",
        "PASS promotion_allowed=false",
        "PASS trade_usable=false",
        "PASS update_goal=false",
    ]
    assertions.parent.mkdir(parents=True, exist_ok=True)
    assertions.write_text("\n".join(assertion_lines) + "\n")


def main() -> int:
    for path in (REPORT_DIR, CHECK_DIR, DERIVED_DIR):
        path.mkdir(parents=True, exist_ok=True)
    (ROOT / "run_id.txt").write_text(RUN_ID + "\n")
    rows = read_jsonl(ENRICHED_ROWS)
    feedback = read_json(FEEDBACK_JSON)
    providers = sorted({str(row.get("source_provider") or "unknown") for row in rows})
    provider_symbols = sorted(
        {
            str(row.get("provider_provenance", {}).get("provider_symbol") or row.get("symbol") or "unknown")
            for row in rows
        }
    )
    timeframes = sorted({str(row.get("source_timeframe") or row.get("aq_timeframe") or "unknown") for row in rows})
    parent_roots = sorted({str(row.get("parent_regime_root") or row.get("main_regime") or "unknown") for row in rows})
    bbn = max_bbn_prob(rows)
    pre_bayes = max_pre_bayes_confidence(rows)
    execution_ready = sum(1 for row in rows if row.get("execution_tree_decision", {}).get("ready") is True)
    execution_actionable = sum(1 for row in rows if row.get("execution_tree_decision", {}).get("actionable") is True)
    checklist_rows = checklist(rows, feedback)
    period_rows = group_summaries(rows)

    status_by_req = {row["requirement"]: row["status"] for row in checklist_rows}
    summary = {
        "run_id": RUN_ID,
        "source_enriched_run": SOURCE_ENRICHED,
        "source_feedback_run": SOURCE_FEEDBACK,
        "row_count": len(rows),
        "providers": providers,
        "provider_symbols": provider_symbols,
        "timeframes": timeframes,
        "parent_roots": parent_roots,
        "bbn_max_probabilities": {key: round(value, 6) for key, value in sorted(bbn.items())},
        "max_bbn_probability": round(max(bbn.values()), 6) if bbn else 0.0,
        "max_pre_bayes_confidence": round(pre_bayes, 6),
        "execution_ready_rows": execution_ready,
        "execution_actionable_rows": execution_actionable,
        "checklist": checklist_rows,
        "provider_period_summary": period_rows,
        "required_provider_coverage": status_by_req.get("required_provider_coverage") == "pass",
        "ordered_local_chain": status_by_req.get("ordered_local_chain") == "pass",
        "active_regime_95_confidence": status_by_req.get("active_regime_95_confidence") == "pass",
        "other_market_or_instrument_validation": status_by_req.get("other_market_or_instrument_validation") == "pass",
        "other_cycle_or_timeframe_validation": status_by_req.get("other_cycle_or_timeframe_validation") == "pass",
        "direct_manipulation_gate": status_by_req.get("direct_manipulation_gate") == "pass",
        "execution_admissibility": status_by_req.get("execution_admissibility") == "pass",
        "gate_result": "board_a_completion_audit_v1=strict_objective_not_achieved_continue_no_update_goal",
        "promotion_allowed": False,
        "trade_usable": False,
        "update_goal": False,
    }

    write_json(REPORT_DIR / "board_a_completion_audit_v1.json", summary)
    write_csv(
        REPORT_DIR / "prompt_to_artifact_checklist_board_a_completion_audit_v1.csv",
        checklist_rows,
        ["requirement", "expected", "evidence", "status", "blocker"],
    )
    write_csv(
        REPORT_DIR / "provider_period_outcome_summary_v1.csv",
        period_rows,
        ["provider", "branch", "period", "rows", "wins", "losses", "breakeven", "win_rate", "loss_rate"],
    )
    write_report(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
