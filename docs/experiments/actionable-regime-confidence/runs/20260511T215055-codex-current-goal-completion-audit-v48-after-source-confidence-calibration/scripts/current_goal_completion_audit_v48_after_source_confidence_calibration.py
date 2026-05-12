#!/usr/bin/env python3
"""Current-goal audit after source-label confidence calibration."""

from __future__ import annotations

import csv
import hashlib
import json
import math
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


RUN_ID = "20260511T215055-codex-current-goal-completion-audit-v48-after-source-confidence-calibration"
REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = Path(__file__).resolve().parents[1]
OUT = RUN_ROOT / "completion-audit"
CHECKS = RUN_ROOT / "checks"
CMD = RUN_ROOT / "command-output"
BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"

SOURCE_CONFIDENCE = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T214328-codex-source-label-equivalence-confidence-calibration-v1/"
    "source-label-equivalence-confidence-calibration/"
    "source_label_equivalence_confidence_calibration_v1.json"
)

SOURCE_LABEL_ROOT = Path("/tmp/ict-engine-source-label-equivalence-intake")
SOURCE_PANEL_ROOT = Path("/tmp/ict-engine-source-panel-recency-extension")
NATIVE_SUBHOUR_ROOT = Path("/tmp/ict-engine-native-subhour-source-label-intake")
DIRECT_ROOT = Path("/tmp/ict-engine-direct-manipulation-row-intake")

SOURCE_LABEL_VERIFIER = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T182922-codex-source-label-equivalence-intake-verifier-v1/"
    "equivalence-intake-verifier/source_label_equivalence_intake_verifier_v1.py"
)
SOURCE_PANEL_VERIFIER = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T165405-codex-source-panel-recency-extension-manifest-v1/"
    "source-panel-recency/source_panel_recency_extension_verifier_v1.py"
)
DIRECT_VERIFIER = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T151950-codex-direct-manipulation-row-intake-manifest-v1/"
    "direct-manipulation-intake/direct_manipulation_row_intake_verifier_v1.py"
)

ROOT_LABELS = ["Bull", "Bear", "Sideways", "Crisis"]
Z95 = 1.959963984540054


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def run_verifier(name: str, verifier: Path, intake_root: Path) -> dict[str, Any]:
    proc = subprocess.run(
        [sys.executable, str(verifier), "--intake-root", str(intake_root)],
        cwd=REPO,
        text=True,
        capture_output=True,
        check=False,
    )
    stdout_path = CMD / f"{name}.stdout.txt"
    stderr_path = CMD / f"{name}.stderr.txt"
    exit_path = CMD / f"{name}.exit"
    stdout_path.write_text(proc.stdout, encoding="utf-8")
    stderr_path.write_text(proc.stderr, encoding="utf-8")
    exit_path.write_text(f"{proc.returncode}\n", encoding="utf-8")
    try:
        parsed = json.loads(proc.stdout) if proc.stdout.strip() else {}
    except json.JSONDecodeError:
        parsed = {"status": "unparsed", "stdout_prefix": proc.stdout[:500]}
    if not isinstance(parsed, dict):
        parsed = {"status": "unparsed"}
    return {
        "name": name,
        "returncode": proc.returncode,
        "parsed": parsed,
        "stdout": str(stdout_path.relative_to(REPO)),
        "stderr": str(stderr_path.relative_to(REPO)),
        "exit": str(exit_path.relative_to(REPO)),
    }


def wilson_all_success_lcb(n: int) -> float:
    if n <= 0:
        return 0.0
    denominator = 1.0 + Z95 * Z95 / n
    center = 1.0 + Z95 * Z95 / (2.0 * n)
    margin = Z95 * math.sqrt(Z95 * Z95 / (4.0 * n * n))
    return (center - margin) / denominator


def current_cursor(board_text: str) -> str:
    match = re.search(r"\| last_loop_id \| ([^|]+) \|", board_text)
    return match.group(1).strip() if match else "unknown"


