#!/usr/bin/env python3
"""Prompt-to-artifact audit for Board A after TSIE target-root quarantine."""

from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = Path(__file__).resolve().parents[1]
RUN_ID = "20260512T064230+0800-codex-current-objective-prompt-artifact-audit-after-063926-v1"
SLUG = "current-objective-prompt-artifact-audit-after-063926-v1"
OUT = RUN_ROOT / SLUG
CHECKS = RUN_ROOT / "checks"
BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"

R6_ROOT = Path("/tmp/ict-engine-board-a-r6-owner-export-v1")
R3_ROOT = Path("/tmp/ict-engine-native-subhour-source-label-intake")
R5_ROOT = Path("/tmp/ict-engine-source-panel-recency-extension")
SOURCE_EQ_ROOT = Path("/tmp/ict-engine-source-label-equivalence-intake")

R3_PROVENANCE = R3_ROOT / "native_subhour_source_label_provenance.json"
R3_ROWS = R3_ROOT / "native_subhour_source_label_rows.csv"
SOURCE_CONTROL_064220_ASSERTIONS = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs/20260512T064220+0800-codex-source-control-arrival-refresh-after-063906-v1/checks/source_control_arrival_refresh_after_063906_v1_assertions.out"
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def file_info(path: Path, *, hash_file: bool = False) -> dict[str, Any]:
    if not path.exists():
        return {"path": str(path), "present": False}
    info: dict[str, Any] = {
        "path": str(path),
        "present": True,
        "size_bytes": path.stat().st_size,
    }
    if hash_file:
        info["sha256"] = sha256_file(path)
    return info


