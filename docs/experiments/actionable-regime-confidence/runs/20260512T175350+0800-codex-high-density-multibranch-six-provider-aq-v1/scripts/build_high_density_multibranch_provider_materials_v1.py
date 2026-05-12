from __future__ import annotations

import csv
import json
import shutil
from pathlib import Path


ROOT = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260512T175350+0800-codex-high-density-multibranch-six-provider-aq-v1"
)

SOURCE_141554 = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260512T141554+0800-codex-provider-longspan-capability-matrix-v1"
)
SOURCE_173141 = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260512T173141+0800-codex-ote-level-leaf-six-provider-aq-v1"
)


BRANCH_PATHS = [
    (
        "TrendExpansion",
        "NormalVolatility",
        "MomentumPullbackFast",
        "ema_rsi_pullback_density_v1",
    ),
    (
        "TrendExpansion",
        "HighVolatility",
        "BreakoutContinuationFast",
        "donchian_volume_breakout_density_v1",
    ),
    (
        "RangeConsolidation",
        "NormalVolatility",
        "MeanReversionFast",
        "rsi_bollinger_reversion_density_v1",
    ),
    (
        "Transition",
        "VolatilityCompression",
        "CompressionBreakoutFast",
        "atr_compression_breakout_density_v1",
    ),
]


STRATEGY = '''from __future__ import annotations

import talib.abstract as ta
from freqtrade.strategy import IStrategy
from pandas import DataFrame


class ProviderHighDensityMultiBranchV1(IStrategy):
    INTERFACE_VERSION = 3

    timeframe = "1h"
    can_short = False

    minimal_roi = {"0": 100}
    stoploss = -0.045

    trailing_stop = True
    trailing_stop_positive = 0.008
    trailing_stop_positive_offset = 0.018
    trailing_only_offset_is_reached = True

    process_only_new_candles = True
    use_exit_signal = True
    exit_profit_only = False
    ignore_roi_if_entry_signal = False
    startup_candle_count: int = 240

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["ema12"] = ta.EMA(dataframe, timeperiod=12)
        dataframe["ema24"] = ta.EMA(dataframe, timeperiod=24)
        dataframe["ema72"] = ta.EMA(dataframe, timeperiod=72)
        dataframe["rsi"] = ta.RSI(dataframe, timeperiod=14)
        dataframe["atr"] = ta.ATR(dataframe, timeperiod=14)
        dataframe["atr_pct"] = dataframe["atr"] / dataframe["close"]
        dataframe["volume_sma"] = ta.SMA(dataframe["volume"], timeperiod=30)
        dataframe["donchian_high"] = dataframe["high"].rolling(48).max().shift(1)
        dataframe["bb_mid"] = ta.SMA(dataframe["close"], timeperiod=20)
        dataframe["bb_std"] = dataframe["close"].rolling(20).std()
        dataframe["bb_low"] = dataframe["bb_mid"] - dataframe["bb_std"] * 2.0
        dataframe["atr_sma"] = ta.SMA(dataframe["atr"], timeperiod=50)
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["enter_long"] = 0
        dataframe["enter_tag"] = ""

        trend = (dataframe["ema12"] > dataframe["ema24"]) & (dataframe["ema24"] > dataframe["ema72"])
        normal_vol = dataframe["atr_pct"].between(0.004, 0.035)
        high_vol = dataframe["atr_pct"].between(0.018, 0.070)
        compression = (dataframe["atr"] < dataframe["atr_sma"] * 0.82) & normal_vol
        reclaim = (dataframe["close"] > dataframe["ema12"]) & (dataframe["close"].shift(1) <= dataframe["ema12"].shift(1))
        pullback = trend & normal_vol & reclaim & dataframe["rsi"].between(42, 63)
        breakout = trend & high_vol & (dataframe["close"] > dataframe["donchian_high"]) & (dataframe["volume"] > dataframe["volume_sma"] * 1.10)
        reversion = normal_vol & (dataframe["close"].shift(1) < dataframe["bb_low"].shift(1)) & (dataframe["close"] > dataframe["bb_low"]) & dataframe["rsi"].between(28, 48)
        compression_breakout = compression.shift(1).fillna(False) & (dataframe["close"] > dataframe["high"].shift(1)) & (dataframe["volume"] > dataframe["volume_sma"])

        dataframe.loc[pullback, "enter_long"] = 1
        dataframe.loc[pullback, "enter_tag"] = "ema_rsi_pullback_density_v1"
        dataframe.loc[breakout, "enter_long"] = 1
        dataframe.loc[breakout, "enter_tag"] = "donchian_volume_breakout_density_v1"
        dataframe.loc[reversion, "enter_long"] = 1
        dataframe.loc[reversion, "enter_tag"] = "rsi_bollinger_reversion_density_v1"
        dataframe.loc[compression_breakout, "enter_long"] = 1
        dataframe.loc[compression_breakout, "enter_tag"] = "atr_compression_breakout_density_v1"
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["exit_long"] = 0
        exit_trend_break = dataframe["close"] < dataframe["ema24"]
        exit_overheat = dataframe["rsi"] > 76
        exit_vol_spike = dataframe["atr_pct"] > 0.085
        dataframe.loc[exit_trend_break | exit_overheat | exit_vol_spike, "exit_long"] = 1
        return dataframe
'''


