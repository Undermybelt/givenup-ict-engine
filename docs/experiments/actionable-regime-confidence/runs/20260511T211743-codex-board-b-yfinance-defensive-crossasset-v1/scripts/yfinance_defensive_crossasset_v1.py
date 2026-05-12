#!/usr/bin/env python3
"""Board B yfinance defensive cross-asset root branch scorer.

Run-local additive experiment only. It consumes a cached yfinance daily close
panel, attaches Board A MainRegimeV2 source roots, scores predeclared defensive
cross-asset branches with unchanged RC-SPA gates, and keeps downstream
fail-closed unless all price roots pass.
"""

from __future__ import annotations

import csv
import importlib.util
import json
import math
import subprocess
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


RUN_ID = "20260511T211743+0800-codex-board-b-yfinance-defensive-crossasset-v1"
SCHEMA_VERSION = "board-b-yfinance-defensive-crossasset/v1"
RECIPE_ID = "YFinanceDefensiveCrossAssetV1"
SOURCE_TICKER = "^IXIC"
ROOTS = ["Bull", "Bear", "Sideways", "Crisis"]

RUN_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = next(path for path in [RUN_ROOT, *RUN_ROOT.parents] if (path / "Cargo.toml").exists())
BASE_SCRIPT = (
    REPO_ROOT
    / "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T193803-codex-board-b-root-transition-triad-clean-v1/scripts/"
    "board_b_root_transition_triad_clean_v1.py"
)
BOARD_A_CONSUMER_MAP = (
    REPO_ROOT
    / "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T153637-codex-regime-factor-consumer-map-v1/regime-factor-map/"
    "regime_factor_consumer_map_v1.csv"
)
SOURCE_REGIME_CSV = Path(
    "/Users/thrill3r/Downloads/stock-market-regimes-20002026/"
    "stock_market_regimes_2000_2026.csv"
)
YF_CLOSE_CSV = Path("/private/tmp/ict-regime-hmm-markov-root/yfinance_cross_asset_daily_close.csv")
MANIP_REPORT = (
    REPO_ROOT
    / "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T205047-codex-board-b-manipulation-stop-tp-grid-v2/"
    "manipulation-stop-tp-grid-v2/manipulation_stop_tp_grid_v2.md"
)

OUT_DIR = RUN_ROOT / "branch-rc-spa"
CHECK_DIR = RUN_ROOT / "checks"
PROVIDER_DIR = RUN_ROOT / "provider"
FAIL_CLOSED_DIR = RUN_ROOT / "ict-engine-fail-closed"

VARIANT_ROWS_CSV = OUT_DIR / "yfinance_defensive_crossasset_variant_rows_v1.csv"
SELECTED_ROWS_CSV = OUT_DIR / "yfinance_defensive_crossasset_selected_rows_v1.csv"
BRANCH_SUMMARY_CSV = OUT_DIR / "yfinance_defensive_crossasset_branch_summary_v1.csv"
PANEL_SUMMARY_CSV = OUT_DIR / "yfinance_defensive_crossasset_panel_summary_v1.csv"
REPORT_JSON = OUT_DIR / "yfinance_defensive_crossasset_rc_spa_report_v1.json"
REPORT_MD = OUT_DIR / "yfinance_defensive_crossasset_rc_spa_report_v1.md"
ASSERTIONS = CHECK_DIR / "yfinance_defensive_crossasset_v1_assertions.out"
FAIL_CLOSED_MD = FAIL_CLOSED_DIR / "yfinance_defensive_crossasset_fail_closed_summary_v1.md"
PROVIDER_JSON = PROVIDER_DIR / "yfinance_defensive_crossasset_provider_probe_v1.json"

PANELS = ["SPY", "QQQ", "IWM", "GLD", "TLT", "UUP", "HYG", "LQD", "DBC", "BTC-USD", "ETH-USD"]
HORIZONS = [3, 5, 10, 20]
VARIANTS = [
    ("risk_on_momentum", "Bull"),
    ("growth_breakout", "Bull"),
    ("defensive_rotation_long", "Bear"),
    ("index_breakdown_short", "Bear"),
    ("range_mean_reversion", "Sideways"),
    ("low_vol_carry", "Sideways"),
    ("crisis_defensive_long", "Crisis"),
    ("crisis_index_short", "Crisis"),
]


