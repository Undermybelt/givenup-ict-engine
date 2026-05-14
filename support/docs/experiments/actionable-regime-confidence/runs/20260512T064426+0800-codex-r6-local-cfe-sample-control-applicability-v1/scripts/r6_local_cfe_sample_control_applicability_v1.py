#!/usr/bin/env python3
"""Assess local CFE/Cboe sample files against the R6 owner-control contract."""

from __future__ import annotations

import csv
import hashlib
import json
import os
import subprocess
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


RUN_ID = "20260512T064426+0800-codex-r6-local-cfe-sample-control-applicability-v1"
GATE_RESULT = (
    "r6_local_cfe_sample_control_applicability_v1="
    "cfe_sample_schema_context_only_no_controls_no_promotion"
)
SCRIPT = Path(__file__).resolve()
RUN_ROOT = SCRIPT.parents[1]
REPO = SCRIPT.parents[6]
BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"
OUT_DIR = RUN_ROOT / "r6-local-cfe-sample-control-applicability-v1"
CHECK_DIR = RUN_ROOT / "checks"
CMD_DIR = RUN_ROOT / "command-output"

CFE_ZIP = Path("/tmp/cfe_futures_trades_sample_226.zip")
HEADER_FILES = [
    Path("/tmp/ict-engine-cboe-futures-market-data-headers.txt"),
    Path("/tmp/ict-engine-cboe-oof-headers.txt"),
    Path("/tmp/ict-engine-databento-docs-headers.txt"),
    Path("/tmp/ict-engine-databento-metadata-range-response.json"),
]
R6_TARGET_ROOT = Path("/tmp/ict-engine-board-a-r6-owner-export-v1")


def sha256_file(path: Path) -> str | None:
    if not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def board_hash() -> str:
    return hashlib.sha256(BOARD.read_bytes()).hexdigest()


def run_cmd(name: str, args: list[str]) -> dict[str, Any]:
    out_path = CMD_DIR / f"{name}.out"
    err_path = CMD_DIR / f"{name}.err"
    proc = subprocess.run(args, cwd=REPO, text=True, capture_output=True, check=False)
    out_path.write_text(proc.stdout, encoding="utf-8")
    err_path.write_text(proc.stderr, encoding="utf-8")
    return {
        "name": name,
        "args": args,
        "returncode": proc.returncode,
        "stdout_path": str(out_path.relative_to(REPO)),
        "stderr_path": str(err_path.relative_to(REPO)),
    }


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def inspect_headers() -> list[dict[str, Any]]:
    rows = []
    for path in HEADER_FILES:
        text = path.read_text(encoding="utf-8", errors="replace") if path.is_file() else ""
        rows.append(
            {
                "path": str(path),
                "exists": path.exists(),
                "size_bytes": path.stat().st_size if path.exists() else 0,
                "sha256": sha256_file(path) or "",
                "http_200": "HTTP/1.1 200 OK" in text,
                "not_authenticated": "Not authenticated" in text,
                "canonical_or_matched_path": ";".join(
                    line.strip()
                    for line in text.splitlines()
                    if "Link:" in line or "x-matched-path:" in line
                ),
            }
        )
    return rows


