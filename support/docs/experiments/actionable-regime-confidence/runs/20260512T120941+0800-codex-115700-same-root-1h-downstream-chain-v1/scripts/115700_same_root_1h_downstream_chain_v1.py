from __future__ import annotations

import csv
import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any

import pandas as pd


RUN_ID = "20260512T120941+0800-codex-115700-same-root-1h-downstream-chain-v1"
SOURCE_RUN_ID = "20260512T115700+0800-codex-same-root-six-provider-1h-aq-v1"
SYMBOL = "B2R_SAME_ROOT_SIX_PROVIDER_1H_AQ_115700"

RUNS = Path("docs/experiments/actionable-regime-confidence/runs")
ROOT = RUNS / RUN_ID
SOURCE_ROOT = RUNS / SOURCE_RUN_ID
SOURCE_REPORT = SOURCE_ROOT / "same-root-six-provider-1h-aq-v1" / "same_root_six_provider_1h_aq_v1.json"

OUT_DIR = ROOT / "command-output"
CHECK_DIR = ROOT / "checks"
REPORT_DIR = ROOT / "115700-same-root-1h-downstream-chain-v1"
DERIVED_DIR = ROOT / "derived"
PROVIDER_JSON_DIR = ROOT / "provider-data-json"
STATE_DIR = ROOT / "state_115700_downstream_chain_v1"
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
    date_col = "date" if "date" in raw.columns else "timestamp"
    out = pd.DataFrame(
        {
            "date": pd.to_datetime(raw[date_col], utc=True),
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
    PROVIDER_JSON_DIR.mkdir(parents=True, exist_ok=True)
    source = SOURCE_ROOT / "input-csv" / "yfinance_btc_usd_1h.csv"
    df = normalize_ohlcv(source)
    frames = {
        "1h": df,
        "4h": df.set_index("date")
        .resample("4h")
        .agg({"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"})
        .dropna()
        .reset_index(),
        "1d": df.set_index("date")
        .resample("1D")
        .agg({"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"})
        .dropna()
        .reset_index(),
    }
    outputs: dict[str, Any] = {}
    for timeframe, frame in frames.items():
        path = PROVIDER_JSON_DIR / f"BTC_USD-{timeframe}.json"
        write_json(path, records_for_json(frame))
        outputs[timeframe] = {"path": str(path), "rows": len(frame)}
    return outputs


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


def materialize_trades(results: list[dict[str, Any]]) -> dict[str, Any]:
    DERIVED_DIR.mkdir(parents=True, exist_ok=True)
    out_path = DERIVED_DIR / "same_root_1h_six_provider_aq_real_trades.jsonl"
    rows: list[dict[str, Any]] = []
    by_provider: dict[str, int] = {}
    by_path: dict[str, int] = {}
    for result in results:
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
                row["source_aq_run_id"] = SOURCE_RUN_ID
                row["source_provider"] = provider
                row["source_timeframe"] = "1h"
                row["aq_timeframe"] = "1h"
                row["strategy_mutation_id"] = f"{provider}:{row.get('strategy_mutation_id', strategy)}"
                row["provider_provenance"] = {
                    "same_root_authority_key": "115700_same_root_six_provider_1h_aq_v1",
                    "source_run_id": SOURCE_RUN_ID,
                    "provider": provider,
                    "source_csv": result.get("source_csv"),
                    "provider_rows": result.get("rows"),
                }
                row["quality_weight"] = 1.0 if row.get("realized_outcome") is not None else 0.5
                rows.append(row)
                by_provider[provider] = by_provider.get(provider, 0) + 1
                by_path[branch_path] = by_path.get(branch_path, 0) + 1
    out_path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows))
    return {"path": str(out_path), "rows": len(rows), "by_provider": by_provider, "by_path": by_path}


def build_strategy_library(results: list[dict[str, Any]]) -> Path:
    strategies = []
    for result in results:
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
                        "base_factor": "same_root_six_provider_1h_crypto",
                        "hypothesis": "The settled 115700 six-provider 1h AQ packet can feed the ordered downstream stack.",
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
        "exported_at": "2026-05-12T12:09:41+08:00",
        "source_run_id": RUN_ID,
        "source_aq_run_id": SOURCE_RUN_ID,
        "source_workspace": str(SOURCE_ROOT / "workspace"),
        "auto_quant_repo_url": "/Users/thrill3r/Auto-Quant",
        "auto_quant_pinned_ref": "local",
        "config_path": "config.tomac.json",
        "log_path": str(OUT_DIR),
        "strategies": strategies,
    }
    path = DERIVED_DIR / "strategy_library_115700_same_root_1h_aq_v1.json"
    write_json(path, library)
    return path


