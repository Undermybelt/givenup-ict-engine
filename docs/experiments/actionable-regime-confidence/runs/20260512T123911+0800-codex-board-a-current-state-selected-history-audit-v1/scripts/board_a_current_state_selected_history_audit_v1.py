from __future__ import annotations

import csv
import hashlib
import json
import re
from pathlib import Path
from typing import Any


RUN_ID = "20260512T123911+0800-codex-board-a-current-state-selected-history-audit-v1"
RUNS = Path("docs/experiments/actionable-regime-confidence/runs")
ROOT = RUNS / RUN_ID
REPORT_DIR = ROOT / "board-a-current-state-selected-history-audit-v1"
CHECK_DIR = ROOT / "checks"
BOARD = Path("docs/plans/2026-05-10-actionable-regime-confidence-todo.md")

PROVIDER_GATE_RUN_ID = "20260512T122933+0800-codex-115700-provider-evidence-node-cross-context-gate-v1"
SELECTED_PREFLIGHT_RUN_ID = "20260512T123211+0800-codex-115700-selected-history-preflight-v1"
SELECTED_AQ_RUN_ID = "20260512T123227+0800-codex-115700-selected-history-btc-alias-aq-v1"
SPLIT_VALIDATION_RUN_ID = "20260512T123233+0800-codex-122351-provider-node-split-validation-v1"

PROVIDER_GATE_JSON = (
    RUNS
    / PROVIDER_GATE_RUN_ID
    / "115700-provider-evidence-node-cross-context-gate-v1"
    / "115700_provider_evidence_node_cross_context_gate_v1.json"
)
SELECTED_PREFLIGHT_JSON = (
    RUNS
    / SELECTED_PREFLIGHT_RUN_ID
    / "115700-selected-history-preflight-v1"
    / "115700_selected_history_preflight_v1.json"
)
SPLIT_VALIDATION_JSON = (
    RUNS
    / SPLIT_VALIDATION_RUN_ID
    / "122351-provider-node-split-validation-v1"
    / "122351_provider_node_split_validation_v1.json"
)
SELECTED_AQ_ROOT = RUNS / SELECTED_AQ_RUN_ID
SELECTED_AQ_COMMANDS = SELECTED_AQ_ROOT / "command-output"


def read_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def read_text(path: Path) -> str:
    try:
        return path.read_text()
    except FileNotFoundError:
        return ""


def read_exit(path: Path) -> int | None:
    text = read_text(path).strip()
    if not text:
        return None
    try:
        return int(text)
    except ValueError:
        return None


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def board_sha256() -> str:
    return hashlib.sha256(BOARD.read_bytes()).hexdigest()


def run_tomac_summary() -> dict[str, Any]:
    output_path = SELECTED_AQ_COMMANDS / "05_run_tomac_timerange_patched.out"
    output = read_text(output_path)
    strategy_blocks: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    for line in output.splitlines():
        if line.startswith("strategy:"):
            if current:
                strategy_blocks.append(current)
            current = {"strategy": line.split(":", 1)[1].strip()}
            continue
        if current is None:
            continue
        for key in ["sharpe", "sortino", "calmar", "total_profit_pct", "max_drawdown_pct", "trade_count", "win_rate_pct", "profit_factor"]:
            prefix = f"{key}:"
            if line.strip().startswith(prefix):
                value = line.split(":", 1)[1].strip()
                try:
                    current[key] = float(value) if "." in value or "-" in value else int(value)
                except ValueError:
                    current[key] = value
    if current:
        strategy_blocks.append(current)
    done_match = re.search(r"Done:\s+(\d+) succeeded,\s+(\d+) failed", output)
    return {
        "exit_initial_autoquant_venv": read_exit(SELECTED_AQ_COMMANDS / "04_run_tomac_autoquant_venv.exit"),
        "exit_timerange_patched": read_exit(SELECTED_AQ_COMMANDS / "05_run_tomac_timerange_patched.exit"),
        "done_succeeded": int(done_match.group(1)) if done_match else None,
        "done_failed": int(done_match.group(2)) if done_match else None,
        "strategies": strategy_blocks,
        "total_trade_count": sum(int(item.get("trade_count") or 0) for item in strategy_blocks),
        "output_path": str(output_path),
    }


