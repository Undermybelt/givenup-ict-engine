#!/usr/bin/env python3
"""Create a Board B nursery packet from exact 220646 execution-admissibility evidence."""

from __future__ import annotations

import csv
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


RUN_ID = "20260511T234601+0800-codex-board-b-b2r-block-crowded-nursery-v1"
SYMBOL = "SRC_ROOT_CARRY_LONG_220646"
RECIPE_ID = "SourceRootStopCarryLongHorizonV1"
ACCEPTED_REGIME_ID = "BoardA_regime_factor_consumer_map_MainRegimeV2_roots_plus_scoped_manipulation"
CRISIS_BRANCH = (
    "Crisis -> CrisisReliefCarry -> StopManagedPanicRecovery -> "
    "SourceRootStopCarryLongHorizonV1:crisis_carry_h8_sl048_tp12"
)

HERE = Path(__file__).resolve().parent
RUN_ROOT = HERE.parent
REPO = next(path for path in [RUN_ROOT, *RUN_ROOT.parents] if (path / "Cargo.toml").exists())
ICT = REPO / "target/debug/ict-engine"

SOURCE_RUN = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T220646-codex-board-b-source-root-stop-carry-longhorizon-v1"
SOURCE_BRANCH_SUMMARY = SOURCE_RUN / "branch-rc-spa/source_root_stop_carry_longhorizon_branch_summary_v1.csv"
SOURCE_SELECTED_ROWS = SOURCE_RUN / "branch-rc-spa/source_root_stop_carry_longhorizon_selected_rows_v1.csv"
SOURCE_RC_REPORT = SOURCE_RUN / "branch-rc-spa/source_root_stop_carry_longhorizon_rc_spa_report_v1.json"
SOURCE_FEEDBACK_MANIFEST = SOURCE_RUN / "b5-branch-feedback-calibration-v1/selected_feedback_manifest.json"
SOURCE_SCORES = SOURCE_RUN / "b5-branch-feedback-calibration-v1/catboost/scores_py313/current_scores_py313.csv"

BLOCKED_STATE = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs/20260511T231800-codex-board-b-220646-exact-branch-closed-loop-readback-v4/"
    "exact-branch-closed-loop-readback-v4/state_exact_branch_closed_loop_v4"
)
LIVE_STATE = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs/20260511T233426-codex-board-b-220646-crisis-branch-live-replay-v1/"
    "state_crisis_branch_live_replay_v1"
)
BLOCKED_SYMBOL_DIR = BLOCKED_STATE / SYMBOL
LIVE_SYMBOL_DIR = LIVE_STATE / SYMBOL
BLOCKED_TRACE = BLOCKED_SYMBOL_DIR / "execution_tree_trace.json"
LIVE_TRACE = LIVE_SYMBOL_DIR / "execution_tree_trace.json"
LIVE_EXECUTION_CANDIDATE = LIVE_SYMBOL_DIR / "execution_candidate.json"
LIVE_WORKFLOW = LIVE_SYMBOL_DIR / "workflow_snapshot.json"

OUT_DIR = RUN_ROOT / "b2r-block-crowded-nursery-v1"
LOG_DIR = RUN_ROOT / "command-output"
CHECK_DIR = RUN_ROOT / "checks"
FEATURES_CSV = OUT_DIR / "block_crowded_nursery_features_v1.csv"
FEEDBACK_CSV = OUT_DIR / "block_crowded_nursery_feedback_rows_v1.csv"
SUMMARY_JSON = OUT_DIR / "block_crowded_nursery_v1.json"
SUMMARY_MD = OUT_DIR / "block_crowded_nursery_v1.md"
ASSERTIONS = CHECK_DIR / "block_crowded_nursery_v1_assertions.out"


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO))
    except ValueError:
        return str(path)


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames: list[str] = []
    for row in rows:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def run_command(name: str, args: list[str], timeout_seconds: int = 180) -> dict[str, Any]:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    try:
        proc = subprocess.run(
            args,
            cwd=REPO,
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
    stdout_path = LOG_DIR / f"{name}.out"
    stderr_path = LOG_DIR / f"{name}.err"
    exit_path = LOG_DIR / f"{name}.exit"
    stdout_path.write_text(stdout, encoding="utf-8")
    stderr_path.write_text(stderr, encoding="utf-8")
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
        "stdout_path": rel(stdout_path),
        "stderr_path": rel(stderr_path),
        "exit_path": rel(exit_path),
        "parsed_json": parsed is not None,
    }


def first_float_from_line(prefix: str, lines: list[str]) -> float | None:
    for line in lines:
        if prefix in line:
            fragment = line.split(prefix, 1)[1]
            chars: list[str] = []
            for char in fragment:
                if char.isdigit() or char in ".-":
                    chars.append(char)
                elif chars:
                    break
            try:
                return float("".join(chars))
            except ValueError:
                return None
    return None


