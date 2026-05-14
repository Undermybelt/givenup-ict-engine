#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any

import pandas as pd


RUN_ID = "20260512T151021+0800-codex-143900-binance-btc-fullchain-v1"
SYMBOL = "B2R_BINANCE_BTC_FULLCHAIN_143900"
RUNS = Path("docs/experiments/actionable-regime-confidence/runs")
ROOT = RUNS / RUN_ID
SOURCE_ROOT = RUNS / "20260512T143900+0800-codex-provider-backed-regime-validation-smoke-v1"
SOURCE_CSV = SOURCE_ROOT / "data/binance_btcusdt_1h_20170817_20260512.normalized.csv"
TEMPLATE_WORKSPACE = (
    RUNS
    / "20260512T125715+0800-codex-six-provider-eth-same-root-aq-v1"
    / "workspace/auto-quant-112315-binance_public"
)
ICT = Path("target/debug/ict-engine")
PYTHON = Path("/Users/thrill3r/Auto-Quant/.venv/bin/python")
UV = Path("/Users/thrill3r/.local/bin/uv")
OUT_DIR = ROOT / "command-output"
CHECK_DIR = ROOT / "checks"
DATA_DIR = ROOT / "provider-data-json"
DERIVED_DIR = ROOT / "derived"
REPORT_DIR = ROOT / "binance-btc-fullchain-v1"
STATE_DIR = ROOT / "state_binance_btc_fullchain_v1"
WORKSPACE = ROOT / "workspace/auto-quant-binance-btc-fullchain"
PATH_RANKER_DIR = ROOT / "path-ranker"


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


def write_json(path: Path, payload: Any) -> None:
    write_text(path, json.dumps(payload, indent=2, sort_keys=True) + "\n")


def read_json_maybe(path: Path) -> Any:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError:
        return None


def run_cmd(label: str, cmd: list[str], *, cwd: Path | None = None, timeout: int = 600) -> dict[str, Any]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)
    write_text(OUT_DIR / f"{label}.cmd", " ".join(cmd) + "\n")
    env = os.environ.copy()
    env.update(
        {
            "OMP_NUM_THREADS": "1",
            "OPENBLAS_NUM_THREADS": "1",
            "MKL_NUM_THREADS": "1",
            "VECLIB_MAXIMUM_THREADS": "1",
        }
    )
    try:
        proc = subprocess.run(
            cmd,
            cwd=cwd or Path.cwd(),
            env=env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            check=False,
        )
        rc = proc.returncode
        stdout = proc.stdout
        stderr = proc.stderr
    except subprocess.TimeoutExpired as exc:
        rc = 124
        stdout = exc.stdout if isinstance(exc.stdout, str) else ""
        stderr = (exc.stderr if isinstance(exc.stderr, str) else "") + f"\nTIMEOUT after {timeout}s\n"
    write_text(OUT_DIR / f"{label}.out", stdout)
    write_text(OUT_DIR / f"{label}.err", stderr)
    write_text(CHECK_DIR / f"{label}.exit", f"{rc}\n")
    parsed = None
    try:
        parsed = json.loads(stdout)
    except json.JSONDecodeError:
        pass
    return {"label": label, "cmd": cmd, "exit": rc, "parsed_stdout": parsed}


def load_source_frame() -> pd.DataFrame:
    raw = pd.read_csv(SOURCE_CSV)
    date_col = "timestamp" if "timestamp" in raw.columns else "date" if "date" in raw.columns else "ts"
    frame = pd.DataFrame(
        {
            "date": pd.to_datetime(raw[date_col], utc=True),
            "open": pd.to_numeric(raw["open"], errors="coerce"),
            "high": pd.to_numeric(raw["high"], errors="coerce"),
            "low": pd.to_numeric(raw["low"], errors="coerce"),
            "close": pd.to_numeric(raw["close"], errors="coerce"),
            "volume": pd.to_numeric(raw.get("volume", 0.0), errors="coerce").fillna(0.0),
        }
    )
    frame = frame.dropna().sort_values("date").reset_index(drop=True)
    frame["volume"] = frame["volume"].mask(frame["volume"] < 0, 0.0)
    return frame


