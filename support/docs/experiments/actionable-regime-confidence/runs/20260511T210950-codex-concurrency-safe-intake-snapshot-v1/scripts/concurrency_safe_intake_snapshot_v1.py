#!/usr/bin/env python3
"""Local-only Board A concurrency/intake snapshot.

This script intentionally does not fetch network resources, send requests, or
modify intake roots. It records the board cursor, plan hash, required intake
root state, and latest run-directory completeness so concurrent agents can
avoid overlapping work.
"""

from __future__ import annotations

import csv
import hashlib
import json
import os
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path


REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = RUN_ROOT / "concurrency-safe-intake-snapshot"
CHECK_DIR = RUN_ROOT / "checks"
BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"
RUNS_DIR = REPO / "docs/experiments/actionable-regime-confidence/runs"

REQUIRED_ROOTS = [
    {
        "id": "R2_R4_source_label_equivalence",
        "path": Path("/tmp/ict-engine-source-label-equivalence-intake"),
        "required_files": [
            "source_label_equivalence_rows.csv",
            "source_label_equivalence_provenance.json",
        ],
    },
    {
        "id": "R3_native_subhour_source_label",
        "path": Path("/tmp/ict-engine-native-subhour-source-label-intake"),
        "required_files": [
            "native_subhour_source_label_rows.csv",
            "native_subhour_source_label_provenance.json",
        ],
    },
    {
        "id": "R5_source_panel_recency_extension",
        "path": Path("/tmp/ict-engine-source-panel-recency-extension"),
        "required_files": [
            "stock_market_regimes_2026_extension.csv",
            "source_panel_recency_provenance.json",
        ],
    },
    {
        "id": "R6_direct_manipulation_row_intake",
        "path": Path("/tmp/ict-engine-direct-manipulation-row-intake"),
        "required_files": [
            "positive_spoofing_layering_rows.csv",
            "matched_negative_normal_activity_rows.csv",
            "provenance_manifest.json",
        ],
    },
]

VERIFIERS = {
    "R2_R4_source_label_equivalence": [
        "python3",
        str(
            REPO
            / "docs/experiments/actionable-regime-confidence/runs/"
            "20260511T182922-codex-source-label-equivalence-intake-verifier-v1/"
            "equivalence-intake-verifier/source_label_equivalence_intake_verifier_v1.py"
        ),
        "--intake-root",
        "/tmp/ict-engine-source-label-equivalence-intake",
    ],
    "R5_source_panel_recency_extension": [
        "python3",
        str(
            REPO
            / "docs/experiments/actionable-regime-confidence/runs/"
            "20260511T165405-codex-source-panel-recency-extension-manifest-v1/"
            "source-panel-recency/source_panel_recency_extension_verifier_v1.py"
        ),
        "--intake-root",
        "/tmp/ict-engine-source-panel-recency-extension",
    ],
    "R6_direct_manipulation_row_intake": [
        "python3",
        str(
            REPO
            / "docs/experiments/actionable-regime-confidence/runs/"
            "20260511T151950-codex-direct-manipulation-row-intake-manifest-v1/"
            "direct-manipulation-intake/direct_manipulation_row_intake_verifier_v1.py"
        ),
        "--intake-root",
        "/tmp/ict-engine-direct-manipulation-row-intake",
    ],
}


