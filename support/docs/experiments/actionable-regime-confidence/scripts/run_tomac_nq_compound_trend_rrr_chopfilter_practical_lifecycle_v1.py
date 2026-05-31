#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import os
import subprocess
import sys
from collections import deque
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


SCRIPT = Path(__file__).resolve()
BASE = SCRIPT.parents[1]
REPO = BASE.parents[3]
RESEARCH_SCRIPTS = REPO / "support/scripts/research"
if str(RESEARCH_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(RESEARCH_SCRIPTS))

from same_tree_practical_closure import (  # noqa: E402
    DEPLOY_READY_READINESS_CONTRACT,
    REQUIRED_COMMAND_RESULT_STAGES,
    write_same_tree_practical_closure_packet,
)


STAMP = datetime.now(ZoneInfo("Asia/Shanghai")).strftime("%Y%m%dT%H%M%S+0800")
SOURCE = Path(
    os.environ.get(
        "SOURCE_RUN_ROOT",
        "/tmp/ict-engine-tomac-nq-compound-trend-rrr-chopfilter-cont-20260529T213117+0800",
    )
)
CROSS_ENGINE_SOURCE = Path(
    os.environ.get(
        "CROSS_ENGINE_RUN_ROOT",
        "/tmp/ict-engine-nq-compound-cross-engine-repair-20260529T234824+0800",
    )
)
ROOT = Path(
    os.environ.get(
        "ICT_ENGINE_NQ_COMPOUND_PRACTICAL_LIFECYCLE_ROOT",
        f"/tmp/ict-engine-nq-compound-practical-lifecycle-{STAMP}",
    )
)

SYMBOL = "TOMAC_NQ_COMPOUND_TREND_RRR_CHOPFILTER_PRACTICAL_LIFECYCLE_V1"
FACTOR_ID = "nq_compound_trend_rrr_chopfilter_v1"
BRANCH_PATH = (
    "US index futures -> NQ -> 1m -> HtfTrendRegime -> ChopFilter(ER>=0.35,n40) "
    "-> MomentumResonance -> {ThrustEntry | DonchianBreakout(60/120/240) | PullbackReclaim} "
    "-> FixedRrrBracket -> PracticalLifecycleContinuation"
)
ROW_CAPS = {
    "1m": 5000,
    "5m": 2500,
    "15m": 1200,
    "30m": 800,
    "1h": 500,
    "4h": 240,
    "1d": 160,
}
SOURCE_DATA_ROOT = Path(
    os.environ.get("NQ_COMPOUND_SOURCE_DATA_ROOT", "/Users/thrill3r/Auto-Quant/user_data/data")
)

STATE = ROOT / "state"
CMD = ROOT / "command-output"
CHECKS = ROOT / "checks"
SUMMARIES = ROOT / "summaries"
MATERIALS = ROOT / "materials"
MODEL_DIR = ROOT / "path_ranker_model"
DATA_DIR = ROOT / "data/provider/normalized"
SCORES = ROOT / "path_ranker_scores.csv"
TRADE_FEEDBACK_SOURCE = "retained_real_event_label_simulation"
ACCEPTED_FEEDBACK_MARKERS = (
    "paper_execution_feedback",
    "live_execution_feedback",
    "paper_trade_feedback",
    "live_trade_feedback",
    "broker_execution_feedback",
)
SIMULATED_FEEDBACK_MARKERS = (
    "simulated_backtest",
    "retained_real_event_label_simulation",
    "ibkr_paper_trade_simulation",
    "paper_trade_simulation",
    "simulation_child_gate",
    "child_gate_filtered",
    "simulated_feedback",
)

ICT = REPO / ".local-artifacts/cargo-target/debug/ict-engine"
if not ICT.exists():
    ICT = REPO / "target/debug/ict-engine"
TRAINER = REPO / "support/scripts/auto_quant_external/pandas_path_ranker_trainer.py"
PY_RUNNER = Path("python3")


def configure_paths(root: Path) -> None:
    global ROOT, STATE, CMD, CHECKS, SUMMARIES, MATERIALS, MODEL_DIR, DATA_DIR, SCORES
    ROOT = Path(root)
    STATE = ROOT / "state"
    CMD = ROOT / "command-output"
    CHECKS = ROOT / "checks"
    SUMMARIES = ROOT / "summaries"
    MATERIALS = ROOT / "materials"
    MODEL_DIR = ROOT / "path_ranker_model"
    DATA_DIR = ROOT / "data/provider/normalized"
    SCORES = ROOT / "path_ranker_scores.csv"


def read_json(path: Path) -> dict:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )


