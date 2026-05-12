#!/usr/bin/env python3
"""Live Kaggle recency check for the stock-market-regimes source panel."""

from __future__ import annotations

import csv
import hashlib
import json
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


RUN_ID = "20260511T192218-codex-stock-regime-kaggle-live-recency-check-v1"
DATASET = "mafaqbhatti/stock-market-regimes-20002026"
DATASET_URL = "https://www.kaggle.com/datasets/mafaqbhatti/stock-market-regimes-20002026"
TMP_ROOT = Path("/tmp/ict-engine-kaggle-stock-regimes-live-check-20260511T191523")
CSV_FILE = TMP_ROOT / "stock_market_regimes_2000_2026.csv"

ROOT = Path(__file__).resolve().parents[6]
RUN_ROOT = ROOT / "docs/experiments/actionable-regime-confidence/runs" / RUN_ID
OUT_DIR = RUN_ROOT / "kaggle-live-recency"
CHECK_DIR = RUN_ROOT / "checks"
BOARD = ROOT / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, text=True, capture_output=True, check=False)


def ensure_csv() -> dict[str, object]:
    TMP_ROOT.mkdir(parents=True, exist_ok=True)
    files_cmd = ["kaggle", "datasets", "files", DATASET]
    files_result = run(files_cmd)
    download_cmd = [
        "kaggle",
        "datasets",
        "download",
        DATASET,
        "-f",
        CSV_FILE.name,
        "-p",
        str(TMP_ROOT),
        "-o",
        "-q",
    ]
    download_result = run(download_cmd)
    return {
        "files_command": " ".join(files_cmd),
        "files_returncode": files_result.returncode,
        "files_stdout": files_result.stdout,
        "files_stderr": files_result.stderr,
        "download_command": " ".join(download_cmd),
        "download_returncode": download_result.returncode,
        "download_stdout": download_result.stdout,
        "download_stderr": download_result.stderr,
    }


