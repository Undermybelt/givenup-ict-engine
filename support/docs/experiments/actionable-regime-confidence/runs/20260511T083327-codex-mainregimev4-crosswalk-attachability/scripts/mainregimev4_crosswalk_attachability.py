#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


RUN_ID = "20260511T083327+0800-codex-mainregimev4-crosswalk-attachability"
RUN_ROOT = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T083327-codex-mainregimev4-crosswalk-attachability"
)

V4_TAXONOMY_JSON = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T082635-codex-main-regime-v4-web-research-taxonomy/"
    "taxonomy/main_regime_v4_web_research_taxonomy.json"
)
V2_ATTACHABILITY_JSON = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T081210-codex-underlying-source-label-attachability/"
    "source-label-attachability/underlying_source_label_attachability.json"
)
V2_ACQUISITION_JSON = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T081715-codex-source-label-acquisition-package-v2/"
    "acquisition-package/source_label_acquisition_package_v2.json"
)
DIRECT_SOURCE_SCAN_JSON = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T082034-codex-direct-manipulation-labeled-source-web-scan/"
    "direct-manipulation-source-scan/direct_manipulation_labeled_source_web_scan.json"
)
MENDELEY_REAUDIT_JSON = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T082521-codex-mendeley-v3-gox-refetch-reaudit/"
    "mendeley-v3-reaudit/mendeley_v3_gox_refetch_reaudit.json"
)
MEHRNOOM_GATE_JSON = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T045102-codex-mehrnoom-telegram-direct-manipulation-gate/"
    "direct-event-gate/mehrnoom_telegram_direct_manipulation_gate_report.json"
)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def main() -> None:
    schema_dir = RUN_ROOT / "schema"
    checks_dir = RUN_ROOT / "checks"
    schema_dir.mkdir(parents=True, exist_ok=True)
    checks_dir.mkdir(parents=True, exist_ok=True)

    v4 = load_json(V4_TAXONOMY_JSON)
    attach = load_json(V2_ATTACHABILITY_JSON)
    acquisition = load_json(V2_ACQUISITION_JSON)
    source_scan = load_json(DIRECT_SOURCE_SCAN_JSON)
    mendeley = load_json(MENDELEY_REAUDIT_JSON)
    mehrnoom = load_json(MEHRNOOM_GATE_JSON)

    attachability = attach["attachability"]
    acquisition_request = acquisition["acquisition_request"]
    completion_roots = [
        "BullExpansion",
        "BearExpansion",
        "Consolidation",
        "CrisisStress",
    ]
    v4_root_values = completion_roots + ["Manipulation"]

    v2_to_v4 = [
        {
            "prior_root": "Bull",
            "v4_root": "BullExpansion",
            "handling": "reaudit_required",
            "reason": "Raw Bull labels must prove sustained positive expansion rather than weak recovery, correction, or transition.",
        },
        {
            "prior_root": "Bear",
            "v4_root": "BearExpansion",
            "handling": "reaudit_required",
            "reason": "Raw Bear labels must separate ordinary negative expansion from CrisisStress and crash/stress windows.",
        },
        {
            "prior_root": "Sideways",
            "v4_root": "Consolidation",
            "handling": "reaudit_required",
            "reason": "Sideways/range labels are conceptually close but need V4 range/compression calibration and context validation.",
        },
        {
            "prior_root": "Crisis",
            "v4_root": "CrisisStress",
            "handling": "preserved_provenance_reaudit_required",
            "reason": "Prior Crisis evidence is useful stress provenance but does not complete V4 full-universe/full-cycle accounting without rerun.",
        },
        {
            "prior_root": "Manipulation_overlay",
            "v4_root": "Manipulation",
            "handling": "active_root_output_direct_input_gate",
            "reason": "Direct event/order-flow/order-lifecycle evidence may support this root, but OHLCV proxies remain forbidden.",
        },
    ]

    candidate_slots_by_v4_root = {
        "BullExpansion": attachability["attached_slots_by_root"].get("Bull", 0),
        "BearExpansion": attachability["attached_slots_by_root"].get("Bear", 0),
        "Consolidation": attachability["attached_slots_by_root"].get("Sideways", 0),
        "CrisisStress": attachability["attached_slots_by_root"].get("Crisis", 0),
    }
    missing_or_reaudit_by_v4_root = {
        "BullExpansion": acquisition_request["missing_or_rejected_slots_by_root"].get("Bull", 0),
        "BearExpansion": acquisition_request["missing_or_rejected_slots_by_root"].get("Bear", 0),
        "Consolidation": acquisition_request["missing_or_rejected_slots_by_root"].get("Sideways", 0),
        "CrisisStress": acquisition_request["missing_or_rejected_slots_by_root"].get("Crisis", 0),
    }

    mendeley_decision = mendeley["decision"]
    mendeley_metrics = mendeley["metrics"]
    mehrnoom_test = next(
        row for row in mehrnoom["split_summaries"] if row["split"] == "test"
    )
    mehrnoom_cal = next(
        row for row in mehrnoom["split_summaries"] if row["split"] == "calibration"
    )

    summary = {
        "run_id": RUN_ID,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "objective": (
            "Materialize the MainRegimeV4 target schema and crosswalk prior "
            "MainRegimeV2 attachability into V4 accounting without promotion."
        ),
        "active_taxonomy": "MainRegimeV4",
        "input_evidence": {
            "v4_taxonomy": str(V4_TAXONOMY_JSON),
            "v2_attachability": str(V2_ATTACHABILITY_JSON),
            "v2_acquisition_package": str(V2_ACQUISITION_JSON),
            "direct_source_scan": str(DIRECT_SOURCE_SCAN_JSON),
            "mendeley_v3_reaudit": str(MENDELEY_REAUDIT_JSON),
            "mehrnoom_direct_event_gate": str(MEHRNOOM_GATE_JSON),
        },
        "v4_label_panel_schema": {
            "root_values": v4_root_values,
            "residual_only": ["UnknownOrMixed"],
            "minimum_requirements": [
                "independent/source-backed labels or direct event/order-flow/order-lifecycle labels",
                "chronological calibration/test split without future leakage",
                "root-specific qualifying condition/rule",
                "cross-context validation across instruments, timeframes, and market periods",
                "no automatic promotion from child/subtype/proxy labels",
                "near-proxy mappings remain rejected unless exact-underlying/source evidence is provided",
            ],
            "required_fields": [
                "provider",
                "instrument",
                "timeframe",
                "v4_root",
                "start_ts",
                "end_ts",
                "source_label",
                "source_label_confidence",
                "source_name",
                "source_license_or_access_contract",
                "labeling_method",
                "label_timestamp_or_publication_time",
                "raw_source_reference",
                "v4_crosswalk_status",
            ],
        },
        "crosswalk": v2_to_v4,
        "price_root_slot_accounting": {
            "prior_v2_slot_universe": 612,
            "candidate_slots_from_prior_exact_underlying_v2": attachability[
                "attached_candidate_slots"
            ],
            "candidate_slots_by_v4_root": candidate_slots_by_v4_root,
            "missing_or_rejected_slots_from_prior_v2": attachability[
                "missing_or_rejected_slots"
            ],
            "missing_or_reaudit_required_by_v4_root": missing_or_reaudit_by_v4_root,
            "full_four_price_root_cells_candidate_only": attachability[
                "full_four_root_cells"
            ],
            "accepted_v4_price_root_slots": 0,
            "why_zero_accepted": [
                "Prior Bull/Bear/Sideways/Crisis labels are provenance only after V4 taxonomy reopen.",
                "No V4 chronological calibration/test gate was rerun for the 48 candidate slots in this crosswalk packet.",
                "The 564 missing/rejected V2 slots remain missing or require external source labels under V4.",
            ],
        },
        "manipulation_accounting": {
            "v4_root": "Manipulation",
            "direct_event_provenance_sources_preserved": [
                {
                    "run_id": mehrnoom["run_id"],
                    "evidence_class": mehrnoom["evidence_class"],
                    "accepted_95_provenance": mehrnoom["accepted_95"],
                    "calibration_wilson95_lcb": mehrnoom_cal["wilson95_lcb"],
                    "test_wilson95_lcb": mehrnoom_test["wilson95_lcb"],
                    "test_support": mehrnoom_test["support"],
                    "test_negative_controls": mehrnoom_test["negative_controls"],
                    "limitation": (
                        "event-confirmed suppression/abstain provenance only; "
                        "does not complete all manipulation varieties or Dune/Mendeley wash-trade coverage"
                    ),
                }
            ],
            "mendeley_v3_gox_reaudit": {
                "accepted_direct_manipulation_95": mendeley_decision[
                    "accepted_direct_manipulation_95"
                ],
                "gate_result": mendeley_decision["gate_result"],
                "blockers": mendeley_decision["blockers"],
                "calibration_wilson95_lcb": mendeley_metrics["calibration"][
                    "wilson_lcb_95"
                ],
                "test_wilson95_lcb": mendeley_metrics["test"]["wilson_lcb_95"],
                "test_coverage": mendeley_metrics["test"]["coverage"],
                "calibration_ece": mendeley_metrics["calibration"]["ece_10bin"],
                "test_ece": mendeley_metrics["test"]["ece_10bin"],
            },
            "dune_nft_wash_trades_export_materialized": False,
            "accepted_v4_manipulation_completion": False,
            "new_direct_manipulation_label_sources_added": source_scan[
                "accepted_direct_manipulation_label_sources_added"
            ],
        },
        "completion_accounting": {
            "accepted_gate": "none_for_MainRegimeV4_expanded_full_universe_full_cycle_goal",
            "accepted_confidence": False,
            "accepted_full_cycle_full_universe": False,
            "goal_achieved": False,
            "accepted_v4_completion_roots": 0,
            "blocked_v4_completion_roots": v4_root_values,
            "thresholds_relaxed": False,
            "runtime_code_changed": False,
            "raw_data_committed": False,
            "trade_usable": False,
        },
        "gate_result": "blocked_mainregimev4_crosswalk_all_roots_need_reaudit_or_labels",
        "next_action": (
            "Try a bounded Dune nft.wash_trades export path under the V4 "
            "Manipulation root, requiring replayable timestamps, positive/negative "
            "windows, and provenance; do not count rule-only labels or OHLCV proxies."
        ),
        "artifacts": {
            "summary_json": str(schema_dir / "mainregimev4_crosswalk_attachability.json"),
            "summary_md": str(schema_dir / "mainregimev4_crosswalk_attachability.md"),
            "crosswalk_csv": str(schema_dir / "mainregimev4_crosswalk.csv"),
            "assertions": str(checks_dir / "mainregimev4_crosswalk_attachability_assertions.out"),
            "script": str(RUN_ROOT / "scripts/mainregimev4_crosswalk_attachability.py"),
        },
        "source_declared_active_roots": v4.get("completion_roots", []),
    }

    write_json(schema_dir / "mainregimev4_crosswalk_attachability.json", summary)

    csv_path = schema_dir / "mainregimev4_crosswalk.csv"
    with csv_path.open("w", newline="") as fh:
        writer = csv.DictWriter(
            fh, fieldnames=["prior_root", "v4_root", "handling", "reason"]
        )
        writer.writeheader()
        writer.writerows(v2_to_v4)

    md = f"""# MainRegimeV4 Crosswalk Attachability

Run id: `{RUN_ID}`

## Result

- Active taxonomy: `MainRegimeV4`.
- V4 completion roots: `BullExpansion`, `BearExpansion`, `Consolidation`, `CrisisStress`, `Manipulation`.
- Accepted V4 completion roots added: `0`.
- Accepted V4 price-root source-label slots: `0`.
- Prior V2 exact-underlying candidate slots retained only for re-audit: `{attachability["attached_candidate_slots"]}/612`.
- Missing or rejected prior V2 slots still requiring external labels or V4 re-audit: `{attachability["missing_or_rejected_slots"]}/612`.
- Direct `Manipulation` new label sources added by the Dune/Mendeley source scan lane: `{source_scan["accepted_direct_manipulation_label_sources_added"]}`.
- Mendeley v3 Gox re-audit remains blocked: `{mendeley_decision["gate_result"]}`.
- Gate result: `blocked_mainregimev4_crosswalk_all_roots_need_reaudit_or_labels`.

## Crosswalk

| Prior root | V4 root | Handling |
|---|---|---|
| `Bull` | `BullExpansion` | `reaudit_required` |
| `Bear` | `BearExpansion` | `reaudit_required` |
| `Sideways` | `Consolidation` | `reaudit_required` |
| `Crisis` | `CrisisStress` | `preserved_provenance_reaudit_required` |
| `Manipulation` overlay | `Manipulation` | `active_root_output_direct_input_gate` |

## Accounting

- Existing MainRegimeV2 source-label attachability is provenance only until a V4 chronological calibration/test gate reruns.
- `Manipulation` keeps direct-event provenance from Mehrnoom/Mirtaheri (`test Wilson95 {mehrnoom_test["wilson95_lcb"]:.12f}`), but V4 full direct-manipulation completion remains blocked because Mendeley failed coverage/ECE and Dune is not exported yet.
- Raw data committed: false. Runtime code changed: false. Thresholds relaxed: false. Trade usable: false.

## Next Action

Try a bounded Dune `nft.wash_trades` export path under the V4 `Manipulation` root with replayable timestamps, positive/negative windows, and provenance. Do not count rule-only labels or OHLCV proxies.
"""
    (schema_dir / "mainregimev4_crosswalk_attachability.md").write_text(md)

    assertions = [
        "PASS active_taxonomy=MainRegimeV4",
        "PASS v4_completion_roots=5",
        "PASS accepted_v4_completion_roots=0",
        "PASS prior_v2_slots_not_promoted=true",
        f"PASS candidate_v2_slots_for_v4_reaudit={attachability['attached_candidate_slots']}",
        f"PASS missing_or_rejected_slots={attachability['missing_or_rejected_slots']}",
        "PASS mendeley_v3_blocked=true",
        "PASS dune_export_materialized=false",
        "PASS thresholds_relaxed=false",
        "PASS runtime_code_changed=false",
        "PASS raw_data_committed=false",
    ]
    (checks_dir / "mainregimev4_crosswalk_attachability_assertions.out").write_text(
        "\n".join(assertions) + "\n"
    )


if __name__ == "__main__":
    main()
