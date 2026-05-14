#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from statistics import mean
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[4]
SOURCE = REPO / "docs/experiments/actionable-regime-confidence/runs/20260512T205906+0800-codex-smt-full-coverage-provider-observation-v2"
SOURCE_PACKET = SOURCE / "materials/smt_provider_observation_packet.json"
SOURCE_PROVIDER_DATA = SOURCE / "provider-data"

REGIMES = ["trend", "range", "transition", "stress", "other"]
ROW_FIELDS = [
    "base_symbol",
    "comparison_symbol",
    "relationship_type",
    "relationship_confidence",
    "timeframe",
    "session",
    "comparison_timeframe",
    "comparison_session",
    "timeframe_aligned",
    "session_overlap",
    "event_time",
    "smt_signal",
    "base_swing_type",
    "regime_bucket",
    "base_level",
    "comparison_swing_type",
    "comparison_level",
    "swept_side",
    "normalized_for_inverse_correlation",
    "raw_comparison_swing_type",
    "raw_comparison_level",
    "same_event_window_confirmed",
    "provider_provenance",
    "evidence_source",
    "forward_6h_return",
    "forward_12h_return",
    "directional_6h_return",
    "directional_12h_return",
    "favorable_6h",
    "favorable_12h",
    "mss_or_cisd_confirmed",
    "displacement_confirmed",
    "near_pd_array",
    "pd_array_type",
    "entry_context_complete",
    "confirmation_role",
    "actionable",
    "confidence",
    "fail_closed_reason",
]


def parse_ts(raw: str) -> datetime:
    value = (raw or "").strip()
    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def parse_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() == "true"


def directional_return(signal: str, ret: float) -> float:
    if signal == "bullish_smt":
        return ret
    if signal == "bearish_smt":
        return -ret
    return 0.0


def provider_file(row: dict[str, Any]) -> Path:
    return SOURCE_PROVIDER_DATA / f"{row['base_symbol']}_{row['comparison_symbol']}_{row['timeframe']}.json"


def candles_by_time(path: Path) -> dict[datetime, dict[str, float]]:
    data = json.loads(path.read_text())
    out: dict[datetime, dict[str, float]] = {}
    for candle in data.get("base_rows", []):
        try:
            ts = parse_ts(candle["time"])
            out[ts] = {key: float(candle[key]) for key in ["open", "high", "low", "close"]}
        except Exception:
            continue
    return out


def horizon_return(candles: dict[datetime, dict[str, float]], event_time: str, hours: int) -> float | None:
    if not event_time:
        return None
    ts = parse_ts(event_time)
    current = candles.get(ts)
    future = candles.get(ts + timedelta(hours=hours))
    if not current or not future or current["close"] == 0:
        return None
    return (future["close"] - current["close"]) / current["close"]


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str] | None = None) -> None:
    if fields is None:
        fields = list(rows[0].keys()) if rows else []
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field) for field in fields})


def summarize_by(rows: list[dict[str, Any]], key: str) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row.get(key) or "other")].append(row)
    names = REGIMES if key == "regime_bucket" else sorted(grouped)
    summary: list[dict[str, Any]] = []
    for name in names:
        vals = grouped.get(name, [])
        with_6h = [row for row in vals if row["forward_6h_return"] != ""]
        with_12h = [row for row in vals if row["forward_12h_return"] != ""]
        entry_complete = [row for row in vals if row["entry_context_complete"]]
        summary.append(
            {
                key: name,
                "event_count": len(vals),
                "outcome_6h_count": len(with_6h),
                "candidate_win_rate_6h": round(mean(1.0 if row["favorable_6h"] else 0.0 for row in with_6h), 6) if with_6h else None,
                "candidate_expectancy_6h": round(mean(float(row["directional_6h_return"]) for row in with_6h), 8) if with_6h else None,
                "outcome_12h_count": len(with_12h),
                "candidate_win_rate_12h": round(mean(1.0 if row["favorable_12h"] else 0.0 for row in with_12h), 6) if with_12h else None,
                "candidate_expectancy_12h": round(mean(float(row["directional_12h_return"]) for row in with_12h), 8) if with_12h else None,
                "entry_context_complete_count": len(entry_complete),
                "trade_count": 0,
                "win_rate": None,
                "expectancy": None,
                "fail_closed_reason": "missing_mss_cisd_displacement_pda_entry_context",
            }
        )
    return summary


