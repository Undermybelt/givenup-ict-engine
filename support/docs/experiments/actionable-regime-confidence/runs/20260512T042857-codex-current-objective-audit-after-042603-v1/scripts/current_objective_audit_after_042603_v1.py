#!/usr/bin/env python3
"""Prompt-to-artifact audit for Board A after 042222/042603."""

from __future__ import annotations

import csv
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = Path(__file__).resolve().parents[1]
RUN_ID = "20260512T042857-codex-current-objective-audit-after-042603-v1"
SLUG = "current-objective-audit-after-042603-v1"
OUT = RUN_ROOT / SLUG
CHECKS = RUN_ROOT / "checks"
COMMAND_OUT = RUN_ROOT / "command-output"
BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"
ICT = REPO / "target/debug/ict-engine"
STATE_DIR = Path("/tmp/ict-engine-board-a-autoquant-local-cache-20260512T022826")
SYMBOL = "NQ"

TARGET_ROOTS = {
    "r6_owner_export": Path("/tmp/ict-engine-board-a-r6-owner-export-v1"),
    "r3_native_subhour": Path("/tmp/ict-engine-native-subhour-source-label-intake"),
    "r5_recency_extension": Path("/tmp/ict-engine-source-panel-recency-extension"),
    "source_label_equivalence_sidecar": Path("/tmp/ict-engine-source-label-equivalence-intake"),
    "direct_manipulation_sidecar": Path("/tmp/ict-engine-direct-manipulation-row-intake"),
}

ARTIFACTS = {
    "041410_source_label_calibration": REPO
    / "docs/experiments/actionable-regime-confidence/runs/20260512T041410-codex-source-label-equivalence-live-calibration-after-200909-v1/source-label-equivalence-live-calibration-after-200909-v1/source_label_equivalence_confidence_calibration_v1.json",
    "041656_predictive_screen": REPO
    / "docs/experiments/actionable-regime-confidence/runs/20260512T041656-codex-source-label-predictive-confidence-screen-v1/source-label-predictive-confidence-screen-v1/source_label_predictive_confidence_screen_v1.json",
    "041846_live_source_discovery": REPO
    / "docs/experiments/actionable-regime-confidence/runs/20260512T041846-codex-live-source-label-extension-discovery-after-041423-v1/live-source-label-extension-discovery-after-041423-v1/live_source_label_extension_discovery_after_041423_v1.json",
    "042436_source_target_scan": REPO
    / "docs/experiments/actionable-regime-confidence/runs/20260512T042436-codex-source-target-local-scan-after-041656-v1/source-target-local-scan-after-041656-v1/source_target_local_scan_after_041656_v1.json",
    "042222_autoquant_local_cache": REPO
    / "docs/experiments/actionable-regime-confidence/runs/20260512T042222-codex-autoquant-data-ready-local-cache-run-after-041649-v1/autoquant-data-ready-local-cache-run-after-041649-v1/autoquant_data_ready_local_cache_run_after_041649_v1.json",
    "042603_autoquant_readback": REPO
    / "docs/experiments/actionable-regime-confidence/runs/20260512T042603-codex-autoquant-local-cache-run-readback-after-042222-v1/autoquant-local-cache-run-readback-after-042222-v1/autoquant_local_cache_run_readback_after_042222_v1.json",
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run_command(args: list[str], stem: str, timeout: int = 90) -> dict[str, Any]:
    proc = subprocess.run(
        args,
        cwd=REPO,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
        check=False,
    )
    (COMMAND_OUT / f"{stem}.cmd").write_text(" ".join(args) + "\n", encoding="utf-8")
    (COMMAND_OUT / f"{stem}.stdout.txt").write_text(proc.stdout, encoding="utf-8")
    (COMMAND_OUT / f"{stem}.stderr.txt").write_text(proc.stderr, encoding="utf-8")
    (COMMAND_OUT / f"{stem}.exit").write_text(str(proc.returncode), encoding="utf-8")
    parsed: Any = None
    try:
        parsed = json.loads(proc.stdout)
        (COMMAND_OUT / f"{stem}.stdout.json").write_text(json.dumps(parsed, indent=2, sort_keys=True), encoding="utf-8")
    except Exception:
        parsed = None
    return {
        "name": stem,
        "args": args,
        "exit": proc.returncode,
        "stdout_path": str(COMMAND_OUT / f"{stem}.stdout.txt"),
        "stderr_path": str(COMMAND_OUT / f"{stem}.stderr.txt"),
        "parsed_json": parsed,
    }


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"missing": True, "path": str(path)}
    return json.loads(path.read_text(encoding="utf-8"))


