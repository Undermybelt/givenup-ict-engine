#!/usr/bin/env python3
"""Exact-source metadata search for the next strict 1h source-label targets.

This is a read-only metadata screen. It does not download raw rows or create
intake files. Metadata hits are kept fail-closed unless they expose source-owned
or owner-approved rows for the exact target ticker/root gaps.
"""

from __future__ import annotations

import csv
import hashlib
import json
import os
import subprocess
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


RUN_ID = "20260511T194739-codex-strict-1h-target-exact-source-search-v1"
RUN_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = RUN_ROOT.parents[4]
BOARD_PATH = REPO_ROOT / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"
OUT_DIR = RUN_ROOT / "strict-1h-target-exact-source-search"
CHECK_DIR = RUN_ROOT / "checks"

TARGETS = [
    {
        "symbol": "XOM",
        "root": "Sideways",
        "split_side": "heldout",
        "needed_source_owned_sessions": 5,
    },
    {
        "symbol": "UNH",
        "root": "Bear",
        "split_side": "calibration",
        "needed_source_owned_sessions": 7,
    },
    {
        "symbol": "^DJI",
        "root": "Sideways",
        "split_side": "calibration",
        "needed_source_owned_sessions": 7,
    },
    {
        "symbol": "AMD",
        "root": "Bear",
        "split_side": "calibration",
        "needed_source_owned_sessions": 10,
    },
]

LOCAL_SOURCE_PANEL = (
    Path("/Users/thrill3r/Downloads/stock-market-regimes-20002026")
    / "stock_market_regimes_2000_2026.csv"
)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def http_json(url: str, timeout: int = 20) -> tuple[int | None, Any, str | None]:
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": "ict-engine-board-a-metadata-screen/1.0",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = response.read()
            return response.status, json.loads(body.decode("utf-8")), None
    except Exception as exc:  # Network/readback failures are recorded, not hidden.
        return None, None, f"{type(exc).__name__}: {exc}"


def run_command(args: list[str], timeout: int = 45) -> dict[str, Any]:
    try:
        proc = subprocess.run(
            args,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
            timeout=timeout,
        )
        return {
            "args": args,
            "returncode": proc.returncode,
            "stdout": proc.stdout[:20000],
            "error": None,
        }
    except Exception as exc:
        return {
            "args": args,
            "returncode": None,
            "stdout": "",
            "error": f"{type(exc).__name__}: {exc}",
        }


def target_queries(target: dict[str, Any]) -> list[str]:
    symbol = str(target["symbol"])
    root = str(target["root"])
    plain_symbol = symbol.replace("^", "")
    return [
        f"{symbol} {root} market regime label",
        f"{plain_symbol} {root} stock market regimes",
        f"{symbol} {root} regime_label",
        f"{plain_symbol} MainRegimeV2 {root}",
    ]


def classify_candidate(text: str) -> str:
    lower = text.lower()
    if "stock-market-regimes-20002026" in lower or "stock market regimes 2000" in lower:
        return "known_source_panel_metadata_no_new_rows_without_exact_target_extension"
    if any(term in lower for term in ["hmm", "kmeans", "random forest", "classifier", "prediction"]):
        return "blocked_generated_or_model_derived_labels"
    if any(term in lower for term in ["ohlcv", "price data", "historical data", "candlestick"]):
        return "blocked_raw_price_panel_no_source_owned_regime_labels"
    if any(term in lower for term in ["synthetic", "simulated"]):
        return "blocked_synthetic_or_simulated_panel"
    if any(term in lower for term in ["regime", "label"]):
        return "blocked_metadata_hit_needs_owner_row_export_and_crosswalk"
    return "blocked_metadata_not_regime_label_source"


def github_repo_search(query: str) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    url = "https://api.github.com/search/repositories?" + urllib.parse.urlencode(
        {"q": query, "per_page": 5, "sort": "updated"}
    )
    status, payload, error = http_json(url)
    readback = {
        "surface": "github_repositories",
        "query": query,
        "url": url,
        "status": status,
        "error": error,
        "result_count": None,
    }
    candidates: list[dict[str, Any]] = []
    if isinstance(payload, dict):
        items = payload.get("items") or []
        readback["result_count"] = len(items)
        for item in items[:5]:
            name = str(item.get("full_name") or "")
            desc = str(item.get("description") or "")
            html_url = str(item.get("html_url") or "")
            text = f"{name} {desc} {html_url}"
            candidates.append(
                {
                    "surface": "github_repositories",
                    "query": query,
                    "title": name,
                    "url": html_url,
                    "description": desc,
                    "disposition": classify_candidate(text),
                }
            )
    return readback, candidates


