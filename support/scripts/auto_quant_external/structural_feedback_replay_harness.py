from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

import pandas as pd

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[2]
sys.path.insert(0, str(REPO_ROOT / "support" / "scripts"))
from path_defaults import resolve_binary_path  # noqa: E402

ICT_ENGINE_BIN = resolve_binary_path(SCRIPT_DIR)
ENRICHER = SCRIPT_DIR / "structural_feedback_trade_enricher.py"
PATH_RANKER_TRAINER = SCRIPT_DIR / "pandas_path_ranker_trainer.py"
MULTI_TIMEFRAME_INTERVALS = ("1m", "5m", "15m", "30m", "1h", "4h", "1d")
PRIMARY_REPLAY_INTERVAL = "15m"


def load_candles(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, dict):
        candles = payload.get("candles", [])
    else:
        candles = payload
    if not isinstance(candles, list) or not candles:
        raise ValueError(f"no candles found in {path}")
    return candles


def write_candles(path: Path, symbol: str, candles: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"symbol": symbol, "candles": candles}, indent=2) + "\n", encoding="utf-8")


def normalize_timestamp(value: Any) -> str:
    timestamp = pd.Timestamp(value)
    if timestamp.tzinfo is None:
        timestamp = timestamp.tz_localize("UTC")
    else:
        timestamp = timestamp.tz_convert("UTC")
    return timestamp.isoformat().replace("+00:00", "Z")


def timeframe_feather_path(aq_data_dir: Path, symbol: str, timeframe: str) -> Path:
    standard = aq_data_dir / f"{symbol}_USD-{timeframe}.feather"
    if standard.exists():
        return standard
    futures = aq_data_dir / f"{symbol}_USD-{timeframe}-futures.feather"
    if futures.exists():
        return futures
    return standard


def materialize_multi_tf_window(
    *,
    aq_data_dir: Path,
    source_symbol: str,
    output_symbol: str,
    timeframe: str,
    anchor_timestamp: str,
    lookback: int,
    output_path: Path,
) -> Path:
    frame = pd.read_feather(timeframe_feather_path(aq_data_dir, source_symbol, timeframe))
    if "date" not in frame.columns:
        raise ValueError(f"missing date column in {timeframe} feather")
    series = pd.to_datetime(frame["date"], utc=True)
    anchor = pd.Timestamp(anchor_timestamp, tz="UTC")
    clipped = frame.loc[series <= anchor].tail(lookback).copy()
    if clipped.empty:
        raise ValueError(f"no {timeframe} candles available at or before {anchor_timestamp}")
    candles = [
        {
            "timestamp": normalize_timestamp(row["date"]),
            "open": float(row["open"]),
            "high": float(row["high"]),
            "low": float(row["low"]),
            "close": float(row["close"]),
            "volume": float(row["volume"]),
        }
        for row in clipped.to_dict(orient="records")
    ]
    write_candles(output_path, output_symbol, candles)
    return output_path


def materialize_cleaned_multi_tf_root(
    *,
    aq_data_dir: Path,
    symbol: str,
    aq_symbol: str | None,
    anchor_timestamp: str,
    lookback: int,
    output_root: Path,
) -> tuple[Path, Path]:
    market = symbol.lower()
    source_symbol = aq_symbol or symbol
    primary_path: Path | None = None
    for timeframe in MULTI_TIMEFRAME_INTERVALS:
        output_path = (
            output_root
            / f"cleaned-{timeframe}"
            / f"{market}.continuous-{timeframe}.json"
        )
        materialize_multi_tf_window(
            aq_data_dir=aq_data_dir,
            source_symbol=source_symbol,
            output_symbol=symbol,
            timeframe=timeframe,
            anchor_timestamp=anchor_timestamp,
            lookback=lookback,
            output_path=output_path,
        )
        if timeframe == PRIMARY_REPLAY_INTERVAL:
            primary_path = output_path
    if primary_path is None:
        raise ValueError("primary replay interval was not materialized")
    return output_root, primary_path


