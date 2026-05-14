#!/usr/bin/env python3
"""Live recheck for the source-panel recency-extension intake root."""

from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path


REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = RUN_ROOT / "recency-extension-live-verifier"
CHECK_DIR = RUN_ROOT / "checks"
INTAKE_ROOT = Path("/tmp/ict-engine-source-panel-recency-extension")
VERIFIER = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T165405-codex-source-panel-recency-extension-manifest-v1/"
    "source-panel-recency/source_panel_recency_extension_verifier_v1.py"
)


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)
    cmd = ["python3", str(VERIFIER.relative_to(REPO)), "--intake-root", str(INTAKE_ROOT)]
    proc = subprocess.run(cmd, cwd=REPO, text=True, capture_output=True)
    try:
        parsed = json.loads(proc.stdout)
    except json.JSONDecodeError:
        parsed = {"status": "parse_error", "raw_stdout": proc.stdout}
    intake_files = sorted(str(path) for path in INTAKE_ROOT.glob("*")) if INTAKE_ROOT.exists() else []
    status = parsed.get("status")
    missing_files = parsed.get("missing_files", [])
    decision = (
        "recency_extension_live_verifier_recheck_v1=recency_extension_intake_ready"
        if status == "ready"
        else "recency_extension_live_verifier_recheck_v1=missing_recency_extension_intake_files"
    )
    result = {
        "run_id": RUN_ROOT.name,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "decision": decision,
        "command": cmd,
        "returncode": proc.returncode,
        "stdout_json": parsed,
        "stderr": proc.stderr,
        "intake_root": str(INTAKE_ROOT),
        "intake_files": intake_files,
        "intake_files_present": len(intake_files),
        "missing_files": missing_files,
        "accepted_rows_added": 0,
        "new_confidence_gate": False,
        "recency_extension_ready": status == "ready",
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "trade_usable": False,
    }

    json_path = OUT_DIR / "recency_extension_live_verifier_recheck_v1.json"
    report_path = OUT_DIR / "recency_extension_live_verifier_recheck_v1.md"
    assertion_path = CHECK_DIR / "recency_extension_live_verifier_recheck_v1_assertions.out"
    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    report = [
        "# Recency Extension Live Verifier Recheck v1",
        "",
        f"Run ID: `{RUN_ROOT.name}`",
        "",
        "## Decision",
        "",
        f"`{decision}`",
        "",
        f"- Verifier return code: `{proc.returncode}`.",
        f"- Verifier status: `{status}`.",
        f"- Intake files present: `{len(intake_files)}`.",
        f"- Missing files: `{'; '.join(missing_files) if missing_files else ''}`.",
        "- Accepted rows added: `0`; new confidence gate: `false`.",
        "- Strict full objective achieved: `false`; `update_goal=false`.",
        "- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; trade usable: `false`.",
        "",
        "## Command",
        "",
        "```bash",
        " ".join(cmd),
        "```",
        "",
        "## Artifacts",
        "",
        f"- JSON: `{json_path}`",
        f"- Assertions: `{assertion_path}`",
    ]
    report_path.write_text("\n".join(report) + "\n", encoding="utf-8")

    assertions = [
        f"PASS decision={decision}",
        f"PASS verifier_status={status}",
        f"PASS verifier_returncode={proc.returncode}",
        f"PASS intake_files_present={len(intake_files)}",
        "PASS accepted_rows_added=0",
        "PASS new_confidence_gate=false",
        "PASS strict_full_objective_achieved=false",
        "PASS update_goal=false",
        "PASS raw_data_committed=false",
    ]
    if status != "blocked" or proc.returncode != 2:
        assertions[1] = f"FAIL verifier_status={status}"
    if len(intake_files) != 0:
        assertions[3] = f"FAIL intake_files_present={len(intake_files)}"
    assertion_path.write_text("\n".join(assertions) + "\n", encoding="utf-8")
    return 0 if all(line.startswith("PASS") for line in assertions) else 1


if __name__ == "__main__":
    raise SystemExit(main())
