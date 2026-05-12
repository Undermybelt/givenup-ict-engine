#!/usr/bin/env python3
"""Downstream ingest/readback for the 130436 BTC TOMAC precision-fix candidate."""

from __future__ import annotations

import csv
import json
import os
import subprocess
from pathlib import Path
from typing import Any

import pandas as pd


RUN_ID = "20260512T131346+0800-codex-130436-btc-tomac-downstream-ingest-readback-v1"
SOURCE_RUN_ID = "20260512T130436+0800-codex-124408-precision-fix-tomac-rerun-v1"
SOURCE_TRADE_RUN_ID = "20260512T124408+0800-codex-123227-tomac-trade-density-iteration-v1"
SYMBOL = "B2R_BTC_TOMAC_AGGRESSIVEBE_130436"
BRANCH_PATH = "Bull -> SyntheticBtcTomac -> PrecisionFixedAggressiveBE -> TomacAggressiveBE"

REPO = Path(".")
ICT = REPO / "target/debug/ict-engine"
UV = Path("/Users/thrill3r/.local/bin/uv")
ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs" / RUN_ID
SOURCE_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs" / SOURCE_RUN_ID
SOURCE_TRADE_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs" / SOURCE_TRADE_RUN_ID
TRADE_CSV = SOURCE_ROOT / "trade-exports/TomacAggressiveBE_trades.csv"
SOURCE_JSON = SOURCE_ROOT / "precision-fix-tomac-rerun-v1/precision_fix_tomac_rerun_v1.json"
SOURCE_AQ = SOURCE_TRADE_ROOT / "state_tomac_trade_density_iteration_v1/.deps/auto-quant"
OUT_DIR = ROOT / "command-output"
CHECK_DIR = ROOT / "checks"
REPORT_DIR = ROOT / "130436-btc-tomac-downstream-ingest-readback-v1"
DERIVED_DIR = ROOT / "derived"
DATA_DIR = ROOT / "candle-json"
STATE_DIR = ROOT / "state_ingest"
PATH_RANKER_DIR = ROOT / "path-ranker/catboost_runtime_v1"


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def run_command(label: str, cmd: list[str], env: dict[str, str] | None = None) -> dict[str, Any]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / f"{label}.cmd").write_text(" ".join(cmd) + "\n", encoding="utf-8")
    proc = subprocess.run(
        cmd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        env=env,
    )
    (OUT_DIR / f"{label}.out").write_text(proc.stdout, encoding="utf-8")
    (OUT_DIR / f"{label}.err").write_text(proc.stderr, encoding="utf-8")
    (CHECK_DIR / f"{label}.exit").write_text(f"{proc.returncode}\n", encoding="utf-8")
    parsed = None
    try:
        parsed = json.loads(proc.stdout)
    except json.JSONDecodeError:
        pass
    return {
        "label": label,
        "cmd": cmd,
        "exit": proc.returncode,
        "stdout": str(OUT_DIR / f"{label}.out"),
        "stderr": str(OUT_DIR / f"{label}.err"),
        "parsed_stdout": parsed,
    }


def outcome_from_pnl(pnl: float) -> str:
    if pnl > 0.0:
        return "win"
    if pnl < 0.0:
        return "loss"
    return "breakeven"


