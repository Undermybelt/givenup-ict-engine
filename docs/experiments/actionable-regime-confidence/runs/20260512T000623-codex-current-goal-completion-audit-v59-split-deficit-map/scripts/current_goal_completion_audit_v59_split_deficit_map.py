#!/usr/bin/env python3
"""Current-goal audit plus R6 split/species deficit map.

This is an evidence/readback slice. It does not mutate the R6 intake, relax
thresholds, or claim Board A completion.
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
from typing import Any


RUN_ID = "20260512T000623-codex-current-goal-completion-audit-v59-split-deficit-map"
REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs" / RUN_ID
OUT = RUN_ROOT / "completion-audit"
CMD = RUN_ROOT / "command-output"
CHECKS = RUN_ROOT / "checks"
STATE_DIR = RUN_ROOT / "state_v59"
BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"

LIVE_R6_ROOT = Path("/tmp/ict-engine-direct-manipulation-row-intake")
DIRECT_VERIFIER = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs"
    / "20260511T151950-codex-direct-manipulation-row-intake-manifest-v1"
    / "direct-manipulation-intake/direct_manipulation_row_intake_verifier_v1.py"
)
V58_ROOT = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs"
    / "20260511T235815-codex-r6-live-intake-rehydrate-calibration-v1"
    / "r6-live-intake-rehydrate-calibration"
)
V58_JSON = V58_ROOT / "r6_live_intake_rehydrate_calibration_v1.json"
V58_SPLIT_METRICS = V58_ROOT / "r6_live_intake_rehydrate_split_metrics_v1.csv"
V58_SIDECAR_METRICS = V58_ROOT / "r6_live_intake_rehydrate_sidecar_metrics_v1.csv"
V58_POSITIVE = V58_ROOT / "positive_spoofing_layering_rows_v1.csv"
V58_NEGATIVE = V58_ROOT / "matched_negative_normal_activity_rows_v1.csv"

Z95 = 1.959963984540054
MIN_WILSON = 0.95
MIN_SUPPORT = 50
STRICT_ROOTS = ["Bull", "Bear", "Sideways", "Crisis", "DirectOverlay::Manipulation"]
MISSING_DIRECT_SPECIES = [
    "quote_stuffing",
    "pinging",
    "bear_raid_or_painting_tape",
    "pump_dump_social_text_or_onchain",
]


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO))
    except ValueError:
        return str(path)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def wilson_all_success_lcb(n: int) -> float:
    if n <= 0:
        return 0.0
    denominator = 1.0 + Z95 * Z95 / n
    center = 1.0 + Z95 * Z95 / (2.0 * n)
    margin = Z95 * math.sqrt(Z95 * Z95 / (4.0 * n * n))
    return (center - margin) / denominator


def min_all_success_count_for_lcb(target: float = MIN_WILSON) -> int:
    n = 1
    while wilson_all_success_lcb(n) < target:
        n += 1
    return n


def run_command(name: str, args: list[str], timeout: int = 120) -> dict[str, Any]:
    result = subprocess.run(
        args,
        cwd=REPO,
        text=True,
        capture_output=True,
        timeout=timeout,
        check=False,
    )
    stdout_path = CMD / f"{name}.stdout.txt"
    stderr_path = CMD / f"{name}.stderr.txt"
    exit_path = CMD / f"{name}.exit"
    stdout_path.write_text(result.stdout, encoding="utf-8")
    stderr_path.write_text(result.stderr, encoding="utf-8")
    exit_path.write_text(f"{result.returncode}\n", encoding="utf-8")
    parsed: Any
    try:
        parsed = json.loads(result.stdout)
    except json.JSONDecodeError:
        parsed = {"json_parse": "failed", "stdout_sample": result.stdout[:1200]}
    return {
        "name": name,
        "args": args,
        "returncode": result.returncode,
        "stdout_path": rel(stdout_path),
        "stderr_path": rel(stderr_path),
        "exit_path": rel(exit_path),
        "parsed": parsed,
    }


def command_summary(command: dict[str, Any]) -> str:
    parsed = command.get("parsed")
    if isinstance(parsed, dict):
        for key in ("status", "gate_result", "workflow_status", "triage_status"):
            if parsed.get(key):
                return str(parsed[key])
        if isinstance(parsed.get("summary"), str):
            return parsed["summary"]
        if isinstance(parsed.get("execution_triage"), dict) and parsed["execution_triage"].get("status"):
            return str(parsed["execution_triage"]["status"])
    return f"returncode={command['returncode']}"


def split_deficits(split_rows: list[dict[str, str]], min_n: int) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in split_rows:
        pos = int(row["positive_support"])
        neg = int(row["negative_support"])
        rows.append(
            {
                "split_family": row["split_family"],
                "split_name": row["split_name"],
                "positive_support": pos,
                "negative_support": neg,
                "min_wilson95_lcb": row["min_wilson95_lcb"],
                "current_pass": row["pass"],
                "positive_rows_needed_to_95": max(0, min_n - pos),
                "negative_rows_needed_to_95": max(0, min_n - neg),
                "pair_rows_needed_to_95": max(max(0, min_n - pos), max(0, min_n - neg)),
                "guidance": deficit_guidance(row["split_family"], row["split_name"], pos, neg, min_n),
            }
        )
    return rows


def deficit_guidance(family: str, name: str, pos: int, neg: int, min_n: int) -> str:
    if family == "pooled_all_source_rows":
        return "pooled axis already passes; do not optimize for more aggregate rows alone"
    if family == "chronological_group_split":
        return "add date-diverse positive/control groups that land in this chronological role after recomputing splits"
    if family == "heldout_symbol_exact":
        if pos == 0 or neg == 0:
            return "avoid adding more of this exact symbol unless both positive and control rows can be brought toward the 95 gate"
        return "only concentrated same-symbol row families move this exact-symbol gate"
    if family == "heldout_venue_exact":
        return "only concentrated same-venue row families move this exact-venue gate"
    return f"need all-success support >= {min_n}"


def aggregate_deficits(deficits: list[dict[str, Any]]) -> dict[str, Any]:
    by_family: dict[str, list[dict[str, Any]]] = {}
    for row in deficits:
        by_family.setdefault(row["split_family"], []).append(row)
    out: dict[str, Any] = {}
    for family, rows in by_family.items():
        failing = [row for row in rows if str(row["current_pass"]).lower() != "true"]
        out[family] = {
            "buckets": len(rows),
            "failing_buckets": len(failing),
            "max_pair_rows_needed_for_one_bucket": max((row["pair_rows_needed_to_95"] for row in rows), default=0),
            "sum_pair_rows_needed_if_all_current_buckets_must_pass": sum(row["pair_rows_needed_to_95"] for row in failing),
            "best_current_bucket": min(rows, key=lambda row: row["pair_rows_needed_to_95"])["split_name"] if rows else "",
            "best_current_bucket_pair_rows_needed": min((row["pair_rows_needed_to_95"] for row in rows), default=0),
        }
    return out


def species_rows(positive_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    labels = Counter(row.get("label", "") for row in positive_rows)
    source_reports = Counter(row.get("source_report", "") for row in positive_rows)
    rows = [
        {
            "species_or_label": label,
            "positive_rows": count,
            "status": "present",
            "note": "current verifier schema labels these as spoofing/layering positives",
        }
        for label, count in sorted(labels.items())
    ]
    for species in MISSING_DIRECT_SPECIES:
        rows.append(
            {
                "species_or_label": species,
                "positive_rows": 0,
                "status": "missing",
                "note": "required for direct-species breadth; not closed by spoofing/layering rows",
            }
        )
    rows.append(
        {
            "species_or_label": "distinct_source_reports",
            "positive_rows": len(source_reports),
            "status": "diagnostic",
            "note": "; ".join(f"{name}={count}" for name, count in source_reports.most_common(8)),
        }
    )
    return rows


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    CMD.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)
    STATE_DIR.mkdir(parents=True, exist_ok=True)

    board_hash = sha256(BOARD)
    min_n = min_all_success_count_for_lcb()
    required_inputs = [DIRECT_VERIFIER, V58_JSON, V58_SPLIT_METRICS, V58_SIDECAR_METRICS, V58_POSITIVE, V58_NEGATIVE]
    missing = [rel(path) for path in required_inputs if not path.exists()]
    if missing:
        payload = {
            "run_id": RUN_ID,
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "board_sha256_at_start": board_hash,
            "status": "blocked",
            "reason": "missing_required_inputs",
            "missing": missing,
            "update_goal": False,
        }
        write_json(OUT / "current_goal_completion_audit_v59_split_deficit_map.json", payload)
        return 2

    commands = [
        run_command("direct_manipulation_row_intake_verifier", ["python3", str(DIRECT_VERIFIER), "--intake-root", str(LIVE_R6_ROOT)]),
        run_command("provider_status_agent", ["./target/debug/ict-engine", "provider-status", "--agent"]),
        run_command("auto_quant_status", ["./target/debug/ict-engine", "auto-quant-status", "--state-dir", str(STATE_DIR), "--output-format", "json"]),
        run_command("analyze_demo", ["./target/debug/ict-engine", "analyze", "--symbol", "DEMO", "--demo", "--state-dir", str(STATE_DIR), "--output-format", "json"]),
        run_command("pre_bayes_status", ["./target/debug/ict-engine", "pre-bayes-status", "--symbol", "DEMO", "--state-dir", str(STATE_DIR), "--refresh", "--output-format", "json"]),
        run_command("policy_training_status", ["./target/debug/ict-engine", "policy-training-status", "--symbol", "DEMO", "--state-dir", str(STATE_DIR), "--output-format", "json"]),
        run_command("workflow_status_execution_candidate", ["./target/debug/ict-engine", "workflow-status", "--symbol", "DEMO", "--state-dir", str(STATE_DIR), "--refresh", "--phase", "execution-candidate", "--output-format", "json"]),
        run_command("export_structural_path_ranking_target", ["./target/debug/ict-engine", "export-structural-path-ranking-target", "--symbol", "DEMO", "--state-dir", str(STATE_DIR)]),
    ]

    v58 = json.loads(V58_JSON.read_text(encoding="utf-8"))
    split_rows = read_csv(V58_SPLIT_METRICS)
    positive_rows = read_csv(V58_POSITIVE)
    deficits = split_deficits(split_rows, min_n)
    deficit_summary = aggregate_deficits(deficits)
    species = species_rows(positive_rows)

    command_csv = OUT / "current_goal_completion_audit_v59_commands.csv"
    deficit_csv = OUT / "r6_split_deficit_map_v59.csv"
    species_csv = OUT / "r6_direct_species_deficit_v59.csv"
    checklist_csv = OUT / "current_goal_completion_audit_v59_checklist.csv"
    write_csv(
        command_csv,
        [
            {
                "name": command["name"],
                "returncode": command["returncode"],
                "summary": command_summary(command),
                "stdout_path": command["stdout_path"],
                "stderr_path": command["stderr_path"],
            }
            for command in commands
        ],
        ["name", "returncode", "summary", "stdout_path", "stderr_path"],
    )
    write_csv(
        deficit_csv,
        deficits,
        [
            "split_family",
            "split_name",
            "positive_support",
            "negative_support",
            "min_wilson95_lcb",
            "current_pass",
            "positive_rows_needed_to_95",
            "negative_rows_needed_to_95",
            "pair_rows_needed_to_95",
            "guidance",
        ],
    )
    write_csv(species_csv, species, ["species_or_label", "positive_rows", "status", "note"])

    direct_payload = commands[0]["parsed"] if isinstance(commands[0].get("parsed"), dict) else {}
    command_returncodes = {command["name"]: command["returncode"] for command in commands}
    all_commands_ran = all(code == 0 for code in command_returncodes.values())
    r6_live_verified = (
        commands[0]["returncode"] == 0
        and direct_payload.get("status") == "schema_ready_unscored"
        and direct_payload.get("positive_rows") == 73
        and direct_payload.get("matched_negative_rows") == 73
    )
    direct_calibration = v58.get("direct_calibration", {})
    sidecar_calibration = v58.get("sidecar_calibration", {})
    decision = v58.get("decision", {})
    r6_pooled_pass = bool(direct_calibration.get("pooled_min_wilson95_lcb", 0) >= MIN_WILSON)
    split_blocked = not bool(direct_calibration.get("chronological_split_gate")) or not bool(direct_calibration.get("heldout_symbol_gate")) or not bool(direct_calibration.get("heldout_venue_gate"))
    strict_complete = False

    checklist = [
        {
            "requirement": "Board file is the authoritative plan",
            "evidence": rel(BOARD),
            "status": "pass",
            "gap": "",
        },
        {
            "requirement": "Every active regime reaches calibrated 95-99 confidence",
            "evidence": "Current Cursor full_objective_gate=none; V58 decision update_goal=false",
            "status": "blocked",
            "gap": "Strict full objective remains blocked; do not call update_goal.",
        },
        {
            "requirement": "Cross-market and cross-timeframe validation",
            "evidence": rel(V58_SPLIT_METRICS),
            "status": "blocked",
            "gap": "R6 chronological/symbol/venue split gates are false.",
        },
        {
            "requirement": "Direct Manipulation uses direct event/order-lifecycle rows, not OHLCV proxies",
            "evidence": f"live verifier status={direct_payload.get('status')}; rows={direct_payload.get('positive_rows')}/{direct_payload.get('matched_negative_rows')}",
            "status": "pass",
            "gap": "",
        },
        {
            "requirement": "Direct Manipulation species breadth",
            "evidence": rel(species_csv),
            "status": "blocked",
            "gap": "Only spoofing/layering label is present; non-spoofing species remain missing.",
        },
        {
            "requirement": "Provider and downstream chain readback: IBKR, TradingViewRemix, yfinance, Kraken, Auto-Quant, pre-Bayes/BBN, CatBoost/path-ranker, execution tree",
            "evidence": rel(command_csv),
            "status": "partial",
            "gap": "Commands were run, but provider/runtime surfaces remain context only and do not close split/species/R5/R3 gates.",
        },
        {
            "requirement": "No proxy signal accepted as completion",
            "evidence": f"r6_pooled_pass={r6_pooled_pass}; split_blocked={split_blocked}; strict_complete={strict_complete}",
            "status": "pass",
            "gap": "",
        },
        {
            "requirement": "Multi-agent safe board updates",
            "evidence": f"board_sha256_at_start={board_hash}; append-only section planned",
            "status": "pass",
            "gap": "",
        },
    ]
    write_csv(checklist_csv, checklist, ["requirement", "evidence", "status", "gap"])

    result = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "board_sha256_at_start": board_hash,
        "objective_restatement": {
            "deliverables": [
                "Each active regime has 95-99 calibrated confidence.",
                "Evidence validates across other markets and timeframes.",
                "Provider/Auto-Quant/pre-Bayes/BBN/CatBoost/execution-tree chain is exercised with IBKR, TradingViewRemix, yfinance, and Kraken surfaces visible.",
                "All findings are written back into the same Board A markdown without disrupting concurrent work.",
            ]
        },
        "minimum_all_success_rows_for_wilson95_ge_095": min_n,
        "v58_live_readback": {
            "json": rel(V58_JSON),
            "gate_result": decision.get("gate_result"),
            "positive_rows": direct_payload.get("positive_rows"),
            "matched_negative_rows": direct_payload.get("matched_negative_rows"),
            "pooled_min_wilson95_lcb": direct_calibration.get("pooled_min_wilson95_lcb"),
            "sidecar_broad_normal_lcb": sidecar_calibration.get("broad_normal_wilson95_lcb"),
            "chronological_split_gate": direct_calibration.get("chronological_split_gate"),
            "heldout_symbol_gate": direct_calibration.get("heldout_symbol_gate"),
            "heldout_venue_gate": direct_calibration.get("heldout_venue_gate"),
            "strict_full_objective_achieved": decision.get("strict_full_objective_achieved"),
            "update_goal": decision.get("update_goal"),
        },
        "split_deficit_summary": deficit_summary,
        "command_returncodes": command_returncodes,
        "all_commands_returned_zero": all_commands_ran,
        "r6_live_verified": r6_live_verified,
        "r6_pooled_wilson_pass": r6_pooled_pass,
        "r6_split_gates_blocked": split_blocked,
        "direct_species_closed": False,
        "source_label_confidence_accepted_roots": "0/4 from Current Cursor",
        "r5_post_2026_01_30_source_panel_rows": "absent from Current Cursor",
        "r3_native_subhour_root": "absent from Current Cursor",
        "checklist_csv": rel(checklist_csv),
        "deficit_csv": rel(deficit_csv),
        "species_csv": rel(species_csv),
        "command_csv": rel(command_csv),
        "gate_result": "current_goal_completion_audit_v59=not_complete_r6_split_species_r5_r3_blocked",
        "strict_full_objective_achieved": strict_complete,
        "update_goal": False,
        "new_confidence_gate": False,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "trade_usable": False,
        "next_action": (
            "Acquire direct event/order-lifecycle rows that deliberately fill chronological calibration/test "
            "support and concentrate on existing exact symbols/venues, while adding missing non-spoofing "
            "direct species; rerun V58 calibration and keep R5/R3 blocked."
        ),
    }

    json_path = OUT / "current_goal_completion_audit_v59_split_deficit_map.json"
    report_path = OUT / "current_goal_completion_audit_v59_split_deficit_map.md"
    write_json(json_path, result)
    report_lines = [
        "# Current Goal Completion Audit v59 Split Deficit Map",
        "",
        f"- Run id: `{RUN_ID}`",
        f"- Board hash at start: `{board_hash}`",
        f"- Minimum all-success rows for Wilson95 >= 0.95: `{min_n}`.",
        f"- Live R6 verifier: `{direct_payload.get('status')}` with positives `{direct_payload.get('positive_rows')}` and controls `{direct_payload.get('matched_negative_rows')}`.",
        f"- R6 pooled Wilson gate: `{str(r6_pooled_pass).lower()}`.",
        f"- R6 split gates blocked: `{str(split_blocked).lower()}`.",
        f"- Direct species closed: `false`.",
        f"- Provider/downstream commands all returned zero: `{str(all_commands_ran).lower()}`.",
        f"- Gate result: `{result['gate_result']}`.",
        "- Strict full objective achieved: `false`; `update_goal=false`.",
        "",
        "## Key Deficits",
        f"- Chronological split supports are train/calibration/test `38/17/18`; fixed-role deficits to Wilson95 are `35/56/55` paired rows.",
        f"- Best exact-symbol bucket still needs `{deficit_summary['heldout_symbol_exact']['best_current_bucket_pair_rows_needed']}` paired rows; all current exact-symbol buckets would require `{deficit_summary['heldout_symbol_exact']['sum_pair_rows_needed_if_all_current_buckets_must_pass']}` paired rows if this all-bucket gate is retained.",
        f"- Best exact-venue bucket still needs `{deficit_summary['heldout_venue_exact']['best_current_bucket_pair_rows_needed']}` paired rows; all current exact-venue buckets would require `{deficit_summary['heldout_venue_exact']['sum_pair_rows_needed_if_all_current_buckets_must_pass']}` paired rows if this all-bucket gate is retained.",
        "- Missing direct species remain: `quote_stuffing`, `pinging`, `bear_raid_or_painting_tape`, and `pump_dump_social_text_or_onchain`.",
        "",
        "## Artifacts",
        f"- JSON: `{rel(json_path)}`",
        f"- Checklist: `{rel(checklist_csv)}`",
        f"- Split deficit CSV: `{rel(deficit_csv)}`",
        f"- Species deficit CSV: `{rel(species_csv)}`",
        f"- Command manifest: `{rel(command_csv)}`",
        "",
        "## Next",
        result["next_action"],
        "",
    ]
    report_path.write_text("\n".join(report_lines), encoding="utf-8")
    assertions = [
        ("direct_verifier_schema_ready", r6_live_verified),
        ("pooled_wilson_pass_present", r6_pooled_pass),
        ("split_gates_blocked", split_blocked),
        ("direct_species_not_closed", not result["direct_species_closed"]),
        ("strict_full_objective_not_complete", not strict_complete),
        ("update_goal_false", not result["update_goal"]),
        ("deficit_csv_written", deficit_csv.exists()),
        ("checklist_written", checklist_csv.exists()),
    ]
    assertion_path = CHECKS / "current_goal_completion_audit_v59_split_deficit_map_assertions.out"
    assertion_path.write_text(
        "\n".join(f"{name}={'ok' if passed else 'FAIL'}" for name, passed in assertions) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"ok": all(passed for _, passed in assertions), "gate_result": result["gate_result"], "update_goal": False}, indent=2))
    return 0 if all(passed for _, passed in assertions) else 2


if __name__ == "__main__":
    raise SystemExit(main())
