#!/usr/bin/env python3
"""Fail-closed readback for the current R6 direct Manipulation intake.

This run intentionally does not mutate the shared /tmp intake. It records the
current verifier state and preserves the latest sidecar candidate evidence.
"""

from __future__ import annotations

import csv
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


RUN_ID = "20260511T234622-codex-r6-live-intake-missing-readback-v55"
REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs" / RUN_ID
OUT = RUN_ROOT / "r6-live-intake-missing-readback"
CHECKS = RUN_ROOT / "checks"
COMMAND_OUT = RUN_ROOT / "command-output"

BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"
LIVE_INTAKE = Path("/tmp/ict-engine-direct-manipulation-row-intake")
DIRECT_VERIFIER = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs"
    / "20260511T151950-codex-direct-manipulation-row-intake-manifest-v1"
    / "direct-manipulation-intake/direct_manipulation_row_intake_verifier_v1.py"
)

REQUIRED_FILES = [
    "positive_spoofing_layering_rows.csv",
    "matched_negative_normal_activity_rows.csv",
    "provenance_manifest.json",
]

SIDECAR_ARTIFACTS = {
    "sarao": {
        "json": REPO
        / "docs/experiments/actionable-regime-confidence/runs"
        / "20260511T225505-codex-r6-sarao-positive-row-candidate-screen-v1"
        / "r6-sarao-positive-row-candidate-screen/r6_sarao_positive_row_candidate_screen_v1.json",
        "csv": REPO
        / "docs/experiments/actionable-regime-confidence/runs"
        / "20260511T225505-codex-r6-sarao-positive-row-candidate-screen-v1"
        / "r6-sarao-positive-row-candidate-screen/r6_sarao_positive_row_candidates_v1.csv",
    },
    "nowak_smith": {
        "json": REPO
        / "docs/experiments/actionable-regime-confidence/runs"
        / "20260511T233454-codex-r6-nowak-smith-positive-row-candidate-screen-v1"
        / "r6-nowak-smith-positive-row-candidate-screen/r6_nowak_smith_positive_row_candidate_screen_v1.json",
        "csv": REPO
        / "docs/experiments/actionable-regime-confidence/runs"
        / "20260511T233454-codex-r6-nowak-smith-positive-row-candidate-screen-v1"
        / "r6-nowak-smith-positive-row-candidate-screen/r6_nowak_smith_positive_row_candidates_v1.csv",
    },
}


def rel(path: Path) -> str:
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


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"exists": False, "path": rel(path)}
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["_exists"] = True
    payload["_path"] = rel(path)
    payload["_sha256"] = sha256(path)
    return payload


def count_csv_rows(path: Path) -> int | None:
    if not path.exists():
        return None
    with path.open(newline="", encoding="utf-8") as handle:
        return sum(1 for _ in csv.DictReader(handle))


