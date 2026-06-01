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


REPO = Path("/Users/thrill3r/projects-ict-engine/ict-engine")
BASE = REPO / "support/docs/experiments/actionable-regime-confidence"
RESEARCH_HELPERS = REPO / "support/scripts/research"
if str(RESEARCH_HELPERS) not in sys.path:
    sys.path.insert(0, str(RESEARCH_HELPERS))

import instrument_cost_model as cost_model  # noqa: E402

STAMP = datetime.now(ZoneInfo("Asia/Shanghai")).strftime("%Y%m%dT%H%M%S+0800")
ROOT = BASE / "runs" / f"{STAMP}-codex-ibkr-mgc1m-rsi-vwap-washout-reclaim-gate1-v1"
PY = Path("/Users/thrill3r/.venvs/ict-engine-provider-py313/bin/python")
if not PY.exists():
    PY = Path("python3")
FETCH = REPO / "support/scripts/auto_quant_external/fetch_external.py"
ICT = REPO / ".local-artifacts/cargo-target/debug/ict-engine"
if not ICT.exists():
    ICT = REPO / "target/debug/ict-engine"
AQ_REPO = Path("/Users/thrill3r/Auto-Quant")

AQ_SYMBOL = "IBKR_MGC1M_RSI_VWAP_WASHOUT_RECLAIM_GATE1_V1"
FACTOR_ID = "ibkr_mgc1m_rsi_vwap_washout_reclaim_gate1_v1"
BRANCH_TEMPLATE = "RangeReversion -> RsiVwapWashoutReclaim -> ibkr_mgc1m_rsi_vwap_washout_reclaim_gate1_v1"


@dataclass(frozen=True)
class Contract:
    symbol: str
    product: str
    exchange: str
    multiplier: str
    last_trade_date: str


@dataclass(frozen=True)
class Variant:
    name: str
    roi: float
    stop: float
    trail: float
    offset: float
    sweep_lookback: int
    sweep_atr: float
    reclaim_atr: float
    vol_mult: float
    max_rsi: int


CONTRACTS = [
    Contract("MGC", "precious_metals", "COMEX", "10", "202606"),
]

VARIANTS = [
    Variant("dense", 0.0014, -0.0032, 0.0006, 0.0014, 20, 0.03, 0.10, 0.40, 70),
    Variant("balanced", 0.0020, -0.0042, 0.0008, 0.0020, 28, 0.06, 0.16, 0.55, 66),
    Variant("quality", 0.0028, -0.0055, 0.0011, 0.0029, 40, 0.10, 0.24, 0.70, 62),
]


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
        time_key = next((key for key in ("timestamp", "time", "datetime", "date", "ts") if key in headers), None)
        if not time_key:
            return 0
        rows = []
        for row in reader:
            if all(row.get(key) not in (None, "") for key in ("open", "high", "low", "close")):
                rows.append({
                    "timestamp": row.get(time_key, ""),
                    "open": row.get("open", ""),
                    "high": row.get("high", ""),
                    "low": row.get("low", ""),
                    "close": row.get("close", ""),
                    "volume": row.get("volume") or "0",
                })
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


def fetch_args(contract: Contract, output: Path, client_id: int) -> list[object]:
    return [
        PY, FETCH, "ibkr-historical",
        "--symbol", contract.symbol,
        "--sec-type", "FUT",
        "--exchange", contract.exchange,
        "--currency", "USD",
        "--last-trade-date", contract.last_trade_date,
        "--multiplier", contract.multiplier,
        "--bar-size", "1 min",
        "--duration", "2 D",
        "--what-to-show", "TRADES",
        "--host", "127.0.0.1",
        "--port", "4002",
        "--client-id", str(client_id),
        "--market-data-type", "3",
        "--output", output,
    ]


def class_name(contract: Contract, variant: Variant) -> str:
    safe_variant = "".join(part.title() for part in variant.name.split("_"))
    return f"IbkrFut{contract.symbol}RsiVwapWashoutReclaim{safe_variant}1MinV1"


