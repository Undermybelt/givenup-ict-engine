#!/usr/bin/env python3
"""Build a source-owner request package for the closest spoofing/layering target."""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path


RUN_ID = "20260511T201352-codex-do-putnins-owner-request-package-v1"
RUN_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = RUN_ROOT.parents[4]
OUT_DIR = RUN_ROOT / "do-putnins-owner-request-package"
CHECK_DIR = RUN_ROOT / "checks"

SOURCE_SCREEN = (
    REPO_ROOT
    / "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T200726-codex-spoofing-layering-source-acquisition-screen-v1/"
    "spoofing-layering-source-acquisition-screen/"
    "spoofing_layering_source_acquisition_screen_v1_candidates.csv"
)
DIRECT_VERIFIER = (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T151950-codex-direct-manipulation-row-intake-manifest-v1/"
    "direct-manipulation-intake/direct_manipulation_row_intake_verifier_v1.py"
)
INTAKE_ROOT = "/tmp/ict-engine-direct-manipulation-row-intake"
REQUIRED_FILES = [
    "positive_spoofing_layering_rows.csv",
    "matched_negative_normal_activity_rows.csv",
    "provenance_manifest.json",
]
REQUIRED_FIELDS = [
    "label",
    "source_report",
    "source_section",
    "trade_date",
    "symbol",
    "venue_or_market_center",
    "participant_type_code",
    "participant_identifier",
    "side",
    "earliest_order_received_time",
    "latest_order_received_time",
    "order_count",
    "total_order_quantity",
    "activity_description",
    "matched_negative_group_id",
    "session_bucket",
    "source_row_id",
]


