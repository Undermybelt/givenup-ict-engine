# HMM/Viterbi Regime Validation Tools

## Purpose
Independent regime label source using Gaussian HMM for validating the existing regime classifier (base+pda + EMA/VIX extension).

## Tools Created
1. **external_regime_hmm_viterbi.py** - GaussianHMM regime inference
   - Input: OHLCV feather/CSV
   - Output: per-bar state labels + family classification
   - Features: log_ret, return_20d, return_60d, volatility_20d, above_sma200_proxy, vol_ratio, trend_eff

2. **external_export_classifier_labels.py** - Export classifier daily labels
   - Captures regime_table from regime_attribution.py
   - Output: JSON with date → family mapping

3. **external_regime_family_comparison.py** - Compare HMM vs classifier
   - Aggregates 15m HMM to daily
   - Computes agreement rate and random baseline
   - Filters "unknown" days for fair comparison

## Key Findings (NQ 15m, 4 states)
- HMM flip rate: 0.0789 (stable state transitions)
- Unfiltered agreement: ~32% (random baseline ~32%)
- **After filtering unknown days: 51.5% agreement (random ~33%)**
- Excess over random: ~18%

## Key Findings (NQ 15m, 8 states) — 2026-05-07
- 4 states insufficient: transition F1 ~0.4, cannot distinguish trend strength
- Expanded to 8-state `RegimeV2` enum:
  - `TrendUpStrong`, `TrendUpWeak` — directional momentum with strength split
  - `RangeVolatile`, `RangeQuiet` — sideways with volatility distinction
  - `TrendDownWeak`, `TrendDownStrong` — bearish with strength split
  - `Transition` — regime change points
  - `CrashRecovery` — extreme events
- Family mapping updated:
```python
REGIME_FAMILY_MAP = {
    "trend_up": "trend",
    "trend_down": "trend",
    "range_volatile": "range",
    "range_quiet": "range",
    "transition": "transition",
    "crash": "transition",
    "recovery": "transition",
}
```
- Rust types added: `RegimeV2`, `RegimeProbsV2` in `src/types.rs`
- FactorContext extended with `regime_v2_labels: Option<&HashMap<i64, RegimeV2>>` for per-bar lookup

## Family Mapping (sharpe-based, 4-state)
```python
if sharpe_proxy > 0.1: family = "trend_up"
elif sharpe_proxy < -0.1: family = "trend_down"
else: family = "range"
```

## Usage
```bash
# Run HMM
python scripts/auto_quant_external/external_regime_hmm_viterbi.py \
  --candle-path /path/to/NQ_USD-15m.feather \
  --n-states 4 \
  --output-dir /tmp/hmm_regime_nq_15m

# Export classifier labels
python scripts/auto_quant_external/external_export_classifier_labels.py \
  --output /tmp/classifier_daily_labels.json

# Compare
python scripts/auto_quant_external/external_regime_family_comparison.py \
  --hmm /tmp/hmm_regime_nq_15m/hmm_regime_4states.json \
  --classifier /tmp/classifier_daily_labels.json
```

## Pitfalls
- ruptures changepoint detection OOM on 15m data → use daily or skip
- HMM features must include above_sma200_proxy to align with classifier logic
- Filter "unknown" days (early history without SMA200) before comparison
- Sharpe threshold 0.1/-0.1 works better than mean_ret/std_ret thresholds for family mapping
