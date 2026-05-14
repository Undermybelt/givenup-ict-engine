#!/usr/bin/env python3
"""Durable rerun for R3/R5 public source-label metadata search."""

from __future__ import annotations

import csv
import hashlib
import json
import re
import subprocess
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

import requests


RUN_ID = "20260512T055912-codex-r3-r5-public-source-durable-rerun-v1"
RUN_ROOT = Path("docs/experiments/actionable-regime-confidence/runs") / RUN_ID
ART_DIR = RUN_ROOT / "r3-r5-public-source-durable-rerun-v1"
CMD_DIR = RUN_ROOT / "command-output"
CHECK_DIR = RUN_ROOT / "checks"
BOARD = Path("docs/plans/2026-05-10-actionable-regime-confidence-todo.md")

REQUIRED_ROOTS = [
    Path("/tmp/ict-engine-board-a-r6-owner-export-v1"),
    Path("/tmp/ict-engine-native-subhour-source-label-intake"),
    Path("/tmp/ict-engine-source-panel-recency-extension"),
]

KAGGLE_QUERIES = [
    "AAPL 15m regime label",
    "AAPL 30m regime label",
    "IXIC 15m regime label",
    "IXIC 30m regime label",
    "NQ futures 15m regime label",
    "MainRegimeV2 market regime labels",
    "Bull Bear Sideways Crisis market regime labels",
    "market regime labels intraday",
]

HF_QUERIES = [
    "AAPL 15m regime label",
    "IXIC 15m regime label",
    "MainRegimeV2 market regime labels",
    "Bull Bear Sideways Crisis market regime labels",
    "market regime labels intraday",
]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def board_hash() -> str | None:
    return sha256_file(BOARD) if BOARD.exists() else None


def slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")


def run_command(name: str, args: list[str], stdout_suffix: str = ".stdout", timeout: int = 120) -> dict[str, Any]:
    CMD_DIR.mkdir(parents=True, exist_ok=True)
    prefix = CMD_DIR / name
    prefix.with_suffix(".cmd").write_text(" ".join(args) + "\n", encoding="utf-8")
    try:
        proc = subprocess.run(args, check=False, capture_output=True, text=True, timeout=timeout)
        code = proc.returncode
        stdout = proc.stdout
        stderr = proc.stderr
    except subprocess.TimeoutExpired as exc:
        code = 124
        stdout = exc.stdout or ""
        stderr = (exc.stderr or "") + f"\nTIMEOUT after {timeout}s\n"
    prefix.with_suffix(stdout_suffix).write_text(stdout, encoding="utf-8")
    prefix.with_suffix(".stderr").write_text(stderr, encoding="utf-8")
    prefix.with_suffix(".exit").write_text(f"{code}\n", encoding="utf-8")
    return {
        "name": name,
        "args": args,
        "exit": code,
        "stdout_path": str(prefix.with_suffix(stdout_suffix)),
        "stderr_path": str(prefix.with_suffix(".stderr")),
        "exit_path": str(prefix.with_suffix(".exit")),
        "stdout": stdout,
        "stderr": stderr,
    }


def csv_rows_from_text(text: str) -> list[dict[str, str]]:
    lines = text.splitlines()
    for idx, line in enumerate(lines):
        if line.startswith("ref,") or line.startswith("name,"):
            lines = lines[idx:]
            break
    rows: list[dict[str, str]] = []
    reader = csv.DictReader(lines)
    for row in reader:
        if not row:
            continue
        clean: dict[str, str] = {}
        extras: list[str] = []
        for key, value in row.items():
            if key is None:
                if isinstance(value, list):
                    extras.extend(str(v) for v in value)
                elif value is not None:
                    extras.append(str(value))
                continue
            clean[str(key)] = "" if value is None else str(value)
        if extras:
            clean["_extra"] = "|".join(extras)
        rows.append(clean)
    return rows


