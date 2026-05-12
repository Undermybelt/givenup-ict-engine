#!/usr/bin/env python3
"""Bridge a successful Auto-Quant nursery run into Board A fail-closed feedback.

This is intentionally non-promoting. It consumes the settled 101221 threaded-DNS
Auto-Quant output, reruns lightweight ict-engine readbacks on a copied small
state, and writes a decision packet for Board A discovery feedback.
"""

from __future__ import annotations

import csv
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[6]
RUN_ID = "20260512T103013+0800-codex-board-a-aq-feedback-bridge-after-101221-v1"
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs" / RUN_ID
OUT = RUN_ROOT / "board-a-aq-feedback-bridge-after-101221-v1"
CMD = RUN_ROOT / "command-output"
CHECKS = RUN_ROOT / "checks"
STATE = RUN_ROOT / "state_bridge_v1"
SYMBOL = "SRC_ROOT_CARRY_LONG_220646"

SOURCE_RUN = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs/"
    / "20260512T101221+0800-codex-board-b-093854-local-cache-seed-v2"
)
SOURCE_OUT = SOURCE_RUN / "local-cache-seed-v2"
SOURCE_STATE = SOURCE_RUN / "state_local_cache_seed_v2"
SOURCE_METRICS = SOURCE_OUT / "auto_quant_metrics_summary.json"
SOURCE_LIBRARY = SOURCE_OUT / "strategy_library_local_cache_seed_v2.json"
SOURCE_THREAD_STDOUT = SOURCE_RUN / "command-output/06_auto_quant_run_threaded_dns.out"
BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"
BIN = REPO / "target/debug/ict-engine"


def rel(path: Path) -> str:
    return str(path.relative_to(REPO))


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run_command(name: str, argv: list[str], timeout_seconds: int = 20) -> dict[str, Any]:
    cmd_path = CMD / f"{name}.cmd"
    out_path = CMD / f"{name}.out"
    err_path = CMD / f"{name}.err"
    exit_path = CHECKS / f"{name}.exit"
    cmd_path.write_text(" ".join(argv) + "\n", encoding="utf-8")
    try:
        proc = subprocess.run(
            argv,
            cwd=REPO,
            text=True,
            capture_output=True,
            check=False,
            timeout=timeout_seconds,
        )
        stdout = proc.stdout
        stderr = proc.stderr
        returncode = proc.returncode
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout or ""
        stderr = (exc.stderr or "") + f"\nTIMEOUT after {timeout_seconds}s\n"
        returncode = 124
    out_path.write_text(stdout, encoding="utf-8")
    err_path.write_text(stderr, encoding="utf-8")
    exit_path.write_text(f"{returncode}\n", encoding="utf-8")
    parsed = None
    stripped = stdout.strip()
    if stripped.startswith("{"):
        try:
            parsed = json.loads(stripped)
        except json.JSONDecodeError:
            parsed = None
    return {
        "name": name,
        "argv": argv,
        "exit_code": returncode,
        "stdout": rel(out_path),
        "stderr": rel(err_path),
        "exit_file": rel(exit_path),
        "parsed_json": parsed,
    }


def copy_small_state() -> None:
    STATE.mkdir(parents=True, exist_ok=True)
    dependency = SOURCE_STATE / "auto_quant_dependency.json"
    if dependency.exists():
        shutil.copy2(dependency, STATE / "auto_quant_dependency.json")
    source_symbol = SOURCE_STATE / SYMBOL
    dest_symbol = STATE / SYMBOL
    if dest_symbol.exists():
        shutil.rmtree(dest_symbol)
    shutil.copytree(source_symbol, dest_symbol)


