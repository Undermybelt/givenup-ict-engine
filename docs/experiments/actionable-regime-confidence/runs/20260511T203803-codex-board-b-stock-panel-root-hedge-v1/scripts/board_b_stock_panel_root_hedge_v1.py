#!/usr/bin/env python3
"""Board B stock/ETF root-hedge RC-SPA readback.

Run-local additive experiment. This deliberately changes the Board B surface
away from Tomac/NQ-only, VRP-only, and the prior NQ intraday stress family.
It consumes local Auto-Quant feather panels, attaches the accepted Board A
MainRegimeV2 root context, and keeps downstream fail-closed unless every
required branch path passes unchanged RC-SPA hard gates.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


RUN_ID = "20260511T203803+0800-codex-board-b-stock-panel-root-hedge-v1"
SCHEMA_VERSION = "board-b-stock-panel-root-hedge/v1"
RECIPE_ID = "StockPanelRootHedgeV1"
SOURCE_TICKER = "^GSPC"

RUN_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = next(path for path in [RUN_ROOT, *RUN_ROOT.parents] if (path / "Cargo.toml").exists())
BASE_SCRIPT = (
    REPO_ROOT
    / "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T193803-codex-board-b-root-transition-triad-clean-v1/scripts/"
    "board_b_root_transition_triad_clean_v1.py"
)
DATA_DIR = Path("/Users/thrill3r/Auto-Quant/user_data/data")


def load_base_module() -> Any:
    spec = importlib.util.spec_from_file_location("board_b_root_transition_base", BASE_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import base evaluator: {BASE_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _arr(df: pd.DataFrame, column: str) -> np.ndarray:
    return df[column].to_numpy(dtype=float)


def _safe(df: pd.DataFrame, column: str, fallback: str) -> np.ndarray:
    return df[column].to_numpy(dtype=float) if column in df else df[fallback].to_numpy(dtype=float)


def _select_non_overlapping(candidates: np.ndarray, hold: int, size: int) -> list[int]:
    selected: list[int] = []
    next_allowed = 0
    for raw_idx in candidates.tolist():
        idx = int(raw_idx)
        if idx < next_allowed or idx + hold >= size:
            continue
        selected.append(idx)
        next_allowed = idx + hold + 1
    return selected


def _is_gold(market: str) -> bool:
    return market.startswith("GLD")


def branch_path(root: str, variant_id: str) -> str:
    if root == "Bull":
        return f"{root} -> TrendExpansion -> EquityRiskOnMomentum -> {RECIPE_ID}:{variant_id}"
    if root == "Bear":
        return f"{root} -> BearMarketDrawdown -> DefensiveHedgeRotation -> {RECIPE_ID}:{variant_id}"
    if root == "Sideways":
        return f"{root} -> RangeConsolidation -> CrossAssetRangeReversion -> {RECIPE_ID}:{variant_id}"
    if root == "Crisis":
        return f"{root} -> ExtremeStress -> TailHedgeRotation -> {RECIPE_ID}:{variant_id}"
    return "Manipulation(scoped) -> DirectEventOverlayMissing -> no_direct_event_rows -> suppress_or_abstain"


def branch_fields(root: str) -> dict[str, str]:
    if root == "Bull":
        return {
            "sub_regime_tags": "TrendExpansion",
            "sub_sub_regime_or_profit_factor": "EquityRiskOnMomentum",
            "profit_factor_family": "stock_panel_root_hedge",
            "allowed_action": "long_research_only_until_branch_rc_spa_passes",
            "suppression_rule": "suppress_if_bull_stock_panel_branch_rc_spa_fails",
        }
    if root == "Bear":
        return {
            "sub_regime_tags": "BearMarketDrawdown",
            "sub_sub_regime_or_profit_factor": "DefensiveHedgeRotation",
            "profit_factor_family": "stock_panel_root_hedge",
            "allowed_action": "short_or_gold_defensive_research_only_until_branch_rc_spa_passes",
            "suppression_rule": "suppress_if_bear_stock_panel_branch_rc_spa_fails",
        }
    if root == "Sideways":
        return {
            "sub_regime_tags": "RangeConsolidation",
            "sub_sub_regime_or_profit_factor": "CrossAssetRangeReversion",
            "profit_factor_family": "stock_panel_root_hedge",
            "allowed_action": "long_short_research_only_until_branch_rc_spa_passes",
            "suppression_rule": "suppress_if_sideways_stock_panel_branch_rc_spa_fails",
        }
    if root == "Crisis":
        return {
            "sub_regime_tags": "ExtremeStress",
            "sub_sub_regime_or_profit_factor": "TailHedgeRotation",
            "profit_factor_family": "stock_panel_root_hedge",
            "allowed_action": "short_or_defensive_research_only_until_branch_rc_spa_passes",
            "suppression_rule": "tail_guard_blocks_crisis_stock_panel_branch_if_rc_spa_fails",
        }
    return {
        "sub_regime_tags": "DirectEventOverlayMissing",
        "sub_sub_regime_or_profit_factor": "no_direct_event_rows",
        "profit_factor_family": "direct_manipulation_overlay",
        "allowed_action": "suppress_or_abstain",
        "suppression_rule": "no_direct_manipulation_profit_rows",
    }


def _signal_vector(df: pd.DataFrame, variant: dict[str, Any]) -> np.ndarray:
    roots = df["parent_regime_root"].astype(str).to_numpy()
    market = str(df["market"].iloc[0])
    mode = str(variant["mode"])
    lookback = int(variant["lookback"])
    ema_col = f"ema{int(variant['ema'])}"
    trend = _safe(df, f"ret{lookback}", "ret5")
    ret1 = _arr(df, "ret1")
    ret3 = _arr(df, "ret3")
    z20 = _arr(df, "z20")
    close = _arr(df, "close")
    ema_value = _arr(df, ema_col)
    ema20 = _arr(df, "ema20")
    ema50 = _arr(df, "ema50")
    ema20_slope = _arr(df, "ema20_slope")
    atr_pct = np.maximum(_arr(df, "atr_pct"), 1e-9)
    vix = _arr(df, "source_ticker_vix")
    high20_prev = np.nan_to_num(_arr(df, "high20_prev"), nan=0.0)
    low20_prev = np.nan_to_num(_arr(df, "low20_prev"), nan=0.0)
    z_threshold = float(variant["z"])
    gold = _is_gold(market)
    low_slope = np.abs(ema20_slope) < np.maximum(0.0035, atr_pct * 0.40)
    signal = np.zeros(len(df), dtype=np.int8)

    bull = roots == "Bull"
    if mode == "risk_on_momentum":
        signal[bull & ~gold & (trend > np.maximum(0.001, atr_pct * 0.15)) & (close > ema_value)] = 1
    elif mode == "risk_on_pullback":
        signal[bull & ~gold & (z20 <= -z_threshold) & (close > ema50) & (ret1 > -0.01)] = 1
    elif mode == "gold_defensive_long":
        signal[bull & gold & (trend > np.maximum(0.0005, atr_pct * 0.10)) & (close > ema20)] = 1

    bear = roots == "Bear"
    if mode == "equity_short_hedge":
        signal[bear & ~gold & (trend < -np.maximum(0.001, atr_pct * 0.20)) & (close < ema_value)] = -1
    elif mode == "failed_rally_short":
        signal[bear & ~gold & (z20 >= z_threshold) & (ret1 < 0) & (close < ema50)] = -1
    elif mode == "gold_defensive_long":
        signal[bear & gold & (trend > np.maximum(0.0005, atr_pct * 0.10)) & (close > ema20)] = 1

    sideways = roots == "Sideways"
    if mode == "range_reversion":
        signal[sideways & low_slope & (z20 >= z_threshold)] = -1
        signal[sideways & low_slope & (z20 <= -z_threshold)] = 1
    elif mode == "range_breakout_failure":
        signal[sideways & low_slope & (close > high20_prev) & (ret1 < 0)] = -1
        signal[sideways & low_slope & (close < low20_prev) & (ret1 > 0)] = 1
    elif mode == "microtrend_carry":
        threshold = np.maximum(0.0008, atr_pct * 0.18)
        signal[sideways & low_slope & (trend > threshold) & (close > ema20)] = 1
        signal[sideways & low_slope & (trend < -threshold) & (close < ema20)] = -1

    crisis = roots == "Crisis"
    if mode == "crisis_equity_tail_short":
        signal[
            crisis
            & ~gold
            & ((trend < -np.maximum(0.0015, atr_pct * 0.25)) | (ret3 < -np.maximum(0.003, atr_pct)))
            & ((close < ema_value) | (vix >= 28))
        ] = -1
    elif mode == "crisis_gold_safehaven":
        signal[crisis & gold & (trend > np.maximum(0.0005, atr_pct * 0.10)) & (close > ema20)] = 1
    elif mode == "crisis_relief_rebound":
        panic = (z20 <= -z_threshold) | (ret3 <= -np.maximum(0.006, atr_pct * 1.2))
        signal[crisis & ~gold & panic & (ret1 > 0) & (vix < 45)] = 1

    return signal


def _build_trade_rows(module: Any, df: pd.DataFrame, variant: dict[str, Any]) -> list[dict[str, Any]]:
    if df.empty:
        return []
    variant_id = str(variant["variant_id"])
    timeframe = str(df["timeframe"].iloc[0])
    market = str(df["market"].iloc[0])
    hold = int(variant["hold"].get(timeframe, 5))
    cost = float(module.roundtrip_cost(market, timeframe))
    signal = _signal_vector(df, variant)
    selected = _select_non_overlapping(np.flatnonzero(signal != 0), hold, len(df))
    if not selected:
        return []

    idx = np.array(selected, dtype=int)
    exit_idx = idx + hold
    close = _arr(df, "close")
    entry = close[idx]
    exit_price = close[exit_idx]
    valid = (entry > 0) & (exit_price > 0)
    idx = idx[valid]
    exit_idx = exit_idx[valid]
    entry = entry[valid]
    exit_price = exit_price[valid]
    if len(idx) == 0:
        return []

    direction = signal[idx].astype(int)
    pnl = direction * (exit_price / entry - 1.0) - cost
    gross = direction * (exit_price / entry - 1.0)
    roots = df["parent_regime_root"].astype(str).to_numpy()
    dates = df["date"].to_numpy()
    session_dates = df["session_date"].to_numpy()
    floors = _arr(df, "parent_regime_confidence_floor")
    conf = _arr(df, "source_ticker_confidence")
    vix = _arr(df, "source_ticker_vix")
    lookup_status = df["root_lookup_status"].astype(str).to_numpy()

    rows: list[dict[str, Any]] = []
    for pos, open_idx in enumerate(idx.tolist()):
        root = str(roots[open_idx])
        if root not in module.ROOTS:
            continue
        fields = branch_fields(root)
        close_idx = int(exit_idx[pos])
        open_ts = pd.Timestamp(dates[open_idx])
        close_ts = pd.Timestamp(dates[close_idx])
        rows.append(
            {
                "schema_version": SCHEMA_VERSION,
                "run_id": RUN_ID,
                "recipe_id": RECIPE_ID,
                "variant_id": variant_id,
                "market": market,
                "timeframe": timeframe,
                "trade_id": f"{RECIPE_ID}:{variant_id}:{market}:{timeframe}:{open_idx}",
                "open_date": open_ts.isoformat(),
                "close_date": close_ts.isoformat(),
                "open_session_date": pd.Timestamp(session_dates[open_idx]).date().isoformat(),
                "source_anchor": SOURCE_TICKER,
                "parent_regime_root": root,
                "parent_regime_confidence_floor": float(floors[open_idx]),
                "source_ticker_confidence": float(conf[open_idx]),
                "source_ticker_vix": float(vix[open_idx]),
                "manipulation_overlay_state": "not_consumed_no_direct_event_rows",
                "sub_regime_tags": fields["sub_regime_tags"],
                "sub_sub_regime_or_profit_factor": fields["sub_sub_regime_or_profit_factor"],
                "profit_factor_family": fields["profit_factor_family"],
                "profit_factor_leaf": f"{RECIPE_ID}:{variant_id}",
                "regime_profit_branch_path": branch_path(root, variant_id),
                "regime_profit_branch_path_version": SCHEMA_VERSION,
                "trade_or_bar_horizon": f"{timeframe}_hold_{hold}",
                "allowed_action": fields["allowed_action"],
                "suppression_rule": fields["suppression_rule"],
                "direction": "long" if int(direction[pos]) > 0 else "short",
                "direction_sign": int(direction[pos]),
                "entry_close": float(entry[pos]),
                "exit_close": float(exit_price[pos]),
                "gross_return": float(gross[pos]),
                "roundtrip_cost": cost,
                "profit_ratio_net": float(pnl[pos]),
                "year_fold": int(open_ts.year),
                "root_lookup_status": str(lookup_status[open_idx]),
            }
        )
    return rows


def make_report_writer(module: Any):
    def write_report(report: dict[str, Any]) -> None:
        decision = report["decision"]
        branch_lines = [
            "| Root | Selected Variant | Trades | Folds | Min Fold Trades | Fold Positive Rate | LCB 5% | PBO | DSR | RC-SPA | Gate |",
            "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|",
        ]
        for row in report["branch_summaries"]:
            branch_lines.append(
                f"| {row['parent_regime_root']} | `{row['selected_variant_id']}` | "
                f"{row['total_trades']} | {row['test_folds']} | "
                f"{row['min_trades_per_test_fold']} | {row['fold_positive_rate']:.4f} | "
                f"{row['bootstrap_edge_lcb_5pct']:.6f} | {row['pbo']:.3f} | "
                f"{row['dsr']:.4f} | {row['rc_spa']:.4f} | `{row['hard_gate_result']}` |"
            )
        lines = [
            "# Stock Panel Root-Hedge RC-SPA v1",
            "",
            f"Run id: `{RUN_ID}`.",
            "",
            "## Decision",
            "",
            f"- Gate result: `{decision['gate_result']}`",
            f"- Stable profit score: `{decision['stable_profit_score']:.4f}`",
            f"- Variant rows: `{decision['variant_trade_rows']}`",
            f"- Selected rows: `{decision['selected_trade_rows']}`",
            f"- Branch paths passed: `{decision['branch_paths_passed']}/{decision['branch_paths_evaluated']}`",
            f"- Selected root counts: `{decision['selected_root_trade_counts']}`",
            f"- Downstream consumption: `{decision['downstream_consumption']}`",
            f"- Primary blocker: {decision['primary_blocker']}",
            "",
            "## Branch Summary",
            "",
            *branch_lines,
            "",
            "## Inputs",
            "",
            f"- Local Auto-Quant feathers: `{DATA_DIR}`",
            f"- Board A consumer map: `{module.rel(module.BOARD_A_CONSUMER_MAP)}`",
            f"- Source root schedule: `{module.SOURCE_REGIME_CSV}` / `{SOURCE_TICKER}`",
            "- Panel: SPY, QQQ, IWM, DIA, GLD across 1h/4h plus SPY/QQQ/ES/AAPL daily where available.",
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

    return write_report


def patch_module(module: Any) -> None:
    module.RUN_ID = RUN_ID
    module.SCHEMA_VERSION = SCHEMA_VERSION
    module.RECIPE_ID = RECIPE_ID
    module.SOURCE_TICKER = SOURCE_TICKER
    module.RUN_ROOT = RUN_ROOT
    module.OUT_DIR = RUN_ROOT / "branch-rc-spa"
    module.CHECK_DIR = RUN_ROOT / "checks"
    module.FAIL_CLOSED_DIR = RUN_ROOT / "ict-engine-fail-closed"
    module.ALL_ROWS_CSV = module.OUT_DIR / "stock_panel_root_hedge_variant_rows_v1.csv"
    module.SELECTED_ROWS_CSV = module.OUT_DIR / "stock_panel_root_hedge_selected_rows_v1.csv"
    module.SUMMARY_CSV = module.OUT_DIR / "stock_panel_root_hedge_branch_summary_v1.csv"
    module.PANEL_SUMMARY_CSV = module.OUT_DIR / "stock_panel_root_hedge_panel_summary_v1.csv"
    module.REPORT_JSON = module.OUT_DIR / "stock_panel_root_hedge_rc_spa_report_v1.json"
    module.REPORT_MD = module.OUT_DIR / "stock_panel_root_hedge_rc_spa_report_v1.md"
    module.ASSERTIONS = module.CHECK_DIR / "stock_panel_root_hedge_v1_assertions.out"
    module.FAIL_CLOSED_MD = module.FAIL_CLOSED_DIR / "stock_panel_root_hedge_fail_closed_summary_v1.md"
    module.START = pd.Timestamp("2023-01-01", tz="UTC")
    module.END = pd.Timestamp("2026-01-31", tz="UTC")
    module.PANELS = [
        ("SPY/USD", "1h", DATA_DIR / "SPY_USD-1h.feather"),
        ("QQQ/USD", "1h", DATA_DIR / "QQQ_USD-1h.feather"),
        ("IWM/USD", "1h", DATA_DIR / "IWM_USD-1h.feather"),
        ("DIA/USD", "1h", DATA_DIR / "DIA_USD-1h.feather"),
        ("GLD/USD", "1h", DATA_DIR / "GLD_USD-1h.feather"),
        ("SPY/USD", "4h", DATA_DIR / "SPY_USD-4h.feather"),
        ("QQQ/USD", "4h", DATA_DIR / "QQQ_USD-4h.feather"),
        ("IWM/USD", "4h", DATA_DIR / "IWM_USD-4h.feather"),
        ("DIA/USD", "4h", DATA_DIR / "DIA_USD-4h.feather"),
        ("GLD/USD", "4h", DATA_DIR / "GLD_USD-4h.feather"),
        ("SPY/USD", "1d", DATA_DIR / "SPY_USD-1d.feather"),
        ("QQQ/USD", "1d", DATA_DIR / "QQQ_USD-1d.feather"),
        ("ES/USD", "1d", DATA_DIR / "ES_USD-1d.feather"),
        ("AAPL/USD", "1d", DATA_DIR / "AAPL_USD-1d.feather"),
    ]
    module.VARIANTS = [
        {"variant_id": "risk_on_momentum_fast", "mode": "risk_on_momentum", "lookback": 5, "ema": 20, "z": 0.9, "hold": {"1h": 8, "4h": 5, "1d": 5}},
        {"variant_id": "risk_on_pullback_slow", "mode": "risk_on_pullback", "lookback": 10, "ema": 50, "z": 0.8, "hold": {"1h": 10, "4h": 6, "1d": 7}},
        {"variant_id": "bear_equity_short_hedge", "mode": "equity_short_hedge", "lookback": 10, "ema": 20, "z": 0.9, "hold": {"1h": 10, "4h": 6, "1d": 6}},
        {"variant_id": "bear_failed_rally_short", "mode": "failed_rally_short", "lookback": 5, "ema": 50, "z": 0.75, "hold": {"1h": 8, "4h": 5, "1d": 5}},
        {"variant_id": "gold_defensive_long", "mode": "gold_defensive_long", "lookback": 10, "ema": 20, "z": 0.8, "hold": {"1h": 12, "4h": 6, "1d": 8}},
        {"variant_id": "sideways_range_reversion", "mode": "range_reversion", "lookback": 5, "ema": 20, "z": 0.85, "hold": {"1h": 7, "4h": 4, "1d": 4}},
        {"variant_id": "sideways_breakout_failure", "mode": "range_breakout_failure", "lookback": 5, "ema": 20, "z": 0.75, "hold": {"1h": 8, "4h": 5, "1d": 5}},
        {"variant_id": "sideways_microtrend_carry", "mode": "microtrend_carry", "lookback": 10, "ema": 50, "z": 0.65, "hold": {"1h": 8, "4h": 5, "1d": 5}},
        {"variant_id": "crisis_equity_tail_short", "mode": "crisis_equity_tail_short", "lookback": 3, "ema": 20, "z": 0.9, "hold": {"1h": 10, "4h": 6, "1d": 6}},
        {"variant_id": "crisis_gold_safehaven", "mode": "crisis_gold_safehaven", "lookback": 5, "ema": 20, "z": 0.8, "hold": {"1h": 12, "4h": 6, "1d": 8}},
        {"variant_id": "crisis_relief_rebound", "mode": "crisis_relief_rebound", "lookback": 3, "ema": 20, "z": 1.2, "hold": {"1h": 8, "4h": 5, "1d": 5}},
    ]
    module.branch_path = branch_path
    module.branch_fields = branch_fields
    module.write_report = make_report_writer(module)

    def build_trade_rows(df: pd.DataFrame, variant: dict[str, Any]) -> list[dict[str, Any]]:
        return _build_trade_rows(module, df, variant)

    module.build_trade_rows = build_trade_rows


def postprocess_outputs(module: Any) -> None:
    if not module.REPORT_JSON.exists():
        return
    report = module.json.loads(module.REPORT_JSON.read_text(encoding="utf-8"))
    report["decision"]["next_action"] = (
        "B2R-repeat: StockPanelRootHedgeV1 failed all required branch gates; "
        "use a broader crisis-bearing provider panel or source executable scoped "
        "Manipulation PnL rows before any downstream promotion."
    )
    report["decision"]["primary_blocker"] = str(report["decision"]["primary_blocker"]).replace(
        "RootTransitionTriad", RECIPE_ID
    )
    module.write_json(module.REPORT_JSON, report)
    module.write_report(report)
    fail_closed = module.FAIL_CLOSED_MD.read_text(encoding="utf-8") if module.FAIL_CLOSED_MD.exists() else ""
    fail_closed = fail_closed.replace("Root Transition Triad", "Stock Panel Root-Hedge")
    fail_closed = fail_closed.replace("RootTransitionTriad", RECIPE_ID)
    fail_closed = fail_closed.replace(
        "direct Manipulation still needs trade/PnL rows, and failed roots need a different family or provider panel without relaxing RC-SPA.",
        "the stock/ETF hedge panel still lacks Crisis and scoped Manipulation branch rows, and failed roots need a broader provider panel without relaxing RC-SPA.",
    )
    module.FAIL_CLOSED_MD.write_text(fail_closed, encoding="utf-8")


def main() -> int:
    module = load_base_module()
    patch_module(module)
    status = int(module.main())
    postprocess_outputs(module)
    return status


if __name__ == "__main__":
    raise SystemExit(main())
