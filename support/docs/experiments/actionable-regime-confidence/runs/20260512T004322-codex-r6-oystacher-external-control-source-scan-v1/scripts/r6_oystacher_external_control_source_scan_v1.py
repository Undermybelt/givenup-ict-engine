#!/usr/bin/env python3
"""Scan external acquisition routes for R6 Oystacher normal controls.

This is a bounded source-readback artifact. It checks whether public/official
or provider routes surfaced for the Oystacher control blocker can supply
verifier-ready source-owned normal controls. It does not download market data,
does not mutate any intake root, and does not approve a control policy.
"""

from __future__ import annotations

import csv
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


RUN_ID = "20260512T004322-codex-r6-oystacher-external-control-source-scan-v1"
REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs" / RUN_ID
OUT = RUN_ROOT / "r6-oystacher-external-control-source-scan"
CHECKS = RUN_ROOT / "checks"
CMD_OUT = RUN_ROOT / "command-output"

CONTROL_REQUEST_CSV = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260512T003627-codex-r6-oystacher-control-contract-request-v1/"
    "r6-oystacher-control-contract-request/r6_oystacher_required_normal_control_cells_v1.csv"
)
LOCAL_DISPOSITION_JSON = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260512T003811-codex-r6-oystacher-local-control-path-disposition-v1/"
    "r6-oystacher-local-control-path-disposition/"
    "r6_oystacher_local_control_path_disposition_v1.json"
)

SOURCES = [
    {
        "source_id": "cftc_oystacher_press_release_7264_15",
        "url": "https://www.cftc.gov/PressRoom/PressReleases/7264-15",
        "owner_type": "official_enforcement_context",
        "classification": "positive_context_only",
        "reason": "Official CFTC context identifies Oystacher/3Red spoofing/layering venues, products, and dates but does not provide independent normal-control rows.",
    },
    {
        "source_id": "cme_historical_market_depth_page",
        "url": "https://www.cmegroup.com/market-data/historical-data/market-depth.html",
        "owner_type": "exchange_market_data_route",
        "classification": "licensed_raw_order_book_route_not_labels",
        "reason": "CME historical market-depth route may support licensed raw depth acquisition, but raw depth/order book data is not verifier-ready source-owned normal/non-manipulation labels.",
    },
    {
        "source_id": "cme_market_depth_faq_pdf",
        "url": "https://www.cmegroup.com/market-data/files/cme-group-market-depth-faq.pdf",
        "owner_type": "exchange_market_data_documentation",
        "classification": "licensed_raw_order_book_route_not_labels",
        "reason": "Market-depth documentation can justify raw order book reconstruction paths, but it does not supply matched_negative_normal_activity rows or normal-control provenance.",
    },
    {
        "source_id": "databento_cme_10_year_backfill",
        "url": "https://databento.com/blog/cme-10-year-backfill",
        "owner_type": "licensed_data_provider_route",
        "classification": "licensed_raw_market_data_route_not_labels",
        "reason": "Databento/CME historical backfill can be a raw market-data acquisition route, but it is not source-owned normal/non-manipulation labeling and may need explicit policy before use as controls.",
    },
]

TERMS = [
    "oystacher",
    "spoof",
    "layering",
    "market depth",
    "order book",
    "mdp 3.0",
    "2011",
    "2014",
    "comex",
    "nymex",
    "normal",
    "non-manipulation",
]


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO))
    except ValueError:
        return str(path)


