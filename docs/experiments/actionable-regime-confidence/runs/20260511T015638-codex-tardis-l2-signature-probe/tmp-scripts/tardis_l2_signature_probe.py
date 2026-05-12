from __future__ import annotations

import csv
import gzip
import json
import math
import subprocess
from collections import Counter, defaultdict, deque
from io import TextIOWrapper
from pathlib import Path
from statistics import mean
from typing import Any


REPO = Path("/Users/thrill3r/projects-ict-engine/ict-engine")
RUN_ROOT = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T015638-codex-tardis-l2-signature-probe"
)
OUT_DIR = RUN_ROOT / "direct-l2-signatures"
CHECKS_DIR = RUN_ROOT / "checks"
LOOP_ID = "20260511T015638+0800-codex-tardis-l2-signature-probe"

SOURCES: list[dict[str, Any]] = []
for month in ("09", "10", "11"):
    SOURCES.append(
        {
            "name": f"bitmex_xbtusd_book_snapshot_5_2020_{month}_01",
            "exchange": "bitmex",
            "symbol": "XBTUSD",
            "data_type": "book_snapshot_5",
            "url": f"https://datasets.tardis.dev/v1/bitmex/book_snapshot_5/2020/{month}/01/XBTUSD.csv.gz",
            "row_limit": 40000,
        }
    )
    SOURCES.append(
        {
            "name": f"binance_futures_btcusdt_book_snapshot_5_2020_{month}_01",
            "exchange": "binance-futures",
            "symbol": "BTCUSDT",
            "data_type": "book_snapshot_5",
            "url": f"https://datasets.tardis.dev/v1/binance-futures/book_snapshot_5/2020/{month}/01/BTCUSDT.csv.gz",
            "row_limit": 40000,
        }
    )
for month in ("04", "05", "06"):
    SOURCES.append(
        {
            "name": f"deribit_btc_perpetual_incremental_book_l2_2020_{month}_01",
            "exchange": "deribit",
            "symbol": "BTC-PERPETUAL",
            "data_type": "incremental_book_L2",
            "url": f"https://datasets.tardis.dev/v1/deribit/incremental_book_L2/2020/{month}/01/BTC-PERPETUAL.csv.gz",
            "row_limit": 60000,
        }
    )


def repo_rel(path: Path) -> str:
    return str(path.relative_to(REPO))


def as_float(value: Any) -> float | None:
    try:
        out = float(value)
    except (TypeError, ValueError):
        return None
    return out if math.isfinite(out) else None


def as_int(value: Any) -> int | None:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def ts_seconds(row: dict[str, str]) -> int | None:
    ts = as_int(row.get("timestamp"))
    if ts is None:
        return None
    # Tardis timestamps are microseconds in the sampled files.
    return ts // 1_000_000


def top_book_depth(row: dict[str, str], side: str, levels: int = 5) -> float:
    total = 0.0
    for idx in range(levels):
        amount = as_float(row.get(f"{side}[{idx}].amount"))
        if amount is not None:
            total += amount
    return total


def top_book_price(row: dict[str, str], side: str, level: int = 0) -> float | None:
    return as_float(row.get(f"{side}[{level}].price"))


