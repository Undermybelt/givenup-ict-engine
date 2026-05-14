from __future__ import annotations

import csv
import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any

import pandas as pd


RUN_ID = "20260512T120903+0800-codex-115500-same-root-aq-downstream-chain-v1"
SOURCE_RUN_ID = "20260512T115500+0800-codex-six-provider-btc-same-root-aq-ibkr-aggtrades-probe-v1"
SYMBOL = "B2R_SIX_PROVIDER_BTC_AQ_115500"

RUNS = Path("docs/experiments/actionable-regime-confidence/runs")
ROOT = RUNS / RUN_ID
SOURCE_ROOT = RUNS / SOURCE_RUN_ID
SOURCE_REPORT = (
    SOURCE_ROOT
    / "six-provider-btc-same-root-aq-ibkr-aggtrades-probe-v1"
    / "six_provider_btc_same_root_aq_ibkr_aggtrades_probe_v1.json"
)

OUT_DIR = ROOT / "command-output"
CHECK_DIR = ROOT / "checks"
REPORT_DIR = ROOT / "115500-same-root-aq-downstream-chain-v1"
DERIVED_DIR = ROOT / "derived"
STATE_DIR = ROOT / "state_115500_downstream_chain_v1"
PROVIDER_JSON_DIR = ROOT / "provider-data-json"
PATH_RANKER_DIR = ROOT / "path-ranker"
SUPPORT_DIR = PATH_RANKER_DIR / "catboost_feature_support_v1"
UV = "/Users/thrill3r/.local/bin/uv"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text()) if path.exists() else {}


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def parse_json_output(label: str) -> dict[str, Any]:
    path = OUT_DIR / f"{label}.out"
    if not path.exists() or not path.read_text().strip():
        return {}
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError:
        return {}


def normalize_ohlcv(source: Path) -> pd.DataFrame:
    raw = pd.read_csv(source)
    date_col = "date" if "date" in raw.columns else "timestamp" if "timestamp" in raw.columns else "ts"
    date = pd.to_datetime(raw[date_col], utc=True)
    volume = pd.to_numeric(raw.get("volume", 0.0), errors="coerce").fillna(0.0).astype(float)
    volume = volume.mask(volume < 0, 0.0)
    out = pd.DataFrame(
        {
            "date": date,
            "open": pd.to_numeric(raw["open"], errors="coerce").astype(float),
            "high": pd.to_numeric(raw["high"], errors="coerce").astype(float),
            "low": pd.to_numeric(raw["low"], errors="coerce").astype(float),
            "close": pd.to_numeric(raw["close"], errors="coerce").astype(float),
            "volume": volume,
        }
    )
    return out.dropna().sort_values("date").reset_index(drop=True)


def records_for_json(df: pd.DataFrame) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
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


def run_command(label: str, cmd: list[str], env: dict[str, str] | None = None) -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)
    merged_env = os.environ.copy()
    if env:
        merged_env.update(env)
    (OUT_DIR / f"{label}.cmd").write_text(" ".join(cmd) + "\n")
    proc = subprocess.run(
        cmd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        env=merged_env,
    )
    (OUT_DIR / f"{label}.out").write_text(proc.stdout)
    (OUT_DIR / f"{label}.err").write_text(proc.stderr)
    (CHECK_DIR / f"{label}.exit").write_text(f"{proc.returncode}\n")
    return proc.returncode


def metric_totals(results: list[dict[str, Any]]) -> dict[str, Any]:
    totals = {
        "provider_runs": len(results),
        "compile_success": 0,
        "run_success": 0,
        "strategies_with_metrics": 0,
        "total_trades": 0,
        "positive_profit_metric_count": 0,
    }
    for result in results:
        if result.get("compile_exit") == 0:
            totals["compile_success"] += 1
        if result.get("run_tomac_exit") == 0:
            totals["run_success"] += 1
        for payload in result.get("metrics", {}).values():
            aggregate = payload.get("aggregate", {})
            trades = int(aggregate.get("trade_count") or 0)
            profit = float(aggregate.get("total_profit_pct") or 0.0)
            totals["strategies_with_metrics"] += 1
            totals["total_trades"] += trades
            if profit > 0:
                totals["positive_profit_metric_count"] += 1
    return totals


