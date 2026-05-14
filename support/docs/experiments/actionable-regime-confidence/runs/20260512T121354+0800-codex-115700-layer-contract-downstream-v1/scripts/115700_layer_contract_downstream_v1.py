#!/usr/bin/env python3
from __future__ import annotations

import csv
import importlib.util
import json
import os
import shutil
import subprocess
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

RUN_ID = "20260512T121354+0800-codex-115700-layer-contract-downstream-v1"
SOURCE_RUN_ID = "20260512T115700+0800-codex-same-root-six-provider-1h-aq-v1"
SYMBOL = "B2R_SIX_PROVIDER_BTC_115700"
RUNS = Path("docs/experiments/actionable-regime-confidence/runs")
ROOT = RUNS / RUN_ID
SOURCE_ROOT = RUNS / SOURCE_RUN_ID
SOURCE_REPORT = SOURCE_ROOT / "same-root-six-provider-1h-aq-v1" / "same_root_six_provider_1h_aq_v1.json"
OUT_DIR = ROOT / "command-output"
CHECK_DIR = ROOT / "checks"
REPORT_DIR = ROOT / "115700-layer-contract-downstream-v1"
DERIVED_DIR = ROOT / "derived"
ENRICHED_WORKSPACE = ROOT / "enriched-workspace"
PROVIDER_JSON_DIR = ROOT / "provider-data-json"
STATE_DIR = ROOT / "state_115700_layer_contract_downstream_v1"
PATH_RANKER_DIR = ROOT / "path-ranker"
UV = "/Users/thrill3r/.local/bin/uv"
ICT = "./target/debug/ict-engine"

REQUIRED_BRANCH_FIELDS = ["main_regime", "sub_regime", "sub_sub_regime_or_profit_factor", "profit_factor"]
REQUIRED_DOWNSTREAM_FIELDS = [
    "provider_provenance",
    "pre_bayes_filter_state",
    "bbn_posterior",
    "catboost_path_ranker_label",
    "execution_tree_decision",
    "failure_reason",
    "quality_weight",
]


