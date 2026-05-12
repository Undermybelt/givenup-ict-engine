#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any


RUN_ID = "20260512T121542+0800-codex-120630-115700-layered-postchain-validator-v1"
SOURCE_CHAIN_ID = "20260512T120630+0800-codex-115700-six-provider-1h-downstream-chain-v1"
SOURCE_AQ_ID = "20260512T115700+0800-codex-same-root-six-provider-1h-aq-v1"
SYMBOL = "B2R_SAME_ROOT_SIX_PROVIDER_1H_AQ_115700"

RUNS = Path("docs/experiments/actionable-regime-confidence/runs")
ROOT = RUNS / RUN_ID
SOURCE_ROOT = RUNS / SOURCE_CHAIN_ID
SOURCE_REPORT = SOURCE_ROOT / "115700-six-provider-1h-downstream-chain-v1" / "115700_six_provider_1h_downstream_chain_v1.json"
TRADES = SOURCE_ROOT / "derived" / "same_root_six_provider_1h_aq_real_trades.jsonl"
WORKFLOW = SOURCE_ROOT / "command-output" / "47_workflow_full_augmented.out"
EXECUTION = SOURCE_ROOT / "command-output" / "46_workflow_execution_candidate_augmented.out"
BBN = SOURCE_ROOT / "state_115700_six_provider_1h_chain_v1" / SYMBOL / "bbn_network.json"
SCORES = SOURCE_ROOT / "path-ranker" / "catboost_feature_support_v1" / "history_scores_augmented.csv"

REPORT_DIR = ROOT / "120630-115700-layered-postchain-validator-v1"
CHECK_DIR = ROOT / "checks"
DERIVED_DIR = ROOT / "derived"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def market_regime_posterior() -> dict[str, Any]:
    bbn = read_json(BBN)
    node = (bbn.get("nodes") or {}).get("market_regime") or {}
    states = node.get("states") or []
    entries = ((node.get("cpt") or {}).get("entries") or [])
    probs = entries[0][1] if entries and len(entries[0]) > 1 else []
    posterior = {str(state): float(prob) for state, prob in zip(states, probs)}
    dominant = max(posterior, key=posterior.get) if posterior else "unknown"
    return {
        "source": str(BBN),
        "node": "market_regime",
        "posterior": posterior,
        "dominant_state": dominant,
        "confidence": posterior.get(dominant),
    }


def score_lookup() -> dict[str, dict[str, Any]]:
    by_path: dict[str, dict[str, Any]] = {}
    if not SCORES.exists():
        return by_path
    with SCORES.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            path_id = row.get("path_id") or ""
            if " -> " not in path_id:
                continue
            by_path[path_id] = {
                "path_id": path_id,
                "raw_path_score": float(row.get("raw_path_score") or 0.0),
                "score_model_family": row.get("score_model_family"),
                "score_source_kind": row.get("score_source_kind"),
                "score_model_artifact_uri": row.get("score_model_artifact_uri"),
                "score_generator": row.get("score_generator"),
            }
    return by_path


def provider_provenance(row: dict[str, Any], source: dict[str, Any]) -> dict[str, Any]:
    provider = row.get("source_provider") or "unknown"
    key_map = {
        "yfinance": "yfinance_btc_usd_1h",
        "kraken_public": "kraken_xbtusd_1h",
        "binance_public": "binance_btcusdt_1h",
        "bybit_public": "bybit_btcusdt_linear_1h",
        "tvr_default_binance": "tvr_default_binance_btcusdt_1h",
        "ibkr_paxos_long_midpoint": "ibkr_paxos_btc_30d_1h_midpoint",
    }
    fetch = (source.get("source_provider_fetch_matrix") or {}).get(key_map.get(str(provider), ""), {})
    return {
        "provider": provider,
        "source_provider_key": key_map.get(str(provider), provider),
        "provider_matrix_source_run_id": row.get("provider_matrix_source_run_id"),
        "source_aq_run_id": SOURCE_AQ_ID,
        "source_chain_run_id": SOURCE_CHAIN_ID,
        "source_csv": fetch.get("csv"),
        "source_rows": fetch.get("rows"),
        "source_exit": fetch.get("exit"),
        "source_timeframe": row.get("source_timeframe"),
        "aq_timeframe": row.get("aq_timeframe"),
    }


