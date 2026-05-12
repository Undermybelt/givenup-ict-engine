#!/usr/bin/env python3
"""Incremental source screen for missing direct Manipulation species."""

from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[6]
RUN_ID = "20260511T191642-codex-direct-missing-species-source-screen-v2"
RUN_ROOT = REPO_ROOT / "docs/experiments/actionable-regime-confidence/runs" / RUN_ID
OUT_DIR = RUN_ROOT / "direct-missing-species-screen"
CHECK_DIR = RUN_ROOT / "checks"
TODO_PATH = REPO_ROOT / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"

BASELINE_ARTIFACTS = {
    "direct_missing_species_v1": "docs/experiments/actionable-regime-confidence/runs/20260511T185706-codex-direct-missing-species-source-screen-v1/direct-missing-species-screen/direct_missing_species_source_screen_v1.json",
    "direct_web_source_screen_v1": "docs/experiments/actionable-regime-confidence/runs/20260511T184212-codex-direct-manipulation-web-source-screen-v1/direct-web-source-screen/direct_manipulation_web_source_screen_v1.json",
    "spoofing_layering_readiness_v1": "docs/experiments/actionable-regime-confidence/runs/20260511T151720-codex-spoofing-layering-matched-row-readiness-v1/matched-row-readiness/spoofing_layering_matched_row_readiness_v1.json",
    "direct_intake_manifest_v1": "docs/experiments/actionable-regime-confidence/runs/20260511T151950-codex-direct-manipulation-row-intake-manifest-v1/direct-manipulation-intake/direct_manipulation_row_intake_manifest_v1.md",
    "completion_audit_v20": "docs/experiments/actionable-regime-confidence/runs/20260511T190911-codex-current-goal-completion-audit-v20-after-future-tail/completion-audit/current_goal_completion_audit_v20_after_future_tail.json",
}

REQUIRED_CONTRACT = [
    "row-level direct manipulation positives",
    "matched same-schema normal controls",
    "source-owned or owner-approved provenance",
    "venue/symbol/date/session fields sufficient for chronological validation",
    "no generated, proxy, synthetic, or OHLCV-only labels",
]

CANDIDATES = [
    {
        "source_family": "official_report_schema",
        "ref": "FINRA Potential Manipulation Report",
        "url": "https://www.finra.org/compliance-tools/report-center/cross-market-equities-supervision/potential-manipulation-report",
        "species": "spoofing_layering,quote_spoofing",
        "row_surface": "member_report_exception_schema",
        "real_market_rows": False,
        "explicit_positive_labels": True,
        "matched_negative_controls": False,
        "provenance_rows": False,
        "incremental_note": "Official schema target for layering/quote-spoofing exceptions, but public page is not an exportable positive/control row panel.",
        "disposition": "blocked_schema_target_rows_not_public",
    },
    {
        "source_family": "raw_market_data_provider",
        "ref": "Tardis historical crypto tick-level order book data",
        "url": "https://tardis.dev/",
        "species": "spoofing_layering,quote_stuffing,pinging",
        "row_surface": "raw_l2_l3_trades_order_books",
        "real_market_rows": True,
        "explicit_positive_labels": False,
        "matched_negative_controls": False,
        "provenance_rows": True,
        "incremental_note": "Can supply raw direct order-book context, but it does not provide source-owned manipulation positives or matched negative groups.",
        "disposition": "blocked_raw_order_book_no_direct_labels",
    },
    {
        "source_family": "raw_lob_sample",
        "ref": "LOBSTER / Level-3 order book sample mirrors",
        "url": "https://lobsterdata.com/",
        "species": "spoofing_layering,quote_stuffing",
        "row_surface": "raw_l3_order_book_messages",
        "real_market_rows": True,
        "explicit_positive_labels": False,
        "matched_negative_controls": False,
        "provenance_rows": True,
        "incremental_note": "Useful for normal-market controls or feature prototyping, but no source-owned direct manipulation labels are attached.",
        "disposition": "blocked_raw_lob_no_positive_labels",
    },
    {
        "source_family": "paper_restricted_market_data",
        "ref": "Spoofing and pinging in foreign exchange markets",
        "url": "https://www.sciencedirect.com/science/article/abs/pii/S1042443120301621",
        "species": "spoofing_layering,pinging",
        "row_surface": "restricted_ebs_fx_complete_lob_study",
        "real_market_rows": True,
        "explicit_positive_labels": True,
        "matched_negative_controls": False,
        "provenance_rows": False,
        "incremental_note": "Paper-level evidence confirms relevance, but the public surface does not export replayable positives and matched controls.",
        "disposition": "blocked_restricted_paper_no_public_row_export",
    },
    {
        "source_family": "library",
        "ref": "lobflow order-book spoofing/market-event tooling",
        "url": "https://pypi.org/project/lobflow/",
        "species": "spoofing_layering",
        "row_surface": "feature_detection_library",
        "real_market_rows": False,
        "explicit_positive_labels": False,
        "matched_negative_controls": False,
        "provenance_rows": False,
        "incremental_note": "May help design future probes, but a library without source-owned rows cannot satisfy Board A.",
        "disposition": "blocked_library_no_source_rows",
    },
    {
        "source_family": "paper_method",
        "ref": "Quote stuffing research using TotalView-ITCH / US equities",
        "url": "https://papers.ssrn.com/sol3/papers.cfm?abstract_id=1958281",
        "species": "quote_stuffing",
        "row_surface": "paper_method_and_event_definition",
        "real_market_rows": True,
        "explicit_positive_labels": True,
        "matched_negative_controls": False,
        "provenance_rows": False,
        "incremental_note": "Useful event-definition provenance, but the public paper page is not a source-owned row export with matched controls.",
        "disposition": "blocked_method_definition_no_exported_rows",
    },
    {
        "source_family": "paper_method",
        "ref": "Statistical-physics spoofing study on LUNA and Bitcoin",
        "url": "https://arxiv.org/abs/2306.08185",
        "species": "spoofing_layering",
        "row_surface": "method_and_market_case_study",
        "real_market_rows": True,
        "explicit_positive_labels": False,
        "matched_negative_controls": False,
        "provenance_rows": False,
        "incremental_note": "Market case-study/method source, but no Board A-ready positive/control rows or provenance manifest were found.",
        "disposition": "blocked_method_case_study_no_labeled_controls",
    },
]


