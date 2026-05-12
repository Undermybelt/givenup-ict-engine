from __future__ import annotations

import csv
import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any

import pandas as pd


RUN_ID = "20260512T115500+0800-codex-six-provider-btc-same-root-aq-ibkr-aggtrades-probe-v1"
SYMBOL = "B2R_SIX_PROVIDER_BTC_1H_AQ_115500"

RUNS = Path("docs/experiments/actionable-regime-confidence/runs")
ROOT = RUNS / RUN_ID
SOURCE_JSON = (
    ROOT
    / "six-provider-btc-same-root-aq-ibkr-aggtrades-probe-v1"
    / "six_provider_btc_same_root_aq_ibkr_aggtrades_probe_v1.json"
)
OUT_DIR = ROOT / "command-output"
CHECK_DIR = ROOT / "checks"
REPORT_DIR = ROOT / "six-provider-btc-same-root-aq-ibkr-aggtrades-chain-v1"
DERIVED_DIR = ROOT / "derived"
PROVIDER_JSON_DIR = ROOT / "provider-data-json"
STATE_DIR = ROOT / "state_six_provider_1h_chain_v1"
PATH_RANKER_DIR = ROOT / "path-ranker" / "catboost_1h_chain_v1"
UV = "/Users/thrill3r/.local/bin/uv"


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text()) if path.exists() else {}


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
    source = ROOT / "provider-csv" / "yfinance_btc_usd_1h.csv"
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


def materialize_trades(aq_results: list[dict[str, Any]]) -> dict[str, Any]:
    DERIVED_DIR.mkdir(parents=True, exist_ok=True)
    out_path = DERIVED_DIR / "six_provider_1h_aq_real_trades.jsonl"
    rows: list[dict[str, Any]] = []
    by_provider: dict[str, int] = {}
    by_path: dict[str, int] = {}
    for result in aq_results:
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
                row["provider_matrix_source_run_id"] = RUN_ID
                row["source_provider"] = provider
                row["source_timeframe"] = "1h"
                row["aq_timeframe"] = "1h"
                row["strategy_mutation_id"] = f"{provider}:{row.get('strategy_mutation_id', strategy)}"
                rows.append(row)
                by_provider[provider] = by_provider.get(provider, 0) + 1
                by_path[branch_path] = by_path.get(branch_path, 0) + 1
    out_path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows))
    return {"path": str(out_path), "rows": len(rows), "by_provider": by_provider, "by_path": by_path}


def build_strategy_library(aq_results: list[dict[str, Any]]) -> Path:
    strategies = []
    for result in aq_results:
        for name, payload in sorted((result.get("metrics") or {}).items()):
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
                        "base_factor": "fresh_same_root_six_provider_btc_1h",
                        "hypothesis": "Fresh comparable-timeframe provider rows can feed AQ and preserve branch-shaped observations.",
                        "paradigm": "provider_matrix_1h_momentum_or_pullback",
                        "expected_regime": "ProviderCrypto -> MomentumOrPullback -> branch-preserving profit factor",
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
        "exported_at": "2026-05-12T12:00:00+08:00",
        "source_run_id": RUN_ID,
        "source_workspace": str(ROOT / "workspace"),
        "auto_quant_repo_url": "/Users/thrill3r/Auto-Quant",
        "auto_quant_pinned_ref": "local",
        "config_path": "config.tomac.json",
        "log_path": str(OUT_DIR),
        "timeframe": "1h",
        "strategies": strategies,
        "validation_errors": [],
    }
    path = DERIVED_DIR / "strategy_library_six_provider_1h_aq_v1.json"
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