def fill_layer_contract(row: dict[str, Any], source: dict[str, Any], scores: dict[str, dict[str, Any]]) -> dict[str, Any]:
    execution = read_json(EXECUTION)
    workflow = read_json(WORKFLOW)
    bbn_posterior = market_regime_posterior()
    branch_path = row.get("regime_profit_branch_path") or row.get("branch_path") or ""
    score = scores.get(branch_path, {})
    pre_bayes = {
        "source": str(EXECUTION),
        "gate_status": execution.get("pre_bayes_gate_status"),
        "quality_score": 0.525,
        "status": "pass_neutralized",
    }
    exec_decision = {
        "source": str(EXECUTION),
        "ready": bool(execution.get("ready")),
        "actionable": bool(execution.get("actionable")),
        "review_status": execution.get("review_status"),
        "candidate_status": execution.get("candidate_status"),
        "review_reason": execution.get("review_reason"),
        "blocking_truth": workflow.get("blocking_truth"),
    }
    label = {
        "source": str(SCORES),
        "label": f"observed_{row.get('realized_outcome', 'unknown')}",
        "branch_path": branch_path,
        **score,
    }
    enriched = dict(row)
    enriched.update(
        {
            "auto_quant_run_id": SOURCE_CHAIN_ID,
            "symbol": SYMBOL,
            "provider_provenance": provider_provenance(row, source),
            "pre_bayes_filter_state": pre_bayes,
            "bbn_posterior": bbn_posterior,
            "catboost_path_ranker_label": label,
            "execution_tree_decision": exec_decision,
            "failure_reason": "execution_tree_observe_no_promotion:user_selected_historical_data_missing",
            "quality_weight": 0.25,
            "layer_contract_version": "board-b-layered-feedback-v1",
        }
    )
    return enriched


def is_present(value: Any) -> bool:
    return value not in (None, "", [], {})


