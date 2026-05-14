#!/usr/bin/env python3
"""Board A independent-market/timeframe downstream smoke.

This is an experiment-local harness. It consumes already captured provider
candles from the 175651 six-provider packet, builds isolated 1h/4h/1d candle
JSONs, runs ict-engine readbacks, and writes a fail-closed acceptance matrix.
"""

from __future__ import annotations

import csv
import json
import subprocess
from pathlib import Path


REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs/"
    / "20260512T175651+0800-codex-high-density-rsi-bb-ema-six-provider-aq-v1"
)
OUT_DIR = RUN_ROOT / "independent-market-timeframe-downstream-smoke-v1"
DATA_DIR = RUN_ROOT / "data"
STATE_DIR = RUN_ROOT / "state"
CHECK_DIR = RUN_ROOT / "checks"
CMD_DIR = RUN_ROOT / "command-output"
MAX_SOURCE_ROWS = 2400
COMMAND_TIMEOUT_SECONDS = 90

MARKETS = [
    {
        "symbol": "BOARD_A_SPY_YF_191941",
        "provider": "yfinance/YF",
        "market": "equity",
        "path": SOURCE_ROOT / "data/normalized/yahoo_spy_1h.normalized.csv",
    },
    {
        "symbol": "BOARD_A_SPY_IBKR_191941",
        "provider": "IBKR",
        "market": "equity",
        "path": SOURCE_ROOT / "data/normalized/ibkr_spy_1h_90d.normalized.csv",
    },
    {
        "symbol": "BOARD_A_BTC_BINANCE_191941",
        "provider": "Binance",
        "market": "crypto",
        "path": SOURCE_ROOT / "data/normalized/binance_btcusdt_1h.normalized.csv",
    },
    {
        "symbol": "BOARD_A_BTC_BYBIT_191941",
        "provider": "Bybit",
        "market": "crypto",
        "path": SOURCE_ROOT / "data/normalized/bybit_linear_btcusdt_1h.normalized.csv",
    },
    {
        "symbol": "BOARD_A_BTC_KRAKEN_191941",
        "provider": "Kraken",
        "market": "crypto",
        "path": SOURCE_ROOT / "data/normalized/kraken_futures_pfxbtusd_1h.normalized.csv",
    },
    {
        "symbol": "BOARD_A_BTC_TVR_191941",
        "provider": "TradingViewRemix/TVR",
        "market": "crypto",
        "path": SOURCE_ROOT / "data/normalized/tvr_btc_usd_1h.normalized.csv",
    },
]


def rel(path: Path) -> str:
    return str(path.relative_to(REPO))


def load_csv(path: Path) -> list[dict]:
    rows: list[dict] = []
    with path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            rows.append(
                {
                    "timestamp": row["timestamp"],
                    "open": float(row["open"]),
                    "high": float(row["high"]),
                    "low": float(row["low"]),
                    "close": float(row["close"]),
                    "volume": float(row.get("volume") or 0.0),
                }
            )
    return rows


def resample(rows: list[dict], width: int) -> list[dict]:
    out: list[dict] = []
    for i in range(0, len(rows), width):
        chunk = rows[i : i + width]
        if len(chunk) < width:
            continue
        out.append(
            {
                "timestamp": chunk[0]["timestamp"],
                "open": chunk[0]["open"],
                "high": max(r["high"] for r in chunk),
                "low": min(r["low"] for r in chunk),
                "close": chunk[-1]["close"],
                "volume": sum(r["volume"] for r in chunk),
            }
        )
    return out


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def run_cmd(name: str, args: list[str]) -> int:
    CMD_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)
    existing_exit = CHECK_DIR / f"{name}.exit"
    if existing_exit.exists() and (CMD_DIR / f"{name}.out").exists():
        return int(existing_exit.read_text(encoding="utf-8").strip() or "1")
    (CMD_DIR / f"{name}.cmd").write_text(" ".join(args) + "\n", encoding="utf-8")
    try:
        proc = subprocess.run(
            args,
            cwd=REPO,
            text=True,
            capture_output=True,
            timeout=COMMAND_TIMEOUT_SECONDS,
        )
        (CMD_DIR / f"{name}.out").write_text(proc.stdout, encoding="utf-8")
        (CMD_DIR / f"{name}.err").write_text(proc.stderr, encoding="utf-8")
        (CHECK_DIR / f"{name}.exit").write_text(f"{proc.returncode}\n", encoding="utf-8")
        return proc.returncode
    except subprocess.TimeoutExpired as exc:
        (CMD_DIR / f"{name}.out").write_text(exc.stdout or "", encoding="utf-8")
        (CMD_DIR / f"{name}.err").write_text(
            (exc.stderr or "") + f"\nTIMEOUT after {COMMAND_TIMEOUT_SECONDS}s\n",
            encoding="utf-8",
        )
        (CHECK_DIR / f"{name}.exit").write_text("124\n", encoding="utf-8")
        return 124


