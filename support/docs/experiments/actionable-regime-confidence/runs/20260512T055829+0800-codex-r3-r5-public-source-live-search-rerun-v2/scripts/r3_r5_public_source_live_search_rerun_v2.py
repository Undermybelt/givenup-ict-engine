#!/usr/bin/env python3
"""Restore and verify the 055829 R3/R5 public-source rerun artifacts."""

from __future__ import annotations

import csv
import hashlib
import json
import re
import subprocess
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


RUN_ID = "20260512T055829+0800-codex-r3-r5-public-source-live-search-rerun-v2"
RUN_ROOT = Path("docs/experiments/actionable-regime-confidence/runs") / RUN_ID
ART_DIR = RUN_ROOT / "r3-r5-public-source-live-search-rerun-v2"
CMD_DIR = RUN_ROOT / "command-output"
CHECK_DIR = RUN_ROOT / "checks"
BOARD = Path("docs/plans/2026-05-10-actionable-regime-confidence-todo.md")

TARGET_ROOTS = [
    Path("/tmp/ict-engine-board-a-r6-owner-export-v1"),
    Path("/tmp/ict-engine-native-subhour-source-label-intake"),
    Path("/tmp/ict-engine-source-panel-recency-extension"),
]

KAGGLE_QUERIES = [
    "AAPL 15m regime label",
    "IXIC 15m regime label",
    "NQ futures 15m regime label",
    "Bull Bear Sideways Crisis market regime labels",
    "market regime labels intraday",
    "MainRegimeV2 market regime labels",
    "post 2026 stock market regime labels",
]

HF_QUERIES = KAGGLE_QUERIES

CANDIDATE_REFS = [
    "thisathdamiru/bybit-multi-crypto-historical-data-2020-2026",
    "sergionefedov/crypto-microstructure",
    "marketsignal/marketsignal-ai-feature-feed-mag-7-stocks",
]

R3_TERMS = re.compile(r"\b(aapl|ixic|nasdaq|nq|15m|30m|intraday|subhour|sub-hour)\b", re.I)
R5_TERMS = re.compile(r"\b(mainregimev2|bull|bear|sideways|crisis|regime|post.?2026|2026)\b", re.I)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def board_hash() -> str | None:
    return sha256_file(BOARD) if BOARD.exists() else None


def slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")


def run_command(name: str, args: list[str], timeout: int = 120) -> dict[str, Any]:
    CMD_DIR.mkdir(parents=True, exist_ok=True)
    prefix = CMD_DIR / name
    prefix.with_suffix(".cmd").write_text(" ".join(args) + "\n", encoding="utf-8")
    try:
        proc = subprocess.run(args, check=False, text=True, capture_output=True, timeout=timeout)
        stdout = proc.stdout
        stderr = proc.stderr
        exit_code = proc.returncode
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout or ""
        stderr = (exc.stderr or "") + f"\nTIMEOUT after {timeout}s\n"
        exit_code = 124
    prefix.with_suffix(".stdout").write_text(stdout, encoding="utf-8")
    prefix.with_suffix(".stderr").write_text(stderr, encoding="utf-8")
    prefix.with_suffix(".exit").write_text(f"{exit_code}\n", encoding="utf-8")
    return {"exit": exit_code, "stdout": stdout, "stderr": stderr}


def csv_rows_from_text(text: str) -> list[dict[str, str]]:
    lines = text.splitlines()
    for idx, line in enumerate(lines):
        if line.startswith("ref,") or line.startswith("name,"):
            lines = lines[idx:]
            break
    rows: list[dict[str, str]] = []
    for row in csv.DictReader(lines):
        if row:
            rows.append({str(k): "" if v is None else str(v) for k, v in row.items() if k is not None})
    return rows


def row_text(row: dict[str, Any]) -> str:
    return json.dumps(row, sort_keys=True, ensure_ascii=True)


