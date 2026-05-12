#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import zipfile
from pathlib import Path
from typing import Any
from urllib.parse import quote
from urllib.request import Request, urlopen


REPO = Path("/Users/thrill3r/projects-ict-engine/ict-engine")
RUN_ID = "20260511T041650+0800-codex-external-root-source-preflight"
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T041650-codex-external-root-source-preflight"
OUT_DIR = RUN_ROOT / "source-preflight"
CHECK_DIR = RUN_ROOT / "checks"
TMP_DIR = Path("/private/tmp/ict-regime-external-root-source-preflight")

KAGGLE_SEARCH_TERMS = [
    "market regimes",
    "bull bear sideways",
    "stock market regime",
    "bear market",
]
HF_SEARCH_TERMS = [
    "market regime",
    "bear bull sideways market regime",
    "sideways market regime dataset",
    "financial market regime labels",
]
NEW_KAGGLE_REF = "nickdatak/us-market-regimes-dataset-1995-2024"


def fetch_json(url: str) -> Any:
    request = Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urlopen(request, timeout=45) as response:
        return json.loads(response.read().decode("utf-8"))


def fetch_bytes(url: str) -> bytes:
    request = Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urlopen(request, timeout=90) as response:
        return response.read()


def kaggle_search() -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    seen: set[str] = set()
    for term in KAGGLE_SEARCH_TERMS:
        url = f"https://www.kaggle.com/api/v1/datasets/list?search={quote(term)}&page=1"
        for item in fetch_json(url)[:12]:
            ref = item.get("ref", "")
            if not ref or ref in seen:
                continue
            seen.add(ref)
            out.append(
                {
                    "source": "kaggle",
                    "search_term": term,
                    "ref": ref,
                    "title": item.get("title"),
                    "total_bytes": item.get("totalBytes"),
                    "download_count": item.get("downloadCount"),
                }
            )
    return out


def hf_search() -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    seen: set[str] = set()
    for term in HF_SEARCH_TERMS:
        url = f"https://huggingface.co/api/datasets?search={quote(term)}&limit=30&full=false"
        for item in fetch_json(url):
            ref = item.get("id", "")
            if not ref or ref in seen:
                continue
            seen.add(ref)
            out.append(
                {
                    "source": "huggingface",
                    "search_term": term,
                    "ref": ref,
                    "likes": item.get("likes"),
                    "downloads": item.get("downloads"),
                }
            )
    return out


def summarize_csv(path: Path) -> dict[str, Any]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        columns = reader.fieldnames or []
        row_count = 0
        label_counts: dict[str, dict[str, int]] = {}
        for row in reader:
            row_count += 1
            for column in columns:
                lowered = column.lower()
                if "regime" not in lowered and "label" not in lowered and "state" not in lowered:
                    continue
                value = row.get(column, "")
                label_counts.setdefault(column, {})
                label_counts[column][value] = label_counts[column].get(value, 0) + 1
    return {"path": str(path), "rows": row_count, "columns": columns, "label_counts": label_counts}


def download_and_summarize_new_kaggle() -> dict[str, Any]:
    TMP_DIR.mkdir(parents=True, exist_ok=True)
    meta = fetch_json(f"https://www.kaggle.com/api/v1/datasets/view/{NEW_KAGGLE_REF}")
    files_meta = fetch_json(f"https://www.kaggle.com/api/v1/datasets/list/{NEW_KAGGLE_REF}")
    zip_path = TMP_DIR / "us-market-regimes-1995-2024.zip"
    if not zip_path.exists() or zip_path.stat().st_size < 100_000:
        zip_path.write_bytes(fetch_bytes(f"https://www.kaggle.com/api/v1/datasets/download/{NEW_KAGGLE_REF}"))
    with zipfile.ZipFile(zip_path) as archive:
        archive.extractall(TMP_DIR)
    summaries = []
    for name in ["gmm_regimes.csv", "hmm_regimes.csv", "market_features_weekly.csv", "market_features_weekly_std.csv"]:
        path = TMP_DIR / name
        if path.exists():
            summaries.append(summarize_csv(path))
    return {
        "ref": NEW_KAGGLE_REF,
        "title": meta.get("title"),
        "description_excerpt": (meta.get("description") or "")[:900],
        "total_bytes": meta.get("totalBytes"),
        "download_count": meta.get("downloadCount"),
        "dataset_files": files_meta.get("datasetFiles", []),
        "zip_path": str(zip_path),
        "raw_committed_to_repo": False,
        "csv_summaries": summaries,
        "preflight_verdict": "not_completion_eligible_for_active_roots",
        "preflight_reasons": [
            "labels are unsupervised `Calm` / `Stressful` / `Transitional`, not active MainRegimeV3SourceBacked `BearExpansion` evidence",
            "single aggregate S&P 500 weekly market context and one timeframe cannot satisfy the board's multi-context root evidence requirement",
            "`Stressful` is crisis/stress provenance, not a directional `BearExpansion` root, and `Calm` is unnecessary for completion after the accepted `SidewaysConsolidation` reissue",
            "no direct event/order-lifecycle/L2/L3/MBO/social/on-chain manipulation evidence is present",
        ],
    }


