#!/usr/bin/env python3
"""Public code-host source/control route probe for Board B.

This is source/control acquisition only. It searches public code-host metadata
and code-search endpoints for exact R3/R5/R6 artifact names and owner-export
terms. It never promotes hits from metadata or code snippets into accepted
source/control rows.
"""

from __future__ import annotations

import csv
import datetime as dt
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


RUN_ID = "20260512T074424+0800-codex-public-codehost-source-route-probe-after-074116-v1"
RUN_ROOT = Path("docs/experiments/actionable-regime-confidence/runs") / RUN_ID
PACKET_DIR = RUN_ROOT / "public-codehost-source-route-probe-after-074116-v1"
RAW_DIR = RUN_ROOT / "command-output"
CHECK_DIR = RUN_ROOT / "checks"

QUERIES = [
    ("mainregimev2_exact", '"MainRegimeV2"', "r5_r3_exact"),
    ("mainregimev2_crisis_exact", '"MainRegimeV2" "Crisis"', "r3_exact"),
    ("native_subhour_rows_exact", '"native_subhour_source_label_rows"', "r3_exact"),
    ("native_subhour_label_exact", '"native subhour source label"', "r3_exact"),
    ("stock_market_regimes_extension_exact", '"stock_market_regimes_2026_extension"', "r5_exact"),
    ("stock_market_regimes_2026_exact", '"stock market regimes 2026"', "r5_context"),
    ("positive_filename_exact", '"direct_manipulation_positive_rows"', "required_filename"),
    ("controls_filename_exact", '"direct_manipulation_matched_controls"', "required_filename"),
    ("provenance_filename_exact", '"direct_manipulation_provenance"', "required_filename"),
    ("oystacher_3red_exact", '"Oystacher" "3Red Trading"', "r6_owner"),
    ("oystacher_order_lifecycle", '"Oystacher" "order lifecycle"', "r6_owner_context"),
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
R3_TERMS = ["native_subhour_source_label_rows", "native subhour source label"]
CRISIS_TERMS = ["Crisis"]
R5_TERMS = ["stock_market_regimes_2026_extension", "stock market regimes 2026"]
R6_TERMS = [
    "direct_manipulation_positive_rows",
    "direct_manipulation_matched_controls",
    "direct_manipulation_provenance",
]


def fetch(url: str, *, headers: dict[str, str] | None = None, timeout: int = 25) -> tuple[int | None, bytes, str | None]:
    req_headers = {
        "User-Agent": "ict-engine-board-b-codehost-source-probe/1.0",
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


def records_from_grep_app(payload: bytes) -> tuple[list[dict[str, object]], int | None]:
    obj = json.loads(payload.decode("utf-8", errors="replace"))
    hits = obj.get("hits") or {}
    total = hits.get("total")
    records: list[dict[str, object]] = []
    for hit in (hits.get("hits") or [])[:10]:
        repo = hit.get("repo") or {}
        records.append(
            {
                "repo": repo.get("raw") or repo.get("name"),
                "branch": hit.get("branch"),
                "path": (hit.get("path") or {}).get("raw") if isinstance(hit.get("path"), dict) else hit.get("path"),
                "content": (hit.get("content") or {}).get("snippet") if isinstance(hit.get("content"), dict) else "",
                "url": hit.get("url"),
            }
        )
    return records, int(total) if isinstance(total, int) else None


def records_from_github_repositories(payload: bytes) -> tuple[list[dict[str, object]], int | None]:
    obj = json.loads(payload.decode("utf-8", errors="replace"))
    total = obj.get("total_count")
    records: list[dict[str, object]] = []
    for item in (obj.get("items") or [])[:10]:
        records.append(
            {
                "full_name": item.get("full_name"),
                "description": item.get("description"),
                "html_url": item.get("html_url"),
                "updated_at": item.get("updated_at"),
                "pushed_at": item.get("pushed_at"),
                "stargazers_count": item.get("stargazers_count"),
            }
        )
    return records, int(total) if isinstance(total, int) else None


def records_from_github_code(payload: bytes) -> tuple[list[dict[str, object]], int | None]:
    obj = json.loads(payload.decode("utf-8", errors="replace"))
    total = obj.get("total_count")
    records: list[dict[str, object]] = []
    for item in (obj.get("items") or [])[:10]:
        repo = item.get("repository") or {}
        records.append(
            {
                "name": item.get("name"),
                "path": item.get("path"),
                "html_url": item.get("html_url"),
                "repo": repo.get("full_name"),
                "repo_url": repo.get("html_url"),
            }
        )
    return records, int(total) if isinstance(total, int) else None


def records_from_gitlab_projects(payload: bytes) -> tuple[list[dict[str, object]], int | None]:
    obj = json.loads(payload.decode("utf-8", errors="replace"))
    if not isinstance(obj, list):
        return [], None
    records: list[dict[str, object]] = []
    for item in obj[:10]:
        records.append(
            {
                "path_with_namespace": item.get("path_with_namespace"),
                "description": item.get("description"),
                "web_url": item.get("web_url"),
                "last_activity_at": item.get("last_activity_at"),
                "star_count": item.get("star_count"),
            }
        )
    return records, len(obj)


def provider_requests(query: str) -> list[dict[str, object]]:
    encoded = urllib.parse.quote_plus(query)
    github_repo_q = urllib.parse.quote_plus(f"{query} in:name,description")
    github_code_q = urllib.parse.quote_plus(f"{query} in:file")
    gitlab_q = urllib.parse.quote_plus(query.replace('"', ""))
    return [
        {
            "provider": "grep_app",
            "url": f"https://grep.app/api/search?q={encoded}&page=1&per_page=10",
            "parser": records_from_grep_app,
            "note": "Public GitHub code index search.",
        },
        {
            "provider": "github_repositories",
            "url": f"https://api.github.com/search/repositories?q={github_repo_q}&per_page=10",
            "parser": records_from_github_repositories,
            "note": "Repository metadata only; code contents are not accepted as source rows.",
        },
        {
            "provider": "github_code",
            "url": f"https://api.github.com/search/code?q={github_code_q}&per_page=10",
            "parser": records_from_github_code,
            "note": "Unauthenticated GitHub code search may be blocked; blocked status is recorded.",
        },
        {
            "provider": "gitlab_projects",
            "url": f"https://gitlab.com/api/v4/search?scope=projects&search={gitlab_q}",
            "parser": records_from_gitlab_projects,
            "note": "Project metadata only; no authenticated blob search.",
        },
    ]


def main() -> int:
    PACKET_DIR.mkdir(parents=True, exist_ok=True)
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)
    (RAW_DIR / "run_id.txt").write_text(RUN_ID + "\n", encoding="utf-8")
    (RAW_DIR / "run_root.txt").write_text(str(RUN_ROOT) + "\n", encoding="utf-8")

    rows: list[dict[str, object]] = []
    request_count = 0
    failed_count = 0
    top_rows_scanned = 0
    required_filename_hits = 0
    owner_hits = 0
    mainregime_hits = 0
    r3_hits = 0
    crisis_context_hits = 0
    r5_hits = 0
    r6_hits = 0
    nonzero_search_total_count = 0

    for slug, query, target in QUERIES:
        for spec in provider_requests(query):
            provider = str(spec["provider"])
            raw_name = f"{provider}_{slug}"
            url = str(spec["url"])
            request_count += 1
            status, payload, error = fetch(url)
            write_raw(raw_name, "url", url + "\n")
            write_raw(raw_name, "status", f"{status}\n")
            if error:
                write_raw(raw_name, "error", error + "\n")
            if payload:
                write_raw(raw_name, "json", payload)

            records: list[dict[str, object]] = []
            total_count: int | None = None
            parse_error = ""
            if status == 200 and payload:
                try:
                    records, total_count = spec["parser"](payload)  # type: ignore[misc]
                except Exception as exc:
                    parse_error = repr(exc)
                    write_raw(raw_name, "parse_error", parse_error + "\n")
            else:
                failed_count += 1

            if parse_error:
                failed_count += 1

            top_rows_scanned += len(records)
            if total_count and total_count > 0:
                nonzero_search_total_count += 1

            required_hit = has_any(records, REQUIRED_FILENAMES) or (
                target in {"required_filename", "r3_exact", "r5_exact"} and bool(total_count)
            )
            owner_hit = has_any(records, OWNER_TERMS) or (target.startswith("r6_owner") and bool(total_count))
            mainregime_hit = has_any(records, MAINREGIME_TERMS) or ("mainregimev2" in slug and bool(total_count))
            r3_hit = has_any(records, R3_TERMS) or ("native_subhour" in slug and bool(total_count))
            crisis_hit = has_any(records, CRISIS_TERMS) or ("crisis" in slug and bool(total_count))
            r5_hit = has_any(records, R5_TERMS) or ("stock_market_regimes" in slug and bool(total_count))
            r6_hit = has_any(records, R6_TERMS) or (target == "required_filename" and bool(total_count))

            required_filename_hits += int(required_hit)
            owner_hits += int(owner_hit)
            mainregime_hits += int(mainregime_hit)
            r3_hits += int(r3_hit)
            crisis_context_hits += int(crisis_hit)
            r5_hits += int(r5_hit)
            r6_hits += int(r6_hit)

            rows.append(
                {
                    "provider": provider,
                    "query_slug": slug,
                    "target": target,
                    "query": query,
                    "status": status,
                    "error": error or "",
                    "parse_error": parse_error,
                    "top_record_count": len(records),
                    "total_count": total_count if total_count is not None else "",
                    "required_filename_hit": required_hit,
                    "owner_hit": owner_hit,
                    "mainregime_hit": mainregime_hit,
                    "r3_hit": r3_hit,
                    "crisis_context_hit": crisis_hit,
                    "r5_hit": r5_hit,
                    "r6_hit": r6_hit,
                    "top_records": json.dumps(records[:3], ensure_ascii=False, sort_keys=True),
                    "url": url,
                    "note": spec["note"],
                }
            )
            time.sleep(0.15)

    accepted_rows_added = 0
    valid_required_root_unlock = False
    source_control_evidence_acquired = False
    canonical_merge = False
    downstream_promotion_rerun = False
    strict_full_objective = False
    trade_usable = False
    gate_result = "public_codehost_source_route_probe_after_074116_v1=no_required_source_export_no_unlock"

    csv_path = PACKET_DIR / "public_codehost_source_route_probe_after_074116_v1.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    summary = {
        "run_id": RUN_ID,
        "generated_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "gate_result": gate_result,
        "requests_sent": request_count,
        "failed_or_blocked_requests": failed_count,
        "top_rows_scanned": top_rows_scanned,
        "nonzero_search_total_count": nonzero_search_total_count,
        "required_filename_hits": required_filename_hits,
        "owner_hits": owner_hits,
        "mainregime_hits": mainregime_hits,
        "r3_hits": r3_hits,
        "crisis_context_hits": crisis_context_hits,
        "r5_hits": r5_hits,
        "r6_hits": r6_hits,
        "accepted_rows_added": accepted_rows_added,
        "valid_required_root_unlock": valid_required_root_unlock,
        "source_control_evidence_acquired": source_control_evidence_acquired,
        "canonical_merge": canonical_merge,
        "downstream_promotion_rerun": downstream_promotion_rerun,
        "strict_full_objective": strict_full_objective,
        "trade_usable": trade_usable,
        "update_goal": False,
        "surfaces": [
            "grep.app public GitHub code index API",
            "GitHub repository search API",
            "GitHub code search API availability/readback",
            "GitLab public project search API",
        ],
        "non_promotion_reason": [
            "Public code-host metadata/code-search hits are discovery evidence only.",
            "No complete verifier-native R6 owner/export packet with valid controls was acquired.",
            "No source-owned post-2026-01-30 R5 source-panel recency root was acquired.",
            "No verifier-native Crisis-capable R3 MainRegimeV2 row export was acquired.",
            "No canonical merge, selected-data AutoQuant, filter/Pre-Bayes, BBN, CatBoost/path-ranking, or execution-tree promotion rerun was allowed.",
        ],
    }
    json_path = PACKET_DIR / "public_codehost_source_route_probe_after_074116_v1.json"
    json_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    md_path = PACKET_DIR / "public_codehost_source_route_probe_after_074116_v1.md"
    md_path.write_text(
        "\n".join(
            [
                "# Public Codehost Source Route Probe After 074116 v1",
                "",
                f"Run id: `{RUN_ID}`",
                "",
                f"Gate result: `{gate_result}`",
                "",
                "## Scope",
                "",
                "Source/control acquisition only after the `074116` manual R3 settlement. This packet searches public code-host surfaces for exact R3/R5/R6 artifact names and owner-export terms. It does not mutate target roots, approve code-host hits as source/control rows, run direct verifier, split calibration, canonical merge, selected-data AutoQuant, filter / Pre-Bayes, BBN, CatBoost/path-ranking, execution-tree promotion, make a trade claim, or call `update_goal`.",
                "",
                "## Public Surfaces Queried",
                "",
                "- grep.app public GitHub code index API",
                "- GitHub repository search API",
                "- GitHub code search API availability/readback",
                "- GitLab public project search API",
                "",
                "## Summary",
                "",
                f"- Requests sent: `{request_count}`",
                f"- Failed or blocked requests: `{failed_count}`",
                f"- Top records scanned: `{top_rows_scanned}`",
                f"- Nonzero provider search totals: `{nonzero_search_total_count}`",
                f"- Required filename hits: `{required_filename_hits}`",
                f"- Owner hits: `{owner_hits}`",
                f"- `MainRegimeV2` hits: `{mainregime_hits}`",
                f"- R3 native-subhour hits: `{r3_hits}`",
                f"- Crisis-context hits: `{crisis_context_hits}`",
                f"- R5 recency hits: `{r5_hits}`",
                f"- R6 filename/owner hits: `{r6_hits}`",
                "",
                "## Decision",
                "",
                "No required source/control root unlocked. Public code-host hits, if any, are discovery metadata/code-snippet evidence only and are not accepted as verifier-native R6 owner/export positives plus matched controls, source-owned post-`2026-01-30` R5 source-panel rows, verifier-native Crisis-capable R3 `MainRegimeV2` labels, or explicit source/control approval.",
                "",
                f"Accepted rows added `{accepted_rows_added}`; valid required-root unlock false; source/control evidence acquired false; canonical merge false; downstream promotion rerun false; strict full objective false; trade usable false; `update_goal=false`.",
                "",
                "## Artifacts",
                "",
                f"- CSV: `{csv_path}`",
                f"- JSON: `{json_path}`",
                f"- Assertions: `{CHECK_DIR / 'public_codehost_source_route_probe_after_074116_v1_assertions.out'}`",
                "",
                "## Next",
                "",
                "Continue only from explicit source/control approval, verifier-native R6 owner-export rows with valid controls, source-owned post-`2026-01-30` R5 rows matching the source-panel schema, verifier-native Crisis-capable R3 `MainRegimeV2` labels, or a genuinely new accepted cross-timeframe `MainRegimeV2` source export before direct verifier, split calibration, canonical merge, selected-data AutoQuant, filter / Pre-Bayes, BBN, CatBoost/path-ranking, or execution-tree promotion.",
                "",
            ]
        ),
        encoding="utf-8",
    )

    assertions = "\n".join(
        [
            gate_result,
            f"requests_sent={request_count}",
            f"failed_or_blocked_requests={failed_count}",
            f"top_rows_scanned={top_rows_scanned}",
            f"nonzero_search_total_count={nonzero_search_total_count}",
            f"required_filename_hits={required_filename_hits}",
            f"owner_hits={owner_hits}",
            f"mainregime_hits={mainregime_hits}",
            f"r3_hits={r3_hits}",
            f"crisis_context_hits={crisis_context_hits}",
            f"r5_hits={r5_hits}",
            f"r6_hits={r6_hits}",
            "accepted_rows_added=0",
            "valid_required_root_unlock=false",
            "source_control_evidence_acquired=false",
            "canonical_merge=false",
            "downstream_promotion_rerun=false",
            "strict_full_objective=false",
            "trade_usable=false",
            "promotion_allowed=false",
            "update_goal=false",
            "",
        ]
    )
    (CHECK_DIR / "public_codehost_source_route_probe_after_074116_v1_assertions.out").write_text(
        assertions,
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
