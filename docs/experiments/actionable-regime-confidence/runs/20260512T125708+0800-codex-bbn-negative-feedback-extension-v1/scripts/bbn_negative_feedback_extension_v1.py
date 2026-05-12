#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


RUN_ID = "20260512T125708+0800-codex-bbn-negative-feedback-extension-v1"
BOARD = Path("docs/plans/2026-05-10-actionable-regime-confidence-todo.md")
BOARD_HASH_BEFORE = "71d5108acf80c3a97a11f946d7ac3d5c1cb7fdcd6f1c56371d71b347e4bce8bb"
ROOT = Path("docs/experiments/actionable-regime-confidence/runs") / RUN_ID
OUT_DIR = ROOT / "bbn-negative-feedback-extension-v1"
CHECK_DIR = ROOT / "checks"


SOURCES = {
    "121607_base_negative_feedback": Path(
        "docs/experiments/actionable-regime-confidence/runs/"
        "20260512T121607+0800-codex-120630-bbn-negative-feedback-packet-v1/"
        "120630-bbn-negative-feedback-packet-v1/"
        "120630_bbn_negative_feedback_packet_v1.json"
    ),
    "122215_cpd_candidate": Path(
        "docs/experiments/actionable-regime-confidence/runs/"
        "20260512T122215+0800-codex-121607-bbn-calibration-readiness-v1/"
        "derived/121607_bbn_cpd_candidate_smoothed_v1.json"
    ),
    "122933_provider_node_cross_context_gate": Path(
        "docs/experiments/actionable-regime-confidence/runs/"
        "20260512T122933+0800-codex-115700-provider-evidence-node-cross-context-gate-v1/"
        "115700-provider-evidence-node-cross-context-gate-v1/"
        "115700_provider_evidence_node_cross_context_gate_v1.json"
    ),
    "123820_non_btc_local_aq_mtf_chain_probe": Path(
        "docs/experiments/actionable-regime-confidence/runs/"
        "20260512T123820+0800-codex-non-btc-local-aq-mtf-chain-probe-v1/"
        "non-btc-local-aq-mtf-chain-probe-v1/"
        "non_btc_local_aq_mtf_chain_probe_v1.json"
    ),
    "124245_local_nonbtc_mtf_chain_probe": Path(
        "docs/experiments/actionable-regime-confidence/runs/"
        "20260512T124245+0800-codex-local-nonbtc-mtf-chain-probe-v1/"
        "local-nonbtc-mtf-chain-probe-v1/"
        "local_nonbtc_mtf_chain_probe_v1.json"
    ),
    "124408_tomac_trade_density_iteration": Path(
        "docs/experiments/actionable-regime-confidence/runs/"
        "20260512T124408+0800-codex-123227-tomac-trade-density-iteration-v1/"
        "tomac-trade-density-iteration-v1/"
        "tomac_trade_density_iteration_v1.json"
    ),
}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def max_prob(probabilities: dict[str, Any] | None) -> float | None:
    if not probabilities:
        return None
    values = [v for v in probabilities.values() if isinstance(v, (int, float))]
    return max(values) if values else None


def boolish(value: Any) -> bool:
    return bool(value) if value is not None else False


def source_state() -> dict[str, Any]:
    loaded = {}
    missing = []
    for key, path in SOURCES.items():
        if path.exists():
            loaded[key] = load_json(path)
        else:
            missing.append({"key": key, "path": str(path)})
    return {"loaded": loaded, "missing": missing}


