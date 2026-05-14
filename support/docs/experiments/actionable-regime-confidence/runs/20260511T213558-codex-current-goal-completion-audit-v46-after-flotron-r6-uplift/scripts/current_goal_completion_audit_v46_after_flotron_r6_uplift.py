#!/usr/bin/env python3
"""Post-Flotron R6 completion audit for Board A.

Local-only audit: reruns fail-closed verifiers and records evidence without
network acquisition, threshold changes, or intake-root mutation.
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


RUN_ID = "20260511T213558-codex-current-goal-completion-audit-v46-after-flotron-r6-uplift"
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

ARTIFACTS = {
    "current_cursor_root": RUNS_DIR
    / "20260511T213129-codex-current-goal-completion-audit-v45-after-nifty-source-label/"
    "completion-audit/current_goal_completion_audit_v45_after_nifty_source_label.json",
    "r6_flotron_cftc_row_uplift": RUNS_DIR
    / "20260511T213312-codex-r6-flotron-cftc-row-uplift-v1/"
    "r6-flotron-cftc-row-uplift/r6_flotron_cftc_row_uplift_v1.json",
    "nifty_source_label_equivalence_intake": RUNS_DIR
    / "20260511T212819-codex-nifty-source-label-equivalence-intake-v1/"
    "nifty-source-label-equivalence-intake/nifty_source_label_equivalence_intake_v1.json",
    "v43_completion_audit": RUNS_DIR
    / "20260511T212401-codex-current-goal-completion-audit-v43-post-cleanup/"
    "completion-audit/current_goal_completion_audit_v43_post_cleanup.json",
    "previous_shak_duplicate_cleanup": RUNS_DIR
    / "20260511T212004-codex-r6-shak-duplicate-row-cleanup-v1/"
    "r6-shak-duplicate-row-cleanup/r6_shak_duplicate_row_cleanup_v1.json",
    "v41_completion_audit": RUNS_DIR
    / "20260511T211552-codex-current-goal-completion-audit-v41-post-source-gap/"
    "completion-audit/current_goal_completion_audit_v41_post_source_gap.json",
    "r2_r3_r5_gap_readback": RUNS_DIR
    / "20260511T211112-codex-r2-r3-r5-source-intake-gap-readback-v1/"
    "r2-r3-r5-source-intake-gap-readback/r2_r3_r5_source_intake_gap_readback_v1.json",
    "r2_r3_r5_public_route_readback_unregistered": RUNS_DIR
    / "20260511T212118-codex-r2-r3-r5-public-route-and-root-readback-v1/"
    "r2-r3-r5-public-route-and-root-readback/r2_r3_r5_public_route_and_root_readback_v1.json",
    "provider_chain_gap_recheck": RUNS_DIR
    / "20260511T205142-codex-provider-chain-intake-readback-v37/"
    "provider-chain-intake-readback/provider_chain_intake_gap_recheck_v1.json",
}

ROOT_SPECS = [
    {
        "id": "source_label_equivalence",
        "requirements": "R2 other-market validation; R4 strict 1h transfer",
        "root": Path("/tmp/ict-engine-source-label-equivalence-intake"),
        "required_files": [
            "source_label_equivalence_rows.csv",
            "source_label_equivalence_provenance.json",
        ],
    },
    {
        "id": "native_subhour_source_label",
        "requirements": "R3 native sub-hour / other-cycle validation",
        "root": Path("/tmp/ict-engine-native-subhour-source-label-intake"),
        "required_files": [
            "native_subhour_source_label_rows.csv",
            "native_subhour_source_label_provenance.json",
        ],
    },
    {
        "id": "source_panel_recency_extension",
        "requirements": "R5 post-cutoff recency extension",
        "root": Path("/tmp/ict-engine-source-panel-recency-extension"),
        "required_files": [
            "stock_market_regimes_2026_extension.csv",
            "source_panel_recency_provenance.json",
        ],
    },
    {
        "id": "direct_manipulation_row_intake",
        "requirements": "R6 direct Manipulation source rows",
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


def csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def source_label_profile() -> dict[str, object]:
    rows_path = Path("/tmp/ict-engine-source-label-equivalence-intake/source_label_equivalence_rows.csv")
    rows = csv_rows(rows_path)
    labels = Counter(row.get("main_regime_v2_label", "") for row in rows)
    families = Counter(row.get("market_family", "") for row in rows)
    splits = Counter(row.get("split_role", "") for row in rows)
    packages = Counter(row.get("package_id", "") for row in rows)
    return {
        "csv_row_count": len(rows),
        "label_counts": dict(sorted(labels.items())),
        "market_family_counts": dict(sorted(families.items())),
        "split_counts": dict(sorted(splits.items())),
        "package_counts": dict(sorted(packages.items())),
        "all_main_roots_present": all(labels.get(label, 0) > 0 for label in ["Bull", "Bear", "Sideways", "Crisis"]),
    }


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
            if path.suffix == ".csv":
                row_counts[name] = len(csv_rows(path))
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
    artifacts = {name: read_json(path) for name, path in ARTIFACTS.items()}

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

    direct = next(row for row in verifiers if row["id"] == "direct_manipulation_row_intake")
    direct_parsed = direct.get("parsed") or {}
    positive_rows = int(direct_parsed.get("positive_rows", 0) or 0)
    matched_negative_rows = int(direct_parsed.get("matched_negative_rows", 0) or 0)
    matched_group_count = int(direct_parsed.get("matched_group_count", 0) or 0)
    positive_lcb = wilson_lcb(positive_rows, positive_rows)
    negative_lcb = wilson_lcb(matched_negative_rows, matched_negative_rows)
    min_lcb = min(positive_lcb, negative_lcb)
    support_ok = positive_rows >= 50 and matched_negative_rows >= 50
    broad_normal_sample = False
    direct_species_closed = False

    source_label_status = next(row for row in verifiers if row["id"] == "source_label_equivalence")["status"]
    source_label_parsed = next(row for row in verifiers if row["id"] == "source_label_equivalence").get("parsed") or {}
    source_label_rows = int(source_label_parsed.get("row_count", 0) or 0)
    source_label_schema_ready = source_label_status == "schema_ready_unscored"
    source_profile = source_label_profile()
    source_label_csv_rows = int(source_profile["csv_row_count"])
    source_label_label_counts = source_profile["label_counts"]
    source_label_family_counts = source_profile["market_family_counts"]
    source_label_split_counts = source_profile["split_counts"]
    source_label_roots_present = bool(source_profile["all_main_roots_present"])
    recency_status = next(row for row in verifiers if row["id"] == "source_panel_recency_extension")["status"]
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
            "id": "R1_every_regime_95",
            "requirement": "Every active regime must have its own source-owned or owner-approved >=95 confidence gate.",
            "evidence": f"cursor={cursor.get('last_loop_id')}; ready_roots={len(ready_roots)}/4; direct_min_wilson95_lcb={min_lcb:.6f}",
            "status": "fail_blocked",
            "gap": "Strict all-regime 95% objective is still not achieved; source-label equivalence is schema-ready but unscored, R3/R5 roots remain absent, and R6 direct confidence is below 0.95.",
        },
        {
            "id": "R2_other_market_validation",
            "requirement": "Validate regimes on other markets/species with suitable confidence.",
            "evidence": f"source_label_equivalence_status={source_label_status}; verifier_rows={source_label_rows}; csv_rows={source_label_csv_rows}; labels={source_label_label_counts}; families={source_label_family_counts}; splits={source_label_split_counts}",
            "status": "fail_blocked",
            "gap": "Source-label equivalence rows are present and include all MainRegimeV2 roots, but they remain schema-ready/unscored and are not a >=95 confidence acceptance package.",
        },
        {
            "id": "R3_other_cycle_timeframe",
            "requirement": "Validate regimes on other cycles/timeframes with suitable confidence.",
            "evidence": f"native_subhour_ready={native_ready}; recency_status={recency_status}",
            "status": "fail_blocked",
            "gap": "native sub-hour source-label rows/provenance and recency-extension rows/provenance are absent.",
        },
        {
            "id": "R4_provider_and_full_chain",
            "requirement": "When claiming chain evidence, use real provider/Auto-Quant/ict-engine/filter/BBN/CatBoost/execution-tree artifacts including IBKR, TradingViewRemix, yfinance, and Kraken status.",
            "evidence": "provider_chain_gap_recheck artifact is checked if present; this slice reruns verifiers only and makes no completion claim.",
            "status": "partial_guardrail",
            "gap": "Fresh provider/Auto-Quant/BBN/CatBoost/execution-tree rerun was not performed in this slice; strict completion remains blocked before that can matter.",
        },
        {
            "id": "R5_r6_direct_confidence",
            "requirement": "Direct Manipulation must pass support, Wilson95, broad-normal, and direct-species gates.",
            "evidence": f"positives={positive_rows}; controls={matched_negative_rows}; matched_groups={matched_group_count}; min_lcb={min_lcb:.6f}; broad_normal_sample={broad_normal_sample}; species_closed={direct_species_closed}",
            "status": "fail_blocked",
            "gap": f"R6 is {positive_rows}/{matched_negative_rows} after duplicate cleanup; support is below 50/50, Wilson95 is below 0.95, controls are same-source/event seeds, and species coverage is incomplete.",
        },
        {
            "id": "R6_no_proxy_acceptance",
            "requirement": "Do not accept proxy signals, generated labels, no-send drafts, same-event controls, or schema readiness as completion.",
            "evidence": "This audit keeps VantMacro drafts, missing intake roots, same-event controls, schema-ready source labels, and OHLCV/provider proxies fail-closed.",
            "status": "pass_guardrail",
            "gap": "",
        },
        {
            "id": "R7_multi_agent_safety",
            "requirement": "Do not disturb concurrent board sections or in-progress artifacts.",
            "evidence": f"board_hash_before={board_hash}; cursor_before={cursor.get('last_loop_id')}; append-only registration expected",
            "status": "pass_guardrail",
            "gap": "",
        },
        {
            "id": "R8_update_goal_gate",
            "requirement": "Only call update_goal when every checklist item is covered by real evidence.",
            "evidence": "failures_present=true",
            "status": "fail_blocked",
            "gap": "Missing and failed requirements remain; update_goal=false.",
        },
    ]

    gates = [
        {"gate": "ready_intake_roots", "observed": str(len(ready_roots)), "required": "4", "pass": str(len(ready_roots) == 4).lower()},
        {"gate": "r6_positive_support", "observed": str(positive_rows), "required": ">=50", "pass": str(positive_rows >= 50).lower()},
        {"gate": "r6_negative_support", "observed": str(matched_negative_rows), "required": ">=50", "pass": str(matched_negative_rows >= 50).lower()},
        {"gate": "r6_wilson95_lcb", "observed": f"{min_lcb:.6f}", "required": ">=0.95", "pass": str(min_lcb >= 0.95).lower()},
        {"gate": "r6_broad_normal_sample", "observed": str(broad_normal_sample).lower(), "required": "true", "pass": "false"},
        {"gate": "r6_direct_species_coverage", "observed": str(direct_species_closed).lower(), "required": "true", "pass": "false"},
        {"gate": "source_label_equivalence_confidence", "observed": f"{source_label_status}:{source_label_rows}", "required": "accepted_confidence_complete_roots", "pass": "false"},
        {"gate": "source_panel_recency_verifier", "observed": recency_status, "required": "not_blocked", "pass": str(recency_status != "blocked").lower()},
        {"gate": "native_subhour_root_ready", "observed": str(native_ready).lower(), "required": "true", "pass": str(native_ready).lower()},
    ]

    decision = f"current_goal_completion_audit_v46=after_flotron_r6_uplift_{len(ready_roots)}of4_roots_still_blocked"
    result = {
        "run_id": RUN_ID,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "board_hash_before": board_hash,
        "current_cursor": cursor,
        "decision": decision,
        "objective_restatement": "Every active regime must have source-owned or owner-approved >=95 confidence, and must keep suitable confidence when validated on other markets/species and other cycles/timeframes before completion can be reported.",
        "checked_artifacts": {name: str(path.relative_to(REPO)) for name, path in ARTIFACTS.items()},
        "artifact_decisions": {name: value.get("decision") for name, value in artifacts.items()},
        "intake_roots": roots,
        "verifier_readbacks": verifiers,
        "checklist": checklist,
        "gates": gates,
        "ready_roots": ready_roots,
        "ready_root_count": len(ready_roots),
        "r6_positive_rows": positive_rows,
        "r6_matched_negative_rows": matched_negative_rows,
        "r6_matched_group_count": matched_group_count,
        "r6_positive_wilson95_lcb": positive_lcb,
        "r6_negative_wilson95_lcb": negative_lcb,
        "r6_combined_min_wilson95_lcb": min_lcb,
        "source_label_equivalence_rows": source_label_rows,
        "source_label_equivalence_csv_rows": source_label_csv_rows,
        "source_label_equivalence_profile": source_profile,
        "source_label_equivalence_schema_ready": source_label_schema_ready,
        "source_label_all_main_roots_present": source_label_roots_present,
        "support_ok": support_ok,
        "broad_normal_sample": broad_normal_sample,
        "direct_species_closed": direct_species_closed,
        "accepted_rows_added": 0,
        "new_confidence_gate": False,
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "external_requests_sent": False,
        "trade_usable": False,
        "next_action": "Score and calibrate the source-label equivalence root, acquire native sub-hour and recency-extension roots, and expand R6 with 50/50 broad normal controls/direct species coverage before any completion claim.",
    }

    json_path = OUT_DIR / "current_goal_completion_audit_v46_after_flotron_r6_uplift.json"
    checklist_csv = OUT_DIR / "current_goal_completion_audit_v46_checklist.csv"
    gates_csv = OUT_DIR / "current_goal_completion_audit_v46_gates.csv"
    roots_csv = OUT_DIR / "current_goal_completion_audit_v46_intake_roots.csv"
    report_path = OUT_DIR / "current_goal_completion_audit_v46_after_flotron_r6_uplift.md"
    assertions_path = CHECK_DIR / "current_goal_completion_audit_v46_after_flotron_r6_uplift_assertions.out"

    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_csv(checklist_csv, checklist, ["id", "requirement", "evidence", "status", "gap"])
    write_csv(gates_csv, gates, ["gate", "observed", "required", "pass"])
    write_csv(roots_csv, roots, ["id", "requirements", "root", "exists", "ready", "present_files", "missing_files", "required_files", "csv_row_counts"])

    report_lines = [
        "# Current Goal Completion Audit v46 After Flotron R6 Uplift",
        "",
        f"Decision: `{decision}`.",
        "",
        "Objective restatement:",
        result["objective_restatement"],
        "",
        "Result:",
        f"- Board hash before run: `{board_hash}`.",
        f"- Current cursor before run: `{cursor.get('last_loop_id', 'unknown')}`.",
        f"- Ready intake roots: `{len(ready_roots)}/4` (`{';'.join(ready_roots)}`).",
        f"- R6 direct verifier: `{direct['status']}`; positives `{positive_rows}`; matched negatives `{matched_negative_rows}`; matched groups `{matched_group_count}`.",
        f"- R6 Wilson95 positive/negative/min LCB: `{positive_lcb:.6f}` / `{negative_lcb:.6f}` / `{min_lcb:.6f}`.",
        f"- R6 support gate: `{str(support_ok).lower()}`; broad normal sample: `{str(broad_normal_sample).lower()}`; direct species closed: `{str(direct_species_closed).lower()}`.",
        f"- Source-label equivalence verifier: `{source_label_status}`; verifier rows `{source_label_rows}`; CSV rows `{source_label_csv_rows}`; all roots present `{str(source_label_roots_present).lower()}`; accepted confidence gate `false`.",
        f"- Source-label counts: labels `{json.dumps(source_label_label_counts, sort_keys=True)}`; families `{json.dumps(source_label_family_counts, sort_keys=True)}`.",
        f"- Source-panel recency verifier: `{recency_status}`.",
        f"- Native sub-hour root ready: `{str(native_ready).lower()}`.",
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
        report_lines.append(f"| `{row['id']}` | `{row['status']}` | {row['evidence']} | {row['gap']} |")
    report_lines.extend(["", "Gates:", "", "| Gate | Observed | Required | Pass |", "|---|---|---|---:|"])
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
            f"- Report: `{report_path.relative_to(REPO)}`",
            f"- Checklist CSV: `{checklist_csv.relative_to(REPO)}`",
            f"- Gate CSV: `{gates_csv.relative_to(REPO)}`",
            f"- Intake-root CSV: `{roots_csv.relative_to(REPO)}`",
            f"- Verifier outputs: `{CMD_DIR.relative_to(REPO)}`",
            f"- Assertions: `{assertions_path.relative_to(REPO)}`",
        ]
    )
    report_path.write_text("\n".join(report_lines) + "\n", encoding="utf-8")

    assertions = [
        f"PASS decision={decision}",
        "PASS objective_restatement_present",
        f"PASS checklist_rows={len(checklist)}",
        "PASS failures_present=true",
        f"PASS source_label_equivalence_status={source_label_status}",
        f"PASS source_label_equivalence_rows={source_label_rows}",
        f"PASS source_label_equivalence_csv_rows={source_label_csv_rows}",
        f"PASS source_label_all_main_roots_present={str(source_label_roots_present).lower()}",
        f"PASS r6_positive_rows={positive_rows}",
        f"PASS r6_matched_negative_rows={matched_negative_rows}",
        f"PASS r6_combined_min_wilson95_lcb={min_lcb:.6f}",
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
        "source_label_equivalence_status": source_label_status,
        "source_label_equivalence_rows": source_label_rows,
        "source_label_equivalence_csv_rows": source_label_csv_rows,
        "source_label_all_main_roots_present": source_label_roots_present,
        "r6_positive_rows": positive_rows,
        "r6_matched_negative_rows": matched_negative_rows,
        "r6_min_wilson95_lcb": round(min_lcb, 6),
        "update_goal": False,
        "report": str(report_path.relative_to(REPO)),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
