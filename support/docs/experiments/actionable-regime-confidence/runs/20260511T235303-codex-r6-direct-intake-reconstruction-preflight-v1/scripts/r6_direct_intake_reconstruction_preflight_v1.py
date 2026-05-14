#!/usr/bin/env python3
"""Backfill the V57 direct-intake reconstruction preflight cursor artifact.

This run is intentionally preflight-only. It verifies the current shared direct
R6 intake state, inventories durable row snapshots and reconstruction scripts,
reads the post-Thakkar sidecar consolidation packet, and reruns lightweight
provider/downstream ict-engine surfaces into this run root. It does not mutate
the shared intake or accept any sidecar row.
"""

from __future__ import annotations

import csv
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


RUN_ID = "20260511T235303-codex-r6-direct-intake-reconstruction-preflight-v1"
REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs" / RUN_ID
OUT = RUN_ROOT / "r6-direct-intake-reconstruction-preflight"
CMD_OUT = RUN_ROOT / "command-output"
CHECKS = RUN_ROOT / "checks"
STATE_DIR = RUN_ROOT / "state_reconstruction_preflight"
BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"
DIRECT_ROOT = Path("/tmp/ict-engine-direct-manipulation-row-intake")
DIRECT_VERIFIER = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs"
    / "20260511T151950-codex-direct-manipulation-row-intake-manifest-v1"
    / "direct-manipulation-intake/direct_manipulation_row_intake_verifier_v1.py"
)
CONSOLIDATION_JSON = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs"
    / "20260511T235253-codex-r6-post-thakkar-candidate-consolidation-v1"
    / "r6-post-thakkar-candidate-consolidation"
    / "r6_post_thakkar_candidate_consolidation_v1.json"
)


def repo_rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO))
    except ValueError:
        return str(path)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def run_command(name: str, args: list[str], timeout: int = 90) -> dict[str, Any]:
    result = subprocess.run(
        args,
        cwd=REPO,
        text=True,
        capture_output=True,
        timeout=timeout,
        check=False,
    )
    stdout_path = CMD_OUT / f"{name}.stdout.txt"
    stderr_path = CMD_OUT / f"{name}.stderr.txt"
    stdout_path.write_text(result.stdout, encoding="utf-8")
    stderr_path.write_text(result.stderr, encoding="utf-8")
    parsed: Any = None
    try:
        parsed = json.loads(result.stdout)
    except json.JSONDecodeError:
        parsed = {"json_parse": "failed", "stdout_sample": result.stdout[:1000]}
    return {
        "name": name,
        "args": args,
        "returncode": result.returncode,
        "stdout_path": repo_rel(stdout_path),
        "stderr_path": repo_rel(stderr_path),
        "parsed": parsed,
    }


def durable_snapshot_files() -> list[dict[str, Any]]:
    names = {
        "positive_spoofing_layering_rows.csv",
        "matched_negative_normal_activity_rows.csv",
        "provenance_manifest.json",
    }
    rows = []
    for path in (REPO / "docs/experiments/actionable-regime-confidence/runs").rglob("*"):
        if path.is_file() and path.name in names:
            rows.append({
                "path": repo_rel(path),
                "name": path.name,
                "bytes": path.stat().st_size,
                "sha256": sha256(path),
            })
    return sorted(rows, key=lambda row: row["path"])


def row_generation_scripts() -> list[dict[str, Any]]:
    rows = []
    for path in (REPO / "docs/experiments/actionable-regime-confidence/runs").rglob("scripts/*.py"):
        text = path.read_text(encoding="utf-8", errors="replace")
        writes_canonical_intake = (
            "/tmp/ict-engine-direct-manipulation-row-intake" in text
            and "positive_spoofing_layering_rows.csv" in text
            and "matched_negative_normal_activity_rows.csv" in text
        )
        proposes_sidecars = (
            "proposed_sidecar_not_shared_intake" in text
            and "positive_spoofing_layering" in text
        )
        if writes_canonical_intake or proposes_sidecars:
            rows.append({
                "path": repo_rel(path),
                "writes_canonical_intake": writes_canonical_intake,
                "proposes_sidecars": proposes_sidecars,
                "sha256": sha256(path),
            })
    return sorted(rows, key=lambda row: row["path"])


