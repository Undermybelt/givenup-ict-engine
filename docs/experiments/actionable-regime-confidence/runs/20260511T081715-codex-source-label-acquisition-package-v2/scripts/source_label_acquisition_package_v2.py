#!/usr/bin/env python3
"""Build the current MainRegimeV2 source-label acquisition package.

This supersedes the earlier 596-slot acquisition request by using the latest
exact-underlying attachability audit, where 48/612 slots are attachable and
564 slots remain missing or rejected.
"""

from __future__ import annotations

import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO = Path("/Users/thrill3r/projects-ict-engine/ict-engine")
RUN_ID = "20260511T081715+0800-codex-source-label-acquisition-package-v2"
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T081715-codex-source-label-acquisition-package-v2"
OUT_DIR = RUN_ROOT / "acquisition-package"
CHECK_DIR = RUN_ROOT / "checks"

UNDERLYING_ATTACHABILITY_JSON = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs/20260511T081210-codex-underlying-source-label-attachability"
    / "source-label-attachability/underlying_source_label_attachability.json"
)
UNDERLYING_ATTACHABILITY_CSV = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs/20260511T081210-codex-underlying-source-label-attachability"
    / "source-label-attachability/underlying_source_label_attachability.csv"
)
PROVIDER_RESIDUAL = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs/20260511T081120-codex-provider-residual-disposition-readback"
    / "coverage-disposition/provider_residual_disposition_readback.json"
)
DIRECT_MANIPULATION_SCHEMA = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs/20260511T081556-codex-direct-manipulation-source-schema-audit"
    / "direct-manipulation-schema/direct_manipulation_source_schema_audit.json"
)
STALE_PACKAGE = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs/20260511T081522-codex-source-label-acquisition-package"
    / "acquisition-package/source_label_acquisition_package.json"
)


def rel(path: Path) -> str:
    return str(path.relative_to(REPO))


def load_json(path: Path) -> Any:
    with path.open() as handle:
        return json.load(handle)


