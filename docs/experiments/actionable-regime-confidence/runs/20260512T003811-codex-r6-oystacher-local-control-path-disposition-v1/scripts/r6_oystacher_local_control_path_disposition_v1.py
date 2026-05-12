#!/usr/bin/env python3
"""Disposition local CME/Databento paths for Oystacher normal controls.

This read-only artifact checks local paths surfaced during the R6 Oystacher
control search and records whether any can satisfy the current source-owned
normal-control contract.
"""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path


RUN_ID = "20260512T003811-codex-r6-oystacher-local-control-path-disposition-v1"
REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs" / RUN_ID
OUT = RUN_ROOT / "r6-oystacher-local-control-path-disposition"
CHECKS = RUN_ROOT / "checks"

CONTROL_REQUEST = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260512T003627-codex-r6-oystacher-control-contract-request-v1/"
    "r6-oystacher-control-contract-request/r6_oystacher_required_normal_control_cells_v1.csv"
)
CONTROL_PREFLIGHT = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260512T003443-codex-r6-oystacher-normal-control-availability-preflight-v1/"
    "r6-oystacher-normal-control-availability-preflight/"
    "r6_oystacher_normal_control_availability_preflight_v1.json"
)

LOCAL_PATHS = [
    Path("/Users/thrill3r/Downloads/external-data-sources/FinceptTerminal/fincept-qt/scripts/cme_data.py"),
    Path("/Users/thrill3r/nautilus_trader/tests/test_data/databento/esh4-glbx-mdp3-20231224.mbo.dbn.zst"),
    Path("/Users/thrill3r/nautilus_trader/tests/test_data/databento/esh4-glbx-mdp3-20231225.mbo.dbn.zst"),
    Path("/Users/thrill3r/nautilus_trader/tests/test_data/databento/historical_bars_catalog/databento/futures_mbp-1_2024-07-01T23-58_2024-07-02T00-02.dbn.zst"),
    Path("/Users/thrill3r/nautilus_trader/tests/test_data/databento/historical_bars_catalog/databento/futures_trades_2024-07-01T23-58_2024-07-02T00-02.dbn.zst"),
    Path("/Users/thrill3r/nautilus_trader/tests/test_data/xcme/6EH4.XCME_1min_bars_20240101_20240131.csv.gz"),
]


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO))
    except ValueError:
        return str(path)


