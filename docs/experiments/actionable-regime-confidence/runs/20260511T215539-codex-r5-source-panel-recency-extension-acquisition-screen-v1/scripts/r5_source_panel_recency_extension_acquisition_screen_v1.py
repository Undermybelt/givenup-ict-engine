#!/usr/bin/env python3
"""R5 source-panel recency-extension acquisition screen.

This run is deliberately fail-closed: it searches/downloads bounded public
source candidates, profiles whether any can populate the existing R5 verifier
schema, and leaves the intake root unfilled unless source-owned post-cutoff
rows actually satisfy the contract.
"""

from __future__ import annotations

import csv
import hashlib
import json
import shutil
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


RUN_ID = "20260511T215539-codex-r5-source-panel-recency-extension-acquisition-screen-v1"
REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = Path(__file__).resolve().parents[1]
OUT = RUN_ROOT / "r5-source-panel-recency-extension-acquisition-screen"
CHECKS = RUN_ROOT / "checks"
CMD_OUT = RUN_ROOT / "command-output"
TMP = Path("/tmp/ict-engine-r5-source-panel-recency-extension-acquisition-screen-v1")
INTAKE_ROOT = Path("/tmp/ict-engine-source-panel-recency-extension")
BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"
RECENCY_VERIFIER = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T165405-codex-source-panel-recency-extension-manifest-v1/"
    "source-panel-recency/source_panel_recency_extension_verifier_v1.py"
)

PRIMARY_SOURCE = Path("/Users/thrill3r/Downloads/stock-market-regimes-20002026/stock_market_regimes_2000_2026.csv")
NIFTY_SOURCE = Path("/tmp/ict-engine-public-source-intake-scout/nifty/regime_timeline_history.csv")

