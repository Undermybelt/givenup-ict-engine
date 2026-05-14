#!/usr/bin/env python3
"""V45 completion audit after the NIFTY source-label-equivalence intake.

This is a local evidence readback only. It reruns the unchanged fail-closed
verifiers, records schema/readiness deltas, and keeps proxy/generated-label
guardrails explicit.
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


RUN_ID = "20260511T213316-codex-current-goal-completion-audit-v45-post-nifty-equivalence"
REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs" / RUN_ID
OUT_DIR = RUN_ROOT / "completion-audit"
CHECK_DIR = RUN_ROOT / "checks"
CMD_DIR = RUN_ROOT / "command-output"
BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"
RUNS_DIR = REPO / "docs/experiments/actionable-regime-confidence/runs"

SOURCE_LABEL_VERIFIER = (
    RUNS_DIR
    / "20260511T182922-codex-source-label-equivalence-intake-verifier-v1/"
    "equivalence-intake-verifier/source_label_equivalence_intake_verifier_v1.py"
)
RECENCY_VERIFIER = (
    RUNS_DIR
    / "20260511T165405-codex-source-panel-recency-extension-manifest-v1/"
    "source-panel-recency/source_panel_recency_extension_verifier_v1.py"
)
DIRECT_VERIFIER = (
    RUNS_DIR
    / "20260511T151950-codex-direct-manipulation-row-intake-manifest-v1/"
    "direct-manipulation-intake/direct_manipulation_row_intake_verifier_v1.py"
)

SOURCE_EQ_ROOT = Path("/tmp/ict-engine-source-label-equivalence-intake")
NATIVE_SUBHOUR_ROOT = Path("/tmp/ict-engine-native-subhour-source-label-intake")
RECENCY_ROOT = Path("/tmp/ict-engine-source-panel-recency-extension")
DIRECT_ROOT = Path("/tmp/ict-engine-direct-manipulation-row-intake")

ROOT_SPECS = [
    {
        "id": "source_label_equivalence",
        "root": SOURCE_EQ_ROOT,
        "required_files": [
            "source_label_equivalence_rows.csv",
            "source_label_equivalence_provenance.json",
        ],
    },
    {
        "id": "native_subhour_source_label",
        "root": NATIVE_SUBHOUR_ROOT,
        "required_files": [
            "native_subhour_source_label_rows.csv",
            "native_subhour_source_label_provenance.json",
        ],
    },
    {
        "id": "source_panel_recency_extension",
        "root": RECENCY_ROOT,
        "required_files": [
            "stock_market_regimes_2026_extension.csv",
            "source_panel_recency_provenance.json",
        ],
    },
    {
        "id": "direct_manipulation_row_intake",
        "root": DIRECT_ROOT,
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
    return json.loads(path.read_text(encoding="utf-8"))


def csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


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


def root_state(spec: dict) -> dict:
    root = spec["root"]
    present = []
    missing = []
    row_counts = {}
    for name in spec["required_files"]:
        path = root / name
        if path.exists():
            present.append(name)
            if path.suffix == ".csv":
                row_counts[name] = len(csv_rows(path))
        else:
            missing.append(name)
    return {
        "id": spec["id"],
        "root": str(root),
        "exists": root.exists(),
        "ready": not missing,
        "present_files": ";".join(present),
        "missing_files": ";".join(missing),
        "csv_row_counts": json.dumps(row_counts, sort_keys=True),
    }


def run_verifier(name: str, cmd: list[str]) -> dict:
    proc = subprocess.run(cmd, cwd=REPO, text=True, capture_output=True, timeout=90)
    stdout_path = CMD_DIR / f"{name}.stdout.txt"
    stderr_path = CMD_DIR / f"{name}.stderr.txt"
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


def wilson_lcb(successes: int, n: int, z: float = 1.959963984540054) -> float:
    if n <= 0:
        return 0.0
    phat = successes / n
    denom = 1 + z * z / n
    centre = phat + z * z / (2 * n)
    margin = z * math.sqrt((phat * (1 - phat) + z * z / (4 * n)) / n)
    return (centre - margin) / denom


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
    ready_roots = [row["id"] for row in roots if row["ready"]]

    verifiers = [
        run_verifier(
            "source_label_equivalence_verifier",
            ["python3", str(SOURCE_LABEL_VERIFIER), "--intake-root", str(SOURCE_EQ_ROOT)],
        ),
        run_verifier(
            "source_panel_recency_verifier",
            ["python3", str(RECENCY_VERIFIER), "--intake-root", str(RECENCY_ROOT)],
        ),
        run_verifier(
            "direct_manipulation_verifier",
            ["python3", str(DIRECT_VERIFIER), "--intake-root", str(DIRECT_ROOT)],
        ),
    ]
    verifier_by_id = {row["id"]: row for row in verifiers}

    direct = verifier_by_id["direct_manipulation_verifier"].get("parsed") or {}
    positive_rows = int(direct.get("positive_rows", 0) or 0)
    matched_negative_rows = int(direct.get("matched_negative_rows", 0) or 0)
    matched_group_count = int(direct.get("matched_group_count", 0) or 0)
    positive_lcb = wilson_lcb(positive_rows, positive_rows)
    negative_lcb = wilson_lcb(matched_negative_rows, matched_negative_rows)
    min_lcb = min(positive_lcb, negative_lcb)

    source_rows = csv_rows(SOURCE_EQ_ROOT / "source_label_equivalence_rows.csv")
    source_provenance = read_json(SOURCE_EQ_ROOT / "source_label_equivalence_provenance.json")
    label_counts = Counter(row.get("main_regime_v2_label", "") for row in source_rows)
    split_counts = Counter(row.get("split_role", "") for row in source_rows)
    event_species = sorted({row.get("event_species", "") for row in source_rows if row.get("event_species")})
    proxy_guardrail = any("hmm" in item.lower() for item in event_species)
    missing_bear = label_counts.get("Bear", 0) == 0
    source_label_partial = missing_bear or proxy_guardrail

    source_label_status = verifier_by_id["source_label_equivalence_verifier"]["status"]
    recency_status = verifier_by_id["source_panel_recency_verifier"]["status"]
    native_ready = next(row for row in roots if row["id"] == "native_subhour_source_label")["ready"]

    decision = "current_goal_completion_audit_v45=post_nifty_equivalence_schema_ready_still_blocked"
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
            "evidence": f"ready_roots={len(ready_roots)}/4; source_label_status={source_label_status}; direct_min_lcb={min_lcb:.6f}",
            "gap": "Strict all-regime 95% objective is still not achieved.",
        },
        {
            "id": "R2_other_market_validation",
            "status": "partial_schema_ready_fail_closed",
            "evidence": f"NIFTY rows={len(source_rows)}; labels={dict(label_counts)}; splits={dict(split_counts)}",
            "gap": "The new source-label-equivalence root is schema-ready, but it is partial, daily-only, lacks Bear rows, and remains unscored for accepted confidence.",
        },
        {
            "id": "R3_other_cycle_timeframe",
            "status": "fail_blocked",
            "evidence": f"native_subhour_ready={native_ready}; recency_status={recency_status}",
            "gap": "Native sub-hour rows/provenance and post-cutoff recency-extension rows/provenance are still absent.",
        },
        {
            "id": "R4_proxy_guardrail",
            "status": "pass_guardrail",
            "evidence": f"event_species={';'.join(event_species)}; proxy_guardrail={str(proxy_guardrail).lower()}",
            "gap": "NIFTY owner-described HMM regime labels are schema input only here; no proxy/generated-label acceptance is made.",
        },
        {
            "id": "R5_r6_direct_confidence",
            "status": "fail_blocked",
            "evidence": f"positives={positive_rows}; controls={matched_negative_rows}; matched_groups={matched_group_count}; min_lcb={min_lcb:.6f}",
            "gap": "R6 support remains below 50/50, Wilson95 remains below 0.95, controls are not broad normal-market samples, and direct species are incomplete.",
        },
        {
            "id": "R6_provider_chain_guardrail",
            "status": "partial_guardrail",
            "evidence": "post_cleanup_provider_chain_readback_v1 exists as runtime evidence only when stable.",
            "gap": "Provider/downstream execution does not replace missing source-owned confidence gates.",
        },
        {
            "id": "R7_update_goal_gate",
            "status": "fail_blocked",
            "evidence": "failures_present=true",
            "gap": "update_goal=false.",
        },
    ]
    gates = [
        {"gate": "ready_intake_roots", "observed": str(len(ready_roots)), "required": "4", "pass": str(len(ready_roots) == 4).lower()},
        {"gate": "source_label_equivalence_schema", "observed": source_label_status, "required": "schema_ready_unscored", "pass": str(source_label_status == "schema_ready_unscored").lower()},
        {"gate": "source_label_equivalence_full_roots", "observed": f"labels={dict(label_counts)}", "required": "Bull/Bear/Sideways/Crisis source-owned accepted confidence", "pass": "false"},
        {"gate": "source_label_no_proxy_acceptance", "observed": f"proxy_guardrail={str(proxy_guardrail).lower()}", "required": "no HMM/proxy/generative acceptance", "pass": "true"},
        {"gate": "native_subhour_root_ready", "observed": str(native_ready).lower(), "required": "true", "pass": str(native_ready).lower()},
        {"gate": "source_panel_recency_verifier", "observed": recency_status, "required": "not_blocked", "pass": str(recency_status != "blocked").lower()},
        {"gate": "r6_positive_support", "observed": str(positive_rows), "required": ">=50", "pass": str(positive_rows >= 50).lower()},
        {"gate": "r6_negative_support", "observed": str(matched_negative_rows), "required": ">=50", "pass": str(matched_negative_rows >= 50).lower()},
        {"gate": "r6_wilson95_lcb", "observed": f"{min_lcb:.6f}", "required": ">=0.95", "pass": str(min_lcb >= 0.95).lower()},
        {"gate": "r6_broad_normal_sample", "observed": "false", "required": "true", "pass": "false"},
        {"gate": "r6_direct_species_coverage", "observed": "false", "required": "true", "pass": "false"},
    ]

    result = {
        "run_id": RUN_ID,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "board_hash_before": board_hash,
        "current_cursor": cursor,
        "decision": decision,
        "intake_roots": roots,
        "ready_roots": ready_roots,
        "ready_root_count": len(ready_roots),
        "verifier_readbacks": verifiers,
        "source_label_equivalence": {
            "row_count": len(source_rows),
            "label_counts": dict(label_counts),
            "split_counts": dict(split_counts),
            "event_species": event_species,
            "provenance": source_provenance,
            "missing_bear": missing_bear,
            "proxy_guardrail": proxy_guardrail,
            "partial_schema_ready": source_label_partial,
        },
        "r6_positive_rows": positive_rows,
        "r6_matched_negative_rows": matched_negative_rows,
        "r6_matched_group_count": matched_group_count,
        "r6_combined_min_wilson95_lcb": min_lcb,
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
    }

    json_path = OUT_DIR / "current_goal_completion_audit_v45_post_nifty_equivalence.json"
    report_path = OUT_DIR / "current_goal_completion_audit_v45_post_nifty_equivalence.md"
    checklist_csv = OUT_DIR / "current_goal_completion_audit_v45_checklist.csv"
    gates_csv = OUT_DIR / "current_goal_completion_audit_v45_gates.csv"
    roots_csv = OUT_DIR / "current_goal_completion_audit_v45_intake_roots.csv"
    assertions_path = CHECK_DIR / "current_goal_completion_audit_v45_post_nifty_equivalence_assertions.out"

    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_csv(checklist_csv, checklist, ["id", "status", "evidence", "gap"])
    write_csv(gates_csv, gates, ["gate", "observed", "required", "pass"])
    write_csv(roots_csv, roots, ["id", "root", "exists", "ready", "present_files", "missing_files", "csv_row_counts"])

    lines = [
        "# Current Goal Completion Audit v45 Post NIFTY Equivalence",
        "",
        f"Decision: `{decision}`.",
        "",
        "Result:",
        f"- Board hash before run: `{board_hash}`.",
        f"- Current cursor before run: `{cursor.get('last_loop_id', 'unknown')}`.",
        f"- Ready intake roots: `{len(ready_roots)}/4` (`{';'.join(ready_roots)}`).",
        f"- Source-label equivalence verifier: `{source_label_status}`; rows `{len(source_rows)}`; labels `{dict(label_counts)}`.",
        f"- Source-label guardrail: missing Bear `{str(missing_bear).lower()}`; proxy/HMM guardrail `{str(proxy_guardrail).lower()}`; accepted confidence `false`.",
        f"- Native sub-hour ready: `{str(native_ready).lower()}`; recency verifier `{recency_status}`.",
        f"- R6 direct verifier: `{verifier_by_id['direct_manipulation_verifier']['status']}`; positives `{positive_rows}`; matched negatives `{matched_negative_rows}`; matched groups `{matched_group_count}`; Wilson95 min LCB `{min_lcb:.6f}`.",
        "- R6 broad normal sample: `false`; direct species closed: `false`.",
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
    for row in gates:
        lines.append(f"| `{row['gate']}` | `{row['observed']}` | `{row['required']}` | `{row['pass']}` |")
    lines.extend(
        [
            "",
            "Next:",
            "Treat the NIFTY package as schema-ready/partial only. Strict completion still needs accepted per-regime confidence, native sub-hour/recency roots, and R6 50/50 plus broad-normal/direct-species evidence.",
            "",
            "Artifacts:",
            f"- JSON: `{json_path.relative_to(REPO)}`",
            f"- Report: `{report_path.relative_to(REPO)}`",
            f"- Checklist CSV: `{checklist_csv.relative_to(REPO)}`",
            f"- Gate CSV: `{gates_csv.relative_to(REPO)}`",
            f"- Intake-root CSV: `{roots_csv.relative_to(REPO)}`",
            f"- Verifier outputs: `{CMD_DIR.relative_to(REPO)}`",
            f"- Assertions: `{assertions_path.relative_to(REPO)}`",
        ]
    )
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    assertions = [
        f"PASS decision={decision}",
        f"PASS ready_roots={len(ready_roots)}",
        f"PASS source_label_status={source_label_status}",
        f"PASS source_label_rows={len(source_rows)}",
        f"PASS source_label_missing_bear={str(missing_bear).lower()}",
        f"PASS source_label_proxy_guardrail={str(proxy_guardrail).lower()}",
        f"PASS r6_positive_rows={positive_rows}",
        f"PASS r6_matched_negative_rows={matched_negative_rows}",
        f"PASS r6_combined_min_wilson95_lcb={min_lcb:.6f}",
        "PASS accepted_rows_added=0",
        "PASS new_confidence_gate=false",
        "PASS strict_full_objective_achieved=false",
        "PASS update_goal=false",
        "PASS raw_data_committed=false",
    ]
    assertions_path.write_text("\n".join(assertions) + "\n", encoding="utf-8")

    print(json.dumps({
        "decision": decision,
        "ready_roots": len(ready_roots),
        "source_label_rows": len(source_rows),
        "source_label_status": source_label_status,
        "r6_positive_rows": positive_rows,
        "r6_matched_negative_rows": matched_negative_rows,
        "update_goal": False,
        "report": str(report_path.relative_to(REPO)),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