def main() -> int:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)
    (ROOT / "run_id.txt").write_text(RUN_ID + "\n")

    provider_gate = read_json(PROVIDER_GATE_JSON)
    selected_preflight = read_json(SELECTED_PREFLIGHT_JSON)
    split_validation = read_json(SPLIT_VALIDATION_JSON)
    aq_prepare = read_json(SELECTED_AQ_COMMANDS / "02_auto_quant_prepare.out")
    aq_after_prepare = read_json(SELECTED_AQ_COMMANDS / "03_factor_research_after_prepare.out")
    tomac = run_tomac_summary()

    selected_results = selected_preflight.get("results") or []
    ready_actionable = [
        item
        for item in selected_results
        if (item.get("workflow_phase_detail") or {}).get("ready")
        and (item.get("workflow_phase_detail") or {}).get("actionable")
    ]
    selected_exit_ok = all(
        item.get("factor_research_exit") == 0 and item.get("workflow_exit") == 0
        for item in selected_results
    ) if selected_results else False

    decision = provider_gate.get("decision") or {}
    feature_gates = provider_gate.get("feature_gates") or []
    best_feature = None
    if feature_gates:
        best_feature = max(feature_gates, key=lambda item: float(item.get("best_bin_win_rate") or 0.0))

    checklist = [
        {
            "requirement": "same Board A markdown updated without disturbing concurrent sections",
            "status": "pending_board_append",
            "evidence": str(BOARD),
            "note": "artifact created first; board append must be done separately after re-reading tail/hash",
        },
        {
            "requirement": "each regime reaches >=95% confidence",
            "status": "fail",
            "evidence": str(PROVIDER_GATE_JSON),
            "note": f"max_bbn_probability={provider_gate.get('max_bbn_probability')}; accepted_feature_gates={decision.get('accepted_feature_gates')}",
        },
        {
            "requirement": "validate on other markets/instruments",
            "status": "fail",
            "evidence": str(PROVIDER_GATE_JSON),
            "note": f"instrument_families={provider_gate.get('instrument_families')}",
        },
        {
            "requirement": "validate on other periods/timeframes",
            "status": "partial_fail_closed",
            "evidence": str(SELECTED_PREFLIGHT_JSON),
            "note": "selected-history native preflight checked 1h/4h/1d, but all remain observe/not ready and still BTC-only",
        },
        {
            "requirement": "run ict-engine filter/BBN/CatBoost/execution-tree path",
            "status": "partial_fail_closed",
            "evidence": str(SELECTED_PREFLIGHT_JSON),
            "note": f"selected_history_exits_ok={selected_exit_ok}; ready_actionable_count={len(ready_actionable)}",
        },
        {
            "requirement": "run Auto-Quant on selected history",
            "status": "partial_fail_closed",
            "evidence": str(SELECTED_AQ_COMMANDS / "05_run_tomac_timerange_patched.out"),
            "note": f"prepare_status={aq_prepare.get('status')}; run_tomac_exit={tomac['exit_timerange_patched']}; total_trade_count={tomac['total_trade_count']}",
        },
        {
            "requirement": "remember IBKR TradingViewRemix YF Kraken provider lineage",
            "status": "partial_fail_closed",
            "evidence": str(PROVIDER_GATE_JSON),
            "note": "six-provider lineage exists upstream in 115700/121347; current selected-history/AQ run remains BTC selected-history only",
        },
        {
            "requirement": "no production BBN mutation or execution promotion without evidence",
            "status": "pass_fail_closed",
            "evidence": str(PROVIDER_GATE_JSON),
            "note": f"production_likelihood_mutation={decision.get('production_likelihood_mutation')}; promotion_allowed={decision.get('promotion_allowed')}",
        },
        {
            "requirement": "do not call update_goal until objective fully achieved",
            "status": "pass_fail_closed",
            "evidence": "current audit",
            "note": "strict objective remains incomplete",
        },
    ]

    split_decision = split_validation.get("decision") or {}

    payload = {
        "run_id": RUN_ID,
        "board_sha256_at_artifact_time": board_sha256(),
        "input_artifacts": {
            "provider_gate": str(PROVIDER_GATE_JSON),
            "selected_history_preflight": str(SELECTED_PREFLIGHT_JSON),
            "selected_history_aq_commands": str(SELECTED_AQ_COMMANDS),
            "split_validation": str(SPLIT_VALIDATION_JSON),
        },
        "selected_history_preflight": {
            "result_count": len(selected_results),
            "exits_all_zero": selected_exit_ok,
            "ready_actionable_count": len(ready_actionable),
            "preferred_for_user_selection": (selected_preflight.get("support") or {}).get("preferred_for_user_selection"),
            "source_state_mutated": selected_preflight.get("source_state_mutated"),
        },
        "selected_history_aq": {
            "prepare_exit": read_exit(SELECTED_AQ_COMMANDS / "02_auto_quant_prepare.exit"),
            "prepare_status": aq_prepare.get("status"),
            "prepare_data_ready": aq_prepare.get("data_ready"),
            "factor_research_after_prepare_exit": read_exit(SELECTED_AQ_COMMANDS / "03_factor_research_after_prepare.exit"),
            "factor_research_after_prepare_data_ready": ((aq_after_prepare.get("auto_quant_handoff_candidate") or {}).get("data_ready")),
            "tomac": tomac,
        },
        "provider_node_gate": {
            "gate": decision.get("gate"),
            "max_bbn_probability": provider_gate.get("max_bbn_probability"),
            "instrument_families": provider_gate.get("instrument_families"),
            "timeframes": provider_gate.get("timeframes"),
            "accepted_feature_gates": decision.get("accepted_feature_gates"),
            "best_feature": best_feature,
            "production_likelihood_mutation": decision.get("production_likelihood_mutation"),
        },
        "split_validation": {
            "gate": split_decision.get("gate"),
            "best_internal_candidate": split_decision.get("best_internal_candidate"),
            "promotion_allowed": split_decision.get("promotion_allowed"),
            "trade_usable": split_decision.get("trade_usable"),
        },
        "checklist": checklist,
        "gate": "board_a_current_state_selected_history_audit_v1=strict_goal_not_achieved_no_update_goal",
        "promotion_allowed": False,
        "trade_usable": False,
        "update_goal": False,
    }

    write_json(REPORT_DIR / "board_a_current_state_selected_history_audit_v1.json", payload)

    with (REPORT_DIR / "prompt_to_artifact_checklist_board_a_current_state_selected_history_audit_v1.csv").open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=["requirement", "status", "evidence", "note"])
        writer.writeheader()
        writer.writerows(checklist)

    md_lines = [
        "# Board A Current State Selected-History Audit v1",
        "",
        f"Run id: `{RUN_ID}`",
        f"Board SHA-256 at artifact time: `{payload['board_sha256_at_artifact_time']}`",
        "",
        "## Objective Readback",
        "- Required outcome: every regime at `>=95%` confidence, validated across other markets/instruments and periods/timeframes, through real Auto-Quant -> ict-engine -> Pre-Bayes/filter -> BBN -> CatBoost/path-ranker -> execution-tree evidence.",
        "- Current result: strict objective is not achieved.",
        "",
        "## Latest Evidence",
        f"- Provider-node cross-context gate `{PROVIDER_GATE_RUN_ID}` remains fail-closed: max BBN probability `{provider_gate.get('max_bbn_probability')}`, instruments `{provider_gate.get('instrument_families')}`, timeframes `{provider_gate.get('timeframes')}`, accepted feature gates `{decision.get('accepted_feature_gates')}`.",
        f"- Selected-history native preflight `{SELECTED_PREFLIGHT_RUN_ID}` ran `{len(selected_results)}` data paths; all command exits were zero: `{selected_exit_ok}`, but ready/actionable count is `{len(ready_actionable)}`.",
        f"- Selected-history Auto-Quant `{SELECTED_AQ_RUN_ID}` prepared data with status `{aq_prepare.get('status')}` and `data_ready={aq_prepare.get('data_ready')}`; patched `run_tomac` exit `{tomac['exit_timerange_patched']}` produced total trades `{tomac['total_trade_count']}` across `{len(tomac['strategies'])}` strategies.",
        f"- Provider-node split validation `{SPLIT_VALIDATION_RUN_ID}` best internal candidate is `{split_decision.get('best_internal_candidate')}`, still candidate-only.",
        "",
        "## Decision",
        f"- Gate: `{payload['gate']}`.",
        "- Do not mutate BBN likelihoods/CPDs from this packet.",
        "- Do not promote execution or trade use.",
        "- Do not call `update_goal`.",
        "",
        "## Next",
        "- Let active selected-history pairmap/run_tomac jobs finish, then only register their settled output if it adds non-duplicate evidence.",
        "- The remaining high-value gap is still non-BTC, non-1h/cross-period evidence plus a pre-trade BBN node that can lift a specific regime toward `>=95%` and survive execution-readiness gates.",
        "",
    ]
    (REPORT_DIR / "board_a_current_state_selected_history_audit_v1.md").write_text("\n".join(md_lines))

    assertions = [
        f"PASS run_id={RUN_ID}",
        f"PASS provider_gate_run_id={PROVIDER_GATE_RUN_ID}",
        f"PASS selected_preflight_run_id={SELECTED_PREFLIGHT_RUN_ID}",
        f"PASS selected_aq_run_id={SELECTED_AQ_RUN_ID}",
        f"PASS selected_history_exits_all_zero={selected_exit_ok}",
        f"FAIL_CLOSED ready_actionable_count={len(ready_actionable)}",
        f"FAIL_CLOSED max_bbn_probability={provider_gate.get('max_bbn_probability')}",
        f"FAIL_CLOSED accepted_feature_gates={decision.get('accepted_feature_gates')}",
        f"FAIL_CLOSED run_tomac_total_trade_count={tomac['total_trade_count']}",
        "PASS promotion_allowed=false",
        "PASS trade_usable=false",
        "PASS update_goal=false",
    ]
    (CHECK_DIR / "board_a_current_state_selected_history_audit_v1_assertions.out").write_text("\n".join(assertions) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