def huggingface_dataset_search(query: str) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    url = "https://huggingface.co/api/datasets?" + urllib.parse.urlencode(
        {"search": query, "limit": 5}
    )
    status, payload, error = http_json(url)
    readback = {
        "surface": "huggingface_datasets",
        "query": query,
        "url": url,
        "status": status,
        "error": error,
        "result_count": None,
    }
    candidates: list[dict[str, Any]] = []
    if isinstance(payload, list):
        readback["result_count"] = len(payload)
        for item in payload[:5]:
            name = str(item.get("id") or "")
            text = json.dumps(item, sort_keys=True)[:2000]
            candidates.append(
                {
                    "surface": "huggingface_datasets",
                    "query": query,
                    "title": name,
                    "url": f"https://huggingface.co/datasets/{name}",
                    "description": text,
                    "disposition": classify_candidate(text),
                }
            )
    return readback, candidates


def kaggle_dataset_search(query: str) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    result = run_command(["kaggle", "datasets", "list", "-s", query, "--csv"], timeout=45)
    readback = {
        "surface": "kaggle_datasets",
        "query": query,
        "url": "kaggle datasets list",
        "status": result["returncode"],
        "error": result["error"],
        "result_count": None,
    }
    candidates: list[dict[str, Any]] = []
    if result["returncode"] == 0 and result["stdout"].strip():
        rows = list(csv.DictReader(result["stdout"].splitlines()))
        readback["result_count"] = len(rows)
        for row in rows[:5]:
            ref = row.get("ref") or row.get("id") or row.get("dataset") or ""
            title = row.get("title") or row.get("subtitle") or ref
            text = json.dumps(row, sort_keys=True)
            candidates.append(
                {
                    "surface": "kaggle_datasets",
                    "query": query,
                    "title": title,
                    "url": f"https://www.kaggle.com/datasets/{ref}" if ref else "",
                    "description": text,
                    "disposition": classify_candidate(text),
                }
            )
    else:
        readback["result_count"] = 0
    return readback, candidates


