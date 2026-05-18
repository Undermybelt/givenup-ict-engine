# 2026-05-18 ICT detector factor hotplug handoff TODO

## Scope

This handoff is for detector/classification factors only. It is not a
profitability-factor or trading-gate lane.

Primary correction:
- Gap/FVG family must include ICT delivery-gap `volume_imbalance`, not only
  rolling volume-spike anomaly.
- Liquidity family must expose explicit `smooth` / `jagged` / `mixed`
  texture classification, not only pool/sweep counts.

## Operating Contract

- Zero-config default: all core detectors must run from ordinary OHLCV candles
  and ATR where already available.
- Consumer-usable surface: no maintainer path, private dataset, broker account,
  API key, or personal symbol universe in default code paths.
- Token-friendly output: report compact enum/string fields plus numeric evidence
  (`touch_count`, `spacing_consistency`, `clean_sweep_likelihood`, confidence).
- No pollution/no debt: personal or richer data content must be an opt-in
  adapter/profile, not a dependency of core ICT detector code.
- Hotplug design: user-specific data should enter through an explicit selected
  provider/profile/bundle and only enrich detector evidence when present.

## Current State

Done in this slice:
- Added a separate `VolumeImbalanceGap` detector type for ICT delivery gaps
  between previous close and current open.
- Kept the existing rolling z-score `VolumeImbalance` detector as a volume-shock
  subtype instead of pretending it covers gap VI.
- Added typed liquidity texture output:
  `LiquidityPoolTextureKind::{None,Smooth,Jagged,Mixed}` and
  `LiquidityPoolTextureClassification`.
- Moved smooth/jagged classifier logic into `src/ict/liquidity.rs` so core ICT
  detector code, not `main.rs`, owns the factor.
- Kept analyze/reporting adapter compact: human output still emits
  `liquidity_pool_texture/smooth_or_jagged=<value>`.

Validation evidence:
- `cargo test --lib volume_imbalance` passed.
- `cargo test --lib liquidity_pool_texture` passed.
- `cargo test --bin ict-engine test_classify_liquidity_pool_texture_scores_smooth_pool`
  passed.

## Detector Completeness Matrix

Gap/FVG family:
- Present: FVG/BISI/SIBI geometry, filled/unfilled, iFVG, liquidity void.
- Added: ICT delivery-gap `volume_imbalance` geometry.
- Still useful next: partial-fill/mitigation percentage and failed mitigation
  state as typed detector outputs.

Liquidity family:
- Present: swing-cluster liquidity pools, buy-side/sell-side direction, sweeps,
  recent sweep count.
- Added: smooth/jagged/mixed texture classifier with spacing consistency and
  clean-sweep likelihood.
- Still useful next: clean/dirty sweep subtype, freshness/age score, touch
  dispersion in ATR units, and equal-high/equal-low subtype labels.

Order-block family:
- Present: bullish/bearish OB, tested/untested, breaker/mitigation/rejection
  variant adapter.
- Still useful next: move all OB variant classification out of `main.rs` into
  `src/ict/ob.rs` with typed variants and tests.

## Hotplug Personal Data Plan

Do not hard-code personal needs into default detectors.

Preferred shape:
- Core detector input: `&[Candle]`, ATR slices, optional compact structural
  context.
- Optional enrichment input: an explicit hotplug profile selected by user, for
  example provider/profile/bundle metadata that can add session labels, richer
  volume source, broker-grade timestamps, or private watchlist context.
- Default behavior when enrichment is absent: fail closed only for that
  enrichment field, not for the core detector.

Next implementation options:
- Add a small detector-context struct with optional fields:
  `session`, `source_profile`, `volume_quality`, `symbol_context`.
- Keep it opt-in and serializable; do not read maintainer-local files from ICT
  detector modules.

## Next

1. Add gap-VI to any compact detector inventory/report surface only if it can be
   done without expanding default output noisily.
2. Consider a small follow-up for clean/dirty sweep and OB typed variants.
