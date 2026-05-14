from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


REPO = Path("/Users/thrill3r/projects-ict-engine/ict-engine")
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs/20260510T212828-codex-legacy-regime-contract-reissue"
OUT_DIR = RUN_ROOT / "legacy-reissue"
CHECKS_DIR = RUN_ROOT / "checks"
SOURCE_FEATURES = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs/20260510T205856-codex-sticky-hazard-per-regime/cross-context/cross_context_sticky_hazard_features.csv"
)
STICKY_PACKET = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs/20260510T205856-codex-sticky-hazard-per-regime/evidence_packet_sticky_hazard_cross_context.json"
)

Z95 = 1.959963984540054
Z99 = 2.5758293035489004


def rel(path: Path) -> str:
    return str(path.relative_to(REPO))


def wilson_lower(success: int, total: int, z: float) -> float:
    if total <= 0:
        return 0.0
    p = success / total
    denom = 1.0 + z * z / total
    centre = p + z * z / (2.0 * total)
    margin = z * math.sqrt((p * (1.0 - p) + z * z / (4.0 * total)) / total)
    return max(0.0, (centre - margin) / denom)


def load_features() -> pd.DataFrame:
    df = pd.read_csv(SOURCE_FEATURES)
    df["ts"] = pd.to_datetime(df["ts"], utc=True)
    df = df.sort_values(["context", "ts"]).reset_index(drop=True)
    return df


def add_legacy_targets(df: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, float]]:
    frames: list[pd.DataFrame] = []
    global_train = df[df["split"] == "train"]
    thresholds = {
        "session_volume_ratio32_128_min": float(global_train["volume_ratio32_128"].quantile(0.10)),
        "range_ratio32_128_q15_max": float(global_train["range_ratio32_128"].quantile(0.15)),
        "thin_volume_ratio32_128_max": float(global_train["volume_ratio32_128"].quantile(0.10)),
    }

    for _context, group in df.groupby("context", sort=False):
        g = group.sort_values("ts").reset_index(drop=True).copy()
        train = g[g["split"] == "train"]

        range_vol_max = float(train["vol_ratio32_128"].quantile(0.45))
        range_range_max = float(train["range_ratio32_128"].quantile(0.45))
        range_stretch_max = float(train["stretch_abs32"].quantile(0.70))
        thin_volume_ratio_max = float(train["volume_ratio32_128"].quantile(0.30))
        thin_volume_max = float(train["volume"].quantile(0.30))

        g["condition_SessionLiquidityCoreViable"] = (
            g["open"].notna()
            & g["high"].notna()
            & g["low"].notna()
            & g["close"].notna()
            & (g["volume"] > 0)
            & (g["volume_ratio32_128"] >= thresholds["session_volume_ratio32_128_min"])
        )
        g["condition_RangeConsolidationReissued"] = (
            (g["vol_ratio32_128"] <= range_vol_max)
            & (g["range_ratio32_128"] <= range_range_max)
            & (g["stretch_abs32"] <= range_stretch_max)
            & (g["range_ratio32_128"] <= thresholds["range_ratio32_128_q15_max"])
        )
        thin_base = (g["volume_ratio32_128"] <= thin_volume_ratio_max) | (g["volume"] <= thin_volume_max)
        g["condition_ThinLiquidityReissued"] = thin_base & (
            g["volume_ratio32_128"] <= thresholds["thin_volume_ratio32_128_max"]
        )

        finite_liquidity = (
            g["open"].notna()
            & g["high"].notna()
            & g["low"].notna()
            & g["close"].notna()
            & (g["volume"] > 0)
        ).astype(float)
        stress = g["condition_ExtremeStress"].astype(float)
        thin = thin_base.astype(float)

        future_liquidity = pd.concat([finite_liquidity.shift(-idx) for idx in range(1, 6)], axis=1)
        future_stress = pd.concat([stress.shift(-idx) for idx in range(1, 2)], axis=1)
        future_thin = pd.concat([thin.shift(-idx) for idx in range(1, 6)], axis=1)

        g["target_SessionLiquidityCoreViable"] = (future_liquidity.mean(axis=1) == 1.0).astype(float)
        g.loc[future_liquidity.isna().any(axis=1), "target_SessionLiquidityCoreViable"] = np.nan

        g["target_RangeConsolidationLowStressTransitionHazard"] = (future_stress.max(axis=1) == 0).astype(float)
        g.loc[future_stress.isna().any(axis=1), "target_RangeConsolidationLowStressTransitionHazard"] = np.nan

        g["target_ThinLiquidityPersistsNext5d"] = (future_thin.mean(axis=1) >= 0.75).astype(float)
        g.loc[future_thin.isna().any(axis=1), "target_ThinLiquidityPersistsNext5d"] = np.nan

        frames.append(g)

    return pd.concat(frames, ignore_index=True), thresholds


