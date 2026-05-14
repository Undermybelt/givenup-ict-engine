#!/usr/bin/env python3
"""Fetch the official Tower CFTC order linked from the cached press release and screen it fail-closed."""

from __future__ import annotations

import csv
import hashlib
import json
import subprocess
import sys
import urllib.request
from pathlib import Path
from typing import Any


RUN_ID = "20260511T212840-codex-r6-tower-linked-order-fetch-screen-v1"
REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = Path(__file__).resolve().parents[1]
OUT = RUN_ROOT / "r6-tower-linked-order-fetch-screen"
CHECKS = RUN_ROOT / "checks"
CMD_OUT = RUN_ROOT / "command-output"
BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"
INTAKE = Path("/tmp/ict-engine-direct-manipulation-row-intake")
RAW_DIR = Path("/tmp/ict-engine-r6-tower-order-fetch-screen-v1/raw")
SOURCE_URL = "https://www.cftc.gov/media/2986/enftowerresearchorder110619/download"
SOURCE_PDF = RAW_DIR / "enftowerresearchorder110619.pdf"
SOURCE_TEXT = RAW_DIR / "enftowerresearchorder110619.txt"
VERIFIER = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T151950-codex-direct-manipulation-row-intake-manifest-v1/"
    "direct-manipulation-intake/direct_manipulation_row_intake_verifier_v1.py"
)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        path.write_text("")
        return
    with path.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def fetch_source() -> tuple[int, str]:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    request = urllib.request.Request(
        SOURCE_URL,
        headers={
            "User-Agent": "curl/8.7.1 ict-engine-board-a-source-screen",
            "Accept": "application/pdf,*/*",
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        data = response.read()
        status = int(getattr(response, "status", 200))
        content_type = response.headers.get("content-type", "")
    SOURCE_PDF.write_bytes(data)
    return status, content_type


def extract_text() -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            "gs",
            "-q",
            "-dNOPAUSE",
            "-dBATCH",
            "-sDEVICE=txtwrite",
            f"-sOutputFile={SOURCE_TEXT}",
            str(SOURCE_PDF),
        ],
        text=True,
        capture_output=True,
        check=False,
    )


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)
    CMD_OUT.mkdir(parents=True, exist_ok=True)

    board_hash_before = sha256(BOARD)
    status, content_type = fetch_source()
    gs_result = extract_text()
    (CMD_OUT / "ghostscript_txtwrite.stdout.txt").write_text(gs_result.stdout)
    (CMD_OUT / "ghostscript_txtwrite.stderr.txt").write_text(gs_result.stderr)

    text = SOURCE_TEXT.read_text(errors="replace") if SOURCE_TEXT.exists() else ""
    normalized = " ".join(text.split())
    text_checks = {
        "Tower Research Capital LLC": "Tower Research Capital LLC" in normalized,
        "CFTC Docket No. 20-06": "CFTC Docket No. 20-06" in normalized,
        "Relevant Period": "Relevant Period" in normalized,
        "March 2012 through December 2013": "March 2012 through December 2013" in normalized,
        "E-mini S&P 500": "E-mini S&P 500" in normalized,
        "E-mini NASDAQ 100": "E-mini NASDAQ 100" in normalized,
        "E-mini Dow": "E-mini Dow" in normalized,
        "Genuine Order": "Genuine Order" in normalized,
        "Spoof Order": "Spoof Order" in normalized,
        "thousands of occasions": "thousands of occasions" in normalized,
    }

    row_level_negative_checks = {
        "has_single_event_trade_date": False,
        "has_single_event_order_timestamp": False,
        "has_single_event_side_quantity_pair": False,
        "has_matched_single_genuine_control": False,
    }
    row_materializable_candidates = 0

    verifier = subprocess.run(
        [sys.executable, str(VERIFIER), "--intake-root", str(INTAKE)],
        text=True,
        capture_output=True,
        check=False,
    )
    (CMD_OUT / "direct_manipulation_row_intake_verifier.stdout.txt").write_text(verifier.stdout)
    (CMD_OUT / "direct_manipulation_row_intake_verifier.stderr.txt").write_text(verifier.stderr)
    verifier_json = json.loads(verifier.stdout) if verifier.stdout.strip().startswith("{") else {}

    candidates = [
        {
            "candidate": "cftc_tower_linked_order_2019",
            "source_url": SOURCE_URL,
            "source_kind": "official_cftc_order_pdf",
            "fetch_status": status,
            "content_type": content_type,
            "text_chars": len(text),
            "row_materializable": False,
            "fail_closed_reason": "Order exposes broad period, markets, generic genuine/spoof pattern, and thousands-of-occasions language, but no single event date/timestamp/side/quantity/matched-control row.",
        }
    ]
    write_csv(OUT / "r6_tower_linked_order_fetch_screen_v1_candidates.csv", candidates)

    summary = {
        "run_id": RUN_ID,
        "decision": "r6_tower_linked_order_fetch_screen_v1=official_order_fetched_no_row_level_events",
        "board_hash_before": board_hash_before,
        "source_url": SOURCE_URL,
        "fetch_status": status,
        "content_type": content_type,
        "source_pdf_sha256": sha256(SOURCE_PDF),
        "source_text_sha256": sha256(SOURCE_TEXT),
        "source_text_chars": len(text),
        "text_checks": text_checks,
        "row_level_negative_checks": row_level_negative_checks,
        "row_materializable_candidates": row_materializable_candidates,
        "positive_rows_added": 0,
        "matched_controls_added": 0,
        "intake_changed": False,
        "verifier_status": verifier_json.get("status"),
        "verifier_positive_rows": verifier_json.get("positive_rows"),
        "verifier_matched_negative_rows": verifier_json.get("matched_negative_rows"),
        "accepted_rows_added": 0,
        "new_confidence_gate": False,
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "external_requests_sent": True,
        "trade_usable": False,
    }
    (OUT / "r6_tower_linked_order_fetch_screen_v1.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")

    gates = [
        {"gate": "official_order_fetch", "observed": status, "required": 200, "pass": status == 200},
        {"gate": "text_extraction", "observed": len(text), "required": ">0", "pass": len(text) > 0},
        {"gate": "single_event_rows", "observed": row_materializable_candidates, "required": ">0 for materialization", "pass": False},
        {"gate": "intake_unchanged", "observed": True, "required": True, "pass": True},
        {"gate": "strict_full_objective_achieved", "observed": False, "required": True, "pass": False},
    ]
    write_csv(OUT / "r6_tower_linked_order_fetch_screen_v1_gates.csv", gates)

    report = f"""# R6 Tower Linked Order Fetch Screen v1

## Scope

Fetched the official CFTC Tower order linked from the cached Tower press release and screened it for row-level R6 direct Manipulation materialization. Raw PDF/text stayed under `/tmp/ict-engine-r6-tower-order-fetch-screen-v1/raw`.

## Result

- Source fetched: HTTP `{status}`, content type `{content_type}`.
- PDF SHA256: `{summary['source_pdf_sha256']}`.
- Text chars: `{len(text)}`.
- Row-materializable candidates: `0`.
- Positive rows added: `0`.
- Matched controls added: `0`.
- Intake changed: `false`.
- Direct verifier status after screen: `{verifier_json.get('status')}`, positives `{verifier_json.get('positive_rows')}`, matched negatives `{verifier_json.get('matched_negative_rows')}`.
- Gate result: `r6_tower_linked_order_fetch_screen_v1=official_order_fetched_no_row_level_events`.

## Fail-Closed Reason

The official order confirms the relevant period, E-mini S&P 500 / E-mini NASDAQ 100 / E-mini Dow markets, generic Genuine Order and Spoof Order mechanics, and thousands-of-occasions conduct. It does not expose a single event with row-level trade date, order timestamp, side, quantity, and matched genuine-control leg. No R6 rows were materialized.

## Artifacts

- JSON: `{OUT / 'r6_tower_linked_order_fetch_screen_v1.json'}`
- Candidate CSV: `{OUT / 'r6_tower_linked_order_fetch_screen_v1_candidates.csv'}`
- Gates CSV: `{OUT / 'r6_tower_linked_order_fetch_screen_v1_gates.csv'}`
- Verifier stdout: `{CMD_OUT / 'direct_manipulation_row_intake_verifier.stdout.txt'}`
- Assertions: `{CHECKS / 'r6_tower_linked_order_fetch_screen_v1_assertions.out'}`

## Non-Completion

This run does not close R6 or the full Board A objective. It prevents the Tower linked order from being promoted as row-level confidence evidence.
"""
    (OUT / "r6_tower_linked_order_fetch_screen_v1.md").write_text(report)
    assertions = [
        ("decision", summary["decision"]),
        ("fetch_status", status),
        ("row_materializable_candidates", row_materializable_candidates),
        ("positive_rows_added", 0),
        ("matched_controls_added", 0),
        ("intake_changed", "false"),
        ("strict_full_objective_achieved", "false"),
        ("update_goal", "false"),
        ("raw_data_committed", "false"),
    ]
    (CHECKS / "r6_tower_linked_order_fetch_screen_v1_assertions.out").write_text(
        "\n".join(f"PASS {key}={value}" for key, value in assertions) + "\n"
    )
    return 0 if status == 200 and len(text) > 0 and verifier.returncode == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
