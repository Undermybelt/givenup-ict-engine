#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import os
import shutil
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


REPO = Path("/Users/thrill3r/projects-ict-engine/ict-engine")
BASE = REPO / "support/docs/experiments/actionable-regime-confidence"
STAMP = datetime.now(ZoneInfo("Asia/Shanghai")).strftime("%Y%m%dT%H%M%S+0800")
RUN_ID = "codex-ibkr-cvx-psar-adx-trend-aq-gate1-v1"
ROOT = BASE / "runs" / f"{STAMP}-{RUN_ID}"
ICT = REPO / ".local-artifacts/cargo-target/debug/ict-engine"
if not ICT.exists():
    ICT = REPO / "target/debug/ict-engine"
PY = Path("/Users/thrill3r/.venvs/ict-engine-provider-py313/bin/python")
if not PY.exists():
    PY = Path("python3")
FETCH = REPO / "support/scripts/auto_quant_external/fetch_external.py"
AQ_REPO = Path("/Users/thrill3r/Auto-Quant")

PROVIDER = "IBKR"
SYMBOL = "CVX"
SEC_TYPE = "STK"
PRIMARY_EXCHANGE = "NYSE"
AQ_SYMBOL = "IBKR_CVX_PSAR_ADX_TREND_AQ_GATE1_V1"
FACTOR_ID = "ibkr_cvx_psar_adx_trend_aq_gate1_v1"
BRANCH_PATH = (
    "TrendExpansion -> EnergyMajorPsarAdxTrend -> "
    "psar_adx_trend_continuation -> ibkr_cvx_psar_adx_trend_aq_gate1_v1"
)
BRANCH_PARTS = [part.strip() for part in BRANCH_PATH.split(" -> ")]
CONTEXT_TIMEFRAMES = ["5m", "15m", "30m", "1h", "4h", "1d"]
MIN_TRADES_PER_DAY = 1.0 / 3.0
MAX_TRADES_PER_DAY = 3.0
COMMAND_SYMBOL_SLUG = "cvx"
STRATEGY_CLASS_STEM = "IbkrCvxPsarAdxTrend"
PACKAGE_PREFIX = "ibkr-cvx-psar-adx-trend"
TITLE_LABEL = "IBKR CVX PSAR/ADX trend continuation"
STRATEGY_BRIEF = "Energy-major CVX PSAR flip plus ADX directional-strength continuation with 1m origin and retained multi-timeframe context."
GATE_ID = "Gate1IbkrCvxPsarAdxTrendContinuation"
SUMMARY_TITLE = "IBKR CVX PSAR/ADX Trend AQ Gate 1"


@dataclass(frozen=True)
class Spec:
    timeframe: str
    bar_size: str
    duration: str
    source_name: str
    role: str


SPECS = [
    Spec("1m", "1 min", "30 D", "ibkr_cvx_1m_30d.csv", "training_origin"),
    Spec("5m", "5 mins", "3 M", "ibkr_cvx_5m_3m.csv", "small_cycle"),
    Spec("15m", "15 mins", "3 M", "ibkr_cvx_15m_3m.csv", "small_cycle_sibling"),
    Spec("30m", "30 mins", "3 M", "ibkr_cvx_30m_3m.csv", "neutralizer"),
    Spec("1h", "1 hour", "3 M", "ibkr_cvx_1h_3m.csv", "higher_timeframe_veto"),
    Spec("4h", "4 hours", "1 Y", "ibkr_cvx_4h_1y.csv", "macro_context"),
    Spec("1d", "1 day", "2 Y", "ibkr_cvx_1d_2y.csv", "daily_context"),
]
SPECS_BY_TIMEFRAME = {spec.timeframe: spec for spec in SPECS}


