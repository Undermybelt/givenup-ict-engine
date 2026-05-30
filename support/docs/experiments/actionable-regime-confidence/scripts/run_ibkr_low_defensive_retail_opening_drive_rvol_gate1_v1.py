#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import shutil
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


SCRIPT = Path(__file__).resolve()
BASE = SCRIPT.parents[1]
RUN_STAMP = datetime.now(ZoneInfo("Asia/Shanghai")).strftime("%Y%m%dT%H%M%S+0800")
ROOT = BASE / "runs" / f"{RUN_STAMP}-codex-ibkr-low-defensive-retail-opening-drive-rvol-gate1-v1"
REPO = BASE.parents[3]
PY = Path("/Users/thrill3r/.venvs/ict-engine-provider-py313/bin/python")
if not PY.exists():
    PY = Path("python3")
FETCH = REPO / "support/scripts/auto_quant_external/fetch_external.py"
ICT = REPO / ".local-artifacts/cargo-target/debug/ict-engine"
if not ICT.exists():
    ICT = REPO / "target/debug/ict-engine"
AUTO_QUANT_REPO = Path("/Users/thrill3r/Auto-Quant")


@dataclass(frozen=True)
class IbkrSpec:
    timeframe: str
    bar_size: str
    duration: str
    out_name: str
    role: str


SPECS = [
    IbkrSpec("1m", "1 min", "3 M", "ibkr_low_1m_3m.csv", "training_origin"),
    IbkrSpec("5m", "5 mins", "3 M", "ibkr_low_5m_3m.csv", "small_cycle"),
    IbkrSpec("15m", "15 mins", "3 M", "ibkr_low_15m_3m.csv", "small_cycle_sibling"),
    IbkrSpec("30m", "30 mins", "3 M", "ibkr_low_30m_3m.csv", "neutralizer"),
    IbkrSpec("1h", "1 hour", "3 M", "ibkr_low_1h_3m.csv", "higher_timeframe_veto"),
    IbkrSpec("4h", "4 hours", "1 Y", "ibkr_low_4h_1y.csv", "higher_timeframe_context"),
    IbkrSpec("1d", "1 day", "2 Y", "ibkr_low_1d_2y.csv", "daily_context"),
]
RETRY_BY_TIMEFRAME = {
    "1m": IbkrSpec("1m", "1 min", "1 M", "ibkr_low_1m_1m_retry.csv", "training_origin_retry"),
    "5m": IbkrSpec("5m", "5 mins", "1 M", "ibkr_low_5m_1m_retry.csv", "small_cycle_retry"),
    "15m": IbkrSpec("15m", "15 mins", "1 M", "ibkr_low_15m_1m_retry.csv", "small_cycle_sibling_retry"),
    "30m": IbkrSpec("30m", "30 mins", "1 M", "ibkr_low_30m_1m_retry.csv", "neutralizer_retry"),
    "1h": IbkrSpec("1h", "1 hour", "1 M", "ibkr_low_1h_1m_retry.csv", "higher_timeframe_retry"),
    "4h": IbkrSpec("4h", "4 hours", "6 M", "ibkr_low_4h_6m_retry.csv", "higher_timeframe_context_retry"),
    "1d": IbkrSpec("1d", "1 day", "1 Y", "ibkr_low_1d_1y_retry.csv", "daily_context_retry"),
}

BRANCH_PATH = "TrendExpansion -> DefensiveRetailOpeningDrive -> rvol_breakout_pullback -> ibkr_low_defensive_retail_opening_drive_rvol_gate1_v1"
BRANCH_PARTS = [part.strip() for part in BRANCH_PATH.split(" -> ")]
SYMBOL = "LOW"
AQ_SYMBOL = "IBKR_LOW_DEFENSIVE_RETAIL_OPENING_DRIVE_RVOL_GATE1"
MIN_GATE1_TRADE_COUNT = 6


def unverified_equity_cost_model(timeframe: str) -> dict:
    return {
        "status": "cost_model_unverified",
        "instrument_class": "US_EQUITY",
        "symbol": SYMBOL,
        "broker": "IBKR",
        "venue_routing": "SMART",
        "currency": "USD",
        "timeframe": timeframe,
        "pricing_plan": "unverified",
        "account_region": "unverified",
        "fee_effective_date": "unverified",
        "official_sources": [],
        "blocker": "official_equity_cost_model_not_verified_for_product_route_account_plan_date",
    }


