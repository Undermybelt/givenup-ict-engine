#!/usr/bin/env python3
"""Public contact-lead package for the stock-regime recency owner request."""

from __future__ import annotations

import csv
import json
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


RUN_ID = "20260511T202304-codex-stock-regime-owner-contact-leads-v1"
RUN_ROOT = Path("docs/experiments/actionable-regime-confidence/runs") / RUN_ID
OUT_DIR = RUN_ROOT / "stock-regime-owner-contact-leads"
CHECK_DIR = RUN_ROOT / "checks"

DATASET_REF = "mafaqbhatti/stock-market-regimes-20002026"
DATASET_URL = f"https://www.kaggle.com/datasets/{DATASET_REF}"
KAGGLE_VIEW_API_URL = f"https://www.kaggle.com/api/v1/datasets/view/{DATASET_REF}"
KAGGLE_METADATA_API_URL = f"https://www.kaggle.com/api/v1/datasets/metadata/{DATASET_REF}"

SOURCE_TARGET = {
    "target_id": "mafaqbhatti_stock_market_regimes_2000_2026",
    "dataset_ref": DATASET_REF,
    "dataset_url": DATASET_URL,
    "prior_request_package": (
        "docs/experiments/actionable-regime-confidence/runs/"
        "20260511T201655-codex-stock-regime-owner-recency-request-package-v1/"
        "stock-regime-owner-recency-request-package/"
        "stock_regime_owner_recency_request_template_v1.md"
    ),
    "required_intake_root": "/tmp/ict-engine-source-label-equivalence-intake",
}

CONTACT_LEADS = [
    {
        "lead_id": "kaggle_dataset_page",
        "contact_surface": "Kaggle dataset page",
        "url": DATASET_URL,
        "intended_use": "Use dataset comments/discussion or Kaggle profile route to ask the owner for source-owned R4/R5 rows and provenance.",
        "status": "ready_public_surface_no_rows_acquired",
        "privacy_boundary": "Use only public Kaggle surfaces; do not scrape private contact details.",
    },
    {
        "lead_id": "kaggle_dataset_discussion",
        "contact_surface": "Kaggle dataset discussions/comments route",
        "url": f"{DATASET_URL}/discussion",
        "intended_use": "Post or send the existing owner-request template through the dataset discussion route if available.",
        "status": "ready_public_surface_no_rows_acquired",
        "privacy_boundary": "No request was sent by this run.",
    },
    {
        "lead_id": "kaggle_owner_profile",
        "contact_surface": "Kaggle owner profile",
        "url": "https://www.kaggle.com/mafaqbhatti",
        "intended_use": "Owner identity route for Muhammad Afaq Bhatti before an authenticated request.",
        "status": "ready_public_surface_no_rows_acquired",
        "privacy_boundary": "Use public profile only.",
    },
    {
        "lead_id": "kaggle_collaborator_profile",
        "contact_surface": "Kaggle collaborator profile from dataset metadata",
        "url": "https://www.kaggle.com/zulqarnain11",
        "intended_use": "Secondary public route because Kaggle metadata lists collaborator `zulqarnain11` as READER.",
        "status": "bibliographic_or_secondary_route_no_rows_acquired",
        "privacy_boundary": "Use only the public Kaggle profile surface.",
    },
]


def fetch_metadata() -> dict[str, object]:
    try:
        with urllib.request.urlopen(KAGGLE_VIEW_API_URL, timeout=25) as response:
            view_data = json.load(response)
        with urllib.request.urlopen(KAGGLE_METADATA_API_URL, timeout=25) as response:
            metadata_data = json.load(response)
        info = metadata_data.get("info", {})
        selected = {
            "fetch_status": "ok",
            "view_api_url": KAGGLE_VIEW_API_URL,
            "metadata_api_url": KAGGLE_METADATA_API_URL,
            "ref": DATASET_REF,
            "title": view_data.get("title") or view_data.get("titleNullable") or info.get("title"),
            "subtitle": view_data.get("subtitle") or view_data.get("subtitleNullable") or info.get("subtitle"),
            "ownerName": view_data.get("ownerName") or view_data.get("creatorNameNullable"),
            "ownerRef": view_data.get("ownerRef") or info.get("ownerUser"),
            "lastUpdated": view_data.get("lastUpdated") or view_data.get("lastUpdatedNullable"),
            "downloadCount": view_data.get("downloadCount") or info.get("totalDownloads"),
            "licenseName": view_data.get("licenseName") or view_data.get("licenseNameNullable"),
            "collaborators": info.get("collaborators", []),
        }
    except Exception as exc:  # pragma: no cover - live network guard
        selected = {
            "fetch_status": "error",
            "error": f"{type(exc).__name__}: {exc}",
        }
    return selected


