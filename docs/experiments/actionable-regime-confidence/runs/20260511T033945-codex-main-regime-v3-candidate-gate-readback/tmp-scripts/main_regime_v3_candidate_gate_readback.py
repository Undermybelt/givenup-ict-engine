from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any


REPO = Path("/Users/thrill3r/projects-ict-engine/ict-engine")
RUN_ROOT = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T033945-codex-main-regime-v3-candidate-gate-readback"
)
OUT_DIR = RUN_ROOT / "v3-candidate-gate"
CHECKS_DIR = RUN_ROOT / "checks"

SOURCE_REPORT = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T032456-codex-expanded-root-schema-gate/expanded-root-gate/"
    "expanded_root_schema_gate_report.json"
)
SOURCE_TAXONOMY = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T033340-codex-main-regime-v3-taxonomy-source-refresh/source-refresh/"
    "main_regime_v3_taxonomy_source_refresh.json"
)

LOOP_ID = "20260511T033945+0800-codex-main-regime-v3-candidate-gate-readback"
ROOT_MAP = {
    "BullExpansion": "BullExpansion",
    "BearExpansion": "BearExpansion",
    "SidewaysConsolidation": "SidewaysConsolidation",
    "CrisisStress": "CrisisCrash",
    "Manipulation": "Manipulation",
}
REQUIRED_ROOTS = [
    "BullExpansion",
    "BearExpansion",
    "SidewaysConsolidation",
    "CrisisCrash",
    "Manipulation",
]


def repo_rel(path: Path) -> str:
    return str(path.relative_to(REPO))


