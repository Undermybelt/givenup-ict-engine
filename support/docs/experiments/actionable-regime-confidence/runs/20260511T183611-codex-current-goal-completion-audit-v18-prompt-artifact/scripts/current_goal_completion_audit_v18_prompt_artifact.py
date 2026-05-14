#!/usr/bin/env python3
"""Prompt-to-artifact completion audit for Board A.

This script is readback-only: it inspects versioned evidence and writes a
completion-audit packet. It does not accept rows, relax thresholds, or mutate
runtime code.
"""

from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


RUN_ID = "20260511T183611+0800-codex-current-goal-completion-audit-v18-prompt-artifact"
RUN_ROOT = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T183611-codex-current-goal-completion-audit-v18-prompt-artifact"
)
OUT_DIR = RUN_ROOT / "completion-audit"
CHECK_DIR = RUN_ROOT / "checks"
BOARD = Path("docs/plans/2026-05-10-actionable-regime-confidence-todo.md")

EVIDENCE = {
    "consumer_map": Path(
        "docs/experiments/actionable-regime-confidence/runs/"
        "20260511T153637-codex-regime-factor-consumer-map-v1/"
        "regime-factor-map/regime_factor_consumer_map_v1.json"
    ),
    "shared_state_v16": Path(
        "docs/experiments/actionable-regime-confidence/runs/"
        "20260511T180401-codex-board-a-shared-state-audit-v16/"
        "shared-state-audit/board_a_shared_state_audit_v16.json"
    ),
    "autoquant_source_label": Path(
        "docs/experiments/actionable-regime-confidence/runs/"
        "20260511T180346-codex-autoquant-local-source-label-equivalence-audit-v1/"
        "autoquant-local-audit/autoquant_local_source_label_equivalence_audit_v1.json"
    ),
    "source_equivalence_request": Path(
        "docs/experiments/actionable-regime-confidence/runs/"
        "20260511T163532-codex-source-label-equivalence-request-v1/"
        "source-label-equivalence/source_label_equivalence_request_v1.json"
    ),
    "source_equivalence_verifier_manifest": Path(
        "docs/experiments/actionable-regime-confidence/runs/"
        "20260511T182922-codex-source-label-equivalence-intake-verifier-v1/"
        "equivalence-intake-verifier/source_label_equivalence_intake_verifier_manifest_v1.json"
    ),
    "source_equivalence_missing_result": Path(
        "docs/experiments/actionable-regime-confidence/runs/"
        "20260511T182922-codex-source-label-equivalence-intake-verifier-v1/"
        "equivalence-intake-verifier/source_label_equivalence_intake_verifier_missing_result_v1.json"
    ),
    "external_source_screen": Path(
        "docs/experiments/actionable-regime-confidence/runs/"
        "20260511T183328-codex-external-source-label-candidate-screen-v1/"
        "external-source-label-screen/external_source_label_candidate_screen_v1.json"
    ),
    "macro_stress_schema": Path(
        "docs/experiments/actionable-regime-confidence/runs/"
        "20260511T183329-codex-macro-stress-asset-regime-schema-audit-v1/"
        "macro-stress-schema/macro_stress_asset_regime_schema_audit_v1.json"
    ),
    "native_subhour": Path(
        "docs/experiments/actionable-regime-confidence/runs/"
        "20260511T180420-codex-native-subhour-overlap-blocker-v1/"
        "native-subhour-overlap/native_subhour_overlap_blocker_v1.json"
    ),
    "strict_1h": Path(
        "docs/experiments/actionable-regime-confidence/runs/"
        "20260511T181859-codex-strict-1h-gap-triage-v1/"
        "strict-1h-gap-triage/strict_1h_gap_triage_v1.json"
    ),
    "recency_upstream": Path(
        "docs/experiments/actionable-regime-confidence/runs/"
        "20260511T181454-codex-stock-regime-upstream-refresh-audit-v1/"
        "upstream-refresh/stock_regime_upstream_refresh_audit_v1.json"
    ),
    "direct_local_intake": Path(
        "docs/experiments/actionable-regime-confidence/runs/"
        "20260511T181211-codex-direct-manipulation-local-intake-probe-v1/"
        "local-intake-probe/direct_manipulation_local_intake_probe_v1.json"
    ),
    "direct_source_scan_v2": Path(
        "docs/experiments/actionable-regime-confidence/runs/"
        "20260511T182601-codex-direct-manipulation-source-scan-v2/"
        "direct-source-scan/direct_manipulation_source_scan_v2.json"
    ),
    "hf_pumpdump_schema": Path(
        "docs/experiments/actionable-regime-confidence/runs/"
        "20260511T183018-codex-hf-pumpdump-schema-audit-v1/"
        "hf-pumpdump-schema/hf_pumpdump_schema_audit_v1.json"
    ),
    "prior_completion_v17": Path(
        "docs/experiments/actionable-regime-confidence/runs/"
        "20260511T182155-current-goal-completion-audit-v17-after-local-upstream-probes/"
        "completion-audit/current_goal_completion_audit_v17_after_local_upstream_probes.json"
    ),
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"_missing_file": str(path)}
    return json.loads(path.read_text())


