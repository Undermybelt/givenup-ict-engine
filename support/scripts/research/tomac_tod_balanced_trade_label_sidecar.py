from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

import factor_payoff_shape_report as payoff_report
import payoff_to_path_ranker_target as path_target
import purged_cv_backtest_guard as purged_cv
import simulated_feedback_admission_guard as admission_guard


SIGNAL_FILE = "aq_workspace/user_data/tod_portfolio_signals.feather"
TERMINAL_METRICS_FILE = "checks/terminal_metrics.json"
PAIR_DATA_DIR = "aq_workspace/user_data/data/futures"
DEFAULT_SL_MULT = 0.01
DEFAULT_COST_BPS_SIDE = 5.0
PROVIDER_PARITY_PROBE_FILE = "checks/provider_parity_probe.json"
DOWNSTREAM_ROOT_GLOB = "downstream-exact-tomac-tod-balanced*"
DOWNSTREAM_TERMINAL_METRICS_FILE = "checks/terminal_metrics.json"
DOWNSTREAM_TRAINER_ARTIFACT_FILE = "path_ranker_model/trainer_artifact.json"


@dataclass(frozen=True)
class OpenTrade:
    pair: str
    side: int
    entry_ts: pd.Timestamp
    entry_index: int
    entry_price: float
    factor_ids: str


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=False) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=False) + "\n")


def _load_optional_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return _load_json(path)


def _normalize_timestamp(series: pd.Series) -> pd.Series:
    return pd.to_datetime(series, utc=True)


def _terminal_rank_row(terminal_metrics: dict[str, Any]) -> dict[str, Any]:
    rank_rows = terminal_metrics.get("rank_rows")
    if isinstance(rank_rows, list) and rank_rows:
        first = rank_rows[0]
        if isinstance(first, dict):
            return first
    return {}


def _load_signal_frame(path: Path) -> pd.DataFrame:
    frame = pd.read_feather(path)
    frame = frame.copy()
    frame["ts"] = _normalize_timestamp(frame["date"])
    frame["pair"] = frame["pair"].astype(str)
    frame = frame.sort_values(["ts", "pair"]).reset_index(drop=True)
    return frame


def _load_price_frames(data_dir: Path) -> dict[str, pd.DataFrame]:
    frames: dict[str, pd.DataFrame] = {}
    for feather in sorted(data_dir.glob("*_USD-1m-futures.feather")):
        pair = feather.name.replace("_USD-1m-futures.feather", "") + "/USD"
        frame = pd.read_feather(feather)
        frame = frame.rename(columns={"date": "timestamp"}).copy()
        frame["ts"] = _normalize_timestamp(frame["timestamp"])
        frame = frame.sort_values("ts").reset_index(drop=True)
        frames[pair] = frame
    if not frames:
        raise FileNotFoundError(f"no 1m futures feathers found under {data_dir}")
    return frames


def _latest_matching_directory(parent: Path, pattern: str) -> Path | None:
    candidates = [path for path in parent.glob(pattern) if path.is_dir()]
    if not candidates:
        return None
    return sorted(candidates)[-1]


def _first_numeric(*values: Any) -> float | None:
    for value in values:
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str) and "/" in value:
            head = value.split("/", 1)[0].strip()
            try:
                return float(head)
            except ValueError:
                continue
    return None


def _int_or_default(value: float | None, default: int) -> int:
    if value is None:
        return default
    return int(value)


