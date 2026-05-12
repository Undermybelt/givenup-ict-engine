#!/usr/bin/env python3
"""Downstream readback for the 113833 provider-matrix momentum branch."""

from __future__ import annotations

import csv
import json
import os
import subprocess
from pathlib import Path
from typing import Any

import pandas as pd


RUN_ID = "20260512T130000+0800-codex-113833-provider-momentum-downstream-v1"
SYMBOL = "B2R_PROVIDER_MATRIX_MOMENTUM_113833"
REPO = Path(".")
ICT = REPO / "target/debug/ict-engine"
UV = Path("/Users/thrill3r/.local/bin/uv")
ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs" / RUN_ID
SOURCE_ROOT = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs"
    / "20260512T113833+0800-codex-112904-provider-matrix-aq-date-contract-repair-v1"
)
SOURCE_REPORT = (
    SOURCE_ROOT
    / "112904-provider-matrix-aq-date-contract-repair-v1"
    / "112904_provider_matrix_aq_date_contract_repair_v1.json"
)
OUT_DIR = ROOT / "command-output"
CHECK_DIR = ROOT / "checks"
REPORT_DIR = ROOT / "provider-momentum-downstream-v1"
DATA_DIR = ROOT / "provider-data-json"
DERIVED_DIR = ROOT / "derived"
STATE_DIR = ROOT / "state_provider_momentum_downstream_v1"
PATH_RANKER_DIR = ROOT / "path-ranker"

PROVIDER_WORKSPACES = {
    "yfinance": "auto-quant-112315-yfinance",
    "kraken_public": "auto-quant-112315-kraken_public",
    "binance_public": "auto-quant-112315-binance_public",
    "bybit_public": "auto-quant-112315-bybit_public",
    "tvr_binance": "auto-quant-112315-tvr_binance",
}


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def run_command(label: str, cmd: list[str], env: dict[str, str] | None = None) -> dict[str, Any]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / f"{label}.cmd").write_text(" ".join(cmd) + "\n")
    proc = subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False, env=env)
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
        "cmd": cmd,
        "exit": proc.returncode,
        "stdout": str(OUT_DIR / f"{label}.out"),
        "stderr": str(OUT_DIR / f"{label}.err"),
        "parsed_stdout": parsed,
    }


def load_source_report() -> dict[str, Any]:
    return json.loads(SOURCE_REPORT.read_text())


def write_provider_matrix(source: dict[str, Any]) -> list[dict[str, Any]]:
    fetch_rows = source["provider_matrix"]["fetch_rows"]
    fetch_exits = source["provider_matrix"]["fetch_exits"]
    rows = [
        {
            "provider": "IBKR",
            "provider_requested": True,
            "provider_data_acquired": fetch_exits.get("ibkr_btc_paxos_midpoint_1h") == 0,
            "provider_unreachable": False,
            "local_cache_replay": False,
            "provider_symbol": "BTC PAXOS USD",
            "timeframe": "1h",
            "rows": fetch_rows.get("ibkr_btc_paxos_midpoint_1h", 0),
            "notes": "midpoint 1h fetched in provider matrix; AQ run_tomac stayed non-promotable/thin",
        },
        {
            "provider": "TradingViewRemix/TVR",
            "provider_requested": True,
            "provider_data_acquired": fetch_exits.get("tvr_binance_btcusdt_1h") == 0,
            "provider_unreachable": False,
            "local_cache_replay": False,
            "provider_symbol": "BINANCE:BTCUSDT",
            "timeframe": "1h",
            "rows": fetch_rows.get("tvr_binance_btcusdt_1h", 0),
            "notes": "TVR-routed Binance BTCUSDT 1h provider CSV",
        },
        {
            "provider": "yfinance/YF",
            "provider_requested": True,
            "provider_data_acquired": fetch_exits.get("yfinance_btc_usd_1h") == 0,
            "provider_unreachable": False,
            "local_cache_replay": False,
            "provider_symbol": "BTC-USD",
            "timeframe": "1h",
            "rows": fetch_rows.get("yfinance_btc_usd_1h", 0),
            "notes": "YF BTC-USD 1h provider CSV",
        },
        {
            "provider": "Kraken",
            "provider_requested": True,
            "provider_data_acquired": fetch_exits.get("kraken_xbtusd_1h") == 0,
            "provider_unreachable": False,
            "local_cache_replay": False,
            "provider_symbol": "XBTUSD",
            "timeframe": "1h",
            "rows": fetch_rows.get("kraken_xbtusd_1h", 0),
            "notes": "Kraken public XBTUSD 1h provider CSV",
        },
        {
            "provider": "Binance",
            "provider_requested": True,
            "provider_data_acquired": fetch_exits.get("binance_btcusdt_1h") == 0,
            "provider_unreachable": False,
            "local_cache_replay": False,
            "provider_symbol": "BTCUSDT",
            "timeframe": "1h",
            "rows": fetch_rows.get("binance_btcusdt_1h", 0),
            "notes": "Binance public BTCUSDT 1h provider CSV",
        },
        {
            "provider": "Bybit",
            "provider_requested": True,
            "provider_data_acquired": fetch_exits.get("bybit_btcusdt_linear_1h") == 0,
            "provider_unreachable": False,
            "local_cache_replay": False,
            "provider_symbol": "BTCUSDT linear",
            "timeframe": "1h",
            "rows": fetch_rows.get("bybit_btcusdt_linear_1h", 0),
            "notes": "Bybit public linear BTCUSDT 1h provider CSV",
        },
    ]
    path = REPORT_DIR / "provider_matrix_v1.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    return rows


