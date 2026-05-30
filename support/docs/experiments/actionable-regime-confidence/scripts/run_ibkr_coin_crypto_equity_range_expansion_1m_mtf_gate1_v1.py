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
RUN_ID = "codex-ibkr-coin-crypto-equity-range-expansion-1m-mtf-gate1-v1"
ROOT = BASE / "runs" / f"{STAMP}-{RUN_ID}"
ICT = REPO / ".local-artifacts/cargo-target/debug/ict-engine"
if not ICT.exists():
    ICT = REPO / "target/debug/ict-engine"
PY = Path("/Users/thrill3r/.venvs/ict-engine-provider-py313/bin/python")
if not PY.exists():
    PY = Path("python3")
FETCH = REPO / "support/scripts/auto_quant_external/fetch_external.py"
AQ_REPO = Path("/Users/thrill3r/Auto-Quant")
CLAIM = Path(
    "/tmp/ict-engine-agent-claims/board-b-factor-refinement/"
    "20260522T-current-codex-ibkr-coin-crypto-equity-range-expansion-1m-mtf-gate1.claim"
)

PROVIDER = "IBKR"
SYMBOL = "COIN"
SEC_TYPE = "STK"
PRIMARY_EXCHANGE = "NASDAQ"
AQ_SYMBOL = "IBKR_COIN_CRYPTO_EQUITY_RANGE_EXPANSION_1M_MTF_GATE1_V1"
FACTOR_ID = "ibkr_coin_crypto_equity_range_expansion_1m_mtf_gate1_v1"
BRANCH_PATH = (
    "TrendExpansion -> CryptoEquityRangeExpansionContinuation -> "
    "prior_day_range_breakout_pullback -> ibkr_coin_crypto_equity_range_expansion_1m_mtf_gate1_v1"
)
BRANCH_PARTS = [part.strip() for part in BRANCH_PATH.split(" -> ")]


@dataclass(frozen=True)
class Spec:
    timeframe: str
    bar_size: str
    duration: str
    source_name: str
    role: str


SPECS = [
    Spec("1m", "1 min", "30 D", "ibkr_coin_1m_30d.csv", "training_origin"),
    Spec("5m", "5 mins", "3 M", "ibkr_coin_5m_3m.csv", "small_cycle"),
    Spec("15m", "15 mins", "3 M", "ibkr_coin_15m_3m.csv", "small_cycle_sibling"),
    Spec("30m", "30 mins", "3 M", "ibkr_coin_30m_3m.csv", "neutralizer"),
    Spec("1h", "1 hour", "3 M", "ibkr_coin_1h_3m.csv", "higher_timeframe_veto"),
    Spec("4h", "4 hours", "1 Y", "ibkr_coin_4h_1y.csv", "macro_context"),
    Spec("1d", "1 day", "2 Y", "ibkr_coin_1d_2y.csv", "daily_context"),
]


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
    return f"IbkrCoinRangeExpansion{suffix(spec.timeframe)}V1"


