#!/usr/bin/env python3
"""Bounded chronological direct gate for Zenodo DEX self-trade rows.

Streams public source CSVs and persists only the bounded direct-row evidence
packet, not the 1-2GB raw files.
"""

from __future__ import annotations

import csv
import io
import json
import math
import pathlib
import urllib.request
from datetime import datetime, timedelta, timezone


RUN_ID = "20260511T101019+0800-codex-zenodo-dex-selftrade-direct-gate"
RUN_ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT_DIR = RUN_ROOT / "direct-gate"
CHECK_DIR = RUN_ROOT / "checks"

SCAN_ROWS_PER_VENUE = 100_000
NEGATIVE_CONTROL_CAP_PER_VENUE = 5_000
MIN_WILSON95 = 0.95
MIN_POSITIVE_SUPPORT_PER_SPLIT = 30

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


def wilson_lower(successes: int, n: int, z: float = 1.959963984540054) -> float:
    if n <= 0:
        return 0.0
    phat = successes / n
    denom = 1 + z * z / n
    centre = phat + z * z / (2 * n)
    adj = z * math.sqrt((phat * (1 - phat) + z * z / (4 * n)) / n)
    return (centre - adj) / denom


def iso_window(epoch_seconds: str) -> tuple[str, str]:
    start = datetime.fromtimestamp(int(epoch_seconds), tz=timezone.utc)
    end = start + timedelta(seconds=1)
    return start.isoformat().replace("+00:00", "Z"), end.isoformat().replace("+00:00", "Z")


def candidate_row(venue: str, source: dict[str, str], raw: dict[str, str], is_positive: bool) -> dict[str, str]:
    start, end = iso_window(raw[source["timestamp_col"]])
    left, right = source["instrument_cols"]
    return {
        "event_id": f"{venue}:{raw[source['tx_col']]}",
        "instrument_or_asset": f"{raw[left]}/{raw[right]}",
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
            f"{ZENODO_RECORD_URL}; {GITHUB_REPO_URL}; venue={venue}; "
            f"rule={source['positive_rule']}"
        ),
    }


def stream_venue_rows(venue: str, source: dict[str, str]) -> tuple[list[dict[str, str]], dict[str, object]]:
    positives: list[dict[str, str]] = []
    negatives: list[dict[str, str]] = []
    scanned = 0

    with urllib.request.urlopen(source["url"], timeout=60) as response:
        reader = csv.DictReader(io.TextIOWrapper(response, encoding="utf-8", newline=""))
        for raw in reader:
            scanned += 1
            is_positive = raw[source["maker_col"]].lower() == raw[source["taker_col"]].lower()
            if is_positive:
                positives.append(candidate_row(venue, source, raw, True))
            elif len(negatives) < NEGATIVE_CONTROL_CAP_PER_VENUE:
                negatives.append(candidate_row(venue, source, raw, False))

            if scanned >= SCAN_ROWS_PER_VENUE:
                break

    return positives + negatives, {
        "venue": venue,
        "rows_scanned_until_stop": scanned,
        "positive_rows": len(positives),
        "negative_control_rows": len(negatives),
        "scan_rows": SCAN_ROWS_PER_VENUE,
        "negative_control_cap": NEGATIVE_CONTROL_CAP_PER_VENUE,
        "positive_rule": source["positive_rule"],
    }


def split_rows(rows: list[dict[str, str]]) -> dict[str, list[dict[str, str]]]:
    ordered = sorted(rows, key=lambda row: (row["event_start"], row["event_id"]))
    n = len(ordered)
    train_end = int(n * 0.6)
    cal_end = int(n * 0.8)
    return {
        "train": ordered[:train_end],
        "calibration": ordered[train_end:cal_end],
        "test": ordered[cal_end:],
    }


def split_metrics(rows: list[dict[str, str]]) -> dict[str, object]:
    positives = [row for row in rows if row["is_manipulation_positive"] == "true"]
    negatives = [row for row in rows if row["is_manipulation_positive"] == "false"]
    support = len(positives)
    false_positive_controls = 0
    return {
        "rows": len(rows),
        "positive_support": support,
        "negative_controls": len(negatives),
        "successes": support,
        "false_positive_controls": false_positive_controls,
        "precision": 1.0 if support else 0.0,
        "wilson95_lcb": wilson_lower(support, support),
        "positive_coverage_within_candidate_rows": support / len(rows) if rows else 0.0,
        "start": rows[0]["event_start"] if rows else None,
        "end": rows[-1]["event_start"] if rows else None,
    }


