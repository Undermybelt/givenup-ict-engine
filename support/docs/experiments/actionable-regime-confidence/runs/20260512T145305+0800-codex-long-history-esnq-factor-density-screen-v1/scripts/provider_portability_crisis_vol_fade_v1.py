from __future__ import annotations

import csv
import json
import math
from pathlib import Path
from typing import Any

import pandas as pd


RUN_ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = RUN_ROOT / "provider-portability-crisis-vol-fade-v1"
PROVIDER_SMOKE = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260512T143900+0800-codex-provider-backed-regime-validation-smoke-v1/data"
)
LONGSPAN_ROOT = Path("/tmp/ict-provider-longspan-20260512T141554+0800")
COST_BPS = 2.0

INPUTS = [
    {
        "provider": "binance_public",
        "symbol": "BTCUSDT",
        "interval": "1h",
        "path": PROVIDER_SMOKE / "binance_btcusdt_1h_20170817_20260512.normalized.csv",
        "timestamp_col": "timestamp",
        "provider_data_acquired": True,
        "classification": "provider_backed_full_listing_1h",
    },
    {
        "provider": "ibkr",
        "symbol": "SPY",
        "interval": "1h",
        "path": PROVIDER_SMOKE / "ibkr_spy_1h_5y.normalized.csv",
        "timestamp_col": "timestamp",
        "provider_data_acquired": True,
        "classification": "provider_backed_5y_1h",
    },
    {
        "provider": "yfinance",
        "symbol": "ES=F",
        "interval": "1h",
        "path": PROVIDER_SMOKE / "yahoo_es_1h_20240513_20260512.normalized.csv",
        "timestamp_col": "timestamp",
        "provider_data_acquired": True,
        "classification": "provider_backed_near_server_max_1h",
    },
    {
        "provider": "kraken_public",
        "symbol": "PF_XBTUSD",
        "interval": "1h",
        "path": LONGSPAN_ROOT / "kraken_futures_pfxbtusd_1h_20200101_20260512.csv",
        "timestamp_col": "date",
        "provider_data_acquired": True,
        "classification": "provider_backed_window_capped_1h",
    },
    {
        "provider": "kraken_public",
        "symbol": "PF_SPXUSD",
        "interval": "1h",
        "path": LONGSPAN_ROOT / "kraken_futures_pfspxusd_1h_20200101_20260512.csv",
        "timestamp_col": "date",
        "provider_data_acquired": True,
        "classification": "provider_backed_window_capped_1h",
    },
    {
        "provider": "bybit_public",
        "symbol": "BTCUSDT_LINEAR",
        "interval": "1h",
        "path": LONGSPAN_ROOT / "bybit_linear_btcusdt_1h_20200101_20260512.csv",
        "timestamp_col": "date",
        "provider_data_acquired": True,
        "classification": "provider_backed_page_capped_1h",
    },
    {
        "provider": "tradingview_mcp",
        "symbol": "NASDAQ:QQQ",
        "interval": "1h",
        "path": None,
        "timestamp_col": "timestamp",
        "provider_data_acquired": False,
        "classification": "fetch_failed_in_141554",
    },
]


def period_bucket(ts: pd.Timestamp) -> str:
    year = int(ts.year)
    if year < 2018:
        return "pre_2018"
    if year <= 2020:
        return "2018_2020"
    if year <= 2022:
        return "2021_2022"
    if year <= 2024:
        return "2023_2024"
    return "2025_plus"


def wilson_lcb(wins: int, total: int, z: float = 1.96) -> float:
    if total <= 0:
        return 0.0
    phat = wins / total
    denom = 1.0 + z * z / total
    center = phat + z * z / (2.0 * total)
    margin = z * math.sqrt((phat * (1.0 - phat) + z * z / (4.0 * total)) / total)
    return (center - margin) / denom


def return_profit_factor(returns: pd.Series) -> float:
    gains = float(returns[returns > 0].sum())
    losses = float(-returns[returns < 0].sum())
    if losses == 0:
        return float("inf") if gains > 0 else 0.0
    return gains / losses


def max_drawdown(returns: pd.Series) -> float:
    equity = (1.0 + returns.fillna(0.0)).cumprod()
    peak = equity.cummax()
    dd = equity / peak - 1.0
    return float(dd.min()) if len(dd) else 0.0


