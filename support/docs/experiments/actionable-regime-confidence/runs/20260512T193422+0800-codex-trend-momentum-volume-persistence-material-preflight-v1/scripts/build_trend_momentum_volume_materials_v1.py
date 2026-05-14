#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import shutil
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[4]
SOURCE_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs/20260512T184139+0800-codex-vwap-session-liquidity-six-provider-aq-v1/data/normalized"


@dataclass(frozen=True)
class Provider:
    provider: str
    label: str
    symbol: str
    timeframe: str
    source_name: str
    replay_name: str


@dataclass(frozen=True)
class Branch:
    branch_id: str
    class_name: str
    path: str
    direction: str
    tag: str
    roi: str
    stoploss: str
    entry_condition: str
    exit_condition: str


PROVIDERS = [
    Provider("Binance", "Binance BTCUSDT 1h", "BTC", "1h", "binance_btcusdt_1h.normalized.csv", "binance_btcusdt_1h.normalized.csv"),
    Provider("Bybit", "Bybit BTCUSDT 1h", "BTC", "1h", "bybit_linear_btcusdt_1h.normalized.csv", "bybit_linear_btcusdt_1h.normalized.csv"),
    Provider("IBKR", "IBKR SPY 1h", "SPY", "1h", "ibkr_spy_1h_90d.normalized.csv", "ibkr_spy_1h_90d.normalized.csv"),
    Provider("Kraken", "Kraken XBTUSD 1h", "BTC", "1h", "kraken_futures_pfxbtusd_1h.normalized.csv", "kraken_futures_pfxbtusd_1h.normalized.csv"),
    Provider("TradingViewRemix/TVR", "TradingViewRemix/TVR BTC-USD 1h", "BTC", "1h", "tvr_btc_usd_1h.normalized.csv", "tvr_btc_usd_1h.normalized.csv"),
    Provider("yfinance/YF", "yfinance/YF SPY 1h", "SPY", "1h", "yahoo_spy_1h.normalized.csv", "yahoo_spy_1h.normalized.csv"),
]

BRANCHES = [
    Branch(
        "volume_impulse_reclaim_long_v1",
        "VolumeImpulseReclaimLongV1",
        "TrendExpansion -> MomentumContinuation -> volume_impulse_pullback -> volume_impulse_reclaim_long_v1",
        "long",
        "volume_impulse_reclaim_long_v1",
        "0.016",
        "-0.032",
        '(dataframe["ema12"] > dataframe["ema48"]) & (dataframe["close"] > dataframe["ema12"]) & (dataframe["rsi14"] > 51) & (dataframe["volume_z"] > 0.15) & (dataframe["close"] > dataframe["open"])',
        '(dataframe["rsi14"] > 74) | (dataframe["close"] < dataframe["ema12"] * 0.985)',
    ),
    Branch(
        "ema_rsi_persistence_long_v1",
        "EmaRsiPersistenceLongV1",
        "TrendExpansion -> MomentumContinuation -> ema_rsi_persistence -> ema_rsi_persistence_long_v1",
        "long",
        "ema_rsi_persistence_long_v1",
        "0.014",
        "-0.028",
        '(dataframe["ema12"] > dataframe["ema48"]) & (dataframe["ema12"].diff() > 0) & (dataframe["rsi14"].between(52, 68)) & (dataframe["close"] > dataframe["close"].shift(3))',
        '(dataframe["rsi14"] > 72) | (dataframe["close"] < dataframe["ema24"])',
    ),
    Branch(
        "compression_breakout_followthrough_long_v1",
        "CompressionBreakoutFollowthroughLongV1",
        "VolatilityCompression -> MomentumBreakout -> compression_breakout_followthrough -> compression_breakout_followthrough_long_v1",
        "long",
        "compression_breakout_followthrough_long_v1",
        "0.018",
        "-0.035",
        '(dataframe["atr_pct"] < dataframe["atr_pct"].rolling(96, min_periods=24).median()) & (dataframe["close"] > dataframe["high"].shift(1).rolling(24, min_periods=8).max()) & (dataframe["volume_z"] > -0.25)',
        '(dataframe["close"] < dataframe["ema24"]) | (dataframe["rsi14"] > 76)',
    ),
    Branch(
        "momentum_failure_guard_v1",
        "MomentumFailureGuardV1",
        "Transition -> ContinuationFailureGuard -> momentum_failure_guard -> momentum_failure_guard_v1",
        "short",
        "momentum_failure_guard_v1",
        "0.012",
        "-0.026",
        '(dataframe["ema12"] < dataframe["ema48"]) & (dataframe["rsi14"] < 48) & (dataframe["close"] < dataframe["ema24"]) & (dataframe["close"] < dataframe["open"])',
        '(dataframe["rsi14"] < 28) | (dataframe["close"] > dataframe["ema24"] * 1.012)',
    ),
]


