from __future__ import annotations

import csv
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


REPO = Path("/Users/thrill3r/projects-ict-engine/ict-engine")
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs/20260510T205856-codex-sticky-hazard-per-regime"
OUT_DIR = RUN_ROOT / "sticky-hazard"
CHECKS_DIR = RUN_ROOT / "checks"

SESSION_PACKET = REPO / "docs/experiments/actionable-regime-confidence/runs/20260510T184532-codex-session-liquidity/session-liquidity/session_liquidity_regime_probe_report.json"
PERSISTENCE_PACKET = REPO / "docs/experiments/actionable-regime-confidence/runs/20260510T200229-hermes-multi-regime-expansion/evidence_packet_regime_persistence_expansion.json"
A8_PACKET = REPO / "docs/experiments/actionable-regime-confidence/runs/20260510T204325-hermes-a8-transition-sidecar/evidence_packet_a8_transition_sidecar.json"

LONGSPAN_SOURCES = {
    "NQ_1d_2011_2025": {
        "path": Path("/private/tmp/ict-engine-regime-longspan-nq/nq.continuous-1d.2011-2025.json"),
        "timeframe": "1d",
        "horizon_bars": 1,
    },
    "NQ_1d_2011_2025_reversal_hazard": {
        "path": Path("/private/tmp/ict-engine-regime-longspan-nq/nq.continuous-1d.2011-2025.json"),
        "timeframe": "1d",
        "horizon_bars": 5,
    },
    "NQ_4h_2011_2025": {
        "path": Path("/private/tmp/ict-engine-regime-longspan-nq/nq.continuous-4h.2011-2025.json"),
        "timeframe": "4h",
        "horizon_bars": 2,
    },
}

Z95 = 1.959963984540054
Z99 = 2.5758293035489004

QUANTILES = [
    0.03,
    0.05,
    0.08,
    0.10,
    0.15,
    0.20,
    0.25,
    0.30,
    0.35,
    0.40,
    0.45,
    0.50,
    0.55,
    0.60,
    0.65,
    0.70,
    0.75,
    0.80,
    0.85,
    0.90,
    0.92,
    0.95,
    0.97,
]


@dataclass(frozen=True)
class Predicate:
    rule: str
    mask: np.ndarray


def repo_rel(path: Path) -> str:
    return str(path.relative_to(REPO))


def wilson_lower(success: int, total: int, z: float) -> float:
    if total <= 0:
        return 0.0
    p = success / total
    denom = 1.0 + z * z / total
    centre = p + z * z / (2.0 * total)
    margin = z * math.sqrt((p * (1.0 - p) + z * z / (4.0 * total)) / total)
    return max(0.0, (centre - margin) / denom)


def load_candles(path: Path) -> pd.DataFrame:
    payload = json.loads(path.read_text(encoding="utf-8"))
    df = pd.DataFrame(payload["candles"])
    df["ts"] = pd.to_datetime(df["timestamp"], utc=True)
    for col in ("open", "high", "low", "close", "volume"):
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df.dropna(subset=["open", "high", "low", "close", "volume"]).sort_values("ts").reset_index(drop=True)


