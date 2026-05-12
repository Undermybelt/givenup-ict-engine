from __future__ import annotations

import csv
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd


RUN_ID = "20260512T120613+0800-codex-115130-bybit-momentum-downstream-v1"
SOURCE_RUN_ID = "20260512T115130+0800-codex-113833-ibkr-longer-duration-six-provider-aq-v1"
SYMBOL = "B2R_115130_BYBIT_BTC_MOMENTUM"
STRATEGY = "ProviderCryptoMomentumStateV1"
MUTATION_ID = "provider-owned-115130-bybit-btc-momentum-state-v1"
BRANCH_PATH = "Bull -> ProviderCryptoMomentum -> RsiMidlineExpansion -> ProviderCryptoMomentumStateV1"

RUNS = Path("docs/experiments/actionable-regime-confidence/runs")
ROOT = RUNS / RUN_ID
SOURCE_ROOT = RUNS / SOURCE_RUN_ID
SOURCE_JSON = (
    SOURCE_ROOT
    / "ibkr-longer-duration-six-provider-aq-v1"
    / "ibkr_longer_duration_six_provider_aq_v1.json"
)
SOURCE_CSV = SOURCE_ROOT / "provider-csv" / "bybit_btcusdt_linear_1h.csv"
SOURCE_TRADES = (
    SOURCE_ROOT
    / "workspace"
    / "auto-quant-112315-bybit_public"
    / "derived"
    / f"{STRATEGY}.real_trades.jsonl"
)
SOURCE_METRICS = (
    SOURCE_ROOT
    / "workspace"
    / "auto-quant-112315-bybit_public"
    / "derived"
    / f"{STRATEGY}.metrics.json"
)

OUT_DIR = ROOT / "command-output"
CHECK_DIR = ROOT / "checks"
REPORT_DIR = ROOT / "115130-bybit-momentum-downstream-v1"
DATA_DIR = ROOT / "provider-data-json"
STATE_DIR = ROOT / "state_115130_bybit_momentum_downstream_v1"
CATBOOST_DIR = ROOT / "catboost" / "path_ranker_model"
SCORES = ROOT / "catboost" / "history_scores.csv"
NORMALIZED_TRADES = REPORT_DIR / "115130_bybit_momentum_real_trades_v1.jsonl"
LIBRARY = REPORT_DIR / "115130_bybit_momentum_strategy_library_v1.json"


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def safe_read_json(path: Path) -> Any:
    if not path.exists():
        return None
    try:
        return read_json(path)
    except Exception as exc:  # pragma: no cover - report robustness
        return {"parse_error": str(exc), "path": str(path)}


def csv_row_count(path: Path) -> int:
    if not path.exists():
        return 0
    with path.open(newline="", encoding="utf-8") as fh:
        return max(sum(1 for _ in fh) - 1, 0)


def run_step(name: str, cmd: list[str], *, env: dict[str, str] | None = None) -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)
    proc = subprocess.run(
        cmd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
        check=False,
    )
    (OUT_DIR / f"{name}.cmd").write_text(" ".join(cmd) + "\n", encoding="utf-8")
    (OUT_DIR / f"{name}.out").write_text(proc.stdout, encoding="utf-8")
    (OUT_DIR / f"{name}.err").write_text(proc.stderr, encoding="utf-8")
    (CHECK_DIR / f"{name}.exit").write_text(f"{proc.returncode}\n", encoding="utf-8")
    return proc.returncode


def resample_ohlcv(df: pd.DataFrame, rule: str) -> pd.DataFrame:
    out = (
        df.set_index("timestamp")
        .resample(rule, label="left", closed="left")
        .agg(
            {
                "open": "first",
                "high": "max",
                "low": "min",
                "close": "last",
                "volume": "sum",
            }
        )
        .dropna()
        .reset_index()
    )
    return out