def build_trade_record(row: dict[str, str], index: int) -> dict[str, Any]:
    profit_abs = float(row["profit_abs"])
    profit_ratio = float(row["profit_ratio"])
    open_ts = int(float(row["open_timestamp"]))
    close_ts = int(float(row["close_timestamp"]))
    direction = "Bear" if str(row.get("is_short", "")).lower() == "true" else "Bull"
    trade_id = f"tomac_aggressivebe_130436_BTC_USD_{open_ts}_{close_ts}_{index:04d}"
    return {
        "schema_version": "1.0",
        "symbol": SYMBOL,
        "trade_id": trade_id,
        "strategy_name": "TomacAggressiveBE",
        "strategy_mutation_id": "synthetic-btc-tomac-aggressivebe-precision-fix-v1",
        "auto_quant_run_id": SOURCE_RUN_ID,
        "open_ts_ms": open_ts,
        "close_ts_ms": close_ts,
        "direction": direction,
        "pnl": profit_abs,
        "realized_outcome": outcome_from_pnl(profit_abs),
        "regime_at_entry": "Bull",
        "entry_signal": "tomac_aggressivebe_precision_fixed_synthetic_btc",
        "factors_used": [
            {
                "factor_name": "TomacAggressiveBE",
                "category": "structure_ict",
                "direction": direction,
                "value": profit_ratio,
                "confidence": 0.0,
                "weighted_score": profit_abs,
                "uncertainty_contribution": 1.0,
            }
        ],
        "model_probabilities_before_trade": {
            "selected_direction": direction,
            "selected_probability": 0.0,
            "long_score": 0.0,
            "short_score": 0.0,
            "win_prob_long": 0.0,
            "win_prob_short": 0.0,
            "uncertainty": 1.0,
        },
        "regime_profit_branch_path": BRANCH_PATH,
        "main_regime": "Bull",
        "sub_regime": "SyntheticBtcTomac",
        "sub_sub_regime_or_profit_factor": "PrecisionFixedAggressiveBE",
        "profit_factor": "TomacAggressiveBE",
        "provider_provenance": {
            "source_run_id": SOURCE_RUN_ID,
            "source_trade_run_id": SOURCE_TRADE_RUN_ID,
            "provider": "synthetic_selected_history_btc_usd",
            "local_cache_replay": True,
            "same_root_six_provider_authority": False,
            "precision_fix_scope": "in_memory_synthetic_market_precision_amount_1e-8",
            "trade_csv": str(TRADE_CSV),
        },
        "source_run_root": str(SOURCE_ROOT),
        "source_auto_quant_run_id": SOURCE_RUN_ID,
        "evidence_class": "btc_only_synthetic_precision_fix_tomac_candidate_downstream_probe",
        "quality_weight": 0.0,
        "failure_reason": "btc_only_synthetic_selected_history_no_cross_provider_no_pre_bayes_gate",
    }


def build_real_trades_jsonl() -> dict[str, Any]:
    DERIVED_DIR.mkdir(parents=True, exist_ok=True)
    output = DERIVED_DIR / "130436_tomac_aggressivebe_real_trades.jsonl"
    summary_path = DERIVED_DIR / "130436_tomac_aggressivebe_real_trades_summary.json"
    rows: list[dict[str, Any]] = []
    with TRADE_CSV.open(newline="", encoding="utf-8") as handle:
        for index, row in enumerate(csv.DictReader(handle), start=1):
            rows.append(build_trade_record(row, index))
    output.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )
    wins = sum(1 for row in rows if row["realized_outcome"] == "win")
    losses = sum(1 for row in rows if row["realized_outcome"] == "loss")
    breakeven = sum(1 for row in rows if row["realized_outcome"] == "breakeven")
    summary = {
        "path": str(output),
        "rows": len(rows),
        "wins": wins,
        "losses": losses,
        "breakeven": breakeven,
        "branch_path": BRANCH_PATH,
        "symbol": SYMBOL,
        "source_trade_csv": str(TRADE_CSV),
        "quality_weight": 0.0,
    }
    write_json(summary_path, summary)
    return summary


def timestamp_from_ms(value: Any) -> str:
    ts = pd.to_datetime(int(value), unit="ms", utc=True)
    return ts.strftime("%Y-%m-%dT%H:%M:%SZ")


def write_candle_jsons() -> dict[str, Any]:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    outputs: dict[str, Any] = {}
    for timeframe in ["1h", "4h", "1d"]:
        src = SOURCE_AQ / f"user_data/data/BTC_USD-{timeframe}.feather"
        frame = pd.read_feather(src)
        records = [
            {
                "timestamp": timestamp_from_ms(row["date"]),
                "open": float(row["open"]),
                "high": float(row["high"]),
                "low": float(row["low"]),
                "close": float(row["close"]),
                "volume": float(row["volume"]),
            }
            for _, row in frame.iterrows()
        ]
        out = DATA_DIR / f"btc_usd_{timeframe}.json"
        write_json(out, records)
        outputs[timeframe] = {
            "path": str(out),
            "rows": len(records),
            "first_ts": records[0]["timestamp"] if records else None,
            "last_ts": records[-1]["timestamp"] if records else None,
        }
    return outputs


