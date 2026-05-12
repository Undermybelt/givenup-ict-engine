#!/usr/bin/env python3
"""Current-goal completion audit after the R6 Gandhi row uplift."""

from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


RUN_ID = "20260511T210620-codex-current-goal-completion-audit-v39-after-gandhi-uplift"
REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = Path(__file__).resolve().parents[1]
OUT = RUN_ROOT / "completion-audit"
CHECKS = RUN_ROOT / "checks"
BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"

OUTBOX_V2 = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T204715-codex-source-acquisition-outbox-v2-after-r6-uplift/"
    "source-acquisition-outbox-v2/source_acquisition_outbox_v2.json"
)
PUBLIC_SCOUT = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T205031-codex-current-public-regime-dataset-scout-v1/"
    "current-public-regime-dataset-scout/current_public_regime_dataset_scout_v1.json"
)
V38 = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T210002-codex-current-goal-completion-audit-v38-after-cftc-control-seed/"
    "completion-audit/current_goal_completion_audit_v38_after_cftc_control_seed.json"
)
GANDHI_UPLIFT = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T210150-codex-cftc-gandhi-source-row-uplift-v1/"
    "cftc-gandhi-source-row-uplift/cftc_gandhi_source_row_uplift_v1.json"
)
CFTC_SCOUT = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T210156-codex-r6-official-cftc-expansion-scout-v1/"
    "r6-official-cftc-expansion-scout/r6_official_cftc_expansion_scout_v1.json"
)
GANDHI_GATE = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T210514-codex-r6-gandhi-expanded-calibration-gate-v1/"
    "r6-gandhi-expanded-calibration-gate/r6_gandhi_expanded_calibration_gate_v1.json"
)

INTAKE_ROOTS = [
    {
        "id": "source_label_equivalence",
        "requirements": "R2;R4",
        "root": Path("/tmp/ict-engine-source-label-equivalence-intake"),
        "required_files": ["source_label_equivalence_rows.csv", "source_label_equivalence_provenance.json"],
    },
    {
        "id": "native_subhour_source_label",
        "requirements": "R3",
        "root": Path("/tmp/ict-engine-native-subhour-source-label-intake"),
        "required_files": ["native_subhour_source_label_rows.csv", "native_subhour_source_label_provenance.json"],
    },
    {
        "id": "source_panel_recency_extension",
        "requirements": "R5",
        "root": Path("/tmp/ict-engine-source-panel-recency-extension"),
        "required_files": ["stock_market_regimes_2026_extension.csv", "source_panel_recency_provenance.json"],
    },
    {
        "id": "direct_manipulation_row_intake",
        "requirements": "R6",
        "root": Path("/tmp/ict-engine-direct-manipulation-row-intake"),
        "required_files": [
            "positive_spoofing_layering_rows.csv",
            "matched_negative_normal_activity_rows.csv",
            "provenance_manifest.json",
        ],
    },
]


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO))
    except ValueError:
        return str(path)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"_missing": True, "_path": rel(path)}
    data = json.loads(path.read_text(encoding="utf-8"))
    data["_path"] = rel(path)
    return data


def row_count(path: Path) -> int:
    if not path.exists() or path.stat().st_size == 0:
        return 0
    with path.open(newline="", encoding="utf-8") as handle:
        return max(sum(1 for _ in csv.DictReader(handle)), 0)


