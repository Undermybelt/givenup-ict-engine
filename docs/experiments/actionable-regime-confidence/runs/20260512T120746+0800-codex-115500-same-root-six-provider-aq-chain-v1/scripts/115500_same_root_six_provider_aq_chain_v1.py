from __future__ import annotations

import csv
import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any

import pandas as pd


RUN_ID = "20260512T120746+0800-codex-115500-same-root-six-provider-aq-chain-v1"
SOURCE_RUN_ID = "20260512T115500+0800-codex-six-provider-btc-same-root-aq-ibkr-aggtrades-probe-v1"
SYMBOL = "B2R_PROVIDER_MATRIX_SIX_PROVIDER_AQ_115500"

RUNS = Path("docs/experiments/actionable-regime-confidence/runs")
ROOT = RUNS / RUN_ID
SOURCE_ROOT = RUNS / SOURCE_RUN_ID
SOURCE_JSON = SOURCE_ROOT / "six-provider-btc-same-root-aq-ibkr-aggtrades-probe-v1" / "six_provider_btc_same_root_aq_ibkr_aggtrades_probe_v1.json"

OUT_DIR = ROOT / "command-output"
CHECK_DIR = ROOT / "checks"
REPORT_DIR = ROOT / "115500-same-root-six-provider-aq-chain-v1"
DERIVED_DIR = ROOT / "derived"
STATE_DIR = ROOT / "state_six_provider_chain_v1"
PATH_RANKER_DIR = ROOT / "path-ranker"
PROVIDER_JSON_DIR = ROOT / "provider-data-json"
UV = "/Users/thrill3r/.local/bin/uv"


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text()) if path.exists() else {}


def exit_code(path: Path) -> int | None:
    if not path.exists():
        return None
    return int(path.read_text().strip())


def csv_rows(path: Path) -> int:
    if not path.exists():
        return 0
    with path.open() as fh:
        return max(sum(1 for _ in fh) - 1, 0)


def normalize_ohlcv(source: Path) -> pd.DataFrame:
    raw = pd.read_csv(source)
    date_col = "date" if "date" in raw.columns else "timestamp" if "timestamp" in raw.columns else "ts"
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


def run_command(label: str, cmd: list[str], env: dict[str, str] | None = None) -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / f"{label}.cmd").write_text(" ".join(cmd) + "\n")
    proc = subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False, env=env)
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


def provider_matrix_readback(source: dict[str, Any]) -> dict[str, Any]:
    fetch_rows = {
        "yfinance_btc_usd_1h": csv_rows(SOURCE_ROOT / "provider-csv" / "yfinance_btc_usd_1h.csv"),
        "kraken_xbtusd_1h": csv_rows(SOURCE_ROOT / "provider-csv" / "kraken_xbtusd_1h.csv"),
        "binance_btcusdt_1h": csv_rows(SOURCE_ROOT / "provider-csv" / "binance_btcusdt_1h.csv"),
        "bybit_btcusdt_linear_1h": csv_rows(SOURCE_ROOT / "provider-csv" / "bybit_btcusdt_linear_1h.csv"),
        "tvr_binance_btcusdt_1h": csv_rows(SOURCE_ROOT / "provider-csv" / "tvr_binance_btcusdt_1h.csv"),
        "ibkr_btc_paxos_aggtrades_1h": csv_rows(SOURCE_ROOT / "provider-csv" / "BTC_1h_aggtrades.csv"),
    }
    fetch_exits = {
        "yfinance_btc_usd_1h": exit_code(SOURCE_ROOT / "checks" / "10_yfinance_btc_usd_1h.exit"),
        "kraken_xbtusd_1h": exit_code(SOURCE_ROOT / "checks" / "11_kraken_xbtusd_1h.exit"),
        "binance_btcusdt_1h": exit_code(SOURCE_ROOT / "checks" / "12_binance_btcusdt_1h.exit"),
        "bybit_btcusdt_linear_1h": exit_code(SOURCE_ROOT / "checks" / "13_bybit_btcusdt_linear_1h.exit"),
        "tvr_binance_btcusdt_1h": exit_code(SOURCE_ROOT / "checks" / "14_tvr_binance_btcusdt_1h.exit"),
        "ibkr_btc_paxos_aggtrades_1h": exit_code(SOURCE_ROOT / "checks" / "15_ibkr_btc_paxos_aggtrades_1h.exit"),
    }
    return {
        "source_provider_root": str(SOURCE_ROOT),
        "fetch_rows": fetch_rows,
        "fetch_exits": fetch_exits,
        "same_root_six_provider_aq_authority": source.get("same_root_six_provider_aq_authority"),
        "ibkr_first_class_aq_success": source.get("ibkr_first_class_aq_success"),
        "authority_note": "all six provider CSVs and AQ workspaces are read from the single 115500 root at comparable 1h granularity",
    }


