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
ROOT = BASE / "runs" / f"{STAMP}-codex-ibkr-mgc1m-floor-pivot-cpr-reclaim-7d-gate1-v1"
SOURCE_ROOT = BASE / "runs/20260519T232924+0800-codex-ibkr-mgc1m-opening-vwap-rvol-reclaim-7d-gate1-v1"
SOURCE_DATA = SOURCE_ROOT / "data/provider/normalized/ibkr_mgc_202606_1m_7d.csv"
PY = Path("/Users/thrill3r/.venvs/ict-engine-provider-py313/bin/python")
if not PY.exists():
    PY = Path("python3")
ICT = REPO / ".local-artifacts/cargo-target/debug/ict-engine"
if not ICT.exists():
    ICT = REPO / "target/debug/ict-engine"
AQ_REPO = Path("/Users/thrill3r/Auto-Quant")

AQ_SYMBOL = "IBKR_MGC1M_FLOOR_PIVOT_CPR_RECLAIM_7D_GATE1_V1"
FACTOR_ID = "ibkr_mgc1m_floor_pivot_cpr_reclaim_7d_gate1_v1"
BRANCH_PATH = "RangeReversion -> FloorPivotCprReclaim -> ibkr_mgc1m_floor_pivot_cpr_reclaim_7d_gate1_v1"


@dataclass(frozen=True)
class Variant:
    name: str
    mode: str
    pivot_band_atr: float
    rvol_min: float
    wick_min: float
    cpr_width_max: float
    roi: float
    stoploss: float
    trail: float
    offset: float


