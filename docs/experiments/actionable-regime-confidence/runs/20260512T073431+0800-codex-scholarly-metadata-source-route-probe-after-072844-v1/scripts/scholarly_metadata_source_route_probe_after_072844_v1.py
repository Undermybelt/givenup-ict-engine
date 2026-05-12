#!/usr/bin/env python3
"""Scholarly metadata source/control route probe for Board B.

This probe is source/control acquisition only. It queries public scholarly
metadata APIs for exact R3/R5/R6 route terms and emits a fail-closed packet
unless required source/control exports are actually visible.
"""

from __future__ import annotations

import csv
import datetime as dt
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


RUN_ID = "20260512T073431+0800-codex-scholarly-metadata-source-route-probe-after-072844-v1"
RUN_ROOT = Path("docs/experiments/actionable-regime-confidence/runs") / RUN_ID
PACKET_DIR = RUN_ROOT / "scholarly-metadata-source-route-probe-after-072844-v1"
RAW_DIR = RUN_ROOT / "command-output"
CHECK_DIR = RUN_ROOT / "checks"

QUERIES = [
    ("mainregimev2_exact", '"MainRegimeV2"', "r5_r3_exact"),
    ("mainregimev2_crisis_exact", '"MainRegimeV2" "Crisis"', "r3_exact"),
    ("native_subhour_rows_exact", '"native_subhour_source_label_rows"', "r3_exact"),
    ("stock_regimes_extension_exact", '"stock_market_regimes_2026_extension"', "r5_exact"),
    ("positive_rows_exact", '"direct_manipulation_positive_rows"', "r6_filename"),
    ("matched_controls_exact", '"direct_manipulation_matched_controls"', "r6_filename"),
    ("provenance_exact", '"direct_manipulation_provenance"', "r6_filename"),
    ("oystacher_3red_exact", '"Oystacher" "3Red Trading"', "r6_owner"),
    ("oystacher_order_lifecycle", '"Oystacher" "order lifecycle"', "r6_owner"),
    ("spoofing_matched_controls", '"spoofing" "matched controls" "futures"', "r6_context"),
]

REQUIRED_FILENAMES = [
    "direct_manipulation_positive_rows",
    "direct_manipulation_matched_controls",
    "direct_manipulation_provenance",
    "native_subhour_source_label_rows",
    "stock_market_regimes_2026_extension",
]
OWNER_TERMS = ["Oystacher", "3Red Trading"]
MAINREGIME_TERMS = ["MainRegimeV2"]
R3_NATIVE_TERMS = ["native_subhour_source_label_rows", "native subhour source label"]
CRISIS_CONTEXT_TERMS = ["Crisis"]
R5_TERMS = ["stock_market_regimes_2026_extension", "stock market regimes 2026"]
R6_TERMS = ["direct_manipulation_positive_rows", "direct_manipulation_matched_controls", "direct_manipulation_provenance"]


