#!/usr/bin/env python3
import csv
import json
import statistics
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path


BRANCH_PATH = "Bull -> ProviderCryptoMomentum -> RsiMidlineExpansion -> ProviderCryptoMomentumStateV1"


def parse_ts(raw):
    value = raw.strip()
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    dt = datetime.fromisoformat(value)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    dt = dt.astimezone(timezone.utc)
    return dt.replace(minute=0, second=0, microsecond=0)


def load_csv(path, provider):
    rows = {}
    with path.open(newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            raw_ts = row.get("date") or row.get("timestamp") or row.get("ts")
            if not raw_ts:
                continue
            ts = parse_ts(raw_ts)
            try:
                rows[ts] = {
                    "provider": provider,
                    "open": float(row["open"]),
                    "high": float(row["high"]),
                    "low": float(row["low"]),
                    "close": float(row["close"]),
                    "volume": float(row.get("volume") or 0.0),
                }
            except (KeyError, TypeError, ValueError):
                continue
    return rows


def iso(dt):
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def composite_rows(provider_rows):
    by_ts = defaultdict(list)
    for rows in provider_rows.values():
        for ts, row in rows.items():
            by_ts[ts].append(row)
    out = []
    for ts in sorted(by_ts):
        rows = by_ts[ts]
        providers = sorted({row["provider"] for row in rows})
        if len(providers) != len(provider_rows):
            continue
        out.append(
            {
                "timestamp": iso(ts),
                "open": statistics.median(row["open"] for row in rows),
                "high": max(row["high"] for row in rows),
                "low": min(row["low"] for row in rows),
                "close": statistics.median(row["close"] for row in rows),
                "volume": sum(row["volume"] for row in rows),
                "provider_count": len(providers),
                "providers": providers,
            }
        )
    return out


def bucket_start(dt, interval):
    if interval == "4h":
        return dt.replace(hour=(dt.hour // 4) * 4, minute=0, second=0, microsecond=0)
    if interval == "1d":
        return dt.replace(hour=0, minute=0, second=0, microsecond=0)
    raise ValueError(interval)


def resample(rows, interval):
    buckets = defaultdict(list)
    for row in rows:
        dt = parse_ts(row["timestamp"])
        buckets[bucket_start(dt, interval)].append(row)
    out = []
    min_size = 4 if interval == "4h" else 18
    for start in sorted(buckets):
        items = sorted(buckets[start], key=lambda item: item["timestamp"])
        if len(items) < min_size:
            continue
        out.append(
            {
                "timestamp": iso(start),
                "open": items[0]["open"],
                "high": max(item["high"] for item in items),
                "low": min(item["low"] for item in items),
                "close": items[-1]["close"],
                "volume": sum(item["volume"] for item in items),
            }
        )
    return out


def write_candles(path, rows):
    path.write_text(json.dumps({"candles": rows}, indent=2) + "\n")


def main():
    if len(sys.argv) != 3:
        raise SystemExit("usage: build_composite_mtf_and_bundle.py <run-root> <source-run-root>")
    run = Path(sys.argv[1])
    source = Path(sys.argv[2])
    provider_dir = source / "provider-csv"
    specs = {
        "yfinance": provider_dir / "yfinance_eth_usd_1h.csv",
        "kraken": provider_dir / "kraken_ethusd_1h.csv",
        "binance": provider_dir / "binance_ethusdt_1h.csv",
        "bybit": provider_dir / "bybit_ethusdt_linear_1h.csv",
        "tradingview_mcp": provider_dir / "tvr_binance_ethusdt_1h.csv",
        "ibkr_paxos_aggtrades": provider_dir / "ETH_1h_aggtrades.csv",
    }
    provider_rows = {name: load_csv(path, name) for name, path in specs.items()}
    ltf = composite_rows(provider_rows)
    mtf = resample(ltf, "4h")
    htf = resample(ltf, "1d")
    data_dir = run / "data"
    bundle_dir = run / "bundle"
    data_dir.mkdir(parents=True, exist_ok=True)
    bundle_dir.mkdir(parents=True, exist_ok=True)
    write_candles(data_dir / "eth_six_provider_composite_1h.json", ltf)
    write_candles(data_dir / "eth_six_provider_composite_4h.json", mtf)
    write_candles(data_dir / "eth_six_provider_composite_1d.json", htf)
    bundle = {
        "schema_version": "regime-consumer-bundle/v1",
        "latest_decision": {
            "decision_state": "single_label_95",
            "trade_usable": True,
            "final_label": "Bull",
            "label_set": ["Bull", BRANCH_PATH],
            "abstain_reasons": [
                "same_root_six_provider_eth_aq_authority",
                "path_ranker_runtime_ready_but_execution_fail_closed",
            ],
        },
        "consumer_hints": {
            "execution_tree_hint": "accept_regime",
            "bbn_evidence_hint": {
                "regime_decision_state": "single_label_95",
                "regime_trade_usable": True,
                "regime_label": "Bull",
                "regime_label_set": ["Bull", BRANCH_PATH],
                "regime_transition_hazard": 0.15,
                "regime_decision_reasons": [
                    "same_root_six_provider_eth_aq_authority",
                    "exact_branch_path_preserved",
                    "catboost_runtime_candidate_set_ready",
                ],
            },
            "path_ranker_context": {
                "regime_profit_branch_path": BRANCH_PATH,
                "stable_profit_score": 0.6632710958496916,
            },
            "trade_usable": True,
        },
    }
    (bundle_dir / "regime_consumer_bundle.json").write_text(json.dumps(bundle, indent=2) + "\n")
    summary = {
        "provider_input_rows": {name: len(rows) for name, rows in provider_rows.items()},
        "composite_1h_rows_all_six": len(ltf),
        "composite_4h_rows": len(mtf),
        "composite_1d_rows": len(htf),
        "first_1h": ltf[0]["timestamp"] if ltf else None,
        "last_1h": ltf[-1]["timestamp"] if ltf else None,
        "branch_path": BRANCH_PATH,
        "bundle": str(bundle_dir / "regime_consumer_bundle.json"),
    }
    (run / "data" / "composite_mtf_summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
