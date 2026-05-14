#!/usr/bin/env python3
import csv
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


RUN_ID = "20260511T192248+0800-codex-native-subhour-projection-quarantine-v1"
RUN_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = RUN_ROOT.parents[4]
BOARD_PATH = REPO_ROOT / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"
OUT_DIR = RUN_ROOT / "native-subhour-projection-quarantine"
CHECK_DIR = RUN_ROOT / "checks"

OUT_DIR.mkdir(parents=True, exist_ok=True)
CHECK_DIR.mkdir(parents=True, exist_ok=True)

PANEL_INPUTS = [
    {
        "run_id": "20260511T124000-codex-unified-source-label-panel-v1",
        "path": REPO_ROOT
        / "docs/experiments/actionable-regime-confidence/runs/20260511T124000-codex-unified-source-label-panel-v1/unified-panel/unified_source_label_panel_v1.csv",
        "schema": "panel_124000",
    },
    {
        "run_id": "20260511T124027-codex-unified-source-label-panel-v1",
        "path": REPO_ROOT
        / "docs/experiments/actionable-regime-confidence/runs/20260511T124027-codex-unified-source-label-panel-v1/unified-source-label-panel/unified_source_label_panel_v1.csv",
        "schema": "panel_124027",
    },
]

NATIVE_SUBHOUR_TIMEFRAMES = {"1m", "5m", "15m", "30m"}


def sha256_file(path):
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_csv(path):
    with path.open(newline="") as fh:
        return list(csv.DictReader(fh))


def normalize_row(row, source):
    if source["schema"] == "panel_124000":
        return {
            "source_run": source["run_id"],
            "row_id": row["label_window_id"],
            "source_lane": row["source_type"],
            "root": row["root"],
            "provider": row["provider"],
            "instrument": row["instrument"],
            "market_context": row["market_context"],
            "timeframe": row["timeframe"],
            "source_id": row["source_id"],
            "evidence_type": row["source_type"],
            "materialization_status": row["status"],
            "date_granularity": row["date_granularity"],
            "crosswalk_layer": row["crosswalk_layer"],
            "crosswalk_decision": row["crosswalk_decision"],
            "confidence_gate_reference": row["confidence_gate_ref"],
            "notes": row["notes"],
        }
    return {
        "source_run": source["run_id"],
        "row_id": row["panel_row_id"],
        "source_lane": row["source_lane"],
        "root": row["root"],
        "provider": row["provider"],
        "instrument": row["instrument"],
        "market_context": row["market_context"],
        "timeframe": row["timeframe"],
        "source_id": row["source_id"],
        "evidence_type": row["evidence_type"],
        "materialization_status": row["materialization_status"],
        "date_granularity": "",
        "crosswalk_layer": row["crosswalk_layer"],
        "crosswalk_decision": row["crosswalk_decision"],
        "confidence_gate_reference": row["confidence_gate_reference"],
        "notes": row["notes"],
    }


def quarantine_reason(row):
    if row["timeframe"] not in NATIVE_SUBHOUR_TIMEFRAMES:
        return "not_subhour_target"
    if "time_projection" in row["crosswalk_layer"]:
        return "projected_day_or_month_source_window_to_subhour_target"
    if row["source_lane"] == "sideways_scoped_dated_windows_from_accepted_gate":
        return "scoped_gate_reuse_not_source_owned_native_subhour"
    if row["source_lane"] == "sideways_scoped_dated_window":
        return "scoped_gate_reuse_not_source_owned_native_subhour"
    if row["evidence_type"] in {"dated_external_source_window", "source_window_crosswalk"}:
        return "dated_window_materialization_not_native_subhour_rows"
    return "not_proven_native_source_label"


