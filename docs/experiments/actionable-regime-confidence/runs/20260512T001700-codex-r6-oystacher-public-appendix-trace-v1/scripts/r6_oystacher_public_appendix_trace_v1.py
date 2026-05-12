#!/usr/bin/env python3
"""Supplemental public-source trace for the R6 Oystacher appendix blocker."""

from __future__ import annotations

import csv
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


RUN_ID = "20260512T001700-codex-r6-oystacher-public-appendix-trace-v1"
RUN_ROOT = Path("docs/experiments/actionable-regime-confidence/runs") / RUN_ID
ARTIFACT_DIR = RUN_ROOT / "r6-oystacher-public-appendix-trace"
COMMAND_DIR = RUN_ROOT / "command-output"
CHECK_DIR = RUN_ROOT / "checks"

BOARD_PATH = Path("docs/plans/2026-05-10-actionable-regime-confidence-todo.md")
LIVE_INTAKE_ROOT = Path("/tmp/ict-engine-direct-manipulation-row-intake")
DIRECT_VERIFIER = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T151950-codex-direct-manipulation-row-intake-manifest-v1/"
    "direct-manipulation-intake/direct_manipulation_row_intake_verifier_v1.py"
)
PRIOR_OYSTACHER_JSON = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260512T001237-codex-r6-oystacher-large-source-acquisition-screen-v1/"
    "r6-oystacher-large-source-acquisition-screen/"
    "r6_oystacher_large_source_acquisition_screen_v1.json"
)
PRIOR_BULK_JSON = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260512T001229-codex-r6-bulk-source-feasibility-scan-v1/"
    "r6-bulk-source-feasibility-scan/r6_bulk_source_feasibility_scan_v1.json"
)


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def run_direct_verifier() -> dict:
    command = [
        sys.executable,
        str(DIRECT_VERIFIER),
        "--intake-root",
        str(LIVE_INTAKE_ROOT),
    ]
    proc = subprocess.run(command, text=True, capture_output=True, check=False)
    (COMMAND_DIR / "direct_manipulation_row_intake_verifier.stdout.txt").write_text(
        proc.stdout, encoding="utf-8"
    )
    (COMMAND_DIR / "direct_manipulation_row_intake_verifier.stderr.txt").write_text(
        proc.stderr, encoding="utf-8"
    )
    (COMMAND_DIR / "direct_manipulation_row_intake_verifier.exit").write_text(
        f"{proc.returncode}\n", encoding="utf-8"
    )
    parsed = {}
    if proc.stdout.strip():
        try:
            parsed = json.loads(proc.stdout)
        except json.JSONDecodeError:
            parsed = {"raw_stdout": proc.stdout}
    parsed["returncode"] = proc.returncode
    parsed["command"] = command
    return parsed


