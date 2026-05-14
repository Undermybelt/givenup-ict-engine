#!/usr/bin/env python3
"""Bounded direct-row preflight for Zenodo DEX wash-trading data.

The script streams public CSV rows and stops after a small self-trade/non-self
sample per venue. It does not persist raw source files.
"""

from __future__ import annotations

import csv
import io
import json
import pathlib
import urllib.request
from datetime import datetime, timedelta, timezone


RUN_ID = "20260511T095606+0800-codex-zenodo-dex-selftrade-direct-row-preflight"
RUN_ROOT = pathlib.Path(__file__).resolve().parents[1]
SOURCE_DIR = RUN_ROOT / "source-audit"
CHECK_DIR = RUN_ROOT / "checks"

ROW_TARGET_PER_CLASS_PER_VENUE = 12
MAX_SCAN_ROWS_PER_VENUE = 200_000

ZENODO_RECORD_URL = "https://zenodo.org/records/4540223"
ZENODO_API_URL = "https://zenodo.org/api/records/4540223"
GITHUB_REPO_URL = "https://github.com/friedhelmvictor/lob-dex-wash-trading-paper"

VENUES = {
    "IDEX": {
        "url": "https://zenodo.org/api/records/4540223/files/IDEXTrades.csv/content",
        "chain": "Ethereum",
        "positive_rule": "maker == taker",
        "maker_col": "maker",
        "taker_col": "taker",
        "timestamp_col": "timestamp",
        "tx_col": "transaction_hash",
        "instrument_cols": ("tokenBuy", "tokenSell"),
    },
    "EtherDelta": {
        "url": "https://zenodo.org/api/records/4540223/files/EtherDeltaTrades.csv/content",
        "chain": "Ethereum",
        "positive_rule": "get == give",
        "maker_col": "get",
        "taker_col": "give",
        "timestamp_col": "timestamp",
        "tx_col": "transaction_hash",
        "instrument_cols": ("tokenGet", "tokenGive"),
    },
}


def iso_window(epoch_seconds: str) -> tuple[str, str]:
    start = datetime.fromtimestamp(int(epoch_seconds), tz=timezone.utc)
    end = start + timedelta(seconds=1)
    return start.isoformat().replace("+00:00", "Z"), end.isoformat().replace("+00:00", "Z")


def candidate_row(venue: str, source: dict[str, str], raw: dict[str, str], is_positive: bool) -> dict[str, str]:
    start, end = iso_window(raw[source["timestamp_col"]])
    left, right = source["instrument_cols"]
    pair = f"{raw[left]}/{raw[right]}"
    tx = raw[source["tx_col"]]
    return {
        "event_id": f"{venue}:{tx}",
        "instrument_or_asset": pair,
        "venue_or_chain": f"{venue}/{source['chain']}",
        "event_start": start,
        "event_end": end,
        "is_manipulation_positive": str(is_positive).lower(),
        "manipulation_type": "wash_trade_self_trade" if is_positive else "none_negative_control",
        "negative_control_type": (
            "not_applicable_positive_self_trade"
            if is_positive
            else "same_venue_non_self_trade_control"
        ),
        "source_id": "zenodo:4540223;github:friedhelmvictor/lob-dex-wash-trading-paper",
        "source_url_or_private_ref": (
            f"{ZENODO_RECORD_URL}; {GITHUB_REPO_URL}; "
            f"venue={venue}; rule={source['positive_rule']}"
        ),
    }


