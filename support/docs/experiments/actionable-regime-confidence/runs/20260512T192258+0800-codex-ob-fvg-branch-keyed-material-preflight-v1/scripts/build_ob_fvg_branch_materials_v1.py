#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import shutil
from pathlib import Path


REPO = Path(__file__).resolve().parents[6]
ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs/20260512T184139+0800-codex-vwap-session-liquidity-six-provider-aq-v1"

PROVIDERS = [
    {
        "provider": "Binance",
        "provider_label": "Binance BTCUSDT 1h",
        "symbol": "BTC",
        "source": SOURCE_ROOT / "data/normalized/binance_btcusdt_1h.normalized.csv",
        "dest": "binance_btcusdt_1h.normalized.csv",
    },
    {
        "provider": "Bybit",
        "provider_label": "Bybit BTCUSDT 1h",
        "symbol": "BTC",
        "source": SOURCE_ROOT / "data/normalized/bybit_linear_btcusdt_1h.normalized.csv",
        "dest": "bybit_linear_btcusdt_1h.normalized.csv",
    },
    {
        "provider": "IBKR",
        "provider_label": "IBKR SPY 1h",
        "symbol": "SPY",
        "source": SOURCE_ROOT / "data/normalized/ibkr_spy_1h_90d.normalized.csv",
        "dest": "ibkr_spy_1h_90d.normalized.csv",
    },
    {
        "provider": "Kraken",
        "provider_label": "Kraken XBTUSD 1h",
        "symbol": "BTC",
        "source": SOURCE_ROOT / "data/normalized/kraken_futures_pfxbtusd_1h.normalized.csv",
        "dest": "kraken_futures_pfxbtusd_1h.normalized.csv",
    },
    {
        "provider": "TradingViewRemix/TVR",
        "provider_label": "TradingViewRemix/TVR BTC-USD 1h",
        "symbol": "BTC",
        "source": SOURCE_ROOT / "data/normalized/tvr_btc_usd_1h.normalized.csv",
        "dest": "tvr_btc_usd_1h.normalized.csv",
    },
    {
        "provider": "yfinance/YF",
        "provider_label": "yfinance/YF SPY 1h",
        "symbol": "SPY",
        "source": SOURCE_ROOT / "data/normalized/yahoo_spy_1h.normalized.csv",
        "dest": "yahoo_spy_1h.normalized.csv",
    },
]

BRANCHES = [
    {
        "branch_id": "fvg_retest_continuation_long_v1",
        "path": "TrendExpansion -> PullbackContinuation -> fair_value_gap_retest -> fvg_retest_continuation_long_v1",
        "class_name": "ObFvgRetestContinuationLongV1",
        "direction": "long",
        "roi": "0.018",
        "stoploss": "-0.035",
    },
    {
        "branch_id": "order_block_retest_continuation_long_v1",
        "path": "TrendExpansion -> PullbackContinuation -> bullish_order_block_retest -> order_block_retest_continuation_long_v1",
        "class_name": "BullishOrderBlockRetestContinuationLongV1",
        "direction": "long",
        "roi": "0.016",
        "stoploss": "-0.032",
    },
    {
        "branch_id": "ob_fvg_confluence_continuation_long_v1",
        "path": "TrendExpansion -> PullbackContinuation -> fvg_plus_order_block_confluence -> ob_fvg_confluence_continuation_long_v1",
        "class_name": "ObFvgConfluenceContinuationLongV1",
        "direction": "long",
        "roi": "0.02",
        "stoploss": "-0.038",
    },
    {
        "branch_id": "ote_fvg_continuation_long_v1",
        "path": "TrendExpansion -> OTERetracement -> ote_plus_fvg_retest -> ote_fvg_continuation_long_v1",
        "class_name": "OteFvgContinuationLongV1",
        "direction": "long",
        "roi": "0.018",
        "stoploss": "-0.034",
    },
    {
        "branch_id": "ote_ob_continuation_long_v1",
        "path": "TrendExpansion -> OTERetracement -> ote_plus_order_block_retest -> ote_ob_continuation_long_v1",
        "class_name": "OteObContinuationLongV1",
        "direction": "long",
        "roi": "0.018",
        "stoploss": "-0.034",
    },
    {
        "branch_id": "session_fvg_continuation_v1",
        "path": "SessionContinuation -> KillzoneRetest -> session_fvg_retest -> session_fvg_continuation_v1",
        "class_name": "SessionFvgContinuationV1",
        "direction": "long",
        "roi": "0.014",
        "stoploss": "-0.028",
    },
    {
        "branch_id": "session_ob_continuation_v1",
        "path": "SessionContinuation -> KillzoneRetest -> session_order_block_retest -> session_ob_continuation_v1",
        "class_name": "SessionObContinuationV1",
        "direction": "long",
        "roi": "0.014",
        "stoploss": "-0.028",
    },
    {
        "branch_id": "smt_confirmed_ob_fvg_continuation_v1",
        "path": "CrossMarketConfirmation -> SMTConfirmedContinuation -> fvg_or_order_block_retest -> smt_confirmed_ob_fvg_continuation_v1",
        "class_name": "SmtConfirmedObFvgContinuationV1",
        "direction": "long",
        "roi": "0.017",
        "stoploss": "-0.033",
    },
    {
        "branch_id": "fvg_displacement_retest_expansion_v1",
        "path": "VolatilityCompression -> LiquidityExpansion -> displacement_fvg_retest -> fvg_displacement_retest_expansion_v1",
        "class_name": "DisplacementFvgRetestExpansionV1",
        "direction": "long",
        "roi": "0.02",
        "stoploss": "-0.04",
    },
    {
        "branch_id": "ob_fvg_failed_mitigation_guard_v1",
        "path": "Transition -> RiskSuppression -> failed_mitigation_guard -> ob_fvg_failed_mitigation_guard_v1",
        "class_name": "ObFvgFailedMitigationGuardV1",
        "direction": "long",
        "roi": "0.01",
        "stoploss": "-0.018",
    },
]