def _build_admission_summary(
    *,
    exact_root: Path,
    trade_count: int,
    terminal_row: dict[str, Any],
) -> dict[str, Any]:
    summary: dict[str, Any] = {
        "trade_count": trade_count,
        "exact_5bps_survivors": [
            {
                "trade_count": trade_count,
                "profit_pct_5bps": terminal_row.get("5bps_per_side_total_profit_pct"),
                "gate1_survivor": terminal_row.get("gate1_survivor"),
            }
        ],
        "provider_parity": False,
        "raw_scored_mature_rows": 0,
        "production_validation_rows": 0,
        "observation_validation_rows": 0,
        "execution_readiness": 0.0,
        "transition_hazard": 1.0,
        "actionable": False,
    }

    provider_probe = _load_optional_json(exact_root / PROVIDER_PARITY_PROBE_FILE)
    if provider_probe:
        summary["provider_parity"] = bool(provider_probe.get("ok"))

    downstream_root = _latest_matching_directory(exact_root.parent, DOWNSTREAM_ROOT_GLOB)
    if downstream_root is None:
        return summary

    downstream_terminal = _load_optional_json(downstream_root / DOWNSTREAM_TERMINAL_METRICS_FILE)
    trainer_artifact = _load_optional_json(downstream_root / DOWNSTREAM_TRAINER_ARTIFACT_FILE)
    validation_metrics = dict(
        trainer_artifact.get("validation_metrics")
        or trainer_artifact.get("validation_summary")
        or {}
    )
    validation_counters = dict(downstream_terminal.get("validation_counters") or {})

    summary["raw_scored_mature_rows"] = _int_or_default(
        _first_numeric(
            validation_metrics.get("raw_scored_mature_rows"),
            validation_counters.get("raw_scored_mature"),
        ),
        int(summary["raw_scored_mature_rows"]),
    )
    summary["production_validation_rows"] = _int_or_default(
        _first_numeric(
            validation_metrics.get("production_validation_rows"),
            validation_counters.get("production_validation"),
        ),
        int(summary["production_validation_rows"]),
    )
    summary["observation_validation_rows"] = _int_or_default(
        _first_numeric(
            validation_metrics.get("observation_validation_rows"),
            validation_counters.get("observation_validation"),
        ),
        int(summary["observation_validation_rows"]),
    )
    summary["execution_readiness"] = (
        downstream_terminal.get("execution_readiness")
        if isinstance(downstream_terminal.get("execution_readiness"), (int, float))
        else summary["execution_readiness"]
    )
    summary["transition_hazard"] = (
        downstream_terminal.get("transition_hazard")
        if isinstance(downstream_terminal.get("transition_hazard"), (int, float))
        else summary["transition_hazard"]
    )
    summary["actionable"] = bool(
        downstream_terminal.get("execution_candidate_actionable")
        if "execution_candidate_actionable" in downstream_terminal
        else downstream_terminal.get("actionable", summary["actionable"])
    )
    return summary


def _timestamp_index(frame: pd.DataFrame) -> dict[pd.Timestamp, int]:
    return {ts: index for index, ts in enumerate(frame["ts"].tolist())}


def _path_mfe_mae(frame: pd.DataFrame, entry_index: int, exit_index: int, entry_price: float, side: int) -> tuple[float, float]:
    mfe = 0.0
    mae = 0.0
    if exit_index <= entry_index:
        return mfe, mae
    for _, row in frame.iloc[entry_index + 1 : exit_index + 1].iterrows():
        high = float(row["high"])
        low = float(row["low"])
        high_ret = side * ((high - entry_price) / entry_price)
        low_ret = side * ((low - entry_price) / entry_price)
        mfe = max(mfe, high_ret, low_ret)
        mae = min(mae, high_ret, low_ret)
    return round(mfe, 6), round(mae, 6)