def strategy_source(branch: Branch) -> str:
    enter_col = "enter_short" if branch.direction == "short" else "enter_long"
    exit_col = "exit_short" if branch.direction == "short" else "exit_long"
    can_short = "True" if branch.direction == "short" else "False"
    return f'''from freqtrade.strategy import IStrategy
from pandas import DataFrame
import talib.abstract as ta


class {branch.class_name}(IStrategy):
    timeframe = "1h"
    can_short = {can_short}
    minimal_roi = {{"0": {branch.roi}, "24": 0}}
    stoploss = {branch.stoploss}
    startup_candle_count = 120

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["ema12"] = ta.EMA(dataframe, timeperiod=12)
        dataframe["ema24"] = ta.EMA(dataframe, timeperiod=24)
        dataframe["ema48"] = ta.EMA(dataframe, timeperiod=48)
        dataframe["atr14"] = ta.ATR(dataframe, timeperiod=14)
        dataframe["rsi14"] = ta.RSI(dataframe, timeperiod=14)
        dataframe["atr_pct"] = dataframe["atr14"] / dataframe["close"].replace(0, 1)
        volume_std = dataframe["volume"].rolling(48, min_periods=12).std().replace(0, 1)
        dataframe["volume_z"] = (
            dataframe["volume"] - dataframe["volume"].rolling(48, min_periods=12).mean()
        ) / volume_std
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        condition = {branch.entry_condition}
        dataframe.loc[condition, ["{enter_col}", "enter_tag"]] = (1, "{branch.tag}")
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[{branch.exit_condition}, ["{exit_col}", "exit_tag"]] = (1, "{branch.tag}_exit")
        return dataframe
'''


def provider_slug(provider: str) -> str:
    return provider.lower().replace("/", "-").replace(" ", "-")