def package_id_for_spec(spec: Spec) -> str:
    duration_tag = spec.duration.replace(" ", "").lower()
    return f"ibkr-coin-crypto-equity-range-expansion-{spec.timeframe}-{duration_tag}-v1"


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
    return f'''from freqtrade.strategy import IStrategy
from pandas import DataFrame


class {class_name}(IStrategy):
    INTERFACE_VERSION = 3
    timeframe = "{timeframe}"
    can_short = False
    minimal_roi = {{"0": 0.018, "90": 0.010, "240": 0.004}}
    stoploss = -0.024
    trailing_stop = True
    trailing_stop_positive = 0.005
    trailing_stop_positive_offset = 0.016
    trailing_only_offset_is_reached = True
    process_only_new_candles = True
    use_exit_signal = True
    startup_candle_count = 260

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        high = dataframe["high"]
        low = dataframe["low"]
        close = dataframe["close"]
        day = dataframe["date"].dt.normalize()
        daily = DataFrame({{"day": day, "high": high, "low": low, "close": close}}).groupby("day").agg(
            prev_high=("high", "max"), prev_low=("low", "min"), prev_close=("close", "last")
        ).shift(1)
        piv = dataframe.join(daily, on=day)
        dataframe["prev_high"] = piv["prev_high"]
        dataframe["prev_low"] = piv["prev_low"]
        dataframe["prev_close"] = piv["prev_close"]
        dataframe["prev_range"] = (dataframe["prev_high"] - dataframe["prev_low"]).replace(0, 1e-9)
        dataframe["ema21"] = close.ewm(span=21, adjust=False).mean()
        dataframe["ema55"] = close.ewm(span=55, adjust=False).mean()
        dataframe["ema144"] = close.ewm(span=144, adjust=False).mean()
        tr = DataFrame({{"hl": high - low, "hc": (high - close.shift()).abs(), "lc": (low - close.shift()).abs()}}).max(axis=1)
        dataframe["atr14"] = tr.rolling(14).mean()
        dataframe["rvol"] = dataframe["volume"] / dataframe["volume"].rolling(45).mean().replace(0, 1)
        dataframe["range_breakout"] = (close > dataframe["prev_high"] + dataframe["prev_range"] * 0.025) & (dataframe["rvol"] >= 1.10)
        dataframe["recent_breakout"] = dataframe["range_breakout"].rolling(24).max().fillna(0) > 0
        dataframe["pullback_hold"] = (
            (low <= dataframe["prev_high"] + dataframe["atr14"] * 0.45)
            & (close > dataframe["prev_high"] - dataframe["atr14"] * 0.15)
            & (close > dataframe["ema21"])
        )
        dataframe["trend_stack"] = (dataframe["ema21"] > dataframe["ema55"]) & (dataframe["ema55"] > dataframe["ema144"])
        dataframe["extension_ok"] = close < dataframe["prev_high"] + dataframe["prev_range"] * 0.90
        minute = dataframe["date"].dt.hour * 60 + dataframe["date"].dt.minute
        dataframe["entry_window"] = (minute >= 13 * 60 + 45) & (minute <= 19 * 60 + 20)
        dataframe["force_exit_window"] = minute >= 19 * 60 + 55
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["enter_long"] = 0
        dataframe["enter_tag"] = ""
        signal = (
            dataframe["entry_window"]
            & dataframe["recent_breakout"]
            & dataframe["pullback_hold"]
            & dataframe["trend_stack"]
            & dataframe["extension_ok"]
            & (dataframe["rvol"] >= 0.75)
        )
        dataframe.loc[signal, ["enter_long", "enter_tag"]] = (1, "{FACTOR_ID}_{timeframe}")
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["exit_long"] = 0
        failed_range = dataframe["close"] < dataframe["prev_high"] - dataframe["atr14"] * 0.55
        trend_lost = dataframe["close"] < dataframe["ema55"] - dataframe["atr14"] * 0.25
        range_target = dataframe["close"] > dataframe["prev_high"] + dataframe["prev_range"] * 0.85
        dataframe.loc[dataframe["force_exit_window"] | failed_range | trend_lost | range_target, "exit_long"] = 1
        return dataframe
'''


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
    prefix = "ibkr-coin-crypto-equity-range-expansion-"
    if package_id.startswith(prefix):
        return package_id[len(prefix) :].split("-", 1)[0]
    unit_label = str(row.get("unit_label") or "")
    label_prefix = "IBKR COIN crypto equity range expansion - "
    if unit_label.startswith(label_prefix):
        return unit_label[len(label_prefix) :].split(" ", 1)[0]
    text = " ".join(str(row.get(key) or "") for key in ("package_id", "unit_label", "provider_provenance"))
    for tf in ("15m", "30m", "5m", "1m", "1h", "4h", "1d"):
        if f"-{tf}-" in text or f"/{tf}" in text or f":{tf}" in text or f" {tf} " in text:
            return tf
    return "unknown"


