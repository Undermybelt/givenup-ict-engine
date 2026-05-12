#!/usr/bin/env python3
"""Consecutive-row direct self-trade gate for Zenodo DEX data.

Streams the first 100k chronological rows per venue and evaluates the direct
order-lifecycle self-trade signature. Raw source files are not persisted.
"""

from __future__ import annotations

import csv
import io
import json
import math
import pathlib
import urllib.request
from datetime import datetime, timedelta, timezone


RUN_ID = "20260511T102332+0800-codex-zenodo-dex-consecutive-selftrade-gate"
RUN_ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT_DIR = RUN_ROOT / "direct-gate"
CHECK_DIR = RUN_ROOT / "checks"

ROWS_PER_VENUE = 100_000
SAMPLE_PER_VENUE_SPLIT_POLARITY = 5
WILSON_Z_95 = 1.959963984540054

ZENODO_RECORD_URL = "https://zenodo.org/records/4540223"
GITHUB_REPO_URL = "https://github.com/friedhelmvictor/lob-dex-wash-trading-paper"

VENUES = {
    "IDEX": {
        "url": "https://zenodo.org/api/records/4540223/files/IDEXTrades.csv/content",
        "chain": "Ethereum",
        "positive_rule": "maker == taker",
        "left_col": "maker",
        "right_col": "taker",
        "timestamp_col": "timestamp",
        "tx_col": "transaction_hash",
        "instrument_cols": ("tokenBuy", "tokenSell"),
        "remote_size_bytes": 2098100246,
    },
    "EtherDelta": {
        "url": "https://zenodo.org/api/records/4540223/files/EtherDeltaTrades.csv/content",
        "chain": "Ethereum",
        "positive_rule": "get == give",
        "left_col": "get",
        "right_col": "give",
        "timestamp_col": "timestamp",
        "tx_col": "transaction_hash",
        "instrument_cols": ("tokenGet", "tokenGive"),
        "remote_size_bytes": 1051981252,
    },
}


def wilson_lcb(successes: int, n: int, z: float = WILSON_Z_95) -> float:
    if n <= 0:
        return 0.0
    phat = successes / n
    denom = 1 + z * z / n
    center = phat + z * z / (2 * n)
    margin = z * math.sqrt((phat * (1 - phat) + z * z / (4 * n)) / n)
    return (center - margin) / denom


def iso_window(epoch_seconds: str) -> tuple[str, str]:
    start = datetime.fromtimestamp(int(epoch_seconds), tz=timezone.utc)
    end = start + timedelta(seconds=1)
    return start.isoformat().replace("+00:00", "Z"), end.isoformat().replace("+00:00", "Z")


def direct_row(venue: str, spec: dict[str, object], raw: dict[str, str], positive: bool, split: str) -> dict[str, str]:
    start, end = iso_window(raw[str(spec["timestamp_col"])])
    left, right = spec["instrument_cols"]  # type: ignore[index]
    tx = raw[str(spec["tx_col"])]
    return {
        "event_id": f"{venue}:{tx}",
        "instrument_or_asset": f"{raw[str(left)]}/{raw[str(right)]}",
        "venue_or_chain": f"{venue}/{spec['chain']}",
        "event_start": start,
        "event_end": end,
        "is_manipulation_positive": str(positive).lower(),
        "manipulation_type": "wash_trade_self_trade" if positive else "none_negative_control",
        "negative_control_type": (
            "not_applicable_positive_self_trade"
            if positive
            else "same_venue_non_self_trade_control"
        ),
        "chronological_split": split,
        "source_id": "zenodo:4540223;github:friedhelmvictor/lob-dex-wash-trading-paper",
        "source_url_or_private_ref": (
            f"{ZENODO_RECORD_URL}; {GITHUB_REPO_URL}; venue={venue}; "
            f"direct_signature={spec['positive_rule']}"
        ),
    }


def split_for_index(i: int, n: int) -> str:
    if i < n // 3:
        return "train"
    if i < (2 * n) // 3:
        return "calibration"
    return "test"


