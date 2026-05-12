#!/usr/bin/env python3
"""Rebuild the R6 Oystacher source-owner control route artifact.

The shared board references this run root. This script is intentionally
non-mutating: it reconstructs the route map and negative disposition artifacts
without approving FLIP controls, copying intake files, or running downstream
promotion gates.
"""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path


RUN_ID = "20260512T004022-codex-r6-oystacher-source-owner-control-route-v1"
REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs" / RUN_ID
OUT = RUN_ROOT / "r6-oystacher-source-owner-control-route"
CHECKS = RUN_ROOT / "checks"

CONTROL_CELLS = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260512T003627-codex-r6-oystacher-control-contract-request-v1/"
    "r6-oystacher-control-contract-request/r6_oystacher_required_normal_control_cells_v1.csv"
)
POLICY_JSON = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260512T003358-codex-r6-oystacher-exhibit-a-policy-review-v1/"
    "r6-oystacher-exhibit-a-policy-review/r6_oystacher_exhibit_a_policy_review_v1.json"
)
NORMAL_PREFLIGHT_JSON = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260512T003443-codex-r6-oystacher-normal-control-availability-preflight-v1/"
    "r6-oystacher-normal-control-availability-preflight/"
    "r6_oystacher_normal_control_availability_preflight_v1.json"
)

SOURCE_ROUTES = [
    {
        "route_id": "cme_datamine_globex_order_book",
        "source_owner": "CME Group",
        "applies_to": "CME Globex; COMEX/CME Globex; NYMEX/CME Globex",
        "url": "https://www.cmegroup.com/market-data/datamine-historical-data/datamine-order-book.html",
        "route_type": "owner_licensed_historical_order_book_export",
        "current_status": "route_identified_rows_not_acquired",
    },
    {
        "route_id": "cme_datamine_landing",
        "source_owner": "CME Group",
        "applies_to": "CME Globex; COMEX/CME Globex; NYMEX/CME Globex",
        "url": "https://www.cmegroup.com/market-data/datamine-historical-data.html",
        "route_type": "owner_licensed_historical_data_entrypoint",
        "current_status": "route_identified_rows_not_acquired",
    },
    {
        "route_id": "cboe_datashop_entrypoint",
        "source_owner": "Cboe Global Markets",
        "applies_to": "CFE/CBOE Futures Exchange; VIX futures",
        "url": "https://datashop.cboe.com/",
        "route_type": "owner_or_affiliated_data_shop_export",
        "current_status": "route_identified_rows_not_acquired",
    },
    {
        "route_id": "cboe_futures_historical_data",
        "source_owner": "Cboe Futures Exchange",
        "applies_to": "CFE/CBOE Futures Exchange; VIX futures",
        "url": "https://www.cboe.com/markets/us/futures/market-statistics/historical-data/futures/",
        "route_type": "public_historical_futures_market_data",
        "current_status": "public_market_data_only_not_control_rows",
    },
    {
        "route_id": "courtlistener_recap_exhibit_a",
        "source_owner": "Public RECAP/PACER mirror",
        "applies_to": "Oystacher Exhibit A SPOOF/FLIP rows",
        "url": "https://storage.courtlistener.com/recap/gov.uscourts.ilnd.316889/gov.uscourts.ilnd.316889.1.1.pdf",
        "route_type": "public_court_exhibit_positive_candidate_source",
        "current_status": "positive_candidate_source_controls_rejected",
    },
    {
        "route_id": "finra_report_center_potential_manipulation",
        "source_owner": "FINRA",
        "applies_to": "equities quote spoofing/layering only; not Oystacher futures cells",
        "url": "https://www.finra.org/filing-reporting/regulatory-filing-systems/report-center",
        "route_type": "entitled_surveillance_report_route",
        "current_status": "not_matching_current_oystacher_control_cells",
    },
]

