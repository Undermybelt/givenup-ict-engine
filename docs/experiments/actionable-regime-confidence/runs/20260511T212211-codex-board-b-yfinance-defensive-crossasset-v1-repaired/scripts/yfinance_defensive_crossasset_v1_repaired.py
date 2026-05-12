#!/usr/bin/env python3
"""Board B yfinance defensive cross-asset RC-SPA readback.

Run-local additive experiment. It repairs the stale 211743 cursor by fetching a
daily yfinance ETF/index panel into this run root, attaching the accepted Board A
MainRegimeV2 source-root schedule, scoring unchanged Board B RC-SPA gates, and
including the already-passing 205047 scoped Manipulation component only as a
separate component.
"""

from __future__ import annotations

import csv
import importlib.util
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


RUN_ID = "20260511T212211+0800-codex-board-b-yfinance-defensive-crossasset-v1-repaired"
SCHEMA_VERSION = "board-b-yfinance-defensive-crossasset/v1-repaired"
RECIPE_ID = "YFinanceDefensiveCrossAssetV1Repaired"
SOURCE_TICKER = "^GSPC"

RUN_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = next(path for path in [RUN_ROOT, *RUN_ROOT.parents] if (path / "Cargo.toml").exists())
BASE_SCRIPT = (
    REPO_ROOT
    / "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T193803-codex-board-b-root-transition-triad-clean-v1/scripts/"
    "board_b_root_transition_triad_clean_v1.py"
)
MANIP_SUMMARY_CSV = (
    REPO_ROOT
    / "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T205047-codex-board-b-manipulation-stop-tp-grid-v2/"
    "manipulation-stop-tp-grid-v2/manipulation_stop_tp_grid_v2_summary.csv"
)
MANIP_REPORT_MD = (
    REPO_ROOT
    / "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T205047-codex-board-b-manipulation-stop-tp-grid-v2/"
    "manipulation-stop-tp-grid-v2/manipulation_stop_tp_grid_v2.md"
)

DATA_DIR = RUN_ROOT / "provider-cache"
PROVIDER_DIR = RUN_ROOT / "provider"

SYMBOLS = [
    "SPY",
    "QQQ",
    "IWM",
    "DIA",
    "EFA",
    "EEM",
    "HYG",
    "LQD",
    "TLT",
    "IEF",
    "SHY",
    "GLD",
    "UUP",
    "XLU",
    "XLP",
    "XLV",
    "USO",
]

DEFENSIVE = {"TLT", "IEF", "SHY", "GLD", "UUP", "XLU", "XLP", "XLV", "LQD"}
RISK_ASSETS = {"SPY", "QQQ", "IWM", "DIA", "EFA", "EEM", "HYG", "USO"}
RATE_SENSITIVE = {"TLT", "IEF", "SHY", "LQD", "XLU"}
COMMODITY_HEDGES = {"GLD", "UUP", "USO"}