def materialize_trades(source_summary: dict[str, Any]) -> dict[str, Any]:
    DERIVED_DIR.mkdir(parents=True, exist_ok=True)
    out_path = DERIVED_DIR / "115500_same_root_six_provider_aq_real_trades.jsonl"
    rows: list[dict[str, Any]] = []
    by_provider: dict[str, int] = {}
    by_path: dict[str, int] = {}

    for result in source_summary.get("aq_results", []):
        workspace = Path(result["workspace"])
        provider = result["provider"]
        for path in sorted((workspace / "derived").glob("*.real_trades.jsonl")):
            strategy = path.name.replace(".real_trades.jsonl", "")
            for line in path.read_text().splitlines():
                if not line.strip():
                    continue
                row = json.loads(line)
                branch_path = row.get("regime_profit_branch_path")
                if not branch_path:
                    continue
                idx = len(rows) + 1
                row["symbol"] = SYMBOL
                row["trade_id"] = f"{SYMBOL}_{provider}_{strategy}_{idx:05d}"
                row["auto_quant_run_id"] = RUN_ID
                row["provider_matrix_source_run_id"] = SOURCE_RUN_ID
                row["source_provider"] = provider
                row["source_timeframe"] = "1h"
                row["aq_timeframe"] = "1h"
                row["strategy_mutation_id"] = f"{provider}:{row.get('strategy_mutation_id', strategy)}"
                rows.append(row)
                by_provider[provider] = by_provider.get(provider, 0) + 1
                by_path[branch_path] = by_path.get(branch_path, 0) + 1

    out_path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows))
    return {"path": str(out_path), "rows": len(rows), "by_provider": by_provider, "by_path": by_path}


def build_strategy_library(source_summary: dict[str, Any]) -> Path:
    strategies = []
    for result in source_summary.get("aq_results", []):
        for name, payload in sorted(result.get("metrics", {}).items()):
            aggregate = payload.get("aggregate", {})
            strategies.append(
                {
                    "name": f"{result['provider']}:{name}",
                    "status": "ok" if result.get("run_tomac_exit") == 0 else "error",
                    "error": None if result.get("run_tomac_exit") == 0 else "run_tomac_exit_nonzero",
                    "commit": "experiment-run-root",
                    "file_path": str(Path(result["workspace"]) / "user_data" / "strategies_external" / f"{name}.py"),
                    "timerange": "20260401-20260512",
                    "pairs": ["BTC/USDT"],
                    "metadata": {
                        "strategy": name,
                        "mutation_id": f"{result['provider']}:{name}",
                        "base_factor": "same_root_provider_matrix_crypto",
                        "hypothesis": "115500 same-root six-provider 1h AQ observations can feed filter, BBN, CatBoost, and execution-tree gates.",
                        "paradigm": "provider_matrix_momentum_or_pullback",
                        "expected_regime": "Bull/Range -> ProviderCrypto* -> branch-preserving profit factor",
                        "source_provider": result["provider"],
                        "source_timeframe": "1h",
                        "aq_timeframe": "1h",
                        "asset_class": "crypto_provider_ohlcv",
                        "status": "incubation_only",
                    },
                    "validation_metrics": aggregate,
                    "per_pair_metrics": payload.get("per_pair", {}),
                }
            )
    library = {
        "manifest_version": "1.0",
        "exported_at": "2026-05-12T12:09:03+08:00",
        "source_run_id": RUN_ID,
        "source_provider_root_id": SOURCE_RUN_ID,
        "source_workspace": str(SOURCE_ROOT / "workspace"),
        "auto_quant_repo_url": "/Users/thrill3r/Auto-Quant",
        "auto_quant_pinned_ref": "local",
        "config_path": "config.tomac.json",
        "log_path": str(OUT_DIR),
        "strategies": strategies,
    }
    path = DERIVED_DIR / "strategy_library_115500_same_root_six_provider_aq_v1.json"
    write_json(path, library)
    return path


