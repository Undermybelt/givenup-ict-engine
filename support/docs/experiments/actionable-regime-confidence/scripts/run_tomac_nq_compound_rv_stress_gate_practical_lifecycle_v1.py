#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


SCRIPT = Path(__file__).resolve()
BASE = SCRIPT.parents[1]
REPO = BASE.parents[3]
RESEARCH_SCRIPTS = REPO / "support/scripts/research"
if str(RESEARCH_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(RESEARCH_SCRIPTS))

from same_tree_practical_closure import (  # noqa: E402
    DEPLOY_READY_READINESS_CONTRACT,
    REQUIRED_COMMAND_RESULT_STAGES,
    write_same_tree_practical_closure_packet,
)


STAMP = datetime.now(ZoneInfo("Asia/Shanghai")).strftime("%Y%m%dT%H%M%S+0800")
DEFAULT_MATERIALIZATION_ROOT = Path(
    "/tmp/ict-engine-nq-compound-rv-stress-feedback-materialization-20260530T043351+0800"
)
ROOT = Path(f"/tmp/ict-engine-nq-compound-rv-stress-practical-lifecycle-{STAMP}")

SYMBOL = "TOMAC_NQ_COMPOUND_RV_STRESS_GATE_PRACTICAL_LIFECYCLE_V1"
FACTOR_ID = "nq_compound_trend_rrr_chopfilter_rv_stress_gate_rescore_v1"
PARENT_FACTOR_ID = "nq_compound_trend_rrr_chopfilter_v1"
BRANCH_PATH = (
    "US index futures -> NQ -> ETH/full_retained_session -> 1m parent execution + shifted 5m/15m/30m/1h/4h/1d context "
    "-> HtfTrendRegime -> ChopFilter(ER>=0.35,n40) -> MomentumResonance -> CompoundTrendRrrBreadth "
    "-> FixedRrrBracket -> RealizedVolatilityStressGate(30m_abs_ret16_max <= 0.04174409724) "
    "-> PracticalLifecycleContinuation"
)

STATE = ROOT / "state"
CHECKS = ROOT / "checks"
SUMMARIES = ROOT / "summaries"


def configure_paths(root: Path) -> None:
    global ROOT, STATE, CHECKS, SUMMARIES
    ROOT = Path(root)
    STATE = ROOT / "state"
    CHECKS = ROOT / "checks"
    SUMMARIES = ROOT / "summaries"


def read_json(path: Path) -> dict:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def command_results_cover_practical_stages(value: object) -> bool:
    if not isinstance(value, list):
        return False
    stages = {
        str(row.get("stage") or "").strip().lower().replace("-", "_").replace(" ", "_")
        for row in value
        if isinstance(row, dict)
    }
    return all(stage in stages for stage in REQUIRED_COMMAND_RESULT_STAGES)


def staged_command_results(materialization_root: Path) -> list[dict]:
    for path in (
        materialization_root / "checks" / "terminal_metrics.json",
        materialization_root / "summaries" / "terminal_summary.json",
    ):
        payload = read_json(path)
        rows = payload.get("command_results")
        if command_results_cover_practical_stages(rows):
            return rows
    return []


def terminal_metrics(root: Path) -> dict:
    return read_json(root / "checks" / "terminal_metrics.json")


def child_rescore_metrics(materialization_root: Path) -> tuple[dict, str | None]:
    material = terminal_metrics(materialization_root)
    child_root = material.get("child_rescore_root")
    if not isinstance(child_root, str) or not child_root.strip():
        return ({}, None)
    child_path = Path(child_root) / "checks" / "terminal_metrics.json"
    return (read_json(child_path), str(child_path))


def market_data_provenance(materialization_root: Path) -> dict:
    payload = terminal_metrics(materialization_root)
    provenance = payload.get("market_data_provenance")
    if isinstance(provenance, dict) and provenance:
        out = dict(provenance)
        source_payload = str(materialization_root / "checks" / "terminal_metrics.json")
    else:
        child_payload, child_payload_path = child_rescore_metrics(materialization_root)
        child_provenance = child_payload.get("market_data_provenance")
        if isinstance(child_provenance, dict) and child_provenance:
            out = dict(child_provenance)
            source_payload = child_payload_path
        else:
            out = {
                "status": "missing_explicit_market_data_provenance",
                "source_class": None,
                "return_sanity": {"status": "missing_explicit_return_sanity"},
            }
            source_payload = None
    out.setdefault("materialization_root", str(materialization_root))
    if source_payload:
        out.setdefault("source_payload", source_payload)
    out.setdefault("status", "missing_explicit_market_data_provenance")
    out.setdefault("source_class", None)
    out.setdefault("return_sanity", {"status": "missing_explicit_return_sanity"})
    return out


def first_present(*values: object) -> object:
    for value in values:
        if value is not None:
            return value
    return None


