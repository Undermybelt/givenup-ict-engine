#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path


RUN_ID = "20260512T014314-codex-r6-owner-route-current-web-recheck-v1"


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    data_path = root / "r6-owner-route-current-web-recheck-v1" / "r6_owner_route_current_web_recheck_v1.json"
    data = json.loads(data_path.read_text(encoding="utf-8"))
    checks = {
        "run_id": data["run_id"] == RUN_ID,
        "gate_result": data["gate_result"] == "r6_owner_route_current_web_recheck_v1=current_official_routes_rechecked_controls_not_acquired_no_merge",
        "official_sources": len(data["official_sources"]) == 4,
        "current_cursor_preserved": data["current_cursor_preserved"] is True,
        "accepted_rows_added": data["accepted_rows_added"] == 0,
        "new_confidence_gate": data["new_confidence_gate"] is False,
        "canonical_merge_allowed": data["canonical_merge_allowed"] is False,
        "downstream_promotion_rerun_allowed": data["downstream_promotion_rerun_allowed"] is False,
        "strict_full_objective_achieved": data["strict_full_objective_achieved"] is False,
        "update_goal": data["update_goal"] is False,
        "runtime_code_changed": data["runtime_code_changed"] is False,
        "shared_intake_mutated": data["shared_intake_mutated"] is False,
        "r3_r5_r6_roots_mutated": data["r3_r5_r6_roots_mutated"] is False,
        "thresholds_relaxed": data["thresholds_relaxed"] is False,
        "raw_data_committed": data["raw_data_committed"] is False,
        "external_requests_sent": data["external_requests_sent"] is False,
        "trade_usable": data["trade_usable"] is False,
    }
    for key, passed in checks.items():
        print(f"{'PASS' if passed else 'FAIL'} {key}")
    return 0 if all(checks.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
