#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path


ROOT = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260512T192000+0800-codex-ote-four-leaf-six-provider-aq-v1"
)
SOURCE_ROOT = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260512T184332+0800-codex-session-liquidity-vwap-opening-range-six-provider-aq-v1"
)

PROVIDERS = [
    {
        "provider": "yfinance/YF",
        "provider_key": "yfinance-yf",
        "title_suffix": "yfinance/YF SPY 1h",
        "symbol": "SPY",
        "data_path": SOURCE_ROOT / "data/normalized/yahoo_spy_1h.normalized.csv",
        "source_material": SOURCE_ROOT / "agent-material/session-liquidity-yfinance-yf-1h-v1.material.json",
    },
    {
        "provider": "Binance",
        "provider_key": "binance",
        "title_suffix": "Binance BTCUSDT 1h",
        "symbol": "BTCUSDT",
        "data_path": SOURCE_ROOT / "data/normalized/binance_btcusdt_1h.normalized.csv",
        "source_material": SOURCE_ROOT / "agent-material/session-liquidity-binance-1h-v1.material.json",
    },
    {
        "provider": "Bybit",
        "provider_key": "bybit",
        "title_suffix": "Bybit BTCUSDT 1h",
        "symbol": "BTCUSDT",
        "data_path": SOURCE_ROOT / "data/normalized/bybit_linear_btcusdt_1h.normalized.csv",
        "source_material": SOURCE_ROOT / "agent-material/session-liquidity-bybit-1h-v1.material.json",
    },
    {
        "provider": "Kraken",
        "provider_key": "kraken",
        "title_suffix": "Kraken XBTUSD 1h",
        "symbol": "XBTUSD",
        "data_path": SOURCE_ROOT / "data/normalized/kraken_futures_pfxbtusd_1h.normalized.csv",
        "source_material": SOURCE_ROOT / "agent-material/session-liquidity-kraken-1h-v1.material.json",
    },
    {
        "provider": "IBKR",
        "provider_key": "ibkr",
        "title_suffix": "IBKR SPY 1h",
        "symbol": "SPY",
        "data_path": SOURCE_ROOT / "data/normalized/ibkr_spy_1h_90d.normalized.csv",
        "source_material": SOURCE_ROOT / "agent-material/session-liquidity-ibkr-1h-v1.material.json",
    },
    {
        "provider": "TradingViewRemix/TVR",
        "provider_key": "tvr-btc-usd",
        "title_suffix": "TradingViewRemix/TVR BTCUSD 1h",
        "symbol": "BTCUSD",
        "data_path": SOURCE_ROOT / "data/normalized/tvr_btc_usd_1h.normalized.csv",
        "source_material": SOURCE_ROOT / "agent-material/session-liquidity-tvr-btc-usd-1h-v1.material.json",
    },
]

OTE_LEAVES = [
    {
        "level": "0500",
        "ratio": 0.500,
        "class_name": "OteRetrace0500ContinuationV1",
        "branch_path": "TrendExpansion -> PullbackContinuation -> ote_retrace_0500 -> ote_retrace_0500_continuation_v1",
        "sub_sub": "ote_retrace_0500",
        "profit_factor": "ote_retrace_0500_continuation_v1",
        "stoploss": -0.022,
        "trailing_positive": 0.008,
        "trailing_offset": 0.018,
    },
    {
        "level": "0618",
        "ratio": 0.618,
        "class_name": "OteRetrace0618ContinuationV1",
        "branch_path": "TrendExpansion -> PullbackContinuation -> ote_retrace_0618 -> ote_retrace_0618_continuation_v1",
        "sub_sub": "ote_retrace_0618",
        "profit_factor": "ote_retrace_0618_continuation_v1",
        "stoploss": -0.026,
        "trailing_positive": 0.010,
        "trailing_offset": 0.022,
    },
    {
        "level": "0705",
        "ratio": 0.705,
        "class_name": "OteRetrace0705ContinuationV1",
        "branch_path": "TrendExpansion -> PullbackContinuation -> ote_retrace_0705 -> ote_retrace_0705_continuation_v1",
        "sub_sub": "ote_retrace_0705",
        "profit_factor": "ote_retrace_0705_continuation_v1",
        "stoploss": -0.030,
        "trailing_positive": 0.011,
        "trailing_offset": 0.024,
    },
    {
        "level": "0786",
        "ratio": 0.786,
        "class_name": "OteRetrace0786ContinuationV1",
        "branch_path": "TrendExpansion -> PullbackContinuation -> ote_retrace_0786 -> ote_retrace_0786_continuation_v1",
        "sub_sub": "ote_retrace_0786",
        "profit_factor": "ote_retrace_0786_continuation_v1",
        "stoploss": -0.034,
        "trailing_positive": 0.012,
        "trailing_offset": 0.026,
    },
]


