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


REPO = Path("/Users/thrill3r/projects-ict-engine/ict-engine")
BASE = REPO / "support/docs/experiments/actionable-regime-confidence"
STAMP = datetime.now(ZoneInfo("Asia/Shanghai")).strftime("%Y%m%dT%H%M%S+0800")
ROOT = BASE / "runs" / f"{STAMP}-codex-ibkr-mgc1m-initial-balance-acceptance-7d-gate1-v1"
PY = Path("/Users/thrill3r/.venvs/ict-engine-provider-py313/bin/python")
if not PY.exists():
    PY = Path("python3")
FETCH = REPO / "support/scripts/auto_quant_external/fetch_external.py"
ICT = REPO / ".local-artifacts/cargo-target/debug/ict-engine"
if not ICT.exists():
    ICT = REPO / "target/debug/ict-engine"
AQ_REPO = Path("/Users/thrill3r/Auto-Quant")

AQ_SYMBOL = "IBKR_MGC1M_INITIAL_BALANCE_ACCEPTANCE_7D_GATE1_V1"
FACTOR_ID = "ibkr_mgc1m_initial_balance_acceptance_7d_gate1_v1"
BRANCH_PATH = "MarketProfile -> InitialBalanceAcceptance -> ibkr_mgc1m_initial_balance_acceptance_7d_gate1_v1"


@dataclass(frozen=True)
class Variant:
    name: str
    ib_minutes: int
    mode: str
    accept_bars: int
    max_extension_atr: float
    rvol_min: float
    roi: float
    stoploss: float
    trail: float
    offset: float
    startup: int


