#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import shutil
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from statistics import median
from typing import Any
from zoneinfo import ZoneInfo


REPO = Path("/Users/thrill3r/projects-ict-engine/ict-engine")
BASE = REPO / "support/docs/experiments/actionable-regime-confidence"
STAMP = datetime.now(ZoneInfo("Asia/Shanghai")).strftime("%Y%m%dT%H%M%S+0800")
ROOT = Path("/tmp") / f"ict-engine-6b-eth-boe-rate-differential-london-stoprun-vwap-reclaim-gate1-{STAMP}"
PY = Path("/Users/thrill3r/.venvs/ict-engine-provider-py313/bin/python")
if not PY.exists():
    PY = Path("python3")
FETCH = REPO / "support/scripts/auto_quant_external/fetch_external.py"
ICT = REPO / ".local-artifacts/cargo-target/debug/ict-engine"
if not ICT.exists():
    ICT = REPO / "target/debug/ict-engine"
AQ_REPO = Path("/Users/thrill3r/Auto-Quant")

AQ_SYMBOL = "IBKR_6B1M_BOE_RATE_DIFFERENTIAL_LONDON_STOPRUN_VWAP_RECLAIM_GATE1_V1"
FACTOR_ID = "6b_eth_boe_rate_differential_london_stoprun_vwap_reclaim_v1"
SESSION_SCOPE = "ETH/full_retained_session"
RTH_FILTER_APPLIED = False
CONTEXT_TIMEFRAMES = ["5m", "15m", "30m", "1h", "4h", "1d"]
REQUIRED_TIMEFRAMES = ["1m", *CONTEXT_TIMEFRAMES]
BRANCH_PATH = (
    "FUTURES -> FXFutures -> CME British Pound / 6B -> ETH/full_retained_session -> "
    "1m execution + shifted 5m/15m/30m/1h/4h/1d context -> "
    "BoE_FedRateDifferentialTransition -> LondonNYLiquidityStopRun -> "
    "VwapReclaimAfterSterlingPolicyShock -> AtrRiskManagedMtfContinuation -> "
    "6b_eth_boe_rate_differential_london_stoprun_vwap_reclaim_v1"
)
PARTS = [part.strip() for part in BRANCH_PATH.split(" -> ")]

IBKR_COST_MODEL_STATUS = "verified_ibkr_broker_side_current_schedule_under_assumptions"
IBKR_COST_SOURCE = "/tmp/ict-engine-6b-eth-boe-rate-differential-london-stoprun-vwap-reclaim-prep-20260530T031647+0800/source_evidence/6b_ibkr_cost_model_20260530T031647+0800.json"
COMMISSION_PER_SIDE_USD = 0.85
EXCHANGE_FEE_PER_SIDE_USD = 1.60
REGULATORY_FEE_PER_SIDE_USD = 0.02
ALL_IN_PER_SIDE_USD = 2.47
ALL_IN_ROUND_TURN_USD = 4.94
TICK_VALUE_USD = 6.25
MIN_TICK = 0.0001


@dataclass(frozen=True)
class Contract:
    human_root: str
    symbol: str
    product: str
    exchange: str
    currency: str
    multiplier: str
    last_trade_date: str


@dataclass(frozen=True)
class Spec:
    timeframe: str
    bar_size: str
    duration: str
    role: str


CONTRACT = Contract("6B", "GBP", "fx_futures", "CME", "USD", "62500", "202606")
SPECS = [
    Spec("1m", "1 min", "7 D", "exact_training_origin"),
    Spec("5m", "5 mins", "1 M", "small_cycle_context"),
    Spec("15m", "15 mins", "1 M", "small_cycle_sibling"),
    Spec("30m", "30 mins", "1 M", "neutralization_context"),
    Spec("1h", "1 hour", "1 M", "higher_timeframe_veto"),
    Spec("4h", "4 hours", "1 M", "attempt_if_provider_supported"),
    Spec("1d", "1 day", "6 M", "daily_context"),
]
SPEC_BY_TIMEFRAME = {spec.timeframe: spec for spec in SPECS}

VARIANTS = {
    "dense": {"roi": 0.0017, "stop": -0.0044, "trail": 0.0007, "off": 0.0019, "sweep_atr": 0.035, "reclaim_atr": 0.075, "slope_floor": -0.010, "rvol": 0.45, "max_ext": 1.25, "max_rsi": 76, "min_policy_proxy": 0.25},
    "balanced": {"roi": 0.0026, "stop": -0.0062, "trail": 0.0011, "off": 0.0028, "sweep_atr": 0.060, "reclaim_atr": 0.115, "slope_floor": 0.000, "rvol": 0.58, "max_ext": 1.00, "max_rsi": 72, "min_policy_proxy": 0.35},
    "quality": {"roi": 0.0038, "stop": -0.0082, "trail": 0.0016, "off": 0.0040, "sweep_atr": 0.095, "reclaim_atr": 0.160, "slope_floor": 0.018, "rvol": 0.78, "max_ext": 0.80, "max_rsi": 68, "min_policy_proxy": 0.50},
}