def metadata_flags(text: str) -> tuple[bool, bool]:
    r3 = bool(R3_TERMS.search(text) and re.search(r"\b(label|regime|state)\b", text, re.I))
    r5 = bool("MainRegimeV2" in text or {"Bull", "Bear", "Sideways", "Crisis"}.issubset(set(re.findall(r"Bear|Bull|Crisis|Sideways", text))))
    return r3, r5


def hf_search(query: str, limit: int = 20) -> dict[str, Any]:
    name = f"hf_{slug(query)}"
    prefix = CMD_DIR / name
    url = "https://huggingface.co/api/datasets?search=" + urllib.parse.quote(query) + f"&limit={limit}"
    prefix.with_suffix(".cmd").write_text(f"GET {url}\n", encoding="utf-8")
    try:
        with urllib.request.urlopen(url, timeout=45) as response:
            body = response.read().decode("utf-8", errors="replace")
        exit_code = 0
        stderr = ""
    except Exception as exc:  # noqa: BLE001 - evidence collector.
        body = "[]"
        exit_code = 1
        stderr = f"{type(exc).__name__}: {exc}\n"
    prefix.with_suffix(".json").write_text(body, encoding="utf-8")
    prefix.with_suffix(".stderr").write_text(stderr, encoding="utf-8")
    prefix.with_suffix(".exit").write_text(f"{exit_code}\n", encoding="utf-8")
    try:
        rows = json.loads(body)
    except json.JSONDecodeError:
        rows = []
    summaries = []
    for row in rows if isinstance(rows, list) else []:
        r3, r5 = metadata_flags(row_text(row))
        summaries.append({"id": row.get("id") or row.get("datasetId"), "r3_metadata_match": r3, "r5_metadata_match": r5})
    return {"query": query, "exit": exit_code, "rows": len(summaries), "summaries": summaries}


def inspect_files(ref: str) -> dict[str, Any]:
    result = run_command(f"kaggle_files_{slug(ref)}", ["kaggle", "datasets", "files", "-d", ref, "--csv"], timeout=120)
    rows = csv_rows_from_text(result["stdout"])
    files = []
    for row in rows:
        text = row_text(row)
        r3, r5 = metadata_flags(text)
        label_named = bool(re.search(r"regime|label|state|signal", text, re.I))
        files.append(
            {
                "name": row.get("name", ""),
                "label_named": label_named,
                "r3_name_match": r3,
                "r5_name_match": r5,
                "raw": row,
            }
        )
    return {
        "ref": ref,
        "exit": result["exit"],
        "file_count": len(files),
        "sample_files": files[:15],
        "exact_r3_file_candidates": [f for f in files if f["label_named"] and f["r3_name_match"]][:10],
        "exact_r5_file_candidates": [f for f in files if f["label_named"] and f["r5_name_match"]][:10],
        "compatible_source_rows_found": False,
        "downloaded_row_data": False,
    }


def write_summary_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    fieldnames = [
        "surface",
        "query_or_ref",
        "exit",
        "rows_or_files",
        "r3_metadata_hits",
        "r5_metadata_hits",
        "compatible_source_rows_found",
        "blocker",
    ]
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})


