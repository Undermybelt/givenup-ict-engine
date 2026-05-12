#!/usr/bin/env python3
import csv
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


RUN_ID = "20260512T032349-codex-current-objective-audit-after-031655-source-label-readback-v1"
REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs" / RUN_ID
OUT = RUN_ROOT / "current-objective-audit-after-031655-source-label-readback-v1"
CHECKS = RUN_ROOT / "checks"
BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"

PATHS = {
    "audit_031655": REPO / "docs/experiments/actionable-regime-confidence/runs/20260512T031655-codex-current-objective-completion-audit-after-031435-v1/current-objective-completion-audit-after-031435-v1/current_objective_completion_audit_after_031435_v1.json",
    "source_label_calibration_011954": REPO / "docs/experiments/actionable-regime-confidence/runs/20260512T011954-codex-source-label-equivalence-arrival-calibration-v1/source-label-equivalence-arrival-calibration/source_label_equivalence_arrival_calibration_v1.json",
    "source_label_failclosed_012425": REPO / "docs/experiments/actionable-regime-confidence/runs/20260512T012425-codex-source-label-qualifying-condition-failclosed-v1/source-label-qualifying-condition-failclosed-v1/source_label_qualifying_condition_failclosed_v1.json",
    "source_label_cross_timeframe_013042": REPO / "docs/experiments/actionable-regime-confidence/runs/20260512T013042-codex-source-label-cross-timeframe-public-source-screen-v1/source-label-cross-timeframe-public-source-screen-v1/source_label_cross_timeframe_public_source_screen_v1.json",
    "readonly_runtime_chain_013533": REPO / "docs/experiments/actionable-regime-confidence/runs/20260512T013533-codex-readonly-runtime-chain-refresh-after-013042-v1/readonly-runtime-chain-refresh-after-013042-v1/readonly_runtime_chain_refresh_after_013042_v1.json",
    "approval_package": Path("/private/tmp/r6_oystacher_approval_decision_package_v1.json.valid"),
    "source_label_rows": Path("/tmp/ict-engine-source-label-equivalence-intake/source_label_equivalence_rows.csv"),
    "source_label_provenance": Path("/tmp/ict-engine-source-label-equivalence-intake/source_label_equivalence_provenance.json"),
}

ROOTS = {
    "r6_owner_export_root": Path("/tmp/ict-engine-board-a-r6-owner-export-v1"),
    "r3_native_subhour_source_label_root": Path("/tmp/ict-engine-native-subhour-source-label-intake"),
    "r5_source_panel_recency_extension_root": Path("/tmp/ict-engine-source-panel-recency-extension"),
    "source_label_equivalence_sidecar": Path("/tmp/ict-engine-source-label-equivalence-intake"),
    "legacy_direct_manipulation_sidecar": Path("/tmp/ict-engine-direct-manipulation-row-intake"),
}


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def file_summary(path):
    if not path.exists():
        return {"path": str(path), "exists": False}
    item = {
        "path": str(path),
        "exists": True,
        "sha256": sha256(path),
        "bytes": path.stat().st_size,
    }
    if path.suffix == ".csv":
        with path.open("r", encoding="utf-8", newline="") as f:
            item["line_count_including_header"] = sum(1 for _ in f)
    return item


def source_label_counts(path):
    if not path.exists():
        return {}
    counters = {
        "labels": Counter(),
        "families": Counter(),
        "timeframes": Counter(),
        "splits": Counter(),
        "owners": Counter(),
        "species": Counter(),
    }
    rows = 0
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows += 1
            counters["labels"][row.get("main_regime_v2_label", "")] += 1
            counters["families"][row.get("market_family", "")] += 1
            counters["timeframes"][row.get("timeframe", "")] += 1
            counters["splits"][row.get("split_role", "")] += 1
            counters["owners"][row.get("source_owner", "")] += 1
            counters["species"][row.get("event_species", "")] += 1
    return {"rows": rows, **{k: dict(v.most_common()) for k, v in counters.items()}}


def root_status():
    rows = []
    for root_id, root in ROOTS.items():
        files = []
        if root.exists() and root.is_dir():
            files = sorted(p.name for p in root.iterdir() if p.is_file())
        rows.append({
            "root_id": root_id,
            "path": str(root),
            "exists": root.exists(),
            "file_count": len(files),
            "files": files,
            "promotion_use": "blocked" if root_id.startswith(("r6_", "r3_", "r5_")) else "non_promoting_sidecar",
        })
    return rows


