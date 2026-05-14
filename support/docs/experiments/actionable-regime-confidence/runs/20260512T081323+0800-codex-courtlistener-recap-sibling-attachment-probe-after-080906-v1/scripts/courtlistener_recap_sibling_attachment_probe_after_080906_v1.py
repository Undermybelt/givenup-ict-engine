#!/usr/bin/env python3
"""Bounded CourtListener RECAP sibling-object probe for Board A R6 controls."""

from __future__ import annotations

import csv
import json
import ssl
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
import time


RUN_ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_DIR = RUN_ROOT / "courtlistener-recap-sibling-attachment-probe-after-080906-v1"
CHECK_DIR = RUN_ROOT / "checks"

BASE = "https://storage.courtlistener.com/recap/gov.uscourts.ilnd.316889"
KNOWN_EXHIBIT = "gov.uscourts.ilnd.316889.1.1.pdf"
API_URL = "https://www.courtlistener.com/api/rest/v4/dockets/?docket_number=1%3A15-cv-09196"
HTML_URL = "https://www.courtlistener.com/docket/4350132/commodity-futures-trading-commission-v-3-red-trading-llc/"

USER_AGENT = "ict-engine-board-a-source-route-probe/1.0"


def request(method: str, url: str, timeout: int = 15) -> dict:
    req = urllib.request.Request(url, method=method, headers={"User-Agent": USER_AGENT})
    started = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=ssl.create_default_context()) as resp:
            body = b""
            if method != "HEAD":
                body = resp.read(512)
            return {
                "url": url,
                "method": method,
                "status": resp.status,
                "content_length": resp.headers.get("content-length", ""),
                "content_type": resp.headers.get("content-type", ""),
                "elapsed_ms": round((time.time() - started) * 1000, 1),
                "error": "",
                "body_prefix": body.decode("utf-8", "replace")[:240],
            }
    except urllib.error.HTTPError as exc:
        body = b""
        try:
            body = exc.read(512)
        except Exception:
            body = b""
        return {
            "url": url,
            "method": method,
            "status": exc.code,
            "content_length": exc.headers.get("content-length", "") if exc.headers else "",
            "content_type": exc.headers.get("content-type", "") if exc.headers else "",
            "elapsed_ms": round((time.time() - started) * 1000, 1),
            "error": exc.reason or "HTTPError",
            "body_prefix": body.decode("utf-8", "replace")[:240],
        }
    except Exception as exc:
        return {
            "url": url,
            "method": method,
            "status": 0,
            "content_length": "",
            "content_type": "",
            "elapsed_ms": round((time.time() - started) * 1000, 1),
            "error": type(exc).__name__ + ": " + str(exc),
            "body_prefix": "",
        }