def backend_busy() -> bool:
    proc = subprocess.run(["ps", "-axo", "command"], text=True, capture_output=True, timeout=20)
    for line in proc.stdout.splitlines():
        if AQ_SYMBOL in line or Path(__file__).name in line:
            continue
        if "factor_claim_terminalization_audit.py" in line:
            continue
        if "/bin/zsh -lc while ps" in line or "while ps -axo command" in line:
            continue
        needles = (
            "/ict-engine auto-quant-agent-material-dispatch",
            "/ict-engine auto-quant-agent-material-rank",
            "run_tomac.py",
            "fetch_external.py ibkr-historical",
            "pandas_path_ranker_trainer.py",
            "freqtrade backtesting",
        )
        if any(needle in line for needle in needles):
            return True
    return False


def run_cmd(name: str, argv: list[object], timeout: int = 300) -> dict[str, Any]:
    (ROOT / "command-output").mkdir(parents=True, exist_ok=True)
    (ROOT / "checks").mkdir(parents=True, exist_ok=True)
    argv_s = [str(item) for item in argv]
    (ROOT / "command-output" / f"{name}.cmd").write_text(" ".join(argv_s) + "\n", encoding="utf-8")
    try:
        proc = subprocess.run(argv_s, cwd=REPO, text=True, capture_output=True, timeout=timeout)
        stdout, stderr, rc, timed_out = proc.stdout, proc.stderr, proc.returncode, False
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout or ""
        stderr = (exc.stderr or "") + f"\nTIMEOUT after {timeout}s\n"
        rc, timed_out = 124, True
    if isinstance(stdout, bytes):
        stdout = stdout.decode("utf-8", errors="replace")
    if isinstance(stderr, bytes):
        stderr = stderr.decode("utf-8", errors="replace")
    out_path = ROOT / "command-output" / f"{name}.out"
    err_path = ROOT / "command-output" / f"{name}.err"
    exit_path = ROOT / "checks" / f"{name}.exit"
    out_path.write_text(stdout, encoding="utf-8")
    err_path.write_text(stderr, encoding="utf-8")
    exit_path.write_text(f"{rc}\n", encoding="utf-8")
    return {"name": name, "exit": rc, "timed_out": timed_out, "stdout_path": str(out_path), "stderr_path": str(err_path), "exit_path": str(exit_path)}


def normalize_root_path(value: object) -> str | None:
    if value in (None, ""):
        return None
    return str(Path(str(value)).expanduser().resolve())


def claim_collision_blockers(audit: dict[str, Any], *, allowed_roots: set[Path]) -> dict[str, Any]:
    allowed = {normalize_root_path(root) for root in allowed_roots}
    foreign_active_claims: list[dict[str, Any]] = []
    for claim in audit.get("claims") or []:
        if str(claim.get("status") or "").lower() != "active":
            continue
        if bool(claim.get("coordination_only")):
            continue
        claim_roots = {normalize_root_path(claim.get("run_root")), normalize_root_path(claim.get("tmp_root"))}
        claim_roots.discard(None)
        if claim_roots and claim_roots.issubset(allowed):
            continue
        foreign_active_claims.append(
            {
                "claim_file": claim.get("claim_file"),
                "run_root": claim.get("run_root"),
                "tmp_root": claim.get("tmp_root"),
                "scope": claim.get("scope"),
            }
        )

    foreign_live_processes: list[dict[str, Any]] = []
    for process in audit.get("live_factor_processes") or []:
        process_root = normalize_root_path(process.get("run_root"))
        if process_root in allowed:
            continue
        foreign_live_processes.append(
            {
                "pid": process.get("pid"),
                "run_root": process.get("run_root"),
                "command_excerpt": process.get("command_excerpt") or process.get("command"),
            }
        )

    return {
        "pass": not foreign_active_claims and not foreign_live_processes,
        "foreign_active_claims": foreign_active_claims,
        "foreign_live_processes": foreign_live_processes,
    }


def run_claim_collision_audit() -> dict[str, Any]:
    command = run_cmd("pre_launch_claim_collision_audit", ["python3", "support/scripts/factor_claim_terminalization_audit.py"], timeout=180)
    audit_path = Path(command["stdout_path"])
    try:
        audit = json.loads(audit_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        guard = {"pass": False, "decision": "launch_blocked_claim_audit_json_parse_failure", "error": str(exc), "command": command}
    else:
        guard = claim_collision_blockers(audit, allowed_roots={ROOT})
        guard.update(
            {
                "decision": "claim_collision_guard_pass" if guard["pass"] else "launch_blocked_by_foreign_claim_or_runtime",
                "command": command,
                "audit_summary": audit.get("summary"),
            }
        )
    (ROOT / "checks").mkdir(parents=True, exist_ok=True)
    (ROOT / "summaries").mkdir(parents=True, exist_ok=True)
    (ROOT / "checks/pre_launch_claim_collision_guard.json").write_text(json.dumps(guard, indent=2) + "\n", encoding="utf-8")
    if not guard["pass"]:
        (ROOT / "summaries/terminal_no_launch_summary.json").write_text(json.dumps(guard, indent=2) + "\n", encoding="utf-8")
    return guard


def normalize(src: Path, dst: Path) -> int:
    if not src.exists() or src.stat().st_size == 0:
        return 0
    with src.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        headers = reader.fieldnames or []
        time_key = next((key for key in ("timestamp", "time", "datetime", "ts_event", "date", "ts") if key in headers), None)
        if not time_key:
            return 0
        rows = []
        for row in reader:
            if all(row.get(key) not in (None, "") for key in ("open", "high", "low", "close")):
                rows.append(
                    {
                        "timestamp": row.get(time_key, ""),
                        "open": row.get("open", ""),
                        "high": row.get("high", ""),
                        "low": row.get("low", ""),
                        "close": row.get("close", ""),
                        "volume": row.get("volume") or "0",
                    }
                )
    dst.parent.mkdir(parents=True, exist_ok=True)
    with dst.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["timestamp", "open", "high", "low", "close", "volume"])
        writer.writeheader()
        writer.writerows(rows)
    return len(rows)


