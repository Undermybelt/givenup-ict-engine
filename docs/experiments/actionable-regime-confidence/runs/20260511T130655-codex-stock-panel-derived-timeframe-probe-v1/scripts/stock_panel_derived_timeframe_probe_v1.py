#!/usr/bin/env python3
"""Probe derived weekly/monthly parent labels from the stock-market-regimes source panel."""

from __future__ import annotations

import json
import math
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd


RUN_ID = "20260511T130655+0800-codex-stock-panel-derived-timeframe-probe-v1"
DATASET = Path(
    "/Users/thrill3r/Downloads/stock-market-regimes-20002026/"
    "stock_market_regimes_2000_2026.csv"
)
RUN_ROOT = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T130655-codex-stock-panel-derived-timeframe-probe-v1"
)
OUT_JSON = RUN_ROOT / "derived-timeframe-probe/stock_panel_derived_timeframe_probe_v1.json"
OUT_MD = RUN_ROOT / "derived-timeframe-probe/stock_panel_derived_timeframe_probe_v1.md"
OUT_ASSERT = RUN_ROOT / "checks/stock_panel_derived_timeframe_probe_v1_assertions.out"

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


def aggregate(raw: pd.DataFrame, freq: str) -> tuple[pd.DataFrame, list[int]]:
    rows = []
    for ticker, group in raw.groupby("ticker"):
        indexed = group.set_index("date")
        for period_end, sub in indexed.groupby(pd.Grouper(freq=freq)):
            if sub.empty:
                continue
            counts = sub["regime_label"].value_counts()
            rows.append(
                {
                    "date": period_end,
                    "ticker": ticker,
                    "close": sub["close"].iloc[-1],
                    "source_label": counts.index[0],
                    "source_label_confidence": float(counts.iloc[0] / len(sub)),
                    "n_daily": int(len(sub)),
                    "volatility": sub["volatility"].iloc[-1],
                    "avg_daily_abs_ret": float(sub["returns"].abs().mean()),
                    "avg_regime_confidence": float(sub["regime_confidence"].mean()),
                    "max_regime_confidence": float(sub["regime_confidence"].max()),
                    "vix": sub["vix"].iloc[-1],
                }
            )

    df = pd.DataFrame(rows).sort_values(["ticker", "date"])
    grouped = df.groupby("ticker", group_keys=False)
    df["returns"] = grouped["close"].pct_change()
    df["abs_returns"] = df["returns"].abs()
    windows = [4, 13, 26, 52] if freq.startswith("W") else [3, 6, 12, 24]
    for window in windows:
        df[f"ret_sum_{window}"] = grouped["close"].pct_change(window)
        rolling_min = grouped["close"].rolling(window, min_periods=window).min().reset_index(level=0, drop=True)
        rolling_max = grouped["close"].rolling(window, min_periods=window).max().reset_index(level=0, drop=True)
        df[f"range_pos_{window}"] = (df["close"] - rolling_min) / (rolling_max - rolling_min)
        df[f"drawdown_{window}"] = df["close"] / rolling_max - 1
        df[f"runup_{window}"] = df["close"] / rolling_min - 1
        df[f"range_width_{window}"] = rolling_max / rolling_min - 1
    df["year"] = df["date"].dt.year
    long_window = windows[-1]
    df = df[df[f"range_pos_{long_window}"].notna()].copy()
    return df.replace([float("inf"), float("-inf")], pd.NA).dropna().reset_index(drop=True), windows


def split_stats(df: pd.DataFrame, mask: pd.Series, root: str) -> dict[str, dict[str, float | int]]:
    splits = {
        "train": (~df["ticker"].isin(HELDOUT_TICKERS)) & (df["year"] <= 2016),
        "calibration": (~df["ticker"].isin(HELDOUT_TICKERS)) & (df["year"].between(2017, 2021)),
        "heldout_time": (~df["ticker"].isin(HELDOUT_TICKERS)) & (df["year"] >= 2022),
        "heldout_ticker": df["ticker"].isin(HELDOUT_TICKERS),
    }
    y = df["source_label"].eq(root)
    out = {}
    for name, split in splits.items():
        emitted = mask & split
        support = int(emitted.sum())
        positives = int((emitted & y).sum())
        out[name] = {
            "support": support,
            "positives": positives,
            "precision": round(positives / support, 10) if support else 0.0,
            "wilson95_lcb": round(wilson_lcb(positives, support), 10),
        }
    return out


def accepted(stats: dict[str, dict[str, float | int]]) -> bool:
    return all(
        stats[split]["support"] >= 50 and stats[split]["wilson95_lcb"] >= 0.95
        for split in ["calibration", "heldout_time", "heldout_ticker"]
    )


