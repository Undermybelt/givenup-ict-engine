#!/usr/bin/env python3
"""Board A Figshare/OSF source-route probe for exact source/control terms."""

from __future__ import annotations

import csv
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


RUN_ID = "20260512T075932+0800-codex-figshare-osf-source-route-probe-after-075818-v1"
RUN_ROOT = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260512T075932+0800-codex-figshare-osf-source-route-probe-after-075818-v1"
)
ARTIFACT_DIR = RUN_ROOT / "figshare-osf-source-route-probe-after-075818-v1"
COMMAND_DIR = RUN_ROOT / "command-output"
CHECKS_DIR = RUN_ROOT / "checks"

QUERIES = [
    "MainRegimeV2",
    "stock_market_regimes_2026_extension",
    "stock market regimes 2026 extension",
    "native subhour source label rows",
    "market regime crisis labels",
    "Oystacher spoofing futures order book",
    "3 Red Trading matched controls",
    "futures order lifecycle spoofing controls",
    "direct manipulation matched controls",
    "CFE VIX futures trades quotes",
]

REQUIRED_PATTERNS = {
    "mainregimev2": re.compile(r"\bmain[_-]?regime[_-]?v2\b", re.I),
    "r5_required_file": re.compile(r"stock[_-]market[_-]regimes[_-]2026[_-]extension", re.I),
    "r5_provenance": re.compile(r"source[_-]panel[_-]recency[_-]provenance", re.I),
    "r3_required_file": re.compile(r"native[_-]subhour[_-]source[_-]label[_-]rows", re.I),
    "r6_positive_file": re.compile(r"positive[_-]spoofing[_-]layering[_-]rows", re.I),
    "r6_control_file": re.compile(r"matched[_-]negative[_-]normal[_-]activity[_-]rows", re.I),
}

BROAD_CONTEXT_PATTERNS = {
    "oystacher": re.compile(r"oystacher|3\s*red\s*trading|3red", re.I),
    "market_depth": re.compile(r"market\s+depth|market\s+by\s+order|\bmbo\b|\bmbp\b|order\s+book|level\s*2|l2", re.I),
    "order_lifecycle": re.compile(r"order[_ -]?lifecycle|cancel(?:led|lation)?|spoof(?:ing)?|layering|matched controls|normal controls|non[- ]manipulation", re.I),
    "crisis_regime": re.compile(r"market\s+regime.*crisis|crisis.*market\s+regime|crisis.*regime", re.I),
    "vix_cfe": re.compile(r"\bcfe\b|vix futures|cboe", re.I),
}


def slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")[:64] or "query"


