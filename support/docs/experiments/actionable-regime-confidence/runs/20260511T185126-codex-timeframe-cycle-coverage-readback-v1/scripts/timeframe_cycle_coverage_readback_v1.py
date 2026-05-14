#!/usr/bin/env python3
"""Read back Board A other-timeframe/cycle coverage from existing artifacts."""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[6]
RUN_ID = "20260511T185126+0800-codex-timeframe-cycle-coverage-readback-v1"
RUN_ROOT = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T185126-codex-timeframe-cycle-coverage-readback-v1"
)
OUT_DIR = RUN_ROOT / "timeframe-cycle-readback"
CHECK_DIR = RUN_ROOT / "checks"
OUT_JSON = OUT_DIR / "timeframe_cycle_coverage_readback_v1.json"
OUT_MD = OUT_DIR / "timeframe_cycle_coverage_readback_v1.md"
OUT_CSV = OUT_DIR / "timeframe_cycle_coverage_readback_v1_rows.csv"
OUT_ASSERT = CHECK_DIR / "timeframe_cycle_coverage_readback_v1_assertions.out"

NATIVE_SUBHOUR_JSON = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T180420-codex-native-subhour-overlap-blocker-v1/"
    "native-subhour-overlap/native_subhour_overlap_blocker_v1.json"
)
STRICT_1H_TRIAGE_JSON = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T181859-codex-strict-1h-gap-triage-v1/"
    "strict-1h-gap-triage/strict_1h_gap_triage_v1.json"
)
NEAR_MISS_JSON = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T184151-codex-strict-1h-near-miss-extension-requirements-v1/"
    "strict-1h-extension-requirements/strict_1h_near_miss_extension_requirements_v1.json"
)
JAN2026_TAIL_JSON = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T184530-codex-strict-1h-jan2026-tail-support-probe-v1/"
    "jan2026-tail-support/strict_1h_jan2026_tail_support_probe_v1.json"
)
UPSTREAM_REFRESH_JSON = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T181454-codex-stock-regime-upstream-refresh-audit-v1/"
    "upstream-refresh/stock_regime_upstream_refresh_audit_v1.json"
)
RECENCY_LOCAL_JSON = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T180345-codex-source-panel-recency-local-acquisition-probe-v1/"
    "local-acquisition-probe/source_panel_recency_local_acquisition_probe_v1.json"
)


def repo_rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO))
    except ValueError:
        return str(path)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def build_rows(
    native: dict[str, Any],
    strict: dict[str, Any],
    near: dict[str, Any],
    tail: dict[str, Any],
    upstream: dict[str, Any],
    recency: dict[str, Any],
) -> list[dict[str, Any]]:
    native_summary = native.get("summary", {})
    near_counts = near.get("counts", {})
    tail_counts = tail.get("counts", {})
    return [
        {
            "axis": "native_subhour_overlap",
            "artifact": repo_rel(NATIVE_SUBHOUR_JSON),
            "covered": native_summary.get("ready_overlap_cells", 0),
            "total": native_summary.get("cells_checked", 0),
            "accepted_added": native.get("decision", {}).get("accepted_rows_added", 0),
            "decision": native.get("decision", {}).get("gate_result", ""),
            "gap": "native source overlap remains 0 cells",
        },
        {
            "axis": "strict_exact_1h",
            "artifact": repo_rel(STRICT_1H_TRIAGE_JSON),
            "covered": strict.get("accepted_strict_rows", 0),
            "total": strict.get("strict_slots", 0),
            "accepted_added": strict.get("decision", {}).get("accepted_rows_added", 0),
            "decision": strict.get("decision", {}).get("gate_result", ""),
            "gap": f"blocked rows={strict.get('blocked_strict_rows')}; provider-ready tickers={strict.get('provider_ready_tickers')}; source labels/recency block completion",
        },
        {
            "axis": "strict_1h_near_miss_extension",
            "artifact": repo_rel(NEAR_MISS_JSON),
            "covered": near_counts.get("post_2025_extension_candidate_rows", 0),
            "total": near_counts.get("blocked_current_strict_rows", 0),
            "accepted_added": near_counts.get("accepted_rows_added", 0),
            "decision": near.get("decision", {}).get("gate_result", ""),
            "gap": "future source-extension targets identified, but no current fixed-split row promoted",
        },
        {
            "axis": "jan2026_tail_support",
            "artifact": repo_rel(JAN2026_TAIL_JSON),
            "covered": tail_counts.get("tail_covers_missing_extra_rows", 0),
            "total": tail_counts.get("candidate_rows", 0),
            "accepted_added": tail_counts.get("accepted_rows_added", 0),
            "decision": tail.get("decision", {}).get("gate_result", ""),
            "gap": f"standalone tail gate passes={tail_counts.get('standalone_tail_gate_passes', 0)}; tail is future-gate only",
        },
        {
            "axis": "upstream_source_recency",
            "artifact": repo_rel(UPSTREAM_REFRESH_JSON),
            "covered": 0,
            "total": 1,
            "accepted_added": upstream.get("accepted_rows_added", 0),
            "decision": upstream.get("gate_result", upstream.get("decision", "")),
            "gap": f"source tail remains {upstream.get('local_summary', {}).get('date_max', '2026-01-30')}; no newer upstream revision",
        },
        {
            "axis": "local_recency_extension_intake",
            "artifact": repo_rel(RECENCY_LOCAL_JSON),
            "covered": 0,
            "total": 1,
            "accepted_added": recency.get("accepted_rows_added", recency.get("decision", {}).get("accepted_rows_added", 0)),
            "decision": recency.get("gate_result", recency.get("decision", {}).get("gate_result", "")),
            "gap": "no local source-owned recency extension rows found",
        },
    ]


