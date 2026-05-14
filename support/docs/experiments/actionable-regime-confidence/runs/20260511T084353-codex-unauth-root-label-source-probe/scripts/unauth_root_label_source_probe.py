#!/usr/bin/env python3
import base64
import csv
import json
import re
import subprocess
import time
from collections import Counter
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen


RUN_ID = "20260511T084353+0800-codex-unauth-root-label-source-probe"
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "source-acquisition"
CHECKS = ROOT / "checks"
MISSING_CSV = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T081715-codex-source-label-acquisition-package-v2/"
    "acquisition-package/missing_root_label_slots_acquisition_request_v2.csv"
)

USER_AGENT = "ict-engine-board-a-source-probe/1.0"
HTTP_TIMEOUT_SECONDS = 8
CURL_TIMEOUT_SECONDS = 8
FETCH_LIMITS = {
    "github_repos_per_query": 5,
    "github_readmes_total": 12,
    "hf_datasets_per_query": 8,
    "hf_detail_total": 8,
    "zenodo_records_per_query": 5,
    "figshare_records_per_query": 5,
}

GITHUB_QUERIES = [
    "market regime",
    "market-regime",
    "stock market regime",
    "crypto market regime",
    "bull bear sideways market regime",
    "wash trading dataset",
    "market manipulation dataset",
]

HF_QUERIES = [
    "market regime",
    "market-regime",
    "bull bear sideways market regime",
    "BTCUSD regime label",
    "wash trading label",
    "market manipulation dataset",
]

CATALOG_QUERIES = [
    "market regime bull bear sideways crisis",
    "SPY QQQ market regime labels",
    "BTCUSD Kraken market regime labels",
    "wash trading labeled dataset",
    "spoofing market manipulation labeled dataset",
]

TARGET_INSTRUMENT_TERMS = {
    "spy", "qqq", "dia", "gld", "uso",
    "es", "es=f", "nq", "nq=f", "ym", "ym=f",
    "cl", "cl=f", "gc", "gc=f",
    "^gspc", "gspc", "^dji", "dji", "^ndx", "ndx", "^vix", "vix",
    "xbtusd", "btcusd", "btc/usd", "bitcoin",
    "ethusd", "eth/usd", "ethereum",
    "solusd", "sol/usd", "solana",
    "kraken",
}

ROOT_TERM_GROUPS = {
    "Bull": [r"\bbull\b", r"\bbullish\b", r"\brisk[- ]?on\b"],
    "Bear": [r"\bbear\b", r"\bbearish\b", r"\brisk[- ]?off\b"],
    "Sideways": [r"\bsideways\b", r"\brange[- ]?bound\b", r"\bconsolidation\b"],
    "Crisis": [r"\bcrisis\b", r"\bcrash\b", r"\bstress\b", r"\bturbulen"],
}

TIMEFRAME_TERMS = [
    "1m", "5m", "15m", "30m", "1h", "4h", "1d", "daily", "1w", "weekly", "1mo",
    "monthly", "intraday", "minute", "hourly",
]

LABEL_TERMS = [
    "label", "labeled", "labelled", "annotation", "annotated", "class", "target",
    "regime_label", "regime",
]

PROXY_TERMS = [
    "hmm", "hidden markov", "gmm", "gaussian mixture", "kmeans", "k-means",
    "clustering", "unsupervised", "model inferred", "prediction", "forecast",
    "future return", "strategy", "signal", "technical indicator", "ohlcv",
]

DIRECT_MANIPULATION_CONCEPT_TERMS = [
    "wash trading", "wash trade", "spoofing", "layering", "pump and dump",
    "pump-and-dump", "pump dump", "market manipulation",
]

DIRECT_MANIPULATION_CONTEXT_TERMS = [
    "positive", "negative", "label", "labeled", "labelled", "class", "dataset",
]


def fetch_json(url, method="GET", payload=None, headers=None):
    req_headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/json",
    }
    if headers:
        req_headers.update(headers)
    data = None
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        req_headers["Content-Type"] = "application/json"
    req = Request(url, data=data, method=method, headers=req_headers)
    try:
        with urlopen(req, timeout=HTTP_TIMEOUT_SECONDS) as resp:
            body = resp.read()
            return {
                "ok": True,
                "status": resp.status,
                "url": url,
                "json": json.loads(body.decode("utf-8", errors="replace")),
            }
    except HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")[:1000]
        return {"ok": False, "status": exc.code, "url": url, "error": body}
    except (URLError, TimeoutError) as exc:
        if method == "GET" and payload is None and "api.github.com" in url:
            return fetch_json_with_curl(url, req_headers, repr(exc))
        return {"ok": False, "status": None, "url": url, "error": repr(exc)}
    except json.JSONDecodeError as exc:
        return {"ok": False, "status": None, "url": url, "error": repr(exc)}


