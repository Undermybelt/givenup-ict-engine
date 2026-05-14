#!/usr/bin/env python3
"""Board A artifact-integrity readback after restoring the 012425 packet."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path


RUN_ID = "20260512T013119-codex-board-reference-integrity-after-012425-restoration-v1"
REPO = Path(__file__).resolve().parents[6]
BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"
OUT_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs" / RUN_ID
OUT_DIR = OUT_ROOT / "board-reference-integrity-after-012425-restoration-v1"
CHECK_DIR = OUT_ROOT / "checks"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def expected_status(run_id: str, files: list[str], board_text: str) -> dict[str, object]:
    root = REPO / "docs/experiments/actionable-regime-confidence/runs" / run_id
    present_files = [name for name in files if (root / name).exists()]
    missing_files = [name for name in files if not (root / name).exists()]
    return {
        "run_id": run_id,
        "board_reference_count": board_text.count(run_id),
        "root_present": root.exists(),
        "expected_files": len(files),
        "present_files": len(present_files),
        "missing_files": ";".join(missing_files),
        "artifact_status": "complete" if len(present_files) == len(files) else "missing_files",
    }


def csv_value(path: Path, match_value: str, return_field: str) -> str:
    if not path.exists():
        return "missing_csv"
    with path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            if match_value in row.get("path", ""):
                return row.get(return_field, "")
    return "missing_row"


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)
    board_text = BOARD.read_text(encoding="utf-8")

    references = [
        expected_status(
            "20260512T012425-codex-source-label-qualifying-condition-failclosed-v1",
            [
                "source-label-qualifying-condition-failclosed-v1/source_label_qualifying_condition_failclosed_v1.md",
                "source-label-qualifying-condition-failclosed-v1/source_label_qualifying_condition_failclosed_v1.json",
                "source-label-qualifying-condition-failclosed-v1/source_label_qualifying_condition_failclosed_conditions_v1.csv",
                "source-label-qualifying-condition-failclosed-v1/source_label_qualifying_condition_failclosed_split_validation_v1.csv",
                "source-label-qualifying-condition-failclosed-v1/source_label_qualifying_condition_failclosed_market_contexts_v1.csv",
                "source-label-qualifying-condition-failclosed-v1/source_label_qualifying_condition_failclosed_sample_rows_v1.csv",
                "checks/source_label_qualifying_condition_failclosed_v1_assertions.out",
                "scripts/source_label_qualifying_condition_failclosed_v1.py",
            ],
            board_text,
        ),
        expected_status(
            "20260512T012616-codex-current-objective-completion-audit-after-012318-v1",
            [
                "current-objective-completion-audit-after-012318-v1/current_objective_completion_audit_after_012318_v1.md",
                "current-objective-completion-audit-after-012318-v1/current_objective_completion_audit_after_012318_v1.json",
                "current-objective-completion-audit-after-012318-v1/prompt_to_artifact_checklist_after_012318_v1.csv",
                "current-objective-completion-audit-after-012318-v1/artifact_presence_after_012318_v1.csv",
                "current-objective-completion-audit-after-012318-v1/intake_root_status_after_012318_v1.csv",
                "checks/current_objective_completion_audit_after_012318_v1_assertions.out",
                "scripts/current_objective_completion_audit_after_012318_v1.py",
            ],
            board_text,
        ),
        expected_status(
            "20260512T012658-codex-current-objective-completion-audit-after-012425-v1",
            [
                "current-objective-completion-audit-after-012425-v1/current_objective_completion_audit_after_012425_v1.md",
                "current-objective-completion-audit-after-012425-v1/current_objective_completion_audit_after_012425_v1.json",
                "current-objective-completion-audit-after-012425-v1/prompt_to_artifact_checklist_after_012425_v1.csv",
                "checks/current_objective_completion_audit_after_012425_v1_assertions.out",
                "scripts/current_objective_completion_audit_after_012425_v1.py",
            ],
            board_text,
        ),
        expected_status(
            "20260512T012926-codex-board-reference-integrity-after-012616-v1",
            [
                "board-reference-integrity-after-012616-v1/board_reference_integrity_after_012616_v1.md",
                "board-reference-integrity-after-012616-v1/board_reference_integrity_after_012616_v1.json",
                "board-reference-integrity-after-012616-v1/board_reference_integrity_after_012616_v1.csv",
                "board-reference-integrity-after-012616-v1/tmp_root_status_after_012616_v1.csv",
                "checks/board_reference_integrity_after_012616_v1_assertions.out",
                "scripts/board_reference_integrity_after_012616_v1.py",
            ],
            board_text,
        ),
        expected_status(
            "20260512T013042-codex-source-label-cross-timeframe-public-source-screen-v1",
            [
                "source-label-cross-timeframe-public-source-screen-v1/source_label_cross_timeframe_public_source_screen_v1.md",
                "source-label-cross-timeframe-public-source-screen-v1/source_label_cross_timeframe_public_source_screen_v1.json",
                "source-label-cross-timeframe-public-source-screen-v1/source_label_cross_timeframe_public_source_screen_results_v1.csv",
                "source-label-cross-timeframe-public-source-screen-v1/source_label_cross_timeframe_current_condition_timeframes_v1.csv",
                "checks/source_label_cross_timeframe_public_source_screen_v1_assertions.out",
                "scripts/source_label_cross_timeframe_public_source_screen_v1.py",
            ],
            board_text,
        ),
        expected_status(
            "20260512T013106-codex-012425-artifact-restoration-readback-v1",
            [
                "qualifying-condition-012425-artifact-restoration-readback-v1/qualifying_condition_012425_artifact_restoration_readback_v1.md",
                "qualifying-condition-012425-artifact-restoration-readback-v1/qualifying_condition_012425_artifact_restoration_readback_v1.json",
                "qualifying-condition-012425-artifact-restoration-readback-v1/qualifying_condition_012425_artifact_restoration_file_status_v1.csv",
                "command-output/source_label_qualifying_condition_failclosed_exit_code.txt",
                "command-output/source_label_qualifying_condition_failclosed_stdout.txt",
                "command-output/source_label_qualifying_condition_failclosed_stderr.txt",
                "checks/qualifying_condition_012425_artifact_restoration_readback_v1_assertions.out",
                "scripts/qualifying_condition_012425_artifact_restoration_readback_v1.py",
            ],
            board_text,
        ),
        expected_status(
            "20260512T013127-codex-012425-restoration-readback-v1",
            [
                "012425-restoration-readback-v1/012425_restoration_readback_v1.md",
                "012425-restoration-readback-v1/012425_restoration_readback_v1.json",
                "012425-restoration-readback-v1/012425_restored_file_status_v1.csv",
                "012425-restoration-readback-v1/stale_012616_presence_row_v1.csv",
                "012425-restoration-readback-v1/tmp_root_status_after_012425_restoration_v1.csv",
                "checks/012425_restoration_readback_v1_assertions.out",
                "scripts/012425_restoration_readback_v1.py",
            ],
            board_text,
        ),
    ]

    artifact_presence_012616 = (
        REPO
        / "docs/experiments/actionable-regime-confidence/runs"
        / "20260512T012616-codex-current-objective-completion-audit-after-012318-v1"
        / "current-objective-completion-audit-after-012318-v1"
        / "artifact_presence_after_012318_v1.csv"
    )
    stale_presence_value = csv_value(
        artifact_presence_012616,
        "source_label_qualifying_condition_failclosed_v1.json",
        "present",
    )

    prior_integrity_json = (
        REPO
        / "docs/experiments/actionable-regime-confidence/runs"
        / "20260512T012926-codex-board-reference-integrity-after-012616-v1"
        / "board-reference-integrity-after-012616-v1"
        / "board_reference_integrity_after_012616_v1.json"
    )
    prior_gate_result = "missing_json"
    if prior_integrity_json.exists():
        prior_gate_result = json.loads(prior_integrity_json.read_text(encoding="utf-8")).get(
            "gate_result", ""
        )

    tmp_roots = [
        {
            "id": "r6_owner_export",
            "root": "/tmp/ict-engine-board-a-r6-owner-export-v1",
            "present": Path("/tmp/ict-engine-board-a-r6-owner-export-v1").exists(),
        },
        {
            "id": "r3_native_subhour",
            "root": "/tmp/ict-engine-native-subhour-source-label-intake",
            "present": Path("/tmp/ict-engine-native-subhour-source-label-intake").exists(),
        },
        {
            "id": "r5_recency_extension",
            "root": "/tmp/ict-engine-source-panel-recency-extension",
            "present": Path("/tmp/ict-engine-source-panel-recency-extension").exists(),
        },
        {
            "id": "source_label_equivalence",
            "root": "/tmp/ict-engine-source-label-equivalence-intake",
            "present": Path("/tmp/ict-engine-source-label-equivalence-intake").exists(),
        },
    ]

    summary = {
        "run_id": RUN_ID,
        "board": "docs/plans/2026-05-10-actionable-regime-confidence-todo.md",
        "board_sha256_before_append": sha256(BOARD),
        "gate_result": "board_reference_integrity_after_012425_restoration_v1=artifacts_restored_new_roots_reviewed_r6_r3_r5_roots_missing_no_promotion",
        "references": references,
        "artifact_presence_012616_records_012425_present": stale_presence_value,
        "prior_012926_gate_result": prior_gate_result,
        "tmp_roots": tmp_roots,
        "accepted_rows_added": 0,
        "new_confidence_gate": False,
        "canonical_merge_allowed": False,
        "downstream_chain_rerun_allowed": False,
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "shared_intake_mutated": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "external_requests_sent": False,
        "trade_usable": False,
    }

    write_csv(
        OUT_DIR / "board_reference_integrity_after_012425_restoration_v1.csv",
        references,
        [
            "run_id",
            "board_reference_count",
            "root_present",
            "expected_files",
            "present_files",
            "missing_files",
            "artifact_status",
        ],
    )
    write_csv(
        OUT_DIR / "tmp_root_status_after_012425_restoration_v1.csv",
        tmp_roots,
        ["id", "root", "present"],
    )
    (OUT_DIR / "board_reference_integrity_after_012425_restoration_v1.json").write_text(
        json.dumps(summary, indent=2) + "\n",
        encoding="utf-8",
    )

    reference_lines = "\n".join(
        f"- `{row['run_id']}`: board refs `{row['board_reference_count']}`, files `{row['present_files']}/{row['expected_files']}`, status `{row['artifact_status']}`."
        for row in references
    )
    tmp_lines = "\n".join(
        f"- `{row['id']}`: present `{str(row['present']).lower()}` at `{row['root']}`."
        for row in tmp_roots
    )
    (OUT_DIR / "board_reference_integrity_after_012425_restoration_v1.md").write_text(
        "\n".join(
            [
                "# Board Reference Integrity After 012425 Restoration v1",
                "",
                f"Run id: `{RUN_ID}`",
                f"Gate result: `{summary['gate_result']}`",
                "",
                "Reference readback:",
                reference_lines,
                "",
                "Stale-reference readback:",
                f"- `012616` artifact-presence CSV still records the `012425` JSON as present `{stale_presence_value}`.",
                f"- Prior `012926` gate result remains `{prior_gate_result}` and is superseded by this refresh.",
                "",
                "Tmp root readback:",
                tmp_lines,
                "",
                "Result:",
                "- The restored `012425` packet is now complete as fail-closed evidence, not acceptance evidence.",
                "- The newer `013042`, `013106`, and `013127` roots are present and complete; they add fail-closed screening/restoration evidence only.",
                "- The stale missing-artifact statements in earlier `012616` / `012658` / `012926` readbacks are superseded by this refresh.",
                "- R6 owner controls, R3 native sub-hour rows, and R5 recency extension rows are still absent.",
                "- No confidence gate, canonical merge, downstream provider/Auto-Quant/pre-Bayes/BBN/CatBoost/execution-tree rerun, or goal completion is authorized.",
                "",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    assertions = {
        "restored_012425_complete": references[0]["artifact_status"] == "complete",
        "current_cursor_010127_seen_in_board": "20260512T010127+0800-codex-r6-owner-route-entitlement-readback-v1" in board_text,
        "stale_012616_presence_detected": stale_presence_value == "False",
        "prior_012926_stale_gate_detected": "missing" in prior_gate_result,
        "source_cross_timeframe_screen_complete": references[4]["artifact_status"] == "complete",
        "restoration_readback_013106_complete": references[5]["artifact_status"] == "complete",
        "restoration_readback_013127_complete": references[6]["artifact_status"] == "complete",
        "r6_root_absent": not tmp_roots[0]["present"],
        "r3_root_absent": not tmp_roots[1]["present"],
        "r5_root_absent": not tmp_roots[2]["present"],
        "downstream_chain_rerun_allowed_false": summary["downstream_chain_rerun_allowed"] is False,
        "update_goal_false": summary["update_goal"] is False,
    }
    (CHECK_DIR / "board_reference_integrity_after_012425_restoration_v1_assertions.out").write_text(
        "\n".join(f"{key}={value}" for key, value in assertions.items()) + "\n",
        encoding="utf-8",
    )
    return 0 if all(assertions.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
