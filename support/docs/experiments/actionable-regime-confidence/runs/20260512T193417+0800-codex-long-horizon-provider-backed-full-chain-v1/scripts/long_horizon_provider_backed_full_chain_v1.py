#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import os
import subprocess
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = Path(__file__).resolve().parents[1]
SOURCE_PROVIDER = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs/"
    / "20260512T175651+0800-codex-high-density-rsi-bb-ema-six-provider-aq-v1"
)
SOURCE_AQ = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs/"
    / "20260512T172142+0800-codex-board-a-feasible-window-same-root-aq-packet-v1"
)
STATE = RUN_ROOT / "state"
DATA = RUN_ROOT / "data"
OUT = RUN_ROOT / "command-output"
CHECKS = RUN_ROOT / "checks"
REPORT = RUN_ROOT / "long-horizon-provider-backed-full-chain-v1"
ENGINE = REPO / "target/debug/ict-engine"
TRAINER = REPO / "scripts/auto_quant_external/pandas_path_ranker_trainer.py"
UV = Path.home() / ".local/bin/uv"
LIBRARY = SOURCE_AQ / "provider_btc_172142_strategy_library_v1.json"
TRADES = SOURCE_AQ / "provider_btc_172142_real_trades_v1.jsonl"

COMMAND_TIMEOUT_SECONDS = 240

