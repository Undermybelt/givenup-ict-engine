#!/usr/bin/env python3
"""Assess whether available bulk sources can close R6 exact split debt."""

from __future__ import annotations

import csv
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


RUN_ID = "20260512T001229-codex-r6-bulk-source-feasibility-scan-v1"
REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs" / RUN_ID
OUT = RUN_ROOT / "r6-bulk-source-feasibility-scan"
CHECKS = RUN_ROOT / "checks"
CMD = RUN_ROOT / "command-output"
BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"
DIRECT_INTAKE = Path("/tmp/ict-engine-direct-manipulation-row-intake")
DIRECT_VERIFIER = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs"
    / "20260511T151950-codex-direct-manipulation-row-intake-manifest-v1"
    / "direct-manipulation-intake/direct_manipulation_row_intake_verifier_v1.py"
)
V59_JSON = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs"
    / "20260512T000801-codex-r6-exact-split-support-debt-audit-v1"
    / "r6-exact-split-support-debt-audit/r6_exact_split_support_debt_audit_v1.json"
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO))
    except ValueError:
        return str(path)


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def run_verifier() -> dict[str, Any]:
    proc = subprocess.run(
        [sys.executable, str(DIRECT_VERIFIER), "--intake-root", str(DIRECT_INTAKE)],
        cwd=REPO,
        text=True,
        capture_output=True,
        check=False,
        timeout=60,
    )
    (CMD / "direct_manipulation_row_intake_verifier.stdout.txt").write_text(proc.stdout, encoding="utf-8")
    (CMD / "direct_manipulation_row_intake_verifier.stderr.txt").write_text(proc.stderr, encoding="utf-8")
    (CMD / "direct_manipulation_row_intake_verifier.exit").write_text(f"{proc.returncode}\n", encoding="utf-8")
    try:
        parsed = json.loads(proc.stdout)
    except json.JSONDecodeError:
        parsed = {"status": "unparsed", "returncode": proc.returncode}
    parsed["returncode"] = proc.returncode
    return parsed


def source_rows() -> list[dict[str, object]]:
    return [
        {
            "source_id": "finra_potential_manipulation_report",
            "source_url": "https://www.finra.org/compliance-tools/report-center/cross-market-equities-supervision/potential-manipulation-report",
            "source_kind": "regulator_member_report",
            "access_state": "authenticated_member_export_required",
            "bulk_rows": True,
            "source_owned_positive_labels": True,
            "matched_negative_or_review_context": True,
            "current_r6_exact_bucket_fit": "equities_not_current_futures_buckets",
            "ready_now_without_owner_export": False,
            "could_close_after_owner_export": True,
            "blocker": "Requires owner/firm FINRA Report Center export; asset class is equities, so current futures exact-symbol/venue buckets would need a predeclared cross-market direct-Manipulation mapping.",
        },
        {
            "source_id": "cftc_public_market_data_and_enforcement_pdfs",
            "source_url": "https://www.cftc.gov/data",
            "source_kind": "public_regulator_reports",
            "access_state": "public",
            "bulk_rows": False,
            "source_owned_positive_labels": True,
            "matched_negative_or_review_context": False,
            "current_r6_exact_bucket_fit": "case_examples_only",
            "ready_now_without_owner_export": False,
            "could_close_after_owner_export": False,
            "blocker": "Public CFTC pages provide reports and enforcement PDFs, but not a downloadable balanced order-lifecycle export with hundreds of matched labeled spoof/non-spoof rows.",
        },
        {
            "source_id": "tardis_exchange_order_book_data",
            "source_url": "https://docs.tardis.dev/historical-data-details",
            "source_kind": "commercial_exchange_l2_trades",
            "access_state": "commercial_or_existing_account",
            "bulk_rows": True,
            "source_owned_positive_labels": False,
            "matched_negative_or_review_context": True,
            "current_r6_exact_bucket_fit": "controls_or_weak_labels_only",
            "ready_now_without_owner_export": False,
            "could_close_after_owner_export": False,
            "blocker": "Can supply depth/trade/order-book style bulk controls, but does not source-own spoofing/manipulation positives required by the direct evidence gate.",
        },
        {
            "source_id": "polymarket_l2_orderbook_kaggle",
            "source_url": "https://www.kaggle.com/datasets/kylebeauchamp/high-frequency-polymarket-orderbook-data",
            "source_kind": "public_market_l2_dataset",
            "access_state": "kaggle_access_required",
            "bulk_rows": True,
            "source_owned_positive_labels": False,
            "matched_negative_or_review_context": True,
            "current_r6_exact_bucket_fit": "prediction_market_controls_or_weak_labels_only",
            "ready_now_without_owner_export": False,
            "could_close_after_owner_export": False,
            "blocker": "Bulk L2/order-book data is useful for controls or research, but it is not source-owned manipulation-positive labeling for current R6 futures/order-lifecycle exact buckets.",
        },
        {
            "source_id": "brogaard_hendershott_riordan_spoofing_study",
            "source_url": "https://www.ecb.europa.eu/pub/conferences/shared/pdf/20231109_markets/Brogaard_paper_2023.pdf",
            "source_kind": "academic_proprietary_regulatory_data_evidence",
            "access_state": "not_public_row_export",
            "bulk_rows": True,
            "source_owned_positive_labels": True,
            "matched_negative_or_review_context": True,
            "current_r6_exact_bucket_fit": "evidence_that_needed_source_is_proprietary",
            "ready_now_without_owner_export": False,
            "could_close_after_owner_export": False,
            "blocker": "Study indicates the relevant order-level manipulation evidence exists in proprietary/regulatory data, but does not provide a public row export for Board A ingestion.",
        },
    ]


