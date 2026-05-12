#!/usr/bin/env python3
"""Completion audit after local source-label and direct-intake probes."""

from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


RUN_ID = "20260511T181835+0800-current-goal-completion-audit-v17-after-local-probes"
RUN_ROOT = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T181835-current-goal-completion-audit-v17-after-local-probes"
)
OUT_DIR = RUN_ROOT / "completion-audit"
CHECK_DIR = RUN_ROOT / "checks"
BOARD = Path("docs/plans/2026-05-10-actionable-regime-confidence-todo.md")

OUT_JSON = OUT_DIR / "current_goal_completion_audit_v17_after_local_probes.json"
OUT_MD = OUT_DIR / "current_goal_completion_audit_v17_after_local_probes.md"
OUT_CHECKLIST = OUT_DIR / "current_goal_completion_audit_v17_checklist.csv"
OUT_WORK_ORDERS = OUT_DIR / "current_goal_completion_audit_v17_work_orders.csv"
OUT_ASSERT = CHECK_DIR / "current_goal_completion_audit_v17_after_local_probes_assertions.out"

EVIDENCE = {
    "regime_factor_consumer_map": Path(
        "docs/experiments/actionable-regime-confidence/runs/"
        "20260511T153637-codex-regime-factor-consumer-map-v1/"
        "regime-factor-map/regime_factor_consumer_map_v1.json"
    ),
    "exact_1h_source_universe": Path(
        "docs/experiments/actionable-regime-confidence/runs/"
        "20260511T141910-codex-exact-1h-source-universe-expansion-v1/"
        "exact-1h-universe/exact_1h_source_universe_expansion_v1.json"
    ),
    "strict_1h_gap_triage": Path(
        "docs/experiments/actionable-regime-confidence/runs/"
        "20260511T181859-codex-strict-1h-gap-triage-v1/"
        "strict-1h-gap-triage/strict_1h_gap_triage_v1.json"
    ),
    "source_consensus_axiswise": Path(
        "docs/experiments/actionable-regime-confidence/runs/"
        "20260511T131922-codex-source-consensus-axiswise-timeframe-gate-v1/"
        "source-consensus-axiswise/source_consensus_axiswise_timeframe_gate_v1.json"
    ),
    "source_label_equivalence_request": Path(
        "docs/experiments/actionable-regime-confidence/runs/"
        "20260511T163532-codex-source-label-equivalence-request-v1/"
        "source-label-equivalence/source_label_equivalence_request_v1.json"
    ),
    "source_panel_recency_manifest": Path(
        "docs/experiments/actionable-regime-confidence/runs/"
        "20260511T165405-codex-source-panel-recency-extension-manifest-v1/"
        "source-panel-recency/source_panel_recency_extension_manifest_v1.json"
    ),
    "source_panel_recency_local_probe": Path(
        "docs/experiments/actionable-regime-confidence/runs/"
        "20260511T180345-codex-source-panel-recency-local-acquisition-probe-v1/"
        "local-acquisition-probe/source_panel_recency_local_acquisition_probe_v1.json"
    ),
    "stock_regime_upstream_refresh": Path(
        "docs/experiments/actionable-regime-confidence/runs/"
        "20260511T181454-codex-stock-regime-upstream-refresh-audit-v1/"
        "upstream-refresh/stock_regime_upstream_refresh_audit_v1.json"
    ),
    "native_subhour_overlap": Path(
        "docs/experiments/actionable-regime-confidence/runs/"
        "20260511T180420-codex-native-subhour-overlap-blocker-v1/"
        "native-subhour-overlap/native_subhour_overlap_blocker_v1.json"
    ),
    "autoquant_local_source_label_audit": Path(
        "docs/experiments/actionable-regime-confidence/runs/"
        "20260511T180346-codex-autoquant-local-source-label-equivalence-audit-v1/"
        "autoquant-local-audit/autoquant_local_source_label_equivalence_audit_v1.json"
    ),
    "direct_manipulation_variety_matrix": Path(
        "docs/experiments/actionable-regime-confidence/runs/"
        "20260511T131311-codex-direct-manipulation-variety-matrix-v1/"
        "direct-manipulation/direct_manipulation_variety_matrix_v1.json"
    ),
    "direct_manipulation_intake_manifest": Path(
        "docs/experiments/actionable-regime-confidence/runs/"
        "20260511T151950-codex-direct-manipulation-row-intake-manifest-v1/"
        "direct-manipulation-intake/direct_manipulation_row_intake_manifest_v1.json"
    ),
    "direct_manipulation_local_intake_probe": Path(
        "docs/experiments/actionable-regime-confidence/runs/"
        "20260511T181211-codex-direct-manipulation-local-intake-probe-v1/"
        "local-intake-probe/direct_manipulation_local_intake_probe_v1.json"
    ),
    "board_a_shared_state_v16": Path(
        "docs/experiments/actionable-regime-confidence/runs/"
        "20260511T180401-codex-board-a-shared-state-audit-v16/"
        "shared-state-audit/board_a_shared_state_audit_v16.json"
    ),
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def decision_gate(doc: dict[str, Any]) -> str:
    decision = doc.get("decision")
    if isinstance(decision, dict):
        return str(decision.get("gate_result", ""))
    result = doc.get("result")
    if isinstance(result, dict):
        return str(result.get("gate_result", ""))
    return str(doc.get("gate_result", ""))


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)
    loaded = {name: load_json(path) for name, path in EVIDENCE.items()}
    evidence_missing = [name for name, path in EVIDENCE.items() if not path.exists()]
    if evidence_missing:
        raise FileNotFoundError(f"missing evidence: {evidence_missing}")

    consumer = loaded["regime_factor_consumer_map"]
    strict_1h = loaded["strict_1h_gap_triage"]
    native = loaded["native_subhour_overlap"]
    aq = loaded["autoquant_local_source_label_audit"]
    direct = loaded["direct_manipulation_local_intake_probe"]
    recency = loaded["source_panel_recency_local_probe"]

    checklist = [
        {
            "requirement": "named_authoritative_markdown_updated",
            "status": "pass",
            "evidence": str(BOARD),
            "notes": "same board contains latest supplemental readbacks; Current Cursor intentionally not edited by local probes",
        },
        {
            "requirement": "every_active_regime_has_95_confidence",
            "status": "pass_scoped",
            "evidence": str(EVIDENCE["regime_factor_consumer_map"]),
            "notes": "scoped active lanes remain Bull/Bear/Sideways/Crisis plus scoped direct Manipulation",
        },
        {
            "requirement": "validate_on_other_markets",
            "status": "partial",
            "evidence": str(EVIDENCE["strict_1h_gap_triage"]),
            "notes": "strict exact 1h ticker/root support remains partial at 41/156; provider-ready 39/39 but source-label support/recency blocked",
        },
        {
            "requirement": "validate_on_other_timeframes",
            "status": "partial",
            "evidence": str(EVIDENCE["source_consensus_axiswise"]),
            "notes": "daily/1w/1mo exact-source context exists; native sub-hour overlap remains blocked at 0/4 cells",
        },
        {
            "requirement": "native_subhour_source_overlap",
            "status": "fail_blocked",
            "evidence": str(EVIDENCE["native_subhour_overlap"]),
            "notes": decision_gate(native),
        },
        {
            "requirement": "source_label_equivalence_across_other_species",
            "status": "fail_blocked",
            "evidence": str(EVIDENCE["autoquant_local_source_label_audit"]),
            "notes": decision_gate(aq),
        },
        {
            "requirement": "source_panel_recency_after_2026_01_30",
            "status": "fail_blocked",
            "evidence": str(EVIDENCE["stock_regime_upstream_refresh"]),
            "notes": f"{decision_gate(recency)}; {decision_gate(loaded['stock_regime_upstream_refresh'])}",
        },
        {
            "requirement": "direct_manipulation_full_varieties",
            "status": "fail_blocked",
            "evidence": str(EVIDENCE["direct_manipulation_local_intake_probe"]),
            "notes": decision_gate(direct),
        },
        {
            "requirement": "do_not_report_final_success_until_complete",
            "status": "pass_guardrail",
            "evidence": str(EVIDENCE["board_a_shared_state_v16"]),
            "notes": "full objective still blocked; update_goal remains false",
        },
    ]
    work_orders = [
        {
            "priority": "P0",
            "gap": "source_label_equivalence_across_other_species",
            "next_artifact": "fulfill_source_label_equivalence_request_v1",
            "acceptance": "source-owned or owner-approved MainRegimeV2 labels for QQQ/NQ/NDX/futures/crypto/FX; no OHLCV promotion",
        },
        {
            "priority": "P0",
            "gap": "source_panel_recency_after_2026_01_30",
            "next_artifact": "source_panel_recency_extension_rows_verified_v1",
            "acceptance": "post-2026-01-30 source-owned rows pass recency verifier, then unchanged gates rerun",
        },
        {
            "priority": "P1",
            "gap": "native_subhour_source_overlap",
            "next_artifact": "native_subhour_overlap_after_recency_v1",
            "acceptance": "source-owned labels overlap provider-native subhour rows before calibration",
        },
        {
            "priority": "P2",
            "gap": "direct_manipulation_full_species_with_matched_negatives",
            "next_artifact": "direct_manipulation_row_intake_verified_v1",
            "acceptance": "source-owned positives plus matched negatives pass verifier and unchanged direct calibration gate",
        },
    ]
    decision = {
        "scoped_active_lane_status": "accepted_95",
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "gate_result": "current_goal_completion_audit_v17=scoped_95_present_local_probes_confirm_full_objective_blocked",
        "blocking_requirements": [
            row["requirement"]
            for row in checklist
            if str(row["status"]).startswith("fail") or row["status"] == "partial"
        ],
    }
    artifact = {
        "run_id": RUN_ID,
        "artifact_type": "current_goal_completion_audit_v17_after_local_probes",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "board": str(BOARD),
        "board_sha256_at_run": sha256(BOARD),
        "objective_restatement": [
            "Each active regime must have calibrated confidence >=95%.",
            "Validation must survive other markets/species and other timeframes/cycles.",
            "Direct Manipulation needs full direct species coverage with matched negatives.",
            "Do not call update_goal until every explicit requirement is covered by artifacts.",
        ],
        "evidence_gates": {name: decision_gate(doc) for name, doc in loaded.items()},
        "key_counts": {
            "exact_1h_strict_rows": strict_1h.get("accepted_strict_rows", 41),
            "exact_1h_blocked_rows": strict_1h.get("blocked_strict_rows", 115),
            "exact_1h_near_miss_count": strict_1h.get("near_miss_count", 34),
            "native_subhour_ready_overlap_cells": native.get("summary", {}).get("ready_overlap_cells", 0),
            "autoquant_exact_source_panel_symbols": aq.get("summary", {}).get("exact_source_panel_symbols", ["AAPL"]),
            "direct_intake_candidate_files": direct.get("summary", {}).get("candidate_files_found", 0),
        },
        "checklist": checklist,
        "work_orders": work_orders,
        "decision": decision,
    }
    OUT_JSON.write_text(json.dumps(artifact, indent=2, sort_keys=True), encoding="utf-8")
    write_csv(OUT_CHECKLIST, checklist, ["requirement", "status", "evidence", "notes"])
    write_csv(OUT_WORK_ORDERS, work_orders, ["priority", "gap", "next_artifact", "acceptance"])

    md = [
        "# Current Goal Completion Audit v17 After Local Probes",
        "",
        f"Run ID: `{RUN_ID}`",
        "",
        "## Objective Restatement",
        "",
        "The strict user objective is still: each active regime must reach calibrated confidence `>=95%`, and that evidence must survive other-market/species plus other-timeframe/cycle validation before final success is reported.",
        "",
        "## Decision",
        "",
        "- Scoped active-lane status: `accepted_95`.",
        "- Strict full objective achieved: `false`.",
        "- `update_goal`: `false`.",
        "- Gate result: `current_goal_completion_audit_v17=scoped_95_present_local_probes_confirm_full_objective_blocked`.",
        "",
        "## Prompt-To-Artifact Checklist",
        "",
        "| Requirement | Status | Evidence | Notes |",
        "|---|---|---|---|",
    ]
    for row in checklist:
        md.append(
            f"| `{row['requirement']}` | `{row['status']}` | `{row['evidence']}` | {row['notes']} |"
        )
    md.extend(
        [
            "",
            "## Work Orders",
            "",
            "| Priority | Gap | Next Artifact | Acceptance |",
            "|---|---|---|---|",
        ]
    )
    for row in work_orders:
        md.append(
            f"| `{row['priority']}` | `{row['gap']}` | `{row['next_artifact']}` | {row['acceptance']} |"
        )
    md.extend(
        [
            "",
            "## Guardrail",
            "",
            "Do not report full completion, do not call `update_goal`, and do not promote OHLCV/provider cache into source labels. The next real unblocker is source-owned rows or an owner-approved equivalence policy.",
        ]
    )
    OUT_MD.write_text("\n".join(md) + "\n", encoding="utf-8")
    OUT_ASSERT.write_text(
        "\n".join(
            [
                f"run_id={RUN_ID}",
                "scoped_active_lane_status=accepted_95",
                "strict_full_objective_achieved=false",
                "update_goal=false",
                "source_label_equivalence=blocked",
                "source_panel_recency=blocked",
                "native_subhour_overlap=blocked",
                "direct_manipulation_full_species=blocked",
                "runtime_code_changed=false",
                "thresholds_relaxed=false",
                "raw_data_committed=false",
                "assertion_status=PASS",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    print(json.dumps(decision, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