def classify_candidate(item: dict[str, Any]) -> dict[str, Any]:
    ref = item["ref"]
    if ref == "mafaqbhatti/stock-market-regimes-20002026":
        state = "already_exhausted_in_board"
        reason = "existing Kaggle direct-label gates accepted `BullExpansion` only; `BearExpansion` remained below 95"
    elif ref == NEW_KAGGLE_REF:
        state = "downloaded_preflight_rejected"
        reason = "unsupervised Calm/Stressful/Transitional labels; one S&P weekly context"
    elif ref == "sujinwo/tsie-market-regime-dataset":
        state = "already_exhausted_in_board"
        reason = "TSIE direct-label gates stayed below 95 and had one market context"
    elif ref in {"AAdevloper/nifty50-market-regime", "akashkumar5/Multi_Timeframe_Market_Regimes_HMM6_BTCUSD"}:
        state = "candidate_not_completion_eligible_without_new_breadth"
        reason = "single-market/single-family public dataset; insufficient for active multi-context parent-root completion by itself"
    elif ref.startswith("ClarusC64/market-regime-"):
        state = "too_small_or_conceptual_mapping"
        reason = "mapping dataset, not calibration-grade market observations"
    else:
        state = "not_selected_this_loop"
        reason = "search hit is not direct BearExpansion evidence or a direct manipulation source"
    return item | {"preflight_state": state, "preflight_reason": reason}


def repo_rel(path: Path) -> str:
    return str(path.relative_to(REPO))


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)
    kaggle_hits = [classify_candidate(item) for item in kaggle_search()]
    hf_hits = [classify_candidate(item) for item in hf_search()]
    nickdatak = download_and_summarize_new_kaggle()

    selected_completion_candidates = [
        item
        for item in kaggle_hits + hf_hits
        if item["preflight_state"] not in {
            "already_exhausted_in_board",
            "downloaded_preflight_rejected",
            "candidate_not_completion_eligible_without_new_breadth",
            "too_small_or_conceptual_mapping",
            "not_selected_this_loop",
        }
    ]
    decision = {
        "gate_result": "blocked_external_source_preflight_no_completion_eligible_new_source",
        "accepted_new_roots_95": [],
        "accepted_root_classes_95_effective": ["BullExpansion", "SidewaysConsolidation", "CrisisCrash"],
        "missing_root_classes_95_effective": ["BearExpansion", "Manipulation"],
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "fresh_calibration_rerun": False,
        "raw_committed_to_repo": False,
        "trade_usable": False,
        "next_action": "Acquire genuinely directional BearExpansion evidence or direct manipulation event/order-lifecycle evidence; do not repeat Kaggle OHLCV/macro transforms.",
    }
    report = {
        "loop_id": RUN_ID,
        "objective": "Preflight newly discoverable external sources before spending another gate on duplicate or non-eligible evidence.",
        "search_policy": {
            "kaggle_search_terms": KAGGLE_SEARCH_TERMS,
            "huggingface_search_terms": HF_SEARCH_TERMS,
            "raw_download_root": str(TMP_DIR),
            "raw_committed_to_repo": False,
        },
        "kaggle_hits": kaggle_hits,
        "huggingface_hits": hf_hits,
        "downloaded_new_kaggle_source": nickdatak,
        "selected_completion_candidates": selected_completion_candidates,
        "decision": decision,
    }
    report_json = OUT_DIR / "external_root_source_preflight.json"
    report_md = OUT_DIR / "external_root_source_preflight.md"
    assertions = CHECK_DIR / "external_root_source_preflight_assertions.out"
    report["artifacts"] = {"report_json": repo_rel(report_json), "report_md": repo_rel(report_md), "assertions": repo_rel(assertions)}
    report_json.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")

    lines = [
        "# External Root Source Preflight",
        "",
        f"Run id: `{RUN_ID}`.",
        "",
        "## Decision",
        "",
        f"- Gate result: `{decision['gate_result']}`",
        "- Accepted new active roots: none",
        "- Missing active roots remain: `BearExpansion`, `Manipulation`",
        "- Raw external files stayed under `/private/tmp`; repo artifact is metadata/preflight only.",
        "",
        "## Newly Downloaded Candidate",
        "",
        f"- `{NEW_KAGGLE_REF}`: `{nickdatak['preflight_verdict']}`",
    ]
    for reason in nickdatak["preflight_reasons"]:
        lines.append(f"  - {reason}")
    lines.extend(["", "## Search Summary", ""])
    for label, hits in [("Kaggle", kaggle_hits), ("Hugging Face", hf_hits)]:
        lines.append(f"### {label}")
        for item in hits[:12]:
            lines.append(f"- `{item['ref']}`: `{item['preflight_state']}` - {item['preflight_reason']}")
        lines.append("")
    report_md.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")

    assertion_lines = [
        f"loop_id={RUN_ID}",
        f"gate_result={decision['gate_result']}",
        "accepted_new_roots_95=none",
        "missing_root_classes_95_effective=BearExpansion,Manipulation",
        f"nickdatak_rows={nickdatak['csv_summaries'][0]['rows'] if nickdatak['csv_summaries'] else 0}",
        "raw_committed_to_repo=false",
        "runtime_code_changed=false",
        "thresholds_relaxed=false",
    ]
    assertions.write_text("\n".join(assertion_lines) + "\n", encoding="utf-8")
    print(json.dumps(decision, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