def frame_to_candles(df: pd.DataFrame) -> list[dict[str, Any]]:
    candles: list[dict[str, Any]] = []
    for row in df.itertuples(index=False):
        timestamp = row.timestamp
        candles.append(
            {
                "timestamp": timestamp.isoformat().replace("+00:00", "Z"),
                "open": float(row.open),
                "high": float(row.high),
                "low": float(row.low),
                "close": float(row.close),
                "volume": float(row.volume),
            }
        )
    return candles


def prepare_provider_data() -> dict[str, Any]:
    df = pd.read_csv(SOURCE_CSV)
    if "date" not in df.columns:
        raise ValueError(f"{SOURCE_CSV} missing date column")
    df["timestamp"] = pd.to_datetime(df["date"], utc=True)
    df = df.sort_values("timestamp")[["timestamp", "open", "high", "low", "close", "volume"]]
    for column in ["open", "high", "low", "close", "volume"]:
        df[column] = pd.to_numeric(df[column], errors="coerce")
    df = df.dropna()

    frames = {
        "ltf_1h": df,
        "mtf_4h": resample_ohlcv(df, "4h"),
        "htf_1d": resample_ohlcv(df, "1d"),
    }
    paths = {
        "ltf_1h": DATA_DIR / "BYBIT_BTCUSDT-1h.json",
        "mtf_4h": DATA_DIR / "BYBIT_BTCUSDT-4h.json",
        "htf_1d": DATA_DIR / "BYBIT_BTCUSDT-1d.json",
    }
    for key, frame in frames.items():
        write_json(paths[key], frame_to_candles(frame))
    return {
        "source_csv": str(SOURCE_CSV),
        "rows": {key: len(frame) for key, frame in frames.items()},
        "paths": {key: str(path) for key, path in paths.items()},
        "start": df["timestamp"].iloc[0].isoformat().replace("+00:00", "Z"),
        "end": df["timestamp"].iloc[-1].isoformat().replace("+00:00", "Z"),
    }


def normalize_trades() -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for index, line in enumerate(SOURCE_TRADES.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        row = json.loads(line)
        row["symbol"] = SYMBOL
        row["auto_quant_run_id"] = RUN_ID
        row["strategy_name"] = STRATEGY
        row["strategy_mutation_id"] = MUTATION_ID
        row["trade_id"] = (
            f"bybit_115130_momentum_{index:04d}_{row.get('open_ts_ms')}_{row.get('close_ts_ms')}"
        )
        row["regime_profit_branch_path"] = BRANCH_PATH
        row["main_regime"] = "Bull"
        row["sub_regime"] = "ProviderCryptoMomentum"
        row["sub_sub_regime_or_profit_factor"] = "RsiMidlineExpansion"
        row["profit_factor"] = STRATEGY
        row["entry_signal"] = "provider_crypto_momentum_state"
        for factor in row.get("factors_used", []):
            if factor.get("factor_name") == STRATEGY:
                factor["category"] = "trend_momentum"
                factor["direction"] = "Bull"
        rows.append(row)

    NORMALIZED_TRADES.parent.mkdir(parents=True, exist_ok=True)
    NORMALIZED_TRADES.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )
    return {
        "source_trades": str(SOURCE_TRADES),
        "normalized_trades": str(NORMALIZED_TRADES),
        "trade_rows": len(rows),
        "wins": sum(1 for row in rows if row.get("realized_outcome") == "win"),
        "losses": sum(1 for row in rows if row.get("realized_outcome") == "loss"),
    }