def build_multi_tf_timestamp_cache(
    *,
    aq_data_dir: Path,
    source_symbol: str,
) -> dict[str, Any]:
    cache: dict[str, Any] = {}
    for timeframe in MULTI_TIMEFRAME_INTERVALS:
        frame = pd.read_feather(
            timeframe_feather_path(aq_data_dir, source_symbol, timeframe),
            columns=["date"],
        )
        series = pd.to_datetime(frame["date"], utc=True)
        cache[timeframe] = series.astype("int64").to_numpy()
    return cache


def anchor_has_multi_tf_history(
    timestamp_cache: dict[str, Any],
    *,
    anchor_timestamp: str,
    required_bars: int,
) -> bool:
    anchor_ns = pd.Timestamp(anchor_timestamp, tz="UTC").value
    for values in timestamp_cache.values():
        if values.searchsorted(anchor_ns, side="right") < required_bars:
            return False
    return True


def run(cmd: list[str], *, cwd: Path = REPO_ROOT) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"command failed ({result.returncode}): {' '.join(cmd)}\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}")
    return result


def outcome_from_forward_window(candles: list[dict[str, Any]], entry_index: int, horizon: int, threshold: float) -> tuple[str, float, float]:
    entry_close = float(candles[entry_index]["close"])
    future = candles[entry_index + 1 : entry_index + 1 + horizon]
    if not future:
        return "breakeven", 0.0, entry_close
    exit_close = float(future[-1]["close"])
    pnl = (exit_close / entry_close) - 1.0
    max_up = max((float(row["high"]) / entry_close) - 1.0 for row in future)
    max_down = min((float(row["low"]) / entry_close) - 1.0 for row in future)
    if pnl > threshold:
        return "win", pnl, exit_close
    if pnl < -threshold:
        return "loss", pnl, exit_close
    if max_down < -threshold * 2.0 and pnl <= 0.0:
        return "invalidated", pnl, exit_close
    return "breakeven", pnl, exit_close


def pnl_cli_arg(pnl: float) -> str:
    return f"--pnl={pnl}"


def copy_prior_state(prior_state: Path | None, target_state: Path) -> None:
    if not prior_state:
        return
    if prior_state.resolve() == target_state.resolve():
        return
    if target_state.exists():
        shutil.rmtree(target_state)
    shutil.copytree(prior_state, target_state)


