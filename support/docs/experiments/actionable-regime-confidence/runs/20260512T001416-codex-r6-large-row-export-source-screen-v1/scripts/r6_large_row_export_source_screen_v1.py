#!/usr/bin/env python3
"""Record a targeted web/source screen for a large R6 direct row export.

The active blocker is no longer pooled confidence; it is row debt for split and
species validation. This screen records whether public/owner surfaces found in
the targeted search expose a Board-A-ready positive/control row export.
"""

from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


RUN_ID = "20260512T001416-codex-r6-large-row-export-source-screen-v1"
REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs" / RUN_ID
OUT = RUN_ROOT / "r6-large-row-export-source-screen"
CHECKS = RUN_ROOT / "checks"
BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"
DRYRUN = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs"
    / "20260512T001116-codex-r6-grouped-heldout-contract-dryrun-v1"
    / "r6-grouped-heldout-contract-dryrun/r6_grouped_heldout_contract_dryrun_v1.json"
)


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO))
    except ValueError:
        return str(path)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)
    missing = [rel(path) for path in [BOARD, DRYRUN] if not path.exists()]
    if missing:
        payload = {
            "run_id": RUN_ID,
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "status": "blocked",
            "reason": "missing_required_inputs",
            "missing_inputs": missing,
            "update_goal": False,
        }
        write_json(OUT / "r6_large_row_export_source_screen_v1.json", payload)
        return 2

    sources = [
        {
            "source_id": "finra_potential_manipulation_report",
            "url": "https://www.finra.org/compliance-tools/report-center/cross-market-equities-supervision/potential-manipulation-report",
            "owner_or_surface": "FINRA",
            "surface_type": "official_supervision_report_schema",
            "positive_rows_public": False,
            "matched_controls_public": False,
            "large_export_public": False,
            "could_be_owner_approved": True,
            "decision": "owner_report_schema_not_public_row_export",
            "next": "Use as an owner/report request target, not as accepted Board A rows.",
        },
        {
            "source_id": "cftc_public_orders",
            "url": "https://www.cftc.gov/LawRegulation/Enforcement/EnforcementActions/index.htm",
            "owner_or_surface": "CFTC",
            "surface_type": "official_case_orders_and_complaints",
            "positive_rows_public": True,
            "matched_controls_public": "some_case_examples_only",
            "large_export_public": False,
            "could_be_owner_approved": True,
            "decision": "official_examples_continue_but_not_large_export",
            "next": "Continue only if extracting rows that fill exact split/species cells; generic examples are insufficient.",
        },
        {
            "source_id": "bmll_level3_data",
            "url": "https://bmlltech.com/",
            "owner_or_surface": "BMLL",
            "surface_type": "commercial_level3_order_book_history",
            "positive_rows_public": False,
            "matched_controls_public": "normal_market_controls_possible_with_license",
            "large_export_public": False,
            "could_be_owner_approved": True,
            "decision": "commercial_raw_controls_no_public_manipulation_labels",
            "next": "Potential broad normal controls only after licensed/user-provided export; not a positive-label source.",
        },
        {
            "source_id": "polymarket_tick_orderbook_kaggle",
            "url": "https://www.kaggle.com/datasets/marvingozo/polymarket-tick-level-orderbook-dataset",
            "owner_or_surface": "Kaggle community dataset",
            "surface_type": "raw_orderbook_ticks",
            "positive_rows_public": False,
            "matched_controls_public": "raw_normal_context_only",
            "large_export_public": True,
            "could_be_owner_approved": False,
            "decision": "raw_unlabeled_orderbook_not_direct_manipulation_export",
            "next": "Fail closed for Board A labels; usable only as exploratory normal/control context if approved.",
        },
        {
            "source_id": "tardis_crypto_market_data",
            "url": "https://tardis.dev/",
            "owner_or_surface": "Tardis.dev",
            "surface_type": "commercial_crypto_l2_l3_orderbook_trades",
            "positive_rows_public": False,
            "matched_controls_public": "normal_market_controls_possible_with_license",
            "large_export_public": False,
            "could_be_owner_approved": True,
            "decision": "raw_orderbook_no_source_owned_manipulation_labels",
            "next": "Potential controls only after owner/user export; not enough for direct species positives.",
        },
        {
            "source_id": "dark_pool_synthetic_hf",
            "url": "https://huggingface.co/datasets/synthetic-trading-data/dark-pool-pack",
            "owner_or_surface": "Hugging Face synthetic dataset",
            "surface_type": "synthetic_labeled_trading_data",
            "positive_rows_public": True,
            "matched_controls_public": True,
            "large_export_public": True,
            "could_be_owner_approved": False,
            "decision": "synthetic_generated_labels_fail_closed",
            "next": "Do not use for Board A source-owned/owner-approved confidence.",
        },
    ]

    ready = [
        row
        for row in sources
        if row["positive_rows_public"] is True
        and row["matched_controls_public"] is True
        and row["large_export_public"] is True
        and row["could_be_owner_approved"] is True
    ]
    owner_request_targets = [
        row["source_id"]
        for row in sources
        if row["could_be_owner_approved"] is True and row["decision"] != "synthetic_generated_labels_fail_closed"
    ]
    dryrun = json.loads(DRYRUN.read_text(encoding="utf-8"))
    payload = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "board_sha256_at_start": sha256(BOARD),
        "dryrun_ref": {
            "path": rel(DRYRUN),
            "gate_result": dryrun.get("decision", {}).get("gate_result"),
        },
        "search_queries": [
            "public dataset market manipulation spoofing layering labeled order book rows",
            "CFTC spoofing order data public dataset row level matched controls",
            "FINRA potential manipulation report data download layering spoofing sample rows",
            "Kaggle market manipulation detection dataset spoofing quote stuffing",
        ],
        "source_screen_csv": rel(OUT / "r6_large_row_export_source_screen_v1_sources.csv"),
        "sources_screened": len(sources),
        "ready_large_owner_exports": len(ready),
        "owner_request_targets": owner_request_targets,
        "decision": {
            "gate_result": "r6_large_row_export_source_screen_v1=no_ready_public_large_owner_export_found",
            "accepted_rows_added": 0,
            "new_confidence_gate": False,
            "strict_full_objective_achieved": False,
            "update_goal": False,
            "runtime_code_changed": False,
            "shared_intake_mutated": False,
            "thresholds_relaxed": False,
            "raw_data_committed": False,
            "external_requests_sent": True,
            "trade_usable": False,
        },
        "next_action": (
            "Treat R6 as blocked on owner/user-provided direct export: FINRA/CFTC/BMLL/Tardis "
            "are owner-request targets, while public raw/synthetic datasets remain fail-closed."
        ),
    }
    fields = [
        "source_id",
        "url",
        "owner_or_surface",
        "surface_type",
        "positive_rows_public",
        "matched_controls_public",
        "large_export_public",
        "could_be_owner_approved",
        "decision",
        "next",
    ]
    write_csv(OUT / "r6_large_row_export_source_screen_v1_sources.csv", sources, fields)
    write_json(OUT / "r6_large_row_export_source_screen_v1.json", payload)

    report = f"""# R6 Large Row Export Source Screen v1

- Run id: `{RUN_ID}`.
- Sources screened: `{len(sources)}`.
- Ready large owner-approved public exports found: `{len(ready)}`.
- Gate result: `{payload["decision"]["gate_result"]}`.
- Strict full objective achieved: `false`; `update_goal=false`.
- Runtime code changed: `false`; shared intake mutated: `false`; thresholds relaxed: `false`; raw data committed: `false`; external requests sent: `true`; trade usable: `false`.

## Result

No public source screened exposes a Board-A-ready large export with direct manipulation positive rows, matched controls, provenance, and owner-approved status. FINRA/CFTC/BMLL/Tardis are retained as owner/user request targets; public raw order-book or synthetic datasets remain fail-closed.

## Artifacts

- JSON: `{rel(OUT / "r6_large_row_export_source_screen_v1.json")}`
- Source screen CSV: `{rel(OUT / "r6_large_row_export_source_screen_v1_sources.csv")}`

## Next

Treat R6 as blocked on owner/user-provided direct export, or get explicit approval for a different validation contract before another R6 split-acceptance attempt.
"""
    (OUT / "r6_large_row_export_source_screen_v1.md").write_text(report, encoding="utf-8")

    checks = [
        ("ready_large_owner_exports_zero", len(ready) == 0),
        ("owner_request_targets_present", len(owner_request_targets) >= 3),
        ("new_confidence_gate_false", payload["decision"]["new_confidence_gate"] is False),
        ("strict_full_objective_not_complete", payload["decision"]["strict_full_objective_achieved"] is False),
        ("update_goal_false", payload["decision"]["update_goal"] is False),
    ]
    (CHECKS / "r6_large_row_export_source_screen_v1_assertions.out").write_text(
        "".join(f"{name}={'PASS' if passed else 'FAIL'}\n" for name, passed in checks),
        encoding="utf-8",
    )
    return 0 if all(passed for _, passed in checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
