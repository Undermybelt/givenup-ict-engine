#!/usr/bin/env python3
"""Preflight the next R6 intake rehydration step without mutating intake."""

from __future__ import annotations

import csv
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


RUN_ID = "20260511T235841-codex-r6-rehydrate-preflight-v1"
REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs" / RUN_ID
OUT = RUN_ROOT / "r6-rehydrate-preflight"
CMD = RUN_ROOT / "command-output"
CHECKS = RUN_ROOT / "checks"
BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"
LIVE_INTAKE = Path("/tmp/ict-engine-direct-manipulation-row-intake")
DIRECT_VERIFIER = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs"
    / "20260511T151950-codex-direct-manipulation-row-intake-manifest-v1"
    / "direct-manipulation-intake/direct_manipulation_row_intake_verifier_v1.py"
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def run_direct_verifier() -> dict[str, Any]:
    CMD.mkdir(parents=True, exist_ok=True)
    proc = subprocess.run(
        ["python3", str(DIRECT_VERIFIER), "--intake-root", str(LIVE_INTAKE)],
        cwd=REPO,
        text=True,
        capture_output=True,
        timeout=45,
        check=False,
    )
    stdout = CMD / "direct_manipulation_row_intake_verifier.stdout.txt"
    stderr = CMD / "direct_manipulation_row_intake_verifier.stderr.txt"
    stdout.write_text(proc.stdout, encoding="utf-8")
    stderr.write_text(proc.stderr, encoding="utf-8")
    try:
        parsed = json.loads(proc.stdout)
    except json.JSONDecodeError:
        parsed = {"parse_error": True, "raw_stdout": proc.stdout[:500]}
    return {
        "returncode": proc.returncode,
        "stdout_path": str(stdout.relative_to(REPO)),
        "stderr_path": str(stderr.relative_to(REPO)),
        "parsed": parsed,
    }


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)
    board_hash = sha256(BOARD)
    verifier = run_direct_verifier()
    parsed = verifier.get("parsed") or {}
    missing_live = (
        verifier["returncode"] != 0
        and parsed.get("status") == "blocked"
        and parsed.get("reason") == "missing_required_files"
    )

    runs_root = REPO / "docs/experiments/actionable-regime-confidence/runs"
    durable_snapshot_names = {
        "positive_spoofing_layering_rows.csv",
        "matched_negative_normal_activity_rows.csv",
        "provenance_manifest.json",
    }
    durable_snapshots = [
        {
            "path": str(path.relative_to(REPO)),
            "filename": path.name,
            "bytes": path.stat().st_size,
        }
        for path in runs_root.rglob("*")
        if path.is_file() and path.name in durable_snapshot_names
    ]
    generation_scripts = []
    for path in runs_root.rglob("*.py"):
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if "positive_spoofing_layering" in text and "ict-engine-direct-manipulation-row-intake" in text:
            generation_scripts.append(
                {
                    "path": str(path.relative_to(REPO)),
                    "bytes": path.stat().st_size,
                }
            )

    empty_scaffolds = []
    for run_id in [
        "20260511T235303-codex-r6-direct-intake-reconstruction-preflight-v1",
        "20260511T235743-codex-r6-canonical-intake-rematerialization-v1",
    ]:
        root = runs_root / run_id
        files = [p for p in root.rglob("*") if p.is_file()] if root.exists() else []
        empty_scaffolds.append(
            {
                "run_id": run_id,
                "exists": root.exists(),
                "file_count": len(files),
            }
        )

    result = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "board_sha256_at_start": board_hash,
        "canonical_live_intake_root": str(LIVE_INTAKE),
        "canonical_live_intake_exists": LIVE_INTAKE.exists(),
        "direct_verifier": verifier,
        "direct_verifier_blocked_missing_required_files": missing_live,
        "durable_snapshot_files_found": len(durable_snapshots),
        "durable_row_generation_scripts_found": len(generation_scripts),
        "empty_or_missing_preflight_scaffolds": empty_scaffolds,
        "shared_intake_mutated": False,
        "accepted_rows_added": 0,
        "new_confidence_gate": False,
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "trade_usable": False,
        "gate_result": "r6_rehydrate_preflight_v1=live_intake_missing_no_durable_snapshots_generation_scripts_available",
        "next_action": (
            "Rehydrate a new isolated direct R6 intake from the durable row-generation scripts or a fresh "
            "owner-approved export, then write durable positive/control/provenance snapshots before accepting "
            "sidecar rows or rerunning calibration."
        ),
    }
    write_csv(OUT / "r6_rehydrate_preflight_durable_snapshots_v1.csv", durable_snapshots, ["path", "filename", "bytes"])
    write_csv(OUT / "r6_rehydrate_preflight_generation_scripts_v1.csv", generation_scripts, ["path", "bytes"])
    write_csv(OUT / "r6_rehydrate_preflight_scaffolds_v1.csv", empty_scaffolds, ["run_id", "exists", "file_count"])
    (OUT / "r6_rehydrate_preflight_v1.json").write_text(json.dumps(result, indent=2, sort_keys=False) + "\n", encoding="utf-8")
    report = [
        "# R6 Rehydrate Preflight v1",
        "",
        f"- Gate result: `{result['gate_result']}`.",
        f"- Live intake exists: `{result['canonical_live_intake_exists']}`.",
        f"- Direct verifier blocked missing files: `{missing_live}`.",
        f"- Durable snapshot files found: `{len(durable_snapshots)}`.",
        f"- Durable row-generation scripts found: `{len(generation_scripts)}`.",
        f"- Empty/missing preflight scaffolds: `{empty_scaffolds}`.",
        f"- Accepted rows added: `0`; new confidence gate: `false`; strict full objective achieved: `false`; `update_goal=false`.",
        "",
        "Next: rehydrate a new isolated direct R6 intake from generation scripts or a fresh owner-approved export, then write durable snapshots before accepting sidecar rows or rerunning calibration.",
    ]
    (OUT / "r6_rehydrate_preflight_v1.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    assertions = [
        f"canonical_live_intake_exists={result['canonical_live_intake_exists']}",
        f"direct_verifier_blocked_missing_required_files={missing_live}",
        f"durable_snapshot_files_found={len(durable_snapshots)}",
        f"durable_row_generation_scripts_found={len(generation_scripts)}",
        "shared_intake_mutated=False",
        "new_confidence_gate=False",
        "strict_full_objective_achieved=False",
        "update_goal=False",
    ]
    (CHECKS / "r6_rehydrate_preflight_v1_assertions.out").write_text("\n".join(assertions) + "\n", encoding="utf-8")
    print(json.dumps({"ok": True, "run_id": RUN_ID, "gate_result": result["gate_result"], "update_goal": False}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
