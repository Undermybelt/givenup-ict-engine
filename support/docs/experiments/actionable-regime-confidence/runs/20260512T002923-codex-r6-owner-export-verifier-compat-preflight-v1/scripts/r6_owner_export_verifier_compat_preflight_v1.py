#!/usr/bin/env python3
"""Preflight V62 owner-export fields against the unchanged direct verifier."""

from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


RUN_ID = "20260512T002923-codex-r6-owner-export-verifier-compat-preflight-v1"
RUN_ROOT = Path("docs/experiments/actionable-regime-confidence/runs") / RUN_ID
ARTIFACT_DIR = RUN_ROOT / "r6-owner-export-verifier-compat-preflight"
CHECK_DIR = RUN_ROOT / "checks"

BOARD_PATH = Path("docs/plans/2026-05-10-actionable-regime-confidence-todo.md")
REQUEST_ROOT = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260512T001636-codex-r6-owner-export-request-package-v1/"
    "r6-owner-export-request-package"
)
REQUEST_FIELDS_CSV = REQUEST_ROOT / "r6_owner_export_request_fields_v1.csv"
REQUEST_MATRIX_CSV = REQUEST_ROOT / "r6_owner_export_request_matrix_v1.csv"
OWNER_EXPORT_TARGET = Path("/tmp/ict-engine-board-a-r6-owner-export-v1")

VERIFIER_POSITIVE_FILE = "positive_spoofing_layering_rows.csv"
VERIFIER_NEGATIVE_FILE = "matched_negative_normal_activity_rows.csv"
VERIFIER_PROVENANCE_FILE = "provenance_manifest.json"

VERIFIER_REQUIRED_FIELDS = [
    "label",
    "source_report",
    "source_section",
    "trade_date",
    "symbol",
    "venue_or_market_center",
    "participant_type_code",
    "participant_identifier",
    "side",
    "earliest_order_received_time",
    "latest_order_received_time",
    "order_count",
    "total_order_quantity",
    "activity_description",
    "matched_negative_group_id",
    "session_bucket",
    "source_row_id",
]

REQUEST_TO_VERIFIER_FIELD_MAP = {
    "label": ["positive_label", "normal_label"],
    "source_report": ["source_dataset", "source_owner"],
    "source_section": [],
    "trade_date": ["event_start"],
    "symbol": ["symbol"],
    "venue_or_market_center": ["venue_or_market_center"],
    "participant_type_code": [],
    "participant_identifier": [],
    "side": [],
    "earliest_order_received_time": ["event_start"],
    "latest_order_received_time": ["event_end"],
    "order_count": [],
    "total_order_quantity": [],
    "activity_description": ["species", "matching_dimensions"],
    "matched_negative_group_id": ["matched_control_group_id"],
    "session_bucket": ["split_role"],
    "source_row_id": ["source_row_id", "control_row_id"],
}


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_request_fields(path: Path) -> dict[str, set[str]]:
    by_file: dict[str, set[str]] = {}
    with path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            by_file.setdefault(row["file"], set()).add(row["field"])
    return by_file


def read_request_matrix(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def mappable_fields(source_fields: set[str]) -> dict[str, dict[str, object]]:
    rows = {}
    for verifier_field, candidates in REQUEST_TO_VERIFIER_FIELD_MAP.items():
        available = [candidate for candidate in candidates if candidate in source_fields]
        rows[verifier_field] = {
            "mappable": bool(available),
            "source_candidates": candidates,
            "available_sources": available,
        }
    return rows


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})


