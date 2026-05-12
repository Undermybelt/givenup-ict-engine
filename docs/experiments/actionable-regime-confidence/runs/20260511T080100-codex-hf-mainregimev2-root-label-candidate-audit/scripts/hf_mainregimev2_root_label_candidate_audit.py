#!/usr/bin/env python3
"""Audit public Hugging Face dataset candidates for MainRegimeV2 labels.

This is a source-discovery audit only. It does not download raw market data and
does not treat dataset titles, tags, HMM states, or generated labels as accepted
source-backed root labels.
"""

from __future__ import annotations

import csv
import json
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO = Path("/Users/thrill3r/projects-ict-engine/ict-engine")
RUN_ID = "20260511T080100+0800-codex-hf-mainregimev2-root-label-candidate-audit"
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T080100-codex-hf-mainregimev2-root-label-candidate-audit"
OUT_DIR = RUN_ROOT / "hf-candidate-audit"
CHECK_DIR = RUN_ROOT / "checks"

HF_API = "https://huggingface.co/api/datasets"
SEARCHES = [
    # Hugging Face dataset search is repo-id weighted; broad terms give better
    # discovery than long natural-language phrases.
    "stock",
    "stocks",
    "crypto",
    "bitcoin",
    "btc",
    "nifty",
    "finance",
    "financial",
    "pump",
    "dump",
    "wash",
    "regime",
    "hmm",
    "market",
]
MAIN_ROOTS = ["Bull", "Bear", "Sideways", "Crisis"]
SEED_DATASETS = [
    # Prior Board A HF materialization candidates. Fetch metadata only here.
    "akashkumar5/Multi_Timeframe_Market_Regimes_HMM6_BTCUSD",
    "AAdevloper/nifty50-market-regime",
    "sujinwo/tsie-market-regime-dataset",
]


def rel(path: Path) -> str:
    return str(path.relative_to(REPO))


