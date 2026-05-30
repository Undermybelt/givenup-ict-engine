from __future__ import annotations

import argparse
import csv
import json
import math
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from statistics import mean
from typing import Any, Iterable


DEFAULT_THRESHOLDS = {
    "min_n": 30,
    "min_abs_t_stat": 2.0,
    "min_abs_ic_spearman": 0.03,
    "min_mean_return_after_cost_bps": 0.0,
    "min_root_delta_bps": 0.0,
}


DEMO_ROWS = [
    {
        "timestamp": f"2026-05-20T09:{i:02d}:00Z",
        "asset": "DEMO",
        "horizon": "1",
        "regime": "Transition",
        "signal": str(-1.0 if i % 2 else 1.0),
        "forward_return": str((0.0012 if i % 2 == 0 else -0.0010) + (i % 5) * 0.00001),
    }
    for i in range(40)
]


@dataclass(frozen=True)
class DiagnosticRow:
    timestamp: str
    asset: str
    horizon: str
    regime: str
    signal: float
    forward_return: float


def _safe_float(value: Any, field: str) -> float:
    try:
        out = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"invalid numeric {field}: {value!r}") from exc
    if not math.isfinite(out):
        raise ValueError(f"invalid finite {field}: {value!r}")
    return out


def _load_profile(path: str | None) -> dict[str, Any]:
    if not path:
        return {}
    with Path(path).open() as handle:
        profile = json.load(handle)
    if not isinstance(profile, dict):
        raise ValueError("profile must be a JSON object")
    return profile


def _read_rows(path: str | None, demo: bool = False) -> list[DiagnosticRow]:
    if demo:
        records = DEMO_ROWS
    elif path:
        with Path(path).open(newline="") as handle:
            records = list(csv.DictReader(handle))
    else:
        raise ValueError("pass --input or --demo")

    rows: list[DiagnosticRow] = []
    for record in records:
        rows.append(
            DiagnosticRow(
                timestamp=str(record.get("timestamp") or ""),
                asset=str(record.get("asset") or "UNKNOWN"),
                horizon=str(record.get("horizon") or "1"),
                regime=str(record.get("regime") or "root_agnostic"),
                signal=_safe_float(record.get("signal"), "signal"),
                forward_return=_safe_float(record.get("forward_return"), "forward_return"),
            )
        )
    return rows


def _branch_parts(branch_path: str | None) -> list[str]:
    return [part.strip() for part in (branch_path or "").split("->") if part.strip()]


def _timeframe_from_branch(branch_path: str | None) -> str:
    for part in _branch_parts(branch_path):
        lowered = part.lower()
        if lowered.endswith(("m", "h", "d")) and lowered[:-1].isdigit():
            return lowered
    return "1"


def _regime_from_branch(branch_path: str | None) -> str:
    parts = _branch_parts(branch_path)
    for idx, part in enumerate(parts):
        lowered = part.lower()
        if lowered.endswith(("m", "h", "d")) and lowered[:-1].isdigit():
            return parts[idx + 1] if idx + 1 < len(parts) else "root_agnostic"
    return parts[0] if parts else "root_agnostic"


def _first_present(record: dict[str, Any], keys: Iterable[str]) -> Any:
    for key in keys:
        value = record.get(key)
        if value not in (None, ""):
            return value
    return None


def _read_rank_rows_csv(path: str) -> list[DiagnosticRow]:
    rows: list[DiagnosticRow] = []
    with Path(path).open(newline="") as handle:
        for idx, record in enumerate(csv.DictReader(handle)):
            trade_count = int(float(_first_present(record, ["trade_count", "trades", "n"]) or 0))
            if trade_count <= 0:
                continue
            total_pct = _safe_float(
                _first_present(
                    record,
                    [
                        "2bps_per_side_total_profit_pct",
                        "1bps_per_side_total_profit_pct",
                        "raw_total_profit_pct",
                        "total_profit_pct",
                        "profit_total_pct",
                    ],
                ),
                "rank_rows_total_profit_pct",
            )
            branch_path = str(_first_present(record, ["branch_path", "regime_profit_branch_path"]) or "")
            per_trade_return = (total_pct / 100.0) / trade_count
            signal = 1.0 if per_trade_return >= 0 else -1.0
            forward_return = abs(per_trade_return)
            for trade_idx in range(trade_count):
                rows.append(
                    DiagnosticRow(
                        timestamp=f"rank-row:{idx}:{trade_idx}",
                        asset=str(_first_present(record, ["asset", "symbol", "label"]) or "rank_row"),
                        horizon=str(_first_present(record, ["horizon", "timeframe"]) or _timeframe_from_branch(branch_path)),
                        regime=_regime_from_branch(branch_path),
                        signal=signal,
                        forward_return=forward_return,
                    )
                )
    return rows