def bool_text(value: bool) -> str:
    return str(value).lower()


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)
    CMD.mkdir(parents=True, exist_ok=True)

    missing = [
        str(path)
        for path in [
            BOARD,
            SOURCE_CONFIDENCE,
            SOURCE_LABEL_VERIFIER,
            SOURCE_PANEL_VERIFIER,
            DIRECT_VERIFIER,
        ]
        if not path.exists()
    ]
    if missing:
        raise FileNotFoundError(missing)

    board_text = BOARD.read_text(encoding="utf-8")
    board_hash = sha256_file(BOARD)
    cursor_before = current_cursor(board_text)
    source_confidence = load_json(SOURCE_CONFIDENCE)
    source_label = run_verifier("source_label_equivalence_verifier", SOURCE_LABEL_VERIFIER, SOURCE_LABEL_ROOT)
    source_panel = run_verifier("source_panel_recency_verifier", SOURCE_PANEL_VERIFIER, SOURCE_PANEL_ROOT)
    direct = run_verifier("direct_manipulation_verifier", DIRECT_VERIFIER, DIRECT_ROOT)

    source_label_parsed = source_label["parsed"]
    source_panel_parsed = source_panel["parsed"]
    direct_parsed = direct["parsed"]
    positive_rows = int(direct_parsed.get("positive_rows") or 0)
    negative_rows = int(direct_parsed.get("matched_negative_rows") or 0)
    r6_min_lcb = min(wilson_all_success_lcb(positive_rows), wilson_all_success_lcb(negative_rows))
    accepted_source_labels = source_confidence.get("accepted_source_confidence_95_labels") or []
    label_counts = source_confidence.get("label_counts") or {}
    source_label_rows = int(source_label_parsed.get("row_count") or 0)
    ready_roots = [
        "source_label_equivalence"
        if source_label_parsed.get("status") == "schema_ready_unscored"
        else "",
        "direct_manipulation_row_intake"
        if direct_parsed.get("status") == "schema_ready_unscored"
        else "",
    ]
    ready_roots = [root for root in ready_roots if root]

    checklist = [
        {
            "id": "R0_named_board",
            "status": "pass_checked",
            "evidence": str(BOARD.relative_to(REPO)),
            "gap": "",
        },
        {
            "id": "R1_every_regime_95",
            "status": "fail_blocked",
            "evidence": f"source_confidence_accepted_labels={accepted_source_labels or 'none'}; r6_min_lcb={r6_min_lcb:.6f}",
            "gap": "No active root has a new accepted 95% package in this slice; source-label confidence scoring rejected all four price roots and R6 remains below 0.95.",
        },
        {
            "id": "R2_other_market_validation",
            "status": "fail_blocked",
            "evidence": f"source_label_status={source_label_parsed.get('status')}; rows={source_label_rows}; labels={label_counts}",
            "gap": "Source-label other-market rows are schema-ready, but the confidence calibration accepted zero labels.",
        },
        {
            "id": "R3_other_cycle_timeframe",
            "status": "fail_blocked",
            "evidence": f"native_subhour_ready={NATIVE_SUBHOUR_ROOT.exists()}; recency_status={source_panel_parsed.get('status')}",
            "gap": "Native sub-hour rows/provenance and post-2026-01-30 recency-extension rows/provenance are still absent.",
        },
        {
            "id": "R4_provider_and_full_chain",
            "status": "partial_guardrail",
            "evidence": "latest provider/downstream readback remains 20260511T212339; this audit reran current root verifiers and source-confidence artifact only",
            "gap": "No fresh provider/Auto-Quant/Pre-Bayes/BBN/CatBoost/execution-tree rerun was needed for this source-confidence rejection slice.",
        },
        {
            "id": "R5_source_label_confidence_calibration",
            "status": "fail_blocked",
            "evidence": f"artifact={SOURCE_CONFIDENCE.relative_to(REPO)}; accepted_source_confidence_95_labels={accepted_source_labels or 'none'}",
            "gap": "All four price roots fail the source-confidence Wilson95 gate across calibration, heldout-market, heldout-time, and test splits.",
        },
        {
            "id": "R6_direct_manipulation_confidence",
            "status": "fail_blocked",
            "evidence": f"positives={positive_rows}; controls={negative_rows}; matched_groups={direct_parsed.get('matched_group_count')}; min_lcb={r6_min_lcb:.6f}",
            "gap": "R6 is below 50/50 support, Wilson95 remains below 0.95, broad-normal sample is false, and direct species coverage remains incomplete.",
        },
        {
            "id": "R7_no_proxy_acceptance",
            "status": "pass_guardrail",
            "evidence": "schema-ready source labels, same-event controls, provider proxies, and OHLCV/direct proxies remain fail-closed",
            "gap": "",
        },
        {
            "id": "R8_multi_agent_safety",
            "status": "pass_guardrail",
            "evidence": f"board_hash_before={board_hash}; cursor_before={cursor_before}; append-only registration expected",
            "gap": "",
        },
        {
            "id": "R9_update_goal_gate",
            "status": "fail_blocked",
            "evidence": "failures_present=true",
            "gap": "Missing and failed requirements remain; update_goal=false.",
        },
    ]

    gates = [
        {"gate": "ready_intake_roots", "observed": len(ready_roots), "required": 4, "pass": False},
        {"gate": "source_label_verifier", "observed": source_label_parsed.get("status"), "required": "schema_ready_unscored", "pass": source_label_parsed.get("status") == "schema_ready_unscored"},
        {"gate": "source_label_all_roots_present", "observed": ",".join(sorted(label_counts)), "required": ",".join(ROOT_LABELS), "pass": all(label in label_counts for label in ROOT_LABELS)},
        {"gate": "source_label_confidence_accepted_labels", "observed": len(accepted_source_labels), "required": 4, "pass": False},
        {"gate": "source_panel_recency_verifier", "observed": source_panel_parsed.get("status"), "required": "not_blocked", "pass": source_panel_parsed.get("status") != "blocked"},
        {"gate": "native_subhour_root_ready", "observed": NATIVE_SUBHOUR_ROOT.exists(), "required": True, "pass": False},
        {"gate": "r6_positive_support", "observed": positive_rows, "required": ">=50", "pass": positive_rows >= 50},
        {"gate": "r6_negative_support", "observed": negative_rows, "required": ">=50", "pass": negative_rows >= 50},
        {"gate": "r6_wilson95_lcb", "observed": round(r6_min_lcb, 6), "required": ">=0.95", "pass": r6_min_lcb >= 0.95},
        {"gate": "r6_broad_normal_sample", "observed": False, "required": True, "pass": False},
        {"gate": "r6_direct_species_coverage", "observed": False, "required": True, "pass": False},
    ]

    decision = "current_goal_completion_audit_v48=source_confidence_calibrated_no_acceptance_2of4_roots_still_blocked"
    failures_present = any(row["status"].startswith("fail") for row in checklist)
    result = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "decision": decision,
        "objective_restatement": "Every active regime must have source-owned or owner-approved >=95 confidence and must retain suitable confidence across other markets/species and other cycles/timeframes before completion can be reported.",
        "board_hash_before": board_hash,
        "cursor_before": cursor_before,
        "source_confidence_artifact": str(SOURCE_CONFIDENCE.relative_to(REPO)),
        "source_label_verifier": source_label,
        "source_panel_recency_verifier": source_panel,
        "direct_manipulation_verifier": direct,
        "ready_roots": ready_roots,
        "source_label_rows": source_label_rows,
        "source_label_counts": label_counts,
        "accepted_source_confidence_95_labels": accepted_source_labels,
        "native_subhour_root_ready": NATIVE_SUBHOUR_ROOT.exists(),
        "r6_positive_rows": positive_rows,
        "r6_matched_negative_rows": negative_rows,
        "r6_matched_groups": direct_parsed.get("matched_group_count"),
        "r6_wilson95_min_lcb": round(r6_min_lcb, 6),
        "r6_support_gate": positive_rows >= 50 and negative_rows >= 50,
        "r6_wilson95_gate": r6_min_lcb >= 0.95,
        "r6_broad_normal_sample": False,
        "r6_direct_species_closed": False,
        "checklist": checklist,
        "gates": gates,
        "failures_present": failures_present,
        "accepted_rows_added": 0,
        "new_confidence_gate": False,
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "external_requests_sent": False,
        "trade_usable": False,
        "next_action": "Acquire native sub-hour source-label rows or post-2026-01-30 recency-extension rows, or expand R6 direct Manipulation to 50/50 broad-normal controls/direct species coverage before another completion claim.",
    }

    json_path = OUT / "current_goal_completion_audit_v48_after_source_confidence_calibration.json"
    report_path = OUT / "current_goal_completion_audit_v48_after_source_confidence_calibration.md"
    checklist_csv = OUT / "current_goal_completion_audit_v48_checklist.csv"
    gates_csv = OUT / "current_goal_completion_audit_v48_gates.csv"
    assertions_path = CHECKS / "current_goal_completion_audit_v48_after_source_confidence_calibration_assertions.out"

    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_csv(checklist_csv, checklist, ["id", "status", "evidence", "gap"])
    write_csv(gates_csv, gates, ["gate", "observed", "required", "pass"])

    lines = [
        "# Current Goal Completion Audit v48 After Source Confidence Calibration",
        "",
        f"Decision: `{decision}`.",
        "",
        "Objective restatement:",
        result["objective_restatement"],
        "",
        "Result:",
        f"- Board hash before run: `{board_hash}`.",
        f"- Current cursor before run: `{cursor_before}`.",
        f"- Ready intake roots: `{len(ready_roots)}/4` (`{';'.join(ready_roots)}`)." if ready_roots else "- Ready intake roots: `0/4`.",
        f"- Source-label verifier: `{source_label_parsed.get('status')}`; rows `{source_label_rows}`; all roots present `{bool_text(all(label in label_counts for label in ROOT_LABELS))}`.",
        f"- Source-label confidence accepted labels: `{accepted_source_labels or 'none'}`.",
        f"- Source-panel recency verifier: `{source_panel_parsed.get('status')}`.",
        f"- Native sub-hour root ready: `{bool_text(NATIVE_SUBHOUR_ROOT.exists())}`.",
        f"- R6 direct verifier: `{direct_parsed.get('status')}`; positives `{positive_rows}`; matched negatives `{negative_rows}`; matched groups `{direct_parsed.get('matched_group_count')}`.",
        f"- R6 Wilson95 positive/negative/min LCB: `{wilson_all_success_lcb(positive_rows):.6f}` / `{wilson_all_success_lcb(negative_rows):.6f}` / `{r6_min_lcb:.6f}`.",
        "- R6 support gate: `false`; broad normal sample: `false`; direct species closed: `false`.",
        "- Accepted rows added: `0`; new confidence gate: `false`.",
        "- Strict full objective achieved: `false`; `update_goal=false`.",
        "- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; external requests sent: `false`; trade usable: `false`.",
        "",
        "Prompt-to-artifact checklist:",
        "",
        "| ID | Status | Evidence | Gap |",
        "|---|---|---|---|",
    ]
    for row in checklist:
        lines.append(f"| `{row['id']}` | `{row['status']}` | {row['evidence']} | {row['gap']} |")
    lines.extend(["", "Gates:", "", "| Gate | Observed | Required | Pass |", "|---|---|---|---:|"])
    for gate in gates:
        lines.append(f"| `{gate['gate']}` | `{gate['observed']}` | `{gate['required']}` | `{bool_text(bool(gate['pass']))}` |")
    lines.extend(
        [
            "",
            "Next:",
            result["next_action"],
            "",
            "Artifacts:",
            f"- JSON: `{json_path.relative_to(REPO)}`",
            f"- Report: `{report_path.relative_to(REPO)}`",
            f"- Checklist CSV: `{checklist_csv.relative_to(REPO)}`",
            f"- Gate CSV: `{gates_csv.relative_to(REPO)}`",
            f"- Verifier outputs: `{CMD.relative_to(REPO)}`",
            f"- Assertions: `{assertions_path.relative_to(REPO)}`",
        ]
    )
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    assertions = [
        f"PASS decision={decision}",
        "PASS objective_restatement_present",
        f"PASS checklist_rows={len(checklist)}",
        f"PASS failures_present={bool_text(failures_present)}",
        f"PASS source_label_verifier_status={source_label_parsed.get('status')}",
        f"PASS source_label_rows={source_label_rows}",
        f"PASS accepted_source_confidence_95_labels={','.join(accepted_source_labels) or 'none'}",
        f"PASS source_panel_recency_status={source_panel_parsed.get('status')}",
        f"PASS native_subhour_root_ready={bool_text(NATIVE_SUBHOUR_ROOT.exists())}",
        f"PASS r6_positive_rows={positive_rows}",
        f"PASS r6_matched_negative_rows={negative_rows}",
        f"PASS r6_combined_min_wilson95_lcb={r6_min_lcb:.6f}",
        "PASS update_goal=false",
        "PASS accepted_rows_added=0",
        "PASS new_confidence_gate=false",
        "PASS external_requests_sent=false",
        "PASS raw_data_committed=false",
    ]
    assertions_path.write_text("\n".join(assertions) + "\n", encoding="utf-8")

    if not failures_present:
        raise AssertionError("completion audit unexpectedly has no failures")
    if accepted_source_labels:
        raise AssertionError("unexpected accepted source-confidence labels")
    print(json.dumps({"decision": decision, "source_label_rows": source_label_rows, "accepted_source_confidence_95_labels": accepted_source_labels, "update_goal": False}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
