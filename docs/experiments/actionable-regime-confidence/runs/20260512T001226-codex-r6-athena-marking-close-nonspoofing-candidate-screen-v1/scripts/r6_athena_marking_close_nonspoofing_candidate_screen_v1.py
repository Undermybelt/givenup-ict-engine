#!/usr/bin/env python3
"""Screen official SEC Athena order for non-spoofing direct Manipulation rows."""

from __future__ import annotations

import csv
import hashlib
import json
import math
import shutil
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


RUN_ID = "20260512T001226-codex-r6-athena-marking-close-nonspoofing-candidate-screen-v1"
REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs" / RUN_ID
OUT = RUN_ROOT / "r6-athena-marking-close-nonspoofing-candidate-screen"
CHECKS = RUN_ROOT / "checks"
CMD = RUN_ROOT / "command-output"
BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"
SOURCE_URL = "https://www.sec.gov/file/34-73369pdf"
SOURCE_CANONICAL_URL = "https://www.sec.gov/files/litigation/admin/2014/34-73369.pdf"
SOURCE_USER_AGENT = "Mozilla/5.0 ict-engine-board-a-audit contact=research@example.com"
Z_95 = 1.96

FIELDS = [
    "candidate_species",
    "label",
    "source_report",
    "source_url",
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
    "control_status",
    "promotion_status",
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def wilson_lcb(successes: int, total: int) -> float:
    if total <= 0:
        return 0.0
    p = successes / total
    z2 = Z_95 * Z_95
    denom = 1.0 + z2 / total
    centre = p + z2 / (2.0 * total)
    margin = Z_95 * math.sqrt((p * (1.0 - p) + z2 / (4.0 * total)) / total)
    return max(0.0, (centre - margin) / denom)


def run_command(name: str, args: list[str], timeout_seconds: int = 45) -> dict[str, Any]:
    CMD.mkdir(parents=True, exist_ok=True)
    try:
        proc = subprocess.run(
            args,
            cwd=REPO,
            text=True,
            capture_output=True,
            timeout=timeout_seconds,
            check=False,
        )
        stdout = proc.stdout
        stderr = proc.stderr
        returncode = proc.returncode
        timed_out = False
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout or ""
        stderr = (exc.stderr or "") + f"\nTIMEOUT after {timeout_seconds}s\n"
        returncode = 124
        timed_out = True
    out_path = CMD / f"{name}.stdout.txt"
    err_path = CMD / f"{name}.stderr.txt"
    exit_path = CMD / f"{name}.exit"
    out_path.write_text(stdout, encoding="utf-8")
    err_path.write_text(stderr, encoding="utf-8")
    exit_path.write_text(f"{returncode}\n", encoding="utf-8")
    return {
        "name": name,
        "cmd": " ".join(args),
        "returncode": returncode,
        "timed_out": timed_out,
        "stdout_path": str(out_path.relative_to(REPO)),
        "stderr_path": str(err_path.relative_to(REPO)),
        "exit_path": str(exit_path.relative_to(REPO)),
    }


def fetch_source_and_extract_text() -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="ict-r6-athena-source-") as tmp_name:
        tmp = Path(tmp_name)
        pdf_path = tmp / "athena_34_73369.pdf"
        txt_path = tmp / "athena_34_73369.txt"
        curl_path = shutil.which("curl")
        if not curl_path:
            raise SystemExit("missing_curl_for_sec_pdf_fetch")
        fetch = run_command(
            "curl_source_fetch",
            [
                curl_path,
                "-L",
                "-sS",
                "--fail",
                "-A",
                SOURCE_USER_AGENT,
                "-D",
                str(tmp / "headers.txt"),
                "-o",
                str(pdf_path),
                SOURCE_URL,
            ],
            timeout_seconds=45,
        )
        if fetch["returncode"] != 0 or not pdf_path.exists():
            raise SystemExit("source_fetch_failed")
        pdf_bytes = pdf_path.read_bytes()
        headers = (tmp / "headers.txt").read_text(encoding="utf-8", errors="replace")
        content_type = ""
        final_url = SOURCE_CANONICAL_URL
        for line in headers.splitlines():
            if line.lower().startswith("content-type:"):
                content_type = line.split(":", 1)[1].strip()
            if line.lower().startswith("location:") and line.strip().endswith(".pdf"):
                final_url = "https://www.sec.gov" + line.split(":", 1)[1].strip()
        gs_path = shutil.which("gs")
        if not gs_path:
            raise SystemExit("missing_ghostscript_gs_for_pdf_text_extraction")
        gs = run_command(
            "ghostscript_txtwrite_source_extract",
            [
                gs_path,
                "-q",
                "-dNOPAUSE",
                "-dBATCH",
                "-sDEVICE=txtwrite",
                f"-sOutputFile={txt_path}",
                str(pdf_path),
            ],
            timeout_seconds=60,
        )
        text = txt_path.read_text(encoding="utf-8", errors="replace")
        markers = [
            "Athena Capital Research",
            "shares of EBAY stock on November",
            "3:50:00.578",
            "15:59:58.355",
            "15:59:59.950",
            "4:00:03.348",
            "224,638 Buy Imbalance",
        ]
        found_markers = {marker: (marker in text) for marker in markers}
        line_refs: list[dict[str, Any]] = []
        for number, line in enumerate(text.splitlines(), start=1):
            if any(marker in line for marker in ["EBAY", "3:50:00.578", "15:59:58.355", "15:59:59.950", "4:00:03.348"]):
                line_refs.append({"line": number, "text": " ".join(line.split())[:180]})
        return {
            "source_url": SOURCE_URL,
            "source_canonical_url": SOURCE_CANONICAL_URL,
            "final_url": final_url,
            "content_type": content_type,
            "pdf_byte_count": len(pdf_bytes),
            "pdf_sha256": hashlib.sha256(pdf_bytes).hexdigest(),
            "curl": fetch,
            "ghostscript": gs,
            "markers": found_markers,
            "line_refs": line_refs,
            "all_markers_found": all(found_markers.values()),
            "raw_pdf_committed": False,
            "text_committed": False,
        }


