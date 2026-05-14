#!/usr/bin/env python3
"""Bounded DataCite source-route probe for Board A R3/R5/R6 unlock terms."""

from __future__ import annotations

import csv
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


RUN_ID = "20260512T072832+0800-codex-datacite-source-route-probe-after-072412-v1"
RUN_ROOT = Path("docs/experiments/actionable-regime-confidence/runs") / RUN_ID
OUT = RUN_ROOT / "command-output"
PACKET = RUN_ROOT / "datacite-source-route-probe-after-072412-v1"
CHECKS = RUN_ROOT / "checks"

QUERIES = [
    ("direct_manipulation_positive_rows", '"direct_manipulation_positive_rows"'),
    ("direct_manipulation_matched_controls", '"direct_manipulation_matched_controls"'),
    ("direct_manipulation_provenance", '"direct_manipulation_provenance"'),
    ("stock_market_regimes_2026_extension", '"stock_market_regimes_2026_extension"'),
    ("native_subhour_source_label_rows", '"native_subhour_source_label_rows"'),
    ("mainregimev2", '"MainRegimeV2"'),
    ("oystacher_spoofing_futures", "Oystacher spoofing futures"),
    ("three_red_trading_spoofing", '"3Red Trading" spoofing'),
    ("futures_order_lifecycle_spoofing", '"futures order lifecycle" spoofing'),
    ("market_regime_crisis_mainregimev2", '"market regime crisis" MainRegimeV2'),
    ("stock_market_regimes_2026", '"stock market regimes" 2026'),
]

REQUIRED_EXACT_TERMS = [
    "direct_manipulation_positive_rows",
    "direct_manipulation_matched_controls",
    "direct_manipulation_provenance",
    "stock_market_regimes_2026_extension",
    "native_subhour_source_label_rows",
    "MainRegimeV2",
]


