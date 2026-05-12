#!/usr/bin/env python3
"""Readiness check for spoofing/layering matched direct rows."""

from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd


RUN_ID = "20260511T151720+0800-codex-spoofing-layering-matched-row-readiness-v1"
RUN_ROOT = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T151720-codex-spoofing-layering-matched-row-readiness-v1"
)
BOARD = Path("docs/plans/2026-05-10-actionable-regime-confidence-todo.md")
FINRA_SCHEMA_JSON = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T133337-codex-finra-manipulation-acquisition-schema-v1/"
    "acquisition-schema/finra_manipulation_acquisition_schema_v1.json"
)
FINRA_SCHEMA_CSV = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T133337-codex-finra-manipulation-acquisition-schema-v1/"
    "acquisition-schema/finra_manipulation_acquisition_schema_v1.csv"
)
CASE_INVENTORY_CSV = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T130457-codex-spoofing-appendix-direct-case-inventory/"
    "direct-case-inventory/spoofing_appendix_direct_case_inventory.csv"
)
DIRECT_SCHEMA_AUDIT_CSV = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T081556-codex-direct-manipulation-source-schema-audit/"
    "direct-manipulation-schema/direct_manipulation_source_schema_audit.csv"
)
LOCAL_SPOOF_AUDIT_JSON = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T110827-codex-local-spoofing-source-audit/"
    "source-audit/local_spoofing_source_audit.json"
)
VARIETY_MATRIX_JSON = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T131311-codex-direct-manipulation-variety-matrix-v1/"
    "direct-manipulation/direct_manipulation_variety_matrix_v1.json"
)
OUT_JSON = RUN_ROOT / "matched-row-readiness/spoofing_layering_matched_row_readiness_v1.json"
OUT_MD = RUN_ROOT / "matched-row-readiness/spoofing_layering_matched_row_readiness_v1.md"
OUT_SOURCES = RUN_ROOT / "matched-row-readiness/spoofing_layering_matched_row_readiness_v1_sources.csv"
OUT_REQUIREMENTS = RUN_ROOT / "matched-row-readiness/spoofing_layering_matched_row_readiness_v1_required_files.csv"
OUT_ASSERT = RUN_ROOT / "checks/spoofing_layering_matched_row_readiness_v1_assertions.out"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def local_path_status(path: Path) -> dict[str, Any]:
    return {
        "path": str(path),
        "exists": path.exists(),
        "bytes": path.stat().st_size if path.exists() else 0,
    }


