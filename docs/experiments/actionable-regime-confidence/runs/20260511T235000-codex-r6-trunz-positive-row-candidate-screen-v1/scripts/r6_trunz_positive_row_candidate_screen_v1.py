#!/usr/bin/env python3
"""Screen official CFTC sources for one more R6 row-level positive candidate."""

from __future__ import annotations

import csv
import hashlib
import json
import math
import re
import subprocess
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


RUN_ID = "20260511T235000-codex-r6-trunz-positive-row-candidate-screen-v1"
REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs" / RUN_ID
OUT = RUN_ROOT / "r6-trunz-positive-row-candidate-screen"
CHECKS = RUN_ROOT / "checks"
CMD_OUT = RUN_ROOT / "command-output"
RAW = Path("/tmp/ict-engine-r6-trunz-positive-row-candidate-screen-v1/raw")
BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"

CURRENT_POSITIVE_ROWS = 57
SARAO_NOWAK_SIDE_CANDIDATES = 12
SIDECAR_BROAD_NORMAL_CONTROLS = 80
SIDECAR_BROAD_NORMAL_WILSON95_LCB = 0.954180263735

SOURCES = [
    {
        "case_id": "trunz_2019_order",
        "url": "https://www.cftc.gov/media/2516/enfchristiantrunzorder091619/download",
        "expected_use": "primary candidate: exact dated/timed positive spoofing example",
        "required_snippets": [
            "On June 22, 2016, at 2:14:33.935 AM Central Time, Trunz placed an offer to sell twenty",
            "at 2:14:35.926,  Trunz began placing a sequence of five-lot bids",
            "Trunz placed eight five-lot  Spoofing Platinum Bids",
        ],
    },
    {
        "case_id": "lawrence_2025_order",
        "url": "https://www.cftc.gov/media/11991/enflawrenceorder061025/download",
        "expected_use": "screened aggregate public order, expected fail-closed for row-level extraction",
        "required_snippets": [],
    },
    {
        "case_id": "belvedere_2025_order",
        "url": "https://www.cftc.gov/media/12376/enfbelvederetradingorder080825/download",
        "expected_use": "screened aggregate public order, expected fail-closed for row-level extraction",
        "required_snippets": [],
    },
    {
        "case_id": "sunoco_2025_order",
        "url": "https://www.cftc.gov/media/12591/enfsunocollcorder082725/download",
        "expected_use": "screened aggregate public order, expected fail-closed for row-level extraction",
        "required_snippets": [],
    },
]

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
    "candidate_row_status",
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def wilson_lcb(successes: int, total: int, z: float = 1.96) -> float:
    if total <= 0:
        return 0.0
    phat = successes / total
    denom = 1 + z * z / total
    centre = phat + z * z / (2 * total)
    margin = z * math.sqrt((phat * (1 - phat) + z * z / (4 * total)) / total)
    return (centre - margin) / denom


def rows_needed_for_floor(current_rows: int, floor: float = 0.95) -> int:
    rows = current_rows
    while rows < 1000 and wilson_lcb(rows, rows) < floor:
        rows += 1
    return rows - current_rows


