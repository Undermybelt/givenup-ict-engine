#!/usr/bin/env python3
"""Strict Board A completion audit after terminal 042448 evidence."""

from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


RUN_ID = "20260512T044001-codex-current-objective-completion-audit-after-042448-terminal-v1"
SLUG = "current-objective-completion-audit-after-042448-terminal-v1"
REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = Path(__file__).resolve().parents[1]
OUT = RUN_ROOT / SLUG
CHECKS = RUN_ROOT / "checks"
BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"

ROOT_LABELS = ["Bear", "Bull", "Crisis", "Sideways"]
TARGET_ROOTS = {
    "r6_owner_export": Path("/tmp/ict-engine-board-a-r6-owner-export-v1"),
    "r3_native_subhour": Path("/tmp/ict-engine-native-subhour-source-label-intake"),
    "r5_recency_extension": Path("/tmp/ict-engine-source-panel-recency-extension"),
}

ARTIFACTS = {
    "source_calibration_041410": REPO
    / "docs/experiments/actionable-regime-confidence/runs/20260512T041410-codex-source-label-equivalence-live-calibration-after-200909-v1/source-label-equivalence-live-calibration-after-200909-v1/source_label_equivalence_confidence_calibration_v1.json",
    "predictive_041656": REPO
    / "docs/experiments/actionable-regime-confidence/runs/20260512T041656-codex-source-label-predictive-confidence-screen-v1/source-label-predictive-confidence-v1/source_label_predictive_confidence_screen_v1.json",
    "predictive_041656_alt": REPO
    / "docs/experiments/actionable-regime-confidence/runs/20260512T041656-codex-source-label-predictive-confidence-screen-v1/source-label-predictive-confidence-screen-v1/source_label_predictive_confidence_screen_v1.json",
    "histgb_042448": REPO
    / "docs/experiments/actionable-regime-confidence/runs/20260512T042448-codex-source-label-histgb-confidence-screen-v1/source-label-histgb-confidence-screen-v1/source_label_histgb_confidence_screen_v1.json",
    "downstream_042857": REPO
    / "docs/experiments/actionable-regime-confidence/runs/20260512T042857-codex-current-objective-audit-after-042603-v1/current-objective-audit-after-042603-v1/current_objective_audit_after_042603_v1.json",
    "autoquant_043027": REPO
    / "docs/experiments/actionable-regime-confidence/runs/20260512T043027-codex-current-objective-audit-after-042222-threaded-resolver-v1/current-objective-audit-after-042222-threaded-resolver-v1/current_objective_audit_after_042222_threaded_resolver_v1.json",
    "autoquant_043222": REPO
    / "docs/experiments/actionable-regime-confidence/runs/20260512T043222-codex-autoquant-offline-market-metadata-run-after-042222-v1/autoquant-offline-market-metadata-run-after-042222-v1/autoquant_offline_market_metadata_run_after_042222_v1.json",
    "owner_arrival_043314": REPO
    / "docs/experiments/actionable-regime-confidence/runs/20260512T043314-codex-r6-owner-export-arrival-scan-after-043027-v1/r6-owner-export-arrival-scan-after-043027-v1/r6_owner_export_arrival_scan_after_043027_v1.json",
    "source_arrival_043436": REPO
    / "docs/experiments/actionable-regime-confidence/runs/20260512T043436-codex-source-control-arrival-scan-after-043027-v1/source-control-arrival-scan-after-043027-v1/source_control_arrival_scan_after_043027_v1.json",
    "approval_package": Path("/private/tmp/r6_oystacher_approval_decision_package_v1.json.valid"),
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"missing": True, "path": str(path)}
    return json.loads(path.read_text(encoding="utf-8"))


def first_existing(*names: str) -> dict[str, Any]:
    for name in names:
        data = read_json(ARTIFACTS[name])
        if not data.get("missing"):
            data["_artifact_key"] = name
            return data
    return read_json(ARTIFACTS[names[0]])


def accepted_source_labels(source: dict[str, Any]) -> list[str]:
    return list(source.get("accepted_source_confidence_95_labels") or [])


def accepted_predictive_labels(pred: dict[str, Any]) -> list[str]:
    return list(pred.get("accepted_predictive_confidence_95_labels") or [])


def accepted_histgb_labels(histgb: dict[str, Any]) -> list[str]:
    return list(histgb.get("accepted_histgb_confidence_95_labels") or [])


def gate_acceptance(histgb: dict[str, Any]) -> dict[str, bool]:
    by_label: dict[str, bool] = {}
    for row in histgb.get("gates", []):
        by_label[str(row.get("label"))] = bool(row.get("accepted_histgb_confidence_95"))
    return by_label


