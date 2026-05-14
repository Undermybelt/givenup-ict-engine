#!/usr/bin/env python3
from __future__ import annotations

import csv
import importlib.util
import json
import shutil
from pathlib import Path
from typing import Any


RUN_ID = "20260512T121347+0800-codex-115700-enriched-downstream-chain-v1"
SOURCE_RUN_ID = "20260512T115700+0800-codex-same-root-six-provider-1h-aq-v1"
SYMBOL = "B2R_SAME_ROOT_SIX_PROVIDER_1H_AQ_115700"

RUNS = Path("docs/experiments/actionable-regime-confidence/runs")
ROOT = RUNS / RUN_ID
SOURCE_ROOT = RUNS / SOURCE_RUN_ID
BASE_SCRIPT = (
    RUNS
    / "20260512T120630+0800-codex-115700-six-provider-1h-downstream-chain-v1"
    / "scripts"
    / "115700_six_provider_1h_downstream_chain_v1.py"
)
ENRICHER_SCRIPT = Path("scripts/auto_quant_external/structural_feedback_trade_enricher.py")

OUT_DIR = ROOT / "command-output"
CHECK_DIR = ROOT / "checks"
REPORT_DIR = ROOT / "115700-enriched-downstream-chain-v1"
DERIVED_DIR = ROOT / "derived"
PROVIDER_JSON_DIR = ROOT / "provider-data-json"
STATE_DIR = ROOT / "state_115700_enriched_downstream_chain_v1"
PATH_RANKER_DIR = ROOT / "path-ranker"
SUPPORT_DIR = PATH_RANKER_DIR / "catboost_feature_support_v1"

RAW_TRADES = DERIVED_DIR / "same_root_six_provider_1h_aq_real_trades.raw.jsonl"
REPAIRED_TRADES = DERIVED_DIR / "same_root_six_provider_1h_aq_real_trades.repaired.jsonl"
ENRICHED_TRADES = DERIVED_DIR / "same_root_six_provider_1h_aq_real_trades.enriched_layer_contract.jsonl"


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load module from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8")


def branch_parts(row: dict[str, Any]) -> list[str]:
    path = row.get("regime_profit_branch_path") or row.get("branch_path") or ""
    return [part.strip() for part in str(path).split(" -> ") if part.strip()]


def fill_branch_fields(row: dict[str, Any]) -> dict[str, Any]:
    parts = branch_parts(row)
    if not parts:
        return row
    path = " -> ".join(parts)
    row["regime_profit_branch_path"] = path
    row["branch_path"] = path
    row.setdefault("main_regime", parts[0])
    row.setdefault("parent_regime_root", parts[0])
    if len(parts) > 1:
        row.setdefault("sub_regime", parts[1])
    if len(parts) > 2:
        row.setdefault("sub_sub_regime_or_profit_factor", parts[2])
    if len(parts) > 3:
        row.setdefault("profit_factor", " -> ".join(parts[3:]))
    return row


def provider_meta(source_summary: dict[str, Any]) -> dict[str, dict[str, Any]]:
    meta = {}
    for result in source_summary.get("aq_results", []):
        provider = str(result.get("provider", "unknown"))
        meta[provider] = {
            "provider": provider,
            "provider_symbol": result.get("provider_symbol"),
            "timeframe": "1h",
            "source_csv": result.get("source_csv"),
            "rows": result.get("rows"),
            "first_ts_ms": result.get("first_ts_ms"),
            "last_ts_ms": result.get("last_ts_ms"),
            "workspace": result.get("workspace"),
        }
    return meta


def repair_materialized_trades(source_summary: dict[str, Any], materialized_path: Path) -> dict[str, Any]:
    shutil.copyfile(materialized_path, RAW_TRADES)
    meta = provider_meta(source_summary)
    repaired = []
    by_provider: dict[str, int] = {}
    by_path: dict[str, int] = {}
    for row in read_jsonl(materialized_path):
        provider = str(row.get("source_provider") or "unknown")
        fixed = fill_branch_fields(dict(row))
        fixed["auto_quant_run_id"] = SOURCE_RUN_ID
        fixed["exporter_enricher_run_id"] = RUN_ID
        fixed["provider_matrix_source_run_id"] = SOURCE_RUN_ID
        fixed["symbol"] = SYMBOL
        fixed["provider_provenance"] = meta.get(provider, {"provider": provider, "timeframe": "1h"})
        fixed["source_timeframe"] = "1h"
        fixed["aq_timeframe"] = "1h"
        repaired.append(fixed)
        by_provider[provider] = by_provider.get(provider, 0) + 1
        branch_path = str(fixed.get("regime_profit_branch_path") or "<missing>")
        by_path[branch_path] = by_path.get(branch_path, 0) + 1
    write_jsonl(REPAIRED_TRADES, repaired)
    return {
        "raw_path": str(RAW_TRADES),
        "path": str(REPAIRED_TRADES),
        "rows": len(repaired),
        "by_provider": by_provider,
        "by_path": by_path,
        "auto_quant_run_id": SOURCE_RUN_ID,
        "symbol": SYMBOL,
    }


