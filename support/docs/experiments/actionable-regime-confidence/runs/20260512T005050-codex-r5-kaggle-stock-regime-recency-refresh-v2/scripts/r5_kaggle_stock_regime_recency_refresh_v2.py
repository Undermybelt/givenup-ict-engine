#!/usr/bin/env python3
"""Live R5 source-panel recency refresh attempt using the source-owned Kaggle panel."""

from __future__ import annotations

import csv
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


RUN_ID = "20260512T005050-codex-r5-kaggle-stock-regime-recency-refresh-v2"
REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = Path(__file__).resolve().parents[1]
OUT = RUN_ROOT / "r5-kaggle-stock-regime-recency-refresh"
CHECKS = RUN_ROOT / "checks"
COMMAND_OUT = RUN_ROOT / "command-output"
DOWNLOAD_ROOT = Path("/tmp/ict-engine-kaggle-stock-regimes-live-refresh-20260512T005050")
INTAKE_ROOT = Path("/tmp/ict-engine-source-panel-recency-extension")
INTAKE_ROWS = INTAKE_ROOT / "stock_market_regimes_2026_extension.csv"
INTAKE_PROVENANCE = INTAKE_ROOT / "source_panel_recency_provenance.json"
LOCAL_REFERENCE = Path("/Users/thrill3r/Downloads/stock-market-regimes-20002026/stock_market_regimes_2000_2026.csv")
DATASET_ID = "mafaqbhatti/stock-market-regimes-20002026"
DATASET_URL = "https://www.kaggle.com/datasets/mafaqbhatti/stock-market-regimes-20002026"
LAST_ACCEPTED_SOURCE_DATE = "2026-01-30"
ROOT_LABELS = {"Bear", "Bull", "Crisis", "Sideways"}
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
TARGET_CELLS = [
    ("XOM", "Sideways", "heldout_time", 5),
    ("UNH", "Bear", "calibration", 7),
    ("^DJI", "Sideways", "calibration", 7),
    ("AMD", "Bear", "calibration", 10),
]
RECENCY_VERIFIER = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T165405-codex-source-panel-recency-extension-manifest-v1/"
    "source-panel-recency/source_panel_recency_extension_verifier_v1.py"
)
BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"


def repo_rel(path: Path) -> str:
    return str(path.relative_to(REPO)) if path.is_relative_to(REPO) else str(path)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run_cmd(name: str, cmd: list[str]) -> dict[str, Any]:
    proc = subprocess.run(cmd, cwd=REPO, text=True, capture_output=True, check=False)
    (COMMAND_OUT / f"{name}.stdout.txt").write_text(proc.stdout, encoding="utf-8")
    (COMMAND_OUT / f"{name}.stderr.txt").write_text(proc.stderr, encoding="utf-8")
    (COMMAND_OUT / f"{name}.exit").write_text(str(proc.returncode) + "\n", encoding="utf-8")
    return {
        "name": name,
        "cmd": cmd,
        "return_code": proc.returncode,
        "stdout_path": repo_rel(COMMAND_OUT / f"{name}.stdout.txt"),
        "stderr_path": repo_rel(COMMAND_OUT / f"{name}.stderr.txt"),
    }


