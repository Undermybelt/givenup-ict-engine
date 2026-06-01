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
BASE = SCRIPT.parents[1]
REPO = BASE.parents[3]
RUN_STAMP = datetime.now(ZoneInfo("Asia/Shanghai")).strftime("%Y%m%dT%H%M%S+0800")
ROOT = BASE / "runs" / f"{RUN_STAMP}-codex-ibkr-ewm-bayesian-markov-trend-detector-1m-mtf-gate1-v1"
ICT = REPO / ".local-artifacts/cargo-target/debug/ict-engine"
if not ICT.exists():
    ICT = REPO / "target/debug/ict-engine"
PY = Path("/Users/thrill3r/.venvs/ict-engine-provider-py313/bin/python")
if not PY.exists():
    PY = Path("python3")
FETCH = REPO / "support/scripts/auto_quant_external/fetch_external.py"
AQ_REPO = Path("/Users/thrill3r/Auto-Quant")

PROVIDER = "IBKR"
SYMBOL = "EWM"
SEC_TYPE = "STK"
PRIMARY_EXCHANGE = "ARCA"
AQ_SYMBOL = "IBKR_EWM_BAYESIAN_MARKOV_TREND_DETECTOR_1M_MTF_GATE1_V1"
FACTOR_NAME = "bayesian_markov_trend_detector"
FACTOR_ID = "ibkr_ewm_bayesian_markov_trend_detector_1m_mtf_gate1_v1"
BRANCH_PATH = (
    "TrendExpansion -> MalaysiaEtfBayesianMarkovTrendContinuation -> "
    "bayesian_markov_trend_detector -> ibkr_ewm_bayesian_markov_trend_detector_1m_mtf_gate1_v1"
)
BRANCH_PARTS = [part.strip() for part in BRANCH_PATH.split(" -> ")]
VARIANTS = ("dense", "balanced", "quality", "wide")


@dataclass(frozen=True)
class Spec:
    timeframe: str
    bar_size: str
    duration: str
    source_name: str
    role: str


SPECS = [
    Spec("1m", "1 min", "30 D", "ibkr_ewm_1m_30d.csv", "training_origin"),
    Spec("5m", "5 mins", "3 M", "ibkr_ewm_5m_3m.csv", "small_cycle"),
    Spec("15m", "15 mins", "3 M", "ibkr_ewm_15m_3m.csv", "small_cycle_sibling"),
    Spec("30m", "30 mins", "3 M", "ibkr_ewm_30m_3m.csv", "neutralizer"),
    Spec("1h", "1 hour", "3 M", "ibkr_ewm_1h_3m.csv", "higher_timeframe_veto"),
    Spec("4h", "4 hours", "1 Y", "ibkr_ewm_4h_1y.csv", "macro_context"),
    Spec("1d", "1 day", "2 Y", "ibkr_ewm_1d_2y.csv", "daily_context"),
]
RETRY_BY_TIMEFRAME = {
    "1m": Spec("1m", "1 min", "10 D", "ibkr_ewm_1m_10d_retry.csv", "training_origin_retry"),
    "5m": Spec("5m", "5 mins", "1 M", "ibkr_ewm_5m_1m_retry.csv", "small_cycle_retry"),
    "15m": Spec("15m", "15 mins", "1 M", "ibkr_ewm_15m_1m_retry.csv", "small_cycle_sibling_retry"),
    "30m": Spec("30m", "30 mins", "1 M", "ibkr_ewm_30m_1m_retry.csv", "neutralizer_retry"),
    "1h": Spec("1h", "1 hour", "1 M", "ibkr_ewm_1h_1m_retry.csv", "higher_timeframe_retry"),
    "4h": Spec("4h", "4 hours", "6 M", "ibkr_ewm_4h_6m_retry.csv", "macro_context_retry"),
    "1d": Spec("1d", "1 day", "1 Y", "ibkr_ewm_1d_1y_retry.csv", "daily_context_retry"),
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


def normalize_csv(source: Path, destination: Path) -> int:
    if not source.exists() or source.stat().st_size == 0:
        return 0
    rows = []
    with source.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        headers = reader.fieldnames or []
        time_key = next((key for key in ("timestamp", "time", "datetime", "ts_event", "date", "ts") if key in headers), None)
        if not time_key:
            return 0
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
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["timestamp", "open", "high", "low", "close", "volume"])
        writer.writeheader()
        writer.writerows(rows)
    return len(rows)