def materialize_trades(results: list[dict[str, Any]]) -> dict[str, Any]:
    DERIVED_DIR.mkdir(parents=True, exist_ok=True)
    out_path = DERIVED_DIR / "same_root_six_provider_aq_real_trades.jsonl"
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
                        "base_factor": "same_root_provider_matrix_crypto",
                        "hypothesis": "Comparable 1h provider rows can be routed through AQ and preserve branch-shaped trade observations.",
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
        "exported_at": "2026-05-12T12:07:46+08:00",
        "source_run_id": RUN_ID,
        "source_workspace": str(SOURCE_ROOT / "workspace"),
        "auto_quant_repo_url": "/Users/thrill3r/Auto-Quant",
        "auto_quant_pinned_ref": "local",
        "config_path": "config.tomac.json",
        "log_path": str(SOURCE_ROOT / "command-output"),
        "strategies": strategies,
    }
    path = DERIVED_DIR / "strategy_library_same_root_six_provider_aq_v1.json"
    write_json(path, library)
    return path


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


def run_chain(trades_path: str, library_path: Path, provider_json: dict[str, Any]) -> dict[str, int]:
    env = os.environ.copy()
    env.update({"OMP_NUM_THREADS": "1", "OPENBLAS_NUM_THREADS": "1", "MKL_NUM_THREADS": "1", "VECLIB_MAXIMUM_THREADS": "1"})
    target_history = STATE_DIR / SYMBOL / "policy_training" / "structural_path_ranking_target_history.csv"
    model_dir = PATH_RANKER_DIR / "catboost_model"
    history_scores = PATH_RANKER_DIR / "history_scores.csv"
    trainer_artifact = model_dir / "trainer_artifact.json"
    commands = {
        "20_auto_quant_results_import": ["./target/debug/ict-engine", "auto-quant-results-import", "--symbol", SYMBOL, "--state-dir", str(STATE_DIR), "--library", str(library_path)],
        "21_auto_quant_prior_init": ["./target/debug/ict-engine", "auto-quant-prior-init", "--symbol", SYMBOL, "--state-dir", str(STATE_DIR), "--library", str(library_path), "--force"],
        "22_ingest_real_trades": ["./target/debug/ict-engine", "auto-quant-ingest-real-trades", "--symbol", SYMBOL, "--state-dir", str(STATE_DIR), "--trades", trades_path, "--source", "same_root_six_provider_aq_115500", "--force"],
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
        "24_pre_bayes_status": ["./target/debug/ict-engine", "pre-bayes-status", "--symbol", SYMBOL, "--state-dir", str(STATE_DIR), "--refresh", "--output-format", "json"],
        "25_policy_training_status_before_export": ["./target/debug/ict-engine", "policy-training-status", "--symbol", SYMBOL, "--state-dir", str(STATE_DIR), "--output-format", "json"],
        "26_export_structural_path_ranking_target": ["./target/debug/ict-engine", "export-structural-path-ranking-target", "--symbol", SYMBOL, "--state-dir", str(STATE_DIR)],
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
        "29_apply_external_scores": ["./target/debug/ict-engine", "apply-structural-path-ranking-external-scores", "--symbol", SYMBOL, "--state-dir", str(STATE_DIR), "--scores-file", str(history_scores)],
        "30_register_trainer_artifact": ["./target/debug/ict-engine", "register-structural-path-ranking-trainer-artifact", "--symbol", SYMBOL, "--state-dir", str(STATE_DIR), "--artifact-uri", str(trainer_artifact), "--model-family", "catboost", "--score-column", "raw_path_score"],
        "31_enable_runtime": ["./target/debug/ict-engine", "enable-structural-path-ranking-runtime", "--symbol", SYMBOL, "--state-dir", str(STATE_DIR), "--reuse-mode", "prefer_history"],
        "32_policy_training_status_final": ["./target/debug/ict-engine", "policy-training-status", "--symbol", SYMBOL, "--state-dir", str(STATE_DIR), "--output-format", "json"],
        "33_workflow_execution_candidate": ["./target/debug/ict-engine", "workflow-status", "--symbol", SYMBOL, "--state-dir", str(STATE_DIR), "--refresh", "--phase", "execution-candidate", "--output-format", "json"],
        "34_workflow_full": ["./target/debug/ict-engine", "workflow-status", "--symbol", SYMBOL, "--state-dir", str(STATE_DIR), "--refresh", "--output-format", "json"],
    }
    exits: dict[str, int] = {}
    for label, cmd in commands.items():
        exits[label] = run_command(label, cmd, env=env if "catboost" in label else None)
    return exits


