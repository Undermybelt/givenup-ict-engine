#!/usr/bin/env python3
"""Run and summarize the additive RootAwareRegimeSwitch Auto-Quant recipe."""

from __future__ import annotations

import csv
import json
import os
from contextlib import redirect_stderr, redirect_stdout
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
from freqtrade.configuration import Configuration
from freqtrade.enums import RunMode
from freqtrade.optimize.backtesting import Backtesting


RUN_ID = "20260511T182138+0800-codex-board-b-rootaware-recipe-b2r-v1"
RECIPE_ID = "RootAwareRegimeSwitch"
PAIRS = ["BTC/USDT", "ETH/USDT", "SOL/USDT", "BNB/USDT", "AVAX/USDT"]
TIMERANGE = "20210101-20251231"
REQUIRED_ROOTS = ["Bull", "Bear", "Sideways", "Crisis", "Manipulation(scoped)"]


def find_repo_root(start: Path) -> Path:
    for candidate in [start, *start.parents]:
        if (candidate / "Cargo.toml").exists() and (candidate / "docs").exists():
            return candidate
    raise RuntimeError(f"cannot find repo root from {start}")


RUN_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = find_repo_root(Path(__file__).resolve())
OUT_DIR = RUN_ROOT / "rootaware-rc-spa"
CHECK_DIR = RUN_ROOT / "checks"
AUTO_QUANT_ROOT = Path(os.environ.get("AUTO_QUANT_ROOT", "/Users/thrill3r/Auto-Quant"))
AUTO_QUANT_CONFIG = AUTO_QUANT_ROOT / "config.json"
AUTO_QUANT_DATA = AUTO_QUANT_ROOT / "user_data" / "data"
AUTO_QUANT_USER_DATA = AUTO_QUANT_ROOT / "user_data"
STRATEGY_PATH = RUN_ROOT / "strategies"


def to_jsonable(value: Any) -> Any:
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    if hasattr(value, "isoformat"):
        try:
            return value.isoformat()
        except TypeError:
            pass
    return str(value)


def run_backtest() -> dict[str, Any]:
    args = {
        "config": [str(AUTO_QUANT_CONFIG)],
        "user_data_dir": str(AUTO_QUANT_USER_DATA),
        "datadir": str(AUTO_QUANT_DATA),
        "strategy": RECIPE_ID,
        "strategy_path": str(STRATEGY_PATH),
        "timerange": TIMERANGE,
        "export": "none",
        "exportfilename": None,
        "cache": "none",
    }
    config = Configuration(args, RunMode.BACKTEST).get_config()
    config["exchange"]["pair_whitelist"] = list(PAIRS)
    bt = Backtesting(config)
    bt.start()
    return bt.results


def metric(strategy_result: dict[str, Any], key: str, default: float = 0.0) -> float:
    value = strategy_result.get(key, default)
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def root_from_tag(tag: str) -> str:
    if tag.startswith("Bull->"):
        return "Bull"
    if tag.startswith("Bear->"):
        return "Bear"
    if tag.startswith("Sideways->"):
        return "Sideways"
    if tag.startswith("Crisis->"):
        return "Crisis"
    return "Unlabeled"


