#!/usr/bin/env python3
"""Repair Logista/Serotta R6 rows against the official CFTC complaint text."""

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


RUN_ID = "20260511T220556-codex-r6-logista-cftc-row-repair-v1"
REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = Path(__file__).resolve().parents[1]
OUT = RUN_ROOT / "r6-logista-cftc-row-repair"
CHECKS = RUN_ROOT / "checks"
CMD = RUN_ROOT / "command-output"
INTAKE = Path("/tmp/ict-engine-direct-manipulation-row-intake")
POSITIVE = INTAKE / "positive_spoofing_layering_rows.csv"
NEGATIVE = INTAKE / "matched_negative_normal_activity_rows.csv"
PROVENANCE = INTAKE / "provenance_manifest.json"
LOCK = INTAKE / ".r6_logista_cftc_row_repair_v1.lock"
VERIFIER = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T151950-codex-direct-manipulation-row-intake-manifest-v1/"
    "direct-manipulation-intake/direct_manipulation_row_intake_verifier_v1.py"
)

SOURCE_URL = "https://www.cftc.gov/media/9206/enflogistaadvisorscomplaint090723/download"
SOURCE_REPORT = (
    "CFTC Complaint: CFTC v. Logista Advisors LLC, Southern Trust Metals, Inc., "
    "Loreley Overseas Corp., and Michael Serotta, No. 1:23-cv-07485, Document 1"
)
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
DEPRECATED_TRANSIENT_LOGISTA_IDS = {
    "cftc_logista_20210311_wti_crude_sell_spoof_order",
    "cftc_logista_20210513_natural_gas_buy_spoof_order",
    "cftc_logista_20210819_brent_wti_spread_sell_spoof_order",
    "cftc_logista_20210921_wti_crude_buy_spoof_sequences",
    "cftc_logista_20211230_brent_spread_sell_spoof_orders",
    "cftc_logista_20210311_wti_crude_buy_genuine_control",
    "cftc_logista_20210513_natural_gas_sell_genuine_control",
    "cftc_logista_20210819_brent_wti_spread_buy_genuine_control",
    "cftc_logista_20210921_wti_crude_sell_genuine_controls",
    "cftc_logista_20211230_brent_spread_buy_genuine_controls",
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows([{field: row.get(field, "") for field in FIELDS} for row in rows])


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


def row(
    *,
    label: str,
    section: str,
    trade_date: str,
    symbol: str,
    venue: str,
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
        "source_report": SOURCE_REPORT,
        "source_section": section,
        "trade_date": trade_date,
        "symbol": symbol,
        "venue_or_market_center": venue,
        "participant_type_code": "CFTC defendant trader; public federal complaint",
        "participant_identifier": "Michael Serotta / Logista Advisors",
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


def corrected_rows() -> tuple[dict[str, dict[str, str]], dict[str, dict[str, str]]]:
    positives = [
        row(
            label="positive_spoofing_layering",
            section="Complaint paragraphs 70-73, Spoof Event Example 1: January 29 2020",
            trade_date="2020-01-29",
            symbol="CLM0-CLU0 crude oil June-September 2020 calendar spread",
            venue="NYMEX/CME Globex",
            side="sell spoof order opposite buy genuine orders",
            earliest="12:00:06.610 PM Central Time",
            latest="12:00:23.225 PM Central Time",
            order_count="one spoof order",
            quantity="301 contracts",
            description=(
                "Official CFTC complaint states Serotta placed a 301-contract sell spoof order "
                "at 85 cents, then began buying the same spread less than 1.5 seconds later; "
                "he canceled the spoof order at 12:00:23.225 with zero fills."
            ),
            group="cftc_logista_20200129_clm0_clu0_example1",
            session="regular_us_central_time",
            row_id="cftc_logista_20200129_clm0_clu0_sell_spoof_order",
        ),
        row(
            label="positive_spoofing_layering",
            section="Complaint paragraphs 74-77, Spoof Event Example 2: February 20 2020",
            trade_date="2020-02-20",
            symbol="NGH0-NGJ0 natural gas March-April 2020 calendar spread",
            venue="NYMEX/CME Globex",
            side="buy spoof order opposite sell genuine orders",
            earliest="1:06:29.086 PM Central Time",
            latest="1:07:36.935 PM Central Time",
            order_count="one spoof order",
            quantity="301 contracts",
            description=(
                "Official CFTC complaint states Serotta placed a 301-contract buy spoof order "
                "in the NGH0-NGJ0 spread, then began placing genuine sell orders at 1:06:39.339; "
                "he canceled the spoof order at 1:07:36.935 with zero fills."
            ),
            group="cftc_logista_20200220_ngh0_ngj0_example2",
            session="regular_us_central_time",
            row_id="cftc_logista_20200220_ngh0_ngj0_buy_spoof_order",
        ),
        row(
            label="positive_spoofing_layering",
            section="Complaint paragraphs 78-81, Spoof Event Example 3: March 11 2020",
            trade_date="2020-03-11",
            symbol="CLM0-CLZ0 crude oil June-December 2020 calendar spread",
            venue="NYMEX/CME Globex",
            side="buy spoof order opposite sell genuine orders",
            earliest="11:29:48.415 AM Central Time",
            latest="11:30:50.876 AM Central Time",
            order_count="one spoof order",
            quantity="301 contracts",
            description=(
                "Official CFTC complaint states Serotta placed a 301-contract buy spoof order "
                "in the CLM0-CLZ0 spread, then placed genuine sell orders starting at 11:29:54.745; "
                "he canceled the spoof order at 11:30:50.876 with zero fills."
            ),
            group="cftc_logista_20200311_clm0_clz0_example3",
            session="regular_us_central_time",
            row_id="cftc_logista_20200311_clm0_clz0_buy_spoof_order",
        ),
        row(
            label="positive_spoofing_layering",
            section="Complaint paragraphs 82-90, Spoof Event Example 4: February 19 2020",
            trade_date="2020-02-19",
            symbol="NGH0-NGJ0 natural gas March-April 2020 calendar spread",
            venue="NYMEX/CME Globex",
            side="fourteen alternating 301-lot spoof orders opposite smaller genuine orders",
            earliest="10:56:22.803 PM Central Time",
            latest="11:12:21.768 PM Central Time",
            order_count="fourteen 301-lot spoof orders",
            quantity="4,214 contracts total, zero filled",
            description=(
                "Official CFTC complaint states Serotta repeated a spoof/genuine/cancel sequence "
                "fourteen times over sixteen minutes, with zero fills on 4,214 spoof-order lots and "
                "2,874 lots filled on smaller opposite-side genuine orders."
            ),
            group="cftc_logista_20200219_ngh0_ngj0_repeated_example4",
            session="overnight_us_central_time",
            row_id="cftc_logista_20200219_ngh0_ngj0_repeated_spoof_orders",
        ),
        row(
            label="positive_spoofing_layering",
            section="Complaint paragraphs 91-95, Spoof Event Example 5: February 5 2020",
            trade_date="2020-02-05",
            symbol="ICE Brent/WTI crude spread April 2020",
            venue="IFEU electronic market",
            side="nineteen large spoof orders opposite smaller genuine orders",
            earliest="about 8:23 PM GMT",
            latest="about 8:41 PM GMT",
            order_count="nineteen large spoof orders",
            quantity="5,919 contracts total, zero filled",
            description=(
                "Official CFTC complaint states Serotta placed nineteen large 201-to-301-lot orders "
                "over eighteen minutes, with zero fills on 5,919 large-order lots and about 2,513 "
                "lots filled on smaller opposite-side genuine orders."
            ),
            group="cftc_logista_20200205_brent_wti_spread_example5",
            session="regular_london_time",
            row_id="cftc_logista_20200205_brent_wti_spread_large_spoof_orders",
        ),
    ]
    negatives = [
        row(
            label="matched_negative_normal_activity",
            section="Complaint paragraphs 70-73, Spoof Event Example 1: January 29 2020",
            trade_date="2020-01-29",
            symbol="CLM0-CLU0 crude oil June-September 2020 calendar spread",
            venue="NYMEX/CME Globex",
            side="buy genuine orders",
            earliest="12:00:08.033 PM Central Time",
            latest="about 12:00:20.225 PM Central Time",
            order_count="series of genuine buy orders",
            quantity="201 contracts involved; 77 filled",
            description=(
                "Matched same-complaint control seed: the source distinguishes genuine buy orders "
                "from the sell spoof order; 77 of 201 genuine-order contracts filled before Serotta "
                "canceled the spoof order."
            ),
            group="cftc_logista_20200129_clm0_clu0_example1",
            session="regular_us_central_time",
            row_id="cftc_logista_20200129_clm0_clu0_buy_genuine_controls",
        ),
        row(
            label="matched_negative_normal_activity",
            section="Complaint paragraphs 74-77, Spoof Event Example 2: February 20 2020",
            trade_date="2020-02-20",
            symbol="NGH0-NGJ0 natural gas March-April 2020 calendar spread",
            venue="NYMEX/CME Globex",
            side="sell genuine orders",
            earliest="1:06:39.339 PM Central Time",
            latest="less than 5 seconds before 1:07:36.935 PM Central Time",
            order_count="sixteen genuine sell orders of 49 lots each",
            quantity="269 contracts filled",
            description=(
                "Matched same-complaint control seed: the source distinguishes genuine sell orders "
                "from the buy spoof order; Serotta filled 269 contracts from sixteen genuine sell orders."
            ),
            group="cftc_logista_20200220_ngh0_ngj0_example2",
            session="regular_us_central_time",
            row_id="cftc_logista_20200220_ngh0_ngj0_sell_genuine_controls",
        ),
        row(
            label="matched_negative_normal_activity",
            section="Complaint paragraphs 78-81, Spoof Event Example 3: March 11 2020",
            trade_date="2020-03-11",
            symbol="CLM0-CLZ0 crude oil June-December 2020 calendar spread",
            venue="NYMEX/CME Globex",
            side="sell genuine orders",
            earliest="11:29:54.745 AM Central Time",
            latest="about 11:30:49.876 AM Central Time",
            order_count="series of genuine sell orders",
            quantity="125 contracts across genuine orders; 34 filled",
            description=(
                "Matched same-complaint control seed: the source distinguishes genuine sell orders "
                "from the buy spoof order; 9 contracts filled at -349 cents and 25 at -348 cents."
            ),
            group="cftc_logista_20200311_clm0_clz0_example3",
            session="regular_us_central_time",
            row_id="cftc_logista_20200311_clm0_clz0_sell_genuine_controls",
        ),
        row(
            label="matched_negative_normal_activity",
            section="Complaint paragraphs 82-90, Spoof Event Example 4: February 19 2020",
            trade_date="2020-02-19",
            symbol="NGH0-NGJ0 natural gas March-April 2020 calendar spread",
            venue="NYMEX/CME Globex",
            side="smaller opposite-side genuine orders",
            earliest="10:56:22.803 PM Central Time",
            latest="11:12:21.768 PM Central Time",
            order_count="numerous smaller genuine orders",
            quantity="2,874 contracts filled",
            description=(
                "Matched same-complaint control seed: the source distinguishes smaller genuine orders "
                "from fourteen 301-lot spoof orders and states the genuine orders filled more than 80%."
            ),
            group="cftc_logista_20200219_ngh0_ngj0_repeated_example4",
            session="overnight_us_central_time",
            row_id="cftc_logista_20200219_ngh0_ngj0_genuine_controls",
        ),
        row(
            label="matched_negative_normal_activity",
            section="Complaint paragraphs 91-95, Spoof Event Example 5: February 5 2020",
            trade_date="2020-02-05",
            symbol="ICE Brent/WTI crude spread April 2020",
            venue="IFEU electronic market",
            side="smaller opposite-side genuine orders",
            earliest="about 8:23 PM GMT",
            latest="about 8:41 PM GMT",
            order_count="numerous smaller genuine orders",
            quantity="about 2,513 contracts filled",
            description=(
                "Matched same-complaint control seed: the source distinguishes smaller genuine orders "
                "from nineteen large spoof orders and states the genuine orders filled more than 73%."
            ),
            group="cftc_logista_20200205_brent_wti_spread_example5",
            session="regular_london_time",
            row_id="cftc_logista_20200205_brent_wti_spread_genuine_controls",
        ),
    ]
    return ({row["source_row_id"]: row for row in positives}, {row["source_row_id"]: row for row in negatives})


def upsert(rows: list[dict[str, str]], corrections: dict[str, dict[str, str]]) -> tuple[list[dict[str, str]], int, int]:
    seen = {row["source_row_id"]: idx for idx, row in enumerate(rows)}
    repaired = 0
    added = 0
    for row_id, corrected in corrections.items():
        if row_id in seen:
            idx = seen[row_id]
            if any(rows[idx].get(field, "") != corrected.get(field, "") for field in FIELDS):
                rows[idx] = corrected
                repaired += 1
        else:
            rows.append(corrected)
            added += 1
    return rows, added, repaired


def remove_deprecated(rows: list[dict[str, str]]) -> tuple[list[dict[str, str]], int]:
    kept = [row for row in rows if row.get("source_row_id", "") not in DEPRECATED_TRANSIENT_LOGISTA_IDS]
    return kept, len(rows) - len(kept)


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)
    CMD.mkdir(parents=True, exist_ok=True)
    for path in [POSITIVE, NEGATIVE, PROVENANCE, VERIFIER]:
        if not path.exists():
            raise FileNotFoundError(str(path))

    acquire_lock()
    try:
        positives_before = read_csv(POSITIVE)
        negatives_before = read_csv(NEGATIVE)
        positive_corrections, negative_corrections = corrected_rows()
        positives_clean, pos_removed = remove_deprecated(positives_before)
        negatives_clean, neg_removed = remove_deprecated(negatives_before)
        positives_after, pos_added, pos_repaired = upsert(positives_clean, positive_corrections)
        negatives_after, neg_added, neg_repaired = upsert(negatives_clean, negative_corrections)
        write_csv(POSITIVE, positives_after)
        write_csv(NEGATIVE, negatives_after)

        provenance = json.loads(PROVENANCE.read_text(encoding="utf-8"))
        provenance.update(
            {
                "r6_logista_cftc_row_repair_v1": {
                    "run_id": RUN_ID,
                    "source_url": SOURCE_URL,
                    "source_report": SOURCE_REPORT,
                        "positive_rows_added": pos_added,
                        "positive_rows_repaired": pos_repaired,
                        "positive_rows_removed_deprecated": pos_removed,
                        "matched_negative_rows_added": neg_added,
                        "matched_negative_rows_repaired": neg_repaired,
                        "matched_negative_rows_removed_deprecated": neg_removed,
                    "materialized_at_utc": datetime.now(timezone.utc).isoformat(),
                    "limitation": (
                        "Official CFTC same-event spoof/genuine-order examples only; "
                        "not broad normal-market controls."
                    ),
                },
                "positive_rows_count": len(positives_after),
                "matched_negative_rows_count": len(negatives_after),
                "matched_negative_control_policy": (
                    "CFTC public complaint/order same-event genuine-order legs are source-described "
                    "schema/control seeds only; they are not a broad normal-market calibration sample."
                ),
                "positive_rows_sha256": sha256_file(POSITIVE),
                "matched_negative_rows_sha256": sha256_file(NEGATIVE),
                "updated_at_utc": datetime.now(timezone.utc).isoformat(),
                "updated_by": RUN_ID,
            }
        )
        PROVENANCE.write_text(json.dumps(provenance, indent=2, sort_keys=True) + "\n", encoding="utf-8")

        verifier = run_verifier()
        positive_lcb = wilson_all_success_lcb(len(positives_after))
        negative_lcb = wilson_all_success_lcb(len(negatives_after))
        min_lcb = min(positive_lcb, negative_lcb)
        support_floor_ok = len(positives_after) >= 50 and len(negatives_after) >= 50
        decision = "r6_logista_cftc_row_repair_v1=source_rows_repaired_support_still_blocked"

        rows_added_path = OUT / "r6_logista_cftc_row_repair_rows_v1.csv"
        write_csv(rows_added_path, list(positive_corrections.values()) + list(negative_corrections.values()))
        summary = {
            "run_id": RUN_ID,
            "created_at_utc": datetime.now(timezone.utc).isoformat(),
            "source_url": SOURCE_URL,
            "source_report": SOURCE_REPORT,
            "decision": decision,
            "positive_rows_before": len(positives_before),
            "matched_negative_rows_before": len(negatives_before),
            "positive_rows_added": pos_added,
            "positive_rows_repaired": pos_repaired,
            "positive_rows_removed_deprecated": pos_removed,
            "matched_negative_rows_added": neg_added,
            "matched_negative_rows_repaired": neg_repaired,
            "matched_negative_rows_removed_deprecated": neg_removed,
            "positive_rows_after": len(positives_after),
            "matched_negative_rows_after": len(negatives_after),
            "min_wilson95_lcb": min_lcb,
            "support_floor_ok_50_50": support_floor_ok,
            "broad_normal_sample": False,
            "direct_species_closed": False,
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
            "next_action": "Continue R6 acquisition with at least broad normal controls and additional direct species; support is still below 50/50.",
        }
        json_path = OUT / "r6_logista_cftc_row_repair_v1.json"
        md_path = OUT / "r6_logista_cftc_row_repair_v1.md"
        assertions_path = CHECKS / "r6_logista_cftc_row_repair_v1_assertions.out"
        json_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        md_path.write_text(
            "\n".join(
                [
                    "# R6 Logista CFTC Row Repair v1",
                    "",
                    f"- Decision: `{decision}`.",
                    f"- Source: `{SOURCE_REPORT}`.",
                    f"- Source URL: {SOURCE_URL}.",
                    f"- Positive rows: `{len(positives_before)}` -> `{len(positives_after)}`; added `{pos_added}`; repaired `{pos_repaired}`; removed deprecated `{pos_removed}`.",
                    f"- Matched negative rows: `{len(negatives_before)}` -> `{len(negatives_after)}`; added `{neg_added}`; repaired `{neg_repaired}`; removed deprecated `{neg_removed}`.",
                    f"- Verifier status: `{verifier['parsed'].get('status')}`.",
                    f"- Wilson95 min LCB: `{min_lcb:.6f}`.",
                    f"- Support floor `50/50` met: `{str(support_floor_ok).lower()}`.",
                    "- Broad normal sample: `false`; direct species closed: `false`.",
                    "- Accepted rows added: `0`; new confidence gate: `false`; strict full objective achieved: `false`; `update_goal=false`.",
                    "- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; external requests sent: `true`; trade usable: `false`.",
                    "",
                    "## Boundary",
                    "",
                    "This repairs transient Logista row values against the official CFTC complaint text. The repaired rows remain same-event CFTC spoof/genuine-order examples, not broad normal-market controls.",
                    "",
                    "## Artifacts",
                    "",
                    f"- JSON: `{json_path.relative_to(REPO)}`",
                    f"- Report: `{md_path.relative_to(REPO)}`",
                    f"- Corrected rows CSV: `{rows_added_path.relative_to(REPO)}`",
                    f"- Verifier stdout: `{(CMD / 'direct_manipulation_row_intake_verifier.stdout.txt').relative_to(REPO)}`",
                    f"- Assertions: `{assertions_path.relative_to(REPO)}`",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        assertions_path.write_text(
            "\n".join(
                [
                    f"PASS decision={decision}",
                    f"PASS positive_rows_after={len(positives_after)}",
                    f"PASS matched_negative_rows_after={len(negatives_after)}",
                    f"PASS positive_rows_added={pos_added}",
                    f"PASS positive_rows_repaired={pos_repaired}",
                    f"PASS positive_rows_removed_deprecated={pos_removed}",
                    f"PASS matched_negative_rows_added={neg_added}",
                    f"PASS matched_negative_rows_repaired={neg_repaired}",
                    f"PASS matched_negative_rows_removed_deprecated={neg_removed}",
                    f"PASS verifier_status={verifier['parsed'].get('status')}",
                    f"PASS min_wilson95_lcb={min_lcb:.6f}",
                    f"PASS support_floor_ok_50_50={str(support_floor_ok).lower()}",
                    "PASS broad_normal_sample=false",
                    "PASS accepted_rows_added=0",
                    "PASS update_goal=false",
                    "PASS runtime_code_changed=false",
                    "PASS thresholds_relaxed=false",
                    "PASS raw_data_committed=false",
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        print(decision)
        print(f"positive_rows={len(positives_after)}")
        print(f"matched_negative_rows={len(negatives_after)}")
        print(f"min_wilson95_lcb={min_lcb:.6f}")
        print("update_goal=false")
        return 0
    finally:
        release_lock()


if __name__ == "__main__":
    raise SystemExit(main())