def timerange(path: Path) -> str:
    if not path.exists():
        return ""
    dates = []
    with path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            raw = (row.get("timestamp") or "").strip()
            if raw:
                dates.append(raw[:10].replace("-", ""))
    return f"{min(dates)}-{max(dates)}" if dates else ""


def trading_days(path: Path) -> int:
    days = set()
    with path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            raw = (row.get("timestamp") or "").strip()
            if raw:
                days.add(raw[:10])
    return max(1, len(days))


def suffix(timeframe: str) -> str:
    return timeframe.replace("m", "Min").replace("h", "Hour").replace("d", "Day")


def strategy_source(class_name: str, timeframe: str, variant: str = "dense") -> str:
    settings = {
        "dense": {
            "roi": 0.0060,
            "stoploss": -0.011,
            "trail": 0.0020,
            "offset": 0.0060,
            "posterior": 0.535,
            "markov": 0.525,
            "entropy": 0.690,
            "transition_edge": 0.020,
            "volume_floor": 0.42,
            "excursion_min": 0.00030,
            "excursion_max": 0.02000,
        },
        "balanced": {
            "roi": 0.0070,
            "stoploss": -0.012,
            "trail": 0.0022,
            "offset": 0.0065,
            "posterior": 0.552,
            "markov": 0.542,
            "entropy": 0.684,
            "transition_edge": 0.024,
            "volume_floor": 0.39,
            "excursion_min": 0.00035,
            "excursion_max": 0.02400,
        },
        "quality": {
            "roi": 0.0085,
            "stoploss": -0.0145,
            "trail": 0.0025,
            "offset": 0.0080,
            "posterior": 0.568,
            "markov": 0.558,
            "entropy": 0.676,
            "transition_edge": 0.028,
            "volume_floor": 0.36,
            "excursion_min": 0.00040,
            "excursion_max": 0.03000,
        },
        "wide": {
            "roi": 0.0100,
            "stoploss": -0.0170,
            "trail": 0.0030,
            "offset": 0.0100,
            "posterior": 0.585,
            "markov": 0.575,
            "entropy": 0.668,
            "transition_edge": 0.032,
            "volume_floor": 0.32,
            "excursion_min": 0.00045,
            "excursion_max": 0.03600,
        },
    }[variant]
    tag = f"{FACTOR_ID}_{variant}_{timeframe}"
    return f'''from freqtrade.strategy import IStrategy
from pandas import DataFrame
import numpy as np


class {class_name}(IStrategy):
    INTERFACE_VERSION = 3
    timeframe = "{timeframe}"
    can_short = False
    minimal_roi = {{"0": {settings["roi"]:.4f}}}
    stoploss = {settings["stoploss"]:.4f}
    trailing_stop = True
    trailing_stop_positive = {settings["trail"]:.4f}
    trailing_stop_positive_offset = {settings["offset"]:.4f}
    trailing_only_offset_is_reached = True
    process_only_new_candles = True
    use_exit_signal = True
    startup_candle_count = 180

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        ret = dataframe["close"].pct_change().fillna(0.0)
        up = (ret > 0.0).astype(int)
        down = (ret < 0.0).astype(int)
        wins = up.rolling(30).sum().fillna(0.0)
        losses = down.rolling(30).sum().fillna(0.0)
        dataframe["bayes_up"] = (2.0 + wins) / (4.0 + wins + losses)

        prev_up = up.shift(1).fillna(0).astype(int)
        prev_down = down.shift(1).fillna(0).astype(int)
        uu = ((prev_up == 1) & (up == 1)).astype(int).rolling(60).sum().fillna(0.0)
        ud = ((prev_up == 1) & (down == 1)).astype(int).rolling(60).sum().fillna(0.0)
        du = ((prev_down == 1) & (up == 1)).astype(int).rolling(60).sum().fillna(0.0)
        dd = ((prev_down == 1) & (down == 1)).astype(int).rolling(60).sum().fillna(0.0)
        dataframe["p_uu"] = (uu + 1.8) / (uu + ud + 2.8)
        dataframe["p_du"] = (du + 1.0) / (du + dd + 2.8)

        ret_mean = ret.rolling(30).mean()
        ret_std = ret.rolling(30).std().replace(0.0, np.nan)
        dataframe["ret_z"] = ((ret - ret_mean) / ret_std).clip(-4.0, 4.0).fillna(0.0)
        emission_up = 1.0 / (1.0 + np.exp(-2.0 * dataframe["ret_z"]))
        prior_up = dataframe["bayes_up"].shift(1).fillna(0.5)
        p_up_pred = prior_up * dataframe["p_uu"] + (1.0 - prior_up) * dataframe["p_du"]
        denom = p_up_pred * emission_up + (1.0 - p_up_pred) * (1.0 - emission_up)
        dataframe["markov_posterior_up"] = np.where(denom > 0.000001, (p_up_pred * emission_up) / denom, p_up_pred)
        fused_up = dataframe["bayes_up"] * 0.70 + dataframe["markov_posterior_up"] * 0.30
        dataframe["smoothed_up"] = fused_up.ewm(alpha=0.35, adjust=False).mean().clip(0.0, 1.0)
        clipped = dataframe["smoothed_up"].clip(0.0001, 0.9999)
        dataframe["entropy"] = -(clipped * np.log(clipped) + (1.0 - clipped) * np.log(1.0 - clipped))

        dataframe["ema21"] = dataframe["close"].ewm(span=21, adjust=False).mean()
        dataframe["ema55"] = dataframe["close"].ewm(span=55, adjust=False).mean()
        tr = DataFrame({{"hl": dataframe["high"] - dataframe["low"], "hc": (dataframe["high"] - dataframe["close"].shift()).abs(), "lc": (dataframe["low"] - dataframe["close"].shift()).abs()}}).max(axis=1)
        dataframe["atr14"] = tr.rolling(14).mean()
        dataframe["vol30"] = dataframe["volume"].rolling(30).mean()
        dataframe["prior_high8"] = dataframe["high"].rolling(8).max().shift(1)
        dataframe["prior_low8"] = dataframe["low"].rolling(8).min().shift(1)
        dataframe["range_pct"] = (dataframe["high"] - dataframe["low"]) / dataframe["close"]
        dataframe["bayes_markov_edge"] = dataframe["smoothed_up"] - 0.5
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["enter_long"] = 0
        dataframe["enter_tag"] = ""
        posterior_ok = dataframe["smoothed_up"] > {settings["posterior"]:.4f}
        markov_ok = dataframe["markov_posterior_up"] > {settings["markov"]:.4f}
        transition_ok = dataframe["p_uu"] > dataframe["p_du"] + {settings["transition_edge"]:.4f}
        entropy_ok = dataframe["entropy"] < {settings["entropy"]:.4f}
        trend_ok = (dataframe["ema21"] >= dataframe["ema55"]) | (dataframe["close"] > dataframe["ema55"])
        reclaim_ok = (dataframe["close"] > dataframe["ema21"]) & (dataframe["close"].shift(1) <= dataframe["ema21"].shift(1))
        breakout_ok = dataframe["close"] > dataframe["prior_high8"]
        participation = dataframe["volume"] >= dataframe["vol30"] * {settings["volume_floor"]:.4f}
        excursion_ok = dataframe["range_pct"].between({settings["excursion_min"]:.5f}, {settings["excursion_max"]:.5f})
        signal = posterior_ok & markov_ok & transition_ok & entropy_ok & trend_ok & (reclaim_ok | breakout_ok) & participation & excursion_ok
        dataframe.loc[signal, ["enter_long", "enter_tag"]] = (1, "{tag}")
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["exit_long"] = 0
        posterior_fail = dataframe["smoothed_up"] < 0.500
        entropy_spike = dataframe["entropy"] > 0.705
        trend_lost = dataframe["close"] < dataframe["ema21"] - dataframe["atr14"] * 0.45
        stop_reclaim_failed = dataframe["close"] < dataframe["prior_low8"]
        dataframe.loc[posterior_fail | entropy_spike | trend_lost | stop_reclaim_failed, "exit_long"] = 1
        return dataframe
'''


