#!/usr/bin/env python3
"""Probe public paper indexes for Board A required source/control exports.

This is source-route metadata only. It does not download datasets, infer labels,
mutate target roots, or authorize downstream promotion.
"""

from __future__ import annotations

import csv
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


RUN_ROOT = Path(__file__).resolve().parents[1]
OUT_ROOT = RUN_ROOT / "openalex-semantic-pwc-source-route-after-080700-v1"
CHECK_ROOT = RUN_ROOT / "checks"
COMMAND_ROOT = RUN_ROOT / "command-output"

QUERIES = [
    ("mainregimev2_exact", '"MainRegimeV2"'),
    ("stock_regimes_extension_exact", '"stock_market_regimes_2026_extension"'),
    ("native_subhour_rows_exact", '"native_subhour_source_label_rows"'),
    ("positive_rows_exact", '"direct_manipulation_positive_rows"'),
    ("matched_controls_exact", '"direct_manipulation_matched_controls"'),
    ("oystacher_3red_controls", '"Oystacher" "3Red Trading" "matched controls"'),
    ("bull_bear_sideways_crisis", '"market regime" "Bull" "Bear" "Sideways" "Crisis"'),
    ("lob_spoofing_controls", '"limit order book" "spoofing" "matched controls"'),
]

REQUIRED_PATTERNS = [
    re.compile(r"MainRegimeV2", re.I),
    re.compile(r"stock_market_regimes_2026_extension", re.I),
    re.compile(r"native_subhour_source_label_rows", re.I),
    re.compile(r"direct_manipulation_positive_rows", re.I),
    re.compile(r"direct_manipulation_matched_controls", re.I),
]

R3_PATTERNS = [
    re.compile(r"native_subhour", re.I),
    re.compile(r"crisis", re.I),
    re.compile(r"MainRegimeV2", re.I),
]

R5_PATTERNS = [
    re.compile(r"2026", re.I),
    re.compile(r"stock.?market.?regime", re.I),
    re.compile(r"MainRegimeV2", re.I),
]

R6_PATTERNS = [
    re.compile(r"Oystacher|3Red|spoof|layering", re.I),
    re.compile(r"matched.?control|normal.?control|order.?lifecycle", re.I),
]

BROAD_PATTERNS = [
    re.compile(r"market.?regime|bull|bear|sideways|crisis", re.I),
    re.compile(r"spoof|layering|limit.?order.?book|wash.?trad", re.I),
]


def fetch_json(url: str) -> tuple[int | None, Any, str | None]:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "ict-engine-board-a-source-route-probe/1.0",
            "Accept": "application/json,text/plain,*/*",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            raw = resp.read(1_000_000)
            text = raw.decode("utf-8", errors="replace")
            try:
                return resp.status, json.loads(text), None
            except json.JSONDecodeError:
                return resp.status, {"raw_text": text[:100_000]}, "json_parse_failed"
    except Exception as exc:  # noqa: BLE001 - record probe disposition, do not fail hard.
        return None, {"error": repr(exc)}, repr(exc)


def normalize_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    try:
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    except TypeError:
        return str(value)


def first_items(surface: str, payload: Any) -> list[dict[str, Any]]:
    if not isinstance(payload, dict):
        return []
    if surface == "openalex":
        raw = payload.get("results") or []
        return [
            {
                "title": item.get("title") or item.get("display_name") or "",
                "url": item.get("id") or item.get("doi") or "",
                "year": item.get("publication_year") or "",
                "raw": item,
            }
            for item in raw[:8]
            if isinstance(item, dict)
        ]
    if surface == "semantic_scholar":
        raw = payload.get("data") or []
        return [
            {
                "title": item.get("title") or "",
                "url": item.get("url") or "",
                "year": item.get("year") or "",
                "raw": item,
            }
            for item in raw[:8]
            if isinstance(item, dict)
        ]
    if surface == "paperswithcode":
        raw = payload.get("results") or []
        return [
            {
                "title": item.get("title") or item.get("name") or "",
                "url": item.get("url") or item.get("paper_url") or "",
                "year": item.get("published") or item.get("year") or "",
                "raw": item,
            }
            for item in raw[:8]
            if isinstance(item, dict)
        ]
    return []


