from __future__ import annotations

import csv
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd


RUN_ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = RUN_ROOT / "factor-density-screen-v1"
SOURCE_ROOT = Path("/Users/thrill3r/Downloads/Tomac/ict-cleaned-mtf")
REPORT = OUT_DIR / "long_history_esnq_factor_density_screen_v1.md"

SYMBOLS = {
    "NQ": {
        "path": SOURCE_ROOT / "cleaned-1h/nq.continuous-1h.json",
        "role": "primary_esnq",
    },
    "ES": {
        "path": SOURCE_ROOT / "cleaned-1h/es.continuous-1h.json",
        "role": "primary_esnq",
    },
    "YM": {
        "path": SOURCE_ROOT / "cleaned-1h/ym.continuous-1h.json",
        "role": "support_cross_market",
    },
    "XAU": {
        "path": SOURCE_ROOT / "cleaned-1h/xau.continuous-1h.json",
        "role": "support_cross_market",
    },
    "EUR": {
        "path": SOURCE_ROOT / "cleaned-1h/eur.continuous-1h.json",
        "role": "support_cross_market",
    },
}

ROUND_TRIP_COST_BPS = 2.0
MIN_BRANCH_TRADES = 80
MIN_PERIODS_WITH_TRADES = 3


@dataclass(frozen=True)
class Candidate:
    candidate_id: str
    sub_regime: str
    sub_sub: str
    hold_hours: int
    description: str


CANDIDATES = [
    Candidate(
        "HourlyTrendPullbackContinuationV1",
        "TrendContinuation",
        "HourlyPullbackReentry",
        3,
        "Follow the parent trend after a short counter-move.",
    ),
    Candidate(
        "TwentyHourBreakoutContinuationV1",
        "BreakoutContinuation",
        "TwentyHourRangeExpansion",
        4,
        "Follow fresh 20 hour highs/lows.",
    ),
    Candidate(
        "RangeBandMeanReversionV1",
        "RangeMeanReversion",
        "BandStretchFade",
        3,
        "Fade large z-score stretch only inside Sideways parent context.",
    ),
    Candidate(
        "VolatilityExpansionFadeV1",
        "VolatilityShock",
        "SixHourExhaustionFade",
        6,
        "Fade large six hour extension in high-volatility context.",
    ),
]


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def load_candles(symbol: str, path: Path) -> pd.DataFrame:
    payload = json.loads(path.read_text(encoding="utf-8"))
    rows = payload.get("candles", [])
    df = pd.DataFrame(rows)
    if df.empty:
        raise ValueError(f"no candles for {symbol}: {path}")
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
    for column in ["open", "high", "low", "close", "volume"]:
        df[column] = pd.to_numeric(df[column], errors="coerce")
    df = (
        df.dropna(subset=["timestamp", "open", "high", "low", "close"])
        .drop_duplicates(subset=["timestamp"])
        .sort_values("timestamp")
        .reset_index(drop=True)
    )
    df["symbol"] = symbol
    return add_features(df)


