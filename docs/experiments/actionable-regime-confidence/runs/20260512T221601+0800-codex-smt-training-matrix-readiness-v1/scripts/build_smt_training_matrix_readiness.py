#!/usr/bin/env python3
import csv
import json
from collections import defaultdict
from pathlib import Path

RUN_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = RUN_ROOT.parents[4]
SOURCE_ROOT = REPO_ROOT / "docs/experiments/actionable-regime-confidence/runs/20260512T215037+0800-codex-smt-provider-window-event-alignment-expansion-v1"
SOURCE_ROWS = SOURCE_ROOT / "summaries/smt_provider_window_event_alignment_expansion_rows.csv"

REQUIRED_REGIMES = ["trend", "range", "transition", "stress", "other"]
REQUIRED_PAIR_LANES = [
    ("NQ", "ES"),
    ("NQ", "YM"),
    ("EURUSD", "GBPUSD"),
    ("EURUSD", "DXY"),
    ("XAUUSD", "XAGUSD"),
    ("XAUUSD", "DXY"),
    ("BTC", "ETH"),
]
MIN_TOTAL_TRAINABLE_ROWS = 30
MIN_PER_REGIME_TRAINABLE_ROWS = 10


def truthy(value):
    return str(value).strip().lower() in {"true", "1", "yes"}


def float_or_none(value):
    text = str(value).strip()
    if not text:
        return None
    return float(text)


def row_blockers(row):
    blockers = []
    if row.get("timeframe") != row.get("comparison_timeframe"):
        blockers.append("timeframe_mismatch")
    if not truthy(row.get("session_overlap")):
        blockers.append("session_not_overlapping")
    if row.get("relationship_type") == "uncertain":
        blockers.append("relationship_uncertain")
    if not row.get("base_level"):
        blockers.append("missing_base_level")
    if not row.get("comparison_level"):
        blockers.append("missing_comparison_level")
    if not truthy(row.get("same_event_window_confirmed")):
        blockers.append("not_same_liquidity_event_window")
    if not truthy(row.get("near_pd_array")):
        blockers.append("missing_pda_context")
    if not truthy(row.get("mss_or_cisd_confirmed")):
        blockers.append("missing_mss_or_cisd")
    if not truthy(row.get("displacement_confirmed")):
        blockers.append("missing_displacement")
    if row.get("forward_return", "").strip() == "" or row.get("outcome_hit", "").strip() == "":
        blockers.append("missing_forward_outcome")
    if truthy(row.get("actionable")):
        blockers.append("standalone_actionable_forbidden")
    if not truthy(row.get("strict_entry_context_complete")):
        source_reason = row.get("fail_closed_reason", "").strip()
        if source_reason and source_reason != "none":
            blockers.append(source_reason)
    return blockers


def summarize(rows, key_fn):
    buckets = defaultdict(list)
    for row in rows:
        buckets[key_fn(row)].append(row)
    out = {}
    for key, bucket in sorted(buckets.items()):
        trainable = [r for r in bucket if truthy(r["training_row_eligible"])]
        wins = [r for r in trainable if truthy(r["outcome_hit"])]
        returns = [float_or_none(r["forward_return"]) for r in trainable]
        returns = [r for r in returns if r is not None]
        out[key] = {
            "event_count": len(bucket),
            "smt_signal_count": sum(1 for r in bucket if r["smt_signal"] != "none"),
            "trainable_count": len(trainable),
            "win_rate": (len(wins) / len(trainable)) if trainable else None,
            "expectancy": (sum(returns) / len(returns)) if returns else None,
        }
    return out


