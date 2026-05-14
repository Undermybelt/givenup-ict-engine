#!/usr/bin/env python3
"""Public contact-lead package for the R3 native sub-hour intake request."""

from __future__ import annotations

import csv
import json
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


RUN_ID = "20260511T203505-codex-native-subhour-contact-leads-v1"
RUN_ROOT = Path("docs/experiments/actionable-regime-confidence/runs") / RUN_ID
OUT_DIR = RUN_ROOT / "native-subhour-contact-leads"
CHECK_DIR = RUN_ROOT / "checks"

REQUEST_RUN = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T203100-codex-native-subhour-intake-request-package-v1/"
    "native-subhour-intake-request-package"
)
REQUEST_JSON = REQUEST_RUN / "native_subhour_intake_request_package_v1.json"
REQUEST_TARGETS = REQUEST_RUN / "native_subhour_intake_request_targets_v1.csv"
FOCUS_CELLS = REQUEST_RUN / "native_subhour_intake_focus_cells_v1.csv"
REQUEST_TEMPLATE = REQUEST_RUN / "native_subhour_intake_request_template_v1.md"
INTAKE_ROOT = "/tmp/ict-engine-native-subhour-source-label-intake"

CONTACT_LEADS = [
    {
        "lead_id": "kaggle_stock_regime_owner_discussion_intraday_extension",
        "contact_surface": "Kaggle stock-regime dataset discussion/comments route",
        "url": "https://www.kaggle.com/datasets/mafaqbhatti/stock-market-regimes-20002026/discussion",
        "lead_type": "source_label_owner_extension",
        "intended_use": "Ask the existing source-label owner whether native 1m/5m/15m/30m/1h/4h regime-label exports exist or can be approved.",
        "status": "ready_public_surface_no_rows_acquired",
    },
    {
        "lead_id": "kaggle_stock_regime_owner_profile_intraday_extension",
        "contact_surface": "Kaggle owner profile for the source-label dataset",
        "url": "https://www.kaggle.com/mafaqbhatti",
        "lead_type": "source_label_owner_identity_route",
        "intended_use": "Owner identity route for the R3 native sub-hour source-label request.",
        "status": "ready_public_surface_no_rows_acquired",
    },
    {
        "lead_id": "yahoo_finance_help_surface",
        "contact_surface": "Yahoo Finance help surface",
        "url": "https://help.yahoo.com/kb/finance-for-web",
        "lead_type": "provider_terms_contact_route",
        "intended_use": "Clarify source provenance/licensing for yfinance-visible intraday panels; not accepted as regime labels by itself.",
        "status": "provider_data_surface_not_label_rows",
    },
    {
        "lead_id": "yahoo_terms_surface",
        "contact_surface": "Yahoo terms/legal surface",
        "url": "https://legal.yahoo.com/us/en/yahoo/terms/otos/index.html",
        "lead_type": "provider_terms_contact_route",
        "intended_use": "Terms/provenance route for Yahoo-origin intraday data; cannot close R3 without source-native labels.",
        "status": "provider_terms_surface_not_label_rows",
    },
    {
        "lead_id": "nasdaq_data_link_contact",
        "contact_surface": "Nasdaq Data Link contact/support route",
        "url": "https://data.nasdaq.com/contact",
        "lead_type": "market_data_vendor_contact_route",
        "intended_use": "Potential route for index/ETF/futures intraday labeled data licensing or source-native regime-label availability.",
        "status": "public_contact_surface_no_rows_acquired",
    },
    {
        "lead_id": "nasdaq_indexes_contact",
        "contact_surface": "Nasdaq indexes contact route",
        "url": "https://indexes.nasdaq.com/contactus",
        "lead_type": "index_owner_contact_route",
        "intended_use": "Ask for index-family intraday source/equivalence approval; not a label source unless source-native labels are provided.",
        "status": "public_contact_surface_no_rows_acquired",
    },
    {
        "lead_id": "cme_market_data_contacts",
        "contact_surface": "CME Group tools/contact list",
        "url": "https://www.cmegroup.com/tools-information/contacts-list.html",
        "lead_type": "futures_market_data_contact_route",
        "intended_use": "Potential route for CL/ES/NQ intraday futures source data and any source-native label or provenance approval.",
        "status": "public_contact_surface_no_rows_acquired",
    },
    {
        "lead_id": "cboe_contact",
        "contact_surface": "Cboe contact route",
        "url": "https://www.cboe.com/contact/",
        "lead_type": "exchange_contact_route",
        "intended_use": "Potential route for exchange-native intraday context; cannot close R3 without owner-approved regime-label rows.",
        "status": "public_contact_surface_no_rows_acquired",
    },
    {
        "lead_id": "polygon_contact",
        "contact_surface": "Polygon.io contact route",
        "url": "https://polygon.io/contact",
        "lead_type": "market_data_vendor_contact_route",
        "intended_use": "Potential market-data licensing route for intraday panels; not accepted as source-native regime labels by itself.",
        "status": "vendor_data_surface_not_label_rows",
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
                "content_type": "",
                "error": f"{type(second_exc).__name__}: {second_exc}",
                "head_error": f"{type(first_exc).__name__}: {first_exc}",
            }


def read_csv_count(path: Path) -> int:
    if not path.exists():
        return 0
    with path.open(newline="", encoding="utf-8") as handle:
        return sum(1 for _ in csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def write_report(payload: dict[str, object], leads: list[dict[str, object]]) -> None:
    md_path = OUT_DIR / "native_subhour_contact_leads_v1.md"
    lines = [
        "# Native Sub-hour Contact Leads v1",
        "",
        f"Run ID: `{RUN_ID}`",
        "",
        f"- Gate result: `{payload['decision']}`.",
        "- Purpose: convert the R3 native sub-hour intake request into public contact/licensing leads without accepting proxy labels.",
        f"- Prior native request rows: `{payload['prior_native_intraday_target_count']}`.",
        f"- Focus blocker cells: `{payload['focus_blocker_cell_count']}`.",
        f"- Contact leads recorded: `{payload['contact_lead_count']}`.",
        f"- URL probes ok: `{payload['url_probe_ok_count']}`; blocked/error probes: `{payload['url_probe_blocked_or_error_count']}`.",
        f"- Request sent: `{str(payload['request_sent']).lower()}`; rows acquired: `{str(payload['rows_acquired']).lower()}`.",
        f"- Strict full objective achieved: `{str(payload['strict_full_objective_achieved']).lower()}`; `update_goal={str(payload['update_goal']).lower()}`.",
        "",
        "## Lead Type Coverage",
        "",
        "| Lead Type | Leads |",
        "|---|---:|",
    ]
    for lead_type, count in payload["lead_type_counts"].items():
        lines.append(f"| `{lead_type}` | `{count}` |")
    lines.extend(["", "## Contact Leads", ""])
    for lead in leads:
        lines.append(
            f"- `{lead['lead_id']}` / `{lead['lead_type']}`: {lead['contact_surface']} ({lead['url']}) -> `{lead['status']}`, probe `{lead['probe_status']}` `{lead['http_status']}`. {lead['intended_use']}"
        )
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            f"This run does not send a request, download rows, or create `{INTAKE_ROOT}` files. R3 remains blocked until owner-approved or source-native sub-hour labels plus provenance pass the native-subhour intake contract. Provider OHLCV, yfinance-visible bars, generated HMM/KMeans labels, future-return labels, and daily/monthly projections remain rejected.",
            "",
            "## Artifacts",
            "",
            "- JSON: `native_subhour_contact_leads_v1.json`",
            "- Contact CSV: `native_subhour_contact_leads_v1.csv`",
            "- Assertions: `../checks/native_subhour_contact_leads_v1_assertions.out`",
            "",
        ]
    )
    md_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)

    request_payload = json.loads(REQUEST_JSON.read_text(encoding="utf-8")) if REQUEST_JSON.exists() else {}
    leads: list[dict[str, object]] = []
    for lead in CONTACT_LEADS:
        enriched = dict(lead)
        enriched.update(probe_url(lead["url"]))
        leads.append(enriched)

    lead_type_counts: dict[str, int] = {}
    for lead in leads:
        lead_type = str(lead["lead_type"])
        lead_type_counts[lead_type] = lead_type_counts.get(lead_type, 0) + 1

    ok_count = sum(1 for lead in leads if str(lead["probe_status"]).startswith("ok"))
    blocked_count = len(leads) - ok_count
    payload: dict[str, object] = {
        "run_id": RUN_ID,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "decision": "native_subhour_contact_leads_v1=public_contact_paths_ready_rows_not_acquired",
        "prior_request_json": str(REQUEST_JSON),
        "prior_request_targets": str(REQUEST_TARGETS),
        "prior_focus_cells": str(FOCUS_CELLS),
        "prior_request_template": str(REQUEST_TEMPLATE),
        "prior_request_json_available": REQUEST_JSON.exists(),
        "prior_request_targets_available": REQUEST_TARGETS.exists(),
        "prior_focus_cells_available": FOCUS_CELLS.exists(),
        "prior_request_template_available": REQUEST_TEMPLATE.exists(),
        "prior_native_intraday_target_count": request_payload.get("native_intraday_target_count", read_csv_count(REQUEST_TARGETS)),
        "focus_blocker_cell_count": request_payload.get("focus_blocker_cell_count", read_csv_count(FOCUS_CELLS)),
        "required_intake_root": INTAKE_ROOT,
        "required_row_file": f"{INTAKE_ROOT}/native_subhour_source_label_rows.csv",
        "required_provenance_file": f"{INTAKE_ROOT}/native_subhour_source_label_provenance.json",
        "contact_leads": leads,
        "contact_lead_count": len(leads),
        "lead_type_counts": dict(sorted(lead_type_counts.items())),
        "url_probe_ok_count": ok_count,
        "url_probe_blocked_or_error_count": blocked_count,
        "request_sent": False,
        "rows_acquired": False,
        "native_subhour_source_label_intake_files_created": False,
        "accepted_rows_added": 0,
        "new_confidence_gate": False,
        "r3_native_subhour_closed": False,
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "trade_usable": False,
    }

    (OUT_DIR / "native_subhour_contact_leads_v1.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    write_csv(
        OUT_DIR / "native_subhour_contact_leads_v1.csv",
        leads,
        [
            "lead_id",
            "lead_type",
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
        ("prior_request_json_available", payload["prior_request_json_available"] is True),
        ("prior_request_targets_available", payload["prior_request_targets_available"] is True),
        ("prior_focus_cells_available", payload["prior_focus_cells_available"] is True),
        ("prior_request_template_available", payload["prior_request_template_available"] is True),
        ("native_intraday_target_count_336", int(payload["prior_native_intraday_target_count"]) == 336),
        ("focus_blocker_cell_count_4", int(payload["focus_blocker_cell_count"]) == 4),
        ("contact_lead_count_ge_8", len(leads) >= 8),
        ("has_source_label_owner_route", lead_type_counts.get("source_label_owner_extension", 0) >= 1),
        ("has_provider_terms_route", lead_type_counts.get("provider_terms_contact_route", 0) >= 1),
        ("request_sent_false", payload["request_sent"] is False),
        ("rows_acquired_false", payload["rows_acquired"] is False),
        ("accepted_rows_added_zero", payload["accepted_rows_added"] == 0),
        ("r3_closed_false", payload["r3_native_subhour_closed"] is False),
        ("strict_full_objective_achieved_false", payload["strict_full_objective_achieved"] is False),
        ("update_goal_false", payload["update_goal"] is False),
        ("raw_data_committed_false", payload["raw_data_committed"] is False),
    ]
    lines = [f"{name}={'PASS' if passed else 'FAIL'}" for name, passed in assertions]
    (CHECK_DIR / "native_subhour_contact_leads_v1_assertions.out").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if all(passed for _, passed in assertions) else 1


if __name__ == "__main__":
    raise SystemExit(main())
