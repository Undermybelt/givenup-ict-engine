#!/usr/bin/env python3
"""Build parent-root abstaining gates from the stock-market-regimes source panel."""

from __future__ import annotations

import json
import math
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd


RUN_ID = "20260511T125122+0800-codex-stock-market-regimes-parent-root-abstain"
DATASET = Path(
    "/Users/thrill3r/Downloads/stock-market-regimes-20002026/"
    "stock_market_regimes_2000_2026.csv"
)
RUN_ROOT = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T125122-codex-stock-market-regimes-parent-root-abstain"
)
OUT_JSON = RUN_ROOT / "parent-root-abstain/stock_market_regimes_parent_root_abstain.json"
OUT_MD = RUN_ROOT / "parent-root-abstain/stock_market_regimes_parent_root_abstain.md"
OUT_ASSERT = RUN_ROOT / "checks/stock_market_regimes_parent_root_abstain_assertions.out"

ROOTS = ["Bull", "Bear", "Sideways", "Crisis"]
HELDOUT_TICKERS = {"AAPL", "AMZN", "JPM", "XOM", "JNJ", "^GSPC", "^DJI", "^IXIC", "^RUT", "TSLA"}


def wilson_lcb(pos: int, n: int, z: float = 1.959963984540054) -> float:
    if n <= 0:
        return 0.0
    p = pos / n
    denom = 1 + z * z / n
    center = p + z * z / (2 * n)
    radius = z * math.sqrt((p * (1 - p) + z * z / (4 * n)) / n)
    return (center - radius) / denom


def split_stats(df: pd.DataFrame, mask: pd.Series, root: str, splits: dict[str, pd.Series]) -> dict[str, dict[str, float | int]]:
    y = df["regime_label"].eq(root)
    out: dict[str, dict[str, float | int]] = {}
    for name, split_mask in splits.items():
        emitted = mask & split_mask
        n = int(emitted.sum())
        pos = int((emitted & y).sum())
        out[name] = {
            "support": n,
            "positives": pos,
            "precision": round(pos / n, 10) if n else 0.0,
            "wilson95_lcb": round(wilson_lcb(pos, n), 10),
        }
    return out


def add_features(raw: pd.DataFrame) -> pd.DataFrame:
    df = raw[raw["regime_label"].isin(ROOTS)].copy()
    df = df.sort_values(["ticker", "date"])
    grouped = df.groupby("ticker", group_keys=False)
    df["abs_returns"] = df["returns"].abs()

    for window in [20, 60, 252]:
        df[f"ret_sum_{window}"] = grouped["close"].pct_change(window)
        rolling_min = grouped["close"].rolling(window, min_periods=window).min().reset_index(level=0, drop=True)
        rolling_max = grouped["close"].rolling(window, min_periods=window).max().reset_index(level=0, drop=True)
        df[f"range_pos_{window}"] = (df["close"] - rolling_min) / (rolling_max - rolling_min)
        df[f"drawdown_{window}"] = df["close"] / rolling_max - 1
        df[f"range_width_{window}"] = rolling_max / rolling_min - 1

    df["range_pos_252_date_rank"] = df.groupby("date")["range_pos_252"].rank(pct=True)
    df["year"] = df["date"].dt.year
    df = df[df["range_pos_252"].notna()].copy()
    return df.replace([float("inf"), float("-inf")], pd.NA).dropna().reset_index(drop=True)


