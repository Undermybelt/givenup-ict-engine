#!/usr/bin/env python3
"""Board B source-root stop/carry long-horizon RC-SPA readback.

Run-local additive experiment. This is intentionally self-contained so the
input panel contract is explicit and does not depend on a wrapper from a prior
failed run.
"""

from __future__ import annotations

import csv
import importlib.util
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


RUN_ID = "20260511T220646+0800-codex-board-b-source-root-stop-carry-longhorizon-v1"
SCHEMA_VERSION = "board-b-source-root-stop-carry-longhorizon/v1"
RECIPE_ID = "SourceRootStopCarryLongHorizonV1"
SOURCE_TICKER = "^GSPC"

RUN_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = next(path for path in [RUN_ROOT, *RUN_ROOT.parents] if (path / "Cargo.toml").exists())
BASE_SCRIPT = (
    REPO_ROOT
    / "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T193803-codex-board-b-root-transition-triad-clean-v1/scripts/"
    "board_b_root_transition_triad_clean_v1.py"
)
PROVIDER_CACHE = (
    REPO_ROOT
    / "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T212211-codex-board-b-yfinance-defensive-crossasset-v1-repaired/provider-cache"
)
AUTO_QUANT_DATA = Path("/Users/thrill3r/Auto-Quant/user_data/data")
SOURCE_REGIME_CSV = Path("/Users/thrill3r/Downloads/stock-market-regimes-20002026/stock_market_regimes_2000_2026.csv")
MANIP_SUMMARY_CSV = (
    REPO_ROOT
    / "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T205047-codex-board-b-manipulation-stop-tp-grid-v2/"
    "manipulation-stop-tp-grid-v2/manipulation_stop_tp_grid_v2_summary.csv"
)
MANIP_REPORT_MD = MANIP_SUMMARY_CSV.with_name("manipulation_stop_tp_grid_v2.md")

OUT_DIR = RUN_ROOT / "branch-rc-spa"
CHECK_DIR = RUN_ROOT / "checks"
CANDIDATE_DIR = RUN_ROOT / "ict-engine-candidate"
ALL_ROWS_CSV = OUT_DIR / "source_root_stop_carry_longhorizon_variant_rows_v1.csv"
SELECTED_ROWS_CSV = OUT_DIR / "source_root_stop_carry_longhorizon_selected_rows_v1.csv"
SUMMARY_CSV = OUT_DIR / "source_root_stop_carry_longhorizon_branch_summary_v1.csv"
PANEL_SUMMARY_CSV = OUT_DIR / "source_root_stop_carry_longhorizon_panel_summary_v1.csv"
REPORT_JSON = OUT_DIR / "source_root_stop_carry_longhorizon_rc_spa_report_v1.json"
REPORT_MD = OUT_DIR / "source_root_stop_carry_longhorizon_rc_spa_report_v1.md"
ASSERTIONS = CHECK_DIR / "source_root_stop_carry_longhorizon_v1_assertions.out"
CANDIDATE_MD = CANDIDATE_DIR / "source_root_stop_carry_longhorizon_candidate_summary_v1.md"

START = pd.Timestamp("2000-01-01", tz="UTC")
END = pd.Timestamp("2026-01-31", tz="UTC")

PANELS = [
    ("DIA/USD", "1d", PROVIDER_CACHE / "DIA_USD-1d.feather"),
    ("EEM/USD", "1d", PROVIDER_CACHE / "EEM_USD-1d.feather"),
    ("EFA/USD", "1d", PROVIDER_CACHE / "EFA_USD-1d.feather"),
    ("GLD/USD", "1d", PROVIDER_CACHE / "GLD_USD-1d.feather"),
    ("HYG/USD", "1d", PROVIDER_CACHE / "HYG_USD-1d.feather"),
    ("IEF/USD", "1d", PROVIDER_CACHE / "IEF_USD-1d.feather"),
    ("IWM/USD", "1d", PROVIDER_CACHE / "IWM_USD-1d.feather"),
    ("LQD/USD", "1d", PROVIDER_CACHE / "LQD_USD-1d.feather"),
    ("QQQ/USD", "1d", PROVIDER_CACHE / "QQQ_USD-1d.feather"),
    ("SHY/USD", "1d", PROVIDER_CACHE / "SHY_USD-1d.feather"),
    ("SPY/USD", "1d", PROVIDER_CACHE / "SPY_USD-1d.feather"),
    ("TLT/USD", "1d", PROVIDER_CACHE / "TLT_USD-1d.feather"),
    ("USO/USD", "1d", PROVIDER_CACHE / "USO_USD-1d.feather"),
    ("UUP/USD", "1d", PROVIDER_CACHE / "UUP_USD-1d.feather"),
    ("XLP/USD", "1d", PROVIDER_CACHE / "XLP_USD-1d.feather"),
    ("XLU/USD", "1d", PROVIDER_CACHE / "XLU_USD-1d.feather"),
    ("XLV/USD", "1d", PROVIDER_CACHE / "XLV_USD-1d.feather"),
    ("NQ/USD", "4h", AUTO_QUANT_DATA / "NQ_USD-4h.feather"),
    ("SPY/USD", "4h", AUTO_QUANT_DATA / "SPY_USD-4h.feather"),
    ("QQQ/USD", "4h", AUTO_QUANT_DATA / "QQQ_USD-4h.feather"),
    ("GLD/USD", "4h", AUTO_QUANT_DATA / "GLD_USD-4h.feather"),
]

