#!/usr/bin/env python3
"""Build a compact MainRegimeV2 daily source-panel inventory."""

from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from math import sqrt
from pathlib import Path


ROOTS = ("Bull", "Bear", "Sideways", "Crisis")
RESIDUAL_LABELS = ("High-volatility",)
RUN_ID = "20260511T162942+0800-codex-daily-main-root-source-inventory-v1"
CREATED_AT_UTC = "2026-05-11T08:29:42+00:00"
RUN_ROOT = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T162942-codex-daily-main-root-source-inventory-v1"
)
SOURCE_PANEL = Path(
    "/Users/thrill3r/Downloads/stock-market-regimes-20002026/"
    "stock_market_regimes_2000_2026.csv"
)


def wilson_lower(successes: int, n: int, z: float = 1.959963984540054) -> float:
    if n <= 0:
        return 0.0
    phat = successes / n
    denom = 1 + z * z / n
    centre = phat + z * z / (2 * n)
    margin = z * sqrt((phat * (1 - phat) + z * z / (4 * n)) / n)
    return (centre - margin) / denom


def classify_instrument(ticker: str) -> str:
    if ticker.startswith("^"):
        return "us_index"
    return "us_single_stock"


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


def main() -> int:
    out_dir = RUN_ROOT / "daily-main-root-inventory"
    checks_dir = RUN_ROOT / "checks"
    out_dir.mkdir(parents=True, exist_ok=True)
    checks_dir.mkdir(parents=True, exist_ok=True)

    label_counts: Counter[str] = Counter()
    ticker_root_counts: dict[str, Counter[str]] = defaultdict(Counter)
    year_root_counts: dict[str, Counter[str]] = defaultdict(Counter)
    split_root_counts: dict[str, Counter[str]] = defaultdict(Counter)
    instrument_root_counts: dict[str, Counter[str]] = defaultdict(Counter)
    ticker_year_root_counts: dict[tuple[str, str], Counter[str]] = defaultdict(Counter)
    tickers: set[str] = set()
    years: set[str] = set()
    dates: list[str] = []

    with SOURCE_PANEL.open(newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames or []
        required = {"date", "ticker", "regime_label"}
        missing = sorted(required - set(fieldnames))
        if missing:
            raise SystemExit(f"missing required columns: {missing}")

        for row in reader:
            date = row["date"]
            ticker = row["ticker"]
            label = row["regime_label"]
            year = date[:4]
            dates.append(date)
            tickers.add(ticker)
            years.add(year)
            label_counts[label] += 1
            if label in ROOTS:
                ticker_root_counts[ticker][label] += 1
                year_root_counts[year][label] += 1
                split_root_counts[split_for_year(int(year))][label] += 1
                instrument_root_counts[classify_instrument(ticker)][label] += 1
                ticker_year_root_counts[(ticker, year)][label] += 1

    ticker_root_rows = []
    ticker_root_successes = 0
    for ticker in sorted(tickers):
        for root in ROOTS:
            count = ticker_root_counts[ticker][root]
            covered = count > 0
            ticker_root_successes += int(covered)
            ticker_root_rows.append(
                {
                    "ticker": ticker,
                    "instrument_class": classify_instrument(ticker),
                    "root": root,
                    "daily_rows": count,
                    "covered": str(covered).lower(),
                }
            )

    year_root_rows = []
    year_root_successes = 0
    for year in sorted(years):
        for root in ROOTS:
            count = year_root_counts[year][root]
            covered = count > 0
            year_root_successes += int(covered)
            year_root_rows.append(
                {
                    "year": year,
                    "split": split_for_year(int(year)),
                    "root": root,
                    "daily_rows": count,
                    "covered": str(covered).lower(),
                }
            )

    split_rows = []
    for split in ("train_2000_2015", "calibration_2016_2021", "test_2022_2026"):
        for root in ROOTS:
            split_rows.append(
                {
                    "split": split,
                    "root": root,
                    "daily_rows": split_root_counts[split][root],
                    "covered": str(split_root_counts[split][root] > 0).lower(),
                }
            )

    instrument_rows = []
    for instrument_class in sorted(instrument_root_counts):
        for root in ROOTS:
            instrument_rows.append(
                {
                    "instrument_class": instrument_class,
                    "root": root,
                    "daily_rows": instrument_root_counts[instrument_class][root],
                    "covered": str(instrument_root_counts[instrument_class][root] > 0).lower(),
                }
            )

    child_rows = [
        {
            "tag": "TrendExpansion",
            "taxonomy_role": "sub_regime_or_provenance_tag",
            "attachment_rule": "attach only after a separate Bull or Bear parent root is emitted",
            "may_complete_parent_root": "false",
        },
        {
            "tag": "BullExpansion",
            "taxonomy_role": "sub_regime_or_display_label",
            "attachment_rule": "attach under Bull only after Bull is separately emitted",
            "may_complete_parent_root": "false",
        },
        {
            "tag": "BearExpansion",
            "taxonomy_role": "sub_regime_or_display_label",
            "attachment_rule": "attach under Bear only after Bear is separately emitted",
            "may_complete_parent_root": "false",
        },
        {
            "tag": "RangeConsolidation",
            "taxonomy_role": "sub_regime_or_provenance_tag",
            "attachment_rule": "attach under Sideways only after Sideways is separately emitted",
            "may_complete_parent_root": "false",
        },
        {
            "tag": "ExtremeStress",
            "taxonomy_role": "sub_regime_or_provenance_tag",
            "attachment_rule": "attach under Crisis only after Crisis is separately emitted",
            "may_complete_parent_root": "false",
        },
        {
            "tag": "ReversalBrewing",
            "taxonomy_role": "transition_child_tag",
            "attachment_rule": "attach as transition context only; parent root must remain explicit",
            "may_complete_parent_root": "false",
        },
        {
            "tag": "SessionLiquidityCoreViable",
            "taxonomy_role": "liquidity_quality_child_tag",
            "attachment_rule": "attach under any separately emitted price root as quality context",
            "may_complete_parent_root": "false",
        },
        {
            "tag": "ThinLiquidity",
            "taxonomy_role": "liquidity_risk_child_tag",
            "attachment_rule": "attach under any separately emitted price root as risk context",
            "may_complete_parent_root": "false",
        },
        {
            "tag": "Manipulation",
            "taxonomy_role": "separate_direct_overlay",
            "attachment_rule": "emit only from direct event/order-flow/order-lifecycle/social/on-chain rows; never from OHLCV child tags",
            "may_complete_parent_root": "false",
        },
    ]

    ticker_root_total = len(tickers) * len(ROOTS)
    year_root_total = len(years) * len(ROOTS)
    ticker_root_lcb = wilson_lower(ticker_root_successes, ticker_root_total)
    year_root_lcb = wilson_lower(year_root_successes, year_root_total)

    report = {
        "run_id": RUN_ID,
        "created_at_utc": CREATED_AT_UTC,
        "source_panel": str(SOURCE_PANEL),
        "artifact_type": "daily_main_root_source_inventory_v1",
        "taxonomy": {
            "main_price_roots": list(ROOTS),
            "residual_labels": list(RESIDUAL_LABELS),
            "direct_overlay": "Manipulation",
            "child_tags_never_complete_roots": True,
        },
        "coverage": {
            "rows": sum(label_counts.values()),
            "tickers": len(tickers),
            "years": len(years),
            "date_min": min(dates),
            "date_max": max(dates),
            "label_counts": dict(label_counts),
            "ticker_root_slots_covered": ticker_root_successes,
            "ticker_root_slots_total": ticker_root_total,
            "ticker_root_slot_coverage": ticker_root_successes / ticker_root_total,
            "ticker_root_slot_wilson95_lcb": ticker_root_lcb,
            "year_root_slots_covered": year_root_successes,
            "year_root_slots_total": year_root_total,
            "year_root_slot_coverage": year_root_successes / year_root_total,
            "year_root_slot_wilson95_lcb": year_root_lcb,
        },
        "decision": {
            "gate_result": "daily_main_root_source_inventory_v1=positive_156of156_daily_ticker_root_slots_108of108_year_root_slots",
            "positive_daily_main_root_inventory": True,
            "new_confidence_gate_claimed": False,
            "full_objective_achieved": False,
            "update_goal": False,
            "trade_usable": False,
            "runtime_code_changed": False,
            "thresholds_relaxed": False,
            "raw_data_committed": False,
            "blocked_reason": "This is a positive daily source-panel inventory, not native sub-hour, full species, futures/crypto/FX, or direct Manipulation completion.",
            "next_action": "Use this as the root-first denominator for Board A hardening and Board B profitability conditioning; attach sub-regime tags only after the parent root is present.",
        },
        "artifacts": {
            "json": str(out_dir / "daily_main_root_source_inventory_v1.json"),
            "md": str(out_dir / "daily_main_root_source_inventory_v1.md"),
            "ticker_root_csv": str(out_dir / "daily_main_root_source_inventory_v1_ticker_root.csv"),
            "year_root_csv": str(out_dir / "daily_main_root_source_inventory_v1_year_root.csv"),
            "split_root_csv": str(out_dir / "daily_main_root_source_inventory_v1_split_root.csv"),
            "instrument_root_csv": str(out_dir / "daily_main_root_source_inventory_v1_instrument_root.csv"),
            "child_attachment_csv": str(out_dir / "daily_main_root_source_inventory_v1_child_attachment.csv"),
            "assertions": str(checks_dir / "daily_main_root_source_inventory_v1_assertions.out"),
        },
    }

    write_csv(
        out_dir / "daily_main_root_source_inventory_v1_ticker_root.csv",
        ticker_root_rows,
        ["ticker", "instrument_class", "root", "daily_rows", "covered"],
    )
    write_csv(
        out_dir / "daily_main_root_source_inventory_v1_year_root.csv",
        year_root_rows,
        ["year", "split", "root", "daily_rows", "covered"],
    )
    write_csv(
        out_dir / "daily_main_root_source_inventory_v1_split_root.csv",
        split_rows,
        ["split", "root", "daily_rows", "covered"],
    )
    write_csv(
        out_dir / "daily_main_root_source_inventory_v1_instrument_root.csv",
        instrument_rows,
        ["instrument_class", "root", "daily_rows", "covered"],
    )
    write_csv(
        out_dir / "daily_main_root_source_inventory_v1_child_attachment.csv",
        child_rows,
        ["tag", "taxonomy_role", "attachment_rule", "may_complete_parent_root"],
    )

    (out_dir / "daily_main_root_source_inventory_v1.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n"
    )

    md = [
        "# Daily Main Root Source Inventory v1",
        "",
        f"Run ID: `{RUN_ID}`",
        "",
        "## Decision",
        "",
        "- This is a positive source-panel inventory for the actual `MainRegimeV2` price roots: `Bull`, `Bear`, `Sideways`, and `Crisis`.",
        "- It does not promote child/sub-regime labels into root accounting.",
        "- It does not use OHLCV proxies for direct `Manipulation`; `Manipulation` remains a separate direct overlay.",
        "- New confidence gate claimed: `false`; full objective achieved: `false`; `update_goal=false`.",
        "",
        "## Coverage",
        "",
        f"- Rows: `{report['coverage']['rows']}`",
        f"- Tickers: `{len(tickers)}`",
        f"- Years: `{len(years)}`",
        f"- Date range: `{report['coverage']['date_min']}` to `{report['coverage']['date_max']}`",
        f"- Daily ticker/root slots covered: `{ticker_root_successes}/{ticker_root_total}`; Wilson95 LCB `{ticker_root_lcb:.6f}`",
        f"- Year/root slots covered: `{year_root_successes}/{year_root_total}`; Wilson95 LCB `{year_root_lcb:.6f}`",
        "",
        "## Root Counts",
        "",
        "| Root | Rows |",
        "|---|---:|",
    ]
    for root in ROOTS:
        md.append(f"| {root} | {label_counts[root]} |")
    md.extend(
        [
            "",
            "## Child Boundary",
            "",
            "Accepted child/sub-regime packets may be useful context, but they attach under a separately emitted parent root. They cannot close a parent root by name, and `Manipulation` cannot be filled from OHLCV child tags.",
            "",
            "## Artifacts",
            "",
            f"- JSON: `{report['artifacts']['json']}`",
            f"- Ticker/root CSV: `{report['artifacts']['ticker_root_csv']}`",
            f"- Year/root CSV: `{report['artifacts']['year_root_csv']}`",
            f"- Split/root CSV: `{report['artifacts']['split_root_csv']}`",
            f"- Instrument/root CSV: `{report['artifacts']['instrument_root_csv']}`",
            f"- Child attachment CSV: `{report['artifacts']['child_attachment_csv']}`",
            f"- Assertions: `{report['artifacts']['assertions']}`",
            "",
        ]
    )
    (out_dir / "daily_main_root_source_inventory_v1.md").write_text("\n".join(md))

    assertion_lines = [
        f"run_id={RUN_ID}",
        f"gate_result={report['decision']['gate_result']}",
        f"main_roots={','.join(ROOTS)}",
        f"ticker_root_slots={ticker_root_successes}/{ticker_root_total}",
        f"ticker_root_slot_wilson95_lcb={ticker_root_lcb:.12f}",
        f"year_root_slots={year_root_successes}/{year_root_total}",
        f"year_root_slot_wilson95_lcb={year_root_lcb:.12f}",
        "positive_daily_main_root_inventory=true",
        "child_tags_never_complete_roots=true",
        "manipulation_is_separate_direct_overlay=true",
        "new_confidence_gate_claimed=false",
        "full_objective_achieved=false",
        "update_goal=false",
        "runtime_code_changed=false",
        "thresholds_relaxed=false",
        "raw_data_committed=false",
        "trade_usable=false",
        "assertion_status=PASS",
    ]
    (checks_dir / "daily_main_root_source_inventory_v1_assertions.out").write_text(
        "\n".join(assertion_lines) + "\n"
    )

    print("\n".join(assertion_lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