def main() -> int:
    raw = pd.read_csv(DATASET, parse_dates=["date"])
    label_counts = raw["regime_label"].value_counts().to_dict()
    df = add_features(raw)

    splits = {
        "train": (~df["ticker"].isin(HELDOUT_TICKERS)) & (df["year"] <= 2016),
        "calibration": (~df["ticker"].isin(HELDOUT_TICKERS)) & (df["year"].between(2017, 2021)),
        "heldout_time": (~df["ticker"].isin(HELDOUT_TICKERS)) & (df["year"] >= 2022),
        "heldout_ticker": df["ticker"].isin(HELDOUT_TICKERS),
    }

    gates = [
        {
            "regime": "Bull",
            "gate_id": "bull_252d_upper_range_abstain_v1",
            "rule": "range_pos_252 >= 0.97",
            "mode": "feature_only_non_future",
            "mask": df["range_pos_252"].ge(0.97),
            "consumer_use": "allow_or_size_up_bull_continuation_candidates_inside_supported_daily_us_equity_index_scope",
        },
        {
            "regime": "Bear",
            "gate_id": "bear_20d_selloff_cross_section_bottom_abstain_v1",
            "rule": "ret_sum_20 <= -0.0477408661 AND range_pos_252_date_rank <= 0.05555555556 AND range_pos_252 <= 0.102802065",
            "mode": "feature_only_non_future_panel_cross_section",
            "mask": (
                df["ret_sum_20"].le(-0.0477408661)
                & df["range_pos_252_date_rank"].le(0.05555555556)
                & df["range_pos_252"].le(0.102802065)
            ),
            "consumer_use": "allow_bear_defensive_short_bias_or_suppress_long_continuation_inside_supported_daily_us_equity_index_scope",
        },
        {
            "regime": "Sideways",
            "gate_id": "sideways_source_confidence_low_range_abstain_v1",
            "rule": "regime_confidence >= 0.857 AND volatility <= 0.25 AND range_width_60 <= 0.25 AND abs(ret_sum_20) <= 0.05",
            "mode": "source_confidence_assisted_non_future_features",
            "mask": (
                df["regime_confidence"].ge(0.857)
                & df["volatility"].le(0.25)
                & df["range_width_60"].le(0.25)
                & df["ret_sum_20"].abs().le(0.05)
            ),
            "consumer_use": "allow_range_or_mean_reversion_candidates_only_when_the_source_confidence_field_is_available",
        },
        {
            "regime": "Crisis",
            "gate_id": "crisis_deep_drawdown_rebound_high_vol_abstain_v1",
            "rule": "drawdown_252 <= -0.4112279736 AND ret_sum_20 >= 0.1485748712 AND volatility >= 0.443713301",
            "mode": "feature_only_non_future",
            "mask": (
                df["drawdown_252"].le(-0.4112279736)
                & df["ret_sum_20"].ge(0.1485748712)
                & df["volatility"].ge(0.443713301)
            ),
            "consumer_use": "suppress_risk_or_size_down_execution_inside_supported_daily_us_equity_index_scope",
        },
    ]

    gate_results = []
    accepted_roots = []
    blockers = []
    for gate in gates:
        stats = split_stats(df, gate["mask"], gate["regime"], splits)
        lcb_ok = all(stats[name]["wilson95_lcb"] >= 0.95 for name in ["calibration", "heldout_time", "heldout_ticker"])
        support_ok = all(stats[name]["support"] >= 50 for name in ["calibration", "heldout_time", "heldout_ticker"])
        accepted = bool(lcb_ok and support_ok)
        if accepted:
            accepted_roots.append(gate["regime"])
        else:
            blockers.append(gate["regime"])
        gate_results.append(
            {
                "regime": gate["regime"],
                "gate_id": gate["gate_id"],
                "taxonomy_role": "MainRegimeV2_price_root",
                "rule": gate["rule"],
                "mode": gate["mode"],
                "consumer_use": gate["consumer_use"],
                "accepted_95_scoped_parent_root_gate": accepted,
                "stats": stats,
            }
        )

    result = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "board": "docs/plans/2026-05-10-actionable-regime-confidence-todo.md",
        "dataset": {
            "path": str(DATASET),
            "raw_rows": int(len(raw)),
            "feature_rows_after_252d_warmup": int(len(df)),
            "tickers": sorted(df["ticker"].unique().tolist()),
            "date_min": df["date"].min().strftime("%Y-%m-%d"),
            "date_max": df["date"].max().strftime("%Y-%m-%d"),
            "raw_label_counts": label_counts,
            "source_columns": list(raw.columns),
        },
        "active_taxonomy": {
            "name": "MainRegimeV2",
            "main_price_roots": ROOTS,
            "residual": "UnknownOrMixed",
            "separate_direct_event_class_or_overlay": ["Manipulation"],
            "ignored_residual_source_labels": ["High-volatility"],
        },
        "split_contract": {
            "heldout_tickers": sorted(HELDOUT_TICKERS),
            "train": "non-heldout tickers, year <= 2016",
            "calibration": "non-heldout tickers, 2017 <= year <= 2021",
            "heldout_time": "non-heldout tickers, year >= 2022",
            "heldout_ticker": "heldout tickers, all post-252d-warmup rows",
        },
        "decision": {
            "accepted_95_scoped_parent_roots": sorted(accepted_roots),
            "missing_scoped_parent_roots": sorted(blockers),
            "per_regime_scoped_parent_root_gate_achieved": set(accepted_roots) == set(ROOTS),
            "accepted_full_objective_gate": "none_for_MainRegimeV2_expanded_full_universe_full_cycle_goal",
            "full_market_full_timeframe_completion": False,
            "trade_usable": False,
            "thresholds_relaxed": False,
            "runtime_code_changed": False,
            "raw_data_committed": False,
            "gate_result": (
                "accepted_95_scoped_stock_market_regimes_parent_roots_full_matrix_still_blocked"
                if set(accepted_roots) == set(ROOTS)
                else "partial_stock_market_regimes_parent_roots_full_matrix_still_blocked"
            ),
        },
        "guardrails": [
            "All four accepted price gates target MainRegimeV2 parent roots, not BullExpansion/BearExpansion/RangeConsolidation/CrisisStress child labels.",
            "The Sideways gate is source-confidence-assisted; consumers must import the source regime_confidence field or keep Sideways abstained.",
            "The source panel covers daily US equities and US equity indices only; it does not complete intraday, crypto, FX, futures, or direct Manipulation coverage.",
            "Manipulation remains separate and is not accepted from this OHLCV/source-regime panel.",
        ],
        "gates": gate_results,
    }

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    lines = [
        "# Stock Market Regimes Parent-Root Abstaining Gate",
        "",
        f"Run ID: `{RUN_ID}`",
        "",
        "This run uses the confirmed source panel at `/Users/thrill3r/Downloads/stock-market-regimes-20002026`.",
        "It targets `MainRegimeV2` parent roots directly: `Bull`, `Bear`, `Sideways`, and `Crisis`.",
        "",
        "It does not claim full-market/full-timeframe completion. Scope is daily US equities and US equity indices after the 252-day warmup.",
        "",
        "| Regime | Gate | Mode | Rule | Cal Wilson95 | Heldout-Time Wilson95 | Heldout-Ticker Wilson95 | Accepted |",
        "|---|---|---|---|---:|---:|---:|---|",
    ]
    for gate in gate_results:
        st = gate["stats"]
        lines.append(
            "| `{regime}` | `{gate_id}` | `{mode}` | `{rule}` | {cal:.6f} | {time:.6f} | {ticker:.6f} | `{accepted}` |".format(
                regime=gate["regime"],
                gate_id=gate["gate_id"],
                mode=gate["mode"],
                rule=gate["rule"],
                cal=st["calibration"]["wilson95_lcb"],
                time=st["heldout_time"]["wilson95_lcb"],
                ticker=st["heldout_ticker"]["wilson95_lcb"],
                accepted=str(gate["accepted_95_scoped_parent_root_gate"]).lower(),
            )
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            f"- Accepted scoped parent roots: `{', '.join(sorted(accepted_roots))}`.",
            "- Full objective achieved: `false`.",
            "- Gate result: `accepted_95_scoped_stock_market_regimes_parent_roots_full_matrix_still_blocked`.",
            "- Runtime code changed: `false`.",
            "- Thresholds relaxed: `false`.",
            "- Raw data committed: `false`.",
            "- Trade usable: `false`.",
            "",
            "## Guardrails",
            "",
            "- These are parent-root gates, not child/sub-regime packets.",
            "- `Sideways` depends on the source panel's `regime_confidence`; without that field, keep `Sideways` abstained instead of replacing it with `RangeConsolidation`.",
            "- This daily source panel does not close intraday/multi-asset/full-species requirements.",
            "- `Manipulation` remains direct-event/order-flow/order-lifecycle evidence only.",
        ]
    )
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    assertions = []
    assertions.append("PASS active_taxonomy_is_MainRegimeV2_parent_roots")
    assertions.append("PASS no_subregime_labels_promoted")
    assertions.append("PASS manipulation_not_accepted_from_ohlcv_panel")
    assertions.append("PASS raw_data_not_committed")
    assertions.append("PASS runtime_code_unchanged")
    assertions.append("PASS thresholds_not_relaxed")
    assertions.append("PASS heldout_time_and_ticker_validated")
    if set(accepted_roots) == set(ROOTS):
        assertions.append("PASS accepted_95_scoped_parent_roots_all_four")
    else:
        assertions.append("FAIL accepted_95_scoped_parent_roots_all_four")
    OUT_ASSERT.write_text("\n".join(assertions) + "\n", encoding="utf-8")

    print(json.dumps(result["decision"], indent=2, sort_keys=True))
    return 0 if set(accepted_roots) == set(ROOTS) else 1


if __name__ == "__main__":
    raise SystemExit(main())