def trace_summary(path: Path) -> dict[str, Any]:
    trace = read_json(path)
    output = trace.get("output") or {}
    lineage = output.get("split_reason_lineage") or []
    if not isinstance(lineage, list):
        lineage = []
    readiness = first_float_from_line("execution_readiness=", [str(item) for item in lineage])
    exact_path_seen = any(CRISIS_BRANCH in str(item) for item in lineage)
    return {
        "source": rel(path),
        "generated_at": trace.get("generated_at"),
        "branch": output.get("branch"),
        "gate_status": output.get("gate_status"),
        "execution_bias": output.get("execution_bias"),
        "decision_hint": output.get("decision_hint"),
        "execution_score": output.get("execution_score"),
        "execution_readiness": readiness,
        "readiness_threshold": 0.45,
        "readiness_margin": None if readiness is None else readiness - 0.45,
        "market_state": ";".join([str(item) for item in lineage if str(item).startswith("market_state=")]),
        "path_ranker_score_used": output.get("path_ranker_score_used_by_execution_tree"),
        "ranker_validation_ready": output.get("ranker_validation_ready"),
        "exact_branch_path_seen": exact_path_seen,
    }


def branch_summary() -> dict[str, dict[str, Any]]:
    rows = read_csv(SOURCE_BRANCH_SUMMARY)
    out: dict[str, dict[str, Any]] = {}
    for row in rows:
        root = row.get("parent_regime_root") or "unknown"
        out[root] = {
            "regime_profit_branch_path": row.get("regime_profit_branch_path"),
            "total_trades": int(float(row.get("total_trades") or 0)),
            "test_folds": int(float(row.get("test_folds") or 0)),
            "fold_positive_rate": float(row.get("fold_positive_rate") or 0),
            "win_rate": float(row.get("win_rate") or 0),
            "bootstrap_edge_lcb_5pct": float(row.get("bootstrap_edge_lcb_5pct") or 0),
            "pbo": float(row.get("pbo") or 0),
            "dsr": float(row.get("dsr") or 0),
            "cost_stress_result": row.get("cost_stress_result"),
            "rc_spa": float(row.get("rc_spa") or 0),
            "hard_gate_result": row.get("hard_gate_result"),
            "promotion_level": row.get("promotion_level"),
        }
    return out


def crisis_score() -> float | None:
    if not SOURCE_SCORES.exists():
        return None
    for row in read_csv(SOURCE_SCORES):
        if row.get("path_id") == CRISIS_BRANCH:
            try:
                return float(row.get("raw_path_score") or "")
            except ValueError:
                return None
    return None


def build_feedback_rows() -> list[dict[str, Any]]:
    manifest = read_json(SOURCE_FEEDBACK_MANIFEST)
    rows = manifest.get("rows") or []
    out = []
    for row in rows:
        if row.get("regime_profit_branch_path") != CRISIS_BRANCH:
            continue
        out.append(
            {
                "source_index": row.get("index"),
                "trade_id": row.get("trade_id"),
                "root": row.get("root"),
                "realized_outcome": row.get("realized_outcome"),
                "pnl": row.get("pnl"),
                "regime_profit_branch_path": row.get("regime_profit_branch_path"),
                "feedback_path": row.get("feedback_path"),
            }
        )
    return out


