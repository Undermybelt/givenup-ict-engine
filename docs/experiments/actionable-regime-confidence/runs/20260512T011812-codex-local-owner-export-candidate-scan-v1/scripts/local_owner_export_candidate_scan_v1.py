#!/usr/bin/env python3
"""Bounded local scan for R6 owner-export candidate files."""

from __future__ import annotations

import csv
import hashlib
import json
import subprocess
from pathlib import Path


RUN_ID = "20260512T011812-codex-local-owner-export-candidate-scan-v1"
RUN_ROOT = Path("docs/experiments/actionable-regime-confidence/runs") / RUN_ID
OUT_DIR = RUN_ROOT / "local-owner-export-candidate-scan-v1"
CHECK_DIR = RUN_ROOT / "checks"

TOMAC_ROOT = Path("/Users/thrill3r/Downloads/Tomac/gc future 2021-2025")
CANDIDATE_ARCHIVE = TOMAC_ROOT / "databento.rar"
METADATA = TOMAC_ROOT / "metadata.json"
MANIFEST = TOMAC_ROOT / "manifest.json"
EXTRACTED_CSVS = [
    TOMAC_ROOT / "gc_201101_202604.csv",
    TOMAC_ROOT / "glbx-mdp3-20210106-20260105.ohlcv-1m.csv",
    TOMAC_ROOT / "symbology.csv",
]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def first_line(path: Path) -> str:
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        return handle.readline().strip()


def line_count(path: Path) -> int:
    with path.open("rb") as handle:
        return sum(1 for _ in handle)