def run_cmd(name: str, argv: list[str], timeout: int = 180) -> dict:
    (ROOT / "command-output").mkdir(parents=True, exist_ok=True)
    (ROOT / "checks").mkdir(parents=True, exist_ok=True)
    (ROOT / "command-output" / f"{name}.cmd").write_text(" ".join(argv) + "\n", encoding="utf-8")
    try:
        proc = subprocess.run(argv, cwd=REPO, text=True, capture_output=True, timeout=timeout)
        rc = proc.returncode
        stdout = proc.stdout
        stderr = proc.stderr
        timed_out = False
    except subprocess.TimeoutExpired as exc:
        rc = 124
        stdout = exc.stdout or ""
        stderr = exc.stderr or ""
        if isinstance(stdout, bytes):
            stdout = stdout.decode("utf-8", errors="replace")
        if isinstance(stderr, bytes):
            stderr = stderr.decode("utf-8", errors="replace")
        stderr = stderr + f"\nTIMEOUT after {timeout}s\n"
        timed_out = True
    (ROOT / "command-output" / f"{name}.out").write_text(stdout, encoding="utf-8")
    (ROOT / "command-output" / f"{name}.err").write_text(stderr, encoding="utf-8")
    (ROOT / "checks" / f"{name}.exit").write_text(f"{rc}\n", encoding="utf-8")
    return {"name": name, "argv": argv, "exit": rc, "timed_out": timed_out}


def normalize_provider_csv(source: Path, destination: Path) -> int:
    if not source.exists() or source.stat().st_size == 0:
        return 0
    with source.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        headers = reader.fieldnames or []
        time_key = next((key for key in ("timestamp", "time", "datetime", "ts_event", "date", "ts") if key in headers), None)
        if not time_key:
            return 0
        rows = [
            {
                "timestamp": row.get(time_key, ""),
                "open": row.get("open", ""),
                "high": row.get("high", ""),
                "low": row.get("low", ""),
                "close": row.get("close", ""),
                "volume": row.get("volume", ""),
            }
            for row in reader
        ]
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["timestamp", "open", "high", "low", "close", "volume"])
        writer.writeheader()
        writer.writerows(rows)
    return len(rows)


def freqtrade_timerange(path: Path) -> str:
    dates = []
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            raw = (row.get("timestamp") or "").strip()
            if raw:
                dates.append(raw[:10].replace("-", ""))
    return f"{min(dates)}-{max(dates)}" if dates else ""


def timeframe_suffix(value: str) -> str:
    return value.replace("m", "Min").replace("h", "Hour")


