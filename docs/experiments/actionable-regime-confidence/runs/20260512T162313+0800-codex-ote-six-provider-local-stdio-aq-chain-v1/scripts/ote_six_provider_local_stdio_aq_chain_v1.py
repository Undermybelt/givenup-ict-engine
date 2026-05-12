#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import json
import os
import shutil
import subprocess
from pathlib import Path

import pandas as pd


RUN_ID = "20260512T162313+0800-codex-ote-six-provider-local-stdio-aq-chain-v1"
RUN_ROOT = Path("docs/experiments/actionable-regime-confidence/runs") / RUN_ID
SOURCE_ROOT = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260512T150855+0800-codex-145809-aq-material-seed-dispatch-v1"
)
TVR_STDIO_HOME = Path("/tmp/ict-engine-tvr-stdio-162313-home")
STRATEGY_SOURCE = SOURCE_ROOT / "agent-material/ProviderOteTrendRetracementV1.py"
FETCH = "scripts/auto_quant_external/fetch_external.py"
PY_FETCH_PREFIX = [
    "uv",
    "run",
    "--with",
    "pandas",
    "--with",
    "requests",
    "--with",
    "ib_async",
    "--with",
    "redis",
    "--with",
    "pyyaml",
    "python",
    FETCH,
]


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_json(path: Path, data: object) -> None:
    write_text(path, json.dumps(data, indent=2, sort_keys=True) + "\n")


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def run_cmd(label: str, args: list[str], timeout: int = 600, env: dict[str, str] | None = None) -> int:
    cmd_path = RUN_ROOT / f"command-output/{label}.cmd"
    out_path = RUN_ROOT / f"command-output/{label}.out"
    err_path = RUN_ROOT / f"command-output/{label}.err"
    exit_path = RUN_ROOT / f"checks/{label}.exit"
    write_text(cmd_path, " ".join(args) + "\n")
    try:
        proc = subprocess.run(args, capture_output=True, text=True, timeout=timeout, check=False, env=env)
        write_text(out_path, proc.stdout)
        write_text(err_path, proc.stderr)
        code = proc.returncode
    except subprocess.TimeoutExpired as exc:
        write_text(out_path, exc.stdout or "")
        write_text(err_path, (exc.stderr or "") + f"\nTIMEOUT after {timeout}s\n")
        code = 124
    write_text(exit_path, f"{code}\n")
    return code


def normalize_csv(src: Path, dst: Path) -> dict[str, object]:
    df = pd.read_csv(src)
    if "timestamp" not in df.columns:
        if "date" in df.columns:
            df = df.rename(columns={"date": "timestamp"})
        elif "ts" in df.columns:
            df = df.rename(columns={"ts": "timestamp"})
        elif "datetime" in df.columns:
            df = df.rename(columns={"datetime": "timestamp"})
    required = ["timestamp", "open", "high", "low", "close", "volume"]
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise ValueError(f"{src} missing required columns {missing}")
    out = df[required].copy()
    out["timestamp"] = pd.to_datetime(out["timestamp"], utc=True).dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    for col in ["open", "high", "low", "close", "volume"]:
        out[col] = pd.to_numeric(out[col], errors="coerce")
    out = out.dropna(subset=["timestamp", "open", "high", "low", "close"])
    out["volume"] = out["volume"].fillna(0).clip(lower=0)
    out = out.drop_duplicates(subset=["timestamp"]).sort_values("timestamp").reset_index(drop=True)
    dst.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(dst, index=False)
    return {
        "raw_path": str(src),
        "normalized_path": str(dst),
        "rows": int(len(out)),
        "first": str(out["timestamp"].iloc[0]) if not out.empty else "",
        "last": str(out["timestamp"].iloc[-1]) if not out.empty else "",
    }


def normalize_tvr_json(src: Path, dst: Path) -> dict[str, object]:
    payload = json.loads(src.read_text(encoding="utf-8"))
    rows = []
    for result in payload.get("results", []):
        if result.get("provider") != "tradingview_mcp":
            continue
        if not result.get("ok"):
            continue
        for bar in result.get("data", []):
            rows.append(
                {
                    "timestamp": bar.get("timestamp", ""),
                    "open": bar.get("open", ""),
                    "high": bar.get("high", ""),
                    "low": bar.get("low", ""),
                    "close": bar.get("close", ""),
                    "volume": bar.get("volume", 0),
                }
            )
    tmp_csv = dst.with_suffix(".raw.csv")
    write_csv(tmp_csv, rows, ["timestamp", "open", "high", "low", "close", "volume"])
    summary = normalize_csv(tmp_csv, dst)
    summary["raw_path"] = str(src)
    return summary


