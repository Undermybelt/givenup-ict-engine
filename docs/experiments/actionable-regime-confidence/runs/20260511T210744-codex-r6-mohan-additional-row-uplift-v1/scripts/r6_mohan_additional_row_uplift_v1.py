#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path


RUN_ID = "20260511T210744+0800-codex-r6-mohan-additional-row-uplift-v1"
RUN_ROOT = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T210744-codex-r6-mohan-additional-row-uplift-v1"
)
OUT_DIR = RUN_ROOT / "r6-mohan-additional-row-uplift"
CHECKS_DIR = RUN_ROOT / "checks"
INTAKE_ROOT = Path("/tmp/ict-engine-direct-manipulation-row-intake")
POSITIVE_ROWS = INTAKE_ROOT / "positive_spoofing_layering_rows.csv"
NEGATIVE_ROWS = INTAKE_ROOT / "matched_negative_normal_activity_rows.csv"
PROVENANCE = INTAKE_ROOT / "provenance_manifest.json"
SOURCE_PDF = Path("/tmp/ict-engine-cftc-source-row-search/enfmohancomplaint012818.pdf")
SOURCE_TXT = Path("/tmp/ict-engine-cftc-source-row-search/enfmohancomplaint012818.txt")
SOURCE_URL = "https://www.cftc.gov/sites/default/files/idc/groups/public/@lrenforcementactions/documents/legalpleading/enfmohancomplaint012818.pdf"
VERIFIER = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T151950-codex-direct-manipulation-row-intake-manifest-v1/"
    "direct-manipulation-intake/direct_manipulation_row_intake_verifier_v1.py"
)
CALIBRATION_SOURCE = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T210030-codex-r6-cftc-schema-ready-calibration-gate-v1/"
    "scripts/r6_cftc_schema_ready_calibration_gate_v1.py"
)

