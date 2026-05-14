#!/usr/bin/env python3
"""Create the R6 owner-export request package after public source exhaustion."""

from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


RUN_ID = "20260512T001636-codex-r6-owner-export-request-package-v1"
REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs" / RUN_ID
OUT = RUN_ROOT / "r6-owner-export-request-package"
CHECKS = RUN_ROOT / "checks"
BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"
SOURCE_SCAN = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs"
    / "20260512T001121-codex-r6-bulk-order-lifecycle-source-scan-v1"
    / "r6-bulk-order-lifecycle-source-scan/r6_bulk_order_lifecycle_source_scan_v1.json"
)
DEBT_AUDIT = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs"
    / "20260512T000801-codex-r6-exact-split-support-debt-audit-v1"
    / "r6-exact-split-support-debt-audit/r6_exact_split_support_debt_audit_v1.json"
)
GROUPED_DRYRUN = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs"
    / "20260512T001116-codex-r6-grouped-heldout-contract-dryrun-v1"
    / "r6-grouped-heldout-contract-dryrun/r6_grouped_heldout_contract_dryrun_v1.json"
)


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


def write_json(path: Path, payload: dict[str, Any]) -> None:
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
    missing = [rel(path) for path in [BOARD, SOURCE_SCAN, DEBT_AUDIT, GROUPED_DRYRUN] if not path.exists()]
    if missing:
        payload = {
            "run_id": RUN_ID,
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "status": "blocked",
            "reason": "missing_required_inputs",
            "missing_inputs": missing,
            "update_goal": False,
        }
        write_json(OUT / "r6_owner_export_request_package_v1.json", payload)
        return 2

    source_scan = json.loads(SOURCE_SCAN.read_text(encoding="utf-8"))
    debt = json.loads(DEBT_AUDIT.read_text(encoding="utf-8"))
    grouped = json.loads(GROUPED_DRYRUN.read_text(encoding="utf-8"))

    field_rows = [
        {"file": "direct_manipulation_positive_rows.csv", "field": "event_id", "required": True, "notes": "Stable unique positive event id."},
        {"file": "direct_manipulation_positive_rows.csv", "field": "species", "required": True, "notes": "One of spoofing_layering, quote_spoofing, quote_stuffing, pinging, bear_raid, painting_tape, social_text_pump_dump if available."},
        {"file": "direct_manipulation_positive_rows.csv", "field": "market_family", "required": True, "notes": "Equity index futures, metals, energy, agriculture, crypto, equities, FX, or venue-owned taxonomy."},
        {"file": "direct_manipulation_positive_rows.csv", "field": "symbol", "required": True, "notes": "Exact traded instrument or contract."},
        {"file": "direct_manipulation_positive_rows.csv", "field": "venue_or_market_center", "required": True, "notes": "Exact venue plus venue family if available."},
        {"file": "direct_manipulation_positive_rows.csv", "field": "event_start", "required": True, "notes": "Timestamp with timezone."},
        {"file": "direct_manipulation_positive_rows.csv", "field": "event_end", "required": True, "notes": "Timestamp with timezone."},
        {"file": "direct_manipulation_positive_rows.csv", "field": "positive_label", "required": True, "notes": "Source-owned manipulation label or owner-approved exception type."},
        {"file": "direct_manipulation_positive_rows.csv", "field": "matched_control_group_id", "required": True, "notes": "Joins to matched controls."},
        {"file": "direct_manipulation_positive_rows.csv", "field": "split_role", "required": True, "notes": "Predeclared train/calibration/test or export-native split id."},
        {"file": "direct_manipulation_positive_rows.csv", "field": "source_owner", "required": True, "notes": "FINRA, exchange, venue surveillance, CAT-like owner, or approved data owner."},
        {"file": "direct_manipulation_positive_rows.csv", "field": "source_dataset", "required": True, "notes": "Export/report identifier."},
        {"file": "direct_manipulation_positive_rows.csv", "field": "source_row_id", "required": True, "notes": "Owner row id."},
        {"file": "direct_manipulation_positive_rows.csv", "field": "provenance_hash", "required": True, "notes": "Hash over source row/provenance payload."},
        {"file": "direct_manipulation_matched_controls.csv", "field": "matched_control_group_id", "required": True, "notes": "Matches positive row control group."},
        {"file": "direct_manipulation_matched_controls.csv", "field": "control_row_id", "required": True, "notes": "Stable unique control id."},
        {"file": "direct_manipulation_matched_controls.csv", "field": "normal_label", "required": True, "notes": "Owner-approved normal/non-manipulation label or report-negative status."},
        {"file": "direct_manipulation_matched_controls.csv", "field": "matching_dimensions", "required": True, "notes": "Symbol/venue/session/market-family/time-window matching policy."},
        {"file": "direct_manipulation_provenance.json", "field": "owner_approval_reference", "required": True, "notes": "Evidence that export is owner-approved or source-owned."},
        {"file": "direct_manipulation_provenance.json", "field": "split_contract", "required": True, "notes": "Exact, market-family, or other approved heldout contract."},
    ]

    request_rows = [
        {
            "request_id": "r6_exact_contract_bulk_export",
            "target_source_class": "FINRA/venue-surveillance/CAT-like/exchange order-lifecycle export",
            "minimum_distribution": "At least 73 positives and 73 matched controls per accepted split cell; V59 exact-symbol debt is 2559 pairwise rows and exact-venue debt is 732 if current exact buckets remain mandatory.",
            "required_decision_before_use": "Owner approval and unchanged verifier/calibration rerun.",
            "acceptance_state": "request_only_not_acquired",
        },
        {
            "request_id": "r6_family_contract_export",
            "target_source_class": "Same owner classes, but grouped by approved market-family and venue-family contract",
            "minimum_distribution": "At least 73 positives and 73 matched controls in each approved family cell; current dry-run still fails, so existing rows are insufficient.",
            "required_decision_before_use": "Explicit owner/user approval of the grouped validation contract before acceptance rerun.",
            "acceptance_state": "request_only_not_approved",
        },
        {
            "request_id": "r6_species_completion_export",
            "target_source_class": "Owner-approved direct Manipulation species labels",
            "minimum_distribution": "Rows must cover missing quote_spoofing, quote_stuffing, pinging, bear_raid, painting_tape, and optionally social_text_pump_dump, each with matched controls and provenance.",
            "required_decision_before_use": "Species taxonomy and matching policy must be preserved in provenance.",
            "acceptance_state": "request_only_not_acquired",
        },
    ]

    payload = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "board_sha256_at_start": sha256(BOARD),
        "input_refs": {
            "source_scan": {"path": rel(SOURCE_SCAN), "gate_result": source_scan.get("gate_result")},
            "debt_audit": {"path": rel(DEBT_AUDIT), "gate_result": debt.get("decision", {}).get("gate_result")},
            "grouped_dryrun": {"path": rel(GROUPED_DRYRUN), "gate_result": grouped.get("decision", {}).get("gate_result")},
        },
        "intake_target_root": "/tmp/ict-engine-board-a-r6-owner-export-v1",
        "required_files": sorted({row["file"] for row in field_rows}),
        "field_schema_csv": rel(OUT / "r6_owner_export_request_fields_v1.csv"),
        "request_matrix_csv": rel(OUT / "r6_owner_export_request_matrix_v1.csv"),
        "decision": {
            "gate_result": "r6_owner_export_request_package_v1=request_package_ready_rows_not_acquired",
            "accepted_rows_added": 0,
            "new_confidence_gate": False,
            "strict_full_objective_achieved": False,
            "update_goal": False,
            "runtime_code_changed": False,
            "shared_intake_mutated": False,
            "thresholds_relaxed": False,
            "raw_data_committed": False,
            "external_requests_sent": False,
            "trade_usable": False,
        },
        "next_action": (
            "Place owner/user-approved R6 export files under /tmp/ict-engine-board-a-r6-owner-export-v1 "
            "or record explicit approval for a different split contract; then rerun direct verifier, "
            "split calibration, provider, Auto-Quant, pre-Bayes/BBN, CatBoost/path-ranking, and execution-tree readback."
        ),
    }

    write_csv(
        OUT / "r6_owner_export_request_fields_v1.csv",
        field_rows,
        ["file", "field", "required", "notes"],
    )
    write_csv(
        OUT / "r6_owner_export_request_matrix_v1.csv",
        request_rows,
        ["request_id", "target_source_class", "minimum_distribution", "required_decision_before_use", "acceptance_state"],
    )
    write_json(OUT / "r6_owner_export_request_package_v1.json", payload)

    request_md = f"""# R6 Owner Export Request Package v1

Target intake root: `/tmp/ict-engine-board-a-r6-owner-export-v1`

Required files:
- `direct_manipulation_positive_rows.csv`
- `direct_manipulation_matched_controls.csv`
- `direct_manipulation_provenance.json`

Minimum distribution:
- Exact contract unchanged: V59 says exact-symbol debt is `{debt.get("debt_summary", {}).get("exact_symbol_pairwise_debt_if_current_buckets_must_all_pass")}` pairwise rows and exact-venue debt is `{debt.get("debt_summary", {}).get("exact_venue_pairwise_debt_if_current_buckets_must_all_pass")}`.
- Family contract path: requires explicit owner/user approval first, and V60 still fails on current rows.
- Missing species must include matched controls and provenance, not labels inferred from raw order book data.

After files arrive:
1. Run unchanged direct intake verifier.
2. Rerun chronological/symbol/venue or approved-family split calibration.
3. Rerun provider, Auto-Quant, pre-Bayes/BBN, CatBoost/path-ranking, and execution-tree readback.
4. Write the result back to the same Board A markdown before claiming acceptance.
"""
    (OUT / "r6_owner_export_request_package_v1_request.md").write_text(request_md, encoding="utf-8")

    report = f"""# R6 Owner Export Request Package v1

- Run id: `{RUN_ID}`.
- Intake target root: `/tmp/ict-engine-board-a-r6-owner-export-v1`.
- Request matrix rows: `{len(request_rows)}`.
- Required field rows: `{len(field_rows)}`.
- Gate result: `{payload["decision"]["gate_result"]}`.
- Strict full objective achieved: `false`; `update_goal=false`.
- Runtime code changed: `false`; shared intake mutated: `false`; thresholds relaxed: `false`; raw data committed: `false`; external requests sent: `false`; trade usable: `false`.

## Artifacts

- JSON: `{rel(OUT / "r6_owner_export_request_package_v1.json")}`
- Request markdown: `{rel(OUT / "r6_owner_export_request_package_v1_request.md")}`
- Field schema CSV: `{rel(OUT / "r6_owner_export_request_fields_v1.csv")}`
- Request matrix CSV: `{rel(OUT / "r6_owner_export_request_matrix_v1.csv")}`

## Next

Place owner/user-approved R6 export files under `/tmp/ict-engine-board-a-r6-owner-export-v1` or record explicit approval for a different split contract; then rerun direct verifier, split calibration, provider, Auto-Quant, pre-Bayes/BBN, CatBoost/path-ranking, and execution-tree readback.
"""
    (OUT / "r6_owner_export_request_package_v1.md").write_text(report, encoding="utf-8")

    checks = [
        ("request_matrix_rows_3", len(request_rows) == 3),
        ("required_files_3", len(payload["required_files"]) == 3),
        ("rows_not_acquired", payload["decision"]["accepted_rows_added"] == 0),
        ("new_confidence_gate_false", payload["decision"]["new_confidence_gate"] is False),
        ("strict_full_objective_not_complete", payload["decision"]["strict_full_objective_achieved"] is False),
        ("update_goal_false", payload["decision"]["update_goal"] is False),
    ]
    (CHECKS / "r6_owner_export_request_package_v1_assertions.out").write_text(
        "".join(f"{name}={'PASS' if passed else 'FAIL'}\n" for name, passed in checks),
        encoding="utf-8",
    )
    return 0 if all(passed for _, passed in checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
