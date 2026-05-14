#!/usr/bin/env python3
"""Fail-closed readback for partial/new roots after the 0130xx registrations."""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


RUN_ID = "20260512T013605-codex-partial-root-hygiene-readback-after-0135-v1"
REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs" / RUN_ID
OUT = RUN_ROOT / "partial-root-hygiene-readback-after-0135-v1"
CHECKS = RUN_ROOT / "checks"
BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"

TARGET_ROOTS = [
    "20260512T013436-codex-provider-autoquant-readonly-refresh-after-0130-v1",
    "20260512T013502-codex-readonly-runtime-surface-registration-after-0130xx-review-v1",
]

TMP_ROOTS = {
    "r6_owner_export": (
        Path("/tmp/ict-engine-board-a-r6-owner-export-v1"),
        ["direct_manipulation_rows.csv", "direct_manipulation_provenance.json"],
    ),
    "source_label_equivalence": (
        Path("/tmp/ict-engine-source-label-equivalence-intake"),
        ["source_label_equivalence_rows.csv", "source_label_equivalence_provenance.json"],
    ),
    "r3_native_subhour": (
        Path("/tmp/ict-engine-native-subhour-source-label-intake"),
        ["native_subhour_source_label_rows.csv", "native_subhour_source_label_provenance.json"],
    ),
    "r5_recency_extension": (
        Path("/tmp/ict-engine-source-panel-recency-extension"),
        ["stock_market_regimes_2026_extension.csv", "source_panel_recency_provenance.json"],
    ),
}


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def rel(path: Path) -> str:
    return str(path.relative_to(REPO))


def board_ref_count(text: str, token: str) -> int:
    return text.count(token)


def command_exit_codes(root: Path) -> str:
    rows = []
    for path in sorted((root / "command-output").glob("*.exit")):
        rows.append(f"{path.name}:{path.read_text(encoding='utf-8').strip()}")
    return ";".join(rows)


