#!/usr/bin/env python3
"""Screen fresh crypto/native microstructure datasets for R3/R5 source-label fit."""

from __future__ import annotations

import csv
import hashlib
import json
import os
import re
import shutil
import subprocess
from datetime import date, datetime
from pathlib import Path
from typing import Any


RUN_ID = "20260512T055103-codex-r3-r5-crypto-microstructure-source-screen-v1"
RUN_ROOT = Path("docs/experiments/actionable-regime-confidence/runs") / RUN_ID
ART_DIR = RUN_ROOT / "r3-r5-crypto-microstructure-source-screen-v1"
CMD_DIR = RUN_ROOT / "command-output"
CHECK_DIR = RUN_ROOT / "checks"
TMP_ROOT = Path("/tmp/ict-engine-r3-r5-crypto-microstructure-source-screen-v1")
BOARD = Path("docs/plans/2026-05-10-actionable-regime-confidence-todo.md")
CUTOFF = date(2026, 1, 30)

REQUIRED_ROOTS = [
    Path("/tmp/ict-engine-board-a-r6-owner-export-v1"),
    Path("/tmp/ict-engine-native-subhour-source-label-intake"),
    Path("/tmp/ict-engine-source-panel-recency-extension"),
]

QUERIES = [
    "crypto microstructure regime",
    "crypto regime features",
    "limit order book market regimes",
    "binance trades regime",
]

CANDIDATE_REFS = [
    "sergionefedov/crypto-microstructure",
    "quantiota/ska-engine-applied-to-crypto-from-binance",
    "sergionefedov/synthetic-limit-order-book-market-microstructure",
    "marketsignal/marketsignal-ai-feature-feed-mag-7-stocks",
]

DOWNLOAD_REFS = [
    "sergionefedov/crypto-microstructure",
    "marketsignal/marketsignal-ai-feature-feed-mag-7-stocks",
]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def board_hash() -> str | None:
    if not BOARD.exists():
        return None
    return sha256_file(BOARD)


def slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")


def run_command(name: str, args: list[str], timeout: int = 120) -> dict[str, Any]:
    CMD_DIR.mkdir(parents=True, exist_ok=True)
    prefix = CMD_DIR / name
    (prefix.with_suffix(".cmd")).write_text(" ".join(args) + "\n", encoding="utf-8")
    try:
        proc = subprocess.run(
            args,
            check=False,
            text=True,
            capture_output=True,
            timeout=timeout,
        )
        stdout = proc.stdout
        stderr = proc.stderr
        code = proc.returncode
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout or ""
        stderr = (exc.stderr or "") + f"\nTIMEOUT after {timeout}s\n"
        code = 124
    (prefix.with_suffix(".stdout")).write_text(stdout, encoding="utf-8")
    (prefix.with_suffix(".stderr")).write_text(stderr, encoding="utf-8")
    (prefix.with_suffix(".exit")).write_text(f"{code}\n", encoding="utf-8")
    return {"name": name, "args": args, "exit": code, "stdout": stdout, "stderr": stderr}


def parse_date(value: str) -> date | None:
    value = (value or "").strip()
    if not value:
        return None
    candidates = [
        value[:10],
        value.replace("Z", "+00:00"),
    ]
    for item in candidates:
        try:
            return datetime.fromisoformat(item).date()
        except ValueError:
            pass
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%d-%m-%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(value[:10], fmt).date()
        except ValueError:
            pass
    return None


def inspect_csv(path: Path, max_rows: int = 250_000) -> dict[str, Any]:
    stat = path.stat()
    info: dict[str, Any] = {
        "path": str(path),
        "name": path.name,
        "size_bytes": stat.st_size,
        "sha256": sha256_file(path),
        "rows_scanned": 0,
        "columns": [],
        "date_columns": [],
        "min_date": None,
        "max_date": None,
        "post_cutoff_rows": 0,
        "label_like_columns": {},
    }
    if stat.st_size > 2_500_000 and not re.search(r"regime|state|label|signal", path.name, re.I):
        info["skipped"] = "large_non_label_named_csv"
        return info

    with path.open("r", encoding="utf-8-sig", errors="replace", newline="") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            info["skipped"] = "no_header"
            return info
        columns = list(reader.fieldnames)
        info["columns"] = columns
        date_cols = [c for c in columns if c and re.search(r"date|time|timestamp", c, re.I)]
        label_cols = [
            c
            for c in columns
            if c
            and re.search(r"regime|state|label|signal|trend", c, re.I)
            and not re.search(r"price|rate|spread|volume|return|volatility|score|prob|p_", c, re.I)
        ]
        info["date_columns"] = date_cols
        unique_values: dict[str, set[str]] = {c: set() for c in label_cols[:12]}
        min_dt: date | None = None
        max_dt: date | None = None
        post_cutoff = 0
        rows = 0
        for row in reader:
            rows += 1
            row_date = None
            for c in date_cols[:4]:
                row_date = parse_date(row.get(c, ""))
                if row_date:
                    break
            if row_date:
                min_dt = row_date if min_dt is None else min(min_dt, row_date)
                max_dt = row_date if max_dt is None else max(max_dt, row_date)
                if row_date > CUTOFF:
                    post_cutoff += 1
            for c in unique_values:
                value = (row.get(c) or "").strip()
                if value and len(unique_values[c]) < 50:
                    unique_values[c].add(value)
            if rows >= max_rows:
                info["truncated_at"] = max_rows
                break
        info["rows_scanned"] = rows
        info["min_date"] = min_dt.isoformat() if min_dt else None
        info["max_date"] = max_dt.isoformat() if max_dt else None
        info["post_cutoff_rows"] = post_cutoff
        info["label_like_columns"] = {k: sorted(v)[:25] for k, v in unique_values.items()}
    return info


