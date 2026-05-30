#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import argparse
import shutil
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


REPO = Path("/Users/thrill3r/projects-ict-engine/ict-engine")
BASE = REPO / "support/docs/experiments/actionable-regime-confidence"
RESEARCH_HELPERS = REPO / "support/scripts/research"
if str(RESEARCH_HELPERS) not in sys.path:
    sys.path.insert(0, str(RESEARCH_HELPERS))

import instrument_cost_model as cost_model  # noqa: E402

STAMP = datetime.now(ZoneInfo("Asia/Shanghai")).strftime("%Y%m%dT%H%M%S+0800")
ROOT = BASE / "runs" / f"{STAMP}-codex-ibkr-futures-micro-trend-pullback-reclaim-1m-mtf-gate1-v1"
PY = Path("/Users/thrill3r/.venvs/ict-engine-provider-py313/bin/python")
if not PY.exists():
    PY = Path("python3")
FETCH = REPO / "support/scripts/auto_quant_external/fetch_external.py"
ICT = REPO / ".local-artifacts/cargo-target/debug/ict-engine"
if not ICT.exists():
    ICT = REPO / "target/debug/ict-engine"
AQ_REPO = Path("/Users/thrill3r/Auto-Quant")

AQ_SYMBOL = "IBKR_FUTURES_MICRO_TREND_PULLBACK_RECLAIM_1M_MTF_V1"
FACTOR_ID = "ibkr_futures_micro_trend_pullback_reclaim_gate1_v1"
BRANCH_PATH = "TrendExpansion -> MicroTrendPullbackReclaim -> ibkr_futures_micro_trend_pullback_reclaim_gate1_v1"
PARTS = [part.strip() for part in BRANCH_PATH.split(" -> ")]


def backend_busy() -> bool:
    proc = subprocess.run(["ps", "-axo", "command"], text=True, capture_output=True, timeout=20)
    for line in proc.stdout.splitlines():
        if AQ_SYMBOL in line or Path(__file__).name in line:
            continue
        if "/bin/zsh -lc while ps" in line or "while ps -axo command" in line:
            continue
        needles = (
            "/ict-engine auto-quant-agent-material-dispatch",
            "/ict-engine auto-quant-agent-material-rank",
            "run_tomac.py",
            "fetch_external.py ibkr-historical",
            "pandas_path_ranker_trainer.py",
            "run_ibkr_futures_index_precious_metals_opening_vwap_rvol_reclaim_1m_mtf_gate1_v1.py",
            "run_ibkr_futures_liquidity_sweep_vwap_reclaim_1m_gate1_v1.py",
        )
        if any(needle in line for needle in needles):
            return True
    return False


@dataclass(frozen=True)
class Contract:
    symbol: str
    product: str
    exchange: str
    multiplier: str
    last_trade_date: str


@dataclass(frozen=True)
class Spec:
    timeframe: str
    bar_size: str
    duration: str
    role: str


CONTRACTS = [
    Contract("MES", "equity_index", "CME", "5", "202606"),
    Contract("MNQ", "equity_index", "CME", "2", "202606"),
    Contract("MGC", "precious_metals", "COMEX", "10", "202606"),
]

SPECS = [
    Spec("1m", "1 min", "2 D", "exact_training_origin"),
    Spec("5m", "5 mins", "10 D", "small_cycle_context"),
    Spec("15m", "15 mins", "1 M", "small_cycle_sibling"),
    Spec("30m", "30 mins", "1 M", "neutralization_context"),
    Spec("1h", "1 hour", "1 M", "higher_timeframe_veto"),
    Spec("4h", "4 hours", "1 M", "attempt_if_provider_supported"),
    Spec("1d", "1 day", "6 M", "daily_context"),
]

VARIANTS = {
    "dense": {"roi": 0.0025, "stop": -0.0045, "trail": 0.0010, "off": 0.0032, "vol": 0.55, "rsi_lo": 38, "rsi_hi": 78, "max_ext": 2.6, "min_slope": -0.04},
    "balanced": {"roi": 0.0035, "stop": -0.0060, "trail": 0.0014, "off": 0.0046, "vol": 0.75, "rsi_lo": 42, "rsi_hi": 74, "max_ext": 2.0, "min_slope": 0.00},
    "quality": {"roi": 0.0050, "stop": -0.0080, "trail": 0.0020, "off": 0.0062, "vol": 1.00, "rsi_lo": 46, "rsi_hi": 70, "max_ext": 1.45, "min_slope": 0.03},
}


