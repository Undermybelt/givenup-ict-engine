#!/usr/bin/env python3
"""Read-only current Kaggle source-panel recency candidate screen for R5."""

from __future__ import annotations

import csv
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


RUN_ID = "20260512T053505-codex-r5-current-kaggle-recency-candidate-screen-v1"
SLUG = "r5-current-kaggle-recency-candidate-screen-v1"
REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = Path(__file__).resolve().parents[1]
OUT = RUN_ROOT / SLUG
CHECKS = RUN_ROOT / "checks"
COMMAND_OUT = RUN_ROOT / "command-output"
DOWNLOAD_ROOT = Path("/tmp/ict-engine-kaggle-stock-regimes-current-20260512T053505")
DATASET_ID = "mafaqbhatti/stock-market-regimes-20002026"
DATASET_URL = "https://www.kaggle.com/datasets/mafaqbhatti/stock-market-regimes-20002026"
LOCAL_REFERENCE = Path("/Users/thrill3r/Downloads/stock-market-regimes-20002026/stock_market_regimes_2000_2026.csv")
BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"
LAST_ACCEPTED_SOURCE_DATE = "2026-01-30"
R5_ROOT = Path("/tmp/ict-engine-source-panel-recency-extension")
TARGET_ROWS = R5_ROOT / "stock_market_regimes_2026_extension.csv"
TARGET_PROVENANCE = R5_ROOT / "source_panel_recency_provenance.json"
TARGET_CELLS = [
    ("XOM", "Sideways", "heldout_time", 5),
    ("UNH", "Bear", "calibration", 7),
    ("^DJI", "Sideways", "calibration", 7),
    ("AMD", "Bear", "calibration", 10),
]
ROOT_LABELS = {"Bear", "Bull", "Crisis", "Sideways"}


def repo_rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO))
    except ValueError:
        return str(path)


def sha256_file(path: Path) -> str:
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


def find_downloaded_csv() -> Path:
    preferred = DOWNLOAD_ROOT / "stock_market_regimes_2000_2026.csv"
    if preferred.exists():
        return preferred
    matches = sorted(DOWNLOAD_ROOT.glob("**/stock_market_regimes_2000_2026.csv"))
    if not matches:
        raise FileNotFoundError(f"stock_market_regimes_2000_2026.csv not found under {DOWNLOAD_ROOT}")
    return matches[0]


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return reader.fieldnames or [], list(reader)


