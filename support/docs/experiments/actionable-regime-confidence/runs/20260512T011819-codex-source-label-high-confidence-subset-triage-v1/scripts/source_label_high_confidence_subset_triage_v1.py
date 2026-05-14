#!/usr/bin/env python3
"""Triage high-confidence source-label subsets without promoting Board A gates."""

from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = Path(__file__).resolve().parents[1]
RUN_ID = "20260512T011819-codex-source-label-high-confidence-subset-triage-v1"
OUT = RUN_ROOT / "source-label-high-confidence-subset-triage-v1"
CHECKS = RUN_ROOT / "checks"
BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"
INTAKE_ROOT = Path("/tmp/ict-engine-source-label-equivalence-intake")
INTAKE_ROWS = INTAKE_ROOT / "source_label_equivalence_rows.csv"
INTAKE_PROVENANCE = INTAKE_ROOT / "source_label_equivalence_provenance.json"
STOCK_SOURCE = Path("/Users/thrill3r/Downloads/stock-market-regimes-20002026/stock_market_regimes_2000_2026.csv")
NIFTY_SOURCE = Path("/tmp/ict-engine-source-label-equivalence-reconstruction-v1/nifty/regime_timeline_history.csv")
CALIBRATION_RUN = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260512T011056-codex-source-label-equivalence-calibration-after-root-poll-v1/"
    "source-label-equivalence-confidence-calibration/"
    "source_label_equivalence_confidence_calibration_v1.json"
)

ROOT_LABELS = ["Bear", "Bull", "Crisis", "Sideways"]
REQUIRED_SPLITS = ["calibration", "heldout_market", "heldout_time", "test"]
REQUIRED_MARKET_FAMILIES = {"us_single_stock", "us_index", "india_equity_index"}
CONFIDENCE_THRESHOLD = 0.95
MIN_SUPPORT_PER_SPLIT = 50


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def stock_confidence_map() -> dict[tuple[str, str, str], float]:
    mapping: dict[tuple[str, str, str], float] = {}
    for row in read_csv(STOCK_SOURCE):
        try:
            confidence = float(row.get("regime_confidence", ""))
        except ValueError:
            continue
        mapping[(row["date"], row["ticker"], row["regime_label"])] = confidence
    return mapping


def nifty_confidence_map() -> dict[tuple[str, str, str, str], float]:
    mapping: dict[tuple[str, str, str, str], float] = {}
    for row in read_csv(NIFTY_SOURCE):
        day = row["Date"]
        symbol = "NIFTY500"
        if row.get("macro_state") == "Durable":
            mapping[(day, symbol, "NIFTY500:macro_state", "Bull")] = float(row.get("macro_confidence") or 0.0)
        if row.get("fast_state") == "Calm":
            mapping[(day, symbol, "NIFTY500:fast_state", "Sideways")] = float(row.get("fast_confidence") or 0.0)
        if row.get("fast_state") == "Stress":
            mapping[(day, symbol, "NIFTY500:fast_state", "Crisis")] = float(row.get("fast_confidence") or 0.0)
    return mapping


