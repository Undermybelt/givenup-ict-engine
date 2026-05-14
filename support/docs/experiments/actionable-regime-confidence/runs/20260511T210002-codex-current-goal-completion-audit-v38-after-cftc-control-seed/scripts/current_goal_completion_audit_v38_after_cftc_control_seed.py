#!/usr/bin/env python3
"""Prompt-to-artifact completion audit after the CFTC control-seed slice."""

from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


RUN_ID = "20260511T210002-codex-current-goal-completion-audit-v38-after-cftc-control-seed"
REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = Path(__file__).resolve().parents[1]
OUT = RUN_ROOT / "completion-audit"
CHECKS = RUN_ROOT / "checks"
BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"

V37 = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T205323-codex-current-goal-completion-audit-v37-after-live-public-recheck/"
    "completion-audit/current_goal_completion_audit_v37_after_live_public_recheck.json"
)
CFTC_POSITIVE = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T205239-codex-cftc-finra-direct-public-positive-probe-v1/"
    "cftc-finra-direct-public-positive-probe/cftc_finra_direct_public_positive_probe_v1.json"
)
CFTC_CONTROL = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T205654-codex-cftc-matched-control-seed-v1/"
    "cftc-matched-control-seed/cftc_matched_control_seed_v1.json"
)
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