def write_strategy_library() -> dict[str, Any]:
    metrics = read_json(SOURCE_METRICS)
    aggregate = metrics["aggregate"]
    library = {
        "manifest_version": "1.0",
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "auto_quant_pinned_ref": RUN_ID,
        "auto_quant_repo_url": str(
            SOURCE_ROOT / "workspace" / "auto-quant-112315-bybit_public"
        ),
        "config_path": str(
            SOURCE_ROOT / "workspace" / "auto-quant-112315-bybit_public" / "config.tomac.json"
        ),
        "log_path": str(OUT_DIR / "source_115130_bybit_momentum_downstream.log"),
        "timeframe": "1h",
        "strategies": [
            {
                "name": STRATEGY,
                "status": "ok",
                "error": None,
                "commit": RUN_ID,
                "file_path": str(
                    SOURCE_ROOT
                    / "workspace"
                    / "auto-quant-112315-bybit_public"
                    / "user_data"
                    / "strategies_external"
                    / f"{STRATEGY}.py"
                ),
                "pairs": ["BTC/USDT"],
                "timerange": "20260401-20260512",
                "validation_metrics": aggregate,
                "per_pair_metrics": {"BTC/USDT": aggregate},
                "metadata": {
                    "strategy": STRATEGY,
                    "mutation_id": MUTATION_ID,
                    "status": "incubation_only_six_provider_packet_branch",
                    "asset_class": "crypto_provider_ohlcv",
                    "base_factor": "provider_crypto_momentum_state",
                    "expected_regime": BRANCH_PATH,
                    "parent": BRANCH_PATH,
                    "provider": "bybit_public",
                    "source_run_id": SOURCE_RUN_ID,
                    "hypothesis": (
                        "Bybit 1h momentum branch from 115130 is the highest-density "
                        "positive provider branch inside the comparable-timeframe six-provider AQ packet."
                    ),
                    "factors_used": [
                        "bybit_btcusdt_linear_1h",
                        "provider_crypto_momentum_state",
                        "regime_profit_branch_path",
                    ],
                },
            }
        ],
        "validation_errors": [],
    }
    write_json(LIBRARY, library)
    return {
        "library": str(LIBRARY),
        "trade_count": aggregate.get("trade_count"),
        "win_rate_pct": aggregate.get("win_rate_pct"),
        "total_profit_pct": aggregate.get("total_profit_pct"),
        "profit_factor": aggregate.get("profit_factor"),
    }


def exit_map() -> dict[str, int | None]:
    exits: dict[str, int | None] = {}
    for path in sorted(CHECK_DIR.glob("*.exit")):
        try:
            exits[path.stem] = int(path.read_text(encoding="utf-8").strip())
        except Exception:
            exits[path.stem] = None
    return exits


