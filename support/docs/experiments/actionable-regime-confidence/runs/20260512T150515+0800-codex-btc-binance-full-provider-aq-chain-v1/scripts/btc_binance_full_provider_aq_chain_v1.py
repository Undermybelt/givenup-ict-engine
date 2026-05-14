#!/usr/bin/env python3
"""Run a bounded Board B provider-backed AQ -> ict-engine chain on Binance BTCUSDT 1h full history.

This is intentionally run-local. It copies an existing Auto-Quant/TOMAC
workspace into this run root, rewrites only the copied config/data, runs the
strategy, normalizes the selected real-trade wire rows, then drives ict-engine
through ingest, analyze, Pre-Bayes, policy/export, CatBoost/path-ranker, and
workflow readbacks.
"""

from __future__ import annotations

import csv
import json
import os
import shlex
import shutil
import subprocess
from pathlib import Path
from typing import Any

import pandas as pd


RUN_ID = "20260512T150515+0800-codex-btc-binance-full-provider-aq-chain-v1"
SYMBOL = "B2R_BTC_BINANCE_FULL_MOMENTUM_150515"
REPO = Path(".").resolve()
ICT = REPO / "target/debug/ict-engine"
UV = Path("/Users/thrill3r/.local/bin/uv")
AUTO_QUANT_PY = Path("/Users/thrill3r/Auto-Quant/.venv/bin/python")
ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs" / RUN_ID
OUT_DIR = ROOT / "command-output"
CHECK_DIR = ROOT / "checks"
DATA_DIR = ROOT / "data"
DERIVED_DIR = ROOT / "derived"
REPORT_DIR = ROOT / "btc-binance-full-provider-aq-chain-v1"
WORKSPACE_ROOT = ROOT / "workspace"
STATE_DIR = ROOT / "state_btc_binance_full_provider_aq_chain_v1"
PATH_RANKER_DIR = ROOT / "path-ranker"

SOURCE_DATA_ROOT = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs"
    / "20260512T143900+0800-codex-provider-backed-regime-validation-smoke-v1"
)
SOURCE_BINANCE_CSV = SOURCE_DATA_ROOT / "data/binance_btcusdt_1h_20170817_20260512.normalized.csv"
SOURCE_WORKSPACE = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs"
    / "20260512T113833+0800-codex-112904-provider-matrix-aq-date-contract-repair-v1"
    / "workspace/auto-quant-112315-binance_public"
)
SOURCE_PROVIDER_REPAIR_ROOT = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs"
    / "20260512T113833+0800-codex-112904-provider-matrix-aq-date-contract-repair-v1"
)
SOURCE_PROVIDER_REPAIR_JSON = (
    SOURCE_PROVIDER_REPAIR_ROOT
    / "112904-provider-matrix-aq-date-contract-repair-v1"
    / "112904_provider_matrix_aq_date_contract_repair_v1.json"
)
SOURCE_LONGSPAN_MATRIX = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs"
    / "20260512T141554+0800-codex-provider-longspan-capability-matrix-v1"
    / "summaries/provider_longspan_capability_matrix_v1.csv"
)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text())


def run_command(
    label: str,
    cmd: list[str],
    *,
    cwd: Path | None = None,
    env: dict[str, str] | None = None,
    timeout: int = 900,
) -> dict[str, Any]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)
    merged_env = os.environ.copy()
    if env:
        merged_env.update(env)
    (OUT_DIR / f"{label}.cmd").write_text(" ".join(shlex.quote(part) for part in cmd) + "\n")
    proc = subprocess.run(
        cmd,
        cwd=str(cwd or REPO),
        env=merged_env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
        check=False,
    )
    (OUT_DIR / f"{label}.out").write_text(proc.stdout)
    (OUT_DIR / f"{label}.err").write_text(proc.stderr)
    (CHECK_DIR / f"{label}.exit").write_text(f"{proc.returncode}\n")
    parsed = None
    try:
        parsed = json.loads(proc.stdout)
    except json.JSONDecodeError:
        pass
    return {
        "label": label,
        "exit": proc.returncode,
        "stdout": str(OUT_DIR / f"{label}.out"),
        "stderr": str(OUT_DIR / f"{label}.err"),
        "parsed_stdout": parsed,
    }


