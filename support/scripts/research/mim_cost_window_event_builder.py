from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Iterable

try:
    from .mim_cost_window_features import Bar, mim_cost_window_features, read_bars, triple_barrier_label
except ImportError:  # pragma: no cover - exercised by direct script execution.
    from mim_cost_window_features import Bar, mim_cost_window_features, read_bars, triple_barrier_label

CONTEXT_TIMEFRAMES = ["5m", "15m", "30m", "1h", "4h", "1d"]
EVENT_ENTRY_INDEX = 29


def build_event_rows(
    input_csv: Path,
    *,
    symbol: str,
    provider: str,
    market: str,
    product: str,
    branch_path: str,
) -> list[dict[str, object]]:
    sessions = _group_by_session(read_bars(Path(input_csv)))
    branch_parts = _branch_parts(branch_path)
    events: list[dict[str, object]] = []
    for session_date in sorted(sessions):
        bars = sessions[session_date]
        if len(bars) < 62:
            continue
        features = mim_cost_window_features(bars)
        side = 1 if features.eligible_long else 0
        label = triple_barrier_label(bars, EVENT_ENTRY_INDEX) if side == 1 else 0
        row: dict[str, object] = {
            "event_date": session_date,
            "event_ts": bars[EVENT_ENTRY_INDEX].ts.isoformat(),
            "symbol": symbol,
            "provider": provider,
            "market": market,
            "product": product,
            "base_timeframe": "1m",
            "context_timeframes": list(CONTEXT_TIMEFRAMES),
            "branch_path": branch_path,
            "main_regime": branch_parts[0] if branch_parts else "",
            "sub_regime": branch_parts[1] if len(branch_parts) > 1 else "",
            "profit_factor": branch_parts[-1] if branch_parts else "",
            "side": side,
            "triple_barrier_label": label,
            "promotion_allowed": False,
            "trade_usable": False,
            "downstream_allowed": False,
        }
        row.update(
            {
                "first_window_return": features.first_window_return,
                "late_window_return": features.late_window_return,
                "first_window_realized_variance": features.first_window_realized_variance,
                "first_window_amihud": features.first_window_amihud,
                "corwin_schultz_spread": features.corwin_schultz_spread,
                "basic_high_low_spread": features.basic_high_low_spread,
                "rvol": features.rvol,
                "momentum_state_prob": features.momentum_state_prob,
                "posterior_entropy_proxy": features.posterior_entropy_proxy,
                "eligible_long": features.eligible_long,
            }
        )
        events.append(row)
    return events


def write_jsonl(path: Path, rows: Iterable[dict[str, object]]) -> None:
    with Path(path).open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def build_summary(rows: list[dict[str, object]]) -> dict[str, object]:
    return {
        "event_count": len(rows),
        "eligible_long_count": sum(1 for row in rows if row.get("side") == 1),
        "promotion_allowed": False,
        "trade_usable": False,
        "downstream_allowed": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build MIM cost-window event rows from retained 1m OHLCV.")
    parser.add_argument("--input-csv", required=True, type=Path)
    parser.add_argument("--output-jsonl", required=True, type=Path)
    parser.add_argument("--summary-json", required=True, type=Path)
    parser.add_argument("--symbol", required=True)
    parser.add_argument("--provider", required=True)
    parser.add_argument("--market", required=True)
    parser.add_argument("--product", required=True)
    parser.add_argument("--branch-path", required=True)
    args = parser.parse_args(argv)

    events = build_event_rows(
        args.input_csv,
        symbol=args.symbol,
        provider=args.provider,
        market=args.market,
        product=args.product,
        branch_path=args.branch_path,
    )
    args.output_jsonl.parent.mkdir(parents=True, exist_ok=True)
    args.summary_json.parent.mkdir(parents=True, exist_ok=True)
    write_jsonl(args.output_jsonl, events)
    args.summary_json.write_text(json.dumps(build_summary(events), sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return 0


def _group_by_session(bars: Iterable[Bar]) -> dict[str, list[Bar]]:
    grouped: dict[str, list[Bar]] = defaultdict(list)
    for bar in bars:
        grouped[bar.ts.date().isoformat()].append(bar)
    return {key: sorted(value, key=lambda item: item.ts) for key, value in grouped.items()}


def _branch_parts(branch_path: str) -> list[str]:
    return [part.strip() for part in branch_path.split("->") if part.strip()]


if __name__ == "__main__":
    raise SystemExit(main())