VARIANTS = [
    Variant("ib30_acceptance_dense", 30, "break_accept", 2, 1.55, 0.50, 0.0028, -0.0065, 0.0009, 0.0026, 220),
    Variant("ib60_acceptance_balanced", 60, "break_accept", 3, 1.30, 0.60, 0.0038, -0.0085, 0.0012, 0.0035, 260),
    Variant("ib30_failed_break_reclaim", 30, "failed_break_reclaim", 2, 1.20, 0.45, 0.0032, -0.0080, 0.0010, 0.0030, 220),
    Variant("ib60_midpoint_drive", 60, "midpoint_drive", 3, 1.70, 0.55, 0.0048, -0.0100, 0.0015, 0.0044, 280),
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


def fetch_args(output: Path) -> list[object]:
    return [
        PY, FETCH, "ibkr-historical",
        "--symbol", "MGC",
        "--sec-type", "FUT",
        "--exchange", "COMEX",
        "--currency", "USD",
        "--last-trade-date", "202606",
        "--multiplier", "10",
        "--bar-size", "1 min",
        "--duration", "7 D",
        "--what-to-show", "TRADES",
        "--host", "127.0.0.1",
        "--port", "4002",
        "--client-id", "946",
        "--market-data-type", "3",
        "--output", output,
    ]


def class_name(variant: Variant) -> str:
    safe = "".join(part.title() for part in variant.name.split("_"))
    return f"IbkrMgcInitialBalanceAcceptance{safe}1MinV1"


def strategy_source(name: str, variant: Variant) -> str:
    tag = f"{FACTOR_ID}_{variant.name}"
    if variant.mode == "break_accept":
        entry_expr = f'''(
            (dataframe["close"] > dataframe["ib_high"])
            & (dataframe["accept_above_ib"] >= {variant.accept_bars})
            & (dataframe["ib_extension_atr"].between(0.0, {variant.max_extension_atr}))
        )'''
    elif variant.mode == "failed_break_reclaim":
        entry_expr = f'''(
            (dataframe["swept_ib_low_recent"] > 0)
            & (dataframe["close"] > dataframe["ib_mid"])
            & (dataframe["close"] > dataframe["session_vwap"] - dataframe["atr14"] * 0.14)
            & (dataframe["ib_mid_reclaim_bars"] >= {variant.accept_bars})
            & (dataframe["ib_extension_atr"].between(-0.45, {variant.max_extension_atr}))
        )'''
    else:
        entry_expr = f'''(
            (dataframe["close"] > dataframe["ib_mid"])
            & (dataframe["close"] < dataframe["ib_high"] + dataframe["atr14"] * {variant.max_extension_atr})
            & (dataframe["accept_above_mid"] >= {variant.accept_bars})
            & (dataframe["ema21"] >= dataframe["ema55"] - dataframe["atr14"] * 0.14)
        )'''
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
    startup_candle_count = {variant.startup}

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["ema21"] = dataframe["close"].ewm(span=21, adjust=False).mean()
        dataframe["ema55"] = dataframe["close"].ewm(span=55, adjust=False).mean()
        dataframe["vol80"] = dataframe["volume"].rolling(80).mean()
        tr = DataFrame({{"hl": dataframe["high"] - dataframe["low"], "hc": (dataframe["high"] - dataframe["close"].shift()).abs(), "lc": (dataframe["low"] - dataframe["close"].shift()).abs()}}).max(axis=1)
        dataframe["atr14"] = tr.rolling(14).mean()
        dt = dataframe["date"]
        day_key = dt.dt.strftime("%Y-%m-%d")
        minute = dt.dt.hour * 60 + dt.dt.minute
        typical = (dataframe["high"] + dataframe["low"] + dataframe["close"]) / 3.0
        pv = typical * dataframe["volume"]
        dataframe["session_vwap"] = pv.groupby(day_key).cumsum() / dataframe["volume"].groupby(day_key).cumsum().replace(0, 1)
        dataframe["regular_session_minute"] = minute - (13 * 60 + 20)
        dataframe["ib_window"] = (dataframe["regular_session_minute"] >= 0) & (dataframe["regular_session_minute"] < {variant.ib_minutes})
        ib_high_series = dataframe["high"].where(dataframe["ib_window"]).groupby(day_key).cummax()
        ib_low_series = dataframe["low"].where(dataframe["ib_window"]).groupby(day_key).cummin()
        dataframe["ib_high"] = ib_high_series.groupby(day_key).ffill()
        dataframe["ib_low"] = ib_low_series.groupby(day_key).ffill()
        dataframe["ib_mid"] = (dataframe["ib_high"] + dataframe["ib_low"]) / 2.0
        dataframe["after_ib"] = dataframe["regular_session_minute"] >= {variant.ib_minutes}
        dataframe["entry_window"] = (dataframe["regular_session_minute"] >= {variant.ib_minutes}) & (dataframe["regular_session_minute"] <= 390)
        dataframe["force_exit_window"] = (minute >= 20 * 60 + 50) & (minute < 21 * 60 + 55)
        dataframe["rvol"] = dataframe["volume"] / dataframe["vol80"].replace(0, 1)
        dataframe["ib_range_atr"] = (dataframe["ib_high"] - dataframe["ib_low"]) / dataframe["atr14"].replace(0, 0.000001)
        dataframe["ib_extension_atr"] = (dataframe["close"] - dataframe["ib_high"]) / dataframe["atr14"].replace(0, 0.000001)
        above_ib = dataframe["after_ib"] & (dataframe["close"] > dataframe["ib_high"])
        above_mid = dataframe["after_ib"] & (dataframe["close"] > dataframe["ib_mid"])
        dataframe["accept_above_ib"] = above_ib.groupby(day_key).rolling(6, min_periods=1).sum().reset_index(level=0, drop=True)
        dataframe["accept_above_mid"] = above_mid.groupby(day_key).rolling(8, min_periods=1).sum().reset_index(level=0, drop=True)
        dataframe["ib_mid_reclaim_bars"] = (dataframe["close"] > dataframe["ib_mid"]).groupby(day_key).rolling(5, min_periods=1).sum().reset_index(level=0, drop=True)
        dataframe["swept_ib_low_recent"] = ((dataframe["low"] < dataframe["ib_low"] - dataframe["atr14"] * 0.08) & dataframe["after_ib"]).groupby(day_key).rolling(20, min_periods=1).sum().reset_index(level=0, drop=True)
        dataframe["ema21_slope_atr"] = (dataframe["ema21"] - dataframe["ema21"].shift(8)) / dataframe["atr14"].replace(0, 0.000001)
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["enter_long"] = 0
        dataframe["enter_tag"] = ""
        profile_signal = {entry_expr}
        signal = (
            dataframe["entry_window"]
            & profile_signal
            & dataframe["ib_range_atr"].between(0.22, 5.60)
            & (dataframe["rvol"] >= {variant.rvol_min})
            & (dataframe["ema21_slope_atr"].fillna(0) >= -0.18)
        )
        dataframe.loc[signal, ["enter_long", "enter_tag"]] = (1, "{tag}")
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["exit_long"] = 0
        fail = (dataframe["close"] < dataframe["ib_mid"] - dataframe["atr14"] * 0.45) | (dataframe["close"] < dataframe["session_vwap"] - dataframe["atr14"] * 0.55)
        dataframe.loc[dataframe["force_exit_window"] | fail, "exit_long"] = 1
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


def cost_survives(trade_count: int, cost_stressed_total_profit_pct: float) -> bool:
    return trade_count > 0 and cost_stressed_total_profit_pct > 0


def hard_gate_downstream_allowed(branch_fields_preserved: bool, exact_1m_5bps: list[str]) -> bool:
    return bool(branch_fields_preserved and exact_1m_5bps)


def label_for(row: dict) -> str:
    package = str(row.get("package_id") or "")
    variant = next((item.name for item in VARIANTS if item.name.replace("_", "-") in package), "unknown")
    return f"MGC/{variant}/1m"


def write_materials(data_path: Path) -> tuple[list[Path], list[Path]]:
    materials: list[Path] = []
    strategies: list[Path] = []
    for variant in VARIANTS:
        klass = class_name(variant)
        strategy = ROOT / "agent-material" / f"{klass}.py"
        strategy.write_text(strategy_source(klass, variant), encoding="utf-8")
        strategies.append(strategy)
        material = ROOT / "agent-material" / f"ibkr_mgc_initial_balance_acceptance_{variant.name}_1m_7d_v1.material.json"
        payload = {
            "package_id": f"ibkr-mgc-initial-balance-acceptance-{variant.name.replace('_', '-')}-1m-7d-v1",
            "title": f"IBKR MGC initial balance acceptance {variant.name} 1m 7D",
            "symbol": "MGC",
            "timeframe": "1m",
            "timerange": timerange(data_path),
            "direction": "long",
            "data_path": str(data_path),
            "strategy_source_path": str(strategy),
            "strategy_class_name": klass,
            "strategy_brief": "IBKR micro gold futures exact 1m market-profile initial-balance acceptance / failed-break reclaim.",
            "evaluation_priority": ["fresh_ibkr_precious_metals", "market_profile_initial_balance", "exact_1m_cost_density"],
            "consumer_evidence_profile": {
                "branch_path": BRANCH_PATH,
                "regime_profit_branch_path": BRANCH_PATH,
                "branch_id": FACTOR_ID,
                "market": "FUTURES",
                "product": "precious_metals",
                "root_symbol": "MGC",
                "root_timeframe": "1m",
                "main_regime": "MarketProfile",
                "sub_regime": "InitialBalanceAcceptance",
                "sub_sub_regime_or_profit_factor": FACTOR_ID,
                "profit_factor": FACTOR_ID,
                "base_timeframe": "1m",
                "training_timeframe": "1m",
                "material_timeframe": "1m",
                "provider": "IBKR",
                "provider_window": "7 D",
                "provider_provenance": "IBKR FUT MGC 202606 1m 7 D",
                "source_backed_family": "market profile / initial balance",
                "asset_class": "futures",
                "sec_type": "FUT",
                "exchange": "COMEX",
                "multiplier": "10",
                "last_trade_date": "202606",
                "gate_id": "Gate1IbkrMgcInitialBalanceAcceptance1m7d",
                "promotion_allowed": False,
                "trade_usable": False,
                "update_goal": False,
            },
            "notes": ["exact_1m_only=true", "local_cache_replay=false", "public_family_rotation=market_profile_initial_balance"],
        }
        material.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        materials.append(material)
    return materials, strategies


def main() -> int:
    for sub in ["data/provider/raw", "data/provider/normalized", "agent-material", "summaries", "checks", "command-output", "state", "scripts"]:
        (ROOT / sub).mkdir(parents=True, exist_ok=True)
    shutil.copy2(__file__, ROOT / "scripts" / Path(__file__).name)
    claim = Path(f"/tmp/ict-engine-agent-claims/board-b-factor-refinement/{STAMP}-codex-ibkr-mgc1m-initial-balance-acceptance-7d-gate1-v1.claim")
    claim.parent.mkdir(parents=True, exist_ok=True)
    claim.write_text(
        f"task={FACTOR_ID}\nrun_root={ROOT}\nbranch_path={BRANCH_PATH}\n"
        "non_takeover=fresh MGC/1m precious-metals market-profile branch; avoids active SI downstream and M2K/MNQ lanes\n",
        encoding="utf-8",
    )
    raw = ROOT / "data/provider/raw/ibkr_mgc_202606_1m_7d.csv"
    norm = ROOT / "data/provider/normalized/ibkr_mgc_202606_1m_7d.csv"
    commands = [run_cmd("00_provider_status_ibkr", [ICT, "provider-status", "--provider", "ibkr", "--agent"], timeout=60)]
    fetch = run_cmd("01_ibkr_fetch_mgc_1m_7d", fetch_args(raw), timeout=660)
    commands.append(fetch)
    rows = normalize(raw, norm) if raw.exists() else 0
    provider_rows = [{"provider": "IBKR", "sec_type": "FUT", "symbol": "MGC", "product": "precious_metals", "exchange": "COMEX", "last_trade_date": "202606", "timeframe": "1m", "duration": "7 D", "rows": rows, "path": str(norm) if rows else "", "exit": fetch["exit"], "local_cache_replay": "false"}]
    with (ROOT / "summaries/provider_provenance_matrix.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(provider_rows[0].keys()))
        writer.writeheader()
        writer.writerows(provider_rows)
    materials, strategies = write_materials(norm) if rows else ([], [])
    commands.append(run_cmd("02_strategy_py_compile", [PY, "-m", "py_compile", *strategies], timeout=120) if strategies else {"name": "02_strategy_py_compile", "exit": 1})
    if materials and commands[-1]["exit"] == 0:
        args: list[object] = [ICT, "auto-quant-agent-material-batch", "--symbol", AQ_SYMBOL, "--state-dir", ROOT / "state", "--max-parallel", "1"]
        if AQ_REPO.exists():
            args += ["--repo-url", AQ_REPO]
        for material in materials:
            args += ["--material", material]
        commands.append(run_cmd("03_auto_quant_agent_material_batch", args, timeout=900))
    if commands[-1]["exit"] == 0:
        commands.append(run_cmd("04_auto_quant_agent_material_dispatch", [ICT, "auto-quant-agent-material-dispatch", "--symbol", AQ_SYMBOL, "--state-dir", ROOT / "state"], timeout=1200))
    if commands[-1]["exit"] == 0:
        commands.append(run_cmd("05_auto_quant_agent_material_rank", [ICT, "auto-quant-agent-material-rank", "--symbol", AQ_SYMBOL, "--state-dir", ROOT / "state"], timeout=240))
    rank_rows = latest_rank_rows() if commands and commands[-1]["name"] == "05_auto_quant_agent_material_rank" and commands[-1]["exit"] == 0 else []
    cost_rows = []
    for row in rank_rows:
        trades = int(row.get("trade_count") or 0)
        gross = safe_float(row.get("total_profit_pct"))
        record = {"label": label_for(row), "status": row.get("status"), "trade_count": trades, "win_rate_pct": safe_float(row.get("win_rate_pct")), "raw_total_profit_pct": gross, "sharpe": safe_float(row.get("sharpe")), "branch_path": row.get("branch_path")}
        for bps in (0, 1, 2, 5):
            record[f"{bps}bps_per_side_total_profit_pct"] = round(gross - trades * bps * 0.02, 6)
        record["survives_2bps_per_side"] = cost_survives(trades, record["2bps_per_side_total_profit_pct"])
        record["survives_5bps_per_side"] = cost_survives(trades, record["5bps_per_side_total_profit_pct"])
        cost_rows.append(record)
    survivors_2 = [row["label"] for row in cost_rows if row["survives_2bps_per_side"]]
    survivors_5 = [row["label"] for row in cost_rows if row["survives_5bps_per_side"]]
    branch_paths = sorted({str(row.get("branch_path") or "") for row in rank_rows})
    branch_ok = bool(rank_rows) and branch_paths == [BRANCH_PATH]
    downstream = hard_gate_downstream_allowed(branch_ok, survivors_5)
    decision = "gate1_ibkr_mgc1m_initial_balance_acceptance_downstream_allowed" if downstream else "drop_or_block_gate1_practical"
    metrics = {"run_root": str(ROOT), "factor_id": FACTOR_ID, "branch_path": BRANCH_PATH, "decision": decision, "provider_rows": provider_rows, "rank_rows": len(rank_rows), "rank_total_trade_count": sum(int(row.get("trade_count") or 0) for row in rank_rows), "exact_1m_cost_stress": cost_rows, "exact_1m_survivors_2bps": survivors_2, "exact_1m_survivors_5bps": survivors_5, "branch_paths": branch_paths, "branch_fields_preserved": branch_ok, "downstream_allowed": downstream, "pre_bayes_allowed": downstream, "bbn_allowed": downstream, "catboost_allowed": False, "execution_tree_allowed": False, "promotion_allowed": False, "trade_usable": False, "update_goal": False, "local_cache_replay": False, "command_exits": {cmd["name"]: cmd["exit"] for cmd in commands}, "skill_update": "needed_after_downstream" if downstream else "not_needed", "source_backed_family": "market profile / initial balance"}
    (ROOT / "checks/terminal_metrics.json").write_text(json.dumps(metrics, indent=2) + "\n", encoding="utf-8")
    with (ROOT / "summaries/rank_rows.csv").open("w", newline="", encoding="utf-8") as handle:
        fields = ["label", "status", "trade_count", "win_rate_pct", "raw_total_profit_pct", "1bps_per_side_total_profit_pct", "2bps_per_side_total_profit_pct", "5bps_per_side_total_profit_pct", "survives_2bps_per_side", "survives_5bps_per_side", "branch_path"]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows([{key: row.get(key, "") for key in fields} for row in cost_rows])
    lines = ["# Terminal Decision Summary", "", f"Decision: `{decision}`", "", "Exact MGC 1m market-profile / initial-balance rows:", "", "| label | trades | win_rate | raw | 1bps | 2bps | 5bps |", "|---|---:|---:|---:|---:|---:|---:|"]
    for row in cost_rows:
        lines.append(f"| `{row['label']}` | {row['trade_count']} | {row['win_rate_pct']:.4f}% | {row['raw_total_profit_pct']:.2f}% | {row['1bps_per_side_total_profit_pct']:.2f}% | {row['2bps_per_side_total_profit_pct']:.2f}% | {row['5bps_per_side_total_profit_pct']:.2f}% |")
    lines += ["", f"- `branch_fields_preserved={branch_ok}`", f"- `exact_1m_survivors_2bps={survivors_2}`", f"- `exact_1m_survivors_5bps={survivors_5}`", f"- `downstream_allowed={downstream}`", "- source-backed family: `market profile / initial balance acceptance and failed-break reclaim`", ""]
    (ROOT / "summaries/terminal_decision_summary.md").write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps(metrics, indent=2))
    return 0 if commands and commands[-1]["name"] == "05_auto_quant_agent_material_rank" and commands[-1]["exit"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