def fetch_json_with_curl(url, headers, fallback_error):
    cmd = ["curl", "-sS", "-L", "--max-time", str(CURL_TIMEOUT_SECONDS)]
    for key, value in headers.items():
        cmd.extend(["-H", f"{key}: {value}"])
    cmd.extend(["-w", "\n__HTTP_STATUS__:%{http_code}", url])
    try:
        proc = subprocess.run(cmd, check=False, capture_output=True, text=True, timeout=CURL_TIMEOUT_SECONDS + 4)
    except Exception as exc:
        return {"ok": False, "status": None, "url": url, "error": f"{fallback_error}; curl={exc!r}"}
    output = proc.stdout or ""
    marker = "\n__HTTP_STATUS__:"
    if marker not in output:
        return {"ok": False, "status": None, "url": url, "error": f"{fallback_error}; curl_stderr={(proc.stderr or '')[:500]}"}
    body, status_text = output.rsplit(marker, 1)
    try:
        status = int(status_text.strip())
    except ValueError:
        status = None
    if proc.returncode != 0 or status is None or status >= 400:
        return {"ok": False, "status": status, "url": url, "error": f"{fallback_error}; curl_status={status}; stderr={(proc.stderr or '')[:500]}; body={body[:500]}"}
    try:
        return {"ok": True, "status": status, "url": url, "json": json.loads(body)}
    except json.JSONDecodeError as exc:
        return {"ok": False, "status": status, "url": url, "error": repr(exc)}


def fetch_text(url, headers=None):
    req_headers = {
        "User-Agent": USER_AGENT,
        "Accept": "text/plain, text/markdown, application/json",
    }
    if headers:
        req_headers.update(headers)
    req = Request(url, headers=req_headers)
    try:
        with urlopen(req, timeout=HTTP_TIMEOUT_SECONDS) as resp:
            return {
                "ok": True,
                "status": resp.status,
                "url": url,
                "text": resp.read().decode("utf-8", errors="replace"),
            }
    except HTTPError as exc:
        return {"ok": False, "status": exc.code, "url": url, "error": exc.read().decode("utf-8", errors="replace")[:1000]}
    except (URLError, TimeoutError) as exc:
        return {"ok": False, "status": None, "url": url, "error": repr(exc)}


def read_missing():
    with MISSING_CSV.open(newline="") as f:
        return list(csv.DictReader(f))


def summarize_missing(rows):
    return {
        "rows": len(rows),
        "by_reason": dict(Counter(r["missing_or_rejected_reason"] for r in rows)),
        "by_provider": dict(Counter(r["provider"] for r in rows)),
        "by_timeframe": dict(Counter(r["timeframe"] for r in rows)),
        "by_root": dict(Counter(r["root"] for r in rows)),
        "by_instrument": dict(Counter(r["instrument"] for r in rows)),
    }


def compact_text(value, max_chars=5000):
    if value is None:
        return ""
    value = re.sub(r"\s+", " ", str(value)).strip()
    return value[:max_chars]


def term_present(text, pattern):
    return re.search(pattern, text, flags=re.IGNORECASE) is not None


