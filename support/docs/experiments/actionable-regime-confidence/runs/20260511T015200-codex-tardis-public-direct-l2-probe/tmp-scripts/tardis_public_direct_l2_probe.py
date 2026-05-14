from __future__ import annotations

import csv
import gzip
import json
import math
import subprocess
from io import TextIOWrapper
from pathlib import Path
from statistics import mean
from typing import Any


REPO = Path("/Users/thrill3r/projects-ict-engine/ict-engine")
RUN_ROOT = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T015200-codex-tardis-public-direct-l2-probe"
)
OUT_DIR = RUN_ROOT / "direct-l2"
CHECKS_DIR = RUN_ROOT / "checks"
LOOP_ID = "20260511T015200+0800-codex-tardis-public-direct-l2-probe"

SOURCES = [
    {
        "name": "bitmex_xbtusd_book_snapshot_5_2020_09_01",
        "exchange": "bitmex",
        "symbol": "XBTUSD",
        "data_type": "book_snapshot_5",
        "url": "https://datasets.tardis.dev/v1/bitmex/book_snapshot_5/2020/09/01/XBTUSD.csv.gz",
        "row_limit": 50000,
    },
    {
        "name": "binance_futures_btcusdt_book_snapshot_5_2020_09_01",
        "exchange": "binance-futures",
        "symbol": "BTCUSDT",
        "data_type": "book_snapshot_5",
        "url": "https://datasets.tardis.dev/v1/binance-futures/book_snapshot_5/2020/09/01/BTCUSDT.csv.gz",
        "row_limit": 50000,
    },
    {
        "name": "deribit_btc_perpetual_incremental_book_l2_2020_04_01",
        "exchange": "deribit",
        "symbol": "BTC-PERPETUAL",
        "data_type": "incremental_book_L2",
        "url": "https://datasets.tardis.dev/v1/deribit/incremental_book_L2/2020/04/01/BTC-PERPETUAL.csv.gz",
        "row_limit": 80000,
    },
]


def repo_rel(path: Path) -> str:
    return str(path.relative_to(REPO))


def as_float(value: Any) -> float | None:
    try:
        out = float(value)
    except (TypeError, ValueError):
        return None
    return out if math.isfinite(out) else None