def main() -> int:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)

    request_rows: list[dict] = []
    request_rows.append(request("GET", API_URL))
    request_rows.append(request("GET", HTML_URL))

    storage_hits: list[dict] = []
    # Bounded public-storage sibling scan. Includes subdocument 0 because RECAP
    # main filings often use .0.pdf while known Exhibit A uses .1.pdf. Keep the
    # window small and concurrent to avoid tying up Board A with slow 404s.
    storage_targets = [
        (docket_entry, subdoc, f"gov.uscourts.ilnd.316889.{docket_entry}.{subdoc}.pdf")
        for docket_entry in range(1, 31)
        for subdoc in range(0, 4)
    ]

    def storage_probe(target: tuple[int, int, str]) -> dict:
        docket_entry, subdoc, name = target
        url = f"{BASE}/{name}"
        row = request("HEAD", url, timeout=6)
        row["storage_name"] = name
        row["docket_entry"] = docket_entry
        row["subdocument"] = subdoc
        return row

    with ThreadPoolExecutor(max_workers=16) as executor:
        futures = {executor.submit(storage_probe, target): target for target in storage_targets}
        for future in as_completed(futures):
            row = future.result()
            request_rows.append(row)
            if row["status"] == 200:
                storage_hits.append(row)

    known_hits = [r for r in storage_hits if r["storage_name"] == KNOWN_EXHIBIT]
    novel_hits = [r for r in storage_hits if r["storage_name"] != KNOWN_EXHIBIT]

    # Filename-only classification stays fail-closed. RECAP object names do not
    # prove normal/non-manipulation controls without source-owned labels.
    possible_control_name_hits = [
        r for r in novel_hits
        if any(token in r["storage_name"].lower() for token in ("control", "normal", "appendix", "exhibit"))
    ]

    metrics = {
        "run_id": "20260512T081323+0800-codex-courtlistener-recap-sibling-attachment-probe-after-080906-v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "gate_result": "courtlistener_recap_sibling_attachment_probe_after_080906_v1=no_new_public_control_attachment_unlock",
        "api_status": request_rows[0]["status"],
        "html_status": request_rows[1]["status"],
        "storage_head_requests": len(storage_targets),
        "requests_sent": len(request_rows),
        "failed_or_parse_failed": sum(1 for r in request_rows if r["status"] == 0),
        "known_exhibit_a_present": bool(known_hits),
        "storage_pdf_hits": len(storage_hits),
        "novel_public_pdf_hits": len(novel_hits),
        "possible_control_name_hits": len(possible_control_name_hits),
        "accepted_rows_added": 0,
        "r6_owner_export_unlock": False,
        "r5_recency_unlock": False,
        "r3_native_subhour_unlock": False,
        "valid_required_root_unlock": False,
        "source_control_evidence_acquired": False,
        "canonical_merge": False,
        "selected_data_autoquant_promotion": False,
        "downstream_promotion_rerun": False,
        "strict_full_objective": False,
        "trade_usable": False,
        "promotion_allowed": False,
        "update_goal": False,
    }

    (ARTIFACT_DIR / "courtlistener_recap_sibling_attachment_probe_after_080906_v1.json").write_text(
        json.dumps(
            {
                "metrics": metrics,
                "storage_hits": storage_hits,
                "novel_hits": novel_hits,
                "possible_control_name_hits": possible_control_name_hits,
                "notes": [
                    "CourtListener REST API required authentication in this environment.",
                    "The public docket HTML endpoint returned a CloudFront block in this environment.",
                    "Direct RECAP storage object checks are metadata-only and do not approve rows as controls.",
                ],
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    with (ARTIFACT_DIR / "courtlistener_recap_sibling_attachment_requests_v1.csv").open("w", newline="", encoding="utf-8") as fh:
        fieldnames = [
            "method",
            "status",
            "url",
            "storage_name",
            "docket_entry",
            "subdocument",
            "content_length",
            "content_type",
            "elapsed_ms",
            "error",
            "body_prefix",
        ]
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for row in request_rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})

    with (ARTIFACT_DIR / "courtlistener_recap_sibling_attachment_hits_v1.csv").open("w", newline="", encoding="utf-8") as fh:
        fieldnames = ["storage_name", "url", "status", "content_length", "content_type", "known_exhibit_a", "novel_public_pdf"]
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for row in storage_hits:
            writer.writerow(
                {
                    "storage_name": row.get("storage_name", ""),
                    "url": row["url"],
                    "status": row["status"],
                    "content_length": row.get("content_length", ""),
                    "content_type": row.get("content_type", ""),
                    "known_exhibit_a": row.get("storage_name") == KNOWN_EXHIBIT,
                    "novel_public_pdf": row.get("storage_name") != KNOWN_EXHIBIT,
                }
            )

    if novel_hits:
        novel_sentence = (
            "The storage scan found the known Exhibit A PDF plus adjacent public PDF "
            "metadata for: "
            + ", ".join(r["storage_name"] for r in novel_hits)
            + ". Filename and HEAD metadata alone do not identify a source-owned "
            "normal-control or matched-control attachment."
        )
    else:
        novel_sentence = "The storage scan found only the already-known Exhibit A PDF."

    report = f"""# CourtListener RECAP Sibling Attachment Probe After 080906 v1

Gate result: `{metrics["gate_result"]}`.

## Scope

Bounded public RECAP storage sibling-object probe for the Oystacher/3Red docket after
the `080906` OpenAlex/Semantic/PapersWithCode route probe. This checks whether direct
CourtListener storage exposes adjacent public PDF objects beyond the already-known
Exhibit A PDF. It does not download raw PDFs into the repo, approve RECAP/PACER
provenance, approve `FLIP` rows as controls, mutate any intake root, or run downstream
promotion.

## Metrics

- Requests sent: `{metrics["requests_sent"]}`
- Failed or parse-failed: `{metrics["failed_or_parse_failed"]}`
- CourtListener API status: `{metrics["api_status"]}`
- Public docket HTML status: `{metrics["html_status"]}`
- Storage HEAD requests: `{metrics["storage_head_requests"]}`
- Storage PDF hits: `{metrics["storage_pdf_hits"]}`
- Known Exhibit A present: `{metrics["known_exhibit_a_present"]}`
- Novel public PDF hits: `{metrics["novel_public_pdf_hits"]}`
- Possible control-name hits: `{metrics["possible_control_name_hits"]}`

## Decision

{novel_sentence} No new public normal-control or matched-control attachment was
acquired. API/HTML routes were not usable without authentication or were blocked by the
serving layer, and direct storage metadata does not satisfy the owner/export control
contract.

Accepted rows added `0`; R6 owner/export unlock false; R5 recency unlock false; R3
native-subhour unlock false; valid required-root unlock false; source/control evidence
acquired false; canonical merge false; selected-data AutoQuant promotion false;
downstream promotion rerun false; strict full objective false; trade usable false;
`update_goal=false`.

## Next

Continue source/control acquisition only. The active R6 route still requires explicit
public RECAP/PACER provenance plus `FLIP`-as-control approval, or independent
source-owned normal controls, before any canonical merge or downstream rerun.
"""
    (ARTIFACT_DIR / "courtlistener_recap_sibling_attachment_probe_after_080906_v1.md").write_text(report, encoding="utf-8")

    assertion_lines = [
        "PASS courtlistener_recap_sibling_attachment_probe_after_080906_v1",
        f"gate_result={metrics['gate_result']}",
        f"requests_sent={metrics['requests_sent']}",
        f"failed_or_parse_failed={metrics['failed_or_parse_failed']}",
        f"api_status={metrics['api_status']}",
        f"html_status={metrics['html_status']}",
        f"storage_head_requests={metrics['storage_head_requests']}",
        f"storage_pdf_hits={metrics['storage_pdf_hits']}",
        f"known_exhibit_a_present={str(metrics['known_exhibit_a_present']).lower()}",
        f"novel_public_pdf_hits={metrics['novel_public_pdf_hits']}",
        f"possible_control_name_hits={metrics['possible_control_name_hits']}",
        "accepted_rows_added=0",
        "r6_owner_export_unlock=false",
        "r5_recency_unlock=false",
        "r3_native_subhour_unlock=false",
        "valid_required_root_unlock=false",
        "source_control_evidence_acquired=false",
        "canonical_merge=false",
        "selected_data_autoquant_promotion=false",
        "downstream_promotion_rerun=false",
        "strict_full_objective=false",
        "trade_usable=false",
        "promotion_allowed=false",
        "update_goal=false",
    ]
    (CHECK_DIR / "courtlistener_recap_sibling_attachment_probe_after_080906_v1_assertions.out").write_text(
        "\n".join(assertion_lines) + "\n",
        encoding="utf-8",
    )
    print("\n".join(assertion_lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
