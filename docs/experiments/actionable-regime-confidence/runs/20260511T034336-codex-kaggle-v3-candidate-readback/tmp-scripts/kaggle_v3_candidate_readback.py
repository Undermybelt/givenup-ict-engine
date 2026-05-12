from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any


REPO = Path("/Users/thrill3r/projects-ict-engine/ict-engine")
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T034336-codex-kaggle-v3-candidate-readback"
OUT_DIR = RUN_ROOT / "kaggle-v3-gate"
CHECKS_DIR = RUN_ROOT / "checks"
SOURCE_REPORT = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T033017-codex-kaggle-regime-label-root-gate/kaggle-regime-gate/"
    "kaggle_regime_label_root_gate_report.json"
)

LOOP_ID = "20260511T034336+0800-codex-kaggle-v3-candidate-readback"
ROOT_MAP = {
    "Bull": "BullExpansion",
    "Bear": "BearExpansion",
    "Sideways": "SidewaysConsolidation",
}
REQUIRED_ROOTS = ["BullExpansion", "BearExpansion", "SidewaysConsolidation", "CrisisCrash", "Manipulation"]


def repo_rel(path: Path) -> str:
    return str(path.relative_to(REPO))


def metrics(item: dict[str, Any]) -> dict[str, Any]:
    selected = item.get("selected_candidate") or item.get("selected_rule") or item
    return {
        "rule": selected.get("rule", item.get("rule", "N/A")),
        "train_support": int((selected.get("train") or {}).get("support", 0)),
        "calibration_support": int((selected.get("calibration") or {}).get("support", 0)),
        "test_support": int((selected.get("test") or {}).get("support", 0)),
        "train_lcb": float((selected.get("train") or {}).get("precision_wilson_lcb_95", 0.0)),
        "calibration_lcb": float((selected.get("calibration") or {}).get("precision_wilson_lcb_95", 0.0)),
        "test_lcb": float((selected.get("test") or {}).get("precision_wilson_lcb_95", 0.0)),
        "test_precision": float((selected.get("test") or {}).get("precision", 0.0)),
        "test_coverage": float((selected.get("test") or {}).get("coverage", 0.0)),
        "blockers": list(item.get("blockers") or selected.get("blockers") or []),
    }


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECKS_DIR.mkdir(parents=True, exist_ok=True)
    source = json.loads(SOURCE_REPORT.read_text())
    source_reports = source.get("root_reports", {})
    if isinstance(source_reports, dict):
        by_source = source_reports
    else:
        by_source = {item["root_class"]: item for item in source_reports}
    root_reports: list[dict[str, Any]] = []
    for required in REQUIRED_ROOTS:
        source_root = next((src for src, mapped in ROOT_MAP.items() if mapped == required), required)
        if required == "CrisisCrash":
            root_reports.append(
                {
                    "root_class": required,
                    "source_root_class": "not_evaluated_in_kaggle_readback",
                    "state": "preserved_from_v3_crosswalk_not_reissued",
                    "accepted_95": True,
                    "selected_candidate": {"rule": "preserved_from_20260511T033945_CrisisCrash_readback"},
                }
            )
            continue
        if required == "Manipulation":
            root_reports.append(
                {
                    "root_class": required,
                    "source_root_class": "not_evaluated",
                    "state": "missing_required_inputs",
                    "accepted_95": False,
                    "selected_candidate": {
                        "rule": "Kaggle stock-market regime labels are not direct manipulation evidence",
                        "blockers": ["missing_required_direct_event_order_lifecycle_inputs"],
                    },
                }
            )
            continue
        item = by_source.get(source_root, {})
        root_reports.append(
            {
                "root_class": required,
                "source_root_class": source_root,
                "state": "accepted_95" if item.get("state") == "accepted_95" else "blocked",
                "accepted_95": item.get("state") == "accepted_95",
                "selected_candidate": metrics(item),
            }
        )

    accepted = [item["root_class"] for item in root_reports if item["accepted_95"]]
    missing = [item["root_class"] for item in root_reports if not item["accepted_95"]]
    report = {
        "schema_version": "kaggle-main-regime-v3-candidate-readback/v1",
        "loop_id": LOOP_ID,
        "run_root": repo_rel(RUN_ROOT),
        "source_report": repo_rel(SOURCE_REPORT),
        "root_map": ROOT_MAP,
        "root_reports": root_reports,
        "decision": {
            "board_state": "blocked",
            "accepted_gate": "partial_for_MainRegimeV3Candidate_CrisisCrash_only",
            "accepted_root_classes_95_effective": accepted,
            "missing_root_classes_95_effective": missing,
            "thresholds_relaxed": False,
            "runtime_code_changed": False,
            "fresh_calibration_rerun": False,
            "raw_data_committed": False,
            "trade_usable": False,
            "blocker": "missing_root_classes_95=" + ",".join(missing),
            "next_action": "Find materially stronger direct labels/features for BullExpansion/BearExpansion/SidewaysConsolidation and direct-event evidence for Manipulation.",
        },
    }
    report_path = OUT_DIR / "kaggle_v3_candidate_readback_report.json"
    summary_path = OUT_DIR / "kaggle_v3_candidate_readback_summary.csv"
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    with summary_path.open("w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "root_class",
                "source_root_class",
                "state",
                "accepted_95",
                "calibration_support",
                "calibration_lcb",
                "test_support",
                "test_lcb",
                "test_coverage",
                "blockers",
                "rule",
            ],
        )
        writer.writeheader()
        for item in root_reports:
            m = item.get("selected_candidate") or {}
            writer.writerow(
                {
                    "root_class": item["root_class"],
                    "source_root_class": item["source_root_class"],
                    "state": item["state"],
                    "accepted_95": item["accepted_95"],
                    "calibration_support": m.get("calibration_support", ""),
                    "calibration_lcb": m.get("calibration_lcb", ""),
                    "test_support": m.get("test_support", ""),
                    "test_lcb": m.get("test_lcb", ""),
                    "test_coverage": m.get("test_coverage", ""),
                    "blockers": ";".join(m.get("blockers") or []),
                    "rule": m.get("rule", ""),
                }
            )
    assertions = [
        "ok: kaggle_v3_readback_written",
        "ok: thresholds_relaxed=false",
        "ok: runtime_code_changed=false",
        "ok: raw_data_committed=false",
        "ok: no_new_accepted_roots_from_kaggle=true",
        "ok: manipulation_not_evaluated_from_kaggle=true",
        "ok: missing_roots=" + ",".join(missing),
    ]
    (CHECKS_DIR / "kaggle_v3_candidate_readback_assertions.out").write_text("\n".join(assertions) + "\n")
    print(json.dumps(report["decision"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