VARIANTS = [
    Variant("pivot_reclaim_dense", "long", 0.18, 0.30, 0.06, 1.75, 0.0018, -0.0048, 0.0007, 0.0019),
    Variant("pivot_reclaim_balanced", "long", 0.12, 0.42, 0.12, 1.35, 0.0028, -0.0062, 0.0010, 0.0029),
    Variant("r1_reject_short", "short", 0.16, 0.36, 0.10, 1.55, 0.0024, -0.0058, 0.0009, 0.0026),
    Variant("cpr_breakout_long", "long_break", 0.10, 0.55, 0.04, 1.00, 0.0036, -0.0072, 0.0013, 0.0038),
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


def timerange(path: Path) -> str:
    dates: list[str] = []
    with path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            raw = (row.get("timestamp") or "").strip()
            if raw:
                dates.append(raw[:10].replace("-", ""))
    return f"{min(dates)}-{max(dates)}" if dates else ""


def row_count(path: Path) -> int:
    with path.open(newline="", encoding="utf-8") as handle:
        return sum(1 for _ in csv.DictReader(handle))


def class_name(variant: Variant) -> str:
    safe = "".join(part.title() for part in variant.name.split("_"))
    return f"IbkrMgcFloorPivotCprReclaim{safe}1MinV1"


def strategy_source(name: str, variant: Variant) -> str:
    tag = f"{FACTOR_ID}_{variant.name}"
    can_short = "True" if variant.mode == "short" else "False"
    if variant.mode == "short":
        entry = f'''(
            (dataframe["high"].rolling(6).max() >= dataframe["r1"] - dataframe["atr14"] * {variant.pivot_band_atr})
            & (dataframe["close"] < dataframe[["r1", "session_vwap", "ema21"]].min(axis=1))
            & (dataframe["upper_wick_atr"] >= {variant.wick_min})
        )'''
        side = "short"
    elif variant.mode == "long_break":
        entry = f'''(
            (dataframe["cpr_width_atr"] <= {variant.cpr_width_max})
            & (dataframe["close"] > dataframe[["tc", "session_vwap", "ema21"]].max(axis=1))
            & (dataframe["close"].shift(1) <= dataframe["tc"].shift(1) + dataframe["atr14"].shift(1) * {variant.pivot_band_atr})
        )'''
        side = "long"
    else:
        entry = f'''(
            (dataframe["low"].rolling(6).min() <= dataframe["pivot"] + dataframe["atr14"] * {variant.pivot_band_atr})
            & (dataframe["close"] > dataframe[["pivot", "session_vwap"]].max(axis=1))
            & (dataframe["lower_wick_atr"] >= {variant.wick_min})
            & (dataframe["cpr_width_atr"] <= {variant.cpr_width_max})
        )'''
        side = "long"
    long_set = f'dataframe.loc[signal, ["enter_long", "enter_tag"]] = (1, "{tag}")' if side == "long" else ""
    short_set = f'dataframe.loc[signal, ["enter_short", "enter_tag"]] = (1, "{tag}")' if side == "short" else ""
    return f'''from freqtrade.strategy import IStrategy
from pandas import DataFrame


class {name}(IStrategy):
    INTERFACE_VERSION = 3
    timeframe = "1m"
    can_short = {can_short}
    minimal_roi = {{"0": {variant.roi}}}
    stoploss = {variant.stoploss}
    trailing_stop = True
    trailing_stop_positive = {variant.trail}
    trailing_stop_positive_offset = {variant.offset}
    trailing_only_offset_is_reached = True
    process_only_new_candles = True
    use_exit_signal = True
    startup_candle_count = 240

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        high = dataframe["high"]
        low = dataframe["low"]
        close = dataframe["close"]
        volume = dataframe["volume"]
        dataframe["ema21"] = close.ewm(span=21, adjust=False).mean()
        dataframe["ema89"] = close.ewm(span=89, adjust=False).mean()
        tr = DataFrame({{"hl": high - low, "hc": (high - close.shift()).abs(), "lc": (low - close.shift()).abs()}}).max(axis=1)
        dataframe["atr14"] = tr.rolling(14).mean()
        day_key = dataframe["date"].dt.strftime("%Y-%m-%d")
        prev_high = high.groupby(day_key).transform("max").shift(1).groupby(day_key).ffill()
        prev_low = low.groupby(day_key).transform("min").shift(1).groupby(day_key).ffill()
        prev_close = close.groupby(day_key).transform("last").shift(1).groupby(day_key).ffill()
        dataframe["pivot"] = (prev_high + prev_low + prev_close) / 3.0
        dataframe["bc"] = (prev_high + prev_low) / 2.0
        dataframe["tc"] = dataframe["pivot"] * 2.0 - dataframe["bc"]
        dataframe["r1"] = dataframe["pivot"] * 2.0 - prev_low
        dataframe["s1"] = dataframe["pivot"] * 2.0 - prev_high
        dataframe["cpr_width_atr"] = (dataframe["tc"] - dataframe["bc"]).abs() / dataframe["atr14"].replace(0, 1)
        minute = dataframe["date"].dt.hour * 60 + dataframe["date"].dt.minute
        liquid_window = ((minute >= 13 * 60 + 35) & (minute <= 20 * 60 + 40)) | ((minute >= 0) & (minute <= 2 * 60 + 20))
        typical = (high + low + close) / 3.0
        dataframe["session_vwap"] = (typical * volume).where(liquid_window).groupby(day_key).cumsum() / volume.where(liquid_window).groupby(day_key).cumsum().replace(0, 1)
        dataframe["vol80"] = volume.rolling(80).mean()
        dataframe["rvol"] = volume / dataframe["vol80"].replace(0, 1)
        dataframe["lower_wick_atr"] = (dataframe[["open", "close"]].min(axis=1) - low) / dataframe["atr14"].replace(0, 1)
        dataframe["upper_wick_atr"] = (high - dataframe[["open", "close"]].max(axis=1)) / dataframe["atr14"].replace(0, 1)
        dataframe["entry_window"] = liquid_window
        dataframe["force_exit_window"] = (minute >= 20 * 60 + 50) & (minute < 21 * 60 + 55)
        dataframe["trend_guard"] = close > dataframe["ema89"] - dataframe["atr14"] * 1.10
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["enter_long"] = 0
        dataframe["enter_short"] = 0
        dataframe["enter_tag"] = ""
        setup = {entry}
        signal = dataframe["entry_window"] & setup & dataframe["trend_guard"] & (dataframe["rvol"] >= {variant.rvol_min}) & dataframe["atr14"].notna()
        {long_set}
        {short_set}
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["exit_long"] = 0
        dataframe["exit_short"] = 0
        dataframe.loc[dataframe["force_exit_window"] | (dataframe["close"] < dataframe["pivot"] - dataframe["atr14"] * 0.65), "exit_long"] = 1
        dataframe.loc[dataframe["force_exit_window"] | (dataframe["close"] > dataframe["r1"] + dataframe["atr14"] * 0.45), "exit_short"] = 1
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


def label_for(row: dict) -> str:
    package = str(row.get("package_id") or "")
    variant = next((item.name for item in VARIANTS if item.name.replace("_", "-") in package), "unknown")
    return f"MGC/{variant}/1m"


def write_materials(data_path: Path) -> list[Path]:
    materials: list[Path] = []
    for variant in VARIANTS:
        klass = class_name(variant)
        strategy = ROOT / "agent-material" / f"{klass}.py"
        strategy.write_text(strategy_source(klass, variant), encoding="utf-8")
        material = ROOT / "agent-material" / f"ibkr_mgc_floor_pivot_cpr_reclaim_{variant.name}_1m_7d_v1.material.json"
        payload = {
            "package_id": f"ibkr-mgc-floor-pivot-cpr-reclaim-{variant.name.replace('_', '-')}-1m-7d-v1",
            "title": f"IBKR MGC floor pivot CPR reclaim {variant.name} 1m 7D",
            "symbol": "MGC",
            "timeframe": "1m",
            "timerange": timerange(data_path),
            "direction": "short" if variant.mode == "short" else "long",
            "data_path": str(data_path),
            "strategy_source_path": str(strategy),
            "strategy_class_name": klass,
            "strategy_brief": "Classic floor-trader pivot / central pivot range reclaim-or-reject on MGC 1m real IBKR futures data.",
            "evaluation_priority": ["public_family_diversity", "exact_1m_cost_density", "precious_metals_provider_parity"],
            "consumer_evidence_profile": {
                "branch_path": BRANCH_PATH,
                "regime_profit_branch_path": BRANCH_PATH,
                "branch_id": FACTOR_ID,
                "market": "FUTURES",
                "product": "precious_metals",
                "root_symbol": "MGC",
                "root_timeframe": "1m",
                "main_regime": "RangeReversion",
                "sub_regime": "FloorPivotCprReclaim",
                "sub_sub_regime_or_profit_factor": FACTOR_ID,
                "profit_factor": FACTOR_ID,
                "base_timeframe": "1m",
                "training_timeframe": "1m",
                "material_timeframe": "1m",
                "provider": "IBKR",
                "provider_window": "7 D",
                "provider_provenance": f"IBKR FUT MGC 202606 1m 7 D source={SOURCE_ROOT.name}",
                "source_backed_family": "floor pivots / central pivot range",
                "asset_class": "futures",
                "sec_type": "FUT",
                "exchange": "COMEX",
                "multiplier": "10",
                "last_trade_date": "202606",
                "gate_id": "Gate1IbkrMgcFloorPivotCprReclaim1m7d",
                "promotion_allowed": False,
                "trade_usable": False,
                "update_goal": False,
            },
            "notes": ["source_backed=classic_floor_trader_pivots_cpr", "local_cache_replay=false_source_provider_root_reused", "downstream_forbidden_until_cost_density_survives"],
        }
        material.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        materials.append(material)
    return materials


def main() -> int:
    for sub in ["data/provider/normalized", "agent-material", "summaries", "checks", "command-output", "state", "scripts", "materials"]:
        (ROOT / sub).mkdir(parents=True, exist_ok=True)
    shutil.copy2(__file__, ROOT / "scripts" / Path(__file__).name)
    claim = Path(f"/tmp/ict-engine-agent-claims/board-b-factor-refinement/{STAMP}-codex-ibkr-mgc1m-floor-pivot-cpr-reclaim-7d-gate1-v1.claim")
    claim.parent.mkdir(parents=True, exist_ok=True)
    claim.write_text(f"task={FACTOR_ID}\nrun_root={ROOT}\nbranch_path={BRANCH_PATH}\n", encoding="utf-8")
    (ROOT / "materials/source_manifest.json").write_text(json.dumps([
        {"source": "classic floor-trader pivot points and central pivot range", "use": "public/crowd-used OHLCV-only intraday pivot family"},
        {"source": "retained IBKR MGC 202606 1m 7 D provider packet", "path": str(SOURCE_DATA)},
    ], indent=2) + "\n", encoding="utf-8")
    if not SOURCE_DATA.exists():
        raise FileNotFoundError(SOURCE_DATA)
    data_path = ROOT / "data/provider/normalized/ibkr_mgc_202606_1m_7d.csv"
    shutil.copy2(SOURCE_DATA, data_path)
    provider_rows = [{"provider": "IBKR", "sec_type": "FUT", "symbol": "MGC", "product": "precious_metals", "exchange": "COMEX", "last_trade_date": "202606", "timeframe": "1m", "duration": "7 D", "rows": row_count(data_path), "path": str(data_path), "source_provider_root": str(SOURCE_ROOT), "local_cache_replay": "false_source_provider_root_reused"}]
    with (ROOT / "summaries/provider_provenance_matrix.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(provider_rows[0].keys()))
        writer.writeheader(); writer.writerows(provider_rows)
    materials = write_materials(data_path)
    strategies = [Path(json.loads(path.read_text())["strategy_source_path"]) for path in materials]
    commands = [run_cmd("00_strategy_py_compile", [PY, "-m", "py_compile", *strategies], timeout=120)]
    if commands[-1]["exit"] == 0:
        args: list[object] = [ICT, "auto-quant-agent-material-batch", "--symbol", AQ_SYMBOL, "--state-dir", ROOT / "state", "--max-parallel", "1"]
        if AQ_REPO.exists():
            args += ["--repo-url", AQ_REPO]
        for material in materials:
            args += ["--material", material]
        commands.append(run_cmd("01_auto_quant_agent_material_batch", args, timeout=900))
    if commands[-1]["exit"] == 0:
        commands.append(run_cmd("02_auto_quant_agent_material_dispatch", [ICT, "auto-quant-agent-material-dispatch", "--symbol", AQ_SYMBOL, "--state-dir", ROOT / "state"], timeout=1200))
    if commands[-1]["exit"] == 0:
        commands.append(run_cmd("03_auto_quant_agent_material_rank", [ICT, "auto-quant-agent-material-rank", "--symbol", AQ_SYMBOL, "--state-dir", ROOT / "state"], timeout=240))

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
    decision = "gate1_ibkr_mgc1m_floor_pivot_cpr_reclaim_downstream_allowed" if downstream else "drop_or_block_gate1_practical"
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
        title="Source: classic floor-trader pivot points / central pivot range public intraday family.",
        rows=cost_rows,
        branch_ok=branch_ok,
        survivors=survivors_instrument_cost,
        downstream=downstream,
    )
    (ROOT / "summaries/terminal_decision_summary.md").write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps(metrics, indent=2))
    return 0 if commands and commands[-1]["name"] == "03_auto_quant_agent_material_rank" and commands[-1]["exit"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
