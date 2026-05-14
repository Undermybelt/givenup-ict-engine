#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import json
import shutil
from pathlib import Path


ROOT = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260512T193452+0800-codex-macd-momentum-branch-keyed-six-provider-aq-v1"
)
SOURCE_ROOT = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260512T184332+0800-codex-session-liquidity-vwap-opening-range-six-provider-aq-v1"
)

BRANCHES = [
    {
        "branch_slug": "macd-zero-line-reclaim",
        "class_name": "MacdZeroLineReclaimLongV1",
        "title_prefix": "MACD zero-line reclaim",
        "main_regime": "TrendExpansion",
        "sub_regime": "MomentumPersistence",
        "sub_sub_regime_or_profit_factor": "macd_zero_line_reclaim",
        "profit_factor": "macd_zero_line_reclaim_long_v1",
    },
    {
        "branch_slug": "macd-signal-pullback",
        "class_name": "MacdSignalPullbackContinuationV1",
        "title_prefix": "MACD signal pullback continuation",
        "main_regime": "TrendExpansion",
        "sub_regime": "MomentumPersistence",
        "sub_sub_regime_or_profit_factor": "macd_signal_pullback",
        "profit_factor": "macd_signal_pullback_continuation_v1",
    },
]

PROVIDERS = [
    {
        "provider": "yfinance/YF",
        "provider_slug": "yfinance-yf",
        "symbol": "SPY",
        "provider_symbol": "SPY",
        "data_path": SOURCE_ROOT / "data/normalized/yahoo_spy_1h.normalized.csv",
        "source_material": SOURCE_ROOT / "agent-material/session-liquidity-yfinance-yf-1h-v1.material.json",
    },
    {
        "provider": "IBKR",
        "provider_slug": "ibkr",
        "symbol": "SPY",
        "provider_symbol": "SPY",
        "data_path": SOURCE_ROOT / "data/normalized/ibkr_spy_1h_90d.normalized.csv",
        "source_material": SOURCE_ROOT / "agent-material/session-liquidity-ibkr-1h-v1.material.json",
    },
    {
        "provider": "TradingViewRemix/TVR",
        "provider_slug": "tvr-btc-usd",
        "symbol": "BTCUSD",
        "provider_symbol": "BTC-USD",
        "data_path": SOURCE_ROOT / "data/normalized/tvr_btc_usd_1h.normalized.csv",
        "source_material": SOURCE_ROOT / "agent-material/session-liquidity-tvr-btc-usd-1h-v1.material.json",
    },
    {
        "provider": "Kraken",
        "provider_slug": "kraken",
        "symbol": "XBTUSD",
        "provider_symbol": "XBTUSD",
        "data_path": SOURCE_ROOT / "data/normalized/kraken_futures_pfxbtusd_1h.normalized.csv",
        "source_material": SOURCE_ROOT / "agent-material/session-liquidity-kraken-1h-v1.material.json",
    },
    {
        "provider": "Binance",
        "provider_slug": "binance",
        "symbol": "BTCUSDT",
        "provider_symbol": "BTCUSDT",
        "data_path": SOURCE_ROOT / "data/normalized/binance_btcusdt_1h.normalized.csv",
        "source_material": SOURCE_ROOT / "agent-material/session-liquidity-binance-1h-v1.material.json",
    },
    {
        "provider": "Bybit",
        "provider_slug": "bybit",
        "symbol": "BTCUSDT",
        "provider_symbol": "BTCUSDT",
        "data_path": SOURCE_ROOT / "data/normalized/bybit_linear_btcusdt_1h.normalized.csv",
        "source_material": SOURCE_ROOT / "agent-material/session-liquidity-bybit-1h-v1.material.json",
    },
]


ZERO_LINE_STRATEGY = '''from __future__ import annotations

import talib.abstract as ta
from freqtrade.strategy import IStrategy
from pandas import DataFrame


class MacdZeroLineReclaimLongV1(IStrategy):
    INTERFACE_VERSION = 3

    timeframe = "1h"
    can_short = False
    minimal_roi = {"0": 100}
    stoploss = -0.040
    trailing_stop = True
    trailing_stop_positive = 0.010
    trailing_stop_positive_offset = 0.022
    trailing_only_offset_is_reached = True
    process_only_new_candles = True
    use_exit_signal = True
    startup_candle_count: int = 240

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["ema34"] = ta.EMA(dataframe, timeperiod=34)
        dataframe["ema89"] = ta.EMA(dataframe, timeperiod=89)
        dataframe["rsi"] = ta.RSI(dataframe, timeperiod=14)
        macd = ta.MACD(dataframe, fastperiod=12, slowperiod=26, signalperiod=9)
        dataframe["macd"] = macd["macd"]
        dataframe["macdsignal"] = macd["macdsignal"]
        dataframe["macdhist"] = macd["macdhist"]
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["enter_long"] = 0
        dataframe["enter_tag"] = ""
        trend = (dataframe["close"] > dataframe["ema34"]) & (dataframe["ema34"] > dataframe["ema89"])
        zero_reclaim = (dataframe["macd"] > 0) & (dataframe["macd"].shift(1) <= 0)
        momentum_ok = dataframe["rsi"].between(44, 72) & (dataframe["macdhist"] > dataframe["macdhist"].shift(1))
        entry = trend & zero_reclaim & momentum_ok
        dataframe.loc[entry, "enter_long"] = 1
        dataframe.loc[entry, "enter_tag"] = "macd_zero_line_reclaim_long_v1"
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["exit_long"] = 0
        exit_signal = (dataframe["macd"] < dataframe["macdsignal"]) | (dataframe["close"] < dataframe["ema34"]) | (dataframe["rsi"] > 78)
        dataframe.loc[exit_signal, "exit_long"] = 1
        return dataframe
'''


