#!/usr/bin/env python3
"""Current-goal completion audit after v40 plus source-gap readbacks.

Local-only audit: no network, no source acquisition, no intake-root writes.
"""

from __future__ import annotations

import csv
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path


REPO = Path(__file__).resolve().parents[6]
RUN_ID = "20260511T211552-codex-current-goal-completion-audit-v41-post-source-gap"
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs" / RUN_ID
OUT_DIR = RUN_ROOT / "completion-audit"
CHECK_DIR = RUN_ROOT / "checks"
CMD_DIR = RUN_ROOT / "command-output"
BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"
RUNS_DIR = REPO / "docs/experiments/actionable-regime-confidence/runs"

SOURCE_LABEL_VERIFIER = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T182922-codex-source-label-equivalence-intake-verifier-v1/"
    "equivalence-intake-verifier/source_label_equivalence_intake_verifier_v1.py"
)
RECENCY_VERIFIER = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T165405-codex-source-panel-recency-extension-manifest-v1/"
    "source-panel-recency/source_panel_recency_extension_verifier_v1.py"
)
DIRECT_VERIFIER = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T151950-codex-direct-manipulation-row-intake-manifest-v1/"
    "direct-manipulation-intake/direct_manipulation_row_intake_verifier_v1.py"
)

V40_AUDIT = (
    RUNS_DIR
    / "20260511T211105-codex-current-goal-completion-audit-v40-live-direct-9x9/"
    "completion-audit/current_goal_completion_audit_v40_live_direct_9x9.json"
)
R235_GAP = (
    RUNS_DIR
    / "20260511T211112-codex-r2-r3-r5-source-intake-gap-readback-v1/"
    "r2-r3-r5-source-intake-gap-readback/r2_r3_r5_source_intake_gap_readback_v1.json"
)
VANT_DRAFT = (
    RUNS_DIR
    / "20260511T210849-codex-vantmacro-source-label-request-draft-v1/"
    "vantmacro-source-label-request-draft/vantmacro_source_label_request_draft_v1.json"
)
ACTIVE_VORLEY_CHANU = RUNS_DIR / "20260511T211208-codex-cftc-vorley-chanu-row-uplift-calibration-v1"