def timerange(path: Path) -> str:
    if not path.exists() or path.stat().st_size == 0:
        return ""
    dates = []
    with path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            raw = (row.get("timestamp") or "").strip()
            if raw:
                dates.append(raw[:10].replace("-", ""))
    return f"{min(dates)}-{max(dates)}" if dates else ""


def suffix(tf: str) -> str:
    return tf.replace("m", "Min").replace("h", "Hour").replace("d", "Day")


def class_name(spec: Spec, variant: str) -> str:
    return f"Ibkr6bBoeRateDifferentialStoprun{variant.title()}{suffix(spec.timeframe)}V1"


def fetch_args(spec: Spec, output: Path, client_id: int) -> list[object]:
    return [
        PY,
        FETCH,
        "ibkr-historical",
        "--symbol",
        CONTRACT.symbol,
        "--sec-type",
        "FUT",
        "--exchange",
        CONTRACT.exchange,
        "--currency",
        CONTRACT.currency,
        "--last-trade-date",
        CONTRACT.last_trade_date,
        "--multiplier",
        CONTRACT.multiplier,
        "--bar-size",
        spec.bar_size,
        "--duration",
        spec.duration,
        "--what-to-show",
        "TRADES",
        "--client-id",
        str(client_id),
        "--market-data-type",
        "3",
        "--output",
        output,
    ]


