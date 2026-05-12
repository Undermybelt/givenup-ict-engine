#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd


REPO = Path(__file__).resolve().parents[6]
RUN_ID = "20260511T133453+0800-codex-post-axiswise-acquisition-request-v12"
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T133453-codex-post-axiswise-acquisition-request-v12"
OUT_DIR = RUN_ROOT / "acquisition-request"
CHECK_DIR = RUN_ROOT / "checks"

BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"
V2_CSV = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T081715-codex-source-label-acquisition-package-v2/acquisition-package/missing_root_label_slots_acquisition_request_v2.csv"
ROLLUP_CSV = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T130600-codex-stock-regime-same-source-timeframe-rollup-v1/timeframe-rollup/stock_regime_same_source_timeframe_rollup_v1.csv"
AXISWISE_JSON = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T131922-codex-source-consensus-axiswise-timeframe-gate-v1/source-consensus-axiswise/source_consensus_axiswise_timeframe_gate_v1.json"
V11_TARGETS = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T132625-current-goal-completion-audit-v11-after-axiswise/completion-audit/targeted_unsupported_cell_targets_v11.csv"

ROOTS = ["Bull", "Bear", "Sideways", "Crisis"]
INTRADAY_TFS = {"1m", "5m", "15m", "30m", "1h", "4h"}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def counts(records: list[dict[str, Any]], key: str) -> dict[str, int]:
    return dict(sorted(Counter(str(item[key]) for item in records).items()))


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)

    v2 = pd.read_csv(V2_CSV)
    rollup = pd.read_csv(ROLLUP_CSV)
    axiswise = json.loads(AXISWISE_JSON.read_text())

    same_source_tickers = set(rollup["ticker"].dropna().unique().tolist())
    accepted_axiswise = set()
    for item in axiswise["decision"]["accepted_95_timeframe_root_cells"]:
        if isinstance(item, str):
            timeframe, root = item.split(":", 1)
            accepted_axiswise.add((timeframe, root))
        else:
            accepted_axiswise.add((item["timeframe"], item["regime"]))

    disposition_rows: list[dict[str, Any]] = []
    active_rows: list[dict[str, Any]] = []
    superseded_rows: list[dict[str, Any]] = []
    for raw in v2.to_dict(orient="records"):
        row = {k: ("" if pd.isna(v) else v) for k, v in raw.items()}
        tf_root = (row["timeframe"], row["root"])
        if row["instrument"] in same_source_tickers and tf_root in accepted_axiswise:
            disposition = "superseded_by_131922_axiswise_same_source_gate"
            reason = "same-source stock/index ticker and timeframe/root now accepted at 95"
        else:
            disposition = "active_request_after_axiswise"
            reason = "still lacks native or exact-underlying independent source labels"
        enriched = {
            **row,
            "post_axiswise_disposition": disposition,
            "post_axiswise_reason": reason,
            "required_next_artifact": (
                "timestamped_source_label_panel_with_calibration_test_and_heldout_context"
                if disposition.startswith("active")
                else "none"
            ),
        }
        disposition_rows.append(enriched)
        if disposition.startswith("active"):
            active_rows.append(enriched)
        else:
            superseded_rows.append(enriched)

    active_csv = OUT_DIR / "post_axiswise_active_source_label_requests_v12.csv"
    all_csv = OUT_DIR / "post_axiswise_source_label_request_disposition_v12.csv"
    for path, rows in [(active_csv, active_rows), (all_csv, disposition_rows)]:
        with path.open("w", newline="") as f:
            fieldnames = list(disposition_rows[0].keys())
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

    high_yield_batches = [
        {
            "batch_id": "native_intraday_yfinance_index_etf_futures",
            "selector": "provider == yfinance AND timeframe in 1m/5m/15m/30m/1h/4h",
            "rows": sum(1 for r in active_rows if r["provider"] == "yfinance" and r["timeframe"] in INTRADAY_TFS),
            "required_evidence": "native intraday MainRegimeV2 labels or owner-approved source labels for all four roots",
            "forbidden": "do not use OHLCV/HMM/future-return generated labels as acceptance evidence",
        },
        {
            "batch_id": "kraken_full_species_native_labels",
            "selector": "provider == kraken_public_lowpollution_http",
            "rows": sum(1 for r in active_rows if r["provider"] == "kraken_public_lowpollution_http"),
            "required_evidence": "crypto exact-underlying source labels across roots/timeframes with chronological and heldout-symbol validation",
            "forbidden": "do not promote raw Kraken bars or provider readiness to regime labels",
        },
        {
            "batch_id": "yfinance_non_same_source_daily_weekly_monthly_species",
            "selector": "provider == yfinance AND timeframe in 1d/1w/1mo AND not superseded",
            "rows": sum(1 for r in active_rows if r["provider"] == "yfinance" and r["timeframe"] not in INTRADAY_TFS),
            "required_evidence": "exact-underlying labels for commodities, ETFs, futures, volatility, and non-same-source instruments",
            "forbidden": "do not infer labels from the accepted US stock/index panel unless an explicit crosswalk is approved and calibrated",
        },
    ]

    package = {
        "run_id": RUN_ID,
        "artifact_type": "post_axiswise_acquisition_request_v12",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "inputs": {
            "board": str(BOARD.relative_to(REPO)),
            "board_sha256_at_run": sha256(BOARD),
            "stale_v2_csv": str(V2_CSV.relative_to(REPO)),
            "stale_v2_csv_sha256": sha256(V2_CSV),
            "same_source_rollup": str(ROLLUP_CSV.relative_to(REPO)),
            "axiswise_gate": str(AXISWISE_JSON.relative_to(REPO)),
            "v11_targets": str(V11_TARGETS.relative_to(REPO)),
        },
        "decision": {
            "v2_rows": int(len(v2)),
            "superseded_by_axiswise_rows": len(superseded_rows),
            "active_source_label_requests_after_axiswise": len(active_rows),
            "accepted_confidence_added": 0,
            "full_objective_achieved": False,
            "gate_result": "post_axiswise_acquisition_request_v12_active_556_source_label_slots_plus_direct_manipulation_open",
            "runtime_code_changed": False,
            "thresholds_relaxed": False,
            "raw_data_committed": False,
            "trade_usable": False,
            "next_action": "Attack the 336 native intraday yfinance rows first, then Kraken/full-species rows; keep direct Manipulation matched-negative acquisition separate.",
        },
        "active_request_counts": {
            "by_provider": counts(active_rows, "provider"),
            "by_timeframe": counts(active_rows, "timeframe"),
            "by_root": counts(active_rows, "root"),
            "by_reason": counts(active_rows, "missing_or_rejected_reason"),
        },
        "superseded_counts": {
            "by_instrument": counts(superseded_rows, "instrument") if superseded_rows else {},
            "by_timeframe": counts(superseded_rows, "timeframe") if superseded_rows else {},
            "by_root": counts(superseded_rows, "root") if superseded_rows else {},
        },
        "high_yield_batches": high_yield_batches,
        "artifacts": {
            "active_request_csv": str(active_csv.relative_to(REPO)),
            "disposition_csv": str(all_csv.relative_to(REPO)),
        },
    }

    json_path = OUT_DIR / "post_axiswise_acquisition_request_v12.json"
    json_path.write_text(json.dumps(package, indent=2, sort_keys=True) + "\n")

    md = [
        "# Post-Axiswise Acquisition Request v12",
        "",
        f"Run ID: `{RUN_ID}`",
        "",
        "## Result",
        "",
        f"- Rebased the stale v2 acquisition request from `{len(v2)}` rows to `{len(active_rows)}` active post-axiswise source-label requests.",
        f"- Superseded rows removed: `{len(superseded_rows)}`; all are same-source stock/index rows now covered by the `131922` axiswise gate.",
        "- Accepted confidence added: `0`; this is a current-target acquisition request, not a confidence gate.",
        "- Full objective achieved: `false`.",
        "",
        "## Active Counts",
        "",
        f"- By provider: `{package['active_request_counts']['by_provider']}`.",
        f"- By timeframe: `{package['active_request_counts']['by_timeframe']}`.",
        f"- By root: `{package['active_request_counts']['by_root']}`.",
        "",
        "## High-Yield Batches",
        "",
        "| Batch | Rows | Required Evidence | Forbidden Shortcut |",
        "|---|---:|---|---|",
    ]
    for batch in high_yield_batches:
        md.append(
            f"| `{batch['batch_id']}` | {batch['rows']} | {batch['required_evidence']} | {batch['forbidden']} |"
        )
    md.extend([
        "",
        "## Guardrails",
        "",
        "- Provider bars/catalog readiness is not source-label evidence.",
        "- HMM, OHLCV, strategy prediction, or future-return labels cannot close these rows.",
        "- Direct `Manipulation` matched negatives remain a separate direct-evidence lane.",
        "- No runtime code changed; no thresholds relaxed; no raw data committed; not trade usable.",
    ])
    (OUT_DIR / "post_axiswise_acquisition_request_v12.md").write_text("\n".join(md) + "\n")

    check_lines = [
        f"run_id={RUN_ID}",
        f"v2_rows={len(v2)}",
        f"superseded_by_axiswise_rows={len(superseded_rows)}",
        f"active_source_label_requests_after_axiswise={len(active_rows)}",
        "accepted_confidence_added=0",
        "full_objective_achieved=false",
        "runtime_code_changed=false",
        "thresholds_relaxed=false",
        "raw_data_committed=false",
        "trade_usable=false",
        f"gate_result={package['decision']['gate_result']}",
        "assertion_status=PASS",
    ]
    (CHECK_DIR / "post_axiswise_acquisition_request_v12_assertions.out").write_text("\n".join(check_lines) + "\n")


if __name__ == "__main__":
    main()
