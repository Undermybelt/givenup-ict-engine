#!/usr/bin/env python3
"""Current-goal audit after the R5 source-panel recency live-refresh attempts."""

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


RUN_ID = "20260511T215929-codex-current-goal-completion-audit-v50-after-r5-live-refresh-readback"
REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = Path(__file__).resolve().parents[1]
RUNS_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs"
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


def bool_text(value: Any) -> str:
    return str(bool(value)).lower()


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def readback_summary(path: Path) -> dict[str, Any]:
    data = load_json(path)
    decision = data.get("decision", "")
    if isinstance(decision, dict):
        decision = decision.get("gate_result") or json.dumps(decision, sort_keys=True)
    source_summary = data.get("source_summary") or {}
    recency_verifier = data.get("recency_verifier") or data.get("source_panel_recency_verifier") or {}
    parsed_verifier = recency_verifier.get("parsed") if isinstance(recency_verifier, dict) else {}
    compatible_post_cutoff = int(data.get("compatible_post_cutoff_source_count") or 0)
    post_cutoff_rows = (
        source_summary.get("rows_after_2026_01_30")
        or source_summary.get("post_cutoff_rows")
        or data.get("post_cutoff_rows")
        or data.get("rows_after_2026_01_30")
        or 0
    )
    if "local_stock_post_cutoff_rows" in data:
        post_cutoff_rows = data["local_stock_post_cutoff_rows"]
    return {
        "artifact": str(path.relative_to(REPO)),
        "decision": decision,
        "dataset": data.get("dataset") or data.get("source_owner_package") or "",
        "rows": source_summary.get("rows") or data.get("latest_downloaded_panel_rows") or "",
        "max_date": source_summary.get("max_date") or data.get("latest_downloaded_max_date") or "",
        "post_cutoff_rows": post_cutoff_rows,
        "compatible_post_cutoff_source_count": compatible_post_cutoff,
        "intake_populated": bool(data.get("intake_rows_written") or data.get("r5_intake_populated")),
        "verifier_status": (parsed_verifier or {}).get("status") or data.get("r5_verifier_status_after_screen") or data.get("r5_verifier_status_after_recheck") or "",
        "accepted_rows_added": int(data.get("accepted_rows_added") or 0),
        "external_requests_sent": bool(data.get("external_requests_sent")),
        "raw_data_committed": bool(data.get("raw_data_committed")),
        "thresholds_relaxed": bool(data.get("thresholds_relaxed")),
        "trade_usable": bool(data.get("trade_usable")),
    }