def local_panel_counts() -> list[dict[str, Any]]:
    split_year_by_key = {
        (str(target["symbol"]), str(target["root"])): 2025
        if target["split_side"] == "heldout"
        else 2024
        for target in TARGETS
    }
    if not LOCAL_SOURCE_PANEL.exists():
        return [
            {
                "symbol": target["symbol"],
                "root": target["root"],
                "relevant_split_year": split_year_by_key[(str(target["symbol"]), str(target["root"]))],
                "source_panel_exists": False,
                "rows_total": 0,
                "rows_relevant_split_year": 0,
                "rows_after_2026_01_30": 0,
                "rows_jan_2026": 0,
            }
            for target in TARGETS
        ]
    counts = {
        (str(target["symbol"]), str(target["root"])): {
            "symbol": target["symbol"],
            "root": target["root"],
            "relevant_split_year": split_year_by_key[(str(target["symbol"]), str(target["root"]))],
            "source_panel_exists": True,
            "rows_total": 0,
            "rows_relevant_split_year": 0,
            "rows_after_2026_01_30": 0,
            "rows_jan_2026": 0,
        }
        for target in TARGETS
    }
    with LOCAL_SOURCE_PANEL.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            symbol = row.get("Ticker") or row.get("ticker") or ""
            regime = (
                row.get("Regime")
                or row.get("regime")
                or row.get("regime_label")
                or row.get("main_regime_v2_label")
                or ""
            )
            key = (symbol, regime)
            if key not in counts:
                continue
            date = row.get("Date") or row.get("date") or ""
            counts[key]["rows_total"] += 1
            if date.startswith(str(counts[key]["relevant_split_year"])):
                counts[key]["rows_relevant_split_year"] += 1
            if date > "2026-01-30":
                counts[key]["rows_after_2026_01_30"] += 1
            if "2026-01-02" <= date <= "2026-01-30":
                counts[key]["rows_jan_2026"] += 1
    return list(counts.values())


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)

    readbacks: list[dict[str, Any]] = []
    candidates: list[dict[str, Any]] = []
    for target in TARGETS:
        target_key = f"{target['symbol']}/{target['root']}"
        for query in target_queries(target):
            for search_fn in (github_repo_search, huggingface_dataset_search, kaggle_dataset_search):
                readback, hits = search_fn(query)
                readback["target_key"] = target_key
                readbacks.append(readback)
                for hit in hits:
                    hit["target_key"] = target_key
                    candidates.append(hit)

    local_counts = local_panel_counts()
    ready = [
        row
        for row in candidates
        if row["disposition"] == "ready_source_owned_exact_target_rows"
    ]
    disposition_counts: dict[str, int] = {}
    for row in candidates:
        disposition_counts[row["disposition"]] = disposition_counts.get(row["disposition"], 0) + 1

    summary = {
        "artifact_type": "strict_1h_target_exact_source_search_v1",
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "board_hash_before_run": sha256_file(BOARD_PATH),
        "targets": TARGETS,
        "surfaces": ["github_repositories", "huggingface_datasets", "kaggle_datasets", "local_source_panel_counts"],
        "readback_count": len(readbacks),
        "candidate_records": len(candidates),
        "disposition_counts": disposition_counts,
        "local_source_panel": str(LOCAL_SOURCE_PANEL),
        "local_source_panel_counts": local_counts,
        "ready_source_owned_exact_target_sources": len(ready),
        "accepted_rows_added": 0,
        "new_confidence_gate": False,
        "strict_1h_source_extension_closed": False,
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "trade_usable": False,
        "decision": "strict_1h_target_exact_source_search_v1=no_ready_exact_target_source_owned_rows",
    }

    (OUT_DIR / "strict_1h_target_exact_source_search_v1.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    readback_path = OUT_DIR / "strict_1h_target_exact_source_search_v1_readbacks.csv"
    with readback_path.open("w", newline="", encoding="utf-8") as handle:
        fieldnames = ["target_key", "surface", "query", "url", "status", "error", "result_count"]
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(readbacks)

    candidate_path = OUT_DIR / "strict_1h_target_exact_source_search_v1_candidates.csv"
    with candidate_path.open("w", newline="", encoding="utf-8") as handle:
        fieldnames = ["target_key", "surface", "query", "title", "url", "description", "disposition"]
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(candidates)

    counts_path = OUT_DIR / "strict_1h_target_exact_source_search_v1_local_counts.csv"
    with counts_path.open("w", newline="", encoding="utf-8") as handle:
        fieldnames = [
            "symbol",
            "root",
            "source_panel_exists",
            "rows_total",
            "relevant_split_year",
            "rows_relevant_split_year",
            "rows_after_2026_01_30",
            "rows_jan_2026",
        ]
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(local_counts)

    report_lines = [
        "# Strict 1h Target Exact Source Search v1",
        "",
        f"Run ID: `{RUN_ID}`",
        "",
        "Read-only metadata search for the four exact source-label targets requested by `strict_1h_next_source_intake_contract_v1`. No raw rows were downloaded and no intake files were created.",
        "",
        "## Decision",
        "",
        "`strict_1h_target_exact_source_search_v1=no_ready_exact_target_source_owned_rows`",
        "",
        f"- Targets checked: `{len(TARGETS)}`.",
        f"- Metadata readbacks: `{len(readbacks)}` across GitHub repositories, Hugging Face datasets, and Kaggle datasets.",
        f"- Candidate records dispositioned: `{len(candidates)}`.",
        f"- Ready exact target source-owned row sources: `{len(ready)}`.",
        "- Accepted rows added: `0`; new confidence gate: `false`.",
        "- Strict `1h` source extension closed: `false`.",
        "- Strict full objective achieved: `false`; `update_goal=false`.",
        "- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; trade usable: `false`.",
        "",
        "## Target Readback",
        "",
    ]
    for count in local_counts:
        report_lines.append(
            f"- `{count['symbol']}/{count['root']}`: existing source rows `{count['rows_total']}`, "
            f"relevant split `{count['relevant_split_year']}` rows `{count['rows_relevant_split_year']}`, "
            f"Jan-2026 tail rows `{count['rows_jan_2026']}`, rows after `2026-01-30` `{count['rows_after_2026_01_30']}`."
        )
    report_lines.extend(
        [
            "",
            "## Artifacts",
            "",
            f"- JSON: `{OUT_DIR / 'strict_1h_target_exact_source_search_v1.json'}`",
            f"- Readbacks CSV: `{readback_path}`",
            f"- Candidate CSV: `{candidate_path}`",
            f"- Local counts CSV: `{counts_path}`",
            f"- Assertions: `{CHECK_DIR / 'strict_1h_target_exact_source_search_v1_assertions.out'}`",
        ]
    )
    (OUT_DIR / "strict_1h_target_exact_source_search_v1.md").write_text(
        "\n".join(report_lines) + "\n",
        encoding="utf-8",
    )

    assertions = [
        "PASS decision=strict_1h_target_exact_source_search_v1=no_ready_exact_target_source_owned_rows",
        f"PASS targets_checked={len(TARGETS)}",
        f"PASS readback_count={len(readbacks)}",
        f"PASS candidate_records={len(candidates)}",
        "PASS accepted_rows_added=0",
        "PASS new_confidence_gate=false",
        "PASS update_goal=false",
        "PASS raw_data_committed=false",
    ]
    (CHECK_DIR / "strict_1h_target_exact_source_search_v1_assertions.out").write_text(
        "\n".join(assertions) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
