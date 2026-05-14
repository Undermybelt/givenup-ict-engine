#!/usr/bin/env python3
"""Public repository source/control route probe for Board A.

This script intentionally stays source/control-only. It records exact public
repository search results and emits a fail-closed packet unless the required
R6/R5/R3 source contracts are actually present.
"""

from __future__ import annotations

import csv
import datetime as dt
import html
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


RUN_ROOT = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260512T072844+0800-codex-public-repository-source-route-probe-after-072412-v1"
)
PACKET_DIR = RUN_ROOT / "public-repository-source-route-probe-after-072412-v1"
RAW_DIR = RUN_ROOT / "command-output"
CHECK_DIR = RUN_ROOT / "checks"

QUERIES = [
    ("mainregimev2_exact", '"MainRegimeV2"', "r5_r3_exact"),
    ("mainregimev2_crisis_exact", '"MainRegimeV2" "Crisis"', "r3_exact"),
    (
        "stock_market_regimes_extension_exact",
        '"stock_market_regimes_2026_extension"',
        "r5_exact",
    ),
    (
        "stock_market_regimes_2026_exact",
        '"stock market regimes 2026"',
        "r5_context",
    ),
    (
        "native_subhour_rows_exact",
        '"native_subhour_source_label_rows"',
        "r3_exact",
    ),
    (
        "native_subhour_label_exact",
        '"native subhour source label"',
        "r3_exact",
    ),
    (
        "positive_filename_exact",
        '"direct_manipulation_positive_rows"',
        "required_filename",
    ),
    (
        "controls_filename_exact",
        '"direct_manipulation_matched_controls"',
        "required_filename",
    ),
    (
        "provenance_filename_exact",
        '"direct_manipulation_provenance"',
        "required_filename",
    ),
    ("oystacher_exact", '"Oystacher"', "r6_owner_export_exact"),
    ("three_red_exact", '"3Red Trading"', "r6_owner_export_exact"),
    (
        "oystacher_3red_lifecycle_exact",
        '"Oystacher" "3Red Trading" "order lifecycle"',
        "r6_owner_export_exact",
    ),
    (
        "futures_order_lifecycle_spoofing_exact",
        '"futures order lifecycle spoofing"',
        "r6_context",
    ),
]

REQUIRED_FILENAMES = [
    "direct_manipulation_positive_rows",
    "direct_manipulation_matched_controls",
    "direct_manipulation_provenance",
]
OWNER_TERMS = ["Oystacher", "3Red Trading"]
MAINREGIME_TERMS = ["MainRegimeV2"]
R3_TERMS = ["native_subhour_source_label_rows", "native subhour source label"]
R5_TERMS = ["stock_market_regimes_2026_extension", "stock market regimes 2026"]
ORDER_CONTEXT_TERMS = ["order lifecycle", "order book", "Level 4", "L2 depth"]


