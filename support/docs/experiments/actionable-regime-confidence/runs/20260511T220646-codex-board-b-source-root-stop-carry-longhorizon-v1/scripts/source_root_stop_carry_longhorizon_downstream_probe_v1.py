#!/usr/bin/env python3
"""Run ict-engine downstream consumption for the 220646 Board B candidate.

This script is run-local. It converts the RC-SPA selected branch rows into the
existing ict-engine real-trade feedback wire format, applies them to an isolated
state dir, and captures Pre-Bayes / BBN / policy / workflow readbacks.
"""

from __future__ import annotations

import csv
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


RUN_ID = "20260511T220646+0800-codex-board-b-source-root-stop-carry-longhorizon-v1"
PROBE_ID = "20260511T220646+0800-codex-board-b-source-root-stop-carry-longhorizon-downstream-v1"
RECIPE_ID = "SourceRootStopCarryLongHorizonV1"
SYMBOL = "SRC_ROOT_CARRY_LONG_220646"
SCHEMA_VERSION = "1.0"

HERE = Path(__file__).resolve().parent
RUN_ROOT = HERE.parent
REPO_ROOT = next(path for path in [RUN_ROOT, *RUN_ROOT.parents] if (path / "Cargo.toml").exists())
ICT = REPO_ROOT / "target/debug/ict-engine"

SELECTED_CSV = RUN_ROOT / "branch-rc-spa/source_root_stop_carry_longhorizon_selected_rows_v1.csv"
REPORT_JSON = RUN_ROOT / "branch-rc-spa/source_root_stop_carry_longhorizon_rc_spa_report_v1.json"
OUT_DIR = RUN_ROOT / "ict-engine-downstream"
LOG_DIR = OUT_DIR / "logs"
STATE_DIR = OUT_DIR / "state_fresh_downstream_v2"
WIRE_JSONL = OUT_DIR / "source_root_stop_carry_longhorizon_real_trades_wire_v1.jsonl"
WIRE_COUNT = OUT_DIR / "source_root_stop_carry_longhorizon_real_trades_wire_v1.count"
WIRE_SAMPLE = OUT_DIR / "source_root_stop_carry_longhorizon_real_trades_wire_v1.sample.json"
SUMMARY_JSON = OUT_DIR / "source_root_stop_carry_longhorizon_downstream_probe_v1.json"
SUMMARY_MD = OUT_DIR / "source_root_stop_carry_longhorizon_downstream_probe_v1.md"
ASSERTIONS = OUT_DIR / "source_root_stop_carry_longhorizon_downstream_probe_v1_assertions.out"


def rel(path: Path) -> str:
    return str(path.relative_to(REPO_ROOT))


def parse_ts_ms(value: str) -> int:
    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return int(dt.timestamp() * 1000)


def factor_direction_for_root(root: str) -> str:
    if root == "Bull":
        return "Bull"
    if root in {"Bear", "Crisis"}:
        return "Bear"
    return "Neutral"


def factor_direction_for_pnl(pnl: float) -> str:
    if pnl > 0.0:
        return "Bull"
    if pnl < 0.0:
        return "Bear"
    return "Neutral"


def confidence(row: dict[str, str]) -> float:
    for key in ("source_ticker_confidence", "parent_regime_confidence_floor"):
        try:
            value = float(row.get(key) or 0.0)
        except ValueError:
            value = 0.0
        if value > 0.0:
            return value
    return 0.5