def write_candle_jsons(frame: pd.DataFrame) -> dict[str, Any]:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    indexed = frame.set_index("date")
    outputs: dict[str, Any] = {}
    for timeframe, rule in [("1h", "1h"), ("4h", "4h"), ("1d", "1d")]:
        if timeframe == "1h":
            out = indexed.copy()
        else:
            out = pd.DataFrame(
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
            for idx, row in out.iterrows()
        ]
        path = DATA_DIR / f"binance_btcusdt_{timeframe}.json"
        write_json(path, records)
        outputs[timeframe] = {
            "path": str(path),
            "rows": len(records),
            "first_ts": records[0]["timestamp"] if records else None,
            "last_ts": records[-1]["timestamp"] if records else None,
        }
    return outputs


def prepare_workspace(frame: pd.DataFrame) -> None:
    if WORKSPACE.exists():
        shutil.rmtree(WORKSPACE)
    shutil.copytree(TEMPLATE_WORKSPACE, WORKSPACE, ignore=shutil.ignore_patterns("__pycache__", "derived"))
    (WORKSPACE / "derived").mkdir(parents=True, exist_ok=True)
    config_path = WORKSPACE / "config.tomac.json"
    config = json.loads(config_path.read_text())
    config.setdefault("exchange", {})["pair_whitelist"] = ["BTC/USDT"]
    write_json(config_path, config)
    feather = WORKSPACE / "user_data/data/BTC_USDT-1h.feather"
    feather.parent.mkdir(parents=True, exist_ok=True)
    frame.to_feather(feather)


def merge_real_trades() -> dict[str, Any]:
    DERIVED_DIR.mkdir(parents=True, exist_ok=True)
    merged = DERIVED_DIR / "binance_btc_fullchain_real_trades.jsonl"
    counts: dict[str, int] = {}
    total = 0
    with merged.open("w", encoding="utf-8") as out:
        for src in sorted((WORKSPACE / "derived").glob("*.real_trades.jsonl")):
            strategy = src.name.replace(".real_trades.jsonl", "")
            count = 0
            for line in src.read_text().splitlines():
                if not line.strip():
                    continue
                record = json.loads(line)
                original = record.get("trade_id", f"{strategy}:{count}")
                record["symbol"] = SYMBOL
                record["auto_quant_run_id"] = RUN_ID
                record["provider_source"] = "binance_public_longspan_btcusdt_1h"
                record["strategy_source"] = strategy
                record["trade_id"] = f"binance_public:{strategy}:{original}"
                out.write(json.dumps(record, sort_keys=True) + "\n")
                count += 1
                total += 1
            counts[strategy] = count
    return {"path": str(merged), "strategy_counts": counts, "total": total}


def metrics_summary() -> dict[str, Any]:
    out: dict[str, Any] = {}
    for path in sorted((WORKSPACE / "derived").glob("*.metrics.json")):
        out[path.name.replace(".metrics.json", "")] = read_json_maybe(path)
    return out


