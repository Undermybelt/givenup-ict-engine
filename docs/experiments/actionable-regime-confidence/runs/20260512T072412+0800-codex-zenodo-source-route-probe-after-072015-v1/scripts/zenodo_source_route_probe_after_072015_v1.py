#!/usr/bin/env python3
"""Board A source/control route probe against Zenodo public records."""

from __future__ import annotations

import csv
import json
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path


RUN_ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = RUN_ROOT / "zenodo-source-route-probe-after-072015-v1"
RAW_DIR = RUN_ROOT / "command-output"
CHECK_DIR = RUN_ROOT / "checks"

QUERY_SPECS = [
    ("oystacher_exact", '"Oystacher"', "r6_owner_export_exact"),
    ("three_red_exact", '"3Red Trading"', "r6_owner_export_exact"),
    ("positive_filename", '"direct_manipulation_positive_rows"', "required_filename"),
    ("controls_filename", '"direct_manipulation_matched_controls"', "required_filename"),
    ("provenance_filename", '"direct_manipulation_provenance"', "required_filename"),
    ("mainregimev2_exact", '"MainRegimeV2"', "r5_r3_exact"),
    ("native_subhour_label_exact", '"native subhour source label"', "r3_exact"),
    ("stock_regime_2026_exact", '"stock market regimes 2026"', "r5_context"),
    ("market_regime_crisis_exact", '"market regime crisis"', "r3_context"),
    ("futures_order_lifecycle_spoofing_exact", '"futures order lifecycle spoofing"', "r6_context"),
    ("level4_order_book_broad", '"Level 4 Order Book"', "order_lifecycle_context"),
    ("hyperliquid_order_book_broad", "Hyperliquid order book", "order_lifecycle_context"),
]

REQUIRED_FILENAMES = {
    "direct_manipulation_positive_rows.csv",
    "direct_manipulation_matched_controls.csv",
    "direct_manipulation_provenance.json",
}


def fetch_records(query: str, size: int = 10) -> dict:
    encoded = urllib.parse.urlencode({"q": query, "size": str(size), "sort": "bestmatch"})
    url = f"https://zenodo.org/api/records?{encoded}"
    request = urllib.request.Request(url, headers={"User-Agent": "ict-engine-board-a-source-route-probe/1.0"})
    with urllib.request.urlopen(request, timeout=30) as response:
        body = response.read().decode("utf-8")
    return {"url": url, "json": json.loads(body)}


def hit_text(hit: dict) -> str:
    metadata = hit.get("metadata") or {}
    files = hit.get("files") or []
    file_names = " ".join(str(f.get("key") or f.get("filename") or "") for f in files if isinstance(f, dict))
    fields = [
        str(metadata.get("title") or ""),
        str(metadata.get("description") or ""),
        " ".join(str(k) for k in metadata.get("keywords") or []),
        file_names,
    ]
    return " ".join(fields).lower()