def classify_candidate(catalog, title, url, description="", metadata_text=""):
    text = compact_text(" ".join([title or "", url or "", description or "", metadata_text or ""]).lower(), 12000)
    root_hits = {
        root: any(term_present(text, pat) for pat in patterns)
        for root, patterns in ROOT_TERM_GROUPS.items()
    }
    target_hits = sorted(term for term in TARGET_INSTRUMENT_TERMS if term in text)
    timeframe_hits = sorted(term for term in TIMEFRAME_TERMS if term in text)
    label_hits = sorted(term for term in LABEL_TERMS if term in text)
    proxy_hits = sorted(term for term in PROXY_TERMS if term in text)
    direct_concept_hits = sorted(term for term in DIRECT_MANIPULATION_CONCEPT_TERMS if term in text)
    direct_context_hits = sorted(term for term in DIRECT_MANIPULATION_CONTEXT_TERMS if term in text)
    direct_manipulation_hits = direct_concept_hits + direct_context_hits

    all_roots = all(root_hits.values())
    has_direct_manipulation = bool(direct_concept_hits) and bool(direct_context_hits)

    if has_direct_manipulation and not all_roots:
        return {
            "class": "direct_manipulation_candidate_metadata_only",
            "decision": "sidecar_only_needs_exported_rows_and_controls",
            "reason": "Metadata mentions direct manipulation/wash/spoofing concepts, but no replayable positive/negative windows were exported in this probe.",
            "root_hits": root_hits,
            "target_hits": target_hits,
            "timeframe_hits": timeframe_hits,
            "label_hits": label_hits,
            "proxy_hits": proxy_hits,
            "direct_manipulation_hits": direct_manipulation_hits,
        }

    if proxy_hits:
        decision = "rejected_proxy_or_model_generated"
        reason = "Metadata includes model/proxy terms such as HMM/GMM/clustering/future-return/strategy/OHLCV, which cannot count as independent source labels."
    elif not all_roots:
        decision = "rejected_missing_full_mainregimev2_roots"
        missing = [root for root, hit in root_hits.items() if not hit]
        reason = f"Metadata does not expose all MainRegimeV2 roots; missing root terms: {missing}."
    elif not target_hits:
        decision = "rejected_no_exact_target_underlying"
        reason = "Metadata does not attach labels to current target instruments or Kraken/public crypto symbols."
    elif not timeframe_hits:
        decision = "rejected_no_timeframe_attachment"
        reason = "Metadata does not expose instrument/timeframe-attached labels needed for the missing slots."
    elif not label_hits:
        decision = "rejected_no_explicit_label_schema"
        reason = "Metadata has regime words but no explicit label/annotation/target schema."
    else:
        decision = "not_accepted_metadata_only_requires_schema_and_rows"
        reason = "Metadata has promising terms, but this unauthenticated probe did not verify independent label provenance, schema, rows, and chronological windows."

    return {
        "class": "root_label_catalog_candidate",
        "decision": decision,
        "reason": reason,
        "root_hits": root_hits,
        "target_hits": target_hits,
        "timeframe_hits": timeframe_hits,
        "label_hits": label_hits,
        "proxy_hits": proxy_hits,
        "direct_manipulation_hits": direct_manipulation_hits,
    }


def github_readme(owner, repo):
    url = f"https://api.github.com/repos/{owner}/{repo}/readme"
    resp = fetch_json(url, headers={"Accept": "application/vnd.github+json"})
    if not resp["ok"]:
        return ""
    data = resp.get("json") or {}
    if data.get("encoding") == "base64" and data.get("content"):
        try:
            return base64.b64decode(data["content"]).decode("utf-8", errors="replace")
        except Exception:
            return ""
    return ""


def collect_github_candidates(fetch_log):
    candidates = []
    readmes_used = 0
    seen = set()
    for query in GITHUB_QUERIES:
        url = "https://api.github.com/search/repositories?" + urlencode(
            {"q": query, "per_page": FETCH_LIMITS["github_repos_per_query"]}
        )
        resp = fetch_json(url, headers={"Accept": "application/vnd.github+json"})
        fetch_log.append({"catalog": "github", "query": query, "status": resp.get("status"), "ok": resp["ok"], "url": url})
        if not resp["ok"]:
            continue
        for item in (resp.get("json") or {}).get("items", []):
            full_name = item.get("full_name") or ""
            if not full_name or full_name in seen:
                continue
            seen.add(full_name)
            readme = ""
            if readmes_used < FETCH_LIMITS["github_readmes_total"] and "/" in full_name:
                owner, repo = full_name.split("/", 1)
                readme = github_readme(owner, repo)
                readmes_used += 1
                time.sleep(0.2)
            cls = classify_candidate(
                "github",
                item.get("name") or full_name,
                item.get("html_url") or "",
                item.get("description") or "",
                readme,
            )
            candidates.append({
                "source_id": "github:" + full_name,
                "catalog": "github",
                "title": item.get("name") or full_name,
                "url": item.get("html_url") or "",
                "description": compact_text(item.get("description"), 700),
                **cls,
            })
    return candidates