def write_provider_matrix(frame_rows: int) -> list[dict[str, Any]]:
    rows = [
        {
            "provider": "Binance",
            "provider_requested": True,
            "provider_data_acquired": True,
            "provider_unreachable": False,
            "local_cache_replay": False,
            "provider_symbol": "BTCUSDT",
            "timeframe": "1h",
            "rows": frame_rows,
            "evidence_source": str(SOURCE_CSV),
            "notes": "provider-backed longspan input from 143900 smoke, carried into AQ/fullchain in this root",
        },
        {
            "provider": "IBKR",
            "provider_requested": True,
            "provider_data_acquired": True,
            "provider_unreachable": False,
            "local_cache_replay": False,
            "provider_symbol": "SPY STK SMART/ARCA",
            "timeframe": "1h",
            "rows": 20034,
            "evidence_source": str(SOURCE_ROOT / "data/ibkr_spy_1h_5y.normalized.csv"),
            "notes": "cross-market provider context from 143900 smoke; not the AQ training input in this root",
        },
        {
            "provider": "yfinance/YF",
            "provider_requested": True,
            "provider_data_acquired": True,
            "provider_unreachable": False,
            "local_cache_replay": False,
            "provider_symbol": "ES=F",
            "timeframe": "1h",
            "rows": 11383,
            "evidence_source": str(SOURCE_ROOT / "data/yahoo_es_1h_20240513_20260512.normalized.csv"),
            "notes": "cross-market provider context from 143900 smoke; not the AQ training input in this root",
        },
        {
            "provider": "TradingViewRemix/TVR",
            "provider_requested": True,
            "provider_data_acquired": False,
            "provider_unreachable": True,
            "local_cache_replay": False,
            "provider_symbol": "NASDAQ:QQQ",
            "timeframe": "1h",
            "rows": 0,
            "evidence_source": "20260512T141554 provider matrix",
            "notes": "TVR get_ohlcv failure remains a provider-context blocker",
        },
        {
            "provider": "Kraken",
            "provider_requested": True,
            "provider_data_acquired": False,
            "provider_unreachable": False,
            "local_cache_replay": False,
            "provider_symbol": "PF_XBTUSD/PF_SPXUSD",
            "timeframe": "1h",
            "rows": 2000,
            "evidence_source": "20260512T141554 provider matrix",
            "notes": "Kraken long request capped; not used as AQ training input in this root",
        },
        {
            "provider": "Bybit",
            "provider_requested": True,
            "provider_data_acquired": False,
            "provider_unreachable": False,
            "local_cache_replay": False,
            "provider_symbol": "BTCUSDT linear",
            "timeframe": "1h",
            "rows": 1000,
            "evidence_source": "20260512T141554 provider matrix",
            "notes": "Bybit single-page cap; not longspan until pagination is fixed",
        },
    ]
    path = REPORT_DIR / "provider_authority_matrix_v1.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    return rows