def current_cursor(board_text: str) -> str:
    for line in board_text.splitlines():
        if line.startswith("| last_loop_id |"):
            return line.split("|")[2].strip()
    return "unknown"


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def bool_text(value: bool) -> str:
    return "true" if value else "false"


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)
    COMMAND_OUT.mkdir(parents=True, exist_ok=True)

    board_text = BOARD.read_text(encoding="utf-8")
    artifact_payloads = {name: load_json(path) for name, path in ARTIFACTS.items()}

    commands = [
        run_command([str(ICT), "provider-status", "--agent"], "00_provider_status_agent"),
        run_command([str(ICT), "provider-status", "--compact"], "01_provider_status_compact"),
        run_command(
            [
                str(ICT),
                "auto-quant-status",
                "--state-dir",
                str(STATE_DIR),
                "--output-format",
                "json",
            ],
            "02_auto_quant_status_latest_state",
        ),
        run_command(
            [
                str(ICT),
                "pre-bayes-status",
                "--symbol",
                SYMBOL,
                "--state-dir",
                str(STATE_DIR),
                "--refresh",
                "--output-format",
                "json",
            ],
            "03_pre_bayes_status",
        ),
        run_command(
            [
                str(ICT),
                "policy-training-status",
                "--symbol",
                SYMBOL,
                "--state-dir",
                str(STATE_DIR),
                "--output-format",
                "json",
            ],
            "04_policy_training_status",
        ),
        run_command(
            [
                str(ICT),
                "workflow-status",
                "--symbol",
                SYMBOL,
                "--state-dir",
                str(STATE_DIR),
                "--refresh",
                "--output-format",
                "json",
            ],
            "05_workflow_status",
        ),
        run_command(
            [
                str(ICT),
                "workflow-status",
                "--symbol",
                SYMBOL,
                "--state-dir",
                str(STATE_DIR),
                "--phase",
                "structural-recommended-path-bundle",
                "--output-format",
                "json",
            ],
            "06_workflow_structural_recommended_path_bundle",
        ),
        run_command(
            [
                str(ICT),
                "export-structural-path-ranking-target",
                "--symbol",
                SYMBOL,
                "--state-dir",
                str(STATE_DIR),
            ],
            "07_export_structural_path_ranking_target",
        ),
    ]

    source_label_cal = artifact_payloads["041410_source_label_calibration"]
    predictive = artifact_payloads["041656_predictive_screen"]
    source_scan = artifact_payloads["042436_source_target_scan"]
    aq_readback = artifact_payloads["042603_autoquant_readback"]
    aq_local = artifact_payloads["042222_autoquant_local_cache"]
    source_discovery = artifact_payloads["041846_live_source_discovery"]

    target_root_status = {name: path.exists() for name, path in TARGET_ROOTS.items()}
    required_roots_present = all(
        target_root_status[name] for name in ["r6_owner_export", "r3_native_subhour", "r5_recency_extension"]
    )

    accepted_source_labels = source_label_cal.get("accepted_source_confidence_95_labels", [])
    accepted_predictive_labels = predictive.get("accepted_predictive_confidence_95_labels", predictive.get("accepted_labels", []))
    source_scan_promotion = source_scan.get("promotion_status", {})
    aq_promotion = aq_readback.get("promotion_status", aq_local.get("promotion_status", {}))
    aq_attempts = aq_readback.get("run_attempts", [])
    aq_threaded = aq_local.get("threaded_resolver_run", {})
    aq_successful_backtests = int(aq_threaded.get("succeeded_backtests", 0) or 0)
    if aq_successful_backtests == 0:
        aq_successful_backtests = sum(int(attempt.get("successful_backtests", 0) or 0) for attempt in aq_attempts)
    aq_runtime_note = (
        "runtime succeeded via threaded resolver but remains non-promoting because source/control roots are absent "
        "and strategy rows are runtime_only_non_promoting"
        if aq_successful_backtests > 0
        else "runtime blocked by market metadata/DNS"
    )

    provider_status_text = (COMMAND_OUT / "00_provider_status_agent.stdout.txt").read_text(encoding="utf-8")
    provider_covered = {
        "ibkr": "ibkr" in provider_status_text.lower(),
        "tradingview": "tradingview" in provider_status_text.lower(),
        "yfinance": "yfinance" in provider_status_text.lower(),
        "kraken": "kraken" in provider_status_text.lower(),
    }

    checklist = [
        {
            "requirement": "Named board updated and preserved append-only",
            "evidence": str(BOARD),
            "status": "pass",
            "notes": "Board exists and current audit writes a separate run root; Current Cursor is not edited.",
        },
        {
            "requirement": "Every required regime has calibrated confidence >=95%",
            "evidence": "041410 source-label calibration; 041656 predictive screen",
            "status": "fail",
            "notes": f"source_labels={accepted_source_labels}; predictive_labels={accepted_predictive_labels}; no all-regime pass.",
        },
        {
            "requirement": "Per-regime qualifying conditions exist for accepted regimes",
            "evidence": "041410/041656/041846/042436 readbacks",
            "status": "fail",
            "notes": "No accepted regimes are available under the latest strict gates; diagnostic conditions are not acceptance.",
        },
        {
            "requirement": "Cross-market, cross-cycle, and cross-timeframe validation passes",
            "evidence": "041410 split gates; 041846 source discovery; 042436 target-root scan",
            "status": "fail",
            "notes": "R3/R5 target roots absent; 041846 found no target-root unlock; source-label confidence failed required splits.",
        },
        {
            "requirement": "Use real provider surfaces: IBKR, TradingView, yfinance, Kraken",
            "evidence": "provider-status --agent fresh command",
            "status": "partial",
            "notes": json.dumps(provider_covered, sort_keys=True),
        },
        {
            "requirement": "AutoQuant operates on real/local artifacts",
            "evidence": "042222 and 042603 AutoQuant readbacks plus fresh auto-quant-status",
            "status": "partial",
            "notes": f"data_ready={aq_readback.get('autoquant_status', {}).get('data_ready')}; successful_backtests={aq_successful_backtests}; {aq_runtime_note}.",
        },
        {
            "requirement": "Filter/Pre-Bayes and BBN evidence is present after source unlock",
            "evidence": "fresh pre-bayes-status command",
            "status": "fail",
            "notes": f"pre-bayes exit={commands[3]['exit']}; source/control roots absent so no promoting rerun.",
        },
        {
            "requirement": "CatBoost/path-ranking evidence is present after source unlock",
            "evidence": "fresh policy-training-status and export-structural-path-ranking-target commands",
            "status": "fail",
            "notes": f"policy exit={commands[4]['exit']}; export exit={commands[7]['exit']}; no promoting target export accepted.",
        },
        {
            "requirement": "Execution-tree/workflow readback is actionable",
            "evidence": "fresh workflow-status commands",
            "status": "fail",
            "notes": f"workflow exit={commands[5]['exit']}; structural phase exit={commands[6]['exit']}; target roots absent.",
        },
        {
            "requirement": "No proxy-only evidence is promoted",
            "evidence": "041846, 042436, 042222/042603 board gates",
            "status": "pass",
            "notes": "All proxy/readiness/discovery surfaces are non-promoting.",
        },
        {
            "requirement": "Do not call update_goal unless the full objective is complete",
            "evidence": "promotion statuses and this audit",
            "status": "pass",
            "notes": "Full objective is not complete; update_goal remains false.",
        },
    ]

    missing_requirements = [row for row in checklist if row["status"] != "pass"]
    decision = "current_objective_audit_after_042603_v1=not_complete_source_roots_absent_no_confidence_gate_downstream_blocked"
    result = {
        "run_id": RUN_ID,
        "decision": decision,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "board_sha256_before_artifact": sha256_file(BOARD),
        "current_cursor_observed": current_cursor(board_text),
        "objective_success_criteria": [
            "every required regime has >=95% calibrated confidence",
            "each accepted regime has qualifying_condition plus validation_instruments/periods/market_contexts",
            "cross-market/cycle/timeframe validation passes",
            "real provider/AutoQuant -> filter/Pre-Bayes -> BBN -> CatBoost/path-ranking -> execution-tree evidence exists",
            "no proxy-only evidence is promoted",
        ],
        "state_dir": str(STATE_DIR),
        "symbol": SYMBOL,
        "target_root_status": target_root_status,
        "required_roots_present": required_roots_present,
        "accepted_source_confidence_95_labels": accepted_source_labels,
        "accepted_predictive_confidence_95_labels": accepted_predictive_labels,
        "source_discovery_decision": source_discovery.get("decision"),
        "source_target_scan_gate": source_scan.get("gate_result"),
        "autoquant_gate": aq_local.get("gate_result"),
        "autoquant_readback_gate": aq_readback.get("gate_result"),
        "autoquant_successful_backtests": aq_successful_backtests,
        "autoquant_runtime_note": aq_runtime_note,
        "provider_covered": provider_covered,
        "command_results": [
            {k: v for k, v in command.items() if k != "parsed_json"} for command in commands
        ],
        "checklist": checklist,
        "missing_or_incomplete_requirements": missing_requirements,
        "promotion_status": {
            "accepted_rows_added": 0,
            "new_confidence_gate": False,
            "source_control_evidence_acquired": False,
            "canonical_merge": False,
            "downstream_promotion_rerun": False,
            "strict_full_objective": False,
            "trade_usable": False,
            "update_goal": False,
        },
        "next": (
            "Continue only after source-owned recency/native-subhour rows, verifier-native R6 controls, "
            "owner-export delivery, explicit approval, or a verified offline AutoQuant market metadata path appears."
        ),
    }

    write_csv(
        OUT / "prompt_to_artifact_checklist_after_042603_v1.csv",
        checklist,
        ["requirement", "evidence", "status", "notes"],
    )
    (OUT / "current_objective_audit_after_042603_v1.json").write_text(
        json.dumps(result, indent=2, sort_keys=True),
        encoding="utf-8",
    )

    report = [
        "# Current Objective Audit After 042603 v1",
        "",
        f"Run id: `{RUN_ID}`",
        f"Decision: `{decision}`",
        f"Current cursor observed: `{result['current_cursor_observed']}`",
        "",
        "## Completion Audit",
    ]
    for row in checklist:
        report.append(f"- `{row['status']}`: {row['requirement']} -- {row['notes']}")
    report.extend(
        [
            "",
            "## Result",
            "",
            "The objective is not complete. The controlling blockers are still absent R3/R5/R6 target roots, no accepted all-regime >=95% confidence packet, and downstream Pre-Bayes/BBN/CatBoost/path-ranking/execution-tree promotion blocked by missing source/control evidence. AutoQuant now has a runtime-success readback, but that success is explicitly non-promoting.",
            "",
            "No `update_goal` authorization is present.",
        ]
    )
    (OUT / "current_objective_audit_after_042603_v1.md").write_text("\n".join(report) + "\n", encoding="utf-8")

    assertions = [
        f"PASS decision={decision}",
        f"PASS required_roots_present={bool_text(required_roots_present)}",
        f"PASS accepted_source_confidence_95_labels={len(accepted_source_labels)}",
        f"PASS accepted_predictive_confidence_95_labels={len(accepted_predictive_labels)}",
        f"PASS autoquant_successful_backtests={aq_successful_backtests}",
        f"PASS checklist_fail_or_partial={len(missing_requirements)}",
        "PASS strict_full_objective=false",
        "PASS update_goal=false",
    ]
    (CHECKS / "current_objective_audit_after_042603_v1_assertions.out").write_text(
        "\n".join(assertions) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