def _direction_to_signal(value: Any) -> float:
    text = str(value or "").lower()
    if any(token in text for token in ["short", "sell", "bear", "down"]):
        return -1.0
    return 1.0


def _return_from_trade(record: dict[str, Any]) -> float | None:
    value = _first_present(record, ["forward_return", "realized_return", "return", "return_pct"])
    if value is not None:
        out = _safe_float(value, "trade_return")
        return out / 100.0 if abs(out) > 1.0 else out
    bps = _first_present(record, ["pnl_bps", "realized_pnl_bps", "outcome_pnl_bps"])
    if bps is not None:
        return _safe_float(bps, "trade_pnl_bps") / 10_000.0
    pct = _first_present(record, ["pnl_pct", "realized_pnl_pct", "profit_pct"])
    if pct is not None:
        return _safe_float(pct, "trade_pnl_pct") / 100.0
    return None


def _read_real_trades_jsonl(path: str) -> list[DiagnosticRow]:
    rows: list[DiagnosticRow] = []
    with Path(path).open() as handle:
        for idx, line in enumerate(handle):
            if not line.strip():
                continue
            record = json.loads(line)
            feedback = record.get("structural_feedback") if isinstance(record.get("structural_feedback"), dict) else {}
            branch_path = str(
                _first_present(record, ["regime_profit_branch_path", "branch_path"])
                or feedback.get("path_id")
                or ""
            )
            forward_return = _return_from_trade(record)
            if forward_return is None:
                continue
            rows.append(
                DiagnosticRow(
                    timestamp=str(_first_present(record, ["timestamp", "opened_at", "closed_at"]) or f"real-trade:{idx}"),
                    asset=str(_first_present(record, ["asset", "symbol", "instrument"]) or "real_trade"),
                    horizon=str(_first_present(record, ["horizon", "timeframe"]) or _timeframe_from_branch(branch_path)),
                    regime=_regime_from_branch(branch_path),
                    signal=_direction_to_signal(_first_present(record, ["direction", "side", "action"])),
                    forward_return=forward_return,
                )
            )
    return rows


def _rank(values: list[float]) -> list[float]:
    indexed = sorted(enumerate(values), key=lambda item: item[1])
    ranks = [0.0] * len(values)
    i = 0
    while i < len(indexed):
        j = i + 1
        while j < len(indexed) and indexed[j][1] == indexed[i][1]:
            j += 1
        avg_rank = (i + 1 + j) / 2.0
        for k in range(i, j):
            ranks[indexed[k][0]] = avg_rank
        i = j
    return ranks


def _pearson(xs: list[float], ys: list[float]) -> float | None:
    if len(xs) < 2:
        return None
    mx = mean(xs)
    my = mean(ys)
    cov = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    vx = sum((x - mx) ** 2 for x in xs)
    vy = sum((y - my) ** 2 for y in ys)
    if vx <= 0.0 or vy <= 0.0:
        return None
    return cov / math.sqrt(vx * vy)


def _spearman(xs: list[float], ys: list[float]) -> float | None:
    if len(xs) < 2:
        return None
    return _pearson(_rank(xs), _rank(ys))


def _through_origin_beta_t(xs: list[float], ys: list[float]) -> tuple[float | None, float | None]:
    n = len(xs)
    denom = sum(x * x for x in xs)
    if n < 3 or denom <= 0.0:
        return None, None
    beta = sum(x * y for x, y in zip(xs, ys)) / denom
    residuals = [y - beta * x for x, y in zip(xs, ys)]
    sigma2 = sum(r * r for r in residuals) / (n - 1)
    if sigma2 <= 1e-24:
        return beta, math.copysign(1e12, beta if beta != 0.0 else 1.0)
    se = math.sqrt(sigma2 / denom)
    return beta, beta / se


def _signed_returns_bps(rows: Iterable[DiagnosticRow], round_trip_cost_fraction: float) -> list[float]:
    declared_return_adjustment_units = round_trip_cost_fraction * 10_000.0
    out = []
    for row in rows:
        if abs(row.signal) <= 0.0:
            continue
        direction = 1.0 if row.signal > 0.0 else -1.0
        out.append(direction * row.forward_return * 10_000.0 - declared_return_adjustment_units)
    return out


