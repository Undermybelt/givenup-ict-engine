#!/usr/bin/env python3
"""Append source-owned CFTC Logista/Franko rows to the R6 direct intake."""

from __future__ import annotations

import csv
import hashlib
import json
import math
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


RUN_ID = "20260511T221034-codex-r6-logista-franko-row-uplift-v1"
REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = Path(__file__).resolve().parents[1]
OUT = RUN_ROOT / "r6-logista-franko-row-uplift"
CHECKS = RUN_ROOT / "checks"
CMD = RUN_ROOT / "command-output"
INTAKE = Path("/tmp/ict-engine-direct-manipulation-row-intake")
POSITIVE = INTAKE / "positive_spoofing_layering_rows.csv"
NEGATIVE = INTAKE / "matched_negative_normal_activity_rows.csv"
PROVENANCE = INTAKE / "provenance_manifest.json"
LOCK = INTAKE / ".r6_logista_franko_row_uplift_v1.lock"
VERIFIER = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T151950-codex-direct-manipulation-row-intake-manifest-v1/"
    "direct-manipulation-intake/direct_manipulation_row_intake_verifier_v1.py"
)
LOGISTA_PDF = Path("/tmp/ict-engine-r6-logista-source/enflogistaadvisorscomplaint090723.pdf")
LOGISTA_TEXT = Path("/tmp/ict-engine-r6-logista-source/logista.txt")
FRANKO_PDF = Path("/tmp/ict-engine-r6-franko-source/enfmichaeldfrankoorder091918.pdf")
FRANKO_TEXT = Path("/tmp/ict-engine-r6-franko-source/enfmichaeldfrankoorder091918.txt")

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
Z95 = 1.959963984540054

