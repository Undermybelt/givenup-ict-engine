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
ROOT = BASE / "runs" / f"{RUN_STAMP}-codex-ibkr-crwd5m-trend-reclaim-retained-gate1-v1"
REPO = BASE.parents[3]
PY = Path("/Users/thrill3r/.venvs/ict-engine-provider-py313/bin/python")
if not PY.exists():
    PY = Path("python3")
ICT = REPO / ".local-artifacts/cargo-target/debug/ict-engine"
if not ICT.exists():
    ICT = REPO / "target/debug/ict-engine"
AUTO_QUANT_REPO = Path("/Users/thrill3r/Auto-Quant")
SOURCE = BASE / "runs/20260519T172058+0800-codex-ibkr-crwd-pda-mtf-soft-confirmation-5m-provider-parity-v1"

SYMBOL = "CRWD"
AQ_SYMBOL = "IBKR_CRWD5M_TREND_RECLAIM_RETAINED_GATE1_V1"
FACTOR_ID = "ibkr_crwd5m_retained_trend_reclaim_gate1_v1"
BRANCH_PATH = (
    "US_EQ -> single_stock -> CRWD -> 5m -> TrendExpansion -> TrendReclaim -> "
    "ibkr_crwd5m_retained_trend_reclaim_gate1_v1"
)
BRANCH_PARTS = [part.strip() for part in BRANCH_PATH.split(" -> ")]


@dataclass(frozen=True)
class Spec:
    timeframe: str
    source_name: str
    role: str


SPECS = [
    Spec("5m", "ibkr_crwd_5m_3m.csv", "exact_trend_reclaim_root"),
    Spec("15m", "ibkr_crwd_15m_3m.csv", "small_cycle_sibling"),
    Spec("30m", "ibkr_crwd_30m_3m.csv", "neutralizer"),
    Spec("1h", "ibkr_crwd_1h_3m.csv", "higher_timeframe_veto"),
    Spec("1d", "ibkr_crwd_1d_2y.csv", "daily_context"),
]


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


def strategy_class_name(spec: Spec) -> str:
    return f"IbkrCrwdTrendReclaimRetained{suffix(spec.timeframe)}"


def package_id_for_spec(spec: Spec) -> str:
    return f"ibkr-crwd5m-trend-reclaim-retained-{spec.timeframe}-v1"