def material_payload(
    spec: Spec,
    variant: str,
    data_path: Path,
    strategy_path: Path,
    class_name: str,
) -> dict:
    duration_id = spec.duration.replace(" ", "").lower()
    package_id = f"ibkr-ewm-bayesian-markov-trend-detector-{spec.timeframe}-{variant}-{duration_id}-v1"
    return {
        "package_id": package_id,
        "title": f"IBKR EWM Bayesian-Markov trend detector - {spec.timeframe} {variant} {spec.duration}",
        "factor_name": FACTOR_NAME,
        "symbol": SYMBOL,
        "timeframe": spec.timeframe,
        "timerange": timerange(data_path),
        "direction": "long",
        "data_path": str(data_path),
        "strategy_source_path": str(strategy_path),
        "strategy_class_name": class_name,
        "strategy_brief": "EWM Malaysia ETF long-only Bayesian win/loss posterior fused with synthetic two-state Markov transition persistence.",
        "evaluation_priority": [
            "exact_1m_origin_verified_instrument_cost",
            "per_timeframe_context",
            "branch_identity",
            "downstream_admission_readiness",
        ],
        "consumer_evidence_profile": {
            "branch_path": BRANCH_PATH,
            "regime_profit_branch_path": BRANCH_PATH,
            "branch_id": FACTOR_ID,
            "factor_name": FACTOR_NAME,
            "main_regime": BRANCH_PARTS[0],
            "sub_regime": BRANCH_PARTS[1],
            "sub_sub_regime_or_profit_factor": BRANCH_PARTS[2],
            "profit_factor": BRANCH_PARTS[3],
            "market": "US_EQUITY_ETF",
            "product": "malaysia_country_etf",
            "sector_or_family": "country_etf",
            "symbol_root": SYMBOL,
            "training_timeframe": spec.timeframe,
            "base_timeframe": "1m",
            "context_timeframes": ["5m", "15m", "30m", "1h", "4h", "1d"],
            "provider": PROVIDER,
            "provider_window": spec.duration,
            "gate_id": "Gate1IbkrEwmBayesianMarkovTrendDetector",
            "promotion_allowed": False,
            "trade_usable": False,
            "update_goal": False,
        },
        "notes": [
            f"source_provider={PROVIDER} {SYMBOL} {spec.timeframe} {spec.duration}",
            f"branch_path={BRANCH_PATH}",
            f"factor_name={FACTOR_NAME}",
            "ibkr_first=true",
            "requested_ladder=1m_5m_15m_30m_1h_4h_1d",
            "cost_model_status=cost_model_unverified_no_downstream",
            "pre_bayes_bbn_catboost_execution_tree_allowed=false_until_exact_origin_gate1_passes",
        ],
    }


