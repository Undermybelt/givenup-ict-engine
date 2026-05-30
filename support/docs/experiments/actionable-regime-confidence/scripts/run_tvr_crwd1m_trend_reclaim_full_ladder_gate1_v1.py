#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import shutil
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


SCRIPT = Path(__file__).resolve()
BASE = Path("/Users/thrill3r/projects-ict-engine/ict-engine/support/docs/experiments/actionable-regime-confidence")
RUN_STAMP = datetime.now(ZoneInfo("Asia/Shanghai")).strftime("%Y%m%dT%H%M%S+0800")
ROOT = BASE / "runs" / f"{RUN_STAMP}-codex-tvr-crwd1m-trend-reclaim-full-ladder-gate1-v1"
REPO = BASE.parents[3]
PY = Path("/Users/thrill3r/.venvs/ict-engine-provider-py313/bin/python")
if not PY.exists():
    PY = Path("python3")
ICT = REPO / ".local-artifacts/cargo-target/debug/ict-engine"
if not ICT.exists():
    ICT = REPO / "target/debug/ict-engine"
AUTO_QUANT_REPO = Path("/Users/thrill3r/Auto-Quant")
SOURCE = BASE / "runs/20260519T143455+0800-hermes-tvr-crwd-pda-mtf-soft-confirmation-1m-full-ladder-v1"

SYMBOL = "CRWD"
AQ_SYMBOL = "TVR_CRWD1M_TREND_RECLAIM_FULL_LADDER_GATE1_V1"
FACTOR_ID = "tvr_crwd1m_trend_reclaim_full_ladder_v1"
PACKAGE_PREFIX = "tvr-crwd1m-trend-reclaim-full-ladder"
TITLE_PREFIX = "TVR CRWD 1m trend-reclaim full-ladder Gate 1"
EXACT_TIMEFRAME = "1m"
EXACT_MIN_TRADES = 10
BRANCH_PATH = (
    "US_EQ -> single_stock -> CRWD -> 1m -> TrendExpansion -> TrendReclaim -> "
    "tvr_crwd1m_trend_reclaim_full_ladder_v1"
)
BRANCH_PARTS = [part.strip() for part in BRANCH_PATH.split(" -> ")]


@dataclass(frozen=True)
class Spec:
    timeframe: str
    source_name: str
    role: str


SPECS = [
    Spec("1m", "tvr_crwd_1m.csv", "exact_trend_reclaim_root"),
    Spec("5m", "tvr_crwd_5m.csv", "small_cycle_sibling"),
    Spec("15m", "tvr_crwd_15m.csv", "small_cycle_sibling"),
    Spec("30m", "tvr_crwd_30m.csv", "neutralizer"),
    Spec("1h", "tvr_crwd_1h.csv", "higher_timeframe_veto"),
    Spec("4h", "tvr_crwd_4h.csv", "higher_timeframe_veto"),
    Spec("1d", "tvr_crwd_1d.csv", "daily_context"),
]


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


def copy_rows(spec: Spec) -> tuple[Path, int]:
    source = SOURCE / "data/provider/normalized" / spec.source_name
    destination = ROOT / "data/provider/normalized" / spec.source_name
    destination.parent.mkdir(parents=True, exist_ok=True)
    if not source.exists():
        return destination, 0
    shutil.copy2(source, destination)
    with destination.open(newline="", encoding="utf-8") as handle:
        return destination, max(sum(1 for _ in csv.DictReader(handle)), 0)


def timerange(path: Path) -> str:
    dates: list[str] = []
    with path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            raw = (row.get("timestamp") or "").strip()
            if raw:
                dates.append(raw[:10].replace("-", ""))
    return f"{min(dates)}-{max(dates)}" if dates else ""


def suffix(tf: str) -> str:
    return tf.replace("m", "Min").replace("h", "Hour").replace("d", "Day")