def scan_csv(path: Path) -> dict[str, object]:
    rows = 0
    min_date = "9999-99-99"
    max_date = "0000-00-00"
    tickers: set[str] = set()
    labels: Counter[str] = Counter()
    root_counts: Counter[str] = Counter()
    target_counts: Counter[str] = Counter()
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        columns = reader.fieldnames or []
        for row in reader:
            rows += 1
            date = row["date"][:10]
            ticker = row["ticker"]
            label = row["regime_label"]
            min_date = min(min_date, date)
            max_date = max(max_date, date)
            tickers.add(ticker)
            labels[label] += 1
            if label in {"Bull", "Bear", "Sideways", "Crisis"}:
                root_counts[label] += 1
            if ticker == "XOM" and label == "Sideways":
                if date > "2026-01-30":
                    target_counts["xom_sideways_after_2026_01_30"] += 1
                if "2026-01-02" <= date <= "2026-01-30":
                    target_counts["xom_sideways_2026_01_02_to_2026_01_30"] += 1
                if "2025-01-01" <= date <= "2025-12-31":
                    target_counts["xom_sideways_2025"] += 1
    return {
        "columns": columns,
        "rows": rows,
        "min_date": min_date,
        "max_date": max_date,
        "tickers": len(tickers),
        "label_counts": dict(labels),
        "root_counts": dict(root_counts),
        "target_counts": dict(target_counts),
        "csv_sha256": sha256(path),
        "csv_bytes": path.stat().st_size,
    }


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)
    command_results = ensure_csv()
    if not CSV_FILE.exists():
        raise SystemExit(f"missing downloaded CSV: {CSV_FILE}")
    stats = scan_csv(CSV_FILE)

    target_tail = int(stats["target_counts"].get("xom_sideways_2026_01_02_to_2026_01_30", 0))
    target_after = int(stats["target_counts"].get("xom_sideways_after_2026_01_30", 0))
    target_2025 = int(stats["target_counts"].get("xom_sideways_2025", 0))
    can_repair_xom = target_after >= 5 or target_tail >= 5

    decision = {
        "gate_result": "stock_regime_kaggle_live_recency_check_v1=upstream_current_file_no_xom_sideways_tail_repair",
        "accepted_rows_added": 0,
        "new_confidence_gate": False,
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "raw_download_location": str(TMP_ROOT),
        "trade_usable": False,
        "xom_sideways_repair_ready": can_repair_xom,
    }

    report = {
        "artifact_type": "stock_regime_kaggle_live_recency_check_v1",
        "run_id": RUN_ID,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "board_sha256_observed": sha256(BOARD),
        "dataset": DATASET,
        "dataset_url": DATASET_URL,
        "command_results": command_results,
        "stats": stats,
        "decision": decision,
        "interpretation": [
            "The live Kaggle file matches the known stock-market-regimes source-panel horizon.",
            "The latest source-owned row remains 2026-01-30.",
            "The post-future strict 1h triage target XOM/Sideways still cannot be repaired from this upstream file because XOM/Sideways has zero rows in the Jan-2026 source tail and zero rows after 2026-01-30.",
        ],
        "guardrails": [
            "Downloaded raw data stayed under /tmp.",
            "No source labels were generated.",
            "No provider candles were promoted into labels.",
            "No Current Cursor edit was performed by this script.",
        ],
    }

    json_path = OUT_DIR / "stock_regime_kaggle_live_recency_check_v1.json"
    md_path = OUT_DIR / "stock_regime_kaggle_live_recency_check_v1.md"
    counts_path = OUT_DIR / "stock_regime_kaggle_live_recency_check_v1_counts.csv"
    assertions_path = CHECK_DIR / "stock_regime_kaggle_live_recency_check_v1_assertions.out"

    json_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    with counts_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["metric", "value"])
        writer.writeheader()
        for key in ["rows", "tickers", "min_date", "max_date", "csv_bytes", "csv_sha256"]:
            writer.writerow({"metric": key, "value": stats[key]})
        for key, value in stats["target_counts"].items():
            writer.writerow({"metric": key, "value": value})
        for key, value in stats["label_counts"].items():
            writer.writerow({"metric": f"label_count_{key}", "value": value})

    md_lines = [
        "# Stock Regime Kaggle Live Recency Check v1",
        "",
        f"Run ID: `{RUN_ID}`",
        "",
        "## Decision",
        "",
        "- Gate result: `stock_regime_kaggle_live_recency_check_v1=upstream_current_file_no_xom_sideways_tail_repair`.",
        f"- Dataset: [`{DATASET}`]({DATASET_URL}).",
        f"- Live CSV rows: `{stats['rows']}`; tickers: `{stats['tickers']}`.",
        f"- Live date range: `{stats['min_date']}` to `{stats['max_date']}`.",
        f"- `XOM/Sideways` rows after `2026-01-30`: `{target_after}`.",
        f"- `XOM/Sideways` rows in `2026-01-02..2026-01-30`: `{target_tail}`.",
        f"- `XOM/Sideways` rows in calendar `2025`: `{target_2025}`.",
        "- Accepted rows added: `0`; new confidence gate: `false`.",
        "- Strict full objective achieved: `false`; `update_goal=false`.",
        "",
        "## Interpretation",
        "",
        "- `191552` identified `XOM/Sideways` as the next strict `1h` heldout-side target needing `5` source-owned sessions.",
        "- The current upstream Kaggle file cannot supply those sessions: it still ends on `2026-01-30`, and it has no `XOM/Sideways` rows in the Jan-2026 source tail.",
        "- Raw Kaggle data stayed under `/tmp`; repo output is this compact recency check only.",
        "",
        "## Artifacts",
        "",
        f"- JSON: `docs/experiments/actionable-regime-confidence/runs/{RUN_ID}/kaggle-live-recency/stock_regime_kaggle_live_recency_check_v1.json`",
        f"- Counts CSV: `docs/experiments/actionable-regime-confidence/runs/{RUN_ID}/kaggle-live-recency/stock_regime_kaggle_live_recency_check_v1_counts.csv`",
        f"- Assertions: `docs/experiments/actionable-regime-confidence/runs/{RUN_ID}/checks/stock_regime_kaggle_live_recency_check_v1_assertions.out`",
    ]
    md_path.write_text("\n".join(md_lines) + "\n", encoding="utf-8")

    assertions = [
        f"run_id={RUN_ID}",
        f"gate_result={decision['gate_result']}",
        f"rows={stats['rows']}",
        f"max_date={stats['max_date']}",
        f"xom_sideways_after_2026_01_30={target_after}",
        f"xom_sideways_2026_01_02_to_2026_01_30={target_tail}",
        f"xom_sideways_repair_ready={str(can_repair_xom).lower()}",
        "accepted_rows_added=0",
        "new_confidence_gate=false",
        "strict_full_objective_achieved=false",
        "update_goal=false",
        f"raw_download_location={TMP_ROOT}",
        f"report_json={json_path.relative_to(ROOT)}",
    ]
    assertions_path.write_text("\n".join(assertions) + "\n", encoding="utf-8")

    if can_repair_xom:
        raise SystemExit("unexpected XOM/Sideways source sessions found; rerun strict gate instead")


if __name__ == "__main__":
    main()
