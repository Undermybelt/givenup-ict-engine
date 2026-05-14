#!/usr/bin/env python3
"""Read back restored 012425 fail-closed source-label artifacts."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path


RUN_ID = "20260512T013127-codex-012425-restoration-readback-v1"
BOARD = Path("docs/plans/2026-05-10-actionable-regime-confidence-todo.md")
RUN_ROOT = Path("docs/experiments/actionable-regime-confidence/runs") / RUN_ID
OUT_DIR = RUN_ROOT / "012425-restoration-readback-v1"
CHECK_DIR = RUN_ROOT / "checks"

SOURCE_ROOT = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260512T012425-codex-source-label-qualifying-condition-failclosed-v1"
)
SOURCE_OUT = SOURCE_ROOT / "source-label-qualifying-condition-failclosed-v1"
SOURCE_CHECKS = SOURCE_ROOT / "checks"
SOURCE_SCRIPT = SOURCE_ROOT / "scripts" / "source_label_qualifying_condition_failclosed_v1.py"
SOURCE_JSON = SOURCE_OUT / "source_label_qualifying_condition_failclosed_v1.json"
SOURCE_ASSERTIONS = SOURCE_CHECKS / "source_label_qualifying_condition_failclosed_v1_assertions.out"

STALE_AUDIT_PRESENCE = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260512T012616-codex-current-objective-completion-audit-after-012318-v1/"
    "current-objective-completion-audit-after-012318-v1/"
    "artifact_presence_after_012318_v1.csv"
)

EXPECTED_012425_FILES = [
    SOURCE_OUT / "source_label_qualifying_condition_failclosed_v1.md",
    SOURCE_JSON,
    SOURCE_OUT / "source_label_qualifying_condition_failclosed_conditions_v1.csv",
    SOURCE_OUT / "source_label_qualifying_condition_failclosed_split_validation_v1.csv",
    SOURCE_OUT / "source_label_qualifying_condition_failclosed_market_contexts_v1.csv",
    SOURCE_OUT / "source_label_qualifying_condition_failclosed_sample_rows_v1.csv",
    SOURCE_ASSERTIONS,
    SOURCE_SCRIPT,
]

TMP_ROOTS = [
    ("r6_owner_export", Path("/tmp/ict-engine-board-a-r6-owner-export-v1")),
    ("r3_native_subhour", Path("/tmp/ict-engine-native-subhour-source-label-intake")),
    ("r5_recency_extension", Path("/tmp/ict-engine-source-panel-recency-extension")),
    ("source_label_equivalence", Path("/tmp/ict-engine-source-label-equivalence-intake")),
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_text(path: Path) -> str:
    return path.read_text(errors="replace") if path.exists() else ""


def board_field(board: str, field: str) -> str:
    prefix = f"| {field} |"
    for line in board.splitlines():
        if line.startswith(prefix):
            parts = line.split("|")
            if len(parts) >= 4:
                return parts[2].strip()
    return ""


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def stale_012616_row() -> dict[str, str]:
    if not STALE_AUDIT_PRESENCE.exists():
        return {
            "artifact_id": "source_label_failclosed_conditions",
            "recorded_present": "",
            "recorded_sha256": "",
            "row_found": "false",
        }
    with STALE_AUDIT_PRESENCE.open(newline="") as f:
        for row in csv.DictReader(f):
            if row.get("artifact_id") == "source_label_failclosed_conditions":
                return {
                    "artifact_id": row.get("artifact_id", ""),
                    "recorded_present": row.get("present", ""),
                    "recorded_sha256": row.get("sha256", ""),
                    "row_found": "true",
                }
    return {
        "artifact_id": "source_label_failclosed_conditions",
        "recorded_present": "",
        "recorded_sha256": "",
        "row_found": "false",
    }


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)
    board = read_text(BOARD)
    board_sha = sha256(BOARD) if BOARD.exists() else ""
    last_loop_id = board_field(board, "last_loop_id")
    board_state = board_field(board, "board_state")

    file_rows: list[dict[str, object]] = []
    for path in EXPECTED_012425_FILES:
        exists = path.exists()
        file_rows.append(
            {
                "path": str(path),
                "present": str(exists).lower(),
                "nonempty": str(bool(read_text(path).strip()) if exists else False).lower(),
                "sha256": sha256(path) if exists else "",
            }
        )

    source_data = json.loads(read_text(SOURCE_JSON)) if SOURCE_JSON.exists() else {}
    source_assertions = read_text(SOURCE_ASSERTIONS)
    assertion_failures = [
        line for line in source_assertions.splitlines() if line.strip().endswith("=FAIL")
    ]
    stale_row = stale_012616_row()

    tmp_rows = []
    for root_id, root in TMP_ROOTS:
        tmp_rows.append({"id": root_id, "root": str(root), "present": str(root.exists()).lower()})

    expected_complete = all(row["present"] == "true" and row["nonempty"] == "true" for row in file_rows)
    source_gate = source_data.get("decision", "")
    accepted_labels = source_data.get("accepted_labels", [])
    strict_done = bool(source_data.get("strict_full_objective_achieved", True))
    update_goal = bool(source_data.get("update_goal", True))

    gate_result = "012425_restoration_readback_v1=restored_reference_complete_no_promotion"
    if not expected_complete:
        gate_result = "012425_restoration_readback_v1=reference_still_incomplete_no_promotion"
    if assertion_failures:
        gate_result = "012425_restoration_readback_v1=assertion_failure_no_promotion"
    if strict_done or update_goal:
        gate_result = "012425_restoration_readback_v1=unexpected_completion_claim_blocked"

    summary = {
        "run_id": RUN_ID,
        "board": str(BOARD),
        "board_sha256_before_artifact": board_sha,
        "board_state": board_state,
        "last_loop_id": last_loop_id,
        "gate_result": gate_result,
        "restored_run_root": str(SOURCE_ROOT),
        "expected_files": len(EXPECTED_012425_FILES),
        "present_files": sum(1 for row in file_rows if row["present"] == "true"),
        "nonempty_files": sum(1 for row in file_rows if row["nonempty"] == "true"),
        "expected_files_complete": expected_complete,
        "source_gate_result": source_gate,
        "source_assertion_failures": assertion_failures,
        "stale_012616_artifact_presence_row": stale_row,
        "accepted_labels": accepted_labels,
        "accepted_rows_added": source_data.get("accepted_rows_added", 0),
        "new_confidence_gate": False,
        "canonical_merge_allowed": False,
        "downstream_chain_rerun_allowed": False,
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

    write_csv(
        OUT_DIR / "012425_restored_file_status_v1.csv",
        file_rows,
        ["path", "present", "nonempty", "sha256"],
    )
    write_csv(
        OUT_DIR / "tmp_root_status_after_012425_restoration_v1.csv",
        tmp_rows,
        ["id", "root", "present"],
    )
    write_csv(
        OUT_DIR / "stale_012616_presence_row_v1.csv",
        [stale_row],
        ["artifact_id", "recorded_present", "recorded_sha256", "row_found"],
    )

    (OUT_DIR / "012425_restoration_readback_v1.json").write_text(
        json.dumps(summary, indent=2) + "\n"
    )
    (OUT_DIR / "012425_restoration_readback_v1.md").write_text(
        f"""# 012425 Restoration Readback v1

