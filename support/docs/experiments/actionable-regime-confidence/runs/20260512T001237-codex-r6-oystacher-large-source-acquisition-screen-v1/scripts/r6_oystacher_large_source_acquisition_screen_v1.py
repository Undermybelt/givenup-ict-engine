#!/usr/bin/env python3
"""Screen official Oystacher/3 Red CFTC sources for large R6 row supply."""

from __future__ import annotations

import csv
import hashlib
import json
import re
import subprocess
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


RUN_ID = "20260512T001237-codex-r6-oystacher-large-source-acquisition-screen-v1"
REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs" / RUN_ID
OUT = RUN_ROOT / "r6-oystacher-large-source-acquisition-screen"
CHECKS = RUN_ROOT / "checks"
CMD = RUN_ROOT / "command-output"
RAW = Path("/tmp/ict-engine-r6-oystacher-large-source-acquisition-screen-v1")
BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"
DEBT_JSON = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs"
    / "20260512T000801-codex-r6-exact-split-support-debt-audit-v1"
    / "r6-exact-split-support-debt-audit/r6_exact_split_support_debt_audit_v1.json"
)

COMPLAINT_URL = "https://www.cftc.gov/sites/default/files/idc/groups/public/%40lrenforcementactions/documents/legalpleading/enfigorcomplnt101915.pdf"
PRESS_URL = "https://www.cftc.gov/PressRoom/PressReleases/7253-15"
SOURCE_REPORT = "CFTC Complaint: CFTC v. Igor B. Oystacher and 3 Red Trading LLC, filed Oct. 19 2015"