def run_cmd(name: str, argv: list[object], timeout: int = 300) -> dict:
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
    (ROOT / "command-output" / f"{name}.out").write_text(stdout, encoding="utf-8")
    (ROOT / "command-output" / f"{name}.err").write_text(stderr, encoding="utf-8")
    (ROOT / "checks" / f"{name}.exit").write_text(f"{rc}\n", encoding="utf-8")
    return {"name": name, "exit": rc, "timed_out": timed_out}


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
    dates = []
    with path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            raw = (row.get("timestamp") or "").strip()
            if raw:
                dates.append(raw[:10].replace("-", ""))
    return f"{min(dates)}-{max(dates)}" if dates else ""


def suffix(tf: str) -> str:
    return tf.replace("m", "Min").replace("h", "Hour").replace("d", "Day")


def class_name(contract: Contract, spec: Spec, variant: str) -> str:
    return f"IbkrFut{contract.symbol}MicroTrendPullbackReclaim{variant.title()}{suffix(spec.timeframe)}V1"


def fetch_args(contract: Contract, spec: Spec, output: Path, client_id: int) -> list[object]:
    return [
        PY,
        FETCH,
        "ibkr-historical",
        "--symbol",
        contract.symbol,
        "--sec-type",
        "FUT",
        "--exchange",
        contract.exchange,
        "--currency",
        "USD",
        "--last-trade-date",
        contract.last_trade_date,
        "--multiplier",
        contract.multiplier,
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
        "--market-data-type",
        "3",
        "--output",
        output,
    ]


