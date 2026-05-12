#!/usr/bin/env python3
"""Build a fail-closed Oystacher govinfo date-level source screen."""

from __future__ import annotations

import csv
import hashlib
import json
import math
import shutil
import subprocess
import sys
import tempfile
import urllib.request
from datetime import UTC, date, datetime
from pathlib import Path


RUN_ID = "20260512T001853-codex-r6-oystacher-govinfo-date-row-screen-v1"
RUN_ROOT = Path("docs/experiments/actionable-regime-confidence/runs") / RUN_ID
OUT_DIR = RUN_ROOT / "r6-oystacher-govinfo-date-row-screen"
CMD_DIR = RUN_ROOT / "command-output"
CHECK_DIR = RUN_ROOT / "checks"
BOARD = Path("docs/plans/2026-05-10-actionable-regime-confidence-todo.md")
DEBT_JSON = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260512T000801-codex-r6-exact-split-support-debt-audit-v1/"
    "r6-exact-split-support-debt-audit/r6_exact_split_support_debt_audit_v1.json"
)
SOURCE_URL = (
    "https://www.govinfo.gov/content/pkg/USCOURTS-ilnd-1_15-cv-09196/pdf/"
    "USCOURTS-ilnd-1_15-cv-09196-1.pdf"
)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def date_range(year: int, month: int, start: int, end: int) -> list[date]:
    return [date(year, month, day) for day in range(start, end + 1)]


def build_source_blocks() -> list[dict[str, object]]:
    return [
        {
            "block_id": "oystacher_comex_copper_dec2011",
            "instrument_scope": "COMEX copper contract on Globex",
            "symbol": "COMEX copper futures",
            "venue_or_market_center": "COMEX / CME Globex",
            "market_family": "metals",
            "order_count": 1633,
            "flip_sequences": 288,
            "trade_dates": (
                date_range(2011, 12, 1, 2)
                + date_range(2011, 12, 5, 9)
                + date_range(2011, 12, 12, 16)
                + date_range(2011, 12, 19, 20)
            ),
        },
        {
            "block_id": "oystacher_nymex_crude_may2012",
            "instrument_scope": "NYMEX crude oil contract on Globex",
            "symbol": "NYMEX crude oil futures",
            "venue_or_market_center": "NYMEX / CME Globex",
            "market_family": "energy",
            "order_count": 1102,
            "flip_sequences": 324,
            "trade_dates": [date(2012, 5, 7)] + date_range(2012, 5, 9, 11),
        },
        {
            "block_id": "oystacher_nymex_natural_gas_nov_dec2012",
            "instrument_scope": "NYMEX natural gas contract on Globex",
            "symbol": "NYMEX natural gas futures",
            "venue_or_market_center": "NYMEX / CME Globex",
            "market_family": "energy",
            "order_count": 1574,
            "flip_sequences": 330,
            "trade_dates": [date(2012, 11, 30)] + date_range(2012, 12, 3, 4),
        },
        {
            "block_id": "oystacher_cfe_vix_feb_mar2013",
            "instrument_scope": "CFE VIX contract",
            "symbol": "CFE VIX futures",
            "venue_or_market_center": "CFE",
            "market_family": "volatility_index",
            "order_count": 284,
            "flip_sequences": 89,
            "trade_dates": (
                date_range(2013, 2, 19, 22)
                + date_range(2013, 2, 25, 28)
                + [date(2013, 3, 1)]
                + date_range(2013, 3, 4, 7)
                + date_range(2013, 3, 11, 12)
                + date_range(2013, 3, 18, 21)
            ),
        },
        {
            "block_id": "oystacher_cme_es_jun_dec_jan2013_2014",
            "instrument_scope": "CME E-Mini S&P 500 contract on Globex",
            "symbol": "CME E-mini S&P 500 futures",
            "venue_or_market_center": "CME Globex",
            "market_family": "equity_index_futures",
            "order_count": 614,
            "flip_sequences": 285,
            "trade_dates": (
                date_range(2013, 6, 11, 12)
                + date_range(2013, 12, 16, 19)
                + date_range(2014, 1, 6, 10)
            ),
        },
    ]