def fetch(
    url: str,
    *,
    method: str = "GET",
    body: bytes | None = None,
    headers: dict[str, str] | None = None,
    timeout: int = 30,
) -> tuple[int | None, bytes, str | None]:
    req_headers = {
        "User-Agent": "ict-engine-board-a-source-route-probe/1.0",
        "Accept": "application/json,text/html;q=0.8,*/*;q=0.5",
    }
    if headers:
        req_headers.update(headers)
    req = urllib.request.Request(url, data=body, method=method, headers=req_headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, resp.read(), None
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read(), str(exc)
    except Exception as exc:  # network evidence belongs in the artifact
        return None, b"", repr(exc)


def write_raw(name: str, suffix: str, payload: bytes | str) -> None:
    path = RAW_DIR / f"{name}.{suffix}"
    if isinstance(payload, str):
        path.write_text(payload, encoding="utf-8")
    else:
        path.write_bytes(payload)


def normalize_text(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, (str, int, float, bool)):
        return str(value)
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def records_from_datacite(payload: bytes) -> list[dict[str, object]]:
    obj = json.loads(payload.decode("utf-8"))
    records = []
    for item in obj.get("data", [])[:10]:
        attrs = item.get("attributes", {})
        titles = attrs.get("titles") or []
        records.append(
            {
                "id": item.get("id"),
                "title": (titles[0] or {}).get("title") if titles else "",
                "publisher": attrs.get("publisher"),
                "publication_year": attrs.get("publicationYear"),
                "resource_type": attrs.get("types", {}).get("resourceTypeGeneral"),
                "doi": attrs.get("doi"),
                "url": attrs.get("url"),
                "description": " ".join(
                    d.get("description", "") for d in (attrs.get("descriptions") or [])[:3]
                ),
            }
        )
    return records


def records_from_osf(payload: bytes) -> list[dict[str, object]]:
    obj = json.loads(payload.decode("utf-8"))
    records = []
    for item in obj.get("data", [])[:10]:
        if not isinstance(item, dict):
            continue
        attrs = item.get("attributes", {})
        links = item.get("links", {})
        records.append(
            {
                "id": item.get("id"),
                "title": attrs.get("title", ""),
                "description": attrs.get("description", ""),
                "category": attrs.get("category"),
                "date_created": attrs.get("date_created"),
                "url": links.get("html") or links.get("self"),
            }
        )
    return records


def records_from_figshare(payload: bytes) -> list[dict[str, object]]:
    obj = json.loads(payload.decode("utf-8"))
    records = []
    if not isinstance(obj, list):
        return records
    for item in obj[:10]:
        records.append(
            {
                "id": item.get("id"),
                "title": item.get("title", ""),
                "doi": item.get("doi"),
                "url": item.get("url") or item.get("published_url"),
                "defined_type": item.get("defined_type"),
                "published_date": item.get("published_date"),
            }
        )
    return records


def records_from_mendeley_html(payload: bytes) -> list[dict[str, object]]:
    text = payload.decode("utf-8", errors="ignore")
    title_match = re.search(r"<title>(.*?)</title>", text, flags=re.I | re.S)
    return [
        {
            "title": html.unescape(title_match.group(1)).strip() if title_match else "",
            "static_html_bytes": len(payload),
            "note": "Mendeley public web HTML was captured; authenticated API was not used.",
        }
    ]


def term_hit(records: list[dict[str, object]], terms: list[str]) -> bool:
    blob = "\n".join(normalize_text(record) for record in records).lower()
    return any(term.lower() in blob for term in terms)


def provider_requests(slug: str, query: str) -> list[dict[str, object]]:
    encoded = urllib.parse.quote_plus(query)
    fig_body = json.dumps({"search_for": query, "page_size": 10}).encode("utf-8")
    return [
        {
            "surface": "datacite",
            "url": f"https://api.datacite.org/dois?query={encoded}&page%5Bsize%5D=10",
            "method": "GET",
            "body": None,
            "headers": {},
            "parser": records_from_datacite,
            "raw_suffix": "json",
        },
        {
            "surface": "osf",
            "url": f"https://api.osf.io/v2/search/?q={encoded}&page%5Bsize%5D=10",
            "method": "GET",
            "body": None,
            "headers": {},
            "parser": records_from_osf,
            "raw_suffix": "json",
        },
        {
            "surface": "figshare",
            "url": "https://api.figshare.com/v2/articles/search",
            "method": "POST",
            "body": fig_body,
            "headers": {"Content-Type": "application/json"},
            "parser": records_from_figshare,
            "raw_suffix": "json",
        },
        {
            "surface": "mendeley_public_web",
            "url": f"https://data.mendeley.com/research-data/?search={encoded}",
            "method": "GET",
            "body": None,
            "headers": {"Accept": "text/html,*/*;q=0.5"},
            "parser": records_from_mendeley_html,
            "raw_suffix": "html",
        },
    ]


def query_all() -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    rows: list[dict[str, object]] = []
    context_hits: list[dict[str, object]] = []
    for slug, query, route in QUERIES:
        for req in provider_requests(slug, query):
            name = f"{req['surface']}_{slug}"
            status, payload, error = fetch(
                str(req["url"]),
                method=str(req["method"]),
                body=req["body"],  # type: ignore[arg-type]
                headers=req["headers"],  # type: ignore[arg-type]
            )
            write_raw(name, "url", str(req["url"]))
            write_raw(name, "status", str(status))
            write_raw(name, "error", error or "")
            write_raw(name, str(req["raw_suffix"]), payload)

            records: list[dict[str, object]] = []
            parse_error = None
            if payload and status and 200 <= status < 300:
                try:
                    records = req["parser"](payload)  # type: ignore[operator]
                except Exception as exc:
                    parse_error = repr(exc)

            required_hit = term_hit(records, REQUIRED_FILENAMES)
            owner_hit = term_hit(records, OWNER_TERMS)
            mainregime_hit = term_hit(records, MAINREGIME_TERMS)
            r3_hit = term_hit(records, R3_TERMS)
            r5_hit = term_hit(records, R5_TERMS)
            order_context_hit = term_hit(records, ORDER_CONTEXT_TERMS)

            top_titles = [
                normalize_text(record.get("title", "")).replace("\n", " ").strip()
                for record in records[:3]
            ]
            row = {
                "surface": req["surface"],
                "slug": slug,
                "route": route,
                "query": query,
                "method": req["method"],
                "status": status,
                "error": error or "",
                "parse_error": parse_error or "",
                "record_count_top10": len(records),
                "required_filename_hit": required_hit,
                "owner_hit": owner_hit,
                "mainregimev2_hit": mainregime_hit,
                "r3_native_subhour_hit": r3_hit,
                "r5_recency_hit": r5_hit,
                "order_context_hit": order_context_hit,
                "top_titles": " | ".join(t for t in top_titles if t),
                "url": req["url"],
            }
            rows.append(row)

            if order_context_hit and not (required_hit or owner_hit or mainregime_hit):
                context_hits.extend(
                    {
                        "surface": req["surface"],
                        "slug": slug,
                        "title": record.get("title", ""),
                        "url": record.get("url", ""),
                    }
                    for record in records[:10]
                    if term_hit([record], ORDER_CONTEXT_TERMS)
                )

            time.sleep(0.15)
    return rows, context_hits


def main() -> int:
    for directory in (PACKET_DIR, RAW_DIR, CHECK_DIR):
        directory.mkdir(parents=True, exist_ok=True)

    rows, context_hits = query_all()
    failed = [row for row in rows if row["status"] is None or row["error"] or row["parse_error"]]
    required_hits = [row for row in rows if row["required_filename_hit"]]
    owner_hits = [row for row in rows if row["owner_hit"]]
    mainregime_hits = [row for row in rows if row["mainregimev2_hit"]]
    r3_hits = [row for row in rows if row["r3_native_subhour_hit"]]
    r5_hits = [row for row in rows if row["r5_recency_hit"]]

    # The public Mendeley web page may echo the search term in static HTML. Do
    # not count it as a row-level hit unless an authenticated/API record parser
    # is available, which this sandbox does not have.
    promoting_surfaces = {"datacite", "osf", "figshare"}
    required_hits = [row for row in required_hits if row["surface"] in promoting_surfaces]
    owner_hits = [row for row in owner_hits if row["surface"] in promoting_surfaces]
    mainregime_hits = [row for row in mainregime_hits if row["surface"] in promoting_surfaces]
    r3_hits = [row for row in r3_hits if row["surface"] in promoting_surfaces]
    r5_hits = [row for row in r5_hits if row["surface"] in promoting_surfaces]

    decision = {
        "gate": "public_repository_source_route_probe_after_072412_v1",
        "gate_result": "exact_required_queries_no_promoting_hits_no_unlock",
        "accepted_rows_added": 0,
        "r6_owner_export_unlock": False,
        "r5_recency_unlock": False,
        "r3_native_subhour_unlock": False,
        "valid_required_root_unlock": False,
        "source_control_evidence_acquired": False,
        "canonical_merge": False,
        "downstream_promotion_rerun": False,
        "strict_full_objective": False,
        "trade_usable": False,
        "update_goal": False,
        "notes": [
            "DataCite, OSF, and Figshare public API searches did not expose required R6 owner/export filenames, MainRegimeV2 source rows, or native-subhour labels.",
            "Mendeley Data public web pages were captured, but the Mendeley API returned unauthorized without OAuth; no authenticated query or credential use was attempted.",
            "No target root was mutated and no downstream verifier/calibration/promotion step is authorized by this packet.",
        ],
    }

    summary = {
        "created_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "query_count": len(QUERIES),
        "surface_count": 4,
        "request_count": len(rows),
        "failed_request_count": len(failed),
        "required_filename_hits": len(required_hits),
        "owner_hits": len(owner_hits),
        "mainregimev2_hits": len(mainregime_hits),
        "r3_native_subhour_hits": len(r3_hits),
        "r5_recency_hits": len(r5_hits),
        "context_only_hits": len(context_hits),
    }

    packet = {
        "run_root": str(RUN_ROOT.resolve()),
        "summary": summary,
        "decision": decision,
        "queries": [
            {"slug": slug, "query": query, "route": route}
            for slug, query, route in QUERIES
        ],
        "rows": rows,
        "context_hits": context_hits[:50],
    }

    json_path = PACKET_DIR / "public_repository_source_route_probe_after_072412_v1.json"
    csv_path = PACKET_DIR / "public_repository_source_route_probe_after_072412_v1.csv"
    md_path = PACKET_DIR / "public_repository_source_route_probe_after_072412_v1.md"
    assertions_path = CHECK_DIR / "public_repository_source_route_probe_after_072412_v1_assertions.out"

    json_path.write_text(json.dumps(packet, indent=2, ensure_ascii=False), encoding="utf-8")
    with csv_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    md_path.write_text(
        "\n".join(
            [
                "# Public Repository Source Route Probe After 072412 v1",
                "",
                "## Decision",
                "",
                f"- Gate result: `{decision['gate_result']}`",
                "- Accepted rows added: `0`",
                "- Valid required-root unlock: `false`",
                "- Source/control evidence acquired: `false`",
                "- Canonical merge: `false`",
                "- Downstream promotion rerun: `false`",
                "- `update_goal`: `false`",
                "",
                "## Public Surfaces Queried",
                "",
                "- DataCite REST API",
                "- OSF search API",
                "- Figshare public articles search API",
                "- Mendeley Data public web search page; unauthenticated Mendeley API access was not used for promotion",
                "",
                "## Summary",
                "",
                f"- Queries: `{summary['query_count']}`",
                f"- Requests: `{summary['request_count']}`",
                f"- Failed/blocked requests: `{summary['failed_request_count']}`",
                f"- Required filename hits: `{summary['required_filename_hits']}`",
                f"- Owner hits: `{summary['owner_hits']}`",
                f"- `MainRegimeV2` hits: `{summary['mainregimev2_hits']}`",
                f"- R3 native-subhour hits: `{summary['r3_native_subhour_hits']}`",
                f"- R5 recency hits: `{summary['r5_recency_hits']}`",
                f"- Context-only order-book hits: `{summary['context_only_hits']}`",
                "",
                "## Non-Promotion Reason",
                "",
                "The public searches did not supply verifier-native R6 owner/export positives, matched controls, provenance package, source-owned post-`2026-01-30` R5 `MainRegimeV2` rows, or verifier-native Crisis-capable R3 labels. Mendeley API access requires OAuth and was not used.",
                "",
                "## Next",
                "",
                "Continue only from explicit source/control approval, verifier-native R6 owner-export rows with valid controls, source-owned post-`2026-01-30` R5 rows matching the source-panel schema, verifier-native Crisis-capable R3 `MainRegimeV2` labels, or a genuinely new accepted cross-timeframe `MainRegimeV2` source export.",
                "",
            ]
        ),
        encoding="utf-8",
    )

    assertions = {
        "gate_result": decision["gate_result"],
        "request_count": summary["request_count"],
        "failed_request_count": summary["failed_request_count"],
        "required_filename_hits": summary["required_filename_hits"],
        "owner_hits": summary["owner_hits"],
        "mainregimev2_hits": summary["mainregimev2_hits"],
        "r3_native_subhour_hits": summary["r3_native_subhour_hits"],
        "r5_recency_hits": summary["r5_recency_hits"],
        "valid_required_root_unlock": decision["valid_required_root_unlock"],
        "source_control_evidence_acquired": decision["source_control_evidence_acquired"],
        "r6_owner_export_unlock": decision["r6_owner_export_unlock"],
        "r5_recency_unlock": decision["r5_recency_unlock"],
        "r3_native_subhour_unlock": decision["r3_native_subhour_unlock"],
        "canonical_merge": decision["canonical_merge"],
        "downstream_promotion_rerun": decision["downstream_promotion_rerun"],
        "strict_full_objective": decision["strict_full_objective"],
        "trade_usable": decision["trade_usable"],
        "update_goal": decision["update_goal"],
    }
    assertions_path.write_text(
        "\n".join(f"{key}={value}" for key, value in assertions.items()) + "\n",
        encoding="utf-8",
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())