def status(condition):
    return "pass" if condition else "blocked"


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)

    evidence = {
        key: read_json(path)
        for key, path in PATHS.items()
        if path.exists() and (path.suffix == ".json" or key == "approval_package")
    }
    audit_031655 = evidence["audit_031655"]
    source_cal = evidence["source_label_calibration_011954"]
    failclosed = evidence["source_label_failclosed_012425"]
    cross_tf = evidence["source_label_cross_timeframe_013042"]
    runtime = evidence["readonly_runtime_chain_013533"]
    approval = evidence["approval_package"]

    roots = root_status()
    roots_by_id = {r["root_id"]: r for r in roots}
    source_counts = source_label_counts(PATHS["source_label_rows"])

    accepted_source_labels = source_cal.get("accepted_source_confidence_95_labels", [])
    accepted_condition_labels = failclosed.get("accepted_labels", [])
    field_complete_labels = failclosed.get("field_complete_labels", [])
    ready_cross_tf = cross_tf.get("ready_public_cross_timeframe_source_label_exports_found", 0)

    checklist = [
        {
            "requirement": "named_board_file_preserved",
            "status": "pass" if BOARD.exists() else "blocked",
            "evidence": str(BOARD.relative_to(REPO)),
            "gap": "",
        },
        {
            "requirement": "every_active_regime_calibrated_95_confidence",
            "status": status(len(accepted_source_labels) >= 4),
            "evidence": f"accepted_source_confidence_95_labels={accepted_source_labels}; source_label_decision={source_cal.get('decision')}",
            "gap": "No source-label regime has Wilson95/source-confidence acceptance at 0.95.",
        },
        {
            "requirement": "per_regime_qualifying_conditions",
            "status": status(len(accepted_condition_labels) >= 4),
            "evidence": f"field_complete_labels={field_complete_labels}; accepted_labels={accepted_condition_labels}",
            "gap": "Bull/Sideways are field-complete leads only; Bear/Crisis are not accepted.",
        },
        {
            "requirement": "cross_market_cycle_timeframe_validation",
            "status": status(ready_cross_tf > 0),
            "evidence": f"ready_public_cross_timeframe_source_label_exports_found={ready_cross_tf}; current_timeframes={source_counts.get('timeframes', {})}",
            "gap": "Current source-label equivalence sidecar is daily-only; no ready source-owned cross-timeframe export was found.",
        },
        {
            "requirement": "r6_owner_export_or_explicit_flip_approval",
            "status": status(roots_by_id["r6_owner_export_root"]["exists"] and approval["assertions"]["approval_present"]),
            "evidence": f"r6_owner_export_root_exists={roots_by_id['r6_owner_export_root']['exists']}; approval_present={approval['assertions']['approval_present']}; flip_controls={approval['assertions']['flip_controls_accepted_under_current_contract']}",
            "gap": "R6 owner-export root is absent and approval package remains non-approving.",
        },
        {
            "requirement": "r3_native_subhour_source_labels",
            "status": status(roots_by_id["r3_native_subhour_source_label_root"]["exists"]),
            "evidence": f"r3_native_subhour_source_label_root_exists={roots_by_id['r3_native_subhour_source_label_root']['exists']}",
            "gap": "Native sub-hour source-label root is absent.",
        },
        {
            "requirement": "r5_source_panel_recency_extension",
            "status": status(roots_by_id["r5_source_panel_recency_extension_root"]["exists"]),
            "evidence": f"r5_source_panel_recency_extension_root_exists={roots_by_id['r5_source_panel_recency_extension_root']['exists']}",
            "gap": "R5 source-panel recency-extension root is absent.",
        },
        {
            "requirement": "provider_autoquant_filter_prebayes_bbn_catboost_execution_tree_chain",
            "status": "blocked",
            "evidence": f"readonly_runtime_gate={runtime.get('gate_result')}; downstream_promotion_rerun_allowed={audit_031655['promotion']['downstream_promotion_rerun_allowed']}",
            "gap": "Read-only runtime surfaces were callable, but promotion rerun remains disallowed until source/control gates pass.",
        },
        {
            "requirement": "canonical_merge_allowed",
            "status": status(audit_031655["promotion"]["canonical_merge_allowed"]),
            "evidence": f"canonical_merge_allowed={audit_031655['promotion']['canonical_merge_allowed']}",
            "gap": "Canonical merge remains false.",
        },
        {
            "requirement": "strict_full_objective",
            "status": status(audit_031655["promotion"]["strict_full_objective_achieved"]),
            "evidence": f"strict_full_objective_achieved={audit_031655['promotion']['strict_full_objective_achieved']}; update_goal={audit_031655['promotion']['update_goal']}",
            "gap": "Objective is not complete; update_goal must remain false.",
        },
    ]

    counts = Counter(row["status"] for row in checklist)
    gate = "current_objective_audit_after_031655_source_label_readback_v1=not_complete_source_label_r6_r3_r5_downstream_blocked"
    result = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "gate_result": gate,
        "objective": "Every active regime reaches calibrated >=95% confidence with per-regime conditions and cross-market/cycle/timeframe validation, then provider/Auto-Quant/filter/Pre-Bayes/BBN/CatBoost/execution-tree promotion reruns after source/control gates pass.",
        "inputs": {key: str(path.relative_to(REPO)) if str(path).startswith(str(REPO)) else str(path) for key, path in PATHS.items()},
        "checklist_counts": dict(counts),
        "latest_current_audit_gate": audit_031655.get("gate_result"),
        "source_label_calibration_decision": source_cal.get("decision"),
        "source_label_accepted_95_labels": accepted_source_labels,
        "source_label_field_complete_labels": field_complete_labels,
        "source_label_accepted_condition_labels": accepted_condition_labels,
        "cross_timeframe_ready_exports": ready_cross_tf,
        "source_label_sidecar": {
            "rows": file_summary(PATHS["source_label_rows"]),
            "provenance": file_summary(PATHS["source_label_provenance"]),
            "counts": source_counts,
        },
        "root_status": roots,
        "approval_readback": {
            "approval_present": approval["assertions"]["approval_present"],
            "flip_controls_accepted_under_current_contract": approval["assertions"]["flip_controls_accepted_under_current_contract"],
            "canonical_merge_allowed_now": approval["assertions"]["canonical_merge_allowed_now"],
            "downstream_rerun_allowed_now": approval["assertions"]["downstream_rerun_allowed_now"],
        },
        "promotion": {
            "accepted_rows_added": 0,
            "new_confidence_gate": False,
            "canonical_merge_allowed": False,
            "downstream_promotion_rerun_allowed": False,
            "strict_full_objective_achieved": False,
            "trade_usable": False,
            "update_goal": False,
        },
        "non_mutations": {
            "runtime_code_changed": False,
            "shared_intake_mutated": False,
            "r3_r5_r6_roots_mutated": False,
            "thresholds_relaxed": False,
            "raw_data_committed": False,
        },
        "next_action": "Continue only from owner/operator R6 export delivery, explicit FLIP approval, or genuinely source-owned cross-timeframe MainRegimeV2 exports before canonical merge and downstream promotion.",
    }

    json_path = OUT / "current_objective_audit_after_031655_source_label_readback_v1.json"
    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    checklist_path = OUT / "current_objective_prompt_to_artifact_checklist_after_031655_source_label_readback_v1.csv"
    with checklist_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["requirement", "status", "evidence", "gap"])
        writer.writeheader()
        writer.writerows(checklist)

    root_path = OUT / "current_objective_root_status_after_031655_source_label_readback_v1.csv"
    with root_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["root_id", "path", "exists", "file_count", "promotion_use", "files"])
        writer.writeheader()
        for row in roots:
            out = dict(row)
            out["files"] = ";".join(row["files"])
            writer.writerow(out)

    source_counts_path = OUT / "current_objective_source_label_counts_after_031655_v1.csv"
    with source_counts_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["axis", "key", "count"])
        writer.writeheader()
        for axis, values in source_counts.items():
            if axis == "rows":
                writer.writerow({"axis": "rows", "key": "total", "count": values})
            else:
                for key, count in values.items():
                    writer.writerow({"axis": axis, "key": key, "count": count})

    md = [
        "# Current Objective Audit After 031655 Source-Label Readback v1",
        "",
        f"Run id: `{RUN_ID}`",
        "",
        f"Gate result: `{gate}`",
        "",
        "## Objective Restatement",
        "",
        result["objective"],
        "",
        "## Evidence Read",
        "",
        f"- Latest current-objective audit: `{audit_031655.get('gate_result')}`.",
        f"- Source-label calibration: `{source_cal.get('decision')}` with accepted 95 labels `{accepted_source_labels}`.",
        f"- Qualifying-condition fail-closed readback: `{failclosed.get('decision')}` with field-complete labels `{field_complete_labels}` and accepted labels `{accepted_condition_labels}`.",
        f"- Cross-timeframe source screen: `{cross_tf.get('decision')}` with ready exports `{ready_cross_tf}`.",
        f"- Read-only runtime chain: `{runtime.get('gate_result')}`; downstream promotion rerun remains false.",
        f"- Source-label sidecar rows: `{source_counts.get('rows', 0)}`; timeframes `{source_counts.get('timeframes', {})}`.",
        "",
        "## Checklist",
        "",
        "| Requirement | Status | Evidence | Gap |",
        "|---|---|---|---|",
    ]
    for row in checklist:
        md.append(f"| `{row['requirement']}` | `{row['status']}` | {row['evidence']} | {row['gap']} |")
    md.extend([
        "",
        "## Decision",
        "",
        "- Strict full objective achieved: `false`",
        "- Accepted rows added: `0`",
        "- New confidence gate: `false`",
        "- Canonical merge allowed: `false`",
        "- Downstream promotion rerun allowed: `false`",
        "- Trade usable: `false`",
        "- `update_goal=false`",
        "",
        "## Next",
        "",
        result["next_action"],
        "",
        "## Artifacts",
        "",
        f"- JSON: `{json_path.relative_to(REPO)}`",
        f"- Checklist CSV: `{checklist_path.relative_to(REPO)}`",
        f"- Root-status CSV: `{root_path.relative_to(REPO)}`",
        f"- Source-label count CSV: `{source_counts_path.relative_to(REPO)}`",
    ])
    md_path = OUT / "current_objective_audit_after_031655_source_label_readback_v1.md"
    md_path.write_text("\n".join(md) + "\n", encoding="utf-8")

    assertions = [
        ("gate_result_not_complete", result["gate_result"] == gate),
        ("latest_audit_031655_not_complete", audit_031655.get("decision") == "not_complete"),
        ("source_label_accepted_95_labels_empty", accepted_source_labels == []),
        ("source_label_accepted_condition_labels_empty", accepted_condition_labels == []),
        ("cross_timeframe_ready_exports_zero", ready_cross_tf == 0),
        ("source_label_timeframe_daily_only", source_counts.get("timeframes", {}) == {"1d": source_counts.get("rows", 0)}),
        ("r6_owner_export_root_absent", roots_by_id["r6_owner_export_root"]["exists"] is False),
        ("r3_native_subhour_root_absent", roots_by_id["r3_native_subhour_source_label_root"]["exists"] is False),
        ("r5_recency_root_absent", roots_by_id["r5_source_panel_recency_extension_root"]["exists"] is False),
        ("approval_present_false", approval["assertions"]["approval_present"] is False),
        ("flip_controls_false", approval["assertions"]["flip_controls_accepted_under_current_contract"] is False),
        ("canonical_merge_allowed_false", result["promotion"]["canonical_merge_allowed"] is False),
        ("downstream_promotion_rerun_allowed_false", result["promotion"]["downstream_promotion_rerun_allowed"] is False),
        ("strict_full_objective_false", result["promotion"]["strict_full_objective_achieved"] is False),
        ("trade_usable_false", result["promotion"]["trade_usable"] is False),
        ("update_goal_false", result["promotion"]["update_goal"] is False),
        ("runtime_code_changed_false", result["non_mutations"]["runtime_code_changed"] is False),
        ("shared_intake_mutated_false", result["non_mutations"]["shared_intake_mutated"] is False),
        ("thresholds_relaxed_false", result["non_mutations"]["thresholds_relaxed"] is False),
        ("raw_data_committed_false", result["non_mutations"]["raw_data_committed"] is False),
    ]
    failures = []
    lines = []
    for name, ok in assertions:
        lines.append(f"{'PASS' if ok else 'FAIL'} {name}={str(ok).lower()}")
        if not ok:
            failures.append(name)
    assertion_path = CHECKS / "current_objective_audit_after_031655_source_label_readback_v1_assertions.out"
    assertion_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    if failures:
        raise SystemExit("assertions failed: " + ",".join(failures))


if __name__ == "__main__":
    main()
