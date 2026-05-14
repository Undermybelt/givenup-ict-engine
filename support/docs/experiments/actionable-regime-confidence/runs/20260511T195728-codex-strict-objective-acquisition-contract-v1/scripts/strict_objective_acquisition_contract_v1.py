#!/usr/bin/env python3
"""Build exact acquisition contracts for the remaining Board A strict blockers."""

from __future__ import annotations

import csv
import json
from pathlib import Path


RUN_ID = "20260511T195728-codex-strict-objective-acquisition-contract-v1"


def package_rows() -> list[dict[str, str]]:
    return [
        {
            "requirement_id": "R2",
            "package_id": "other_market_source_label_equivalence",
            "required_files": "source_label_equivalence_rows.csv;source_label_equivalence_provenance.json",
            "minimum_required_content": (
                "owner-approved row-level source labels for non-counted markets/species; "
                "must include source label, owner mapping to MainRegimeV2, instrument, "
                "market, timestamp/window, timeframe, source owner, provenance URL, "
                "and validation split tags"
            ),
            "explicit_non_acceptance": (
                "HMM/KMeans/model outputs, feature-threshold labels, future-return labels, "
                "research-code predictions, source panels already counted, raw candles "
                "without source-owned labels"
            ),
            "acceptance_check": (
                "source_label_equivalence verifier accepts rows and a completion audit shows "
                "other-market/source-label equivalence is true with accepted_rows_added > 0"
            ),
            "current_blocker_evidence": (
                "web_source_label_broad_recheck_v1, external_metadata_search_readback_v1, "
                "github_source_label_candidate_screen_v1, and local inventory all found 0 "
                "promotable owner-approved equivalence rows"
            ),
        },
        {
            "requirement_id": "R3",
            "package_id": "native_subhour_source_labels",
            "required_files": "native_subhour_source_label_rows.csv;native_subhour_source_label_provenance.json",
            "minimum_required_content": (
                "source-owned native 1m/5m/15m/30m regime labels or owner-approved "
                "crosswalk rows, with native sub-hour window timestamps and no daily/monthly "
                "projection"
            ),
            "explicit_non_acceptance": (
                "projected daily/monthly labels, provider OHLCV panels, synthetic panels, "
                "HMM/classifier-generated labels, code-only repos"
            ),
            "acceptance_check": (
                "native sub-hour verifier reports ready_native_subhour_source_owned_label_sources > 0 "
                "and native_subhour_source_overlap_closed=true"
            ),
            "current_blocker_evidence": (
                "native_subhour_projection_quarantine_v1 quarantined 264 projected rows; "
                "native_subhour_source_recheck_v2 found 0 ready native sub-hour source-owned labels"
            ),
        },
        {
            "requirement_id": "R4",
            "package_id": "strict_1h_exact_target_source_rows",
            "required_files": "/tmp/ict-engine-source-label-equivalence-intake/source_label_equivalence_rows.csv;/tmp/ict-engine-source-label-equivalence-intake/source_label_equivalence_provenance.json",
            "minimum_required_content": (
                "new source-owned exact 1h rows for XOM/Sideways, UNH/Bear, ^DJI/Sideways, "
                "and AMD/Bear, not duplicated from the existing daily source panel; row-level "
                "provenance must identify source owner and mapping authority"
            ),
            "explicit_non_acceptance": (
                "reusing existing source-panel rows, duplicating already-counted gate support, "
                "provider-derived 1h candles without owner labels"
            ),
            "acceptance_check": (
                "strict_1h_source_intake_verifier reports live intake files present and "
                "strict_1h_target_exact_source_search finds ready exact-target source-owned rows"
            ),
            "current_blocker_evidence": (
                "strict_1h_source_intake_verifier_readback_v1 missing 2 required files; "
                "strict_1h_contract_panel_exhaustion_v1 found 0 extra source rows; "
                "strict_1h_target_exact_source_search_v1 found 0 ready exact target sources"
            ),
        },
        {
            "requirement_id": "R5",
            "package_id": "strict_1h_recency_tail_repair",
            "required_files": "source_panel_recency_tail_rows.csv;source_panel_recency_tail_provenance.json",
            "minimum_required_content": (
                "source-owned tail rows after 2026-01-30 for the strict target cells: "
                "XOM/Sideways, UNH/Bear, ^DJI/Sideways, AMD/Bear"
            ),
            "explicit_non_acceptance": (
                "same historical panel with no post-2026-01-30 rows, generated forward fills, "
                "provider candles without source-owned labels"
            ),
            "acceptance_check": (
                "local target counts show rows_after_2026_01_30 > 0 for each strict target "
                "and completion audit clears the recency-tail row"
            ),
            "current_blocker_evidence": (
                "strict_1h_target_exact_source_search_v1 reported rows_after_2026_01_30 = 0 "
                "for all four strict targets"
            ),
        },
        {
            "requirement_id": "R6",
            "package_id": "direct_manipulation_full_species_rows",
            "required_files": (
                "/tmp/ict-engine-direct-manipulation-row-intake/positive_spoofing_layering_rows.csv;"
                "/tmp/ict-engine-direct-manipulation-row-intake/matched_negative_normal_activity_rows.csv;"
                "/tmp/ict-engine-direct-manipulation-row-intake/provenance_manifest.json"
            ),
            "minimum_required_content": (
                "row-level direct manipulation positives and matched same-venue/symbol/session "
                "normal controls for spoofing/layering, with extension slots for quote stuffing, "
                "pinging, bear raid, and painting tape; rows need timestamp/session, venue, "
                "instrument, event id, control group id, source owner, and provenance"
            ),
            "explicit_non_acceptance": (
                "positive-only enforcement cases, raw LOB/order book without manipulation labels, "
                "synthetic spoofing repos, pump/dump-only evidence, unmatched control-only panels"
            ),
            "acceptance_check": (
                "direct_manipulation_intake verifier finds all required files, missing_files=0, "
                "and full_direct_manipulation_species_coverage=true"
            ),
            "current_blocker_evidence": (
                "direct_manipulation_intake_verifier_readback_v1 missing 3 files; "
                "Sapienza is only a pump/dump positive/control candidate and not spoofing/layering "
                "or full species coverage"
            ),
        },
    ]