def main():
    if not SOURCE_ROWS.exists():
        raise SystemExit(f"missing source rows: {SOURCE_ROWS}")

    rows = list(csv.DictReader(SOURCE_ROWS.open()))
    matrix = []
    for index, row in enumerate(rows, start=1):
        blockers = row_blockers(row)
        training_row_eligible = not blockers
        pair_lane = f"{row['base_symbol']}/{row['comparison_symbol']}"
        matrix.append(
            {
                "row_id": f"smt215037_{index:04d}",
                "base_symbol": row["base_symbol"],
                "comparison_symbol": row["comparison_symbol"],
                "pair_lane": pair_lane,
                "relationship_type": row["relationship_type"],
                "relationship_confidence": row["relationship_confidence"],
                "timeframe": row["timeframe"],
                "session": row["session"],
                "event_time": row["event_time"],
                "smt_signal": row["smt_signal"],
                "base_swing_type": row["base_swing_type"],
                "base_level": row["base_level"],
                "comparison_swing_type": row["comparison_swing_type"],
                "comparison_level": row["comparison_level"],
                "swept_side": row["swept_side"],
                "normalized_for_inverse_correlation": row["normalized_for_inverse_correlation"],
                "raw_comparison_swing_type": row["raw_comparison_swing_type"],
                "raw_comparison_level": row["raw_comparison_level"],
                "same_event_window_confirmed": row["same_event_window_confirmed"],
                "near_pd_array": row["near_pd_array"],
                "pd_array_type": row["pd_array_type"],
                "mss_or_cisd_confirmed": row["mss_or_cisd_confirmed"],
                "displacement_confirmed": row["displacement_confirmed"],
                "regime_bucket": row["regime_bucket"],
                "forward_return": row["forward_return"],
                "outcome_hit": row["outcome_hit"],
                "confirmation_role": row["confirmation_role"],
                "actionable": row["actionable"],
                "branch_path": row["branch_path"],
                "training_row_eligible": str(training_row_eligible),
                "training_blockers": "none" if training_row_eligible else ",".join(blockers),
            }
        )

    summaries_dir = RUN_ROOT / "summaries"
    materials_dir = RUN_ROOT / "materials"
    summaries_dir.mkdir(parents=True, exist_ok=True)
    materials_dir.mkdir(parents=True, exist_ok=True)

    matrix_path = summaries_dir / "smt_training_matrix_rows.csv"
    with matrix_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(matrix[0].keys()))
        writer.writeheader()
        writer.writerows(matrix)

    pair_summary = summarize(matrix, lambda r: r["pair_lane"])
    regime_summary = {regime: {"event_count": 0, "smt_signal_count": 0, "trainable_count": 0, "win_rate": None, "expectancy": None} for regime in REQUIRED_REGIMES}
    regime_summary.update(summarize(matrix, lambda r: r["regime_bucket"] or "other"))

    required_pair_summary = {}
    for base, comparison in REQUIRED_PAIR_LANES:
        key = f"{base}/{comparison}"
        current = pair_summary.get(key, {"event_count": 0, "smt_signal_count": 0, "trainable_count": 0, "win_rate": None, "expectancy": None})
        required_pair_summary[key] = current | {"covered": current["event_count"] > 0, "trainable_present": current["trainable_count"] > 0}

    total_trainable = sum(1 for row in matrix if truthy(row["training_row_eligible"]))
    per_regime_floor_met = all(regime_summary[regime]["trainable_count"] >= MIN_PER_REGIME_TRAINABLE_ROWS for regime in REQUIRED_REGIMES)
    pair_coverage_met = all(required_pair_summary[key]["covered"] and required_pair_summary[key]["trainable_present"] for key in required_pair_summary)
    inverse_rows = [row for row in matrix if truthy(row["normalized_for_inverse_correlation"])]
    inverse_auditable = all(row["raw_comparison_swing_type"] and row["raw_comparison_level"] for row in inverse_rows)
    standalone_actionable_count = sum(1 for row in matrix if truthy(row["actionable"]))

    packet = {
        "source_root": str(SOURCE_ROOT.relative_to(REPO_ROOT)),
        "training_matrix_rows": str(matrix_path.relative_to(REPO_ROOT)),
        "factor_name": "smt_relationship_resolver_same_event_confirmation_failure_v1",
        "definition": "SMT divergence is sibling-market same liquidity/swing event confirmation failure, not generic correlation or relative strength.",
        "confirmation_only": True,
        "standalone_actionable_allowed": False,
        "counts": {
            "rows": len(matrix),
            "smt_signal_rows": sum(1 for row in matrix if row["smt_signal"] != "none"),
            "training_row_eligible": total_trainable,
            "inverse_normalized_rows": len(inverse_rows),
            "standalone_actionable_count": standalone_actionable_count,
        },
        "required_pair_summary": required_pair_summary,
        "per_regime_statistics": regime_summary,
        "quality_gate": {
            "min_total_trainable_rows": MIN_TOTAL_TRAINABLE_ROWS,
            "min_per_regime_trainable_rows": MIN_PER_REGIME_TRAINABLE_ROWS,
            "total_learning_floor_met": total_trainable >= MIN_TOTAL_TRAINABLE_ROWS,
            "per_regime_learning_floor_met": per_regime_floor_met,
            "pair_coverage_met": pair_coverage_met,
            "inverse_normalization_auditable": inverse_auditable,
            "standalone_actionable_count": standalone_actionable_count,
            "downstream_allowed": total_trainable >= MIN_TOTAL_TRAINABLE_ROWS and per_regime_floor_met and pair_coverage_met and inverse_auditable and standalone_actionable_count == 0,
            "fail_closed_reason": "insufficient_pair_and_per_regime_strict_entry_training_rows",
        },
    }

    (materials_dir / "smt_training_matrix_readiness_packet.json").write_text(json.dumps(packet, indent=2) + "\n")

    with (summaries_dir / "smt_training_matrix_pair_summary.csv").open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["pair_lane", "event_count", "smt_signal_count", "trainable_count", "win_rate", "expectancy", "covered", "trainable_present"])
        writer.writeheader()
        for pair, data in required_pair_summary.items():
            writer.writerow({"pair_lane": pair, **data})

    with (summaries_dir / "smt_training_matrix_per_regime.csv").open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["regime_bucket", "event_count", "smt_signal_count", "trainable_count", "win_rate", "expectancy"])
        writer.writeheader()
        for regime in REQUIRED_REGIMES:
            writer.writerow({"regime_bucket": regime, **regime_summary[regime]})

    print(json.dumps(packet["counts"] | packet["quality_gate"], sort_keys=True))


if __name__ == "__main__":
    main()
