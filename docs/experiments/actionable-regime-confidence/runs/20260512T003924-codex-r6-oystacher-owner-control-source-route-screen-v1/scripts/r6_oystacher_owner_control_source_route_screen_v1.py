#!/usr/bin/env python3
"""Build a source-route screen for Oystacher independent normal controls.

This is a no-mutation planning artifact: it maps the 17 required control cells
from the active R6 Oystacher contract to official/source-owner acquisition
routes. It does not approve FLIP controls, acquire rows, or mutate /tmp intake
roots.
"""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path


RUN_ID = "20260512T003924-codex-r6-oystacher-owner-control-source-route-screen-v1"
RUN_ROOT = Path(
    "docs/experiments/actionable-regime-confidence/runs"
) / RUN_ID
OUT_DIR = RUN_ROOT / "r6-oystacher-owner-control-source-route-screen"
CHECK_DIR = RUN_ROOT / "checks"
REQUIRED_CELLS_CSV = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260512T003627-codex-r6-oystacher-control-contract-request-v1/"
    "r6-oystacher-control-contract-request/"
    "r6_oystacher_required_normal_control_cells_v1.csv"
)


OFFICIAL_SOURCES = [
    {
        "source_id": "cme_datamine_market_depth_fixfast",
        "owner": "CME Group",
        "url": "https://www.cmegroup.com/market-data/files/cme-group-market-depth-faq.pdf",
        "evidence": (
            "CME DataMine Market Depth files contain market data messages to "
            "recreate Globex futures order books, with millisecond timestamps; "
            "product start dates vary by product."
        ),
        "route_status": "official_route_identified_access_required",
    },
    {
        "source_id": "cme_market_depth_google_analytics_hub",
        "owner": "CME Group",
        "url": "https://www.cmegroup.com/market-data/connect-data/cloud-mdp.html",
        "evidence": (
            "CME describes historical market depth in Google Analytics Hub as "
            "including order book, statistics, and quotes across energy, "
            "metals, equity index, and other asset classes, dating back to 2014."
        ),
        "route_status": "official_route_identified_date_limited_for_2011_2013_cells",
    },
    {
        "source_id": "cboe_cfe_datashop_custom_vix_futures",
        "owner": "Cboe",
        "url": "https://www.cboe.com/markets/us/futures/market-statistics/historical-data/oof/",
        "evidence": (
            "Cboe points users to Cboe DataShop for custom VIX options and "
            "futures historical data on demand, with CFE daily volume/open "
            "interest available from 2004 to current."
        ),
        "route_status": "official_route_identified_detail_level_must_be_confirmed",
    },
    {
        "source_id": "cboe_cfe_depth_of_book_market_data",
        "owner": "Cboe",
        "url": "https://www.cboe.com/market_data_services/us/futures/",
        "evidence": (
            "Cboe Futures Exchange market data is available with Top-of-Book "
            "and Depth-of-Book feeds; historical/licensed retrieval must be "
            "confirmed with Cboe market data support."
        ),
        "route_status": "official_route_identified_access_required",
    },
]


def read_required_cells() -> list[dict[str, str]]:
    with REQUIRED_CELLS_CSV.open(newline="") as handle:
        return list(csv.DictReader(handle))


