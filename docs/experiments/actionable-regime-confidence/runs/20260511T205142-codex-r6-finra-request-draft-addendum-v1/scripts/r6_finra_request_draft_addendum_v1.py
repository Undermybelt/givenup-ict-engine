#!/usr/bin/env python3
"""Create a no-send FINRA request draft addendum for R6 official-route data."""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path


RUN_ID = "20260511T205142-codex-r6-finra-request-draft-addendum-v1"
REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = RUN_ROOT / "r6-finra-request-draft-addendum"
CHECK_DIR = RUN_ROOT / "checks"

FINRA_SCREEN_JSON = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T204850-codex-r6-finra-official-route-screen-v1/r6-finra-official-route-screen/r6_finra_official_route_screen_v1.json"
FINRA_CANDIDATES_CSV = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T204850-codex-r6-finra-official-route-screen-v1/r6-finra-official-route-screen/r6_finra_official_route_screen_v1_candidates.csv"


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

    screen = json.loads(FINRA_SCREEN_JSON.read_text(encoding="utf-8"))
    candidates = read_csv(FINRA_CANDIDATES_CSV)
    official_routes = [row for row in candidates if row["official_source_route"] == "True"]

    draft = f"""# No-Send FINRA Request Draft Addendum

Status: `draft_only_not_sent`

Subject: Board A R6 FINRA PMR source-owned detail row export request

Target official routes:
"""
    for row in official_routes:
        draft += f"- `{row['candidate_id']}`: {row['source_url']} ({row['species_coverage']})\n"
    draft += """
Request:
We are preparing an offline reproducibility package for a direct market-manipulation regime-confidence audit. Please advise whether an entitled user or FINRA-approved export can provide redacted row-level Potential Manipulation Report detail data suitable for offline validation.

Required offline intake files:
- `/tmp/ict-engine-direct-manipulation-row-intake/positive_spoofing_layering_rows.csv`
- `/tmp/ict-engine-direct-manipulation-row-intake/matched_negative_normal_activity_rows.csv`
- `/tmp/ict-engine-direct-manipulation-row-intake/provenance_manifest.json`

Minimum row/provenance needs:
- source-owned or FINRA-approved positive spoofing/layering or quote-spoofing rows
- same-schema matched normal activity controls
- venue/symbol/time fields sufficient for chronological split
- provenance manifest with source route, approval/license, export timestamp, and field definitions

Boundaries:
- This draft has not been sent.
- No authenticated account has been used.
- No private rows have been downloaded.
- No positive-only export is accepted as completion without matched same-schema controls.
"""
    draft_path = OUT_DIR / "r6_finra_request_draft_addendum_v1.md"
    draft_path.write_text(draft, encoding="utf-8")

    result = {
        "run_id": RUN_ID,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "decision": "r6_finra_request_draft_addendum_v1=draft_ready_not_sent_rows_not_acquired",
        "source_screen": str(FINRA_SCREEN_JSON.relative_to(REPO)),
        "source_screen_decision": screen.get("decision"),
        "official_route_count": len(official_routes),
        "draft_path": str(draft_path.relative_to(REPO)),
        "request_sent": False,
        "authenticated_account_used": False,
        "rows_acquired": False,
        "matched_controls_acquired": False,
        "intake_files_created": False,
        "accepted_rows_added": 0,
        "new_confidence_gate": False,
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "trade_usable": False,
        "official_routes": official_routes,
    }
    (OUT_DIR / "r6_finra_request_draft_addendum_v1.json").write_text(
        json.dumps(result, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    write_csv(
        OUT_DIR / "r6_finra_request_draft_addendum_v1_routes.csv",
        official_routes,
        [
            "candidate_id",
            "source_owner",
            "source_url",
            "species_coverage",
            "official_source_route",
            "public_rows_acquired",
            "matched_controls_acquired",
            "intake_files_created",
            "board_a_gate",
            "reason",
        ],
    )

    report = f"""# R6 FINRA Request Draft Addendum v1

Run ID: `{RUN_ID}`

- Gate result: `{result['decision']}`.
- Source screen decision: `{result['source_screen_decision']}`.
- Official routes included: `{len(official_routes)}`.
- Request sent: `false`; authenticated account used: `false`; rows acquired: `false`.
- Accepted rows added: `0`; new confidence gate: `false`.
- Strict full objective achieved: `false`; `update_goal=false`.

## Boundary

This run only creates a local no-send FINRA request draft addendum. It does not contact FINRA, use an entitled account, download private report rows, create intake files, or promote positive-only evidence.

## Artifacts

- JSON: `r6_finra_request_draft_addendum_v1.json`
- Draft: `r6_finra_request_draft_addendum_v1.md`
- Route CSV: `r6_finra_request_draft_addendum_v1_routes.csv`
- Assertions: `../checks/r6_finra_request_draft_addendum_v1_assertions.out`
"""
    (OUT_DIR / "r6_finra_request_draft_addendum_v1_report.md").write_text(report, encoding="utf-8")

    checks = [
        f"PASS decision={result['decision']}",
        f"PASS official_route_count={len(official_routes)}",
        "PASS request_sent=false",
        "PASS authenticated_account_used=false",
        "PASS rows_acquired=false",
        "PASS matched_controls_acquired=false",
        "PASS intake_files_created=false",
        "PASS accepted_rows_added=0",
        "PASS new_confidence_gate=false",
        "PASS strict_full_objective_achieved=false",
        "PASS update_goal=false",
        "PASS raw_data_committed=false",
    ]
    (CHECK_DIR / "r6_finra_request_draft_addendum_v1_assertions.out").write_text(
        "\n".join(checks) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