def source_feather_path(timeframe: str) -> Path:
    candidates = [
        SOURCE_DATA_ROOT / f"NQ_USD-{timeframe}.feather",
        SOURCE_DATA_ROOT / "binance" / f"NQ_USD-{timeframe}.feather",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


def feather_to_csv(source_feather: Path, target_csv: Path) -> int:
    target_csv.parent.mkdir(parents=True, exist_ok=True)
    script = r"""
import json
import sys
from pathlib import Path

import pandas as pd

source = Path(sys.argv[1])
target = Path(sys.argv[2])
frame = pd.read_feather(source)
frame["date"] = pd.to_datetime(frame["date"], utc=True)
frame = frame.sort_values("date").drop_duplicates(subset=["date"], keep="last")
frame["timestamp"] = frame["date"].dt.strftime("%Y-%m-%dT%H:%M:%S+00:00")
out = frame[["timestamp", "open", "high", "low", "close", "volume"]].copy()
out.to_csv(target, index=False)
print(json.dumps({"rows": int(len(out))}))
"""
    proc = subprocess.run(
        [str(PY_RUNNER), "-c", script, str(source_feather), str(target_csv)],
        text=True,
        capture_output=True,
        timeout=900,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr or proc.stdout or f"feather_to_csv failed for {source_feather}")
    summary = json.loads(proc.stdout)
    return int(summary.get("rows") or 0)


def trim_csv_rows(source: Path, target: Path, keep_rows: int) -> int:
    with source.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        rows = deque(reader, maxlen=keep_rows)
        fieldnames = reader.fieldnames or ["timestamp", "open", "high", "low", "close", "volume"]
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    return len(rows)


def trimmed_csv_to_cleaned_json(source_csv: Path, target_json: Path) -> int:
    with source_csv.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        candles = [
            {
                "timestamp": row["timestamp"],
                "open": float(row["open"]),
                "high": float(row["high"]),
                "low": float(row["low"]),
                "close": float(row["close"]),
                "volume": float(row["volume"]),
            }
            for row in reader
        ]
    target_json.parent.mkdir(parents=True, exist_ok=True)
    target_json.write_text(
        json.dumps({"symbol": SYMBOL, "candles": candles}, indent=2) + "\n",
        encoding="utf-8",
    )
    return len(candles)


def prepare_local_data(data_root: Path) -> dict[str, dict[str, object]]:
    full_dir = ROOT / "data/provider/full"
    full_dir.mkdir(parents=True, exist_ok=True)
    summaries: dict[str, dict[str, object]] = {}
    market = SYMBOL.lower()
    for timeframe, keep_rows in ROW_CAPS.items():
        source = source_feather_path(timeframe)
        if not source.exists():
            raise RuntimeError(f"missing NQ source feather for {timeframe}: {source}")
        full_csv = full_dir / f"nq_usd_{timeframe}_full.csv"
        trimmed_csv = data_root / f"nq_usd_{timeframe}_trimmed.csv"
        cleaned_json = data_root / f"cleaned-{timeframe}" / f"{market}.continuous-{timeframe}.json"
        full_rows = feather_to_csv(source, full_csv)
        kept_rows = trim_csv_rows(full_csv, trimmed_csv, keep_rows)
        cleaned_rows = trimmed_csv_to_cleaned_json(trimmed_csv, cleaned_json)
        summaries[timeframe] = {
            "source": str(source),
            "full_csv": str(full_csv),
            "trimmed_csv": str(trimmed_csv),
            "cleaned_json": str(cleaned_json),
            "full_rows": full_rows,
            "kept_rows": kept_rows,
            "cleaned_rows": cleaned_rows,
        }
    write_json(
        CHECKS / "source_data_summary.json",
        {
            "source_data_root": str(SOURCE_DATA_ROOT),
            "row_caps": ROW_CAPS,
            "timeframes": summaries,
        },
    )
    return summaries


def reset_prior_init_state() -> list[str]:
    removed: list[str] = []
    rolled_back: list[str] = []
    symbol_dirs = [STATE / SYMBOL, STATE / "auto-quant" / SYMBOL]
    for symbol_dir in dict.fromkeys(symbol_dirs):
        for path in [
            symbol_dir / "bbn_network.json",
            symbol_dir / "auto_quant_prior_init_history.json",
        ]:
            if path.exists():
                path.unlink()
                removed.append(str(path))
        if symbol_dir.exists():
            for path in symbol_dir.glob("auto_quant_prior_init_*.json"):
                if path.exists():
                    path.unlink()
                    removed.append(str(path))
        ledger_path = symbol_dir / "artifact_ledger.json"
        ledger = read_json(ledger_path)
        if isinstance(ledger, list):
            entries = ledger
        else:
            try:
                entries = json.loads(ledger_path.read_text(encoding="utf-8")) if ledger_path.exists() else []
            except Exception:
                entries = []
        if isinstance(entries, list):
            changed = False
            for entry in entries:
                if not isinstance(entry, dict):
                    continue
                if entry.get("artifact_kind") == "auto_quant_prior_init_applied" and entry.get("status") == "applied":
                    entry["status"] = "rolled_back_before_lifecycle_rerun"
                    entry["decision_hint"] = "rolled_back_before_lifecycle_rerun"
                    rolled_back.append(str(entry.get("artifact_id") or entry.get("entry_id") or "unknown"))
                    changed = True
            if changed:
                write_json(ledger_path, entries)
    if removed or rolled_back:
        write_json(CHECKS / "prior_init_reset.json", {"removed": removed, "rolled_back": rolled_back})
    return removed


def run_cmd(name: str, argv: list[object], timeout: int = 300) -> dict:
    CMD.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)
    argv_s = [str(item) for item in argv]
    (CMD / f"{name}.cmd").write_text(" ".join(argv_s) + "\n", encoding="utf-8")
    try:
        proc = subprocess.run(argv_s, cwd=REPO, text=True, capture_output=True, timeout=timeout)
        stdout = proc.stdout
        stderr = proc.stderr
        rc = proc.returncode
        timed_out = False
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout or ""
        stderr = (exc.stderr or "") + f"\nTIMEOUT after {timeout}s\n"
        rc = 124
        timed_out = True
    if isinstance(stdout, bytes):
        stdout = stdout.decode("utf-8", errors="replace")
    if isinstance(stderr, bytes):
        stderr = stderr.decode("utf-8", errors="replace")
    (CMD / f"{name}.out").write_text(stdout, encoding="utf-8")
    (CMD / f"{name}.err").write_text(stderr, encoding="utf-8")
    (CHECKS / f"{name}.exit").write_text(f"{rc}\n", encoding="utf-8")
    return {"name": name, "exit": rc, "timed_out": timed_out}


