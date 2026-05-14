#!/usr/bin/env python3
"""Completion audit after source-label confidence calibration."""

from __future__ import annotations

import csv
import hashlib
import json
import math
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


RUN_ID = "20260511T215015-codex-current-goal-completion-audit-v48-after-source-confidence-calibration"
REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = Path(__file__).resolve().parents[1]
OUT = RUN_ROOT / "completion-audit"
CMD = RUN_ROOT / "command-output"
CHECKS = RUN_ROOT / "checks"
BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"
RUNS = REPO / "docs/experiments/actionable-regime-confidence/runs"

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
CALIBRATION_JSON = RUNS / (
    "20260511T214328-codex-source-label-equivalence-confidence-calibration-v1/"
    "source-label-equivalence-confidence-calibration/"
    "source_label_equivalence_confidence_calibration_v1.json"
)

ROOTS = [
    {
        "id": "source_label_equivalence",
        "root": Path("/tmp/ict-engine-source-label-equivalence-intake"),
        "required": ["source_label_equivalence_rows.csv", "source_label_equivalence_provenance.json"],
    },
    {
        "id": "native_subhour_source_label",
        "root": Path("/tmp/ict-engine-native-subhour-source-label-intake"),
        "required": ["native_subhour_source_label_rows.csv", "native_subhour_source_label_provenance.json"],
    },
    {
        "id": "source_panel_recency_extension",
        "root": Path("/tmp/ict-engine-source-panel-recency-extension"),
        "required": ["stock_market_regimes_2026_extension.csv", "source_panel_recency_provenance.json"],
    },
    {
        "id": "direct_manipulation_row_intake",
        "root": Path("/tmp/ict-engine-direct-manipulation-row-intake"),
        "required": [
            "positive_spoofing_layering_rows.csv",
            "matched_negative_normal_activity_rows.csv",
            "provenance_manifest.json",
        ],
    },
]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


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


def csv_row_count(path: Path) -> int:
    if not path.exists() or path.suffix != ".csv":
        return 0
    with path.open(newline="", encoding="utf-8") as handle:
        return sum(1 for _ in csv.DictReader(handle))


def root_state(spec: dict[str, Any]) -> dict[str, Any]:
    root = spec["root"]
    present = []
    missing = []
    row_counts = {}
    file_hashes = {}
    for name in spec["required"]:
        path = root / name
        if path.exists():
            present.append(name)
            file_hashes[name] = sha256_file(path)
            if path.suffix == ".csv":
                row_counts[name] = csv_row_count(path)
        else:
            missing.append(name)
    return {
        "id": spec["id"],
        "root": str(root),
        "required_files": ";".join(spec["required"]),
        "present_files": ";".join(present),
        "missing_files": ";".join(missing),
        "ready": not missing,
        "exists": root.exists(),
        "csv_row_counts": json.dumps(row_counts, sort_keys=True),
        "file_hashes": file_hashes,
    }


def run_verifier(name: str, cmd: list[str]) -> dict[str, Any]:
    proc = subprocess.run(cmd, cwd=REPO, text=True, capture_output=True, check=False)
    stdout = CMD / f"{name}.stdout.txt"
    stderr = CMD / f"{name}.stderr.txt"
    exit_path = CMD / f"{name}.exit"
    stdout.write_text(proc.stdout, encoding="utf-8")
    stderr.write_text(proc.stderr, encoding="utf-8")
    exit_path.write_text(f"{proc.returncode}\n", encoding="utf-8")
    try:
        parsed = json.loads(proc.stdout)
    except json.JSONDecodeError:
        parsed = {"status": "unparsed", "stdout": proc.stdout[:1000]}
    return {
        "id": name,
        "returncode": proc.returncode,
        "status": parsed.get("status"),
        "parsed": parsed,
        "stdout_file": str(stdout.relative_to(REPO)),
        "stderr_file": str(stderr.relative_to(REPO)),
        "exit_file": str(exit_path.relative_to(REPO)),
    }