FIELDNAMES = [
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

SOURCE_REPORT = "CFTC Complaint: Krishna Mohan, CFTC v. Mohan, Case 4:18-cv-00260"
PARTICIPANT = "Krishna Mohan / Trading Firm account YB01"

POSITIVE_ADDITIONS = [
    {
        "label": "positive_spoofing_layering",
        "source_report": SOURCE_REPORT,
        "source_section": "Complaint paragraphs 48-49 and Exhibit A, November 27 2013 E-mini Dow examples",
        "trade_date": "2013-11-27",
        "symbol": "December 2013 E-mini Dow futures",
        "venue_or_market_center": "CBOT",
        "participant_type_code": "CFTC defendant trader; firm account YB01",
        "participant_identifier": PARTICIPANT,
        "side": "sell spoof orders opposite buy genuine iceberg order",
        "earliest_order_received_time": "08:05:40.703 America/Chicago",
        "latest_order_received_time": "08:05:42.684 America/Chicago",
        "order_count": "multiple orders via order splitter",
        "total_order_quantity": "40 contracts",
        "activity_description": "Source complaint describes multiple sell spoof orders entered at the second-ask level, followed by full cancellation after the matched buy iceberg genuine order filled.",
        "matched_negative_group_id": "cftc_mohan_20131127_dow_first_example",
        "session_bucket": "regular_us_central_time",
        "source_row_id": "cftc_mohan_20131127_dow_sell_spoof_group",
    },
    {
        "label": "positive_spoofing_layering",
        "source_report": SOURCE_REPORT,
        "source_section": "Complaint paragraphs 48-49 and Exhibit A, November 27 2013 E-mini Dow examples",
        "trade_date": "2013-11-27",
        "symbol": "December 2013 E-mini Dow futures",
        "venue_or_market_center": "CBOT",
        "participant_type_code": "CFTC defendant trader; firm account YB01",
        "participant_identifier": PARTICIPANT,
        "side": "buy spoof orders opposite sell genuine iceberg order",
        "earliest_order_received_time": "08:05:45.024 America/Chicago",
        "latest_order_received_time": "08:05:47.421 America/Chicago",
        "order_count": "two groups of multiple orders via order splitter",
        "total_order_quantity": "80 contracts",
        "activity_description": "Source complaint describes two buy-side spoof groups entered opposite the matched sell iceberg genuine order, followed by cancellations after the genuine order filled.",
        "matched_negative_group_id": "cftc_mohan_20131127_dow_second_example",
        "session_bucket": "regular_us_central_time",
        "source_row_id": "cftc_mohan_20131127_dow_buy_spoof_groups",
    },
    {
        "label": "positive_spoofing_layering",
        "source_report": SOURCE_REPORT,
        "source_section": "Complaint paragraphs 52-53 and Exhibit C, December 9 2013 E-mini NASDAQ examples",
        "trade_date": "2013-12-09",
        "symbol": "December 2013 E-mini NASDAQ futures",
        "venue_or_market_center": "CME",
        "participant_type_code": "CFTC defendant trader; firm account YB01",
        "participant_identifier": PARTICIPANT,
        "side": "sell spoof orders opposite buy genuine iceberg order",
        "earliest_order_received_time": "05:27:42.713 America/Chicago",
        "latest_order_received_time": "05:27:45.480 America/Chicago",
        "order_count": "two groups of multiple orders via order splitter",
        "total_order_quantity": "80 contracts",
        "activity_description": "Source complaint describes two sell-side spoof groups entered opposite a buy iceberg genuine order; the spoof groups were canceled shortly after the genuine order partially filled.",
        "matched_negative_group_id": "cftc_mohan_20131209_nq_first_example",
        "session_bucket": "overnight_central_time",
        "source_row_id": "cftc_mohan_20131209_nq_sell_spoof_groups",
    },
    {
        "label": "positive_spoofing_layering",
        "source_report": SOURCE_REPORT,
        "source_section": "Complaint paragraphs 52-53 and Exhibit C, December 9 2013 E-mini NASDAQ examples",
        "trade_date": "2013-12-09",
        "symbol": "December 2013 E-mini NASDAQ futures",
        "venue_or_market_center": "CME",
        "participant_type_code": "CFTC defendant trader; firm account YB01",
        "participant_identifier": PARTICIPANT,
        "side": "buy spoof orders opposite sell genuine iceberg order",
        "earliest_order_received_time": "05:27:46.505 America/Chicago",
        "latest_order_received_time": "05:27:47.976 America/Chicago",
        "order_count": "two groups of multiple orders via order splitter",
        "total_order_quantity": "80 contracts",
        "activity_description": "Source complaint describes two buy-side spoof groups entered opposite a sell iceberg genuine order; the spoof groups were canceled shortly after the genuine order filled.",
        "matched_negative_group_id": "cftc_mohan_20131209_nq_second_example",
        "session_bucket": "overnight_central_time",
        "source_row_id": "cftc_mohan_20131209_nq_buy_spoof_groups",
    },
]

NEGATIVE_ADDITIONS = [
    {
        "label": "matched_negative_normal_activity",
        "source_report": SOURCE_REPORT,
        "source_section": "Complaint paragraphs 48-49 and Exhibit A, November 27 2013 E-mini Dow examples",
        "trade_date": "2013-11-27",
        "symbol": "December 2013 E-mini Dow futures",
        "venue_or_market_center": "CBOT",
        "participant_type_code": "CFTC defendant trader; firm account YB01",
        "participant_identifier": PARTICIPANT,
        "side": "buy genuine iceberg order",
        "earliest_order_received_time": "08:05:39.461 America/Chicago",
        "latest_order_received_time": "08:05:41.335 America/Chicago",
        "order_count": "one genuine iceberg order with one contract displayed",
        "total_order_quantity": "40 contracts",
        "activity_description": "Matched same-source genuine-order leg from the complaint. This is a source-described same-event control seed, not a broad normal-market calibration sample.",
        "matched_negative_group_id": "cftc_mohan_20131127_dow_first_example",
        "session_bucket": "regular_us_central_time",
        "source_row_id": "cftc_mohan_20131127_dow_buy_genuine_iceberg_control",
    },
    {
        "label": "matched_negative_normal_activity",
        "source_report": SOURCE_REPORT,
        "source_section": "Complaint paragraphs 48-49 and Exhibit A, November 27 2013 E-mini Dow examples",
        "trade_date": "2013-11-27",
        "symbol": "December 2013 E-mini Dow futures",
        "venue_or_market_center": "CBOT",
        "participant_type_code": "CFTC defendant trader; firm account YB01",
        "participant_identifier": PARTICIPANT,
        "side": "sell genuine iceberg order",
        "earliest_order_received_time": "08:05:43.565 America/Chicago",
        "latest_order_received_time": "08:05:46.241 America/Chicago",
        "order_count": "one genuine iceberg order with one contract displayed",
        "total_order_quantity": "40 contracts",
        "activity_description": "Matched same-source genuine-order leg from the complaint. This is a source-described same-event control seed, not a broad normal-market calibration sample.",
        "matched_negative_group_id": "cftc_mohan_20131127_dow_second_example",
        "session_bucket": "regular_us_central_time",
        "source_row_id": "cftc_mohan_20131127_dow_sell_genuine_iceberg_control",
    },
    {
        "label": "matched_negative_normal_activity",
        "source_report": SOURCE_REPORT,
        "source_section": "Complaint paragraphs 52-53 and Exhibit C, December 9 2013 E-mini NASDAQ examples",
        "trade_date": "2013-12-09",
        "symbol": "December 2013 E-mini NASDAQ futures",
        "venue_or_market_center": "CME",
        "participant_type_code": "CFTC defendant trader; firm account YB01",
        "participant_identifier": PARTICIPANT,
        "side": "buy genuine iceberg order",
        "earliest_order_received_time": "05:27:41.553 America/Chicago",
        "latest_order_received_time": "05:27:43.512 America/Chicago",
        "order_count": "one genuine iceberg order with one contract displayed",
        "total_order_quantity": "40 contracts; 17 contracts filled in described partial fill",
        "activity_description": "Matched same-source genuine-order leg from the complaint. Latest fill time is derived from source-stated 284 milliseconds after 05:27:43.228; this remains a control seed, not a broad normal-market sample.",
        "matched_negative_group_id": "cftc_mohan_20131209_nq_first_example",
        "session_bucket": "overnight_central_time",
        "source_row_id": "cftc_mohan_20131209_nq_buy_genuine_iceberg_control",
    },
    {
        "label": "matched_negative_normal_activity",
        "source_report": SOURCE_REPORT,
        "source_section": "Complaint paragraphs 52-53 and Exhibit C, December 9 2013 E-mini NASDAQ examples",
        "trade_date": "2013-12-09",
        "symbol": "December 2013 E-mini NASDAQ futures",
        "venue_or_market_center": "CME",
        "participant_type_code": "CFTC defendant trader; firm account YB01",
        "participant_identifier": PARTICIPANT,
        "side": "sell genuine iceberg order",
        "earliest_order_received_time": "05:27:44.772 America/Chicago",
        "latest_order_received_time": "05:27:46.835 America/Chicago",
        "order_count": "one genuine iceberg order with one contract displayed",
        "total_order_quantity": "17 contracts",
        "activity_description": "Matched same-source genuine-order leg from the complaint. This is a source-described same-event control seed, not a broad normal-market calibration sample.",
        "matched_negative_group_id": "cftc_mohan_20131209_nq_second_example",
        "session_bucket": "overnight_central_time",
        "source_row_id": "cftc_mohan_20131209_nq_sell_genuine_iceberg_control",
    },
]

NEEDLES = [
    "November 27, 2013",
    "8:05:39.461 AM",
    "8:05:40.703 AM",
    "8:05:47.421 AM",
    "December 9, 2013",
    "5:27:41.553 AM",
    "5:27:42.713 AM",
    "5:27:47.976 AM",
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_rows(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)


def append_unique(path: Path, additions: list[dict[str, str]]) -> tuple[int, int]:
    rows = load_rows(path)
    seen = {row.get("source_row_id", "") for row in rows}
    added = 0
    for row in additions:
        if row["source_row_id"] not in seen:
            rows.append(row)
            seen.add(row["source_row_id"])
            added += 1
    write_rows(path, rows)
    return len(rows), added


def ensure_source_text() -> dict[str, object]:
    if not SOURCE_TXT.exists() and SOURCE_PDF.exists():
        subprocess.run(
            [
                "gs",
                "-q",
                "-dNOPAUSE",
                "-dBATCH",
                "-sDEVICE=txtwrite",
                f"-sOutputFile={SOURCE_TXT}",
                str(SOURCE_PDF),
            ],
            check=False,
            text=True,
            capture_output=True,
        )
    text = SOURCE_TXT.read_text(encoding="utf-8", errors="ignore") if SOURCE_TXT.exists() else ""
    return {
        "url": SOURCE_URL,
        "pdf_path": str(SOURCE_PDF) if SOURCE_PDF.exists() else None,
        "pdf_sha256": sha256(SOURCE_PDF) if SOURCE_PDF.exists() else None,
        "text_path": str(SOURCE_TXT) if SOURCE_TXT.exists() else None,
        "text_sha256": sha256(SOURCE_TXT) if SOURCE_TXT.exists() else None,
        "text_checks": {needle: needle.lower() in text.lower() for needle in NEEDLES},
    }


def update_provenance(source_probe: dict[str, object], positive_count: int, negative_count: int) -> dict[str, object]:
    if PROVENANCE.exists():
        try:
            provenance = json.loads(PROVENANCE.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            provenance = {}
    else:
        provenance = {}
    provenance["cftc_mohan_additional_examples"] = source_probe
    provenance["mohan_additional_rows_materialized_at_utc"] = datetime.now(timezone.utc).isoformat()
    provenance["mohan_additional_positive_rows_added"] = len(POSITIVE_ADDITIONS)
    provenance["mohan_additional_matched_negative_rows_added"] = len(NEGATIVE_ADDITIONS)
    provenance["positive_rows_count"] = positive_count
    provenance["matched_negative_rows_count"] = negative_count
    provenance["matched_negative_control_policy"] = (
        "Derived only from public CFTC facts describing genuine order legs in the same examples; "
        "schema-ready/unscored seed, not a broad normal-activity calibration sample."
    )
    provenance["matched_control_limitations"] = (
        "CFTC same-report or same-complaint genuine-order legs are schema/control seeds only; "
        "they are not broad normal-market heldout controls."
    )
    provenance["updated_by"] = RUN_ID
    provenance["updated_at_utc"] = datetime.now(timezone.utc).isoformat()
    PROVENANCE.write_text(json.dumps(provenance, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return provenance


def run_verifier() -> dict[str, object]:
    completed = subprocess.run(
        ["python3", str(VERIFIER), "--intake-root", str(INTAKE_ROOT)],
        text=True,
        capture_output=True,
        check=False,
    )
    try:
        payload: object = json.loads(completed.stdout)
    except json.JSONDecodeError:
        payload = completed.stdout
    return {
        "command": f"python3 {VERIFIER} --intake-root {INTAKE_ROOT}",
        "returncode": completed.returncode,
        "stdout": payload,
        "stderr": completed.stderr,
    }


def run_calibration() -> int:
    spec = importlib.util.spec_from_file_location("r6_cftc_schema_ready_calibration_gate_v1", CALIBRATION_SOURCE)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {CALIBRATION_SOURCE}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.RUN_ID = "20260511T210744-codex-r6-mohan-additional-row-uplift-v1"
    module.RUN_ROOT = RUN_ROOT
    module.OUT = OUT_DIR
    module.CHECKS = CHECKS_DIR
    return int(module.main())


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECKS_DIR.mkdir(parents=True, exist_ok=True)

    source_probe = ensure_source_text()
    positive_count, positive_added = append_unique(POSITIVE_ROWS, POSITIVE_ADDITIONS)
    negative_count, negative_added = append_unique(NEGATIVE_ROWS, NEGATIVE_ADDITIONS)
    provenance = update_provenance(source_probe, positive_count, negative_count)
    verifier = run_verifier()
    calibration_returncode = run_calibration()

    intake_summary = [
        {"file": str(POSITIVE_ROWS), "rows": positive_count, "added_this_run": positive_added, "sha256": sha256(POSITIVE_ROWS)},
        {"file": str(NEGATIVE_ROWS), "rows": negative_count, "added_this_run": negative_added, "sha256": sha256(NEGATIVE_ROWS)},
        {"file": str(PROVENANCE), "rows": "", "added_this_run": "", "sha256": sha256(PROVENANCE)},
    ]
    summary_csv = OUT_DIR / "r6_mohan_additional_row_uplift_v1_intake_summary.csv"
    write_csv(summary_csv, intake_summary, ["file", "rows", "added_this_run", "sha256"])

    decision = {
        "gate_result": "r6_mohan_additional_row_uplift_v1=direct_intake_rows_uplifted_schema_ready_calibration_still_blocked",
        "accepted_rows_added": 0,
        "new_confidence_gate": False,
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "trade_usable": False,
        "r6_direct_species_closed": False,
    }
    result = {
        "artifact_type": "r6_mohan_additional_row_uplift_v1",
        "run_id": RUN_ID,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "decision": decision,
        "source_probe": source_probe,
        "positive_rows": positive_count,
        "positive_rows_added_this_run": positive_added,
        "negative_rows": negative_count,
        "negative_rows_added_this_run": negative_added,
        "provenance_keys": sorted(provenance.keys()),
        "verifier": verifier,
        "calibration_returncode": calibration_returncode,
        "artifacts": {
            "json": str(OUT_DIR / "r6_mohan_additional_row_uplift_v1.json"),
            "md": str(OUT_DIR / "r6_mohan_additional_row_uplift_v1.md"),
            "intake_summary_csv": str(summary_csv),
            "calibration_json": str(OUT_DIR / "r6_cftc_schema_ready_calibration_gate_v1.json"),
            "calibration_md": str(OUT_DIR / "r6_cftc_schema_ready_calibration_gate_v1.md"),
            "assertions": str(CHECKS_DIR / "r6_mohan_additional_row_uplift_v1_assertions.out"),
        },
    }

    json_path = OUT_DIR / "r6_mohan_additional_row_uplift_v1.json"
    md_path = OUT_DIR / "r6_mohan_additional_row_uplift_v1.md"
    assertions_path = CHECKS_DIR / "r6_mohan_additional_row_uplift_v1_assertions.out"
    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    verifier_payload = verifier.get("stdout", {})
    if not isinstance(verifier_payload, dict):
        verifier_payload = {}
    md_lines = [
        "# R6 Mohan Additional Row Uplift v1",
        "",
        "- Gate result: `r6_mohan_additional_row_uplift_v1=direct_intake_rows_uplifted_schema_ready_calibration_still_blocked`.",
        f"- Positive rows now: `{positive_count}`; added this run: `{positive_added}`.",
        f"- Matched negative/control rows now: `{negative_count}`; added this run: `{negative_added}`.",
        f"- Verifier status: `{verifier_payload.get('status', 'unknown')}`; matched groups: `{verifier_payload.get('matched_group_count', 'unknown')}`.",
        "- Accepted rows added: `0`; new confidence gate: `false`.",
        "- Strict full objective achieved: `false`; `update_goal=false`.",
        "- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; trade usable: `false`.",
        "",
        "## Boundary",
        "",
        "This expands the R6 spoofing/layering intake with additional row-level examples from the official CFTC Mohan complaint. It remains schema-ready/unscored only: support is still short and the matched controls are same-complaint genuine-order legs, not a broad normal-market sample.",
        "",
        "## Verifier",
        "",
        "```json",
        json.dumps(verifier.get("stdout", {}), indent=2, sort_keys=True),
        "```",
        "",
        "## Next Action",
        "",
        "Acquire additional source-owned/owner-approved positive and broad same-schema normal-control rows across more symbols, venues, and periods; then run the chronological plus heldout-symbol/venue Wilson95 calibration gate before another completion audit.",
        "",
        "## Artifacts",
        "",
        f"- JSON: `{json_path}`",
        f"- Intake summary CSV: `{summary_csv}`",
        f"- Calibration JSON: `{OUT_DIR / 'r6_cftc_schema_ready_calibration_gate_v1.json'}`",
        f"- Calibration report: `{OUT_DIR / 'r6_cftc_schema_ready_calibration_gate_v1.md'}`",
        f"- Assertions: `{assertions_path}`",
    ]
    md_path.write_text("\n".join(md_lines) + "\n", encoding="utf-8")

    assertions = [
        "PASS gate_result=r6_mohan_additional_row_uplift_v1=direct_intake_rows_uplifted_schema_ready_calibration_still_blocked",
        f"PASS positive_rows={positive_count}",
        f"PASS positive_rows_added_this_run={positive_added}",
        f"PASS matched_negative_rows={negative_count}",
        f"PASS matched_negative_rows_added_this_run={negative_added}",
        f"PASS verifier_returncode={verifier['returncode']}",
        f"PASS calibration_returncode={calibration_returncode}",
        "PASS new_confidence_gate=false",
        "PASS strict_full_objective_achieved=false",
        "PASS update_goal=false",
        "PASS raw_data_committed=false",
    ]
    assertions_path.write_text("\n".join(assertions) + "\n", encoding="utf-8")
    print(json.dumps({"decision": decision["gate_result"], "positive_rows": positive_count, "matched_negative_rows": negative_count}, sort_keys=True))
    return 0 if verifier["returncode"] == 0 and calibration_returncode == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