def main():
    board_hash_before = sha256_file(BOARD_PATH)
    all_rows = []
    panels = []
    for source in PANEL_INPUTS:
        raw_rows = read_csv(source["path"])
        rows = [normalize_row(row, source) for row in raw_rows]
        all_rows.extend(rows)
        panels.append(
            {
                "run_id": source["run_id"],
                "path": str(source["path"].relative_to(REPO_ROOT)),
                "rows": len(rows),
                "timeframes": dict(Counter(row["timeframe"] for row in rows)),
                "source_lanes": dict(Counter(row["source_lane"] for row in rows)),
                "roots": dict(Counter(row["root"] for row in rows)),
            }
        )

    subhour_rows = [row for row in all_rows if row["timeframe"] in NATIVE_SUBHOUR_TIMEFRAMES]
    quarantine_rows = []
    for row in subhour_rows:
        reason = quarantine_reason(row)
        quarantine_rows.append({**row, "quarantine_reason": reason, "native_subhour_eligible": False})

    summary = {
        "run_id": RUN_ID,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "board_hash_before": board_hash_before,
        "decision": "native_subhour_projection_quarantine_v1=projected_subhour_rows_not_native_source_labels",
        "scope": "Audit old unified source-label panels for rows that look sub-hour but are actually projected dated windows.",
        "panels_read": panels,
        "total_rows_read": len(all_rows),
        "subhour_rows_read": len(subhour_rows),
        "native_subhour_eligible_rows": 0,
        "quarantined_subhour_rows": len(quarantine_rows),
        "subhour_timeframes": dict(Counter(row["timeframe"] for row in subhour_rows)),
        "subhour_roots": dict(Counter(row["root"] for row in subhour_rows)),
        "subhour_crosswalk_layers": dict(Counter(row["crosswalk_layer"] for row in subhour_rows)),
        "subhour_quarantine_reasons": dict(Counter(row["quarantine_reason"] for row in quarantine_rows)),
        "accepted_rows_added": 0,
        "new_confidence_gate": False,
        "native_subhour_source_overlap_closed": False,
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "trade_usable": False,
        "guardrails": [
            "Do not treat source-window projection rows as native sub-hour source labels.",
            "Do not treat scoped accepted gates as source-owned other-cycle validation rows.",
            "Do not rerun calibration from projected labels without a source-owned native sub-hour panel.",
        ],
    }

    (OUT_DIR / "native_subhour_projection_quarantine_v1.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True)
    )

    rows_path = OUT_DIR / "native_subhour_projection_quarantine_v1_rows.csv"
    with rows_path.open("w", newline="") as fh:
        fieldnames = [
            "source_run",
            "row_id",
            "root",
            "provider",
            "instrument",
            "market_context",
            "timeframe",
            "source_id",
            "evidence_type",
            "materialization_status",
            "date_granularity",
            "crosswalk_layer",
            "crosswalk_decision",
            "confidence_gate_reference",
            "quarantine_reason",
            "native_subhour_eligible",
        ]
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for row in quarantine_rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})

    md_lines = [
        "# Native Subhour Projection Quarantine v1",
        "",
        f"Run ID: `{RUN_ID}`",
        "",
        "This audit checks whether old unified source-label panel rows that carry `1m`, `5m`, `15m`, or `30m` timeframes can satisfy Board A native sub-hour validation. They cannot: every such row is a dated source-window projection, not a source-owned native sub-hour label panel.",
        "",
        "## Decision",
        "",
        "`native_subhour_projection_quarantine_v1=projected_subhour_rows_not_native_source_labels`",
        "",
        f"- Panels read: `{len(PANEL_INPUTS)}`.",
        f"- Total panel rows read: `{len(all_rows)}`.",
        f"- Sub-hour-looking rows read: `{len(subhour_rows)}`.",
        "- Native sub-hour eligible rows: `0`.",
        f"- Quarantined sub-hour rows: `{len(quarantine_rows)}`.",
        "- Accepted rows added: `0`.",
        "- New confidence gate: `false`.",
        "- Native sub-hour source overlap closed: `false`.",
        "- Strict full objective achieved: `false`; `update_goal=false`.",
        "- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; trade usable: `false`.",
        "",
        "## Counts",
        "",
        f"- Sub-hour timeframes: `{summary['subhour_timeframes']}`.",
        f"- Sub-hour roots: `{summary['subhour_roots']}`.",
        f"- Sub-hour crosswalk layers: `{summary['subhour_crosswalk_layers']}`.",
        f"- Quarantine reasons: `{summary['subhour_quarantine_reasons']}`.",
        "",
        "## Why It Still Blocks",
        "",
        "The sub-hour-looking rows are `Bull` / `Bear` / `Crisis` windows projected from S&P 500/Yardeni day windows or NBER month windows into `1m`, `5m`, `15m`, and `30m` targets. Projection can preserve provenance as a source-window attachment, but it is not a native source-owned sub-hour label. Board A still needs a real native sub-hour source panel or owner-approved rows before this gate can move.",
        "",
        "## Artifacts",
        "",
        f"- JSON: `{OUT_DIR / 'native_subhour_projection_quarantine_v1.json'}`",
        f"- Quarantine rows CSV: `{rows_path}`",
        f"- Assertions: `{CHECK_DIR / 'native_subhour_projection_quarantine_v1_assertions.out'}`",
    ]
    (OUT_DIR / "native_subhour_projection_quarantine_v1.md").write_text("\n".join(md_lines) + "\n")

    assertions = [
        "PASS decision=native_subhour_projection_quarantine_v1=projected_subhour_rows_not_native_source_labels",
        f"PASS subhour_rows_read={len(subhour_rows)}",
        "PASS native_subhour_eligible_rows=0",
        f"PASS quarantined_subhour_rows={len(quarantine_rows)}",
        "PASS update_goal=false",
    ]
    (CHECK_DIR / "native_subhour_projection_quarantine_v1_assertions.out").write_text(
        "\n".join(assertions) + "\n"
    )


if __name__ == "__main__":
    main()