def latest_rank_rows() -> list[dict]:
    rank_files = sorted((ROOT / "state/auto-quant" / AQ_SYMBOL).glob("auto_quant_agent_material_rank.*.json"))
    if not rank_files:
        return []
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
    prefix = "ibkr-ewm-bayesian-markov-trend-detector-"
    if package_id.startswith(prefix):
        return package_id[len(prefix) :].split("-", 1)[0]
    unit_label = str(row.get("unit_label") or "")
    label_prefix = "IBKR EWM Bayesian-Markov trend detector - "
    if unit_label.startswith(label_prefix):
        return unit_label[len(label_prefix) :].split(" ", 1)[0]
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
        rows.append(
            {
                "package_id": row.get("package_id"),
                "unit_label": row.get("unit_label"),
                "timeframe": timeframe,
                "trade_count": trade_count,
                "trading_days": days,
                "trades_per_day": trades_per_day,
                "raw_pct": raw_pct,
                "instrument_cost_total_profit_pct": None,
                "cost_model_status": "cost_model_unverified",
                "promotion_cost_verified": False,
                "survives_instrument_cost": False,
                "win_rate_pct": safe_float(row.get("win_rate_pct")),
                "sharpe": safe_float(row.get("sharpe")),
                "minimum_trade_sample_floor_met": trade_count > 0,
                "gate1_survivor": False,
            }
        )
    return rows


