#!/usr/bin/env python3
import csv
import hashlib
import json
from pathlib import Path


REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = Path(__file__).resolve().parents[1]
OUT = RUN_ROOT / "current-objective-audit-after-062409-v1"
CHECKS = RUN_ROOT / "checks"

BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"
REQUIRED_ROOTS = [
    Path("/tmp/ict-engine-board-a-r6-owner-export-v1"),
    Path("/tmp/ict-engine-native-subhour-source-label-intake"),
    Path("/tmp/ict-engine-source-panel-recency-extension"),
]
SOURCE_EQUIV = Path("/tmp/ict-engine-source-label-equivalence-intake")

ASSERTION_FILES = {
    "061421_source_confidence": REPO
    / "docs/experiments/actionable-regime-confidence/runs/20260512T061421+0800-codex-source-label-equivalence-current-calibration-after-061229-v1/checks/source_label_equivalence_confidence_calibration_v1_assertions.out",
    "061521_current_audit": REPO
    / "docs/experiments/actionable-regime-confidence/runs/20260512T061521+0800-codex-current-objective-audit-after-061314-v1/checks/current_objective_audit_after_061314_v1_assertions.out",
    "061855_r3_candidate": REPO
    / "docs/experiments/actionable-regime-confidence/runs/20260512T061855+0800-codex-r3-hf-tsie-native-subhour-source-screen-v1/checks/r3_hf_tsie_native_subhour_source_screen_v1_assertions.out",
    "062029_tsie_target_cells": REPO
    / "docs/experiments/actionable-regime-confidence/runs/20260512T062029+0800-codex-r3-tsie-target-cell-disposition-after-061855-empty-v1/checks/r3_tsie_target_cell_disposition_after_061855_empty_v1_assertions.out",
    "062409_source_selection": REPO
    / "docs/experiments/actionable-regime-confidence/runs/20260512T062409+0800-codex-r3-r5-source-selection-readback-after-061855-v1/checks/r3_r5_source_selection_readback_after_061855_v1_assertions.out",
}


def sha256(path: Path) -> str | None:
    if not path.is_file():
        return None
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_assertions(path: Path) -> dict:
    result = {}
    if not path.is_file():
        return result
    for line in path.read_text(errors="replace").splitlines():
        if "=" in line:
            k, v = line.split("=", 1)
            result[k.strip()] = v.strip()
    return result