def strategy_source(name: str, variant: Variant) -> str:
    tag = f"{FACTOR_ID}_{variant.name}"
    return f'''from freqtrade.strategy import IStrategy
from pandas import DataFrame


class {name}(IStrategy):
    INTERFACE_VERSION = 3
    timeframe = "1m"
    can_short = False
    minimal_roi = {{"0": {variant.roi}}}
    stoploss = {variant.stop}
    trailing_stop = True
    trailing_stop_positive = {variant.trail}
    trailing_stop_positive_offset = {variant.offset}
    trailing_only_offset_is_reached = True
    process_only_new_candles = True
    use_exit_signal = True
    startup_candle_count = 90

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["ema9"] = dataframe["close"].ewm(span=9, adjust=False).mean()
        dataframe["ema20"] = dataframe["close"].ewm(span=20, adjust=False).mean()
        dataframe["ema55"] = dataframe["close"].ewm(span=55, adjust=False).mean()
        tr = DataFrame({{"hl": dataframe["high"] - dataframe["low"], "hc": (dataframe["high"] - dataframe["close"].shift()).abs(), "lc": (dataframe["low"] - dataframe["close"].shift()).abs()}}).max(axis=1)
        dataframe["atr14"] = tr.rolling(14).mean()
        delta = dataframe["close"].diff()
        gain = delta.clip(lower=0).rolling(14).mean()
        loss = (-delta.clip(upper=0)).rolling(14).mean().replace(0, 0.000001)
        dataframe["rsi14"] = 100.0 - (100.0 / (1.0 + gain / loss))
        gain2 = delta.clip(lower=0).rolling(2).mean()
        loss2 = (-delta.clip(upper=0)).rolling(2).mean().replace(0, 0.000001)
        dataframe["rsi2"] = 100.0 - (100.0 / (1.0 + gain2 / loss2))
        dataframe["vol30"] = dataframe["volume"].rolling(30).mean()
        dt = dataframe["date"]
        day_key = dt.dt.strftime("%Y-%m-%d")
        minute = dt.dt.hour * 60 + dt.dt.minute
        liquid_window = ((minute >= 13 * 60 + 35) & (minute < 20 * 60 + 45)) | ((minute >= 0) & (minute < 2 * 60))
        typical = (dataframe["high"] + dataframe["low"] + dataframe["close"]) / 3.0
        pv = (typical * dataframe["volume"]).where(liquid_window)
        vv = dataframe["volume"].where(liquid_window)
        dataframe["session_vwap"] = pv.groupby(day_key).cumsum() / vv.groupby(day_key).cumsum().replace(0, 1)
        dataframe["entry_window"] = liquid_window
        dataframe["force_exit_window"] = (minute >= 20 * 60 + 45) & (minute < 21 * 60 + 45)
        prior_low = dataframe["low"].rolling({variant.sweep_lookback}).min().shift(1)
        band_mid = dataframe["close"].rolling(36).mean()
        band_std = dataframe["close"].rolling(36).std()
        dataframe["lower_band"] = band_mid - band_std * 1.35
        dataframe["sweep_low"] = dataframe["low"] <= prior_low - dataframe["atr14"] * {variant.sweep_atr}
        dataframe["lower_wick"] = (dataframe[["open", "close"]].min(axis=1) - dataframe["low"]) / dataframe["atr14"]
        dataframe["washout"] = dataframe["sweep_low"] | (dataframe["close"] < dataframe["lower_band"]) | (dataframe["rsi2"] < 18)
        dataframe["recent_washout"] = dataframe["washout"].rolling(6).max().fillna(0) > 0
        dataframe["vwap_reclaim"] = (dataframe["close"] > dataframe["session_vwap"] - dataframe["atr14"] * {variant.reclaim_atr}) | ((dataframe["close"] > dataframe["ema20"]) & (dataframe["close"].shift(1) <= dataframe["ema20"].shift(1)))
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["enter_long"] = 0
        dataframe["enter_tag"] = ""
        trend_guard = dataframe["close"] > dataframe["ema55"] - dataframe["atr14"] * 1.60
        participation = dataframe["volume"] >= dataframe["vol30"] * {variant.vol_mult}
        reset = dataframe["rsi14"].between(22, {variant.max_rsi})
        wick_or_washout = dataframe["recent_washout"] | (dataframe["lower_wick"] > 0.35)
        signal = dataframe["entry_window"] & trend_guard & participation & reset & wick_or_washout & dataframe["vwap_reclaim"]
        dataframe.loc[signal, ["enter_long", "enter_tag"]] = (1, "{tag}")
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["exit_long"] = 0
        failed = dataframe["close"] < dataframe["low"].rolling(8).min().shift(1)
        stretched = dataframe["rsi2"] > 88
        dataframe.loc[dataframe["force_exit_window"] | failed | stretched, "exit_long"] = 1
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
    symbol = next((s.upper() for s in ("mgc",) if f"-{s}-" in package), "UNKNOWN")
    variant = next((v for v in ("dense", "balanced", "quality") if f"-{v}-" in package), "unknown")
    return f"{symbol}/{variant}/1m"


def hard_gate_downstream_allowed(branch_fields_preserved: bool, survivors: list[str]) -> bool:
    return bool(branch_fields_preserved and survivors)


def main() -> int:
    for sub in ["data/provider/raw", "data/provider/normalized", "agent-material", "summaries", "checks", "command-output", "state", "scripts"]:
        (ROOT / sub).mkdir(parents=True, exist_ok=True)
    shutil.copy2(__file__, ROOT / "scripts" / Path(__file__).name)
    commands = [run_cmd("00_provider_status_ibkr", [ICT, "provider-status", "--provider", "ibkr", "--agent"], timeout=60)]
    provider_rows = []
    strategies = []
    materials = []
    for index, contract in enumerate(CONTRACTS, start=1):
        raw = ROOT / "data/provider/raw" / f"ibkr_{contract.symbol.lower()}_{contract.last_trade_date}_1m_2d.csv"
        norm = ROOT / "data/provider/normalized" / raw.name
        fetch = run_cmd(f"{index:02d}_ibkr_fetch_{contract.symbol.lower()}_1m_2d", fetch_args(contract, raw, 810 + index), timeout=540)
        commands.append(fetch)
        rows = normalize(raw, norm)
        provider_rows.append({
            "provider": "IBKR", "sec_type": "FUT", "symbol": contract.symbol,
            "product": contract.product, "exchange": contract.exchange,
            "last_trade_date": contract.last_trade_date, "timeframe": "1m",
            "duration": "2 D", "rows": rows, "path": str(norm) if rows else "",
            "exit": fetch["exit"], "local_cache_replay": "false",
        })
        if rows == 0:
            continue
        for variant in VARIANTS:
            klass = class_name(contract, variant)
            strategy = ROOT / "agent-material" / f"{klass}.py"
            strategy.write_text(strategy_source(klass, variant), encoding="utf-8")
            strategies.append(strategy)
            branch = BRANCH_TEMPLATE
            material = ROOT / "agent-material" / f"ibkr_{contract.symbol.lower()}_rsi_vwap_washout_reclaim_{variant.name}_1m_v1.material.json"
            payload = {
                "package_id": f"ibkr-{contract.symbol.lower()}-rsi-vwap-washout-reclaim-{variant.name}-1m-v1",
                "title": f"IBKR {contract.symbol} futures RSI/VWAP washout reclaim {variant.name} 1m",
                "symbol": contract.symbol,
                "timeframe": "1m",
                "timerange": timerange(norm),
                "direction": "long",
                "data_path": str(norm),
                "strategy_source_path": str(strategy),
                "strategy_class_name": klass,
                "strategy_brief": "MGC precious-metals exact 1m RSI2/lower-band washout reclaim back toward session VWAP or EMA20 with participation and ATR-risk guards.",
                "evaluation_priority": ["exact_1m_cost_density", "precious_metals_specific_root", "real_ibkr_futures_provider"],
                "consumer_evidence_profile": {
                    "branch_path": branch,
                    "regime_profit_branch_path": branch,
                    "branch_id": FACTOR_ID,
                    "market": "FUTURES",
                    "product": contract.product,
                    "root_symbol": contract.symbol,
                    "root_timeframe": "1m",
                    "main_regime": "RangeReversion",
                    "sub_regime": "RsiVwapWashoutReclaim",
                    "profit_factor": FACTOR_ID,
                    "base_timeframe": "1m",
                    "training_timeframe": "1m",
                    "material_timeframe": "1m",
                    "provider": "IBKR",
                    "provider_window": "2 D",
                    "provider_provenance": f"IBKR FUT {contract.symbol} {contract.last_trade_date} 1m 2 D",
                    "asset_class": "futures",
                    "sec_type": "FUT",
                    "exchange": contract.exchange,
                    "multiplier": contract.multiplier,
                    "last_trade_date": contract.last_trade_date,
                    "gate_id": "Gate1IbkrMgcRsiVwapWashoutReclaim1m",
                    "promotion_allowed": False,
                    "trade_usable": False,
                    "update_goal": False,
                },
                "notes": ["exact_1m_only=true", "local_cache_replay=false", "precious_metals_specific_root=true", "downstream_forbidden_until_cost_density_survives=true"],
            }
            material.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
            materials.append(material)
    if provider_rows:
        with (ROOT / "summaries/provider_provenance_matrix.csv").open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(provider_rows[0].keys()))
            writer.writeheader()
            writer.writerows(provider_rows)
    compile_result = run_cmd("04_strategy_py_compile", [PY, "-m", "py_compile", *strategies], timeout=120) if strategies else {"name": "04_strategy_py_compile", "exit": 1}
    commands.append(compile_result)
    batch = dispatch = rank = None
    if materials and compile_result["exit"] == 0:
        args = [ICT, "auto-quant-agent-material-batch", "--symbol", AQ_SYMBOL, "--state-dir", ROOT / "state", "--max-parallel", "1"]
        if AQ_REPO.exists():
            args += ["--repo-url", AQ_REPO]
        for material in materials:
            args += ["--material", material]
        batch = run_cmd("05_auto_quant_agent_material_batch", args, timeout=900)
        commands.append(batch)
    if batch and batch["exit"] == 0:
        dispatch = run_cmd("06_auto_quant_agent_material_dispatch", [ICT, "auto-quant-agent-material-dispatch", "--symbol", AQ_SYMBOL, "--state-dir", ROOT / "state"], timeout=1200)
        commands.append(dispatch)
    if dispatch and dispatch["exit"] == 0:
        rank = run_cmd("07_auto_quant_agent_material_rank", [ICT, "auto-quant-agent-material-rank", "--symbol", AQ_SYMBOL, "--state-dir", ROOT / "state"], timeout=180)
        commands.append(rank)
    rank_rows = latest_rank_rows() if commands[-1]["name"] == "03_auto_quant_agent_material_rank" and commands[-1]["exit"] == 0 else []
    representative_price = cost_model.representative_price_from_provider_rows(provider_rows)
    cost_summary = cost_model.rank_rows_real_fee_summary(
        rank_rows,
        symbol=ROOT_SYMBOL,
        representative_price=representative_price,
        label_fn=label_for,
    )
    cost_rows = cost_summary["rows"]
    survivors_instrument_cost = cost_summary["survivors"]
    branch_paths = sorted({str(row.get("branch_path") or "") for row in rank_rows})
    branch_ok = bool(rank_rows) and branch_paths == [BRANCH_PATH]
    downstream = hard_gate_downstream_allowed(branch_ok, survivors_instrument_cost)
    decision = "gate1_ibkr_mgc1m_rsi_vwap_washout_reclaim_downstream_allowed" if downstream else "drop_or_block_gate1_practical"
    metrics = {
        "run_root": str(ROOT), "factor_id": FACTOR_ID, "branch_path": BRANCH_PATH,
        "decision": decision, "provider_rows": provider_rows, "rank_rows": len(rank_rows),
        "rank_total_trade_count": sum(int(row.get("trade_count") or 0) for row in rank_rows),
        "representative_price": representative_price,
        "cost_model": cost_summary["cost_model"],
        "promotion_cost_verified": cost_summary["promotion_cost_verified"],
        "exact_1m_instrument_cost_rows": cost_rows,
        "exact_1m_survivors_instrument_cost": survivors_instrument_cost,
        "branch_paths": branch_paths,
        "branch_fields_preserved": branch_ok, "downstream_allowed": downstream,
        "pre_bayes_allowed": downstream, "bbn_allowed": downstream, "catboost_allowed": False,
        "execution_tree_allowed": False, "promotion_allowed": False, "trade_usable": False,
        "update_goal": False, "local_cache_replay": False,
        "command_exits": {cmd["name"]: cmd["exit"] for cmd in commands},
        "skill_update": "needed_after_downstream" if downstream else "not_needed",
    }
    (ROOT / "checks/terminal_metrics.json").write_text(json.dumps(metrics, indent=2) + "\n", encoding="utf-8")
    cost_model.write_real_fee_rank_rows_csv(ROOT / "summaries/rank_rows.csv", cost_rows)
    lines = cost_model.real_fee_rank_table_lines(
        decision=decision,
        title="Exact 1m rows:",
        rows=cost_rows,
        branch_ok=branch_ok,
        survivors=survivors_instrument_cost,
        downstream=downstream,
    )
    (ROOT / "summaries/terminal_decision_summary.md").write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps(metrics, indent=2))
    return 0 if rank and rank["exit"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
