#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import os
import shutil
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

from same_tree_practical_closure import write_same_tree_practical_closure_packet  # noqa: E402

SOURCE_ENV = os.environ.get("SOURCE_RUN_ROOT", "").strip()
if SOURCE_ENV:
    SOURCE = Path(SOURCE_ENV)
else:
    SOURCE = Path("/tmp/ict-engine-tomac-opening-drive-exact-owner-recovery-20260527T165131+0800")

STAMP = datetime.now(ZoneInfo("Asia/Shanghai")).strftime("%Y%m%dT%H%M%S+0800")
ROOT_ENV = os.environ.get("ICT_ENGINE_TOMAC_BIDIR_EXACT_DOWNSTREAM_ROOT", "").strip()
if ROOT_ENV:
    ROOT = Path(ROOT_ENV)
else:
    ROOT = SOURCE / f"downstream-exact-tomac-nq-bidir-opening-drive-{STAMP}"

SYMBOL = "TOMAC_NQ_BIDIR_OPENING_DRIVE_EXACT_DOWNSTREAM_V1"
FACTOR_ID = "tomac_nq_bidir_opening_drive_t10_w0_e900_x1245_exact_v1"
BRANCH_PATH = (
    "TrendExpansion -> OpeningDrive -> BidirectionalIntradayTrendContinuation -> "
    "tomac_nq_bidir_opening_drive_t10_w0_e900_x1245_exact_v1"
)
ROW_CAPS = {
    "1m": 2000,
    "5m": 1000,
    "15m": 500,
    "30m": 300,
    "1h": 200,
    "4h": 120,
    "1d": 90,
}
LIVE_EXECUTION_READINESS_FLOOR = 0.45

STATE = ROOT / "state"
CMD = ROOT / "command-output"
CHECKS = ROOT / "checks"
SUMMARIES = ROOT / "summaries"
MATERIALS = ROOT / "materials"
MODEL_DIR = ROOT / "path_ranker_model"
DATA_DIR = ROOT / "data/provider/normalized"
SCORES = ROOT / "path_ranker_scores.csv"

SOURCE_LIBRARY = SOURCE / "materials/tomac_nq_bidir_opening_drive_strategy_library.json"
SOURCE_DATA_ROOT = SOURCE / "aq_workspace/user_data/data/futures"
SOURCE_FULL_CSV_ROOT_ENV = os.environ.get("SOURCE_FULL_CSV_ROOT", "").strip()
SOURCE_FULL_CSV_ROOT = Path(SOURCE_FULL_CSV_ROOT_ENV) if SOURCE_FULL_CSV_ROOT_ENV else None

ICT = REPO / ".local-artifacts/cargo-target/debug/ict-engine"
if not ICT.exists():
    ICT = REPO / "target/debug/ict-engine"

TRAINER = REPO / "support/scripts/auto_quant_external/pandas_path_ranker_trainer.py"
PY_RUNNER = Path("python3")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the TOMAC NQ bidirectional opening-drive exact downstream owner."
    )
    return parser.parse_args(argv)


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


def read_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def write_strategy_library() -> Path:
    MATERIALS.mkdir(parents=True, exist_ok=True)
    payload = read_json(SOURCE_LIBRARY)
    strategies = payload.get("strategies") or []
    strategy = None
    for candidate in strategies:
        if candidate.get("name") == FACTOR_ID:
            strategy = dict(candidate)
            break
    if strategy is None:
        raise SystemExit(f"missing exact strategy '{FACTOR_ID}' in {SOURCE_LIBRARY}")
    strategy["metadata"] = dict(strategy.get("metadata") or {})
    strategy["metadata"]["bounded_rows"] = dict(ROW_CAPS)
    strategy["metadata"]["branch_path"] = BRANCH_PATH
    strategy["metadata"]["regime_profit_branch_path"] = BRANCH_PATH
    strategy["metadata"]["promotion_allowed"] = False
    strategy["metadata"]["trade_usable"] = False
    strategy["metadata"]["source_packet"] = str(SOURCE)
    strategy["status"] = strategy.get("status") or "ok"
    out = {
        "manifest_version": payload.get("manifest_version") or "1.0",
        "exported_at": datetime.now(ZoneInfo("Asia/Shanghai")).isoformat(),
        "auto_quant_repo_url": "tomac_nq_bidir_opening_drive_exact_downstream_v1",
        "timeframe": payload.get("timeframe") or "1m",
        "strategies": [strategy],
    }
    path = MATERIALS / "tomac_nq_bidir_opening_drive_exact_strategy_library.json"
    path.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    return path


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