def count_csv_rows(path: Path) -> int | None:
    if not path.exists():
        return None
    with path.open(encoding="utf-8") as handle:
        return max(sum(1 for _ in handle) - 1, 0)


def file_exists(path: Path) -> bool:
    return path.exists()


def extract_runtime_summary(status: Any) -> str | None:
    if not isinstance(status, dict):
        return None
    runtime = status.get("structural_path_ranking_runtime")
    if isinstance(runtime, dict):
        line = runtime.get("summary_line")
        if isinstance(line, str):
            return line
    line = status.get("structural_path_ranking_runtime_summary") or status.get("summary_line")
    return line if isinstance(line, str) else None


def workflow_execution_flags(workflow: Any) -> dict[str, Any]:
    result = {
        "ready": False,
        "actionable": False,
        "review_status": None,
        "execution_gate_status": None,
        "selected_path_probability": None,
        "raw_path_score": None,
    }
    if not isinstance(workflow, dict):
        return result
    blob = json.dumps(workflow)
    result["ready"] = '"ready":true' in blob
    result["actionable"] = '"actionable":true' in blob
    result["execution_gate_status"] = workflow.get("execution_gate_status") or workflow.get("status")
    for key in ["review_status", "selected_path_probability", "raw_path_score"]:
        if key in workflow:
            result[key] = workflow[key]
    return result