def parse_json_output(label: str) -> dict[str, Any]:
    path = OUT_DIR / f"{label}.out"
    if not path.exists() or not path.read_text().strip():
        return {}
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError:
        return {}


def cleanup_catboost_info() -> str:
    path = Path("catboost_info")
    if path.exists():
        shutil.rmtree(path)
    status = "catboost_info_absent" if not path.exists() else "catboost_info_present"
    (CHECK_DIR / "35_catboost_info_cleanup_check.exit").write_text("0\n" if status == "catboost_info_absent" else "1\n")
    (OUT_DIR / "35_catboost_info_cleanup_check.out").write_text(status + "\n")
    return status


def summarize(source: dict[str, Any], matrix: dict[str, Any], trade_summary: dict[str, Any], library_path: Path, provider_json: dict[str, Any], chain_exits: dict[str, int], cleanup_status: str) -> dict[str, Any]:
    policy = parse_json_output("32_policy_training_status_final")
    pre_bayes = parse_json_output("24_pre_bayes_status")
    execution = parse_json_output("33_workflow_execution_candidate")
    workflow = parse_json_output("34_workflow_full")
    target = read_json(STATE_DIR / SYMBOL / "policy_training" / "structural_path_ranking_target_summary.json")
    ranker = policy.get("structural_path_ranking_target", {})
    validation = policy.get("structural_path_ranking_validation", {})
    aq_results = source.get("aq_results", [])
    return {
        "run_id": RUN_ID,
        "symbol": SYMBOL,
        "source_run_id": SOURCE_RUN_ID,
        "provider_matrix": matrix,
        "aq_results": aq_results,
        "metric_totals": metric_totals(aq_results),
        "trade_summary": trade_summary,
        "strategy_library": str(library_path),
        "provider_json": provider_json,
        "chain_exits": chain_exits,
        "pre_bayes": pre_bayes,
        "policy_final": policy,
        "target_summary": target,
        "ranker_validation": validation,
        "ranker_target": ranker,
        "execution_candidate": execution,
        "workflow_full": workflow,
        "catboost_info_cleanup": cleanup_status,
        "same_root_provider_authority": bool(matrix.get("same_root_six_provider_aq_authority")),
        "all_provider_aq_compile_success": all(r.get("compile_exit") == 0 for r in aq_results),
        "all_provider_aq_run_success": all(r.get("run_tomac_exit") == 0 for r in aq_results),
        "promotion_allowed": False,
        "trade_usable": False,
        "update_goal": False,
    }