def main() -> int:
    for path in (OUT, CHECKS, CMD):
        path.mkdir(parents=True, exist_ok=True)

    v59 = json.loads(V59_JSON.read_text(encoding="utf-8"))
    verifier_payload = run_verifier()
    rows = source_rows()
    ready_now = [row for row in rows if row["ready_now_without_owner_export"]]
    owner_export_candidates = [row for row in rows if row["could_close_after_owner_export"]]
    bulk_unlabeled = [
        row
        for row in rows
        if row["bulk_rows"] and not row["source_owned_positive_labels"]
    ]
    decision = "r6_bulk_source_feasibility_scan_v1=no_public_ready_bulk_export_finra_owner_export_or_contract_reset_required"
    result = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "board_sha256_at_start": sha256(BOARD),
        "v59_source": rel(V59_JSON),
        "direct_verifier": verifier_payload,
        "v59_gate_result": v59["decision"]["gate_result"],
        "v59_debt_summary": v59["debt_summary"],
        "support_floor_for_all_correct_wilson95": v59["support_floor_for_all_correct_wilson95"],
        "sources_screened": rows,
        "ready_now_source_count": len(ready_now),
        "owner_export_candidate_count": len(owner_export_candidates),
        "bulk_unlabeled_source_count": len(bulk_unlabeled),
        "decision": decision,
        "accepted_rows_added": 0,
        "new_confidence_gate": False,
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "shared_intake_mutated": False,
        "external_requests_sent_by_script": False,
        "trade_usable": False,
        "next_action": "For R6 exact split closure, acquire an owner-approved FINRA-style or exchange/regulator bulk row export with labels and matched review context; otherwise stop R6 exact-bucket acceptance work and ask for/record a new family-level split contract before any acceptance rerun.",
    }
    fields = [
        "source_id",
        "source_url",
        "source_kind",
        "access_state",
        "bulk_rows",
        "source_owned_positive_labels",
        "matched_negative_or_review_context",
        "current_r6_exact_bucket_fit",
        "ready_now_without_owner_export",
        "could_close_after_owner_export",
        "blocker",
    ]
    write_csv(OUT / "r6_bulk_source_feasibility_sources_v1.csv", rows, fields)
    json_path = OUT / "r6_bulk_source_feasibility_scan_v1.json"
    report_path = OUT / "r6_bulk_source_feasibility_scan_v1.md"
    assertions_path = CHECKS / "r6_bulk_source_feasibility_scan_v1_assertions.out"
    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    lines = [
        "# R6 Bulk Source Feasibility Scan v1",
        "",
        f"- Run id: `{RUN_ID}`",
        f"- V59 debt source: `{rel(V59_JSON)}`",
        f"- Direct verifier status: `{verifier_payload.get('status')}`; positives `{verifier_payload.get('positive_rows')}`, matched negatives `{verifier_payload.get('matched_negative_rows')}`.",
        f"- V59 chronological additional-row debt: `{v59['debt_summary']['additional_positive_rows_for_chrono_quantiles_before_symbol_venue']}` before exact symbol/venue gates.",
        f"- V59 exact-symbol pairwise debt: `{v59['debt_summary']['exact_symbol_pairwise_debt_if_current_buckets_must_all_pass']}`; exact-venue pairwise debt: `{v59['debt_summary']['exact_venue_pairwise_debt_if_current_buckets_must_all_pass']}`.",
        f"- Sources screened: `{len(rows)}`; ready-now public bulk source count: `{len(ready_now)}`; owner-export candidate count: `{len(owner_export_candidates)}`.",
        f"- Gate result: `{decision}`.",
        "- Strict full objective achieved: `false`; `update_goal=false`.",
        "- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; shared intake mutated: `false`; trade usable: `false`.",
        "",
        "## Source Decisions",
        "",
        "| Source | Ready Now | Owner Export Candidate | R6 Fit | Blocker |",
        "|---|---:|---:|---|---|",
    ]
    for row in rows:
        lines.append(
            "| `{}` | `{}` | `{}` | `{}` | {} |".format(
                row["source_id"],
                str(row["ready_now_without_owner_export"]).lower(),
                str(row["could_close_after_owner_export"]).lower(),
                row["current_r6_exact_bucket_fit"],
                row["blocker"],
            )
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- No unauthenticated/public source in this bounded screen is ready to close the current R6 exact chronological/symbol/venue gates.",
            "- FINRA Potential Manipulation Report is the only credible bulk labeled-source candidate, but it requires owner/firm export and likely a predeclared equities-to-direct-Manipulation validation mapping.",
            "- Tardis and Polymarket-style L2/order-book datasets can help build controls or weak-label research, but they do not source-own the manipulation-positive labels required by the current Board A direct evidence gate.",
            "- Existing public CFTC PDFs remain useful for precise row examples, not for the hundreds to thousands of matched rows quantified by V59.",
            "",
            "## Artifacts",
            f"- JSON: `{rel(json_path)}`",
            f"- Report: `{rel(report_path)}`",
            f"- Source CSV: `{rel(OUT / 'r6_bulk_source_feasibility_sources_v1.csv')}`",
            f"- Verifier stdout: `{rel(CMD / 'direct_manipulation_row_intake_verifier.stdout.txt')}`",
            f"- Assertions: `{rel(assertions_path)}`",
            "",
        ]
    )
    report_path.write_text("\n".join(lines), encoding="utf-8")
    assertions = {
        "v59_loaded": v59["decision"]["gate_result"].startswith("r6_exact_split_support_debt_audit_v1="),
        "direct_verifier_schema_ready": verifier_payload.get("status") == "schema_ready_unscored",
        "ready_now_sources_zero": len(ready_now) == 0,
        "finra_owner_export_candidate_present": any(row["source_id"] == "finra_potential_manipulation_report" for row in owner_export_candidates),
        "cftc_public_not_ready_bulk": next(row for row in rows if row["source_id"] == "cftc_public_market_data_and_enforcement_pdfs")["ready_now_without_owner_export"] is False,
        "strict_full_objective_not_complete": result["strict_full_objective_achieved"] is False,
        "update_goal_false": result["update_goal"] is False,
    }
    assertions_path.write_text(
        "\n".join(f"{key}={'ok' if value else 'FAIL'}" for key, value in assertions.items()) + "\n",
        encoding="utf-8",
    )
    if not all(assertions.values()):
        return 2
    print(json.dumps({"decision": decision, "ready_now_sources": len(ready_now), "owner_export_candidates": len(owner_export_candidates)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
