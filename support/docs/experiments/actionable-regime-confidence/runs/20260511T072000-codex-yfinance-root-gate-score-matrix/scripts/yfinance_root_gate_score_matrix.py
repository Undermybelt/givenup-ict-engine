#!/usr/bin/env python3
"""Score accepted root gate expressions over the yfinance full matrix.

This is an applicability/coverage pass. It does not promote a full-cycle /
full-universe confidence gate because the fetched close matrix does not carry
source labels for every symbol/timeframe cell.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


REPO = Path("/Users/thrill3r/projects-ict-engine/ict-engine")
RUN_ID = "20260511T072000+0800-codex-yfinance-root-gate-score-matrix"
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T072000-codex-yfinance-root-gate-score-matrix"
OUT_DIR = RUN_ROOT / "score-matrix"
CHECK_DIR = RUN_ROOT / "checks"

FETCH_MATRIX = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T070440-codex-provider-universe-manifest-readback/yfinance-full-matrix/yfinance_full_universe_fetch_matrix.json"
RAW_ROOT = Path("/private/tmp/ict-regime-yfinance-full-matrix-20260511T070549")

TIMEFRAMES = ["1m", "5m", "15m", "30m", "1h", "4h", "1d", "1w", "1mo"]
SOURCE_TIMEFRAME = {
    "1m": "1m",
    "5m": "5m",
    "15m": "15m",
    "30m": "30m",
    "1h": "1h",
    "4h": "1h",
    "1d": "1d",
    "1w": "1w",
    "1mo": "1mo",
}


def rel(path: Path) -> str:
    return str(path.relative_to(REPO))


def load_json(path: Path) -> Any:
    with path.open() as handle:
        return json.load(handle)


def close_file(timeframe: str) -> Path:
    return RAW_ROOT / f"close_{SOURCE_TIMEFRAME[timeframe]}.csv"


def load_close(timeframe: str) -> pd.DataFrame:
    path = close_file(timeframe)
    df = pd.read_csv(path, index_col=0, parse_dates=True)
    df = df.apply(pd.to_numeric, errors="coerce")
    if timeframe == "4h":
        # The fetch matrix defines 4h as derived from 1h summary. Use the same
        # close-only source and resample by last close for score coverage.
        return df.resample("4h").last().dropna(how="all")
    return df


def annualizer(timeframe: str) -> float:
    if timeframe == "1m":
        return 252 * 390
    if timeframe == "5m":
        return 252 * 78
    if timeframe == "15m":
        return 252 * 26
    if timeframe == "30m":
        return 252 * 13
    if timeframe in {"1h", "4h"}:
        return 252 * 6.5
    if timeframe == "1d":
        return 252
    if timeframe == "1w":
        return 52
    return 12


def safe_series(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce").replace([np.inf, -np.inf], np.nan)


def score_symbol(series: pd.Series, timeframe: str) -> dict[str, Any]:
    close = safe_series(series).dropna()
    if len(close) < 160:
        return {
            "bars": int(len(close)),
            "status": "insufficient_rows",
            "root_hits": {},
        }
    ret1 = close.pct_change()
    roll60 = close.rolling(60)
    roll128 = close.rolling(128)
    close_drawdown60 = close / roll60.max() - 1.0
    volatility = ret1.rolling(20).std() * float(np.sqrt(annualizer(timeframe)))
    ret60 = close.pct_change(60)
    ret120 = close.pct_change(120)
    drawdown120 = close / close.rolling(120).max() - 1.0
    range60 = (roll60.max() - roll60.min()) / roll60.mean()
    range32 = (close.rolling(32).max() - close.rolling(32).min()) / close.rolling(32).mean()
    range128 = (roll128.max() - roll128.min()) / roll128.mean()

    # Accepted gate expressions, adapted to the close-only ready-provider matrix.
    bull = (close_drawdown60 >= -0.0032047199531) & (volatility <= 0.152179344579)
    bear_drawdown_ratio = -drawdown120 / 0.20
    bear_return_ratio = -ret60 / 0.04
    bear = (bear_drawdown_ratio >= 1.0) & (bear_return_ratio >= 1.0)
    sideways_abs_return_ratio = ret60.abs() / 0.04
    sideways_range_ratio = range60 / 0.18
    sideways = (sideways_abs_return_ratio <= 0.505204858191) & (sideways_range_ratio <= 0.357222193236)
    crisis = (range32 / range128) >= 1.43116959912

    gates = {
        "Bull": bull,
        "Bear": bear,
        "Sideways": sideways,
        "Crisis": crisis,
    }
    valid = pd.concat([close, close_drawdown60, volatility, ret60, ret120, drawdown120, range60, range32, range128], axis=1).dropna().index
    out: dict[str, Any] = {}
    for root, mask in gates.items():
        mask = mask.reindex(valid).fillna(False)
        out[root] = {
            "candidate_rows": int(mask.sum()),
            "evaluated_rows": int(len(valid)),
            "candidate_coverage": float(mask.mean()) if len(valid) else 0.0,
        }
    return {
        "bars": int(len(close)),
        "status": "scored",
        "first_ts": str(close.index.min()),
        "last_ts": str(close.index.max()),
        "root_hits": out,
    }


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)
    fetch_matrix = load_json(FETCH_MATRIX)
    symbols = fetch_matrix["symbols"]

    rows: list[dict[str, Any]] = []
    for timeframe in TIMEFRAMES:
        close = load_close(timeframe)
        for symbol in symbols:
            if symbol not in close.columns:
                rows.append(
                    {
                        "symbol": symbol,
                        "timeframe": timeframe,
                        "status": "missing_symbol_column",
                        "bars": 0,
                        "root_hits": {},
                    }
                )
                continue
            score = score_symbol(close[symbol], timeframe)
            rows.append({"symbol": symbol, "timeframe": timeframe, **score})

    root_summary: dict[str, dict[str, Any]] = {}
    for root in ["Bull", "Bear", "Sideways", "Crisis"]:
        scored_cells = [row for row in rows if row["status"] == "scored" and root in row["root_hits"]]
        hit_cells = [row for row in scored_cells if row["root_hits"][root]["candidate_rows"] > 0]
        root_summary[root] = {
            "scored_cells": len(scored_cells),
            "hit_cells": len(hit_cells),
            "total_candidate_rows": int(sum(row["root_hits"][root]["candidate_rows"] for row in scored_cells)),
            "timeframes_with_hits": sorted({row["timeframe"] for row in hit_cells}, key=TIMEFRAMES.index),
            "symbols_with_hits": sorted({row["symbol"] for row in hit_cells}),
        }

    report = {
        "run_id": RUN_ID,
        "goal_achieved": False,
        "objective": "Score accepted MainRegimeV2 root gate expressions over the yfinance full species/cycle matrix.",
        "source_artifacts": {
            "fetch_matrix": rel(FETCH_MATRIX),
            "raw_close_root": str(RAW_ROOT),
        },
        "raw_ohlcv_committed": False,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "trade_usable": False,
        "score_rows": rows,
        "root_summary": root_summary,
        "completion_accounting": {
            "full_matrix_scored": True,
            "accepted_full_cycle_full_universe": False,
            "why_not_accepted": [
                "This is close-only rule/gate scoring, not source-labeled calibration.",
                "No per-cell calibration/test Wilson95 can be computed without root labels for every symbol/timeframe.",
                "Crisis scoring uses close-range proxy coverage only; it is not the original high/low feature table.",
                "Manipulation is not an OHLCV bar root and must remain in direct-event variety lanes.",
            ],
        },
        "next_action": "Build labeled calibration panels for the ready yfinance cells or mark cells unsupported; separately enumerate accepted/blocked direct Manipulation varieties.",
        "artifacts": {
            "score_json": rel(OUT_DIR / "yfinance_root_gate_score_matrix.json"),
            "score_md": rel(OUT_DIR / "yfinance_root_gate_score_matrix.md"),
            "assertions": rel(CHECK_DIR / "yfinance_root_gate_score_matrix_assertions.out"),
            "script": rel(Path(__file__)),
        },
    }

    (OUT_DIR / "yfinance_root_gate_score_matrix.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")

    lines = [
        "# YFinance Root Gate Score Matrix",
        "",
        f"Run id: `{RUN_ID}`",
        "",
        "Goal achieved: `false`",
        "",
        "## Summary",
        "",
        "| Root | Scored Cells | Hit Cells | Candidate Rows | Timeframes With Hits | Symbols With Hits |",
        "|---|---:|---:|---:|---|---:|",
    ]
    for root, item in root_summary.items():
        lines.append(
            f"| `{root}` | {item['scored_cells']} | {item['hit_cells']} | {item['total_candidate_rows']} | "
            f"`{', '.join(item['timeframes_with_hits'])}` | {len(item['symbols_with_hits'])} |"
        )
    lines.extend(
        [
            "",
            "## Accounting",
            "",
            "- This is close-only rule/gate scoring over the yfinance full matrix.",
            "- It does not claim accepted 95% confidence because source labels are absent for every symbol/timeframe cell.",
            "- Runtime code changed: false. Thresholds relaxed: false. Trade usable: false.",
            "",
            "Gate result: `yfinance_full_matrix_root_gate_scored_confidence_pending`",
        ]
    )
    (OUT_DIR / "yfinance_root_gate_score_matrix.md").write_text("\n".join(lines) + "\n")

    assertion_lines = [
        "goal_achieved=false",
        "full_matrix_scored=true",
        "accepted_full_cycle_full_universe=false",
    ]
    for root, item in root_summary.items():
        assertion_lines.append(f"{root}.scored_cells={item['scored_cells']}")
        assertion_lines.append(f"{root}.hit_cells={item['hit_cells']}")
        assertion_lines.append(f"{root}.candidate_rows={item['total_candidate_rows']}")
    assertion_lines.extend(
        [
            "raw_ohlcv_committed=false",
            "runtime_code_changed=false",
            "thresholds_relaxed=false",
            "trade_usable=false",
        ]
    )
    (CHECK_DIR / "yfinance_root_gate_score_matrix_assertions.out").write_text("\n".join(assertion_lines) + "\n")
    print("\n".join(assertion_lines))


if __name__ == "__main__":
    main()
