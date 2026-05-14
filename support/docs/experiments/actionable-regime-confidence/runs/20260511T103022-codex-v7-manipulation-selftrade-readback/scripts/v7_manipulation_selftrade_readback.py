#!/usr/bin/env python3
"""Map the Zenodo consecutive self-trade gate into ActionableRegimeRootV7."""

from __future__ import annotations

import json
import pathlib


RUN_ID = "20260511T103022+0800-codex-v7-manipulation-selftrade-readback"
RUN_ROOT = pathlib.Path(__file__).resolve().parents[1]
REPO_ROOT = RUN_ROOT.parents[4]
SOURCE_JSON = REPO_ROOT / "docs/experiments/actionable-regime-confidence/runs/20260511T102332-codex-zenodo-dex-consecutive-selftrade-gate/direct-gate/zenodo_dex_consecutive_selftrade_gate.json"
OUT_DIR = RUN_ROOT / "v7-readback"
CHECK_DIR = RUN_ROOT / "checks"


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)

    source = json.loads(SOURCE_JSON.read_text(encoding="utf-8"))
    accepted_slice = bool(source["accepted_direct_self_trade_slice_95"])
    min_lcb = float(source["min_calibration_test_positive_or_negative_wilson95_lcb"])
    min_pos = int(source["min_calibration_test_positive_support"])
    min_neg = int(source["min_calibration_test_negative_support"])

    out_json = OUT_DIR / "v7_manipulation_selftrade_readback.json"
    out_md = OUT_DIR / "v7_manipulation_selftrade_readback.md"
    checks = CHECK_DIR / "v7_manipulation_selftrade_readback_assertions.out"

    packet = {
        "run_id": RUN_ID,
        "active_taxonomy": "ActionableRegimeRootV7",
        "candidate_root": "ManipulationIntegrityEvent",
        "source_gate_run": "docs/experiments/actionable-regime-confidence/runs/20260511T102332-codex-zenodo-dex-consecutive-selftrade-gate/direct-gate/zenodo_dex_consecutive_selftrade_gate.json",
        "source_gate_result": source["gate_result"],
        "direct_slice": "wash_trade_self_trade",
        "accepted_direct_slice_95": accepted_slice,
        "rows_streamed_consecutive": source["rows_streamed_consecutive"],
        "positive_self_trade_rows": source["positive_self_trade_rows"],
        "negative_control_rows": source["negative_control_rows"],
        "minimum_calibration_test_positive_or_negative_wilson95_lcb": min_lcb,
        "minimum_calibration_test_positive_support": min_pos,
        "minimum_calibration_test_negative_support": min_neg,
        "accepted_v7_parent_roots_added": 0,
        "accepted_v7_root_slices_added": 1 if accepted_slice else 0,
        "accepted_direct_manipulation_integrity_event_rows_evaluated": source["accepted_direct_manipulation_rows_evaluated"] if accepted_slice else 0,
        "full_manipulation_integrity_event_root_complete": False,
        "full_v7_goal_achieved": False,
        "gate_result": "partial_v7_manipulation_integrity_event_selftrade_slice_95_full_root_blocked"
        if accepted_slice
        else "blocked_v7_manipulation_integrity_event_selftrade_slice_below_95",
        "raw_data_committed": False,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "trade_usable": False,
        "limitations": [
            "This maps only direct self-trade/wash-trade order-lifecycle evidence into V7 ManipulationIntegrityEvent.",
            "It does not complete every ManipulationIntegrityEvent mechanism or venue.",
            "It does not add BullExpansion, BearExpansion, ConsolidationBalance, or CrisisDislocation source labels.",
            "The full all-market/all-timeframe V7 objective remains blocked.",
        ],
        "next_action": (
            "Acquire or build V7 label panels and run unchanged 95%-99% chronological calibration separately "
            "for BullExpansion, BearExpansion, ConsolidationBalance, CrisisDislocation, and broader "
            "ManipulationIntegrityEvent mechanisms beyond self-trade."
        ),
    }
    out_json.write_text(json.dumps(packet, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    out_md.write_text(
        f"""# V7 Manipulation Self-Trade Readback

Run ID: `{RUN_ID}`

## Result

- Active taxonomy: `ActionableRegimeRootV7`.
- Candidate root: `ManipulationIntegrityEvent`.
- Accepted direct slice: `wash_trade_self_trade` = `{str(accepted_slice).lower()}`.
- Consecutive rows streamed in source gate: `{source["rows_streamed_consecutive"]}`.
- Minimum calibration/test positive-or-negative Wilson95 LCB: `{min_lcb}`.
- Minimum calibration/test positive support: `{min_pos}`.
- Minimum calibration/test negative support: `{min_neg}`.
- Accepted V7 parent roots added: `0`.
- Accepted V7 root slices added: `{1 if accepted_slice else 0}`.
- Gate result: `{packet["gate_result"]}`.

## Boundary

This is a partial direct slice for `ManipulationIntegrityEvent`; it does not
complete the full root or any price-action V7 root.
""",
        encoding="utf-8",
    )

    checks.write_text(
        "\n".join(
            [
                "PASS source_gate_json_read",
                f"PASS accepted_direct_slice_95={str(accepted_slice).lower()}",
                f"PASS min_wilson95_lcb={min_lcb}",
                f"PASS min_positive_support={min_pos}",
                f"PASS min_negative_support={min_neg}",
                "PASS accepted_v7_parent_roots_added=0",
                "PASS raw_data_committed=false",
                f"GATE {packet['gate_result']}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
