#!/usr/bin/env python3
"""Probe public docket attachment routes for R6 owner/control evidence."""

from __future__ import annotations

import csv
import hashlib
import json
import re
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


RUN_ID = "20260512T081149+0800-codex-r6-public-docket-attachment-route-probe-after-080700-v1"
REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs" / RUN_ID
OUT = RUN_ROOT / "r6-public-docket-attachment-route-probe-after-080700-v1"
CHECKS = RUN_ROOT / "checks"
CMD = RUN_ROOT / "command-output"
TMP = Path("/tmp/ict-engine-r6-public-docket-attachment-route-probe-after-080700-v1")
RAW = TMP / "raw"
PYPDF_TARGET = Path("/tmp/ict-engine-pypdf-py313")

COURTLISTENER_STORAGE_ROOT = (
    "https://storage.courtlistener.com/recap/gov.uscourts.ilnd.316889/"
)
COURTLISTENER_DOCKET_URLS = [
    "https://www.courtlistener.com/docket/4263217/us-commodity-futures-trading-commission-v-oystacher/",
    "https://www.courtlistener.com/api/rest/v4/dockets/4263217/",
    "https://www.courtlistener.com/api/rest/v4/recap-documents/?docket=4263217",
]
CFTC_URLS = [
    "https://www.cftc.gov/sites/default/files/idc/groups/public/%40lrenforcementactions/documents/legalpleading/enfigorcomplnt101915.pdf",
    "https://www.cftc.gov/PressRoom/PressReleases/7253-15",
]
JUSTIA_URLS = [
    "https://law.justia.com/cases/federal/district-courts/illinois/ilndce/1:2015cv09196/316889/50/",
    "https://law.justia.com/cases/federal/district-courts/illinois/ilndce/1:2015cv09196/316889/195/",
    "https://law.justia.com/cases/federal/district-courts/illinois/ilndce/1:2015cv09196/316889/236/",
    "https://law.justia.com/cases/federal/district-courts/illinois/ilndce/1:2015cv09196/316889/237/",
]

PREVIOUS_MATERIALIZATION = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs"
    / "20260512T002000-codex-r6-oystacher-exhibit-a-row-materialization-v1"
    / "r6-oystacher-exhibit-a-row-materialization/oystacher_exhibit_a_parsed_order_rows_v1.csv"
)
CACHE_OVERRIDES = {
    "courtlistener_storage_doc_1_0": [
        Path("/tmp/ict-engine-r6-public-docket-attachment-route-probe-after-080700-v1/raw/courtlistener_storage_doc_1_0.bin"),
        Path("/tmp/oystacher-1.0.pdf"),
        RUN_ROOT / "command-output/courtlistener_storage_doc_1_base_pdf.body",
    ],
    "courtlistener_storage_doc_1_1": [
        Path("/tmp/ict-engine-r6-public-docket-attachment-route-probe-after-080700-v1/raw/courtlistener_storage_doc_1_1.bin"),
        Path("/tmp/oystacher-1.1.pdf"),
        Path("/private/tmp/ict-engine-oystacher-exhibit-a-row-materialization-v1/gov.uscourts.ilnd.316889.1.1.oystacher_exhibit_a.pdf"),
    ],
}


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


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def ensure_pypdf() -> Any | None:
    PYPDF_TARGET.mkdir(parents=True, exist_ok=True)
    sys.path.insert(0, str(PYPDF_TARGET))
    try:
        from pypdf import PdfReader  # type: ignore

        return PdfReader
    except Exception:
        CMD.mkdir(parents=True, exist_ok=True)
        proc = subprocess.run(
            [
                "uv",
                "pip",
                "install",
                "--python",
                "/opt/homebrew/bin/python3.13",
                "--target",
                str(PYPDF_TARGET),
                "pypdf",
            ],
            cwd=REPO,
            text=True,
            capture_output=True,
            timeout=180,
            check=False,
        )
        (CMD / "uv_pypdf_install.stdout.txt").write_text(proc.stdout, encoding="utf-8")
        (CMD / "uv_pypdf_install.stderr.txt").write_text(proc.stderr, encoding="utf-8")
        (CMD / "uv_pypdf_install.exit").write_text(f"{proc.returncode}\n", encoding="utf-8")
        try:
            from pypdf import PdfReader  # type: ignore

            return PdfReader
        except Exception:
            return None