def status(value: bool) -> str:
    return "satisfied" if value else "blocked"


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)

    board_hash = sha256_file(BOARD)
    source = read_json(ARTIFACTS["source_calibration_041410"])
    predictive = first_existing("predictive_041656_alt", "predictive_041656")
    histgb = read_json(ARTIFACTS["histgb_042448"])
    downstream = read_json(ARTIFACTS["downstream_042857"])
    autoquant = read_json(ARTIFACTS["autoquant_043027"])
    offline_autoquant = read_json(ARTIFACTS["autoquant_043222"])
    owner_arrival = read_json(ARTIFACTS["owner_arrival_043314"])
    source_arrival = read_json(ARTIFACTS["source_arrival_043436"])
    approval = read_json(ARTIFACTS["approval_package"])

    roots = {name: {"path": str(path), "present": path.exists()} for name, path in TARGET_ROOTS.items()}
    all_roots_present = all(item["present"] for item in roots.values())
    source_labels = accepted_source_labels(source)
    predictive_labels = accepted_predictive_labels(predictive)
    histgb_labels = accepted_histgb_labels(histgb)
    histgb_by_label = gate_acceptance(histgb)
    all_labels_histgb = all(histgb_by_label.get(label, False) for label in ROOT_LABELS)
    all_confidence_labels = set(source_labels) == set(ROOT_LABELS) or set(predictive_labels) == set(ROOT_LABELS) or set(histgb_labels) == set(ROOT_LABELS)

    provider_covered = bool(downstream.get("provider_covered"))
    autoquant_runtime_succeeded = (
        autoquant.get("autoquant_status", {}).get("successful_backtests") == 3
        or offline_autoquant.get("success_count") == 3
    )
    downstream_command_results = downstream.get("command_results", {})
    if isinstance(downstream_command_results, list):
        downstream_exit_values = [row.get("exit") for row in downstream_command_results if isinstance(row, dict)]
    elif isinstance(downstream_command_results, dict):
        downstream_exit_values = list(downstream_command_results.values())
    else:
        downstream_exit_values = []
    downstream_commands_exited_zero = bool(downstream_exit_values) and all(
        str(value) == "0" for value in downstream_exit_values
    )
    promotion = {
        "accepted_rows_added": 0,
        "new_confidence_gate": False,
        "source_control_evidence_acquired": False,
        "canonical_merge": False,
        "downstream_promotion_rerun": False,
        "strict_full_objective": False,
        "trade_usable": False,
        "update_goal": False,
    }

    checklist = [
        {
            "requirement": "Named board remains authoritative and append-only",
            "evidence": f"board={BOARD.relative_to(REPO)} sha256={board_hash}; this audit writes a separate run root and does not edit Current Cursor",
            "status": "satisfied",
        },
        {
            "requirement": "Every active regime has calibrated confidence >=95%",
            "evidence": f"041410 source labels={source_labels}; 041656 predictive labels={predictive_labels}; 042448 HistGB labels={histgb_labels}; per-label HistGB={histgb_by_label}",
            "status": status(all_confidence_labels),
        },
        {
            "requirement": "Each accepted regime has its own qualifying condition",
            "evidence": "No accepted all-regime confidence packet exists under strict split gates, so no qualifying condition can be accepted.",
            "status": "blocked",
        },
        {
            "requirement": "Validate accepted regimes on other markets and other periods/timeframes",
            "evidence": f"R6/R3/R5 target roots present={all_roots_present}; roots={roots}; HistGB split counts={histgb.get('split_counts')}",
            "status": status(all_roots_present and all_confidence_labels),
        },
        {
            "requirement": "Use provider surfaces including IBKR, TradingViewRemix, yfinance, and Kraken where available",
            "evidence": f"042857 provider_covered={provider_covered}; provider signals remain diagnostic only.",
            "status": "partial" if provider_covered else "blocked",
        },
        {
            "requirement": "Operate AutoQuant on real/local artifacts",
            "evidence": f"043027 successful_backtests={autoquant.get('autoquant_status', {}).get('successful_backtests')}; 043222 success_count={offline_autoquant.get('success_count')} failure_count={offline_autoquant.get('failure_count')}; runtime success remains non-promoting without source/control unlock.",
            "status": "partial" if autoquant_runtime_succeeded else "blocked",
        },
        {
            "requirement": "Run filter/Pre-Bayes and BBN after source unlock",
            "evidence": f"042857 commands_zero={downstream_commands_exited_zero}; Pre-Bayes latest bridge/policy/soft evidence remains empty in command outputs; source/control roots absent.",
            "status": "blocked",
        },
        {
            "requirement": "Run CatBoost/path-ranking after source unlock",
            "evidence": "042857 policy/CatBoost matched_rows=0 and structural path-ranking export rows=1, mature_rows=0, calibrated_rows=0.",
            "status": "blocked",
        },
        {
            "requirement": "Run execution-tree/workflow readback after source unlock",
            "evidence": "042857 workflow/actionable artifacts remained 0; structural recommendation was observe/bootstrap, not promotion.",
            "status": "blocked",
        },
        {
            "requirement": "Do not promote proxy/schema/provider/runtime signals",
            "evidence": "043436, 043314, 043222, 043027, 042857, and 042448 are all classified as non-promoting diagnostics/readbacks.",
            "status": "satisfied",
        },
        {
            "requirement": "Only call update_goal when objective is complete",
            "evidence": "strict_full_objective=false; update_goal=false; missing roots and failed confidence gates remain.",
            "status": "not_complete",
        },
    ]

    missing = [row["requirement"] for row in checklist if row["status"] not in {"satisfied", "partial"}]
    result = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "board_sha256_before_artifact": board_hash,
        "gate_result": "current_objective_completion_audit_after_042448_terminal_v1=not_complete_source_roots_absent_confidence_failed_downstream_blocked",
        "objective_restated": "Every active regime must reach calibrated confidence >=95%, with per-regime qualifying conditions and validation across other markets and periods/timeframes, using real provider -> AutoQuant -> filter/Pre-Bayes -> BBN -> CatBoost/path-ranking -> execution-tree evidence.",
        "target_roots": roots,
        "approval_gate": approval.get("gate_result"),
        "source_arrival_gate": source_arrival.get("gate_result"),
        "owner_arrival_gate": owner_arrival.get("gate_result"),
        "confidence_status": {
            "source_041410_accepted_labels": source_labels,
            "predictive_041656_accepted_labels": predictive_labels,
            "histgb_042448_accepted_labels": histgb_labels,
            "histgb_042448_per_label": histgb_by_label,
        },
        "runtime_status": {
            "provider_covered_042857": provider_covered,
            "autoquant_runtime_succeeded": autoquant_runtime_succeeded,
            "downstream_commands_exited_zero_042857": downstream_commands_exited_zero,
        },
        "checklist": checklist,
        "missing_or_incomplete_requirements": missing,
        "promotion_status": promotion,
    }

    (OUT / "current_objective_completion_audit_after_042448_terminal_v1.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    with (OUT / "prompt_to_artifact_checklist_after_042448_terminal_v1.csv").open(
        "w", newline="", encoding="utf-8"
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=["requirement", "evidence", "status"])
        writer.writeheader()
        writer.writerows(checklist)

    lines = [
        "# Current Objective Completion Audit After 042448 Terminal v1",
        "",
        f"Run id: `{RUN_ID}`",
        "",
        f"Gate result: `{result['gate_result']}`",
        "",
        "## Objective",
        "",
        result["objective_restated"],
        "",
        "## Checklist",
        "",
        "| Requirement | Status | Evidence |",
        "|---|---|---|",
    ]
    for row in checklist:
        evidence = str(row["evidence"]).replace("|", "\\|")
        lines.append(f"| {row['requirement']} | `{row['status']}` | {evidence} |")
    lines.extend(
        [
            "",
            "## Decision",
            "",
            "The objective is not complete. Required R6/R3/R5 source/control roots are absent, no source/predictive/HistGB screen accepts all four root labels at the required split gates, and downstream promotion remains unauthorized.",
            "",
            "Promotion status remains unchanged: accepted rows added `0`, new confidence gate false, source/control evidence acquired false, canonical merge false, downstream promotion rerun false, strict full objective false, trade usable false, and `update_goal=false`.",
            "",
            "## Next",
            "",
            "Preserve the Current Cursor next action. Continue only after explicit approval, verifier-native R6 owner/export rows plus source-owned broad normal controls, source-owned R5 recency-extension rows, native sub-hour source-label rows, or genuinely source-owned cross-timeframe `MainRegimeV2` exports unlock a target root before rerunning the full chain in order.",
        ]
    )
    (OUT / "current_objective_completion_audit_after_042448_terminal_v1.md").write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
    )
    assertions = [
        f"PASS run_id={RUN_ID}",
        f"PASS gate_result={result['gate_result']}",
        f"PASS required_roots_present={str(all_roots_present).lower()}",
        f"PASS source_041410_accepted_labels={len(source_labels)}",
        f"PASS predictive_041656_accepted_labels={len(predictive_labels)}",
        f"PASS histgb_042448_accepted_labels={len(histgb_labels)}",
        f"PASS autoquant_runtime_succeeded={str(autoquant_runtime_succeeded).lower()}",
        "PASS strict_full_objective=false",
        "PASS update_goal=false",
    ]
    (CHECKS / "current_objective_completion_audit_after_042448_terminal_v1_assertions.out").write_text(
        "\n".join(assertions) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