def main() -> int:
    agent_dir = ROOT / "agent-material"
    data_dir = ROOT / "data/normalized"
    summaries = ROOT / "summaries"
    checks = ROOT / "checks"
    for directory in (agent_dir, data_dir, summaries, checks):
        directory.mkdir(parents=True, exist_ok=True)

    provider_rows = []
    for provider in PROVIDERS:
        source = SOURCE_ROOT / provider.source_name
        replay = data_dir / provider.replay_name
        if not source.exists():
            raise FileNotFoundError(source)
        shutil.copy2(source, replay)
        provider_rows.append(
            {
                "provider": provider.provider,
                "provider_label": provider.label,
                "symbol": provider.symbol,
                "timeframe": provider.timeframe,
                "source_path": str(source),
                "replay_path": str(replay),
                "provider_data_acquired_this_step": "false",
                "local_cache_replay": "true",
            }
        )

    material_rows = []
    material_paths = []
    for branch in BRANCHES:
        strategy_path = agent_dir / f"{branch.class_name}.py"
        strategy_path.write_text(strategy_source(branch), encoding="utf-8")
        parts = [part.strip() for part in branch.path.split(" -> ")]
        for provider in PROVIDERS:
            replay = data_dir / provider.replay_name
            package_id = f"tmvp-{branch.branch_id}-{provider_slug(provider.provider)}-1h-v1"
            material_path = agent_dir / f"{package_id}.material.json"
            material = {
                "package_id": package_id,
                "title": f"TMVP {branch.branch_id} - {provider.label}",
                "symbol": provider.symbol,
                "timeframe": provider.timeframe,
                "timerange": "20250101-20260512",
                "direction": branch.direction,
                "data_path": str(replay),
                "strategy_source_path": str(strategy_path),
                "strategy_class_name": branch.class_name,
                "strategy_brief": "Board B trend-momentum volume-persistence branch-keyed profitability material.",
                "evaluation_priority": [
                    "branch_trade_density",
                    "regime_conditioned_win_rate",
                    "profit_factor",
                    "cross_provider_survival",
                    "cost_slippage_robustness",
                ],
                "consumer_evidence_profile": {
                    "branch_path": branch.path,
                    "regime_profit_branch_path": branch.path,
                    "branch_id": branch.branch_id,
                    "main_regime": parts[0],
                    "sub_regime": parts[1],
                    "sub_sub_regime_or_profit_factor": parts[2],
                    "profit_factor": parts[3],
                    "provider": provider.provider,
                    "promotion_allowed": False,
                    "trade_usable": False,
                    "update_goal": False,
                },
                "notes": [
                    f"source_provider={provider.label}",
                    f"branch_path={branch.path}",
                    "provider_data_acquired_this_step=false",
                    "local_cache_replay=true",
                    "material_preflight_only=true",
                    "promotion_allowed=false until AQ dispatch/rank and ordered downstream chain pass",
                ],
            }
            material_path.write_text(json.dumps(material, indent=2) + "\n", encoding="utf-8")
            material_paths.append(str(material_path))
            material_rows.append(
                {
                    "provider": provider.provider,
                    "provider_label": provider.label,
                    "branch_id": branch.branch_id,
                    "branch_path": branch.path,
                    "main_regime": parts[0],
                    "sub_regime": parts[1],
                    "sub_sub_regime_or_profit_factor": parts[2],
                    "profit_factor": parts[3],
                    "material_path": str(material_path),
                    "strategy_path": str(strategy_path),
                    "symbol": provider.symbol,
                    "direction": branch.direction,
                }
            )

    provider_matrix = summaries / "provider_provenance_matrix.csv"
    with provider_matrix.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(provider_rows[0].keys()))
        writer.writeheader()
        writer.writerows(provider_rows)

    material_matrix = summaries / "material_paths.csv"
    with material_matrix.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(material_rows[0].keys()))
        writer.writeheader()
        writer.writerows(material_rows)

    summary = {
        "root": str(ROOT),
        "material_count": len(material_rows),
        "provider_count": len(PROVIDERS),
        "branch_count": len(BRANCHES),
        "branch_paths": [branch.path for branch in BRANCHES],
        "material_paths": material_paths,
        "provider_data_acquired_this_step": False,
        "local_cache_replay": True,
        "promotion_allowed": False,
        "trade_usable": False,
        "update_goal": False,
    }
    (summaries / "trend_momentum_volume_material_preflight_v1.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )

    assertions = [
        f"material_count={len(material_rows)}",
        f"provider_count={len(PROVIDERS)}",
        f"branch_count={len(BRANCHES)}",
        f"expected_material_count={len(PROVIDERS) * len(BRANCHES)}",
        "branch_keyed_by_construction=True",
        "new_provider_fetch=False",
        "local_cache_replay=True",
        "promotion_allowed=False",
        "trade_usable=False",
        "update_goal=False",
    ]
    (checks / "trend_momentum_volume_material_preflight_assertions.out").write_text(
        "\n".join(assertions) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