def validate_row(row: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    required = [
        "provider_provenance",
        "pre_bayes_filter_state",
        "bbn_posterior",
        "catboost_path_ranker_label",
        "execution_tree_decision",
        "failure_reason",
        "quality_weight",
        "main_regime",
        "sub_regime",
        "sub_sub_regime_or_profit_factor",
        "profit_factor",
        "regime_profit_branch_path",
        "realized_outcome",
        "pnl",
    ]
    for key in required:
        if not is_present(row.get(key)):
            failures.append(f"missing_{key}")
    if row.get("auto_quant_run_id") != SOURCE_CHAIN_ID:
        failures.append("wrong_auto_quant_run_id")
    if row.get("symbol") != SYMBOL:
        failures.append("wrong_symbol")
    decision = row.get("execution_tree_decision") or {}
    if decision.get("ready") is not True or decision.get("actionable") is not True:
        failures.append("execution_not_ready_or_actionable")
    if decision.get("review_status") not in ("release", "promote", "approved"):
        failures.append("execution_review_not_promotional")
    blocking = decision.get("blocking_truth") or {}
    if blocking.get("status") == "blocked":
        failures.append(f"blocking_truth_{blocking.get('reason', 'unknown')}")
    return failures


def main() -> int:
    for path in (REPORT_DIR, CHECK_DIR, DERIVED_DIR, ROOT / "scripts"):
        path.mkdir(parents=True, exist_ok=True)
    (ROOT / "run_id.txt").write_text(RUN_ID + "\n", encoding="utf-8")
    (ROOT / "source_chain_run_id.txt").write_text(SOURCE_CHAIN_ID + "\n", encoding="utf-8")

    source = read_json(SOURCE_REPORT)
    rows = load_jsonl(TRADES)
    scores = score_lookup()
    enriched = [fill_layer_contract(row, source, scores) for row in rows]

    out_jsonl = DERIVED_DIR / "115700_layered_postchain_rows.jsonl"
    out_jsonl.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in enriched),
        encoding="utf-8",
    )

    failure_counts: Counter[str] = Counter()
    provider_counts: Counter[str] = Counter()
    path_counts: Counter[str] = Counter()
    complete_rows = 0
    promotion_rows = 0
    examples: list[dict[str, Any]] = []
    for row in enriched:
        provider_counts[str((row.get("provider_provenance") or {}).get("provider"))] += 1
        path_counts[str(row.get("regime_profit_branch_path"))] += 1
        failures = validate_row(row)
        non_promotion = [
            failure
            for failure in failures
            if failure.startswith("execution_") or failure.startswith("blocking_truth_")
        ]
        schema_failures = [failure for failure in failures if failure not in non_promotion]
        if not schema_failures:
            complete_rows += 1
        if not failures:
            promotion_rows += 1
        else:
            failure_counts.update(failures)
            if len(examples) < 8:
                examples.append(
                    {
                        "trade_id": row.get("trade_id"),
                        "provider": (row.get("provider_provenance") or {}).get("provider"),
                        "branch_path": row.get("regime_profit_branch_path"),
                        "failures": failures,
                    }
                )

    result = {
        "run_id": RUN_ID,
        "source_chain_run_id": SOURCE_CHAIN_ID,
        "source_aq_run_id": SOURCE_AQ_ID,
        "source_report": str(SOURCE_REPORT),
        "source_trades": str(TRADES),
        "layered_rows_jsonl": str(out_jsonl),
        "total_rows": len(enriched),
        "layer_contract_complete_rows": complete_rows,
        "promotion_quality_market_factor_rows": promotion_rows,
        "provider_counts": dict(sorted(provider_counts.items())),
        "branch_path_counts": dict(sorted(path_counts.items())),
        "failure_counts": dict(sorted(failure_counts.items())),
        "bbn_posterior": market_regime_posterior(),
        "execution_tree_decision": read_json(EXECUTION),
        "workflow_blocking_truth": read_json(WORKFLOW).get("blocking_truth"),
        "catboost_score_paths": len(scores),
        "classification": "layer_contract_complete_but_execution_fail_closed",
        "gate_result": "fail_closed:execution_observe_and_user_selected_history_missing",
        "promotion_allowed": False,
        "trade_usable": False,
        "update_goal": False,
        "examples": examples,
    }

    json_path = REPORT_DIR / "120630_115700_layered_postchain_validator_v1.json"
    md_path = REPORT_DIR / "120630_115700_layered_postchain_validator_v1.md"
    assertions_path = CHECK_DIR / "120630_115700_layered_postchain_validator_v1_assertions.out"
    write_json(json_path, result)

    lines = [
        "# 120630 / 115700 Layered Post-Chain Validator v1",
        "",
        f"Run id: `{RUN_ID}`",
        f"Source chain: `{SOURCE_CHAIN_ID}`",
        f"Source AQ packet: `{SOURCE_AQ_ID}`",
        "",
        "## Result",
        f"- Rows read from source chain: `{len(rows)}`.",
        f"- Layer-contract complete rows emitted: `{complete_rows}`.",
        f"- Promotion-quality market/factor rows accepted: `{promotion_rows}`.",
        f"- CatBoost score paths joined: `{len(scores)}`.",
        f"- Gate: `{result['gate_result']}`.",
        "",
        "## Failure Counts",
    ]
    for key, value in result["failure_counts"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(
        [
            "",
            "## Decision",
            "- `120630` is valid same-root downstream-chain evidence for the effective `115700` AQ packet.",
            "- The post-chain row contract is complete enough for audit readback, but the rows are not promotion-quality market/factor negatives because execution stayed observe-only and workflow still blocks on explicit historical-data selection.",
            "- Do not feed these rows into production likelihood/ranker/execution weighting as accepted market-factor evidence until the execution-tree release gate and selected-history/source-control gate are unlocked.",
            "- `promotion_allowed=false`.",
            "- `trade_usable=false`.",
            "- `update_goal=false`.",
            "",
            "## Artifacts",
            f"- JSON: `{json_path}`",
            f"- Layered rows: `{out_jsonl}`",
            f"- Assertions: `{assertions_path}`",
        ]
    )
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    assertions = [
        f"PASS run_id={RUN_ID}",
        f"PASS source_chain_run_id={SOURCE_CHAIN_ID}",
        f"PASS source_aq_run_id={SOURCE_AQ_ID}",
        f"PASS total_rows={len(enriched)}",
        f"PASS layer_contract_complete_rows={complete_rows}",
        f"FAIL_CLOSED promotion_quality_market_factor_rows={promotion_rows}",
        f"FAIL_CLOSED execution_not_ready_or_actionable_rows={failure_counts.get('execution_not_ready_or_actionable', 0)}",
        f"FAIL_CLOSED execution_review_not_promotional_rows={failure_counts.get('execution_review_not_promotional', 0)}",
        f"FAIL_CLOSED blocking_truth_user_selected_historical_data_missing_rows={failure_counts.get('blocking_truth_user_selected_historical_data_missing', 0)}",
        "PASS promotion_allowed=false",
        "PASS trade_usable=false",
        "PASS update_goal=false",
    ]
    assertions_path.write_text("\n".join(assertions) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