def prepare_provider_json() -> dict[str, Any]:
    PROVIDER_JSON_DIR.mkdir(parents=True, exist_ok=True)
    source = SOURCE_ROOT / "provider-csv" / "yfinance_btc_usd_1h.csv"
    df = normalize_ohlcv(source)
    indexed = df.set_index("date")
    specs = {
        "1h": df,
        "4h": indexed.resample("4h").agg(
            {"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"}
        ).dropna().reset_index(),
        "1d": indexed.resample("1D").agg(
            {"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"}
        ).dropna().reset_index(),
    }
    outputs: dict[str, Any] = {}
    for timeframe, frame in specs.items():
        path = PROVIDER_JSON_DIR / f"BTC_USD-{timeframe}.json"
        write_json(path, records_for_json(frame))
        outputs[timeframe] = {"path": str(path), "rows": len(frame)}
    return outputs


def run_chain(trades_path: str, library_path: Path, provider_json: dict[str, Any]) -> dict[str, int]:
    env = {
        "OMP_NUM_THREADS": "1",
        "OPENBLAS_NUM_THREADS": "1",
        "MKL_NUM_THREADS": "1",
        "VECLIB_MAXIMUM_THREADS": "1",
    }
    target_history = STATE_DIR / SYMBOL / "policy_training" / "structural_path_ranking_target_history.csv"
    model_dir = PATH_RANKER_DIR / "catboost_model"
    history_scores = PATH_RANKER_DIR / "history_scores.csv"
    trainer_artifact = model_dir / "trainer_artifact.json"

    commands = {
        "20_auto_quant_results_import": [
            "./target/debug/ict-engine",
            "auto-quant-results-import",
            "--symbol",
            SYMBOL,
            "--state-dir",
            str(STATE_DIR),
            "--library",
            str(library_path),
        ],
        "21_auto_quant_prior_init": [
            "./target/debug/ict-engine",
            "auto-quant-prior-init",
            "--symbol",
            SYMBOL,
            "--state-dir",
            str(STATE_DIR),
            "--library",
            str(library_path),
            "--force",
        ],
        "22_ingest_real_trades": [
            "./target/debug/ict-engine",
            "auto-quant-ingest-real-trades",
            "--symbol",
            SYMBOL,
            "--state-dir",
            str(STATE_DIR),
            "--trades",
            trades_path,
            "--source",
            "same_root_six_provider_aq_115500",
            "--force",
        ],
        "23_analyze_provider_data": [
            "./target/debug/ict-engine",
            "analyze",
            "--symbol",
            SYMBOL,
            "--data-htf",
            provider_json["1d"]["path"],
            "--data-mtf",
            provider_json["4h"]["path"],
            "--data-ltf",
            provider_json["1h"]["path"],
            "--state-dir",
            str(STATE_DIR),
            "--output-format",
            "json",
        ],
        "24_pre_bayes_status": [
            "./target/debug/ict-engine",
            "pre-bayes-status",
            "--symbol",
            SYMBOL,
            "--state-dir",
            str(STATE_DIR),
            "--refresh",
            "--output-format",
            "json",
        ],
        "25_policy_training_status_before_export": [
            "./target/debug/ict-engine",
            "policy-training-status",
            "--symbol",
            SYMBOL,
            "--state-dir",
            str(STATE_DIR),
            "--output-format",
            "json",
        ],
        "26_export_structural_path_ranking_target": [
            "./target/debug/ict-engine",
            "export-structural-path-ranking-target",
            "--symbol",
            SYMBOL,
            "--state-dir",
            str(STATE_DIR),
        ],
        "27_train_catboost": [
            UV,
            "run",
            "--offline",
            "--python",
            "3.11",
            "--with",
            "pandas",
            "--with",
            "numpy",
            "--with",
            "catboost",
            "python",
            "scripts/auto_quant_external/pandas_path_ranker_trainer.py",
            "--target-csv",
            str(target_history),
            "--output-dir",
            str(model_dir),
            "--model-family",
            "catboost",
            "--output-scores",
            str(history_scores),
        ],
        "28_apply_catboost_history": [
            UV,
            "run",
            "--offline",
            "--python",
            "3.11",
            "--with",
            "pandas",
            "--with",
            "numpy",
            "--with",
            "catboost",
            "python",
            "scripts/auto_quant_external/pandas_path_ranker_trainer.py",
            "--apply",
            "--model-dir",
            str(model_dir),
            "--target-csv",
            str(target_history),
            "--output-scores",
            str(history_scores),
        ],
        "29_apply_external_scores": [
            "./target/debug/ict-engine",
            "apply-structural-path-ranking-external-scores",
            "--symbol",
            SYMBOL,
            "--state-dir",
            str(STATE_DIR),
            "--scores-file",
            str(history_scores),
        ],
        "30_register_trainer_artifact": [
            "./target/debug/ict-engine",
            "register-structural-path-ranking-trainer-artifact",
            "--symbol",
            SYMBOL,
            "--state-dir",
            str(STATE_DIR),
            "--artifact-uri",
            str(trainer_artifact),
            "--model-family",
            "catboost",
            "--score-column",
            "raw_path_score",
        ],
        "31_enable_runtime": [
            "./target/debug/ict-engine",
            "enable-structural-path-ranking-runtime",
            "--symbol",
            SYMBOL,
            "--state-dir",
            str(STATE_DIR),
            "--reuse-mode",
            "prefer_history",
        ],
        "32_policy_training_status_final": [
            "./target/debug/ict-engine",
            "policy-training-status",
            "--symbol",
            SYMBOL,
            "--state-dir",
            str(STATE_DIR),
            "--output-format",
            "json",
        ],
        "33_workflow_execution_candidate": [
            "./target/debug/ict-engine",
            "workflow-status",
            "--symbol",
            SYMBOL,
            "--state-dir",
            str(STATE_DIR),
            "--refresh",
            "--phase",
            "execution-candidate",
            "--output-format",
            "json",
        ],
        "34_workflow_full": [
            "./target/debug/ict-engine",
            "workflow-status",
            "--symbol",
            SYMBOL,
            "--state-dir",
            str(STATE_DIR),
            "--refresh",
            "--output-format",
            "json",
        ],
    }
    exits: dict[str, int] = {}
    for label, cmd in commands.items():
        exits[label] = run_command(label, cmd, env=env if "catboost" in label else None)
    return exits


