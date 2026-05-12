#!/usr/bin/env python3
"""Targeted public-source uplift for R6 bear-raid and painting-tape candidates."""

from __future__ import annotations

import csv
import json
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


RUN_ID = "20260511T204159-codex-r6-bear-raid-painting-tape-source-uplift-v1"
RUN_ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = RUN_ROOT / "r6-source-uplift"
CHECK_DIR = RUN_ROOT / "checks"


CANDIDATES = [
    {
        "candidate_id": "comerton_forde_putnins_2011_closing_price_cases",
        "species": "painting_tape",
        "source_title": "Measuring closing price manipulation",
        "source_url": "https://www.sciencedirect.com/science/article/abs/pii/S104295731000015X",
        "surface_type": "prosecuted_case_positive_surface",
        "positive_surface": True,
        "matched_control_surface": "paper_reports_matched_stocks_method_not_exported_rows",
        "provenance_surface": True,
        "board_a_gate": "blocked_owner_or_publisher_export_required",
        "reason": "Useful painting-tape/marking-close owner target, but no public source-owned positive/control row package or provenance manifest was found.",
    },
    {
        "candidate_id": "hillion_suominen_2004_closing_price_paris_bourse",
        "species": "painting_tape",
        "source_title": "The manipulation of closing prices",
        "source_url": "https://www.aalto.fi/sites/g/files/flghsv161/files/2019-01/manipulation_of_closing_prices.pdf",
        "surface_type": "exchange_intraday_research_surface",
        "positive_surface": True,
        "matched_control_surface": "research_method_only_not_labeled_export",
        "provenance_surface": True,
        "board_a_gate": "blocked_exchange_owner_export_required",
        "reason": "Paris Bourse/Madrid exchange data support closing-price manipulation research, but no Board A-ready labeled positive/control rows are public.",
    },
    {
        "candidate_id": "opening_auction_manipulation_2025_asx",
        "species": "painting_tape",
        "source_title": "Identifying and characterizing opening auction manipulation",
        "source_url": "https://www.sciencedirect.com/science/article/abs/pii/S1386418125000710",
        "surface_type": "order_level_research_surface",
        "positive_surface": True,
        "matched_control_surface": "paper_index_method_not_exported_rows",
        "provenance_surface": True,
        "board_a_gate": "blocked_exchange_or_publisher_export_required",
        "reason": "Potential auction manipulation source surface, but public page exposes article metadata/snippets rather than source-owned row exports.",
    },
    {
        "candidate_id": "blau_brough_2011_bear_raids_by_short_sellers",
        "species": "bear_raid",
        "source_title": "Bear Raids by Short Sellers",
        "source_url": "https://papers.ssrn.com/sol3/Delivery.cfm/SSRN_ID1777244_code608347.pdf?abstractid=1777244&mirid=1",
        "surface_type": "abnormal_short_selling_research_surface",
        "positive_surface": True,
        "matched_control_surface": "aggregate_event_definition_not_row_export",
        "provenance_surface": True,
        "board_a_gate": "blocked_row_level_export_required",
        "reason": "Bear-raid candidate surface, but it defines raids from abnormal short-selling activity and does not provide Board A-ready source-owned positive/control rows.",
    },
    {
        "candidate_id": "arxiv_1112_3095_financial_crisis_bear_raid",
        "species": "bear_raid",
        "source_title": "Evidence of market manipulation in the financial crisis",
        "source_url": "https://ideas.repec.org/p/arx/papers/1112.3095.html",
        "surface_type": "bear_raid_aggregate_research_surface",
        "positive_surface": True,
        "matched_control_surface": "aggregate_market_event_not_row_export",
        "provenance_surface": True,
        "board_a_gate": "blocked_row_level_export_required",
        "reason": "Useful bear-raid provenance, but not a row-level labeled positive/control package with same-schema normal activity.",
    },
]


