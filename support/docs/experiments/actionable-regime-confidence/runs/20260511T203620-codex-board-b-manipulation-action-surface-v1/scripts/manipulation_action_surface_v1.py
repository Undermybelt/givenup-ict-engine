#!/usr/bin/env python3
"""Board B scoped Manipulation action-surface diagnostic.

This run-local script consumes the existing Mehrnoom/Binance provider
reconstructed direct-event rows plus the cached Binance 1h bars. It tests
whether the scoped Manipulation branch has any tradeable long/short action
surface after costs. A cooldown-relative row is reported only as diagnostic
specificity context and is never treated as a tradeable profitability packet.
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


RUN_ID = "20260511T203620+0800-codex-board-b-manipulation-action-surface-v1"
RUN_SLUG = "20260511T203620-codex-board-b-manipulation-action-surface-v1"
RECIPE_ID = "ManipulationActionSurfaceV1"
SCHEMA_VERSION = "board-b-manipulation-action-surface/v1"
SOURCE_RUN_SLUG = "20260511T194035-codex-board-b-mehrnoom-binance-intraday-pnl-v1"
HORIZONS = [1, 2, 3, 4, 6, 8, 12, 18, 24, 36, 48]
ROUNDTRIP_COST = 0.0015


def find_repo_root(start: Path) -> Path:
    for candidate in [start, *start.parents]:
        if (candidate / "Cargo.toml").exists() and (candidate / "docs").exists():
            return candidate
    raise RuntimeError(f"cannot locate repo root from {start}")


REPO_ROOT = find_repo_root(Path(__file__).resolve())
RUN_ROOT = REPO_ROOT / "docs/experiments/actionable-regime-confidence/runs" / RUN_SLUG
OUT_DIR = RUN_ROOT / "manipulation-action-surface"
CHECK_DIR = RUN_ROOT / "checks"
SOURCE_DIR = (
    REPO_ROOT
    / "docs/experiments/actionable-regime-confidence/runs"
    / SOURCE_RUN_SLUG
    / "mehrnoom-binance-intraday-pnl"
)
SOURCE_ROWS = SOURCE_DIR / "mehrnoom_binance_intraday_pnl_rows_v1.csv"
SOURCE_REPORT = SOURCE_DIR / "mehrnoom_binance_intraday_pnl_v1.json"
SOURCE_CACHE = SOURCE_DIR / "ohlcv-cache"

SUMMARY_CSV = OUT_DIR / "manipulation_action_surface_summary_v1.csv"
BRANCH_ROWS_CSV = OUT_DIR / "manipulation_action_surface_branch_rows_v1.csv"
REPORT_JSON = OUT_DIR / "manipulation_action_surface_v1.json"
REPORT_MD = OUT_DIR / "manipulation_action_surface_v1.md"
ASSERTIONS = CHECK_DIR / "manipulation_action_surface_v1_assertions.out"


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


def load_close_maps(symbols: set[str]) -> dict[str, dict[int, float]]:
    maps: dict[str, dict[int, float]] = {}
    for symbol in sorted(symbols):
        close_map: dict[int, float] = {}
        path = cache_path(symbol)
        if path.exists():
            with path.open(newline="", encoding="utf-8") as handle:
                for row in csv.DictReader(handle):
                    close_map[int(row["timestamp_ms"])] = safe_float(row["close"])
        maps[symbol] = close_map
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


def branch_path(action: str) -> str:
    if action == "event_long":
        return "Manipulation(scoped) -> TelegramPumpEvent -> ProviderExitLong -> ManipulationActionSurfaceV1:event_long"
    if action == "event_short":
        return "Manipulation(scoped) -> TelegramPumpEvent -> ProviderExitShort -> ManipulationActionSurfaceV1:event_short"
    return "Manipulation(scoped) -> TelegramPumpEvent -> CooldownRelativeUnderperformance -> diagnostic_not_tradeable"


def summarize_action(
    *,
    action: str,
    horizon: int,
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
    if action == "cooldown_relative":
        failures.append("diagnostic_only:not_tradeable_profit_row")
    if len(positive) < 500 or len(control) < 500:
        failures.append("reject_min_positive_or_control_rows_lt500")
    if shared_folds < 6:
        failures.append("reject_monthly_folds_lt6")
    if action != "cooldown_relative":
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
    gate = "pass:tradeable_manipulation_action_candidate" if not failures else "fail:" + "|".join(failures)
    return {
        "schema_version": SCHEMA_VERSION,
        "run_id": RUN_ID,
        "recipe_id": RECIPE_ID,
        "parent_regime_root": "Manipulation(scoped)",
        "manipulation_overlay_state": "direct_event_provider_reconstructed",
        "sub_regime_tags": "TelegramPumpEvent",
        "sub_sub_regime_or_profit_factor": "ProviderExitActionSurface",
        "profit_factor_family": "direct_manipulation_action_surface",
        "profit_factor_leaf": f"{RECIPE_ID}:{action}:{horizon}h",
        "regime_profit_branch_path": branch_path(action),
        "regime_profit_branch_path_version": SCHEMA_VERSION,
        "trade_or_bar_horizon": f"{horizon}h",
        "allowed_action": action,
        "suppression_rule": "suppress_or_abstain_if_no_tradeable_action_surface",
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
        "roundtrip_cost": 0.0 if action == "cooldown_relative" else ROUNDTRIP_COST,
        "gate_result": gate,
    }


def collect() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    rows = load_source_rows()
    close_maps = load_close_maps({row["provider_symbol"] for row in rows})
    buckets: dict[tuple[str, int], dict[str, Any]] = {}
    branch_rows: list[dict[str, Any]] = []
    for action in ["event_long", "event_short", "cooldown_relative"]:
        for horizon in HORIZONS:
            buckets[(action, horizon)] = {
                "positive": [],
                "control": [],
                "positive_by_fold": defaultdict(list),
                "control_by_fold": defaultdict(list),
            }

    for row in rows:
        symbol = row["provider_symbol"]
        entry_ts = parse_iso(row["entry_ts"])
        entry_open = safe_float(row["entry_open"])
        if entry_open <= 0.0:
            continue
        is_positive = parse_bool(row["is_manipulation_positive"])
        fold = entry_ts.strftime("%Y-%m")
        close_map = close_maps.get(symbol, {})
        for horizon in HORIZONS:
            exit_close = close_map.get(dt_to_ms(entry_ts + timedelta(hours=horizon)))
            if not exit_close or exit_close <= 0.0:
                continue
            gross = exit_close / entry_open - 1.0
            action_values = {
                "event_long": gross - ROUNDTRIP_COST,
                "event_short": -gross - ROUNDTRIP_COST,
                "cooldown_relative": gross,
            }
            for action, value in action_values.items():
                bucket = buckets[(action, horizon)]
                side = "positive" if is_positive else "control"
                fold_side = "positive_by_fold" if is_positive else "control_by_fold"
                bucket[side].append(value)
                bucket[fold_side][fold].append(value)
                if is_positive and action != "cooldown_relative":
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
                            "horizon_hours": horizon,
                            "action": action,
                            "gross_return": gross if action == "event_long" else -gross,
                            "roundtrip_cost": ROUNDTRIP_COST,
                            "profit_ratio_net": value,
                            "parent_regime_root": "Manipulation(scoped)",
                            "regime_profit_branch_path": branch_path(action),
                            "year_month_fold": fold,
                            "source": "Mehrnoom_Mirtaheri_Telegram_events",
                            "provider": "binance_public_1h_cache",
                        }
                    )

    summaries: list[dict[str, Any]] = []
    for action in ["event_long", "event_short", "cooldown_relative"]:
        for horizon in HORIZONS:
            bucket = buckets[(action, horizon)]
            summaries.append(
                summarize_action(
                    action=action,
                    horizon=horizon,
                    positive=bucket["positive"],
                    control=bucket["control"],
                    positive_by_fold=bucket["positive_by_fold"],
                    control_by_fold=bucket["control_by_fold"],
                )
            )
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


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)
    source_report = json.loads(SOURCE_REPORT.read_text(encoding="utf-8"))
    summaries, branch_rows = collect()
    tradeable = [row for row in summaries if not str(row["gate_result"]).startswith("fail:")]
    best_trade = max(
        [row for row in summaries if row["allowed_action"] != "cooldown_relative"],
        key=lambda row: (row["positive_lcb_5pct"], row["positive_mean_net"], row["positive_minus_control_lcb_5pct"]),
    )
    best_specificity = max(
        summaries,
        key=lambda row: (row["positive_minus_control_lcb_5pct"], row["positive_minus_control_net"]),
    )
    decision = {
        "gate_result": "pass:tradeable_manipulation_action_candidate" if tradeable else "fail:no_tradeable_manipulation_action_surface",
        "tradeable_candidates": [
            f"{row['allowed_action']}:{row['trade_or_bar_horizon']}" for row in tradeable
        ],
        "best_trade_action": best_trade["allowed_action"],
        "best_trade_horizon": best_trade["trade_or_bar_horizon"],
        "best_trade_mean_net": best_trade["positive_mean_net"],
        "best_trade_lcb_5pct": best_trade["positive_lcb_5pct"],
        "best_specificity_action": best_specificity["allowed_action"],
        "best_specificity_horizon": best_specificity["trade_or_bar_horizon"],
        "best_specificity_edge": best_specificity["positive_minus_control_net"],
        "best_specificity_lcb_5pct": best_specificity["positive_minus_control_lcb_5pct"],
        "branch_rows": len(branch_rows),
        "downstream_consumption": "not_started:diagnostic_only_full_board_b_still_requires_all_root_rc_spa",
        "promotion_allowed_for_full_board_b": False,
        "primary_blocker": "no long/short direct-event action has positive absolute net LCB after costs",
        "next_action": "B2R-repeat: scoped Manipulation still lacks tradeable PnL edge; switch source/family/panel before downstream promotion.",
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
        },
    }
    write_csv(SUMMARY_CSV, summaries)
    write_csv(BRANCH_ROWS_CSV, branch_rows)
    REPORT_JSON.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    lines = [
        "# Manipulation Action Surface v1",
        "",
        f"Run ID: `{RUN_ID}`",
        "",
        "## Decision",
        "",
        f"- Gate result: `{decision['gate_result']}`",
        f"- Tradeable candidates: `{decision['tradeable_candidates']}`",
        f"- Best trade action: `{decision['best_trade_action']}` / `{decision['best_trade_horizon']}`",
        f"- Best trade mean net: `{decision['best_trade_mean_net']:.6f}`",
        f"- Best trade LCB 5%: `{decision['best_trade_lcb_5pct']:.6f}`",
        f"- Best specificity action: `{decision['best_specificity_action']}` / `{decision['best_specificity_horizon']}`",
        f"- Best specificity edge: `{decision['best_specificity_edge']:.6f}`",
        f"- Best specificity LCB 5%: `{decision['best_specificity_lcb_5pct']:.6f}`",
        f"- Branch rows: `{decision['branch_rows']}`",
        f"- Downstream consumption: `{decision['downstream_consumption']}`",
        "",
        "## Summary",
        "",
        "| Action | Horizon | Pos Rows | Ctrl Rows | Folds | Pos Mean Net | Ctrl Mean Net | Edge | Pos LCB | Edge LCB | Fold+ Abs | Fold+ Ctrl | Gate |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in summaries:
        lines.append(
            f"| `{row['allowed_action']}` | {row['trade_or_bar_horizon']} | {row['positive_rows']} | {row['control_rows']} | {row['monthly_folds']} | "
            f"{row['positive_mean_net']:.6f} | {row['control_mean_net']:.6f} | {row['positive_minus_control_net']:.6f} | "
            f"{row['positive_lcb_5pct']:.6f} | {row['positive_minus_control_lcb_5pct']:.6f} | "
            f"{row['fold_positive_rate_absolute']:.4f} | {row['fold_positive_rate_vs_control']:.4f} | `{row['gate_result']}` |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- `event_long` and `event_short` are tradeable action probes and include roundtrip cost.",
            "- `cooldown_relative` measures event underperformance versus controls only; it is not a tradeable PnL row and cannot promote downstream.",
            "- Full Board B promotion remains impossible unless Bull, Bear, Sideways, Crisis, and scoped Manipulation all pass branch RC-SPA.",
            "",
            "## Artifacts",
            "",
            f"- JSON: `{rel(REPORT_JSON)}`",
            f"- Summary CSV: `{rel(SUMMARY_CSV)}`",
            f"- Branch rows CSV: `{rel(BRANCH_ROWS_CSV)}`",
            f"- Assertions: `{rel(ASSERTIONS)}`",
            "",
            "## Next",
            "",
            f"- {decision['next_action']}",
        ]
    )
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    ASSERTIONS.write_text(
        "\n".join(
            [
                f"run_id={RUN_ID}",
                f"gate_result={decision['gate_result']}",
                f"tradeable_candidates={','.join(decision['tradeable_candidates'])}",
                f"best_trade_action={decision['best_trade_action']}",
                f"best_trade_horizon={decision['best_trade_horizon']}",
                f"best_trade_mean_net={decision['best_trade_mean_net']:.10f}",
                f"best_trade_lcb_5pct={decision['best_trade_lcb_5pct']:.10f}",
                f"best_specificity_action={decision['best_specificity_action']}",
                f"best_specificity_horizon={decision['best_specificity_horizon']}",
                f"best_specificity_edge={decision['best_specificity_edge']:.10f}",
                f"best_specificity_lcb_5pct={decision['best_specificity_lcb_5pct']:.10f}",
                f"branch_rows={decision['branch_rows']}",
                f"downstream_consumption={decision['downstream_consumption']}",
                f"promotion_allowed_for_full_board_b={decision['promotion_allowed_for_full_board_b']}",
                f"artifacts_exist={REPORT_JSON.exists() and REPORT_MD.exists() and SUMMARY_CSV.exists() and BRANCH_ROWS_CSV.exists()}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    print(json.dumps(decision, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
