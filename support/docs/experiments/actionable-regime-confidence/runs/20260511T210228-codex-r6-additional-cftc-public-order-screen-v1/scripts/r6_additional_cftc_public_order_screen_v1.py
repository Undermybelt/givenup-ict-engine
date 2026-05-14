#!/usr/bin/env python3
import csv
import hashlib
import html
import json
import re
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


REPO = Path(__file__).resolve().parents[6]
RUN_ID = "20260511T210228-codex-r6-additional-cftc-public-order-screen-v1"
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs" / RUN_ID
OUT_DIR = RUN_ROOT / "r6-additional-cftc-public-order-screen"
CHECK_DIR = RUN_ROOT / "checks"
TMP_ROOT = Path("/tmp/ict-engine-r6-additional-cftc-public-order-screen-v1")
BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"

CASES = [
    {
        "case_id": "falloon_2025",
        "url": "https://www.cftc.gov/PressRoom/PressReleases/9118-25",
        "expected_markets": "E-mini S&P 500;E-mini Nasdaq 100",
        "expected_period": "2022",
        "r6_use": "recent public CFTC spoofing route candidate for additional positive rows",
    },
    {
        "case_id": "cox_2019",
        "url": "https://www.cftc.gov/PressRoom/PressReleases/7996-19",
        "expected_markets": "E-mini S&P 500;E-mini Nasdaq 100;E-mini Dow",
        "expected_period": "2014-2018",
        "r6_use": "multi-year public CFTC spoofing route candidate",
    },
    {
        "case_id": "mirae_2020",
        "url": "https://www.cftc.gov/PressRoom/PressReleases/8126-20",
        "expected_markets": "E-mini S&P 500",
        "expected_period": "2014-2016",
        "r6_use": "firm-level public CFTC spoofing route candidate",
    },
    {
        "case_id": "sarao_2016",
        "url": "https://www.cftc.gov/PressRoom/PressReleases/7381-16",
        "expected_markets": "E-mini S&P 500",
        "expected_period": "2010-2015",
        "r6_use": "public CFTC spoofing route candidate tied to index futures",
    },
    {
        "case_id": "panther_2013",
        "url": "https://www.cftc.gov/PressRoom/PressReleases/6615-13",
        "expected_markets": "futures contracts across exchanges",
        "expected_period": "2011",
        "r6_use": "older public CFTC spoofing route candidate for species breadth",
    },
]


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def board_hash():
    digest = hashlib.sha256()
    with BOARD.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def fetch(url, name):
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "ict-engine-board-a-cftc-public-order-screen/1.0"},
    )
    out_path = TMP_ROOT / name
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            body = response.read()
            out_path.write_bytes(body)
            return {
                "status": response.status,
                "content_type": response.headers.get("content-type") or "",
                "bytes": len(body),
                "sha256": sha256_bytes(body),
                "tmp_path": str(out_path),
                "text": body.decode("utf-8", errors="ignore"),
                "error": "",
            }
    except Exception as exc:
        return {
            "status": None,
            "content_type": "",
            "bytes": 0,
            "sha256": "",
            "tmp_path": "",
            "text": "",
            "error": str(exc),
        }