SIGNAL_PULLBACK_STRATEGY = '''from __future__ import annotations

import talib.abstract as ta
from freqtrade.strategy import IStrategy
from pandas import DataFrame


class MacdSignalPullbackContinuationV1(IStrategy):
    INTERFACE_VERSION = 3

    timeframe = "1h"
    can_short = False
    minimal_roi = {"0": 100}
    stoploss = -0.045
    trailing_stop = True
    trailing_stop_positive = 0.012
    trailing_stop_positive_offset = 0.026
    trailing_only_offset_is_reached = True
    process_only_new_candles = True
    use_exit_signal = True
    startup_candle_count: int = 240

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["ema21"] = ta.EMA(dataframe, timeperiod=21)
        dataframe["ema55"] = ta.EMA(dataframe, timeperiod=55)
        dataframe["rsi"] = ta.RSI(dataframe, timeperiod=14)
        macd = ta.MACD(dataframe, fastperiod=12, slowperiod=26, signalperiod=9)
        dataframe["macd"] = macd["macd"]
        dataframe["macdsignal"] = macd["macdsignal"]
        dataframe["macdhist"] = macd["macdhist"]
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["enter_long"] = 0
        dataframe["enter_tag"] = ""
        trend = (dataframe["close"] > dataframe["ema55"]) & (dataframe["ema21"] > dataframe["ema55"])
        signal_reclaim = (dataframe["macd"] > dataframe["macdsignal"]) & (dataframe["macd"].shift(1) <= dataframe["macdsignal"].shift(1))
        pullback_zone = (dataframe["macd"] > 0) & dataframe["rsi"].between(40, 68)
        entry = trend & signal_reclaim & pullback_zone
        dataframe.loc[entry, "enter_long"] = 1
        dataframe.loc[entry, "enter_tag"] = "macd_signal_pullback_continuation_v1"
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["exit_long"] = 0
        exit_signal = (dataframe["macd"] < 0) | (dataframe["close"] < dataframe["ema55"]) | (dataframe["rsi"] > 80)
        dataframe.loc[exit_signal, "exit_long"] = 1
        return dataframe
'''

STRATEGIES = {
    "MacdZeroLineReclaimLongV1": ZERO_LINE_STRATEGY,
    "MacdSignalPullbackContinuationV1": SIGNAL_PULLBACK_STRATEGY,
}


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