def wilson_lcb_all_success(n: int, z: float = 1.96) -> float:
    if n <= 0:
        return 0.0
    phat = 1.0
    denom = 1.0 + z * z / n
    centre = phat + z * z / (2 * n)
    margin = z * math.sqrt((phat * (1 - phat) + z * z / (4 * n)) / n)
    return (centre - margin) / denom


def download_source(tmp: Path) -> dict[str, object]:
    request = urllib.request.Request(
        SOURCE_URL,
        headers={"User-Agent": "Mozilla/5.0 ict-engine-board-a-audit contact=research@example.com"},
    )
    with urllib.request.urlopen(request, timeout=45) as response:
        data = response.read()
        final_url = response.geturl()
        status = response.status
        content_type = response.headers.get("content-type", "")
    pdf_path = tmp / "govinfo_oystacher_doc195.pdf"
    pdf_path.write_bytes(data)
    (CMD_DIR / "govinfo_fetch.headers.txt").write_text(
        f"status={status}\ncontent-type={content_type}\nfinal-url={final_url}\nbytes={len(data)}\n",
        encoding="utf-8",
    )
    return {
        "http_status": status,
        "content_type": content_type,
        "final_url": final_url,
        "pdf_path": str(pdf_path),
        "pdf_bytes": len(data),
        "pdf_sha256": sha256_bytes(data),
    }


def extract_text(pdf_path: Path, tmp: Path) -> dict[str, object]:
    gs = shutil.which("gs") or "/opt/homebrew/bin/gs"
    text_path = tmp / "govinfo_oystacher_doc195.txt"
    cmd = [
        gs,
        "-q",
        "-dNOPAUSE",
        "-dBATCH",
        "-sDEVICE=txtwrite",
        f"-sOutputFile={text_path}",
        str(pdf_path),
    ]
    proc = subprocess.run(cmd, text=True, capture_output=True, timeout=90)
    (CMD_DIR / "ghostscript_extract.stdout.txt").write_text(proc.stdout, encoding="utf-8")
    (CMD_DIR / "ghostscript_extract.stderr.txt").write_text(proc.stderr, encoding="utf-8")
    (CMD_DIR / "ghostscript_extract.exit").write_text(str(proc.returncode), encoding="utf-8")
    text = text_path.read_text(encoding="utf-8", errors="replace") if text_path.exists() else ""
    return {
        "cmd": " ".join(cmd),
        "returncode": proc.returncode,
        "text_path": str(text_path),
        "text_bytes": len(text.encode("utf-8")),
        "text_sha256": sha256_file(text_path) if text_path.exists() else None,
        "markers": {
            "document_195": "Document #: 195" in text,
            "orders_1633": "1,633 orders" in text,
            "orders_1102": "1,102 orders" in text,
            "orders_1574": "1,574 orders" in text,
            "orders_284": "284 orders" in text,
            "orders_614": "614 orders" in text,
            "flip_288": "at least 288 times" in text,
            "flip_324": "at least 324 times" in text,
            "flip_330": "at least 330 times" in text,
            "flip_89": "at least 89 times" in text,
            "flip_285": "at least 285 times" in text,
        },
    }


def load_debt() -> dict[str, object]:
    if not DEBT_JSON.exists():
        return {}
    with DEBT_JSON.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def board_hash() -> str:
    return sha256_file(BOARD) if BOARD.exists() else "missing"