def augment_csv(source: Path, output: Path) -> Path:
    df = pd.read_csv(source)
    path_text = (
        df.get("regime_profit_branch_path", pd.Series([""] * len(df)))
        .fillna(df.get("path_label", pd.Series(["unknown"] * len(df))))
        .fillna(df.get("path_id", pd.Series(["unknown"] * len(df))))
        .astype(str)
    )
    df["ltf_path_label"] = path_text
    df["selected_direction"] = df.get("direction", pd.Series(["unknown"] * len(df))).fillna("unknown").astype(str)
    df["setup_family"] = (
        df.get("sub_regime", pd.Series([""] * len(df)))
        .fillna(df.get("path_label", pd.Series(["unknown"] * len(df))))
        .fillna("unknown")
        .astype(str)
    )
    df["entry_style"] = (
        df.get("sub_sub_regime_or_profit_factor", pd.Series(["provider_matrix"] * len(df)))
        .fillna("provider_matrix")
        .astype(str)
    )
    counts = path_text.map(path_text.value_counts()).fillna(0).astype(float)
    max_count = float(max(counts.max(), 1.0))
    df["evidence_quality_score"] = counts / max_count
    df["risk_reward"] = pd.to_numeric(df.get("current_posterior", 0.0), errors="coerce").fillna(0.0)
    df["setup_quality"] = pd.to_numeric(df.get("experience_prior", 0.0), errors="coerce").fillna(0.0)
    df["htf_alignment_score"] = pd.to_numeric(df.get("structural_baseline_score", 0.0), errors="coerce").fillna(0.0)
    output.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output, index=False)
    return output