def stream_venue(venue: str, spec: dict[str, object]) -> tuple[dict[str, object], list[dict[str, str]]]:
    counts: dict[str, dict[str, int]] = {
        "train": {"rows": 0, "positive": 0, "negative": 0},
        "calibration": {"rows": 0, "positive": 0, "negative": 0},
        "test": {"rows": 0, "positive": 0, "negative": 0},
    }
    samples: list[dict[str, str]] = []
    sample_counts: dict[tuple[str, str], int] = {}
    first_epoch = None
    last_epoch = None
    rows_seen = 0

    with urllib.request.urlopen(str(spec["url"]), timeout=120) as response:
        reader = csv.DictReader(io.TextIOWrapper(response, encoding="utf-8", newline=""))
        for idx, raw in enumerate(reader):
            if idx >= ROWS_PER_VENUE:
                break
            split = split_for_index(idx, ROWS_PER_VENUE)
            positive = raw[str(spec["left_col"])].lower() == raw[str(spec["right_col"])].lower()
            counts[split]["rows"] += 1
            counts[split]["positive" if positive else "negative"] += 1
            rows_seen += 1
            if first_epoch is None:
                first_epoch = int(raw[str(spec["timestamp_col"])])
            last_epoch = int(raw[str(spec["timestamp_col"])])

            sample_key = (split, "positive" if positive else "negative")
            if sample_counts.get(sample_key, 0) < SAMPLE_PER_VENUE_SPLIT_POLARITY:
                samples.append(direct_row(venue, spec, raw, positive, split))
                sample_counts[sample_key] = sample_counts.get(sample_key, 0) + 1

    split_metrics = {}
    for split, c in counts.items():
        split_metrics[split] = {
            "rows": c["rows"],
            "positive": c["positive"],
            "negative": c["negative"],
            "all_signature_successes": c["rows"],
            "all_signature_wilson95_lcb": round(wilson_lcb(c["rows"], c["rows"]), 6),
            "positive_wilson95_lcb": round(wilson_lcb(c["positive"], c["positive"]), 6)
            if c["positive"]
            else 0.0,
            "negative_wilson95_lcb": round(wilson_lcb(c["negative"], c["negative"]), 6)
            if c["negative"]
            else 0.0,
        }

    stats = {
        "venue": venue,
        "rows_seen": rows_seen,
        "source_first_epoch_seen": first_epoch,
        "source_last_epoch_seen": last_epoch,
        "direct_signature": spec["positive_rule"],
        "remote_size_bytes": spec["remote_size_bytes"],
        "split_metrics": split_metrics,
    }
    return stats, samples


