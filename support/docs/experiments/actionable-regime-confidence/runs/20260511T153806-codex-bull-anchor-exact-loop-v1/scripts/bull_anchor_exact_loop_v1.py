#!/usr/bin/env python3
"""Materialize the positive Bull-anchor loop from existing exact-source rows."""

from __future__ import annotations

import csv
import json
from pathlib import Path


RUN_ID = "20260511T153806+0800-codex-bull-anchor-exact-loop-v1"
RUN_ROOT = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T153806-codex-bull-anchor-exact-loop-v1"
)
OUT_DIR = RUN_ROOT / "bull-anchor-loop"
CHECK_DIR = RUN_ROOT / "checks"

EXACT_ROWS = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T141910-codex-exact-1h-source-universe-expansion-v1/"
    "exact-1h-universe/exact_1h_source_universe_expansion_v1_rows.csv"
)
RARE_ROWS = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T144604-codex-pfe-tsla-rare-root-exact-loop-v1/"
    "rare-root-loop/pfe_tsla_rare_root_exact_loop_v1_rows.csv"
)

SELECTED_BULL_PAIR = ("GE", "GS")
ACTIVE_ROOTS = ("Bull", "Bear", "Sideways", "Crisis")


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as handle:
        return list(csv.DictReader(handle))


def is_true(value: str) -> bool:
    return value.strip().lower() == "true"