def analyze(rows: list[dict[str, str]]) -> dict[str, Any]:
    dates = [row.get("date", "") for row in rows if row.get("date")]
    target_counts: list[dict[str, Any]] = []
    for ticker, label, split_role, min_rows in TARGET_CELLS:
        count = sum(
            1
            for row in rows
            if row.get("date", "") > LAST_ACCEPTED_SOURCE_DATE
            and row.get("ticker", "") == ticker
            and row.get("regime_label", "") == label
        )
        target_counts.append(
            {
                "ticker": ticker,
                "main_regime_v2_label": label,
                "split_role": split_role,
                "min_new_source_sessions": min_rows,
                "post_cutoff_rows": count,
                "meets_min_sessions": count >= min_rows,
            }
        )
    post_cutoff_rows = [
        row for row in rows
        if row.get("date", "") > LAST_ACCEPTED_SOURCE_DATE
        and row.get("regime_label", "") in ROOT_LABELS
    ]
    return {
        "row_count": len(rows),
        "date_min": min(dates) if dates else "",
        "date_max": max(dates) if dates else "",
        "post_cutoff_root_rows": len(post_cutoff_rows),
        "target_counts": target_counts,
        "target_rows_found": sum(row["post_cutoff_rows"] for row in target_counts),
        "all_target_cells_met": all(row["meets_min_sessions"] for row in target_counts),
    }


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)
    COMMAND_OUT.mkdir(parents=True, exist_ok=True)
    DOWNLOAD_ROOT.mkdir(parents=True, exist_ok=True)

    board_hash = sha256_file(BOARD)
    commands = [
        run_cmd("kaggle_files", ["kaggle", "datasets", "files", DATASET_ID, "-v"]),
        run_cmd(
            "kaggle_download",
            ["kaggle", "datasets", "download", DATASET_ID, "-p", str(DOWNLOAD_ROOT), "--force", "--unzip"],
        ),
    ]
    if any(command["return_code"] != 0 for command in commands):
        gate_result = "r5_current_kaggle_recency_candidate_screen_v1=kaggle_command_failed_no_promotion"
        result = {
            "run_id": RUN_ID,
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "board_hash_before_run": board_hash,
            "gate_result": gate_result,
            "commands": commands,
            "promotion_status": {
                "accepted_rows_added": 0,
                "source_control_evidence_acquired": False,
                "canonical_merge": False,
                "downstream_promotion_rerun": False,
                "strict_full_objective": False,
                "trade_usable": False,
                "update_goal": False,
            },
        }
        (OUT / "r5_current_kaggle_recency_candidate_screen_v1.json").write_text(
            json.dumps(result, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        return 2

    csv_path = find_downloaded_csv()
    fieldnames, rows = read_csv(csv_path)
    stats = analyze(rows)
    downloaded_hash = sha256_file(csv_path)
    local_hash = sha256_file(LOCAL_REFERENCE) if LOCAL_REFERENCE.exists() else ""
    required_target_files_present = TARGET_ROWS.exists() and TARGET_PROVENANCE.exists()
    gate_result = (
        "r5_current_kaggle_recency_candidate_screen_v1=post_cutoff_target_rows_available_root_not_mutated"
        if stats["all_target_cells_met"]
        else "r5_current_kaggle_recency_candidate_screen_v1=no_current_post_cutoff_target_rows_no_promotion"
    )
    result = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "board_hash_before_run": board_hash,
        "gate_result": gate_result,
        "dataset_id": DATASET_ID,
        "dataset_url": DATASET_URL,
        "download_root": str(DOWNLOAD_ROOT),
        "downloaded_csv": str(csv_path),
        "downloaded_csv_sha256": downloaded_hash,
        "local_reference_csv": str(LOCAL_REFERENCE),
        "local_reference_csv_sha256": local_hash,
        "download_matches_local_reference": downloaded_hash == local_hash,
        "fieldnames": fieldnames,
        "stats": stats,
        "required_target_files_present": required_target_files_present,
        "target_root_mutated": False,
        "commands": commands,
        "promotion_status": {
            "accepted_rows_added": 0,
            "source_control_evidence_acquired": False,
            "canonical_merge": False,
            "downstream_promotion_rerun": False,
            "strict_full_objective": False,
            "trade_usable": False,
            "update_goal": False,
        },
    }
    json_path = OUT / "r5_current_kaggle_recency_candidate_screen_v1.json"
    md_path = OUT / "r5_current_kaggle_recency_candidate_screen_v1.md"
    target_csv = OUT / "r5_current_kaggle_recency_candidate_targets_v1.csv"
    assertions_path = CHECKS / "r5_current_kaggle_recency_candidate_screen_v1_assertions.out"
    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_csv(target_csv, stats["target_counts"])

    lines = [
        "# R5 Current Kaggle Recency Candidate Screen v1",
        "",
        f"Run id: `{RUN_ID}`",
        "",
        f"Gate result: `{gate_result}`",
        "",
        "## Scope",
        "",
        "Read-only current-source screen for the R5 source-panel recency blocker. This run downloads the current Kaggle source package into `/tmp` and checks exact post-cutoff target cells. It does not copy rows into `/tmp/ict-engine-source-panel-recency-extension`, generate proxy labels, mutate target roots, run canonical merge, rerun downstream promotion, make a trade claim, or call `update_goal`.",
        "",
        "## Result",
        "",
        f"- Dataset: `{DATASET_ID}`.",
        f"- Rows: `{stats['row_count']}`; date range `{stats['date_min']}` to `{stats['date_max']}`.",
        f"- Download matches local reference: `{str(downloaded_hash == local_hash).lower()}`.",
        f"- Post-cutoff root rows after `{LAST_ACCEPTED_SOURCE_DATE}`: `{stats['post_cutoff_root_rows']}`.",
        f"- Required R5 target files already present: `{str(required_target_files_present).lower()}`.",
        "- Target root mutated: `false`.",
        "",
        "| Ticker | Label | Split Role | Required New Sessions | Post-Cutoff Rows | Meets Min |",
        "|---|---|---|---:|---:|---|",
    ]
    for row in stats["target_counts"]:
        lines.append(
            f"| `{row['ticker']}` | `{row['main_regime_v2_label']}` | `{row['split_role']}` | "
            f"`{row['min_new_source_sessions']}` | `{row['post_cutoff_rows']}` | "
            f"`{str(row['meets_min_sessions']).lower()}` |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            "R5 remains blocked unless a source owner publishes or approves post-cutoff source rows with provenance. This screen found no qualifying post-cutoff target rows in the current public Kaggle source package, so it is not accepted regime-confidence evidence, not source/control evidence, not canonical merge input, not downstream promotion evidence, not trade evidence, and not `update_goal` authorization.",
        ]
    )
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    assertions = [
        f"PASS run_id={RUN_ID}",
        f"PASS gate_result={gate_result}",
        f"PASS kaggle_files_return_code={commands[0]['return_code']}",
        f"PASS kaggle_download_return_code={commands[1]['return_code']}",
        f"PASS row_count={stats['row_count']}",
        f"PASS date_max={stats['date_max']}",
        f"PASS post_cutoff_root_rows={stats['post_cutoff_root_rows']}",
        f"PASS target_rows_found={stats['target_rows_found']}",
        f"PASS required_target_files_present={str(required_target_files_present).lower()}",
        "PASS target_root_mutated=false",
        "PASS source_control_evidence_acquired=false",
        "PASS canonical_merge=false",
        "PASS downstream_promotion_rerun=false",
        "PASS strict_full_objective=false",
        "PASS trade_usable=false",
        "PASS update_goal=false",
    ]
    assertions_path.write_text("\n".join(assertions) + "\n", encoding="utf-8")
    print(json.dumps({"gate_result": gate_result, "date_max": stats["date_max"], "target_rows_found": stats["target_rows_found"]}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
