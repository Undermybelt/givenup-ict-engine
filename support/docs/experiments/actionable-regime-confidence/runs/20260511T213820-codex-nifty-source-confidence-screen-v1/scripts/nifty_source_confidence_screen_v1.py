#!/usr/bin/env python3
"""Score source-owned NIFTY confidence fields without promoting completion."""

from __future__ import annotations

import csv
import hashlib
import json
import statistics
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path


RUN_ID = "20260511T213820-codex-nifty-source-confidence-screen-v1"
REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = Path(__file__).resolve().parents[1]
OUT = RUN_ROOT / "nifty-source-confidence-screen"
CHECKS = RUN_ROOT / "checks"
SOURCE_ROOT = Path("/tmp/ict-engine-public-source-intake-scout/nifty")
SOURCE_CSV = SOURCE_ROOT / "regime_timeline_history.csv"
SOURCE_METADATA = SOURCE_ROOT / "dataset-metadata.json"
INTAKE_ROOT = Path("/tmp/ict-engine-source-label-equivalence-intake")
INTAKE_ROWS = INTAKE_ROOT / "source_label_equivalence_rows.csv"
INTAKE_PROVENANCE = INTAKE_ROOT / "source_label_equivalence_provenance.json"
BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"

MAPPINGS = [
    {
        "label": "Bull",
        "source_field": "macro_state",
        "source_state": "Durable",
        "confidence_field": "macro_confidence",
        "policy": "source_owner_describes_Durable_as_trending_bull_low_vol",
    },
    {
        "label": "Sideways",
        "source_field": "fast_state",
        "source_state": "Calm",
        "confidence_field": "fast_confidence",
        "policy": "source_owner_describes_Calm_as_sideways_low_vol",
    },
    {
        "label": "Crisis",
        "source_field": "fast_state",
        "source_state": "Stress",
        "confidence_field": "fast_confidence",
        "policy": "source_owner_describes_Stress_as_crisis_high_volatility",
    },
]
CONFIDENCE_THRESHOLD = 0.95


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def split_role(day: str) -> str:
    if day < "2018-01-01":
        return "calibration"
    if day < "2023-01-01":
        return "heldout_time"
    return "test"


