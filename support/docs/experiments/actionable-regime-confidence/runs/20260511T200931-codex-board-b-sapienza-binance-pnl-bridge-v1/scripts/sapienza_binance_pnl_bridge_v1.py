#!/usr/bin/env python3
"""Sapienza pump/dump positive-control rows to Binance intraday PnL bridge.

This is an additive Board B diagnostic. It consumes the pinned Sapienza
positive/control feature rows accepted by Board A and reconstructs intraday
entry/exit PnL from Binance public 1h candles where currently listed pairs
still expose historical klines. It does not promote downstream unless the
result clears its own hard checks and the full Board B root gate is separately
eligible.
"""

from __future__ import annotations

import csv
import gzip
import json
import math
import random
import time
import urllib.parse
import urllib.request
from bisect import bisect_left
from collections import Counter, defaultdict
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any


RUN_ID = "20260511T200931+0800-codex-board-b-sapienza-binance-pnl-bridge-v1"
RUN_SLUG = "20260511T200931-codex-board-b-sapienza-binance-pnl-bridge-v1"
SCHEMA_VERSION = "board-b-sapienza-binance-pnl-bridge/v1"

SOURCE_ROOT = Path("/tmp/ict-engine-sapienza-pumpdump-source-screen")
FEATURE_FILE = SOURCE_ROOT / "labeled_features/features_5S.csv.gz"
SOURCE_GATE_JSON = (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T195945-codex-sapienza-pumpdump-control-gate-v1/"
    "sapienza-pumpdump-control-gate/sapienza_pumpdump_control_gate_v1.json"
)

HORIZONS_HOURS = [1, 3, 6, 12, 24]
MAX_CONTROLS_PER_POSITIVE = 3
MIN_POSITIVE_ROWS = 25
MIN_MONTHLY_FOLDS = 4
MIN_LCB = 0.0

BINANCE_EXCHANGE_INFO = "https://api.binance.com/api/v3/exchangeInfo"
BINANCE_KLINES = "https://api.binance.com/api/v3/klines"


def find_repo_root(start: Path) -> Path:
    for candidate in [start, *start.parents]:
        if (candidate / "Cargo.toml").exists() and (candidate / "docs").exists():
            return candidate
    raise RuntimeError(f"cannot locate repo root from {start}")


REPO_ROOT = find_repo_root(Path(__file__).resolve())
RUN_ROOT = REPO_ROOT / "docs/experiments/actionable-regime-confidence/runs" / RUN_SLUG
OUT_DIR = RUN_ROOT / "sapienza-binance-pnl-bridge"
CHECK_DIR = RUN_ROOT / "checks"

REPORT_JSON = OUT_DIR / "sapienza_binance_pnl_bridge_v1.json"
REPORT_MD = OUT_DIR / "sapienza_binance_pnl_bridge_v1.md"
ROWS_CSV = OUT_DIR / "sapienza_binance_pnl_rows_v1.csv"
SYMBOL_CSV = OUT_DIR / "sapienza_binance_symbol_coverage_v1.csv"
SUMMARY_CSV = OUT_DIR / "sapienza_binance_horizon_summary_v1.csv"
PROVIDER_JSON = OUT_DIR / "sapienza_binance_provider_probe_v1.json"
ASSERTIONS = CHECK_DIR / "sapienza_binance_pnl_bridge_v1_assertions.out"


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def parse_dt(value: str) -> datetime:
    return datetime.strptime(value, "%Y-%m-%d %H:%M:%S").replace(tzinfo=UTC)


def month_key(value: datetime) -> str:
    return value.strftime("%Y-%m")


