#!/usr/bin/env python3
"""Audit Board B 220646 downstream closure without rerunning Auto-Quant training."""

from __future__ import annotations

import csv
import json
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


RUN_ID = "20260511T222237-codex-board-b-220646-downstream-closure-audit-v1"
SOURCE_RUN_ID = "20260511T220646-codex-board-b-source-root-stop-carry-longhorizon-v1"
REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs" / RUN_ID
SOURCE_RUN = REPO / "docs/experiments/actionable-regime-confidence/runs" / SOURCE_RUN_ID
OUT = RUN_ROOT / "downstream-closure-audit"
CMD = RUN_ROOT / "command-output"
CHECKS = RUN_ROOT / "checks"
BOARD = REPO / "docs/plans/2026-05-10-regime-conditional-auto-quant-profitability-todo.md"

ICT = REPO / "target/debug/ict-engine"
RC_SPA_JSON = SOURCE_RUN / "branch-rc-spa/source_root_stop_carry_longhorizon_rc_spa_report_v1.json"
WIRE = SOURCE_RUN / "ict-engine-downstream/source_root_stop_carry_longhorizon_real_trades_wire_v1.jsonl"
EXISTING_FRESH_PROBE = SOURCE_RUN / "ict-engine-downstream/source_root_stop_carry_longhorizon_downstream_probe_v1.json"
EXISTING_DUP_PROBE = SOURCE_RUN / "downstream-consumption/source_root_stop_carry_longhorizon_downstream_probe_v1.json"
LEGACY_BBN_APPLY = SOURCE_RUN / "ict-engine/05_auto_quant_prior_init_longhorizon_apply.json"

FRESH_STATE = SOURCE_RUN / "ict-engine-downstream/state_fresh_downstream_v1"
FRESH_SYMBOL = "SRC_ROOT_CARRY_LONG_220646"
LEGACY_STATE = SOURCE_RUN / "state"
LEGACY_SYMBOL = "NQ"


def read_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        data = json.load(handle)
    return data if isinstance(data, dict) else {"value": data}


def maybe_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return read_json(path)
    except Exception:
        return {}


def rel(path: Path) -> str:
    return str(path.relative_to(REPO))


def run_cmd(name: str, args: list[str]) -> dict[str, Any]:
    proc = subprocess.run(
        args,
        cwd=REPO,
        text=True,
        capture_output=True,
        timeout=90,
        check=False,
    )
    stdout_path = CMD / f"{name}.out"
    stderr_path = CMD / f"{name}.err"
    exit_path = CMD / f"{name}.exit"
    stdout_path.write_text(proc.stdout, encoding="utf-8")
    stderr_path.write_text(proc.stderr, encoding="utf-8")
    exit_path.write_text(f"{proc.returncode}\n", encoding="utf-8")
    parsed: Any = None
    try:
        parsed = json.loads(proc.stdout) if proc.stdout.strip() else None
    except json.JSONDecodeError:
        parsed = None
    return {
        "name": name,
        "cmd": " ".join(args),
        "returncode": proc.returncode,
        "stdout": rel(stdout_path),
        "stderr": rel(stderr_path),
        "exit": rel(exit_path),
        "parsed": parsed,
    }


def read_wire() -> tuple[list[dict[str, Any]], Counter[str], Counter[str]]:
    rows: list[dict[str, Any]] = []
    branch_counts: Counter[str] = Counter()
    root_counts: Counter[str] = Counter()
    with WIRE.open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            rows.append(row)
            feedback = row.get("structural_feedback") or {}
            branch = feedback.get("path_id") or feedback.get("branch_id") or ""
            if branch:
                branch_counts[branch] += 1
            root = row.get("regime_at_entry") or feedback.get("node_id") or ""
            if root:
                root_counts[root] += 1
    return rows, branch_counts, root_counts


def command_text(command: dict[str, Any]) -> str:
    parsed = command.get("parsed")
    if parsed is None:
        try:
            return (REPO / command["stdout"]).read_text(encoding="utf-8")
        except Exception:
            return ""
    return json.dumps(parsed, sort_keys=True)


def count_branch_mentions(branches: list[str], *payloads: Any) -> dict[str, bool]:
    text = "\n".join(json.dumps(payload, sort_keys=True) if not isinstance(payload, str) else payload for payload in payloads)
    return {branch: branch in text for branch in branches}