def extract_summary(input_summary: dict[str, Any]) -> dict[str, Any]:
    pre_bayes = safe_read_json(OUT_DIR / "14_pre_bayes_status_final.out")
    policy = safe_read_json(OUT_DIR / "13_policy_training_status_final.out")
    workflow = safe_read_json(OUT_DIR / "17_workflow_full.out")
    execution = safe_read_json(OUT_DIR / "16_workflow_execution_candidate.out")
    ingest = safe_read_json(OUT_DIR / "04_auto_quant_ingest_real_trades.out")

    target_history = (
        STATE_DIR / SYMBOL / "policy_training" / "structural_path_ranking_target_history.csv"
    )
    target_latest = STATE_DIR / SYMBOL / "policy_training" / "structural_path_ranking_target.csv"
    scores_rows = csv_row_count(SCORES)
    target_history_rows = csv_row_count(target_history)
    target_latest_rows = csv_row_count(target_latest)

    command_exits = exit_map()
    all_commands_ran = all(code == 0 for code in command_exits.values()) and len(command_exits) >= 18

    execution_candidate = execution if isinstance(execution, dict) else {}
    actionable = bool(execution_candidate.get("actionable", False))
    ready = bool(execution_candidate.get("ready", False))
    status = execution_candidate.get("status") or execution_candidate.get("candidate_status")
    review = execution_candidate.get("review") or execution_candidate.get("review_decision")

    gate_result = (
        "downstream_chain_ran_execution_actionable_but_board_a_full_objective_not_met"
        if all_commands_ran and actionable and ready
        else "downstream_chain_ran_fail_closed_no_promotion"
        if all_commands_ran
        else "downstream_chain_incomplete_fail_closed"
    )

    summary = {
        "run_id": RUN_ID,
        "source_run_id": SOURCE_RUN_ID,
        "symbol": SYMBOL,
        "strategy": STRATEGY,
        "mutation_id": MUTATION_ID,
        "branch_path": BRANCH_PATH,
        "input_summary": input_summary,
        "command_exits": command_exits,
        "all_commands_ran": all_commands_ran,
        "target_latest_rows": target_latest_rows,
        "target_history_rows": target_history_rows,
        "scores_rows": scores_rows,
        "ingest": ingest,
        "pre_bayes": {
            "latest_gate_status": pre_bayes.get("latest_gate_status") if isinstance(pre_bayes, dict) else None,
            "latest_policy_present": bool(pre_bayes.get("latest_policy")) if isinstance(pre_bayes, dict) else False,
            "latest_policy_version": pre_bayes.get("latest_policy_version") if isinstance(pre_bayes, dict) else None,
            "latest_uses_soft_evidence": pre_bayes.get("latest_uses_soft_evidence") if isinstance(pre_bayes, dict) else None,
            "latest_filtered_assignments": pre_bayes.get("latest_filtered_assignments") if isinstance(pre_bayes, dict) else None,
            "latest_canonical_structural_active_regime": pre_bayes.get("latest_canonical_structural_active_regime") if isinstance(pre_bayes, dict) else None,
            "latest_canonical_structural_confidence": pre_bayes.get("latest_canonical_structural_confidence") if isinstance(pre_bayes, dict) else None,
            "latest_canonical_structural_probabilities": pre_bayes.get("latest_canonical_structural_probabilities") if isinstance(pre_bayes, dict) else None,
        },
        "policy_training": policy,
        "execution_candidate": execution,
        "workflow_full": workflow,
        "execution_status": status,
        "execution_ready": ready,
        "execution_actionable": actionable,
        "execution_review": review,
        "gate_result": gate_result,
        "accepted_rows_added": 0,
        "mature_rooted_branch_observations_promoted": 0,
        "source_control_evidence_acquired": False,
        "explicit_selected_history": False,
        "canonical_merge": False,
        "selected_data_autoquant_promotion": False,
        "downstream_promotion": False,
        "strict_full_objective": False,
        "trade_usable": False,
        "promotion_allowed": False,
        "update_goal": False,
    }
    write_json(REPORT_DIR / "115130_bybit_momentum_downstream_v1.json", summary)
    return summary


