from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import Any


REPO = Path("/Users/thrill3r/projects-ict-engine/ict-engine")
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs/20260510T234759-corrected-root-train-select-refinement"
CHECKS_DIR = RUN_ROOT / "checks"
BASE_RUN = REPO / "docs/experiments/actionable-regime-confidence/runs/20260510T232844-codex-main-regime-v2-root-probe"
BASE_SCRIPT = BASE_RUN / "tmp-scripts/main_regime_v2_root_probe.py"
BASE_REPORT = BASE_RUN / "root-v2/main_regime_v2_root_calibration_report.json"


def repo_rel(path: Path) -> str:
    return str(path.relative_to(REPO))


def load_base_module():
    spec = importlib.util.spec_from_file_location("main_regime_v2_root_probe", BASE_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {BASE_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def evaluate_rule(module: Any, label: str, rule: Any, train_rows: list[dict[str, Any]], calibration_rows: list[dict[str, Any]], test_rows: list[dict[str, Any]]) -> dict[str, Any]:
    train = module._metric(label, rule.select(train_rows), len(train_rows))
    calibration = module._metric(label, rule.select(calibration_rows), len(calibration_rows))
    test = module._metric(label, rule.select(test_rows), len(test_rows))
    ece = abs(test["precision"] - calibration["precision"]) if calibration["support"] else 1.0
    return {
        "rule": rule.description,
        "train": train,
        "calibration": calibration,
        "test": test,
        "ece": ece,
        "accepted_95": module._passes_gate(calibration, test, ece),
        "blockers": module._blockers(calibration, test, ece),
    }


def train_select_label(module: Any, label: str, rules: list[Any], train_rows: list[dict[str, Any]], calibration_rows: list[dict[str, Any]], test_rows: list[dict[str, Any]]) -> dict[str, Any]:
    candidates = [
        evaluate_rule(module, label, rule, train_rows, calibration_rows, test_rows)
        for rule in rules
    ]
    train_viable = [
        item
        for item in candidates
        if item["train"]["support"] >= 120
        and item["train"]["coverage"] >= 0.03
        and len(item["train"]["validation_instruments"]) >= 2
        and len(item["train"]["validation_market_contexts"]) >= 2
        and len(item["train"]["validation_timeframes"]) >= 2
    ]
    pool = train_viable if train_viable else candidates
    pool.sort(
        key=lambda item: (
            item["train"]["precision_wilson_lcb_95"],
            item["train"]["support"],
            -len(item["rule"]),
        ),
        reverse=True,
    )
    selected = pool[0]
    best_test = max(candidates, key=lambda item: item["test"]["precision_wilson_lcb_95"])
    return {
        "root_class": label,
        "state": "accepted_95" if selected["accepted_95"] else "blocked",
        "selected_candidate": selected,
        "candidate_count": len(candidates),
        "train_viable_candidate_count": len(train_viable),
        "selection_policy": "train_only_rank_by_train_wilson_lcb_then_support; calibration/test are held-out checks",
        "best_test_observed_not_accepted": {
            "rule": best_test["rule"],
            "test_wilson95": best_test["test"]["precision_wilson_lcb_95"],
            "calibration_support": best_test["calibration"]["support"],
            "test_support": best_test["test"]["support"],
            "test_timeframes": best_test["test"]["validation_timeframes"],
            "blockers": best_test["blockers"],
            "note": "Exploratory only; not an acceptance basis because it is test-selected.",
        },
    }


def main() -> int:
    CHECKS_DIR.mkdir(parents=True, exist_ok=True)
    module = load_base_module()
    rows = module._read_rows()
    train_rows = module._split_rows(rows, "train")
    calibration_rows = module._split_rows(rows, "calibration")
    test_rows = module._split_rows(rows, "test")
    thresholds = module._root_thresholds(train_rows)
    for row in rows:
        row["_root_label"] = module._assign_root_label(row, thresholds)
    rules = module._candidate_rules(train_rows)
    reports = [
        train_select_label(module, label, rules, train_rows, calibration_rows, test_rows)
        for label in ["Bull", "Bear", "Sideways", "Crisis"]
    ]
    manipulation = {
        "root_class": "Manipulation",
        "state": "missing_required_inputs",
        "selected_candidate": {
            "rule": "",
            "train": {"support": 0, "precision_wilson_lcb_95": 0.0},
            "calibration": {"support": 0, "precision_wilson_lcb_95": 0.0},
            "test": {
                "support": 0,
                "precision_wilson_lcb_95": 0.0,
                "coverage": 0.0,
                "validation_instruments": [],
                "validation_market_contexts": [],
                "validation_timeframes": [],
            },
            "ece": 1.0,
            "accepted_95": False,
            "blockers": ["missing_required_inputs", "proxy_only_low_confidence"],
        },
        "selection_policy": "fail_closed_required_inputs_missing",
    }
    reports.append(manipulation)
    accepted = [item["root_class"] for item in reports if item["state"] == "accepted_95"]
    missing = [item["root_class"] for item in reports if item["state"] != "accepted_95"]
    packet = {
        "schema_version": "corrected-main-regime-v2-train-select-refinement/v1",
        "loop_id": "20260510T234759+0800-corrected-root-train-select-refinement",
        "run_root": repo_rel(RUN_ROOT),
        "objective": "Rerun corrected MainRegimeV2 root-axis candidates with train-only selection discipline.",
        "source_probe": repo_rel(BASE_REPORT),
        "source_script": repo_rel(BASE_SCRIPT),
        "threshold_policy": {
            **module.ACCEPTANCE_95,
            "thresholds_relaxed": False,
            "blocked_predictor_prefixes": list(module.BLOCKED_PREDICTOR_PREFIXES),
        },
        "root_reports": reports,
        "accepted_root_classes_95": accepted,
        "missing_root_classes_95": missing,
        "decision": {
            "board_state": "accepted_95" if not missing else "blocked",
            "accepted_gate": "main_regime_v2_accepted_95_all_root_classes" if not missing else "none_for_MainRegimeV2",
            "trade_usable": False,
            "blocker": "missing_root_classes_95=" + ",".join(missing),
            "next_action": "Current corrected-root feature set still fails; add higher-signal root inputs or direct manipulation inputs before rerunning unchanged gates.",
        },
    }
    packet_path = RUN_ROOT / "corrected_root_train_select_refinement_packet.json"
    packet_path.write_text(json.dumps(packet, indent=2) + "\n", encoding="utf-8")
    lines = [
        f"accepted_root_classes_95: {accepted}",
        f"missing_root_classes_95: {missing}",
        f"accepted_gate: {packet['decision']['accepted_gate']}",
        "thresholds_relaxed: False",
        "blocked_future_target_predictors: True",
        "trade_usable: False",
    ]
    for item in reports:
        selected = item["selected_candidate"]
        test = selected["test"]
        lines.append(
            f"{item['root_class']}: state={item['state']} "
            f"test_lcb={test['precision_wilson_lcb_95']} "
            f"cal={selected['calibration']['support']} test={test['support']} "
            f"blockers={','.join(selected['blockers'])}"
        )
    (CHECKS_DIR / "corrected_root_train_select_refinement_assertions.out").write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"packet": repo_rel(packet_path), "accepted": accepted, "missing": missing}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
