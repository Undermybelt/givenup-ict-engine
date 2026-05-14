#!/usr/bin/env python3
"""Build sendable owner-export request drafts from the current R6 cell matrix."""

from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path


RUN_ID = "20260512T005913-codex-r6-owner-export-sendable-requests-v3"
BASE = Path("docs/experiments/actionable-regime-confidence/runs")
SOURCE_RUN = BASE / "20260512T005126-codex-r6-owner-export-request-bundle-v2"
SOURCE_DIR = SOURCE_RUN / "r6-owner-export-request-bundle-v2"
SOURCE_CSV = SOURCE_DIR / "r6_oystacher_required_cell_owner_export_request_v2.csv"
OUT_ROOT = BASE / RUN_ID
OUT_DIR = OUT_ROOT / "r6-owner-export-sendable-requests-v3"
CHECK_DIR = OUT_ROOT / "checks"

DELIVERY_ROOT = "/tmp/ict-engine-board-a-r6-owner-export-v1"
REQUIRED_FILES = [
    "positive_spoofing_layering_rows.csv",
    "matched_negative_normal_activity_rows.csv",
    "provenance_manifest.json",
]

OFFICIAL_ROUTES = [
    {
        "owner": "CME Group",
        "route": "CME DataMine historical data",
        "url": "https://www.cmegroup.com/market-data/datamine-historical-data/index.html",
        "evidence": "DataMine lists historical Futures & Options datasets including Market by Order and provides data-sales ordering contact.",
        "request_use": "Primary path for CME, NYMEX, COMEX, and CME Globex historical order-lifecycle/depth export request.",
    },
    {
        "owner": "CME Group",
        "route": "CME Market Depth Files FAQ",
        "url": "https://www.cmegroup.com/market-data/files/cme-group-market-depth-faq.pdf",
        "evidence": "Market Depth FAQ describes FIX/FAST market-depth files, order-book reconstruction, millisecond timestamps, and product-dependent start dates.",
        "request_use": "Use to ask CME Data Sales to confirm 2011-2013 product coverage for CL, NG, HG, and ES cells.",
    },
    {
        "owner": "Cboe/CFE",
        "route": "Cboe U.S. Futures historical data",
        "url": "https://www.cboe.com/markets/us/futures/market-statistics/historical-data/oof/",
        "evidence": "Cboe's public CFE page exposes daily volume/open-interest history and points to Cboe DataShop for custom VIX futures historical data.",
        "request_use": "Public history is not enough; use this to route the 2014 VIX/CFE depth/order-lifecycle request to DataShop/support.",
    },
    {
        "owner": "Cboe/CFE",
        "route": "Cboe Market Data Services U.S. Futures",
        "url": "https://res.cboe.com/market_data_services/us/futures/",
        "evidence": "Cboe U.S. Futures market-data services describe VIX futures data with Top-of-Book and Depth-of-Book feeds and support contacts.",
        "request_use": "Use to request CFE/VIX futures depth/order-lifecycle availability and licensing for historical 2014 controls.",
    },
]


