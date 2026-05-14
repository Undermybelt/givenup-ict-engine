#!/usr/bin/env python3
"""Focused R6 source-acquisition screen for spoofing/layering rows."""

from __future__ import annotations

import csv
import json
from pathlib import Path


RUN_ID = "20260511T200726-codex-spoofing-layering-source-acquisition-screen-v1"
RUN_ROOT = Path(
    "docs/experiments/actionable-regime-confidence/runs"
) / RUN_ID
OUT_DIR = RUN_ROOT / "spoofing-layering-source-acquisition-screen"
CHECK_DIR = RUN_ROOT / "checks"

REQUIREMENTS = {
    "row_level_direct_manipulation_positive_rows": True,
    "matched_same_schema_normal_controls": True,
    "source_owned_or_owner_approved_provenance": True,
    "venue_symbol_timestamp_fields": True,
    "chronological_validation_possible": True,
    "no_generated_proxy_synthetic_or_ohlcv_only_labels": True,
}

CANDIDATES = [
    {
        "candidate_id": "do_putnins_2023_detecting_layering_spoofing",
        "name": "Detecting Layering and Spoofing in Markets",
        "source_url": "https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4525036",
        "mirror_or_readback_url": "https://studylib.net/doc/28317823/ssrn-4525036",
        "target_species": "spoofing_layering",
        "evidence_readback": (
            "SSRN page describes a global prosecuted-case sample; the text mirror "
            "says case information was hand collected from regulatory/court "
            "documents and FOI requests, with some cases down to individual "
            "trades and orders."
        ),
        "has_row_level_positive_hint": True,
        "has_public_row_export": False,
        "has_matched_controls": False,
        "source_owned_or_owner_approved": False,
        "disposition": "blocked_owner_approval_or_export_required",
        "reason": (
            "High-value owner/contact target, but no public owner-approved "
            "positive/control row package or provenance manifest was found."
        ),
    },
    {
        "candidate_id": "delise_2023_deep_sad_tmx_fraud",
        "name": "Deep Semi-Supervised Anomaly Detection for Finding Fraud in the Futures Market",
        "source_url": "https://arxiv.org/abs/2309.00088",
        "mirror_or_readback_url": "/tmp/ict-engine-spoofing-layering-source-acquisition-screen-v1/deep-sad-futures-fraud-2309.00088.clean.txt",
        "target_species": "spoofing_layering_or_futures_fraud",
        "evidence_readback": (
            "arXiv abstract and extracted PDF text state the data is exclusive "
            "proprietary TMX limit order book data with a small set of true "
            "labeled fraud instances."
        ),
        "has_row_level_positive_hint": True,
        "has_public_row_export": False,
        "has_matched_controls": False,
        "source_owned_or_owner_approved": False,
        "disposition": "blocked_proprietary_no_public_rows",
        "reason": (
            "Real-label evidence exists in the paper, but the row panel is "
            "proprietary and not an exportable Board A intake package."
        ),
    },
    {
        "candidate_id": "lin_2025_multilevel_manipulation_lob",
        "name": "Detecting Multilevel Manipulation from Limit Order Book via Cascaded Contrastive Representation Learning",
        "source_url": "https://arxiv.org/abs/2508.17086",
        "mirror_or_readback_url": "/tmp/ict-engine-spoofing-layering-source-acquisition-screen-v1/decoupled-lob-2508.17086.clean.txt",
        "target_species": "multilevel_spoofing_layering",
        "evidence_readback": (
            "Extracted PDF text says raw data comes from LOBSTER and selected "
            "data contained no reported manipulation before multilevel "
            "manipulation was injected."
        ),
        "has_row_level_positive_hint": True,
        "has_public_row_export": False,
        "has_matched_controls": True,
        "source_owned_or_owner_approved": False,
        "disposition": "blocked_injected_synthetic_labels",
        "reason": (
            "Useful method source, but injected manipulation labels violate the "
            "no generated/synthetic label rule for strict direct species closure."
        ),
    },
    {
        "candidate_id": "veryzhenko_spoofing_hft_ml",
        "name": "Detecting Spoofing in High Frequency Trading Using Machine Learning Techniques",
        "source_url": "https://www.institutlouisbachelier.org/wp-content/uploads/2024/03/detecting-spoofing-in-high-frequency-trading-using-machine-learning-techniques.pdf",
        "mirror_or_readback_url": "https://www.preprints.org/manuscript/202505.0199/v1",
        "target_species": "spoofing_layering",
        "evidence_readback": (
            "Primary PDF URL currently returned a small 404 HTML response in "
            "the local readback; public comparative tables describe the study "
            "as using simulated order book data."
        ),
        "has_row_level_positive_hint": True,
        "has_public_row_export": False,
        "has_matched_controls": False,
        "source_owned_or_owner_approved": False,
        "disposition": "blocked_simulated_or_unreachable_source_rows",
        "reason": (
            "No reachable owner-approved real positive/control row package was "
            "found; simulated order-book evidence is disallowed for strict R6."
        ),
    },
    {
        "candidate_id": "tao_day_ling_drapeau_2020_spoofing_hft",
        "name": "On Detecting Spoofing Strategies in High-Frequency Trading",
        "source_url": "https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3746263",
        "mirror_or_readback_url": "https://www.maths.ox.ac.uk/events/past/661",
        "target_species": "spoofing_layering_pinging",
        "evidence_readback": (
            "Public event/readback pages describe spoofing mechanics around "
            "order-book imbalance, order placement, cancellation, and execution."
        ),
        "has_row_level_positive_hint": False,
        "has_public_row_export": False,
        "has_matched_controls": False,
        "source_owned_or_owner_approved": False,
        "disposition": "blocked_method_source_no_row_export",
        "reason": (
            "Method/provenance only in public surfaces; no source-owned labeled "
            "positive/control rows or provenance manifest were found."
        ),
    },
]


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)

    ready = [
        row
        for row in CANDIDATES
        if row["has_row_level_positive_hint"]
        and row["has_public_row_export"]
        and row["has_matched_controls"]
        and row["source_owned_or_owner_approved"]
    ]
    owner_approval_targets = [
        row["candidate_id"]
        for row in CANDIDATES
        if row["disposition"] == "blocked_owner_approval_or_export_required"
    ]
    summary = {
        "run_id": RUN_ID,
        "scope": "R6 direct Manipulation: spoofing/layering positives plus matched normal controls",
        "requirements": REQUIREMENTS,
        "candidate_count": len(CANDIDATES),
        "ready_positive_control_sources": len(ready),
        "owner_approval_targets": owner_approval_targets,
        "accepted_rows_added": 0,
        "new_confidence_gate": False,
        "direct_species_coverage_closed": False,
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "trade_usable": False,
        "decision": "spoofing_layering_source_acquisition_screen_v1=no_ready_positive_control_intake_source",
        "candidates": CANDIDATES,
    }

    json_path = OUT_DIR / "spoofing_layering_source_acquisition_screen_v1.json"
    csv_path = OUT_DIR / "spoofing_layering_source_acquisition_screen_v1_candidates.csv"
    md_path = OUT_DIR / "spoofing_layering_source_acquisition_screen_v1.md"
    assertions_path = CHECK_DIR / "spoofing_layering_source_acquisition_screen_v1_assertions.out"

    json_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    with csv_path.open("w", newline="") as handle:
        fieldnames = [
            "candidate_id",
            "name",
            "source_url",
            "mirror_or_readback_url",
            "target_species",
            "has_row_level_positive_hint",
            "has_public_row_export",
            "has_matched_controls",
            "source_owned_or_owner_approved",
            "disposition",
            "reason",
        ]
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in CANDIDATES:
            writer.writerow({field: row[field] for field in fieldnames})

    lines = [
        "# Spoofing/Layering Source Acquisition Screen v1",
        "",
        f"Run ID: `{RUN_ID}`",
        "",
        "Focused follow-up to the `195728` strict acquisition contract and `200319` v26 completion audit. "
        "This screen targets only R6: source-owned spoofing/layering positives plus matched normal controls. "
        "Raw readbacks stayed under `/tmp/ict-engine-spoofing-layering-source-acquisition-screen-v1`; no raw data was committed.",
        "",
        "## Decision",
        "",
        f"`{summary['decision']}`",
        "",
        f"- Candidates screened: `{summary['candidate_count']}`.",
        f"- Ready positive/control intake sources found: `{summary['ready_positive_control_sources']}`.",
        f"- Owner-approval/export target retained: `{', '.join(owner_approval_targets) if owner_approval_targets else 'none'}`.",
        "- Accepted rows added: `0`; new confidence gate: `false`.",
        "- Direct species coverage closed: `false`.",
        "- Strict full objective achieved: `false`; `update_goal=false`.",
        "",
        "## Required Contract",
        "",
    ]
    for key in REQUIREMENTS:
        lines.append(f"- `{key}`")
    lines.extend(["", "## Candidate Disposition", ""])
    for row in CANDIDATES:
        lines.append(
            f"- `{row['candidate_id']}` ({row['target_species']}): `{row['disposition']}`. "
            f"Source: {row['source_url']}. Reason: {row['reason']}"
        )
    lines.extend(
        [
            "",
            "## Carry-Forward",
            "",
            "The closest acquisition target is `do_putnins_2023_detecting_layering_spoofing`: it appears to have real prosecuted-case provenance and some order/trade-level granularity, but it still needs owner-approved export or author/regulator cooperation before Board A can materialize `/tmp/ict-engine-direct-manipulation-row-intake/positive_spoofing_layering_rows.csv`, matched controls, and `provenance_manifest.json`.",
            "",
            "## Artifacts",
            "",
            f"- JSON: `{json_path}`",
            f"- Candidate CSV: `{csv_path}`",
            f"- Assertions: `{assertions_path}`",
        ]
    )
    md_path.write_text("\n".join(lines) + "\n")

    checks = [
        ("candidate_count", summary["candidate_count"] >= 5, str(summary["candidate_count"])),
        ("ready_positive_control_sources", summary["ready_positive_control_sources"] == 0, str(summary["ready_positive_control_sources"])),
        ("accepted_rows_added", summary["accepted_rows_added"] == 0, str(summary["accepted_rows_added"])),
        ("new_confidence_gate", summary["new_confidence_gate"] is False, str(summary["new_confidence_gate"]).lower()),
        ("strict_full_objective_achieved", summary["strict_full_objective_achieved"] is False, str(summary["strict_full_objective_achieved"]).lower()),
        ("update_goal", summary["update_goal"] is False, str(summary["update_goal"]).lower()),
        ("owner_approval_target_present", "do_putnins_2023_detecting_layering_spoofing" in owner_approval_targets, ",".join(owner_approval_targets)),
    ]
    assertion_lines = []
    ok = True
    for name, passed, value in checks:
        ok = ok and passed
        assertion_lines.append(f"{'PASS' if passed else 'FAIL'} {name}={value}")
    assertions_path.write_text("\n".join(assertion_lines) + "\n")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
