#!/usr/bin/env python3
"""Build an exact owner-export request bundle for R6 Oystacher normal controls."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[6]
RUN_ID = "20260512T005126-codex-r6-owner-export-request-bundle-v2"
RUN_ROOT = (
    REPO_ROOT
    / "docs/experiments/actionable-regime-confidence/runs"
    / RUN_ID
)
OUT_DIR = RUN_ROOT / "r6-owner-export-request-bundle-v2"
CHECK_DIR = RUN_ROOT / "checks"

BOARD_PATH = REPO_ROOT / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"
CONTROL_CELLS_CSV = (
    REPO_ROOT
    / "docs/experiments/actionable-regime-confidence/runs"
    / "20260512T003627-codex-r6-oystacher-control-contract-request-v1"
    / "r6-oystacher-control-contract-request/r6_oystacher_required_normal_control_cells_v1.csv"
)
ROUTE_FIT_CSV = (
    REPO_ROOT
    / "docs/experiments/actionable-regime-confidence/runs"
    / "20260512T004410-codex-r6-official-route-date-fit-check-v1"
    / "r6-official-route-date-fit-check/r6_official_route_date_fit_cells_v1.csv"
)
SOURCE_FIT_CSV = (
    REPO_ROOT
    / "docs/experiments/actionable-regime-confidence/runs"
    / "20260512T004410-codex-r6-official-route-date-fit-check-v1"
    / "r6-official-route-date-fit-check/r6_official_route_date_fit_sources_v1.csv"
)
TARGET_ROOT = Path("/tmp/ict-engine-board-a-r6-owner-export-v1")
VERIFIER = (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T151950-codex-direct-manipulation-row-intake-manifest-v1/"
    "direct-manipulation-intake/direct_manipulation_row_intake_verifier_v1.py"
)

CSV_FIELDS = [
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


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def route_owner(route: str) -> str:
    if route.startswith("cboe") or "cboe" in route:
        return "Cboe/CFE"
    return "CME Group"


def requested_scope(row: dict[str, str]) -> str:
    axis = row["axis"]
    bucket = row["bucket"]
    if axis == "symbol_exact":
        return bucket
    if axis == "venue_exact":
        return f"all Oystacher symbols on {bucket}"
    if axis == "contract_family":
        return f"all Oystacher {bucket} contract-family symbols"
    if axis == "chronological_year":
        return f"all Oystacher required symbols active in {bucket}"
    return bucket


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)

    board_text = BOARD_PATH.read_text(encoding="utf-8")
    board_hash = sha256_text(board_text)
    control_rows = read_csv(CONTROL_CELLS_CSV)
    route_rows = read_csv(ROUTE_FIT_CSV)
    source_rows = read_csv(SOURCE_FIT_CSV)
    route_by_cell = {(r["axis"], r["bucket"]): r for r in route_rows}

    request_rows: list[dict[str, str]] = []
    for row in control_rows:
        route = route_by_cell[(row["axis"], row["bucket"])]
        owner = route_owner(route["official_route"])
        request_rows.append(
            {
                "axis": row["axis"],
                "bucket": row["bucket"],
                "positive_spoof_support": row["positive_spoof_support"],
                "invalid_flip_candidate_support": row["invalid_flip_candidate_support"],
                "required_valid_normal_control_support": row["required_valid_normal_control_support"],
                "owner": owner,
                "official_route": route["official_route"],
                "date_fit_status": route["date_fit_status"],
                "detail_fit_status": route["detail_fit_status"],
                "requested_product_scope": requested_scope(row),
                "requested_date_scope": (
                    "2011-2014 Oystacher Exhibit A date coverage; exact rows must map to the "
                    "requested axis/bucket and be outside same-exhibit FLIP promotion unless approved"
                ),
                "requested_detail": (
                    "source-owned normal/non-manipulation order-lifecycle rows with order/trade "
                    "timestamps, side, product/contract, venue, order count, quantity, and provenance"
                ),
                "delivery_file": str(TARGET_ROOT / "matched_negative_normal_activity_rows.csv"),
                "decision": "export_required_controls_not_acquired",
            }
        )

    schema_rows = [
        {
            "field": field,
            "required": "true",
            "control_value_rule": (
                "must be matched_negative_normal_activity"
                if field == "label"
                else "source-owned export value; no same-exhibit FLIP controls unless explicitly approved"
            ),
        }
        for field in CSV_FIELDS
    ]

    provenance_rows = [
        {"key": "source_owner", "required": "true", "rule": "CME Group or Cboe/CFE"},
        {"key": "licensed_export_reference", "required": "true", "rule": "invoice/order/ticket/export id or owner approval reference"},
        {"key": "raw_file_sha256", "required": "true", "rule": "hash of raw export kept outside repo, usually under /tmp"},
        {"key": "field_mapping", "required": "true", "rule": "mapping from owner columns to verifier-native CSV fields"},
        {"key": "normal_control_basis", "required": "true", "rule": "why rows are normal/non-manipulation controls, not Exhibit A FLIP rows"},
        {"key": "license_constraints", "required": "true", "rule": "state whether raw market data can be committed; default false"},
    ]

    commands = [
        {
            "step": "1",
            "name": "place_owner_export_files",
            "command_or_check": (
                f"write {TARGET_ROOT}/matched_negative_normal_activity_rows.csv and "
                f"{TARGET_ROOT}/provenance_manifest.json from licensed owner export"
            ),
            "requires_prior_approval": "true",
            "allowed_now": "false",
        },
        {
            "step": "2",
            "name": "copy_isolated_oystacher_positives_under_lock",
            "command_or_check": (
                f"copy isolated positive_spoofing_layering_rows.csv into {TARGET_ROOT} only "
                "after source/control policy approval"
            ),
            "requires_prior_approval": "true",
            "allowed_now": "false",
        },
        {
            "step": "3",
            "name": "direct_verifier",
            "command_or_check": f"python3 {VERIFIER} --intake-root {TARGET_ROOT}",
            "requires_prior_approval": "true",
            "allowed_now": "false",
        },
        {
            "step": "4",
            "name": "downstream_chain",
            "command_or_check": (
                "direct verifier -> split calibration -> provider status -> Auto-Quant -> "
                "Pre-Bayes/BBN -> CatBoost/path-ranking -> execution-tree readback"
            ),
            "requires_prior_approval": "true",
            "allowed_now": "false",
        },
    ]

    def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
        with path.open("w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)

    request_csv = OUT_DIR / "r6_oystacher_required_cell_owner_export_request_v2.csv"
    schema_csv = OUT_DIR / "r6_oystacher_verifier_native_control_schema_v2.csv"
    provenance_csv = OUT_DIR / "r6_oystacher_provenance_manifest_requirements_v2.csv"
    chain_csv = OUT_DIR / "r6_oystacher_post_export_chain_v2.csv"
    write_csv(request_csv, request_rows)
    write_csv(schema_csv, schema_rows)
    write_csv(provenance_csv, provenance_rows)
    write_csv(chain_csv, commands)

    summary = {
        "run_id": RUN_ID,
        "board_file_sha256_before_writeback": board_hash,
        "gate_result": "r6_owner_export_request_bundle_v2=request_ready_controls_not_acquired_no_merge",
        "source_control_branch": "source_owned_normal_controls",
        "required_cells": len(request_rows),
        "cells_with_owner_route": len([r for r in request_rows if r["official_route"]]),
        "cme_cells": len([r for r in request_rows if r["owner"] == "CME Group"]),
        "cboe_cfe_cells": len([r for r in request_rows if r["owner"] == "Cboe/CFE"]),
        "required_support_per_cell": 73,
        "valid_source_owned_normal_controls_found": 0,
        "owner_export_root": str(TARGET_ROOT),
        "required_delivery_files": [
            str(TARGET_ROOT / "positive_spoofing_layering_rows.csv"),
            str(TARGET_ROOT / "matched_negative_normal_activity_rows.csv"),
            str(TARGET_ROOT / "provenance_manifest.json"),
        ],
        "csv_fields": CSV_FIELDS,
        "official_sources_reused": source_rows,
        "canonical_merge_allowed": False,
        "downstream_chain_rerun_allowed": False,
        "accepted_rows_added": 0,
        "new_confidence_gate": False,
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "shared_intake_mutated": False,
        "owner_export_root_mutated": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "external_requests_sent": False,
        "trade_usable": False,
        "next_action": (
            "Send the cell-level request to CME DataMine/FIX-FAST/Market by Order or licensed equivalent "
            "for CME/NYMEX/COMEX/CME Globex cells, and to Cboe/CFE DataShop or market-data support for "
            "the 2014 VIX/CFE depth/order-lifecycle cell. Only after verifier-native controls and provenance "
            "arrive should the owner-export root be populated and the full chain rerun."
        ),
    }
    json_path = OUT_DIR / "r6_owner_export_request_bundle_v2.json"
    json_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    report = [
        "# R6 Owner Export Request Bundle v2",
        "",
        f"- Run id: `{RUN_ID}`.",
        f"- Gate result: `{summary['gate_result']}`.",
        f"- Required Oystacher normal-control cells: `{summary['required_cells']}`.",
        f"- Cells with owner route: `{summary['cells_with_owner_route']}`.",
        f"- CME Group cells: `{summary['cme_cells']}`; Cboe/CFE cells: `{summary['cboe_cfe_cells']}`.",
        f"- Required support per cell: `{summary['required_support_per_cell']}` valid source-owned normal controls.",
        "- Delivery root: `/tmp/ict-engine-board-a-r6-owner-export-v1`.",
        "- Required verifier-native files: `positive_spoofing_layering_rows.csv`, `matched_negative_normal_activity_rows.csv`, `provenance_manifest.json`.",
        "- Valid source-owned normal controls found now: `0`.",
        "- Canonical merge allowed now: `false`; downstream rerun allowed now: `false`.",
        "- Accepted rows added: `0`; strict full objective achieved: false. `update_goal=false`.",
        "- Runtime code changed: false. Shared intake mutated: false. Owner-export root mutated: false. Raw data committed: false. External requests sent: false.",
        "",
        "## What To Request",
        "",
        "- CME/NYMEX/COMEX/CME Globex cells: CME DataMine/FIX-FAST/Market by Order or licensed equivalent with 2011-2013 product/date coverage confirmation.",
        "- VIX/CFE cell: Cboe/CFE DataShop or market-data support export that explicitly covers 2014 historical depth/order-lifecycle rows.",
        "- Every delivered row must be a source-owned normal/non-manipulation control row and must not be same-exhibit `FLIP` unless the explicit exception is approved.",
        "",
        "## Artifacts",
        f"- JSON: `{json_path.relative_to(REPO_ROOT)}`",
        f"- Cell request CSV: `{request_csv.relative_to(REPO_ROOT)}`",
        f"- Verifier-native schema CSV: `{schema_csv.relative_to(REPO_ROOT)}`",
        f"- Provenance requirements CSV: `{provenance_csv.relative_to(REPO_ROOT)}`",
        f"- Post-export chain CSV: `{chain_csv.relative_to(REPO_ROOT)}`",
        f"- Assertions: `{(CHECK_DIR / 'r6_owner_export_request_bundle_v2_assertions.out').relative_to(REPO_ROOT)}`",
        "",
        "## Next",
        summary["next_action"],
    ]
    report_path = OUT_DIR / "r6_owner_export_request_bundle_v2.md"
    report_path.write_text("\n".join(report) + "\n", encoding="utf-8")

    assertions = [
        f"run_id={RUN_ID}",
        "gate_result=" + summary["gate_result"],
        f"required_cells={summary['required_cells']}",
        f"cells_with_owner_route={summary['cells_with_owner_route']}",
        f"cme_cells={summary['cme_cells']}",
        f"cboe_cfe_cells={summary['cboe_cfe_cells']}",
        f"required_support_per_cell={summary['required_support_per_cell']}",
        f"valid_source_owned_normal_controls_found={summary['valid_source_owned_normal_controls_found']}",
        f"canonical_merge_allowed={str(summary['canonical_merge_allowed']).lower()}",
        f"downstream_chain_rerun_allowed={str(summary['downstream_chain_rerun_allowed']).lower()}",
        f"accepted_rows_added={summary['accepted_rows_added']}",
        f"new_confidence_gate={str(summary['new_confidence_gate']).lower()}",
        f"strict_full_objective_achieved={str(summary['strict_full_objective_achieved']).lower()}",
        f"update_goal={str(summary['update_goal']).lower()}",
        f"runtime_code_changed={str(summary['runtime_code_changed']).lower()}",
        f"shared_intake_mutated={str(summary['shared_intake_mutated']).lower()}",
        f"owner_export_root_mutated={str(summary['owner_export_root_mutated']).lower()}",
    ]
    (CHECK_DIR / "r6_owner_export_request_bundle_v2_assertions.out").write_text(
        "\n".join(assertions) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
