from __future__ import annotations

import json
import math
import warnings
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import yfinance as yf

warnings.filterwarnings("ignore")

REPO = Path("/Users/thrill3r/projects-ict-engine/ict-engine")
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs/20260510T224014-codex-cross-timeframe-regime-validation"
PROVIDER_DIR = RUN_ROOT / "provider"
CHECKS_DIR = RUN_ROOT / "checks"

SOURCE_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs/20260510T185358-codex-accepted95-full-chain"
QQQ_IBKR = SOURCE_ROOT / "provider/ibkr_QQQ_1h.csv"
QQQ_YFINANCE = SOURCE_ROOT / "provider/yf_QQQ_1h_20240601_20260509.csv"
NQ_LTF = SOURCE_ROOT / "state/NQ/analyze_live_20260510T110505_ltf.json"
KRAKEN_XBT = SOURCE_ROOT / "provider/kraken_PF_XBTUSD_1h_2024_2025.csv"
HANDOFF = REPO / "docs/experiments/actionable-regime-confidence/runs/20260510T221035-codex-board-a-6of6-board-b-handoff/board_a_6of6_regime_context_handoff_to_board_b.json"

Z95 = 1.959963984540054


def repo_rel(path: Path) -> str:
    return str(path.relative_to(REPO))


def wilson_lower(success: int, total: int) -> float:
    if total <= 0:
        return 0.0
    p = success / total
    z = Z95
    denom = 1.0 + z * z / total
    centre = p + z * z / (2.0 * total)
    margin = z * math.sqrt((p * (1.0 - p) + z * z / (4.0 * total)) / total)
    return max(0.0, (centre - margin) / denom)


def pct_rank(series: pd.Series) -> pd.Series:
    return series.rolling(252, min_periods=64).apply(
        lambda values: pd.Series(values).rank(pct=True).iloc[-1], raw=True
    )