def write_outputs(download: dict[str, object], extraction: dict[str, object]) -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)

    blocks = build_source_blocks()
    rows: list[dict[str, object]] = []
    for block in blocks:
        for trade_date in block["trade_dates"]:  # type: ignore[index]
            rows.append(
                {
                    "candidate_status": "date_level_context_only_not_accepted",
                    "source_report": "GovInfo USCOURTS-ilnd-1_15-cv-09196 Document 195",
                    "source_url": SOURCE_URL,
                    "block_id": block["block_id"],
                    "trade_date": trade_date.isoformat(),
                    "symbol": block["symbol"],
                    "venue_or_market_center": block["venue_or_market_center"],
                    "market_family": block["market_family"],
                    "aggregate_order_count_for_block": block["order_count"],
                    "aggregate_flip_sequences_for_block": block["flip_sequences"],
                    "row_level_blocker": "no_exhibit_a_order_timestamp_appendix_in_public_govinfo_pdf",
                }
            )

    date_csv = OUT_DIR / "r6_oystacher_govinfo_date_context_candidates_v1.csv"
    with date_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    market_csv = OUT_DIR / "r6_oystacher_govinfo_market_blocks_v1.csv"
    with market_csv.open("w", newline="", encoding="utf-8") as handle:
        fieldnames = [
            "block_id",
            "instrument_scope",
            "symbol",
            "venue_or_market_center",
            "market_family",
            "order_count",
            "flip_sequences",
            "trading_days",
            "first_trade_date",
            "last_trade_date",
        ]
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for block in blocks:
            trade_dates = block["trade_dates"]  # type: ignore[index]
            writer.writerow(
                {
                    "block_id": block["block_id"],
                    "instrument_scope": block["instrument_scope"],
                    "symbol": block["symbol"],
                    "venue_or_market_center": block["venue_or_market_center"],
                    "market_family": block["market_family"],
                    "order_count": block["order_count"],
                    "flip_sequences": block["flip_sequences"],
                    "trading_days": len(trade_dates),
                    "first_trade_date": min(trade_dates).isoformat(),
                    "last_trade_date": max(trade_dates).isoformat(),
                }
            )

    debt = load_debt()
    v59_summary = debt.get("debt_summary", debt.get("summary", {})) if isinstance(debt, dict) else {}
    total_orders = sum(int(block["order_count"]) for block in blocks)
    total_flips = sum(int(block["flip_sequences"]) for block in blocks)
    total_days = sum(len(block["trade_dates"]) for block in blocks)  # type: ignore[arg-type]
    all_markers_found = bool(extraction["markers"]) and all(extraction["markers"].values())  # type: ignore[index]
    row_level_materialized = False
    matched_controls_materialized = False
    accepted_rows_added = 0
    strict_full_objective_achieved = False
    gate_result = (
        "r6_oystacher_govinfo_date_row_screen_v1="
        "official_date_contexts_materialized_exhibit_a_or_owner_export_still_required"
    )
    next_action = (
        "Acquire Oystacher Exhibit A or an owner-approved equivalent order-lifecycle export with "
        "timestamped spoof rows and matched normal controls; date-level court context is not enough "
        "for R6 split acceptance."
    )

    result = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "board_sha256_at_start": board_hash(),
        "source_url": SOURCE_URL,
        "download": {
            "http_status": download["http_status"],
            "content_type": download["content_type"],
            "final_url": download["final_url"],
            "pdf_bytes": download["pdf_bytes"],
            "pdf_sha256": download["pdf_sha256"],
            "raw_pdf_committed": False,
        },
        "extraction": {
            "returncode": extraction["returncode"],
            "text_bytes": extraction["text_bytes"],
            "text_sha256": extraction["text_sha256"],
            "markers": extraction["markers"],
            "all_markers_found": all_markers_found,
            "raw_text_committed": False,
        },
        "candidate_date_context_csv": str(date_csv),
        "market_blocks_csv": str(market_csv),
        "candidate_date_context_rows": len(rows),
        "market_block_count": len(blocks),
        "totals": {
            "trading_days": total_days,
            "spoof_orders": total_orders,
            "flip_sequences": total_flips,
            "date_context_positive_only_wilson95_lcb": round(wilson_lcb_all_success(total_days), 12),
        },
        "v59_debt_reference": {
            "json": str(DEBT_JSON),
            "loaded": bool(debt),
            "summary": v59_summary,
        },
        "materialization_assessment": {
            "date_contexts_materialized": True,
            "row_level_materialized": row_level_materialized,
            "matched_controls_materialized": matched_controls_materialized,
            "acceptance_reason": "date-level official context lacks Exhibit A timestamps/order legs and matched controls",
            "positive_supply_if_appendix_acquired": (
                "aggregate spoof orders and flip sequences exceed current debt, but only an appendix/export can "
                "turn that supply into accepted rows"
            ),
        },
        "gate_result": gate_result,
        "accepted_rows_added": accepted_rows_added,
        "new_confidence_gate": False,
        "strict_full_objective_achieved": strict_full_objective_achieved,
        "update_goal": False,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "shared_intake_mutated": False,
        "external_requests_sent": True,
        "trade_usable": False,
        "next_action": next_action,
    }

    json_path = OUT_DIR / "r6_oystacher_govinfo_date_row_screen_v1.json"
    json_path.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")

    report_path = OUT_DIR / "r6_oystacher_govinfo_date_row_screen_v1.md"
    report_path.write_text(
        "\n".join(
            [
                "# R6 Oystacher GovInfo Date-Row Screen v1",
                "",
                f"- Run id: `{RUN_ID}`.",
                f"- Official govinfo source fetched: `{download['http_status'] == 200}`; content type `{download['content_type']}`; PDF bytes `{download['pdf_bytes']}`.",
                f"- Extracted marker check all-pass: `{all_markers_found}`.",
                f"- Date-level candidate contexts: `{len(rows)}` across `{len(blocks)}` market blocks.",
                f"- Aggregates: spoof orders `{total_orders}`, flip sequences `{total_flips}`, trading days `{total_days}`.",
                "- Materialization status: `date_level_context_only_not_accepted`; no Exhibit A timestamp/order-leg appendix was exposed in this public govinfo PDF.",
                f"- Gate result: `{gate_result}`.",
                "- Accepted rows added: `0`; new confidence gate: `false`; strict full objective achieved: `false`; `update_goal=false`.",
                "- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; shared intake mutated: `false`; trade usable: `false`.",
                "",
                "## Artifacts",
                "",
                f"- JSON: `{json_path}`",
                f"- Report: `{report_path}`",
                f"- Date-context CSV: `{date_csv}`",
                f"- Market-block CSV: `{market_csv}`",
                f"- Command outputs: `{CMD_DIR}`",
                f"- Assertions: `{CHECK_DIR / 'r6_oystacher_govinfo_date_row_screen_v1_assertions.out'}`",
                "",
                "## Interpretation",
                "",
                "The official court document gives exact charged dates and market blocks for Oystacher/3Red, which is useful for an acquisition request. It still cannot be accepted as R6 split evidence because Board A needs timestamped order-lifecycle rows and matched controls, not date-level aggregate counts.",
                "",
                "## Next",
                "",
                next_action,
                "",
            ]
        ),
        encoding="utf-8",
    )

    assertions = {
        "govinfo_http_200": download["http_status"] == 200,
        "ghostscript_returncode_0": extraction["returncode"] == 0,
        "source_markers_all_found": all_markers_found,
        "candidate_date_context_rows_51": len(rows) == 51,
        "total_spoof_orders_5207": total_orders == 5207,
        "total_flip_sequences_1316": total_flips == 1316,
        "row_level_not_materialized": row_level_materialized is False,
        "matched_controls_not_materialized": matched_controls_materialized is False,
        "accepted_rows_zero": accepted_rows_added == 0,
        "strict_full_objective_false": strict_full_objective_achieved is False,
        "update_goal_false": result["update_goal"] is False,
    }
    assertion_path = CHECK_DIR / "r6_oystacher_govinfo_date_row_screen_v1_assertions.out"
    assertion_path.write_text(
        "\n".join(f"{name}={'PASS' if passed else 'FAIL'}" for name, passed in assertions.items()) + "\n",
        encoding="utf-8",
    )

    print(json.dumps({"gate_result": gate_result, "candidate_date_context_rows": len(rows), "update_goal": False}, sort_keys=True))
    return 0 if all(assertions.values()) else 1


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CMD_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="ict-r6-oystacher-govinfo-") as tmp_name:
        tmp = Path(tmp_name)
        download = download_source(tmp)
        extraction = extract_text(Path(download["pdf_path"]), tmp)
        return write_outputs(download, extraction)


if __name__ == "__main__":
    sys.exit(main())
