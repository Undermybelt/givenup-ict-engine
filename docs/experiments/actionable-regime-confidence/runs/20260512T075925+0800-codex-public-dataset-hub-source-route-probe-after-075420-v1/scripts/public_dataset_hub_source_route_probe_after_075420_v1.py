#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[6]
RUN_ID = "20260512T075925+0800-codex-public-dataset-hub-source-route-probe-after-075420-v1"
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs" / RUN_ID
ARTIFACT_DIR = RUN_ROOT / "public-dataset-hub-source-route-probe-after-075420-v1"
CHECK_DIR = RUN_ROOT / "checks"
COMMAND_OUTPUT_DIR = RUN_ROOT / "command-output"
BOARD_A = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"
BOARD_B = REPO / "docs/plans/2026-05-10-regime-conditional-auto-quant-profitability-todo.md"

QUERIES = [
    "MainRegimeV2",
    "stock market regimes 2000 2026",
    "native subhour market regime labels Crisis",
    "source panel market regime labels 2026",
    "Oystacher spoofing matched controls",
    "3Red Trading spoofing controls",
]

REQUIRED_PATTERNS = {
    "mainregimev2": re.compile(r"main\s*regime\s*v?2|mainregimev2", re.I),
    "source_panel": re.compile(r"source[-_\s]?panel|source[-_\s]?label", re.I),
    "native_subhour": re.compile(r"native[-_\s]?sub[-_\s]?hour|subhour", re.I),
    "crisis": re.compile(r"\bcrisis\b|stress|dislocation", re.I),
    "oystacher": re.compile(r"oystacher|3red|3\s*red", re.I),
    "matched_control": re.compile(r"matched[-_\s]?control|normal[-_\s]?control|negative[-_\s]?control", re.I),
    "owner_export": re.compile(r"owner[-_\s]?export|source[-_\s]?owned|exchange[-_\s]?owned|verifier[-_\s]?native", re.I),
    "recency": re.compile(r"2026|2025|2024", re.I),
}

USER_AGENT = "ict-engine-board-a-source-control-probe/1.0"