def _metrics_for(rows: list[DiagnosticRow], round_trip_cost_fraction: float) -> dict[str, Any]:
    xs = [row.signal for row in rows]
    ys = [row.forward_return for row in rows]
    beta, t_stat = _through_origin_beta_t(xs, ys)
    signed_bps = _signed_returns_bps(rows, round_trip_cost_fraction)
    return {
        "n": len(rows),
        "asset_count": len({row.asset for row in rows}),
        "beta": beta,
        "t_stat": t_stat,
        "ic_pearson": _pearson(xs, ys),
        "ic_spearman": _spearman(xs, ys),
        "mean_signed_return_bps_after_cost": mean(signed_bps) if signed_bps else None,
        "active_observations": len(signed_bps),
    }


def _passes(metrics: dict[str, Any], thresholds: dict[str, Any], root_delta_bps: float | None) -> bool:
    checks = [
        metrics.get("n", 0) >= int(thresholds["min_n"]),
        abs(metrics.get("t_stat") or 0.0) >= float(thresholds["min_abs_t_stat"]),
        abs(metrics.get("ic_spearman") or 0.0) >= float(thresholds["min_abs_ic_spearman"]),
        (metrics.get("mean_signed_return_bps_after_cost") or -math.inf)
        > float(thresholds["min_mean_return_after_cost_bps"]),
    ]
    if root_delta_bps is not None:
        checks.append(root_delta_bps > float(thresholds["min_root_delta_bps"]))
    return all(checks)


def _best_bucket_for_horizon(buckets: list[dict[str, Any]], horizon: str) -> dict[str, Any] | None:
    candidates = [bucket for bucket in buckets if bucket.get("horizon") == horizon]
    if not candidates:
        return None
    return max(
        candidates,
        key=lambda item: (
            item["candidate_passed_gate"],
            item.get("mean_signed_return_bps_after_cost") or -math.inf,
            abs(item.get("t_stat") or 0.0),
        ),
    )


def _timeframe_ladder_summary(
    buckets: list[dict[str, Any]], profile: dict[str, Any]
) -> dict[str, Any] | None:
    ladder = [str(item) for item in profile.get("timeframe_ladder", []) if str(item)]
    if not ladder:
        return None
    best_by_horizon = []
    for horizon in ladder:
        best = _best_bucket_for_horizon(buckets, horizon)
        best_by_horizon.append(
            {
                "horizon": horizon,
                "covered": best is not None,
                "best_regime": best.get("regime") if best else None,
                "n": best.get("n") if best else 0,
                "candidate_passed_gate": bool(best and best.get("candidate_passed_gate")),
                "mean_signed_return_bps_after_cost": (
                    best.get("mean_signed_return_bps_after_cost") if best else None
                ),
                "t_stat": best.get("t_stat") if best else None,
                "ic_spearman": best.get("ic_spearman") if best else None,
            }
        )
    covered = [item["horizon"] for item in best_by_horizon if item["covered"]]
    passed = [item["horizon"] for item in best_by_horizon if item["candidate_passed_gate"]]
    return {
        "schema_version": "ict-engine-timeframe-ladder-diagnostics/v1",
        "expected_ladder": ladder,
        "covered_timeframes": covered,
        "missing_timeframes": [horizon for horizon in ladder if horizon not in covered],
        "passed_timeframes": passed,
        "best_by_horizon": best_by_horizon,
        "all_expected_timeframes_covered": len(covered) == len(ladder),
        "all_expected_timeframes_passed": len(passed) == len(ladder),
    }