STRATEGY_TEMPLATE = '''from __future__ import annotations

import talib.abstract as ta
from freqtrade.strategy import IStrategy
from pandas import DataFrame


class {class_name}(IStrategy):
    INTERFACE_VERSION = 3

    timeframe = "1h"
    can_short = False

    minimal_roi = {{"0": 100}}
    stoploss = {stoploss}
    trailing_stop = True
    trailing_stop_positive = {trailing_positive}
    trailing_stop_positive_offset = {trailing_offset}
    trailing_only_offset_is_reached = True
    process_only_new_candles = True
    use_exit_signal = True
    startup_candle_count: int = 260

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["ema20"] = ta.EMA(dataframe, timeperiod=20)
        dataframe["ema50"] = ta.EMA(dataframe, timeperiod=50)
        dataframe["ema200"] = ta.EMA(dataframe, timeperiod=200)
        dataframe["rsi"] = ta.RSI(dataframe, timeperiod=14)
        dataframe["atr"] = ta.ATR(dataframe, timeperiod=14)
        dataframe["swing_high_48"] = dataframe["high"].rolling(48, min_periods=24).max().shift(1)
        dataframe["swing_low_48"] = dataframe["low"].rolling(48, min_periods=24).min().shift(1)
        dataframe["impulse_range_48"] = dataframe["swing_high_48"] - dataframe["swing_low_48"]
        dataframe["ote_price"] = dataframe["swing_high_48"] - dataframe["impulse_range_48"] * {ratio}
        dataframe["ote_touch"] = dataframe["low"] <= dataframe["ote_price"]
        dataframe["ote_reclaim"] = dataframe["close"] > dataframe["ote_price"]
        dataframe["hour_utc"] = dataframe["date"].dt.hour
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["enter_long"] = 0
        dataframe["enter_tag"] = ""

        trend_expansion = (
            (dataframe["ema20"] > dataframe["ema50"])
            & (dataframe["ema50"] > dataframe["ema200"])
            & (dataframe["close"] > dataframe["ema200"])
            & (dataframe["impulse_range_48"] > dataframe["atr"] * 2.8)
        )
        pullback_continuation = (
            trend_expansion
            & dataframe["ote_touch"]
            & dataframe["ote_reclaim"]
            & (dataframe["rsi"].between(38, 68))
            & dataframe["hour_utc"].between(0, 23)
        )

        dataframe.loc[pullback_continuation, "enter_long"] = 1
        dataframe.loc[pullback_continuation, "enter_tag"] = "{profit_factor}"
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["exit_long"] = 0
        trend_loss = dataframe["close"] < dataframe["ema50"]
        exhaustion = dataframe["rsi"] > 76
        failed_reclaim = dataframe["close"] < dataframe["ote_price"] - dataframe["atr"] * 0.35
        dataframe.loc[trend_loss | exhaustion | failed_reclaim, "exit_long"] = 1
        return dataframe
'''


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def csv_rows(path: Path) -> int:
    with path.open(newline="") as handle:
        reader = csv.reader(handle)
        next(reader, None)
        return sum(1 for _ in reader)


def write_strategy(leaf: dict[str, object]) -> Path:
    strategy_path = ROOT / "agent-material" / f"{leaf['class_name']}.py"
    strategy_path.write_text(
        STRATEGY_TEMPLATE.format(
            class_name=leaf["class_name"],
            ratio=f"{leaf['ratio']:.3f}",
            profit_factor=leaf["profit_factor"],
            stoploss=f"{leaf['stoploss']:.3f}",
            trailing_positive=f"{leaf['trailing_positive']:.3f}",
            trailing_offset=f"{leaf['trailing_offset']:.3f}",
        )
    )
    return strategy_path


