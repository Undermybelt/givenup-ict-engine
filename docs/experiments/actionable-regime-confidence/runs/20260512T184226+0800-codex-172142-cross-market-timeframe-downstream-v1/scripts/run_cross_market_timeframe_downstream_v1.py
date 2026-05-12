#!/usr/bin/env python3
"""Expand Board A 172142 downstream readback across provider/window contexts."""

from __future__ import annotations

import csv
import json
import math
import os
import subprocess
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path


REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs/"
    "20260512T172142+0800-codex-board-a-feasible-window-same-root-aq-packet-v1"
)
STATE_DIR = RUN_ROOT / "state_cross_market_timeframe_v1"
DATA_DIR = RUN_ROOT / "data"
CMD_DIR = RUN_ROOT / "command-output"
CHECK_DIR = RUN_ROOT / "checks"
SUMMARY_DIR = RUN_ROOT / "cross-market-timeframe-downstream-v1"
PATH_RANKER_DIR = RUN_ROOT / "path-ranker/catboost_cross_market_timeframe_v1"

ENGINE = REPO / "target/debug/ict-engine"
UV = Path("/Users/thrill3r/.local/bin/uv")
TRAINER = REPO / "scripts/auto_quant_external/pandas_path_ranker_trainer.py"
LIBRARY = SOURCE_ROOT / "provider_btc_172142_strategy_library_v1.json"
TRADES = SOURCE_ROOT / "provider_btc_172142_real_trades_v1.jsonl"