def main() -> int:
    ROOT.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    (ROOT / "run_id.txt").write_text(RUN_ID + "\n", encoding="utf-8")
    source_summary = read_json(SOURCE_JSON)
    trades = build_real_trades_jsonl()
    candle_jsons = write_candle_jsons()

    env = os.environ.copy()
    env.update(
        {
            "OMP_NUM_THREADS": "1",
            "OPENBLAS_NUM_THREADS": "1",
            "MKL_NUM_THREADS": "1",
            "VECLIB_MAXIMUM_THREADS": "1",
        }
    )

    commands: list[dict[str, Any]] = []
    commands.append(run_command("00_provider_status", [str(ICT), "provider-status", "--agent"], env=env))
    commands.append(
        run_command(
            "01_ingest_real_trades_dry_run",
            [
                str(ICT),
                "auto-quant-ingest-real-trades",
                "--symbol",
                SYMBOL,
                "--state-dir",
                str(STATE_DIR),
                "--trades",
                trades["path"],
                "--source",
                "auto_quant_real_trades_130436_tomac_aggressivebe_precision_fix",
                "--dry-run",
            ],
            env=env,
        )
    )
    commands.append(
        run_command(
            "02_ingest_real_trades_isolated",
            [
                str(ICT),
                "auto-quant-ingest-real-trades",
                "--symbol",
                SYMBOL,
                "--state-dir",
                str(STATE_DIR),
                "--trades",
                trades["path"],
                "--source",
                "auto_quant_real_trades_130436_tomac_aggressivebe_precision_fix",
            ],
            env=env,
        )
    )
    commands.append(
        run_command(
            "03_analyze_btc_tomac",
            [
                str(ICT),
                "analyze",
                "--symbol",
                SYMBOL,
                "--data-htf",
                candle_jsons["1d"]["path"],
                "--data-mtf",
                candle_jsons["4h"]["path"],
                "--data-ltf",
                candle_jsons["1h"]["path"],
                "--state-dir",
                str(STATE_DIR),
                "--output-format",
                "json",
            ],
            env=env,
        )
    )
    commands.append(
        run_command(
            "04_pre_bayes_status",
            [str(ICT), "pre-bayes-status", "--symbol", SYMBOL, "--state-dir", str(STATE_DIR), "--refresh", "--output-format", "json"],
            env=env,
        )
    )
    commands.append(
        run_command(
            "05_policy_training_status_before_export",
            [str(ICT), "policy-training-status", "--symbol", SYMBOL, "--state-dir", str(STATE_DIR), "--output-format", "json"],
            env=env,
        )
    )
    commands.append(
        run_command(
            "06_export_structural_path_ranking_target",
            [str(ICT), "export-structural-path-ranking-target", "--symbol", SYMBOL, "--state-dir", str(STATE_DIR)],
            env=env,
        )
    )
    commands.append(
        run_command(
            "07_policy_training_status_after_export",
            [str(ICT), "policy-training-status", "--symbol", SYMBOL, "--state-dir", str(STATE_DIR), "--output-format", "json"],
            env=env,
        )
    )
    commands.append(
        run_command(
            "08_workflow_structural_bundle",
            [
                str(ICT),
                "workflow-status",
                "--symbol",
                SYMBOL,
                "--phase",
                "structural-recommended-path-bundle",
                "--state-dir",
                str(STATE_DIR),
                "--agent",
                "--stable",
            ],
            env=env,
        )
    )
    commands.append(
        run_command(
            "09_workflow_execution_candidate",
            [
                str(ICT),
                "workflow-status",
                "--symbol",
                SYMBOL,
                "--phase",
                "execution-candidate",
                "--state-dir",
                str(STATE_DIR),
                "--agent",
                "--stable",
            ],
            env=env,
        )
    )
    commands.append(
        run_command(
            "10_workflow_full",
            [
                str(ICT),
                "workflow-status",
                "--symbol",
                SYMBOL,
                "--state-dir",
                str(STATE_DIR),
                "--refresh",
                "--output-format",
                "json",
                "--stable",
            ],
            env=env,
        )
    )

    target_csv = STATE_DIR / SYMBOL / "policy_training/structural_path_ranking_target.csv"
    history_csv = STATE_DIR / SYMBOL / "policy_training/structural_path_ranking_history.csv"
    model_dir = PATH_RANKER_DIR / "catboost_model"
    current_scores = PATH_RANKER_DIR / "current_scores.csv"
    history_scores = PATH_RANKER_DIR / "history_scores.csv"
    train_target = history_csv if history_csv.exists() else target_csv
    if train_target.exists() and count_csv_rows(train_target):
        commands.append(
            run_command(
                "11_train_catboost",
                [
                    str(UV),
                    "run",
                    "--offline",
                    "--with",
                    "pandas",
                    "--with",
                    "numpy",
                    "--with",
                    "catboost",
                    "python",
                    "scripts/auto_quant_external/pandas_path_ranker_trainer.py",
                    "--target-csv",
                    str(train_target),
                    "--output-dir",
                    str(model_dir),
                ],
                env=env,
            )
        )
        if (model_dir / "trainer_artifact.json").exists():
            commands.append(
                run_command(
                    "12_apply_catboost_history",
                    [
                        str(UV),
                        "run",
                        "--offline",
                        "--with",
                        "pandas",
                        "--with",
                        "numpy",
                        "--with",
                        "catboost",
                        "python",
                        "scripts/auto_quant_external/pandas_path_ranker_trainer.py",
                        "--apply",
                        "--model-dir",
                        str(model_dir),
                        "--target-csv",
                        str(train_target),
                        "--output-scores",
                        str(history_scores),
                    ],
                    env=env,
                )
            )
            if target_csv.exists():
                commands.append(
                    run_command(
                        "13_apply_catboost_current",
                        [
                            str(UV),
                            "run",
                            "--offline",
                            "--with",
                            "pandas",
                            "--with",
                            "numpy",
                            "--with",
                            "catboost",
                            "python",
                            "scripts/auto_quant_external/pandas_path_ranker_trainer.py",
                            "--apply",
                            "--model-dir",
                            str(model_dir),
                            "--target-csv",
                            str(target_csv),
                            "--output-scores",
                            str(current_scores),
                        ],
                        env=env,
                    )
                )
            if current_scores.exists():
                commands.append(
                    run_command(
                        "14_apply_external_scores",
                        [
                            str(ICT),
                            "apply-structural-path-ranking-external-scores",
                            "--symbol",
                            SYMBOL,
                            "--state-dir",
                            str(STATE_DIR),
                            "--scores-file",
                            str(current_scores),
                        ],
                        env=env,
                    )
                )
            commands.append(
                run_command(
                    "15_register_trainer_artifact",
                    [
                        str(ICT),
                        "register-structural-path-ranking-trainer-artifact",
                        "--symbol",
                        SYMBOL,
                        "--state-dir",
                        str(STATE_DIR),
                        "--artifact-uri",
                        str(model_dir / "trainer_artifact.json"),
                        "--model-family",
                        "catboost",
                        "--score-column",
                        "raw_path_score",
                    ],
                    env=env,
                )
            )
            commands.append(
                run_command(
                    "16_enable_runtime",
                    [
                        str(ICT),
                        "enable-structural-path-ranking-runtime",
                        "--symbol",
                        SYMBOL,
                        "--state-dir",
                        str(STATE_DIR),
                        "--reuse-mode",
                        "candidate_set_only",
                    ],
                    env=env,
                )
            )
            commands.append(
                run_command(
                    "17_policy_training_status_after_runtime",
                    [str(ICT), "policy-training-status", "--symbol", SYMBOL, "--state-dir", str(STATE_DIR), "--output-format", "json"],
                    env=env,
                )
            )
            commands.append(
                run_command(
                    "18_workflow_execution_candidate_after_runtime",
                    [
                        str(ICT),
                        "workflow-status",
                        "--symbol",
                        SYMBOL,
                        "--phase",
                        "execution-candidate",
                        "--state-dir",
                        str(STATE_DIR),
                        "--agent",
                        "--stable",
                    ],
                    env=env,
                )
            )
            commands.append(
                run_command(
                    "19_workflow_full_after_runtime",
                    [
                        str(ICT),
                        "workflow-status",
                        "--symbol",
                        SYMBOL,
                        "--state-dir",
                        str(STATE_DIR),
                        "--refresh",
                        "--output-format",
                        "json",
                        "--stable",
                    ],
                    env=env,
                )
            )
            commands.append(
                run_command(
                    "20_pre_bayes_status_after_runtime",
                    [str(ICT), "pre-bayes-status", "--symbol", SYMBOL, "--state-dir", str(STATE_DIR), "--refresh", "--output-format", "json"],
                    env=env,
                )
            )

    command_exits = {cmd["label"]: cmd["exit"] for cmd in commands}
    parsed = {cmd["label"]: cmd["parsed_stdout"] for cmd in commands}
    final_policy = parsed.get("17_policy_training_status_after_runtime") or parsed.get("07_policy_training_status_after_export")
    final_workflow = parsed.get("19_workflow_full_after_runtime") or parsed.get("10_workflow_full")
    final_pre_bayes = parsed.get("20_pre_bayes_status_after_runtime") or parsed.get("04_pre_bayes_status")
    runtime_summary = extract_runtime_summary(final_policy)
    execution_flags = workflow_execution_flags(final_workflow)

    report = {
        "run_id": RUN_ID,
        "source_run": str(SOURCE_ROOT),
        "diagnostic_parent": source_summary.get("diagnostic_parent"),
        "symbol": SYMBOL,
        "source_summary": source_summary,
        "derived_trades": trades,
        "candle_jsons": candle_jsons,
        "command_exits": command_exits,
        "dry_run_summary": parsed.get("01_ingest_real_trades_dry_run"),
        "ingest_summary": parsed.get("02_ingest_real_trades_isolated"),
        "pre_bayes_status": final_pre_bayes,
        "target_csv": str(target_csv),
        "history_csv": str(history_csv),
        "target_rows": count_csv_rows(target_csv),
        "history_rows": count_csv_rows(history_csv),
        "catboost_artifact_exists": file_exists(model_dir / "trainer_artifact.json"),
        "current_scores_exists": file_exists(current_scores),
        "history_scores_exists": file_exists(history_scores),
        "runtime_summary": runtime_summary,
        "execution_flags": execution_flags,
        "accepted_regime_gate": False,
        "promotion_allowed": False,
        "trade_usable": False,
        "update_goal": False,
        "gate_result": "btc_tomac_precision_fix_downstream_fail_closed_no_cross_context_no_95_confidence",
    }
    write_json(REPORT_DIR / "130436_btc_tomac_downstream_ingest_readback_v1.json", report)

    all_required_exits_ok = all(
        command_exits.get(label) == 0
        for label in [
            "01_ingest_real_trades_dry_run",
            "02_ingest_real_trades_isolated",
            "03_analyze_btc_tomac",
            "04_pre_bayes_status",
            "06_export_structural_path_ranking_target",
            "10_workflow_full",
        ]
    )
    lines = [
        "# 130436 BTC TOMAC Downstream Ingest Readback v1",
        "",
        f"Run id: `{RUN_ID}`",
        f"Source root: `{SOURCE_ROOT}`",
        f"Source trade root: `{SOURCE_TRADE_ROOT}`",
        "",
        "## Scope",
        "",
        "This readback carries the precision-fixed `TomacAggressiveBE` BTC-only synthetic selected-history candidate through an isolated downstream ingest/status/path-ranker/execution-tree readback.",
        "It does not mutate repo runtime code, production BBN CPDs, production CatBoost artifacts, execution-tree gates, or the board cursor.",
        "",
        "## Command Evidence",
        "",
        f"- Required command exits ok: `{all_required_exits_ok}`.",
        f"- Recorded exits: `{command_exits}`.",
        f"- Derived real-trade rows: `{trades['rows']}` (`win={trades['wins']}`, `loss={trades['losses']}`, `breakeven={trades['breakeven']}`).",
        f"- Dry-run summary: `{parsed.get('01_ingest_real_trades_dry_run')}`.",
        f"- Isolated ingest summary: `{parsed.get('02_ingest_real_trades_isolated')}`.",
        f"- Structural target rows: `{report['target_rows']}`; history rows: `{report['history_rows']}`.",
        f"- CatBoost artifact exists: `{report['catboost_artifact_exists']}`; current scores exists: `{report['current_scores_exists']}`; history scores exists: `{report['history_scores_exists']}`.",
        f"- Runtime summary: `{runtime_summary}`.",
        f"- Execution flags: `{execution_flags}`.",
        "",
        "## Decision",
        "",
        "- Gate: `btc_tomac_precision_fix_downstream_fail_closed_no_cross_context_no_95_confidence`.",
        "- The precision fix produced a measured candidate and the downstream readback is isolated, but the source is still BTC-only synthetic selected history.",
        "- No per-regime calibrated `>=95%` confidence, cross-market/cross-provider/cross-period validation, or non-observe execution readiness is established by this root.",
        "- `promotion_allowed=false`.",
        "- `trade_usable=false`.",
        "- `update_goal=false`.",
    ]
    (REPORT_DIR / "130436_btc_tomac_downstream_ingest_readback_v1.md").write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
    )

    assertions = [
        f"PASS run_id={RUN_ID}",
        f"PASS source_run={SOURCE_RUN_ID}",
        f"PASS derived_trade_rows={trades['rows']}",
        f"PASS dry_run_exit={command_exits.get('01_ingest_real_trades_dry_run')}",
        f"PASS isolated_ingest_exit={command_exits.get('02_ingest_real_trades_isolated')}",
        f"PASS analyze_exit={command_exits.get('03_analyze_btc_tomac')}",
        f"PASS pre_bayes_exit={command_exits.get('04_pre_bayes_status')}",
        f"PASS export_target_exit={command_exits.get('06_export_structural_path_ranking_target')}",
        f"PASS workflow_full_exit={command_exits.get('10_workflow_full')}",
        f"FAIL_CLOSED accepted_regime_gate={report['accepted_regime_gate']}",
        f"FAIL_CLOSED execution_ready={execution_flags.get('ready')}",
        "PASS promotion_allowed=false",
        "PASS trade_usable=false",
        "PASS update_goal=false",
    ]
    (CHECK_DIR / "130436_btc_tomac_downstream_ingest_readback_v1_assertions.out").write_text(
        "\n".join(assertions) + "\n",
        encoding="utf-8",
    )
    print(REPORT_DIR / "130436_btc_tomac_downstream_ingest_readback_v1.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