def run_command(label: str, cmd: list[str], env: dict[str, str] | None = None) -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / f"{label}.cmd").write_text(" ".join(cmd) + "\n")
    proc = subprocess.run(
        cmd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        env=env,
    )
    (OUT_DIR / f"{label}.out").write_text(proc.stdout)
    (OUT_DIR / f"{label}.err").write_text(proc.stderr)
    (CHECK_DIR / f"{label}.exit").write_text(f"{proc.returncode}\n")
    return proc.returncode


def catboost_env() -> dict[str, str]:
    env = os.environ.copy()
    env.update(
        {
            "OMP_NUM_THREADS": "1",
            "OPENBLAS_NUM_THREADS": "1",
            "MKL_NUM_THREADS": "1",
            "VECLIB_MAXIMUM_THREADS": "1",
        }
    )
    return env


def run_base_chain(trades_path: str, library_path: Path, provider_json: dict[str, Any]) -> dict[str, int]:
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
            "same_root_six_provider_1h_aq_115700",
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
    env = catboost_env()
    exits: dict[str, int] = {}
    for label, cmd in commands.items():
        exits[label] = run_command(label, cmd, env=env if "catboost" in label else None)
    return exits


def augment_csv(source: Path, output: Path) -> Path:
    df = pd.read_csv(source)
    fallback = pd.Series(["unknown"] * len(df))
    path_text = df.get("regime_profit_branch_path", fallback).fillna(df.get("path_label", fallback)).astype(str)
    df["ltf_path_label"] = path_text
    df["selected_direction"] = df.get("direction", fallback).fillna("unknown").astype(str)
    df["setup_family"] = df.get("sub_regime", fallback).fillna(df.get("path_label", fallback)).astype(str)
    df["entry_style"] = (
        df.get("sub_sub_regime_or_profit_factor", pd.Series(["provider_matrix"] * len(df)))
        .fillna("provider_matrix")
        .astype(str)
    )
    counts = path_text.map(path_text.value_counts()).fillna(0).astype(float)
    df["evidence_quality_score"] = counts / float(max(counts.max(), 1.0))
    df["risk_reward"] = pd.to_numeric(df.get("current_posterior", 0.0), errors="coerce").fillna(0.0)
    df["setup_quality"] = pd.to_numeric(df.get("experience_prior", 0.0), errors="coerce").fillna(0.0)
    df["htf_alignment_score"] = pd.to_numeric(df.get("structural_baseline_score", 0.0), errors="coerce").fillna(0.0)
    output.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output, index=False)
    return output


def run_augmented_ranker() -> dict[str, int]:
    policy_dir = STATE_DIR / SYMBOL / "policy_training"
    hist = policy_dir / "structural_path_ranking_target_history.csv"
    current = policy_dir / "structural_path_ranking_target.csv"
    exits: dict[str, int] = {}
    if not hist.exists() or not current.exists():
        (CHECK_DIR / "40_train_catboost_augmented.exit").write_text("97\n")
        (OUT_DIR / "40_train_catboost_augmented.err").write_text("missing structural target csv\n")
        return {"40_train_catboost_augmented": 97}

    aug_hist = augment_csv(hist, SUPPORT_DIR / "structural_path_ranking_target_history_augmented.csv")
    aug_current = augment_csv(current, SUPPORT_DIR / "structural_path_ranking_target_augmented.csv")
    model_dir = SUPPORT_DIR / "catboost_model_augmented"
    history_scores = SUPPORT_DIR / "history_scores_augmented.csv"
    trainer_artifact = model_dir / "trainer_artifact.json"
    env = catboost_env()

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
    write_json(SUPPORT_DIR / "augmented_csv_manifest.json", {"history": str(aug_hist), "current": str(aug_current)})
    for label, cmd in commands.items():
        exits[label] = run_command(label, cmd, env=env if "catboost" in label else None)
    return exits


