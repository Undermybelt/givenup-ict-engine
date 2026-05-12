#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
from pathlib import Path
from statistics import mean


ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = ROOT.parents[0] / "20260512T210915+0800-codex-smt-entry-context-outcome-labeling-v1"
SRC_ROWS = SRC_ROOT / "materials/smt_entry_context_outcome_rows.csv"
OUT_PACKET = ROOT / "materials/smt_entry_context_density_triage_packet.json"
OUT_SUMMARY = ROOT / "summaries/smt_entry_context_density_triage_summary.csv"
OUT_BLOCKERS = ROOT / "summaries/smt_entry_context_blockers.csv"

REGIMES = ["trend", "range", "transition", "stress", "other"]
MIN_TRADE_COUNT_FOR_LEARNING = 30

SCENARIOS = {
    "mss_only": ("mss_or_cisd_confirmed",),
    "displacement_only": ("displacement_confirmed",),
    "pda_only": ("near_pd_array",),
    "mss_plus_pda": ("mss_or_cisd_confirmed", "near_pd_array"),
    "mss_plus_displacement": ("mss_or_cisd_confirmed", "displacement_confirmed"),
    "displacement_plus_pda": ("displacement_confirmed", "near_pd_array"),
    "strict_mss_displacement_pda": ("mss_or_cisd_confirmed", "displacement_confirmed", "near_pd_array"),
}


def as_bool(value: str) -> bool:
    return str(value).lower() == "true"


def as_float(value: str) -> float | None:
    if value in ("", "None", "null"):
        return None
    return float(value)


def scenario_rows(rows: list[dict], fields: tuple[str, ...]) -> list[dict]:
    out = []
    for row in rows:
        if row.get("smt_signal") == "none":
            continue
        if as_float(row.get("forward_return", "")) is None:
            continue
        if all(as_bool(row.get(field, "")) for field in fields):
            out.append(row)
    return out


def summarize(rows: list[dict]) -> dict:
    returns = [as_float(row["forward_return"]) for row in rows]
    returns = [value for value in returns if value is not None]
    hits = [as_bool(row["outcome_hit"]) for row in rows]
    return {
        "trade_count": len(rows),
        "win_rate": (sum(1 for hit in hits if hit) / len(hits)) if hits else None,
        "expectancy": mean(returns) if returns else None,
        "instrument_coverage": sorted({row["base_symbol"] for row in rows}),
    }


def main() -> int:
    rows = list(csv.DictReader(SRC_ROWS.open(newline="")))
    summary_rows: list[dict] = []
    packet_summary: dict[str, dict] = {}

    for scenario, fields in SCENARIOS.items():
        selected = scenario_rows(rows, fields)
        aggregate = summarize(selected)
        packet_summary[scenario] = {"aggregate": aggregate, "per_regime": {}}
        summary_rows.append({
            "scenario": scenario,
            "regime": "all",
            **aggregate,
            "instrument_coverage": ",".join(aggregate["instrument_coverage"]),
        })
        for regime in REGIMES:
            regime_rows = [row for row in selected if row.get("regime_bucket") == regime]
            stats = summarize(regime_rows)
            packet_summary[scenario]["per_regime"][regime] = stats
            summary_rows.append({
                "scenario": scenario,
                "regime": regime,
                **stats,
                "instrument_coverage": ",".join(stats["instrument_coverage"]),
            })

    blocker_counts = {
        "total_rows": len(rows),
        "signal_rows": sum(1 for row in rows if row.get("smt_signal") != "none"),
        "mss_or_cisd_true": sum(1 for row in rows if as_bool(row.get("mss_or_cisd_confirmed", ""))),
        "displacement_true": sum(1 for row in rows if as_bool(row.get("displacement_confirmed", ""))),
        "pda_true": sum(1 for row in rows if as_bool(row.get("near_pd_array", ""))),
        "strict_complete": packet_summary["strict_mss_displacement_pda"]["aggregate"]["trade_count"],
    }
    strict_count = blocker_counts["strict_complete"]
    best_relaxed = max(
        (item["aggregate"]["trade_count"], name)
        for name, item in packet_summary.items()
        if name != "strict_mss_displacement_pda"
    )
    missingness = {}
    for row in rows:
        reason = row.get("label_fail_closed_reason") or "entry_context_complete"
        missingness[reason] = missingness.get(reason, 0) + 1

    packet = {
        "source_root": str(SRC_ROOT),
        "branch_path": "Transition -> LiquiditySweepConfirmationFailure -> smt_divergence_confirmation_only -> smt_entry_context_density_triage_v1",
        "scenarios": packet_summary,
        "blocker_counts": blocker_counts,
        "missingness": missingness,
        "best_relaxed_scenario": {"scenario": best_relaxed[1], "trade_count": best_relaxed[0]},
        "quality_gate": {
            "quality_weight": 0.0,
            "downstream_allowed": False,
            "promotion_allowed": False,
            "trade_usable": False,
            "fail_closed_reason": "triage_only_no_label_mutation_and_strict_trade_count_below_learning_floor",
            "min_trade_count_for_learning": MIN_TRADE_COUNT_FOR_LEARNING,
            "strict_trade_count": strict_count,
        },
    }
    OUT_PACKET.write_text(json.dumps(packet, indent=2) + "\n")
    with OUT_SUMMARY.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=["scenario", "regime", "trade_count", "win_rate", "expectancy", "instrument_coverage"])
        writer.writeheader()
        writer.writerows(summary_rows)
    with OUT_BLOCKERS.open("w", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["blocker", "count"])
        for key, value in blocker_counts.items():
            writer.writerow([key, value])
        for key, value in sorted(missingness.items(), key=lambda item: (-item[1], item[0])):
            writer.writerow([f"missingness:{key}", value])

    print(json.dumps({
        "smt_entry_context_density_triage": "pass",
        "rows": len(rows),
        "signal_rows": blocker_counts["signal_rows"],
        "strict_trade_count": strict_count,
        "best_relaxed_scenario": best_relaxed[1],
        "best_relaxed_trade_count": best_relaxed[0],
        "downstream_allowed": False,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
