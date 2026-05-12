#!/usr/bin/env python3
"""Audit Board A objective after the R3 TSIE target root materialization."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


RUN_ID = "20260512T063733+0800-codex-current-objective-audit-after-r3-tsie-materialization-v1"
RUN_ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_DIR = RUN_ROOT / "current-objective-audit-after-r3-tsie-materialization-v1"
CHECK_DIR = RUN_ROOT / "checks"
R3_PROVENANCE = Path("/tmp/ict-engine-native-subhour-source-label-intake/native_subhour_source_label_provenance.json")
R3_ROWS = Path("/tmp/ict-engine-native-subhour-source-label-intake/native_subhour_source_label_rows.csv")
R6_ROOT = Path("/tmp/ict-engine-board-a-r6-owner-export-v1")
R5_ROOT = Path("/tmp/ict-engine-source-panel-recency-extension")
EQUIV_ROOT = Path("/tmp/ict-engine-source-label-equivalence-intake")
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
    r3_provenance = load_json(R3_PROVENANCE)
    accepted_labels = r3_provenance.get("accepted_mapping_confidence_95_labels", [])
    missing_active_roots = [label for label in ["Bear", "Bull", "Sideways", "Crisis"] if label not in accepted_labels]
    r3_ready = R3_ROWS.exists() and R3_PROVENANCE.exists() and set(["Bear", "Bull", "Sideways"]).issubset(set(accepted_labels))
    result = {
        "run_id": RUN_ID,
        "observed_at_utc": datetime.now(timezone.utc).isoformat(),
        "gate_result": "current_objective_audit_after_r3_tsie_materialization_v1=not_complete_r3_bull_bear_sideways_ready_crisis_r6_r5_downstream_blocked",
        "source_roots": {
            "r3_native_subhour": {
                "root": str(R3_ROWS.parent),
                "present": R3_ROWS.parent.exists(),
                "required_files_complete": R3_ROWS.exists() and R3_PROVENANCE.exists(),
                "file_count": count_files(R3_ROWS.parent),
                "row_count": r3_provenance.get("row_count", 0),
                "accepted_mapping_confidence_95_labels": accepted_labels,
                "crisis_present": "Crisis" in accepted_labels,
            },
            "r6_owner_export": {
                "root": str(R6_ROOT),
                "present": R6_ROOT.exists(),
                "file_count": count_files(R6_ROOT),
            },
            "r5_recency_extension": {
                "root": str(R5_ROOT),
                "present": R5_ROOT.exists(),
                "file_count": count_files(R5_ROOT),
            },
            "source_label_equivalence": {
                "root": str(EQUIV_ROOT),
                "present": EQUIV_ROOT.exists(),
                "file_count": count_files(EQUIV_ROOT),
                "status": "non_target_current_negative_evidence",
            },
        },
        "materialization_assertions": str(MATERIALIZATION_ASSERTIONS),
        "decision": {
            "r3_native_subhour_ready_for_bull_bear_sideways": r3_ready,
            "active_root_labels_missing_after_r3": missing_active_roots,
            "r6_source_control_evidence_acquired": False,
            "r5_recency_evidence_acquired": False,
            "canonical_merge": False,
            "downstream_promotion_rerun": False,
            "strict_full_objective": False,
            "trade_usable": False,
            "update_goal": False,
        },
        "next_action": (
            "Do not run canonical/downstream promotion yet. Acquire a source-owned Crisis/native-subhour "
            "class or another per-regime packet for Crisis, and still satisfy R6 owner/export controls "
            "or R5 recency evidence before canonical merge and provider/AutoQuant -> Pre-Bayes/BBN -> "
            "CatBoost/path-ranking -> execution-tree readback."
        ),
    }
    json_path = ARTIFACT_DIR / "current_objective_audit_after_r3_tsie_materialization_v1.json"
    md_path = ARTIFACT_DIR / "current_objective_audit_after_r3_tsie_materialization_v1.md"
    assertions_path = CHECK_DIR / "current_objective_audit_after_r3_tsie_materialization_v1_assertions.out"
    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    md_path.write_text(
        "\n".join(
            [
                "# Current Objective Audit After R3 TSIE Materialization v1",
                "",
                f"Run id: `{RUN_ID}`",
                "",
                f"Gate result: `{result['gate_result']}`",
                "",
                "Readback:",
                f"- R3 native-subhour root present: `{result['source_roots']['r3_native_subhour']['present']}`.",
                f"- R3 rows: `{result['source_roots']['r3_native_subhour']['row_count']}`.",
                f"- R3 accepted mapping-confidence labels: `{', '.join(accepted_labels) if accepted_labels else 'none'}`.",
                f"- R6 owner/export root present: `{result['source_roots']['r6_owner_export']['present']}`.",
                f"- R5 recency root present: `{result['source_roots']['r5_recency_extension']['present']}`.",
                "",
                "Decision:",
                "- Board A improved: R3 native-subhour source labels now exist for Bull, Bear, and Sideways.",
                "- Board A is still not complete: Crisis is absent from the R3 source taxonomy, R6 owner/export controls are absent, R5 recency is absent, canonical merge is false, and downstream promotion did not rerun.",
                "- `update_goal=false`.",
                "",
                "Next:",
                f"- {result['next_action']}",
                "",
            ]
        )
    )
    assertions_path.write_text(
        "\n".join(
            [
                f"gate_result={result['gate_result']}",
                f"r3_native_subhour_ready_for_bull_bear_sideways={str(r3_ready).lower()}",
                f"active_root_labels_missing_after_r3={','.join(missing_active_roots)}",
                "r6_source_control_evidence_acquired=false",
                "r5_recency_evidence_acquired=false",
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