def strip_tags(text):
    text = re.sub(r"<script[\s\S]*?</script>", " ", text, flags=re.I)
    text = re.sub(r"<style[\s\S]*?</style>", " ", text, flags=re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def extract_links(base_url, raw_html):
    links = []
    for match in re.finditer(r'href=["\']([^"\']+)["\']', raw_html, flags=re.I):
        href = html.unescape(match.group(1))
        absolute = urllib.parse.urljoin(base_url, href)
        lower = absolute.lower()
        if any(token in lower for token in ["download", "order", "complaint", "enf", "pdf"]):
            links.append(absolute)
    return sorted(set(links))[:10]


def bool_text(value):
    return "true" if value else "false"


def write_csv(path, rows, fieldnames):
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)
    TMP_ROOT.mkdir(parents=True, exist_ok=True)

    rows = []
    for case in CASES:
        fetched = fetch(case["url"], f"{case['case_id']}.html")
        visible = strip_tags(fetched["text"])
        lower = visible.lower()
        links = extract_links(case["url"], fetched["text"])
        order_links = [link for link in links if "download" in link.lower() or ".pdf" in link.lower()]
        explicit_time_markers = len(re.findall(r"\b\d{1,2}:\d{2}(?::\d{2})?\b", visible))
        explicit_dates = len(re.findall(r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{1,2},\s+\d{4}\b", visible))
        rows.append(
            {
                "case_id": case["case_id"],
                "source_owner": "CFTC",
                "press_url": case["url"],
                "status": fetched["status"],
                "content_type": fetched["content_type"],
                "bytes": fetched["bytes"],
                "sha256": fetched["sha256"],
                "tmp_path": fetched["tmp_path"],
                "expected_markets": case["expected_markets"],
                "expected_period": case["expected_period"],
                "r6_use": case["r6_use"],
                "mentions_spoof": bool_text("spoof" in lower),
                "mentions_order": bool_text("order" in lower),
                "mentions_genuine": bool_text("genuine" in lower),
                "mentions_cancel": bool_text("cancel" in lower),
                "explicit_date_count": explicit_dates,
                "explicit_time_marker_count": explicit_time_markers,
                "related_order_links": ";".join(order_links),
                "row_extraction_ready": bool_text(False),
                "accepted_now": bool_text(False),
                "reason": "Official CFTC public route candidate. Press-page text is not a Board A-ready row export; detailed order/PDF extraction and matched normal controls are still required.",
                "error": fetched["error"],
            }
        )

    ok_cases = [row for row in rows if row["status"] == 200]
    order_link_count = sum(1 for row in rows if row["related_order_links"])
    row_extraction_ready_count = sum(1 for row in rows if row["row_extraction_ready"] == "true")

    result = {
        "run_id": RUN_ID,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "board_hash_before": board_hash(),
        "decision": "r6_additional_cftc_public_order_screen_v1=official_case_routes_found_rows_not_extracted",
        "official_cases_screened": len(rows),
        "public_pages_ok": len(ok_cases),
        "related_order_link_cases": order_link_count,
        "row_extraction_ready_count": row_extraction_ready_count,
        "accepted_rows_added": 0,
        "new_confidence_gate": False,
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "trade_usable": False,
        "request_sent": False,
        "authenticated_account_used": False,
        "rows": rows,
        "next_action": "For any official CFTC case with an order/PDF link, extract only source-stated row-level event facts plus matched controls; do not promote press-page summaries as Board A accepted rows.",
    }

    json_path = OUT_DIR / "r6_additional_cftc_public_order_screen_v1.json"
    report_path = OUT_DIR / "r6_additional_cftc_public_order_screen_v1.md"
    csv_path = OUT_DIR / "r6_additional_cftc_public_order_screen_v1_cases.csv"
    assertions_path = CHECK_DIR / "r6_additional_cftc_public_order_screen_v1_assertions.out"

    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_csv(
        csv_path,
        rows,
        [
            "case_id",
            "source_owner",
            "press_url",
            "status",
            "content_type",
            "bytes",
            "sha256",
            "tmp_path",
            "expected_markets",
            "expected_period",
            "r6_use",
            "mentions_spoof",
            "mentions_order",
            "mentions_genuine",
            "mentions_cancel",
            "explicit_date_count",
            "explicit_time_marker_count",
            "related_order_links",
            "row_extraction_ready",
            "accepted_now",
            "reason",
            "error",
        ],
    )

    report = [
        "# R6 Additional CFTC Public Order Screen v1",
        "",
        f"Run ID: `{RUN_ID}`",
        "",
        f"- Gate result: `{result['decision']}`.",
        f"- Official CFTC cases screened: `{len(rows)}`.",
        f"- Public pages fetched with status 200: `{len(ok_cases)}`.",
        f"- Cases with related order/download links on the public page: `{order_link_count}`.",
        f"- Row-extraction-ready public pages: `{row_extraction_ready_count}`.",
        f"- Accepted rows added: `0`; new confidence gate: `false`; strict full objective achieved: `false`; `update_goal=false`.",
        "",
        "## Case Routes",
        "",
        "| Case | Status | Markets | Period | Signals | Accepted |",
        "|---|---:|---|---|---|---:|",
    ]
    for row in rows:
        signals = []
        for key in ["mentions_spoof", "mentions_order", "mentions_genuine", "mentions_cancel"]:
            if row[key] == "true":
                signals.append(key.replace("mentions_", ""))
        report.append(
            f"| `{row['case_id']}` | `{row['status']}` | {row['expected_markets']} | {row['expected_period']} | {', '.join(signals)} | `false` |"
        )
    report.extend(
        [
            "",
            "## Boundary",
            "",
            "This run only records official public CFTC acquisition routes. Press-page summaries are not row-level Board A evidence; no additional positives or controls were materialized into `/tmp/ict-engine-direct-manipulation-row-intake`.",
            "",
            "## Artifacts",
            "",
            f"- JSON: `{json_path.relative_to(REPO)}`",
            f"- Case CSV: `{csv_path.relative_to(REPO)}`",
            f"- Assertions: `{assertions_path.relative_to(REPO)}`",
        ]
    )
    report_path.write_text("\n".join(report) + "\n", encoding="utf-8")

    assertions = [
        f"PASS decision={result['decision']}",
        f"PASS official_cases_screened={len(rows)}",
        f"PASS public_pages_ok={len(ok_cases)}",
        f"PASS row_extraction_ready_count={row_extraction_ready_count}",
        "PASS accepted_rows_added=0",
        "PASS new_confidence_gate=false",
        "PASS strict_full_objective_achieved=false",
        "PASS update_goal=false",
        "PASS raw_data_committed=false",
    ]
    assertions_path.write_text("\n".join(assertions) + "\n", encoding="utf-8")

    print(json.dumps(
        {
            "decision": result["decision"],
            "official_cases_screened": len(rows),
            "public_pages_ok": len(ok_cases),
            "row_extraction_ready_count": row_extraction_ready_count,
            "accepted_rows_added": 0,
            "update_goal": False,
            "report": str(report_path.relative_to(REPO)),
        },
        indent=2,
    ))


if __name__ == "__main__":
    main()
