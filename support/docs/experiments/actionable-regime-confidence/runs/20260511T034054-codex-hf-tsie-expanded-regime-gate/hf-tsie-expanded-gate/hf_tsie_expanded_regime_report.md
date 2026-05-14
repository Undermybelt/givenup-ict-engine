# Hugging Face TSIE Expanded Regime Gate

Run id: `20260511T034054+0800-codex-hf-tsie-expanded-regime-gate`.

## Decision

- Gate result: `blocked_hf_tsie_expanded_regime_gate_below_95_or_validation_scope`
- Accepted roots in this source: none
- Missing active expanded roots after this source: BullExpansion, BearExpansion, SidewaysConsolidation, Manipulation
- Runtime code changed: `false`
- Thresholds relaxed: `false`

## Results

| Root | State | Rule | Cal support | Cal LCB | Test support | Test LCB | Test precision | Blockers |
|---|---:|---|---:|---:|---:|---:|---:|---|
| BullExpansion | blocked | `price_norm >= 1.20797261929 AND volatility >= 0.0374098724778` | 18238 | 0.227657 | 23373 | 0.276770 | 0.282505 | calibration_wilson95_below_0_95, test_wilson95_below_0_95, validation_market_contexts_below_2 |
| BearExpansion | blocked | `atr_norm >= 0.0867510117393 AND volatility >= 0.0694431642154` | 11586 | 0.273858 | 14327 | 0.330609 | 0.338312 | calibration_wilson95_below_0_95, test_wilson95_below_0_95, calibration_coverage_below_0_03, test_coverage_below_0_03, ece_above_0_05, validation_market_contexts_below_2 |
| SidewaysConsolidation | blocked | `volatility <= 0.0062368796138 AND bb_pos <= 0.17330594717` | 27061 | 0.854376 | 15496 | 0.765920 | 0.772586 | calibration_wilson95_below_0_95, test_wilson95_below_0_95, test_coverage_below_0_03, ece_above_0_05, validation_market_contexts_below_2 |

## Source Policy

- Source is external direct-labeled TSIE IDX market-regime data from Hugging Face.
- Mapping: `STRONG BUY` -> `BullExpansion`; `STRONG SELL` -> `BearExpansion`; `FLAT / NOISE` -> `SidewaysConsolidation`; weak/trap labels remain `UnknownOrMixed`.
- Blocked as predictors: `future_volatility`, `trend_return`, `target_return`, and `regime_label`.
- This loop uses all rows for timeframe suffixes `1D, 240`; it is completion-eligible for this source but still must pass the unchanged cross-context and 95 LCB gates.
- Raw 564MB parquet stays under `/private/tmp`; repo artifacts are compact summaries/samples only.
