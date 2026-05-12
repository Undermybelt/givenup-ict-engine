#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import os
import subprocess
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path


RUN_ROOT = Path(__file__).resolve().parents[1]
REPO = RUN_ROOT.parents[4]
SOURCE = REPO / "docs/experiments/actionable-regime-confidence/runs/20260512T172142+0800-codex-board-a-feasible-window-same-root-aq-packet-v1"
STATE = RUN_ROOT / "state"
DATA = RUN_ROOT / "data"
OUT = RUN_ROOT / "command-output"
CHECKS = RUN_ROOT / "checks"
REPORT = RUN_ROOT / "cross-axis-two-context-downstream-v1"
ENGINE = REPO / "target/debug/ict-engine"
TRAINER = REPO / "scripts/auto_quant_external/pandas_path_ranker_trainer.py"
UV = Path.home() / ".local/bin/uv"
LIBRARY = SOURCE / "provider_btc_172142_strategy_library_v1.json"
TRADES = SOURCE / "provider_btc_172142_real_trades_v1.jsonl"

CONTEXTS = [
    ("yfinance", SOURCE / "provider-csv/yfinance_btc_usd_1h.csv", "tail"),
    ("kraken", SOURCE / "provider-csv/kraken_xbtusd_1h.csv", "tail"),
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def parse_ts(value: str) -> datetime:
    text = value.strip().replace("Z", "+00:00")
    if " " in text and "T" not in text:
        text = text.replace(" ", "T")
    return datetime.fromisoformat(text).astimezone(timezone.utc)


def ts_out(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def load_rows(path: Path) -> list[dict]:
    rows: list[dict] = []
    with path.open(newline="") as handle:
        for row in csv.DictReader(handle):
            key = "timestamp" if row.get("timestamp") else "date" if row.get("date") else "ts"
            try:
                rows.append(
                    {
                        "timestamp": parse_ts(row[key]),
                        "open": float(row["open"]),
                        "high": float(row["high"]),
                        "low": float(row["low"]),
                        "close": float(row["close"]),
                        "volume": float(row.get("volume") or 0.0),
                    }
                )
            except Exception:
                continue
    rows.sort(key=lambda item: item["timestamp"])
    return rows


def resample(rows: list[dict], hours: int) -> list[dict]:
    buckets: dict[int, list[dict]] = defaultdict(list)
    for row in rows:
        epoch_hour = int(row["timestamp"].timestamp() // 3600)
        bucket = epoch_hour - (epoch_hour % hours)
        buckets[bucket].append(row)
    out = []
    for bucket in sorted(buckets):
        chunk = sorted(buckets[bucket], key=lambda item: item["timestamp"])
        out.append(
            {
                "timestamp": ts_out(datetime.fromtimestamp(bucket * 3600, tz=timezone.utc)),
                "open": chunk[0]["open"],
                "high": max(item["high"] for item in chunk),
                "low": min(item["low"] for item in chunk),
                "close": chunk[-1]["close"],
                "volume": sum(item["volume"] for item in chunk),
            }
        )
    return out


def write_candles(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = []
    for row in rows:
        item = dict(row)
        if isinstance(item["timestamp"], datetime):
            item["timestamp"] = ts_out(item["timestamp"])
        payload.append(item)
    path.write_text(json.dumps(payload, indent=2) + "\n")


def run_step(name: str, argv: list[str], timeout: int = 120, env: dict[str, str] | None = None) -> dict:
    OUT.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)
    (OUT / f"{name}.cmd").write_text(" ".join(argv) + "\n")
    try:
        proc = subprocess.run(
            argv,
            cwd=REPO,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            env={**os.environ, **(env or {})},
        )
        rc = proc.returncode
        stdout = proc.stdout
        stderr = proc.stderr
        timed_out = False
    except subprocess.TimeoutExpired as exc:
        rc = 124
        stdout = exc.stdout or ""
        stderr = (exc.stderr or "") + f"\nTIMEOUT after {timeout}s\n"
        timed_out = True
    (OUT / f"{name}.out").write_text(stdout)
    (OUT / f"{name}.err").write_text(stderr)
    (CHECKS / f"{name}.exit").write_text(str(rc) + "\n")
    return {"name": name, "exit": rc, "timed_out": timed_out, "argv": argv}


def load_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text())
    except Exception:
        return {}


def csv_rows(path: Path) -> int:
    if not path.exists() or path.stat().st_size == 0:
        return 0
    with path.open(newline="") as handle:
        return max(0, sum(1 for _ in csv.reader(handle)) - 1)


def main() -> int:
    REPORT.mkdir(parents=True, exist_ok=True)
    steps = []
    contexts = []
    targets = []
    for index, (provider, csv_path, window_name) in enumerate(CONTEXTS, start=1):
        rows = load_rows(csv_path)
        window = rows[-min(len(rows), 720) :]
        htf = DATA / provider / window_name / "htf_1d.json"
        mtf = DATA / provider / window_name / "mtf_4h.json"
        ltf = DATA / provider / window_name / "ltf_1h.json"
        write_candles(ltf, window)
        write_candles(mtf, resample(window, 4))
        write_candles(htf, resample(window, 24))
        symbol = f"BOARD_A_191612_{provider.upper()}_{window_name.upper()}"
        prefix = f"{index:02d}_{provider}_{window_name}"
        steps.append(run_step(f"{prefix}_auto_quant_results_import", [str(ENGINE), "auto-quant-results-import", "--symbol", symbol, "--state-dir", str(STATE), "--library", str(LIBRARY)]))
        steps.append(run_step(f"{prefix}_auto_quant_prior_init", [str(ENGINE), "auto-quant-prior-init", "--symbol", symbol, "--state-dir", str(STATE), "--library", str(LIBRARY)]))
        steps.append(run_step(f"{prefix}_auto_quant_ingest_real_trades", [str(ENGINE), "auto-quant-ingest-real-trades", "--symbol", symbol, "--state-dir", str(STATE), "--trades", str(TRADES), "--source", f"board_a_191612_{provider}_{window_name}"]))
        steps.append(run_step(f"{prefix}_analyze", [str(ENGINE), "analyze", "--symbol", symbol, "--data-htf", str(htf), "--data-mtf", str(mtf), "--data-ltf", str(ltf), "--state-dir", str(STATE), "--agent"], timeout=180))
        steps.append(run_step(f"{prefix}_pre_bayes_status", [str(ENGINE), "pre-bayes-status", "--symbol", symbol, "--state-dir", str(STATE), "--refresh", "--output-format", "json"]))
        steps.append(run_step(f"{prefix}_export_structural_path_target", [str(ENGINE), "export-structural-path-ranking-target", "--symbol", symbol, "--state-dir", str(STATE)]))
        steps.append(run_step(f"{prefix}_workflow_execution_candidate", [str(ENGINE), "workflow-status", "--symbol", symbol, "--state-dir", str(STATE), "--phase", "execution-candidate", "--agent"]))
        target = STATE / symbol / "policy_training/structural_path_ranking_target_history.csv"
        targets.append(target)
        pre = load_json(OUT / f"{prefix}_pre_bayes_status.out")
        candidate = load_json(STATE / symbol / "execution_candidate.json")
        summary = load_json(STATE / symbol / "policy_training/structural_path_ranking_target_summary.json")
        contexts.append(
            {
                "provider": provider,
                "symbol": symbol,
                "rows_1h": len(window),
                "rows_4h": len(load_json(mtf) if mtf.exists() else []),
                "rows_1d": len(load_json(htf) if htf.exists() else []),
                "start": ts_out(window[0]["timestamp"]) if window else None,
                "end": ts_out(window[-1]["timestamp"]) if window else None,
                "pre_bayes_confidence": pre.get("latest_confidence") or pre.get("confidence"),
                "pre_bayes_gate": pre.get("latest_gate_status") or pre.get("gate_status"),
                "candidate_actionable": candidate.get("actionable"),
                "candidate_status": candidate.get("candidate_status"),
                "execution_gate_status": candidate.get("execution_gate_status"),
                "target_history_rows": csv_rows(target),
                "history_mature_rows": summary.get("history_mature_rows"),
                "history_calibrated_rows": summary.get("history_rows_with_calibrated_path_prob"),
            }
        )
    aggregate_csv = REPORT / "aggregate_structural_path_ranking_target_history.csv"
    fieldnames = None
    all_rows = []
    for target in targets:
        if target.exists() and target.stat().st_size:
            with target.open(newline="") as handle:
                reader = csv.DictReader(handle)
                fieldnames = fieldnames or list(reader.fieldnames or [])
                all_rows.extend(list(reader))
    if fieldnames:
        with aggregate_csv.open("w", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(all_rows)
    env = {"OMP_NUM_THREADS": "1", "OPENBLAS_NUM_THREADS": "1", "VECLIB_MAXIMUM_THREADS": "1"}
    aggregate_rows = csv_rows(aggregate_csv)
    if aggregate_rows:
        model_dir = REPORT / "catboost_aggregate_v1"
        scores_csv = REPORT / "aggregate_scores.csv"
        steps.append(run_step("20_train_catboost_aggregate", [str(UV), "run", "--offline", "--with", "pandas", "--with", "numpy", "--with", "catboost", "python", str(TRAINER), "--target-csv", str(aggregate_csv), "--output-dir", str(model_dir), "--model-family", "catboost"], timeout=180, env=env))
        steps.append(run_step("21_apply_catboost_aggregate", [str(UV), "run", "--offline", "--with", "pandas", "--with", "numpy", "--with", "catboost", "python", str(TRAINER), "--apply", "--model-dir", str(model_dir), "--target-csv", str(aggregate_csv), "--output-scores", str(scores_csv)], timeout=180, env=env))
    accepted_95 = [item for item in contexts if (item.get("pre_bayes_confidence") or 0) >= 0.95]
    execution_ready = [item for item in contexts if item.get("candidate_actionable") is True or item.get("execution_gate_status") in {"execution_ready", "ready"}]
    report = {
        "generated_at": utc_now(),
        "source_packet": "172142_feasible_window_same_root_aq_packet",
        "contexts_total": len(contexts),
        "contexts": contexts,
        "steps_total": len(steps),
        "steps_exit_zero": sum(1 for step in steps if step["exit"] == 0),
        "steps_all_zero": all(step["exit"] == 0 for step in steps),
        "aggregate_target_rows": aggregate_rows,
        "accepted_95_contexts": len(accepted_95),
        "execution_ready_contexts": len(execution_ready),
        "promotion_allowed": False,
        "trade_usable": False,
        "update_goal": False,
        "steps": steps,
    }
    (REPORT / "cross_axis_two_context_downstream_v1.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    (REPORT / "cross_axis_two_context_downstream_v1.md").write_text(
        "# Cross-Axis Two-Context Downstream v1\n\n"
        f"Contexts: `{len(contexts)}`.\n\n"
        f"Command exits: `{report['steps_exit_zero']}/{report['steps_total']}`.\n\n"
        f"Aggregate target rows: `{aggregate_rows}`.\n\n"
        f"Accepted >=95 contexts: `{len(accepted_95)}`.\n\n"
        f"Execution-ready contexts: `{len(execution_ready)}`.\n\n"
        "Gate: fail-closed unless per-regime >=95, cross-axis validation, CatBoost readiness, and execution admission all pass.\n"
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["steps_all_zero"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