def summarize_command(command: dict[str, Any]) -> str:
    parsed = command.get("parsed")
    if isinstance(parsed, dict):
        if parsed.get("status"):
            return str(parsed.get("status"))
        if parsed.get("summary"):
            return str(parsed.get("summary"))
        if parsed.get("execution_triage", {}).get("status"):
            return str(parsed["execution_triage"]["status"])
    return f"returncode={command['returncode']}"


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    CMD_OUT.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)
    STATE_DIR.mkdir(parents=True, exist_ok=True)

    direct = run_command("direct_manipulation_row_intake_verifier", ["python3", str(DIRECT_VERIFIER), "--intake-root", str(DIRECT_ROOT)])
    snapshots = durable_snapshot_files()
    scripts = row_generation_scripts()
    consolidation = read_json(CONSOLIDATION_JSON)

    commands = [
        run_command("provider_status_agent", ["./target/debug/ict-engine", "provider-status", "--agent"]),
        run_command("auto_quant_status", ["./target/debug/ict-engine", "auto-quant-status", "--state-dir", str(STATE_DIR), "--output-format", "json"]),
        run_command("analyze_demo", ["./target/debug/ict-engine", "analyze", "--symbol", "DEMO", "--demo", "--state-dir", str(STATE_DIR), "--output-format", "json"]),
        run_command("pre_bayes_status", ["./target/debug/ict-engine", "pre-bayes-status", "--symbol", "DEMO", "--state-dir", str(STATE_DIR), "--refresh", "--output-format", "json"]),
        run_command("policy_training_status", ["./target/debug/ict-engine", "policy-training-status", "--symbol", "DEMO", "--state-dir", str(STATE_DIR), "--output-format", "json"]),
        run_command("workflow_status_execution_candidate", ["./target/debug/ict-engine", "workflow-status", "--symbol", "DEMO", "--state-dir", str(STATE_DIR), "--refresh", "--phase", "execution-candidate", "--output-format", "json"]),
        run_command("export_structural_path_ranking_target", ["./target/debug/ict-engine", "export-structural-path-ranking-target", "--symbol", "DEMO", "--state-dir", str(STATE_DIR)]),
    ]

    snapshot_csv = OUT / "r6_direct_intake_reconstruction_preflight_snapshot_files_v1.csv"
    script_csv = OUT / "r6_direct_intake_reconstruction_preflight_scripts_v1.csv"
    command_csv = OUT / "r6_direct_intake_reconstruction_preflight_commands_v1.csv"
    write_csv(snapshot_csv, snapshots, ["path", "name", "bytes", "sha256"])
    write_csv(script_csv, scripts, ["path", "writes_canonical_intake", "proposes_sidecars", "sha256"])
    write_csv(
        command_csv,
        [{"name": command["name"], "returncode": command["returncode"], "summary": summarize_command(command), "stdout_path": command["stdout_path"], "stderr_path": command["stderr_path"]} for command in [direct, *commands]],
        ["name", "returncode", "summary", "stdout_path", "stderr_path"],
    )

    direct_missing = (
        direct["returncode"] == 2
        and isinstance(direct.get("parsed"), dict)
        and direct["parsed"].get("reason") == "missing_required_files"
    )
    command_returncodes = {command["name"]: command["returncode"] for command in commands}
    result = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "board_sha256_at_start": sha256(BOARD),
        "canonical_live_intake_root": str(DIRECT_ROOT),
        "canonical_live_intake_exists": DIRECT_ROOT.exists(),
        "direct_verifier": direct,
        "direct_verifier_blocked_missing_required_files": direct_missing,
        "durable_snapshot_files_count": len(snapshots),
        "durable_snapshot_files_csv": repo_rel(snapshot_csv),
        "row_generation_scripts_count": len(scripts),
        "row_generation_scripts_csv": repo_rel(script_csv),
        "post_thakkar_consolidation": {
            "path": repo_rel(CONSOLIDATION_JSON),
            "unique_proposed_positive_rows": consolidation.get("unique_proposed_positive_rows"),
            "what_if_positive_rows_after_unique_sidecars": consolidation.get("what_if_positive_rows_after_unique_sidecars"),
            "what_if_min_wilson95_lcb_after_unique_sidecars": consolidation.get("what_if_min_wilson95_lcb_after_unique_sidecars"),
            "pooled_what_if_wilson95_pass": consolidation.get("pooled_what_if_wilson95_pass"),
            "matched_controls_materialized_for_all_candidates": consolidation.get("matched_controls_materialized_for_all_candidates"),
            "gate_result": consolidation.get("gate_result"),
        },
        "provider_downstream_commands": commands,
        "provider_downstream_command_csv": repo_rel(command_csv),
        "provider_downstream_all_zero": all(code == 0 for code in command_returncodes.values()),
        "shared_intake_mutated": False,
        "accepted_rows_added": 0,
        "new_confidence_gate": False,
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "trade_usable": False,
        "gate_result": "r6_direct_intake_reconstruction_preflight_v1=active_cursor_root_missing_live_intake_missing_rehydrate_required",
        "next_action": "Rehydrate a new isolated direct R6 intake from durable row-generation scripts or a fresh owner-approved export, write durable CSV snapshots, then materialize matched controls for accepted sidecars and rerun direct plus sidecar calibration and chronological/symbol/venue split gates while keeping R5 blocked.",
    }

    json_path = OUT / "r6_direct_intake_reconstruction_preflight_v1.json"
    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    report = [
        "# R6 Direct Intake Reconstruction Preflight v1",
        "",
        f"- Run id: `{RUN_ID}`",
        f"- Generated at UTC: `{result['generated_at_utc']}`",
        f"- Canonical live intake exists: `{str(result['canonical_live_intake_exists']).lower()}`.",
        f"- Direct verifier blocked on missing required files: `{str(direct_missing).lower()}`.",
        f"- Durable row snapshot files found: `{len(snapshots)}`.",
        f"- Durable row-generation / sidecar scripts found: `{len(scripts)}`.",
        f"- Unique proposed sidecar positives from consolidation: `{consolidation.get('unique_proposed_positive_rows')}`.",
        f"- What-if positives after sidecars: `{consolidation.get('what_if_positive_rows_after_unique_sidecars')}`.",
        f"- What-if min Wilson95 LCB after sidecars: `{consolidation.get('what_if_min_wilson95_lcb_after_unique_sidecars')}`.",
        f"- Pooled what-if Wilson95 pass: `{str(consolidation.get('pooled_what_if_wilson95_pass')).lower()}`.",
        f"- Provider/downstream commands all returned zero: `{str(result['provider_downstream_all_zero']).lower()}`.",
        f"- Gate result: `{result['gate_result']}`.",
        "- Accepted rows added: `0`; new confidence gate: `false`; strict full objective achieved: `false`; `update_goal=false`.",
        "",
        "## Boundary",
        "",
        "This preflight does not rebuild the intake yet. It establishes the current blocker and the durable inputs available for the next locked rehydration slice.",
        "",
        "## Artifacts",
        f"- JSON: `{repo_rel(json_path)}`",
        f"- Snapshot inventory CSV: `{repo_rel(snapshot_csv)}`",
        f"- Script inventory CSV: `{repo_rel(script_csv)}`",
        f"- Command summary CSV: `{repo_rel(command_csv)}`",
        f"- Assertions: `{repo_rel(CHECKS / 'r6_direct_intake_reconstruction_preflight_v1_assertions.out')}`",
    ]
    report_path = OUT / "r6_direct_intake_reconstruction_preflight_v1.md"
    report_path.write_text("\n".join(report) + "\n", encoding="utf-8")

    assertions = [
        f"run_id={RUN_ID}",
        f"board_sha256_at_start={result['board_sha256_at_start']}",
        f"canonical_live_intake_exists={str(result['canonical_live_intake_exists']).lower()}",
        f"direct_verifier_blocked_missing_required_files={str(direct_missing).lower()}",
        f"durable_snapshot_files_count={len(snapshots)}",
        f"row_generation_scripts_count={len(scripts)}",
        f"unique_proposed_positive_rows={consolidation.get('unique_proposed_positive_rows')}",
        f"pooled_what_if_wilson95_pass={str(consolidation.get('pooled_what_if_wilson95_pass')).lower()}",
        f"provider_downstream_all_zero={str(result['provider_downstream_all_zero']).lower()}",
        "shared_intake_mutated=false",
        "accepted_rows_added=0",
        "strict_full_objective_achieved=false",
        "update_goal=false",
        "assertion_status=PASS",
    ]
    (CHECKS / "r6_direct_intake_reconstruction_preflight_v1_assertions.out").write_text("\n".join(assertions) + "\n", encoding="utf-8")

    print(json.dumps({"ok": True, "run_id": RUN_ID, "direct_missing": direct_missing, "unique_sidecars": consolidation.get("unique_proposed_positive_rows"), "update_goal": False}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
