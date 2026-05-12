from __future__ import annotations

import contextlib
import io
import json
import math
import sys
from pathlib import Path
from typing import Any

import pandas as pd
from freqtrade.configuration import Configuration
from freqtrade.enums import RunMode
from freqtrade.optimize.backtesting import Backtesting


REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = RUN_ROOT / "regime-branch-winrate-v1"
COMMAND_OUTPUT = RUN_ROOT / "command-output"
CHECKS = RUN_ROOT / "checks"
SOURCE_ROOT = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs/"
    "20260512T135257+0800-codex-long-history-es-nq-1m-aq-stage-v1"
)
SOURCE_WORKSPACE = SOURCE_ROOT / "workspace/auto-quant"
STRATEGY = "TomacNQ_KillzoneBreakout"


sys.path.insert(0, str(SOURCE_WORKSPACE))
import run_tomac  # noqa: E402


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def run_backtest_with_trades() -> tuple[dict[str, Any], pd.DataFrame]:
    args = {
        "config": [str(SOURCE_WORKSPACE / "config.tomac.json")],
        "user_data_dir": str(SOURCE_WORKSPACE / "user_data"),
        "datadir": str(SOURCE_WORKSPACE / "user_data/data"),
        "strategy": STRATEGY,
        "strategy_path": str(SOURCE_WORKSPACE / "user_data/strategies_external"),
        "export": "none",
        "exportfilename": None,
        "cache": "none",
    }
    config = Configuration(args, RunMode.BACKTEST).get_config()
    exchange = run_tomac._build_exchange_with_synthetic_pairs(config)
    bt = Backtesting(config, exchange=exchange)
    captured = io.StringIO()
    with contextlib.redirect_stdout(captured):
        bt.start()
    (COMMAND_OUTPUT / "01_rerun_135257_trade_export_table.out").write_text(
        captured.getvalue(), encoding="utf-8"
    )
    metrics = run_tomac.extract_metrics(bt.results, STRATEGY)
    raw_trades = bt.all_bt_content.get(STRATEGY, {}).get("results")
    if isinstance(raw_trades, pd.DataFrame):
        trades = raw_trades.copy()
    else:
        trades = pd.DataFrame()
    return metrics, trades