def main() -> int:
    for directory in [OUT_DIR, LOG_DIR, CHECK_DIR]:
        directory.mkdir(parents=True, exist_ok=True)

    commands = [
        run_command("01_provider_status_agent", [str(ICT), "provider-status", "--agent"]),
        run_command(
            "02_auto_quant_status_source_state",
            [str(ICT), "auto-quant-status", "--state-dir", rel(SOURCE_RUN / "auto-quant"), "--output-format", "json"],
        ),
        run_command(
            "03_pre_bayes_status_latest_live",
            [str(ICT), "pre-bayes-status", "--symbol", SYMBOL, "--state-dir", rel(LIVE_STATE), "--output-format", "json"],
        ),
        run_command(
            "04_workflow_structural_bundle_latest_live",
            [
                str(ICT),
                "workflow-status",
                "--symbol",
                SYMBOL,
                "--state-dir",
                rel(LIVE_STATE),
                "--phase",
                "structural-recommended-path-bundle",
                "--output-format",
                "json",
            ],
        ),
        run_command(
            "05_workflow_execution_candidate_latest_live",
            [
                str(ICT),
                "workflow-status",
                "--symbol",
                SYMBOL,
                "--state-dir",
                rel(LIVE_STATE),
                "--phase",
                "execution-candidate",
                "--output-format",
                "json",
            ],
        ),
        run_command(
            "06_workflow_status_latest_live",
            [str(ICT), "workflow-status", "--symbol", SYMBOL, "--state-dir", rel(LIVE_STATE), "--output-format", "json"],
        ),
    ]

    branches = branch_summary()
    selected_rows = read_csv(SOURCE_SELECTED_ROWS)
    rc_report = read_json(SOURCE_RC_REPORT)
    blocked_trace = trace_summary(BLOCKED_TRACE)
    live_trace = trace_summary(LIVE_TRACE)
    live_candidate = read_json(LIVE_EXECUTION_CANDIDATE)
    live_workflow = read_json(LIVE_WORKFLOW)
    feedback_rows = build_feedback_rows()
    write_csv(FEEDBACK_CSV, feedback_rows)

    features = [
        {
            "nursery_branch_id": "B2R-220646-crisis-execution-admissibility-margin-v1",
            "nursery_status": "incubation_only",
            "parent_regime_root": "Crisis",
            "root_confidence_source": ACCEPTED_REGIME_ID,
            "child_regime_hypothesis": "CrisisReliefCarry",
            "child_child_or_profit_factor": "StopManagedPanicRecovery",
            "profit_factor_leaf": "SourceRootStopCarryLongHorizonV1:crisis_carry_h8_sl048_tp12",
            "action_leaf": "passive_or_no_trade_when_execution_readiness_near_floor",
            "branch_path": CRISIS_BRANCH,
            "why_keep_exploring": "strict RC-SPA passed and exact downstream path is consumed, but execution admissibility flipped from block_crowded to observe/passive around the 0.45 readiness floor",
            "backtest_artifact": rel(SOURCE_BRANCH_SUMMARY),
            "provider_panel": "provider_cache_yfinance; provider status refreshed in command-output/01_provider_status_agent.out; IBKR reachable but dependency-blocked in this runtime; TradingViewMCP/yfinance/Kraken status captured by provider-status",
            "trade_count": branches.get("Crisis", {}).get("total_trades"),
            "win_rate_net": branches.get("Crisis", {}).get("win_rate"),
            "edge_lcb": branches.get("Crisis", {}).get("bootstrap_edge_lcb_5pct"),
            "max_drawdown_or_tail_loss": "",
            "rc_spa_score_if_available": branches.get("Crisis", {}).get("rc_spa"),
            "filter_probe_result": live_candidate.get("pre_bayes_evidence_filter", {}).get("gating_status"),
            "bbn_probe_result": live_candidate.get("pre_bayes_evidence_filter", {}).get("evidence_assignments", {}).get("regime_bundle_bbn_application_status"),
            "catboost_probe_result": f"ranker_score_used={live_trace.get('path_ranker_score_used')} raw_score={crisis_score()}",
            "execution_tree_probe_result": f"{blocked_trace.get('branch')}@{blocked_trace.get('execution_readiness')} -> {live_trace.get('branch')}@{live_trace.get('execution_readiness')}",
            "feedback_to_board_a": "none; this is Board B execution-admissibility nursery feedback, not an accepted regime-definition replacement",
            "promotion_blocker": "promotion_allowed=false; latest live status is observe/passive, not a final closed_loop_confidence promotion",
            "block_crowded_negative_feature": True,
            "execution_readiness_floor": 0.45,
            "blocked_readiness_margin": blocked_trace.get("readiness_margin"),
            "latest_readiness_margin": live_trace.get("readiness_margin"),
        }
    ]
    write_csv(FEATURES_CSV, features)

    latest_analyze = (live_workflow.get("latest_analyze") or {}) if isinstance(live_workflow, dict) else {}
    summary = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "accepted_regime_id": ACCEPTED_REGIME_ID,
        "recipe_id": RECIPE_ID,
        "regime_profit_branch_path": CRISIS_BRANCH,
        "source_rc_spa_report": rel(SOURCE_RC_REPORT),
        "source_branch_summary": rel(SOURCE_BRANCH_SUMMARY),
        "source_selected_rows": rel(SOURCE_SELECTED_ROWS),
        "source_feedback_manifest": rel(SOURCE_FEEDBACK_MANIFEST),
        "selected_trade_rows": len(selected_rows),
        "crisis_feedback_rows": len(feedback_rows),
        "branch_summary": branches,
        "rc_report_manipulation_component": rc_report.get("manipulation_component"),
        "catboost_crisis_raw_score": crisis_score(),
        "blocked_readback": blocked_trace,
        "latest_live_readback": live_trace,
        "latest_live_candidate": {
            "candidate_status": live_candidate.get("candidate_status"),
            "actionable": live_candidate.get("actionable"),
            "selected_direction": live_candidate.get("selected_direction"),
            "pre_bayes_gate": live_candidate.get("pre_bayes_evidence_filter", {}).get("gating_status"),
            "pre_bayes_quality": live_candidate.get("pre_bayes_evidence_filter", {}).get("evidence_quality_score"),
            "regime_bundle_branch_paths": live_candidate.get("pre_bayes_evidence_filter", {})
            .get("evidence_assignments", {})
            .get("regime_bundle_branch_paths_json"),
            "decision_hint": live_candidate.get("decision_hint"),
        },
        "latest_workflow": {
            "promotion_status": latest_analyze.get("promotion_status"),
            "workflow_phase": latest_analyze.get("workflow_phase"),
            "phase_summary": latest_analyze.get("phase_summary"),
            "risk_flags": latest_analyze.get("risk_flags"),
            "recommended_next_command_meta": latest_analyze.get("recommended_next_command_meta"),
        },
        "nursery_status": "incubation_only",
        "promotion_allowed": False,
        "promotion_blocker": "latest exact branch replay is observe/passive with pass_neutralized Pre-Bayes and different_data_fingerprint; no explicit closed_loop_confidence promotion exists",
        "features_csv": rel(FEATURES_CSV),
        "feedback_csv": rel(FEEDBACK_CSV),
        "commands": commands,
    }
    write_json(SUMMARY_JSON, summary)

    md = f"""# B2R Block Crowded Nursery v1

Run id: `{RUN_ID}`

This is an additive Board B nursery packet. It does not promote `220646`.

## Result

- Branch path: `{CRISIS_BRANCH}`
- Nursery status: `incubation_only`
- RC-SPA source remains pass for the source-root family; Crisis branch RC-SPA is `{branches.get('Crisis', {}).get('rc_spa')}` over `{branches.get('Crisis', {}).get('total_trades')}` trades.
- Earlier exact readback: execution tree branch `{blocked_trace.get('branch')}`, gate `{blocked_trace.get('gate_status')}`, readiness `{blocked_trace.get('execution_readiness')}`.
- Latest live replay: execution tree branch `{live_trace.get('branch')}`, gate `{live_trace.get('gate_status')}`, readiness `{live_trace.get('execution_readiness')}`.
- Pre-Bayes latest gate: `{summary['latest_live_candidate']['pre_bayes_gate']}` quality `{summary['latest_live_candidate']['pre_bayes_quality']}`.
- CatBoost/path-ranker: exact Crisis branch score is `{summary['catboost_crisis_raw_score']}`, and execution tree reports ranker score used: `{live_trace.get('path_ranker_score_used')}`.

## Interpretation

`block_crowded` is now a nursery execution-admissibility feature, not a profitability rejection. The same exact Crisis branch crossed from blocked to observe/passive when readiness moved around the `0.45` floor, but promotion remains blocked because the latest replay is `observe`, Pre-Bayes is only `pass_neutralized`, the data fingerprint is not comparable to the previous replay, and no explicit closed-loop confidence promotion exists.

## Artifacts

- JSON: `{rel(SUMMARY_JSON)}`
- Features CSV: `{rel(FEATURES_CSV)}`
- Feedback rows CSV: `{rel(FEEDBACK_CSV)}`
- Assertions: `{rel(ASSERTIONS)}`
- Command logs: `{rel(LOG_DIR)}`
"""
    SUMMARY_MD.write_text(md, encoding="utf-8")

    checks = {
        "provider_status_exit0": commands[0]["returncode"] == 0,
        "auto_quant_status_exit0": commands[1]["returncode"] == 0,
        "pre_bayes_status_exit0": commands[2]["returncode"] == 0,
        "workflow_bundle_exit0": commands[3]["returncode"] == 0,
        "workflow_execution_candidate_exit0": commands[4]["returncode"] == 0,
        "workflow_status_exit0": commands[5]["returncode"] == 0,
        "blocked_trace_was_block_crowded": blocked_trace.get("branch") == "block_crowded",
        "latest_trace_observe_or_better": live_trace.get("gate_status") in {"observe", "admitted"},
        "exact_crisis_branch_seen_in_latest_trace": bool(live_trace.get("exact_branch_path_seen")),
        "source_crisis_has_nonzero_trades": int(branches.get("Crisis", {}).get("total_trades") or 0) > 0,
        "nursery_status_incubation_only": summary["nursery_status"] == "incubation_only",
        "promotion_allowed_false": summary["promotion_allowed"] is False,
    }
    assertion_lines = [f"{name}={str(value).lower()}" for name, value in checks.items()]
    assertion_lines.append("PASS" if all(checks.values()) else "FAIL")
    ASSERTIONS.write_text("\n".join(assertion_lines) + "\n", encoding="utf-8")
    return 0 if all(checks.values()) else 2


if __name__ == "__main__":
    raise SystemExit(main())