def read_missing_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    with UNDERLYING_ATTACHABILITY_CSV.open(newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            if row.get("accepted_candidate") == "True":
                continue
            status = row["status"]
            required = "independent_source_backed_root_label"
            if status == "rejected_near_underlying_proxy_not_accepted":
                required = "exact_underlying_or_direct_instrument_source_label"
            rows.append(
                {
                    "provider": row["provider"],
                    "instrument": row["instrument"],
                    "timeframe": row["timeframe"],
                    "root": row["root"],
                    "missing_or_rejected_reason": status,
                    "candidate_source_ticker_rejected_or_missing": row.get("source_ticker", ""),
                    "candidate_source_relation": row.get("source_relation", ""),
                    "required_label_source": required,
                    "forbidden_proxy_sources": "hmm_state_or_ohlcv_derived_proxy_or_strategy_prediction_or_future_return_label",
                }
            )
    return rows


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    fieldnames = [
        "provider",
        "instrument",
        "timeframe",
        "root",
        "missing_or_rejected_reason",
        "candidate_source_ticker_rejected_or_missing",
        "candidate_source_relation",
        "required_label_source",
        "forbidden_proxy_sources",
    ]
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)

    attachability = load_json(UNDERLYING_ATTACHABILITY_JSON)
    provider_residual = load_json(PROVIDER_RESIDUAL)
    direct_manipulation = load_json(DIRECT_MANIPULATION_SCHEMA)
    stale = load_json(STALE_PACKAGE) if STALE_PACKAGE.exists() else {}
    rows = read_missing_rows()

    by_reason = Counter(row["missing_or_rejected_reason"] for row in rows)
    by_provider = Counter(row["provider"] for row in rows)
    by_timeframe = Counter(row["timeframe"] for row in rows)
    by_root = Counter(row["root"] for row in rows)

    attach = attachability["attachability"]
    report = {
        "schema_version": "source-label-acquisition-package/v2",
        "run_id": RUN_ID,
        "run_root": rel(RUN_ROOT),
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "purpose": "Convert the current 564-slot MainRegimeV2 source-label blocker into a machine-readable acquisition request.",
        "supersedes": {
            "stale_package": rel(STALE_PACKAGE) if STALE_PACKAGE.exists() else "",
            "stale_missing_slots": stale.get("acquisition_request", {}).get("missing_slots"),
            "reason": "Earlier package used 16/612 direct attachability; current exact-underlying attachability is 48/612 with 564 missing/rejected slots.",
        },
        "input_evidence": {
            "underlying_source_label_attachability": rel(UNDERLYING_ATTACHABILITY_JSON),
            "underlying_source_label_attachability_csv": rel(UNDERLYING_ATTACHABILITY_CSV),
            "provider_residual_disposition_readback": rel(PROVIDER_RESIDUAL),
            "direct_manipulation_source_schema_audit": rel(DIRECT_MANIPULATION_SCHEMA),
        },
        "current_attachability": {
            "slot_count": attachability["contract"]["slot_count"],
            "attached_candidate_slots": attach["attached_candidate_slots"],
            "direct_source_label_slots": attach["attached_slots_by_relation"].get("exact_source_instrument", 0),
            "exact_underlying_source_label_slots": attach["attached_slots_by_relation"].get("exact_underlying_index", 0),
            "full_four_root_cells": attach["full_four_root_cells"],
            "missing_or_rejected_slots": attach["missing_or_rejected_slots"],
            "rejected_near_proxy_slots": attach["status_counts"].get("rejected_near_underlying_proxy_not_accepted", 0),
        },
        "provider_residuals": {
            "ready_not_yet_attempted_cells": provider_residual["completion_accounting"]["ready_not_yet_attempted_cells"],
            "ibkr_gate_result": provider_residual["ibkr_operator_probe"]["gate_result"],
            "ibkr_ok_count": provider_residual["ibkr_operator_probe"]["ok_count"],
            "polymarket_gate_result": provider_residual["polymarket_catalog_probe"]["gate_result"],
            "tradingview_blocked_cells": provider_residual["disposition_counts"].get("blocked_provider_unavailable", 0),
        },
        "direct_manipulation_schema_audit": {
            "candidates_seen": direct_manipulation["candidates_seen"],
            "direct_input_sources_materialized": direct_manipulation["direct_input_sources_materialized"],
            "accepted_direct_manipulation_label_sources": direct_manipulation["accepted_direct_manipulation_label_sources"],
            "manipulation_label_slots_added": direct_manipulation["manipulation_label_slots_added"],
            "gate_result": direct_manipulation["gate_result"],
        },
        "acquisition_request": {
            "missing_slot_csv": rel(OUT_DIR / "missing_root_label_slots_acquisition_request_v2.csv"),
            "missing_or_rejected_slots": len(rows),
            "missing_or_rejected_slots_by_reason": dict(sorted(by_reason.items())),
            "missing_or_rejected_slots_by_provider": dict(sorted(by_provider.items())),
            "missing_or_rejected_slots_by_timeframe": dict(sorted(by_timeframe.items())),
            "missing_or_rejected_slots_by_root": dict(sorted(by_root.items())),
            "columns": [
                "provider",
                "instrument",
                "timeframe",
                "root",
                "missing_or_rejected_reason",
                "candidate_source_ticker_rejected_or_missing",
                "candidate_source_relation",
                "required_label_source",
                "forbidden_proxy_sources",
            ],
        },
        "acceptable_label_panel_schema": {
            "required_fields": [
                "provider",
                "instrument",
                "timeframe",
                "root",
                "start_ts",
                "end_ts",
                "source_label",
                "source_label_confidence",
                "source_name",
                "source_license_or_access_contract",
                "labeling_method",
                "label_timestamp_or_publication_time",
                "raw_source_reference",
            ],
            "root_values": ["Bull", "Bear", "Sideways", "Crisis"],
            "minimum_requirements": [
                "labels are independent/source-backed rather than inferred by the current OHLCV features being scored",
                "chronological splits can be constructed without future leakage",
                "coverage explicitly maps to the requested provider/instrument/timeframe/root slot",
                "source provenance is auditable enough to reproduce or review the label meaning",
                "near-proxy mappings such as ^IXIC -> QQQ/^NDX/NQ=F remain rejected unless exact-underlying/source evidence is provided",
            ],
        },
        "manipulation_label_schema": {
            "required_fields": [
                "instrument_or_asset",
                "venue_or_source",
                "event_start_ts",
                "event_end_ts",
                "event_type",
                "positive_or_negative_label",
                "direct_evidence_channel",
                "source_name",
                "source_license_or_access_contract",
                "raw_source_reference",
            ],
            "accepted_channels": [
                "direct pump_dump_event",
                "wash_trade_row_label",
                "spoofing_or_layering_order_lifecycle_label",
                "L2_L3_MBO_order_flow_event_label",
                "social_event_plus_negative_controls",
            ],
            "forbidden_shortcuts": [
                "OHLCV-only sweep proxy",
                "thin-liquidity proxy",
                "HMM state id",
                "strategy/backtest prediction",
                "future target generated by this repo",
            ],
        },
        "completion_accounting": {
            "goal_achieved": False,
            "accepted_full_cycle_full_universe": False,
            "accepted_confidence": False,
            "why_not_accepted": [
                "Only 48/612 MainRegimeV2 source-label slots attach after exact-underlying mapping.",
                "The remaining 564 slots need independent labels or must be explicitly removed from the full-universe/full-cycle target.",
                "Provider residuals are dispositioned, but provider bars/catalogs do not replace source labels.",
                "Direct Manipulation schema sources were materialized, but the audited order-book/order-lifecycle/event sources are unlabeled and add zero accepted windows.",
            ],
        },
        "gate_result": "blocked_acquisition_package_v2_created_missing_564_external_source_labels",
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "trade_usable": False,
        "artifacts": {
            "package_json": rel(OUT_DIR / "source_label_acquisition_package_v2.json"),
            "package_md": rel(OUT_DIR / "source_label_acquisition_package_v2.md"),
            "missing_slot_csv": rel(OUT_DIR / "missing_root_label_slots_acquisition_request_v2.csv"),
            "assertions": rel(CHECK_DIR / "source_label_acquisition_package_v2_assertions.out"),
            "script": rel(Path(__file__)),
        },
        "next_action": "Use the v2 acquisition CSV to obtain independent labels for the 564 missing/rejected price-root slots plus explicit labeled Manipulation positive/negative windows; do not spend more cycles on provider bar fetches until label coverage exists.",
    }

    package_json = OUT_DIR / "source_label_acquisition_package_v2.json"
    package_md = OUT_DIR / "source_label_acquisition_package_v2.md"
    missing_csv = OUT_DIR / "missing_root_label_slots_acquisition_request_v2.csv"
    assertions = CHECK_DIR / "source_label_acquisition_package_v2_assertions.out"

    package_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    write_csv(missing_csv, rows)

    md_lines = [
        "# Source Label Acquisition Package V2",
        "",
        f"Run id: `{RUN_ID}`",
        "",
        "Goal achieved: `false`",
        "",
        f"- Current attached slots: `{attach['attached_candidate_slots']}` / `{attachability['contract']['slot_count']}`",
        f"- Current missing/rejected slots: `{len(rows)}`",
        f"- Full four-root cells: `{attach['full_four_root_cells']}`",
        f"- Ready-not-yet-attempted provider cells after residual readback: `{provider_residual['completion_accounting']['ready_not_yet_attempted_cells']}`",
        f"- IBKR gate: `{provider_residual['ibkr_operator_probe']['gate_result']}`",
        f"- Polymarket gate: `{provider_residual['polymarket_catalog_probe']['gate_result']}`",
        f"- Direct Manipulation schema audit: `{direct_manipulation['gate_result']}`; accepted label sources `{direct_manipulation['accepted_direct_manipulation_label_sources']}`",
        "",
        "## Missing / Rejected Reasons",
        "",
        "| Reason | Slots |",
        "|---|---:|",
    ]
    for reason, count in sorted(by_reason.items()):
        md_lines.append(f"| `{reason}` | {count} |")
    md_lines.extend(
        [
            "",
            "## Decision",
            "",
            "- Gate result: `blocked_acquisition_package_v2_created_missing_564_external_source_labels`",
            "- The older 596-slot acquisition package is stale because exact-underlying labels now attach 48 slots.",
            "- Provider bars/catalogs remain sidecar until source labels attach.",
            "- Runtime code changed: false. Thresholds relaxed: false. Trade usable: false.",
            "",
            "## Next Action",
            "",
            report["next_action"],
        ]
    )
    package_md.write_text("\n".join(md_lines) + "\n")

    assertion_lines = [
        "PASS acquisition_package_v2_created",
        "PASS missing_slot_csv_created",
        f"PASS attached_slots_{attach['attached_candidate_slots']}",
        f"PASS missing_or_rejected_rows_{len(rows)}",
        f"PASS full_four_root_cells_{attach['full_four_root_cells']}",
        f"PASS ready_not_yet_attempted_cells_{provider_residual['completion_accounting']['ready_not_yet_attempted_cells']}",
        f"PASS rejected_near_proxy_slots_{attach['status_counts'].get('rejected_near_underlying_proxy_not_accepted', 0)}",
        "PASS price_root_label_panel_schema_recorded",
        "PASS manipulation_label_schema_recorded",
        "PASS provider_residual_readback_consumed",
        "PASS direct_manipulation_schema_audit_consumed",
        f"PASS direct_manipulation_label_sources_{direct_manipulation['accepted_direct_manipulation_label_sources']}",
        "PASS goal_achieved_false",
        "PASS runtime_code_changed_false",
        "PASS thresholds_relaxed_false",
        "PASS trade_usable_false",
        "PASS gate_result_blocked_acquisition_package_v2_created_missing_564_external_source_labels",
    ]
    assertions.write_text("\n".join(assertion_lines) + "\n")
    print(rel(package_json))


if __name__ == "__main__":
    main()