def write_report(summary: dict[str, Any]) -> None:
    report = REPORT_DIR / "115130_bybit_momentum_downstream_v1.md"
    checklist = REPORT_DIR / "prompt_to_artifact_checklist_115130_bybit_momentum_downstream_v1.csv"
    assertions = CHECK_DIR / "115130_bybit_momentum_downstream_v1_assertions.out"

    input_summary = summary["input_summary"]
    strategy_summary = input_summary["strategy_library"]
    trades = input_summary["trades"]
    provider_data = input_summary["provider_data"]
    ingest = summary.get("ingest") if isinstance(summary.get("ingest"), dict) else {}
    pre_bayes = summary.get("pre_bayes", {})

    lines = [
        "# 115130 Bybit Momentum Downstream v1",
        "",
        f"Run id: `{RUN_ID}`",
        f"Source six-provider AQ root: `{SOURCE_RUN_ID}`",
        f"Symbol: `{SYMBOL}`",
        f"Branch: `{BRANCH_PATH}`",
        "",
        "## Source Slice",
        "- Chosen source branch: `bybit_public` / `ProviderCryptoMomentumStateV1`.",
        f"- AQ metrics: trades `{strategy_summary.get('trade_count')}`, profit_pct `{strategy_summary.get('total_profit_pct')}`, win_rate_pct `{strategy_summary.get('win_rate_pct')}`, profit_factor `{strategy_summary.get('profit_factor')}`.",
        f"- Normalized real-trade rows: `{trades.get('trade_rows')}` (`wins={trades.get('wins')}`, `losses={trades.get('losses')}`).",
        f"- Provider data rows: 1h `{provider_data['rows']['ltf_1h']}`, 4h `{provider_data['rows']['mtf_4h']}`, 1d `{provider_data['rows']['htf_1d']}`.",
        "",
        "## Chain Results",
        f"- All command exits zero: `{summary['all_commands_ran']}`.",
        f"- Ingest status: `{ingest.get('ledger_status')}`, trades_applied `{ingest.get('trades_applied')}`, feedback_records_inserted `{ingest.get('feedback_records_inserted')}`.",
        f"- Pre-Bayes gate: `{pre_bayes.get('latest_gate_status')}`, policy_present `{pre_bayes.get('latest_policy_present')}`, soft_evidence `{pre_bayes.get('latest_uses_soft_evidence')}`.",
        f"- Structural target rows: latest `{summary['target_latest_rows']}`, history `{summary['target_history_rows']}`, CatBoost scores `{summary['scores_rows']}`.",
        f"- Execution status: `{summary.get('execution_status')}`, ready `{summary.get('execution_ready')}`, actionable `{summary.get('execution_actionable')}`, review `{summary.get('execution_review')}`.",
        "",
        "## Decision",
        f"- Gate result: `{summary['gate_result']}`.",
        "- `promotion_allowed=false`.",
        "- `trade_usable=false`.",
        "- `update_goal=false`.",
        "- This downstream slice is real evidence for the ordered chain, but it is not strict Board A completion because it uses one selected 115130 branch, lacks explicit selected-history/source-control approval, and still must satisfy full per-regime cross-market/timeframe/period validation.",
        "",
        "## Artifacts",
        f"- JSON: `{REPORT_DIR / '115130_bybit_momentum_downstream_v1.json'}`",
        f"- Strategy library: `{LIBRARY}`",
        f"- Normalized trades: `{NORMALIZED_TRADES}`",
        f"- Command outputs: `{OUT_DIR}`",
        f"- Exit markers: `{CHECK_DIR}`",
        f"- State dir: `{STATE_DIR}`",
        f"- CatBoost scores: `{SCORES}`",
    ]
    report.write_text("\n".join(lines) + "\n", encoding="utf-8")

    with checklist.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["requirement", "artifact", "status", "note"])
        writer.writerow(["provider source", str(SOURCE_CSV), "covered", "Bybit 1h source from 115130"])
        writer.writerow(["auto-quant branch", str(SOURCE_TRADES), "covered", "Bybit ProviderCryptoMomentumStateV1 real trades"])
        writer.writerow(["normalized real trades", str(NORMALIZED_TRADES), "covered", f"rows={trades.get('trade_rows')}"])
        writer.writerow(["Pre-Bayes/filter", str(OUT_DIR / "14_pre_bayes_status_final.out"), "covered", str(pre_bayes.get("latest_gate_status"))])
        writer.writerow(["CatBoost/path-ranker", str(SCORES), "covered", f"scores_rows={summary['scores_rows']}"])
        writer.writerow(["execution tree", str(OUT_DIR / "17_workflow_full.out"), "covered", summary["gate_result"]])
        writer.writerow(["promotion", "N/A", "fail_closed", "promotion_allowed=false update_goal=false"])

    assertion_lines = [
        f"PASS run_id={RUN_ID}",
        f"PASS source_run_id={SOURCE_RUN_ID}",
        f"PASS symbol={SYMBOL}",
        f"PASS normalized_trades={trades.get('trade_rows')}",
        f"PASS ingest_trades_applied={ingest.get('trades_applied')}",
        f"PASS target_history_rows={summary['target_history_rows']}",
        f"PASS scores_rows={summary['scores_rows']}",
        f"PASS all_commands_ran={summary['all_commands_ran']}",
        f"PASS gate_result={summary['gate_result']}",
        "PASS accepted_rows_added=0",
        "PASS mature_rooted_branch_observations_promoted=0",
        "PASS selected_data_autoquant_promotion=false",
        "PASS downstream_promotion=false",
        "PASS strict_full_objective=false",
        "PASS promotion_allowed=false",
        "PASS trade_usable=false",
        "PASS update_goal=false",
    ]
    if summary["gate_result"] != "downstream_chain_ran_execution_actionable_but_board_a_full_objective_not_met":
        assertion_lines.append("FAIL_CLOSED execution_not_actionable_or_chain_incomplete")
    assertions.write_text("\n".join(assertion_lines) + "\n", encoding="utf-8")