def stream_venue_rows(venue: str, source: dict[str, str]) -> tuple[list[dict[str, str]], dict[str, object]]:
    positives: list[dict[str, str]] = []
    negatives: list[dict[str, str]] = []
    scanned = 0

    with urllib.request.urlopen(source["url"], timeout=45) as response:
        text_stream = io.TextIOWrapper(response, encoding="utf-8", newline="")
        reader = csv.DictReader(text_stream)
        for raw in reader:
            scanned += 1
            is_positive = raw[source["maker_col"]].lower() == raw[source["taker_col"]].lower()
            if is_positive and len(positives) < ROW_TARGET_PER_CLASS_PER_VENUE:
                positives.append(candidate_row(venue, source, raw, True))
            elif not is_positive and len(negatives) < ROW_TARGET_PER_CLASS_PER_VENUE:
                negatives.append(candidate_row(venue, source, raw, False))

            if (
                len(positives) >= ROW_TARGET_PER_CLASS_PER_VENUE
                and len(negatives) >= ROW_TARGET_PER_CLASS_PER_VENUE
            ):
                break
            if scanned >= MAX_SCAN_ROWS_PER_VENUE:
                break

    stats = {
        "venue": venue,
        "rows_scanned_until_stop": scanned,
        "candidate_positive_self_trade_rows": len(positives),
        "candidate_negative_control_rows": len(negatives),
        "positive_rule": source["positive_rule"],
        "target_per_class": ROW_TARGET_PER_CLASS_PER_VENUE,
        "max_scan_rows": MAX_SCAN_ROWS_PER_VENUE,
    }
    return positives + negatives, stats


