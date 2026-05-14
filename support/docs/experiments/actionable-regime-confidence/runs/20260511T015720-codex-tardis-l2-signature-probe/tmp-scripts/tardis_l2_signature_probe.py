from __future__ import annotations

import csv
import gzip
import json
import math
import subprocess
from collections import Counter, defaultdict
from io import TextIOWrapper
from pathlib import Path
from statistics import mean
from typing import Any


REPO = Path("/Users/thrill3r/projects-ict-engine/ict-engine")
RUN_ROOT = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T015720-codex-tardis-l2-signature-probe"
)
OUT_DIR = RUN_ROOT / "signature-probe"
CHECKS_DIR = RUN_ROOT / "checks"
LOOP_ID = "20260511T015720+0800-codex-tardis-l2-signature-probe"

MONTHS = ["2020/09/01", "2020/10/01", "2020/11/01"]
SOURCES = []
for month in MONTHS:
    y, m, d = month.split("/")
    SOURCES.extend(
        [
            {
                "name": f"bitmex_xbtusd_book_snapshot_5_{y}_{m}_{d}",
                "exchange": "bitmex",
                "symbol": "XBTUSD",
                "data_type": "book_snapshot_5",
                "url": f"https://datasets.tardis.dev/v1/bitmex/book_snapshot_5/{month}/XBTUSD.csv.gz",
                "row_limit": 70000,
            },
            {
                "name": f"binance_futures_btcusdt_book_snapshot_5_{y}_{m}_{d}",
                "exchange": "binance-futures",
                "symbol": "BTCUSDT",
                "data_type": "book_snapshot_5",
                "url": f"https://datasets.tardis.dev/v1/binance-futures/book_snapshot_5/{month}/BTCUSDT.csv.gz",
                "row_limit": 70000,
            },
        ]
    )