def trimmed_csv_to_cleaned_json(source_csv: Path, target_json: Path, symbol: str) -> int:
    with source_csv.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        candles = []
        for row in reader:
            candles.append(
                {
                    "timestamp": row["timestamp"],
                    "open": float(row["open"]),
                    "high": float(row["high"]),
                    "low": float(row["low"]),
                    "close": float(row["close"]),
                    "volume": float(row["volume"]),
                }
            )
    # `ict-engine analyze --data-root` auto-discovers sibling frames only from the
    # cleaned-interval layout `<root>/cleaned-<tf>/<market>.continuous-<tf>.json`.
    target_json.parent.mkdir(parents=True, exist_ok=True)
    target_json.write_text(
        json.dumps({"symbol": symbol, "candles": candles}, indent=2) + "\n",
        encoding="utf-8",
    )
    return len(candles)


def feather_to_csv(source_feather: Path, target_csv: Path, py_runner: Path) -> int:
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
        [str(py_runner), "-c", script, str(source_feather), str(target_csv)],
        text=True,
        capture_output=True,
        timeout=900,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr or proc.stdout or f"feather_to_csv failed for {source_feather}")
    summary = json.loads(proc.stdout)
    return int(summary.get("rows") or 0)


def source_feather_path(timeframe: str) -> Path:
    return SOURCE_DATA_ROOT / f"NQ_USD-{timeframe}-futures.feather"