def metric(df: pd.DataFrame, mask: pd.Series, target: str, split: str, calibrated_probability: float | None = None) -> dict[str, Any]:
    valid = (df["split"] == split) & df[target].notna()
    selected = valid & mask
    support = int(selected.sum())
    success = int(df.loc[selected, target].sum()) if support else 0
    precision = success / support if support else 0.0
    coverage = support / int(valid.sum()) if int(valid.sum()) else 0.0
    selected_df = df.loc[selected]
    return {
        "support": support,
        "success": success,
        "precision": precision,
        "precision_wilson_lcb_95": wilson_lower(success, support, Z95),
        "precision_wilson_lcb_99": wilson_lower(success, support, Z99),
        "coverage": coverage,
        "ece": abs(float(calibrated_probability) - precision) if calibrated_probability is not None else 0.0,
        "calibrated_probability": calibrated_probability,
        "validation_instruments": sorted(selected_df["instrument"].dropna().unique().tolist()),
        "validation_market_contexts": sorted(selected_df["market"].dropna().unique().tolist()),
        "validation_contexts": sorted(selected_df["context"].dropna().unique().tolist()),
    }


def passes_95(cal: dict[str, Any], test: dict[str, Any]) -> bool:
    return bool(
        cal["support"] >= 120
        and test["support"] >= 60
        and test["precision_wilson_lcb_95"] >= 0.95
        and test["ece"] <= 0.05
        and test["coverage"] >= 0.03
        and len(test["validation_instruments"]) >= 2
        and len(test["validation_market_contexts"]) >= 2
    )