def write_material_for_spec(spec: Spec, normalized_path: Path) -> Path:
    class_name = strategy_class_name(spec)
    strategy_path = ROOT / "agent-material" / f"{class_name}.py"
    strategy_path.write_text(strategy_source(class_name, spec.timeframe), encoding="utf-8")
    package_id = package_id_for_spec(spec)
    material_path = ROOT / "agent-material" / f"{package_id}.material.json"
    material = {
        "package_id": package_id,
        "title": f"IBKR COIN crypto equity range expansion - {spec.timeframe} {spec.duration}",
        "symbol": SYMBOL,
        "timeframe": spec.timeframe,
        "timerange": timerange(normalized_path),
        "direction": "long",
        "data_path": str(normalized_path),
        "strategy_source_path": str(strategy_path),
        "strategy_class_name": class_name,
        "strategy_brief": "COIN prior-day range breakout followed by pullback hold, RVOL participation, and trend-stack continuation.",
        "evaluation_priority": ["instrument_cost_verification", "per_timeframe_gate", "branch_identity", "downstream_admission_readiness"],
        "consumer_evidence_profile": {
            "branch_path": BRANCH_PATH,
            "regime_profit_branch_path": BRANCH_PATH,
            "branch_id": FACTOR_ID,
            "main_regime": BRANCH_PARTS[0],
            "sub_regime": BRANCH_PARTS[1],
            "sub_sub_regime_or_profit_factor": BRANCH_PARTS[2],
            "profit_factor": BRANCH_PARTS[3],
            "market": "US_EQUITY",
            "product": "single_stock",
            "sector_or_family": "crypto_equity",
            "symbol_root": SYMBOL,
            "training_timeframe": spec.timeframe,
            "base_timeframe": "1m",
            "context_timeframes": ["5m", "15m", "30m", "1h", "4h", "1d"],
            "provider": PROVIDER,
            "provider_window": spec.duration,
            "gate_id": "Gate1IbkrCoinCryptoEquityRangeExpansion",
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
            "equity_commission_model=unverified_fail_closed",
            "pre_bayes_bbn_catboost_execution_tree_allowed=false_until_instrument_cost_gate_passes",
        ],
    }
    material_path.write_text(json.dumps(material, indent=2) + "\n", encoding="utf-8")
    return material_path


def instrument_cost_rows(rank_rows: list[dict], day_counts: dict[str, int]) -> list[dict]:
    rows = []
    for row in rank_rows:
        timeframe = rank_timeframe(row)
        trade_count = int(row.get("trade_count") or 0)
        raw_pct = safe_float(row.get("total_profit_pct"))
        days = max(1, day_counts.get(timeframe, 1))
        trades_per_day = trade_count / days
        density_ok = 1.0 <= trades_per_day <= 3.0
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
    text = f"""# IBKR COIN Crypto-Equity Range Expansion Gate 1

Decision: `{metrics["decision"]}`

Branch path:

```text
{BRANCH_PATH}
```

Provider/window:

- IBKR-first COIN STK SMART/USD primary exchange NASDAQ.
- Requested ladder: `1m=30D`, `5m/15m/30m/1h=3M`, `4h=1Y`, `1d=2Y`.
- Provider, symbol, and timeframe are provenance labels, not branch roots.

Instrument Cost Verification Table:

| Timeframe | Trades | Trades/day | Raw | Instrument cost | Cost model status | Promotion cost verified | Survives instrument cost | Gate 1 survivor |
|---|---:|---:|---:|---:|---|---|---|---|
{chr(10).join(table) if table else "| none | 0 | 0.000 | 0.00% | unverified | `cost_model_unverified` | `False` | `False` | `False` |"}

Interpretation:

{metrics["interpretation"]}

Next:

{metrics["next_useful_work"]}
"""
    (ROOT / "summaries/terminal_decision_summary.md").write_text(text, encoding="utf-8")


def terminal_claim_text(decision: str, instrument_cost_survivors: list[dict], downstream_allowed: bool) -> str:
    return (
        f"status=terminalized\nrun_root={ROOT}\ndecision={decision}\n"
        f"instrument_cost_survivors={json.dumps(instrument_cost_survivors)}\n"
        f"downstream_allowed={str(downstream_allowed).lower()}\n"
        "promotion_allowed=false\ntrade_usable=false\nupdate_goal=false\n"
    )


def append_claim(text: str) -> None:
    if CLAIM.exists():
        CLAIM.write_text(CLAIM.read_text(encoding="utf-8") + text, encoding="utf-8")


