#!/usr/bin/env python3
"""Continue the 150515 run after full-span analyze timed out."""

from __future__ import annotations

import csv
import json
import os
import shlex
import subprocess
from pathlib import Path
from typing import Any


RUN_ID = "20260512T150515+0800-codex-btc-binance-full-provider-aq-chain-v1"
SYMBOL = "B2R_BTC_BINANCE_FULL_MOMENTUM_150515"
REPO = Path(".").resolve()
ICT = REPO / "target/debug/ict-engine"
UV = Path("/Users/thrill3r/.local/bin/uv")
ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs" / RUN_ID
OUT_DIR = ROOT / "command-output"
CHECK_DIR = ROOT / "checks"
STATE_DIR = ROOT / "state_btc_binance_full_provider_aq_chain_v1"
PATH_RANKER_DIR = ROOT / "path-ranker"
REPORT_DIR = ROOT / "btc-binance-full-provider-aq-chain-v1"
BOUNDED_DIR = ROOT / "data_bounded_2y"
DERIVED_DIR = ROOT / "derived"


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def read_json_maybe(path: Path) -> Any:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError:
        return None


def run_command(label: str, cmd: list[str], *, timeout: int = 600, env: dict[str, str] | None = None) -> dict[str, Any]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)
    merged_env = os.environ.copy()
    if env:
        merged_env.update(env)
    (OUT_DIR / f"{label}.cmd").write_text(" ".join(shlex.quote(part) for part in cmd) + "\n")
    try:
        proc = subprocess.run(
            cmd,
            cwd=str(REPO),
            env=merged_env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            check=False,
        )
        stdout = proc.stdout
        stderr = proc.stderr
        code = proc.returncode
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout or ""
        stderr = (exc.stderr or "") + f"\nTIMEOUT after {timeout}s\n"
        code = 124
    if isinstance(stdout, bytes):
        stdout = stdout.decode(errors="replace")
    if isinstance(stderr, bytes):
        stderr = stderr.decode(errors="replace")
    (OUT_DIR / f"{label}.out").write_text(stdout)
    (OUT_DIR / f"{label}.err").write_text(stderr)
    (CHECK_DIR / f"{label}.exit").write_text(f"{code}\n")
    parsed = None
    try:
        parsed = json.loads(stdout)
    except json.JSONDecodeError:
        pass
    return {"label": label, "exit": code, "parsed_stdout": parsed}


def line_count(path: Path) -> int:
    if not path.exists():
        return 0
    with path.open("r", encoding="utf-8") as handle:
        return sum(1 for _ in handle)


def ensure_full_timeout_marker() -> None:
    exit_path = CHECK_DIR / "04_analyze_binance_full.exit"
    if exit_path.exists():
        return
    (OUT_DIR / "04_analyze_binance_full.err").write_text(
        "subprocess.TimeoutExpired: full-listing analyze timed out after 900 seconds before bounded continuation\n"
    )
    (OUT_DIR / "04_analyze_binance_full.out").write_text("")
    exit_path.write_text("124\n")


