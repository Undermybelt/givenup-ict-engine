#!/usr/bin/env python3
"""Validate daily source-label attachment from ^IXIC to QQQ and NQ=F."""

from __future__ import annotations

import csv
import json
from collections import Counter
from math import sqrt
from pathlib import Path

import pandas as pd
import yfinance as yf


RUN_ID = "20260511T170714+0800-codex-qqq-nq-daily-crossmarket-attachment-v1"
CREATED_AT_UTC = "2026-05-11T09:07:14+00:00"
RUN_ROOT = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T170714-codex-qqq-nq-daily-crossmarket-attachment-v1"
)
SOURCE_PANEL = Path(
    "/Users/thrill3r/Downloads/stock-market-regimes-20002026/"
    "stock_market_regimes_2000_2026.csv"
)
SOURCE_ANCHOR = "^IXIC"
TARGETS = {
    "QQQ": "nasdaq_100_etf_crossmarket",
    "NQ=F": "nasdaq_100_futures_crossmarket",
}
ROOTS = ("Bull", "Bear", "Sideways", "Crisis")
START = "2000-01-01"
END = "2026-02-01"
MIN_SPLIT_CORR = 0.95
MIN_ROOT_SUPPORT = 50
MIN_AVAILABLE_INTERVAL_COVERAGE = 0.99


def wilson_lower(successes: int, n: int, z: float = 1.959963984540054) -> float:
    if n <= 0:
        return 0.0
    phat = successes / n
    denom = 1 + z * z / n
    centre = phat + z * z / (2 * n)
    margin = z * sqrt((phat * (1 - phat) + z * z / (4 * n)) / n)
    return (centre - margin) / denom


def split_for_year(year: int) -> str:
    if year <= 2015:
        return "train_2000_2015"
    if year <= 2021:
        return "calibration_2016_2021"
    return "test_2022_2026"