def record_from_row(row: dict[str, str], idx: int, total: int) -> dict[str, Any]:
    pnl = float(row["profit_ratio_net"])
    root = row["parent_regime_root"]
    conf = confidence(row)
    uncertainty = max(0.0, 1.0 - conf)
    variant_id = row["variant_id"]
    branch_path = row["regime_profit_branch_path"]
    trade_id = row.get("trade_id") or f"{RECIPE_ID}|{variant_id}|{idx}"
    direction = row.get("direction") or "long"
    return {
        "schema_version": SCHEMA_VERSION,
        "symbol": SYMBOL,
        "trade_id": trade_id,
        "strategy_name": RECIPE_ID,
        "strategy_mutation_id": f"board-b-source-root-stop-carry-longhorizon-{variant_id}",
        "auto_quant_run_id": RUN_ID,
        "open_ts_ms": parse_ts_ms(row["open_date"]),
        "close_ts_ms": parse_ts_ms(row.get("close_date") or row["open_date"]),
        "direction": direction,
        "pnl": pnl,
        "realized_outcome": "win" if pnl > 0.0 else "loss",
        "regime_at_entry": root,
        "entry_signal": variant_id,
        "factors_used": [
            {
                "factor_name": "market_regime_context.root",
                "category": "regime_context",
                "direction": factor_direction_for_root(root),
                "value": conf,
                "confidence": conf,
                "weighted_score": conf,
                "uncertainty_contribution": uncertainty,
            },
            {
                "factor_name": "regime_profit_branch_path",
                "category": "branch_path",
                "direction": factor_direction_for_pnl(pnl),
                "value": pnl,
                "confidence": conf,
                "weighted_score": pnl,
                "uncertainty_contribution": uncertainty,
            },
            {
                "factor_name": row.get("profit_factor_leaf") or f"{RECIPE_ID}:{variant_id}",
                "category": row.get("profit_factor_family") or "source_root_stop_carry_longhorizon",
                "direction": factor_direction_for_pnl(pnl),
                "value": pnl,
                "confidence": 0.60,
                "weighted_score": pnl,
                "uncertainty_contribution": 0.40,
            },
        ],
        "structural_feedback": {
            "protocol_version": row.get("regime_profit_branch_path_version") or "board-b-source-root-stop-carry-longhorizon/v1",
            "recommendation_id": trade_id,
            "recommended_at": row["open_date"],
            "symbol": SYMBOL,
            "node_id": root,
            "branch_id": branch_path,
            "scenario_id": row.get("sub_regime_tags") or root,
            "path_id": branch_path,
            "direction": direction,
            "entry_style": variant_id,
            "candidate_set_id": RUN_ID,
            "candidate_set_size": total,
            "followed_path": True,
            "realized_outcome": "win" if pnl > 0.0 else "loss",
            "realized_pnl": pnl,
            "exit_reason": row.get("exit_reason") or None,
            "notes": "board_b_rc_spa_pass_downstream_probe_not_production_until_all_stages_close",
        },
    }


def write_wire() -> dict[str, Any]:
    with SELECTED_CSV.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    records = [record_from_row(row, idx, len(rows)) for idx, row in enumerate(rows, start=1)]
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    with WIRE_JSONL.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, sort_keys=True) + "\n")
    WIRE_COUNT.write_text(f"{len(records)}\n", encoding="utf-8")
    if records:
        WIRE_SAMPLE.write_text(json.dumps(records[0], indent=2, sort_keys=True) + "\n", encoding="utf-8")
    csv_paths = {row["regime_profit_branch_path"] for row in rows}
    wire_paths = {record["structural_feedback"]["path_id"] for record in records}
    return {
        "records": len(records),
        "unique_csv_branch_paths": len(csv_paths),
        "unique_wire_branch_paths": len(wire_paths),
        "branch_paths_preserved": csv_paths == wire_paths,
    }