def root_info(root: Path, required: list[str], *, quarantined: bool = False) -> dict[str, Any]:
    files = {p.name: p for p in root.iterdir()} if root.exists() else {}
    missing = [name for name in required if name not in files]
    return {
        "root": str(root),
        "present": root.exists(),
        "required_files": required,
        "missing_required_files": missing,
        "all_required_present": root.exists() and not missing,
        "quarantined": quarantined,
        "accepted_unlock": root.exists() and not missing and not quarantined,
        "present_files": sorted(files),
    }


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)

    board_text = BOARD.read_text(encoding="utf-8")
    board_hash = sha256_text(board_text)
    r3_provenance = read_json(R3_PROVENANCE)
    r3_labels = sorted(r3_provenance.get("accepted_mapping_confidence_95_labels", []))
    r3_row_count = r3_provenance.get("row_count")
    r3_policy_blockers = [
        "tsie_rule_or_ohlcv_generated_labels",
        "crisis_absent_from_tsie_taxonomy",
        "r3_root_policy_quarantined",
        "no_accepted_mainregimev2_equivalence_under_current_policy",
        "canonical_merge_not_run",
        "downstream_promotion_not_rerun",
    ]

    roots = {
        "r6_owner_export": root_info(
            R6_ROOT,
            [
                "positive_spoofing_layering_rows.csv",
                "matched_negative_normal_activity_rows.csv",
                "provenance_manifest.json",
            ],
        ),
        "r3_native_subhour": root_info(
            R3_ROOT,
            [
                "native_subhour_source_label_rows.csv",
                "native_subhour_source_label_provenance.json",
            ],
            quarantined=True,
        ),
        "r5_recency_extension": root_info(
            R5_ROOT,
            [
                "stock_market_regimes_2026_extension.csv",
                "source_panel_recency_provenance.json",
            ],
        ),
        "source_label_equivalence_non_target": root_info(
            SOURCE_EQ_ROOT,
            [
                "source_label_equivalence_rows.csv",
                "source_label_equivalence_provenance.json",
            ],
            quarantined=True,
        ),
    }

    checklist = [
        {
            "requirement": "Every active MainRegimeV2 regime reaches >=95% accepted confidence",
            "evidence": "latest board 063906 plus R3 provenance",
            "status": "blocked",
            "details": f"R3 physical labels={','.join(r3_labels) or 'none'}; Crisis absent; Board A accepted TSIE rows=0",
        },
        {
            "requirement": "Cross-market/cycle/timeframe validation is accepted for each regime",
            "evidence": "063217 public sweep and 063906 current audit",
            "status": "blocked",
            "details": "No accepted R3/R5/R6 source/control unlock; public candidates accepted=0",
        },
        {
            "requirement": "R6 owner/export controls available",
            "evidence": str(R6_ROOT),
            "status": "blocked",
            "details": "R6 owner/export root absent",
        },
        {
            "requirement": "R5 post-cutoff source-panel recency rows available",
            "evidence": str(R5_ROOT),
            "status": "blocked",
            "details": "R5 recency root absent",
        },
        {
            "requirement": "R3 native-subhour labels accepted under current policy",
            "evidence": str(R3_ROOT),
            "status": "blocked",
            "details": "Root present but TSIE-quarantined/proxy; not an accepted unlock",
        },
        {
            "requirement": "Provider/AutoQuant/filter/Pre-Bayes/BBN/CatBoost/path-ranking/execution-tree promotion rerun",
            "evidence": "062854 read-only runtime correction",
            "status": "blocked",
            "details": "Read-only runtime evidence only; canonical merge false; downstream promotion false",
        },
        {
            "requirement": "Latest source/control arrival refresh after 063906 changes the unlock state",
            "evidence": str(SOURCE_CONTROL_064220_ASSERTIONS),
            "status": "blocked",
            "details": "064220 reports no valid required unlock and no downstream rerun",
        },
        {
            "requirement": "Do not accept proxy signals as completion",
            "evidence": "063734/063906 quarantine and fail-close readbacks",
            "status": "pass",
            "details": "TSIE physical rows are explicitly quarantined and count as 0 accepted rows",
        },
        {
            "requirement": "Board A markdown remains the authoritative ledger",
            "evidence": str(BOARD),
            "status": "pass",
            "details": "Latest relevant roots are registered through 063906/063217/063734 in board tail",
        },
    ]

    blocked = [row for row in checklist if row["status"] != "pass"]
    result = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "board_sha256_before_artifact": board_hash,
        "gate_result": "current_objective_prompt_artifact_audit_after_063926_v1=not_complete_required_unlocks_absent_or_quarantined_no_downstream",
        "objective_complete": False,
        "checklist": checklist,
        "roots": roots,
        "r3_target_root": {
            "rows_file": file_info(R3_ROWS),
            "provenance_file": file_info(R3_PROVENANCE, hash_file=True),
            "provenance_run_id": r3_provenance.get("run_id"),
            "physical_row_count": r3_row_count,
            "physical_labels": r3_labels,
            "policy_blockers": r3_policy_blockers,
            "accepted_rows_added_for_board_a": 0,
        },
        "promotion": {
            "source_control_evidence_acquired": False,
            "valid_required_root_unlock": False,
            "canonical_merge": False,
            "downstream_promotion_rerun": False,
            "strict_full_objective": False,
            "trade_usable": False,
            "update_goal": False,
        },
        "blocked_requirements": [row["requirement"] for row in blocked],
        "next": (
            "Continue only from explicit source/control approval, verifier-native R6 owner-export rows with controls, "
            "source-owned R5 recency rows, verifier-native R3 MainRegimeV2 labels, or a genuinely new accepted "
            "cross-timeframe MainRegimeV2 source export before canonical merge and downstream chain."
        ),
    }

    json_path = OUT / "current_objective_prompt_artifact_audit_after_063926_v1.json"
    checklist_path = OUT / "prompt_to_artifact_checklist_after_063926_v1.csv"
    roots_path = OUT / "required_root_status_after_063926_v1.csv"
    report_path = OUT / "current_objective_prompt_artifact_audit_after_063926_v1.md"
    assertions_path = CHECKS / "current_objective_prompt_artifact_audit_after_063926_v1_assertions.out"

    write_json(json_path, result)
    write_csv(checklist_path, checklist, ["requirement", "evidence", "status", "details"])
    write_csv(
        roots_path,
        [
            {
                "root_id": key,
                "root": value["root"],
                "present": value["present"],
                "all_required_present": value["all_required_present"],
                "quarantined": value["quarantined"],
                "accepted_unlock": value["accepted_unlock"],
                "missing_required_files": ";".join(value["missing_required_files"]),
            }
            for key, value in roots.items()
        ],
        [
            "root_id",
            "root",
            "present",
            "all_required_present",
            "quarantined",
            "accepted_unlock",
            "missing_required_files",
        ],
    )

    report_lines = [
        "# Current Objective Prompt Artifact Audit After 063926 v1",
        "",
        f"Run id: `{RUN_ID}`",
        "",
        f"Gate result: `{result['gate_result']}`",
        "",
        "## Objective Restatement",
        "",
        "Board A is complete only if every active regime has accepted >=95% confidence, cross-market/cycle/timeframe validation is accepted, real source/control roots unlock, canonical merge is allowed, and provider/AutoQuant -> filter/Pre-Bayes -> BBN -> CatBoost/path-ranking -> execution-tree promotion is rerun without treating proxy rows as completion.",
        "",
        "## Checklist Result",
        "",
    ]
    for row in checklist:
        report_lines.append(f"- `{row['status']}`: {row['requirement']} -- {row['details']}")
    report_lines.extend(
        [
            "",
            "## Decision",
            "",
            "- Objective complete: `false`.",
            f"- R3 root present: `{roots['r3_native_subhour']['present']}`; accepted unlock: `false`.",
            f"- R3 physical row count: `{r3_row_count}`; labels: `{','.join(r3_labels)}`.",
            "- R6 owner/export root accepted: `false`.",
            "- R5 recency root accepted: `false`.",
            "- Canonical merge: `false`.",
            "- Downstream promotion rerun: `false`.",
            "- Trade usable: `false`.",
            "- `update_goal=false`.",
            "",
            "## Next",
            "",
            result["next"],
            "",
            "## Artifacts",
            "",
            f"- JSON: `{json_path.relative_to(REPO)}`",
            f"- Checklist CSV: `{checklist_path.relative_to(REPO)}`",
            f"- Required roots CSV: `{roots_path.relative_to(REPO)}`",
            f"- Assertions: `{assertions_path.relative_to(REPO)}`",
        ]
    )
    report_path.write_text("\n".join(report_lines) + "\n", encoding="utf-8")

    assertions = [
        f"gate_result={result['gate_result']}",
        "objective_complete=false",
        f"r6_owner_export_unlock={str(roots['r6_owner_export']['accepted_unlock']).lower()}",
        f"r3_native_subhour_unlock={str(roots['r3_native_subhour']['accepted_unlock']).lower()}",
        f"r5_recency_unlock={str(roots['r5_recency_extension']['accepted_unlock']).lower()}",
        f"r3_physical_rows={r3_row_count}",
        "r3_board_accepted_rows=0",
        "canonical_merge=false",
        "downstream_promotion_rerun=false",
        "strict_full_objective=false",
        "trade_usable=false",
        "update_goal=false",
    ]
    assertions_path.write_text("\n".join(assertions) + "\n", encoding="utf-8")
    print(json.dumps({"ok": True, "gate_result": result["gate_result"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