def write_sources_csv(path: Path, sources: list[dict]) -> None:
    fieldnames = [
        "source_id",
        "url",
        "source_class",
        "public_access_state",
        "row_appendix_visible",
        "board_a_utility",
        "blocker",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for source in sources:
            writer.writerow({field: source[field] for field in fieldnames})


def write_report(path: Path, payload: dict, sources: list[dict]) -> None:
    direct = payload["direct_verifier"]
    prior = payload["prior_oystacher_screen"]
    debt = payload["v59_debt_summary"]
    lines = [
        "# R6 Oystacher Public Appendix Trace v1",
        "",
        f"- Run id: `{RUN_ID}`.",
        f"- Direct verifier status: `{direct.get('status')}`; positives `{direct.get('positive_rows')}`; matched negatives `{direct.get('matched_negative_rows')}`; matched groups `{direct.get('matched_group_count')}`.",
        f"- Prior Oystacher screen found aggregate source totals: trading days `{prior['totals']['trading_days']}`, flip sequences `{prior['totals']['flip_sequences']}`, spoof orders `{prior['totals']['spoof_orders']}`, spoof contracts `{prior['totals']['spoof_contracts']}`.",
        f"- V59 debt reference still requires chronological additional rows `{debt['additional_positive_rows_for_chrono_quantiles_before_symbol_venue']}` before exact symbol/venue gates; exact-symbol debt `{debt['exact_symbol_pairwise_debt_if_current_buckets_must_all_pass']}`; exact-venue debt `{debt['exact_venue_pairwise_debt_if_current_buckets_must_all_pass']}`.",
        "- Public appendix materialized: `false`.",
        "- Gate result: `r6_oystacher_public_appendix_trace_v1=public_sources_confirm_large_aggregate_but_no_row_appendix_materialized`.",
        "- Accepted rows added: `0`; new confidence gate: `false`; strict full objective achieved: `false`; `update_goal=false`.",
        "- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; shared intake mutated: `false`; trade usable: `false`.",
        "",
        "## Source Trace",
        "",
        "| Source | Row Appendix Visible | Board A Utility | Blocker |",
        "|---|---:|---|---|",
    ]
    for source in sources:
        lines.append(
            f"| `{source['source_id']}` | `{str(source['row_appendix_visible']).lower()}` | {source['board_a_utility']} | {source['blocker']} |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- The Oystacher source remains the most promising public lead because its aggregate counts exceed the current chronological and pairwise debt scale.",
            "- The public materials reviewed here still stop at aggregate counts or source-description level; they do not materialize the row appendix with timestamps/order legs needed for Board A ingestion.",
            "- No sidecar row is accepted by this trace. The next acceptance attempt still needs the actual Exhibit A appendix, an owner-approved equivalent export, or explicit approval for a different heldout contract.",
            "",
            "## Artifacts",
            "",
            f"- JSON: `{ARTIFACT_DIR / 'r6_oystacher_public_appendix_trace_v1.json'}`",
            f"- Source CSV: `{ARTIFACT_DIR / 'r6_oystacher_public_appendix_sources_v1.csv'}`",
            f"- Verifier stdout: `{COMMAND_DIR / 'direct_manipulation_row_intake_verifier.stdout.txt'}`",
            f"- Assertions: `{CHECK_DIR / 'r6_oystacher_public_appendix_trace_v1_assertions.out'}`",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    COMMAND_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)

    prior_oystacher = load_json(PRIOR_OYSTACHER_JSON)
    prior_bulk = load_json(PRIOR_BULK_JSON)
    direct = run_direct_verifier()

    sources = [
        {
            "source_id": "cftc_oystacher_complaint_public_pdf",
            "url": "https://www.cftc.gov/sites/default/files/idc/groups/public/%40lrenforcementactions/documents/legalpleading/enfigorcomplnt101915.pdf",
            "source_class": "official_regulator_complaint",
            "public_access_state": "public_pdf",
            "row_appendix_visible": False,
            "board_a_utility": "confirms source-owned large aggregate row universe and Exhibit A reference",
            "blocker": "public PDF artifact does not expose the row appendix needed for timestamp/order-leg ingestion",
        },
        {
            "source_id": "cftc_oystacher_press_release",
            "url": "https://www.cftc.gov/PressRoom/PressReleases/7253-15",
            "source_class": "official_regulator_press_release",
            "public_access_state": "public_html",
            "row_appendix_visible": False,
            "board_a_utility": "confirms official enforcement context and source identity",
            "blocker": "summary page is not a row-level order-lifecycle export",
        },
        {
            "source_id": "secondary_oystacher_aggregate_table",
            "url": "https://academic.oup.com/cmlj/article/doi/10.1093/cmlj/kmaf012/8257809",
            "source_class": "secondary_legal_academic_summary",
            "public_access_state": "public_page",
            "row_appendix_visible": False,
            "board_a_utility": "corroborates that public discourse preserves aggregate counts, not Board A rows",
            "blocker": "secondary summary cannot source-own positive labels or matched controls",
        },
    ]

    totals = prior_oystacher["market_counts"]["totals"]
    payload = {
        "accepted_rows_added": 0,
        "board_sha256_at_start": file_sha256(BOARD_PATH),
        "direct_verifier": direct,
        "external_requests_sent_by_script": False,
        "gate_result": "r6_oystacher_public_appendix_trace_v1=public_sources_confirm_large_aggregate_but_no_row_appendix_materialized",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "new_confidence_gate": False,
        "next_action": "Acquire the Oystacher Exhibit A row appendix or owner-approved equivalent row export; otherwise record explicit owner approval for a different heldout split contract before another R6 acceptance rerun.",
        "prior_oystacher_screen": {
            "json": str(PRIOR_OYSTACHER_JSON),
            "gate_result": prior_oystacher["gate_result"],
            "appendix_exhibit_a_referenced": prior_oystacher["materialization_assessment"]["appendix_exhibit_a_referenced"],
            "appendix_rows_visible_in_public_pdf": prior_oystacher["materialization_assessment"]["appendix_rows_visible_in_public_pdf"],
            "public_pdf_page_count": prior_oystacher["materialization_assessment"]["public_pdf_page_count"],
            "totals": totals,
        },
        "raw_data_committed": False,
        "row_appendix_materialized": False,
        "run_id": RUN_ID,
        "runtime_code_changed": False,
        "shared_intake_mutated": False,
        "sources": sources,
        "strict_full_objective_achieved": False,
        "thresholds_relaxed": False,
        "trade_usable": False,
        "update_goal": False,
        "v59_debt_summary": prior_bulk["v59_debt_summary"],
        "v59_gate_result": prior_bulk["v59_gate_result"],
    }

    json_path = ARTIFACT_DIR / "r6_oystacher_public_appendix_trace_v1.json"
    csv_path = ARTIFACT_DIR / "r6_oystacher_public_appendix_sources_v1.csv"
    report_path = ARTIFACT_DIR / "r6_oystacher_public_appendix_trace_v1.md"
    assertion_path = CHECK_DIR / "r6_oystacher_public_appendix_trace_v1_assertions.out"

    write_json(json_path, payload)
    write_sources_csv(csv_path, sources)
    write_report(report_path, payload, sources)

    assertions = [
        f"direct_verifier_returncode={direct.get('returncode')}",
        f"direct_verifier_status={direct.get('status')}",
        f"prior_oystacher_appendix_referenced={payload['prior_oystacher_screen']['appendix_exhibit_a_referenced']}",
        f"row_appendix_materialized={payload['row_appendix_materialized']}",
        f"accepted_rows_added={payload['accepted_rows_added']}",
        f"strict_full_objective_achieved={payload['strict_full_objective_achieved']}",
        f"update_goal={payload['update_goal']}",
    ]
    assertion_path.write_text("\n".join(assertions) + "\n", encoding="utf-8")

    print(json.dumps({"run_id": RUN_ID, "json": str(json_path), "report": str(report_path)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