def material(package_id: str, title: str, symbol: str, data_path: Path, provider_note: str) -> dict[str, object]:
    return {
        "package_id": package_id,
        "title": title,
        "symbol": symbol,
        "timeframe": "1h",
        "direction": "long",
        "data_path": str(data_path),
        "strategy_source_path": str(RUN_ROOT / "agent-material/ProviderOteTrendRetracementV1.py"),
        "strategy_class_name": "ProviderOteTrendRetracementV1",
        "strategy_brief": (
            "Board A six-provider OTE continuation packet using 0.500, 0.618, "
            "0.705, and 0.786 retracement leaves inside TrendExpansion."
        ),
        "evaluation_priority": [
            "branch_trade_density",
            "regime_conditioned_win_rate",
            "profit_factor",
            "walk_forward_survival",
        ],
        "notes": [
            "branch_path=TrendExpansion -> NormalVolatility -> OTERetracementLevel -> OTEContinuationLong",
            provider_note,
            "promotion_allowed=false until downstream filter/pre-Bayes -> BBN -> CatBoost/path-ranker -> execution-tree gates pass",
        ],
    }


def main() -> int:
    RUN_ROOT.mkdir(parents=True, exist_ok=True)
    for subdir in ["checks", "command-output", "data/raw", "data/normalized", "agent-material", "summaries", "state"]:
        (RUN_ROOT / subdir).mkdir(parents=True, exist_ok=True)
    write_text(RUN_ROOT / "run_root.txt", str(RUN_ROOT) + "\n")
    shutil.copyfile(STRATEGY_SOURCE, RUN_ROOT / "agent-material/ProviderOteTrendRetracementV1.py")

    start = "2026-02-12"
    end = "2026-05-12"
    raw = RUN_ROOT / "data/raw"
    norm = RUN_ROOT / "data/normalized"

    fetch_jobs = [
        (
            "01_fetch_yahoo_spy_1h",
            PY_FETCH_PREFIX + ["yahoo", "--symbol", "SPY", "--interval", "1h", "--start", start, "--end", end, "--output", str(raw / "yahoo_spy_1h.csv")],
            raw / "yahoo_spy_1h.csv",
            norm / "yahoo_spy_1h.normalized.csv",
            "yfinance/YF",
        ),
        (
            "02_fetch_binance_btcusdt_1h",
            PY_FETCH_PREFIX + ["binance-kline", "--symbol", "BTCUSDT", "--interval", "1h", "--start", start, "--end", end, "--output", str(raw / "binance_btcusdt_1h.csv")],
            raw / "binance_btcusdt_1h.csv",
            norm / "binance_btcusdt_1h.normalized.csv",
            "Binance",
        ),
        (
            "03_fetch_bybit_linear_btcusdt_1h",
            PY_FETCH_PREFIX + ["bybit-kline", "--category", "linear", "--symbol", "BTCUSDT", "--interval", "1h", "--start", start, "--end", end, "--output", str(raw / "bybit_linear_btcusdt_1h.csv")],
            raw / "bybit_linear_btcusdt_1h.csv",
            norm / "bybit_linear_btcusdt_1h.normalized.csv",
            "Bybit",
        ),
        (
            "04_fetch_kraken_futures_pfxbtusd_1h",
            PY_FETCH_PREFIX + ["kraken-kline", "--market", "futures", "--pair", "PF_XBTUSD", "--interval", "1h", "--start", start, "--end", end, "--output", str(raw / "kraken_futures_pfxbtusd_1h.csv")],
            raw / "kraken_futures_pfxbtusd_1h.csv",
            norm / "kraken_futures_pfxbtusd_1h.normalized.csv",
            "Kraken",
        ),
        (
            "05_fetch_ibkr_spy_1h",
            PY_FETCH_PREFIX
            + [
                "ibkr-historical",
                "--symbol",
                "SPY",
                "--sec-type",
                "STK",
                "--exchange",
                "SMART",
                "--currency",
                "USD",
                "--primary-exchange",
                "ARCA",
                "--bar-size",
                "1 hour",
                "--duration",
                "90 D",
                "--what-to-show",
                "TRADES",
                "--port",
                "4002",
                "--client-id",
                "64",
                "--output",
                str(raw / "ibkr_spy_1h_90d.csv"),
            ],
            raw / "ibkr_spy_1h_90d.csv",
            norm / "ibkr_spy_1h_90d.normalized.csv",
            "IBKR",
        ),
    ]

    fetch_rows: list[dict[str, object]] = []
    for label, args, raw_path, norm_path, provider in fetch_jobs:
        exit_code = run_cmd(label, args, timeout=420)
        row: dict[str, object] = {
            "provider": provider,
            "label": label,
            "exit": exit_code,
            "raw_path": str(raw_path),
            "normalized_path": str(norm_path),
            "rows": 0,
            "first": "",
            "last": "",
        }
        if exit_code == 0 and raw_path.exists():
            row.update(normalize_csv(raw_path, norm_path))
        fetch_rows.append(row)

    tvr_env = {
        **os.environ,
        "HOME": str(TVR_STDIO_HOME),
        "ICT_ENGINE_TVREMIX_MCP_URL": "",
        "ICT_ENGINE_TVREMIX_MCP_API_KEY": "",
        "ICT_ENGINE_TRADINGVIEW_MCP_CMD": "uv",
        "ICT_ENGINE_TRADINGVIEW_MCP_ARGS": "--directory /Users/thrill3r/tradingview-mcp/tradingview-mcp run tradingview-mcp",
    }
    tvr_json = raw / "tvr_btc_usd_1h.json"
    tvr_exit = run_cmd(
        "06_fetch_tvr_local_stdio_btc_usd_1h",
        [
            "./target/debug/ict-engine",
            "market-data-harness",
            "--action",
            "fetch",
            "--market",
            "board-a-162313-tvr-stdio-btc-usd-1h",
            "--interval",
            "1h",
            "--role",
            "crypto_reference",
            "--provider",
            "crypto_reference=tradingview_mcp",
            "--symbol-spec",
            "crypto_reference=BTC-USD",
        ],
        timeout=300,
        env=tvr_env,
    )
    shutil.copyfile(RUN_ROOT / "command-output/06_fetch_tvr_local_stdio_btc_usd_1h.out", tvr_json)
    tvr_row: dict[str, object] = {
        "provider": "TradingViewRemix/TVR",
        "label": "06_fetch_tvr_local_stdio_btc_usd_1h",
        "exit": tvr_exit,
        "raw_path": str(tvr_json),
        "normalized_path": str(norm / "tvr_btc_usd_1h.normalized.csv"),
        "rows": 0,
        "first": "",
        "last": "",
    }
    if tvr_exit == 0 and tvr_json.exists():
        tvr_row.update(normalize_tvr_json(tvr_json, norm / "tvr_btc_usd_1h.normalized.csv"))
    fetch_rows.append(tvr_row)

    material_specs = [
        ("ote-162313-yf-spy-1h-v1", "OTE six-provider local-stdio packet - yfinance SPY 1h", "SPY", norm / "yahoo_spy_1h.normalized.csv", "source_provider=yfinance/YF SPY 1h current fetch"),
        ("ote-162313-binance-btcusdt-1h-v1", "OTE six-provider local-stdio packet - Binance BTCUSDT 1h", "BTCUSDT", norm / "binance_btcusdt_1h.normalized.csv", "source_provider=Binance public BTCUSDT 1h current fetch"),
        ("ote-162313-bybit-btcusdt-1h-v1", "OTE six-provider local-stdio packet - Bybit BTCUSDT linear 1h", "BTCUSDT", norm / "bybit_linear_btcusdt_1h.normalized.csv", "source_provider=Bybit public linear BTCUSDT 1h current fetch"),
        ("ote-162313-kraken-pfxbtusd-1h-v1", "OTE six-provider local-stdio packet - Kraken PF_XBTUSD 1h", "XBTUSD", norm / "kraken_futures_pfxbtusd_1h.normalized.csv", "source_provider=Kraken futures PF_XBTUSD 1h current fetch"),
        ("ote-162313-ibkr-spy-1h-v1", "OTE six-provider local-stdio packet - IBKR SPY 1h", "SPY", norm / "ibkr_spy_1h_90d.normalized.csv", "source_provider=IBKR gateway SPY 1h 90D current fetch"),
        ("ote-162313-tvr-btc-usd-1h-v1", "OTE six-provider local-stdio packet - TVR BTC-USD 1h", "BTC-USD", norm / "tvr_btc_usd_1h.normalized.csv", "source_provider=TradingViewRemix/TVR local-stdio BTC-USD 1h current fetch"),
    ]
    material_paths: list[Path] = []
    for package_id, title, symbol, data_path, provider_note in material_specs:
        if data_path.exists():
            path = RUN_ROOT / f"agent-material/{package_id}.material.json"
            write_json(path, material(package_id, title, symbol, data_path, provider_note))
            material_paths.append(path)

    provider_rows = []
    provider_order = ["IBKR", "TradingViewRemix/TVR", "yfinance/YF", "Kraken", "Binance", "Bybit"]
    provider_to_material = {
        "IBKR": "ote-162313-ibkr-spy-1h-v1.material.json",
        "TradingViewRemix/TVR": "ote-162313-tvr-btc-usd-1h-v1.material.json",
        "yfinance/YF": "ote-162313-yf-spy-1h-v1.material.json",
        "Kraken": "ote-162313-kraken-pfxbtusd-1h-v1.material.json",
        "Binance": "ote-162313-binance-btcusdt-1h-v1.material.json",
        "Bybit": "ote-162313-bybit-btcusdt-1h-v1.material.json",
    }
    by_provider = {str(row["provider"]): row for row in fetch_rows}
    for provider in provider_order:
        row = by_provider.get(provider, {})
        material_name = provider_to_material[provider]
        provider_rows.append(
            {
                "provider": provider,
                "provider_requested": True,
                "provider_data_acquired": bool(row.get("rows", 0)),
                "rows": row.get("rows", 0),
                "first": row.get("first", ""),
                "last": row.get("last", ""),
                "aq_material_created": (RUN_ROOT / "agent-material" / material_name).exists(),
                "source_or_blocker": row.get("normalized_path", ""),
                "exit": row.get("exit", ""),
            }
        )

    write_csv(RUN_ROOT / "summaries/provider_provenance_matrix.csv", provider_rows, ["provider", "provider_requested", "provider_data_acquired", "rows", "first", "last", "aq_material_created", "source_or_blocker", "exit"])
    write_csv(RUN_ROOT / "summaries/fetch_summary.csv", fetch_rows, ["provider", "label", "exit", "raw_path", "normalized_path", "rows", "first", "last"])
    write_text(RUN_ROOT / "summaries/material_paths.txt", "\n".join(str(path) for path in material_paths) + "\n")

    all_six_materials = len(material_paths) == 6 and all(row["aq_material_created"] for row in provider_rows)
    batch_exit = 99
    dispatch_exit = 99
    rank_exit = 99
    if material_paths:
        batch_args = [
            "./target/debug/ict-engine",
            "auto-quant-agent-material-batch",
            "--symbol",
            "PROVIDER_OTE_162313",
            "--state-dir",
            str(RUN_ROOT / "state"),
            "--repo-url",
            "/Users/thrill3r/Auto-Quant",
            "--max-parallel",
            "1",
        ]
        for path in material_paths:
            batch_args.extend(["--material", str(path)])
        batch_exit = run_cmd("07_agent_material_batch", batch_args, timeout=300)
    if batch_exit == 0 and all_six_materials:
        dispatch_exit = run_cmd(
            "08_agent_material_dispatch_groups_0_5",
            [
                "./target/debug/ict-engine",
                "auto-quant-agent-material-dispatch",
                "--symbol",
                "PROVIDER_OTE_162313",
                "--state-dir",
                str(RUN_ROOT / "state"),
                "--group-indices",
                "0,1,2,3,4,5",
            ],
            timeout=1800,
        )
        rank_exit = run_cmd(
            "09_agent_material_rank",
            [
                "./target/debug/ict-engine",
                "auto-quant-agent-material-rank",
                "--symbol",
                "PROVIDER_OTE_162313",
                "--state-dir",
                str(RUN_ROOT / "state"),
            ],
            timeout=300,
        )

    prep_summary = {
        "run_id": RUN_ID,
        "fetch_rows": fetch_rows,
        "provider_rows": provider_rows,
        "material_paths": [str(path) for path in material_paths],
        "all_six_materials": all_six_materials,
        "batch_exit": batch_exit,
        "dispatch_exit": dispatch_exit,
        "rank_exit": rank_exit,
        "same_root_six_provider_data_packet": all_six_materials,
        "same_root_six_provider_aq_dispatch_exit0": bool(batch_exit == 0 and dispatch_exit == 0),
        "promotion_allowed": False,
        "trade_usable": False,
        "update_goal": False,
    }
    write_json(RUN_ROOT / "summaries/ote_six_provider_local_stdio_aq_chain_summary_v1.json", prep_summary)

    assertions = [
        f"all_six_materials={str(all_six_materials).lower()}",
        f"batch_exit={batch_exit}",
        f"dispatch_exit={dispatch_exit}",
        f"rank_exit={rank_exit}",
        "promotion_allowed=false",
        "trade_usable=false",
        "update_goal=false",
    ]
    write_text(RUN_ROOT / "checks/ote_six_provider_local_stdio_aq_chain_v1_assertions.out", "\n".join(assertions) + "\n")
    manifest_targets = [
        RUN_ROOT / "summaries/ote_six_provider_local_stdio_aq_chain_summary_v1.json",
        RUN_ROOT / "summaries/provider_provenance_matrix.csv",
        RUN_ROOT / "summaries/fetch_summary.csv",
        RUN_ROOT / "summaries/material_paths.txt",
        RUN_ROOT / "checks/ote_six_provider_local_stdio_aq_chain_v1_assertions.out",
    ]
    write_text(RUN_ROOT / "checks/sha256_manifest.out", "".join(f"{sha256(path)}  {path}\n" for path in manifest_targets if path.exists()))

    print(json.dumps(prep_summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