def strategy_source(name: str, tf: str, variant: str, cfg: dict[str, float]) -> str:
    tag = f"{FACTOR_ID}_{variant}_{tf}"
    return f'''from freqtrade.strategy import IStrategy
from pandas import DataFrame


class {name}(IStrategy):
    INTERFACE_VERSION = 3
    timeframe = "{tf}"
    can_short = True
    minimal_roi = {{"0": {cfg['roi']}}}
    stoploss = {cfg['stop']}
    trailing_stop = True
    trailing_stop_positive = {cfg['trail']}
    trailing_stop_positive_offset = {cfg['off']}
    trailing_only_offset_is_reached = True
    process_only_new_candles = True
    use_exit_signal = True
    startup_candle_count = 240

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        close = dataframe["close"]
        high = dataframe["high"]
        low = dataframe["low"]
        volume = dataframe["volume"]
        prev_close = close.shift()
        tr = DataFrame({{"hl": high - low, "hc": (high - prev_close).abs(), "lc": (low - prev_close).abs()}}).max(axis=1)
        dataframe["atr14"] = tr.rolling(14).mean()
        dataframe["atr50"] = tr.rolling(50).mean()
        dataframe["ema21"] = close.ewm(span=21, adjust=False).mean()
        dataframe["ema55"] = close.ewm(span=55, adjust=False).mean()
        dataframe["ema144"] = close.ewm(span=144, adjust=False).mean()
        dataframe["htf_slope_proxy"] = (dataframe["ema55"] - dataframe["ema55"].shift(18)) / dataframe["atr14"].replace(0, 1)
        delta = close.diff()
        gain = delta.clip(lower=0).rolling(14).mean()
        loss = (-delta.clip(upper=0)).rolling(14).mean().replace(0, 0.000001)
        dataframe["rsi14"] = 100.0 - (100.0 / (1.0 + gain / loss))
        dt = dataframe["date"]
        day_key = dt.dt.strftime("%Y-%m-%d")
        minute = dt.dt.hour * 60 + dt.dt.minute
        dataframe["asia_window"] = (minute >= 0) & (minute < 7 * 60)
        dataframe["london_ny_window"] = (minute >= 7 * 60) & (minute < 16 * 60)
        dataframe["late_exit_window"] = (minute >= 20 * 60 + 30) & (minute < 22 * 60)
        dataframe["asia_high"] = high.where(dataframe["asia_window"]).groupby(day_key).transform("max")
        dataframe["asia_low"] = low.where(dataframe["asia_window"]).groupby(day_key).transform("min")
        typical = (high + low + close) / 3.0
        pv = typical * volume
        dataframe["session_vwap"] = pv.groupby(day_key).cumsum() / volume.groupby(day_key).cumsum().replace(0, 1)
        dataframe["vol80"] = volume.rolling(80).mean()
        dataframe["rvol"] = volume / dataframe["vol80"].replace(0, 1)
        dataframe["range_atr"] = (dataframe["asia_high"] - dataframe["asia_low"]) / dataframe["atr14"].replace(0, 1)
        dataframe["vwap_distance_atr"] = (close - dataframe["session_vwap"]) / dataframe["atr14"].replace(0, 1)
        dataframe["policy_shock_proxy"] = (dataframe["rvol"].clip(upper=8) / 8.0 + dataframe["range_atr"].clip(upper=4) / 4.0) / 2.0
        dataframe["sweep_low"] = low <= dataframe["asia_low"] - dataframe["atr14"] * {cfg['sweep_atr']}
        dataframe["sweep_high"] = high >= dataframe["asia_high"] + dataframe["atr14"] * {cfg['sweep_atr']}
        dataframe["recent_sweep_low"] = dataframe["sweep_low"].rolling(12).max().fillna(0) > 0
        dataframe["recent_sweep_high"] = dataframe["sweep_high"].rolling(12).max().fillna(0) > 0
        dataframe["stoprun_reclaim_long"] = dataframe["recent_sweep_low"] & (close > dataframe["session_vwap"] - dataframe["atr14"] * {cfg['reclaim_atr']}) & (close > dataframe["asia_low"])
        dataframe["stoprun_reclaim_short"] = dataframe["recent_sweep_high"] & (close < dataframe["session_vwap"] + dataframe["atr14"] * {cfg['reclaim_atr']}) & (close < dataframe["asia_high"])
        dataframe["trend_resonance_long"] = (dataframe["ema21"] >= dataframe["ema55"] - dataframe["atr14"] * 0.12) & (dataframe["ema55"] >= dataframe["ema144"] - dataframe["atr14"] * 0.35) & (dataframe["htf_slope_proxy"].fillna(0) >= {cfg['slope_floor']})
        dataframe["trend_resonance_short"] = (dataframe["ema21"] <= dataframe["ema55"] + dataframe["atr14"] * 0.12) & (dataframe["ema55"] <= dataframe["ema144"] + dataframe["atr14"] * 0.35) & (dataframe["htf_slope_proxy"].fillna(0) <= -{cfg['slope_floor']})
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["enter_long"] = 0
        dataframe["enter_short"] = 0
        dataframe["enter_tag"] = ""
        range_ok = dataframe["range_atr"] >= 0.75
        participation = dataframe["rvol"] >= {cfg['rvol']}
        policy_ok = dataframe["policy_shock_proxy"] >= {cfg['min_policy_proxy']}
        long_extension_ok = dataframe["vwap_distance_atr"].between(-0.35, {cfg['max_ext']})
        short_extension_ok = dataframe["vwap_distance_atr"].between(-{cfg['max_ext']}, 0.35)
        rsi_long_ok = dataframe["rsi14"].between(34, {cfg['max_rsi']})
        rsi_short_ok = dataframe["rsi14"].between(100 - {cfg['max_rsi']}, 66)
        long_signal = dataframe["london_ny_window"] & range_ok & participation & policy_ok & long_extension_ok & rsi_long_ok & dataframe["stoprun_reclaim_long"] & dataframe["trend_resonance_long"]
        short_signal = dataframe["london_ny_window"] & range_ok & participation & policy_ok & short_extension_ok & rsi_short_ok & dataframe["stoprun_reclaim_short"] & dataframe["trend_resonance_short"]
        dataframe.loc[long_signal, ["enter_long", "enter_tag"]] = (1, "{tag}_long")
        dataframe.loc[short_signal, ["enter_short", "enter_tag"]] = (1, "{tag}_short")
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["exit_long"] = 0
        dataframe["exit_short"] = 0
        failed_long_reclaim = dataframe["close"] < dataframe[["session_vwap", "asia_low"]].min(axis=1) - dataframe["atr14"] * 0.35
        failed_short_reclaim = dataframe["close"] > dataframe[["session_vwap", "asia_high"]].max(axis=1) + dataframe["atr14"] * 0.35
        long_rollover = dataframe["close"] < dataframe["ema55"] - dataframe["atr14"] * 0.30
        short_rollover = dataframe["close"] > dataframe["ema55"] + dataframe["atr14"] * 0.30
        dataframe.loc[dataframe["late_exit_window"] | failed_long_reclaim | long_rollover | (dataframe["rsi14"] > 84), "exit_long"] = 1
        dataframe.loc[dataframe["late_exit_window"] | failed_short_reclaim | short_rollover | (dataframe["rsi14"] < 16), "exit_short"] = 1
        return dataframe
'''