def write_csv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)

    exact_rows = read_rows(EXACT_ROWS)
    rare_rows = read_rows(RARE_ROWS)

    selected_rows = [
        row
        for row in exact_rows
        if row["instrument"] in SELECTED_BULL_PAIR
    ]
    accepted_bull_rows = [
        row
        for row in selected_rows
        if row["root"] == "Bull"
        and is_true(row["accepted_95_strict_ticker_root_attachment"])
    ]
    non_target_blocked_rows = [
        row
        for row in selected_rows
        if not is_true(row["accepted_95_strict_ticker_root_attachment"])
    ]

    rare_accepted_rows = [
        row
        for row in rare_rows
        if is_true(row["accepted_95_strict_ticker_root_attachment"])
    ]
    combined_accepted = accepted_bull_rows + rare_accepted_rows
    combined_roots = sorted({row["root"] for row in combined_accepted})

    summary = {
        "run_id": RUN_ID,
        "gate_result": "bull_anchor_exact_loop_v1=accepted2_bull_anchor_no_new_download",
        "selected_pair": list(SELECTED_BULL_PAIR),
        "purpose": "close abundant Bull exact-source supply after the PFE+TSLA rare-root loop already closed Bear/Sideways/Crisis",
        "source_exact_rows": str(EXACT_ROWS),
        "source_rare_root_rows": str(RARE_ROWS),
        "selected_pair_rows": len(selected_rows),
        "accepted_bull_rows": len(accepted_bull_rows),
        "non_target_blocked_rows": len(non_target_blocked_rows),
        "accepted_roots_this_loop": sorted({row["root"] for row in accepted_bull_rows}),
        "combined_with_pfe_tsla_covered_roots": combined_roots,
        "combined_price_root_supply_covers_all_active_mainregimev2_roots": combined_roots == sorted(ACTIVE_ROOTS),
        "full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "trade_usable": False,
        "direct_manipulation_lane_state": "separate_waiting_for_external_row_level_positive_and_matched_negative_exports",
        "next_action": "run a completion audit that separates MainRegimeV2 price-root evidence from the direct Manipulation row-intake blocker; do not continue broad negative source sweeps",
        "accepted_rows": accepted_bull_rows,
        "combined_accepted_root_supply": [
            {
                "source_loop": "bull_anchor_exact_loop_v1"
                if row in accepted_bull_rows
                else "pfe_tsla_rare_root_exact_loop_v1",
                "instrument": row["instrument"],
                "root": row["root"],
                "timeframe": row["timeframe"],
                "calibration_2024_support": row["calibration_2024_support"],
                "calibration_2024_wilson95_lcb": row["calibration_2024_wilson95_lcb"],
                "heldout_time_2025_support": row["heldout_time_2025_support"],
                "heldout_time_2025_wilson95_lcb": row["heldout_time_2025_wilson95_lcb"],
            }
            for row in combined_accepted
        ],
    }

    fieldnames = list(exact_rows[0].keys())
    write_csv(OUT_DIR / "bull_anchor_exact_loop_v1_rows.csv", selected_rows, fieldnames)

    combined_fieldnames = [
        "source_loop",
        "instrument",
        "root",
        "timeframe",
        "calibration_2024_support",
        "calibration_2024_wilson95_lcb",
        "heldout_time_2025_support",
        "heldout_time_2025_wilson95_lcb",
    ]
    write_csv(
        OUT_DIR / "bull_anchor_exact_loop_v1_combined_root_supply.csv",
        summary["combined_accepted_root_supply"],
        combined_fieldnames,
    )

    json_path = OUT_DIR / "bull_anchor_exact_loop_v1.json"
    json_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")

    accepted_table = "\n".join(
        "| `{instrument}` | `{root}` | {calibration_2024_support} | {calibration_2024_wilson95_lcb} | {heldout_time_2025_support} | {heldout_time_2025_wilson95_lcb} |".format(
            **row
        )
        for row in accepted_bull_rows
    )
    if not accepted_table:
        accepted_table = "| N/A | N/A | N/A | N/A | N/A | N/A |"

    combined_table = "\n".join(
        "| `{source_loop}` | `{instrument}` | `{root}` | {calibration_2024_support} | {calibration_2024_wilson95_lcb} | {heldout_time_2025_support} | {heldout_time_2025_wilson95_lcb} |".format(
            **row
        )
        for row in summary["combined_accepted_root_supply"]
    )

    report = f"""# Bull Anchor Exact Loop v1

Run ID: `{RUN_ID}`

This loop follows the positive next step left by the PFE/TSLA rare-root loop. It does not perform another source sweep.
It consumes the existing accepted strict exact-source `1h` rows from `141910`.

## Result

- Selected pair: `GE+GS`.
- Purpose: close abundant `Bull` exact-source supply after `PFE+TSLA` already closed `Bear`, `Sideways`, and `Crisis`.
- Selected pair rows: `{len(selected_rows)}`.
- Accepted strict Bull rows: `{len(accepted_bull_rows)}`.
- Non-target blocked rows retained: `{len(non_target_blocked_rows)}`.
- Accepted roots this loop: `{", ".join(summary["accepted_roots_this_loop"])}`.
- Combined with `PFE+TSLA` rare-root loop, covered active `MainRegimeV2` price roots: `{", ".join(combined_roots)}`.
- Full objective achieved: `false`.
- Runtime code changed: `false`.
- Thresholds relaxed: `false`.
- Raw data committed: `false`.
- Trade usable: `false`.
- Gate result: `bull_anchor_exact_loop_v1=accepted2_bull_anchor_no_new_download`.

## Accepted Bull Rows

| Ticker | Root | 2024 Cal Support | 2024 Cal Wilson95 | 2025 Heldout Support | 2025 Heldout Wilson95 |
|---|---|---:|---:|---:|---:|
{accepted_table}

## Combined Price-Root Supply

| Source Loop | Ticker | Root | 2024 Cal Support | 2024 Cal Wilson95 | 2025 Heldout Support | 2025 Heldout Wilson95 |
|---|---|---|---:|---:|---:|---:|
{combined_table}

## Boundary

- This is positive `MainRegimeV2` price-root supply, not a direct `Manipulation` label.
- Direct `Manipulation` remains a separate row-intake lane waiting for external row-level positive and matched-negative exports.
- Do not spend the next active Board A loop on broad negative source sweeps; run a completion audit that separates price-root evidence from the direct row-intake blocker.
"""
    (OUT_DIR / "bull_anchor_exact_loop_v1.md").write_text(report)

    assertions = []
    assertions.append(("accepted_bull_rows_eq_2", len(accepted_bull_rows) == 2))
    assertions.append(("this_loop_only_bull", {row["root"] for row in accepted_bull_rows} == {"Bull"}))
    assertions.append(("rare_loop_closes_three_roots", {"Bear", "Sideways", "Crisis"}.issubset({row["root"] for row in rare_accepted_rows})))
    assertions.append(("combined_roots_cover_mainregimev2", combined_roots == sorted(ACTIVE_ROOTS)))
    assertions.append(("full_objective_not_claimed", summary["full_objective_achieved"] is False))
    assertions.append(("no_threshold_relaxation", summary["thresholds_relaxed"] is False))

    lines = [f"{name}: {'PASS' if passed else 'FAIL'}" for name, passed in assertions]
    (CHECK_DIR / "bull_anchor_exact_loop_v1_assertions.out").write_text("\n".join(lines) + "\n")

    if not all(passed for _, passed in assertions):
        raise SystemExit("assertion failure")


if __name__ == "__main__":
    main()