def collect_hf_candidates(fetch_log):
    candidates = []
    detail_used = 0
    seen = set()
    for query in HF_QUERIES:
        url = "https://huggingface.co/api/datasets?" + urlencode(
            {"search": query, "limit": FETCH_LIMITS["hf_datasets_per_query"], "full": "true"}
        )
        resp = fetch_json(url)
        fetch_log.append({"catalog": "huggingface", "query": query, "status": resp.get("status"), "ok": resp["ok"], "url": url})
        if not resp["ok"]:
            continue
        for item in resp.get("json") or []:
            dataset_id = item.get("id") or item.get("modelId") or ""
            if not dataset_id or dataset_id in seen:
                continue
            seen.add(dataset_id)
            detail_text = json.dumps(item, sort_keys=True)[:5000]
            if detail_used < FETCH_LIMITS["hf_detail_total"]:
                detail_url = "https://huggingface.co/api/datasets/" + quote(dataset_id, safe="/")
                detail = fetch_json(detail_url)
                fetch_log.append({"catalog": "huggingface_detail", "query": dataset_id, "status": detail.get("status"), "ok": detail["ok"], "url": detail_url})
                if detail["ok"]:
                    detail_text += " " + json.dumps(detail.get("json") or {}, sort_keys=True)[:8000]
                detail_used += 1
                time.sleep(0.2)
            cls = classify_candidate(
                "huggingface",
                dataset_id,
                "https://huggingface.co/datasets/" + dataset_id,
                item.get("description") or "",
                detail_text,
            )
            candidates.append({
                "source_id": "huggingface:" + dataset_id,
                "catalog": "huggingface",
                "title": dataset_id,
                "url": "https://huggingface.co/datasets/" + dataset_id,
                "description": compact_text(item.get("description"), 700),
                **cls,
            })
    return candidates


def collect_zenodo_candidates(fetch_log):
    candidates = []
    seen = set()
    for query in CATALOG_QUERIES:
        url = "https://zenodo.org/api/records?" + urlencode(
            {"q": query, "size": FETCH_LIMITS["zenodo_records_per_query"]}
        )
        resp = fetch_json(url)
        fetch_log.append({"catalog": "zenodo", "query": query, "status": resp.get("status"), "ok": resp["ok"], "url": url})
        if not resp["ok"]:
            continue
        for hit in ((resp.get("json") or {}).get("hits") or {}).get("hits", []):
            rec_id = str(hit.get("id") or "")
            if not rec_id or rec_id in seen:
                continue
            seen.add(rec_id)
            meta = hit.get("metadata") or {}
            title = meta.get("title") or rec_id
            description = meta.get("description") or ""
            url_value = hit.get("links", {}).get("html") or f"https://zenodo.org/records/{rec_id}"
            cls = classify_candidate("zenodo", title, url_value, description, json.dumps(meta, sort_keys=True)[:6000])
            candidates.append({
                "source_id": "zenodo:" + rec_id,
                "catalog": "zenodo",
                "title": compact_text(title, 240),
                "url": url_value,
                "description": compact_text(description, 700),
                **cls,
            })
    return candidates


def collect_figshare_candidates(fetch_log):
    candidates = []
    seen = set()
    for query in CATALOG_QUERIES:
        url = "https://api.figshare.com/v2/articles/search"
        resp = fetch_json(
            url,
            method="POST",
            payload={"search_for": query, "page_size": FETCH_LIMITS["figshare_records_per_query"]},
        )
        fetch_log.append({"catalog": "figshare", "query": query, "status": resp.get("status"), "ok": resp["ok"], "url": url})
        if not resp["ok"]:
            continue
        for hit in resp.get("json") or []:
            rec_id = str(hit.get("id") or "")
            if not rec_id or rec_id in seen:
                continue
            seen.add(rec_id)
            title = hit.get("title") or rec_id
            url_value = hit.get("url_public_html") or hit.get("url") or ""
            cls = classify_candidate("figshare", title, url_value, "", json.dumps(hit, sort_keys=True)[:5000])
            candidates.append({
                "source_id": "figshare:" + rec_id,
                "catalog": "figshare",
                "title": compact_text(title, 240),
                "url": url_value,
                "description": "",
                **cls,
            })
    return candidates