def snapshot_signatures(rows: list[dict[str, str]]) -> dict[str, Any]:
    spreads: list[float] = []
    imbalances: list[float] = []
    wall_events = 0
    wall_cancel_events = 0
    layering_stack_events = 0
    previous_walls: deque[tuple[int, str, float, float]] = deque(maxlen=50)

    for row in rows:
        sec = ts_seconds(row)
        ask0 = top_book_price(row, "asks")
        bid0 = top_book_price(row, "bids")
        if ask0 is None or bid0 is None or ask0 < bid0:
            continue
        spread = ask0 - bid0
        spreads.append(spread)
        mid = (ask0 + bid0) / 2.0
        ask_depth = top_book_depth(row, "asks", 5)
        bid_depth = top_book_depth(row, "bids", 5)
        if ask_depth + bid_depth > 0:
            imbalances.append((bid_depth - ask_depth) / (bid_depth + ask_depth))
        if min(ask_depth, bid_depth) <= 0:
            continue

        ask_ratio = ask_depth / bid_depth
        bid_ratio = bid_depth / ask_depth
        wall_side = ""
        wall_depth = 0.0
        wall_ratio = 0.0
        if ask_ratio >= 8.0:
            wall_side = "ask"
            wall_depth = ask_depth
            wall_ratio = ask_ratio
        elif bid_ratio >= 8.0:
            wall_side = "bid"
            wall_depth = bid_depth
            wall_ratio = bid_ratio

        if wall_side:
            wall_events += 1
            if wall_ratio >= 12.0:
                layering_stack_events += 1
            if sec is not None:
                for prev_sec, prev_side, prev_depth, prev_mid in list(previous_walls):
                    if prev_side != wall_side:
                        continue
                    if sec - prev_sec < 0 or sec - prev_sec > 5:
                        continue
                    if prev_depth <= 0:
                        continue
                    depth_drop = (prev_depth - wall_depth) / prev_depth
                    mid_move = abs(mid - prev_mid)
                    if depth_drop >= 0.70 and mid_move <= max(spread * 2.0, 1e-9):
                        wall_cancel_events += 1
                        break
                previous_walls.append((sec, wall_side, wall_depth, mid))

    return {
        "spread_count": len(spreads),
        "spread_mean": mean(spreads) if spreads else None,
        "spread_max": max(spreads) if spreads else None,
        "top5_imbalance_mean": mean(imbalances) if imbalances else None,
        "wall_events": wall_events,
        "wall_cancel_without_price_move_events": wall_cancel_events,
        "layering_stack_events": layering_stack_events,
    }


def incremental_signatures(rows: list[dict[str, str]]) -> dict[str, Any]:
    by_second: dict[int, Counter[str]] = defaultdict(Counter)
    side_counts: Counter[str] = Counter()
    zero_amount_updates = 0
    snapshot_rows = 0
    update_rows = 0
    for row in rows:
        sec = ts_seconds(row)
        side = row.get("side") or "unknown"
        amount = as_float(row.get("amount"))
        if row.get("is_snapshot", "").lower() == "true":
            snapshot_rows += 1
        if amount == 0.0:
            zero_amount_updates += 1
            if sec is not None:
                by_second[sec][f"cancel_{side}"] += 1
        if sec is not None:
            by_second[sec]["updates"] += 1
            by_second[sec][side] += 1
        side_counts[side] += 1
        update_rows += 1

    burst_seconds = 0
    one_sided_cancel_burst_seconds = 0
    max_updates_per_second = 0
    for counts in by_second.values():
        updates = counts["updates"]
        max_updates_per_second = max(max_updates_per_second, updates)
        if updates >= 250:
            burst_seconds += 1
        cancel_buy = counts["cancel_buy"]
        cancel_sell = counts["cancel_sell"]
        cancels = cancel_buy + cancel_sell
        if updates >= 250 and cancels >= 100 and max(cancel_buy, cancel_sell) / max(cancels, 1) >= 0.75:
            one_sided_cancel_burst_seconds += 1

    return {
        "update_rows": update_rows,
        "snapshot_rows": snapshot_rows,
        "zero_amount_updates": zero_amount_updates,
        "zero_amount_update_ratio": zero_amount_updates / update_rows if update_rows else None,
        "side_counts": dict(side_counts),
        "seconds_observed": len(by_second),
        "max_updates_per_second": max_updates_per_second,
        "update_burst_seconds": burst_seconds,
        "one_sided_cancel_burst_seconds": one_sided_cancel_burst_seconds,
    }


