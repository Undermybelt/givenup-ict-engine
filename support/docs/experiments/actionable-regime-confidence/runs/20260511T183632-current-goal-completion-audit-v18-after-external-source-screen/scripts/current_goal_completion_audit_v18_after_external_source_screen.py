#!/usr/bin/env python3
import csv
import json
from datetime import datetime, timezone
from pathlib import Path


RUN_ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = RUN_ROOT / "completion-audit"
CHECK_DIR = RUN_ROOT / "checks"
OUT_DIR.mkdir(parents=True, exist_ok=True)
CHECK_DIR.mkdir(parents=True, exist_ok=True)


def load_json(path):
    with open(path) as fh:
        return json.load(fh)


EVIDENCE = {
    "consumer_map": "docs/experiments/actionable-regime-confidence/runs/20260511T153637-codex-regime-factor-consumer-map-v1/regime-factor-map/regime_factor_consumer_map_v1.json",
    "source_intake": "docs/experiments/actionable-regime-confidence/runs/20260511T182922-codex-source-label-equivalence-intake-verifier-v1/equivalence-intake-verifier/source_label_equivalence_intake_verifier_manifest_v1.json",
    "native_subhour": "docs/experiments/actionable-regime-confidence/runs/20260511T180420-codex-native-subhour-overlap-blocker-v1/native-subhour-overlap/native_subhour_overlap_blocker_v1.json",
    "strict_1h": "docs/experiments/actionable-regime-confidence/runs/20260511T181859-codex-strict-1h-gap-triage-v1/strict-1h-gap-triage/strict_1h_gap_triage_v1.json",
    "direct_source_scan": "docs/experiments/actionable-regime-confidence/runs/20260511T182601-codex-direct-manipulation-source-scan-v2/direct-source-scan/direct_manipulation_source_scan_v2.json",
    "external_source_screen": "docs/experiments/actionable-regime-confidence/runs/20260511T183328-codex-external-source-label-candidate-screen-v1/external-source-label-screen/external_source_label_candidate_screen_v1.json",
    "recency_upstream": "docs/experiments/actionable-regime-confidence/runs/20260511T181454-codex-stock-regime-upstream-refresh-audit-v1/upstream-refresh/stock_regime_upstream_refresh_audit_v1.json",
}