def fetch(url: str, *, headers: dict[str, str] | None = None, timeout: int = 35) -> tuple[int | None, bytes, str | None]:
    req_headers = {
        "User-Agent": "ict-engine-board-b-source-route-probe/1.0 (metadata route audit)",
        "Accept": "application/json,text/plain;q=0.8,*/*;q=0.5",
    }
    if headers:
        req_headers.update(headers)
    req = urllib.request.Request(url, headers=req_headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, resp.read(), None
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read(), str(exc)
    except Exception as exc:
        return None, b"", repr(exc)


def write_raw(name: str, suffix: str, payload: bytes | str) -> None:
    path = RAW_DIR / f"{name}.{suffix}"
    if isinstance(payload, bytes):
        path.write_bytes(payload)
    else:
        path.write_text(payload, encoding="utf-8")


def norm(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, (str, int, float, bool)):
        return str(value)
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def text_blob(records: list[dict[str, object]]) -> str:
    return "\n".join(norm(record) for record in records).lower()


def has_any(records: list[dict[str, object]], terms: list[str]) -> bool:
    blob = text_blob(records)
    return any(term.lower() in blob for term in terms)


def openalex_records(payload: bytes) -> list[dict[str, object]]:
    obj = json.loads(payload.decode("utf-8"))
    records: list[dict[str, object]] = []
    for item in (obj.get("results") or [])[:10]:
        records.append(
            {
                "id": item.get("id"),
                "doi": item.get("doi"),
                "title": item.get("title") or item.get("display_name"),
                "publication_year": item.get("publication_year"),
                "type": item.get("type"),
                "cited_by_count": item.get("cited_by_count"),
                "primary_location": item.get("primary_location"),
            }
        )
    return records


def crossref_records(payload: bytes) -> list[dict[str, object]]:
    obj = json.loads(payload.decode("utf-8"))
    records: list[dict[str, object]] = []
    for item in ((obj.get("message") or {}).get("items") or [])[:10]:
        titles = item.get("title") or []
        records.append(
            {
                "doi": item.get("DOI"),
                "title": titles[0] if titles else "",
                "container_title": (item.get("container-title") or [""])[0],
                "publisher": item.get("publisher"),
                "type": item.get("type"),
                "published": item.get("published-print") or item.get("published-online") or item.get("created"),
                "url": item.get("URL"),
            }
        )
    return records


def semanticscholar_records(payload: bytes) -> list[dict[str, object]]:
    obj = json.loads(payload.decode("utf-8"))
    records: list[dict[str, object]] = []
    for item in (obj.get("data") or [])[:10]:
        records.append(
            {
                "paperId": item.get("paperId"),
                "title": item.get("title"),
                "year": item.get("year"),
                "venue": item.get("venue"),
                "url": item.get("url"),
                "externalIds": item.get("externalIds"),
            }
        )
    return records


def europepmc_records(payload: bytes) -> list[dict[str, object]]:
    obj = json.loads(payload.decode("utf-8"))
    records: list[dict[str, object]] = []
    for item in (((obj.get("resultList") or {}).get("result")) or [])[:10]:
        records.append(
            {
                "id": item.get("id"),
                "doi": item.get("doi"),
                "title": item.get("title"),
                "journal": item.get("journalTitle"),
                "pubYear": item.get("pubYear"),
                "source": item.get("source"),
                "pmcid": item.get("pmcid"),
            }
        )
    return records


def provider_requests(slug: str, query: str) -> list[dict[str, object]]:
    encoded = urllib.parse.quote_plus(query)
    return [
        {
            "provider": "openalex",
            "url": f"https://api.openalex.org/works?search={encoded}&per-page=10",
            "parser": openalex_records,
        },
        {
            "provider": "crossref",
            "url": f"https://api.crossref.org/works?query={encoded}&rows=10",
            "parser": crossref_records,
        },
        {
            "provider": "semantic_scholar",
            "url": "https://api.semanticscholar.org/graph/v1/paper/search?"
            f"query={encoded}&limit=10&fields=title,year,venue,url,externalIds",
            "parser": semanticscholar_records,
        },
        {
            "provider": "europe_pmc",
            "url": "https://www.ebi.ac.uk/europepmc/webservices/rest/search?"
            f"query={encoded}&format=json&pageSize=10",
            "parser": europepmc_records,
        },
    ]


def exact_required_hit(records: list[dict[str, object]]) -> bool:
    blob = text_blob(records)
    return any(term.lower() in blob for term in REQUIRED_FILENAMES)


def main() -> int:
    PACKET_DIR.mkdir(parents=True, exist_ok=True)
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)
    (RAW_DIR / "run_id.txt").write_text(RUN_ID + "\n", encoding="utf-8")
    (RAW_DIR / "run_root.txt").write_text(str(RUN_ROOT) + "\n", encoding="utf-8")

    rows: list[dict[str, object]] = []
    request_count = 0
    failed_count = 0
    required_filename_hits = 0
    owner_hits = 0
    mainregime_hits = 0
    r3_native_hits = 0
    crisis_context_hits = 0
    r5_hits = 0
    r6_hits = 0
    top_rows_scanned = 0
    accepted_unlocks = 0

    for slug, query, route in QUERIES:
        for request in provider_requests(slug, query):
            provider = str(request["provider"])
            raw_name = f"{provider}_{slug}"
            url = str(request["url"])
            parser = request["parser"]
            status, payload, error = fetch(url)
            request_count += 1
            write_raw(raw_name, "url", url + "\n")
            write_raw(raw_name, "status", "" if status is None else str(status))
            if payload:
                write_raw(raw_name, "json", payload)
            if error:
                write_raw(raw_name, "error", error + "\n")
            failed = status is None or status >= 400
            failed_count += int(failed)
            records: list[dict[str, object]] = []
            parse_error = None
            if not failed and payload:
                try:
                    records = parser(payload)
                except Exception as exc:
                    parse_error = repr(exc)
                    failed_count += 1
                    write_raw(raw_name, "parse_error", parse_error + "\n")

            required_hit = exact_required_hit(records)
            owner_hit = has_any(records, OWNER_TERMS)
            mainregime_hit = has_any(records, MAINREGIME_TERMS)
            r3_native_hit = has_any(records, R3_NATIVE_TERMS)
            crisis_context_hit = has_any(records, CRISIS_CONTEXT_TERMS)
            r5_hit = has_any(records, R5_TERMS)
            r6_hit = has_any(records, R6_TERMS)
            top_rows_scanned += len(records)
            required_filename_hits += int(required_hit)
            owner_hits += int(owner_hit)
            mainregime_hits += int(mainregime_hit)
            r3_native_hits += int(r3_native_hit)
            crisis_context_hits += int(crisis_context_hit)
            r5_hits += int(r5_hit)
            r6_hits += int(r6_hit)

            # Metadata hits are not accepted as rows. This stays zero unless a
            # future parser sees all required source/export files in one source.
            accepted = bool(required_hit and owner_hit and r6_hit and not failed)
            accepted_unlocks += int(accepted)
            rows.append(
                {
                    "provider": provider,
                    "slug": slug,
                    "route": route,
                    "query": query,
                    "status": status,
                    "failed": failed,
                    "parse_error": parse_error or "",
                    "records_scanned": len(records),
                    "required_filename_hit": required_hit,
                    "owner_hit": owner_hit,
                    "mainregime_hit": mainregime_hit,
                    "r3_native_hit": r3_native_hit,
                    "crisis_context_hit": crisis_context_hit,
                    "r5_hit": r5_hit,
                    "r6_hit": r6_hit,
                    "accepted_unlock": accepted,
                }
            )
            time.sleep(0.25)

    gate = "scholarly_metadata_source_route_probe_after_072844_v1=no_required_source_export_no_unlock"
    if accepted_unlocks:
        gate = "scholarly_metadata_source_route_probe_after_072844_v1=manual_review_required_metadata_mentions_required_terms"

    summary = {
        "run_id": RUN_ID,
        "created_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "gate": gate,
        "request_count": request_count,
        "failed_request_count": failed_count,
        "top_rows_scanned": top_rows_scanned,
        "required_filename_hits": required_filename_hits,
        "owner_hits": owner_hits,
        "mainregime_hits": mainregime_hits,
        "r3_native_subhour_hits": r3_native_hits,
        "crisis_context_hits": crisis_context_hits,
        "r5_recency_hits": r5_hits,
        "r6_required_file_hits": r6_hits,
        "accepted_rows_added": 0,
        "accepted_unlocks": accepted_unlocks,
        "r6_owner_export_unlock": False,
        "r5_recency_unlock": False,
        "r3_native_subhour_unlock": False,
        "valid_required_root_unlock": False,
        "source_control_evidence_acquired": False,
        "canonical_merge": False,
        "downstream_promotion_rerun": False,
        "strict_full_objective": False,
        "trade_usable": False,
        "promotion_allowed": False,
        "update_goal": False,
        "notes": [
            "Queried OpenAlex, Crossref, Semantic Scholar, and Europe PMC metadata APIs.",
            "Metadata records are route-disposition evidence only, not row-level owner/export evidence.",
            "No target roots were mutated and no downstream promotion was run.",
        ],
    }

    csv_path = PACKET_DIR / "scholarly_metadata_source_route_probe_after_072844_v1.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()) if rows else ["provider"])
        writer.writeheader()
        writer.writerows(rows)

    json_path = PACKET_DIR / "scholarly_metadata_source_route_probe_after_072844_v1.json"
    json_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    report = [
        "# Scholarly Metadata Source Route Probe After 072844 v1",
        "",
        f"Run root: `{RUN_ROOT}`",
        "",
        "## Gate",
        "",
        f"- `{gate}`",
        "- `promotion_allowed=false`",
        "- `update_goal=false`",
        "",
        "## Readback",
        "",
        f"- Requests sent: `{request_count}`",
        f"- Failed requests or parse failures: `{failed_count}`",
        f"- Top metadata rows scanned: `{top_rows_scanned}`",
        f"- Required filename hits: `{required_filename_hits}`",
        f"- Owner hits: `{owner_hits}`",
        f"- `MainRegimeV2` hits: `{mainregime_hits}`",
        f"- R3 native-subhour hits: `{r3_native_hits}`",
        f"- Crisis-context metadata hits: `{crisis_context_hits}`",
        f"- R5 recency hits: `{r5_hits}`",
        f"- R6 required-file hits: `{r6_hits}`",
        "- Accepted rows added: `0`",
        "",
        "## Decision",
        "",
        "This is public scholarly metadata route-disposition evidence only. It does not supply verifier-native R6 owner/export positives, matched normal controls, owner/export provenance, source-owned post-2026-01-30 R5 `MainRegimeV2` rows, or verifier-native Crisis-capable R3 labels.",
        "",
        "No direct verifier, split calibration, canonical merge, selected-data AutoQuant, filter / Pre-Bayes, BBN, CatBoost / path-ranking, or execution-tree promotion was run.",
        "",
    ]
    report_path = PACKET_DIR / "scholarly_metadata_source_route_probe_after_072844_v1.md"
    report_path.write_text("\n".join(report), encoding="utf-8")

    assertion_lines = [
        f"gate={gate}",
        "accepted_rows_added=0",
        "r6_owner_export_unlock=false",
        "r5_recency_unlock=false",
        "r3_native_subhour_unlock=false",
        "valid_required_root_unlock=false",
        "source_control_evidence_acquired=false",
        "canonical_merge=false",
        "downstream_promotion_rerun=false",
        "promotion_allowed=false",
        "update_goal=false",
    ]
    assertions = CHECK_DIR / "scholarly_metadata_source_route_probe_after_072844_v1_assertions.out"
    assertions.write_text("\n".join(assertion_lines) + "\n", encoding="utf-8")

    return 0 if accepted_unlocks == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
