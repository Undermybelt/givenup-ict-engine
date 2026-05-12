#!/usr/bin/env python3
"""Build a branch-keyed volatility-breakout packet from the settled 145809 screen."""

from __future__ import annotations

import csv
import json
import math
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path


RUN = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260512T150654+0800-codex-145809-volatility-breakout-aq-route-v1"
)
SOURCE_ROOT = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260512T145809+0800-codex-provider-backed-high-density-factor-screen-v1"
)
SOURCE_TRADES = SOURCE_ROOT / "summaries/provider_backed_high_density_factor_trades.csv"
SOURCE_MANIFEST = SOURCE_ROOT / "summaries/provider_backed_high_density_factor_manifest.json"

STRATEGY = "volatility_breakout_follow_v1"
BRANCH_PATH = "trend_expansion->high_volatility->up_momentum->volatility_breakout_follow"
SYMBOL = "B2R_VOL_BREAKOUT_150654"


def parse_dt(value: str) -> datetime:
    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def parse_ts_ms(value: str) -> int:
    return int(parse_dt(value).timestamp() * 1000)


def safe_float(value: str) -> float:
    try:
        val = float(value)
    except (TypeError, ValueError):
        return 0.0
    return val if math.isfinite(val) else 0.0


def profit_factor(values: list[float]) -> float:
    gross_win = sum(v for v in values if v > 0.0)
    gross_loss = abs(sum(v for v in values if v < 0.0))
    if gross_loss == 0.0:
        return float("inf") if gross_win > 0.0 else 0.0
    return gross_win / gross_loss


def summarize(values: list[float]) -> dict[str, float | int]:
    wins = sum(1 for v in values if v > 0.0)
    trades = len(values)
    return {
        "trades": trades,
        "wins": wins,
        "losses": trades - wins,
        "win_rate": wins / trades if trades else 0.0,
        "avg_return": sum(values) / trades if trades else 0.0,
        "total_return_units": sum(values),
        "profit_factor": profit_factor(values),
    }


def load_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    with SOURCE_TRADES.open(newline="") as fh:
        for row in csv.DictReader(fh):
            if row["strategy"] == STRATEGY and row["branch_path"] == BRANCH_PATH:
                rows.append(row)
    rows.sort(key=lambda row: parse_ts_ms(row["entry_time"]))
    return rows


def write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def build_manifest(rows: list[dict[str, str]], summary: dict[str, float | int]) -> dict:
    source_manifest = json.loads(SOURCE_MANIFEST.read_text())
    provider_counts = Counter(row["provider"] for row in rows)
    return {
        "manifest_version": "1.0",
        "exported_at": "2026-05-12T15:06:54+08:00",
        "auto_quant_repo_url": (
            "provider-backed volatility breakout packet derived from settled 145809 screen; "
            "not an Auto-Quant-native backtest yet"
        ),
        "auto_quant_pinned_ref": "screen-145809-volatility-breakout-150654",
        "config_path": str(SOURCE_MANIFEST),
        "timeframe": "1h_provider_backed",
        "log_path": str(RUN / "checks/volatility_breakout_packet_assertions.out"),
        "validation_errors": [
            {
                "file": str(SOURCE_TRADES),
                "error": "not_auto_quant_native_backtest",
            },
            {
                "file": str(RUN / "derived/aq_provider_provenance_volatility_breakout.csv"),
                "error": "missing_provider_data_rows_for_tvr_kraken_bybit",
            },
            {
                "file": str(RUN / "summaries/volatility_breakout_walkforward_summary.csv"),
                "error": "branch_seed_requires_walk_forward_and_downstream_readback",
            },
        ],
        "source_manifest": source_manifest,
        "strategies": [
            {
                "name": STRATEGY,
                "file_path": str(SOURCE_TRADES),
                "metadata": {
                    "strategy": STRATEGY,
                    "mutation_id": "150654_145809_volatility_breakout_follow_v1",
                    "base_factor": STRATEGY,
                    "hypothesis": (
                        "Trend-expansion plus high-volatility plus up-momentum continuation "
                        "can be a branch-local profit factor when provider-backed 1h data agrees."
                    ),
                    "paradigm": "provider_backed_branch_factor_seed",
                    "expected_regime": "trend_expansion",
                    "regime_profit_branch_path": BRANCH_PATH,
                    "factors_used": [STRATEGY, "high_volatility", "up_momentum"],
                    "parent": "145809_provider_backed_high_density_factor_screen_v1",
                    "asset_class": "multi_asset_provider_backed",
                    "provider_counts": dict(provider_counts),
                    "status": "support_only_branch_seed_not_auto_quant_native_backtest",
                },
                "status": "ok",
                "validation_metrics": {
                    "sharpe": 0.0,
                    "sortino": 0.0,
                    "calmar": 0.0,
                    "total_profit_pct": float(summary["total_return_units"]) * 100.0,
                    "max_drawdown_pct": 0.0,
                    "trade_count": int(summary["trades"]),
                    "win_rate_pct": float(summary["win_rate"]) * 100.0,
                    "profit_factor": float(summary["profit_factor"]),
                    "avg_return": float(summary["avg_return"]),
                },
                "per_pair_metrics": {
                    "PROVIDER_BACKED/VOL_BREAKOUT": {
                        "trade_count": int(summary["trades"]),
                        "win_rate_pct": float(summary["win_rate"]) * 100.0,
                        "profit_factor": float(summary["profit_factor"]),
                        "total_profit_pct": float(summary["total_return_units"]) * 100.0,
                    }
                },
                "pairs": ["PROVIDER_BACKED/VOL_BREAKOUT"],
                "timerange": "2017-10-19 -> 2026-04-30",
                "commit": "provider-backed-screen-145809-volatility-breakout-150654",
            }
        ],
    }