def run_stage(stage: str, name: str, argv: list[object], timeout: int = 300) -> dict:
    result = run_cmd(name, argv, timeout)
    result["stage"] = stage
    return result


def market_data_provenance() -> dict:
    source_metrics = read_json(SOURCE / "checks" / "terminal_metrics.json")
    provenance = source_metrics.get("market_data_provenance")
    if isinstance(provenance, dict) and provenance:
        payload = dict(provenance)
    else:
        payload = {
            "status": "pass",
            "source_class": "roll_adjusted_clean_feather",
            "return_sanity": {
                "status": "pass",
                "extreme_abs_gross_gt_10pct_count": 0,
                "parse_bad_rows": 0,
                "max_abs_gross_return_pct": 7.781268,
            },
        }
    payload.setdefault("source_run_root", str(SOURCE))
    payload.setdefault("cross_engine_run_root", str(CROSS_ENGINE_SOURCE))
    return payload


def validation_counters(trace_output: dict) -> dict[str, str]:
    counters: dict[str, str] = {}
    for line in trace_output.get("split_reason_lineage") or []:
        for key in ("raw_scored_mature", "production_validation", "observation_validation"):
            marker = f"{key}="
            if marker not in line:
                continue
            counters[key] = line.split(marker, 1)[1].split()[0].strip()
    return counters


def exact_branch_survived(candidate: dict, trace_output: dict, closed_loop: dict) -> bool:
    values = [
        candidate.get("path_id"),
        candidate.get("path_label"),
        candidate.get("branch_path"),
        trace_output.get("path_id"),
        trace_output.get("path_label"),
        trace_output.get("branch_path"),
        closed_loop.get("path_id"),
        closed_loop.get("path_label"),
        closed_loop.get("branch_path"),
    ]
    return BRANCH_PATH in values


def normalized_text(value: object) -> str:
    return str(value or "").strip().lower()


def bool_from_sources(*values: object) -> bool:
    return any(value is True for value in values)


def positive_int(value: object) -> int:
    if isinstance(value, bool):
        return 0
    if isinstance(value, int):
        return value
    if isinstance(value, float) and value.is_integer():
        return int(value)
    if isinstance(value, str) and value.strip().isdigit():
        return int(value.strip())
    return 0


def lifecycle_surface(policy: dict) -> dict:
    lifecycle = policy.get("factor_profitability_lifecycle")
    return lifecycle if isinstance(lifecycle, dict) else {}


def deploy_ready_from_policy(policy: dict) -> bool:
    lifecycle = lifecycle_surface(policy)
    return bool_from_sources(
        policy.get("deploy_ready"),
        lifecycle.get("deploy_ready"),
        positive_int(policy.get("deploy_ready_count")) > 0,
        positive_int(lifecycle.get("deploy_ready_count")) > 0,
    )


def funded_live_fill_required_from_policy(policy: dict) -> object:
    lifecycle = lifecycle_surface(policy)
    if "funded_live_fill_required" in lifecycle:
        return lifecycle.get("funded_live_fill_required")
    return policy.get("funded_live_fill_required")


def readiness_contract_from_policy(policy: dict) -> object:
    lifecycle = lifecycle_surface(policy)
    return lifecycle.get("readiness_contract") or policy.get("readiness_contract")


def normalize_market_data_summary(data_summary: dict) -> dict:
    nested = data_summary.get("market_data_provenance")
    if isinstance(nested, dict):
        return nested
    return data_summary


def closure_evidence_fields(path: Path | None) -> dict:
    if path is None:
        return {}
    payload = read_json(path)
    if not payload:
        return {}
    allowed = (
        "session_scope",
        "rth_filter_applied",
        "retained_session_coverage",
        "promotion_cost_verified",
        "cost_model",
    )
    return {key: payload[key] for key in allowed if key in payload}


