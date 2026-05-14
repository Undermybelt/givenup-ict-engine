from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


RUN_ID = "20260512T121607+0800-codex-120630-bbn-negative-feedback-packet-v1"
SOURCE_RUN_ID = "20260512T120630+0800-codex-115700-six-provider-1h-downstream-chain-v1"
SOURCE_AQ_RUN_ID = "20260512T115700+0800-codex-same-root-six-provider-1h-aq-v1"
SYMBOL = "B2R_SAME_ROOT_SIX_PROVIDER_1H_AQ_115700"

RUNS = Path("docs/experiments/actionable-regime-confidence/runs")
ROOT = RUNS / RUN_ID
SOURCE_ROOT = RUNS / SOURCE_RUN_ID
REPORT_DIR = ROOT / "120630-bbn-negative-feedback-packet-v1"
CHECK_DIR = ROOT / "checks"
TRADES_PATH = SOURCE_ROOT / "derived" / "same_root_six_provider_1h_aq_real_trades.jsonl"
SOURCE_SUMMARY_PATH = SOURCE_ROOT / "115700-six-provider-1h-downstream-chain-v1" / "115700_six_provider_1h_downstream_chain_v1.json"
STATE_SYMBOL_DIR = SOURCE_ROOT / "state_115700_six_provider_1h_chain_v1" / SYMBOL
BBN_PATH = STATE_SYMBOL_DIR / "bbn_network.json"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text()) if path.exists() else {}


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def pct(value: float) -> float:
    return round(value, 6)


def load_trades() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in TRADES_PATH.read_text().splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def summarize_group(rows: list[dict[str, Any]]) -> dict[str, Any]:
    total = len(rows)
    outcomes = Counter(str(row.get("realized_outcome", "unknown")) for row in rows)
    pnl_values = [float(row.get("pnl") or 0.0) for row in rows]
    wins = outcomes.get("win", 0)
    losses = outcomes.get("loss", 0)
    breakeven = outcomes.get("breakeven", 0)
    return {
        "rows": total,
        "wins": wins,
        "losses": losses,
        "breakeven": breakeven,
        "win_rate": pct(wins / total) if total else 0.0,
        "loss_rate": pct(losses / total) if total else 0.0,
        "total_pnl": pct(sum(pnl_values)),
        "avg_pnl": pct(sum(pnl_values) / total) if total else 0.0,
    }


def grouped(rows: list[dict[str, Any]], key: str) -> dict[str, Any]:
    buckets: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        buckets[str(row.get(key, "unknown"))].append(row)
    return {name: summarize_group(bucket) for name, bucket in sorted(buckets.items())}


def grouped_pair(rows: list[dict[str, Any]], left: str, right: str) -> dict[str, Any]:
    buckets: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        name = f"{row.get(left, 'unknown')} | {row.get(right, 'unknown')}"
        buckets[name].append(row)
    return {name: summarize_group(bucket) for name, bucket in sorted(buckets.items())}


def cpd_for_trade_outcome(bbn: dict[str, Any], parent_state_names: list[str]) -> dict[str, Any]:
    node = bbn.get("nodes", {}).get("trade_outcome", {})
    parents = node.get("parents", [])
    states = node.get("states", [])
    parent_indexes: list[int] = []
    for parent, state in zip(parents, parent_state_names):
        parent_states = bbn.get("nodes", {}).get(parent, {}).get("states", [])
        parent_indexes.append(parent_states.index(state) if state in parent_states else -1)
    current = None
    for indexes, probs in node.get("cpt", {}).get("entries", []):
        if indexes == parent_indexes:
            current = probs
            break
    return {
        "parents": parents,
        "parent_state_names": parent_state_names,
        "parent_indexes": parent_indexes,
        "states": states,
        "current_probs": current,
    }