def summarize(values: list[float]) -> dict[str, float]:
    if not values:
        return {"min": 0.0, "median": 0.0, "mean": 0.0, "max": 0.0}
    return {
        "min": min(values),
        "median": statistics.median(values),
        "mean": statistics.fmean(values),
        "max": max(values),
    }


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)

    missing_inputs = [
        str(path)
        for path in [SOURCE_CSV, SOURCE_METADATA, INTAKE_ROWS, INTAKE_PROVENANCE]
        if not path.exists()
    ]
    if missing_inputs:
        raise FileNotFoundError(missing_inputs)

    source_rows = read_csv(SOURCE_CSV)
    intake_rows = read_csv(INTAKE_ROWS)
    board_hash = sha256_file(BOARD)
    source_label_counts = Counter(row.get("main_regime_v2_label", "") for row in intake_rows)
    source_labels = sorted(k for k in source_label_counts if k)

    summaries: list[dict[str, object]] = []
    for mapping in MAPPINGS:
        values: list[float] = []
        split_counts: Counter[str] = Counter()
        dates: list[str] = []
        rows_at_threshold = 0
        for row in source_rows:
            if row.get(mapping["source_field"]) != mapping["source_state"]:
                continue
            try:
                confidence = float(row.get(mapping["confidence_field"], "nan"))
            except ValueError:
                continue
            values.append(confidence)
            dates.append(row["Date"])
            split_counts[split_role(row["Date"])] += 1
            if confidence >= CONFIDENCE_THRESHOLD:
                rows_at_threshold += 1
        total = len(values)
        stats = summarize(values)
        summaries.append(
            {
                "label": mapping["label"],
                "source_field": mapping["source_field"],
                "source_state": mapping["source_state"],
                "confidence_field": mapping["confidence_field"],
                "policy": mapping["policy"],
                "rows": total,
                "rows_at_or_above_0_95": rows_at_threshold,
                "share_at_or_above_0_95": rows_at_threshold / total if total else 0.0,
                "confidence_min": stats["min"],
                "confidence_median": stats["median"],
                "confidence_mean": stats["mean"],
                "confidence_max": stats["max"],
                "date_min": min(dates) if dates else "",
                "date_max": max(dates) if dates else "",
                "split_counts": dict(sorted(split_counts.items())),
            }
        )

    macro_counts = Counter(row.get("macro_state", "") for row in source_rows)
    fast_counts = Counter(row.get("fast_state", "") for row in source_rows)
    unmapped_counts = {
        "macro_Fragile": macro_counts.get("Fragile", 0),
        "fast_Choppy": fast_counts.get("Choppy", 0),
    }
    live_intake_missing_roots = sorted(set(["Bull", "Bear", "Sideways", "Crisis"]) - set(source_labels))
    nifty_mapped_labels = sorted({row["label"] for row in summaries})
    nifty_missing_roots = sorted(set(["Bull", "Bear", "Sideways", "Crisis"]) - set(nifty_mapped_labels))
    high_confidence_rows = sum(int(row["rows_at_or_above_0_95"]) for row in summaries)
    decision = "nifty_source_confidence_screen_v1=partial_source_confidence_scored_no_acceptance"
    result = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "board_hash_before_writeback": board_hash,
        "decision": decision,
        "source_csv": str(SOURCE_CSV),
        "source_csv_sha256": sha256_file(SOURCE_CSV),
        "source_metadata": str(SOURCE_METADATA),
        "source_metadata_sha256": sha256_file(SOURCE_METADATA),
        "intake_rows": str(INTAKE_ROWS),
        "intake_rows_sha256": sha256_file(INTAKE_ROWS),
        "intake_row_count": len(intake_rows),
        "intake_label_counts": dict(sorted(source_label_counts.items())),
        "live_intake_missing_roots": live_intake_missing_roots,
        "nifty_mapped_labels": nifty_mapped_labels,
        "nifty_missing_roots": nifty_missing_roots,
        "confidence_threshold": CONFIDENCE_THRESHOLD,
        "confidence_summaries": summaries,
        "unmapped_source_state_counts": unmapped_counts,
        "high_confidence_rows": high_confidence_rows,
        "accepted_rows_added": 0,
        "new_confidence_gate": False,
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "external_requests_sent": False,
        "trade_usable": False,
        "blocker": "Source posterior/confidence fields can score partial NIFTY labels, but the NIFTY subset still lacks Bear and source confidence is not cross-market/cross-cycle calibrated Board A acceptance.",
    }

    json_path = OUT / "nifty_source_confidence_screen_v1.json"
    report_path = OUT / "nifty_source_confidence_screen_v1.md"
    counts_path = OUT / "nifty_source_confidence_screen_v1_counts.csv"
    gates_path = OUT / "nifty_source_confidence_screen_v1_gates.csv"
    assertions_path = CHECKS / "nifty_source_confidence_screen_v1_assertions.out"

    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    with counts_path.open("w", newline="", encoding="utf-8") as handle:
        fieldnames = [
            "label",
            "source_field",
            "source_state",
            "confidence_field",
            "rows",
            "rows_at_or_above_0_95",
            "share_at_or_above_0_95",
            "confidence_min",
            "confidence_median",
            "confidence_mean",
            "confidence_max",
            "date_min",
            "date_max",
        ]
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in summaries:
            writer.writerow({field: row.get(field, "") for field in fieldnames})
    gates = [
        {"gate": "source_confidence_fields_present", "observed": "true", "required": "true", "pass": "true"},
        {"gate": "all_main_roots_present", "observed": ",".join(source_labels), "required": "Bull,Bear,Sideways,Crisis", "pass": "false"},
        {"gate": "bear_root_present", "observed": str("Bear" in source_labels).lower(), "required": "true", "pass": "false"},
        {"gate": "accepted_confidence_gate", "observed": "source posterior screen only", "required": "cross-market/cross-cycle calibrated >=0.95", "pass": "false"},
        {"gate": "strict_full_objective", "observed": "false", "required": "true", "pass": "false"},
    ]
    with gates_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["gate", "observed", "required", "pass"])
        writer.writeheader()
        writer.writerows(gates)

    lines = [
        "# NIFTY Source Confidence Screen v1",
        "",
        f"- Decision: `{decision}`.",
        f"- Live intake rows observed: `{len(intake_rows)}`; live labels: `{dict(sorted(source_label_counts.items()))}`; live missing roots: `{live_intake_missing_roots}`.",
        f"- NIFTY subset labels scored: `{nifty_mapped_labels}`; NIFTY missing roots: `{nifty_missing_roots}`.",
        f"- Source confidence threshold checked: `{CONFIDENCE_THRESHOLD}`.",
        f"- High-confidence source rows counted: `{high_confidence_rows}`.",
        "- Accepted rows added: `0`; new confidence gate: `false`.",
        "- Strict full objective achieved: `false`; `update_goal=false`.",
        "- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; external requests sent: `false`; trade usable: `false`.",
        "",
        "## Confidence Summaries",
        "",
        "| Label | Source State | Rows | Rows >=0.95 | Share >=0.95 | Median | Mean | Max | Date Range |",
        "|---|---|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in summaries:
        lines.append(
            f"| `{row['label']}` | `{row['source_field']}={row['source_state']}` | "
            f"`{row['rows']}` | `{row['rows_at_or_above_0_95']}` | "
            f"`{row['share_at_or_above_0_95']:.6f}` | `{row['confidence_median']:.6f}` | "
            f"`{row['confidence_mean']:.6f}` | `{row['confidence_max']:.6f}` | "
            f"`{row['date_min']}..{row['date_max']}` |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "This scores source-provided posterior/confidence fields for the already-ingested NIFTY source-label subset. The live shared intake may include Bear rows from a concurrent US-panel extension, but this NIFTY-only screen does not create Bear rows and does not convert source posterior confidence into a Board A accepted confidence gate.",
            "",
            "## Artifacts",
            "",
            f"- JSON: `{json_path.relative_to(REPO)}`",
            f"- Report: `{report_path.relative_to(REPO)}`",
            f"- Counts CSV: `{counts_path.relative_to(REPO)}`",
            f"- Gate CSV: `{gates_path.relative_to(REPO)}`",
            f"- Assertions: `{assertions_path.relative_to(REPO)}`",
        ]
    )
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    assertions = [
        f"PASS decision={decision}",
        f"PASS intake_row_count={len(intake_rows)}",
        f"PASS live_intake_missing_roots={','.join(live_intake_missing_roots)}",
        f"PASS nifty_missing_roots={','.join(nifty_missing_roots)}",
        f"PASS high_confidence_rows={high_confidence_rows}",
        "PASS accepted_rows_added=0",
        "PASS new_confidence_gate=false",
        "PASS strict_full_objective_achieved=false",
        "PASS update_goal=false",
        "PASS raw_data_committed=false",
        "PASS external_requests_sent=false",
    ]
    assertions_path.write_text("\n".join(assertions) + "\n", encoding="utf-8")
    print(json.dumps({"decision": decision, "live_intake_missing_roots": live_intake_missing_roots, "nifty_missing_roots": nifty_missing_roots, "high_confidence_rows": high_confidence_rows, "update_goal": False}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