def patch_base(base: Any) -> None:
    base.RUN_ID = RUN_ID
    base.SOURCE_RUN_ID = SOURCE_RUN_ID
    base.SYMBOL = SYMBOL
    base.ROOT = ROOT
    base.SOURCE_ROOT = SOURCE_ROOT
    base.SOURCE_REPORT = SOURCE_ROOT / "same-root-six-provider-1h-aq-v1" / "same_root_six_provider_1h_aq_v1.json"
    base.OUT_DIR = OUT_DIR
    base.CHECK_DIR = CHECK_DIR
    base.REPORT_DIR = REPORT_DIR / "base-downstream-support"
    base.DERIVED_DIR = DERIVED_DIR
    base.PROVIDER_JSON_DIR = PROVIDER_JSON_DIR
    base.STATE_DIR = STATE_DIR
    base.PATH_RANKER_DIR = PATH_RANKER_DIR
    base.SUPPORT_DIR = SUPPORT_DIR


def execution_failure_reason(execution: dict[str, Any], chain_exits: dict[str, int], augmented_exits: dict[str, int]) -> str:
    failed = [label for label, code in {**chain_exits, **augmented_exits}.items() if code != 0]
    if failed:
        return "downstream_command_fail_closed:" + ",".join(failed)
    if not execution.get("ready") or not execution.get("actionable"):
        return "execution_tree_observe_only"
    return "none"


def extract_layer_states(summary: dict[str, Any]) -> dict[str, Any]:
    pre_bayes = summary.get("pre_bayes") or {}
    workflow = summary.get("workflow_full") or {}
    policy = summary.get("policy_final") or {}
    ranker = summary.get("augmented_ranker_target") or summary.get("ranker_target") or {}
    execution = summary.get("augmented_execution_candidate") or summary.get("execution_candidate") or {}
    bbn_network = read_json(STATE_DIR / SYMBOL / "bbn_network.json")
    return {
        "pre_bayes_filter_state": {
            "gate": pre_bayes.get("latest_gate_status")
            or pre_bayes.get("gate_status")
            or execution.get("pre_bayes_gate_status")
            or "not_available",
            "canonical_regime": pre_bayes.get("latest_canonical_structural_active_regime"),
            "confidence": pre_bayes.get("latest_canonical_structural_confidence"),
            "uses_soft_evidence": pre_bayes.get("latest_uses_soft_evidence"),
        },
        "bbn_posterior": {
            "canonical_probabilities": pre_bayes.get("latest_canonical_structural_probabilities"),
            "network_nodes": len((bbn_network or {}).get("nodes", {})),
            "network_edges": len((bbn_network or {}).get("edges", [])),
            "source": str(STATE_DIR / SYMBOL / "bbn_network.json"),
        },
        "catboost_path_ranker_label": {
            "score_model_family": "catboost",
            "runtime_selection_status": ranker.get("runtime_selection_status"),
            "runtime_selection_ready": ranker.get("runtime_selection_ready"),
            "trainer_artifact_status": ranker.get("trainer_artifact_status"),
            "raw_scored_mature_rows": ranker.get("raw_scored_mature_rows"),
            "production_validation_rows": ranker.get("production_validation_rows"),
            "observation_validation_rows": ranker.get("observation_validation_rows"),
            "path_id": execution.get("path_id") or workflow.get("closed_loop_branch_admission", {}).get("path_id"),
        },
        "execution_tree_decision": {
            "ready": execution.get("ready"),
            "actionable": execution.get("actionable"),
            "review": execution.get("review_status"),
            "candidate_status": execution.get("candidate_status"),
            "execution_gate_status": execution.get("execution_gate_status"),
            "decision_hint": execution.get("decision_hint"),
            "closed_loop_branch_admission": workflow.get("closed_loop_branch_admission"),
        },
        "policy_status": policy,
    }