def write_provider_matrix(rows: list[dict[str, str]]) -> None:
    observed = Counter(row["provider"] for row in rows)
    matrix = [
        ["IBKR", True, True, observed["ibkr"] > 0, False, False, "143900", observed["ibkr"], "SPY 1h 5Y rows present in this branch seed"],
        ["TradingViewRemix/TVR", False, False, False, True, False, "141554/150346", 0, "TVR was not acquired for 145809 branch rows"],
        ["yfinance/YF", True, True, observed["yahoo"] > 0, False, False, "143900", observed["yahoo"], "Yahoo ES 1h rows present in this branch seed"],
        ["Kraken", False, False, False, False, False, "141554", 0, "Kraken rows were not acquired for this branch seed"],
        ["Binance", True, True, observed["binance"] > 0, False, False, "143900", observed["binance"], "BTCUSDT 1h rows present in this branch seed"],
        ["Bybit", False, False, False, False, False, "141554", 0, "Bybit rows were not acquired for this branch seed"],
    ]
    with (RUN / "derived/aq_provider_provenance_volatility_breakout.csv").open("w", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(
            [
                "provider",
                "aq_provider_invoked",
                "provider_requested",
                "provider_data_acquired",
                "provider_unreachable",
                "local_cache_replay",
                "context_source",
                "branch_seed_rows",
                "note",
            ]
        )
        writer.writerows(matrix)


def write_walk_forward(rows: list[dict[str, str]]) -> list[dict[str, object]]:
    grouped: dict[str, list[float]] = defaultdict(list)
    for row in rows:
        grouped[str(parse_dt(row["entry_time"]).year)].append(safe_float(row["return"]))
    out_rows: list[dict[str, object]] = []
    with (RUN / "summaries/volatility_breakout_walkforward_summary.csv").open("w", newline="") as fh:
        fieldnames = [
            "fold",
            "trades",
            "win_rate",
            "profit_factor",
            "total_return_units",
            "fold_gate",
        ]
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for fold in sorted(grouped):
            summary = summarize(grouped[fold])
            gate = (
                "pass"
                if summary["trades"] >= 30
                and summary["win_rate"] >= 0.50
                and summary["profit_factor"] >= 1.05
                else "fail_closed"
            )
            record = {
                "fold": fold,
                "trades": summary["trades"],
                "win_rate": summary["win_rate"],
                "profit_factor": summary["profit_factor"],
                "total_return_units": summary["total_return_units"],
                "fold_gate": gate,
            }
            writer.writerow(record)
            out_rows.append(record)
    return out_rows


def write_real_trades(rows: list[dict[str, str]]) -> None:
    path = RUN / "derived/volatility_breakout_real_trades.jsonl"
    with path.open("w") as out:
        for idx, row in enumerate(rows, start=1):
            ret = safe_float(row["return"])
            direction = "Bull" if row["direction"].lower() == "long" else "Bear"
            payload = {
                "schema_version": "1.0",
                "symbol": SYMBOL,
                "provider": row["provider"],
                "trade_id": f"150654-vol-breakout-{idx:06d}",
                "strategy_name": STRATEGY,
                "strategy_mutation_id": "150654_145809_volatility_breakout_follow_v1",
                "auto_quant_run_id": "20260512T150654-volatility-breakout-provider-backed-branch-seed-v1",
                "open_ts_ms": parse_ts_ms(row["entry_time"]),
                "close_ts_ms": parse_ts_ms(row["exit_time"]),
                "direction": direction,
                "pnl": ret,
                "realized_outcome": "win" if ret > 0.0 else "loss",
                "regime_at_entry": row["main_regime"],
                "entry_signal": STRATEGY,
                "regime_profit_branch_path": BRANCH_PATH,
                "main_regime": row["main_regime"],
                "sub_regime": row["sub_regime"],
                "sub_sub_regime_or_profit_factor": row["sub_sub_regime_or_profit_factor"],
                "profit_factor": row["profit_factor"],
                "factors_used": [
                    {
                        "factor_name": STRATEGY,
                        "category": "provider_backed_volatility_breakout",
                        "direction": direction,
                        "value": ret,
                        "confidence": 0.55,
                        "weighted_score": ret,
                        "uncertainty_contribution": 0.45,
                    }
                ],
            }
            out.write(json.dumps(payload, separators=(",", ":")) + "\n")


def write_checklist(rows: list[dict[str, str]], folds: list[dict[str, object]], provider_rows_ok: bool) -> None:
    fold_passes = sum(1 for row in folds if row["fold_gate"] == "pass")
    items = [
        ("branch_path_present", bool(rows) and all(row["branch_path"] == BRANCH_PATH for row in rows), "all selected rows preserve exact branch path"),
        ("trade_count_ge_300", len(rows) >= 300, f"selected rows={len(rows)}"),
        ("six_provider_rows_emitted", provider_rows_ok, "provider matrix contains six required provider rows"),
        ("all_six_providers_acquired", False, "TVR/Kraken/Bybit absent from this 145809 seed"),
        ("walk_forward_any_pass", fold_passes > 0, f"passing folds={fold_passes}/{len(folds)}"),
        ("walk_forward_all_pass", fold_passes == len(folds), f"passing folds={fold_passes}/{len(folds)}"),
        ("auto_quant_native_backtest", False, "this packet is derived from provider-backed screen rows, not AQ-native backtest"),
        ("promotion_allowed", False, "screen/packet only"),
    ]
    with (RUN / "prompt_to_artifact_checklist_volatility_breakout_v1.csv").open("w", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["requirement", "status", "evidence"])
        for name, passed, evidence in items:
            writer.writerow([name, "pass" if passed else "fail_closed", evidence])
    with (RUN / "checks/volatility_breakout_packet_assertions.out").open("w") as fh:
        for name, passed, evidence in items:
            fh.write(f"{'pass' if passed else 'fail_closed'}:{name}:{evidence}\n")


def main() -> int:
    for rel in ["derived", "summaries", "checks", "command-output"]:
        (RUN / rel).mkdir(parents=True, exist_ok=True)
    rows = load_rows()
    returns = [safe_float(row["return"]) for row in rows]
    summary = summarize(returns)
    providers = Counter(row["provider"] for row in rows)
    symbols = Counter(row["symbol"] for row in rows)

    manifest = build_manifest(rows, summary)
    write_json(RUN / "derived/strategy_library_volatility_breakout_v1.json", manifest)
    write_provider_matrix(rows)
    folds = write_walk_forward(rows)
    write_real_trades(rows)

    packet = {
        "protocol": "150654-volatility-breakout-aq-route-packet-v1",
        "source_root": str(SOURCE_ROOT),
        "source_screen": "145809_provider_backed_high_density_factor_screen_v1",
        "strategy": STRATEGY,
        "symbol": SYMBOL,
        "branch_path": BRANCH_PATH,
        "main_regime": "trend_expansion",
        "sub_regime": "high_volatility",
        "sub_sub_regime_or_profit_factor": "up_momentum",
        "profit_factor_leaf": "volatility_breakout_follow",
        "summary": summary,
        "provider_counts": dict(providers),
        "symbol_counts": dict(symbols),
        "walk_forward_folds": folds,
        "provider_matrix": str(RUN / "derived/aq_provider_provenance_volatility_breakout.csv"),
        "strategy_library": str(RUN / "derived/strategy_library_volatility_breakout_v1.json"),
        "real_trades": str(RUN / "derived/volatility_breakout_real_trades.jsonl"),
        "promotion_allowed": False,
        "trade_usable": False,
        "update_goal": False,
    }
    write_json(RUN / "summaries/volatility_breakout_recipe_packet_v1.json", packet)
    write_checklist(rows, folds, True)
    print(json.dumps(packet, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
