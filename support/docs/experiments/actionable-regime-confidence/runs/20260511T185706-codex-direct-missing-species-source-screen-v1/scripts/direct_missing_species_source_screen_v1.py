#!/usr/bin/env python3
"""Screen missing direct Manipulation species sources without accepting rows."""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = RUN_ROOT / "direct-missing-species-screen"
CHECK_DIR = RUN_ROOT / "checks"
OUT_JSON = OUT_DIR / "direct_missing_species_source_screen_v1.json"
OUT_MD = OUT_DIR / "direct_missing_species_source_screen_v1.md"
OUT_CSV = OUT_DIR / "direct_missing_species_source_screen_v1_candidates.csv"
OUT_ASSERT = CHECK_DIR / "direct_missing_species_source_screen_v1_assertions.out"


def repo_rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO))
    except ValueError:
        return str(path)


def candidates() -> list[dict[str, Any]]:
    return [
        {
            "source_family": "paper",
            "ref": "Learning from the Sequence of Order Events in the Stock Market",
            "url": "https://arxiv.org/abs/2204.12270",
            "species": "spoofing_layering",
            "row_surface": "method_and_prediction_task",
            "real_market_rows": False,
            "explicit_positive_labels": False,
            "matched_negative_controls": False,
            "provenance_rows": False,
            "disposition": "blocked_paper_method_no_exported_labeled_rows",
            "reason": "Paper is useful for order-event modeling, but this screen found no public source-owned positive spoofing/layering rows plus matched normal controls.",
        },
        {
            "source_family": "paper",
            "ref": "FX spoofing and pinging case study",
            "url": "https://www.sciencedirect.com/science/article/abs/pii/S0304405X21002368",
            "species": "spoofing_layering,pinging",
            "row_surface": "restricted_ebs_fx_order_book_study",
            "real_market_rows": True,
            "explicit_positive_labels": True,
            "matched_negative_controls": False,
            "provenance_rows": False,
            "disposition": "blocked_restricted_data_no_public_controls",
            "reason": "The study discusses real EBS order-book behavior, but the public surface is a paper/abstract rather than exportable row-level positives and matched controls.",
        },
        {
            "source_family": "paper",
            "ref": "Cross-market spoofing article",
            "url": "https://www.sciencedirect.com/science/article/pii/S1386418124000624",
            "species": "spoofing_layering",
            "row_surface": "restricted_high_frequency_cross_market_study",
            "real_market_rows": True,
            "explicit_positive_labels": True,
            "matched_negative_controls": False,
            "provenance_rows": False,
            "disposition": "blocked_restricted_case_data_no_public_row_export",
            "reason": "The article is relevant to spoofing mechanics, but no public source-owned row table with matched normal controls was located.",
        },
        {
            "source_family": "web_dataset_or_demo",
            "ref": "parasec Bitstamp spoofing visualisation",
            "url": "https://parasec.net/transmission/order-book-visualisation/",
            "species": "spoofing_layering",
            "row_surface": "visualized_bitstamp_orderbook_case",
            "real_market_rows": True,
            "explicit_positive_labels": False,
            "matched_negative_controls": False,
            "provenance_rows": False,
            "disposition": "blocked_visual_case_no_machine_readable_labels_controls",
            "reason": "A useful case-study/visualization surface, but not a replayable labeled positive/control dataset for the Board A verifier.",
        },
        {
            "source_family": "github",
            "ref": "codyrodgers/capstone-quote-stuffing",
            "url": "https://github.com/codyrodgers/capstone-quote-stuffing",
            "species": "quote_stuffing",
            "row_surface": "detection_project",
            "real_market_rows": True,
            "explicit_positive_labels": False,
            "matched_negative_controls": False,
            "provenance_rows": False,
            "disposition": "blocked_detection_project_no_source_owned_labels",
            "reason": "Project describes quote-stuffing detection over collected market data, but does not provide Board A direct positives, matched normal controls, and provenance files.",
        },
        {
            "source_family": "python_package",
            "ref": "microalpha PyPI",
            "url": "https://pypi.org/project/microalpha/",
            "species": "quote_stuffing,spoofing_layering",
            "row_surface": "feature_engineering_library",
            "real_market_rows": False,
            "explicit_positive_labels": False,
            "matched_negative_controls": False,
            "provenance_rows": False,
            "disposition": "blocked_feature_library_no_direct_labels",
            "reason": "A potentially useful feature library for future probes, but it is not a source-owned manipulation label dataset with controls.",
        },
        {
            "source_family": "huggingface",
            "ref": "nguyentranai07/HTrade_Analyze_all",
            "url": "https://huggingface.co/datasets/nguyentranai07/HTrade_Analyze_all",
            "species": "quote_stuffing,spoofing_layering,pinging",
            "row_surface": "text_or_instruction_dataset",
            "real_market_rows": False,
            "explicit_positive_labels": False,
            "matched_negative_controls": False,
            "provenance_rows": False,
            "disposition": "blocked_text_instruction_dataset_no_market_rows",
            "reason": "Hugging Face surface is not a real market row dataset with positive and matched-control event groups.",
        },
    ]