def branch_path(branch: dict[str, str]) -> str:
    return " -> ".join(
        [
            branch["main_regime"],
            branch["sub_regime"],
            branch["sub_sub_regime_or_profit_factor"],
            branch["profit_factor"],
        ]
    )


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    for rel in [
        "agent-material",
        "checks",
        "command-output",
        "data/normalized",
        "manifests",
        "summaries",
    ]:
        (ROOT / rel).mkdir(parents=True, exist_ok=True)

    strategy_paths: dict[str, Path] = {}
    for class_name, source in STRATEGIES.items():
        path = ROOT / "agent-material" / f"{class_name}.py"
        path.write_text(source, encoding="utf-8")
        strategy_paths[class_name] = path

    materials: list[Path] = []
    provenance_rows: list[dict[str, object]] = []
    material_rows: list[dict[str, object]] = []
    manifest_rows: list[dict[str, object]] = []

    for provider in PROVIDERS:
        if not provider["data_path"].exists():
            raise SystemExit(f"missing data_path: {provider['data_path']}")
        if not provider["source_material"].exists():
            raise SystemExit(f"missing source_material: {provider['source_material']}")

        target_data = ROOT / "data/normalized" / Path(provider["data_path"]).name
        shutil.copy2(provider["data_path"], target_data)
        data_hash = sha256(target_data)
        source_material_hash = sha256(provider["source_material"])
        row_count = csv_rows(target_data)
        source = json.loads(Path(provider["source_material"]).read_text())
        timerange = source.get("timerange", "20250101-20260512")

        for branch in BRANCHES:
            path = branch_path(branch)
            package_id = f"{branch['branch_slug']}-{provider['provider_slug']}-1h-v1"
            material_path = ROOT / "agent-material" / f"{package_id}.material.json"
            title = f"{branch['title_prefix']} - {provider['provider']} {provider['provider_symbol']} 1h"
            material = {
                "package_id": package_id,
                "title": title,
                "symbol": provider["symbol"],
                "timeframe": "1h",
                "timerange": timerange,
                "direction": "long",
                "data_path": str(target_data),
                "strategy_source_path": str(strategy_paths[branch["class_name"]]),
                "strategy_class_name": branch["class_name"],
                "strategy_brief": "Board B MACD momentum branch-keyed profitability factor replay.",
                "consumer_evidence_profile": {
                    "branch_paths": [path],
                    "branch_path": path,
                    "main_regime": branch["main_regime"],
                    "sub_regime": branch["sub_regime"],
                    "sub_sub_regime_or_profit_factor": branch["sub_sub_regime_or_profit_factor"],
                    "profit_factor": branch["profit_factor"],
                    "branch_keyed_by_construction": True,
                    "provider": provider["provider"],
                    "local_cache_replay": True,
                    "new_provider_fetch": False,
                    "source_root": str(SOURCE_ROOT),
                    "source_material": str(provider["source_material"]),
                    "promotion_allowed": False,
                    "trade_usable": False,
                },
                "evaluation_priority": [
                    "branch_trade_density",
                    "regime_conditioned_win_rate",
                    "profit_factor",
                    "cross_provider_survival",
                    "sample_adequacy",
                ],
                "negative_evidence_contract": {
                    "profitable_but_low_density": "low_density_weak_positive_provider_sample",
                    "loss_after_adequate_density": "market_factor_negative_sample",
                    "provider_zero_trades": "low_density_negative_sample",
                    "provider_or_runtime_fault": "infrastructure_negative_sample",
                    "missing_branch_fields": "identity_negative_sample",
                },
                "notes": [
                    f"source_provider={provider['provider']}",
                    f"source_root={SOURCE_ROOT}",
                    f"source_material={provider['source_material']}",
                    f"branch_path={path}",
                    "branch_fields_explicit=true",
                    "local_cache_replay=true",
                    "new_provider_fetch=false",
                    "promotion_allowed=false until AQ and downstream gates pass",
                ],
            }
            material_path.write_text(json.dumps(material, indent=2, sort_keys=True) + "\n")
            materials.append(material_path)
            material_hash = sha256(material_path)
            row = {
                "package_id": package_id,
                "provider": provider["provider"],
                "symbol": provider["symbol"],
                "provider_symbol": provider["provider_symbol"],
                "timeframe": "1h",
                "branch_path": path,
                "main_regime": branch["main_regime"],
                "sub_regime": branch["sub_regime"],
                "sub_sub_regime_or_profit_factor": branch["sub_sub_regime_or_profit_factor"],
                "profit_factor": branch["profit_factor"],
                "strategy_class_name": branch["class_name"],
                "material_path": str(material_path),
                "material_sha256": material_hash,
                "data_path": str(target_data),
                "data_rows": row_count,
                "data_sha256": data_hash,
                "source_material": str(provider["source_material"]),
                "source_material_sha256": source_material_hash,
                "local_cache_replay": "true",
                "new_provider_fetch": "false",
                "provider_authority_state": "replay_from_184332_provider_preflight",
            }
            provenance_rows.append(row)
            material_rows.append(row)
            manifest_rows.append({"path": str(material_path), "sha256": material_hash})

        manifest_rows.append({"path": str(target_data), "sha256": data_hash})
        manifest_rows.append({"path": str(provider["source_material"]), "sha256": source_material_hash})

    write_csv(ROOT / "summaries" / "material_paths.csv", [{"material": str(path)} for path in materials], ["material"])
    write_csv(
        ROOT / "summaries" / "provider_provenance_matrix.csv",
        provenance_rows,
        list(provenance_rows[0].keys()),
    )
    write_csv(
        ROOT / "summaries" / "branch_material_matrix.csv",
        material_rows,
        list(material_rows[0].keys()),
    )
    write_csv(ROOT / "manifests" / "sha256_manifest.csv", manifest_rows, ["path", "sha256"])

    branch_paths = sorted({row["branch_path"] for row in material_rows})
    providers = sorted({row["provider"] for row in material_rows})
    assertions = {
        "material_count": len(materials),
        "provider_count": len(providers),
        "branch_leaf_count": len(branch_paths),
        "providers": providers,
        "branch_paths": branch_paths,
        "branch_keyed_by_construction": True,
        "explicit_branch_fields": all(
            row["main_regime"]
            and row["sub_regime"]
            and row["sub_sub_regime_or_profit_factor"]
            and row["profit_factor"]
            for row in material_rows
        ),
        "local_cache_replay": True,
        "new_provider_fetch": False,
        "promotion_allowed": False,
        "trade_usable": False,
        "update_goal": False,
    }
    (ROOT / "summaries" / "macd_momentum_material_summary_v1.json").write_text(
        json.dumps(assertions, indent=2, sort_keys=True) + "\n"
    )
    (ROOT / "checks" / "macd_momentum_material_assertions.out").write_text(
        "\n".join(f"{key}={value}" for key, value in assertions.items()) + "\n"
    )

    ok = (
        assertions["material_count"] == 12
        and assertions["provider_count"] == 6
        and assertions["branch_leaf_count"] == 2
        and assertions["explicit_branch_fields"]
        and assertions["branch_keyed_by_construction"]
        and not assertions["new_provider_fetch"]
    )
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