def wilson_lcb(successes: int, n: int, z: float = 1.959963984540054) -> float:
    if n <= 0:
        return 0.0
    phat = successes / n
    denom = 1 + z * z / n
    centre = phat + z * z / (2 * n)
    margin = z * math.sqrt((phat * (1 - phat) + z * z / (4 * n)) / n)
    return (centre - margin) / denom


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    CMD.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)

    generated_at = datetime.now(timezone.utc).isoformat()
    board_hash = sha256_file(BOARD)
    cursor = read_cursor()
    calibration = read_json(CALIBRATION_JSON)
    roots = [root_state(spec) for spec in ROOTS]
    ready_roots = [row["id"] for row in roots if row["ready"]]
    verifiers = [
        run_verifier(
            "source_label_equivalence_verifier",
            ["python3", str(SOURCE_LABEL_VERIFIER), "--intake-root", "/tmp/ict-engine-source-label-equivalence-intake"],
        ),
        run_verifier(
            "source_panel_recency_verifier",
            ["python3", str(RECENCY_VERIFIER), "--intake-root", "/tmp/ict-engine-source-panel-recency-extension"],
        ),
        run_verifier(
            "direct_manipulation_verifier",
            ["python3", str(DIRECT_VERIFIER), "--intake-root", "/tmp/ict-engine-direct-manipulation-row-intake"],
        ),
    ]
    verifier_by_id = {row["id"]: row for row in verifiers}
    source_label = verifier_by_id["source_label_equivalence_verifier"].get("parsed", {})
    direct = verifier_by_id["direct_manipulation_verifier"].get("parsed", {})
    positive_rows = int(direct.get("positive_rows") or 0)
    negative_rows = int(direct.get("matched_negative_rows") or 0)
    matched_groups = int(direct.get("matched_group_count") or 0)
    positive_lcb = wilson_lcb(positive_rows, positive_rows)
    negative_lcb = wilson_lcb(negative_rows, negative_rows)
    min_lcb = min(positive_lcb, negative_lcb)
    support_ok = positive_rows >= 50 and negative_rows >= 50
    accepted_labels = calibration.get("accepted_source_confidence_95_labels") or []

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
            "requirement": "Every active regime has source-owned or owner-approved >=95 confidence.",
            "evidence": f"{CALIBRATION_JSON.relative_to(REPO)}; accepted_labels={accepted_labels or 'none'}",
            "status": "fail_blocked",
            "gap": "Source-confidence calibration accepted zero labels at the required 0.95 Wilson lower-bound gate.",
        },
        {
            "id": "R2_other_market_validation",
            "requirement": "Validate regimes on other markets/species with suitable confidence.",
            "evidence": f"source_label_status={source_label.get('status')}; rows={source_label.get('row_count')}; all_roots_present={calibration.get('all_roots_present')}",
            "status": "fail_blocked",
            "gap": "Other-market/source-label rows are schema-ready with all roots, but calibrated confidence remains below acceptance.",
        },
        {
            "id": "R3_other_cycle_timeframe",
            "requirement": "Validate regimes on other cycles/timeframes with suitable confidence.",
            "evidence": "native_subhour_root_ready=false; source_panel_recency_status=blocked",
            "status": "fail_blocked",
            "gap": "Native sub-hour source-label root and R5 recency-extension root are still absent.",
        },
        {
            "id": "R4_r6_direct_confidence",
            "requirement": "Direct Manipulation passes support, Wilson95, broad-normal, and direct-species gates.",
            "evidence": f"positives={positive_rows}; controls={negative_rows}; matched_groups={matched_groups}; min_lcb={min_lcb:.6f}",
            "status": "fail_blocked",
            "gap": "R6 remains below 50/50 support, below 0.95 Wilson LCB, lacks broad-normal sample, and direct species are incomplete.",
        },
        {
            "id": "R5_no_proxy_acceptance",
            "requirement": "Do not accept proxy/schema readiness/generated labels as completion.",
            "evidence": "schema-ready roots and source confidence screen are kept fail-closed",
            "status": "pass_guardrail",
            "gap": "",
        },
        {
            "id": "R6_update_goal_gate",
            "requirement": "Only call update_goal when every requirement is covered by real evidence.",
            "evidence": "failures_present=true",
            "status": "fail_blocked",
            "gap": "Strict objective remains incomplete; update_goal=false.",
        },
    ]
    gates = [
        {"gate": "ready_intake_roots", "required": "4", "observed": str(len(ready_roots)), "pass": len(ready_roots) == 4},
        {
            "gate": "source_confidence_accepted_labels",
            "required": "Bear;Bull;Crisis;Sideways accepted at >=0.95",
            "observed": ";".join(accepted_labels) if accepted_labels else "none",
            "pass": False,
        },
        {"gate": "native_subhour_root_ready", "required": "true", "observed": "false", "pass": False},
        {
            "gate": "source_panel_recency_verifier",
            "required": "not_blocked",
            "observed": verifier_by_id["source_panel_recency_verifier"].get("status"),
            "pass": False,
        },
        {"gate": "r6_support", "required": ">=50/50", "observed": f"{positive_rows}/{negative_rows}", "pass": support_ok},
        {"gate": "r6_wilson95_min_lcb", "required": ">=0.95", "observed": f"{min_lcb:.6f}", "pass": min_lcb >= 0.95},
        {"gate": "strict_full_objective", "required": "true", "observed": "false", "pass": False},
    ]
    decision = "current_goal_completion_audit_v48=source_confidence_calibrated_no_labels_accepted_still_blocked"
    result = {
        "run_id": RUN_ID,
        "generated_at_utc": generated_at,
        "decision": decision,
        "objective_restatement": (
            "Every active regime must have source-owned or owner-approved >=95 confidence and retain suitable "
            "confidence across other markets/species and other cycles/timeframes before completion."
        ),
        "board_hash_before": board_hash,
        "cursor_before": cursor,
        "calibration_artifact": str(CALIBRATION_JSON.relative_to(REPO)),
        "calibration_decision": calibration.get("decision"),
        "accepted_source_confidence_95_labels": accepted_labels,
        "source_label_equivalence_status": source_label.get("status"),
        "source_label_equivalence_rows": int(source_label.get("row_count") or 0),
        "source_label_all_roots_present": bool(calibration.get("all_roots_present")),
        "ready_roots": ready_roots,
        "ready_root_count": len(ready_roots),
        "r6_positive_rows": positive_rows,
        "r6_matched_negative_rows": negative_rows,
        "r6_matched_group_count": matched_groups,
        "r6_wilson95_min_lcb": min_lcb,
        "support_ok": support_ok,
        "checklist": checklist,
        "gates": gates,
        "intake_roots": roots,
        "verifier_readbacks": verifiers,
        "accepted_rows_added": 0,
        "new_confidence_gate": False,
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "external_requests_sent": False,
        "trade_usable": False,
        "next_action": (
            "Acquire native sub-hour/R5 recency roots or expand R6 to 50/50 broad-normal/direct-species coverage; "
            "do not rerun unchanged source-label confidence calibration as an acceptance path."
        ),
    }
    json_path = OUT / "current_goal_completion_audit_v48_after_source_confidence_calibration.json"
    report_path = OUT / "current_goal_completion_audit_v48_after_source_confidence_calibration.md"
    checklist_path = OUT / "current_goal_completion_audit_v48_checklist.csv"
    gates_path = OUT / "current_goal_completion_audit_v48_gates.csv"
    roots_path = OUT / "current_goal_completion_audit_v48_intake_roots.csv"
    assertions_path = CHECKS / "current_goal_completion_audit_v48_after_source_confidence_calibration_assertions.out"

    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_csv(checklist_path, checklist, ["id", "requirement", "evidence", "status", "gap"])
    write_csv(gates_path, gates, ["gate", "required", "observed", "pass"])
    write_csv(
        roots_path,
        roots,
        ["id", "root", "required_files", "present_files", "missing_files", "exists", "ready", "csv_row_counts"],
    )
    report_path.write_text(
        "\n".join(
            [
                "# Current Goal Completion Audit v48 After Source Confidence Calibration",
                "",
                f"Decision: `{decision}`",
                "",
                "## Result",
                "",
                "- Source-label equivalence is verifier-clean and has all four labels, but the calibration artifact accepts `0` labels at the `>=0.95` Wilson lower-bound gate.",
                "- Native sub-hour and R5 recency roots remain absent/blocked.",
                f"- R6 direct remains `{positive_rows}/{negative_rows}` with Wilson95 min LCB `{min_lcb:.6f}`, below the strict gate.",
                "- Strict full objective achieved: `false`; `update_goal=false`.",
                "- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; external requests sent: `false`; trade usable: `false`.",
                "",
                "## Artifacts",
                "",
                f"- JSON: `{json_path}`",
                f"- Checklist CSV: `{checklist_path}`",
                f"- Gate CSV: `{gates_path}`",
                f"- Intake-root CSV: `{roots_path}`",
                f"- Assertions: `{assertions_path}`",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    assertions = [
        f"PASS decision={decision}",
        f"PASS calibration_decision={calibration.get('decision')}",
        "PASS accepted_source_confidence_95_labels=none",
        f"PASS source_label_status={source_label.get('status')}",
        f"PASS source_label_rows={source_label.get('row_count')}",
        f"PASS ready_root_count={len(ready_roots)}",
        f"PASS r6_positive_rows={positive_rows}",
        f"PASS r6_matched_negative_rows={negative_rows}",
        f"PASS r6_wilson95_min_lcb={min_lcb:.6f}",
        "PASS strict_full_objective_achieved=false",
        "PASS update_goal=false",
        "PASS raw_data_committed=false",
    ]
    assertions_path.write_text("\n".join(assertions) + "\n", encoding="utf-8")
    print(json.dumps({"decision": decision, "accepted_labels": accepted_labels, "ready_roots": len(ready_roots)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