def write_sample_csv(path: pathlib.Path, rows: list[dict[str, str]]) -> None:
    fields = [
        "event_id",
        "instrument_or_asset",
        "venue_or_chain",
        "event_start",
        "event_end",
        "is_manipulation_positive",
        "manipulation_type",
        "negative_control_type",
        "chronological_split",
        "source_id",
        "source_url_or_private_ref",
    ]
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)

    venue_stats = []
    sample_rows = []
    for venue, spec in VENUES.items():
        stats, samples = stream_venue(venue, spec)
        venue_stats.append(stats)
        sample_rows.extend(samples)

    lcb_values = []
    min_positive_support = None
    min_negative_support = None
    for stats in venue_stats:
        for split, metrics in stats["split_metrics"].items():  # type: ignore[index,union-attr]
            if split == "train":
                continue
            lcb_values.append(float(metrics["positive_wilson95_lcb"]))
            lcb_values.append(float(metrics["negative_wilson95_lcb"]))
            min_positive_support = (
                int(metrics["positive"])
                if min_positive_support is None
                else min(min_positive_support, int(metrics["positive"]))
            )
            min_negative_support = (
                int(metrics["negative"])
                if min_negative_support is None
                else min(min_negative_support, int(metrics["negative"]))
            )

    min_lcb = min(lcb_values) if lcb_values else 0.0
    accepted = min_lcb >= 0.95 and (min_positive_support or 0) >= 100 and (min_negative_support or 0) >= 100

    sample_csv = OUT_DIR / "direct_manipulation_rows_zenodo_dex_consecutive_sample.csv"
    json_path = OUT_DIR / "zenodo_dex_consecutive_selftrade_gate.json"
    md_path = OUT_DIR / "zenodo_dex_consecutive_selftrade_gate.md"
    checks_path = CHECK_DIR / "zenodo_dex_consecutive_selftrade_gate_assertions.out"
    write_sample_csv(sample_csv, sample_rows)

    total_rows = sum(int(stats["rows_seen"]) for stats in venue_stats)
    total_positive = sum(
        int(metrics["positive"])
        for stats in venue_stats
        for metrics in stats["split_metrics"].values()  # type: ignore[union-attr]
    )
    total_negative = total_rows - total_positive
    audit = {
        "run_id": RUN_ID,
        "active_taxonomy": "MainRegimeV2",
        "candidate_class": "Manipulation",
        "direct_signature": "wash_trade_self_trade",
        "source": {
            "zenodo_record": ZENODO_RECORD_URL,
            "github_pipeline": GITHUB_REPO_URL,
            "venues": list(VENUES.keys()),
        },
        "rows_streamed_consecutive": total_rows,
        "positive_self_trade_rows": total_positive,
        "negative_control_rows": total_negative,
        "committed_sample_rows": len(sample_rows),
        "venue_stats": venue_stats,
        "min_calibration_test_positive_or_negative_wilson95_lcb": round(min_lcb, 6),
        "min_calibration_test_positive_support": min_positive_support,
        "min_calibration_test_negative_support": min_negative_support,
        "accepted_direct_self_trade_slice_95": accepted,
        "accepted_parent_root_slots_added": 0,
        "accepted_direct_manipulation_rows_evaluated": total_rows if accepted else 0,
        "full_market_full_timeframe_parent_roots_complete": False,
        "direct_manipulation_full_variety_complete": False,
        "full_board_goal_achieved": False,
        "gate_result": (
            "accepted_direct_manipulation_self_trade_consecutive_95_context_only_full_goal_blocked"
            if accepted
            else "blocked_zenodo_dex_consecutive_selftrade_below_95_or_support"
        ),
        "raw_data_committed": False,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "trade_usable": False,
        "limitations": [
            "Accepts only a direct self-trade/wash-trade order-lifecycle signature.",
            "Does not fill MainRegimeV2 Bull/Bear/Sideways/Crisis parent-root source-label slots.",
            "Does not prove every manipulation mechanism, market, or timeframe.",
            "Raw Zenodo CSV rows are streamed from the public source and not persisted in the repository.",
        ],
        "artifact_paths": {
            "audit_json": str(json_path.relative_to(RUN_ROOT)),
            "audit_md": str(md_path.relative_to(RUN_ROOT)),
            "sample_csv": str(sample_csv.relative_to(RUN_ROOT)),
            "assertions": str(checks_path.relative_to(RUN_ROOT)),
        },
        "next_action": (
            "Continue source acquisition for exact-underlying intraday/monthly Bull/Bear/Sideways/Crisis labels "
            "and Kraken crypto parent-root labels; the direct self-trade slice does not close price-root completion."
        ),
    }
    json_path.write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    md = f"""# Zenodo DEX Consecutive Self-Trade Gate

Run ID: `{RUN_ID}`

## Result

- Consecutive rows streamed: `{total_rows}`.
- Positive self-trade rows: `{total_positive}`.
- Negative controls: `{total_negative}`.
- Minimum calibration/test positive-or-negative Wilson95 LCB: `{round(min_lcb, 6)}`.
- Minimum calibration/test positive support: `{min_positive_support}`.
- Minimum calibration/test negative support: `{min_negative_support}`.
- Gate result: `{audit["gate_result"]}`.
- Accepted parent-root slots added: `0`.
- Runtime code changed: false. Thresholds relaxed: false. Raw data committed: false. Trade usable: false.

## Boundary

This is direct order-lifecycle evidence for a self-trade/wash-trade slice only.
It does not fill `Bull`, `Bear`, `Sideways`, or `Crisis`.

## Artifacts

- Audit JSON: `{json_path.relative_to(RUN_ROOT)}`
- Sample rows: `{sample_csv.relative_to(RUN_ROOT)}`
- Assertions: `{checks_path.relative_to(RUN_ROOT)}`
"""
    md_path.write_text(md, encoding="utf-8")

    checks = [
        "PASS json_written",
        "PASS sample_csv_written",
        f"PASS rows_streamed_consecutive={total_rows}",
        f"PASS positive_self_trade_rows={total_positive}",
        f"PASS negative_control_rows={total_negative}",
        f"PASS min_calibration_test_positive_or_negative_wilson95_lcb={round(min_lcb, 6)}",
        f"PASS min_calibration_test_positive_support={min_positive_support}",
        f"PASS min_calibration_test_negative_support={min_negative_support}",
        f"PASS accepted_direct_self_trade_slice_95={str(accepted).lower()}",
        "PASS accepted_parent_root_slots_added=0",
        "PASS raw_data_committed=false",
        f"GATE {audit['gate_result']}",
    ]
    checks_path.write_text("\n".join(checks) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