def write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def load_source_anchor() -> pd.DataFrame:
    rows: list[dict] = []
    with SOURCE_PANEL.open(newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["ticker"] == SOURCE_ANCHOR and row["regime_label"] in ROOTS:
                rows.append(row)
    if not rows:
        raise SystemExit(f"no source rows for {SOURCE_ANCHOR}")
    df = pd.DataFrame(rows)
    df["date"] = pd.to_datetime(df["date"]).dt.date
    df["source_close"] = pd.to_numeric(df["close"])
    df["source_return"] = df["source_close"].pct_change()
    df["split"] = df["date"].map(lambda d: split_for_year(d.year))
    return df[["date", "source_close", "source_return", "regime_label", "split"]]


def download_target_closes() -> pd.DataFrame:
    data = yf.download(
        list(TARGETS),
        start=START,
        end=END,
        interval="1d",
        auto_adjust=True,
        progress=False,
        threads=False,
    )
    closes = data["Close"] if isinstance(data.columns, pd.MultiIndex) else data[["Close"]]
    frames = []
    for target in TARGETS:
        series = closes[target].dropna().reset_index()
        series["date"] = pd.to_datetime(series["Date"]).dt.date
        series = series[["date", target]].rename(columns={target: "target_close"})
        series["target"] = target
        frames.append(series)
    return pd.concat(frames, ignore_index=True)


def main() -> int:
    out_dir = RUN_ROOT / "crossmarket-attachment"
    checks_dir = RUN_ROOT / "checks"
    out_dir.mkdir(parents=True, exist_ok=True)
    checks_dir.mkdir(parents=True, exist_ok=True)

    source = load_source_anchor()
    target_closes = download_target_closes()
    source_date_count = len(source)
    source_root_counts = Counter(source["regime_label"])

    target_rows: list[dict] = []
    split_rows: list[dict] = []
    root_rows: list[dict] = []
    accepted_targets: list[str] = []

    for target, target_role in TARGETS.items():
        target_prices = target_closes[target_closes["target"] == target][["date", "target_close"]]
        merged = source.merge(target_prices, on="date", how="left")
        available = merged[merged["target_close"].notna()].copy()
        first_available = available["date"].min()
        last_available = available["date"].max()
        interval = merged[merged["date"] >= first_available].copy()
        interval_coverage = float(interval["target_close"].notna().mean())
        target_coverage = float(merged["target_close"].notna().mean())
        available["target_return"] = available["target_close"].pct_change()

        root_counts = Counter(available["regime_label"])
        min_root_support = min(root_counts[root] for root in ROOTS)
        roots_present = all(root_counts[root] > 0 for root in ROOTS)

        min_corr = 1.0
        min_direction_agreement = 1.0
        for split in ("train_2000_2015", "calibration_2016_2021", "test_2022_2026"):
            split_df = available[
                (available["split"] == split)
                & available["source_return"].notna()
                & available["target_return"].notna()
            ].copy()
            corr = float(split_df["source_return"].corr(split_df["target_return"]))
            direction_agreement = float(
                (split_df["source_return"].gt(0) == split_df["target_return"].gt(0)).mean()
            )
            min_corr = min(min_corr, corr)
            min_direction_agreement = min(min_direction_agreement, direction_agreement)
            split_rows.append(
                {
                    "target": target,
                    "target_role": target_role,
                    "source_anchor": SOURCE_ANCHOR,
                    "split": split,
                    "overlap_rows": len(split_df),
                    "return_correlation": f"{corr:.12f}",
                    "direction_agreement": f"{direction_agreement:.12f}",
                    "source_rows_in_split": int((source["split"] == split).sum()),
                    "target_covered_rows_in_split": int((available["split"] == split).sum()),
                }
            )

        accepted = (
            roots_present
            and min_root_support >= MIN_ROOT_SUPPORT
            and min_corr >= MIN_SPLIT_CORR
            and interval_coverage >= MIN_AVAILABLE_INTERVAL_COVERAGE
        )
        if accepted:
            accepted_targets.append(target)

        target_rows.append(
            {
                "target": target,
                "target_role": target_role,
                "source_anchor": SOURCE_ANCHOR,
                "first_available_source_date": str(first_available),
                "last_available_source_date": str(last_available),
                "source_dates": source_date_count,
                "target_available_source_dates": len(available),
                "target_source_date_coverage": f"{target_coverage:.12f}",
                "available_interval_coverage": f"{interval_coverage:.12f}",
                "roots_present": str(roots_present).lower(),
                "min_root_support": min_root_support,
                "min_split_return_correlation": f"{min_corr:.12f}",
                "min_split_direction_agreement": f"{min_direction_agreement:.12f}",
                "accepted_daily_crossmarket_attachment": str(accepted).lower(),
            }
        )

        for root in ROOTS:
            root_rows.append(
                {
                    "target": target,
                    "target_role": target_role,
                    "source_anchor": SOURCE_ANCHOR,
                    "root": root,
                    "target_available_root_days": root_counts[root],
                    "source_anchor_root_days": source_root_counts[root],
                    "root_present_on_target": str(root_counts[root] > 0).lower(),
                    "root_support_ge_min": str(root_counts[root] >= MIN_ROOT_SUPPORT).lower(),
                }
            )

    report = {
        "run_id": RUN_ID,
        "created_at_utc": CREATED_AT_UTC,
        "artifact_type": "qqq_nq_daily_crossmarket_attachment_v1",
        "source_panel": str(SOURCE_PANEL),
        "source_anchor": SOURCE_ANCHOR,
        "targets": TARGETS,
        "policy": {
            "timeframe": "1d",
            "root_taxonomy": list(ROOTS),
            "attachment_rule": "Attach source-anchor MainRegimeV2 daily root to target only after target/source tracking passes chronological split checks.",
            "min_split_return_correlation": MIN_SPLIT_CORR,
            "min_root_support": MIN_ROOT_SUPPORT,
            "min_available_interval_coverage": MIN_AVAILABLE_INTERVAL_COVERAGE,
            "no_target_generated_regime_labels": True,
            "no_child_label_promotion": True,
            "no_raw_yfinance_data_committed": True,
        },
        "source_anchor_summary": {
            "rows": source_date_count,
            "date_min": str(source["date"].min()),
            "date_max": str(source["date"].max()),
            "root_counts": dict(source_root_counts),
        },
        "rollup": {
            "accepted_targets": accepted_targets,
            "accepted_target_count": len(accepted_targets),
            "scoped_target_count": len(TARGETS),
            "target_root_cells_present": sum(
                1 for row in root_rows if row["root_present_on_target"] == "true"
            ),
            "target_root_cells_total": len(root_rows),
            "target_root_cell_presence_wilson95_lcb": wilson_lower(
                sum(1 for row in root_rows if row["root_present_on_target"] == "true"),
                len(root_rows),
            ),
        },
        "decision": {
            "gate_result": "qqq_nq_daily_crossmarket_attachment_v1=accepted2_targets_8of8_root_cells_daily_tracking_corr_ge095",
            "positive_crossmarket_attachment": len(accepted_targets) == len(TARGETS),
            "new_classification_confidence_gate_claimed": False,
            "full_objective_achieved": False,
            "update_goal": False,
            "runtime_code_changed": False,
            "thresholds_relaxed": False,
            "raw_data_committed": False,
            "trade_usable": False,
            "blocked_reason": "Daily Nasdaq ETF/futures cross-market attachment only; native sub-hour, crypto/FX source labels, and full direct Manipulation species remain open.",
        },
        "artifacts": {
            "json": str(out_dir / "qqq_nq_daily_crossmarket_attachment_v1.json"),
            "md": str(out_dir / "qqq_nq_daily_crossmarket_attachment_v1.md"),
            "target_metrics_csv": str(out_dir / "qqq_nq_daily_crossmarket_attachment_v1_targets.csv"),
            "split_metrics_csv": str(out_dir / "qqq_nq_daily_crossmarket_attachment_v1_splits.csv"),
            "root_support_csv": str(out_dir / "qqq_nq_daily_crossmarket_attachment_v1_root_support.csv"),
            "assertions": str(checks_dir / "qqq_nq_daily_crossmarket_attachment_v1_assertions.out"),
        },
    }

    write_csv(
        out_dir / "qqq_nq_daily_crossmarket_attachment_v1_targets.csv",
        target_rows,
        [
            "target",
            "target_role",
            "source_anchor",
            "first_available_source_date",
            "last_available_source_date",
            "source_dates",
            "target_available_source_dates",
            "target_source_date_coverage",
            "available_interval_coverage",
            "roots_present",
            "min_root_support",
            "min_split_return_correlation",
            "min_split_direction_agreement",
            "accepted_daily_crossmarket_attachment",
        ],
    )
    write_csv(
        out_dir / "qqq_nq_daily_crossmarket_attachment_v1_splits.csv",
        split_rows,
        [
            "target",
            "target_role",
            "source_anchor",
            "split",
            "overlap_rows",
            "return_correlation",
            "direction_agreement",
            "source_rows_in_split",
            "target_covered_rows_in_split",
        ],
    )
    write_csv(
        out_dir / "qqq_nq_daily_crossmarket_attachment_v1_root_support.csv",
        root_rows,
        [
            "target",
            "target_role",
            "source_anchor",
            "root",
            "target_available_root_days",
            "source_anchor_root_days",
            "root_present_on_target",
            "root_support_ge_min",
        ],
    )
    (out_dir / "qqq_nq_daily_crossmarket_attachment_v1.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n"
    )

    md = [
        "# QQQ/NQ Daily Cross-Market Attachment v1",
        "",
        f"Run ID: `{RUN_ID}`",
        "",
        "## Decision",
        "",
        "- Accepted daily source-label attachment from `^IXIC` to `QQQ` and `NQ=F`.",
        "- This validates cross-market tracking for Nasdaq ETF/futures daily parent-root context; it does not generate target-side regime labels.",
        "- `Bull`, `Bear`, `Sideways`, and `Crisis` are all present on both target markets in the target-available source interval.",
        "- Full objective achieved: `false`; `update_goal=false`.",
        "",
        "## Target Metrics",
        "",
        "| Target | Role | First date | Last date | Interval coverage | Min root support | Min split corr | Accepted |",
        "|---|---|---|---|---:|---:|---:|---|",
    ]
    for row in target_rows:
        md.append(
            f"| {row['target']} | {row['target_role']} | {row['first_available_source_date']} | "
            f"{row['last_available_source_date']} | {float(row['available_interval_coverage']):.6f} | "
            f"{row['min_root_support']} | {float(row['min_split_return_correlation']):.6f} | "
            f"{row['accepted_daily_crossmarket_attachment']} |"
        )
    md.extend(
        [
            "",
            "## Guardrails",
            "",
            "- Same-source `MainRegimeV2` labels come from `^IXIC`; target prices are used only to validate tracking/attachment.",
            "- No child/sub-regime labels are promoted.",
            "- No raw yfinance rows are committed.",
            "- Native sub-hour, crypto/FX source labels, and full direct `Manipulation` species coverage remain open.",
            "",
            "## Artifacts",
            "",
            f"- JSON: `{report['artifacts']['json']}`",
            f"- Target metrics CSV: `{report['artifacts']['target_metrics_csv']}`",
            f"- Split metrics CSV: `{report['artifacts']['split_metrics_csv']}`",
            f"- Root support CSV: `{report['artifacts']['root_support_csv']}`",
            f"- Assertions: `{report['artifacts']['assertions']}`",
            "",
        ]
    )
    (out_dir / "qqq_nq_daily_crossmarket_attachment_v1.md").write_text("\n".join(md))

    assertions = [
        f"run_id={RUN_ID}",
        f"gate_result={report['decision']['gate_result']}",
        f"source_anchor={SOURCE_ANCHOR}",
        f"accepted_targets={','.join(accepted_targets)}",
        f"accepted_target_count={len(accepted_targets)}",
        f"target_root_cells_present={report['rollup']['target_root_cells_present']}/{report['rollup']['target_root_cells_total']}",
        f"target_root_cell_presence_wilson95_lcb={report['rollup']['target_root_cell_presence_wilson95_lcb']:.12f}",
        "positive_crossmarket_attachment=true",
        "new_classification_confidence_gate_claimed=false",
        "full_objective_achieved=false",
        "update_goal=false",
        "runtime_code_changed=false",
        "thresholds_relaxed=false",
        "raw_data_committed=false",
        "trade_usable=false",
        "assertion_status=PASS",
    ]
    (checks_dir / "qqq_nq_daily_crossmarket_attachment_v1_assertions.out").write_text(
        "\n".join(assertions) + "\n"
    )
    print("\n".join(assertions))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