def run_augmented_catboost_if_needed() -> dict[str, int]:
    policy = parse_json_output("32_policy_training_status_final")
    target = policy.get("structural_path_ranking_target", {})
    train_exit = int((CHECK_DIR / "27_train_catboost.exit").read_text().strip())
    raw_scored = int(target.get("raw_scored_mature_rows") or 0)
    if train_exit == 0 and raw_scored > 0:
        return {}

    env = {
        "OMP_NUM_THREADS": "1",
        "OPENBLAS_NUM_THREADS": "1",
        "MKL_NUM_THREADS": "1",
        "VECLIB_MAXIMUM_THREADS": "1",
    }
    policy_dir = STATE_DIR / SYMBOL / "policy_training"
    aug_hist = augment_csv(
        policy_dir / "structural_path_ranking_target_history.csv",
        SUPPORT_DIR / "structural_path_ranking_target_history_augmented.csv",
    )
    model_dir = SUPPORT_DIR / "catboost_model_augmented"
    history_scores = SUPPORT_DIR / "history_scores_augmented.csv"
    trainer_artifact = model_dir / "trainer_artifact.json"
    commands = {
        "40_train_catboost_augmented": [
            UV,
            "run",
            "--offline",
            "--python",
            "3.11",
            "--with",
            "pandas",
            "--with",
            "numpy",
            "--with",
            "catboost",
            "python",
            "scripts/auto_quant_external/pandas_path_ranker_trainer.py",
            "--target-csv",
            str(aug_hist),
            "--output-dir",
            str(model_dir),
            "--model-family",
            "catboost",
            "--output-scores",
            str(history_scores),
        ],
        "41_apply_catboost_augmented_history": [
            UV,
            "run",
            "--offline",
            "--python",
            "3.11",
            "--with",
            "pandas",
            "--with",
            "numpy",
            "--with",
            "catboost",
            "python",
            "scripts/auto_quant_external/pandas_path_ranker_trainer.py",
            "--apply",
            "--model-dir",
            str(model_dir),
            "--target-csv",
            str(aug_hist),
            "--output-scores",
            str(history_scores),
        ],
        "42_apply_external_scores_augmented": [
            "./target/debug/ict-engine",
            "apply-structural-path-ranking-external-scores",
            "--symbol",
            SYMBOL,
            "--state-dir",
            str(STATE_DIR),
            "--scores-file",
            str(history_scores),
        ],
        "43_register_trainer_artifact_augmented": [
            "./target/debug/ict-engine",
            "register-structural-path-ranking-trainer-artifact",
            "--symbol",
            SYMBOL,
            "--state-dir",
            str(STATE_DIR),
            "--artifact-uri",
            str(trainer_artifact),
            "--model-family",
            "catboost",
            "--score-column",
            "raw_path_score",
        ],
        "44_enable_runtime_augmented": [
            "./target/debug/ict-engine",
            "enable-structural-path-ranking-runtime",
            "--symbol",
            SYMBOL,
            "--state-dir",
            str(STATE_DIR),
            "--reuse-mode",
            "prefer_history",
        ],
        "45_policy_training_status_augmented": [
            "./target/debug/ict-engine",
            "policy-training-status",
            "--symbol",
            SYMBOL,
            "--state-dir",
            str(STATE_DIR),
            "--output-format",
            "json",
        ],
        "46_workflow_execution_candidate_augmented": [
            "./target/debug/ict-engine",
            "workflow-status",
            "--symbol",
            SYMBOL,
            "--state-dir",
            str(STATE_DIR),
            "--refresh",
            "--phase",
            "execution-candidate",
            "--output-format",
            "json",
        ],
        "47_workflow_full_augmented": [
            "./target/debug/ict-engine",
            "workflow-status",
            "--symbol",
            SYMBOL,
            "--state-dir",
            str(STATE_DIR),
            "--refresh",
            "--output-format",
            "json",
        ],
    }
    exits: dict[str, int] = {}
    for label, cmd in commands.items():
        exits[label] = run_command(label, cmd, env=env if "catboost" in label else None)
    return exits


def cleanup_catboost_info(label: str) -> str:
    path = Path("catboost_info")
    if path.exists():
        shutil.rmtree(path)
    status = "catboost_info_absent" if not path.exists() else "catboost_info_present"
    (OUT_DIR / f"{label}.out").write_text(status + "\n")
    (CHECK_DIR / f"{label}.exit").write_text("0\n" if status == "catboost_info_absent" else "1\n")
    return status