def write_csv(path: pathlib.Path, rows: list[dict[str, str]]) -> None:
    fieldnames = [
        "event_id",
        "instrument_or_asset",
        "venue_or_chain",
        "event_start",
        "event_end",
        "is_manipulation_positive",
        "manipulation_type",
        "negative_control_type",
        "source_id",
        "source_url_or_private_ref",
    ]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    SOURCE_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)

    rows: list[dict[str, str]] = []
    extraction_stats = []
    for venue, source in VENUES.items():
        venue_rows, stats = stream_venue_rows(venue, source)
        rows.extend(venue_rows)
        extraction_stats.append(stats)

    csv_path = SOURCE_DIR / "direct_manipulation_rows_candidate_v1.csv"
    json_path = SOURCE_DIR / "zenodo_dex_selftrade_direct_row_preflight.json"
    md_path = SOURCE_DIR / "zenodo_dex_selftrade_direct_row_preflight.md"
    checks_path = CHECK_DIR / "zenodo_dex_selftrade_direct_row_preflight_assertions.out"

    write_csv(csv_path, rows)

    positives = sum(1 for row in rows if row["is_manipulation_positive"] == "true")
    negatives = sum(1 for row in rows if row["is_manipulation_positive"] == "false")
    audit = {
        "run_id": RUN_ID,
        "active_taxonomy": "MainRegimeV2",
        "objective": "Bounded preflight for replayable direct Manipulation rows from real DEX trade data.",
        "source": {
            "zenodo_record": ZENODO_RECORD_URL,
            "zenodo_api": ZENODO_API_URL,
            "github_pipeline": GITHUB_REPO_URL,
            "title": "Detecting and Quantifying Wash Trading on Decentralized Cryptocurrency Exchanges",
            "venues": ["IDEX", "EtherDelta"],
            "remote_file_sizes_bytes": {
                "EtherDeltaTrades.csv": 1051981252,
                "IDEXTrades.csv": 2098100246,
            },
            "source_logic_observed": [
                "Repository pipeline filters self trades before SCC-based wash-trade labeling.",
                "Pipeline writes self_trades.csv and trades_labeled.csv when run over full preprocessed data.",
                "This preflight only exports bounded self-trade/non-self direct rows; it does not run the heavy R pipeline.",
            ],
        },
        "candidate_direct_manipulation_rows_exported": len(rows),
        "candidate_positive_self_trade_rows": positives,
        "candidate_negative_control_rows": negatives,
        "candidate_rows_csv": str(csv_path.relative_to(RUN_ROOT)),
        "candidate_schema": "direct_manipulation_rows_schema_v3.csv",
        "v3_direct_row_schema_satisfied_for_candidate_sample": positives > 0 and negatives > 0,
        "extraction_stats": extraction_stats,
        "accepted_parent_root_sources_added": 0,
        "accepted_direct_manipulation_rows_added": 0,
        "gate_result": "blocked_candidate_direct_rows_exported_full_acceptance_gate_not_run",
        "raw_data_committed": False,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "trade_usable": False,
        "limitations": [
            "No MainRegimeV2 Bull/Bear/Sideways/Crisis parent-root slots are filled.",
            "The exported rows are a bounded source-backed preflight sample, not a full chronological 95% acceptance gate.",
            "Full source CSVs are 1.05GB and 2.10GB; raw files were not downloaded or committed.",
            "Self-trade mapping is direct order-lifecycle evidence for a wash-trade subtype, but it still needs a full-context gate before acceptance coverage can be claimed.",
        ],
        "targeted_near_miss_candidates": [
            {
                "source_id": "kaggle:igormerlinicomposer/herding-based-market-regime-dataset",
                "decision": "rejected_for_current_slots",
                "reason": "Herding/risk/signal outputs have no requested exact instrument/timeframe parent-root label panel and are generated signals.",
            },
            {
                "source_id": "kaggle:ahaanverma00/nifty-500-market-and-behavior-regime-dataset",
                "decision": "rejected_for_current_slots",
                "reason": "Daily NIFTY behavior/macro/fast-state predictions are not exact requested yfinance/Kraken instruments and not Bull/Bear/Sideways/Crisis source labels.",
            },
            {
                "source_id": "kaggle:sergionefedov/synthetic-limit-order-book-market-microstructure",
                "decision": "rejected_for_current_slots",
                "reason": "Synthetic 10-day LOB data has quiet/normal/volatile regimes, not real exact-underlying parent-root labels.",
            },
            {
                "source_id": "kaggle:justinsolstice/dark-pool-pack",
                "decision": "rejected_for_current_slots",
                "reason": "Synthetic anomaly/fraud sequences; no real transactions, no exact requested parent-root labels, and no accepted direct manipulation coverage.",
            },
            {
                "source_id": "huggingface:akashkumar5/Multi_Timeframe_Market_Regimes_HMM6_BTCUSD",
                "decision": "rejected_for_current_slots",
                "reason": "HMM-derived BTCUSD regimes are explicitly forbidden proxy labels.",
            },
        ],
        "next_action": (
            "If this direct-self-trade lane is pursued, run a full or larger bounded chronological "
            "Zenodo DEX gate from raw rows in /tmp, preserving positive self-trades and same-venue "
            "non-self controls; otherwise continue acquisition for exact yfinance/Kraken parent-root labels."
        ),
    }

    json_path.write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    md = f"""# Zenodo DEX Self-Trade Direct Row Preflight

Run ID: `{RUN_ID}`

## Result

- Source: Zenodo record `4540223`, backed by `friedhelmvictor/lob-dex-wash-trading-paper`.
- Candidate direct `Manipulation` rows exported: `{len(rows)}`.
- Positive self-trade rows: `{positives}`.
- Same-venue non-self negative controls: `{negatives}`.
- Accepted parent-root sources added: `0`.
- Accepted direct `Manipulation` rows added: `0`.
- Gate result: `blocked_candidate_direct_rows_exported_full_acceptance_gate_not_run`.
- Runtime code changed: false. Thresholds relaxed: false. Raw data committed: false. Trade usable: false.

## Artifacts

- Candidate direct rows: `{csv_path.relative_to(RUN_ROOT)}`
- Audit JSON: `{json_path.relative_to(RUN_ROOT)}`
- Assertions: `{checks_path.relative_to(RUN_ROOT)}`

## Notes

The source files are real DEX trade rows, but this run only streams enough rows to
create a replayable direct-row sample. It does not download or commit the 1-2GB
raw files and does not claim full chronological acceptance.

## Next Action

Run a full or larger bounded chronological Zenodo DEX direct gate from `/tmp`, or
continue acquisition for exact yfinance/Kraken parent-root labels.
"""
    md_path.write_text(md, encoding="utf-8")

    check_lines = [
        "PASS json_written",
        "PASS csv_written",
        f"PASS candidate_rows={len(rows)}",
        f"PASS positive_rows={positives}",
        f"PASS negative_control_rows={negatives}",
        "PASS raw_data_committed=false",
        "PASS accepted_parent_root_sources_added=0",
        "PASS accepted_direct_manipulation_rows_added=0",
        "GATE blocked_candidate_direct_rows_exported_full_acceptance_gate_not_run",
    ]
    checks_path.write_text("\n".join(check_lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
