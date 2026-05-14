#!/usr/bin/env python3
"""Board B scoped Manipulation stop/take-profit action-surface diagnostic.

Run-local additive experiment. It consumes the existing Mehrnoom/Binance
provider-reconstructed direct-event rows and cached Binance 1h OHLCV bars,
then tests executable stop/take-profit paths for the scoped Manipulation branch.
"""

from __future__ import annotations

import csv
import json
import math
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from statistics import mean, variance
from typing import Any


RUN_ID = "20260511T204718+0800-codex-board-b-manipulation-stop-tp-v1"
RUN_SLUG = "20260511T204718-codex-board-b-manipulation-stop-tp-v1"
RECIPE_ID = "ManipulationStopTakeProfitV1"
SCHEMA_VERSION = "board-b-manipulation-stop-tp/v1"
SOURCE_RUN_SLUG = "20260511T194035-codex-board-b-mehrnoom-binance-intraday-pnl-v1"
ROUNDTRIP_COST = 0.0015

VARIANTS: list[dict[str, Any]] = [
    {"variant_id": "long_tp015_sl020_h6", "direction": "long", "tp": 0.015, "sl": 0.020, "horizon": 6},
    {"variant_id": "long_tp030_sl020_h12", "direction": "long", "tp": 0.030, "sl": 0.020, "horizon": 12},
    {"variant_id": "long_tp050_sl030_h24", "direction": "long", "tp": 0.050, "sl": 0.030, "horizon": 24},
    {"variant_id": "long_tp080_sl050_h48", "direction": "long", "tp": 0.080, "sl": 0.050, "horizon": 48},
    {"variant_id": "short_tp015_sl020_h6", "direction": "short", "tp": 0.015, "sl": 0.020, "horizon": 6},
    {"variant_id": "short_tp030_sl020_h12", "direction": "short", "tp": 0.030, "sl": 0.020, "horizon": 12},
    {"variant_id": "short_tp050_sl030_h24", "direction": "short", "tp": 0.050, "sl": 0.030, "horizon": 24},
    {"variant_id": "short_tp080_sl050_h48", "direction": "short", "tp": 0.080, "sl": 0.050, "horizon": 48},
]


def find_repo_root(start: Path) -> Path:
    for candidate in [start, *start.parents]:
        if (candidate / "Cargo.toml").exists() and (candidate / "docs").exists():
            return candidate
    raise RuntimeError(f"cannot locate repo root from {start}")


REPO_ROOT = find_repo_root(Path(__file__).resolve())
RUN_ROOT = REPO_ROOT / "docs/experiments/actionable-regime-confidence/runs" / RUN_SLUG
OUT_DIR = RUN_ROOT / "manipulation-stop-tp"
CHECK_DIR = RUN_ROOT / "checks"
FAIL_CLOSED_DIR = RUN_ROOT / "ict-engine-fail-closed"
SOURCE_DIR = (
    REPO_ROOT
    / "docs/experiments/actionable-regime-confidence/runs"
    / SOURCE_RUN_SLUG
    / "mehrnoom-binance-intraday-pnl"
)
SOURCE_ROWS = SOURCE_DIR / "mehrnoom_binance_intraday_pnl_rows_v1.csv"
SOURCE_REPORT = SOURCE_DIR / "mehrnoom_binance_intraday_pnl_v1.json"
SOURCE_CACHE = SOURCE_DIR / "ohlcv-cache"

SUMMARY_CSV = OUT_DIR / "manipulation_stop_tp_summary_v1.csv"
BRANCH_ROWS_CSV = OUT_DIR / "manipulation_stop_tp_branch_rows_v1.csv"
REPORT_JSON = OUT_DIR / "manipulation_stop_tp_v1.json"
REPORT_MD = OUT_DIR / "manipulation_stop_tp_v1.md"
ASSERTIONS = CHECK_DIR / "manipulation_stop_tp_v1_assertions.out"
FAIL_CLOSED_MD = FAIL_CLOSED_DIR / "manipulation_stop_tp_fail_closed_summary_v1.md"


def rel(path: Path) -> str:
    return str(path.relative_to(REPO_ROOT))