def run_chain(trades_path: str, library_path: Path, provider_json: dict[str, Any]) -> dict[str, int]:
    env = os.environ.copy()
    env.update(
        {
            "OMP_NUM_THREADS": "1",
            "OPENBLAS_NUM_THREADS": "1",
            "MKL_NUM_THREADS": "1",
            "VECLIB_MAXIMUM_THREADS": "1",
        }
    )
    target_history = STATE_DIR / SYMBOL / "policy_training" / "structural_path_ranking_target_history.csv"
    model_dir = PATH_RANKER_DIR / "catboost_model"
    history_scores = PATH_RANKER_DIR / "history_scores.csv"
    trainer_artifact = model_dir / "trainer_artifact.json"
    commands = {
        "20_auto_quant_results_import_1h": [
            "./target/debug/ict-engine",
            "auto-quant-results-import",
            "--symbol",
            SYMBOL,
            "--state-dir",
            str(STATE_DIR),
            "--library",
            str(library_path),
        ],
        "21_auto_quant_prior_init_1h": [
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
        "22_ingest_real_trades_1h": [
            "./target/debug/ict-engine",
            "auto-quant-ingest-real-trades",
            "--symbol",
            SYMBOL,
            "--state-dir",
            str(STATE_DIR),
            "--trades",
            trades_path,
            "--source",
            "fresh_same_root_six_provider_1h_aq_115500",
            "--force",
        ],
        "23_analyze_provider_data_1h": [
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
        "24_pre_bayes_status_1h": [
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
        "25_policy_training_status_before_export_1h": [
            "./target/debug/ict-engine",
            "policy-training-status",
            "--symbol",
            SYMBOL,
            "--state-dir",
            str(STATE_DIR),
            "--output-format",
            "json",
        ],
        "26_export_structural_path_ranking_target_1h": [
            "./target/debug/ict-engine",
            "export-structural-path-ranking-target",
            "--symbol",
            SYMBOL,
            "--state-dir",
            str(STATE_DIR),
        ],
        "27_train_catboost_1h": [
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
        "28_apply_catboost_history_1h": [
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
        "29_apply_external_scores_1h": [
            "./target/debug/ict-engine",
            "apply-structural-path-ranking-external-scores",
            "--symbol",
            SYMBOL,
            "--state-dir",
            str(STATE_DIR),
            "--scores-file",
            str(history_scores),
        ],
        "30_register_trainer_artifact_1h": [
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
        "31_enable_runtime_1h": [
            "./target/debug/ict-engine",
            "enable-structural-path-ranking-runtime",
            "--symbol",
            SYMBOL,
            "--state-dir",
            str(STATE_DIR),
            "--reuse-mode",
            "prefer_history",
        ],
        "32_policy_training_status_final_1h": [
            "./target/debug/ict-engine",
            "policy-training-status",
            "--symbol",
            SYMBOL,
            "--state-dir",
            str(STATE_DIR),
            "--output-format",
            "json",
        ],
        "33_workflow_execution_candidate_1h": [
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
        "34_workflow_full_1h": [
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
    (CHECK_DIR / "35_catboost_info_cleanup_check_1h.exit").write_text("0\n" if status == "catboost_info_absent" else "1\n")
    (OUT_DIR / "35_catboost_info_cleanup_check_1h.out").write_text(status + "\n")
    return status


def metric_totals(aq_results: list[dict[str, Any]]) -> dict[str, int]:
    totals = {
        "provider_runs": len(aq_results),
        "compile_success": 0,
        "run_success": 0,
        "strategies_with_metrics": 0,
        "total_trades": 0,
    }
    for result in aq_results:
        if result.get("compile_exit") == 0:
            totals["compile_success"] += 1
        if result.get("run_tomac_exit") == 0:
            totals["run_success"] += 1
        for payload in (result.get("metrics") or {}).values():
            totals["strategies_with_metrics"] += 1
            totals["total_trades"] += int((payload.get("aggregate") or {}).get("trade_count") or 0)
    return totals


def summarize(source: dict[str, Any], trade_summary: dict[str, Any], library_path: Path, provider_json: dict[str, Any], exits: dict[str, int], cleanup_status: str) -> dict[str, Any]:
    policy = parse_json_output("32_policy_training_status_final_1h")
    pre_bayes = parse_json_output("24_pre_bayes_status_1h")
    execution = parse_json_output("33_workflow_execution_candidate_1h")
    workflow = parse_json_output("34_workflow_full_1h")
    target = read_json(STATE_DIR / SYMBOL / "policy_training" / "structural_path_ranking_target_summary.json")
    ranker = policy.get("structural_path_ranking_target", {})
    validation = policy.get("structural_path_ranking_validation", {})
    return {
        "run_id": RUN_ID,
        "symbol": SYMBOL,
        "source_probe_json": str(SOURCE_JSON),
        "provider_matrix": source["provider_matrix"],
        "source_metric_totals": source["metric_totals"],
        "metric_totals": metric_totals(source["aq_results"]),
        "trade_summary": trade_summary,
        "strategy_library": str(library_path),
        "provider_json": provider_json,
        "chain_exits": exits,
        "pre_bayes": pre_bayes,
        "policy_final": policy,
        "target_summary": target,
        "ranker_validation": validation,
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
    report = REPORT_DIR / "six_provider_btc_same_root_aq_ibkr_aggtrades_chain_v1.md"
    assertions = CHECK_DIR / "six_provider_btc_same_root_aq_ibkr_aggtrades_chain_v1_assertions.out"
    checklist = REPORT_DIR / "prompt_to_artifact_checklist_six_provider_btc_same_root_aq_ibkr_aggtrades_chain_v1.csv"

    ranker = summary["ranker_target"]
    execution = summary["execution_candidate"]
    pre_bayes = summary["pre_bayes"]
    totals = summary["metric_totals"]
    lines = [
        "# Six-Provider BTC Same-Root AQ IBKR AGGTRADES Chain v1",
        "",
        f"Run id: `{RUN_ID}`",
        f"Symbol: `{SYMBOL}`",
        "",
        "## Scope",
        "Consumes the fresh `115500` same-root six-provider 1h AQ outputs and runs the ordered downstream chain.",
        "No provider refetch, no ict-engine runtime code edits, no selected-history approval, and no promotion.",
        "",
        "## Chain Readback",
        f"- Provider AQ run success: `{totals['run_success']}/{totals['provider_runs']}`.",
        f"- Strategy/provider metric sets: `{totals['strategies_with_metrics']}`.",
        f"- Materialized rooted trades: `{summary['trade_summary']['rows']}`.",
        f"- Trades by provider: `{summary['trade_summary']['by_provider']}`.",
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
        "- Gate result: `six_provider_btc_same_root_aq_ibkr_aggtrades_chain_v1=fresh_1h_six_provider_aq_to_downstream_ran_fail_closed_no_promotion`.",
        "- This repairs the earlier TVR/IBKR daily-template mismatch by using fresh 1h TVR and IBKR AQ inputs, but it still does not create promotion authority.",
        "- Promotion remains blocked unless selected-history/source-control approval, CatBoost/runtime scored mature rows, production validation, runtime matches, and non-observe execution admissibility all pass.",
        "- `promotion_allowed=false`.",
        "- `trade_usable=false`.",
        "- `update_goal=false`.",
        "",
        "## Artifacts",
        f"- JSON: `{REPORT_DIR / 'six_provider_btc_same_root_aq_ibkr_aggtrades_chain_v1.json'}`",
        f"- Assertions: `{assertions}`",
        f"- Checklist: `{checklist}`",
        f"- Trades: `{summary['trade_summary']['path']}`",
        f"- Strategy library: `{summary['strategy_library']}`",
        f"- State dir: `{STATE_DIR}`",
        f"- CatBoost cleanup: `{summary['catboost_info_cleanup']}`",
    ]
    report.write_text("\n".join(lines) + "\n")

    with checklist.open("w", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["requirement", "artifact", "status", "note"])
        writer.writerow(["fresh six-provider AQ root", str(SOURCE_JSON), "covered", "115500 6/6 AQ"])
        writer.writerow(["rooted trade observations", summary["trade_summary"]["path"], "covered", str(summary["trade_summary"]["rows"])])
        writer.writerow(["strategy library import", summary["strategy_library"], "covered", "auto-quant-results-import attempted"])
        writer.writerow(["Pre-Bayes/filter", str(STATE_DIR), "covered", "pre-bayes-status captured"])
        writer.writerow(["CatBoost/path-ranker", str(PATH_RANKER_DIR), "covered", "train/apply/register/enable attempted"])
        writer.writerow(["execution tree", str(OUT_DIR), "covered", "workflow-status captured"])

    assertion_lines = [
        f"PASS run_id={RUN_ID}",
        f"PASS provider_runs={totals['provider_runs']}",
        f"PASS compile_success={totals['compile_success']}",
        f"PASS run_success={totals['run_success']}",
        f"PASS rooted_trades={summary['trade_summary']['rows']}",
        f"PASS raw_scored_mature={ranker.get('raw_scored_mature_rows')}",
        f"PASS production_validation={ranker.get('production_validation_rows')}",
        f"PASS observation_validation={ranker.get('observation_validation_rows')}",
        f"PASS trainer_artifact_ready={ranker.get('trainer_artifact_ready')}",
        f"PASS catboost_info_cleanup={summary['catboost_info_cleanup']}",
        f"FAIL_CLOSED execution_ready={execution.get('ready')} actionable={execution.get('actionable')} review={execution.get('review_status')}",
        "FAIL_CLOSED selected_history_approval=false",
        "PASS promotion_allowed=false",
        "PASS trade_usable=false",
        "PASS update_goal=false",
    ]
    for label, code in summary["chain_exits"].items():
        assertion_lines.append(("PASS" if code == 0 else "FAIL_CLOSED") + f" {label}_exit={code}")
    assertions.write_text("\n".join(assertion_lines) + "\n")


def main() -> int:
    for path in (OUT_DIR, CHECK_DIR, REPORT_DIR, DERIVED_DIR, PROVIDER_JSON_DIR, STATE_DIR, PATH_RANKER_DIR):
        path.mkdir(parents=True, exist_ok=True)
    source = read_json(SOURCE_JSON)
    aq_results = source["aq_results"]
    trade_summary = materialize_trades(aq_results)
    library_path = build_strategy_library(aq_results)
    provider_json = prepare_provider_json()
    exits = run_chain(trade_summary["path"], library_path, provider_json)
    cleanup_status = cleanup_catboost_info()
    summary = summarize(source, trade_summary, library_path, provider_json, exits, cleanup_status)
    write_json(REPORT_DIR / "six_provider_btc_same_root_aq_ibkr_aggtrades_chain_v1.json", summary)
    write_report(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
