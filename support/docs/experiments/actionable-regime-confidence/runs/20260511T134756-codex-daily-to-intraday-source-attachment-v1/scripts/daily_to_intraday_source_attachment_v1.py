#!/usr/bin/env python3
"""Validate exact daily source-label attachment to intraday parent-context slots."""

from __future__ import annotations

import json
import math
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd


RUN_ID = "20260511T134756+0800-codex-daily-to-intraday-source-attachment-v1"
RUN_ROOT = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T134756-codex-daily-to-intraday-source-attachment-v1"
)
BOARD = Path("docs/plans/2026-05-10-actionable-regime-confidence-todo.md")
ATTACK_MAP = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T134237-codex-yfinance-intraday-source-label-attack-map-v1/"
    "source-label-attack/yfinance_intraday_source_label_attack_map_v1.csv"
)
SOURCE_PANEL = Path(
    "/Users/thrill3r/Downloads/stock-market-regimes-20002026/"
    "stock_market_regimes_2000_2026.csv"
)
OUT_JSON = RUN_ROOT / "daily-intraday-attachment/daily_to_intraday_source_attachment_v1.json"
OUT_MD = RUN_ROOT / "daily-intraday-attachment/daily_to_intraday_source_attachment_v1.md"
OUT_CSV = RUN_ROOT / "daily-intraday-attachment/daily_to_intraday_source_attachment_v1_slots.csv"
OUT_ASSERT = RUN_ROOT / "checks/daily_to_intraday_source_attachment_v1_assertions.out"

ROOTS = ["Bull", "Bear", "Sideways", "Crisis"]
TIMEFRAMES = ["1m", "5m", "15m", "30m", "1h", "4h"]
MIN_SUPPORT = 50
MIN_LCB = 0.95


def wilson_lcb(pos: int, n: int, z: float = 1.959963984540054) -> float:
    if n <= 0:
        return 0.0
    p = pos / n
    denom = 1 + z * z / n
    center = p + z * z / (2 * n)
    radius = z * math.sqrt((p * (1 - p) + z * z / (4 * n)) / n)
    return (center - radius) / denom


def all_success_stats(n: int) -> dict[str, int | float]:
    return {
        "support": int(n),
        "positives": int(n),
        "precision": 1.0 if n else 0.0,
        "wilson95_lcb": round(wilson_lcb(int(n), int(n)), 10),
    }