def fetch_probe(url: str) -> dict[str, object]:
    request = Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urlopen(request, timeout=20) as response:
            payload = response.read(100_000)
            text = payload.decode("utf-8", errors="ignore").lower()
            term_hits = [term for term in TERMS if term in text]
            return {
                "http_status": response.status,
                "content_type": response.headers.get("content-type", ""),
                "sample_bytes": len(payload),
                "term_hits": term_hits,
                "fetch_error": "",
            }
    except HTTPError as exc:
        return {
            "http_status": exc.code,
            "content_type": exc.headers.get("content-type", "") if exc.headers else "",
            "sample_bytes": 0,
            "term_hits": [],
            "fetch_error": f"HTTPError:{exc.code}",
        }
    except URLError as exc:
        return {
            "http_status": None,
            "content_type": "",
            "sample_bytes": 0,
            "term_hits": [],
            "fetch_error": f"URLError:{exc.reason}",
        }
    except Exception as exc:  # pragma: no cover - defensive artifact capture
        return {
            "http_status": None,
            "content_type": "",
            "sample_bytes": 0,
            "term_hits": [],
            "fetch_error": f"{type(exc).__name__}:{exc}",
        }


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def read_required_cells() -> list[dict[str, str]]:
    with CONTROL_REQUEST_CSV.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)
    CMD_OUT.mkdir(parents=True, exist_ok=True)
    if not CONTROL_REQUEST_CSV.exists():
        raise FileNotFoundError(CONTROL_REQUEST_CSV)
    if not LOCAL_DISPOSITION_JSON.exists():
        raise FileNotFoundError(LOCAL_DISPOSITION_JSON)

    required_cells = read_required_cells()
    fetch_rows: list[dict[str, object]] = []
    source_rows: list[dict[str, object]] = []
    for source in SOURCES:
        probe = fetch_probe(source["url"])
        row = {**source, **probe}
        row["term_hits"] = ";".join(probe["term_hits"])
        row["verifier_ready_source_owned_normal_controls"] = "false"
        row["canonical_merge_allowed_from_this_source"] = "false"
        source_rows.append(row)
        fetch_rows.append(
            {
                "source_id": source["source_id"],
                "url": source["url"],
                "http_status": probe["http_status"],
                "content_type": probe["content_type"],
                "sample_bytes": probe["sample_bytes"],
                "term_hits": row["term_hits"],
                "fetch_error": probe["fetch_error"],
            }
        )

    raw_data_routes = [
        row for row in source_rows
        if re.search(r"raw_(order_book|market_data)_route", row["classification"])
    ]
    verifier_ready_rows = [
        row for row in source_rows
        if row["verifier_ready_source_owned_normal_controls"] == "true"
    ]
    gate = "r6_oystacher_external_control_source_scan_v1=external_routes_identified_no_verifier_ready_source_owned_normal_controls"
    result = {
        "run_id": RUN_ID,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "gate_result": gate,
        "control_request_csv": rel(CONTROL_REQUEST_CSV),
        "local_disposition_json": rel(LOCAL_DISPOSITION_JSON),
        "external_sources_checked": len(source_rows),
        "raw_data_routes_identified": len(raw_data_routes),
        "verifier_ready_source_owned_normal_controls_found": len(verifier_ready_rows),
        "required_control_cells": len(required_cells),
        "required_cells_still_short": len(required_cells),
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
            "If using raw CME/Databento market data as normal controls is desired, "
            "record explicit owner/user policy approval and acquire licensed data; "
            "otherwise R6 still needs verifier-ready source-owned normal controls."
        ),
    }

    sources_csv = OUT / "r6_oystacher_external_control_sources_v1.csv"
    fetch_csv = OUT / "r6_oystacher_external_fetch_readback_v1.csv"
    json_path = OUT / "r6_oystacher_external_control_source_scan_v1.json"
    report_path = OUT / "r6_oystacher_external_control_source_scan_v1.md"
    assertions_path = CHECKS / "r6_oystacher_external_control_source_scan_v1_assertions.out"

    write_csv(
        sources_csv,
        source_rows,
        [
            "source_id",
            "url",
            "owner_type",
            "classification",
            "http_status",
            "content_type",
            "sample_bytes",
            "term_hits",
            "fetch_error",
            "verifier_ready_source_owned_normal_controls",
            "canonical_merge_allowed_from_this_source",
            "reason",
        ],
    )
    write_csv(
        fetch_csv,
        fetch_rows,
        ["source_id", "url", "http_status", "content_type", "sample_bytes", "term_hits", "fetch_error"],
    )
    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report_path.write_text(
        "\n".join(
            [
                "# R6 Oystacher External Control Source Scan v1",
                "",
                f"- Run id: `{RUN_ID}`.",
                f"- Gate result: `{gate}`.",
                f"- External sources checked: `{len(source_rows)}`.",
                f"- Raw market-data acquisition routes identified: `{len(raw_data_routes)}`.",
                "- Verifier-ready source-owned normal controls found: `0`.",
                f"- Required Oystacher normal-control cells still short: `{len(required_cells)}`.",
                "- CME/Databento routes remain acquisition or licensing paths for raw order-book/depth data, not source-owned normal/non-manipulation labels under the current contract.",
                "- Canonical merge allowed: `false`; downstream verifier/provider/Auto-Quant/pre-Bayes/BBN/CatBoost/execution-tree rerun: `false`.",
                "- Accepted rows added: `0`; strict full objective achieved: `false`; `update_goal=false`.",
                "- Runtime code changed: `false`; shared intake mutated: `false`; thresholds relaxed: `false`; raw data committed: `false`; external requests sent: `true`; trade usable: `false`.",
                "",
                "Artifacts:",
                f"- JSON: `{rel(json_path)}`",
                f"- Sources CSV: `{rel(sources_csv)}`",
                f"- Fetch readback CSV: `{rel(fetch_csv)}`",
                f"- Assertions: `{rel(assertions_path)}`",
                "",
                "Next:",
                "- Keep the Oystacher rows isolated. Either obtain explicit approval for RECAP/PACER provenance plus FLIP-as-control, or acquire verifier-ready source-owned normal controls. Raw CME/Databento data needs explicit policy approval before it can be treated as normal controls.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    assertions_path.write_text(
        "\n".join(
            [
                f"gate_result={gate}",
                f"external_sources_checked={len(source_rows)}",
                f"raw_data_routes_identified={len(raw_data_routes)}",
                "verifier_ready_source_owned_normal_controls_found=0",
                f"required_cells_still_short={len(required_cells)}",
                "canonical_merge_allowed=False",
                "downstream_chain_rerun=False",
                "shared_intake_mutated=False",
                "strict_full_objective_achieved=False",
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
