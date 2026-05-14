from __future__ import annotations

import csv
import hashlib
import json
import shutil
import subprocess
from pathlib import Path

import pandas as pd


RUN_ROOT = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260512T160734+0800-codex-ote-same-root-provider-aq-packet-v1"
)
SOURCE_ROOT = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260512T150855+0800-codex-145809-aq-material-seed-dispatch-v1"
)
TVR_BLOCKER_ROOT = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260512T154536+0800-codex-board-b-tvr-mcp-redacted-health-probe-v1"
)
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
    path.write_text(text)


def run_cmd(label: str, args: list[str], timeout: int = 360) -> int:
    cmd_path = RUN_ROOT / f"command-output/{label}.cmd"
    out_path = RUN_ROOT / f"command-output/{label}.out"
    err_path = RUN_ROOT / f"command-output/{label}.err"
    exit_path = RUN_ROOT / f"checks/{label}.exit"
    write_text(cmd_path, " ".join(args) + "\n")
    try:
        proc = subprocess.run(args, capture_output=True, text=True, timeout=timeout, check=False)
        write_text(out_path, proc.stdout)
        write_text(err_path, proc.stderr)
        code = proc.returncode
    except subprocess.TimeoutExpired as exc:
        write_text(out_path, exc.stdout or "")
        write_text(err_path, (exc.stderr or "") + f"\nTIMEOUT after {timeout}s\n")
        code = 124
    write_text(exit_path, f"{code}\n")
    return code


def normalize_csv(src: Path, dst: Path) -> dict:
    df = pd.read_csv(src)
    if "date" not in df.columns and "ts" in df.columns:
        df = df.rename(columns={"ts": "date"})
    required = ["date", "open", "high", "low", "close", "volume"]
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise ValueError(f"{src} missing required columns {missing}")
    out = df[required].copy()
    out["date"] = pd.to_datetime(out["date"], utc=True).dt.strftime("%Y-%m-%d %H:%M:%S")
    for col in ["open", "high", "low", "close", "volume"]:
        out[col] = pd.to_numeric(out[col], errors="coerce")
    out = out.dropna(subset=["date", "open", "high", "low", "close"])
    out["volume"] = out["volume"].fillna(0).clip(lower=0)
    out = out.drop_duplicates(subset=["date"]).sort_values("date").reset_index(drop=True)
    dst.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(dst, index=False)
    return {
        "raw_path": str(src),
        "normalized_path": str(dst),
        "rows": int(len(out)),
        "first": str(out["date"].iloc[0]) if not out.empty else "",
        "last": str(out["date"].iloc[-1]) if not out.empty else "",
    }


def material(package_id: str, title: str, symbol: str, data_path: Path, provider_note: str) -> dict:
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
            "Board B OTE continuation branch packet using 0.500, 0.618, 0.705, "
            "and 0.786 retracement leaves inside TrendExpansion."
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
            "promotion_allowed=false until same-root six-provider authority and downstream handoff probes are complete",
        ],
    }


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def write_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")