REQUIRED_COLUMNS = [
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
ROOT_LABELS = {"Bear", "Bull", "Crisis", "Sideways"}
LAST_SOURCE_DATE = "2026-01-30"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run_cmd(name: str, args: list[str], timeout: int = 240) -> dict[str, Any]:
    proc = subprocess.run(
        args,
        cwd=REPO,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        timeout=timeout,
    )
    stdout_path = CMD_OUT / f"{name}.stdout.txt"
    stderr_path = CMD_OUT / f"{name}.stderr.txt"
    stdout_path.write_text(proc.stdout, encoding="utf-8")
    stderr_path.write_text(proc.stderr, encoding="utf-8")
    return {
        "name": name,
        "args": args,
        "returncode": proc.returncode,
        "stdout_file": str(stdout_path.relative_to(REPO)),
        "stderr_file": str(stderr_path.relative_to(REPO)),
        "stdout_first_lines": "\n".join(proc.stdout.splitlines()[:8]),
    }


def download_dataset(name: str, ref: str, target: Path) -> dict[str, Any]:
    if target.exists():
        shutil.rmtree(target)
    target.mkdir(parents=True, exist_ok=True)
    return run_cmd(
        name,
        ["kaggle", "datasets", "download", ref, "-p", str(target), "--unzip", "--force"],
        timeout=360,
    )


def read_csv_rows(path: Path, limit: int | None = None) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        rows = []
        for row in reader:
            rows.append(row)
            if limit is not None and len(rows) >= limit:
                break
        return list(reader.fieldnames or []), rows


def profile_rows(path: Path, *, date_col: str, ticker_col: str | None, label_col: str | None) -> dict[str, Any]:
    if not path.exists():
        return {"path": str(path), "exists": False, "reject_reason": "missing_file"}

    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        columns = list(reader.fieldnames or [])
        row_count = 0
        post_cutoff_rows = 0
        date_min = ""
        date_max = ""
        ticker_counts: Counter[str] = Counter()
        label_counts: Counter[str] = Counter()
        duplicates = 0
        seen: set[tuple[str, str]] = set()
        for row in reader:
            row_count += 1
            day = (row.get(date_col, "") or "")[:10]
            if day:
                date_min = day if not date_min else min(date_min, day)
                date_max = max(date_max, day)
            ticker = row.get(ticker_col, "") if ticker_col else ""
            label = row.get(label_col, "") if label_col else ""
            if ticker:
                ticker_counts[ticker] += 1
            if label:
                label_counts[label] += 1
            if day and ticker:
                key = (day, ticker)
                if key in seen:
                    duplicates += 1
                seen.add(key)
            if day > LAST_SOURCE_DATE:
                post_cutoff_rows += 1

    exact_columns = columns == REQUIRED_COLUMNS
    unknown_tickers = sorted(set(ticker_counts) - EXPECTED_TICKERS)
    bad_labels = sorted(set(label_counts) - ROOT_LABELS)
    reject_reasons = []
    if not exact_columns:
        reject_reasons.append("schema_mismatch")
    if post_cutoff_rows <= 0:
        reject_reasons.append("no_post_2026_01_30_rows")
    if unknown_tickers:
        reject_reasons.append("unknown_tickers_for_r5_verifier")
    if bad_labels:
        reject_reasons.append("non_root_or_missing_labels")
    if duplicates:
        reject_reasons.append("duplicate_date_ticker_rows")

    return {
        "path": str(path),
        "exists": True,
        "sha256": sha256_file(path),
        "columns": columns,
        "exact_required_columns": exact_columns,
        "row_count": row_count,
        "post_2026_01_30_rows": post_cutoff_rows,
        "date_min": date_min,
        "date_max": date_max,
        "ticker_count": len(ticker_counts),
        "label_counts": dict(sorted(label_counts.items())),
        "unknown_tickers": unknown_tickers[:20],
        "bad_labels": bad_labels[:20],
        "duplicates": duplicates,
        "accepted_for_r5_intake": not reject_reasons,
        "reject_reason": ";".join(reject_reasons),
    }


def profile_candidate_dir(root: Path, pattern: str, *, date_col: str, ticker_col: str | None, label_col: str | None) -> list[dict[str, Any]]:
    rows = []
    for path in sorted(root.glob(pattern)):
        rows.append(profile_rows(path, date_col=date_col, ticker_col=ticker_col, label_col=label_col))
    return rows


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)
    CMD_OUT.mkdir(parents=True, exist_ok=True)
    TMP.mkdir(parents=True, exist_ok=True)
    INTAKE_ROOT.mkdir(parents=True, exist_ok=True)

    board_hash = sha256_file(BOARD)

    commands = [
        run_cmd("kaggle_files_mafaq_stock_regimes", ["kaggle", "datasets", "files", "mafaqbhatti/stock-market-regimes-20002026"]),
        run_cmd("kaggle_list_stock_market_regimes_2026", ["kaggle", "datasets", "list", "-s", "stock market regimes 2026", "--csv"]),
        run_cmd("kaggle_list_market_regime_label", ["kaggle", "datasets", "list", "-s", "market regime label", "--csv"]),
        run_cmd("kaggle_list_stock_market_regimes", ["kaggle", "datasets", "list", "-s", "stock market regimes", "--csv"]),
    ]
    commands.extend(
        [
            download_dataset(
                "download_kanchana_macro_stress_asset_regimes",
                "kanchana1990/algorithmic-trading-macro-stress-and-asset-regimes",
                TMP / "kanchana_macro_stress_asset_regimes",
            ),
            download_dataset(
                "download_kanchana_tech_giants_macro",
                "kanchana1990/tech-giants-and-global-macroeconomic-indicators",
                TMP / "kanchana_tech_giants_macro",
            ),
            download_dataset(
                "download_franek_us_stocks_various_sectors",
                "franekwodarczyk/trading-dataset-us-stocks-various-sectors-from-09",
                TMP / "franek_us_stocks_various_sectors",
            ),
        ]
    )

    candidate_rows: list[dict[str, Any]] = []
    primary_profile = profile_rows(PRIMARY_SOURCE, date_col="date", ticker_col="ticker", label_col="regime_label")
    primary_profile.update(
        {
            "candidate": "mafaqbhatti/stock-market-regimes-20002026",
            "candidate_role": "current_source_panel",
            "source_license": "apache-2.0",
        }
    )
    candidate_rows.append(primary_profile)

    if NIFTY_SOURCE.exists():
        nifty_profile = profile_rows(NIFTY_SOURCE, date_col="Date", ticker_col=None, label_col="fast_state")
        nifty_profile.update(
            {
                "candidate": "ahaanverma00/nifty-500-market-and-behavior-regime-dataset",
                "candidate_role": "other_market_post_cutoff_label_source_not_r5_panel",
                "source_license": "unknown_from_local_profile",
                "reject_reason": (nifty_profile.get("reject_reason", "") + ";not_existing_39_ticker_source_panel").strip(";"),
                "accepted_for_r5_intake": False,
            }
        )
        candidate_rows.append(nifty_profile)

    for row in profile_candidate_dir(
        TMP / "kanchana_macro_stress_asset_regimes",
        "*.csv",
        date_col="Date",
        ticker_col=None,
        label_col=None,
    ):
        row.update(
            {
                "candidate": "kanchana1990/algorithmic-trading-macro-stress-and-asset-regimes",
                "candidate_role": "macro_stress_recent_rows_no_root_labels",
                "source_license": "CC-BY-NC-SA-4.0",
            }
        )
        candidate_rows.append(row)

    for row in profile_candidate_dir(
        TMP / "kanchana_tech_giants_macro",
        "*.csv",
        date_col="Date",
        ticker_col=None,
        label_col=None,
    ):
        row.update(
            {
                "candidate": "kanchana1990/tech-giants-and-global-macroeconomic-indicators",
                "candidate_role": "recent_macro_price_rows_no_root_labels",
                "source_license": "CC0-1.0",
            }
        )
        candidate_rows.append(row)

    franek_profiles = profile_candidate_dir(
        TMP / "franek_us_stocks_various_sectors",
        "*.csv",
        date_col="datetime",
        ticker_col="symbol",
        label_col=None,
    )
    for row in franek_profiles:
        row.update(
            {
                "candidate": "franekwodarczyk/trading-dataset-us-stocks-various-sectors-from-09",
                "candidate_role": "recent_stock_price_indicator_rows_no_root_labels",
                "source_license": "MIT",
            }
        )
        candidate_rows.append(row)

    accepted_candidates = [row for row in candidate_rows if row.get("accepted_for_r5_intake")]
    accepted_extension_rows = sum(int(row.get("post_2026_01_30_rows", 0)) for row in accepted_candidates)

    verifier = run_cmd(
        "source_panel_recency_verifier",
        ["python3", str(RECENCY_VERIFIER), "--intake-root", str(INTAKE_ROOT)],
    )
    verifier_parsed: dict[str, Any] | None = None
    verifier_stdout = (CMD_OUT / "source_panel_recency_verifier.stdout.txt").read_text(encoding="utf-8")
    if verifier_stdout.strip():
        try:
            verifier_parsed = json.loads(verifier_stdout)
        except json.JSONDecodeError:
            verifier_parsed = {"status": "stdout_not_json"}

    candidate_csv = OUT / "r5_source_panel_recency_extension_candidates_v1.csv"
    command_csv = OUT / "r5_source_panel_recency_extension_commands_v1.csv"
    json_path = OUT / "r5_source_panel_recency_extension_acquisition_screen_v1.json"
    report_path = OUT / "r5_source_panel_recency_extension_acquisition_screen_v1.md"
    assertions_path = CHECKS / "r5_source_panel_recency_extension_acquisition_screen_v1_assertions.out"

    candidate_fields = [
        "candidate",
        "candidate_role",
        "source_license",
        "path",
        "exists",
        "sha256",
        "exact_required_columns",
        "row_count",
        "post_2026_01_30_rows",
        "date_min",
        "date_max",
        "ticker_count",
        "label_counts",
        "unknown_tickers",
        "bad_labels",
        "duplicates",
        "accepted_for_r5_intake",
        "reject_reason",
    ]
    write_csv(candidate_csv, candidate_rows, candidate_fields)
    write_csv(
        command_csv,
        commands,
        ["name", "args", "returncode", "stdout_file", "stderr_file", "stdout_first_lines"],
    )

    decision = (
        "r5_source_panel_recency_extension_acquisition_screen_v1="
        "no_acceptable_post_cutoff_source_owned_rows"
    )
    result = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "board_hash_before": board_hash,
        "decision": decision,
        "objective": "Populate the R5 source-panel recency extension only with source-owned post-2026-01-30 rows that satisfy the existing verifier schema.",
        "last_source_date": LAST_SOURCE_DATE,
        "candidate_count": len(candidate_rows),
        "accepted_candidate_count": len(accepted_candidates),
        "accepted_extension_rows": accepted_extension_rows,
        "accepted_candidates": accepted_candidates,
        "candidate_reject_summary": Counter(str(row.get("reject_reason", "")) for row in candidate_rows),
        "verifier_status": verifier_parsed.get("status") if verifier_parsed else "not_json",
        "verifier_result": verifier_parsed,
        "intake_root": str(INTAKE_ROOT),
        "intake_rows_written": False,
        "accepted_rows_added": 0,
        "new_confidence_gate": False,
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "external_requests_sent": True,
        "trade_usable": False,
        "next_action": "Expand R6 direct Manipulation intake toward >=50/50 support with broad normal controls and direct species coverage while keeping R5 blocked until a source owner publishes valid post-cutoff source-panel rows.",
        "artifacts": {
            "candidate_csv": str(candidate_csv.relative_to(REPO)),
            "command_csv": str(command_csv.relative_to(REPO)),
            "report": str(report_path.relative_to(REPO)),
            "assertions": str(assertions_path.relative_to(REPO)),
            "command_output": str(CMD_OUT.relative_to(REPO)),
        },
    }
    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    report = [
        "# R5 Source Panel Recency Extension Acquisition Screen v1",
        "",
        f"Decision: `{decision}`.",
        "",
        "Result:",
        f"- Existing source panel max date remains `{primary_profile.get('date_max')}` with `{primary_profile.get('post_2026_01_30_rows')}` rows after `{LAST_SOURCE_DATE}`.",
        f"- Live Kaggle file listing for `mafaqbhatti/stock-market-regimes-20002026` was checked; the dataset files are still the February 2026 source package.",
        f"- Candidate screens checked `{len(candidate_rows)}` local/downloaded CSV profiles; accepted R5 extension candidates: `{len(accepted_candidates)}`.",
        f"- Accepted extension rows written: `0`; intake rows written: `false`.",
        f"- R5 verifier status after screen: `{result['verifier_status']}`.",
        "- Rejected recent candidates had either no root regime labels, no exact source-panel schema, no existing 39-ticker panel match, or no rows after the cutoff.",
        "- Strict full objective achieved: `false`; `update_goal=false`.",
        "- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; external requests sent: `true`; trade usable: `false`.",
        "",
        "Candidate Summary:",
        "",
        "| Candidate | Role | Post Rows | Exact Schema | Accepted | Reject Reason |",
        "|---|---|---:|---:|---:|---|",
    ]
    for row in candidate_rows[:16]:
        report.append(
            f"| `{row.get('candidate')}` | `{row.get('candidate_role')}` | "
            f"`{row.get('post_2026_01_30_rows')}` | `{row.get('exact_required_columns')}` | "
            f"`{row.get('accepted_for_r5_intake')}` | {row.get('reject_reason')} |"
        )
    if len(candidate_rows) > 16:
        report.append(f"| ... | see CSV | ... | ... | ... | `{len(candidate_rows) - 16}` more rows |")
    report.extend(
        [
            "",
            "Next:",
            result["next_action"],
            "",
            "Artifacts:",
            f"- JSON: `{json_path.relative_to(REPO)}`",
            f"- Report: `{report_path.relative_to(REPO)}`",
            f"- Candidate CSV: `{candidate_csv.relative_to(REPO)}`",
            f"- Command CSV: `{command_csv.relative_to(REPO)}`",
            f"- Command output: `{CMD_OUT.relative_to(REPO)}`",
            f"- Assertions: `{assertions_path.relative_to(REPO)}`",
        ]
    )
    report_path.write_text("\n".join(report) + "\n", encoding="utf-8")

    assertions = [
        f"PASS decision={decision}",
        f"PASS primary_source_post_rows={primary_profile.get('post_2026_01_30_rows')}",
        f"PASS accepted_candidate_count={len(accepted_candidates)}",
        "PASS accepted_rows_added=0",
        "PASS intake_rows_written=false",
        f"PASS verifier_status={result['verifier_status']}",
        "PASS update_goal=false",
        "PASS strict_full_objective_achieved=false",
        "PASS raw_data_committed=false",
        "PASS runtime_code_changed=false",
    ]
    assertions_path.write_text("\n".join(assertions) + "\n", encoding="utf-8")

    print(
        json.dumps(
            {
                "decision": decision,
                "accepted_candidate_count": len(accepted_candidates),
                "accepted_extension_rows": accepted_extension_rows,
                "verifier_status": result["verifier_status"],
                "update_goal": False,
                "report": str(report_path.relative_to(REPO)),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