LOGISTA_REPORT = "CFTC Complaint: Logista Advisors LLC and Andrew Harris Serotta, Case 1:23-cv-07485"
FRANKO_REPORT = "CFTC Order: Michael D. Franko, CFTC Docket No. 18-35"
CONTROL_LIMITATION = (
    "Same-source genuine-order leg from a public CFTC complaint/order; schema/control seed only, "
    "not an independent broad normal-market calibration sample."
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != FIELDS:
            raise SystemExit(f"unexpected_csv_header:{path}:{reader.fieldnames}")
        return list(reader)


def write_csv(path: Path, rows: list[dict[str, str]], fields: list[str] = FIELDS) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows([{field: row.get(field, "") for field in fields} for row in rows])


def wilson_all_success_lcb(n: int) -> float:
    if n <= 0:
        return 0.0
    denominator = 1.0 + Z95 * Z95 / n
    center = 1.0 + Z95 * Z95 / (2.0 * n)
    margin = Z95 * math.sqrt(Z95 * Z95 / (4.0 * n * n))
    return (center - margin) / denominator


def acquire_lock() -> None:
    fd = os.open(str(LOCK), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        handle.write(datetime.now(timezone.utc).isoformat() + "\n")


def release_lock() -> None:
    try:
        LOCK.unlink()
    except FileNotFoundError:
        pass


def require_source_checks() -> dict[str, Any]:
    for path in [LOGISTA_PDF, LOGISTA_TEXT, FRANKO_PDF, FRANKO_TEXT]:
        if not path.exists():
            raise FileNotFoundError(str(path))
    checks = {
        "logista": {
            "Spoof Event Example 1: January 29, 2020": "Spoof Event Example 1: January 29, 2020",
            "12:00:06.610 PM Central Time": "12:00:06.610 PM Central Time",
            "77 contracts": "77 contracts",
            "Spoof Event Example 2: February 20, 2020": "Spoof Event Example 2: February 20, 2020",
            "1:06:29.086 PM": "1:06:29.086 PM",
            "269 contracts": "269 contracts",
            "Spoof Event Example 3: March 11, 2020": "Spoof Event Example 3: March 11, 2020",
            "11:29:48.415 AM": "11:29:48.415 AM",
            "filling 9 contracts": "filling 9 contracts",
        },
        "franko": {
            "December 17, 2013": "December 17, 2013",
            "First Genuine Order": "First Genuine Order",
            "Second Genuine Order": "Second Genuine Order",
            "100 lot bid": "100 lot bid",
            "approximately one second": "approximately one second",
            "COMEX copper futures": "COMEX copper futures",
            "LME copper futures": "LME copper futures",
        },
    }
    texts = {
        "logista": LOGISTA_TEXT.read_text(encoding="utf-8", errors="replace"),
        "franko": FRANKO_TEXT.read_text(encoding="utf-8", errors="replace"),
    }
    result: dict[str, Any] = {}
    for source, needles in checks.items():
        result[source] = {label: needle in texts[source] for label, needle in needles.items()}
        missing = [label for label, ok in result[source].items() if not ok]
        if missing:
            raise SystemExit(f"missing_source_text_checks:{source}:{json.dumps(missing, sort_keys=True)}")
    return result


def row(
    *,
    label: str,
    report: str,
    section: str,
    trade_date: str,
    symbol: str,
    venue: str,
    participant_type: str,
    participant: str,
    side: str,
    earliest: str,
    latest: str,
    order_count: str,
    quantity: str,
    description: str,
    group: str,
    session: str,
    row_id: str,
) -> dict[str, str]:
    return {
        "label": label,
        "source_report": report,
        "source_section": section,
        "trade_date": trade_date,
        "symbol": symbol,
        "venue_or_market_center": venue,
        "participant_type_code": participant_type,
        "participant_identifier": participant,
        "side": side,
        "earliest_order_received_time": earliest,
        "latest_order_received_time": latest,
        "order_count": order_count,
        "total_order_quantity": quantity,
        "activity_description": description,
        "matched_negative_group_id": group,
        "session_bucket": session,
        "source_row_id": row_id,
    }


def build_rows() -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    logista_type = "CFTC defendants; commodity trading advisor / head trader"
    franko_type = "CFTC respondent trader; public administrative order"
    positives = [
        row(
            label="positive_spoofing_layering",
            report=LOGISTA_REPORT,
            section="Complaint paragraphs 69-73, Spoof Event Example 1",
            trade_date="2020-01-29",
            symbol="CLM0-CLU0 crude oil June-September 2020 calendar spread",
            venue="US futures exchange / CFTC complaint",
            participant_type=logista_type,
            participant="Logista Advisors LLC / Andrew Harris Serotta",
            side="sell spoof order opposite buy genuine orders",
            earliest="12:00:06.610 America/Chicago",
            latest="12:00:23.225 America/Chicago",
            order_count="one 301-lot spoof order",
            quantity="301 contracts",
            description="CFTC complaint describes a 301-contract sell order later canceled with zero fills after opposite-side genuine buy orders filled.",
            group="cftc_logista_serotta_20200129_clm0_clu0_example1",
            session="central_time_midday",
            row_id="cftc_logista_serotta_20200129_clm0_clu0_sell_spoof_order",
        ),
        row(
            label="positive_spoofing_layering",
            report=LOGISTA_REPORT,
            section="Complaint paragraphs 74-77, Spoof Event Example 2",
            trade_date="2020-02-20",
            symbol="NGH0-NGJ0 natural gas March-April 2020 calendar spread",
            venue="US futures exchange / CFTC complaint",
            participant_type=logista_type,
            participant="Logista Advisors LLC / Andrew Harris Serotta",
            side="buy spoof order opposite sell genuine orders",
            earliest="13:06:29.086 America/Chicago",
            latest="13:07:36.935 America/Chicago",
            order_count="one 301-lot spoof order",
            quantity="301 contracts",
            description="CFTC complaint describes a 301-contract buy order later canceled with zero fills after opposite-side genuine sell orders filled.",
            group="cftc_logista_serotta_20200220_ngh0_ngj0_example2",
            session="central_time_afternoon",
            row_id="cftc_logista_serotta_20200220_ngh0_ngj0_buy_spoof_order",
        ),
        row(
            label="positive_spoofing_layering",
            report=LOGISTA_REPORT,
            section="Complaint paragraphs 78-81, Spoof Event Example 3",
            trade_date="2020-03-11",
            symbol="CLM0-CLZ0 crude oil June-December 2020 calendar spread",
            venue="US futures exchange / CFTC complaint",
            participant_type=logista_type,
            participant="Logista Advisors LLC / Andrew Harris Serotta",
            side="buy spoof order opposite sell genuine orders",
            earliest="11:29:48.415 America/Chicago",
            latest="11:30:50.876 America/Chicago",
            order_count="one 301-lot spoof order",
            quantity="301 contracts",
            description="CFTC complaint describes a 301-contract buy order later canceled with zero fills after opposite-side genuine sell orders partially filled.",
            group="cftc_logista_serotta_20200311_clm0_clz0_example3",
            session="central_time_midday",
            row_id="cftc_logista_serotta_20200311_clm0_clz0_buy_spoof_order",
        ),
        row(
            label="positive_spoofing_layering",
            report=FRANKO_REPORT,
            section="Findings II.C, December 17 2013 cross-market copper example, first LME spoof order",
            trade_date="2013-12-17",
            symbol="LME copper futures / COMEX copper futures cross-market example",
            venue="LME and COMEX",
            participant_type=franko_type,
            participant="Michael D. Franko / WAMI",
            side="buy LME spoof order opposite COMEX sell genuine orders",
            earliest="source_relative_after_two_comex_genuine_orders",
            latest="approximately one second after entry",
            order_count="one fully visible 100-lot LME bid",
            quantity="100 lots",
            description="CFTC order states Franko placed a fully visible 100-lot LME copper bid at the second-best bid; while it rested, a COMEX copper genuine sell order fully filled and four lots of a second genuine sell order filled before the LME bid was canceled.",
            group="cftc_franko_20131217_copper_crossmarket_first",
            session="source_time_not_stated",
            row_id="cftc_franko_20131217_lme_copper_first_buy_spoof_order",
        ),
        row(
            label="positive_spoofing_layering",
            report=FRANKO_REPORT,
            section="Findings II.C, December 17 2013 cross-market copper example, second LME spoof order",
            trade_date="2013-12-17",
            symbol="LME copper futures / COMEX copper futures cross-market example",
            venue="LME and COMEX",
            participant_type=franko_type,
            participant="Michael D. Franko / WAMI",
            side="buy LME spoof order opposite COMEX sell genuine orders",
            earliest="source_relative_after_first_spoof_cancel",
            latest="approximately one second after entry",
            order_count="one fully visible 100-lot LME bid",
            quantity="100 lots",
            description="CFTC order states Franko placed a second 100-lot LME copper bid at a higher price; while it rested, five more lots of the second COMEX copper genuine sell order filled before the LME bid was canceled.",
            group="cftc_franko_20131217_copper_crossmarket_second",
            session="source_time_not_stated",
            row_id="cftc_franko_20131217_lme_copper_second_buy_spoof_order",
        ),
    ]
    negatives = [
        row(
            label="normal_control",
            report=LOGISTA_REPORT,
            section="Complaint paragraphs 69-73, Spoof Event Example 1",
            trade_date="2020-01-29",
            symbol="CLM0-CLU0 crude oil June-September 2020 calendar spread",
            venue="US futures exchange / CFTC complaint",
            participant_type=logista_type,
            participant="Logista Advisors LLC / Andrew Harris Serotta",
            side="buy genuine orders opposite sell spoof order",
            earliest="12:00:08.033 America/Chicago",
            latest="12:00:20.225 America/Chicago",
            order_count="series of genuine buy orders",
            quantity="201 contracts involved; 77 contracts filled",
            description=f"CFTC complaint describes smaller aggressive genuine buy orders. {CONTROL_LIMITATION}",
            group="cftc_logista_serotta_20200129_clm0_clu0_example1",
            session="central_time_midday",
            row_id="cftc_logista_serotta_20200129_clm0_clu0_buy_genuine_orders_control",
        ),
        row(
            label="normal_control",
            report=LOGISTA_REPORT,
            section="Complaint paragraphs 74-77, Spoof Event Example 2",
            trade_date="2020-02-20",
            symbol="NGH0-NGJ0 natural gas March-April 2020 calendar spread",
            venue="US futures exchange / CFTC complaint",
            participant_type=logista_type,
            participant="Logista Advisors LLC / Andrew Harris Serotta",
            side="sell genuine orders opposite buy spoof order",
            earliest="13:06:39.339 America/Chicago",
            latest="13:07:31.935 America/Chicago",
            order_count="16 genuine sell orders of 49 lots each",
            quantity="784 contracts ordered; 269 contracts filled",
            description=f"CFTC complaint describes aggressive genuine sell orders. {CONTROL_LIMITATION}",
            group="cftc_logista_serotta_20200220_ngh0_ngj0_example2",
            session="central_time_afternoon",
            row_id="cftc_logista_serotta_20200220_ngh0_ngj0_sell_genuine_orders_control",
        ),
        row(
            label="normal_control",
            report=LOGISTA_REPORT,
            section="Complaint paragraphs 78-81, Spoof Event Example 3",
            trade_date="2020-03-11",
            symbol="CLM0-CLZ0 crude oil June-December 2020 calendar spread",
            venue="US futures exchange / CFTC complaint",
            participant_type=logista_type,
            participant="Logista Advisors LLC / Andrew Harris Serotta",
            side="sell genuine orders opposite buy spoof order",
            earliest="11:29:54.745 America/Chicago",
            latest="11:30:49.876 America/Chicago",
            order_count="series of genuine sell orders",
            quantity="125 contracts across genuine orders; 34 contracts filled",
            description=f"CFTC complaint describes genuine sell orders and 34 contracts filled. {CONTROL_LIMITATION}",
            group="cftc_logista_serotta_20200311_clm0_clz0_example3",
            session="central_time_midday",
            row_id="cftc_logista_serotta_20200311_clm0_clz0_sell_genuine_orders_control",
        ),
        row(
            label="normal_control",
            report=FRANKO_REPORT,
            section="Findings II.C, December 17 2013 cross-market copper example, first COMEX genuine order",
            trade_date="2013-12-17",
            symbol="COMEX copper futures",
            venue="COMEX",
            participant_type=franko_type,
            participant="Michael D. Franko / WAMI",
            side="sell genuine order at best offer",
            earliest="source_relative_before_first_lme_spoof",
            latest="source_relative_fully_filled_while_first_spoof_resting",
            order_count="one genuine order",
            quantity="11 lots",
            description=f"CFTC order states Franko placed an eleven-lot COMEX copper sell genuine order at the best offer and it fully filled while the first LME spoof order was on the market. {CONTROL_LIMITATION}",
            group="cftc_franko_20131217_copper_crossmarket_first",
            session="source_time_not_stated",
            row_id="cftc_franko_20131217_comex_copper_first_sell_genuine_control",
        ),
        row(
            label="normal_control",
            report=FRANKO_REPORT,
            section="Findings II.C, December 17 2013 cross-market copper example, second COMEX genuine order",
            trade_date="2013-12-17",
            symbol="COMEX copper futures",
            venue="COMEX",
            participant_type=franko_type,
            participant="Michael D. Franko / WAMI",
            side="sell genuine order at second best offer",
            earliest="source_relative_before_first_lme_spoof",
            latest="source_relative_partially_filled_across_two_lme_spoofs",
            order_count="one genuine order",
            quantity="11 lots; nine lots filled across the two LME spoof orders",
            description=f"CFTC order states Franko placed an eleven-lot COMEX copper sell genuine order at the second best offer; four lots filled while the first LME spoof rested and five more lots filled while the second LME spoof rested. {CONTROL_LIMITATION}",
            group="cftc_franko_20131217_copper_crossmarket_second",
            session="source_time_not_stated",
            row_id="cftc_franko_20131217_comex_copper_second_sell_genuine_control",
        ),
    ]
    return positives, negatives


def run_verifier() -> dict[str, Any]:
    proc = subprocess.run(
        [sys.executable, str(VERIFIER), "--intake-root", str(INTAKE)],
        cwd=REPO,
        text=True,
        capture_output=True,
        check=False,
    )
    stdout_path = CMD / "direct_manipulation_row_intake_verifier.stdout.txt"
    stderr_path = CMD / "direct_manipulation_row_intake_verifier.stderr.txt"
    exit_path = CMD / "direct_manipulation_row_intake_verifier.exit"
    stdout_path.write_text(proc.stdout, encoding="utf-8")
    stderr_path.write_text(proc.stderr, encoding="utf-8")
    exit_path.write_text(f"{proc.returncode}\n", encoding="utf-8")
    try:
        parsed = json.loads(proc.stdout)
    except json.JSONDecodeError:
        parsed = {"status": "unparsed"}
    return {
        "returncode": proc.returncode,
        "parsed": parsed,
        "stdout": str(stdout_path.relative_to(REPO)),
        "stderr": str(stderr_path.relative_to(REPO)),
        "exit": str(exit_path.relative_to(REPO)),
    }


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)
    CMD.mkdir(parents=True, exist_ok=True)
    for path in [POSITIVE, NEGATIVE, PROVENANCE, VERIFIER]:
        if not path.exists():
            raise FileNotFoundError(str(path))
    source_checks = require_source_checks()

    acquire_lock()
    try:
        positive_before = read_csv(POSITIVE)
        negative_before = read_csv(NEGATIVE)
        manifest = json.loads(PROVENANCE.read_text(encoding="utf-8"))
        pre_shas = {
            "positive_rows": sha256_file(POSITIVE),
            "matched_negative_rows": sha256_file(NEGATIVE),
            "provenance_manifest": sha256_file(PROVENANCE),
        }

        candidate_positive, candidate_negative = build_rows()
        existing_positive_ids = {row["source_row_id"] for row in positive_before}
        existing_negative_ids = {row["source_row_id"] for row in negative_before}
        added_positive = [row for row in candidate_positive if row["source_row_id"] not in existing_positive_ids]
        added_negative = [row for row in candidate_negative if row["source_row_id"] not in existing_negative_ids]

        positive_after = positive_before + added_positive
        negative_after = negative_before + added_negative
        if added_positive or added_negative:
            write_csv(POSITIVE, positive_after)
            write_csv(NEGATIVE, negative_after)
            now = datetime.now(timezone.utc).isoformat()
            manifest["cftc_logista_2020_complaint_examples"] = {
                "run_id": RUN_ID,
                "source_kind": "official_cftc_federal_complaint_pdf",
                "source_report": LOGISTA_REPORT,
                "source_url": "https://www.cftc.gov/sites/default/files/2023-09/enflogistaadvisorscomplaint090723.pdf",
                "pdf_path": str(LOGISTA_PDF),
                "pdf_sha256": sha256_file(LOGISTA_PDF),
                "text_path": str(LOGISTA_TEXT),
                "text_sha256": sha256_file(LOGISTA_TEXT),
                "text_checks": source_checks["logista"],
                "positive_source_row_ids": [row["source_row_id"] for row in added_positive if row["source_report"] == LOGISTA_REPORT],
                "matched_negative_source_row_ids": [row["source_row_id"] for row in added_negative if row["source_report"] == LOGISTA_REPORT],
                "control_policy": CONTROL_LIMITATION,
                "broad_normal_sample_added": False,
                "rows_materialized_at_utc": now,
            }
            manifest["cftc_franko_order_2018_examples"] = {
                "run_id": RUN_ID,
                "source_kind": "official_cftc_administrative_order_pdf",
                "source_report": FRANKO_REPORT,
                "source_url": "https://www.cftc.gov/sites/default/files/2018-09/enfmichaeldfrankoorder091918.pdf",
                "pdf_path": str(FRANKO_PDF),
                "pdf_sha256": sha256_file(FRANKO_PDF),
                "text_path": str(FRANKO_TEXT),
                "text_sha256": sha256_file(FRANKO_TEXT),
                "text_checks": source_checks["franko"],
                "positive_source_row_ids": [row["source_row_id"] for row in added_positive if row["source_report"] == FRANKO_REPORT],
                "matched_negative_source_row_ids": [row["source_row_id"] for row in added_negative if row["source_report"] == FRANKO_REPORT],
                "control_policy": CONTROL_LIMITATION,
                "broad_normal_sample_added": False,
                "rows_materialized_at_utc": now,
            }
            manifest["r6_logista_franko_row_uplift_v1"] = {
                "run_id": RUN_ID,
                "positive_rows_added": len(added_positive),
                "matched_negative_rows_added": len(added_negative),
                "broad_normal_sample_added": False,
                "confidence_gate": False,
            }
            manifest["positive_rows_count"] = len(positive_after)
            manifest["matched_negative_rows_count"] = len(negative_after)
            manifest["positive_rows_sha256"] = sha256_file(POSITIVE)
            manifest["matched_negative_rows_sha256"] = sha256_file(NEGATIVE)
            manifest["updated_at_utc"] = now
            manifest["updated_by"] = RUN_ID
            PROVENANCE.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")

        verifier = run_verifier()
        positive_lcb = wilson_all_success_lcb(len(positive_after))
        negative_lcb = wilson_all_success_lcb(len(negative_after))
        min_lcb = min(positive_lcb, negative_lcb)
        support_ok = len(positive_after) >= 50 and len(negative_after) >= 50
        wilson_ok = min_lcb >= 0.95
        broad_normal_sample = False
        direct_species_closed = False
        decision = "r6_logista_franko_row_uplift_v1=support_50_50_reached_confidence_still_blocked"
        if not added_positive and not added_negative:
            decision = "r6_logista_franko_row_uplift_v1=no_new_rows_already_present_still_blocked"

        rows_added_csv = OUT / "r6_logista_franko_row_uplift_rows_added_v1.csv"
        write_csv(rows_added_csv, added_positive + added_negative)
        summary = {
            "run_id": RUN_ID,
            "created_at_utc": datetime.now(timezone.utc).isoformat(),
            "decision": decision,
            "pre_shas": pre_shas,
            "post_shas": {
                "positive_rows": sha256_file(POSITIVE),
                "matched_negative_rows": sha256_file(NEGATIVE),
                "provenance_manifest": sha256_file(PROVENANCE),
            },
            "source_checks": source_checks,
            "sources": [
                {
                    "source_report": LOGISTA_REPORT,
                    "source_url": "https://www.cftc.gov/sites/default/files/2023-09/enflogistaadvisorscomplaint090723.pdf",
                    "pdf_sha256": sha256_file(LOGISTA_PDF),
                    "text_sha256": sha256_file(LOGISTA_TEXT),
                },
                {
                    "source_report": FRANKO_REPORT,
                    "source_url": "https://www.cftc.gov/sites/default/files/2018-09/enfmichaeldfrankoorder091918.pdf",
                    "pdf_sha256": sha256_file(FRANKO_PDF),
                    "text_sha256": sha256_file(FRANKO_TEXT),
                },
            ],
            "positive_rows_before": len(positive_before),
            "matched_negative_rows_before": len(negative_before),
            "positive_rows_added": len(added_positive),
            "matched_negative_rows_added": len(added_negative),
            "positive_rows_after": len(positive_after),
            "matched_negative_rows_after": len(negative_after),
            "matched_group_count_after": verifier["parsed"].get("matched_group_count"),
            "positive_wilson95_lcb": positive_lcb,
            "matched_negative_wilson95_lcb": negative_lcb,
            "min_wilson95_lcb": min_lcb,
            "support_floor_ok_50_50": support_ok,
            "wilson95_ok": wilson_ok,
            "broad_normal_sample": broad_normal_sample,
            "direct_species_closed": direct_species_closed,
            "verifier": verifier,
            "accepted_rows_added": 0,
            "new_confidence_gate": False,
            "strict_full_objective_achieved": False,
            "update_goal": False,
            "runtime_code_changed": False,
            "thresholds_relaxed": False,
            "raw_data_committed": False,
            "external_requests_sent": True,
            "trade_usable": False,
            "next_action": (
                "Continue R6 direct Manipulation acquisition toward at least 73/73 source-owned rows "
                "plus independent broad normal-market controls and remaining direct species coverage."
            ),
        }
        json_path = OUT / "r6_logista_franko_row_uplift_v1.json"
        md_path = OUT / "r6_logista_franko_row_uplift_v1.md"
        assertions_path = CHECKS / "r6_logista_franko_row_uplift_v1_assertions.out"
        json_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        md_path.write_text(
            "\n".join(
                [
                    "# R6 Logista/Franko Row Uplift v1",
                    "",
                    f"- Decision: `{decision}`.",
                    f"- Positive rows: `{len(positive_before)}` -> `{len(positive_after)}`; added `{len(added_positive)}`.",
                    f"- Matched negative rows: `{len(negative_before)}` -> `{len(negative_after)}`; added `{len(added_negative)}`.",
                    f"- Verifier status: `{verifier['parsed'].get('status')}`; matched groups `{verifier['parsed'].get('matched_group_count')}`.",
                    f"- Wilson95 LCB positive/negative/min: `{positive_lcb:.6f}` / `{negative_lcb:.6f}` / `{min_lcb:.6f}`.",
                    f"- Support floor `50/50` met: `{str(support_ok).lower()}`; Wilson95 `>=0.95`: `{str(wilson_ok).lower()}`.",
                    "- Broad normal sample: `false`; direct species closed: `false`.",
                    "- Accepted rows added: `0`; new confidence gate: `false`; strict full objective achieved: `false`; `update_goal=false`.",
                    "- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; external requests sent: `true`; trade usable: `false`.",
                    "",
                    "## Boundary",
                    "",
                    "The added rows are official CFTC complaint/order event examples. The matched negatives are same-source genuine-order legs, so this slice closes the raw `50/50` support floor but does not provide independent broad normal-market controls or a 95% Wilson gate.",
                    "",
                    "## Artifacts",
                    "",
                    f"- JSON: `{json_path.relative_to(REPO)}`",
                    f"- Report: `{md_path.relative_to(REPO)}`",
                    f"- Rows added CSV: `{rows_added_csv.relative_to(REPO)}`",
                    f"- Verifier stdout: `{(CMD / 'direct_manipulation_row_intake_verifier.stdout.txt').relative_to(REPO)}`",
                    f"- Assertions: `{assertions_path.relative_to(REPO)}`",
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        assertions = [
            f"PASS decision={decision}",
            f"PASS positive_rows_after={len(positive_after)}",
            f"PASS matched_negative_rows_after={len(negative_after)}",
            f"PASS verifier_status={verifier['parsed'].get('status')}",
            f"PASS support_floor_ok_50_50={str(support_ok).lower()}",
            f"PASS min_wilson95_lcb={min_lcb:.6f}",
            f"PASS wilson95_ok={str(wilson_ok).lower()}",
            f"PASS broad_normal_sample={str(broad_normal_sample).lower()}",
            f"PASS direct_species_closed={str(direct_species_closed).lower()}",
            "PASS new_confidence_gate=false",
            "PASS strict_full_objective_achieved=false",
            "PASS update_goal=false",
            "PASS runtime_code_changed=false",
            "PASS thresholds_relaxed=false",
            "PASS raw_data_committed=false",
        ]
        assertions_path.write_text("\n".join(assertions) + "\n", encoding="utf-8")
        print(decision)
        print(f"positive_rows={len(positive_after)}")
        print(f"matched_negative_rows={len(negative_after)}")
        print(f"support_floor_ok_50_50={str(support_ok).lower()}")
        print(f"min_wilson95_lcb={min_lcb:.6f}")
        print("update_goal=false")
        return 0
    finally:
        release_lock()


if __name__ == "__main__":
    raise SystemExit(main())