def main() -> int:
    for rel in ["agent-material", "checks", "manifests", "summaries"]:
        (ROOT / rel).mkdir(parents=True, exist_ok=True)

    strategy_paths = {leaf["level"]: write_strategy(leaf) for leaf in OTE_LEAVES}
    materials = []
    provenance_rows = []
    manifest_rows = []

    for leaf in OTE_LEAVES:
        strategy_path = strategy_paths[leaf["level"]]
        manifest_rows.append({"path": str(strategy_path), "sha256": sha256(strategy_path)})
        for provider in PROVIDERS:
            data_path = provider["data_path"]
            source_material = provider["source_material"]
            if not data_path.exists():
                raise SystemExit(f"missing data_path: {data_path}")
            if not source_material.exists():
                raise SystemExit(f"missing source_material: {source_material}")

            source = json.loads(source_material.read_text())
            timerange = source.get("timerange", "20250101-20260512")
            package_id = f"ote-{leaf['level']}-{provider['provider_key']}-1h-v1"
            material_path = ROOT / "agent-material" / f"{package_id}.material.json"
            material = {
                "package_id": package_id,
                "title": f"OTE {leaf['level']} continuation - {provider['title_suffix']}",
                "symbol": provider["symbol"],
                "timeframe": "1h",
                "timerange": timerange,
                "direction": "long",
                "data_path": str(data_path),
                "strategy_source_path": str(strategy_path),
                "strategy_class_name": leaf["class_name"],
                "strategy_brief": (
                    "Board B single OTE pullback-continuation branch leaf. "
                    "Each OTE level is materialized separately before AQ ranking."
                ),
                "consumer_evidence_profile": {
                    "branch_paths": [leaf["branch_path"]],
                    "branch_path": leaf["branch_path"],
                    "main_regime": "TrendExpansion",
                    "sub_regime": "PullbackContinuation",
                    "sub_sub_regime_or_profit_factor": leaf["sub_sub"],
                    "profit_factor": leaf["profit_factor"],
                    "ote_retrace_ratio": leaf["ratio"],
                    "promotion_allowed": False,
                    "branch_keyed_by_construction": True,
                    "provider": provider["provider"],
                    "local_cache_replay": True,
                    "source_root": str(SOURCE_ROOT),
                    "source_material": str(source_material),
                },
                "evaluation_priority": [
                    "branch_trade_density",
                    "regime_conditioned_win_rate",
                    "profit_factor",
                    "average_adverse_excursion",
                    "walk_forward_survival",
                    "sample_adequacy",
                ],
                "negative_evidence_contract": {
                    "loss_after_branch_keyed_aq": "market_negative_sample",
                    "missing_branch_fields": "identity_negative_sample",
                    "provider_or_fetch_fault": "infrastructure_negative_sample",
                    "low_trade_density": "low_density_negative_sample",
                },
                "notes": [
                    f"source_provider={provider['provider']}",
                    f"source_root={SOURCE_ROOT}",
                    f"source_material={source_material}",
                    f"branch_path={leaf['branch_path']}",
                    f"ote_retrace_ratio={leaf['ratio']}",
                    "local_cache_replay=true",
                    "new_provider_fetch=false",
                    "promotion_allowed=false until AQ dispatch/rank readback and ordered downstream chain pass",
                ],
            }
            material_path.write_text(json.dumps(material, indent=2, sort_keys=True) + "\n")
            materials.append(material_path)

            row = {
                "package_id": package_id,
                "provider": provider["provider"],
                "symbol": provider["symbol"],
                "timeframe": "1h",
                "branch_path": leaf["branch_path"],
                "main_regime": "TrendExpansion",
                "sub_regime": "PullbackContinuation",
                "sub_sub_regime_or_profit_factor": leaf["sub_sub"],
                "profit_factor": leaf["profit_factor"],
                "ote_retrace_ratio": f"{leaf['ratio']:.3f}",
                "data_path": str(data_path),
                "data_rows": str(csv_rows(data_path)),
                "data_sha256": sha256(data_path),
                "source_material": str(source_material),
                "source_material_sha256": sha256(source_material),
                "strategy_source_path": str(strategy_path),
                "strategy_sha256": sha256(strategy_path),
                "local_cache_replay": "true",
                "new_provider_fetch": "false",
            }
            provenance_rows.append(row)
            manifest_rows.append({"path": str(material_path), "sha256": sha256(material_path)})
            manifest_rows.append({"path": str(data_path), "sha256": row["data_sha256"]})

    material_paths = ROOT / "summaries" / "material_paths.csv"
    with material_paths.open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["material"])
        for path in materials:
            writer.writerow([path])

    provenance_path = ROOT / "summaries" / "provider_provenance_matrix.csv"
    with provenance_path.open("w", newline="") as handle:
        fieldnames = list(provenance_rows[0].keys())
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(provenance_rows)

    manifest_path = ROOT / "manifests" / "sha256_manifest.csv"
    with manifest_path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["path", "sha256"])
        writer.writeheader()
        writer.writerows(manifest_rows)

    expected_branches = sorted(leaf["branch_path"] for leaf in OTE_LEAVES)
    assertions = {
        "material_count": len(materials),
        "provider_count": len({row["provider"] for row in provenance_rows}),
        "branch_leaf_count": len({row["branch_path"] for row in provenance_rows}),
        "branch_paths": sorted({row["branch_path"] for row in provenance_rows}),
        "branch_keyed_by_construction": all(
            json.loads(path.read_text())["consumer_evidence_profile"]["branch_paths"]
            == [json.loads(path.read_text())["consumer_evidence_profile"]["branch_path"]]
            for path in materials
        ),
        "provider_rows_per_branch": {
            branch: sum(1 for row in provenance_rows if row["branch_path"] == branch)
            for branch in expected_branches
        },
        "local_cache_replay": all(row["local_cache_replay"] == "true" for row in provenance_rows),
        "new_provider_fetch": False,
        "promotion_allowed": False,
        "trade_usable": False,
        "update_goal": False,
    }
    (ROOT / "summaries" / "ote_leaf_material_summary_v1.json").write_text(
        json.dumps(assertions, indent=2, sort_keys=True) + "\n"
    )

    ok = (
        assertions["material_count"] == 24
        and assertions["provider_count"] == 6
        and assertions["branch_leaf_count"] == 4
        and assertions["branch_paths"] == expected_branches
        and assertions["branch_keyed_by_construction"]
        and all(count == 6 for count in assertions["provider_rows_per_branch"].values())
    )
    (ROOT / "checks" / "ote_leaf_material_assertions.out").write_text(
        "\n".join(f"{key}={value}" for key, value in assertions.items()) + "\n"
    )
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