LOCAL_PATHS = [
    (
        "/Users/thrill3r/Downloads/external-data-sources/FinceptTerminal/fincept-qt/scripts/cme_data.py",
        "cme_public_aggregate_api_wrapper",
        "aggregate settlement volume open-interest or delayed quote surface, not source-owned order-lifecycle normal controls",
    ),
    (
        "/Users/thrill3r/nautilus_trader/tests/test_data/databento/esh4-glbx-mdp3-20231224.mbo.dbn.zst",
        "databento_mbo_sample",
        "modern ES sample test data, not Oystacher 2011-2014 multi-symbol normal controls",
    ),
    (
        "/Users/thrill3r/nautilus_trader/tests/test_data/databento/esh4-glbx-mdp3-20231225.mbo.dbn.zst",
        "databento_mbo_sample",
        "modern ES sample test data, not Oystacher 2011-2014 multi-symbol normal controls",
    ),
    (
        "/Users/thrill3r/nautilus_trader/tests/test_data/databento/historical_bars_catalog/databento/futures_mbp-1_2024-07-01T23-58_2024-07-02T00-02.dbn.zst",
        "databento_mbp_sample",
        "modern book sample without source-owned normal labels or required Oystacher cells",
    ),
    (
        "/Users/thrill3r/nautilus_trader/tests/test_data/databento/historical_bars_catalog/databento/futures_trades_2024-07-01T23-58_2024-07-02T00-02.dbn.zst",
        "databento_trade_sample",
        "modern trade sample without source-owned normal labels or required Oystacher cells",
    ),
    (
        "/Users/thrill3r/nautilus_trader/tests/test_data/xcme/6EH4.XCME_1min_bars_20240101_20240131.csv.gz",
        "xcme_bar_sample",
        "one-minute bars are OHLCV proxy evidence and cannot close direct Manipulation controls",
    ),
]


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO))
    except ValueError:
        return str(path)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def route_for_cell(cell: dict[str, str]) -> str:
    bucket = cell.get("bucket", "")
    cme_buckets = {
        "CME Globex",
        "COMEX/CME Globex",
        "NYMEX/CME Globex",
        "E-mini S&P 500 futures",
        "High-Grade Copper futures",
        "Crude Oil futures",
        "Natural Gas futures",
        "energy",
        "equity_index",
        "metals",
    }
    cboe_buckets = {"CFE/CBOE Futures Exchange", "VIX futures", "volatility_index"}
    if bucket in cme_buckets:
        return "cme_datamine_globex_order_book"
    if bucket in cboe_buckets:
        return "cboe_datashop_entrypoint"
    if cell.get("axis") == "chronological_year":
        return "cme_or_cboe_by_symbol_mix_required"
    return "manual_owner_route_review_required"


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)
    for required in [CONTROL_CELLS, POLICY_JSON, NORMAL_PREFLIGHT_JSON]:
        if not required.exists():
            raise FileNotFoundError(required)

    cells = read_csv(CONTROL_CELLS)
    cell_rows = []
    for cell in cells:
        cell_rows.append(
            {
                "axis": cell.get("axis", ""),
                "bucket": cell.get("bucket", ""),
                "positive_spoof_support": cell.get("positive_spoof_support", ""),
                "invalid_flip_candidate_support": cell.get("invalid_flip_candidate_support", ""),
                "required_valid_normal_control_support": cell.get("required_valid_normal_control_support", "73"),
                "valid_normal_control_support_observed_after_route_screen": 0,
                "valid_normal_control_shortfall_after_route_screen": cell.get("valid_normal_control_shortfall", "73"),
                "source_owner_route": route_for_cell(cell),
                "current_decision": "route_only_controls_not_acquired",
                "accepted_for_canonical_merge": "false",
            }
        )

    local_rows = []
    for path_text, data_kind, reason in LOCAL_PATHS:
        path = Path(path_text)
        local_rows.append(
            {
                "path": path_text,
                "exists": str(path.exists()).lower(),
                "data_kind": data_kind,
                "decision": "reject_for_current_contract",
                "reason": reason,
                "valid_source_owned_normal_control": "false",
                "accepted_for_current_contract": "false",
            }
        )

    gate = "r6_oystacher_source_owner_control_route_v1=routes_identified_controls_not_acquired_no_merge_or_chain_rerun"
    result = {
        "run_id": RUN_ID,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "gate_result": gate,
        "control_cells_input": rel(CONTROL_CELLS),
        "policy_input": rel(POLICY_JSON),
        "normal_control_preflight_input": rel(NORMAL_PREFLIGHT_JSON),
        "required_cells": len(cells),
        "source_owner_routes_checked": len(SOURCE_ROUTES),
        "local_paths_checked": len(local_rows),
        "existing_local_paths_checked": sum(1 for row in local_rows if row["exists"] == "true"),
        "valid_source_owned_normal_controls_found": 0,
        "canonical_merge_allowed": False,
        "downstream_chain_rerun": False,
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
    }

    json_path = OUT / "r6_oystacher_source_owner_control_route_v1.json"
    report_path = OUT / "r6_oystacher_source_owner_control_route_v1.md"
    routes_csv = OUT / "r6_oystacher_source_owner_control_routes_v1.csv"
    cells_csv = OUT / "r6_oystacher_control_cell_route_map_v1.csv"
    local_csv = OUT / "r6_oystacher_local_control_path_disposition_v1.csv"
    request_md = OUT / "r6_oystacher_source_owner_control_request_v1.md"
    assertions = CHECKS / "r6_oystacher_source_owner_control_route_v1_assertions.out"

    write_csv(
        routes_csv,
        [{**route, "controls_acquired": "false", "accepted_for_current_contract": "false"} for route in SOURCE_ROUTES],
        [
            "route_id",
            "source_owner",
            "applies_to",
            "url",
            "route_type",
            "current_status",
            "controls_acquired",
            "accepted_for_current_contract",
        ],
    )
    write_csv(
        cells_csv,
        cell_rows,
        [
            "axis",
            "bucket",
            "positive_spoof_support",
            "invalid_flip_candidate_support",
            "required_valid_normal_control_support",
            "valid_normal_control_support_observed_after_route_screen",
            "valid_normal_control_shortfall_after_route_screen",
            "source_owner_route",
            "current_decision",
            "accepted_for_canonical_merge",
        ],
    )
    write_csv(
        local_csv,
        local_rows,
        [
            "path",
            "exists",
            "data_kind",
            "decision",
            "reason",
            "valid_source_owned_normal_control",
            "accepted_for_current_contract",
        ],
    )
    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    request_md.write_text(
        "\n".join(
            [
                "# R6 Oystacher Source-Owned Normal Control Request v1",
                "",
                "Target root after approval/export: `/tmp/ict-engine-board-a-r6-owner-export-v1`",
                "",
                "Required verifier-native files:",
                "- `positive_spoofing_layering_rows.csv`",
                "- `matched_negative_normal_activity_rows.csv`",
                "- `provenance_manifest.json`",
                "",
                "Required coverage:",
                "- At least `73` valid source-owned normal-control rows for each of the 17 Oystacher cells.",
                "- CME/CME Globex/COMEX/NYMEX cells require CME owner-approved order-lifecycle exports.",
                "- CFE/VIX cells require Cboe/CFE owner-approved order-lifecycle exports.",
                "",
                "Boundary:",
                "- Public market data, OHLCV bars, aggregate settlements, modern samples, and same-exhibit `FLIP` rows are not accepted controls unless an explicit exception approves FLIP-as-control.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    report_path.write_text(
        "\n".join(
            [
                "# R6 Oystacher Source-Owner Control Route v1",
                "",
                f"- Run id: `{RUN_ID}`.",
                f"- Gate result: `{gate}`.",
                f"- Required cells mapped: `{len(cells)}`.",
                f"- Source-owner routes checked: `{len(SOURCE_ROUTES)}`.",
                f"- Local paths checked: `{len(local_rows)}`; existing local paths: `{result['existing_local_paths_checked']}`.",
                "- CME Group is the source-owner route for CME/COMEX/NYMEX Oystacher cells.",
                "- Cboe/CFE is the source-owner route for VIX futures cells.",
                "- CourtListener/RECAP Exhibit A remains positive-candidate evidence only.",
                "- FINRA Report Center remains useful for a separate equities manipulation branch, not the current Oystacher futures control cells.",
                "- Local CME/Databento/Nautilus paths are aggregate, modern sample, or OHLCV/proxy data and remain rejected for this contract.",
                "- Valid source-owned normal controls found: `0`.",
                "- Canonical merge allowed: `false`; downstream provider/Auto-Quant/pre-Bayes/BBN/CatBoost/execution-tree rerun: `false`.",
                "- Accepted rows added: `0`; new confidence gate: `false`; strict full objective achieved: `false`; `update_goal=false`.",
                "- Runtime code changed: `false`; shared intake mutated: `false`; owner-export root mutated: `false`; thresholds relaxed: `false`; raw data committed: `false`; trade usable: `false`.",
                "",
                "Artifacts:",
                f"- JSON: `{rel(json_path)}`",
                f"- Source-owner routes CSV: `{rel(routes_csv)}`",
                f"- Control cell route map CSV: `{rel(cells_csv)}`",
                f"- Local path disposition CSV: `{rel(local_csv)}`",
                f"- Source-owned normal control request: `{rel(request_md)}`",
                f"- Assertions: `{rel(assertions)}`",
                "",
                "Next:",
                "- Acquire source-owned normal controls from the mapped CME/Cboe routes, or obtain explicit board/user approval for RECAP/PACER provenance plus FLIP-as-control, then merge under a shared lock and rerun the full chain.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    assertions.write_text(
        "\n".join(
            [
                f"gate_result={gate}",
                f"required_cells={len(cells)}",
                f"source_owner_routes_checked={len(SOURCE_ROUTES)}",
                f"local_paths_checked={len(local_rows)}",
                "valid_source_owned_normal_controls_found=0",
                "canonical_merge_allowed=False",
                "downstream_chain_rerun=False",
                "accepted_rows_added=0",
                "new_confidence_gate=False",
                "strict_full_objective_achieved=False",
                "shared_intake_mutated=False",
                "owner_export_root_mutated=False",
                "update_goal=False",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