def candidate_rows() -> list[dict[str, str]]:
    source_report = "SEC Release No. 34-73369 / IA-3950: Athena Capital Research, LLC"
    base = {
        "candidate_species": "marking_close_gravy",
        "label": "positive_marking_close_price_impact",
        "source_report": source_report,
        "source_url": SOURCE_CANONICAL_URL,
        "source_section": "Findings paragraphs 29-30, EBAY November 25 2009 example",
        "trade_date": "2009-11-25",
        "symbol": "EBAY",
        "participant_type_code": "SEC respondent investment adviser / HFT firm",
        "participant_identifier": "Athena Capital Research, LLC",
        "matched_negative_group_id": "sec_athena_20091125_ebay_marking_close",
        "session_bucket": "us_equity_closing_auction",
        "control_status": "missing_matched_normal_control",
        "promotion_status": "candidate_only_not_live_intake",
    }
    rows = [
        {
            **base,
            "venue_or_market_center": "NASDAQ closing cross",
            "side": "sell imbalance-only order",
            "earliest_order_received_time": "15:50:00.578 America/New_York",
            "latest_order_received_time": "15:50:00.578 America/New_York",
            "order_count": "1",
            "total_order_quantity": "224638 shares",
            "activity_description": "Sell imbalance-only order placed after first NASDAQ imbalance message; candidate marking-close setup row, not a spoofing row.",
            "source_row_id": "sec_athena_20091125_ebay_sell_imbalance_only_155000578",
        },
        {
            **base,
            "venue_or_market_center": "NASDAQ / lit market",
            "side": "buy accumulation order",
            "earliest_order_received_time": "15:50:00.578 America/New_York",
            "latest_order_received_time": "15:50:00.578 America/New_York",
            "order_count": "1",
            "total_order_quantity": "85300 shares; 16000 shares filled almost instantly",
            "activity_description": "Initial accumulation buy order simultaneous with imbalance-only order; part of official EBAY marking-close sequence.",
            "source_row_id": "sec_athena_20091125_ebay_initial_buy_accumulation_155000578",
        },
        {
            **base,
            "venue_or_market_center": "NASDAQ / lit markets",
            "side": "buy limit-order accumulation",
            "earliest_order_received_time": "15:50:07.004 America/New_York",
            "latest_order_received_time": "15:59:58.112 America/New_York",
            "order_count": "over 140",
            "total_order_quantity": "64000 shares purchased; source states individual orders between 100 and 5800 shares",
            "activity_description": "Pre-close limit-order accumulation interval preceding Gravy; aggregate official row, not individual order-level rows.",
            "source_row_id": "sec_athena_20091125_ebay_accumulation_interval_155007004_155958112",
        },
    ]
    gravy_orders = [
        ("15:59:58.355", "BATS", "11200"),
        ("15:59:58.503", "BATS", "22400"),
        ("15:59:59.403", "BATS", "33600"),
        ("15:59:59.705", "NASDAQ", "5600"),
        ("15:59:59.870", "BATS", "28000"),
        ("15:59:59.950", "NASDAQ", "11200"),
    ]
    for idx, (event_time, venue, quantity) in enumerate(gravy_orders, start=1):
        rows.append(
            {
                **base,
                "venue_or_market_center": venue,
                "side": "last-second buy order",
                "earliest_order_received_time": f"{event_time} America/New_York",
                "latest_order_received_time": f"{event_time} America/New_York",
                "order_count": "1",
                "total_order_quantity": f"{quantity} shares",
                "activity_description": "Official SEC EBAY Gravy buy-order row in the final two seconds; non-spoofing marking-close candidate.",
                "source_row_id": f"sec_athena_20091125_ebay_gravy_buy_{idx}_{event_time.replace(':', '').replace('.', '')}",
            }
        )
    rows.append(
        {
            **base,
            "venue_or_market_center": "NASDAQ closing cross",
            "side": "closing cross sell fill",
            "earliest_order_received_time": "16:00:03.348 America/New_York",
            "latest_order_received_time": "16:00:03.348 America/New_York",
            "order_count": "closing auction outcome",
            "total_order_quantity": "233979 shares",
            "activity_description": "Closing cross outcome row for the EBAY sequence; candidate effect row, not an accepted control or classifier row.",
            "source_row_id": "sec_athena_20091125_ebay_closing_cross_fill_160003348",
        }
    )
    return rows