def build_material_payload(spec: Spec, variant: str, strategy_path: Path, normalized_data_path: Path, strategy_class_name: str) -> tuple[Path, dict[str, Any]]:
    material_path = ROOT / "agent-material" / f"ibkr_6b_boe_rate_differential_london_stoprun_vwap_reclaim_{variant}_{spec.timeframe}_v1.material.json"
    material = {
        "package_id": f"ibkr-6b-boe-rate-differential-london-stoprun-vwap-reclaim-{variant}-{spec.timeframe}-v1",
        "title": f"IBKR 6B BoE rate-differential London stop-run VWAP reclaim {variant} {spec.timeframe}",
        "symbol": CONTRACT.symbol,
        "display_symbol": CONTRACT.human_root,
        "timeframe": spec.timeframe,
        "timerange": timerange(normalized_data_path),
        "direction": "long_short",
        "data_path": str(normalized_data_path),
        "strategy_source_path": str(strategy_path),
        "strategy_class_name": strategy_class_name,
        "strategy_brief": "6B/GBP ETH full-session stop-run through Asia range followed by VWAP reclaim after a local policy-shock proxy and higher-timeframe slope resonance.",
        "evaluation_priority": [
            "ibkr_native_futures_provider",
            "eth_full_retained_session",
            "exact_1m_origin_density",
            "shifted_mtf_ladder_provider_rows",
            "verified_real_contract_cost_survival",
            "same_tree_downstream_readiness",
        ],
        "consumer_evidence_profile": {
            "branch_path": BRANCH_PATH,
            "regime_profit_branch_path": BRANCH_PATH,
            "branch_id": FACTOR_ID,
            "market": "FUTURES",
            "product": CONTRACT.product,
            "root_symbol": CONTRACT.human_root,
            "broker_side_symbol": CONTRACT.symbol,
            "root_timeframe": "1m",
            "context_timeframes": CONTEXT_TIMEFRAMES,
            "session_scope": SESSION_SCOPE,
            "rth_filter_applied": RTH_FILTER_APPLIED,
            "main_regime": "BoE_FedRateDifferentialTransition",
            "sub_regime": "LondonNYLiquidityStopRun",
            "sub_sub_regime_or_profit_factor": "VwapReclaimAfterSterlingPolicyShock",
            "profit_factor": FACTOR_ID,
            "base_timeframe": "1m",
            "training_timeframe": "1m",
            "material_timeframe": spec.timeframe,
            "provider": "IBKR",
            "provider_window": spec.duration,
            "provider_provenance": f"IBKR FUT {CONTRACT.symbol}/{CONTRACT.human_root} {CONTRACT.last_trade_date} {spec.timeframe} {spec.duration}",
            "policy_sidecar_status": "unknown_unscored_proxy_only",
            "asset_class": "futures",
            "sec_type": "FUT",
            "exchange": CONTRACT.exchange,
            "currency": CONTRACT.currency,
            "multiplier": CONTRACT.multiplier,
            "last_trade_date": CONTRACT.last_trade_date,
            "cost_model_status": IBKR_COST_MODEL_STATUS,
            "cost_model_source": IBKR_COST_SOURCE,
            "tick_size": MIN_TICK,
            "tick_value_usd": TICK_VALUE_USD,
            "all_in_per_contract_per_side_usd": ALL_IN_PER_SIDE_USD,
            "all_in_round_turn_per_contract_usd": ALL_IN_ROUND_TURN_USD,
            "gate_id": "Gate1Ibkr6bBoeRateDifferentialLondonStoprunVwapReclaim",
            "promotion_allowed": False,
            "trade_usable": False,
            "update_goal": False,
        },
        "notes": [
            "ibkr_first=true",
            "session_scope=ETH/full_retained_session",
            "rth_filter_applied=false",
            "local_cache_replay=false",
            "policy_rate_differential_sidecar=unknown_unscored_proxy_only",
            "pre_bayes_bbn_catboost_execution_tree_allowed=false_until_exact_1m_real_cost_density_and_context_rows_pass",
        ],
    }
    return material_path, material


def latest_rank_rows() -> list[dict[str, Any]]:
    files = sorted((ROOT / f"state/auto-quant/{AQ_SYMBOL}").glob("auto_quant_agent_material_rank.*.json"))
    if not files:
        return []
    return json.loads(files[-1].read_text(encoding="utf-8")).get("ranking", []) or []


def safe_float(value: object) -> float:
    try:
        return float(str(value))
    except Exception:
        return 0.0


def row_label(row: dict[str, Any]) -> str:
    package = str(row.get("package_id") or "")
    variant = next((item for item in VARIANTS if f"-{item}-" in package), "unknown")
    timeframe = next((spec.timeframe for spec in SPECS if package.endswith(f"-{spec.timeframe}-v1")), str(row.get("timeframe") or "unknown"))
    return f"6B/{variant}/{timeframe}"


def read_provider_rows() -> list[dict[str, Any]]:
    matrix = ROOT / "summaries/provider_provenance_matrix.csv"
    if not matrix.exists():
        return []
    with matrix.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def cost_pct_by_timeframe(provider_rows: list[dict[str, Any]]) -> dict[str, float]:
    out: dict[str, float] = {}
    for row in provider_rows:
        path = Path(str(row.get("path") or ""))
        timeframe = str(row.get("timeframe") or "")
        if not path.exists() or int(row.get("rows") or 0) <= 0:
            continue
        closes: list[float] = []
        with path.open(newline="", encoding="utf-8") as handle:
            for record in csv.DictReader(handle):
                try:
                    value = float(record.get("close") or "")
                except ValueError:
                    continue
                if value > 0:
                    closes.append(value)
        if closes:
            notional = median(closes) * float(CONTRACT.multiplier)
            if notional > 0:
                out[timeframe] = (ALL_IN_ROUND_TURN_USD / notional) * 100.0
    return out