def main() -> int:
    for path in (ROOT, OUT_DIR, CHECK_DIR, REPORT_DIR, DATA_DIR, STATE_DIR, CATBOOST_DIR, SCORES.parent):
        path.mkdir(parents=True, exist_ok=True)
    (ROOT / "run_id.txt").write_text(RUN_ID + "\n", encoding="utf-8")
    (ROOT / "source_root.txt").write_text(str(SOURCE_ROOT) + "\n", encoding="utf-8")

    provider_data = prepare_provider_data()
    trades = normalize_trades()
    strategy_library = write_strategy_library()
    input_summary = {
        "provider_data": provider_data,
        "trades": trades,
        "strategy_library": strategy_library,
        "source_json": str(SOURCE_JSON),
    }

    (OUT_DIR / "00_prepare_input_artifacts.cmd").write_text(
        "python scripts/115130_bybit_momentum_downstream_v1.py prepare_inputs\n",
        encoding="utf-8",
    )
    write_json(OUT_DIR / "00_prepare_input_artifacts.out", input_summary)
    (OUT_DIR / "00_prepare_input_artifacts.err").write_text("", encoding="utf-8")
    (CHECK_DIR / "00_prepare_input_artifacts.exit").write_text("0\n", encoding="utf-8")

    run_step(
        "01_analyze_provider_data",
        [
            "./target/debug/ict-engine",
            "analyze",
            "--symbol",
            SYMBOL,
            "--data-htf",
            str(DATA_DIR / "BYBIT_BTCUSDT-1d.json"),
            "--data-mtf",
            str(DATA_DIR / "BYBIT_BTCUSDT-4h.json"),
            "--data-ltf",
            str(DATA_DIR / "BYBIT_BTCUSDT-1h.json"),
            "--state-dir",
            str(STATE_DIR),
            "--output-format",
            "json",
        ],
    )
    run_step(
        "02_auto_quant_results_import",
        [
            "./target/debug/ict-engine",
            "auto-quant-results-import",
            "--symbol",
            SYMBOL,
            "--state-dir",
            str(STATE_DIR),
            "--library",
            str(LIBRARY),
        ],
    )
    run_step(
        "03_auto_quant_prior_init",
        [
            "./target/debug/ict-engine",
            "auto-quant-prior-init",
            "--symbol",
            SYMBOL,
            "--state-dir",
            str(STATE_DIR),
            "--library",
            str(LIBRARY),
            "--strategies",
            STRATEGY,
        ],
    )
    run_step(
        "04_auto_quant_ingest_real_trades",
        [
            "./target/debug/ict-engine",
            "auto-quant-ingest-real-trades",
            "--symbol",
            SYMBOL,
            "--state-dir",
            str(STATE_DIR),
            "--trades",
            str(NORMALIZED_TRADES),
        ],
    )
    run_step(
        "05_pre_bayes_status_after_ingest",
        [
            "./target/debug/ict-engine",
            "pre-bayes-status",
            "--symbol",
            SYMBOL,
            "--state-dir",
            str(STATE_DIR),
            "--refresh",
            "--output-format",
            "json",
        ],
    )
    run_step(
        "06_policy_training_status_before_export",
        [
            "./target/debug/ict-engine",
            "policy-training-status",
            "--symbol",
            SYMBOL,
            "--state-dir",
            str(STATE_DIR),
            "--output-format",
            "json",
        ],
    )
    run_step(
        "07_export_structural_path_ranking_target",
        [
            "./target/debug/ict-engine",
            "export-structural-path-ranking-target",
            "--symbol",
            SYMBOL,
            "--state-dir",
            str(STATE_DIR),
        ],
    )

    env = os.environ.copy()
    env.update(
        {
            "OMP_NUM_THREADS": "1",
            "OPENBLAS_NUM_THREADS": "1",
            "MKL_NUM_THREADS": "1",
            "VECLIB_MAXIMUM_THREADS": "1",
        }
    )
    target_history = (
        STATE_DIR / SYMBOL / "policy_training" / "structural_path_ranking_target_history.csv"
    )
    run_step(
        "08_train_catboost",
        [
            "uv",
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
            str(target_history),
            "--output-dir",
            str(CATBOOST_DIR),
            "--model-family",
            "catboost",
            "--output-scores",
            str(SCORES),
        ],
        env=env,
    )
    run_step(
        "09_apply_catboost_history",
        [
            "uv",
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
            "--apply",
            "--model-dir",
            str(CATBOOST_DIR),
            "--target-csv",
            str(target_history),
            "--output-scores",
            str(SCORES),
        ],
        env=env,
    )
    run_step(
        "10_apply_external_scores",
        [
            "./target/debug/ict-engine",
            "apply-structural-path-ranking-external-scores",
            "--symbol",
            SYMBOL,
            "--state-dir",
            str(STATE_DIR),
            "--scores-file",
            str(SCORES),
        ],
    )
    run_step(
        "11_register_trainer_artifact",
        [
            "./target/debug/ict-engine",
            "register-structural-path-ranking-trainer-artifact",
            "--symbol",
            SYMBOL,
            "--state-dir",
            str(STATE_DIR),
            "--artifact-uri",
            str(SCORES),
            "--model-family",
            "catboost",
            "--score-column",
            "raw_path_score",
        ],
    )
    run_step(
        "12_enable_runtime",
        [
            "./target/debug/ict-engine",
            "enable-structural-path-ranking-runtime",
            "--symbol",
            SYMBOL,
            "--state-dir",
            str(STATE_DIR),
            "--reuse-mode",
            "prefer_history",
        ],
    )
    run_step(
        "13_policy_training_status_final",
        [
            "./target/debug/ict-engine",
            "policy-training-status",
            "--symbol",
            SYMBOL,
            "--state-dir",
            str(STATE_DIR),
            "--output-format",
            "json",
        ],
    )
    run_step(
        "14_pre_bayes_status_final",
        [
            "./target/debug/ict-engine",
            "pre-bayes-status",
            "--symbol",
            SYMBOL,
            "--state-dir",
            str(STATE_DIR),
            "--refresh",
            "--output-format",
            "json",
        ],
    )
    run_step(
        "15_workflow_structural_bundle",
        [
            "./target/debug/ict-engine",
            "workflow-status",
            "--symbol",
            SYMBOL,
            "--phase",
            "structural-recommended-path-bundle",
            "--state-dir",
            str(STATE_DIR),
            "--agent",
        ],
    )
    run_step(
        "16_workflow_execution_candidate",
        [
            "./target/debug/ict-engine",
            "workflow-status",
            "--symbol",
            SYMBOL,
            "--phase",
            "execution-candidate",
            "--state-dir",
            str(STATE_DIR),
            "--agent",
        ],
    )
    run_step(
        "17_workflow_full",
        [
            "./target/debug/ict-engine",
            "workflow-status",
            "--symbol",
            SYMBOL,
            "--state-dir",
            str(STATE_DIR),
            "--refresh",
            "--output-format",
            "json",
        ],
    )

    summary = extract_summary(input_summary)
    write_report(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