def generate_observation(
    *,
    symbol: str,
    candles: list[dict[str, Any]],
    output_root: Path,
    prior_state: Path | None,
    index: int,
    lookback: int,
    horizon: int,
    threshold: float,
    observation_id: int,
    branch_path: str | None = None,
    aq_data_dir: Path | None = None,
    aq_symbol: str | None = None,
) -> dict[str, Any]:
    state_dir = output_root / "state"
    copy_prior_state(prior_state, state_dir)
    data_path = output_root / "windows" / f"{symbol.lower()}_15m_obs_{observation_id:02d}.json"
    feedback_path = output_root / "feedback" / f"structural_feedback_obs_{observation_id:02d}.json"
    start = index - lookback + 1
    if start < 0 or index + horizon >= len(candles):
        raise ValueError(f"invalid window index={index} lookback={lookback} horizon={horizon}")
    analyze_data_ltf = data_path
    analyze_data_mtf = data_path
    analyze_data_htf = data_path
    analyze_data_root: Path | None = None
    if aq_data_dir:
        anchor_timestamp = candles[index]["timestamp"]
        analyze_data_root, analyze_primary_path = materialize_cleaned_multi_tf_root(
            aq_data_dir=aq_data_dir,
            symbol=symbol,
            aq_symbol=aq_symbol,
            anchor_timestamp=anchor_timestamp,
            lookback=lookback + horizon,
            output_root=output_root / "windows" / f"obs_{observation_id:02d}_clean_root",
        )
        data_path = analyze_primary_path
    else:
        write_candles(data_path, symbol, candles[start : index + 1])

    analyze_cmd = [
        str(ICT_ENGINE_BIN),
        "analyze",
        "--symbol",
        symbol,
    ]
    if analyze_data_root is not None:
        analyze_cmd.extend(["--data-root", str(analyze_data_root)])
    else:
        analyze_cmd.extend(
            [
                "--data-ltf",
                str(analyze_data_ltf),
                "--data-mtf",
                str(analyze_data_mtf),
                "--data-htf",
                str(analyze_data_htf),
            ]
        )
    analyze_cmd.extend(["--state-dir", str(state_dir), "--human"])
    run(analyze_cmd)
    run([
        str(ICT_ENGINE_BIN),
        "export-structural-path-ranking-target",
        "--symbol",
        symbol,
        "--state-dir",
        str(state_dir),
    ])

    target_csv = state_dir / symbol / "policy_training" / "structural_path_ranking_target.csv"
    model_dir = state_dir / symbol / "policy_training" / "path_ranker_model"
    scores_path = output_root / "scores" / f"scores_obs_{observation_id:02d}.csv"
    scores_path.parent.mkdir(parents=True, exist_ok=True)
    if model_dir.exists():
        run([
            sys.executable,
            str(PATH_RANKER_TRAINER),
            "--apply",
            "--model-dir",
            str(model_dir),
            "--target-csv",
            str(target_csv),
            "--output-scores",
            str(scores_path),
        ])
        run([
            str(ICT_ENGINE_BIN),
            "apply-structural-path-ranking-external-scores",
            "--symbol",
            symbol,
            "--state-dir",
            str(state_dir),
            "--scores-file",
            str(scores_path),
        ])
        run([
            str(ICT_ENGINE_BIN),
            "export-structural-path-ranking-target",
            "--symbol",
            symbol,
            "--state-dir",
            str(state_dir),
        ])
    outcome, pnl, exit_close = outcome_from_forward_window(candles, index, horizon, threshold)
    emit_cmd = [
        sys.executable,
        str(ENRICHER),
        "emit-probe",
        "--target-csv",
        str(target_csv),
        "--output",
        str(feedback_path),
        "--rank",
        "1",
        "--realized-outcome",
        outcome,
        pnl_cli_arg(pnl),
        "--exit-reason",
        f"forward_{horizon}_bar_close",
        "--notes",
        f"semi_auto_replay observation={observation_id} data_index={index} threshold={threshold}",
    ]
    if branch_path:
        emit_cmd.extend(["--path-id", branch_path])
    run(emit_cmd)
    update = run([
        str(ICT_ENGINE_BIN),
        "update",
        "--symbol",
        symbol,
        "--outcome",
        outcome,
        "--entry-signal",
        "medium",
        "--state-dir",
        str(state_dir),
        f"--pnl={pnl}",
        "--feedback-file",
        str(feedback_path),
    ])
    export = run([
        str(ICT_ENGINE_BIN),
        "export-structural-path-ranking-target",
        "--symbol",
        symbol,
        "--state-dir",
        str(state_dir),
    ])
    summary = json.loads(export.stdout)
    return {
        "observation_id": observation_id,
        "data_path": str(data_path),
        "data_root": str(analyze_data_root) if analyze_data_root else None,
        "feedback_path": str(feedback_path),
        "window_start": candles[start]["timestamp"],
        "entry_timestamp": candles[index]["timestamp"],
        "exit_timestamp": candles[index + horizon]["timestamp"],
        "entry_close": float(candles[index]["close"]),
        "exit_close": exit_close,
        "outcome": outcome,
        "pnl": pnl,
        "mature_rows": summary.get("mature_rows"),
        "history_mature_rows": summary.get("history_mature_rows"),
        "summary_line": summary.get("summary_line"),
        "update_stdout_bytes": len(update.stdout),
    }