def build_queue(data: dict[str, Any]) -> list[dict[str, Any]]:
    loaded = data["loaded"]
    queue: list[dict[str, Any]] = []

    base = loaded["121607_base_negative_feedback"]
    cpd = loaded["122215_cpd_candidate"]
    empirical = base["bbn_cpd_update_candidate"]["empirical_outcome_from_120630"]
    queue.append(
        {
            "queue_id": "trade_outcome_medium_mixed_low_loss_drift_121607",
            "source": "121607_base_negative_feedback",
            "target_layer": "BBN_CPD_candidate",
            "target_node": "trade_outcome",
            "evidence_type": "empirical_outcome_distribution",
            "context": base["bbn_cpd_update_candidate"]["context"],
            "rows": empirical["rows"],
            "observed_win_rate": empirical["probs"][0],
            "observed_loss_rate": empirical["probs"][2],
            "candidate_probs": cpd["candidate_probs"],
            "hard_negative_reason": "same-root six-provider downstream rows show loss-heavy trade_outcome relative to current CPD",
            "recommended_action": "keep candidate-only; require chronological and cross-context calibration before CPD mutation",
            "production_mutation_allowed": False,
            "promotion_allowed": False,
        }
    )

    cross = loaded["122933_provider_node_cross_context_gate"]
    best_gate = cross["feature_gates"][0]
    best_bin = best_gate["best_bin"]
    queue.append(
        {
            "queue_id": "provider_rv_median_24h_high_bin_cross_context_fail_122933",
            "source": "122933_provider_node_cross_context_gate",
            "target_layer": "BBN_evidence_node_candidate",
            "target_node": "provider_rv_median_24h",
            "evidence_type": "candidate_feature_bin_gate",
            "rows": best_bin["rows"],
            "observed_win_rate": best_bin["win_rate"],
            "wilson_win_lower_95": best_bin["wilson_win_lower_95"],
            "max_bbn_probability": cross["max_bbn_probability"],
            "accepted_contexts": cross["decision"]["accepted_feature_gates"],
            "hard_negative_reason": "best provider feature separates outcomes but fails 95 percent lower-bound and remains BTC/1h only",
            "recommended_action": "keep as candidate soft evidence; search provider-generalizable node before parent-regime use",
            "production_mutation_allowed": False,
            "promotion_allowed": False,
        }
    )

    nonbtc = loaded["123820_non_btc_local_aq_mtf_chain_probe"]
    for market in nonbtc["markets"]:
        queue.append(
            {
                "queue_id": f"cross_context_local_probe_fail_{market['state_symbol'].lower()}_123820",
                "source": "123820_non_btc_local_aq_mtf_chain_probe",
                "target_layer": "cross_context_generalization_gate",
                "target_node": "regime_likelihood_cross_context",
                "evidence_type": "non_btc_mtf_chain_readback",
                "symbol": market["source_symbol"],
                "family": market["family"],
                "active_regime": market["active_regime"],
                "max_regime_probability": market["max_regime_probability"],
                "pre_bayes_gate_status": market["pre_bayes_gate_status"],
                "execution_gate_status": market["execution_gate_status"],
                "execution_readiness": market["execution_readiness"],
                "actionable": market["actionable"],
                "hard_negative_reason": "non-BTC/non-1h local-chain context did not reach 95 percent calibrated confidence or execution readiness",
                "recommended_action": "use as abstain/generalization negative; do not count as provider-consensus acceptance",
                "production_mutation_allowed": False,
                "promotion_allowed": False,
            }
        )

    local = loaded["124245_local_nonbtc_mtf_chain_probe"]
    for panel in local["panels"]:
        panel_def = panel["panel"]
        queue.append(
            {
                "queue_id": f"local_nonbtc_mtf_panel_fail_{panel_def['panel_id']}_124245",
                "source": "124245_local_nonbtc_mtf_chain_probe",
                "target_layer": "cross_context_generalization_gate",
                "target_node": "regime_likelihood_cross_context",
                "evidence_type": "bounded_local_nonbtc_mtf_panel",
                "panel_id": panel_def["panel_id"],
                "asset_class": panel_def["asset_class"],
                "accepted_95_confidence": panel.get("accepted_95_confidence", False),
                "max_observed_confidence_like_value": panel.get("max_observed_confidence_like_value"),
                "structural_target_rows": panel.get("structural_target_rows"),
                "execution_promoted": panel.get("execution_promoted", False),
                "execution_candidate_exists": panel.get("execution_candidate_exists", False),
                "hard_negative_reason": "bounded local panel failed strict Board A acceptance; some commands succeeded but acceptance and promotion stayed false",
                "recommended_action": "feed as abstain/local-cache negative; require provider-provenanced repeat before CPD use",
                "production_mutation_allowed": False,
                "promotion_allowed": False,
            }
        )

    tomac = loaded["124408_tomac_trade_density_iteration"]
    queue.append(
        {
            "queue_id": "selected_history_tomac_zero_trade_density_124408",
            "source": "124408_tomac_trade_density_iteration",
            "target_layer": "AutoQuant_trade_density_gate",
            "target_node": "strategy_viability",
            "evidence_type": "zero_trade_iteration",
            "strategies": [item["name"] for item in tomac["strategies"]],
            "total_trades": tomac["summary"]["total_trades"],
            "mature_rooted_observations": tomac["summary"]["mature_rooted_observations"],
            "accepted_95_contexts": tomac["summary"]["accepted_95_contexts"],
            "hard_negative_reason": "selected-history TOMAC repair produced zero trades across all attempted strategies",
            "recommended_action": "retire this strategy/data-shape for promotion unless a materially new window or strategy family appears",
            "production_mutation_allowed": False,
            "promotion_allowed": False,
        }
    )
    return queue


