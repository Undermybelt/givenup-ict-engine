#!/usr/bin/env python3
"""Verify the Board B CrossAssetVolCarryV1 RC-SPA artifact packet.

This run root was produced by the active 215311 Board B process. The verifier is
kept self-contained so later readbacks do not depend on another run-local script.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


RUN_ID = "20260511T215311+0800-codex-board-b-crossasset-vol-carry-v1"
RECIPE_ID = "CrossAssetVolCarryV1"
RUN_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = next(path for path in [RUN_ROOT, *RUN_ROOT.parents] if (path / "Cargo.toml").exists())
REPORT_JSON = RUN_ROOT / "branch-rc-spa/crossasset_vol_carry_rc_spa_report_v1.json"
REPORT_MD = RUN_ROOT / "branch-rc-spa/crossasset_vol_carry_rc_spa_report_v1.md"
ASSERTIONS = RUN_ROOT / "checks/crossasset_vol_carry_v1_assertions.out"
FAIL_CLOSED = RUN_ROOT / "ict-engine-fail-closed/crossasset_vol_carry_fail_closed_summary_v1.md"


def require_file(path: Path) -> None:
    if not path.exists() or path.stat().st_size == 0:
        raise RuntimeError(f"missing or empty artifact: {path}")


def main() -> int:
    for path in [REPORT_JSON, REPORT_MD, ASSERTIONS, FAIL_CLOSED]:
        require_file(path)

    report: dict[str, Any] = json.loads(REPORT_JSON.read_text(encoding="utf-8"))
    decision = report.get("decision", {})
    artifacts = report.get("artifacts", {})

    expected = {
        "run_id": RUN_ID,
        "recipe_id": RECIPE_ID,
        "gate_result": "fail:required_root_branch_hard_gates_failed",
        "downstream_consumption": "not_started:blocked_by_branch_rc_spa_hard_gates",
        "price_root_paths_passed": 0,
        "manipulation_component_pass": True,
    }
    observed = {
        "run_id": report.get("run_id"),
        "recipe_id": report.get("recipe_id"),
        "gate_result": decision.get("gate_result"),
        "downstream_consumption": decision.get("downstream_consumption"),
        "price_root_paths_passed": decision.get("price_root_paths_passed"),
        "manipulation_component_pass": decision.get("manipulation_component_pass"),
    }
    mismatches = {key: {"expected": value, "observed": observed.get(key)} for key, value in expected.items() if observed.get(key) != value}
    if mismatches:
        raise RuntimeError(json.dumps({"mismatches": mismatches}, indent=2, sort_keys=True))

    for rel_path in artifacts.values():
        artifact_path = REPO_ROOT / rel_path if str(rel_path).startswith("docs/") else Path(rel_path)
        require_file(artifact_path)

    print(json.dumps({"artifact_packet_verified": True, **observed}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