def practical_evidence_fields(materialization_root: Path | None) -> dict:
    if materialization_root is None:
        return {
            "session_scope": None,
            "rth_filter_applied": None,
            "retained_session_coverage": {"status": "missing_explicit_retained_session_coverage"},
            "promotion_cost_verified": False,
            "cost_model": {"status": "missing_explicit_verified_cost_model"},
        }
    material = terminal_metrics(materialization_root)
    child, _child_path = child_rescore_metrics(materialization_root)
    return {
        "session_scope": first_present(material.get("session_scope"), child.get("session_scope")),
        "rth_filter_applied": first_present(material.get("rth_filter_applied"), child.get("rth_filter_applied")),
        "retained_session_coverage": first_present(
            material.get("retained_session_coverage"),
            child.get("retained_session_coverage"),
            {"status": "missing_explicit_retained_session_coverage"},
        ),
        "promotion_cost_verified": first_present(
            material.get("promotion_cost_verified"),
            child.get("promotion_cost_verified"),
            False,
        )
        is True,
        "cost_model": first_present(
            material.get("cost_model"),
            child.get("cost_model"),
            {"status": "missing_explicit_verified_cost_model"},
        ),
    }


def normalized_text(value: object) -> str:
    return str(value or "").strip().lower()


def positive_int(value: object) -> int:
    if isinstance(value, bool):
        return 0
    if isinstance(value, int):
        return value
    if isinstance(value, float) and value.is_integer():
        return int(value)
    if isinstance(value, str) and value.strip().isdigit():
        return int(value.strip())
    return 0


def lifecycle_surface(policy: dict) -> dict:
    lifecycle = policy.get("factor_profitability_lifecycle")
    return lifecycle if isinstance(lifecycle, dict) else {}


def deploy_ready_from_policy(policy: dict) -> bool:
    lifecycle = lifecycle_surface(policy)
    return bool(
        policy.get("deploy_ready") is True
        or lifecycle.get("deploy_ready") is True
        or positive_int(policy.get("deploy_ready_count")) > 0
        or positive_int(lifecycle.get("deploy_ready_count")) > 0
    )


def funded_live_fill_required_from_policy(policy: dict) -> object:
    lifecycle = lifecycle_surface(policy)
    if "funded_live_fill_required" in lifecycle:
        return lifecycle.get("funded_live_fill_required")
    return policy.get("funded_live_fill_required")


def readiness_contract_from_policy(policy: dict) -> object:
    lifecycle = lifecycle_surface(policy)
    return lifecycle.get("readiness_contract") or policy.get("readiness_contract")


def validation_counters(trace_output: dict) -> dict[str, str]:
    counters: dict[str, str] = {}
    for line in trace_output.get("split_reason_lineage") or []:
        for key in ("raw_scored_mature", "production_validation", "observation_validation"):
            marker = f"{key}="
            if marker in line:
                counters[key] = line.split(marker, 1)[1].split()[0].strip()
    return counters


def ratio_covers(value: str | None) -> bool:
    if not value or "/" not in value:
        return False
    left, right = value.split("/", 1)
    try:
        actual = int(left)
        required = int(right)
    except ValueError:
        return False
    return required > 0 and actual >= required


def exact_branch_survived(candidate: dict, trace_output: dict, closed_loop: dict) -> bool:
    values = [
        candidate.get("path_id"),
        candidate.get("path_label"),
        candidate.get("branch_path"),
        trace_output.get("path_id"),
        trace_output.get("path_label"),
        trace_output.get("branch_path"),
        closed_loop.get("path_id"),
        closed_loop.get("path_label"),
        closed_loop.get("branch_path"),
    ]
    return BRANCH_PATH in values


def branch_local_admitted(closed_loop: dict) -> bool:
    status = normalized_text(closed_loop.get("status") or closed_loop.get("admission_status"))
    return bool(closed_loop.get("ready") is True and closed_loop.get("actionable") is True) or status in {
        "admitted",
        "ready",
        "execution_ready",
    }


def materialization_summary(materialization_root: Path) -> dict:
    return read_json(materialization_root / "checks" / "terminal_metrics.json")


