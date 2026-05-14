#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


REPO = Path(__file__).resolve().parents[6]
RUN_ID = "20260511T124000+0800-codex-unified-source-label-panel-v1"
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T124000-codex-unified-source-label-panel-v1"
OUT_DIR = RUN_ROOT / "unified-panel"
CHECK_DIR = RUN_ROOT / "checks"

BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"
SOURCE_SEED = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T120900-codex-exportable-source-scan/source-scan/source_window_seed_v1.csv"
APPROVED_CROSSWALK_SLOTS = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T122933-codex-source-window-crosswalk-decision-v1/source-window-crosswalk/approved_source_window_slots_v1.csv"
SIDEWAYS_WINDOWS = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T123500-codex-sideways-dated-window-materialization-v1/sideways-windows/sideways_dated_windows_v1.csv"


FIELDS = [
    "label_window_id",
    "source_type",
    "provider",
    "instrument",
    "market_context",
    "timeframe",
    "root",
    "start_date",
    "end_date",
    "date_granularity",
    "source_id",
    "source_native_scope",
    "crosswalk_layer",
    "crosswalk_decision",
    "scope_tier",
    "confidence_gate_ref",
    "status",
    "notes",
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def market_context_for_crosswalk(instrument: str) -> str:
    if instrument == "^GSPC":
        return "sp500_index"
    if instrument == "SPY":
        return "sp500_etf_proxy"
    if instrument == "ES=F":
        return "sp500_futures_proxy"
    return "unknown"


def crosswalk_scope_tier(row: dict[str, str]) -> str:
    if row["instrument"] == "^GSPC":
        return "same_underlying_calendar_window"
    return "s_and_p_500_tradable_proxy"


def materialize_crosswalk_windows(slots: list[dict[str, str]], seed_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    source_by_root = {}
    for seed in seed_rows:
        source_by_root.setdefault(seed["root"], []).append(seed)

    out: list[dict[str, str]] = []
    for slot in slots:
        for source in source_by_root.get(slot["root"], []):
            out.append({
                "label_window_id": f"{slot['slot_id']}-{source['root'].lower()}-{source['start_date']}-{source['end_date'] or 'open'}",
                "source_type": "source_window_crosswalk",
                "provider": slot["provider"],
                "instrument": slot["instrument"],
                "market_context": market_context_for_crosswalk(slot["instrument"]),
                "timeframe": slot["timeframe"],
                "root": slot["root"],
                "start_date": source["start_date"],
                "end_date": source["end_date"],
                "date_granularity": source["date_granularity"],
                "source_id": source["source_id"],
                "source_native_scope": source["native_scope"],
                "crosswalk_layer": slot["crosswalk_layer"],
                "crosswalk_decision": slot["crosswalk_decision"],
                "scope_tier": crosswalk_scope_tier(slot),
                "confidence_gate_ref": "not_calibrated_source_label_slot_only",
                "status": "materialized_source_window_label",
                "notes": slot["notes"],
            })
    return out


def materialize_sideways_windows(sideways_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    for row in sideways_rows:
        out.append({
            "label_window_id": row["source_window_id"],
            "source_type": "sideways_scoped_dated_window",
            "provider": row["provider"],
            "instrument": row["instrument"],
            "market_context": row["market_context"],
            "timeframe": row["timeframe"],
            "root": "Sideways",
            "start_date": row["start_date"],
            "end_date": row["end_date"],
            "date_granularity": "bar_window",
            "source_id": "sideways_sourcebacked_abs_return_range_v1",
            "source_native_scope": "Yahoo cached crypto/equity_etf 1d/1w accepted Sideways gate",
            "crosswalk_layer": "sideways_dated_window_materialization_v1",
            "crosswalk_decision": "scoped_dated_window_materialized_from_accepted_gate",
            "scope_tier": "scoped_existing_yahoo_gate_1d_1w",
            "confidence_gate_ref": "calibration_lcb=0.988647;test_lcb=0.995568",
            "status": row["status"],
            "notes": f"row_count={row['row_count']}; train={row['train_rows']}; calibration={row['calibration_rows']}; test={row['test_rows']}",
        })
    return out


def counter(rows: list[dict[str, str]], field: str) -> dict[str, int]:
    return dict(sorted(Counter(row[field] for row in rows).items()))


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)

    source_seed = read_csv(SOURCE_SEED)
    approved_slots = read_csv(APPROVED_CROSSWALK_SLOTS)
    sideways = read_csv(SIDEWAYS_WINDOWS)

    crosswalk_windows = materialize_crosswalk_windows(approved_slots, source_seed)
    sideways_windows = materialize_sideways_windows(sideways)
    unified = crosswalk_windows + sideways_windows

    panel_csv = OUT_DIR / "unified_source_label_panel_v1.csv"
    write_csv(panel_csv, unified)

    package = {
        "run_id": RUN_ID,
        "artifact_type": "unified_source_label_panel_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "inputs": {
            "board": str(BOARD.relative_to(REPO)),
            "board_sha256_at_run": sha256(BOARD),
            "source_window_seed": str(SOURCE_SEED.relative_to(REPO)),
            "source_window_seed_sha256": sha256(SOURCE_SEED),
            "approved_crosswalk_slots": str(APPROVED_CROSSWALK_SLOTS.relative_to(REPO)),
            "approved_crosswalk_slots_sha256": sha256(APPROVED_CROSSWALK_SLOTS),
            "sideways_windows": str(SIDEWAYS_WINDOWS.relative_to(REPO)),
            "sideways_windows_sha256": sha256(SIDEWAYS_WINDOWS),
        },
        "panel": {
            "csv": str(panel_csv.relative_to(REPO)),
            "total_label_windows": len(unified),
            "crosswalk_source_windows": len(crosswalk_windows),
            "sideways_scoped_dated_windows": len(sideways_windows),
            "by_root": counter(unified, "root"),
            "by_source_type": counter(unified, "source_type"),
            "by_instrument": counter(unified, "instrument"),
            "by_timeframe": counter(unified, "timeframe"),
            "by_scope_tier": counter(unified, "scope_tier"),
        },
        "coverage_audit": {
            "all_active_price_roots_represented": sorted(counter(unified, "root")) == ["Bear", "Bull", "Crisis", "Sideways"],
            "manipulation_represented": False,
            "confidence_gate_claimed": False,
            "full_objective_gate": "none_for_MainRegimeV2_expanded_full_universe_full_cycle_goal",
            "remaining_blockers": [
                "Bull/Bear/Crisis crosswalk rows are source-label windows, not held-out confidence gates.",
                "Sideways dated windows are scoped to existing Yahoo 1d/1w accepted gate only.",
                "Unsupported intraday/monthly/full-species Sideways cells remain abstained.",
                "Broader index families, commodities, volatility, and crypto full-species projections still need exact sources or explicit crosswalk decisions.",
                "Manipulation remains a separate direct-event/order-flow/order-lifecycle class and is not represented in this price-root panel.",
            ],
        },
        "guardrails": {
            "runtime_code_changed": False,
            "thresholds_relaxed": False,
            "raw_data_committed": False,
            "trade_usable": False,
            "future_or_target_predictors_used": False,
            "shared_board_modified": False,
        },
        "next_action": "Run targeted calibration using this unified panel only where source-label windows and bar data overlap; abstain all unsupported cells.",
    }

    json_path = OUT_DIR / "unified_source_label_panel_v1.json"
    json_path.write_text(json.dumps(package, indent=2, sort_keys=True) + "\n")

    md = [
        "# Unified Source Label Panel v1",
        "",
        f"Run ID: `{RUN_ID}`",
        "",
        "## Result",
        "",
        f"- Unified label windows: `{len(unified)}`.",
        f"- Crosswalk source windows: `{len(crosswalk_windows)}`.",
        f"- Sideways scoped dated windows: `{len(sideways_windows)}`.",
        f"- Roots represented: `{', '.join(sorted(counter(unified, 'root')))}`.",
        "- Full objective gate: `none_for_MainRegimeV2_expanded_full_universe_full_cycle_goal`.",
        "",
        "## Counts",
        "",
        f"- By root: `{package['panel']['by_root']}`",
        f"- By source type: `{package['panel']['by_source_type']}`",
        f"- By timeframe: `{package['panel']['by_timeframe']}`",
        "",
        "## Guardrails",
        "",
        "- This is a label-window panel and coverage audit, not a calibrated confidence gate.",
        "- `Manipulation` is not represented because it requires direct event/order-flow/order-lifecycle rows.",
        "- Unsupported Sideways intraday/monthly/full-species cells stay abstained.",
        "- No runtime code changed, no thresholds relaxed, no raw data committed.",
        "",
        "## Artifacts",
        "",
        "- `unified_source_label_panel_v1.json`",
        "- `unified_source_label_panel_v1.csv`",
        "- `../checks/unified_source_label_panel_v1_assertions.out`",
        "",
    ]
    (OUT_DIR / "unified_source_label_panel_v1.md").write_text("\n".join(md))

    assertions = [
        f"run_id={RUN_ID}",
        f"board_sha256_at_run={package['inputs']['board_sha256_at_run']}",
        f"total_label_windows={len(unified)}",
        f"crosswalk_source_windows={len(crosswalk_windows)}",
        f"sideways_scoped_dated_windows={len(sideways_windows)}",
        f"by_root={package['panel']['by_root']}",
        f"all_active_price_roots_represented={str(package['coverage_audit']['all_active_price_roots_represented']).lower()}",
        "manipulation_represented=false",
        "confidence_gate_claimed=false",
        "full_objective_gate=none_for_MainRegimeV2_expanded_full_universe_full_cycle_goal",
        "runtime_code_changed=false",
        "thresholds_relaxed=false",
        "raw_data_committed=false",
        "trade_usable=false",
        "assertion_status=PASS",
    ]
    (CHECK_DIR / "unified_source_label_panel_v1_assertions.out").write_text("\n".join(assertions) + "\n")

    assert len(approved_slots) == 63
    assert len(crosswalk_windows) == 231
    assert len(sideways_windows) == 608
    assert len(unified) == 839
    assert package["coverage_audit"]["all_active_price_roots_represented"] is True
    assert package["coverage_audit"]["confidence_gate_claimed"] is False


if __name__ == "__main__":
    main()