def run_cmd(name: str, argv: list[object], timeout: int = 300) -> dict:
    (ROOT / "command-output").mkdir(parents=True, exist_ok=True)
    (ROOT / "checks").mkdir(parents=True, exist_ok=True)
    argv_s = [str(item) for item in argv]
    (ROOT / "command-output" / f"{name}.cmd").write_text(" ".join(argv_s) + "\n", encoding="utf-8")
    env = os.environ.copy()
    env["ICT_ENGINE_IBKR_ENABLE"] = "1"
    try:
        proc = subprocess.run(argv_s, cwd=REPO, text=True, capture_output=True, timeout=timeout, env=env)
        stdout, stderr, rc, timed_out = proc.stdout, proc.stderr, proc.returncode, False
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout or ""
        stderr = exc.stderr or ""
        if isinstance(stdout, bytes):
            stdout = stdout.decode("utf-8", errors="replace")
        if isinstance(stderr, bytes):
            stderr = stderr.decode("utf-8", errors="replace")
        stderr += f"\nTIMEOUT after {timeout}s\n"
        rc, timed_out = 124, True
    (ROOT / "command-output" / f"{name}.out").write_text(stdout, encoding="utf-8")
    (ROOT / "command-output" / f"{name}.err").write_text(stderr, encoding="utf-8")
    (ROOT / "checks" / f"{name}.exit").write_text(f"{rc}\n", encoding="utf-8")
    return {"name": name, "exit": rc, "timed_out": timed_out}


def normalize_csv(source: Path, destination: Path) -> int:
    if not source.exists() or source.stat().st_size == 0:
        return 0
    rows: list[dict[str, str]] = []
    with source.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        headers = reader.fieldnames or []
        time_key = next((key for key in ("timestamp", "time", "datetime", "date", "ts", "ts_event") if key in headers), None)
        if not time_key:
            return 0
        for row in reader:
            timestamp = (row.get(time_key) or "").strip()
            if not timestamp:
                continue
            if not all(row.get(key) not in (None, "") for key in ("open", "high", "low", "close")):
                continue
            rows.append(
                {
                    "timestamp": timestamp,
                    "open": row.get("open", ""),
                    "high": row.get("high", ""),
                    "low": row.get("low", ""),
                    "close": row.get("close", ""),
                    "volume": row.get("volume") or "0",
                }
            )
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["timestamp", "open", "high", "low", "close", "volume"])
        writer.writeheader()
        writer.writerows(rows)
    return len(rows)


def timerange(path: Path) -> str:
    dates: list[str] = []
    with path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            raw = (row.get("timestamp") or "").strip()
            if raw:
                dates.append(raw[:10].replace("-", ""))
    return f"{min(dates)}-{max(dates)}" if dates else ""