for month in ["2020/04/01", "2020/05/01", "2020/06/01"]:
    y, m, d = month.split("/")
    SOURCES.append(
        {
            "name": f"deribit_btc_perpetual_incremental_book_l2_{y}_{m}_{d}",
            "exchange": "deribit",
            "symbol": "BTC-PERPETUAL",
            "data_type": "incremental_book_L2",
            "url": f"https://datasets.tardis.dev/v1/deribit/incremental_book_L2/{month}/BTC-PERPETUAL.csv.gz",
            "row_limit": 100000,
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


def stream_rows(source: dict[str, Any]):
    proc = subprocess.Popen(
        ["curl", "-L", "--silent", "--show-error", "--max-time", "60", source["url"]],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    assert proc.stdout is not None
    text = TextIOWrapper(gzip.GzipFile(fileobj=proc.stdout), encoding="utf-8", newline="")
    reader = csv.DictReader(text)
    try:
        for idx, row in enumerate(reader, start=1):
            yield idx, row, reader.fieldnames or []
            if idx >= int(source["row_limit"]):
                break
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            proc.kill()


def probe_snapshot(source: dict[str, Any]) -> dict[str, Any]:
    rows = 0
    extreme_imbalance = 0
    wide_spread = 0
    spread_values: list[float] = []
    imbalance_values: list[float] = []
    first_ts = None
    last_ts = None
    headers: list[str] = []
    truncated_stream = False
    try:
        for rows, row, headers in stream_rows(source):
            first_ts = first_ts or row.get("timestamp")
            last_ts = row.get("timestamp")
            ask0 = as_float(row.get("asks[0].price"))
            bid0 = as_float(row.get("bids[0].price"))
            ask_amt = as_float(row.get("asks[0].amount"))
            bid_amt = as_float(row.get("bids[0].amount"))
            spread = None
            if ask0 is not None and bid0 is not None and ask0 >= bid0:
                spread = ask0 - bid0
                spread_values.append(spread)
            if ask_amt is not None and bid_amt is not None and ask_amt + bid_amt > 0:
                imb = (bid_amt - ask_amt) / (bid_amt + ask_amt)
                imbalance_values.append(imb)
                if abs(imb) >= 0.90:
                    extreme_imbalance += 1
            if spread is not None and spread_values and spread >= 5.0 * max(1e-12, mean(spread_values)):
                wide_spread += 1
    except EOFError:
        # Bounded streaming deliberately terminates curl before gzip sees an
        # end-of-stream marker. Rows already read are the intended sample.
        truncated_stream = True
    return {
        **source,
        "rows_sampled": rows,
        "first_timestamp": first_ts,
        "last_timestamp": last_ts,
        "headers": headers,
        "bounded_stream_truncated": truncated_stream,
        "direct_fields": ["top_book_levels"] if rows else [],
        "signature_counts": {
            "top_level_abs_imbalance_ge_0_90": extreme_imbalance,
            "spread_ge_5x_running_mean": wide_spread,
        },
        "signature_rates": {
            "top_level_abs_imbalance_ge_0_90": extreme_imbalance / rows if rows else 0.0,
            "spread_ge_5x_running_mean": wide_spread / rows if rows else 0.0,
        },
        "spread_mean": mean(spread_values) if spread_values else None,
        "top_level_imbalance_mean": mean(imbalance_values) if imbalance_values else None,
    }


def probe_incremental(source: dict[str, Any]) -> dict[str, Any]:
    rows = 0
    zero_amount = 0
    snapshot_rows = 0
    side_counts: Counter[str] = Counter()
    zero_by_ts: Counter[str] = Counter()
    update_by_ts: Counter[str] = Counter()
    first_ts = None
    last_ts = None
    headers: list[str] = []
    truncated_stream = False
    try:
        for rows, row, headers in stream_rows(source):
            ts = str(row.get("timestamp") or "")
            first_ts = first_ts or ts
            last_ts = ts
            update_by_ts[ts] += 1
            if row.get("is_snapshot", "").lower() == "true":
                snapshot_rows += 1
            side = row.get("side")
            if side:
                side_counts[side] += 1
            amount = as_float(row.get("amount"))
            if amount == 0.0:
                zero_amount += 1
                zero_by_ts[ts] += 1
    except EOFError:
        truncated_stream = True
    cancel_bursts = sum(1 for count in zero_by_ts.values() if count >= 10)
    update_bursts = sum(1 for count in update_by_ts.values() if count >= 50)
    return {
        **source,
        "rows_sampled": rows,
        "first_timestamp": first_ts,
        "last_timestamp": last_ts,
        "headers": headers,
        "bounded_stream_truncated": truncated_stream,
        "direct_fields": ["l2_update_side_price_amount", "snapshot_flag"] if rows else [],
        "snapshot_rows": snapshot_rows,
        "side_counts": dict(side_counts),
        "zero_amount_updates": zero_amount,
        "signature_counts": {
            "zero_amount_updates": zero_amount,
            "timestamp_cancel_bursts_ge_10": cancel_bursts,
            "timestamp_update_bursts_ge_50": update_bursts,
        },
        "signature_rates": {
            "zero_amount_updates": zero_amount / rows if rows else 0.0,
            "timestamp_cancel_bursts_ge_10_per_distinct_ts": cancel_bursts / max(1, len(zero_by_ts)),
            "timestamp_update_bursts_ge_50_per_distinct_ts": update_bursts / max(1, len(update_by_ts)),
        },
    }


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECKS_DIR.mkdir(parents=True, exist_ok=True)
    probes = []
    for source in SOURCES:
        if source["data_type"] == "book_snapshot_5":
            probes.append(probe_snapshot(source))
        else:
            probes.append(probe_incremental(source))
    accessible = [p for p in probes if p["rows_sampled"] > 0 and p["direct_fields"]]
    months = sorted({p["name"].split("_")[-3] + "-" + p["name"].split("_")[-2] for p in accessible})
    exchanges = sorted({p["exchange"] for p in accessible})
    decision = {
        "direct_l2_sources_sampled": len(accessible),
        "exchanges_sampled": exchanges,
        "month_buckets_sampled": months,
        "signature_probe_completed": True,
        "manipulation_input_state": "direct_l2_signatures_unlabeled_not_manipulation_acceptance",
        "qualifying_direct_manipulation_input_sets": 0,
        "accepted_gate": "blocked_signature_probe_only",
        "thresholds_relaxed": False,
        "runtime_code_changed": False,
        "fresh_calibration_rerun": False,
        "trade_usable": False,
        "blocker": "Direct L2 signatures were derived across public samples, but there is no labeled/event-confirmed manipulation target and no chronological 95 calibration packet.",
        "next_action": "Pair direct L2 signatures with event-confirmed manipulation labels, regulatory event windows, or broader labeled pump/spoof datasets before rerunning Manipulation gates; keep OHLCV/proxy-only paths fail-closed.",
    }
    report = {
        "schema_version": "tardis-l2-signature-probe/v1",
        "loop_id": LOOP_ID,
        "run_root": repo_rel(RUN_ROOT),
        "source_doc": "https://docs.tardis.dev/downloadable-csv-files/overview.md",
        "data_types_doc": "https://docs.tardis.dev/downloadable-csv-files/data-types.md",
        "sources": probes,
        "declared_signatures": {
            "top_level_abs_imbalance_ge_0_90": "snapshot top-level imbalance extreme; context feature only",
            "spread_ge_5x_running_mean": "snapshot spread shock; context feature only",
            "zero_amount_updates": "incremental L2 remove/update events; cancellation-pressure feature only",
            "timestamp_cancel_bursts_ge_10": "same-timestamp cancellation burst; spoofing/layering candidate feature only",
            "timestamp_update_bursts_ge_50": "same-timestamp update burst; quote-stuffing candidate feature only",
        },
        "decision": decision,
    }
    report_path = OUT_DIR / "tardis_l2_signature_probe.json"
    report_md = OUT_DIR / "tardis_l2_signature_probe.md"
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    report_md.write_text(
        "# Tardis L2 Signature Probe\n\n"
        f"Run id: `{LOOP_ID}`\n\n"
        f"Sampled {len(accessible)} direct L2/order-book public sources across exchanges: {', '.join(exchanges)}.\n\n"
        "Declared signatures are cancellation/imbalance/spread-shock context features only. "
        "They are not accepted manipulation labels without event confirmation or labeled manipulation targets.\n\n"
        f"Decision: `{decision['accepted_gate']}`. Blocker: {decision['blocker']}\n",
        encoding="utf-8",
    )
    (CHECKS_DIR / "tardis_l2_signature_probe_assertions.out").write_text(
        "\n".join(
            [
                f"report: {repo_rel(report_path)}",
                f"report_md: {repo_rel(report_md)}",
                f"direct_l2_sources_sampled: {decision['direct_l2_sources_sampled']}",
                "signature_probe_completed: True",
                "qualifying_direct_manipulation_input_sets: 0",
                f"manipulation_input_state: {decision['manipulation_input_state']}",
                "thresholds_relaxed: False",
                "runtime_code_changed: False",
                "fresh_calibration_rerun: False",
                "trade_usable: False",
                "GATE blocked_signature_probe_only",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (RUN_ROOT / "README.md").write_text(
        "# Tardis L2 Signature Probe\n\n"
        "Streams bounded public Tardis first-day direct L2/order-book samples and keeps only derived metadata/signature summaries.\n",
        encoding="utf-8",
    )
    print(json.dumps(decision, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