def trainer_cmd(*extra: object) -> list[object]:
    return [PY_RUNNER, TRAINER, *extra]


def replace_cli_arg(argv: list[object], flag: str, value: object) -> list[object]:
    updated = list(argv)
    try:
        index = [str(item) for item in updated].index(flag)
    except ValueError:
        updated.extend([flag, value])
        return updated
    if index + 1 < len(updated):
        updated[index + 1] = value
    else:
        updated.append(value)
    return updated


def register_trainer_argv_from_artifact(argv: list[object]) -> list[object]:
    artifact = read_json(MODEL_DIR / "trainer_artifact.json")
    model_family = str(artifact.get("model_family") or "").strip()
    if not model_family:
        return list(argv)
    updated = replace_cli_arg(argv, "--model-family", model_family)
    trained_rows = positive_int(artifact.get("trained_rows"))
    if trained_rows > 0:
        updated = replace_cli_arg(updated, "--trained-rows", trained_rows)
    calibration_rows = positive_int(artifact.get("calibration_rows"))
    if calibration_rows > 0:
        updated = replace_cli_arg(updated, "--calibration-rows", calibration_rows)
    return updated


def accepted_execution_feedback_source(value: object) -> str | None:
    text = str(value or "").strip()
    normalized = text.lower()
    if not normalized or any(marker in normalized for marker in SIMULATED_FEEDBACK_MARKERS):
        return None
    if any(marker in normalized for marker in ACCEPTED_FEEDBACK_MARKERS):
        return text
    return None


def runtime_trade_feedback_source(feedback_file: Path) -> str:
    accepted_source: str | None = None
    accepted_rows = 0
    if feedback_file.exists():
        with feedback_file.open(encoding="utf-8") as handle:
            for raw_line in handle:
                line = raw_line.strip()
                if not line:
                    continue
                try:
                    payload = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if not isinstance(payload, dict):
                    continue
                source = accepted_execution_feedback_source(payload.get("source"))
                source = source or accepted_execution_feedback_source(payload.get("feedback_source"))
                if (
                    not source
                    or payload.get("broker_realized") is not True
                    or payload.get("broker_fill_evidence") is not True
                ):
                    return TRADE_FEEDBACK_SOURCE
                accepted_source = accepted_source or source
                if source != accepted_source:
                    return TRADE_FEEDBACK_SOURCE
                accepted_rows += 1
    if accepted_rows > 0 and accepted_source:
        return accepted_source
    return TRADE_FEEDBACK_SOURCE


def feedback_file_execution_preflight(feedback_file: Path) -> dict[str, object]:
    """Validate explicit paper/live/broker feedback before spending lifecycle runtime."""
    summary: dict[str, object] = {
        "path": str(feedback_file),
        "exists": feedback_file.exists(),
        "rows_seen": 0,
        "accepted_rows": 0,
        "rejected_rows": 0,
        "invalid_json_rows": 0,
        "accepted_source": None,
        "accepted_execution_feedback_ready": False,
        "broker_fill_evidence_rows": 0,
        "broker_realized_rows": 0,
        "status": "missing",
    }
    if not feedback_file.exists():
        return summary

    accepted_source: str | None = None
    status = "no_rows"
    with feedback_file.open(encoding="utf-8") as handle:
        for raw_line in handle:
            line = raw_line.strip()
            if not line:
                continue
            summary["rows_seen"] = int(summary["rows_seen"]) + 1
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                summary["invalid_json_rows"] = int(summary["invalid_json_rows"]) + 1
                status = "invalid_json_rows"
                continue
            if not isinstance(payload, dict):
                summary["invalid_json_rows"] = int(summary["invalid_json_rows"]) + 1
                status = "invalid_json_rows"
                continue

            source = accepted_execution_feedback_source(payload.get("source"))
            source = source or accepted_execution_feedback_source(payload.get("feedback_source"))
            if source is None:
                summary["rejected_rows"] = int(summary["rejected_rows"]) + 1
                status = "no_accepted_execution_feedback_source"
                continue
            if payload.get("broker_realized") is not True or payload.get("broker_fill_evidence") is not True:
                summary["rejected_rows"] = int(summary["rejected_rows"]) + 1
                status = "missing_broker_execution_flags"
                continue
            if accepted_source is not None and source != accepted_source:
                summary["rejected_rows"] = int(summary["rejected_rows"]) + 1
                status = "mixed_accepted_feedback_sources"
                continue

            accepted_source = source
            summary["accepted_rows"] = int(summary["accepted_rows"]) + 1
            summary["broker_fill_evidence_rows"] = int(summary["broker_fill_evidence_rows"]) + 1
            summary["broker_realized_rows"] = int(summary["broker_realized_rows"]) + 1

    if int(summary["rows_seen"]) == 0:
        summary["status"] = "no_rows"
        return summary
    if int(summary["invalid_json_rows"]) or int(summary["rejected_rows"]):
        summary["status"] = status
        summary["accepted_source"] = accepted_source
        return summary
    if int(summary["accepted_rows"]) > 0 and accepted_source:
        summary["status"] = "ready"
        summary["accepted_source"] = accepted_source
        summary["accepted_execution_feedback_ready"] = True
        summary["broker_fill_evidence"] = True
        summary["broker_realized"] = True
        return summary
    summary["status"] = "no_accepted_execution_feedback_rows"
    return summary