def build_trade_labels(
    *,
    signals: pd.DataFrame,
    price_frames: dict[str, pd.DataFrame],
    factor_id: str,
    branch_path: str,
    sl_mult: float,
    cost_bps_side: float,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    if sl_mult <= 0:
        raise ValueError("sl_mult must be positive")
    round_trip_cost = (cost_bps_side * 2.0) / 10_000.0
    index_lookup = {pair: _timestamp_index(frame) for pair, frame in price_frames.items()}
    open_positions: dict[str, OpenTrade] = {}
    labels: list[dict[str, Any]] = []
    ignored_rows: list[str] = []

    for _, signal in signals.iterrows():
        pair = str(signal["pair"])
        if pair not in price_frames:
            ignored_rows.append(f"missing_pair_frame:{pair}")
            continue
        frame = price_frames[pair]
        ts = signal["ts"]
        candle_index = index_lookup[pair].get(ts)
        if candle_index is None:
            ignored_rows.append(f"missing_timestamp:{pair}:{ts.isoformat()}")
            continue
        candle = frame.iloc[candle_index]
        price = float(candle["close"])
        open_trade = open_positions.get(pair)
        exit_long = bool(signal.get("tod_exit_long", 0))
        exit_short = bool(signal.get("tod_exit_short", 0))

        if open_trade and ((open_trade.side == 1 and exit_long) or (open_trade.side == -1 and exit_short)):
            gross_return = open_trade.side * ((price - open_trade.entry_price) / open_trade.entry_price)
            net_return = gross_return - round_trip_cost
            mfe, mae = _path_mfe_mae(
                frame=frame,
                entry_index=open_trade.entry_index,
                exit_index=candle_index,
                entry_price=open_trade.entry_price,
                side=open_trade.side,
            )
            labels.append(
                {
                    "schema_version": "tomac-balanced-trade-label/v1",
                    "candidate_id": factor_id,
                    "factor_id": factor_id,
                    "branch_path": branch_path,
                    "pair": pair,
                    "entry_index": open_trade.entry_index,
                    "exit_index": candle_index,
                    "entry_timestamp": open_trade.entry_ts.isoformat().replace("+00:00", "Z"),
                    "exit_timestamp": ts.isoformat().replace("+00:00", "Z"),
                    "open_timestamp": open_trade.entry_ts.isoformat().replace("+00:00", "Z"),
                    "close_timestamp": ts.isoformat().replace("+00:00", "Z"),
                    "open_ts": open_trade.entry_ts.isoformat().replace("+00:00", "Z"),
                    "close_ts": ts.isoformat().replace("+00:00", "Z"),
                    "open_ts_ms": int(open_trade.entry_ts.timestamp() * 1000),
                    "close_ts_ms": int(ts.timestamp() * 1000),
                    "side": open_trade.side,
                    "entry_price": open_trade.entry_price,
                    "exit_price": price,
                    "gross_return": round(gross_return, 6),
                    "net_return": round(net_return, 6),
                    "realized_R": round(net_return / sl_mult, 6),
                    "cost_R": round(round_trip_cost / sl_mult, 6),
                    "slippage_R": round(round_trip_cost / sl_mult, 6),
                    "mfe": mfe,
                    "mae": mae,
                    "time_to_hit": candle_index - open_trade.entry_index,
                    "meta_label": 1 if net_return > 0 else 0,
                    "barrier_hit": "signal_exit",
                    "tod_factor_ids": open_trade.factor_ids,
                    "feedback_source": "retained_real_event_label_simulation",
                    "risk_normalization_basis": f"fixed_sl_mult_{sl_mult:.4f}",
                }
            )
            del open_positions[pair]
            open_trade = None

        enter_long = bool(signal.get("tod_enter_long", 0))
        enter_short = bool(signal.get("tod_enter_short", 0))
        if open_trade is None:
            if enter_long:
                open_positions[pair] = OpenTrade(
                    pair=pair,
                    side=1,
                    entry_ts=ts,
                    entry_index=candle_index,
                    entry_price=price,
                    factor_ids=str(signal.get("tod_factor_ids", "")),
                )
            elif enter_short:
                open_positions[pair] = OpenTrade(
                    pair=pair,
                    side=-1,
                    entry_ts=ts,
                    entry_index=candle_index,
                    entry_price=price,
                    factor_ids=str(signal.get("tod_factor_ids", "")),
                )

    diagnostics = {
        "ignored_rows": ignored_rows,
        "ignored_row_count": len(ignored_rows),
        "open_position_count": len(open_positions),
        "dangling_pairs": sorted(open_positions),
        "pair_breakdown": {
            pair: sum(1 for row in labels if row["pair"] == pair)
            for pair in sorted({row["pair"] for row in labels})
        },
    }
    return labels, diagnostics


def run_sidecar(
    *,
    exact_root: Path,
    output_dir: Path,
    sl_mult: float,
    cost_bps_side: float,
    nb_trials: int,
    periods_per_year: int,
    embargo_bars: int,
    fold_count: int,
) -> dict[str, Any]:
    terminal_metrics = _load_json(exact_root / TERMINAL_METRICS_FILE)
    terminal_row = _terminal_rank_row(terminal_metrics)
    factor_id = str(terminal_metrics.get("factor_id") or terminal_metrics.get("strategy_id") or "")
    branch_path = str(terminal_metrics.get("branch_path") or "")
    signals = _load_signal_frame(exact_root / SIGNAL_FILE)
    price_frames = _load_price_frames(exact_root / PAIR_DATA_DIR)
    labels, diagnostics = build_trade_labels(
        signals=signals,
        price_frames=price_frames,
        factor_id=factor_id,
        branch_path=branch_path,
        sl_mult=sl_mult,
        cost_bps_side=cost_bps_side,
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    labels_path = output_dir / "labels.jsonl"
    _write_jsonl(labels_path, labels)

    payoff = payoff_report.build_payoff_shape_report(
        candidate_id=factor_id,
        trades=labels,
        nb_trials=nb_trials,
        periods_per_year=periods_per_year,
    )
    payoff_path = output_dir / "payoff_report.json"
    _write_json(payoff_path, payoff)

    purged = purged_cv.build_guard_report(
        labels=labels,
        nb_trials=nb_trials,
        embargo_bars=embargo_bars,
        fold_count=fold_count,
    )
    purged_path = output_dir / "purged_cv_guard.json"
    _write_json(purged_path, purged)

    payoff["pbo"] = purged.get("pbo")
    payoff["oos_sharpe_lcb"] = purged.get("oos_sharpe_lcb")
    payoff["purged_cv_gate"] = purged.get("purged_cv_gate")
    if purged.get("purged_cv_gate") in {"reject", "insufficient_data"}:
        payoff["promotion_gate"] = "reject"
        if "purged_cv_reject" not in payoff["failure_tags"]:
            payoff["failure_tags"].append("purged_cv_reject")
    elif purged.get("purged_cv_gate") == "probe" and payoff.get("promotion_gate") == "promote":
        payoff["promotion_gate"] = "probe"
    _write_json(payoff_path, payoff)

    target = path_target.export_targets(
        labels_jsonl=labels_path,
        payoff_report_json=payoff_path,
        output_dir=output_dir / "path_ranker_handoff",
        symbol="TOMAC_BALANCED",
        auxiliary_fields=["pair", "factor_id", "tod_factor_ids", "risk_normalization_basis"],
    )
    target_path = output_dir / "path_ranker_handoff_summary.json"
    _write_json(target_path, target)

    admission = admission_guard.validate_bundle(
        labels,
        summary=_build_admission_summary(
            exact_root=exact_root,
            trade_count=len(labels),
            terminal_row=terminal_row,
        ),
        require_trend_root=False,
        require_mtf_resonance=False,
    )
    admission_path = output_dir / "simulated_feedback_admission_guard.json"
    _write_json(admission_path, admission)

    summary = {
        "ok": True,
        "schema_version": "tomac-balanced-trade-label-sidecar/v1",
        "exact_root": str(exact_root),
        "factor_id": factor_id,
        "branch_path": branch_path,
        "sl_mult": sl_mult,
        "cost_bps_side": cost_bps_side,
        "round_trip_cost_bps": cost_bps_side * 2.0,
        "label_count": len(labels),
        "terminal_trade_count": int(terminal_row.get("trade_count") or terminal_metrics.get("trade_count", 0) or 0),
        "trade_count_parity": len(labels)
        == int(terminal_row.get("trade_count") or terminal_metrics.get("trade_count", 0) or 0),
        "gate1_survivor": bool(terminal_row.get("gate1_survivor", terminal_metrics.get("gate1_survivor", False))),
        "payoff_gate": payoff.get("promotion_gate"),
        "purged_cv_gate": purged.get("purged_cv_gate"),
        "next_recommended_layer": "transition_and_validation_still_blocked",
        "diagnostics": diagnostics,
        "artifact_paths": {
            "labels_jsonl": str(labels_path),
            "payoff_report_json": str(payoff_path),
            "purged_cv_guard_json": str(purged_path),
            "path_ranker_handoff_summary_json": str(target_path),
            "simulated_feedback_admission_guard_json": str(admission_path),
        },
    }
    summary_path = output_dir / "summary.json"
    _write_json(summary_path, summary)
    summary["artifact_paths"]["summary_json"] = str(summary_path)
    _write_json(summary_path, summary)
    return summary


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build same-root payoff sidecar artifacts from TOMAC balanced TOD exact AQ signals.")
    parser.add_argument("--exact-root", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--sl-mult", type=float, default=DEFAULT_SL_MULT)
    parser.add_argument("--cost-bps-side", type=float, default=DEFAULT_COST_BPS_SIDE)
    parser.add_argument("--nb-trials", type=int, default=1)
    parser.add_argument("--periods-per-year", type=int, default=252)
    parser.add_argument("--embargo-bars", type=int, default=1)
    parser.add_argument("--fold-count", type=int, default=4)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    summary = run_sidecar(
        exact_root=Path(args.exact_root).resolve(),
        output_dir=Path(args.output_dir).resolve(),
        sl_mult=args.sl_mult,
        cost_bps_side=args.cost_bps_side,
        nb_trials=args.nb_trials,
        periods_per_year=args.periods_per_year,
        embargo_bars=args.embargo_bars,
        fold_count=args.fold_count,
    )
    print(json.dumps(summary, indent=2, sort_keys=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