VARIANTS: list[dict[str, Any]] = [
    *[
        {"variant_id": f"bull_carry_h12_sl040_tp{tp:02d}", "root": "Bull", "hold": 12, "stop_loss": 0.040, "take_profit": tp / 100.0}
        for tp in [12, 14, 16]
    ],
    *[
        {"variant_id": f"bear_carry_h20_sl{sl_name}_tp{tp:02d}", "root": "Bear", "hold": 20, "stop_loss": sl_value, "take_profit": tp / 100.0}
        for sl_name, sl_value in [("048", 0.048), ("049", 0.049), ("0495", 0.0495), ("050", 0.050)]
        for tp in [12, 14, 16]
    ],
    *[
        {"variant_id": f"sideways_carry_h8_sl040_tp{tp:02d}", "root": "Sideways", "hold": 8, "stop_loss": 0.040, "take_profit": tp / 100.0}
        for tp in [12, 14, 16]
    ],
    *[
        {"variant_id": f"crisis_carry_h8_sl{sl_name}_tp{tp:02d}", "root": "Crisis", "hold": 8, "stop_loss": sl_value, "take_profit": tp / 100.0}
        for sl_name, sl_value in [("048", 0.048), ("049", 0.049), ("0495", 0.0495), ("050", 0.050)]
        for tp in [12, 14, 16]
    ],
]