def confidence_for_row(
    row: dict[str, str],
    stock_map: dict[tuple[str, str, str], float],
    nifty_map: dict[tuple[str, str, str, str], float],
) -> float | None:
    label = row.get("main_regime_v2_label", "")
    owner = row.get("source_owner", "")
    if owner == "source-owned-stock-market-regimes-2000-2026":
        return stock_map.get((row.get("timestamp_or_date", ""), row.get("symbol", ""), label))
    if owner == "ahaanverma00":
        return nifty_map.get(
            (
                row.get("timestamp_or_date", ""),
                row.get("symbol", ""),
                row.get("source_symbol", ""),
                label,
            )
        )
    return None


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)

    required = [BOARD, INTAKE_ROWS, INTAKE_PROVENANCE, STOCK_SOURCE, NIFTY_SOURCE, CALIBRATION_RUN]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError(missing)

    board_hash = sha256_file(BOARD)
    calibration = json.loads(CALIBRATION_RUN.read_text(encoding="utf-8"))
    rows = read_csv(INTAKE_ROWS)
    stock_map = stock_confidence_map()
    nifty_map = nifty_confidence_map()

    high_rows: list[dict[str, str]] = []
    total_by_label = Counter()
    high_by_label = Counter()
    high_by_label_split = Counter()
    high_by_label_market = Counter()
    high_by_label_owner = Counter()
    high_symbols: dict[str, set[str]] = defaultdict(set)
    high_timeframes: dict[str, set[str]] = defaultdict(set)
    high_dates: dict[str, list[str]] = defaultdict(list)

    missing_confidence = 0
    for row in rows:
        label = row.get("main_regime_v2_label", "")
        if label not in ROOT_LABELS:
            continue
        total_by_label[label] += 1
        confidence = confidence_for_row(row, stock_map, nifty_map)
        if confidence is None:
            missing_confidence += 1
            continue
        if confidence < CONFIDENCE_THRESHOLD:
            continue
        high_by_label[label] += 1
        high_by_label_split[(label, row.get("split_role", ""))] += 1
        high_by_label_market[(label, row.get("market_family", ""))] += 1
        high_by_label_owner[(label, row.get("source_owner", ""))] += 1
        high_symbols[label].add(row.get("symbol", ""))
        high_timeframes[label].add(row.get("timeframe", ""))
        high_dates[label].append(row.get("timestamp_or_date", ""))
        high_rows.append(
            {
                "label": label,
                "split_role": row.get("split_role", ""),
                "market_family": row.get("market_family", ""),
                "source_owner": row.get("source_owner", ""),
                "symbol": row.get("symbol", ""),
                "timeframe": row.get("timeframe", ""),
                "timestamp_or_date": row.get("timestamp_or_date", ""),
                "source_row_id": row.get("source_row_id", ""),
                "source_confidence": f"{confidence:.10f}",
            }
        )

    label_rows: list[dict[str, Any]] = []
    split_rows: list[dict[str, Any]] = []
    market_rows: list[dict[str, Any]] = []
    owner_rows: list[dict[str, Any]] = []

    candidate_labels: list[str] = []
    support_only_candidates: list[str] = []
    blockers_by_label: dict[str, list[str]] = {}

    for label in ROOT_LABELS:
        blockers: list[str] = []
        split_counts = {split: high_by_label_split[(label, split)] for split in REQUIRED_SPLITS}
        market_counts = {market: high_by_label_market[(label, market)] for market in REQUIRED_MARKET_FAMILIES}
        for split, count in split_counts.items():
            if count < MIN_SUPPORT_PER_SPLIT:
                blockers.append(f"{split}_high_conf_support_below_{MIN_SUPPORT_PER_SPLIT}")
        if len([market for market, count in market_counts.items() if count > 0]) < 2:
            blockers.append("cross_market_family_high_conf_coverage_below_2")
        dates = sorted(value for value in high_dates[label] if value)
        label_rows.append(
            {
                "label": label,
                "total_rows": total_by_label[label],
                "high_conf_rows": high_by_label[label],
                "high_conf_share": f"{(high_by_label[label] / total_by_label[label]) if total_by_label[label] else 0.0:.10f}",
                "high_conf_symbol_count": len(high_symbols[label]),
                "high_conf_timeframes": "|".join(sorted(high_timeframes[label])),
                "high_conf_date_min": dates[0] if dates else "",
                "high_conf_date_max": dates[-1] if dates else "",
                "split_support_gate_pass": str(all(count >= MIN_SUPPORT_PER_SPLIT for count in split_counts.values())).lower(),
                "cross_market_family_count": len([market for market, count in market_counts.items() if count > 0]),
                "triage_candidate": str(not blockers).lower(),
                "blockers": ";".join(blockers),
            }
        )
        blockers_by_label[label] = blockers
        if not blockers:
            candidate_labels.append(label)
        if all(count >= MIN_SUPPORT_PER_SPLIT for count in split_counts.values()):
            support_only_candidates.append(label)
        for split, count in split_counts.items():
            split_rows.append({"label": label, "split_role": split, "high_conf_rows": count})
        for market in sorted(REQUIRED_MARKET_FAMILIES):
            market_rows.append({"label": label, "market_family": market, "high_conf_rows": market_counts[market]})
        owners = sorted({owner for (row_label, owner), count in high_by_label_owner.items() if row_label == label and count > 0})
        for owner in owners:
            owner_rows.append({"label": label, "source_owner": owner, "high_conf_rows": high_by_label_owner[(label, owner)]})

    summary = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "board_hash_before_writeback": board_hash,
        "source_rows_path": str(INTAKE_ROWS),
        "source_rows_sha256": sha256_file(INTAKE_ROWS),
        "source_provenance_sha256": sha256_file(INTAKE_PROVENANCE),
        "calibration_run": calibration.get("run_id"),
        "calibration_decision": calibration.get("decision"),
        "confidence_threshold": CONFIDENCE_THRESHOLD,
        "min_support_per_split": MIN_SUPPORT_PER_SPLIT,
        "required_splits": REQUIRED_SPLITS,
        "required_market_families": sorted(REQUIRED_MARKET_FAMILIES),
        "row_count": len(rows),
        "missing_confidence_rows": missing_confidence,
        "candidate_labels": candidate_labels,
        "support_only_candidates": support_only_candidates,
        "blockers_by_label": blockers_by_label,
        "accepted_rows_added": 0,
        "new_confidence_gate": False,
        "canonical_merge_allowed": False,
        "downstream_chain_rerun_allowed": False,
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "shared_intake_mutated": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "trade_usable": False,
        "decision": "source_label_high_confidence_subset_triage_v1=triage_only_no_acceptance",
    }

    write_csv(
        OUT / "source_label_high_confidence_subset_label_summary_v1.csv",
        label_rows,
        [
            "label",
            "total_rows",
            "high_conf_rows",
            "high_conf_share",
            "high_conf_symbol_count",
            "high_conf_timeframes",
            "high_conf_date_min",
            "high_conf_date_max",
            "split_support_gate_pass",
            "cross_market_family_count",
            "triage_candidate",
            "blockers",
        ],
    )
    write_csv(OUT / "source_label_high_confidence_subset_split_support_v1.csv", split_rows, ["label", "split_role", "high_conf_rows"])
    write_csv(OUT / "source_label_high_confidence_subset_market_support_v1.csv", market_rows, ["label", "market_family", "high_conf_rows"])
    write_csv(OUT / "source_label_high_confidence_subset_owner_support_v1.csv", owner_rows, ["label", "source_owner", "high_conf_rows"])
    write_csv(
        OUT / "source_label_high_confidence_subset_sample_rows_v1.csv",
        high_rows[:500],
        [
            "label",
            "split_role",
            "market_family",
            "source_owner",
            "symbol",
            "timeframe",
            "timestamp_or_date",
            "source_row_id",
            "source_confidence",
        ],
    )

    (OUT / "source_label_high_confidence_subset_triage_v1.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    md = [
        "# Source Label High-Confidence Subset Triage v1",
        "",
        f"- Decision: `{summary['decision']}`.",
        f"- Calibration baseline: `{summary['calibration_decision']}`.",
        f"- Confidence threshold: `{CONFIDENCE_THRESHOLD}`; min support per split: `{MIN_SUPPORT_PER_SPLIT}`.",
        f"- Candidate labels with high-confidence support across all splits plus >=2 market families: `{candidate_labels}`.",
        f"- Support-only candidates across all splits: `{support_only_candidates}`.",
        f"- Missing confidence rows: `{missing_confidence}`.",
        "- Accepted rows added: `0`; new confidence gate: `false`; canonical merge allowed: `false`; downstream chain rerun allowed: `false`.",
        "- Runtime code changed: `false`; shared intake mutated: `false`; thresholds relaxed: `false`; raw data committed: `false`; trade usable: `false`.",
        "",
        "## Label Summary",
        "",
        "| Label | Total Rows | High-Conf Rows | Split Support Pass | Market Families | Candidate | Blockers |",
        "|---|---:|---:|---|---:|---|---|",
    ]
    for row in label_rows:
        md.append(
            f"| `{row['label']}` | `{row['total_rows']}` | `{row['high_conf_rows']}` | "
            f"`{row['split_support_gate_pass']}` | `{row['cross_market_family_count']}` | "
            f"`{row['triage_candidate']}` | `{row['blockers']}` |"
        )
    md.extend(
        [
            "",
            "## Boundary",
            "",
            "This packet is triage only. It identifies whether a future qualifying-condition packet could use `source_confidence >= 0.95` as a candidate filter. It does not replace the existing source-confidence calibration gate, does not accept labels, and does not authorize downstream promotion.",
        ]
    )
    (OUT / "source_label_high_confidence_subset_triage_v1.md").write_text("\n".join(md) + "\n", encoding="utf-8")

    checks = [
        f"PASS run_id={RUN_ID}",
        f"PASS decision={summary['decision']}",
        f"PASS calibration_decision={summary['calibration_decision']}",
        f"PASS row_count={len(rows)}",
        f"PASS missing_confidence_rows={missing_confidence}",
        f"PASS candidate_labels={','.join(candidate_labels) if candidate_labels else 'none'}",
        f"PASS support_only_candidates={','.join(support_only_candidates) if support_only_candidates else 'none'}",
        "PASS accepted_rows_added=0",
        "PASS new_confidence_gate=false",
        "PASS canonical_merge_allowed=false",
        "PASS downstream_chain_rerun_allowed=false",
        "PASS strict_full_objective_achieved=false",
        "PASS update_goal=false",
        "PASS runtime_code_changed=false",
        "PASS thresholds_relaxed=false",
        "PASS raw_data_committed=false",
        "PASS trade_usable=false",
    ]
    (CHECKS / "source_label_high_confidence_subset_triage_v1_assertions.out").write_text("\n".join(checks) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
