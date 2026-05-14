#!/usr/bin/env python3
"""Public contact-lead package for the R2 source-label equivalence request."""

from __future__ import annotations

import csv
import json
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


RUN_ID = "20260511T202712-codex-source-label-equivalence-contact-leads-v1"
RUN_ROOT = Path("docs/experiments/actionable-regime-confidence/runs") / RUN_ID
OUT_DIR = RUN_ROOT / "source-label-equivalence-contact-leads"
CHECK_DIR = RUN_ROOT / "checks"

REQUEST_TEMPLATE = (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T163532-codex-source-label-equivalence-request-v1/"
    "source-label-equivalence/source_label_equivalence_request_v1.md"
)
REQUEST_TARGETS = (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T163532-codex-source-label-equivalence-request-v1/"
    "source-label-equivalence/source_label_equivalence_request_v1_targets.csv"
)
INTAKE_ROOT = "/tmp/ict-engine-source-label-equivalence-intake"

CONTACT_LEADS = [
    {
        "lead_id": "kaggle_stock_regime_owner_discussion",
        "package_id": "price_root_equivalence_us_index_futures",
        "contact_surface": "Kaggle stock-regime dataset discussion/comments route",
        "url": "https://www.kaggle.com/datasets/mafaqbhatti/stock-market-regimes-20002026/discussion",
        "intended_use": "Request owner-approved equivalence policy or source-native rows for QQQ/NQ/NDX/futures extensions.",
        "status": "ready_public_surface_no_rows_acquired",
    },
    {
        "lead_id": "kaggle_stock_regime_owner_profile",
        "package_id": "price_root_equivalence_us_index_futures",
        "contact_surface": "Kaggle owner profile for stock-market-regimes source labels",
        "url": "https://www.kaggle.com/mafaqbhatti",
        "intended_use": "Owner identity route for the R2 source-label equivalence request.",
        "status": "ready_public_surface_no_rows_acquired",
    },
    {
        "lead_id": "nasdaq_indexes_contact",
        "package_id": "price_root_equivalence_us_index_futures",
        "contact_surface": "Nasdaq indexes contact page",
        "url": "https://indexes.nasdaq.com/contactus",
        "intended_use": "Ask whether Nasdaq-100/NDX equivalence policy or source-native index label documentation can be approved for QQQ/NQ/NDX use.",
        "status": "public_contact_surface_no_rows_acquired",
    },
    {
        "lead_id": "nasdaq_global_indexes_licensing",
        "package_id": "price_root_equivalence_us_index_futures",
        "contact_surface": "Nasdaq global indexes licensing and ETPs page",
        "url": "https://www.nasdaq.com/solutions/global-indexes/licensing-and-etps",
        "intended_use": "Index licensing route for explicit crosswalk/equivalence approval, not a label source by itself.",
        "status": "public_licensing_surface_no_rows_acquired",
    },
    {
        "lead_id": "sp_dji_contact",
        "package_id": "price_root_equivalence_us_index_futures",
        "contact_surface": "S&P Dow Jones Indices contact page",
        "url": "https://www.spglobal.com/spdji/en/contact-us/",
        "intended_use": "Potential route for S&P/Dow Jones index family source/equivalence approval; WAF may block unauthenticated probes.",
        "status": "public_contact_surface_no_rows_acquired",
    },
    {
        "lead_id": "cme_market_data_contacts",
        "package_id": "price_root_equivalence_us_index_futures",
        "contact_surface": "CME Group tools/contact list",
        "url": "https://www.cmegroup.com/tools-information/contacts-list.html",
        "intended_use": "Potential route for ES/NQ/MNQ futures market-data licensing or source equivalence policy.",
        "status": "public_contact_surface_no_rows_acquired",
    },
    {
        "lead_id": "kraken_public_api_examples",
        "package_id": "price_root_equivalence_crypto",
        "contact_surface": "Kraken public API examples/support page",
        "url": "https://support.kraken.com/hc/articles/360000919986-Public-endpoint-examples-you-can-try-them-directly-in-a-web-browser-",
        "intended_use": "Venue/public-data route for crypto source provenance; not accepted as regime labels without owner-approved labels.",
        "status": "venue_data_surface_not_label_rows",
    },
    {
        "lead_id": "kraken_futures_market_history_docs",
        "package_id": "price_root_equivalence_crypto",
        "contact_surface": "Kraken futures market-history API docs",
        "url": "https://docs.kraken.com/api/docs/futures-api/history/market-history/",
        "intended_use": "Venue-native crypto market-history route; can support provenance only, not MainRegimeV2 labels by itself.",
        "status": "venue_data_surface_not_label_rows",
    },
    {
        "lead_id": "cme_fx_rates_commodities_contacts",
        "package_id": "price_root_equivalence_fx_rates_commodities",
        "contact_surface": "CME Group tools/contact list for FX/rates/commodities futures",
        "url": "https://www.cmegroup.com/tools-information/contacts-list.html",
        "intended_use": "Potential route for GC/CL/ZN or FX/rates/commodities futures data/equivalence policy.",
        "status": "public_contact_surface_no_rows_acquired",
    },
]


