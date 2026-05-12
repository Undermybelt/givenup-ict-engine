#!/usr/bin/env python3
"""Corrected current-objective audit after TSIE target-root quarantine."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


RUN_ID = "20260512T063906+0800-codex-current-objective-audit-after-r3-tsie-quarantine-v1"
RUN_ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_DIR = RUN_ROOT / "current-objective-audit-after-r3-tsie-quarantine-v1"
CHECK_DIR = RUN_ROOT / "checks"
R3_ROOT = Path("/tmp/ict-engine-native-subhour-source-label-intake")
R3_PROVENANCE = R3_ROOT / "native_subhour_source_label_provenance.json"
R3_ROWS = R3_ROOT / "native_subhour_source_label_rows.csv"
R6_ROOT = Path("/tmp/ict-engine-board-a-r6-owner-export-v1")
R5_ROOT = Path("/tmp/ict-engine-source-panel-recency-extension")
QUARANTINE_ASSERTIONS = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260512T063707+0800-codex-r3-tsie-target-root-policy-quarantine-v1/"
    "checks/r3_tsie_target_root_policy_quarantine_v1_assertions.out"
)
MATERIALIZATION_ASSERTIONS = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260512T063155+0800-codex-r3-tsie-native-subhour-intake-materialization-v1/"
    "checks/r3_tsie_native_subhour_intake_materialization_v1_assertions.out"
)


def load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text())


def count_files(path: Path) -> int:
    if not path.exists():
        return 0
    return sum(1 for item in path.rglob("*") if item.is_file())


def main() -> int:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)
    prov = load_json(R3_PROVENANCE)
    physical_labels = prov.get("accepted_mapping_confidence_95_labels", [])
    result = {
        "run_id": RUN_ID,
        "observed_at_utc": datetime.now(timezone.utc).isoformat(),
        "gate_result": "current_objective_audit_after_r3_tsie_quarantine_v1=not_complete_tsie_root_present_policy_quarantined_no_unlock",
        "readback": {
            "r3_root_present": R3_ROOT.exists(),
            "r3_required_files_complete": R3_ROWS.exists() and R3_PROVENANCE.exists(),
            "r3_file_count": count_files(R3_ROOT),
            "r3_physical_row_count": prov.get("row_count", 0),
            "r3_physical_mapping_labels": physical_labels,
            "quarantine_assertions": str(QUARANTINE_ASSERTIONS),
            "materialization_assertions": str(MATERIALIZATION_ASSERTIONS),
            "r6_root_present": R6_ROOT.exists(),
            "r5_root_present": R5_ROOT.exists(),
        },
        "decision": {
            "r3_counts_as_unlock": False,
            "r3_policy_state": "present_quarantined_proxy_tsie_not_accepted",
            "accepted_rows_added_for_board_a": 0,
            "accepted_regime_roots_after_quarantine": [],
            "missing_or_blocked_roots": ["Bull", "Bear", "Sideways", "Crisis"],
            "r6_source_control_evidence_acquired": False,
            "r5_recency_evidence_acquired": False,
            "canonical_merge": False,
            "downstream_promotion_rerun": False,
            "strict_full_objective": False,
            "trade_usable": False,
            "update_goal": False,
        },
        "next_action": (
            "Treat the TSIE root as quarantined/proxy evidence only. Replace it with explicit "
            "source/control-approved R3 MainRegimeV2 labels or obtain R6 owner/export controls, "
            "source-owned R5 recency, or a genuine Crisis-capable source packet before canonical "
            "merge and downstream readback."
        ),
    }
    json_path = ARTIFACT_DIR / "current_objective_audit_after_r3_tsie_quarantine_v1.json"
    md_path = ARTIFACT_DIR / "current_objective_audit_after_r3_tsie_quarantine_v1.md"
    assertions = CHECK_DIR / "current_objective_audit_after_r3_tsie_quarantine_v1_assertions.out"
    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    md_path.write_text(
        "\n".join(
            [
                "# Current Objective Audit After R3 TSIE Quarantine v1",
                "",
                f"Run id: `{RUN_ID}`",
                "",
                f"Gate result: `{result['gate_result']}`",
                "",
                "Readback:",
                f"- R3 target path present: `{result['readback']['r3_root_present']}`.",
                f"- R3 physical rows from TSIE materialization: `{result['readback']['r3_physical_row_count']}`.",
                f"- Physical mapping labels: `{', '.join(physical_labels) if physical_labels else 'none'}`.",
                f"- R6 owner/export root present: `{result['readback']['r6_root_present']}`.",
                f"- R5 recency root present: `{result['readback']['r5_root_present']}`.",
                "",
                "Decision:",
                "- The TSIE root is present but policy-quarantined by the current board ledger.",
                "- It does not count as an R3 unlock, accepted Board A evidence, canonical merge input, downstream promotion evidence, or trade evidence.",
                "- Board A accepted rows added remains `0` for this TSIE branch; `update_goal=false`.",
                "",
                "Next:",
                f"- {result['next_action']}",
                "",
            ]
        )
    )
    assertions.write_text(
        "\n".join(
            [
                f"gate_result={result['gate_result']}",
                f"r3_root_present={str(result['readback']['r3_root_present']).lower()}",
                "r3_counts_as_unlock=false",
                "accepted_rows_added_for_board_a=0",
                "canonical_merge=false",
                "downstream_promotion_rerun=false",
                "strict_full_objective=false",
                "trade_usable=false",
                "update_goal=false",
                "",
            ]
        )
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