def parse_iso(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def parse_bool(value: object) -> bool:
    return str(value).strip().lower() in {"true", "1", "yes"}


def safe_float(value: object) -> float:
    try:
        out = float(value)
    except (TypeError, ValueError):
        return 0.0
    return 0.0 if math.isnan(out) or math.isinf(out) else out


def dt_to_ms(value: datetime) -> int:
    return int(value.timestamp() * 1000)


def cache_path(symbol: str) -> Path:
    return SOURCE_CACHE / f"{symbol.replace('/', '_')}_1h.csv"


def load_source_rows() -> list[dict[str, str]]:
    with SOURCE_ROWS.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def load_ohlc_maps(symbols: set[str]) -> dict[str, dict[int, dict[str, float]]]:
    maps: dict[str, dict[int, dict[str, float]]] = {}
    for symbol in sorted(symbols):
        rows: dict[int, dict[str, float]] = {}
        path = cache_path(symbol)
        if path.exists():
            with path.open(newline="", encoding="utf-8") as handle:
                for row in csv.DictReader(handle):
                    rows[int(row["timestamp_ms"])] = {
                        "open": safe_float(row["open"]),
                        "high": safe_float(row["high"]),
                        "low": safe_float(row["low"]),
                        "close": safe_float(row["close"]),
                    }
        maps[symbol] = rows
    return maps


def lcb_5pct(values: list[float]) -> float:
    if not values:
        return 0.0
    if len(values) == 1:
        return values[0]
    return mean(values) - 1.645 * math.sqrt(variance(values) / len(values))


def diff_lcb_5pct(primary: list[float], control: list[float]) -> float:
    if not primary or not control:
        return 0.0
    primary_var = variance(primary) if len(primary) > 1 else 0.0
    control_var = variance(control) if len(control) > 1 else 0.0
    stderr = math.sqrt(primary_var / len(primary) + control_var / len(control))
    return mean(primary) - mean(control) - 1.645 * stderr


def fold_rates(
    primary_by_fold: dict[str, list[float]],
    control_by_fold: dict[str, list[float]],
) -> tuple[int, float, float]:
    absolute_folds = [(fold, vals) for fold, vals in primary_by_fold.items() if vals]
    abs_rate = (
        sum(1 for _, vals in absolute_folds if mean(vals) > 0.0) / len(absolute_folds)
        if absolute_folds
        else 0.0
    )
    shared = sorted(set(primary_by_fold) & set(control_by_fold))
    diff_values = [
        mean(primary_by_fold[fold]) - mean(control_by_fold[fold])
        for fold in shared
        if primary_by_fold[fold] and control_by_fold[fold]
    ]
    diff_rate = sum(1 for value in diff_values if value > 0.0) / len(diff_values) if diff_values else 0.0
    return len(diff_values), abs_rate, diff_rate


def simulate_variant(
    *,
    entry_ts: datetime,
    entry_open: float,
    ohlc_map: dict[int, dict[str, float]],
    direction: str,
    tp: float,
    sl: float,
    horizon: int,
) -> tuple[float | None, str]:
    if entry_open <= 0.0:
        return None, "missing_entry"
    if direction == "long":
        take_price = entry_open * (1.0 + tp)
        stop_price = entry_open * (1.0 - sl)
    else:
        take_price = entry_open * (1.0 - tp)
        stop_price = entry_open * (1.0 + sl)

    last_close: float | None = None
    for offset in range(horizon):
        bar = ohlc_map.get(dt_to_ms(entry_ts + timedelta(hours=offset)))
        if not bar:
            continue
        high = bar["high"]
        low = bar["low"]
        last_close = bar["close"]
        if direction == "long":
            if low <= stop_price:
                return stop_price / entry_open - 1.0 - ROUNDTRIP_COST, "stop"
            if high >= take_price:
                return take_price / entry_open - 1.0 - ROUNDTRIP_COST, "take_profit"
        else:
            if high >= stop_price:
                return entry_open / stop_price - 1.0 - ROUNDTRIP_COST, "stop"
            if low <= take_price:
                return entry_open / take_price - 1.0 - ROUNDTRIP_COST, "take_profit"
    if last_close is None or last_close <= 0.0:
        return None, "missing_exit"
    if direction == "long":
        return last_close / entry_open - 1.0 - ROUNDTRIP_COST, "time_exit"
    return entry_open / last_close - 1.0 - ROUNDTRIP_COST, "time_exit"


def branch_path(variant_id: str, direction: str) -> str:
    leaf = "ProviderStopTakeLong" if direction == "long" else "ProviderStopTakeShort"
    return f"Manipulation(scoped) -> TelegramPumpEvent -> {leaf} -> {RECIPE_ID}:{variant_id}"


def summarize_variant(
    *,
    variant: dict[str, Any],
    positive: list[float],
    control: list[float],
    positive_by_fold: dict[str, list[float]],
    control_by_fold: dict[str, list[float]],
) -> dict[str, Any]:
    shared_folds, fold_abs, fold_vs_control = fold_rates(positive_by_fold, control_by_fold)
    positive_mean = mean(positive) if positive else 0.0
    control_mean = mean(control) if control else 0.0
    edge = positive_mean - control_mean
    failures: list[str] = []
    if len(positive) < 500 or len(control) < 500:
        failures.append("reject_min_positive_or_control_rows_lt500")
    if shared_folds < 6:
        failures.append("reject_monthly_folds_lt6")
    if positive_mean <= 0.0:
        failures.append("reject_no_positive_absolute_edge_after_cost")
    if lcb_5pct(positive) <= 0.0:
        failures.append("reject_absolute_lcb_nonpositive")
    if fold_abs < 0.60:
        failures.append("reject_absolute_fold_positive_rate_lt60pct")
    if edge <= 0.0:
        failures.append("reject_no_regime_specificity_vs_controls")
    if diff_lcb_5pct(positive, control) <= 0.0:
        failures.append("reject_specificity_lcb_nonpositive")
    if fold_vs_control < 0.60:
        failures.append("reject_specificity_fold_rate_lt60pct")
    gate = "pass:tradeable_manipulation_stop_tp_candidate" if not failures else "fail:" + "|".join(failures)
    return {
        "schema_version": SCHEMA_VERSION,
        "run_id": RUN_ID,
        "recipe_id": RECIPE_ID,
        "parent_regime_root": "Manipulation(scoped)",
        "manipulation_overlay_state": "direct_event_provider_reconstructed",
        "sub_regime_tags": "TelegramPumpEvent",
        "sub_sub_regime_or_profit_factor": "ProviderStopTakeProfit",
        "profit_factor_family": "direct_manipulation_stop_take_profit",
        "profit_factor_leaf": f"{RECIPE_ID}:{variant['variant_id']}",
        "regime_profit_branch_path": branch_path(variant["variant_id"], variant["direction"]),
        "regime_profit_branch_path_version": SCHEMA_VERSION,
        "trade_or_bar_horizon": f"{variant['horizon']}h",
        "allowed_action": f"{variant['direction']}_stop_tp",
        "suppression_rule": "suppress_or_abstain_if_no_tradeable_stop_tp_action",
        "variant_id": variant["variant_id"],
        "take_profit": variant["tp"],
        "stop_loss": variant["sl"],
        "positive_rows": len(positive),
        "control_rows": len(control),
        "monthly_folds": shared_folds,
        "positive_mean_net": positive_mean,
        "control_mean_net": control_mean,
        "positive_minus_control_net": edge,
        "positive_lcb_5pct": lcb_5pct(positive),
        "positive_minus_control_lcb_5pct": diff_lcb_5pct(positive, control),
        "fold_positive_rate_absolute": fold_abs,
        "fold_positive_rate_vs_control": fold_vs_control,
        "roundtrip_cost": ROUNDTRIP_COST,
        "gate_result": gate,
    }


def collect() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    rows = load_source_rows()
    ohlc_maps = load_ohlc_maps({row["provider_symbol"] for row in rows})
    buckets: dict[str, dict[str, Any]] = {}
    for variant in VARIANTS:
        buckets[variant["variant_id"]] = {
            "positive": [],
            "control": [],
            "positive_by_fold": defaultdict(list),
            "control_by_fold": defaultdict(list),
        }
    branch_rows: list[dict[str, Any]] = []

    for row in rows:
        symbol = row["provider_symbol"]
        entry_ts = parse_iso(row["entry_ts"])
        entry_open = safe_float(row["entry_open"])
        is_positive = parse_bool(row["is_manipulation_positive"])
        fold = entry_ts.strftime("%Y-%m")
        ohlc_map = ohlc_maps.get(symbol, {})
        for variant in VARIANTS:
            value, exit_reason = simulate_variant(
                entry_ts=entry_ts,
                entry_open=entry_open,
                ohlc_map=ohlc_map,
                direction=variant["direction"],
                tp=variant["tp"],
                sl=variant["sl"],
                horizon=variant["horizon"],
            )
            if value is None:
                continue
            bucket = buckets[variant["variant_id"]]
            side = "positive" if is_positive else "control"
            fold_side = "positive_by_fold" if is_positive else "control_by_fold"
            bucket[side].append(value)
            bucket[fold_side][fold].append(value)
            if is_positive:
                branch_rows.append(
                    {
                        "schema_version": SCHEMA_VERSION,
                        "run_id": RUN_ID,
                        "recipe_id": RECIPE_ID,
                        "row_id": row["row_id"],
                        "coin": row["coin"],
                        "provider_symbol": symbol,
                        "event_dt": row["event_dt"],
                        "entry_ts": entry_ts.isoformat(),
                        "variant_id": variant["variant_id"],
                        "direction": variant["direction"],
                        "horizon_hours": variant["horizon"],
                        "take_profit": variant["tp"],
                        "stop_loss": variant["sl"],
                        "exit_reason": exit_reason,
                        "roundtrip_cost": ROUNDTRIP_COST,
                        "profit_ratio_net": value,
                        "parent_regime_root": "Manipulation(scoped)",
                        "regime_profit_branch_path": branch_path(variant["variant_id"], variant["direction"]),
                        "year_month_fold": fold,
                        "source": "Mehrnoom_Mirtaheri_Telegram_events",
                        "provider": "binance_public_1h_cache",
                    }
                )

    summaries = [
        summarize_variant(
            variant=variant,
            positive=buckets[variant["variant_id"]]["positive"],
            control=buckets[variant["variant_id"]]["control"],
            positive_by_fold=buckets[variant["variant_id"]]["positive_by_fold"],
            control_by_fold=buckets[variant["variant_id"]]["control_by_fold"],
        )
        for variant in VARIANTS
    ]
    return summaries, branch_rows


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def write_report(report: dict[str, Any], summaries: list[dict[str, Any]]) -> None:
    decision = report["decision"]
    rows = [
        "# Manipulation Stop/Take-Profit v1",
        "",
        f"Run ID: `{RUN_ID}`",
        "",
        "## Decision",
        "",
        f"- Gate result: `{decision['gate_result']}`",
        f"- Tradeable candidates: `{decision['tradeable_candidates']}`",
        f"- Best variant: `{decision['best_variant']}`",
        f"- Best positive mean net: `{decision['best_positive_mean_net']:.6f}`",
        f"- Best positive LCB 5%: `{decision['best_positive_lcb_5pct']:.6f}`",
        f"- Best specificity edge: `{decision['best_specificity_edge']:.6f}`",
        f"- Best specificity LCB 5%: `{decision['best_specificity_lcb_5pct']:.6f}`",
        f"- Branch rows: `{decision['branch_rows']}`",
        f"- Downstream consumption: `{decision['downstream_consumption']}`",
        "",
        "## Summary",
        "",
        "| Variant | Action | Horizon | Pos Rows | Ctrl Rows | Folds | Pos Mean Net | Ctrl Mean Net | Edge | Pos LCB | Edge LCB | Fold+ Abs | Fold+ Ctrl | Gate |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in summaries:
        rows.append(
            f"| `{row['variant_id']}` | `{row['allowed_action']}` | {row['trade_or_bar_horizon']} | "
            f"{row['positive_rows']} | {row['control_rows']} | {row['monthly_folds']} | "
            f"{row['positive_mean_net']:.6f} | {row['control_mean_net']:.6f} | "
            f"{row['positive_minus_control_net']:.6f} | {row['positive_lcb_5pct']:.6f} | "
            f"{row['positive_minus_control_lcb_5pct']:.6f} | "
            f"{row['fold_positive_rate_absolute']:.4f} | {row['fold_positive_rate_vs_control']:.4f} | "
            f"`{row['gate_result']}` |"
        )
    rows.extend(
        [
            "",
            "## Interpretation",
            "",
            "- This is an executable provider-OHLC path probe: entries use the reconstructed next-bar open, then stop/take-profit logic over Binance 1h bars.",
            "- Same-bar stop/take-profit collisions are resolved conservatively as stop first.",
            "- Full Board B promotion still requires Bull, Bear, Sideways, Crisis, and scoped Manipulation to pass branch gates before Pre-Bayes / BBN / CatBoost / execution tree consumption.",
            "",
            "## Artifacts",
            "",
            f"- JSON: `{rel(REPORT_JSON)}`",
            f"- Summary CSV: `{rel(SUMMARY_CSV)}`",
            f"- Branch rows CSV: `{rel(BRANCH_ROWS_CSV)}`",
            f"- Assertions: `{rel(ASSERTIONS)}`",
            f"- Fail-closed summary: `{rel(FAIL_CLOSED_MD)}`",
            "",
            "## Next",
            "",
            f"- {decision['next_action']}",
        ]
    )
    REPORT_MD.write_text("\n".join(rows) + "\n", encoding="utf-8")
    FAIL_CLOSED_MD.write_text(
        "\n".join(
            [
                "# Manipulation Stop/Take-Profit ict-engine Fail-Closed Summary v1",
                "",
                f"Run ID: `{RUN_ID}`",
                "",
                f"- Direct Manipulation branch gate: `{decision['gate_result']}`",
                f"- Downstream consumption: `{decision['downstream_consumption']}`",
                "- Pre-Bayes / BBN / CatBoost / execution tree were not started because the full Board B five-branch RC-SPA gate is not satisfied.",
                "- This is fail-closed direct-branch evidence, not a promoted profitability packet.",
                "",
                f"Primary blocker: {decision['primary_blocker']}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)
    FAIL_CLOSED_DIR.mkdir(parents=True, exist_ok=True)
    source_report = json.loads(SOURCE_REPORT.read_text(encoding="utf-8"))
    summaries, branch_rows = collect()
    tradeable = [row for row in summaries if not str(row["gate_result"]).startswith("fail:")]
    best = max(
        summaries,
        key=lambda row: (
            row["positive_lcb_5pct"],
            row["positive_mean_net"],
            row["positive_minus_control_lcb_5pct"],
        ),
    )
    best_specificity = max(
        summaries,
        key=lambda row: (
            row["positive_minus_control_lcb_5pct"],
            row["positive_minus_control_net"],
            row["positive_lcb_5pct"],
        ),
    )
    gate_result = (
        "pass:direct_manipulation_stop_tp_candidate"
        if tradeable
        else "fail:no_tradeable_stop_tp_action_surface"
    )
    decision = {
        "gate_result": gate_result,
        "tradeable_candidates": [f"{row['variant_id']}:{row['trade_or_bar_horizon']}" for row in tradeable],
        "best_variant": best["variant_id"],
        "best_positive_mean_net": best["positive_mean_net"],
        "best_positive_lcb_5pct": best["positive_lcb_5pct"],
        "best_specificity_variant": best_specificity["variant_id"],
        "best_specificity_edge": best_specificity["positive_minus_control_net"],
        "best_specificity_lcb_5pct": best_specificity["positive_minus_control_lcb_5pct"],
        "branch_rows": len(branch_rows),
        "downstream_consumption": "not_started:full_board_b_branch_gate_not_satisfied",
        "promotion_allowed_for_full_board_b": False,
        "primary_blocker": (
            "full Board B still requires Bull/Bear/Sideways/Crisis plus scoped Manipulation branch gates; "
            "this run only evaluates direct Manipulation stop/take-profit action paths"
        ),
        "next_action": (
            "B2R-repeat: if a direct Manipulation stop/take-profit candidate passed, combine it only with a "
            "separate root-branch candidate that passes Bull/Bear/Sideways/Crisis RC-SPA; otherwise switch source."
        ),
    }
    report = {
        "run_id": RUN_ID,
        "schema_version": SCHEMA_VERSION,
        "recipe_id": RECIPE_ID,
        "source_bridge_run_id": source_report["run_id"],
        "source_rows": rel(SOURCE_ROWS),
        "decision": decision,
        "summary": summaries,
        "artifacts": {
            "report_json": rel(REPORT_JSON),
            "report_md": rel(REPORT_MD),
            "summary_csv": rel(SUMMARY_CSV),
            "branch_rows_csv": rel(BRANCH_ROWS_CSV),
            "assertions": rel(ASSERTIONS),
            "fail_closed_summary": rel(FAIL_CLOSED_MD),
        },
    }
    write_csv(SUMMARY_CSV, summaries)
    write_csv(BRANCH_ROWS_CSV, branch_rows)
    REPORT_JSON.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_report(report, summaries)
    ASSERTIONS.write_text(
        "\n".join(
            [
                f"run_id={RUN_ID}",
                f"gate_result={decision['gate_result']}",
                f"tradeable_candidates={','.join(decision['tradeable_candidates'])}",
                f"best_variant={decision['best_variant']}",
                f"best_positive_mean_net={decision['best_positive_mean_net']:.10f}",
                f"best_positive_lcb_5pct={decision['best_positive_lcb_5pct']:.10f}",
                f"best_specificity_variant={decision['best_specificity_variant']}",
                f"best_specificity_edge={decision['best_specificity_edge']:.10f}",
                f"best_specificity_lcb_5pct={decision['best_specificity_lcb_5pct']:.10f}",
                f"branch_rows={decision['branch_rows']}",
                f"downstream_consumption={decision['downstream_consumption']}",
                f"promotion_allowed_for_full_board_b={decision['promotion_allowed_for_full_board_b']}",
                f"artifacts_exist={REPORT_JSON.exists() and REPORT_MD.exists() and SUMMARY_CSV.exists() and BRANCH_ROWS_CSV.exists() and FAIL_CLOSED_MD.exists()}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    print(json.dumps(decision, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
