#!/usr/bin/env python3
"""Append exact Logista/Serotta CFTC complaint rows to the R6 direct intake."""

from __future__ import annotations

import csv
import hashlib
import json
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[6]
RUN_ID = "20260511T220727+0800-codex-r6-logista-serotta-cftc-row-uplift-v1"
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T220727-codex-r6-logista-serotta-cftc-row-uplift-v1"
OUT_DIR = RUN_ROOT / "r6-logista-serotta-cftc-row-uplift"
CHECK_DIR = RUN_ROOT / "checks"
CMD_DIR = RUN_ROOT / "command-output"

BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"
INTAKE_ROOT = Path("/tmp/ict-engine-direct-manipulation-row-intake")
POSITIVE_CSV = INTAKE_ROOT / "positive_spoofing_layering_rows.csv"
NEGATIVE_CSV = INTAKE_ROOT / "matched_negative_normal_activity_rows.csv"
PROVENANCE_JSON = INTAKE_ROOT / "provenance_manifest.json"
VERIFIER = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T151950-codex-direct-manipulation-row-intake-manifest-v1/"
    "direct-manipulation-intake/direct_manipulation_row_intake_verifier_v1.py"
)

SOURCE_URL = "https://www.cftc.gov/media/9206/enflogistaadvisorscomplaint090723/download"
RAW_DIR = Path("/tmp/ict-engine-r6-logista-serotta-cftc-row-uplift-v1/raw")
PDF_PATH = RAW_DIR / "enflogistaadvisorscomplaint090723.pdf"
TEXT_PATH = RAW_DIR / "enflogistaadvisorscomplaint090723.txt"

FIELDS = [
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

SOURCE_REPORT = "CFTC Complaint: Logista Advisors LLC and Andrew Harris Serotta, Case 1:23-cv-07485"
PARTICIPANT_TYPE = "CFTC defendants; CPO/CTA head trader"
PARTICIPANT = "Andrew Harris Serotta / Logista Advisors LLC"


def repo_rel(path: Path) -> str:
    return str(path.relative_to(REPO)) if path.is_relative_to(REPO) else str(path)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def run_command(name: str, args: list[str]) -> dict[str, Any]:
    result = subprocess.run(args, cwd=str(REPO), text=True, capture_output=True, check=False)
    stdout_path = CMD_DIR / f"{name}.stdout.txt"
    stderr_path = CMD_DIR / f"{name}.stderr.txt"
    stdout_path.write_text(result.stdout, encoding="utf-8")
    stderr_path.write_text(result.stderr, encoding="utf-8")
    return {
        "name": name,
        "args": args,
        "returncode": result.returncode,
        "stdout_path": repo_rel(stdout_path),
        "stderr_path": repo_rel(stderr_path),
        "stdout": result.stdout,
        "stderr": result.stderr,
    }


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_rows_atomic(path: Path, rows: list[dict[str, str]]) -> None:
    tmp = path.with_suffix(path.suffix + f".{RUN_ID}.tmp")
    with tmp.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in FIELDS})
    tmp.replace(path)


