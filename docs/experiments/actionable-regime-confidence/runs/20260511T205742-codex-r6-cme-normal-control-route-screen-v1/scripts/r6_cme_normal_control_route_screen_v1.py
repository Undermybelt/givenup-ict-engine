#!/usr/bin/env python3
import csv
import hashlib
import json
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


REPO = Path(__file__).resolve().parents[6]
RUN_ID = "20260511T205742-codex-r6-cme-normal-control-route-screen-v1"
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs" / RUN_ID
OUT_DIR = RUN_ROOT / "r6-cme-normal-control-route-screen"
CHECK_DIR = RUN_ROOT / "checks"
BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"
INTAKE_ROOT = Path("/tmp/ict-engine-direct-manipulation-row-intake")
POSITIVE_ROWS = INTAKE_ROOT / "positive_spoofing_layering_rows.csv"
NEGATIVE_ROWS = INTAKE_ROOT / "matched_negative_normal_activity_rows.csv"
PROVENANCE = INTAKE_ROOT / "provenance_manifest.json"

PUBLIC_SOURCES = [
    {
        "id": "cme_datamine_landing",
        "owner": "CME Group",
        "url": "https://www.cmegroup.com/market-data/datamine-historical-data.html",
        "role": "Official historical-data acquisition route for CME futures market data.",
    },
    {
        "id": "cme_datamine_order_book",
        "owner": "CME Group",
        "url": "https://www.cmegroup.com/market-data/datamine-historical-data/datamine-order-book.html",
        "role": "Official CME DataMine order-book route candidate for matched normal activity controls.",
    },
    {
        "id": "cme_datamine_contact",
        "owner": "CME Group",
        "url": "https://www.cmegroup.com/market-data/datamine-historical-data/contact-us.html",
        "role": "Official inquiry route for acquiring permissioned historical CME market data exports.",
    },
]


