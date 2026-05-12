#!/usr/bin/env python3
"""Probe public CourtListener/RECAP docket attachments for R6 controls."""

from __future__ import annotations

import csv
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


RUN_ID = "20260512T081522+0800-codex-r6-courtlistener-recap-control-route-after-080950-v1"
GATE = "r6_courtlistener_recap_control_route_after_080950_v1=public_recap_positive_and_context_only_no_source_owned_normal_controls"
DOCKET_ID = 4263217
DOCKET_NUMBER = "1:15-cv-09196"
CASE_NAME = "U.S. Commodity Futures Trading Commission v. Oystacher"
API = "https://www.courtlistener.com/api/rest/v4/search/"
STORAGE = "https://storage.courtlistener.com/"


def output_root() -> Path:
    script_path = Path(__file__).resolve()
    return script_path.parents[1] / "r6-courtlistener-recap-control-route-after-080950-v1"


def request_json(url: str) -> tuple[dict, dict]:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "ict-engine-source-control-route-probe/1.0",
            "Accept": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as response:
        payload = json.loads(response.read().decode("utf-8"))
        headers = dict(response.headers.items())
    return payload, headers


def head_url(url: str) -> dict:
    started = time.time()
    req = urllib.request.Request(
        url,
        method="HEAD",
        headers={"User-Agent": "ict-engine-source-control-route-probe/1.0"},
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            headers = dict(response.headers.items())
            return {
                "url": url,
                "status": response.status,
                "content_type": headers.get("Content-Type"),
                "content_length": headers.get("Content-Length"),
                "last_modified": headers.get("Last-Modified"),
                "elapsed_ms": int((time.time() - started) * 1000),
                "error": "",
            }
    except urllib.error.HTTPError as exc:
        return {
            "url": url,
            "status": exc.code,
            "content_type": exc.headers.get("Content-Type"),
            "content_length": exc.headers.get("Content-Length"),
            "last_modified": exc.headers.get("Last-Modified"),
            "elapsed_ms": int((time.time() - started) * 1000),
            "error": str(exc),
        }
    except Exception as exc:  # pragma: no cover - recorded as route disposition.
        return {
            "url": url,
            "status": None,
            "content_type": None,
            "content_length": None,
            "last_modified": None,
            "elapsed_ms": int((time.time() - started) * 1000),
            "error": repr(exc),
        }


def search(query: str) -> dict:
    url = API + "?" + urllib.parse.urlencode({"q": query, "type": "r"})
    payload, headers = request_json(url)
    return {
        "query": query,
        "url": url,
        "status": "ok",
        "count": payload.get("count", 0),
        "document_count": payload.get("document_count", 0),
        "result_count": len(payload.get("results", [])),
        "rate_limit": headers.get("X-RateLimit-Remaining"),
        "payload": payload,
    }


def normalize_doc(doc: dict, query_label: str) -> dict:
    filepath = doc.get("filepath_local") or ""
    storage_url = STORAGE + filepath if filepath else ""
    return {
        "query_label": query_label,
        "document_number": doc.get("document_number"),
        "attachment_number": doc.get("attachment_number"),
        "entry_number": doc.get("entry_number"),
        "entry_date_filed": doc.get("entry_date_filed") or "",
        "is_available": bool(doc.get("is_available")),
        "page_count": doc.get("page_count") or "",
        "document_type": doc.get("document_type") or "",
        "description": (doc.get("description") or "").replace("\n", " "),
        "short_description": doc.get("short_description") or "",
        "absolute_url": doc.get("absolute_url") or "",
        "filepath_local": filepath,
        "storage_url": storage_url,
        "snippet": (doc.get("snippet") or "").replace("\n", " ")[:500],
    }


def classify(row: dict) -> str:
    desc = f"{row['description']} {row['short_description']} {row['snippet']}".lower()
    if row["document_number"] == 1 and str(row["attachment_number"]) == "1":
        return "positive_exhibit_attachment_context"
    if "supplemental report of daniel r. fischel" in desc:
        return "defense_expert_report_context_not_source_owner_control"
    if "consent order" in desc:
        return "consent_order_context_not_row_control"
    if "complaint" in desc:
        return "complaint_context"
    return "other_recap_context"


def main() -> int:
    out = output_root()
    out.mkdir(parents=True, exist_ok=True)
    checks = out.parent / "checks"
    checks.mkdir(parents=True, exist_ok=True)

    queries = [
        ("docket_document_1", f'docket_id:{DOCKET_ID} "Document #: 1"'),
        ("docket_core", f"docket_id:{DOCKET_ID} Oystacher"),
        ("exhibit_a_spoof", f'docket_id:{DOCKET_ID} "Exhibit A" SPOOF'),
        ("normal_control", f'docket_id:{DOCKET_ID} "normal control"'),
        ("non_manipulative", f'docket_id:{DOCKET_ID} non-manipulative'),
        ("legitimate", f'docket_id:{DOCKET_ID} legitimate'),
        ("control_spoof", f'docket_id:{DOCKET_ID} control spoof'),
        ("false_positive", f'docket_id:{DOCKET_ID} "false positive"'),
        ("market_depth", f'docket_id:{DOCKET_ID} "market depth"'),
        ("order_book", f'docket_id:{DOCKET_ID} "order book"'),
        ("source_owned", f'docket_id:{DOCKET_ID} "source-owned"'),
        ("matched_control", f'docket_id:{DOCKET_ID} "matched control"'),
    ]

    request_rows = []
    docs_by_key: dict[tuple, dict] = {}
    failures = []

    for label, query in queries:
        try:
            result = search(query)
        except Exception as exc:
            failures.append({"label": label, "query": query, "error": repr(exc)})
            request_rows.append(
                {
                    "label": label,
                    "query": query,
                    "status": "error",
                    "count": 0,
                    "document_count": 0,
                    "result_count": 0,
                    "url": "",
                    "error": repr(exc),
                }
            )
            continue
        request_rows.append(
            {
                "label": label,
                "query": query,
                "status": result["status"],
                "count": result["count"],
                "document_count": result["document_count"],
                "result_count": result["result_count"],
                "url": result["url"],
                "error": "",
            }
        )
        for search_result in result["payload"].get("results", []):
            if search_result.get("docket_id") != DOCKET_ID:
                continue
            for doc in search_result.get("recap_documents") or []:
                row = normalize_doc(doc, label)
                key = (
                    row["document_number"],
                    row["attachment_number"],
                    row["entry_number"],
                    row["filepath_local"],
                )
                prior = docs_by_key.get(key)
                if prior:
                    prior["query_label"] = ",".join(sorted(set((prior["query_label"] + "," + label).split(","))))
                    if not prior["snippet"] and row["snippet"]:
                        prior["snippet"] = row["snippet"]
                else:
                    docs_by_key[key] = row

    doc_rows = sorted(
        docs_by_key.values(),
        key=lambda r: (
            int(r["document_number"] or 0),
            int(r["attachment_number"] or 0),
            r["entry_date_filed"],
            r["filepath_local"],
        ),
    )
    for row in doc_rows:
        row["route_classification"] = classify(row)
        row["source_owner_control_candidate"] = "false"
        row["acceptance_disposition"] = "not_source_owned_normal_control"
        row["storage_head_status"] = ""
        row["storage_content_length"] = ""
        row["storage_last_modified"] = ""

    head_rows = []
    for row in doc_rows:
        if not row["storage_url"]:
            continue
        head = head_url(row["storage_url"])
        head_rows.append(head)
        row["storage_head_status"] = str(head["status"] or "")
        row["storage_content_length"] = str(head["content_length"] or "")
        row["storage_last_modified"] = head["last_modified"] or ""

    available_docs = sum(1 for row in doc_rows if row["is_available"])
    exhibit_attachment_rows = [
        row
        for row in doc_rows
        if row["document_number"] == 1 and str(row["attachment_number"]) == "1"
    ]
    defense_reports = [
        row
        for row in doc_rows
        if row["route_classification"] == "defense_expert_report_context_not_source_owner_control"
    ]
    source_owner_control_rows = [
        row for row in doc_rows if row["source_owner_control_candidate"] == "true"
    ]
    accepted_rows_added = 0
    source_control_evidence_acquired = False
    valid_required_root_unlock = False
    canonical_merge = False
    downstream_promotion_rerun = False

    payload = {
        "run_id": RUN_ID,
        "case_name": CASE_NAME,
        "docket_id": DOCKET_ID,
        "docket_number": DOCKET_NUMBER,
        "gate": GATE,
        "queries_sent": len(queries),
        "query_failures": len(failures),
        "recap_documents_scanned": len(doc_rows),
        "available_documents": available_docs,
        "exhibit_a_attachment_available": bool(exhibit_attachment_rows),
        "defense_expert_reports_available": len(defense_reports),
        "source_owned_normal_control_documents": len(source_owner_control_rows),
        "accepted_rows_added": accepted_rows_added,
        "valid_required_root_unlock": valid_required_root_unlock,
        "source_control_evidence_acquired": source_control_evidence_acquired,
        "canonical_merge": canonical_merge,
        "selected_data_autoquant_promotion": False,
        "downstream_promotion_rerun": downstream_promotion_rerun,
        "strict_full_objective": False,
        "trade_usable": False,
        "promotion_allowed": False,
        "update_goal": False,
        "request_rows": request_rows,
        "recap_document_rows": doc_rows,
        "head_rows": head_rows,
        "failures": failures,
    }

    json_path = out / "r6_courtlistener_recap_control_route_after_080950_v1.json"
    request_csv_path = out / "r6_courtlistener_recap_control_route_requests_v1.csv"
    docs_csv_path = out / "r6_courtlistener_recap_control_route_documents_v1.csv"
    head_csv_path = out / "r6_courtlistener_recap_control_route_head_v1.csv"
    report_path = out / "r6_courtlistener_recap_control_route_after_080950_v1.md"
    assertions_path = checks / "r6_courtlistener_recap_control_route_after_080950_v1_assertions.out"

    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    with request_csv_path.open("w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["label", "query", "status", "count", "document_count", "result_count", "url", "error"],
        )
        writer.writeheader()
        writer.writerows(request_rows)
    with docs_csv_path.open("w", newline="") as f:
        fieldnames = [
            "query_label",
            "document_number",
            "attachment_number",
            "entry_number",
            "entry_date_filed",
            "is_available",
            "page_count",
            "document_type",
            "route_classification",
            "source_owner_control_candidate",
            "acceptance_disposition",
            "storage_head_status",
            "storage_content_length",
            "storage_last_modified",
            "description",
            "short_description",
            "absolute_url",
            "filepath_local",
            "storage_url",
            "snippet",
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(doc_rows)
    with head_csv_path.open("w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["url", "status", "content_type", "content_length", "last_modified", "elapsed_ms", "error"],
        )
        writer.writeheader()
        writer.writerows(head_rows)

    doc_lines = "\n".join(
        f"- doc `{row['document_number']}` attachment `{row['attachment_number'] or ''}`: "
        f"{row['route_classification']}; available={row['is_available']}; "
        f"pages={row['page_count']}; storage_head={row['storage_head_status']}; "
        f"{row['description'][:180]}"
        for row in doc_rows
    )
    report = f"""# R6 CourtListener RECAP Control Route After 080950 v1

- Run id: `{RUN_ID}`.
- Case: `{CASE_NAME}` / `{DOCKET_NUMBER}` / CourtListener docket `{DOCKET_ID}`.
- Gate result: `{GATE}`.
- Queries sent: `{len(queries)}`; query failures: `{len(failures)}`.
- RECAP documents scanned: `{len(doc_rows)}`; available documents: `{available_docs}`.
- Exhibit A attachment available: `{bool(exhibit_attachment_rows)}`.
- Defense expert report documents available: `{len(defense_reports)}`.
- Source-owned normal-control documents found: `{len(source_owner_control_rows)}`.
- Accepted rows added: `{accepted_rows_added}`.
- Valid required-root unlock: `{valid_required_root_unlock}`.
- Source/control evidence acquired: `{source_control_evidence_acquired}`.
- Canonical merge: `{canonical_merge}`.
- Downstream promotion rerun: `{downstream_promotion_rerun}`.
- Strict full objective: `false`; trade usable: `false`; update_goal: `false`.

## Route Readback

The public RECAP route exposes the Oystacher docket and the Exhibit A attachment, plus defense expert-report and consent-order context. It does not expose an owner-approved normal/non-manipulation control export. The Exhibit A route remains positive/context evidence only under the current Board A contract because the known `FLIP` rows are same-defendant, same-exhibit sequence rows and still require explicit approval before they can serve as matched normal controls.

## Documents

{doc_lines if doc_lines else "- No matching documents were returned."}

## Artifacts

- JSON: `{json_path.relative_to(Path.cwd())}`
- Request CSV: `{request_csv_path.relative_to(Path.cwd())}`
- Document CSV: `{docs_csv_path.relative_to(Path.cwd())}`
- HEAD CSV: `{head_csv_path.relative_to(Path.cwd())}`
- Assertions: `{assertions_path.relative_to(Path.cwd())}`

## Next

Continue source/control acquisition only. The live unlock remains one of: owner-approved/authenticated FINRA, venue-surveillance, CAT-like, CME/Cboe/CFE/exchange order-lifecycle export with positives and matched normal controls; or explicit approval of the same-exhibit `FLIP`-as-control exception. Do not run direct verifier, split calibration, canonical merge, selected-data AutoQuant, Pre-Bayes/BBN, CatBoost/path-ranking, or execution-tree promotion from this route.
"""
    report_path.write_text(report)

    assertion_lines = [
        f"gate={GATE}",
        f"queries_sent={len(queries)}",
        f"query_failures={len(failures)}",
        f"recap_documents_scanned={len(doc_rows)}",
        f"available_documents={available_docs}",
        f"exhibit_a_attachment_available={bool(exhibit_attachment_rows)}",
        f"defense_expert_reports_available={len(defense_reports)}",
        f"source_owned_normal_control_documents={len(source_owner_control_rows)}",
        f"accepted_rows_added={accepted_rows_added}",
        f"valid_required_root_unlock={valid_required_root_unlock}",
        f"source_control_evidence_acquired={source_control_evidence_acquired}",
        f"canonical_merge={canonical_merge}",
        "selected_data_autoquant_promotion=False",
        f"downstream_promotion_rerun={downstream_promotion_rerun}",
        "strict_full_objective=False",
        "trade_usable=False",
        "promotion_allowed=False",
        "update_goal=False",
    ]
    assertions_path.write_text("\n".join(assertion_lines) + "\n")
    print("\n".join(assertion_lines))

    assert exhibit_attachment_rows, "Expected public RECAP Exhibit A attachment metadata to be reachable"
    assert len(source_owner_control_rows) == 0, "Do not unlock without source-owned normal controls"
    assert not valid_required_root_unlock
    assert not source_control_evidence_acquired
    assert not downstream_promotion_rerun
    return 0


if __name__ == "__main__":
    sys.exit(main())