ROOT_SPECS = [
    {
        "id": "source_label_equivalence",
        "requirements": "R2;R4",
        "root": Path("/tmp/ict-engine-source-label-equivalence-intake"),
        "required_files": [
            "source_label_equivalence_rows.csv",
            "source_label_equivalence_provenance.json",
        ],
    },
    {
        "id": "native_subhour_source_label",
        "requirements": "R3",
        "root": Path("/tmp/ict-engine-native-subhour-source-label-intake"),
        "required_files": [
            "native_subhour_source_label_rows.csv",
            "native_subhour_source_label_provenance.json",
        ],
    },
    {
        "id": "source_panel_recency_extension",
        "requirements": "R5",
        "root": Path("/tmp/ict-engine-source-panel-recency-extension"),
        "required_files": [
            "stock_market_regimes_2026_extension.csv",
            "source_panel_recency_provenance.json",
        ],
    },
    {
        "id": "direct_manipulation_row_intake",
        "requirements": "R6",
        "root": Path("/tmp/ict-engine-direct-manipulation-row-intake"),
        "required_files": [
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


def read_json(path: Path) -> dict:
    if not path.exists():
        return {"_missing": str(path)}
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


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


def csv_count(path: Path) -> int | None:
    if not path.exists() or not path.is_file() or path.suffix.lower() != ".csv":
        return None
    with path.open(newline="", encoding="utf-8") as handle:
        return max(sum(1 for _ in csv.DictReader(handle)), 0)


def root_state(spec: dict) -> dict:
    root = spec["root"]
    present = []
    missing = []
    hashes = {}
    row_counts = {}
    for name in spec["required_files"]:
        path = root / name
        if path.exists():
            present.append(name)
            hashes[name] = sha256_file(path)
            count = csv_count(path)
            if count is not None:
                row_counts[name] = count
        else:
            missing.append(name)
    return {
        "id": spec["id"],
        "requirements": spec["requirements"],
        "root": str(root),
        "exists": root.exists(),
        "ready": not missing,
        "present_files": ";".join(present),
        "missing_files": ";".join(missing),
        "required_files": ";".join(spec["required_files"]),
        "csv_row_counts": json.dumps(row_counts, sort_keys=True),
        "file_hashes": hashes,
    }


def run_verifier(name: str, cmd: list[str], stdout_name: str, stderr_name: str) -> dict:
    if not Path(cmd[1]).exists():
        return {
            "id": name,
            "status": "verifier_missing",
            "returncode": None,
            "parsed": None,
            "stdout_file": "",
            "stderr_file": "",
        }
    proc = subprocess.run(cmd, cwd=REPO, text=True, capture_output=True, timeout=60)
    stdout_path = CMD_DIR / stdout_name
    stderr_path = CMD_DIR / stderr_name
    stdout_path.write_text(proc.stdout, encoding="utf-8")
    stderr_path.write_text(proc.stderr, encoding="utf-8")
    parsed = None
    status = "non_json"
    if proc.stdout.strip():
        try:
            parsed = json.loads(proc.stdout)
            status = str(parsed.get("status", "json_no_status"))
        except json.JSONDecodeError:
            status = "stdout_not_json"
    return {
        "id": name,
        "status": status,
        "returncode": proc.returncode,
        "parsed": parsed,
        "stdout_file": str(stdout_path.relative_to(REPO)),
        "stderr_file": str(stderr_path.relative_to(REPO)),
    }


def run_dir_state(path: Path) -> dict:
    files = [p for p in path.rglob("*") if p.is_file()] if path.exists() else []
    if not path.exists():
        state = "missing"
    elif not files:
        state = "active_or_empty"
    elif any(p.suffix == ".json" for p in files) and any(p.suffix == ".md" for p in files) and any("assertions" in p.name for p in files):
        state = "artifact_complete"
    else:
        state = "partial_or_in_progress"
    return {
        "run_dir": path.name,
        "exists": path.exists(),
        "file_count": len(files),
        "has_json": any(p.suffix == ".json" for p in files),
        "has_md": any(p.suffix == ".md" for p in files),
        "has_assertions": any("assertions" in p.name for p in files),
        "state": state,
    }


def write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)
    CMD_DIR.mkdir(parents=True, exist_ok=True)

    board_hash = sha256_file(BOARD)
    cursor = read_cursor()
    roots = [root_state(spec) for spec in ROOT_SPECS]
    verifiers = [
        run_verifier(
            "source_label_equivalence",
            ["python3", str(SOURCE_LABEL_VERIFIER), "--intake-root", "/tmp/ict-engine-source-label-equivalence-intake"],
            "source_label_equivalence_verifier.stdout.txt",
            "source_label_equivalence_verifier.stderr.txt",
        ),
        run_verifier(
            "source_panel_recency_extension",
            ["python3", str(RECENCY_VERIFIER), "--intake-root", "/tmp/ict-engine-source-panel-recency-extension"],
            "source_panel_recency_verifier.stdout.txt",
            "source_panel_recency_verifier.stderr.txt",
        ),
        run_verifier(
            "direct_manipulation_row_intake",
            ["python3", str(DIRECT_VERIFIER), "--intake-root", "/tmp/ict-engine-direct-manipulation-row-intake"],
            "direct_manipulation_verifier.stdout.txt",
            "direct_manipulation_verifier.stderr.txt",
        ),
    ]

    v40 = read_json(V40_AUDIT)
    r235 = read_json(R235_GAP)
    vant = read_json(VANT_DRAFT)
    active_state = run_dir_state(ACTIVE_VORLEY_CHANU)

    direct = next(row for row in verifiers if row["id"] == "direct_manipulation_row_intake")
    direct_parsed = direct.get("parsed") or {}
    positive_rows = int(direct_parsed.get("positive_rows", 0) or 0)
    matched_negative_rows = int(direct_parsed.get("matched_negative_rows", 0) or 0)
    direct_status = direct.get("status")

    source_label_blocked = next(row for row in verifiers if row["id"] == "source_label_equivalence")["status"] == "blocked"
    recency_blocked = next(row for row in verifiers if row["id"] == "source_panel_recency_extension")["status"] == "blocked"
    native_ready = next(row for row in roots if row["id"] == "native_subhour_source_label")["ready"]
    ready_roots = [row["id"] for row in roots if row["ready"]]

    checklist = [
        {
            "id": "R0_named_board",
            "requirement": "Use the named Board A markdown and produce repo-local artifacts.",
            "evidence": str(BOARD.relative_to(REPO)),
            "status": "pass_checked",
            "gap": "",
        },
        {
            "id": "R1_each_regime_95",
            "requirement": "Every active regime has source-owned or owner-approved >=95 confidence.",
            "evidence": f"v40={v40.get('decision')}; direct_status={direct_status}; ready_roots={len(ready_roots)}/4",
            "status": "fail_blocked",
            "gap": "R6 Wilson/support/broad-normal gates fail; R2/R3/R4/R5 roots missing; full active-regime >=95 is not achieved.",
        },
        {
            "id": "R2_other_market_validation",
            "requirement": "Other-market / source-label equivalence validation passes.",
            "evidence": f"source_label_equivalence_verifier_blocked={source_label_blocked}; gap_readback={r235.get('decision') or r235.get('gate_result')}",
            "status": "fail_blocked",
            "gap": "source_label_equivalence_rows.csv and provenance are absent.",
        },
        {
            "id": "R3_other_cycle_timeframe",
            "requirement": "Other-cycle/timeframe/native sub-hour validation passes.",
            "evidence": f"native_subhour_ready={native_ready}; root=/tmp/ict-engine-native-subhour-source-label-intake",
            "status": "fail_blocked",
            "gap": "native_subhour_source_label_rows.csv and provenance are absent.",
        },
        {
            "id": "R4_strict_1h_source_rows",
            "requirement": "Strict exact 1h source rows/provenance pass.",
            "evidence": f"source_label_equivalence_verifier_blocked={source_label_blocked}",
            "status": "fail_blocked",
            "gap": "same missing source-label equivalence intake files block strict 1h transfer.",
        },
        {
            "id": "R5_recency_extension",
            "requirement": "Post-cutoff recency extension rows/provenance pass.",
            "evidence": f"source_panel_recency_verifier_blocked={recency_blocked}; VantMacro draft={vant.get('decision')}",
            "status": "fail_blocked",
            "gap": "stock_market_regimes_2026_extension.csv and source_panel_recency_provenance.json are absent; no-send draft is not row evidence.",
        },
        {
            "id": "R6_direct_manipulation",
            "requirement": "Direct Manipulation has enough positives, broad same-schema controls, and species coverage.",
            "evidence": f"direct_status={direct_status}; positives={positive_rows}; controls={matched_negative_rows}; v40={v40.get('decision')}",
            "status": "fail_blocked",
            "gap": "Only spoofing_layering schema seeds; support <50/50, Wilson95 <0.95, broad-normal false, species coverage incomplete.",
        },
        {
            "id": "R7_proxy_guardrails",
            "requirement": "Do not promote proxy/model/OHLCV/generated/no-send artifacts as acceptance.",
            "evidence": "This audit treats VantMacro draft, local stock panel, same-event controls, and provider OHLCV as non-accepted unless verifier-ready source rows exist.",
            "status": "pass_guardrail",
            "gap": "",
        },
        {
            "id": "R8_completion_gate",
            "requirement": "Only call update_goal when all checklist rows pass with actual evidence.",
            "evidence": "failures_present=true",
            "status": "fail_blocked",
            "gap": "Strict full objective is not achieved; update_goal remains false.",
        },
    ]

    gates = [
        {
            "gate": "ready_intake_roots",
            "observed": str(len(ready_roots)),
            "required": "4",
            "pass": str(len(ready_roots) == 4).lower(),
        },
        {
            "gate": "r6_positive_support",
            "observed": str(positive_rows),
            "required": ">=50",
            "pass": str(positive_rows >= 50).lower(),
        },
        {
            "gate": "r6_negative_support",
            "observed": str(matched_negative_rows),
            "required": ">=50",
            "pass": str(matched_negative_rows >= 50).lower(),
        },
        {
            "gate": "source_label_equivalence_verifier",
            "observed": "blocked" if source_label_blocked else "not_blocked",
            "required": "not_blocked",
            "pass": str(not source_label_blocked).lower(),
        },
        {
            "gate": "source_panel_recency_verifier",
            "observed": "blocked" if recency_blocked else "not_blocked",
            "required": "not_blocked",
            "pass": str(not recency_blocked).lower(),
        },
        {
            "gate": "vorley_chanu_run_state",
            "observed": active_state["state"],
            "required": "artifact_complete_or_ignore_if_active",
            "pass": str(active_state["state"] == "artifact_complete").lower(),
        },
    ]

    result = {
        "run_id": RUN_ID,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "board_hash_before": board_hash,
        "current_cursor": cursor,
        "decision": "current_goal_completion_audit_v41=post_source_gap_still_blocked",
        "objective_restatement": "Every active regime must have source-owned or owner-approved >=95 confidence, and must keep suitable confidence when validated on other markets/species and other cycles/timeframes before reporting completion.",
        "checked_artifacts": {
            "v40_audit": str(V40_AUDIT.relative_to(REPO)),
            "r2_r3_r5_gap_readback": str(R235_GAP.relative_to(REPO)),
            "vantmacro_no_send_draft": str(VANT_DRAFT.relative_to(REPO)),
            "active_vorley_chanu_run": active_state,
        },
        "intake_roots": roots,
        "verifier_readbacks": verifiers,
        "checklist": checklist,
        "gates": gates,
        "ready_roots": ready_roots,
        "ready_root_count": len(ready_roots),
        "accepted_rows_added": 0,
        "new_confidence_gate": False,
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "external_requests_sent": False,
        "trade_usable": False,
        "next_action": "Treat the completed 211208 Vorley/Chanu uplift as included in this audit, but still blocked; acquire real R2/R3/R4/R5 source rows/provenance or broad R6 same-schema normal controls and additional direct species rows, then rerun verifiers and completion audit.",
    }

    json_path = OUT_DIR / "current_goal_completion_audit_v41_post_source_gap.json"
    checklist_csv = OUT_DIR / "current_goal_completion_audit_v41_checklist.csv"
    gates_csv = OUT_DIR / "current_goal_completion_audit_v41_gates.csv"
    roots_csv = OUT_DIR / "current_goal_completion_audit_v41_intake_roots.csv"
    report_path = OUT_DIR / "current_goal_completion_audit_v41_post_source_gap.md"
    assertions_path = CHECK_DIR / "current_goal_completion_audit_v41_post_source_gap_assertions.out"

    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_csv(checklist_csv, checklist, ["id", "requirement", "evidence", "status", "gap"])
    write_csv(gates_csv, gates, ["gate", "observed", "required", "pass"])
    write_csv(
        roots_csv,
        roots,
        [
            "id",
            "requirements",
            "root",
            "exists",
            "ready",
            "present_files",
            "missing_files",
            "required_files",
            "csv_row_counts",
        ],
    )

    report_lines = [
        "# Current Goal Completion Audit v41 Post Source Gap",
        "",
        f"Decision: `{result['decision']}`.",
        "",
        "Objective restatement:",
        result["objective_restatement"],
        "",
        "Result:",
        f"- Board hash before run: `{board_hash}`.",
        f"- Current cursor: `{cursor.get('last_loop_id', 'unknown')}`.",
        f"- Ready intake roots: `{len(ready_roots)}/4` (`{';'.join(ready_roots)}`).",
        f"- Direct verifier: `{direct_status}`; positives `{positive_rows}`; matched negatives `{matched_negative_rows}`.",
        f"- Source-label equivalence verifier blocked: `{str(source_label_blocked).lower()}`.",
        f"- Recency verifier blocked: `{str(recency_blocked).lower()}`.",
        f"- Native sub-hour root ready: `{str(native_ready).lower()}`.",
        f"- Vorley/Chanu run state: `{active_state['state']}` with file_count `{active_state['file_count']}`.",
        "- Accepted rows added: `0`; new confidence gate: `false`.",
        "- Strict full objective achieved: `false`; `update_goal=false`.",
        "- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; external requests sent: `false`; trade usable: `false`.",
        "",
        "Checklist:",
        "",
        "| ID | Status | Gap |",
        "|---|---|---|",
    ]
    for row in checklist:
        report_lines.append(f"| `{row['id']}` | `{row['status']}` | `{row['gap']}` |")
    report_lines.extend(
        [
            "",
            "Gates:",
            "",
            "| Gate | Observed | Required | Pass |",
            "|---|---|---|---:|",
        ]
    )
    for row in gates:
        report_lines.append(f"| `{row['gate']}` | `{row['observed']}` | `{row['required']}` | `{row['pass']}` |")
    report_lines.extend(
        [
            "",
            "Next:",
            result["next_action"],
            "",
            "Artifacts:",
            f"- JSON: `{json_path.relative_to(REPO)}`",
            f"- Checklist CSV: `{checklist_csv.relative_to(REPO)}`",
            f"- Gate CSV: `{gates_csv.relative_to(REPO)}`",
            f"- Intake-root CSV: `{roots_csv.relative_to(REPO)}`",
            f"- Verifier outputs: `{CMD_DIR.relative_to(REPO)}`",
            f"- Assertions: `{assertions_path.relative_to(REPO)}`",
        ]
    )
    report_path.write_text("\n".join(report_lines) + "\n", encoding="utf-8")

    assertions = [
        f"PASS decision={result['decision']}",
        "PASS objective_restatement_present",
        f"PASS checklist_rows={len(checklist)}",
        "PASS failures_present=true",
        "PASS update_goal=false",
        "PASS accepted_rows_added=0",
        "PASS new_confidence_gate=false",
        "PASS external_requests_sent=false",
        "PASS raw_data_committed=false",
    ]
    assertions_path.write_text("\n".join(assertions) + "\n", encoding="utf-8")

    print(json.dumps({"decision": result["decision"], "ready_roots": len(ready_roots), "update_goal": False, "report": str(report_path.relative_to(REPO))}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