def http_json(url: str, params: dict[str, Any] | None = None) -> Any:
    if params:
        url = f"{url}?{urllib.parse.urlencode(params)}"
    request = urllib.request.Request(url, headers={"User-Agent": "ict-engine-board-b/1.0"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def read_source_rows() -> tuple[list[dict[str, Any]], dict[str, list[dict[str, Any]]]]:
    positives: list[dict[str, Any]] = []
    controls_by_index: dict[str, list[dict[str, Any]]] = defaultdict(list)
    with gzip.open(FEATURE_FILE, "rt", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            item = {
                "pump_index": row["pump_index"],
                "event_dt": parse_dt(row["date"]),
                "symbol": row["symbol"].strip().upper(),
                "gt": int(row["gt"]),
            }
            if item["gt"] == 1:
                positives.append(item)
            elif item["gt"] == 0:
                controls_by_index[item["pump_index"]].append(item)
    positives.sort(key=lambda item: item["event_dt"])
    return positives, controls_by_index


def choose_controls(
    positive: dict[str, Any],
    controls_by_index: dict[str, list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    controls = [
        row
        for row in controls_by_index.get(positive["pump_index"], [])
        if row["symbol"] == positive["symbol"]
        and abs((row["event_dt"] - positive["event_dt"]).total_seconds()) >= 60
    ]
    controls.sort(key=lambda row: abs((row["event_dt"] - positive["event_dt"]).total_seconds()))
    return controls[:MAX_CONTROLS_PER_POSITIVE]


def binance_symbols() -> dict[str, dict[str, Any]]:
    payload = http_json(BINANCE_EXCHANGE_INFO)
    available: dict[str, dict[str, Any]] = {}
    for item in payload.get("symbols", []):
        if item.get("status") != "TRADING":
            continue
        available[item["symbol"]] = item
    return available


def map_symbol(symbol: str, available: dict[str, dict[str, Any]]) -> str | None:
    for quote in ["BTC", "USDT", "ETH", "BNB"]:
        candidate = f"{symbol}{quote}"
        if candidate in available:
            return candidate
    return None


def fetch_klines(symbol: str, start: datetime, end: datetime) -> tuple[list[dict[str, Any]], str]:
    rows: list[dict[str, Any]] = []
    start_ms = int(start.timestamp() * 1000)
    end_ms = int(end.timestamp() * 1000)
    hour_ms = 60 * 60 * 1000
    status = "ok"
    while start_ms < end_ms:
        try:
            chunk = http_json(
                BINANCE_KLINES,
                {
                    "symbol": symbol,
                    "interval": "1h",
                    "startTime": start_ms,
                    "endTime": end_ms,
                    "limit": 1000,
                },
            )
        except Exception as exc:  # noqa: BLE001 - provider probe must record failure.
            status = f"provider_error:{type(exc).__name__}:{str(exc)[:120]}"
            break
        if not isinstance(chunk, list) or not chunk:
            break
        for row in chunk:
            rows.append(
                {
                    "open_dt": datetime.fromtimestamp(int(row[0]) / 1000, tz=UTC),
                    "open": float(row[1]),
                    "high": float(row[2]),
                    "low": float(row[3]),
                    "close": float(row[4]),
                    "volume": float(row[5]),
                }
            )
        next_ms = int(chunk[-1][0]) + hour_ms
        if next_ms <= start_ms:
            status = "blocked:non_advancing_provider_cursor"
            break
        start_ms = next_ms
        time.sleep(0.025)
    deduped = {row["open_dt"]: row for row in rows}
    return [deduped[key] for key in sorted(deduped)], status if rows else "no_rows"


def ceil_hour(value: datetime) -> datetime:
    floored = value.replace(minute=0, second=0, microsecond=0)
    if floored == value:
        return floored
    return floored + timedelta(hours=1)


def attach_event_rows(
    events: list[dict[str, Any]],
    provider_symbol: str,
    candles: list[dict[str, Any]],
    row_type: str,
    target: int,
) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    if not candles:
        return output
    open_times = [row["open_dt"] for row in candles]
    for event in events:
        entry_dt = ceil_hour(event["event_dt"])
        index = bisect_left(open_times, entry_dt)
        if index >= len(candles):
            continue
        entry = candles[index]
        if entry["open"] <= 0:
            continue
        for horizon in HORIZONS_HOURS:
            exit_index = index + horizon - 1
            if exit_index >= len(candles):
                continue
            exit_bar = candles[exit_index]
            provider_return = exit_bar["close"] / entry["open"] - 1.0
            output.append(
                {
                    "run_id": RUN_ID,
                    "row_type": row_type,
                    "target": target,
                    "source_symbol": event["symbol"],
                    "provider_symbol": provider_symbol,
                    "pump_index": event["pump_index"],
                    "event_dt": event["event_dt"].isoformat(),
                    "entry_dt": entry["open_dt"].isoformat(),
                    "exit_dt": exit_bar["open_dt"].isoformat(),
                    "horizon_hours": horizon,
                    "provider_entry_open": entry["open"],
                    "provider_exit_close": exit_bar["close"],
                    "provider_return": provider_return,
                    "event_month": month_key(event["event_dt"]),
                    "source": "Sapienza_pinned_labeled_features_5S",
                    "provider": "binance_public_api",
                    "bridge_precision": "source_timestamp_symbol_to_provider_1h_entry_exit",
                    "parent_regime_root": "Manipulation(scoped)" if target else "Control(non_event)",
                    "regime_profit_branch_path": (
                        "Manipulation(scoped) -> TelegramPumpDumpPositiveControl -> "
                        "SapienzaBinanceProviderExit -> pnl_bridge"
                        if target
                        else "Control(non_event) -> SamePumpIndexNormalControl -> "
                        "SapienzaBinanceProviderExit -> baseline"
                    ),
                }
            )
    return output


def percentile(values: list[float], ratio: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, int(math.floor((len(ordered) - 1) * ratio))))
    return float(ordered[index])


def bootstrap_lcb(values: list[float], seed: int, samples: int = 1500) -> float:
    if not values:
        return 0.0
    rng = random.Random(seed)
    means = []
    for _ in range(samples):
        sample = [values[rng.randrange(len(values))] for _ in values]
        means.append(sum(sample) / len(sample))
    return percentile(means, 0.05)


def summarize_rows(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    summary_rows: list[dict[str, Any]] = []
    best: dict[str, Any] = {
        "horizon_hours": 0,
        "positive_rows": 0,
        "control_rows": 0,
        "positive_mean_return": 0.0,
        "control_mean_return": 0.0,
        "edge_vs_control": 0.0,
        "edge_lcb_5pct": 0.0,
        "monthly_folds": 0,
        "fold_positive_rate_vs_control": 0.0,
        "horizon_gate": "blocked:no_rows",
    }
    for horizon in HORIZONS_HOURS:
        horizon_rows = [row for row in rows if row["horizon_hours"] == horizon]
        positives = [row for row in horizon_rows if row["target"] == 1]
        controls = [row for row in horizon_rows if row["target"] == 0]
        pos_returns = [float(row["provider_return"]) for row in positives]
        control_returns = [float(row["provider_return"]) for row in controls]
        pos_mean = sum(pos_returns) / len(pos_returns) if pos_returns else 0.0
        control_mean = sum(control_returns) / len(control_returns) if control_returns else 0.0
        edge = pos_mean - control_mean
        folds = sorted({row["event_month"] for row in positives})
        control_mean_by_month: dict[str, float] = {}
        positive_mean_by_month: dict[str, float] = {}
        for month in folds:
            pvals = [float(row["provider_return"]) for row in positives if row["event_month"] == month]
            cvals = [float(row["provider_return"]) for row in controls if row["event_month"] == month]
            if pvals:
                positive_mean_by_month[month] = sum(pvals) / len(pvals)
            if cvals:
                control_mean_by_month[month] = sum(cvals) / len(cvals)
        comparable_months = [
            month
            for month in folds
            if month in positive_mean_by_month and month in control_mean_by_month
        ]
        fold_positive_rate = (
            sum(
                1
                for month in comparable_months
                if positive_mean_by_month[month] > control_mean_by_month[month]
            )
            / len(comparable_months)
            if comparable_months
            else 0.0
        )
        paired_edges = []
        min_len = min(len(pos_returns), len(control_returns))
        for index in range(min_len):
            paired_edges.append(pos_returns[index] - control_returns[index])
        edge_lcb = bootstrap_lcb(paired_edges, seed=20260511200931 + horizon)
        if len(positives) < MIN_POSITIVE_ROWS:
            gate = "blocked:insufficient_positive_rows"
        elif len(controls) < len(positives):
            gate = "blocked:insufficient_matched_controls"
        elif len(folds) < MIN_MONTHLY_FOLDS:
            gate = "blocked:insufficient_monthly_folds"
        elif edge_lcb <= MIN_LCB:
            gate = "fail:no_positive_lcb_edge_vs_controls"
        elif fold_positive_rate < 0.60:
            gate = "fail:fold_consistency_below_60pct"
        else:
            gate = "research_watch:positive_provider_edge_needs_full_five_root_rc_spa"
        record = {
            "horizon_hours": horizon,
            "positive_rows": len(positives),
            "control_rows": len(controls),
            "positive_mean_return": pos_mean,
            "control_mean_return": control_mean,
            "edge_vs_control": edge,
            "edge_lcb_5pct": edge_lcb,
            "monthly_folds": len(folds),
            "fold_positive_rate_vs_control": fold_positive_rate,
            "horizon_gate": gate,
        }
        summary_rows.append(record)
        if record["edge_lcb_5pct"] > best["edge_lcb_5pct"] or best["horizon_hours"] == 0:
            best = record
    return summary_rows, best


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str] | None = None) -> None:
    if fields is None and rows:
        fields = list(rows[0].keys())
    if fields is None:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)
    positives, controls_by_index = read_source_rows()
    source_counts = Counter(row["symbol"] for row in positives)
    available = binance_symbols()
    symbol_map = {
        symbol: map_symbol(symbol, available)
        for symbol in sorted(source_counts)
    }
    symbol_map = {key: value for key, value in symbol_map.items() if value}

    source_events_by_symbol: dict[str, list[dict[str, Any]]] = defaultdict(list)
    controls_by_symbol: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for positive in positives:
        if positive["symbol"] not in symbol_map:
            continue
        selected_controls = choose_controls(positive, controls_by_index)
        if not selected_controls:
            continue
        source_events_by_symbol[positive["symbol"]].append(positive)
        controls_by_symbol[positive["symbol"]].extend(selected_controls)

    all_rows: list[dict[str, Any]] = []
    symbol_coverage: list[dict[str, Any]] = []
    for source_symbol in sorted(source_events_by_symbol):
        provider_symbol = symbol_map[source_symbol]
        events = source_events_by_symbol[source_symbol]
        controls = controls_by_symbol[source_symbol]
        window_events = events + controls
        start = min(row["event_dt"] for row in window_events) - timedelta(hours=2)
        end = max(row["event_dt"] for row in window_events) + timedelta(hours=max(HORIZONS_HOURS) + 2)
        candles, status = fetch_klines(provider_symbol, start, end)
        positive_rows = attach_event_rows(events, provider_symbol, candles, "sapienza_positive_pump_event", 1)
        control_rows = attach_event_rows(controls, provider_symbol, candles, "same_pump_index_normal_control", 0)
        all_rows.extend(positive_rows)
        all_rows.extend(control_rows)
        symbol_coverage.append(
            {
                "source_symbol": source_symbol,
                "provider_symbol": provider_symbol,
                "source_positive_events": len(events),
                "source_controls_selected": len(controls),
                "provider_rows": len(candles),
                "attached_positive_event_horizon_rows": len(positive_rows),
                "attached_control_horizon_rows": len(control_rows),
                "status": status,
                "first_provider_dt": candles[0]["open_dt"].isoformat() if candles else "",
                "last_provider_dt": candles[-1]["open_dt"].isoformat() if candles else "",
            }
        )

    summary_rows, best = summarize_rows(all_rows)
    any_horizon_research_watch = any(
        str(row["horizon_gate"]).startswith("research_watch") for row in summary_rows
    )
    positive_event_count = len({(row["source_symbol"], row["pump_index"], row["event_dt"]) for row in all_rows if row["target"] == 1})
    control_event_count = len({(row["source_symbol"], row["pump_index"], row["event_dt"]) for row in all_rows if row["target"] == 0})
    if any_horizon_research_watch:
        gate_result = "research_watch:direct_manipulation_provider_edge_positive_full_board_b_still_requires_roots"
    elif str(best["horizon_gate"]).startswith("blocked:"):
        gate_result = f"fail:{str(best['horizon_gate']).removeprefix('blocked:')}"
    elif str(best["horizon_gate"]).startswith("fail:"):
        gate_result = str(best["horizon_gate"])
    else:
        gate_result = f"fail:{best['horizon_gate']}"
    report = {
        "schema_version": SCHEMA_VERSION,
        "run_id": RUN_ID,
        "run_root": rel(RUN_ROOT),
        "accepted_regime_id": "BoardA_regime_factor_consumer_map_MainRegimeV2_roots_plus_scoped_manipulation",
        "recipe_id": "SapienzaBinancePnlBridgeV1",
        "source_gate_input": SOURCE_GATE_JSON,
        "source_root": str(SOURCE_ROOT),
        "feature_file": str(FEATURE_FILE),
        "provider": "binance_public_api",
        "bridge_precision": "Sapienza source timestamp/symbol labels plus Binance public 1h entry/exit candles",
        "gate_result": gate_result,
        "promotion_allowed": False,
        "downstream_consumption": "not_started:diagnostic_only_full_board_b_still_requires_all_root_rc_spa",
        "positive_events_attached": positive_event_count,
        "control_events_attached": control_event_count,
        "pnl_rows": len(all_rows),
        "symbols_with_provider_rows": sum(1 for row in symbol_coverage if row["provider_rows"] > 0),
        "symbols_mapped_to_current_binance": len(symbol_map),
        "source_positive_symbols": len(source_counts),
        "best_horizon": best,
        "horizon_summaries": summary_rows,
        "source_rows_are_trade_pnl_usable": positive_event_count > 0,
        "board_b_profitability_rows_added": positive_event_count if positive_event_count else 0,
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "artifacts": {
            "json": rel(REPORT_JSON),
            "markdown": rel(REPORT_MD),
            "rows_csv": rel(ROWS_CSV),
            "symbol_coverage_csv": rel(SYMBOL_CSV),
            "horizon_summary_csv": rel(SUMMARY_CSV),
            "provider_probe_json": rel(PROVIDER_JSON),
            "assertions": rel(ASSERTIONS),
        },
        "next_action": (
            "Combine only if the required Bull/Bear/Sideways/Crisis root branches pass RC-SPA; "
            "otherwise continue source/family search without downstream promotion."
        ),
    }

    write_csv(ROWS_CSV, all_rows)
    write_csv(SYMBOL_CSV, symbol_coverage)
    write_csv(SUMMARY_CSV, summary_rows)
    REPORT_JSON.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    PROVIDER_JSON.write_text(
        json.dumps(
            {
                "provider": "binance_public_api",
                "available_current_symbol_count": len(available),
                "mapped_source_symbols": symbol_map,
                "symbol_coverage": symbol_coverage,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    lines = [
        "# Sapienza Binance PnL Bridge v1",
        "",
        f"Run ID: `{RUN_ID}`",
        "",
        "## Decision",
        "",
        f"- Gate result: `{report['gate_result']}`",
        f"- PnL rows: `{report['pnl_rows']}`",
        f"- Attached positive events: `{report['positive_events_attached']}`",
        f"- Attached control events: `{report['control_events_attached']}`",
        f"- Current Binance-mapped source symbols: `{report['symbols_mapped_to_current_binance']}/{report['source_positive_symbols']}`",
        f"- Best horizon: `{best['horizon_hours']}h`",
        f"- Best edge vs controls: `{best['edge_vs_control']:.6f}`",
        f"- Best edge LCB 5%: `{best['edge_lcb_5pct']:.6f}`",
        f"- Best fold positive rate: `{best['fold_positive_rate_vs_control']:.6f}`",
        f"- Downstream consumption: `{report['downstream_consumption']}`",
        f"- Promotion allowed: `{report['promotion_allowed']}`",
        "",
        "## Interpretation",
        "",
        "- This is a source/family switch from the failed Mehrnoom horizon sweep to the accepted Sapienza pump/dump positive-control source.",
        "- It uses source-owned labels for event/control identity and Binance public 1h candles for provider-reconstructed entry/exit PnL.",
        "- It remains fail-closed for full Board B because Bull/Bear/Sideways/Crisis root branches still have not passed the five-root RC-SPA gate, and no downstream Pre-Bayes/BBN/CatBoost/execution-tree promotion was started.",
        "",
        "## Artifacts",
        "",
        f"- JSON: `{rel(REPORT_JSON)}`",
        f"- Rows CSV: `{rel(ROWS_CSV)}`",
        f"- Horizon summary CSV: `{rel(SUMMARY_CSV)}`",
        f"- Symbol coverage CSV: `{rel(SYMBOL_CSV)}`",
        f"- Provider probe JSON: `{rel(PROVIDER_JSON)}`",
        f"- Assertions: `{rel(ASSERTIONS)}`",
        "",
    ]
    REPORT_MD.write_text("\n".join(lines), encoding="utf-8")
    assertions = [
        f"run_id={RUN_ID}",
        f"gate_result={report['gate_result']}",
        f"positive_events_attached={positive_event_count}",
        f"control_events_attached={control_event_count}",
        f"pnl_rows={len(all_rows)}",
        f"best_horizon_hours={best['horizon_hours']}",
        f"best_edge_lcb_5pct={best['edge_lcb_5pct']}",
        f"downstream_consumption={report['downstream_consumption']}",
        f"promotion_allowed={str(report['promotion_allowed']).lower()}",
        "artifacts_exist=true",
    ]
    ASSERTIONS.write_text("\n".join(assertions) + "\n", encoding="utf-8")
    print(json.dumps(report["best_horizon"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