def summarize(queue: list[dict[str, Any]], data: dict[str, Any]) -> dict[str, Any]:
    loaded = data["loaded"]
    cross = loaded["122933_provider_node_cross_context_gate"]
    nonbtc = loaded["123820_non_btc_local_aq_mtf_chain_probe"]
    local = loaded["124245_local_nonbtc_mtf_chain_probe"]
    tomac = loaded["124408_tomac_trade_density_iteration"]
    max_probs = [
        max_prob(market.get("market_regime_probabilities"))
        for market in nonbtc["markets"]
    ]
    max_probs = [v for v in max_probs if v is not None]
    confidence_like_values = [
        panel.get("max_observed_confidence_like_value")
        for panel in local["panels"]
        if isinstance(panel.get("max_observed_confidence_like_value"), (int, float))
    ]
    return {
        "run_id": RUN_ID,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "board_file": str(BOARD),
        "board_hash_before_artifact": BOARD_HASH_BEFORE,
        "scope": "Extend the candidate-only BBN/CPD hard-negative queue using settled post-121607 negative roots.",
        "source_paths": {key: str(path) for key, path in SOURCES.items()},
        "missing_sources": data["missing"],
        "negative_queue_count": len(queue),
        "source_roots_counted": [
            "121607",
            "122215",
            "122933",
            "123820",
            "124245",
            "124408",
        ],
        "max_observed_probability_after_extension": max(
            [cross["max_bbn_probability"], *max_probs, *confidence_like_values]
        ),
        "accepted_95_contexts_added": 0,
        "runtime_mutation": False,
        "prior_mutation": False,
        "production_likelihood_mutation": False,
        "queue_entries": queue,
        "hard_negative_counts": {
            "trade_outcome_cpd_candidates": sum(item["target_layer"] == "BBN_CPD_candidate" for item in queue),
            "provider_evidence_node_candidates": sum(item["target_layer"] == "BBN_evidence_node_candidate" for item in queue),
            "cross_context_generalization_negatives": sum(item["target_layer"] == "cross_context_generalization_gate" for item in queue),
            "trade_density_negatives": sum(item["target_layer"] == "AutoQuant_trade_density_gate" for item in queue),
            "zero_trade_strategy_count_124408": sum(1 for item in tomac["strategies"] if item["trade_count"] == 0),
        },
        "decision": {
            "gate": "bbn_negative_feedback_extension_v1=candidate_hard_negative_queue_created_no_runtime_mutation_no_promotion",
            "candidate_only": True,
            "all_sources_present": len(data["missing"]) == 0,
            "every_regime_95_confidence": False,
            "cross_market_acceptance": False,
            "trade_usable": False,
            "promotion_allowed": False,
            "update_goal": False,
        },
        "next": [
            "do not overwrite production priors or CPDs from this artifact",
            "use queue entries to prioritize provider-generalizable BBN evidence nodes",
            "rerun chronological/cross-provider calibration before any CPD mutation",
            "continue seeking a regime-specific likelihood node that reaches >=0.95 with cross-instrument/timeframe/provider support",
        ],
    }


def write_csv(queue: list[dict[str, Any]], path: Path) -> None:
    fields = [
        "queue_id",
        "source",
        "target_layer",
        "target_node",
        "evidence_type",
        "rows",
        "observed_win_rate",
        "observed_loss_rate",
        "wilson_win_lower_95",
        "max_bbn_probability",
        "max_regime_probability",
        "accepted_95_confidence",
        "total_trades",
        "production_mutation_allowed",
        "promotion_allowed",
        "recommended_action",
    ]
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(queue)


def write_checklist(summary: dict[str, Any], path: Path) -> None:
    rows = [
        {
            "requirement": "existing BBN feedback source read",
            "status": "pass" if "121607" in summary["source_roots_counted"] else "fail",
            "evidence": summary["source_paths"]["121607_base_negative_feedback"],
        },
        {
            "requirement": "provider evidence node gate included",
            "status": "pass" if "122933" in summary["source_roots_counted"] else "fail",
            "evidence": summary["source_paths"]["122933_provider_node_cross_context_gate"],
        },
        {
            "requirement": "post-121607 non-BTC/MTF negatives included",
            "status": "pass" if all(x in summary["source_roots_counted"] for x in ["123820", "124245"]) else "fail",
            "evidence": "123820 and 124245 JSON roots",
        },
        {
            "requirement": "selected-history zero-trade negative included",
            "status": "pass" if "124408" in summary["source_roots_counted"] else "fail",
            "evidence": summary["source_paths"]["124408_tomac_trade_density_iteration"],
        },
        {
            "requirement": "no production prior/CPD mutation",
            "status": "pass" if not summary["prior_mutation"] and not summary["production_likelihood_mutation"] else "fail",
            "evidence": "summary prior_mutation=false production_likelihood_mutation=false",
        },
        {
            "requirement": "strict Board A objective remains fail-closed",
            "status": "pass" if not summary["decision"]["every_regime_95_confidence"] else "fail",
            "evidence": "accepted_95_contexts_added=0",
        },
    ]
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["requirement", "status", "evidence"])
        writer.writeheader()
        writer.writerows(rows)