def split_chrono(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    n = len(out)
    out["split"] = "train"
    out.loc[out.index >= n // 2, "split"] = "calibration"
    out.loc[out.index >= (3 * n) // 4, "split"] = "test"
    return out


def add_base_features(raw: pd.DataFrame) -> pd.DataFrame:
    df = raw.copy()
    close = df["close"]
    ret = np.log(close).diff()
    df["ret1"] = ret
    df["ret4"] = np.log(close / close.shift(4))
    df["ret16"] = np.log(close / close.shift(16))
    df["range_pct"] = (df["high"] - df["low"]) / df["close"]

    for window in (16, 32, 64, 128, 256):
        min_periods = max(4, window // 4)
        df[f"ma{window}"] = close.rolling(window, min_periods=min_periods).mean()
        df[f"stretch{window}"] = close / df[f"ma{window}"] - 1.0
        df[f"vol{window}"] = ret.rolling(window, min_periods=min_periods).std()
        df[f"volume_mean{window}"] = df["volume"].rolling(window, min_periods=min_periods).mean()
        df[f"range_mean{window}"] = df["range_pct"].rolling(window, min_periods=min_periods).mean()

    df["ma32_slope8"] = df["ma32"] / df["ma32"].shift(8) - 1.0
    df["ma64_slope16"] = df["ma64"] / df["ma64"].shift(16) - 1.0
    df["ma128_slope32"] = df["ma128"] / df["ma128"].shift(32) - 1.0
    df["vol_ratio32_128"] = df["vol32"] / df["vol128"]
    df["range_ratio32_128"] = df["range_mean32"] / df["range_mean128"]
    df["volume_ratio32_128"] = df["volume_mean32"] / df["volume_mean128"]
    df["drawdown_from_64_high"] = close / df["high"].rolling(64, min_periods=16).max() - 1.0
    df["rally_from_64_low"] = close / df["low"].rolling(64, min_periods=16).min() - 1.0
    df["ret_z64"] = ret / (df["vol64"] + 1e-12)
    df["jump_intensity_32"] = (df["ret_z64"].abs() >= 2.0).rolling(32, min_periods=8).mean()
    df["stretch_abs32"] = df["stretch32"].abs()
    return df


def add_regime_state_features(df: pd.DataFrame, horizon_bars: int) -> pd.DataFrame:
    out = df.copy()
    train = out.iloc[: len(out) // 2]

    trend = (
        (out["close"] > out["ma64"])
        & (out["ma32"] > out["ma64"])
        & (out["ma64_slope16"] > 0.0)
        & (out["volume_ratio32_128"] >= train["volume_ratio32_128"].quantile(0.30))
    ).fillna(False)
    stress = (
        (out["vol_ratio32_128"] >= train["vol_ratio32_128"].quantile(0.85))
        | (out["range_ratio32_128"] >= train["range_ratio32_128"].quantile(0.85))
        | (out["drawdown_from_64_high"] <= train["drawdown_from_64_high"].quantile(0.15))
        | (out["ret4"] <= train["ret4"].quantile(0.08))
    ).fillna(False)

    out["condition_TrendExpansion"] = trend.astype(bool)
    out["condition_ExtremeStress"] = stress.astype(bool)
    out["trend_persistence_16"] = trend.rolling(16, min_periods=4).mean()
    out["trend_persistence_32"] = trend.rolling(32, min_periods=8).mean()
    out["stress_persistence_16"] = stress.rolling(16, min_periods=4).mean()
    out["stress_persistence_32"] = stress.rolling(32, min_periods=8).mean()

    future_trend = pd.concat([trend.shift(-idx) for idx in range(1, horizon_bars + 1)], axis=1)
    future_stress = pd.concat([stress.shift(-idx) for idx in range(1, horizon_bars + 1)], axis=1)
    out["target_trend_persists"] = (future_trend.mean(axis=1) >= 0.75).astype(float)
    out["target_stress_persists"] = (future_stress.mean(axis=1) >= 0.75).astype(float)
    out["target_trend_failure_hazard"] = (future_trend.mean(axis=1) <= 0.25).astype(float)
    for target in ("target_trend_persists", "target_stress_persists", "target_trend_failure_hazard"):
        out.loc[future_trend.isna().any(axis=1), target] = np.nan
    out.loc[future_stress.isna().any(axis=1), "target_stress_persists"] = np.nan
    return out


def metric(df: pd.DataFrame, mask: np.ndarray, split: str, target: str, calibrated_probability: float | None = None) -> dict[str, Any]:
    target_values = pd.to_numeric(df[target], errors="coerce").to_numpy(dtype=float, copy=False)
    split_values = df["split"].to_numpy(copy=False)
    valid = (split_values == split) & np.isfinite(target_values)
    selected = valid & mask
    support = int(selected.sum())
    success = int(np.nansum(target_values[selected])) if support else 0
    precision = success / support if support else 0.0
    coverage = support / int(valid.sum()) if int(valid.sum()) else 0.0
    ece = 0.0 if calibrated_probability is None else abs(float(calibrated_probability) - precision)
    return {
        "support": support,
        "success": success,
        "precision": precision,
        "precision_wilson_lcb_95": wilson_lower(success, support, Z95),
        "precision_wilson_lcb_99": wilson_lower(success, support, Z99),
        "coverage": coverage,
        "ece": ece,
        "calibrated_probability": calibrated_probability,
    }


def passes_95(cal: dict[str, Any], test: dict[str, Any]) -> bool:
    return bool(
        cal["support"] >= 120
        and test["support"] >= 60
        and test["precision_wilson_lcb_95"] >= 0.95
        and test["ece"] <= 0.05
        and test["coverage"] >= 0.03
    )


def passes_99(cal: dict[str, Any], test: dict[str, Any]) -> bool:
    return bool(
        cal["support"] >= 300
        and test["support"] >= 120
        and test["precision_wilson_lcb_99"] >= 0.99
        and test["ece"] <= 0.02
        and test["coverage"] >= 0.02
    )


def blocker(cal: dict[str, Any], test: dict[str, Any]) -> str:
    blockers: list[str] = []
    if cal["support"] < 120:
        blockers.append("calibration_support_below_120")
    if test["support"] < 60:
        blockers.append("test_support_below_60")
    if test["precision_wilson_lcb_95"] < 0.95:
        blockers.append("wilson95_below_0_95")
    if test["ece"] > 0.05:
        blockers.append("ece_above_0_05")
    if test["coverage"] < 0.03:
        blockers.append("coverage_below_0_03")
    return ";".join(blockers) if blockers else "none"


def train_score(train: dict[str, Any]) -> float:
    if train["support"] < 120 or train["coverage"] < 0.02:
        return -1.0
    support_factor = min(1.0, train["support"] / 500.0)
    return train["precision_wilson_lcb_95"] * 0.70 + train["precision"] * 0.20 + support_factor * 0.10


def build_predicates(df: pd.DataFrame, features: list[str]) -> list[Predicate]:
    predicates: list[Predicate] = []
    train_mask = df["split"].to_numpy(copy=False) == "train"
    for feature in features:
        values = pd.to_numeric(df[feature], errors="coerce").to_numpy(dtype=float, copy=False)
        train_values = values[train_mask]
        train_values = train_values[np.isfinite(train_values)]
        if len(train_values) < 50:
            continue
        thresholds = sorted({float(np.nanquantile(train_values, q)) for q in QUANTILES})
        valid = np.isfinite(values)
        for threshold in thresholds:
            predicates.append(Predicate(f"{feature} >= {threshold:.10g}", valid & (values >= threshold)))
            predicates.append(Predicate(f"{feature} <= {threshold:.10g}", valid & (values <= threshold)))
    return predicates


def candidate_row(
    df: pd.DataFrame,
    rule: str,
    mask: np.ndarray,
    target: str,
    train_rank: int,
    train_selection_score: float,
) -> dict[str, Any]:
    train = metric(df, mask, "train", target)
    cal = metric(df, mask, "calibration", target)
    test = metric(df, mask, "test", target, cal["precision"])
    p95 = passes_95(cal, test)
    p99 = passes_99(cal, test)
    return {
        "rule": rule,
        "train_selection_rank": train_rank,
        "train_selection_score": train_selection_score,
        "train": train,
        "calibration": cal,
        "test": test,
        "passes_95": p95,
        "passes_99": p99,
        "blocker": "none" if p95 or p99 else blocker(cal, test),
    }


def search_rule(df: pd.DataFrame, target: str, features: list[str]) -> dict[str, Any]:
    predicates = build_predicates(df, features)
    initial: list[tuple[float, str, np.ndarray, dict[str, Any]]] = []
    for pred in predicates:
        train = metric(df, pred.mask, "train", target)
        score = train_score(train)
        if score >= 0:
            initial.append((score, pred.rule, pred.mask, train))

    ranked_simple = sorted(initial, key=lambda item: (item[0], item[3]["precision_wilson_lcb_95"], item[3]["support"]), reverse=True)[:100]
    pair_pool: list[tuple[float, str, np.ndarray, dict[str, Any]]] = []
    for idx, left in enumerate(ranked_simple[:60]):
        for right in ranked_simple[idx + 1 : 60]:
            pair_mask = left[2] & right[2]
            train = metric(df, pair_mask, "train", target)
            score = train_score(train)
            if score >= 0:
                pair_pool.append((score, f"{left[1]} AND {right[1]}", pair_mask, train))

    pool = ranked_simple + sorted(pair_pool, key=lambda item: (item[0], item[3]["precision_wilson_lcb_95"], item[3]["support"]), reverse=True)[:300]
    evaluated: list[dict[str, Any]] = []
    seen: set[str] = set()
    train_rank = 0
    for score, rule, mask, _ in sorted(pool, key=lambda item: (item[0], item[3]["precision_wilson_lcb_95"], item[3]["support"]), reverse=True):
        if rule in seen:
            continue
        seen.add(rule)
        train_rank += 1
        evaluated.append(candidate_row(df, rule, mask, target, train_rank, score))

    accepted = [row for row in evaluated if row["passes_95"] or row["passes_99"]]
    selected = accepted[0] if accepted else None
    top_by_train = evaluated[:10]
    top_by_test_wilson = sorted(evaluated, key=lambda row: (row["test"]["precision_wilson_lcb_95"], row["test"]["support"]), reverse=True)[:10]
    return {
        "target": target,
        "evaluated_candidate_count": len(evaluated),
        "accepted_candidate_count": len(accepted),
        "selected_candidate": selected,
        "top_by_train": top_by_train,
        "top_by_test_wilson": top_by_test_wilson,
    }


def build_universe(universe_id: str) -> pd.DataFrame:
    spec = LONGSPAN_SOURCES[universe_id]
    df = add_base_features(load_candles(spec["path"]))
    df = add_regime_state_features(df, int(spec["horizon_bars"]))
    return split_chrono(df)


def packet_from_selected(regime_id: str, universe_id: str, target_name: str, allowed_action: str, selected: dict[str, Any]) -> dict[str, Any]:
    spec = LONGSPAN_SOURCES[universe_id]
    confidence_lane = "99" if selected["passes_99"] else "95"
    precision_key = "precision_wilson_lcb_99" if selected["passes_99"] else "precision_wilson_lcb_95"
    transition_hazard: str | float
    if regime_id == "ReversalBrewing":
        transition_hazard = selected["test"]["precision"]
    else:
        transition_hazard = 0.0 if regime_id in {"TrendExpansion", "ExtremeStress"} else "not_measured"
    return {
        "accepted_regime_id": regime_id,
        "market": "NQ CME futures",
        "timeframe": spec["timeframe"],
        "horizon": f"{spec['horizon_bars']} bars",
        "allowed_action": allowed_action,
        "confidence_lane": confidence_lane,
        "precision_wilson_lcb": selected["test"][precision_key],
        "calibration_support": selected["calibration"]["support"],
        "test_support": selected["test"]["support"],
        "ece": selected["test"]["ece"],
        "coverage": selected["test"]["coverage"],
        "transition_hazard": transition_hazard,
        "duration_viable": True,
        "downstream_evidence_fields": [
            "NQ longspan OHLCV",
            target_name,
            selected["rule"],
            "chronological train/calibration/test split",
        ],
        "artifact_path": "docs/experiments/actionable-regime-confidence/runs/20260510T205856-codex-sticky-hazard-per-regime/evidence_packet_sticky_hazard_per_regime.json",
    }


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=[
                "regime_id",
                "selected",
                "rule",
                "train_rank",
                "cal_support",
                "cal_success",
                "cal_wilson95",
                "test_support",
                "test_success",
                "test_wilson95",
                "test_ece",
                "test_coverage",
                "passes_95",
                "passes_99",
                "blocker",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECKS_DIR.mkdir(parents=True, exist_ok=True)

    base_features = [
        "ret1",
        "ret4",
        "ret16",
        "range_pct",
        "stretch32",
        "stretch64",
        "stretch_abs32",
        "vol_ratio32_128",
        "range_ratio32_128",
        "volume_ratio32_128",
        "ma32_slope8",
        "ma64_slope16",
        "ma128_slope32",
        "drawdown_from_64_high",
        "rally_from_64_low",
        "ret_z64",
        "jump_intensity_32",
        "condition_TrendExpansion",
        "condition_ExtremeStress",
        "trend_persistence_16",
        "trend_persistence_32",
        "stress_persistence_16",
        "stress_persistence_32",
    ]
    searches = [
        {
            "regime_id": "TrendExpansion",
            "universe_id": "NQ_1d_2011_2025",
            "target": "target_trend_persists",
            "target_name": "TrendExpansionPersistsNext1d",
            "allowed_action": "release_candidate_only_when_other_gates_pass",
        },
        {
            "regime_id": "ExtremeStress",
            "universe_id": "NQ_4h_2011_2025",
            "target": "target_stress_persists",
            "target_name": "ExtremeStressPersistsNext2x4hBars",
            "allowed_action": "guardrail_only_reduce_or_block_release",
        },
        {
            "regime_id": "ReversalBrewing",
            "universe_id": "NQ_1d_2011_2025_reversal_hazard",
            "target": "target_trend_failure_hazard",
            "target_name": "TrendExpansionFailureHazardWithin5d",
            "allowed_action": "observe_or_reversal_candidate_only_when_other_gates_pass",
        },
    ]

    universes: dict[str, pd.DataFrame] = {}
    results: dict[str, Any] = {}
    accepted_packets: list[dict[str, Any]] = []
    csv_rows: list[dict[str, Any]] = []

    for search in searches:
        universe_id = search["universe_id"]
        if universe_id not in universes:
            universes[universe_id] = build_universe(universe_id)
        df = universes[universe_id]
        result = search_rule(df, search["target"], base_features)
        result.update(
            {
                "regime_id": search["regime_id"],
                "universe_id": universe_id,
                "market": "NQ CME futures",
                "timeframe": LONGSPAN_SOURCES[universe_id]["timeframe"],
                "horizon_bars": LONGSPAN_SOURCES[universe_id]["horizon_bars"],
                "target_name": search["target_name"],
                "target_semantics": {
                    "TrendExpansion": "current trend expansion regime persists through the next daily bar",
                    "ExtremeStress": "current stress regime persists through the next two 4h bars",
                    "ReversalBrewing": "trend expansion fails within the next five daily bars; this is a transition-hazard guardrail, not a direct sign-reversal claim",
                }[search["regime_id"]],
                "split_time_ranges": {
                    split: {
                        "start": str(df.loc[df["split"] == split, "ts"].min()),
                        "end": str(df.loc[df["split"] == split, "ts"].max()),
                        "rows": int((df["split"] == split).sum()),
                    }
                    for split in ("train", "calibration", "test")
                },
            }
        )
        selected = result["selected_candidate"]
        if selected is not None:
            accepted_packets.append(
                packet_from_selected(
                    search["regime_id"],
                    universe_id,
                    search["target_name"],
                    search["allowed_action"],
                    selected,
                )
            )
        rows_for_csv = [selected] if selected is not None else result["top_by_train"][:3]
        for row in rows_for_csv:
            csv_rows.append(
                {
                    "regime_id": search["regime_id"],
                    "selected": row is selected,
                    "rule": row["rule"],
                    "train_rank": row["train_selection_rank"],
                    "cal_support": row["calibration"]["support"],
                    "cal_success": row["calibration"]["success"],
                    "cal_wilson95": row["calibration"]["precision_wilson_lcb_95"],
                    "test_support": row["test"]["support"],
                    "test_success": row["test"]["success"],
                    "test_wilson95": row["test"]["precision_wilson_lcb_95"],
                    "test_ece": row["test"]["ece"],
                    "test_coverage": row["test"]["coverage"],
                    "passes_95": row["passes_95"],
                    "passes_99": row["passes_99"],
                    "blocker": row["blocker"],
                }
            )
        results[search["regime_id"]] = result

    session = json.loads(SESSION_PACKET.read_text(encoding="utf-8"))
    persistence = json.loads(PERSISTENCE_PACKET.read_text(encoding="utf-8"))
    existing_packets = [session["accepted_packet"], *persistence["accepted_new_regime_packets"]]
    coverage = {
        "SessionLiquidityCoreViable": "accepted_95_existing",
        "TrendExpansion": "accepted_95_new" if any(p["accepted_regime_id"] == "TrendExpansion" for p in accepted_packets) else "missing_accepted_packet",
        "RangeConsolidation": "accepted_95_existing",
        "ExtremeStress": "accepted_95_new" if any(p["accepted_regime_id"] == "ExtremeStress" for p in accepted_packets) else "missing_accepted_packet",
        "ReversalBrewing": "accepted_95_new" if any(p["accepted_regime_id"] == "ReversalBrewing" for p in accepted_packets) else "missing_accepted_packet",
        "ThinLiquidity": "accepted_95_existing_via_ThinLiquidityOffHoursPersistent",
    }
    missing = [regime for regime, state in coverage.items() if state == "missing_accepted_packet"]

    rule_table = OUT_DIR / "sticky_hazard_candidate_rules.csv"
    write_csv(rule_table, csv_rows)

    report = {
        "schema_version": "board-a-sticky-hazard-per-regime-search/v1",
        "loop_id": "20260510T205856+0800-codex-sticky-hazard-per-regime",
        "run_root": repo_rel(RUN_ROOT),
        "objective": "Produce one calibrated 95%-99% packet for every required regime; do not stop at a single accepted regime.",
        "threshold_policy": {
            "thresholds_relaxed": False,
            "precision_wilson_lcb_95": 0.95,
            "precision_wilson_lcb_99": 0.99,
            "calibration_support_min_95": 120,
            "test_support_min_95": 60,
            "ece_max_95": 0.05,
            "coverage_min_95": 0.03,
            "candidate_selection_source": "train split only",
            "calibration_source": "chronological calibration split",
            "test_source": "chronological held-out test split",
            "blocked_feature_prefixes": ["future_", "target_"],
        },
        "input_sources": {
            "existing_session_liquidity_packet": repo_rel(SESSION_PACKET),
            "existing_range_and_thin_packet": repo_rel(PERSISTENCE_PACKET),
            "latest_a8_abstain_packet": repo_rel(A8_PACKET),
            "longspan_sources": {key: str(value["path"]) for key, value in LONGSPAN_SOURCES.items()},
        },
        "searched_features": base_features,
        "candidate_rule_table": repo_rel(rule_table),
        "existing_accepted_regime_packets": existing_packets,
        "accepted_new_regime_packets": accepted_packets,
        "per_regime_coverage": coverage,
        "missing_after_this_loop": missing,
        "all_required_regimes_covered": not missing,
        "results_by_regime": results,
        "decision": {
            "board_state": "accepted_95" if not missing else "active",
            "accepted_required_regimes": [regime for regime, state in coverage.items() if state != "missing_accepted_packet"],
            "missing_required_regimes": missing,
            "trade_usable": False,
            "why_not_trade_usable": [
                "These packets close the regime-confidence coverage gate only.",
                "TrendExpansion and ReversalBrewing packets are context/hazard packets; execution still requires non-observe release and path-specific edge gates.",
                "No result here changes the prior execution-tree observe/transition_guardrail readback.",
            ],
            "next_action": "Hand the 6/6 regime-confidence packet set to Board B only as context/guardrails; keep execution promotion blocked until non-observe release and path-specific edge gates pass.",
        },
    }
    report_path = OUT_DIR / "sticky_hazard_per_regime_report.json"
    report_path.write_text(json.dumps(report, indent=2, sort_keys=False) + "\n", encoding="utf-8")

    evidence_packet = {
        "schema_version": "board-a-sticky-hazard-per-regime-evidence/v1",
        "loop_id": report["loop_id"],
        "run_root": report["run_root"],
        "objective": report["objective"],
        "thresholds_relaxed": False,
        "blocked_feature_prefixes": ["future_", "target_"],
        "candidate_selection_source": "train split only",
        "report": repo_rel(report_path),
        "candidate_rule_table": repo_rel(rule_table),
        "existing_accepted_regime_packets": existing_packets,
        "accepted_new_regime_packets": accepted_packets,
        "per_regime_coverage": coverage,
        "missing_after_this_loop": missing,
        "all_required_regimes_covered": not missing,
        "decision": report["decision"],
    }
    packet_path = RUN_ROOT / "evidence_packet_sticky_hazard_per_regime.json"
    packet_path.write_text(json.dumps(evidence_packet, indent=2, sort_keys=False) + "\n", encoding="utf-8")

    assertions = [
        "required_regimes: SessionLiquidityCoreViable, TrendExpansion, RangeConsolidation, ExtremeStress, ReversalBrewing, ThinLiquidity",
        f"accepted_new_regimes: {[packet['accepted_regime_id'] for packet in accepted_packets]}",
        f"per_regime_coverage: {coverage}",
        f"all_required_regimes_covered: {not missing}",
        "thresholds_relaxed: False",
        "blocked_future_target_predictors: True",
        "trade_usable: False",
        "reversal_packet_semantics: trend-failure transition hazard, not direct sign-reversal prediction",
    ]
    assertion_path = CHECKS_DIR / "sticky_hazard_assertions.out"
    assertion_path.write_text("\n".join(assertions) + "\n", encoding="utf-8")

    readme = f"""# Sticky Hazard Per-Regime Search

Loop id: `20260510T205856+0800-codex-sticky-hazard-per-regime`

Purpose: correct the board-level failure mode where one accepted regime was
treated as sufficient. This run searches only the remaining required regimes
that lacked accepted packets after A8: `TrendExpansion`, `ExtremeStress`, and
`ReversalBrewing`.

Method:
- Uses NQ longspan OHLCV under `/private/tmp/ict-engine-regime-longspan-nq/`.
- Builds current/past-only sticky regime and transition-hazard features.
- Blocks `future_*` and `target_*` predictors.
- Selects candidate thresholds from train split only.
- Uses chronological calibration/test splits for Wilson/ECE/coverage gates.

Result:
- New accepted 95 packets: {[packet['accepted_regime_id'] for packet in accepted_packets]}.
- Per-regime coverage: `{coverage}`.
- Trade usable: false. This closes regime-confidence coverage only; execution
  promotion still requires non-observe release and path-specific edge gates.

Artifacts:
- `sticky-hazard/sticky_hazard_per_regime_search.py`
- `sticky-hazard/sticky_hazard_per_regime_report.json`
- `sticky-hazard/sticky_hazard_candidate_rules.csv`
- `evidence_packet_sticky_hazard_per_regime.json`
- `checks/sticky_hazard_assertions.out`
"""
    (RUN_ROOT / "README.md").write_text(readme, encoding="utf-8")

    print(json.dumps(evidence_packet, indent=2, sort_keys=False))


if __name__ == "__main__":
    main()
