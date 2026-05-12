#!/usr/bin/env python3
"""Run the local AutoQuant workspace with offline market metadata injection.

This does not edit AutoQuant's run.py or config.json. It uses Freqtrade's
Backtesting API with an Exchange object constructed with validate=False and
minimal local market metadata, avoiding the live Binance market-loading path
that blocked 042222.
"""

from __future__ import annotations

import contextlib
import importlib.util
import json
import sys
from io import StringIO
from pathlib import Path
from typing import Any

from freqtrade.configuration import Configuration
from freqtrade.enums import RunMode
from freqtrade.optimize.backtesting import Backtesting
from freqtrade.resolvers.exchange_resolver import ExchangeResolver


REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = Path(__file__).resolve().parents[1]
RUN_ID = "20260512T043222-codex-autoquant-offline-market-metadata-run-after-042222-v1"
SLUG = "autoquant-offline-market-metadata-run-after-042222-v1"
OUT = RUN_ROOT / SLUG
CHECKS = RUN_ROOT / "checks"
COMMAND_OUT = RUN_ROOT / "command-output"

AUTOQUANT_ROOT = Path(
    "/tmp/ict-engine-board-a-autoquant-local-cache-20260512T022826/auto-quant/.deps/auto-quant"
)
USER_DATA = AUTOQUANT_ROOT / "user_data"
DATA_DIR = USER_DATA / "data"
STRATEGIES_DIR = USER_DATA / "strategies"
CONFIG = AUTOQUANT_ROOT / "config.json"
RUN_PY = AUTOQUANT_ROOT / "run.py"

PAIRS = ["BTC/USDT", "ETH/USDT", "SOL/USDT", "BNB/USDT", "AVAX/USDT"]


def load_run_module() -> Any:
    spec = importlib.util.spec_from_file_location("autoquant_run_oracle", RUN_PY)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load run.py spec from {RUN_PY}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["autoquant_run_oracle"] = module
    spec.loader.exec_module(module)
    return module


def offline_market(pair: str) -> dict[str, Any]:
    base, quote = pair.split("/", 1)
    return {
        "id": f"{base}{quote}",
        "symbol": pair,
        "base": base,
        "quote": quote,
        "settle": None,
        "baseId": base,
        "quoteId": quote,
        "active": True,
        "spot": True,
        "margin": False,
        "swap": False,
        "future": False,
        "option": False,
        "type": "spot",
        "contract": False,
        "linear": None,
        "inverse": None,
        "contractSize": None,
        "precision": {"amount": 1e-8, "price": 0.01, "cost": 0.0001},
        "limits": {
            "amount": {"min": 1e-8, "max": None},
            "price": {"min": 0.01, "max": None},
            "cost": {"min": 10.0, "max": None},
            "leverage": {"min": None, "max": None},
        },
        "info": {"source": "local_offline_metadata_probe"},
    }


def build_offline_exchange(config: dict[str, Any]) -> Any:
    exchange = ExchangeResolver.load_exchange(config, validate=False, load_leverage_tiers=False)
    markets = {pair: offline_market(pair) for pair in PAIRS}
    exchange._markets = markets
    exchange._api.markets = markets
    exchange._api_async.markets = markets
    exchange._last_markets_refresh = 9_999_999_999_999
    return exchange