def main() -> int:
    for sub in ("data/provider/raw", "data/provider/normalized", "agent-material", "summaries", "checks", "command-output", "state", "scripts"):
        (ROOT / sub).mkdir(parents=True, exist_ok=True)
    shutil.copy2(Path(__file__).resolve(), ROOT / "scripts" / Path(__file__).name)
    append_claim(f"status=running\nrun_root={ROOT}\n")

    command_results = [
        run_cmd("00_provider_status_ibkr", [ICT, "provider-status", "--provider", "ibkr", "--agent"], timeout=60)
    ]
    provider_rows = []
    day_counts: dict[str, int] = {}
    material_paths = []
    material_rows = []

    for index, spec in enumerate(SPECS, start=1):
        duration_tag = spec.duration.replace(" ", "").lower()
        raw_path = ROOT / "data/provider/raw" / spec.source_name
        normalized_path = ROOT / "data/provider/normalized" / spec.source_name
        result = run_cmd(
            f"{index:02d}_ibkr_coin_{spec.timeframe}_{duration_tag}_fetch",
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
                "--port",
                "4002",
                "--client-id",
                str(1290 + index),
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
        class_name = strategy_class_name(spec)
        strategy_path = ROOT / "agent-material" / f"{class_name}.py"
        material_paths.append(str(material_path))
        material_rows.append(
            {
                "branch_path": BRANCH_PATH,
                "timeframe": spec.timeframe,
                "duration": spec.duration,
                "material_path": str(material_path),
                "strategy_path": str(strategy_path),
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
        batch = run_cmd(
            "09_auto_quant_agent_material_batch",
            [
                ICT,
                "auto-quant-agent-material-batch",
                "--symbol",
                AQ_SYMBOL,
                "--state-dir",
                ROOT / "state",
                "--max-parallel",
                "1",
                "--repo-url",
                AQ_REPO,
                *sum([["--material", path] for path in material_paths], []),
            ],
            timeout=2400,
        )
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

    instrument_cost_survivors = [row for row in cost_rows if row["gate1_survivor"]]
    all_commands_ok = all(item["exit"] == 0 for item in command_results)
    branch_fields_preserved = bool(material_rows) and all(row["branch_path"] == BRANCH_PATH for row in material_rows)
    cost_model_verified = any(row["promotion_cost_verified"] for row in cost_rows)
    if instrument_cost_survivors and branch_fields_preserved and cost_model_verified:
        decision = "gate1_instrument_cost_density_survivor_downstream_candidate"
        interpretation = "At least one exact COIN timeframe survived verified instrument-cost economics with practical density and rooted branch fields preserved. Same-root downstream readback is allowed next, but promotion remains false until execution predicates pass."
        next_work = "Run same-root downstream only after preserving the verified instrument-cost packet, then require the full practical lifecycle before promotion."
        pre_bayes_allowed = bbn_allowed = catboost_allowed = execution_tree_allowed = True
    elif rank_rows and not cost_model_verified:
        decision = "gate1_cost_model_unverified_no_downstream"
        interpretation = "COIN produced AQ rank rows, but the exact IBKR COIN equity commission model was not verified from official sources, so cost survival and downstream admission fail closed."
        next_work = "Verify official IBKR US equity commission, regulatory, routing, account, pricing-plan, currency, and fee-effective-date assumptions before any downstream admission."
        pre_bayes_allowed = bbn_allowed = catboost_allowed = execution_tree_allowed = False
    elif rank_rows:
        decision = "drop_gate1_instrument_cost_or_density_failed"
        interpretation = "COIN produced AQ rank rows, but no row survived both verified instrument-cost economics and practical trade density. Stop before downstream."
        next_work = "Preserve as observation and rotate to a materially different family or a same-root variant that widens per-trade excursion before verified costs."
        pre_bayes_allowed = bbn_allowed = catboost_allowed = execution_tree_allowed = False
    else:
        decision = "provider_or_aq_blocked_no_gate1_verdict"
        interpretation = "Provider/material/AQ did not produce rank rows, so this is not a factor verdict. Inspect command-output and retry only the failed infrastructure leg."
        next_work = "Classify blocker from command exits; do not promote or call the factor negative without AQ rank evidence."
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
        "survivors_instrument_cost": instrument_cost_survivors,
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
                ["coin_nasdaq_stock_contract", "yes", f"{SYMBOL} {SEC_TYPE} {PRIMARY_EXCHANGE}"],
                ["requested_full_ladder", "yes", "1m/5m/15m/30m/1h/4h/1d"],
                ["branch_fields_preserved", "yes" if branch_fields_preserved else "no", BRANCH_PATH],
                ["instrument_cost_table_written", "yes", str(ROOT / "checks/instrument_cost_table.json")],
                ["downstream_blocked_or_allowed_by_gate1", "yes", decision],
                ["commands_all_zero", "yes" if all_commands_ok else "no", str(ROOT / "checks")],
            ]
        )
    write_terminal_summary(metrics, cost_rows)
    append_claim(terminal_claim_text(decision, instrument_cost_survivors, execution_tree_allowed))
    (ROOT / "checks/ibkr_coin_crypto_equity_range_expansion_1m_mtf_gate1_v1.exit").write_text("0\n", encoding="utf-8")
    print(str(ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