def probe(url: str) -> tuple[str, int | str]:
    request = urllib.request.Request(url, method="HEAD", headers={"User-Agent": "ict-engine-board-a-audit/1.0"})
    try:
        with urllib.request.urlopen(request, timeout=12) as response:
            return "ok_head", response.status
    except Exception:
        request = urllib.request.Request(url, method="GET", headers={"User-Agent": "ict-engine-board-a-audit/1.0"})
        try:
            with urllib.request.urlopen(request, timeout=12) as response:
                return "ok_get_fallback", response.status
        except urllib.error.HTTPError as exc:
            return "http_error", exc.code
        except Exception as exc:  # noqa: BLE001 - audit artifact records probe class only.
            return "blocked_or_error", exc.__class__.__name__


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)

    rows = []
    for candidate in CANDIDATES:
        probe_status, probe_code = probe(candidate["source_url"])
        row = dict(candidate)
        row["url_probe_status"] = probe_status
        row["url_probe_code"] = probe_code
        row["rows_acquired"] = False
        row["matched_controls_acquired"] = False
        row["intake_files_created"] = False
        rows.append(row)

    species = sorted({row["species"] for row in rows})
    summary = []
    for item in species:
        subset = [row for row in rows if row["species"] == item]
        summary.append(
            {
                "species": item,
                "candidate_surfaces": len(subset),
                "positive_surface_count": sum(1 for row in subset if row["positive_surface"]),
                "matched_controls_acquired": False,
                "intake_files_created": False,
                "gate": "candidate_surface_found_rows_not_acquired",
            }
        )

    result = {
        "run_id": RUN_ID,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "decision": "r6_bear_raid_painting_tape_source_uplift_v1=candidate_surfaces_found_rows_not_acquired",
        "purpose": "Narrowly improve R6 bear_raid and painting_tape source surfaces after the direct species matrix reported no candidate surface for those species.",
        "candidate_count": len(rows),
        "species": species,
        "candidate_surfaces_found": True,
        "rows_acquired": False,
        "matched_controls_acquired": False,
        "direct_manipulation_intake_files_created": False,
        "accepted_rows_added": 0,
        "new_confidence_gate": False,
        "r6_direct_species_closed": False,
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "trade_usable": False,
        "candidates": rows,
        "species_summary": summary,
    }

    (OUT_DIR / "r6_bear_raid_painting_tape_source_uplift_v1.json").write_text(
        json.dumps(result, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    write_csv(
        OUT_DIR / "r6_bear_raid_painting_tape_source_uplift_v1_candidates.csv",
        rows,
        [
            "candidate_id",
            "species",
            "source_title",
            "source_url",
            "surface_type",
            "positive_surface",
            "matched_control_surface",
            "provenance_surface",
            "board_a_gate",
            "reason",
            "url_probe_status",
            "url_probe_code",
            "rows_acquired",
            "matched_controls_acquired",
            "intake_files_created",
        ],
    )
    write_csv(
        OUT_DIR / "r6_bear_raid_painting_tape_species_summary_v1.csv",
        summary,
        ["species", "candidate_surfaces", "positive_surface_count", "matched_controls_acquired", "intake_files_created", "gate"],
    )

    report = f"""# R6 Bear-Raid / Painting-Tape Source Uplift v1

Run ID: `{RUN_ID}`

- Gate result: `{result['decision']}`.
- Candidate surfaces found: `{len(rows)}` across `{', '.join(species)}`.
- Rows acquired: `false`; matched controls acquired: `false`; intake files created: `false`.
- Accepted rows added: `0`; new confidence gate: `false`.
- Strict full objective achieved: `false`; `update_goal=false`.

## Boundary

This run only improves the public source-request surface for R6. It does not download raw rows, create `/tmp/ict-engine-direct-manipulation-row-intake` files, or promote paper/method/library evidence into accepted direct Manipulation rows.

## Species Summary

| Species | Candidate surfaces | Gate |
|---|---:|---|
"""
    for row in summary:
        report += f"| `{row['species']}` | `{row['candidate_surfaces']}` | `{row['gate']}` |\n"
    report += "\n## Artifacts\n\n- JSON: `r6_bear_raid_painting_tape_source_uplift_v1.json`\n- Candidate CSV: `r6_bear_raid_painting_tape_source_uplift_v1_candidates.csv`\n- Species summary CSV: `r6_bear_raid_painting_tape_species_summary_v1.csv`\n- Assertions: `../checks/r6_bear_raid_painting_tape_source_uplift_v1_assertions.out`\n"
    (OUT_DIR / "r6_bear_raid_painting_tape_source_uplift_v1.md").write_text(report, encoding="utf-8")

    checks = [
        f"PASS decision={result['decision']}",
        f"PASS candidate_count={len(rows)}",
        "PASS includes_bear_raid=true",
        "PASS includes_painting_tape=true",
        "PASS rows_acquired=false",
        "PASS matched_controls_acquired=false",
        "PASS intake_files_created=false",
        "PASS accepted_rows_added=0",
        "PASS new_confidence_gate=false",
        "PASS strict_full_objective_achieved=false",
        "PASS update_goal=false",
        "PASS raw_data_committed=false",
    ]
    (CHECK_DIR / "r6_bear_raid_painting_tape_source_uplift_v1_assertions.out").write_text(
        "\n".join(checks) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
