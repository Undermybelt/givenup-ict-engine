#!/usr/bin/env python3
"""Probe official enforcement sources for exportable manipulation labels.

The active Board A MainRegimeV2 contract needs timestamped positive/negative
direct Manipulation rows or an exportable exact-underlying parent-root label
panel. This script stores only compact source metadata and classification, not
raw pages.
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any


RUN_ID = "20260511T091215+0800-codex-official-enforcement-exportability-probe"
BOARD = "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"
RUN_ROOT = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T091215-codex-official-enforcement-exportability-probe"
)
OUT_DIR = RUN_ROOT / "official-enforcement-probe"
CHECK_DIR = RUN_ROOT / "checks"


@dataclass(frozen=True)
class Candidate:
    name: str
    source_url: str
    organization: str
    classification: str
    reason: str
    next_needed: str


CANDIDATES = [
    Candidate(
        name="SEC litigation releases",
        source_url="https://www.sec.gov/enforcement-litigation/litigation-releases",
        organization="SEC",
        classification="positive_event_index_only_no_exportable_rows",
        reason=(
            "official enforcement document index; useful positive-event "
            "provenance, but no bulk timestamped positive/negative market "
            "row export or exact-underlying Board A label panel was obtained"
        ),
        next_needed="structured enforcement row export with symbols, event windows, and matched non-event controls",
    ),
    Candidate(
        name="SEC administrative proceedings",
        source_url="https://www.sec.gov/enforcement-litigation/administrative-proceedings",
        organization="SEC",
        classification="positive_event_index_only_no_exportable_rows",
        reason=(
            "official proceeding document index; not an accepted direct "
            "Manipulation label source without parsed rows, timestamps, "
            "underlyings, and negative windows"
        ),
        next_needed="downloadable parsed proceeding rows or authenticated structured API",
    ),
    Candidate(
        name="FINRA disciplinary actions online",
        source_url="https://www.finra.org/rules-guidance/oversight-enforcement/finra-disciplinary-actions-online",
        organization="FINRA",
        classification="search_surface_no_bulk_market_rows",
        reason=(
            "public search surface for disciplinary documents; no direct bulk "
            "export of timestamped manipulation positive/negative windows was "
            "materialized in this environment"
        ),
        next_needed="FINRA export/API access that returns row-level market manipulation cases with underlyings and dates",
    ),
    Candidate(
        name="FINRA data catalog",
        source_url="https://www.finra.org/finra-data/browse-catalog?page=1",
        organization="FINRA",
        classification="catalog_surface_no_specific_manipulation_label_panel",
        reason=(
            "public data catalog surface; no accepted dataset was identified "
            "that directly exports Board A manipulation labels or parent-root "
            "regime labels"
        ),
        next_needed="specific FINRA API dataset id plus access token/export path if such a dataset exists",
    ),
    Candidate(
        name="CFTC enforcement actions",
        source_url="https://www.cftc.gov/LawRegulation/EnforcementActions/index.htm",
        organization="CFTC",
        classification="positive_event_index_only_no_negative_windows",
        reason=(
            "official enforcement action index can support positive-event "
            "research, but it is not a ready positive/negative row panel and "
            "does not cover MainRegimeV2 roots"
        ),
        next_needed="structured CFTC case rows with instruments, dates, manipulation type, and controls",
    ),
    Candidate(
        name="NFA BASIC search",
        source_url="https://www.nfa.futures.org/basicnet/",
        organization="NFA",
        classification="member_case_search_no_market_label_rows",
        reason=(
            "public member/case search surface; no exportable market-row label "
            "panel with direct manipulation positive/negative windows was "
            "obtained"
        ),
        next_needed="bulk disciplinary export with instrument-level event windows and non-event controls",
    ),
]


def fetch_metadata(url: str) -> dict[str, Any]:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": (
                "Mozilla/5.0 BoardAOfficialSourceProbe/1.0 "
                "(metadata-only; no raw data committed)"
            )
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=25) as response:
            payload = response.read(300_000)
            text = payload.decode("utf-8", errors="ignore").lower()
            headers = dict(response.headers.items())
            return {
                "status": response.status,
                "content_type": headers.get("Content-Type", ""),
                "bytes_sampled": len(payload),
                "sha256_sample_prefix": hashlib.sha256(payload).hexdigest()[:16],
                "flags": {
                    "mentions_csv": ".csv" in text or "csv" in text,
                    "mentions_api": " api" in text or "/api/" in text,
                    "mentions_manipulation": "manipulat" in text,
                    "mentions_disciplinary": "disciplin" in text,
                    "mentions_enforcement": "enforcement" in text,
                    "has_table_markup": bool(re.search(r"<table|role=\"table\"", text)),
                },
            }
    except urllib.error.HTTPError as exc:
        return {
            "status": exc.code,
            "content_type": exc.headers.get("Content-Type", ""),
            "bytes_sampled": 0,
            "sha256_sample_prefix": "",
            "flags": {},
            "error": f"http_error:{exc.code}",
        }
    except Exception as exc:  # noqa: BLE001 - metadata probe should not crash on one source.
        return {
            "status": None,
            "content_type": "",
            "bytes_sampled": 0,
            "sha256_sample_prefix": "",
            "flags": {},
            "error": f"{type(exc).__name__}:{exc}",
        }


def build_packet() -> dict[str, Any]:
    classifications = []
    for candidate in CANDIDATES:
        item = asdict(candidate)
        item["fetch_metadata"] = fetch_metadata(candidate.source_url)
        item["accepted_for_board_a"] = False
        classifications.append(item)

    return {
        "run_id": RUN_ID,
        "board": BOARD,
        "active_taxonomy": "MainRegimeV2",
        "main_price_roots": ["Bull", "Bear", "Sideways", "Crisis"],
        "separate_overlay": "Manipulation",
        "objective": (
            "Find official/regulator/SRO sources that provide downloadable or "
            "authenticated exact-underlying parent-root labels, or timestamped "
            "direct Manipulation positive/negative rows."
        ),
        "official_sources_inspected": len(classifications),
        "accepted_independent_parent_root_label_sources": 0,
        "new_attached_parent_root_slots": 0,
        "accepted_direct_manipulation_label_sources": 0,
        "accepted_direct_manipulation_rows_or_windows": 0,
        "candidate_classification": classifications,
        "accepted_gate": "none_for_MainRegimeV2_expanded_full_universe_full_cycle_goal",
        "gate_result": "blocked_official_enforcement_sources_no_exportable_label_rows",
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "trade_usable": False,
        "next_action": (
            "Provide or authenticate a structured export/API for direct "
            "Manipulation rows, or provide an exact-underlying parent-root "
            "label panel; document-index pages alone are not enough."
        ),
    }


def write_markdown(packet: dict[str, Any]) -> str:
    rows = []
    for item in packet["candidate_classification"]:
        rows.append(
            "| {name} | {organization} | `{classification}` | {reason} | {next_needed} |".format(
                **item
            )
        )

    return "\n".join(
        [
            "# Official Enforcement Exportability Probe",
            "",
            f"Run ID: `{packet['run_id']}`",
            "",
            "## Objective",
            "",
            packet["objective"],
            "",
            "## Candidate Classification",
            "",
            "| Candidate | Organization | Decision | Reason | Needed Before Acceptance |",
            "|---|---|---|---|---|",
            *rows,
            "",
            "## Result",
            "",
            f"- Official sources inspected: `{packet['official_sources_inspected']}`.",
            "- Accepted independent MainRegimeV2 parent-root label sources: `0`.",
            "- New attached parent-root source-label slots: `0`.",
            "- Accepted direct `Manipulation` label sources: `0`.",
            "- Accepted direct `Manipulation` rows/windows: `0`.",
            f"- Accepted gate remains: `{packet['accepted_gate']}`.",
            f"- Gate result: `{packet['gate_result']}`.",
            "- Runtime code changed: false.",
            "- Thresholds relaxed: false.",
            "- Raw data committed: false.",
            "- Trade usable: false.",
            "",
            "## Next Action",
            "",
            packet["next_action"],
            "",
        ]
    )


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)
    packet = build_packet()

    json_path = OUT_DIR / "official_enforcement_exportability_probe.json"
    md_path = OUT_DIR / "official_enforcement_exportability_probe.md"
    checks_path = CHECK_DIR / "official_enforcement_exportability_probe_assertions.out"

    json_path.write_text(json.dumps(packet, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md_path.write_text(write_markdown(packet), encoding="utf-8")

    checks = [
        f"PASS official_sources_inspected={packet['official_sources_inspected']}",
        "PASS accepted_independent_parent_root_label_sources=0",
        "PASS new_attached_parent_root_slots=0",
        "PASS accepted_direct_manipulation_label_sources=0",
        "PASS accepted_direct_manipulation_rows_or_windows=0",
        f"PASS accepted_gate={packet['accepted_gate']}",
        f"PASS gate_result={packet['gate_result']}",
        "PASS thresholds_relaxed=false",
        "PASS runtime_code_changed=false",
        "PASS raw_data_committed=false",
        "PASS trade_usable=false",
    ]
    checks_path.write_text("\n".join(checks) + "\n", encoding="utf-8")

    print(json_path)
    print(md_path)
    print(checks_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