def write_summary(command_results: list[dict], data_summary: dict, materialization_root: Path | None = None) -> dict:
    workflow = read_json(STATE / SYMBOL / "workflow_snapshot.json")
    candidate = read_json(STATE / SYMBOL / "execution_candidate.json")
    trace = read_json(STATE / SYMBOL / "execution_tree_trace.json")
    trace_output = trace.get("output") if isinstance(trace.get("output"), dict) else trace
    policy = read_json(STATE / SYMBOL / "policy_training/structural_path_ranking_target_summary.json")
    closed_loop = workflow.get("closed_loop_branch_admission") or trace.get("closed_loop_branch_admission") or {}
    counters = validation_counters(trace_output)
    actionable = bool(candidate.get("actionable") or trace_output.get("actionable") or closed_loop.get("actionable"))
    candidate_status = str(candidate.get("candidate_status") or closed_loop.get("candidate_status") or trace_output.get("candidate_status") or "")
    exact_survived = exact_branch_survived(candidate, trace_output, closed_loop)
    all_ok = bool(command_results) and all(
        row.get("exit") == 0 and row.get("timed_out") is False for row in command_results
    )
    material = materialization_summary(materialization_root) if materialization_root else {}
    evidence_fields = practical_evidence_fields(materialization_root)
    metrics = {
        "schema_version": "tomac-nq-compound-rv-stress-practical-lifecycle-terminal/v1",
        "status": "practical_lifecycle_evaluating",
        "run_root": str(ROOT),
        "symbol": SYMBOL,
        "factor_id": FACTOR_ID,
        "parent_factor_id": PARENT_FACTOR_ID,
        "branch_path": BRANCH_PATH,
        "materialization_root": str(materialization_root) if materialization_root else None,
        "materialization_status": material.get("status"),
        "feedback_rows": material.get("feedback_rows"),
        "best_gate": material.get("best_gate"),
        "best_threshold": material.get("best_threshold"),
        "command_results": command_results,
        "all_command_exits_zero": all_ok,
        "exact_branch_survived": exact_survived,
        "execution_candidate_actionable": actionable,
        "execution_candidate_status": candidate_status,
        "branch_local_admitted": branch_local_admitted(closed_loop) and exact_survived,
        "validation_ready": all(ratio_covers(counters.get(key)) for key in ("raw_scored_mature", "production_validation", "observation_validation")),
        "validation_counters": counters,
        "path_ranker_score_visible_to_execution_tree": trace_output.get("path_ranker_score_visible_to_execution_tree"),
        "path_ranker_score_used_by_execution_tree": trace_output.get("path_ranker_score_used_by_execution_tree"),
        "path_ranker_used": trace_output.get("path_ranker_score_used_by_execution_tree") is True,
        "policy_training_summary": policy,
        "learning_admission_status": policy.get("learning_admission_status"),
        "paper_admission_status": policy.get("paper_admission_status"),
        "deploy_ready": deploy_ready_from_policy(policy),
        "live_trade_status": policy.get("live_trade_status"),
        "funded_live_fill_required": funded_live_fill_required_from_policy(policy),
        "readiness_contract": readiness_contract_from_policy(policy),
        "market_data_provenance": data_summary,
        "session_scope": evidence_fields["session_scope"],
        "rth_filter_applied": evidence_fields["rth_filter_applied"],
        "retained_session_coverage": evidence_fields["retained_session_coverage"],
        "promotion_cost_verified": evidence_fields["promotion_cost_verified"],
        "cost_model": evidence_fields["cost_model"],
        "promotion_allowed": False,
        "trade_usable": False,
        "update_goal": False,
    }
    write_json(CHECKS / "terminal_metrics.json", metrics)
    packet = write_same_tree_practical_closure_packet(
        metrics,
        SUMMARIES / "same_tree_practical_closure.json",
        evidence_packet="checks/terminal_metrics.json",
    )
    metrics["status"] = "practical_closure_pass" if packet is not None else "practical_lifecycle_fail_closed"
    # Practical authority lives in the canonical same-tree packet. The wrapper
    # terminal metrics stay fail-closed so local lifecycle readbacks cannot
    # self-promote through stale workflow flags.
    metrics["promotion_allowed"] = False
    metrics["trade_usable"] = False
    metrics["update_goal"] = False
    write_json(CHECKS / "terminal_metrics.json", metrics)
    summary = {
        "status": metrics["status"],
        "factor_id": FACTOR_ID,
        "branch_path": BRANCH_PATH,
        "all_command_exits_zero": all_ok,
        "exact_branch_survived": exact_survived,
        "execution_candidate_actionable": actionable,
        "execution_candidate_status": candidate_status,
        "branch_local_admitted": metrics["branch_local_admitted"],
        "validation_ready": metrics["validation_ready"],
        "path_ranker_score_used_by_execution_tree": metrics["path_ranker_score_used_by_execution_tree"],
        "promotion_allowed": False,
        "trade_usable": False,
        "update_goal": False,
        "same_tree_practical_closure": str(SUMMARIES / "same_tree_practical_closure.json") if packet else None,
    }
    write_json(SUMMARIES / "terminal_summary.json", summary)
    return metrics


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Summarize same-tree practical lifecycle evidence for the NQ compound RV-stress child gate."
    )
    parser.add_argument("--root", default=str(ROOT))
    parser.add_argument("--materialization-root", default=str(DEFAULT_MATERIALIZATION_ROOT))
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = Path(args.root)
    materialization_root = Path(args.materialization_root)
    configure_paths(root)
    for directory in (STATE, CHECKS, SUMMARIES):
        directory.mkdir(parents=True, exist_ok=True)
    metrics = write_summary(
        staged_command_results(materialization_root),
        market_data_provenance(materialization_root),
        materialization_root,
    )
    print(json.dumps({"status": metrics["status"], "feedback_rows": metrics.get("feedback_rows")}, sort_keys=True))
    return 0 if (SUMMARIES / "same_tree_practical_closure.json").exists() else 2


if __name__ == "__main__":
    raise SystemExit(main())