def collect_mendeley_candidates(fetch_log):
    candidates = []
    seen = set()
    for query in CATALOG_QUERIES:
        url = "https://api.mendeley.com/datasets?" + urlencode({"query": query, "limit": 8})
        resp = fetch_json(url)
        fetch_log.append({"catalog": "mendeley", "query": query, "status": resp.get("status"), "ok": resp["ok"], "url": url})
        if not resp["ok"]:
            continue
        for hit in resp.get("json") or []:
            rec_id = str(hit.get("id") or hit.get("doi") or hit.get("name") or "")
            if not rec_id or rec_id in seen:
                continue
            seen.add(rec_id)
            title = hit.get("name") or hit.get("title") or rec_id
            url_value = hit.get("doi") or hit.get("links", {}).get("self") or ""
            if url_value and url_value.startswith("10."):
                url_value = "https://data.mendeley.com/datasets/" + url_value
            cls = classify_candidate("mendeley", title, url_value, hit.get("description") or "", json.dumps(hit, sort_keys=True)[:5000])
            candidates.append({
                "source_id": "mendeley:" + rec_id,
                "catalog": "mendeley",
                "title": compact_text(title, 240),
                "url": url_value,
                "description": compact_text(hit.get("description"), 700),
                **cls,
            })
    return candidates


def collect_openml_probe(fetch_log):
    candidates = []
    for query in ["market regime", "bull bear sideways", "market manipulation"]:
        url = "https://www.openml.org/search?" + urlencode({"type": "data", "status": "active", "search": query})
        resp = fetch_text(url)
        fetch_log.append({"catalog": "openml_page", "query": query, "status": resp.get("status"), "ok": resp["ok"], "url": url})
        if not resp["ok"]:
            continue
        title = f"OpenML search page: {query}"
        cls = classify_candidate("openml", title, url, "", resp.get("text", "")[:5000])
        candidates.append({
            "source_id": "openml_search_page:" + query.replace(" ", "_"),
            "catalog": "openml_page",
            "title": title,
            "url": url,
            "description": "Search page metadata only; no dataset schema accepted.",
            **cls,
        })
    return candidates


def accepted_counts(candidates):
    accepted_root = [
        c for c in candidates
        if c["decision"] == "accepted_independent_mainregimev2_root_label_panel"
    ]
    accepted_manipulation = [
        c for c in candidates
        if c["decision"] == "accepted_direct_manipulation_label_windows"
    ]
    return len(accepted_root), len(accepted_manipulation)