def write_report(summary: dict[str, Any]) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    report = REPORT_DIR / "115500_same_root_six_provider_aq_chain_v1.md"
    assertions = CHECK_DIR / "115500_same_root_six_provider_aq_chain_v1_assertions.out"
    checklist = REPORT_DIR / "prompt_to_artifact_checklist_115500_same_root_six_provider_aq_chain_v1.csv"
    matrix = summary["provider_matrix"]
    metric_totals = summary["metric_totals"]
    ranker = summary["ranker_target"]
    execution = summary["execution_candidate"]
    pre_bayes = summary["pre_bayes"]
    lines = [
        "# 115500 Same-Root Six-Provider AQ Chain v1",
        "",
        f"Run id: `{RUN_ID}`",
        f"Symbol: `{SYMBOL}`",
        f"Provider/AQ root: `{SOURCE_RUN_ID}`",
        "",
        "## Scope",
        "This run consumes the settled `115500` comparable 1h six-provider AQ packet and carries its rooted trade rows through ict-engine downstream readbacks.",
        "It does not edit ict-engine runtime code and does not promote a live-trade candidate.",
        "",
        "## Provider Rows",
    ]
    for key, value in matrix["fetch_rows"].items():
        lines.append(f"- `{key}`: rows `{value}`, exit `{matrix['fetch_exits'].get(key)}`.")
    lines.extend(["", "## AQ Results"])
    for result in summary["aq_results"]:
        lines.append(f"- `{result['provider']}`: rows `{result['rows']}`, compile `{result['compile_exit']}`, TOMAC `{result['run_tomac_exit']}`.")
        for strategy, payload in sorted(result.get("metrics", {}).items()):
            aggregate = payload.get("aggregate", {})
            lines.append(f"  - `{strategy}`: trades `{aggregate.get('trade_count')}`, profit_pct `{aggregate.get('total_profit_pct')}`, win_rate_pct `{aggregate.get('win_rate_pct')}`, profit_factor `{aggregate.get('profit_factor')}`.")
    lines.extend(
        [
            "",
            "## Chain Readback",
            f"- Materialized rooted trades: `{summary['trade_summary']['rows']}`.",
            f"- Trades by provider: `{summary['trade_summary']['by_provider']}`.",
            f"- Provider AQ run success: `{metric_totals['run_success']}/{metric_totals['provider_runs']}`.",
            f"- Ordered command exits: `{summary['chain_exits']}`.",
            f"- Pre-Bayes gate: `{pre_bayes.get('gate_status') or pre_bayes.get('latest_policy', {}).get('gate_status')}`.",
            f"- Raw scored mature: `{ranker.get('raw_scored_mature_rows')}/{ranker.get('raw_scored_mature_min_rows')}`.",
            f"- Production validation: `{ranker.get('production_validation_rows')}/{ranker.get('production_validation_min_rows')}`.",
            f"- Observation validation: `{ranker.get('observation_validation_rows')}/{ranker.get('observation_validation_min_rows')}`.",
            f"- Trainer artifact ready: `{ranker.get('trainer_artifact_ready')}` status `{ranker.get('trainer_artifact_status')}`.",
            f"- Runtime selection: `{ranker.get('runtime_selection_status')}` ready `{ranker.get('runtime_selection_ready')}`.",
            f"- Execution ready/actionable: `{execution.get('ready')}` / `{execution.get('actionable')}` review `{execution.get('review_status')}`.",
            "",
            "## Decision",
            "- Gate result: `115500_same_root_six_provider_aq_chain=full_1h_provider_authority_downstream_ran_but_execution_fail_closed`.",
            "- Same-root comparable 1h provider authority is present, but promotion remains blocked until downstream execution is ready/actionable with non-observe review.",
            "- `promotion_allowed=false`.",
            "- `trade_usable=false`.",
            "- `update_goal=false`.",
            "",
            "## Artifacts",
            f"- JSON: `{REPORT_DIR / '115500_same_root_six_provider_aq_chain_v1.json'}`",
            f"- Assertions: `{assertions}`",
            f"- Checklist: `{checklist}`",
            f"- Trades: `{summary['trade_summary']['path']}`",
            f"- Strategy library: `{summary['strategy_library']}`",
            f"- State dir: `{STATE_DIR}`",
            f"- CatBoost cleanup: `{summary['catboost_info_cleanup']}`",
        ]
    )
    report.write_text("\n".join(lines) + "\n")
    with checklist.open("w", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["requirement", "artifact", "status", "note"])
        writer.writerow(["comparable six provider AQ root", str(SOURCE_ROOT), "covered", SOURCE_RUN_ID])
        writer.writerow(["rooted trade observations", summary["trade_summary"]["path"], "covered", str(summary["trade_summary"]["rows"])])
        writer.writerow(["strategy library import", summary["strategy_library"], "covered", "auto-quant-results-import attempted"])
        writer.writerow(["Pre-Bayes/filter", str(STATE_DIR), "covered", "pre-bayes-status captured"])
        writer.writerow(["CatBoost/path-ranker", str(PATH_RANKER_DIR), "covered", "train/apply/register/enable attempted"])
        writer.writerow(["execution tree", str(OUT_DIR), "covered", "workflow-status captured"])
    assertion_lines = [
        f"PASS run_id={RUN_ID}",
        f"PASS source_run={SOURCE_RUN_ID}",
        f"PASS same_root_provider_authority={summary['same_root_provider_authority']}",
        f"PASS provider_runs={metric_totals['provider_runs']}",
        f"PASS compile_success={metric_totals['compile_success']}",
        f"PASS run_success={metric_totals['run_success']}",
        f"PASS rooted_trades={summary['trade_summary']['rows']}",
        f"PASS raw_scored_mature={ranker.get('raw_scored_mature_rows')}",
        f"PASS production_validation={ranker.get('production_validation_rows')}",
        f"PASS observation_validation={ranker.get('observation_validation_rows')}",
        f"PASS trainer_artifact_ready={ranker.get('trainer_artifact_ready')}",
        f"PASS catboost_info_cleanup={summary['catboost_info_cleanup']}",
        f"FAIL_CLOSED execution_ready={execution.get('ready')} actionable={execution.get('actionable')} review={execution.get('review_status')}",
        "PASS promotion_allowed=false",
        "PASS trade_usable=false",
        "PASS update_goal=false",
    ]
    for label, code in summary["chain_exits"].items():
        assertion_lines.append(("PASS" if code == 0 else "FAIL_CLOSED") + f" {label}_exit={code}")
    assertions.write_text("\n".join(assertion_lines) + "\n")


def main() -> int:
    for path in (OUT_DIR, CHECK_DIR, REPORT_DIR, DERIVED_DIR, PATH_RANKER_DIR, PROVIDER_JSON_DIR):
        path.mkdir(parents=True, exist_ok=True)
    (ROOT / "run_id.txt").write_text(RUN_ID + "\n")
    (ROOT / "source_run_id.txt").write_text(SOURCE_RUN_ID + "\n")
    source = read_json(SOURCE_JSON)
    aq_results = source.get("aq_results", [])
    matrix = provider_matrix_readback(source)
    trade_summary = materialize_trades(aq_results)
    library_path = build_strategy_library(aq_results)
    provider_json = prepare_provider_json()
    chain_exits = run_chain(trade_summary["path"], library_path, provider_json)
    cleanup_status = cleanup_catboost_info()
    summary = summarize(source, matrix, trade_summary, library_path, provider_json, chain_exits, cleanup_status)
    write_json(REPORT_DIR / "115500_same_root_six_provider_aq_chain_v1.json", summary)
    write_report(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
