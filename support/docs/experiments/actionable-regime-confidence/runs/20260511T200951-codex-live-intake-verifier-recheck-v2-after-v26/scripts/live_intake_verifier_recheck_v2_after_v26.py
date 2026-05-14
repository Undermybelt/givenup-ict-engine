#!/usr/bin/env python3
"""Live verifier recheck for Board A source-label/direct-manipulation intake roots."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path


RUN_ID = "20260511T200951-codex-live-intake-verifier-recheck-v2-after-v26"
RUN_ROOT = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T200951-codex-live-intake-verifier-recheck-v2-after-v26"
)
OUT_DIR = RUN_ROOT / "live-intake-verifier-recheck"
CHECK_DIR = RUN_ROOT / "checks"

SOURCE_LABEL_VERIFIER = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T182922-codex-source-label-equivalence-intake-verifier-v1/"
    "equivalence-intake-verifier/source_label_equivalence_intake_verifier_v1.py"
)
DIRECT_VERIFIER = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T151950-codex-direct-manipulation-row-intake-manifest-v1/"
    "direct-manipulation-intake/direct_manipulation_row_intake_verifier_v1.py"
)

SOURCE_LABEL_ROOT = Path("/tmp/ict-engine-source-label-equivalence-intake")
DIRECT_ROOT = Path("/tmp/ict-engine-direct-manipulation-row-intake")


def run_json_command(args: list[str]) -> dict[str, object]:
    proc = subprocess.run(args, text=True, capture_output=True, check=False)
    parsed: object
    try:
        parsed = json.loads(proc.stdout)
    except json.JSONDecodeError:
        parsed = {"raw_stdout": proc.stdout}
    return {
        "args": args,
        "returncode": proc.returncode,
        "stdout_json": parsed,
        "stderr": proc.stderr,
    }


def list_files(root: Path) -> list[str]:
    if not root.exists():
        return []
    return sorted(str(path) for path in root.rglob("*") if path.is_file())


def write_report(payload: dict[str, object]) -> None:
    report = OUT_DIR / "live_intake_verifier_recheck_v2_after_v26.md"
    source = payload["source_label_recheck"]
    direct = payload["direct_manipulation_recheck"]
    lines = [
        "# Live Intake Verifier Recheck v2 After v26",
        "",
        f"Run ID: `{RUN_ID}`",
        "",
        "## Decision",
        "",
        f"`{payload['decision']}`",
        "",
        f"- Source-label verifier status: `{payload['source_label_status']}`.",
        f"- Direct-manipulation verifier status: `{payload['direct_manipulation_status']}`.",
        f"- Intake files present: `{payload['intake_files_present']}`.",
        f"- Accepted rows added: `{payload['accepted_rows_added']}`; new confidence gate: `{str(payload['new_confidence_gate']).lower()}`.",
        f"- Strict full objective achieved: `{str(payload['strict_full_objective_achieved']).lower()}`; `update_goal={str(payload['update_goal']).lower()}`.",
        "",
        "## Source-Label Equivalence Verifier",
        "",
        f"- Return code: `{source['returncode']}`",
        f"- Parsed output: `{json.dumps(source['stdout_json'], sort_keys=True)}`",
        "",
        "## Direct Manipulation Verifier",
        "",
        f"- Return code: `{direct['returncode']}`",
        f"- Parsed output: `{json.dumps(direct['stdout_json'], sort_keys=True)}`",
        "",
        "## Carry-Forward Blocker",
        "",
        "No live intake files are present under either `/tmp` root. R2/R4 source-label equivalence and R6 direct spoofing/layering intake remain blocked.",
        "",
    ]
    report.write_text("\n".join(lines))


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)

    source_result = run_json_command(
        [
            "python3",
            str(SOURCE_LABEL_VERIFIER),
            "--intake-root",
            str(SOURCE_LABEL_ROOT),
        ]
    )
    direct_result = run_json_command(
        [
            "python3",
            str(DIRECT_VERIFIER),
            "--intake-root",
            str(DIRECT_ROOT),
        ]
    )
    files = list_files(SOURCE_LABEL_ROOT) + list_files(DIRECT_ROOT)
    source_status = source_result["stdout_json"].get("status") if isinstance(source_result["stdout_json"], dict) else "unknown"
    direct_status = direct_result["stdout_json"].get("status") if isinstance(direct_result["stdout_json"], dict) else "unknown"

    payload: dict[str, object] = {
        "run_id": RUN_ID,
        "decision": "live_intake_verifier_recheck_v2_after_v26=both_required_intake_roots_still_missing_files",
        "source_label_recheck": source_result,
        "direct_manipulation_recheck": direct_result,
        "source_label_status": source_status,
        "direct_manipulation_status": direct_status,
        "intake_files": files,
        "intake_files_present": len(files),
        "accepted_rows_added": 0,
        "new_confidence_gate": False,
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "trade_usable": False,
    }
    json_path = OUT_DIR / "live_intake_verifier_recheck_v2_after_v26.json"
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    write_report(payload)

    assertions = [
        ("source_label_blocked", source_status == "blocked"),
        ("direct_manipulation_blocked", direct_status == "blocked"),
        ("intake_files_present_zero", len(files) == 0),
        ("accepted_rows_added_zero", payload["accepted_rows_added"] == 0),
        ("new_confidence_gate_false", payload["new_confidence_gate"] is False),
        ("strict_full_objective_achieved_false", payload["strict_full_objective_achieved"] is False),
        ("update_goal_false", payload["update_goal"] is False),
    ]
    failed = [name for name, ok in assertions if not ok]
    (CHECK_DIR / "live_intake_verifier_recheck_v2_after_v26_assertions.out").write_text(
        "\n".join(f"{name}=PASS" if ok else f"{name}=FAIL" for name, ok in assertions)
        + "\n"
    )
    if failed:
        raise SystemExit(f"failed assertions: {', '.join(failed)}")


if __name__ == "__main__":
    main()