def run_execution_materialization_analyze(
    *,
    symbol: str,
    state_dir: Path,
    observation: dict[str, Any],
) -> dict[str, Any]:
    data_root = observation.get("data_root")
    data_path = observation.get("data_path")
    analyze_cmd = [str(ICT_ENGINE_BIN), "analyze", "--symbol", symbol]
    if data_root:
        analyze_cmd.extend(["--data-root", str(data_root)])
    elif data_path:
        analyze_cmd.extend(
            [
                "--data-ltf",
                str(data_path),
                "--data-mtf",
                str(data_path),
                "--data-htf",
                str(data_path),
            ]
        )
    else:
        raise ValueError("selected observation has no data_root or data_path")
    analyze_cmd.extend(["--state-dir", str(state_dir), "--human"])
    result = run(analyze_cmd)
    return {
        "observation_id": observation.get("observation_id"),
        "observation_label": observation.get("observation_label"),
        "data_root": str(data_root) if data_root else None,
        "data_path": str(data_path) if data_path else None,
        "stdout_bytes": len(result.stdout),
    }


def run_materialization_only(
    *,
    output_root: Path,
    symbol: str,
    prior_state: Path | None,
    data_root: Path | None,
    data_path: Path | None,
    observation_label: str | None = None,
) -> dict[str, Any]:
    if data_root is None and data_path is None:
        raise ValueError("materialization-only mode requires data_root or data_path")
    output_root.mkdir(parents=True, exist_ok=True)
    state_dir = output_root / "state"
    copy_prior_state(prior_state, state_dir)
    execution_materialization = run_execution_materialization_analyze(
        symbol=symbol,
        state_dir=state_dir,
        observation={
            "observation_label": observation_label,
            "data_root": str(data_root) if data_root is not None else None,
            "data_path": str(data_path) if data_path is not None else None,
        },
    )
    summary = {
        "ok": True,
        "symbol": symbol,
        "output_root": str(output_root),
        "count": 0,
        "branch_path": None,
        "final_mature_rows": None,
        "execution_materialization": execution_materialization,
        "observations": [],
    }
    (output_root / "replay_summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    return summary


def run_replay(
    *,
    candles_path: Path,
    output_root: Path,
    symbol: str,
    count: int,
    lookback: int,
    horizon: int,
    threshold: float,
    prior_state: Path | None,
    branch_path: str | None = None,
    aq_data_dir: Path | None = None,
    aq_symbol: str | None = None,
    execution_materialization_observation_id: int | None = None,
) -> dict[str, Any]:
    candles = load_candles(candles_path)
    output_root.mkdir(parents=True, exist_ok=True)
    min_index = lookback - 1
    max_index = len(candles) - horizon - 1
    if max_index <= min_index:
        raise ValueError("not enough candles for replay")
    candidate_indices = list(range(min_index, max_index + 1))
    if aq_data_dir:
        timestamp_cache = build_multi_tf_timestamp_cache(
            aq_data_dir=aq_data_dir,
            source_symbol=aq_symbol or symbol,
        )
        candidate_indices = [
            index
            for index in candidate_indices
            if anchor_has_multi_tf_history(
                timestamp_cache,
                anchor_timestamp=candles[index]["timestamp"],
                required_bars=lookback + horizon,
            )
        ]
        if not candidate_indices:
            raise ValueError("no replay anchors satisfy multi-timeframe history requirements")
    if count <= 1:
        indices = [candidate_indices[-1]]
    elif len(candidate_indices) <= count:
        indices = candidate_indices
    else:
        last = len(candidate_indices) - 1
        indices = [
            candidate_indices[(last * idx) // (count - 1)]
            for idx in range(count)
        ]
    observations = []
    for obs_id, index in enumerate(indices, start=1):
        observations.append(
            generate_observation(
                symbol=symbol,
                candles=candles,
                output_root=output_root,
                prior_state=prior_state if obs_id == 1 else output_root / "state",
                index=index,
                lookback=lookback,
                horizon=horizon,
                threshold=threshold,
                observation_id=obs_id,
                branch_path=branch_path,
                aq_data_dir=aq_data_dir,
                aq_symbol=aq_symbol,
            )
        )
    execution_materialization = None
    if execution_materialization_observation_id is not None:
        selected = next(
            (
                observation
                for observation in observations
                if observation.get("observation_id") == execution_materialization_observation_id
            ),
            None,
        )
        if selected is None:
            raise ValueError(
                "execution materialization observation "
                f"{execution_materialization_observation_id} was not generated"
            )
        execution_materialization = run_execution_materialization_analyze(
            symbol=symbol,
            state_dir=output_root / "state",
            observation=selected,
        )
    summary = {
        "ok": True,
        "symbol": symbol,
        "candles_path": str(candles_path),
        "output_root": str(output_root),
        "count": len(observations),
        "lookback": lookback,
        "horizon": horizon,
        "threshold": threshold,
        "branch_path": branch_path,
        "final_mature_rows": observations[-1]["mature_rows"] if observations else None,
        "execution_materialization": execution_materialization,
        "observations": observations,
    }
    (output_root / "replay_summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    return summary


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Semi-auto structural feedback replay harness")
    parser.add_argument("--candles")
    parser.add_argument("--output-root", required=True)
    parser.add_argument("--symbol", default="NQ")
    parser.add_argument("--count", type=int, default=29)
    parser.add_argument("--lookback", type=int, default=52)
    parser.add_argument("--horizon", type=int, default=16)
    parser.add_argument("--threshold", type=float, default=0.001)
    parser.add_argument("--prior-state")
    parser.add_argument(
        "--branch-path",
        help="Exact regime_profit_branch_path/path_id to emit feedback for instead of rank 1.",
    )
    parser.add_argument(
        "--aq-data-dir",
        help="Optional AQ feather directory used to materialize distinct 1m/15m/1h replay windows.",
    )
    parser.add_argument(
        "--aq-symbol",
        help="Optional source symbol for AQ feather lookup when replay state symbol differs from the retained market symbol.",
    )
    parser.add_argument(
        "--execution-materialization-observation-id",
        type=int,
        help="After feedback replay, rerun analyze from this generated observation window without adding another feedback/update row.",
    )
    parser.add_argument(
        "--execution-materialization-data-root",
        help="Run materialization-only analyze from an existing data-root, without generating observations or feedback/update rows.",
    )
    parser.add_argument(
        "--execution-materialization-data-path",
        help="Run materialization-only analyze from an existing single data path, without generating observations or feedback/update rows.",
    )
    parser.add_argument(
        "--execution-materialization-label",
        help="Optional label recorded in materialization-only summary, for example obs_09.",
    )
    args = parser.parse_args(argv)
    has_materialization_input = bool(
        args.execution_materialization_data_root or args.execution_materialization_data_path
    )
    if not args.candles and not has_materialization_input:
        parser.error("--candles is required unless materialization-only data is supplied")
    return args


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    materialization_data_root = Path(args.execution_materialization_data_root) if args.execution_materialization_data_root else None
    materialization_data_path = Path(args.execution_materialization_data_path) if args.execution_materialization_data_path else None
    if materialization_data_root is not None or materialization_data_path is not None:
        summary = run_materialization_only(
            output_root=Path(args.output_root),
            symbol=args.symbol,
            prior_state=Path(args.prior_state) if args.prior_state else None,
            data_root=materialization_data_root,
            data_path=materialization_data_path,
            observation_label=args.execution_materialization_label,
        )
        print(json.dumps({k: v for k, v in summary.items() if k != "observations"}, indent=2))
        print("[done] materialization_only=true observations=0")
        return 0
    summary = run_replay(
        candles_path=Path(args.candles),
        output_root=Path(args.output_root),
        symbol=args.symbol,
        count=args.count,
        lookback=args.lookback,
        horizon=args.horizon,
        threshold=args.threshold,
        prior_state=Path(args.prior_state) if args.prior_state else None,
        branch_path=args.branch_path,
        aq_data_dir=Path(args.aq_data_dir) if args.aq_data_dir else None,
        aq_symbol=args.aq_symbol,
        execution_materialization_observation_id=args.execution_materialization_observation_id,
    )
    print(json.dumps({k: v for k, v in summary.items() if k != "observations"}, indent=2))
    print(f"[done] observations={len(summary['observations'])} final_mature_rows={summary['final_mature_rows']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