def route_for_cell(cell: dict[str, str]) -> dict[str, str]:
    axis = cell["axis"]
    bucket = cell["bucket"]
    cme_buckets = {
        "energy",
        "equity_index",
        "metals",
        "CME Globex",
        "COMEX/CME Globex",
        "NYMEX/CME Globex",
        "Crude Oil futures",
        "E-mini S&P 500 futures",
        "High-Grade Copper futures",
        "Natural Gas futures",
    }
    cboe_buckets = {
        "volatility_index",
        "CFE/CBOE Futures Exchange",
        "VIX futures",
    }
    if bucket in cme_buckets:
        route = "cme_datamine_market_depth_fixfast"
        coverage = "candidate_route_covers_cell_access_and_export_required"
        caveat = "Need licensed CME DataMine/market-depth export and owner-approved normal window selection."
    elif bucket in cboe_buckets:
        route = "cboe_cfe_depth_of_book_market_data"
        coverage = "candidate_route_covers_cell_access_and_detail_confirmation_required"
        caveat = "Need CFE depth/order-book export or explicit confirmation DataShop detail is enough."
    elif axis == "chronological_year":
        route = "mixed_cme_cboe_by_contract_dates"
        coverage = "candidate_routes_cover_year_but_2011_2013_cme_cloud_depth_may_be_limited"
        caveat = "Year cells require both CME and CFE exports; CME cloud depth starts 2014, DataMine product start dates must be confirmed for 2011-2013."
    else:
        route = "unmapped"
        coverage = "no_route_identified"
        caveat = "No official owner route mapped."
    return {
        "axis": axis,
        "bucket": bucket,
        "required_valid_normal_control_support": cell["required_valid_normal_control_support"],
        "valid_normal_control_support_observed": "0",
        "route_id": route,
        "route_coverage_status": coverage,
        "decision": "source_route_identified_controls_not_acquired",
        "caveat": caveat,
    }