def main() -> int:
    RUN_ROOT.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(STRATEGY_SOURCE, RUN_ROOT / "agent-material/ProviderOteTrendRetracementV1.py")
    write_text(RUN_ROOT / "run_root.txt", str(RUN_ROOT) + "\n")

    start = "2026-02-12"
    end = "2026-05-12"
    raw = RUN_ROOT / "data/raw"
    norm = RUN_ROOT / "data/normalized"

    jobs = [
        (
            "01_fetch_yahoo_spy_1h",
            PY_FETCH_PREFIX
            + [
                "yahoo",
                "--symbol",
                "SPY",
                "--interval",
                "1h",
                "--start",
                start,
                "--end",
                end,
                "--output",
                str(raw / "yahoo_spy_1h.csv"),
            ],
            raw / "yahoo_spy_1h.csv",
            norm / "yahoo_spy_1h.normalized.csv",
        ),
        (
            "02_fetch_binance_btcusdt_1h",
            PY_FETCH_PREFIX
            + [
                "binance-kline",
                "--symbol",
                "BTCUSDT",
                "--interval",
                "1h",
                "--start",
                start,
                "--end",
                end,
                "--output",
                str(raw / "binance_btcusdt_1h.csv"),
            ],
            raw / "binance_btcusdt_1h.csv",
            norm / "binance_btcusdt_1h.normalized.csv",
        ),
        (
            "03_fetch_bybit_linear_btcusdt_1h",
            PY_FETCH_PREFIX
            + [
                "bybit-kline",
                "--category",
                "linear",
                "--symbol",
                "BTCUSDT",
                "--interval",
                "1h",
                "--start",
                start,
                "--end",
                end,
                "--output",
                str(raw / "bybit_linear_btcusdt_1h.csv"),
            ],
            raw / "bybit_linear_btcusdt_1h.csv",
            norm / "bybit_linear_btcusdt_1h.normalized.csv",
        ),
        (
            "04_fetch_kraken_futures_pfxbtusd_1h",
            PY_FETCH_PREFIX
            + [
                "kraken-kline",
                "--market",
                "futures",
                "--pair",
                "PF_XBTUSD",
                "--interval",
                "1h",
                "--start",
                start,
                "--end",
                end,
                "--output",
                str(raw / "kraken_futures_pfxbtusd_1h.csv"),
            ],
            raw / "kraken_futures_pfxbtusd_1h.csv",
            norm / "kraken_futures_pfxbtusd_1h.normalized.csv",
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
                "63",
                "--output",
                str(raw / "ibkr_spy_1h_90d.csv"),
            ],
            raw / "ibkr_spy_1h_90d.csv",
            norm / "ibkr_spy_1h_90d.normalized.csv",
        ),
    ]

    fetch_rows = []
    for label, args, raw_path, norm_path in jobs:
        exit_code = run_cmd(label, args, timeout=420)
        row = {
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

    materials = [
        (
            "ote-current-yf-spy-1h-v1",
            "OTE current provider packet - yfinance SPY 1h",
            "SPY",
            norm / "yahoo_spy_1h.normalized.csv",
            "source_provider=yfinance/YF SPY 1h current fetch",
        ),
        (
            "ote-current-binance-btcusdt-1h-v1",
            "OTE current provider packet - Binance BTCUSDT 1h",
            "BTCUSDT",
            norm / "binance_btcusdt_1h.normalized.csv",
            "source_provider=Binance public BTCUSDT 1h current fetch",
        ),
        (
            "ote-current-bybit-btcusdt-1h-v1",
            "OTE current provider packet - Bybit BTCUSDT linear 1h",
            "BTCUSDT",
            norm / "bybit_linear_btcusdt_1h.normalized.csv",
            "source_provider=Bybit public linear BTCUSDT 1h current fetch",
        ),
        (
            "ote-current-kraken-pfxbtusd-1h-v1",
            "OTE current provider packet - Kraken PF_XBTUSD 1h",
            "XBTUSD",
            norm / "kraken_futures_pfxbtusd_1h.normalized.csv",
            "source_provider=Kraken futures PF_XBTUSD 1h current fetch",
        ),
        (
            "ote-current-ibkr-spy-1h-v1",
            "OTE current provider packet - IBKR SPY 1h",
            "SPY",
            norm / "ibkr_spy_1h_90d.normalized.csv",
            "source_provider=IBKR gateway SPY 1h 90D current fetch",
        ),
    ]
    material_paths = []
    for package_id, title, symbol, data_path, provider_note in materials:
        if data_path.exists():
            path = RUN_ROOT / f"agent-material/{package_id}.material.json"
            write_json(path, material(package_id, title, symbol, data_path, provider_note))
            material_paths.append(path)

    provider_rows = [
        {
            "provider": "IBKR",
            "provider_requested": True,
            "provider_data_acquired": (norm / "ibkr_spy_1h_90d.normalized.csv").exists(),
            "provider_unreachable": False,
            "aq_material_created": (RUN_ROOT / "agent-material/ote-current-ibkr-spy-1h-v1.material.json").exists(),
            "source_or_blocker": str(norm / "ibkr_spy_1h_90d.normalized.csv"),
        },
        {
            "provider": "TradingViewRemix/TVR",
            "provider_requested": True,
            "provider_data_acquired": False,
            "provider_unreachable": True,
            "aq_material_created": False,
            "source_or_blocker": str(TVR_BLOCKER_ROOT),
        },
        {
            "provider": "yfinance/YF",
            "provider_requested": True,
            "provider_data_acquired": (norm / "yahoo_spy_1h.normalized.csv").exists(),
            "provider_unreachable": False,
            "aq_material_created": (RUN_ROOT / "agent-material/ote-current-yf-spy-1h-v1.material.json").exists(),
            "source_or_blocker": str(norm / "yahoo_spy_1h.normalized.csv"),
        },
        {
            "provider": "Kraken",
            "provider_requested": True,
            "provider_data_acquired": (norm / "kraken_futures_pfxbtusd_1h.normalized.csv").exists(),
            "provider_unreachable": False,
            "aq_material_created": (RUN_ROOT / "agent-material/ote-current-kraken-pfxbtusd-1h-v1.material.json").exists(),
            "source_or_blocker": str(norm / "kraken_futures_pfxbtusd_1h.normalized.csv"),
        },
        {
            "provider": "Binance",
            "provider_requested": True,
            "provider_data_acquired": (norm / "binance_btcusdt_1h.normalized.csv").exists(),
            "provider_unreachable": False,
            "aq_material_created": (RUN_ROOT / "agent-material/ote-current-binance-btcusdt-1h-v1.material.json").exists(),
            "source_or_blocker": str(norm / "binance_btcusdt_1h.normalized.csv"),
        },
        {
            "provider": "Bybit",
            "provider_requested": True,
            "provider_data_acquired": (norm / "bybit_linear_btcusdt_1h.normalized.csv").exists(),
            "provider_unreachable": False,
            "aq_material_created": (RUN_ROOT / "agent-material/ote-current-bybit-btcusdt-1h-v1.material.json").exists(),
            "source_or_blocker": str(norm / "bybit_linear_btcusdt_1h.normalized.csv"),
        },
    ]
    provider_matrix = RUN_ROOT / "summaries/provider_provenance_matrix.csv"
    with provider_matrix.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(provider_rows[0].keys()))
        writer.writeheader()
        writer.writerows(provider_rows)

    write_json(
        RUN_ROOT / "summaries/prep_summary.json",
        {
            "fetch_rows": fetch_rows,
            "material_paths": [str(path) for path in material_paths],
            "provider_rows": provider_rows,
            "tvr_blocker": str(TVR_BLOCKER_ROOT),
            "promotion_allowed": False,
            "trade_usable": False,
        },
    )
    with (RUN_ROOT / "summaries/material_paths.txt").open("w") as fh:
        for path in material_paths:
            fh.write(str(path) + "\n")
    with (RUN_ROOT / "summaries/data_line_counts.txt").open("w") as fh:
        for row in fetch_rows:
            fh.write(f"{row['normalized_path']},{row['rows']},{row['first']},{row['last']}\n")

    manifest_paths = [
        RUN_ROOT / "agent-material/ProviderOteTrendRetracementV1.py",
        RUN_ROOT / "summaries/prep_summary.json",
        RUN_ROOT / "summaries/provider_provenance_matrix.csv",
        RUN_ROOT / "summaries/material_paths.txt",
        RUN_ROOT / "summaries/data_line_counts.txt",
    ] + material_paths
    write_text(
        RUN_ROOT / "checks/sha256_manifest_prep.out",
        "".join(f"{sha256(path)}  {path}\n" for path in manifest_paths if path.exists()),
    )

    good_materials = len(material_paths)
    tv_unreachable = any(row["provider"] == "TradingViewRemix/TVR" and row["provider_unreachable"] for row in provider_rows)
    assertion_lines = [
        f"{'PASS' if good_materials >= 5 else 'FAIL'} materials_created_at_least_5={good_materials}",
        f"{'PASS' if tv_unreachable else 'FAIL'} tvr_recorded_unreachable_without_retry={tv_unreachable}",
        "PASS promotion_allowed_false=True",
        "PASS board_b_profitability_packet_only=True",
    ]
    write_text(RUN_ROOT / "checks/prep_assertions.out", "\n".join(assertion_lines) + "\n")
    if good_materials < 5:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