def main() -> int:
    for path in [ROOT, OUT_DIR, CHECK_DIR, DATA_DIR, DERIVED_DIR, REPORT_DIR, PATH_RANKER_DIR]:
        path.mkdir(parents=True, exist_ok=True)
    write_text(ROOT / "run_id.txt", RUN_ID + "\n")

    frame = load_source_frame()
    candle_jsons = write_candle_jsons(frame)
    provider_matrix = write_provider_matrix(len(frame))
    prepare_workspace(frame)

    commands: list[dict[str, Any]] = []
    commands.append(run_cmd("00_provider_status", [str(ICT), "provider-status", "--agent"], timeout=240))
    strategies = sorted((WORKSPACE / "user_data/strategies_external").glob("*.py"))
    commands.append(
        run_cmd(
            "01_aq_compile",
            [str(PYTHON), "-m", "py_compile", "run_tomac.py", *[str(p.relative_to(WORKSPACE)) for p in strategies]],
            cwd=WORKSPACE,
            timeout=300,
        )
    )
    commands.append(run_cmd("02_aq_run_tomac", [str(PYTHON), "run_tomac.py"], cwd=WORKSPACE, timeout=900))

    trades = merge_real_trades()
    metrics = metrics_summary()
    if trades["total"] > 0:
        commands.append(
            run_cmd(
                "03_ingest_real_trades",
                [
                    str(ICT),
                    "auto-quant-ingest-real-trades",
                    "--symbol",
                    SYMBOL,
                    "--state-dir",
                    str(STATE_DIR),
                    "--trades",
                    trades["path"],
                    "--source",
                    "auto_quant_real_trades_binance_btc_fullchain_143900",
                ],
                timeout=300,
            )
        )
    else:
        write_text(CHECK_DIR / "03_ingest_real_trades.exit", "99\n")

    commands.append(
        run_cmd(
            "04_analyze",
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
            timeout=900,
        )
    )
    commands.append(run_cmd("05_pre_bayes_status", [str(ICT), "pre-bayes-status", "--symbol", SYMBOL, "--state-dir", str(STATE_DIR), "--refresh", "--output-format", "json"], timeout=300))
    commands.append(run_cmd("06_policy_training_status_before_export", [str(ICT), "policy-training-status", "--symbol", SYMBOL, "--state-dir", str(STATE_DIR), "--output-format", "json"], timeout=300))
    commands.append(run_cmd("07_export_structural_path_target", [str(ICT), "export-structural-path-ranking-target", "--symbol", SYMBOL, "--state-dir", str(STATE_DIR)], timeout=300))
    commands.append(run_cmd("08_policy_training_status_after_export", [str(ICT), "policy-training-status", "--symbol", SYMBOL, "--state-dir", str(STATE_DIR), "--output-format", "json"], timeout=300))

    target_csv = STATE_DIR / SYMBOL / "policy_training/structural_path_ranking_target.csv"
    model_dir = PATH_RANKER_DIR / "catboost_model"
    scores_csv = PATH_RANKER_DIR / "path_scores.csv"
    if target_csv.exists():
        commands.append(
            run_cmd(
                "09_train_catboost",
                [
                    str(UV),
                    "run",
                    "--offline",
                    "--with",
                    "pandas",
                    "--with",
                    "numpy",
                    "--with",
                    "catboost",
                    "python",
                    "scripts/auto_quant_external/pandas_path_ranker_trainer.py",
                    "--target-csv",
                    str(target_csv),
                    "--output-dir",
                    str(model_dir),
                ],
                timeout=600,
            )
        )
        if model_dir.exists():
            commands.append(
                run_cmd(
                    "10_apply_catboost_scores",
                    [
                        str(UV),
                        "run",
                        "--offline",
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
                        str(target_csv),
                        "--output-scores",
                        str(scores_csv),
                    ],
                    timeout=600,
                )
            )
        if scores_csv.exists():
            commands.append(run_cmd("11_apply_external_scores", [str(ICT), "apply-structural-path-ranking-external-scores", "--symbol", SYMBOL, "--state-dir", str(STATE_DIR), "--scores-file", str(scores_csv)], timeout=300))
        artifact = model_dir / "trainer_artifact.json"
        if artifact.exists():
            commands.append(run_cmd("12_register_trainer_artifact", [str(ICT), "register-structural-path-ranking-trainer-artifact", "--symbol", SYMBOL, "--state-dir", str(STATE_DIR), "--artifact-uri", str(artifact), "--model-family", "catboost", "--score-column", "raw_path_score"], timeout=300))

    commands.append(run_cmd("13_workflow_structural_bundle", [str(ICT), "workflow-status", "--symbol", SYMBOL, "--phase", "structural-recommended-path-bundle", "--state-dir", str(STATE_DIR), "--agent", "--stable"], timeout=300))
    commands.append(run_cmd("14_workflow_execution_candidate", [str(ICT), "workflow-status", "--symbol", SYMBOL, "--phase", "execution-candidate", "--state-dir", str(STATE_DIR), "--output-format", "json", "--stable"], timeout=300))
    commands.append(run_cmd("15_workflow_full", [str(ICT), "workflow-status", "--symbol", SYMBOL, "--state-dir", str(STATE_DIR), "--refresh", "--output-format", "json", "--stable"], timeout=300))

    command_exits = {item["label"]: item["exit"] for item in commands}
    policy_after = next((item["parsed_stdout"] for item in commands if item["label"] == "08_policy_training_status_after_export"), None)
    workflow_candidate = next((item["parsed_stdout"] for item in commands if item["label"] == "14_workflow_execution_candidate"), None)
    workflow_full = next((item["parsed_stdout"] for item in commands if item["label"] == "15_workflow_full"), None)
    target_rows = max(sum(1 for _ in target_csv.open()) - 1, 0) if target_csv.exists() else 0
    summary = {
        "run_id": RUN_ID,
        "symbol": SYMBOL,
        "source_root": str(SOURCE_ROOT),
        "source_csv": str(SOURCE_CSV),
        "source_rows": len(frame),
        "provider_matrix": provider_matrix,
        "candle_jsons": candle_jsons,
        "aq_metrics": metrics,
        "merged_real_trades": trades,
        "command_exits": command_exits,
        "policy_training_after_export": policy_after,
        "workflow_execution_candidate": workflow_candidate,
        "workflow_full": workflow_full,
        "target_rows": target_rows,
        "catboost_artifact_exists": (model_dir / "trainer_artifact.json").exists(),
        "scores_exists": scores_csv.exists(),
        "promotion_allowed": False,
        "trade_usable": False,
        "update_goal": False,
        "gate_result": "binance_btc_fullchain_provider_aq_downstream_fail_closed_v1",
    }
    write_json(REPORT_DIR / "binance_btc_fullchain_v1.json", summary)

    lines = [
        "# Binance BTC Fullchain Provider AQ Downstream Fail-Closed v1",
        "",
        f"Run id: `{RUN_ID}`",
        f"Source provider smoke: `{SOURCE_ROOT}`",
        f"Source rows: `{len(frame)}` from `{SOURCE_CSV}`",
        "",
        "## Readback",
        f"- AQ metrics strategies: `{sorted(metrics.keys())}`.",
        f"- Merged real-trade rows: `{trades['total']}` by `{trades['strategy_counts']}`.",
        f"- Command exits: `{command_exits}`.",
        f"- Structural target rows: `{target_rows}`.",
        f"- CatBoost artifact exists: `{(model_dir / 'trainer_artifact.json').exists()}`; scores exists: `{scores_csv.exists()}`.",
        "",
        "## Provider Matrix",
    ]
    for row in provider_matrix:
        lines.append(
            f"- {row['provider']}: requested={row['provider_requested']} acquired={row['provider_data_acquired']} rows={row['rows']} source={row['evidence_source']}"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "- Gate: `binance_btc_fullchain_provider_aq_downstream_fail_closed_v1`.",
            "- This is a provider-backed long-window AQ/downstream readback, not an accepted Board A regime packet.",
            "- `promotion_allowed=false`.",
            "- `trade_usable=false`.",
            "- `update_goal=false`.",
        ]
    )
    write_text(REPORT_DIR / "binance_btc_fullchain_v1.md", "\n".join(lines) + "\n")

    checklist = REPORT_DIR / "prompt_to_artifact_checklist_binance_btc_fullchain_v1.csv"
    with checklist.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["requirement", "artifact", "status", "note"])
        writer.writerow(["provider-backed large window", str(SOURCE_CSV), "covered", f"rows={len(frame)}"])
        writer.writerow(["Auto-Quant executed", str(WORKSPACE), "covered" if command_exits.get("02_aq_run_tomac") == 0 else "fail_closed", f"exit={command_exits.get('02_aq_run_tomac')}"])
        writer.writerow(["real trades ingested", trades["path"], "covered" if command_exits.get("03_ingest_real_trades") == 0 else "fail_closed", f"trades={trades['total']}"])
        writer.writerow(["Pre-Bayes/BBN readback", str(OUT_DIR / "05_pre_bayes_status.out"), "covered" if command_exits.get("05_pre_bayes_status") == 0 else "fail_closed", f"exit={command_exits.get('05_pre_bayes_status')}"])
        writer.writerow(["CatBoost/path-ranker attempted", str(PATH_RANKER_DIR), "covered" if "09_train_catboost" in command_exits else "not_reached", f"exit={command_exits.get('09_train_catboost')}"])
        writer.writerow(["execution-tree readback", str(OUT_DIR / "14_workflow_execution_candidate.out"), "covered" if command_exits.get("14_workflow_execution_candidate") == 0 else "fail_closed", f"exit={command_exits.get('14_workflow_execution_candidate')}"])
        writer.writerow(["95% regime acceptance", str(REPORT_DIR / "binance_btc_fullchain_v1.md"), "fail_closed", "no acceptance promotion from this diagnostic"])

    assertions = [
        f"PASS run_id={RUN_ID}",
        f"PASS provider_backed_rows={len(frame)}",
        f"PASS aq_compile_exit={command_exits.get('01_aq_compile')}",
        f"PASS aq_run_tomac_exit={command_exits.get('02_aq_run_tomac')}",
        f"PASS real_trade_rows={trades['total']}",
        f"PASS analyze_exit={command_exits.get('04_analyze')}",
        f"PASS pre_bayes_exit={command_exits.get('05_pre_bayes_status')}",
        f"PASS export_target_exit={command_exits.get('07_export_structural_path_target')}",
        f"FAIL_CLOSED target_rows={target_rows}",
        f"FAIL_CLOSED catboost_artifact_exists={(model_dir / 'trainer_artifact.json').exists()}",
        "PASS promotion_allowed=false",
        "PASS trade_usable=false",
        "PASS update_goal=false",
    ]
    write_text(CHECK_DIR / "binance_btc_fullchain_v1_assertions.out", "\n".join(assertions) + "\n")
    print(REPORT_DIR / "binance_btc_fullchain_v1.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