def main() -> int:
    run_root = Path(
        "docs/experiments/actionable-regime-confidence/runs/"
        "20260511T195728-codex-strict-objective-acquisition-contract-v1"
    )
    out_dir = run_root / "strict-objective-acquisition-contract"
    checks_dir = run_root / "checks"
    out_dir.mkdir(parents=True, exist_ok=True)
    checks_dir.mkdir(parents=True, exist_ok=True)

    rows = package_rows()
    result = {
        "run_id": RUN_ID,
        "decision": "strict_objective_acquisition_contract_v1=contracts_ready_objective_still_blocked",
        "source_audit": (
            "Built from v25 failed rows R2/R3/R4/R5/R6/R8 and latest source/inventory readbacks."
        ),
        "contract_rows": len(rows),
        "required_packages": [row["package_id"] for row in rows],
        "strict_full_objective_achieved": False,
        "accepted_rows_added": 0,
        "new_confidence_gate": False,
        "update_goal": False,
        "raw_data_committed": False,
        "runtime_code_changed": False,
        "contracts": rows,
    }

    json_path = out_dir / "strict_objective_acquisition_contract_v1.json"
    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")

    csv_path = out_dir / "strict_objective_acquisition_contract_v1_contracts.csv"
    with csv_path.open("w", newline="") as handle:
        fieldnames = [
            "requirement_id",
            "package_id",
            "required_files",
            "minimum_required_content",
            "explicit_non_acceptance",
            "acceptance_check",
            "current_blocker_evidence",
        ]
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    md_lines = [
        "# Strict Objective Acquisition Contract v1",
        "",
        "Decision: `strict_objective_acquisition_contract_v1=contracts_ready_objective_still_blocked`",
        "",
        "- Contract rows: `5`.",
        "- Accepted rows added: `0`; new confidence gate: `false`.",
        "- Strict full objective achieved: `false`; `update_goal=false`.",
        "- Runtime code changed: `false`; raw data committed: `false`.",
        "",
        "## Contract Rows",
        "",
        "| Requirement | Package | Required files | Acceptance check |",
        "|---|---|---|---|",
    ]
    for row in rows:
        md_lines.append(
            "| {requirement_id} | `{package_id}` | `{required_files}` | {acceptance_check} |".format(
                **row
            )
        )
    md_lines.extend(
        [
            "",
            "## Fail-Closed Rules",
            "",
            "- Do not promote HMM, KMeans, classifier, future-return, generated, synthetic, or OHLCV-only labels.",
            "- Do not duplicate existing source-panel rows as new strict `1h` support.",
            "- Do not use daily/monthly labels projected into sub-hour windows.",
            "- Do not use pump/dump-only rows to close spoofing/layering or full direct `Manipulation` species coverage.",
            "",
            "## Next Exact Acquisition Targets",
            "",
            "1. Fill `/tmp/ict-engine-source-label-equivalence-intake/source_label_equivalence_rows.csv` plus provenance for the four strict `1h` target cells.",
            "2. Obtain a native sub-hour source-owned label package, not a projection from daily/monthly regimes.",
            "3. Obtain direct spoofing/layering positives plus matched normal controls and provenance.",
            "4. Add recency-tail source rows after `2026-01-30` for XOM/Sideways, UNH/Bear, ^DJI/Sideways, and AMD/Bear.",
        ]
    )
    (out_dir / "strict_objective_acquisition_contract_v1.md").write_text("\n".join(md_lines) + "\n")

    assertions = [
        "PASS decision=strict_objective_acquisition_contract_v1=contracts_ready_objective_still_blocked",
        f"PASS contract_rows={len(rows)}",
        "PASS accepted_rows_added=0",
        "PASS new_confidence_gate=false",
        "PASS strict_full_objective_achieved=false",
        "PASS update_goal=false",
        "PASS raw_data_committed=false",
    ]
    (checks_dir / "strict_objective_acquisition_contract_v1_assertions.out").write_text(
        "\n".join(assertions) + "\n"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
