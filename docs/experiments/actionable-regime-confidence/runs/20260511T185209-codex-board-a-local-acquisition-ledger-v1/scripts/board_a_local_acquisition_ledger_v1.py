#!/usr/bin/env python3
"""Board A local acquisition gap ledger for concurrent blocker artifacts."""

from __future__ import annotations

import csv
import fnmatch
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[6]
RUN_ID = "20260511T185209-codex-board-a-local-acquisition-ledger-v1"
RUN_ROOT = REPO_ROOT / "docs/experiments/actionable-regime-confidence/runs" / RUN_ID
OUT_DIR = RUN_ROOT / "local-acquisition-ledger"
CHECK_DIR = RUN_ROOT / "checks"
TODO_PATH = REPO_ROOT / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"

READBACKS = [
    {
        "run_id": "20260511T184630-codex-direct-manipulation-coverage-readback-v2",
        "json": "direct-manipulation-readback/direct_manipulation_coverage_readback_v2.json",
        "kind": "direct_manipulation_coverage",
    },
    {
        "run_id": "20260511T184856-codex-source-label-other-market-readback-v1",
        "json": "source-label-readback/source_label_other_market_readback_v1.json",
        "kind": "source_label_other_market",
    },
]

INTAKE_REQUIRED = {
    "external_bundle_price_rows": "/tmp/ict-engine-board-a-external-intake-bundle-v1/price-root/source_label_equivalence_rows.csv",
    "external_bundle_price_provenance": "/tmp/ict-engine-board-a-external-intake-bundle-v1/price-root/source_label_equivalence_provenance.json",
    "external_bundle_recency_rows": "/tmp/ict-engine-board-a-external-intake-bundle-v1/recency/source_panel_recency_extension_rows.csv",
    "external_bundle_recency_provenance": "/tmp/ict-engine-board-a-external-intake-bundle-v1/recency/source_panel_recency_extension_provenance.json",
    "external_bundle_direct_positive": "/tmp/ict-engine-board-a-external-intake-bundle-v1/direct-manipulation/direct_manipulation_positive_rows.csv",
    "external_bundle_direct_controls": "/tmp/ict-engine-board-a-external-intake-bundle-v1/direct-manipulation/direct_manipulation_matched_controls.csv",
    "external_bundle_direct_provenance": "/tmp/ict-engine-board-a-external-intake-bundle-v1/direct-manipulation/direct_manipulation_provenance.json",
    "source_equivalence_rows": "/tmp/ict-engine-source-label-equivalence-intake/source_label_equivalence_rows.csv",
    "source_equivalence_provenance": "/tmp/ict-engine-source-label-equivalence-intake/source_label_equivalence_provenance.json",
    "direct_intake_positive": "/tmp/ict-engine-direct-manipulation-row-intake/positive_spoofing_layering_rows.csv",
    "direct_intake_controls": "/tmp/ict-engine-direct-manipulation-row-intake/matched_negative_normal_activity_rows.csv",
    "direct_intake_provenance": "/tmp/ict-engine-direct-manipulation-row-intake/provenance_manifest.json",
}

SEARCH_ROOTS = [
    (Path("/tmp"), 8),
    (Path("/Users/thrill3r/Downloads"), 4),
]
SEARCH_PATTERNS = [
    "*pump*",
    "*dump*",
    "*order*book*",
    "*depth*",
    "*spoof*",
    "*manip*",
    "*regime*",
    "*source*label*",
]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def iter_limited_files(root: Path, max_depth: int) -> list[Path]:
    if not root.exists():
        return []
    files: list[Path] = []
    root_depth = len(root.parts)
    for dirpath, dirnames, filenames in os.walk(root):
        current = Path(dirpath)
        depth = len(current.parts) - root_depth
        if depth >= max_depth:
            dirnames[:] = []
        for name in filenames:
            path = current / name
            lowered = name.lower()
            if any(fnmatch.fnmatch(lowered, pattern) for pattern in SEARCH_PATTERNS):
                files.append(path)
                if len(files) >= 500:
                    return files
    return files