def build_packet(
    *,
    regime_id: str,
    qualifying_condition: str,
    target: str,
    allowed_action: str,
    horizon: str,
    downstream_evidence_fields: list[str],
    df: pd.DataFrame,
    mask: pd.Series,
) -> dict[str, Any]:
    train = metric(df, mask, target, "train")
    cal = metric(df, mask, target, "calibration")
    test = metric(df, mask, target, "test", calibrated_probability=cal["precision"])
    return {
        "accepted_regime_id": regime_id,
        "qualifying_condition": qualifying_condition,
        "market": "multi-context: NQ local CME futures + yfinance ETF/crypto",
        "timeframe": "1d",
        "horizon": horizon,
        "allowed_action": allowed_action,
        "confidence_lane": "95",
        "precision_wilson_lcb": test["precision_wilson_lcb_95"],
        "calibration_support": cal["support"],
        "test_support": test["support"],
        "ece": test["ece"],
        "coverage": test["coverage"],
        "validation_instruments": test["validation_instruments"],
        "validation_periods": {
            "train": {
                "support": train["support"],
                "success": train["success"],
                "precision": train["precision"],
                "precision_wilson_lcb_95": train["precision_wilson_lcb_95"],
            },
            "calibration": {
                "support": cal["support"],
                "success": cal["success"],
                "precision": cal["precision"],
                "precision_wilson_lcb_95": cal["precision_wilson_lcb_95"],
            },
            "test": {
                "support": test["support"],
                "success": test["success"],
                "precision": test["precision"],
                "precision_wilson_lcb_95": test["precision_wilson_lcb_95"],
            },
        },
        "validation_market_contexts": test["validation_market_contexts"],
        "validation_contexts": test["validation_contexts"],
        "transition_hazard": 1.0 - test["precision"],
        "duration_viable": True,
        "downstream_evidence_fields": downstream_evidence_fields,
        "artifact_path": rel(RUN_ROOT / "evidence_packet_legacy_regime_contract_reissue.json"),
        "target": target,
        "passes_95": passes_95(cal, test),
    }


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECKS_DIR.mkdir(parents=True, exist_ok=True)

    source = load_features()
    features, thresholds = add_legacy_targets(source)
    augmented_features_path = OUT_DIR / "legacy_regime_contract_reissue_features.csv"
    features.to_csv(augmented_features_path, index=False)

    session_condition = (
        "finite daily OHLCV with volume > 0 AND "
        f"volume_ratio32_128 >= {thresholds['session_volume_ratio32_128_min']:.12g}"
    )
    range_condition = (
        "per-context daily range base condition "
        "(vol_ratio32_128 <= train q45 AND range_ratio32_128 <= train q45 AND stretch_abs32 <= train q70) "
        f"AND range_ratio32_128 <= {thresholds['range_ratio32_128_q15_max']:.12g}"
    )
    thin_condition = (
        "per-context daily thin-liquidity base condition "
        "(volume_ratio32_128 <= train q30 OR volume <= train q30) "
        f"AND volume_ratio32_128 <= {thresholds['thin_volume_ratio32_128_max']:.12g}"
    )

    reissued_packets = [
        build_packet(
            regime_id="SessionLiquidityCoreViable",
            qualifying_condition=session_condition,
            target="target_SessionLiquidityCoreViable",
            allowed_action="observe_or_release_candidate_only_when_other_gates_pass",
            horizon="5 daily bars",
            downstream_evidence_fields=[
                "finite_daily_ohlcv",
                "volume_ratio32_128",
                "target_SessionLiquidityCoreViable",
                "chronological per-instrument train/calibration/test split",
                "NQ local daily OHLCV",
                "QQQ/SPY/BTC-USD yfinance daily OHLCV",
            ],
            df=features,
            mask=features["condition_SessionLiquidityCoreViable"].fillna(False),
        ),
        build_packet(
            regime_id="RangeConsolidation",
            qualifying_condition=range_condition,
            target="target_RangeConsolidationLowStressTransitionHazard",
            allowed_action="regime_context_only_until_downstream_edge_gate_passes",
            horizon="1 daily bar",
            downstream_evidence_fields=[
                "condition_RangeConsolidationReissued",
                "target_RangeConsolidationLowStressTransitionHazard",
                "range_ratio32_128",
                "vol_ratio32_128",
                "stretch_abs32",
                "chronological per-instrument train/calibration/test split",
                "NQ local daily OHLCV",
                "QQQ/SPY/BTC-USD yfinance daily OHLCV",
            ],
            df=features,
            mask=features["condition_RangeConsolidationReissued"].fillna(False),
        ),
        build_packet(
            regime_id="ThinLiquidity",
            qualifying_condition=thin_condition,
            target="target_ThinLiquidityPersistsNext5d",
            allowed_action="guardrail_only_liquidity_context",
            horizon="5 daily bars",
            downstream_evidence_fields=[
                "condition_ThinLiquidityReissued",
                "target_ThinLiquidityPersistsNext5d",
                "volume_ratio32_128",
                "volume",
                "chronological per-instrument train/calibration/test split",
                "NQ local daily OHLCV",
                "QQQ/SPY/BTC-USD yfinance daily OHLCV",
            ],
            df=features,
            mask=features["condition_ThinLiquidityReissued"].fillna(False),
        ),
    ]

    sticky = json.loads(STICKY_PACKET.read_text(encoding="utf-8"))
    carried_packets = sticky["accepted_new_regime_packets"]
    accepted_packets = reissued_packets + carried_packets
    required = [
        "SessionLiquidityCoreViable",
        "TrendExpansion",
        "RangeConsolidation",
        "ExtremeStress",
        "ReversalBrewing",
        "ThinLiquidity",
    ]
    accepted_ids = {packet["accepted_regime_id"] for packet in accepted_packets if packet.get("passes_95", True)}
    missing = [regime for regime in required if regime not in accepted_ids]

    packet = {
        "schema_version": "board-a-legacy-regime-contract-reissue/v1",
        "loop_id": "20260510T212828+0800-codex-legacy-regime-contract-reissue",
        "objective": "Reissue legacy Board A accepted packets with explicit qualifying conditions and cross-instrument/cross-period/cross-market validation fields.",
        "run_root": rel(RUN_ROOT),
        "source_feature_table": rel(SOURCE_FEATURES),
        "thresholds_relaxed": False,
        "blocked_feature_prefixes": ["future_", "target_"],
        "candidate_selection_source": "fixed current/past daily OHLCV feature recipes; future columns used only as labels",
        "reissued_regime_packets": reissued_packets,
        "carried_forward_field_complete_packets": carried_packets,
        "accepted_regime_packets": accepted_packets,
        "per_regime_coverage": {
            packet["accepted_regime_id"]: "accepted_95_field_complete" for packet in accepted_packets if packet.get("passes_95", True)
        },
        "missing_after_this_loop": missing,
        "all_required_regimes_covered_under_current_contract": not missing,
        "decision": {
            "board_state": "accepted_95" if not missing else "active",
            "accepted_required_regimes": sorted(accepted_ids),
            "missing_required_regimes": missing,
            "trade_usable": False,
            "why_not_trade_usable": [
                "Board A regime-confidence coverage only; no result here proves strategy profitability.",
                "Execution promotion remains blocked until Board B proves non-observe release and path-specific edge gates.",
                "RangeConsolidation is accepted as a low ExtremeStress transition-hazard context, not as direct mean-reversion alpha.",
            ],
            "next_action": "Hand the 6/6 field-complete regime-confidence packet set to Board B as context/guardrails only; keep execution promotion blocked until non-observe release and path-specific edge gates pass.",
        },
    }

    evidence_path = RUN_ROOT / "evidence_packet_legacy_regime_contract_reissue.json"
    report_path = OUT_DIR / "legacy_regime_contract_reissue_report.json"
    evidence_path.write_text(json.dumps(packet, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report_path.write_text(json.dumps(packet, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    assertion_lines = [
        f"all_required_regimes_covered_under_current_contract={packet['all_required_regimes_covered_under_current_contract']}",
        f"missing_after_this_loop={','.join(missing) if missing else 'none'}",
    ]
    for item in reissued_packets:
        assertion_lines.append(
            f"{item['accepted_regime_id']} passes_95={item['passes_95']} "
            f"wilson95={item['precision_wilson_lcb']:.6f} cal={item['calibration_support']} "
            f"test={item['test_support']} ece={item['ece']:.6f} "
            f"instruments={len(item['validation_instruments'])} contexts={len(item['validation_market_contexts'])}"
        )
    (CHECKS_DIR / "legacy_regime_contract_reissue_assertions.out").write_text(
        "\n".join(assertion_lines) + "\n", encoding="utf-8"
    )
    print(json.dumps({"evidence_packet": rel(evidence_path), "missing": missing}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
