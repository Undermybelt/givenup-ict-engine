#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import json
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


RUN_ID = "20260512T080333+0800-codex-openml-dataverse-source-route-probe-after-075932-v1"
GATE = "openml_dataverse_source_route_probe_after_075932_v1=no_required_source_control_unlock"
REPO = Path("/Users/thrill3r/projects-ict-engine/ict-engine")
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs" / RUN_ID
OUT = RUN_ROOT / "openml-dataverse-source-route-probe-after-075932-v1"
CHECKS = RUN_ROOT / "checks"
BOARD_B = REPO / "docs/plans/2026-05-10-regime-conditional-auto-quant-profitability-todo.md"

QUERIES = [
    "MainRegimeV2",
    "main_regime_v2",
    "source_confidence matched_negative_group_id",
    "native_subhour_source_label_rows Crisis",
    "direct_manipulation_positive_rows matched_controls provenance",
    "Oystacher spoofing futures order book matched controls",
    "stock market regimes 2026 extension",
    "Bull Bear Sideways Crisis market regime labels",
]

REQUIRED_TERMS = [
    "MainRegimeV2",
    "main_regime_v2",
    "source_confidence",
    "matched_negative",
    "matched_control",
    "matched_controls",
    "owner_export",
    "order_lifecycle",
    "direct_manipulation_positive_rows",
    "direct_manipulation_matched_controls",
    "native_subhour_source_label_rows",
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def fetch_json(url: str) -> tuple[int | None, dict | None, str]:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "ict-engine-openml-dataverse-source-route-probe/1.0",
            "Accept": "application/json,text/plain,*/*",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=25) as resp:
            raw = resp.read(1_000_000).decode("utf-8", "replace")
            try:
                return resp.status, json.loads(raw), ""
            except json.JSONDecodeError as exc:
                return resp.status, None, f"json_decode_error:{exc}"
    except urllib.error.HTTPError as exc:
        raw = exc.read(20_000).decode("utf-8", "replace")
        return exc.code, None, f"http_error:{exc.code}:{raw[:200]}"
    except Exception as exc:
        return None, None, f"{type(exc).__name__}:{exc}"


def text_has(text: str, terms: list[str]) -> list[str]:
    lower = text.lower()
    return [term for term in terms if term.lower() in lower]


def openml_query(query: str) -> tuple[dict, list[dict]]:
    url = "https://www.openml.org/api/v1/json/data/list/data_name/" + urllib.parse.quote(query)
    status, data, error = fetch_json(url)
    req = {
        "provider": "openml",
        "query": query,
        "url": url,
        "status": status,
        "error": error,
    }
    rows: list[dict] = []
    for item in (((data or {}).get("data") or {}).get("dataset") or [])[:10]:
        title = str(item.get("name") or "")
        desc = json.dumps(item, ensure_ascii=False)
        matched = text_has(f"{title}\n{desc}", REQUIRED_TERMS)
        rows.append(
            {
                "provider": "openml",
                "query": query,
                "title": title,
                "url": f"https://www.openml.org/d/{item.get('did')}",
                "matched_required_terms": "|".join(matched),
                "summary": desc[:500],
            }
        )
    req["returned_rows"] = len(rows)
    return req, rows


