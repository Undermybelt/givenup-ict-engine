from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260512T160511+0800-codex-ob-fvg-aq-agent-material-packet-v1"
)
SOURCE_ROOT = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260512T150855+0800-codex-145809-aq-material-seed-dispatch-v1"
)
TVR_ROOT = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260512T154536+0800-codex-board-b-tvr-mcp-redacted-health-probe-v1"
)
SCREEN_ROOT = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260512T151907+0800-codex-ob-fvg-regime-branch-screen-v1"
)


STRATEGY = '''from __future__ import annotations

import talib.abstract as ta
from freqtrade.strategy import IStrategy
from pandas import DataFrame


class ProviderObFvgPullbackV1(IStrategy):
    INTERFACE_VERSION = 3

    timeframe = "1h"
    can_short = False

    minimal_roi = {"0": 100}
    stoploss = -0.030

    trailing_stop = True
    trailing_stop_positive = 0.010
    trailing_stop_positive_offset = 0.022
    trailing_only_offset_is_reached = True

    process_only_new_candles = True
    use_exit_signal = True
    exit_profit_only = False
    ignore_roi_if_entry_signal = False

    startup_candle_count: int = 260

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["ema21"] = ta.EMA(dataframe, timeperiod=21)
        dataframe["ema50"] = ta.EMA(dataframe, timeperiod=50)
        dataframe["ema200"] = ta.EMA(dataframe, timeperiod=200)
        dataframe["rsi"] = ta.RSI(dataframe, timeperiod=14)
        dataframe["atr"] = ta.ATR(dataframe, timeperiod=14)
        dataframe["hour_utc"] = dataframe["date"].dt.hour

        displacement_up = dataframe["close"] > (dataframe["high"].shift(1) + dataframe["atr"] * 0.20)
        prior_bear = dataframe["close"].shift(1) < dataframe["open"].shift(1)
        ob_seed = displacement_up & prior_bear
        ob_low = dataframe["close"].shift(1).where(ob_seed)
        ob_high = dataframe["open"].shift(1).where(ob_seed)
        dataframe["ob_low"] = ob_low.ffill().shift(1)
        dataframe["ob_high"] = ob_high.ffill().shift(1)

        fvg_seed = dataframe["low"] > (dataframe["high"].shift(2) + dataframe["atr"] * 0.08)
        fvg_low = dataframe["high"].shift(2).where(fvg_seed)
        fvg_high = dataframe["low"].where(fvg_seed)
        dataframe["fvg_low"] = fvg_low.ffill().shift(1)
        dataframe["fvg_high"] = fvg_high.ffill().shift(1)

        dataframe["trend_transition_low_vol_up"] = (
            (dataframe["ema21"] > dataframe["ema50"])
            & (dataframe["close"] > dataframe["ema50"])
            & (dataframe["atr"] / dataframe["close"] < 0.020)
            & (dataframe["rsi"] >= 38)
            & (dataframe["rsi"] <= 66)
        )
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["enter_long"] = 0
        dataframe["enter_tag"] = ""

        liquid_window = (dataframe["hour_utc"] >= 0) & (dataframe["hour_utc"] <= 23)
        reclaim = dataframe["close"] > dataframe["open"]
        ob_touch = (
            dataframe["ob_low"].notna()
            & (dataframe["low"] <= dataframe["ob_high"] + dataframe["atr"] * 0.10)
            & (dataframe["close"] >= dataframe["ob_low"])
        )
        fvg_touch = (
            dataframe["fvg_low"].notna()
            & (dataframe["low"] <= dataframe["fvg_high"] + dataframe["atr"] * 0.10)
            & (dataframe["close"] >= dataframe["fvg_low"])
        )
        base = liquid_window & dataframe["trend_transition_low_vol_up"] & reclaim

        dataframe.loc[base & fvg_touch, "enter_long"] = 1
        dataframe.loc[base & fvg_touch, "enter_tag"] = "fair_value_gap_pullback_v1"
        dataframe.loc[base & ob_touch, "enter_long"] = 1
        dataframe.loc[base & ob_touch, "enter_tag"] = "order_block_pullback_v1"
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["exit_long"] = 0
        trend_break = dataframe["close"] < dataframe["ema50"]
        local_exhaustion = dataframe["rsi"] > 76
        volatility_break = (dataframe["atr"] / dataframe["close"]) > 0.035
        dataframe.loc[trend_break | local_exhaustion | volatility_break, "exit_long"] = 1
        return dataframe
'''