def selected_metric(root_report: dict[str, Any]) -> dict[str, Any]:
    candidate = root_report.get("selected_candidate") or {}
    return {
        "rule": candidate.get("rule", "N/A"),
        "method": candidate.get("method", "N/A"),
        "calibration_support": int((candidate.get("calibration") or {}).get("support", 0)),
        "test_support": int((candidate.get("test") or {}).get("support", 0)),
        "calibration_wilson95_lcb": float(
            (candidate.get("calibration") or {}).get("precision_wilson_lcb_95", 0.0)
        ),
        "test_wilson95_lcb": float((candidate.get("test") or {}).get("precision_wilson_lcb_95", 0.0)),
        "calibration_precision": float((candidate.get("calibration") or {}).get("precision", 0.0)),
        "test_precision": float((candidate.get("test") or {}).get("precision", 0.0)),
        "ece": float(candidate.get("ece", 1.0)),
        "blockers": list(candidate.get("blockers") or root_report.get("blockers") or []),
    }


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECKS_DIR.mkdir(parents=True, exist_ok=True)
    source = json.loads(SOURCE_REPORT.read_text())
    taxonomy = json.loads(SOURCE_TAXONOMY.read_text())
    by_root = {item["root_class"]: item for item in source["root_reports"]}

    root_reports: list[dict[str, Any]] = []
    accepted: list[str] = []
    missing: list[str] = []
    for required in REQUIRED_ROOTS:
        source_root = next((old for old, new in ROOT_MAP.items() if new == required), required)
        source_item = by_root.get(source_root)
        if not source_item:
            state = "missing_source_report"
            metric = selected_metric({})
            accepted_95 = False
        else:
            metric = selected_metric(source_item)
            accepted_95 = bool(source_item.get("state") == "accepted_95" or source_item.get("accepted_candidate_count", 0))
            state = "accepted_95" if accepted_95 else source_item.get("state", "blocked")
        if required == "Manipulation":
            accepted_95 = False
            state = "missing_required_inputs"
            metric["blockers"] = ["missing_required_direct_event_order_lifecycle_inputs"]
        if accepted_95:
            accepted.append(required)
        else:
            missing.append(required)
        root_reports.append(
            {
                "root_class": required,
                "source_root_class": source_root,
                "state": state,
                "accepted_95": accepted_95,
                "selected_candidate": metric,
            }
        )

    schema = {
        "schema_id": "MainRegimeV3Candidate",
        "source_taxonomy_refresh": repo_rel(SOURCE_TAXONOMY),
        "source_calibration_report": repo_rel(SOURCE_REPORT),
        "required_roots": REQUIRED_ROOTS,
        "residual_root": "UnknownOrMixed",
        "optional_preflight_roots": taxonomy["preflight_only_optional_roots"],
        "root_map": ROOT_MAP,
        "gate_note": "Readback/crosswalk only; does not relax thresholds or introduce a fresh calibration rerun.",
    }
    crosswalk = {
        "schema_id": "MainRegimeV3CandidateCrosswalk",
        "crosswalk": {
            "BullExpansion": "same source-backed expanded root label",
            "BearExpansion": "same source-backed expanded root label",
            "SidewaysConsolidation": "source labels Consolidation/ConsolidationRange collapsed to SidewaysConsolidation",
            "CrisisCrash": "crosswalk from source root CrisisStress",
            "Manipulation": "direct event/order-lifecycle/L2/L3/MBO/social/on-chain evidence only",
            "UnknownOrMixed": "residual abstain bucket, not release confidence",
        },
    }
    report = {
        "schema_version": "main-regime-v3-candidate-gate-readback/v1",
        "loop_id": LOOP_ID,
        "run_root": repo_rel(RUN_ROOT),
        "objective": "Reissue the latest expanded-root calibration result through the current MainRegimeV3Candidate taxonomy without relaxing thresholds.",
        "source_report": repo_rel(SOURCE_REPORT),
        "source_taxonomy_refresh": repo_rel(SOURCE_TAXONOMY),
        "target_schema": schema,
        "crosswalk": crosswalk,
        "root_reports": root_reports,
        "decision": {
            "board_state": "blocked",
            "accepted_gate": "partial_for_MainRegimeV3Candidate_CrisisCrash_only",
            "accepted_95_all_required_roots": False,
            "accepted_root_classes_95": accepted,
            "missing_root_classes_95": missing,
            "thresholds_relaxed": False,
            "runtime_code_changed": False,
            "fresh_calibration_rerun": False,
            "raw_data_committed": False,
            "trade_usable": False,
            "blocker": "missing_root_classes_95=" + ",".join(missing),
            "next_action": "Run a fresh MainRegimeV3Candidate gate with materially stronger signed expansion/consolidation inputs and a direct Manipulation evidence source.",
        },
    }

    report_path = OUT_DIR / "main_regime_v3_candidate_gate_readback_report.json"
    schema_path = OUT_DIR / "main_regime_v3_candidate_schema.json"
    crosswalk_path = OUT_DIR / "main_regime_v3_candidate_crosswalk.json"
    summary_path = OUT_DIR / "main_regime_v3_candidate_gate_readback_summary.csv"
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    schema_path.write_text(json.dumps(schema, indent=2, sort_keys=True) + "\n")
    crosswalk_path.write_text(json.dumps(crosswalk, indent=2, sort_keys=True) + "\n")
    with summary_path.open("w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "root_class",
                "source_root_class",
                "state",
                "accepted_95",
                "calibration_support",
                "test_support",
                "calibration_wilson95_lcb",
                "test_wilson95_lcb",
                "rule",
            ],
        )
        writer.writeheader()
        for item in root_reports:
            metric = item["selected_candidate"]
            writer.writerow(
                {
                    "root_class": item["root_class"],
                    "source_root_class": item["source_root_class"],
                    "state": item["state"],
                    "accepted_95": item["accepted_95"],
                    "calibration_support": metric["calibration_support"],
                    "test_support": metric["test_support"],
                    "calibration_wilson95_lcb": f"{metric['calibration_wilson95_lcb']:.12f}",
                    "test_wilson95_lcb": f"{metric['test_wilson95_lcb']:.12f}",
                    "rule": metric["rule"],
                }
            )

    assertions = [
        "ok: main_regime_v3_candidate_schema_written",
        "ok: thresholds_relaxed=false",
        "ok: runtime_code_changed=false",
        "ok: raw_data_committed=false",
        "ok: fresh_calibration_rerun=false_readback_only",
        f"ok: accepted_roots={','.join(accepted) if accepted else 'none'}",
        f"ok: missing_roots={','.join(missing) if missing else 'none'}",
    ]
    (CHECKS_DIR / "main_regime_v3_candidate_gate_readback_assertions.out").write_text(
        "\n".join(assertions) + "\n"
    )
    print(json.dumps(report["decision"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
