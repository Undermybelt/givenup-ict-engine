#!/usr/bin/env python3
"""Build run-local ict-engine downstream inputs for Board A 162400."""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKET = ROOT / "six-provider-btc-local-tvr-aq-packet-v1" / "six_provider_btc_local_tvr_aq_packet_v1.json"
OUT_LIBRARY = ROOT / "provider_btc_162400_strategy_library_v1.json"
OUT_CANDLES = ROOT / "data" / "cleaned" / "btc_usd_1h_yfinance_candles.json"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def metric_dict(raw: dict) -> dict:
    return {
        "sharpe": float(raw.get("sharpe", 0.0)),
        "sortino": float(raw.get("sortino", 0.0)),
        "calmar": float(raw.get("calmar", 0.0)),
        "total_profit_pct": float(raw.get("total_profit_pct", 0.0)),
        "max_drawdown_pct": float(raw.get("max_drawdown_pct", 0.0)),
        "trade_count": int(raw.get("trade_count", 0)),
        "win_rate_pct": float(raw.get("win_rate_pct", 0.0)),
        "profit_factor": float(raw.get("profit_factor", 0.0)),
    }


def strategy_file(provider: str, strategy: str) -> str:
    matches = sorted(
        (ROOT / "workspace").glob(
            f"same-root-repair-v2/auto-quant-112315-{provider}/user_data/strategies_external/{strategy}.py"
        )
    )
    return str(matches[0]) if matches else ""


def build_library() -> None:
    packet = json.loads(PACKET.read_text())
    strategies = []
    for result in packet["aq_results"]:
        provider = result["provider"]
        provider_symbol = result.get("provider_symbol", "BTC")
        rows = int(result.get("rows", 0))
        for strategy, metrics_payload in result["metrics"].items():
            aggregate = metric_dict(metrics_payload.get("aggregate", {}))
            mutation_id = f"162400_{provider}_{strategy}"
            strategies.append(
                {
                    "name": f"{strategy}_{provider}_162400",
                    "file_path": strategy_file(provider, strategy),
                    "metadata": {
                        "strategy": strategy,
                        "mutation_id": mutation_id,
                        "base_factor": "six_provider_btc_provider_aq",
                        "hypothesis": (
                            "Board A BTC 1h six-provider AQ evidence packet; "
                            "provider-backed downstream plumbing only, not acceptance."
                        ),
                        "paradigm": "provider_backed_crypto_regime_probe",
                        "expected_regime": "BoardA -> BTC -> six_provider_provider_aq_surface",
                        "factors_used": [
                            "provider_crypto_momentum",
                            "provider_crypto_pullback_reversion",
                            "six_provider_agreement",
                        ],
                        "parent": "BoardA_BTC_162400",
                        "asset_class": "crypto_cross_provider",
                        "status": "provider_backed_auto_quant_downstream_input",
                        "created": "2026-05-12T16:24:00+08:00",
                    },
                    "status": "ok",
                    "validation_metrics": aggregate,
                    "per_pair_metrics": {"BTC/USDT": aggregate},
                    "pairs": ["BTC/USDT"],
                    "timerange": f"provider_rows={rows};provider_symbol={provider_symbol}",
                    "commit": "",
                    "error": None,
                }
            )

    manifest = {
        "manifest_version": "1.0",
        "exported_at": utc_now(),
        "auto_quant_repo_url": "/Users/thrill3r/Auto-Quant",
        "auto_quant_pinned_ref": "",
        "config_path": str(PACKET),
        "timeframe": "1h",
        "log_path": str(ROOT / "six-provider-btc-local-tvr-aq-packet-v1" / "six_provider_btc_local_tvr_aq_packet_v1.md"),
        "strategies": strategies,
        "validation_errors": [],
    }
    OUT_LIBRARY.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")


def normalize_ts(raw: str) -> str:
    text = raw.strip()
    if text.endswith("+00:00"):
        text = text[:-6] + "Z"
    if " " in text and "T" not in text:
        text = text.replace(" ", "T")
    return text


def build_candles() -> None:
    src = ROOT / "provider-csv" / "yfinance_btc_usd_1h.csv"
    rows = []
    with src.open(newline="") as handle:
        for row in csv.DictReader(handle):
            rows.append(
                {
                    "timestamp": normalize_ts(row["date"]),
                    "open": float(row["open"]),
                    "high": float(row["high"]),
                    "low": float(row["low"]),
                    "close": float(row["close"]),
                    "volume": float(row.get("volume") or 0.0),
                }
            )
    OUT_CANDLES.parent.mkdir(parents=True, exist_ok=True)
    OUT_CANDLES.write_text(json.dumps(rows, indent=2) + "\n")


def main() -> int:
    build_library()
    build_candles()
    print(f"strategy_library={OUT_LIBRARY}")
    print(f"candles={OUT_CANDLES}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