def all_match(patterns: list[re.Pattern[str]], text: str) -> bool:
    return all(pattern.search(text) for pattern in patterns)


def any_match(patterns: list[re.Pattern[str]], text: str) -> bool:
    return any(pattern.search(text) for pattern in patterns)


def score_candidate(surface: str, query_id: str, item: dict[str, Any]) -> dict[str, Any]:
    text = normalize_text(item)
    required = any_match(REQUIRED_PATTERNS, text)
    r3 = all_match(R3_PATTERNS, text)
    r5 = all_match(R5_PATTERNS, text)
    r6 = all_match(R6_PATTERNS, text)
    broad = any_match(BROAD_PATTERNS, text)
    return {
        "surface": surface,
        "query_id": query_id,
        "title": item.get("title", ""),
        "url": item.get("url", ""),
        "year": item.get("year", ""),
        "required_filename_or_token_hit": required,
        "r3_native_subhour_crisis_hit": r3,
        "r5_post_cutoff_route_hit": r5,
        "r6_owner_control_route_hit": r6,
        "broad_context_hit": broad,
    }


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def main() -> int:
    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    CHECK_ROOT.mkdir(parents=True, exist_ok=True)
    COMMAND_ROOT.mkdir(parents=True, exist_ok=True)

    surfaces = {
        "openalex": "https://api.openalex.org/works?per-page=8&search={query}",
        "semantic_scholar": (
            "https://api.semanticscholar.org/graph/v1/paper/search"
            "?limit=8&fields=title,year,url,abstract,externalIds&query={query}"
        ),
        "paperswithcode": "https://paperswithcode.com/api/v1/search/?q={query}",
    }

    requests: list[dict[str, Any]] = []
    candidates: list[dict[str, Any]] = []

    for surface, template in surfaces.items():
        for query_id, query in QUERIES:
            encoded = urllib.parse.quote(query)
            url = template.format(query=encoded)
            status, payload, error = fetch_json(url)
            slug = f"{surface}_{query_id}"
            write_json(COMMAND_ROOT / f"{slug}.json", payload)
            (COMMAND_ROOT / f"{slug}.url").write_text(url + "\n", encoding="utf-8")
            requests.append(
                {
                    "surface": surface,
                    "query_id": query_id,
                    "query": query,
                    "url": url,
                    "status": status,
                    "error": error or "",
                }
            )
            for item in first_items(surface, payload):
                candidates.append(score_candidate(surface, query_id, item))
            time.sleep(0.25)

    accepted_rows_added = 0
    required_hits = sum(1 for row in candidates if row["required_filename_or_token_hit"])
    exact_mainregimev2_hits = sum(
        1 for row in candidates if re.search(r"MainRegimeV2", normalize_text(row), re.I)
    )
    r3_hits = sum(1 for row in candidates if row["r3_native_subhour_crisis_hit"])
    r5_hits = sum(1 for row in candidates if row["r5_post_cutoff_route_hit"])
    r6_hits = sum(1 for row in candidates if row["r6_owner_control_route_hit"])
    broad_hits = sum(1 for row in candidates if row["broad_context_hit"])
    failed_or_parse_failed = sum(1 for row in requests if row["status"] is None or row["error"])

    gate_result = "openalex_semantic_pwc_source_route_after_080700_v1=no_required_source_control_unlock"
    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "gate_result": gate_result,
        "requests_sent": len(requests),
        "failed_or_parse_failed": failed_or_parse_failed,
        "candidate_rows": len(candidates),
        "required_filename_or_token_hits": required_hits,
        "exact_mainregimev2_hits": exact_mainregimev2_hits,
        "r5_post_cutoff_route_hits": r5_hits,
        "r3_native_subhour_crisis_hits": r3_hits,
        "r6_owner_control_route_hits": r6_hits,
        "broad_context_hits": broad_hits,
        "accepted_rows_added": accepted_rows_added,
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
        "update_goal": False,
    }

    write_json(OUT_ROOT / "openalex_semantic_pwc_source_route_after_080700_v1.json", summary)

    with (OUT_ROOT / "openalex_semantic_pwc_source_route_requests_v1.csv").open(
        "w", newline="", encoding="utf-8"
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=list(requests[0].keys()))
        writer.writeheader()
        writer.writerows(requests)

    candidate_fields = [
        "surface",
        "query_id",
        "title",
        "url",
        "year",
        "required_filename_or_token_hit",
        "r3_native_subhour_crisis_hit",
        "r5_post_cutoff_route_hit",
        "r6_owner_control_route_hit",
        "broad_context_hit",
    ]
    with (OUT_ROOT / "openalex_semantic_pwc_source_route_candidates_v1.csv").open(
        "w", newline="", encoding="utf-8"
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=candidate_fields)
        writer.writeheader()
        writer.writerows(candidates)

    report = [
        "# OpenAlex / Semantic Scholar / PapersWithCode Source Route Probe After 080700 v1",
        "",
        f"Gate result: `{gate_result}`.",
        "",
        "This is public paper-index metadata only. It does not approve metadata, method papers,",
        "or broad context hits as source/control evidence.",
        "",
        "## Metrics",
        "",
        f"- Requests sent: `{summary['requests_sent']}`",
        f"- Failed or parse-failed: `{summary['failed_or_parse_failed']}`",
        f"- Candidate rows scanned: `{summary['candidate_rows']}`",
        f"- Required filename/token hits: `{summary['required_filename_or_token_hits']}`",
        f"- Exact `MainRegimeV2` hits: `{summary['exact_mainregimev2_hits']}`",
        f"- R5 post-cutoff route hits: `{summary['r5_post_cutoff_route_hits']}`",
        f"- R3 native-subhour Crisis route hits: `{summary['r3_native_subhour_crisis_hits']}`",
        f"- R6 owner/control route hits: `{summary['r6_owner_control_route_hits']}`",
        f"- Broad context hits: `{summary['broad_context_hits']}`",
        "",
        "## Decision",
        "",
        "- Accepted rows added: `0`.",
        "- No valid required R3/R5/R6 source/control root was acquired.",
        "- No canonical merge, selected-data AutoQuant promotion, or downstream promotion rerun is allowed.",
        "- `update_goal=false`.",
    ]
    (OUT_ROOT / "openalex_semantic_pwc_source_route_after_080700_v1.md").write_text(
        "\n".join(report) + "\n", encoding="utf-8"
    )

    assertion_lines = [
        "PASS openalex_semantic_pwc_source_route_after_080700_v1",
        f"gate_result={gate_result}",
        f"requests_sent={summary['requests_sent']}",
        f"failed_or_parse_failed={summary['failed_or_parse_failed']}",
        f"candidate_rows={summary['candidate_rows']}",
        f"required_filename_or_token_hits={summary['required_filename_or_token_hits']}",
        f"exact_mainregimev2_hits={summary['exact_mainregimev2_hits']}",
        f"r5_post_cutoff_route_hits={summary['r5_post_cutoff_route_hits']}",
        f"r3_native_subhour_crisis_hits={summary['r3_native_subhour_crisis_hits']}",
        f"r6_owner_control_route_hits={summary['r6_owner_control_route_hits']}",
        f"broad_context_hits={summary['broad_context_hits']}",
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
    (CHECK_ROOT / "openalex_semantic_pwc_source_route_after_080700_v1_assertions.out").write_text(
        "\n".join(assertion_lines) + "\n", encoding="utf-8"
    )

    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