def required_provider_timeframes_covered(provider_rows: list[dict[str, Any]]) -> bool:
    covered = {str(row.get("timeframe")) for row in provider_rows if int(row.get("rows") or 0) > 0}
    return set(REQUIRED_TIMEFRAMES).issubset(covered)


def classify_provider_blocker(commands: list[dict[str, Any]], provider_rows: list[dict[str, Any]]) -> str | None:
    if not provider_rows:
        return None
    all_zero_rows = all(int(row.get("rows") or 0) == 0 for row in provider_rows)
    fetch_failed = any("ibkr_fetch" in str(cmd.get("name") or "") and int(cmd.get("exit") or 0) != 0 for cmd in commands)
    if not (all_zero_rows and fetch_failed):
        return None

    error_text = []
    for cmd in commands:
        path = cmd.get("stderr_path")
        if not path:
            continue
        stderr_path = Path(str(path))
        if stderr_path.exists():
            error_text.append(stderr_path.read_text(encoding="utf-8", errors="replace"))
    joined = "\n".join(error_text)
    if "no reachable local IBKR API port" in joined or "ibkr_gateway_unreachable" in joined:
        return "ibkr_gateway_unreachable"
    return "ibkr_historical_fetch_failed_zero_rows"


def build_terminal_metrics(commands: list[dict[str, Any]], rank_rows: list[dict[str, Any]], provider_rows: list[dict[str, Any]], branch_paths: list[str], cost_rows: list[dict[str, Any]]) -> dict[str, Any]:
    exact_1m_survivors = [
        row["label"]
        for row in cost_rows
        if str(row.get("label", "")).endswith("/1m") and bool(row.get("survives_real_cost")) and int(row.get("trade_count") or 0) >= 6
    ]
    branch_fields_preserved = bool(rank_rows) and all(path == BRANCH_PATH for path in branch_paths)
    context_rows_covered = required_provider_timeframes_covered(provider_rows)
    downstream_allowed = bool(branch_fields_preserved and exact_1m_survivors and context_rows_covered)
    provider_blocker = classify_provider_blocker(commands, provider_rows)
    decision = f"provider_blocked_{provider_blocker}" if provider_blocker else (
        "gate1_6b_boe_stoprun_exact_1m_downstream_allowed" if downstream_allowed else "drop_or_block_6b_boe_stoprun_gate1_practical"
    )
    covered = sorted({f"{row.get('symbol')}/{row.get('timeframe')}" for row in provider_rows if int(row.get("rows") or 0) > 0})
    missing = sorted({f"{row.get('symbol')}/{row.get('timeframe')}" for row in provider_rows if int(row.get("rows") or 0) == 0})
    return {
        "schema_version": "ibkr-6b-boe-stoprun-gate1-terminal/v1",
        "run_root": str(ROOT),
        "factor_id": FACTOR_ID,
        "branch_path_template": BRANCH_PATH,
        "session_scope": SESSION_SCOPE,
        "rth_filter_applied": RTH_FILTER_APPLIED,
        "origin_timeframe": "1m",
        "context_timeframes": CONTEXT_TIMEFRAMES,
        "cost_model_status": IBKR_COST_MODEL_STATUS,
        "cost_model_source": IBKR_COST_SOURCE,
        "all_in_per_contract_per_side_usd": ALL_IN_PER_SIDE_USD,
        "all_in_round_turn_per_contract_usd": ALL_IN_ROUND_TURN_USD,
        "decision": decision,
        "provider_blocked": provider_blocker is not None,
        "provider_blocker": provider_blocker,
        "provider_rows": provider_rows,
        "material_count": len(list((ROOT / "agent-material").glob("*.material.json"))),
        "rank_rows": len(rank_rows),
        "rank_total_trade_count": sum(int(row.get("trade_count") or 0) for row in rank_rows),
        "cost_rows": cost_rows,
        "exact_1m_real_cost_survivors": exact_1m_survivors,
        "branch_paths": branch_paths,
        "branch_fields_preserved": branch_fields_preserved,
        "context_rows_covered": context_rows_covered,
        "covered_timeframes": covered,
        "missing_timeframes": missing,
        "command_exits": {cmd["name"]: cmd["exit"] for cmd in commands},
        "downstream_allowed": downstream_allowed,
        "pre_bayes_allowed": downstream_allowed,
        "bbn_allowed": downstream_allowed,
        "catboost_allowed": downstream_allowed,
        "execution_tree_allowed": downstream_allowed,
        "promotion_allowed": False,
        "trade_usable": False,
        "update_goal": False,
    }


def write_terminal_metrics(metrics: dict[str, Any]) -> dict[str, Any]:
    metrics = {
        "schema_version": "ibkr-6b-boe-stoprun-gate1-terminal/v1",
        "run_root": str(ROOT),
        "factor_id": FACTOR_ID,
        "branch_path_template": BRANCH_PATH,
        "session_scope": SESSION_SCOPE,
        "rth_filter_applied": RTH_FILTER_APPLIED,
        "promotion_allowed": False,
        "trade_usable": False,
        "update_goal": False,
        **metrics,
    }
    (ROOT / "checks").mkdir(parents=True, exist_ok=True)
    (ROOT / "summaries").mkdir(parents=True, exist_ok=True)
    (ROOT / "checks/terminal_metrics.json").write_text(json.dumps(metrics, indent=2) + "\n", encoding="utf-8")
    (ROOT / "summaries/terminal_decision_summary.md").write_text("# Terminal Decision Summary\n\n" + json.dumps(metrics, indent=2) + "\n", encoding="utf-8")
    return metrics


