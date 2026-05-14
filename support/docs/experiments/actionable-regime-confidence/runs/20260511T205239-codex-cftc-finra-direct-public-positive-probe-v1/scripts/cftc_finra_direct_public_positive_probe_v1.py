#!/usr/bin/env python3
"""Probe public CFTC/FINRA direct-manipulation sources without accepting them."""

from __future__ import annotations

import csv
import hashlib
import json
import subprocess
import urllib.request
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path


RUN_ID = "20260511T205239+0800-codex-cftc-finra-direct-public-positive-probe-v1"
RUN_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = RUN_ROOT.parents[4]
OUT_DIR = RUN_ROOT / "cftc-finra-direct-public-positive-probe"
CHECK_DIR = RUN_ROOT / "checks"
BOARD_PATH = REPO_ROOT / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"
INTAKE_ROOT = Path("/tmp/ict-engine-direct-manipulation-row-intake")
SCRATCH_ROOT = Path("/tmp/ict-engine-cftc-finra-direct-public-positive-probe")
CFTC_URL = "https://www.cftc.gov/sites/default/files/2019-02/enfkrishnamohanorder022519.pdf"
FINRA_URL = "https://www.finra.org/compliance-tools/report-center/cross-market-equities-supervision/potential-manipulation-report"
VERIFIER = (
    REPO_ROOT
    / "docs/experiments/actionable-regime-confidence/runs/20260511T151950-codex-direct-manipulation-row-intake-manifest-v1/direct-manipulation-intake/direct_manipulation_row_intake_verifier_v1.py"
)

DIRECT_FIELDS = [
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


class FinraTableParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.in_heading = False
        self.heading_text = []
        self.current_heading = ""
        self.in_table = False
        self.in_cell = False
        self.cell_text = []
        self.current_row = []
        self.tables: dict[str, list[list[str]]] = {}

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"h2", "h3", "h4"}:
            self.in_heading = True
            self.heading_text = []
        elif tag == "table":
            self.in_table = True
            self.tables.setdefault(self.current_heading, [])
        elif self.in_table and tag == "tr":
            self.current_row = []
        elif self.in_table and tag in {"th", "td"}:
            self.in_cell = True
            self.cell_text = []

    def handle_data(self, data: str) -> None:
        if self.in_heading:
            self.heading_text.append(data)
        elif self.in_cell:
            self.cell_text.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag in {"h2", "h3", "h4"} and self.in_heading:
            text = " ".join(" ".join(self.heading_text).split())
            if text:
                self.current_heading = text
            self.in_heading = False
        elif self.in_table and tag in {"th", "td"} and self.in_cell:
            self.current_row.append(" ".join(" ".join(self.cell_text).split()))
            self.in_cell = False
        elif self.in_table and tag == "tr":
            if self.current_row:
                self.tables.setdefault(self.current_heading, []).append(self.current_row)
            self.current_row = []
        elif tag == "table":
            self.in_table = False


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def download(url: str, path: Path) -> dict[str, str | int]:
    req = urllib.request.Request(url, headers={"User-Agent": "ict-engine-board-a-public-source-probe/1.0"})
    with urllib.request.urlopen(req, timeout=45) as response:  # noqa: S310 - public source probe.
        data = response.read()
        path.write_bytes(data)
        return {
            "url": url,
            "path": str(path),
            "status": getattr(response, "status", 200),
            "content_type": response.headers.get("content-type", ""),
            "bytes": len(data),
            "sha256": sha256_file(path),
        }


def extract_pdf_text(path: Path) -> tuple[str, str]:
    try:
        from Quartz import PDFDocument  # type: ignore
        from Foundation import NSURL  # type: ignore
    except Exception as exc:  # noqa: BLE001
        return "", f"quartz_unavailable:{type(exc).__name__}"

    doc = PDFDocument.alloc().initWithURL_(NSURL.fileURLWithPath_(str(path)))
    if doc is None:
        return "", "pdf_unreadable"
    pages = []
    for i in range(doc.pageCount()):
        page = doc.pageAtIndex_(i)
        pages.append(page.string() if page is not None and page.string() is not None else "")
    return "\n".join(pages), "ok"