def load_enricher():
    path = Path("scripts/auto_quant_external/structural_feedback_trade_enricher.py")
    spec = importlib.util.spec_from_file_location("structural_feedback_trade_enricher", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def load_jsonl(path: Path):
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            yield json.loads(line)


def non_empty(value: Any) -> bool:
    return value is not None and value != "" and value != [] and value != {}


def normalize_ohlcv(source: Path) -> pd.DataFrame:
    raw = pd.read_csv(source)
    date_col = "date" if "date" in raw.columns else "ts" if "ts" in raw.columns else "timestamp"
    date = pd.to_datetime(raw[date_col], utc=True)
    out = pd.DataFrame(
        {
            "date": date,
            "open": pd.to_numeric(raw["open"], errors="coerce"),
            "high": pd.to_numeric(raw["high"], errors="coerce"),
            "low": pd.to_numeric(raw["low"], errors="coerce"),
            "close": pd.to_numeric(raw["close"], errors="coerce"),
            "volume": pd.to_numeric(raw.get("volume", 0.0), errors="coerce").fillna(0.0),
        }
    )
    out["volume"] = out["volume"].mask(out["volume"] < 0, 0.0)
    return out.dropna().sort_values("date").reset_index(drop=True)


def records_for_json(df: pd.DataFrame) -> list[dict[str, Any]]:
    records = []
    for row in df.itertuples(index=False):
        ts = pd.Timestamp(row.date)
        records.append(
            {
                "timestamp": ts.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "open": float(row.open),
                "high": float(row.high),
                "low": float(row.low),
                "close": float(row.close),
                "volume": float(row.volume),
            }
        )
    return records


def prepare_provider_json() -> dict[str, Any]:
    source = SOURCE_ROOT / "provider-csv" / "yfinance_btc_usd_1h.csv"
    df = normalize_ohlcv(source)
    outputs: dict[str, Any] = {}
    specs = {
        "1h": df,
        "4h": df.set_index("date").resample("4h").agg(
            {"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"}
        ).dropna().reset_index(),
        "1d": df.set_index("date").resample("1D").agg(
            {"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"}
        ).dropna().reset_index(),
    }
    for timeframe, frame in specs.items():
        path = PROVIDER_JSON_DIR / f"BTC_USD-{timeframe}.json"
        write_json(path, records_for_json(frame))
        outputs[timeframe] = {"path": str(path), "rows": len(frame)}
    return outputs


def build_library(report: dict[str, Any]) -> Path:
    strategies = []
    for result in report.get("aq_results", []):
        workspace = Path(result["workspace"])
        for name, payload in sorted(result.get("metrics", {}).items()):
            aggregate = payload.get("aggregate", {})
            strategies.append(
                {
                    "name": f"{result['provider']}:{name}",
                    "status": "ok" if result.get("run_tomac_exit") == 0 else "error",
                    "error": None if result.get("run_tomac_exit") == 0 else "run_tomac_exit_nonzero",
                    "commit": "experiment-run-root",
                    "file_path": str(workspace / "user_data" / "strategies_external" / f"{name}.py"),
                    "timerange": "20240601-20260512",
                    "pairs": ["BTC/USDT"],
                    "metadata": {
                        "strategy": name,
                        "mutation_id": f"{result['provider']}:{name}",
                        "base_factor": "same_root_provider_matrix_crypto",
                        "hypothesis": "115700 same-root six-provider 1h rows carry branch and provider provenance into the downstream chain.",
                        "paradigm": "provider_matrix_momentum_or_pullback",
                        "expected_regime": "Bull/Range -> ProviderCrypto* -> branch-preserving profit factor",
                        "source_provider": result.get("provider"),
                        "source_timeframe": "1h",
                        "aq_timeframe": "1h",
                        "provider_symbol": result.get("provider_symbol"),
                        "provider_source_csv": result.get("source_csv"),
                        "asset_class": "crypto_provider_ohlcv",
                        "status": "incubation_only",
                    },
                    "validation_metrics": aggregate,
                    "per_pair_metrics": payload.get("per_pair", {}),
                }
            )
    library = {
        "manifest_version": "1.0",
        "exported_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source_run_id": RUN_ID,
        "source_workspace": str(SOURCE_ROOT / "workspace"),
        "auto_quant_repo_url": "/Users/thrill3r/Auto-Quant",
        "auto_quant_pinned_ref": "local",
        "config_path": "config.tomac.json",
        "log_path": str(OUT_DIR),
        "strategies": strategies,
    }
    path = DERIVED_DIR / "strategy_library_115700_layer_contract_v1.json"
    write_json(path, library)
    return path


def layer_context_pending() -> dict[str, Any]:
    return {
        "pre_bayes_filter_state": {"status": "pending_downstream_readback", "source_run_id": RUN_ID},
        "bbn_posterior": {"status": "pending_downstream_readback", "source_run_id": RUN_ID},
        "catboost_path_ranker_label": {"status": "pending_downstream_readback", "source_run_id": RUN_ID},
        "execution_tree_decision": {"status": "pending_downstream_readback", "source_run_id": RUN_ID, "ready": False, "actionable": False},
        "failure_reason": "pending_downstream_readback",
        "quality_weight": 0.0,
    }


def parse_json_output(label: str) -> dict[str, Any]:
    path = OUT_DIR / f"{label}.out"
    if not path.exists() or not path.read_text(encoding="utf-8").strip():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def layer_context_from_chain(total_rows: int, exits: dict[str, int]) -> dict[str, Any]:
    pre = parse_json_output("24_pre_bayes_status")
    policy = parse_json_output("32_policy_training_status_final")
    execution = parse_json_output("33_workflow_execution_candidate")
    workflow = parse_json_output("34_workflow_full")
    validation = policy.get("structural_path_ranking_validation") or {}
    runtime = policy.get("structural_path_ranking_runtime") or {}
    raw_scored = validation.get("raw_scored_mature") or validation.get("raw_scored_mature_rows")
    production = validation.get("production_validation") or validation.get("production_validation_rows")
    observation = validation.get("observation_validation") or validation.get("observation_validation_rows")
    catboost_ok = exits.get("27_train_catboost") == 0 and exits.get("28_apply_catboost_history") == 0 and exits.get("29_apply_external_scores") == 0
    downstream_ok = all(exits.get(k) == 0 for k in ["22_ingest_real_trades", "23_analyze_provider_data", "24_pre_bayes_status", "25_policy_training_status_before_export", "26_export_structural_path_ranking_target", "32_policy_training_status_final", "33_workflow_execution_candidate", "34_workflow_full"])
    quality_weight = 1.0 if downstream_ok and catboost_ok else 0.0
    if quality_weight > 0.0 and isinstance(observation, int) and observation < min(total_rows, 30):
        quality_weight = 0.25
    failure_reason = execution.get("review_reason") or execution.get("candidate_status") or "downstream_readback_unavailable"
    return {
        "pre_bayes_filter_state": {
            "status": pre.get("latest_gate_status"),
            "canonical_regime": pre.get("latest_canonical_structural_active_regime"),
            "confidence": pre.get("latest_canonical_structural_confidence"),
            "policy_version": pre.get("latest_policy_version"),
            "uses_soft_evidence": pre.get("latest_uses_soft_evidence"),
        },
        "bbn_posterior": {
            "canonical_probabilities": pre.get("latest_canonical_structural_probabilities"),
            "soft_evidence": pre.get("latest_soft_evidence"),
            "filtered_assignments": pre.get("latest_filtered_assignments"),
        },
        "catboost_path_ranker_label": {
            "train_exit": exits.get("27_train_catboost"),
            "apply_exit": exits.get("28_apply_catboost_history"),
            "external_score_exit": exits.get("29_apply_external_scores"),
            "runtime": runtime,
            "validation": validation,
            "raw_scored_mature": raw_scored,
            "production_validation": production,
            "observation_validation": observation,
            "score_model_family": "catboost" if catboost_ok else "catboost_unavailable_or_failed",
        },
        "execution_tree_decision": {
            "ready": execution.get("ready"),
            "actionable": execution.get("actionable"),
            "review_status": execution.get("review_status"),
            "candidate_status": execution.get("candidate_status"),
            "execution_gate_status": execution.get("execution_gate_status"),
            "review_reason": execution.get("review_reason"),
            "path_id": execution.get("path_id"),
            "closed_loop_branch_admission": workflow.get("closed_loop_branch_admission"),
        },
        "failure_reason": str(failure_reason),
        "quality_weight": quality_weight,
    }


def provider_map(report: dict[str, Any]) -> dict[str, dict[str, Any]]:
    mapping = {}
    for result in report.get("aq_results", []):
        workspace = Path(result["workspace"]).name
        mapping[workspace] = {
            "provider": result.get("provider"),
            "provider_symbol": result.get("provider_symbol"),
            "timeframe": "1h",
            "source_csv": result.get("source_csv"),
            "source_rows": result.get("rows"),
            "first_ts_ms": result.get("first_ts_ms"),
            "last_ts_ms": result.get("last_ts_ms"),
        }
    return mapping


def enrich_all(report: dict[str, Any], context: dict[str, Any], suffix: str) -> dict[str, Any]:
    enricher = load_enricher()
    providers = provider_map(report)
    combined_path = DERIVED_DIR / f"115700_{suffix}_real_trades.jsonl"
    counts = Counter()
    source_files = []
    examples = []
    DERIVED_DIR.mkdir(parents=True, exist_ok=True)
    with combined_path.open("w", encoding="utf-8") as combined:
        for trade_file in sorted((SOURCE_ROOT / "workspace").glob("*/derived/*.real_trades.jsonl")):
            workspace_name = trade_file.parts[-3]
            provenance = providers.get(workspace_name, {"provider": workspace_name, "timeframe": "1h"})
            rel_output = ENRICHED_WORKSPACE / workspace_name / "derived" / trade_file.name
            rel_output.parent.mkdir(parents=True, exist_ok=True)
            rows = []
            for trade in load_jsonl(trade_file):
                enriched = enricher.enrich_trade_with_layer_contract(
                    trade,
                    auto_quant_run_id=SOURCE_RUN_ID,
                    symbol=SYMBOL,
                    provider_provenance=provenance,
                    pre_bayes_filter_state=context["pre_bayes_filter_state"],
                    bbn_posterior=context["bbn_posterior"],
                    catboost_path_ranker_label=context["catboost_path_ranker_label"],
                    execution_tree_decision=context["execution_tree_decision"],
                    failure_reason=context["failure_reason"],
                    quality_weight=float(context["quality_weight"]),
                )
                rows.append(enriched)
                combined.write(json.dumps(enriched, ensure_ascii=True) + "\n")
                counts["rows"] += 1
                counts[f"provider:{provenance.get('provider')}"] += 1
                if len(examples) < 3:
                    examples.append(enriched)
            rel_output.write_text("".join(json.dumps(row, ensure_ascii=True) + "\n" for row in rows), encoding="utf-8")
            source_files.append({"source": str(trade_file), "output": str(rel_output), "rows": len(rows), "provider": provenance.get("provider")})
    return {"path": str(combined_path), "rows": counts["rows"], "counts": dict(counts), "files": source_files, "examples": examples}


def run_command(label: str, cmd: list[str], env: dict[str, str] | None = None) -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)
    write_text(OUT_DIR / f"{label}.cmd", " ".join(cmd) + "\n")
    proc = subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False, env=env)
    write_text(OUT_DIR / f"{label}.out", proc.stdout)
    write_text(OUT_DIR / f"{label}.err", proc.stderr)
    write_text(CHECK_DIR / f"{label}.exit", f"{proc.returncode}\n")
    return proc.returncode