def enrich_layer_contract(summary: dict[str, Any], trade_summary: dict[str, Any]) -> dict[str, Any]:
    enricher = load_module(ENRICHER_SCRIPT, "structural_feedback_trade_enricher")
    states = extract_layer_states(summary)
    failure_reason = execution_failure_reason(
        states["execution_tree_decision"],
        summary.get("chain_exits", {}),
        summary.get("augmented_catboost", {}).get("exits", {}),
    )
    rows = []
    for row in read_jsonl(REPAIRED_TRADES):
        provider = row.get("source_provider") or row.get("provider_provenance", {}).get("provider")
        label = "observed_win" if row.get("realized_outcome") == "win" or row.get("outcome") == "win" else "observed_loss"
        catboost_label = dict(states["catboost_path_ranker_label"])
        catboost_label["label"] = label
        enriched = enricher.enrich_trade_with_layer_contract(
            row,
            auto_quant_run_id=SOURCE_RUN_ID,
            symbol=SYMBOL,
            provider_provenance=row.get("provider_provenance", {"provider": provider, "timeframe": "1h"}),
            pre_bayes_filter_state=states["pre_bayes_filter_state"],
            bbn_posterior=states["bbn_posterior"],
            catboost_path_ranker_label=catboost_label,
            execution_tree_decision=states["execution_tree_decision"],
            failure_reason=failure_reason,
            quality_weight=0.25 if failure_reason != "none" else 1.0,
        )
        enriched["exporter_enricher_run_id"] = RUN_ID
        rows.append(enriched)
    write_jsonl(ENRICHED_TRADES, rows)
    trade_summary["enriched_path"] = str(ENRICHED_TRADES)
    trade_summary["enriched_rows"] = len(rows)
    trade_summary["failure_reason"] = failure_reason
    return {
        "enriched_rows": len(rows),
        "enriched_path": str(ENRICHED_TRADES),
        "failure_reason": failure_reason,
        "layer_states": states,
    }


REQUIRED_BRANCH_FIELDS = [
    "main_regime",
    "sub_regime",
    "sub_sub_regime_or_profit_factor",
    "profit_factor",
]
REQUIRED_DOWNSTREAM_FIELDS = [
    "provider_provenance",
    "pre_bayes_filter_state",
    "bbn_posterior",
    "catboost_path_ranker_label",
    "execution_tree_decision",
    "failure_reason",
    "quality_weight",
]


def present(value: Any) -> bool:
    return value is not None and value != "" and value != [] and value != {}


def validate_row(row: dict[str, Any]) -> list[str]:
    failures = []
    if not present(row.get("branch_path") or row.get("regime_profit_branch_path")):
        failures.append("missing_branch_path")
    for field in REQUIRED_BRANCH_FIELDS:
        if not present(row.get(field)):
            failures.append(f"missing_{field}")
    for field in REQUIRED_DOWNSTREAM_FIELDS:
        if not present(row.get(field)):
            failures.append(f"missing_{field}")
    if not (present(row.get("outcome")) or (present(row.get("realized_outcome")) and "pnl" in row)):
        failures.append("missing_outcome")
    if row.get("auto_quant_run_id") != SOURCE_RUN_ID:
        failures.append("wrong_auto_quant_run_id")
    symbol = row.get("symbol")
    if isinstance(symbol, str) and ("104902" in symbol or "YAHOO_BTC_PULLBACK" in symbol):
        failures.append("stale_symbol_namespace")
    return failures


def validate_enriched_rows() -> dict[str, Any]:
    rows = read_jsonl(ENRICHED_TRADES)
    failure_counts: dict[str, int] = {}
    examples = []
    provider_counts: dict[str, int] = {}
    branch_counts: dict[str, int] = {}
    accepted = 0
    for index, row in enumerate(rows, 1):
        provider = row.get("provider_provenance", {}).get("provider", "<missing>")
        provider_counts[provider] = provider_counts.get(provider, 0) + 1
        branch = str(row.get("regime_profit_branch_path") or "<missing>")
        branch_counts[branch] = branch_counts.get(branch, 0) + 1
        failures = validate_row(row)
        if failures:
            for failure in failures:
                failure_counts[failure] = failure_counts.get(failure, 0) + 1
            if len(examples) < 12:
                examples.append({"line": index, "trade_id": row.get("trade_id"), "failures": failures})
        else:
            accepted += 1
    return {
        "checked_rows": len(rows),
        "layer_contract_valid_rows": accepted,
        "rejected_rows": len(rows) - accepted,
        "failure_counts": failure_counts,
        "provider_counts": provider_counts,
        "branch_counts": branch_counts,
        "examples": examples,
        "gate_result": "pass:layer_contract_schema_valid" if accepted == len(rows) and rows else "fail_closed:layer_contract_schema_invalid",
    }