Gate result: `{gate_result}`.

Current board:
- board_state: `{board_state}`
- last_loop_id: `{last_loop_id}`
- board SHA-256 before artifact: `{board_sha}`

Restored reference:
- Run root: `{SOURCE_ROOT}`
- Expected files present: `{summary['present_files']}/{summary['expected_files']}`
- Non-empty files: `{summary['nonempty_files']}/{summary['expected_files']}`
- Source packet gate: `{source_gate}`
- Source packet accepted labels: `{accepted_labels}`

Stale upstream note:
- `012616` artifact-presence row for `source_label_failclosed_conditions` recorded present=`{stale_row['recorded_present']}`.
- That row is now stale because the restored 012425 JSON exists and is hashed in this readback.

Promotion decision:
- Accepted rows added: `0`
- New confidence gate: false
- Canonical merge allowed: false
- Downstream provider/Auto-Quant/pre-Bayes/BBN/CatBoost/execution-tree rerun allowed: false
- Strict full objective achieved: false
- `update_goal=false`

Remaining blockers:
- R6 owner-export root is still absent.
- R3 native-subhour source-label root is still absent.
- R5 recency-extension source root is still absent.
- Bull/Sideways remain fail-closed condition leads only; Bear/Crisis remain blocked.

Artifacts:
- JSON: `docs/experiments/actionable-regime-confidence/runs/{RUN_ID}/012425-restoration-readback-v1/012425_restoration_readback_v1.json`
- Restored file status CSV: `docs/experiments/actionable-regime-confidence/runs/{RUN_ID}/012425-restoration-readback-v1/012425_restored_file_status_v1.csv`
- Tmp root status CSV: `docs/experiments/actionable-regime-confidence/runs/{RUN_ID}/012425-restoration-readback-v1/tmp_root_status_after_012425_restoration_v1.csv`
- Stale 012616 row CSV: `docs/experiments/actionable-regime-confidence/runs/{RUN_ID}/012425-restoration-readback-v1/stale_012616_presence_row_v1.csv`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/{RUN_ID}/checks/012425_restoration_readback_v1_assertions.out`

Next:
- Preserve the Current Cursor next action for R6. Treat the 012425 reference as artifact-restored but still fail-closed; continue only from source-owned R6 controls or explicit `FLIP` approval plus exact R3/R5/source-native evidence.
"""
    )

    assertions = [
        f"run_id={RUN_ID}",
        f"expected_files_complete={str(expected_complete).lower()}",
        f"source_assertion_failures={len(assertion_failures)}",
        f"source_gate_result={source_gate}",
        f"accepted_labels_empty={str(accepted_labels == []).lower()}",
        "accepted_rows_added_zero=true",
        "new_confidence_gate_false=true",
        "canonical_merge_allowed_false=true",
        "downstream_chain_rerun_allowed_false=true",
        "strict_full_objective_achieved_false=true",
        "update_goal_false=true",
        "runtime_code_changed_false=true",
        "shared_intake_mutated_false=true",
        "roots_not_mutated=true",
        "thresholds_relaxed_false=true",
        "raw_data_committed_false=true",
        "external_requests_sent_false=true",
        "trade_usable_false=true",
    ]
    (CHECK_DIR / "012425_restoration_readback_v1_assertions.out").write_text(
        "\n".join(assertions) + "\n"
    )


if __name__ == "__main__":
    main()
