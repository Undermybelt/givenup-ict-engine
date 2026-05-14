#!/usr/bin/env python3
"""Strict current-goal audit after the R6 duplicate cleanup."""

from __future__ import annotations

import csv
import hashlib
import json
import math
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


RUN_ID = "20260511T212256-codex-current-goal-completion-audit-v42-after-duplicate-cleanup"
REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = Path(__file__).resolve().parents[1]
OUT = RUN_ROOT / "completion-audit"
CHECKS = RUN_ROOT / "checks"
CMD_OUT = RUN_ROOT / "command-output"
BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"

SOURCE_LABEL_VERIFIER = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T182922-codex-source-label-equivalence-intake-verifier-v1/"
    "equivalence-intake-verifier/source_label_equivalence_intake_verifier_v1.py"
)
RECENCY_VERIFIER = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T165405-codex-source-panel-recency-extension-manifest-v1/"
    "source-panel-recency/source_panel_recency_extension_verifier_v1.py"
)
DIRECT_VERIFIER = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T151950-codex-direct-manipulation-row-intake-manifest-v1/"
    "direct-manipulation-intake/direct_manipulation_row_intake_verifier_v1.py"
)

ROOT_SPECS = [
    ("R2_R4_source_label_equivalence", Path("/tmp/ict-engine-source-label-equivalence-intake"), ["source_label_equivalence_rows.csv", "source_label_equivalence_provenance.json"]),
    ("R3_native_subhour_source_label", Path("/tmp/ict-engine-native-subhour-source-label-intake"), ["native_subhour_source_label_rows.csv", "native_subhour_source_label_provenance.json"]),
    ("R5_source_panel_recency_extension", Path("/tmp/ict-engine-source-panel-recency-extension"), ["stock_market_regimes_2026_extension.csv", "source_panel_recency_provenance.json"]),
    ("R6_direct_manipulation_row_intake", Path("/tmp/ict-engine-direct-manipulation-row-intake"), ["positive_spoofing_layering_rows.csv", "matched_negative_normal_activity_rows.csv", "provenance_manifest.json"]),
]


def sha256(path: Path) -> str:
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
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def csv_count(path: Path) -> int | None:
    if not path.exists() or path.suffix.lower() != ".csv":
        return None
    return len(read_csv(path))


def root_state(root_id: str, root: Path, required_files: list[str]) -> dict[str, Any]:
    present = []
    missing = []
    row_counts: dict[str, int] = {}
    hashes: dict[str, str] = {}
    for filename in required_files:
        path = root / filename
        if path.exists():
            present.append(filename)
            hashes[filename] = sha256(path)
            count = csv_count(path)
            if count is not None:
                row_counts[filename] = count
        else:
            missing.append(filename)
    return {
        "root_id": root_id,
        "root": str(root),
        "exists": root.exists(),
        "ready": not missing,
        "present_files": ";".join(present),
        "missing_files": ";".join(missing),
        "row_counts": json.dumps(row_counts, sort_keys=True),
        "hashes": hashes,
    }


def run_verifier(name: str, cmd: list[str], stdout_name: str, stderr_name: str) -> dict[str, Any]:
    proc = subprocess.run(cmd, cwd=REPO, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=90, check=False)
    stdout_path = CMD_OUT / stdout_name
    stderr_path = CMD_OUT / stderr_name
    stdout_path.write_text(proc.stdout, encoding="utf-8")
    stderr_path.write_text(proc.stderr, encoding="utf-8")
    parsed: dict[str, Any] | None = None
    status = "stdout_not_json"
    if proc.stdout.strip():
        try:
            parsed = json.loads(proc.stdout)
            status = str(parsed.get("status", "json_no_status"))
        except json.JSONDecodeError:
            pass
    return {
        "name": name,
        "status": status,
        "returncode": proc.returncode,
        "parsed": parsed,
        "stdout": str(stdout_path.relative_to(REPO)),
        "stderr": str(stderr_path.relative_to(REPO)),
    }


