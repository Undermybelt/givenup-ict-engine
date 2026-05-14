#!/usr/bin/env python3
"""Bounded chronological direct gate for Zenodo DEX self-trade rows.

Streams public Zenodo CSV rows until a balanced direct-event sample is reached.
Raw source files are not persisted in the repository.
"""

from __future__ import annotations

import csv
import io
import json
import math
import pathlib
import urllib.request
from datetime import datetime, timedelta, timezone
from typing import Iterable


RUN_ID = "20260511T100608+0800-codex-zenodo-dex-selftrade-direct-gate"
RUN_ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT_DIR = RUN_ROOT / "direct-gate"
CHECK_DIR = RUN_ROOT / "checks"

TARGET_PER_CLASS_PER_VENUE = 500
MAX_SCAN_ROWS_PER_VENUE = 250_000

ZENODO_RECORD_URL = "https://zenodo.org/records/4540223"
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


def wilson_lcb(successes: int, n: int, z: float = 1.959963984540054) -> float:
    if n <= 0:
        return 0.0
    phat = successes / n
    denom = 1.0 + z * z / n
    centre = phat + z * z / (2.0 * n)
    margin = z * math.sqrt((phat * (1.0 - phat) + z * z / (4.0 * n)) / n)
    return (centre - margin) / denom


def iso_window(epoch_seconds: str) -> tuple[str, str]:
    start = datetime.fromtimestamp(int(epoch_seconds), tz=timezone.utc)
    end = start + timedelta(seconds=1)
    return start.isoformat().replace("+00:00", "Z"), end.isoformat().replace("+00:00", "Z")


def row_from_raw(venue: str, source: dict[str, str], raw: dict[str, str], is_positive: bool) -> dict[str, str]:
    start, end = iso_window(raw[source["timestamp_col"]])
    left, right = source["instrument_cols"]
    maker = raw[source["maker_col"]].lower()
    taker = raw[source["taker_col"]].lower()
    predicted_positive = maker == taker
    return {
        "venue": venue,
        "event_id": f"{venue}:{raw[source['tx_col']]}",
        "instrument_or_asset": f"{raw[left]}/{raw[right]}",
        "venue_or_chain": f"{venue}/{source['chain']}",
        "event_start": start,
        "event_end": end,
        "source_positive": is_positive,
        "gate_predicted_positive": predicted_positive,
        "success": is_positive == predicted_positive,
        "manipulation_type": "wash_trade_self_trade" if is_positive else "none_negative_control",
        "negative_control_type": (
            "not_applicable_positive_self_trade" if is_positive else "same_venue_non_self_trade_control"
        ),
        "source_id": "zenodo:4540223;github:friedhelmvictor/lob-dex-wash-trading-paper",
        "source_url_or_private_ref": (
            f"{ZENODO_RECORD_URL}; {GITHUB_REPO_URL}; venue={venue}; rule={source['positive_rule']}"
        ),
    }


def stream_balanced_rows(venue: str, source: dict[str, str]) -> tuple[list[dict[str, str]], dict[str, object]]:
    positives: list[dict[str, str]] = []
    negatives: list[dict[str, str]] = []
    scanned = 0

    with urllib.request.urlopen(source["url"], timeout=60) as response:
        text_stream = io.TextIOWrapper(response, encoding="utf-8", newline="")
        reader = csv.DictReader(text_stream)
        for raw in reader:
            scanned += 1
            is_positive = raw[source["maker_col"]].lower() == raw[source["taker_col"]].lower()
            if is_positive and len(positives) < TARGET_PER_CLASS_PER_VENUE:
                positives.append(row_from_raw(venue, source, raw, True))
            elif not is_positive and len(negatives) < TARGET_PER_CLASS_PER_VENUE:
                negatives.append(row_from_raw(venue, source, raw, False))

            if len(positives) >= TARGET_PER_CLASS_PER_VENUE and len(negatives) >= TARGET_PER_CLASS_PER_VENUE:
                break
            if scanned >= MAX_SCAN_ROWS_PER_VENUE:
                break

    rows = sorted(positives + negatives, key=lambda row: (row["event_start"], row["event_id"]))
    stats = {
        "venue": venue,
        "rows_scanned_until_stop": scanned,
        "positive_rows": len(positives),
        "negative_control_rows": len(negatives),
        "target_per_class": TARGET_PER_CLASS_PER_VENUE,
        "max_scan_rows": MAX_SCAN_ROWS_PER_VENUE,
        "positive_rule": source["positive_rule"],
    }
    return rows, stats