def build_diagnostics(
    rows: list[DiagnosticRow],
    *,
    round_trip_cost_fraction: float = 0.0,
    profile: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if round_trip_cost_fraction < 0:
        raise ValueError("round_trip_cost_fraction must be >= 0")
    profile = profile or {}
    thresholds = {**DEFAULT_THRESHOLDS, **(profile.get("thresholds") or {})}
    root_regime = profile.get("root_regime")
    branch_path = profile.get("regime_profit_branch_path")

    by_key: dict[tuple[str, str], list[DiagnosticRow]] = defaultdict(list)
    for row in rows:
        by_key[(row.horizon, row.regime)].append(row)

    buckets = []
    for (horizon, regime), bucket_rows in sorted(by_key.items()):
        metrics = _metrics_for(bucket_rows, round_trip_cost_fraction)
        outside_rows = [row for row in rows if row.horizon == horizon and row.regime != regime]
        outside_mean = None
        root_delta_bps = None
        if outside_rows:
            outside_metrics = _metrics_for(outside_rows, round_trip_cost_fraction)
            outside_mean = outside_metrics["mean_signed_return_bps_after_cost"]
            if metrics["mean_signed_return_bps_after_cost"] is not None and outside_mean is not None:
                root_delta_bps = metrics["mean_signed_return_bps_after_cost"] - outside_mean
        buckets.append(
            {
                "horizon": horizon,
                "regime": regime,
                **metrics,
                "outside_regime_mean_signed_return_bps_after_cost": outside_mean,
                "root_delta_bps": root_delta_bps,
                "candidate_passed_gate": _passes(metrics, thresholds, root_delta_bps if root_regime else None),
            }
        )

    best = max(
        buckets,
        key=lambda item: (
            item["candidate_passed_gate"],
            item.get("mean_signed_return_bps_after_cost") or -math.inf,
            abs(item.get("t_stat") or 0.0),
        ),
        default=None,
    )
    ladder_summary = _timeframe_ladder_summary(buckets, profile)
    return {
        "schema_version": "ict-engine-factor-signal-diagnostics/v1",
        "source_inspiration": "QuantInvestStrats/qis.perfstats.signal_diagnostics",
        "hotplug_profile_used": bool(profile),
        "root_regime": root_regime,
        "regime_profit_branch_path": branch_path,
        "round_trip_cost_fraction": round_trip_cost_fraction,
        "declared_cost_role": "caller_supplied_fraction_not_fixed_bps_gate_authority",
        "thresholds": thresholds,
        "rows": len(rows),
        "bucket_count": len(buckets),
        "buckets": buckets,
        "timeframe_ladder_summary": ladder_summary,
        "best_bucket": best,
        "diagnostic_candidate_passed_gate": bool(best and best["candidate_passed_gate"]),
        "requires_downstream_live_gates": True,
        "diagnostic_reason": "diagnostic_only_hotplug; downstream Pre-Bayes/BBN/CatBoost/execution-tree gates still required",
    }


def _compact_line(report: dict[str, Any]) -> str:
    best = report.get("best_bucket") or {}
    return (
        f"factor_signal_diagnostics rows={report['rows']} buckets={report['bucket_count']} "
        f"best={best.get('regime','none')}/{best.get('horizon','none')} "
        f"n={best.get('n',0)} t={best.get('t_stat')} ic_s={best.get('ic_spearman')} "
        f"mean_signed_return_bps_after_cost={best.get('mean_signed_return_bps_after_cost')} "
        f"diagnostic_candidate_passed_gate={str(report['diagnostic_candidate_passed_gate']).lower()} "
        "requires_downstream_live_gates=true"
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Zero-config factor signal diagnostics")
    parser.add_argument("--input", help="CSV with timestamp,asset,horizon,regime,signal,forward_return")
    parser.add_argument("--rank-rows-csv", help="Optional Auto-Quant rank_rows.csv aggregate input")
    parser.add_argument("--real-trades-jsonl", help="Optional real/simulated trade JSONL input")
    parser.add_argument("--profile", help="Optional hotplug profile JSON")
    parser.add_argument("--demo", action="store_true", help="Run bundled zero-config demo rows")
    parser.add_argument("--round-trip-cost-fraction", type=float, default=0.0)
    parser.add_argument("--output", help="Optional JSON report path; stdout remains compact unless --json")
    parser.add_argument("--json", action="store_true", help="Print full JSON report")
    parser.add_argument("--compact", action="store_true", help="Print one token-friendly line")
    args = parser.parse_args(argv)

    profile = _load_profile(args.profile)
    input_modes = [bool(args.input), bool(args.rank_rows_csv), bool(args.real_trades_jsonl), bool(args.demo)]
    if sum(input_modes) != 1:
        raise ValueError("choose exactly one of --input, --rank-rows-csv, --real-trades-jsonl, or --demo")
    if args.rank_rows_csv:
        rows = _read_rank_rows_csv(args.rank_rows_csv)
    elif args.real_trades_jsonl:
        rows = _read_real_trades_jsonl(args.real_trades_jsonl)
    else:
        rows = _read_rows(args.input, args.demo)
    report = build_diagnostics(rows, round_trip_cost_fraction=args.round_trip_cost_fraction, profile=profile)

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(_compact_line(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