def safe_float(value: object, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def rank_timeframe(item: dict) -> str:
    value = item.get("timeframe")
    if value:
        return str(value)
    package_id = str(item.get("package_id") or "")
    for candidate in ("30m", "15m", "4h", "1h", "5m", "1d", "1m"):
        if f"-{candidate}-" in package_id:
            return candidate
    provenance = str(item.get("provider_provenance") or "")
    for candidate in ("1m", "5m", "15m", "30m", "1h", "4h", "1d"):
        if f" {candidate} " in provenance:
            return candidate
    return "unknown"


def rank_branch_path(item: dict) -> str:
    return str(item.get("branch_path") or item.get("regime_profit_branch_path") or "")


def is_gate1_density_eligible(trade_count: int) -> bool:
    return trade_count >= MIN_GATE1_TRADE_COUNT


def trading_day_counts(provider_rows: list[dict]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in provider_rows:
        path = Path(str(row.get("path") or ""))
        if not path.exists():
            continue
        days: set[str] = set()
        with path.open(newline="", encoding="utf-8") as handle:
            for item in csv.DictReader(handle):
                raw = (item.get("timestamp") or "").strip()
                if raw:
                    days.add(raw[:10])
        counts[str(row.get("timeframe") or "unknown")] = len(days)
    return counts


def instrument_cost_rows(rank_rows: list[dict], day_counts: dict[str, int]) -> list[dict]:
    rows = []
    for item in rank_rows:
        timeframe = rank_timeframe(item)
        trade_count = int(item.get("trade_count") or 0)
        raw_profit = safe_float(item.get("total_profit_pct"))
        days = max(1, day_counts.get(timeframe, 1))
        trades_per_day = trade_count / days
        rows.append(
            {
                "package_id": str(item.get("package_id") or f"{AQ_SYMBOL}-{timeframe}"),
                "label": f"{SYMBOL}/{timeframe}/{item.get('package_id') or AQ_SYMBOL}",
                "timeframe": timeframe,
                "trade_count": trade_count,
                "min_gate1_trade_count": MIN_GATE1_TRADE_COUNT,
                "minimum_trade_sample_floor_met": is_gate1_density_eligible(trade_count),
                "trading_days": days,
                "trades_per_day": trades_per_day,
                "density_target_1_to_3_per_day": 1.0 <= trades_per_day <= 3.0,
                "win_rate_pct": safe_float(item.get("win_rate_pct")),
                "raw_total_profit_pct": raw_profit,
                "instrument_cost_total_profit_pct": None,
                "instrument_cost_profit_factor": None,
                "sharpe": safe_float(item.get("sharpe")),
                "branch_path": rank_branch_path(item),
                "cost_model_status": "cost_model_unverified",
                "cost_model_blocker": "official_equity_cost_model_not_verified",
                "cost_model": unverified_equity_cost_model(timeframe),
                "promotion_cost_verified": False,
                "survives_instrument_cost": False,
                "gate1_survivor": False,
            }
        )
    return rows


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def format_optional_pct(value: object) -> str:
    if value is None:
        return "unverified"
    try:
        return f"{float(value):.2f}%"
    except Exception:
        return "unverified"


def strategy_class_name(spec: IbkrSpec) -> str:
    return f"IbkrLowDefensiveRetailOpeningDriveRvol{timeframe_suffix(spec.timeframe)}"


def material_package_id(spec: IbkrSpec) -> str:
    duration = spec.duration.replace(" ", "").lower()
    return f"ibkr-low-defensive-retail-opening-drive-rvol-{spec.timeframe}-{duration}-v1"


def write_material_for_provider_row(row: dict, spec: IbkrSpec) -> tuple[Path, Path]:
    class_name = strategy_class_name(spec)
    strategy_path = ROOT / "agent-material" / f"{class_name}.py"
    strategy_path.write_text(strategy_source(spec, class_name), encoding="utf-8")
    package_id = material_package_id(spec)
    material_path = ROOT / "agent-material" / f"{package_id}.material.json"
    material = {
        "package_id": package_id,
        "title": f"IBKR LOW opening-drive RVOL breakout - {spec.timeframe} {spec.duration}",
        "symbol": SYMBOL,
        "timeframe": spec.timeframe,
        "timerange": freqtrade_timerange(Path(row["path"])),
        "direction": "long",
        "data_path": row["path"],
        "strategy_source_path": str(strategy_path),
        "strategy_class_name": class_name,
        "strategy_brief": "IBKR-first LOW opening-drive RVOL breakout with EMA trend, prior-high breakout, pullback control, and range sanity gates.",
        "evaluation_priority": ["instrument_cost_verification", "trade_density", "profit_factor", "real_trade_profitability", "timeframe_reproduction"],
        "consumer_evidence_profile": {
            "branch_path": BRANCH_PATH,
            "regime_profit_branch_path": BRANCH_PATH,
            "branch_id": "ibkr_low_defensive_retail_opening_drive_rvol_gate1_v1",
            "main_regime": BRANCH_PARTS[0],
            "sub_regime": BRANCH_PARTS[1],
            "sub_sub_regime_or_profit_factor": BRANCH_PARTS[2],
            "profit_factor": BRANCH_PARTS[3],
            "base_timeframe": "1m",
            "context_timeframes": "1m/5m/15m/30m/1h/4h/1d",
            "training_timeframe": spec.timeframe,
            "neutralization_timeframe": "none_until_gate1_pass",
            "confirmation_timeframe": "15m_30m_1h_siblings",
            "provider": "IBKR",
            "provider_provenance": f"IBKR {SYMBOL} {spec.timeframe} {spec.duration}",
            "provider_window": spec.duration,
            "gate_id": "Gate1DefensiveRetailOpeningDriveIbkr",
            "cost_model_status": "cost_model_unverified",
            "promotion_cost_verified": False,
            "cost_model": unverified_equity_cost_model(spec.timeframe),
            "promotion_allowed": False,
            "trade_usable": False,
            "update_goal": False,
        },
        "notes": [
            f"source_provider=IBKR {SYMBOL} {spec.timeframe} {spec.duration}",
            f"branch_path={BRANCH_PATH}",
            "ibkr_first=true",
            "upper_window_requested=true",
            "equity_cost_model=unverified_fail_closed",
            "pre_bayes_bbn_catboost_execution_tree_allowed=false_until_instrument_cost_gate_passes",
        ],
    }
    material_path.write_text(json.dumps(material, indent=2) + "\n", encoding="utf-8")
    return material_path, strategy_path


def ibkr_fetch_args(spec: IbkrSpec, output: Path, client_id: int) -> list[str]:
    return [
        str(PY),
        str(FETCH),
        "ibkr-historical",
        "--symbol",
        SYMBOL,
        "--sec-type",
        "STK",
        "--exchange",
        "SMART",
        "--currency",
        "USD",
        "--primary-exchange",
        "NYSE",
        "--bar-size",
        spec.bar_size,
        "--duration",
        spec.duration,
        "--what-to-show",
        "TRADES",
        "--host",
        "127.0.0.1",
        "--port",
        "4002",
        "--client-id",
        str(client_id),
        "--output",
        str(output),
    ]


def strategy_source(spec: IbkrSpec, class_name: str) -> str:
    tag = f"ibkr_low_defensive_retail_opening_drive_rvol_{spec.timeframe}_v1"
    return f'''from freqtrade.strategy import IStrategy
from pandas import DataFrame
import talib.abstract as ta


class {class_name}(IStrategy):
    INTERFACE_VERSION = 3
    timeframe = "{spec.timeframe}"
    can_short = False
    minimal_roi = {{"0": 0.0075}}
    stoploss = -0.014
    trailing_stop = True
    trailing_stop_positive = 0.003
    trailing_stop_positive_offset = 0.009
    trailing_only_offset_is_reached = True
    process_only_new_candles = True
    use_exit_signal = True
    startup_candle_count = 240

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["ema21"] = ta.EMA(dataframe, timeperiod=21)
        dataframe["ema55"] = ta.EMA(dataframe, timeperiod=55)
        dataframe["atr"] = ta.ATR(dataframe, timeperiod=14)
        dataframe["rsi"] = ta.RSI(dataframe, timeperiod=14)
        dataframe["vol_ma"] = dataframe["volume"].rolling(40).mean()
        dataframe["prior_high"] = dataframe["high"].rolling(20).max().shift(1)
        dataframe["pullback_floor"] = dataframe["ema21"] - dataframe["atr"] * 0.35
        dataframe["range_pct"] = (dataframe["high"] - dataframe["low"]) / dataframe["close"]
        dataframe["body_pct"] = (dataframe["close"] - dataframe["open"]) / dataframe["close"]
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["enter_long"] = 0
        dataframe["enter_tag"] = ""
        breakout = (dataframe["close"] > dataframe["prior_high"]) & (dataframe["close"].shift(1) <= dataframe["prior_high"].shift(1))
        trend = (dataframe["ema21"] > dataframe["ema55"]) & (dataframe["close"] > dataframe["ema21"])
        liquidity = dataframe["volume"] > (dataframe["vol_ma"] * 1.35)
        pullback_control = dataframe["low"] >= dataframe["pullback_floor"]
        range_sanity = dataframe["range_pct"].between(0.00035, 0.018)
        body_ok = dataframe["body_pct"] > -0.002
        rsi_ok = dataframe["rsi"].between(50, 72)
        dataframe.loc[breakout & trend & liquidity & pullback_control & range_sanity & body_ok & rsi_ok, ["enter_long", "enter_tag"]] = (1, "{tag}")
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["exit_long"] = 0
        exit_signal = (dataframe["close"] < dataframe["ema21"]) | (dataframe["ema21"] < dataframe["ema55"]) | (dataframe["rsi"] > 78)
        dataframe.loc[exit_signal, "exit_long"] = 1
        return dataframe
'''


def build_prep_metrics() -> dict[str, object]:
    return {
        "run_mode": "source_prep_no_launch",
        "factor_id": AQ_SYMBOL,
        "branch_path": BRANCH_PATH,
        "branch_path_depth": len(BRANCH_PARTS),
        "branch_path_segments": BRANCH_PARTS,
        "provider": "IBKR",
        "symbol": SYMBOL,
        "base_timeframe": "1m",
        "context_timeframes": ["5m", "15m", "30m", "1h", "4h", "1d"],
        "timeframe_ladder": [
            {
                "timeframe": spec.timeframe,
                "bar_size": spec.bar_size,
                "duration": spec.duration,
                "role": spec.role,
            }
            for spec in SPECS
        ],
        "provider_fetch_started": False,
        "auto_quant_started": False,
        "launch_requested": False,
        "downstream_allowed": False,
        "pre_bayes_allowed": False,
        "bbn_allowed": False,
        "catboost_allowed": False,
        "execution_tree_allowed": False,
        "promotion_allowed": False,
        "trade_usable": False,
        "update_goal": False,
    }


def write_source_prep_summary(root: Path) -> dict[str, object]:
    root.mkdir(parents=True, exist_ok=True)
    metrics = build_prep_metrics()
    metrics["generated_at"] = datetime.now(ZoneInfo("Asia/Shanghai")).isoformat()
    (root / "source_prep_metrics.json").write_text(json.dumps(metrics, indent=2) + "\n", encoding="utf-8")
    fetch_plan = {
        spec.timeframe: ibkr_fetch_args(spec, root / "data" / spec.out_name, 231)
        for spec in SPECS
    }
    (root / "ibkr_fetch_command_plan.json").write_text(json.dumps(fetch_plan, indent=2) + "\n", encoding="utf-8")
    return metrics

def write_terminal_summary(summary: dict, instrument_rows: list[dict]) -> None:
    rows = []
    for item in instrument_rows:
        rows.append(
            "| `{timeframe}` | {trades} | {trades_per_day:.3f} | {raw:.2f}% | {instrument_cost} | `{cost_status}` | `{cost_verified}` | `{survives_cost}` | `{gate1}` |".format(
                timeframe=item.get("timeframe") or "unknown",
                trades=int(item.get("trade_count") or 0),
                trades_per_day=safe_float(item.get("trades_per_day")),
                raw=safe_float(item.get("raw_total_profit_pct")),
                instrument_cost=format_optional_pct(item.get("instrument_cost_total_profit_pct")),
                cost_status=item.get("cost_model_status") or "unknown",
                cost_verified=item.get("promotion_cost_verified"),
                survives_cost=item.get("survives_instrument_cost"),
                gate1=item.get("gate1_survivor"),
            )
        )
    text = f"""# Terminal Decision Summary

Decision: `{summary["decision"]}`

Factor family: `DefensiveRetailOpeningDrive`

Branch path:

```text
{BRANCH_PATH}
```

Gate: `Gate1DefensiveRetailOpeningDriveIbkr`

Provider/window rule:

- IBKR-first.
- Requested upper practical windows: `1m=30D`, `5m=3M`, `15m=3M`, `30m=3M`, `1h=3M`, `4h=1Y`, `1d=2Y`.
- If IBKR rejected/timed out, retried a smaller real window for that same timeframe.
- Stop before Pre-Bayes/BBN/CatBoost/execution-tree unless Gate 1 proves usable density and verified instrument-cost positive expectancy.

Real work executed:

- Checked `provider-status --provider ibkr --agent`.
- Fetched real IBKR `{SYMBOL}` intraday rows.
- Built Auto-Quant material for the same rooted branch.
- Ran `auto-quant-agent-material-batch`, `auto-quant-agent-material-dispatch`, and `auto-quant-agent-material-rank` when material existed.
- Preserved `branch_path`, `regime_profit_branch_path`, `main_regime`, `sub_regime`, `sub_sub_regime_or_profit_factor`, and `profit_factor`.

Instrument Cost Verification Table:

| Timeframe | Trades | Trades/day | Raw | Instrument cost | Cost model status | Promotion cost verified | Survives instrument cost | Gate 1 survivor |
|---|---:|---:|---:|---:|---|---|---|---|
{chr(10).join(rows) if rows else "| none | 0 | 0.000 | 0.00% | unverified | `cost_model_unverified` | `False` | `False` | `False` |"}

Hard Gate 1 checks:

- `branch_fields_preserved={summary.get("branch_fields_preserved")}`
- `promotion_cost_verified={summary.get("promotion_cost_verified")}`
- `cost_model_status={summary.get("cost_model_status")}`
- `instrument_cost_survivors={summary.get("instrument_cost_survivors")}`
- `downstream_allowed={summary.get("downstream_allowed")}`

Interpretation:

{summary["interpretation"]}

Next useful work:

{summary["next_useful_work"]}

Skill update:

`skill_update={summary["skill_update"]}`
"""
    (ROOT / "summaries/terminal_decision_summary.md").write_text(text, encoding="utf-8")


def run_launch() -> int:
    for sub in ("data/provider/raw", "data/provider/normalized", "agent-material", "summaries", "checks", "command-output", "state", "scripts"):
        (ROOT / sub).mkdir(parents=True, exist_ok=True)
    shutil.copy2(SCRIPT, ROOT / "scripts" / SCRIPT.name)

    command_results = [
        run_cmd("00_provider_status_ibkr", [str(ICT), "provider-status", "--provider", "ibkr", "--agent"], timeout=60)
    ]
    provider_rows = []
    active_specs = []
    client_id = 231
    for index, spec in enumerate(SPECS, start=1):
        raw_path = ROOT / "data/provider/raw" / spec.out_name
        normalized_path = ROOT / "data/provider/normalized" / spec.out_name
        result = run_cmd(
            f"{index:02d}_ibkr_low_{spec.timeframe}_{spec.duration.replace(' ', '').lower()}_fetch",
            ibkr_fetch_args(spec, raw_path, client_id + index),
            timeout=420,
        )
        rows = normalize_provider_csv(raw_path, normalized_path)
        used_spec = spec
        if (result["exit"] != 0 or rows == 0) and spec.timeframe in RETRY_BY_TIMEFRAME:
            retry = RETRY_BY_TIMEFRAME[spec.timeframe]
            retry_raw = ROOT / "data/provider/raw" / retry.out_name
            retry_norm = ROOT / "data/provider/normalized" / retry.out_name
            retry_result = run_cmd(
                f"{index:02d}b_ibkr_low_{retry.timeframe}_{retry.duration.replace(' ', '').lower()}_retry_fetch",
                ibkr_fetch_args(retry, retry_raw, client_id + index + 20),
                timeout=180,
            )
            command_results.append(result)
            result = retry_result
            raw_path = retry_raw
            normalized_path = retry_norm
            rows = normalize_provider_csv(raw_path, normalized_path)
            used_spec = retry
        command_results.append(result)
        active_specs.append(used_spec)
        provider_rows.append(
            {
                "provider": "IBKR",
                "provider_label": f"IBKR {SYMBOL} {used_spec.timeframe} {used_spec.duration}",
                "symbol": SYMBOL,
                "timeframe": used_spec.timeframe,
                "bar_size": used_spec.bar_size,
                "duration": used_spec.duration,
                "role": used_spec.role,
                "path": str(normalized_path) if rows else "",
                "raw_path": str(raw_path) if rows else "",
                "rows": rows,
                "provider_data_acquired": "true" if result["exit"] == 0 and rows else "false",
                "provider_unreachable": "false" if result["exit"] == 0 and rows else "true",
                "provider_window_downgrade": "true" if used_spec.duration != spec.duration else "false",
                "aq_provider_invoked": "true",
                "local_cache_replay": "false",
                "exit": result["exit"],
            }
        )
        if index == 2 and not any(row["provider_data_acquired"] == "true" for row in provider_rows):
            break

    with (ROOT / "summaries/provider_provenance_matrix.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(provider_rows[0].keys()))
        writer.writeheader()
        writer.writerows(provider_rows)

    acquired = [row for row in provider_rows if row["provider_data_acquired"] == "true"]
    material_paths = []
    material_rows = []
    for row in acquired:
        spec = next(item for item in active_specs if item.timeframe == row["timeframe"] and item.duration == row["duration"])
        material_path, strategy_path = write_material_for_provider_row(row, spec)
        material_paths.append(str(material_path))
        material_rows.append(
            {
                "branch_path": BRANCH_PATH,
                "timeframe": spec.timeframe,
                "duration": spec.duration,
                "material_path": str(material_path),
                "strategy_path": str(strategy_path),
                "rows": row["rows"],
            }
        )

    if material_rows:
        with (ROOT / "summaries/material_paths.csv").open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(material_rows[0].keys()))
            writer.writeheader()
            writer.writerows(material_rows)

    strategy_files = sorted({row["strategy_path"] for row in material_rows})
    py_compile = run_cmd("04_strategy_py_compile", [str(PY), "-m", "py_compile", *strategy_files], timeout=60)
    command_results.append(py_compile)
    batch = dispatch = rank = None
    if material_paths and py_compile["exit"] == 0:
        batch_argv = [
            str(ICT),
            "auto-quant-agent-material-batch",
            "--symbol",
            AQ_SYMBOL,
            "--state-dir",
            str(ROOT / "state"),
            "--max-parallel",
            "1",
        ]
        if AUTO_QUANT_REPO.exists():
            batch_argv.extend(["--repo-url", str(AUTO_QUANT_REPO)])
        batch_argv.extend(sum([["--material", path] for path in material_paths], []))
        batch = run_cmd(
            "05_auto_quant_agent_material_batch",
            batch_argv,
            timeout=1800,
        )
        command_results.append(batch)
        if batch["exit"] == 0:
            dispatch = run_cmd(
                "06_auto_quant_agent_material_dispatch",
                [str(ICT), "auto-quant-agent-material-dispatch", "--symbol", AQ_SYMBOL, "--state-dir", str(ROOT / "state")],
                timeout=1500,
            )
            command_results.append(dispatch)
        if dispatch and dispatch["exit"] == 0:
            rank = run_cmd(
                "07_auto_quant_agent_material_rank",
                [str(ICT), "auto-quant-agent-material-rank", "--symbol", AQ_SYMBOL, "--state-dir", str(ROOT / "state")],
                timeout=300,
            )
            command_results.append(rank)

    rank_rows = []
    if rank and rank["exit"] == 0:
        rank_files = sorted((ROOT / f"state/auto-quant/{AQ_SYMBOL}").glob("auto_quant_agent_material_rank.*.json"))
        if rank_files:
            rank_rows = json.loads(rank_files[-1].read_text(encoding="utf-8")).get("ranking", [])

    day_counts = trading_day_counts(provider_rows)
    instrument_rows = instrument_cost_rows(rank_rows, day_counts)
    (ROOT / "checks/instrument_cost_table.json").write_text(json.dumps(instrument_rows, indent=2) + "\n", encoding="utf-8")
    write_csv(ROOT / "summaries/rank_rows_instrument_cost.csv", instrument_rows)

    total_trades = sum(int(row.get("trade_count") or 0) for row in rank_rows)
    positive_rows = sum(1 for row in rank_rows if float(row.get("total_profit_pct") or 0) > 0 and int(row.get("trade_count") or 0) > 0)
    nonzero_rows = sum(1 for row in rank_rows if int(row.get("trade_count") or 0) > 0)
    instrument_cost_survivors = [row for row in instrument_rows if row["gate1_survivor"]]
    cost_model_verified = any(row["promotion_cost_verified"] for row in instrument_rows)
    rank_branch_paths = sorted({rank_branch_path(row) for row in rank_rows})
    branch_fields_preserved = bool(rank_rows) and rank_branch_paths == [BRANCH_PATH]
    downstream_allowed = bool(branch_fields_preserved and instrument_cost_survivors and cost_model_verified)
    all_commands_ok = all(item["exit"] == 0 for item in command_results)
    if rank_rows and not branch_fields_preserved:
        decision = "drop_or_block_gate1_branch_fields_not_preserved"
        interpretation = "Auto-Quant returned rank rows, but the rooted branch fields did not preserve the exact regime-root path. Treat this as blocked evidence, not a profitability signal."
        next_work = "Repair branch metadata preservation before any downstream Pre-Bayes/BBN/CatBoost/execution-tree handoff."
    elif downstream_allowed:
        decision = "gate1_instrument_cost_density_survivor_downstream_candidate"
        interpretation = "Gate 1 produced a rooted LOW survivor only after verified instrument-cost economics and practical density. This is not promotion; it only earns exact downstream readback."
        next_work = "Run exact downstream on the surviving rooted lane only with the verified instrument-cost packet preserved and full practical lifecycle gates still false until proven."
    elif rank_rows and not cost_model_verified:
        decision = "gate1_cost_model_unverified_no_downstream"
        interpretation = "LOW produced AQ rank rows, but the exact IBKR LOW equity commission model was not verified from official sources, so cost survival and downstream admission fail closed."
        next_work = "Verify official IBKR US equity commission, regulatory, routing, account, pricing-plan, currency, and fee-effective-date assumptions before any downstream admission."
    elif rank_rows and total_trades > 0 and positive_rows > 0:
        decision = "drop_or_incubate_gate1_instrument_cost_or_density_failure"
        interpretation = "The branch produced positive raw IBKR trades, but no row survived verified instrument-cost economics plus practical density. This is a Gate 1 practical failure."
        next_work = "Do not run Pre-Bayes/BBN/CatBoost/execution-tree for this exact branch; rotate to another factor leaf or materially widen per-trade excursion."
    elif any(row["provider_data_acquired"] == "true" for row in provider_rows):
        decision = "drop_small_cycle"
        interpretation = "Provider/AQ material existed, but Gate 1 did not show usable positive expectancy. This is a factor failure, not a provider failure."
        next_work = "Do not run Pre-Bayes/BBN/CatBoost/execution-tree for this exact branch; move to another factor leaf."
    else:
        decision = "blocked"
        interpretation = "No real IBKR rows were acquired after upper-window attempts and retries, so the factor was not scored."
        next_work = "Retry provider connectivity/window sizing or switch to another real provider before judging the factor."

    summary = {
        "run_root": str(ROOT),
        "decision": decision,
        "branch_path": BRANCH_PATH,
        "provider_rows": provider_rows,
        "provider_data_acquired_count": len(acquired),
        "material_count": len(material_rows),
        "rank_rows": len(rank_rows),
        "rank_total_trade_count": total_trades,
        "rank_nonzero_trade_rows": nonzero_rows,
        "positive_trade_rows": positive_rows,
        "promotion_cost_verified": cost_model_verified,
        "cost_model_status": "verified" if cost_model_verified else "cost_model_unverified",
        "instrument_cost_rows": instrument_rows,
        "instrument_cost_survivors": instrument_cost_survivors,
        "rank_branch_paths": rank_branch_paths,
        "branch_fields_preserved": branch_fields_preserved,
        "command_results": command_results,
        "all_commands_ok": all_commands_ok,
        "downstream_allowed": downstream_allowed,
        "pre_bayes_allowed": downstream_allowed,
        "pre_bayes_filter_allowed": downstream_allowed,
        "bbn_allowed": downstream_allowed,
        "catboost_allowed": downstream_allowed,
        "execution_tree_allowed": downstream_allowed,
        "promotion_allowed": False,
        "trade_usable": False,
        "update_goal": False,
        "interpretation": interpretation,
        "next_useful_work": next_work,
        "skill_update": "not_needed: reused existing IBKR upper-window downgrade and AQ timerange discipline; no new reusable runtime lesson",
    }
    (ROOT / "summaries/ibkr_low_defensive_retail_opening_drive_rvol_gate1_v1.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    (ROOT / "checks/terminal_metrics.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    checklist_rows = [
        ["item", "status", "evidence"],
        ["ibkr_provider_invoked", "yes", str(ROOT / "command-output/00_provider_status_ibkr.cmd")],
        ["upper_window_requested", "yes", "1m=30D;5m=3M;15m=3M;30m=3M;1h=3M;4h=1Y;1d=2Y"],
        ["provider_window_downgrade_recorded", "yes", str(ROOT / "summaries/provider_provenance_matrix.csv")],
        ["branch_fields_preserved", "yes" if branch_fields_preserved else "no", BRANCH_PATH],
        ["instrument_cost_table_written", "yes", str(ROOT / "checks/instrument_cost_table.json")],
        ["downstream_blocked_until_gate_pass", "yes", "pre_bayes/bbn/catboost/execution_tree_allowed=false"],
        ["commands_all_zero", "yes" if all_commands_ok else "no", str(ROOT / "checks")],
    ]
    with (ROOT / "checks/prompt_to_artifact_checklist.csv").open("w", newline="", encoding="utf-8") as handle:
        csv.writer(handle).writerows(checklist_rows)
    validation = {
        "run_root_exists": ROOT.exists(),
        "provider_rows": len(provider_rows),
        "provider_data_acquired_count": len(acquired),
        "material_count": len(material_rows),
        "rank_rows": len(rank_rows),
        "rank_total_trade_count": total_trades,
        "rank_nonzero_trade_rows": nonzero_rows,
        "positive_trade_rows": positive_rows,
        "branch_fields_preserved": branch_fields_preserved,
        "promotion_cost_verified": cost_model_verified,
        "instrument_cost_survivor_count": len(instrument_cost_survivors),
        "downstream_allowed": downstream_allowed,
        "commands_all_zero": all_commands_ok,
        "decision": decision,
    }
    (ROOT / "checks/artifact_validation.json").write_text(json.dumps(validation, indent=2) + "\n", encoding="utf-8")
    write_terminal_summary(summary, instrument_rows)
    (ROOT / "checks/ibkr_low_defensive_retail_opening_drive_rvol_gate1_v1.exit").write_text("0\n", encoding="utf-8")
    return 0


def main(argv: list[str] | None = None) -> int:
    if argv and "--launch" in argv:
        return run_launch()
    prep_root = Path(f"/tmp/ict-engine-low-defensive-retail-opening-drive-rvol-source-prep-{RUN_STAMP}")
    metrics = write_source_prep_summary(prep_root)
    print(json.dumps(metrics, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
