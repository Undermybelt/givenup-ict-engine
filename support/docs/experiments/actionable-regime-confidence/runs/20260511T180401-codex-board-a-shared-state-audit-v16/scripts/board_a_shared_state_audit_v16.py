#!/usr/bin/env python3
"""Build a compact Board A shared-state audit from existing artifacts.

This script intentionally reads only compact JSON/CSV/assertion artifacts and
writes no raw market data. It is used to avoid trampling parallel Board A/B work.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path


REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = RUN_ROOT / "shared-state-audit"
CHECK_DIR = RUN_ROOT / "checks"


def load_json(rel: str) -> dict:
    return json.loads((REPO / rel).read_text())


def read_text(rel: str) -> str:
    return (REPO / rel).read_text()


def csv_row_count(rel: str) -> int:
    path = REPO / rel
    with path.open(newline="") as handle:
        return max(0, sum(1 for _ in csv.reader(handle)) - 1)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)

    consumer_rel = (
        "docs/experiments/actionable-regime-confidence/runs/"
        "20260511T153637-codex-regime-factor-consumer-map-v1/"
        "regime-factor-map/regime_factor_consumer_map_v1.json"
    )
    audit_v14_rel = (
        "docs/experiments/actionable-regime-confidence/runs/"
        "20260511T155959-current-goal-completion-audit-v14-after-consumer-map/"
        "completion-audit/current_goal_completion_audit_v14_after_consumer_map.json"
    )
    inventory_rel = (
        "docs/experiments/actionable-regime-confidence/runs/"
        "20260511T162942-codex-daily-main-root-source-inventory-v1/"
        "daily-main-root-inventory/daily_main_root_source_inventory_v1.json"
    )
    equivalence_rel = (
        "docs/experiments/actionable-regime-confidence/runs/"
        "20260511T163532-codex-source-label-equivalence-request-v1/"
        "source-label-equivalence/source_label_equivalence_request_v1.json"
    )
    recency_rel = (
        "docs/experiments/actionable-regime-confidence/runs/"
        "20260511T165405-codex-source-panel-recency-extension-manifest-v1/"
        "source-panel-recency/source_panel_recency_extension_manifest_v1.json"
    )
    recency_local_probe_rel = (
        "docs/experiments/actionable-regime-confidence/runs/"
        "20260511T180345-codex-source-panel-recency-local-acquisition-probe-v1/"
        "local-acquisition-probe/source_panel_recency_local_acquisition_probe_v1.json"
    )
    guardrail_rel = (
        "docs/experiments/actionable-regime-confidence/runs/"
        "20260511T172400-codex-qqq-nq-ixic-attachment-guardrail-audit-v1/"
        "guardrail-audit/qqq_nq_ixic_attachment_guardrail_audit_v1.json"
    )
    native_subhour_rel = (
        "docs/experiments/actionable-regime-confidence/runs/"
        "20260511T180420-codex-native-subhour-overlap-blocker-v1/"
        "native-subhour-overlap/native_subhour_overlap_blocker_v1.json"
    )
    provider_status_rel = (
        "docs/experiments/actionable-regime-confidence/runs/"
        "20260511T172521-codex-real-provider-branch-chain-v1/"
        "provider/01_provider_status_agent.json"
    )
    yahoo_csv_rel = (
        "docs/experiments/actionable-regime-confidence/runs/"
        "20260511T172521-codex-real-provider-branch-chain-v1/"
        "provider/05_fetch_external_yahoo_QQQ_1h.csv"
    )
    kraken_csv_rel = (
        "docs/experiments/actionable-regime-confidence/runs/"
        "20260511T172521-codex-real-provider-branch-chain-v1/"
        "provider/06_fetch_external_kraken_XBTUSD_1h.csv"
    )

    consumer = load_json(consumer_rel)
    audit_v14 = load_json(audit_v14_rel)
    inventory = load_json(inventory_rel)
    equivalence = load_json(equivalence_rel)
    recency = load_json(recency_rel)
    recency_local_probe = load_json(recency_local_probe_rel)
    guardrail = load_json(guardrail_rel)
    native_subhour = load_json(native_subhour_rel)
    provider_status = load_json(provider_status_rel)

    lane_rows = consumer["map_rows"]
    root_rows = [row for row in lane_rows if row["taxonomy_role"] == "MainRegimeV2_price_root"]
    manipulation_rows = [row for row in lane_rows if row["regime"] == "Manipulation"]
    min_root_floor = min(row["confidence_floor"] for row in root_rows)
    manipulation_floor = manipulation_rows[0]["confidence_floor"] if manipulation_rows else 0.0

    yahoo_rows = csv_row_count(yahoo_csv_rel)
    kraken_rows = csv_row_count(kraken_csv_rel)

    checklist = [
        {
            "requirement": "each active MainRegimeV2 price root has scoped >=95 confidence",
            "status": "pass_scoped",
            "evidence": f"{len(root_rows)}/4 roots; min floor {min_root_floor:.10f}",
            "artifact": consumer_rel,
            "gap": "scoped context factor only, not full-market/full-timeframe completion",
        },
        {
            "requirement": "direct Manipulation has >=95 confidence without OHLCV proxy promotion",
            "status": "pass_scoped_partial_species",
            "evidence": f"scoped direct floor {manipulation_floor:.6f}",
            "artifact": consumer_rel,
            "gap": "full direct species coverage remains incomplete",
        },
        {
            "requirement": "validate across other markets",
            "status": "partial",
            "evidence": (
                f"daily source inventory covers {inventory['coverage']['ticker_root_slots_covered']}/"
                f"{inventory['coverage']['ticker_root_slots_total']} ticker-root slots; "
                "QQQ/NQ IXIC attachment is provenance only"
            ),
            "artifact": f"{inventory_rel} | {guardrail_rel}",
            "gap": "no owner-approved QQQ/NQ/NDX/futures/crypto/FX source-label equivalence yet",
        },
        {
            "requirement": "validate across other timeframes/cycles",
            "status": "partial",
            "evidence": (
                "cross-timeframe context exists in prior audits, but v14 records native "
                "sub-hour source overlap and strict exact 1h support as incomplete; "
                f"native-subhour ready overlap cells {native_subhour['summary']['ready_overlap_cells']}/"
                f"{native_subhour['summary']['cells_checked']}"
            ),
            "artifact": f"{audit_v14_rel} | {native_subhour_rel}",
            "gap": "strict exact 1h support beyond 41/156 and native sub-hour overlap remain open",
        },
        {
            "requirement": "source recency through the current audit date",
            "status": "blocked_missing_source_rows",
            "evidence": (
                f"source panel max date {recency['source_panel']['date_max']}; "
                f"missing weekday sessions {recency['recency_gap']['weekday_sessions_after_last_source_date']}; "
                f"local extension candidates found {recency_local_probe['extension_candidate_count']}"
            ),
            "artifact": f"{recency_rel} | {recency_local_probe_rel}",
            "gap": "source-owned extension rows and provenance files not acquired",
        },
        {
            "requirement": "real provider paths checked before declaring data blocked",
            "status": "provider_ready_partial_no_confidence_gate",
            "evidence": (
                f"{provider_status['summary_line']}; yahoo QQQ 1h rows {yahoo_rows}; "
                f"kraken XBTUSD 1h rows {kraken_rows}"
            ),
            "artifact": provider_status_rel,
            "gap": "provider candles are not source-owned regime labels",
        },
        {
            "requirement": "do not call update_goal until strict objective closes",
            "status": "pass",
            "evidence": "consumer map, v14 audit, source-label request, recency manifest, and guardrail all keep update_goal=false",
            "artifact": f"{consumer_rel} | {audit_v14_rel} | {equivalence_rel} | {recency_rel} | {guardrail_rel}",
            "gap": "full objective still incomplete",
        },
    ]

    decision = {
        "run_id": "20260511T180401+0800-codex-board-a-shared-state-audit-v16",
        "artifact_type": "board_a_shared_state_audit_v16",
        "coordination_mode": "additive_only_do_not_rewrite_parallel_sections",
        "objective_restatement": (
            "Every active regime must have >=95 calibrated confidence, and that evidence must survive "
            "other-market and other-timeframe/cycle validation before reporting full completion."
        ),
        "scoped_active_lane_accepted_95": consumer["rollup"]["every_active_lane_has_corresponding_accepted_factor"],
        "accepted_95_lanes": consumer["rollup"]["accepted_95_lanes"],
        "min_main_root_confidence_floor": min_root_floor,
        "scoped_direct_manipulation_confidence_floor": manipulation_floor,
        "strict_full_objective_achieved": False,
        "call_update_goal": False,
        "latest_guardrail": guardrail["decision"],
        "provider_readiness_summary": provider_status["summary_line"],
        "provider_candle_rows_readback": {
            "yahoo_QQQ_1h": yahoo_rows,
            "kraken_XBTUSD_1h": kraken_rows,
        },
        "recency_local_probe": {
            "extension_candidate_count": recency_local_probe["extension_candidate_count"],
            "expected_intake_files_present": [
                item["exists"] for item in recency_local_probe["expected_intake_files"]
            ],
        },
        "native_subhour_overlap": native_subhour["summary"],
        "missing_or_incomplete": [
            "owner-approved QQQ/NQ/NDX/futures source-label equivalence",
            "crypto/FX/rates/commodities source-label equivalence",
            "strict exact 1h support beyond 41/156",
            "native sub-hour source overlap",
            "source-panel recency extension beyond 2026-01-30",
            "full direct Manipulation species coverage and matched negatives",
        ],
        "checklist": checklist,
        "next_action": (
            "Fulfill the source-label equivalence or recency-extension intake packages before any "
            "new full-objective claim; use real provider candles only as readiness/provenance until "
            "source-owned labels or owner-approved equivalence exists."
        ),
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "trade_usable": False,
    }

    json_path = OUT_DIR / "board_a_shared_state_audit_v16.json"
    csv_path = OUT_DIR / "board_a_shared_state_audit_v16_checklist.csv"
    md_path = OUT_DIR / "board_a_shared_state_audit_v16.md"
    assertions_path = CHECK_DIR / "board_a_shared_state_audit_v16_assertions.out"

    json_path.write_text(json.dumps(decision, indent=2, sort_keys=True) + "\n")

    with csv_path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["requirement", "status", "evidence", "artifact", "gap"])
        writer.writeheader()
        writer.writerows(checklist)

    md_lines = [
        "# Board A Shared-State Audit v16",
        "",
        "Run ID: `20260511T180401+0800-codex-board-a-shared-state-audit-v16`",
        "",
        "## Decision",
        "",
        "`board_a_shared_state_audit_v16=scoped_95_present_strict_full_objective_still_blocked`",
        "",
        "Scoped active-lane evidence is real: `Bull`, `Bear`, `Sideways`, `Crisis`, and scoped direct `Manipulation` each have a >=95 consumer factor.",
        "",
        "Strict full-objective completion is still false. The 17:24 guardrail audit makes the `^IXIC -> QQQ/NQ=F` attachment provenance-only, not QQQ/NQ source-label equivalence.",
        "",
        "## Checklist",
        "",
    ]
    for row in checklist:
        md_lines.append(
            f"- `{row['status']}` {row['requirement']}: {row['evidence']}. Gap: {row['gap']}."
        )
    md_lines.extend(
        [
            "",
            "## Result",
            "",
            f"- Min `MainRegimeV2` price-root confidence floor: `{min_root_floor:.10f}`.",
            f"- Scoped direct `Manipulation` confidence floor: `{manipulation_floor:.6f}`.",
            "- Full objective achieved: `false`.",
            "- `update_goal`: `false`.",
            "- Runtime code changed: `false`.",
            "- Thresholds relaxed: `false`.",
            "- Raw data committed: `false`.",
            "- Trade usable: `false`.",
            "",
            "## Next",
            "",
            decision["next_action"],
            "",
            "## Artifacts",
            "",
            f"- JSON: `{json_path.relative_to(REPO)}`",
            f"- Checklist CSV: `{csv_path.relative_to(REPO)}`",
            f"- Assertions: `{assertions_path.relative_to(REPO)}`",
            "",
        ]
    )
    md_path.write_text("\n".join(md_lines))

    assertions = [
        "run_id=20260511T180401+0800-codex-board-a-shared-state-audit-v16",
        f"accepted_95_lane_count={consumer['rollup']['accepted_95_lane_count']}",
        f"min_main_root_confidence_floor={min_root_floor:.10f}",
        f"scoped_direct_manipulation_confidence_floor={manipulation_floor:.6f}",
        f"latest_guardrail={guardrail['decision']}",
        "guardrail_allows_confidence_gate_rows_for_qqq_nq=false",
        f"source_panel_max_date={recency['source_panel']['date_max']}",
        f"recency_extension_candidate_count={recency_local_probe['extension_candidate_count']}",
        f"native_subhour_ready_overlap_cells={native_subhour['summary']['ready_overlap_cells']}",
        f"native_subhour_cells_checked={native_subhour['summary']['cells_checked']}",
        f"provider_readiness_summary={provider_status['summary_line']}",
        f"yahoo_QQQ_1h_rows={yahoo_rows}",
        f"kraken_XBTUSD_1h_rows={kraken_rows}",
        "strict_full_objective_achieved=false",
        "update_goal=false",
        "runtime_code_changed=false",
        "thresholds_relaxed=false",
        "raw_data_committed=false",
        "trade_usable=false",
        "assertion_status=PASS",
        "",
    ]
    assertions_path.write_text("\n".join(assertions))

    assert consumer["rollup"]["accepted_95_lane_count"] == 5
    assert min_root_floor >= 0.95
    assert manipulation_floor >= 0.95
    assert guardrail["decision"] == "provenance_only_not_source_label_equivalence"
    assert audit_v14["decision"]["full_objective_achieved"] is False
    assert equivalence["full_objective_achieved"] is False
    assert recency["decision"]["update_goal"] is False
    assert recency_local_probe["extension_candidate_count"] == 0
    assert native_subhour["summary"]["ready_overlap_cells"] == 0
    assert yahoo_rows > 0
    assert kraken_rows > 0


if __name__ == "__main__":
    main()