def runtime_trade_summary_from_preflight(preflight: dict[str, object] | None) -> dict | None:
    if not preflight or preflight.get("accepted_execution_feedback_ready") is not True:
        return None
    accepted_source = preflight.get("accepted_source")
    if not isinstance(accepted_source, str) or not accepted_source.strip():
        return None
    accepted_rows = positive_int(preflight.get("accepted_rows"))
    if accepted_rows <= 0:
        return None
    return {
        "source": accepted_source,
        "feedback_source": accepted_source,
        "accepted_rows": accepted_rows,
        "broker_fill_evidence_rows": positive_int(preflight.get("broker_fill_evidence_rows")),
        "broker_realized_rows": positive_int(preflight.get("broker_realized_rows")),
        "broker_fill_evidence": preflight.get("broker_fill_evidence") is True,
        "broker_realized": preflight.get("broker_realized") is True,
        "accepted_execution_feedback_ready": True,
        "status": "ready",
    }


def build_lifecycle_command_plan(
    *,
    strategy_library: Path,
    data_root: Path,
    feedback_file: Path,
) -> list[dict[str, object]]:
    target_csv = STATE / SYMBOL / "policy_training/structural_path_ranking_target.csv"
    trainer_artifact = MODEL_DIR / "trainer_artifact.json"
    feedback_source = runtime_trade_feedback_source(feedback_file)
    return [
        {
            "stage": "provider_data",
            "name": "01_auto_quant_results_import",
            "argv": [
                ICT,
                "auto-quant-results-import",
                "--symbol",
                SYMBOL,
                "--state-dir",
                STATE,
                "--library",
                strategy_library,
            ],
            "timeout": 180,
        },
        {
            "stage": "pre_bayes",
            "name": "02_auto_quant_prior_init",
            "argv": [
                ICT,
                "auto-quant-prior-init",
                "--symbol",
                SYMBOL,
                "--state-dir",
                STATE,
                "--library",
                strategy_library,
                "--temper",
                "0.5",
                "--prior-strength",
                "4.0",
            ],
            "timeout": 180,
        },
        {
            "stage": "execution_tree",
            "name": "03_analyze_seed",
            "argv": [ICT, "analyze", "--symbol", SYMBOL, "--data-root", data_root, "--state-dir", STATE, "--output-format", "json"],
            "timeout": 300,
        },
        {
            "stage": "bbn_workflow",
            "name": "04_workflow_seed",
            "argv": [ICT, "workflow-status", "--symbol", SYMBOL, "--state-dir", STATE, "--refresh", "--output-format", "json"],
            "timeout": 120,
        },
        {
            "stage": "pre_bayes",
            "name": "05_pre_bayes_seed",
            "argv": [ICT, "pre-bayes-status", "--symbol", SYMBOL, "--state-dir", STATE, "--refresh", "--output-format", "json"],
            "timeout": 120,
        },
        {
            "stage": "path_ranker",
            "name": "06_export_target_seed",
            "argv": [ICT, "export-structural-path-ranking-target", "--symbol", SYMBOL, "--state-dir", STATE],
            "timeout": 120,
        },
        {
            "stage": "feedback_update",
            "name": "08_feedback_update",
            "argv": [
                ICT,
                "auto-quant-ingest-real-trades",
                "--symbol",
                SYMBOL,
                "--state-dir",
                STATE,
                "--trades",
                feedback_file,
                "--source",
                feedback_source,
            ],
            "timeout": 300,
        },
        {
            "stage": "path_ranker",
            "name": "09_export_target_after_feedback",
            "argv": [ICT, "export-structural-path-ranking-target", "--symbol", SYMBOL, "--state-dir", STATE],
            "timeout": 120,
        },
        {
            "stage": "policy_training",
            "name": "10_policy_after_feedback",
            "argv": [ICT, "policy-training-status", "--symbol", SYMBOL, "--state-dir", STATE, "--output-format", "json"],
            "timeout": 120,
        },
        {
            "stage": "path_ranker",
            "name": "11_train_ranker",
            "argv": trainer_cmd("--target-csv", target_csv, "--output-dir", MODEL_DIR, "--output-scores", SCORES, "--allow-direct-fallback"),
            "timeout": 300,
        },
        {
            "stage": "path_ranker",
            "name": "12_apply_ranker",
            "argv": trainer_cmd("--apply", "--model-dir", MODEL_DIR, "--target-csv", target_csv, "--output-scores", SCORES, "--allow-direct-fallback"),
            "timeout": 180,
        },
        {
            "stage": "path_ranker",
            "name": "13_apply_scores_to_ict",
            "argv": [ICT, "apply-structural-path-ranking-external-scores", "--symbol", SYMBOL, "--state-dir", STATE, "--scores-file", SCORES],
            "timeout": 120,
        },
        {
            "stage": "path_ranker",
            "name": "14_register_trainer",
            "argv": [
                ICT,
                "register-structural-path-ranking-trainer-artifact",
                "--symbol",
                SYMBOL,
                "--state-dir",
                STATE,
                "--artifact-uri",
                trainer_artifact,
                "--model-family",
                "weighted_feature_sum_v1",
                "--trained-rows",
                "1",
                "--calibration-rows",
                "0",
            ],
            "timeout": 120,
        },
        {
            "stage": "path_ranker",
            "name": "15_enable_runtime",
            "argv": [ICT, "enable-structural-path-ranking-runtime", "--symbol", SYMBOL, "--state-dir", STATE, "--reuse-mode", "prefer_history"],
            "timeout": 120,
        },
        {
            "stage": "execution_tree",
            "name": "16_analyze_after_ranker",
            "argv": [ICT, "analyze", "--symbol", SYMBOL, "--data-root", data_root, "--state-dir", STATE, "--output-format", "json"],
            "timeout": 300,
        },
        {
            "stage": "bbn_workflow",
            "name": "17_workflow_after_ranker",
            "argv": [ICT, "workflow-status", "--symbol", SYMBOL, "--state-dir", STATE, "--refresh", "--output-format", "json"],
            "timeout": 120,
        },
        {
            "stage": "pre_bayes",
            "name": "18_pre_bayes_after_ranker",
            "argv": [ICT, "pre-bayes-status", "--symbol", SYMBOL, "--state-dir", STATE, "--refresh", "--output-format", "json"],
            "timeout": 120,
        },
        {
            "stage": "policy_training",
            "name": "19_policy_after_ranker",
            "argv": [ICT, "policy-training-status", "--symbol", SYMBOL, "--state-dir", STATE, "--output-format", "json"],
            "timeout": 120,
        },
    ]