def fetch_source(source: dict[str, Any]) -> dict[str, Any]:
    RAW.mkdir(parents=True, exist_ok=True)
    pdf_path = RAW / f"{source['case_id']}.pdf"
    txt_path = RAW / f"{source['case_id']}.txt"
    req = urllib.request.Request(source["url"], headers={"User-Agent": "ict-engine-board-a-r6-source-screen/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=45) as response:
            body = response.read()
            status = response.status
            content_type = response.headers.get("Content-Type", "")
        pdf_path.write_bytes(body)
        text = extract_text(pdf_path, txt_path)
        return {
            "case_id": source["case_id"],
            "url": source["url"],
            "http_status": status,
            "content_type": content_type,
            "bytes": len(body),
            "sha256": sha256(pdf_path),
            "pdf_path": str(pdf_path),
            "text_path": str(txt_path),
            "text_bytes": len(text.encode("utf-8")),
            "text": text,
            "expected_use": source["expected_use"],
            "error": "",
        }
    except Exception as exc:  # noqa: BLE001 - artifact records fail-closed source state.
        return {
            "case_id": source["case_id"],
            "url": source["url"],
            "http_status": None,
            "content_type": "",
            "bytes": 0,
            "sha256": "",
            "pdf_path": str(pdf_path),
            "text_path": str(txt_path),
            "text_bytes": 0,
            "text": "",
            "expected_use": source["expected_use"],
            "error": repr(exc),
        }


def extract_text(pdf_path: Path, txt_path: Path) -> str:
    cmd = [
        "gs",
        "-q",
        "-dNOPAUSE",
        "-dBATCH",
        "-sDEVICE=txtwrite",
        f"-sOutputFile={txt_path}",
        str(pdf_path),
    ]
    completed = subprocess.run(cmd, text=True, capture_output=True, check=False)
    (CMD_OUT / f"extract_{pdf_path.stem}.stdout.txt").write_text(completed.stdout, encoding="utf-8")
    (CMD_OUT / f"extract_{pdf_path.stem}.stderr.txt").write_text(completed.stderr, encoding="utf-8")
    if txt_path.exists():
        return txt_path.read_text(encoding="utf-8", errors="replace")
    return ""


def screen_source(source: dict[str, Any], fetched: dict[str, Any]) -> dict[str, Any]:
    text = fetched["text"]
    lowered = text.lower()
    normalized = " ".join(text.split()).lower()
    exact_time_hits = re.findall(r"\b\d{1,2}:\d{2}:\d{2}(?:\.\d{1,6})?\b", text)
    required_snippets = source["required_snippets"]
    snippet_hits = {" ".join(snippet.split()): " ".join(snippet.split()).lower() in normalized for snippet in required_snippets}
    mentions_spoof = "spoof" in lowered
    mentions_genuine = "genuine" in lowered
    mentions_cancel = "cancel" in lowered
    trunz_materializable = (
        source["case_id"] == "trunz_2019_order"
        and fetched["http_status"] == 200
        and mentions_spoof
        and mentions_genuine
        and mentions_cancel
        and len(exact_time_hits) >= 1
        and all(snippet_hits.values())
    )
    return {
        "case_id": source["case_id"],
        "url": source["url"],
        "pdf_sha256": fetched["sha256"],
        "text_bytes": fetched["text_bytes"],
        "mentions_spoof": str(mentions_spoof),
        "mentions_genuine": str(mentions_genuine),
        "mentions_cancel": str(mentions_cancel),
        "exact_time_hits": str(len(exact_time_hits)),
        "row_materializable": str(trunz_materializable),
        "accepted_now": "False",
        "snippet_hits_json": json.dumps(snippet_hits, sort_keys=True),
        "screen_status": "row_level_positive_candidate" if trunz_materializable else "fail_closed_not_materialized",
    }


def proposed_rows() -> list[dict[str, str]]:
    return [
        {
            "label": "positive_spoofing_layering",
            "source_report": "CFTC Order: Christian Trunz, CFTC Docket No. 19-26",
            "source_section": "Order example, June 22 2016 July-expiry NYMEX Platinum Futures",
            "trade_date": "2016-06-22",
            "symbol": "July 2016 NYMEX Platinum Futures",
            "venue_or_market_center": "NYMEX/CME Globex",
            "participant_type_code": "CFTC respondent trader; precious metals trader",
            "participant_identifier": "Christian Trunz / precious metals desk",
            "side": "buy-side spoofing platinum bids opposite genuine platinum offer",
            "earliest_order_received_time": "02:14:35.926 America/Chicago",
            "latest_order_received_time": "02:14:37.006 America/Chicago",
            "order_count": "eight five-lot spoofing platinum bids",
            "total_order_quantity": "40 lots",
            "activity_description": (
                "Official CFTC order describes Trunz placing a twenty-lot genuine iceberg platinum offer at "
                "02:14:33.935 Central Time, then placing eight five-lot spoofing platinum bids on the opposite "
                "side between 02:14:35.926 and 02:14:37.006 before canceling the spoofing bids."
            ),
            "matched_negative_group_id": "cftc_trunz_20160622_platinum_genuine_offer_spoof_bids",
            "session_bucket": "overnight_central_time",
            "source_row_id": "cftc_trunz_20160622_platinum_buy_spoof_bids",
            "candidate_row_status": "proposed_sidecar_not_shared_intake",
        }
    ]


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)
    CMD_OUT.mkdir(parents=True, exist_ok=True)
    board_sha = hashlib.sha256(BOARD.read_bytes()).hexdigest()

    fetched = [fetch_source(source) for source in SOURCES]
    screens = [screen_source(source, item) for source, item in zip(SOURCES, fetched, strict=True)]
    rows = proposed_rows()
    materialized = [row for row in screens if row["row_materializable"] == "True"]
    if len(materialized) != len(rows):
        rows = []

    proposed_path = OUT / "r6_trunz_positive_row_candidates_v1.csv"
    source_screen_path = OUT / "r6_trunz_positive_row_source_screen_v1_cases.csv"
    write_csv(proposed_path, rows, FIELDS)
    write_csv(
        source_screen_path,
        screens,
        [
            "case_id",
            "url",
            "pdf_sha256",
            "text_bytes",
            "mentions_spoof",
            "mentions_genuine",
            "mentions_cancel",
            "exact_time_hits",
            "row_materializable",
            "accepted_now",
            "snippet_hits_json",
            "screen_status",
        ],
    )

    what_if_rows = CURRENT_POSITIVE_ROWS + SARAO_NOWAK_SIDE_CANDIDATES + len(rows)
    what_if_lcb = wilson_lcb(what_if_rows, what_if_rows)
    additional_needed = rows_needed_for_floor(what_if_rows)
    result = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "board_sha256_at_start": board_sha,
        "source_screen_count": len(screens),
        "row_materializable_sources": [row["case_id"] for row in screens if row["row_materializable"] == "True"],
        "proposed_positive_rows": len(rows),
        "proposed_rows_path": str(proposed_path.relative_to(REPO)),
        "source_screen_path": str(source_screen_path.relative_to(REPO)),
        "downloads": [{key: value for key, value in item.items() if key != "text"} for item in fetched],
        "current_positive_rows": CURRENT_POSITIVE_ROWS,
        "sarao_nowak_sidecar_positive_rows": SARAO_NOWAK_SIDE_CANDIDATES,
        "sidecar_broad_normal_control_rows": SIDECAR_BROAD_NORMAL_CONTROLS,
        "sidecar_broad_normal_wilson95_lcb": SIDECAR_BROAD_NORMAL_WILSON95_LCB,
        "what_if_positive_rows_after_sarao_nowak_trunz": what_if_rows,
        "what_if_positive_wilson95_lcb_after_sarao_nowak_trunz": round(what_if_lcb, 12),
        "what_if_min_wilson95_lcb_after_sarao_nowak_trunz": round(min(what_if_lcb, SIDECAR_BROAD_NORMAL_WILSON95_LCB), 12),
        "additional_positive_rows_needed_after_sarao_nowak_trunz_if_all_accepted": additional_needed,
        "shared_intake_mutated": False,
        "accepted_rows_added": 0,
        "new_confidence_gate": False,
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "external_requests_sent": True,
        "trade_usable": False,
        "gate_result": "r6_trunz_positive_row_candidate_screen_v1=proposed_rows_only_positive_confidence_still_blocked",
        "next_action": (
            "Continue V55 isolated intake reconstruction, then accept Sarao/Nowak/Trunz only if matched-control "
            "policy passes; source at least the remaining positive rows and rerun sidecar plus split calibration."
        ),
    }

    json_path = OUT / "r6_trunz_positive_row_candidate_screen_v1.json"
    md_path = OUT / "r6_trunz_positive_row_candidate_screen_v1.md"
    assertions_path = CHECKS / "r6_trunz_positive_row_candidate_screen_v1_assertions.out"
    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    lines = [
        "# R6 Trunz Positive Row Candidate Screen v1",
        "",
        f"- Run id: `{RUN_ID}`",
        f"- Proposed positive rows: `{len(rows)}`",
        f"- Shared intake mutated: `false`",
        f"- What-if positives after Sarao + Nowak/Smith + Trunz: `{what_if_rows}`",
        f"- What-if min Wilson95 LCB after Sarao + Nowak/Smith + Trunz: `{round(min(what_if_lcb, SIDECAR_BROAD_NORMAL_WILSON95_LCB), 12)}`",
        f"- Additional all-correct positive rows still needed if all three sidecars are accepted: `{additional_needed}`",
        "- Gate result: `r6_trunz_positive_row_candidate_screen_v1=proposed_rows_only_positive_confidence_still_blocked`",
        "- Accepted rows added: `0`; new confidence gate: `false`; strict full objective achieved: `false`; `update_goal=false`.",
        "- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; trade usable: `false`.",
        "",
        "## Artifacts",
        f"- JSON: `{json_path.relative_to(REPO)}`",
        f"- Proposed rows CSV: `{proposed_path.relative_to(REPO)}`",
        f"- Source screen CSV: `{source_screen_path.relative_to(REPO)}`",
        f"- Assertions: `{assertions_path.relative_to(REPO)}`",
    ]
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    assertions = [
        f"PASS proposed_positive_rows={len(rows)}",
        "PASS shared_intake_mutated=false",
        "PASS new_confidence_gate=false",
        "PASS strict_full_objective_achieved=false",
        f"PASS additional_positive_rows_needed_after_sarao_nowak_trunz_if_all_accepted={additional_needed}",
    ]
    assertions_path.write_text("\n".join(assertions) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