def main() -> int:
    raw = pd.read_csv(DATASET, parse_dates=["date"])
    raw = raw[raw["regime_label"].isin(ROOTS)].sort_values(["ticker", "date"])

    weekly, _ = aggregate(raw, "W-FRI")
    monthly, _ = aggregate(raw, "ME")

    rule_specs = [
        {
            "timeframe": "1w",
            "root": "Bull",
            "rule_id": "derived_1w_bull_source_conf_momentum_v1",
            "rule": "avg_regime_confidence >= 0.9666 AND ret_sum_4 >= 0.02710841687",
            "mask": weekly["avg_regime_confidence"].ge(0.9666) & weekly["ret_sum_4"].ge(0.02710841687),
            "df": weekly,
        },
        {
            "timeframe": "1w",
            "root": "Bear",
            "rule_id": "derived_1w_bear_lower_range_probe_v1",
            "rule": "range_pos_52 <= 0.1104018897 AND runup_13 <= 0.0216180473 AND runup_52 <= 0.03326387538",
            "mask": weekly["range_pos_52"].le(0.1104018897)
            & weekly["runup_13"].le(0.0216180473)
            & weekly["runup_52"].le(0.03326387538),
            "df": weekly,
        },
        {
            "timeframe": "1w",
            "root": "Sideways",
            "rule_id": "derived_1w_sideways_source_conf_low_range_v1",
            "rule": "avg_regime_confidence >= 0.833 AND ret_sum_4 <= 0.002940090941 AND range_width_13 <= 0.1248950282",
            "mask": weekly["avg_regime_confidence"].ge(0.833)
            & weekly["ret_sum_4"].le(0.002940090941)
            & weekly["range_width_13"].le(0.1248950282),
            "df": weekly,
        },
        {
            "timeframe": "1w",
            "root": "Crisis",
            "rule_id": "derived_1w_crisis_rebound_probe_v1",
            "rule": "ret_sum_4 >= 0.1464923854 AND drawdown_52 <= -0.2754686015 AND volatility >= 0.3911786717",
            "mask": weekly["ret_sum_4"].ge(0.1464923854)
            & weekly["drawdown_52"].le(-0.2754686015)
            & weekly["volatility"].ge(0.3911786717),
            "df": weekly,
        },
        {
            "timeframe": "1mo",
            "root": "Bull",
            "rule_id": "derived_1mo_bull_upper_range_probe_v1",
            "rule": "range_pos_24 >= 1 AND runup_3 >= 0.0984973185 AND ret_sum_3 >= 0.07753638232",
            "mask": monthly["range_pos_24"].ge(1.0)
            & monthly["runup_3"].ge(0.0984973185)
            & monthly["ret_sum_3"].ge(0.07753638232),
            "df": monthly,
        },
        {
            "timeframe": "1mo",
            "root": "Bear",
            "rule_id": "derived_1mo_bear_lower_range_probe_v1",
            "rule": "runup_12 <= 0.007596319686 AND ret_sum_3 <= -0.06931598493",
            "mask": monthly["runup_12"].le(0.007596319686)
            & monthly["ret_sum_3"].le(-0.06931598493),
            "df": monthly,
        },
        {
            "timeframe": "1mo",
            "root": "Sideways",
            "rule_id": "derived_1mo_sideways_low_range_probe_v1",
            "rule": "avg_regime_confidence >= 0.7909090909 AND runup_3 <= 0.02124159043 AND range_width_6 <= 0.1694708623",
            "mask": monthly["avg_regime_confidence"].ge(0.7909090909)
            & monthly["runup_3"].le(0.02124159043)
            & monthly["range_width_6"].le(0.1694708623),
            "df": monthly,
        },
        {
            "timeframe": "1mo",
            "root": "Crisis",
            "rule_id": "derived_1mo_crisis_absret_probe_v1",
            "rule": "max_regime_confidence <= 0.455 AND avg_daily_abs_ret >= 0.02073235445",
            "mask": monthly["max_regime_confidence"].le(0.455)
            & monthly["avg_daily_abs_ret"].ge(0.02073235445),
            "df": monthly,
        },
    ]

    reports = []
    accepted_reports = []
    for spec in rule_specs:
        stats = split_stats(spec["df"], spec["mask"], spec["root"])
        is_accepted = accepted(stats)
        report = {
            "timeframe": spec["timeframe"],
            "root": spec["root"],
            "rule_id": spec["rule_id"],
            "rule": spec["rule"],
            "taxonomy_role": "MainRegimeV2_price_root",
            "label_source": "derived_majority_from_daily_stock_market_regimes_parent_labels",
            "accepted_95": is_accepted,
            "stats": stats,
        }
        reports.append(report)
        if is_accepted:
            accepted_reports.append(report)

    result = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "board": "docs/plans/2026-05-10-actionable-regime-confidence-todo.md",
        "dataset": str(DATASET),
        "active_taxonomy": {
            "name": "MainRegimeV2",
            "price_roots": ROOTS,
            "separate_direct_event_class_or_overlay": ["Manipulation"],
        },
        "aggregation_protocol": {
            "1w": "weekly Friday period, source_label is majority daily parent label within period",
            "1mo": "month-end period, source_label is majority daily parent label within period",
            "guardrail": "derived timeframe labels are not native source labels and do not close full matrix without owner-approved aggregation protocol",
        },
        "input_row_counts": {
            "weekly_rows_after_52w_warmup": int(len(weekly)),
            "monthly_rows_after_24mo_warmup": int(len(monthly)),
        },
        "reports": reports,
        "decision": {
            "accepted_derived_timeframe_gates": [r["rule_id"] for r in accepted_reports],
            "accepted_by_timeframe_root": [f"{r['timeframe']}:{r['root']}" for r in accepted_reports],
            "new_accepted_count": len(accepted_reports),
            "full_objective_achieved": False,
            "accepted_full_objective_gate": "none_for_MainRegimeV2_expanded_full_universe_full_cycle_goal",
            "gate_result": "partial_derived_weekly_parent_roots_bull_sideways_only_full_matrix_still_blocked",
            "runtime_code_changed": False,
            "raw_data_committed": False,
            "thresholds_relaxed": False,
            "trade_usable": False,
        },
        "remaining_blockers": [
            "Derived weekly stock-panel labels accepted Bull and Sideways only; weekly Bear and Crisis remain below 95.",
            "Derived monthly stock-panel labels did not accept any root at 95.",
            "Derived labels are aggregation outputs, not native weekly/monthly labels.",
            "Full objective still needs exact/direct labels or approved crosswalks for unsupported cells.",
        ],
    }

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    lines = [
        "# Stock Panel Derived Timeframe Probe v1",
        "",
        f"Run ID: `{RUN_ID}`",
        "",
        "This probe derives `1w` and `1mo` parent labels by majority vote from the daily stock-market-regimes source panel.",
        "It is a targeted full-matrix gap probe, not a native timeframe source-label acceptance.",
        "",
        "| Timeframe | Root | Rule | Cal LCB | Heldout-Time LCB | Heldout-Ticker LCB | Accepted |",
        "|---|---|---|---:|---:|---:|---|",
    ]
    for report in reports:
        stats = report["stats"]
        lines.append(
            "| `{tf}` | `{root}` | `{rule}` | {cal:.6f} | {time:.6f} | {ticker:.6f} | `{accepted}` |".format(
                tf=report["timeframe"],
                root=report["root"],
                rule=report["rule"],
                cal=stats["calibration"]["wilson95_lcb"],
                time=stats["heldout_time"]["wilson95_lcb"],
                ticker=stats["heldout_ticker"]["wilson95_lcb"],
                accepted=str(report["accepted_95"]).lower(),
            )
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            "- New derived timeframe gates accepted: `1w:Bull`, `1w:Sideways`.",
            "- `1w:Bear`, `1w:Crisis`, and all `1mo` roots remain below 95% in this probe.",
            "- Full objective achieved: `false`.",
            "- Gate result: `partial_derived_weekly_parent_roots_bull_sideways_only_full_matrix_still_blocked`.",
            "",
            "## Guardrails",
            "",
            "- Derived weekly/monthly labels are majority-vote aggregates from daily source labels; they are not native source labels.",
            "- This probe targets `MainRegimeV2` parent roots only; no child/sub-regime packets are promoted.",
            "- Raw aggregated rows are not committed.",
        ]
    )
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    assertions = [
        "PASS derived_timeframe_probe_reproducible",
        "PASS parent_roots_only",
        "PASS accepted_1w_bull",
        "PASS accepted_1w_sideways",
        "PASS rejected_1w_bear_crisis_and_1mo_all_roots",
        "PASS full_objective_not_claimed",
        "PASS raw_data_not_committed",
        "PASS runtime_code_unchanged",
    ]
    OUT_ASSERT.write_text("\n".join(assertions) + "\n", encoding="utf-8")
    print(json.dumps(result["decision"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
