#!/usr/bin/env python3
"""Current send-channel preflight for R6 owner-export requests.

This artifact refreshes official route/contact evidence only. It does not
submit vendor requests, acquire data, populate the owner-export root, or rerun
promotion.
"""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


RUN_ID = "20260512T014300-codex-r6-owner-export-current-send-channel-preflight-v1"
REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs" / RUN_ID
OUT = RUN_ROOT / "r6-owner-export-current-send-channel-preflight-v1"
CHECKS = RUN_ROOT / "checks"

TMP_ROOTS = {
    "r6_owner_export": (
        Path("/tmp/ict-engine-board-a-r6-owner-export-v1"),
        ["positive_spoofing_layering_rows.csv", "matched_negative_normal_activity_rows.csv", "provenance_manifest.json"],
    ),
    "source_label_equivalence": (
        Path("/tmp/ict-engine-source-label-equivalence-intake"),
        ["source_label_equivalence_rows.csv", "source_label_equivalence_provenance.json"],
    ),
    "r3_native_subhour": (
        Path("/tmp/ict-engine-native-subhour-source-label-intake"),
        ["native_subhour_source_label_rows.csv", "native_subhour_source_label_provenance.json"],
    ),
    "r5_recency_extension": (
        Path("/tmp/ict-engine-source-panel-recency-extension"),
        ["stock_market_regimes_2026_extension.csv", "source_panel_recency_provenance.json"],
    ),
}

SEND_CHANNELS = [
    {
        "owner": "CME Group",
        "route": "DataMine historical data",
        "url": "https://www.cmegroup.com/market-data/datamine-historical-data/index.html",
        "current_web_evidence": "Official CME DataMine page exposes a Data Sales contact channel, including CMEDataSales@cmegroup.com, for historical data packages.",
        "request_use": "Primary send channel for CME/NYMEX/COMEX/CME Globex normal-control export request covering 2011-2013 Oystacher cells.",
        "send_status": "not_sent_needs_owner_or_operator_submission",
    },
    {
        "owner": "CME Group",
        "route": "Market Depth Files FAQ",
        "url": "https://www.cmegroup.com/market-data/files/cme-group-market-depth-faq.pdf",
        "current_web_evidence": "FAQ remains route evidence for order-book reconstruction, FIX/FAST depth files, timestamps, and exchange-level start-date fit; it is not a data export.",
        "request_use": "Attach as scope evidence when asking CME Data Sales to confirm product-level CL/NG/HG/ES coverage and matched normal-control exports.",
        "send_status": "not_sent_supporting_reference_only",
    },
    {
        "owner": "Cboe/CFE",
        "route": "Cboe U.S. Futures historical data",
        "url": "https://www.cboe.com/markets/us/futures/market-statistics/historical-data/oof/",
        "current_web_evidence": "CFE public history route points to Cboe DataShop for custom VIX futures historical data; public page itself is not verifier-native normal-control data.",
        "request_use": "Route 2014 VIX/CFE cells to Cboe DataShop/support for historical trades/quotes or depth/order-lifecycle export.",
        "send_status": "not_sent_needs_owner_or_operator_submission",
    },
    {
        "owner": "Cboe/CFE",
        "route": "Cboe Market Data Services U.S. Futures",
        "url": "https://res.cboe.com/market_data_services/us/futures/",
        "current_web_evidence": "Cboe U.S. Futures market-data services document Top-of-Book and Depth-of-Book routes for VIX futures data, but historical verifier-native export terms still require DataShop/support.",
        "request_use": "Supporting route for CFE/VIX depth/order-lifecycle availability and licensing clarification.",
        "send_status": "not_sent_supporting_reference_only",
    },
    {
        "owner": "Cboe/CFE",
        "route": "Cboe DataShop CFE futures trades",
        "url": "https://datashop.cboe.com/cfe-futures-trades",
        "current_web_evidence": "DataShop CFE futures trades product exposes trade fields such as trade date, contract symbol, size, price, side, trade time, and originating-order indicators; it is useful route evidence but not yet acquired/provenanced Board A input.",
        "request_use": "Ask whether this product or a custom support export can satisfy matched normal/non-manipulation controls for 2014 VIX futures cells.",
        "send_status": "not_sent_needs_owner_or_operator_submission",
    },
]


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def tmp_root_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for root_id, (root, required_files) in TMP_ROOTS.items():
        missing = [name for name in required_files if not (root / name).exists()]
        rows.append(
            {
                "root_id": root_id,
                "root": str(root),
                "root_present": str(root.exists()).lower(),
                "required_files": ";".join(required_files),
                "required_files_present": str(not missing).lower(),
                "missing_files": ";".join(missing),
            }
        )
    return rows


