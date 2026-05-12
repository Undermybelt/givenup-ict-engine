#!/usr/bin/env python3
"""Aggregate per-regime field readback for the accepted HGB diagnostic screen."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
from typing import Any


RUN_ID = "20260512T055058-codex-hgb-aggregate-field-readback-v1"
SLUG = "hgb-aggregate-field-readback-v1"
RUN_ROOT = Path(__file__).resolve().parents[1]
OUT = RUN_ROOT / SLUG
CHECKS = RUN_ROOT / "checks"
HGB_JSON = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260512T051844-codex-source-label-hgb-numeric-threshold-screen-v1/"
    "source-label-hgb-numeric-threshold-screen-v1/"
    "source_label_hgb_numeric_threshold_screen_v1.json"
)
INTAKE_ROOT = Path("/tmp/ict-engine-source-label-equivalence-intake")
ROWS = INTAKE_ROOT / "source_label_equivalence_rows.csv"
PROVENANCE = INTAKE_ROOT / "source_label_equivalence_provenance.json"
ROOT_LABELS = ["Bear", "Bull", "Crisis", "Sideways"]
REQUIRED_SPLITS = ["calibration", "heldout_market", "heldout_time", "test"]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fieldnames: list[str] = []
    for row in rows:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def compact(values: set[str], limit: int = 24) -> dict[str, Any]:
    clean = sorted(value for value in values if value)
    return {"count": len(clean), "sample": clean[:limit], "truncated": len(clean) > limit}


def empty_label_state() -> dict[str, Any]:
    return {
        "row_count": 0,
        "symbols": set(),
        "contexts": set(),
        "sources": set(),
        "timeframes": set(),
        "splits": {
            split: {
                "row_count": 0,
                "symbols": set(),
                "contexts": set(),
                "date_min": "",
                "date_max": "",
                "sample_source_row_ids": [],
            }
            for split in REQUIRED_SPLITS
        },
    }


def update_date_bounds(state: dict[str, Any], value: str) -> None:
    if not value:
        return
    if not state["date_min"] or value < state["date_min"]:
        state["date_min"] = value
    if not state["date_max"] or value > state["date_max"]:
        state["date_max"] = value


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)
    hgb = json.loads(HGB_JSON.read_text(encoding="utf-8"))
    gates = {row["label"]: row for row in hgb["gates"]}
    labels = {label: empty_label_state() for label in ROOT_LABELS}
    total_rows = 0

    with ROWS.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            label = row.get("main_regime_v2_label", "")
            if label not in labels:
                continue
            split = row.get("split_role", "")
            if split not in REQUIRED_SPLITS:
                continue
            total_rows += 1
            state = labels[label]
            symbol = row.get("symbol", "")
            source_owner = row.get("source_owner", "")
            market_family = row.get("market_family", "")
            timeframe = row.get("timeframe", "")
            context = f"{source_owner}|{market_family}|{timeframe}"
            state["row_count"] += 1
            state["symbols"].add(symbol)
            state["contexts"].add(context)
            state["sources"].add(source_owner)
            state["timeframes"].add(timeframe)
            split_state = state["splits"][split]
            split_state["row_count"] += 1
            split_state["symbols"].add(symbol)
            split_state["contexts"].add(context)
            update_date_bounds(split_state, row.get("timestamp_or_date", ""))
            if len(split_state["sample_source_row_ids"]) < 8:
                split_state["sample_source_row_ids"].append(row.get("source_row_id", ""))

    field_rows: list[dict[str, Any]] = []
    split_rows: list[dict[str, Any]] = []
    packets: dict[str, Any] = {}
    for label in ROOT_LABELS:
        gate = gates[label]
        state = labels[label]
        period_splits = [
            split for split, detail in state["splits"].items() if detail["row_count"] > 0
        ]
        aggregate_field_complete = (
            gate["accepted_extra_trees_confidence_95"] is True
            and len(state["symbols"]) >= 2
            and len(period_splits) == len(REQUIRED_SPLITS)
            and len(state["contexts"]) >= 2
        )
        packet = {
            "label": label,
            "qualifying_condition": f"hgb_numeric_probability({label}) >= {gate['threshold']}",
            "hgb_threshold": gate["threshold"],
            "hgb_min_split_support": gate["min_split_support"],
            "hgb_min_split_wilson95_lcb": gate["min_split_wilson95_lcb"],
            "hgb_accepted_95": gate["accepted_extra_trees_confidence_95"],
            "validation_instruments": compact(state["symbols"]),
            "validation_periods": [
                {
                    "split_role": split,
                    "row_count": detail["row_count"],
                    "date_min": detail["date_min"],
                    "date_max": detail["date_max"],
                    "symbol_count": len(detail["symbols"]),
                    "context_count": len(detail["contexts"]),
                }
                for split, detail in state["splits"].items()
            ],
            "validation_market_contexts": compact(state["contexts"]),
            "aggregate_field_complete_diagnostic": aggregate_field_complete,
            "axis_scope_caveat": "Validation axes are aggregate actual source-label rows for the regime, not exact HGB high-confidence selected rows; exact HGB selected split support is preserved from the 051844 gate table.",
            "source_control_evidence_acquired": False,
            "canonical_merge": False,
            "downstream_promotion_rerun": False,
            "trade_usable": False,
            "update_goal": False,
        }
        packets[label] = packet
        field_rows.append(
            {
                "label": label,
                "qualifying_condition": packet["qualifying_condition"],
                "hgb_accepted_95": packet["hgb_accepted_95"],
                "hgb_min_split_support": packet["hgb_min_split_support"],
                "hgb_min_split_wilson95_lcb": packet["hgb_min_split_wilson95_lcb"],
                "aggregate_source_rows": state["row_count"],
                "validation_instrument_count": len(state["symbols"]),
                "validation_instrument_sample": ";".join(packet["validation_instruments"]["sample"]),
                "validation_period_count": len(period_splits),
                "validation_context_count": len(state["contexts"]),
                "validation_context_sample": ";".join(packet["validation_market_contexts"]["sample"]),
                "aggregate_field_complete_diagnostic": aggregate_field_complete,
                "source_control_evidence_acquired": False,
                "canonical_merge": False,
                "downstream_promotion_rerun": False,
                "update_goal": False,
            }
        )
        for split, detail in state["splits"].items():
            split_rows.append(
                {
                    "label": label,
                    "split_role": split,
                    "row_count": detail["row_count"],
                    "date_min": detail["date_min"],
                    "date_max": detail["date_max"],
                    "symbol_count": len(detail["symbols"]),
                    "symbol_sample": ";".join(compact(detail["symbols"])["sample"]),
                    "context_count": len(detail["contexts"]),
                    "context_sample": ";".join(compact(detail["contexts"])["sample"]),
                    "sample_source_row_ids": ";".join(detail["sample_source_row_ids"]),
                }
            )

    diagnostic_complete = [
        label for label, packet in packets.items() if packet["aggregate_field_complete_diagnostic"]
    ]
    gate_result = (
        "hgb_aggregate_field_readback_v1=all_hgb_labels_aggregate_fields_present_source_control_absent"
        if len(diagnostic_complete) == len(ROOT_LABELS)
        else "hgb_aggregate_field_readback_v1=aggregate_fields_incomplete_or_source_control_absent"
    )
    result = {
        "run_id": RUN_ID,
        "gate_result": gate_result,
        "source_hgb_run": str(HGB_JSON),
        "row_count_scanned": total_rows,
        "rows_sha256": sha256_file(ROWS),
        "provenance_sha256": sha256_file(PROVENANCE),
        "packets": packets,
        "diagnostic_aggregate_field_complete_labels": diagnostic_complete,
        "promotion_status": {
            "accepted_rows_added": 0,
            "source_control_evidence_acquired": False,
            "canonical_merge": False,
            "downstream_promotion_rerun": False,
            "strict_full_objective": False,
            "trade_usable": False,
            "update_goal": False,
        },
    }
    (OUT / "hgb_aggregate_field_readback_v1.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    write_csv(OUT / "hgb_aggregate_field_summary_v1.csv", field_rows)
    write_csv(OUT / "hgb_aggregate_split_validation_v1.csv", split_rows)

    lines = [
        "# HGB Aggregate Field Readback v1",
        "",
        f"Run id: `{RUN_ID}`",
        "",
        f"Gate result: `{gate_result}`",
        "",
        "## Scope",
        "",
        "This readback maps the accepted `051844` HGB diagnostic confidence gates to explicit per-regime aggregate validation fields from the source-label equivalence intake.",
        "",
        "Caveat: validation axes here are aggregate actual source-label rows for each regime, not exact HGB high-confidence selected rows. Exact high-confidence split support and Wilson95 values come from the `051844` HGB gate table.",
        "",
        "## Summary",
        "",
        "| Label | Qualifying condition | HGB 95 accepted | Min support | Min Wilson95 | Source rows | Instruments | Periods | Contexts | Aggregate fields present |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in field_rows:
        lines.append(
            f"| `{row['label']}` | `{row['qualifying_condition']}` | "
            f"`{str(row['hgb_accepted_95']).lower()}` | `{row['hgb_min_split_support']}` | "
            f"`{row['hgb_min_split_wilson95_lcb']}` | `{row['aggregate_source_rows']}` | "
            f"`{row['validation_instrument_count']}` | `{row['validation_period_count']}` | "
            f"`{row['validation_context_count']}` | "
            f"`{str(row['aggregate_field_complete_diagnostic']).lower()}` |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            f"- Diagnostic aggregate field-complete labels: `{diagnostic_complete}`.",
            "- Source/control evidence acquired `false`; canonical merge `false`; downstream promotion rerun `false`; trade usable `false`; `update_goal=false`.",
            "- This readback can help audit per-regime fields after source/control unlock, but it cannot unlock Board A promotion by itself.",
        ]
    )
    (OUT / "hgb_aggregate_field_readback_v1.md").write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
    )
    assertions = [
        f"PASS run_id={RUN_ID}",
        f"PASS gate_result={gate_result}",
        f"PASS diagnostic_aggregate_field_complete_labels={','.join(diagnostic_complete)}",
        f"PASS diagnostic_aggregate_field_complete_label_count={len(diagnostic_complete)}",
        "PASS source_control_evidence_acquired=false",
        "PASS canonical_merge=false",
        "PASS downstream_promotion_rerun=false",
        "PASS strict_full_objective=false",
        "PASS trade_usable=false",
        "PASS update_goal=false",
    ]
    (CHECKS / "hgb_aggregate_field_readback_v1_assertions.out").write_text(
        "\n".join(assertions) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"gate_result": gate_result, "diagnostic_aggregate_field_complete_labels": diagnostic_complete}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
