#!/usr/bin/env python3
"""Materialize public Oystacher Exhibit A rows into an isolated R6 candidate."""

from __future__ import annotations

import csv
import hashlib
import json
import math
import re
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


RUN_ID = "20260512T002000-codex-r6-oystacher-exhibit-a-row-materialization-v1"
REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs" / RUN_ID
OUT = RUN_ROOT / "r6-oystacher-exhibit-a-row-materialization"
CMD = RUN_ROOT / "command-output"
CHECKS = RUN_ROOT / "checks"
BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"
TMP = Path("/tmp/ict-engine-oystacher-exhibit-a-row-materialization-v1")
PDF = TMP / "gov.uscourts.ilnd.316889.1.1.oystacher_exhibit_a.pdf"
PYPDF_TARGET = Path("/tmp/ict-engine-pypdf-py313")
PDF_URL = "https://storage.courtlistener.com/recap/gov.uscourts.ilnd.316889/gov.uscourts.ilnd.316889.1.1.pdf"
COURTLISTENER_DOCKET_URL = "https://www.courtlistener.com/docket/4263217/us-commodity-futures-trading-commission-v-oystacher/"
CFTC_COMPLAINT_URL = "https://www.cftc.gov/sites/default/files/idc/groups/public/%40lrenforcementactions/documents/legalpleading/enfigorcomplnt101915.pdf"
CFTC_PRESS_URL = "https://www.cftc.gov/PressRoom/PressReleases/7253-15"
DIRECT_VERIFIER = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs"
    / "20260511T151950-codex-direct-manipulation-row-intake-manifest-v1"
    / "direct-manipulation-intake/direct_manipulation_row_intake_verifier_v1.py"
)
INTAKE = OUT / "isolated-oystacher-exhibit-a-intake"
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
Z_95 = 1.96
MIN_WILSON = 0.95


ROW_RE = re.compile(
    r"^\s*(?P<record>\d+)\s*(?P<prefix>.*?)\s+"
    r"(?P<day>\d{1,2})\s*-\s*(?P<mon>[A-Za-z]{3})\s*-\s*(?P<yy>\d{2})\s+"
    r"(?P<time>\d{2}:\d{2}:\d{2}\.\d{3})\s+"
    r"(?P<order_id>\d+)\s+(?P<order_at>\S+)\s+"
    r"(?P<side_type>SPOOF|FLIP)\s+(?P<buy_sell>[BS])\s+"
    r"(?P<price>[0-9]+(?:\.[0-9]+)?)\s+(?P<qty>\d+)"
)


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO))
    except ValueError:
        return str(path)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def run_cmd(name: str, args: list[str], timeout: int = 120) -> dict[str, Any]:
    CMD.mkdir(parents=True, exist_ok=True)
    proc = subprocess.run(args, cwd=REPO, text=True, capture_output=True, timeout=timeout, check=False)
    stdout = CMD / f"{name}.stdout.txt"
    stderr = CMD / f"{name}.stderr.txt"
    exit_path = CMD / f"{name}.exit"
    stdout.write_text(proc.stdout, encoding="utf-8")
    stderr.write_text(proc.stderr, encoding="utf-8")
    exit_path.write_text(f"{proc.returncode}\n", encoding="utf-8")
    parsed = None
    try:
        parsed = json.loads(proc.stdout)
    except json.JSONDecodeError:
        pass
    return {
        "name": name,
        "returncode": proc.returncode,
        "stdout_path": rel(stdout),
        "stderr_path": rel(stderr),
        "exit_path": rel(exit_path),
        "parsed": parsed,
    }


def ensure_pypdf() -> Any:
    PYPDF_TARGET.mkdir(parents=True, exist_ok=True)
    sys.path.insert(0, str(PYPDF_TARGET))
    try:
        from pypdf import PdfReader  # type: ignore

        return PdfReader
    except Exception:
        run_cmd(
            "uv_pypdf_install",
            ["uv", "pip", "install", "--python", "/opt/homebrew/bin/python3.13", "--target", str(PYPDF_TARGET), "pypdf"],
            timeout=180,
        )
        from pypdf import PdfReader  # type: ignore

        return PdfReader