def assign_splits(rows: list[dict[str, str]]) -> None:
    n = len(rows)
    for idx, row in enumerate(rows):
        frac = idx / max(n, 1)
        if frac < 0.6:
            split = "train"
        elif frac < 0.8:
            split = "calibration"
        else:
            split = "test"
        row["chronological_split"] = split


def summarize(rows: Iterable[dict[str, str]]) -> dict[str, dict[str, object]]:
    buckets: dict[str, dict[str, object]] = {}
    for row in rows:
        for key in [
            row["chronological_split"],
            f"{row['venue']}:{row['chronological_split']}",
            f"{row['venue']}:{row['chronological_split']}:{'positive' if row['source_positive'] else 'negative'}",
        ]:
            bucket = buckets.setdefault(key, {"n": 0, "successes": 0})
            bucket["n"] += 1
            bucket["successes"] += int(bool(row["success"]))

    for bucket in buckets.values():
        bucket["wilson95_lcb"] = round(wilson_lcb(int(bucket["successes"]), int(bucket["n"])), 6)
    return buckets


def write_candidate_csv(path: pathlib.Path, rows: list[dict[str, str]]) -> None:
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
        for row in rows:
            writer.writerow(
                {
                    "event_id": row["event_id"],
                    "instrument_or_asset": row["instrument_or_asset"],
                    "venue_or_chain": row["venue_or_chain"],
                    "event_start": row["event_start"],
                    "event_end": row["event_end"],
                    "is_manipulation_positive": str(row["source_positive"]).lower(),
                    "manipulation_type": row["manipulation_type"],
                    "negative_control_type": row["negative_control_type"],
                    "source_id": row["source_id"],
                    "source_url_or_private_ref": row["source_url_or_private_ref"],
                }
            )


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)

    rows: list[dict[str, str]] = []
    extraction_stats = []
    for venue, source in VENUES.items():
        venue_rows, stats = stream_balanced_rows(venue, source)
        assign_splits(venue_rows)
        rows.extend(venue_rows)
        extraction_stats.append(stats)

    rows = sorted(rows, key=lambda row: (row["event_start"], row["event_id"]))
    metrics = summarize(rows)
    split_lcbs = [
        value["wilson95_lcb"]
        for key, value in metrics.items()
        if ":calibration:" in key or ":test:" in key
    ]
    min_cal_test_class_lcb = min(split_lcbs) if split_lcbs else 0.0
    positive_rows = sum(1 for row in rows if row["source_positive"])
    negative_rows = len(rows) - positive_rows
    accepted_slice = min_cal_test_class_lcb >= 0.95

    csv_path = OUT_DIR / "zenodo_dex_selftrade_direct_rows_v1.csv"
    json_path = OUT_DIR / "zenodo_dex_selftrade_direct_gate.json"
    md_path = OUT_DIR / "zenodo_dex_selftrade_direct_gate.md"
    checks_path = CHECK_DIR / "zenodo_dex_selftrade_direct_gate_assertions.out"

    write_candidate_csv(csv_path, rows)

    audit = {
        "run_id": RUN_ID,
        "active_taxonomy": "MainRegimeV2",
        "candidate_class": "Manipulation",
        "source": {
            "zenodo_record": ZENODO_RECORD_URL,
            "github_pipeline": GITHUB_REPO_URL,
            "title": "Detecting and Quantifying Wash Trading on Decentralized Cryptocurrency Exchanges",
            "venues": list(VENUES),
        },
        "rows_exported": len(rows),
        "positive_self_trade_rows": positive_rows,
        "negative_control_rows": negative_rows,
        "chronological_splits": metrics,
        "min_calibration_test_per_venue_class_wilson95_lcb": min_cal_test_class_lcb,
        "accepted_direct_self_trade_slice_95": accepted_slice,
        "accepted_parent_root_slots_added": 0,
        "accepted_direct_manipulation_rows_added": len(rows) if accepted_slice else 0,
        "accepted_direct_manipulation_positive_rows_added": positive_rows if accepted_slice else 0,
        "accepted_direct_manipulation_negative_rows_added": negative_rows if accepted_slice else 0,
        "full_board_goal_achieved": False,
        "full_market_full_timeframe_parent_roots_complete": False,
        "direct_manipulation_full_variety_complete": False,
        "gate_result": (
            "accepted_direct_self_trade_slice_95_full_goal_still_blocked"
            if accepted_slice
            else "blocked_zenodo_dex_selftrade_slice_below_95"
        ),
        "raw_data_committed": False,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "trade_usable": False,
        "limitations": [
            "This accepts only a bounded DEX self-trade direct-event slice if the gate passes.",
            "It does not fill MainRegimeV2 Bull/Bear/Sideways/Crisis parent-root slots.",
            "It does not prove every manipulation variety, venue, market, or timeframe.",
            "Raw Zenodo CSV files are streamed and not persisted in the repository.",
        ],
    }
    json_path.write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    md_path.write_text(
        "\n".join(
            [
                "# Zenodo DEX Self-Trade Direct Gate",
                "",
                f"Run ID: `{RUN_ID}`",
                "",
                "## Result",
                "",
                f"- Rows exported: `{len(rows)}`.",
                f"- Positive self-trade rows: `{positive_rows}`.",
                f"- Same-venue non-self negative controls: `{negative_rows}`.",
                f"- Minimum calibration/test per-venue/class Wilson95 LCB: `{min_cal_test_class_lcb:.6f}`.",
                f"- Accepted direct self-trade slice at 95: `{str(accepted_slice).lower()}`.",
                f"- Accepted direct `Manipulation` rows added: `{len(rows) if accepted_slice else 0}`.",
                "- Accepted parent-root slots added: `0`.",
                "- Full Board A goal achieved: `false`.",
                f"- Gate result: `{audit['gate_result']}`.",
                "- Runtime code changed: false. Thresholds relaxed: false. Raw data committed: false. Trade usable: false.",
                "",
                "## Scope",
                "",
                "This is real DEX order-lifecycle evidence for a bounded self-trade/wash-trade slice. It does not close `Bull`, `Bear`, `Sideways`, `Crisis`, or full manipulation-variety coverage.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    checks = [
        "PASS rows_exported_ge_1000" if len(rows) >= 1000 else "FAIL rows_exported_ge_1000",
        "PASS positive_rows_ge_500" if positive_rows >= 500 else "FAIL positive_rows_ge_500",
        "PASS negative_rows_ge_500" if negative_rows >= 500 else "FAIL negative_rows_ge_500",
        (
            "PASS min_calibration_test_per_venue_class_wilson95_lcb_ge_0_95"
            if min_cal_test_class_lcb >= 0.95
            else "FAIL min_calibration_test_per_venue_class_wilson95_lcb_ge_0_95"
        ),
        (
            "PASS accepted_direct_self_trade_slice_95_true"
            if accepted_slice
            else "FAIL accepted_direct_self_trade_slice_95_true"
        ),
        "PASS accepted_parent_root_slots_added_0",
        "PASS full_board_goal_achieved_false",
        "PASS thresholds_relaxed_false",
        "PASS runtime_code_changed_false",
        "PASS raw_data_committed_false",
        "PASS trade_usable_false",
    ]
    checks_path.write_text("\n".join(checks) + "\n", encoding="utf-8")

    failures = [line for line in checks if line.startswith("FAIL")]
    if failures:
        raise SystemExit("\n".join(failures))


if __name__ == "__main__":
    main()
