#!/usr/bin/env python3
"""Poll Board A source-intake roots after the owner/contact request packets."""

from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


RUN_ID = "20260512T010814-codex-source-intake-root-poll-after-contact-route-v1"
ROOT = Path("docs/experiments/actionable-regime-confidence/runs") / RUN_ID
OUT = ROOT / "source-intake-root-poll-after-contact-route-v1"
CHECKS = ROOT / "checks"
BOARD = Path("docs/plans/2026-05-10-actionable-regime-confidence-todo.md")

TARGETS = [
    {
        "request_id": "r6_oystacher_owner_export",
        "root": "/tmp/ict-engine-board-a-r6-owner-export-v1",
        "required_files": [
            "positive_spoofing_layering_rows.csv",
            "matched_negative_normal_activity_rows.csv",
            "provenance_manifest.json",
        ],
        "verifier": "direct_manipulation_row_intake_verifier",
    },
    {
        "request_id": "r6_oystacher_owner_export_private_tmp_alias",
        "root": "/private/tmp/ict-engine-board-a-r6-owner-export-v1",
        "required_files": [
            "positive_spoofing_layering_rows.csv",
            "matched_negative_normal_activity_rows.csv",
            "provenance_manifest.json",
        ],
        "verifier": "direct_manipulation_row_intake_verifier",
    },
    {
        "request_id": "source_label_equivalence",
        "root": "/tmp/ict-engine-source-label-equivalence-intake",
        "required_files": [
            "source_label_equivalence_rows.csv",
            "source_label_equivalence_provenance.json",
        ],
        "verifier": "source_label_equivalence_verifier",
    },
    {
        "request_id": "r3_native_subhour_source_labels",
        "root": "/tmp/ict-engine-native-subhour-source-label-intake",
        "required_files": [
            "native_subhour_source_label_rows.csv",
            "native_subhour_source_label_provenance.json",
        ],
        "verifier": "native_subhour_source_label_readback",
    },
    {
        "request_id": "r5_source_panel_recency_extension",
        "root": "/tmp/ict-engine-source-panel-recency-extension",
        "required_files": [
            "stock_market_regimes_2026_extension.csv",
            "source_panel_recency_provenance.json",
        ],
        "verifier": "source_panel_recency_extension_verifier",
    },
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def csv_data_rows(path: Path) -> int:
    if not path.exists() or path.suffix.lower() != ".csv":
        return 0
    count = 0
    with path.open("r", encoding="utf-8", errors="replace", newline="") as handle:
        for count, _ in enumerate(handle, start=1):
            pass
    return max(count - 1, 0)


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)

    board_text = BOARD.read_text()
    board_hash = sha256(BOARD)
    cursor = "unknown"
    for line in board_text.splitlines():
        if line.startswith("| last_loop_id |"):
            cursor = line.split("|")[2].strip()
            break

    root_rows: list[dict[str, object]] = []
    file_rows: list[dict[str, object]] = []

    roots_with_all_files = 0
    total_required_files = 0
    present_required_files = 0
    source_rows_present = 0

    for target in TARGETS:
        root = Path(str(target["root"]))
        exists = root.exists()
        is_dir = root.is_dir()
        present_files = []
        for file_name in target["required_files"]:
            file_path = root / file_name
            present = file_path.is_file()
            data_rows = csv_data_rows(file_path) if present else 0
            total_required_files += 1
            present_required_files += int(present)
            source_rows_present += data_rows
            if present:
                present_files.append(file_name)
            file_rows.append(
                {
                    "request_id": target["request_id"],
                    "root": str(root),
                    "required_file": file_name,
                    "present": str(present).lower(),
                    "size_bytes": file_path.stat().st_size if present else 0,
                    "data_rows": data_rows,
                    "sha256": sha256(file_path) if present else "",
                }
            )
        all_files = len(present_files) == len(target["required_files"])
        roots_with_all_files += int(all_files)
        root_rows.append(
            {
                "request_id": target["request_id"],
                "root": str(root),
                "exists": str(exists).lower(),
                "is_dir": str(is_dir).lower(),
                "required_file_count": len(target["required_files"]),
                "present_required_file_count": len(present_files),
                "all_required_files_present": str(all_files).lower(),
                "verifier": target["verifier"],
                "verifier_rerun_allowed": str(all_files).lower(),
            }
        )

    verifier_rerun_allowed = roots_with_all_files > 0
    canonical_merge_allowed = False
    downstream_chain_rerun_allowed = False
    strict_full_objective_achieved = False

    gate_result = "source_intake_root_poll_after_contact_route_v1=target_roots_absent_no_verifier_rerun"
    if verifier_rerun_allowed:
        gate_result = "source_intake_root_poll_after_contact_route_v1=required_files_present_rerun_verifiers_next"

    checklist_rows = [
        {
            "requirement": "every regime reaches 95 percent calibrated confidence",
            "evidence": "board cursor plus root poll",
            "status": "blocked",
            "reason": "source-owned rows remain absent, so no new calibrated regime packet can be promoted",
        },
        {
            "requirement": "validate across other markets and periods",
            "evidence": "target root poll",
            "status": "blocked",
            "reason": "R6 owner controls and non-R6 source-label/R3/R5 roots are absent",
        },
        {
            "requirement": "use real provider/Auto-Quant/pre-Bayes/BBN/CatBoost/execution-tree evidence",
            "evidence": "current board cursor",
            "status": "blocked_not_rerun",
            "reason": "board explicitly forbids downstream promotion rerun until verifier-native controls/provenance arrive",
        },
        {
            "requirement": "do not disturb concurrent board work",
            "evidence": "append-only artifact and board hash",
            "status": "satisfied_for_this_slice",
            "reason": "no shared intake roots were created or mutated; no cursor rewrite by this artifact",
        },
    ]

    write_csv(
        OUT / "target_root_presence_v1.csv",
        root_rows,
        [
            "request_id",
            "root",
            "exists",
            "is_dir",
            "required_file_count",
            "present_required_file_count",
            "all_required_files_present",
            "verifier",
            "verifier_rerun_allowed",
        ],
    )
    write_csv(
        OUT / "required_file_presence_v1.csv",
        file_rows,
        ["request_id", "root", "required_file", "present", "size_bytes", "data_rows", "sha256"],
    )
    write_csv(
        OUT / "prompt_to_artifact_checklist_v1.csv",
        checklist_rows,
        ["requirement", "evidence", "status", "reason"],
    )

    summary = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "board_path": str(BOARD),
        "board_sha256": board_hash,
        "observed_cursor": cursor,
        "gate_result": gate_result,
        "target_roots_checked": len(TARGETS),
        "roots_with_all_required_files": roots_with_all_files,
        "total_required_files": total_required_files,
        "present_required_files": present_required_files,
        "source_rows_present": source_rows_present,
        "source_rows_acquired": source_rows_present,
        "valid_source_owned_normal_controls_found": 0,
        "same_exhibit_flip_approval": False,
        "canonical_merge_allowed": canonical_merge_allowed,
        "verifier_rerun_allowed": verifier_rerun_allowed,
        "downstream_chain_rerun_allowed": downstream_chain_rerun_allowed,
        "accepted_rows_added": 0,
        "new_confidence_gate": False,
        "strict_full_objective_achieved": strict_full_objective_achieved,
        "update_goal": False,
        "runtime_code_changed": False,
        "shared_intake_mutated": False,
        "owner_export_root_mutated": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "trade_usable": False,
    }
    (OUT / "source_intake_root_poll_after_contact_route_v1.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n"
    )

    report = [
        "# Source Intake Root Poll After Contact Route v1",
        "",
        f"- Run id: `{RUN_ID}`.",
        f"- Observed cursor: `{cursor}`.",
        f"- Board SHA-256: `{board_hash}`.",
        f"- Gate result: `{gate_result}`.",
        f"- Target roots checked: `{len(TARGETS)}`.",
        f"- Roots with all required files: `{roots_with_all_files}`.",
        f"- Required files present: `{present_required_files}/{total_required_files}`.",
        f"- Source rows present in checked roots: `{source_rows_present}`.",
        "- Canonical merge allowed: `false`; downstream chain rerun allowed: `false`.",
        "- Accepted rows added: `0`; strict full objective achieved: false. `update_goal=false`.",
        "- Runtime code changed: false. Shared intake mutated: false. Owner-export root mutated: false.",
        "",
        "## Decision",
        "",
        (
            "A complete source-label equivalence root is present, so rerun the fail-closed source-label verifier and confidence calibration before making any Board A confidence claim. "
            "R6 owner controls, R3 native sub-hour rows, and R5 recency-extension rows are still absent or incomplete, so do not rerun the direct verifier or the provider/Auto-Quant/pre-Bayes/BBN/CatBoost/execution-tree chain as promotion evidence yet."
            if verifier_rerun_allowed
            else "No verifier-native source rows or provenance files are present under the required R6 or non-R6 intake roots. Do not rerun the direct verifier or the provider/Auto-Quant/pre-Bayes/BBN/CatBoost/execution-tree chain as promotion evidence until exact source-owned files arrive or explicit `FLIP` control approval is recorded."
        ),
    ]
    (OUT / "source_intake_root_poll_after_contact_route_v1.md").write_text("\n".join(report) + "\n")

    assertions = [
        f"run_id={RUN_ID}",
        f"gate_result={gate_result}",
        f"observed_cursor={cursor}",
        f"target_roots_checked={len(TARGETS)}",
        f"roots_with_all_required_files={roots_with_all_files}",
        f"present_required_files={present_required_files}",
        f"total_required_files={total_required_files}",
        f"source_rows_present={source_rows_present}",
        f"valid_source_owned_normal_controls_found=0",
        f"same_exhibit_flip_approval=false",
        f"canonical_merge_allowed={str(canonical_merge_allowed).lower()}",
        f"verifier_rerun_allowed={str(verifier_rerun_allowed).lower()}",
        f"downstream_chain_rerun_allowed={str(downstream_chain_rerun_allowed).lower()}",
        "accepted_rows_added=0",
        "new_confidence_gate=false",
        "strict_full_objective_achieved=false",
        "update_goal=false",
        "runtime_code_changed=false",
        "shared_intake_mutated=false",
        "owner_export_root_mutated=false",
        "thresholds_relaxed=false",
        "raw_data_committed=false",
        "trade_usable=false",
    ]
    (CHECKS / "source_intake_root_poll_after_contact_route_v1_assertions.out").write_text(
        "\n".join(assertions) + "\n"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