def discover_r5_readbacks() -> list[Path]:
    paths = []
    for path in RUNS_ROOT.glob("20260511T*-codex-*r5*/**/*.json"):
        if RUN_ID not in str(path):
            paths.append(path)
    return sorted(set(paths))


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)
    CMD.mkdir(parents=True, exist_ok=True)

    required = [
        BOARD,
        SOURCE_CONFIDENCE,
        SOURCE_LABEL_VERIFIER,
        SOURCE_PANEL_VERIFIER,
        DIRECT_VERIFIER,
    ]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError(missing)

    board_text = BOARD.read_text(encoding="utf-8")
    board_hash = sha256_file(BOARD)
    cursor_before = current_cursor(board_text)
    source_confidence = load_json(SOURCE_CONFIDENCE)
    r5_paths = discover_r5_readbacks()
    if not r5_paths:
        raise FileNotFoundError("no existing R5 readback JSON artifacts found")
    r5_readbacks = [readback_summary(path) for path in r5_paths]

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
    r5_any_intake = any(row["intake_populated"] for row in r5_readbacks)
    r5_any_post_cutoff = any(int(row["compatible_post_cutoff_source_count"] or 0) > 0 for row in r5_readbacks)
    r5_external_count = sum(1 for row in r5_readbacks if row["external_requests_sent"])
    ready_roots = [
        root
        for root, ready in [
            ("source_label_equivalence", source_label_parsed.get("status") == "schema_ready_unscored"),
            ("direct_manipulation_row_intake", direct_parsed.get("status") == "schema_ready_unscored"),
        ]
        if ready
    ]

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
            "gap": "No active regime/root has an accepted source-owned >=95% package.",
        },
        {
            "id": "R2_other_market_validation",
            "status": "fail_blocked",
            "evidence": f"source_label_status={source_label_parsed.get('status')}; rows={source_label_rows}; accepted_labels={accepted_source_labels or 'none'}",
            "gap": "All four source-label roots are present, but the confidence calibration accepted zero labels.",
        },
        {
            "id": "R3_other_cycle_timeframe",
            "status": "fail_blocked",
            "evidence": f"native_subhour_ready={NATIVE_SUBHOUR_ROOT.exists()}; r5_verifier={source_panel_parsed.get('status')}/{source_panel_parsed.get('reason')}",
            "gap": "Native sub-hour rows/provenance are absent; R5 recency files are still missing after live source-owner refresh checks.",
        },
        {
            "id": "R4_provider_and_full_chain",
            "status": "partial_guardrail",
            "evidence": "This audit reran current root verifiers and read existing R5 live-refresh artifacts; no fresh Auto-Quant/downstream packet is eligible.",
            "gap": "Pre-Bayes/BBN/CatBoost/execution-tree completion remains blocked until a root confidence packet is accepted.",
        },
        {
            "id": "R5_source_panel_recency_extension",
            "status": "fail_blocked",
            "evidence": f"r5_readbacks={len(r5_readbacks)}; external_checks={r5_external_count}; any_intake_populated={r5_any_intake}; verifier={source_panel_parsed.get('status')}",
            "gap": "The owner package still ends at 2026-01-30; provider OHLCV/proxy rows were rejected and no source-owned post-cutoff rows were written.",
        },
        {
            "id": "R6_direct_manipulation_confidence",
            "status": "fail_blocked",
            "evidence": f"positives={positive_rows}; controls={negative_rows}; matched_groups={direct_parsed.get('matched_group_count')}; min_lcb={r6_min_lcb:.6f}",
            "gap": "R6 remains below support, Wilson95, broad-normal sample, and direct-species gates.",
        },
        {
            "id": "R7_no_proxy_acceptance",
            "status": "pass_guardrail",
            "evidence": "R5 OHLCV-only/yfinance rows and schema-mismatched recent datasets are explicitly rejected.",
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
        {"gate": "r5_post_cutoff_source_owned_rows", "observed": r5_any_post_cutoff, "required": True, "pass": False},
        {"gate": "r5_intake_populated", "observed": r5_any_intake, "required": True, "pass": False},
        {"gate": "native_subhour_root_ready", "observed": NATIVE_SUBHOUR_ROOT.exists(), "required": True, "pass": False},
        {"gate": "r6_positive_support", "observed": positive_rows, "required": ">=50", "pass": positive_rows >= 50},
        {"gate": "r6_negative_support", "observed": negative_rows, "required": ">=50", "pass": negative_rows >= 50},
        {"gate": "r6_wilson95_lcb", "observed": round(r6_min_lcb, 6), "required": ">=0.95", "pass": r6_min_lcb >= 0.95},
        {"gate": "r6_broad_normal_sample", "observed": False, "required": True, "pass": False},
        {"gate": "r6_direct_species_coverage", "observed": False, "required": True, "pass": False},
    ]

    decision = "current_goal_completion_audit_v50=r5_live_refresh_no_post_cutoff_rows_2of4_roots_still_blocked"
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
        "r5_readbacks": r5_readbacks,
        "ready_roots": ready_roots,
        "source_label_rows": source_label_rows,
        "source_label_counts": label_counts,
        "accepted_source_confidence_95_labels": accepted_source_labels,
        "r5_readback_count": len(r5_readbacks),
        "r5_external_readback_count": r5_external_count,
        "r5_any_source_owned_post_cutoff_rows": r5_any_post_cutoff,
        "r5_intake_populated": r5_any_intake,
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
        "accepted_rows_added": 0,
        "new_confidence_gate": False,
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "external_requests_sent": False,
        "trade_usable": False,
        "next_action": "Move the active slice to R6 direct Manipulation broad-normal/direct-species row acquisition, or native sub-hour source-label acquisition; keep R5 blocked until the source owner publishes post-2026-01-30 source-panel rows.",
    }

    json_path = OUT / "current_goal_completion_audit_v50_after_r5_live_refresh_readback.json"
    report_path = OUT / "current_goal_completion_audit_v50_after_r5_live_refresh_readback.md"
    checklist_path = OUT / "current_goal_completion_audit_v50_checklist.csv"
    gates_path = OUT / "current_goal_completion_audit_v50_gates.csv"
    readbacks_path = OUT / "current_goal_completion_audit_v50_r5_readbacks.csv"
    assertions_path = CHECKS / "current_goal_completion_audit_v50_after_r5_live_refresh_readback_assertions.out"

    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_csv(checklist_path, checklist, ["id", "status", "evidence", "gap"])
    write_csv(gates_path, gates, ["gate", "observed", "required", "pass"])
    write_csv(
        readbacks_path,
        r5_readbacks,
        [
            "artifact",
            "decision",
            "dataset",
            "rows",
            "max_date",
            "post_cutoff_rows",
            "compatible_post_cutoff_source_count",
            "intake_populated",
            "verifier_status",
            "accepted_rows_added",
            "external_requests_sent",
            "raw_data_committed",
            "thresholds_relaxed",
            "trade_usable",
        ],
    )

    checklist_lines = "\n".join(
        f"| `{row['id']}` | `{row['status']}` | {row['evidence']} | {row['gap']} |"
        for row in checklist
    )
    gate_lines = "\n".join(
        f"| `{row['gate']}` | `{row['observed']}` | `{row['required']}` | `{bool_text(row['pass'])}` |"
        for row in gates
    )
    r5_lines = "\n".join(
        f"| `{Path(row['artifact']).parts[-1]}` | `{row['decision']}` | `{row['post_cutoff_rows']}` | `{bool_text(row['intake_populated'])}` | `{row['verifier_status']}` |"
        for row in r5_readbacks
    )
    report = f"""# Current Goal Completion Audit v50 After R5 Live Refresh Readback

Decision: `{decision}`.

Objective restatement:
Every active regime must have source-owned or owner-approved >=95 confidence and must retain suitable confidence across other markets/species and other cycles/timeframes before completion can be reported.

Result:
- Board hash before run: `{board_hash}`.
- Current cursor before run: `{cursor_before}`.
- Ready intake roots: `{len(ready_roots)}/4` (`{';'.join(ready_roots)}`).
- Source-label verifier: `{source_label_parsed.get('status')}`; rows `{source_label_rows}`; all roots present `{bool_text(all(label in label_counts for label in ROOT_LABELS))}`.
- Source-label confidence accepted labels: `{accepted_source_labels or 'none'}`.
- R5 live/source-owner readbacks reviewed: `{len(r5_readbacks)}`; external source checks among them: `{r5_external_count}`.
- R5 source-owned post-cutoff rows found: `{bool_text(r5_any_post_cutoff)}`; R5 intake populated: `{bool_text(r5_any_intake)}`.
- Source-panel recency verifier after readback: `{source_panel_parsed.get('status')}` / `{source_panel_parsed.get('reason')}`.
- Native sub-hour root ready: `{bool_text(NATIVE_SUBHOUR_ROOT.exists())}`.
- R6 direct verifier: `{direct_parsed.get('status')}`; positives `{positive_rows}`; matched negatives `{negative_rows}`; matched groups `{direct_parsed.get('matched_group_count')}`.
- R6 Wilson95 min LCB: `{r6_min_lcb:.6f}`; support gate `{bool_text(positive_rows >= 50 and negative_rows >= 50)}`; broad normal sample `false`; direct species closed `false`.
- Accepted rows added: `0`; new confidence gate: `false`.
- Strict full objective achieved: `false`; `update_goal=false`.
- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; external requests sent by this audit: `false`; trade usable: `false`.

R5 readback ledger:

| Artifact | Decision | Post-Cutoff Rows | Intake Populated | Verifier |
|---|---|---:|---:|---|
{r5_lines}

Prompt-to-artifact checklist:

| ID | Status | Evidence | Gap |
|---|---|---|---|
{checklist_lines}

Gates:

| Gate | Observed | Required | Pass |
|---|---|---|---:|
{gate_lines}

Next:
Move the active slice to R6 direct Manipulation broad-normal/direct-species row acquisition, or native sub-hour source-label acquisition. Keep R5 blocked until the source owner publishes post-`2026-01-30` source-panel rows.

Artifacts:
- JSON: `{json_path.relative_to(REPO)}`
- Report: `{report_path.relative_to(REPO)}`
- Checklist CSV: `{checklist_path.relative_to(REPO)}`
- Gate CSV: `{gates_path.relative_to(REPO)}`
- R5 readback CSV: `{readbacks_path.relative_to(REPO)}`
- Verifier outputs: `{CMD.relative_to(REPO)}`
- Assertions: `{assertions_path.relative_to(REPO)}`
"""
    report_path.write_text(report, encoding="utf-8")

    assertions = [
        f"decision={decision}",
        f"ready_roots={len(ready_roots)}/4",
        f"source_label_status={source_label_parsed.get('status')}",
        f"source_panel_recency_status={source_panel_parsed.get('status')}",
        f"r5_intake_populated={bool_text(r5_any_intake)}",
        f"r5_any_source_owned_post_cutoff_rows={bool_text(r5_any_post_cutoff)}",
        f"r6_positive_rows={positive_rows}",
        f"r6_matched_negative_rows={negative_rows}",
        f"r6_wilson95_min_lcb={r6_min_lcb:.6f}",
        "strict_full_objective_achieved=false",
        "update_goal=false",
    ]
    assertions_path.write_text("\n".join(assertions) + "\n", encoding="utf-8")

    if source_label_parsed.get("status") != "schema_ready_unscored":
        return 2
    if source_panel_parsed.get("status") != "blocked":
        return 3
    if direct_parsed.get("status") != "schema_ready_unscored":
        return 4
    if r5_any_intake or r5_any_post_cutoff:
        return 5
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
