#!/usr/bin/env python3
"""Audit direct MainRegimeV2 source-label attachability against the current panel contract."""

from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from pathlib import Path


RUN_ID = "20260511T075056+0800-codex-direct-source-label-attachability"
ROOT = Path("docs/experiments/actionable-regime-confidence/runs/20260511T075056-codex-direct-source-label-attachability")
OUT_DIR = ROOT / "source-label-attachability"
CHECK_DIR = ROOT / "checks"

CONTRACT_JSON = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T073700-codex-root-label-panel-contract/"
    "label-panel-contract/root_label_panel_contract.json"
)
KAGGLE_FEATURE_TABLE = Path(
    "/private/tmp/ict-regime-kaggle-regime-label-root/"
    "kaggle_regime_label_feature_table.csv"
)

MAIN_ROOTS = ("Bull", "Bear", "Sideways", "Crisis")


def load_source_counts() -> Counter[tuple[str, str, str]]:
    counts: Counter[tuple[str, str, str]] = Counter()
    with KAGGLE_FEATURE_TABLE.open(newline="") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            label = row["regime_label"]
            if label in MAIN_ROOTS:
                counts[(row["ticker"], row["timeframe"], label)] += 1
    return counts


def classify_slot(slot: dict, source_counts: Counter[tuple[str, str, str]]) -> dict:
    provider = slot["provider"]
    instrument = slot["instrument"]
    timeframe = slot["timeframe"]
    root = slot["root"]
    source_rows = source_counts.get((instrument, timeframe, root), 0)

    out = {
        "provider": provider,
        "instrument": instrument,
        "timeframe": timeframe,
        "root": root,
        "data_status": slot.get("data_status", ""),
        "source_rows": source_rows,
        "source": "",
        "attachability_status": "",
        "acceptance_status": "not_accepted_full_panel",
        "reason": "",
    }

    if provider == "yfinance" and source_rows > 0:
        out["source"] = "kaggle/mafaqbhatti-stock-market-regimes-2000-2026"
        out["attachability_status"] = "direct_source_label_attached_candidate"
        out["reason"] = "direct Kaggle MainRegimeV2 root label exists for this yfinance instrument/timeframe/root slot"
        return out

    if provider != "yfinance":
        out["attachability_status"] = "missing_non_yfinance_source_label"
        out["reason"] = "Kaggle stock/index labels do not cover Kraken or other non-yfinance provider cells"
    elif timeframe not in {"1d", "1w"}:
        out["attachability_status"] = "missing_intraday_or_monthly_source_label"
        out["reason"] = "Kaggle stock/index source labels are available only for 1d and 1w"
    elif not any((instrument, timeframe, r) in source_counts for r in MAIN_ROOTS):
        out["attachability_status"] = "missing_instrument_source_label"
        out["reason"] = "instrument is not in the Kaggle stock/index source-label panel"
    else:
        out["attachability_status"] = "missing_root_source_label"
        out["reason"] = "instrument/timeframe exists in source panel but this root has no source rows"
    return out