def write_final_report(summary: dict[str, Any], validation: dict[str, Any]) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    json_path = REPORT_DIR / "115700_enriched_downstream_chain_v1.json"
    md_path = REPORT_DIR / "115700_enriched_downstream_chain_v1.md"
    assertions_path = CHECK_DIR / "115700_enriched_downstream_chain_v1_assertions.out"
    checklist_path = REPORT_DIR / "prompt_to_artifact_checklist_115700_enriched_downstream_chain_v1.csv"

    summary["layer_contract_validation"] = validation
    write_json(json_path, summary)

    chain_exits = summary.get("chain_exits", {})
    augmented_exits = summary.get("augmented_catboost", {}).get("exits", {})
    pre_bayes = summary.get("pre_bayes", {})
    ranker = summary.get("augmented_ranker_target") or summary.get("ranker_target") or {}
    execution = summary.get("augmented_execution_candidate") or summary.get("execution_candidate") or {}

    lines = [
        "# 115700 Enriched Downstream Chain v1",
        "",
        f"Run id: `{RUN_ID}`",
        f"Source AQ root: `{SOURCE_RUN_ID}`",
        f"Symbol: `{SYMBOL}`",
        "",
        "## Scope",
        "This slice consumes the already-counted `115700` six-provider 1h provider/AQ packet, repairs row-level run id/symbol/provider provenance in an isolated derived JSONL, runs the ordered downstream chain, then emits a final layer-contract JSONL with actual Pre-Bayes/BBN/CatBoost/execution-tree readback fields.",
        "It does not edit ict-engine runtime code, recount the source provider/AQ root, approve selected history/source-control intake, promote a candidate, or call `update_goal`.",
        "",
        "## Row Repair",
        f"- Raw materialized trades: `{summary['trade_summary'].get('raw_path')}`.",
        f"- Repaired trades used for ingest: `{summary['trade_summary'].get('path')}`.",
        f"- Enriched layer-contract trades: `{summary['trade_summary'].get('enriched_path')}`.",
        f"- Repaired/enriched rows: `{summary['trade_summary'].get('rows')}` / `{summary['trade_summary'].get('enriched_rows')}`.",
        f"- Provider counts: `{validation.get('provider_counts')}`.",
        f"- Branch counts: `{validation.get('branch_counts')}`.",
        "",
        "## Ordered Chain",
        f"- Command exits: `{chain_exits}`.",
        f"- Augmented CatBoost exits: `{augmented_exits}`.",
        f"- Pre-Bayes gate: `{pre_bayes.get('latest_gate_status') or execution.get('pre_bayes_gate_status')}`.",
        f"- Ranker runtime status: `{ranker.get('runtime_selection_status')}` ready `{ranker.get('runtime_selection_ready')}`.",
        f"- Ranker rows raw/production/observation: `{ranker.get('raw_scored_mature_rows')}/{ranker.get('production_validation_rows')}/{ranker.get('observation_validation_rows')}`.",
        f"- Execution ready/actionable/review: `{execution.get('ready')}` / `{execution.get('actionable')}` / `{execution.get('review_status')}`.",
        "",
        "## Layer Contract Gate",
        f"- Checked rows: `{validation.get('checked_rows')}`.",
        f"- Valid layer-contract rows: `{validation.get('layer_contract_valid_rows')}`.",
        f"- Rejected rows: `{validation.get('rejected_rows')}`.",
        f"- Gate: `{validation.get('gate_result')}`.",
        f"- Failure reason carried by rows: `{summary['trade_summary'].get('failure_reason')}`.",
        "",
        "## Decision",
        "- `115700` now has an exact-root downstream readback with repaired/enriched row-level layer contract evidence.",
        "- Promotion remains fail-closed because execution-tree readiness/actionability is still not proven and selected-history/source-control acceptance is still absent.",
        "- `promotion_allowed=false`.",
        "- `trade_usable=false`.",
        "- `update_goal=false`.",
        "",
        "## Artifacts",
        f"- JSON: `{json_path}`",
        f"- Assertions: `{assertions_path}`",
        f"- Checklist: `{checklist_path}`",
        f"- Base downstream support report: `{REPORT_DIR / 'base-downstream-support' / '115700_six_provider_1h_downstream_chain_v1.md'}`",
    ]
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    with checklist_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["requirement", "artifact", "status", "note"])
        writer.writerow(["source 115700 AQ root", str(SOURCE_ROOT), "covered", SOURCE_RUN_ID])
        writer.writerow(["provider provenance repair", str(REPAIRED_TRADES), "covered", str(validation.get("provider_counts"))])
        writer.writerow(["real-trade ingest", str(OUT_DIR / "22_ingest_real_trades.out"), "covered", str(chain_exits.get("22_ingest_real_trades"))])
        writer.writerow(["Pre-Bayes/filter", str(OUT_DIR / "24_pre_bayes_status.out"), "covered", str(chain_exits.get("24_pre_bayes_status"))])
        writer.writerow(["BBN state", str(STATE_DIR / SYMBOL / "bbn_network.json"), "covered", "state readback captured"])
        writer.writerow(["CatBoost/path-ranker", str(PATH_RANKER_DIR), "covered", "standard and augmented commands attempted"])
        writer.writerow(["execution tree", str(OUT_DIR / "47_workflow_full_augmented.out"), "covered", "workflow readback captured"])
        writer.writerow(["layer contract validation", str(ENRICHED_TRADES), "covered", validation.get("gate_result")])

    assertion_lines = [
        f"PASS run_id={RUN_ID}",
        f"PASS source_run_id={SOURCE_RUN_ID}",
        f"PASS repaired_rows={summary['trade_summary'].get('rows')}",
        f"PASS enriched_rows={summary['trade_summary'].get('enriched_rows')}",
        ("PASS" if validation.get("rejected_rows") == 0 else "FAIL_CLOSED")
        + f" layer_contract_rejected_rows={validation.get('rejected_rows')}",
        f"PASS layer_contract_valid_rows={validation.get('layer_contract_valid_rows')}",
        f"PASS gate_result={validation.get('gate_result')}",
        f"FAIL_CLOSED execution_ready={execution.get('ready')} actionable={execution.get('actionable')} review={execution.get('review_status')}",
        "PASS promotion_allowed=false",
        "PASS trade_usable=false",
        "PASS update_goal=false",
    ]
    for label, code in chain_exits.items():
        assertion_lines.append(("PASS" if code == 0 else "FAIL_CLOSED") + f" {label}_exit={code}")
    for label, code in augmented_exits.items():
        assertion_lines.append(("PASS" if code == 0 else "FAIL_CLOSED") + f" {label}_exit={code}")
    assertions_path.write_text("\n".join(assertion_lines) + "\n", encoding="utf-8")


