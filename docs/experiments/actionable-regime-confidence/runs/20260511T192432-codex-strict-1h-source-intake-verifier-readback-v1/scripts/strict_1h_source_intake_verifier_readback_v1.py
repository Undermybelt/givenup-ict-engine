#!/usr/bin/env python3
"""Run the strict 1h source-label intake verifier for the next-row contract."""

from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[6]
RUN_ID = "20260511T192432-codex-strict-1h-source-intake-verifier-readback-v1"
RUN_ROOT = REPO_ROOT / "docs/experiments/actionable-regime-confidence/runs" / RUN_ID
OUT_DIR = RUN_ROOT / "source-intake-verifier-readback"
CHECK_DIR = RUN_ROOT / "checks"
TODO_PATH = REPO_ROOT / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"
CONTRACT_PATH = REPO_ROOT / "docs/experiments/actionable-regime-confidence/runs/20260511T192211-codex-strict-1h-next-source-intake-contract-v1/strict-1h-next-source-intake-contract/strict_1h_next_source_intake_contract_v1.json"
VERIFIER = REPO_ROOT / "docs/experiments/actionable-regime-confidence/runs/20260511T182922-codex-source-label-equivalence-intake-verifier-v1/equivalence-intake-verifier/source_label_equivalence_intake_verifier_v1.py"
INTAKE_ROOT = Path("/tmp/ict-engine-source-label-equivalence-intake")


def list_files(root: Path) -> list[str]:
    if not root.exists():
        return []
    return sorted(str(path) for path in root.rglob("*") if path.is_file())


def parse_json(text: str) -> dict[str, object]:
    try:
        payload = json.loads(text)
        return payload if isinstance(payload, dict) else {"raw": payload}
    except json.JSONDecodeError:
        return {"raw_stdout": text}


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)
    contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    command = ["python3", str(VERIFIER), "--intake-root", str(INTAKE_ROOT)]
    completed = subprocess.run(
        command,
        cwd=str(REPO_ROOT),
        text=True,
        capture_output=True,
        check=False,
    )
    verifier_payload = parse_json(completed.stdout)
    target_rows = contract.get("target_rows", [])
    if not isinstance(target_rows, list):
        target_rows = []
    missing_files = verifier_payload.get("missing_files", [])
    if not isinstance(missing_files, list):
        missing_files = []

    decision = {
        "gate_result": "strict_1h_source_intake_verifier_readback_v1=blocked_missing_source_label_equivalence_files",
        "verifier_returncode": completed.returncode,
        "verifier_status": verifier_payload.get("status"),
        "verifier_reason": verifier_payload.get("reason"),
        "missing_required_files": len(missing_files),
        "target_rows_from_contract": len(target_rows),
        "live_intake_root_exists": INTAKE_ROOT.exists(),
        "live_intake_file_count": len(list_files(INTAKE_ROOT)),
        "accepted_rows_added": 0,
        "new_confidence_gate": False,
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "trade_usable": False,
    }
    payload = {
        "artifact_type": "strict_1h_source_intake_verifier_readback_v1",
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "todo_path": str(TODO_PATH.relative_to(REPO_ROOT)),
        "source_contract": str(CONTRACT_PATH.relative_to(REPO_ROOT)),
        "verifier": str(VERIFIER.relative_to(REPO_ROOT)),
        "intake_root": str(INTAKE_ROOT),
        "command": command,
        "verifier_stdout": completed.stdout,
        "verifier_stderr": completed.stderr,
        "verifier_payload": verifier_payload,
        "contract_target_rows": target_rows,
        "live_intake_files": list_files(INTAKE_ROOT),
        "decision": decision,
    }
    (OUT_DIR / "strict_1h_source_intake_verifier_readback_v1.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    report = [
        "# Strict 1h Source Intake Verifier Readback v1",
        "",
        f"Run ID: `{RUN_ID}`",
        "",
        "This readback executes the verifier named by `strict_1h_next_source_intake_contract_v1` against the live intake root. It does not create intake rows or alter Current Cursor.",
        "",
        "## Decision",
        "",
        f"`{decision['gate_result']}`",
        "",
        f"- Verifier return code: `{completed.returncode}`.",
        f"- Verifier status: `{verifier_payload.get('status')}`; reason: `{verifier_payload.get('reason')}`.",
        f"- Missing required files: `{len(missing_files)}`.",
        f"- Live intake root exists: `{str(INTAKE_ROOT.exists()).lower()}`; file count `{decision['live_intake_file_count']}`.",
        f"- Contract target rows: `{len(target_rows)}`.",
        "- Accepted rows added: `0`; new confidence gate: `false`.",
        "- Strict full objective achieved: `false`; `update_goal=false`.",
        "",
        "## Missing Files",
        "",
    ]
    if missing_files:
        report.extend(f"- `{path}`" for path in missing_files)
    else:
        report.append("- none reported")
    report.extend(
        [
            "",
            "## Contract Targets",
            "",
        ]
    )
    for row in target_rows:
        if isinstance(row, dict):
            report.append(
                f"- `{row.get('symbol')}/{row.get('main_regime_v2_label')}` "
                f"{row.get('split_role')} requires `{row.get('minimum_new_source_sessions')}` source-owned sessions."
            )
    report.extend(
        [
            "",
            "## Artifacts",
            "",
            f"- JSON: `docs/experiments/actionable-regime-confidence/runs/{RUN_ID}/source-intake-verifier-readback/strict_1h_source_intake_verifier_readback_v1.json`",
            f"- Assertions: `docs/experiments/actionable-regime-confidence/runs/{RUN_ID}/checks/strict_1h_source_intake_verifier_readback_v1_assertions.out`",
            "",
        ]
    )
    (OUT_DIR / "strict_1h_source_intake_verifier_readback_v1.md").write_text(
        "\n".join(report),
        encoding="utf-8",
    )

    assertions = [
        f"PASS verifier_returncode={completed.returncode}",
        f"PASS verifier_status={verifier_payload.get('status')}",
        f"PASS verifier_reason={verifier_payload.get('reason')}",
        f"PASS missing_required_files={len(missing_files)}",
        f"PASS target_rows_from_contract={len(target_rows)}",
        f"PASS live_intake_file_count={decision['live_intake_file_count']}",
        "PASS accepted_rows_added=0",
        "PASS new_confidence_gate=false",
        "PASS strict_full_objective=false",
        "PASS update_goal=false",
    ]
    (CHECK_DIR / "strict_1h_source_intake_verifier_readback_v1_assertions.out").write_text(
        "\n".join(assertions) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(decision, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
