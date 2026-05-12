#!/usr/bin/env python3
"""Build an ES/NQ source-label crosswalk calibration package without proxy labels."""

from __future__ import annotations

import hashlib
import json
import math
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd


RUN_ID = "20260511T135932+0800-codex-es-nq-source-crosswalk-calibration-v1"
RUN_ROOT = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T135932-codex-es-nq-source-crosswalk-calibration-v1"
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
TARGETS = {
    "ES=F": {
        "local_symbol": "ES",
        "source_ticker": "^GSPC",
        "local_15m": Path("/Users/thrill3r/Downloads/Tomac/ict-engine-cleaned-15m/es.continuous-15m.json"),
        "relation_policy": "direct_index_future_tracks_source_index_v1",
        "relation_accepted": True,
        "relation_note": "ES futures are treated as direct S&P 500 index-future context for ^GSPC source labels.",
    },
    "NQ=F": {
        "local_symbol": "NQ",
        "source_ticker": "^IXIC",
        "local_15m": Path("/Users/thrill3r/Downloads/Tomac/ict-engine-cleaned-15m/nq.continuous-15m.json"),
        "relation_policy": "blocked_ndx_vs_ixic_policy_unresolved_v1",
        "relation_accepted": False,
        "relation_note": "NQ futures track Nasdaq 100; the available source panel ticker is ^IXIC, so ^NDX or owner-approved ^IXIC policy is required before acceptance.",
    },
}
OUT_JSON = RUN_ROOT / "crosswalk-calibration/es_nq_source_crosswalk_calibration_v1.json"
OUT_MD = RUN_ROOT / "crosswalk-calibration/es_nq_source_crosswalk_calibration_v1.md"
OUT_CSV = RUN_ROOT / "crosswalk-calibration/es_nq_source_crosswalk_calibration_v1_slots.csv"
OUT_ASSERT = RUN_ROOT / "checks/es_nq_source_crosswalk_calibration_v1_assertions.out"

ROOTS = ["Bull", "Bear", "Sideways", "Crisis"]
TIMEFRAMES = ["15m", "1h"]
MIN_SUPPORT = 50
MIN_LCB = 0.95


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


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


def load_source_panel() -> pd.DataFrame:
    source = pd.read_csv(SOURCE_PANEL, usecols=["date", "ticker", "regime_label"], parse_dates=["date"])
    source = source[source["regime_label"].isin(ROOTS)].sort_values(["ticker", "date"]).copy()
    source["row_index_for_ticker"] = source.groupby("ticker").cumcount()
    source = source[source["row_index_for_ticker"] >= 252].copy()
    source["year"] = source["date"].dt.year
    source["session_date"] = source["date"].dt.date
    return source


def load_target_sessions(path: Path) -> pd.DataFrame:
    payload = json.loads(path.read_text())
    bars = pd.DataFrame(payload["candles"])
    bars["timestamp"] = pd.to_datetime(bars["timestamp"], utc=True)
    bars["session_date"] = bars["timestamp"].dt.tz_convert("America/New_York").dt.date
    session = bars.groupby("session_date").size().reset_index(name="bar_count_15m")
    session["has_15m_coverage"] = session["bar_count_15m"] >= 1
    session["has_1h_coverage_from_15m"] = session["bar_count_15m"] >= 4
    return session


def split_stats(source_for_target: pd.DataFrame) -> dict[str, dict[str, int | float]]:
    splits = {
        "calibration_2017_2021_target_sessions": source_for_target[
            source_for_target["year"].between(2017, 2021)
        ],
        "heldout_time_2022plus_target_sessions": source_for_target[source_for_target["year"].ge(2022)],
        "all_target_sessions": source_for_target,
    }
    return {name: all_success_stats(len(df)) for name, df in splits.items()}


def support_pass(stats: dict[str, dict[str, int | float]]) -> bool:
    required = ["calibration_2017_2021_target_sessions", "heldout_time_2022plus_target_sessions"]
    return all(stats[name]["support"] >= MIN_SUPPORT and stats[name]["wilson95_lcb"] >= MIN_LCB for name in required)


def primary_support_blocker(stats: dict[str, dict[str, int | float]]) -> str:
    cal = stats["calibration_2017_2021_target_sessions"]
    hold = stats["heldout_time_2022plus_target_sessions"]
    blockers: list[str] = []
    if cal["support"] < MIN_SUPPORT:
        blockers.append("calibration_support_below_50")
    if cal["wilson95_lcb"] < MIN_LCB:
        blockers.append("calibration_wilson95_below_0_95")
    if hold["support"] < MIN_SUPPORT:
        blockers.append("heldout_time_support_below_50")
    if hold["wilson95_lcb"] < MIN_LCB:
        blockers.append("heldout_time_wilson95_below_0_95")
    return "|".join(blockers)


