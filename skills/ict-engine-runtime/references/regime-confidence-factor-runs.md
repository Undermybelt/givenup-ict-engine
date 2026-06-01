# Regime confidence factor runs

Session learning from an ICT-Engine regime-discrimination run.

## Goal shape

When asked for "95% confidence regime discrimination factors" and "every regime covered", separate three meanings:

1. Runtime confidence bucket / gating confidence.
2. Coverage across emitted regimes.
3. Calibrated statistical precision/accuracy >= 0.95.

Do not imply (1) proves (3). Current validator reports confidence buckets, not calibrated per-regime precision.

## Fast high-confidence runtime check

Use `validate-market-state` with the `high_confidence` profile first:

```bash
./target/debug/ict-engine validate-market-state \
  --data /tmp/ict-engine-ibkr-probe/qqq.1d.10y.json \
  --window-size 100 --step-size 20 \
  --profile high_confidence
```

Observed on QQQ/NQ proxy 1d 10y (`/tmp/ict-engine-ibkr-probe/qqq.1d.10y.json`):

- samples: 122
- avg_confidence: 77.20%
- high_confidence >=0.75: 65.57%
- tradeable/covered >=0.55: 100.00%
- Low/VeryLow: 0.00%
- covered primary regimes: `TrendExpansion`, `RangeConsolidation`, `ExtremeStress`
- `ReversalBrewing` had no samples in that lane/profile, so it cannot be claimed covered.

Useful comparison across profiles on same data:

- `default`: avg 61.84%, high 10.66%, tradeable 76.23%
- `risk_control`: avg 59.42%, high 0.82%, tradeable 74.59%
- `high_confidence`: avg 77.20%, high 65.57%, tradeable 100.00%

## Independent OOS classifier check

Run `regime_factor_benchmark.py` as a sanity check, not as a replacement for runtime validation:

```bash
python3 scripts/auto_quant_external/regime_factor_benchmark.py \
  --symbol NQ --base-timeframe 1d \
  --truth-mode post_transition_direction --outcome-horizon 8 \
  --train-fraction 0.7 \
  --data /tmp/ict-engine-ibkr-probe/qqq.1d.10y.json \
  --paired-data QQQ_IV=/tmp/ict-engine-ibkr-probe/qqq.iv.1d.10y.json \
  --paired-data QQQ_HV=/tmp/ict-engine-ibkr-probe/qqq.hv.1d.10y.json \
  --paired-data VIX=/tmp/ict-engine-ibkr-probe/vix.1d.10y.json \
  --feature-set base,pda,indicator,cluster_proto,hazard,ms_regime,vol_regime \
  --extra-tree-count 21 --extra-tree-depth 9 --extra-tree-min-leaf 20 \
  --extra-tree-max-samples 30000 --skip-stumps --skip-gaussian \
  --output-json /tmp/ict-engine-ibkr-probe/regime95_post_direction.json \
  --output-md /tmp/ict-engine-ibkr-probe/regime95_post_direction.md
```

Observed best trained factor:

- `trained_family_extra_trees_v1`
- eval_family_f1: 0.5624
- eval_macro_f1: 0.5624
- eval_non_unknown_accuracy: 0.5305
- eval_coverage: 0.3223
- coverage: 0.2988
- covered_precision: 0.5925
- transition_f1: 0.1633

Interpretation: usable as high-confidence regime filter evidence, not as proof of calibrated 95% predictive precision.

## Pitfalls

### `--enhanced` is not a flag

`validate-market-state` uses enhanced aggregation by default. To disable it, pass `--no-enhanced`. Passing `--enhanced` fails with `unexpected argument '--enhanced'`.

### `bocpd_lite` feature set can fail

Observed command using `--feature-set ... bocpd_lite ...` failed with:

```text
NameError: name 'mean' is not defined
```

Workaround: omit `bocpd_lite` unless the script has been fixed.

### Python tool environment mismatch

`execute_code` may lack pandas even when terminal `python3` has pandas installed. For this repo's scripts, prefer terminal `python3` from repo cwd when running `scripts/auto_quant_external/*.py`.

### Coverage wording

Say "covered emitted regimes" unless every enum regime has nonzero samples. If a regime has zero truth/runtime samples, record `no sample`, not `covered`.

## Promotion standard

Before claiming true 95% regime identification:

1. Export per-window regime probabilities or labels.
2. Compare against independent labels (`post_transition_direction`, HMM/Viterbi, change-point, outcome-defined regimes).
3. Require per-regime precision >=0.95 and nontrivial recall/coverage.
4. Report regimes with zero samples separately.