def probe_url(url: str) -> dict[str, object]:
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        request = urllib.request.Request(url, method="HEAD", headers=headers)
        with urllib.request.urlopen(request, timeout=20) as response:
            return {
                "probe_status": "ok",
                "http_status": response.status,
                "content_type": response.headers.get("content-type", ""),
            }
    except Exception as first_exc:
        try:
            request = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(request, timeout=20) as response:
                return {
                    "probe_status": "ok_get_fallback",
                    "http_status": response.status,
                    "content_type": response.headers.get("content-type", ""),
                }
        except Exception as second_exc:
            return {
                "probe_status": "blocked_or_error",
                "http_status": "",
                "error": f"{type(second_exc).__name__}: {second_exc}",
                "head_error": f"{type(first_exc).__name__}: {first_exc}",
            }


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def write_report(payload: dict[str, object], leads: list[dict[str, object]]) -> None:
    md_path = OUT_DIR / "source_label_equivalence_contact_leads_v1.md"
    lines = [
        "# Source Label Equivalence Contact Leads v1",
        "",
        f"Run ID: `{RUN_ID}`",
        "",
        f"- Gate result: `{payload['decision']}`.",
        "- Purpose: convert the R2 source-label equivalence request into concrete public contact/licensing leads without promoting proxy data.",
        f"- Contact leads recorded: `{payload['contact_lead_count']}`.",
        f"- URL probes ok: `{payload['url_probe_ok_count']}`; blocked/error probes: `{payload['url_probe_blocked_or_error_count']}`.",
        f"- Request sent: `{str(payload['request_sent']).lower()}`; rows acquired: `{str(payload['rows_acquired']).lower()}`.",
        f"- Strict full objective achieved: `{str(payload['strict_full_objective_achieved']).lower()}`; `update_goal={str(payload['update_goal']).lower()}`.",
        "",
        "## Package Coverage",
        "",
        "| Package | Leads |",
        "|---|---:|",
    ]
    for package_id, count in payload["package_lead_counts"].items():
        lines.append(f"| `{package_id}` | `{count}` |")
    lines.extend(["", "## Contact Leads", ""])
    for lead in leads:
        lines.append(
            f"- `{lead['lead_id']}` / `{lead['package_id']}`: {lead['contact_surface']} ({lead['url']}) -> `{lead['status']}`, probe `{lead['probe_status']}` `{lead['http_status']}`. {lead['intended_use']}"
        )
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            f"This run does not send a request, download rows, or create `{INTAKE_ROOT}` files. R2 remains blocked until source-owned or owner-approved rows plus provenance pass the existing source-label equivalence verifier.",
            "",
            "## Artifacts",
            "",
            "- JSON: `source_label_equivalence_contact_leads_v1.json`",
            "- Contact CSV: `source_label_equivalence_contact_leads_v1.csv`",
            "- Assertions: `../checks/source_label_equivalence_contact_leads_v1_assertions.out`",
            "",
        ]
    )
    md_path.write_text("\n".join(lines))


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)

    leads: list[dict[str, object]] = []
    for lead in CONTACT_LEADS:
        enriched = dict(lead)
        enriched.update(probe_url(lead["url"]))
        leads.append(enriched)

    package_counts: dict[str, int] = {}
    for lead in leads:
        package_id = str(lead["package_id"])
        package_counts[package_id] = package_counts.get(package_id, 0) + 1

    ok_count = sum(1 for lead in leads if str(lead["probe_status"]).startswith("ok"))
    blocked_count = len(leads) - ok_count
    payload: dict[str, object] = {
        "run_id": RUN_ID,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "decision": "source_label_equivalence_contact_leads_v1=public_contact_paths_ready_rows_not_acquired",
        "prior_request_template": REQUEST_TEMPLATE,
        "prior_request_targets": REQUEST_TARGETS,
        "prior_request_template_available": Path(REQUEST_TEMPLATE).exists(),
        "prior_request_targets_available": Path(REQUEST_TARGETS).exists(),
        "required_intake_root": INTAKE_ROOT,
        "contact_leads": leads,
        "contact_lead_count": len(leads),
        "package_lead_counts": dict(sorted(package_counts.items())),
        "url_probe_ok_count": ok_count,
        "url_probe_blocked_or_error_count": blocked_count,
        "request_sent": False,
        "rows_acquired": False,
        "source_label_equivalence_intake_files_created": False,
        "accepted_rows_added": 0,
        "new_confidence_gate": False,
        "r2_other_market_source_label_equivalence_closed": False,
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "trade_usable": False,
    }

    (OUT_DIR / "source_label_equivalence_contact_leads_v1.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n"
    )
    write_csv(
        OUT_DIR / "source_label_equivalence_contact_leads_v1.csv",
        leads,
        [
            "lead_id",
            "package_id",
            "contact_surface",
            "url",
            "intended_use",
            "status",
            "probe_status",
            "http_status",
            "content_type",
            "error",
            "head_error",
        ],
    )
    write_report(payload, leads)

    assertions = [
        ("prior_request_template_available", payload["prior_request_template_available"] is True),
        ("prior_request_targets_available", payload["prior_request_targets_available"] is True),
        ("contact_lead_count_ge_8", len(leads) >= 8),
        ("has_us_index_futures_leads", package_counts.get("price_root_equivalence_us_index_futures", 0) >= 4),
        ("has_crypto_leads", package_counts.get("price_root_equivalence_crypto", 0) >= 1),
        ("has_fx_rates_commodities_leads", package_counts.get("price_root_equivalence_fx_rates_commodities", 0) >= 1),
        ("request_sent_false", payload["request_sent"] is False),
        ("rows_acquired_false", payload["rows_acquired"] is False),
        ("accepted_rows_added_zero", payload["accepted_rows_added"] == 0),
        ("new_confidence_gate_false", payload["new_confidence_gate"] is False),
        ("r2_closed_false", payload["r2_other_market_source_label_equivalence_closed"] is False),
        ("strict_full_objective_achieved_false", payload["strict_full_objective_achieved"] is False),
        ("update_goal_false", payload["update_goal"] is False),
        ("raw_data_committed_false", payload["raw_data_committed"] is False),
    ]
    failed = [name for name, ok in assertions if not ok]
    (CHECK_DIR / "source_label_equivalence_contact_leads_v1_assertions.out").write_text(
        "\n".join(f"{name}=PASS" if ok else f"{name}=FAIL" for name, ok in assertions)
        + "\n"
    )
    if failed:
        raise SystemExit(f"failed assertions: {', '.join(failed)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