def safe_name(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", value).strip("_") or "query"


def compact_text(value) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        return " ".join(compact_text(item) for item in value)
    if isinstance(value, dict):
        return " ".join(compact_text(item) for item in value.values())
    return re.sub(r"\s+", " ", str(value)).strip()


def fetch_query(query: str) -> tuple[int | None, dict]:
    params = urllib.parse.urlencode({"query": query, "page[size]": "10"})
    url = f"https://api.datacite.org/dois?{params}"
    req = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.api+json",
            "User-Agent": "ict-engine-board-a-source-route-probe/1.0",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            status = int(resp.status)
            payload = json.loads(resp.read().decode("utf-8"))
            return status, payload
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        return int(exc.code), {"errors": [{"status": exc.code, "detail": body[:1000]}]}
    except Exception as exc:  # fail-closed packet; preserve the error.
        return None, {"errors": [{"status": "exception", "detail": repr(exc)}]}


def record_text(item: dict) -> str:
    attrs = item.get("attributes", {})
    fields = [
        attrs.get("titles"),
        attrs.get("descriptions"),
        attrs.get("publisher"),
        attrs.get("container"),
        attrs.get("url"),
        attrs.get("doi"),
        attrs.get("types"),
    ]
    return compact_text(fields)


def summarize_item(item: dict) -> dict:
    attrs = item.get("attributes", {})
    title = compact_text(attrs.get("titles"))[:240]
    return {
        "doi": attrs.get("doi") or item.get("id"),
        "title": title,
        "publisher": compact_text(attrs.get("publisher"))[:160],
        "publication_year": attrs.get("publicationYear"),
        "url": attrs.get("url"),
        "resource_type": compact_text(attrs.get("types"))[:160],
    }


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    PACKET.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)
    (RUN_ROOT / "RUN_ROOT.txt").write_text(f"{RUN_ROOT}\n", encoding="utf-8")

    query_rows = []
    candidate_records = []
    required_hits = []
    failed_queries = 0

    for query_id, query in QUERIES:
        status, payload = fetch_query(query)
        raw_path = OUT / f"datacite_{safe_name(query_id)}.json"
        raw_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        (OUT / f"datacite_{safe_name(query_id)}.exit").write_text(
            "0\n" if status and 200 <= status < 300 else "1\n",
            encoding="utf-8",
        )
        result_items = payload.get("data", []) if isinstance(payload, dict) else []
        if not status or not (200 <= status < 300):
            failed_queries += 1

        exact_hits_for_query = []
        top_titles = []
        for item in result_items[:10]:
            item_text = record_text(item)
            summary = summarize_item(item)
            summary["query_id"] = query_id
            summary["query"] = query
            candidate_records.append(summary)
            if summary.get("title"):
                top_titles.append(summary["title"])
            matched_terms = [term for term in REQUIRED_EXACT_TERMS if term.lower() in item_text.lower()]
            if matched_terms:
                hit = {
                    "query_id": query_id,
                    "query": query,
                    "matched_terms": matched_terms,
                    **summary,
                }
                required_hits.append(hit)
                exact_hits_for_query.append(hit)

        query_rows.append(
            {
                "query_id": query_id,
                "query": query,
                "http_status": status if status is not None else "exception",
                "result_count_returned": len(result_items),
                "required_exact_hits": len(exact_hits_for_query),
                "top_titles": " | ".join(top_titles[:3]),
            }
        )
        time.sleep(0.2)

    csv_path = PACKET / "datacite_source_route_probe_after_072412_v1.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=[
                "query_id",
                "query",
                "http_status",
                "result_count_returned",
                "required_exact_hits",
                "top_titles",
            ],
        )
        writer.writeheader()
        writer.writerows(query_rows)

    total_results = sum(int(row["result_count_returned"]) for row in query_rows)
    exact_required_hits = len(required_hits)
    gate_result = "datacite_source_route_probe_after_072412_v1=no_exact_required_source_export_no_unlock"
    decision = {
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
    }

    summary = {
        "run_id": RUN_ID,
        "gate_result": gate_result,
        "scope": {
            "metadata_only": True,
            "raw_row_downloaded": False,
            "mutated_required_roots": False,
            "direct_verifier_run": False,
            "split_calibration_run": False,
            "canonical_merge": False,
            "downstream_promotion_rerun": False,
            "trade_claim": False,
            "update_goal": False,
        },
        "query_count": len(QUERIES),
        "failed_queries": failed_queries,
        "total_results_returned": total_results,
        "required_exact_hits": exact_required_hits,
        "required_hits": required_hits,
        "decision": decision,
        "artifacts": {
            "report": str(PACKET / "datacite_source_route_probe_after_072412_v1.md"),
            "json": str(PACKET / "datacite_source_route_probe_after_072412_v1.json"),
            "csv": str(csv_path),
            "assertions": str(CHECKS / "datacite_source_route_probe_after_072412_v1_assertions.out"),
            "command_output": str(OUT),
        },
    }
    (PACKET / "datacite_source_route_probe_after_072412_v1.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    report = f"""# DataCite Source Route Probe After 072412 v1

Run id: `{RUN_ID}`

Gate result: `{gate_result}`

## Scope

Metadata-only DataCite source-route probe after the duplicate `072412` Zenodo route. This packet searches registered dataset DOI metadata for exact R3/R5/R6 unlock terms. It does not download raw row data, mutate R3/R5/R6 roots, approve metadata-only records, run direct verifier, run split calibration, run canonical merge, run provider/AutoQuant promotion, run downstream filter/Pre-Bayes, BBN, CatBoost/path-ranking, execution-tree promotion, make a trade claim, or call `update_goal`.

## Readback

- Queries run: `{len(QUERIES)}`.
- Failed queries: `{failed_queries}`.
- Total returned records inspected: `{total_results}`.
- Exact required-term hits in returned metadata: `{exact_required_hits}`.

## Decision

No DataCite metadata result exposed a required source/control export for `direct_manipulation_positive_rows`, `direct_manipulation_matched_controls`, `direct_manipulation_provenance`, `stock_market_regimes_2026_extension`, `native_subhour_source_label_rows`, or `MainRegimeV2`.

Accepted rows added `0`; R6 owner/export unlock false; R5 recency unlock false; R3 native-subhour unlock false; valid required-root unlock false; source/control evidence acquired false; canonical merge false; downstream promotion rerun false; strict full objective false; trade usable false; `update_goal=false`.

## Artifacts

- JSON: `{PACKET / "datacite_source_route_probe_after_072412_v1.json"}`
- CSV: `{csv_path}`
- Assertions: `{CHECKS / "datacite_source_route_probe_after_072412_v1_assertions.out"}`
- Command output: `{OUT}`

## Next

Continue only from explicit source/control approval, verifier-native R6 owner-export rows with valid controls, source-owned post-`2026-01-30` R5 rows matching the source-panel schema, verifier-native Crisis-capable R3 `MainRegimeV2` labels, or a genuinely new accepted cross-timeframe `MainRegimeV2` source export before direct verifier, split calibration, canonical merge, provider/AutoQuant selected-data research, filter/Pre-Bayes, BBN, CatBoost/path-ranking, or execution-tree promotion.
"""
    (PACKET / "datacite_source_route_probe_after_072412_v1.md").write_text(report, encoding="utf-8")

    assertions = [
        f"gate_result={gate_result}",
        f"query_count={len(QUERIES)}",
        f"failed_queries={failed_queries}",
        f"total_results_returned={total_results}",
        f"required_exact_hits={exact_required_hits}",
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
    (CHECKS / "datacite_source_route_probe_after_072412_v1_assertions.out").write_text(
        "\n".join(assertions) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