def get_json(url: str) -> Any:
    request = urllib.request.Request(url, headers={"User-Agent": "ict-engine-board-a-audit/1.0"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def search_hf(query: str) -> list[dict[str, Any]]:
    params = urllib.parse.urlencode({"search": query, "limit": 25})
    url = f"{HF_API}?{params}"
    payload = get_json(url)
    if isinstance(payload, list):
        return payload
    return []


def fetch_hf_dataset(dataset_id: str) -> dict[str, Any]:
    url = f"{HF_API}/{urllib.parse.quote(dataset_id, safe='/')}"
    payload = get_json(url)
    if isinstance(payload, dict):
        return payload
    return {}


def text_blob(item: dict[str, Any]) -> str:
    parts: list[str] = []
    for key in ["id", "description", "pretty_name"]:
        value = item.get(key)
        if isinstance(value, str):
            parts.append(value)
    tags = item.get("tags") or []
    if isinstance(tags, list):
        parts.extend(str(tag) for tag in tags)
    card_data = item.get("cardData") or {}
    if isinstance(card_data, dict):
        parts.append(json.dumps(card_data, sort_keys=True))
    return " ".join(parts).lower()


def classify_candidate(item: dict[str, Any], query: str) -> dict[str, Any]:
    blob = text_blob(item)
    dataset_id = item.get("id") or ""
    tags = item.get("tags") or []
    known_prior_materialization = dataset_id in SEED_DATASETS
    root_hits = {
        "Bull": any(term in blob for term in ["bull", "bullish", "expansion", "risk_on", "risk-on", "strong buy"]),
        "Bear": any(term in blob for term in ["bear", "bearish", "drawdown", "risk_off", "risk-off", "sell"]),
        "Sideways": any(term in blob for term in ["sideways", "range", "consolidation", "flat", "noise", "choppy", "squeeze"]),
        "Crisis": any(term in blob for term in ["crisis", "crash", "stress", "dislocation", "volatility spike"]),
    }
    manipulation_hits = any(term in blob for term in ["pump", "dump", "manipulation", "wash", "spoof", "layering"])
    explicit_label_terms = any(
        term in blob
        for term in ["label", "labels", "classification", "class", "regime", "risk_on", "risk_off", "hmm"]
    )
    market_terms = any(
        term in blob
        for term in [
            "stock",
            "market",
            "crypto",
            "bitcoin",
            "btc",
            "nifty",
            "financial",
            "finance",
            "trading",
            "token",
            "coin",
            "orderbook",
            "l2",
            "derivative",
        ]
    )
    has_all_roots = all(root_hits.values())

    if has_all_roots and explicit_label_terms and market_terms:
        status = "candidate_needs_manual_schema_fetch"
        reason = "metadata_mentions_all_roots_and_labels_but_no_schema_verified"
    elif manipulation_hits and explicit_label_terms and market_terms:
        status = "manipulation_candidate_only"
        reason = "may help direct Manipulation evidence, not four-root bar-label panel"
    elif market_terms and explicit_label_terms:
        status = "partial_or_ambiguous_market_label_candidate"
        reason = "market label metadata found but not full Bull/Bear/Sideways/Crisis roots"
    elif known_prior_materialization:
        status = "prior_materialized_sidecar_candidate"
        reason = "known prior HF sidecar candidate, but not full Bull/Bear/Sideways/Crisis panel"
    else:
        status = "not_a_full_root_label_panel"
        reason = "metadata does not evidence a full independent MainRegimeV2 label panel"

    return {
        "query": query,
        "dataset_id": dataset_id,
        "url": f"https://huggingface.co/datasets/{dataset_id}" if dataset_id else "",
        "likes": item.get("likes", 0),
        "downloads": item.get("downloads", 0),
        "last_modified": item.get("lastModified", ""),
        "tags": "|".join(str(tag) for tag in tags[:20]) if isinstance(tags, list) else "",
        "root_hits": root_hits,
        "manipulation_hit": manipulation_hits,
        "explicit_label_terms": explicit_label_terms,
        "market_terms": market_terms,
        "known_prior_materialization": known_prior_materialization,
        "status": status,
        "reason": reason,
        "accepted_for_board_a": False,
    }


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)

    dedup: dict[str, dict[str, Any]] = {}
    query_errors: list[dict[str, str]] = []
    for query in SEARCHES:
        try:
            for item in search_hf(query):
                dataset_id = item.get("id") or ""
                if not dataset_id:
                    continue
                row = classify_candidate(item, query)
                if dataset_id in dedup:
                    dedup[dataset_id]["query"] += f"|{query}"
                    continue
                dedup[dataset_id] = row
            time.sleep(0.2)
        except Exception as exc:  # noqa: BLE001 - audit must preserve exact remote failure
            query_errors.append({"query": query, "error": f"{type(exc).__name__}: {exc}"})

    for dataset_id in SEED_DATASETS:
        try:
            item = fetch_hf_dataset(dataset_id)
            if not item.get("id"):
                item["id"] = dataset_id
            row = classify_candidate(item, f"seed:{dataset_id}")
            if dataset_id in dedup:
                dedup[dataset_id]["query"] += f"|seed:{dataset_id}"
                dedup[dataset_id]["known_prior_materialization"] = True
                continue
            dedup[dataset_id] = row
            time.sleep(0.2)
        except Exception as exc:  # noqa: BLE001 - audit must preserve exact remote failure
            query_errors.append({"query": f"seed:{dataset_id}", "error": f"{type(exc).__name__}: {exc}"})

    rows = sorted(dedup.values(), key=lambda row: (row["status"], -int(row.get("downloads") or 0), row["dataset_id"]))
    status_counts: dict[str, int] = {}
    for row in rows:
        status_counts[row["status"]] = status_counts.get(row["status"], 0) + 1

    accepted_candidates = [row for row in rows if row["accepted_for_board_a"]]
    manual_schema_candidates = [row for row in rows if row["status"] == "candidate_needs_manual_schema_fetch"]
    manipulation_candidates = [row for row in rows if row["status"] == "manipulation_candidate_only"]

    report = {
        "run_id": RUN_ID,
        "goal_achieved": False,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "objective": "Audit public Hugging Face dataset candidates for an independent MainRegimeV2 four-root label panel.",
        "source": {
            "api": HF_API,
            "searches": SEARCHES,
            "raw_dataset_committed": False,
        },
        "main_roots_required": MAIN_ROOTS,
        "dataset_candidates_seen": len(rows),
        "query_error_count": len(query_errors),
        "status_counts": status_counts,
        "accepted_candidates": len(accepted_candidates),
        "manual_schema_candidates": len(manual_schema_candidates),
        "manipulation_candidates": len(manipulation_candidates),
        "rows": rows,
        "query_errors": query_errors,
        "completion_accounting": {
            "accepted_full_cycle_full_universe": False,
            "why_not_accepted": [
                "No Hugging Face metadata result is accepted as an independent full MainRegimeV2 label panel.",
                "Metadata/title/tag matches are not enough to prove symbol/timeframe-attached Bull/Bear/Sideways/Crisis labels.",
                "Manipulation candidates are direct-event side evidence only and cannot complete bar price roots.",
                "Any promising candidate must be schema-fetched and attached to the root-label slot contract before calibration.",
            ],
        },
        "raw_ohlcv_committed": False,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "trade_usable": False,
        "gate_result": "blocked_hf_scan_no_accepted_full_root_label_panel",
        "next_action": "Schema-fetch any manual Hugging Face candidates if present; otherwise acquire an external labeled MainRegimeV2 panel outside HF or keep Board A blocked.",
        "artifacts": {
            "audit_json": rel(OUT_DIR / "hf_root_label_candidate_audit.json"),
            "audit_md": rel(OUT_DIR / "hf_root_label_candidate_audit.md"),
            "audit_csv": rel(OUT_DIR / "hf_root_label_candidate_audit.csv"),
            "assertions": rel(CHECK_DIR / "hf_root_label_candidate_audit_assertions.out"),
            "script": rel(Path(__file__)),
        },
    }

    (OUT_DIR / "hf_root_label_candidate_audit.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    with (OUT_DIR / "hf_root_label_candidate_audit.csv").open("w", newline="") as handle:
        fieldnames = [
            "query",
            "dataset_id",
            "url",
            "likes",
            "downloads",
            "last_modified",
            "tags",
            "manipulation_hit",
            "explicit_label_terms",
            "market_terms",
            "status",
            "reason",
            "accepted_for_board_a",
        ]
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})

    lines = [
        "# Hugging Face Root Label Candidate Audit",
        "",
        f"Run id: `{RUN_ID}`",
        "",
        "Goal achieved: `false`",
        "",
        f"- Dataset candidates seen: `{len(rows)}`",
        f"- Accepted Board A candidates: `{len(accepted_candidates)}`",
        f"- Manual schema candidates: `{len(manual_schema_candidates)}`",
        f"- Manipulation-only candidates: `{len(manipulation_candidates)}`",
        f"- Query errors: `{len(query_errors)}`",
        "",
        "## Status Counts",
        "",
        "| Status | Count |",
        "|---|---:|",
    ]
    for status, count in sorted(status_counts.items()):
        lines.append(f"| `{status}` | {count} |")
    lines.extend(["", "## Manual Schema Candidates", ""])
    if manual_schema_candidates:
        for row in manual_schema_candidates[:20]:
            lines.append(f"- `{row['dataset_id']}`: {row['url']}")
    else:
        lines.append("- None.")
    lines.extend(["", "## Partial / Sidecar Candidates", ""])
    partial_candidates = [
        row
        for row in rows
        if row["status"]
        in {
            "partial_or_ambiguous_market_label_candidate",
            "prior_materialized_sidecar_candidate",
            "manipulation_candidate_only",
        }
    ]
    if partial_candidates:
        for row in partial_candidates[:25]:
            lines.append(f"- `{row['dataset_id']}` (`{row['status']}`): {row['reason']}")
    else:
        lines.append("- None.")
    lines.extend(
        [
            "",
            "## Accounting",
            "",
            "- No HF candidate is accepted as a full independent `Bull/Bear/Sideways/Crisis` label panel.",
            "- Metadata matches are source-discovery only; schema and label columns must be verified before calibration.",
            "- Runtime code changed: false. Thresholds relaxed: false. Trade usable: false.",
            "",
            "Gate result: `blocked_hf_scan_no_accepted_full_root_label_panel`",
        ]
    )
    (OUT_DIR / "hf_root_label_candidate_audit.md").write_text("\n".join(lines) + "\n")

    assertion_lines = [
        "goal_achieved=false",
        f"dataset_candidates_seen={len(rows)}",
        f"accepted_candidates={len(accepted_candidates)}",
        f"manual_schema_candidates={len(manual_schema_candidates)}",
        f"manipulation_candidates={len(manipulation_candidates)}",
        f"query_error_count={len(query_errors)}",
        "accepted_full_cycle_full_universe=false",
        "raw_ohlcv_committed=false",
        "runtime_code_changed=false",
        "thresholds_relaxed=false",
        "trade_usable=false",
        "gate_result=blocked_hf_scan_no_accepted_full_root_label_panel",
    ]
    for status, count in sorted(status_counts.items()):
        assertion_lines.append(f"status.{status}={count}")
    (CHECK_DIR / "hf_root_label_candidate_audit_assertions.out").write_text("\n".join(assertion_lines) + "\n")
    print(rel(OUT_DIR / "hf_root_label_candidate_audit.json"))


if __name__ == "__main__":
    main()