def summarize_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    summary = []
    for root in REQUIRED_ROOTS:
        if root == "Manipulation(scoped)":
            root_rows: list[dict[str, Any]] = []
            path = "Manipulation(scoped)->DirectEventOverlayMissing->no_direct_event_rows->suppress_or_abstain"
        else:
            root_rows = [r for r in rows if r["parent_regime_root"] == root]
            path = root_rows[0]["regime_profit_branch_path"] if root_rows else f"{root}->no_rows->no_rows->{RECIPE_ID}"
        profits = [float(r["profit_ratio_net"]) for r in root_rows]
        wins = sum(1 for p in profits if p > 0)
        years = sorted({r["year_fold"] for r in root_rows})
        summary.append(
            {
                "parent_regime_root": root,
                "regime_profit_branch_path": path,
                "total_trades": len(root_rows),
                "test_folds": len(years),
                "folds": ",".join(str(y) for y in years),
                "win_rate": wins / len(root_rows) if root_rows else 0.0,
                "mean_profit_ratio_net": sum(profits) / len(profits) if profits else 0.0,
                "sum_profit_ratio_net": sum(profits),
            }
        )
    return summary


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)
    stdout_path = CHECK_DIR / "rootaware_freqtrade_backtest.out"
    stderr_path = CHECK_DIR / "rootaware_freqtrade_backtest.err"
    with stdout_path.open("w", encoding="utf-8") as out, stderr_path.open("w", encoding="utf-8") as err:
        with redirect_stdout(out), redirect_stderr(err):
            results = run_backtest()

    strategy_result = results.get("strategy", {}).get(RECIPE_ID, {}) or {}
    trades = strategy_result.get("trades", []) or []
    trade_rows = []
    for idx, trade in enumerate(trades, start=1):
        tag = str(trade.get("enter_tag") or "")
        root = root_from_tag(tag)
        opened = pd.to_datetime(trade["open_date"], utc=True)
        trade_rows.append(
            {
                "row_id": idx,
                "recipe_id": RECIPE_ID,
                "pair": trade.get("pair", ""),
                "open_date": pd.Timestamp(opened).isoformat(),
                "close_date": to_jsonable(trade.get("close_date", "")),
                "parent_regime_root": root,
                "regime_profit_branch_path": tag or f"{root}->missing_tag->missing_tag->{RECIPE_ID}",
                "regime_profit_branch_path_version": "board-b-rootaware-recipe-b2r/v1",
                "manipulation_overlay_state": "not_consumed_no_direct_event_rows",
                "year_fold": int(pd.Timestamp(opened).year),
                "profit_ratio_net": float(trade.get("profit_ratio") or 0.0),
                "profit_abs": float(trade.get("profit_abs") or 0.0),
                "exit_reason": trade.get("exit_reason", ""),
            }
        )

    root_summary = summarize_rows(trade_rows)
    write_csv(OUT_DIR / "rootaware_regime_switch_trades_v1.csv", trade_rows)
    write_csv(OUT_DIR / "rootaware_regime_switch_root_summary_v1.csv", root_summary)

    roots_with_trades = [r["parent_regime_root"] for r in root_summary if int(r["total_trades"]) > 0]
    decision = {
        "selected_for_b3": False,
        "gate_result": "reject_b2r_insufficient_root_coverage",
        "reason": "RootAwareRegimeSwitch ran as a real Auto-Quant/Freqtrade strategy, but did not produce trades across Bull/Bear/Sideways/Crisis.",
        "next_action": "B2R: synthesize another root-aware recipe or loosen only the recipe logic, not the RC-SPA gates.",
    }
    if len(set(roots_with_trades) & {"Bull", "Bear", "Sideways"}) >= 3 and len(trade_rows) >= 100:
        decision = {
            "selected_for_b3": True,
            "gate_result": "selected_for_branch_rc_spa",
            "reason": "RootAwareRegimeSwitch produced enough multi-root trade rows to justify B3 branch RC-SPA.",
            "next_action": "B3: compute full branch RC-SPA hard gates for RootAwareRegimeSwitch.",
        }

    report = {
        "schema_version": "board-b-rootaware-recipe-b2r/v1",
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "run_root": str(RUN_ROOT.relative_to(REPO_ROOT)),
        "recipe_id": RECIPE_ID,
        "strategy_artifact": str((STRATEGY_PATH / f"{RECIPE_ID}.py").relative_to(REPO_ROOT)),
        "auto_quant": {
            "root": str(AUTO_QUANT_ROOT),
            "config": str(AUTO_QUANT_CONFIG),
            "pairs": PAIRS,
            "timerange": TIMERANGE,
        },
        "aggregate_metrics": {
            "trade_count": int(metric(strategy_result, "total_trades")),
            "win_rate": metric(strategy_result, "winrate"),
            "total_profit_pct": metric(strategy_result, "profit_total") * 100.0,
            "profit_factor": metric(strategy_result, "profit_factor"),
            "sharpe": metric(strategy_result, "sharpe"),
            "max_drawdown_pct": -abs(metric(strategy_result, "max_drawdown_account")) * 100.0,
        },
        "root_summary": root_summary,
        "decision": decision,
        "artifacts": {
            "trade_rows_csv": str((OUT_DIR / "rootaware_regime_switch_trades_v1.csv").relative_to(REPO_ROOT)),
            "root_summary_csv": str((OUT_DIR / "rootaware_regime_switch_root_summary_v1.csv").relative_to(REPO_ROOT)),
            "backtest_stdout": str(stdout_path.relative_to(REPO_ROOT)),
            "backtest_stderr": str(stderr_path.relative_to(REPO_ROOT)),
        },
    }
    report_path = OUT_DIR / "rootaware_regime_switch_b2r_report_v1.json"
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    md_lines = [
        "# RootAwareRegimeSwitch B2R v1",
        "",
        f"Run id: `{RUN_ID}`.",
        "",
        "## Decision",
        "",
        f"- Gate result: `{decision['gate_result']}`",
        f"- Selected for B3: `{str(decision['selected_for_b3']).lower()}`",
        f"- Reason: {decision['reason']}",
        "",
        "## Aggregate",
        "",
        f"- Trades: `{report['aggregate_metrics']['trade_count']}`",
        f"- Win rate: `{report['aggregate_metrics']['win_rate']:.4f}`",
        f"- Total profit pct: `{report['aggregate_metrics']['total_profit_pct']:.4f}`",
        f"- Profit factor: `{report['aggregate_metrics']['profit_factor']:.4f}`",
        f"- Sharpe: `{report['aggregate_metrics']['sharpe']:.4f}`",
        "",
        "## Root Summary",
        "",
        "| Root | Trades | Folds | Win Rate | Sum Profit Ratio | Path |",
        "|---|---:|---:|---:|---:|---|",
    ]
    for row in root_summary:
        md_lines.append(
            f"| {row['parent_regime_root']} | {row['total_trades']} | {row['test_folds']} | "
            f"{row['win_rate']:.4f} | {row['sum_profit_ratio_net']:.6f} | `{row['regime_profit_branch_path']}` |"
        )
    md_lines.extend(
        [
            "",
            "## Artifacts",
            "",
            f"- Strategy: `{(STRATEGY_PATH / f'{RECIPE_ID}.py').relative_to(REPO_ROOT)}`",
            f"- Report JSON: `{report_path.relative_to(REPO_ROOT)}`",
            f"- Trade rows: `{(OUT_DIR / 'rootaware_regime_switch_trades_v1.csv').relative_to(REPO_ROOT)}`",
            f"- Root summary: `{(OUT_DIR / 'rootaware_regime_switch_root_summary_v1.csv').relative_to(REPO_ROOT)}`",
            "",
            "## Next",
            "",
            f"- {decision['next_action']}",
        ]
    )
    md_path = OUT_DIR / "rootaware_regime_switch_b2r_report_v1.md"
    md_path.write_text("\n".join(md_lines) + "\n", encoding="utf-8")

    assertions = [
        f"trade_rows={len(trade_rows)}",
        f"roots_with_trades={','.join(roots_with_trades)}",
        f"gate_result={decision['gate_result']}",
        f"selected_for_b3={str(decision['selected_for_b3']).lower()}",
        f"report_json={report_path.relative_to(REPO_ROOT)}",
    ]
    (CHECK_DIR / "rootaware_recipe_b2r_v1_assertions.out").write_text(
        "\n".join(assertions) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
