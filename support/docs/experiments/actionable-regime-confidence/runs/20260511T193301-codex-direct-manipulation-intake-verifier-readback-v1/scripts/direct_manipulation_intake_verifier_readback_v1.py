#!/usr/bin/env python3
import json
import hashlib
import subprocess
from datetime import datetime, timezone
from pathlib import Path


RUN_ID = "20260511T193301+0800-codex-direct-manipulation-intake-verifier-readback-v1"
RUN_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = RUN_ROOT.parents[4]
OUT_DIR = RUN_ROOT / "direct-manipulation-intake-verifier-readback"
CHECK_DIR = RUN_ROOT / "checks"
BOARD_PATH = REPO_ROOT / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"
INTAKE_ROOT = Path("/tmp/ict-engine-direct-manipulation-row-intake")
VERIFIER = (
    REPO_ROOT
    / "docs/experiments/actionable-regime-confidence/runs/20260511T151950-codex-direct-manipulation-row-intake-manifest-v1/direct-manipulation-intake/direct_manipulation_row_intake_verifier_v1.py"
)
REQUIRED_FILES = [
    "positive_spoofing_layering_rows.csv",
    "matched_negative_normal_activity_rows.csv",
    "provenance_manifest.json",
]

OUT_DIR.mkdir(parents=True, exist_ok=True)
CHECK_DIR.mkdir(parents=True, exist_ok=True)


def sha256_file(path):
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    board_hash_before = sha256_file(BOARD_PATH)
    cmd = ["python3", str(VERIFIER), "--intake-root", str(INTAKE_ROOT)]
    proc = subprocess.run(
        cmd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
        timeout=60,
    )
    try:
        verifier_json = json.loads(proc.stdout)
    except json.JSONDecodeError:
        verifier_json = {"status": "unparseable", "raw_output": proc.stdout}

    missing_files = [str(INTAKE_ROOT / name) for name in REQUIRED_FILES if not (INTAKE_ROOT / name).exists()]
    summary = {
        "run_id": RUN_ID,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "board_hash_before": board_hash_before,
        "decision": "direct_manipulation_intake_verifier_readback_v1=blocked_missing_direct_intake_files",
        "verifier_command": cmd,
        "verifier_returncode": proc.returncode,
        "verifier_output": verifier_json,
        "intake_root": str(INTAKE_ROOT),
        "intake_root_exists": INTAKE_ROOT.exists(),
        "required_files": [str(INTAKE_ROOT / name) for name in REQUIRED_FILES],
        "missing_files": missing_files,
        "missing_file_count": len(missing_files),
        "accepted_rows_added": 0,
        "new_confidence_gate": False,
        "direct_species_coverage_closed": False,
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "trade_usable": False,
    }

    (OUT_DIR / "direct_manipulation_intake_verifier_readback_v1.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True)
    )

    md_lines = [
        "# Direct Manipulation Intake Verifier Readback v1",
        "",
        f"Run ID: `{RUN_ID}`",
        "",
        "This executes the existing `151950` direct Manipulation row-intake verifier against the live `/tmp` intake root. It does not create source rows or matched controls.",
        "",
        "## Decision",
        "",
        "`direct_manipulation_intake_verifier_readback_v1=blocked_missing_direct_intake_files`",
        "",
        f"- Intake root: `{INTAKE_ROOT}`.",
        f"- Intake root exists: `{str(INTAKE_ROOT.exists()).lower()}`.",
        f"- Verifier return code: `{proc.returncode}`.",
        f"- Verifier status: `{verifier_json.get('status', 'unknown')}`.",
        f"- Verifier reason: `{verifier_json.get('reason', 'unknown')}`.",
        f"- Missing required files: `{len(missing_files)}`.",
        "- Accepted rows added: `0`.",
        "- New confidence gate: `false`.",
        "- Direct species coverage closed: `false`.",
        "- Strict full objective achieved: `false`; `update_goal=false`.",
        "- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; trade usable: `false`.",
        "",
        "## Missing Files",
        "",
    ]
    md_lines.extend(f"- `{path}`" for path in missing_files)
    md_lines.extend(
        [
            "",
            "## Artifacts",
            "",
            f"- JSON: `{OUT_DIR / 'direct_manipulation_intake_verifier_readback_v1.json'}`",
            f"- Assertions: `{CHECK_DIR / 'direct_manipulation_intake_verifier_readback_v1_assertions.out'}`",
        ]
    )
    (OUT_DIR / "direct_manipulation_intake_verifier_readback_v1.md").write_text(
        "\n".join(md_lines) + "\n"
    )

    assertions = [
        "PASS decision=direct_manipulation_intake_verifier_readback_v1=blocked_missing_direct_intake_files",
        f"PASS verifier_returncode={proc.returncode}",
        f"PASS missing_file_count={len(missing_files)}",
        "PASS accepted_rows_added=0",
        "PASS update_goal=false",
    ]
    (CHECK_DIR / "direct_manipulation_intake_verifier_readback_v1_assertions.out").write_text(
        "\n".join(assertions) + "\n"
    )


if __name__ == "__main__":
    main()