def strategy_source(name: str, tf: str, variant: str, cfg: dict) -> str:
    tag = f"{FACTOR_ID}_{variant}_{tf}"
    return f'''from freqtrade.strategy import IStrategy
from pandas import DataFrame


class {name}(IStrategy):
    INTERFACE_VERSION = 3
    timeframe = "{tf}"
    can_short = False
    minimal_roi = {{"0": {cfg['roi']}}}
    stoploss = {cfg['stop']}
    trailing_stop = True
    trailing_stop_positive = {cfg['trail']}
    trailing_stop_positive_offset = {cfg['off']}
    trailing_only_offset_is_reached = True
    process_only_new_candles = True
    use_exit_signal = True
    startup_candle_count = 160

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["ema9"] = dataframe["close"].ewm(span=9, adjust=False).mean()
        dataframe["ema21"] = dataframe["close"].ewm(span=21, adjust=False).mean()
        dataframe["ema55"] = dataframe["close"].ewm(span=55, adjust=False).mean()
        tr = DataFrame({{"hl": dataframe["high"] - dataframe["low"], "hc": (dataframe["high"] - dataframe["close"].shift()).abs(), "lc": (dataframe["low"] - dataframe["close"].shift()).abs()}}).max(axis=1)
        dataframe["atr14"] = tr.rolling(14).mean()
        dataframe["atr50"] = tr.rolling(50).mean()
        delta = dataframe["close"].diff()
        gain = delta.clip(lower=0).rolling(14).mean()
        loss = (-delta.clip(upper=0)).rolling(14).mean().replace(0, 0.000001)
        dataframe["rsi14"] = 100.0 - (100.0 / (1.0 + gain / loss))
        dataframe["vol40"] = dataframe["volume"].rolling(40).mean()
        dt = dataframe["date"]
        day_key = dt.dt.strftime("%Y-%m-%d")
        minute = dt.dt.hour * 60 + dt.dt.minute
        liquid_window = ((minute >= 13 * 60 + 30) & (minute < 20 * 60)) | ((minute >= 0) & (minute < 2 * 60 + 30))
        typical = (dataframe["high"] + dataframe["low"] + dataframe["close"]) / 3.0
        pv = (typical * dataframe["volume"]).where(liquid_window)
        vv = dataframe["volume"].where(liquid_window)
        dataframe["session_vwap"] = pv.groupby(day_key).cumsum() / vv.groupby(day_key).cumsum().replace(0, 1)
        dataframe["liquid_window"] = liquid_window
        dataframe["entry_window"] = liquid_window
        dataframe["force_exit_window"] = (minute >= 20 * 60 + 30) & (minute < 21 * 60 + 30)
        dataframe["ema_slope"] = dataframe["ema21"] - dataframe["ema21"].shift(5)
        dataframe["vwap_distance_atr"] = (dataframe["close"] - dataframe["session_vwap"]) / dataframe["atr14"]
        dataframe["rv_expansion"] = dataframe["atr14"] / dataframe["atr50"]
        dataframe["micro_trend_pullback"] = (dataframe["close"] > dataframe["session_vwap"]) & (dataframe["close"].shift(1) <= dataframe["session_vwap"].shift(1) * 1.0004)
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["enter_long"] = 0
        dataframe["enter_tag"] = ""
        trend = (dataframe["ema9"] > dataframe["ema21"] - dataframe["atr14"] * 0.08) & (dataframe["ema21"] > dataframe["ema55"] - dataframe["atr14"] * 0.30)
        slope_ok = dataframe["ema_slope"].fillna(0) >= dataframe["atr14"] * {cfg['min_slope']}
        vol_ok = dataframe["volume"] >= dataframe["vol40"] * {cfg['vol']}
        rsi_ok = dataframe["rsi14"].between({cfg['rsi_lo']}, {cfg['rsi_hi']})
        extension_ok = dataframe["vwap_distance_atr"].between(-0.35, {cfg['max_ext']})
        volatility_ok = dataframe["rv_expansion"].between(0.55, 2.80)
        reclaim_or_hold = dataframe["micro_trend_pullback"] | ((dataframe["close"] > dataframe["session_vwap"]) & (dataframe["close"] > dataframe["ema9"]))
        signal = dataframe["entry_window"] & trend & slope_ok & vol_ok & rsi_ok & extension_ok & volatility_ok & reclaim_or_hold
        dataframe.loc[signal, ["enter_long", "enter_tag"]] = (1, "{tag}")
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["exit_long"] = 0
        fail = (dataframe["close"] < dataframe["ema21"] - dataframe["atr14"] * 0.25) | (dataframe["close"] < dataframe["session_vwap"] - dataframe["atr14"] * 0.55)
        dataframe.loc[dataframe["force_exit_window"] | fail | (dataframe["rsi14"] > 84), "exit_long"] = 1
        return dataframe
'''


def latest_rank_rows() -> list[dict]:
    files = sorted((ROOT / f"state/auto-quant/{AQ_SYMBOL}").glob("auto_quant_agent_material_rank.*.json"))
    if not files:
        return []
    return json.loads(files[-1].read_text(encoding="utf-8")).get("ranking", []) or []


def safe_float(value: object) -> float:
    try:
        return float(str(value))
    except Exception:
        return 0.0


def row_label(row: dict) -> str:
    package = str(row.get("package_id") or "")
    pieces = package.split("-")
    symbol = next((item.upper() for item in pieces if item in {"mes", "mnq", "mgc"}), "UNKNOWN")
    variant = next((item for item in pieces if item in VARIANTS), "unknown")
    timeframe = next((spec.timeframe for spec in SPECS if package.endswith(f"-{spec.timeframe}-v1")), str(row.get("timeframe") or "unknown"))
    return f"{symbol}/{variant}/{timeframe}"


def read_provider_rows() -> list[dict]:
    matrix = ROOT / "summaries/provider_provenance_matrix.csv"
    if not matrix.exists():
        return []
    with matrix.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def representative_prices_by_symbol(provider_rows: list[dict]) -> dict[str, float]:
    prices: dict[str, float] = {}
    for contract in CONTRACTS:
        symbol_rows = [row for row in provider_rows if row.get("symbol") == contract.symbol and row.get("path")]
        exact_rows = [row for row in symbol_rows if row.get("timeframe") == "1m"]
        try:
            prices[contract.symbol] = cost_model.representative_price_from_provider_rows(exact_rows or symbol_rows)
        except Exception:
            continue
    return prices