def write_instrument_cost_csv(rows: list[dict]) -> None:
    path = ROOT / "summaries/rank_rows_instrument_cost.csv"
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def write_terminal_summary(metrics: dict, cost_rows: list[dict]) -> None:
    table = []
    for row in cost_rows:
        table.append(
            "| `{}` | {} | {:.3f} | {:.2f}% | `{}` | `{}` | `{}` |".format(
                row["timeframe"],
                row["trade_count"],
                row["trades_per_day"],
                row["raw_pct"],
                row["cost_model_status"],
                row["survives_instrument_cost"],
                row["gate1_survivor"],
            )
        )
    text = f"""# IBKR EWM Bayesian-Markov Trend Detector Gate 1

Decision: `{metrics["decision"]}`

Branch path:

```text
{BRANCH_PATH}
```

Provider/window:

- IBKR-first EWM STK SMART/USD primary exchange ARCA.
- Requested ladder: `1m=30D`, `5m/15m/30m/1h=3M`, `4h=1Y`, `1d=2Y`, with narrower retry windows if a provider leg times out.
- Provider, symbol, product, and timeframe are provenance labels, not branch roots.

Gate result:

| Timeframe | Trades | Trades/day | Raw | Cost model | Survives instrument cost | Gate 1 survivor |
|---|---:|---:|---:|---|---|---|
{chr(10).join(table) if table else "| none | 0 | 0.000 | 0.00% | `cost_model_unverified` | `False` | `False` |"}

Interpretation:

{metrics["interpretation"]}

Next:

{metrics["next_useful_work"]}
"""
    (ROOT / "summaries/terminal_decision_summary.md").write_text(text, encoding="utf-8")


def fetch_and_normalize(spec: Spec, index: int, command_results: list[dict]) -> tuple[Spec, Path, Path, int, int, dict]:
    attempts = [spec]
    if spec.timeframe in RETRY_BY_TIMEFRAME:
        attempts.append(RETRY_BY_TIMEFRAME[spec.timeframe])
    last_result = {"exit": 1, "timed_out": False}
    last_raw = ROOT / "data/provider/raw" / spec.source_name
    last_normalized = ROOT / "data/provider/normalized" / spec.source_name
    for attempt_index, attempt in enumerate(attempts):
        raw_path = ROOT / "data/provider/raw" / attempt.source_name
        normalized_path = ROOT / "data/provider/normalized" / attempt.source_name
        command_name = f"{index:02d}_ibkr_ewm_{attempt.timeframe}_{attempt.duration.replace(' ', '').lower()}"
        if attempt_index:
            command_name += "_retry"
        result = run_cmd(
            command_name,
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
                attempt.bar_size,
                "--duration",
                attempt.duration,
                "--what-to-show",
                "TRADES",
                "--host",
                "127.0.0.1",
                "--port",
                "4002",
                "--client-id",
                str(970 + index * 3 + attempt_index),
                "--output",
                raw_path,
            ],
            timeout=540,
        )
        command_results.append(result)
        rows = normalize_csv(raw_path, normalized_path)
        last_result, last_raw, last_normalized = result, raw_path, normalized_path
        if rows:
            return attempt, raw_path, normalized_path, rows, trading_days(normalized_path), result
    return attempts[-1], last_raw, last_normalized, 0, 0, last_result


