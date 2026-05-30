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
ROOT = BASE / "runs" / f"{STAMP}-codex-ibkr-mym1m-opening-range-failure-reclaim-7d-gate1-v1"
PY = Path("/Users/thrill3r/.venvs/ict-engine-provider-py313/bin/python")
if not PY.exists():
    PY = Path("python3")
FETCH = REPO / "support/scripts/auto_quant_external/fetch_external.py"
ICT = REPO / ".local-artifacts/cargo-target/debug/ict-engine"
if not ICT.exists():
    ICT = REPO / "target/debug/ict-engine"
AQ_REPO = Path("/Users/thrill3r/Auto-Quant")

AQ_SYMBOL = "IBKR_MYM1M_OPENING_RANGE_FAILURE_RECLAIM_7D_GATE1_V1"
FACTOR_ID = "ibkr_mym1m_opening_range_failure_reclaim_7d_gate1_v1"
BRANCH_PATH = (
    "RangeReversion -> OpeningRangeFailureReclaim -> "
    f"OpeningRangeFailureReclaim -> {FACTOR_ID}"
)


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
    Contract("MYM", "equity_index", "CBOT", "0.5", "202606"),
]

VARIANTS = [
    Variant("dense", 0.0014, -0.0035, 0.0006, 0.0014, 18, 0.05, 0.10, 0.38, 72),
    Variant("balanced", 0.0022, -0.0048, 0.0009, 0.0022, 24, 0.10, 0.18, 0.55, 68),
    Variant("quality", 0.0035, -0.0065, 0.0014, 0.0036, 36, 0.18, 0.28, 0.75, 64),
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
        "--duration", "7 D",
        "--what-to-show", "TRADES",
        "--host", "127.0.0.1",
        "--port", "4002",
        "--client-id", str(client_id),
        "--market-data-type", "3",
        "--output", output,
    ]


def class_name(contract: Contract, variant: Variant) -> str:
    return f"IbkrFut{contract.symbol}OpeningRangeFailureReclaim{variant.name.title()}1MinV1"


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
        dataframe["ema21"] = dataframe["close"].ewm(span=21, adjust=False).mean()
        dataframe["ema55"] = dataframe["close"].ewm(span=55, adjust=False).mean()
        tr = DataFrame({{"hl": dataframe["high"] - dataframe["low"], "hc": (dataframe["high"] - dataframe["close"].shift()).abs(), "lc": (dataframe["low"] - dataframe["close"].shift()).abs()}}).max(axis=1)
        dataframe["atr14"] = tr.rolling(14).mean()
        delta = dataframe["close"].diff()
        gain = delta.clip(lower=0).rolling(14).mean()
        loss = (-delta.clip(upper=0)).rolling(14).mean().replace(0, 0.000001)
        dataframe["rsi14"] = 100.0 - (100.0 / (1.0 + gain / loss))
        dataframe["vol30"] = dataframe["volume"].rolling(30).mean()
        dt = dataframe["date"]
        day_key = dt.dt.strftime("%Y-%m-%d")
        minute = dt.dt.hour * 60 + dt.dt.minute
        rth = (minute >= 13 * 60 + 30) & (minute < 20 * 60)
        opening = (minute >= 13 * 60 + 30) & (minute < 14 * 60)
        typical = (dataframe["high"] + dataframe["low"] + dataframe["close"]) / 3.0
        pv = (typical * dataframe["volume"]).where(rth)
        vv = dataframe["volume"].where(rth)
        dataframe["session_vwap"] = pv.groupby(day_key).cumsum() / vv.groupby(day_key).cumsum().replace(0, 1)
        dataframe["or_high"] = dataframe["high"].where(opening).groupby(day_key).transform("max").ffill()
        dataframe["or_low"] = dataframe["low"].where(opening).groupby(day_key).transform("min").ffill()
        dataframe["or_mid"] = (dataframe["or_high"] + dataframe["or_low"]) / 2.0
        dataframe["or_width_atr"] = (dataframe["or_high"] - dataframe["or_low"]) / dataframe["atr14"].replace(0, 0.000001)
        dataframe["session_low"] = dataframe["low"].where(rth).groupby(day_key).cummin()
        dataframe["failed_breakdown"] = dataframe["session_low"] < dataframe["or_low"] - dataframe["atr14"] * {variant.sweep_atr}
        dataframe["pierce_atr"] = (dataframe["or_low"] - dataframe["session_low"]) / dataframe["atr14"].replace(0, 0.000001)
        dataframe["rvol"] = dataframe["volume"] / dataframe["vol30"].replace(0, 1)
        dataframe["entry_window"] = (minute >= 14 * 60) & (minute < 19 * 60 + 15)
        dataframe["force_exit_window"] = minute >= 19 * 60 + 50
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["enter_long"] = 0
        dataframe["enter_tag"] = ""
        controlled_range = dataframe["or_width_atr"].between(0.35, {variant.sweep_lookback / 6.0:.4f})
        failed_then_reclaimed = dataframe["failed_breakdown"] & dataframe["pierce_atr"].between({variant.sweep_atr}, {variant.reclaim_atr}) & (dataframe["close"] > dataframe["or_mid"])
        participation = dataframe["rvol"] >= {variant.vol_mult}
        range_context = dataframe["rsi14"].between(28, {variant.max_rsi}) & (dataframe["close"] >= dataframe["ema55"] - dataframe["atr14"] * 1.20)
        signal = dataframe["entry_window"] & controlled_range & failed_then_reclaimed & participation & range_context
        dataframe.loc[signal, ["enter_long", "enter_tag"]] = (1, "{tag}")
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["exit_long"] = 0
        range_fail = dataframe["close"] < dataframe["or_low"] - dataframe["atr14"] * 0.20
        mean_revert_done = dataframe["close"] > dataframe["or_high"] - dataframe["atr14"] * 0.10
        dataframe.loc[dataframe["force_exit_window"] | range_fail | mean_revert_done | (dataframe["rsi14"] > 78), "exit_long"] = 1
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