CONTEXTS = [
    {
        "symbol": "BOARD_A_YF_SPY_193417",
        "provider": "yfinance/YF",
        "market": "equity",
        "source_native_timeframe": "1h",
        "path": SOURCE_PROVIDER / "data/normalized/yahoo_spy_1h.normalized.csv",
    },
    {
        "symbol": "BOARD_A_IBKR_SPY_193417",
        "provider": "IBKR",
        "market": "equity",
        "source_native_timeframe": "1h",
        "path": SOURCE_PROVIDER / "data/normalized/ibkr_spy_1h_90d.normalized.csv",
    },
    {
        "symbol": "BOARD_A_BINANCE_BTC_193417",
        "provider": "Binance",
        "market": "crypto",
        "source_native_timeframe": "1h",
        "path": SOURCE_PROVIDER / "data/normalized/binance_btcusdt_1h.normalized.csv",
    },
    {
        "symbol": "BOARD_A_BYBIT_BTC_193417",
        "provider": "Bybit",
        "market": "crypto",
        "source_native_timeframe": "1h",
        "path": SOURCE_PROVIDER / "data/normalized/bybit_linear_btcusdt_1h.normalized.csv",
    },
    {
        "symbol": "BOARD_A_KRAKEN_BTC_193417",
        "provider": "Kraken",
        "market": "crypto",
        "source_native_timeframe": "1h",
        "path": SOURCE_PROVIDER / "data/normalized/kraken_futures_pfxbtusd_1h.normalized.csv",
    },
    {
        "symbol": "BOARD_A_TVR_BTC_193417",
        "provider": "TradingViewRemix/TVR",
        "market": "crypto",
        "source_native_timeframe": "1h",
        "path": SOURCE_PROVIDER / "data/normalized/tvr_btc_usd_1h.normalized.csv",
    },
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    return str(path.relative_to(REPO))


def parse_ts(value: str) -> datetime:
    text = value.strip().replace("Z", "+00:00")
    if " " in text and "T" not in text:
        text = text.replace(" ", "T")
    return datetime.fromisoformat(text).astimezone(timezone.utc)


def ts_out(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def load_csv(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(newline="", encoding="utf-8") as handle:
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


def resample(rows: list[dict[str, Any]], hours: int) -> list[dict[str, Any]]:
    buckets: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        epoch_hour = int(row["timestamp"].timestamp() // 3600)
        bucket = epoch_hour - (epoch_hour % hours)
        buckets[bucket].append(row)
    out: list[dict[str, Any]] = []
    for bucket in sorted(buckets):
        chunk = sorted(buckets[bucket], key=lambda item: item["timestamp"])
        out.append(
            {
                "timestamp": datetime.fromtimestamp(bucket * 3600, tz=timezone.utc),
                "open": chunk[0]["open"],
                "high": max(item["high"] for item in chunk),
                "low": min(item["low"] for item in chunk),
                "close": chunk[-1]["close"],
                "volume": sum(item["volume"] for item in chunk),
            }
        )
    return out


def write_candles(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = []
    for row in rows:
        item = dict(row)
        if isinstance(item["timestamp"], datetime):
            item["timestamp"] = ts_out(item["timestamp"])
        payload.append(item)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def gap_stats(rows: list[dict[str, Any]]) -> dict[str, Any]:
    if len(rows) < 2:
        return {"gap_count_gt_1h": 0, "max_gap_hours": 0.0}
    gaps = []
    for left, right in zip(rows, rows[1:]):
        hours = (right["timestamp"] - left["timestamp"]).total_seconds() / 3600.0
        gaps.append(hours)
    return {
        "gap_count_gt_1h": sum(1 for gap in gaps if gap > 1.5),
        "max_gap_hours": max(gaps) if gaps else 0.0,
        "median_gap_hours": sorted(gaps)[len(gaps) // 2] if gaps else 0.0,
    }


def run_step(name: str, argv: list[str], timeout: int = COMMAND_TIMEOUT_SECONDS, env: dict[str, str] | None = None) -> dict[str, Any]:
    OUT.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)
    (OUT / f"{name}.cmd").write_text(" ".join(argv) + "\n", encoding="utf-8")
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
    (OUT / f"{name}.out").write_text(stdout, encoding="utf-8")
    (OUT / f"{name}.err").write_text(stderr, encoding="utf-8")
    (CHECKS / f"{name}.exit").write_text(f"{rc}\n", encoding="utf-8")
    return {"name": name, "exit": rc, "timed_out": timed_out, "argv": argv}


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def csv_rows(path: Path) -> int:
    if not path.exists() or path.stat().st_size == 0:
        return 0
    with path.open(newline="", encoding="utf-8") as handle:
        return max(0, sum(1 for _ in csv.reader(handle)) - 1)


def read_policy_summary(symbol: str) -> dict[str, Any]:
    base = STATE / symbol / "policy_training"
    return {
        "target_rows": csv_rows(base / "structural_path_ranking_target_history.csv"),
        "summary": load_json(base / "structural_path_ranking_target_summary.json"),
        "status": load_json(base / "status.json"),
    }


def confidence_from_pre(pre: dict[str, Any]) -> float:
    for key in ("latest_confidence", "confidence", "canonical_confidence"):
        value = pre.get(key)
        if isinstance(value, (int, float)):
            return float(value)
    latest = pre.get("latest") if isinstance(pre.get("latest"), dict) else {}
    value = latest.get("confidence")
    return float(value) if isinstance(value, (int, float)) else 0.0


def main() -> int:
    REPORT.mkdir(parents=True, exist_ok=True)
    steps: list[dict[str, Any]] = []
    contexts: list[dict[str, Any]] = []
    targets: list[Path] = []

    for index, ctx in enumerate(CONTEXTS, start=1):
        symbol = ctx["symbol"]
        provider_slug = symbol.lower()
        source_rows = load_csv(ctx["path"]) if ctx["path"].exists() else []
        one_h = DATA / symbol / "1h.json"
        four_h = DATA / symbol / "4h.json"
        one_d = DATA / symbol / "1d.json"
        rows_4h = resample(source_rows, 4)
        rows_1d = resample(source_rows, 24)
        write_candles(one_h, source_rows)
        write_candles(four_h, rows_4h)
        write_candles(one_d, rows_1d)

        prefix = f"{index:02d}_{provider_slug}"
        steps.append(run_step(f"{prefix}_validate_1h", [str(ENGINE), "validate-market-state", "--data", rel(one_h), "--compact"]))
        steps.append(run_step(f"{prefix}_auto_quant_results_import", [str(ENGINE), "auto-quant-results-import", "--symbol", symbol, "--state-dir", rel(STATE), "--library", rel(LIBRARY)]))
        steps.append(run_step(f"{prefix}_auto_quant_prior_init", [str(ENGINE), "auto-quant-prior-init", "--symbol", symbol, "--state-dir", rel(STATE), "--library", rel(LIBRARY)]))
        steps.append(run_step(f"{prefix}_auto_quant_ingest_real_trades", [str(ENGINE), "auto-quant-ingest-real-trades", "--symbol", symbol, "--state-dir", rel(STATE), "--trades", rel(TRADES), "--source", f"board_a_193417_{provider_slug}"]))
        steps.append(run_step(f"{prefix}_analyze", [str(ENGINE), "analyze", "--symbol", symbol, "--data-ltf", rel(one_h), "--data-mtf", rel(four_h), "--data-htf", rel(one_d), "--state-dir", rel(STATE), "--agent"], timeout=360))
        steps.append(run_step(f"{prefix}_pre_bayes_status", [str(ENGINE), "pre-bayes-status", "--symbol", symbol, "--state-dir", rel(STATE), "--refresh", "--output-format", "json"]))
        steps.append(run_step(f"{prefix}_export_structural_path_target", [str(ENGINE), "export-structural-path-ranking-target", "--symbol", symbol, "--state-dir", rel(STATE)]))
        steps.append(run_step(f"{prefix}_policy_training_status_before_scores", [str(ENGINE), "policy-training-status", "--symbol", symbol, "--state-dir", rel(STATE), "--output-format", "json"]))
        steps.append(run_step(f"{prefix}_workflow_execution_candidate_before_scores", [str(ENGINE), "workflow-status", "--symbol", symbol, "--state-dir", rel(STATE), "--phase", "execution-candidate", "--agent"]))

        targets.append(STATE / symbol / "policy_training/structural_path_ranking_target_history.csv")
        pre = load_json(OUT / f"{prefix}_pre_bayes_status.out")
        candidate = load_json(STATE / symbol / "execution_candidate.json")
        policy = read_policy_summary(symbol)
        contexts.append(
            {
                "symbol": symbol,
                "provider": ctx["provider"],
                "market": ctx["market"],
                "source_path": rel(ctx["path"]),
                "requested_span": "all_available_rows_from_source_provider_artifact",
                "actual_start": ts_out(source_rows[0]["timestamp"]) if source_rows else None,
                "actual_end": ts_out(source_rows[-1]["timestamp"]) if source_rows else None,
                "source_native_timeframe": ctx["source_native_timeframe"],
                "native_cross_timeframe": False,
                "derived_timeframes": ["4h", "1d"],
                "rows_1h": len(source_rows),
                "rows_4h": len(rows_4h),
                "rows_1d": len(rows_1d),
                "gap_stats_1h": gap_stats(source_rows),
                "pre_bayes_confidence": confidence_from_pre(pre if isinstance(pre, dict) else {}),
                "pre_bayes_gate": (pre or {}).get("latest_gate_status") or (pre or {}).get("gate_status") if isinstance(pre, dict) else None,
                "candidate_actionable_before_scores": candidate.get("actionable") if isinstance(candidate, dict) else None,
                "candidate_ready_before_scores": candidate.get("ready") if isinstance(candidate, dict) else None,
                "candidate_status_before_scores": candidate.get("candidate_status") if isinstance(candidate, dict) else None,
                "execution_gate_status_before_scores": candidate.get("execution_gate_status") if isinstance(candidate, dict) else None,
                "target_history_rows_before_scores": policy["target_rows"],
                "target_summary_before_scores": policy["summary"],
            }
        )

    aggregate_csv = REPORT / "aggregate_structural_path_ranking_target_history.csv"
    fieldnames: list[str] | None = None
    all_rows: list[dict[str, Any]] = []
    for target in targets:
        if target.exists() and target.stat().st_size:
            with target.open(newline="", encoding="utf-8") as handle:
                reader = csv.DictReader(handle)
                fieldnames = fieldnames or list(reader.fieldnames or [])
                all_rows.extend(list(reader))
    if fieldnames:
        with aggregate_csv.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(all_rows)

    env = {"OMP_NUM_THREADS": "1", "OPENBLAS_NUM_THREADS": "1", "VECLIB_MAXIMUM_THREADS": "1"}
    aggregate_rows = csv_rows(aggregate_csv)
    scores_csv = REPORT / "aggregate_scores.csv"
    trainer_artifact = REPORT / "catboost_aggregate_v1/trainer_artifact.json"
    if aggregate_rows:
        model_dir = REPORT / "catboost_aggregate_v1"
        steps.append(run_step("70_train_catboost_aggregate", [str(UV), "run", "--offline", "--with", "pandas", "--with", "numpy", "--with", "catboost", "python", str(TRAINER), "--target-csv", str(aggregate_csv), "--output-dir", str(model_dir), "--model-family", "catboost"], timeout=240, env=env))
        steps.append(run_step("71_apply_catboost_aggregate", [str(UV), "run", "--offline", "--with", "pandas", "--with", "numpy", "--with", "catboost", "python", str(TRAINER), "--apply", "--model-dir", str(model_dir), "--target-csv", str(aggregate_csv), "--output-scores", str(scores_csv)], timeout=240, env=env))

    for index, ctx in enumerate(CONTEXTS, start=1):
        symbol = ctx["symbol"]
        provider_slug = symbol.lower()
        prefix = f"{index:02d}_{provider_slug}"
        if scores_csv.exists():
            steps.append(run_step(f"{prefix}_apply_structural_path_scores", [str(ENGINE), "apply-structural-path-ranking-external-scores", "--symbol", symbol, "--state-dir", rel(STATE), "--scores-file", rel(scores_csv)]))
        if trainer_artifact.exists():
            steps.append(run_step(f"{prefix}_register_trainer_artifact", [str(ENGINE), "register-structural-path-ranking-trainer-artifact", "--symbol", symbol, "--state-dir", rel(STATE), "--artifact-uri", rel(trainer_artifact), "--model-family", "catboost", "--score-column", "raw_path_score"]))
            steps.append(run_step(f"{prefix}_enable_path_ranker_runtime", [str(ENGINE), "enable-structural-path-ranking-runtime", "--symbol", symbol, "--state-dir", rel(STATE), "--reuse-mode", "candidate_set_only"]))
        steps.append(run_step(f"{prefix}_policy_training_status_after_scores", [str(ENGINE), "policy-training-status", "--symbol", symbol, "--state-dir", rel(STATE), "--output-format", "json"]))
        steps.append(run_step(f"{prefix}_workflow_execution_candidate_after_scores", [str(ENGINE), "workflow-status", "--symbol", symbol, "--state-dir", rel(STATE), "--phase", "execution-candidate", "--agent"]))
        after_candidate = load_json(STATE / symbol / "execution_candidate.json")
        after_policy = read_policy_summary(symbol)
        for item in contexts:
            if item["symbol"] == symbol:
                item["candidate_actionable_after_scores"] = after_candidate.get("actionable") if isinstance(after_candidate, dict) else None
                item["candidate_ready_after_scores"] = after_candidate.get("ready") if isinstance(after_candidate, dict) else None
                item["candidate_status_after_scores"] = after_candidate.get("candidate_status") if isinstance(after_candidate, dict) else None
                item["execution_gate_status_after_scores"] = after_candidate.get("execution_gate_status") if isinstance(after_candidate, dict) else None
                item["target_history_rows_after_scores"] = after_policy["target_rows"]
                item["target_summary_after_scores"] = after_policy["summary"]

    accepted_95 = [item for item in contexts if float(item.get("pre_bayes_confidence") or 0.0) >= 0.95]
    execution_ready = [
        item
        for item in contexts
        if item.get("candidate_actionable_after_scores") is True
        or item.get("execution_gate_status_after_scores") in {"execution_ready", "ready"}
    ]
    trainer = load_json(trainer_artifact) if trainer_artifact.exists() else {}
    report = {
        "schema_version": "board-a-long-horizon-provider-backed-full-chain-v1",
        "generated_at": utc_now(),
        "run_root": rel(RUN_ROOT),
        "source_provider_root": rel(SOURCE_PROVIDER),
        "source_aq_root": rel(SOURCE_AQ),
        "contexts_total": len(contexts),
        "providers_tested": sorted({item["provider"] for item in contexts}),
        "markets_tested": sorted({item["market"] for item in contexts}),
        "contexts": contexts,
        "steps_total": len(steps),
        "steps_exit_zero": sum(1 for step in steps if step["exit"] == 0),
        "steps_all_zero": all(step["exit"] == 0 for step in steps),
        "aggregate_target_rows": aggregate_rows,
        "catboost_trainer_artifact": rel(trainer_artifact) if trainer_artifact.exists() else None,
        "catboost_trained_rows": trainer.get("trained_rows") if isinstance(trainer, dict) else None,
        "catboost_calibration_rows": trainer.get("calibration_rows") if isinstance(trainer, dict) else None,
        "score_rows": csv_rows(scores_csv),
        "accepted_95_contexts": len(accepted_95),
        "execution_ready_contexts": len(execution_ready),
        "native_cross_timeframe_provider_fetch": False,
        "long_horizon_provider_backed_inventory": True,
        "promotion_allowed": False,
        "trade_usable": False,
        "update_goal": False,
        "hard_failures": [
            "4h and 1d are derived from provider 1h rows, not native provider timeframe fetches",
            "per-regime calibrated >=95 is required but only accepted_95_contexts can promote",
            "execution tree must be non-observe/actionable before any trade usable claim",
        ],
        "steps": steps,
    }
    (REPORT / "long_horizon_provider_backed_full_chain_v1.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (REPORT / "long_horizon_provider_backed_full_chain_v1.md").write_text(
        "# Long-Horizon Provider-Backed Full-Chain v1\n\n"
        f"Contexts: `{report['contexts_total']}`.\n\n"
        f"Command exits: `{report['steps_exit_zero']}/{report['steps_total']}`.\n\n"
        f"Aggregate target rows: `{aggregate_rows}`.\n\n"
        f"CatBoost trained rows: `{report['catboost_trained_rows']}`.\n\n"
        f"Accepted >=95 contexts: `{report['accepted_95_contexts']}`.\n\n"
        f"Execution-ready contexts: `{report['execution_ready_contexts']}`.\n\n"
        "Gate: fail-closed unless per-regime >=95, provider adequacy, CatBoost readiness, and execution admission all pass.\n",
        encoding="utf-8",
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["steps_all_zero"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