@dataclass
class ProviderRequest:
    provider: str
    query: str
    url: str
    method: str = "GET"
    body: bytes | None = None


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def request_json(req: ProviderRequest) -> tuple[int | None, Any | None, str | None, str]:
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/json, text/plain;q=0.9, */*;q=0.8",
    }
    if req.body is not None:
        headers["Content-Type"] = "application/json"
    http_req = urllib.request.Request(req.url, data=req.body, headers=headers, method=req.method)
    try:
        with urllib.request.urlopen(http_req, timeout=20) as resp:
            raw = resp.read(2_000_000)
            text = raw.decode("utf-8", errors="replace")
            try:
                return resp.status, json.loads(text), None, text[:1000]
            except json.JSONDecodeError as exc:
                return resp.status, None, f"json_decode_error:{exc}", text[:1000]
    except urllib.error.HTTPError as exc:
        snippet = exc.read(1000).decode("utf-8", errors="replace")
        return exc.code, None, f"http_error:{exc.code}", snippet
    except Exception as exc:  # network APIs vary; preserve the failure as evidence.
        return None, None, f"{type(exc).__name__}:{exc}", ""


def as_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (str, int, float, bool)):
        return str(value)
    if isinstance(value, list):
        return " ".join(as_text(v) for v in value[:20])
    if isinstance(value, dict):
        parts: list[str] = []
        for key in (
            "title",
            "name",
            "id",
            "description",
            "summary",
            "notes",
            "tags",
            "keywords",
            "metadata",
            "created",
            "modified",
            "updated",
            "published",
            "links",
            "url",
            "html_url",
            "doi",
        ):
            if key in value:
                parts.append(as_text(value[key]))
        if not parts:
            parts = [as_text(v) for _, v in list(value.items())[:20]]
        return " ".join(parts)
    return str(value)


def get_first(record: dict[str, Any], keys: tuple[str, ...]) -> str:
    for key in keys:
        value = record.get(key)
        if isinstance(value, str) and value:
            return value
        if value is not None and not isinstance(value, (dict, list)):
            return str(value)
    return ""


def extract_records(provider: str, payload: Any) -> list[dict[str, Any]]:
    if payload is None:
        return []
    if provider == "huggingface":
        return payload if isinstance(payload, list) else []
    if provider == "zenodo":
        if isinstance(payload, dict) and isinstance(payload.get("hits"), dict):
            hits = payload["hits"].get("hits")
            return hits if isinstance(hits, list) else []
        return []
    if provider == "figshare":
        return payload if isinstance(payload, list) else []
    if provider == "kaggle":
        return payload if isinstance(payload, list) else []
    return []


def record_url(provider: str, record: dict[str, Any]) -> str:
    if provider == "huggingface":
        dataset_id = get_first(record, ("id", "_id"))
        return f"https://huggingface.co/datasets/{dataset_id}" if dataset_id else ""
    if provider == "zenodo":
        links = record.get("links")
        if isinstance(links, dict):
            return str(links.get("html") or links.get("self_html") or links.get("latest_html") or "")
        return get_first(record, ("doi_url", "url"))
    if provider == "figshare":
        return get_first(record, ("url_public_html", "url", "doi"))
    if provider == "kaggle":
        ref = get_first(record, ("ref", "datasetSlug", "url"))
        if ref.startswith("http"):
            return ref
        return f"https://www.kaggle.com/datasets/{ref}" if ref else ""
    return ""


def record_title(provider: str, record: dict[str, Any]) -> str:
    if provider == "huggingface":
        return get_first(record, ("id", "cardData", "description"))[:300]
    if provider == "zenodo":
        metadata = record.get("metadata") if isinstance(record.get("metadata"), dict) else {}
        return get_first(metadata, ("title",)) or get_first(record, ("title", "id"))
    if provider in {"figshare", "kaggle"}:
        return get_first(record, ("title", "name", "ref", "datasetSlug"))
    return get_first(record, ("title", "name", "id"))


def providers_for_query(query: str) -> list[ProviderRequest]:
    encoded = urllib.parse.quote(query)
    figshare_body = json.dumps({"search_for": query, "page_size": 10}).encode("utf-8")
    return [
        ProviderRequest(
            provider="huggingface",
            query=query,
            url=f"https://huggingface.co/api/datasets?search={encoded}&limit=10",
        ),
        ProviderRequest(
            provider="zenodo",
            query=query,
            url=f"https://zenodo.org/api/records?q={encoded}&size=10",
        ),
        ProviderRequest(
            provider="figshare",
            query=query,
            url="https://api.figshare.com/v2/articles/search",
            method="POST",
            body=figshare_body,
        ),
        ProviderRequest(
            provider="kaggle",
            query=query,
            url=(
                "https://www.kaggle.com/api/v1/datasets/list"
                f"?search={encoded}&page=1&sortBy=relevance&fileType=all"
            ),
        ),
    ]


def flags_for_text(text: str) -> dict[str, bool]:
    return {name: bool(pattern.search(text)) for name, pattern in REQUIRED_PATTERNS.items()}


def main() -> int:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)
    COMMAND_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    board_hash_before = {
        "board_a": sha256_file(BOARD_A) if BOARD_A.exists() else None,
        "board_b": sha256_file(BOARD_B) if BOARD_B.exists() else None,
    }

    request_rows: list[dict[str, Any]] = []
    candidate_rows: list[dict[str, Any]] = []

    for query in QUERIES:
        for provider_req in providers_for_query(query):
            status, payload, error, raw_snippet = request_json(provider_req)
            records = extract_records(provider_req.provider, payload)
            request_rows.append(
                {
                    "provider": provider_req.provider,
                    "query": query,
                    "status": status,
                    "error": error or "",
                    "record_count": len(records),
                    "url": provider_req.url,
                    "raw_snippet": raw_snippet.replace("\n", " ")[:300],
                }
            )
            for idx, record in enumerate(records[:10]):
                text = as_text(record)
                flags = flags_for_text(text)
                required_hit = (
                    flags["mainregimev2"]
                    or flags["source_panel"]
                    or flags["native_subhour"]
                    or flags["oystacher"]
                    or flags["owner_export"]
                    or (flags["matched_control"] and flags["oystacher"])
                )
                broad_context_hit = flags["crisis"] or flags["recency"]
                candidate_rows.append(
                    {
                        "provider": provider_req.provider,
                        "query": query,
                        "rank": idx + 1,
                        "title": record_title(provider_req.provider, record),
                        "url": record_url(provider_req.provider, record),
                        "required_hit": required_hit,
                        "broad_context_hit": broad_context_hit,
                        "mainregimev2_hit": flags["mainregimev2"],
                        "source_panel_hit": flags["source_panel"],
                        "native_subhour_hit": flags["native_subhour"],
                        "crisis_hit": flags["crisis"],
                        "oystacher_hit": flags["oystacher"],
                        "matched_control_hit": flags["matched_control"],
                        "owner_export_hit": flags["owner_export"],
                        "recency_hint": flags["recency"],
                        "excerpt": " ".join(text.split())[:500],
                    }
                )
            time.sleep(0.25)

    required_hits = [row for row in candidate_rows if row["required_hit"]]
    broad_context_hits = [row for row in candidate_rows if row["broad_context_hit"] and not row["required_hit"]]
    mainregime_hits = [row for row in candidate_rows if row["mainregimev2_hit"]]
    r3_hits = [row for row in candidate_rows if row["native_subhour_hit"] and row["crisis_hit"]]
    r5_hits = [
        row
        for row in candidate_rows
        if row["recency_hint"] and (row["mainregimev2_hit"] or row["source_panel_hit"])
    ]
    r6_hits = [
        row
        for row in candidate_rows
        if row["oystacher_hit"] and (row["matched_control_hit"] or row["owner_export_hit"])
    ]

    # Public dataset-hub metadata is discovery evidence only. Unlock stays false
    # unless the route yields verifier-native files under the required roots.
    r6_owner_export_unlock = False
    r5_recency_unlock = False
    r3_native_subhour_unlock = False
    valid_required_root_unlock = False
    source_control_evidence_acquired = False

    summary = {
        "run_id": RUN_ID,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "board_hash_before_artifact": board_hash_before,
        "gate_result": "public_dataset_hub_source_route_probe_after_075420_v1=no_required_source_control_unlock",
        "queries": QUERIES,
        "providers": sorted({req["provider"] for req in request_rows}),
        "request_count": len(request_rows),
        "failed_or_parse_failed_request_count": sum(1 for row in request_rows if row["error"]),
        "top_metadata_rows_scanned": len(candidate_rows),
        "required_metadata_hits": len(required_hits),
        "broad_context_metadata_hits": len(broad_context_hits),
        "mainregimev2_hits": len(mainregime_hits),
        "r3_native_subhour_crisis_metadata_hits": len(r3_hits),
        "r5_recency_metadata_hits": len(r5_hits),
        "r6_oystacher_control_metadata_hits": len(r6_hits),
        "r6_owner_export_unlock": r6_owner_export_unlock,
        "r5_recency_unlock": r5_recency_unlock,
        "r3_native_subhour_unlock": r3_native_subhour_unlock,
        "valid_required_root_unlock": valid_required_root_unlock,
        "source_control_evidence_acquired": source_control_evidence_acquired,
        "accepted_rows_added": 0,
        "canonical_merge": False,
        "selected_data_autoquant_promotion": False,
        "downstream_promotion_rerun": False,
        "strict_full_objective": False,
        "trade_usable": False,
        "update_goal": False,
        "sample_required_hits": required_hits[:20],
        "sample_broad_context_hits": broad_context_hits[:20],
        "requests": request_rows,
    }

    json_path = ARTIFACT_DIR / "public_dataset_hub_source_route_probe_after_075420_v1.json"
    csv_path = ARTIFACT_DIR / "public_dataset_hub_source_route_candidates_v1.csv"
    req_csv_path = ARTIFACT_DIR / "public_dataset_hub_source_route_requests_v1.csv"
    report_path = ARTIFACT_DIR / "public_dataset_hub_source_route_probe_after_075420_v1.md"
    assertions_path = CHECK_DIR / "public_dataset_hub_source_route_probe_after_075420_v1_assertions.out"

    json_path.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")

    fieldnames = [
        "provider",
        "query",
        "rank",
        "title",
        "url",
        "required_hit",
        "broad_context_hit",
        "mainregimev2_hit",
        "source_panel_hit",
        "native_subhour_hit",
        "crisis_hit",
        "oystacher_hit",
        "matched_control_hit",
        "owner_export_hit",
        "recency_hint",
        "excerpt",
    ]
    with csv_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(candidate_rows)

    req_fieldnames = ["provider", "query", "status", "error", "record_count", "url", "raw_snippet"]
    with req_csv_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=req_fieldnames)
        writer.writeheader()
        writer.writerows(request_rows)

    report_lines = [
        "# Public Dataset Hub Source Route Probe After 075420 v1",
        "",
        f"Run id: `{RUN_ID}`",
        "",
        "Gate result: `public_dataset_hub_source_route_probe_after_075420_v1=no_required_source_control_unlock`",
        "",
        "## Scope",
        "",
        "Bounded public dataset-hub acquisition probe after the `075420` provider/cache sweep. It queries Hugging Face Datasets, Zenodo, Figshare, and the public Kaggle dataset-list endpoint for exact or near-exact R3/R5/R6 source/control terms. It does not mutate target roots, derive labels, approve controls, run direct verifier, split calibration, canonical merge, selected-data AutoQuant, filter / Pre-Bayes, BBN, CatBoost/path-ranking, execution-tree promotion, make a trade claim, or call `update_goal`.",
        "",
        "## Readback",
        "",
        f"- Board hash before artifact: `{board_hash_before['board_a']}`.",
        f"- Requests sent: `{summary['request_count']}`.",
        f"- Failed or parse-failed requests: `{summary['failed_or_parse_failed_request_count']}`.",
        f"- Top metadata rows scanned: `{summary['top_metadata_rows_scanned']}`.",
        f"- Required metadata hits: `{summary['required_metadata_hits']}`.",
        f"- Broad context-only metadata hits: `{summary['broad_context_metadata_hits']}`.",
        f"- `MainRegimeV2` hits: `{summary['mainregimev2_hits']}`.",
        f"- R3 native-subhour plus Crisis metadata hits: `{summary['r3_native_subhour_crisis_metadata_hits']}`.",
        f"- R5 recency metadata hits: `{summary['r5_recency_metadata_hits']}`.",
        f"- R6 Oystacher/control metadata hits: `{summary['r6_oystacher_control_metadata_hits']}`.",
        "",
        "## Decision",
        "",
        "No public dataset-hub route supplied verifier-native R6 owner/export positives with matched controls and approving provenance, source-owned post-`2026-01-30` R5 `MainRegimeV2` rows, verifier-native Crisis-capable R3 labels, or a genuinely new accepted cross-timeframe `MainRegimeV2` source export.",
        "",
        "Accepted rows added `0`; valid required-root unlock false; source/control evidence acquired false; canonical merge false; selected-data AutoQuant promotion false; downstream promotion rerun false; strict full objective false; trade usable false; `update_goal=false`.",
        "",
        "## Artifacts",
        "",
        f"- JSON: `{json_path.relative_to(REPO)}`",
        f"- Candidate CSV: `{csv_path.relative_to(REPO)}`",
        f"- Request CSV: `{req_csv_path.relative_to(REPO)}`",
        f"- Assertions: `{assertions_path.relative_to(REPO)}`",
        "",
        "## Next",
        "",
        "Continue source/control acquisition only before direct verifier, split calibration, canonical merge, selected-data AutoQuant, filter / Pre-Bayes, BBN, CatBoost/path-ranking, or execution-tree promotion.",
    ]
    report_path.write_text("\n".join(report_lines) + "\n", encoding="utf-8")

    assertion_lines = [
        "gate_result=public_dataset_hub_source_route_probe_after_075420_v1=no_required_source_control_unlock",
        f"request_count={summary['request_count']}",
        f"failed_or_parse_failed_request_count={summary['failed_or_parse_failed_request_count']}",
        f"top_metadata_rows_scanned={summary['top_metadata_rows_scanned']}",
        f"required_metadata_hits={summary['required_metadata_hits']}",
        f"broad_context_metadata_hits={summary['broad_context_metadata_hits']}",
        f"mainregimev2_hits={summary['mainregimev2_hits']}",
        f"r3_native_subhour_crisis_metadata_hits={summary['r3_native_subhour_crisis_metadata_hits']}",
        f"r5_recency_metadata_hits={summary['r5_recency_metadata_hits']}",
        f"r6_oystacher_control_metadata_hits={summary['r6_oystacher_control_metadata_hits']}",
        f"r6_owner_export_unlock={str(r6_owner_export_unlock).lower()}",
        f"r5_recency_unlock={str(r5_recency_unlock).lower()}",
        f"r3_native_subhour_unlock={str(r3_native_subhour_unlock).lower()}",
        f"valid_required_root_unlock={str(valid_required_root_unlock).lower()}",
        f"source_control_evidence_acquired={str(source_control_evidence_acquired).lower()}",
        "accepted_rows_added=0",
        "canonical_merge=false",
        "selected_data_autoquant_promotion=false",
        "downstream_promotion_rerun=false",
        "strict_full_objective=false",
        "trade_usable=false",
        "update_goal=false",
    ]
    assertions_path.write_text("\n".join(assertion_lines) + "\n", encoding="utf-8")

    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