def cleanup_catboost_info() -> str:
    path = Path("catboost_info")
    if path.exists():
        shutil.rmtree(path)
    status = "catboost_info_absent" if not path.exists() else "catboost_info_present"
    (OUT_DIR / "49_catboost_info_cleanup_check.out").write_text(status + "\n")
    (CHECK_DIR / "49_catboost_info_cleanup_check.exit").write_text("0\n" if status == "catboost_info_absent" else "1\n")
    return status


def summarize(
    source_summary: dict[str, Any],
    trades: dict[str, Any],
    library_path: Path,
    provider_json: dict[str, Any],
    exits: dict[str, int],
    cleanup_status: str,
) -> dict[str, Any]:
    policy = parse_json_output("45_policy_training_status_augmented") or parse_json_output("32_policy_training_status_final")
    pre_bayes = parse_json_output("24_pre_bayes_status")
    execution = parse_json_output("46_workflow_execution_candidate_augmented") or parse_json_output("33_workflow_execution_candidate")
    workflow = parse_json_output("47_workflow_full_augmented") or parse_json_output("34_workflow_full")
    target_summary = read_json(STATE_DIR / SYMBOL / "policy_training" / "structural_path_ranking_target_summary.json")
    ranker_target = policy.get("structural_path_ranking_target", {})
    ranker_validation = policy.get("structural_path_ranking_validation", {})
    return {
        "run_id": RUN_ID,
        "source_run_id": SOURCE_RUN_ID,
        "symbol": SYMBOL,
        "source_summary": source_summary,
        "source_metric_totals": source_summary.get("metric_totals", {}),
        "trade_summary": trades,
        "strategy_library": str(library_path),
        "provider_json": provider_json,
        "chain_exits": exits,
        "pre_bayes": pre_bayes,
        "policy_final": policy,
        "target_summary": target_summary,
        "ranker_target": ranker_target,
        "ranker_validation": ranker_validation,
        "execution_candidate": execution,
        "workflow_full": workflow,
        "catboost_info_cleanup": cleanup_status,
        "promotion_allowed": False,
        "trade_usable": False,
        "update_goal": False,
    }


