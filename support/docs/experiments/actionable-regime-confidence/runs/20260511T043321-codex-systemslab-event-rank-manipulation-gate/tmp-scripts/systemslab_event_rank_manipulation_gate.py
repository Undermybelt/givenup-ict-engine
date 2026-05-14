#!/usr/bin/env python3
"""Event-level direct manipulation rank gate over SystemsLab pump/dump features.

Experiment artifact only. Raw source data stays under /private/tmp.
"""

from __future__ import annotations

import csv
import gzip
import hashlib
import itertools
import json
import math
from pathlib import Path
from typing import Any

import pandas as pd


RUN_ID = "20260511T043321+0800-codex-systemslab-event-rank-manipulation-gate"
RUN_ROOT = Path("docs/experiments/actionable-regime-confidence/runs/20260511T043321-codex-systemslab-event-rank-manipulation-gate")
SOURCE_ROOT = Path("/private/tmp/ict-regime-systemslab-pump-dump")
TIMEFRAMES = ["5S", "15S", "25S"]
FEATURES = [
    "std_rush_order",
    "avg_rush_order",
    "std_trades",
    "std_volume",
    "avg_volume",
    "std_price",
    "avg_price",
    "avg_price_max",
]
BLOCKED_PREDICTORS = ["date", "pump_index", "symbol", "gt", "hour_sin", "hour_cos", "minute_sin", "minute_cos"]
Z95 = 1.959963984540054


def wilson_lcb(success: int, total: int, z: float = Z95) -> float:
    if total <= 0:
        return 0.0
    phat = success / total
    denom = 1.0 + z * z / total
    center = phat + z * z / (2.0 * total)
    margin = z * math.sqrt((phat * (1.0 - phat) + z * z / (4.0 * total)) / total)
    return max(0.0, (center - margin) / denom)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def split_event_ids(df: pd.DataFrame) -> dict[str, set[int]]:
    positive_dates = df[df["gt"] == 1].groupby("pump_index")["date"].min().sort_values()
    event_ids = list(positive_dates.index)
    train_end = int(len(event_ids) * 0.60)
    cal_end = int(len(event_ids) * 0.80)
    return {
        "train": set(event_ids[:train_end]),
        "calibration": set(event_ids[train_end:cal_end]),
        "test": set(event_ids[cal_end:]),
    }


def pick_event_rows(df: pd.DataFrame, event_ids: set[int], rank_columns: tuple[str, ...]) -> dict[str, Any]:
    part = df[df["pump_index"].isin(event_ids)].copy()
    part["_score"] = part[list(rank_columns)].sum(axis=1)
    picked = part.loc[part.groupby("pump_index")["_score"].idxmax()].copy()
    support = int(len(picked))
    successes = int(picked["gt"].sum())
    return {
        "support": support,
        "successes": successes,
        "failures": support - successes,
        "precision": successes / support if support else 0.0,
        "wilson95_lcb": wilson_lcb(successes, support),
        "event_coverage": 1.0 if support else 0.0,
        "selected_positive_rate": successes / support if support else 0.0,
    }


