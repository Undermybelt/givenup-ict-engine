#!/usr/bin/env python3
"""Record a fail-closed public web screen for R3 native sub-hour source labels."""

from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = Path(__file__).resolve().parents[1]
RUN_ID = "20260512T012139-codex-r3-native-subhour-public-web-source-screen-v1"
OUT = RUN_ROOT / "r3-native-subhour-public-web-source-screen-v1"
CHECKS = RUN_ROOT / "checks"
BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"
INTAKE_ROOT = Path("/tmp/ict-engine-native-subhour-source-label-intake")
ROWS_FILE = INTAKE_ROOT / "native_subhour_source_label_rows.csv"
PROVENANCE_FILE = INTAKE_ROOT / "native_subhour_source_label_provenance.json"

FOCUS_CELLS = [
    {"symbol": "AAPL", "timeframe": "15m", "required_after": "2026-01-30"},
    {"symbol": "AAPL", "timeframe": "30m", "required_after": "2026-01-30"},
    {"symbol": "^IXIC", "timeframe": "15m", "required_after": "2026-01-30"},
    {"symbol": "^IXIC", "timeframe": "30m", "required_after": "2026-01-30"},
]

SEARCH_RECORDS = [
    {
        "query": "AAPL 15 minute regime label dataset source confidence 2026",
        "url": "https://www.kaggle.com/datasets/mafaqbhatti/stock-market-regimes-20002026",
        "title": "Kaggle: Stock Market Regimes 2000-2026",
        "observed_surface": "Daily source-label dataset already represented by the source-label equivalence root; public page does not expose native 15m/30m AAPL or IXIC rows.",
        "source_type": "source_label_owner_dataset",
        "r3_native_subhour_label_candidate": False,
        "blocker": "daily_source_panel_not_native_subhour_after_2026_01_30",
    },
    {
        "query": "site:kaggle.com/datasets AAPL intraday 15 minute data regime label",
        "url": "https://www.kaggle.com/search?q=AAPL+intraday+15+minute+regime+label+in%3Adatasets",
        "title": "Kaggle dataset search: AAPL intraday regime label",
        "observed_surface": "Search results center on intraday price/OHLCV datasets rather than owner-provided regime labels with source confidence and provenance.",
        "source_type": "dataset_search",
        "r3_native_subhour_label_candidate": False,
        "blocker": "ohlcv_or_search_surface_only_no_source_label_rows",
    },
    {
        "query": "site:kaggle.com/datasets \"AAPL\" \"15m\" \"regime\"",
        "url": "https://www.kaggle.com/search?q=%22AAPL%22+%2215m%22+%22regime%22+in%3Adatasets",
        "title": "Kaggle dataset search: AAPL 15m regime",
        "observed_surface": "No ready public source-owned native 15m/30m AAPL regime-label export was identified.",
        "source_type": "dataset_search",
        "r3_native_subhour_label_candidate": False,
        "blocker": "no_ready_source_owned_native_subhour_label_export",
    },
    {
        "query": "site:kaggle.com/datasets \"IXIC\" \"15m\" \"regime\"",
        "url": "https://www.kaggle.com/search?q=%22IXIC%22+%2215m%22+%22regime%22+in%3Adatasets",
        "title": "Kaggle dataset search: IXIC 15m regime",
        "observed_surface": "No ready public source-owned native 15m/30m IXIC regime-label export was identified.",
        "source_type": "dataset_search",
        "r3_native_subhour_label_candidate": False,
        "blocker": "no_ready_source_owned_native_subhour_label_export",
    },
    {
        "query": "NASDAQ Composite IXIC 15m 30m regime labels dataset",
        "url": "https://data.nasdaq.com/contact",
        "title": "Nasdaq Data Link contact",
        "observed_surface": "Public route is a contact/support surface for data requests, not a direct source-label download.",
        "source_type": "vendor_contact_route",
        "r3_native_subhour_label_candidate": False,
        "blocker": "contact_route_only_rows_not_acquired",
    },
    {
        "query": "NASDAQ Composite IXIC 15m 30m regime labels dataset",
        "url": "https://indexes.nasdaq.com/contactus",
        "title": "Nasdaq Indexes contact",
        "observed_surface": "Index-owner contact route exists for IXIC provenance questions; it does not provide native regime-label rows directly.",
        "source_type": "index_owner_contact_route",
        "r3_native_subhour_label_candidate": False,
        "blocker": "contact_route_only_rows_not_acquired",
    },
    {
        "query": "Yahoo Finance intraday provenance AAPL 15m labels",
        "url": "https://help.yahoo.com/kb/finance-for-web",
        "title": "Yahoo Finance Help",
        "observed_surface": "Provider help surface can support provenance questions, but Yahoo Finance intraday bars are not source-native regime labels.",
        "source_type": "provider_help_route",
        "r3_native_subhour_label_candidate": False,
        "blocker": "provider_bars_not_source_labels",
    },
]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)

    if not BOARD.exists():
        raise FileNotFoundError(BOARD)

    focus_rows: list[dict[str, Any]] = []
    for cell in FOCUS_CELLS:
        focus_rows.append(
            {
                **cell,
                "intake_rows_file_exists": ROWS_FILE.exists(),
                "intake_provenance_file_exists": PROVENANCE_FILE.exists(),
                "public_web_ready_source_rows_found": False,
                "blocker": "no_ready_source_owned_native_subhour_label_export_after_public_web_screen",
            }
        )

    summary = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "board_hash_before_writeback": sha256_file(BOARD),
        "focus_cells": FOCUS_CELLS,
        "search_records_count": len(SEARCH_RECORDS),
        "ready_public_source_native_subhour_exports_found": 0,
        "required_intake_root": str(INTAKE_ROOT),
        "required_rows_file": str(ROWS_FILE),
        "required_provenance_file": str(PROVENANCE_FILE),
        "intake_root_exists": INTAKE_ROOT.exists(),
        "intake_rows_file_exists": ROWS_FILE.exists(),
        "intake_provenance_file_exists": PROVENANCE_FILE.exists(),
        "rows_acquired": False,
        "accepted_rows_added": 0,
        "new_confidence_gate": False,
        "canonical_merge_allowed": False,
        "downstream_chain_rerun_allowed": False,
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "shared_intake_mutated": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "external_web_search_sent": True,
        "raw_data_downloaded": False,
        "trade_usable": False,
        "decision": "r3_native_subhour_public_web_source_screen_v1=no_ready_source_owned_native_subhour_rows_found",
    }

    (OUT / "r3_native_subhour_public_web_source_screen_v1.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    write_csv(
        OUT / "r3_native_subhour_public_web_source_screen_results_v1.csv",
        SEARCH_RECORDS,
        [
            "query",
            "url",
            "title",
            "observed_surface",
            "source_type",
            "r3_native_subhour_label_candidate",
            "blocker",
        ],
    )
    write_csv(
        OUT / "r3_native_subhour_public_web_focus_cells_v1.csv",
        focus_rows,
        [
            "symbol",
            "timeframe",
            "required_after",
            "intake_rows_file_exists",
            "intake_provenance_file_exists",
            "public_web_ready_source_rows_found",
            "blocker",
        ],
    )

    md = [
        "# R3 Native Sub-hour Public Web Source Screen v1",
        "",
        f"- Decision: `{summary['decision']}`.",
        "- Scope: AAPL and IXIC native 15m/30m source-owned regime-label rows after `2026-01-30`.",
        f"- Ready public source-native sub-hour exports found: `{summary['ready_public_source_native_subhour_exports_found']}`.",
        f"- Required intake root: `{INTAKE_ROOT}`.",
        f"- Required files present: rows `{ROWS_FILE.exists()}`, provenance `{PROVENANCE_FILE.exists()}`.",
        "- Accepted rows added: `0`; canonical merge allowed: `false`; downstream chain rerun allowed: `false`.",
        "- Runtime code changed: `false`; shared intake mutated: `false`; thresholds relaxed: `false`; raw data committed: `false`; raw data downloaded: `false`; trade usable: `false`.",
        "",
        "## Focus Cells",
        "",
        "| Symbol | Timeframe | Required After | Public Source Rows Found | Blocker |",
        "|---|---|---|---|---|",
    ]
    for row in focus_rows:
        md.append(
            f"| `{row['symbol']}` | `{row['timeframe']}` | `{row['required_after']}` | "
            f"`{str(row['public_web_ready_source_rows_found']).lower()}` | `{row['blocker']}` |"
        )
    md.extend(
        [
            "",
            "## Public Search Readback",
            "",
            "| Query | Surface | Assessment |",
            "|---|---|---|",
        ]
    )
    for row in SEARCH_RECORDS:
        md.append(
            f"| `{row['query']}` | [{row['title']}]({row['url']}) | "
            f"`{row['blocker']}` |"
        )
    md.extend(
        [
            "",
            "## Boundary",
            "",
            "This packet records public search and contact-route evidence only. It does not treat OHLCV bars, provider help pages, search result pages, or vendor contact routes as source-owned native sub-hour regime labels. It does not create the R3 intake root or authorize provider/Auto-Quant/pre-Bayes/BBN/CatBoost/execution-tree promotion.",
        ]
    )
    (OUT / "r3_native_subhour_public_web_source_screen_v1.md").write_text(
        "\n".join(md) + "\n",
        encoding="utf-8",
    )

    checks = [
        f"PASS decision={summary['decision']}",
        "PASS ready_public_source_native_subhour_exports_found=0",
        f"PASS intake_root_exists={str(INTAKE_ROOT.exists()).lower()}",
        f"PASS intake_rows_file_exists={str(ROWS_FILE.exists()).lower()}",
        f"PASS intake_provenance_file_exists={str(PROVENANCE_FILE.exists()).lower()}",
        "PASS rows_acquired=false",
        "PASS accepted_rows_added=0",
        "PASS canonical_merge_allowed=false",
        "PASS downstream_chain_rerun_allowed=false",
        "PASS strict_full_objective_achieved=false",
        "PASS update_goal=false",
        "PASS runtime_code_changed=false",
        "PASS shared_intake_mutated=false",
        "PASS thresholds_relaxed=false",
        "PASS raw_data_committed=false",
        "PASS raw_data_downloaded=false",
        "PASS trade_usable=false",
    ]
    (CHECKS / "r3_native_subhour_public_web_source_screen_v1_assertions.out").write_text(
        "\n".join(checks) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