def download_pdf() -> dict[str, Any]:
    TMP.mkdir(parents=True, exist_ok=True)
    return run_cmd("download_oystacher_exhibit_a_pdf", ["curl", "-L", "--max-time", "60", "-o", str(PDF), PDF_URL], timeout=90)


def normalize_line(line: str) -> str:
    text = line.replace("\x03", " ").replace("\u0372", "-").replace("Ͳ", "-")
    replacements = {
        "Ma y": "May",
        "M ay": "May",
        "Ja n": "Jan",
        "J an": "Jan",
        "Fe b": "Feb",
        "F eb": "Feb",
        "Ma r": "Mar",
        "M ar": "Mar",
        "Ju n": "Jun",
        "J un": "Jun",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    text = re.sub(r":\s+", ":", text)
    text = re.sub(r"(\d+)\.\s+(\d+)", r"\1.\2", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def parse_pdf_rows() -> tuple[list[dict[str, Any]], list[dict[str, Any]], int]:
    PdfReader = ensure_pypdf()
    reader = PdfReader(str(PDF))
    parsed: list[dict[str, Any]] = []
    unparsed: list[dict[str, Any]] = []
    for page_index, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        for line in text.splitlines():
            normalized = normalize_line(line)
            if not normalized or not re.match(r"^\d+", normalized):
                continue
            match = ROW_RE.match(normalized)
            if match:
                row = match.groupdict()
                row["record"] = int(row["record"])
                row["contract"] = "".join(row.pop("prefix").split())
                row["page"] = page_index
                row["trade_date_iso"] = f"20{row['yy']}-{month_number(row['mon'])}-{int(row['day']):02d}"
                parsed.append(row)
            elif "SPOOF" in normalized or "FLIP" in normalized:
                unparsed.append({"page": page_index, "line": normalized})
    parsed.sort(key=lambda row: row["record"])
    return parsed, unparsed, len(reader.pages)


def month_number(mon: str) -> str:
    months = {"Jan": "01", "Feb": "02", "Mar": "03", "Apr": "04", "May": "05", "Jun": "06", "Jul": "07", "Aug": "08", "Sep": "09", "Oct": "10", "Nov": "11", "Dec": "12"}
    return months.get(mon[:3], "00")


def symbol_name(contract: str) -> str:
    if contract.startswith("HG"):
        return "High-Grade Copper futures"
    if contract.startswith("CL"):
        return "Crude Oil futures"
    if contract.startswith("NG"):
        return "Natural Gas futures"
    if contract.startswith("VX"):
        return "VIX futures"
    if contract.startswith("ES"):
        return "E-mini S&P 500 futures"
    return contract


def market_family(contract: str) -> str:
    if contract.startswith("HG"):
        return "metals"
    if contract.startswith(("CL", "NG")):
        return "energy"
    if contract.startswith("VX"):
        return "volatility_index"
    if contract.startswith("ES"):
        return "equity_index"
    return "other"


def venue_name(contract: str) -> str:
    if contract.startswith("HG"):
        return "COMEX/CME Globex"
    if contract.startswith(("CL", "NG")):
        return "NYMEX/CME Globex"
    if contract.startswith("VX"):
        return "CFE/CBOE Futures Exchange"
    if contract.startswith("ES"):
        return "CME Globex"
    return "US futures exchange / court exhibit"


def session_bucket(time_text: str) -> str:
    hour = int(time_text[:2])
    if hour < 8:
        return "early_us_central_time"
    if hour < 14:
        return "regular_us_central_time"
    return "late_us_central_time"


def grouped_rows(parsed: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    positives: list[dict[str, Any]] = []
    negatives: list[dict[str, Any]] = []
    group_index = 0
    current_group = ""
    positive_group_ids: set[str] = set()
    negative_group_ids: set[str] = set()
    for row in parsed:
        if not current_group:
            group_index += 1
            current_group = f"cftc_oystacher_exhibit_a_flip_sequence_{group_index:04d}"
        common = {
            "source_report": "Court-filed Exhibit A: CFTC v. Igor Oystacher and 3Red Trading LLC, N.D. Ill. 1:15-cv-09196, Document 1-1",
            "source_section": f"Exhibit A page {row['page']}, record {row['record']}",
            "trade_date": row["trade_date_iso"],
            "symbol": symbol_name(row["contract"]),
            "venue_or_market_center": venue_name(row["contract"]),
            "participant_type_code": "CFTC defendant trader; 3Red Trading LLC",
            "participant_identifier": "Igor Oystacher / 3Red Trading LLC",
            "earliest_order_received_time": f"{row['time']} America/Chicago",
            "latest_order_received_time": f"{row['time']} America/Chicago",
            "order_count": "1 court-exhibit order row",
            "total_order_quantity": row["qty"],
            "matched_negative_group_id": current_group,
            "session_bucket": session_bucket(row["time"]),
            "source_row_id": f"cftc_oystacher_exhibit_a_record_{row['record']:05d}",
        }
        if row["side_type"] == "SPOOF":
            out = {
                **common,
                "label": "positive_spoofing_layering",
                "side": f"{row['buy_sell']} spoof order; price={row['price']}; contract={row['contract']}; order_id={row['order_id']}; order_at={row['order_at']}",
                "activity_description": "Court-filed Exhibit A marks this order row as SPOOF in an Oystacher flip sequence.",
            }
            positives.append(out)
            positive_group_ids.add(current_group)
        else:
            out = {
                **common,
                "label": "matched_negative_normal_activity",
                "side": f"{row['buy_sell']} flip order; price={row['price']}; contract={row['contract']}; order_id={row['order_id']}; order_at={row['order_at']}",
                "activity_description": "Court-filed Exhibit A marks this row as FLIP; used here only as same-source matched control candidate for the preceding spoof sequence.",
            }
            negatives.append(out)
            negative_group_ids.add(current_group)
            current_group = ""
    orphan_groups = sorted(positive_group_ids - negative_group_ids)
    if orphan_groups:
        positives = [row for row in positives if row["matched_negative_group_id"] not in orphan_groups]
    return positives, negatives, {
        "groups_started": group_index,
        "positive_groups": len({row["matched_negative_group_id"] for row in positives}),
        "negative_groups": len({row["matched_negative_group_id"] for row in negatives}),
        "orphan_positive_groups_dropped": len(orphan_groups),
    }


def wilson_lcb(successes: int, total: int) -> float:
    if total <= 0:
        return 0.0
    p = successes / total
    z2 = Z_95 * Z_95
    denom = 1.0 + z2 / total
    centre = p + z2 / (2.0 * total)
    margin = Z_95 * math.sqrt((p * (1.0 - p) + z2 / (4.0 * total)) / total)
    return max(0.0, (centre - margin) / denom)


def split_metrics(positives: list[dict[str, Any]], negatives: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    all_rows = [(row, "positive") for row in positives] + [(row, "negative") for row in negatives]
    for axis, getter in [
        ("contract_family", lambda r: market_family(str(r["side"]).split("contract=")[-1].split(";")[0])),
        ("venue_exact", lambda r: r["venue_or_market_center"]),
        ("symbol_exact", lambda r: r["symbol"]),
        ("chronological_year", lambda r: r["trade_date"][:4]),
    ]:
        buckets = sorted({getter(row) for row, _ in all_rows})
        for bucket in buckets:
            pos = sum(1 for row, klass in all_rows if klass == "positive" and getter(row) == bucket)
            neg = sum(1 for row, klass in all_rows if klass == "negative" and getter(row) == bucket)
            rows.append(
                {
                    "axis": axis,
                    "bucket": bucket,
                    "positive_support": pos,
                    "negative_support": neg,
                    "min_wilson95_lcb": round(min(wilson_lcb(pos, pos), wilson_lcb(neg, neg)), 12),
                    "pooled95_pass": pos >= 73 and neg >= 73 and min(wilson_lcb(pos, pos), wilson_lcb(neg, neg)) >= MIN_WILSON,
                }
            )
    return rows


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    CMD.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)
    INTAKE.mkdir(parents=True, exist_ok=True)

    download = download_pdf()
    parsed, unparsed, page_count = parse_pdf_rows()
    positives, negatives, group_stats = grouped_rows(parsed)

    positive_csv = INTAKE / "positive_spoofing_layering_rows.csv"
    negative_csv = INTAKE / "matched_negative_normal_activity_rows.csv"
    provenance_path = INTAKE / "provenance_manifest.json"
    parsed_csv = OUT / "oystacher_exhibit_a_parsed_order_rows_v1.csv"
    unparsed_csv = OUT / "oystacher_exhibit_a_unparsed_candidate_lines_v1.csv"
    metrics_csv = OUT / "oystacher_exhibit_a_split_metrics_v1.csv"
    write_csv(positive_csv, positives, REQUIRED_FIELDS)
    write_csv(negative_csv, negatives, REQUIRED_FIELDS)
    write_csv(parsed_csv, parsed, ["record", "contract", "trade_date_iso", "time", "order_id", "order_at", "side_type", "buy_sell", "price", "qty", "page", "day", "mon", "yy"])
    write_csv(unparsed_csv, unparsed, ["page", "line"])
    metrics = split_metrics(positives, negatives)
    write_csv(metrics_csv, metrics, ["axis", "bucket", "positive_support", "negative_support", "min_wilson95_lcb", "pooled95_pass"])
    provenance = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_pdf_url": PDF_URL,
        "courtlistener_docket_url": COURTLISTENER_DOCKET_URL,
        "cftc_complaint_url_without_exhibit_a": CFTC_COMPLAINT_URL,
        "cftc_press_url": CFTC_PRESS_URL,
        "raw_pdf_path_tmp": str(PDF),
        "raw_pdf_sha256": sha256(PDF),
        "raw_data_committed": False,
        "parser": "pypdf text extraction plus fail-closed regex row parser",
        "unparsed_candidate_lines_csv": rel(unparsed_csv),
        "thresholds_relaxed": False,
        "runtime_code_changed": False,
        "shared_intake_mutated": False,
    }
    write_json(provenance_path, provenance)

    verifier = run_cmd("direct_manipulation_row_intake_verifier", ["python3", str(DIRECT_VERIFIER), "--intake-root", str(INTAKE)])
    verifier_payload = verifier.get("parsed") or {}
    side_counts = Counter(row["side_type"] for row in parsed)
    contract_counts = Counter(row["contract"] for row in parsed)
    all_split_axes_pass = all(row["pooled95_pass"] for row in metrics if row["axis"] in {"contract_family", "venue_exact", "symbol_exact", "chronological_year"})
    result = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "board_sha256_at_start": sha256(BOARD),
        "source_pdf_url": PDF_URL,
        "courtlistener_docket_url": COURTLISTENER_DOCKET_URL,
        "pdf_pages": page_count,
        "download_returncode": download["returncode"],
        "raw_pdf_path_tmp": str(PDF),
        "raw_pdf_sha256": sha256(PDF),
        "parsed_order_rows": len(parsed),
        "unparsed_candidate_lines": len(unparsed),
        "side_counts": dict(side_counts),
        "contract_counts": dict(contract_counts),
        "positive_candidate_rows": len(positives),
        "matched_control_candidate_rows": len(negatives),
        "group_stats": group_stats,
        "isolated_intake_root": rel(INTAKE),
        "direct_verifier": verifier,
        "split_metrics_csv": rel(metrics_csv),
        "all_materialized_split_axes_pass": all_split_axes_pass,
        "source_accepted_for_live_canonical_intake": False,
        "accepted_rows_added": 0,
        "new_confidence_gate": False,
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "shared_intake_mutated": False,
        "trade_usable": False,
        "gate_result": "r6_oystacher_exhibit_a_row_materialization_v1=public_court_exhibit_rows_isolated_schema_ready_policy_review_required",
        "next_action": "Review whether public RECAP/PACER Exhibit A is acceptable source provenance for canonical R6 intake, then merge through a shared lock and rerun split/species plus downstream chain only if approved.",
    }
    json_path = OUT / "r6_oystacher_exhibit_a_row_materialization_v1.json"
    report_path = OUT / "r6_oystacher_exhibit_a_row_materialization_v1.md"
    assertions_path = CHECKS / "r6_oystacher_exhibit_a_row_materialization_v1_assertions.out"
    write_json(json_path, result)
    report = [
        "# R6 Oystacher Exhibit A Row Materialization v1",
        "",
        f"- Run id: `{RUN_ID}`.",
        f"- Public Exhibit A PDF: `{PDF_URL}`.",
        f"- Pages: `{page_count}`; parsed order rows: `{len(parsed)}`; unparsed candidate lines: `{len(unparsed)}`.",
        f"- Parsed side counts: `{dict(side_counts)}`.",
        f"- Isolated candidate intake verifier status: `{verifier_payload.get('status')}`; positives `{verifier_payload.get('positive_rows')}`; controls `{verifier_payload.get('matched_negative_rows')}`; matched groups `{verifier_payload.get('matched_group_count')}`.",
        f"- Split axes pass in isolated materialization: `{str(all_split_axes_pass).lower()}`.",
        "- Canonical live intake mutated: `false`; accepted rows added: `0`; source policy review required before promotion.",
        f"- Gate result: `{result['gate_result']}`.",
        "- Strict full objective achieved: `false`; `update_goal=false`.",
        "",
        "Artifacts:",
        f"- JSON: `{rel(json_path)}`",
        f"- Parsed rows CSV: `{rel(parsed_csv)}`",
        f"- Candidate positive CSV: `{rel(positive_csv)}`",
        f"- Candidate matched-control CSV: `{rel(negative_csv)}`",
        f"- Split metrics CSV: `{rel(metrics_csv)}`",
        f"- Unparsed candidate lines CSV: `{rel(unparsed_csv)}`",
        f"- Verifier stdout: `{verifier['stdout_path']}`",
        f"- Assertions: `{rel(assertions_path)}`",
    ]
    report_path.write_text("\n".join(report) + "\n", encoding="utf-8")
    assertions = {
        "pdf_downloaded": PDF.exists() and PDF.stat().st_size > 1_000_000,
        "parsed_rows_ge_6000": len(parsed) >= 6000,
        "positive_candidates_ge_5000": len(positives) >= 5000,
        "matched_controls_ge_1000": len(negatives) >= 1000,
        "isolated_verifier_schema_ready": verifier_payload.get("status") == "schema_ready_unscored",
        "canonical_live_intake_not_mutated": result["shared_intake_mutated"] is False,
        "accepted_rows_added_zero": result["accepted_rows_added"] == 0,
        "policy_review_required_no_goal_update": result["update_goal"] is False,
    }
    assertions_path.write_text("\n".join(f"{name}={'ok' if value else 'FAIL'}" for name, value in assertions.items()) + "\n", encoding="utf-8")
    if not all(assertions.values()):
        return 2
    print(json.dumps({"ok": True, "run_id": RUN_ID, "gate_result": result["gate_result"], "positive_candidates": len(positives), "matched_controls": len(negatives), "update_goal": False}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
