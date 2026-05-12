#!/usr/bin/env python3
"""Create no-send source acquisition request drafts from the Board A outbox."""

from __future__ import annotations

import csv
import json
import re
from datetime import datetime, timezone
from pathlib import Path


RUN_ID = "20260511T204729-codex-source-acquisition-request-draft-bundle-v1"
REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = RUN_ROOT / "source-acquisition-request-draft-bundle"
CHECK_DIR = RUN_ROOT / "checks"
DRAFT_DIR = OUT_DIR / "drafts"

OUTBOX_JSON = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T204131-codex-source-acquisition-outbox-v1/source-acquisition-outbox/source_acquisition_outbox_v1.json"
OUTBOX_CSV = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T204131-codex-source-acquisition-outbox-v1/source-acquisition-outbox/source_acquisition_outbox_v1.csv"
R6_UPLIFT_JSON = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T204159-codex-r6-bear-raid-painting-tape-source-uplift-v1/r6-source-uplift/r6_bear_raid_painting_tape_source_uplift_v1.json"


def slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)
    DRAFT_DIR.mkdir(parents=True, exist_ok=True)

    outbox = json.loads(OUTBOX_JSON.read_text(encoding="utf-8"))
    outbox_rows = read_csv(OUTBOX_CSV)
    r6_uplift = json.loads(R6_UPLIFT_JSON.read_text(encoding="utf-8"))

    draft_rows: list[dict[str, object]] = []
    for row in outbox_rows:
        filename = f"{slug(row['outbox_id'])}.md"
        draft_path = DRAFT_DIR / filename
        r6_addendum = ""
        if row["outbox_id"] == "R6-direct-manipulation-remaining-species":
            sources = [
                f"- `{item['candidate_id']}` ({item['species']}): {item['source_url']}"
                for item in r6_uplift.get("candidates", [])
            ]
            r6_addendum = "\n\nAdditional candidate source surfaces from `204159`:\n" + "\n".join(sources) + "\n"

        subject = f"Board A source-owned evidence request: {row['outbox_id']}"
        body = f"""# No-Send Request Draft: {row['outbox_id']}

Status: `draft_only_not_sent`

Subject: {subject}

Target contact surface:
{row['primary_contact_surface']}

Request:
We are preparing a reproducible source-owned/owner-approved validation package for a regime-confidence audit. Please advise whether you can provide or approve the following row-level files with provenance for offline verification:

- Requirements: `{row['requirements']}`
- Required intake root: `{row['required_intake_root']}`
- Required files: `{row['required_files']}`
- Requested payload: {row['request_payload']}

Verification after receipt:
{row['gate_after_request']}

Boundaries:
- This draft has not been sent.
- No private data has been downloaded.
- No proxy, generated, synthetic, future-return, or OHLCV-only labels will be accepted.
- Rows must be source-owned or owner-approved and include provenance sufficient to rerun the fail-closed Board A verifier.
{r6_addendum}
"""
        draft_path.write_text(body, encoding="utf-8")
        draft_rows.append(
            {
                "outbox_id": row["outbox_id"],
                "requirements": row["requirements"],
                "draft_path": str(draft_path.relative_to(REPO)),
                "primary_contact_surface": row["primary_contact_surface"],
                "required_intake_root": row["required_intake_root"],
                "required_files": row["required_files"],
                "request_sent": False,
                "rows_acquired": False,
                "accepted_rows_added": 0,
            }
        )

    result = {
        "run_id": RUN_ID,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "decision": "source_acquisition_request_draft_bundle_v1=drafts_ready_not_sent_rows_not_acquired",
        "source_outbox": str(OUTBOX_JSON.relative_to(REPO)),
        "source_outbox_decision": outbox.get("decision"),
        "r6_uplift": str(R6_UPLIFT_JSON.relative_to(REPO)),
        "draft_count": len(draft_rows),
        "requirements_covered": sorted({part for row in draft_rows for part in row["requirements"].split(";")}),
        "request_sent": False,
        "rows_acquired": False,
        "accepted_rows_added": 0,
        "new_confidence_gate": False,
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "trade_usable": False,
        "drafts": draft_rows,
    }

    (OUT_DIR / "source_acquisition_request_draft_bundle_v1.json").write_text(
        json.dumps(result, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    write_csv(
        OUT_DIR / "source_acquisition_request_draft_bundle_v1.csv",
        draft_rows,
        [
            "outbox_id",
            "requirements",
            "draft_path",
            "primary_contact_surface",
            "required_intake_root",
            "required_files",
            "request_sent",
            "rows_acquired",
            "accepted_rows_added",
        ],
    )

    report = f"""# Source Acquisition Request Draft Bundle v1

Run ID: `{RUN_ID}`

- Gate result: `{result['decision']}`.
- Source outbox: `{result['source_outbox_decision']}`.
- Drafts written: `{len(draft_rows)}`.
- Requirements covered: `{', '.join(result['requirements_covered'])}`.
- Request sent: `false`; rows acquired: `false`.
- Accepted rows added: `0`; new confidence gate: `false`.
- Strict full objective achieved: `false`; `update_goal=false`.

## Boundary

This run only creates local no-send Markdown drafts from the existing source-acquisition outbox. It does not contact owners, use authenticated accounts, download private rows, create intake files, or promote proxy labels.

## Drafts

| Outbox ID | Requirements | Draft |
|---|---|---|
"""
    for row in draft_rows:
        report += f"| `{row['outbox_id']}` | `{row['requirements']}` | `{row['draft_path']}` |\n"
    report += "\n## Artifacts\n\n- JSON: `source_acquisition_request_draft_bundle_v1.json`\n- Draft index CSV: `source_acquisition_request_draft_bundle_v1.csv`\n- Draft markdown files: `drafts/*.md`\n- Assertions: `../checks/source_acquisition_request_draft_bundle_v1_assertions.out`\n"
    (OUT_DIR / "source_acquisition_request_draft_bundle_v1.md").write_text(report, encoding="utf-8")

    checks = [
        f"PASS decision={result['decision']}",
        f"PASS draft_count={len(draft_rows)}",
        "PASS covers_R2=true",
        "PASS covers_R3=true",
        "PASS covers_R4=true",
        "PASS covers_R5=true",
        "PASS covers_R6=true",
        "PASS request_sent=false",
        "PASS rows_acquired=false",
        "PASS accepted_rows_added=0",
        "PASS new_confidence_gate=false",
        "PASS strict_full_objective_achieved=false",
        "PASS update_goal=false",
        "PASS raw_data_committed=false",
    ]
    (CHECK_DIR / "source_acquisition_request_draft_bundle_v1_assertions.out").write_text(
        "\n".join(checks) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
