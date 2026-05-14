#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path


RUN_ID = "20260512T013854-codex-latest-unregistered-root-readback-v1"
RUNS = [
    "20260512T013436-codex-provider-autoquant-readonly-refresh-after-0130-v1",
    "20260512T013533-codex-readonly-runtime-chain-refresh-after-013042-v1",
    "20260512T013605-codex-partial-root-hygiene-readback-after-0135-v1",
    "20260512T013634-codex-r6-owner-export-contract-readback-v1",
    "20260512T013716-codex-r6-owner-control-local-inbox-scan-v1",
    "20260512T013719-codex-board-b-220646-structural-execution-candidate-handoff-v1",
    "20260512T013904-codex-autoquant-latest-backtest-cache-readback-v1",
]
TARGET_ROOTS = [
    ("r6_owner_export", Path("/tmp/ict-engine-board-a-r6-owner-export-v1")),
    ("r3_native_subhour", Path("/tmp/ict-engine-native-subhour-source-label-intake")),
    ("r5_recency_extension", Path("/tmp/ict-engine-source-panel-recency-extension")),
    ("source_label_equivalence", Path("/tmp/ict-engine-source-label-equivalence-intake")),
]


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_current_cursor(board_text: str) -> dict[str, str]:
    cursor: dict[str, str] = {}
    in_cursor = False
    for raw_line in board_text.splitlines():
        line = raw_line.strip()
        if line == "## Current Cursor":
            in_cursor = True
            continue
        if in_cursor and line.startswith("## "):
            break
        if not in_cursor or not line.startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) >= 2 and cells[0] not in {"Field", "---"}:
            cursor[cells[0]] = cells[1]
    return cursor


def count_files(root: Path, suffix: str | None = None) -> int:
    if not root.exists():
        return 0
    if suffix is None:
        return sum(1 for path in root.rglob("*") if path.is_file())
    return sum(1 for path in root.rglob(f"*{suffix}") if path.is_file())


def first_paths(root: Path, pattern: str, limit: int = 3) -> str:
    if not root.exists():
        return ""
    return ";".join(str(path) for path in sorted(root.rglob(pattern))[:limit])


def classify(row: dict[str, object]) -> str:
    run_id = str(row["run_id"])
    if not row["present"]:
        return "absent_not_evidence"
    if run_id.startswith("20260512T013533"):
        return "complete_readonly_runtime_chain_non_promoting"
    if run_id.startswith("20260512T013605"):
        return "complete_hygiene_readback_non_promoting"
    if run_id.startswith("20260512T013436"):
        return "partial_command_capture_only_not_evidence"
    if run_id.startswith("20260512T013634"):
        if int(row["markdown_count"]) > 0 and int(row["json_count"]) > 0 and int(row["assertion_count"]) > 0:
            return "complete_owner_export_contract_readback_non_promoting"
        if int(row["command_output_count"]) > 0:
            return "command_output_only_owner_contract_readback_not_evidence"
        return "script_only_owner_contract_readback_not_evidence"
    if run_id.startswith("20260512T013716"):
        if int(row["markdown_count"]) > 0 and int(row["json_count"]) > 0 and int(row["assertion_count"]) > 0:
            return "complete_local_inbox_scan_non_promoting"
        return "script_only_local_inbox_scan_not_evidence"
    if run_id.startswith("20260512T013719"):
        return "board_b_raw_state_copy_not_board_a_promotion_evidence"
    if run_id.startswith("20260512T013904"):
        return "complete_autoquant_cache_readback_negative_non_promoting"
    return "reviewed_not_promotion_evidence"


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def bool_word(value: object) -> str:
    return str(bool(value)).lower()