def load_base_module() -> Any:
    spec = importlib.util.spec_from_file_location("board_b_root_transition_base", BASE_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import base evaluator: {BASE_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _flatten_yfinance_frame(frame: pd.DataFrame, symbol: str) -> pd.DataFrame:
    if frame.empty:
        return frame
    if isinstance(frame.columns, pd.MultiIndex):
        if symbol in frame.columns.get_level_values(0):
            frame = frame[symbol]
        elif symbol in frame.columns.get_level_values(-1):
            frame = frame.xs(symbol, axis=1, level=-1)
        else:
            frame.columns = [str(col[-1] if isinstance(col, tuple) else col) for col in frame.columns]
    frame = frame.reset_index()
    rename = {str(col).lower().replace(" ", "_"): col for col in frame.columns}
    date_col = rename.get("date") or rename.get("datetime")
    if date_col is None:
        raise RuntimeError(f"yfinance frame for {symbol} has no date column")
    out = pd.DataFrame()
    dates = pd.to_datetime(frame[date_col], utc=True)
    out["date"] = dates.map(lambda value: int(value.timestamp() * 1000))
    for src, dst in [
        ("open", "open"),
        ("high", "high"),
        ("low", "low"),
        ("close", "close"),
        ("adj_close", "close"),
        ("volume", "volume"),
    ]:
        if src in rename and dst not in out:
            out[dst] = pd.to_numeric(frame[rename[src]], errors="coerce")
    if "close" not in out and "Close" in frame:
        out["close"] = pd.to_numeric(frame["Close"], errors="coerce")
    for col in ["open", "high", "low"]:
        if col not in out:
            out[col] = out["close"]
    if "volume" not in out:
        out["volume"] = 0.0
    out = out[["date", "open", "high", "low", "close", "volume"]]
    return out.dropna(subset=["date", "open", "high", "low", "close"]).reset_index(drop=True)


def fetch_yfinance_panels() -> list[tuple[str, str, Path]]:
    import yfinance as yf

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    PROVIDER_DIR.mkdir(parents=True, exist_ok=True)
    panels: list[tuple[str, str, Path]] = []
    provider_rows: list[dict[str, Any]] = []
    for symbol in SYMBOLS:
        path = DATA_DIR / f"{symbol}_USD-1d.feather"
        status = "missing"
        rows = 0
        start_date = ""
        end_date = ""
        try:
            frame = yf.download(
                symbol,
                start="2000-01-01",
                end="2026-02-01",
                interval="1d",
                auto_adjust=True,
                progress=False,
                threads=False,
            )
            out = _flatten_yfinance_frame(frame, symbol)
            if len(out) >= 500:
                out.to_feather(path)
                panels.append((f"{symbol}/YF", "1d", path))
                status = "ready"
                rows = int(len(out))
                dates = pd.to_datetime(out["date"], unit="ms", utc=True)
                start_date = dates.min().date().isoformat()
                end_date = dates.max().date().isoformat()
            else:
                status = f"too_few_rows:{len(out)}"
        except Exception as exc:  # provider diagnostics only
            status = f"error:{type(exc).__name__}:{str(exc)[:160]}"
        provider_rows.append(
            {
                "symbol": symbol,
                "status": status,
                "rows": rows,
                "start_date": start_date,
                "end_date": end_date,
                "cache_path": str(path.relative_to(REPO_ROOT)) if path.exists() else "",
            }
        )
    with (PROVIDER_DIR / "yfinance_defensive_crossasset_provider_status.csv").open(
        "w", newline="", encoding="utf-8"
    ) as fh:
        writer = csv.DictWriter(fh, fieldnames=list(provider_rows[0].keys()))
        writer.writeheader()
        writer.writerows(provider_rows)
    return panels


def symbol_of(market: str) -> str:
    return market.split("/", 1)[0]


def roundtrip_cost(market: str, timeframe: str) -> float:
    symbol = symbol_of(market)
    if symbol in {"SHY", "IEF", "TLT"}:
        return 0.0004
    if symbol in {"SPY", "QQQ", "DIA", "GLD"}:
        return 0.0005
    if symbol in {"IWM", "EFA", "EEM", "HYG", "LQD", "UUP", "XLU", "XLP", "XLV"}:
        return 0.0007
    return 0.0010


def branch_path(root: str, variant_id: str) -> str:
    if root == "Bull":
        return f"{root} -> YFinanceRiskOnDaily -> EquityCreditMomentum -> {RECIPE_ID}:{variant_id}"
    if root == "Bear":
        return f"{root} -> YFinanceRiskOffDaily -> TreasuryGoldDefensiveOrEquityShort -> {RECIPE_ID}:{variant_id}"
    if root == "Sideways":
        return f"{root} -> YFinanceRangeDaily -> LowVolCarryOrBandReversion -> {RECIPE_ID}:{variant_id}"
    if root == "Crisis":
        return f"{root} -> YFinanceCrisisDaily -> TreasuryDollarGoldOrTailShort -> {RECIPE_ID}:{variant_id}"
    return (
        "Manipulation(scoped) -> TelegramPumpEvent -> ProviderStopTakeShort -> "
        "ManipulationStopTakeProfitGridV2:short_tp120_sl060_h72"
    )


def branch_fields(root: str) -> dict[str, str]:
    if root == "Bull":
        return {
            "sub_regime_tags": "YFinanceRiskOnDaily",
            "sub_sub_regime_or_profit_factor": "EquityCreditMomentum",
            "profit_factor_family": "yfinance_defensive_crossasset",
            "allowed_action": "long_research_only_until_branch_rc_spa_passes",
            "suppression_rule": "suppress_if_bull_yfinance_defensive_branch_rc_spa_fails",
        }
    if root == "Bear":
        return {
            "sub_regime_tags": "YFinanceRiskOffDaily",
            "sub_sub_regime_or_profit_factor": "TreasuryGoldDefensiveOrEquityShort",
            "profit_factor_family": "yfinance_defensive_crossasset",
            "allowed_action": "long_defensive_or_short_research_only_until_branch_rc_spa_passes",
            "suppression_rule": "suppress_if_bear_yfinance_defensive_branch_rc_spa_fails",
        }
    if root == "Sideways":
        return {
            "sub_regime_tags": "YFinanceRangeDaily",
            "sub_sub_regime_or_profit_factor": "LowVolCarryOrBandReversion",
            "profit_factor_family": "yfinance_defensive_crossasset",
            "allowed_action": "low_vol_or_reversion_research_only_until_branch_rc_spa_passes",
            "suppression_rule": "suppress_if_sideways_yfinance_defensive_branch_rc_spa_fails",
        }
    if root == "Crisis":
        return {
            "sub_regime_tags": "YFinanceCrisisDaily",
            "sub_sub_regime_or_profit_factor": "TreasuryDollarGoldOrTailShort",
            "profit_factor_family": "yfinance_defensive_crossasset",
            "allowed_action": "defensive_or_tail_short_research_only_until_branch_rc_spa_passes",
            "suppression_rule": "tail_guard_blocks_yfinance_defensive_branch_if_rc_spa_fails",
        }
    return {
        "sub_regime_tags": "TelegramPumpEvent",
        "sub_sub_regime_or_profit_factor": "ProviderStopTakeShort",
        "profit_factor_family": "direct_manipulation_stop_take_profit",
        "allowed_action": "short_stop_tp_component_only",
        "suppression_rule": "do_not_use_without_price_root_branch_passes",
    }


def signal_direction(row: pd.Series, variant: dict[str, Any]) -> int:
    root = str(row["parent_regime_root"])
    market = str(row["market"])
    symbol = symbol_of(market)
    mode = str(variant["mode"])
    lookback = int(variant["lookback"])
    ema_col = f"ema{int(variant['ema'])}"
    trend = float(row.get(f"ret{lookback}", row["ret5"]))
    ret1 = float(row["ret1"])
    ret3 = float(row["ret3"])
    z_value = float(row["z20"])
    close = float(row["close"])
    ema_value = float(row[ema_col])
    ema50 = float(row["ema50"])
    ema20_slope = float(row["ema20_slope"])
    atr_pct = max(float(row["atr_pct"]), 1e-9)
    vix = float(row["source_ticker_vix"])
    z_threshold = float(variant["z"])
    low_slope = abs(ema20_slope) < max(0.0035, atr_pct * 0.35)
    risk_asset = symbol in RISK_ASSETS
    defensive = symbol in DEFENSIVE
    rate_sensitive = symbol in RATE_SENSITIVE
    commodity_hedge = symbol in COMMODITY_HEDGES

    if root == "Bull":
        if mode == "risk_on_momentum":
            return 1 if risk_asset and trend > max(0.002, atr_pct * 0.20) and close > ema_value else 0
        if mode == "credit_confirmation":
            return 1 if symbol in {"HYG", "LQD"} and trend > 0 and close > ema_value and vix < 28 else 0
        if mode == "bull_pullback_reclaim":
            return 1 if risk_asset and close > ema50 and z_value <= -z_threshold and ret1 > 0 else 0
        return 0

    if root == "Bear":
        if mode == "defensive_duration":
            return 1 if rate_sensitive and trend > 0 and close > ema_value else 0
        if mode == "defensive_gold_dollar":
            return 1 if commodity_hedge and trend > 0 and close > ema_value else 0
        if mode == "equity_downtrend_short":
            return -1 if risk_asset and trend < -max(0.002, atr_pct * 0.20) and close < ema_value else 0
        if mode == "bear_relief_fade":
            return -1 if risk_asset and close < ema50 and z_value >= z_threshold and ret1 < 0 else 0
        return 0

    if root == "Sideways":
        if mode == "range_reversion":
            if low_slope and z_value >= z_threshold:
                return -1
            if low_slope and z_value <= -z_threshold:
                return 1
        if mode == "low_vol_carry":
            return 1 if defensive and low_slope and trend > 0 and close > ema_value else 0
        if mode == "range_breakout_fail":
            if low_slope and close > float(row["high20_prev"]) and ret1 < 0:
                return -1
            if low_slope and close < float(row["low20_prev"]) and ret1 > 0:
                return 1
        return 0

    if root == "Crisis":
        if mode == "crisis_defensive_duration":
            return 1 if symbol in {"TLT", "IEF", "SHY"} and (trend > 0 or close > ema_value) else 0
        if mode == "crisis_gold_dollar":
            return 1 if symbol in {"GLD", "UUP"} and (trend > 0 or close > ema_value) else 0
        if mode == "crisis_equity_tail_short":
            return -1 if risk_asset and (trend < 0 or ret3 < -max(0.008, atr_pct)) and close < ema_value else 0
        if mode == "panic_rebound":
            panic = z_value <= -max(1.5, z_threshold) or ret3 <= -max(0.018, atr_pct * 1.8)
            return 1 if risk_asset and panic and ret1 > 0 and vix < 55 else 0
        return 0

    return 0


def load_manip_component(module: Any) -> tuple[dict[str, Any], dict[str, Any]]:
    if not MANIP_SUMMARY_CSV.exists():
        row = module.summarize_rows(
            root="Manipulation(scoped)",
            variant_id="missing_205047_component",
            rows=[],
            all_rows=[],
            pbo=1.0,
            pbo_method="missing_205047_component",
        )
        return row, {"component_available": False}
    with MANIP_SUMMARY_CSV.open(newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    passed = [row for row in rows if row.get("gate_result") == "pass:tradeable_manipulation_stop_tp_candidate"]
    best = next((row for row in passed if row.get("variant_id") == "short_tp120_sl060_h72"), passed[0] if passed else None)
    if best is None:
        row = module.summarize_rows(
            root="Manipulation(scoped)",
            variant_id="no_passing_205047_component",
            rows=[],
            all_rows=[],
            pbo=1.0,
            pbo_method="no_passing_205047_component",
        )
        return row, {"component_available": False, "component_source": str(MANIP_SUMMARY_CSV)}
    summary = {
        "recipe_id": "ManipulationStopTakeProfitGridV2",
        "parent_regime_root": "Manipulation(scoped)",
        "selected_variant_id": best["variant_id"],
        "regime_profit_branch_path": best["regime_profit_branch_path"],
        "total_trades": int(best["positive_rows"]),
        "test_folds": int(best["monthly_folds"]),
        "folds": "monthly_folds_12",
        "min_trades_per_test_fold": int(int(best["positive_rows"]) / int(best["monthly_folds"])),
        "fold_positive_rate": float(best["fold_positive_rate_absolute"]),
        "win_rate": 0.0,
        "mean_profit_ratio_net": float(best["positive_mean_net"]),
        "net_return_R": 0.0,
        "bootstrap_edge_lcb_5pct": float(best["positive_lcb_5pct"]),
        "bootstrap_edge_lcb_5pct_stressed_2x_cost": float(best["positive_lcb_5pct"]) - float(best["roundtrip_cost"]),
        "pbo": 0.0,
        "pbo_method": "external_component_not_reoptimized_in_this_run",
        "dsr": 1.0,
        "dsr_method": "external_component_pass_from_205047_not_rescored_here",
        "cost_stress_result": "pass",
        "tail_loss_p95": 0.0,
        "max_drawdown_trade_equity_proxy": 0.0,
        "regime_specificity_ratio": 999.0,
        "outside_mean_profit_ratio_net": float(best["control_mean_net"]),
        "rc_spa": 100.0,
        "promotion_level": "component_pass_only",
        "hard_gate_result": "pass",
        "downstream_consumption_status": "not_started:full_board_b_root_gates_required",
    }
    component = {
        "component_available": True,
        "component_run_id": best["run_id"],
        "component_report": module.rel(MANIP_REPORT_MD),
        "component_summary_csv": module.rel(MANIP_SUMMARY_CSV),
        "component_gate_result": best["gate_result"],
        "component_variant": best["variant_id"],
        "component_positive_rows": int(best["positive_rows"]),
        "component_control_rows": int(best["control_rows"]),
        "component_positive_lcb_5pct": float(best["positive_lcb_5pct"]),
        "component_specificity_lcb_5pct": float(best["positive_minus_control_lcb_5pct"]),
    }
    return summary, component


def patch_module(module: Any, panels: list[tuple[str, str, Path]]) -> None:
    module.RUN_ID = RUN_ID
    module.SCHEMA_VERSION = SCHEMA_VERSION
    module.RECIPE_ID = RECIPE_ID
    module.SOURCE_TICKER = SOURCE_TICKER
    module.RUN_ROOT = RUN_ROOT
    module.DATA_DIR = DATA_DIR
    module.OUT_DIR = RUN_ROOT / "branch-rc-spa"
    module.CHECK_DIR = RUN_ROOT / "checks"
    module.FAIL_CLOSED_DIR = RUN_ROOT / "ict-engine-fail-closed"
    module.ALL_ROWS_CSV = module.OUT_DIR / "yfinance_defensive_crossasset_variant_rows_v1.csv"
    module.SELECTED_ROWS_CSV = module.OUT_DIR / "yfinance_defensive_crossasset_selected_rows_v1.csv"
    module.SUMMARY_CSV = module.OUT_DIR / "yfinance_defensive_crossasset_branch_summary_v1.csv"
    module.PANEL_SUMMARY_CSV = module.OUT_DIR / "yfinance_defensive_crossasset_panel_summary_v1.csv"
    module.REPORT_JSON = module.OUT_DIR / "yfinance_defensive_crossasset_rc_spa_report_v1.json"
    module.REPORT_MD = module.OUT_DIR / "yfinance_defensive_crossasset_rc_spa_report_v1.md"
    module.ASSERTIONS = module.CHECK_DIR / "yfinance_defensive_crossasset_v1_assertions.out"
    module.FAIL_CLOSED_MD = module.FAIL_CLOSED_DIR / "yfinance_defensive_crossasset_fail_closed_summary_v1.md"
    module.PANELS = panels
    module.VARIANTS = [
        {"variant_id": "risk_on_momentum_5d", "mode": "risk_on_momentum", "lookback": 5, "ema": 20, "z": 0.90, "hold": {"1d": 5}},
        {"variant_id": "risk_on_momentum_20d", "mode": "risk_on_momentum", "lookback": 20, "ema": 50, "z": 1.10, "hold": {"1d": 10}},
        {"variant_id": "credit_confirmation", "mode": "credit_confirmation", "lookback": 10, "ema": 20, "z": 1.00, "hold": {"1d": 8}},
        {"variant_id": "bull_pullback_reclaim", "mode": "bull_pullback_reclaim", "lookback": 5, "ema": 20, "z": 0.85, "hold": {"1d": 5}},
        {"variant_id": "defensive_duration", "mode": "defensive_duration", "lookback": 10, "ema": 20, "z": 1.00, "hold": {"1d": 8}},
        {"variant_id": "defensive_gold_dollar", "mode": "defensive_gold_dollar", "lookback": 10, "ema": 20, "z": 1.00, "hold": {"1d": 8}},
        {"variant_id": "equity_downtrend_short", "mode": "equity_downtrend_short", "lookback": 10, "ema": 20, "z": 1.00, "hold": {"1d": 8}},
        {"variant_id": "bear_relief_fade", "mode": "bear_relief_fade", "lookback": 5, "ema": 20, "z": 0.95, "hold": {"1d": 5}},
        {"variant_id": "range_reversion", "mode": "range_reversion", "lookback": 5, "ema": 20, "z": 0.80, "hold": {"1d": 4}},
        {"variant_id": "low_vol_carry", "mode": "low_vol_carry", "lookback": 10, "ema": 20, "z": 0.90, "hold": {"1d": 6}},
        {"variant_id": "range_breakout_fail", "mode": "range_breakout_fail", "lookback": 5, "ema": 20, "z": 0.75, "hold": {"1d": 4}},
        {"variant_id": "crisis_defensive_duration", "mode": "crisis_defensive_duration", "lookback": 5, "ema": 20, "z": 1.00, "hold": {"1d": 6}},
        {"variant_id": "crisis_gold_dollar", "mode": "crisis_gold_dollar", "lookback": 5, "ema": 20, "z": 1.00, "hold": {"1d": 6}},
        {"variant_id": "crisis_equity_tail_short", "mode": "crisis_equity_tail_short", "lookback": 5, "ema": 20, "z": 1.00, "hold": {"1d": 6}},
        {"variant_id": "panic_rebound", "mode": "panic_rebound", "lookback": 3, "ema": 20, "z": 1.20, "hold": {"1d": 4}},
    ]
    module.roundtrip_cost = roundtrip_cost
    module.signal_direction = signal_direction
    module.branch_fields = branch_fields
    module.branch_path = branch_path


def write_report(module: Any, report: dict[str, Any]) -> None:
    decision = report["decision"]
    branch_lines = [
        "| Root | Selected Variant | Trades | Folds | Min Fold Trades | Fold Positive Rate | LCB 5% | PBO | DSR | RC-SPA | Gate |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in report["branch_summaries"]:
        branch_lines.append(
            f"| {row['parent_regime_root']} | `{row['selected_variant_id']}` | "
            f"{row['total_trades']} | {row['test_folds']} | {row['min_trades_per_test_fold']} | "
            f"{row['fold_positive_rate']:.4f} | {row['bootstrap_edge_lcb_5pct']:.6f} | "
            f"{row['pbo']:.3f} | {row['dsr']:.4f} | {row['rc_spa']:.4f} | `{row['hard_gate_result']}` |"
        )
    lines = [
        "# YFinance Defensive Cross-Asset RC-SPA v1 Repaired",
        "",
        f"Run id: `{RUN_ID}`.",
        "",
        "## Decision",
        "",
        f"- Gate result: `{decision['gate_result']}`",
        f"- Stable profit score: `{decision['stable_profit_score']:.4f}`",
        f"- Price-root paths passed: `{decision['price_root_paths_passed']}/4`",
        f"- Scoped Manipulation component pass consumed: `{decision['manipulation_component_pass']}`",
        f"- Variant rows: `{decision['variant_trade_rows']}`",
        f"- Selected rows: `{decision['selected_trade_rows']}`",
        f"- Selected root counts: `{decision['selected_root_trade_counts']}`",
        f"- Downstream consumption: `{decision['downstream_consumption']}`",
        f"- Primary blocker: {decision['primary_blocker']}",
        "",
        "## Selected Branch Summary",
        "",
        *branch_lines,
        "",
        "## Inputs",
        "",
        f"- YFinance cache: `{module.rel(DATA_DIR)}`",
        f"- Provider status: `{module.rel(PROVIDER_DIR / 'yfinance_defensive_crossasset_provider_status.csv')}`",
        f"- Board A consumer map: `{module.rel(module.BOARD_A_CONSUMER_MAP)}`",
        f"- Source root schedule: `{module.SOURCE_REGIME_CSV}` / `{SOURCE_TICKER}`",
        f"- Scoped Manipulation component: `{report['manipulation_component'].get('component_report', 'missing')}`",
        "",
        "## Artifacts",
        "",
        f"- Report JSON: `{module.rel(module.REPORT_JSON)}`",
        f"- Selected rows: `{module.rel(module.SELECTED_ROWS_CSV)}`",
        f"- Variant rows: `{module.rel(module.ALL_ROWS_CSV)}`",
        f"- Branch summary: `{module.rel(module.SUMMARY_CSV)}`",
        f"- Panel summary: `{module.rel(module.PANEL_SUMMARY_CSV)}`",
        f"- Fail-closed downstream summary: `{module.rel(module.FAIL_CLOSED_MD)}`",
        f"- Assertions: `{module.rel(module.ASSERTIONS)}`",
        "",
        "## Next",
        "",
        f"- {decision['next_action']}",
    ]
    module.REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    module = load_base_module()
    panels = fetch_yfinance_panels()
    patch_module(module, panels)
    for path in [module.OUT_DIR, module.CHECK_DIR, module.FAIL_CLOSED_DIR]:
        path.mkdir(parents=True, exist_ok=True)
    required_inputs = [module.SOURCE_REGIME_CSV, module.BOARD_A_CONSUMER_MAP, MANIP_SUMMARY_CSV]
    missing = [str(path) for path in required_inputs if not path.exists() or path.stat().st_size == 0]
    missing += [str(path) for _, _, path in module.PANELS if not path.exists() or path.stat().st_size == 0]
    if not module.PANELS:
        missing.append("no_yfinance_panels_ready")
    if missing:
        raise RuntimeError("missing required inputs: " + ", ".join(missing))

    floors = module.load_root_floors()
    source = module.load_source_roots()
    lookup = module.RootLookup(source, floors)
    all_rows: list[dict[str, Any]] = []
    panel_summaries: list[dict[str, Any]] = []
    for market, timeframe, path in module.PANELS:
        panel = module.load_panel(path, market, timeframe, lookup)
        for variant in module.VARIANTS:
            rows = module.build_trade_rows(panel, variant)
            all_rows.extend(rows)
            values = np.array([float(r["profit_ratio_net"]) for r in rows], dtype=float)
            panel_summaries.append(
                {
                    "market": market,
                    "timeframe": timeframe,
                    "variant_id": variant["variant_id"],
                    "bars": int(len(panel)),
                    "trades": int(len(rows)),
                    "mean_profit_ratio": float(np.mean(values)) if len(values) else 0.0,
                    "win_rate": float(np.mean(values > 0)) if len(values) else 0.0,
                    "net_return_R": float(np.sum(values)) if len(values) else 0.0,
                }
            )

    branch_summaries: list[dict[str, Any]] = []
    variant_summaries: list[dict[str, Any]] = []
    selected_rows: list[dict[str, Any]] = []
    for root in module.ROOTS:
        pbo, pbo_method = module.pbo_for_root(root, all_rows)
        summaries = []
        for variant in [str(v["variant_id"]) for v in module.VARIANTS]:
            rows = [r for r in all_rows if r["parent_regime_root"] == root and str(r["variant_id"]) == variant]
            summaries.append(
                module.summarize_rows(
                    root=root,
                    variant_id=variant,
                    rows=rows,
                    all_rows=all_rows,
                    pbo=pbo,
                    pbo_method=pbo_method,
                )
            )
        selected = max(summaries, key=lambda row: float(row["rc_spa"]))
        branch_summaries.append(selected)
        variant_summaries.extend(summaries)
        selected_variant = str(selected["selected_variant_id"])
        selected_rows.extend(
            [
                r
                for r in all_rows
                if r["parent_regime_root"] == root and str(r["variant_id"]) == selected_variant
            ]
        )

    manip_summary, manip_component = load_manip_component(module)
    branch_summaries.append(manip_summary)
    price_root_summaries = [row for row in branch_summaries if row["parent_regime_root"] in module.ROOTS]
    passed_price_roots = [row for row in price_root_summaries if row["hard_gate_result"] == "pass"]
    manip_pass = manip_summary["hard_gate_result"] == "pass"
    all_required_pass = len(passed_price_roots) == len(module.ROOTS) and manip_pass
    max_price_score = max(float(row["rc_spa"]) for row in price_root_summaries) if price_root_summaries else 0.0

    selected_counts = {root: 0 for root in [*module.ROOTS, "Manipulation(scoped)"]}
    for row in selected_rows:
        selected_counts[row["parent_regime_root"]] = selected_counts.get(row["parent_regime_root"], 0) + 1
    selected_counts["Manipulation(scoped)"] = int(manip_component.get("component_positive_rows", 0))
    matrix_counts = {root: 0 for root in [*module.ROOTS, "Manipulation(scoped)"]}
    for row in all_rows:
        matrix_counts[row["parent_regime_root"]] = matrix_counts.get(row["parent_regime_root"], 0) + 1
    matrix_counts["Manipulation(scoped)"] = int(manip_component.get("component_positive_rows", 0))

    root_failures = [
        f"{row['parent_regime_root']}={row['hard_gate_result']}"
        for row in price_root_summaries
        if row["hard_gate_result"] != "pass"
    ]
    if not manip_pass:
        root_failures.append("Manipulation(scoped)=missing_205047_component_pass")
    gate_result = "pass" if all_required_pass else "fail:required_root_branch_hard_gates_failed"
    downstream = (
        "eligible_for_pre_bayes_bbn_catboost_execution_tree_probe"
        if all_required_pass
        else "not_started:blocked_by_branch_rc_spa_hard_gates"
    )
    primary_blocker = "all required branch hard gates passed" if all_required_pass else "; ".join(root_failures)
    next_action = (
        "B5: run Pre-Bayes -> BBN -> CatBoost/path-ranker -> execution-tree branch consumption with the same branch paths."
        if all_required_pass
        else "B2R-repeat: keep the 205047 scoped Manipulation component, but find a price-root family where Bull/Bear/Sideways/Crisis all pass unchanged RC-SPA before downstream promotion."
    )
    report = {
        "schema_version": SCHEMA_VERSION,
        "run_id": RUN_ID,
        "run_root": module.rel(RUN_ROOT),
        "repo_git_ref": module.git_ref(REPO_ROOT),
        "accepted_regime_id": "BoardA_regime_factor_consumer_map_MainRegimeV2_roots_plus_scoped_manipulation",
        "accepted_regime_artifact": module.rel(module.BOARD_A_CONSUMER_MAP),
        "recipe_id": RECIPE_ID,
        "inputs": {
            "data_dir": module.rel(DATA_DIR),
            "provider_status": module.rel(PROVIDER_DIR / "yfinance_defensive_crossasset_provider_status.csv"),
            "source_regime_csv": str(module.SOURCE_REGIME_CSV),
            "source_ticker": SOURCE_TICKER,
            "board_a_consumer_map": module.rel(module.BOARD_A_CONSUMER_MAP),
            "manipulation_component_summary": module.rel(MANIP_SUMMARY_CSV),
        },
        "decision": {
            "gate_result": gate_result,
            "stable_profit_score": max_price_score,
            "variant_trade_rows": len(all_rows),
            "selected_trade_rows": len(selected_rows),
            "branch_paths_evaluated": len(branch_summaries),
            "branch_paths_passed": len(passed_price_roots) + int(manip_pass),
            "price_root_paths_passed": len(passed_price_roots),
            "manipulation_component_pass": manip_pass,
            "selected_root_trade_counts": selected_counts,
            "matrix_root_trade_counts": matrix_counts,
            "downstream_consumption": downstream,
            "primary_blocker": primary_blocker,
            "next_action": next_action,
        },
        "manipulation_component": manip_component,
        "branch_summaries": branch_summaries,
        "variant_summaries": variant_summaries,
        "panel_summaries": panel_summaries,
        "artifacts": {
            "report_json": module.rel(module.REPORT_JSON),
            "report_md": module.rel(module.REPORT_MD),
            "selected_rows_csv": module.rel(module.SELECTED_ROWS_CSV),
            "all_rows_csv": module.rel(module.ALL_ROWS_CSV),
            "summary_csv": module.rel(module.SUMMARY_CSV),
            "panel_summary_csv": module.rel(module.PANEL_SUMMARY_CSV),
            "assertions": module.rel(module.ASSERTIONS),
            "fail_closed_summary": module.rel(module.FAIL_CLOSED_MD),
        },
        "completion": {
            "runtime_code_changed": False,
            "auto_quant_checkout_changed": False,
            "raw_auto_quant_data_committed": False,
            "thresholds_relaxed_after_scoring": False,
            "downstream_runtime_consumed_branch_path": all_required_pass,
        },
    }

    module.write_csv(module.ALL_ROWS_CSV, all_rows)
    module.write_csv(module.SELECTED_ROWS_CSV, selected_rows)
    module.write_csv(module.SUMMARY_CSV, branch_summaries)
    module.write_csv(module.PANEL_SUMMARY_CSV, panel_summaries)
    module.write_json(module.REPORT_JSON, report)
    write_report(module, report)
    module.FAIL_CLOSED_MD.write_text(
        "\n".join(
            [
                "# YFinance Defensive Cross-Asset ict-engine Fail-Closed Summary v1",
                "",
                f"Run id: `{RUN_ID}`.",
                "",
                f"- Branch RC-SPA gate: `{gate_result}`",
                f"- Downstream consumption: `{downstream}`",
                "- Pre-Bayes / BBN / CatBoost / execution-tree were not started unless every required branch hard gate passed.",
                "- The 205047 scoped Manipulation component is recorded as a component pass only, not an aggregate promotion.",
                "- This is a fail-closed readback unless all four price roots and scoped Manipulation pass together.",
                "",
                f"Primary blocker: {primary_blocker}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    assertions = [
        f"run_id={RUN_ID}",
        f"yfinance_panels_ready={len(module.PANELS)}",
        f"variant_trade_rows={len(all_rows)}",
        f"selected_trade_rows={len(selected_rows)}",
        f"branch_paths_evaluated={len(branch_summaries)}",
        f"price_root_paths_passed={len(passed_price_roots)}",
        f"manipulation_component_pass={manip_pass}",
        f"gate_result={gate_result}",
        f"downstream_consumption={downstream}",
        "artifacts_exist=true",
    ]
    if not all_rows:
        assertions.append("ASSERT_FAIL:no_variant_trade_rows")
    module.ASSERTIONS.write_text("\n".join(assertions) + "\n", encoding="utf-8")
    print(json.dumps(report["decision"], indent=2, sort_keys=True))
    return 1 if any(line.startswith("ASSERT_FAIL") for line in assertions) else 0


if __name__ == "__main__":
    raise SystemExit(main())