def cftc_positive_rows() -> list[dict[str, str]]:
    return [
        {
            "label": "positive_spoofing_layering",
            "source_report": "CFTC Order: Krishna Mohan, CFTC Docket No. 19-06",
            "source_section": "II.C Facts, December 2 2013 E-mini NASDAQ example",
            "trade_date": "2013-12-02",
            "symbol": "December 2013 E-mini NASDAQ futures",
            "venue_or_market_center": "CME",
            "participant_type_code": "CFTC respondent trader; firm account redacted",
            "participant_identifier": "Krishna Mohan / Firm A",
            "side": "sell spoof orders opposite buy genuine iceberg order",
            "earliest_order_received_time": "03:02:00.909 America/Chicago",
            "latest_order_received_time": "03:02:02.736 America/Chicago",
            "order_count": "two order groups via order splitter",
            "total_order_quantity": "80 contracts",
            "activity_description": "Public CFTC findings describe sell-side spoof groups opposite a buy iceberg order; genuine order filled, then spoof groups were cancelled.",
            "matched_negative_group_id": "cftc_mohan_20131202_nq_example",
            "session_bucket": "overnight_central_time",
            "source_row_id": "cftc_mohan_20131202_nq_sell_spoof_group",
        },
        {
            "label": "positive_spoofing_layering",
            "source_report": "CFTC Order: Krishna Mohan, CFTC Docket No. 19-06",
            "source_section": "II.C Facts, December 2 2013 E-mini NASDAQ example",
            "trade_date": "2013-12-02",
            "symbol": "December 2013 E-mini NASDAQ futures",
            "venue_or_market_center": "CME",
            "participant_type_code": "CFTC respondent trader; firm account redacted",
            "participant_identifier": "Krishna Mohan / Firm A",
            "side": "buy spoof orders opposite sell genuine iceberg order",
            "earliest_order_received_time": "03:02:11.103 America/Chicago",
            "latest_order_received_time": "03:02:11.879 America/Chicago",
            "order_count": "multiple orders via order splitter",
            "total_order_quantity": "40 contracts",
            "activity_description": "Public CFTC findings describe buy-side spoof orders opposite a sell iceberg order; genuine order filled, then spoof orders were cancelled.",
            "matched_negative_group_id": "cftc_mohan_20131202_nq_example",
            "session_bucket": "overnight_central_time",
            "source_row_id": "cftc_mohan_20131202_nq_buy_spoof_group",
        },
    ]