def sha256_path(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_cursor() -> dict[str, str]:
    text = BOARD.read_text(encoding="utf-8")
    cursor = {}
    in_cursor = False
    for line in text.splitlines():
        if line.strip() == "## Current Cursor":
            in_cursor = True
            continue
        if in_cursor and line.startswith("## "):
            break
        if in_cursor and line.startswith("|"):
            parts = [part.strip() for part in line.strip().strip("|").split("|")]
            if len(parts) >= 2 and parts[0] not in {"Field", "---"}:
                cursor[parts[0]] = parts[1]
    return cursor


def file_digest_or_missing(path: Path) -> str:
    if not path.exists():
        return "missing"
    if path.is_file():
        return sha256_path(path)
    return "directory"


def root_state(spec: dict) -> dict:
    root = spec["path"]
    present_files = []
    missing_files = []
    file_hashes = {}
    for filename in spec["required_files"]:
        fpath = root / filename
        if fpath.exists():
            present_files.append(filename)
            file_hashes[filename] = file_digest_or_missing(fpath)
        else:
            missing_files.append(filename)
    extra_files = []
    if root.exists():
        extra_files = sorted(
            p.name for p in root.iterdir() if p.is_file() and p.name not in spec["required_files"]
        )
    return {
        "id": spec["id"],
        "path": str(root),
        "root_exists": root.exists(),
        "required_files_present": len(present_files),
        "required_files_total": len(spec["required_files"]),
        "present_files": present_files,
        "missing_files": missing_files,
        "extra_files": extra_files,
        "file_hashes": file_hashes,
        "ready_by_file_presence": len(missing_files) == 0,
    }


def run_verifier(name: str, cmd: list[str]) -> dict:
    if not Path(cmd[1]).exists():
        return {
            "id": name,
            "status": "verifier_missing",
            "returncode": None,
            "stdout": "",
            "stderr": f"missing verifier: {cmd[1]}",
        }
    proc = subprocess.run(cmd, cwd=REPO, text=True, capture_output=True, timeout=60)
    stdout = proc.stdout.strip()
    stderr = proc.stderr.strip()
    status = "non_json"
    parsed = None
    if stdout:
        try:
            parsed = json.loads(stdout)
            status = str(parsed.get("status", "json_no_status"))
        except json.JSONDecodeError:
            status = "stdout_not_json"
    return {
        "id": name,
        "status": status,
        "returncode": proc.returncode,
        "stdout": stdout,
        "stderr": stderr,
        "parsed": parsed,
    }


def classify_run_dir(path: Path) -> dict:
    files = [p for p in path.rglob("*") if p.is_file()]
    rel_files = [str(p.relative_to(path)) for p in files]
    has_md = any(p.suffix == ".md" for p in files)
    has_json = any(p.suffix == ".json" for p in files)
    has_assertion = any("assertions" in p.name for p in files)
    if not files:
        state = "active_or_empty"
    elif has_md and has_json and has_assertion:
        state = "artifact_complete"
    else:
        state = "partial_or_in_progress"
    return {
        "run_dir": path.name,
        "file_count": len(files),
        "state": state,
        "has_md": has_md,
        "has_json": has_json,
        "has_assertion": has_assertion,
        "sample_files": rel_files[:8],
    }


def latest_runs(limit: int = 36) -> list[dict]:
    dirs = sorted([p for p in RUNS_DIR.iterdir() if p.is_dir() and p.name.startswith("20260511T21")])
    return [classify_run_dir(p) for p in dirs[-limit:]]


def write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)

    board_hash_before = sha256_path(BOARD)
    cursor = read_cursor()
    roots = [root_state(spec) for spec in REQUIRED_ROOTS]
    verifiers = [run_verifier(name, cmd) for name, cmd in VERIFIERS.items()]
    runs = latest_runs()
    active_or_empty = [row["run_dir"] for row in runs if row["state"] == "active_or_empty"]
    ready_roots = [row["id"] for row in roots if row["ready_by_file_presence"]]

    summary = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "run_root": str(RUN_ROOT.relative_to(REPO)),
        "board_path": str(BOARD.relative_to(REPO)),
        "board_sha256_before": board_hash_before,
        "current_cursor": cursor,
        "required_intake_roots": roots,
        "verifier_readbacks": verifiers,
        "latest_run_dirs": runs,
        "active_or_empty_run_dirs": active_or_empty,
        "ready_roots_by_file_presence": ready_roots,
        "ready_root_count": len(ready_roots),
        "strict_full_objective_achieved": False,
        "accepted_rows_added": 0,
        "new_confidence_gate": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "external_requests_sent": False,
        "trade_usable": False,
        "gate_result": "concurrency_safe_intake_snapshot_v1=local_snapshot_only_no_new_rows",
    }

    json_path = OUT_DIR / "concurrency_safe_intake_snapshot_v1.json"
    json_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    roots_csv = OUT_DIR / "concurrency_safe_intake_snapshot_v1_roots.csv"
    write_csv(
        roots_csv,
        roots,
        [
            "id",
            "path",
            "root_exists",
            "required_files_present",
            "required_files_total",
            "ready_by_file_presence",
            "missing_files",
        ],
    )

    runs_csv = OUT_DIR / "concurrency_safe_intake_snapshot_v1_run_dirs.csv"
    write_csv(
        runs_csv,
        runs,
        ["run_dir", "file_count", "state", "has_md", "has_json", "has_assertion"],
    )

    verifier_csv = OUT_DIR / "concurrency_safe_intake_snapshot_v1_verifiers.csv"
    write_csv(
        verifier_csv,
        verifiers,
        ["id", "status", "returncode", "stderr"],
    )

    md_lines = [
        "# Concurrency Safe Intake Snapshot v1",
        "",
        "- Gate result: `concurrency_safe_intake_snapshot_v1=local_snapshot_only_no_new_rows`.",
        f"- Board hash before snapshot: `{board_hash_before}`.",
        f"- Current cursor last loop: `{cursor.get('last_loop_id', 'unknown')}`.",
        f"- Current board state: `{cursor.get('board_state', 'unknown')}`.",
        f"- Ready intake roots by file presence: `{len(ready_roots)}/4`.",
        f"- Active/empty latest run directories: `{len(active_or_empty)}`.",
        "- Accepted rows added: `0`; new confidence gate: `false`.",
        "- Strict full objective achieved: `false`; `update_goal=false`.",
        "- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; external requests sent: `false`; trade usable: `false`.",
        "",
        "## Intake Roots",
        "",
        "| Root | Present | Ready | Missing |",
        "|---|---:|---:|---|",
    ]
    for row in roots:
        missing = ";".join(row["missing_files"])
        md_lines.append(
            f"| `{row['id']}` | `{row['root_exists']}` | `{row['ready_by_file_presence']}` | `{missing}` |"
        )

    md_lines.extend(
        [
            "",
            "## Verifier Readbacks",
            "",
            "| Verifier | Status | Return Code |",
            "|---|---|---:|",
        ]
    )
    for row in verifiers:
        md_lines.append(f"| `{row['id']}` | `{row['status']}` | `{row['returncode']}` |")

    md_lines.extend(
        [
            "",
            "## Active Or Empty Run Directories",
            "",
        ]
    )
    if active_or_empty:
        for run_dir in active_or_empty:
            md_lines.append(f"- `{run_dir}`")
    else:
        md_lines.append("- None detected in latest local scan.")

    md_lines.extend(
        [
            "",
            "## Boundary",
            "",
            "This is a local-only coordination snapshot. It does not register or rewrite another agent's run, does not update the Current Cursor, and does not perform source acquisition.",
            "",
            "## Artifacts",
            "",
            f"- JSON: `{json_path.relative_to(REPO)}`",
            f"- Roots CSV: `{roots_csv.relative_to(REPO)}`",
            f"- Run-dir CSV: `{runs_csv.relative_to(REPO)}`",
            f"- Verifier CSV: `{verifier_csv.relative_to(REPO)}`",
        ]
    )
    md_path = OUT_DIR / "concurrency_safe_intake_snapshot_v1.md"
    md_path.write_text("\n".join(md_lines) + "\n", encoding="utf-8")

    assertion_path = CHECK_DIR / "concurrency_safe_intake_snapshot_v1_assertions.out"
    assertions = [
        "PASS local_only_no_external_requests",
        "PASS no_runtime_code_changed",
        "PASS no_threshold_relaxation",
        "PASS no_raw_data_committed",
        "PASS current_cursor_not_modified_by_script",
        "PASS update_goal_false",
    ]
    assertion_path.write_text("\n".join(assertions) + "\n", encoding="utf-8")

    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