def hard_gate_downstream_allowed(branch_fields_preserved: bool, survivors: list[str]) -> bool:
    return bool(branch_fields_preserved and survivors)


def row_label(row: dict) -> str:
    package = str(row.get("package_id") or "")
    symbol = next((s.upper() for s in ("mym",) if f"-{s}-" in package), "UNKNOWN")
    variant = next((v for v in ("dense", "balanced", "quality") if f"-{v}-" in package), "unknown")
    return f"{symbol}/{variant}/1m"


def build_cost_summary(rank_rows: list[dict], *, representative_price: float) -> tuple[list[dict], list[str], bool]:
    summary = cost_model.rank_rows_real_fee_summary(
        rank_rows,
        symbol="MYM",
        representative_price=representative_price,
        label_fn=row_label,
    )
    rows = list(summary["rows"])
    branch_ok = bool(rank_rows) and all(row.get("branch_path") == BRANCH_PATH for row in rows)
    return rows, list(summary["survivors"]), branch_ok


def write_materials(contract: Contract, data_path: Path) -> list[Path]:
    materials = []
    for variant in VARIANTS:
        klass = class_name(contract, variant)
        strategy = ROOT / "agent-material" / f"{klass}.py"
        strategy.write_text(strategy_source(klass, variant), encoding="utf-8")
        material = ROOT / "agent-material" / f"ibkr_mym_opening_range_failure_reclaim_{variant.name}_1m_7d_v1.material.json"
        payload = {
            "package_id": f"ibkr-mym-opening-range-failure-reclaim-{variant.name}-1m-7d-v1",
            "title": f"IBKR {contract.symbol} futures opening-range failure reclaim {variant.name} 1m 7D",
            "symbol": contract.symbol,
            "timeframe": "1m",
            "timerange": timerange(data_path),
            "direction": "long",
            "data_path": str(data_path),
            "strategy_source_path": str(strategy),
            "strategy_class_name": klass,
            "strategy_brief": "Micro Dow exact 1m opening-range breakdown failure reclaimed through the opening midpoint with RVOL guard.",
            "evaluation_priority": ["exact_1m_cost_density", "opening_range_failure_reclaim_family", "real_ibkr_futures_provider"],
            "consumer_evidence_profile": {
                "branch_path": BRANCH_PATH,
                "regime_profit_branch_path": BRANCH_PATH,
                "branch_id": FACTOR_ID,
                "market": "FUTURES",
                "product": contract.product,
                "root_symbol": contract.symbol,
                "root_timeframe": "1m",
                "main_regime": "RangeReversion",
                "sub_regime": "OpeningRangeFailureReclaim",
                "sub_sub_regime_or_profit_factor": "OpeningRangeFailureReclaim",
                "profit_factor_id": FACTOR_ID,
                "profit_factor": FACTOR_ID,
                "base_timeframe": "1m",
                "training_timeframe": "1m",
                "material_timeframe": "1m",
                "provider": "IBKR",
                "provider_window": "7 D",
                "provider_provenance": f"IBKR FUT {contract.symbol} {contract.last_trade_date} 1m 7 D",
                "asset_class": "futures",
                "sec_type": "FUT",
                "exchange": contract.exchange,
                "multiplier": contract.multiplier,
                "last_trade_date": contract.last_trade_date,
                "gate_id": "Gate1IbkrMymOpeningRangeFailureReclaim1m7d",
                "promotion_allowed": False,
                "trade_usable": False,
                "update_goal": False,
            },
            "notes": ["exact_1m_only=true", "local_cache_replay=false", "source_backed=opening_range_failure_reclaim", "downstream_forbidden_until_cost_density_survives=true"],
        }
        material.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        materials.append(material)
    return materials