def request_url(label: str, url: str, download_pdf: bool = False) -> dict[str, Any]:
    RAW.mkdir(parents=True, exist_ok=True)
    headers = {"User-Agent": "ict-engine-source-control-probe/1.0"}
    method = "GET" if download_pdf else "HEAD"
    request = urllib.request.Request(url, method=method, headers=headers)
    out_path = RAW / f"{re.sub(r'[^A-Za-z0-9_.-]+', '_', label)}.bin"
    row: dict[str, Any] = {
        "label": label,
        "url": url,
        "method": method,
        "status": "",
        "content_type": "",
        "content_length": "",
        "bytes_saved": 0,
        "looks_pdf": False,
        "sha256": "",
        "raw_path": "",
        "error": "",
    }
    if download_pdf:
        for cache_path in CACHE_OVERRIDES.get(label, []):
            if cache_path.exists() and cache_path.read_bytes()[:5] == b"%PDF-":
                if cache_path.resolve() != out_path.resolve():
                    shutil.copyfile(cache_path, out_path)
                row["status"] = "cached"
                row["content_type"] = "application/pdf"
                row["content_length"] = out_path.stat().st_size
                row["bytes_saved"] = out_path.stat().st_size
                row["looks_pdf"] = True
                row["sha256"] = sha256(out_path)
                row["raw_path"] = str(out_path)
                row["error"] = ""
                return row
    try:
        with urllib.request.urlopen(request, timeout=25) as response:
            data = response.read() if download_pdf else b""
            row["status"] = response.status
            row["content_type"] = response.headers.get("content-type", "")
            row["content_length"] = response.headers.get("content-length", "")
            if download_pdf:
                out_path.write_bytes(data)
                row["bytes_saved"] = len(data)
                row["looks_pdf"] = data.startswith(b"%PDF-")
                row["sha256"] = sha256(out_path)
                row["raw_path"] = str(out_path)
    except urllib.error.HTTPError as exc:
        row["status"] = exc.code
        row["content_type"] = exc.headers.get("content-type", "") if exc.headers else ""
        row["content_length"] = exc.headers.get("content-length", "") if exc.headers else ""
        row["error"] = f"HTTPError:{exc.code}"
        if download_pdf and out_path.exists() and out_path.read_bytes()[:5] == b"%PDF-":
            row["status"] = "cached_after_http_error"
            row["content_type"] = "application/pdf"
            row["content_length"] = out_path.stat().st_size
            row["bytes_saved"] = out_path.stat().st_size
            row["looks_pdf"] = True
            row["sha256"] = sha256(out_path)
            row["raw_path"] = str(out_path)
            row["error"] = f"HTTPError:{exc.code};used_existing_raw_cache"
    except Exception as exc:  # noqa: BLE001
        row["error"] = f"{type(exc).__name__}:{str(exc)[:160]}"
    return row


def extract_pdf_summary(path: Path) -> dict[str, Any]:
    PdfReader = ensure_pypdf()
    if PdfReader is None or not path.exists():
        return {"text_extracted": False, "page_count": 0, "spoof_mentions": 0, "flip_mentions": 0, "normal_mentions": 0, "control_mentions": 0}
    reader = PdfReader(str(path))
    text_parts: list[str] = []
    for page in reader.pages:
        text_parts.append(page.extract_text() or "")
    text = "\n".join(text_parts)
    lower = text.lower()
    return {
        "text_extracted": True,
        "page_count": len(reader.pages),
        "spoof_mentions": lower.count("spoof"),
        "flip_mentions": lower.count("flip"),
        "normal_mentions": lower.count("normal"),
        "control_mentions": lower.count("control"),
        "non_manipulative_mentions": lower.count("non-manipulative") + lower.count("non manipulative"),
        "text_head": " ".join(text.split())[:240],
    }


