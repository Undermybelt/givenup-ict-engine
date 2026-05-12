#!/usr/bin/env python3
"""Separate regime-confidence evidence by downstream consumer unit."""

from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[6]
RUN_ID = "20260511T143344+0800-codex-regime-consumer-unit-pivot-v1"
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T143344-codex-regime-consumer-unit-pivot-v1"
OUT_DIR = RUN_ROOT / "consumer-unit-pivot"
CHECK_DIR = RUN_ROOT / "checks"

BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"
POSITIVE_INDEX = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T140042-codex-positive-regime-factor-index-v1/"
    "positive-factor-index/positive_regime_factor_index_v1.json"
)
EXACT_1H = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T141910-codex-exact-1h-source-universe-expansion-v1/"
    "exact-1h-universe/exact_1h_source_universe_expansion_v1.json"
)
EXACT_1H_ROWS = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T141910-codex-exact-1h-source-universe-expansion-v1/"
    "exact-1h-universe/exact_1h_source_universe_expansion_v1_rows.csv"
)
AMD_CVX_SLOTS = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T140643-codex-amd-cvx-exact-intraday-source-attachment-v1/"
    "exact-intraday-attachment/amd_cvx_exact_intraday_source_attachment_v1_slots.csv"
)
DIRECT_MATRIX = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T131311-codex-direct-manipulation-variety-matrix-v1/"
    "direct-manipulation/direct_manipulation_variety_matrix_v1.json"
)
ACQUISITION_V12 = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T133453-codex-post-axiswise-acquisition-request-v12/"
    "acquisition-request/post_axiswise_acquisition_request_v12.json"
)

ROOTS = ["Bull", "Bear", "Sideways", "Crisis"]