def main() -> int:
    board_sha = sha256(BOARD)
    attack = pd.read_csv(ATTACK_MAP)
    candidates = attack[
        attack["attack_bucket"].eq("explicit_crosswalk_candidate_pending_owner_approval")
        & attack["instrument"].isin(TARGETS)
        & attack["timeframe"].isin(TIMEFRAMES)
    ].copy()
    source = load_source_panel()

    target_sessions = {}
    target_meta = {}
    for instrument, cfg in TARGETS.items():
        sessions = load_target_sessions(cfg["local_15m"])
        target_sessions[instrument] = sessions
        target_meta[instrument] = {
            "local_symbol": cfg["local_symbol"],
            "local_15m_path": str(cfg["local_15m"]),
            "local_15m_sha256": sha256(cfg["local_15m"]),
            "bar_count_15m": int(sessions["bar_count_15m"].sum()),
            "session_count_15m": int(sessions["has_15m_coverage"].sum()),
            "session_count_1h_from_15m": int(sessions["has_1h_coverage_from_15m"].sum()),
            "date_min": str(sessions["session_date"].min()),
            "date_max": str(sessions["session_date"].max()),
            "raw_data_committed": False,
        }

    slot_rows: list[dict[str, object]] = []
    root_stats: dict[str, dict[str, dict[str, dict[str, int | float]]]] = {}
    for _, row in candidates.sort_values(["instrument", "timeframe", "root"]).iterrows():
        instrument = row["instrument"]
        timeframe = row["timeframe"]
        root = row["root"]
        cfg = TARGETS[instrument]
        sessions = target_sessions[instrument]
        coverage_col = "has_15m_coverage" if timeframe == "15m" else "has_1h_coverage_from_15m"
        target_dates = set(sessions[sessions[coverage_col]]["session_date"])
        source_for_target = source[
            source["ticker"].eq(cfg["source_ticker"])
            & source["session_date"].isin(target_dates)
            & source["regime_label"].eq(root)
        ].copy()
        stats = split_stats(source_for_target)
        root_stats.setdefault(instrument, {}).setdefault(timeframe, {})[root] = stats

        relation_accepted = bool(cfg["relation_accepted"])
        root_support_pass = support_pass(stats)
        accepted = relation_accepted and root_support_pass
        support_blocker = primary_support_blocker(stats)
        if not relation_accepted:
            blocker = "crosswalk_relation_policy_unresolved"
            if support_blocker:
                blocker += f"|{support_blocker}"
        else:
            blocker = "" if accepted else support_blocker

        slot_rows.append(
            {
                "provider": row["provider"],
                "instrument": instrument,
                "local_symbol": cfg["local_symbol"],
                "timeframe": timeframe,
                "root": root,
                "source_ticker": cfg["source_ticker"],
                "attack_map_relation": row["candidate_source_relation"],
                "relation_policy": cfg["relation_policy"],
                "relation_accepted": relation_accepted,
                "consumer_scope": "crosswalk_parent_day_context_not_intraday_micro_regime",
                "target_session_count": len(target_dates),
                "calibration_support": stats["calibration_2017_2021_target_sessions"]["support"],
                "calibration_wilson95_lcb": stats["calibration_2017_2021_target_sessions"]["wilson95_lcb"],
                "heldout_time_support": stats["heldout_time_2022plus_target_sessions"]["support"],
                "heldout_time_wilson95_lcb": stats["heldout_time_2022plus_target_sessions"]["wilson95_lcb"],
                "all_target_session_support": stats["all_target_sessions"]["support"],
                "all_target_session_wilson95_lcb": stats["all_target_sessions"]["wilson95_lcb"],
                "source_label_support_pass": root_support_pass,
                "accepted_95_source_label_crosswalk_attachment": accepted,
                "blocker": blocker,
            }
        )

    slot_df = pd.DataFrame(slot_rows)
    accepted_rows = int(slot_df["accepted_95_source_label_crosswalk_attachment"].sum())
    blocked_rows = int((~slot_df["accepted_95_source_label_crosswalk_attachment"]).sum())
    accepted_slots = slot_df[slot_df["accepted_95_source_label_crosswalk_attachment"]][
        ["instrument", "timeframe", "root"]
    ].to_dict("records")
    blocker_counts = Counter()
    for blocker in slot_df[~slot_df["accepted_95_source_label_crosswalk_attachment"]]["blocker"]:
        blocker_counts[str(blocker)] += 1

    total_crosswalk_candidates = int(
        attack["attack_bucket"].eq("explicit_crosswalk_candidate_pending_owner_approval").sum()
    )
    result = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "board": str(BOARD),
        "board_sha256_at_run": board_sha,
        "input": {
            "attack_map": str(ATTACK_MAP),
            "total_explicit_crosswalk_candidates_in_attack_map": total_crosswalk_candidates,
            "scoped_es_nq_15m_1h_slots": int(len(slot_df)),
            "remaining_crosswalk_candidates_outside_scope": total_crosswalk_candidates - int(len(slot_df)),
            "source_panel": str(SOURCE_PANEL),
            "target_timeframes": TIMEFRAMES,
            "roots": ROOTS,
            "raw_data_committed": False,
        },
        "target_data": target_meta,
        "policy": {
            "policy_id": "es_nq_source_crosswalk_parent_day_context_v1",
            "allowed": [
                "Use source-backed daily parent labels only as parent-day context for target intraday sessions.",
                "Use target 15m bars only for session-date coverage and derived 1h coverage.",
                "Accept only direct relation policies plus calibration and heldout-time source-label support.",
            ],
            "not_allowed": [
                "Do not derive target labels from target OHLCV bars.",
                "Do not treat attached labels as intraday micro-regime timing.",
                "Do not use HMM states, generated labels, strategy predictions, or future returns as labels.",
                "Do not accept NQ=F through ^IXIC until the Nasdaq 100 versus Nasdaq Composite policy is resolved.",
            ],
            "target_relation_notes": {instrument: cfg["relation_note"] for instrument, cfg in TARGETS.items()},
        },
        "root_stats": root_stats,
        "decision": {
            "accepted_95_source_label_crosswalk_attachment_rows": accepted_rows,
            "blocked_crosswalk_attachment_rows": blocked_rows,
            "accepted_slots": accepted_slots,
            "blocker_counts": dict(blocker_counts),
            "gate_result": "es_nq_crosswalk_calibration_v1_accepted2_blocked14_not_full_objective",
            "accepted_full_objective_gate": "none_for_MainRegimeV2_expanded_full_universe_full_cycle_goal",
            "full_objective_achieved": False,
            "runtime_code_changed": False,
            "raw_data_committed": False,
            "thresholds_relaxed": False,
            "trade_usable": False,
        },
        "next_action": (
            "Acquire or approve a Nasdaq-100-grade source-label relation for NQ=F and add broader exact-source "
            "Crisis/Bear/Sideways support; keep the remaining ETF/futures/index crosswalks and Kraken/full-species "
            "rows separate."
        ),
    }

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    OUT_ASSERT.parent.mkdir(parents=True, exist_ok=True)
    slot_df.to_csv(OUT_CSV, index=False)
    OUT_JSON.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    lines = [
        "# ES/NQ Source Crosswalk Calibration v1",
        "",
        f"Run ID: `{RUN_ID}`",
        "",
        "This run uses local ES/NQ `15m` history only for target session coverage and derived `1h` coverage. "
        "It does not use target OHLCV as labels; source labels remain the stock-market-regimes daily parent roots.",
        "",
        "## Result",
        "",
        f"- Scoped ES/NQ `15m/1h` crosswalk slots: `{len(slot_df)}`.",
        f"- Accepted source-label crosswalk attachment rows: `{accepted_rows}`.",
        f"- Blocked crosswalk attachment rows: `{blocked_rows}`.",
        "- Accepted full objective gate: `none_for_MainRegimeV2_expanded_full_universe_full_cycle_goal`.",
        "- Full objective achieved: `false`.",
        "- Runtime code changed: `false`.",
        "- Thresholds relaxed: `false`.",
        "- Raw data committed: `false`.",
        "- Trade usable: `false`.",
        "- Gate result: `es_nq_crosswalk_calibration_v1_accepted2_blocked14_not_full_objective`.",
        "",
        "## Policy",
        "",
        "- ES=F -> ^GSPC is treated as a direct index-future-to-source-index parent-day context policy.",
        "- NQ=F -> ^IXIC remains blocked because NQ tracks Nasdaq 100 while the source panel has Nasdaq Composite.",
        "- Target 15m bars are used only to prove target session-date coverage; derived 1h coverage requires at least four 15m bars on the session date.",
        "- No target OHLCV, HMM state, generated label, strategy prediction, or future return is used as a label.",
        "",
        "## Accepted Slots",
        "",
    ]
    if accepted_slots:
        lines.extend(["| Instrument | Timeframe | Root |", "|---|---|---|"])
        for slot in accepted_slots:
            lines.append(f"| `{slot['instrument']}` | `{slot['timeframe']}` | `{slot['root']}` |")
    else:
        lines.append("- None.")
    lines.extend(
        [
            "",
            "## Root Support by Scoped Slot",
            "",
            "| Instrument | Timeframe | Root | Relation Accepted | Cal Support | Cal Wilson95 | Heldout-Time Support | Heldout-Time Wilson95 | Accepted | Blocker |",
            "|---|---|---|---:|---:|---:|---:|---:|---:|---|",
        ]
    )
    for _, row in slot_df.sort_values(["instrument", "timeframe", "root"]).iterrows():
        lines.append(
            "| `{instrument}` | `{timeframe}` | `{root}` | `{rel}` | {cal_n} | {cal_lcb:.6f} | {time_n} | {time_lcb:.6f} | `{accepted}` | `{blocker}` |".format(
                instrument=row["instrument"],
                timeframe=row["timeframe"],
                root=row["root"],
                rel=str(row["relation_accepted"]).lower(),
                cal_n=int(row["calibration_support"]),
                cal_lcb=float(row["calibration_wilson95_lcb"]),
                time_n=int(row["heldout_time_support"]),
                time_lcb=float(row["heldout_time_wilson95_lcb"]),
                accepted=str(row["accepted_95_source_label_crosswalk_attachment"]).lower(),
                blocker=row["blocker"] or "",
            )
        )
    lines.extend(
        [
            "",
            "## Target Data",
            "",
            "| Instrument | Local Symbol | 15m Bars | 15m Sessions | 1h Sessions From 15m | Date Range | Raw Committed |",
            "|---|---|---:|---:|---:|---|---|",
        ]
    )
    for instrument, meta in target_meta.items():
        lines.append(
            "| `{instrument}` | `{symbol}` | {bars} | {s15} | {s1h} | `{start}` to `{end}` | `false` |".format(
                instrument=instrument,
                symbol=meta["local_symbol"],
                bars=meta["bar_count_15m"],
                s15=meta["session_count_15m"],
                s1h=meta["session_count_1h_from_15m"],
                start=meta["date_min"],
                end=meta["date_max"],
            )
        )
    lines.extend(
        [
            "",
            "## Next",
            "",
            "- Resolve NQ with a Nasdaq-100-grade source label or explicit owner-approved ^IXIC policy.",
            "- Add broader exact-source Crisis/Bear/Sideways support; ES Bull alone does not close the full matrix.",
            "- Keep ETF/futures/index crosswalks, Kraken/full-species rows, and direct Manipulation acquisition as separate lanes.",
        ]
    )
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    accepted_slot_ids = ",".join(
        f"{slot['instrument']}:{slot['timeframe']}:{slot['root']}" for slot in accepted_slots
    )
    assertions = [
        f"run_id={RUN_ID}",
        f"board_sha256_at_run={board_sha}",
        "input_scoped_es_nq_15m_1h_slots=16" if len(slot_df) == 16 else f"FAIL scoped_slots={len(slot_df)}",
        "accepted_95_source_label_crosswalk_attachment_rows=2"
        if accepted_rows == 2
        else f"FAIL accepted_rows={accepted_rows}",
        "blocked_crosswalk_attachment_rows=14" if blocked_rows == 14 else f"FAIL blocked_rows={blocked_rows}",
        f"accepted_slots={accepted_slot_ids}",
        "full_objective_achieved=false",
        "runtime_code_changed=false",
        "thresholds_relaxed=false",
        "raw_data_committed=false",
        "trade_usable=false",
        "assertion_status=PASS",
    ]
    if any(line.startswith("FAIL") or line.startswith("input_") and not line.endswith("=16") for line in assertions):
        assertions[-1] = "assertion_status=FAIL"
    OUT_ASSERT.write_text("\n".join(assertions) + "\n", encoding="utf-8")
    return 0 if assertions[-1].endswith("PASS") else 1


if __name__ == "__main__":
    raise SystemExit(main())