def read_cells() -> list[dict[str, str]]:
    with SOURCE_CSV.open(newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def md_table(rows: list[dict[str, str]], fields: list[str]) -> str:
    lines = ["| " + " | ".join(fields) + " |", "| " + " | ".join(["---"] * len(fields)) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(str(row.get(field, "")).replace("|", "/") for field in fields) + " |")
    return "\n".join(lines)


def owner_request(owner: str, rows: list[dict[str, str]], official_routes: list[dict[str, str]]) -> str:
    fields = [
        "axis",
        "bucket",
        "positive_spoof_support",
        "invalid_flip_candidate_support",
        "required_valid_normal_control_support",
        "date_fit_status",
        "requested_product_scope",
        "requested_date_scope",
    ]
    source_lines = "\n".join(f"- {r['route']}: {r['url']}" for r in official_routes)
    return f"""# {owner} R6 Oystacher Normal-Control Export Request v3

Purpose: request source-owned normal/non-manipulation order-lifecycle controls for the Board A R6 Oystacher verifier. This is a request draft only; it is not approval, not acquired data, and not a canonical merge.

Delivery root after approval/export: `{DELIVERY_ROOT}`

Required verifier-native files:
- `{REQUIRED_FILES[0]}`
- `{REQUIRED_FILES[1]}`
- `{REQUIRED_FILES[2]}`

Controls must be source-owned normal/non-manipulation rows. Do not use same-exhibit `FLIP` rows unless the user/board explicitly approves that exception.

Official route references:
{source_lines}

Requested cells:

{md_table(rows, fields)}

Required row fields:
- label
- source_report
- source_section
- trade_date
- symbol
- venue_or_market_center
- participant_type_code
- participant_identifier
- side
- earliest_order_received_time
- latest_order_received_time
- order_count
- total_order_quantity
- activity_description
- matched_negative_group_id
- session_bucket
- source_row_id

Post-delivery chain:
1. Place owner-approved files under `{DELIVERY_ROOT}`.
2. Rerun direct verifier and split calibration under the shared lock.
3. Only if accepted, rerun provider, Auto-Quant, pre-Bayes/BBN, CatBoost/path-ranking, and execution-tree readback.
4. Keep R5/R3/source-label roots blocked until their exact source-owned inputs exist.
"""


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)
    rows = read_cells()
    by_owner = {"CME Group": [], "Cboe/CFE": []}
    for row in rows:
        owner = row["owner"]
        if owner in by_owner:
            by_owner[owner].append(row)

    route_fields = ["owner", "route", "url", "evidence", "request_use"]
    write_csv(OUT_DIR / "official_route_sources_v3.csv", OFFICIAL_ROUTES, route_fields)

    for owner, owner_rows in by_owner.items():
        owner_slug = "cme_group" if owner == "CME Group" else "cboe_cfe"
        official = [route for route in OFFICIAL_ROUTES if route["owner"] == owner]
        (OUT_DIR / f"{owner_slug}_owner_export_request_v3.md").write_text(
            owner_request(owner, owner_rows, official)
        )

    counts = Counter(row["owner"] for row in rows)
    summary = {
        "run_id": RUN_ID,
        "source_request_bundle": str(SOURCE_RUN),
        "gate_result": "r6_owner_export_sendable_requests_v3=sendable_requests_created_controls_not_acquired_no_merge",
        "required_oystacher_control_cells": len(rows),
        "cme_group_cells": counts["CME Group"],
        "cboe_cfe_cells": counts["Cboe/CFE"],
        "required_support_per_cell": 73,
        "delivery_root": DELIVERY_ROOT,
        "required_files": REQUIRED_FILES,
        "official_route_sources": OFFICIAL_ROUTES,
        "valid_source_owned_normal_controls_found": 0,
        "canonical_merge_allowed": False,
        "downstream_chain_rerun_allowed": False,
        "accepted_rows_added": 0,
        "new_confidence_gate": False,
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "shared_intake_mutated": False,
        "owner_export_root_mutated": False,
        "raw_data_committed": False,
        "external_requests_sent": False,
    }
    (OUT_DIR / "r6_owner_export_sendable_requests_v3.json").write_text(json.dumps(summary, indent=2) + "\n")
    (OUT_DIR / "r6_owner_export_sendable_requests_v3.md").write_text(
        f"""# R6 Owner Export Sendable Requests v3

- Run id: `{RUN_ID}`.
- Gate result: `{summary['gate_result']}`.
- Source matrix: `{SOURCE_CSV}`.
- Required Oystacher normal-control cells: `{len(rows)}`.
- CME Group cells: `{counts['CME Group']}`.
- Cboe/CFE cells: `{counts['Cboe/CFE']}`.
- Required support per cell: `73` valid source-owned normal controls.
- Delivery root after approval/export: `{DELIVERY_ROOT}`.
- Required verifier-native files: `{', '.join(REQUIRED_FILES)}`.
- Valid source-owned normal controls found now: `0`.
- Canonical merge allowed now: `false`; downstream rerun allowed now: `false`.
- Accepted rows added: `0`; strict full objective achieved: false. `update_goal=false`.
- Runtime code changed: false. Shared intake mutated: false. Owner-export root mutated: false. Raw data committed: false. External requests sent: false.

## Created Request Drafts

- CME Group request: `docs/experiments/actionable-regime-confidence/runs/{RUN_ID}/r6-owner-export-sendable-requests-v3/cme_group_owner_export_request_v3.md`
- Cboe/CFE request: `docs/experiments/actionable-regime-confidence/runs/{RUN_ID}/r6-owner-export-sendable-requests-v3/cboe_cfe_owner_export_request_v3.md`
- Official route sources: `docs/experiments/actionable-regime-confidence/runs/{RUN_ID}/r6-owner-export-sendable-requests-v3/official_route_sources_v3.csv`

## Decision

This packet makes the active V71 owner-export next action sendable. It does not satisfy the source/control gate by itself. Do not populate `{DELIVERY_ROOT}` or rerun the full chain until verifier-native controls and provenance arrive, or until explicit same-exhibit `FLIP` approval is recorded.
"""
    )

    assertions = [
        f"run_id={RUN_ID}",
        f"gate_result={summary['gate_result']}",
        f"required_cells={len(rows)}",
        f"cme_group_cells={counts['CME Group']}",
        f"cboe_cfe_cells={counts['Cboe/CFE']}",
        "valid_source_owned_normal_controls_found=0",
        "canonical_merge_allowed=false",
        "downstream_chain_rerun_allowed=false",
        "accepted_rows_added=0",
        "new_confidence_gate=false",
        "strict_full_objective_achieved=false",
        "update_goal=false",
        "runtime_code_changed=false",
        "shared_intake_mutated=false",
        "owner_export_root_mutated=false",
        "external_requests_sent=false",
    ]
    (CHECK_DIR / "r6_owner_export_sendable_requests_v3_assertions.out").write_text("\n".join(assertions) + "\n")


if __name__ == "__main__":
    main()