def summarize_rank_result(commands: list[dict[str, Any]], rank: dict[str, Any] | None = None) -> dict[str, Any]:
    provider_rows = read_provider_rows()
    rank_rows = latest_rank_rows() if rank and rank["exit"] == 0 else []
    cost_by_tf = cost_pct_by_timeframe(provider_rows)
    cost_rows = []
    for row in rank_rows:
        label = row_label(row)
        timeframe = label.rsplit("/", 1)[-1]
        trades = int(row.get("trade_count") or 0)
        gross = safe_float(row.get("total_profit_pct"))
        real_cost_pct = cost_by_tf.get(timeframe)
        real_cost_total = None if real_cost_pct is None else round(gross - trades * real_cost_pct, 6)
        cost_rows.append(
            {
                "label": label,
                "trade_count": trades,
                "raw_total_profit_pct": gross,
                "win_rate_pct": safe_float(row.get("win_rate_pct")),
                "sharpe": safe_float(row.get("sharpe")),
                "round_turn_cost_pct_per_trade": real_cost_pct,
                "real_cost_total_profit_pct": real_cost_total,
                "survives_real_cost": real_cost_total is not None and trades >= 6 and real_cost_total > 0,
            }
        )
    branch_paths = sorted({str(row.get("branch_path") or row.get("consumer_evidence_profile", {}).get("branch_path") or "") for row in rank_rows})
    metrics = build_terminal_metrics(commands, rank_rows, provider_rows, branch_paths, cost_rows)
    write_terminal_metrics(metrics)
    return metrics


def selected_specs(timeframes: str) -> list[Spec]:
    requested = [item.strip() for item in timeframes.split(",") if item.strip()]
    unknown = [item for item in requested if item not in SPEC_BY_TIMEFRAME]
    if unknown:
        raise ValueError(f"unknown timeframes: {','.join(unknown)}")
    return [SPEC_BY_TIMEFRAME[item] for item in requested]


def terminal_no_launch(decision: str, extra: dict[str, Any] | None = None) -> dict[str, Any]:
    metrics = write_terminal_metrics(
        {
            "decision": decision,
            "provider_rows": read_provider_rows(),
            "downstream_allowed": False,
            "pre_bayes_allowed": False,
            "bbn_allowed": False,
            "catboost_allowed": False,
            "execution_tree_allowed": False,
            **(extra or {}),
        }
    )
    print(json.dumps(metrics, indent=2))
    return metrics