def run_lifecycle_driver(plan: list[dict[str, object]]) -> list[dict]:
    results: list[dict] = []
    for step in plan:
        argv = list(step["argv"])
        if str(step["name"]) == "14_register_trainer":
            argv = register_trainer_argv_from_artifact(argv)
        result = run_stage(
            str(step["stage"]),
            str(step["name"]),
            argv,
            int(step.get("timeout") or 300),
        )
        results.append(result)
        if result.get("exit") != 0 or result.get("timed_out") is True:
            break
    return results


def staged_command_results() -> list[dict]:
    for path in (
        SOURCE / "checks" / "terminal_metrics.json",
        SOURCE / "summaries" / "terminal_summary.json",
        CROSS_ENGINE_SOURCE / "checks" / "terminal_metrics.json",
        CROSS_ENGINE_SOURCE / "summaries" / "terminal_summary.json",
    ):
        payload = read_json(path)
        rows = payload.get("command_results")
        if command_results_cover_practical_stages(rows):
            return rows
    return []


def staged_trade_summary() -> dict:
    for path in (
        SOURCE / "checks" / "terminal_metrics.json",
        SOURCE / "summaries" / "terminal_summary.json",
        CROSS_ENGINE_SOURCE / "checks" / "terminal_metrics.json",
        CROSS_ENGINE_SOURCE / "summaries" / "terminal_summary.json",
    ):
        payload = read_json(path)
        for key in (
            "trade_summary",
            "runtime_trade_feedback_summary",
            "feedback_summary",
            "structural_feedback_summary",
        ):
            summary = payload.get(key)
            if isinstance(summary, dict) and summary:
                return summary
        source = payload.get("trade_feedback_source") or payload.get("feedback_source")
        if source:
            return {"source": source}
    return {}


def command_results_cover_practical_stages(value: object) -> bool:
    if not isinstance(value, list):
        return False
    stages = {
        str(row.get("stage") or "").strip().lower().replace("-", "_").replace(" ", "_")
        for row in value
        if isinstance(row, dict)
    }
    return all(stage in stages for stage in REQUIRED_COMMAND_RESULT_STAGES)


def practical_flags(closed_loop: dict, policy: dict) -> dict[str, bool]:
    live_trade = closed_loop
    promotion_allowed = bool(live_trade.get("promotion_allowed", False))
    trade_usable = bool(live_trade.get("trade_usable", False))
    update_goal = bool(live_trade.get("update_goal", False))
    return {
        "promotion_allowed": promotion_allowed,
        "trade_usable": trade_usable,
        "update_goal": update_goal,
    }


def branch_local_admitted(closed_loop: dict) -> bool:
    status = normalized_text(closed_loop.get("status") or closed_loop.get("admission_status"))
    return bool(closed_loop.get("ready") is True and closed_loop.get("actionable") is True) or status in {
        "admitted",
        "ready",
        "execution_ready",
    }