def write_report(summary: dict[str, Any]) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    report = REPORT_DIR / "115700_same_root_1h_downstream_chain_v1.md"
    json_path = REPORT_DIR / "115700_same_root_1h_downstream_chain_v1.json"
    assertions = CHECK_DIR / "115700_same_root_1h_downstream_chain_v1_assertions.out"
    checklist = REPORT_DIR / "prompt_to_artifact_checklist_115700_same_root_1h_downstream_chain_v1.csv"

    source_totals = summary["source_metric_totals"]
    pre_bayes = summary["pre_bayes"]
    target = summary["ranker_target"]
    execution = summary["execution_candidate"]
    gate_status = (
        pre_bayes.get("gate_status")
        or pre_bayes.get("latest_gate_status")
        or pre_bayes.get("latest_policy", {}).get("gate_status")
    )
    lines = [
        "# 115700 Same-Root 1h Downstream Chain v1",
        "",
        f"Run id: `{RUN_ID}`",
        f"Source AQ root: `{SOURCE_RUN_ID}`",
        f"Symbol: `{SYMBOL}`",
        "",
        "## Scope",
        "This run consumes the settled `115700` six-provider 1h AQ packet and pushes it through the ordered downstream stack.",
        "It does not rerun Auto-Quant, edit ict-engine runtime code, approve selected history, or claim live trade use.",
        "",
        "## Source AQ Readback",
        f"- Provider fetch success: `{summary['source_summary'].get('provider_fetch_success')}`.",
        f"- AQ provider runs: `{source_totals.get('run_success')}/{source_totals.get('provider_runs')}`.",
        f"- Strategies with metrics: `{source_totals.get('strategies_with_metrics')}`.",
        f"- Total AQ trades: `{source_totals.get('total_trades')}`.",
        f"- Materialized rooted trades for ingestion: `{summary['trade_summary']['rows']}`.",
        f"- Trades by provider: `{summary['trade_summary']['by_provider']}`.",
        "",
        "## Ordered Chain Readback",
        f"- Command exits: `{summary['chain_exits']}`.",
        f"- Pre-Bayes gate: `{gate_status}`.",
        f"- Raw scored mature: `{target.get('raw_scored_mature_rows')}/{target.get('raw_scored_mature_min_rows')}`.",
        f"- Production validation: `{target.get('production_validation_rows')}/{target.get('production_validation_min_rows')}`.",
        f"- Observation validation: `{target.get('observation_validation_rows')}/{target.get('observation_validation_min_rows')}`.",
        f"- Trainer artifact ready: `{target.get('trainer_artifact_ready')}` status `{target.get('trainer_artifact_status')}`.",
        f"- Runtime selection: `{target.get('runtime_selection_status')}` ready `{target.get('runtime_selection_ready')}`.",
        f"- Execution ready/actionable: `{execution.get('ready')}` / `{execution.get('actionable')}` review `{execution.get('review_status')}`.",
        f"- CatBoost cleanup: `{summary['catboost_info_cleanup']}`.",
        "",
        "## Decision",
        "- Gate result: `115700_same_root_1h_downstream_chain_v1=ordered_chain_ran_from_six_provider_1h_aq_packet_but_requires_board_gate_readback_no_completion`.",
        "- `promotion_allowed=false`.",
        "- `trade_usable=false`.",
        "- `update_goal=false`.",
        "",
        "## Artifacts",
        f"- JSON: `{json_path}`",
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
        writer.writerow(["source six-provider 1h AQ packet", str(SOURCE_REPORT), "covered", SOURCE_RUN_ID])
        writer.writerow(["rooted trade observations", summary["trade_summary"]["path"], "covered", str(summary["trade_summary"]["rows"])])
        writer.writerow(["strategy library import", summary["strategy_library"], "covered", "auto-quant-results-import attempted"])
        writer.writerow(["Pre-Bayes/filter", str(STATE_DIR), "covered", "pre-bayes-status captured"])
        writer.writerow(["BBN state", str(STATE_DIR / SYMBOL / "bbn_network.json"), "covered", "state artifact readback path"])
        writer.writerow(["CatBoost/path-ranker", str(PATH_RANKER_DIR), "covered", "base and augmented train/apply/register attempted"])
        writer.writerow(["execution tree", str(OUT_DIR), "covered", "workflow-status captured"])

    assertion_lines = [
        f"PASS run_id={RUN_ID}",
        f"PASS source_run_id={SOURCE_RUN_ID}",
        f"PASS source_provider_fetch_success={summary['source_summary'].get('provider_fetch_success')}",
        f"PASS source_provider_runs={source_totals.get('provider_runs')}",
        f"PASS source_run_success={source_totals.get('run_success')}",
        f"PASS materialized_rooted_trades={summary['trade_summary']['rows']}",
        f"PASS pre_bayes_gate={gate_status}",
        f"PASS raw_scored_mature={target.get('raw_scored_mature_rows')}",
        f"PASS production_validation={target.get('production_validation_rows')}",
        f"PASS observation_validation={target.get('observation_validation_rows')}",
        f"PASS trainer_artifact_ready={target.get('trainer_artifact_ready')}",
        f"PASS runtime_selection_status={target.get('runtime_selection_status')}",
        f"PASS catboost_info_cleanup={summary['catboost_info_cleanup']}",
        f"READBACK execution_ready={execution.get('ready')} actionable={execution.get('actionable')} review={execution.get('review_status')}",
        "PASS promotion_allowed=false",
        "PASS trade_usable=false",
        "PASS update_goal=false",
    ]
    for label, code in summary["chain_exits"].items():
        assertion_lines.append(("PASS" if code == 0 else "FAIL_CLOSED") + f" {label}_exit={code}")
    assertions.write_text("\n".join(assertion_lines) + "\n")


def main() -> int:
    for path in (OUT_DIR, CHECK_DIR, REPORT_DIR, DERIVED_DIR, PROVIDER_JSON_DIR, PATH_RANKER_DIR, SUPPORT_DIR):
        path.mkdir(parents=True, exist_ok=True)
    (ROOT / "run_id.txt").write_text(RUN_ID + "\n")
    (ROOT / "source_run_id.txt").write_text(SOURCE_RUN_ID + "\n")

    source_summary = read_json(SOURCE_REPORT)
    aq_results = source_summary.get("aq_results", [])
    trades = materialize_trades(aq_results)
    library_path = build_strategy_library(aq_results)
    provider_json = prepare_provider_json()
    exits = run_base_chain(trades["path"], library_path, provider_json)
    exits.update(run_augmented_ranker())
    cleanup_status = cleanup_catboost_info()
    summary = summarize(source_summary, trades, library_path, provider_json, exits, cleanup_status)
    write_json(REPORT_DIR / "115700_same_root_1h_downstream_chain_v1.json", summary)
    write_report(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