PROVIDERS = [
    {
        "provider": "IBKR",
        "symbol": "SPY",
        "material_symbol": "SPY",
        "source": SOURCE_141554 / "data/ibkr_spy_1h_5y.normalized.csv",
        "fallback_raw_source": Path(
            "/tmp/ict-provider-longspan-20260512T141554+0800/ibkr_spy_1h_5y.csv"
        ),
        "target": "ibkr_spy_1h_5y.normalized.csv",
        "source_root": SOURCE_141554,
    },
    {
        "provider": "TradingViewRemix/TVR",
        "symbol": "BTCUSD",
        "material_symbol": "BTC",
        "source": SOURCE_173141 / "data/normalized/tvr_btc_usd_1h.normalized.csv",
        "target": "tvr_btc_usd_1h.normalized.csv",
        "source_root": SOURCE_173141,
    },
    {
        "provider": "yfinance/YF",
        "symbol": "SPY",
        "material_symbol": "SPY",
        "source": SOURCE_173141 / "data/normalized/yahoo_spy_1h.normalized.csv",
        "target": "yahoo_spy_1h.normalized.csv",
        "source_root": SOURCE_173141,
    },
    {
        "provider": "Kraken",
        "symbol": "XBTUSD",
        "material_symbol": "XBTUSD",
        "source": SOURCE_173141 / "data/normalized/kraken_futures_pfxbtusd_1h.normalized.csv",
        "target": "kraken_futures_pfxbtusd_1h.normalized.csv",
        "source_root": SOURCE_173141,
    },
    {
        "provider": "Binance",
        "symbol": "BTCUSDT",
        "material_symbol": "BTCUSDT",
        "source": SOURCE_173141 / "data/normalized/binance_btcusdt_1h.normalized.csv",
        "target": "binance_btcusdt_1h.normalized.csv",
        "source_root": SOURCE_173141,
    },
    {
        "provider": "Bybit",
        "symbol": "BTCUSDT",
        "material_symbol": "BTCUSDT",
        "source": SOURCE_173141 / "data/normalized/bybit_linear_btcusdt_1h.normalized.csv",
        "target": "bybit_linear_btcusdt_1h.normalized.csv",
        "source_root": SOURCE_173141,
    },
]


def csv_row_count(path: Path) -> int:
    with path.open(newline="") as handle:
        return max(sum(1 for _ in handle) - 1, 0)


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def normalize_ibkr_raw(source: Path, target: Path) -> None:
    with source.open(newline="") as in_handle, target.open("w", newline="") as out_handle:
        reader = csv.DictReader(in_handle)
        writer = csv.DictWriter(
            out_handle,
            fieldnames=["timestamp", "open", "high", "low", "close", "volume"],
        )
        writer.writeheader()
        for row in reader:
            timestamp = row["ts"]
            if timestamp.endswith("+00:00"):
                timestamp = timestamp.removesuffix("+00:00") + "Z"
            writer.writerow(
                {
                    "timestamp": timestamp,
                    "open": row["open"],
                    "high": row["high"],
                    "low": row["low"],
                    "close": row["close"],
                    "volume": row["volume"],
                }
            )