def run_chain(trades_path: str, library_path: Path, provider_json: dict[str, Any]) -> dict[str, int]:
    env = os.environ.copy()
    env.update({"OMP_NUM_THREADS": "1", "OPENBLAS_NUM_THREADS": "1", "MKL_NUM_THREADS": "1", "VECLIB_MAXIMUM_THREADS": "1"})
    target_history = STATE_DIR / SYMBOL / "policy_training" / "structural_path_ranking_target_history.csv"
    model_dir = PATH_RANKER_DIR / "catboost_model"
    history_scores = PATH_RANKER_DIR / "history_scores.csv"
    trainer_artifact = model_dir / "trainer_artifact.json"
    commands = {
        "20_auto_quant_results_import": [ICT, "auto-quant-results-import", "--symbol", SYMBOL, "--state-dir", str(STATE_DIR), "--library", str(library_path)],
        "21_auto_quant_prior_init": [ICT, "auto-quant-prior-init", "--symbol", SYMBOL, "--state-dir", str(STATE_DIR), "--library", str(library_path), "--force"],
        "22_ingest_real_trades": [ICT, "auto-quant-ingest-real-trades", "--symbol", SYMBOL, "--state-dir", str(STATE_DIR), "--trades", trades_path, "--source", "same_root_six_provider_1h_aq_115700_layer_contract", "--force"],
        "23_analyze_provider_data": [ICT, "analyze", "--symbol", SYMBOL, "--data-htf", provider_json["1d"]["path"], "--data-mtf", provider_json["4h"]["path"], "--data-ltf", provider_json["1h"]["path"], "--state-dir", str(STATE_DIR), "--output-format", "json"],
        "24_pre_bayes_status": [ICT, "pre-bayes-status", "--symbol", SYMBOL, "--state-dir", str(STATE_DIR), "--refresh", "--output-format", "json"],
        "25_policy_training_status_before_export": [ICT, "policy-training-status", "--symbol", SYMBOL, "--state-dir", str(STATE_DIR), "--output-format", "json"],
        "26_export_structural_path_ranking_target": [ICT, "export-structural-path-ranking-target", "--symbol", SYMBOL, "--state-dir", str(STATE_DIR)],
        "27_train_catboost": [UV, "run", "--offline", "--python", "3.11", "--with", "pandas", "--with", "numpy", "--with", "catboost", "python", "scripts/auto_quant_external/pandas_path_ranker_trainer.py", "--target-csv", str(target_history), "--output-dir", str(model_dir), "--model-family", "catboost", "--output-scores", str(history_scores)],
        "28_apply_catboost_history": [UV, "run", "--offline", "--python", "3.11", "--with", "pandas", "--with", "numpy", "--with", "catboost", "python", "scripts/auto_quant_external/pandas_path_ranker_trainer.py", "--apply", "--model-dir", str(model_dir), "--target-csv", str(target_history), "--output-scores", str(history_scores)],
        "29_apply_external_scores": [ICT, "apply-structural-path-ranking-external-scores", "--symbol", SYMBOL, "--state-dir", str(STATE_DIR), "--scores-file", str(history_scores)],
        "30_register_trainer_artifact": [ICT, "register-structural-path-ranking-trainer-artifact", "--symbol", SYMBOL, "--state-dir", str(STATE_DIR), "--artifact-uri", str(trainer_artifact), "--model-family", "catboost", "--score-column", "raw_path_score"],
        "31_enable_runtime": [ICT, "enable-structural-path-ranking-runtime", "--symbol", SYMBOL, "--state-dir", str(STATE_DIR), "--reuse-mode", "prefer_history"],
        "32_policy_training_status_final": [ICT, "policy-training-status", "--symbol", SYMBOL, "--state-dir", str(STATE_DIR), "--output-format", "json"],
        "33_workflow_execution_candidate": [ICT, "workflow-status", "--symbol", SYMBOL, "--state-dir", str(STATE_DIR), "--refresh", "--phase", "execution-candidate", "--output-format", "json"],
        "34_workflow_full": [ICT, "workflow-status", "--symbol", SYMBOL, "--state-dir", str(STATE_DIR), "--refresh", "--output-format", "json"],
    }
    exits = {}
    for label, cmd in commands.items():
        exits[label] = run_command(label, cmd, env=env if "catboost" in label else None)
    return exits