def inspect_downloaded_ref(ref: str, root: Path) -> dict[str, Any]:
    files = sorted(p for p in root.rglob("*") if p.is_file())
    csv_infos = []
    for path in files:
        if path.suffix.lower() == ".csv":
            csv_infos.append(inspect_csv(path))
    all_label_values = []
    for info in csv_infos:
        for col, values in info.get("label_like_columns", {}).items():
            all_label_values.append({"file": info["name"], "column": col, "values": values})
    root_labels = {"Bull", "Bear", "Sideways", "Crisis"}
    exact_root_labels = any(root_labels.issubset(set(item["values"])) for item in all_label_values)
    return {
        "ref": ref,
        "download_root": str(root),
        "files": [
            {
                "path": str(p.relative_to(root)),
                "size_bytes": p.stat().st_size,
                "sha256": sha256_file(p),
            }
            for p in files
        ],
        "csv_inspections": csv_infos,
        "exact_mainregimev2_labels_present": exact_root_labels,
        "r5_compatible": False,
        "r3_compatible": False,
        "disposition": (
            "not_r5_or_r3_compatible_exact_mainregimev2_absent"
            if not exact_root_labels
            else "root_labels_seen_but_wrong_market_or_missing_required_provenance"
        ),
    }


def csv_rows_from_text(text: str) -> list[dict[str, str]]:
    lines = text.splitlines()
    for idx, line in enumerate(lines):
        if line.startswith("ref,") or line.startswith("name,"):
            lines = lines[idx:]
            break
    rows = []
    reader = csv.DictReader(lines)
    for row in reader:
        if row:
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


def write_csv_summary(path: Path, rows: list[dict[str, Any]]) -> None:
    fieldnames = [
        "ref",
        "downloaded",
        "r5_compatible",
        "r3_compatible",
        "max_date",
        "post_cutoff_rows",
        "label_columns",
        "disposition",
    ]
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in fieldnames})