STRATEGY_TEMPLATE = '''from freqtrade.strategy import IStrategy
from pandas import DataFrame
import talib.abstract as ta


class {class_name}(IStrategy):
    timeframe = "1h"
    can_short = {can_short}
    minimal_roi = {{"0": {roi}, "24": 0}}
    stoploss = {stoploss}
    startup_candle_count = 120

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["ema20"] = ta.EMA(dataframe, timeperiod=20)
        dataframe["ema50"] = ta.EMA(dataframe, timeperiod=50)
        dataframe["atr14"] = ta.ATR(dataframe, timeperiod=14)
        dataframe["rsi14"] = ta.RSI(dataframe, timeperiod=14)
        dataframe["swing_high"] = dataframe["high"].rolling(20, min_periods=5).max()
        dataframe["swing_low"] = dataframe["low"].rolling(20, min_periods=5).min()
        dataframe["bull_fvg"] = dataframe["low"] > dataframe["high"].shift(2)
        dataframe["bear_fvg"] = dataframe["high"] < dataframe["low"].shift(2)
        dataframe["bull_fvg_mid"] = (dataframe["low"] + dataframe["high"].shift(2)) / 2.0
        dataframe["bear_fvg_mid"] = (dataframe["high"] + dataframe["low"].shift(2)) / 2.0
        dataframe["bull_order_block"] = (
            (dataframe["close"].shift(1) < dataframe["open"].shift(1))
            & (dataframe["close"] > dataframe["high"].shift(1))
            & (dataframe["close"] > dataframe["ema20"])
        )
        dataframe["bear_order_block"] = (
            (dataframe["close"].shift(1) > dataframe["open"].shift(1))
            & (dataframe["close"] < dataframe["low"].shift(1))
            & (dataframe["close"] < dataframe["ema20"])
        )
        dataframe["volume_z"] = (
            dataframe["volume"] - dataframe["volume"].rolling(48, min_periods=12).mean()
        ) / dataframe["volume"].rolling(48, min_periods=12).std()
        swing_range = (dataframe["swing_high"] - dataframe["swing_low"]).replace(0, 1)
        dataframe["ote_position"] = (dataframe["close"] - dataframe["swing_low"]) / swing_range
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        long_trend = (dataframe["ema20"] > dataframe["ema50"]) & (dataframe["close"] > dataframe["ema20"])
        short_trend = (dataframe["ema20"] < dataframe["ema50"]) & (dataframe["close"] < dataframe["ema20"])
        bull_fvg_retest = dataframe["bull_fvg"].rolling(12, min_periods=1).max().fillna(0).astype(bool) & (
            dataframe["low"] <= dataframe["bull_fvg_mid"].rolling(12, min_periods=1).max()
        )
        bear_fvg_retest = dataframe["bear_fvg"].rolling(12, min_periods=1).max().fillna(0).astype(bool) & (
            dataframe["high"] >= dataframe["bear_fvg_mid"].rolling(12, min_periods=1).min()
        )
        bull_ob_retest = dataframe["bull_order_block"].rolling(16, min_periods=1).max().fillna(0).astype(bool) & (
            dataframe["low"] <= dataframe["open"].shift(1).rolling(16, min_periods=1).max()
        )
        bear_ob_retest = dataframe["bear_order_block"].rolling(16, min_periods=1).max().fillna(0).astype(bool) & (
            dataframe["high"] >= dataframe["open"].shift(1).rolling(16, min_periods=1).min()
        )
        displacement = dataframe["volume_z"] > 0.8
        ote_zone = dataframe["ote_position"].between(0.50, 0.786)
        smt_proxy = dataframe["volume_z"].between(-0.25, 1.25) & (dataframe["rsi14"] > 48)
        failed_mitigation = (dataframe["rsi14"].between(45, 55)) & (dataframe["atr14"] > 0)
        condition = {condition}
        dataframe.loc[condition, ["{entry_column}", "enter_tag"]] = (1, "{branch_id}")
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (
                (dataframe["rsi14"] > 72)
                | (dataframe["close"] < dataframe["ema20"] * 0.985)
            ),
            ["exit_long", "exit_tag"],
        ] = (1, "ob_fvg_long_exit_v1")
        dataframe.loc[
            (
                (dataframe["rsi14"] < 28)
                | (dataframe["close"] > dataframe["ema20"] * 1.015)
            ),
            ["exit_short", "exit_tag"],
        ] = (1, "ob_fvg_short_exit_v1")
        return dataframe
'''