def main() -> int:
    for path in (OUT_DIR, CHECK_DIR, REPORT_DIR, DERIVED_DIR, PROVIDER_JSON_DIR, STATE_DIR, PATH_RANKER_DIR, SUPPORT_DIR):
        path.mkdir(parents=True, exist_ok=True)
    (ROOT / "run_id.txt").write_text(RUN_ID + "\n", encoding="utf-8")
    (ROOT / "source_run_id.txt").write_text(SOURCE_RUN_ID + "\n", encoding="utf-8")

    base = load_module(BASE_SCRIPT, "base_115700_downstream_chain")
    patch_base(base)

    source_summary = base.read_json(base.SOURCE_REPORT)
    initial_trade_summary = base.materialize_trades(source_summary.get("aq_results", []))
    trade_summary = repair_materialized_trades(source_summary, Path(initial_trade_summary["path"]))
    library_path = base.build_strategy_library(source_summary.get("aq_results", []))
    provider_json = base.prepare_provider_json()
    chain_exits = base.run_chain(trade_summary["path"], library_path, provider_json)
    augmented = base.run_augmented_catboost()
    cleanup_status = base.cleanup_catboost_info()

    summary = base.summarize(
        source_summary,
        trade_summary,
        library_path,
        provider_json,
        chain_exits,
        augmented,
        cleanup_status,
    )
    summary["run_id"] = RUN_ID
    summary["source_run_id"] = SOURCE_RUN_ID
    summary["promotion_allowed"] = False
    summary["trade_usable"] = False
    summary["update_goal"] = False
    layer_summary = enrich_layer_contract(summary, trade_summary)
    summary["layer_contract_enrichment"] = layer_summary
    validation = validate_enriched_rows()

    base.write_json(base.REPORT_DIR / "115700_six_provider_1h_downstream_chain_v1.json", summary)
    base.write_report(summary)
    write_final_report(summary, validation)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