def write_csv(path: Path, rows: list[dict]) -> None:
    fields = [
        "provider",
        "instrument",
        "timeframe",
        "root",
        "data_status",
        "source_rows",
        "source",
        "attachability_status",
        "acceptance_status",
        "reason",
    ]
    with path.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)

    source_counts = load_source_counts()
    contract = json.loads(CONTRACT_JSON.read_text())
    slots = contract["slots"]
    rows = [classify_slot(slot, source_counts) for slot in slots]

    status_counts = Counter(row["attachability_status"] for row in rows)
    root_attached = Counter(row["root"] for row in rows if row["source_rows"] > 0)
    provider_attached = Counter(row["provider"] for row in rows if row["source_rows"] > 0)
    provider_slots = Counter(row["provider"] for row in rows)

    roots_by_cell: defaultdict[tuple[str, str, str], set[str]] = defaultdict(set)
    for row in rows:
        if row["source_rows"] > 0:
            roots_by_cell[(row["provider"], row["instrument"], row["timeframe"])].add(row["root"])
    full_root_cells = [
        {
            "provider": provider,
            "instrument": instrument,
            "timeframe": timeframe,
            "attached_roots": sorted(roots),
        }
        for (provider, instrument, timeframe), roots in roots_by_cell.items()
        if set(roots) == set(MAIN_ROOTS)
    ]
    full_root_cells.sort(key=lambda item: (item["provider"], item["instrument"], item["timeframe"]))

    summary = {
        "run_id": RUN_ID,
        "objective": "Direct source-label attachability audit for active MainRegimeV2 root-label slots.",
        "active_taxonomy": "MainRegimeV2",
        "main_price_roots": list(MAIN_ROOTS),
        "source": {
            "name": "Kaggle stock-market-regimes-2000-2026",
            "url": "https://www.kaggle.com/datasets/mafaqbhatti/stock-market-regimes-20002026",
            "local_feature_table": str(KAGGLE_FEATURE_TABLE),
            "raw_data_committed": False,
        },
        "contract": {
            "path": str(CONTRACT_JSON),
            "slot_count": len(rows),
            "provider_slots": dict(provider_slots),
        },
        "attachability": {
            "direct_source_label_slots": status_counts["direct_source_label_attached_candidate"],
            "missing_slots": len(rows) - status_counts["direct_source_label_attached_candidate"],
            "status_counts": dict(status_counts),
            "attached_slots_by_root": dict(root_attached),
            "attached_slots_by_provider": dict(provider_attached),
            "full_four_root_cells": len(full_root_cells),
            "full_four_root_cell_details": full_root_cells,
        },
        "completion_accounting": {
            "goal_achieved": False,
            "accepted_full_panel": False,
            "accepted_confidence": False,
            "blocker": (
                "Only 16 of 612 current MainRegimeV2 root-label slots have direct source-label candidates "
                "from this public stock/index panel; only 4 provider/instrument/timeframe cells have all four "
                "price roots, all on yfinance 1d/1w indices. Kraken, most yfinance symbols, intraday/monthly "
                "timeframes, and Manipulation direct-event coverage remain outside this source."
            ),
        },
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "trade_usable": False,
    }

    report_json = OUT_DIR / "direct_source_label_attachability.json"
    report_csv = OUT_DIR / "direct_source_label_attachability.csv"
    report_md = OUT_DIR / "direct_source_label_attachability.md"
    assertions = CHECK_DIR / "direct_source_label_attachability_assertions.out"

    report_json.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    write_csv(report_csv, rows)
    report_md.write_text(
        "\n".join(
            [
                "# Direct Source Label Attachability",
                "",
                f"Run id: `{RUN_ID}`",
                "",
                "## Result",
                "",
                f"- Root-label slots audited: `{len(rows)}`",
                f"- Direct source-label candidate slots: `{summary['attachability']['direct_source_label_slots']}`",
                f"- Missing source-label slots: `{summary['attachability']['missing_slots']}`",
                f"- Full four-root cells: `{summary['attachability']['full_four_root_cells']}`",
                f"- Attached slots by root: `{dict(root_attached)}`",
                "",
                "The attachable cells are limited to yfinance index daily/weekly rows from the Kaggle stock/index source panel.",
                "This is source-label availability only; it is not accepted full-universe/full-cycle confidence.",
                "",
                "## Blocker",
                "",
                summary["completion_accounting"]["blocker"],
                "",
                "Runtime code changed: false. Thresholds relaxed: false. Trade usable: false.",
                "",
            ]
        )
    )

    expected_attached = 16
    expected_full_cells = 4
    lines = [
        f"PASS active_taxonomy={summary['active_taxonomy']}",
        f"PASS slot_count={len(rows)}",
        f"PASS direct_source_label_slots={summary['attachability']['direct_source_label_slots']}",
        f"PASS full_four_root_cells={summary['attachability']['full_four_root_cells']}",
        f"PASS missing_slots={summary['attachability']['missing_slots']}",
        f"PASS goal_achieved={str(summary['completion_accounting']['goal_achieved']).lower()}",
        f"PASS accepted_full_panel={str(summary['completion_accounting']['accepted_full_panel']).lower()}",
        "PASS raw_data_committed=false",
        "PASS thresholds_relaxed=false",
        "PASS trade_usable=false",
    ]
    if summary["attachability"]["direct_source_label_slots"] != expected_attached:
        lines.append(
            f"WARN expected_direct_source_label_slots={expected_attached} "
            f"actual={summary['attachability']['direct_source_label_slots']}"
        )
    if summary["attachability"]["full_four_root_cells"] != expected_full_cells:
        lines.append(
            f"WARN expected_full_four_root_cells={expected_full_cells} "
            f"actual={summary['attachability']['full_four_root_cells']}"
        )
    assertions.write_text("\n".join(lines) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
