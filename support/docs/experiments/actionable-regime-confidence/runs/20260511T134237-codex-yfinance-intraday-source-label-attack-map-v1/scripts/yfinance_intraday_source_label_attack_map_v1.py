#!/usr/bin/env python3
"""Triage v12 yfinance intraday source-label requests without promoting proxies."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd


RUN_ID = "20260511T134237+0800-codex-yfinance-intraday-source-label-attack-map-v1"
RUN_ROOT = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T134237-codex-yfinance-intraday-source-label-attack-map-v1"
)
V12_REQUESTS = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T133453-codex-post-axiswise-acquisition-request-v12/"
    "acquisition-request/post_axiswise_active_source_label_requests_v12.csv"
)
SOURCE_PANEL = Path(
    "/Users/thrill3r/Downloads/stock-market-regimes-20002026/"
    "stock_market_regimes_2000_2026.csv"
)
OUT_JSON = RUN_ROOT / "source-label-attack/yfinance_intraday_source_label_attack_map_v1.json"
OUT_MD = RUN_ROOT / "source-label-attack/yfinance_intraday_source_label_attack_map_v1.md"
OUT_CSV = RUN_ROOT / "source-label-attack/yfinance_intraday_source_label_attack_map_v1.csv"
OUT_ASSERT = RUN_ROOT / "checks/yfinance_intraday_source_label_attack_map_v1_assertions.out"

INTRADAY_TIMEFRAMES = {"1m", "5m", "15m", "30m", "1h", "4h"}
ROOTS = ["Bull", "Bear", "Sideways", "Crisis"]

# Candidate relation only. These are not accepted labels until an explicit
# owner-approved crosswalk and calibration gate exists.
CROSSWALK_CANDIDATES = {
    "DIA": {"source_ticker": "^DJI", "relation": "index_etf_tracks_dow"},
    "YM=F": {"source_ticker": "^DJI", "relation": "index_future_tracks_dow"},
    "SPY": {"source_ticker": "^GSPC", "relation": "index_etf_tracks_sp500"},
    "ES=F": {"source_ticker": "^GSPC", "relation": "index_future_tracks_sp500"},
    "QQQ": {"source_ticker": "^IXIC", "relation": "nasdaq_etf_candidate_requires_ndx_vs_ixic_policy"},
    "NQ=F": {"source_ticker": "^IXIC", "relation": "nasdaq_future_candidate_requires_ndx_vs_ixic_policy"},
    "^NDX": {"source_ticker": "^IXIC", "relation": "nasdaq100_vs_composite_candidate_requires_policy"},
}


def classify_request(row: pd.Series, source_tickers: set[str]) -> dict[str, str]:
    instrument = row["instrument"]
    if instrument in source_tickers:
        return {
            "attack_bucket": "exact_same_source_daily_label_attachable_pending_policy",
            "candidate_source_ticker": instrument,
            "candidate_source_relation": "exact_same_ticker_daily_source_label",
            "required_next_artifact": "daily_to_intraday_source_label_attachment_policy_and_calibration_probe",
            "acceptance_state": "not_accepted_policy_required",
        }

    if instrument in CROSSWALK_CANDIDATES:
        candidate = CROSSWALK_CANDIDATES[instrument]
        return {
            "attack_bucket": "explicit_crosswalk_candidate_pending_owner_approval",
            "candidate_source_ticker": candidate["source_ticker"],
            "candidate_source_relation": candidate["relation"],
            "required_next_artifact": "owner_approved_crosswalk_then_calibrated_source_label_attachment_probe",
            "acceptance_state": "not_accepted_crosswalk_required",
        }

    return {
        "attack_bucket": "unsupported_no_current_source_label",
        "candidate_source_ticker": "",
        "candidate_source_relation": "none",
        "required_next_artifact": "acquire_native_source_label_rows_or_drop_from_current_high_yield_batch",
        "acceptance_state": "blocked_no_source_label",
    }


def main() -> int:
    requests = pd.read_csv(V12_REQUESTS)
    source_tickers = set(pd.read_csv(SOURCE_PANEL, usecols=["ticker"])["ticker"].unique())

    yfinance_intraday = requests[
        (requests["provider"] == "yfinance") & (requests["timeframe"].isin(INTRADAY_TIMEFRAMES))
    ].copy()

    enriched_rows = []
    for _, row in yfinance_intraday.iterrows():
        classified = classify_request(row, source_tickers)
        enriched = row.to_dict()
        enriched.update(classified)
        enriched_rows.append(enriched)

    enriched_df = pd.DataFrame(enriched_rows)
    summary_by_bucket = enriched_df.groupby("attack_bucket").size().sort_values(ascending=False).to_dict()
    summary_by_bucket_root = (
        enriched_df.groupby(["attack_bucket", "root"]).size().sort_values(ascending=False).to_dict()
    )
    summary_by_bucket_timeframe = (
        enriched_df.groupby(["attack_bucket", "timeframe"]).size().sort_values(ascending=False).to_dict()
    )
    summary_by_instrument = (
        enriched_df.groupby(["attack_bucket", "instrument"]).size().sort_values(ascending=False).to_dict()
    )

    exact_rows = int((enriched_df["attack_bucket"] == "exact_same_source_daily_label_attachable_pending_policy").sum())
    crosswalk_rows = int((enriched_df["attack_bucket"] == "explicit_crosswalk_candidate_pending_owner_approval").sum())
    unsupported_rows = int((enriched_df["attack_bucket"] == "unsupported_no_current_source_label").sum())

    result = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "board": "docs/plans/2026-05-10-actionable-regime-confidence-todo.md",
        "source_request_artifact": str(V12_REQUESTS),
        "source_panel": str(SOURCE_PANEL),
        "active_taxonomy": {
            "name": "MainRegimeV2",
            "price_roots": ROOTS,
            "separate_direct_event_class_or_overlay": ["Manipulation"],
        },
        "scope": {
            "provider": "yfinance",
            "timeframes": sorted(INTRADAY_TIMEFRAMES),
            "input_rows": int(len(yfinance_intraday)),
            "guardrail": "classification_only_no_provider_bars_no_hmm_no_ohlcv_generated_labels",
        },
        "summaries": {
            "by_bucket": summary_by_bucket,
            "by_bucket_root": {str(k): int(v) for k, v in summary_by_bucket_root.items()},
            "by_bucket_timeframe": {str(k): int(v) for k, v in summary_by_bucket_timeframe.items()},
            "by_instrument": {str(k): int(v) for k, v in summary_by_instrument.items()},
        },
        "decision": {
            "exact_same_source_daily_label_attachable_pending_policy_rows": exact_rows,
            "explicit_crosswalk_candidate_pending_owner_approval_rows": crosswalk_rows,
            "unsupported_no_current_source_label_rows": unsupported_rows,
            "accepted_confidence_added": 0,
            "accepted_full_objective_gate": "none_for_MainRegimeV2_expanded_full_universe_full_cycle_goal",
            "full_objective_achieved": False,
            "gate_result": "yfinance_intraday_attack_map_exact48_crosswalk168_unsupported120_no_confidence_gate",
            "runtime_code_changed": False,
            "raw_data_committed": False,
            "thresholds_relaxed": False,
            "trade_usable": False,
        },
        "next_action": (
            "Start with the 48 exact same-source ^GSPC/^DJI intraday rows: write an explicit "
            "daily-to-intraday source-label attachment policy and calibration probe. Do not use yfinance bars, HMM, "
            "future returns, or strategy predictions as labels."
        ),
    }

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    OUT_ASSERT.parent.mkdir(parents=True, exist_ok=True)
    enriched_df.to_csv(OUT_CSV, index=False)
    OUT_JSON.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    lines = [
        "# YFinance Intraday Source-Label Attack Map v1",
        "",
        f"Run ID: `{RUN_ID}`",
        "",
        "This artifact attacks the v12 `336` native yfinance intraday requests by triage only.",
        "It does not download provider bars and does not promote OHLCV/HMM/future-return/generated labels.",
        "",
        "## Result",
        "",
        f"- Exact same-source daily-label attachable rows pending policy: `{exact_rows}`.",
        f"- Explicit crosswalk candidate rows pending owner approval: `{crosswalk_rows}`.",
        f"- Unsupported rows with no current source label: `{unsupported_rows}`.",
        "- Accepted confidence added: `0`.",
        "- Full objective achieved: `false`.",
        "- Gate result: `yfinance_intraday_attack_map_exact48_crosswalk168_unsupported120_no_confidence_gate`.",
        "",
        "## Buckets",
        "",
        "| Bucket | Rows | Meaning |",
        "|---|---:|---|",
    ]
    bucket_notes = {
        "exact_same_source_daily_label_attachable_pending_policy": "Instrument exists in the stock-market-regimes source panel; needs explicit daily-to-intraday attachment policy before calibration.",
        "explicit_crosswalk_candidate_pending_owner_approval": "Instrument has a plausible index/ETF/futures relation to a source ticker; still not accepted until approved and calibrated.",
        "unsupported_no_current_source_label": "No source ticker currently exists; needs native source-label rows or should leave the high-yield batch.",
    }
    for bucket, count in summary_by_bucket.items():
        lines.append(f"| `{bucket}` | {count} | {bucket_notes[bucket]} |")
    lines.extend(
        [
            "",
            "## Next",
            "",
            "- Start with the `48` exact same-source `^GSPC`/`^DJI` intraday rows.",
            "- Required next artifact: daily-to-intraday source-label attachment policy plus calibration probe.",
            "- Keep `Manipulation` FINRA matched-negative acquisition separate.",
        ]
    )
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    assertions = [
        f"run_id={RUN_ID}",
        "input_yfinance_intraday_rows=336" if len(yfinance_intraday) == 336 else f"FAIL input_yfinance_intraday_rows={len(yfinance_intraday)}",
        "exact_same_source_rows=48" if exact_rows == 48 else f"FAIL exact_same_source_rows={exact_rows}",
        "crosswalk_candidate_rows=168" if crosswalk_rows == 168 else f"FAIL crosswalk_candidate_rows={crosswalk_rows}",
        "unsupported_rows=120" if unsupported_rows == 120 else f"FAIL unsupported_rows={unsupported_rows}",
        "accepted_confidence_added=0",
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
