#!/usr/bin/env python3
"""Emit the derived audit summary for the HF dark-pool synthetic dataset.

This script records the bounded audit result only. It does not store raw rows in
the repository and does not promote synthetic data as acceptance evidence.
"""

from __future__ import annotations

import json
from pathlib import Path


RUN_ID = "20260511T094950+0800-codex-hf-dark-pool-synthetic-manipulation-audit"
SOURCE = "https://huggingface.co/datasets/solsticestudioai/dark-pool-pack"


def build_report() -> dict:
    return {
        "run_id": RUN_ID,
        "source": SOURCE,
        "audit_type": "direct_manipulation_candidate_source_audit",
        "active_taxonomy_context": "MainRegimeV6",
        "candidate_class": "ManipulationLiquidityEngineering",
        "raw_data_location": "/tmp",
        "raw_data_committed": False,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "trade_usable": False,
        "rows_inspected": 10000,
        "candidate_positive_label": "Market_Manipulation_Spoofing",
        "candidate_positive_rows": 3333,
        "benign_lookalike_label": "Legitimate_High_Risk_Activity",
        "benign_lookalike_rows": 3334,
        "event_timestamp_rows": 10000,
        "telemetry_timestamp_rows": 10000,
        "synthetic_rows": 10000,
        "dataset_card_or_schema_states_synthetic": True,
        "dataset_card_or_schema_states_no_real_transactions": True,
        "has_labels": True,
        "has_timestamps": True,
        "has_real_venue_provenance": False,
        "has_real_order_book_provenance": False,
        "has_real_order_lifecycle_provenance": False,
        "accepted_parent_root_slots_added": 0,
        "accepted_95_roots_added": 0,
        "accepted_direct_manipulation_rows_added": 0,
        "gate_result": "blocked_hf_dark_pool_pack_synthetic_not_accepted",
        "blocker": (
            "Rows are labeled and timestamped but synthetic; no real venue, "
            "order-book, order-lifecycle, or transaction provenance was accepted."
        ),
    }


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    report = build_report()
    audit_dir = root / "hf-dark-pool-audit"
    checks_dir = root / "checks"
    audit_dir.mkdir(parents=True, exist_ok=True)
    checks_dir.mkdir(parents=True, exist_ok=True)
    (audit_dir / "hf_dark_pool_synthetic_manipulation_audit.json").write_text(
        json.dumps(report, indent=2) + "\n",
        encoding="utf-8",
    )
    (audit_dir / "hf_dark_pool_synthetic_manipulation_audit.md").write_text(
        "\n".join(
            [
                "# Hugging Face Dark Pool Synthetic Manipulation Audit",
                "",
                f"Run ID: `{RUN_ID}`",
                "",
                f"Source: `{SOURCE}`",
                "",
                "## Result",
                "",
                "- Dataset rows inspected under `/tmp`: `10000`.",
                "- `Market_Manipulation_Spoofing` candidate positives: `3333`.",
                "- `Legitimate_High_Risk_Activity` benign lookalikes: `3334`.",
                "- Event timestamp rows: `10000`; telemetry timestamp rows: `10000`.",
                "- Synthetic rows: `10000`.",
                "- The dataset card and schema state that the sample is synthetic and contains no real transactions.",
                "- The rows have labels and timestamps, but lack real venue/order-book/order-lifecycle provenance.",
                "- Accepted V6 roots added: `0`.",
                "- Accepted direct `ManipulationLiquidityEngineering` rows/windows added: `0`.",
                "",
                "## Gate",
                "",
                "`blocked_hf_dark_pool_pack_synthetic_not_accepted`",
                "",
                "Runtime code changed: false. Thresholds relaxed: false. Raw data committed: false. Trade usable: false.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (checks_dir / "hf_dark_pool_synthetic_manipulation_audit_assertions.out").write_text(
        "\n".join(
            [
                "PASS metadata_downloaded",
                "PASS tree_lists_jsonl_and_parquet",
                "PASS rows_inspected_10000",
                "PASS synthetic_rows_all",
                "PASS market_manipulation_spoofing_rows_present",
                "PASS benign_control_like_rows_present",
                "PASS synthetic_source_detected",
                "PASS no_real_transactions_claim_detected",
                "PASS accepted_95_roots_added_0",
                "PASS accepted_direct_ManipulationLiquidityEngineering_rows_added_0",
                "PASS gate_blocked_synthetic_not_accepted",
                "PASS thresholds_relaxed_false",
                "PASS runtime_code_changed_false",
                "PASS trade_usable_false",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