def slim_hit(hit: dict) -> dict:
    metadata = hit.get("metadata") or {}
    files = hit.get("files") or []
    return {
        "id": hit.get("id"),
        "conceptdoi": hit.get("conceptdoi"),
        "doi": hit.get("doi"),
        "created": hit.get("created"),
        "updated": hit.get("updated"),
        "title": metadata.get("title"),
        "publication_date": metadata.get("publication_date"),
        "resource_type": (metadata.get("resource_type") or {}).get("type"),
        "keywords": metadata.get("keywords") or [],
        "links": {
            "html": (hit.get("links") or {}).get("html"),
            "self": (hit.get("links") or {}).get("self"),
        },
        "files": [
            {
                "key": f.get("key"),
                "size": f.get("size"),
                "checksum": f.get("checksum"),
            }
            for f in files
            if isinstance(f, dict)
        ],
    }


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)

    query_results = []
    context_hits = []
    required_hit_count = 0
    exact_unlock_hit_count = 0

    for slug, query, route in QUERY_SPECS:
        try:
            fetched = fetch_records(query)
            exit_code = 0
            error = ""
        except Exception as exc:  # noqa: BLE001 - artifact should record failed route probes.
            fetched = {"url": "", "json": {"hits": {"total": 0, "hits": []}}}
            exit_code = 1
            error = repr(exc)

        raw_path = RAW_DIR / f"zenodo_{slug}.json"
        raw_path.write_text(json.dumps(fetched["json"], indent=2, sort_keys=True), encoding="utf-8")
        (RAW_DIR / f"zenodo_{slug}.url").write_text(fetched["url"] + "\n", encoding="utf-8")
        (RAW_DIR / f"zenodo_{slug}.exit").write_text(str(exit_code) + "\n", encoding="utf-8")
        if error:
            (RAW_DIR / f"zenodo_{slug}.stderr").write_text(error + "\n", encoding="utf-8")

        hits_obj = fetched["json"].get("hits") or {}
        total = int(hits_obj.get("total") or 0)
        hits = hits_obj.get("hits") or []
        slim_hits = [slim_hit(hit) for hit in hits[:10]]

        query_required_hits = 0
        query_exact_unlock_hits = 0
        query_context_hits = 0
        for hit in hits[:10]:
            text = hit_text(hit)
            has_required_file = any(name in text for name in REQUIRED_FILENAMES)
            has_owner_terms = ("oystacher" in text) or ("3red trading" in text) or ("3 red trading" in text)
            has_mainregime = "mainregimev2" in text
            has_order_lifecycle_context = ("order book" in text) or ("level 4" in text) or ("l4" in text)

            if has_required_file:
                query_required_hits += 1
            if has_owner_terms or has_mainregime:
                query_exact_unlock_hits += 1
            if has_order_lifecycle_context:
                query_context_hits += 1
                context_hits.append(slim_hit(hit))

        required_hit_count += query_required_hits
        exact_unlock_hit_count += query_exact_unlock_hits

        query_results.append(
            {
                "slug": slug,
                "query": query,
                "route": route,
                "api_url": fetched["url"],
                "exit_code": exit_code,
                "total": total,
                "required_filename_hits_in_top_10": query_required_hits,
                "owner_or_mainregime_hits_in_top_10": query_exact_unlock_hits,
                "order_lifecycle_context_hits_in_top_10": query_context_hits,
                "hits": slim_hits,
            }
        )

        time.sleep(0.25)

    unique_context = {}
    for hit in context_hits:
        unique_context[str(hit.get("id") or hit.get("doi") or hit.get("title"))] = hit

    exact_queries_failed = sum(1 for r in query_results if r["exit_code"] != 0)
    required_roots = {
        "/tmp/ict-engine-board-a-r6-owner-export-v1": Path("/tmp/ict-engine-board-a-r6-owner-export-v1").exists(),
        "/tmp/ict-engine-source-panel-recency-extension": Path("/tmp/ict-engine-source-panel-recency-extension").exists(),
        "/tmp/ict-engine-native-subhour-source-label-intake": Path("/tmp/ict-engine-native-subhour-source-label-intake").exists(),
        "/tmp/ict-engine-source-label-equivalence-intake": Path("/tmp/ict-engine-source-label-equivalence-intake").exists(),
    }

    decision = {
        "gate": "zenodo_source_route_probe_after_072015_v1",
        "gate_result": "exact_required_queries_zero_generic_l4_context_only_no_unlock",
        "valid_required_root_unlock": False,
        "source_control_evidence_acquired": False,
        "r6_owner_export_unlock": False,
        "r5_recency_unlock": False,
        "r3_native_subhour_unlock": False,
        "canonical_merge": False,
        "downstream_promotion_rerun": False,
        "strict_full_objective": False,
        "trade_usable": False,
        "update_goal": False,
        "notes": [
            "Zenodo exact searches did not find Oystacher/3Red owner-export records, required direct_manipulation filenames, MainRegimeV2 rows, or native-subhour source labels.",
            "Broader Level 4 / Hyperliquid order-book hits are context only: they are not CFTC/Oystacher/3Red positives, matched normal controls, source-panel MainRegimeV2 recency rows, or Crisis-capable R3 labels.",
            "This probe did not mutate required roots and does not authorize direct verifier, split calibration, canonical merge, AutoQuant selected-data promotion, or downstream BBN/CatBoost/execution-tree promotion.",
        ],
    }

    payload = {
        "run_root": str(RUN_ROOT),
        "decision": decision,
        "required_roots": required_roots,
        "summary": {
            "query_count": len(query_results),
            "failed_query_count": exact_queries_failed,
            "required_filename_hits_in_top_10": required_hit_count,
            "owner_or_mainregime_hits_in_top_10": exact_unlock_hit_count,
            "unique_order_lifecycle_context_hits": len(unique_context),
        },
        "query_results": query_results,
        "context_hits": list(unique_context.values()),
    }

    json_path = OUT_DIR / "zenodo_source_route_probe_after_072015_v1.json"
    csv_path = OUT_DIR / "zenodo_source_route_probe_after_072015_v1.csv"
    md_path = OUT_DIR / "zenodo_source_route_probe_after_072015_v1.md"
    assertions_path = CHECK_DIR / "zenodo_source_route_probe_after_072015_v1_assertions.out"

    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")

    with csv_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "slug",
                "query",
                "route",
                "exit_code",
                "total",
                "required_filename_hits_in_top_10",
                "owner_or_mainregime_hits_in_top_10",
                "order_lifecycle_context_hits_in_top_10",
                "api_url",
            ],
        )
        writer.writeheader()
        for row in query_results:
            writer.writerow({field: row[field] for field in writer.fieldnames})

    context_lines = []
    for hit in list(unique_context.values())[:5]:
        context_lines.append(f"- {hit.get('title')} ({hit.get('links', {}).get('html') or hit.get('doi')})")
    if not context_lines:
        context_lines.append("- None")

    md_path.write_text(
        "\n".join(
            [
                "# Zenodo Source Route Probe After 072015 v1",
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
                "## Exact Required Query Result",
                "",
                f"- Required filename hits in top 10: `{required_hit_count}`",
                f"- Owner/MainRegimeV2 hits in top 10: `{exact_unlock_hit_count}`",
                f"- Failed query count: `{exact_queries_failed}`",
                "",
                "## Context-Only Hits",
                "",
                *context_lines,
                "",
                "## Non-Promotion Reason",
                "",
                "Broader order-book records do not supply CFTC/Oystacher/3Red manipulation positives, matched normal controls, owner-export provenance, source-panel `MainRegimeV2` post-cutoff rows, or verifier-native Crisis-capable R3 labels.",
                "",
                "## Next",
                "",
                "Continue only from explicit source/control approval, verifier-native R6 owner-export rows with valid controls, source-owned post-`2026-01-30` R5 rows matching the source-panel schema, verifier-native Crisis-capable R3 `MainRegimeV2` labels, or a genuinely new accepted cross-timeframe `MainRegimeV2` source export.",
                "",
            ]
        ),
        encoding="utf-8",
    )

    assertions_path.write_text(
        "\n".join(
            [
                f"gate_result={decision['gate_result']}",
                f"query_count={len(query_results)}",
                f"failed_query_count={exact_queries_failed}",
                f"required_filename_hits_in_top_10={required_hit_count}",
                f"owner_or_mainregime_hits_in_top_10={exact_unlock_hit_count}",
                f"unique_order_lifecycle_context_hits={len(unique_context)}",
                "valid_required_root_unlock=false",
                "source_control_evidence_acquired=false",
                "r6_owner_export_unlock=false",
                "r5_recency_unlock=false",
                "r3_native_subhour_unlock=false",
                "canonical_merge=false",
                "downstream_promotion_rerun=false",
                "strict_full_objective=false",
                "trade_usable=false",
                "update_goal=false",
                "",
            ]
        ),
        encoding="utf-8",
    )

    print(json.dumps(payload["summary"], sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