def main() -> int:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)
    (ROOT / "run_id.txt").write_text(RUN_ID + "\n")
    (ROOT / "source_run_id.txt").write_text(SOURCE_RUN_ID + "\n")

    trades = load_trades()
    source = read_json(SOURCE_SUMMARY_PATH)
    bbn = read_json(BBN_PATH)
    pre_bayes = source.get("pre_bayes", {})
    augmented_ranker = source.get("augmented_ranker_target", {})
    execution = source.get("augmented_execution_candidate", {})

    overall = summarize_group(trades)
    by_provider = grouped(trades, "source_provider")
    by_branch = grouped(trades, "regime_profit_branch_path")
    by_provider_branch = grouped_pair(trades, "source_provider", "regime_profit_branch_path")
    by_regime_at_entry = grouped(trades, "regime_at_entry")
    by_strategy = grouped(trades, "strategy_name")
    provider_reliability = {
        provider: {
            "rows": stats["rows"],
            "win_rate": stats["win_rate"],
            "loss_rate": stats["loss_rate"],
            "suggested_reliability_weight": pct(max(0.0, min(1.0, stats["win_rate"]))),
            "negative_sample_weight": pct(stats["loss_rate"]),
        }
        for provider, stats in by_provider.items()
    }

    empirical_outcome = {
        "states": ["win", "breakeven", "loss"],
        "probs": [
            overall["win_rate"],
            pct(overall["breakeven"] / overall["rows"]) if overall["rows"] else 0.0,
            overall["loss_rate"],
        ],
        "rows": overall["rows"],
    }
    cpd_context = cpd_for_trade_outcome(bbn, ["medium", "mixed", "low"])
    cpd_candidate = {
        "target_node": "trade_outcome",
        "context": "entry_quality=medium,factor_alignment=mixed,factor_uncertainty=low",
        "current_cpd": cpd_context,
        "empirical_outcome_from_120630": empirical_outcome,
        "recommended_update_mode": "candidate_only_chronological_smoothing_required",
        "safety_note": "Do not directly overwrite priors. Treat this as likelihood/CPD evidence gated by chronological and cross-context validation.",
    }

    feedback = {
        "run_id": RUN_ID,
        "source_run_id": SOURCE_RUN_ID,
        "source_aq_run_id": SOURCE_AQ_RUN_ID,
        "symbol": SYMBOL,
        "input_artifacts": {
            "trades": str(TRADES_PATH),
            "source_summary": str(SOURCE_SUMMARY_PATH),
            "bbn_network": str(BBN_PATH),
        },
        "overall": overall,
        "by_provider": by_provider,
        "by_branch": by_branch,
        "by_provider_branch": by_provider_branch,
        "by_regime_at_entry": by_regime_at_entry,
        "by_strategy": by_strategy,
        "provider_reliability_candidates": provider_reliability,
        "pre_bayes_bbn_readback": {
            "latest_gate_status": pre_bayes.get("latest_gate_status"),
            "latest_canonical_structural_active_regime": pre_bayes.get("latest_canonical_structural_active_regime"),
            "latest_canonical_structural_confidence": pre_bayes.get("latest_canonical_structural_confidence"),
            "latest_canonical_structural_probabilities": pre_bayes.get("latest_canonical_structural_probabilities"),
            "latest_filtered_assignments": pre_bayes.get("latest_filtered_assignments"),
            "latest_soft_evidence": pre_bayes.get("latest_soft_evidence"),
            "latest_uses_soft_evidence": pre_bayes.get("latest_uses_soft_evidence"),
        },
        "catboost_path_ranker_readback": {
            "raw_scored_mature_rows": augmented_ranker.get("raw_scored_mature_rows"),
            "raw_scored_mature_min_rows": augmented_ranker.get("raw_scored_mature_min_rows"),
            "production_validation_rows": augmented_ranker.get("production_validation_rows"),
            "production_validation_min_rows": augmented_ranker.get("production_validation_min_rows"),
            "observation_validation_rows": augmented_ranker.get("observation_validation_rows"),
            "runtime_selection_status": augmented_ranker.get("runtime_selection_status"),
            "runtime_selection_ready": augmented_ranker.get("runtime_selection_ready"),
            "score_model_family": augmented_ranker.get("score_model_family"),
            "score_source_kind": augmented_ranker.get("score_source_kind"),
        },
        "execution_tree_readback": {
            "ready": execution.get("ready"),
            "actionable": execution.get("actionable"),
            "review_status": execution.get("review_status"),
            "execution_gate_status": execution.get("execution_gate_status"),
            "execution_readiness": execution.get("execution_readiness"),
            "pre_bayes_gate_status": execution.get("pre_bayes_gate_status"),
            "path_id": execution.get("path_id"),
            "selected_path_probability": execution.get("selected_path_probability"),
        },
        "bbn_cpd_update_candidate": cpd_candidate,
        "negative_feedback_targets": [
            "BBN trade_outcome likelihood under medium/mixed/low context",
            "provider reliability weights",
            "CatBoost/path-ranker hard negatives by exact branch path",
            "execution-tree observe/block reason weights",
            "Pre-Bayes pass_neutralized calibration policy",
        ],
        "promotion_allowed": False,
        "trade_usable": False,
        "update_goal": False,
    }

    write_json(REPORT_DIR / "120630_bbn_negative_feedback_packet_v1.json", feedback)

    rows_csv = REPORT_DIR / "120630_bbn_negative_feedback_by_provider_branch_v1.csv"
    with rows_csv.open("w", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["provider_branch", "rows", "wins", "losses", "win_rate", "loss_rate", "total_pnl", "avg_pnl"])
        for name, stats in feedback["by_provider_branch"].items():
            writer.writerow([name, stats["rows"], stats["wins"], stats["losses"], stats["win_rate"], stats["loss_rate"], stats["total_pnl"], stats["avg_pnl"]])

    checklist = REPORT_DIR / "prompt_to_artifact_checklist_120630_bbn_negative_feedback_packet_v1.csv"
    with checklist.open("w", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["requirement", "artifact", "status", "note"])
        writer.writerow(["negative 120630 rows", str(TRADES_PATH), "covered", f"rows={overall['rows']}"])
        writer.writerow(["BBN/Pre-Bayes evidence", str(SOURCE_SUMMARY_PATH), "covered", str(pre_bayes.get("latest_gate_status"))])
        writer.writerow(["CatBoost/path-ranker hard negatives", str(SOURCE_SUMMARY_PATH), "covered", str(augmented_ranker.get("raw_scored_mature_rows"))])
        writer.writerow(["execution-tree block reason", str(SOURCE_SUMMARY_PATH), "covered", str(execution.get("review_status"))])
        writer.writerow(["CPD update candidate", str(REPORT_DIR / "120630_bbn_negative_feedback_packet_v1.json"), "covered", "candidate_only"])

    md = REPORT_DIR / "120630_bbn_negative_feedback_packet_v1.md"
    md.write_text(
        "\n".join(
            [
                "# 120630 BBN Negative Feedback Packet v1",
                "",
                f"Run id: `{RUN_ID}`",
                f"Source downstream run: `{SOURCE_RUN_ID}`",
                f"Source AQ root: `{SOURCE_AQ_RUN_ID}`",
                "",
                "## Result",
                f"- Rows: `{overall['rows']}`; wins `{overall['wins']}`; losses `{overall['losses']}`; win rate `{overall['win_rate']}`; loss rate `{overall['loss_rate']}`.",
                f"- Branches: `{by_branch}`.",
                f"- Provider reliability candidates: `{provider_reliability}`.",
                f"- Pre-Bayes gate: `{pre_bayes.get('latest_gate_status')}`; active structural regime `{pre_bayes.get('latest_canonical_structural_active_regime')}` confidence `{pre_bayes.get('latest_canonical_structural_confidence')}`.",
                f"- CatBoost/path-ranker: raw scored mature `{augmented_ranker.get('raw_scored_mature_rows')}/{augmented_ranker.get('raw_scored_mature_min_rows')}`, production validation `{augmented_ranker.get('production_validation_rows')}/{augmented_ranker.get('production_validation_min_rows')}`, runtime `{augmented_ranker.get('runtime_selection_status')}`.",
                f"- Execution tree: ready `{execution.get('ready')}`, actionable `{execution.get('actionable')}`, review `{execution.get('review_status')}`, readiness `{execution.get('execution_readiness')}`.",
                "",
                "## BBN Feedback Candidate",
                "- This packet is candidate evidence for likelihood/CPD calibration, not direct prior overwrite.",
                f"- Context: `{cpd_candidate['context']}`.",
                f"- Current CPD: `{cpd_candidate['current_cpd']}`.",
                f"- Empirical outcome: `{cpd_candidate['empirical_outcome_from_120630']}`.",
                "",
                "## Decision",
                "- Gate: `120630_bbn_negative_feedback_packet_v1=candidate_likelihood_feedback_only_no_promotion`.",
                "- Feed this into chronological/cross-context BBN calibration and CatBoost hard-negative queues.",
                "- `promotion_allowed=false`.",
                "- `trade_usable=false`.",
                "- `update_goal=false`.",
                "",
                "## Artifacts",
                f"- JSON: `{REPORT_DIR / '120630_bbn_negative_feedback_packet_v1.json'}`",
                f"- Provider/branch CSV: `{rows_csv}`",
                f"- Checklist: `{checklist}`",
            ]
        )
        + "\n"
    )

    assertions = CHECK_DIR / "120630_bbn_negative_feedback_packet_v1_assertions.out"
    assertion_lines = [
        f"PASS run_id={RUN_ID}",
        f"PASS source_run_id={SOURCE_RUN_ID}",
        f"PASS rows={overall['rows']}",
        f"PASS wins={overall['wins']}",
        f"PASS losses={overall['losses']}",
        f"PASS win_rate={overall['win_rate']}",
        f"PASS loss_rate={overall['loss_rate']}",
        f"PASS pre_bayes_gate={pre_bayes.get('latest_gate_status')}",
        f"PASS raw_scored_mature={augmented_ranker.get('raw_scored_mature_rows')}",
        f"PASS production_validation={augmented_ranker.get('production_validation_rows')}",
        f"FAIL_CLOSED execution_ready={execution.get('ready')} actionable={execution.get('actionable')} review={execution.get('review_status')}",
        "PASS cpd_update_candidate_only=true",
        "PASS promotion_allowed=false",
        "PASS trade_usable=false",
        "PASS update_goal=false",
    ]
    assertions.write_text("\n".join(assertion_lines) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