def wilson_lcb(successes: int, total: int, z: float = 1.959963984540054) -> float:
    if total <= 0:
        return 0.0
    phat = successes / total
    denom = 1 + z * z / total
    centre = phat + z * z / (2 * total)
    margin = z * math.sqrt((phat * (1 - phat) + z * z / (4 * total)) / total)
    return (centre - margin) / denom


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)
    CMD_OUT.mkdir(parents=True, exist_ok=True)

    board_hash = sha256(BOARD)
    cursor = read_cursor()
    roots = [root_state(*spec) for spec in ROOT_SPECS]
    source_label = run_verifier(
        "source_label_equivalence",
        ["python3", str(SOURCE_LABEL_VERIFIER), "--intake-root", "/tmp/ict-engine-source-label-equivalence-intake"],
        "source_label_equivalence_verifier.stdout.txt",
        "source_label_equivalence_verifier.stderr.txt",
    )
    recency = run_verifier(
        "source_panel_recency_extension",
        ["python3", str(RECENCY_VERIFIER), "--intake-root", "/tmp/ict-engine-source-panel-recency-extension"],
        "source_panel_recency_verifier.stdout.txt",
        "source_panel_recency_verifier.stderr.txt",
    )
    direct = run_verifier(
        "direct_manipulation_row_intake",
        ["python3", str(DIRECT_VERIFIER), "--intake-root", "/tmp/ict-engine-direct-manipulation-row-intake"],
        "direct_manipulation_verifier.stdout.txt",
        "direct_manipulation_verifier.stderr.txt",
    )
    verifiers = [source_label, recency, direct]

    direct_root = Path("/tmp/ict-engine-direct-manipulation-row-intake")
    positives = read_csv(direct_root / "positive_spoofing_layering_rows.csv")
    negatives = read_csv(direct_root / "matched_negative_normal_activity_rows.csv")
    provenance = json.loads((direct_root / "provenance_manifest.json").read_text(encoding="utf-8"))
    dates = sorted({row["trade_date"] for row in positives + negatives if row.get("trade_date")})
    symbols = sorted({row["symbol"] for row in positives + negatives if row.get("symbol")})
    venues = sorted({row["venue_or_market_center"] for row in positives + negatives if row.get("venue_or_market_center")})
    direct_lcb = min(wilson_lcb(len(positives), len(positives)), wilson_lcb(len(negatives), len(negatives)))
    direct_support_ok = len(positives) >= 50 and len(negatives) >= 50
    direct_broad_normal = "not a broad normal-market" not in provenance.get("matched_negative_control_policy", "").lower()

    gates = [
        {"requirement": "R1 active-regime confidence", "observed": cursor.get("confidence_lane", ""), "required": "all active regimes >=95 source-owned/owner-approved", "pass": False},
        {"requirement": "R2 other-market/source-label equivalence", "observed": next(r for r in roots if r["root_id"] == "R2_R4_source_label_equivalence")["missing_files"], "required": "required files present", "pass": False},
        {"requirement": "R3 other-cycle/native-subhour validation", "observed": next(r for r in roots if r["root_id"] == "R3_native_subhour_source_label")["missing_files"], "required": "required files present", "pass": False},
        {"requirement": "R5 source-panel recency extension", "observed": next(r for r in roots if r["root_id"] == "R5_source_panel_recency_extension")["missing_files"], "required": "required files present", "pass": False},
        {"requirement": "R6 direct support", "observed": f"{len(positives)}/{len(negatives)}", "required": ">=50/50", "pass": direct_support_ok},
        {"requirement": "R6 direct Wilson95", "observed": f"{direct_lcb:.6f}", "required": ">=0.95", "pass": direct_lcb >= 0.95},
        {"requirement": "R6 broad normal sample", "observed": provenance.get("matched_negative_control_policy", ""), "required": "broad source-owned normal controls", "pass": direct_broad_normal},
        {"requirement": "R8 completion gate", "observed": "blocked gates remain", "required": "all rows pass", "pass": False},
    ]
    decision = "current_goal_completion_audit_v42=duplicate_cleanup_still_blocked"

    result = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "board_hash_before_artifact_generation": board_hash,
        "decision": decision,
        "cursor": cursor,
        "intake_roots": roots,
        "verifiers": verifiers,
        "direct_metrics": {
            "positive_rows": len(positives),
            "matched_negative_rows": len(negatives),
            "unique_dates": len(dates),
            "unique_symbols": len(symbols),
            "unique_venues": len(venues),
            "wilson95_min_lcb": direct_lcb,
            "support_ok": direct_support_ok,
            "broad_normal_sample": direct_broad_normal,
        },
        "gates": gates,
        "blocked_count": sum(1 for row in gates if not row["pass"]),
        "accepted_rows_added": 0,
        "new_confidence_gate": False,
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "external_requests_sent": False,
        "trade_usable": False,
    }

    json_path = OUT / "current_goal_completion_audit_v42_after_duplicate_cleanup.json"
    report_path = OUT / "current_goal_completion_audit_v42_after_duplicate_cleanup.md"
    gates_csv = OUT / "current_goal_completion_audit_v42_gates.csv"
    roots_csv = OUT / "current_goal_completion_audit_v42_intake_roots.csv"
    assertions = CHECKS / "current_goal_completion_audit_v42_after_duplicate_cleanup_assertions.out"
    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_csv(gates_csv, gates, ["requirement", "observed", "required", "pass"])
    write_csv(roots_csv, roots, ["root_id", "root", "exists", "ready", "present_files", "missing_files", "row_counts"])

    lines = [
        "# Current Goal Completion Audit v42 After Duplicate Cleanup",
        "",
        f"- Decision: `{decision}`.",
        f"- Current cursor: `{cursor.get('last_loop_id', '')}`.",
        f"- Direct R6 rows after cleanup: positive `{len(positives)}`, matched negative `{len(negatives)}`.",
        f"- Direct R6 Wilson95 min LCB: `{direct_lcb:.6f}`; support ok: `{str(direct_support_ok).lower()}`; broad normal sample: `{str(direct_broad_normal).lower()}`.",
        f"- Ready intake roots: `{sum(1 for row in roots if row['ready'])}/4`.",
        f"- Blocked audit rows: `{sum(1 for row in gates if not row['pass'])}/{len(gates)}`.",
        "- Strict full objective achieved: `false`; `update_goal=false`.",
        "- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; external requests sent: `false`; trade usable: `false`.",
        "",
        "## Gates",
        "",
        "| Requirement | Observed | Required | Pass |",
        "|---|---|---|---:|",
    ]
    for row in gates:
        lines.append(f"| `{row['requirement']}` | `{row['observed']}` | `{row['required']}` | `{str(row['pass']).lower()}` |")
    lines.extend(
        [
            "",
            "## Artifacts",
            "",
            f"- JSON: `{json_path.relative_to(REPO)}`",
            f"- Gate CSV: `{gates_csv.relative_to(REPO)}`",
            f"- Intake-root CSV: `{roots_csv.relative_to(REPO)}`",
            f"- Verifier outputs: `{CMD_OUT.relative_to(REPO)}`",
            f"- Assertions: `{assertions.relative_to(REPO)}`",
        ]
    )
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    assertion_lines = [
        f"PASS decision={decision}",
        f"PASS direct_positive_rows={len(positives)}",
        f"PASS direct_matched_negative_rows={len(negatives)}",
        f"PASS direct_wilson95_min_lcb={direct_lcb:.6f}",
        f"PASS ready_intake_roots={sum(1 for row in roots if row['ready'])}/4",
        f"PASS blocked_count={sum(1 for row in gates if not row['pass'])}",
        "PASS strict_full_objective_achieved=false",
        "PASS update_goal=false",
    ]
    assertions.write_text("\n".join(assertion_lines) + "\n", encoding="utf-8")
    print(json.dumps({"decision": decision, "blocked_count": result["blocked_count"], "update_goal": False}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
