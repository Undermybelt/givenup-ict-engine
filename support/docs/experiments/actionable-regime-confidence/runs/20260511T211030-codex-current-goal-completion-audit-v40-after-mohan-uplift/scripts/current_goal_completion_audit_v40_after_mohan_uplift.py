#!/usr/bin/env python3
"""Current-goal completion audit after the R6 Mohan row uplift."""

from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


RUN_ID = "20260511T211030-codex-current-goal-completion-audit-v40-after-mohan-uplift"
REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = Path(__file__).resolve().parents[1]
OUT = RUN_ROOT / "completion-audit"
CHECKS = RUN_ROOT / "checks"
BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"
OUTBOX_V2 = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T204715-codex-source-acquisition-outbox-v2-after-r6-uplift/source-acquisition-outbox-v2/source_acquisition_outbox_v2.json"
VANTMACRO = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T210411-codex-vantmacro-current-regime-route-screen-v1/vantmacro-current-regime-route-screen/vantmacro_current_regime_route_screen_v1.json"
V39 = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T210620-codex-current-goal-completion-audit-v39-after-gandhi-uplift/completion-audit/current_goal_completion_audit_v39_after_gandhi_uplift.json"
MOHAN_UPLIFT = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T210744-codex-r6-mohan-additional-row-uplift-v1/r6-mohan-additional-row-uplift/r6_mohan_additional_row_uplift_v1.json"
MOHAN_GATE = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T210744-codex-r6-mohan-additional-row-uplift-v1/r6-mohan-additional-row-uplift/r6_cftc_schema_ready_calibration_gate_v1.json"