def strategy_source(spec: Spec, class_name: str) -> str:
    tag = f"{FACTOR_ID}_{spec.timeframe}"
    return f'''from freqtrade.strategy import IStrategy
from pandas import DataFrame
import talib.abstract as ta


class {class_name}(IStrategy):
    INTERFACE_VERSION = 3
    timeframe = "{spec.timeframe}"
    can_short = False
    minimal_roi = {{"0": 0.0060}}
    stoploss = -0.0108
    trailing_stop = True
    trailing_stop_positive = 0.0018
    trailing_stop_positive_offset = 0.0062
    trailing_only_offset_is_reached = True
    process_only_new_candles = True
    use_exit_signal = True
    startup_candle_count = 170

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["ema8"] = ta.EMA(dataframe, timeperiod=8)
        dataframe["ema13"] = ta.EMA(dataframe, timeperiod=13)
        dataframe["ema21"] = ta.EMA(dataframe, timeperiod=21)
        dataframe["ema55"] = ta.EMA(dataframe, timeperiod=55)
        dataframe["rsi7"] = ta.RSI(dataframe, timeperiod=7)
        dataframe["rsi14"] = ta.RSI(dataframe, timeperiod=14)
        dataframe["adx14"] = ta.ADX(dataframe, timeperiod=14)
        dataframe["atr14"] = ta.ATR(dataframe, timeperiod=14)
        dataframe["vol20"] = dataframe["volume"].rolling(20).mean()
        dataframe["vol60"] = dataframe["volume"].rolling(60).mean()
        dataframe["ret3"] = dataframe["close"].pct_change(3)
        dataframe["ret12"] = dataframe["close"].pct_change(12)
        dataframe["ret36"] = dataframe["close"].pct_change(36)
        typical = (dataframe["high"] + dataframe["low"] + dataframe["close"]) / 3.0
        dt = dataframe["date"]
        day_key = dt.dt.strftime("%Y-%m-%d")
        minute = dt.dt.hour * 60 + dt.dt.minute
        regular = (minute >= 13 * 60 + 30) & (minute < 20 * 60)
        cumulative_volume = dataframe["volume"].where(regular).groupby(day_key).cumsum()
        cumulative_pv = (typical * dataframe["volume"]).where(regular).groupby(day_key).cumsum()
        dataframe["vwap"] = cumulative_pv / cumulative_volume
        dataframe["entry_window"] = (minute >= 14 * 60) & (minute < 19 * 60 + 15)
        dataframe["force_exit_window"] = minute >= 19 * 60 + 50
        dataframe["rvol20"] = dataframe["volume"] / dataframe["vol20"]
        dataframe["rvol60"] = dataframe["volume"] / dataframe["vol60"]
        dataframe["range_pct"] = (dataframe["high"] - dataframe["low"]) / dataframe["close"]
        dataframe["vwap_dist_atr"] = (dataframe["close"] - dataframe["vwap"]) / dataframe["atr14"]
        dataframe["ema8_slope_atr"] = (dataframe["ema8"] - dataframe["ema8"].shift(5)) / dataframe["atr14"]
        dataframe["ema21_slope_atr"] = (dataframe["ema21"] - dataframe["ema21"].shift(8)) / dataframe["atr14"]
        dataframe["range_high_36"] = dataframe["high"].rolling(36).max()
        dataframe["range_low_36"] = dataframe["low"].rolling(36).min()
        dataframe["range_pos_36"] = (dataframe["close"] - dataframe["range_low_36"]) / dataframe["range_high_36"].sub(dataframe["range_low_36"]).replace(0, 1)
        dataframe["close_pos"] = (dataframe["close"] - dataframe["low"]) / dataframe["high"].sub(dataframe["low"]).replace(0, 1)
        dataframe["upper_wick_pct"] = (dataframe["high"] - dataframe[["open", "close"]].max(axis=1)) / dataframe["close"]
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["enter_long"] = 0
        dataframe["enter_tag"] = ""
        trend_reclaim = (
            (dataframe["close"] > dataframe["vwap"] - dataframe["atr14"] * 0.08)
            & (dataframe["close"] > dataframe["ema13"] * 0.997)
            & (dataframe["ema8"] > dataframe["ema21"] * 0.996)
            & dataframe["ema8_slope_atr"].gt(-0.05)
            & dataframe["ema21_slope_atr"].gt(-0.10)
            & dataframe["ret12"].gt(-0.006)
            & dataframe["ret36"].gt(-0.012)
            & dataframe["range_pos_36"].between(0.45, 0.93)
        )
        participation = (
            dataframe["rvol20"].between(0.42, 4.8)
            & dataframe["rvol60"].between(0.40, 4.4)
            & dataframe["adx14"].between(9, 46)
            & dataframe["rsi7"].between(38, 83)
            & dataframe["rsi14"].between(42, 76)
        )
        not_exhausted = (
            dataframe["vwap_dist_atr"].between(-0.18, 1.20)
            & dataframe["upper_wick_pct"].lt(0.010)
            & dataframe["range_pct"].between(0.00010, 0.012)
            & dataframe["ret3"].lt(0.014)
            & dataframe["close_pos"].between(0.42, 0.98)
        )
        signal = dataframe["entry_window"] & trend_reclaim & participation & not_exhausted
        dataframe.loc[signal, ["enter_long", "enter_tag"]] = (1, "{tag}")
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["exit_long"] = 0
        lost_reclaim = dataframe["close"] < dataframe["vwap"] - dataframe["atr14"] * 0.32
        trend_break = dataframe["close"] < dataframe["ema21"] - dataframe["atr14"] * 0.24
        stretched = dataframe["vwap_dist_atr"] > 1.55
        dataframe.loc[dataframe["force_exit_window"] | lost_reclaim | trend_break | stretched, "exit_long"] = 1
        return dataframe
'''