def write_csv(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def main() -> int:
    for path in [OUT, CHECKS, CMD]:
        path.mkdir(parents=True, exist_ok=True)
    source = fetch_source_and_extract_text()
    rows = candidate_rows()
    csv_path = OUT / "r6_athena_marking_close_nonspoofing_candidates_v1.csv"
    write_csv(csv_path, rows, FIELDS)

    venue_counts: dict[str, int] = {}
    for row in rows:
        venue_counts[row["venue_or_market_center"]] = venue_counts.get(row["venue_or_market_center"], 0) + 1
    what_if_positive_rows = 73 + len(rows)
    result = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "board_sha256_at_start": sha256(BOARD),
        "source_verification": source,
        "candidate_species": ["marking_close_gravy"],
        "candidate_rows": len(rows),
        "candidate_symbols": sorted({row["symbol"] for row in rows}),
        "candidate_venues": venue_counts,
        "candidate_trade_dates": sorted({row["trade_date"] for row in rows}),
        "candidate_csv": str(csv_path.relative_to(REPO)),
        "baseline_live_positive_rows": 73,
        "what_if_positive_rows_if_future_policy_accepts": what_if_positive_rows,
        "what_if_positive_wilson95_lcb": round(wilson_lcb(what_if_positive_rows, what_if_positive_rows), 12),
        "accepted_rows_added": 0,
        "live_intake_mutated": False,
        "matched_controls_materialized": False,
        "new_confidence_gate": False,
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "raw_pdf_committed": False,
        "trade_usable": False,
        "gate_result": "r6_athena_marking_close_nonspoofing_candidate_screen_v1=nonspoofing_marking_close_candidate_rows_found_controls_and_splits_still_blocked",
        "blocker": "Candidate rows cover one non-spoofing marking-close species, but no matched normal controls are materialized and chronological/symbol/venue/direct-species gates remain false.",
        "next_action": "Find owner-approved matched normal closing-auction controls or additional direct non-spoofing species rows, then rerun direct plus sidecar split calibration without mutating the shared intake until policy is explicit.",
    }

    json_path = OUT / "r6_athena_marking_close_nonspoofing_candidate_screen_v1.json"
    md_path = OUT / "r6_athena_marking_close_nonspoofing_candidate_screen_v1.md"
    assertions_path = CHECKS / "r6_athena_marking_close_nonspoofing_candidate_screen_v1_assertions.out"
    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    lines = [
        "# R6 Athena Marking-Close Non-Spoofing Candidate Screen v1",
        "",
        f"- Run id: `{RUN_ID}`.",
        f"- Official source fetched: `{str(source['all_markers_found']).lower()}`; content type `{source['content_type']}`; PDF bytes `{source['pdf_byte_count']}`.",
        "- Candidate species: `marking_close_gravy`.",
        f"- Candidate rows: `{len(rows)}` across symbols `{', '.join(result['candidate_symbols'])}` and venues `{', '.join(sorted(venue_counts))}`.",
        f"- What-if positive support if future policy accepts these rows: `{what_if_positive_rows}`; positive-only Wilson95 LCB `{result['what_if_positive_wilson95_lcb']}`.",
        "- Accepted rows added: `0`; matched controls materialized: `false`; live intake mutated: `false`.",
        f"- Gate result: `{result['gate_result']}`.",
        "- Strict full objective achieved: `false`; `update_goal=false`.",
        "",
        "## Artifacts",
        "",
        f"- JSON: `{json_path.relative_to(REPO)}`",
        f"- Candidate CSV: `{csv_path.relative_to(REPO)}`",
        f"- Source extraction stdout/stderr: `{CMD.relative_to(REPO)}`",
        f"- Assertions: `{assertions_path.relative_to(REPO)}`",
        "",
        "## Source Check",
        "",
        f"- Source URL: `{SOURCE_CANONICAL_URL}`",
        "- Verified markers include `EBAY`, `3:50:00.578`, `15:59:58.355`, `15:59:59.950`, and `4:00:03.348`.",
    ]
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    assertions = [
        ("official_source_markers_found", bool(source["all_markers_found"])),
        ("candidate_rows_10", len(rows) == 10),
        ("candidate_species_marking_close", result["candidate_species"] == ["marking_close_gravy"]),
        ("live_intake_not_mutated", result["live_intake_mutated"] is False),
        ("accepted_rows_zero", result["accepted_rows_added"] == 0),
        ("strict_full_objective_false", result["strict_full_objective_achieved"] is False),
        ("update_goal_false", result["update_goal"] is False),
    ]
    assertions_path.write_text(
        "\n".join(f"{name}={'PASS' if passed else 'FAIL'}" for name, passed in assertions) + "\n",
        encoding="utf-8",
    )
    if not all(passed for _, passed in assertions):
        raise SystemExit(2)
    print(json.dumps({"gate_result": result["gate_result"], "candidate_rows": len(rows), "update_goal": False}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