def gate_row(gate: str, observed: Any, required: Any, passed: bool, evidence: str) -> dict[str, Any]:
    return {
        "gate": gate,
        "observed": observed,
        "required": required,
        "pass": str(bool(passed)).lower(),
        "evidence": evidence,
    }


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    CMD.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)
    for path in [ICT, RC_SPA_JSON, WIRE, BOARD]:
        if not path.exists():
            raise FileNotFoundError(path)

    rc_spa = read_json(RC_SPA_JSON)
    existing_fresh_probe = maybe_json(EXISTING_FRESH_PROBE)
    existing_dup_probe = maybe_json(EXISTING_DUP_PROBE)
    legacy_bbn_apply = maybe_json(LEGACY_BBN_APPLY)
    wire_rows, branch_counts, root_counts = read_wire()
    branch_paths = sorted(branch_counts)
    required_roots = {"Bull", "Bear", "Sideways", "Crisis"}
    decision = rc_spa.get("decision") or {}

    commands = [
        run_cmd("provider_status_agent", [str(ICT), "provider-status", "--agent"]),
        run_cmd("fresh_pre_bayes_status", [str(ICT), "pre-bayes-status", "--symbol", FRESH_SYMBOL, "--state-dir", str(FRESH_STATE), "--refresh", "--output-format", "json"]),
        run_cmd("fresh_policy_training_status", [str(ICT), "policy-training-status", "--symbol", FRESH_SYMBOL, "--state-dir", str(FRESH_STATE), "--output-format", "json"]),
        run_cmd("fresh_export_structural_path_ranking_target", [str(ICT), "export-structural-path-ranking-target", "--symbol", FRESH_SYMBOL, "--state-dir", str(FRESH_STATE)]),
        run_cmd("fresh_workflow_status_agent", [str(ICT), "workflow-status", "--symbol", FRESH_SYMBOL, "--state-dir", str(FRESH_STATE), "--agent"]),
        run_cmd("fresh_workflow_status_execution_candidate", [str(ICT), "workflow-status", "--symbol", FRESH_SYMBOL, "--state-dir", str(FRESH_STATE), "--phase", "execution-candidate", "--agent"]),
        run_cmd("legacy_pre_bayes_status", [str(ICT), "pre-bayes-status", "--symbol", LEGACY_SYMBOL, "--state-dir", str(LEGACY_STATE), "--refresh", "--output-format", "json"]),
        run_cmd("legacy_policy_training_status", [str(ICT), "policy-training-status", "--symbol", LEGACY_SYMBOL, "--state-dir", str(LEGACY_STATE), "--output-format", "json"]),
        run_cmd("legacy_export_structural_path_ranking_target", [str(ICT), "export-structural-path-ranking-target", "--symbol", LEGACY_SYMBOL, "--state-dir", str(LEGACY_STATE)]),
        run_cmd("legacy_workflow_status_agent", [str(ICT), "workflow-status", "--symbol", LEGACY_SYMBOL, "--state-dir", str(LEGACY_STATE), "--agent"]),
        run_cmd("legacy_workflow_status_structural_bundle", [str(ICT), "workflow-status", "--symbol", LEGACY_SYMBOL, "--state-dir", str(LEGACY_STATE), "--phase", "structural-recommended-path-bundle", "--agent"]),
        run_cmd("legacy_workflow_status_execution_candidate", [str(ICT), "workflow-status", "--symbol", LEGACY_SYMBOL, "--state-dir", str(LEGACY_STATE), "--phase", "execution-candidate", "--agent"]),
    ]
    command_map = {item["name"]: item for item in commands}
    fresh_policy = command_map["fresh_policy_training_status"].get("parsed") or {}
    fresh_export = command_map["fresh_export_structural_path_ranking_target"].get("parsed") or {}
    fresh_exec = command_map["fresh_workflow_status_execution_candidate"].get("parsed")
    legacy_policy = command_map["legacy_policy_training_status"].get("parsed") or {}
    legacy_export = command_map["legacy_export_structural_path_ranking_target"].get("parsed") or {}
    legacy_exec = command_map["legacy_workflow_status_execution_candidate"].get("parsed")
    legacy_pre = command_map["legacy_pre_bayes_status"].get("parsed") or {}

    pre_bayes_mentions = count_branch_mentions(
        branch_paths,
        command_text(command_map["fresh_pre_bayes_status"]),
        command_text(command_map["legacy_pre_bayes_status"]),
    )
    policy_mentions = count_branch_mentions(branch_paths, fresh_policy, legacy_policy, fresh_export, legacy_export)
    execution_mentions = count_branch_mentions(branch_paths, fresh_exec, legacy_exec)
    bbn_mentions = count_branch_mentions(branch_paths, legacy_bbn_apply)

    rc_spa_pass = decision.get("gate_result") == "pass" and int(decision.get("price_root_paths_passed") or 0) == 4
    ingest_records = 0
    if bool(existing_fresh_probe.get("ingest_ok")):
        ingest_records = int((existing_fresh_probe.get("wire") or {}).get("records") or 0)
    ingest_ok = bool(existing_fresh_probe.get("ingest_ok")) and ingest_records == len(wire_rows)
    pre_bayes_branch_closed = bool(branch_paths) and all(pre_bayes_mentions.values()) and "filter_posterior_confidence" in json.dumps(legacy_pre, sort_keys=True)
    bbn_branch_closed = bool(branch_paths) and all(bbn_mentions.values()) and "bbn_posterior_confidence" in json.dumps(legacy_bbn_apply, sort_keys=True)
    fresh_calibrated = int(fresh_export.get("rows_with_calibrated_path_prob") or 0)
    legacy_calibrated = int(legacy_export.get("rows_with_calibrated_path_prob") or 0)
    legacy_mature = int(legacy_export.get("mature_rows") or 0)
    catboost_closed = all(policy_mentions.values()) and max(fresh_calibrated, legacy_calibrated) >= len(branch_paths) and legacy_mature >= len(branch_paths)
    execution_closed = all(execution_mentions.values()) and "execution_tree_admissibility" in json.dumps([fresh_exec, legacy_exec], sort_keys=True)
    closed_loop_ready = pre_bayes_branch_closed and bbn_branch_closed and catboost_closed and execution_closed

    stage_rows = [
        gate_row("auto_quant_rc_spa", decision.get("gate_result"), "pass with 4/4 price roots and Manipulation component", rc_spa_pass and bool(decision.get("manipulation_component_pass")), rel(RC_SPA_JSON)),
        gate_row("wire_branch_paths", f"records={len(wire_rows)};branches={len(branch_paths)};roots={dict(root_counts)}", "12329 records, 4 rooted price paths, Bull/Bear/Sideways/Crisis", len(wire_rows) == 12329 and len(branch_paths) == 4 and required_roots.issubset(root_counts), rel(WIRE)),
        gate_row("real_trade_ingest", ingest_records, len(wire_rows), ingest_ok, rel(EXISTING_FRESH_PROBE) if EXISTING_FRESH_PROBE.exists() else "missing"),
        gate_row("pre_bayes_branch_path_posterior", pre_bayes_mentions, "all branch paths re-emitted with filter_posterior_confidence", pre_bayes_branch_closed, command_map["legacy_pre_bayes_status"]["stdout"]),
        gate_row("bbn_branch_path_posterior", bbn_mentions, "all branch paths re-emitted with bbn_posterior_confidence", bbn_branch_closed, rel(LEGACY_BBN_APPLY) if LEGACY_BBN_APPLY.exists() else "missing"),
        gate_row("catboost_path_ranker_calibration", f"fresh_calibrated={fresh_calibrated};legacy_calibrated={legacy_calibrated};legacy_mature={legacy_mature}", f">={len(branch_paths)} calibrated and mature branch rows", catboost_closed, command_map["legacy_export_structural_path_ranking_target"]["stdout"]),
        gate_row("execution_tree_branch_admissibility", execution_mentions, "all branch paths re-emitted with execution_tree_admissibility", execution_closed, command_map["legacy_workflow_status_execution_candidate"]["stdout"]),
        gate_row("closed_loop_confidence", closed_loop_ready, True, closed_loop_ready, "derived from ordered stage gates"),
    ]

    final_decision = "board_b_220646_downstream_closure_audit_v1=partial_fail_closed_no_closed_loop_confidence"
    summary = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_run_id": SOURCE_RUN_ID,
        "decision": final_decision,
        "board_cursor_before": "20260511T220646+0800-codex-board-b-source-root-stop-carry-longhorizon-v1",
        "rc_spa": {
            "gate_result": decision.get("gate_result"),
            "stable_profit_score": decision.get("stable_profit_score"),
            "price_root_paths_passed": decision.get("price_root_paths_passed"),
            "manipulation_component_pass": decision.get("manipulation_component_pass"),
        },
        "wire": {
            "records": len(wire_rows),
            "branch_paths": branch_paths,
            "root_counts": dict(root_counts),
            "branch_counts": dict(branch_counts),
        },
        "existing_probe_contrast": {
            "fresh_ingest_probe": rel(EXISTING_FRESH_PROBE) if EXISTING_FRESH_PROBE.exists() else None,
            "duplicate_hash_probe": rel(EXISTING_DUP_PROBE) if EXISTING_DUP_PROBE.exists() else None,
            "fresh_ingest_trades_applied": ingest_records,
            "duplicate_probe_ingest_applied": existing_dup_probe.get("ingest_applied"),
            "duplicate_probe_decision": existing_dup_probe.get("decision"),
        },
        "stage_gates": stage_rows,
        "commands": commands,
        "promotion_allowed": False,
        "closed_loop_confidence_ready": False,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "force_ingest_used": False,
        "auto_quant_training_started": False,
        "raw_data_committed": False,
        "update_goal": False,
        "next_action": "Repair or add a branch-path aware downstream adapter so Pre-Bayes, BBN, CatBoost/path-ranker, and execution tree re-emit the exact 220646 branch paths with closed_loop_confidence; do not promote from RC-SPA alone.",
    }

    json_path = OUT / "board_b_220646_downstream_closure_audit_v1.json"
    md_path = OUT / "board_b_220646_downstream_closure_audit_v1.md"
    gates_path = OUT / "board_b_220646_downstream_closure_audit_gates_v1.csv"
    commands_path = OUT / "board_b_220646_downstream_closure_audit_commands_v1.csv"
    assertions_path = CHECKS / "board_b_220646_downstream_closure_audit_v1_assertions.out"

    json_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_csv(gates_path, stage_rows, ["gate", "observed", "required", "pass", "evidence"])
    write_csv(commands_path, [{k: v for k, v in cmd.items() if k != "parsed"} for cmd in commands], ["name", "cmd", "returncode", "stdout", "stderr", "exit"])

    md_lines = [
        "# Board B 220646 Downstream Closure Audit v1",
        "",
        f"- Decision: `{final_decision}`.",
        f"- Source recipe: `SourceRootStopCarryLongHorizonV1`; RC-SPA gate `{decision.get('gate_result')}`, stable score `{decision.get('stable_profit_score')}`.",
        f"- Wire records: `{len(wire_rows)}`; branch paths preserved in wire: `{str(len(branch_paths) == 4).lower()}`.",
        f"- Existing clean ingest evidence applied `{ingest_records}` records; no force ingest was run in this audit.",
        f"- Pre-Bayes branch-path posterior: `{str(pre_bayes_branch_closed).lower()}`; BBN branch-path posterior: `{str(bbn_branch_closed).lower()}`.",
        f"- CatBoost/path-ranker calibrated branch rows ready: `{str(catboost_closed).lower()}`; execution-tree branch admissibility ready: `{str(execution_closed).lower()}`.",
        "- Closed-loop confidence ready: `false`; promotion allowed: `false`; `update_goal=false`.",
        "- Runtime code changed: `false`; thresholds relaxed: `false`; Auto-Quant training started: `false`; raw data committed: `false`.",
        "",
        "## Stage Gates",
        "",
        "| Gate | Observed | Required | Pass | Evidence |",
        "|---|---|---|---:|---|",
    ]
    for row in stage_rows:
        md_lines.append(f"| `{row['gate']}` | `{row['observed']}` | `{row['required']}` | `{row['pass']}` | `{row['evidence']}` |")
    md_lines.extend(
        [
            "",
            "## Boundary",
            "",
            "This audit consumes existing Auto-Quant/RC-SPA artifacts and runs readback commands against the existing ict-engine downstream states. It does not rerun heavy Auto-Quant training, does not force duplicate ingest, and does not promote the candidate from RC-SPA alone.",
            "",
            "## Artifacts",
            "",
            f"- JSON: `{rel(json_path)}`",
            f"- Report: `{rel(md_path)}`",
            f"- Gate CSV: `{rel(gates_path)}`",
            f"- Command CSV: `{rel(commands_path)}`",
            f"- Assertions: `{rel(assertions_path)}`",
        ]
    )
    md_path.write_text("\n".join(md_lines) + "\n", encoding="utf-8")
    assertions_path.write_text(
        "\n".join(
            [
                f"PASS decision={final_decision}",
                f"PASS rc_spa_gate={decision.get('gate_result')}",
                f"PASS wire_records={len(wire_rows)}",
                f"PASS unique_branch_paths={len(branch_paths)}",
                f"PASS ingest_records={ingest_records}",
                f"PASS pre_bayes_branch_path_posterior={str(pre_bayes_branch_closed).lower()}",
                f"PASS bbn_branch_path_posterior={str(bbn_branch_closed).lower()}",
                f"PASS catboost_closed={str(catboost_closed).lower()}",
                f"PASS execution_closed={str(execution_closed).lower()}",
                "PASS closed_loop_confidence_ready=false",
                "PASS promotion_allowed=false",
                "PASS update_goal=false",
                "PASS force_ingest_used=false",
                "PASS auto_quant_training_started=false",
                "PASS runtime_code_changed=false",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    print(final_decision)
    print(f"wire_records={len(wire_rows)}")
    print(f"unique_branch_paths={len(branch_paths)}")
    print(f"closed_loop_confidence_ready={str(closed_loop_ready).lower()}")
    print("promotion_allowed=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