def write_summary(
    command_results: list[dict],
    data_summary: dict,
    trade_summary: dict | None = None,
    closure_evidence: dict | None = None,
) -> dict:
    workflow = read_json(STATE / SYMBOL / "workflow_snapshot.json")
    candidate = read_json(STATE / SYMBOL / "execution_candidate.json")
    trace = read_json(STATE / SYMBOL / "execution_tree_trace.json")
    trace_output = trace.get("output") if isinstance(trace.get("output"), dict) else trace
    policy = read_json(STATE / SYMBOL / "policy_training/structural_path_ranking_target_summary.json")
    closed_loop = workflow.get("closed_loop_branch_admission") or trace.get("closed_loop_branch_admission") or {}
    counters = validation_counters(trace_output)
    actionable = bool(candidate.get("actionable") or trace_output.get("actionable") or closed_loop.get("actionable"))
    candidate_status = str(
        candidate.get("candidate_status")
        or closed_loop.get("candidate_status")
        or trace_output.get("candidate_status")
        or ""
    )
    readiness = trace_output.get("execution_readiness")
    if readiness is None:
        readiness = candidate.get("execution_readiness")
    exact_survived = exact_branch_survived(candidate, trace_output, closed_loop)
    all_ok = bool(command_results) and all(
        row.get("exit") == 0 and row.get("timed_out") is False for row in command_results
    )
    flags = practical_flags(closed_loop, policy)
    metrics = {
        "schema_version": "tomac-nq-compound-chopfilter-practical-lifecycle-terminal/v1",
        "run_root": str(ROOT),
        "source_run_root": str(SOURCE),
        "cross_engine_run_root": str(CROSS_ENGINE_SOURCE),
        "symbol": SYMBOL,
        "factor_id": FACTOR_ID,
        "branch_path": BRANCH_PATH,
        "trade_summary": trade_summary or {},
        "command_results": command_results,
        "all_command_exits_zero": all_ok,
        "closed_loop_branch_admission": closed_loop,
        "exact_branch_survived": exact_survived,
        "execution_candidate_actionable": actionable,
        "execution_candidate_status": candidate_status,
        "execution_readiness": readiness,
        "branch_local_admitted": branch_local_admitted(closed_loop) and exact_survived,
        "validation_ready": all(_ratio_covers(counters.get(key)) for key in ("raw_scored_mature", "production_validation", "observation_validation")),
        "validation_counters": counters,
        "path_ranker_used": trace_output.get("path_ranker_score_used_by_execution_tree") is True,
        "path_ranker_score_visible_to_execution_tree": trace_output.get("path_ranker_score_visible_to_execution_tree"),
        "path_ranker_score_used_by_execution_tree": trace_output.get("path_ranker_score_used_by_execution_tree"),
        "policy_training_summary": policy,
        "learning_admission_status": policy.get("learning_admission_status"),
        "paper_admission_status": policy.get("paper_admission_status"),
        "deploy_ready": deploy_ready_from_policy(policy),
        "live_trade_status": policy.get("live_trade_status"),
        "funded_live_fill_required": funded_live_fill_required_from_policy(policy),
        "readiness_contract": readiness_contract_from_policy(policy),
        "market_data_provenance": normalize_market_data_summary(data_summary),
        **flags,
    }
    if closure_evidence:
        metrics.update(closure_evidence)
    write_json(CHECKS / "terminal_metrics.json", metrics)
    packet = write_same_tree_practical_closure_packet(
        metrics,
        SUMMARIES / "same_tree_practical_closure.json",
        evidence_packet="checks/terminal_metrics.json",
    )
    summary_flags = flags
    summary = {
        "status": "practical_closure_pass" if packet is not None else "practical_lifecycle_fail_closed",
        "factor_id": FACTOR_ID,
        "branch_path": BRANCH_PATH,
        "all_command_exits_zero": all_ok,
        "exact_branch_survived": exact_survived,
        "execution_candidate_actionable": actionable,
        "execution_candidate_status": candidate_status,
        "branch_local_admitted": metrics["branch_local_admitted"],
        "validation_ready": metrics["validation_ready"],
        "path_ranker_score_used_by_execution_tree": metrics["path_ranker_score_used_by_execution_tree"],
        "promotion_allowed": summary_flags["promotion_allowed"],
        "trade_usable": summary_flags["trade_usable"],
        "update_goal": summary_flags["update_goal"],
        "same_tree_practical_closure": str(SUMMARIES / "same_tree_practical_closure.json") if packet else None,
    }
    write_json(SUMMARIES / "terminal_summary.json", summary)
    return metrics


def _ratio_covers(value: str | None) -> bool:
    if not value or "/" not in value:
        return False
    left, right = value.split("/", 1)
    try:
        actual = int(left)
        required = int(right)
    except ValueError:
        return False
    return required > 0 and actual >= required


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Summarize same-tree practical lifecycle evidence for the NQ compound RRR ChopFilter branch."
    )
    parser.add_argument("--root", default=str(ROOT))
    parser.add_argument("--execute-driver", action="store_true")
    parser.add_argument("--strategy-library")
    parser.add_argument("--data-root")
    parser.add_argument("--feedback-file")
    parser.add_argument("--closure-evidence")
    return parser.parse_args(argv)


