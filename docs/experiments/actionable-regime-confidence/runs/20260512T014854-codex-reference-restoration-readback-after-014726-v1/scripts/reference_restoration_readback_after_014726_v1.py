#!/usr/bin/env python3
"""Reproduce the reference-restoration readback after the 014726 correction."""

from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[6]
RUNS = ROOT / "docs/experiments/actionable-regime-confidence/runs"

checks = {
    "014221_json": RUNS / "20260512T014221-codex-current-objective-completion-audit-after-013904-v1/current-objective-completion-audit-after-013904-v1/current_objective_completion_audit_after_013904_v1.json",
    "014221_assertions": RUNS / "20260512T014221-codex-current-objective-completion-audit-after-013904-v1/checks/current_objective_completion_audit_after_013904_v1_assertions.out",
    "014314_json": RUNS / "20260512T014314-codex-r6-owner-route-current-web-recheck-v1/r6-owner-route-current-web-recheck-v1/r6_owner_route_current_web_recheck_v1.json",
    "014314_assertions": RUNS / "20260512T014314-codex-r6-owner-route-current-web-recheck-v1/checks/r6_owner_route_current_web_recheck_v1_assertions.out",
}

missing = [name for name, path in checks.items() if not path.exists()]
if missing:
    raise SystemExit(f"missing required files: {missing}")

audit_014221 = json.loads(checks["014221_json"].read_text())
audit_014314 = json.loads(checks["014314_json"].read_text())

assert audit_014221["accepted_rows_added"] == 0
assert audit_014221["canonical_merge_allowed"] is False
assert audit_014221["downstream_chain_rerun_allowed"] is False
assert audit_014221["strict_full_objective_achieved"] is False
assert audit_014221["update_goal"] is False

assert audit_014314["accepted_rows_added"] == 0
assert audit_014314["canonical_merge_allowed"] is False
assert audit_014314["downstream_promotion_rerun_allowed"] is False
assert audit_014314["strict_full_objective_achieved"] is False
assert audit_014314["update_goal"] is False

print("reference_restoration_readback_after_014726_v1=PASS")