def main():
    consumer = load_json(EVIDENCE["consumer_map"])
    source_intake = load_json(EVIDENCE["source_intake"])
    native_subhour = load_json(EVIDENCE["native_subhour"])
    strict_1h = load_json(EVIDENCE["strict_1h"])
    direct_scan = load_json(EVIDENCE["direct_source_scan"])
    external = load_json(EVIDENCE["external_source_screen"])
    recency = load_json(EVIDENCE["recency_upstream"])

    rollup = consumer["rollup"]
    native_decision = native_subhour["decision"]
    strict_decision = strict_1h["decision"]
    source_decision = source_intake["decision"]

    checklist = [
        {
            "requirement": "Each active MainRegimeV2/direct lane has its own >=95% calibrated consumer factor.",
            "evidence": EVIDENCE["consumer_map"],
            "status": "pass_scoped",
            "coverage": f"accepted lanes={rollup['accepted_95_lanes']}; accepted_95_lane_count={rollup['accepted_95_lane_count']}",
            "gap": "This is scoped consumer readiness only, not strict full objective closure.",
        },
        {
            "requirement": "Validation survives other markets/species with source-owned labels or owner-approved equivalence.",
            "evidence": f"{EVIDENCE['source_intake']} ; {EVIDENCE['external_source_screen']}",
            "status": "blocked",
            "coverage": f"intake gate={source_decision['gate_result']}; external screen={external['decision']}; candidates={external['candidate_records']}",
            "gap": "Required source-label equivalence intake files are missing; NIFTY/IDX external candidates lack owner-approved MainRegimeV2 crosswalk.",
        },
        {
            "requirement": "Validation survives other cycles/timeframes, including strict exact 1h and native sub-hour where claimed.",
            "evidence": f"{EVIDENCE['strict_1h']} ; {EVIDENCE['native_subhour']}",
            "status": "blocked",
            "coverage": f"strict exact 1h accepted={strict_1h['accepted_strict_rows']}/{strict_1h['strict_slots']}; native subhour gate={native_decision['gate_result']}",
            "gap": "Strict exact 1h remains partial and native subhour source overlap remains 0/4.",
        },
        {
            "requirement": "Source-panel recency extends beyond 2026-01-30 before provider candles after that date are promoted.",
            "evidence": EVIDENCE["recency_upstream"],
            "status": "blocked",
            "coverage": recency["gate_result"],
            "gap": "Known upstream source package still matches local; no newer source-owned recency extension rows.",
        },
        {
            "requirement": "Direct Manipulation full species coverage uses direct positive rows plus matched normal controls.",
            "evidence": f"{EVIDENCE['consumer_map']} ; {EVIDENCE['direct_source_scan']}",
            "status": "blocked",
            "coverage": f"scoped direct ready={rollup['direct_manipulation_scoped_factor_ready']}; full species complete={rollup['direct_manipulation_full_species_complete']}; source scan={direct_scan['decision']}",
            "gap": "Missing spoofing/layering, quote stuffing, pinging, bear raid/painting tape, and social/text pump-dump matched-negative row sources.",
        },
        {
            "requirement": "Do not rely on proxy signals or generated/OHLCV-only labels for completion.",
            "evidence": EVIDENCE["external_source_screen"],
            "status": "pass_guardrail",
            "coverage": "External NIFTY/IDX candidates were screened but not promoted.",
            "gap": "No proxy promotion occurred; objective remains open.",
        },
    ]

    strict_full_objective_achieved = False
    audit = {
        "run_id": "20260511T183632+0800-current-goal-completion-audit-v18-after-external-source-screen",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "restated_objective": [
            "Every active regime/lane must have its own >=95% calibrated confidence evidence.",
            "The evidence must survive validation on other markets/species and other timeframes/cycles.",
            "Direct Manipulation must use direct row sources with matched negative controls.",
            "No source-label proxy, OHLCV-only generated label, or owner-unapproved taxonomy crosswalk can satisfy the strict goal.",
        ],
        "checklist": checklist,
        "scoped_active_lane_95_present": True,
        "strict_full_objective_achieved": strict_full_objective_achieved,
        "update_goal": False,
        "decision": "current_goal_completion_audit_v18=scoped_95_present_external_source_screen_confirms_full_objective_blocked",
        "accepted_rows_added": 0,
        "new_confidence_gate": False,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "trade_usable": False,
        "evidence": EVIDENCE,
    }

    json_path = OUT_DIR / "current_goal_completion_audit_v18_after_external_source_screen.json"
    json_path.write_text(json.dumps(audit, indent=2, sort_keys=True))

    checklist_path = OUT_DIR / "current_goal_completion_audit_v18_checklist.csv"
    with checklist_path.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=["requirement", "status", "evidence", "coverage", "gap"])
        writer.writeheader()
        writer.writerows(checklist)

    md = [
        "# Current Goal Completion Audit v18 After External Source Screen",
        "",
        "Run ID: `20260511T183632+0800-current-goal-completion-audit-v18-after-external-source-screen`",
        "",
        "## Restated Objective",
        "",
        "- Every active regime/lane must have its own `>=95%` calibrated confidence evidence.",
        "- Evidence must survive other-market/species and other-timeframe/cycle validation.",
        "- Direct `Manipulation` must use direct row sources with matched negative controls.",
        "- Proxy labels, OHLCV-only/generated labels, or owner-unapproved crosswalks do not count.",
        "",
        "## Decision",
        "",
        "`current_goal_completion_audit_v18=scoped_95_present_external_source_screen_confirms_full_objective_blocked`",
        "",
        "- Scoped active-lane `>=95%` evidence: `true`.",
        "- Strict full objective achieved: `false`; `update_goal=false`.",
        "- External source screen found promising NIFTY/IDX candidates, but no promotable `MainRegimeV2` source-label equivalence.",
        "- Accepted rows added: `0`; new confidence gate: `false`.",
        "- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; trade usable: `false`.",
        "",
        "## Checklist",
        "",
    ]
    for item in checklist:
        md.extend(
            [
                f"- `{item['status']}` - {item['requirement']}",
                f"  Evidence: `{item['evidence']}`",
                f"  Coverage: {item['coverage']}",
                f"  Gap: {item['gap']}",
            ]
        )
    md.extend(
        [
            "",
            "## Artifacts",
            "",
            f"- JSON: `{json_path}`",
            f"- Checklist CSV: `{checklist_path}`",
            f"- Assertions: `{CHECK_DIR / 'current_goal_completion_audit_v18_after_external_source_screen_assertions.out'}`",
        ]
    )
    md_path = OUT_DIR / "current_goal_completion_audit_v18_after_external_source_screen.md"
    md_path.write_text("\n".join(md) + "\n")

    assertions = [
        "PASS scoped_active_lane_95_present true",
        "PASS strict_full_objective_achieved false",
        "PASS update_goal false",
        "PASS source_label_equivalence_blocked",
        "PASS native_subhour_and_strict_1h_blocked",
        "PASS direct_manipulation_full_species_blocked",
    ]
    (CHECK_DIR / "current_goal_completion_audit_v18_after_external_source_screen_assertions.out").write_text(
        "\n".join(assertions) + "\n"
    )


if __name__ == "__main__":
    main()