def safe_float(value: object) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def rank_timeframe(item: dict) -> str:
    value = item.get("timeframe")
    if value:
        return str(value)
    package_id = str(item.get("package_id") or "")
    for candidate in ("15m", "30m", "1m", "5m", "1h", "4h", "1d"):
        if f"-{candidate}-" in package_id:
            return candidate
    return "unknown"


def unverified_equity_cost_model(timeframe: str) -> dict:
    return {
        "status": "cost_model_unverified",
        "instrument_class": "US_EQUITY",
        "symbol": SYMBOL,
        "broker": "IBKR_or_TVR_execution_route_unverified",
        "venue_routing": "unverified",
        "currency": "USD",
        "timeframe": timeframe,
        "pricing_plan": "unverified",
        "account_region": "unverified",
        "unit_convention": "per_share_commission_plus_regulatory_fees",
        "fee_effective_date": "unverified",
        "official_sources": [],
        "blocker": "official_equity_cost_model_not_verified_for_product_route_account_plan_date",
    }


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
        trades = int(item.get("trade_count") or 0)
        raw = safe_float(item.get("total_profit_pct"))
        timeframe = rank_timeframe(item)
        days = max(1, day_counts.get(timeframe, 1))
        trades_per_day = trades / days
        rows.append(
            {
                "package_id": item.get("package_id") or "",
                "timeframe": timeframe,
                "trade_count": trades,
                "min_gate1_trade_count": EXACT_MIN_TRADES,
                "minimum_trade_sample_floor_met": trades >= EXACT_MIN_TRADES,
                "trading_days": days,
                "trades_per_day": trades_per_day,
                "density_target_1_to_3_per_day": 1.0 <= trades_per_day <= 3.0,
                "win_rate_pct": safe_float(item.get("win_rate_pct")),
                "raw_total_profit_pct": raw,
                "instrument_cost_total_profit_pct": None,
                "instrument_cost_profit_factor": None,
                "sharpe": safe_float(item.get("sharpe")),
                "branch_path": item.get("branch_path") or item.get("consumer_evidence_profile", {}).get("branch_path") or "",
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


def write_terminal_summary(summary: dict, instrument_rows: list[dict]) -> None:
    rows = []
    for row in instrument_rows:
        rows.append(
            "| `{}` | {} | {:.3f} | {:.2f}% | {} | `{}` | `{}` | `{}` |".format(
                row["timeframe"],
                row["trade_count"],
                safe_float(row.get("trades_per_day")),
                safe_float(row.get("raw_total_profit_pct")),
                format_optional_pct(row.get("instrument_cost_total_profit_pct")),
                row.get("cost_model_status") or "unknown",
                row.get("promotion_cost_verified"),
                row.get("gate1_survivor"),
            )
        )

    text = f"""# {TITLE_PREFIX}

Decision: `{summary["decision"]}`

Branch path:

```text
{BRANCH_PATH}
```

Provider rule: retained/corrected TradingViewRemix CRWD rows only. This does not claim fresh-provider parity.

Instrument Cost Verification Table:

| Timeframe | Trades | Trades/day | Raw | Instrument cost | Cost model status | Promotion cost verified | Gate 1 survivor |
|---|---:|---:|---:|---:|---|---|---|
{chr(10).join(rows) if rows else "| none | 0 | 0.000 | 0.00% | unverified | `cost_model_unverified` | `False` | `False` |"}

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

Promotion allowed: `false`
Trade usable: `false`
Update goal: `false`
"""
    (ROOT / "summaries/terminal_decision_summary.md").write_text(text, encoding="utf-8")


def main() -> int:
    for sub in ("data/provider/normalized", "agent-material", "summaries", "checks", "command-output", "state", "scripts"):
        (ROOT / sub).mkdir(parents=True, exist_ok=True)
    shutil.copy2(SCRIPT, ROOT / "scripts" / SCRIPT.name)

    provider_rows = []
    material_paths = []
    strategy_files = []
    for spec in SPECS:
        data_path, rows = copy_rows(spec)
        provider_rows.append({
            "provider": "TradingViewRemix",
            "provider_label": f"retained TVR CRWD {spec.timeframe}",
            "symbol": SYMBOL,
            "timeframe": spec.timeframe,
            "role": spec.role,
            "path": str(data_path) if rows else "",
            "rows": rows,
            "provider_data_acquired": "true" if rows else "false",
            "provider_unreachable": "false",
            "local_cache_replay": "true",
            "source_run_root": str(SOURCE),
        })
        if not rows:
            continue
        class_name = f"TvrCrwdTrendReclaimFullLadder{suffix(spec.timeframe)}"
        strategy_path = ROOT / "agent-material" / f"{class_name}.py"
        strategy_path.write_text(strategy_source(spec, class_name), encoding="utf-8")
        strategy_files.append(str(strategy_path))
        package_id = f"{PACKAGE_PREFIX}-{spec.timeframe}-v1"
        material_path = ROOT / "agent-material" / f"{package_id}.material.json"
        material = {
            "package_id": package_id,
            "title": f"{TITLE_PREFIX} - {spec.timeframe}",
            "symbol": SYMBOL,
            "timeframe": spec.timeframe,
            "timerange": timerange(data_path),
            "direction": "long",
            "data_path": str(data_path),
            "strategy_source_path": str(strategy_path),
            "strategy_class_name": class_name,
            "strategy_brief": "TradingViewRemix CRWD trend-reclaim re-root from corrected CRWD ladder rows; exact branch starts at 1m.",
            "evaluation_priority": ["one_minute_origin", "instrument_cost_verification", "trade_density", "same_root_preservation", "mtf_context"],
            "consumer_evidence_profile": {
                "branch_path": BRANCH_PATH,
                "regime_profit_branch_path": BRANCH_PATH,
                "branch_id": FACTOR_ID,
                "main_regime": BRANCH_PARTS[4],
                "sub_regime": BRANCH_PARTS[5],
                "sub_sub_regime_or_profit_factor": BRANCH_PARTS[6],
                "profit_factor": BRANCH_PARTS[6],
                "base_timeframe": "1m",
                "training_timeframe": spec.timeframe,
                "context_timeframes": "1m/5m/15m/30m/1h/4h/1d",
                "provider": "TradingViewRemix",
                "provider_provenance": "retained TVR CRWD corrected rows from 20260519 full ladder run",
                "local_cache_replay": True,
                "fresh_provider_parity": False,
                "gate_id": "Gate1TvrCrwd1mTrendReclaimFullLadderV1",
                "cost_model_status": "cost_model_unverified",
                "promotion_cost_verified": False,
                "cost_model": unverified_equity_cost_model(spec.timeframe),
                "promotion_allowed": False,
                "trade_usable": False,
                "update_goal": False,
            },
            "notes": [
                "re_rooted_from_crwd_range_reversion_failure=true",
                "fresh_provider_parity=false",
                "local_cache_replay=true",
                f"branch_path={BRANCH_PATH}",
                f"downstream_allowed=false_until_exact_{EXACT_TIMEFRAME}_instrument_cost_density_survives",
                "equity_cost_model=unverified_fail_closed",
            ],
        }
        material_path.write_text(json.dumps(material, indent=2) + "\n", encoding="utf-8")
        material_paths.append(str(material_path))

    with (ROOT / "summaries/provider_provenance_matrix.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(provider_rows[0].keys()))
        writer.writeheader()
        writer.writerows(provider_rows)

    command_results = []
    command_results.append(run_cmd("00_strategy_py_compile", [str(PY), "-m", "py_compile", *strategy_files], timeout=60))
    if material_paths and command_results[-1]["exit"] == 0:
        batch_argv = [str(ICT), "auto-quant-agent-material-batch", "--symbol", AQ_SYMBOL, "--state-dir", str(ROOT / "state"), "--max-parallel", "1"]
        if AUTO_QUANT_REPO.exists():
            batch_argv.extend(["--repo-url", str(AUTO_QUANT_REPO)])
        for path in material_paths:
            batch_argv.extend(["--material", path])
        command_results.append(run_cmd("01_auto_quant_agent_material_batch", batch_argv, timeout=1800))
    if len(command_results) >= 2 and command_results[-1]["exit"] == 0:
        command_results.append(run_cmd("02_auto_quant_agent_material_dispatch", [str(ICT), "auto-quant-agent-material-dispatch", "--symbol", AQ_SYMBOL, "--state-dir", str(ROOT / "state")], timeout=1800))
    if len(command_results) >= 3 and command_results[-1]["exit"] == 0:
        command_results.append(run_cmd("03_auto_quant_agent_material_rank", [str(ICT), "auto-quant-agent-material-rank", "--symbol", AQ_SYMBOL, "--state-dir", str(ROOT / "state")], timeout=300))

    rank_rows: list[dict] = []
    rank_root = ROOT / f"state/auto-quant/{AQ_SYMBOL}"
    rank_files = sorted(rank_root.glob("auto_quant_agent_material_rank.*.json"))
    if rank_files:
        rank_rows = json.loads(rank_files[-1].read_text(encoding="utf-8")).get("ranking", [])
    day_counts = trading_day_counts(provider_rows)
    instrument_rows = instrument_cost_rows(rank_rows, day_counts)
    (ROOT / "checks/instrument_cost_table.json").write_text(json.dumps(instrument_rows, indent=2) + "\n", encoding="utf-8")
    write_csv(ROOT / "summaries/rank_rows_instrument_cost.csv", instrument_rows)

    exact_1m = [row for row in instrument_rows if row["timeframe"] == EXACT_TIMEFRAME]
    exact_1m_trades = sum(row["trade_count"] for row in exact_1m)
    instrument_cost_survivors = [row for row in instrument_rows if row["gate1_survivor"]]
    cost_model_verified = any(row["promotion_cost_verified"] for row in instrument_rows)
    branch_fields_preserved = bool(rank_rows) and all(
        (row.get("branch_path") or row.get("consumer_evidence_profile", {}).get("branch_path")) == BRANCH_PATH
        for row in rank_rows
    )
    downstream_allowed = bool(branch_fields_preserved and instrument_cost_survivors and cost_model_verified)
    if downstream_allowed:
        decision = "gate1_instrument_cost_density_survivor_downstream_candidate"
        interpretation = "CRWD exact root survived only after verified instrument-cost economics and branch fields were preserved. This is not promotion; it only allows exact downstream readback."
        next_work = "Run downstream only with the verified instrument-cost packet preserved and practical lifecycle gates still false until independently proven."
    elif rank_rows and not cost_model_verified:
        decision = "gate1_cost_model_unverified_no_downstream"
        interpretation = "CRWD produced AQ rank rows from retained TVR data, but the exact equity commission model was not verified from official sources, so cost survival and downstream admission fail closed."
        next_work = "Verify official CRWD equity commission, regulatory, routing, account, pricing-plan, currency, and fee-effective-date assumptions before downstream admission."
    elif rank_rows:
        decision = "drop_gate1_instrument_cost_or_density_failed"
        interpretation = "CRWD produced AQ rank rows, but no row survived both verified instrument-cost economics and practical density. Stop before downstream."
        next_work = "Preserve as observation and rotate to a materially different family or verify exact instrument costs before reconsidering."
    else:
        decision = "tvr_crwd1m_trend_reclaim_aq_rank_blocked"
        interpretation = "Provider/material/AQ did not produce rank rows, so this is not a factor verdict."
        next_work = "Classify the blocker from command exits before judging the factor."

    summary = {
        "run_root": str(ROOT),
        "decision": decision,
        "branch_path": BRANCH_PATH,
        "provider_rows": provider_rows,
        "local_cache_replay": True,
        "fresh_provider_parity": False,
        "material_count": len(material_paths),
        "rank_rows": len(rank_rows),
        "exact_1m_trades": exact_1m_trades,
        "promotion_cost_verified": cost_model_verified,
        "cost_model_status": "verified" if cost_model_verified else "cost_model_unverified",
        "instrument_cost_rows": instrument_rows,
        "instrument_cost_survivors": instrument_cost_survivors,
        "branch_fields_preserved": branch_fields_preserved,
        "command_results": command_results,
        "command_exits": {item["name"]: item["exit"] for item in command_results},
        "downstream_allowed": downstream_allowed,
        "promotion_allowed": False,
        "trade_usable": False,
        "update_goal": False,
        "interpretation": interpretation,
        "next_useful_work": next_work,
    }
    (ROOT / "checks/terminal_metrics.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    (ROOT / "checks/instrument_cost_gate.json").write_text(json.dumps({"rows": instrument_rows, "gate_pass": downstream_allowed}, indent=2) + "\n", encoding="utf-8")
    write_terminal_summary(summary, instrument_rows)
    print(str(ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