def build_instrument_cost_summary(rank_rows: list[dict], provider_rows: list[dict]) -> dict:
    prices = representative_prices_by_symbol(provider_rows)
    cost_models = {
        symbol: cost_model.cost_model_packet(symbol, price)
        for symbol, price in prices.items()
    }
    rows = []
    survivors = []
    for row in rank_rows:
        label = row_label(row)
        symbol = label.split("/", 1)[0]
        price = prices.get(symbol)
        packet = cost_models.get(symbol) or cost_model.cost_model_packet(symbol)
        profile = cost_model.futures_cost_profile(symbol)
        trades = int(row.get("trade_count") or 0)
        gross = safe_float(row.get("total_profit_pct"))
        net = None
        real_fee_round_turn_pct = None
        survives = False
        if price and profile and profile.verified_for_promotion:
            real_fee_round_turn_pct = profile.round_trip_fee_pct(price)
            net = round(gross - trades * real_fee_round_turn_pct, 6)
            survives = trades > 0 and net > 0.0
        record = {
            "label": label,
            "trade_count": trades,
            "raw_total_profit_pct": gross,
            "win_rate_pct": safe_float(row.get("win_rate_pct")),
            "sharpe": safe_float(row.get("sharpe")),
            "representative_price": price,
            "instrument_cost_total_profit_pct": net,
            "survives_instrument_cost": survives,
            "real_fee_round_turn_pct": real_fee_round_turn_pct,
            "cost_model_status": packet.get("cost_model_status") or packet.get("status"),
            "cost_profile_id": packet.get("cost_profile_id", "unknown"),
            "promotion_cost_verified": bool(packet.get("verified_for_promotion")),
        }
        rows.append(record)
        if survives:
            survivors.append(label)
    return {
        "rows": rows,
        "survivors": survivors,
        "representative_prices": prices,
        "cost_models": cost_models,
        "promotion_cost_verified": bool(cost_models) and all(
            bool(packet.get("verified_for_promotion")) for packet in cost_models.values()
        ),
    }


def hard_gate_downstream_allowed(branch_fields_preserved: bool, exact_1m_survivors: list[str]) -> bool:
    return bool(branch_fields_preserved and exact_1m_survivors)


def summarize_rank_result(commands: list[dict], rank: dict | None = None) -> dict:
    provider_rows = read_provider_rows()
    rank_rows = latest_rank_rows() if rank and rank["exit"] == 0 else []
    cost_summary = build_instrument_cost_summary(rank_rows, provider_rows)
    instrument_cost_rows = cost_summary["rows"]
    exact_1m = [row for row in instrument_cost_rows if row["label"].endswith("/1m")]
    exact_1m_survivors = [row["label"] for row in exact_1m if row["survives_instrument_cost"]]
    branch_paths = sorted({str(row.get("branch_path") or row.get("consumer_evidence_profile", {}).get("branch_path") or "") for row in rank_rows})
    branch_fields_preserved = bool(rank_rows) and all(path == BRANCH_PATH for path in branch_paths)
    covered = sorted({f"{row.get('symbol')}/{row.get('timeframe')}" for row in provider_rows if int(row.get("rows") or 0) > 0})
    missing = sorted({f"{row.get('symbol')}/{row.get('timeframe')}" for row in provider_rows if int(row.get("rows") or 0) == 0})
    downstream_allowed = hard_gate_downstream_allowed(branch_fields_preserved, exact_1m_survivors)
    decision = "gate1_ibkr_futures_exact_1m_downstream_allowed" if downstream_allowed else "drop_or_block_gate1_practical"
    metrics = {
        "run_root": str(ROOT),
        "factor_id": FACTOR_ID,
        "branch_path_template": BRANCH_PATH,
        "decision": decision,
        "provider_rows": provider_rows,
        "material_count": len(list((ROOT / "agent-material").glob("*.material.json"))),
        "rank_rows": len(rank_rows),
        "rank_total_trade_count": sum(int(row.get("trade_count") or 0) for row in rank_rows),
        "cost_gate_authority": "instrument_cost",
        "representative_prices": cost_summary["representative_prices"],
        "cost_models": cost_summary["cost_models"],
        "promotion_cost_verified": cost_summary["promotion_cost_verified"],
        "instrument_cost_rows": instrument_cost_rows,
        "exact_1m_survivors_instrument_cost": exact_1m_survivors,
        "branch_paths": branch_paths,
        "branch_fields_preserved": branch_fields_preserved,
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
        "skill_update": "not_needed",
    }
    (ROOT / "checks/terminal_metrics.json").write_text(json.dumps(metrics, indent=2) + "\n", encoding="utf-8")
    (ROOT / "summaries/terminal_decision_summary.md").write_text("# Terminal Decision Summary\n\n" + json.dumps(metrics, indent=2) + "\n", encoding="utf-8")
    return metrics