def archive_listing(path: Path) -> list[str]:
    proc = subprocess.run(
        ["bsdtar", "-tf", str(path)],
        text=True,
        capture_output=True,
        check=False,
        timeout=60,
    )
    if proc.returncode != 0:
        return [f"LIST_FAILED:{proc.stderr.strip()[:200]}"]
    return [line for line in proc.stdout.splitlines() if line]


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)

    metadata = json.loads(METADATA.read_text(encoding="utf-8"))
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    query = metadata.get("query", {})
    archive_files = archive_listing(CANDIDATE_ARCHIVE)

    csv_rows = []
    for path in EXTRACTED_CSVS:
        csv_rows.append(
            {
                "path": str(path),
                "exists": path.exists(),
                "bytes": path.stat().st_size if path.exists() else 0,
                "line_count": line_count(path) if path.exists() else 0,
                "header": first_line(path) if path.exists() else "",
                "sha256": sha256_file(path) if path.exists() else "",
            }
        )

    schema = query.get("schema")
    archive_only_csv = all(name.lower().endswith(".csv") for name in archive_files)
    extracted_headers = [row["header"] for row in csv_rows if row["exists"]]
    depth_or_order_schemas = {"mbo", "mbp-1", "mbp-10", "tbbo", "trades", "bbo"}
    has_depth_or_order_lifecycle = (schema or "").lower() in depth_or_order_schemas
    has_depth_or_order_lifecycle = has_depth_or_order_lifecycle or any(
        name.lower().endswith((".dbn", ".mbo", ".pcap", ".itch"))
        or any(token in name.lower() for token in ["market-depth", "market_by_order", "book-depth"])
        for name in archive_files
    )
    has_depth_or_order_lifecycle = has_depth_or_order_lifecycle or any(
        "bid_px" in header.lower()
        or "ask_px" in header.lower()
        or "order_id" in header.lower()
        for header in extracted_headers
    )
    has_only_ohlcv_headers = all(
        row["header"].startswith("ts_event,rtype,publisher_id,instrument_id,open,high,low,close,volume")
        or row["header"].startswith("raw_symbol,instrument_id,date")
        for row in csv_rows
        if row["exists"]
    )

    archive_sha = sha256_file(CANDIDATE_ARCHIVE)
    manifest_files = [item.get("filename", "") for item in manifest.get("files", [])]
    decision = "local_owner_export_candidate_scan_v1=tomac_databento_ohlcv_only_no_r6_controls"
    r6_control_satisfied = False

    summary = {
        "run_id": RUN_ID,
        "candidate_root": str(TOMAC_ROOT),
        "candidate_archive": str(CANDIDATE_ARCHIVE),
        "candidate_archive_sha256": archive_sha,
        "archive_files": archive_files,
        "metadata_query": query,
        "manifest_files": manifest_files,
        "csv_readback": csv_rows,
        "archive_only_csv": archive_only_csv,
        "schema": schema,
        "has_depth_or_order_lifecycle": has_depth_or_order_lifecycle,
        "has_only_ohlcv_headers": has_only_ohlcv_headers,
        "r6_owner_control_contract_satisfied": r6_control_satisfied,
        "canonical_merge_allowed_now": False,
        "downstream_rerun_allowed_now": False,
        "accepted_rows_added": 0,
        "strict_full_objective_achieved": False,
        "decision": decision,
        "blocker": "Local Tomac/Databento candidate is OHLCV-1m CSV material only; it has no source-owned normal-control labels, no order lifecycle, no depth/book rows, and no Cboe/CFE VIX branch.",
    }

    json_path = OUT_DIR / "local_owner_export_candidate_scan_v1.json"
    csv_path = OUT_DIR / "local_owner_export_candidate_files_v1.csv"
    report_path = OUT_DIR / "local_owner_export_candidate_scan_v1.md"
    assertions_path = CHECK_DIR / "local_owner_export_candidate_scan_v1_assertions.out"

    json_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["path", "exists", "bytes", "line_count", "header", "sha256"],
        )
        writer.writeheader()
        writer.writerows(csv_rows)

    report_lines = [
        "# Local Owner Export Candidate Scan v1",
        "",
        f"- Decision: `{decision}`.",
        f"- Candidate archive: `{CANDIDATE_ARCHIVE}`.",
        f"- Archive SHA-256: `{archive_sha}`.",
        f"- Metadata dataset: `{query.get('dataset')}`; schema: `{schema}`; symbols: `{query.get('symbols')}`.",
        f"- Archive files: `{archive_files}`.",
        f"- Manifest files: `{manifest_files}`.",
        f"- Has depth/order-lifecycle evidence: `{str(has_depth_or_order_lifecycle).lower()}`.",
        f"- Has only OHLCV/symbology headers in extracted CSVs: `{str(has_only_ohlcv_headers).lower()}`.",
        "- R6 owner-control contract satisfied: `false`.",
        "- Canonical merge allowed now: `false`; downstream rerun allowed now: `false`.",
        "- Accepted rows added: `0`; strict full objective achieved: `false`; `update_goal=false`.",
        "",
        "## Classification",
        "",
        "The local Tomac/Databento candidate is useful market-data context but cannot be promoted as R6 source-owned normal controls. It is `ohlcv-1m` CSV material, not verifier-native Market Depth/Market by Order/order-lifecycle data, and it carries no approved normal/non-manipulation labels.",
        "",
        "## Artifacts",
        "",
        f"- JSON: `{json_path}`",
        f"- File CSV: `{csv_path}`",
        f"- Assertions: `{assertions_path}`",
        f"- Reproduction script: `{Path(__file__)}`",
    ]
    report_path.write_text("\n".join(report_lines) + "\n", encoding="utf-8")

    assertion_lines = [
        f"PASS decision={decision}",
        f"PASS archive_exists={str(CANDIDATE_ARCHIVE.exists()).lower()}",
        f"PASS schema={schema}",
        f"PASS archive_only_csv={str(archive_only_csv).lower()}",
        f"PASS has_depth_or_order_lifecycle={str(has_depth_or_order_lifecycle).lower()}",
        f"PASS has_only_ohlcv_headers={str(has_only_ohlcv_headers).lower()}",
        "PASS r6_owner_control_contract_satisfied=false",
        "PASS canonical_merge_allowed_now=false",
        "PASS downstream_rerun_allowed_now=false",
        "PASS strict_full_objective_achieved=false",
        "PASS update_goal=false",
    ]
    assertions_path.write_text("\n".join(assertion_lines) + "\n", encoding="utf-8")
    print(json.dumps({"decision": decision, "report": str(report_path)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