MARKET_ROWS = [
    {
        "market_family": "metals",
        "instrument_scope": "High-Grade Copper futures",
        "trading_days": 14,
        "flip_sequences": 288,
        "spoof_orders": 1633,
        "spoof_contracts": 24354,
    },
    {
        "market_family": "energy",
        "instrument_scope": "Crude Oil futures",
        "trading_days": 4,
        "flip_sequences": 324,
        "spoof_orders": 1102,
        "spoof_contracts": 26204,
    },
    {
        "market_family": "energy",
        "instrument_scope": "Natural Gas futures",
        "trading_days": 3,
        "flip_sequences": 330,
        "spoof_orders": 1574,
        "spoof_contracts": 29590,
    },
    {
        "market_family": "volatility_index",
        "instrument_scope": "VIX futures",
        "trading_days": 19,
        "flip_sequences": 89,
        "spoof_orders": 284,
        "spoof_contracts": 37694,
    },
    {
        "market_family": "equity_index",
        "instrument_scope": "E-mini S&P 500 futures, June 2013 contract",
        "trading_days": 2,
        "flip_sequences": 59,
        "spoof_orders": 202,
        "spoof_contracts": 35523,
    },
    {
        "market_family": "equity_index",
        "instrument_scope": "E-mini S&P 500 futures, December 2013 and January 2014 contracts",
        "trading_days": 9,
        "flip_sequences": 226,
        "spoof_orders": 412,
        "spoof_contracts": 206425,
    },
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def download(url: str, path: Path) -> dict[str, object]:
    request = urllib.request.Request(url, headers={"User-Agent": "ict-engine-board-a-audit/1.0"})
    with urllib.request.urlopen(request, timeout=60) as response:
        body = response.read()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(body)
        return {
            "url": url,
            "path": str(path),
            "http_status": getattr(response, "status", None),
            "content_type": response.headers.get("content-type", ""),
            "bytes": len(body),
            "sha256": sha256(path),
        }


def extract_pdf_text(pdf: Path, out: Path) -> dict[str, object]:
    script = (
        "from pathlib import Path\n"
        "from pypdf import PdfReader\n"
        f"pdf=Path({str(pdf)!r})\n"
        f"out=Path({str(out)!r})\n"
        "reader=PdfReader(str(pdf))\n"
        "out.write_text('\\n'.join(page.extract_text() or '' for page in reader.pages), encoding='utf-8')\n"
        "print(len(reader.pages))\n"
    )
    completed = subprocess.run(
        ["uv", "run", "--with", "pypdf", "python", "-c", script],
        cwd=REPO,
        text=True,
        capture_output=True,
        timeout=180,
        check=False,
    )
    (CMD / "extract_oystacher_pdf.stdout.txt").write_text(completed.stdout, encoding="utf-8")
    (CMD / "extract_oystacher_pdf.stderr.txt").write_text(completed.stderr, encoding="utf-8")
    pages = int((completed.stdout.strip().splitlines() or ["0"])[-1]) if completed.returncode == 0 else 0
    return {
        "returncode": completed.returncode,
        "stdout_path": str((CMD / "extract_oystacher_pdf.stdout.txt").relative_to(REPO)),
        "stderr_path": str((CMD / "extract_oystacher_pdf.stderr.txt").relative_to(REPO)),
        "text_path": str(out),
        "page_count": pages,
        "text_sha256": sha256(out) if out.exists() else "",
    }


def norm(text: str) -> str:
    return " ".join(text.split())


def main() -> int:
    for path in [OUT, CHECKS, CMD, RAW]:
        path.mkdir(parents=True, exist_ok=True)

    board_hash = sha256(BOARD)
    debt = json.loads(DEBT_JSON.read_text(encoding="utf-8"))
    complaint_pdf = RAW / "enfigorcomplnt101915.pdf"
    complaint_txt = RAW / "enfigorcomplnt101915.txt"
    press_html = RAW / "press_7253_15.html"
    complaint_download = download(COMPLAINT_URL, complaint_pdf)
    press_download = download(PRESS_URL, press_html)
    extract = extract_pdf_text(complaint_pdf, complaint_txt)
    text = complaint_txt.read_text(encoding="utf-8", errors="replace")
    compact = norm(text)

    snippet_checks = {
        "fifty_one_trading_days": "at least fifty-one trading days" in compact,
        "one_thousand_three_hundred_sixteen": "at least 1316 times" in compact,
        "five_thousand_two_hundred_seven": "5,207" in compact,
        "appendix_exhibit_a_attached": "attached as Exhibit A" in compact,
        "market_table_total": bool(re.search(r"Total\s+51\s+1,316\s+5,207\s+359,790", compact)),
    }
    totals = {
        "trading_days": sum(int(row["trading_days"]) for row in MARKET_ROWS),
        "flip_sequences": sum(int(row["flip_sequences"]) for row in MARKET_ROWS),
        "spoof_orders": sum(int(row["spoof_orders"]) for row in MARKET_ROWS),
        "spoof_contracts": sum(int(row["spoof_contracts"]) for row in MARKET_ROWS),
    }
    debt_summary = debt["debt_summary"]
    materialization_assessment = {
        "public_pdf_page_count": extract["page_count"],
        "appendix_exhibit_a_referenced": snippet_checks["appendix_exhibit_a_attached"],
        "appendix_rows_visible_in_public_pdf": False,
        "row_level_materialization_status": "source_owner_appendix_required",
        "flip_sequences_cover_chronological_debt": totals["flip_sequences"] >= debt_summary["additional_positive_rows_for_chrono_quantiles_before_symbol_venue"],
        "spoof_orders_cover_exact_bucket_debt_if_appendix_has_timestamps": totals["spoof_orders"] >= debt_summary["total_pairwise_rows_needed_if_existing_exact_buckets_are_filled"],
        "matched_control_feasibility": "same-source flip orders are plausible matched controls but require Exhibit A timestamps/order legs before acceptance",
    }
    fields = [
        "market_family",
        "instrument_scope",
        "trading_days",
        "flip_sequences",
        "spoof_orders",
        "spoof_contracts",
    ]
    market_csv = OUT / "r6_oystacher_large_source_market_counts_v1.csv"
    write_csv(market_csv, MARKET_ROWS, fields)

    result = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "board_sha256_at_start": board_hash,
        "source_report": SOURCE_REPORT,
        "downloads": {
            "complaint": complaint_download,
            "press_release": press_download,
            "raw_payload_committed": False,
        },
        "pdf_extraction": extract,
        "snippet_checks": snippet_checks,
        "market_counts": {
            "rows": MARKET_ROWS,
            "totals": totals,
            "csv": str(market_csv.relative_to(REPO)),
        },
        "debt_reference": {
            "json": str(DEBT_JSON.relative_to(REPO)),
            "additional_positive_rows_for_chrono_quantiles_before_symbol_venue": debt_summary["additional_positive_rows_for_chrono_quantiles_before_symbol_venue"],
            "total_pairwise_rows_needed_if_existing_exact_buckets_are_filled": debt_summary["total_pairwise_rows_needed_if_existing_exact_buckets_are_filled"],
        },
        "materialization_assessment": materialization_assessment,
        "gate_result": "r6_oystacher_large_source_acquisition_screen_v1=official_large_row_source_found_appendix_required_not_materialized",
        "accepted_rows_added": 0,
        "new_confidence_gate": False,
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "shared_intake_mutated": False,
        "external_requests_sent": True,
        "trade_usable": False,
        "next_action": "Acquire the Oystacher Exhibit A row appendix or an owner-approved equivalent row export; if unavailable, get owner approval for a market-family/venue-family heldout split contract before continuing R6 split acceptance.",
    }
    json_path = OUT / "r6_oystacher_large_source_acquisition_screen_v1.json"
    md_path = OUT / "r6_oystacher_large_source_acquisition_screen_v1.md"
    assertions_path = CHECKS / "r6_oystacher_large_source_acquisition_screen_v1_assertions.out"
    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    lines = [
        "# R6 Oystacher Large Source Acquisition Screen v1",
        "",
        f"- Run id: `{RUN_ID}`.",
        f"- Official CFTC complaint URL: `{COMPLAINT_URL}`.",
        f"- Official CFTC press URL: `{PRESS_URL}`.",
        f"- Source totals from the complaint table: trading days `{totals['trading_days']}`, flip sequences `{totals['flip_sequences']}`, spoof orders `{totals['spoof_orders']}`, spoof contracts `{totals['spoof_contracts']}`.",
        f"- Debt reference: chronological positive/control debt `{debt_summary['additional_positive_rows_for_chrono_quantiles_before_symbol_venue']}`, exact-bucket pairwise debt `{debt_summary['total_pairwise_rows_needed_if_existing_exact_buckets_are_filled']}`.",
        f"- Exhibit A referenced: `{str(materialization_assessment['appendix_exhibit_a_referenced']).lower()}`; appendix rows visible in public PDF: `false`.",
        "- This is a source-acquisition screen only: no rows are accepted until the appendix or an owner-approved equivalent row export is acquired and parsed.",
        f"- Gate result: `{result['gate_result']}`.",
        "- Accepted rows added: `0`; new confidence gate: `false`; strict full objective achieved: `false`; `update_goal=false`.",
        "",
        "## Artifacts",
        "",
        f"- JSON: `{json_path.relative_to(REPO)}`",
        f"- Report: `{md_path.relative_to(REPO)}`",
        f"- Market counts CSV: `{market_csv.relative_to(REPO)}`",
        f"- Assertions: `{assertions_path.relative_to(REPO)}`",
    ]
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    assertions = [
        ("complaint_download_http_200", complaint_download["http_status"] == 200),
        ("press_download_http_200", press_download["http_status"] == 200),
        ("pdf_extract_returncode_0", extract["returncode"] == 0),
        ("snippet_fifty_one_days", snippet_checks["fifty_one_trading_days"]),
        ("snippet_1316_flips", snippet_checks["one_thousand_three_hundred_sixteen"]),
        ("snippet_5207_spoof_orders", snippet_checks["five_thousand_two_hundred_seven"]),
        ("snippet_exhibit_a", snippet_checks["appendix_exhibit_a_attached"]),
        ("table_totals_match", totals == {"trading_days": 51, "flip_sequences": 1316, "spoof_orders": 5207, "spoof_contracts": 359790}),
        ("strict_full_objective_false", result["strict_full_objective_achieved"] is False),
        ("update_goal_false", result["update_goal"] is False),
    ]
    assertions_path.write_text(
        "\n".join(f"{name}={'PASS' if passed else 'FAIL'}" for name, passed in assertions) + "\n",
        encoding="utf-8",
    )
    if not all(passed for _, passed in assertions):
        raise SystemExit(2)
    print(json.dumps({"gate_result": result["gate_result"], "flip_sequences": totals["flip_sequences"], "spoof_orders": totals["spoof_orders"], "update_goal": False}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
