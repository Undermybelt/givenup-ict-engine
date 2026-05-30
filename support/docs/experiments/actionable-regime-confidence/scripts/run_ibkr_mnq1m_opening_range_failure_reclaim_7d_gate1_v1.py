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
ROOT = BASE / "runs" / f"{STAMP}-codex-ibkr-mnq1m-opening-range-failure-reclaim-7d-gate1-v1"
SOURCE_CSV = Path("/tmp/ict-mnq-1m-7d.csv")
PY = Path("/Users/thrill3r/.venvs/ict-engine-provider-py313/bin/python")
if not PY.exists():
    PY = Path("python3")
ICT = REPO / ".local-artifacts/cargo-target/debug/ict-engine"
if not ICT.exists():
    ICT = REPO / "target/debug/ict-engine"
AQ_REPO = Path("/Users/thrill3r/Auto-Quant")

AQ_SYMBOL = "IBKR_MNQ1M_OPENING_RANGE_FAILURE_RECLAIM_7D_GATE1_V1"
FACTOR_ID = "ibkr_mnq1m_opening_range_failure_reclaim_7d_gate1_v1"
BRANCH_PATH = (
    "RangeReversion -> OpeningRangeFailure -> "
    f"OpeningRangeFailure -> {FACTOR_ID}"
)


@dataclass(frozen=True)
class Variant:
    name: str
    rvol_min: float
    reclaim_level: str
    max_or_width_atr: float
    min_pierce_atr: float
    max_pierce_atr: float
    stoploss: float
    roi: float
    trail: float
    offset: float