def inspect_cfe_zip() -> dict[str, Any]:
    info: dict[str, Any] = {
        "zip_path": str(CFE_ZIP),
        "zip_exists": CFE_ZIP.exists(),
        "zip_size_bytes": CFE_ZIP.stat().st_size if CFE_ZIP.exists() else 0,
        "zip_sha256": sha256_file(CFE_ZIP) or "",
        "members": [],
        "csv_rows": 0,
        "columns": [],
        "date_min": "",
        "date_max": "",
        "symbol_count": 0,
        "symbols_sample": [],
        "futures_roots": [],
        "label_columns_present": [],
        "normal_control_columns_present": [],
        "order_lifecycle_columns_present": [],
        "has_bid_ask": False,
        "has_order_ids": False,
        "contract_fit": False,
        "rejection_reasons": [],
    }
    if not CFE_ZIP.exists():
        info["rejection_reasons"].append("zip_missing")
        return info

    with zipfile.ZipFile(CFE_ZIP) as archive:
        members = archive.infolist()
        info["members"] = [
            {"filename": member.filename, "file_size": member.file_size} for member in members
        ]
        csv_members = [member for member in members if member.filename.lower().endswith(".csv")]
        if not csv_members:
            info["rejection_reasons"].append("no_csv_member")
            return info
        member = csv_members[0]
        with archive.open(member) as handle:
            text_handle = (line.decode("utf-8", errors="replace") for line in handle)
            reader = csv.DictReader(text_handle)
            columns = reader.fieldnames or []
            info["columns"] = columns
            label_tokens = ["label", "spoof", "manip", "normal", "control", "case", "violation"]
            info["label_columns_present"] = [
                col for col in columns if any(token in col.lower() for token in label_tokens)
            ]
            info["normal_control_columns_present"] = [
                col for col in columns if any(token in col.lower() for token in ["normal", "control"])
            ]
            info["order_lifecycle_columns_present"] = [
                col
                for col in columns
                if any(token in col.lower() for token in ["order_id", "order_datetime", "fill_count"])
            ]
            info["has_bid_ask"] = "bid" in columns and "ask" in columns
            info["has_order_ids"] = "buy_order_id" in columns and "sell_order_id" in columns
            dates = []
            symbols = set()
            roots = set()
            rows = 0
            sample_rows = []
            for row in reader:
                rows += 1
                if rows <= 5:
                    sample_rows.append({key: row.get(key, "") for key in columns[:12]})
                dt = row.get("trade_datetime", "")
                if dt:
                    dates.append(dt[:10])
                if row.get("symbol"):
                    symbols.add(row["symbol"])
                if row.get("futures_root"):
                    roots.add(row["futures_root"])
            info["csv_rows"] = rows
            info["date_min"] = min(dates) if dates else ""
            info["date_max"] = max(dates) if dates else ""
            info["symbol_count"] = len(symbols)
            info["symbols_sample"] = sorted(symbols)[:20]
            info["futures_roots"] = sorted(roots)
            info["sample_rows"] = sample_rows

    if info["date_min"] == info["date_max"] == "2022-11-01":
        info["rejection_reasons"].append("single_day_sample_not_cross_period")
    if "VX" not in info["futures_roots"]:
        info["rejection_reasons"].append("not_vx_cfe")
    if not info["label_columns_present"]:
        info["rejection_reasons"].append("no_source_manipulation_or_normal_control_labels")
    if not info["normal_control_columns_present"]:
        info["rejection_reasons"].append("no_explicit_normal_control_column")
    if not (info["has_bid_ask"] and info["has_order_ids"]):
        info["rejection_reasons"].append("missing_order_lifecycle_fields")
    if info["date_min"] < "2011-01-01" or info["date_max"] > "2013-12-31":
        info["rejection_reasons"].append("not_oystacher_2011_2013_control_window")
    if info["csv_rows"] < 50_000:
        info["rejection_reasons"].append("below_board_broad_control_support_floor")
    info["contract_fit"] = not info["rejection_reasons"]
    return info


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)
    CMD_DIR.mkdir(parents=True, exist_ok=True)

    commands = []
    if CFE_ZIP.exists():
        commands.append(run_cmd("cfe_zip_listing", ["unzip", "-l", str(CFE_ZIP)]))
    header_rows = inspect_headers()
    cfe_info = inspect_cfe_zip()
    target_root_files = sorted(str(path) for path in R6_TARGET_ROOT.glob("*")) if R6_TARGET_ROOT.exists() else []

    source_control_evidence_acquired = False
    target_root_mutated = False
    accepted_rows_added = 0
    canonical_merge_allowed_now = False
    downstream_rerun_allowed_now = False

    write_csv(
        OUT_DIR / "r6_local_cfe_sample_header_readback_v1.csv",
        header_rows,
        [
            "path",
            "exists",
            "size_bytes",
            "sha256",
            "http_200",
            "not_authenticated",
            "canonical_or_matched_path",
        ],
    )
    write_csv(
        OUT_DIR / "r6_local_cfe_sample_member_summary_v1.csv",
        [
            {
                "zip_path": cfe_info["zip_path"],
                "zip_sha256": cfe_info["zip_sha256"],
                "member_count": len(cfe_info["members"]),
                "csv_rows": cfe_info["csv_rows"],
                "date_min": cfe_info["date_min"],
                "date_max": cfe_info["date_max"],
                "symbol_count": cfe_info["symbol_count"],
                "futures_roots": ";".join(cfe_info["futures_roots"]),
                "label_columns_present": ";".join(cfe_info["label_columns_present"]),
                "normal_control_columns_present": ";".join(
                    cfe_info["normal_control_columns_present"]
                ),
                "order_lifecycle_columns_present": ";".join(
                    cfe_info["order_lifecycle_columns_present"]
                ),
                "contract_fit": cfe_info["contract_fit"],
                "rejection_reasons": ";".join(cfe_info["rejection_reasons"]),
            }
        ],
        [
            "zip_path",
            "zip_sha256",
            "member_count",
            "csv_rows",
            "date_min",
            "date_max",
            "symbol_count",
            "futures_roots",
            "label_columns_present",
            "normal_control_columns_present",
            "order_lifecycle_columns_present",
            "contract_fit",
            "rejection_reasons",
        ],
    )

    summary = {
        "run_id": RUN_ID,
        "gate_result": GATE_RESULT,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "board_sha256_before_artifact": board_hash(),
        "scope": {
            "read_only_local_sample_applicability": True,
            "target_root_mutated": target_root_mutated,
            "external_requests_sent": False,
            "vendor_portal_used": False,
            "canonical_merge": False,
            "downstream_promotion_rerun": False,
            "trade_claim": False,
            "update_goal": False,
        },
        "cfe_sample": cfe_info,
        "header_readback": header_rows,
        "r6_target_root": {
            "path": str(R6_TARGET_ROOT),
            "exists": R6_TARGET_ROOT.exists(),
            "files": target_root_files,
        },
        "promotion": {
            "accepted_rows_added": accepted_rows_added,
            "source_control_evidence_acquired": source_control_evidence_acquired,
            "target_root_mutated": target_root_mutated,
            "canonical_merge_allowed_now": canonical_merge_allowed_now,
            "downstream_rerun_allowed_now": downstream_rerun_allowed_now,
            "strict_full_objective": False,
            "trade_usable": False,
            "update_goal": False,
        },
        "decision": (
            "The local CFE sample is useful schema context for VX trades/order IDs/bid-ask, "
            "but it is a one-day 2022 sample with no source normal-control labels, no "
            "Oystacher-era date fit, and no ticket/license/export provenance. It does not "
            "satisfy the R6 owner-export control contract."
        ),
        "next": (
            "Continue only from explicit source/control approval, verifier-native R6 owner-export "
            "rows with valid controls, source-owned R5 recency rows, verifier-native R3 "
            "MainRegimeV2 labels, or a genuinely new accepted cross-timeframe MainRegimeV2 source export."
        ),
        "commands": commands,
    }
    json_path = OUT_DIR / "r6_local_cfe_sample_control_applicability_v1.json"
    json_path.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")

    reasons = "; ".join(cfe_info["rejection_reasons"]) or "none"
    md_lines = [
        "# R6 Local CFE Sample Control Applicability v1",
        "",
        f"Run id: `{RUN_ID}`",
        "",
        f"Gate result: `{GATE_RESULT}`",
        "",
        f"Board sha256 before artifact: `{summary['board_sha256_before_artifact']}`",
        "",
        "## Scope",
        "",
        (
            "Read-only applicability audit for local CFE/Cboe sample files after the "
            "`063906` objective audit. This does not copy files into the R6 target root, "
            "approve controls, run canonical merge, rerun downstream promotion, make a "
            "trade claim, or call `update_goal`."
        ),
        "",
        "## Local Sample Readback",
        "",
        f"- Zip present: `{cfe_info['zip_exists']}`.",
        f"- Zip SHA-256: `{cfe_info['zip_sha256']}`.",
        f"- Member count: `{len(cfe_info['members'])}`.",
        f"- CSV rows: `{cfe_info['csv_rows']}`.",
        f"- Date span: `{cfe_info['date_min']}` to `{cfe_info['date_max']}`.",
        f"- Futures roots: `{','.join(cfe_info['futures_roots'])}`.",
        f"- Symbol count: `{cfe_info['symbol_count']}`.",
        f"- Has bid/ask: `{cfe_info['has_bid_ask']}`; has buy/sell order ids: `{cfe_info['has_order_ids']}`.",
        f"- Label/control columns: `{','.join(cfe_info['label_columns_present']) or 'none'}`.",
        f"- Rejection reasons: `{reasons}`.",
        "",
        "## Header Readback",
        "",
        "| File | Exists | HTTP 200 | Not Authenticated | SHA-256 |",
        "|---|---:|---:|---:|---|",
    ]
    for row in header_rows:
        md_lines.append(
            f"| `{row['path']}` | `{row['exists']}` | `{row['http_200']}` | "
            f"`{row['not_authenticated']}` | `{row['sha256']}` |"
        )
    md_lines.extend(
        [
            "",
            "## Decision",
            "",
            (
                "The CFE sample has useful order-lifecycle schema context, but it is not "
                "accepted R6 owner/export control evidence. It covers a single RTH sample "
                "day in `2022`, has no source manipulation/normal-control labels, has no "
                "ticket/license/export/support provenance, and does not cover the "
                "Oystacher 2011-2013 control window."
            ),
            "",
            (
                "Promotion remains blocked: accepted rows added `0`, source/control evidence "
                "acquired false, target root mutated false, canonical merge false, downstream "
                "promotion rerun false, strict full objective false, trade usable false, and "
                "`update_goal=false`."
            ),
            "",
            "## Next",
            "",
            (
                "Continue only from explicit source/control approval, verifier-native R6 "
                "owner-export rows with valid controls, source-owned R5 recency rows, "
                "verifier-native R3 `MainRegimeV2` labels, or a genuinely new accepted "
                "cross-timeframe `MainRegimeV2` source export."
            ),
            "",
            "## Artifacts",
            "",
            f"- JSON: `{json_path.relative_to(REPO)}`",
            f"- Header CSV: `{(OUT_DIR / 'r6_local_cfe_sample_header_readback_v1.csv').relative_to(REPO)}`",
            f"- Member summary CSV: `{(OUT_DIR / 'r6_local_cfe_sample_member_summary_v1.csv').relative_to(REPO)}`",
            f"- Assertions: `{(CHECK_DIR / 'r6_local_cfe_sample_control_applicability_v1_assertions.out').relative_to(REPO)}`",
        ]
    )
    report_path = OUT_DIR / "r6_local_cfe_sample_control_applicability_v1.md"
    report_path.write_text("\n".join(md_lines) + "\n", encoding="utf-8")

    assertion_lines = [
        f"gate_result={GATE_RESULT}",
        f"cfe_sample_contract_fit={cfe_info['contract_fit']}",
        "accepted_rows_added=0",
        "source_control_evidence_acquired_false=True",
        "target_root_mutated_false=True",
        "canonical_merge_allowed_now_false=True",
        "downstream_rerun_allowed_now_false=True",
        "strict_full_objective_false=True",
        "trade_usable_false=True",
        "update_goal_false=True",
    ]
    assertions_path = CHECK_DIR / "r6_local_cfe_sample_control_applicability_v1_assertions.out"
    assertions_path.write_text("\n".join(assertion_lines) + "\n", encoding="utf-8")
    print(report_path)
    return 0 if not cfe_info["contract_fit"] else 1


if __name__ == "__main__":
    sys.exit(main())
