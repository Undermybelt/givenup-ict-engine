#!/usr/bin/env python3
"""Assert the R6 Oystacher owner market-data access preflight artifact."""

from __future__ import annotations

import csv
import json
from pathlib import Path


RUN_ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_ROOT = RUN_ROOT / "r6-oystacher-owner-market-data-access-preflight"
JSON_PATH = ARTIFACT_ROOT / "r6_oystacher_owner_market_data_access_preflight_v1.json"
SOURCE_CSV = ARTIFACT_ROOT / "r6_oystacher_owner_source_access_probe_v1.csv"


def require(condition: bool, label: str) -> None:
    if not condition:
        raise AssertionError(label)
    print(f"PASS {label}")


def main() -> None:
    data = json.loads(JSON_PATH.read_text())
    with SOURCE_CSV.open(newline="") as f:
        source_rows = list(csv.DictReader(f))

    require(data["run_id"] == "20260512T004507-codex-r6-oystacher-owner-market-data-access-preflight-v1", "run_id_matches")
    require(data["source_owned_normal_controls_acquired"] == 0, "source_owned_normal_controls_acquired_is_zero")
    require(data["cells_with_valid_controls"] == 0, "cells_with_valid_controls_zero")
    require(data["total_normal_control_shortfall"] == 1241, "total_normal_control_shortfall_is_1241")
    require(data["canonical_merge_allowed"] is False, "canonical_merge_blocked")
    require(data["downstream_rerun_allowed"] is False, "downstream_rerun_blocked")
    require(data["runtime_code_changed"] is False and data["shared_intake_mutated"] is False, "no_runtime_code_or_intake_mutation")
    require(data["gate_result"].endswith("owner_data_access_not_available_locally_no_controls_acquired"), "gate_result_owner_data_access_not_available_locally")
    require(all(int(row["source_owned_normal_controls_acquired"]) == 0 for row in source_rows), "source_csv_zero_controls")


if __name__ == "__main__":
    main()