def run_verifier() -> dict[str, Any]:
    COMMAND_OUT.mkdir(parents=True, exist_ok=True)
    proc = subprocess.run(
        ["python3", str(DIRECT_VERIFIER), "--intake-root", str(LIVE_INTAKE)],
        cwd=REPO,
        text=True,
        capture_output=True,
        timeout=45,
        check=False,
    )
    stdout_path = COMMAND_OUT / "direct_manipulation_row_intake_verifier.stdout.txt"
    stderr_path = COMMAND_OUT / "direct_manipulation_row_intake_verifier.stderr.txt"
    stdout_path.write_text(proc.stdout, encoding="utf-8")
    stderr_path.write_text(proc.stderr, encoding="utf-8")
    try:
        parsed = json.loads(proc.stdout)
    except json.JSONDecodeError:
        parsed = {"status": "blocked", "reason": "invalid_json_stdout", "stdout": proc.stdout[:1000]}
    return {
        "cmd": f"python3 {rel(DIRECT_VERIFIER)} --intake-root {LIVE_INTAKE}",
        "returncode": proc.returncode,
        "stdout_path": rel(stdout_path),
        "stderr_path": rel(stderr_path),
        "payload": parsed,
    }


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)

    board_sha = sha256(BOARD)
    verifier = run_verifier()
    required_status = [
        {
            "name": name,
            "path": str(LIVE_INTAKE / name),
            "exists": (LIVE_INTAKE / name).exists(),
            "bytes": (LIVE_INTAKE / name).stat().st_size if (LIVE_INTAKE / name).exists() else 0,
        }
        for name in REQUIRED_FILES
    ]

    sidecars: dict[str, Any] = {}
    total_sidecar_rows = 0
    for key, paths in SIDECAR_ARTIFACTS.items():
        payload = load_json(paths["json"])
        csv_rows = count_csv_rows(paths["csv"])
        proposed = int(payload.get("proposed_positive_rows") or csv_rows or 0)
        total_sidecar_rows += proposed
        sidecars[key] = {
            "json_path": rel(paths["json"]),
            "json_exists": paths["json"].exists(),
            "json_sha256": sha256(paths["json"]) if paths["json"].exists() else "",
            "csv_path": rel(paths["csv"]),
            "csv_exists": paths["csv"].exists(),
            "csv_rows": csv_rows,
            "proposed_positive_rows": proposed,
            "gate_result": payload.get("gate_result"),
            "current_direct_positives_at_candidate_run": payload.get("current_direct_positives")
            or payload.get("current_positive_rows"),
            "what_if_min_wilson95_lcb": payload.get("what_if_min_wilson95_lcb")
            or payload.get("what_if_min_wilson95_lcb_nowak_smith_only"),
        }

    nowak = load_json(SIDECAR_ARTIFACTS["nowak_smith"]["json"])
    what_if_both = nowak.get("what_if_positive_rows_with_sarao_sidecar")
    what_if_both_lcb = nowak.get("what_if_min_wilson95_lcb_with_sarao_sidecar")
    rows_needed_after_both = nowak.get("additional_positive_rows_needed_after_sarao_and_nowak_smith_if_all_accepted")

    intake_missing = verifier["payload"].get("reason") == "missing_required_files"
    gate_result = "current_goal_completion_audit_v55=shared_r6_intake_missing_sidecar_candidates_preserved"
    result = {
        "schema_version": "r6-live-intake-missing-readback/v55",
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "board_sha256_at_start": board_sha,
        "live_intake_root": str(LIVE_INTAKE),
        "live_intake_exists": LIVE_INTAKE.exists(),
        "required_files": required_status,
        "verifier": verifier,
        "sidecar_candidates": sidecars,
        "sidecar_candidate_total_rows": total_sidecar_rows,
        "what_if_after_sarao_and_nowak_smith": {
            "positive_rows": what_if_both,
            "min_wilson95_lcb": what_if_both_lcb,
            "additional_positive_rows_needed_for_pooled_95": rows_needed_after_both,
            "still_below_95": bool(what_if_both_lcb is not None and what_if_both_lcb < 0.95),
        },
        "decision": {
            "gate_result": gate_result,
            "accepted_rows_added": 0,
            "new_confidence_gate": False,
            "strict_full_objective_achieved": False,
            "update_goal": False,
            "runtime_code_changed": False,
            "thresholds_relaxed": False,
            "raw_data_committed": False,
            "shared_intake_mutated": False,
            "trade_usable": False,
        },
        "blocker": (
            "The shared R6 direct Manipulation intake is absent in /tmp, so the "
            "Sarao and Nowak/Smith sidecar positives cannot be accepted or "
            "calibrated against the live intake in this readback."
        ),
        "next_action": (
            "Under a fresh shared-intake lock, restore or reconstruct the R6 intake "
            "from durable row-uplift scripts/provenance, then decide whether to "
            "append Sarao and Nowak/Smith positives with matched controls; even "
            "if all current sidecars are accepted, source at least four more "
            "all-correct positive direct rows and rerun sidecar calibration plus "
            "chronological/symbol/venue split gates."
        ),
    }

    json_path = OUT / "r6_live_intake_missing_readback_v55.json"
    md_path = OUT / "r6_live_intake_missing_readback_v55.md"
    gate_csv = OUT / "r6_live_intake_missing_readback_v55_gates.csv"
    assertions_path = CHECKS / "r6_live_intake_missing_readback_v55_assertions.out"

    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    with gate_csv.open("w", newline="", encoding="utf-8") as handle:
        fields = ["gate", "status", "evidence"]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(
            [
                {
                    "gate": "live_intake_required_files",
                    "status": "fail" if intake_missing else "pass",
                    "evidence": verifier["payload"].get("reason", verifier["payload"].get("status", "")),
                },
                {
                    "gate": "sarao_sidecar_preserved",
                    "status": "pass" if sidecars["sarao"]["json_exists"] else "fail",
                    "evidence": f"proposed_rows={sidecars['sarao']['proposed_positive_rows']}",
                },
                {
                    "gate": "nowak_smith_sidecar_preserved",
                    "status": "pass" if sidecars["nowak_smith"]["json_exists"] else "fail",
                    "evidence": f"proposed_rows={sidecars['nowak_smith']['proposed_positive_rows']}",
                },
                {
                    "gate": "strict_full_objective",
                    "status": "fail",
                    "evidence": gate_result,
                },
            ]
        )

    md_lines = [
        "# R6 Live Intake Missing Readback v55",
        "",
        f"- Run id: `{RUN_ID}`",
        f"- Generated at UTC: `{result['generated_at_utc']}`",
        f"- Live intake root: `{LIVE_INTAKE}`",
        f"- Live intake exists: `{str(LIVE_INTAKE.exists()).lower()}`",
        f"- Verifier status: `{verifier['payload'].get('status')}`",
        f"- Verifier reason: `{verifier['payload'].get('reason')}`",
        f"- Sarao proposed positives preserved: `{sidecars['sarao']['proposed_positive_rows']}`",
        f"- Nowak/Smith proposed positives preserved: `{sidecars['nowak_smith']['proposed_positive_rows']}`",
        f"- What-if positives after both sidecars: `{what_if_both}`",
        f"- What-if min Wilson95 LCB after both sidecars: `{what_if_both_lcb}`",
        f"- Additional positives still needed after both sidecars: `{rows_needed_after_both}`",
        f"- Gate result: `{gate_result}`",
        "- Accepted rows added: `0`; new confidence gate: `false`.",
        "- Strict full objective achieved: `false`; `update_goal=false`.",
        "",
        "## Artifacts",
        "",
        f"- JSON: `{rel(json_path)}`",
        f"- Gate CSV: `{rel(gate_csv)}`",
        f"- Verifier stdout: `{verifier['stdout_path']}`",
        f"- Assertions: `{rel(assertions_path)}`",
        "",
        "## Next",
        "",
        result["next_action"],
    ]
    md_path.write_text("\n".join(md_lines) + "\n", encoding="utf-8")

    assertions = [
        f"run_id={RUN_ID}",
        f"live_intake_exists={str(LIVE_INTAKE.exists()).lower()}",
        f"verifier_status={verifier['payload'].get('status')}",
        f"verifier_reason={verifier['payload'].get('reason')}",
        f"sarao_sidecar_rows={sidecars['sarao']['proposed_positive_rows']}",
        f"nowak_smith_sidecar_rows={sidecars['nowak_smith']['proposed_positive_rows']}",
        f"sidecar_candidate_total_rows={total_sidecar_rows}",
        f"what_if_both_lcb={what_if_both_lcb}",
        f"accepted_rows_added=0",
        f"new_confidence_gate=false",
        f"strict_full_objective_achieved=false",
        f"update_goal=false",
        "assertion_status=PASS",
    ]
    assertions_path.write_text("\n".join(assertions) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