def main() -> int:
    for sub in ("data/provider/raw", "data/provider/normalized", "agent-material", "summaries", "checks", "command-output", "state", "scripts"):
        (ROOT / sub).mkdir(parents=True, exist_ok=True)
    shutil.copy2(SCRIPT, ROOT / "scripts" / SCRIPT.name)

    command_results = [
        run_cmd("00_provider_status_ibkr", [ICT, "provider-status", "--provider", "ibkr", "--agent"], timeout=60)
    ]
    provider_rows = []
    day_counts: dict[str, int] = {}
    material_paths = []
    material_rows = []

    for index, spec in enumerate(SPECS, start=1):
        used_spec, raw_path, normalized_path, rows, days, result = fetch_and_normalize(spec, index, command_results)
        if rows:
            day_counts[used_spec.timeframe] = days
        provider_rows.append(
            {
                "provider": PROVIDER,
                "provider_label": f"{PROVIDER} {SYMBOL} {used_spec.timeframe} {used_spec.duration}",
                "symbol": SYMBOL,
                "timeframe": used_spec.timeframe,
                "bar_size": used_spec.bar_size,
                "duration": used_spec.duration,
                "role": used_spec.role,
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

        for variant in VARIANTS:
            class_name = f"IbkrEwmBayesianMarkovTrendDetector{suffix(used_spec.timeframe)}{variant.title()}V1"
            strategy_path = ROOT / "agent-material" / f"{class_name}.py"
            strategy_path.write_text(strategy_source(class_name, used_spec.timeframe, variant), encoding="utf-8")
            material = material_payload(used_spec, variant, normalized_path, strategy_path, class_name)
            material_path = ROOT / "agent-material" / f"{material['package_id']}.material.json"
            material_path.write_text(json.dumps(material, indent=2) + "\n", encoding="utf-8")
            material_paths.append(str(material_path))
            material_rows.append(
                {
                    "branch_path": BRANCH_PATH,
                    "factor_name": FACTOR_NAME,
                    "timeframe": used_spec.timeframe,
                    "duration": used_spec.duration,
                    "variant": variant,
                    "material_path": str(material_path),
                    "strategy_path": str(strategy_path),
                    "rows": rows,
                    "trading_days": days,
                }
            )

    with (ROOT / "summaries/provider_provenance_matrix.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(provider_rows[0].keys()))
        writer.writeheader()
        writer.writerows(provider_rows)
    (ROOT / "summaries/provider_provenance_matrix.json").write_text(json.dumps(provider_rows, indent=2) + "\n", encoding="utf-8")

    if material_rows:
        with (ROOT / "summaries/material_paths.csv").open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(material_rows[0].keys()))
            writer.writeheader()
            writer.writerows(material_rows)

    strategy_files = [row["strategy_path"] for row in material_rows]
    py_compile = run_cmd("08_strategy_py_compile", [PY, "-m", "py_compile", *strategy_files], timeout=60)
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
                timeout=2400,
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
    if rank_rows:
        with (ROOT / "summaries/rank_rows.csv").open("w", newline="", encoding="utf-8") as handle:
            fieldnames = sorted({key for row in rank_rows for key in row.keys()})
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rank_rows)
    cost_rows = instrument_cost_rows(rank_rows, day_counts)
    (ROOT / "checks/instrument_cost_table.json").write_text(json.dumps(cost_rows, indent=2) + "\n", encoding="utf-8")
    write_instrument_cost_csv(cost_rows)

    survivors_instrument_cost = [row for row in cost_rows if row["gate1_survivor"]]
    exact_origin_survivors_instrument_cost = [row for row in survivors_instrument_cost if row["timeframe"] == "1m"]
    all_commands_ok = all(item["exit"] == 0 for item in command_results)
    branch_fields_preserved = bool(material_rows) and all(row["branch_path"] == BRANCH_PATH and row["factor_name"] == FACTOR_NAME for row in material_rows)
    if exact_origin_survivors_instrument_cost and branch_fields_preserved:
        decision = "gate1_exact_1m_instrument_cost_survivor_downstream_candidate"
        interpretation = "The exact EWM 1m Bayesian-Markov origin has an instrument-cost survivor, but this script does not verify the ETF commission model in-slice. Downstream remains blocked until promotion_cost_verified is true."
        next_work = "Verify the exact IBKR ETF cost model from official broker/exchange/regulatory sources in the same slice, then rerun the instrument-cost gate."
        pre_bayes_allowed = bbn_allowed = catboost_allowed = execution_tree_allowed = False
    elif rank_rows:
        decision = "gate1_cost_model_unverified_no_downstream"
        interpretation = "EWM produced AQ rank rows, but this script has no verified IBKR ETF instrument-cost model. Stop before downstream instead of applying a fixed-bps stress ladder."
        next_work = "Verify the exact ETF cost model from official sources in-slice or keep this family observation-only."
        pre_bayes_allowed = bbn_allowed = catboost_allowed = execution_tree_allowed = False
    else:
        decision = "provider_or_aq_blocked_no_gate1_verdict"
        interpretation = "Provider/material/AQ did not produce rank rows, so this is not a factor verdict. Inspect command-output and retry only the failed infrastructure leg."
        next_work = "Classify blocker from command exits; do not promote or call the factor negative without AQ rank evidence."
        pre_bayes_allowed = bbn_allowed = catboost_allowed = execution_tree_allowed = False

    metrics = {
        "run_root": str(ROOT),
        "factor_id": FACTOR_ID,
        "factor_name": FACTOR_NAME,
        "branch_path": BRANCH_PATH,
        "decision": decision,
        "provider_rows": provider_rows,
        "provider_data_acquired_count": sum(1 for row in provider_rows if row["provider_data_acquired"] == "true"),
        "material_count": len(material_rows),
        "rank_rows": len(rank_rows),
        "rank_total_trade_count": sum(int(row.get("trade_count") or 0) for row in rank_rows),
        "positive_raw_rows": sum(1 for row in cost_rows if row["raw_pct"] > 0),
        "cost_gate_authority": "instrument_cost",
        "cost_model_status": "cost_model_unverified",
        "promotion_cost_verified": False,
        "instrument_cost_rows": cost_rows,
        "survivors_instrument_cost": survivors_instrument_cost,
        "exact_origin_survivors_instrument_cost": exact_origin_survivors_instrument_cost,
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
                ["ewm_arca_etf_contract", "yes", f"{SYMBOL} {SEC_TYPE} SMART/{PRIMARY_EXCHANGE}"],
                ["requested_full_ladder", "yes", "1m/5m/15m/30m/1h/4h/1d"],
                ["factor_identity_reused", "yes" if branch_fields_preserved else "no", FACTOR_NAME],
                ["branch_fields_preserved", "yes" if branch_fields_preserved else "no", BRANCH_PATH],
                ["instrument_cost_table_written", "yes", str(ROOT / "checks/instrument_cost_table.json")],
                ["downstream_blocked_until_cost_model_verified", "yes", decision],
                ["commands_all_zero", "yes" if all_commands_ok else "no", str(ROOT / "checks")],
            ]
        )
    write_terminal_summary(metrics, cost_rows)
    (ROOT / "checks/ibkr_ewm_bayesian_markov_trend_detector_1m_mtf_gate1_v1.exit").write_text("0\n", encoding="utf-8")
    print(str(ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