def rel(path: Path) -> str:
    return str(path.relative_to(REPO))


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)

    tmp_roots = tmp_root_rows()
    r6_ready = next(row for row in tmp_roots if row["root_id"] == "r6_owner_export")["required_files_present"] == "true"
    r3_ready = next(row for row in tmp_roots if row["root_id"] == "r3_native_subhour")["required_files_present"] == "true"
    r5_ready = next(row for row in tmp_roots if row["root_id"] == "r5_recency_extension")["required_files_present"] == "true"
    source_ready = next(row for row in tmp_roots if row["root_id"] == "source_label_equivalence")["required_files_present"] == "true"

    gate_result = "r6_owner_export_current_send_channel_preflight_v1=current_send_channels_confirmed_no_request_sent_no_controls_acquired"
    result = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "gate_result": gate_result,
        "official_web_route_lookup_performed": True,
        "owner_or_vendor_request_submitted": False,
        "ticket_or_export_identifier_received": False,
        "source_owned_normal_controls_acquired": 0,
        "flip_as_control_approved": False,
        "send_channels": SEND_CHANNELS,
        "tmp_roots": tmp_roots,
        "source_label_equivalence_ready": source_ready,
        "r6_owner_export_ready": r6_ready,
        "r3_native_subhour_ready": r3_ready,
        "r5_recency_extension_ready": r5_ready,
        "canonical_merge_allowed": False,
        "downstream_chain_rerun_allowed": False,
        "accepted_rows_added": 0,
        "new_confidence_gate": False,
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "shared_intake_mutated": False,
        "r3_root_mutated": False,
        "r5_root_mutated": False,
        "r6_owner_export_root_mutated": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "owner_export_request_sent": False,
        "external_contact_submitted": False,
        "trade_usable": False,
    }

    json_path = OUT / "r6_owner_export_current_send_channel_preflight_v1.json"
    report_path = OUT / "r6_owner_export_current_send_channel_preflight_v1.md"
    channel_csv = OUT / "r6_owner_export_current_send_channels_v1.csv"
    root_csv = OUT / "r6_owner_export_current_tmp_roots_v1.csv"
    assertions_path = CHECKS / "r6_owner_export_current_send_channel_preflight_v1_assertions.out"

    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_csv(
        channel_csv,
        SEND_CHANNELS,
        ["owner", "route", "url", "current_web_evidence", "request_use", "send_status"],
    )
    write_csv(
        root_csv,
        tmp_roots,
        ["root_id", "root", "root_present", "required_files", "required_files_present", "missing_files"],
    )

    channel_lines = [
        f"- `{row['owner']}` / `{row['route']}`: `{row['send_status']}`; {row['url']}"
        for row in SEND_CHANNELS
    ]
    report_path.write_text(
        "\n".join(
            [
                "# R6 Owner Export Current Send-Channel Preflight v1",
                "",
                f"- Gate result: `{gate_result}`.",
                "- Current official web route lookup performed: `true`.",
                "- Owner/vendor request submitted: `false`; ticket/export identifier received: `false`.",
                "- Source-owned normal controls acquired: `0`; FLIP-as-control approved: `false`.",
                "- This refresh confirms send channels only. It does not replace the v3 sendable request drafts and does not authorize owner-root population.",
                "",
                "## Current Send Channels",
                *channel_lines,
                "",
                "## Root Readback",
                f"- Source-label equivalence root ready: `{str(source_ready).lower()}`.",
                f"- R6 owner-export root ready: `{str(r6_ready).lower()}`.",
                f"- R3 native-subhour root ready: `{str(r3_ready).lower()}`.",
                f"- R5 recency-extension root ready: `{str(r5_ready).lower()}`.",
                "",
                "## Promotion Status",
                "- Accepted rows added: `0`; new confidence gate: false; canonical merge allowed: false; downstream chain rerun allowed: false.",
                "- Runtime code changed: false. Shared intake mutated: false. R3/R5/R6 roots mutated: false. Thresholds relaxed: false. Raw data committed: false. External contact submitted: false. Trade usable: false.",
                "",
                "Artifacts:",
                f"- JSON: `{rel(json_path)}`",
                f"- Send-channel CSV: `{rel(channel_csv)}`",
                f"- Tmp-root CSV: `{rel(root_csv)}`",
                f"- Assertions: `{rel(assertions_path)}`",
                "",
                "Next:",
                "- Submit the CME and Cboe/CFE request drafts through an owner/operator account, or record explicit FLIP-as-control approval. Only after ticket/export identifiers and verifier-native rows arrive should `/tmp/ict-engine-board-a-r6-owner-export-v1` be populated and the full chain rerun.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    checks = [
        ("official_web_route_lookup_performed_true", result["official_web_route_lookup_performed"] is True),
        ("owner_vendor_request_submitted_false", result["owner_or_vendor_request_submitted"] is False),
        ("source_owned_normal_controls_zero", result["source_owned_normal_controls_acquired"] == 0),
        ("flip_as_control_approved_false", result["flip_as_control_approved"] is False),
        ("source_label_root_ready", source_ready),
        ("r6_owner_export_not_ready", not r6_ready),
        ("r3_native_subhour_not_ready", not r3_ready),
        ("r5_recency_extension_not_ready", not r5_ready),
        ("canonical_merge_allowed_false", result["canonical_merge_allowed"] is False),
        ("downstream_chain_rerun_allowed_false", result["downstream_chain_rerun_allowed"] is False),
        ("strict_full_objective_achieved_false", result["strict_full_objective_achieved"] is False),
        ("update_goal_false", result["update_goal"] is False),
        ("external_contact_submitted_false", result["external_contact_submitted"] is False),
        ("trade_usable_false", result["trade_usable"] is False),
    ]
    assertions_path.write_text(
        "\n".join(f"{name}={'PASS' if passed else 'FAIL'}" for name, passed in checks) + "\n",
        encoding="utf-8",
    )
    failed = [name for name, passed in checks if not passed]
    if failed:
        raise SystemExit("failed checks: " + ", ".join(failed))
    print(json.dumps({"gate_result": gate_result, "update_goal": False}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