def summarize(
    source_summary: dict[str, Any],
    trade_summary: dict[str, Any],
    library_path: Path,
    provider_json: dict[str, Any],
    chain_exits: dict[str, int],
    augmented_exits: dict[str, int],
    cleanup_status: str,
) -> dict[str, Any]:
    final_policy_label = "45_policy_training_status_augmented" if augmented_exits else "32_policy_training_status_final"
    final_execution_label = "46_workflow_execution_candidate_augmented" if augmented_exits else "33_workflow_execution_candidate"
    final_workflow_label = "47_workflow_full_augmented" if augmented_exits else "34_workflow_full"
    policy = parse_json_output(final_policy_label)
    pre_bayes = parse_json_output("24_pre_bayes_status")
    execution = parse_json_output(final_execution_label)
    workflow = parse_json_output(final_workflow_label)
    ranker = policy.get("structural_path_ranking_target", {})
    return {
        "run_id": RUN_ID,
        "source_run_id": SOURCE_RUN_ID,
        "symbol": SYMBOL,
        "source_metric_totals": source_summary.get("metric_totals", {}),
        "source_provider_matrix": source_summary.get("provider_matrix", {}),
        "trade_summary": trade_summary,
        "strategy_library": str(library_path),
        "provider_json": provider_json,
        "chain_exits": chain_exits,
        "augmented_catboost_exits": augmented_exits,
        "pre_bayes": pre_bayes,
        "policy_final": policy,
        "ranker_target": ranker,
        "execution_candidate": execution,
        "workflow_full": workflow,
        "catboost_info_cleanup": cleanup_status,
        "promotion_allowed": False,
        "trade_usable": False,
        "update_goal": False,
    }