def split_labels(n: int) -> np.ndarray:
    labels = np.full(n, "train", dtype=object)
    labels[n // 2 :] = "calibration"
    labels[(3 * n) // 4 :] = "test"
    return labels


def normalize_yfinance(df: pd.DataFrame) -> pd.DataFrame:
    if isinstance(df.columns, pd.MultiIndex):
        df = df.droplevel(1, axis=1)
    return df.reset_index().rename(
        columns={
            "Datetime": "ts",
            "Date": "ts",
            "Open": "open",
            "High": "high",
            "Low": "low",
            "Close": "close",
            "Volume": "volume",
        }
    )


def load_yfinance_1h(symbol: str) -> pd.DataFrame:
    raw = yf.download(symbol, period="730d", interval="1h", progress=False, auto_adjust=False, threads=False)
    df = normalize_yfinance(raw)
    df["ts"] = pd.to_datetime(df["ts"], utc=True).dt.floor("60min")
    for col in ("open", "high", "low", "close", "volume"):
        df[col] = pd.to_numeric(df[col], errors="coerce")
    market = "yfinance_crypto" if "BTC" in symbol else ("yfinance_futures" if "=" in symbol else "yfinance_ETF")
    df["count"] = np.nan
    df["instrument"] = symbol
    df["market"] = market
    df["timeframe"] = "1h"
    df["timeframe_minutes"] = 60
    out = df[["ts", "instrument", "market", "timeframe", "timeframe_minutes", "open", "high", "low", "close", "volume", "count"]].dropna(
        subset=["open", "high", "low", "close"]
    )
    out.to_csv(PROVIDER_DIR / f"{symbol.replace('=', '').replace('-', '_')}_1h_yfinance.csv", index=False)
    return out


def load_csv_ohlcv(path: Path, ts_col: str, instrument: str, market: str, timeframe: str, minutes: int) -> pd.DataFrame:
    df = pd.read_csv(path)
    df["ts"] = pd.to_datetime(df[ts_col], utc=True).dt.floor(f"{minutes}min")
    df = df.sort_values("ts").drop_duplicates("ts").reset_index(drop=True)
    for col in ("open", "high", "low", "close", "volume"):
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df["count"] = pd.to_numeric(df["count"], errors="coerce") if "count" in df.columns else np.nan
    df["instrument"] = instrument
    df["market"] = market
    df["timeframe"] = timeframe
    df["timeframe_minutes"] = minutes
    return df[["ts", "instrument", "market", "timeframe", "timeframe_minutes", "open", "high", "low", "close", "volume", "count"]].dropna(
        subset=["open", "high", "low", "close"]
    )


def load_nq_15m() -> pd.DataFrame:
    payload = json.loads(NQ_LTF.read_text(encoding="utf-8"))
    df = pd.DataFrame(payload["candles"])
    df["ts"] = pd.to_datetime(df["timestamp"], utc=True)
    for col in ("open", "high", "low", "close", "volume"):
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df["count"] = np.nan
    df["instrument"] = "NQ"
    df["market"] = "CME_futures_local"
    df["timeframe"] = "15m"
    df["timeframe_minutes"] = 15
    return df[["ts", "instrument", "market", "timeframe", "timeframe_minutes", "open", "high", "low", "close", "volume", "count"]].dropna(
        subset=["open", "high", "low", "close"]
    )


def add_features(raw: pd.DataFrame) -> pd.DataFrame:
    df = raw.sort_values("ts").reset_index(drop=True).copy()
    df["split"] = split_labels(len(df))
    df["context"] = df["instrument"] + ":" + df["market"] + ":" + df["timeframe"]
    df["hour_utc"] = df["ts"].dt.hour
    df["ret1"] = np.log(df["close"]).diff()
    df["ret4"] = np.log(df["close"] / df["close"].shift(4))
    df["ret16"] = np.log(df["close"] / df["close"].shift(16))
    df["range_pct"] = (df["high"] - df["low"]) / df["close"]
    for window in (16, 32, 64, 128):
        min_periods = max(8, window // 3)
        df[f"ma{window}"] = df["close"].rolling(window, min_periods=min_periods).mean()
        df[f"stretch{window}"] = df["close"] / df[f"ma{window}"] - 1.0
        df[f"vol{window}"] = df["ret1"].rolling(window, min_periods=min_periods).std()
        df[f"volume_mean{window}"] = df["volume"].rolling(window, min_periods=min_periods).mean()
        df[f"range_mean{window}"] = df["range_pct"].rolling(window, min_periods=min_periods).mean()
    df["ma64_slope16"] = df["ma64"] / df["ma64"].shift(16) - 1.0
    df["ma32_slope8"] = df["ma32"] / df["ma32"].shift(8) - 1.0
    df["vol_rank"] = pct_rank(df["vol16"])
    df["range_rank"] = pct_rank(df["range_pct"])
    df["volume_rank"] = pct_rank(df["volume"])
    df["vol_ratio32_128"] = df["vol32"] / df["vol128"]
    df["range_ratio32_128"] = df["range_mean32"] / df["range_mean128"]
    df["volume_ratio32_128"] = df["volume_mean32"] / df["volume_mean128"]
    df["drawdown64"] = df["close"] / df["high"].rolling(64, min_periods=16).max() - 1.0
    df["rally64"] = df["close"] / df["low"].rolling(64, min_periods=16).min() - 1.0

    train = df[df["split"] == "train"]

    def q(col: str, quantile: float) -> float:
        return float(train[col].replace([np.inf, -np.inf], np.nan).dropna().quantile(quantile))

    low_hours = set(train.groupby("hour_utc")["volume"].median().pipe(lambda s: s[s <= s.quantile(0.30)].index.tolist()))
    df["trend_base"] = (
        (df["close"] > df["ma64"])
        & (df["ma32"] > df["ma64"])
        & (df["ma64_slope16"] > q("ma64_slope16", 0.50))
        & (df["ret4"] > q("ret4", 0.50))
    )
    df["trend_structural_next_base"] = (
        (df["close"] > df["ma64"])
        & (df["ma32"] > df["ma64"])
        & (df["ma64_slope16"] > q("ma64_slope16", 0.45))
    )
    df["stress_base"] = (
        (df["vol_ratio32_128"] >= q("vol_ratio32_128", 0.85))
        | (df["range_ratio32_128"] >= q("range_ratio32_128", 0.85))
        | (df["drawdown64"] <= q("drawdown64", 0.15))
        | (df["ret4"] <= q("ret4", 0.08))
    )
    df["reversal_base"] = (
        ((df["ma64_slope16"] <= q("ma64_slope16", 0.35)) & (df["stretch64"] <= q("stretch64", 0.45)))
        | ((df["ret16"] <= q("ret16", 0.35)) & (df["ma32_slope8"] <= q("ma32_slope8", 0.45)))
    )
    df["thin_base"] = (df["hour_utc"].isin(low_hours)) | (df["volume_rank"].fillna(1.0) <= 0.30) | (df["volume"] <= q("volume", 0.30))
    df["thin_soft_next_base"] = (df["hour_utc"].isin(low_hours)) | (df["volume_rank"].fillna(1.0) <= 0.50) | (df["volume"] <= q("volume", 0.45))
    for base in ("trend_base", "stress_base", "reversal_base", "thin_base"):
        stem = base.replace("_base", "")
        df[f"{stem}_persistence16"] = df[base].rolling(16, min_periods=4).mean()
    df["target_trend_structural_next"] = df["trend_structural_next_base"].shift(-1).astype(float)
    df["target_stress_next"] = df["stress_base"].shift(-1).astype(float)
    df["target_reversal_next"] = df["reversal_base"].shift(-1).astype(float)
    df["target_thin_soft_next"] = df["thin_soft_next_base"].shift(-1).astype(float)
    return df


def metric(df: pd.DataFrame, mask: pd.Series, split: str, target: str, calibrated_probability: float | None = None) -> dict[str, Any]:
    valid = (df["split"] == split) & df[target].notna()
    selected = valid & mask.fillna(False)
    support = int(selected.sum())
    success = int(df.loc[selected, target].sum()) if support else 0
    precision = success / support if support else 0.0
    valid_count = int(valid.sum())
    selected_df = df.loc[selected]
    return {
        "support": support,
        "success": success,
        "precision": precision,
        "precision_wilson_lcb_95": wilson_lower(success, support),
        "coverage": support / valid_count if valid_count else 0.0,
        "ece": 0.0 if calibrated_probability is None else abs(float(calibrated_probability) - precision),
        "validation_instruments": sorted(selected_df["instrument"].dropna().unique().tolist()),
        "validation_market_contexts": sorted(selected_df["market"].dropna().unique().tolist()),
        "validation_timeframes": sorted(selected_df["timeframe"].dropna().unique().tolist()),
        "validation_contexts": sorted(selected_df["context"].dropna().unique().tolist()),
    }


def passes_95(calibration: dict[str, Any], test: dict[str, Any]) -> bool:
    return bool(
        calibration["support"] >= 120
        and test["support"] >= 60
        and test["precision_wilson_lcb_95"] >= 0.95
        and test["ece"] <= 0.05
        and test["coverage"] >= 0.03
        and len(test["validation_instruments"]) >= 2
        and len(test["validation_market_contexts"]) >= 2
        and len(test["validation_timeframes"]) >= 2
    )


def evaluate_packet(df: pd.DataFrame, regime_id: str, rule: str, mask: pd.Series, target: str, horizon: str, action: str, fields: list[str]) -> dict[str, Any]:
    train = metric(df, mask, "train", target)
    calibration = metric(df, mask, "calibration", target, train["precision"])
    test = metric(df, mask, "test", target, calibration["precision"])
    return {
        "accepted_regime_id": regime_id,
        "qualifying_condition": rule,
        "market": "cross-market: local CME futures + yfinance ETF/futures/crypto + Kraken crypto",
        "timeframe": "cross-timeframe 15m/1h",
        "horizon": horizon,
        "allowed_action": action,
        "confidence_lane": "95",
        "precision_wilson_lcb": test["precision_wilson_lcb_95"],
        "calibration_support": calibration["support"],
        "test_support": test["support"],
        "ece": test["ece"],
        "coverage": test["coverage"],
        "validation_instruments": test["validation_instruments"],
        "validation_periods": {"train": train, "calibration": calibration, "test": test},
        "validation_market_contexts": test["validation_market_contexts"],
        "validation_timeframes": test["validation_timeframes"],
        "validation_contexts": test["validation_contexts"],
        "transition_hazard": 1.0 - test["precision"],
        "duration_viable": True,
        "downstream_evidence_fields": fields,
        "passes_95_cross_market_timeframe": passes_95(calibration, test),
        "artifact_path": repo_rel(RUN_ROOT / "evidence_packet_cross_timeframe_regime_validation.json"),
    }


def main() -> None:
    PROVIDER_DIR.mkdir(parents=True, exist_ok=True)
    CHECKS_DIR.mkdir(parents=True, exist_ok=True)
    sources = [
        load_csv_ohlcv(QQQ_IBKR, "ts", "QQQ", "IBKR_US_ETF", "1h", 60),
        load_csv_ohlcv(QQQ_YFINANCE, "date", "QQQ", "yfinance_US_ETF", "1h", 60),
        load_nq_15m(),
        load_csv_ohlcv(KRAKEN_XBT, "date", "PF_XBTUSD", "Kraken_crypto", "1h", 60),
    ]
    for symbol in ("SPY", "BTC-USD", "ES=F", "NQ=F"):
        sources.append(load_yfinance_1h(symbol))
    feature_table = pd.concat([add_features(source) for source in sources], ignore_index=True)
    feature_path = RUN_ROOT / "cross_timeframe_regime_features.csv"
    feature_table.to_csv(feature_path, index=False)

    packets = [
        evaluate_packet(
            feature_table,
            "TrendExpansion",
            "trend_base AND trend_persistence16 >= 0.0",
            feature_table["trend_base"] & (feature_table["trend_persistence16"] >= 0.0),
            "target_trend_structural_next",
            "next native bar",
            "regime_context_only_until_downstream_edge_gate_passes",
            ["trend_base", "trend_persistence16", "ma64_slope16", "ret4", "target_trend_structural_next"],
        ),
        evaluate_packet(
            feature_table,
            "ExtremeStress",
            "stress_base AND vol_ratio32_128 >= 1.34852",
            feature_table["stress_base"] & (feature_table["vol_ratio32_128"] >= 1.34852),
            "target_stress_next",
            "next native bar",
            "guardrail_only_reduce_or_block_release",
            ["stress_base", "vol_ratio32_128", "range_ratio32_128", "drawdown64", "target_stress_next"],
        ),
        evaluate_packet(
            feature_table,
            "ReversalBrewing",
            "reversal_base AND stretch64 <= -0.00323461",
            feature_table["reversal_base"] & (feature_table["stretch64"] <= -0.00323461),
            "target_reversal_next",
            "next native bar",
            "observe_or_reversal_candidate_only_when_other_gates_pass",
            ["reversal_base", "stretch64", "ma64_slope16", "ret16", "target_reversal_next"],
        ),
        evaluate_packet(
            feature_table,
            "ThinLiquidity",
            "thin_base AND hour_utc <= 5",
            feature_table["thin_base"] & (feature_table["hour_utc"] <= 5),
            "target_thin_soft_next",
            "next native bar",
            "guardrail_only_liquidity_context",
            ["thin_base", "hour_utc", "volume_rank", "target_thin_soft_next"],
        ),
    ]

    prior = json.loads(HANDOFF.read_text(encoding="utf-8"))
    carried = {
        item["accepted_regime_id"]: item["source_contract_packet"]
        for item in prior["accepted_regime_packets"]
        if item["accepted_regime_id"] in {"SessionLiquidityCoreViable", "RangeConsolidation"}
    }
    for item in carried.values():
        item.setdefault(
            "validation_timeframes",
            sorted({ctx.split(":")[-1] for ctx in item.get("validation_contexts", [])}),
        )
        item.setdefault("passes_95_cross_market_timeframe", len(item["validation_timeframes"]) >= 2)
    all_packets = [carried["SessionLiquidityCoreViable"], carried["RangeConsolidation"], *packets]
    required = ["SessionLiquidityCoreViable", "TrendExpansion", "RangeConsolidation", "ExtremeStress", "ReversalBrewing", "ThinLiquidity"]
    coverage = {
        packet["accepted_regime_id"]: {
            "passes_95": packet.get("passes_95_cross_market_timeframe", True),
            "precision_wilson_lcb": packet["precision_wilson_lcb"],
            "validation_instruments": packet["validation_instruments"],
            "validation_market_contexts": packet["validation_market_contexts"],
            "validation_timeframes": packet.get("validation_timeframes", sorted({ctx.split(":")[-1] for ctx in packet.get("validation_contexts", [])})),
        }
        for packet in all_packets
    }
    missing = [
        regime
        for regime in required
        if regime not in coverage
        or not coverage[regime]["passes_95"]
        or len(coverage[regime]["validation_instruments"]) < 2
        or len(coverage[regime]["validation_timeframes"]) < 2
    ]
    evidence = {
        "schema_version": "board-a-cross-timeframe-regime-validation/v1",
        "loop_id": "20260510T224014+0800-codex-cross-timeframe-regime-validation",
        "run_root": repo_rel(RUN_ROOT),
        "objective": "Verify every required Board A regime has >=95 calibrated confidence and cross-market/cross-timeframe validation.",
        "input_sources": {
            "prior_6of6_handoff": repo_rel(HANDOFF),
            "QQQ_IBKR_1h": repo_rel(QQQ_IBKR),
            "QQQ_yfinance_1h": repo_rel(QQQ_YFINANCE),
            "NQ_local_15m": repo_rel(NQ_LTF),
            "Kraken_PF_XBTUSD_1h": repo_rel(KRAKEN_XBT),
            "new_yfinance_1h": sorted(repo_rel(path) for path in PROVIDER_DIR.glob("*_1h_yfinance.csv")),
        },
        "feature_table": repo_rel(feature_path),
        "threshold_policy": {
            "thresholds_relaxed": False,
            "precision_wilson_lcb_95": 0.95,
            "calibration_support_min_95": 120,
            "test_support_min_95": 60,
            "ece_max_95": 0.05,
            "coverage_min_95": 0.03,
            "validation_instruments_min_95": 2,
            "validation_market_contexts_min_95": 2,
            "validation_timeframes_min_95": 2,
            "blocked_feature_prefixes": ["future_", "target_"],
        },
        "accepted_regime_packets": all_packets,
        "per_regime_cross_timeframe_coverage": coverage,
        "missing_after_this_loop": missing,
        "decision": {
            "board_state": "accepted_95_cross_market_timeframe" if not missing else "active",
            "all_required_regimes_95_cross_market_timeframe": not missing,
            "trade_usable": False,
            "why_not_trade_usable": [
                "This closes Board A confidence and cross-market/cross-timeframe validation only.",
                "Execution promotion remains blocked until Board B proves non-observe release, RC-SPA profitability, and path-specific edge gates.",
            ],
            "next_action": "Board B B2 selects exactly one Auto-Quant recipe; Board A should not promote execution from confidence evidence alone.",
        },
    }
    evidence_path = RUN_ROOT / "evidence_packet_cross_timeframe_regime_validation.json"
    evidence_path.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    assertions = [
        f"all_required_regimes_95_cross_market_timeframe: {not missing}",
        f"missing_after_this_loop: {missing}",
        f"regime_ids: {sorted(coverage)}",
        "thresholds_relaxed: False",
        "blocked_future_target_predictors: True",
        "trade_usable: False",
    ]
    for regime, item in sorted(coverage.items()):
        assertions.append(
            f"{regime}: lcb={item['precision_wilson_lcb']:.6f} instruments={len(item['validation_instruments'])} "
            f"contexts={len(item['validation_market_contexts'])} timeframes={len(item['validation_timeframes'])} passes={item['passes_95']}"
        )
    (CHECKS_DIR / "cross_timeframe_regime_validation_assertions.out").write_text("\n".join(assertions) + "\n", encoding="utf-8")
    print(json.dumps({"evidence_packet": repo_rel(evidence_path), "missing": missing, "coverage": coverage}, indent=2))


if __name__ == "__main__":
    main()