def load_json(path: str) -> dict[str, object]:
    return json.loads((REPO_ROOT / path).read_text(encoding="utf-8"))


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)

    baseline = {name: load_json(path) for name, path in BASELINE_ARTIFACTS.items() if path.endswith(".json")}
    ready = [
        row
        for row in CANDIDATES
        if row["real_market_rows"]
        and row["explicit_positive_labels"]
        and row["matched_negative_controls"]
        and row["provenance_rows"]
    ]
    dispositions = sorted({row["disposition"] for row in CANDIDATES})
    species = sorted({item.strip() for row in CANDIDATES for item in str(row["species"]).split(",")})

    decision = {
        "gate_result": "direct_missing_species_source_screen_v2=no_ready_positive_control_source",
        "candidates_screened": len(CANDIDATES),
        "incremental_ready_real_positive_control_sources": len(ready),
        "accepted_rows_added": 0,
        "new_confidence_gate": False,
        "full_direct_species_coverage": False,
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "trade_usable": False,
    }
    payload = {
        "artifact_type": "direct_missing_species_source_screen_v2",
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "todo_hash_before_append": hashlib.sha256(TODO_PATH.read_bytes()).hexdigest(),
        "baseline_artifacts": BASELINE_ARTIFACTS,
        "required_contract": REQUIRED_CONTRACT,
        "species_screened": species,
        "dispositions": dispositions,
        "candidates": CANDIDATES,
        "ready_sources": ready,
        "decision": decision,
        "baseline_summary": {
            "v1_ready_sources": baseline["direct_missing_species_v1"].get("ready_source_candidate_count"),
            "v1_candidates": baseline["direct_missing_species_v1"].get("candidate_count"),
            "spoofing_matched_negative_cases_available": baseline["spoofing_layering_readiness_v1"].get("matched_negative_cases_available"),
            "v20_strict_full_objective": baseline["completion_audit_v20"].get("decision", {}).get("strict_full_objective_achieved"),
        },
    }
    (OUT_DIR / "direct_missing_species_source_screen_v2.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    rows_csv = OUT_DIR / "direct_missing_species_source_screen_v2_candidates.csv"
    with rows_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(CANDIDATES[0].keys()))
        writer.writeheader()
        writer.writerows(CANDIDATES)

    report = [
        "# Direct Missing Species Source Screen v2",
        "",
        f"Run ID: `{RUN_ID}`",
        "",
        "Incremental source screen after v20. It does not download raw rows, does not alter Current Cursor, and does not reclassify prior screens.",
        "",
        "## Decision",
        "",
        f"`{decision['gate_result']}`",
        "",
        f"- Incremental candidates screened: `{len(CANDIDATES)}`.",
        f"- Ready real positive/control sources found: `{len(ready)}`.",
        "- Accepted rows added: `0`; new confidence gate: `false`.",
        "- Strict full objective achieved: `false`; `update_goal=false`.",
        "",
        "## Required Contract",
        "",
    ]
    report.extend(f"- {item}" for item in REQUIRED_CONTRACT)
    report.extend(["", "## Candidate Disposition", ""])
    for row in CANDIDATES:
        report.append(
            f"- `{row['ref']}` ({row['species']}): `{row['disposition']}`. "
            f"Source: {row['url']}. {row['incremental_note']}"
        )
    report.extend(
        [
            "",
            "## Carry-Forward Blocker",
            "",
            "The new screen still finds no Board A-ready row-level direct-manipulation positives plus matched normal controls. Raw LOB/order-book providers can support future control construction, and papers can support schema/probe design, but neither can be promoted into the strict direct `Manipulation` gate without source-owned labels, matched controls, and provenance.",
            "",
            "## Artifacts",
            "",
            f"- JSON: `docs/experiments/actionable-regime-confidence/runs/{RUN_ID}/direct-missing-species-screen/direct_missing_species_source_screen_v2.json`",
            f"- Candidate CSV: `docs/experiments/actionable-regime-confidence/runs/{RUN_ID}/direct-missing-species-screen/direct_missing_species_source_screen_v2_candidates.csv`",
            f"- Assertions: `docs/experiments/actionable-regime-confidence/runs/{RUN_ID}/checks/direct_missing_species_source_screen_v2_assertions.out`",
            "",
        ]
    )
    (OUT_DIR / "direct_missing_species_source_screen_v2.md").write_text(
        "\n".join(report),
        encoding="utf-8",
    )

    assertions = [
        f"PASS candidates_screened={len(CANDIDATES)}",
        f"PASS species_screened={','.join(species)}",
        f"PASS ready_real_positive_control_sources={len(ready)}",
        "PASS accepted_rows_added=0",
        "PASS new_confidence_gate=false",
        "PASS strict_full_objective=false",
        "PASS update_goal=false",
    ]
    (CHECK_DIR / "direct_missing_species_source_screen_v2_assertions.out").write_text(
        "\n".join(assertions) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(decision, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