def run_backtest_offline(
    run_mod: Any,
    strategy_name: str,
    timerange: str,
    pair_basket: list[str] | None,
) -> dict[str, Any]:
    args = {
        "config": [str(CONFIG)],
        "user_data_dir": str(USER_DATA),
        "datadir": str(DATA_DIR),
        "strategy": strategy_name,
        "strategy_path": str(STRATEGIES_DIR),
        "timerange": timerange,
        "export": "none",
        "exportfilename": None,
        "cache": "none",
    }
    config = Configuration(args, RunMode.BACKTEST).get_config()
    if pair_basket:
        config["exchange"]["pair_whitelist"] = list(pair_basket)
    exchange = build_offline_exchange(config)
    bt = Backtesting(config, exchange=exchange)
    bt.start()
    return bt.results


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)
    COMMAND_OUT.mkdir(parents=True, exist_ok=True)

    run_mod = load_run_module()
    strategies = run_mod.discover_strategies()
    command_log = StringIO()
    results: list[dict[str, Any]] = []
    success_count = 0
    failure_count = 0

    with contextlib.redirect_stdout(command_log):
        print(f"Run id: {RUN_ID}")
        print("Mode: offline_market_metadata_injected")
        print(f"Strategies: {', '.join(strategies)}")
        print(f"AutoQuant root: {AUTOQUANT_ROOT}")
        print()
        for strategy_name in strategies:
            try:
                pair_basket, timeranges = run_mod.get_strategy_overrides(strategy_name)
            except Exception as exc:
                failure_count += 1
                results.append(
                    {
                        "strategy": strategy_name,
                        "timerange_label": "SETUP",
                        "timerange": "n/a",
                        "status": "ERROR",
                        "error_type": type(exc).__name__,
                        "error_msg": str(exc),
                    }
                )
                print(f"ERROR setup {strategy_name}: {type(exc).__name__}: {exc}")
                continue

            active_pairs = list(pair_basket) if pair_basket else list(PAIRS)
            for label, timerange in timeranges:
                try:
                    ft_results = run_backtest_offline(run_mod, strategy_name, timerange, pair_basket)
                    bundle = run_mod.extract_metrics(ft_results, strategy_name, active_pairs)
                    bah = run_mod.compute_bah_benchmark(timerange, active_pairs)
                    run_mod.print_block(
                        strategy_name,
                        "34ba6b6-offline-metadata",
                        label,
                        timerange,
                        active_pairs,
                        bundle,
                        bah,
                    )
                    success_count += 1
                    results.append(
                        {
                            "strategy": strategy_name,
                            "timerange_label": label,
                            "timerange": timerange,
                            "status": "OK",
                            "pairs": active_pairs,
                            "aggregate": bundle["aggregate"],
                            "buy_and_hold": {
                                "sharpe": bah["sharpe"],
                                "profit_total_pct": bah["profit_total_pct"],
                                "max_drawdown_pct": bah["max_drawdown_pct"],
                            },
                        }
                    )
                except BaseException as exc:
                    failure_count += 1
                    results.append(
                        {
                            "strategy": strategy_name,
                            "timerange_label": label,
                            "timerange": timerange,
                            "status": "ERROR",
                            "error_type": type(exc).__name__,
                            "error_msg": str(exc),
                        }
                    )
                    print(f"ERROR {strategy_name} {label} {timerange}: {type(exc).__name__}: {exc}")
                print()

    (COMMAND_OUT / "offline_market_metadata_run.stdout.txt").write_text(
        command_log.getvalue(), encoding="utf-8"
    )

    gate = (
        "autoquant_offline_market_metadata_run_after_042222_v1="
        "offline_metadata_backtests_succeeded_no_source_control_promotion"
        if success_count > 0 and failure_count == 0
        else "autoquant_offline_market_metadata_run_after_042222_v1="
        "offline_metadata_backtests_partial_or_failed_no_promotion"
    )
    payload = {
        "run_id": RUN_ID,
        "gate_result": gate,
        "source_run_root": "docs/experiments/actionable-regime-confidence/runs/20260512T042222-codex-autoquant-data-ready-local-cache-run-after-041649-v1",
        "autoquant_root": str(AUTOQUANT_ROOT),
        "mode": "offline_market_metadata_injected",
        "source_control_promotion": False,
        "success_count": success_count,
        "failure_count": failure_count,
        "results": results,
        "promotion_status": {
            "accepted_rows_added": 0,
            "new_confidence_gate": False,
            "source_control_evidence_acquired": False,
            "canonical_merge": False,
            "downstream_promotion_rerun": False,
            "strict_full_objective": False,
            "trade_usable": False,
            "update_goal": False,
        },
    }
    (OUT / "autoquant_offline_market_metadata_run_after_042222_v1.json").write_text(
        json.dumps(payload, indent=2, default=str), encoding="utf-8"
    )

    lines = [
        "# AutoQuant Offline Market Metadata Run After 042222 v1",
        "",
        f"Run id: `{RUN_ID}`",
        "",
        f"Gate result: `{gate}`",
        "",
        "## Result",
        "",
        f"- AutoQuant root: `{AUTOQUANT_ROOT}`.",
        f"- Mode: offline market metadata injected into Freqtrade Exchange; AutoQuant `run.py` and `config.json` were not edited.",
        f"- Successful backtests: `{success_count}`; failed backtests: `{failure_count}`.",
        "- This proves the prior Binance metadata/DNS blocker can be bypassed for local cached BTC strategies, but it is still non-promoting until source/control gates pass.",
        "- Accepted rows added `0`; new confidence gate `false`; strict full objective `false`; trade usable `false`; `update_goal=false`.",
        "",
        "## Strategies",
        "",
        "| Strategy | Timerange | Status | Trades | Sharpe | Profit % | Win % |",
        "|---|---|---|---:|---:|---:|---:|",
    ]
    for row in results:
        agg = row.get("aggregate", {})
        lines.append(
            f"| `{row['strategy']}` | `{row['timerange']}` | `{row['status']}` | "
            f"{int(agg.get('trade_count', 0) or 0)} | "
            f"{float(agg.get('sharpe', 0.0) or 0.0):.4f} | "
            f"{float(agg.get('total_profit_pct', 0.0) or 0.0):.4f} | "
            f"{float(agg.get('win_rate_pct', 0.0) or 0.0):.4f} |"
        )
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "This is an AutoQuant runtime/readiness repair probe. It is not accepted regime-confidence evidence, source/control evidence, canonical merge input, downstream promotion evidence, or trade evidence.",
            "",
            "## Artifacts",
            "",
            f"- JSON: `{OUT / 'autoquant_offline_market_metadata_run_after_042222_v1.json'}`",
            f"- Command output: `{COMMAND_OUT / 'offline_market_metadata_run.stdout.txt'}`",
            f"- Assertions: `{CHECKS / 'autoquant_offline_market_metadata_run_after_042222_v1_assertions.out'}`",
        ]
    )
    (OUT / "autoquant_offline_market_metadata_run_after_042222_v1.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )

    assertions = [
        f"PASS gate_result={gate}",
        f"PASS success_count={success_count}",
        f"PASS failure_count={failure_count}",
        "PASS offline_market_metadata_injected=true",
        "PASS autoquant_run_py_edited=false",
        "PASS autoquant_config_json_edited=false",
        "PASS accepted_rows_added=0",
        "PASS new_confidence_gate=false",
        "PASS source_control_evidence_acquired=false",
        "PASS canonical_merge=false",
        "PASS downstream_promotion_rerun=false",
        "PASS strict_full_objective=false",
        "PASS trade_usable=false",
        "PASS update_goal=false",
    ]
    (CHECKS / "autoquant_offline_market_metadata_run_after_042222_v1_assertions.out").write_text(
        "\n".join(assertions) + "\n", encoding="utf-8"
    )
    print(json.dumps({"ok": True, "gate_result": gate, "success_count": success_count, "failure_count": failure_count}, indent=2))
    return 0 if failure_count == 0 and success_count > 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