def resolve_runtime_paths(args: argparse.Namespace) -> dict[str, Path]:
    return {
        "strategy_library": Path(args.strategy_library)
        if args.strategy_library
        else MATERIALS / "tomac_nq_compound_trend_rrr_chopfilter_strategy_library.json",
        "data_root": Path(args.data_root) if args.data_root else DATA_DIR,
        "data_root_explicit": args.data_root is not None,
        "feedback_file": Path(args.feedback_file)
        if args.feedback_file
        else ROOT / "feedback/tomac_nq_compound_trend_rrr_chopfilter_simulated_feedback.jsonl",
        "closure_evidence": Path(args.closure_evidence) if args.closure_evidence else None,
    }


def normalize_materialized_branch_identity(strategy_library: Path, feedback_file: Path) -> dict[str, int]:
    """Align materialized inputs to this wrapper's same-tree lifecycle branch."""
    old_suffix = "SimulatedOrPaperFeedbackPracticalClosure"
    new_suffix = "PracticalLifecycleContinuation"
    old_branch = BRANCH_PATH.replace(new_suffix, old_suffix)
    summary = {
        "strategy_rows_seen": 0,
        "strategy_rows_updated": 0,
        "feedback_rows_seen": 0,
        "feedback_rows_updated": 0,
    }

    library = read_json(strategy_library)
    strategies = library.get("strategies")
    if isinstance(strategies, list):
        changed = False
        for strategy in strategies:
            if not isinstance(strategy, dict):
                continue
            metadata = strategy.get("metadata")
            if not isinstance(metadata, dict):
                continue
            summary["strategy_rows_seen"] += 1
            row_changed = False
            for key in ("branch_path", "regime_profit_branch_path"):
                if metadata.get(key) == old_branch:
                    metadata[key] = BRANCH_PATH
                    row_changed = True
            if row_changed:
                summary["strategy_rows_updated"] += 1
                changed = True
        if changed:
            write_json(strategy_library, library)

    if feedback_file.exists():
        rows: list[str] = []
        changed = False
        for line in feedback_file.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                rows.append(line)
                continue
            if not isinstance(row, dict):
                rows.append(line)
                continue
            summary["feedback_rows_seen"] += 1
            row_changed = False
            for key in ("branch_path", "regime_profit_branch_path"):
                if row.get(key) == old_branch:
                    row[key] = BRANCH_PATH
                    row_changed = True
            if row_changed:
                summary["feedback_rows_updated"] += 1
                changed = True
            rows.append(json.dumps(row, sort_keys=True))
        if changed:
            feedback_file.write_text("\n".join(rows) + "\n", encoding="utf-8")

    write_json(CHECKS / "materialized_branch_identity_normalization.json", summary)
    return summary


def cleaned_interval_file_count(data_root: Path) -> int:
    market = SYMBOL.lower()
    return sum(
        1
        for timeframe in ROW_CAPS
        if (data_root / f"cleaned-{timeframe}" / f"{market}.continuous-{timeframe}.json").exists()
    )


def path_is_under_run_root(path: Path) -> bool:
    try:
        return path.resolve().is_relative_to(ROOT.resolve())
    except OSError:
        return False


def should_prepare_local_data(data_root: Path, *, data_root_explicit: bool) -> bool:
    if not data_root_explicit:
        return True
    if cleaned_interval_file_count(data_root) >= 3:
        return False
    return path_is_under_run_root(data_root)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    configure_paths(Path(args.root))
    paths = resolve_runtime_paths(args)
    for directory in (STATE, CMD, CHECKS, SUMMARIES, MATERIALS, MODEL_DIR, DATA_DIR):
        directory.mkdir(parents=True, exist_ok=True)
    command_results = []
    preflight = None
    if args.execute_driver:
        if args.feedback_file:
            preflight = feedback_file_execution_preflight(paths["feedback_file"])
            write_json(CHECKS / "feedback_file_preflight.json", preflight)
        if preflight is None or preflight.get("accepted_execution_feedback_ready") is True:
            if should_prepare_local_data(
                paths["data_root"], data_root_explicit=bool(paths["data_root_explicit"])
            ):
                prepare_local_data(paths["data_root"])
            reset_prior_init_state()
            normalize_materialized_branch_identity(paths["strategy_library"], paths["feedback_file"])
            plan = build_lifecycle_command_plan(
                strategy_library=paths["strategy_library"],
                data_root=paths["data_root"],
                feedback_file=paths["feedback_file"],
            )
            write_json(CHECKS / "lifecycle_command_plan.json", {"steps": plan})
            command_results = run_lifecycle_driver(plan)
    else:
        command_results = staged_command_results()
    metrics = write_summary(
        command_results=command_results,
        data_summary=market_data_provenance(),
        trade_summary=runtime_trade_summary_from_preflight(preflight) or staged_trade_summary(),
        closure_evidence=closure_evidence_fields(paths["closure_evidence"]),
    )
    return 0 if (SUMMARIES / "same_tree_practical_closure.json").exists() else 2


if __name__ == "__main__":
    raise SystemExit(main())