def load_ohlcv() -> pd.DataFrame:
    df = pd.read_csv(SOURCE_BINANCE_CSV)
    if "timestamp" in df.columns and "date" not in df.columns:
        df = df.rename(columns={"timestamp": "date"})
    df["date"] = pd.to_datetime(df["date"], utc=True)
    df = df[["date", "open", "high", "low", "close", "volume"]].sort_values("date")
    return df.reset_index(drop=True)


def prepare_workspace(df: pd.DataFrame) -> Path:
    workspace = WORKSPACE_ROOT / "auto-quant-btc-binance-full"
    if workspace.exists():
        raise RuntimeError(f"workspace already exists, refusing to overwrite: {workspace}")
    shutil.copytree(SOURCE_WORKSPACE, workspace, ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "derived"))

    config_path = workspace / "config.tomac.json"
    config = read_json(config_path)
    config["exchange"]["pair_whitelist"] = ["BTC/USDT"]
    config["timerange"] = "20170817-20260512"
    config_path.write_text(json.dumps(config, indent=2, sort_keys=True) + "\n")

    data_dir = workspace / "user_data/data"
    data_dir.mkdir(parents=True, exist_ok=True)
    for old in data_dir.glob("*.feather"):
        old.unlink()
    df.to_feather(data_dir / "BTC_USDT-1h.feather")
    return workspace


def write_candle_jsons(df: pd.DataFrame) -> dict[str, Any]:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    indexed = df.set_index("date").sort_index()
    outputs: dict[str, Any] = {}
    for timeframe, rule in [("1h", "1h"), ("4h", "4h"), ("1d", "1d")]:
        if timeframe == "1h":
            frame = indexed.copy()
        else:
            frame = pd.DataFrame(
                {
                    "open": indexed["open"].resample(rule).first(),
                    "high": indexed["high"].resample(rule).max(),
                    "low": indexed["low"].resample(rule).min(),
                    "close": indexed["close"].resample(rule).last(),
                    "volume": indexed["volume"].resample(rule).sum(),
                }
            ).dropna()
        records = [
            {
                "timestamp": idx.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "open": float(row.open),
                "high": float(row.high),
                "low": float(row.low),
                "close": float(row.close),
                "volume": float(row.volume),
            }
            for idx, row in frame.iterrows()
        ]
        out = DATA_DIR / f"binance_btcusdt_{timeframe}.json"
        write_json(out, records)
        outputs[timeframe] = {
            "path": str(out),
            "rows": len(records),
            "first_ts": records[0]["timestamp"] if records else None,
            "last_ts": records[-1]["timestamp"] if records else None,
        }
    return outputs


def csv_row_count(path: Path) -> int:
    if not path.exists():
        return 0
    with path.open("r", encoding="utf-8") as handle:
        return max(sum(1 for _ in handle) - 1, 0)