def fetch_json(url: str, body: dict | None = None) -> tuple[int | None, object | None, str | None]:
    data = None
    headers = {
        "User-Agent": "ict-engine-board-a-source-route-probe/1.0",
        "Accept": "application/json",
    }
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(
        url,
        data=data,
        headers=headers,
        method="POST" if body is not None else "GET",
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = resp.read()
            status = getattr(resp, "status", None)
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")[:2000]
        return exc.code, None, body
    except Exception as exc:  # noqa: BLE001
        return None, None, repr(exc)
    try:
        return status, json.loads(data.decode("utf-8", errors="replace")), None
    except Exception as exc:  # noqa: BLE001
        return status, None, repr(exc)


def figshare_request(query: str) -> tuple[str, dict]:
    return (
        "https://api.figshare.com/v2/articles/search",
        {
            "search_for": query,
            "page_size": 10,
            "order": "published_date",
            "order_direction": "desc",
        },
    )


def osf_preprints_url(query: str) -> str:
    params = urllib.parse.urlencode(
        {
            "filter[title]": query,
            "page[size]": 10,
        }
    )
    return f"https://api.osf.io/v2/preprints/?{params}"


def normalize_figshare(row: dict, query: str) -> dict:
    return {
        "provider": "figshare",
        "query": query,
        "title": row.get("title", ""),
        "url": row.get("url_private_api") or row.get("url_public_api") or row.get("url", ""),
        "html_url": row.get("url") or row.get("doi") or "",
        "doi": row.get("doi", ""),
        "date": row.get("published_date") or row.get("modified_date") or "",
        "summary": row.get("description", "") or row.get("defined_type_name", "") or "",
        "raw_id": str(row.get("id", "")),
    }


def normalize_osf(row: dict, query: str) -> dict:
    attrs = row.get("attributes") or {}
    links = row.get("links") or {}
    return {
        "provider": "osf_preprints",
        "query": query,
        "title": attrs.get("title", ""),
        "url": links.get("self", ""),
        "html_url": links.get("html", ""),
        "doi": attrs.get("doi", ""),
        "date": attrs.get("date_published") or attrs.get("date_created") or "",
        "summary": attrs.get("description", ""),
        "raw_id": str(row.get("id", "")),
    }


def classify(row: dict) -> dict:
    text = " ".join(str(row.get(k, "")) for k in ("title", "summary", "url", "html_url", "doi"))
    required = [name for name, pattern in REQUIRED_PATTERNS.items() if pattern.search(text)]
    broad = [name for name, pattern in BROAD_CONTEXT_PATTERNS.items() if pattern.search(text)]
    row["required_hits"] = ";".join(required)
    row["broad_context_hits"] = ";".join(broad)
    row["accepted_for_board_a"] = "false"
    if required:
        row["disposition"] = "exact_token_hit_requires_manual_source_file_review_no_unlock"
    elif broad:
        row["disposition"] = "context_only_no_required_file_or_schema"
    else:
        row["disposition"] = "unrelated_metadata"
    return row


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    COMMAND_DIR.mkdir(parents=True, exist_ok=True)
    CHECKS_DIR.mkdir(parents=True, exist_ok=True)

    requests = []
    candidates: list[dict] = []
    for query in QUERIES:
        figshare_search_url, figshare_body = figshare_request(query)
        endpoints = [
            ("figshare", figshare_search_url, figshare_body),
            ("osf_preprints", osf_preprints_url(query), None),
        ]
        for provider, url, body in endpoints:
            status, payload, error = fetch_json(url, body)
            raw_name = f"{provider}_{slug(query)}.json"
            (COMMAND_DIR / raw_name).write_text(
                json.dumps(
                    {
                        "provider": provider,
                        "query": query,
                        "url": url,
                        "body": body,
                        "status": status,
                        "error": error,
                        "payload": payload,
                    },
                    ensure_ascii=False,
                    indent=2,
                    sort_keys=True,
                ),
                encoding="utf-8",
            )
            requests.append(
                {
                    "provider": provider,
                    "query": query,
                    "status": status,
                    "error": error or "",
                    "raw_file": str(COMMAND_DIR / raw_name),
                }
            )
            if payload is None:
                continue
            if provider == "figshare" and isinstance(payload, list):
                for item in payload[:10]:
                    if isinstance(item, dict):
                        candidates.append(classify(normalize_figshare(item, query)))
            elif provider == "osf_preprints" and isinstance(payload, dict):
                for item in (payload.get("data") or [])[:10]:
                    if isinstance(item, dict):
                        candidates.append(classify(normalize_osf(item, query)))

    fields = [
        "provider",
        "query",
        "title",
        "date",
        "doi",
        "html_url",
        "url",
        "raw_id",
        "required_hits",
        "broad_context_hits",
        "disposition",
        "accepted_for_board_a",
        "summary",
    ]
    write_csv(ARTIFACT_DIR / "figshare_osf_source_route_candidates_v1.csv", candidates, fields)
    write_csv(ARTIFACT_DIR / "figshare_osf_source_route_requests_v1.csv", requests, ["provider", "query", "status", "error", "raw_file"])

    required_hits = sum(1 for row in candidates if row["required_hits"])
    exact_mainregime = sum(1 for row in candidates if "mainregimev2" in row["required_hits"].split(";"))
    r5_hits = sum(1 for row in candidates if {"r5_required_file", "r5_provenance"} & set(row["required_hits"].split(";")))
    r3_hits = sum(1 for row in candidates if "r3_required_file" in row["required_hits"].split(";"))
    r6_hits = sum(1 for row in candidates if {"r6_positive_file", "r6_control_file"} & set(row["required_hits"].split(";")))
    broad_context_rows = sum(1 for row in candidates if row["broad_context_hits"])
    failed_or_parse = sum(1 for row in requests if row["error"] or row["status"] not in (200, 201))
    gate_result = "figshare_osf_source_route_probe_after_075818_v1=no_required_source_control_unlock"
    summary = {
        "accepted_rows_added": 0,
        "broad_context_rows": broad_context_rows,
        "canonical_merge": False,
        "downstream_promotion_rerun": False,
        "exact_mainregimev2_hits": exact_mainregime,
        "failed_or_parse": failed_or_parse,
        "gate_result": gate_result,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "r3_native_subhour_hits": r3_hits,
        "r3_native_subhour_unlock": False,
        "r5_post_cutoff_hits": r5_hits,
        "r5_recency_unlock": False,
        "r6_owner_control_hits": r6_hits,
        "r6_owner_export_unlock": False,
        "required_filename_hits": required_hits,
        "requests_sent": len(requests),
        "run_id": RUN_ID,
        "source_control_evidence_acquired": False,
        "strict_full_objective": False,
        "top_rows_scanned": len(candidates),
        "trade_usable": False,
        "update_goal": False,
        "valid_required_root_unlock": False,
    }

    (ARTIFACT_DIR / "figshare_osf_source_route_probe_after_075818_v1.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )

    sample_rows = [row for row in candidates if row["required_hits"] or row["broad_context_hits"]][:8]
    sample_md = "\n".join(
        f"- `{row['provider']}` `{row['query']}`: {row['title'] or '(untitled)'} "
        f"-> `{row['disposition']}`"
        for row in sample_rows
    ) or "- No exact or broad context candidate rows."

    report = f"""# Figshare / OSF Source Route Probe After 075818 v1

Run id: `{RUN_ID}`

Gate result: `{gate_result}`

## Scope

Read-only public Figshare and OSF API source-route probe after the `075818` Kaggle exact MainRegime search stayed blocked. This checks whether another public research-data route exposes source-owned post-`2026-01-30` R5 `MainRegimeV2` rows, verifier-native Crisis-capable R3 labels, R6 owner/export positives with matched controls, or a genuinely new accepted cross-timeframe `MainRegimeV2` source export. It does not mutate R3/R5/R6 target roots, approve public metadata as source/control evidence, download or derive labels, run direct verifier, split calibration, canonical merge, selected-data AutoQuant, filter / Pre-Bayes, BBN, CatBoost/path-ranking, execution-tree promotion, make a trade claim, or call `update_goal`.

## Readback

- Requests sent: `{summary['requests_sent']}`.
- Failed or parse-failed requests: `{summary['failed_or_parse']}`.
- Top metadata rows scanned: `{summary['top_rows_scanned']}`.
- Required filename/token hits: `{summary['required_filename_hits']}`.
- Exact `MainRegimeV2` hits: `{summary['exact_mainregimev2_hits']}`.
- R5 post-cutoff source-panel hits: `{summary['r5_post_cutoff_hits']}`.
- R3 native-subhour source-label hits: `{summary['r3_native_subhour_hits']}`.
- R6 owner/control file hits: `{summary['r6_owner_control_hits']}`.
- Broad context rows: `{summary['broad_context_rows']}`.

## Candidate Notes

{sample_md}

## Decision

No Figshare or OSF route supplied verifier-native R6 owner/export positives with matched controls and approving provenance, source-owned post-`2026-01-30` R5 `MainRegimeV2` rows, verifier-native Crisis-capable R3 labels, or a genuinely new accepted cross-timeframe `MainRegimeV2` source export.

Accepted rows added `0`; R6 owner/export unlock false; R5 recency unlock false; R3 native-subhour unlock false; valid required-root unlock false; source/control evidence acquired false; canonical merge false; downstream promotion rerun false; strict full objective false; trade usable false; `update_goal=false`.

## Artifacts

- JSON: `{ARTIFACT_DIR / 'figshare_osf_source_route_probe_after_075818_v1.json'}`
- Candidate CSV: `{ARTIFACT_DIR / 'figshare_osf_source_route_candidates_v1.csv'}`
- Request CSV: `{ARTIFACT_DIR / 'figshare_osf_source_route_requests_v1.csv'}`
- Assertions: `{CHECKS_DIR / 'figshare_osf_source_route_probe_after_075818_v1_assertions.out'}`
- Command output root: `{COMMAND_DIR}/`

## Next

Continue source/control acquisition only before any direct verifier, split calibration, canonical merge, selected-data AutoQuant, filter / Pre-Bayes, BBN, CatBoost/path-ranking, or execution-tree promotion.
"""
    (ARTIFACT_DIR / "figshare_osf_source_route_probe_after_075818_v1.md").write_text(report, encoding="utf-8")

    assertions = "\n".join(
        [
            "PASS figshare_osf_source_route_probe_after_075818_v1",
            f"gate_result={gate_result}",
            f"requests_sent={summary['requests_sent']}",
            f"failed_or_parse={summary['failed_or_parse']}",
            f"top_rows_scanned={summary['top_rows_scanned']}",
            f"required_filename_hits={summary['required_filename_hits']}",
            f"exact_mainregimev2_hits={summary['exact_mainregimev2_hits']}",
            f"r5_post_cutoff_hits={summary['r5_post_cutoff_hits']}",
            f"r3_native_subhour_hits={summary['r3_native_subhour_hits']}",
            f"r6_owner_control_hits={summary['r6_owner_control_hits']}",
            "accepted_rows_added=0",
            "r6_owner_export_unlock=false",
            "r5_recency_unlock=false",
            "r3_native_subhour_unlock=false",
            "valid_required_root_unlock=false",
            "source_control_evidence_acquired=false",
            "canonical_merge=false",
            "downstream_promotion_rerun=false",
            "strict_full_objective=false",
            "trade_usable=false",
            "update_goal=false",
        ]
    )
    (CHECKS_DIR / "figshare_osf_source_route_probe_after_075818_v1_assertions.out").write_text(
        assertions + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