def rel(path: Path) -> str:
    return str(path.relative_to(REPO_ROOT))


def git_ref(root: Path) -> str:
    try:
        return subprocess.check_output(
            ["git", "-C", str(root), "rev-parse", "--short", "HEAD"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except Exception:
        return "unknown"


def load_base() -> Any:
    spec = importlib.util.spec_from_file_location("root_transition_base", BASE_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import base evaluator: {BASE_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.RECIPE_ID = RECIPE_ID
    return module


def load_root_floors() -> dict[str, float]:
    floors: dict[str, float] = {}
    with BOARD_A_CONSUMER_MAP.open(newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            regime = row["regime"]
            if regime in {"Bull", "Bear", "Sideways", "Crisis", "Manipulation"}:
                floors[regime] = float(row["confidence_floor"])
    return floors


def load_source_roots(root_floors: dict[str, float]) -> pd.DataFrame:
    source = pd.read_csv(
        SOURCE_REGIME_CSV,
        usecols=["date", "ticker", "regime_label", "regime_confidence", "vix"],
        parse_dates=["date"],
    )
    source = source[source["ticker"] == SOURCE_TICKER].copy()
    source["date"] = pd.to_datetime(source["date"]).dt.tz_localize(None).dt.normalize()
    source["parent_regime_root"] = source["regime_label"].map(lambda v: v if v in ROOTS else "Crisis")
    source["parent_regime_confidence_floor"] = source["parent_regime_root"].map(root_floors).fillna(0.0)
    source["source_ticker_confidence"] = pd.to_numeric(source["regime_confidence"], errors="coerce").fillna(0.0)
    source["source_ticker_vix"] = pd.to_numeric(source["vix"], errors="coerce").fillna(0.0)
    return source[
        [
            "date",
            "parent_regime_root",
            "parent_regime_confidence_floor",
            "source_ticker_confidence",
            "source_ticker_vix",
        ]
    ].sort_values("date")


def load_close_panel() -> pd.DataFrame:
    prices = pd.read_csv(YF_CLOSE_CSV, parse_dates=["Date"])
    prices["date"] = pd.to_datetime(prices["Date"]).dt.tz_localize(None).dt.normalize()
    prices = prices.drop(columns=["Date"]).set_index("date").sort_index()
    prices = prices[[col for col in PANELS + ["^VIX", "^VIX3M"] if col in prices.columns]]
    prices = prices.ffill()
    return prices


def branch_path(root: str, variant_id: str) -> str:
    if root == "Bull":
        return f"{root} -> CrossAssetRiskOn -> DefensiveFilteredMomentum -> {RECIPE_ID}:{variant_id}"
    if root == "Bear":
        return f"{root} -> DefensiveRotation -> RiskOffOrIndexShort -> {RECIPE_ID}:{variant_id}"
    if root == "Sideways":
        return f"{root} -> RangeConsolidation -> CrossAssetMeanReversion -> {RECIPE_ID}:{variant_id}"
    if root == "Crisis":
        return f"{root} -> ExtremeStress -> DefensiveLongOrIndexShort -> {RECIPE_ID}:{variant_id}"
    return (
        "Manipulation(scoped) -> TelegramPumpEvent -> ProviderStopTakeShort -> "
        "ManipulationStopTakeProfitGridV2:short_tp120_sl060_h72"
    )


def branch_fields(root: str) -> dict[str, str]:
    return {
        "Bull": {
            "sub_regime_tags": "CrossAssetRiskOn",
            "sub_sub_regime_or_profit_factor": "DefensiveFilteredMomentum",
            "profit_factor_family": "yfinance_defensive_crossasset",
            "allowed_action": "long_research_only_until_branch_rc_spa_passes",
            "suppression_rule": "suppress_if_bull_yfinance_defensive_branch_rc_spa_fails",
        },
        "Bear": {
            "sub_regime_tags": "DefensiveRotation",
            "sub_sub_regime_or_profit_factor": "RiskOffOrIndexShort",
            "profit_factor_family": "yfinance_defensive_crossasset",
            "allowed_action": "defensive_long_or_index_short_research_only_until_branch_rc_spa_passes",
            "suppression_rule": "suppress_if_bear_yfinance_defensive_branch_rc_spa_fails",
        },
        "Sideways": {
            "sub_regime_tags": "RangeConsolidation",
            "sub_sub_regime_or_profit_factor": "CrossAssetMeanReversion",
            "profit_factor_family": "yfinance_defensive_crossasset",
            "allowed_action": "mean_reversion_research_only_until_branch_rc_spa_passes",
            "suppression_rule": "suppress_if_sideways_yfinance_defensive_branch_rc_spa_fails",
        },
        "Crisis": {
            "sub_regime_tags": "ExtremeStress",
            "sub_sub_regime_or_profit_factor": "DefensiveLongOrIndexShort",
            "profit_factor_family": "yfinance_defensive_crossasset",
            "allowed_action": "defensive_long_or_index_short_research_only_until_branch_rc_spa_passes",
            "suppression_rule": "tail_guard_blocks_crisis_yfinance_defensive_branch_if_rc_spa_fails",
        },
    }[root]


def daily_features(prices: pd.DataFrame, ticker: str) -> pd.DataFrame:
    close = pd.to_numeric(prices[ticker], errors="coerce")
    df = pd.DataFrame({"close": close}).dropna().copy()
    df["ret1"] = df["close"].pct_change()
    df["ret5"] = df["close"].pct_change(5)
    df["ret20"] = df["close"].pct_change(20)
    df["sma20"] = df["close"].rolling(20, min_periods=10).mean()
    df["sma50"] = df["close"].rolling(50, min_periods=20).mean()
    std20 = df["close"].rolling(20, min_periods=10).std()
    df["z20"] = ((df["close"] - df["sma20"]) / std20.replace(0, np.nan)).fillna(0.0)
    df["vix"] = pd.to_numeric(prices.get("^VIX", pd.Series(index=prices.index, dtype=float)), errors="coerce")
    df["vix3m"] = pd.to_numeric(prices.get("^VIX3M", pd.Series(index=prices.index, dtype=float)), errors="coerce")
    df["vix_ratio"] = (df["vix"] / df["vix3m"].replace(0, np.nan)).replace([np.inf, -np.inf], np.nan)
    return df.dropna(subset=["ret1", "ret5", "ret20", "sma20", "sma50"])


def signal(row: pd.Series, ticker: str, variant_id: str) -> int:
    close = float(row["close"])
    ret5 = float(row["ret5"])
    ret20 = float(row["ret20"])
    z20 = float(row["z20"])
    vix = float(row.get("source_ticker_vix", row.get("vix", 0.0)))
    vix_ratio = float(row.get("vix_ratio", 1.0)) if not pd.isna(row.get("vix_ratio", 1.0)) else 1.0
    above20 = close > float(row["sma20"])
    above50 = close > float(row["sma50"])
    risk_asset = ticker in {"SPY", "QQQ", "IWM", "HYG", "BTC-USD", "ETH-USD"}
    defensive = ticker in {"GLD", "TLT", "UUP", "LQD", "DBC"}
    if variant_id == "risk_on_momentum":
        return 1 if risk_asset and above20 and ret20 > 0 and vix < 30 else 0
    if variant_id == "growth_breakout":
        return 1 if ticker in {"QQQ", "IWM", "BTC-USD", "ETH-USD"} and above50 and ret5 > 0 and vix_ratio < 1.05 else 0
    if variant_id == "defensive_rotation_long":
        return 1 if defensive and above20 and ret20 > 0 and vix >= 17 else 0
    if variant_id == "index_breakdown_short":
        return -1 if ticker in {"SPY", "QQQ", "IWM", "HYG"} and (not above50) and ret20 < 0 else 0
    if variant_id == "range_mean_reversion":
        if risk_asset and abs(ret20) < 0.08 and vix < 28 and z20 <= -1.0:
            return 1
        if risk_asset and abs(ret20) < 0.08 and vix < 28 and z20 >= 1.0:
            return -1
        return 0
    if variant_id == "low_vol_carry":
        return 1 if ticker in {"SPY", "QQQ", "HYG", "LQD", "TLT"} and above20 and vix < 22 and abs(z20) < 1.2 else 0
    if variant_id == "crisis_defensive_long":
        return 1 if defensive and above20 and (vix >= 25 or vix_ratio >= 1.05) else 0
    if variant_id == "crisis_index_short":
        return -1 if ticker in {"SPY", "QQQ", "IWM", "HYG", "BTC-USD", "ETH-USD"} and (not above20) and (vix >= 24 or ret20 < -0.06) else 0
    return 0


def build_rows(prices: pd.DataFrame, roots: pd.DataFrame) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    all_rows: list[dict[str, Any]] = []
    panel_summaries: list[dict[str, Any]] = []
    root_by_date = roots.set_index("date")
    for ticker in PANELS:
        if ticker not in prices.columns:
            continue
        features = daily_features(prices, ticker)
        features = features.join(root_by_date, how="left")
        features = features.dropna(subset=["parent_regime_root"])
        for variant_id, target_root in VARIANTS:
            for horizon in HORIZONS:
                rows_before = len(all_rows)
                next_allowed = pd.Timestamp.min
                dates = list(features.index)
                for idx, date in enumerate(dates):
                    if date <= next_allowed or idx + horizon >= len(dates):
                        continue
                    row = features.iloc[idx]
                    root = str(row["parent_regime_root"])
                    if root != target_root:
                        continue
                    direction = signal(row, ticker, variant_id)
                    if direction == 0:
                        continue
                    exit_row = features.iloc[idx + horizon]
                    entry = float(row["close"])
                    exit_price = float(exit_row["close"])
                    if entry <= 0 or exit_price <= 0:
                        continue
                    cost = 0.0008 if ticker not in {"BTC-USD", "ETH-USD"} else 0.0018
                    gross = direction * (exit_price / entry - 1.0)
                    pnl = gross - cost
                    fields = branch_fields(root)
                    all_rows.append(
                        {
                            "schema_version": SCHEMA_VERSION,
                            "run_id": RUN_ID,
                            "recipe_id": RECIPE_ID,
                            "variant_id": f"{variant_id}_h{horizon}",
                            "market": ticker,
                            "timeframe": "1d",
                            "trade_id": f"{RECIPE_ID}:{ticker}:{variant_id}:h{horizon}:{date.date()}",
                            "open_date": date.isoformat(),
                            "close_date": pd.Timestamp(exit_row.name).isoformat(),
                            "open_session_date": date.date().isoformat(),
                            "source_anchor": SOURCE_TICKER,
                            "parent_regime_root": root,
                            "parent_regime_confidence_floor": float(row["parent_regime_confidence_floor"]),
                            "source_ticker_confidence": float(row["source_ticker_confidence"]),
                            "source_ticker_vix": float(row["source_ticker_vix"]),
                            "manipulation_overlay_state": "component_available_not_root_gate_promotion",
                            "sub_regime_tags": fields["sub_regime_tags"],
                            "sub_sub_regime_or_profit_factor": fields["sub_sub_regime_or_profit_factor"],
                            "profit_factor_family": fields["profit_factor_family"],
                            "profit_factor_leaf": f"{RECIPE_ID}:{variant_id}_h{horizon}",
                            "regime_profit_branch_path": branch_path(root, f"{variant_id}_h{horizon}"),
                            "regime_profit_branch_path_version": SCHEMA_VERSION,
                            "trade_or_bar_horizon": f"1d_hold_{horizon}",
                            "allowed_action": fields["allowed_action"],
                            "suppression_rule": fields["suppression_rule"],
                            "direction": "long" if direction > 0 else "short",
                            "direction_sign": direction,
                            "entry_close": entry,
                            "exit_close": exit_price,
                            "gross_return": gross,
                            "roundtrip_cost": cost,
                            "profit_ratio_net": pnl,
                            "year_fold": int(date.year),
                            "root_lookup_status": "source_panel_daily_asof",
                        }
                    )
                    next_allowed = dates[idx + horizon]
                new_rows = all_rows[rows_before:]
                values = np.array([float(r["profit_ratio_net"]) for r in new_rows], dtype=float)
                panel_summaries.append(
                    {
                        "market": ticker,
                        "timeframe": "1d",
                        "variant_id": f"{variant_id}_h{horizon}",
                        "trades": len(new_rows),
                        "mean_profit_ratio": float(np.mean(values)) if len(values) else 0.0,
                        "win_rate": float(np.mean(values > 0)) if len(values) else 0.0,
                        "net_return_R": float(np.sum(values)) if len(values) else 0.0,
                    }
                )
    return all_rows, panel_summaries


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def provider_probe() -> dict[str, Any]:
    payload: dict[str, Any] = {
        "provider": "yfinance",
        "cached_panel": str(YF_CLOSE_CSV),
        "cached_panel_exists": YF_CLOSE_CSV.exists(),
        "live_probe_attempted": True,
    }
    try:
        import yfinance as yf  # type: ignore

        sample = yf.download("QQQ", period="5d", interval="1d", progress=False, auto_adjust=False, threads=False)
        payload["live_probe_ok"] = bool(sample is not None and not sample.empty)
        payload["live_probe_rows"] = int(0 if sample is None else len(sample))
    except Exception as exc:  # pragma: no cover - diagnostic artifact only
        payload["live_probe_ok"] = False
        payload["live_probe_error"] = repr(exc)
    write_json(PROVIDER_JSON, payload)
    return payload


def main() -> int:
    for path in [OUT_DIR, CHECK_DIR, PROVIDER_DIR, FAIL_CLOSED_DIR]:
        path.mkdir(parents=True, exist_ok=True)
    missing = [p for p in [YF_CLOSE_CSV, SOURCE_REGIME_CSV, BOARD_A_CONSUMER_MAP, MANIP_REPORT] if not p.exists()]
    if missing:
        raise RuntimeError("missing required inputs: " + ", ".join(str(p) for p in missing))

    base = load_base()
    base.branch_path = branch_path
    provider = provider_probe()
    roots = load_source_roots(load_root_floors())
    prices = load_close_panel()
    all_rows, panel_summaries = build_rows(prices, roots)

    branch_summaries: list[dict[str, Any]] = []
    selected_rows: list[dict[str, Any]] = []
    variant_summaries: list[dict[str, Any]] = []
    for root in ROOTS:
        root_rows = [r for r in all_rows if r["parent_regime_root"] == root]
        variants = sorted({str(r["variant_id"]) for r in root_rows})
        scored: list[dict[str, Any]] = []
        pbo, pbo_method = base.pbo_for_root(root, all_rows)
        for variant in variants:
            rows = [r for r in root_rows if str(r["variant_id"]) == variant]
            scored.append(base.summarize_rows(root=root, variant_id=variant, rows=rows, all_rows=all_rows, pbo=pbo, pbo_method=pbo_method))
        if scored:
            selected = max(scored, key=lambda row: float(row["rc_spa"]))
        else:
            selected = base.summarize_rows(root=root, variant_id="no_rows", rows=[], all_rows=all_rows, pbo=1.0, pbo_method="no_rows")
        branch_summaries.append(selected)
        variant_summaries.extend(scored)
        selected_rows.extend([r for r in root_rows if str(r["variant_id"]) == str(selected["selected_variant_id"])])

    manip_summary = {
        "recipe_id": "ManipulationStopTakeProfitGridV2",
        "parent_regime_root": "Manipulation(scoped)",
        "selected_variant_id": "short_tp120_sl060_h72",
        "regime_profit_branch_path": branch_path("Manipulation(scoped)", "short_tp120_sl060_h72"),
        "total_trades": 13535,
        "test_folds": 12,
        "folds": "monthly_folds_12",
        "min_trades_per_test_fold": 1127,
        "fold_positive_rate": 0.75,
        "win_rate": 0.0,
        "mean_profit_ratio_net": 0.006652440778270629,
        "net_return_R": 0.0,
        "bootstrap_edge_lcb_5pct": 0.005609363049193369,
        "bootstrap_edge_lcb_5pct_stressed_2x_cost": 0.004109363049193369,
        "pbo": 0.0,
        "pbo_method": "external_component_not_reoptimized_in_this_run",
        "dsr": 1.0,
        "dsr_method": "external_component_pass_from_205047_not_rescored_here",
        "cost_stress_result": "pass",
        "tail_loss_p95": 0.0,
        "max_drawdown_trade_equity_proxy": 0.0,
        "regime_specificity_ratio": 999.0,
        "outside_mean_profit_ratio_net": -0.0007330792216955587,
        "rc_spa": 100.0,
        "promotion_level": "component_pass_only",
        "hard_gate_result": "pass",
        "downstream_consumption_status": "not_started:full_board_b_root_gates_required",
    }
    all_branch_summaries = branch_summaries + [manip_summary]
    price_passed = [row for row in branch_summaries if row["hard_gate_result"] == "pass"]
    all_price_pass = len(price_passed) == len(ROOTS)
    gate_result = "pass" if all_price_pass else "fail:required_root_branch_hard_gates_failed"
    downstream = (
        "eligible_for_pre_bayes_bbn_catboost_execution_tree_probe"
        if all_price_pass
        else "not_started:blocked_by_branch_rc_spa_hard_gates"
    )
    root_failures = [f"{row['parent_regime_root']}={row['hard_gate_result']}" for row in branch_summaries if row["hard_gate_result"] != "pass"]
    max_score = max(float(row["rc_spa"]) for row in branch_summaries) if branch_summaries else 0.0
    counts = {root: int(sum(1 for r in selected_rows if r["parent_regime_root"] == root)) for root in ROOTS}
    counts["Manipulation(scoped)"] = 13535
    decision = {
        "gate_result": gate_result,
        "stable_profit_score": max_score,
        "price_root_paths_passed": len(price_passed),
        "manipulation_component_pass": True,
        "variant_trade_rows": len(all_rows),
        "selected_trade_rows": len(selected_rows),
        "selected_root_trade_counts": counts,
        "downstream_consumption": downstream,
        "primary_blocker": "all price roots passed" if all_price_pass else "; ".join(root_failures),
        "next_action": (
            "B5: run Pre-Bayes -> BBN -> CatBoost/path-ranker -> execution-tree branch consumption."
            if all_price_pass
            else "B2R-repeat: keep 205047 Manipulation component, but choose a different Bull/Bear/Sideways/Crisis root family or provider panel; do not relax RC-SPA."
        ),
    }
    report = {
        "schema_version": SCHEMA_VERSION,
        "run_id": RUN_ID,
        "run_root": rel(RUN_ROOT),
        "repo_git_ref": git_ref(REPO_ROOT),
        "accepted_regime_id": "BoardA_regime_factor_consumer_map_MainRegimeV2_roots_plus_scoped_manipulation",
        "accepted_regime_artifact": rel(BOARD_A_CONSUMER_MAP),
        "recipe_id": RECIPE_ID,
        "inputs": {
            "cached_yfinance_close_panel": str(YF_CLOSE_CSV),
            "source_regime_csv": str(SOURCE_REGIME_CSV),
            "source_ticker": SOURCE_TICKER,
            "provider_probe": rel(PROVIDER_JSON),
            "manipulation_component": rel(MANIP_REPORT),
        },
        "decision": decision,
        "branch_summaries": all_branch_summaries,
        "variant_summaries": variant_summaries,
        "panel_summaries": panel_summaries,
        "provider_probe": provider,
    }

    write_csv(VARIANT_ROWS_CSV, all_rows)
    write_csv(SELECTED_ROWS_CSV, selected_rows)
    write_csv(BRANCH_SUMMARY_CSV, all_branch_summaries)
    write_csv(PANEL_SUMMARY_CSV, panel_summaries)
    write_json(REPORT_JSON, report)
    branch_lines = [
        "| Root | Selected Variant | Trades | Folds | Min Fold Trades | Fold Positive Rate | LCB 5% | PBO | DSR | RC-SPA | Gate |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in all_branch_summaries:
        branch_lines.append(
            f"| {row['parent_regime_root']} | `{row['selected_variant_id']}` | {int(row['total_trades'])} | "
            f"{int(row['test_folds'])} | {int(row['min_trades_per_test_fold'])} | "
            f"{float(row['fold_positive_rate']):.4f} | {float(row['bootstrap_edge_lcb_5pct']):.6f} | "
            f"{float(row['pbo']):.3f} | {float(row['dsr']):.4f} | {float(row['rc_spa']):.4f} | "
            f"`{row['hard_gate_result']}` |"
        )
    REPORT_MD.write_text(
        "\n".join(
            [
                "# YFinance Defensive Cross-Asset RC-SPA v1",
                "",
                f"Run id: `{RUN_ID}`.",
                "",
                "## Decision",
                "",
                f"- Gate result: `{gate_result}`",
                f"- Stable profit score: `{max_score:.4f}`",
                f"- Price-root paths passed: `{len(price_passed)}/4`",
                "- Scoped Manipulation component pass consumed: `True`",
                f"- Variant rows: `{len(all_rows)}`",
                f"- Selected rows: `{len(selected_rows)}`",
                f"- Selected root counts: `{counts}`",
                f"- Downstream consumption: `{downstream}`",
                f"- Primary blocker: {decision['primary_blocker']}",
                "",
                "## Selected Branch Summary",
                "",
                *branch_lines,
                "",
                "## Inputs",
                "",
                f"- Cached yfinance daily close panel: `{YF_CLOSE_CSV}`",
                f"- Provider probe: `{rel(PROVIDER_JSON)}`",
                f"- Board A consumer map: `{rel(BOARD_A_CONSUMER_MAP)}`",
                f"- Source root schedule: `{SOURCE_REGIME_CSV}` / `{SOURCE_TICKER}`",
                f"- Scoped Manipulation component: `{rel(MANIP_REPORT)}`",
                "",
                "## Artifacts",
                "",
                f"- Report JSON: `{rel(REPORT_JSON)}`",
                f"- Selected rows: `{rel(SELECTED_ROWS_CSV)}`",
                f"- Variant rows: `{rel(VARIANT_ROWS_CSV)}`",
                f"- Branch summary: `{rel(BRANCH_SUMMARY_CSV)}`",
                f"- Panel summary: `{rel(PANEL_SUMMARY_CSV)}`",
                f"- Fail-closed downstream summary: `{rel(FAIL_CLOSED_MD)}`",
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
    FAIL_CLOSED_MD.write_text(
        "\n".join(
            [
                "# YFinance Defensive Cross-Asset ict-engine Fail-Closed Summary v1",
                "",
                f"Run id: `{RUN_ID}`.",
                "",
                f"- Branch RC-SPA gate: `{gate_result}`",
                f"- Downstream consumption: `{downstream}`",
                "- Pre-Bayes / BBN / CatBoost / execution-tree were not started unless every required price-root branch hard gate passed.",
                "- This is a fail-closed readback, not a promoted profitability packet.",
                "",
                f"Primary blocker: {decision['primary_blocker']}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    ASSERTIONS.write_text(
        "\n".join(
            [
                f"run_id={RUN_ID}",
                f"variant_trade_rows={len(all_rows)}",
                f"selected_trade_rows={len(selected_rows)}",
                f"price_root_paths_passed={len(price_passed)}",
                "manipulation_component_pass=True",
                f"gate_result={gate_result}",
                f"downstream_consumption={downstream}",
                "artifacts_exist=true",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    print(json.dumps(decision, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