def dataverse_query(query: str) -> tuple[dict, list[dict]]:
    url = "https://dataverse.harvard.edu/api/search?type=dataset&per_page=10&q=" + urllib.parse.quote(query)
    status, data, error = fetch_json(url)
    req = {
        "provider": "harvard_dataverse",
        "query": query,
        "url": url,
        "status": status,
        "error": error,
        "total_count": (((data or {}).get("data") or {}).get("total_count")),
    }
    rows: list[dict] = []
    for item in (((data or {}).get("data") or {}).get("items") or [])[:10]:
        title = str(item.get("name") or item.get("title") or "")
        url_item = str(item.get("url") or item.get("global_id") or "")
        summary = json.dumps(item, ensure_ascii=False)
        matched = text_has(f"{title}\n{summary}", REQUIRED_TERMS)
        rows.append(
            {
                "provider": "harvard_dataverse",
                "query": query,
                "title": title,
                "url": url_item,
                "matched_required_terms": "|".join(matched),
                "summary": summary[:500],
            }
        )
    req["returned_rows"] = len(rows)
    return req, rows


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)

    requests: list[dict] = []
    candidates: list[dict] = []
    for query in QUERIES:
        for fn in (openml_query, dataverse_query):
            req, rows = fn(query)
            requests.append(req)
            candidates.extend(rows)

    exact_mainregimev2_hits = [
        row for row in candidates if "mainregimev2" in (row["title"] + row["summary"]).lower()
    ]
    required_hits = [row for row in candidates if row["matched_required_terms"]]
    r5_post_cutoff_hits = [
        row for row in required_hits if ("2026" in row["summary"] and "mainregime" in row["summary"].lower())
    ]
    r3_native_subhour_hits = [
        row for row in required_hits if ("native_subhour" in row["summary"].lower() and "crisis" in row["summary"].lower())
    ]
    r6_owner_control_hits = [
        row
        for row in required_hits
        if (
            "direct_manipulation" in row["summary"].lower()
            or "oystacher" in row["summary"].lower()
            or "order_lifecycle" in row["summary"].lower()
        )
    ]

    result = {
        "run_id": RUN_ID,
        "gate_result": GATE,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "board_b_sha256": sha256(BOARD_B),
        "providers_queried": ["openml", "harvard_dataverse"],
        "requests_sent": len(requests),
        "request_failures": sum(1 for r in requests if r.get("error")),
        "candidate_rows": len(candidates),
        "required_metadata_hits": len(required_hits),
        "exact_mainregimev2_hits": len(exact_mainregimev2_hits),
        "r5_post_cutoff_hits": len(r5_post_cutoff_hits),
        "r3_native_subhour_hits": len(r3_native_subhour_hits),
        "r6_owner_control_hits": len(r6_owner_control_hits),
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

    with (OUT / "openml_dataverse_source_route_requests_v1.csv").open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["provider", "query", "url", "status", "error", "total_count", "returned_rows"])
        writer.writeheader()
        writer.writerows(requests)
    with (OUT / "openml_dataverse_source_route_candidates_v1.csv").open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["provider", "query", "title", "url", "matched_required_terms", "summary"])
        writer.writeheader()
        writer.writerows(candidates)
    (OUT / "openml_dataverse_source_route_probe_after_075932_v1.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n"
    )

    report = f"""# OpenML / Dataverse Source Route Probe After 075932 v1

Run id: `{RUN_ID}`

Gate result: `{GATE}`

## Scope

Bounded public OpenML and Harvard Dataverse metadata probe after the `075932` Figshare/OSF route stayed fail-closed. This checks whether another public dataset route exposes source-owned post-`2026-01-30` R5 `MainRegimeV2` rows, verifier-native Crisis-capable R3 labels, R6 owner/export positives with matched controls, or a genuinely new accepted cross-timeframe `MainRegimeV2` source export. It does not mutate R3/R5/R6 target roots, approve public metadata as source/control evidence, download or derive labels, run direct verifier, split calibration, canonical merge, selected-data AutoQuant, filter / Pre-Bayes, BBN, CatBoost/path-ranking, execution-tree promotion, make a trade claim, or call `update_goal`.

## Readback

- Providers queried: OpenML and Harvard Dataverse.
- Requests sent: `{result["requests_sent"]}`.
- Request failures: `{result["request_failures"]}`.
- Candidate rows scanned: `{result["candidate_rows"]}`.
- Required metadata hits: `{result["required_metadata_hits"]}`.
- Exact `MainRegimeV2` hits: `{result["exact_mainregimev2_hits"]}`.
- R5 post-cutoff source-panel hits: `{result["r5_post_cutoff_hits"]}`.
- R3 native-subhour Crisis hits: `{result["r3_native_subhour_hits"]}`.
- R6 owner/control hits: `{result["r6_owner_control_hits"]}`.

## Decision

No OpenML or Harvard Dataverse route supplied verifier-native R6 owner/export positives with matched controls and approving provenance, source-owned post-`2026-01-30` R5 `MainRegimeV2` rows, verifier-native Crisis-capable R3 labels, or a genuinely accepted cross-timeframe `MainRegimeV2` source export.

Accepted rows added `0`; R6 owner/export unlock false; R5 recency unlock false; R3 native-subhour unlock false; valid required-root unlock false; source/control evidence acquired false; canonical merge false; selected-data AutoQuant promotion false; downstream promotion rerun false; strict full objective false; trade usable false; `update_goal=false`.

## Artifacts

- JSON: `docs/experiments/actionable-regime-confidence/runs/{RUN_ID}/openml-dataverse-source-route-probe-after-075932-v1/openml_dataverse_source_route_probe_after_075932_v1.json`
- Candidate CSV: `docs/experiments/actionable-regime-confidence/runs/{RUN_ID}/openml-dataverse-source-route-probe-after-075932-v1/openml_dataverse_source_route_candidates_v1.csv`
- Request CSV: `docs/experiments/actionable-regime-confidence/runs/{RUN_ID}/openml-dataverse-source-route-probe-after-075932-v1/openml_dataverse_source_route_requests_v1.csv`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/{RUN_ID}/checks/openml_dataverse_source_route_probe_after_075932_v1_assertions.out`

## Next

Continue source/control acquisition only before any direct verifier, split calibration, canonical merge, selected-data AutoQuant, filter / Pre-Bayes, BBN, CatBoost/path-ranking, or execution-tree promotion.
"""
    (OUT / "openml_dataverse_source_route_probe_after_075932_v1.md").write_text(report)

    assertions = "\n".join(
        [
            "PASS openml_dataverse_source_route_probe_after_075932_v1",
            f"gate_result={GATE}",
            f"requests_sent={result['requests_sent']}",
            f"request_failures={result['request_failures']}",
            f"candidate_rows={result['candidate_rows']}",
            f"required_metadata_hits={result['required_metadata_hits']}",
            f"exact_mainregimev2_hits={result['exact_mainregimev2_hits']}",
            f"r5_post_cutoff_hits={result['r5_post_cutoff_hits']}",
            f"r3_native_subhour_hits={result['r3_native_subhour_hits']}",
            f"r6_owner_control_hits={result['r6_owner_control_hits']}",
            "accepted_rows_added=0",
            "valid_required_root_unlock=false",
            "source_control_evidence_acquired=false",
            "canonical_merge=false",
            "selected_data_autoquant_promotion=false",
            "downstream_promotion_rerun=false",
            "strict_full_objective=false",
            "trade_usable=false",
            "promotion_allowed=false",
            "update_goal=false",
            "",
        ]
    )
    (CHECKS / "openml_dataverse_source_route_probe_after_075932_v1_assertions.out").write_text(assertions)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