def get(data: dict[str, Any], path: list[str], default: Any = None) -> Any:
    cur: Any = data
    for key in path:
        if not isinstance(cur, dict) or key not in cur:
            return default
        cur = cur[key]
    return cur


def status_from_bool(ok: bool, pass_status: str, fail_status: str) -> str:
    return pass_status if ok else fail_status


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)

    data = {name: load_json(path) for name, path in EVIDENCE.items()}
    board_hash = sha256(BOARD) if BOARD.exists() else "missing"

    consumer = data["consumer_map"]
    consumer_rollup = consumer.get("rollup", {})
    active_lanes = consumer_rollup.get("accepted_95_lanes", [])
    expected_lanes = ["Bull", "Bear", "Sideways", "Crisis", "Manipulation"]
    lane_set = set(active_lanes)
    lane_rows = consumer.get("map_rows", [])
    min_price_floor = min(
        [
            float(row.get("confidence_floor", 0))
            for row in lane_rows
            if row.get("taxonomy_role") == "MainRegimeV2_price_root"
        ],
        default=0.0,
    )
    direct_floor = min(
        [
            float(row.get("confidence_floor", 0))
            for row in lane_rows
            if row.get("regime") == "Manipulation"
        ],
        default=0.0,
    )
    scoped_95_ok = all(lane in lane_set for lane in expected_lanes) and min_price_floor >= 0.95 and direct_floor >= 0.95

    strict = data["strict_1h"]
    strict_accepted = int(
        get(strict, ["summary", "accepted_strict_rows"], get(strict, ["accepted_strict_rows"], 0)) or 0
    )
    strict_total = int(
        get(strict, ["summary", "strict_ticker_root_slots"], get(strict, ["strict_ticker_root_slots"], 156)) or 156
    )
    strict_blocked = int(
        get(strict, ["summary", "blocked_strict_rows"], get(strict, ["blocked_strict_rows"], 0)) or 0
    )

    native = data["native_subhour"]
    native_ready = int(
        get(native, ["summary", "ready_overlap_cells"], get(native, ["ready_overlap_cells"], 0)) or 0
    )
    native_total = int(
        get(native, ["summary", "cells_checked"], get(native, ["cells_checked"], 4)) or 4
    )

    recency = data["recency_upstream"]
    source_max_date = (
        get(recency, ["local_source", "date_max"])
        or get(recency, ["source_panel_date_max"])
        or get(data["prior_completion_v17"], ["key_counts", "source_panel_date_max"])
        or "2026-01-30"
    )
    upstream_same = bool(
        get(recency, ["same_csv_size"], get(data["prior_completion_v17"], ["key_counts", "upstream_same_csv_size"], True))
    )

    source_missing = data["source_equivalence_missing_result"]
    missing_equivalence_files = source_missing.get("missing_files", [])
    external_screen = data["external_source_screen"]
    macro_schema = data["macro_stress_schema"]
    autoquant_source = data["autoquant_source_label"]
    source_equivalence_blocked = (
        source_missing.get("status") == "blocked"
        and bool(missing_equivalence_files)
        and external_screen.get("accepted_rows_added") == 0
        and macro_schema.get("accepted_rows_added") == 0
        and autoquant_source.get("new_confidence_gate") is False
    )

    direct_local = data["direct_local_intake"]
    direct_scan = data["direct_source_scan_v2"]
    hf_schema = data["hf_pumpdump_schema"]
    direct_full_species_complete = bool(consumer_rollup.get("direct_manipulation_full_species_complete"))
    direct_blocked = (
        not direct_full_species_complete
        and direct_local.get("accepted_rows_added", 0) == 0
        and direct_scan.get("accepted_rows_added", 0) == 0
        and hf_schema.get("accepted_rows_added", 0) == 0
    )

    checklist = [
        {
            "requirement": "every active regime has calibrated confidence >=95",
            "artifact": str(EVIDENCE["consumer_map"]),
            "evidence": (
                f"accepted_95_lanes={active_lanes}; min_price_root_floor={min_price_floor}; "
                f"scoped_direct_manipulation_floor={direct_floor}"
            ),
            "status": status_from_bool(scoped_95_ok, "pass_scoped", "fail"),
            "gap": "Scoped active lane passes, but consumer map itself marks full objective false.",
        },
        {
            "requirement": "validated on other markets with source-owned or owner-approved labels",
            "artifact": str(EVIDENCE["source_equivalence_missing_result"]),
            "evidence": (
                f"source_equivalence_missing_files={missing_equivalence_files}; "
                f"external_screen_decision={external_screen.get('decision')}; "
                f"autoquant_gate={autoquant_source.get('gate_result', autoquant_source.get('decision'))}"
            ),
            "status": "fail_blocked" if source_equivalence_blocked else "needs_manual_review",
            "gap": "No source-owned MainRegimeV2 equivalence rows/provenance for QQQ/NQ/crypto/FX/rates/commodities/native sub-hour/direct species.",
        },
        {
            "requirement": "validated on other cycles/timeframes beyond scoped daily/weekly/monthly support",
            "artifact": str(EVIDENCE["native_subhour"]),
            "evidence": f"native_subhour_ready_overlap={native_ready}/{native_total}; strict_1h={strict_accepted}/{strict_total}",
            "status": "fail_blocked" if native_ready == 0 else "partial",
            "gap": "Native sub-hour source-overlap cells are 0; strict exact 1h remains partial.",
        },
        {
            "requirement": "strict exact 1h ticker/root support complete enough for full objective",
            "artifact": str(EVIDENCE["strict_1h"]),
            "evidence": f"accepted={strict_accepted}; blocked={strict_blocked}; total={strict_total}",
            "status": "partial_blocked" if strict_accepted < strict_total else "pass",
            "gap": "Provider rows are ready, but source-label support/recency blocks 115 strict rows.",
        },
        {
            "requirement": "source panel recency after 2026-01-30",
            "artifact": str(EVIDENCE["recency_upstream"]),
            "evidence": (
                f"source_max_date={source_max_date}; upstream_same_csv_or_parquet_size={upstream_same}; "
                f"macro_post_tail_rows={get(macro_schema, ['schema', 'post_source_tail_rows_after_2026_01_30'], 0)} feature rows only"
            ),
            "status": "fail_blocked",
            "gap": "Post-tail feature rows are not source labels; upstream source package has no newer label revision.",
        },
        {
            "requirement": "direct Manipulation full species coverage with matched negatives",
            "artifact": str(EVIDENCE["direct_source_scan_v2"]),
            "evidence": (
                f"full_species_complete={direct_full_species_complete}; "
                f"direct_local_accepted={direct_local.get('accepted_rows_added', 0)}; "
                f"direct_scan_ready={direct_scan.get('ready_row_schema_candidates', direct_scan.get('ready_candidates', 0))}; "
                f"hf_schema_decision={hf_schema.get('decision')}"
            ),
            "status": "fail_blocked" if direct_blocked else "needs_manual_review",
            "gap": "Scoped direct overlay passes, but spoofing/layering/quote-stuffing/pinging/bear-raid/painting-tape/social-text variants remain missing or positive-only.",
        },
        {
            "requirement": "do not rely on proxy signals as completion",
            "artifact": str(EVIDENCE["external_source_screen"]),
            "evidence": (
                "external source candidates with labels/signals were screened but blocked without owner-approved MainRegimeV2 equivalence; "
                f"macro_label_like_fields={get(macro_schema, ['schema', 'label_like_fields'], [])}"
            ),
            "status": "pass_guardrail",
            "gap": "Proxy OHLCV/rule labels remain excluded.",
        },
        {
            "requirement": "update_goal only if full objective is achieved",
            "artifact": str(EVIDENCE["prior_completion_v17"]),
            "evidence": (
                f"prior_strict_full_objective={get(data['prior_completion_v17'], ['decision', 'strict_full_objective_achieved'])}; "
                "this_audit_full_objective=false"
            ),
            "status": "pass_guardrail",
            "gap": "Do not call update_goal.",
        },
    ]

    blocking = [
        row["requirement"]
        for row in checklist
        if row["status"] in {"fail_blocked", "partial_blocked", "needs_manual_review"}
    ]
    full_objective = not blocking

    result = {
        "artifact_type": "current_goal_completion_audit_v18_prompt_artifact",
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "board": str(BOARD),
        "board_sha256_at_run": board_hash,
        "objective": (
            "Every active regime has confidence >=95 and remains suitably confident "
            "when validated on other markets and other timeframes/cycles."
        ),
        "success_criteria": [
            "Bull/Bear/Sideways/Crisis/Manipulation all have calibrated confidence floors >=0.95.",
            "Each accepted regime has its own qualifying condition and validation evidence.",
            "Other-market validation uses source-owned labels or owner-approved equivalence, not provider/OHLCV proxy rows.",
            "Other-timeframe/cycle validation includes strict exact 1h and native sub-hour source-overlap coverage.",
            "Source labels are current enough beyond 2026-01-30 or explicitly extended with provenance.",
            "Direct Manipulation covers full species set with positive rows, matched negatives, and provenance.",
        ],
        "checklist": checklist,
        "evidence_paths": {name: str(path) for name, path in EVIDENCE.items()},
        "key_counts": {
            "accepted_95_lanes": active_lanes,
            "min_price_root_confidence_floor": min_price_floor,
            "scoped_direct_manipulation_confidence_floor": direct_floor,
            "strict_1h_accepted_rows": strict_accepted,
            "strict_1h_total_rows": strict_total,
            "strict_1h_blocked_rows": strict_blocked,
            "native_subhour_ready_overlap_cells": native_ready,
            "native_subhour_total_cells": native_total,
            "source_panel_date_max": source_max_date,
            "source_label_equivalence_missing_files": missing_equivalence_files,
            "external_source_candidate_records": external_screen.get("candidate_records"),
            "macro_post_tail_feature_rows_after_2026_01_30": get(
                macro_schema, ["schema", "post_source_tail_rows_after_2026_01_30"], 0
            ),
            "direct_manipulation_full_species_complete": direct_full_species_complete,
        },
        "decision": {
            "scoped_active_lane_status": "accepted_95" if scoped_95_ok else "not_accepted",
            "strict_full_objective_achieved": full_objective,
            "blocking_requirements": blocking,
            "gate_result": "current_goal_completion_audit_v18=scoped_95_present_prompt_artifact_audit_blocks_full_objective",
            "update_goal": False,
        },
        "guardrails": {
            "runtime_code_changed": False,
            "thresholds_relaxed": False,
            "raw_data_committed": False,
            "trade_usable": False,
            "proxy_signals_accepted_as_completion": False,
        },
        "next_action": (
            "Fill the source-label equivalence intake with source-owned rows/provenance, "
            "or obtain matched direct Manipulation species rows, then rerun unchanged gates."
        ),
    }

    json_path = OUT_DIR / "current_goal_completion_audit_v18_prompt_artifact.json"
    checklist_path = OUT_DIR / "current_goal_completion_audit_v18_prompt_artifact_checklist.csv"
    unmet_path = OUT_DIR / "current_goal_completion_audit_v18_unmet_requirements.csv"
    md_path = OUT_DIR / "current_goal_completion_audit_v18_prompt_artifact.md"
    assertions_path = CHECK_DIR / "current_goal_completion_audit_v18_prompt_artifact_assertions.out"

    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")

    with checklist_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["requirement", "artifact", "status", "evidence", "gap"])
        writer.writeheader()
        writer.writerows(checklist)

    with unmet_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["requirement", "artifact", "status", "gap"])
        writer.writeheader()
        for row in checklist:
            if row["status"] in {"fail_blocked", "partial_blocked", "needs_manual_review"}:
                writer.writerow(
                    {
                        "requirement": row["requirement"],
                        "artifact": row["artifact"],
                        "status": row["status"],
                        "gap": row["gap"],
                    }
                )

    lines = [
        "# Current Goal Completion Audit v18 Prompt-to-Artifact",
        "",
        f"Run ID: `{RUN_ID}`",
        "",
        "## Objective Restated",
        "",
        result["objective"],
        "",
        "## Decision",
        "",
        "- Scoped active-lane status: `accepted_95`.",
        "- Strict full objective achieved: `false`; `update_goal=false`.",
        "- Gate result: `current_goal_completion_audit_v18=scoped_95_present_prompt_artifact_audit_blocks_full_objective`.",
        "- Runtime code changed: false. Thresholds relaxed: false. Raw data committed: false. Trade usable: false.",
        "",
        "## Prompt-to-Artifact Checklist",
        "",
        "| Requirement | Status | Evidence | Gap |",
        "|---|---|---|---|",
    ]
    for row in checklist:
        evidence = row["evidence"].replace("|", "/")
        gap = row["gap"].replace("|", "/")
        lines.append(f"| {row['requirement']} | `{row['status']}` | {evidence} | {gap} |")
    lines.extend(
        [
            "",
            "## Blocking Requirements",
            "",
        ]
    )
    for item in blocking:
        lines.append(f"- {item}")
    lines.extend(
        [
            "",
            "## Next",
            "",
            result["next_action"],
        ]
    )
    md_path.write_text("\n".join(lines) + "\n")

    assertion_lines = [
        f"run_id={RUN_ID}",
        f"scoped_95_ok={str(scoped_95_ok).lower()}",
        f"strict_full_objective_achieved={str(full_objective).lower()}",
        "update_goal=false",
        f"blocking_requirement_count={len(blocking)}",
        f"strict_1h_accepted_rows={strict_accepted}",
        f"strict_1h_total_rows={strict_total}",
        f"native_subhour_ready_overlap_cells={native_ready}",
        f"source_label_equivalence_missing_files={len(missing_equivalence_files)}",
        f"direct_manipulation_full_species_complete={str(direct_full_species_complete).lower()}",
        "runtime_code_changed=false",
        "thresholds_relaxed=false",
        "raw_data_committed=false",
        "trade_usable=false",
    ]
    assertion_status = "PASS" if scoped_95_ok and not full_objective and len(blocking) >= 5 else "FAIL"
    assertion_lines.append(f"assertion_status={assertion_status}")
    assertions_path.write_text("\n".join(assertion_lines) + "\n")

    return 0 if assertion_status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