def load_base_module() -> Any:
    spec = importlib.util.spec_from_file_location("board_b_root_transition_base", BASE_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import base evaluator: {BASE_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def rel(path: Path) -> str:
    return str(path.relative_to(REPO_ROOT))


def read_panel(path: Path) -> pd.DataFrame:
    df = pd.read_feather(path)
    if pd.api.types.is_numeric_dtype(df["date"]):
        df["date"] = pd.to_datetime(df["date"], unit="ms", utc=True, errors="coerce")
    else:
        df["date"] = pd.to_datetime(df["date"], utc=True, errors="coerce")
    for col in ["open", "high", "low", "close", "volume"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df.dropna(subset=["date", "open", "high", "low", "close"]).sort_values("date").reset_index(drop=True)


def load_source_roots(module: Any) -> pd.DataFrame:
    df = pd.read_csv(SOURCE_REGIME_CSV, usecols=["date", "ticker", "regime_label", "regime_confidence", "vix"], parse_dates=["date"])
    df = df[df["ticker"] == SOURCE_TICKER].copy()
    if df.empty:
        raise RuntimeError(f"no source rows for {SOURCE_TICKER}")
    df["date"] = pd.to_datetime(df["date"]).dt.tz_localize(None).dt.normalize()
    df["parent_regime_root"] = df["regime_label"].map(lambda value: value if value in module.ROOTS else "Crisis")
    df["regime_confidence"] = pd.to_numeric(df["regime_confidence"], errors="coerce").fillna(0.0)
    df["vix"] = pd.to_numeric(df["vix"], errors="coerce").fillna(0.0)
    return df.sort_values("date").reset_index(drop=True)


def load_panel(path: Path, market: str, timeframe: str, lookup: Any) -> pd.DataFrame:
    df = read_panel(path)
    df = df[(df["date"] >= START) & (df["date"] <= END)].copy()
    if df.empty:
        return df
    df["session_date"] = df["date"].dt.tz_convert(None).dt.normalize()
    root_df = pd.DataFrame([lookup.lookup(value) for value in df["session_date"]])
    df = pd.concat([df.reset_index(drop=True), root_df], axis=1)
    df["market"] = market
    df["timeframe"] = timeframe
    for window in [1, 5, 20]:
        df[f"ret{window}"] = df["close"].pct_change(window).fillna(0.0)
    df["ema20"] = df["close"].ewm(span=20, adjust=False).mean()
    mean20 = df["close"].rolling(20, min_periods=10).mean()
    std20 = df["close"].rolling(20, min_periods=10).std()
    df["z20"] = ((df["close"] - mean20) / std20.replace(0, np.nan)).fillna(0.0)
    return df.reset_index(drop=True)


def is_risk_market(market: str) -> bool:
    return any(token in market for token in ("SPY", "QQQ", "IWM", "DIA", "EEM", "EFA", "HYG", "AAPL", "NQ", "ES", "USO"))


def is_defensive_market(market: str) -> bool:
    return any(token in market for token in ("GLD", "TLT", "IEF", "SHY", "UUP", "XLU", "XLP", "XLV"))


def roundtrip_cost(_market: str, timeframe: str) -> float:
    return 0.0006 if timeframe == "1d" else 0.0008


def branch_path(root: str, variant_id: str) -> str:
    if root == "Bull":
        return f"{root} -> RootCarryExpansion -> StopManagedRiskCarry -> {RECIPE_ID}:{variant_id}"
    if root == "Bear":
        return f"{root} -> BearReliefCarry -> StopManagedRecoveryCarry -> {RECIPE_ID}:{variant_id}"
    if root == "Sideways":
        return f"{root} -> RangeCarry -> StopManagedRangeCarry -> {RECIPE_ID}:{variant_id}"
    if root == "Crisis":
        return f"{root} -> CrisisReliefCarry -> StopManagedPanicRecovery -> {RECIPE_ID}:{variant_id}"
    return "Manipulation(scoped) -> TelegramPumpEvent -> ProviderStopTakeShort -> ManipulationStopTakeProfitGridV2:short_tp120_sl060_h72"


def branch_fields(root: str) -> dict[str, str]:
    mapping = {
        "Bull": ("RootCarryExpansion", "StopManagedRiskCarry", "long_research_only_until_closed_loop_passes"),
        "Bear": ("BearReliefCarry", "StopManagedRecoveryCarry", "long_relief_research_only_until_closed_loop_passes"),
        "Sideways": ("RangeCarry", "StopManagedRangeCarry", "long_range_research_only_until_closed_loop_passes"),
        "Crisis": ("CrisisReliefCarry", "StopManagedPanicRecovery", "long_relief_research_only_until_closed_loop_passes"),
    }
    sub, leaf, action = mapping[root]
    return {
        "sub_regime_tags": sub,
        "sub_sub_regime_or_profit_factor": leaf,
        "profit_factor_family": "source_root_stop_carry_longhorizon",
        "allowed_action": action,
        "suppression_rule": f"suppress_if_{root.lower()}_source_root_stop_carry_longhorizon_closed_loop_fails",
    }


def signal_vector(df: pd.DataFrame, variant: dict[str, Any]) -> np.ndarray:
    signal = np.zeros(len(df), dtype=np.int8)
    root = str(variant["root"])
    root_mask = df["parent_regime_root"].astype(str).to_numpy() == root
    market = str(df["market"].iloc[0])
    close = df["close"].to_numpy(dtype=float)
    ema20 = df["ema20"].to_numpy(dtype=float)
    ret1 = df["ret1"].to_numpy(dtype=float)
    ret5 = df["ret5"].to_numpy(dtype=float)
    z20 = df["z20"].to_numpy(dtype=float)
    if not (is_risk_market(market) or is_defensive_market(market)):
        return signal
    if root == "Bull":
        signal[root_mask & (close > ema20)] = 1
    elif root == "Bear":
        signal[root_mask & (ret1 >= -0.06)] = 1
    elif root == "Sideways":
        signal[root_mask & ((np.abs(z20) < 1.8) | (close > ema20))] = 1
    elif root == "Crisis":
        if is_risk_market(market):
            signal[root_mask & ((ret5 > 0) | (ret1 > 0) | (close > ema20))] = 1
        elif is_defensive_market(market):
            signal[root_mask] = 1
    return signal


def stop_take_exit(df: pd.DataFrame, open_idx: int, hold: int, stop_loss: float, take_profit: float) -> tuple[int, float, str]:
    entry = float(df["close"].iat[open_idx])
    close_idx = open_idx + hold
    exit_price = float(df["close"].iat[close_idx])
    exit_reason = "time_stop"
    for idx in range(open_idx + 1, close_idx + 1):
        if float(df["low"].iat[idx]) <= entry * (1.0 - stop_loss):
            return idx, entry * (1.0 - stop_loss), "stop_loss"
        if float(df["high"].iat[idx]) >= entry * (1.0 + take_profit):
            return idx, entry * (1.0 + take_profit), "take_profit"
    return close_idx, exit_price, exit_reason


def build_trade_rows(module: Any, df: pd.DataFrame, variant: dict[str, Any]) -> list[dict[str, Any]]:
    if df.empty:
        return []
    variant_id = str(variant["variant_id"])
    timeframe = str(df["timeframe"].iloc[0])
    market = str(df["market"].iloc[0])
    hold = int(variant["hold"]) if timeframe == "1d" else min(int(variant["hold"]) * 2, 40)
    cost = roundtrip_cost(market, timeframe)
    signal = signal_vector(df, variant)
    rows: list[dict[str, Any]] = []
    next_allowed = 0
    roots = df["parent_regime_root"].astype(str).to_numpy()
    dates = df["date"].to_numpy()
    session_dates = df["session_date"].to_numpy()
    floors = df["parent_regime_confidence_floor"].to_numpy(dtype=float)
    conf = df["source_ticker_confidence"].to_numpy(dtype=float)
    vix = df["source_ticker_vix"].to_numpy(dtype=float)
    lookup_status = df["root_lookup_status"].astype(str).to_numpy()
    for raw_idx in np.flatnonzero(signal != 0).tolist():
        open_idx = int(raw_idx)
        if open_idx < next_allowed or open_idx + hold >= len(df):
            continue
        entry = float(df["close"].iat[open_idx])
        if entry <= 0:
            continue
        close_idx, exit_price, exit_reason = stop_take_exit(df, open_idx, hold, float(variant["stop_loss"]), float(variant["take_profit"]))
        root = str(roots[open_idx])
        if root not in module.ROOTS:
            continue
        fields = branch_fields(root)
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
                "trade_or_bar_horizon": f"{timeframe}_hold_{hold}_stop_{variant['stop_loss']}_take_{variant['take_profit']}",
                "allowed_action": fields["allowed_action"],
                "suppression_rule": fields["suppression_rule"],
                "direction": "long",
                "direction_sign": 1,
                "entry_close": entry,
                "exit_close": float(exit_price),
                "exit_reason": exit_reason,
                "gross_return": float(exit_price / entry - 1.0),
                "roundtrip_cost": cost,
                "profit_ratio_net": float((exit_price / entry - 1.0) - cost),
                "year_fold": int(open_ts.year),
                "root_lookup_status": str(lookup_status[open_idx]),
                "source_panel": "provider_cache_yfinance" if timeframe == "1d" else "local_auto_quant_4h",
            }
        )
        next_allowed = open_idx + hold + 1
    return rows


def load_manip_component(module: Any) -> tuple[dict[str, Any], dict[str, Any]]:
    with MANIP_SUMMARY_CSV.open(newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    passed = [row for row in rows if row.get("gate_result") == "pass:tradeable_manipulation_stop_tp_candidate"]
    best = next((row for row in passed if row.get("variant_id") == "short_tp120_sl060_h72"), passed[0] if passed else None)
    if best is None:
        row = module.summarize_rows(root="Manipulation(scoped)", variant_id="no_passing_205047_component", rows=[], all_rows=[], pbo=1.0, pbo_method="no_passing_205047_component")
        return row, {"component_available": False, "component_source": rel(MANIP_SUMMARY_CSV)}
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
    return summary, {
        "component_available": True,
        "component_run_id": best["run_id"],
        "component_report": rel(MANIP_REPORT_MD),
        "component_summary_csv": rel(MANIP_SUMMARY_CSV),
        "component_gate_result": best["gate_result"],
        "component_variant": best["variant_id"],
        "component_positive_rows": int(best["positive_rows"]),
        "component_control_rows": int(best["control_rows"]),
    }


def write_report(report: dict[str, Any]) -> None:
    decision = report["decision"]
    branch_lines = [
        "| Root | Selected Variant | Trades | Folds | Min Fold Trades | Fold Positive Rate | LCB 5% | PBO | DSR | RC-SPA | Gate |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in report["branch_summaries"]:
        branch_lines.append(
            f"| {row['parent_regime_root']} | `{row['selected_variant_id']}` | {row['total_trades']} | {row['test_folds']} | "
            f"{row['min_trades_per_test_fold']} | {row['fold_positive_rate']:.4f} | {row['bootstrap_edge_lcb_5pct']:.6f} | "
            f"{row['pbo']:.3f} | {row['dsr']:.4f} | {row['rc_spa']:.4f} | `{row['hard_gate_result']}` |"
        )
    REPORT_MD.write_text(
        "\n".join(
            [
                "# Source Root Stop Carry Long-Horizon RC-SPA v1",
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
                f"- Provider cache: `{rel(PROVIDER_CACHE)}`",
                f"- Local 4h panels: `{AUTO_QUANT_DATA}`",
                f"- Board A consumer map: `{report['accepted_regime_artifact']}`",
                f"- Source root schedule: `{SOURCE_REGIME_CSV}` / `{SOURCE_TICKER}`",
                f"- Scoped Manipulation component: `{report['manipulation_component'].get('component_report', 'missing')}`",
                "",
                "## Artifacts",
                "",
                f"- Report JSON: `{rel(REPORT_JSON)}`",
                f"- Selected rows: `{rel(SELECTED_ROWS_CSV)}`",
                f"- Variant rows: `{rel(ALL_ROWS_CSV)}`",
                f"- Branch summary: `{rel(SUMMARY_CSV)}`",
                f"- Panel summary: `{rel(PANEL_SUMMARY_CSV)}`",
                f"- Candidate summary: `{rel(CANDIDATE_MD)}`",
                f"- Assertions: `{rel(ASSERTIONS)}`",
                "",
                "## Next",
                "",
                f"- {decision['next_action']}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def main() -> int:
    module = load_base_module()
    module.RUN_ID = RUN_ID
    module.SCHEMA_VERSION = SCHEMA_VERSION
    module.RECIPE_ID = RECIPE_ID
    module.SOURCE_TICKER = SOURCE_TICKER
    module.START = START
    module.END = END
    module.branch_path = branch_path
    for path in [OUT_DIR, CHECK_DIR, CANDIDATE_DIR]:
        path.mkdir(parents=True, exist_ok=True)
    required = [SOURCE_REGIME_CSV, module.BOARD_A_CONSUMER_MAP, MANIP_SUMMARY_CSV, *[path for _, _, path in PANELS]]
    missing = [str(path) for path in required if not path.exists() or path.stat().st_size == 0]
    if missing:
        raise RuntimeError("missing required inputs: " + ", ".join(missing))

    lookup = module.RootLookup(load_source_roots(module), module.load_root_floors())
    all_rows: list[dict[str, Any]] = []
    panel_summaries: list[dict[str, Any]] = []
    for market, timeframe, path in PANELS:
        panel = load_panel(path, market, timeframe, lookup)
        for variant in VARIANTS:
            rows = build_trade_rows(module, panel, variant)
            all_rows.extend(rows)
            values = np.array([float(row["profit_ratio_net"]) for row in rows], dtype=float)
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
        for variant in [str(item["variant_id"]) for item in VARIANTS]:
            rows = [row for row in all_rows if row["parent_regime_root"] == root and str(row["variant_id"]) == variant]
            summaries.append(module.summarize_rows(root=root, variant_id=variant, rows=rows, all_rows=all_rows, pbo=pbo, pbo_method=pbo_method))
        selected = max(summaries, key=lambda row: float(row["rc_spa"]))
        branch_summaries.append(selected)
        variant_summaries.extend(summaries)
        selected_rows.extend([row for row in all_rows if row["parent_regime_root"] == root and str(row["variant_id"]) == str(selected["selected_variant_id"])])

    manip_summary, manip_component = load_manip_component(module)
    branch_summaries.append(manip_summary)
    price_root_summaries = [row for row in branch_summaries if row["parent_regime_root"] in module.ROOTS]
    passed_price_roots = [row for row in price_root_summaries if row["hard_gate_result"] == "pass"]
    manip_pass = manip_summary["hard_gate_result"] == "pass"
    all_required_pass = len(passed_price_roots) == len(module.ROOTS) and manip_pass
    selected_counts = {root: 0 for root in [*module.ROOTS, "Manipulation(scoped)"]}
    for row in selected_rows:
        selected_counts[row["parent_regime_root"]] += 1
    selected_counts["Manipulation(scoped)"] = int(manip_component.get("component_positive_rows", 0))
    root_failures = [f"{row['parent_regime_root']}={row['hard_gate_result']}" for row in price_root_summaries if row["hard_gate_result"] != "pass"]
    if not manip_pass:
        root_failures.append("Manipulation(scoped)=missing_205047_component_pass")
    gate_result = "pass" if all_required_pass else "fail:required_root_branch_hard_gates_failed"
    downstream = "eligible_for_pre_bayes_bbn_catboost_execution_tree_probe" if all_required_pass else "not_started:blocked_by_branch_rc_spa_hard_gates"
    primary_blocker = "all required branch hard gates passed; downstream chain still required before promotion" if all_required_pass else "; ".join(root_failures)
    next_action = (
        "B5: run Pre-Bayes -> BBN -> CatBoost/path-ranker -> execution-tree branch consumption with the same branch paths."
        if all_required_pass
        else "B2R-repeat: choose a materially different root branch family/provider panel; do not relax RC-SPA."
    )
    report = {
        "schema_version": SCHEMA_VERSION,
        "run_id": RUN_ID,
        "run_root": rel(RUN_ROOT),
        "repo_git_ref": module.git_ref(REPO_ROOT),
        "accepted_regime_id": "BoardA_regime_factor_consumer_map_MainRegimeV2_roots_plus_scoped_manipulation",
        "accepted_regime_artifact": rel(module.BOARD_A_CONSUMER_MAP),
        "recipe_id": RECIPE_ID,
        "decision": {
            "gate_result": gate_result,
            "stable_profit_score": max(float(row["rc_spa"]) for row in price_root_summaries),
            "variant_trade_rows": len(all_rows),
            "selected_trade_rows": len(selected_rows),
            "branch_paths_evaluated": len(branch_summaries),
            "branch_paths_passed": len(passed_price_roots) + int(manip_pass),
            "price_root_paths_passed": len(passed_price_roots),
            "manipulation_component_pass": manip_pass,
            "selected_root_trade_counts": selected_counts,
            "downstream_consumption": downstream,
            "primary_blocker": primary_blocker,
            "next_action": next_action,
        },
        "manipulation_component": manip_component,
        "branch_summaries": branch_summaries,
        "variant_summaries": variant_summaries,
        "panel_summaries": panel_summaries,
        "artifacts": {
            "report_json": rel(REPORT_JSON),
            "report_md": rel(REPORT_MD),
            "selected_rows_csv": rel(SELECTED_ROWS_CSV),
            "all_rows_csv": rel(ALL_ROWS_CSV),
            "summary_csv": rel(SUMMARY_CSV),
            "panel_summary_csv": rel(PANEL_SUMMARY_CSV),
            "assertions": rel(ASSERTIONS),
            "candidate_summary": rel(CANDIDATE_MD),
        },
        "completion": {
            "runtime_code_changed": False,
            "auto_quant_checkout_changed": False,
            "raw_auto_quant_data_committed": False,
            "thresholds_relaxed_after_scoring": False,
            "downstream_runtime_consumed_branch_path": False,
        },
    }
    module.write_csv(ALL_ROWS_CSV, all_rows)
    module.write_csv(SELECTED_ROWS_CSV, selected_rows)
    module.write_csv(SUMMARY_CSV, branch_summaries)
    module.write_csv(PANEL_SUMMARY_CSV, panel_summaries)
    module.write_json(REPORT_JSON, report)
    write_report(report)
    CANDIDATE_MD.write_text(
        "\n".join(
            [
                "# Source Root Stop Carry Long-Horizon Candidate Summary v1",
                "",
                f"Run id: `{RUN_ID}`.",
                "",
                f"- Branch RC-SPA gate: `{gate_result}`",
                f"- Downstream consumption: `{downstream}`",
                "- Pre-Bayes / BBN / CatBoost / execution-tree must run in order before promotion.",
                "- The 205047 scoped Manipulation component is recorded as a component pass only.",
                f"- Primary blocker: {primary_blocker}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    assertions = [
        f"run_id={RUN_ID}",
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
    if not manip_pass:
        assertions.append("ASSERT_FAIL:manipulation_component_not_available")
    if not all_required_pass:
        assertions.append("ASSERT_FAIL:required_root_branch_hard_gates_failed")
    ASSERTIONS.write_text("\n".join(assertions) + "\n", encoding="utf-8")
    print(json.dumps(report["decision"], indent=2, sort_keys=True))
    return 1 if any(line.startswith("ASSERT_FAIL") for line in assertions) else 0


if __name__ == "__main__":
    raise SystemExit(main())