def load_provider_frame(item: dict[str, Any]) -> pd.DataFrame:
    path = item["path"]
    if path is None or not Path(path).exists():
        return pd.DataFrame()
    df = pd.read_csv(path)
    df = df.rename(columns={item["timestamp_col"]: "timestamp"})
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
    for column in ["open", "high", "low", "close", "volume"]:
        df[column] = pd.to_numeric(df[column], errors="coerce")
    df = (
        df.dropna(subset=["timestamp", "open", "high", "low", "close"])
        .drop_duplicates(subset=["timestamp"])
        .sort_values("timestamp")
        .reset_index(drop=True)
    )
    df["provider"] = item["provider"]
    df["symbol"] = item["symbol"]
    df["interval"] = item["interval"]
    return add_features(df)


def add_features(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["ret_1h"] = out["close"].pct_change(1)
    out["ret_6h"] = out["close"].pct_change(6)
    out["ret_24h"] = out["close"].pct_change(24)
    out["ret_63h"] = out["close"].pct_change(63)
    prev_close = out["close"].shift(1)
    tr = pd.concat(
        [
            out["high"] - out["low"],
            (out["high"] - prev_close).abs(),
            (out["low"] - prev_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    out["atr14"] = tr.rolling(14, min_periods=14).mean()
    out["atr_pct"] = out["atr14"] / out["close"].replace(0, math.nan)
    atr_q75 = out["atr_pct"].quantile(0.75)
    ret24_q12 = out["ret_24h"].quantile(0.12)
    ret63_q12 = out["ret_63h"].quantile(0.12)
    out["main_regime"] = "Other"
    crisis = ((out["ret_24h"] <= ret24_q12) | (out["ret_63h"] <= ret63_q12)) & (out["atr_pct"] >= atr_q75)
    out.loc[crisis, "main_regime"] = "Crisis"
    out["high_vol_context"] = out["atr_pct"] >= atr_q75
    out["period_bucket"] = out["timestamp"].map(period_bucket)
    out["future_close_6h"] = out["close"].shift(-6)
    return out


def build_branch_trades(frames: list[pd.DataFrame]) -> pd.DataFrame:
    rows = []
    for df in frames:
        if df.empty:
            continue
        ret6_hi = df["ret_6h"].quantile(0.9)
        ret6_lo = df["ret_6h"].quantile(0.1)
        long_signal = (df["main_regime"] == "Crisis") & df["high_vol_context"] & (df["ret_6h"] <= ret6_lo)
        short_signal = (df["main_regime"] == "Crisis") & df["high_vol_context"] & (df["ret_6h"] >= ret6_hi)
        selected = df.loc[long_signal.fillna(False) | short_signal.fillna(False)].copy()
        if selected.empty:
            continue
        selected["direction_sign"] = 0.0
        selected.loc[long_signal.loc[selected.index].fillna(False), "direction_sign"] = 1.0
        selected.loc[short_signal.loc[selected.index].fillna(False), "direction_sign"] = -1.0
        selected["direction"] = selected["direction_sign"].map({1.0: "long", -1.0: "short"})
        selected = selected.dropna(subset=["future_close_6h", "close"])
        gross = selected["direction_sign"] * (selected["future_close_6h"] / selected["close"] - 1.0)
        selected["net_return"] = gross - COST_BPS / 10000.0
        selected["win"] = selected["net_return"] > 0
        selected["sub_regime"] = "VolatilityShock"
        selected["sub_sub_regime_or_profit_factor"] = "SixHourExhaustionFade"
        selected["profit_factor"] = "VolatilityExpansionFadeV1"
        selected["branch_path"] = (
            selected["main_regime"]
            + " -> "
            + selected["sub_regime"]
            + " -> "
            + selected["sub_sub_regime_or_profit_factor"]
            + " -> "
            + selected["profit_factor"]
        )
        rows.append(
            selected[
                [
                    "provider",
                    "symbol",
                    "interval",
                    "timestamp",
                    "period_bucket",
                    "direction",
                    "main_regime",
                    "sub_regime",
                    "sub_sub_regime_or_profit_factor",
                    "profit_factor",
                    "branch_path",
                    "close",
                    "future_close_6h",
                    "net_return",
                    "win",
                    "ret_6h",
                    "ret_24h",
                    "ret_63h",
                    "atr_pct",
                ]
            ]
        )
    if not rows:
        return pd.DataFrame()
    return pd.concat(rows, ignore_index=True).sort_values(["timestamp", "provider", "symbol"])


def summarize(frame: pd.DataFrame, keys: list[str]) -> pd.DataFrame:
    rows = []
    for key_values, group in frame.groupby(keys, dropna=False):
        if not isinstance(key_values, tuple):
            key_values = (key_values,)
        returns = group["net_return"]
        wins = int(group["win"].sum())
        trades = int(len(group))
        row = {key: value for key, value in zip(keys, key_values)}
        row.update(
            {
                "trades": trades,
                "wins": wins,
                "losses": trades - wins,
                "win_rate": wins / trades if trades else 0.0,
                "win_rate_wilson95_lcb": wilson_lcb(wins, trades),
                "mean_net_return": float(returns.mean()) if trades else 0.0,
                "sum_net_return": float(returns.sum()) if trades else 0.0,
                "return_profit_factor": return_profit_factor(returns),
                "max_drawdown_compounded": max_drawdown(returns),
            }
        )
        rows.append(row)
    return pd.DataFrame(rows).sort_values(keys).reset_index(drop=True)


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    frames = []
    provider_rows = []
    for item in INPUTS:
        df = load_provider_frame(item)
        if not df.empty:
            frames.append(df)
        provider_rows.append(
            {
                "provider": item["provider"],
                "symbol": item["symbol"],
                "interval": item["interval"],
                "provider_requested": item["path"] is not None,
                "provider_data_acquired": bool(item["provider_data_acquired"] and not df.empty),
                "rows": int(len(df)),
                "first_timestamp": "" if df.empty else df["timestamp"].min().isoformat(),
                "last_timestamp": "" if df.empty else df["timestamp"].max().isoformat(),
                "classification": item["classification"],
                "source_path": "" if item["path"] is None else str(item["path"]),
            }
        )
    trades = build_branch_trades(frames)
    trades.to_csv(OUT_DIR / "provider_branch_trades.csv", index=False)
    provider_summary = summarize(trades, ["provider", "symbol", "interval", "branch_path"]) if not trades.empty else pd.DataFrame()
    period_summary = summarize(trades, ["provider", "symbol", "period_bucket"]) if not trades.empty else pd.DataFrame()
    provider_summary.to_csv(OUT_DIR / "provider_branch_summary.csv", index=False)
    period_summary.to_csv(OUT_DIR / "provider_period_summary.csv", index=False)
    write_csv(OUT_DIR / "provider_provenance_sidecar.csv", provider_rows)
    summary = {
        "run_root": str(RUN_ROOT),
        "selected_branch_path": "Crisis -> VolatilityShock -> SixHourExhaustionFade -> VolatilityExpansionFadeV1",
        "total_provider_branch_trades": int(len(trades)),
        "provider_rows": provider_rows,
        "promotion_allowed": False,
        "trade_usable": False,
        "update_goal": False,
        "evidence_class": "provider_backed_branch_portability_probe_not_promotion",
    }
    (OUT_DIR / "provider_portability_crisis_vol_fade_v1.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    top_lines = []
    if not provider_summary.empty:
        for row in provider_summary.sort_values("trades", ascending=False).to_dict("records"):
            top_lines.append(
                f"- {row['provider']} {row['symbol']}: trades `{row['trades']}`, "
                f"win_rate `{row['win_rate']:.6f}`, PF `{row['return_profit_factor']:.6f}`, "
                f"mean `{row['mean_net_return']:.8f}`"
            )
    report = [
        "# Provider Portability Probe: Crisis Volatility Expansion Fade v1",
        "",
        f"Run root: `{RUN_ROOT}`",
        "",
        "Selected branch: `Crisis -> VolatilityShock -> SixHourExhaustionFade -> VolatilityExpansionFadeV1`",
        "",
        "## Provider Readback",
        "",
        *top_lines,
        "",
        "## Gate",
        "",
        "- `evidence_class:provider_backed_branch_portability_probe_not_promotion`",
        f"- `total_provider_branch_trades:{len(trades)}`",
        "- `pass:branch_path_fields_emitted`",
        "- `partial:provider_backed_rows_present`",
        "- `fail_closed:tradingview_mcp_fetch_failed_no_rows`",
        "- `fail_closed:not_auto_quant_provider_routed_recipe`",
        "- `fail_closed:no_pre_bayes_bbn_catboost_execution_tree_chain`",
        "- `promotion_allowed=false`",
        "- `trade_usable=false`",
        "- `update_goal=false`",
        "",
        "## Next",
        "",
        "If a provider-backed row survives profitability checks, convert the branch into an Auto-Quant material recipe and then run Pre-Bayes/filter -> BBN -> CatBoost/path-ranker -> execution tree. Otherwise keep this as provider-portability negative evidence.",
        "",
    ]
    (OUT_DIR / "provider_portability_crisis_vol_fade_v1.md").write_text("\n".join(report), encoding="utf-8")
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