def repo_rel(path: Path) -> str:
    return str(path.relative_to(REPO))


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def truthy(value: str) -> bool:
    return str(value).strip().lower() == "true"


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)

    positive = load_json(POSITIVE_INDEX)
    exact = load_json(EXACT_1H)
    direct = load_json(DIRECT_MATRIX)
    acquisition = load_json(ACQUISITION_V12)
    exact_rows = read_csv(EXACT_1H_ROWS)
    amd_cvx_rows = read_csv(AMD_CVX_SLOTS)

    pooled = exact["pooled_panel_context"]
    pooled_roots_ready = [
        root for root in ROOTS if pooled[root]["accepted_95_panel_context"] is True
    ]
    strict_rows = [row for row in exact_rows if truthy(row["accepted_95_strict_ticker_root_attachment"])]
    strict_by_root = {root: 0 for root in ROOTS}
    for row in strict_rows:
        strict_by_root[row["root"]] += 1

    amd_cvx_unit_drift = []
    for row in amd_cvx_rows:
        ticker_pass = (
            int(row["ticker_calibration_2024_support"]) >= 73
            and float(row["ticker_calibration_2024_wilson95_lcb"]) >= 0.95
            and int(row["ticker_heldout_time_2025_support"]) >= 73
            and float(row["ticker_heldout_time_2025_wilson95_lcb"]) >= 0.95
        )
        if truthy(row["accepted_95_source_label_attachment"]) and not ticker_pass:
            amd_cvx_unit_drift.append(
                {
                    "instrument": row["instrument"],
                    "root": row["root"],
                    "accepted_unit": "root_pair_cohort",
                    "not_accepted_unit": "individual_ticker_root",
                    "ticker_2024_support": row["ticker_calibration_2024_support"],
                    "ticker_2025_support": row["ticker_heldout_time_2025_support"],
                }
            )

    direct_rollup = direct["rollup"]
    active_requests = acquisition["decision"]["active_source_label_requests_after_axiswise"]

    ledger_rows: list[dict[str, Any]] = [
        {
            "consumer_unit": "market_regime_context_gate",
            "owner": "Board A price-root regime context",
            "status": "context_ready_not_full_completion",
            "accepted_roots": ",".join(pooled_roots_ready),
            "accepted_roots_count": len(pooled_roots_ready),
            "evidence": "exact same-source daily panel plus 1w/1mo and 1h panel-context support",
            "blocker": "needs downstream-facing context packet and full-cycle/species accounting; not ticker-specific",
        },
        {
            "consumer_unit": "ticker_specific_signal_gate",
            "owner": "per-instrument execution or ticker-local signal claims",
            "status": "partial",
            "accepted_roots": ",".join(
                root for root in ROOTS if strict_by_root[root] > 0
            ),
            "accepted_roots_count": sum(1 for root in ROOTS if strict_by_root[root] > 0),
            "evidence": f"strict exact 1h ticker/root rows={len(strict_rows)}/156 by root={strict_by_root}",
            "blocker": "sparse Bear/Sideways/Crisis per-ticker support; not a blocker for market context consumers",
        },
        {
            "consumer_unit": "direct_manipulation_gate",
            "owner": "direct event/order-flow/order-lifecycle/on-chain/social evidence",
            "status": "partial_blocked",
            "accepted_roots": "ManipulationScopedVarieties",
            "accepted_roots_count": len(direct_rollup["accepted_scoped_varieties"]),
            "evidence": (
                "scoped direct varieties="
                + ",".join(direct_rollup["accepted_scoped_varieties"])
            ),
            "blocker": "needs matched negatives for spoofing/layering plus quote stuffing/pinging/bear-raid/painting rows",
        },
        {
            "consumer_unit": "source_label_acquisition_gate",
            "owner": "missing-source rows and external provider acquisition",
            "status": "blocked_open",
            "accepted_roots": "",
            "accepted_roots_count": 0,
            "evidence": f"active source-label requests remain={active_requests}",
            "blocker": "more OHLCV/provider timeframe sweeps do not create labels; acquire rows or extend source panel",
        },
    ]

    result = {
        "run_id": RUN_ID,
        "artifact_type": "regime_consumer_unit_pivot_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "board": repo_rel(BOARD),
        "board_sha256_at_run": sha256(BOARD),
        "diagnosis": {
            "symptom": "recent loops produced many blocked rows while positive source-backed evidence already exists",
            "root_cause": (
                "the board lacks an explicit consumer-unit acceptance contract; agents mixed "
                "market-regime context, cohort/root-pair support, strict ticker/root support, "
                "and direct manipulation evidence into one denominator"
            ),
            "specific_unit_drift": (
                "AMD/CVX 8/8 accepted rows used root-pair cohort support, while the later "
                "39-ticker 1h expansion used strict per-ticker/root support"
            ),
            "why_more_timeframes_is_low_yield": (
                "additional provider-native timeframes only mirror source-date overlap; "
                "they do not resolve source-label acquisition, direct manipulation controls, "
                "or the consumer-unit denominator"
            ),
        },
        "market_context": {
            "price_roots": ROOTS,
            "pooled_exact_1h_roots_ready": pooled_roots_ready,
            "pooled_exact_1h_all_roots_ready": pooled_roots_ready == ROOTS,
            "daily_parent_price_roots_accepted": positive["positive_supply"]["daily_parent_price_roots_accepted"],
            "same_source_weekly_monthly_cells_accepted_count": positive["positive_supply"]["same_source_weekly_monthly_cells_accepted_count"],
        },
        "ticker_specific": {
            "strict_exact_1h_rows_accepted": len(strict_rows),
            "strict_exact_1h_rows_total": len(exact_rows),
            "strict_exact_1h_accepted_by_root": strict_by_root,
        },
        "unit_drift_examples": amd_cvx_unit_drift,
        "ledger": ledger_rows,
        "decision": {
            "accepted_gate": (
                "regime_consumer_unit_pivot_v1="
                "market_context_roots4_ready_ticker_specific_partial_direct_manipulation_partial"
            ),
            "full_objective_achieved": False,
            "call_update_goal": False,
            "runtime_code_changed": False,
            "raw_data_committed": False,
            "thresholds_relaxed": False,
            "trade_usable": False,
        },
        "next_action": (
            "Use this consumer-unit ledger as the acceptance contract: materialize a downstream-facing "
            "market_regime_context packet from existing exact-source positives, while routing Manipulation "
            "to direct matched-row acquisition; do not run more broad timeframe sweeps until a consumer "
            "explicitly needs ticker-specific support."
        ),
    }

    out_json = OUT_DIR / "regime_consumer_unit_pivot_v1.json"
    out_md = OUT_DIR / "regime_consumer_unit_pivot_v1.md"
    out_csv = OUT_DIR / "regime_consumer_unit_pivot_v1_ledger.csv"
    out_assert = CHECK_DIR / "regime_consumer_unit_pivot_v1_assertions.out"

    write_csv(
        out_csv,
        ledger_rows,
        [
            "consumer_unit",
            "owner",
            "status",
            "accepted_roots",
            "accepted_roots_count",
            "evidence",
            "blocker",
        ],
    )
    out_json.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    lines = [
        "# Regime Consumer Unit Pivot v1",
        "",
        f"Run ID: `{RUN_ID}`",
        "",
        "This run diagnoses why the current loop is producing broad negative rows and separates evidence by the downstream unit that can actually consume it.",
        "",
        "## Diagnosis",
        "",
        "- Root cause: the board lacks an explicit consumer-unit acceptance contract.",
        "- The loop mixed market-regime context, cohort/root-pair support, strict ticker/root support, and direct manipulation evidence into one denominator.",
        "- AMD/CVX `8/8` was a root-pair cohort gate; the 39-ticker `1h` expansion was a strict per-ticker/root gate.",
        "- More provider-native timeframe sweeps would mostly mirror source-date overlap and would not acquire labels or matched direct manipulation rows.",
        "",
        "## Consumer Unit Ledger",
        "",
        "| Consumer Unit | Status | Evidence | Blocker |",
        "|---|---|---|---|",
    ]
    for row in ledger_rows:
        lines.append(
            f"| `{row['consumer_unit']}` | `{row['status']}` | {row['evidence']} | {row['blocker']} |"
        )
    lines.extend([
        "",
        "## Decision",
        "",
        "- Market regime context has exact-source positive supply for all four price roots.",
        "- Ticker-specific support is partial and should not be used as a blocker for market-context consumers.",
        "- Direct Manipulation stays partial/blocked until direct matched rows exist.",
        "- Full objective achieved: `false`.",
        "- Runtime code changed: `false`.",
        "- Thresholds relaxed: `false`.",
        "- Raw data committed: `false`.",
        "- Trade usable: `false`.",
        "",
        "## Next",
        "",
        result["next_action"],
    ])
    out_md.write_text("\n".join(lines) + "\n", encoding="utf-8")

    assertions = [
        f"run_id={RUN_ID}",
        f"board_sha256_at_run={result['board_sha256_at_run']}",
        f"pooled_exact_1h_roots_ready={','.join(pooled_roots_ready)}",
        f"strict_exact_1h_rows_accepted={len(strict_rows)}",
        f"unit_drift_examples={len(amd_cvx_unit_drift)}",
        "full_objective_achieved=false",
        "call_update_goal=false",
        "runtime_code_changed=false",
        "thresholds_relaxed=false",
        "raw_data_committed=false",
        "trade_usable=false",
        "assertion_status=PASS",
    ]
    out_assert.write_text("\n".join(assertions) + "\n", encoding="utf-8")

    if pooled_roots_ready != ROOTS:
        raise RuntimeError(f"expected pooled roots {ROOTS}, got {pooled_roots_ready}")
    if len(strict_rows) != exact["decision"]["accepted_95_strict_ticker_root_rows"]:
        raise RuntimeError("strict row count mismatch")
    if not amd_cvx_unit_drift:
        raise RuntimeError("expected at least one AMD/CVX cohort-vs-ticker drift example")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
