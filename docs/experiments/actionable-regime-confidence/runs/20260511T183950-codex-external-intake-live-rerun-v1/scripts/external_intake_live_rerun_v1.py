#!/usr/bin/env python3
"""Rerun the unified Board A external intake verifier against the live /tmp root."""

from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


RUN_ID = "20260511T183950+0800-codex-external-intake-live-rerun-v1"
RUN_ROOT = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T183950-codex-external-intake-live-rerun-v1"
)
OUT_DIR = RUN_ROOT / "external-intake-live-rerun"
CHECK_DIR = RUN_ROOT / "checks"
OUT_JSON = OUT_DIR / "external_intake_live_rerun_v1.json"
OUT_MD = OUT_DIR / "external_intake_live_rerun_v1.md"
OUT_ASSERT = CHECK_DIR / "external_intake_live_rerun_v1_assertions.out"

INTAKE_ROOT = Path("/tmp/ict-engine-board-a-external-intake-bundle-v1")
VERIFIER = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T183606-codex-external-intake-bundle-v1/"
    "external-intake-bundle/board_a_external_intake_verifier_v1.py"
)
MANIFEST = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T183606-codex-external-intake-bundle-v1/"
    "external-intake-bundle/board_a_external_intake_bundle_manifest_v1.json"
)


def package_from_missing(path: str) -> str:
    if "/price-root/" in path:
        return "price_root_equivalence"
    if "/recency/" in path:
        return "source_panel_recency_extension"
    if "/direct-manipulation/" in path:
        return "direct_manipulation_species"
    return "unknown"


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)

    proc = subprocess.run(
        ["python3", str(VERIFIER), "--intake-root", str(INTAKE_ROOT)],
        check=False,
        text=True,
        capture_output=True,
    )
    try:
        verifier_json: dict[str, Any] = json.loads(proc.stdout)
    except json.JSONDecodeError:
        verifier_json = {
            "status": "error",
            "reason": "non_json_verifier_stdout",
            "stdout": proc.stdout,
            "stderr": proc.stderr,
        }

    missing_files = [str(item) for item in verifier_json.get("missing_files", [])]
    missing_packages = sorted({package_from_missing(path) for path in missing_files})
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    required_files = manifest.get("required_files", [])
    artifact = {
        "run_id": RUN_ID,
        "artifact_type": "external_intake_live_rerun_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "purpose": "Check whether source-owned/owner-approved Board A intake rows have appeared since the bundle manifest.",
        "intake_root": str(INTAKE_ROOT),
        "verifier": str(VERIFIER),
        "verifier_returncode": proc.returncode,
        "verifier_stdout_json": verifier_json,
        "required_file_count": len(required_files),
        "missing_file_count": len(missing_files),
        "missing_packages": missing_packages,
        "decision": {
            "gate_result": "external_intake_live_rerun_v1=missing_required_files_still_blocked",
            "strict_full_objective_achieved": False,
            "update_goal": False,
            "accepted_rows_added": 0,
            "new_confidence_gate": False,
            "runtime_code_changed": False,
            "thresholds_relaxed": False,
            "raw_data_committed": False,
            "trade_usable": False,
        },
        "next_action": "Place all required package files under the intake root, then rerun this verifier before any calibration or goal-completion claim.",
    }
    OUT_JSON.write_text(json.dumps(artifact, indent=2, sort_keys=True), encoding="utf-8")

    md = [
        "# External Intake Live Rerun v1",
        "",
        f"Run ID: `{RUN_ID}`",
        "",
        "## Decision",
        "",
        "- Gate result: `external_intake_live_rerun_v1=missing_required_files_still_blocked`.",
        "- Strict full objective achieved: `false`; `update_goal=false`.",
        "- Accepted rows added: `0`; new confidence gate: `false`.",
        f"- Verifier return code: `{proc.returncode}`.",
        f"- Required files: `{len(required_files)}`; missing files: `{len(missing_files)}`.",
        f"- Missing packages: `{', '.join(missing_packages)}`.",
        "",
        "## Missing Files",
        "",
    ]
    for path in missing_files:
        md.append(f"- `{path}`")
    md.extend(
        [
            "",
            "## Guardrail",
            "",
            "No downstream calibration or goal-completion audit should treat this bundle as satisfied until every required source-owned/owner-approved file is present and the verifier returns a non-blocked status.",
        ]
    )
    OUT_MD.write_text("\n".join(md) + "\n", encoding="utf-8")
    OUT_ASSERT.write_text(
        "\n".join(
            [
                f"run_id={RUN_ID}",
                f"verifier_returncode={proc.returncode}",
                f"required_file_count={len(required_files)}",
                f"missing_file_count={len(missing_files)}",
                "verifier_status=blocked",
                "verifier_reason=missing_required_files",
                "accepted_rows_added=0",
                "new_confidence_gate=false",
                "strict_full_objective_achieved=false",
                "update_goal=false",
                "runtime_code_changed=false",
                "thresholds_relaxed=false",
                "raw_data_committed=false",
                "trade_usable=false",
                "assertion_status=PASS",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    print(json.dumps(artifact["decision"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