def write_csv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)

    cells = read_required_cells()
    cell_routes = [route_for_cell(cell) for cell in cells]

    source_rows = [
        {
            "source_id": source["source_id"],
            "owner": source["owner"],
            "url": source["url"],
            "route_status": source["route_status"],
            "evidence": source["evidence"],
        }
        for source in OFFICIAL_SOURCES
    ]

    covered_cells = sum(
        1 for row in cell_routes if row["route_coverage_status"] != "no_route_identified"
    )
    summary = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "gate_result": (
            "r6_oystacher_owner_control_source_route_screen_v1="
            "official_source_routes_identified_controls_not_acquired"
        ),
        "required_cells": len(cells),
        "official_source_routes": len(source_rows),
        "cells_with_candidate_source_route": covered_cells,
        "valid_normal_controls_acquired": 0,
        "source_owned_normal_control_ready": False,
        "flip_control_approved": False,
        "canonical_merge_allowed": False,
        "downstream_chain_rerun": False,
        "accepted_rows_added": 0,
        "new_confidence_gate": False,
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "shared_intake_mutated": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "external_requests_sent": True,
        "trade_usable": False,
        "next_action": (
            "Use CME DataMine/market-depth exports for CME/NYMEX/COMEX/CME Globex "
            "cells and Cboe/CFE DataShop or depth-of-book exports for VIX/CFE cells; "
            "place source-owned normal controls under /tmp/ict-engine-board-a-r6-owner-export-v1 "
            "with provenance, or get explicit FLIP-control approval, then rerun the full chain."
        ),
        "official_sources": source_rows,
    }

    write_csv(
        OUT_DIR / "r6_oystacher_owner_control_source_routes_v1.csv",
        source_rows,
        ["source_id", "owner", "url", "route_status", "evidence"],
    )
    write_csv(
        OUT_DIR / "r6_oystacher_required_cell_source_routes_v1.csv",
        cell_routes,
        [
            "axis",
            "bucket",
            "required_valid_normal_control_support",
            "valid_normal_control_support_observed",
            "route_id",
            "route_coverage_status",
            "decision",
            "caveat",
        ],
    )

    request_md = OUT_DIR / "owner_normal_control_export_request_v1.md"
    request_md.write_text(
        "\n".join(
            [
                "# Owner Normal-Control Export Request v1",
                "",
                "Preferred branch: source-owned normal/non-manipulation controls.",
                "",
                "Required target root: `/tmp/ict-engine-board-a-r6-owner-export-v1`.",
                "",
                "Required files:",
                "- `matched_negative_normal_activity_rows.csv`",
                "- `provenance_manifest.json`",
                "",
                "Minimum support:",
                "- `73` valid source-owned normal controls for each of the 17 required cells.",
                "",
                "Source route:",
                "- CME/NYMEX/COMEX/CME Globex cells: CME DataMine Market Depth/FIX-FAST or licensed equivalent.",
                "- VIX/CFE cells: Cboe/CFE DataShop or Depth-of-Book licensed equivalent.",
                "",
                "Do not use same-exhibit `FLIP` rows as controls unless the explicit exception template is approved.",
                "",
            ]
        )
    )

    report = OUT_DIR / "r6_oystacher_owner_control_source_route_screen_v1.md"
    report.write_text(
        "\n".join(
            [
                "# R6 Oystacher Owner-Control Source Route Screen v1",
                "",
                f"- Run id: `{RUN_ID}`.",
                f"- Gate result: `{summary['gate_result']}`.",
                f"- Required cells: `{summary['required_cells']}`.",
                f"- Cells with candidate official source route: `{summary['cells_with_candidate_source_route']}`.",
                "- Valid source-owned normal controls acquired: `0`.",
                "- FLIP-as-control approved: `false`.",
                "- Canonical merge allowed: `false`.",
                "- Downstream provider/Auto-Quant/pre-Bayes/BBN/CatBoost/execution-tree rerun: `false`.",
                "- Accepted rows added: `0`; new confidence gate: `false`; strict full objective achieved: `false`; `update_goal=false`.",
                "- Runtime code changed: `false`; shared intake mutated: `false`; thresholds relaxed: `false`; raw data committed: `false`; trade usable: `false`.",
                "",
                "## Official Source Routes",
                "",
                "- CME route: CME DataMine Market Depth/FIX-FAST or cloud market-depth export for CME Globex, NYMEX, and COMEX cells. Use for crude oil, natural gas, high-grade copper, and E-mini S&P 500 normal controls; confirm product/date availability for 2011-2013 cells.",
                "- Cboe route: Cboe/CFE DataShop or CFE Depth-of-Book market data export for VIX futures normal controls; confirm historical depth/order-book detail and licensing.",
                "",
                "## Next",
                "",
                summary["next_action"],
                "",
                "Artifacts:",
                f"- JSON: `{OUT_DIR / 'r6_oystacher_owner_control_source_route_screen_v1.json'}`",
                f"- Source routes CSV: `{OUT_DIR / 'r6_oystacher_owner_control_source_routes_v1.csv'}`",
                f"- Cell route CSV: `{OUT_DIR / 'r6_oystacher_required_cell_source_routes_v1.csv'}`",
                f"- Export request: `{request_md}`",
                f"- Assertions: `{CHECK_DIR / 'r6_oystacher_owner_control_source_route_screen_v1_assertions.out'}`",
                "",
            ]
        )
    )

    (OUT_DIR / "r6_oystacher_owner_control_source_route_screen_v1.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n"
    )

    assertions = [
        ("required_cells_17", len(cells) == 17),
        ("candidate_routes_cover_17_cells", covered_cells == 17),
        ("controls_not_acquired", summary["valid_normal_controls_acquired"] == 0),
        ("flip_control_not_approved", summary["flip_control_approved"] is False),
        ("canonical_merge_false", summary["canonical_merge_allowed"] is False),
        ("downstream_rerun_false", summary["downstream_chain_rerun"] is False),
        ("accepted_rows_zero", summary["accepted_rows_added"] == 0),
        ("strict_full_objective_false", summary["strict_full_objective_achieved"] is False),
        ("update_goal_false", summary["update_goal"] is False),
    ]
    assertion_lines = [
        f"{name}={'PASS' if passed else 'FAIL'}" for name, passed in assertions
    ]
    (CHECK_DIR / "r6_oystacher_owner_control_source_route_screen_v1_assertions.out").write_text(
        "\n".join(assertion_lines) + "\n"
    )

    if not all(passed for _, passed in assertions):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