def strategy_source(spec: Spec, class_name: str) -> str:
    tag = f"{FACTOR_ID}_{spec.timeframe}"
    return f'''from freqtrade.strategy import IStrategy
from pandas import DataFrame
import talib.abstract as ta


class {class_name}(IStrategy):
    INTERFACE_VERSION = 3
    timeframe = "{spec.timeframe}"
    can_short = False
    minimal_roi = {{"0": 0.0062}}
    stoploss = -0.0105
    trailing_stop = True
    trailing_stop_positive = 0.0018
    trailing_stop_positive_offset = 0.0064
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
    for candidate in ("15m", "30m", "5m", "1h", "1d"):
        if f"-{candidate}-" in package_id:
            return candidate
    return "unknown"


def trading_days(path: Path) -> int:
    days: set[str] = set()
    if not path.exists():
        return 0
    with path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            raw = (row.get("timestamp") or "").strip()
            if raw:
                days.add(raw[:10])
    return len(days)


def write_material_for_spec(spec: Spec, normalized_path: Path) -> Path:
    class_name = strategy_class_name(spec)
    strategy_path = ROOT / "agent-material" / f"{class_name}.py"
    strategy_path.write_text(strategy_source(spec, class_name), encoding="utf-8")
    package_id = package_id_for_spec(spec)
    material_path = ROOT / "agent-material" / f"{package_id}.material.json"
    material = {
        "package_id": package_id,
        "title": f"IBKR CRWD retained trend-reclaim re-root Gate 1 - {spec.timeframe}",
        "symbol": SYMBOL,
        "timeframe": spec.timeframe,
        "timerange": timerange(normalized_path),
        "direction": "long",
        "data_path": str(normalized_path),
        "strategy_source_path": str(strategy_path),
        "strategy_class_name": class_name,
        "strategy_brief": "Retained-cache IBKR CRWD trend-reclaim re-root from directionality diagnostic; not fresh-provider parity.",
        "evaluation_priority": ["instrument_cost_verification", "trade_density", "same_root_preservation", "local_cache_replay"],
        "consumer_evidence_profile": {
            "branch_path": BRANCH_PATH,
            "regime_profit_branch_path": BRANCH_PATH,
            "branch_id": FACTOR_ID,
            "main_regime": BRANCH_PARTS[4],
            "sub_regime": BRANCH_PARTS[5],
            "sub_sub_regime_or_profit_factor": BRANCH_PARTS[6],
            "profit_factor": BRANCH_PARTS[6],
            "market": "US_EQUITY",
            "product": "single_stock",
            "symbol_root": SYMBOL,
            "base_timeframe": "5m",
            "training_timeframe": spec.timeframe,
            "context_timeframes": "5m/15m/30m/1h/1d",
            "provider": "IBKR",
            "provider_provenance": "retained IBKR provider rows from 20260519 provider-parity run",
            "local_cache_replay": True,
            "gate_id": "Gate1IbkrCrwd5mTrendReclaimRetainedV1",
            "cost_model_status": "cost_model_unverified",
            "promotion_cost_verified": False,
            "cost_model": unverified_equity_cost_model(spec.timeframe),
            "promotion_allowed": False,
            "trade_usable": False,
            "update_goal": False,
        },
        "notes": [
            "re_rooted_from_directionality_probe=true",
            "fresh_provider_parity=false",
            "local_cache_replay=true",
            f"branch_path={BRANCH_PATH}",
            "equity_cost_model=unverified_fail_closed",
            "downstream_allowed=false_until_verified_instrument_cost_gate_passes",
        ],
    }
    material_path.write_text(json.dumps(material, indent=2) + "\n", encoding="utf-8")
    return material_path


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
                "trading_days": days,
                "trades_per_day": trades_per_day,
                "win_rate_pct": safe_float(item.get("win_rate_pct")),
                "raw_total_profit_pct": raw,
                "instrument_cost_total_profit_pct": None,
                "instrument_cost_profit_factor": None,
                "sharpe": safe_float(item.get("sharpe")),
                "cost_model_status": "cost_model_unverified",
                "cost_model_blocker": "official_equity_cost_model_not_verified",
                "cost_model": unverified_equity_cost_model(timeframe),
                "promotion_cost_verified": False,
                "survives_instrument_cost": False,
                "minimum_trade_sample_floor_met": trades > 0,
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


def write_terminal_summary(metrics: dict, instrument_rows: list[dict]) -> None:
    table_rows = []
    for row in instrument_rows:
        table_rows.append(
            "| `{}` | {} | {:.3f} | {:.2f}% | {} | `{}` | `{}` | `{}` | `{}` |".format(
                row["timeframe"],
                row["trade_count"],
                row["trades_per_day"],
                row["raw_total_profit_pct"],
                format_optional_pct(row["instrument_cost_total_profit_pct"]),
                row["cost_model_status"],
                row["promotion_cost_verified"],
                row["survives_instrument_cost"],
                row["gate1_survivor"],
            )
        )
    summary_text = f"""# IBKR CRWD 5m Trend-Reclaim Retained Gate 1

Decision: `{metrics["decision"]}`

Branch path:

```text
{BRANCH_PATH}
```

Provider rule: retained IBKR cache replay only. This does not claim fresh-provider parity.

Instrument Cost Verification Table:

| Timeframe | Trades | Trades/day | Raw profit | Instrument cost | Cost model status | Promotion cost verified | Survives instrument cost | Gate 1 survivor |
|---|---:|---:|---:|---:|---|---|---|---|
{chr(10).join(table_rows) if table_rows else "| none | 0 | 0.000 | 0.00% | unverified | `cost_model_unverified` | `False` | `False` | `False` |"}

Interpretation:

{metrics["interpretation"]}

Next:

{metrics["next_useful_work"]}

Downstream allowed: `{str(metrics.get("downstream_allowed", False)).lower()}`
Promotion allowed: `false`
Trade usable: `false`
Update goal: `false`
"""
    (ROOT / "summaries/terminal_decision_summary.md").write_text(summary_text, encoding="utf-8")


def main() -> int:
    for sub in ("data/provider/normalized", "agent-material", "summaries", "checks", "command-output", "state", "scripts"):
        (ROOT / sub).mkdir(parents=True, exist_ok=True)
    shutil.copy2(SCRIPT, ROOT / "scripts" / SCRIPT.name)

    provider_rows = []
    material_paths = []
    strategy_files = []
    day_counts: dict[str, int] = {}
    for spec in SPECS:
        data_path, rows = copy_rows(spec)
        days = trading_days(data_path) if rows else 0
        if rows:
            day_counts[spec.timeframe] = days
        provider_rows.append({
            "provider": "IBKR",
            "provider_label": f"retained IBKR CRWD {spec.timeframe}",
            "symbol": SYMBOL,
            "timeframe": spec.timeframe,
            "role": spec.role,
            "path": str(data_path) if rows else "",
            "rows": rows,
            "trading_days": days,
            "provider_data_acquired": "true" if rows else "false",
            "provider_unreachable": "false",
            "local_cache_replay": "true",
            "source_run_root": str(SOURCE),
        })
        if not rows:
            continue
        class_name = strategy_class_name(spec)
        strategy_path = ROOT / "agent-material" / f"{class_name}.py"
        strategy_files.append(str(strategy_path))
        material_path = write_material_for_spec(spec, data_path)
        material_paths.append(str(material_path))

    with (ROOT / "summaries/provider_provenance_matrix.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(provider_rows[0].keys()))
        writer.writeheader()
        writer.writerows(provider_rows)

    command_results = []
    compile_result = run_cmd("00_strategy_py_compile", [str(PY), "-m", "py_compile", *strategy_files], timeout=60)
    command_results.append(compile_result)
    if material_paths and compile_result["exit"] == 0:
        batch_argv = [str(ICT), "auto-quant-agent-material-batch", "--symbol", AQ_SYMBOL, "--state-dir", str(ROOT / "state"), "--max-parallel", "1"]
        if AUTO_QUANT_REPO.exists():
            batch_argv.extend(["--repo-url", str(AUTO_QUANT_REPO)])
        for path in material_paths:
            batch_argv.extend(["--material", path])
        command_results.append(run_cmd("01_auto_quant_agent_material_batch", batch_argv, timeout=1800))
    if len(command_results) >= 2 and command_results[-1]["exit"] == 0:
        command_results.append(run_cmd("02_auto_quant_agent_material_dispatch", [str(ICT), "auto-quant-agent-material-dispatch", "--symbol", AQ_SYMBOL, "--state-dir", str(ROOT / "state")], timeout=1500))
    if len(command_results) >= 3 and command_results[-1]["exit"] == 0:
        command_results.append(run_cmd("03_auto_quant_agent_material_rank", [str(ICT), "auto-quant-agent-material-rank", "--symbol", AQ_SYMBOL, "--state-dir", str(ROOT / "state")], timeout=300))

    rank_rows: list[dict] = []
    rank_root = ROOT / f"state/auto-quant/{AQ_SYMBOL}"
    rank_files = sorted(rank_root.glob("auto_quant_agent_material_rank.*.json"))
    if rank_files:
        rank_rows = json.loads(rank_files[-1].read_text(encoding="utf-8")).get("ranking", [])
    cost_rows = instrument_cost_rows(rank_rows, day_counts)
    branch_fields_preserved = bool(rank_rows) and all(
        (row.get("branch_path") or row.get("consumer_evidence_profile", {}).get("branch_path")) == BRANCH_PATH
        for row in rank_rows
    )
    instrument_cost_survivors = [row for row in cost_rows if row["gate1_survivor"]]
    cost_model_verified = any(row["promotion_cost_verified"] for row in cost_rows)
    downstream_allowed = bool(branch_fields_preserved and instrument_cost_survivors and cost_model_verified)
    if downstream_allowed:
        decision = "retained_trend_reclaim_gate1_instrument_cost_survivor_downstream_allowed"
        interpretation = "CRWD retained-cache rows have a verified instrument-cost survivor with rooted branch fields preserved. Promotion still remains false until the full practical lifecycle passes."
        next_work = "Run same-root downstream only after preserving the verified instrument-cost packet."
    elif rank_rows and not cost_model_verified:
        decision = "gate1_cost_model_unverified_no_downstream"
        interpretation = "CRWD produced AQ rank rows, but the exact IBKR US equity commission model was not verified from official sources, so cost survival and downstream admission fail closed."
        next_work = "Verify official IBKR US equity commission, regulatory, routing, account, pricing-plan, currency, and fee-effective-date assumptions before any downstream admission."
    elif rank_rows:
        decision = "retained_trend_reclaim_gate1_instrument_cost_or_branch_fields_failed"
        interpretation = "CRWD produced AQ rank rows, but no row survived verified instrument-cost economics with rooted branch fields preserved. Stop before downstream."
        next_work = "Preserve as observation and rotate or verify the exact instrument-cost packet before any admission."
    else:
        decision = "retained_trend_reclaim_aq_rank_blocked"
        interpretation = "Provider/material/AQ did not produce rank rows, so this is not a factor verdict. Inspect command-output and retry only the failed infrastructure leg."
        next_work = "Classify blocker from command exits; do not promote or call the factor negative without AQ rank evidence."

    summary = {
        "run_root": str(ROOT),
        "decision": decision,
        "branch_path": BRANCH_PATH,
        "provider_rows": provider_rows,
        "local_cache_replay": True,
        "fresh_provider_parity": False,
        "material_count": len(material_paths),
        "rank_rows": len(rank_rows),
        "rank_total_trade_count": sum(int(row.get("trade_count") or 0) for row in rank_rows),
        "promotion_cost_verified": cost_model_verified,
        "cost_model_status": "verified" if cost_model_verified else "cost_model_unverified",
        "instrument_cost_rows": cost_rows,
        "survivors_instrument_cost": instrument_cost_survivors,
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
    (ROOT / "checks/instrument_cost_table.json").write_text(json.dumps(cost_rows, indent=2) + "\n", encoding="utf-8")
    write_csv(ROOT / "summaries/rank_rows_instrument_cost.csv", cost_rows)
    write_terminal_summary(summary, cost_rows)
    print(str(ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