def classify_row(row: dict[str, Any]) -> list[str]:
    failures = []
    branch_path = row.get("branch_path") or row.get("regime_profit_branch_path")
    if not non_empty(branch_path):
        failures.append("missing_branch_path")
    for field in REQUIRED_BRANCH_FIELDS:
        if not non_empty(row.get(field)):
            failures.append(f"missing_{field}")
    for field in REQUIRED_DOWNSTREAM_FIELDS:
        if not non_empty(row.get(field)):
            failures.append(f"missing_{field}")
    if row.get("auto_quant_run_id") != SOURCE_RUN_ID:
        failures.append("stale_or_wrong_auto_quant_run_id")
    symbol = row.get("symbol")
    if isinstance(symbol, str) and ("104902" in symbol or "YAHOO_BTC_PULLBACK" in symbol):
        failures.append("stale_symbol_namespace")
    return failures


def validate_rows(final_path: str, exits: dict[str, int]) -> dict[str, Any]:
    totals = Counter()
    failure_counts = Counter()
    examples = []
    provider_counts = Counter()
    for line_no, row in enumerate(load_jsonl(Path(final_path)), 1):
        totals["rows"] += 1
        failures = classify_row(row)
        if failures:
            totals["contract_rejected_rows"] += 1
            failure_counts.update(failures)
            if len(examples) < 8:
                examples.append({"line": line_no, "trade_id": row.get("trade_id"), "failures": failures})
        else:
            totals["contract_complete_rows"] += 1
            provider_counts[row.get("provider_provenance", {}).get("provider", "unknown")] += 1
            catboost = row.get("catboost_path_ranker_label") or {}
            execution = row.get("execution_tree_decision") or {}
            if float(row.get("quality_weight") or 0.0) > 0.0 and catboost.get("score_model_family") == "catboost" and non_empty(execution.get("execution_gate_status")):
                totals["market_factor_trainable_rows"] += 1
            else:
                totals["schema_complete_but_not_trainable_rows"] += 1
    return {
        "total_rows": totals["rows"],
        "contract_complete_rows": totals["contract_complete_rows"],
        "contract_rejected_rows": totals["contract_rejected_rows"],
        "market_factor_trainable_rows": totals["market_factor_trainable_rows"],
        "schema_complete_but_not_trainable_rows": totals["schema_complete_but_not_trainable_rows"],
        "failure_counts": dict(failure_counts),
        "provider_counts": dict(provider_counts),
        "examples": examples,
        "gate_result": "pass:market_factor_rows_available" if totals["market_factor_trainable_rows"] > 0 else "fail_closed:schema_complete_but_no_trainable_market_factor_rows",
        "promotion_allowed": False,
        "trade_usable": False,
        "update_goal": False,
        "command_exits": exits,
    }