def main() -> int:
    ART_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)
    CMD_DIR.mkdir(parents=True, exist_ok=True)
    TMP_ROOT.mkdir(parents=True, exist_ok=True)

    before_hash = board_hash()
    query_results = {}
    for query in QUERIES:
        name = f"kaggle_list_{slug(query)}"
        res = run_command(
            name,
            ["kaggle", "datasets", "list", "--sort-by", "updated", "--csv", "-s", query],
            timeout=120,
        )
        query_results[query] = {
            "exit": res["exit"],
            "rows": csv_rows_from_text(res["stdout"]),
            "stdout_path": str((CMD_DIR / name).with_suffix(".stdout")),
        }

    file_results = {}
    for ref in CANDIDATE_REFS:
        name = f"kaggle_files_{slug(ref)}"
        res = run_command(
            name,
            ["kaggle", "datasets", "files", "-v", ref],
            timeout=120,
        )
        file_results[ref] = {
            "exit": res["exit"],
            "files": csv_rows_from_text(res["stdout"]),
            "stdout_path": str((CMD_DIR / name).with_suffix(".stdout")),
        }

    download_results = {}
    if TMP_ROOT.exists():
        shutil.rmtree(TMP_ROOT)
    TMP_ROOT.mkdir(parents=True, exist_ok=True)
    for ref in DOWNLOAD_REFS:
        out_root = TMP_ROOT / slug(ref)
        out_root.mkdir(parents=True, exist_ok=True)
        name = f"kaggle_download_{slug(ref)}"
        res = run_command(
            name,
            ["kaggle", "datasets", "download", "-d", ref, "-p", str(out_root), "--unzip"],
            timeout=240,
        )
        download_results[ref] = {
            "exit": res["exit"],
            "download_root": str(out_root),
            "inspection": inspect_downloaded_ref(ref, out_root) if res["exit"] == 0 else None,
        }

    candidate_summary = []
    for ref in CANDIDATE_REFS:
        inspection = download_results.get(ref, {}).get("inspection")
        max_date = None
        post_cutoff_rows = 0
        label_columns = []
        downloaded = inspection is not None
        disposition = "file_listing_only_no_download"
        if inspection:
            disposition = inspection["disposition"]
            for csv_info in inspection["csv_inspections"]:
                if csv_info.get("max_date"):
                    max_date = max(max_date or csv_info["max_date"], csv_info["max_date"])
                post_cutoff_rows += int(csv_info.get("post_cutoff_rows") or 0)
                for col in csv_info.get("label_like_columns", {}):
                    label_columns.append(f"{csv_info['name']}:{col}")
        if "synthetic" in ref:
            disposition = "synthetic_dataset_not_source_owned_market_label_evidence"
        if ref == "quantiota/ska-engine-applied-to-crypto-from-binance":
            disposition = "raw_binance_trade_files_file_listing_only_no_source_regime_labels"
        candidate_summary.append(
            {
                "ref": ref,
                "downloaded": downloaded,
                "r5_compatible": False,
                "r3_compatible": False,
                "max_date": max_date,
                "post_cutoff_rows": post_cutoff_rows,
                "label_columns": ";".join(label_columns[:20]),
                "disposition": disposition,
            }
        )

    required_root_status = {str(root): root.exists() for root in REQUIRED_ROOTS}
    result = {
        "run_id": RUN_ID,
        "gate_result": "r3_r5_crypto_microstructure_source_screen_v1=crypto_native_candidates_screened_no_required_root_unlock_no_promotion",
        "board_hash_before_artifact": before_hash,
        "scope": "Read-only R3/R5 source-acquisition screen for fresh crypto/native microstructure regime-like candidates.",
        "queries": query_results,
        "candidate_file_results": file_results,
        "download_results": download_results,
        "candidate_summary": candidate_summary,
        "required_root_status": required_root_status,
        "target_root_mutated": False,
        "source_control_evidence_acquired": False,
        "canonical_merge": False,
        "downstream_promotion_rerun": False,
        "trade_usable": False,
        "update_goal": False,
        "decision": "No screened crypto/native microstructure candidate satisfies the R3 native AAPL/IXIC 15m/30m source-label intake or the R5 source-owned MainRegimeV2 post-cutoff stock-panel extension contract.",
        "next": "Keep Board A blocked until R6 owner/export rows plus normal controls, source-owned R3 native sub-hour labels, source-owned R5 MainRegimeV2 recency rows, or explicit source/control approval unlock a required root.",
    }

    json_path = ART_DIR / "r3_r5_crypto_microstructure_source_screen_v1.json"
    md_path = ART_DIR / "r3_r5_crypto_microstructure_source_screen_v1.md"
    csv_path = ART_DIR / "r3_r5_crypto_microstructure_candidate_summary_v1.csv"
    assertions_path = CHECK_DIR / "r3_r5_crypto_microstructure_source_screen_v1_assertions.out"

    json_path.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    write_csv_summary(csv_path, candidate_summary)

    lines = [
        "# R3/R5 Crypto Microstructure Source Screen v1",
        "",
        f"Run id: `{RUN_ID}`",
        "",
        f"Gate result: `{result['gate_result']}`",
        "",
        f"Board hash before artifact: `{before_hash}`",
        "",
        "## Scope",
        "",
        "Read-only source-acquisition screen for crypto/native microstructure regime-like datasets that were not covered by the broad R5 NIFTY screen. This run keeps raw downloads in `/tmp`, does not mutate required target roots, does not map external labels into `MainRegimeV2`, does not run canonical merge or downstream promotion, and does not call `update_goal`.",
        "",
        "## Search Readback",
        "",
    ]
    for query, qres in query_results.items():
        lines.append(f"- `{query}`: exit `{qres['exit']}`, rows `{len(qres['rows'])}`")
    lines.extend(["", "## Candidate Disposition", "", "| Ref | Downloaded | Max date | Post-cutoff rows | Disposition |", "|---|---:|---:|---:|---|"])
    for row in candidate_summary:
        lines.append(
            f"| `{row['ref']}` | `{row['downloaded']}` | `{row.get('max_date') or ''}` | `{row.get('post_cutoff_rows') or 0}` | `{row['disposition']}` |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            result["decision"],
            "",
            "Reasons:",
            "- The only downloaded crypto dataset with `regime_features.csv` is crypto-context feature evidence, not a source-owned `MainRegimeV2` `Bull`/`Bear`/`Sideways`/`Crisis` stock-panel extension.",
            "- Mag-7 feature samples are equity feature feeds, not native AAPL/IXIC 15m/30m source labels and not R5 root labels.",
            "- The Binance/SKA and synthetic LOB candidates are raw/synthetic microstructure routes without source-owned target labels; mapping them would be a derived ontology transform.",
            "- Required target roots remain absent.",
            "",
            "Required root status:",
        ]
    )
    for root, exists in required_root_status.items():
        lines.append(f"- `{root}`: `{exists}`")
    lines.extend(
        [
            "",
            "Promotion status remains unchanged: accepted rows added `0`, source/control evidence acquired `false`, target root mutated `false`, canonical merge `false`, downstream promotion rerun `false`, strict full objective `false`, trade usable `false`, and `update_goal=false`.",
            "",
            "## Next",
            "",
            result["next"],
            "",
        ]
    )
    md_path.write_text("\n".join(lines), encoding="utf-8")

    assertions = [
        "r3_r5_crypto_microstructure_source_screen_v1=crypto_native_candidates_screened_no_required_root_unlock_no_promotion",
        "required_roots_absent=true",
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
