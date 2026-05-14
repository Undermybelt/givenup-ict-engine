#!/usr/bin/env python3
"""Probe for source-owned post-cutoff rows for the R5 recency extension gate."""

from __future__ import annotations

import csv
import hashlib
import json
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


RUN_ID = "20260511T215420-codex-r5-recency-source-acquisition-probe-v1"
REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = Path(__file__).resolve().parents[1]
OUT = RUN_ROOT / "r5-recency-source-acquisition-probe"
CHECKS = RUN_ROOT / "checks"
CMD = RUN_ROOT / "command-output"

SOURCE_PANEL_ROOT = Path("/tmp/ict-engine-source-panel-recency-extension")
SOURCE_PANEL_VERIFIER = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T165405-codex-source-panel-recency-extension-manifest-v1/"
    "source-panel-recency/source_panel_recency_extension_verifier_v1.py"
)
STOCK_SOURCE = Path("/Users/thrill3r/Downloads/stock-market-regimes-20002026/stock_market_regimes_2000_2026.csv")
NIFTY_SOURCE = Path("/tmp/ict-engine-public-source-intake-scout/nifty/regime_timeline_history.csv")
KAGGLE_REF = "mafaqbhatti/stock-market-regimes-20002026"
LAST_SOURCE_DATE = "2026-01-30"
EXPECTED_R5_COLUMNS = [
    "date",
    "ticker",
    "close",
    "returns",
    "volatility",
    "regime_label",
    "regime_confidence",
    "macro_context",
    "unemployment_rate",
    "fed_funds_rate",
    "cpi",
    "10y_treasury",
    "2y_treasury",
    "vix",
]
EXPECTED_TICKERS = {
    "AAPL",
    "ABBV",
    "AMD",
    "AMZN",
    "BA",
    "BAC",
    "CAT",
    "COP",
    "CSCO",
    "CVX",
    "DIS",
    "GE",
    "GOOGL",
    "GS",
    "HD",
    "INTC",
    "JNJ",
    "JPM",
    "MCD",
    "META",
    "MS",
    "MSFT",
    "NFLX",
    "NKE",
    "NVDA",
    "PFE",
    "SBUX",
    "T",
    "TMO",
    "TSLA",
    "UNH",
    "VZ",
    "WFC",
    "WMT",
    "XOM",
    "^DJI",
    "^GSPC",
    "^IXIC",
    "^RUT",
}


def sha256_file(path: Path) -> str | None:
    if not path.exists():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run_command(name: str, command: list[str]) -> dict[str, Any]:
    proc = subprocess.run(command, cwd=REPO, text=True, capture_output=True, check=False)
    stdout = CMD / f"{name}.stdout.txt"
    stderr = CMD / f"{name}.stderr.txt"
    exit_path = CMD / f"{name}.exit"
    stdout.write_text(proc.stdout, encoding="utf-8")
    stderr.write_text(proc.stderr, encoding="utf-8")
    exit_path.write_text(f"{proc.returncode}\n", encoding="utf-8")
    return {
        "command": command,
        "returncode": proc.returncode,
        "stdout": str(stdout.relative_to(REPO)),
        "stderr": str(stderr.relative_to(REPO)),
        "exit": str(exit_path.relative_to(REPO)),
    }


def summarize_csv(path: Path, source_type: str) -> dict[str, Any]:
    summary: dict[str, Any] = {
        "path": str(path),
        "exists": path.exists(),
        "source_type": source_type,
        "sha256": sha256_file(path),
    }
    if not path.exists():
        return summary
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        fields = reader.fieldnames or []
        rows = list(reader)
    date_key = "date" if "date" in fields else "Date" if "Date" in fields else None
    ticker_key = "ticker" if "ticker" in fields else None
    label_key = "regime_label" if "regime_label" in fields else "combined_state" if "combined_state" in fields else None
    dates = [row.get(date_key, "")[:10] for row in rows if date_key and row.get(date_key)]
    tickers = {row.get(ticker_key, "") for row in rows if ticker_key and row.get(ticker_key)}
    labels = Counter(row.get(label_key, "") for row in rows if label_key)
    post_cutoff_rows = [row for row in rows if date_key and row.get(date_key, "")[:10] > LAST_SOURCE_DATE]
    missing_cols = [col for col in EXPECTED_R5_COLUMNS if col not in fields]
    unknown_tickers = sorted(tickers - EXPECTED_TICKERS) if tickers else []
    summary.update(
        {
            "fields": fields,
            "row_count": len(rows),
            "date_min": min(dates) if dates else None,
            "date_max": max(dates) if dates else None,
            "post_cutoff_row_count": len(post_cutoff_rows),
            "ticker_count": len(tickers) if tickers else None,
            "unknown_tickers": unknown_tickers[:40],
            "label_counts": dict(sorted(labels.items())),
            "r5_schema_compatible": not missing_cols and not unknown_tickers,
            "missing_r5_columns": missing_cols,
        }
    )
    return summary


