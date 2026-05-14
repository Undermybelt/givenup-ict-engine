#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path


ROOT = Path("docs/experiments/actionable-regime-confidence/runs/20260512T191916+0800-codex-ote-four-leaf-branch-keyed-aq-v1")
SOURCE_ROOT = Path("docs/experiments/actionable-regime-confidence/runs/20260512T184332+0800-codex-session-liquidity-vwap-opening-range-six-provider-aq-v1")
STRATEGY = ROOT / "agent-material" / "OtePullbackContinuationLongV1.py"

LEVELS = [
    ("0500", "ote_retrace_0500", "ote_retrace_0500_continuation_v1"),
    ("0618", "ote_retrace_0618", "ote_retrace_0618_continuation_v1"),
    ("0705", "ote_retrace_0705", "ote_retrace_0705_continuation_v1"),
    ("0786", "ote_retrace_0786", "ote_retrace_0786_continuation_v1"),
]

PROVIDERS = [
    ("yfinance/YF", "yfinance-yf", "SPY", "SPY", "yahoo_spy_1h.normalized.csv", "session-liquidity-yfinance-yf-1h-v1.material.json"),
    ("Binance", "binance", "BTCUSDT", "BTCUSDT", "binance_btcusdt_1h.normalized.csv", "session-liquidity-binance-1h-v1.material.json"),
    ("Bybit", "bybit", "BTCUSDT", "BTCUSDT", "bybit_linear_btcusdt_1h.normalized.csv", "session-liquidity-bybit-1h-v1.material.json"),
    ("Kraken", "kraken", "XBTUSD", "XBTUSD", "kraken_futures_pfxbtusd_1h.normalized.csv", "session-liquidity-kraken-1h-v1.material.json"),
    ("IBKR", "ibkr", "SPY", "SPY", "ibkr_spy_1h_90d.normalized.csv", "session-liquidity-ibkr-1h-v1.material.json"),
    ("TradingViewRemix/TVR", "tvr-btc-usd", "BTCUSD", "BTC-USD", "tvr_btc_usd_1h.normalized.csv", "session-liquidity-tvr-btc-usd-1h-v1.material.json"),
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


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    for rel in ["agent-material", "checks", "manifests", "summaries"]:
        (ROOT / rel).mkdir(parents=True, exist_ok=True)

    materials: list[Path] = []
    provenance_rows: list[dict[str, object]] = []
    branch_rows: list[dict[str, object]] = []
    manifest_rows: list[dict[str, object]] = []

    for provider, provider_slug, symbol, provider_symbol, data_name, source_name in PROVIDERS:
        data_path = SOURCE_ROOT / "data" / "normalized" / data_name
        source_material = SOURCE_ROOT / "agent-material" / source_name
        if not data_path.exists():
            raise SystemExit(f"missing data_path: {data_path}")
        if not source_material.exists():
            raise SystemExit(f"missing source_material: {source_material}")

        source = json.loads(source_material.read_text())
        timerange = source.get("timerange", "20250101-20260512")
        row_count = csv_rows(data_path)
        data_hash = sha256(data_path)
        source_hash = sha256(source_material)

        for level_value, branch_leaf, profit_factor in LEVELS:
            branch_path = f"TrendExpansion -> PullbackContinuation -> {branch_leaf} -> {profit_factor}"
            package_id = f"ote-{level_value}-pullback-{provider_slug}-1h-v1"
            material_path = ROOT / "agent-material" / f"{package_id}.material.json"
            material = {
                "package_id": package_id,
                "title": f"OTE {level_value} pullback continuation - {provider} {provider_symbol} 1h",
                "symbol": symbol,
                "timeframe": "1h",
                "timerange": timerange,
                "direction": "long",
                "data_path": str(data_path),
                "strategy_source_path": str(STRATEGY),
                "strategy_class_name": "OtePullbackContinuationLongV1",
                "strategy_brief": "Board B branch-keyed OTE pullback-continuation profitability factor replay.",
                "consumer_evidence_profile": {
                    "branch_paths": [branch_path],
                    "branch_path": branch_path,
                    "main_regime": "TrendExpansion",
                    "sub_regime": "PullbackContinuation",
                    "sub_sub_regime_or_profit_factor": branch_leaf,
                    "profit_factor": profit_factor,
                    "ote_level": level_value,
                    "promotion_allowed": False,
                    "branch_keyed_by_construction": True,
                    "provider": provider,
                    "provider_symbol": provider_symbol,
                    "local_cache_replay": True,
                    "new_provider_fetch": False,
                    "source_root": str(SOURCE_ROOT),
                    "source_material": str(source_material),
                },
                "evaluation_priority": [
                    "per_leaf_trade_density",
                    "regime_conditioned_win_rate",
                    "payoff_ratio",
                    "profit_factor",
                    "max_drawdown",
                    "cross_provider_survival",
                    "sample_adequacy",
                ],
                "negative_evidence_contract": {
                    "loss_after_full_chain": "market_factor_negative_sample",
                    "missing_branch_fields": "chain_contract_negative_sample",
                    "provider_or_fetch_fault": "infrastructure_negative_sample",
                    "low_trade_density": "low_density_negative_sample",
                    "provider_disagreement": "cross_provider_disagreement_sample",
                },
                "notes": [
                    f"source_provider={provider}",
                    f"source_root={SOURCE_ROOT}",
                    f"source_material={source_material}",
                    f"branch_path={branch_path}",
                    f"ote_level={level_value}",
                    "local_cache_replay=true",
                    "new_provider_fetch=false",
                    "promotion_allowed=false until AQ dispatch/rank and ordered downstream chain pass",
                ],
            }
            material_path.write_text(json.dumps(material, indent=2, sort_keys=True) + "\n")
            materials.append(material_path)

            row = {
                "package_id": package_id,
                "provider": provider,
                "symbol": symbol,
                "provider_symbol": provider_symbol,
                "timeframe": "1h",
                "branch_path": branch_path,
                "main_regime": "TrendExpansion",
                "sub_regime": "PullbackContinuation",
                "sub_sub_regime_or_profit_factor": branch_leaf,
                "profit_factor": profit_factor,
                "ote_level": level_value,
                "data_path": str(data_path),
                "data_rows": row_count,
                "data_sha256": data_hash,
                "source_material": str(source_material),
                "source_material_sha256": source_hash,
                "provider_requested": "false",
                "provider_data_acquired": "false",
                "aq_provider_invoked": "false",
                "local_cache_replay": "true",
                "new_provider_fetch": "false",
                "provider_authority_state": "replay_from_184332_provider_preflight",
            }
            provenance_rows.append(row)
            branch_rows.append(
                {
                    "branch_path": branch_path,
                    "provider": provider,
                    "package_id": package_id,
                    "material_path": str(material_path),
                }
            )
            manifest_rows.append({"path": str(material_path), "sha256": sha256(material_path)})

        manifest_rows.append({"path": str(data_path), "sha256": data_hash})
        manifest_rows.append({"path": str(source_material), "sha256": source_hash})

    material_paths = ROOT / "summaries" / "material_paths.csv"
    with material_paths.open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["material"])
        for path in materials:
            writer.writerow([path])

    write_csv(
        ROOT / "summaries" / "provider_provenance_matrix.csv",
        provenance_rows,
        list(provenance_rows[0].keys()),
    )
    write_csv(
        ROOT / "summaries" / "branch_material_matrix.csv",
        branch_rows,
        ["branch_path", "provider", "package_id", "material_path"],
    )
    write_csv(ROOT / "manifests" / "sha256_manifest.csv", manifest_rows, ["path", "sha256"])

    branch_paths = sorted({row["branch_path"] for row in provenance_rows})
    providers = sorted({row["provider"] for row in provenance_rows})
    assertions = {
        "material_count": len(materials),
        "provider_count": len(providers),
        "branch_leaf_count": len(branch_paths),
        "branch_paths": branch_paths,
        "branch_keyed_by_construction": all(
            json.loads(path.read_text())["consumer_evidence_profile"]["branch_paths"]
            == [json.loads(path.read_text())["consumer_evidence_profile"]["branch_path"]]
            for path in materials
        ),
        "local_cache_replay": all(row["local_cache_replay"] == "true" for row in provenance_rows),
        "new_provider_fetch": False,
        "promotion_allowed": False,
        "trade_usable": False,
        "update_goal": False,
    }
    (ROOT / "summaries" / "ote_four_leaf_material_summary_v1.json").write_text(
        json.dumps(assertions, indent=2, sort_keys=True) + "\n"
    )
    (ROOT / "checks" / "ote_four_leaf_material_assertions.out").write_text(
        "\n".join(f"{key}={value}" for key, value in assertions.items()) + "\n"
    )

    ok = (
        assertions["material_count"] == 24
        and assertions["provider_count"] == 6
        and assertions["branch_leaf_count"] == 4
        and assertions["branch_keyed_by_construction"]
        and assertions["local_cache_replay"]
    )
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
