from __future__ import annotations

import argparse
import json
from pathlib import Path

try:
    from .mim_cost_window_event_builder import CONTEXT_TIMEFRAMES, build_event_rows, build_summary, write_jsonl
except ImportError:  # pragma: no cover - exercised by direct script execution.
    from mim_cost_window_event_builder import CONTEXT_TIMEFRAMES, build_event_rows, build_summary, write_jsonl


def build_material_bundle(
    input_csv: Path,
    output_dir: Path,
    *,
    symbol: str,
    provider: str,
    market: str,
    product: str,
    branch_path: str,
    factor_id: str,
) -> dict[str, object]:
    root = Path(output_dir)
    root.mkdir(parents=True, exist_ok=True)
    events_path = root / "mim_cost_window_events.jsonl"
    event_summary_path = root / "mim_cost_window_event_summary.json"
    strategy_path = root / f"{_strategy_class_name(factor_id)}.py"
    material_path = root / f"{_slug(factor_id)}.material.json"
    summary_path = root / "mim_cost_window_material_summary.json"

    events = build_event_rows(
        input_csv,
        symbol=symbol,
        provider=provider,
        market=market,
        product=product,
        branch_path=branch_path,
    )
    write_jsonl(events_path, events)
    event_summary_path.write_text(json.dumps(build_summary(events), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    strategy_class = _strategy_class_name(factor_id)
    strategy_path.write_text(_strategy_source(strategy_class, factor_id), encoding="utf-8")

    branch_parts = _branch_parts(branch_path)
    material = {
        "package_id": _slug(factor_id),
        "title": f"{symbol} MIM cost-window retained-real Gate 1 prep",
        "symbol": symbol,
        "timeframe": "1m",
        "timerange": _timerange(events),
        "direction": "long",
        "data_path": str(input_csv),
        "strategy_source_path": str(strategy_path),
        "strategy_class_name": strategy_class,
        "strategy_brief": (
            "Market intraday momentum cost-window candidate using first-window return, "
            "spread proxies, relative volume, posterior proxy, and triple-barrier labels."
        ),
        "evaluation_priority": [
            "source_backed_intraday_momentum",
            "exact_1m_cost_density",
            "branch_path_preservation",
            "provider_parity_later",
        ],
        "consumer_evidence_profile": {
            "branch_path": branch_path,
            "regime_profit_branch_path": branch_path,
            "branch_id": factor_id,
            "main_regime": branch_parts[0] if branch_parts else "",
            "sub_regime": branch_parts[1] if len(branch_parts) > 1 else "",
            "sub_sub_regime_or_profit_factor": branch_parts[2] if len(branch_parts) > 2 else "",
            "profit_factor": branch_parts[-1] if branch_parts else factor_id,
            "base_timeframe": "1m",
            "context_timeframes": list(CONTEXT_TIMEFRAMES),
            "training_timeframe": "1m",
            "material_timeframe": "1m",
            "provider": provider,
            "provider_provenance": f"{provider} retained 1m rows for {symbol}",
            "market": market,
            "product": product,
            "source_backed_family": "market_intraday_momentum_cost_window",
            "gate_id": "Gate1MimCostWindowRetainedRealPrep",
            "event_count": len(events),
            "eligible_long_count": sum(1 for row in events if row.get("side") == 1),
            "promotion_allowed": False,
            "trade_usable": False,
            "downstream_allowed": False,
            "update_goal": False,
        },
        "notes": [
            "provider_fetch_started=false",
            "auto_quant_started=false",
            "pre_bayes_bbn_catboost_execution_tree_allowed=false_until_gate1_passes",
        ],
    }
    material_path.write_text(json.dumps(material, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    summary = {
        "symbol": symbol,
        "factor_id": factor_id,
        "branch_path": branch_path,
        "event_count": len(events),
        "eligible_long_count": material["consumer_evidence_profile"]["eligible_long_count"],
        "material_path": str(material_path),
        "strategy_source_path": str(strategy_path),
        "events_jsonl": str(events_path),
        "event_summary": str(event_summary_path),
        "promotion_allowed": False,
        "trade_usable": False,
        "downstream_allowed": False,
        "provider_fetch_started": False,
        "auto_quant_started": False,
    }
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build a no-provider MIM cost-window material prep bundle.")
    parser.add_argument("--input-csv", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--symbol", required=True)
    parser.add_argument("--provider", required=True)
    parser.add_argument("--market", required=True)
    parser.add_argument("--product", required=True)
    parser.add_argument("--branch-path", required=True)
    parser.add_argument("--factor-id", required=True)
    args = parser.parse_args(argv)
    summary = build_material_bundle(
        args.input_csv,
        args.output_dir,
        symbol=args.symbol,
        provider=args.provider,
        market=args.market,
        product=args.product,
        branch_path=args.branch_path,
        factor_id=args.factor_id,
    )
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


def _strategy_source(class_name: str, factor_id: str) -> str:
    return f'''from freqtrade.strategy import IStrategy
from pandas import DataFrame


class {class_name}(IStrategy):
    INTERFACE_VERSION = 3
    timeframe = "1m"
    can_short = False
    minimal_roi = {{"0": 0.0025}}
    stoploss = -0.0050
    trailing_stop = True
    trailing_stop_positive = 0.0008
    trailing_stop_positive_offset = 0.0025
    trailing_only_offset_is_reached = True
    process_only_new_candles = True
    use_exit_signal = True
    startup_candle_count = 120

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe = dataframe.sort_values("date").copy()
        typical = (dataframe["high"] + dataframe["low"] + dataframe["close"]) / 3.0
        day_key = dataframe["date"].dt.strftime("%Y-%m-%d")
        minute = dataframe["date"].dt.hour * 60 + dataframe["date"].dt.minute
        regular = (minute >= 13 * 60 + 30) & (minute <= 20 * 60)
        first = (minute >= 13 * 60 + 30) & (minute < 14 * 60)
        late = (minute >= 19 * 60 + 30) & (minute < 20 * 60)
        dataframe["late_window"] = late
        dataframe["force_exit_window"] = minute >= 20 * 60
        dataframe["session_open"] = dataframe["open"].where(minute == 13 * 60 + 30).groupby(day_key).transform("first").ffill()
        dataframe["first_window_close"] = dataframe["close"].where(first).groupby(day_key).transform("last").ffill()
        dataframe["first_window_high"] = dataframe["high"].where(first).groupby(day_key).transform("max").ffill()
        dataframe["first_window_low"] = dataframe["low"].where(first).groupby(day_key).transform("min").ffill()
        dataframe["first_window_return"] = (dataframe["first_window_close"] - dataframe["session_open"]) / dataframe["session_open"]
        dataframe["basic_high_low_spread"] = (dataframe["first_window_high"] - dataframe["first_window_low"]) / dataframe["session_open"]
        dataframe["vwap"] = (typical * dataframe["volume"]).where(regular).groupby(day_key).cumsum() / dataframe["volume"].where(regular).groupby(day_key).cumsum()
        dataframe["rvol"] = dataframe["volume"] / dataframe["volume"].rolling(60).mean().replace(0, 1)
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["enter_long"] = 0
        dataframe["enter_tag"] = ""
        signal = (
            dataframe["late_window"]
            & (dataframe["first_window_return"] >= 0.0015)
            & (dataframe["basic_high_low_spread"].between(0.0002, 0.018))
            & (dataframe["close"] >= dataframe["vwap"])
            & (dataframe["rvol"] >= 0.45)
        )
        dataframe.loc[signal, ["enter_long", "enter_tag"]] = (1, "{factor_id}")
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["exit_long"] = 0
        dataframe.loc[dataframe["force_exit_window"] | (dataframe["close"] < dataframe["vwap"] * 0.999), "exit_long"] = 1
        return dataframe
'''


def _timerange(events: list[dict[str, object]]) -> str:
    dates = [str(row.get("event_date") or "").replace("-", "") for row in events if row.get("event_date")]
    return f"{min(dates)}-{max(dates)}" if dates else ""


def _branch_parts(branch_path: str) -> list[str]:
    return [part.strip() for part in branch_path.split("->") if part.strip()]


def _strategy_class_name(factor_id: str) -> str:
    return "".join(part.title() for part in _slug(factor_id).split("-")) + "Strategy"


def _slug(value: str) -> str:
    return value.strip().lower().replace("_", "-").replace(" ", "-")


if __name__ == "__main__":
    raise SystemExit(main())