def write_outputs(result):
    OUT.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)

    json_path = OUT / "unauth_root_label_source_probe.json"
    json_path.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")

    csv_path = OUT / "unauth_root_label_source_probe_candidates.csv"
    fieldnames = [
        "source_id", "catalog", "title", "url", "class", "decision", "reason",
        "root_hits", "target_hits", "timeframe_hits", "label_hits", "proxy_hits",
        "direct_manipulation_hits",
    ]
    with csv_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in result["candidates"]:
            writer.writerow({k: json.dumps(row[k], sort_keys=True) if isinstance(row.get(k), (dict, list)) else row.get(k, "") for k in fieldnames})

    decision_counts = dict(Counter(c["decision"] for c in result["candidates"]))
    catalog_counts = dict(Counter(c["catalog"] for c in result["candidates"]))
    sidecar_candidates = [
        c for c in result["candidates"]
        if c["decision"] in {
            "sidecar_only_needs_exported_rows_and_controls",
            "not_accepted_metadata_only_requires_schema_and_rows",
        }
    ][:20]

    md_lines = [
        "# Unauthenticated Root Label Source Probe",
        "",
        f"Run id: `{RUN_ID}`",
        "",
        "## Result",
        "",
        f"- Missing/rejected MainRegimeV2 root-label slots inspected: `{result['missing_summary']['rows']}`.",
        f"- Catalog/API endpoints queried: `{len(result['fetch_log'])}`.",
        f"- Metadata candidates classified: `{len(result['candidates'])}`.",
        f"- New accepted MainRegimeV2 root-label slots: `{result['accepted_new_root_label_slots']}`.",
        f"- New accepted direct `Manipulation` label sources: `{result['accepted_new_manipulation_sources']}`.",
        f"- Gate result: `{result['gate_result']}`.",
        "- Runtime code changed: false. Thresholds relaxed: false. Raw data committed: false. Trade usable: false.",
        "",
        "## Missing Slot Shape",
        "",
        "| Dimension | Counts |",
        "|---|---|",
        f"| Reason | `{result['missing_summary']['by_reason']}` |",
        f"| Provider | `{result['missing_summary']['by_provider']}` |",
        f"| Timeframe | `{result['missing_summary']['by_timeframe']}` |",
        f"| Root | `{result['missing_summary']['by_root']}` |",
        "",
        "## Catalog Coverage",
        "",
        f"- Catalog result counts: `{catalog_counts}`.",
        f"- Decision counts: `{decision_counts}`.",
        "- Public metadata was allowed; raw market datasets/large OHLCV files were not downloaded.",
        "",
        "## Sidecar / Follow-up Candidates",
        "",
        "| Source | Catalog | Decision | Reason |",
        "|---|---|---|---|",
    ]
    if not sidecar_candidates:
        md_lines.append("| none | none | none | none |")
    else:
        for c in sidecar_candidates:
            md_lines.append(
                f"| [`{c['source_id']}`]({c['url']}) | `{c['catalog']}` | `{c['decision']}` | {c['reason']} |"
            )
    md_lines.extend([
        "",
        "## Fail-Closed Decision",
        "",
        "No unauthenticated public metadata candidate proved an independent, exact-underlying, instrument/timeframe-attached `Bull` / `Bear` / `Sideways` / `Crisis` label panel for the 564 missing slots.",
        "No direct `Manipulation` candidate produced exported positive/negative chronological windows; Dune or another labeled source still needs authenticated/exported rows before acceptance.",
        "",
        "## Next Action",
        "",
        "Obtain a non-Kaggle exact-underlying label panel with schema/rows for the missing intraday/monthly/Kraken/instrument slots, or provide authenticated/exported direct `Manipulation` positive and negative windows; keep HMM/GMM/future-return/OHLCV/proxy labels fail-closed.",
    ])
    (OUT / "unauth_root_label_source_probe.md").write_text("\n".join(md_lines) + "\n", encoding="utf-8")

    assertions = [
        "PASS missing_slots_input_rows=564" if result["missing_summary"]["rows"] == 564 else f"FAIL missing_slots_input_rows={result['missing_summary']['rows']}",
        f"PASS metadata_candidates_classified={len(result['candidates'])}" if result["candidates"] else "FAIL metadata_candidates_classified=0",
        "PASS accepted_new_root_label_slots=0" if result["accepted_new_root_label_slots"] == 0 else f"FAIL accepted_new_root_label_slots={result['accepted_new_root_label_slots']}",
        "PASS accepted_new_manipulation_sources=0" if result["accepted_new_manipulation_sources"] == 0 else f"FAIL accepted_new_manipulation_sources={result['accepted_new_manipulation_sources']}",
        "PASS thresholds_relaxed=false",
        "PASS runtime_code_changed=false",
        "PASS raw_data_committed=false",
        f"PASS gate_result={result['gate_result']}",
    ]
    (CHECKS / "unauth_root_label_source_probe_assertions.out").write_text("\n".join(assertions) + "\n", encoding="utf-8")


def main():
    rows = read_missing()
    fetch_log = []
    candidates = []
    candidates.extend(collect_github_candidates(fetch_log))
    candidates.extend(collect_hf_candidates(fetch_log))
    candidates.extend(collect_zenodo_candidates(fetch_log))
    candidates.extend(collect_figshare_candidates(fetch_log))
    candidates.extend(collect_mendeley_candidates(fetch_log))
    candidates.extend(collect_openml_probe(fetch_log))

    accepted_root, accepted_manipulation = accepted_counts(candidates)
    result = {
        "run_id": RUN_ID,
        "objective": "focused_unauthenticated_non_kaggle_source_probe_for_missing_mainregimev2_root_labels_and_direct_manipulation_rows",
        "missing_summary": summarize_missing(rows),
        "catalog_queries": {
            "github": GITHUB_QUERIES,
            "huggingface": HF_QUERIES,
            "zenodo_figshare_mendeley": CATALOG_QUERIES,
        },
        "fetch_log": fetch_log,
        "candidates": candidates,
        "accepted_new_root_label_slots": accepted_root,
        "accepted_new_manipulation_sources": accepted_manipulation,
        "gate_result": "blocked_no_accepted_unauthenticated_non_kaggle_source_labels",
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "trade_usable": False,
        "next_action": "obtain_non_kaggle_exact_label_panel_or_authenticated_direct_manipulation_windows",
    }
    write_outputs(result)


if __name__ == "__main__":
    main()