def row_text(row: dict[str, Any]) -> str:
    return " ".join(str(v) for v in row.values() if v is not None)


def classify_exact_hits(rows: list[dict[str, Any]]) -> dict[str, int]:
    r3 = 0
    r5 = 0
    for row in rows:
        text = row_text(row).lower()
        has_subhour = bool(re.search(r"\b(15m|15 min|15-minute|30m|30 min|30-minute|intraday)\b", text))
        has_r3_symbol = bool(re.search(r"\b(aapl|ixic|nq|nasdaq)\b", text))
        has_label = bool(re.search(r"\b(regime|label|state)\b", text))
        if has_subhour and has_r3_symbol and has_label:
            r3 += 1
        root_labels = all(token in text for token in ("bull", "bear", "sideways", "crisis"))
        if "mainregimev2" in text or (root_labels and has_label):
            r5 += 1
    return {"r3_exact_metadata_hits": r3, "r5_exact_metadata_hits": r5}


def get_hf(query: str, limit: int = 20) -> dict[str, Any]:
    CMD_DIR.mkdir(parents=True, exist_ok=True)
    name = f"hf_{slug(query)}"
    prefix = CMD_DIR / name
    url = "https://huggingface.co/api/datasets?" + urlencode({"search": query, "limit": limit, "full": "false"})
    prefix.with_suffix(".cmd").write_text(f"GET {url}\n", encoding="utf-8")
    try:
        response = requests.get(url, timeout=60)
        code = 0 if response.ok else 1
        text = response.text
        stderr = "" if response.ok else f"HTTP {response.status_code}\n"
        try:
            data = response.json()
        except ValueError:
            data = []
            code = 1
            stderr += "invalid json\n"
    except requests.RequestException as exc:
        code = 1
        text = ""
        stderr = f"{type(exc).__name__}: {exc}\n"
        data = []
    prefix.with_suffix(".json").write_text(text if text else "[]\n", encoding="utf-8")
    prefix.with_suffix(".stderr").write_text(stderr, encoding="utf-8")
    prefix.with_suffix(".exit").write_text(f"{code}\n", encoding="utf-8")
    rows = data if isinstance(data, list) else []
    return {
        "query": query,
        "exit": code,
        "rows": rows,
        "row_count": len(rows),
        "json_path": str(prefix.with_suffix(".json")),
        "stderr_path": str(prefix.with_suffix(".stderr")),
    }


def select_file_listing_refs(kaggle_searches: dict[str, Any]) -> list[str]:
    refs: list[str] = []
    fallback_refs: list[str] = []
    for result in kaggle_searches.values():
        for row in result["rows"]:
            ref = row.get("ref") or row.get("Ref") or ""
            text = row_text(row).lower()
            if not ref:
                continue
            if ref not in fallback_refs:
                fallback_refs.append(ref)
            interesting = bool(re.search(r"regime|intraday|aapl|ixic|nasdaq|mainregime|bull|bear|sideways|crisis", text))
            if interesting and ref not in refs:
                refs.append(ref)
            if len(refs) >= 5:
                return refs
    for ref in fallback_refs:
        if ref not in refs:
            refs.append(ref)
        if len(refs) >= 5:
            break
    return refs


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    fields = [
        "source",
        "query",
        "exit",
        "row_count",
        "r3_exact_metadata_hits",
        "r5_exact_metadata_hits",
        "artifact",
    ]
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fields})