def resume_dispatch_rank() -> int:
    if backend_busy():
        print(json.dumps({"decision": "backend_busy_no_dispatch", "run_root": str(ROOT), "factor_id": FACTOR_ID}, indent=2))
        return 0
    commands = []
    dispatch = run_cmd("10_auto_quant_agent_material_dispatch", [ICT, "auto-quant-agent-material-dispatch", "--symbol", AQ_SYMBOL, "--state-dir", ROOT / "state"], timeout=1800)
    commands.append(dispatch)
    rank = None
    if dispatch["exit"] == 0:
        rank = run_cmd("11_auto_quant_agent_material_rank", [ICT, "auto-quant-agent-material-rank", "--symbol", AQ_SYMBOL, "--state-dir", ROOT / "state"], timeout=360)
        commands.append(rank)
    metrics = summarize_rank_result(commands, rank)
    print(json.dumps(metrics, indent=2))
    return 0 if rank and rank["exit"] == 0 else 1


def main() -> int:
    global ROOT
    parser = argparse.ArgumentParser(description="Run or resume IBKR futures Auto-Quant Gate 1.")
    parser.add_argument("--resume-root", type=Path, help="Existing run root with provider rows, materials, and batch state; run dispatch/rank only.")
    args = parser.parse_args()
    if args.resume_root:
        ROOT = args.resume_root.resolve()
        return resume_dispatch_rank()

    if backend_busy():
        for sub in ["summaries", "checks", "command-output", "scripts"]:
            (ROOT / sub).mkdir(parents=True, exist_ok=True)
        shutil.copy2(__file__, ROOT / "scripts" / Path(__file__).name)
        metrics = {
            "run_root": str(ROOT),
            "factor_id": FACTOR_ID,
            "branch_path_template": BRANCH_PATH,
            "decision": "backend_busy_no_ibkr_fetch_or_aq_dispatch",
            "provider_rows": [],
            "material_count": 0,
            "rank_rows": 0,
            "downstream_allowed": False,
            "pre_bayes_allowed": False,
            "bbn_allowed": False,
            "catboost_allowed": False,
            "execution_tree_allowed": False,
            "promotion_allowed": False,
            "trade_usable": False,
            "update_goal": False,
            "skill_update": "not_needed",
        }
        (ROOT / "checks/terminal_metrics.json").write_text(json.dumps(metrics, indent=2) + "\n", encoding="utf-8")
        (ROOT / "summaries/terminal_decision_summary.md").write_text("# Terminal Decision Summary\n\n" + json.dumps(metrics, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(metrics, indent=2))
        return 0

    for sub in ["data/provider/raw", "data/provider/normalized", "agent-material", "summaries", "checks", "command-output", "state", "scripts"]:
        (ROOT / sub).mkdir(parents=True, exist_ok=True)
    shutil.copy2(__file__, ROOT / "scripts" / Path(__file__).name)

    commands = [run_cmd("00_provider_status_ibkr", [ICT, "provider-status", "--provider", "ibkr", "--agent"], timeout=60)]
    provider_rows = []
    materials = []
    strategies = []

    for c_index, contract in enumerate(CONTRACTS, start=1):
        for s_index, spec in enumerate(SPECS, start=1):
            compact_duration = spec.duration.replace(" ", "").lower()
            raw = ROOT / "data/provider/raw" / f"ibkr_{contract.symbol.lower()}_{contract.last_trade_date}_{spec.timeframe}_{compact_duration}.csv"
            norm = ROOT / "data/provider/normalized" / raw.name
            name = f"{c_index:02d}{s_index:02d}_ibkr_fetch_{contract.symbol.lower()}_{spec.timeframe}_{compact_duration}"
            result = run_cmd(name, fetch_args(contract, spec, raw, 730 + c_index * 20 + s_index), timeout=540)
            commands.append(result)
            rows = normalize(raw, norm)
            provider_rows.append(
                {
                    "provider": "IBKR",
                    "sec_type": "FUT",
                    "symbol": contract.symbol,
                    "product": contract.product,
                    "exchange": contract.exchange,
                    "last_trade_date": contract.last_trade_date,
                    "timeframe": spec.timeframe,
                    "bar_size": spec.bar_size,
                    "duration": spec.duration,
                    "role": spec.role,
                    "rows": rows,
                    "path": str(norm) if rows else "",
                    "exit": result["exit"],
                    "local_cache_replay": "false",
                }
            )
            if rows == 0:
                continue
            for variant, cfg in VARIANTS.items():
                klass = class_name(contract, spec, variant)
                strategy_path = ROOT / "agent-material" / f"{klass}.py"
                strategy_path.write_text(strategy_source(klass, spec.timeframe, variant, cfg), encoding="utf-8")
                strategies.append(strategy_path)
                material_path = ROOT / "agent-material" / f"ibkr_futures_{contract.symbol.lower()}_micro_trend_pullback_reclaim_{variant}_{spec.timeframe}_v1.material.json"
                material = {
                    "package_id": f"ibkr-futures-{contract.symbol.lower()}-micro-trend-pullback-reclaim-{variant}-{spec.timeframe}-v1",
                    "title": f"IBKR {contract.symbol} futures micro-trend pullback reclaim {variant} {spec.timeframe}",
                    "symbol": contract.symbol,
                    "timeframe": spec.timeframe,
                    "timerange": timerange(norm),
                    "direction": "long",
                    "data_path": str(norm),
                    "strategy_source_path": str(strategy_path),
                    "strategy_class_name": klass,
                    "strategy_brief": "IBKR FUT 1m-root liquid-window micro-trend pullback reclaim with VWAP hold, EMA slope, RSI, participation, and cost-aware short-hold controls.",
                    "evaluation_priority": ["ibkr_native_futures_provider", "exact_1m_origin_density", "real_cost_survival", "mtf_ladder_resonance", "same_root_downstream_readiness"],
                    "consumer_evidence_profile": {
                        "branch_path": BRANCH_PATH,
                        "regime_profit_branch_path": BRANCH_PATH,
                        "branch_id": FACTOR_ID,
                        "market": "FUTURES",
                        "product": contract.product,
                        "root_symbol": contract.symbol,
                        "root_timeframe": "1m",
                        "main_regime": PARTS[0],
                        "sub_regime": PARTS[1],
                        "profit_factor": FACTOR_ID,
                        "base_timeframe": "1m",
                        "training_timeframe": "1m",
                        "material_timeframe": spec.timeframe,
                        "provider": "IBKR",
                        "provider_window": spec.duration,
                        "provider_provenance": f"IBKR FUT {contract.symbol} {contract.last_trade_date} {spec.timeframe} {spec.duration}",
                        "asset_class": "futures",
                        "sec_type": "FUT",
                        "exchange": contract.exchange,
                        "multiplier": contract.multiplier,
                        "last_trade_date": contract.last_trade_date,
                        "gate_id": "Gate1IbkrFuturesMicroTrendPullbackReclaim",
                        "promotion_allowed": False,
                        "trade_usable": False,
                        "update_goal": False,
                    },
                    "notes": ["ibkr_first=true", "local_cache_replay=false", "root_branch_excludes_market_product_symbol_timeframe=true", "pre_bayes_bbn_catboost_execution_tree_allowed=false_until_exact_1m_cost_density_passes"],
                }
                material_path.write_text(json.dumps(material, indent=2) + "\n", encoding="utf-8")
                materials.append(material_path)

    provider_matrix = ROOT / "summaries/provider_provenance_matrix.csv"
    if provider_rows:
        with provider_matrix.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(provider_rows[0].keys()))
            writer.writeheader()
            writer.writerows(provider_rows)

    compile_result = run_cmd("08_strategy_py_compile", [PY, "-m", "py_compile", *strategies], timeout=180) if strategies else {"name": "08_strategy_py_compile", "exit": 1, "timed_out": False}
    commands.append(compile_result)
    batch = dispatch = rank = None
    if materials and compile_result["exit"] == 0:
        args = [ICT, "auto-quant-agent-material-batch", "--symbol", AQ_SYMBOL, "--state-dir", ROOT / "state", "--max-parallel", "1"]
        if AQ_REPO.exists():
            args += ["--repo-url", AQ_REPO]
        for material in materials:
            args += ["--material", material]
        batch = run_cmd("09_auto_quant_agent_material_batch", args, timeout=1800)
        commands.append(batch)
    if batch and batch["exit"] == 0 and backend_busy():
        metrics = summarize_rank_result(commands, None)
        metrics["decision"] = "material_batch_done_backend_busy_no_dispatch"
        metrics["downstream_allowed"] = False
        metrics["pre_bayes_allowed"] = False
        metrics["bbn_allowed"] = False
        metrics["catboost_allowed"] = False
        metrics["execution_tree_allowed"] = False
        (ROOT / "checks/terminal_metrics.json").write_text(json.dumps(metrics, indent=2) + "\n", encoding="utf-8")
        (ROOT / "summaries/terminal_decision_summary.md").write_text("# Terminal Decision Summary\n\n" + json.dumps(metrics, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(metrics, indent=2))
        return 0
    if batch and batch["exit"] == 0:
        dispatch = run_cmd("10_auto_quant_agent_material_dispatch", [ICT, "auto-quant-agent-material-dispatch", "--symbol", AQ_SYMBOL, "--state-dir", ROOT / "state"], timeout=1800)
        commands.append(dispatch)
    if dispatch and dispatch["exit"] == 0:
        rank = run_cmd("11_auto_quant_agent_material_rank", [ICT, "auto-quant-agent-material-rank", "--symbol", AQ_SYMBOL, "--state-dir", ROOT / "state"], timeout=360)
        commands.append(rank)

    rank_rows = latest_rank_rows() if rank and rank["exit"] == 0 else []
    cost_summary = build_instrument_cost_summary(rank_rows, provider_rows)
    instrument_cost_rows = cost_summary["rows"]
    exact_1m = [row for row in instrument_cost_rows if row["label"].endswith("/1m")]
    exact_1m_survivors = [row["label"] for row in exact_1m if row["survives_instrument_cost"]]
    branch_paths = sorted({str(row.get("branch_path") or row.get("consumer_evidence_profile", {}).get("branch_path") or "") for row in rank_rows})
    branch_fields_preserved = bool(rank_rows) and all(path == BRANCH_PATH for path in branch_paths)
    covered = sorted({f"{row['symbol']}/{row['timeframe']}" for row in provider_rows if row["rows"] > 0})
    missing = sorted({f"{row['symbol']}/{row['timeframe']}" for row in provider_rows if row["rows"] == 0})
    downstream_allowed = hard_gate_downstream_allowed(branch_fields_preserved, exact_1m_survivors)
    decision = "gate1_ibkr_futures_exact_1m_downstream_allowed" if downstream_allowed else "drop_or_block_gate1_practical"
    metrics = {
        "run_root": str(ROOT),
        "factor_id": FACTOR_ID,
        "branch_path_template": BRANCH_PATH,
        "decision": decision,
        "provider_rows": provider_rows,
        "material_count": len(materials),
        "rank_rows": len(rank_rows),
        "rank_total_trade_count": sum(int(row.get("trade_count") or 0) for row in rank_rows),
        "cost_gate_authority": "instrument_cost",
        "representative_prices": cost_summary["representative_prices"],
        "cost_models": cost_summary["cost_models"],
        "promotion_cost_verified": cost_summary["promotion_cost_verified"],
        "instrument_cost_rows": instrument_cost_rows,
        "exact_1m_survivors_instrument_cost": exact_1m_survivors,
        "branch_paths": branch_paths,
        "branch_fields_preserved": branch_fields_preserved,
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
        "skill_update": "not_needed",
    }
    (ROOT / "checks/terminal_metrics.json").write_text(json.dumps(metrics, indent=2) + "\n", encoding="utf-8")
    (ROOT / "summaries/terminal_decision_summary.md").write_text("# Terminal Decision Summary\n\n" + json.dumps(metrics, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(metrics, indent=2))
    return 0 if rank and rank["exit"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