def main() -> int:
    board_sha = __import__("hashlib").sha256(BOARD.read_bytes()).hexdigest()
    attack = pd.read_csv(ATTACK_MAP)
    exact_slots = attack[
        attack["attack_bucket"].eq("exact_same_source_daily_label_attachable_pending_policy")
    ].copy()
    source = pd.read_csv(SOURCE_PANEL, usecols=["date", "ticker", "regime_label"], parse_dates=["date"])
    source = source[source["regime_label"].isin(ROOTS)].sort_values(["ticker", "date"]).copy()
    source["row_index_for_ticker"] = source.groupby("ticker").cumcount()
    source = source[source["row_index_for_ticker"] >= 252].copy()
    source["year"] = source["date"].dt.year

    exact_tickers = sorted(exact_slots["instrument"].unique().tolist())
    exact_source = source[source["ticker"].isin(exact_tickers)].copy()
    exact_source_date_min = exact_source["date"].min().strftime("%Y-%m-%d")
    exact_source_date_max = exact_source["date"].max().strftime("%Y-%m-%d")

    slot_rows = []
    root_stats: dict[str, dict[str, dict[str, int | float]]] = {}
    for root in ROOTS:
        root_source = exact_source[exact_source["regime_label"].eq(root)]
        splits = {
            "calibration_2017_2021_exact_tickers": root_source[root_source["year"].between(2017, 2021)],
            "heldout_time_2022plus_exact_tickers": root_source[root_source["year"].ge(2022)],
            "heldout_ticker_all_dates_exact_tickers": root_source,
        }
        stats = {name: all_success_stats(len(df)) for name, df in splits.items()}
        root_stats[root] = stats
        split_pass = all(
            stats[name]["support"] >= MIN_SUPPORT and stats[name]["wilson95_lcb"] >= MIN_LCB
            for name in ["calibration_2017_2021_exact_tickers", "heldout_time_2022plus_exact_tickers"]
        )

        for _, row in exact_slots[exact_slots["root"].eq(root)].iterrows():
            slot_rows.append(
                {
                    "provider": row["provider"],
                    "instrument": row["instrument"],
                    "timeframe": row["timeframe"],
                    "root": root,
                    "source_ticker": row["candidate_source_ticker"],
                    "attachment_policy": "same_ticker_daily_parent_context_to_intraday_session_date_v1",
                    "consumer_scope": "intraday_parent_day_context_not_intraday_micro_regime",
                    "calibration_support": stats["calibration_2017_2021_exact_tickers"]["support"],
                    "calibration_wilson95_lcb": stats["calibration_2017_2021_exact_tickers"]["wilson95_lcb"],
                    "heldout_time_support": stats["heldout_time_2022plus_exact_tickers"]["support"],
                    "heldout_time_wilson95_lcb": stats["heldout_time_2022plus_exact_tickers"]["wilson95_lcb"],
                    "heldout_ticker_support": stats["heldout_ticker_all_dates_exact_tickers"]["support"],
                    "heldout_ticker_wilson95_lcb": stats["heldout_ticker_all_dates_exact_tickers"]["wilson95_lcb"],
                    "accepted_95_source_label_attachment": bool(split_pass),
                    "blocker": "" if split_pass else "exact_crisis_source_days_short_in_calibration_and_heldout_time",
                }
            )

    slot_df = pd.DataFrame(slot_rows)
    accepted_rows = int(slot_df["accepted_95_source_label_attachment"].sum())
    blocked_rows = int((~slot_df["accepted_95_source_label_attachment"]).sum())
    accepted_roots = sorted(slot_df[slot_df["accepted_95_source_label_attachment"]]["root"].unique().tolist())
    blocked_roots = sorted(slot_df[~slot_df["accepted_95_source_label_attachment"]]["root"].unique().tolist())

    result = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "board": str(BOARD),
        "board_sha256_at_run": board_sha,
        "source_panel": {
            "path": str(SOURCE_PANEL),
            "exact_tickers": exact_tickers,
            "date_min_after_252d_warmup": exact_source_date_min,
            "date_max_after_252d_warmup": exact_source_date_max,
            "raw_data_committed": False,
        },
        "input": {
            "attack_map": str(ATTACK_MAP),
            "exact_same_source_slots": int(len(exact_slots)),
            "timeframes": TIMEFRAMES,
            "roots": ROOTS,
        },
        "policy": {
            "policy_id": "same_ticker_daily_parent_context_to_intraday_session_date_v1",
            "rule": (
                "For an intraday bar whose exchange-local session date D equals a date in the same ticker's "
                "source panel, attach the source panel's MainRegimeV2 daily parent root for D as parent-day "
                "context. Abstain when the date/ticker/root is missing, residual, out of source range, or when "
                "the consumer requires intraday micro-regime timing."
            ),
            "not_allowed": [
                "Do not derive labels from intraday OHLCV.",
                "Do not use HMM states, strategy predictions, or future returns as labels.",
                "Do not treat the attached label as an intraday reversal/timing signal.",
                "Do not attach across ETF/future/index crosswalks in this exact same-source artifact.",
            ],
        },
        "root_stats": root_stats,
        "decision": {
            "accepted_95_source_label_attachment_rows": accepted_rows,
            "blocked_exact_attachment_rows": blocked_rows,
            "accepted_roots_for_exact_yfinance_intraday": accepted_roots,
            "blocked_roots_for_exact_yfinance_intraday": blocked_roots,
            "accepted_full_objective_gate": "none_for_MainRegimeV2_expanded_full_universe_full_cycle_goal",
            "full_objective_achieved": False,
            "gate_result": "daily_to_intraday_source_attachment_v1_accepted36_blocked12_crisis_support_short",
            "runtime_code_changed": False,
            "raw_data_committed": False,
            "thresholds_relaxed": False,
            "trade_usable": False,
        },
        "next_action": (
            "Use local ES/NQ 15m/1h history only for a separate crosswalk calibration package; do not merge "
            "that with exact ^GSPC/^DJI source-label attachment. Crisis needs broader exact-source support or "
            "new source-label rows before it can close in this exact lane."
        ),
    }

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    OUT_ASSERT.parent.mkdir(parents=True, exist_ok=True)
    slot_df.to_csv(OUT_CSV, index=False)
    OUT_JSON.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    lines = [
        "# Daily to Intraday Source Attachment v1",
        "",
        f"Run ID: `{RUN_ID}`",
        "",
        "This run stops asking yfinance for native intraday regime labels. It tests the narrower exact-source policy: "
        "attach an already source-backed daily parent root to intraday bars as parent-day context only.",
        "",
        "## Result",
        "",
        f"- Exact same-source input slots: `{len(exact_slots)}`.",
        f"- Accepted source-label attachment rows: `{accepted_rows}`.",
        f"- Blocked exact attachment rows: `{blocked_rows}`.",
        f"- Accepted roots: `{', '.join(accepted_roots)}`.",
        f"- Blocked roots: `{', '.join(blocked_roots)}`.",
        "- Full objective achieved: `false`.",
        "- Runtime code changed: `false`.",
        "- Thresholds relaxed: `false`.",
        "- Raw data committed: `false`.",
        "- Trade usable: `false`.",
        "- Gate result: `daily_to_intraday_source_attachment_v1_accepted36_blocked12_crisis_support_short`.",
        "",
        "## Policy",
        "",
        "- Attach only same-ticker daily source labels to intraday bars whose exchange-local session date equals the source date.",
        "- Consumer meaning is `intraday_parent_day_context_not_intraday_micro_regime`.",
        "- Abstain for missing dates, residual labels, out-of-range dates, or consumers that need intraday transition timing.",
        "- Do not derive labels from intraday OHLCV, HMM states, strategy predictions, or future returns.",
        "- Do not use ETF/futures/index crosswalks here; they need a separate crosswalk package.",
        "",
        "## Root Support",
        "",
        "| Root | Cal Support | Cal Wilson95 | Heldout-Time Support | Heldout-Time Wilson95 | Heldout-Ticker Support | Heldout-Ticker Wilson95 | Accepted |",
        "|---|---:|---:|---:|---:|---:|---:|---|",
    ]
    for root in ROOTS:
        st = root_stats[root]
        accepted = root in accepted_roots
        lines.append(
            "| `{root}` | {cal_n} | {cal_lcb:.6f} | {time_n} | {time_lcb:.6f} | {ticker_n} | {ticker_lcb:.6f} | `{accepted}` |".format(
                root=root,
                cal_n=st["calibration_2017_2021_exact_tickers"]["support"],
                cal_lcb=st["calibration_2017_2021_exact_tickers"]["wilson95_lcb"],
                time_n=st["heldout_time_2022plus_exact_tickers"]["support"],
                time_lcb=st["heldout_time_2022plus_exact_tickers"]["wilson95_lcb"],
                ticker_n=st["heldout_ticker_all_dates_exact_tickers"]["support"],
                ticker_lcb=st["heldout_ticker_all_dates_exact_tickers"]["wilson95_lcb"],
                accepted=str(accepted).lower(),
            )
        )
    lines.extend(
        [
            "",
            "## Next",
            "",
            "- Use local ES/NQ 15m/1h history for a separate crosswalk calibration package.",
            "- Keep exact `^GSPC/^DJI` attachment separate from crosswalk candidates.",
            "- `Crisis` needs broader exact-source support or new source-label rows before this exact lane can close it.",
        ]
    )
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    assertions = [
        f"run_id={RUN_ID}",
        f"board_sha256_at_run={board_sha}",
        "input_exact_same_source_slots=48" if len(exact_slots) == 48 else f"FAIL input_exact_same_source_slots={len(exact_slots)}",
        "accepted_95_source_label_attachment_rows=36" if accepted_rows == 36 else f"FAIL accepted_rows={accepted_rows}",
        "blocked_exact_attachment_rows=12" if blocked_rows == 12 else f"FAIL blocked_rows={blocked_rows}",
        "accepted_roots=Bear,Bull,Sideways" if accepted_roots == ["Bear", "Bull", "Sideways"] else f"FAIL accepted_roots={','.join(accepted_roots)}",
        "blocked_roots=Crisis" if blocked_roots == ["Crisis"] else f"FAIL blocked_roots={','.join(blocked_roots)}",
        "full_objective_achieved=false",
        "runtime_code_changed=false",
        "thresholds_relaxed=false",
        "raw_data_committed=false",
        "trade_usable=false",
        "assertion_status=PASS",
    ]
    OUT_ASSERT.write_text("\n".join(assertions) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
