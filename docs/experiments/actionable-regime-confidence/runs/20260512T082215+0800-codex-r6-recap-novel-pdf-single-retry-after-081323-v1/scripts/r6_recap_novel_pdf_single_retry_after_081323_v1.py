#!/usr/bin/env python3
"""Classify the RECAP novel-PDF retry output without issuing new requests."""

from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


RUN_ID = "20260512T082215+0800-codex-r6-recap-novel-pdf-single-retry-after-081323-v1"
SLUG = "r6-recap-novel-pdf-single-retry-after-081323-v1"
GATE = (
    "r6_recap_novel_pdf_single_retry_after_081323_v1="
    "rate_limited_no_body_no_control_unlock"
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_status(path: Path) -> int:
    text = path.read_text(encoding="utf-8", errors="replace").strip()
    try:
        return int(text)
    except ValueError:
        return 0


def parse_headers(path: Path) -> dict[str, str]:
    headers: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        headers[key.strip().lower()] = value.strip()
    return headers


def main() -> int:
    run_root = Path(__file__).resolve().parents[1]
    out_dir = run_root / SLUG
    checks_dir = run_root / "checks"
    command_dir = run_root / "command-output"
    out_dir.mkdir(parents=True, exist_ok=True)
    checks_dir.mkdir(parents=True, exist_ok=True)

    status_path = command_dir / "gov_uscourts_ilnd_316889_1_0_pdf.status"
    headers_path = command_dir / "gov_uscourts_ilnd_316889_1_0_pdf.headers.txt"
    stderr_path = command_dir / "gov_uscourts_ilnd_316889_1_0_pdf.stderr.txt"
    body_path = command_dir / "gov_uscourts_ilnd_316889_1_0_pdf.body"

    status = parse_status(status_path)
    headers = parse_headers(headers_path)
    body_bytes = body_path.read_bytes()
    body_prefix = body_bytes[:256].decode("utf-8", errors="replace")
    body_text = body_bytes.decode("utf-8", errors="replace")
    content_type = headers.get("content-type", "")
    cloudfront_rate_limited = status == 429 or "too many documents" in body_text.lower()
    body_is_pdf = body_bytes.startswith(b"%PDF")
    body_is_html = body_bytes.lstrip().lower().startswith(b"<html") or "text/html" in content_type.lower()

    metrics = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "gate_result": GATE,
        "retried_object": "gov.uscourts.ilnd.316889.1.0.pdf",
        "http_status": status,
        "content_type": content_type,
        "content_length_header": headers.get("content-length", ""),
        "body_bytes": len(body_bytes),
        "body_sha256": sha256_file(body_path),
        "body_is_pdf": body_is_pdf,
        "body_is_html": body_is_html,
        "cloudfront_rate_limited": cloudfront_rate_limited,
        "pdf_acquired": body_is_pdf and status == 200,
        "source_owned_normal_control_document": False,
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

    result = {
        "metrics": metrics,
        "command_output": {
            "status_path": str(status_path),
            "headers_path": str(headers_path),
            "stderr_path": str(stderr_path),
            "body_path": str(body_path),
        },
        "headers": headers,
        "body_prefix": body_prefix,
        "decision": (
            "The retry did not acquire a PDF. It produced an HTTP 429 CloudFront/"
            "CourtListener rate-limit HTML response, so it cannot supply source-owned "
            "normal controls or any R3/R5/R6 source-control unlock."
        ),
    }

    json_path = out_dir / "r6_recap_novel_pdf_single_retry_after_081323_v1.json"
    report_path = out_dir / "r6_recap_novel_pdf_single_retry_after_081323_v1.md"
    csv_path = out_dir / "r6_recap_novel_pdf_single_retry_requests_v1.csv"
    assertions_path = checks_dir / "r6_recap_novel_pdf_single_retry_after_081323_v1_assertions.out"

    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "object_name",
                "http_status",
                "content_type",
                "body_bytes",
                "body_is_pdf",
                "body_is_html",
                "cloudfront_rate_limited",
                "pdf_acquired",
                "source_owned_normal_control_document",
            ],
        )
        writer.writeheader()
        writer.writerow(
            {
                "object_name": metrics["retried_object"],
                "http_status": status,
                "content_type": content_type,
                "body_bytes": len(body_bytes),
                "body_is_pdf": body_is_pdf,
                "body_is_html": body_is_html,
                "cloudfront_rate_limited": cloudfront_rate_limited,
                "pdf_acquired": metrics["pdf_acquired"],
                "source_owned_normal_control_document": False,
            }
        )

    report = f"""# R6 RECAP Novel PDF Single Retry After 081323 v1

Run id: `{RUN_ID}`

Gate result: `{GATE}`

## Scope

Read-only classification of the existing retry command output for
`gov.uscourts.ilnd.316889.1.0.pdf`. This run does not issue a new network
request, does not download or parse a PDF, does not mutate any target intake
root, does not approve RECAP/PACER provenance or `FLIP` rows as controls, and
does not run verifier, canonical merge, AutoQuant, Pre-Bayes, BBN,
CatBoost/path-ranking, execution-tree promotion, or `update_goal`.

## Readback

- HTTP status: `{status}`
- Content type: `{content_type}`
- Body bytes: `{len(body_bytes)}`
- Body is PDF: `{str(body_is_pdf).lower()}`
- Body is HTML: `{str(body_is_html).lower()}`
- CloudFront/CourtListener rate-limited: `{str(cloudfront_rate_limited).lower()}`
- PDF acquired: `{str(metrics["pdf_acquired"]).lower()}`
- Source-owned normal-control document: `false`

## Decision

The retry did not acquire a PDF. The stored body is an HTTP `429` HTML
rate-limit response from the CourtListener/CloudFront route, not a
verifier-native source document. Accepted rows added `0`; R6 owner/export
unlock false; R5 recency unlock false; R3 native-subhour unlock false; valid
required-root unlock false; source/control evidence acquired false; canonical
merge false; selected-data AutoQuant promotion false; downstream promotion
rerun false; strict full objective false; trade usable false;
`promotion_allowed=false`; `update_goal=false`.

## Next

Continue source/control acquisition only. The live unblocker remains an
owner-approved/authenticated FINRA, venue-surveillance, CAT-like,
CME/Cboe/CFE/exchange order-lifecycle export with both positives and matched
normal controls, or explicit same-exhibit `FLIP`-as-control approval before any
verifier, split calibration, canonical merge, selected-data AutoQuant,
Pre-Bayes/BBN, CatBoost/path-ranking, or execution-tree promotion.
"""
    report_path.write_text(report, encoding="utf-8")

    assertions = [
        "PASS r6_recap_novel_pdf_single_retry_after_081323_v1",
        f"gate_result={GATE}",
        f"http_status={status}",
        f"content_type={content_type}",
        f"body_bytes={len(body_bytes)}",
        f"body_is_pdf={str(body_is_pdf).lower()}",
        f"body_is_html={str(body_is_html).lower()}",
        f"cloudfront_rate_limited={str(cloudfront_rate_limited).lower()}",
        f"pdf_acquired={str(metrics['pdf_acquired']).lower()}",
        "source_owned_normal_control_document=false",
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
    assertions_path.write_text("\n".join(assertions) + "\n", encoding="utf-8")
    print("\n".join(assertions))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