def main() -> int:
    ART_DIR.mkdir(parents=True, exist_ok=True)
    CMD_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)

    roots_before = {str(p): p.exists() for p in TARGET_ROOTS}
    hash_before = board_hash()

    kaggle_results = {}
    for query in KAGGLE_QUERIES:
        result = run_command(f"kaggle_{slug(query)}", ["kaggle", "datasets", "list", "-s", query, "--csv"], timeout=120)
        rows = csv_rows_from_text(result["stdout"])
        summaries = []
        for row in rows:
            r3, r5 = metadata_flags(row_text(row))
            summaries.append({"ref": row.get("ref") or row.get("title") or "", "r3_metadata_match": r3, "r5_metadata_match": r5, "raw": row})
        kaggle_results[query] = {
            "exit": result["exit"],
            "rows": len(summaries),
            "summaries": summaries,
            "r3_metadata_hits": sum(1 for row in summaries if row["r3_metadata_match"]),
            "r5_metadata_hits": sum(1 for row in summaries if row["r5_metadata_match"]),
        }

    hf_results = {query: hf_search(query) for query in HF_QUERIES}
    file_results = {ref: inspect_files(ref) for ref in CANDIDATE_REFS}
    roots_after = {str(p): p.exists() for p in TARGET_ROOTS}
    target_root_mutated = roots_before != roots_after

    csv_rows = []
    for query, result in kaggle_results.items():
        csv_rows.append(
            {
                "surface": "kaggle",
                "query_or_ref": query,
                "exit": result["exit"],
                "rows_or_files": result["rows"],
                "r3_metadata_hits": result["r3_metadata_hits"],
                "r5_metadata_hits": result["r5_metadata_hits"],
                "compatible_source_rows_found": False,
                "blocker": "metadata_only_no_downloaded_source_owned_labels",
            }
        )
    for query, result in hf_results.items():
        csv_rows.append(
            {
                "surface": "huggingface",
                "query_or_ref": query,
                "exit": result["exit"],
                "rows_or_files": result["rows"],
                "r3_metadata_hits": sum(1 for row in result["summaries"] if row["r3_metadata_match"]),
                "r5_metadata_hits": sum(1 for row in result["summaries"] if row["r5_metadata_match"]),
                "compatible_source_rows_found": False,
                "blocker": "metadata_only_no_downloaded_source_owned_labels",
            }
        )
    for ref, result in file_results.items():
        csv_rows.append(
            {
                "surface": "kaggle_files",
                "query_or_ref": ref,
                "exit": result["exit"],
                "rows_or_files": result["file_count"],
                "r3_metadata_hits": len(result["exact_r3_file_candidates"]),
                "r5_metadata_hits": len(result["exact_r5_file_candidates"]),
                "compatible_source_rows_found": False,
                "blocker": "file_listing_only_no_source_owned_required_rows",
            }
        )

    summary_csv = ART_DIR / "r3_r5_public_source_live_search_rerun_v2_summary.csv"
    write_summary_csv(summary_csv, csv_rows)

    gate_result = "r3_r5_public_source_live_search_rerun_v2=no_exact_r3_r5_rows_no_promotion"
    totals = {
        "kaggle_rows": sum(v["rows"] for v in kaggle_results.values()),
        "huggingface_rows": sum(v["rows"] for v in hf_results.values()),
        "candidate_file_rows": sum(v["file_count"] for v in file_results.values()),
        "r3_metadata_hits": sum(v["r3_metadata_hits"] for v in kaggle_results.values())
        + sum(sum(1 for row in v["summaries"] if row["r3_metadata_match"]) for v in hf_results.values())
        + sum(len(v["exact_r3_file_candidates"]) for v in file_results.values()),
        "r5_metadata_hits": sum(v["r5_metadata_hits"] for v in kaggle_results.values())
        + sum(sum(1 for row in v["summaries"] if row["r5_metadata_match"]) for v in hf_results.values())
        + sum(len(v["exact_r5_file_candidates"]) for v in file_results.values()),
        "compatible_source_rows_found": False,
    }

    doc = {
        "run_id": RUN_ID,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "gate_result": gate_result,
        "board_hash_before_artifact": hash_before,
        "scope": "durable 055829 public-source search artifact restoration",
        "kaggle_results": kaggle_results,
        "huggingface_results": hf_results,
        "candidate_file_listings": file_results,
        "totals": totals,
        "target_roots_before": roots_before,
        "target_roots_after": roots_after,
        "decision": {
            "accepted_rows_added": 0,
            "source_control_evidence_acquired": False,
            "target_root_mutated": target_root_mutated,
            "canonical_merge": False,
            "downstream_promotion_rerun": False,
            "strict_full_objective": False,
            "trade_usable": False,
            "update_goal": False,
        },
    }
    json_path = ART_DIR / "r3_r5_public_source_live_search_rerun_v2.json"
    json_path.write_text(json.dumps(doc, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    md_path = ART_DIR / "r3_r5_public_source_live_search_rerun_v2.md"
    md_path.write_text(
        "\n".join(
            [
                "# R3/R5 Public Source Live Search Rerun v2",
                "",
                f"Run id: `{RUN_ID}`",
                "",
                f"Gate result: `{gate_result}`",
                "",
                f"Board hash before artifact: `{hash_before}`",
                "",
                "## Scope",
                "",
                "Durable restoration of the `055829` metadata/file-listing source search artifacts. "
                "This run checks Kaggle and Hugging Face metadata plus selected Kaggle file listings. "
                "It does not download row data, create labels, mutate target intake roots, run canonical merge, rerun downstream promotion, make a trade claim, or call `update_goal`.",
                "",
                "## Readback",
                "",
                f"- Kaggle rows scanned: `{totals['kaggle_rows']}` across `{len(KAGGLE_QUERIES)}` queries.",
                f"- Hugging Face rows scanned: `{totals['huggingface_rows']}` across `{len(HF_QUERIES)}` queries.",
                f"- Kaggle file-list rows scanned: `{totals['candidate_file_rows']}` across `{len(CANDIDATE_REFS)}` candidate refs.",
                f"- R3 metadata/file hits: `{totals['r3_metadata_hits']}`.",
                f"- R5 metadata/file hits: `{totals['r5_metadata_hits']}`.",
                "- Compatible source rows acquired: `false`.",
                "",
                "## Required Roots",
                "",
                *[f"- `{path}`: before `{roots_before[path]}`, after `{roots_after[path]}`" for path in roots_before],
                "",
                "## Decision",
                "",
                "No source-owned AAPL/IXIC/NQ native 15m/30m regime-label rows and no source-owned post-cutoff `MainRegimeV2` rows were acquired. The run is countable only as source-search evidence and remains non-promoting.",
                "",
                "Promotion remains blocked: accepted rows added `0`, source/control evidence acquired `false`, target root mutated `false`, canonical merge `false`, downstream promotion rerun `false`, strict full objective `false`, trade usable `false`, and `update_goal=false`.",
                "",
                "## Next",
                "",
                "Continue only after explicit source/control approval, verifier-native R6 owner/export rows with valid controls, source-owned R5 recency rows, or source-owned R3 native sub-hour labels unlock a required target root. Then rerun direct verifier, split calibration, canonical merge, providers, Auto-Quant, filter/Pre-Bayes, BBN, CatBoost/path-ranking, and execution-tree readback in order.",
                "",
            ]
        ),
        encoding="utf-8",
    )

    assertions = [
        f"gate_result={gate_result}",
        f"json_exists={json_path.exists()}",
        f"md_exists={md_path.exists()}",
        f"summary_csv_exists={summary_csv.exists()}",
        f"kaggle_rows={totals['kaggle_rows']}",
        f"huggingface_rows={totals['huggingface_rows']}",
        f"candidate_file_rows={totals['candidate_file_rows']}",
        f"compatible_source_rows_found={str(totals['compatible_source_rows_found']).lower()}",
        f"target_root_mutated={str(target_root_mutated).lower()}",
        "canonical_merge=false",
        "downstream_promotion_rerun=false",
        "trade_usable=false",
        "update_goal=false",
    ]
    (CHECK_DIR / "r3_r5_public_source_live_search_rerun_v2_assertions.out").write_text("\n".join(assertions) + "\n", encoding="utf-8")

    print(json.dumps({"run_id": RUN_ID, "gate_result": gate_result, "totals": totals}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