def main() -> int:
    for subdir in ("agent-material", "data/normalized", "summaries", "checks", "command-output"):
        (ROOT / subdir).mkdir(parents=True, exist_ok=True)

    strategy_path = ROOT / "agent-material/ProviderHighDensityMultiBranchV1.py"
    strategy_path.write_text(STRATEGY, encoding="utf-8")

    material_paths: list[str] = []
    provenance_rows: list[dict[str, object]] = []
    material_rows: list[dict[str, object]] = []
    missing: list[str] = []

    for spec in PROVIDERS:
        source = spec["source"]
        target = ROOT / "data/normalized" / spec["target"]
        source_path_for_provenance = source
        status = "material_ready_from_prior_verified_provider_artifact"
        if not source.exists():
            fallback_raw_source = spec.get("fallback_raw_source")
            if fallback_raw_source and Path(fallback_raw_source).exists():
                normalize_ibkr_raw(Path(fallback_raw_source), target)
                source_path_for_provenance = Path(fallback_raw_source)
                status = "material_ready_from_prior_verified_tmp_raw_normalized_into_run_root"
            else:
                missing.append(str(source))
                continue
        else:
            shutil.copy2(source, target)
        rows = csv_row_count(target)
        package_id = (
            "high-density-multibranch-"
            + str(spec["provider"]).lower().replace("/", "-").replace(" ", "-")
            + "-"
            + str(spec["symbol"]).lower().replace("/", "-")
            + "-1h-v1"
        )
        material_path = ROOT / "agent-material" / f"{package_id}.material.json"
        branch_notes = [
            "branch_path="
            + " -> ".join([main, sub, sub_sub, factor])
            for main, sub, sub_sub, factor in BRANCH_PATHS
        ]
        material = {
            "package_id": package_id,
            "title": f"High-density multibranch - {spec['provider']} {spec['symbol']} 1h",
            "symbol": spec["material_symbol"],
            "timeframe": "1h",
            "direction": "long",
            "data_path": str(target),
            "strategy_source_path": str(strategy_path),
            "strategy_class_name": "ProviderHighDensityMultiBranchV1",
            "strategy_brief": (
                "Board B high-density profitability packet preserving four "
                "main_regime -> sub_regime -> sub_sub_regime_or_profit_factor -> profit_factor branches."
            ),
            "evaluation_priority": [
                "branch_trade_density",
                "regime_conditioned_win_rate",
                "profit_factor",
                "walk_forward_survival",
            ],
            "notes": branch_notes
            + [
                f"source_provider={spec['provider']}",
                f"provider_replay_source_root={spec['source_root']}",
                "same_root_copy=true",
                "promotion_allowed=false until AQ dispatch/rank and downstream admission readbacks pass",
            ],
        }
        material_path.write_text(json.dumps(material, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        material_paths.append(str(material_path))
        provenance_rows.append(
            {
                "provider": spec["provider"],
                "symbol": spec["symbol"],
                "timeframe": "1h",
                "source_root": str(spec["source_root"]),
                "source_path": str(source_path_for_provenance),
                "same_root_data_path": str(target),
                "material_path": str(material_path),
                "rows": rows,
                "provider_requested": "true",
                "provider_data_acquired_this_step": "false",
                "same_root_replay_copy": "true",
                "status": status,
            }
        )
        material_rows.append(
            {
                "provider": spec["provider"],
                "material_path": str(material_path),
                "same_root_data_path": str(target),
                "rows": rows,
            }
        )

    write_csv(
        ROOT / "summaries/provider_provenance_matrix.csv",
        provenance_rows,
        [
            "provider",
            "symbol",
            "timeframe",
            "source_root",
            "source_path",
            "same_root_data_path",
            "material_path",
            "rows",
            "provider_requested",
            "provider_data_acquired_this_step",
            "same_root_replay_copy",
            "status",
        ],
    )
    write_csv(
        ROOT / "summaries/material_paths.csv",
        material_rows,
        ["provider", "material_path", "same_root_data_path", "rows"],
    )

    contract = {
        "run_root": str(ROOT),
        "packet": "175350_high_density_multibranch_six_provider_aq_packet_v1",
        "branch_paths": [
            {
                "main_regime": main,
                "sub_regime": sub,
                "sub_sub_regime_or_profit_factor": sub_sub,
                "profit_factor": factor,
                "path": " -> ".join([main, sub, sub_sub, factor]),
            }
            for main, sub, sub_sub, factor in BRANCH_PATHS
        ],
        "provider_rows": len(provenance_rows),
        "agent_material_count": len(material_paths),
        "materials": material_paths,
        "provider_data_acquired_this_step": False,
        "same_root_replay_copy": True,
        "promotion_allowed": False,
        "trade_usable": False,
        "update_goal": False,
        "missing_sources": missing,
    }
    (ROOT / "summaries/high_density_multibranch_contract_v1.json").write_text(
        json.dumps(contract, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (ROOT / "run_root.txt").write_text(str(ROOT) + "\n", encoding="utf-8")

    assertions = [
        f"{'PASS' if len(provenance_rows) == 6 else 'FAIL'} provider_rows_6 actual={len(provenance_rows)}",
        f"{'PASS' if len(material_paths) == 6 else 'FAIL'} material_count_6 actual={len(material_paths)}",
        f"{'PASS' if len(BRANCH_PATHS) == 4 else 'FAIL'} branch_paths_4 actual={len(BRANCH_PATHS)}",
        "PASS promotion_allowed_false",
        "PASS trade_usable_false",
        "PASS update_goal_false",
    ]
    if missing:
        assertions.append("FAIL missing_sources " + ";".join(missing))
    (ROOT / "checks/provider_material_preflight_assertions.out").write_text(
        "\n".join(assertions) + "\n",
        encoding="utf-8",
    )
    (ROOT / "high_density_multibranch_provider_materials_v1.md").write_text(
        "\n".join(
            [
                "# 175350 High-Density Multibranch Provider Materials v1",
                "",
                f"Run root: `{ROOT}`",
                "",
                "Purpose: materialize a Board B profitability-factor packet that keeps the regime-factor root as the first-class branch key.",
                "",
                "Branch paths:",
                *[
                    f"- `{main} -> {sub} -> {sub_sub} -> {factor}`"
                    for main, sub, sub_sub, factor in BRANCH_PATHS
                ],
                "",
                "Provider handling:",
                "- Six provider rows and six agent-material JSON files are generated under this root.",
                "- Data files are same-root copies of prior verified provider-normalized artifacts, not newly acquired provider fetches in this step.",
                "- Current provider-status and TVR harness readbacks must be stored separately before any downstream promotion claim.",
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
    print(json.dumps(contract, indent=2, sort_keys=True))
    return 0 if len(provenance_rows) == 6 and not missing else 1


if __name__ == "__main__":
    raise SystemExit(main())