def count_csv_rows(path: Path) -> int | None:
    if not path.is_file():
        return None
    with path.open("r", encoding="utf-8", errors="replace", newline="") as f:
        return max(sum(1 for _ in csv.reader(f)) - 1, 0)


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)

    board_hash = sha256(BOARD)
    assertions = {name: read_assertions(path) for name, path in ASSERTION_FILES.items()}
    required_status = {str(root): root.exists() for root in REQUIRED_ROOTS}
    source_equiv_rows = count_csv_rows(SOURCE_EQUIV / "source_label_equivalence_rows.csv")

    checklist = [
        {
            "requirement": "Each active MainRegimeV2 root reaches >=95% calibrated confidence",
            "evidence": "061421 source-label equivalence calibration; 061813 failure decomposition",
            "status": "blocked",
            "gap": "Accepted source-confidence labels remain 0/4; all labels miss Wilson95 lower-bound gate.",
        },
        {
            "requirement": "Validate every regime across other markets, cycles, and timeframes",
            "evidence": "053856 axis audit; 061855/062029/062409 R3 TSIE disposition",
            "status": "blocked",
            "gap": "Current reliable evidence remains daily/source-equivalence or rejected sidecar; R3 native subhour root absent.",
        },
        {
            "requirement": "Use real source/control evidence, not proxy datasets",
            "evidence": "062409 source selection; 061659 arrival refresh",
            "status": "blocked",
            "gap": "Selected unlock candidates 0; required roots absent; TSIE/HMM/NIFTY/Kaggle sidecars rejected.",
        },
        {
            "requirement": "R6 owner/export controls available for direct Manipulation",
            "evidence": "061314 operator dispatch handoff; 061659 arrival refresh",
            "status": "blocked",
            "gap": "Dispatch drafts present but not sent; no approval, ticket, export/license id, or verifier-native rows.",
        },
        {
            "requirement": "R5 post-cutoff source-panel recency rows",
            "evidence": "060446 local drop sweep; 062409 source selection",
            "status": "blocked",
            "gap": "Known stock-market-regimes panel remains daily through 2026-01-30; R5 target root absent.",
        },
        {
            "requirement": "R3 native sub-hour source labels",
            "evidence": "061855 candidate screen; 062029 target-cell disposition; 062409 source selection",
            "status": "blocked",
            "gap": "No verifier-native AAPL/IXIC 15m/30m MainRegimeV2 rows in required root.",
        },
        {
            "requirement": "Run provider/AutoQuant -> filter/Pre-Bayes -> BBN -> CatBoost/path-ranking -> execution-tree after unlock",
            "evidence": "061521 current audit and later source-selection gates",
            "status": "blocked",
            "gap": "No required root unlock; canonical merge and downstream promotion rerun are not allowed.",
        },
        {
            "requirement": "Do not disturb multi-agent board work",
            "evidence": "Append-only 062409 registration and duplicate-placement reconciliations",
            "status": "pass",
            "gap": "Current Cursor not edited; duplicate sections counted once.",
        },
    ]

    objective_complete = all(row["status"] == "pass" for row in checklist)
    gate = (
        "current_objective_audit_after_062409_v1="
        "not_complete_required_roots_absent_no_source_control_no_downstream_rerun"
    )
    result = {
        "run_id": RUN_ROOT.name,
        "gate_result": gate,
        "board_sha256_before_artifact": board_hash,
        "objective_complete": objective_complete,
        "checklist": checklist,
        "required_roots": required_status,
        "source_label_equivalence_present": SOURCE_EQUIV.exists(),
        "source_label_equivalence_rows": source_equiv_rows,
        "latest_assertions": assertions,
        "accepted_rows_added": 0,
        "source_control_evidence_acquired": False,
        "target_root_mutated": False,
        "canonical_merge": False,
        "downstream_promotion_rerun": False,
        "strict_full_objective": False,
        "trade_usable": False,
        "update_goal": False,
    }
    json_path = OUT / "current_objective_audit_after_062409_v1.json"
    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")

    checklist_path = OUT / "prompt_to_artifact_checklist_after_062409_v1.csv"
    with checklist_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["requirement", "evidence", "status", "gap"])
        writer.writeheader()
        writer.writerows(checklist)

    report = [
        "# Current Objective Audit After 062409 v1",
        "",
        f"Run id: `{RUN_ROOT.name}`",
        "",
        f"Gate result: `{gate}`",
        "",
        f"Board sha256 before artifact: `{board_hash}`",
        "",
        "## Objective",
        "",
        "Every active regime must reach at least 95% calibrated confidence, survive validation across other markets/cycles/timeframes, and then pass the ordered provider/AutoQuant -> filter/Pre-Bayes -> BBN -> CatBoost/path-ranking -> execution-tree chain without disturbing concurrent board work.",
        "",
        "## Prompt-To-Artifact Checklist",
        "",
        "| Requirement | Evidence | Status | Gap |",
        "|---|---|---|---|",
    ]
    for row in checklist:
        report.append(
            f"| {row['requirement']} | {row['evidence']} | `{row['status']}` | {row['gap']} |"
        )
    report.extend(
        [
            "",
            "## Current Roots",
            "",
        ]
    )
    for root, present in required_status.items():
        report.append(f"- `{root}`: `{str(present).lower()}`")
    report.extend(
        [
            f"- `/tmp/ict-engine-source-label-equivalence-intake`: `{str(SOURCE_EQUIV.exists()).lower()}`, rows `{source_equiv_rows}`",
            "",
            "## Decision",
            "",
            "The objective is not complete. The latest source-selection readback selected `0` R3/R5 public candidates for target-root materialization, the three required roots remain absent, source/control evidence is still false, and downstream promotion rerun is not allowed.",
            "",
            "No `update_goal` call is authorized.",
            "",
            "## Next",
            "",
            "Continue only after explicit source/control approval, verifier-native R6 owner-export rows with valid controls, source-owned R5 recency rows, or verifier-native R3 native-subhour MainRegimeV2 rows unlock a required root. Then rerun direct verifier, split calibration, canonical merge, providers, AutoQuant, filter/Pre-Bayes, BBN, CatBoost/path-ranking, and execution-tree readback in order.",
            "",
            "## Artifacts",
            "",
            f"- JSON: `{json_path.relative_to(REPO)}`",
            f"- Checklist CSV: `{checklist_path.relative_to(REPO)}`",
            f"- Assertions: `{(CHECKS / 'current_objective_audit_after_062409_v1_assertions.out').relative_to(REPO)}`",
        ]
    )
    (OUT / "current_objective_audit_after_062409_v1.md").write_text(
        "\n".join(report) + "\n"
    )

    assertion_lines = [
        f"gate_result={gate}",
        f"objective_complete={str(objective_complete).lower()}",
        f"required_roots_absent={str(not any(required_status.values())).lower()}",
        f"source_label_equivalence_rows={source_equiv_rows}",
        "accepted_rows_added=0",
        "source_control_evidence_acquired=false",
        "target_root_mutated=false",
        "canonical_merge=false",
        "downstream_promotion_rerun=false",
        "strict_full_objective=false",
        "trade_usable=false",
        "update_goal=false",
    ]
    (CHECKS / "current_objective_audit_after_062409_v1_assertions.out").write_text(
        "\n".join(assertion_lines) + "\n"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
