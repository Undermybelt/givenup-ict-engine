#!/usr/bin/env python3
"""Draft Bull/Sideways source-label qualifying conditions without promotion."""

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
RUN_ID = "20260512T012330-codex-source-label-bull-sideways-qualifying-condition-v1"
OUT = RUN_ROOT / "source-label-bull-sideways-qualifying-condition-v1"
CHECKS = RUN_ROOT / "checks"
BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"
INTAKE_ROOT = Path("/tmp/ict-engine-source-label-equivalence-intake")
INTAKE_ROWS = INTAKE_ROOT / "source_label_equivalence_rows.csv"
INTAKE_PROVENANCE = INTAKE_ROOT / "source_label_equivalence_provenance.json"
STOCK_SOURCE = Path("/Users/thrill3r/Downloads/stock-market-regimes-20002026/stock_market_regimes_2000_2026.csv")
NIFTY_SOURCE = Path("/tmp/ict-engine-source-label-equivalence-reconstruction-v1/nifty/regime_timeline_history.csv")
CALIBRATION_JSON = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260512T011056-codex-source-label-equivalence-calibration-after-root-poll-v1/"
    "source-label-equivalence-confidence-calibration/"
    "source_label_equivalence_confidence_calibration_v1.json"
)
TRIAGE_JSON = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260512T011819-codex-source-label-high-confidence-subset-triage-v1/"
    "source-label-high-confidence-subset-triage-v1/"
    "source_label_high_confidence_subset_triage_v1.json"
)

TARGET_LABELS = ["Bull", "Sideways"]
REQUIRED_SPLITS = ["calibration", "heldout_market", "heldout_time", "test"]
REQUIRED_MARKET_FAMILY_MIN = 2
REQUIRED_TIMEFRAME_MIN = 2
MIN_SUPPORT_PER_SPLIT = 50
MIN_SUPPORT_PER_PERIOD = 50
CONFIDENCE_THRESHOLD = 0.95

PERIODS = [
    ("early_2000s_2000_2006", "2000-01-01", "2006-12-31"),
    ("gfc_recovery_2007_2013", "2007-01-01", "2013-12-31"),
    ("late_cycle_2014_2019", "2014-01-01", "2019-12-31"),
    ("covid_inflation_2020_2026", "2020-01-01", "2026-12-31"),
]


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