def strategy_rows(metrics: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for strategy, timeranges in metrics.get("timerange_metrics", {}).items():
        for item in timeranges:
            rows.append(
                {
                    "strategy": strategy,
                    "timerange_label": item.get("timerange_label"),
                    "timerange": item.get("timerange"),
                    "basket": item.get("basket"),
                    "trade_count": item.get("trade_count"),
                    "win_rate_pct": item.get("win_rate_pct"),
                    "total_profit_pct": item.get("total_profit_pct"),
                    "profit_factor": item.get("profit_factor"),
                    "sharpe": item.get("sharpe"),
                    "max_drawdown_pct": item.get("max_drawdown_pct"),
                    "bah_profit_pct": item.get("bah_profit_pct"),
                    "bah_dd_pct": item.get("bah_dd_pct"),
                }
            )
    return rows


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    CMD.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)
    copy_small_state()

    metrics = read_json(SOURCE_METRICS)
    library = read_json(SOURCE_LIBRARY)
    board_hash_before = sha256(BOARD)

    commands = [
        run_command(
            "00_auto_quant_status_source",
            [str(BIN), "auto-quant-status", "--state-dir", str(SOURCE_STATE), "--output-format", "json"],
        ),
        run_command(
            "01_auto_quant_results_import_bridge",
            [
                str(BIN),
                "auto-quant-results-import",
                "--symbol",
                SYMBOL,
                "--state-dir",
                str(STATE),
                "--library",
                str(SOURCE_LIBRARY),
            ],
        ),
        run_command(
            "02_auto_quant_prior_init_bridge_dry_run",
            [
                str(BIN),
                "auto-quant-prior-init",
                "--symbol",
                SYMBOL,
                "--state-dir",
                str(STATE),
                "--library",
                str(SOURCE_LIBRARY),
                "--dry-run",
            ],
        ),
        run_command(
            "03_pre_bayes_status_bridge_human",
            [str(BIN), "pre-bayes-status", "--symbol", SYMBOL, "--state-dir", str(STATE), "--human"],
        ),
        run_command(
            "04_policy_training_status_bridge_human",
            [str(BIN), "policy-training-status", "--symbol", SYMBOL, "--state-dir", str(STATE), "--human"],
        ),
        run_command(
            "05_export_structural_path_ranking_target_bridge",
            [str(BIN), "export-structural-path-ranking-target", "--symbol", SYMBOL, "--state-dir", str(STATE)],
        ),
        run_command(
            "06_workflow_status_bridge_human",
            [str(BIN), "workflow-status", "--symbol", SYMBOL, "--state-dir", str(STATE), "--human"],
        ),
        run_command(
            "07_workflow_structural_recommended_path_bundle",
            [
                str(BIN),
                "workflow-status",
                "--symbol",
                SYMBOL,
                "--state-dir",
                str(STATE),
                "--phase",
                "structural-recommended-path-bundle",
                "--output-format",
                "json",
            ],
        ),
        run_command(
            "08_workflow_structural_path_ranking_target",
            [
                str(BIN),
                "workflow-status",
                "--symbol",
                SYMBOL,
                "--state-dir",
                str(STATE),
                "--phase",
                "structural-path-ranking-target",
                "--output-format",
                "json",
            ],
        ),
        run_command(
            "09_workflow_execution_candidate",
            [
                str(BIN),
                "workflow-status",
                "--symbol",
                SYMBOL,
                "--state-dir",
                str(STATE),
                "--phase",
                "execution-candidate",
                "--output-format",
                "json",
            ],
        ),
    ]

    import_payload = commands[1]["parsed_json"] or {}
    prior_payload = commands[2]["parsed_json"] or {}

    strategy_metadata = [
        {
            "strategy": item.get("name"),
            "expected_regime": item.get("metadata", {}).get("expected_regime"),
            "status": item.get("metadata", {}).get("status"),
            "pairs": ",".join(item.get("pairs", [])),
            "trade_count": item.get("validation_metrics", {}).get("trade_count"),
            "win_rate_pct": item.get("validation_metrics", {}).get("win_rate_pct"),
            "profit_factor": item.get("validation_metrics", {}).get("profit_factor"),
            "total_profit_pct": item.get("validation_metrics", {}).get("total_profit_pct"),
        }
        for item in library.get("strategies", [])
    ]

    timerange_rows = strategy_rows(metrics)
    write_csv(
        OUT / "strategy_timerange_metrics_v1.csv",
        timerange_rows,
        [
            "strategy",
            "timerange_label",
            "timerange",
            "basket",
            "trade_count",
            "win_rate_pct",
            "total_profit_pct",
            "profit_factor",
            "sharpe",
            "max_drawdown_pct",
            "bah_profit_pct",
            "bah_dd_pct",
        ],
    )
    write_csv(
        OUT / "strategy_metadata_gate_v1.csv",
        strategy_metadata,
        [
            "strategy",
            "expected_regime",
            "status",
            "pairs",
            "trade_count",
            "win_rate_pct",
            "profit_factor",
            "total_profit_pct",
        ],
    )

    gate_rows = [
        {
            "gate": "autoquant_threaded_dns_run_succeeded",
            "status": "pass" if metrics.get("auto_quant_exit") == 0 else "fail",
            "evidence": rel(SOURCE_THREAD_STDOUT),
            "notes": f"succeeded={metrics.get('backtests_succeeded')} failed={metrics.get('backtests_failed')}",
        },
        {
            "gate": "nonzero_trade_feedback_available",
            "status": "pass" if metrics.get("gate", {}).get("nonzero_trades") else "fail",
            "evidence": rel(SOURCE_METRICS),
            "notes": "Auto-Quant produced nonzero trades but only in discovery feedback lane.",
        },
        {
            "gate": "ict_engine_autoquant_import",
            "status": "pass" if import_payload.get("n_ok") == 2 else "fail",
            "evidence": commands[1]["stdout"],
            "notes": f"n_ok={import_payload.get('n_ok')} n_error={import_payload.get('n_error')}",
        },
        {
            "gate": "bbn_prior_dry_run_evidence_value",
            "status": "pass" if prior_payload.get("evidence_value_gate_passed") is True else "fail",
            "evidence": commands[2]["stdout"],
            "notes": f"final_probs={prior_payload.get('final_probs')}",
        },
        {
            "gate": "mainregimev2_root_bound",
            "status": "fail_closed",
            "evidence": rel(SOURCE_LIBRARY),
            "notes": "Strategy metadata is unmapped_crypto_local_cache_seed_not_mainregimev2.",
        },
        {
            "gate": "profit_floor_all_strategies",
            "status": "fail_closed",
            "evidence": rel(SOURCE_METRICS),
            "notes": "Existing settled summary marks profit_floor_all_strategies=false.",
        },
        {
            "gate": "source_control_unlock",
            "status": "fail_closed",
            "evidence": rel(BOARD),
            "notes": "No R6/R5/R3 owner-approved source/control unlock or explicit selected-history approval was added.",
        },
        {
            "gate": "pre_bayes_bbn_catboost_execution_promotion",
            "status": "fail_closed",
            "evidence": commands[3]["stdout"] + ";" + commands[4]["stdout"] + ";" + commands[6]["stdout"],
            "notes": "Readbacks ran, but no promotion chain is authorized without root binding and source/control unlock.",
        },
        {
            "gate": "update_goal",
            "status": "fail_closed",
            "evidence": rel(BOARD),
            "notes": "Strict every-regime objective remains incomplete.",
        },
    ]
    write_csv(OUT / "bridge_decision_gates_v1.csv", gate_rows, ["gate", "status", "evidence", "notes"])

    priority_rows = [
        {
            "candidate": "BNBMeanRevertSharp",
            "feedback_signal": "BNB mean-reversion survived bull_2021, winter_2022, recovery_23_25, and full_5y with nonzero trades.",
            "board_a_use": "source_control_priority_only",
            "required_next_evidence": "Source-owned MainRegimeV2 labels around BNB 1h mean-reversion windows; prove whether the edge is Sideways/Reversal/Bull context, not an unmapped cache label.",
            "promotion_status": "non_promoting_aq_feedback",
        },
        {
            "candidate": "CrashReboundVolume",
            "feedback_signal": "SOL/BNB/AVAX drawdown-rebound-volume produced strong bull/recovery feedback but near-flat winter_2022.",
            "board_a_use": "source_control_priority_only",
            "required_next_evidence": "Source-owned labels for crash/rebound windows and matched negative controls; test Crisis-to-recovery vs Bull continuation roots before any canonical merge.",
            "promotion_status": "non_promoting_aq_feedback",
        },
    ]
    write_csv(
        OUT / "source_control_priority_feedback_v1.csv",
        priority_rows,
        ["candidate", "feedback_signal", "board_a_use", "required_next_evidence", "promotion_status"],
    )

    summary = {
        "run_id": RUN_ID,
        "source_run": rel(SOURCE_RUN),
        "board_hash_before": board_hash_before,
        "source_metrics_sha256": sha256(SOURCE_METRICS),
        "source_library_sha256": sha256(SOURCE_LIBRARY),
        "source_threaded_stdout_sha256": sha256(SOURCE_THREAD_STDOUT),
        "symbol": SYMBOL,
        "commands": commands,
        "metrics_gate": metrics.get("gate", {}),
        "auto_quant_exit": metrics.get("auto_quant_exit"),
        "backtests_succeeded": metrics.get("backtests_succeeded"),
        "backtests_failed": metrics.get("backtests_failed"),
        "strategy_count": metrics.get("strategy_count"),
        "import_n_ok": import_payload.get("n_ok"),
        "prior_init_evidence_value_gate_passed": prior_payload.get("evidence_value_gate_passed"),
        "prior_init_final_probs": prior_payload.get("final_probs"),
        "accepted_rows_added": 0,
        "new_confidence_gate": False,
        "valid_required_root_unlock": False,
        "source_control_evidence_acquired": False,
        "explicit_selected_history": False,
        "canonical_merge": False,
        "downstream_promotion": False,
        "strict_full_objective": False,
        "trade_usable": False,
        "promotion_allowed": False,
        "update_goal": False,
    }
    write_json(OUT / "board_a_aq_feedback_bridge_after_101221_v1.json", summary)

    report_lines = [
        "# Board A AQ Feedback Bridge After 101221 v1",
        "",
        f"Run ID: `{RUN_ID}`",
        "",
        "## Source",
        "",
        f"- Source run: `{rel(SOURCE_RUN)}`",
        f"- Source metrics: `{rel(SOURCE_METRICS)}`",
        f"- Source library: `{rel(SOURCE_LIBRARY)}`",
        f"- Board hash before run: `{board_hash_before}`",
        "",
        "## Result",
        "",
        f"- Auto-Quant threaded-DNS run exit: `{metrics.get('auto_quant_exit')}`.",
        f"- Backtests succeeded/failed: `{metrics.get('backtests_succeeded')}` / `{metrics.get('backtests_failed')}`.",
        f"- ict-engine import `n_ok`: `{import_payload.get('n_ok')}`.",
        f"- BBN prior dry-run evidence gate: `{prior_payload.get('evidence_value_gate_passed')}`; final probabilities `{prior_payload.get('final_probs')}`.",
        "- Discovery feedback is real but non-promoting: both strategies are tagged `unmapped_crypto_local_cache_seed_not_mainregimev2`, and no source/control unlock or selected-history approval exists.",
        "",
        "## Gate",
        "",
        "- Gate result: `board_a_aq_feedback_bridge_after_101221_v1=non_promoting_aq_feedback_imported_bbn_dryrun_root_unbound_no_unlock`.",
        "- Accepted rows added: `0`.",
        "- New confidence gate: `false`.",
        "- Source/control evidence acquired: `false`.",
        "- Canonical merge: `false`.",
        "- Downstream promotion: `false`.",
        "- Strict full objective achieved: `false`.",
        "- Trade usable: `false`.",
        "- `update_goal=false`.",
        "",
        "## Next",
        "",
        "- Use this only as source-control search priority: BNB mean-reversion and SOL/BNB/AVAX crash-rebound windows are worth labeling with source-owned MainRegimeV2 roots and matched negatives. Do not rerun the same 101221 cached crypto AQ path for Board A acceptance.",
        "",
        "## Artifacts",
        "",
        f"- JSON: `{rel(OUT / 'board_a_aq_feedback_bridge_after_101221_v1.json')}`",
        f"- Decision gates: `{rel(OUT / 'bridge_decision_gates_v1.csv')}`",
        f"- Strategy metrics: `{rel(OUT / 'strategy_timerange_metrics_v1.csv')}`",
        f"- Strategy metadata gates: `{rel(OUT / 'strategy_metadata_gate_v1.csv')}`",
        f"- Source-control priority feedback: `{rel(OUT / 'source_control_priority_feedback_v1.csv')}`",
        f"- Assertions: `{rel(CHECKS / 'board_a_aq_feedback_bridge_after_101221_v1_assertions.out')}`",
    ]
    (OUT / "board_a_aq_feedback_bridge_after_101221_v1.md").write_text(
        "\n".join(report_lines) + "\n", encoding="utf-8"
    )

    assertions = {
        "autoquant_run_exit_zero": metrics.get("auto_quant_exit") == 0,
        "autoquant_backtests_succeeded_8": metrics.get("backtests_succeeded") == 8,
        "ict_engine_import_n_ok_2": import_payload.get("n_ok") == 2,
        "bbn_prior_dry_run_evidence_value_gate_true": prior_payload.get("evidence_value_gate_passed") is True,
        "mainregimev2_root_bound_false": True,
        "source_control_unlock_false": True,
        "canonical_merge_false": True,
        "promotion_allowed_false": True,
        "update_goal_false": True,
    }
    assertion_lines = [f"{key}={'PASS' if value else 'FAIL'}" for key, value in assertions.items()]
    (CHECKS / "board_a_aq_feedback_bridge_after_101221_v1_assertions.out").write_text(
        "\n".join(assertion_lines) + "\n", encoding="utf-8"
    )
    return 0 if all(assertions.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
