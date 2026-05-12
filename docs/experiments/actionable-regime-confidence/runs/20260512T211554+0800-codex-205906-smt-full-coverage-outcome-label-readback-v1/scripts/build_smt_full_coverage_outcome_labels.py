#!/usr/bin/env python3
import csv
import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[4]
SOURCE = REPO / "docs/experiments/actionable-regime-confidence/runs/20260512T205906+0800-codex-smt-full-coverage-provider-observation-v2"
ROWS_CSV = SOURCE / "materials/smt_provider_observation_rows.csv"
PROVIDER_DIR = SOURCE / "provider-data"
OUT_DIR = ROOT / "summaries"

BRANCH_PATH = "Transition -> LiquiditySweepConfirmationFailure -> smt_divergence_confirmation_only -> smt_full_coverage_outcome_label_readback:v1"


def parse_time(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def load_provider_rows() -> dict[tuple[str, str, str], list[dict]]:
    by_key: dict[tuple[str, str, str], list[dict]] = {}
    for path in PROVIDER_DIR.glob("*.json"):
        data = json.loads(path.read_text())
        spec = data["spec"]
        rows = sorted(data.get("base_rows") or [], key=lambda row: row["time"])
        key = (spec["base_symbol"], spec["comparison_symbol"], spec["timeframe"])
        by_key[key] = rows
    return by_key


def direction_sign(signal: str) -> int:
    if signal == "bullish_smt":
        return 1
    if signal == "bearish_smt":
        return -1
    return 0


def mean(values: list[float]) -> float | None:
    if not values:
        return None
    return sum(values) / len(values)


def summarise(rows: list[dict], group_key: str, required_groups: list[str] | None = None) -> list[dict]:
    grouped: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        grouped[row[group_key]].append(row)
    names = sorted(set(grouped) | set(required_groups or []))
    summary = []
    for name in names:
        items = grouped.get(name, [])
        returns_6h = [float(row["forward_return_6_bars"]) for row in items if row["forward_return_6_bars"] != ""]
        returns_12h = [float(row["forward_return_12_bars"]) for row in items if row["forward_return_12_bars"] != ""]
        hits_6h = [int(row["directional_hit_6_bars"]) for row in items if row["directional_hit_6_bars"] != ""]
        hits_12h = [int(row["directional_hit_12_bars"]) for row in items if row["directional_hit_12_bars"] != ""]
        summary.append(
            {
                group_key: name,
                "event_count": len(items),
                "outcome_6_bar_count": len(hits_6h),
                "outcome_12_bar_count": len(hits_12h),
                "hit_rate_6_bars": mean(hits_6h),
                "hit_rate_12_bars": mean(hits_12h),
                "expectancy_6_bars": mean(returns_6h),
                "expectancy_12_bars": mean(returns_12h),
            }
        )
    return summary


def main() -> int:
    provider_rows = load_provider_rows()
    event_rows = []
    missing = 0

    with ROWS_CSV.open(newline="") as handle:
        for source_row in csv.DictReader(handle):
            if source_row["smt_signal"] not in {"bullish_smt", "bearish_smt"}:
                continue
            key = (source_row["base_symbol"], source_row["comparison_symbol"], source_row["timeframe"])
            rows = provider_rows.get(key) or []
            time_index = {row["time"]: idx for idx, row in enumerate(rows)}
            event_time = source_row["event_time"]
            idx = time_index.get(event_time)
            if idx is None:
                missing += 1
                continue

            close = float(rows[idx]["close"])
            sign = direction_sign(source_row["smt_signal"])
            out = {
                "base_symbol": source_row["base_symbol"],
                "comparison_symbol": source_row["comparison_symbol"],
                "relationship_type": source_row["relationship_type"],
                "timeframe": source_row["timeframe"],
                "session": source_row["session"],
                "event_time": event_time,
                "smt_signal": source_row["smt_signal"],
                "base_swing_type": source_row["base_swing_type"],
                "comparison_swing_type": source_row["comparison_swing_type"],
                "base_level": source_row["base_level"],
                "comparison_level": source_row["comparison_level"],
                "regime_bucket": source_row["regime_bucket"],
                "provider_provenance": source_row["provider_provenance"],
                "branch_path": BRANCH_PATH,
                "mss_or_cisd_confirmed": "false",
                "displacement_confirmed": "false",
                "pda_entry_model_confirmed": "false",
                "actionable": "false",
            }
            for horizon in (3, 6, 12):
                target_idx = idx + horizon
                if target_idx >= len(rows):
                    out[f"forward_return_{horizon}_bars"] = ""
                    out[f"directional_hit_{horizon}_bars"] = ""
                    continue
                future_close = float(rows[target_idx]["close"])
                forward_return = (future_close - close) / close
                out[f"forward_return_{horizon}_bars"] = f"{forward_return:.10f}"
                out[f"directional_hit_{horizon}_bars"] = "1" if forward_return * sign > 0 else "0"
            event_rows.append(out)

    event_rows.sort(key=lambda row: (row["base_symbol"], row["comparison_symbol"], row["event_time"]))
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    event_csv = OUT_DIR / "smt_full_coverage_outcome_labels.csv"
    fieldnames = list(event_rows[0].keys()) if event_rows else [
        "base_symbol",
        "comparison_symbol",
        "event_time",
        "branch_path",
    ]
    with event_csv.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(event_rows)

    regime_summary = summarise(event_rows, "regime_bucket", ["trend", "range", "transition", "stress", "other"])
    provider_summary = summarise(event_rows, "provider_provenance")
    pair_summary = summarise(event_rows, "comparison_symbol")

    for filename, rows in [
        ("smt_full_coverage_outcome_regime_summary.csv", regime_summary),
        ("smt_full_coverage_outcome_provider_summary.csv", provider_summary),
        ("smt_full_coverage_outcome_pair_summary.csv", pair_summary),
    ]:
        path = OUT_DIR / filename
        with path.open("w", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()) if rows else ["empty"])
            writer.writeheader()
            writer.writerows(rows)

    hits_6h = [int(row["directional_hit_6_bars"]) for row in event_rows if row["directional_hit_6_bars"] != ""]
    rets_6h = [float(row["forward_return_6_bars"]) for row in event_rows if row["forward_return_6_bars"] != ""]
    summary = {
        "source_root": str(SOURCE),
        "branch_path": BRANCH_PATH,
        "event_count": len(event_rows),
        "missing_event_time_count": missing,
        "outcome_6_bar_count": len(hits_6h),
        "hit_rate_6_bars": mean(hits_6h),
        "expectancy_6_bars": mean(rets_6h),
        "regime_summary": regime_summary,
        "provider_summary": provider_summary,
        "pair_summary": pair_summary,
        "mss_or_cisd_confirmed": False,
        "displacement_confirmed": False,
        "pda_entry_model_confirmed": False,
        "pre_bayes_filter_allowed": False,
        "bbn_learning_allowed": False,
        "catboost_learning_allowed": False,
        "execution_tree_branch_weight_update_allowed": False,
        "promotion_allowed": False,
        "trade_usable": False,
        "update_goal": False,
    }
    (OUT_DIR / "smt_full_coverage_outcome_label_readback_v1.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(f"event_count={len(event_rows)} outcome_6_bar_count={len(hits_6h)} hit_rate_6_bars={summary['hit_rate_6_bars']} promotion_allowed=False")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
