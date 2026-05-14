#!/usr/bin/env python3
"""Fast Mehrnoom Binance intraday horizon sweep.

Uses the 194035 Binance 1h cache and event/control rows. This diagnostic only
tests fixed exit horizons for the direct Manipulation bridge; it never promotes
full Board B without a later five-root RC-SPA pass.
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


RUN_ID = "20260511T194637+0800-codex-board-b-mehrnoom-binance-horizon-sweep-v1"
RUN_SLUG = "20260511T194637-codex-board-b-mehrnoom-binance-horizon-sweep-v1"
SOURCE_RUN_SLUG = "20260511T194035-codex-board-b-mehrnoom-binance-intraday-pnl-v1"
HORIZONS = [1, 2, 3, 4, 6, 8, 12, 18, 24, 36, 48]


def find_repo_root(start: Path) -> Path:
    for candidate in [start, *start.parents]:
        if (candidate / "Cargo.toml").exists() and (candidate / "docs").exists():
            return candidate
    raise RuntimeError(f"cannot locate repo root from {start}")


REPO_ROOT = find_repo_root(Path(__file__).resolve())
RUN_ROOT = REPO_ROOT / "docs/experiments/actionable-regime-confidence/runs" / RUN_SLUG
OUT_DIR = RUN_ROOT / "mehrnoom-binance-horizon-sweep"
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

REPORT_JSON = OUT_DIR / "mehrnoom_binance_horizon_sweep_v1.json"
REPORT_MD = OUT_DIR / "mehrnoom_binance_horizon_sweep_v1.md"
SUMMARY_CSV = OUT_DIR / "mehrnoom_binance_horizon_sweep_summary_v1.csv"
ASSERTIONS = CHECK_DIR / "mehrnoom_binance_horizon_sweep_v1_assertions.out"


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


def cache_path(symbol: str) -> Path:
    return SOURCE_CACHE / f"{symbol.replace('/', '_')}_1h.csv"


def load_close_maps(symbols: set[str]) -> dict[str, dict[int, float]]:
    maps: dict[str, dict[int, float]] = {}
    for symbol in sorted(symbols):
        path = cache_path(symbol)
        close_map: dict[int, float] = {}
        if path.exists():
            with path.open(newline="", encoding="utf-8") as handle:
                for row in csv.DictReader(handle):
                    close_map[int(row["timestamp_ms"])] = safe_float(row["close"])
        maps[symbol] = close_map
    return maps


def dt_to_ms(value: datetime) -> int:
    return int(value.timestamp() * 1000)


def lcb_5pct(pos: list[float], ctrl: list[float]) -> float:
    if not pos or not ctrl:
        return 0.0
    pos_var = variance(pos) if len(pos) > 1 else 0.0
    ctrl_var = variance(ctrl) if len(ctrl) > 1 else 0.0
    stderr = math.sqrt(pos_var / len(pos) + ctrl_var / len(ctrl))
    return mean(pos) - mean(ctrl) - 1.645 * stderr


def load_source() -> list[dict[str, str]]:
    with SOURCE_ROWS.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def summarize() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rows = load_source()
    close_maps = load_close_maps({row["provider_symbol"] for row in rows})
    buckets: dict[int, dict[str, Any]] = {
        horizon: {"pos": [], "ctrl": [], "fold_pos": defaultdict(list), "fold_ctrl": defaultdict(list)}
        for horizon in HORIZONS
    }
    for row in rows:
        symbol = row["provider_symbol"]
        entry_ts = parse_iso(row["entry_ts"])
        entry_open = safe_float(row["entry_open"])
        if entry_open <= 0.0:
            continue
        is_pos = parse_bool(row["is_manipulation_positive"])
        fold = entry_ts.strftime("%Y-%m")
        close_map = close_maps.get(symbol, {})
        for horizon in HORIZONS:
            exit_ms = dt_to_ms(entry_ts + timedelta(hours=horizon))
            exit_close = close_map.get(exit_ms)
            if not exit_close or exit_close <= 0.0:
                continue
            ret = exit_close / entry_open - 1.0
            key = "pos" if is_pos else "ctrl"
            fold_key = "fold_pos" if is_pos else "fold_ctrl"
            buckets[horizon][key].append(ret)
            buckets[horizon][fold_key][fold].append(ret)

    summaries: list[dict[str, Any]] = []
    for horizon in HORIZONS:
        bucket = buckets[horizon]
        pos = bucket["pos"]
        ctrl = bucket["ctrl"]
        folds = sorted(set(bucket["fold_pos"]) | set(bucket["fold_ctrl"]))
        fold_diffs = []
        for fold in folds:
            fold_pos = bucket["fold_pos"].get(fold, [])
            fold_ctrl = bucket["fold_ctrl"].get(fold, [])
            if fold_pos and fold_ctrl:
                fold_diffs.append(mean(fold_pos) - mean(fold_ctrl))
        diff = mean(pos) - mean(ctrl) if pos and ctrl else 0.0
        lcb = lcb_5pct(pos, ctrl)
        fold_rate = sum(1 for item in fold_diffs if item > 0.0) / len(fold_diffs) if fold_diffs else 0.0
        failures: list[str] = []
        if len(pos) < 500 or len(ctrl) < 500:
            failures.append("reject_min_positive_or_control_rows_lt500")
        if len(fold_diffs) < 6:
            failures.append("reject_monthly_folds_lt6")
        if diff <= 0.0:
            failures.append("reject_positive_underperforms_control")
        if lcb <= 0.0:
            failures.append("reject_lcb_nonpositive")
        if fold_rate < 0.60:
            failures.append("reject_fold_positive_rate_lt60pct")
        summaries.append(
            {
                "horizon_hours": horizon,
                "positive_rows": len(pos),
                "control_rows": len(ctrl),
                "monthly_folds": len(fold_diffs),
                "positive_mean_return": mean(pos) if pos else 0.0,
                "control_mean_return": mean(ctrl) if ctrl else 0.0,
                "positive_minus_control_return": diff,
                "positive_minus_control_lcb_5pct": lcb,
                "fold_positive_rate_vs_control": fold_rate,
                "gate_result": "pass:direct_horizon_candidate" if not failures else "fail:" + "|".join(failures),
            }
        )
    passed = [row for row in summaries if str(row["gate_result"]).startswith("pass:")]
    best = max(summaries, key=lambda row: (row["positive_minus_control_lcb_5pct"], row["positive_minus_control_return"]))
    decision = {
        "gate_result": "pass:diagnostic_horizon_candidate_found" if passed else "fail:no_horizon_positive_vs_controls",
        "best_horizon_hours": best["horizon_hours"],
        "horizons_passed": [row["horizon_hours"] for row in passed],
        "horizons_evaluated": len(summaries),
        "best_positive_minus_control_return": best["positive_minus_control_return"],
        "best_positive_minus_control_lcb_5pct": best["positive_minus_control_lcb_5pct"],
        "best_fold_positive_rate_vs_control": best["fold_positive_rate_vs_control"],
        "promotion_allowed_for_full_board_b": False,
        "downstream_consumption": "not_started:diagnostic_only_full_board_b_still_requires_all_root_rc_spa",
        "primary_blocker": "no swept horizon has positive lower-bound edge versus same-coin controls" if not passed else "diagnostic horizon candidate only",
        "next_action": "B2R-repeat: direct Manipulation horizon sweep failed; switch source/family or source-owned exits before promotion." if not passed else "B2R-repeat: use passing horizon only as later five-root RC-SPA input; no downstream promotion from this diagnostic alone.",
    }
    return summaries, decision


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)
    source_report = json.loads(SOURCE_REPORT.read_text(encoding="utf-8"))
    summaries, decision = summarize()
    report = {
        "run_id": RUN_ID,
        "schema_version": "board-b-mehrnoom-binance-horizon-sweep/v1",
        "source_bridge_run_id": source_report["run_id"],
        "source_rows": rel(SOURCE_ROWS),
        "decision": decision,
        "summary": summaries,
        "artifacts": {
            "report_json": rel(REPORT_JSON),
            "report_md": rel(REPORT_MD),
            "summary_csv": rel(SUMMARY_CSV),
            "assertions": rel(ASSERTIONS),
        },
    }
    write_csv(SUMMARY_CSV, summaries)
    REPORT_JSON.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    lines = [
        "# Mehrnoom Binance Intraday Horizon Sweep v1",
        "",
        f"Run ID: `{RUN_ID}`",
        "",
        "## Decision",
        "",
        f"- Gate result: `{decision['gate_result']}`",
        f"- Best horizon: `{decision['best_horizon_hours']}h`",
        f"- Best positive-control diff: `{decision['best_positive_minus_control_return']:.6f}`",
        f"- Best LCB 5%: `{decision['best_positive_minus_control_lcb_5pct']:.6f}`",
        f"- Horizons passed: `{decision['horizons_passed']}`",
        f"- Downstream consumption: `{decision['downstream_consumption']}`",
        "",
        "## Horizon Summary",
        "",
        "| Horizon | Pos Rows | Ctrl Rows | Folds | Pos Mean | Ctrl Mean | Diff | LCB 5% | Fold+ | Gate |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in summaries:
        lines.append(
            f"| {row['horizon_hours']} | {row['positive_rows']} | {row['control_rows']} | {row['monthly_folds']} | "
            f"{row['positive_mean_return']:.6f} | {row['control_mean_return']:.6f} | "
            f"{row['positive_minus_control_return']:.6f} | {row['positive_minus_control_lcb_5pct']:.6f} | "
            f"{row['fold_positive_rate_vs_control']:.4f} | `{row['gate_result']}` |"
        )
    lines.extend(
        [
            "",
            "## Artifacts",
            "",
            f"- JSON: `{rel(REPORT_JSON)}`",
            f"- Summary CSV: `{rel(SUMMARY_CSV)}`",
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
                f"best_horizon_hours={decision['best_horizon_hours']}",
                f"best_positive_minus_control_return={decision['best_positive_minus_control_return']:.10f}",
                f"best_positive_minus_control_lcb_5pct={decision['best_positive_minus_control_lcb_5pct']:.10f}",
                f"horizons_passed={','.join(str(x) for x in decision['horizons_passed'])}",
                f"promotion_allowed_for_full_board_b={decision['promotion_allowed_for_full_board_b']}",
                f"artifacts_exist={REPORT_JSON.exists() and REPORT_MD.exists() and SUMMARY_CSV.exists()}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    print(json.dumps(decision, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