def read_required_cells() -> list[dict[str, str]]:
    with CONTROL_REQUEST.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def classify_path(path: Path) -> dict[str, str]:
    name = path.name.lower()
    exists = path.exists()
    if "cme_data.py" in name:
        data_kind = "cme_public_aggregate_api_wrapper"
        rejection = "aggregate_settlement_volume_open_interest_or_delayed_quotes_only_not_order_lifecycle_normal_controls"
    elif name.endswith(".mbo.dbn.zst"):
        data_kind = "databento_mbo_sample"
        rejection = "sample_test_data_modern_esh4_only_not_oystacher_2011_2014_multi_symbol_source_owned_controls"
    elif "mbp" in name or "trades" in name:
        data_kind = "databento_book_or_trade_sample"
        rejection = "sample_modern_market_data_not_labeled_normal_controls_and_not_oystacher_cells"
    elif name.endswith(".csv.gz"):
        data_kind = "xcme_bar_sample"
        rejection = "one_minute_bars_are_ohlcv_proxy_not_order_lifecycle_normal_controls"
    else:
        data_kind = "unknown_local_candidate"
        rejection = "not_mapped_to_required_oystacher_control_contract"
    return {
        "path": str(path),
        "exists": str(exists).lower(),
        "data_kind": data_kind,
        "valid_source_owned_normal_control": "false",
        "canonical_merge_allowed": "false",
        "rejection_reason": rejection,
    }


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)
    for required in [CONTROL_REQUEST, CONTROL_PREFLIGHT]:
        if not required.exists():
            raise FileNotFoundError(required)

    required_cells = read_required_cells()
    candidates = [classify_path(path) for path in LOCAL_PATHS]
    valid_candidates = [row for row in candidates if row["valid_source_owned_normal_control"] == "true"]
    cell_rows: list[dict[str, object]] = []
    for row in required_cells:
        out_row = dict(row)
        out_row["new_valid_local_controls_found"] = 0
        out_row["new_valid_local_controls_shortfall_after_disposition"] = row.get("valid_normal_control_shortfall", "73")
        out_row["decision_after_disposition"] = "still_needs_source_owned_normal_controls_or_explicit_flip_control_approval"
        cell_rows.append(out_row)

    created_at = datetime.now(timezone.utc).isoformat()
    gate = "r6_oystacher_local_control_path_disposition_v1=no_local_path_satisfies_source_owned_normal_control_contract"
    result = {
        "run_id": RUN_ID,
        "created_at_utc": created_at,
        "gate_result": gate,
        "control_request": rel(CONTROL_REQUEST),
        "control_preflight": rel(CONTROL_PREFLIGHT),
        "local_paths_checked": len(candidates),
        "existing_paths_checked": sum(1 for row in candidates if row["exists"] == "true"),
        "valid_source_owned_normal_controls_found": len(valid_candidates),
        "required_cells": len(required_cells),
        "required_cells_still_short": len(required_cells),
        "canonical_merge_allowed": False,
        "downstream_chain_rerun": False,
        "accepted_rows_added": 0,
        "new_confidence_gate": False,
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "shared_intake_mutated": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "external_requests_sent": False,
        "trade_usable": False,
    }

    candidate_csv = OUT / "r6_oystacher_local_control_path_candidates_v1.csv"
    cells_csv = OUT / "r6_oystacher_local_control_required_cells_v1.csv"
    json_path = OUT / "r6_oystacher_local_control_path_disposition_v1.json"
    report_path = OUT / "r6_oystacher_local_control_path_disposition_v1.md"
    assertions_path = CHECKS / "r6_oystacher_local_control_path_disposition_v1_assertions.out"

    write_csv(
        candidate_csv,
        candidates,
        ["path", "exists", "data_kind", "valid_source_owned_normal_control", "canonical_merge_allowed", "rejection_reason"],
    )
    write_csv(
        cells_csv,
        cell_rows,
        list(cell_rows[0].keys()) if cell_rows else ["axis", "bucket"],
    )
    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report_path.write_text(
        "\n".join([
            "# R6 Oystacher Local Control Path Disposition v1",
            "",
            f"- Run id: `{RUN_ID}`.",
            f"- Gate result: `{gate}`.",
            f"- Local paths checked: `{len(candidates)}`; existing paths checked: `{result['existing_paths_checked']}`.",
            "- Fincept CME path is aggregate public market data only: settlements, volume, open interest, delayed quotes, product/calendar metadata.",
            "- Nautilus/Databento paths are sample/test data or bars/trades from modern ES/other contracts, not Oystacher 2011-2014 multi-symbol source-owned normal controls.",
            "- Valid source-owned normal controls found: `0`.",
            f"- Required Oystacher normal-control cells still short: `{len(required_cells)}`.",
            "- Canonical merge allowed: `false`; downstream verifier/provider/Auto-Quant/pre-Bayes/BBN/CatBoost/execution-tree rerun: `false`.",
            "- Accepted rows added: `0`; strict full objective achieved: `false`; `update_goal=false`.",
            "- Runtime code changed: `false`; shared intake mutated: `false`; thresholds relaxed: `false`; raw data committed: `false`; external requests sent: `false`; trade usable: `false`.",
            "",
            "Artifacts:",
            f"- JSON: `{rel(json_path)}`",
            f"- Candidate CSV: `{rel(candidate_csv)}`",
            f"- Required cells CSV: `{rel(cells_csv)}`",
            f"- Assertions: `{rel(assertions_path)}`",
            "",
            "Next:",
            "- Keep the Oystacher rows isolated. Either obtain explicit approval for RECAP/PACER provenance plus FLIP-as-control, or supply independent source-owned normal controls for all required cells before canonical merge and full-chain rerun.",
        ]) + "\n",
        encoding="utf-8",
    )
    assertions_path.write_text(
        "\n".join([
            f"gate_result={gate}",
            f"local_paths_checked={len(candidates)}",
            f"existing_paths_checked={result['existing_paths_checked']}",
            "valid_source_owned_normal_controls_found=0",
            f"required_cells_still_short={len(required_cells)}",
            "canonical_merge_allowed=False",
            "downstream_chain_rerun=False",
            "shared_intake_mutated=False",
            "strict_full_objective_achieved=False",
            "update_goal=False",
        ]) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