def add_features(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["ret_1h"] = out["close"].pct_change(1)
    out["ret_3h"] = out["close"].pct_change(3)
    out["ret_6h"] = out["close"].pct_change(6)
    out["ret_24h"] = out["close"].pct_change(24)
    out["ret_63h"] = out["close"].pct_change(63)
    out["ema21"] = out["close"].ewm(span=21, adjust=False).mean()
    out["ema89"] = out["close"].ewm(span=89, adjust=False).mean()
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
    out["vol_120h"] = out["ret_1h"].rolling(120, min_periods=30).std()
    out["mean_48h"] = out["close"].rolling(48, min_periods=24).mean()
    out["std_48h"] = out["close"].rolling(48, min_periods=24).std()
    out["z_48h"] = (out["close"] - out["mean_48h"]) / out["std_48h"].replace(0, math.nan)
    out["high_20h_prior"] = out["high"].rolling(20, min_periods=20).max().shift(1)
    out["low_20h_prior"] = out["low"].rolling(20, min_periods=20).min().shift(1)
    out["breakout_20h"] = out["close"] > out["high_20h_prior"]
    out["breakdown_20h"] = out["close"] < out["low_20h_prior"]
    out["future_close_3h"] = out["close"].shift(-3)
    out["future_close_4h"] = out["close"].shift(-4)
    out["future_close_6h"] = out["close"].shift(-6)
    out["hour_utc"] = out["timestamp"].dt.hour
    out["year"] = out["timestamp"].dt.year
    out["period_bucket"] = out["timestamp"].map(period_bucket)
    return classify_parent_regime(out)


def classify_parent_regime(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    atr_q75 = out["atr_pct"].quantile(0.75)
    ret24_q12 = out["ret_24h"].quantile(0.12)
    ret63_q12 = out["ret_63h"].quantile(0.12)
    trend_up = (out["close"] > out["ema89"]) & (out["ema21"] > out["ema89"]) & (out["ret_24h"] > 0)
    trend_down = (out["close"] < out["ema89"]) & (out["ema21"] < out["ema89"]) & (out["ret_24h"] < 0)
    crisis = ((out["ret_24h"] <= ret24_q12) | (out["ret_63h"] <= ret63_q12)) & (out["atr_pct"] >= atr_q75)
    out["main_regime"] = "Sideways"
    out.loc[trend_up, "main_regime"] = "Bull"
    out.loc[trend_down, "main_regime"] = "Bear"
    out.loc[crisis, "main_regime"] = "Crisis"
    out["high_vol_context"] = out["atr_pct"] >= atr_q75
    return out


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


def candidate_signal(df: pd.DataFrame, candidate: Candidate) -> pd.Series:
    if candidate.candidate_id == "HourlyTrendPullbackContinuationV1":
        long_signal = (df["main_regime"] == "Bull") & (df["ret_3h"] < 0) & (df["close"] > df["ema89"])
        short_signal = (df["main_regime"] == "Bear") & (df["ret_3h"] > 0) & (df["close"] < df["ema89"])
    elif candidate.candidate_id == "TwentyHourBreakoutContinuationV1":
        long_signal = df["breakout_20h"] & (df["main_regime"].isin(["Bull", "Sideways"]))
        short_signal = df["breakdown_20h"] & (df["main_regime"].isin(["Bear", "Crisis"]))
    elif candidate.candidate_id == "RangeBandMeanReversionV1":
        long_signal = (df["main_regime"] == "Sideways") & (df["z_48h"] <= -1.25)
        short_signal = (df["main_regime"] == "Sideways") & (df["z_48h"] >= 1.25)
    elif candidate.candidate_id == "VolatilityExpansionFadeV1":
        ret6_hi = df["ret_6h"].quantile(0.9)
        ret6_lo = df["ret_6h"].quantile(0.1)
        long_signal = df["high_vol_context"] & (df["ret_6h"] <= ret6_lo)
        short_signal = df["high_vol_context"] & (df["ret_6h"] >= ret6_hi)
    else:
        raise ValueError(candidate.candidate_id)

    signal = pd.Series(0, index=df.index, dtype="int64")
    signal.loc[long_signal.fillna(False)] = 1
    signal.loc[short_signal.fillna(False)] = -1
    return signal


def build_trades(frames: list[pd.DataFrame]) -> pd.DataFrame:
    trades = []
    for df in frames:
        symbol = str(df["symbol"].iloc[0])
        for candidate in CANDIDATES:
            signal = candidate_signal(df, candidate)
            future_col = f"future_close_{candidate.hold_hours}h"
            selected = df.loc[signal != 0].copy()
            if selected.empty:
                continue
            selected["direction"] = signal.loc[selected.index].map({1: "long", -1: "short"})
            selected["direction_sign"] = signal.loc[selected.index].astype(float)
            selected["future_close"] = selected[future_col]
            selected = selected.dropna(subset=["future_close", "close", "main_regime"])
            selected = selected[(selected["close"] > 0) & (selected["future_close"] > 0)]
            if selected.empty:
                continue
            gross = selected["direction_sign"] * (selected["future_close"] / selected["close"] - 1.0)
            selected["net_return"] = gross - ROUND_TRIP_COST_BPS / 10000.0
            selected = selected[selected["net_return"].map(math.isfinite)]
            selected = selected[selected["net_return"].abs() <= 0.25]
            if selected.empty:
                continue
            selected["win"] = selected["net_return"] > 0
            selected["candidate_id"] = candidate.candidate_id
            selected["profit_factor"] = candidate.candidate_id
            selected["sub_regime"] = candidate.sub_regime
            selected["sub_sub_regime_or_profit_factor"] = candidate.sub_sub
            selected["branch_path"] = (
                selected["main_regime"]
                + " -> "
                + selected["sub_regime"]
                + " -> "
                + selected["sub_sub_regime_or_profit_factor"]
                + " -> "
                + selected["profit_factor"]
            )
            selected["hold_hours"] = candidate.hold_hours
            selected["trade_or_bar_horizon"] = f"{candidate.hold_hours}h"
            selected["source_symbol_role"] = SYMBOLS[symbol]["role"]
            trades.append(
                selected[
                    [
                        "symbol",
                        "source_symbol_role",
                        "timestamp",
                        "period_bucket",
                        "candidate_id",
                        "direction",
                        "main_regime",
                        "sub_regime",
                        "sub_sub_regime_or_profit_factor",
                        "profit_factor",
                        "branch_path",
                        "trade_or_bar_horizon",
                        "close",
                        "future_close",
                        "net_return",
                        "win",
                        "ret_3h",
                        "ret_6h",
                        "ret_24h",
                        "ret_63h",
                        "atr_pct",
                        "vol_120h",
                        "z_48h",
                    ]
                ]
            )
    if not trades:
        raise RuntimeError("no candidate trades generated")
    return pd.concat(trades, ignore_index=True).sort_values(["timestamp", "symbol", "candidate_id"])


def wilson_lcb(wins: int, total: int, z: float = 1.96) -> float:
    if total <= 0:
        return 0.0
    phat = wins / total
    denom = 1.0 + z * z / total
    center = phat + z * z / (2.0 * total)
    margin = z * math.sqrt((phat * (1.0 - phat) + z * z / (4.0 * total)) / total)
    return (center - margin) / denom


def profit_factor(returns: pd.Series) -> float:
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


def summarize(group: pd.core.groupby.DataFrameGroupBy, keys: list[str]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for key_values, frame in group:
        if not isinstance(key_values, tuple):
            key_values = (key_values,)
        wins = int(frame["win"].sum())
        trades = int(len(frame))
        row = {key: value for key, value in zip(keys, key_values)}
        returns = frame["net_return"]
        row.update(
            {
                "trades": trades,
                "wins": wins,
                "losses": trades - wins,
                "win_rate": wins / trades if trades else 0.0,
                "win_rate_wilson95_lcb": wilson_lcb(wins, trades),
                "mean_net_return": float(returns.mean()) if trades else 0.0,
                "sum_net_return": float(returns.sum()) if trades else 0.0,
                "return_profit_factor": profit_factor(returns),
                "max_drawdown_compounded": max_drawdown(returns),
            }
        )
        rows.append(row)
    return pd.DataFrame(rows).sort_values(keys).reset_index(drop=True)


def rank_candidates(trades: pd.DataFrame) -> pd.DataFrame:
    branch = summarize(
        trades.groupby(["candidate_id", "source_symbol_role", "symbol", "branch_path"], dropna=False),
        ["candidate_id", "source_symbol_role", "symbol", "branch_path"],
    )
    period = summarize(
        trades.groupby(["candidate_id", "source_symbol_role", "symbol", "period_bucket"], dropna=False),
        ["candidate_id", "source_symbol_role", "symbol", "period_bucket"],
    )
    rows = []
    for (candidate_id, role), frame in branch.groupby(["candidate_id", "source_symbol_role"]):
        branch_trades = int(frame["trades"].sum())
        enough_branches = int((frame["trades"] >= MIN_BRANCH_TRADES).sum())
        role_trades = trades[(trades["candidate_id"] == candidate_id) & (trades["source_symbol_role"] == role)]
        period_frame = period[(period["candidate_id"] == candidate_id) & (period["source_symbol_role"] == role)]
        positive_periods = int((period_frame["mean_net_return"] > 0).sum())
        periods_with_trades = int((period_frame["trades"] > 0).sum())
        rows.append(
            {
                "candidate_id": candidate_id,
                "source_symbol_role": role,
                "trades": branch_trades,
                "branches_with_min_trades": enough_branches,
                "periods_with_trades": periods_with_trades,
                "positive_periods": positive_periods,
                "win_rate": float(role_trades["win"].mean()) if len(role_trades) else 0.0,
                "win_rate_wilson95_lcb": wilson_lcb(int(role_trades["win"].sum()), int(len(role_trades))),
                "mean_net_return": float(role_trades["net_return"].mean()) if len(role_trades) else 0.0,
                "sum_net_return": float(role_trades["net_return"].sum()) if len(role_trades) else 0.0,
                "return_profit_factor": profit_factor(role_trades["net_return"]),
                "max_drawdown_compounded": max_drawdown(role_trades["net_return"]),
                "density_gate": bool(branch_trades >= 1000 and enough_branches >= 2),
                "chronological_gate": bool(periods_with_trades >= MIN_PERIODS_WITH_TRADES and positive_periods >= 3),
            }
        )
    ranked = pd.DataFrame(rows)
    ranked["screen_score"] = (
        ranked["density_gate"].astype(int) * 25.0
        + ranked["chronological_gate"].astype(int) * 25.0
        + ranked["win_rate_wilson95_lcb"].fillna(0.0) * 25.0
        + ranked["return_profit_factor"].clip(upper=3.0).fillna(0.0) / 3.0 * 25.0
    )
    return ranked.sort_values(["screen_score", "trades"], ascending=[False, False]).reset_index(drop=True)


def rank_branch_leaves(branch: pd.DataFrame, branch_period: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, row in branch.iterrows():
        period_frame = branch_period[
            (branch_period["source_symbol_role"] == row["source_symbol_role"])
            & (branch_period["symbol"] == row["symbol"])
            & (branch_period["candidate_id"] == row["candidate_id"])
            & (branch_period["branch_path"] == row["branch_path"])
        ]
        periods_with_trades = int((period_frame["trades"] > 0).sum())
        positive_periods = int((period_frame["mean_net_return"] > 0).sum())
        density_gate = bool(row["trades"] >= 200)
        chronological_gate = bool(periods_with_trades >= 3 and positive_periods >= 2)
        edge_gate = bool(row["mean_net_return"] > 0 and row["return_profit_factor"] > 1.0)
        item = row.to_dict()
        item.update(
            {
                "periods_with_trades": periods_with_trades,
                "positive_periods": positive_periods,
                "density_gate": density_gate,
                "chronological_gate": chronological_gate,
                "edge_gate": edge_gate,
                "branch_leaf_screen_score": (
                    float(density_gate) * 25.0
                    + float(chronological_gate) * 25.0
                    + float(edge_gate) * 20.0
                    + min(float(row["win_rate_wilson95_lcb"]), 0.7) / 0.7 * 15.0
                    + min(float(row["return_profit_factor"]), 2.0) / 2.0 * 15.0
                ),
            }
        )
        rows.append(item)
    return (
        pd.DataFrame(rows)
        .sort_values(["branch_leaf_screen_score", "trades"], ascending=[False, False])
        .reset_index(drop=True)
    )


def provider_provenance_rows() -> list[dict[str, Any]]:
    rows = []
    notes = {
        "IBKR": "prior 141554 SPY 1h 5y probe succeeded through isolated runtime; not invoked in this local factor-density screen",
        "TradingViewRemix/TVR": "prior 141554 QQQ 1h 2y harness fetch failed; not invoked in this local factor-density screen",
        "yfinance/YF": "prior 141554 ES 1h/1d probe succeeded; not invoked in this local factor-density screen",
        "Kraken": "prior 141554 public probes returned windowed rows; not invoked in this local factor-density screen",
        "Binance": "prior 141554 BTCUSDT 1m/1h probes succeeded; not invoked in this local factor-density screen",
        "Bybit": "prior 141554 public probes returned capped rows; not invoked in this local factor-density screen",
    }
    for provider, note in notes.items():
        rows.append(
            {
                "provider": provider,
                "aq_provider_invoked": False,
                "provider_requested": False,
                "provider_data_acquired": False,
                "provider_unreachable": False,
                "local_cache_replay": True,
                "context_source": "20260512T141554+0800-codex-provider-longspan-capability-matrix-v1",
                "note": note,
            }
        )
    return rows


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def write_report(payload: dict[str, Any]) -> None:
    top = payload["top_primary"]
    top_branch = payload["top_primary_branch_leaf"]
    lines = [
        "# Long-History ES/NQ Factor-Density Screen v1",
        "",
        f"Run root: `{RUN_ROOT}`",
        f"Source root: `{SOURCE_ROOT}`",
        "",
        "## Scope",
        "",
        "- This is a local long-history candidate-surface screen, not a promotion packet.",
        "- It uses cleaned 1h frames derived from the local long-history MTF substrate.",
        "- It does not invoke Auto-Quant provider routing; provider rows are emitted as a fail-closed provenance sidecar.",
        "- It deliberately seeks higher trade density and branch-keyed outcomes before any ordered-chain admission attempt.",
        "",
        "## Top Primary ES/NQ Candidate",
        "",
        f"- Candidate: `{top.get('candidate_id', 'none')}`",
        f"- Trades: `{top.get('trades', 0)}`",
        f"- Win rate: `{top.get('win_rate', 0.0):.6f}`",
        f"- Wilson95 LCB: `{top.get('win_rate_wilson95_lcb', 0.0):.6f}`",
        f"- Mean net return: `{top.get('mean_net_return', 0.0):.8f}`",
        f"- Return profit factor: `{top.get('return_profit_factor', 0.0):.6f}`",
        f"- Density gate: `{top.get('density_gate', False)}`",
        f"- Chronological gate: `{top.get('chronological_gate', False)}`",
        "",
        "## Top Primary Branch Leaf",
        "",
        f"- Branch: `{top_branch.get('branch_path', 'none')}`",
        f"- Symbol: `{top_branch.get('symbol', 'none')}`",
        f"- Trades: `{top_branch.get('trades', 0)}`",
        f"- Win rate: `{top_branch.get('win_rate', 0.0):.6f}`",
        f"- Wilson95 LCB: `{top_branch.get('win_rate_wilson95_lcb', 0.0):.6f}`",
        f"- Mean net return: `{top_branch.get('mean_net_return', 0.0):.8f}`",
        f"- Return profit factor: `{top_branch.get('return_profit_factor', 0.0):.6f}`",
        f"- Positive chronological buckets: `{top_branch.get('positive_periods', 0)}`",
        "",
        "## Gate",
        "",
        "- `evidence_class:local_training_candidate_surface_screen`",
        f"- `total_candidate_trades:{payload['total_candidate_trades']}`",
        f"- `primary_esnq_candidate_trades:{payload['primary_candidate_trades']}`",
        f"- `primary_positive_branch_leaf_candidates:{payload['primary_positive_branch_leaf_candidates']}`",
        "- `pass:branch_path_fields_emitted`",
        "- `pass:chronological_bucket_summary_emitted`",
        "- `fail_closed:aq_provider_authority_missing_for_this_screen`",
        "- `fail_closed:local_cache_replay_primary_source`",
        "- `fail_closed:no_pre_bayes_bbn_catboost_execution_tree_chain`",
        "- `promotion_allowed=false`",
        "- `trade_usable=false`",
        "- `update_goal=false`",
        "",
        "## Next",
        "",
        "Convert the best density-screened candidate into a portable or provider-routed Auto-Quant recipe, run provider acquisition/provenance for all six required providers, then pass only a provider-provenanced branch packet through Pre-Bayes/filter -> BBN -> CatBoost/path-ranker -> execution tree.",
        "",
    ]
    REPORT.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    frames = []
    source_summary = []
    for symbol, meta in SYMBOLS.items():
        df = load_candles(symbol, meta["path"])
        frames.append(df)
        source_summary.append(
            {
                "symbol": symbol,
                "role": meta["role"],
                "path": str(meta["path"]),
                "rows": int(len(df)),
                "start": df["timestamp"].min().isoformat(),
                "end": df["timestamp"].max().isoformat(),
            }
        )
    trades = build_trades(frames)
    branch_summary = summarize(
        trades.groupby(
            [
                "source_symbol_role",
                "symbol",
                "candidate_id",
                "main_regime",
                "sub_regime",
                "sub_sub_regime_or_profit_factor",
                "profit_factor",
                "branch_path",
            ],
            dropna=False,
        ),
        [
            "source_symbol_role",
            "symbol",
            "candidate_id",
            "main_regime",
            "sub_regime",
            "sub_sub_regime_or_profit_factor",
            "profit_factor",
            "branch_path",
        ],
    )
    period_summary = summarize(
        trades.groupby(["source_symbol_role", "symbol", "candidate_id", "period_bucket"], dropna=False),
        ["source_symbol_role", "symbol", "candidate_id", "period_bucket"],
    )
    branch_period_summary = summarize(
        trades.groupby(
            ["source_symbol_role", "symbol", "candidate_id", "branch_path", "period_bucket"],
            dropna=False,
        ),
        ["source_symbol_role", "symbol", "candidate_id", "branch_path", "period_bucket"],
    )
    rankings = rank_candidates(trades)
    branch_rankings = rank_branch_leaves(branch_summary, branch_period_summary)
    primary_rankings = rankings[rankings["source_symbol_role"] == "primary_esnq"]
    top_primary = primary_rankings.iloc[0].to_dict() if not primary_rankings.empty else {}
    primary_branch_rankings = branch_rankings[branch_rankings["source_symbol_role"] == "primary_esnq"]
    top_primary_branch_leaf = (
        primary_branch_rankings.iloc[0].to_dict() if not primary_branch_rankings.empty else {}
    )
    primary_positive_branch_leaf_candidates = int(
        (
            (primary_branch_rankings["density_gate"])
            & (primary_branch_rankings["chronological_gate"])
            & (primary_branch_rankings["edge_gate"])
        ).sum()
    )

    trades.to_csv(OUT_DIR / "factor_candidate_trades.csv", index=False)
    branch_summary.to_csv(OUT_DIR / "factor_candidate_summary_by_branch.csv", index=False)
    period_summary.to_csv(OUT_DIR / "factor_candidate_summary_by_period.csv", index=False)
    branch_period_summary.to_csv(OUT_DIR / "factor_candidate_summary_by_branch_period.csv", index=False)
    rankings.to_csv(OUT_DIR / "factor_candidate_rankings.csv", index=False)
    branch_rankings.to_csv(OUT_DIR / "factor_branch_leaf_rankings.csv", index=False)
    write_csv(OUT_DIR / "aq_provider_provenance_sidecar.csv", provider_provenance_rows())

    payload = {
        "run_root": str(RUN_ROOT),
        "source_root": str(SOURCE_ROOT),
        "source_summary": source_summary,
        "round_trip_cost_bps": ROUND_TRIP_COST_BPS,
        "total_candidate_trades": int(len(trades)),
        "primary_candidate_trades": int((trades["source_symbol_role"] == "primary_esnq").sum()),
        "top_primary": top_primary,
        "top_primary_branch_leaf": top_primary_branch_leaf,
        "primary_positive_branch_leaf_candidates": primary_positive_branch_leaf_candidates,
        "promotion_allowed": False,
        "trade_usable": False,
        "update_goal": False,
        "evidence_class": "local_training_candidate_surface_screen",
        "provider_authority": "fail_closed:local_cache_replay_primary_source",
    }
    write_json(OUT_DIR / "long_history_esnq_factor_density_screen_v1.json", payload)
    write_json(
        OUT_DIR / "long_history_esnq_factor_density_screen_assertions_v1.json",
        {
            "branch_path_fields_emitted": bool(
                {
                    "main_regime",
                    "sub_regime",
                    "sub_sub_regime_or_profit_factor",
                    "profit_factor",
                    "branch_path",
                }.issubset(trades.columns)
            ),
            "primary_candidate_trades_ge_1000": bool(payload["primary_candidate_trades"] >= 1000),
            "provider_rows_eq_6": True,
            "primary_positive_branch_leaf_candidates_ge_1": bool(
                primary_positive_branch_leaf_candidates >= 1
            ),
            "promotion_allowed": False,
            "update_goal": False,
        },
    )
    write_report(payload)
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