def cleanup_catboost_info() -> str:
    path = Path("catboost_info")
    if path.exists():
        shutil.rmtree(path)
    status = "catboost_info_absent" if not path.exists() else "catboost_info_present"
    write_text(CHECK_DIR / "35_catboost_info_cleanup_check.exit", "0\n" if status == "catboost_info_absent" else "1\n")
    write_text(OUT_DIR / "35_catboost_info_cleanup_check.out", status + "\n")
    return status


def write_report(report: dict[str, Any]) -> None:
    json_path = REPORT_DIR / "115700_layer_contract_downstream_v1.json"
    md_path = REPORT_DIR / "115700_layer_contract_downstream_v1.md"
    assertions_path = CHECK_DIR / "115700_layer_contract_downstream_v1_assertions.out"
    write_json(json_path, report)
    validation = report["validation"]
    exits = report["chain_exits"]
    lines = [
        "# 115700 Layer Contract Downstream v1",
        "",
        f"Run id: `{RUN_ID}`",
        f"Source root: `{SOURCE_RUN_ID}`",
        "",
        "## Result",
        f"- Enriched rows: `{report['final_enrichment']['rows']}`.",
        f"- Contract-complete rows: `{validation['contract_complete_rows']}`.",
        f"- Market/factor trainable rows: `{validation['market_factor_trainable_rows']}`.",
        f"- Gate: `{validation['gate_result']}`.",
        f"- Promotion allowed: `{validation['promotion_allowed']}`.",
        "",
        "## Ordered Chain Exits",
    ]
    for key in sorted(exits):
        lines.append(f"- `{key}`: `{exits[key]}`")
    lines.extend([
        "",
        "## Provider Row Counts",
    ])
    for key, value in sorted(validation.get("provider_counts", {}).items()):
        lines.append(f"- `{key}`: `{value}`")
    lines.extend([
        "",
        "## Artifacts",
        f"- Pre-chain enriched JSONL: `{report['prechain_enrichment']['path']}`",
        f"- Final enriched JSONL: `{report['final_enrichment']['path']}`",
        f"- Strategy library: `{report['strategy_library']}`",
        f"- Provider JSON: `{PROVIDER_JSON_DIR}`",
        f"- State dir: `{STATE_DIR}`",
        f"- Command output: `{OUT_DIR}`",
        f"- JSON: `{json_path}`",
        f"- Assertions: `{assertions_path}`",
    ])
    write_text(md_path, "\n".join(lines) + "\n")
    assertions = [
        f"PASS run_id={RUN_ID}",
        f"PASS source_run_id={SOURCE_RUN_ID}",
        f"PASS enriched_rows={report['final_enrichment']['rows']}",
        f"PASS contract_complete_rows={validation['contract_complete_rows']}",
        f"PASS contract_rejected_rows={validation['contract_rejected_rows']}",
        ("PASS" if validation["market_factor_trainable_rows"] > 0 else "FAIL_CLOSED") + f" market_factor_trainable_rows={validation['market_factor_trainable_rows']}",
        f"PASS stale_or_wrong_auto_quant_run_id_rows={validation['failure_counts'].get('stale_or_wrong_auto_quant_run_id', 0)}",
        f"PASS stale_symbol_namespace_rows={validation['failure_counts'].get('stale_symbol_namespace', 0)}",
        f"PASS provider_counts={json.dumps(validation.get('provider_counts', {}), sort_keys=True)}",
        f"PASS promotion_allowed={str(validation['promotion_allowed']).lower()}",
        f"PASS trade_usable={str(validation['trade_usable']).lower()}",
        f"PASS update_goal={str(validation['update_goal']).lower()}",
    ]
    write_text(assertions_path, "\n".join(assertions) + "\n")