def read_rows(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return reader.fieldnames or [], list(reader)


def write_rows(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows([{field: row.get(field, "") for field in fieldnames} for row in rows])


def analyze(rows: list[dict[str, str]]) -> dict[str, Any]:
    dates = [row.get("date", "") for row in rows if row.get("date")]
    tickers = {row.get("ticker", "") for row in rows if row.get("ticker")}
    label_counts: dict[str, int] = {}
    post_cutoff_rows = []
    post_cutoff_root_rows = []
    target_counts = {
        f"{symbol}/{label}": {
            "symbol": symbol,
            "main_regime_v2_label": label,
            "split_role": split_role,
            "min_new_source_sessions": min_rows,
            "post_cutoff_rows": 0,
        }
        for symbol, label, split_role, min_rows in TARGET_CELLS
    }
    for row in rows:
        label = row.get("regime_label", "")
        label_counts[label] = label_counts.get(label, 0) + 1
        if row.get("date", "") > LAST_ACCEPTED_SOURCE_DATE:
            post_cutoff_rows.append(row)
            if label in ROOT_LABELS:
                post_cutoff_root_rows.append(row)
            key = f"{row.get('ticker', '')}/{label}"
            if key in target_counts:
                target_counts[key]["post_cutoff_rows"] += 1
    return {
        "row_count": len(rows),
        "date_min": min(dates) if dates else "",
        "date_max": max(dates) if dates else "",
        "ticker_count": len(tickers),
        "label_counts": dict(sorted(label_counts.items())),
        "post_cutoff_rows": len(post_cutoff_rows),
        "post_cutoff_root_rows": len(post_cutoff_root_rows),
        "target_counts": list(target_counts.values()),
    }


def find_downloaded_csv() -> Path:
    preferred = DOWNLOAD_ROOT / "stock_market_regimes_2000_2026.csv"
    if preferred.exists():
        return preferred
    matches = sorted(DOWNLOAD_ROOT.glob("**/stock_market_regimes_2000_2026.csv"))
    if not matches:
        raise FileNotFoundError(f"stock_market_regimes_2000_2026.csv not found under {DOWNLOAD_ROOT}")
    return matches[0]


def run_recency_verifier() -> dict[str, Any]:
    result = run_cmd(
        "source_panel_recency_verifier",
        ["python3", str(RECENCY_VERIFIER), "--intake-root", str(INTAKE_ROOT)],
    )
    stdout = (COMMAND_OUT / "source_panel_recency_verifier.stdout.txt").read_text(encoding="utf-8")
    try:
        parsed = json.loads(stdout)
    except json.JSONDecodeError:
        parsed = {"status": "blocked", "reason": "stdout_not_json"}
    parsed["return_code"] = result["return_code"]
    return parsed


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)
    COMMAND_OUT.mkdir(parents=True, exist_ok=True)
    DOWNLOAD_ROOT.mkdir(parents=True, exist_ok=True)

    board_hash = sha256(BOARD)
    commands = [
        run_cmd("kaggle_files", ["kaggle", "datasets", "files", DATASET_ID, "-v"]),
        run_cmd(
            "kaggle_download",
            ["kaggle", "datasets", "download", DATASET_ID, "-p", str(DOWNLOAD_ROOT), "--force", "--unzip"],
        ),
    ]
    csv_path = find_downloaded_csv()
    fieldnames, rows = read_rows(csv_path)
    missing_columns = [field for field in REQUIRED_COLUMNS if field not in fieldnames]
    stats = analyze(rows)
    downloaded_hash = sha256(csv_path)
    local_hash = sha256(LOCAL_REFERENCE) if LOCAL_REFERENCE.exists() else ""
    extension_rows = [row for row in rows if row.get("date", "") > LAST_ACCEPTED_SOURCE_DATE and row.get("regime_label", "") in ROOT_LABELS]

    wrote_intake = False
    if extension_rows and not missing_columns:
        write_rows(INTAKE_ROWS, REQUIRED_COLUMNS, extension_rows)
        provenance = {
            "run_id": RUN_ID,
            "created_at_utc": datetime.now(timezone.utc).isoformat(),
            "source_owner": "mafaqbhatti",
            "source_report_or_dataset": f"kaggle:{DATASET_ID}",
            "source_url": DATASET_URL,
            "source_pull_root": str(DOWNLOAD_ROOT),
            "source_csv_sha256": downloaded_hash,
            "local_reference_csv_sha256": local_hash,
            "source_pull_date": "2026-05-12",
            "last_accepted_source_date": LAST_ACCEPTED_SOURCE_DATE,
            "extension_row_count": len(extension_rows),
            "raw_payload_committed_to_repo": False,
            "proxy_labels_generated": False,
            "notes": "Rows copied only if the live source-owned Kaggle panel exposes post-cutoff root labels.",
        }
        INTAKE_PROVENANCE.write_text(json.dumps(provenance, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        wrote_intake = True

    recency_verifier = run_recency_verifier()
    verifier_ready = recency_verifier.get("status") == "schema_ready_unscored"
    decision = (
        "r5_kaggle_stock_regime_recency_refresh_v2=recency_extension_rows_materialized"
        if verifier_ready
        else "r5_kaggle_stock_regime_recency_refresh_v2=latest_public_dataset_no_post_2026_01_30_rows"
    )

    result = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "board_hash_before_run": board_hash,
        "dataset_id": DATASET_ID,
        "dataset_url": DATASET_URL,
        "download_root": str(DOWNLOAD_ROOT),
        "downloaded_csv": str(csv_path),
        "downloaded_csv_sha256": downloaded_hash,
        "local_reference_csv": str(LOCAL_REFERENCE),
        "local_reference_csv_sha256": local_hash,
        "download_matches_local_reference": downloaded_hash == local_hash,
        "missing_columns": missing_columns,
        "csv_stats": stats,
        "last_accepted_source_date": LAST_ACCEPTED_SOURCE_DATE,
        "extension_rows_found": len(extension_rows),
        "intake_rows_written": wrote_intake,
        "intake_root": str(INTAKE_ROOT),
        "recency_verifier": recency_verifier,
        "commands": commands,
        "decision": decision,
        "accepted_rows_added": len(extension_rows) if verifier_ready else 0,
        "new_confidence_gate": False,
        "r5_recency_ready": verifier_ready,
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "external_requests_sent": True,
        "trade_usable": False,
    }

    json_path = OUT / "r5_kaggle_stock_regime_recency_refresh_v2.json"
    md_path = OUT / "r5_kaggle_stock_regime_recency_refresh_v2.md"
    targets_csv = OUT / "r5_kaggle_stock_regime_recency_refresh_targets_v2.csv"
    assertions_path = CHECKS / "r5_kaggle_stock_regime_recency_refresh_v2_assertions.out"
    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    with targets_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["symbol", "main_regime_v2_label", "split_role", "min_new_source_sessions", "post_cutoff_rows"],
        )
        writer.writeheader()
        writer.writerows(stats["target_counts"])

    lines = [
        "# R5 Kaggle Stock Regime Recency Refresh v2",
        "",
        f"- Decision: `{decision}`.",
        f"- Dataset: `{DATASET_ID}`.",
        f"- Download root: `{DOWNLOAD_ROOT}`.",
        f"- Rows: `{stats['row_count']}`; date range `{stats['date_min']}` to `{stats['date_max']}`.",
        f"- Download matches local reference: `{str(downloaded_hash == local_hash).lower()}`.",
        f"- Post-cutoff root rows after `{LAST_ACCEPTED_SOURCE_DATE}`: `{len(extension_rows)}`.",
        f"- R5 verifier status: `{recency_verifier.get('status')}`; return code `{recency_verifier.get('return_code')}`.",
        f"- Intake rows written: `{str(wrote_intake).lower()}`.",
        f"- Accepted rows added: `{result['accepted_rows_added']}`; new confidence gate: `false`.",
        "- Strict full objective achieved: `false`; `update_goal=false`.",
        "- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; external requests sent: `true`; trade usable: `false`.",
        "",
        "## Target Cells",
        "",
        "| Symbol | Label | Split Role | Required New Sessions | Post-Cutoff Rows |",
        "|---|---|---|---:|---:|",
    ]
    for row in stats["target_counts"]:
        lines.append(
            f"| `{row['symbol']}` | `{row['main_regime_v2_label']}` | `{row['split_role']}` | "
            f"`{row['min_new_source_sessions']}` | `{row['post_cutoff_rows']}` |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "The current public Kaggle source-owned panel was fetched live into `/tmp` and compared against the local reference. It still ends at the accepted source cutoff, so this run cannot populate the R5 post-cutoff recency intake without generating proxy labels.",
            "",
            "## Artifacts",
            "",
            f"- JSON: `{repo_rel(json_path)}`",
            f"- Report: `{repo_rel(md_path)}`",
            f"- Target CSV: `{repo_rel(targets_csv)}`",
            f"- Kaggle files stdout: `{repo_rel(COMMAND_OUT / 'kaggle_files.stdout.txt')}`",
            f"- Kaggle download stdout: `{repo_rel(COMMAND_OUT / 'kaggle_download.stdout.txt')}`",
            f"- R5 verifier stdout: `{repo_rel(COMMAND_OUT / 'source_panel_recency_verifier.stdout.txt')}`",
            f"- Assertions: `{repo_rel(assertions_path)}`",
        ]
    )
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    assertions = [
        f"PASS decision={decision}",
        f"PASS kaggle_files_return_code={commands[0]['return_code']}",
        f"PASS kaggle_download_return_code={commands[1]['return_code']}",
        f"PASS row_count={stats['row_count']}",
        f"PASS date_max={stats['date_max']}",
        f"PASS extension_rows_found={len(extension_rows)}",
        f"PASS recency_verifier_status={recency_verifier.get('status')}",
        f"PASS accepted_rows_added={result['accepted_rows_added']}",
        "PASS new_confidence_gate=false",
        "PASS strict_full_objective_achieved=false",
        "PASS update_goal=false",
        "PASS raw_data_committed=false",
        "PASS external_requests_sent=true",
    ]
    if commands[0]["return_code"] != 0 or commands[1]["return_code"] != 0:
        raise AssertionError("kaggle command failed")
    assertions_path.write_text("\n".join(assertions) + "\n", encoding="utf-8")
    print(json.dumps({"ok": True, "decision": decision, "date_max": stats["date_max"], "extension_rows_found": len(extension_rows), "r5_recency_ready": verifier_ready}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