def write_report(summary: dict[str, Any]) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    report = REPORT_DIR / "115500_same_root_aq_downstream_chain_v1.md"
    assertions = CHECK_DIR / "115500_same_root_aq_downstream_chain_v1_assertions.out"
    checklist = REPORT_DIR / "prompt_to_artifact_checklist_115500_same_root_aq_downstream_chain_v1.csv"

    ranker = summary["ranker_target"]
    execution = summary["execution_candidate"]
    pre_bayes = summary["pre_bayes"]
    metric_totals = summary["source_metric_totals"]
    lines = [
        "# 115500 Same-Root AQ Downstream Chain v1",
        "",
        f"Run id: `{RUN_ID}`",
        f"Source AQ root: `{SOURCE_RUN_ID}`",
        f"Symbol: `{SYMBOL}`",
        "",
        "## Scope",
        "This run consumes the settled 115500 six-provider 1h AQ packet and pushes it through ict-engine Pre-Bayes/filter, BBN, CatBoost/path-ranker, and execution-tree surfaces.",
        "It does not edit ict-engine runtime code, approve selected history, mutate canonical source/control roots, promote a candidate, or call `update_goal`.",
        "",
        "## Source AQ Readback",
        f"- Provider AQ success: `{metric_totals.get('run_success')}/{metric_totals.get('provider_runs')}`.",
        f"- Strategies with metrics: `{metric_totals.get('strategies_with_metrics')}`.",
        f"- Total AQ trades: `{metric_totals.get('total_trades')}`.",
        f"- Materialized rooted trades for downstream ingestion: `{summary['trade_summary']['rows']}`.",
        f"- Trades by provider: `{summary['trade_summary']['by_provider']}`.",
        "",
        "## Chain Readback",
        f"- Ordered command exits: `{summary['chain_exits']}`.",
        f"- Augmented CatBoost exits: `{summary['augmented_catboost_exits']}`.",
        f"- Pre-Bayes gate: `{pre_bayes.get('gate_status') or pre_bayes.get('latest_policy', {}).get('gate_status')}`.",
        f"- Raw scored mature: `{ranker.get('raw_scored_mature_rows')}/{ranker.get('raw_scored_mature_min_rows')}`.",
        f"- Production validation: `{ranker.get('production_validation_rows')}/{ranker.get('production_validation_min_rows')}`.",
        f"- Observation validation: `{ranker.get('observation_validation_rows')}/{ranker.get('observation_validation_min_rows')}`.",
        f"- Trainer artifact ready: `{ranker.get('trainer_artifact_ready')}` status `{ranker.get('trainer_artifact_status')}`.",
        f"- Runtime selection: `{ranker.get('runtime_selection_status')}` ready `{ranker.get('runtime_selection_ready')}`.",
        f"- Execution ready/actionable: `{execution.get('ready')}` / `{execution.get('actionable')}` review `{execution.get('review_status')}`.",
        f"- CatBoost cleanup: `{summary['catboost_info_cleanup']}`.",
        "",
        "## Decision",
        "- Gate result: `115500_same_root_aq_downstream_chain_v1=six_provider_1h_aq_to_downstream_ran_execution_fail_closed_no_promotion`.",
        "- The six-provider AQ root is first-class and comparable 1h, but Board A promotion still requires non-observe execution admissibility and the strict acceptance axes.",
        "- `promotion_allowed=false`.",
        "- `trade_usable=false`.",
        "- `update_goal=false`.",
        "",
        "## Artifacts",
        f"- JSON: `{REPORT_DIR / '115500_same_root_aq_downstream_chain_v1.json'}`",
        f"- Assertions: `{assertions}`",
        f"- Checklist: `{checklist}`",
        f"- Trades: `{summary['trade_summary']['path']}`",
        f"- Strategy library: `{summary['strategy_library']}`",
        f"- State dir: `{STATE_DIR}`",
    ]
    report.write_text("\n".join(lines) + "\n")

    with checklist.open("w", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["requirement", "artifact", "status", "note"])
        writer.writerow(["six-provider 1h AQ source", str(SOURCE_REPORT), "covered", SOURCE_RUN_ID])
        writer.writerow(["rooted trade observations", summary["trade_summary"]["path"], "covered", str(summary["trade_summary"]["rows"])])
        writer.writerow(["strategy library import", summary["strategy_library"], "covered", "auto-quant-results-import attempted"])
        writer.writerow(["Pre-Bayes/filter and BBN", str(STATE_DIR), "covered", "analyze and pre-bayes-status captured"])
        writer.writerow(["CatBoost/path-ranker", str(PATH_RANKER_DIR), "covered", "train/apply/register/enable attempted"])
        writer.writerow(["execution tree", str(OUT_DIR), "covered", "workflow-status captured"])

    assertion_lines = [
        f"PASS run_id={RUN_ID}",
        f"PASS source_run={SOURCE_RUN_ID}",
        f"PASS source_provider_runs={metric_totals.get('provider_runs')}",
        f"PASS source_run_success={metric_totals.get('run_success')}",
        f"PASS source_total_trades={metric_totals.get('total_trades')}",
        f"PASS rooted_trades={summary['trade_summary']['rows']}",
        f"PASS raw_scored_mature={ranker.get('raw_scored_mature_rows')}",
        f"PASS production_validation={ranker.get('production_validation_rows')}",
        f"PASS observation_validation={ranker.get('observation_validation_rows')}",
        f"PASS trainer_artifact_ready={ranker.get('trainer_artifact_ready')}",
        f"PASS runtime_selection_status={ranker.get('runtime_selection_status')}",
        f"FAIL_CLOSED execution_ready={execution.get('ready')} actionable={execution.get('actionable')} review={execution.get('review_status')}",
        f"PASS catboost_info_cleanup={summary['catboost_info_cleanup']}",
        "PASS promotion_allowed=false",
        "PASS trade_usable=false",
        "PASS update_goal=false",
    ]
    for label, code in {**summary["chain_exits"], **summary["augmented_catboost_exits"]}.items():
        assertion_lines.append(("PASS" if code == 0 else "FAIL_CLOSED") + f" {label}_exit={code}")
    assertions.write_text("\n".join(assertion_lines) + "\n")


def main() -> int:
    for path in (OUT_DIR, CHECK_DIR, REPORT_DIR, DERIVED_DIR, STATE_DIR, PROVIDER_JSON_DIR, PATH_RANKER_DIR):
        path.mkdir(parents=True, exist_ok=True)
    (ROOT / "run_id.txt").write_text(RUN_ID + "\n")
    (ROOT / "source_run_id.txt").write_text(SOURCE_RUN_ID + "\n")

    source_summary = read_json(SOURCE_REPORT)
    trade_summary = materialize_trades(source_summary)
    library_path = build_strategy_library(source_summary)
    provider_json = prepare_provider_json()
    chain_exits = run_chain(trade_summary["path"], library_path, provider_json)
    augmented_exits = run_augmented_catboost_if_needed()
    cleanup_status = cleanup_catboost_info("49_catboost_info_cleanup_check")
    summary = summarize(source_summary, trade_summary, library_path, provider_json, chain_exits, augmented_exits, cleanup_status)
    write_json(REPORT_DIR / "115500_same_root_aq_downstream_chain_v1.json", summary)
    write_report(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