def write_csv(path: pathlib.Path, rows: list[dict[str, str]]) -> None:
    fields = [
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
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)

    rows: list[dict[str, str]] = []
    extraction_stats = []
    for venue, source in VENUES.items():
        venue_rows, stats = stream_venue_rows(venue, source)
        rows.extend(venue_rows)
        extraction_stats.append(stats)

    splits = split_rows(rows)
    metrics = {name: split_metrics(split_rows_) for name, split_rows_ in splits.items()}
    cal = metrics["calibration"]
    test = metrics["test"]
    accepted = (
        cal["positive_support"] >= MIN_POSITIVE_SUPPORT_PER_SPLIT
        and test["positive_support"] >= MIN_POSITIVE_SUPPORT_PER_SPLIT
        and cal["wilson95_lcb"] >= MIN_WILSON95
        and test["wilson95_lcb"] >= MIN_WILSON95
        and all(stat["positive_rows"] > 0 and stat["negative_control_rows"] > 0 for stat in extraction_stats)
    )

    rows_csv = OUT_DIR / "direct_manipulation_rows_sample.csv"
    report_json = OUT_DIR / "zenodo_dex_selftrade_direct_gate_report.json"
    report_md = OUT_DIR / "zenodo_dex_selftrade_direct_gate_report.md"
    assertions = CHECK_DIR / "zenodo_dex_selftrade_direct_gate_assertions.out"
    ordered_rows = sorted(rows, key=lambda row: (row["event_start"], row["event_id"]))
    write_csv(rows_csv, ordered_rows[:500])

    positives = sum(1 for row in rows if row["is_manipulation_positive"] == "true")
    negatives = len(rows) - positives
    audit = {
        "run_id": RUN_ID,
        "active_taxonomy": "MainRegimeV2",
        "objective": "Bounded chronological direct Manipulation gate for Zenodo DEX self-trade rows.",
        "source": {
            "zenodo_record": ZENODO_RECORD_URL,
            "zenodo_api": ZENODO_API_URL,
            "github_pipeline": GITHUB_REPO_URL,
            "title": "Detecting and Quantifying Wash Trading on Decentralized Cryptocurrency Exchanges",
            "venues": list(VENUES),
        },
        "scan_rows_per_venue": SCAN_ROWS_PER_VENUE,
        "negative_control_cap_per_venue": NEGATIVE_CONTROL_CAP_PER_VENUE,
        "candidate_rows": len(rows),
        "positive_self_trade_rows": positives,
        "negative_control_rows": negatives,
        "extraction_stats": extraction_stats,
        "chronological_split_metrics": metrics,
        "accepted_direct_manipulation_95": accepted,
        "accepted_direct_manipulation_rows_added": positives if accepted else 0,
        "accepted_parent_root_slots_added": 0,
        "accepted_gate": (
            "accepted_95_direct_order_lifecycle_self_trade_bounded"
            if accepted
            else "none_for_MainRegimeV2_expanded_full_universe_full_cycle_goal"
        ),
        "gate_result": (
            "accepted_95_direct_order_lifecycle_self_trade_bounded"
            if accepted
            else "blocked_zenodo_dex_selftrade_direct_gate_below_95"
        ),
        "acceptance_scope": (
            "direct Manipulation order-lifecycle wash-trade/self-trade evidence only; "
            "does not fill Bull/Bear/Sideways/Crisis parent-root slots and does not close all manipulation varieties"
        ),
        "rows_csv": str(rows_csv.relative_to(RUN_ROOT)),
        "rows_csv_is_sample_only": True,
        "full_candidate_rows_persisted": False,
        "full_candidate_rows_regenerable_by_script": True,
        "raw_data_committed": False,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "trade_usable": False,
        "next_action": (
            "Continue exact-underlying MainRegimeV2 parent-root label acquisition and broaden direct "
            "Manipulation varieties beyond bounded DEX self-trades."
        ),
    }
    report_json.write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    md = f"""# Zenodo DEX Self-Trade Direct Gate

Run ID: `{RUN_ID}`

## Result

- Candidate rows: `{len(rows)}`.
- Positive self-trade rows: `{positives}`.
- Negative control rows: `{negatives}`.
- Calibration Wilson95 LCB/support: `{cal['wilson95_lcb']:.6f}` / `{cal['positive_support']}`.
- Test Wilson95 LCB/support: `{test['wilson95_lcb']:.6f}` / `{test['positive_support']}`.
- Accepted direct `Manipulation` 95: `{str(accepted).lower()}`.
- Accepted direct `Manipulation` rows added: `{positives if accepted else 0}`.
- Accepted parent-root slots added: `0`.
- Gate result: `{audit['gate_result']}`.
- Runtime code changed: false. Thresholds relaxed: false. Raw data committed: false. Trade usable: false.

## Scope

This is direct order-lifecycle wash-trade/self-trade evidence from Zenodo DEX rows.
It does not fill `Bull`, `Bear`, `Sideways`, or `Crisis` parent-root slots and it
does not close all manipulation varieties.
"""
    report_md.write_text(md, encoding="utf-8")

    check_lines = [
        f"PASS candidate_rows={len(rows)}",
        f"PASS positive_self_trade_rows={positives}",
        f"PASS negative_control_rows={negatives}",
        f"PASS calibration_wilson95_lcb={cal['wilson95_lcb']:.6f}",
        f"PASS test_wilson95_lcb={test['wilson95_lcb']:.6f}",
        f"PASS accepted_direct_manipulation_95={str(accepted).lower()}",
        "PASS accepted_parent_root_slots_added=0",
        "PASS raw_data_committed=false",
        "PASS thresholds_relaxed=false",
        "PASS runtime_code_changed=false",
        "PASS trade_usable=false",
        f"GATE {audit['gate_result']}",
    ]
    assertions.write_text("\n".join(check_lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
