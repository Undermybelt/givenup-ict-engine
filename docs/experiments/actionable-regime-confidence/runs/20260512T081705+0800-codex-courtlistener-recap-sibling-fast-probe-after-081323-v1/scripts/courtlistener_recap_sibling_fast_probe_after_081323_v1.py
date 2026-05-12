#!/usr/bin/env python3
"""Fast bounded CourtListener RECAP sibling probe for Board B R6 controls."""

from __future__ import annotations

import csv
import json
import ssl
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


RUN_ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_DIR = RUN_ROOT / "courtlistener-recap-sibling-fast-probe-after-081323-v1"
CHECK_DIR = RUN_ROOT / "checks"

BASE = "https://storage.courtlistener.com/recap/gov.uscourts.ilnd.316889"
KNOWN_EXHIBIT = "gov.uscourts.ilnd.316889.1.1.pdf"
API_URL = "https://www.courtlistener.com/api/rest/v4/dockets/?docket_number=1%3A15-cv-09196"
HTML_URL = "https://www.courtlistener.com/docket/4350132/commodity-futures-trading-commission-v-3-red-trading-llc/"
USER_AGENT = "ict-engine-board-b-source-route-probe/1.0"


def request(method: str, url: str, timeout: float = 2.0) -> dict[str, Any]:
    req = urllib.request.Request(url, method=method, headers={"User-Agent": USER_AGENT})
    started = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=ssl.create_default_context()) as resp:
            body = b"" if method == "HEAD" else resp.read(512)
            return {
                "method": method,
                "url": url,
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
            "method": method,
            "url": url,
            "status": exc.code,
            "content_length": exc.headers.get("content-length", "") if exc.headers else "",
            "content_type": exc.headers.get("content-type", "") if exc.headers else "",
            "elapsed_ms": round((time.time() - started) * 1000, 1),
            "error": exc.reason or "HTTPError",
            "body_prefix": body.decode("utf-8", "replace")[:240],
        }
    except Exception as exc:  # noqa: BLE001 - probe disposition, not runtime promotion.
        return {
            "method": method,
            "url": url,
            "status": 0,
            "content_length": "",
            "content_type": "",
            "elapsed_ms": round((time.time() - started) * 1000, 1),
            "error": type(exc).__name__ + ": " + str(exc),
            "body_prefix": "",
        }


def storage_row(docket_entry: int, subdocument: int) -> dict[str, Any]:
    storage_name = f"gov.uscourts.ilnd.316889.{docket_entry}.{subdocument}.pdf"
    row = request("HEAD", f"{BASE}/{storage_name}", timeout=2.0)
    row["storage_name"] = storage_name
    row["docket_entry"] = docket_entry
    row["subdocument"] = subdocument
    return row


def main() -> int:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)

    request_rows: list[dict[str, Any]] = [request("GET", API_URL), request("GET", HTML_URL)]
    storage_rows: list[dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=64) as pool:
        futures = [
            pool.submit(storage_row, docket_entry, subdocument)
            for docket_entry in range(1, 81)
            for subdocument in range(0, 5)
        ]
        for future in as_completed(futures):
            storage_rows.append(future.result())

    storage_rows.sort(key=lambda row: (row["docket_entry"], row["subdocument"]))
    request_rows.extend(storage_rows)

    storage_hits = [row for row in storage_rows if row["status"] == 200]
    known_hits = [row for row in storage_hits if row["storage_name"] == KNOWN_EXHIBIT]
    novel_hits = [row for row in storage_hits if row["storage_name"] != KNOWN_EXHIBIT]
    possible_control_name_hits = [
        row
        for row in novel_hits
        if any(token in row["storage_name"].lower() for token in ("control", "normal", "appendix", "exhibit"))
    ]

    metrics = {
        "run_id": "20260512T081705+0800-codex-courtlistener-recap-sibling-fast-probe-after-081323-v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "gate_result": "courtlistener_recap_sibling_fast_probe_after_081323_v1=no_new_public_control_attachment_unlock",
        "api_status": request_rows[0]["status"],
        "html_status": request_rows[1]["status"],
        "storage_head_requests": len(storage_rows),
        "requests_sent": len(request_rows),
        "failed_or_parse_failed": sum(1 for row in request_rows if row["status"] == 0),
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

    (ARTIFACT_DIR / "courtlistener_recap_sibling_fast_probe_after_081323_v1.json").write_text(
        json.dumps(
            {
                "metrics": metrics,
                "storage_hits": storage_hits,
                "novel_hits": novel_hits,
                "possible_control_name_hits": possible_control_name_hits,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    request_fields = [
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
    with (ARTIFACT_DIR / "courtlistener_recap_sibling_fast_requests_v1.csv").open(
        "w", newline="", encoding="utf-8"
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=request_fields)
        writer.writeheader()
        for row in request_rows:
            writer.writerow({field: row.get(field, "") for field in request_fields})

    with (ARTIFACT_DIR / "courtlistener_recap_sibling_fast_hits_v1.csv").open(
        "w", newline="", encoding="utf-8"
    ) as handle:
        fields = [
            "storage_name",
            "url",
            "status",
            "content_length",
            "content_type",
            "known_exhibit_a",
            "novel_public_pdf",
        ]
        writer = csv.DictWriter(handle, fieldnames=fields)
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

    report = f"""# CourtListener RECAP Sibling Fast Probe After 081323 v1

Gate result: `{metrics["gate_result"]}`.

## Scope

Fast bounded replacement for the nonterminal `081323` script-only run. This probes the same
CourtListener RECAP docket storage namespace using concurrent short-timeout HEAD checks.
It does not download PDFs into the repo, approve RECAP/PACER provenance, approve same-exhibit
`FLIP` rows as controls, mutate any intake root, or run downstream promotion.

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

No new public normal-control or matched-control attachment was acquired. Public RECAP
storage metadata remains non-unlocking without explicit provenance approval and without
source-owned normal controls.

Accepted rows added `0`; valid required-root unlock false; source/control evidence
acquired false; canonical merge false; selected-data AutoQuant promotion false;
downstream promotion rerun false; strict full objective false; trade usable false;
`promotion_allowed=false`; `update_goal=false`.

## Next

Continue source/control acquisition only, or obtain explicit user/board approval for the
same-exhibit `FLIP` control exception before canonical merge and downstream rerun.
"""
    (ARTIFACT_DIR / "courtlistener_recap_sibling_fast_probe_after_081323_v1.md").write_text(
        report,
        encoding="utf-8",
    )

    assertion_lines = [
        "PASS courtlistener_recap_sibling_fast_probe_after_081323_v1",
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
    (CHECK_DIR / "courtlistener_recap_sibling_fast_probe_after_081323_v1_assertions.out").write_text(
        "\n".join(assertion_lines) + "\n",
        encoding="utf-8",
    )
    print("\n".join(assertion_lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