def load_context(pair: str) -> pd.DataFrame:
    stem = pair.replace("/", "_")
    path = SOURCE_WORKSPACE / "user_data/data" / f"{stem}-1h.feather"
    df = pd.read_feather(path)
    df["context_date"] = pd.to_datetime(df["date"], unit="ms", utc=True)
    df = df.sort_values("context_date").reset_index(drop=True)
    df["ema21"] = df["close"].ewm(span=21, adjust=False).mean()
    df["ema89"] = df["close"].ewm(span=89, adjust=False).mean()
    prev_close = df["close"].shift(1)
    true_range = pd.concat(
        [
            df["high"] - df["low"],
            (df["high"] - prev_close).abs(),
            (df["low"] - prev_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    df["atr14"] = true_range.rolling(14, min_periods=14).mean()
    df["atr_pct"] = df["atr14"] / df["close"].replace(0.0, math.nan)
    df["ret_24h"] = df["close"].pct_change(24)
    df["ret_63h"] = df["close"].pct_change(63)
    df["rolling_vol_120h"] = df["close"].pct_change().rolling(120, min_periods=30).std()
    df["breakout_20h"] = df["close"] > df["high"].rolling(20, min_periods=20).max().shift(1)
    df["breakdown_20h"] = df["close"] < df["low"].rolling(20, min_periods=20).min().shift(1)
    return df[
        [
            "context_date",
            "close",
            "ema21",
            "ema89",
            "atr_pct",
            "ret_24h",
            "ret_63h",
            "rolling_vol_120h",
            "breakout_20h",
            "breakdown_20h",
        ]
    ]


def classify_context(row: pd.Series) -> dict[str, str]:
    trend_up = bool(row["close"] > row["ema89"] and row["ema21"] > row["ema89"])
    trend_down = bool(row["close"] < row["ema89"] and row["ema21"] < row["ema89"])
    high_vol = bool(row["atr_pct"] >= 0.012 or row["rolling_vol_120h"] >= 0.01)
    sharp_down = bool(row["ret_24h"] <= -0.025)
    if trend_down and (high_vol or sharp_down):
        main = "Crisis"
        sub = "HighVolDrawdown"
        sub_sub = "KillzoneBreakoutStressRecovery"
    elif trend_up:
        main = "Bull"
        sub = "TrendAlignedBreakout"
        sub_sub = "OneHourMomentumContinuation"
    elif trend_down:
        main = "Bear"
        sub = "CountertrendBreakout"
        sub_sub = "OneHourWeakTrendContinuation"
    else:
        main = "Sideways"
        sub = "RangeBreakoutAttempt"
        sub_sub = "OneHourRangeExpansion"
    return {
        "main_regime": main,
        "sub_regime": sub,
        "sub_sub_regime_or_profit_factor": sub_sub,
        "profit_factor": STRATEGY,
        "branch_path": f"{main} -> {sub} -> {sub_sub} -> {STRATEGY}",
    }


def attach_entry_regimes(trades: pd.DataFrame) -> pd.DataFrame:
    if trades.empty:
        return trades
    trades = trades.copy()
    date_col = "open_date" if "open_date" in trades.columns else "open_timestamp"
    trades["entry_ts"] = pd.to_datetime(trades[date_col], utc=True)
    if "profit_ratio" in trades.columns:
        trades["profit_ratio_numeric"] = pd.to_numeric(trades["profit_ratio"], errors="coerce")
    elif "profit_abs" in trades.columns:
        trades["profit_ratio_numeric"] = pd.to_numeric(trades["profit_abs"], errors="coerce")
    else:
        trades["profit_ratio_numeric"] = 0.0
    frames = []
    for pair, group in trades.groupby("pair", dropna=False):
        context = load_context(str(pair))
        merged = pd.merge_asof(
            group.sort_values("entry_ts"),
            context,
            left_on="entry_ts",
            right_on="context_date",
            direction="backward",
        )
        labels = pd.DataFrame([classify_context(row) for _, row in merged.iterrows()])
        frames.append(pd.concat([merged.reset_index(drop=True), labels], axis=1))
    out = pd.concat(frames, ignore_index=True)
    out["win"] = out["profit_ratio_numeric"] > 0
    out["period_bucket"] = out["entry_ts"].map(period_bucket)
    return out


def period_bucket(ts: pd.Timestamp) -> str:
    year = ts.year
    if year < 2020:
        return "pre_2020"
    if 2020 <= year <= 2022:
        return "2020_2022"
    if 2023 <= year <= 2024:
        return "2023_2024"
    return "2025_2026"


def wilson_lower_bound(wins: int, total: int, z: float = 1.96) -> float:
    if total <= 0:
        return 0.0
    phat = wins / total
    denom = 1 + z * z / total
    center = phat + z * z / (2 * total)
    margin = z * math.sqrt((phat * (1 - phat) + z * z / (4 * total)) / total)
    return (center - margin) / denom


def summarize(grouped: pd.core.groupby.DataFrameGroupBy, key_columns: list[str]) -> pd.DataFrame:
    rows = []
    for keys, frame in grouped:
        if not isinstance(keys, tuple):
            keys = (keys,)
        wins = int(frame["win"].sum())
        total = int(len(frame))
        row = {column: value for column, value in zip(key_columns, keys)}
        row.update(
            {
                "trades": total,
                "wins": wins,
                "losses": int(total - wins),
                "win_rate": wins / total if total else 0.0,
                "win_rate_wilson95_lcb": wilson_lower_bound(wins, total),
                "mean_profit_ratio": float(frame["profit_ratio_numeric"].mean()) if total else 0.0,
                "sum_profit_ratio": float(frame["profit_ratio_numeric"].sum()) if total else 0.0,
            }
        )
        rows.append(row)
    return pd.DataFrame(rows).sort_values(key_columns).reset_index(drop=True)


def write_report(payload: dict[str, Any]) -> None:
    lines = [
        "# 135257 Regime/Branch Win-Rate Readback v1",
        "",
        f"Source root: `{payload['source_root']}`",
        "",
        "## Result",
        "",
        f"- Trade rows exported: `{payload['trade_rows']}`",
        f"- Pair count: `{payload['pair_count']}`",
        f"- Branch count: `{payload['branch_count']}`",
        f"- Promotion allowed: `{str(payload['promotion_allowed']).lower()}`",
        "",
        "## Key Readback",
        "",
        "- The run reuses the already-registered `135257` isolated Auto-Quant workspace.",
        "- Trade-level rows are now keyed by `main_regime -> sub_regime -> sub_sub_regime_or_profit_factor -> profit_factor` using entry-time long-history 1h context derived from the staged 1m substrate.",
        "- This is a screening readback, not a Board B promotion packet: the branch labels are heuristic entry-context labels and have not yet passed Board A Pre-Bayes/BBN/CatBoost/execution-tree admission.",
        "",
        "## Gates",
        "",
    ]
    lines.extend(f"- `{gate}`" for gate in payload["gates"])
    lines.append("")
    (OUT_DIR / "135257_regime_branch_winrate_readback_v1.md").write_text(
        "\n".join(lines), encoding="utf-8"
    )


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    COMMAND_OUTPUT.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)
    metrics, trades = run_backtest_with_trades()
    trades.to_csv(OUT_DIR / "135257_raw_trades_export.csv", index=False)
    enriched = attach_entry_regimes(trades)
    enriched.to_csv(OUT_DIR / "135257_trades_with_entry_regime.csv", index=False)
    branch_summary = summarize(
        enriched.groupby(
            [
                "pair",
                "main_regime",
                "sub_regime",
                "sub_sub_regime_or_profit_factor",
                "profit_factor",
                "branch_path",
            ],
            dropna=False,
        ),
        [
            "pair",
            "main_regime",
            "sub_regime",
            "sub_sub_regime_or_profit_factor",
            "profit_factor",
            "branch_path",
        ],
    )
    period_summary = summarize(
        enriched.groupby(["pair", "period_bucket"], dropna=False),
        ["pair", "period_bucket"],
    )
    branch_summary.to_csv(OUT_DIR / "regime_branch_winrate_summary.csv", index=False)
    period_summary.to_csv(OUT_DIR / "chronological_bucket_summary.csv", index=False)
    pair_summary = metrics["per_pair"]
    gates = [
        "support_once:135257_regime_branch_winrate_readback_v1",
        "evidence_class:market_factor_screening_sample_not_promotion",
        f"pass:trade_rows_exported_{len(enriched)}",
        f"pass:branch_paths_populated_{int(enriched['branch_path'].notna().sum())}",
        f"pass:branch_summary_rows_{len(branch_summary)}",
        "pass:chronological_bucket_summary_written",
        "fail_closed:heuristic_entry_regime_not_board_a_accepted_regime",
        "fail_closed:not_yet_pre_bayes_bbn_catboost_execution_tree",
        "fail_closed:not_yet_provider_context_matrix_validated",
        "promotion_allowed=false",
        "trade_usable=false",
        "update_goal=false",
    ]
    payload = {
        "run_root": str(RUN_ROOT.relative_to(REPO)),
        "source_root": str(SOURCE_ROOT.relative_to(REPO)),
        "source_workspace": str(SOURCE_WORKSPACE.relative_to(REPO)),
        "strategy": STRATEGY,
        "trade_rows": int(len(enriched)),
        "pair_count": int(enriched["pair"].nunique()) if not enriched.empty else 0,
        "branch_count": int(enriched["branch_path"].nunique()) if not enriched.empty else 0,
        "aggregate_metrics": metrics["aggregate"],
        "per_pair_metrics": pair_summary,
        "artifacts": {
            "raw_trades": str((OUT_DIR / "135257_raw_trades_export.csv").relative_to(REPO)),
            "trades_with_entry_regime": str(
                (OUT_DIR / "135257_trades_with_entry_regime.csv").relative_to(REPO)
            ),
            "branch_summary": str((OUT_DIR / "regime_branch_winrate_summary.csv").relative_to(REPO)),
            "period_summary": str((OUT_DIR / "chronological_bucket_summary.csv").relative_to(REPO)),
        },
        "gates": gates,
        "promotion_allowed": False,
        "trade_usable": False,
        "update_goal": False,
    }
    _write_json(OUT_DIR / "135257_regime_branch_winrate_readback_v1.json", payload)
    write_report(payload)
    assertions = {
        "trade_rows_gt_0": len(enriched) > 0,
        "pair_count_ge_2": payload["pair_count"] >= 2,
        "branch_paths_populated": bool(enriched["branch_path"].notna().all()) if not enriched.empty else False,
        "promotion_false": payload["promotion_allowed"] is False,
    }
    (CHECKS / "135257_regime_branch_winrate_readback_v1_assertions.out").write_text(
        "\n".join(f"{key}={value}" for key, value in assertions.items()) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"payload": payload, "assertions": assertions}, indent=2, sort_keys=True))
    return 0 if all(assertions.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