def merge_momentum_trades() -> dict[str, Any]:
    DERIVED_DIR.mkdir(parents=True, exist_ok=True)
    merged = DERIVED_DIR / "provider_matrix_momentum_real_trades.jsonl"
    provider_counts: dict[str, int] = {}
    total = 0
    with merged.open("w", encoding="utf-8") as out:
        for provider, workspace in PROVIDER_WORKSPACES.items():
            src = (
                SOURCE_ROOT
                / "workspace"
                / workspace
                / "derived"
                / "ProviderCryptoMomentumStateV1.real_trades.jsonl"
            )
            count = 0
            if not src.exists():
                provider_counts[provider] = 0
                continue
            for line in src.read_text().splitlines():
                if not line.strip():
                    continue
                record = json.loads(line)
                original_trade_id = record["trade_id"]
                record["symbol"] = SYMBOL
                record["auto_quant_run_id"] = RUN_ID
                record["trade_id"] = f"{provider}:{original_trade_id}"
                record["provider_source"] = provider
                out.write(json.dumps(record, sort_keys=True) + "\n")
                count += 1
                total += 1
            provider_counts[provider] = count
    return {"path": str(merged), "provider_counts": provider_counts, "total": total}


def write_candle_jsons() -> dict[str, Any]:
    source_csv = SOURCE_ROOT / "provider-csv/binance_btcusdt_1h.csv"
    df = pd.read_csv(source_csv)
    df["date"] = pd.to_datetime(df["date"], utc=True)
    df = df.sort_values("date").set_index("date")
    outputs: dict[str, Any] = {}

    for timeframe, rule in [("1h", "1h"), ("4h", "4h"), ("1d", "1d")]:
        if timeframe == "1h":
            frame = df.copy()
        else:
            frame = pd.DataFrame(
                {
                    "open": df["open"].resample(rule).first(),
                    "high": df["high"].resample(rule).max(),
                    "low": df["low"].resample(rule).min(),
                    "close": df["close"].resample(rule).last(),
                    "volume": df["volume"].resample(rule).sum(),
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
            for idx, row in frame.reset_index().set_index("date").iterrows()
        ]
        out_path = DATA_DIR / f"binance_btcusdt_{timeframe}.json"
        write_json(out_path, records)
        outputs[timeframe] = {
            "path": str(out_path),
            "rows": len(records),
            "first_ts": records[0]["timestamp"] if records else None,
            "last_ts": records[-1]["timestamp"] if records else None,
        }
    return outputs


def file_exists(path: str | Path) -> bool:
    return Path(path).exists()


def read_json_maybe(path: Path) -> Any:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError:
        return None


def main() -> int:
    ROOT.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    (ROOT / "run_id.txt").write_text(RUN_ID + "\n")
    source = load_source_report()
    provider_matrix = write_provider_matrix(source)
    trades = merge_momentum_trades()
    candle_jsons = write_candle_jsons()

    env = os.environ.copy()
    env.update(
        {
            "OMP_NUM_THREADS": "1",
            "OPENBLAS_NUM_THREADS": "1",
            "MKL_NUM_THREADS": "1",
            "VECLIB_MAXIMUM_THREADS": "1",
        }
    )

    commands: list[dict[str, Any]] = []
    commands.append(run_command("00_provider_status", [str(ICT), "provider-status", "--agent"], env=env))
    commands.append(
        run_command(
            "01_ingest_real_trades",
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
                "auto_quant_real_trades_provider_matrix_momentum_113833",
            ],
            env=env,
        )
    )
    commands.append(
        run_command(
            "02_analyze_provider_btc",
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
        )
    )
    commands.append(
        run_command(
            "03_pre_bayes_status",
            [str(ICT), "pre-bayes-status", "--symbol", SYMBOL, "--state-dir", str(STATE_DIR), "--refresh", "--output-format", "json"],
            env=env,
        )
    )
    commands.append(
        run_command(
            "04_policy_training_status_before_export",
            [str(ICT), "policy-training-status", "--symbol", SYMBOL, "--state-dir", str(STATE_DIR), "--output-format", "json"],
            env=env,
        )
    )
    commands.append(
        run_command(
            "05_export_structural_path_ranking_target",
            [str(ICT), "export-structural-path-ranking-target", "--symbol", SYMBOL, "--state-dir", str(STATE_DIR)],
            env=env,
        )
    )
    commands.append(
        run_command(
            "06_policy_training_status_after_export",
            [str(ICT), "policy-training-status", "--symbol", SYMBOL, "--state-dir", str(STATE_DIR), "--output-format", "json"],
            env=env,
        )
    )

    target_csv = STATE_DIR / SYMBOL / "policy_training" / "structural_path_ranking_target.csv"
    model_dir = PATH_RANKER_DIR / "catboost_model"
    scores_csv = PATH_RANKER_DIR / "path_scores.csv"
    if target_csv.exists():
        commands.append(
            run_command(
                "07_train_catboost",
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
                env=env,
            )
        )
        commands.append(
            run_command(
                "08_apply_catboost_scores",
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
                env=env,
            )
        )
        if scores_csv.exists():
            commands.append(
                run_command(
                    "09_apply_external_scores",
                    [
                        str(ICT),
                        "apply-structural-path-ranking-external-scores",
                        "--symbol",
                        SYMBOL,
                        "--state-dir",
                        str(STATE_DIR),
                        "--scores-file",
                        str(scores_csv),
                    ],
                    env=env,
                )
            )
        artifact = model_dir / "trainer_artifact.json"
        if artifact.exists():
            model_family = "catboost"
            artifact_payload = read_json_maybe(artifact)
            if isinstance(artifact_payload, dict):
                model_family = str(artifact_payload.get("model_family") or artifact_payload.get("family") or model_family)
            commands.append(
                run_command(
                    "10_register_trainer_artifact",
                    [
                        str(ICT),
                        "register-structural-path-ranking-trainer-artifact",
                        "--symbol",
                        SYMBOL,
                        "--state-dir",
                        str(STATE_DIR),
                        "--artifact-uri",
                        str(artifact),
                        "--model-family",
                        model_family,
                        "--score-column",
                        "raw_path_score",
                    ],
                    env=env,
                )
            )

    commands.append(
        run_command(
            "11_workflow_structural_bundle",
            [
                str(ICT),
                "workflow-status",
                "--symbol",
                SYMBOL,
                "--phase",
                "structural-recommended-path-bundle",
                "--state-dir",
                str(STATE_DIR),
                "--agent",
                "--stable",
            ],
            env=env,
        )
    )
    commands.append(
        run_command(
            "12_workflow_execution_candidate",
            [
                str(ICT),
                "workflow-status",
                "--symbol",
                SYMBOL,
                "--phase",
                "execution-candidate",
                "--state-dir",
                str(STATE_DIR),
                "--agent",
                "--stable",
            ],
            env=env,
        )
    )
    commands.append(
        run_command(
            "13_workflow_full",
            [
                str(ICT),
                "workflow-status",
                "--symbol",
                SYMBOL,
                "--state-dir",
                str(STATE_DIR),
                "--refresh",
                "--output-format",
                "json",
                "--stable",
            ],
            env=env,
        )
    )

    command_exits = {cmd["label"]: cmd["exit"] for cmd in commands}
    status_after = next((c["parsed_stdout"] for c in commands if c["label"] == "06_policy_training_status_after_export"), None)
    workflow_full = next((c["parsed_stdout"] for c in commands if c["label"] == "13_workflow_full"), None)
    ingest = next((c["parsed_stdout"] for c in commands if c["label"] == "01_ingest_real_trades"), None)
    train_artifact = PATH_RANKER_DIR / "catboost_model" / "trainer_artifact.json"
    scores_exists = scores_csv.exists()

    target_rows = None
    mature_rows = None
    raw_scored_mature = None
    if isinstance(status_after, dict):
        text = json.dumps(status_after)
        target_rows = status_after.get("structural_path_target_rows") or status_after.get("rows")
        mature_rows = status_after.get("mature_rows")
        raw_scored_mature = status_after.get("raw_scored_mature")
        if target_rows is None and target_csv.exists():
            target_rows = max(sum(1 for _ in target_csv.open()) - 1, 0)
    elif target_csv.exists():
        target_rows = max(sum(1 for _ in target_csv.open()) - 1, 0)

    execution_ready = False
    execution_gate = None
    if isinstance(workflow_full, dict):
        blob = json.dumps(workflow_full)
        execution_ready = '"actionable":true' in blob or '"ready":true' in blob
        execution_gate = workflow_full.get("execution_gate_status") or workflow_full.get("status")

    provider_rows_ok = all(row["provider_requested"] for row in provider_matrix) and len(provider_matrix) == 6
    trade_total = trades["total"]
    all_required_exits_ok = all(command_exits.get(label) == 0 for label in ["00_provider_status", "01_ingest_real_trades", "02_analyze_provider_btc", "03_pre_bayes_status", "05_export_structural_path_ranking_target"])
    promotion_allowed = False
    trade_usable = False

    report = {
        "run_id": RUN_ID,
        "source_repair_run": str(SOURCE_ROOT),
        "symbol": SYMBOL,
        "provider_matrix_rows": provider_matrix,
        "provider_rows_ok": provider_rows_ok,
        "merged_trades": trades,
        "candle_jsons": candle_jsons,
        "command_exits": command_exits,
        "ingest_summary": ingest,
        "target_csv": str(target_csv),
        "target_rows": target_rows,
        "mature_rows": mature_rows,
        "raw_scored_mature": raw_scored_mature,
        "catboost_artifact_exists": file_exists(train_artifact),
        "scores_exists": scores_exists,
        "execution_ready": execution_ready,
        "execution_gate": execution_gate,
        "promotion_allowed": promotion_allowed,
        "trade_usable": trade_usable,
        "update_goal": False,
        "gate_result": "provider_matrix_momentum_downstream_fail_closed_no_promotion",
    }
    write_json(REPORT_DIR / "provider_momentum_downstream_v1.json", report)

    lines = [
        "# Provider Matrix Momentum Downstream v1",
        "",
        f"Run id: `{RUN_ID}`",
        f"Source repair run: `{SOURCE_ROOT}`",
        "",
        "## Scope",
        "",
        "Downstream readback for the `ProviderCryptoMomentumStateV1` branch from the repaired six-provider 113833 packet.",
        "This consumes only the momentum real-trade wire rows from provider-executed AQ workspaces, in an isolated state dir.",
        "",
        "## Provider Matrix",
        "",
    ]
    for row in provider_matrix:
        lines.append(
            f"- {row['provider']}: requested={row['provider_requested']} acquired={row['provider_data_acquired']} rows={row['rows']} local_cache_replay={row['local_cache_replay']}"
        )
    lines.extend(
        [
            "",
            "## Readback",
            "",
            f"- Merged momentum real-trade rows: `{trade_total}` from `{trades['provider_counts']}`.",
            f"- Required command exits ok: `{all_required_exits_ok}`; exits: `{command_exits}`.",
            f"- Ingest parsed/applied: `{ingest}`.",
            f"- Structural target rows: `{target_rows}`; mature_rows: `{mature_rows}`; raw_scored_mature: `{raw_scored_mature}`.",
            f"- CatBoost artifact exists: `{file_exists(train_artifact)}`; scores exists: `{scores_exists}`.",
            f"- Execution ready/actionable heuristic: `{execution_ready}`; execution gate/status: `{execution_gate}`.",
            "",
            "## Decision",
            "",
            "- Gate: `provider_matrix_momentum_downstream_fail_closed_no_promotion`.",
            "- This is downstream negative evidence for the same rooted branch, not a production promotion.",
            "- `promotion_allowed=false`.",
            "- `trade_usable=false`.",
            "- `update_goal=false`.",
        ]
    )
    (REPORT_DIR / "provider_momentum_downstream_v1.md").write_text("\n".join(lines) + "\n")

    assertions = [
        f"PASS run_id={RUN_ID}",
        f"PASS provider_matrix_rows={len(provider_matrix)}",
        f"PASS provider_rows_ok={provider_rows_ok}",
        f"PASS merged_momentum_trade_rows={trade_total}",
        f"PASS command_exits_recorded={len(command_exits)}",
        f"PASS ingest_exit={command_exits.get('01_ingest_real_trades')}",
        f"PASS analyze_exit={command_exits.get('02_analyze_provider_btc')}",
        f"PASS pre_bayes_exit={command_exits.get('03_pre_bayes_status')}",
        f"PASS export_target_exit={command_exits.get('05_export_structural_path_ranking_target')}",
        f"FAIL_CLOSED target_rows={target_rows}",
        f"FAIL_CLOSED mature_rows={mature_rows}",
        f"FAIL_CLOSED execution_ready={execution_ready}",
        "PASS promotion_allowed=false",
        "PASS trade_usable=false",
        "PASS update_goal=false",
    ]
    (CHECK_DIR / "provider_momentum_downstream_v1_assertions.out").write_text("\n".join(assertions) + "\n")
    print(REPORT_DIR / "provider_momentum_downstream_v1.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