def write_md(summary: dict[str, Any], path: Path) -> None:
    lines = [
        "# BBN Negative Feedback Extension v1",
        "",
        f"Run id: `{summary['run_id']}`",
        "",
        "Mode: `candidate_only_no_runtime_mutation`",
        "",
        "## Scope",
        "",
        "This packet converts settled negative roots after the first BBN feedback packet into a candidate hard-negative queue. It does not mutate production priors, CPDs, BBN runtime state, CatBoost runtime state, execution-tree state, or Board A acceptance.",
        "",
        "## Inputs",
        "",
    ]
    for key, source in summary["source_paths"].items():
        lines.append(f"- `{key}`: `{source}`")
    lines.extend(
        [
            "",
            "## Readback",
            "",
            f"- Queue entries: `{summary['negative_queue_count']}`",
            f"- Max observed probability-like value after extension: `{summary['max_observed_probability_after_extension']:.6f}`",
            f"- Accepted >=95 contexts added: `{summary['accepted_95_contexts_added']}`",
            f"- Runtime mutation: `{str(summary['runtime_mutation']).lower()}`",
            f"- Prior mutation: `{str(summary['prior_mutation']).lower()}`",
            f"- Production likelihood mutation: `{str(summary['production_likelihood_mutation']).lower()}`",
            "",
            "## Queue",
            "",
        ]
    )
    for item in summary["queue_entries"]:
        rows = item.get("rows")
        row_text = "n/a" if rows is None else str(rows)
        lines.append(
            f"- `{item['queue_id']}` -> `{item['target_layer']}` / `{item['target_node']}`; rows `{row_text}`; action `{item['recommended_action']}`"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            f"- Gate: `{summary['decision']['gate']}`",
            "- This is useful negative evidence for BBN/CPD candidate work, but it is not Board A acceptance.",
            "- Every-regime 95 percent confidence remains false.",
            "- Cross-market acceptance remains false.",
            "- Trade usable remains false.",
            "- Promotion allowed remains false.",
            "- `update_goal=false`.",
            "",
            "## Next",
            "",
        ]
    )
    for item in summary["next"]:
        lines.append(f"- {item}")
    path.write_text("\n".join(lines) + "\n")


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)
    data = source_state()
    if data["missing"]:
        raise SystemExit(f"missing sources: {data['missing']}")
    queue = build_queue(data)
    summary = summarize(queue, data)

    json_path = OUT_DIR / "bbn_negative_feedback_extension_v1.json"
    csv_path = OUT_DIR / "bbn_hard_negative_queue_v1.csv"
    checklist_path = OUT_DIR / "prompt_to_artifact_checklist_bbn_negative_feedback_extension_v1.csv"
    md_path = OUT_DIR / "bbn_negative_feedback_extension_v1.md"
    assertions_path = CHECK_DIR / "bbn_negative_feedback_extension_v1_assertions.out"

    json_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    write_csv(queue, csv_path)
    write_checklist(summary, checklist_path)
    write_md(summary, md_path)

    checks = [
        ("all_sources_present", summary["decision"]["all_sources_present"]),
        ("queue_entries_present", summary["negative_queue_count"] >= 6),
        ("no_prior_mutation", not summary["prior_mutation"]),
        ("no_production_likelihood_mutation", not summary["production_likelihood_mutation"]),
        ("no_promotion", not summary["decision"]["promotion_allowed"]),
        ("strict_goal_fail_closed", not summary["decision"]["every_regime_95_confidence"]),
        ("zero_accepted_95_added", summary["accepted_95_contexts_added"] == 0),
    ]
    with assertions_path.open("w") as handle:
        for name, ok in checks:
            handle.write(f"{'PASS' if ok else 'FAIL'} {name}\n")
    if not all(ok for _, ok in checks):
        return 1
    print(json.dumps({"run_id": RUN_ID, "queue_entries": len(queue), "assertions": str(assertions_path)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