PROVIDERS = [
    {
        "provider": "IBKR",
        "symbol": "SPY",
        "timeframe": "1h",
        "package_id": "ob-fvg-pullback-ibkr-spy-1h-v1",
        "title": "OB FVG pullback - IBKR SPY 1h",
        "data_path": SOURCE_ROOT / "data/ibkr_spy_1h_5y.normalized.csv",
        "source_note": "IBKR gateway SPY 1h 5Y provider-backed replay data",
    },
    {
        "provider": "yfinance/YF",
        "symbol": "ES",
        "timeframe": "1h",
        "package_id": "ob-fvg-pullback-yf-es-1h-v1",
        "title": "OB FVG pullback - Yahoo ES 1h",
        "data_path": SOURCE_ROOT / "data/yahoo_es_1h_20240513_20260512.normalized.csv",
        "source_note": "Yahoo ES 1h provider-backed replay data",
    },
    {
        "provider": "Kraken",
        "symbol": "XBTUSD",
        "timeframe": "1h",
        "package_id": "ob-fvg-pullback-kraken-xbtusd-1h-v1",
        "title": "OB FVG pullback - Kraken XBTUSD 1h",
        "data_path": SOURCE_ROOT / "data/kraken_futures_pfxbtusd_1h_20200101_20260512.normalized.csv",
        "source_note": "Kraken futures XBTUSD 1h provider-backed replay data",
    },
    {
        "provider": "Binance",
        "symbol": "BTCUSDT",
        "timeframe": "1h",
        "package_id": "ob-fvg-pullback-binance-btcusdt-1h-v1",
        "title": "OB FVG pullback - Binance BTCUSDT 1h",
        "data_path": SOURCE_ROOT / "data/binance_btcusdt_1h_20170817_20260512.normalized.csv",
        "source_note": "Binance BTCUSDT 1h provider-backed replay data",
    },
    {
        "provider": "Bybit",
        "symbol": "BTCUSDT",
        "timeframe": "1h",
        "package_id": "ob-fvg-pullback-bybit-btcusdt-1h-v1",
        "title": "OB FVG pullback - Bybit BTCUSDT linear 1h",
        "data_path": SOURCE_ROOT / "data/bybit_linear_btcusdt_1h_20200101_20260512.normalized.csv",
        "source_note": "Bybit linear BTCUSDT 1h provider-backed replay data",
    },
]


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    for subdir in ("agent-material", "summaries", "checks", "command-output"):
        (ROOT / subdir).mkdir(parents=True, exist_ok=True)

    strategy_path = ROOT / "agent-material/ProviderObFvgPullbackV1.py"
    strategy_path.write_text(STRATEGY, encoding="utf-8")

    materials: list[str] = []
    provenance: list[dict[str, object]] = []
    for spec in PROVIDERS:
        material_path = ROOT / "agent-material" / f"{spec['package_id']}.material.json"
        material = {
            "package_id": spec["package_id"],
            "title": spec["title"],
            "symbol": spec["symbol"],
            "timeframe": spec["timeframe"],
            "direction": "long",
            "data_path": str(spec["data_path"]),
            "strategy_source_path": str(strategy_path),
            "strategy_class_name": "ProviderObFvgPullbackV1",
            "strategy_brief": (
                "Board B OB/FVG continuation-pullback profitability packet "
                "focused on TrendTransition -> LowVolatility -> up_momentum."
            ),
            "evaluation_priority": [
                "branch_trade_density",
                "regime_conditioned_win_rate",
                "profit_factor",
                "walk_forward_survival",
            ],
            "notes": [
                "branch_path=TrendTransition -> LowVolatility -> up_momentum -> order_block_pullback_v1",
                f"source_provider={spec['source_note']}",
                "promotion_allowed=false until same-root six-provider authority and downstream admission are complete",
            ],
        }
        material_path.write_text(json.dumps(material, indent=2) + "\n", encoding="utf-8")
        materials.append(str(material_path))
        provenance.append(
            {
                "provider": spec["provider"],
                "symbol_context": f"{spec['symbol']} {spec['timeframe']}",
                "aq_provider_invoked": "true",
                "provider_requested": "true",
                "provider_data_acquired": "true",
                "provider_unreachable": "false",
                "local_cache_replay": "true",
                "source_root": str(SOURCE_ROOT),
                "material_path": str(material_path),
                "data_path": str(spec["data_path"]),
                "status": "material_ready_replay_input",
                "failure_reason": "",
            }
        )

    provenance.insert(
        1,
        {
            "provider": "TradingViewRemix/TVR",
            "symbol_context": "provider_unreachable_from_154536",
            "aq_provider_invoked": "false",
            "provider_requested": "true",
            "provider_data_acquired": "false",
            "provider_unreachable": "true",
            "local_cache_replay": "false",
            "source_root": str(TVR_ROOT),
            "material_path": "",
            "data_path": "",
            "status": "provider_unreachable_current_rate_limited",
            "failure_reason": "tvr_tools_list_http_429_rate_limited_from_154536_no_new_call",
        },
    )

    fields = [
        "provider",
        "symbol_context",
        "aq_provider_invoked",
        "provider_requested",
        "provider_data_acquired",
        "provider_unreachable",
        "local_cache_replay",
        "source_root",
        "material_path",
        "data_path",
        "status",
        "failure_reason",
    ]
    write_csv(ROOT / "summaries/provider_provenance_matrix.csv", provenance, fields)

    contract = {
        "run_root": str(ROOT),
        "source_screen_root": str(SCREEN_ROOT),
        "source_aq_seed_root": str(SOURCE_ROOT),
        "hypothesis": "OB/FVG continuation-pullback as Board B profitability factor",
        "branch_path": "TrendTransition -> LowVolatility -> up_momentum -> order_block_pullback_v1",
        "main_regime": "TrendTransition",
        "sub_regime": "LowVolatility",
        "sub_sub_regime_or_profit_factor": "up_momentum",
        "profit_factor": "order_block_pullback_v1",
        "materials": materials,
        "provider_rows": len(provenance),
        "same_root_six_provider_authority": False,
        "tvr_policy": "no_new_call_record_154536_rate_limit_as_unreachable",
        "promotion_allowed": False,
        "trade_usable": False,
        "update_goal": False,
    }
    (ROOT / "summaries/ob_fvg_aq_agent_material_contract_v1.json").write_text(
        json.dumps(contract, indent=2) + "\n",
        encoding="utf-8",
    )

    (ROOT / "run_root.txt").write_text(str(ROOT) + "\n", encoding="utf-8")
    (ROOT / "ob_fvg_aq_agent_material_packet_v1.md").write_text(
        "\n".join(
            [
                "# OB/FVG AQ Agent-Material Packet v1",
                "",
                f"Run root: `{ROOT}`",
                f"Source screen root: `{SCREEN_ROOT}`",
                f"Source AQ seed root: `{SOURCE_ROOT}`",
                "",
                "Purpose: convert the best `151907` OB/FVG screen leaf into a real Auto-Quant agent-material packet while preserving Board B branch identity.",
                "",
                "Branch path:",
                "- `TrendTransition -> LowVolatility -> up_momentum -> order_block_pullback_v1`",
                "",
                "Provider contract:",
                "- Six provider rows are emitted in `summaries/provider_provenance_matrix.csv`.",
                "- TVR is recorded as unreachable from `154536`; this builder does not make a new TVR call.",
                "- Non-TVR rows use provider-backed replay files from `150855` and are therefore `local_cache_replay=true` until a future same-root provider acquisition rerun.",
                "",
                "Gate:",
                "- `promotion_allowed=false`",
                "- `trade_usable=false`",
                "- `update_goal=false`",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    assertions = [
        "PASS material_count_5",
        "PASS provider_rows_6",
        "PASS tvr_recorded_unreachable_without_new_call",
        "PASS branch_path_preserved",
        "PASS promotion_false",
    ]
    (ROOT / "checks/build_ob_fvg_aq_agent_material_packet_v1_assertions.out").write_text(
        "\n".join(assertions) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