def main() -> int:
    for path in [OUT_DIR, CHECK_DIR, REPORT_DIR, DERIVED_DIR, ENRICHED_WORKSPACE, PROVIDER_JSON_DIR, PATH_RANKER_DIR]:
        path.mkdir(parents=True, exist_ok=True)
    write_text(ROOT / "run_id.txt", RUN_ID + "\n")
    report = json.loads(SOURCE_REPORT.read_text(encoding="utf-8"))
    library_path = build_library(report)
    provider_json = prepare_provider_json()
    prechain = enrich_all(report, layer_context_pending(), "prechain_layer_contract")
    exits = run_chain(prechain["path"], library_path, provider_json)
    cleanup = cleanup_catboost_info()
    final_context = layer_context_from_chain(prechain["rows"], exits)
    final_enrichment = enrich_all(report, final_context, "postchain_layer_contract")
    validation = validate_rows(final_enrichment["path"], exits)
    output = {
        "run_id": RUN_ID,
        "source_run_id": SOURCE_RUN_ID,
        "symbol": SYMBOL,
        "prechain_enrichment": prechain,
        "final_enrichment": final_enrichment,
        "strategy_library": str(library_path),
        "provider_json": provider_json,
        "chain_exits": exits,
        "final_layer_context": final_context,
        "validation": validation,
        "catboost_info_cleanup": cleanup,
        "promotion_allowed": False,
        "trade_usable": False,
        "update_goal": False,
    }
    write_report(output)
    print(json.dumps(output, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