def logista_rows() -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    positives = [
        {
            "label": "positive_spoofing_layering",
            "source_report": SOURCE_REPORT,
            "source_section": "Complaint paragraphs 69-73, Spoof Event Example 1",
            "trade_date": "2020-01-29",
            "symbol": "CLM0-CLU0 crude oil June-September 2020 calendar spread",
            "venue_or_market_center": "CME/NYMEX",
            "participant_type_code": PARTICIPANT_TYPE,
            "participant_identifier": PARTICIPANT,
            "side": "sell spoof order opposite buy genuine orders",
            "earliest_order_received_time": "12:00:06.610 PM Central Time",
            "latest_order_received_time": "12:00:23.225 PM Central Time",
            "order_count": "one 301-lot spoof order",
            "total_order_quantity": "301 contracts",
            "activity_description": "CFTC complaint describes a 301-contract sell spoof order in the crude oil June-September 2020 calendar spread, followed by buy genuine orders and full cancellation with zero fills.",
            "matched_negative_group_id": "cftc_logista_serotta_20200129_cl_example",
            "session_bucket": "regular_us_central_time",
            "source_row_id": "cftc_logista_serotta_20200129_cl_sell_spoof_order",
        },
        {
            "label": "positive_spoofing_layering",
            "source_report": SOURCE_REPORT,
            "source_section": "Complaint paragraphs 74-77, Spoof Event Example 2",
            "trade_date": "2020-02-20",
            "symbol": "NGH0-NGJ0 natural gas March-April 2020 calendar spread",
            "venue_or_market_center": "CME/NYMEX",
            "participant_type_code": PARTICIPANT_TYPE,
            "participant_identifier": PARTICIPANT,
            "side": "buy spoof order opposite sell genuine orders",
            "earliest_order_received_time": "1:06:29.086 PM Central Time",
            "latest_order_received_time": "1:07:36.935 PM Central Time",
            "order_count": "one 301-lot spoof order",
            "total_order_quantity": "301 contracts",
            "activity_description": "CFTC complaint describes a 301-contract buy spoof order in the natural gas March-April 2020 calendar spread, followed by sell genuine orders and complete cancellation with zero fills.",
            "matched_negative_group_id": "cftc_logista_serotta_20200220_ng_example",
            "session_bucket": "regular_us_central_time",
            "source_row_id": "cftc_logista_serotta_20200220_ng_buy_spoof_order",
        },
        {
            "label": "positive_spoofing_layering",
            "source_report": SOURCE_REPORT,
            "source_section": "Complaint paragraphs 78-81, Spoof Event Example 3",
            "trade_date": "2020-03-11",
            "symbol": "CLM0-CLZ0 crude oil June-December 2020 calendar spread",
            "venue_or_market_center": "CME/NYMEX",
            "participant_type_code": PARTICIPANT_TYPE,
            "participant_identifier": PARTICIPANT,
            "side": "buy spoof order opposite sell genuine orders",
            "earliest_order_received_time": "11:29:48.415 AM Central Time",
            "latest_order_received_time": "11:30:50.876 AM Central Time",
            "order_count": "one 301-lot spoof order",
            "total_order_quantity": "301 contracts",
            "activity_description": "CFTC complaint describes a 301-contract buy spoof order in the crude oil June-December 2020 calendar spread, followed by sell genuine orders and complete cancellation with zero fills.",
            "matched_negative_group_id": "cftc_logista_serotta_20200311_cl_example",
            "session_bucket": "regular_us_central_time",
            "source_row_id": "cftc_logista_serotta_20200311_cl_buy_spoof_order",
        },
    ]
    negatives = [
        {
            "label": "matched_negative_normal_activity",
            "source_report": SOURCE_REPORT,
            "source_section": "Complaint paragraph 72, Spoof Event Example 1 genuine-order leg",
            "trade_date": "2020-01-29",
            "symbol": "CLM0-CLU0 crude oil June-September 2020 calendar spread",
            "venue_or_market_center": "CME/NYMEX",
            "participant_type_code": PARTICIPANT_TYPE,
            "participant_identifier": PARTICIPANT,
            "side": "buy genuine orders",
            "earliest_order_received_time": "12:00:08.033 PM Central Time",
            "latest_order_received_time": "before 12:00:23.225 PM Central Time",
            "order_count": "series of smaller genuine orders",
            "total_order_quantity": "201 contracts involved; 77 contracts filled",
            "activity_description": "Matched same-complaint genuine-order leg. This is a source-described same-event control seed, not a broad normal-market calibration sample.",
            "matched_negative_group_id": "cftc_logista_serotta_20200129_cl_example",
            "session_bucket": "regular_us_central_time",
            "source_row_id": "cftc_logista_serotta_20200129_cl_buy_genuine_orders_control",
        },
        {
            "label": "matched_negative_normal_activity",
            "source_report": SOURCE_REPORT,
            "source_section": "Complaint paragraph 76, Spoof Event Example 2 genuine-order leg",
            "trade_date": "2020-02-20",
            "symbol": "NGH0-NGJ0 natural gas March-April 2020 calendar spread",
            "venue_or_market_center": "CME/NYMEX",
            "participant_type_code": PARTICIPANT_TYPE,
            "participant_identifier": PARTICIPANT,
            "side": "sell genuine orders",
            "earliest_order_received_time": "1:06:39.339 PM Central Time",
            "latest_order_received_time": "before 1:07:36.935 PM Central Time",
            "order_count": "16 genuine orders of 49 lots each",
            "total_order_quantity": "269 contracts filled from 16 genuine orders",
            "activity_description": "Matched same-complaint genuine-order leg. This is a source-described same-event control seed, not a broad normal-market calibration sample.",
            "matched_negative_group_id": "cftc_logista_serotta_20200220_ng_example",
            "session_bucket": "regular_us_central_time",
            "source_row_id": "cftc_logista_serotta_20200220_ng_sell_genuine_orders_control",
        },
        {
            "label": "matched_negative_normal_activity",
            "source_report": SOURCE_REPORT,
            "source_section": "Complaint paragraph 80, Spoof Event Example 3 genuine-order leg",
            "trade_date": "2020-03-11",
            "symbol": "CLM0-CLZ0 crude oil June-December 2020 calendar spread",
            "venue_or_market_center": "CME/NYMEX",
            "participant_type_code": PARTICIPANT_TYPE,
            "participant_identifier": PARTICIPANT,
            "side": "sell genuine orders",
            "earliest_order_received_time": "11:29:54.745 AM Central Time",
            "latest_order_received_time": "before 11:30:50.876 AM Central Time",
            "order_count": "series of sell genuine orders",
            "total_order_quantity": "125 contracts placed; 34 contracts filled",
            "activity_description": "Matched same-complaint genuine-order leg. This is a source-described same-event control seed, not a broad normal-market calibration sample.",
            "matched_negative_group_id": "cftc_logista_serotta_20200311_cl_example",
            "session_bucket": "regular_us_central_time",
            "source_row_id": "cftc_logista_serotta_20200311_cl_sell_genuine_orders_control",
        },
    ]
    return positives, negatives


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)
    CMD_DIR.mkdir(parents=True, exist_ok=True)
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    curl = run_command("curl_logista_complaint", ["curl", "-L", "--fail", "--silent", "--show-error", SOURCE_URL, "-o", str(PDF_PATH)])
    gs = run_command("gs_logista_text", ["gs", "-q", "-dNOPAUSE", "-dBATCH", "-sDEVICE=txtwrite", f"-sOutputFile={TEXT_PATH}", str(PDF_PATH)])
    if curl["returncode"] != 0 or gs["returncode"] != 0:
        raise SystemExit(2)

    text = TEXT_PATH.read_text(encoding="utf-8", errors="replace")
    text_checks = {
        "Spoof Event Example 1": "Spoof Event Example 1: January 29, 2020" in text,
        "12:00:06.610": "12:00:06.610 PM" in text,
        "12:00:23.225": "12:00:23.225 PM" in text,
        "Spoof Event Example 2": "Spoof Event Example 2: February 20, 2020" in text,
        "1:06:29.086": "1:06:29.086 PM" in text,
        "1:07:36.935": "1:07:36.935 PM" in text,
        "Spoof Event Example 3": "Spoof Event Example 3: March 11, 2020" in text,
        "11:29:48.415": "11:29:48.415 AM" in text,
        "11:30:50.876": "11:30:50.876 AM" in text,
        "zero fills": "received zero fills and was completely canceled" in text,
    }
    if not all(text_checks.values()):
        (CHECK_DIR / "r6_logista_serotta_cftc_row_uplift_v1_assertions.out").write_text(
            "assertion_status=FAIL\nmissing_text_checks="
            + ",".join(key for key, ok in text_checks.items() if not ok)
            + "\n",
            encoding="utf-8",
        )
        return 1

    positive_rows = read_rows(POSITIVE_CSV)
    negative_rows = read_rows(NEGATIVE_CSV)
    before_positive = len(positive_rows)
    before_negative = len(negative_rows)
    new_positive_rows, new_negative_rows = logista_rows()
    existing_positive_ids = {row["source_row_id"] for row in positive_rows}
    existing_negative_ids = {row["source_row_id"] for row in negative_rows}
    accepted_positive_rows = [row for row in new_positive_rows if row["source_row_id"] not in existing_positive_ids]
    accepted_negative_rows = [row for row in new_negative_rows if row["source_row_id"] not in existing_negative_ids]

    if accepted_positive_rows:
        write_rows_atomic(POSITIVE_CSV, positive_rows + accepted_positive_rows)
    if accepted_negative_rows:
        write_rows_atomic(NEGATIVE_CSV, negative_rows + accepted_negative_rows)

    provenance = json.loads(PROVENANCE_JSON.read_text(encoding="utf-8"))
    provenance["cftc_logista_serotta_complaint_examples"] = {
        "url": SOURCE_URL,
        "pdf_path": str(PDF_PATH),
        "pdf_sha256": sha256(PDF_PATH),
        "text_path": str(TEXT_PATH),
        "text_sha256": sha256(TEXT_PATH),
        "source_kind": "public CFTC federal complaint",
        "control_boundary": "same-complaint genuine-order legs are schema/control seeds only, not broad normal-market calibration controls",
        "materialized_examples": ["example_1", "example_2", "example_3"],
        "screened_not_materialized": {
            "example_4": "aggregate sequence without clean individual row-level side/timestamp rows",
            "example_5": "IFEU supervision/order-violation example, not included in CEA spoofing count rows",
        },
        "text_checks": text_checks,
        "positive_rows_added_this_run": [row["source_row_id"] for row in accepted_positive_rows],
        "matched_negative_rows_added_this_run": [row["source_row_id"] for row in accepted_negative_rows],
        "rows_materialized_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    provenance["r6_logista_serotta_cftc_row_uplift_v1"] = {
        "positive_rows_added": len(accepted_positive_rows),
        "matched_negative_rows_added": len(accepted_negative_rows),
        "expected_total_positive_rows": before_positive + len(accepted_positive_rows),
        "expected_total_matched_negative_rows": before_negative + len(accepted_negative_rows),
    }
    tmp_provenance = PROVENANCE_JSON.with_suffix(f".json.{RUN_ID}.tmp")
    tmp_provenance.write_text(json.dumps(provenance, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp_provenance.replace(PROVENANCE_JSON)
    shutil.copy2(PROVENANCE_JSON, OUT_DIR / "provenance_manifest_after_logista_serotta_v1.json")

    verifier = run_command("direct_manipulation_row_intake_verifier", ["python3", str(VERIFIER), "--intake-root", str(INTAKE_ROOT)])
    verifier_payload = json.loads(verifier["stdout"])
    after_positive = int(verifier_payload.get("positive_rows", 0) or 0)
    after_negative = int(verifier_payload.get("matched_negative_rows", 0) or 0)

    already_present = (
        not accepted_positive_rows
        and not accepted_negative_rows
        and all(row["source_row_id"] in existing_positive_ids for row in new_positive_rows)
        and all(row["source_row_id"] in existing_negative_ids for row in new_negative_rows)
    )
    expected_new_rows = not already_present
    gate_result = (
        "r6_logista_serotta_cftc_row_uplift_v1=duplicate_already_present_no_new_rows_calibration_still_blocked"
        if already_present
        else "r6_logista_serotta_cftc_row_uplift_v1=three_complaint_examples_added_calibration_still_blocked"
    )

    gate_rows = [
        {"gate": "source_text_checks", "status": "pass" if all(text_checks.values()) else "fail", "evidence": json.dumps(text_checks, sort_keys=True)},
        {"gate": "positive_rows_added_or_already_present", "status": "pass" if already_present or len(accepted_positive_rows) == 3 else "fail", "evidence": f"added={len(accepted_positive_rows)}; already_present={already_present}"},
        {"gate": "matched_negative_rows_added_or_already_present", "status": "pass" if already_present or len(accepted_negative_rows) == 3 else "fail", "evidence": f"added={len(accepted_negative_rows)}; already_present={already_present}"},
        {"gate": "direct_verifier", "status": "pass" if verifier_payload.get("status") == "schema_ready_unscored" else "fail", "evidence": json.dumps(verifier_payload, sort_keys=True)},
        {"gate": "support_50_50", "status": "pass" if after_positive >= 50 and after_negative >= 50 else "fail", "evidence": f"{after_positive}/{after_negative}"},
        {"gate": "broad_normal_sample", "status": "fail", "evidence": "matched controls are same-complaint genuine-order legs only"},
        {"gate": "strict_full_objective", "status": "fail", "evidence": "R6 remains below support/Wilson95/broad-normal/direct-species gates"},
    ]
    with (OUT_DIR / "r6_logista_serotta_cftc_row_uplift_v1_gates.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["gate", "status", "evidence"])
        writer.writeheader()
        writer.writerows(gate_rows)

    intake_summary = {
        "run_id": RUN_ID,
        "artifact_type": "r6_logista_serotta_cftc_row_uplift_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "board": repo_rel(BOARD),
        "board_sha256_at_run": sha256(BOARD),
        "source": {
            "url": SOURCE_URL,
            "pdf_path": str(PDF_PATH),
            "pdf_sha256": sha256(PDF_PATH),
            "text_path": str(TEXT_PATH),
            "text_sha256": sha256(TEXT_PATH),
            "text_checks": text_checks,
        },
        "rows": {
            "positive_rows_before": before_positive,
            "matched_negative_rows_before": before_negative,
            "positive_rows_added": len(accepted_positive_rows),
            "matched_negative_rows_added": len(accepted_negative_rows),
            "positive_rows_after": after_positive,
            "matched_negative_rows_after": after_negative,
            "matched_group_count_after": verifier_payload.get("matched_group_count"),
        },
        "verifier": {
            "path": repo_rel(VERIFIER),
            "stdout_path": verifier["stdout_path"],
            "stderr_path": verifier["stderr_path"],
            "payload": verifier_payload,
        },
        "decision": {
            "gate_result": gate_result,
            "accepted_rows_added": len(accepted_positive_rows) + len(accepted_negative_rows),
            "new_confidence_gate": False,
            "strict_full_objective_achieved": False,
            "update_goal": False,
            "runtime_code_changed": False,
            "thresholds_relaxed": False,
            "raw_data_committed": False,
            "external_requests_sent": True,
            "trade_usable": False,
        },
        "next_action": "Continue R6 direct calibration; support may be above 50/50 after concurrent rows, but Wilson95/broad-normal/direct-species gates remain open.",
    }
    (OUT_DIR / "r6_logista_serotta_cftc_row_uplift_v1.json").write_text(json.dumps(intake_summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report = [
        "# R6 Logista/Serotta CFTC Row Uplift v1",
        "",
        f"Run ID: `{RUN_ID}`",
        "",
        "## Result",
        "",
        f"- Added positive rows: `{len(accepted_positive_rows)}`.",
        f"- Added matched same-complaint genuine-control rows: `{len(accepted_negative_rows)}`.",
        f"- Duplicate/already-present readback: `{already_present}`.",
        f"- Direct verifier after uplift: `{verifier_payload.get('status')}` with positives `{after_positive}`, matched negatives `{after_negative}`, matched groups `{verifier_payload.get('matched_group_count')}`.",
        "- Examples 4 and 5 were screened but not materialized because they are aggregate/supervision-oriented rather than clean row-level Count I spoof rows.",
        "- Same-complaint controls remain schema/control seeds only; broad normal sample is still `false`.",
        f"- Gate result: `{gate_result}`.",
        "- Strict full objective achieved: `false`; `update_goal=false`.",
    ]
    (OUT_DIR / "r6_logista_serotta_cftc_row_uplift_v1.md").write_text("\n".join(report) + "\n", encoding="utf-8")

    failures = []
    if expected_new_rows and len(accepted_positive_rows) != 3:
        failures.append("positive_rows_added_not_3")
    if expected_new_rows and len(accepted_negative_rows) != 3:
        failures.append("matched_negative_rows_added_not_3")
    if verifier_payload.get("status") != "schema_ready_unscored":
        failures.append("direct_verifier_not_schema_ready")
    assertions = [
        f"run_id={RUN_ID}",
        f"board_sha256_at_run={intake_summary['board_sha256_at_run']}",
        f"positive_rows_before={before_positive}",
        f"matched_negative_rows_before={before_negative}",
        f"positive_rows_added={len(accepted_positive_rows)}",
        f"matched_negative_rows_added={len(accepted_negative_rows)}",
        f"already_present={str(already_present).lower()}",
        f"positive_rows_after={after_positive}",
        f"matched_negative_rows_after={after_negative}",
        f"direct_verifier_status={verifier_payload.get('status')}",
        "support_50_50=false",
        "broad_normal_sample=false",
        "runtime_code_changed=false",
        "thresholds_relaxed=false",
        "raw_data_committed=false",
        "strict_full_objective_achieved=false",
        "update_goal=false",
        f"assertion_status={'FAIL' if failures else 'PASS'}",
    ]
    if failures:
        assertions.append("failures=" + ",".join(failures))
    (CHECK_DIR / "r6_logista_serotta_cftc_row_uplift_v1_assertions.out").write_text("\n".join(assertions) + "\n", encoding="utf-8")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