def source_full_csv_path(timeframe: str) -> Path | None:
    candidates: list[Path] = []
    if SOURCE_FULL_CSV_ROOT is not None:
        candidates.append(SOURCE_FULL_CSV_ROOT / f"nq_usd_{timeframe}_full.csv")
    candidates.extend(SOURCE.glob(f"downstream-exact-tomac-nq-bidir-opening-drive-*/data/provider/full/nq_usd_{timeframe}_full.csv"))
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def prepare_local_data() -> dict:
    full_dir = ROOT / "data/provider/full"
    full_dir.mkdir(parents=True, exist_ok=True)
    summaries: dict[str, dict[str, object]] = {}
    market = SYMBOL.lower()
    for timeframe, keep_rows in ROW_CAPS.items():
        reusable_full_csv = source_full_csv_path(timeframe)
        full_csv = full_dir / f"nq_usd_{timeframe}_full.csv"
        trimmed_csv = DATA_DIR / f"nq_usd_{timeframe}_ultra.csv"
        cleaned_json = DATA_DIR / f"cleaned-{timeframe}" / f"{market}.continuous-{timeframe}.json"
        source_label: str
        if reusable_full_csv is not None:
            source_label = str(reusable_full_csv)
            full_rows: int | str = "reused_existing_csv"
            kept_rows = trim_csv_rows(reusable_full_csv, trimmed_csv, keep_rows)
        else:
            feather = source_feather_path(timeframe)
            if not feather.exists():
                raise RuntimeError(f"missing exact-owner timeframe feather: {feather}")
            source_label = str(feather)
            full_rows = feather_to_csv(feather, full_csv, PY_RUNNER)
            kept_rows = trim_csv_rows(full_csv, trimmed_csv, keep_rows)
        cleaned_rows = trimmed_csv_to_cleaned_json(trimmed_csv, cleaned_json, SYMBOL)
        summaries[timeframe] = {
            "source": source_label,
            "full_csv": str(reusable_full_csv or full_csv),
            "trimmed_csv": str(trimmed_csv),
            "cleaned_json": str(cleaned_json),
            "full_rows": full_rows,
            "kept_rows": kept_rows,
            "cleaned_rows": cleaned_rows,
        }
    CHECKS.mkdir(parents=True, exist_ok=True)
    (CHECKS / "source_data_summary.json").write_text(
        json.dumps(
            {
                "source_run_root": str(SOURCE),
                "source_library": str(SOURCE_LIBRARY),
                "source_data_root": str(SOURCE_DATA_ROOT),
                "source_full_csv_root": str(SOURCE_FULL_CSV_ROOT) if SOURCE_FULL_CSV_ROOT else None,
                "row_caps": ROW_CAPS,
                "timeframes": summaries,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return summaries


def validation_counters(trace_output: dict) -> dict[str, str]:
    counters: dict[str, str] = {}
    for line in trace_output.get("split_reason_lineage") or []:
        for key in ("raw_scored_mature", "production_validation", "observation_validation"):
            marker = f"{key}="
            if marker not in line:
                continue
            value = line.split(marker, 1)[1].split()[0].strip()
            counters[key] = value
    return counters


def trainer_cmd(*extra: object) -> list[object]:
    return [PY_RUNNER, TRAINER, *extra]


def numeric_ratio(counter: str | None) -> tuple[int, int]:
    if not counter or "/" not in counter:
        return (0, 0)
    left, right = counter.split("/", 1)
    try:
        return (int(left), int(right))
    except ValueError:
        return (0, 0)


def exact_branch_survived(candidate: dict, trace_output: dict, closed_loop: dict) -> bool:
    values = [
        candidate.get("path_id"),
        candidate.get("path_label"),
        candidate.get("branch_path"),
        trace_output.get("path_id"),
        trace_output.get("path_label"),
        closed_loop.get("path_id"),
        closed_loop.get("path_label"),
    ]
    return BRANCH_PATH in values


def practical_admission_flags(
    actionable: bool,
    branch_survived: bool,
    candidate_status: str,
    counters: dict[str, str],
    readiness: float | None,
    hazard: float | None,
    path_ranker_used: bool | None,
    all_ok: bool,
) -> dict[str, object]:
    raw_ready = numeric_ratio(counters.get("raw_scored_mature"))
    prod_ready = numeric_ratio(counters.get("production_validation"))
    obs_ready = numeric_ratio(counters.get("observation_validation"))
    validation_ready = (
        raw_ready[1] > 0
        and prod_ready[1] > 0
        and obs_ready[1] > 0
        and raw_ready[0] >= raw_ready[1]
        and prod_ready[0] >= prod_ready[1]
        and obs_ready[0] >= obs_ready[1]
    )
    admitted = (
        all_ok
        and branch_survived
        and actionable
        and candidate_status not in {"", "no_trade", "observe", "discard"}
        and validation_ready
        and readiness is not None
        and readiness >= LIVE_EXECUTION_READINESS_FLOOR
    )
    return {
        "branch_local_admitted": admitted,
        "validation_ready": validation_ready,
        "path_ranker_used": path_ranker_used is True,
        "promotion_allowed": False,
        "trade_usable": False,
        "update_goal": False,
    }


def write_summary(command_results: list[dict], data_summary: dict) -> None:
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
    hazard = trace_output.get("hybrid_transition_hazard")
    if hazard is None:
        hazard = candidate.get("hybrid_transition_hazard")
    branch_survived = exact_branch_survived(candidate, trace_output, closed_loop)
    all_ok = all(row["exit"] == 0 for row in command_results)
    flags = practical_admission_flags(
        actionable=actionable,
        branch_survived=branch_survived,
        candidate_status=candidate_status,
        counters=counters,
        readiness=readiness,
        hazard=hazard,
        path_ranker_used=trace_output.get("path_ranker_score_used_by_execution_tree"),
        all_ok=all_ok,
    )
    metrics = {
        "run_root": str(ROOT),
        "source_run_root": str(SOURCE),
        "branch_path": BRANCH_PATH,
        "factor_id": FACTOR_ID,
        "row_caps": ROW_CAPS,
        "data_summary": data_summary,
        "command_results": command_results,
        "all_command_exits_zero": all_ok,
        "closed_loop_branch_admission": closed_loop,
        "exact_branch_survived": branch_survived,
        "execution_candidate_actionable": actionable,
        "execution_candidate_status": candidate_status,
        "execution_readiness": readiness,
        "transition_hazard": hazard,
        "path_ranker_score_visible_to_execution_tree": trace_output.get("path_ranker_score_visible_to_execution_tree"),
        "path_ranker_score_used_by_execution_tree": trace_output.get("path_ranker_score_used_by_execution_tree"),
        "validation_counters": counters,
        "policy_training_summary": policy,
        "learning_admission_status": policy.get("learning_admission_status"),
        "paper_admission_status": policy.get("paper_admission_status"),
        "live_trade_status": policy.get("live_trade_status"),
        "market_data_provenance": data_summary.get("market_data_provenance"),
        **flags,
    }
    CHECKS.mkdir(parents=True, exist_ok=True)
    (CHECKS / "terminal_metrics.json").write_text(json.dumps(metrics, indent=2) + "\n", encoding="utf-8")
    SUMMARIES.mkdir(parents=True, exist_ok=True)
    write_same_tree_practical_closure_packet(
        metrics,
        SUMMARIES / "same_tree_practical_closure.json",
        evidence_packet="checks/terminal_metrics.json",
    )
    summary_lines = [
        "# TOMAC NQ Bidirectional Opening-Drive Exact Downstream Summary",
        "",
        f"- run_root: `{ROOT}`",
        f"- source_run_root: `{SOURCE}`",
        f"- branch_path: `{BRANCH_PATH}`",
        f"- all_command_exits_zero: `{all_ok}`",
        f"- exact_branch_survived: `{branch_survived}`",
        f"- execution_candidate: actionable=`{actionable}` status=`{candidate_status}`",
        f"- execution_readiness: `{readiness}`",
        f"- transition_hazard: `{hazard}`",
        f"- validation: raw=`{counters.get('raw_scored_mature', 'missing')}` "
        f"production=`{counters.get('production_validation', 'missing')}` "
        f"observation=`{counters.get('observation_validation', 'missing')}`",
        "",
        f"`promotion_allowed={str(flags['promotion_allowed']).lower()}`; "
        f"`trade_usable={str(flags['trade_usable']).lower()}`; "
        f"`update_goal={str(flags['update_goal']).lower()}`.",
        "",
    ]
    (SUMMARIES / "terminal_decision_summary.md").write_text("\n".join(summary_lines), encoding="utf-8")


def main() -> int:
    for directory in (CMD, CHECKS, SUMMARIES, MATERIALS, MODEL_DIR, DATA_DIR, ROOT / "scripts"):
        directory.mkdir(parents=True, exist_ok=True)
    if STATE.exists():
        shutil.rmtree(STATE)
    STATE.mkdir(parents=True, exist_ok=True)
    shutil.copy2(SCRIPT, ROOT / "scripts" / SCRIPT.name)
    library = write_strategy_library()
    data_summary = prepare_local_data()
    target_csv = STATE / SYMBOL / "policy_training/structural_path_ranking_target.csv"
    trainer_artifact = MODEL_DIR / "trainer_artifact.json"
    commands = [
        run_cmd("01_auto_quant_results_import", [ICT, "auto-quant-results-import", "--symbol", SYMBOL, "--state-dir", STATE, "--library", library], 180),
        run_cmd(
            "02_auto_quant_prior_init",
            [ICT, "auto-quant-prior-init", "--symbol", SYMBOL, "--state-dir", STATE, "--library", library, "--temper", "0.5", "--prior-strength", "4.0"],
            180,
        ),
        run_cmd(
            "03_analyze_seed",
            [ICT, "analyze", "--symbol", SYMBOL, "--data-root", DATA_DIR, "--state-dir", STATE, "--output-format", "json"],
            300,
        ),
        run_cmd("04_workflow_seed", [ICT, "workflow-status", "--symbol", SYMBOL, "--state-dir", STATE, "--refresh", "--output-format", "json"], 120),
        run_cmd("05_pre_bayes_seed", [ICT, "pre-bayes-status", "--symbol", SYMBOL, "--state-dir", STATE, "--refresh", "--output-format", "json"], 120),
        run_cmd("06_export_target_seed", [ICT, "export-structural-path-ranking-target", "--symbol", SYMBOL, "--state-dir", STATE], 120),
    ]
    if all(row["exit"] == 0 for row in commands):
        commands.extend(
            [
                run_cmd("07_train_ranker", trainer_cmd("--target-csv", target_csv, "--output-dir", MODEL_DIR, "--output-scores", SCORES, "--allow-direct-fallback"), 300),
                run_cmd("08_apply_ranker", trainer_cmd("--apply", "--model-dir", MODEL_DIR, "--target-csv", target_csv, "--output-scores", SCORES, "--allow-direct-fallback"), 180),
                run_cmd("09_apply_scores_to_ict", [ICT, "apply-structural-path-ranking-external-scores", "--symbol", SYMBOL, "--state-dir", STATE, "--scores-file", SCORES], 120),
                run_cmd("10_register_trainer", [ICT, "register-structural-path-ranking-trainer-artifact", "--symbol", SYMBOL, "--state-dir", STATE, "--artifact-uri", trainer_artifact, "--model-family", "weighted_feature_sum_v1", "--trained-rows", "1", "--calibration-rows", "0"], 120),
                run_cmd("11_enable_runtime", [ICT, "enable-structural-path-ranking-runtime", "--symbol", SYMBOL, "--state-dir", STATE, "--reuse-mode", "prefer_history"], 120),
                run_cmd("12_analyze_after_ranker", [ICT, "analyze", "--symbol", SYMBOL, "--data-root", DATA_DIR, "--state-dir", STATE, "--output-format", "json"], 300),
                run_cmd("13_workflow_after_ranker", [ICT, "workflow-status", "--symbol", SYMBOL, "--state-dir", STATE, "--refresh", "--output-format", "json"], 120),
                run_cmd("14_pre_bayes_after_ranker", [ICT, "pre-bayes-status", "--symbol", SYMBOL, "--state-dir", STATE, "--refresh", "--output-format", "json"], 120),
                run_cmd("15_policy_after_ranker", [ICT, "policy-training-status", "--symbol", SYMBOL, "--state-dir", STATE, "--output-format", "json"], 120),
            ]
        )
    write_summary(commands, data_summary)
    return 0


def run_cli(argv: list[str] | None = None) -> int:
    try:
        parse_args(argv)
    except SystemExit as exc:
        return int(exc.code or 0)
    return main()


if __name__ == "__main__":
    raise SystemExit(run_cli())