def stream_rows(source: dict[str, Any]) -> tuple[list[dict[str, str]], list[str], str]:
    proc = subprocess.Popen(
        ["curl", "-L", "--silent", "--show-error", "--max-time", "60", source["url"]],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    assert proc.stdout is not None
    rows: list[dict[str, str]] = []
    header: list[str] = []
    stderr = ""
    try:
        with gzip.GzipFile(fileobj=proc.stdout) as gzip_file:
            text = TextIOWrapper(gzip_file, encoding="utf-8", newline="")
            reader = csv.DictReader(text)
            header = reader.fieldnames or []
            for row in reader:
                rows.append(dict(row))
                if len(rows) >= int(source["row_limit"]):
                    break
    except Exception as exc:  # noqa: BLE001 - artifact needs failure state.
        stderr = f"{type(exc).__name__}: {exc}"
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            proc.kill()
        if proc.stderr is not None:
            stderr = (stderr + "\n" + proc.stderr.read().decode("utf-8", errors="replace")).strip()
    return rows, header, stderr[-800:]


def analyze_source(source: dict[str, Any]) -> dict[str, Any]:
    rows, header, stderr = stream_rows(source)
    direct_fields: list[str] = []
    if any(column.startswith("asks[") or column.startswith("bids[") for column in header):
        direct_fields.append("top_book_levels")
    if {"side", "price", "amount"}.issubset(set(header)):
        direct_fields.append("l2_update_side_price_amount")
    if "is_snapshot" in header:
        direct_fields.append("snapshot_flag")

    if source["data_type"] == "incremental_book_L2":
        signatures = incremental_signatures(rows)
    else:
        signatures = snapshot_signatures(rows)

    first_ts = rows[0].get("timestamp") if rows else None
    last_ts = rows[-1].get("timestamp") if rows else None
    return {
        **source,
        "sample_status": "sampled" if rows else "no_rows",
        "rows_sampled": len(rows),
        "first_timestamp": first_ts,
        "last_timestamp": last_ts,
        "headers": header,
        "direct_fields": direct_fields,
        "signature_features": signatures,
        "stderr_tail": stderr,
    }


def write_outputs(result: dict[str, Any]) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECKS_DIR.mkdir(parents=True, exist_ok=True)
    report_json = OUT_DIR / "tardis_l2_signature_probe_report.json"
    report_md = OUT_DIR / "tardis_l2_signature_probe_report.md"
    summary_csv = OUT_DIR / "tardis_l2_signature_probe_summary.csv"
    report_json.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")

    with summary_csv.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(
            [
                "name",
                "exchange",
                "symbol",
                "data_type",
                "rows_sampled",
                "wall_events",
                "wall_cancel_without_price_move_events",
                "layering_stack_events",
                "zero_amount_updates",
                "update_burst_seconds",
                "one_sided_cancel_burst_seconds",
            ]
        )
        for source in result["sources"]:
            features = source.get("signature_features", {})
            writer.writerow(
                [
                    source["name"],
                    source["exchange"],
                    source["symbol"],
                    source["data_type"],
                    source["rows_sampled"],
                    features.get("wall_events", 0),
                    features.get("wall_cancel_without_price_move_events", 0),
                    features.get("layering_stack_events", 0),
                    features.get("zero_amount_updates", 0),
                    features.get("update_burst_seconds", 0),
                    features.get("one_sided_cancel_burst_seconds", 0),
                ]
            )

    decision = result["decision"]
    report_md.write_text(
        "# Tardis L2 Signature Probe\n\n"
        f"Run id: `{LOOP_ID}`\n\n"
        "This run streamed bounded public Tardis first-day direct L2/order-book samples across multiple months and exchanges. "
        "It kept only compact derived feature summaries in the repo, not full raw order-book files.\n\n"
        "Explicit signatures tested:\n"
        "- snapshot wall imbalance,\n"
        "- wall cancellation without immediate price movement,\n"
        "- layering-stack depth imbalance,\n"
        "- incremental L2 update bursts,\n"
        "- one-sided cancellation bursts.\n\n"
        f"Accessible source count: {decision['accessible_source_count']} / {decision['attempted_source_count']}.\n"
        f"Signature candidate events: {decision['signature_candidate_events']}.\n"
        f"Gate: `{decision['accepted_gate']}`.\n"
        f"Reason: {decision['blocker']}\n\n"
        "These are unlabeled direct-L2 signatures, not accepted manipulation proof.\n",
        encoding="utf-8",
    )

    (CHECKS_DIR / "tardis_l2_signature_probe_assertions.out").write_text(
        "\n".join(
            [
                f"RUN_ID {LOOP_ID}",
                f"REPORT {repo_rel(report_json)}",
                f"SUMMARY {repo_rel(summary_csv)}",
                f"ATTEMPTED_SOURCE_COUNT {decision['attempted_source_count']}",
                f"ACCESSIBLE_SOURCE_COUNT {decision['accessible_source_count']}",
                f"SIGNATURE_CANDIDATE_EVENTS {decision['signature_candidate_events']}",
                "QUALIFYING_DIRECT_MANIPULATION_INPUT_SETS 0",
                f"ACCEPTED_GATE {decision['accepted_gate']}",
                f"MANIPULATION_INPUT_STATE {decision['manipulation_input_state']}",
                "THRESHOLDS_RELAXED false",
                "RUNTIME_CODE_CHANGED false",
                "FRESH_CALIBRATION_RERUN false",
                "TRADE_USABLE false",
                "NO_FULL_RAW_L2_COMMITTED true",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (RUN_ROOT / "README.md").write_text(
        "# Tardis L2 Signature Probe\n\n"
        "- report: `direct-l2-signatures/tardis_l2_signature_probe_report.md`\n"
        "- json: `direct-l2-signatures/tardis_l2_signature_probe_report.json`\n"
        "- summary: `direct-l2-signatures/tardis_l2_signature_probe_summary.csv`\n"
        "- assertions: `checks/tardis_l2_signature_probe_assertions.out`\n",
        encoding="utf-8",
    )


def main() -> int:
    sources = [analyze_source(source) for source in SOURCES]
    accessible = [source for source in sources if source["rows_sampled"] > 0 and source["direct_fields"]]
    signature_candidate_events = 0
    for source in accessible:
        features = source.get("signature_features", {})
        signature_candidate_events += int(features.get("wall_cancel_without_price_move_events", 0) or 0)
        signature_candidate_events += int(features.get("layering_stack_events", 0) or 0)
        signature_candidate_events += int(features.get("one_sided_cancel_burst_seconds", 0) or 0)

    result = {
        "schema_version": "tardis-l2-signature-probe/v1",
        "loop_id": LOOP_ID,
        "run_root": repo_rel(RUN_ROOT),
        "raw_data_policy": "stream_bounded_samples_only_no_full_raw_l2_committed",
        "sources": sources,
        "decision": {
            "attempted_source_count": len(SOURCES),
            "accessible_source_count": len(accessible),
            "accessible_direct_sources": [source["name"] for source in accessible],
            "signature_candidate_events": signature_candidate_events,
            "explicit_signatures_tested": [
                "snapshot_wall_imbalance",
                "wall_cancel_without_immediate_price_move",
                "layering_stack_depth_imbalance",
                "incremental_l2_update_burst",
                "one_sided_cancel_burst",
            ],
            "manipulation_input_state": "direct_l2_signature_features_unlabeled_not_calibration_grade",
            "qualifying_direct_manipulation_input_sets": 0,
            "accepted_gate": "blocked_unlabeled_direct_l2_signatures",
            "thresholds_relaxed": False,
            "runtime_code_changed": False,
            "fresh_calibration_rerun": False,
            "trade_usable": False,
            "blocker": "Public Tardis first-day samples can produce direct-L2 signature features, but there is no labeled/event-confirmed manipulation truth and no chronological positive/negative calibration set. Signature counts remain candidate evidence only.",
            "next_action": "Add labeled/event-confirmed manipulation windows or construct an explicit positive/negative event ledger before any 95% Manipulation calibration attempt; otherwise keep Manipulation fail-closed.",
        },
    }
    write_outputs(result)
    print(json.dumps(result["decision"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