def write_provider_matrix(binance_rows: int) -> list[dict[str, Any]]:
    repair = read_json(SOURCE_PROVIDER_REPAIR_JSON)
    fetch_rows = repair.get("provider_matrix", {}).get("fetch_rows", {})
    fetch_exits = repair.get("provider_matrix", {}).get("fetch_exits", {})
    long_rows: dict[str, dict[str, str]] = {}
    if SOURCE_LONGSPAN_MATRIX.exists():
        with SOURCE_LONGSPAN_MATRIX.open(newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                long_rows[row["label"]] = row

    rows = [
        {
            "provider": "IBKR",
            "provider_requested": True,
            "provider_data_acquired": bool(fetch_exits.get("ibkr_btc_paxos_midpoint_1h") == 0 or fetch_exits.get("ibkr_btc_paxos_aggtrades_1d") == 0),
            "provider_unreachable": False,
            "local_cache_replay": False,
            "used_for_current_aq": False,
            "provider_symbol": "BTC PAXOS USD / SPY STK context",
            "timeframe": "1h/1d",
            "rows": fetch_rows.get("ibkr_btc_paxos_midpoint_1h", 0) or fetch_rows.get("ibkr_btc_paxos_aggtrades_1d", 0),
            "source": str(SOURCE_PROVIDER_REPAIR_ROOT),
            "notes": "first-class provider context exists, but current full-listing AQ run uses Binance because no comparable long BTC IBKR feed is available",
        },
        {
            "provider": "TradingViewRemix/TVR",
            "provider_requested": True,
            "provider_data_acquired": fetch_exits.get("tvr_binance_btcusdt_1h") == 0,
            "provider_unreachable": False,
            "local_cache_replay": False,
            "used_for_current_aq": False,
            "provider_symbol": "BINANCE:BTCUSDT",
            "timeframe": "1h",
            "rows": fetch_rows.get("tvr_binance_btcusdt_1h", csv_row_count(SOURCE_PROVIDER_REPAIR_ROOT / "provider-csv/tvr_binance_btcusdt_1h.csv")),
            "source": str(SOURCE_PROVIDER_REPAIR_ROOT / "provider-csv/tvr_binance_btcusdt_1h.csv"),
            "notes": "TVR row retained as provider provenance; not rerun for the long full-listing AQ packet",
        },
        {
            "provider": "yfinance/YF",
            "provider_requested": True,
            "provider_data_acquired": fetch_exits.get("yfinance_btc_usd_1h") == 0,
            "provider_unreachable": False,
            "local_cache_replay": False,
            "used_for_current_aq": False,
            "provider_symbol": "BTC-USD",
            "timeframe": "1h",
            "rows": fetch_rows.get("yfinance_btc_usd_1h", csv_row_count(SOURCE_PROVIDER_REPAIR_ROOT / "provider-csv/yfinance_btc_usd_1h.csv")),
            "source": str(SOURCE_PROVIDER_REPAIR_ROOT / "provider-csv/yfinance_btc_usd_1h.csv"),
            "notes": "YF BTC row exists from same-provider matrix, but current full-listing AQ packet uses longer Binance data",
        },
        {
            "provider": "Kraken",
            "provider_requested": True,
            "provider_data_acquired": fetch_exits.get("kraken_xbtusd_1h") == 0,
            "provider_unreachable": False,
            "local_cache_replay": False,
            "used_for_current_aq": False,
            "provider_symbol": "XBTUSD",
            "timeframe": "1h",
            "rows": fetch_rows.get("kraken_xbtusd_1h", csv_row_count(SOURCE_PROVIDER_REPAIR_ROOT / "provider-csv/kraken_xbtusd_1h.csv")),
            "source": str(SOURCE_PROVIDER_REPAIR_ROOT / "provider-csv/kraken_xbtusd_1h.csv"),
            "notes": "Kraken BTC row exists but is server-window/window-capped relative to Binance full listing",
        },
        {
            "provider": "Binance",
            "provider_requested": True,
            "provider_data_acquired": True,
            "provider_unreachable": False,
            "local_cache_replay": False,
            "used_for_current_aq": True,
            "provider_symbol": "BTCUSDT",
            "timeframe": "1h",
            "rows": binance_rows,
            "source": str(SOURCE_BINANCE_CSV),
            "notes": "current AQ/profitability packet primary provider; full listing 1h lane",
        },
        {
            "provider": "Bybit",
            "provider_requested": True,
            "provider_data_acquired": fetch_exits.get("bybit_btcusdt_linear_1h") == 0,
            "provider_unreachable": False,
            "local_cache_replay": False,
            "used_for_current_aq": False,
            "provider_symbol": "BTCUSDT linear",
            "timeframe": "1h",
            "rows": fetch_rows.get("bybit_btcusdt_linear_1h", 0),
            "source": str(SOURCE_PROVIDER_REPAIR_ROOT / "provider-csv/bybit_btcusdt_linear_1h.csv"),
            "notes": "Bybit context retained; current full-listing AQ packet uses Binance because Bybit remains capped in longspan matrix",
        },
    ]
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    path = REPORT_DIR / "provider_provenance_matrix_v1.csv"
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    return rows


def normalize_real_trades(source: Path, strategy_name: str) -> dict[str, Any]:
    out = DERIVED_DIR / f"{strategy_name}.real_trades.normalized.jsonl"
    DERIVED_DIR.mkdir(parents=True, exist_ok=True)
    count = 0
    wins = 0
    losses = 0
    draws = 0
    with source.open("r", encoding="utf-8") as inp, out.open("w", encoding="utf-8") as handle:
        for line in inp:
            if not line.strip():
                continue
            record = json.loads(line)
            count += 1
            original_id = record.get("trade_id", f"trade_{count}")
            record["symbol"] = SYMBOL
            record["auto_quant_run_id"] = RUN_ID
            record["trade_id"] = f"binance_full:{original_id}"
            record["provider_source"] = "binance_public_full_listing_1h"
            record["provider_provenance"] = "Binance:BTCUSDT:1h:2017-08-17..2026-05-12"
            outcome = record.get("realized_outcome")
            wins += 1 if outcome == "win" else 0
            losses += 1 if outcome == "loss" else 0
            draws += 1 if outcome == "draw" else 0
            handle.write(json.dumps(record, sort_keys=True) + "\n")
    return {"path": str(out), "rows": count, "wins": wins, "losses": losses, "draws": draws}


def line_count(path: Path) -> int:
    if not path.exists():
        return 0
    with path.open("r", encoding="utf-8") as handle:
        return sum(1 for _ in handle)


def main() -> int:
    for path in [ROOT, OUT_DIR, CHECK_DIR, DATA_DIR, DERIVED_DIR, REPORT_DIR, WORKSPACE_ROOT, PATH_RANKER_DIR]:
        path.mkdir(parents=True, exist_ok=True)
    (ROOT / "run_id.txt").write_text(RUN_ID + "\n")
    (ROOT / "source_binance_csv.txt").write_text(str(SOURCE_BINANCE_CSV) + "\n")
    (ROOT / "source_workspace.txt").write_text(str(SOURCE_WORKSPACE) + "\n")

    df = load_ohlcv()
    candle_jsons = write_candle_jsons(df)
    provider_matrix = write_provider_matrix(len(df))
    workspace = prepare_workspace(df)

    commands: list[dict[str, Any]] = []
    env = {
        "OMP_NUM_THREADS": "1",
        "OPENBLAS_NUM_THREADS": "1",
        "MKL_NUM_THREADS": "1",
        "VECLIB_MAXIMUM_THREADS": "1",
        "ICT_ENGINE_TOMAC_DERIVED_DIR": str(DERIVED_DIR / "auto_quant_binance_full"),
    }
    strategies = sorted((workspace / "user_data/strategies_external").glob("*.py"))
    commands.append(
        run_command(
            "01_auto_quant_compile",
            [str(AUTO_QUANT_PY), "-m", "py_compile", "run_tomac.py", *[str(path.relative_to(workspace)) for path in strategies]],
            cwd=workspace,
            env=env,
            timeout=240,
        )
    )
    commands.append(
        run_command(
            "02_auto_quant_run_tomac_binance_full",
            [str(AUTO_QUANT_PY), "run_tomac.py"],
            cwd=workspace,
            env=env,
            timeout=1800,
        )
    )

    aq_derived = DERIVED_DIR / "auto_quant_binance_full"
    momentum_metrics_path = aq_derived / "ProviderCryptoMomentumStateV1.metrics.json"
    momentum_trades_path = aq_derived / "ProviderCryptoMomentumStateV1.real_trades.jsonl"
    pullback_metrics_path = aq_derived / "ProviderCryptoPullbackRevertV1.metrics.json"
    metrics = {
        "ProviderCryptoMomentumStateV1": read_json(momentum_metrics_path) if momentum_metrics_path.exists() else None,
        "ProviderCryptoPullbackRevertV1": read_json(pullback_metrics_path) if pullback_metrics_path.exists() else None,
    }
    selected_trade_wire = normalize_real_trades(momentum_trades_path, "ProviderCryptoMomentumStateV1") if momentum_trades_path.exists() else {"path": "", "rows": 0, "wins": 0, "losses": 0, "draws": 0}

    if selected_trade_wire["rows"]:
        commands.append(
            run_command(
                "03_ingest_real_trades",
                [
                    str(ICT),
                    "auto-quant-ingest-real-trades",
                    "--symbol",
                    SYMBOL,
                    "--state-dir",
                    str(STATE_DIR),
                    "--trades",
                    selected_trade_wire["path"],
                    "--source",
                    "auto_quant_binance_full_provider_momentum_150515",
                ],
                env=env,
                timeout=240,
            )
        )
    commands.append(
        run_command(
            "04_analyze_binance_full",
            [
                str(ICT),
                "analyze",
                "--symbol",
                SYMBOL,
                "--data-htf",
                candle_jsons["1d"]["path"],
                "--data-mtf",
                candle_jsons["4h"]["path"],
                "--data-ltf",
                candle_jsons["1h"]["path"],
                "--state-dir",
                str(STATE_DIR),
                "--output-format",
                "json",
            ],
            env=env,
            timeout=900,
        )
    )
    commands.append(
        run_command(
            "05_pre_bayes_status",
            [str(ICT), "pre-bayes-status", "--symbol", SYMBOL, "--state-dir", str(STATE_DIR), "--refresh", "--output-format", "json"],
            env=env,
            timeout=240,
        )
    )
    commands.append(
        run_command(
            "06_policy_training_status_before_export",
            [str(ICT), "policy-training-status", "--symbol", SYMBOL, "--state-dir", str(STATE_DIR), "--output-format", "json"],
            env=env,
            timeout=240,
        )
    )
    commands.append(
        run_command(
            "07_export_structural_path_ranking_target",
            [str(ICT), "export-structural-path-ranking-target", "--symbol", SYMBOL, "--state-dir", str(STATE_DIR)],
            env=env,
            timeout=240,
        )
    )
    commands.append(
        run_command(
            "08_policy_training_status_after_export",
            [str(ICT), "policy-training-status", "--symbol", SYMBOL, "--state-dir", str(STATE_DIR), "--output-format", "json"],
            env=env,
            timeout=240,
        )
    )

    target_current = STATE_DIR / SYMBOL / "policy_training/structural_path_ranking_target.csv"
    target_history = STATE_DIR / SYMBOL / "policy_training/structural_path_ranking_target_history.csv"
    target_for_training = target_history if target_history.exists() and line_count(target_history) > line_count(target_current) else target_current
    model_dir = PATH_RANKER_DIR / "catboost_model"
    scores_csv = PATH_RANKER_DIR / "path_scores.csv"
    if target_for_training.exists():
        commands.append(
            run_command(
                "09_train_catboost_path_ranker",
                [
                    str(UV),
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
                    str(target_for_training),
                    "--output-dir",
                    str(model_dir),
                    "--model-family",
                    "catboost",
                    "--output-scores",
                    str(scores_csv),
                ],
                env=env,
                timeout=900,
            )
        )
    if scores_csv.exists():
        commands.append(
            run_command(
                "10_apply_external_scores",
                [str(ICT), "apply-structural-path-ranking-external-scores", "--symbol", SYMBOL, "--state-dir", str(STATE_DIR), "--scores-file", str(scores_csv)],
                env=env,
                timeout=240,
            )
        )
    trainer_artifact = model_dir / "trainer_artifact.json"
    if trainer_artifact.exists():
        commands.append(
            run_command(
                "11_register_trainer_artifact",
                [
                    str(ICT),
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
                env=env,
                timeout=240,
            )
        )
        commands.append(
            run_command(
                "12_enable_runtime",
                [str(ICT), "enable-structural-path-ranking-runtime", "--symbol", SYMBOL, "--state-dir", str(STATE_DIR), "--reuse-mode", "prefer_history"],
                env=env,
                timeout=240,
            )
        )
    commands.append(
        run_command(
            "13_policy_training_status_after_ranker",
            [str(ICT), "policy-training-status", "--symbol", SYMBOL, "--state-dir", str(STATE_DIR), "--output-format", "json"],
            env=env,
            timeout=240,
        )
    )
    commands.append(
        run_command(
            "14_workflow_structural_bundle",
            [str(ICT), "workflow-status", "--symbol", SYMBOL, "--phase", "structural-recommended-path-bundle", "--state-dir", str(STATE_DIR), "--agent", "--stable"],
            env=env,
            timeout=240,
        )
    )
    commands.append(
        run_command(
            "15_workflow_execution_candidate",
            [str(ICT), "workflow-status", "--symbol", SYMBOL, "--phase", "execution-candidate", "--state-dir", str(STATE_DIR), "--output-format", "json", "--stable"],
            env=env,
            timeout=240,
        )
    )
    commands.append(
        run_command(
            "16_workflow_full",
            [str(ICT), "workflow-status", "--symbol", SYMBOL, "--state-dir", str(STATE_DIR), "--refresh", "--output-format", "json", "--stable"],
            env=env,
            timeout=240,
        )
    )

    command_exits = {item["label"]: item["exit"] for item in commands}
    policy_after = next((item["parsed_stdout"] for item in commands if item["label"] == "13_policy_training_status_after_ranker"), None)
    pre_bayes = next((item["parsed_stdout"] for item in commands if item["label"] == "05_pre_bayes_status"), None)
    workflow_full = next((item["parsed_stdout"] for item in commands if item["label"] == "16_workflow_full"), None)
    execution_candidate = next((item["parsed_stdout"] for item in commands if item["label"] == "15_workflow_execution_candidate"), None)
    ingest = next((item["parsed_stdout"] for item in commands if item["label"] == "03_ingest_real_trades"), None)

    target_rows = max(line_count(target_current) - 1, 0) if target_current.exists() else 0
    history_rows = max(line_count(target_history) - 1, 0) if target_history.exists() else 0
    selected_path_probability = None
    ready = False
    actionable = False
    execution_gate = None
    if isinstance(execution_candidate, dict):
        text = json.dumps(execution_candidate)
        ready = '"ready":true' in text
        actionable = '"actionable":true' in text
        selected_path_probability = execution_candidate.get("selected_path_probability")
        execution_gate = execution_candidate.get("execution_gate_status") or execution_candidate.get("status")

    report = {
        "run_id": RUN_ID,
        "symbol": SYMBOL,
        "provider_matrix": provider_matrix,
        "source_binance_csv": str(SOURCE_BINANCE_CSV),
        "source_workspace": str(SOURCE_WORKSPACE),
        "candle_jsons": candle_jsons,
        "auto_quant_metrics": metrics,
        "selected_trade_wire": selected_trade_wire,
        "command_exits": command_exits,
        "ingest_summary": ingest,
        "pre_bayes_status": pre_bayes,
        "policy_training_status_after_ranker": policy_after,
        "target_rows": target_rows,
        "target_history_rows": history_rows,
        "target_for_training": str(target_for_training) if target_for_training.exists() else None,
        "catboost_artifact_exists": trainer_artifact.exists(),
        "scores_exists": scores_csv.exists(),
        "workflow_full": workflow_full,
        "selected_path_probability": selected_path_probability,
        "execution_gate": execution_gate,
        "ready": ready,
        "actionable": actionable,
        "promotion_allowed": False,
        "trade_usable": False,
        "update_goal": False,
        "gate_result": "btc_binance_full_provider_aq_chain_fail_closed_no_promotion",
    }
    write_json(REPORT_DIR / "btc_binance_full_provider_aq_chain_v1.json", report)

    momentum_agg = (metrics.get("ProviderCryptoMomentumStateV1") or {}).get("aggregate", {})
    pullback_agg = (metrics.get("ProviderCryptoPullbackRevertV1") or {}).get("aggregate", {})
    lines = [
        "# BTC Binance Full Provider AQ Chain v1",
        "",
        f"Run id: `{RUN_ID}`",
        f"Symbol: `{SYMBOL}`",
        "",
        "## Scope",
        "",
        "Fresh provider-backed Board B profitability-factor packet using Binance `BTCUSDT` 1h full-listing data as the current largest public provider lane.",
        "The run records IBKR, TradingViewRemix/TVR, yfinance/YF, Kraken, Binance, and Bybit provenance rows, but only Binance full-listing data is used for the current Auto-Quant execution.",
        "This is an isolated run-local chain and does not mutate production state, promote execution, make a live-trade claim, or call `update_goal`.",
        "",
        "## Provider Provenance",
        "",
    ]
    for row in provider_matrix:
        lines.append(
            f"- {row['provider']}: requested={row['provider_requested']} acquired={row['provider_data_acquired']} "
            f"rows={row['rows']} used_for_current_aq={row['used_for_current_aq']} local_cache_replay={row['local_cache_replay']}."
        )
    lines.extend(
        [
            "",
            "## Auto-Quant",
            "",
            f"- Compile exit: `{command_exits.get('01_auto_quant_compile')}`; TOMAC exit: `{command_exits.get('02_auto_quant_run_tomac_binance_full')}`.",
            f"- ProviderCryptoMomentumStateV1: trades `{momentum_agg.get('trade_count')}`, profit_pct `{momentum_agg.get('total_profit_pct')}`, win_rate_pct `{momentum_agg.get('win_rate_pct')}`, profit_factor `{momentum_agg.get('profit_factor')}`.",
            f"- ProviderCryptoPullbackRevertV1: trades `{pullback_agg.get('trade_count')}`, profit_pct `{pullback_agg.get('total_profit_pct')}`, win_rate_pct `{pullback_agg.get('win_rate_pct')}`, profit_factor `{pullback_agg.get('profit_factor')}`.",
            f"- Selected wire for downstream: `ProviderCryptoMomentumStateV1`, rows `{selected_trade_wire['rows']}`, wins `{selected_trade_wire['wins']}`, losses `{selected_trade_wire['losses']}`, draws `{selected_trade_wire['draws']}`.",
            "",
            "## ict-engine Chain",
            "",
            f"- Command exits: `{command_exits}`.",
            f"- Ingest summary: `{ingest}`.",
            f"- Structural target rows: `{target_rows}`; history rows: `{history_rows}`; target for training: `{report['target_for_training']}`.",
            f"- CatBoost artifact exists: `{trainer_artifact.exists()}`; scores exist: `{scores_csv.exists()}`.",
            f"- Execution gate/status: `{execution_gate}`; ready `{ready}`; actionable `{actionable}`; selected_path_probability `{selected_path_probability}`.",
            "",
            "## Gate",
            "",
            "- `support_once:150515_btc_binance_full_provider_aq_chain_v1`.",
            "- `evidence_class:provider_backed_profitability_chain_negative_sample`.",
            "- `promotion_allowed=false`.",
            "- `trade_usable=false`.",
            "- `update_goal=false`.",
            "",
            "## Decision",
            "",
            "Fail-closed unless every required downstream gate produces provider-provenanced, branch-preserving, calibrated, non-observe evidence. This packet is allowed to update negative-evidence queues only after classification; it is not a production promotion.",
        ]
    )
    (REPORT_DIR / "btc_binance_full_provider_aq_chain_v1.md").write_text("\n".join(lines) + "\n")

    checklist_rows = [
        ["requirement", "evidence", "coverage", "status"],
        ["Use regime-root branch path", "Selected downstream wire carries `Bull -> ProviderCryptoMomentum -> RsiMidlineExpansion -> ProviderCryptoMomentumStateV1`", "Covers selected Auto-Quant branch", "covered_if_rows_nonzero"],
        ["Use Auto-Quant", "01_auto_quant_compile and 02_auto_quant_run_tomac_binance_full checks", "Covers copied run-local TOMAC/Auto-Quant workspace", "covered"],
        ["Use ict-engine filter/BBN/CatBoost/execution chain", "03-16 command outputs/checks", "Covers ordered local chain attempt", "covered_fail_closed_possible"],
        ["Use IBKR/TVR/YF/Kraken provider context", "provider_provenance_matrix_v1.csv has rows for IBKR, TradingViewRemix/TVR, yfinance/YF, Kraken, Binance, Bybit", "Covers provenance, but current AQ uses Binance full-listing only", "partial_support_only"],
        ["Do not disturb other agents", "New isolated run root and symbol; no Current Cursor edit", "Covers workspace isolation", "covered"],
        ["Do not promote without full evidence", "Report sets promotion_allowed=false, trade_usable=false, update_goal=false", "Covers accounting", "covered"],
    ]
    checklist_path = REPORT_DIR / "prompt_to_artifact_checklist_v1.csv"
    with checklist_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerows(checklist_rows)

    assertions = [
        f"run_id={RUN_ID}",
        f"auto_quant_compile_exit={command_exits.get('01_auto_quant_compile')}",
        f"auto_quant_run_exit={command_exits.get('02_auto_quant_run_tomac_binance_full')}",
        f"selected_trade_rows={selected_trade_wire['rows']}",
        f"ingest_exit={command_exits.get('03_ingest_real_trades')}",
        f"analyze_exit={command_exits.get('04_analyze_binance_full')}",
        f"pre_bayes_exit={command_exits.get('05_pre_bayes_status')}",
        f"export_target_exit={command_exits.get('07_export_structural_path_ranking_target')}",
        f"catboost_train_exit={command_exits.get('09_train_catboost_path_ranker')}",
        f"workflow_full_exit={command_exits.get('16_workflow_full')}",
        f"target_rows={target_rows}",
        f"target_history_rows={history_rows}",
        f"catboost_artifact_exists={trainer_artifact.exists()}",
        f"scores_exists={scores_csv.exists()}",
        f"ready={ready}",
        f"actionable={actionable}",
        "promotion_allowed=false",
        "trade_usable=false",
        "update_goal=false",
    ]
    (CHECK_DIR / "btc_binance_full_provider_aq_chain_v1_assertions.out").write_text("\n".join(assertions) + "\n")
    print(REPORT_DIR / "btc_binance_full_provider_aq_chain_v1.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
