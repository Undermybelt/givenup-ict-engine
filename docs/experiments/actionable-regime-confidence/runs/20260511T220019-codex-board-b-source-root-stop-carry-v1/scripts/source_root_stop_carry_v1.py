#!/usr/bin/env python3
"""Verify the Board B SourceRootStopCarryV1 RC-SPA artifact packet."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any


RUN_ID = "20260511T220019+0800-codex-board-b-source-root-stop-carry-v1"
RECIPE_ID = "SourceRootStopCarryV1"
RUN_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = next(path for path in [RUN_ROOT, *RUN_ROOT.parents] if (path / "Cargo.toml").exists())

REPORT_JSON = RUN_ROOT / "branch-rc-spa/source_root_stop_carry_rc_spa_report_v1.json"
REPORT_MD = RUN_ROOT / "branch-rc-spa/source_root_stop_carry_rc_spa_report_v1.md"
SELECTED_ROWS = RUN_ROOT / "branch-rc-spa/source_root_stop_carry_selected_rows_v1.csv"
VARIANT_ROWS = RUN_ROOT / "branch-rc-spa/source_root_stop_carry_variant_rows_v1.csv"
SUMMARY_CSV = RUN_ROOT / "branch-rc-spa/source_root_stop_carry_branch_summary_v1.csv"
ASSERTIONS = RUN_ROOT / "checks/source_root_stop_carry_v1_assertions.out"
FAIL_CLOSED = RUN_ROOT / "ict-engine-fail-closed/source_root_stop_carry_fail_closed_summary_v1.md"


def require_file(path: Path) -> None:
    if not path.exists() or path.stat().st_size == 0:
        raise RuntimeError(f"missing or empty artifact: {path}")


def csv_data_rows(path: Path) -> int:
    with path.open(newline="", encoding="utf-8") as fh:
        return max(0, sum(1 for _ in csv.reader(fh)) - 1)


def main() -> int:
    for path in [REPORT_JSON, REPORT_MD, SELECTED_ROWS, VARIANT_ROWS, SUMMARY_CSV, ASSERTIONS, FAIL_CLOSED]:
        require_file(path)

    report: dict[str, Any] = json.loads(REPORT_JSON.read_text(encoding="utf-8"))
    decision = report.get("decision", {})
    observed = {
        "run_id": report.get("run_id"),
        "recipe_id": report.get("recipe_id"),
        "gate_result": decision.get("gate_result"),
        "downstream_consumption": decision.get("downstream_consumption"),
        "price_root_paths_passed": decision.get("price_root_paths_passed"),
        "manipulation_component_pass": decision.get("manipulation_component_pass"),
        "variant_trade_rows": decision.get("variant_trade_rows"),
        "selected_trade_rows": decision.get("selected_trade_rows"),
    }
    expected = {
        "run_id": RUN_ID,
        "recipe_id": RECIPE_ID,
        "gate_result": "fail:required_root_branch_hard_gates_failed",
        "downstream_consumption": "not_started:blocked_by_branch_rc_spa_hard_gates",
        "price_root_paths_passed": 0,
        "manipulation_component_pass": True,
        "variant_trade_rows": csv_data_rows(VARIANT_ROWS),
        "selected_trade_rows": csv_data_rows(SELECTED_ROWS),
    }
    mismatches = {
        key: {"expected": value, "observed": observed.get(key)}
        for key, value in expected.items()
        if observed.get(key) != value
    }
    if mismatches:
        raise RuntimeError(json.dumps({"mismatches": mismatches}, indent=2, sort_keys=True))

    assertion_text = ASSERTIONS.read_text(encoding="utf-8")
    for key, value in expected.items():
        if key in {"run_id", "recipe_id"}:
            continue
        token = f"{key}={value}"
        if token not in assertion_text:
            raise RuntimeError(f"assertion output missing token: {token}")

    summary_roots = set()
    with SUMMARY_CSV.open(newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            summary_roots.add(row.get("parent_regime_root", ""))
    required_roots = {"Bull", "Bear", "Sideways", "Crisis", "Manipulation(scoped)"}
    if not required_roots.issubset(summary_roots):
        raise RuntimeError(f"missing summary roots: {sorted(required_roots - summary_roots)}")

    for rel_path in report.get("artifacts", {}).values():
        artifact_path = REPO_ROOT / rel_path if str(rel_path).startswith("docs/") else Path(rel_path)
        require_file(artifact_path)

    print(json.dumps({"artifact_packet_verified": True, **observed}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