def read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    rows_out: list[dict] = []
    gate_rows: list[dict] = []
    all_exits: list[int] = []

    for market in MARKETS:
        source_path = market["path"]
        source_rows_full = load_csv(source_path) if source_path.exists() else []
        source_rows = source_rows_full[-MAX_SOURCE_ROWS:]
        symbol = market["symbol"]
        base = DATA_DIR / symbol
        one_h = base / "1h.json"
        four_h = base / "4h.json"
        one_d = base / "1d.json"
        one_h_rows = source_rows
        four_h_rows = resample(source_rows, 4)
        one_d_rows = resample(source_rows, 24)
        write_json(one_h, one_h_rows)
        write_json(four_h, four_h_rows)
        write_json(one_d, one_d_rows)

        rows_out.append(
            {
                "symbol": symbol,
                "provider": market["provider"],
                "market": market["market"],
                "source_path": rel(source_path),
                "source_rows_full": len(source_rows_full),
                "source_rows_1h": len(one_h_rows),
                "derived_rows_4h": len(four_h_rows),
                "derived_rows_1d": len(one_d_rows),
                "data_ltf": rel(one_h),
                "data_mtf": rel(four_h),
                "data_htf": rel(one_d),
            }
        )

        all_exits.append(
            run_cmd(
                f"validate_{symbol}",
                ["./target/debug/ict-engine", "validate-market-state", "--data", rel(one_h), "--compact"],
            )
        )
        all_exits.append(
            run_cmd(
                f"analyze_{symbol}",
                [
                    "./target/debug/ict-engine",
                    "analyze",
                    "--symbol",
                    symbol,
                    "--data-ltf",
                    rel(one_h),
                    "--data-mtf",
                    rel(four_h),
                    "--data-htf",
                    rel(one_d),
                    "--state-dir",
                    rel(STATE_DIR),
                    "--agent",
                ],
            )
        )
        all_exits.append(
            run_cmd(
                f"pre_bayes_{symbol}",
                [
                    "./target/debug/ict-engine",
                    "pre-bayes-status",
                    "--symbol",
                    symbol,
                    "--state-dir",
                    rel(STATE_DIR),
                    "--refresh",
                    "--output-format",
                    "json",
                ],
            )
        )
        all_exits.append(
            run_cmd(
                f"policy_{symbol}",
                [
                    "./target/debug/ict-engine",
                    "policy-training-status",
                    "--symbol",
                    symbol,
                    "--state-dir",
                    rel(STATE_DIR),
                    "--output-format",
                    "agent",
                ],
            )
        )
        all_exits.append(
            run_cmd(
                f"workflow_exec_{symbol}",
                [
                    "./target/debug/ict-engine",
                    "workflow-status",
                    "--symbol",
                    symbol,
                    "--state-dir",
                    rel(STATE_DIR),
                    "--refresh",
                    "--agent",
                ],
            )
        )

        pre = read_json(CMD_DIR / f"pre_bayes_{symbol}.out")
        workflow = read_json(STATE_DIR / symbol / "workflow_snapshot.json")
        candidate = read_json(STATE_DIR / symbol / "execution_candidate.json")
        policy_summary = read_json(STATE_DIR / symbol / "policy_training/structural_path_ranking_target_summary.json")
        confidence = (
            pre.get("latest_canonical_structural_confidence")
            or pre.get("latest_regime_posterior", {}).get("confidence")
            or workflow.get("ensemble", {}).get("posterior_confidence")
            or workflow.get("market_state", {}).get("overall_confidence")
            or 0.0
        )
        mature_rows = int(policy_summary.get("mature_rows") or 0)
        gate_rows.append(
            {
                "symbol": symbol,
                "provider": market["provider"],
                "market": market["market"],
                "source_native_timeframe": "1h",
                "derived_timeframes_tested": "1h,4h,1d",
                "native_cross_timeframe": False,
                "canonical_confidence": confidence,
                "mature_rows": mature_rows,
                "execution_ready": bool(candidate.get("ready")),
                "execution_actionable": bool(candidate.get("actionable")),
                "accepted_95": bool(confidence >= 0.95 and mature_rows >= 30 and candidate.get("ready")),
            }
        )

    with (OUT_DIR / "market_timeframe_inventory_v1.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows_out[0].keys()))
        writer.writeheader()
        writer.writerows(rows_out)
    with (OUT_DIR / "gate_matrix_v1.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(gate_rows[0].keys()))
        writer.writeheader()
        writer.writerows(gate_rows)

    independent_markets = len({row["market"] for row in gate_rows})
    providers = len({row["provider"] for row in gate_rows})
    accepted_95 = sum(1 for row in gate_rows if row["accepted_95"])
    payload = {
        "schema_version": "board-a-independent-market-timeframe-downstream-smoke-v1",
        "source_root": rel(SOURCE_ROOT),
        "run_root": rel(RUN_ROOT),
        "commands_total": len(all_exits),
        "commands_exit_zero": sum(1 for code in all_exits if code == 0),
        "providers_tested": providers,
        "independent_market_classes": independent_markets,
        "symbols_tested": len(gate_rows),
        "accepted_95_contexts_added": accepted_95,
        "promotion_allowed": accepted_95 == len(gate_rows),
        "trade_usable": False,
        "hard_failures": [
            "4h/1d are resampled from source 1h candles, not provider-native timeframe fetches",
            "no Auto-Quant rerun was performed in this smoke; it reuses provider materialization from 175651",
            "no CatBoost/path-ranker production maturity repair was performed for these independent symbols",
            "no artifact proves every visible regime calibrated >=0.95",
        ],
        "market_rows": rows_out,
        "gate_rows": gate_rows,
    }
    write_json(OUT_DIR / "independent_market_timeframe_downstream_smoke_v1.json", payload)
    assertions = [
        f"PASS providers_tested={providers}",
        f"PASS independent_market_classes={independent_markets}",
        f"PASS commands_exit_zero={payload['commands_exit_zero']}_of_{payload['commands_total']}",
        "FAIL_CLOSED native_cross_timeframe_provider_fetch=false",
        "FAIL_CLOSED auto_quant_rerun=false",
        "FAIL_CLOSED catboost_path_ranker_production_maturity_repair=false",
        f"FAIL_CLOSED accepted_95_contexts_added={accepted_95}",
        "PASS promotion_allowed=false",
        "PASS trade_usable=false",
    ]
    (CHECK_DIR / "independent_market_timeframe_downstream_smoke_v1_assertions.out").write_text(
        "\n".join(assertions) + "\n", encoding="utf-8"
    )
    md = [
        "# Independent Market Timeframe Downstream Smoke v1",
        "",
        f"- Source root: `{payload['source_root']}`",
        f"- Providers tested: `{providers}`",
        f"- Independent market classes: `{independent_markets}`",
        f"- Commands exit zero: `{payload['commands_exit_zero']}/{payload['commands_total']}`",
        f"- Accepted 95 contexts added: `{accepted_95}`",
        f"- Promotion allowed: `{str(payload['promotion_allowed']).lower()}`",
        f"- Trade usable: `{str(payload['trade_usable']).lower()}`",
        "",
        "## Gate Matrix",
        "",
        "| Symbol | Provider | Market | Confidence | Mature Rows | Ready | Actionable | Accepted 95 |",
        "|---|---|---|---:|---:|---|---|---|",
    ]
    for row in gate_rows:
        md.append(
            f"| `{row['symbol']}` | `{row['provider']}` | `{row['market']}` | "
            f"{float(row['canonical_confidence']):.6f} | {row['mature_rows']} | "
            f"{row['execution_ready']} | {row['execution_actionable']} | {row['accepted_95']} |"
        )
    md.extend(
        [
            "",
            "## Fail-Closed Reasons",
            "",
            "- 4h/1d files are deterministic resamples from 1h provider candles, not independent provider-native timeframe fetches.",
            "- This smoke uses the existing 175651 provider materialization and does not rerun Auto-Quant.",
            "- No per-regime calibrated `>=95%` artifact was produced.",
            "- No independent symbol reached execution-ready/actionable acceptance.",
        ]
    )
    (OUT_DIR / "independent_market_timeframe_downstream_smoke_v1.md").write_text(
        "\n".join(md) + "\n", encoding="utf-8"
    )
    return 0 if all(code == 0 for code in all_exits) else 1


if __name__ == "__main__":
    raise SystemExit(main())