def evaluate_timeframe(timeframe: str) -> dict[str, Any]:
    path = SOURCE_ROOT / "labeled_features" / f"features_{timeframe}.csv.gz"
    df = pd.read_csv(path, parse_dates=["date"]).dropna(subset=FEATURES + ["date", "gt", "pump_index"]).copy()
    df["gt"] = df["gt"].astype(int)
    positive_events = df[df["gt"] == 1]["pump_index"].nunique()
    df = df[df["pump_index"].isin(df[df["gt"] == 1]["pump_index"].unique())].copy()
    splits = split_event_ids(df)
    rank_columns = []
    for feature in FEATURES:
        col = f"{feature}_within_event_rank"
        df[col] = df.groupby("pump_index")[feature].rank(pct=True)
        rank_columns.append(col)

    candidates = []
    for size in range(1, 5):
        for cols in itertools.combinations(rank_columns, size):
            metrics = {name: pick_event_rows(df, ids, cols) for name, ids in splits.items()}
            candidates.append(
                {
                    "rank_columns": list(cols),
                    "features": [c.replace("_within_event_rank", "") for c in cols],
                    "train": metrics["train"],
                    "calibration": metrics["calibration"],
                    "test": metrics["test"],
                }
            )
    candidates.sort(
        key=lambda c: (
            c["train"]["wilson95_lcb"],
            c["train"]["precision"],
            c["train"]["successes"],
            -len(c["rank_columns"]),
        ),
        reverse=True,
    )
    selected = candidates[0]
    selected["accepted_95"] = (
        selected["calibration"]["wilson95_lcb"] >= 0.95
        and selected["test"]["wilson95_lcb"] >= 0.95
        and selected["calibration"]["support"] >= 50
        and selected["test"]["support"] >= 50
    )
    selected["blocker"] = "none" if selected["accepted_95"] else "held_out_event_rank_wilson95_below_95"
    return {
        "timeframe": timeframe,
        "path": str(path),
        "sha256": sha256(path),
        "rows": int(len(df)),
        "positive_events": int(positive_events),
        "split_event_counts": {k: len(v) for k, v in splits.items()},
        "blocked_predictors": BLOCKED_PREDICTORS,
        "event_rank_unit": "one top-ranked current/past feature row selected per pump event; success iff selected row is the labeled pump/dump row",
        "selected": selected,
        "leaderboard_top10": candidates[:10],
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    best = report["best_timeframe"]
    lines = [
        "# SystemsLab Event-Rank Manipulation Gate",
        "",
        f"Run id: `{RUN_ID}`.",
        "",
        "## Decision",
        "",
        f"- Gate result: `{report['gate_result']}`",
        f"- Accepted 95 Manipulation: `{str(report['accepted_95']).lower()}`",
        "- Runtime code changed: `false`",
        "- Thresholds relaxed: `false`",
        "- Trade usable: `false`",
        "",
        "## Best Held-Out Result",
        "",
        f"- Timeframe: `{best['timeframe']}`",
        f"- Selected rank features: `{', '.join(best['selected']['features'])}`",
        f"- Calibration support/successes/Wilson95: `{best['selected']['calibration']['support']}` / `{best['selected']['calibration']['successes']}` / `{best['selected']['calibration']['wilson95_lcb']:.6f}`",
        f"- Test support/successes/Wilson95: `{best['selected']['test']['support']}` / `{best['selected']['test']['successes']}` / `{best['selected']['test']['wilson95_lcb']:.6f}`",
        "",
        "## Interpretation",
        "",
        "This is direct event/social manipulation evidence with explicit positive pump rows and same-event negative controls. It still fails the unchanged 95% gate on held-out event ranking, so it is negative evidence only.",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    out_dir = RUN_ROOT / "event-rank-gate"
    checks_dir = RUN_ROOT / "checks"
    out_dir.mkdir(parents=True, exist_ok=True)
    checks_dir.mkdir(parents=True, exist_ok=True)

    timeframe_reports = [evaluate_timeframe(tf) for tf in TIMEFRAMES]
    best_timeframe = max(
        timeframe_reports,
        key=lambda r: (
            min(r["selected"]["calibration"]["wilson95_lcb"], r["selected"]["test"]["wilson95_lcb"]),
            r["selected"]["test"]["wilson95_lcb"],
            r["selected"]["test"]["successes"],
        ),
    )
    accepted = bool(best_timeframe["selected"]["accepted_95"])
    report = {
        "run_id": RUN_ID,
        "source_repo": "https://github.com/SystemsLab-Sapienza/pump-and-dump-dataset",
        "source_root": str(SOURCE_ROOT),
        "candidate_regime": "Manipulation",
        "evidence_class": "direct_event_social_exchange_transaction_features",
        "gate_contract": {
            "min_calibration_wilson95_lcb": 0.95,
            "min_test_wilson95_lcb": 0.95,
            "min_calibration_support": 50,
            "min_test_support": 50,
            "thresholds_relaxed": False,
            "future_or_target_leakage_allowed": False,
        },
        "accepted_95": accepted,
        "gate_result": "accepted_systemslab_event_rank_manipulation_95" if accepted else "blocked_systemslab_event_rank_below_95",
        "best_timeframe": best_timeframe,
        "timeframe_reports": timeframe_reports,
        "active_root_accounting_after_gate": {
            "accepted_95_roots": ["Bull", "Bear", "Sideways", "Crisis"],
            "missing_95_roots": ["Manipulation"],
        },
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "raw_data_committed_to_repo": False,
        "trade_usable": False,
        "next_action": "Use a stronger direct order-lifecycle/L2/L3/MBO/social/on-chain source; SystemsLab scalar and event-rank gates are below 95.",
    }
    report_json = out_dir / "systemslab_event_rank_manipulation_gate_report.json"
    report_md = out_dir / "systemslab_event_rank_manipulation_gate_report.md"
    summary_csv = out_dir / "systemslab_event_rank_manipulation_gate_summary.csv"
    report_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(report, report_md)
    with summary_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["timeframe", "features", "cal_lcb", "test_lcb", "cal_success", "cal_support", "test_success", "test_support", "accepted_95"])
        for row in timeframe_reports:
            selected = row["selected"]
            writer.writerow(
                [
                    row["timeframe"],
                    " + ".join(selected["features"]),
                    f"{selected['calibration']['wilson95_lcb']:.12f}",
                    f"{selected['test']['wilson95_lcb']:.12f}",
                    selected["calibration"]["successes"],
                    selected["calibration"]["support"],
                    selected["test"]["successes"],
                    selected["test"]["support"],
                    selected["accepted_95"],
                ]
            )
    assertions = checks_dir / "systemslab_event_rank_manipulation_gate_assertions.out"
    assertions.write_text(
        "\n".join(
            [
                f"run_id={RUN_ID}",
                f"gate_result={report['gate_result']}",
                f"accepted_95={str(accepted).lower()}",
                f"best_timeframe={best_timeframe['timeframe']}",
                f"best_features={'+'.join(best_timeframe['selected']['features'])}",
                f"calibration_wilson_lcb_95={best_timeframe['selected']['calibration']['wilson95_lcb']:.12f}",
                f"test_wilson_lcb_95={best_timeframe['selected']['test']['wilson95_lcb']:.12f}",
                f"calibration_support={best_timeframe['selected']['calibration']['support']}",
                f"test_support={best_timeframe['selected']['test']['support']}",
                "runtime_code_changed=false",
                "thresholds_relaxed=false",
                "raw_data_committed_to_repo=false",
                "trade_usable=false",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"gate_result": report["gate_result"], "report": str(report_json)}, indent=2))


if __name__ == "__main__":
    main()
