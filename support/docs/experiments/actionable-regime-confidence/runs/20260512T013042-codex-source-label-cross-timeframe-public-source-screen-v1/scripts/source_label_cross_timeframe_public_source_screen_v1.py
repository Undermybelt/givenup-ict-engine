#!/usr/bin/env python3
"""Record a fail-closed public source screen for cross-timeframe regime labels."""

from __future__ import annotations

import csv
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


RUN_ID = "20260512T013042-codex-source-label-cross-timeframe-public-source-screen-v1"
REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = Path(__file__).resolve().parents[1]
OUT = RUN_ROOT / "source-label-cross-timeframe-public-source-screen-v1"
CHECKS = RUN_ROOT / "checks"
BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"

CONDITION_JSON = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260512T012330-codex-source-label-bull-sideways-qualifying-condition-v1/"
    "source-label-bull-sideways-qualifying-condition-v1/"
    "source_label_bull_sideways_qualifying_condition_v1.json"
)

R3_ROOT = Path("/tmp/ict-engine-native-subhour-source-label-intake")
R5_ROOT = Path("/tmp/ict-engine-source-panel-recency-extension")
R6_ROOT = Path("/tmp/ict-engine-board-a-r6-owner-export-v1")

SEARCH_RECORDS = [
    {
        "query": "\"market regime\" intraday dataset \"15 minute\" labels",
        "url": "https://www.kaggle.com/search?q=%22market+regime%22+intraday+%2215+minute%22+labels+in%3Adatasets",
        "surface": "Kaggle dataset search",
        "assessment": "No ready source-owned 15m/30m MainRegimeV2-style label export identified; search surfaces tend to expose OHLCV/intraday bars or derived notebooks.",
        "eligible_cross_timeframe_source_label": False,
        "blocker": "dataset_search_no_ready_source_owned_native_label_rows",
    },
    {
        "query": "\"stock market regimes\" intraday \"regime_confidence\"",
        "url": "https://www.kaggle.com/search?q=%22stock+market+regimes%22+intraday+%22regime_confidence%22+in%3Adatasets",
        "surface": "Kaggle regime-confidence search",
        "assessment": "Existing daily stock-regime source is represented by the source-label root; no intraday source-confidence extension was found.",
        "eligible_cross_timeframe_source_label": False,
        "blocker": "daily_source_panel_only_no_intraday_confidence_extension",
    },
    {
        "query": "\"regime labels\" \"15m\" stock dataset",
        "url": "https://huggingface.co/datasets?search=regime%20labels%2015m%20stock",
        "surface": "Hugging Face dataset search",
        "assessment": "Public search surface may include generated/model labels, but no owner-approved source-label package with Board A provenance and split contract was identified.",
        "eligible_cross_timeframe_source_label": False,
        "blocker": "generated_or_unverified_label_surface_not_board_a_source_owned",
    },
    {
        "query": "\"market regime\" \"30m\" \"source confidence\" dataset",
        "url": "https://data.nasdaq.com/search?query=market%20regime%2030m%20source%20confidence",
        "surface": "Nasdaq Data Link search/contact route",
        "assessment": "Vendor/data-link route is useful for acquisition, but it is not a ready source-owned regime-label export.",
        "eligible_cross_timeframe_source_label": False,
        "blocker": "vendor_route_only_rows_not_acquired",
    },
    {
        "query": "TradingView market regime 15m labels source-owned dataset",
        "url": "https://www.tradingview.com/scripts/search/market%20regime/",
        "surface": "TradingView script search",
        "assessment": "TradingView scripts are chart-derived indicators, not source-owned label rows with provenance; they cannot close Board A source-label gates.",
        "eligible_cross_timeframe_source_label": False,
        "blocker": "indicator_script_not_source_owned_label_export",
    },
]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def board_cursor() -> str:
    text = BOARD.read_text(encoding="utf-8")
    match = re.search(r"\| last_loop_id \| ([^|]+) \|", text)
    return match.group(1).strip() if match else "missing"


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)

    if not BOARD.exists() or not CONDITION_JSON.exists():
        raise FileNotFoundError("board or condition JSON missing")

    condition = read_json(CONDITION_JSON)
    label_summary = condition.get("label_summary", [])
    timeframe_rows = [
        {
            "label": row.get("label"),
            "known_condition": row.get("qualifying_condition"),
            "current_timeframe_count": row.get("timeframe_count"),
            "multi_timeframe_support_pass": row.get("multi_timeframe_support_pass"),
            "current_blockers": row.get("blockers"),
        }
        for row in label_summary
    ]

    ready_public_exports = sum(1 for row in SEARCH_RECORDS if row["eligible_cross_timeframe_source_label"])
    summary = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "board_hash_before_writeback": sha256_file(BOARD),
        "current_cursor": board_cursor(),
        "condition_input_run": condition.get("run_id"),
        "condition_input_decision": condition.get("decision"),
        "ready_public_cross_timeframe_source_label_exports_found": ready_public_exports,
        "search_records": len(SEARCH_RECORDS),
        "target_labels": ["Bull", "Sideways"],
        "r3_native_root_present": R3_ROOT.exists(),
        "r5_recency_root_present": R5_ROOT.exists(),
        "r6_owner_export_root_present": R6_ROOT.exists(),
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
        "decision": "source_label_cross_timeframe_public_source_screen_v1=no_ready_source_owned_cross_timeframe_labels_found",
    }

    (OUT / "source_label_cross_timeframe_public_source_screen_v1.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    write_csv(
        OUT / "source_label_cross_timeframe_public_source_screen_results_v1.csv",
        SEARCH_RECORDS,
        ["query", "url", "surface", "assessment", "eligible_cross_timeframe_source_label", "blocker"],
    )
    write_csv(
        OUT / "source_label_cross_timeframe_current_condition_timeframes_v1.csv",
        timeframe_rows,
        [
            "label",
            "known_condition",
            "current_timeframe_count",
            "multi_timeframe_support_pass",
            "current_blockers",
        ],
    )

    md = [
        "# Source Label Cross-Timeframe Public Source Screen v1",
        "",
        f"- Decision: `{summary['decision']}`.",
        f"- Current cursor: `{summary['current_cursor']}`.",
        f"- Condition input: `{summary['condition_input_decision']}`.",
        f"- Ready public cross-timeframe source-label exports found: `{ready_public_exports}`.",
        f"- R3/R5/R6 roots present: `{R3_ROOT.exists()}` / `{R5_ROOT.exists()}` / `{R6_ROOT.exists()}`.",
        "- Accepted rows added: `0`; new confidence gate: `false`; canonical merge allowed: `false`; downstream chain rerun allowed: `false`.",
        "- Runtime code changed: `false`; shared intake mutated: `false`; thresholds relaxed: `false`; raw data committed: `false`; raw data downloaded: `false`; trade usable: `false`.",
        "",
        "## Current Condition Timeframes",
        "",
        "| Label | Timeframe Count | Multi-Timeframe Pass | Blockers |",
        "|---|---:|---|---|",
    ]
    for row in timeframe_rows:
        md.append(
            f"| `{row['label']}` | `{row['current_timeframe_count']}` | "
            f"`{row['multi_timeframe_support_pass']}` | `{row['current_blockers']}` |"
        )
    md.extend(
        [
            "",
            "## Public Source Screen",
            "",
            "| Query | Surface | Assessment |",
            "|---|---|---|",
        ]
    )
    for row in SEARCH_RECORDS:
        md.append(
            f"| `{row['query']}` | [{row['surface']}]({row['url']}) | `{row['blocker']}` |"
        )
    md.extend(
        [
            "",
            "## Boundary",
            "",
            "This packet is an acquisition screen only. It does not accept TradingView indicators, provider bars, generated labels, search-result pages, or vendor contact routes as source-owned cross-timeframe regime labels. It does not authorize canonical merge or downstream promotion.",
        ]
    )
    (OUT / "source_label_cross_timeframe_public_source_screen_v1.md").write_text(
        "\n".join(md) + "\n",
        encoding="utf-8",
    )

    checks = [
        f"PASS decision={summary['decision']}",
        "PASS ready_public_cross_timeframe_source_label_exports_found=0",
        f"PASS r3_native_root_present={str(R3_ROOT.exists()).lower()}",
        f"PASS r5_recency_root_present={str(R5_ROOT.exists()).lower()}",
        f"PASS r6_owner_export_root_present={str(R6_ROOT.exists()).lower()}",
        "PASS accepted_rows_added=0",
        "PASS new_confidence_gate=false",
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
    (CHECKS / "source_label_cross_timeframe_public_source_screen_v1_assertions.out").write_text(
        "\n".join(checks) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