def main() -> int:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)

    fields_by_file = read_request_fields(REQUEST_FIELDS_CSV)
    matrix_rows = read_request_matrix(REQUEST_MATRIX_CSV)
    positive_fields = fields_by_file.get("direct_manipulation_positive_rows.csv", set())
    control_fields = fields_by_file.get("direct_manipulation_matched_controls.csv", set())
    provenance_fields = fields_by_file.get("direct_manipulation_provenance.json", set())

    positive_map = mappable_fields(positive_fields)
    control_map = mappable_fields(control_fields)
    positive_missing = [
        field for field, meta in positive_map.items() if not meta["mappable"]
    ]
    control_missing = [
        field for field, meta in control_map.items() if not meta["mappable"]
    ]

    compatibility_rows: list[dict[str, object]] = []
    for verifier_field in VERIFIER_REQUIRED_FIELDS:
        compatibility_rows.append(
            {
                "verifier_field": verifier_field,
                "positive_mappable": positive_map[verifier_field]["mappable"],
                "positive_available_sources": "|".join(
                    positive_map[verifier_field]["available_sources"]
                ),
                "control_mappable": control_map[verifier_field]["mappable"],
                "control_available_sources": "|".join(
                    control_map[verifier_field]["available_sources"]
                ),
                "adapter_decision": (
                    "ready"
                    if positive_map[verifier_field]["mappable"]
                    and control_map[verifier_field]["mappable"]
                    else "requires_augmented_export_field_or_explicit_transform"
                ),
            }
        )

    file_contract_rows = [
        {
            "contract_item": "requested_positive_file",
            "v62_request": "direct_manipulation_positive_rows.csv",
            "verifier_expected": VERIFIER_POSITIVE_FILE,
            "ready_without_copy_or_adapter": False,
        },
        {
            "contract_item": "requested_control_file",
            "v62_request": "direct_manipulation_matched_controls.csv",
            "verifier_expected": VERIFIER_NEGATIVE_FILE,
            "ready_without_copy_or_adapter": False,
        },
        {
            "contract_item": "requested_provenance_file",
            "v62_request": "direct_manipulation_provenance.json",
            "verifier_expected": VERIFIER_PROVENANCE_FILE,
            "ready_without_copy_or_adapter": False,
        },
    ]

    augmented_fields = [
        {
            "target_file": "direct_manipulation_positive_rows.csv",
            "required_for_verifier_compat": field,
            "reason": "missing_or_not_directly_mappable_from_v62_positive_request",
        }
        for field in positive_missing
    ] + [
        {
            "target_file": "direct_manipulation_matched_controls.csv",
            "required_for_verifier_compat": field,
            "reason": "missing_or_not_directly_mappable_from_v62_control_request",
        }
        for field in control_missing
    ]

    payload = {
        "accepted_rows_added": 0,
        "augmented_positive_field_count": len(positive_missing),
        "augmented_control_field_count": len(control_missing),
        "board_sha256_at_start": file_sha256(BOARD_PATH),
        "file_contract_ready_without_adapter": False,
        "gate_result": "r6_owner_export_verifier_compat_preflight_v1=adapter_required_and_augmented_fields_needed_before_verifier_rerun",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "new_confidence_gate": False,
        "next_action": (
            "Keep V62 active. When owner-approved export data arrives, provide verifier-native filenames "
            "or run an explicit adapter, and include the missing verifier fields before calibration."
        ),
        "owner_export_target": str(OWNER_EXPORT_TARGET),
        "owner_export_target_exists": OWNER_EXPORT_TARGET.exists(),
        "positive_missing_verifier_fields": positive_missing,
        "control_missing_verifier_fields": control_missing,
        "provenance_request_fields": sorted(provenance_fields),
        "raw_data_committed": False,
        "request_field_rows": sum(len(fields) for fields in fields_by_file.values()),
        "request_matrix_rows": len(matrix_rows),
        "run_id": RUN_ID,
        "runtime_code_changed": False,
        "shared_intake_mutated": False,
        "strict_full_objective_achieved": False,
        "thresholds_relaxed": False,
        "trade_usable": False,
        "update_goal": False,
    }

    json_path = ARTIFACT_DIR / "r6_owner_export_verifier_compat_preflight_v1.json"
    report_path = ARTIFACT_DIR / "r6_owner_export_verifier_compat_preflight_v1.md"
    compat_csv = ARTIFACT_DIR / "r6_owner_export_verifier_field_compat_v1.csv"
    augmented_csv = ARTIFACT_DIR / "r6_owner_export_augmented_fields_required_v1.csv"
    file_contract_csv = ARTIFACT_DIR / "r6_owner_export_file_contract_v1.csv"
    checklist_csv = ARTIFACT_DIR / "prompt_to_artifact_checklist_v1.csv"
    assertions_path = CHECK_DIR / "r6_owner_export_verifier_compat_preflight_v1_assertions.out"

    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_csv(
        compat_csv,
        compatibility_rows,
        [
            "verifier_field",
            "positive_mappable",
            "positive_available_sources",
            "control_mappable",
            "control_available_sources",
            "adapter_decision",
        ],
    )
    write_csv(
        augmented_csv,
        augmented_fields,
        ["target_file", "required_for_verifier_compat", "reason"],
    )
    write_csv(
        file_contract_csv,
        file_contract_rows,
        [
            "contract_item",
            "v62_request",
            "verifier_expected",
            "ready_without_copy_or_adapter",
        ],
    )
    write_csv(
        checklist_csv,
        [
            {
                "requirement": "each regime reaches 95 confidence",
                "status": "blocked",
                "evidence": "Board Current Cursor V62 plus prior strict gap audit",
                "notes": "Scoped consumer lanes pass, strict full objective still blocked.",
            },
            {
                "requirement": "validate across other markets and periods",
                "status": "blocked",
                "evidence": "V59 exact split debt and V60 grouped dry-run",
                "notes": "Exact and grouped split gates remain false.",
            },
            {
                "requirement": "personally operate provider/Auto-Quant/filter/BBN/CatBoost/execution-tree chain",
                "status": "deferred",
                "evidence": "V62 Current Cursor next_action",
                "notes": "Rerun only after owner-export files or explicit split-contract approval.",
            },
            {
                "requirement": "do not disturb multi-agent work",
                "status": "pass",
                "evidence": RUN_ID,
                "notes": "New unique run root; Current Cursor not edited.",
            },
            {
                "requirement": "owner-export files can feed unchanged verifier",
                "status": "blocked",
                "evidence": str(compat_csv),
                "notes": "Filename adapter plus augmented fields are required.",
            },
        ],
        ["requirement", "status", "evidence", "notes"],
    )

    report_lines = [
        "# R6 Owner Export Verifier Compatibility Preflight v1",
        "",
        f"- Run id: `{RUN_ID}`.",
        f"- V62 request field rows: `{payload['request_field_rows']}`; request matrix rows: `{payload['request_matrix_rows']}`.",
        "- File contract ready without adapter: `false`.",
        f"- Positive export fields missing for verifier compatibility: `{len(positive_missing)}`.",
        f"- Control export fields missing for verifier compatibility: `{len(control_missing)}`.",
        "- Owner-export target exists now: `" + str(OWNER_EXPORT_TARGET.exists()).lower() + "`.",
        "- Gate result: `r6_owner_export_verifier_compat_preflight_v1=adapter_required_and_augmented_fields_needed_before_verifier_rerun`.",
        "- Accepted rows added: `0`; new confidence gate: `false`; strict full objective achieved: false. `update_goal=false`.",
        "- Runtime code changed: false. Shared intake mutated: false. Thresholds relaxed: false. Raw data committed: false. External requests sent: false. Trade usable: false.",
        "",
        "## Interpretation",
        "",
        "- V62 solved the human request shape, but the unchanged direct verifier expects different filenames.",
        "- The V62 positive/control field request is also not sufficient for a lossless verifier-native intake: participant, side, quantity/count, source-section, activity, and session fields need to be provided or explicitly transformed.",
        "- This run does not change the active cursor. It makes the next real-row rerun deterministic: owner data must arrive either already verifier-native or with an explicit adapter plus augmented fields.",
        "",
        "## Artifacts",
        "",
        f"- JSON: `{json_path}`",
        f"- Field compatibility CSV: `{compat_csv}`",
        f"- Augmented required fields CSV: `{augmented_csv}`",
        f"- File contract CSV: `{file_contract_csv}`",
        f"- Prompt-to-artifact checklist: `{checklist_csv}`",
        f"- Assertions: `{assertions_path}`",
        "",
    ]
    report_path.write_text("\n".join(report_lines), encoding="utf-8")

    assertions = [
        "file_contract_ready_without_adapter=False",
        f"augmented_positive_field_count={len(positive_missing)}",
        f"augmented_control_field_count={len(control_missing)}",
        "accepted_rows_added=0",
        "strict_full_objective_achieved=False",
        "update_goal=False",
    ]
    assertions_path.write_text("\n".join(assertions) + "\n", encoding="utf-8")

    print(json.dumps({"run_id": RUN_ID, "json": str(json_path), "report": str(report_path)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
