#!/usr/bin/env python3
"""Canonical same-tree practical-closure packet builder.

This helper is intentionally small and strict. Wrapper scripts may produce
terminal metrics, but the pass packet that objective closure trusts must come
from one owner with one validation contract.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ALLOWED_MARKET_DATA_SOURCE_CLASSES = {
    "roll_adjusted_clean_feather",
    "verified_provider_historical",
    "ibkr_historical_verified",
    "paper_execution_feedback",
    "live_execution_feedback",
    "paper_trade_feedback",
    "live_trade_feedback",
    "broker_execution_feedback",
}
DISALLOWED_MARKET_DATA_SOURCE_CLASSES = {
    "raw_contract_stitching",
    "raw_csv_stitching",
    "raw_local_csv_stitching",
    "raw_databento_contract_stitching",
    "tomac_raw_csv",
    "raw_local_csv",
}
DEPLOY_READY_READINESS_CONTRACT = (
    "deploy_ready_from_backtest_autoquant_provider_or_paper_sim_execution_chain_not_funded_fill"
)
REQUIRED_COMMAND_RESULT_STAGES: tuple[str, ...] = (
    "provider_data",
    "pre_bayes",
    "bbn_workflow",
    "path_ranker",
    "execution_tree",
    "feedback_update",
    "policy_training",
)


def build_same_tree_practical_closure_packet(
    metrics: dict[str, Any],
    *,
    evidence_packet: str = "checks/terminal_metrics.json",
) -> dict[str, Any] | None:
    """Return a pass packet only when metrics prove the full practical chain."""
    if not evidence_packet.strip():
        return None
    if not metrics_prove_same_tree_practical_closure(metrics):
        return None
    return {
        "schema_version": "same-tree-practical-closure/v1",
        "status": "pass",
        "branch_path": metrics.get("branch_path"),
        "factor_id": metrics.get("factor_id"),
        "promotion_allowed": True,
        "trade_usable": True,
        "update_goal": metrics.get("update_goal") is True,
        "deploy_ready": True,
        "funded_live_fill_required": False,
        "readiness_contract": DEPLOY_READY_READINESS_CONTRACT,
        "provider_execution_feedback_chain": "pass",
        "evidence_packet": evidence_packet,
        "path_ranker_score_used_by_execution_tree": metrics.get(
            "path_ranker_score_used_by_execution_tree"
        ),
        "validation_counters": metrics.get("validation_counters"),
    }


def write_same_tree_practical_closure_packet(
    metrics: dict[str, Any],
    packet_path: Path,
    *,
    evidence_packet: str = "checks/terminal_metrics.json",
) -> dict[str, Any] | None:
    """Write or remove a same-tree practical-closure packet from metrics."""
    packet = build_same_tree_practical_closure_packet(metrics, evidence_packet=evidence_packet)
    packet_path.parent.mkdir(parents=True, exist_ok=True)
    if packet is None:
        packet_path.unlink(missing_ok=True)
        return None
    packet_path.write_text(json.dumps(packet, indent=2) + "\n", encoding="utf-8")
    return packet


def metrics_prove_same_tree_practical_closure(metrics: dict[str, Any]) -> bool:
    """Return true only for complete same-tree practical lifecycle evidence."""
    if metrics.get("promotion_allowed") is not True or metrics.get("trade_usable") is not True:
        return False
    if metrics.get("all_command_exits_zero") is not True:
        return False
    if metrics.get("exact_branch_survived") is not True:
        return False
    if metrics.get("execution_candidate_actionable") is not True:
        return False
    if metrics.get("branch_local_admitted") is not True:
        return False
    if metrics.get("validation_ready") is not True:
        return False
    if metrics.get("path_ranker_used") is not True:
        return False
    if metrics.get("path_ranker_score_used_by_execution_tree") is not True:
        return False
    candidate_status = str(metrics.get("execution_candidate_status") or "")
    if candidate_status in {"", "no_trade", "observe", "discard"}:
        return False
    if not validation_counters_cover_practical_chain(metrics.get("validation_counters")):
        return False
    if not policy_training_summary_proves_practical_closure(metrics.get("policy_training_summary")):
        return False
    if not lifecycle_tuple_proves_practical_closure(metrics):
        return False
    if not market_data_provenance_proves_practical_closure(metrics.get("market_data_provenance")):
        return False
    return command_results_prove_practical_closure(metrics.get("command_results"))


def command_results_prove_practical_closure(value: object) -> bool:
    if not isinstance(value, list) or not value:
        return False
    unmatched_stages: list[str] = []
    for row in value:
        if not isinstance(row, dict):
            return False
        if row.get("exit") != 0 or row.get("timed_out") is not False:
            return False
        stage = normalized_key(row.get("stage"))
        if stage not in REQUIRED_COMMAND_RESULT_STAGES:
            return False
        name = normalized_text(row.get("name"))
        if not name:
            return False
        unmatched_stages.append(stage)
    for required_stage in REQUIRED_COMMAND_RESULT_STAGES:
        matched_index = next(
            (index for index, stage in enumerate(unmatched_stages) if stage == required_stage),
            None,
        )
        if matched_index is None:
            return False
        unmatched_stages.pop(matched_index)
    return True


def lifecycle_tuple_proves_practical_closure(metrics: dict[str, Any]) -> bool:
    return (
        normalized_text(metrics.get("learning_admission_status")) == "admitted"
        and normalized_text(metrics.get("paper_admission_status")) == "ready"
        and normalized_text(metrics.get("live_trade_status")) == "ready"
        and metrics.get("deploy_ready") is True
        and metrics.get("funded_live_fill_required") is False
        and normalized_text(metrics.get("readiness_contract"))
        == DEPLOY_READY_READINESS_CONTRACT
    )


def policy_training_summary_proves_practical_closure(value: object) -> bool:
    if not isinstance(value, dict) or not value:
        return False
    lifecycle = value.get("factor_profitability_lifecycle")
    if lifecycle is None and any(
        key in value
        for key in (
            "learning_admitted_count",
            "paper_ready_count",
            "live_ready_count",
            "live_trade_usable_count",
            "promotion_allowed",
            "trade_usable",
        )
    ):
        lifecycle = value
    if not isinstance(lifecycle, dict):
        return False
    required_positive_counts = (
        "learning_admitted_count",
        "paper_ready_count",
        "deploy_ready_count",
        "live_ready_count",
        "live_trade_usable_count",
    )
    if any(positive_int(lifecycle.get(key)) <= 0 for key in required_positive_counts):
        return False
    return (
        lifecycle.get("promotion_allowed") is True
        and lifecycle.get("trade_usable") is True
        and lifecycle.get("funded_live_fill_required") is False
        and normalized_text(lifecycle.get("readiness_contract"))
        == DEPLOY_READY_READINESS_CONTRACT
    )


def market_data_provenance_proves_practical_closure(value: object) -> bool:
    if not isinstance(value, dict):
        return False
    if normalized_text(value.get("status")) != "pass":
        return False
    source_class = normalized_key(value.get("source_class") or value.get("provenance_class"))
    if source_class in DISALLOWED_MARKET_DATA_SOURCE_CLASSES:
        return False
    if source_class not in ALLOWED_MARKET_DATA_SOURCE_CLASSES:
        return False
    for key in ("raw_contract_stitching", "raw_csv_stitching", "raw_local_csv_stitching"):
        if value.get(key) is True:
            return False
    return return_sanity_proves_practical_closure(value.get("return_sanity"))


def return_sanity_proves_practical_closure(value: object) -> bool:
    if not isinstance(value, dict):
        return False
    if normalized_text(value.get("status")) != "pass":
        return False
    if positive_int(value.get("extreme_abs_gross_gt_10pct_count")) > 0:
        return False
    if positive_int(value.get("parse_bad_rows")) > 0:
        return False
    max_abs_gross_return_pct = optional_float(value.get("max_abs_gross_return_pct"))
    if max_abs_gross_return_pct is not None and max_abs_gross_return_pct > 10.0:
        return False
    return True


def validation_counters_cover_practical_chain(value: object) -> bool:
    if not isinstance(value, dict):
        return False
    for key in ("raw_scored_mature", "production_validation", "observation_validation"):
        actual, required = parse_ratio(value.get(key))
        if required <= 0 or actual < required:
            return False
    return True


def parse_ratio(value: object) -> tuple[int, int]:
    if not isinstance(value, str) or "/" not in value:
        return (0, 0)
    left, right = value.split("/", 1)
    try:
        return (int(left), int(right))
    except ValueError:
        return (0, 0)


def optional_float(value: object) -> float | None:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value.strip())
        except ValueError:
            return None
    return None


def positive_int(value: object) -> int:
    if isinstance(value, bool):
        return 0
    if isinstance(value, int):
        return value
    if isinstance(value, float) and value.is_integer():
        return int(value)
    if isinstance(value, str):
        text = value.strip()
        if text.isdigit():
            return int(text)
    return 0


def normalized_text(value: object) -> str:
    return str(value or "").strip().lower()


def normalized_key(value: object) -> str:
    return normalized_text(value).replace("-", "_").replace(" ", "_")