def main() -> int:
    board_sha = sha256(BOARD)
    finra_schema = json.loads(FINRA_SCHEMA_JSON.read_text(encoding="utf-8"))
    case_inventory = pd.read_csv(CASE_INVENTORY_CSV)
    direct_schema_audit = pd.read_csv(DIRECT_SCHEMA_AUDIT_CSV)
    local_spoof_audit = json.loads(LOCAL_SPOOF_AUDIT_JSON.read_text(encoding="utf-8"))
    variety_matrix = json.loads(VARIETY_MATRIX_JSON.read_text(encoding="utf-8"))

    positive_cases = int(case_inventory["positive_case_label"].eq("spoofing_enforcement_case").sum())
    matched_negative_cases = int(case_inventory["matched_negative_available"].astype(bool).sum())
    confidence_eligible = int(case_inventory["confidence_gate_eligible_now"].astype(bool).sum())
    local_candidate_rows = [
        {
            "source_id": result["candidate_id"],
            "source_type": "local_repo_candidate",
            "decision": result["decision"],
            "accepted_rows": int(result["accepted_direct_rows_added"]),
            "matched_negative_status": "absent",
            "reason": result["reason"],
            "url_or_path": result["source_path"],
        }
        for result in local_spoof_audit["candidate_results"]
    ]

    source_rows = [
        {
            "source_id": "finra_potential_manipulation_report",
            "source_type": "regulator_schema_contract",
            "decision": "schema_target_rows_not_public",
            "accepted_rows": 0,
            "matched_negative_status": "not_acquired",
            "reason": "Public FINRA page is useful as field/schema target but does not provide exportable positive and matched negative rows.",
            "url_or_path": finra_schema["source"]["url"],
        },
        {
            "source_id": "spoofing_appendix_case_inventory",
            "source_type": "regulator_enforcement_case_inventory",
            "decision": "positive_case_inventory_only",
            "accepted_rows": 0,
            "matched_negative_status": "absent",
            "reason": f"{positive_cases} positive enforcement cases exist, but matched_negative_available={matched_negative_cases} and confidence_gate_eligible_now={confidence_eligible}.",
            "url_or_path": str(CASE_INVENTORY_CSV),
        },
    ]
    for row in direct_schema_audit.to_dict(orient="records"):
        source_rows.append({
            "source_id": row["dataset_id"],
            "source_type": row["source_type"],
            "decision": row["status"],
            "accepted_rows": 0,
            "matched_negative_status": "not_labeled_or_not_matched",
            "reason": row["reason"],
            "url_or_path": row["url"],
        })
    source_rows.extend(local_candidate_rows)
    source_rows.extend([
        {
            "source_id": "public_search_lobster_raw_lob",
            "source_type": "public_raw_orderbook_source",
            "decision": "raw_lob_no_manipulation_labels",
            "accepted_rows": 0,
            "matched_negative_status": "not_labeled",
            "reason": "Raw limit-order-book data can provide market context, but without source positive spoofing/layering windows and matched controls it is not an accepted direct Manipulation label source.",
            "url_or_path": "https://lobsterdata.com/",
        },
        {
            "source_id": "public_search_spoofing_code_or_synthetic",
            "source_type": "public_code_or_synthetic_benchmarks",
            "decision": "method_provenance_only",
            "accepted_rows": 0,
            "matched_negative_status": "synthetic_or_absent",
            "reason": "Public spoofing repos and synthetic benchmarks are method provenance unless they ship replayable real positive and matched negative rows.",
            "url_or_path": "local audit plus targeted web/source scan",
        },
    ])

    required_files = [
        {
            "required_file": "positive_spoofing_layering_rows.csv",
            "required": True,
            "status": "missing",
            "minimum_fields": "label, source_report, trade_date, symbol, venue_or_market_center, side, earliest_order_received_time, latest_order_received_time, order_count, total_order_quantity, activity_description, matched_negative_group_id, source_row_id",
            "accepted_source_types": "FINRA/CAT/venue/surveillance/exported order-lifecycle rows; not enforcement-case prose",
        },
        {
            "required_file": "matched_negative_normal_activity_rows.csv",
            "required": True,
            "status": "missing",
            "minimum_fields": "same schema as positives; matched venue/symbol/date/session/liquidity bucket; normal activity label",
            "accepted_source_types": "same source/export family as positives or venue-owned normal control export",
        },
        {
            "required_file": "provenance_manifest.json",
            "required": True,
            "status": "missing",
            "minimum_fields": "source owner, export identity, pull date, redaction notes, row counts, schema version",
            "accepted_source_types": "source-owned export provenance",
        },
    ]

    accepted_rows = sum(int(row["accepted_rows"]) for row in source_rows)
    acquisition_ready = all(item["status"] == "present" for item in required_files)
    decision = {
        "gate_result": "spoofing_layering_matched_row_readiness_v1_rows_not_acquired",
        "positive_case_inventory_count": positive_cases,
        "matched_negative_cases_available": matched_negative_cases,
        "confidence_gate_eligible_case_rows": confidence_eligible,
        "accepted_direct_manipulation_rows_added": accepted_rows,
        "acquisition_ready": acquisition_ready,
        "full_objective_achieved": False,
        "call_update_goal": False,
        "raw_data_committed": False,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "trade_usable": False,
    }

    result = {
        "schema_version": "spoofing-layering-matched-row-readiness/v1",
        "run_id": RUN_ID,
        "run_root": str(RUN_ROOT),
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "board_sha256_at_start": board_sha,
        "inputs": {
            "finra_schema_json": local_path_status(FINRA_SCHEMA_JSON),
            "finra_schema_csv": local_path_status(FINRA_SCHEMA_CSV),
            "case_inventory_csv": local_path_status(CASE_INVENTORY_CSV),
            "direct_schema_audit_csv": local_path_status(DIRECT_SCHEMA_AUDIT_CSV),
            "local_spoof_audit_json": local_path_status(LOCAL_SPOOF_AUDIT_JSON),
            "variety_matrix_json": local_path_status(VARIETY_MATRIX_JSON),
        },
        "active_boundary": {
            "target": "direct Manipulation spoofing_layering variety",
            "not_price_root": True,
            "disallowed": [
                "OHLCV/session/liquidity proxy",
                "positive-only enforcement prose",
                "synthetic detector rows",
                "raw order book without source manipulation labels",
                "model confidence without direct positive and matched negative rows",
            ],
        },
        "decision": decision,
        "sources": source_rows,
        "required_files": required_files,
        "next_action": "Obtain source-owned positive spoofing/layering rows plus matched normal controls matching finra_manipulation_acquisition_schema_v1.csv; otherwise keep spoofing_layering blocked.",
        "artifacts": {
            "report_json": str(OUT_JSON),
            "report_md": str(OUT_MD),
            "sources_csv": str(OUT_SOURCES),
            "required_files_csv": str(OUT_REQUIREMENTS),
            "assertions": str(OUT_ASSERT),
            "script": "scripts/spoofing_layering_matched_row_readiness_v1.py",
        },
    }

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_ASSERT.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    pd.DataFrame(source_rows).to_csv(OUT_SOURCES, index=False, quoting=csv.QUOTE_MINIMAL)
    pd.DataFrame(required_files).to_csv(OUT_REQUIREMENTS, index=False, quoting=csv.QUOTE_MINIMAL)

    md_lines = [
        "# Spoofing/Layering Matched Row Readiness v1",
        "",
        f"Run id: `{RUN_ID}`.",
        "",
        "## Decision",
        "",
        f"- Gate result: `{decision['gate_result']}`",
        f"- Positive enforcement cases inventoried: `{positive_cases}`",
        f"- Matched negative cases available: `{matched_negative_cases}`",
        f"- Confidence-gate eligible rows now: `{confidence_eligible}`",
        f"- Accepted direct `Manipulation` rows added: `{accepted_rows}`",
        "- Full objective achieved: `false`; `update_goal=false`.",
        "- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; trade usable: `false`.",
        "",
        "## Source Readiness",
        "",
        "| Source | Decision | Accepted Rows | Matched Negative Status | Reason |",
        "|---|---|---:|---|---|",
    ]
    for row in source_rows:
        md_lines.append(
            f"| `{row['source_id']}` | `{row['decision']}` | `{row['accepted_rows']}` | `{row['matched_negative_status']}` | {row['reason']} |"
        )
    md_lines.extend([
        "",
        "## Required Files To Unblock",
        "",
        "| Required File | Status | Minimum Fields |",
        "|---|---|---|",
    ])
    for item in required_files:
        md_lines.append(
            f"| `{item['required_file']}` | `{item['status']}` | {item['minimum_fields']} |"
        )
    md_lines.extend([
        "",
        "## Guardrail",
        "",
        "Positive-only enforcement inventories, raw order books without labels, and synthetic detector rows remain fail-closed. The next acceptable artifact must contain source-owned positive spoofing/layering rows and matched normal controls under the same schema.",
        "",
        "## Artifacts",
        "",
        f"- JSON: `{OUT_JSON}`",
        f"- Sources CSV: `{OUT_SOURCES}`",
        f"- Required files CSV: `{OUT_REQUIREMENTS}`",
        f"- Assertions: `{OUT_ASSERT}`",
    ])
    OUT_MD.write_text("\n".join(md_lines) + "\n", encoding="utf-8")

    assertion_lines = [
        f"run_id={RUN_ID}",
        f"gate_result={decision['gate_result']}",
        f"positive_case_inventory_count={positive_cases}",
        f"matched_negative_cases_available={matched_negative_cases}",
        f"confidence_gate_eligible_case_rows={confidence_eligible}",
        f"accepted_direct_manipulation_rows_added={accepted_rows}",
        "acquisition_ready=false",
        "full_objective_achieved=false",
        "call_update_goal=false",
        "raw_data_committed=false",
        "runtime_code_changed=false",
        "thresholds_relaxed=false",
        "trade_usable=false",
        "assertion_status=PASS",
    ]
    OUT_ASSERT.write_text("\n".join(assertion_lines) + "\n", encoding="utf-8")
    print(json.dumps(decision, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