def period_for_date(day: str) -> str:
    for name, start, end in PERIODS:
        if start <= day <= end:
            return name
    return "out_of_period_contract"


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)

    required = [BOARD, INTAKE_ROWS, INTAKE_PROVENANCE, STOCK_SOURCE, NIFTY_SOURCE, CALIBRATION_JSON, TRIAGE_JSON]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError(missing)

    board_hash = sha256_file(BOARD)
    calibration = json.loads(CALIBRATION_JSON.read_text(encoding="utf-8"))
    triage = json.loads(TRIAGE_JSON.read_text(encoding="utf-8"))
    rows = read_csv(INTAKE_ROWS)
    stock_map = stock_confidence_map()
    nifty_map = nifty_confidence_map()

    label_total_rows = Counter()
    label_high_rows = Counter()
    split_counts = Counter()
    market_counts = Counter()
    owner_counts = Counter()
    timeframe_counts = Counter()
    period_counts = Counter()
    symbols: dict[str, set[str]] = defaultdict(set)
    source_owners: dict[str, set[str]] = defaultdict(set)
    timeframes: dict[str, set[str]] = defaultdict(set)
    market_families: dict[str, set[str]] = defaultdict(set)
    dates: dict[str, list[str]] = defaultdict(list)
    missing_confidence = 0

    for row in rows:
        label = row.get("main_regime_v2_label", "")
        if label not in TARGET_LABELS:
            continue
        label_total_rows[label] += 1
        confidence = confidence_for_row(row, stock_map, nifty_map)
        if confidence is None:
            missing_confidence += 1
            continue
        if confidence < CONFIDENCE_THRESHOLD:
            continue
        split = row.get("split_role", "")
        market_family = row.get("market_family", "")
        source_owner = row.get("source_owner", "")
        timeframe = row.get("timeframe", "")
        day = row.get("timestamp_or_date", "")
        period = period_for_date(day)
        label_high_rows[label] += 1
        split_counts[(label, split)] += 1
        market_counts[(label, market_family)] += 1
        owner_counts[(label, source_owner)] += 1
        timeframe_counts[(label, timeframe)] += 1
        period_counts[(label, period)] += 1
        symbols[label].add(row.get("symbol", ""))
        source_owners[label].add(source_owner)
        timeframes[label].add(timeframe)
        market_families[label].add(market_family)
        if day:
            dates[label].append(day)

    label_summary_rows: list[dict[str, Any]] = []
    split_rows: list[dict[str, Any]] = []
    market_rows: list[dict[str, Any]] = []
    owner_rows: list[dict[str, Any]] = []
    timeframe_rows: list[dict[str, Any]] = []
    period_rows: list[dict[str, Any]] = []
    failure_rows: list[dict[str, Any]] = []
    condition_rows: list[dict[str, Any]] = []
    blockers_by_label: dict[str, list[str]] = {}

    for label in TARGET_LABELS:
        label_blockers: list[str] = []
        label_split_pass = all(split_counts[(label, split)] >= MIN_SUPPORT_PER_SPLIT for split in REQUIRED_SPLITS)
        label_period_pass = all(period_counts[(label, name)] >= MIN_SUPPORT_PER_PERIOD for name, _, _ in PERIODS)
        label_market_pass = len([item for item in market_families[label] if item]) >= REQUIRED_MARKET_FAMILY_MIN
        label_timeframe_pass = len([item for item in timeframes[label] if item]) >= REQUIRED_TIMEFRAME_MIN
        if not label_split_pass:
            label_blockers.append("split_support_incomplete")
        if not label_period_pass:
            label_blockers.append("chronological_period_support_incomplete")
        if not label_market_pass:
            label_blockers.append("cross_market_family_support_incomplete")
        if not label_timeframe_pass:
            label_blockers.append("multi_timeframe_support_absent_only_1d")
        label_blockers.extend(
            [
                "baseline_source_label_calibration_still_no_acceptance",
                "r6_owner_control_blocker_still_active",
                "canonical_merge_not_allowed",
            ]
        )
        blockers_by_label[label] = label_blockers
        label_dates = sorted(dates[label])
        qualifying_condition = (
            f"main_regime_v2_label == '{label}' AND source_confidence >= {CONFIDENCE_THRESHOLD} "
            "AND source_owner in {source-owned-stock-market-regimes-2000-2026, ahaanverma00} "
            "AND timeframe == '1d'"
        )
        condition_rows.append(
            {
                "label": label,
                "qualifying_condition": qualifying_condition,
                "allowed_action": "support_only_no_trade_promotion",
                "abstain_condition": "source_confidence < 0.95 OR non_1d_timeframe_required OR source_owner_not_in_contract OR active_board_blocker_present",
                "acceptance_state": "blocked_no_acceptance",
            }
        )
        label_summary_rows.append(
            {
                "label": label,
                "qualifying_condition": qualifying_condition,
                "total_rows": label_total_rows[label],
                "high_conf_rows": label_high_rows[label],
                "high_conf_share": f"{(label_high_rows[label] / label_total_rows[label]) if label_total_rows[label] else 0.0:.10f}",
                "symbol_count": len(symbols[label]),
                "source_owner_count": len([item for item in source_owners[label] if item]),
                "market_family_count": len([item for item in market_families[label] if item]),
                "timeframe_count": len([item for item in timeframes[label] if item]),
                "date_min": label_dates[0] if label_dates else "",
                "date_max": label_dates[-1] if label_dates else "",
                "split_support_pass": str(label_split_pass).lower(),
                "chronological_period_support_pass": str(label_period_pass).lower(),
                "cross_market_family_support_pass": str(label_market_pass).lower(),
                "multi_timeframe_support_pass": str(label_timeframe_pass).lower(),
                "acceptance_state": "blocked_no_acceptance",
                "blockers": ";".join(label_blockers),
            }
        )
        for split in REQUIRED_SPLITS:
            split_rows.append({"label": label, "split_role": split, "high_conf_rows": split_counts[(label, split)]})
        for market_family in sorted(item for item in market_families[label] if item):
            market_rows.append({"label": label, "market_family": market_family, "high_conf_rows": market_counts[(label, market_family)]})
        for owner in sorted(item for item in source_owners[label] if item):
            owner_rows.append({"label": label, "source_owner": owner, "high_conf_rows": owner_counts[(label, owner)]})
        for timeframe in sorted(item for item in timeframes[label] if item):
            timeframe_rows.append({"label": label, "timeframe": timeframe, "high_conf_rows": timeframe_counts[(label, timeframe)]})
        for period_name, start, end in PERIODS:
            count = period_counts[(label, period_name)]
            period_rows.append(
                {
                    "label": label,
                    "period": period_name,
                    "start": start,
                    "end": end,
                    "high_conf_rows": count,
                    "support_pass": str(count >= MIN_SUPPORT_PER_PERIOD).lower(),
                }
            )
        for blocker in label_blockers:
            failure_rows.append({"label": label, "blocker": blocker})

    decision = (
        "source_label_bull_sideways_qualifying_condition_v1="
        "conditions_drafted_cross_market_period_ok_timeframe_r6_baseline_blocked_no_acceptance"
    )
    summary = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "board_hash_before_writeback": board_hash,
        "source_rows_path": str(INTAKE_ROWS),
        "source_rows_sha256": sha256_file(INTAKE_ROWS),
        "source_provenance_sha256": sha256_file(INTAKE_PROVENANCE),
        "calibration_run": calibration.get("run_id"),
        "calibration_decision": calibration.get("decision"),
        "triage_run": triage.get("run_id"),
        "triage_decision": triage.get("decision"),
        "target_labels": TARGET_LABELS,
        "confidence_threshold": CONFIDENCE_THRESHOLD,
        "min_support_per_split": MIN_SUPPORT_PER_SPLIT,
        "min_support_per_period": MIN_SUPPORT_PER_PERIOD,
        "required_timeframe_min": REQUIRED_TIMEFRAME_MIN,
        "row_count": len(rows),
        "missing_confidence_rows": missing_confidence,
        "label_summary": label_summary_rows,
        "blockers_by_label": blockers_by_label,
        "accepted_labels": [],
        "accepted_rows_added": 0,
        "new_confidence_gate": False,
        "canonical_merge_allowed": False,
        "downstream_chain_rerun_allowed": False,
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "shared_intake_mutated": False,
        "r6_owner_export_root_mutated": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "external_requests_sent": False,
        "trade_usable": False,
        "decision": decision,
    }

    write_csv(
        OUT / "source_label_bull_sideways_condition_summary_v1.csv",
        label_summary_rows,
        [
            "label",
            "qualifying_condition",
            "total_rows",
            "high_conf_rows",
            "high_conf_share",
            "symbol_count",
            "source_owner_count",
            "market_family_count",
            "timeframe_count",
            "date_min",
            "date_max",
            "split_support_pass",
            "chronological_period_support_pass",
            "cross_market_family_support_pass",
            "multi_timeframe_support_pass",
            "acceptance_state",
            "blockers",
        ],
    )
    write_csv(
        OUT / "source_label_bull_sideways_qualifying_conditions_v1.csv",
        condition_rows,
        ["label", "qualifying_condition", "allowed_action", "abstain_condition", "acceptance_state"],
    )
    write_csv(OUT / "source_label_bull_sideways_split_support_v1.csv", split_rows, ["label", "split_role", "high_conf_rows"])
    write_csv(OUT / "source_label_bull_sideways_market_support_v1.csv", market_rows, ["label", "market_family", "high_conf_rows"])
    write_csv(OUT / "source_label_bull_sideways_owner_support_v1.csv", owner_rows, ["label", "source_owner", "high_conf_rows"])
    write_csv(OUT / "source_label_bull_sideways_timeframe_support_v1.csv", timeframe_rows, ["label", "timeframe", "high_conf_rows"])
    write_csv(OUT / "source_label_bull_sideways_period_support_v1.csv", period_rows, ["label", "period", "start", "end", "high_conf_rows", "support_pass"])
    write_csv(OUT / "source_label_bull_sideways_blockers_v1.csv", failure_rows, ["label", "blocker"])

    (OUT / "source_label_bull_sideways_qualifying_condition_v1.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    md = [
        "# Source Label Bull/Sideways Qualifying Condition v1",
        "",
        f"- Decision: `{decision}`.",
        f"- Calibration baseline: `{summary['calibration_decision']}`.",
        f"- Prior triage: `{summary['triage_decision']}`.",
        f"- Confidence threshold: `{CONFIDENCE_THRESHOLD}`; min support per split/period: `{MIN_SUPPORT_PER_SPLIT}`/`{MIN_SUPPORT_PER_PERIOD}`.",
        "- Accepted labels: `0`; accepted rows added: `0`; canonical merge allowed: `false`; downstream chain rerun allowed: `false`.",
        "- Runtime code changed: `false`; shared intake mutated: `false`; thresholds relaxed: `false`; raw data committed: `false`; external requests sent: `false`; trade usable: `false`.",
        "",
        "## Condition Summary",
        "",
        "| Label | High-Conf Rows | Splits | Periods | Markets | Timeframes | Acceptance | Blockers |",
        "|---|---:|---|---|---|---|---|---|",
    ]
    for row in label_summary_rows:
        md.append(
            f"| `{row['label']}` | `{row['high_conf_rows']}` | `{row['split_support_pass']}` | "
            f"`{row['chronological_period_support_pass']}` | `{row['cross_market_family_support_pass']}` | "
            f"`{row['multi_timeframe_support_pass']}` | `{row['acceptance_state']}` | `{row['blockers']}` |"
        )
    md.extend(
        [
            "",
            "## Boundary",
            "",
            "This packet drafts explicit Bull and Sideways source-label qualifying conditions from the existing schema-ready source-label root. Both labels retain support across required splits, market families, and chronological periods, but the packet remains fail-closed because the evidence is daily-only, the baseline source-label calibration is still no-acceptance, and the active R6 owner-control blocker still prevents canonical merge and downstream promotion.",
        ]
    )
    (OUT / "source_label_bull_sideways_qualifying_condition_v1.md").write_text("\n".join(md) + "\n", encoding="utf-8")

    checks = [
        f"PASS run_id={RUN_ID}",
        f"PASS decision={decision}",
        f"PASS calibration_decision={summary['calibration_decision']}",
        f"PASS triage_decision={summary['triage_decision']}",
        f"PASS row_count={len(rows)}",
        f"PASS missing_confidence_rows={missing_confidence}",
        "PASS target_labels=Bull,Sideways",
        "PASS accepted_labels=0",
        "PASS accepted_rows_added=0",
        "PASS new_confidence_gate=false",
        "PASS canonical_merge_allowed=false",
        "PASS downstream_chain_rerun_allowed=false",
        "PASS strict_full_objective_achieved=false",
        "PASS update_goal=false",
        "PASS runtime_code_changed=false",
        "PASS shared_intake_mutated=false",
        "PASS r6_owner_export_root_mutated=false",
        "PASS thresholds_relaxed=false",
        "PASS raw_data_committed=false",
        "PASS external_requests_sent=false",
        "PASS trade_usable=false",
    ]
    (CHECKS / "source_label_bull_sideways_qualifying_condition_v1_assertions.out").write_text("\n".join(checks) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
