#!/usr/bin/env python3
"""Public contact-lead package for the Do/Putnins owner-request target."""

from __future__ import annotations

import csv
import json
from pathlib import Path


RUN_ID = "20260511T201759-codex-do-putnins-contact-leads-v1"
RUN_ROOT = Path("docs/experiments/actionable-regime-confidence/runs") / RUN_ID
OUT_DIR = RUN_ROOT / "do-putnins-contact-leads"
CHECK_DIR = RUN_ROOT / "checks"

SOURCE_TARGET = {
    "target_id": "do_putnins_2023_detecting_layering_spoofing",
    "paper_title": "Detecting Layering and Spoofing in Markets",
    "primary_source_url": "https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4525036",
    "prior_request_package": "docs/experiments/actionable-regime-confidence/runs/20260511T201352-codex-do-putnins-owner-request-package-v1/do-putnins-owner-request-package/do_putnins_owner_request_template_v1.md",
    "required_intake_root": "/tmp/ict-engine-direct-manipulation-row-intake",
}

CONTACT_LEADS = [
    {
        "lead_id": "ssrn_author_email_links",
        "contact_surface": "SSRN abstract page author email links",
        "url": "https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4525036",
        "intended_use": "Use the page's public author email links to send the owner-request template.",
        "status": "ready_contact_surface_no_rows_acquired",
        "privacy_boundary": "Use only public SSRN/institutional contact surfaces; do not scrape private addresses.",
    },
    {
        "lead_id": "ssrn_contact_author",
        "contact_surface": "SSRN contact author listing for Bao Linh Do",
        "url": "https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4525036",
        "intended_use": "Ask whether an owner-approved, redacted positive/control row package can be exported for Board A verifier intake.",
        "status": "ready_contact_surface_no_rows_acquired",
        "privacy_boundary": "Contact path is public on the SSRN record; no request was sent by this run.",
    },
    {
        "lead_id": "uts_talis_putnins_profile",
        "contact_surface": "UTS public profile for Talis Putnins",
        "url": "https://profiles.uts.edu.au/talis.putnins",
        "intended_use": "Secondary author/institutional route if SSRN author email links are unavailable.",
        "status": "ready_contact_surface_no_rows_acquired",
        "privacy_boundary": "Use public institutional profile/contact route only.",
    },
    {
        "lead_id": "repec_author_record",
        "contact_surface": "RePEc author-paper record",
        "url": "https://ideas.repec.org/p/arx/papers/2308.00198.html",
        "intended_use": "Bibliographic fallback to confirm paper identity and author linkage before sending the request.",
        "status": "bibliographic_fallback_no_rows_acquired",
        "privacy_boundary": "Use as identity/source confirmation only.",
    },
]


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)

    result = {
        "run_id": RUN_ID,
        "decision": "do_putnins_contact_leads_v1=public_contact_paths_ready_rows_not_acquired",
        "source_target": SOURCE_TARGET,
        "contact_leads": CONTACT_LEADS,
        "contact_lead_count": len(CONTACT_LEADS),
        "request_template_available": True,
        "request_sent": False,
        "rows_acquired": False,
        "accepted_rows_added": 0,
        "new_confidence_gate": False,
        "ready_spoofing_layering_intake_source": False,
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "trade_usable": False,
    }

    json_path = OUT_DIR / "do_putnins_contact_leads_v1.json"
    csv_path = OUT_DIR / "do_putnins_contact_leads_v1.csv"
    md_path = OUT_DIR / "do_putnins_contact_leads_v1.md"
    assertions_path = CHECK_DIR / "do_putnins_contact_leads_v1_assertions.out"

    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    with csv_path.open("w", newline="") as handle:
        fields = ["lead_id", "contact_surface", "url", "intended_use", "status", "privacy_boundary"]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for lead in CONTACT_LEADS:
            writer.writerow({field: lead[field] for field in fields})

    lines = [
        "# Do/Putnins Contact Leads v1",
        "",
        f"Run ID: `{RUN_ID}`",
        "",
        f"- Gate result: `{result['decision']}`.",
        "- Purpose: turn the `201352` owner-request template into executable public contact leads for the closest R6 spoofing/layering owner target.",
        "- Request sent: `false`; rows acquired: `false`; accepted rows added: `0`.",
        "- Strict full objective achieved: `false`; `update_goal=false`.",
        "",
        "## Source Target",
        "",
        f"- Target: `{SOURCE_TARGET['target_id']}` / `{SOURCE_TARGET['paper_title']}`.",
        f"- Primary source: {SOURCE_TARGET['primary_source_url']}.",
        f"- Request template: `{SOURCE_TARGET['prior_request_package']}`.",
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
            "This run does not send a request and does not create intake rows. It only identifies public contact surfaces for a human or authenticated follow-up. Rows remain unacceptable until an owner-approved package lands under `/tmp/ict-engine-direct-manipulation-row-intake` and passes the existing verifier.",
            "",
            "## Artifacts",
            "",
            f"- JSON: `{json_path}`",
            f"- Contact CSV: `{csv_path}`",
            f"- Assertions: `{assertions_path}`",
        ]
    )
    md_path.write_text("\n".join(lines) + "\n")

    checks = [
        ("decision", result["decision"] == "do_putnins_contact_leads_v1=public_contact_paths_ready_rows_not_acquired", result["decision"]),
        ("contact_lead_count", result["contact_lead_count"] >= 4, str(result["contact_lead_count"])),
        ("request_template_available", result["request_template_available"] is True, "true"),
        ("request_sent", result["request_sent"] is False, "false"),
        ("rows_acquired", result["rows_acquired"] is False, "false"),
        ("accepted_rows_added", result["accepted_rows_added"] == 0, "0"),
        ("strict_full_objective_achieved", result["strict_full_objective_achieved"] is False, "false"),
        ("update_goal", result["update_goal"] is False, "false"),
    ]
    ok = True
    assertion_lines = []
    for name, passed, value in checks:
        ok = ok and passed
        assertion_lines.append(f"{'PASS' if passed else 'FAIL'} {name}={value}")
    assertions_path.write_text("\n".join(assertion_lines) + "\n")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