CONDITIONS = {
    "fvg_retest_continuation_long_v1": "long_trend & bull_fvg_retest & (dataframe[\"close\"] > dataframe[\"open\"])",
    "order_block_retest_continuation_long_v1": "long_trend & bull_ob_retest & (dataframe[\"close\"] > dataframe[\"open\"])",
    "ob_fvg_confluence_continuation_long_v1": "long_trend & bull_fvg_retest & bull_ob_retest",
    "ote_fvg_continuation_long_v1": "long_trend & ote_zone & bull_fvg_retest",
    "ote_ob_continuation_long_v1": "long_trend & ote_zone & bull_ob_retest",
    "session_fvg_continuation_v1": "long_trend & bull_fvg_retest & (dataframe[\"volume\"] > 0)",
    "session_ob_continuation_v1": "long_trend & bull_ob_retest & (dataframe[\"volume\"] > 0)",
    "smt_confirmed_ob_fvg_continuation_v1": "long_trend & smt_proxy & (bull_fvg_retest | bull_ob_retest)",
    "fvg_displacement_retest_expansion_v1": "long_trend & bull_fvg_retest & displacement",
    "ob_fvg_failed_mitigation_guard_v1": "failed_mitigation & ~(bull_fvg_retest | bull_ob_retest | bear_fvg_retest | bear_ob_retest)",
}


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    (ROOT / "agent-material").mkdir(parents=True, exist_ok=True)
    (ROOT / "data/normalized").mkdir(parents=True, exist_ok=True)
    (ROOT / "summaries").mkdir(parents=True, exist_ok=True)
    (ROOT / "checks").mkdir(parents=True, exist_ok=True)
    for pattern in ("*.material.json", "*.py"):
        for generated in (ROOT / "agent-material").glob(pattern):
            generated.unlink()
    pycache = ROOT / "agent-material/__pycache__"
    if pycache.exists():
        shutil.rmtree(pycache)

    provenance_rows = []
    material_rows = []
    material_paths = []

    for provider in PROVIDERS:
        dest = ROOT / "data/normalized" / provider["dest"]
        shutil.copyfile(provider["source"], dest)
        provenance_rows.append(
            {
                "provider": provider["provider"],
                "provider_label": provider["provider_label"],
                "symbol": provider["symbol"],
                "timeframe": "1h",
                "source_path": str(provider["source"]),
                "replay_path": str(dest),
                "provider_data_acquired_this_step": "false",
                "local_cache_replay": "true",
            }
        )

    for branch in BRANCHES:
        strategy_path = ROOT / "agent-material" / f"{branch['class_name']}.py"
        entry_column = "enter_short" if branch["direction"] == "short" else "enter_long"
        strategy_path.write_text(
            STRATEGY_TEMPLATE.format(
                class_name=branch["class_name"],
                can_short="True" if branch["direction"] == "short" else "False",
                roi=branch["roi"],
                stoploss=branch["stoploss"],
                condition=CONDITIONS[branch["branch_id"]],
                entry_column=entry_column,
                branch_id=branch["branch_id"],
            )
        )
        for provider in PROVIDERS:
            package_id = f"ob-fvg-{branch['branch_id']}-{provider['provider'].lower().replace('/', '-').replace(' ', '-')}-1h-v1"
            material_path = ROOT / "agent-material" / f"{package_id}.material.json"
            package = {
                "package_id": package_id,
                "title": f"OB/FVG {branch['branch_id']} - {provider['provider_label']}",
                "symbol": provider["symbol"],
                "timeframe": "1h",
                "timerange": "20250101-20260512",
                "direction": branch["direction"],
                "data_path": str(ROOT / "data/normalized" / provider["dest"]),
                "strategy_source_path": str(strategy_path),
                "strategy_class_name": branch["class_name"],
                "strategy_brief": "Board B OB/FVG branch-keyed profitability material.",
                "evaluation_priority": [
                    "branch_trade_density",
                    "regime_conditioned_win_rate",
                    "profit_factor",
                    "walk_forward_survival",
                    "cost_slippage_robustness",
                ],
                "consumer_evidence_profile": {
                    "branch_path": branch["path"],
                    "branch_id": branch["branch_id"],
                    "main_regime": branch["path"].split(" -> ")[0],
                    "sub_regime": branch["path"].split(" -> ")[1],
                    "sub_sub_regime_or_profit_factor": branch["path"].split(" -> ")[2],
                    "profit_factor": branch["path"].split(" -> ")[3],
                    "provider": provider["provider"],
                    "promotion_allowed": False,
                    "trade_usable": False,
                    "update_goal": False,
                },
                "notes": [
                    f"source_provider={provider['provider_label']}",
                    f"branch_path={branch['path']}",
                    "provider_data_acquired_this_step=false",
                    "local_cache_replay=true",
                    "material_preflight_only=true",
                    "promotion_allowed=false until AQ dispatch/rank and ordered downstream chain pass",
                ],
            }
            material_path.write_text(json.dumps(package, indent=2) + "\n")
            material_paths.append(str(material_path))
            material_rows.append(
                {
                    "provider": provider["provider"],
                    "provider_label": provider["provider_label"],
                    "branch_id": branch["branch_id"],
                    "branch_path": branch["path"],
                    "material_path": str(material_path),
                    "strategy_path": str(strategy_path),
                    "symbol": provider["symbol"],
                    "direction": branch["direction"],
                }
            )

    write_csv(
        ROOT / "summaries/provider_provenance_matrix.csv",
        provenance_rows,
        [
            "provider",
            "provider_label",
            "symbol",
            "timeframe",
            "source_path",
            "replay_path",
            "provider_data_acquired_this_step",
            "local_cache_replay",
        ],
    )
    write_csv(
        ROOT / "summaries/material_paths.csv",
        material_rows,
        [
            "provider",
            "provider_label",
            "branch_id",
            "branch_path",
            "material_path",
            "strategy_path",
            "symbol",
            "direction",
        ],
    )
    summary = {
        "root": str(ROOT),
        "material_count": len(material_rows),
        "provider_count": len(PROVIDERS),
        "branch_count": len(BRANCHES),
        "branch_paths": [branch["path"] for branch in BRANCHES],
        "material_paths": material_paths,
        "provider_data_acquired_this_step": False,
        "local_cache_replay": True,
        "promotion_allowed": False,
        "trade_usable": False,
        "update_goal": False,
    }
    (ROOT / "summaries/ob_fvg_branch_material_preflight_v1.json").write_text(
        json.dumps(summary, indent=2) + "\n"
    )

    branch_paths = {row["branch_path"] for row in material_rows}
    providers = {row["provider"] for row in material_rows}
    assertions = [
        f"material_count={len(material_rows)}",
        f"provider_count={len(providers)}",
        f"branch_count={len(branch_paths)}",
        f"expected_material_count={len(PROVIDERS) * len(BRANCHES)}",
        f"branch_keyed_by_construction={len(branch_paths) == len(BRANCHES)}",
        "new_provider_fetch=False",
        "local_cache_replay=True",
        "promotion_allowed=False",
        "trade_usable=False",
        "update_goal=False",
    ]
    (ROOT / "checks/ob_fvg_material_preflight_assertions.out").write_text("\n".join(assertions) + "\n")


if __name__ == "__main__":
    main()