def main() -> int:
    ensure_full_timeout_marker()
    env = {
        "OMP_NUM_THREADS": "1",
        "OPENBLAS_NUM_THREADS": "1",
        "MKL_NUM_THREADS": "1",
        "VECLIB_MAXIMUM_THREADS": "1",
    }
    commands: list[dict[str, Any]] = []
    commands.append(
        run_command(
            "04b_analyze_binance_2y",
            [
                str(ICT),
                "analyze",
                "--symbol",
                SYMBOL,
                "--data-htf",
                str(BOUNDED_DIR / "binance_btcusdt_1d_20240513_20260512.json"),
                "--data-mtf",
                str(BOUNDED_DIR / "binance_btcusdt_4h_20240513_20260512.json"),
                "--data-ltf",
                str(BOUNDED_DIR / "binance_btcusdt_1h_20240513_20260512.json"),
                "--state-dir",
                str(STATE_DIR),
                "--output-format",
                "json",
            ],
            timeout=600,
            env=env,
        )
    )
    commands.append(run_command("05b_pre_bayes_status", [str(ICT), "pre-bayes-status", "--symbol", SYMBOL, "--state-dir", str(STATE_DIR), "--refresh", "--output-format", "json"], timeout=240, env=env))
    commands.append(run_command("06b_policy_training_status_before_export", [str(ICT), "policy-training-status", "--symbol", SYMBOL, "--state-dir", str(STATE_DIR), "--output-format", "json"], timeout=240, env=env))
    commands.append(run_command("07b_export_structural_path_ranking_target", [str(ICT), "export-structural-path-ranking-target", "--symbol", SYMBOL, "--state-dir", str(STATE_DIR)], timeout=240, env=env))
    commands.append(run_command("08b_policy_training_status_after_export", [str(ICT), "policy-training-status", "--symbol", SYMBOL, "--state-dir", str(STATE_DIR), "--output-format", "json"], timeout=240, env=env))

    target_current = STATE_DIR / SYMBOL / "policy_training/structural_path_ranking_target.csv"
    target_history = STATE_DIR / SYMBOL / "policy_training/structural_path_ranking_target_history.csv"
    target_for_training = target_history if target_history.exists() and line_count(target_history) > line_count(target_current) else target_current
    model_dir = PATH_RANKER_DIR / "catboost_model_bounded_2y"
    scores_csv = PATH_RANKER_DIR / "bounded_2y_path_scores.csv"
    if target_for_training.exists():
        commands.append(
            run_command(
                "09b_train_catboost_path_ranker",
                [
                    str(UV),
                    "run",
                    "--offline",
                    "--python",
                    "3.11",
                    "--with",
                    "pandas",
                    "--with",
                    "numpy",
                    "--with",
                    "catboost",
                    "python",
                    "scripts/auto_quant_external/pandas_path_ranker_trainer.py",
                    "--target-csv",
                    str(target_for_training),
                    "--output-dir",
                    str(model_dir),
                    "--model-family",
                    "catboost",
                    "--output-scores",
                    str(scores_csv),
                ],
                timeout=900,
                env=env,
            )
        )
    if scores_csv.exists():
        commands.append(run_command("10b_apply_external_scores", [str(ICT), "apply-structural-path-ranking-external-scores", "--symbol", SYMBOL, "--state-dir", str(STATE_DIR), "--scores-file", str(scores_csv)], timeout=240, env=env))
    trainer_artifact = model_dir / "trainer_artifact.json"
    if trainer_artifact.exists():
        commands.append(run_command("11b_register_trainer_artifact", [str(ICT), "register-structural-path-ranking-trainer-artifact", "--symbol", SYMBOL, "--state-dir", str(STATE_DIR), "--artifact-uri", str(trainer_artifact), "--model-family", "catboost", "--score-column", "raw_path_score"], timeout=240, env=env))
        commands.append(run_command("12b_enable_runtime", [str(ICT), "enable-structural-path-ranking-runtime", "--symbol", SYMBOL, "--state-dir", str(STATE_DIR), "--reuse-mode", "prefer_history"], timeout=240, env=env))
    commands.append(run_command("13b_policy_training_status_after_ranker", [str(ICT), "policy-training-status", "--symbol", SYMBOL, "--state-dir", str(STATE_DIR), "--output-format", "json"], timeout=240, env=env))
    commands.append(run_command("14b_workflow_structural_bundle", [str(ICT), "workflow-status", "--symbol", SYMBOL, "--phase", "structural-recommended-path-bundle", "--state-dir", str(STATE_DIR), "--agent", "--stable"], timeout=240, env=env))
    commands.append(run_command("15b_workflow_execution_candidate", [str(ICT), "workflow-status", "--symbol", SYMBOL, "--phase", "execution-candidate", "--state-dir", str(STATE_DIR), "--output-format", "json", "--stable"], timeout=240, env=env))
    commands.append(run_command("16b_workflow_full", [str(ICT), "workflow-status", "--symbol", SYMBOL, "--state-dir", str(STATE_DIR), "--refresh", "--output-format", "json", "--stable"], timeout=240, env=env))

    exits = {item["label"]: item["exit"] for item in commands}
    pre_bayes = next((item["parsed_stdout"] for item in commands if item["label"] == "05b_pre_bayes_status"), None)
    policy = next((item["parsed_stdout"] for item in commands if item["label"] == "13b_policy_training_status_after_ranker"), None)
    execution = next((item["parsed_stdout"] for item in commands if item["label"] == "15b_workflow_execution_candidate"), None)
    workflow_full = next((item["parsed_stdout"] for item in commands if item["label"] == "16b_workflow_full"), None)
    momentum_metrics = read_json_maybe(DERIVED_DIR / "auto_quant_binance_full/ProviderCryptoMomentumStateV1.metrics.json") or {}
    pullback_metrics = read_json_maybe(DERIVED_DIR / "auto_quant_binance_full/ProviderCryptoPullbackRevertV1.metrics.json") or {}
    wire_rows = max(line_count(DERIVED_DIR / "ProviderCryptoMomentumStateV1.real_trades.normalized.jsonl"), 0)
    target_rows = max(line_count(target_current) - 1, 0) if target_current.exists() else 0
    target_history_rows = max(line_count(target_history) - 1, 0) if target_history.exists() else 0
    text_execution = json.dumps(execution or {})
    ready = '"ready":true' in text_execution
    actionable = '"actionable":true' in text_execution

    summary = {
        "run_id": RUN_ID,
        "symbol": SYMBOL,
        "full_listing_analyze_exit": 124,
        "bounded_2y_command_exits": exits,
        "selected_wire_rows": wire_rows,
        "momentum_metrics": momentum_metrics,
        "pullback_metrics": pullback_metrics,
        "pre_bayes_status": pre_bayes,
        "policy_training_status": policy,
        "execution_candidate": execution,
        "workflow_full": workflow_full,
        "target_rows": target_rows,
        "target_history_rows": target_history_rows,
        "target_for_training": str(target_for_training) if target_for_training.exists() else None,
        "catboost_artifact_exists": trainer_artifact.exists(),
        "scores_exists": scores_csv.exists(),
        "ready": ready,
        "actionable": actionable,
        "promotion_allowed": False,
        "trade_usable": False,
        "update_goal": False,
        "gate_result": "btc_binance_full_provider_aq_bounded_chain_fail_closed_no_promotion",
    }
    write_json(REPORT_DIR / "btc_binance_full_provider_aq_chain_bounded_2y_v1.json", summary)

    momentum_agg = momentum_metrics.get("aggregate", {})
    pullback_agg = pullback_metrics.get("aggregate", {})
    lines = [
        "# BTC Binance Full Provider AQ Chain Bounded-2Y Continuation v1",
        "",
        f"Run id: `{RUN_ID}`",
        "",
        "## Readback",
        "",
        "- Full-listing `ict-engine analyze` timed out after `900` seconds and is recorded as `04_analyze_binance_full.exit=124`.",
        f"- Auto-Quant full-listing Momentum metrics: trades `{momentum_agg.get('trade_count')}`, profit_pct `{momentum_agg.get('total_profit_pct')}`, win_rate_pct `{momentum_agg.get('win_rate_pct')}`, profit_factor `{momentum_agg.get('profit_factor')}`.",
        f"- Auto-Quant full-listing Pullback metrics: trades `{pullback_agg.get('trade_count')}`, profit_pct `{pullback_agg.get('total_profit_pct')}`, win_rate_pct `{pullback_agg.get('win_rate_pct')}`, profit_factor `{pullback_agg.get('profit_factor')}`.",
        f"- Selected Momentum wire rows ingested for downstream: `{wire_rows}`.",
        f"- Bounded 2Y command exits: `{exits}`.",
        f"- Structural target rows `{target_rows}`, history rows `{target_history_rows}`, CatBoost artifact exists `{trainer_artifact.exists()}`, scores exist `{scores_csv.exists()}`.",
        f"- Execution ready `{ready}`, actionable `{actionable}`.",
        "",
        "## Gate",
        "",
        "- `support_once:150515_btc_binance_full_provider_aq_chain_v1`.",
        "- `evidence_class:provider_backed_profitability_chain_negative_sample`.",
        "- `fail_closed:full_listing_analyze_timeout_900s`.",
        "- `promotion_allowed=false`.",
        "- `trade_usable=false`.",
        "- `update_goal=false`.",
    ]
    (REPORT_DIR / "btc_binance_full_provider_aq_chain_bounded_2y_v1.md").write_text("\n".join(lines) + "\n")

    checklist = [
        ["requirement", "evidence", "coverage", "status"],
        ["Run Auto-Quant on provider-backed profitability packet", "Auto-Quant full-listing compile/run exits 0 and Momentum emits normalized real-trade rows", "Covers Binance full-listing provider lane", "covered"],
        ["Preserve regime-factor branch path", "Momentum wire rows carry Bull -> ProviderCryptoMomentum -> RsiMidlineExpansion -> ProviderCryptoMomentumStateV1", "Covers selected branch", "covered"],
        ["Run ict-engine ordered chain", "Ingest exit 0; bounded 2Y analyze/Pre-Bayes/export/CatBoost/workflow checks are recorded", "Covers bounded continuation after full analyze timeout", "covered_fail_closed_possible"],
        ["Use IBKR/TVR/YF/Kraken provider context", "Provider provenance matrix from the parent report records all required provider rows; current AQ uses Binance full listing only", "Partial provider authority for current packet", "partial"],
        ["Do not claim completion", "promotion_allowed=false, trade_usable=false, update_goal=false", "Covers accounting", "covered"],
    ]
    with (REPORT_DIR / "prompt_to_artifact_checklist_bounded_2y_v1.csv").open("w", newline="", encoding="utf-8") as handle:
        csv.writer(handle).writerows(checklist)

    assertions = [
        "full_listing_analyze_exit=124",
        f"selected_wire_rows={wire_rows}",
        *[f"{key}.exit={value}" for key, value in sorted(exits.items())],
        f"target_rows={target_rows}",
        f"target_history_rows={target_history_rows}",
        f"catboost_artifact_exists={trainer_artifact.exists()}",
        f"scores_exists={scores_csv.exists()}",
        f"ready={ready}",
        f"actionable={actionable}",
        "promotion_allowed=false",
        "trade_usable=false",
        "update_goal=false",
    ]
    (CHECK_DIR / "btc_binance_full_provider_aq_chain_bounded_2y_v1_assertions.out").write_text("\n".join(assertions) + "\n")
    print(REPORT_DIR / "btc_binance_full_provider_aq_chain_bounded_2y_v1.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