def write_csv(rows: list[dict[str, Any]]) -> None:
    fields = [
        "source_family",
        "ref",
        "url",
        "species",
        "row_surface",
        "real_market_rows",
        "explicit_positive_labels",
        "matched_negative_controls",
        "provenance_rows",
        "disposition",
        "reason",
    ]
    with OUT_CSV.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def write_md(payload: dict[str, Any]) -> None:
    lines = [
        "# Direct Missing Species Source Screen v1",
        "",
        f"Run ID: `{payload['run_id']}`",
        "",
        "Supplemental public-source screen for missing direct `Manipulation` species: `quote_stuffing`, `pinging`, and `spoofing_layering`. It does not download raw rows, fill intake files, or edit Current Cursor.",
        "",
        "## Decision",
        "",
        f"`{payload['decision']['gate_result']}`",
        "",
        f"- Candidates screened: `{payload['candidate_count']}`.",
        f"- Ready real positive/control sources: `{payload['ready_source_candidate_count']}`.",
        "- Accepted rows added: `0`.",
        "- New confidence gate: `false`.",
        "- Full objective achieved: `false`; `update_goal=false`.",
        "",
        "## Candidate Disposition",
        "",
    ]
    for row in payload["candidates"]:
        lines.append(
            f"- `{row['ref']}` ({row['species']}): `{row['disposition']}`. Source: {row['url']}"
        )
    lines.extend(
        [
            "",
            "## Guardrail",
            "",
            "Papers, case-study pages, feature libraries, demos, and text/instruction datasets can inform future probes, but Board A direct `Manipulation` still requires row-level positives, matched normal controls, provenance, and unchanged chronological/heldout validation before any 95% confidence claim.",
            "",
            "## Artifacts",
            "",
            f"- JSON: `{repo_rel(OUT_JSON)}`",
            f"- Candidate CSV: `{repo_rel(OUT_CSV)}`",
            f"- Assertions: `{repo_rel(OUT_ASSERT)}`",
        ]
    )
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)
    rows = candidates()
    ready = [
        row for row in rows
        if row["real_market_rows"]
        and row["explicit_positive_labels"]
        and row["matched_negative_controls"]
        and row["provenance_rows"]
    ]
    payload = {
        "run_id": "20260511T185706+0800-codex-direct-missing-species-source-screen-v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "artifact_type": "direct_missing_species_source_screen_v1",
        "current_cursor_edited": False,
        "missing_species_screened": ["quote_stuffing", "pinging", "spoofing_layering"],
        "candidate_count": len(rows),
        "ready_source_candidate_count": len(ready),
        "candidates": rows,
        "decision": {
            "gate_result": "direct_missing_species_source_screen_v1=no_ready_positive_control_source",
            "accepted_rows_added": 0,
            "new_confidence_gate": False,
            "full_direct_species_coverage": False,
            "strict_full_objective_achieved": False,
            "update_goal": False,
            "runtime_code_changed": False,
            "thresholds_relaxed": False,
            "raw_data_committed": False,
            "trade_usable": False,
        },
        "next": "Only promote a missing direct Manipulation species after acquiring real row-level positives, matched normal controls, provenance, and a verifier pass.",
    }
    OUT_JSON.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_csv(rows)
    write_md(payload)
    assertions = [
        "PASS candidate_count=7" if len(rows) == 7 else "FAIL candidate_count",
        "PASS ready_source_candidate_count=0" if len(ready) == 0 else "FAIL ready_source_candidate_count",
        "PASS accepted_rows_added=0",
        "PASS new_confidence_gate=false",
        "PASS strict_full_objective=false",
        "PASS current_cursor_edited=false",
    ]
    OUT_ASSERT.write_text("\n".join(assertions) + "\n", encoding="utf-8")
    if any(line.startswith("FAIL") for line in assertions):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