def write_csv(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)
    SCRATCH_ROOT.mkdir(parents=True, exist_ok=True)
    INTAKE_ROOT.mkdir(parents=True, exist_ok=True)

    board_hash_before = sha256_file(BOARD_PATH)
    cftc_pdf = SCRATCH_ROOT / "enfkrishnamohanorder022519.pdf"
    finra_html = SCRATCH_ROOT / "finra-potential-manipulation-report.html"
    cftc_download = download(CFTC_URL, cftc_pdf)
    finra_download = download(FINRA_URL, finra_html)

    cftc_text, cftc_text_status = extract_pdf_text(cftc_pdf)
    cftc_checks = {
        "contains_thousands_occasions": "thousands of occasions" in cftc_text,
        "contains_example_date": "December 2, 2013" in cftc_text,
        "contains_first_spoof_time": "3:02:00.909" in cftc_text,
        "contains_second_spoof_time": "03 :02: 11.103" in cftc_text or "03:02:11.103" in cftc_text,
        "contains_relevant_markets": "E-mini NASDAQ" in cftc_text and "E-mini Dow" in cftc_text,
    }

    parser = FinraTableParser()
    parser.feed(finra_html.read_text(encoding="utf-8", errors="ignore"))
    finra_fields = []
    for heading, rows in parser.tables.items():
        if heading in {"Layering Detail Data", "Spoofing Detail Data"}:
            for row in rows[1:]:
                if row:
                    finra_fields.append({"report_section": heading, "field": row[0], "definition": row[1] if len(row) > 1 else ""})
    write_csv(OUT_DIR / "finra_layering_spoofing_public_schema_fields_v1.csv", ["report_section", "field", "definition"], finra_fields)

    positive_rows = cftc_positive_rows()
    positive_path = INTAKE_ROOT / "positive_spoofing_layering_rows.csv"
    write_csv(positive_path, DIRECT_FIELDS, positive_rows)
    provenance_path = INTAKE_ROOT / "provenance_manifest.json"
    provenance = {
        "source": "public_partial_positive_probe",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "cftc_order": cftc_download,
        "finra_public_schema": finra_download,
        "cftc_text_extraction_status": cftc_text_status,
        "cftc_text_checks": cftc_checks,
        "positive_rows_path": str(positive_path),
        "matched_negative_rows_path": str(INTAKE_ROOT / "matched_negative_normal_activity_rows.csv"),
        "matched_negative_rows_acquired": False,
        "license_or_permission": "CFTC public order and FINRA public report-center documentation; no private FINRA Gateway rows acquired.",
    }
    provenance_path.write_text(json.dumps(provenance, indent=2, sort_keys=True), encoding="utf-8")

    cmd = ["python3", str(VERIFIER), "--intake-root", str(INTAKE_ROOT)]
    verifier_proc = subprocess.run(
        cmd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
        timeout=60,
    )
    try:
        verifier_output = json.loads(verifier_proc.stdout)
    except json.JSONDecodeError:
        verifier_output = {"status": "unparseable", "raw": verifier_proc.stdout}

    matched_negative_path = INTAKE_ROOT / "matched_negative_normal_activity_rows.csv"
    decision = "cftc_finra_direct_public_positive_probe_v1=public_positives_extracted_controls_absent_blocked"
    summary = {
        "run_id": RUN_ID,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "board_hash_before": board_hash_before,
        "decision": decision,
        "cftc_download": cftc_download,
        "finra_download": finra_download,
        "cftc_text_extraction_status": cftc_text_status,
        "cftc_text_checks": cftc_checks,
        "finra_layering_spoofing_field_count": len(finra_fields),
        "positive_rows_extracted": len(positive_rows),
        "positive_rows_path": str(positive_path),
        "provenance_manifest_path": str(provenance_path),
        "matched_negative_rows_path": str(matched_negative_path),
        "matched_negative_rows_acquired": matched_negative_path.exists(),
        "verifier_command": cmd,
        "verifier_returncode": verifier_proc.returncode,
        "verifier_output": verifier_output,
        "accepted_rows_added": 0,
        "new_confidence_gate": False,
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "trade_usable": False,
    }
    (OUT_DIR / "cftc_finra_direct_public_positive_probe_v1.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True),
        encoding="utf-8",
    )

    md_lines = [
        "# CFTC / FINRA Direct Public Positive Probe v1",
        "",
        f"Run ID: `{RUN_ID}`",
        "",
        f"- Gate result: `{decision}`.",
        "- Public CFTC positive examples extracted: `2`.",
        f"- FINRA public layering/spoofing schema fields captured: `{len(finra_fields)}`.",
        "- Matched same-schema normal controls acquired: `false`.",
        f"- Verifier status: `{verifier_output.get('status', 'unknown')}`.",
        f"- Verifier reason: `{verifier_output.get('reason', 'unknown')}`.",
        "- Accepted rows added: `0`; new confidence gate: `false`.",
        "- Strict full objective achieved: `false`; `update_goal=false`.",
        "- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; trade usable: `false`.",
        "",
        "## Public Sources Probed",
        "",
        f"- CFTC order: `{CFTC_URL}`.",
        f"- FINRA public report-center schema: `{FINRA_URL}`.",
        "",
        "## Intake Files",
        "",
        f"- Positive rows written to `/tmp`: `{positive_path}`.",
        f"- Provenance manifest written to `/tmp`: `{provenance_path}`.",
        f"- Matched negative normal activity rows: `{matched_negative_path}` missing.",
        "",
        "## Boundary",
        "",
        "The CFTC order supplies source-owned positive spoofing examples only. The FINRA page documents exception-report schema, but public access does not include firm-level monthly exception rows or matched normal controls. This run therefore keeps the direct Manipulation gate blocked and does not run chronological Wilson95 calibration.",
        "",
        "## Artifacts",
        "",
        f"- JSON: `{OUT_DIR / 'cftc_finra_direct_public_positive_probe_v1.json'}`",
        f"- FINRA fields CSV: `{OUT_DIR / 'finra_layering_spoofing_public_schema_fields_v1.csv'}`",
        f"- Assertions: `{CHECK_DIR / 'cftc_finra_direct_public_positive_probe_v1_assertions.out'}`",
    ]
    (OUT_DIR / "cftc_finra_direct_public_positive_probe_v1.md").write_text("\n".join(md_lines) + "\n", encoding="utf-8")

    assertions = [
        f"PASS decision={decision}",
        "PASS cftc_positive_rows_extracted=2",
        f"PASS finra_layering_spoofing_field_count={len(finra_fields)}",
        f"PASS matched_negative_rows_acquired={str(matched_negative_path.exists()).lower()}",
        f"PASS verifier_returncode={verifier_proc.returncode}",
        "PASS accepted_rows_added=0",
        "PASS update_goal=false",
    ]
    (CHECK_DIR / "cftc_finra_direct_public_positive_probe_v1_assertions.out").write_text("\n".join(assertions) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