def main() -> int:
    packet = json.loads(SOURCE_PACKET.read_text())
    candle_cache: dict[Path, dict[datetime, dict[str, float]]] = {}
    labelled: list[dict[str, Any]] = []
    provider_pair_readback = []
    for item in packet.get("provider_readbacks", []):
        provider_pair_readback.append(
            {
                "family": item.get("family"),
                "base_symbol": item.get("base_symbol"),
                "comparison_symbol": item.get("comparison_symbol"),
                "relationship_type": item.get("relationship_type"),
                "timeframe": item.get("timeframe"),
                "session": item.get("session"),
                "provider": item.get("provider"),
                "provider_data_acquired": item.get("provider_data_acquired"),
                "aligned_rows": item.get("aligned_rows"),
                "recent_correlation": item.get("recent_correlation"),
                "smt_event_count": item.get("smt_event_count"),
                "fail_closed_reason": item.get("fail_closed_reason"),
            }
        )
    for row in packet["rows"]:
        if row.get("smt_signal") == "none" or not row.get("event_time"):
            continue
        path = provider_file(row)
        if path not in candle_cache:
            candle_cache[path] = candles_by_time(path)
        ret6 = horizon_return(candle_cache[path], str(row["event_time"]), 6)
        ret12 = horizon_return(candle_cache[path], str(row["event_time"]), 12)
        entry_context_complete = (
            parse_bool(row.get("mss_or_cisd_confirmed"))
            and parse_bool(row.get("displacement_confirmed"))
            and parse_bool(row.get("near_pd_array"))
            and str(row.get("pd_array_type") or "none") != "none"
        )
        output = {
            **{field: row.get(field) for field in ROW_FIELDS if field in row},
            "forward_6h_return": round(ret6, 8) if ret6 is not None else "",
            "forward_12h_return": round(ret12, 8) if ret12 is not None else "",
            "directional_6h_return": round(directional_return(str(row["smt_signal"]), ret6), 8) if ret6 is not None else "",
            "directional_12h_return": round(directional_return(str(row["smt_signal"]), ret12), 8) if ret12 is not None else "",
            "favorable_6h": directional_return(str(row["smt_signal"]), ret6) > 0 if ret6 is not None else "",
            "favorable_12h": directional_return(str(row["smt_signal"]), ret12) > 0 if ret12 is not None else "",
            "mss_or_cisd_confirmed": parse_bool(row.get("mss_or_cisd_confirmed")),
            "displacement_confirmed": parse_bool(row.get("displacement_confirmed")),
            "near_pd_array": parse_bool(row.get("near_pd_array")),
            "pd_array_type": row.get("pd_array_type") or "none",
            "entry_context_complete": entry_context_complete,
            "actionable": False,
            "fail_closed_reason": "missing_mss_cisd_displacement_pda_entry_context",
        }
        labelled.append(output)

    regime_summary = summarize_by(labelled, "regime_bucket")
    pair_summary = summarize_by(labelled, "comparison_symbol")
    with_6h = [row for row in labelled if row["forward_6h_return"] != ""]
    with_12h = [row for row in labelled if row["forward_12h_return"] != ""]
    summary = {
        "factor_name": "smt_full_coverage_outcome_entry_context_v1",
        "factor_version": "2026-05-12",
        "source_observation_root": str(SOURCE.relative_to(REPO)),
        "source_packet": str(SOURCE_PACKET.relative_to(REPO)),
        "branch_path_contract": packet["branch_path_contract"],
        "coverage_target": packet["coverage_target"],
        "aggregate": {
            "event_count": len(labelled),
            "outcome_6h_count": len(with_6h),
            "outcome_12h_count": len(with_12h),
            "required_provider_pair_count": len(provider_pair_readback),
            "required_provider_pairs_with_data": sum(1 for row in provider_pair_readback if row["provider_data_acquired"]),
            "required_provider_pairs_without_smt_event": sum(1 for row in provider_pair_readback if int(row.get("smt_event_count") or 0) == 0),
            "inverse_relationship_event_count": sum(1 for row in labelled if row.get("relationship_type") == "negative"),
            "inverse_normalized_event_count": sum(1 for row in labelled if row.get("normalized_for_inverse_correlation")),
            "candidate_win_rate_6h": round(mean(1.0 if row["favorable_6h"] else 0.0 for row in with_6h), 6) if with_6h else None,
            "candidate_expectancy_6h": round(mean(float(row["directional_6h_return"]) for row in with_6h), 8) if with_6h else None,
            "candidate_win_rate_12h": round(mean(1.0 if row["favorable_12h"] else 0.0 for row in with_12h), 6) if with_12h else None,
            "candidate_expectancy_12h": round(mean(float(row["directional_12h_return"]) for row in with_12h), 8) if with_12h else None,
            "entry_context_complete_count": sum(1 for row in labelled if row["entry_context_complete"]),
        },
        "per_regime_statistics": {row["regime_bucket"]: row for row in regime_summary},
        "provider_pair_readback": provider_pair_readback,
        "pair_summary": pair_summary,
        "quality_gate": {
            "outcome_labels_present": len(with_6h) > 0,
            "entry_context_complete": False,
            "learning_quality_weight": 0.0,
            "auto_quant_dispatch_allowed": False,
            "pre_bayes_filter_allowed": False,
            "bbn_learning_allowed": False,
            "catboost_learning_allowed": False,
            "execution_tree_branch_weight_update_allowed": False,
            "promotion_allowed": False,
            "trade_usable": False,
            "fail_closed_reason": "forward_outcomes_exist_but_mss_cisd_displacement_pda_entry_context_missing",
        },
    }

    write_csv(ROOT / "summaries/smt_full_coverage_outcome_entry_context_rows.csv", labelled, ROW_FIELDS)
    write_csv(ROOT / "summaries/smt_full_coverage_outcome_entry_context_regime_summary.csv", regime_summary)
    write_csv(ROOT / "summaries/smt_full_coverage_outcome_entry_context_pair_summary.csv", pair_summary)
    (ROOT / "materials/smt_full_coverage_outcome_entry_context_packet.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary["aggregate"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