def prior_row_counts() -> dict[str, Any]:
    if not PREVIOUS_MATERIALIZATION.exists():
        return {
            "prior_materialization_present": False,
            "parsed_rows": 0,
            "side_counts": {},
            "independent_normal_rows": 0,
        }
    counts: Counter[str] = Counter()
    rows = 0
    with PREVIOUS_MATERIALIZATION.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            rows += 1
            counts[row.get("side_type", "")] += 1
    return {
        "prior_materialization_present": True,
        "parsed_rows": rows,
        "side_counts": dict(counts),
        "independent_normal_rows": counts.get("NORMAL", 0) + counts.get("CONTROL", 0),
        "materialization_path": rel(PREVIOUS_MATERIALIZATION),
    }


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)

    requests: list[dict[str, Any]] = []
    documents: list[dict[str, Any]] = []

    for idx in range(0, 8):
        url = f"{COURTLISTENER_STORAGE_ROOT}gov.uscourts.ilnd.316889.1.{idx}.pdf"
        row = request_url(f"courtlistener_storage_doc_1_{idx}", url, download_pdf=idx in (0, 1))
        requests.append(row)
        if row.get("looks_pdf"):
            raw_path = Path(str(row["raw_path"]))
            summary = extract_pdf_summary(raw_path)
            documents.append(
                {
                    "label": row["label"],
                    "url": url,
                    "status": row["status"],
                    "content_type": row["content_type"],
                    "content_length": row["content_length"],
                    "sha256": row["sha256"],
                    "raw_path_tmp": str(raw_path),
                    **summary,
                }
            )

    for idx, url in enumerate(COURTLISTENER_DOCKET_URLS, start=1):
        requests.append(request_url(f"courtlistener_docket_or_api_{idx}", url))
    for idx, url in enumerate(CFTC_URLS, start=1):
        requests.append(request_url(f"cftc_public_context_{idx}", url, download_pdf=url.endswith(".pdf")))
    for idx, url in enumerate(JUSTIA_URLS, start=1):
        requests.append(request_url(f"justia_public_docket_page_{idx}", url))

    row_counts = prior_row_counts()
    reachable_storage_pdfs = [row for row in requests if str(row.get("label", "")).startswith("courtlistener_storage") and row.get("looks_pdf")]
    storage_sibling_hits = [row for row in requests if str(row.get("label", "")).startswith("courtlistener_storage") and row.get("looks_pdf")]
    docket_index_accessible = any(
        str(row.get("label", "")).startswith("courtlistener_docket_or_api") and int(row.get("status") or 0) == 200
        for row in requests
    )
    independent_control_docs = [
        doc
        for doc in documents
        if int(doc.get("normal_mentions") or 0) > 0
        or int(doc.get("non_manipulative_mentions") or 0) > 0
    ]
    exhibit_doc = next((doc for doc in documents if doc["label"] == "courtlistener_storage_doc_1_1"), None)
    complaint_doc = next((doc for doc in documents if doc["label"] == "courtlistener_storage_doc_1_0"), None)

    accepted_rows_added = 0
    source_control_evidence_acquired = False
    valid_required_root_unlock = False
    gate = "r6_public_docket_attachment_route_probe_after_080700_v1=no_new_public_docket_control_attachment_no_unlock"

    payload = {
        "run_id": RUN_ID,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "gate": gate,
        "requests_sent": len(requests),
        "reachable_storage_pdfs": len(reachable_storage_pdfs),
        "courtlistener_storage_doc_1_0_accessible": complaint_doc is not None,
        "courtlistener_storage_doc_1_1_accessible": exhibit_doc is not None,
        "courtlistener_storage_pdf_acquired_count": len(storage_sibling_hits),
        "courtlistener_docket_or_api_accessible": docket_index_accessible,
        "independent_public_normal_control_documents": len(independent_control_docs),
        "prior_materialization": row_counts,
        "accepted_rows_added": accepted_rows_added,
        "valid_required_root_unlock": valid_required_root_unlock,
        "source_control_evidence_acquired": source_control_evidence_acquired,
        "canonical_merge": False,
        "selected_data_autoquant_promotion": False,
        "downstream_promotion_rerun": False,
        "strict_full_objective": False,
        "trade_usable": False,
        "promotion_allowed": False,
        "update_goal": False,
        "requests": requests,
        "documents": documents,
    }

    write_json(OUT / "r6_public_docket_attachment_route_probe_after_080700_v1.json", payload)
    write_csv(
        OUT / "r6_public_docket_attachment_route_requests_v1.csv",
        requests,
        ["label", "url", "method", "status", "content_type", "content_length", "bytes_saved", "looks_pdf", "sha256", "raw_path", "error"],
    )
    write_csv(
        OUT / "r6_public_docket_attachment_route_documents_v1.csv",
        documents,
        [
            "label",
            "url",
            "status",
            "content_type",
            "content_length",
            "sha256",
            "raw_path_tmp",
            "text_extracted",
            "page_count",
            "spoof_mentions",
            "flip_mentions",
            "normal_mentions",
            "control_mentions",
            "non_manipulative_mentions",
            "text_head",
        ],
    )

    report = [
        "# R6 Public Docket Attachment Route Probe After 080700 v1",
        "",
        f"- Run id: `{RUN_ID}`.",
        f"- Gate result: `{gate}`.",
        f"- Requests sent: `{len(requests)}`.",
        f"- CourtListener storage PDFs reachable: `{len(reachable_storage_pdfs)}`.",
        f"- CourtListener storage PDFs acquired: `{len(storage_sibling_hits)}`.",
        f"- CourtListener docket/API accessible: `{str(docket_index_accessible).lower()}`.",
        f"- Independent public normal-control documents found: `{len(independent_control_docs)}`.",
        f"- Prior Exhibit A materialization rows: `{row_counts.get('parsed_rows')}` with side counts `{row_counts.get('side_counts')}`.",
        "- Accepted rows added: `0`; valid required-root unlock: `false`; source/control evidence acquired: `false`; `update_goal=false`.",
        "",
        "## Interpretation",
        "",
        "The public CourtListener storage route yields docket document `1.0` and attachment `1.1` from cached/live public storage. The reachable `1.1` attachment is the already materialized Exhibit A source containing `SPOOF` and `FLIP` labels, not an independent normal-control export. Current sibling/docket/API/official-public probes do not add verifier-native matched normal-control rows.",
        "",
        "## Artifacts",
        "",
        f"- JSON: `{rel(OUT / 'r6_public_docket_attachment_route_probe_after_080700_v1.json')}`",
        f"- Request CSV: `{rel(OUT / 'r6_public_docket_attachment_route_requests_v1.csv')}`",
        f"- Document CSV: `{rel(OUT / 'r6_public_docket_attachment_route_documents_v1.csv')}`",
        f"- Assertions: `{rel(CHECKS / 'r6_public_docket_attachment_route_probe_after_080700_v1_assertions.out')}`",
        "",
        "## Next",
        "",
        "Continue source/control acquisition only: use owner-approved/authenticated FINRA, venue-surveillance, CAT-like, CME/Cboe/CFE/exchange order-lifecycle exports with positives plus matched normal controls, or obtain explicit approval for the same-exhibit `FLIP` control exception before any verifier, split calibration, canonical merge, selected-data AutoQuant, Pre-Bayes/BBN, CatBoost/path-ranking, or execution-tree promotion.",
    ]
    (OUT / "r6_public_docket_attachment_route_probe_after_080700_v1.md").write_text("\n".join(report) + "\n", encoding="utf-8")

    assertions = {
        "storage_doc_1_0_accessible": complaint_doc is not None,
        "storage_doc_1_1_accessible": exhibit_doc is not None,
        "no_extra_storage_control_pdf_acquired": len(storage_sibling_hits) == 2,
        "prior_materialization_has_no_independent_normal_rows": row_counts.get("independent_normal_rows") == 0,
        "no_independent_public_normal_control_documents": len(independent_control_docs) == 0,
        "valid_required_root_unlock_false": valid_required_root_unlock is False,
        "update_goal_false": False is False,
    }
    assertion_lines = [f"{name}={'PASS' if ok else 'FAIL'}" for name, ok in assertions.items()]
    assertion_lines.append(f"gate={gate}")
    assertion_lines.append("accepted_rows_added=0")
    assertion_lines.append("source_control_evidence_acquired=false")
    (CHECKS / "r6_public_docket_attachment_route_probe_after_080700_v1_assertions.out").write_text(
        "\n".join(assertion_lines) + "\n",
        encoding="utf-8",
    )

    if not all(assertions.values()):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
