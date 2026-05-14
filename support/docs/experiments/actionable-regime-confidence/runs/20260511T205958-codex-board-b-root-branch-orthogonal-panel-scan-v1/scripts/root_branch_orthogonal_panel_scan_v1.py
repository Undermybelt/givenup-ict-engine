#!/usr/bin/env python3
"""Board B root-branch orthogonal panel scan.

This is a run-local repair for the active 205958 cursor. It consumes existing
local Auto-Quant feather panels, attaches the accepted Board A root schedule,
and keeps the downstream stages fail-closed unless Bull/Bear/Sideways/Crisis
all pass unchanged RC-SPA gates. The scoped Manipulation component is not
rescored here; it is referenced only as the existing 205047 component pass.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


RUN_ID = "20260511T205958+0800-codex-board-b-root-branch-orthogonal-panel-scan-v1"
SCHEMA_VERSION = "board-b-root-branch-orthogonal-panel-scan/v1"
RECIPE_ID = "RootBranchOrthogonalPanelScanV1"
SOURCE_TICKER = "^IXIC"

RUN_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = next(path for path in [RUN_ROOT, *RUN_ROOT.parents] if (path / "Cargo.toml").exists())
DATA_DIR = Path("/Users/thrill3r/Auto-Quant/user_data/data")
BASE_SCRIPT = (
    REPO_ROOT
    / "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T193803-codex-board-b-root-transition-triad-clean-v1/scripts/"
    "board_b_root_transition_triad_clean_v1.py"
)


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


def _is_crypto(market: str) -> bool:
    return "USDT" in market or market.startswith("BTCY")


def _is_equity_risk(market: str) -> bool:
    return any(market.startswith(prefix) for prefix in ("NQ", "QQQ", "SPY", "IWM", "DIA", "ES", "AAPL"))


def _is_defensive(market: str) -> bool:
    return market.startswith(("GLD", "EUR"))


def branch_path(root: str, variant_id: str) -> str:
    if root == "Bull":
        return f"{root} -> OrthogonalRiskOn -> MultiAssetMomentumOrCarry -> {RECIPE_ID}:{variant_id}"
    if root == "Bear":
        return f"{root} -> OrthogonalRiskOff -> DefensiveHedgeOrShort -> {RECIPE_ID}:{variant_id}"
    if root == "Sideways":
        return f"{root} -> OrthogonalRange -> CompressionReversionOrBreakoutFailure -> {RECIPE_ID}:{variant_id}"
    if root == "Crisis":
        return f"{root} -> OrthogonalStress -> TailHedgeOrPanicReversal -> {RECIPE_ID}:{variant_id}"
    return "Manipulation(scoped) -> DirectEventOverlayPassedSeparately -> stop_take_profit_grid -> ManipulationStopTakeProfitGridV2"


def branch_fields(root: str) -> dict[str, str]:
    if root == "Bull":
        return {
            "sub_regime_tags": "OrthogonalRiskOn",
            "sub_sub_regime_or_profit_factor": "MultiAssetMomentumOrCarry",
            "profit_factor_family": "orthogonal_panel_scan",
            "allowed_action": "long_research_only_until_branch_rc_spa_passes",
            "suppression_rule": "suppress_if_bull_orthogonal_panel_branch_rc_spa_fails",
        }
    if root == "Bear":
        return {
            "sub_regime_tags": "OrthogonalRiskOff",
            "sub_sub_regime_or_profit_factor": "DefensiveHedgeOrShort",
            "profit_factor_family": "orthogonal_panel_scan",
            "allowed_action": "short_or_defensive_research_only_until_branch_rc_spa_passes",
            "suppression_rule": "suppress_if_bear_orthogonal_panel_branch_rc_spa_fails",
        }
    if root == "Sideways":
        return {
            "sub_regime_tags": "OrthogonalRange",
            "sub_sub_regime_or_profit_factor": "CompressionReversionOrBreakoutFailure",
            "profit_factor_family": "orthogonal_panel_scan",
            "allowed_action": "long_short_research_only_until_branch_rc_spa_passes",
            "suppression_rule": "suppress_if_sideways_orthogonal_panel_branch_rc_spa_fails",
        }
    if root == "Crisis":
        return {
            "sub_regime_tags": "OrthogonalStress",
            "sub_sub_regime_or_profit_factor": "TailHedgeOrPanicReversal",
            "profit_factor_family": "orthogonal_panel_scan",
            "allowed_action": "short_or_defensive_research_only_until_branch_rc_spa_passes",
            "suppression_rule": "tail_guard_blocks_crisis_orthogonal_panel_branch_if_rc_spa_fails",
        }
    return {
        "sub_regime_tags": "DirectEventOverlayPassedSeparately",
        "sub_sub_regime_or_profit_factor": "stop_take_profit_grid",
        "profit_factor_family": "direct_manipulation_overlay",
        "allowed_action": "component_pass_not_downstream_ready",
        "suppression_rule": "requires_all_price_roots_before_downstream",
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
    risk_asset = _is_equity_risk(market) or _is_crypto(market)
    crypto = _is_crypto(market)
    defensive = _is_defensive(market)
    low_slope = np.abs(ema20_slope) < np.maximum(0.003, atr_pct * 0.35)
    signal = np.zeros(len(df), dtype=np.int8)

    bull = roots == "Bull"
    if mode == "risk_on_momentum":
        signal[bull & risk_asset & (trend > np.maximum(0.0008, atr_pct * 0.12)) & (close > ema_value)] = 1
    elif mode == "risk_on_pullback":
        signal[bull & risk_asset & (z20 <= -z_threshold) & (close > ema50) & (ret1 > -0.012)] = 1
    elif mode == "crypto_carry":
        signal[bull & crypto & (trend > 0) & (close > ema20) & (z20 < 1.8)] = 1

    bear = roots == "Bear"
    if mode == "risk_off_short":
        signal[bear & risk_asset & (trend < -np.maximum(0.0008, atr_pct * 0.16)) & (close < ema_value)] = -1
    elif mode == "failed_rally_short":
        signal[bear & risk_asset & (z20 >= z_threshold) & (ret1 < 0) & (close < ema50)] = -1
    elif mode == "defensive_long":
        signal[bear & defensive & (trend > np.maximum(0.0004, atr_pct * 0.08)) & (close > ema20)] = 1

    sideways = roots == "Sideways"
    if mode == "range_reversion":
        signal[sideways & low_slope & (z20 >= z_threshold)] = -1
        signal[sideways & low_slope & (z20 <= -z_threshold)] = 1
    elif mode == "breakout_failure":
        signal[sideways & low_slope & (close > high20_prev) & (ret1 < 0)] = -1
        signal[sideways & low_slope & (close < low20_prev) & (ret1 > 0)] = 1
    elif mode == "compression_carry":
        threshold = np.maximum(0.0006, atr_pct * 0.12)
        signal[sideways & low_slope & risk_asset & (trend > threshold) & (close > ema20)] = 1
        signal[sideways & low_slope & risk_asset & (trend < -threshold) & (close < ema20)] = -1

    crisis = roots == "Crisis"
    if mode == "crisis_tail_short":
        signal[
            crisis
            & risk_asset
            & ((trend < -np.maximum(0.001, atr_pct * 0.18)) | (ret3 < -np.maximum(0.0025, atr_pct * 0.80)))
            & ((close < ema_value) | (vix >= 24))
        ] = -1
    elif mode == "crisis_defensive_long":
        signal[crisis & defensive & ((trend > 0) | (close > ema20))] = 1
    elif mode == "panic_reversal":
        panic = risk_asset & ((z20 <= -max(1.1, z_threshold)) | (ret3 <= -np.maximum(0.005, atr_pct)))
        signal[crisis & panic & (ret1 > 0) & (vix < 55)] = 1

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
                "manipulation_overlay_state": "component_pass_from_205047_not_rescored_here",
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
            "# Root Branch Orthogonal Panel Scan RC-SPA v1",
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
            "- Panel: multi-asset local Auto-Quant feathers across NQ, equity ETFs, crypto, GLD, EUR, ES, AAPL, and BTCY where available.",
            "- Scoped Manipulation component: existing `20260511T205047` stop/take-profit grid pass; not consumed downstream by this root-only scan.",
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
    module.ALL_ROWS_CSV = module.OUT_DIR / "root_branch_orthogonal_panel_scan_variant_rows_v1.csv"
    module.SELECTED_ROWS_CSV = module.OUT_DIR / "root_branch_orthogonal_panel_scan_selected_rows_v1.csv"
    module.SUMMARY_CSV = module.OUT_DIR / "root_branch_orthogonal_panel_scan_branch_summary_v1.csv"
    module.PANEL_SUMMARY_CSV = module.OUT_DIR / "root_branch_orthogonal_panel_scan_panel_summary_v1.csv"
    module.REPORT_JSON = module.OUT_DIR / "root_branch_orthogonal_panel_scan_rc_spa_report_v1.json"
    module.REPORT_MD = module.OUT_DIR / "root_branch_orthogonal_panel_scan_rc_spa_report_v1.md"
    module.ASSERTIONS = module.CHECK_DIR / "root_branch_orthogonal_panel_scan_v1_assertions.out"
    module.FAIL_CLOSED_MD = module.FAIL_CLOSED_DIR / "root_branch_orthogonal_panel_scan_fail_closed_summary_v1.md"
    module.START = pd.Timestamp("2016-01-01", tz="UTC")
    module.END = pd.Timestamp("2026-01-31", tz="UTC")
    module.PANELS = [
        ("NQ/USD", "15m", DATA_DIR / "NQ_USD-15m.feather"),
        ("NQ/USD", "1h", DATA_DIR / "NQ_USD-1h.feather"),
        ("NQ/USD", "4h", DATA_DIR / "NQ_USD-4h.feather"),
        ("QQQ/USD", "1h", DATA_DIR / "QQQ_USD-1h.feather"),
        ("QQQ/USD", "4h", DATA_DIR / "QQQ_USD-4h.feather"),
        ("SPY/USD", "1h", DATA_DIR / "SPY_USD-1h.feather"),
        ("SPY/USD", "4h", DATA_DIR / "SPY_USD-4h.feather"),
        ("IWM/USD", "1h", DATA_DIR / "IWM_USD-1h.feather"),
        ("DIA/USD", "1h", DATA_DIR / "DIA_USD-1h.feather"),
        ("GLD/USD", "1h", DATA_DIR / "GLD_USD-1h.feather"),
        ("GLD/USD", "4h", DATA_DIR / "GLD_USD-4h.feather"),
        ("BTC/USDT", "1h", DATA_DIR / "BTC_USDT-1h.feather"),
        ("BTC/USDT", "4h", DATA_DIR / "BTC_USDT-4h.feather"),
        ("ETH/USDT", "1h", DATA_DIR / "ETH_USDT-1h.feather"),
        ("ETH/USDT", "4h", DATA_DIR / "ETH_USDT-4h.feather"),
        ("BNB/USDT", "1h", DATA_DIR / "BNB_USDT-1h.feather"),
        ("SOL/USDT", "1h", DATA_DIR / "SOL_USDT-1h.feather"),
        ("AVAX/USDT", "1h", DATA_DIR / "AVAX_USDT-1h.feather"),
        ("SPY/USD", "1d", DATA_DIR / "SPY_USD-1d.feather"),
        ("QQQ/USD", "1d", DATA_DIR / "QQQ_USD-1d.feather"),
        ("ES/USD", "1d", DATA_DIR / "ES_USD-1d.feather"),
        ("AAPL/USD", "1d", DATA_DIR / "AAPL_USD-1d.feather"),
        ("BTCY/USD", "1d", DATA_DIR / "BTCY_USD-1d.feather"),
        ("EUR/USD", "1d", DATA_DIR / "EUR_USD-1d.feather"),
    ]
    module.VARIANTS = [
        {"variant_id": "bull_risk_on_momentum_fast", "mode": "risk_on_momentum", "lookback": 5, "ema": 20, "z": 0.9, "hold": {"15m": 12, "1h": 8, "4h": 5, "1d": 5}},
        {"variant_id": "bull_risk_on_pullback", "mode": "risk_on_pullback", "lookback": 10, "ema": 50, "z": 0.8, "hold": {"15m": 16, "1h": 10, "4h": 6, "1d": 7}},
        {"variant_id": "bull_crypto_carry", "mode": "crypto_carry", "lookback": 20, "ema": 50, "z": 1.2, "hold": {"15m": 16, "1h": 12, "4h": 6, "1d": 7}},
        {"variant_id": "bear_risk_off_short", "mode": "risk_off_short", "lookback": 10, "ema": 20, "z": 0.9, "hold": {"15m": 16, "1h": 10, "4h": 6, "1d": 6}},
        {"variant_id": "bear_failed_rally_short", "mode": "failed_rally_short", "lookback": 5, "ema": 50, "z": 0.75, "hold": {"15m": 12, "1h": 8, "4h": 5, "1d": 5}},
        {"variant_id": "bear_defensive_long", "mode": "defensive_long", "lookback": 10, "ema": 20, "z": 0.8, "hold": {"15m": 16, "1h": 12, "4h": 6, "1d": 8}},
        {"variant_id": "sideways_range_reversion", "mode": "range_reversion", "lookback": 5, "ema": 20, "z": 0.85, "hold": {"15m": 10, "1h": 7, "4h": 4, "1d": 4}},
        {"variant_id": "sideways_breakout_failure", "mode": "breakout_failure", "lookback": 5, "ema": 20, "z": 0.75, "hold": {"15m": 12, "1h": 8, "4h": 5, "1d": 5}},
        {"variant_id": "sideways_compression_carry", "mode": "compression_carry", "lookback": 10, "ema": 50, "z": 0.65, "hold": {"15m": 12, "1h": 8, "4h": 5, "1d": 5}},
        {"variant_id": "crisis_tail_short", "mode": "crisis_tail_short", "lookback": 3, "ema": 20, "z": 0.9, "hold": {"15m": 16, "1h": 10, "4h": 6, "1d": 6}},
        {"variant_id": "crisis_defensive_long", "mode": "crisis_defensive_long", "lookback": 5, "ema": 20, "z": 0.8, "hold": {"15m": 16, "1h": 12, "4h": 6, "1d": 8}},
        {"variant_id": "crisis_panic_reversal", "mode": "panic_reversal", "lookback": 3, "ema": 20, "z": 1.1, "hold": {"15m": 12, "1h": 8, "4h": 5, "1d": 5}},
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
    report = json.loads(module.REPORT_JSON.read_text(encoding="utf-8"))
    decision = report["decision"]
    if decision["branch_paths_passed"] == 4:
        decision["next_action"] = (
            "Combine these four root branches with the existing 205047 scoped Manipulation "
            "component, then run Pre-Bayes -> BBN -> CatBoost/path-ranker -> execution-tree consumption."
        )
    else:
        decision["next_action"] = (
            "Keep Board B in research_watch/fail-closed: this root-only scan did not produce "
            "passing Bull/Bear/Sideways/Crisis roots under unchanged RC-SPA, so do not combine "
            "it with the 205047 Manipulation component for downstream promotion."
        )
    module.write_json(module.REPORT_JSON, report)
    module.write_report(report)
    fail_closed = module.FAIL_CLOSED_MD.read_text(encoding="utf-8") if module.FAIL_CLOSED_MD.exists() else ""
    fail_closed = fail_closed.replace("Root Transition Triad", "Root Branch Orthogonal Panel Scan")
    fail_closed = fail_closed.replace("RootTransitionTriad", RECIPE_ID)
    module.FAIL_CLOSED_MD.write_text(fail_closed, encoding="utf-8")


def main() -> int:
    module = load_base_module()
    patch_module(module)
    status = int(module.main())
    postprocess_outputs(module)
    return status


if __name__ == "__main__":
    raise SystemExit(main())