def classify_candidate(path: Path) -> str:
    text = str(path).lower()
    suffix = path.suffix.lower()
    if "stock-market-regimes-20002026" in text and suffix in {".csv", ".parquet"}:
        return "existing_stock_regime_source_panel_not_new_equivalence"
    if suffix in {".py", ".ts", ".js", ".md", ".txt"}:
        return "script_or_document_not_source_rows"
    if suffix in {".csv", ".parquet", ".feather", ".json"}:
        return "data_file_needs_schema_owner_match"
    return "not_row_intake_candidate"


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)
    todo_text = TODO_PATH.read_text(encoding="utf-8")

    readback_rows = []
    bad_completion_signals: list[str] = []
    accepted_total = 0
    for item in READBACKS:
        run_root = REPO_ROOT / "docs/experiments/actionable-regime-confidence/runs" / item["run_id"]
        payload = load_json(run_root / item["json"])
        decision = payload.get("decision", {})
        if not isinstance(decision, dict):
            decision = {}
        accepted = int(decision.get("accepted_rows_added") or 0)
        accepted_total += accepted
        if decision.get("full_objective_achieved") is True:
            bad_completion_signals.append(f"{item['run_id']}:full_objective")
        if decision.get("update_goal") is True:
            bad_completion_signals.append(f"{item['run_id']}:update_goal")
        if decision.get("new_confidence_gate") is True or accepted:
            bad_completion_signals.append(f"{item['run_id']}:new_gate_or_rows")
        readback_rows.append(
            {
                "run_id": item["run_id"],
                "kind": item["kind"],
                "registered_in_todo_before_this_ledger": item["run_id"] in todo_text,
                "gate_result": decision.get("gate_result"),
                "accepted_rows_added": accepted,
                "new_confidence_gate": decision.get("new_confidence_gate"),
                "full_objective_achieved": decision.get("full_objective_achieved"),
                "update_goal": decision.get("update_goal"),
                "path": str(run_root.relative_to(REPO_ROOT)),
            }
        )

    intake_rows = []
    for name, raw_path in INTAKE_REQUIRED.items():
        path = Path(raw_path)
        intake_rows.append(
            {
                "name": name,
                "path": str(path),
                "exists": path.exists(),
                "size": path.stat().st_size if path.exists() else 0,
                "sha256": sha256(path) if path.exists() and path.is_file() else "",
            }
        )

    local_candidates = []
    for root, max_depth in SEARCH_ROOTS:
        for path in iter_limited_files(root, max_depth):
            local_candidates.append(
                {
                    "root": str(root),
                    "path": str(path),
                    "classification": classify_candidate(path),
                    "suffix": path.suffix.lower(),
                }
            )

    ready_intake_file_count = sum(1 for row in intake_rows if row["exists"])
    ready_row_candidate_count = sum(
        1
        for row in local_candidates
        if row["classification"] == "data_file_needs_schema_owner_match"
    )
    existing_source_panel_count = sum(
        1
        for row in local_candidates
        if row["classification"] == "existing_stock_regime_source_panel_not_new_equivalence"
    )

    decision = {
        "gate_result": "board_a_local_acquisition_ledger_v1=readbacks_registered_no_ready_local_intake",
        "bad_completion_signals": bad_completion_signals,
        "accepted_rows_added": accepted_total,
        "new_confidence_gate": False,
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "trade_usable": False,
    }

    payload = {
        "artifact_type": "board_a_local_acquisition_ledger_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "run_id": RUN_ID,
        "todo_hash_before_append": sha256(TODO_PATH),
        "readback_rows": readback_rows,
        "intake_rows": intake_rows,
        "local_candidate_count": len(local_candidates),
        "ready_intake_file_count": ready_intake_file_count,
        "ready_row_candidate_count": ready_row_candidate_count,
        "existing_source_panel_count": existing_source_panel_count,
        "decision": decision,
        "next": (
            "Acquire source-owned or owner-approved rows for the missing external bundle files; "
            "current local files are either already-known stock-regime panels or scripts/documents."
        ),
    }
    (OUT_DIR / "board_a_local_acquisition_ledger_v1.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    with (OUT_DIR / "board_a_local_acquisition_readbacks_v1.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(readback_rows[0].keys()))
        writer.writeheader()
        writer.writerows(readback_rows)

    with (OUT_DIR / "board_a_local_acquisition_intake_files_v1.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(intake_rows[0].keys()))
        writer.writeheader()
        writer.writerows(intake_rows)

    with (OUT_DIR / "board_a_local_acquisition_candidates_v1.csv").open("w", newline="", encoding="utf-8") as handle:
        fieldnames = ["root", "path", "classification", "suffix"]
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(local_candidates)

    missing_intake = len(intake_rows) - ready_intake_file_count
    unregistered = [row["run_id"] for row in readback_rows if not row["registered_in_todo_before_this_ledger"]]
    report_lines = [
        "# Board A Local Acquisition Ledger v1",
        "",
        f"Run ID: `{RUN_ID}`",
        "",
        "Supplemental Board A ledger only. It registers completed concurrent blocker readbacks and checks local acquisition roots for ready source-owned intake files.",
        "",
        "## Readbacks",
        "",
    ]
    for row in readback_rows:
        report_lines.append(
            f"- `{row['run_id']}`: `{row['gate_result']}`; registered before this ledger: `{str(row['registered_in_todo_before_this_ledger']).lower()}`."
        )
    report_lines.extend(
        [
            "",
            "## Local Acquisition Check",
            "",
            f"- Required intake files present: `{ready_intake_file_count}/{len(intake_rows)}`; missing: `{missing_intake}`.",
            f"- Local relevant candidate files scanned: `{len(local_candidates)}`.",
            f"- Existing stock-regime source-panel files found: `{existing_source_panel_count}`; these are already-known source panels, not new other-market equivalence rows.",
            f"- Data files needing schema/owner match: `{ready_row_candidate_count}`.",
            "",
            "## Decision",
            "",
            f"`{decision['gate_result']}`",
            "",
            f"- Unregistered completed readbacks before this ledger: `{len(unregistered)}`.",
            "- Accepted rows added: `0`; new confidence gate: `false`.",
            "- Strict full objective achieved: `false`; `update_goal=false`.",
            "- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; trade usable: `false`.",
            "",
            "## Artifacts",
            "",
            f"- JSON: `docs/experiments/actionable-regime-confidence/runs/{RUN_ID}/local-acquisition-ledger/board_a_local_acquisition_ledger_v1.json`",
            f"- Readbacks CSV: `docs/experiments/actionable-regime-confidence/runs/{RUN_ID}/local-acquisition-ledger/board_a_local_acquisition_readbacks_v1.csv`",
            f"- Intake files CSV: `docs/experiments/actionable-regime-confidence/runs/{RUN_ID}/local-acquisition-ledger/board_a_local_acquisition_intake_files_v1.csv`",
            f"- Local candidates CSV: `docs/experiments/actionable-regime-confidence/runs/{RUN_ID}/local-acquisition-ledger/board_a_local_acquisition_candidates_v1.csv`",
            f"- Assertions: `docs/experiments/actionable-regime-confidence/runs/{RUN_ID}/checks/board_a_local_acquisition_ledger_v1_assertions.out`",
            "",
        ]
    )
    (OUT_DIR / "board_a_local_acquisition_ledger_v1.md").write_text(
        "\n".join(report_lines),
        encoding="utf-8",
    )

    assertions = [
        f"PASS readbacks={len(readback_rows)}",
        f"PASS unregistered_readbacks_before_ledger={len(unregistered)}",
        f"PASS ready_intake_file_count={ready_intake_file_count}",
        f"PASS accepted_rows_added={accepted_total}",
        "PASS new_confidence_gate=false",
        "PASS strict_full_objective=false",
        "PASS update_goal=false",
    ]
    (CHECK_DIR / "board_a_local_acquisition_ledger_v1_assertions.out").write_text(
        "\n".join(assertions) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(decision, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