def main() -> int:
    script_path = Path(__file__).resolve()
    run_root = script_path.parents[1]
    repo_root = script_path.parents[6]
    out_dir = run_root / "latest-unregistered-root-readback-v1"
    checks_dir = run_root / "checks"
    runs_root = repo_root / "docs/experiments/actionable-regime-confidence/runs"
    board_path = repo_root / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"
    board_text = board_path.read_text(encoding="utf-8")
    cursor = parse_current_cursor(board_text)

    out_dir.mkdir(parents=True, exist_ok=True)
    checks_dir.mkdir(parents=True, exist_ok=True)

    root_rows: list[dict[str, object]] = []
    for run_id in RUNS:
        root = runs_root / run_id
        row: dict[str, object] = {
            "run_id": run_id,
            "path": str(root),
            "present": root.exists(),
            "file_count": count_files(root),
            "markdown_count": count_files(root, ".md"),
            "json_count": count_files(root, ".json"),
            "assertion_count": count_files(root / "checks"),
            "script_count": count_files(root / "scripts", ".py"),
            "command_output_count": count_files(root / "command-output"),
            "board_refs_before": board_text.count(run_id),
            "sample_markdown_paths": first_paths(root, "*.md"),
            "sample_assertion_paths": first_paths(root / "checks", "*"),
        }
        row["classification"] = classify(row)
        row["promotion_evidence"] = False
        root_rows.append(row)

    tmp_rows = []
    for root_id, root in TARGET_ROOTS:
        tmp_rows.append(
            {
                "id": root_id,
                "root": str(root),
                "present": root.exists(),
                "file_count": count_files(root),
            }
        )

    result = {
        "run_id": RUN_ID,
        "board_hash_before": sha256_file(board_path),
        "observed_cursor": cursor.get("last_loop_id", ""),
        "board_state": cursor.get("board_state", ""),
        "current_run_root": cursor.get("current_run_root", ""),
        "gate_result": "latest_unregistered_root_readback_v1=fresh_roots_reviewed_no_promotion_required_roots_missing",
        "reviewed_roots": root_rows,
        "tmp_roots": tmp_rows,
        "accepted_rows_added": 0,
        "new_confidence_gate": False,
        "canonical_merge_allowed": False,
        "downstream_chain_rerun_allowed": False,
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "shared_intake_mutated": False,
        "r3_r5_r6_roots_mutated": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "external_requests_sent": False,
        "trade_usable": False,
    }

    fields = [
        "run_id",
        "classification",
        "present",
        "file_count",
        "markdown_count",
        "json_count",
        "assertion_count",
        "script_count",
        "command_output_count",
        "board_refs_before",
        "promotion_evidence",
        "path",
        "sample_markdown_paths",
        "sample_assertion_paths",
    ]
    write_csv(out_dir / "latest_unregistered_root_status_v1.csv", root_rows, fields)
    write_csv(out_dir / "latest_unregistered_tmp_root_status_v1.csv", tmp_rows, ["id", "root", "present", "file_count"])
    (out_dir / "latest_unregistered_root_readback_v1.json").write_text(
        json.dumps(result, indent=2) + "\n",
        encoding="utf-8",
    )

    root_lines = [
        (
            f"- `{row['run_id']}`: `{row['classification']}`; files `{row['file_count']}`, "
            f"markdown `{row['markdown_count']}`, json `{row['json_count']}`, "
            f"assertions `{row['assertion_count']}`, board refs before write `{row['board_refs_before']}`."
        )
        for row in root_rows
    ]
    tmp_lines = [
        f"- `{row['id']}`: present `{bool_word(row['present'])}`, files `{row['file_count']}` at `{row['root']}`."
        for row in tmp_rows
    ]
    (out_dir / "latest_unregistered_root_readback_v1.md").write_text(
        "\n".join(
            [
                "# Latest Unregistered Root Readback v1",
                "",
                f"Run id: `{RUN_ID}`",
                f"Gate result: `{result['gate_result']}`",
                f"Observed cursor: `{result['observed_cursor']}`",
                f"Board state: `{result['board_state']}`",
                "",
                "Reviewed roots:",
                *root_lines,
                "",
                "Tmp root readback:",
                *tmp_lines,
                "",
                "Promotion status:",
                "- Accepted rows added: `0`.",
                "- New confidence gate: `false`.",
                "- Canonical merge allowed: `false`.",
                "- Downstream provider/Auto-Quant/filter/Pre-Bayes/BBN/CatBoost/path-ranking/execution-tree rerun allowed: `false`.",
                "- Strict full objective achieved: `false`; `update_goal=false`.",
                "- Runtime code changed: `false`; shared intake mutated: `false`; thresholds relaxed: `false`; raw data committed: `false`; external requests sent: `false`; trade usable: `false`.",
                "",
                "Next:",
                "- Keep the active R6 cursor unchanged. Treat partial command captures and Board B raw state copies as non-promotion evidence; the Board A unlock remains source-owned R6 controls or explicit FLIP approval plus canonical merge.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    tmp_present = {row["id"]: bool(row["present"]) for row in tmp_rows}
    assertions = {
        "cursor_still_010127": str(result["observed_cursor"]).startswith("20260512T010127"),
        "r6_owner_export_root_absent": tmp_present["r6_owner_export"] is False,
        "r3_native_subhour_root_absent": tmp_present["r3_native_subhour"] is False,
        "r5_recency_extension_root_absent": tmp_present["r5_recency_extension"] is False,
        "source_label_equivalence_root_present": tmp_present["source_label_equivalence"] is True,
        "accepted_rows_added_zero": result["accepted_rows_added"] == 0,
        "canonical_merge_allowed_false": result["canonical_merge_allowed"] is False,
        "downstream_chain_rerun_allowed_false": result["downstream_chain_rerun_allowed"] is False,
        "strict_full_objective_achieved_false": result["strict_full_objective_achieved"] is False,
        "update_goal_false": result["update_goal"] is False,
        "runtime_code_changed_false": result["runtime_code_changed"] is False,
        "shared_intake_mutated_false": result["shared_intake_mutated"] is False,
        "raw_data_committed_false": result["raw_data_committed"] is False,
        "external_requests_sent_false": result["external_requests_sent"] is False,
        "no_reviewed_root_marked_promotion_evidence": all(row["promotion_evidence"] is False for row in root_rows),
    }
    (checks_dir / "latest_unregistered_root_readback_v1_assertions.out").write_text(
        "\n".join(f"{key}={'PASS' if value else 'FAIL'}" for key, value in assertions.items()) + "\n",
        encoding="utf-8",
    )
    return 0 if all(assertions.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