def run_command(name: str, args: list[str], timeout_seconds: int = 180) -> dict[str, Any]:
    try:
        proc = subprocess.run(
            args,
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            check=False,
            timeout=timeout_seconds,
        )
        stdout = proc.stdout
        stderr = proc.stderr
        code = proc.returncode
        timed_out = False
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout or ""
        stderr = (exc.stderr or "") + f"\nTIMEOUT after {timeout_seconds}s\n"
        code = 124
        timed_out = True
    out_path = LOG_DIR / f"{name}.out"
    err_path = LOG_DIR / f"{name}.err"
    exit_path = LOG_DIR / f"{name}.exit"
    out_path.write_text(stdout, encoding="utf-8")
    err_path.write_text(stderr, encoding="utf-8")
    exit_path.write_text(f"{code}\n", encoding="utf-8")
    parsed = None
    try:
        parsed = json.loads(stdout)
    except json.JSONDecodeError:
        parsed = None
    return {
        "name": name,
        "cmd": " ".join(args),
        "returncode": code,
        "timed_out": timed_out,
        "stdout_path": rel(out_path),
        "stderr_path": rel(err_path),
        "exit_path": rel(exit_path),
        "parsed": parsed,
    }


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    wire = write_wire()

    commands = [
        run_command(
            "auto_quant_ingest_real_trades_apply",
            [
                str(ICT),
                "auto-quant-ingest-real-trades",
                "--symbol",
                SYMBOL,
                "--state-dir",
                str(STATE_DIR),
                "--trades",
                str(WIRE_JSONL),
                "--source",
                "board_b_source_root_stop_carry_longhorizon_220646",
            ],
        ),
        run_command(
            "pre_bayes_status_json",
            [str(ICT), "pre-bayes-status", "--symbol", SYMBOL, "--state-dir", str(STATE_DIR), "--refresh", "--output-format", "json"],
        ),
        run_command(
            "policy_training_status_json",
            [str(ICT), "policy-training-status", "--symbol", SYMBOL, "--state-dir", str(STATE_DIR), "--output-format", "json"],
        ),
        run_command(
            "workflow_status_execution_candidate_agent",
            [str(ICT), "workflow-status", "--symbol", SYMBOL, "--state-dir", str(STATE_DIR), "--phase", "execution-candidate", "--agent"],
        ),
        run_command(
            "export_structural_path_ranking_target",
            [str(ICT), "export-structural-path-ranking-target", "--symbol", SYMBOL, "--state-dir", str(STATE_DIR)],
        ),
    ]

    command_by_name = {row["name"]: row for row in commands}
    ingest = command_by_name["auto_quant_ingest_real_trades_apply"].get("parsed") or {}
    pre_bayes = command_by_name["pre_bayes_status_json"].get("parsed") or {}
    policy = command_by_name["policy_training_status_json"].get("parsed") or {}
    workflow = command_by_name["workflow_status_execution_candidate_agent"].get("parsed") or {}
    export = command_by_name["export_structural_path_ranking_target"].get("parsed") or {}
    report = json.loads(REPORT_JSON.read_text(encoding="utf-8"))
    decision = report.get("decision", {})

    auto_quant_symbol_state = STATE_DIR / "auto-quant" / SYMBOL
    bbn_state = auto_quant_symbol_state / "bbn_network.json"
    learning_state = auto_quant_symbol_state / "learning_state.json"
    workflow_snapshot = STATE_DIR / SYMBOL / "workflow_snapshot.json"

    ingest_ok = (
        command_by_name["auto_quant_ingest_real_trades_apply"]["returncode"] == 0
        and int(ingest.get("trades_invalid", -1)) == 0
        and int(ingest.get("trades_total", -1)) == wire["records"]
    )
    command_exits_ok = all(row["returncode"] == 0 for row in commands)
    same_path_consumed = bool(wire["branch_paths_preserved"] and ingest_ok)
    execution_tree_ready = bool(workflow.get("top_actionable") or workflow.get("execution_candidate") or workflow.get("latest_promotable_artifact"))
    policy_ready = bool(policy.get("ready") or policy.get("path_ranking_ready") or policy.get("production_validatable"))

    downstream_consumption = (
        "consumed_through_bbn_feedback_readback;pre_bayes_policy_workflow_export_checked"
        if ingest_ok and command_exits_ok
        else "blocked:downstream_command_failure"
    )
    promotion_status = (
        "not_promoted:execution_tree_or_policy_not_calibrated"
        if ingest_ok
        else "not_promoted:ingest_failed"
    )

    result = {
        "probe_id": PROBE_ID,
        "run_id": RUN_ID,
        "recipe_id": RECIPE_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "symbol": SYMBOL,
        "state_dir": str(STATE_DIR),
        "wire": {
            **wire,
            "jsonl": rel(WIRE_JSONL),
            "count": rel(WIRE_COUNT),
            "sample": rel(WIRE_SAMPLE),
        },
        "rc_spa": {
            "gate_result": decision.get("gate_result"),
            "stable_profit_score": decision.get("stable_profit_score"),
            "price_root_paths_passed": decision.get("price_root_paths_passed"),
            "manipulation_component_pass": decision.get("manipulation_component_pass"),
        },
        "ingest_ok": ingest_ok,
        "same_branch_paths_preserved_to_wire": same_path_consumed,
        "bbn_state_exists": bbn_state.exists(),
        "learning_state_exists": learning_state.exists(),
        "workflow_snapshot_exists": workflow_snapshot.exists(),
        "pre_bayes_gate_status": pre_bayes.get("latest_gate_status"),
        "pre_bayes_policy": pre_bayes.get("latest_policy"),
        "policy_ready": policy_ready,
        "policy_summary_line": policy.get("summary") or policy.get("summary_line"),
        "execution_tree_ready": execution_tree_ready,
        "workflow_top_actionable": workflow.get("top_actionable"),
        "export_returncode": command_by_name["export_structural_path_ranking_target"]["returncode"],
        "export_payload_keys": sorted(export.keys()) if isinstance(export, dict) else [],
        "downstream_consumption": downstream_consumption,
        "promotion_status": promotion_status,
        "commands": [{key: value for key, value in row.items() if key != "parsed"} for row in commands],
    }
    SUMMARY_JSON.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    lines = [
        "# Source Root Stop Carry Long-Horizon Downstream Probe v1",
        "",
        f"- Probe id: `{PROBE_ID}`.",
        f"- RC-SPA gate: `{decision.get('gate_result')}`; stable score `{decision.get('stable_profit_score')}`; price roots passed `{decision.get('price_root_paths_passed')}/4`; Manipulation component pass `{decision.get('manipulation_component_pass')}`.",
        f"- Real-trade wire: `{rel(WIRE_JSONL)}` with `{wire['records']}` records and branch paths preserved `{wire['branch_paths_preserved']}`.",
        f"- Real-trade ingest: `ingest_ok={ingest_ok}`, `trades_invalid={ingest.get('trades_invalid')}`, `trades_total={ingest.get('trades_total')}`, `trades_applied={ingest.get('trades_applied')}`.",
        f"- BBN state exists: `{bbn_state.exists()}`; learning state exists: `{learning_state.exists()}`.",
        f"- Pre-Bayes: gate `{result['pre_bayes_gate_status']}`, policy `{result['pre_bayes_policy']}`.",
        f"- CatBoost/path-ranker policy readiness: `{policy_ready}`; summary `{result['policy_summary_line']}`.",
        f"- Workflow/execution-tree ready: `{execution_tree_ready}`; workflow snapshot exists `{workflow_snapshot.exists()}`.",
        f"- Structural path-ranking export exit: `{result['export_returncode']}`.",
        f"- Downstream consumption: `{downstream_consumption}`.",
        f"- Promotion status: `{promotion_status}`.",
        "",
        "Artifacts:",
        f"- `{rel(SUMMARY_JSON)}`",
        f"- `{rel(ASSERTIONS)}`",
        f"- logs under `{rel(LOG_DIR)}`",
        "",
        "Next:",
        "- Do not call production promotion complete until execution-tree admissibility and calibrated path-ranker readiness are proven for the same branch paths.",
    ]
    SUMMARY_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    assertion_lines = [
        f"probe_id={PROBE_ID}",
        f"wire_records={wire['records']}",
        f"branch_paths_preserved={wire['branch_paths_preserved']}",
        f"ingest_ok={ingest_ok}",
        f"bbn_state_exists={bbn_state.exists()}",
        f"learning_state_exists={learning_state.exists()}",
        f"command_exits_ok={command_exits_ok}",
        f"downstream_consumption={downstream_consumption}",
        f"promotion_status={promotion_status}",
    ]
    ASSERTIONS.write_text("\n".join(assertion_lines) + "\n", encoding="utf-8")
    print(json.dumps({"ok": True, "summary": rel(SUMMARY_JSON), "downstream_consumption": downstream_consumption}, sort_keys=True))
    return 0 if ingest_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
