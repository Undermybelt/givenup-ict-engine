#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path


ROOT = Path("docs/experiments/actionable-regime-confidence/runs/20260512T190929+0800-codex-branch-leaf-vwap-reclaim-six-provider-aq-v1")
SOURCE_ROOT = Path("docs/experiments/actionable-regime-confidence/runs/20260512T184332+0800-codex-session-liquidity-vwap-opening-range-six-provider-aq-v1")
STRATEGY = ROOT / "agent-material" / "BranchLeafVwapReclaimLongV1.py"
BRANCH_PATH = "Sideways -> SessionLiquidityMeanReversion -> VWAPReclaim -> session_vwap_reclaim_long_v1"

PROVIDERS = [
    {
        "provider": "yfinance/YF",
        "package_id": "branch-leaf-vwap-reclaim-yfinance-yf-1h-v1",
        "title": "Branch leaf VWAP reclaim - yfinance/YF SPY 1h",
        "symbol": "SPY",
        "data_path": SOURCE_ROOT / "data/normalized/yahoo_spy_1h.normalized.csv",
        "source_material": SOURCE_ROOT / "agent-material/session-liquidity-yfinance-yf-1h-v1.material.json",
    },
    {
        "provider": "Binance",
        "package_id": "branch-leaf-vwap-reclaim-binance-1h-v1",
        "title": "Branch leaf VWAP reclaim - Binance BTCUSDT 1h",
        "symbol": "BTCUSDT",
        "data_path": SOURCE_ROOT / "data/normalized/binance_btcusdt_1h.normalized.csv",
        "source_material": SOURCE_ROOT / "agent-material/session-liquidity-binance-1h-v1.material.json",
    },
    {
        "provider": "Bybit",
        "package_id": "branch-leaf-vwap-reclaim-bybit-1h-v1",
        "title": "Branch leaf VWAP reclaim - Bybit BTCUSDT 1h",
        "symbol": "BTCUSDT",
        "data_path": SOURCE_ROOT / "data/normalized/bybit_linear_btcusdt_1h.normalized.csv",
        "source_material": SOURCE_ROOT / "agent-material/session-liquidity-bybit-1h-v1.material.json",
    },
    {
        "provider": "Kraken",
        "package_id": "branch-leaf-vwap-reclaim-kraken-1h-v1",
        "title": "Branch leaf VWAP reclaim - Kraken XBTUSD 1h",
        "symbol": "XBTUSD",
        "data_path": SOURCE_ROOT / "data/normalized/kraken_futures_pfxbtusd_1h.normalized.csv",
        "source_material": SOURCE_ROOT / "agent-material/session-liquidity-kraken-1h-v1.material.json",
    },
    {
        "provider": "IBKR",
        "package_id": "branch-leaf-vwap-reclaim-ibkr-1h-v1",
        "title": "Branch leaf VWAP reclaim - IBKR SPY 1h",
        "symbol": "SPY",
        "data_path": SOURCE_ROOT / "data/normalized/ibkr_spy_1h_90d.normalized.csv",
        "source_material": SOURCE_ROOT / "agent-material/session-liquidity-ibkr-1h-v1.material.json",
    },
    {
        "provider": "TradingViewRemix/TVR",
        "package_id": "branch-leaf-vwap-reclaim-tvr-btc-usd-1h-v1",
        "title": "Branch leaf VWAP reclaim - TradingViewRemix/TVR BTCUSD 1h",
        "symbol": "BTCUSD",
        "data_path": SOURCE_ROOT / "data/normalized/tvr_btc_usd_1h.normalized.csv",
        "source_material": SOURCE_ROOT / "agent-material/session-liquidity-tvr-btc-usd-1h-v1.material.json",
    },
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def csv_rows(path: Path) -> int:
    with path.open(newline="") as handle:
        reader = csv.reader(handle)
        next(reader, None)
        return sum(1 for _ in reader)


def main() -> int:
    for rel in ["agent-material", "checks", "manifests", "summaries"]:
        (ROOT / rel).mkdir(parents=True, exist_ok=True)

    materials = []
    provenance_rows = []
    manifest_rows = []

    for provider in PROVIDERS:
        data_path = provider["data_path"]
        source_material = provider["source_material"]
        if not data_path.exists():
            raise SystemExit(f"missing data_path: {data_path}")
        if not source_material.exists():
            raise SystemExit(f"missing source_material: {source_material}")

        source = json.loads(source_material.read_text())
        timerange = source.get("timerange", "20250101-20260512")
        package_id = provider["package_id"]
        material_path = ROOT / "agent-material" / f"{package_id}.material.json"
        material = {
            "package_id": package_id,
            "title": provider["title"],
            "symbol": provider["symbol"],
            "timeframe": "1h",
            "timerange": timerange,
            "direction": "long",
            "data_path": str(data_path),
            "strategy_source_path": str(STRATEGY),
            "strategy_class_name": "BranchLeafVwapReclaimLongV1",
            "strategy_brief": "Board B single branch-leaf VWAP reclaim profitability factor replay.",
            "consumer_evidence_profile": {
                "branch_paths": [BRANCH_PATH],
                "branch_path": BRANCH_PATH,
                "main_regime": "Sideways",
                "sub_regime": "SessionLiquidityMeanReversion",
                "sub_sub_regime_or_profit_factor": "VWAPReclaim",
                "profit_factor": "session_vwap_reclaim_long_v1",
                "promotion_allowed": False,
                "branch_keyed_by_construction": True,
                "provider": provider["provider"],
                "local_cache_replay": True,
                "source_root": str(SOURCE_ROOT),
                "source_material": str(source_material),
            },
            "evaluation_priority": [
                "branch_trade_density",
                "regime_conditioned_win_rate",
                "profit_factor",
                "walk_forward_survival",
                "sample_adequacy",
            ],
            "negative_evidence_contract": {
                "loss_after_full_chain": "market_factor_negative_sample",
                "missing_branch_fields": "chain_contract_negative_sample",
                "provider_or_fetch_fault": "infrastructure_negative_sample",
                "low_trade_density": "low_density_negative_sample",
            },
            "notes": [
                f"source_provider={provider['provider']}",
                f"source_root={SOURCE_ROOT}",
                f"source_material={source_material}",
                f"branch_path={BRANCH_PATH}",
                "local_cache_replay=true",
                "new_provider_fetch=false",
                "promotion_allowed=false until AQ dispatch/rank and ordered downstream chain pass",
            ],
        }
        material_path.write_text(json.dumps(material, indent=2, sort_keys=True) + "\n")
        materials.append(material_path)

        row = {
            "package_id": package_id,
            "provider": provider["provider"],
            "symbol": provider["symbol"],
            "timeframe": "1h",
            "branch_path": BRANCH_PATH,
            "main_regime": "Sideways",
            "sub_regime": "SessionLiquidityMeanReversion",
            "sub_sub_regime_or_profit_factor": "VWAPReclaim",
            "profit_factor": "session_vwap_reclaim_long_v1",
            "data_path": str(data_path),
            "data_rows": str(csv_rows(data_path)),
            "data_sha256": sha256(data_path),
            "source_material": str(source_material),
            "source_material_sha256": sha256(source_material),
            "local_cache_replay": "true",
            "new_provider_fetch": "false",
        }
        provenance_rows.append(row)
        manifest_rows.append({"path": str(material_path), "sha256": sha256(material_path)})
        manifest_rows.append({"path": str(data_path), "sha256": row["data_sha256"]})

    material_paths = ROOT / "summaries" / "material_paths.csv"
    with material_paths.open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["material"])
        for path in materials:
            writer.writerow([path])

    provenance_path = ROOT / "summaries" / "provider_provenance_matrix.csv"
    with provenance_path.open("w", newline="") as handle:
        fieldnames = list(provenance_rows[0].keys())
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(provenance_rows)

    manifest_path = ROOT / "manifests" / "sha256_manifest.csv"
    with manifest_path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["path", "sha256"])
        writer.writeheader()
        writer.writerows(manifest_rows)

    assertions = {
        "material_count": len(materials),
        "provider_count": len(provenance_rows),
        "branch_paths": sorted({row["branch_path"] for row in provenance_rows}),
        "branch_keyed_by_construction": all(
            json.loads(path.read_text())["consumer_evidence_profile"]["branch_paths"] == [BRANCH_PATH]
            for path in materials
        ),
        "local_cache_replay": all(row["local_cache_replay"] == "true" for row in provenance_rows),
        "new_provider_fetch": False,
        "promotion_allowed": False,
        "trade_usable": False,
        "update_goal": False,
    }
    (ROOT / "summaries" / "branch_leaf_material_summary_v1.json").write_text(
        json.dumps(assertions, indent=2, sort_keys=True) + "\n"
    )

    ok = (
        assertions["material_count"] == 6
        and assertions["provider_count"] == 6
        and assertions["branch_paths"] == [BRANCH_PATH]
        and assertions["branch_keyed_by_construction"]
    )
    (ROOT / "checks" / "branch_leaf_material_assertions.out").write_text(
        "\n".join(f"{key}={value}" for key, value in assertions.items()) + "\n"
    )
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