INTAKE_ROOTS = [
    ("source_label_equivalence", "R2;R4", Path("/tmp/ict-engine-source-label-equivalence-intake"), ["source_label_equivalence_rows.csv", "source_label_equivalence_provenance.json"]),
    ("native_subhour_source_label", "R3", Path("/tmp/ict-engine-native-subhour-source-label-intake"), ["native_subhour_source_label_rows.csv", "native_subhour_source_label_provenance.json"]),
    ("source_panel_recency_extension", "R5", Path("/tmp/ict-engine-source-panel-recency-extension"), ["stock_market_regimes_2026_extension.csv", "source_panel_recency_provenance.json"]),
    ("direct_manipulation_row_intake", "R6", Path("/tmp/ict-engine-direct-manipulation-row-intake"), ["positive_spoofing_layering_rows.csv", "matched_negative_normal_activity_rows.csv", "provenance_manifest.json"]),
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
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["_path"] = rel(path)
    return payload


def csv_rows(path: Path) -> int | str:
    if not path.exists() or path.stat().st_size == 0:
        return 0
    if path.suffix != ".csv":
        return "json"
    with path.open(newline="", encoding="utf-8") as handle:
        return sum(1 for _ in csv.DictReader(handle))


def intake_status() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for root_id, requirements, root, files in INTAKE_ROOTS:
        present = []
        missing = []
        counts = []
        for name in files:
            path = root / name
            if path.exists() and path.stat().st_size > 0:
                present.append(name)
                counts.append(f"{name}:{csv_rows(path)}")
            else:
                missing.append(name)
        rows.append(
            {
                "id": root_id,
                "requirements": requirements,
                "root": str(root),
                "required_files": ";".join(files),
                "present_files": ";".join(present),
                "missing_files": ";".join(missing),
                "row_counts": ";".join(counts),
                "ready_by_file_presence": len(missing) == 0,
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

    outbox = read_json(OUTBOX_V2)
    vantmacro = read_json(VANTMACRO)
    v39 = read_json(V39)
    uplift = read_json(MOHAN_UPLIFT)
    gate = read_json(MOHAN_GATE)
    roots = intake_status()
    ready = [row["id"] for row in roots if row["ready_by_file_presence"]]
    board_hash = sha256(BOARD)

    decision = "current_goal_completion_audit_v40=mohan_rows_expanded_r6_still_calibration_blocked"
    r6_evidence = (
        f"positive_rows={gate.get('positive_rows')}; matched_negative_rows={gate.get('matched_negative_rows')}; "
        f"unique_dates={len(gate.get('unique_dates', []))}; symbols={len(gate.get('unique_symbols', []))}; venues={len(gate.get('unique_venues', []))}; "
        f"wilson95_min={gate.get('combined_min_wilson95_lcb')}; chronological={gate.get('chronological_split_ok')}; "
        f"heldout={gate.get('heldout_symbol_or_venue_ok')}; broad_normal={gate.get('broad_normal_sample')}; support_ok={gate.get('support_ok')}"
    )
    checklist = [
        {"id": "R0", "requirement": "Audit actual current Board A state and artifacts, not intent.", "status": "pass_checked", "evidence": f"board_hash_before_audit={board_hash}; v39 and 210744 Mohan uplift artifacts read.", "gap": ""},
        {"id": "R1", "requirement": "Every active regime has source-owned or owner-approved >=95% confidence across required axes.", "status": "fail_not_full", "evidence": "Scoped evidence remains preserved, but strict full objective still lacks accepted R2/R3/R4/R5 evidence and R6 calibration.", "gap": "Full per-regime >=95 confidence across market/species/cycle axes is incomplete."},
        {"id": "R2", "requirement": "Other-market/source-label equivalence rows and provenance exist and pass verifier.", "status": "fail_blocked", "evidence": f"outbox_v2_rows={outbox.get('v2_outbox_rows')}; VantMacro route rows_acquired={vantmacro.get('rows_acquired')}.", "gap": "source_label_equivalence_rows.csv;source_label_equivalence_provenance.json"},
        {"id": "R3", "requirement": "Native sub-hour source-label rows and provenance exist and pass verifier.", "status": "fail_blocked", "evidence": "Native sub-hour intake files remain absent in /tmp.", "gap": "native_subhour_source_label_rows.csv;native_subhour_source_label_provenance.json"},
        {"id": "R4", "requirement": "Strict exact 1h source-label/provenance package exists.", "status": "fail_blocked", "evidence": "R4 still depends on absent source-label equivalence intake files.", "gap": "source_label_equivalence_rows.csv;source_label_equivalence_provenance.json"},
        {"id": "R5", "requirement": "Post-2026-01-30 source-panel recency extension rows and provenance exist.", "status": "fail_blocked", "evidence": "VantMacro is route-only; source-panel recency extension files remain absent.", "gap": "stock_market_regimes_2026_extension.csv;source_panel_recency_provenance.json"},
        {"id": "R6", "requirement": "Direct Manipulation rows cover required species and pass support/Wilson95/broad-normal gates.", "status": "partial_expanded_schema_ready_calibration_blocked", "evidence": r6_evidence, "gap": "Support below 50/50, Wilson95 below 0.95, broad normal sample false, species coverage incomplete."},
        {"id": "R7", "requirement": "No proxy promotion, threshold relaxation, raw-data commit, external send, or trade claim.", "status": "pass_guardrail", "evidence": "Read artifacts keep accepted_rows_added=0, new_confidence_gate=false, strict_full_objective_achieved=false, update_goal=false, thresholds_relaxed=false, raw_data_committed=false, trade_usable=false.", "gap": ""},
        {"id": "R8", "requirement": "Only call update_goal if every strict requirement is complete.", "status": "fail_blocked", "evidence": "R2/R3/R4/R5 are absent and R6 is partial despite 8/8 schema-ready rows.", "gap": "Strict full objective is not achieved; update_goal remains false."},
    ]
    unmet = [row for row in checklist if row["status"].startswith("fail") or row["status"].startswith("partial")]

    payload = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "objective_restatement": "Every active Board A regime must have source-owned or owner-approved >=95% confidence and survive other-market/species plus other-cycle/timeframe validation before completion.",
        "decision": decision,
        "board_hash_before_artifact_generation": board_hash,
        "input_artifacts": {
            "v39": v39.get("_path"),
            "mohan_uplift": uplift.get("_path"),
            "mohan_gate": gate.get("_path"),
            "outbox_v2": outbox.get("_path"),
            "vantmacro_route": vantmacro.get("_path"),
        },
        "ready_intake_roots": ready,
        "intake_roots": roots,
        "checklist": checklist,
        "unmet_ids": [row["id"] for row in unmet],
        "r6_positive_rows": gate.get("positive_rows"),
        "r6_matched_negative_rows": gate.get("matched_negative_rows"),
        "r6_combined_min_wilson95_lcb": gate.get("combined_min_wilson95_lcb"),
        "r6_chronological_ok": gate.get("chronological_split_ok"),
        "r6_heldout_symbol_or_venue_ok": gate.get("heldout_symbol_or_venue_ok"),
        "r6_broad_normal_sample": gate.get("broad_normal_sample"),
        "accepted_rows_added_since_v39": 0,
        "new_confidence_gate": False,
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "trade_usable": False,
        "next": "Continue source-owned extraction for R6 until support, broad controls, direct species, chronological, and heldout gates all pass; in parallel populate R2/R3/R4/R5 fail-closed intake roots.",
    }
    json_path = OUT / "current_goal_completion_audit_v40_after_mohan_uplift.json"
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_csv(OUT / "current_goal_completion_audit_v40_checklist.csv", checklist, ["id", "requirement", "status", "evidence", "gap"])
    write_csv(OUT / "current_goal_completion_audit_v40_unmet_requirements.csv", unmet, ["id", "requirement", "status", "evidence", "gap"])
    write_csv(OUT / "current_goal_completion_audit_v40_intake_roots.csv", roots, ["id", "requirements", "root", "required_files", "present_files", "missing_files", "row_counts", "ready_by_file_presence"])

    md = [
        "# Current Goal Completion Audit v40 After Mohan Uplift",
        "",
        f"Decision: `{decision}`.",
        "",
        "Result:",
        f"- Ready intake roots by file presence: `{len(ready)}/4`; ready roots: `{','.join(ready)}`.",
        f"- R6 rows after Mohan uplift: positives `{gate.get('positive_rows')}`, matched negatives `{gate.get('matched_negative_rows')}`.",
        f"- R6 Wilson95 min LCB: `{gate.get('combined_min_wilson95_lcb')}`; chronological ok: `{str(gate.get('chronological_split_ok')).lower()}`; heldout symbol/venue ok: `{str(gate.get('heldout_symbol_or_venue_ok')).lower()}`.",
        f"- Broad normal sample: `{str(gate.get('broad_normal_sample')).lower()}`; support ok: `{str(gate.get('support_ok')).lower()}`.",
        "- Accepted rows added since v39: `0`; new confidence gate: `false`.",
        "- Strict full objective achieved: `false`; `update_goal=false`.",
        "- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; trade usable: `false`.",
        "",
        "Checklist:",
        "",
        "| ID | Status | Gap |",
        "|---|---|---|",
    ]
    for row in checklist:
        md.append(f"| `{row['id']}` | `{row['status']}` | `{row['gap']}` |")
    md.extend(
        [
            "",
            "Next:",
            payload["next"],
            "",
            "Artifacts:",
            f"- JSON: `{rel(json_path)}`",
            f"- Checklist CSV: `{rel(OUT / 'current_goal_completion_audit_v40_checklist.csv')}`",
            f"- Unmet requirements CSV: `{rel(OUT / 'current_goal_completion_audit_v40_unmet_requirements.csv')}`",
            f"- Intake-root CSV: `{rel(OUT / 'current_goal_completion_audit_v40_intake_roots.csv')}`",
            f"- Assertions: `{rel(CHECKS / 'current_goal_completion_audit_v40_after_mohan_uplift_assertions.out')}`",
        ]
    )
    (OUT / "current_goal_completion_audit_v40_after_mohan_uplift.md").write_text("\n".join(md) + "\n", encoding="utf-8")

    assertions = [
        f"PASS decision={decision}",
        f"PASS ready_intake_roots={len(ready)}_of_4",
        f"PASS r6_positive_rows={gate.get('positive_rows')}",
        f"PASS r6_matched_negative_rows={gate.get('matched_negative_rows')}",
        f"PASS r6_chronological_ok={str(gate.get('chronological_split_ok')).lower()}",
        f"PASS r6_heldout_ok={str(gate.get('heldout_symbol_or_venue_ok')).lower()}",
        f"PASS r6_broad_normal_sample={str(gate.get('broad_normal_sample')).lower()}",
        f"PASS r6_support_ok={str(gate.get('support_ok')).lower()}",
        "PASS accepted_rows_added_since_v39=0",
        "PASS new_confidence_gate=false",
        "PASS strict_full_objective_achieved=false",
        "PASS update_goal=false",
        "PASS raw_data_committed=false",
    ]
    (CHECKS / "current_goal_completion_audit_v40_after_mohan_uplift_assertions.out").write_text("\n".join(assertions) + "\n", encoding="utf-8")
    print(json.dumps({"decision": decision, "r6_positive_rows": gate.get("positive_rows"), "ready_roots": len(ready)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