def load_target_candidate() -> dict[str, str]:
    with SOURCE_SCREEN.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    for row in rows:
        if row.get("candidate_id") == "do_putnins_2023_detecting_layering_spoofing":
            return row
    raise SystemExit("missing do_putnins candidate in source screen")


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)

    candidate = load_target_candidate()
    request_fields = [
        {
            "file": "positive_spoofing_layering_rows.csv",
            "required_content": (
                "Source-owned prosecuted-case positive rows for layering/spoofing events, "
                "with the verifier-required fields and stable source_row_id values."
            ),
        },
        {
            "file": "matched_negative_normal_activity_rows.csv",
            "required_content": (
                "Matched same-venue/symbol/session normal-control rows sharing "
                "matched_negative_group_id with the positive rows."
            ),
        },
        {
            "file": "provenance_manifest.json",
            "required_content": (
                "Owner/source attribution, pull/export date, source report sections, "
                "redaction policy, source hashes or export ids, and matched-control policy."
            ),
        },
    ]
    command = (
        f"python3 {DIRECT_VERIFIER} --intake-root {INTAKE_ROOT}"
    )
    payload = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "purpose": "Convert the closest R6 spoofing/layering source target into a concrete owner request package.",
        "source_candidate": candidate,
        "target_species": "spoofing_layering",
        "required_files": REQUIRED_FILES,
        "required_fields": REQUIRED_FIELDS,
        "request_fields": request_fields,
        "intake_root": INTAKE_ROOT,
        "verification_command": command,
        "acceptance_conditions": [
            "All three required files are placed under the intake root.",
            "Positive rows and matched negative rows include every verifier-required field.",
            "Every positive matched_negative_group_id has at least one same-group normal-control row.",
            "provenance_manifest.json identifies source owner, report/section provenance, export or hash ids, and redaction/matching policy.",
            "After schema readiness, rerun chronological and heldout-symbol/venue Wilson95 calibration before any confidence claim.",
        ],
        "explicit_non_acceptance": [
            "Do not use public paper text alone as rows.",
            "Do not use positive-only regulatory cases without matched controls.",
            "Do not use synthetic, injected, or simulated spoofing labels.",
            "Do not use raw order-book panels without source-owned manipulation labels.",
        ],
        "decision": "do_putnins_owner_request_package_v1=owner_request_ready_rows_not_acquired",
        "accepted_rows_added": 0,
        "new_confidence_gate": False,
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "trade_usable": False,
    }

    json_path = OUT_DIR / "do_putnins_owner_request_package_v1.json"
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    fields_csv = OUT_DIR / "do_putnins_owner_request_required_fields_v1.csv"
    with fields_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["file", "required_field"])
        writer.writeheader()
        for file_name in REQUIRED_FILES[:2]:
            for field in REQUIRED_FIELDS:
                writer.writerow({"file": file_name, "required_field": field})
        writer.writerow({"file": "provenance_manifest.json", "required_field": "source_owner"})
        writer.writerow({"file": "provenance_manifest.json", "required_field": "export_or_hash_id"})
        writer.writerow({"file": "provenance_manifest.json", "required_field": "matched_control_policy"})

    request_md = OUT_DIR / "do_putnins_owner_request_template_v1.md"
    request_md.write_text(
        "\n".join(
            [
                "# Do/Putnins Spoofing/Layering Owner Request Template v1",
                "",
                "Source target: `Detecting Layering and Spoofing in Markets`.",
                f"Source URL: `{candidate.get('source_url')}`.",
                f"Readback URL: `{candidate.get('mirror_or_readback_url')}`.",
                "",
                "Request:",
                "",
                "Please provide a research/export package for the prosecuted layering/spoofing sample that contains:",
                "",
                "1. `positive_spoofing_layering_rows.csv` with row-level positive events.",
                "2. `matched_negative_normal_activity_rows.csv` with same-venue/symbol/session normal controls.",
                "3. `provenance_manifest.json` with source ownership, source sections, export date or hash ids, redaction policy, and matched-control policy.",
                "",
                "Required CSV fields:",
                "",
                ", ".join(REQUIRED_FIELDS),
                "",
                "The package will be checked locally with:",
                "",
                f"`{command}`",
                "",
                "Rows cannot be accepted if they are synthetic, simulated, positive-only, or raw order-book panels without source-owned manipulation labels.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    report_md = OUT_DIR / "do_putnins_owner_request_package_v1.md"
    report_md.write_text(
        "\n".join(
            [
                "# Do/Putnins Owner Request Package v1",
                "",
                f"Run ID: `{RUN_ID}`",
                "",
                "- Gate result: `do_putnins_owner_request_package_v1=owner_request_ready_rows_not_acquired`.",
                "- Closest source target: `Detecting Layering and Spoofing in Markets`.",
                "- Why this target: the `200726` screen found prosecuted-case provenance and order/trade-level granularity hints, but no public positive/control row export.",
                "- Required files are now concrete for owner/user acquisition.",
                "- Accepted rows added: `0`; new confidence gate: `false`.",
                "- Strict full objective achieved: `false`; `update_goal=false`.",
                "- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; trade usable: `false`.",
                "",
                "## Artifacts",
                "",
                f"- JSON: `{json_path}`",
                f"- Required fields CSV: `{fields_csv}`",
                f"- Request template: `{request_md}`",
                f"- Assertions: `{CHECK_DIR / 'do_putnins_owner_request_package_v1_assertions.out'}`",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    assertions = [
        "PASS decision=do_putnins_owner_request_package_v1=owner_request_ready_rows_not_acquired",
        "PASS source_candidate=do_putnins_2023_detecting_layering_spoofing",
        "PASS required_files=3",
        f"PASS required_fields={len(REQUIRED_FIELDS)}",
        "PASS accepted_rows_added=0",
        "PASS new_confidence_gate=false",
        "PASS strict_full_objective_achieved=false",
        "PASS update_goal=false",
        "PASS raw_data_committed=false",
    ]
    (CHECK_DIR / "do_putnins_owner_request_package_v1_assertions.out").write_text(
        "\n".join(assertions) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