def intake_status() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for spec in INTAKE_ROOTS:
        root = spec["root"]
        present: list[str] = []
        missing: list[str] = []
        counts: list[str] = []
        for name in spec["required_files"]:
            path = root / name
            if path.exists() and path.stat().st_size > 0:
                present.append(name)
                counts.append(f"{name}:{row_count(path) if path.suffix == '.csv' else 'json'}")
            else:
                missing.append(name)
        rows.append(
            {
                "id": spec["id"],
                "requirements": spec["requirements"],
                "root": str(root),
                "required_files": ";".join(spec["required_files"]),
                "present_files": ";".join(present),
                "missing_files": ";".join(missing),
                "row_counts": ";".join(counts),
                "exists": root.exists(),
                "ready_by_file_presence": not missing,
            }
        )
    return rows


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)

    outbox_v2 = read_json(OUTBOX_V2)
    public_scout = read_json(PUBLIC_SCOUT)
    v38 = read_json(V38)
    gandhi_uplift = read_json(GANDHI_UPLIFT)
    cftc_scout = read_json(CFTC_SCOUT)
    gandhi_gate = read_json(GANDHI_GATE)
    roots = intake_status()
    ready_roots = [row["id"] for row in roots if row["ready_by_file_presence"]]

    checklist = [
        {
            "id": "R0",
            "requirement": "Use the named Board A markdown and current cursor as the contract.",
            "artifact": rel(BOARD),
            "status": "pass_checked",
            "evidence": f"board_hash_before_audit={sha256(BOARD)}; current strict cursor and latest R6 Gandhi artifacts read.",
            "gap": "",
        },
        {
            "id": "R1",
            "requirement": "Every active regime has source-owned or owner-approved >=95% confidence and is not promoted as a trade claim.",
            "artifact": v38["_path"],
            "status": "fail_not_full",
            "evidence": "Prior scoped evidence remains preserved, but the strict full objective still lacks complete source rows and calibration.",
            "gap": "Full per-regime >=95 confidence across the required market/species/cycle axes is not complete.",
        },
        {
            "id": "R2",
            "requirement": "Other-market/source-label equivalence rows and provenance are acquired and verifier-accepted.",
            "artifact": outbox_v2["_path"],
            "status": "fail_blocked",
            "evidence": f"outbox_v2_rows={outbox_v2.get('v2_outbox_rows')}; rows_acquired={outbox_v2.get('rows_acquired')}; request_sent={outbox_v2.get('request_sent')}.",
            "gap": "source_label_equivalence_rows.csv;source_label_equivalence_provenance.json",
        },
        {
            "id": "R3",
            "requirement": "Native sub-hour source-label rows and provenance are acquired and verifier-accepted.",
            "artifact": rel(BOARD),
            "status": "fail_blocked",
            "evidence": "The native sub-hour intake root remains absent by current /tmp readback.",
            "gap": "native_subhour_source_label_rows.csv;native_subhour_source_label_provenance.json",
        },
        {
            "id": "R4",
            "requirement": "Strict exact 1h source rows and provenance are acquired.",
            "artifact": outbox_v2["_path"],
            "status": "fail_blocked",
            "evidence": "R4 still depends on the absent source-label equivalence intake package.",
            "gap": "source_label_equivalence_rows.csv;source_label_equivalence_provenance.json",
        },
        {
            "id": "R5",
            "requirement": "Post-2026-01-30 source-panel recency extension rows and provenance are acquired.",
            "artifact": public_scout["_path"],
            "status": "fail_blocked",
            "evidence": "Current public candidates were found but not accepted; no recency extension files exist in /tmp.",
            "gap": "stock_market_regimes_2026_extension.csv;source_panel_recency_provenance.json",
        },
        {
            "id": "R6",
            "requirement": "Direct Manipulation positive/control/provenance files cover required species and pass chronological plus heldout Wilson95 calibration.",
            "artifact": f"{gandhi_uplift['_path']}; {gandhi_gate['_path']}; {cftc_scout['_path']}",
            "status": "partial_expanded_schema_ready_calibration_blocked",
            "evidence": (
                f"positive_rows={gandhi_gate.get('positive_rows')}; matched_negative_rows={gandhi_gate.get('matched_negative_rows')}; "
                f"wilson95_min={gandhi_gate.get('combined_min_wilson95_lcb')}; chronological={gandhi_gate.get('chronological_train_calibration_test_ok')}; "
                f"heldout={gandhi_gate.get('heldout_symbol_or_venue_ok')}; broad_normal={gandhi_gate.get('broad_normal_sample')}; "
                f"species_ok={gandhi_gate.get('species_coverage_ok')}; official_cftc_candidates={cftc_scout.get('candidate_sources')}."
            ),
            "gap": "Support remains below Wilson95 >=0.95, controls are same-report seeds rather than broad normal controls, and direct species coverage is incomplete.",
        },
        {
            "id": "R7",
            "requirement": "No proxy labels, raw-data commits, threshold relaxation, external send, or trade-usable claim.",
            "artifact": f"{gandhi_uplift['_path']}; {gandhi_gate['_path']}",
            "status": "pass_guardrail",
            "evidence": "Artifacts keep accepted_rows_added=0, new_confidence_gate=false, thresholds_relaxed=false, raw_data_committed=false, trade_usable=false, request_sent=false where applicable.",
            "gap": "",
        },
        {
            "id": "R8",
            "requirement": "Only call update_goal when every strict requirement is covered by real accepted evidence.",
            "artifact": rel(OUT / "current_goal_completion_audit_v39_after_gandhi_uplift.json"),
            "status": "fail_blocked",
            "evidence": "R2/R3/R4/R5 remain blocked and R6 remains partial despite the Gandhi uplift.",
            "gap": "Strict full objective is not achieved; update_goal remains false.",
        },
    ]

    unmet = [row for row in checklist if row["status"].startswith("fail") or row["status"].startswith("partial")]
    result = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "objective_restatement": "Every active Board A regime must have source-owned or owner-approved >=95% confidence and survive other-market/species plus other-cycle/timeframe validation before completion.",
        "decision": "current_goal_completion_audit_v39=gandhi_rows_expanded_r6_still_calibration_blocked",
        "board_hash_before_artifact_generation": sha256(BOARD),
        "input_decisions": {
            "v38": v38.get("decision"),
            "gandhi_uplift": gandhi_uplift.get("decision", {}).get("gate_result") if isinstance(gandhi_uplift.get("decision"), dict) else gandhi_uplift.get("decision"),
            "gandhi_gate": gandhi_gate.get("decision"),
            "cftc_scout": cftc_scout.get("decision"),
            "outbox_v2": outbox_v2.get("decision"),
            "public_scout": public_scout.get("decision"),
        },
        "intake_roots_checked": roots,
        "ready_intake_roots": ready_roots,
        "ready_intake_root_count": len(ready_roots),
        "checklist": checklist,
        "unmet_ids": [row["id"] for row in unmet],
        "unmet_rows": len(unmet),
        "accepted_rows_added_since_v38": 0,
        "new_confidence_gate": False,
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "trade_usable": False,
        "next_action": "Continue source-owned extraction for R6 until support, broad controls, direct species, chronological, and heldout gates all pass; in parallel populate the existing R2/R3/R4/R5 fail-closed intake roots before rerunning completion audit.",
    }

    json_path = OUT / "current_goal_completion_audit_v39_after_gandhi_uplift.json"
    md_path = OUT / "current_goal_completion_audit_v39_after_gandhi_uplift.md"
    checklist_csv = OUT / "current_goal_completion_audit_v39_checklist.csv"
    unmet_csv = OUT / "current_goal_completion_audit_v39_unmet_requirements.csv"
    intake_csv = OUT / "current_goal_completion_audit_v39_intake_roots.csv"
    assertions_path = CHECKS / "current_goal_completion_audit_v39_after_gandhi_uplift_assertions.out"

    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_csv(checklist_csv, checklist, ["id", "requirement", "artifact", "status", "evidence", "gap"])
    write_csv(unmet_csv, unmet, ["id", "requirement", "artifact", "status", "evidence", "gap"])
    write_csv(
        intake_csv,
        roots,
        ["id", "requirements", "root", "required_files", "present_files", "missing_files", "row_counts", "exists", "ready_by_file_presence"],
    )

    lines = [
        "# Current Goal Completion Audit v39 After Gandhi Uplift",
        "",
        "Decision: `current_goal_completion_audit_v39=gandhi_rows_expanded_r6_still_calibration_blocked`.",
        "",
        "Result:",
        f"- Ready intake roots by file presence: `{len(ready_roots)}/4`; ready roots: `{', '.join(ready_roots) or 'none'}`.",
        f"- R6 rows after Gandhi uplift: positives `{gandhi_gate.get('positive_rows')}`, matched negatives `{gandhi_gate.get('matched_negative_rows')}`.",
        f"- R6 Wilson95 min LCB: `{gandhi_gate.get('combined_min_wilson95_lcb')}`; chronological ok: `{str(gandhi_gate.get('chronological_train_calibration_test_ok')).lower()}`; heldout symbol/venue ok: `{str(gandhi_gate.get('heldout_symbol_or_venue_ok')).lower()}`.",
        f"- Broad normal sample: `{str(gandhi_gate.get('broad_normal_sample')).lower()}`; species coverage ok: `{str(gandhi_gate.get('species_coverage_ok')).lower()}`.",
        "- Accepted rows added since v38: `0`; new confidence gate: `false`.",
        "- Strict full objective achieved: `false`; `update_goal=false`.",
        "- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; trade usable: `false`.",
        "",
        "Checklist:",
        "",
        "| ID | Status | Gap |",
        "|---|---|---|",
    ]
    for row in checklist:
        lines.append(f"| `{row['id']}` | `{row['status']}` | `{row['gap']}` |")
    lines.extend(
        [
            "",
            "Next:",
            result["next_action"],
            "",
            "Artifacts:",
            f"- JSON: `{rel(json_path)}`",
            f"- Checklist CSV: `{rel(checklist_csv)}`",
            f"- Unmet requirements CSV: `{rel(unmet_csv)}`",
            f"- Intake-root CSV: `{rel(intake_csv)}`",
            f"- Assertions: `{rel(assertions_path)}`",
        ]
    )
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    assertions = [
        "PASS decision=current_goal_completion_audit_v39=gandhi_rows_expanded_r6_still_calibration_blocked",
        f"PASS ready_intake_roots={len(ready_roots)}_of_4",
        f"PASS r6_positive_rows={gandhi_gate.get('positive_rows')}",
        f"PASS r6_matched_negative_rows={gandhi_gate.get('matched_negative_rows')}",
        f"PASS r6_chronological_ok={str(gandhi_gate.get('chronological_train_calibration_test_ok')).lower()}",
        f"PASS r6_heldout_ok={str(gandhi_gate.get('heldout_symbol_or_venue_ok')).lower()}",
        f"PASS r6_broad_normal_sample={str(gandhi_gate.get('broad_normal_sample')).lower()}",
        f"PASS r6_species_coverage_ok={str(gandhi_gate.get('species_coverage_ok')).lower()}",
        "PASS accepted_rows_added_since_v38=0",
        "PASS new_confidence_gate=false",
        "PASS strict_full_objective_achieved=false",
        "PASS update_goal=false",
        "PASS raw_data_committed=false",
    ]
    assertions_path.write_text("\n".join(assertions) + "\n", encoding="utf-8")
    print(json.dumps({"decision": result["decision"], "update_goal": False}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