def write_csv(rows: list[dict[str, Any]]) -> None:
    fields = ["axis", "artifact", "covered", "total", "accepted_added", "decision", "gap"]
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUT_CSV.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def write_markdown(payload: dict[str, Any]) -> None:
    lines = [
        "# Timeframe/Cycle Coverage Readback v1",
        "",
        f"Run ID: `{RUN_ID}`",
        "",
        "This readback merges existing strict `1h`, native sub-hour, Jan-2026 tail, and source-recency artifacts. It does not fetch raw rows and does not edit the shared Current Cursor.",
        "",
        "## Decision",
        "",
        f"`{payload['decision']['gate_result']}`",
        "",
        f"- Strict exact `1h` accepted rows: `{payload['strict_1h_accepted_rows']}/{payload['strict_1h_total_slots']}`.",
        f"- Native sub-hour ready overlap cells: `{payload['native_subhour_ready_cells']}/{payload['native_subhour_total_cells']}`.",
        f"- Jan-2026 tail source support candidates covered: `{payload['jan2026_tail_covers_missing_extra_rows']}/{payload['jan2026_tail_candidate_rows']}`.",
        f"- Standalone Jan-2026 tail gates passing: `{payload['jan2026_tail_standalone_gate_passes']}`.",
        "- Accepted rows added: `0`.",
        "- Full other-cycle/timeframe validation: `false`.",
        "- Full objective achieved: `false`; `update_goal=false`.",
        "",
        "## Rows",
        "",
        "| Axis | Covered | Total | Accepted Added | Decision | Gap |",
        "|---|---:|---:|---:|---|---|",
    ]
    for row in payload["rows"]:
        lines.append(
            f"| `{row['axis']}` | `{row['covered']}` | `{row['total']}` | `{row['accepted_added']}` | `{row['decision']}` | {row['gap']} |"
        )
    lines.extend(
        [
            "",
            "## Readback",
            "",
            "- Provider `1h` data readiness is not the blocker; source-label support and recency are.",
            "- Existing Jan-2026 source tail helps identify future-gate candidates, but it does not retroactively repair the fixed 2024/2025 strict gate.",
            "- Native sub-hour remains blocked at `0` source-overlap cells.",
            "- The known upstream stock-regime source still ends at `2026-01-30`; provider candles after that date are not promoted into labels.",
        ]
    )
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)
    native = load_json(NATIVE_SUBHOUR_JSON)
    strict = load_json(STRICT_1H_TRIAGE_JSON)
    near = load_json(NEAR_MISS_JSON)
    tail = load_json(JAN2026_TAIL_JSON)
    upstream = load_json(UPSTREAM_REFRESH_JSON)
    recency = load_json(RECENCY_LOCAL_JSON)
    rows = build_rows(native, strict, near, tail, upstream, recency)
    native_summary = native.get("summary", {})
    tail_counts = tail.get("counts", {})
    payload = {
        "run_id": RUN_ID,
        "artifact_type": "timeframe_cycle_coverage_readback_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "current_cursor_edited": False,
        "rows": rows,
        "strict_1h_accepted_rows": strict.get("accepted_strict_rows", 0),
        "strict_1h_total_slots": strict.get("strict_slots", 0),
        "native_subhour_ready_cells": native_summary.get("ready_overlap_cells", 0),
        "native_subhour_total_cells": native_summary.get("cells_checked", 0),
        "jan2026_tail_covers_missing_extra_rows": tail_counts.get("tail_covers_missing_extra_rows", 0),
        "jan2026_tail_candidate_rows": tail_counts.get("candidate_rows", 0),
        "jan2026_tail_standalone_gate_passes": tail_counts.get("standalone_tail_gate_passes", 0),
        "decision": {
            "gate_result": "timeframe_cycle_coverage_readback_v1=strict_1h_partial_native_subhour_recency_blocked",
            "accepted_rows_added": 0,
            "new_confidence_gate": False,
            "full_other_cycle_timeframe_validation": False,
            "full_objective_achieved": False,
            "update_goal": False,
            "runtime_code_changed": False,
            "thresholds_relaxed": False,
            "raw_data_committed": False,
            "trade_usable": False,
        },
    }
    OUT_JSON.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_csv(rows)
    write_markdown(payload)
    assertions = [
        "PASS row_count=6" if len(rows) == 6 else "FAIL row_count",
        "PASS strict_1h_accepted_rows=41" if payload["strict_1h_accepted_rows"] == 41 else "FAIL strict_1h_accepted_rows",
        "PASS strict_1h_total_slots=156" if payload["strict_1h_total_slots"] == 156 else "FAIL strict_1h_total_slots",
        "PASS native_subhour_ready_cells=0" if payload["native_subhour_ready_cells"] == 0 else "FAIL native_subhour_ready_cells",
        "PASS jan2026_tail_standalone_gate_passes=0" if payload["jan2026_tail_standalone_gate_passes"] == 0 else "FAIL jan2026_tail_standalone_gate_passes",
        "PASS full_objective=false" if not payload["decision"]["full_objective_achieved"] else "FAIL full_objective",
        "PASS current_cursor_edited=false" if not payload["current_cursor_edited"] else "FAIL current_cursor_edited",
    ]
    OUT_ASSERT.write_text("\n".join(assertions) + "\n", encoding="utf-8")
    if any(line.startswith("FAIL") for line in assertions):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