def trading_days(path: Path) -> int:
    days: set[str] = set()
    if path.exists():
        with path.open(newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                raw = (row.get("timestamp") or "").strip()
                if raw:
                    days.add(raw[:10])
    return max(1, len(days))


def suffix(timeframe: str) -> str:
    return timeframe.replace("m", "Min").replace("h", "Hour").replace("d", "Day")


def strategy_class_name(spec: Spec) -> str:
    return f"{STRATEGY_CLASS_STEM}{suffix(spec.timeframe)}V1"


def unverified_equity_cost_model(timeframe: str) -> dict:
    return {
        "status": "cost_model_unverified",
        "instrument_class": "US_EQUITY",
        "symbol": SYMBOL,
        "sec_type": SEC_TYPE,
        "primary_exchange": PRIMARY_EXCHANGE,
        "venue_routing": "SMART",
        "currency": "USD",
        "broker": PROVIDER,
        "pricing_plan": "unknown",
        "account_region": "unknown",
        "unit_convention": "per_share_commission_plus_regulatory_fees",
        "fee_effective_date": "unverified",
        "timeframe": timeframe,
        "source_refs": [],
        "verification_blocker": "official IBKR equity commission schedule was not verified in this run",
    }


def strategy_source(class_name: str, timeframe: str) -> str:
    intraday = timeframe not in {"4h", "1d"}
    entry_window = (
        "((minute >= 13 * 60 + 35) & (minute <= 19 * 60 + 45)) | "
        "((minute >= 0) & (minute <= 2 * 60 + 10))"
        if intraday
        else "True"
    )
    force_exit_window = "(minute >= 20 * 60 + 50) & (minute <= 21 * 60 + 55)" if intraday else "False"
    return f'''from freqtrade.strategy import IStrategy
from pandas import DataFrame


class {class_name}(IStrategy):
    INTERFACE_VERSION = 3
    timeframe = "{timeframe}"
    can_short = True
    minimal_roi = {{"0": 0.020, "240": 0.010, "720": 0.004}}
    stoploss = -0.022
    trailing_stop = True
    trailing_stop_positive = 0.005
    trailing_stop_positive_offset = 0.014
    trailing_only_offset_is_reached = True
    process_only_new_candles = True
    use_exit_signal = True
    startup_candle_count = 260

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        high = dataframe["high"]
        low = dataframe["low"]
        close = dataframe["close"]
        tr = DataFrame({{"hl": high - low, "hc": (high - close.shift()).abs(), "lc": (low - close.shift()).abs()}}).max(axis=1)
        dataframe["atr14"] = tr.rolling(14).mean()
        atr_safe = dataframe["atr14"].replace(0, 1e-9)
        up_move = high.diff()
        down_move = -low.diff()
        plus_dm = up_move.where((up_move > down_move) & (up_move > 0), 0.0)
        minus_dm = down_move.where((down_move > up_move) & (down_move > 0), 0.0)
        plus_di = 100.0 * plus_dm.rolling(14).sum() / atr_safe.rolling(14).sum().replace(0, 1e-9)
        minus_di = 100.0 * minus_dm.rolling(14).sum() / atr_safe.rolling(14).sum().replace(0, 1e-9)
        dx = ((plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, 1e-9)) * 100.0
        dataframe["plus_di"] = plus_di
        dataframe["minus_di"] = minus_di
        dataframe["adx14"] = dx.rolling(14).mean()
        dataframe["ema21"] = close.ewm(span=21, adjust=False).mean()
        dataframe["ema55"] = close.ewm(span=55, adjust=False).mean()
        dataframe["ema144"] = close.ewm(span=144, adjust=False).mean()
        dataframe["rvol45"] = dataframe["volume"] / dataframe["volume"].rolling(45).mean().replace(0, 1)
        delta = close.diff()
        gain = delta.clip(lower=0).rolling(14).mean()
        loss = (-delta.clip(upper=0)).rolling(14).mean().replace(0, 1e-9)
        dataframe["rsi14"] = 100.0 - (100.0 / (1.0 + gain / loss))
        swing_low = low.shift(1).rolling(24).min()
        swing_high = high.shift(1).rolling(24).max()
        band = (swing_high - swing_low).replace(0, 1e-9)
        dataframe["psar_proxy_long"] = swing_low + band * 0.18
        dataframe["psar_proxy_short"] = swing_high - band * 0.18
        dataframe["psar_flip_up"] = (close > dataframe["psar_proxy_long"]) & (close.shift(1) <= dataframe["psar_proxy_long"].shift(1))
        dataframe["psar_flip_down"] = (close < dataframe["psar_proxy_short"]) & (close.shift(1) >= dataframe["psar_proxy_short"].shift(1))
        dataframe["pullback_long_atr"] = (close - dataframe["ema21"]).abs() / atr_safe
        dataframe["pullback_short_atr"] = (close - dataframe["ema21"]).abs() / atr_safe
        dataframe["extension_up_atr"] = (close - dataframe["ema21"]) / atr_safe
        dataframe["extension_down_atr"] = (dataframe["ema21"] - close) / atr_safe
        minute = dataframe["date"].dt.hour * 60 + dataframe["date"].dt.minute
        dataframe["entry_window"] = {entry_window}
        dataframe["force_exit_window"] = {force_exit_window}
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["enter_long"] = 0
        dataframe["enter_short"] = 0
        dataframe["enter_tag"] = ""
        long_trend = (
            (dataframe["ema21"] > dataframe["ema55"])
            & (dataframe["ema55"] > dataframe["ema144"])
            & (dataframe["adx14"] >= 16.0)
            & (dataframe["plus_di"] > dataframe["minus_di"])
        )
        short_trend = (
            (dataframe["ema21"] < dataframe["ema55"])
            & (dataframe["ema55"] < dataframe["ema144"])
            & (dataframe["adx14"] >= 16.0)
            & (dataframe["minus_di"] > dataframe["plus_di"])
        )
        long_signal = (
            dataframe["entry_window"]
            & long_trend
            & (dataframe["rvol45"] >= 0.70)
            & dataframe["rsi14"].between(46.0, 78.0)
            & (dataframe["extension_up_atr"] <= 1.40)
            & (
                dataframe["psar_flip_up"]
                | ((dataframe["close"] > dataframe["psar_proxy_long"]) & (dataframe["pullback_long_atr"] <= 0.95))
            )
        )
        short_signal = (
            dataframe["entry_window"]
            & short_trend
            & (dataframe["rvol45"] >= 0.70)
            & dataframe["rsi14"].between(22.0, 54.0)
            & (dataframe["extension_down_atr"] <= 1.40)
            & (
                dataframe["psar_flip_down"]
                | ((dataframe["close"] < dataframe["psar_proxy_short"]) & (dataframe["pullback_short_atr"] <= 0.95))
            )
        )
        dataframe.loc[long_signal, ["enter_long", "enter_tag"]] = (1, "{FACTOR_ID}_long")
        dataframe.loc[short_signal, ["enter_short", "enter_tag"]] = (1, "{FACTOR_ID}_short")
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["exit_long"] = 0
        dataframe["exit_short"] = 0
        exit_long = (
            dataframe["force_exit_window"]
            | (dataframe["close"] < dataframe["ema21"] - dataframe["atr14"] * 0.35)
            | (dataframe["minus_di"] > dataframe["plus_di"])
            | (dataframe["rsi14"] > 82.0)
        )
        exit_short = (
            dataframe["force_exit_window"]
            | (dataframe["close"] > dataframe["ema21"] + dataframe["atr14"] * 0.35)
            | (dataframe["plus_di"] > dataframe["minus_di"])
            | (dataframe["rsi14"] < 18.0)
        )
        dataframe.loc[exit_long, "exit_long"] = 1
        dataframe.loc[exit_short, "exit_short"] = 1
        return dataframe
'''


def write_material_for_spec(spec: Spec, normalized_path: Path) -> Path:
    strategy_path = ROOT / "agent-material" / f"{strategy_class_name(spec)}.py"
    strategy_path.write_text(strategy_source(strategy_class_name(spec), spec.timeframe), encoding="utf-8")
    duration_tag = spec.duration.replace(" ", "").lower()
    package_id = f"{PACKAGE_PREFIX}-{spec.timeframe}-{duration_tag}-v1"
    material_path = ROOT / "agent-material" / f"{package_id}.material.json"
    payload = {
        "package_id": package_id,
        "title": f"{TITLE_LABEL} - {spec.timeframe} {spec.duration}",
        "symbol": SYMBOL,
        "timeframe": spec.timeframe,
        "timerange": timerange(normalized_path),
        "direction": "long_short",
        "data_path": str(normalized_path),
        "strategy_source_path": str(strategy_path),
        "strategy_class_name": strategy_class_name(spec),
        "strategy_brief": STRATEGY_BRIEF,
        "evaluation_priority": ["instrument_cost_verification", "ibkr_real_row_truth", "psar_adx_trend_continuation"],
        "consumer_evidence_profile": {
            "branch_path": BRANCH_PATH,
            "regime_profit_branch_path": BRANCH_PATH,
            "branch_id": FACTOR_ID,
            "main_regime": BRANCH_PARTS[0],
            "sub_regime": BRANCH_PARTS[1],
            "sub_sub_regime_or_profit_factor": BRANCH_PARTS[2],
            "profit_factor": BRANCH_PARTS[3],
            "profit_factor_id": FACTOR_ID,
            "market": "US_EQUITY",
            "product": "single_stock",
            "sector_or_family": "energy_major",
            "symbol_root": SYMBOL,
            "root_symbol": SYMBOL,
            "base_timeframe": "1m",
            "root_timeframe": "1m",
            "training_timeframe": spec.timeframe,
            "material_timeframe": spec.timeframe,
            "context_timeframes": CONTEXT_TIMEFRAMES,
            "provider": PROVIDER,
            "provider_window": spec.duration,
            "provider_provenance": f"IBKR {SYMBOL} {spec.timeframe} {spec.duration} same-session fetch without fixed port",
            "gate_id": GATE_ID,
            "cost_model_status": "cost_model_unverified",
            "promotion_cost_verified": False,
            "cost_model": unverified_equity_cost_model(spec.timeframe),
            "promotion_allowed": False,
            "trade_usable": False,
            "update_goal": False,
        },
        "notes": [
            f"source_provider={PROVIDER} {SYMBOL} {spec.timeframe} {spec.duration}",
            f"branch_path={BRANCH_PATH}",
            "ibkr_first=true",
            "requested_ladder=1m_5m_15m_30m_1h_4h_1d",
            "auto_port_probe=true",
            "equity_commission_model=unverified_fail_closed",
            "paper_sim_blocked_until_exact_instrument_cost_survivor=true",
        ],
    }
    material_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return material_path


def latest_rank_rows() -> list[dict]:
    rank_files = sorted((ROOT / "state/auto-quant" / AQ_SYMBOL).glob("auto_quant_agent_material_rank.*.json"))
    if not rank_files:
        return []
    (ROOT / "checks/rank_artifact_path.txt").write_text(str(rank_files[-1]) + "\n", encoding="utf-8")
    return json.loads(rank_files[-1].read_text(encoding="utf-8")).get("ranking", []) or []


def safe_float(value: object) -> float:
    try:
        return float(value)
    except Exception:
        return 0.0


def rank_timeframe(row: dict) -> str:
    value = row.get("timeframe")
    if value:
        return str(value)
    package_id = str(row.get("package_id") or "")
    prefix = f"{PACKAGE_PREFIX}-"
    if package_id.startswith(prefix):
        return package_id[len(prefix) :].split("-", 1)[0]
    text = " ".join(str(row.get(key) or "") for key in ("package_id", "unit_label", "provider_provenance"))
    for tf in ("15m", "30m", "5m", "1m", "1h", "4h", "1d"):
        if f"-{tf}-" in text or f"/{tf}" in text or f":{tf}" in text or f" {tf} " in text:
            return tf
    return "unknown"


def instrument_cost_rows(rank_rows: list[dict], day_counts: dict[str, int]) -> list[dict]:
    rows = []
    for row in rank_rows:
        timeframe = rank_timeframe(row)
        trade_count = int(row.get("trade_count") or 0)
        raw_pct = safe_float(row.get("total_profit_pct"))
        days = max(1, day_counts.get(timeframe, 1))
        trades_per_day = trade_count / days
        density_ok = MIN_TRADES_PER_DAY <= trades_per_day <= MAX_TRADES_PER_DAY
        rows.append(
            {
                "package_id": row.get("package_id"),
                "unit_label": row.get("unit_label"),
                "timeframe": timeframe,
                "trade_count": trade_count,
                "trading_days": days,
                "trades_per_day": trades_per_day,
                "raw_total_profit_pct": raw_pct,
                "instrument_cost_total_profit_pct": None,
                "instrument_cost_profit_factor": None,
                "win_rate_pct": safe_float(row.get("win_rate_pct")),
                "sharpe": safe_float(row.get("sharpe")),
                "cost_model_status": "cost_model_unverified",
                "cost_model_blocker": "official_equity_commission_model_not_verified",
                "cost_model": unverified_equity_cost_model(timeframe),
                "promotion_cost_verified": False,
                "survives_instrument_cost": False,
                "density_target_1_to_3_per_day": density_ok,
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
    table = []
    for row in instrument_rows:
        table.append(
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
    text = f"""# {SUMMARY_TITLE}

Decision: `{metrics["decision"]}`

Interpretation: {metrics["interpretation"]}

Next useful work: {metrics["next_useful_work"]}

## Instrument Cost Verification Table

| timeframe | trades | trades/day | raw | instrument cost | cost model status | promotion cost verified | survives instrument cost | gate1_survivor |
|---|---:|---:|---:|---:|---|---|---|---|
{chr(10).join(table) if table else "| n/a | 0 | 0.000 | 0.00% | unverified | `cost_model_unverified` | `False` | `False` | `False` |"}
"""
    (ROOT / "summaries/terminal_decision_summary.md").write_text(text, encoding="utf-8")


def main() -> int:
    for sub in ("data/provider/raw", "data/provider/normalized", "agent-material", "summaries", "checks", "command-output", "state", "scripts"):
        (ROOT / sub).mkdir(parents=True, exist_ok=True)
    shutil.copy2(Path(__file__).resolve(), ROOT / "scripts" / Path(__file__).name)

    command_results = [
        run_cmd("00_provider_status_ibkr", [ICT, "provider-status", "--provider", "ibkr", "--agent"], timeout=60)
    ]
    provider_rows = []
    day_counts: dict[str, int] = {}
    material_paths: list[str] = []
    material_rows: list[dict] = []

    for index, spec in enumerate(SPECS, start=1):
        duration_tag = spec.duration.replace(" ", "").lower()
        raw_path = ROOT / "data/provider/raw" / spec.source_name
        normalized_path = ROOT / "data/provider/normalized" / spec.source_name
        result = run_cmd(
            f"{index:02d}_ibkr_{COMMAND_SYMBOL_SLUG}_{spec.timeframe}_{duration_tag}_fetch",
            [
                PY,
                FETCH,
                "ibkr-historical",
                "--symbol",
                SYMBOL,
                "--sec-type",
                SEC_TYPE,
                "--exchange",
                "SMART",
                "--currency",
                "USD",
                "--primary-exchange",
                PRIMARY_EXCHANGE,
                "--bar-size",
                spec.bar_size,
                "--duration",
                spec.duration,
                "--what-to-show",
                "TRADES",
                "--rth",
                "--host",
                "127.0.0.1",
                "--client-id",
                str(1510 + index),
                "--market-data-type",
                "3",
                "--output",
                raw_path,
            ],
            timeout=540,
        )
        command_results.append(result)
        rows = normalize_csv(raw_path, normalized_path)
        days = trading_days(normalized_path) if rows else 0
        if rows:
            day_counts[spec.timeframe] = days
        provider_rows.append(
            {
                "provider": PROVIDER,
                "provider_label": f"{PROVIDER} {SYMBOL} {spec.timeframe} {spec.duration}",
                "symbol": SYMBOL,
                "timeframe": spec.timeframe,
                "bar_size": spec.bar_size,
                "duration": spec.duration,
                "role": spec.role,
                "path": str(normalized_path) if rows else "",
                "raw_path": str(raw_path) if rows else "",
                "rows": rows,
                "trading_days": days,
                "provider_data_acquired": "true" if result["exit"] == 0 and rows else "false",
                "provider_unreachable": "false" if result["exit"] == 0 and rows else "true",
                "local_cache_replay": "false",
                "exit": result["exit"],
            }
        )
        if not rows:
            continue
        material_path = write_material_for_spec(spec, normalized_path)
        material_paths.append(str(material_path))
        material_rows.append(
            {
                "branch_path": BRANCH_PATH,
                "timeframe": spec.timeframe,
                "duration": spec.duration,
                "material_path": str(material_path),
                "strategy_path": str(ROOT / "agent-material" / f"{strategy_class_name(spec)}.py"),
                "rows": rows,
                "trading_days": days,
            }
        )

    write_csv(ROOT / "summaries/provider_provenance_matrix.csv", provider_rows)
    (ROOT / "summaries/provider_provenance_matrix.json").write_text(json.dumps(provider_rows, indent=2) + "\n", encoding="utf-8")
    if material_rows:
        write_csv(ROOT / "summaries/material_paths.csv", material_rows)

    strategy_files = [row["strategy_path"] for row in material_rows]
    py_compile = run_cmd("08_strategy_py_compile", [PY, "-m", "py_compile", *strategy_files], timeout=60) if strategy_files else {"name": "08_strategy_py_compile", "exit": 1, "timed_out": False}
    command_results.append(py_compile)
    batch = dispatch = rank = None
    if material_paths and py_compile["exit"] == 0:
        batch_args: list[object] = [
            ICT,
            "auto-quant-agent-material-batch",
            "--symbol",
            AQ_SYMBOL,
            "--state-dir",
            ROOT / "state",
            "--max-parallel",
            "1",
        ]
        if AQ_REPO.exists():
            batch_args += ["--repo-url", AQ_REPO]
        batch_args += sum([["--material", path] for path in material_paths], [])
        batch = run_cmd("09_auto_quant_agent_material_batch", batch_args, timeout=2400)
        command_results.append(batch)
        if batch["exit"] == 0:
            dispatch = run_cmd(
                "10_auto_quant_agent_material_dispatch",
                [ICT, "auto-quant-agent-material-dispatch", "--symbol", AQ_SYMBOL, "--state-dir", ROOT / "state"],
                timeout=1800,
            )
            command_results.append(dispatch)
        if dispatch and dispatch["exit"] == 0:
            rank = run_cmd(
                "11_auto_quant_agent_material_rank",
                [ICT, "auto-quant-agent-material-rank", "--symbol", AQ_SYMBOL, "--state-dir", ROOT / "state"],
                timeout=300,
            )
            command_results.append(rank)

    rank_rows = latest_rank_rows() if rank and rank["exit"] == 0 else []
    cost_rows = instrument_cost_rows(rank_rows, day_counts)
    (ROOT / "checks/instrument_cost_table.json").write_text(json.dumps(cost_rows, indent=2) + "\n", encoding="utf-8")
    write_csv(ROOT / "summaries/rank_rows_instrument_cost.csv", cost_rows)

    exact_1m_instrument_cost_survivors = [row for row in cost_rows if row["timeframe"] == "1m" and row["gate1_survivor"]]
    non_origin_instrument_cost_survivors = [row for row in cost_rows if row["timeframe"] != "1m" and row["gate1_survivor"]]
    all_commands_ok = all(item["exit"] == 0 for item in command_results)
    branch_fields_preserved = bool(material_rows) and all(row["branch_path"] == BRANCH_PATH for row in material_rows)
    cost_model_verified = any(row["promotion_cost_verified"] for row in cost_rows)
    if exact_1m_instrument_cost_survivors and branch_fields_preserved and cost_model_verified:
        decision = "gate1_exact_1m_instrument_cost_density_survivor_downstream_candidate"
        interpretation = "Exact 1m origin survived verified instrument-cost economics within the user cadence band while preserving the regime-rooted branch."
        next_work = "Use the same rooted branch for downstream Pre-Bayes, BBN, CatBoost/path-ranker, and execution-tree readback; keep promotion false until those gates pass."
        pre_bayes_allowed = bbn_allowed = catboost_allowed = execution_tree_allowed = True
    elif rank_rows and not cost_model_verified:
        decision = "gate1_cost_model_unverified_no_downstream"
        interpretation = "AQ rank rows exist, but the exact IBKR CVX equity commission model was not verified from official sources, so cost survival and downstream admission fail closed."
        next_work = "Verify the official IBKR US equity commission, regulatory, routing, currency, account, pricing-plan, and fee-effective-date assumptions before any downstream practical admission."
        pre_bayes_allowed = bbn_allowed = catboost_allowed = execution_tree_allowed = False
    elif rank_rows and non_origin_instrument_cost_survivors:
        decision = "incubate_non_origin_context_positive_exact_1m_missing"
        interpretation = "Some higher-timeframe context rows survived verified instrument-cost economics and cadence, but the exact 1m origin did not. Preserve as evidence only."
        next_work = "Keep the same factor family but iterate the 1m entry structure; do not treat higher-timeframe positives as exact-origin admission proof."
        pre_bayes_allowed = bbn_allowed = catboost_allowed = execution_tree_allowed = False
    elif rank_rows:
        decision = "drop_gate1_instrument_cost_or_density_failed"
        interpretation = "AQ rank rows exist, but no timeframe met verified instrument-cost profitability inside the 0.333-to-3.0 trades/day cadence band."
        next_work = "Stop before downstream. Preserve the negative row truth and rotate to a materially different factor or repair the 1m entry economics."
        pre_bayes_allowed = bbn_allowed = catboost_allowed = execution_tree_allowed = False
    else:
        decision = "provider_or_aq_blocked_no_gate1_verdict"
        interpretation = "Provider/material/AQ did not produce rank rows, so there is no factor verdict yet."
        next_work = "Inspect command-output for the failed infrastructure leg and retry only that leg; do not call the factor positive or negative."
        pre_bayes_allowed = bbn_allowed = catboost_allowed = execution_tree_allowed = False

    metrics = {
        "run_root": str(ROOT),
        "factor_id": FACTOR_ID,
        "branch_path": BRANCH_PATH,
        "decision": decision,
        "provider_rows": provider_rows,
        "provider_data_acquired_count": sum(1 for row in provider_rows if row["provider_data_acquired"] == "true"),
        "material_count": len(material_rows),
        "rank_rows": len(rank_rows),
        "rank_total_trade_count": sum(int(row.get("trade_count") or 0) for row in rank_rows),
        "positive_raw_rows": sum(1 for row in cost_rows if row["raw_total_profit_pct"] > 0),
        "promotion_cost_verified": cost_model_verified,
        "cost_model_status": "verified" if cost_model_verified else "cost_model_unverified",
        "instrument_cost_rows": cost_rows,
        "exact_1m_survivors_instrument_cost": exact_1m_instrument_cost_survivors,
        "non_origin_survivors_instrument_cost": non_origin_instrument_cost_survivors,
        "branch_fields_preserved": branch_fields_preserved,
        "command_results": command_results,
        "all_commands_ok": all_commands_ok,
        "pre_bayes_allowed": pre_bayes_allowed,
        "bbn_allowed": bbn_allowed,
        "catboost_allowed": catboost_allowed,
        "execution_tree_allowed": execution_tree_allowed,
        "promotion_allowed": False,
        "trade_usable": False,
        "update_goal": False,
        "interpretation": interpretation,
        "next_useful_work": next_work,
    }
    (ROOT / "checks/terminal_metrics.json").write_text(json.dumps(metrics, indent=2) + "\n", encoding="utf-8")
    (ROOT / "summaries/terminal_metrics.json").write_text(json.dumps(metrics, indent=2) + "\n", encoding="utf-8")
    validation = {
        "run_root_exists": ROOT.exists(),
        "provider_rows": len(provider_rows),
        "material_count": len(material_rows),
        "rank_rows": len(rank_rows),
        "rank_total_trade_count": metrics["rank_total_trade_count"],
        "commands_all_zero": all_commands_ok,
        "branch_fields_preserved": branch_fields_preserved,
        "decision": decision,
    }
    (ROOT / "checks/artifact_validation.json").write_text(json.dumps(validation, indent=2) + "\n", encoding="utf-8")
    with (ROOT / "checks/prompt_to_artifact_checklist.csv").open("w", newline="", encoding="utf-8") as handle:
        csv.writer(handle).writerows(
            [
                ["item", "status", "evidence"],
                ["ibkr_provider_invoked", "yes", str(ROOT / "command-output/00_provider_status_ibkr.cmd")],
                ["cvx_nyse_stock_contract", "yes", f"{SYMBOL} {SEC_TYPE} {PRIMARY_EXCHANGE}"],
                ["requested_full_ladder", "yes", "1m/5m/15m/30m/1h/4h/1d"],
                ["branch_fields_preserved", "yes" if branch_fields_preserved else "no", BRANCH_PATH],
                ["instrument_cost_table_written", "yes", str(ROOT / "checks/instrument_cost_table.json")],
                ["one_third_to_three_trades_per_day_gate", "yes", f"{MIN_TRADES_PER_DAY:.6f}-{MAX_TRADES_PER_DAY:.1f}"],
                ["downstream_blocked_or_allowed_by_gate1", "yes", decision],
                ["commands_all_zero", "yes" if all_commands_ok else "no", str(ROOT / "checks")],
            ]
        )
    write_terminal_summary(metrics, cost_rows)
    (ROOT / "checks/ibkr_cvx_psar_adx_trend_aq_gate1_v1.exit").write_text("0\n", encoding="utf-8")
    print(str(ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