def main() -> int:
    ART_DIR.mkdir(parents=True, exist_ok=True)
    CMD_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)

    before_hash = board_hash()

    kaggle_searches: dict[str, Any] = {}
    for query in KAGGLE_QUERIES:
        name = f"kaggle_{slug(query)}"
        res = run_command(name, ["kaggle", "datasets", "list", "--sort-by", "updated", "--csv", "-s", query], ".csv")
        rows = csv_rows_from_text(res["stdout"])
        hits = classify_exact_hits(rows)
        kaggle_searches[query] = {
            "query": query,
            "exit": res["exit"],
            "rows": rows,
            "row_count": len(rows),
            **hits,
            "csv_path": res["stdout_path"],
            "stderr_path": res["stderr_path"],
        }

    hf_searches: dict[str, Any] = {}
    for query in HF_QUERIES:
        res = get_hf(query)
        hits = classify_exact_hits(res["rows"])
        hf_searches[query] = {**res, **hits}

    file_listing_refs = select_file_listing_refs(kaggle_searches)
    file_results: dict[str, Any] = {}
    for ref in file_listing_refs:
        name = f"kaggle_files_{slug(ref)}"
        res = run_command(name, ["kaggle", "datasets", "files", "-v", ref], ".csv")
        file_results[ref] = {
            "ref": ref,
            "exit": res["exit"],
            "files": csv_rows_from_text(res["stdout"]),
            "csv_path": res["stdout_path"],
            "stderr_path": res["stderr_path"],
        }

    summary_rows: list[dict[str, Any]] = []
    for query, item in kaggle_searches.items():
        summary_rows.append(
            {
                "source": "kaggle",
                "query": query,
                "exit": item["exit"],
                "row_count": item["row_count"],
                "r3_exact_metadata_hits": item["r3_exact_metadata_hits"],
                "r5_exact_metadata_hits": item["r5_exact_metadata_hits"],
                "artifact": item["csv_path"],
            }
        )
    for query, item in hf_searches.items():
        summary_rows.append(
            {
                "source": "huggingface",
                "query": query,
                "exit": item["exit"],
                "row_count": item["row_count"],
                "r3_exact_metadata_hits": item["r3_exact_metadata_hits"],
                "r5_exact_metadata_hits": item["r5_exact_metadata_hits"],
                "artifact": item["json_path"],
            }
        )

    total_kaggle_rows = sum(item["row_count"] for item in kaggle_searches.values())
    total_hf_rows = sum(item["row_count"] for item in hf_searches.values())
    total_r3_hits = sum(item["r3_exact_metadata_hits"] for item in kaggle_searches.values()) + sum(
        item["r3_exact_metadata_hits"] for item in hf_searches.values()
    )
    total_r5_hits = sum(item["r5_exact_metadata_hits"] for item in kaggle_searches.values()) + sum(
        item["r5_exact_metadata_hits"] for item in hf_searches.values()
    )
    required_root_status = {str(root): root.exists() for root in REQUIRED_ROOTS}
    required_roots_present = [root for root, exists in required_root_status.items() if exists]

    gate_result = "r3_r5_public_source_durable_rerun_v1=metadata_search_no_required_root_unlock_no_promotion"
    decision = (
        "Durable public metadata search did not unlock R3/R5 source-control evidence. "
        "No required target root exists, and no exact source-owned native sub-hour R3 rows or post-cutoff MainRegimeV2 R5 rows were acquired."
    )
    if total_r3_hits or total_r5_hits:
        gate_result = "r3_r5_public_source_durable_rerun_v1=metadata_hits_require_owner_row_validation_no_promotion"
        decision = (
            "Metadata-only candidates were observed, but no row data was acquired into a required target root. "
            "Treat as source-acquisition leads only until owner/source rows are validated."
        )
    if required_roots_present:
        gate_result = "r3_r5_public_source_durable_rerun_v1=required_root_present_manual_followup_required_no_auto_promotion"
        decision = "A required target root exists and must be verified before any canonical merge or downstream rerun."

    result = {
        "run_id": RUN_ID,
        "gate_result": gate_result,
        "board_hash_before_artifact": before_hash,
        "scope": "Durable rerun of the missing 055212 R3/R5 Kaggle/Hugging Face public metadata search.",
        "kaggle_searches": kaggle_searches,
        "huggingface_searches": hf_searches,
        "file_listing_refs": file_listing_refs,
        "file_listing_results": file_results,
        "summary": {
            "kaggle_queries": len(KAGGLE_QUERIES),
            "kaggle_rows_scanned": total_kaggle_rows,
            "huggingface_queries": len(HF_QUERIES),
            "huggingface_rows_scanned": total_hf_rows,
            "r3_exact_metadata_hits": total_r3_hits,
            "r5_exact_metadata_hits": total_r5_hits,
        },
        "required_root_status": required_root_status,
        "accepted_rows_added": 0,
        "source_control_evidence_acquired": False,
        "target_root_mutated": False,
        "canonical_merge": False,
        "downstream_promotion_rerun": False,
        "strict_full_objective": False,
        "trade_usable": False,
        "update_goal": False,
        "decision": decision,
        "next": "Continue only after explicit source/control approval, verifier-native R6 owner/export rows with valid controls, source-owned R5 recency rows, or source-owned R3 native sub-hour labels unlock a required target root.",
    }

    json_path = ART_DIR / "r3_r5_public_source_durable_rerun_v1.json"
    md_path = ART_DIR / "r3_r5_public_source_durable_rerun_v1.md"
    csv_path = ART_DIR / "r3_r5_public_source_durable_rerun_v1_search_summary.csv"
    assertions_path = CHECK_DIR / "r3_r5_public_source_durable_rerun_v1_assertions.out"

    json_path.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    write_csv(csv_path, summary_rows)

    lines = [
        "# R3/R5 Public Source Durable Rerun v1",
        "",
        f"Run id: `{RUN_ID}`",
        "",
        f"Gate result: `{gate_result}`",
        "",
        f"Board hash before artifact: `{before_hash}`",
        "",
        "## Scope",
        "",
        "Durable rerun of the missing `055212` Kaggle/Hugging Face R3/R5 public metadata search. This run stores command outputs and summaries under this run root. It does not download row data, create labels, mutate R3/R5/R6 target roots, approve controls, run canonical merge, rerun downstream promotion, make a trade claim, or call `update_goal`.",
        "",
        "## Search Readback",
        "",
        f"- Kaggle queries: `{len(KAGGLE_QUERIES)}`, rows scanned: `{total_kaggle_rows}`",
        f"- Hugging Face queries: `{len(HF_QUERIES)}`, rows scanned: `{total_hf_rows}`",
        f"- Exact R3 metadata hits: `{total_r3_hits}`",
        f"- Exact R5 metadata hits: `{total_r5_hits}`",
        f"- Kaggle file listings inspected: `{len(file_listing_refs)}`",
        "",
        "Summary CSV:",
        f"- `{csv_path}`",
        "",
        "## Decision",
        "",
        decision,
        "",
        "Required root status:",
    ]
    for root, exists in required_root_status.items():
        lines.append(f"- `{root}`: `{exists}`")
    lines.extend(
        [
            "",
            "Promotion remains blocked: accepted rows added `0`, source/control evidence acquired `false`, target root mutated `false`, canonical merge `false`, downstream promotion rerun `false`, strict full objective `false`, trade usable `false`, and `update_goal=false`.",
            "",
            "## Next",
            "",
            result["next"],
            "",
        ]
    )
    md_path.write_text("\n".join(lines), encoding="utf-8")

    assertions = [
        gate_result,
        f"kaggle_rows_scanned={total_kaggle_rows}",
        f"huggingface_rows_scanned={total_hf_rows}",
        f"r3_exact_metadata_hits={total_r3_hits}",
        f"r5_exact_metadata_hits={total_r5_hits}",
        f"required_roots_present={len(required_roots_present)}",
        "accepted_rows_added=0",
        "source_control_evidence_acquired=false",
        "target_root_mutated=false",
        "canonical_merge=false",
        "downstream_promotion_rerun=false",
        "trade_usable=false",
        "update_goal=false",
    ]
    assertions_path.write_text("\n".join(assertions) + "\n", encoding="utf-8")

    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