def sha256_file(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def board_hash():
    return sha256_file(BOARD)


def download_source(source):
    request = urllib.request.Request(
        source["url"],
        headers={"User-Agent": "ict-engine-board-a-source-route-screen/1.0"},
    )
    out_path = OUT_DIR / f"{source['id']}.html"
    record = dict(source)
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            body = response.read()
            out_path.write_bytes(body)
            text = body[:500000].decode("utf-8", errors="ignore")
            record.update(
                {
                    "status": response.status,
                    "content_type": response.headers.get("content-type"),
                    "bytes": len(body),
                    "sha256": hashlib.sha256(body).hexdigest(),
                    "saved_path": str(out_path.relative_to(REPO)),
                    "mentions_market_depth": "market depth" in text.lower(),
                    "mentions_order_book": "order book" in text.lower(),
                    "mentions_historical": "historical" in text.lower(),
                    "mentions_contact": "contact" in text.lower(),
                }
            )
    except Exception as exc:
        record.update(
            {
                "status": None,
                "content_type": None,
                "bytes": 0,
                "sha256": "",
                "saved_path": "",
                "error": str(exc),
                "mentions_market_depth": False,
                "mentions_order_book": False,
                "mentions_historical": False,
                "mentions_contact": False,
            }
        )
    return record


def count_csv(path):
    if not path.exists():
        return 0, []
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
    return len(rows), reader.fieldnames or []


def write_csv(path, rows, fieldnames):
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)

    positive_count, positive_fields = count_csv(POSITIVE_ROWS)
    negative_count, negative_fields = count_csv(NEGATIVE_ROWS)
    provenance_present = PROVENANCE.exists()
    source_records = [download_source(source) for source in PUBLIC_SOURCES]

    route_rows = [
        {
            "route_id": "cme_datamine_nq_order_book_controls",
            "source_owner": "CME Group",
            "target_file": str(NEGATIVE_ROWS),
            "match_group_id": "cftc_mohan_20131202_nq_example",
            "required_symbol": "E-mini NASDAQ futures / NQ",
            "required_venue": "CME",
            "required_session": "overnight_central_time",
            "required_schema": ";".join(positive_fields),
            "accepted_now": "false",
            "reason": "The public CME route identifies a plausible source owner for matched normal controls, but no owner-approved row export has been acquired.",
        }
    ]

    draft = "\n".join(
        [
            "# No-Send Request Draft: R6 CME Normal Controls",
            "",
            "Purpose: acquire same-schema normal activity rows for Board A R6 direct Manipulation controls.",
            "",
            "Requested file: `/tmp/ict-engine-direct-manipulation-row-intake/matched_negative_normal_activity_rows.csv`.",
            "",
            "Positive group to match: `cftc_mohan_20131202_nq_example` from the public CFTC Krishna Mohan order.",
            "",
            "Required matching axes:",
            "- Source owner or owner-approved export: CME Group or other explicitly licensed CME historical order-book export.",
            "- Venue: CME.",
            "- Instrument family: E-mini NASDAQ / NQ futures.",
            "- Session bucket: overnight Central Time.",
            "- Normal activity: no spoofing/layering/manipulation finding for the control rows.",
            "- Same Board A intake schema as `positive_spoofing_layering_rows.csv`.",
            "",
            "Boundary: this draft was not sent. It does not grant permission, download private rows, or create accepted evidence.",
            "",
        ]
    )
    draft_path = OUT_DIR / "r6_cme_normal_control_request_draft_v1.md"
    draft_path.write_text(draft, encoding="utf-8")

    result = {
        "run_id": RUN_ID,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "board_hash_before": board_hash(),
        "decision": "r6_cme_normal_control_route_screen_v1=official_route_identified_controls_not_acquired",
        "positive_rows_present": POSITIVE_ROWS.exists(),
        "positive_rows_count": positive_count,
        "positive_fields": positive_fields,
        "provenance_present": provenance_present,
        "matched_negative_rows_present": NEGATIVE_ROWS.exists(),
        "matched_negative_rows_count": negative_count,
        "matched_negative_rows_fields": negative_fields,
        "source_records": source_records,
        "route_rows": route_rows,
        "request_draft": str(draft_path.relative_to(REPO)),
        "request_sent": False,
        "authenticated_account_used": False,
        "rows_acquired": False,
        "matched_controls_acquired": False,
        "intake_files_created": False,
        "accepted_rows_added": 0,
        "new_confidence_gate": False,
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "trade_usable": False,
        "next_action": "Acquire owner-approved CME/NQ normal activity control rows or another source-owned same-schema control export, then rerun the direct Manipulation intake verifier.",
    }

    json_path = OUT_DIR / "r6_cme_normal_control_route_screen_v1.json"
    report_path = OUT_DIR / "r6_cme_normal_control_route_screen_v1.md"
    route_csv = OUT_DIR / "r6_cme_normal_control_route_screen_v1_routes.csv"
    source_csv = OUT_DIR / "r6_cme_normal_control_route_screen_v1_sources.csv"
    assertions_path = CHECK_DIR / "r6_cme_normal_control_route_screen_v1_assertions.out"

    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_csv(
        route_csv,
        route_rows,
        [
            "route_id",
            "source_owner",
            "target_file",
            "match_group_id",
            "required_symbol",
            "required_venue",
            "required_session",
            "required_schema",
            "accepted_now",
            "reason",
        ],
    )
    write_csv(
        source_csv,
        source_records,
        [
            "id",
            "owner",
            "url",
            "role",
            "status",
            "content_type",
            "bytes",
            "sha256",
            "saved_path",
            "mentions_market_depth",
            "mentions_order_book",
            "mentions_historical",
            "mentions_contact",
            "error",
        ],
    )

    report_lines = [
        "# R6 CME Normal-Control Route Screen v1",
        "",
        f"Run ID: `{RUN_ID}`",
        "",
        f"- Gate result: `{result['decision']}`.",
        f"- Positive rows currently present in `/tmp`: `{positive_count}`.",
        f"- Provenance manifest present: `{str(provenance_present).lower()}`.",
        f"- Matched negative normal-control rows present: `{str(NEGATIVE_ROWS.exists()).lower()}`.",
        f"- Official/public route records checked: `{len(source_records)}`.",
        f"- Request sent: `false`; authenticated account used: `false`; rows acquired: `false`.",
        f"- Accepted rows added: `0`; new confidence gate: `false`; strict full objective achieved: `false`; `update_goal=false`.",
        "",
        "## Route Judgment",
        "",
        "CME Group is the direct source owner for the positive examples' venue/instrument family, so the official CME historical order-book route is a plausible acquisition path for matched NQ normal controls. It is not accepted evidence until an owner-approved export supplies same-schema normal rows.",
        "",
        "## Required Control File",
        "",
        f"- Target: `{NEGATIVE_ROWS}`.",
        "- Match group: `cftc_mohan_20131202_nq_example`.",
        "- Required axes: CME venue, E-mini NASDAQ/NQ futures family, overnight Central Time session, normal non-manipulation activity, same CSV schema.",
        "",
        "## Public Sources Checked",
        "",
    ]
    for record in source_records:
        report_lines.append(
            f"- `{record['id']}`: status `{record.get('status')}`, owner `{record['owner']}`, URL `{record['url']}`."
        )
    report_lines.extend(
        [
            "",
            "## Boundary",
            "",
            "This run identifies a source-owner route and writes a local no-send request draft only. It does not create `matched_negative_normal_activity_rows.csv`, does not use a CME account, and does not promote positive-only evidence.",
            "",
            "## Artifacts",
            "",
            f"- JSON: `{json_path.relative_to(REPO)}`",
            f"- Route CSV: `{route_csv.relative_to(REPO)}`",
            f"- Source CSV: `{source_csv.relative_to(REPO)}`",
            f"- No-send request draft: `{draft_path.relative_to(REPO)}`",
            f"- Assertions: `{assertions_path.relative_to(REPO)}`",
        ]
    )
    report_path.write_text("\n".join(report_lines) + "\n", encoding="utf-8")

    assertions = [
        f"PASS decision={result['decision']}",
        f"PASS positive_rows_count={positive_count}",
        f"PASS provenance_present={str(provenance_present).lower()}",
        f"PASS matched_negative_rows_present={str(NEGATIVE_ROWS.exists()).lower()}",
        "PASS request_sent=false",
        "PASS authenticated_account_used=false",
        "PASS rows_acquired=false",
        "PASS matched_controls_acquired=false",
        "PASS accepted_rows_added=0",
        "PASS new_confidence_gate=false",
        "PASS strict_full_objective_achieved=false",
        "PASS update_goal=false",
    ]
    assertions_path.write_text("\n".join(assertions) + "\n", encoding="utf-8")

    print(json.dumps({
        "decision": result["decision"],
        "positive_rows_count": positive_count,
        "matched_negative_rows_present": NEGATIVE_ROWS.exists(),
        "request_sent": False,
        "accepted_rows_added": 0,
        "update_goal": False,
        "report": str(report_path.relative_to(REPO)),
    }, indent=2))


if __name__ == "__main__":
    main()