def probe_source(source: dict[str, Any]) -> dict[str, Any]:
    proc = subprocess.Popen(
        ["curl", "-L", "--silent", "--show-error", "--max-time", "45", source["url"]],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    assert proc.stdout is not None
    gzip_file = gzip.GzipFile(fileobj=proc.stdout)
    text = TextIOWrapper(gzip_file, encoding="utf-8", newline="")
    reader = csv.DictReader(text)
    rows = 0
    first_timestamp: str | None = None
    last_timestamp: str | None = None
    spreads: list[float] = []
    imbalance: list[float] = []
    side_counts: dict[str, int] = {}
    zero_amount_updates = 0
    snapshot_rows = 0
    sample_rows: list[dict[str, str]] = []

    try:
        for row in reader:
            rows += 1
            if rows <= 3:
                sample_rows.append(dict(row))
            if first_timestamp is None:
                first_timestamp = row.get("timestamp")
            last_timestamp = row.get("timestamp")
            if row.get("is_snapshot", "").lower() == "true":
                snapshot_rows += 1
            side = row.get("side")
            if side:
                side_counts[side] = side_counts.get(side, 0) + 1
            amount = as_float(row.get("amount"))
            if amount == 0.0:
                zero_amount_updates += 1
            ask0 = as_float(row.get("asks[0].price"))
            bid0 = as_float(row.get("bids[0].price"))
            ask_amt = as_float(row.get("asks[0].amount"))
            bid_amt = as_float(row.get("bids[0].amount"))
            if ask0 is not None and bid0 is not None and ask0 >= bid0:
                spreads.append(ask0 - bid0)
            if ask_amt is not None and bid_amt is not None and (ask_amt + bid_amt) > 0:
                imbalance.append((bid_amt - ask_amt) / (bid_amt + ask_amt))
            if rows >= int(source["row_limit"]):
                break
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            proc.kill()
        stderr = proc.stderr.read().decode("utf-8", errors="replace") if proc.stderr is not None else ""

    header = reader.fieldnames or []
    direct_fields = []
    if any(column.startswith("asks[") or column.startswith("bids[") for column in header):
        direct_fields.append("top_book_levels")
    if {"side", "price", "amount"}.issubset(set(header)):
        direct_fields.append("l2_update_side_price_amount")
    if "is_snapshot" in header:
        direct_fields.append("snapshot_flag")
    return {
        **source,
        "download_probe_status": "sampled" if rows > 0 else "no_rows",
        "rows_sampled": rows,
        "first_timestamp": first_timestamp,
        "last_timestamp": last_timestamp,
        "headers": header,
        "direct_fields": direct_fields,
        "snapshot_rows": snapshot_rows,
        "side_counts": side_counts,
        "zero_amount_updates": zero_amount_updates,
        "spread_stats": {
            "count": len(spreads),
            "mean": mean(spreads) if spreads else None,
            "min": min(spreads) if spreads else None,
            "max": max(spreads) if spreads else None,
        },
        "top_level_imbalance_mean": mean(imbalance) if imbalance else None,
        "sample_rows": sample_rows,
        "stderr_tail": stderr[-500:],
    }


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECKS_DIR.mkdir(parents=True, exist_ok=True)
    sources = [probe_source(source) for source in SOURCES]
    accessible = [source for source in sources if source["rows_sampled"] > 0 and source["direct_fields"]]
    result = {
        "schema_version": "tardis-public-direct-l2-probe/v1",
        "loop_id": LOOP_ID,
        "run_root": repo_rel(RUN_ROOT),
        "source_doc": "https://docs.tardis.dev/downloadable-csv-files/overview.md",
        "data_types_doc": "https://docs.tardis.dev/downloadable-csv-files/data-types.md",
        "sources": sources,
        "decision": {
            "public_tardis_direct_l2_accessible": len(accessible) >= 2,
            "accessible_direct_sources": [source["name"] for source in accessible],
            "manipulation_input_state": "direct_l2_accessible_but_unlabeled_not_calibration_grade",
            "qualifying_direct_manipulation_input_sets": 0,
            "accepted_gate": "blocked_direct_l2_probe_only",
            "thresholds_relaxed": False,
            "runtime_code_changed": False,
            "fresh_calibration_rerun": False,
            "trade_usable": False,
            "blocker": "Public Tardis first-day data provides direct L2/order-book inputs, but this probe is unlabeled, partial, and not yet a multi-period manipulation calibration set.",
            "next_action": "Stream bounded Tardis first-day direct L2 samples across multiple months/exchanges into run-local derived features, then test only explicitly declared spoofing/layering signatures; keep Manipulation fail-closed without labeled/event confirmation.",
        },
    }
    report_path = OUT_DIR / "tardis_public_direct_l2_probe.json"
    report_md = OUT_DIR / "tardis_public_direct_l2_probe.md"
    report_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    report_md.write_text(
        "# Tardis Public Direct L2 Probe\n\n"
        f"Run id: `{LOOP_ID}`\n\n"
        "Tardis documentation says first-day-of-month historical CSV datasets can be downloaded without an API key. "
        "This probe sampled public direct order-book URLs without saving full raw datasets into the repo.\n\n"
        f"Accessible direct sources: {', '.join(result['decision']['accessible_direct_sources']) or 'none'}.\n\n"
        f"Decision: `{result['decision']['accepted_gate']}`. "
        f"Manipulation input state: `{result['decision']['manipulation_input_state']}`. "
        f"Blocker: {result['decision']['blocker']}\n",
        encoding="utf-8",
    )
    (CHECKS_DIR / "tardis_public_direct_l2_probe_assertions.out").write_text(
        "\n".join(
            [
                f"report: {repo_rel(report_path)}",
                f"report_md: {repo_rel(report_md)}",
                f"public_tardis_direct_l2_accessible: {result['decision']['public_tardis_direct_l2_accessible']}",
                "qualifying_direct_manipulation_input_sets: 0",
                f"manipulation_input_state: {result['decision']['manipulation_input_state']}",
                "thresholds_relaxed: False",
                "runtime_code_changed: False",
                "fresh_calibration_rerun: False",
                "trade_usable: False",
                "GATE blocked_direct_l2_probe_only",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (RUN_ROOT / "README.md").write_text(
        "# Tardis Public Direct L2 Probe\n\n"
        "Probe-only run for public Tardis first-day direct L2/order-book datasets. "
        "No full raw data is committed; only small metadata/sample summaries are kept.\n",
        encoding="utf-8",
    )
    print(json.dumps(result["decision"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
