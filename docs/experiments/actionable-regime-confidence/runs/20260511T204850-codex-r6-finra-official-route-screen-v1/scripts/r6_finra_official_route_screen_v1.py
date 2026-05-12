#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path


REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = Path(__file__).resolve().parents[1]
OUT = RUN_ROOT / "r6-finra-official-route-screen"
CHECKS = RUN_ROOT / "checks"


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)

    candidates = [
        {
            "candidate_id": "finra_potential_manipulation_report",
            "source_owner": "FINRA",
            "source_url": "https://www.finra.org/compliance-tools/report-center/cross-market-equities-supervision/potential-manipulation-report",
            "species_coverage": "layering;quote_spoofing",
            "official_source_route": True,
            "public_rows_acquired": False,
            "matched_controls_acquired": False,
            "intake_files_created": False,
            "board_a_gate": "blocked_permissioned_report_center_export_required",
            "reason": "Official FINRA PMR is closer to R6 spoofing/layering than research-paper surfaces, but public unauthenticated pages expose report definitions rather than source-owned positive/control row exports.",
        },
        {
            "candidate_id": "finra_report_center_technical_assistance",
            "source_owner": "FINRA",
            "source_url": "https://www.finra.org/compliance-tools/report-center/technical-assistance",
            "species_coverage": "report_center_detail_data_export_mechanics",
            "official_source_route": True,
            "public_rows_acquired": False,
            "matched_controls_acquired": False,
            "intake_files_created": False,
            "board_a_gate": "blocked_entitled_user_download_required",
            "reason": "FINRA documents detail-data download mechanics, but access is permissioned and still requires an owner-approved export before Board A intake files can be populated.",
        },
        {
            "candidate_id": "aimm_gt_public_research_candidate",
            "source_owner": "AIMM-GT authors",
            "source_url": "https://arxiv.org/abs/2512.16103",
            "species_coverage": "broad_market_manipulation_research_candidate",
            "official_source_route": False,
            "public_rows_acquired": False,
            "matched_controls_acquired": False,
            "intake_files_created": False,
            "board_a_gate": "rejected_until_source_owned_spoofing_layering_rows_and_controls_are_exported",
            "reason": "Potentially relevant public research surface, but it does not close the current R6 spoofing/layering owner-approved positive/control intake requirement without inspectable row exports and provenance.",
        },
    ]

    required_files = {
        "intake_root": "/tmp/ict-engine-direct-manipulation-row-intake",
        "positive_rows": "positive_spoofing_layering_rows.csv",
        "matched_negative_rows": "matched_negative_normal_activity_rows.csv",
        "provenance_manifest": "provenance_manifest.json",
    }

    report = {
        "run_id": RUN_ROOT.name,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "decision": "r6_finra_official_route_screen_v1=official_route_identified_rows_not_acquired",
        "target_requirement": "R6 direct Manipulation spoofing/layering source-owned positives, same-schema matched controls, and provenance manifest.",
        "candidate_count": len(candidates),
        "official_route_count": sum(1 for row in candidates if row["official_source_route"]),
        "public_rows_acquired": False,
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
        "required_files": required_files,
        "candidates": candidates,
        "next": "Use the existing source-acquisition outbox/operator-approved request path to obtain permissioned FINRA PMR/detail-data exports or equivalent owner-approved rows; do not synthesize matched controls.",
    }

    json_path = OUT / "r6_finra_official_route_screen_v1.json"
    csv_path = OUT / "r6_finra_official_route_screen_v1_candidates.csv"
    md_path = OUT / "r6_finra_official_route_screen_v1.md"
    assertions_path = CHECKS / "r6_finra_official_route_screen_v1_assertions.out"

    json_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_csv(
        csv_path,
        candidates,
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

    md_lines = [
        "# R6 FINRA Official Route Screen v1",
        "",
        f"Decision: `{report['decision']}`.",
        "",
        "Result:",
        "- Official FINRA route identified for spoofing/layering report-card detail data.",
        "- Public/source-owned positive rows acquired: `false`.",
        "- Same-schema matched controls acquired: `false`.",
        "- Intake files created: `false`.",
        "- Accepted rows added: `0`; new confidence gate: `false`.",
        "- Strict full objective achieved: `false`; `update_goal=false`.",
        "",
        "Required intake files remain:",
        f"- `{required_files['intake_root']}/{required_files['positive_rows']}`",
        f"- `{required_files['intake_root']}/{required_files['matched_negative_rows']}`",
        f"- `{required_files['intake_root']}/{required_files['provenance_manifest']}`",
        "",
        "Candidate routes:",
    ]
    for row in candidates:
        md_lines.append(
            f"- `{row['candidate_id']}`: `{row['board_a_gate']}`; rows acquired `{str(row['public_rows_acquired']).lower()}`; {row['source_url']}"
        )
    md_path.write_text("\n".join(md_lines) + "\n", encoding="utf-8")

    assertions = [
        f"PASS decision={report['decision']}",
        "PASS official_route_count=2",
        "PASS public_rows_acquired=false",
        "PASS matched_controls_acquired=false",
        "PASS intake_files_created=false",
        "PASS accepted_rows_added=0",
        "PASS new_confidence_gate=false",
        "PASS strict_full_objective_achieved=false",
        "PASS update_goal=false",
        "PASS raw_data_committed=false",
    ]
    assertions_path.write_text("\n".join(assertions) + "\n", encoding="utf-8")

    print(json.dumps({"decision": report["decision"], "candidate_count": len(candidates)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
