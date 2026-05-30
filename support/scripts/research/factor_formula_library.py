from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


BASE_SEEDS: list[dict[str, Any]] = [
    {
        "seed_id": "qlib_alpha158_momentum_roc",
        "family": "momentum",
        "source": "qlib_alpha158_style",
        "expression": "roc(close, n) * rank(volume / mean(volume, n))",
        "required_fields": ["close", "volume"],
        "default_params": {"n": 20},
        "allowed_regimes": ["TrendExpansion", "HighLiquidity"],
        "mutation_hints": {"n": [10, 20, 40], "volume_weight": [0.5, 1.0, 1.5]},
        "hotplug_ready": True,
    },
    {
        "seed_id": "qlib_alpha158_vol_breakout",
        "family": "volatility_breakout",
        "source": "qlib_alpha158_style",
        "expression": "zscore(true_range, n) * sign(close - rolling_high(close, n))",
        "required_fields": ["high", "low", "close"],
        "default_params": {"n": 20},
        "allowed_regimes": ["TrendExpansion", "ExtremeStress"],
        "mutation_hints": {"n": [14, 20, 50], "z_threshold": [1.0, 1.5, 2.0]},
        "hotplug_ready": True,
    },
    {
        "seed_id": "alpha101_rank_decay_reversion",
        "family": "mean_reversion",
        "source": "alpha101_operator_skeleton",
        "expression": "-rank(decay_linear(delta(close, d), n))",
        "required_fields": ["close"],
        "default_params": {"d": 3, "n": 10},
        "allowed_regimes": ["RangeConsolidation", "ReversalBrewing"],
        "mutation_hints": {"d": [1, 3, 5], "n": [5, 10, 20]},
        "hotplug_ready": True,
    },
    {
        "seed_id": "alpha101_corr_liquidity_pressure",
        "family": "liquidity",
        "source": "alpha101_operator_skeleton",
        "expression": "-rank(correlation(rank(close), rank(volume), n))",
        "required_fields": ["close", "volume"],
        "default_params": {"n": 10},
        "allowed_regimes": ["ThinLiquidity", "HighLiquidity"],
        "mutation_hints": {"n": [5, 10, 20], "sign": [-1, 1]},
        "hotplug_ready": True,
    },
    {
        "seed_id": "vrp_compression_regime",
        "family": "options_vrp",
        "source": "ict_engine_vrp_v2",
        "expression": "zscore(vix3m_level, n) - zscore(qqq_hv_level, n) + rank(vvix_over_vix)",
        "required_fields": ["vix3m_level", "qqq_hv_level", "vvix_over_vix"],
        "default_params": {"n": 60},
        "allowed_regimes": ["RangeConsolidation", "ReversalBrewing"],
        "mutation_hints": {"n": [30, 60, 120], "vvix_weight": [0.5, 1.0, 1.5]},
        "hotplug_ready": True,
    },
    {
        "seed_id": "ict_fvg_reclaim_quality",
        "family": "structure_ict",
        "source": "ict_engine_structure_family",
        "expression": "fvg_reclaim_score * liquidity_sweep_score * mtf_alignment",
        "required_fields": ["fvg_reclaim_score", "liquidity_sweep_score", "mtf_alignment"],
        "default_params": {"min_alignment": 0.5},
        "allowed_regimes": ["TrendExpansion", "ReversalBrewing"],
        "mutation_hints": {"min_alignment": [0.3, 0.5, 0.7], "sweep_weight": [0.5, 1.0, 1.5]},
        "hotplug_ready": True,
    },
    {
        "seed_id": "crowding_reversal_pressure",
        "family": "crowding",
        "source": "crowded_trades_skeleton",
        "expression": "rank(volume_zscore) * rank(rsi_extreme) * -sign(recent_return)",
        "required_fields": ["volume", "rsi", "close"],
        "default_params": {"lookback": 14},
        "allowed_regimes": ["ReversalBrewing", "ExtremeStress"],
        "mutation_hints": {"lookback": [7, 14, 28], "extreme_threshold": [0.8, 0.9, 0.95]},
        "hotplug_ready": True,
    },
    {
        "seed_id": "mtf_trend_resonance_breakout_v1",
        "family": "mtf_trend_resonance",
        "source": "donchian_turtle_supertrend_adx_keltner_atr_plus_tsmom_vol_state",
        "expression": (
            "primary_1m_breakout_or_pullback * "
            "mtf_trend_resonance(5m,15m,30m,1h,4h,1d) * "
            "atr_excursion_capacity * cost_guard * volatility_state_guard"
        ),
        "required_fields": [
            "open",
            "high",
            "low",
            "close",
            "volume",
            "donchian_high",
            "donchian_low",
            "supertrend_direction",
            "adx",
            "atr",
            "keltner_mid",
            "mtf_trend_resonance",
            "volatility_state",
            "instrument_cost_model",
        ],
        "default_params": {
            "candidate_policy": "trend_following_only",
            "branch_path_template": (
                "TrendExpansion -> MTFTrendContinuationOrPullback -> "
                "mtf_trend_resonance_breakout_v1"
            ),
            "base_timeframe": "1m",
            "context_timeframes": ["5m", "15m", "30m", "1h", "4h", "1d"],
            "entry_shapes": [
                "donchian_breakout_retest",
                "supertrend_adx_continuation",
                "keltner_atr_breakout_pullback",
            ],
            "min_mtf_aligned": 3,
            "donchian_lookback": 20,
            "adx_min": 18.0,
            "atr_excursion_min_bps": 18.0,
            "keltner_atr_mult": 1.5,
            "allowed_volatility_states": ["expanding", "controlled_high_vol"],
            "cost_model_status": "cost_model_unverified",
            "promotion_cost_verified": False,
            "promotion_requires": [
                "real_provider_or_retained_real_rows",
                "verified_instrument_cost_model",
                "survives_instrument_cost",
                "positive_trade_count",
                "same_root_downstream",
                "provider_parity",
                "validation_rows",
                "execution_materialization",
            ],
        },
        "allowed_regimes": ["TrendExpansion"],
        "mutation_hints": {
            "donchian_lookback": [10, 20, 40],
            "adx_min": [14.0, 18.0, 24.0],
            "atr_excursion_min_bps": [12.0, 18.0, 30.0],
            "min_mtf_aligned": [2, 3, 4],
            "keltner_atr_mult": [1.25, 1.5, 2.0],
        },
        "helper_module": "support.scripts.research.mtf_trend_resonance",
        "overlay_policy": "triple_barrier_meta_label_only_after_primary_event_survives_cost",
        "artifact_policy": "provider_rows_required_no_simulated_promotion",
        "hotplug_ready": True,
    },
    {
        "seed_id": "mim_cost_window_regime_filter_v1",
        "family": "intraday_momentum_cost_window",
        "source": "paper_intraday_momentum_transaction_costs_plus_hmm_side_info",
        "expression": (
            "sign(first_window_return) * "
            "low_cost_window(corwin_schultz_spread, basic_high_low_spread) * "
            "rvol * momentum_state_prob * entropy_guard"
        ),
        "required_fields": [
            "open",
            "high",
            "low",
            "close",
            "volume",
            "first_window_return",
            "corwin_schultz_spread",
            "basic_high_low_spread",
            "rvol",
            "momentum_state_prob",
            "posterior_entropy_proxy",
            "mtf_trend_resonance",
        ],
        "default_params": {
            "candidate_policy": "trend_following_only",
            "base_timeframe": "1m",
            "context_timeframes": ["5m", "15m", "30m", "1h", "4h", "1d"],
            "min_mtf_aligned": 2,
            "open_minutes": 30,
            "late_minutes": 30,
            "first_abs_return_min": 0.0015,
            "spread_max": 0.0065,
            "rvol_min": 0.60,
            "momentum_prob_min": 0.58,
            "entropy_max": 0.92,
            "cost_model_status": "cost_model_unverified",
            "promotion_cost_verified": False,
            "promotion_requires": [
                "real_provider_or_retained_real_rows",
                "verified_instrument_cost_model",
                "survives_instrument_cost",
                "positive_trade_count",
            ],
        },
        "allowed_regimes": ["TrendExpansion"],
        "mutation_hints": {
            "open_minutes": [15, 30, 45],
            "late_minutes": [15, 30, 60],
            "first_abs_return_min": [0.0010, 0.0015, 0.0025],
            "spread_max": [0.0045, 0.0065, 0.0080],
            "momentum_prob_min": [0.56, 0.60, 0.64],
            "entropy_max": [0.86, 0.92, 0.98],
        },
        "helper_module": "support.scripts.research.mim_cost_window_features",
        "artifact_policy": "provider_rows_required_no_simulated_promotion",
        "hotplug_ready": True,
    },
    {
        "seed_id": "cost_aware_triple_barrier_meta_gate_v1",
        "family": "cost_aware_event_labeling",
        "source": "FinMLKit_TBMLabel_min_ret_meta_labeling_plus_Lopez_de_Prado_triple_barrier",
        "source_urls": [
            "https://github.com/quantscious/finmlkit",
            "https://mlfinpy.readthedocs.io/en/latest/Labelling.html",
        ],
        "expression": (
            "primary_side * meta_label_probability_gate("
            "triple_barrier_label, p_hat, p_min) * "
            "event_return_capacity_bps >= "
            "verified_instrument_cost_edge_floor("
            "instrument_cost_model, instrument_cost_buffer_model)"
        ),
        "required_fields": [
            "open",
            "high",
            "low",
            "close",
            "volume",
            "primary_side",
            "target_volatility",
            "event_return_capacity_bps",
            "instrument_cost_model",
            "instrument_cost_buffer_model",
            "meta_label_probability",
            "triple_barrier_label",
            "vertical_barrier_bars",
        ],
        "default_params": {
            "candidate_policy": "cost_gate_before_downstream",
            "branch_path_template": (
                "TrendExpansion -> CostAwareEventLabeling -> "
                "cost_aware_triple_barrier_meta_gate_v1"
            ),
            "base_timeframe": "1m",
            "context_timeframes": ["5m", "15m", "30m", "1h", "4h", "1d"],
            "cost_model_status": "cost_model_unverified",
            "promotion_cost_verified": False,
            "instrument_cost_buffer_model": "unverified_fail_closed",
            "min_ret_bps": 14.0,
            "horizontal_barriers": [1.5, 1.5],
            "vertical_barrier_bars": 30,
            "p_min": 0.58,
            "max_trades_per_day": 3,
            "max_trade_gap_days": 3.0,
            "promotion_requires": [
                "real_provider_or_retained_real_rows",
                "verified_instrument_cost_model",
                "survives_instrument_cost",
                "positive_trade_count",
                "same_root_downstream",
                "provider_parity",
                "walk_forward_or_forward_bucket_validation",
                "execution_materialization",
            ],
        },
        "allowed_regimes": ["TrendExpansion"],
        "mutation_hints": {
            "min_ret_bps": [10.0, 14.0, 18.0, 24.0],
            "horizontal_barriers": [[1.0, 1.5], [1.5, 1.5], [1.5, 2.0]],
            "vertical_barrier_bars": [15, 30, 60],
            "p_min": [0.55, 0.58, 0.62, 0.66],
        },
        "helper_module": "support.scripts.research.mim_cost_window_gate_report",
        "overlay_policy": "use_as_admission_gate_before_pre_bayes_bbn_catboost_execution_tree",
        "artifact_policy": "provider_rows_required_no_simulated_promotion",
        "hotplug_ready": True,
    },
]


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=False) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=False) + "\n")


def build_formula_library(families: list[str] | None = None) -> dict[str, Any]:
    family_filter = {family.strip() for family in families or [] if family.strip()}
    seeds = [dict(seed) for seed in BASE_SEEDS if not family_filter or seed["family"] in family_filter]
    return {
        "schema_version": "factor-formula-library/v1",
        "seed_count": len(seeds),
        "families": sorted({seed["family"] for seed in seeds}),
        "seeds": seeds,
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export a hot-pluggable factor formula seed library.")
    parser.add_argument("--output-json", required=True)
    parser.add_argument("--output-jsonl")
    parser.add_argument("--family", action="append", default=[])
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    payload = build_formula_library(families=args.family)
    _write_json(Path(args.output_json), payload)
    if args.output_jsonl:
        _write_jsonl(Path(args.output_jsonl), payload["seeds"])
    print(json.dumps({"ok": True, "output": args.output_json, "seed_count": payload["seed_count"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