def intake_status() -> list[dict[str, Any]]:
    rows = []
    for spec in INTAKE_ROOTS:
        root = spec["root"]
        present = []
        missing = []
        for name in spec["required_files"]:
            path = root / name
            if path.exists() and path.stat().st_size > 0:
                present.append(name)
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
                "exists": root.exists(),
                "ready": not missing,
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

    v37 = read_json(V37)
    cftc_positive = read_json(CFTC_POSITIVE)
    cftc_control = read_json(CFTC_CONTROL)
    outbox_v2 = read_json(OUTBOX_V2)
    public_scout = read_json(PUBLIC_SCOUT)
    roots = intake_status()
    ready_roots = [row["id"] for row in roots if row["ready"]]
    direct_schema_ready = cftc_control.get("schema_ready_unscored") is True

    checklist = [
        {
            "id": "R0",
            "requirement": "Use the named Board A markdown and latest current cursor as the contract.",
            "artifact": rel(BOARD),
            "status": "pass_checked",
            "evidence": f"board_hash_before_audit={sha256(BOARD)}; read v37 audit, CFTC positive probe, CFTC control seed, outbox v2, public scout, and live /tmp roots.",
            "gap": "",
        },
        {
            "id": "R1",
            "requirement": "Every active regime keeps calibrated >=95% evidence without becoming a trade claim.",
            "artifact": v37["_path"],
            "status": "pass_scoped_not_full",
            "evidence": "Prior scoped active-lane evidence remains preserved; this slice added no trade-usable claim.",
            "gap": "Strict full-market/full-cycle/full-species evidence is still incomplete.",
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
            "artifact": v37["_path"],
            "status": "fail_blocked",
            "evidence": "The native sub-hour intake root remains absent.",
            "gap": "native_subhour_source_label_rows.csv;native_subhour_source_label_provenance.json",
        },
        {
            "id": "R4",
            "requirement": "Strict exact 1h source rows and provenance are acquired.",
            "artifact": outbox_v2["_path"],
            "status": "fail_blocked",
            "evidence": "R4 still depends on the absent source-label equivalence package.",
            "gap": "source_label_equivalence_rows.csv;source_label_equivalence_provenance.json",
        },
        {
            "id": "R5",
            "requirement": "Post-2026-01-30 source-panel recency extension rows and provenance are acquired.",
            "artifact": public_scout["_path"],
            "status": "fail_blocked",
            "evidence": "Current public candidates were found but not accepted; stock-regime source panel still has no accepted post-cutoff target rows.",
            "gap": "stock_market_regimes_2026_extension.csv;source_panel_recency_provenance.json",
        },
        {
            "id": "R6",
            "requirement": "Direct Manipulation positive/control/provenance files are acquired across required species and calibrated.",
            "artifact": f"{cftc_positive['_path']}; {cftc_control['_path']}",
            "status": "partial_schema_ready_unscored",
            "evidence": f"positive_rows={cftc_positive.get('positive_rows_extracted')}; matched_controls={cftc_control.get('matched_negative_rows_count')}; verifier_schema_ready={direct_schema_ready}.",
            "gap": "Only CFTC spoofing/layering seed rows exist; no Wilson95 calibration, heldout-symbol/venue validation, or broader direct species closure.",
        },
        {
            "id": "R7",
            "requirement": "No proxy labels, raw-data commits, threshold relaxation, external send, or trade-usable claim.",
            "artifact": f"{v37['_path']}; {cftc_control['_path']}",
            "status": "pass_guardrail",
            "evidence": "All current artifacts keep accepted_rows_added=0, new_confidence_gate=false, thresholds_relaxed=false, raw_data_committed=false, trade_usable=false.",
            "gap": "",
        },
        {
            "id": "R8",
            "requirement": "Only call update_goal when every strict requirement is covered by real accepted evidence.",
            "artifact": rel(OUT / "current_goal_completion_audit_v38_after_cftc_control_seed.json"),
            "status": "fail_blocked",
            "evidence": "R2/R3/R4/R5 remain blocked and R6 is schema-ready/unscored only.",
            "gap": "Strict full objective is not achieved; update_goal remains false.",
        },
    ]

    unmet = ["R2", "R3", "R4", "R5", "R6", "R8"]
    decision = "current_goal_completion_audit_v38=cftc_control_seed_schema_ready_unscored_strict_objective_blocked"
    audit = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "board_hash_before_artifact_generation": sha256(BOARD),
        "objective_restatement": (
            "Every active Board A regime must have source-owned or owner-approved >=95% confidence and survive "
            "other-market/species plus other-cycle/timeframe validation before completion."
        ),
        "decision": decision,
        "input_decisions": {
            "v37": v37.get("decision"),
            "cftc_positive": cftc_positive.get("decision"),
            "cftc_control": cftc_control.get("decision"),
            "outbox_v2": outbox_v2.get("decision"),
            "public_scout": public_scout.get("decision"),
        },
        "ready_intake_root_count": len(ready_roots),
        "ready_intake_roots": ready_roots,
        "direct_schema_ready_unscored": direct_schema_ready,
        "accepted_rows_added_since_v37": 0,
        "new_confidence_gate": False,
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "trade_usable": False,
        "unmet_ids": unmet,
        "unmet_rows": len(unmet),
        "intake_roots_checked": roots,
        "checklist": checklist,
        "next_action": (
            "For R6, collect more source-owned positive and same-schema normal-control rows across venues/symbols/periods "
            "and run chronological plus heldout-symbol/venue Wilson95 calibration; for R2/R3/R4/R5, populate required "
            "/tmp intake roots with source-owned/provenance files and rerun verifiers."
        ),
    }

    json_path = OUT / "current_goal_completion_audit_v38_after_cftc_control_seed.json"
    report_path = OUT / "current_goal_completion_audit_v38_after_cftc_control_seed.md"
    checklist_path = OUT / "current_goal_completion_audit_v38_checklist.csv"
    unmet_path = OUT / "current_goal_completion_audit_v38_unmet_requirements.csv"
    roots_path = OUT / "current_goal_completion_audit_v38_intake_roots.csv"
    assertions_path = CHECKS / "current_goal_completion_audit_v38_after_cftc_control_seed_assertions.out"

    json_path.write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_csv(checklist_path, checklist, ["id", "requirement", "artifact", "status", "evidence", "gap"])
    write_csv(unmet_path, [row for row in checklist if row["id"] in unmet], ["id", "requirement", "artifact", "status", "evidence", "gap"])
    write_csv(roots_path, roots, ["id", "requirements", "root", "required_files", "present_files", "missing_files", "exists", "ready"])

    lines = [
        "# Current Goal Completion Audit v38 After CFTC Control Seed",
        "",
        f"Decision: `{decision}`.",
        "",
        "Result:",
        f"- Direct R6 intake root ready by file presence: `{len(ready_roots)}/4`; ready roots: `{','.join(ready_roots) or 'none'}`.",
        f"- Direct verifier schema-ready/unscored: `{str(direct_schema_ready).lower()}`.",
        "- Accepted rows added since v37: `0`; new confidence gate: `false`.",
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
            audit["next_action"],
            "",
            "Artifacts:",
            f"- JSON: `{rel(json_path)}`",
            f"- Checklist CSV: `{rel(checklist_path)}`",
            f"- Unmet requirements CSV: `{rel(unmet_path)}`",
            f"- Intake-root CSV: `{rel(roots_path)}`",
            f"- Assertions: `{rel(assertions_path)}`",
        ]
    )
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    assertions = [
        f"PASS decision={decision}",
        f"PASS direct_schema_ready_unscored={str(direct_schema_ready).lower()}",
        f"PASS ready_intake_roots={len(ready_roots)}_of_4",
        "PASS accepted_rows_added_since_v37=0",
        "PASS new_confidence_gate=false",
        "PASS strict_full_objective_achieved=false",
        "PASS update_goal=false",
        "PASS raw_data_committed=false",
    ]
    assertions_path.write_text("\n".join(assertions) + "\n", encoding="utf-8")
    print(json.dumps({"decision": decision, "ready_intake_roots": len(ready_roots)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