def parse_verifier(command_result: dict[str, Any]) -> dict[str, Any]:
    stdout_path = REPO / command_result["stdout"]
    try:
        loaded = json.loads(stdout_path.read_text(encoding="utf-8"))
        return loaded if isinstance(loaded, dict) else {"status": "unparsed"}
    except json.JSONDecodeError:
        return {"status": "unparsed"}


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)
    CMD.mkdir(parents=True, exist_ok=True)

    local_candidates = [
        summarize_csv(STOCK_SOURCE, "r5_expected_stock_panel"),
        summarize_csv(NIFTY_SOURCE, "nifty_source_label_timeline"),
    ]
    kaggle_list = run_command("kaggle_datasets_list_stock_market_regimes", ["kaggle", "datasets", "list", "-s", "stock market regimes 2000 2026"])
    kaggle_files = run_command("kaggle_dataset_files_stock_market_regimes", ["kaggle", "datasets", "files", KAGGLE_REF])
    verifier_command = run_command(
        "source_panel_recency_verifier",
        ["python3", str(SOURCE_PANEL_VERIFIER), "--intake-root", str(SOURCE_PANEL_ROOT)],
    )
    verifier = parse_verifier(verifier_command)

    compatible_post_cutoff_sources = [
        item for item in local_candidates
        if item.get("r5_schema_compatible") and int(item.get("post_cutoff_row_count") or 0) > 0
    ]
    decision = "r5_recency_source_acquisition_probe_v1=no_source_owned_post_cutoff_rows_found"
    result = {
        "run_id": RUN_ID,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "decision": decision,
        "last_source_date_required_after": LAST_SOURCE_DATE,
        "local_candidates": local_candidates,
        "compatible_post_cutoff_source_count": len(compatible_post_cutoff_sources),
        "kaggle_dataset_ref": KAGGLE_REF,
        "kaggle_list_command": kaggle_list,
        "kaggle_files_command": kaggle_files,
        "source_panel_recency_verifier": {
            "command": verifier_command,
            "parsed": verifier,
        },
        "intake_files_written": False,
        "accepted_rows_added": 0,
        "new_confidence_gate": False,
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "external_requests_sent": True,
        "trade_usable": False,
        "next": "Find source-owned post-2026-01-30 stock-panel regime rows or keep R5 blocked; do not synthesize labels from price providers.",
    }

    json_path = OUT / "r5_recency_source_acquisition_probe_v1.json"
    report_path = OUT / "r5_recency_source_acquisition_probe_v1.md"
    candidates_csv = OUT / "r5_recency_source_acquisition_candidates_v1.csv"
    assertions_path = CHECKS / "r5_recency_source_acquisition_probe_v1_assertions.out"
    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    with candidates_csv.open("w", newline="", encoding="utf-8") as handle:
        fields = [
            "source_type",
            "path",
            "exists",
            "row_count",
            "date_min",
            "date_max",
            "post_cutoff_row_count",
            "r5_schema_compatible",
            "missing_r5_columns",
            "unknown_tickers",
            "sha256",
        ]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for item in local_candidates:
            writer.writerow({field: json.dumps(item.get(field), sort_keys=True) if isinstance(item.get(field), (list, dict)) else item.get(field) for field in fields})

    stock = local_candidates[0]
    nifty = local_candidates[1]
    report_path.write_text(
        "\n".join([
            "# R5 Recency Source Acquisition Probe v1",
            "",
            f"- Decision: `{decision}`.",
            f"- Required R5 extension cutoff: rows must be after `{LAST_SOURCE_DATE}`.",
            f"- Local stock source rows: `{stock.get('row_count')}`; date range `{stock.get('date_min')}..{stock.get('date_max')}`; post-cutoff rows `{stock.get('post_cutoff_row_count')}`.",
            f"- Local NIFTY source rows: `{nifty.get('row_count')}`; date range `{nifty.get('date_min')}..{nifty.get('date_max')}`; post-cutoff rows `{nifty.get('post_cutoff_row_count')}`; R5 schema compatible `{nifty.get('r5_schema_compatible')}`.",
            f"- Kaggle dataset ref checked: `{KAGGLE_REF}`; files command return code `{kaggle_files['returncode']}`.",
            f"- Source-panel recency verifier: `{verifier.get('status')}` / `{verifier.get('reason')}`.",
            "- No `/tmp/ict-engine-source-panel-recency-extension` rows were written because no source-owned R5-compatible post-cutoff rows were found.",
            "- Accepted rows added: `0`; new confidence gate: `false`.",
            "- Strict full objective achieved: `false`; `update_goal=false`.",
            "- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; external requests sent: `true` (Kaggle metadata only); trade usable: `false`.",
            "",
            "Artifacts:",
            f"- JSON: `{json_path.relative_to(REPO)}`",
            f"- Report: `{report_path.relative_to(REPO)}`",
            f"- Candidate CSV: `{candidates_csv.relative_to(REPO)}`",
            f"- Kaggle files stdout: `{kaggle_files['stdout']}`",
            f"- Verifier stdout: `{verifier_command['stdout']}`",
            f"- Assertions: `{assertions_path.relative_to(REPO)}`",
        ]) + "\n",
        encoding="utf-8",
    )
    assertions_path.write_text(
        "\n".join([
            f"PASS decision={decision}",
            f"PASS stock_source_date_max={stock.get('date_max')}",
            f"PASS stock_source_post_cutoff_rows={stock.get('post_cutoff_row_count')}",
            f"PASS compatible_post_cutoff_source_count={len(compatible_post_cutoff_sources)}",
            f"PASS source_panel_recency_status={verifier.get('status')}",
            f"PASS source_panel_recency_reason={verifier.get('reason')}",
            "PASS intake_files_written=false",
            "PASS accepted_rows_added=0",
            "PASS new_confidence_gate=false",
            "PASS strict_full_objective_achieved=false",
            "PASS update_goal=false",
            "PASS raw_data_committed=false",
            "PASS external_requests_sent=true_metadata_only",
        ]) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "decision": decision,
        "stock_source_date_max": stock.get("date_max"),
        "stock_source_post_cutoff_rows": stock.get("post_cutoff_row_count"),
        "compatible_post_cutoff_source_count": len(compatible_post_cutoff_sources),
        "source_panel_recency_status": verifier.get("status"),
        "source_panel_recency_reason": verifier.get("reason"),
        "report": str(report_path.relative_to(REPO)),
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