VARIANTS = [
    Variant("mid_reclaim_dense", 0.65, "mid", 4.40, 0.05, 1.20, -0.0060, 0.0032, 0.0010, 0.0036),
    Variant("mid_reclaim_balanced", 0.85, "mid", 3.60, 0.08, 1.00, -0.0070, 0.0040, 0.0013, 0.0045),
    Variant("vwap_reclaim_dense", 0.65, "vwap", 4.20, 0.04, 1.25, -0.0065, 0.0036, 0.0011, 0.0040),
    Variant("inside_close_quality", 1.00, "inside", 3.10, 0.10, 0.85, -0.0080, 0.0048, 0.0016, 0.0054),
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
    rows = []
    with src.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        headers = reader.fieldnames or []
        time_key = next((key for key in ("timestamp", "ts", "time", "datetime", "date") if key in headers), None)
        if not time_key:
            return 0
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
    dates: list[str] = []
    with path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            raw = (row.get("timestamp") or "").strip()
            if raw:
                dates.append(raw[:10].replace("-", ""))
    return f"{min(dates)}-{max(dates)}" if dates else ""


def class_name(variant: Variant) -> str:
    safe = "".join(part.title() for part in variant.name.split("_"))
    return f"IbkrMnqOpeningRangeFailureReclaim{safe}1MinV1"


def strategy_source(name: str, variant: Variant) -> str:
    tag = f"{FACTOR_ID}_{variant.name}"
    reclaim_expr = {
        "mid": '(dataframe["close"] > dataframe["or_mid"])',
        "vwap": '(dataframe["close"] > dataframe["session_vwap"])',
        "inside": '(dataframe["close"] > dataframe["or_low"]) & (dataframe["close"] < dataframe["or_high"])',
    }[variant.reclaim_level]
    return f'''from freqtrade.strategy import IStrategy
from pandas import DataFrame


class {name}(IStrategy):
    INTERFACE_VERSION = 3
    timeframe = "1m"
    can_short = False
    minimal_roi = {{"0": {variant.roi}}}
    stoploss = {variant.stoploss}
    trailing_stop = True
    trailing_stop_positive = {variant.trail}
    trailing_stop_positive_offset = {variant.offset}
    trailing_only_offset_is_reached = True
    process_only_new_candles = True
    use_exit_signal = True
    startup_candle_count = 220

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["ema21"] = dataframe["close"].ewm(span=21, adjust=False).mean()
        dataframe["ema55"] = dataframe["close"].ewm(span=55, adjust=False).mean()
        dataframe["vol60"] = dataframe["volume"].rolling(60).median()
        tr = DataFrame({{"hl": dataframe["high"] - dataframe["low"], "hc": (dataframe["high"] - dataframe["close"].shift()).abs(), "lc": (dataframe["low"] - dataframe["close"].shift()).abs()}}).max(axis=1)
        dataframe["atr14"] = tr.rolling(14).mean()
        dataframe["atr50"] = tr.rolling(50).mean()
        delta = dataframe["close"].diff()
        gain = delta.clip(lower=0).rolling(14).mean()
        loss = (-delta.clip(upper=0)).rolling(14).mean().replace(0, 0.000001)
        dataframe["rsi14"] = 100.0 - (100.0 / (1.0 + gain / loss))
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
        dataframe["failed_breakdown"] = dataframe["session_low"] < dataframe["or_low"] - dataframe["atr14"] * {variant.min_pierce_atr}
        dataframe["pierce_atr"] = (dataframe["or_low"] - dataframe["session_low"]) / dataframe["atr14"].replace(0, 0.000001)
        dataframe["rvol"] = dataframe["volume"] / dataframe["vol60"].replace(0, 1)
        dataframe["entry_window"] = (minute >= 14 * 60) & (minute < 19 * 60 + 15)
        dataframe["force_exit_window"] = minute >= 19 * 60 + 50
        dataframe["rv_expansion"] = dataframe["atr14"] / dataframe["atr50"].replace(0, 0.000001)
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["enter_long"] = 0
        dataframe["enter_tag"] = ""
        controlled_range = dataframe["or_width_atr"].between(0.35, {variant.max_or_width_atr})
        failed_then_reclaimed = dataframe["failed_breakdown"] & dataframe["pierce_atr"].between({variant.min_pierce_atr}, {variant.max_pierce_atr}) & {reclaim_expr}
        participation = dataframe["rvol"] >= {variant.rvol_min}
        volatility_ok = dataframe["rv_expansion"].between(0.60, 2.65)
        range_context = dataframe["rsi14"].between(28, 68) & (dataframe["close"] >= dataframe["ema21"] - dataframe["atr14"] * 0.85)
        signal = dataframe["entry_window"] & controlled_range & failed_then_reclaimed & participation & volatility_ok & range_context
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


def row_label(row: dict) -> str:
    package = str(row.get("package_id") or "")
    variant = next((v.name for v in VARIANTS if v.name.replace("_", "-") in package), "unknown")
    return f"MNQ/{variant}/1m"


def build_cost_summary(rank_rows: list[dict], *, representative_price: float) -> tuple[list[dict], list[str], bool]:
    summary = cost_model.rank_rows_real_fee_summary(
        rank_rows,
        symbol="MNQ",
        representative_price=representative_price,
        label_fn=row_label,
    )
    summary_rows = list(summary["rows"])
    branch_fields_preserved = bool(rank_rows) and all(row.get("branch_path") == BRANCH_PATH for row in summary_rows)
    return summary_rows, list(summary["survivors"]), branch_fields_preserved


def write_materials(data_path: Path) -> list[Path]:
    material_paths: list[Path] = []
    for variant in VARIANTS:
        klass = class_name(variant)
        strategy_path = ROOT / "agent-material" / f"{klass}.py"
        strategy_path.write_text(strategy_source(klass, variant), encoding="utf-8")
        material_path = ROOT / "agent-material" / f"ibkr_mnq_opening_range_failure_reclaim_{variant.name}_1m_7d_v1.material.json"
        payload = {
            "package_id": f"ibkr-mnq-opening-range-failure-reclaim-{variant.name.replace('_', '-')}-1m-7d-v1",
            "title": f"IBKR MNQ opening-range failure reclaim {variant.name} 1m 7D",
            "symbol": "MNQ",
            "timeframe": "1m",
            "timerange": timerange(data_path),
            "direction": "long",
            "data_path": str(data_path),
            "strategy_source_path": str(strategy_path),
            "strategy_class_name": klass,
            "strategy_brief": "Source-backed opening-range failure fade/reclaim on real IBKR MNQ 1m data; range-reversion root chosen after trend-continuation downstream showed range/transition PDA conflict.",
            "evaluation_priority": ["exact_1m_cost_density", "range_reversion_alignment", "execution_tree_pda_conflict_repair"],
            "consumer_evidence_profile": {
                "branch_path": BRANCH_PATH,
                "regime_profit_branch_path": BRANCH_PATH,
                "branch_id": FACTOR_ID,
                "market": "FUTURES",
                "product": "equity_index",
                "root_symbol": "MNQ",
                "root_timeframe": "1m",
                "main_regime": "RangeReversion",
                "sub_regime": "OpeningRangeFailure",
                "sub_sub_regime_or_profit_factor": "OpeningRangeFailure",
                "profit_factor_id": FACTOR_ID,
                "profit_factor": FACTOR_ID,
                "base_timeframe": "1m",
                "training_timeframe": "1m",
                "neutralization_timeframe": "15m/1h_context_from_downstream_when_earned",
                "provider": "IBKR",
                "provider_window": "7 D",
                "provider_provenance": "IBKR FUT MNQ 202606 1m 7 D source=/tmp/ict-mnq-1m-7d.csv same-session",
                "source_backed_family": "Opening-range failure fade/reclaim",
                "gate_id": "Gate1IbkrMnqOpeningRangeFailureReclaim1m7d",
                "promotion_allowed": False,
                "trade_usable": False,
                "update_goal": False,
            },
            "notes": ["source_backed=orb_failure_reclaim", "downstream_forbidden_until_cost_density_survives", "do_not_flatten_root_to_prior_orb_breakout"],
        }
        material_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        material_paths.append(material_path)
    return material_paths


def main() -> int:
    for sub in ["data/provider/raw", "data/provider/normalized", "agent-material", "summaries", "checks", "command-output", "state", "scripts"]:
        (ROOT / sub).mkdir(parents=True, exist_ok=True)
    shutil.copy2(__file__, ROOT / "scripts" / Path(__file__).name)
    commands = [run_cmd("00_provider_status_ibkr", [ICT, "provider-status", "--provider", "ibkr", "--agent"], timeout=60)]
    raw = ROOT / "data/provider/raw/ibkr_mnq_202606_1m_7d.csv"
    norm = ROOT / "data/provider/normalized/ibkr_mnq_202606_1m_7d.csv"
    if SOURCE_CSV.exists():
        shutil.copy2(SOURCE_CSV, raw)
    rows = normalize(raw, norm) if raw.exists() else 0
    provider_rows = [{
        "provider": "IBKR", "sec_type": "FUT", "symbol": "MNQ", "product": "equity_index",
        "exchange": "CME", "last_trade_date": "202606", "timeframe": "1m", "duration": "7 D",
        "rows": rows, "path": str(norm) if rows else "", "source_csv": str(SOURCE_CSV),
        "local_cache_replay": "false_fresh_ibkr_fetch_from_same_session",
    }]
    with (ROOT / "summaries/provider_provenance_matrix.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(provider_rows[0].keys()))
        writer.writeheader(); writer.writerows(provider_rows)
    if rows == 0:
        raise FileNotFoundError(SOURCE_CSV)

    write_materials(norm)
    strategy_paths = sorted((ROOT / "agent-material").glob("*.py"))

    commands.append(run_cmd("04_strategy_py_compile", [PY, "-m", "py_compile", *strategy_paths], timeout=120))
    if commands[-1]["exit"] == 0:
        args: list[object] = [ICT, "auto-quant-agent-material-batch", "--symbol", AQ_SYMBOL, "--state-dir", ROOT / "state", "--max-parallel", "1"]
        if AQ_REPO.exists():
            args += ["--repo-url", AQ_REPO]
        for material in sorted((ROOT / "agent-material").glob("*.material.json")):
            args += ["--material", material]
        commands.append(run_cmd("05_auto_quant_agent_material_batch", args, timeout=600))
    if commands[-1]["exit"] == 0:
        commands.append(run_cmd("06_auto_quant_agent_material_dispatch", [ICT, "auto-quant-agent-material-dispatch", "--symbol", AQ_SYMBOL, "--state-dir", ROOT / "state"], timeout=900))
    if commands[-1]["exit"] == 0:
        commands.append(run_cmd("07_auto_quant_agent_material_rank", [ICT, "auto-quant-agent-material-rank", "--symbol", AQ_SYMBOL, "--state-dir", ROOT / "state"], timeout=300))

    rank_rows = latest_rank_rows()
    representative_price = cost_model.representative_price_from_provider_rows(provider_rows)
    summary_rows, survivors_instrument_cost, branch_fields_preserved = build_cost_summary(
        rank_rows,
        representative_price=representative_price,
    )
    cost_packet = cost_model.cost_model_packet("MNQ", representative_price)
    cost_model.write_real_fee_rank_rows_csv(ROOT / "summaries/rank_rows.csv", summary_rows)

    downstream_allowed = branch_fields_preserved and bool(survivors_instrument_cost)
    decision = "gate1_ibkr_mnq1m_opening_range_failure_reclaim_downstream_allowed" if downstream_allowed else "drop_or_block_gate1_practical"
    metrics = {
        "run_root": str(ROOT),
        "decision": decision,
        "aq_symbol": AQ_SYMBOL,
        "branch_path": BRANCH_PATH,
        "provider_rows": rows,
        "command_exits": {item["name"]: item["exit"] for item in commands},
        "branch_fields_preserved": branch_fields_preserved,
        "rank_rows": len(summary_rows),
        "representative_price": representative_price,
        "cost_model": cost_packet,
        "promotion_cost_verified": bool(cost_packet.get("verified_for_promotion")),
        "exact_1m_instrument_cost_rows": summary_rows,
        "exact_1m_survivors_instrument_cost": survivors_instrument_cost,
        "downstream_allowed": downstream_allowed,
        "pre_bayes_allowed": downstream_allowed,
        "bbn_allowed": downstream_allowed,
        "catboost_allowed": downstream_allowed,
        "execution_tree_allowed": downstream_allowed,
        "promotion_allowed": False,
        "trade_usable": False,
        "update_goal": False,
        "rows": summary_rows,
    }
    (ROOT / "checks/terminal_metrics.json").write_text(json.dumps(metrics, indent=2) + "\n", encoding="utf-8")
    lines = cost_model.real_fee_rank_table_lines(
        decision=decision,
        title="Exact MNQ 1m opening-range failure reclaim rows:",
        rows=summary_rows,
        branch_ok=branch_fields_preserved,
        survivors=survivors_instrument_cost,
        downstream=downstream_allowed,
    )
    (ROOT / "summaries/terminal_decision_summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
