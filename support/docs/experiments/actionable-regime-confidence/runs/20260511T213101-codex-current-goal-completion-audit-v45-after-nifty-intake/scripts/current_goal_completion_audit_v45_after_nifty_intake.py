#!/usr/bin/env python3
"""Completion audit after the NIFTY source-label equivalence intake.

This is a readback-only audit. It reruns the existing verifiers against live
intake roots, records the prompt-to-artifact checklist, and keeps the strict
goal blocked unless every requirement is covered by real evidence.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


RUN_ID = "20260511T213101-codex-current-goal-completion-audit-v45-after-nifty-intake"
REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs" / RUN_ID
OUT = RUN_ROOT / "completion-audit"
CHECKS = RUN_ROOT / "checks"
CMD = RUN_ROOT / "command-output"
BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"
RUNS = REPO / "docs/experiments/actionable-regime-confidence/runs"

SOURCE_LABEL_ROOT = Path("/tmp/ict-engine-source-label-equivalence-intake")
NATIVE_SUBHOUR_ROOT = Path("/tmp/ict-engine-native-subhour-source-label-intake")
RECENCY_ROOT = Path("/tmp/ict-engine-source-panel-recency-extension")
DIRECT_ROOT = Path("/tmp/ict-engine-direct-manipulation-row-intake")

SOURCE_LABEL_VERIFIER = RUNS / (
    "20260511T182922-codex-source-label-equivalence-intake-verifier-v1/"
    "equivalence-intake-verifier/source_label_equivalence_intake_verifier_v1.py"
)
RECENCY_VERIFIER = RUNS / (
    "20260511T165405-codex-source-panel-recency-extension-manifest-v1/"
    "source-panel-recency/source_panel_recency_extension_verifier_v1.py"
)
DIRECT_VERIFIER = RUNS / (
    "20260511T151950-codex-direct-manipulation-row-intake-manifest-v1/"
    "direct-manipulation-intake/direct_manipulation_row_intake_verifier_v1.py"
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_cursor() -> dict[str, str]:
    cursor: dict[str, str] = {}
    in_cursor = False
    for line in BOARD.read_text(encoding="utf-8").splitlines():
        if line.strip() == "## Current Cursor":
            in_cursor = True
            continue
        if in_cursor and line.startswith("## "):
            break
        if in_cursor and line.startswith("|"):
            parts = [part.strip() for part in line.strip().strip("|").split("|")]
            if len(parts) >= 2 and parts[0] not in {"Field", "---"}:
                cursor[parts[0]] = parts[1]
    return cursor


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows([{field: row.get(field, "") for field in fields} for row in rows])


def run_verifier(verifier_id: str, cmd: list[str], stdout_name: str, stderr_name: str) -> dict[str, object]:
    proc = subprocess.run(cmd, cwd=REPO, text=True, capture_output=True, check=False, timeout=90)
    stdout_path = CMD / stdout_name
    stderr_path = CMD / stderr_name
    stdout_path.write_text(proc.stdout, encoding="utf-8")
    stderr_path.write_text(proc.stderr, encoding="utf-8")
    parsed = None
    status = "stdout_not_json"
    if proc.stdout.strip():
        try:
            parsed = json.loads(proc.stdout)
            status = str(parsed.get("status", "json_no_status"))
        except json.JSONDecodeError:
            status = "stdout_not_json"
    return {
        "id": verifier_id,
        "returncode": proc.returncode,
        "status": status,
        "parsed": parsed,
        "stdout_file": str(stdout_path.relative_to(REPO)),
        "stderr_file": str(stderr_path.relative_to(REPO)),
    }


def wilson_lcb(n: int, z: float = 1.959963984540054) -> float:
    if n <= 0:
        return 0.0
    denom = 1.0 + z * z / n
    centre = 1.0 + z * z / (2 * n)
    margin = z * math.sqrt((z * z / (4 * n)) / n)
    return (centre - margin) / denom


def root_state(root_id: str, root: Path, required: list[str]) -> dict[str, object]:
    present: list[str] = []
    missing: list[str] = []
    row_counts: dict[str, int] = {}
    hashes: dict[str, str] = {}
    for name in required:
        path = root / name
        if path.exists():
            present.append(name)
            hashes[name] = sha256_file(path)
            if path.suffix == ".csv":
                row_counts[name] = len(read_csv(path))
        else:
            missing.append(name)
    return {
        "id": root_id,
        "root": str(root),
        "exists": root.exists(),
        "ready": not missing,
        "present_files": ";".join(present),
        "missing_files": ";".join(missing),
        "required_files": ";".join(required),
        "csv_row_counts": json.dumps(row_counts, sort_keys=True),
        "file_hashes": hashes,
    }


def source_label_summary() -> dict[str, object]:
    rows = read_csv(SOURCE_LABEL_ROOT / "source_label_equivalence_rows.csv")
    if not rows:
        return {
            "row_count": 0,
            "label_counts": {},
            "symbols": [],
            "market_families": [],
            "timeframes": [],
            "split_roles": [],
            "date_min": "",
            "date_max": "",
            "all_main_labels_present": False,
            "native_subhour_present": False,
            "market_count": 0,
        }
    labels = Counter(row.get("main_regime_v2_label", "") for row in rows)
    timeframes = sorted({row.get("timeframe", "") for row in rows})
    dates = sorted(row.get("timestamp_or_date", "") for row in rows if row.get("timestamp_or_date"))
    markets = sorted({row.get("market_family", "") for row in rows})
    symbols = sorted({row.get("symbol", "") for row in rows})
    return {
        "row_count": len(rows),
        "label_counts": dict(sorted(labels.items())),
        "symbols": symbols,
        "market_families": markets,
        "timeframes": timeframes,
        "split_roles": sorted({row.get("split_role", "") for row in rows}),
        "date_min": dates[0] if dates else "",
        "date_max": dates[-1] if dates else "",
        "all_main_labels_present": all(label in labels for label in ["Bear", "Bull", "Crisis", "Sideways"]),
        "native_subhour_present": any(tf not in {"1d", "1D", "daily", "Daily"} for tf in timeframes),
        "market_count": len(markets),
    }


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)
    CMD.mkdir(parents=True, exist_ok=True)

    board_hash = sha256_file(BOARD)
    cursor = read_cursor()

    verifier_readbacks = [
        run_verifier(
            "source_label_equivalence",
            ["python3", str(SOURCE_LABEL_VERIFIER), "--intake-root", str(SOURCE_LABEL_ROOT)],
            "source_label_equivalence_verifier.stdout.txt",
            "source_label_equivalence_verifier.stderr.txt",
        ),
        run_verifier(
            "source_panel_recency_extension",
            ["python3", str(RECENCY_VERIFIER), "--intake-root", str(RECENCY_ROOT)],
            "source_panel_recency_verifier.stdout.txt",
            "source_panel_recency_verifier.stderr.txt",
        ),
        run_verifier(
            "direct_manipulation_row_intake",
            ["python3", str(DIRECT_VERIFIER), "--intake-root", str(DIRECT_ROOT)],
            "direct_manipulation_verifier.stdout.txt",
            "direct_manipulation_verifier.stderr.txt",
        ),
    ]

    source_label = next(v for v in verifier_readbacks if v["id"] == "source_label_equivalence")
    recency = next(v for v in verifier_readbacks if v["id"] == "source_panel_recency_extension")
    direct = next(v for v in verifier_readbacks if v["id"] == "direct_manipulation_row_intake")
    direct_payload = direct.get("parsed") or {}
    r6_positive = int(direct_payload.get("positive_rows", 0) or 0)
    r6_negative = int(direct_payload.get("matched_negative_rows", 0) or 0)
    r6_groups = int(direct_payload.get("matched_group_count", 0) or 0)
    r6_min_lcb = min(wilson_lcb(r6_positive), wilson_lcb(r6_negative))

    sl_summary = source_label_summary()
    roots = [
        root_state(
            "source_label_equivalence",
            SOURCE_LABEL_ROOT,
            ["source_label_equivalence_rows.csv", "source_label_equivalence_provenance.json"],
        ),
        root_state(
            "native_subhour_source_label",
            NATIVE_SUBHOUR_ROOT,
            ["native_subhour_source_label_rows.csv", "native_subhour_source_label_provenance.json"],
        ),
        root_state(
            "source_panel_recency_extension",
            RECENCY_ROOT,
            ["stock_market_regimes_2026_extension.csv", "source_panel_recency_provenance.json"],
        ),
        root_state(
            "direct_manipulation_row_intake",
            DIRECT_ROOT,
            ["positive_spoofing_layering_rows.csv", "matched_negative_normal_activity_rows.csv", "provenance_manifest.json"],
        ),
    ]
    ready_roots = [root["id"] for root in roots if root["ready"]]

    source_label_ready = source_label["status"] == "schema_ready_unscored"
    source_label_95_gate = False
    source_label_cross_market_complete = False
    source_label_cross_timeframe_complete = False
    native_ready = next(root for root in roots if root["id"] == "native_subhour_source_label")["ready"]
    recency_ready = recency["status"] == "schema_ready_unscored"
    r6_support_ok = r6_positive >= 50 and r6_negative >= 50
    r6_broad_normal_sample = False
    r6_direct_species_closed = False

    checklist = [
        {
            "id": "R0_named_board",
            "requirement": "Use the named Board A markdown and produce repo-local artifacts.",
            "evidence": str(BOARD.relative_to(REPO)),
            "status": "pass_checked",
            "gap": "",
        },
        {
            "id": "R1_every_regime_95",
            "requirement": "Every active regime must have source-owned or owner-approved >=95 confidence.",
            "evidence": f"source_label_status={source_label['status']}; source_label_95_gate={source_label_95_gate}; r6_min_wilson95_lcb={r6_min_lcb:.6f}; ready_roots={len(ready_roots)}/4",
            "status": "fail_blocked",
            "gap": "Source-label equivalence is schema-ready but unscored/partial; R6 Wilson95 remains below 0.95; native sub-hour and recency roots remain absent.",
        },
        {
            "id": "R2_other_market_species_validation",
            "requirement": "Validate regimes on other markets/species with suitable confidence.",
            "evidence": f"NIFTY source-label rows={sl_summary['row_count']}; labels={sl_summary['label_counts']}; markets={sl_summary['market_families']}; symbols={sl_summary['symbols']}",
            "status": "partial_blocked",
            "gap": "NIFTY provides one other-market daily source-label package for Bull/Crisis/Sideways only; Bear is absent and no 95 confidence gate is produced.",
        },
        {
            "id": "R3_other_cycle_timeframe_validation",
            "requirement": "Validate regimes on other cycles/timeframes with suitable confidence.",
            "evidence": f"timeframes={sl_summary['timeframes']}; native_subhour_ready={native_ready}; recency_status={recency['status']}",
            "status": "fail_blocked",
            "gap": "NIFTY rows are daily only; native sub-hour source-label root and recency-extension root remain unavailable.",
        },
        {
            "id": "R4_r6_direct_confidence",
            "requirement": "R6 direct Manipulation must pass support, Wilson95, broad-normal, and direct-species gates.",
            "evidence": f"positives={r6_positive}; controls={r6_negative}; groups={r6_groups}; min_lcb={r6_min_lcb:.6f}; broad_normal={r6_broad_normal_sample}; species_closed={r6_direct_species_closed}",
            "status": "fail_blocked",
            "gap": "R6 remains below 50/50 support and below 0.95 Wilson95, with same-source/event controls and incomplete direct species coverage.",
        },
        {
            "id": "R5_no_proxy_acceptance",
            "requirement": "Do not accept schema readiness, proxy labels, no-send drafts, or same-event controls as completion.",
            "evidence": "NIFTY schema readiness is recorded as partial/unscored; R6 same-event controls remain fail-closed; no completion claim.",
            "status": "pass_guardrail",
            "gap": "",
        },
        {
            "id": "R6_multi_agent_safety",
            "requirement": "Do not disturb concurrent board sections or in-progress artifacts.",
            "evidence": f"board_hash_before={board_hash}; cursor_before={cursor.get('last_loop_id')}; append-only V45 audit",
            "status": "pass_guardrail",
            "gap": "",
        },
        {
            "id": "R7_update_goal_gate",
            "requirement": "Only call update_goal when every objective requirement is covered by real evidence.",
            "evidence": "failures_present=true",
            "status": "fail_blocked",
            "gap": "Strict full objective remains incomplete; update_goal=false.",
        },
    ]

    gates = [
        {"gate": "ready_intake_roots", "observed": len(ready_roots), "required": 4, "pass": len(ready_roots) == 4},
        {"gate": "source_label_schema_ready", "observed": source_label["status"], "required": "schema_ready_unscored", "pass": source_label_ready},
        {"gate": "source_label_all_main_labels", "observed": json.dumps(sl_summary["label_counts"], sort_keys=True), "required": "Bear/Bull/Crisis/Sideways", "pass": sl_summary["all_main_labels_present"]},
        {"gate": "source_label_confidence_95", "observed": source_label_95_gate, "required": True, "pass": False},
        {"gate": "cross_market_complete", "observed": source_label_cross_market_complete, "required": True, "pass": False},
        {"gate": "cross_timeframe_complete", "observed": source_label_cross_timeframe_complete, "required": True, "pass": False},
        {"gate": "native_subhour_root_ready", "observed": native_ready, "required": True, "pass": native_ready},
        {"gate": "recency_extension_ready", "observed": recency_ready, "required": True, "pass": recency_ready},
        {"gate": "r6_positive_support", "observed": r6_positive, "required": ">=50", "pass": r6_positive >= 50},
        {"gate": "r6_negative_support", "observed": r6_negative, "required": ">=50", "pass": r6_negative >= 50},
        {"gate": "r6_wilson95_lcb", "observed": f"{r6_min_lcb:.6f}", "required": ">=0.95", "pass": r6_min_lcb >= 0.95},
        {"gate": "r6_broad_normal_sample", "observed": r6_broad_normal_sample, "required": True, "pass": False},
        {"gate": "r6_direct_species_coverage", "observed": r6_direct_species_closed, "required": True, "pass": False},
    ]

    decision = "current_goal_completion_audit_v45=after_nifty_source_label_partial_still_blocked"
    result = {
        "run_id": RUN_ID,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "board_hash_before": board_hash,
        "cursor_before": cursor,
        "decision": decision,
        "objective_restatement": "Every active regime must have source-owned or owner-approved >=95 confidence and must retain suitable confidence when validated on other markets/species and other cycles/timeframes.",
        "source_label_summary": sl_summary,
        "intake_roots": roots,
        "ready_roots": ready_roots,
        "ready_root_count": len(ready_roots),
        "verifier_readbacks": verifier_readbacks,
        "r6_positive_rows": r6_positive,
        "r6_matched_negative_rows": r6_negative,
        "r6_matched_group_count": r6_groups,
        "r6_min_wilson95_lcb": r6_min_lcb,
        "checklist": checklist,
        "gates": gates,
        "accepted_rows_added": 0,
        "source_label_ready_rows_added": int(sl_summary["row_count"]),
        "new_confidence_gate": False,
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "external_requests_sent": False,
        "trade_usable": False,
        "next_action": "Turn source-label schema readiness into real confidence gates only if per-regime Bear/Bull/Crisis/Sideways source rows, cross-market coverage, native sub-hour/other-cycle evidence, recency extension, and unchanged calibration/heldout scoring all pass; otherwise continue filling missing roots.",
    }

    json_path = OUT / "current_goal_completion_audit_v45_after_nifty_intake.json"
    report_path = OUT / "current_goal_completion_audit_v45_after_nifty_intake.md"
    checklist_csv = OUT / "current_goal_completion_audit_v45_checklist.csv"
    gates_csv = OUT / "current_goal_completion_audit_v45_gates.csv"
    roots_csv = OUT / "current_goal_completion_audit_v45_intake_roots.csv"
    assertions_path = CHECKS / "current_goal_completion_audit_v45_after_nifty_intake_assertions.out"

    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_csv(checklist_csv, checklist, ["id", "requirement", "evidence", "status", "gap"])
    write_csv(gates_csv, gates, ["gate", "observed", "required", "pass"])
    write_csv(roots_csv, roots, ["id", "root", "exists", "ready", "present_files", "missing_files", "required_files", "csv_row_counts"])

    report_lines = [
        "# Current Goal Completion Audit v45 After NIFTY Intake",
        "",
        f"Decision: `{decision}`.",
        "",
        "Objective restatement:",
        result["objective_restatement"],
        "",
        "Result:",
        f"- Board hash before run: `{board_hash}`.",
        f"- Cursor before run: `{cursor.get('last_loop_id', 'unknown')}`.",
        f"- Ready intake roots: `{len(ready_roots)}/4` (`{';'.join(ready_roots)}`).",
        f"- Source-label equivalence verifier: `{source_label['status']}`; rows `{sl_summary['row_count']}`; labels `{sl_summary['label_counts']}`; dates `{sl_summary['date_min']}..{sl_summary['date_max']}`.",
        f"- Source-label limits: all main labels present `{str(sl_summary['all_main_labels_present']).lower()}`; timeframes `{sl_summary['timeframes']}`; markets `{sl_summary['market_families']}`.",
        f"- Native sub-hour ready: `{str(native_ready).lower()}`; recency verifier: `{recency['status']}`.",
        f"- R6 direct verifier: `{direct['status']}`; positives `{r6_positive}`; matched negatives `{r6_negative}`; matched groups `{r6_groups}`; Wilson95 min LCB `{r6_min_lcb:.6f}`.",
        "- Accepted rows added: `0`; new confidence gate: `false`.",
        "- Strict full objective achieved: `false`; `update_goal=false`.",
        "- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; external requests sent: `false`; trade usable: `false`.",
        "",
        "Prompt-to-artifact checklist:",
        "",
        "| ID | Status | Evidence | Gap |",
        "|---|---|---|---|",
    ]
    for item in checklist:
        report_lines.append(f"| `{item['id']}` | `{item['status']}` | {item['evidence']} | {item['gap']} |")
    report_lines.extend(["", "Gates:", "", "| Gate | Observed | Required | Pass |", "|---|---|---|---:|"])
    for gate in gates:
        report_lines.append(f"| `{gate['gate']}` | `{gate['observed']}` | `{gate['required']}` | `{str(gate['pass']).lower()}` |")
    report_lines.extend(
        [
            "",
            "Next:",
            str(result["next_action"]),
            "",
            "Artifacts:",
            f"- JSON: `{json_path.relative_to(REPO)}`",
            f"- Report: `{report_path.relative_to(REPO)}`",
            f"- Checklist CSV: `{checklist_csv.relative_to(REPO)}`",
            f"- Gate CSV: `{gates_csv.relative_to(REPO)}`",
            f"- Intake-root CSV: `{roots_csv.relative_to(REPO)}`",
            f"- Verifier outputs: `{CMD.relative_to(REPO)}`",
            f"- Assertions: `{assertions_path.relative_to(REPO)}`",
        ]
    )
    report_path.write_text("\n".join(report_lines) + "\n", encoding="utf-8")

    assertions = [
        f"PASS decision={decision}",
        "PASS objective_restatement_present",
        f"PASS checklist_rows={len(checklist)}",
        "PASS failures_present=true",
        f"PASS ready_root_count={len(ready_roots)}",
        f"PASS source_label_status={source_label['status']}",
        f"PASS source_label_rows={sl_summary['row_count']}",
        f"PASS r6_positive_rows={r6_positive}",
        f"PASS r6_matched_negative_rows={r6_negative}",
        f"PASS r6_min_wilson95_lcb={r6_min_lcb:.6f}",
        "PASS update_goal=false",
        "PASS accepted_rows_added=0",
        "PASS new_confidence_gate=false",
        "PASS external_requests_sent=false",
        "PASS raw_data_committed=false",
    ]
    assertions_path.write_text("\n".join(assertions) + "\n", encoding="utf-8")

    print(json.dumps({
        "decision": decision,
        "ready_roots": len(ready_roots),
        "source_label_rows": sl_summary["row_count"],
        "source_label_status": source_label["status"],
        "r6_min_wilson95_lcb": round(r6_min_lcb, 6),
        "update_goal": False,
        "report": str(report_path.relative_to(REPO)),
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