def write_report(payload: dict[str, object]) -> None:
    md_path = OUT_DIR / "stock_regime_owner_contact_leads_v1.md"
    metadata = payload["kaggle_metadata"]
    lines = [
        "# Stock Regime Owner Contact Leads v1",
        "",
        f"Run ID: `{RUN_ID}`",
        "",
        f"- Gate result: `{payload['decision']}`.",
        "- Purpose: make the `201655` R4/R5 owner-request package actionable without inventing rows or contacting anyone from this run.",
        f"- Dataset target: `{DATASET_REF}`.",
        f"- Kaggle metadata fetch status: `{metadata.get('fetch_status')}`.",
        f"- Request sent: `{str(payload['request_sent']).lower()}`; rows acquired: `{str(payload['rows_acquired']).lower()}`; accepted rows added: `{payload['accepted_rows_added']}`.",
        f"- Strict full objective achieved: `{str(payload['strict_full_objective_achieved']).lower()}`; `update_goal={str(payload['update_goal']).lower()}`.",
        "",
        "## Source Metadata",
        "",
        f"- Owner: `{metadata.get('ownerName', '')}` / `{metadata.get('ownerRef', '')}`.",
        f"- Last updated: `{metadata.get('lastUpdated', '')}`.",
        f"- License: `{metadata.get('licenseName', '')}`.",
        f"- Collaborators: `{json.dumps(metadata.get('collaborators', []), ensure_ascii=False)}`.",
        "",
        "## Public Contact Leads",
        "",
    ]
    for lead in CONTACT_LEADS:
        lines.append(
            f"- `{lead['lead_id']}`: {lead['contact_surface']} ({lead['url']}) -> `{lead['status']}`. {lead['intended_use']}"
        )
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "This run does not send a request, download rows, or create `/tmp` intake files. R4/R5 remain blocked until source-owned rows plus provenance are provided under `/tmp/ict-engine-source-label-equivalence-intake` and pass the existing verifier.",
            "",
            "## Artifacts",
            "",
            "- JSON: `stock_regime_owner_contact_leads_v1.json`",
            "- Contact CSV: `stock_regime_owner_contact_leads_v1.csv`",
            "- Assertions: `../checks/stock_regime_owner_contact_leads_v1_assertions.out`",
            "",
        ]
    )
    md_path.write_text("\n".join(lines))


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)
    metadata = fetch_metadata()

    payload: dict[str, object] = {
        "run_id": RUN_ID,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "decision": "stock_regime_owner_contact_leads_v1=public_contact_paths_ready_rows_not_acquired",
        "source_target": SOURCE_TARGET,
        "kaggle_metadata": metadata,
        "contact_leads": CONTACT_LEADS,
        "contact_lead_count": len(CONTACT_LEADS),
        "prior_request_template_available": Path(SOURCE_TARGET["prior_request_package"]).exists(),
        "request_sent": False,
        "rows_acquired": False,
        "source_label_equivalence_intake_files_created": False,
        "accepted_rows_added": 0,
        "new_confidence_gate": False,
        "r4_strict_1h_source_rows_acquired": False,
        "r5_recency_tail_repair_closed": False,
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "trade_usable": False,
    }

    (OUT_DIR / "stock_regime_owner_contact_leads_v1.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n"
    )
    with (OUT_DIR / "stock_regime_owner_contact_leads_v1.csv").open("w", newline="") as handle:
        fields = ["lead_id", "contact_surface", "url", "intended_use", "status", "privacy_boundary"]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for lead in CONTACT_LEADS:
            writer.writerow({field: lead[field] for field in fields})
    write_report(payload)

    assertions = [
        ("metadata_fetch_ok", metadata.get("fetch_status") == "ok"),
        ("dataset_ref_matches", metadata.get("ref") == DATASET_REF),
        ("contact_lead_count_ge_4", len(CONTACT_LEADS) >= 4),
        ("prior_request_template_available", payload["prior_request_template_available"] is True),
        ("request_sent_false", payload["request_sent"] is False),
        ("rows_acquired_false", payload["rows_acquired"] is False),
        ("accepted_rows_added_zero", payload["accepted_rows_added"] == 0),
        ("new_confidence_gate_false", payload["new_confidence_gate"] is False),
        ("strict_full_objective_achieved_false", payload["strict_full_objective_achieved"] is False),
        ("update_goal_false", payload["update_goal"] is False),
        ("raw_data_committed_false", payload["raw_data_committed"] is False),
    ]
    failed = [name for name, ok in assertions if not ok]
    (CHECK_DIR / "stock_regime_owner_contact_leads_v1_assertions.out").write_text(
        "\n".join(f"{name}=PASS" if ok else f"{name}=FAIL" for name, ok in assertions)
        + "\n"
    )
    if failed:
        raise SystemExit(f"failed assertions: {', '.join(failed)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