def target_status_rows(board_text: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for run_id in TARGET_ROOTS:
        root = REPO / "docs/experiments/actionable-regime-confidence/runs" / run_id
        files = sorted(path for path in root.rglob("*") if path.is_file())
        report_files = [path for path in files if path.suffix == ".md"]
        json_files = [path for path in files if path.suffix == ".json"]
        assertion_files = [path for path in files if "checks" in path.parts and path.name.endswith("_assertions.out")]
        command_files = [path for path in files if "command-output" in path.parts]
        if assertion_files and json_files and report_files:
            status = "artifact_backed_requires_separate_review"
        elif command_files:
            status = "partial_command_capture_only_not_evidence"
        elif root.exists():
            status = "empty_or_scaffold_root_not_evidence"
        else:
            status = "absent_not_evidence"
        rows.append(
            {
                "run_id": run_id,
                "root_present": str(root.exists()).lower(),
                "file_count": len(files),
                "report_count": len(report_files),
                "json_count": len(json_files),
                "assertion_count": len(assertion_files),
                "command_output_count": len(command_files),
                "command_exit_codes": command_exit_codes(root),
                "board_ref_count": board_ref_count(board_text, run_id),
                "status": status,
            }
        )
    return rows


def tmp_root_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for root_id, (root, required_files) in TMP_ROOTS.items():
        missing = [name for name in required_files if not (root / name).exists()]
        rows.append(
            {
                "root_id": root_id,
                "root": str(root),
                "root_present": str(root.exists()).lower(),
                "required_files": ";".join(required_files),
                "required_files_present": str(not missing).lower(),
                "missing_files": ";".join(missing),
            }
        )
    return rows


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)

    board_text = BOARD.read_text(encoding="utf-8")
    roots = target_status_rows(board_text)
    tmp_roots = tmp_root_rows()

    r6_ready = next(row for row in tmp_roots if row["root_id"] == "r6_owner_export")["required_files_present"] == "true"
    r3_ready = next(row for row in tmp_roots if row["root_id"] == "r3_native_subhour")["required_files_present"] == "true"
    r5_ready = next(row for row in tmp_roots if row["root_id"] == "r5_recency_extension")["required_files_present"] == "true"
    source_ready = next(row for row in tmp_roots if row["root_id"] == "source_label_equivalence")["required_files_present"] == "true"

    gate_result = "partial_root_hygiene_readback_after_0135_v1=partial_roots_not_evidence_r6_r3_r5_missing_no_promotion"
    if any(row["status"] == "artifact_backed_requires_separate_review" for row in roots):
        gate_result = "partial_root_hygiene_readback_after_0135_v1=new_artifact_backed_roots_require_separate_review_no_promotion"

    result = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "gate_result": gate_result,
        "target_roots": roots,
        "tmp_roots": tmp_roots,
        "source_label_equivalence_ready": source_ready,
        "r6_owner_export_ready": r6_ready,
        "r3_native_subhour_ready": r3_ready,
        "r5_recency_extension_ready": r5_ready,
        "canonical_merge_allowed": False,
        "downstream_chain_rerun_allowed": False,
        "accepted_rows_added": 0,
        "new_confidence_gate": False,
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "shared_intake_mutated": False,
        "r3_root_mutated": False,
        "r5_root_mutated": False,
        "r6_owner_export_root_mutated": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "external_requests_sent": False,
        "trade_usable": False,
    }

    json_path = OUT / "partial_root_hygiene_readback_after_0135_v1.json"
    report_path = OUT / "partial_root_hygiene_readback_after_0135_v1.md"
    root_csv = OUT / "new_root_status_after_0135_v1.csv"
    tmp_csv = OUT / "tmp_root_status_after_0135_v1.csv"
    assertions_path = CHECKS / "partial_root_hygiene_readback_after_0135_v1_assertions.out"

    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_csv(
        root_csv,
        roots,
        [
            "run_id",
            "root_present",
            "file_count",
            "report_count",
            "json_count",
            "assertion_count",
            "command_output_count",
            "command_exit_codes",
            "board_ref_count",
            "status",
        ],
    )
    write_csv(
        tmp_csv,
        tmp_roots,
        ["root_id", "root", "root_present", "required_files", "required_files_present", "missing_files"],
    )

    root_lines = [
        f"- `{row['run_id']}`: `{row['status']}`; files `{row['file_count']}`; reports `{row['report_count']}`; JSON `{row['json_count']}`; assertions `{row['assertion_count']}`; board refs `{row['board_ref_count']}`."
        for row in roots
    ]
    report_path.write_text(
        "\n".join(
            [
                "# Partial Root Hygiene Readback After 0135 v1",
                "",
                f"- Gate result: `{gate_result}`.",
                "- Reviewed only the newly visible partial roots after the latest 0130xx registrations.",
                *root_lines,
                f"- Source-label equivalence root ready: `{str(source_ready).lower()}`; R6 owner-export ready: `{str(r6_ready).lower()}`; R3 native-subhour ready: `{str(r3_ready).lower()}`; R5 recency ready: `{str(r5_ready).lower()}`.",
                "- Accepted rows added: `0`; new confidence gate: false; canonical merge allowed: false; downstream chain rerun allowed: false.",
                "- Runtime code changed: false. Shared intake mutated: false. R3/R5/R6 roots mutated: false. Thresholds relaxed: false. Raw data committed: false. External requests sent: false. Trade usable: false.",
                "",
                "Artifacts:",
                f"- JSON: `{rel(json_path)}`",
                f"- New-root CSV: `{rel(root_csv)}`",
                f"- Tmp-root CSV: `{rel(tmp_csv)}`",
                f"- Assertions: `{rel(assertions_path)}`",
                "",
                "Next:",
                "- Preserve the Current Cursor next action for R6. Treat partial command captures and empty scaffolds as non-evidence until report, JSON, provenance, and assertions exist.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    checks = [
        ("source_label_root_ready", source_ready),
        ("r6_owner_export_not_ready", not r6_ready),
        ("r3_native_subhour_not_ready", not r3_ready),
        ("r5_recency_extension_not_ready", not r5_ready),
        ("canonical_merge_allowed_false", result["canonical_merge_allowed"] is False),
        ("downstream_chain_rerun_allowed_false", result["downstream_chain_rerun_allowed"] is False),
        ("strict_full_objective_achieved_false", result["strict_full_objective_achieved"] is False),
        ("update_goal_false", result["update_goal"] is False),
        ("runtime_code_changed_false", result["runtime_code_changed"] is False),
        ("raw_data_committed_false", result["raw_data_committed"] is False),
        ("external_requests_sent_false", result["external_requests_sent"] is False),
    ]
    assertions_path.write_text(
        "\n".join(f"{name}={'PASS' if passed else 'FAIL'}" for name, passed in checks) + "\n",
        encoding="utf-8",
    )
    failed = [name for name, passed in checks if not passed]
    if failed:
        raise SystemExit("failed checks: " + ", ".join(failed))
    print(json.dumps({"gate_result": gate_result, "update_goal": False}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