def main() -> int:
    global ROOT
    parser = argparse.ArgumentParser(description="Run or resume IBKR 6B BoE rate-differential London stop-run VWAP reclaim Gate 1.")
    parser.add_argument("--root", type=Path, default=ROOT, help="Run root; use /tmp for claim-local artifacts.")
    parser.add_argument("--resume-root", type=Path, help="Existing run root; run dispatch/rank only.")
    parser.add_argument("--timeframes", default=",".join(REQUIRED_TIMEFRAMES), help="Comma-separated subset of 1m,5m,15m,30m,1h,4h,1d.")
    parser.add_argument("--session-scope", default=SESSION_SCOPE)
    parser.add_argument("--launch-aq", action="store_true", help="After provider/material prep, launch AutoQuant batch/dispatch/rank when guards are clear.")
    args = parser.parse_args()
    if args.resume_root:
        ROOT = args.resume_root.resolve()
    else:
        ROOT = args.root.resolve()
    if args.session_scope != SESSION_SCOPE:
        raise SystemExit(f"unsupported session scope: {args.session_scope}")
    specs = selected_specs(args.timeframes)

    if args.resume_root:
        for sub in ["summaries", "checks", "command-output"]:
            (ROOT / sub).mkdir(parents=True, exist_ok=True)
        guard = run_claim_collision_audit()
        if not guard["pass"] or backend_busy():
            terminal_no_launch("backend_or_claim_busy_no_dispatch", {"claim_collision_guard": guard})
            return 0
        commands = [run_cmd("10_auto_quant_agent_material_dispatch", [ICT, "auto-quant-agent-material-dispatch", "--symbol", AQ_SYMBOL, "--state-dir", ROOT / "state"], timeout=1800)]
        rank = None
        if commands[-1]["exit"] == 0:
            rank = run_cmd("11_auto_quant_agent_material_rank", [ICT, "auto-quant-agent-material-rank", "--symbol", AQ_SYMBOL, "--state-dir", ROOT / "state"], timeout=360)
            commands.append(rank)
        print(json.dumps(summarize_rank_result(commands, rank), indent=2))
        return 0 if rank and rank["exit"] == 0 else 1

    for sub in ["data/provider/raw", "data/provider/normalized", "agent-material", "summaries", "checks", "command-output", "state", "scripts"]:
        (ROOT / sub).mkdir(parents=True, exist_ok=True)
    shutil.copy2(__file__, ROOT / "scripts" / Path(__file__).name)

    guard = run_claim_collision_audit()
    if not guard["pass"]:
        terminal_no_launch("launch_blocked_by_foreign_claim_or_runtime", {"claim_collision_guard": guard})
        return 0
    if backend_busy():
        terminal_no_launch("backend_busy_no_ibkr_fetch_or_aq_dispatch", {"claim_collision_guard": guard})
        return 0

    commands = [run_cmd("00_provider_status_ibkr", [ICT, "provider-status", "--provider", "ibkr", "--agent"], timeout=60)]
    provider_rows = []
    materials = []
    strategies = []
    for s_index, spec in enumerate(specs, start=1):
        compact_duration = spec.duration.replace(" ", "").lower()
        raw = ROOT / "data/provider/raw" / f"ibkr_6b_{CONTRACT.symbol.lower()}_{CONTRACT.last_trade_date}_{spec.timeframe}_{compact_duration}.csv"
        norm = ROOT / "data/provider/normalized" / raw.name
        name = f"{s_index:02d}_ibkr_fetch_6b_{spec.timeframe}_{compact_duration}"
        result = run_cmd(name, fetch_args(spec, raw, 910 + s_index), timeout=540)
        commands.append(result)
        rows = normalize(raw, norm)
        provider_rows.append(
            {
                "provider": "IBKR",
                "sec_type": "FUT",
                "symbol": CONTRACT.symbol,
                "display_symbol": CONTRACT.human_root,
                "product": CONTRACT.product,
                "exchange": CONTRACT.exchange,
                "last_trade_date": CONTRACT.last_trade_date,
                "timeframe": spec.timeframe,
                "bar_size": spec.bar_size,
                "duration": spec.duration,
                "role": spec.role,
                "rows": rows,
                "path": str(norm) if rows else "",
                "exit": result["exit"],
                "session_scope": SESSION_SCOPE,
                "rth_filter_applied": RTH_FILTER_APPLIED,
                "local_cache_replay": "false",
            }
        )
        if rows == 0:
            continue
        for variant, cfg in VARIANTS.items():
            klass = class_name(spec, variant)
            strategy_path = ROOT / "agent-material" / f"{klass}.py"
            strategy_path.write_text(strategy_source(klass, spec.timeframe, variant, cfg), encoding="utf-8")
            strategies.append(strategy_path)
            material_path, material = build_material_payload(spec, variant, strategy_path, norm, klass)
            material_path.write_text(json.dumps(material, indent=2) + "\n", encoding="utf-8")
            materials.append(material_path)

    if provider_rows:
        with (ROOT / "summaries/provider_provenance_matrix.csv").open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(provider_rows[0].keys()))
            writer.writeheader()
            writer.writerows(provider_rows)

    compile_result = run_cmd("08_strategy_py_compile", [PY, "-m", "py_compile", *strategies], timeout=180) if strategies else {"name": "08_strategy_py_compile", "exit": 1, "timed_out": False}
    commands.append(compile_result)
    if not args.launch_aq:
        metrics = summarize_rank_result(commands, None)
        metrics["decision"] = "provider_material_ready_no_aq_launch_requested"
        write_terminal_metrics(metrics)
        print(json.dumps(metrics, indent=2))
        return 0

    batch = dispatch = rank = None
    if materials and compile_result["exit"] == 0:
        guard = run_claim_collision_audit()
        if not guard["pass"] or backend_busy():
            terminal_no_launch("material_ready_but_backend_or_claim_busy_no_aq", {"claim_collision_guard": guard})
            return 0
        batch_args = [ICT, "auto-quant-agent-material-batch", "--symbol", AQ_SYMBOL, "--state-dir", ROOT / "state", "--max-parallel", "1"]
        if AQ_REPO.exists():
            batch_args += ["--repo-url", AQ_REPO]
        for material in materials:
            batch_args += ["--material", material]
        batch = run_cmd("09_auto_quant_agent_material_batch", batch_args, timeout=1800)
        commands.append(batch)
    if batch and batch["exit"] == 0:
        guard = run_claim_collision_audit()
        if not guard["pass"] or backend_busy():
            metrics = summarize_rank_result(commands, None)
            metrics["decision"] = "material_batch_done_backend_or_claim_busy_no_dispatch"
            metrics["claim_collision_guard"] = guard
            write_terminal_metrics(metrics)
            print(json.dumps(metrics, indent=2))
            return 0
        dispatch = run_cmd("10_auto_quant_agent_material_dispatch", [ICT, "auto-quant-agent-material-dispatch", "--symbol", AQ_SYMBOL, "--state-dir", ROOT / "state"], timeout=1800)
        commands.append(dispatch)
    if dispatch and dispatch["exit"] == 0:
        rank = run_cmd("11_auto_quant_agent_material_rank", [ICT, "auto-quant-agent-material-rank", "--symbol", AQ_SYMBOL, "--state-dir", ROOT / "state"], timeout=360)
        commands.append(rank)
    metrics = summarize_rank_result(commands, rank)
    print(json.dumps(metrics, indent=2))
    return 0 if rank and rank["exit"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