PROVIDERS = {
    "yfinance": SOURCE_ROOT / "provider-csv/yfinance_btc_usd_1h.csv",
    "ibkr_aggtrades": SOURCE_ROOT / "provider-csv/BTC_1h_aggtrades.csv",
    "kraken": SOURCE_ROOT / "provider-csv/kraken_xbtusd_1h.csv",
    "binance": SOURCE_ROOT / "provider-csv/binance_btcusdt_1h.csv",
    "bybit": SOURCE_ROOT / "provider-csv/bybit_btcusdt_linear_1h.csv",
    "tvr_local_stdio": SOURCE_ROOT / "provider-csv/tvr_btc_usd_local_stdio_1h.csv",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def parse_ts(text: str) -> datetime:
    value = text.strip().replace("Z", "+00:00")
    if " " in value and "T" not in value:
        value = value.replace(" ", "T")
    return datetime.fromisoformat(value).astimezone(timezone.utc)


def ts_out(ts: datetime) -> str:
    return ts.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def load_rows(path: Path) -> list[dict]:
    with path.open(newline="") as handle:
        reader = csv.DictReader(handle)
        rows = []
        for row in reader:
            key = "timestamp" if "timestamp" in row else "date" if "date" in row else "ts"
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
            except (KeyError, TypeError, ValueError):
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
        if not chunk:
            continue
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


def write_json(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    serializable = []
    for row in rows:
        item = dict(row)
        if isinstance(item["timestamp"], datetime):
            item["timestamp"] = ts_out(item["timestamp"])
        serializable.append(item)
    path.write_text(json.dumps(serializable, indent=2) + "\n")


def contexts() -> list[dict]:
    result = []
    ratios = [0.34, 0.50, 0.67, 0.84, 1.00]
    for provider, path in PROVIDERS.items():
        rows = load_rows(path)
        n = len(rows)
        for idx, ratio in enumerate(ratios, start=1):
            take = max(120, int(math.floor(n * ratio)))
            take = min(n, take)
            window = rows[-take:]
            ltf = DATA_DIR / provider / f"w{idx}" / "ltf_1h.json"
            mtf = DATA_DIR / provider / f"w{idx}" / "mtf_4h.json"
            htf = DATA_DIR / provider / f"w{idx}" / "htf_1d.json"
            write_json(ltf, window)
            write_json(mtf, resample(window, 4))
            write_json(htf, resample(window, 24))
            result.append(
                {
                    "provider": provider,
                    "window": f"w{idx}",
                    "symbol": f"BOARD_A_172142_{provider.upper()}_W{idx}",
                    "rows_1h": len(window),
                    "rows_4h": len(json.loads(mtf.read_text())),
                    "rows_1d": len(json.loads(htf.read_text())),
                    "start": ts_out(window[0]["timestamp"]),
                    "end": ts_out(window[-1]["timestamp"]),
                    "ltf": str(ltf),
                    "mtf": str(mtf),
                    "htf": str(htf),
                }
            )
    return result


def run_step(name: str, argv: list[str], env: dict | None = None) -> dict:
    CMD_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)
    safe = name.replace("/", "_")
    (CMD_DIR / f"{safe}.cmd").write_text(" ".join(argv) + "\n")
    proc = subprocess.run(
        argv,
        cwd=REPO,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env={**os.environ, **(env or {})},
    )
    (CMD_DIR / f"{safe}.out").write_text(proc.stdout)
    (CMD_DIR / f"{safe}.err").write_text(proc.stderr)
    (CHECK_DIR / f"{safe}.exit").write_text(str(proc.returncode) + "\n")
    return {
        "name": name,
        "argv": argv,
        "exit": proc.returncode,
        "stdout_path": str(CMD_DIR / f"{safe}.out"),
        "stderr_path": str(CMD_DIR / f"{safe}.err"),
    }


def collect_csv_rows(paths: list[Path], out_csv: Path) -> int:
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = None
    rows = []
    for path in paths:
        if not path.exists() or path.stat().st_size == 0:
            continue
        with path.open(newline="") as handle:
            reader = csv.DictReader(handle)
            if fieldnames is None:
                fieldnames = list(reader.fieldnames or [])
            for row in reader:
                rows.append(row)
    if not fieldnames:
        out_csv.write_text("")
        return 0
    with out_csv.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    return len(rows)


def json_from_out(path: Path) -> dict:
    try:
        return json.loads(path.read_text())
    except Exception:
        return {}


def main() -> int:
    SUMMARY_DIR.mkdir(parents=True, exist_ok=True)
    PATH_RANKER_DIR.mkdir(parents=True, exist_ok=True)
    context_rows = contexts()
    steps = []
    per_context = []
    target_csvs = []

    for idx, ctx in enumerate(context_rows, start=1):
        prefix = f"{idx:02d}_{ctx['provider']}_{ctx['window']}"
        symbol = ctx["symbol"]
        steps.append(
            run_step(
                f"{prefix}_auto_quant_results_import",
                [
                    str(ENGINE),
                    "auto-quant-results-import",
                    "--symbol",
                    symbol,
                    "--state-dir",
                    str(STATE_DIR),
                    "--library",
                    str(LIBRARY),
                ],
            )
        )
        steps.append(
            run_step(
                f"{prefix}_auto_quant_prior_init",
                [
                    str(ENGINE),
                    "auto-quant-prior-init",
                    "--symbol",
                    symbol,
                    "--state-dir",
                    str(STATE_DIR),
                    "--library",
                    str(LIBRARY),
                ],
            )
        )
        steps.append(
            run_step(
                f"{prefix}_auto_quant_ingest_real_trades",
                [
                    str(ENGINE),
                    "auto-quant-ingest-real-trades",
                    "--symbol",
                    symbol,
                    "--state-dir",
                    str(STATE_DIR),
                    "--trades",
                    str(TRADES),
                    "--source",
                    f"board_a_184226_{ctx['provider']}_{ctx['window']}",
                ],
            )
        )
        steps.append(
            run_step(
                f"{prefix}_analyze",
                [
                    str(ENGINE),
                    "analyze",
                    "--symbol",
                    symbol,
                    "--data-htf",
                    ctx["htf"],
                    "--data-mtf",
                    ctx["mtf"],
                    "--data-ltf",
                    ctx["ltf"],
                    "--state-dir",
                    str(STATE_DIR),
                    "--agent",
                ],
            )
        )
        steps.append(
            run_step(
                f"{prefix}_pre_bayes_status",
                [
                    str(ENGINE),
                    "pre-bayes-status",
                    "--symbol",
                    symbol,
                    "--state-dir",
                    str(STATE_DIR),
                    "--refresh",
                    "--output-format",
                    "json",
                ],
            )
        )
        steps.append(
            run_step(
                f"{prefix}_export_structural_path_target",
                [
                    str(ENGINE),
                    "export-structural-path-ranking-target",
                    "--symbol",
                    symbol,
                    "--state-dir",
                    str(STATE_DIR),
                ],
            )
        )
        steps.append(
            run_step(
                f"{prefix}_workflow_execution_candidate",
                [
                    str(ENGINE),
                    "workflow-status",
                    "--symbol",
                    symbol,
                    "--state-dir",
                    str(STATE_DIR),
                    "--phase",
                    "execution-candidate",
                    "--agent",
                ],
            )
        )

        target = STATE_DIR / symbol / "policy_training/structural_path_ranking_target_history.csv"
        target_csvs.append(target)
        pre = json_from_out(CMD_DIR / f"{prefix}_pre_bayes_status.out")
        candidate = json_from_out(STATE_DIR / symbol / "execution_candidate.json")
        per_context.append(
            {
                **ctx,
                "target_history_csv": str(target),
                "target_history_rows": sum(1 for _ in target.open()) - 1 if target.exists() else 0,
                "pre_bayes_confidence": pre.get("latest_confidence")
                or pre.get("confidence")
                or pre.get("latest", {}).get("confidence"),
                "pre_bayes_status": pre.get("latest_gate_status")
                or pre.get("gate_status")
                or pre.get("latest", {}).get("gate_status"),
                "candidate_actionable": candidate.get("actionable"),
                "candidate_status": candidate.get("candidate_status"),
                "execution_gate_status": candidate.get("execution_gate_status"),
            }
        )

    aggregate_csv = PATH_RANKER_DIR / "aggregate_structural_path_ranking_target_history.csv"
    aggregate_rows = collect_csv_rows(target_csvs, aggregate_csv)

    env = {
        "OMP_NUM_THREADS": "1",
        "OPENBLAS_NUM_THREADS": "1",
        "MKL_NUM_THREADS": "1",
        "VECLIB_MAXIMUM_THREADS": "1",
    }
    steps.append(
        run_step(
            "31_catboost_train_aggregate",
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
                str(TRAINER),
                "--target-csv",
                str(aggregate_csv),
                "--output-dir",
                str(PATH_RANKER_DIR),
                "--model-family",
                "catboost",
            ],
            env=env,
        )
    )
    scores_csv = PATH_RANKER_DIR / "aggregate_path_scores.csv"
    steps.append(
        run_step(
            "32_catboost_apply_aggregate",
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
                str(TRAINER),
                "--apply",
                "--model-dir",
                str(PATH_RANKER_DIR),
                "--target-csv",
                str(aggregate_csv),
                "--output-scores",
                str(scores_csv),
            ],
            env=env,
        )
    )

    trainer_artifact = json_from_out(PATH_RANKER_DIR / "trainer_artifact.json")
    exits_ok = sum(1 for step in steps if step["exit"] == 0)
    confidences = [
        item["pre_bayes_confidence"]
        for item in per_context
        if isinstance(item.get("pre_bayes_confidence"), (int, float))
    ]
    max_confidence = max(confidences) if confidences else None
    accepted_95 = [item for item in per_context if (item.get("pre_bayes_confidence") or 0) >= 0.95]
    execution_ready = [
        item
        for item in per_context
        if item.get("candidate_actionable") is True
        or item.get("execution_gate_status") in {"execution_ready", "ready"}
    ]
    report = {
        "generated_at": utc_now(),
        "source_packet": "172142_feasible_window_same_root_aq_packet",
        "source_root": str(SOURCE_ROOT),
        "run_root": str(RUN_ROOT),
        "state_dir": str(STATE_DIR),
        "provider_contexts": sorted(PROVIDERS),
        "window_contexts_per_provider": 5,
        "contexts_total": len(per_context),
        "aggregate_target_csv": str(aggregate_csv),
        "aggregate_target_rows": aggregate_rows,
        "steps_total": len(steps),
        "steps_exit_zero": exits_ok,
        "steps_all_zero": exits_ok == len(steps),
        "max_pre_bayes_confidence": max_confidence,
        "accepted_95_contexts": len(accepted_95),
        "execution_ready_contexts": len(execution_ready),
        "trainer_artifact": trainer_artifact,
        "score_rows": max(0, sum(1 for _ in scores_csv.open()) - 1) if scores_csv.exists() else 0,
        "promotion_allowed": False,
        "trade_usable": False,
        "update_goal": False,
        "contexts": per_context,
        "steps": steps,
    }
    (SUMMARY_DIR / "cross_market_timeframe_downstream_v1.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n"
    )
    lines = [
        "# Cross-Market/Timeframe Downstream v1",
        "",
        f"Generated: `{report['generated_at']}`",
        f"Source packet: `{report['source_packet']}`",
        f"Contexts: `{report['contexts_total']}` across `{', '.join(report['provider_contexts'])}`",
        f"Command exits: `{report['steps_exit_zero']}/{report['steps_total']}`",
        f"Aggregate target rows: `{report['aggregate_target_rows']}`",
        f"Score rows: `{report['score_rows']}`",
        f"Max Pre-Bayes confidence: `{report['max_pre_bayes_confidence']}`",
        f"Accepted >=95 contexts: `{report['accepted_95_contexts']}`",
        f"Execution-ready contexts: `{report['execution_ready_contexts']}`",
        "",
        "Gate: fail-closed unless every Board A requirement is met from artifacts.",
    ]
    (SUMMARY_DIR / "cross_market_timeframe_downstream_v1.md").write_text("\n".join(lines) + "\n")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if exits_ok == len(steps) else 2


if __name__ == "__main__":
    raise SystemExit(main())