def main() -> int:
    for sub in ["data/provider/raw", "data/provider/normalized", "agent-material", "summaries", "checks", "command-output", "state", "scripts"]:
        (ROOT / sub).mkdir(parents=True, exist_ok=True)
    shutil.copy2(__file__, ROOT / "scripts" / Path(__file__).name)
    commands = [run_cmd("00_provider_status_ibkr", [ICT, "provider-status", "--provider", "ibkr", "--agent"], timeout=60)]
    provider_rows = []
    strategies = []
    materials = []
    for index, contract in enumerate(CONTRACTS, start=1):
        raw = ROOT / "data/provider/raw" / f"ibkr_{contract.symbol.lower()}_{contract.last_trade_date}_1m_7d.csv"
        norm = ROOT / "data/provider/normalized" / raw.name
        fetch = run_cmd(f"{index:02d}_ibkr_fetch_{contract.symbol.lower()}_1m_7d", fetch_args(contract, raw, 870 + index), timeout=660)
        commands.append(fetch)
        rows = normalize(raw, norm)
        provider_rows.append({
            "provider": "IBKR", "sec_type": "FUT", "symbol": contract.symbol,
            "product": contract.product, "exchange": contract.exchange,
            "last_trade_date": contract.last_trade_date, "timeframe": "1m",
            "duration": "7 D", "rows": rows, "path": str(norm) if rows else "",
            "exit": fetch["exit"], "local_cache_replay": "false",
        })
        if rows == 0:
            continue
        materials.extend(write_materials(contract, norm))
        strategies.extend(sorted((ROOT / "agent-material").glob("*.py")))
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
    rank_rows = latest_rank_rows() if rank and rank["exit"] == 0 else []
    representative_price = cost_model.representative_price_from_provider_rows(provider_rows)
    cost_rows, survivors_instrument_cost, branch_ok = build_cost_summary(
        rank_rows,
        representative_price=representative_price,
    )
    cost_packet = cost_model.cost_model_packet("MYM", representative_price)
    branch_paths = sorted({str(row.get("branch_path") or "") for row in rank_rows})
    downstream = hard_gate_downstream_allowed(branch_ok, survivors_instrument_cost)
    decision = "gate1_ibkr_mym1m_opening_range_failure_downstream_allowed" if downstream else "drop_or_block_gate1_practical"
    metrics = {
        "run_root": str(ROOT),
        "factor_id": FACTOR_ID,
        "decision": decision,
        "provider_rows": provider_rows,
        "rank_rows": len(rank_rows),
        "rank_total_trade_count": sum(int(row.get("trade_count") or 0) for row in rank_rows),
        "representative_price": representative_price,
        "cost_model": cost_packet,
        "promotion_cost_verified": bool(cost_packet.get("verified_for_promotion")),
        "exact_1m_instrument_cost_rows": cost_rows,
        "exact_1m_survivors_instrument_cost": survivors_instrument_cost,
        "branch_paths": branch_paths,
        "branch_fields_preserved": branch_ok,
        "downstream_allowed": downstream,
        "pre_bayes_allowed": downstream,
        "bbn_allowed": downstream,
        "catboost_allowed": False,
        "execution_tree_allowed": False,
        "promotion_allowed": False,
        "trade_usable": False,
        "update_goal": False,
        "local_cache_replay": False,
        "command_exits": {cmd["name"]: cmd["exit"] for cmd in commands},
        "skill_update": "not_needed" if not downstream else "needed_after_downstream",
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
