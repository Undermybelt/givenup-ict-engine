# Regime Classifier Research + 95-99% Confidence TODO

> Goal: absorb market-regime papers/repos into ICT Engine and train one high-confidence factor/expert per regime label. The target is not full-coverage 99% prediction; target is 95-99% confidence on accepted samples, with abstain/unknown when evidence is weak.

## Routing / Scope

- Repo: `/Users/thrill3r/projects-ict-engine/ict-engine`
- Runtime route: `ict-engine-runtime`
- Research route: `research/arxiv`
- Output: plan only. No Rust/runtime edits in this document.
- Design rule: sidecar first; only promote to Rust runtime after proof by calibrated OOS evidence.

## Executive Conclusion

Current repo already has a useful regime ontology, but confidence is still mostly heuristic. To reach 95-99% confidence, do not build one monolithic classifier. Build a regime expert bank:

1. One-vs-rest binary expert per primary regime.
2. One-vs-rest binary expert per secondary regime.
3. Dimension experts for volatility / liquidity / structure / behavior.
4. HMM or BOCPD transition layer for temporal persistence.
5. Wasserstein / distributional distance layer for shape validation.
6. Conformal prediction layer for coverage guarantees.
7. Entropy / margin / contradiction gates for abstain.
8. Only emit `confidence_95=true` when calibration proves it.

High confidence must mean: historically calibrated probability + low entropy + stable transition + distributional agreement + enough sample support.

## Research / Repo Findings

### 1. HMM -> sequence classifier pattern

Source:
- Paper: `A Hybrid Learning Approach to Detecting Regime Switches in Financial Markets`, arXiv `2108.05801`
- Repo pattern: `akash-kumar5/CryptoMarket_Regime_Classifier`
  - HMM discovers latent regimes.
  - LSTM learns temporal transitions from HMM labels.
  - Feature families: momentum, trend, volatility.
  - Example label set: Strong Trend, Weak Trend, Range, Choppy High-Volatility, Volatility Spike, Squeeze.
  - HMM state count selected by BIC.

Lesson for ICT Engine:
- Use unsupervised discovery to define local market geometry, but do not trust raw HMM labels directly.
- Train supervised experts on HMM/cluster labels only after mapping them to our fixed ontology.
- Track transition matrix and regime duration statistics as evidence nodes.

TODO:
- [ ] Add sidecar `regime_hmm_discovery_report.py`.
- [ ] Inputs: OHLCV + auxiliary evidence rows.
- [ ] Outputs: `hmm_state_id`, `posterior`, `transition_matrix`, `state_duration_stats`, `bic_by_k`, `mapped_regime_candidates`.
- [ ] Evaluate `k=3..12`; choose by BIC/AIC + OOS stability, not in-sample fit only.
- [ ] Add mapping layer from discovered HMM states to ICT ontology labels.

### 2. HMM + Wasserstein hybrid pattern

Source:
- Repo: `kratu/wess_hmm`
  - Hybrid Wasserstein + HMM market regime detection.
  - HMM captures temporal memory: when regime persists or switches.
  - Wasserstein clustering captures distributional shape: what current window looks like.
  - Uses confidence `max(p)` and entropy `-sum p log p`.
  - Uses persistence governor to reduce spurious flips.
  - Labels: Trending, Range, Choppy, Transitional.

Lesson for ICT Engine:
- HMM posterior alone is not enough. Add distributional agreement.
- High confidence should require HMM posterior and Wasserstein nearest-centroid agreement.
- Transitional state should be explicit when entropy high or HMM/Wasserstein disagree.

TODO:
- [ ] Add sidecar `regime_distributional_agreement_report.py`.
- [ ] Compute rolling feature windows for each regime candidate.
- [ ] Compute Wasserstein / energy distance to stored archetype centroids.
- [ ] Output `distributional_distance`, `nearest_archetype`, `hmm_agreement`, `entropy`, `transitional_flag`.
- [ ] Use as BBN evidence before any regime label gets 95% confidence.

### 3. HMM + Gradient Boosting + Conformal prediction pattern

Source:
- Repo: `Qyuzet/simulating-finance-market-regimes`
  - HMM for regime discovery.
  - Gradient Boosting for classification.
  - Conformal prediction for uncertainty quantification.
  - Reported coverage focus, not blind point prediction.
  - Regime set: bear, bull, neutral.

Lesson for ICT Engine:
- 95-99% confidence is a calibration problem, not just a better classifier.
- Use conformal prediction to decide: accept single label / emit set / abstain.
- Class-conditional conformal is needed because rare regimes like crisis/thin-liquidity suffer under global calibration.

TODO:
- [ ] Add sidecar `regime_conformal_calibration_report.py`.
- [ ] Use split conformal, class-conditional conformal, and adaptive conformal variants.
- [ ] Output per-label `coverage`, `avg_set_size`, `singleton_rate`, `abstain_rate`, `calibration_window`.
- [ ] Gate `confidence_95=true` only when class-conditional coverage >= target.
- [ ] For 99% mode, allow lower coverage / higher abstain.

### 4. Explainable clustering / macro + sentiment pattern

Source:
- Paper: `Explainable Machine Learning for Regime-Based Asset Allocation` (Zhang, Yi, Chen, 2020)
  - Hierarchical clustering over macro + market data.
  - Uses rolling windows.
  - Regimes interpreted by macro indicators and investor mood.
  - Asset-return stats differ by regime.

Lesson for ICT Engine:
- A regime label must have a stable economic interpretation.
- Cluster assignments should include feature-attribution and return distribution summary.
- For trading, regime labels are valuable only if payoff distributions differ after costs.

TODO:
- [ ] Add `regime_cluster_interpretability_report.py`.
- [ ] Features: volatility, liquidity, structure, behavior, VIX/VIX3M/VVIX, HV rank, yield/macro if available.
- [ ] Output per-regime feature medians, SHAP/permutation ranking where possible, payoff distribution, risk-adjusted utility.
- [ ] Reject labels whose post-cost payoff distribution is not distinct.

### 5. Binary trend-vs-oscillation threshold pattern

Source:
- Paper: `Leveraging Machine Learning for Financial Forecasting: Distinguishing Market Trends from Oscillations in ETFs` (2026)
  - Binary problem: trending vs oscillating days.
  - Features: VIX, RSI, ATR, macro announcement indicators.
  - Rolling-window CV.
  - Thresholded intraday movement defines labels.

Lesson for ICT Engine:
- Some labels should start as binary one-vs-rest detectors before multiclass aggregation.
- Trend/Range separation should be trained directly as a high-value binary task.

TODO:
- [ ] Add direct binary experts:
  - `is_trend_expansion`
  - `is_range_consolidation`
  - `is_reversal_brewing`
  - `is_extreme_stress`
- [ ] Add threshold-defined labels for trend/oscillation based on realized range / ATR / directional efficiency.
- [ ] Train per-symbol and cross-symbol variants.

## Current ICT Engine Ontology

### Primary regimes: 5 labels

Source: `src/market_state/mod.rs`

1. `TrendExpansion`
2. `RangeConsolidation`
3. `ExtremeStress`
4. `ReversalBrewing`
5. `Unknown`

Trainable expert count: 4 active + 1 abstain/unknown detector.

### Secondary regimes: 16 labels

Source: `src/market_state/mod.rs`

Trend expansion family:
1. `BullTrendAcceleration`
2. `BearTrendAcceleration`
3. `BullTrendExhaustion`
4. `BearTrendExhaustion`

Range family:
5. `TightRange`
6. `WideRange`
7. `Accumulation`
8. `Distribution`

Extreme family:
9. `VolatilitySpike`
10. `LiquidityCrunch`
11. `PanicSelling`
12. `PanicBuying`

Reversal family:
13. `TrendFatigue`
14. `SentimentExtreme`
15. `StructureBreakdown`

Fallback:
16. `Unknown`

Trainable expert count: 15 active + 1 abstain/unknown detector.

### Dimension regimes: 24 labels total

Volatility: 5
1. `LowVol`
2. `NormalVol`
3. `ElevatedVol`
4. `CrisisVol`
5. `Unknown`

Liquidity: 4
1. `HighLiquidity`
2. `NormalLiquidity`
3. `ThinLiquidity`
4. `Unknown`

Structure: 8
1. `Trending`
2. `MeanReverting`
3. `Ranging`
4. `Accumulation`
5. `Distribution`
6. `Breakout`
7. `Breakdown`
8. `Unknown`

Behavior: 7
1. `Crowding`
2. `Exhaustion`
3. `FOMO`
4. `Capitulation`
5. `RiskOn`
6. `RiskOff`
7. `Neutral`

Trainable expert count: 20 active dimension experts + 4 unknown/neutral detectors.

### Total expert bank target

- Primary experts: 5
- Secondary experts: 16
- Dimension experts: 24
- Transition experts: at least 8
  - stay trend
  - trend -> range
  - trend -> reversal
  - range -> trend
  - range -> stress
  - reversal -> trend
  - stress -> normalize
  - any -> unknown/transitional

Total initial expert count: 53.

## Proposed Classification Architecture

```text
market rows / auxiliary evidence
  -> feature builder
  -> dimension experts
      volatility expert bank
      liquidity expert bank
      structure expert bank
      behavior expert bank
  -> primary one-vs-rest experts
  -> secondary one-vs-rest experts
  -> HMM temporal posterior
  -> Wasserstein / energy-distance agreement
  -> transition persistence governor
  -> conformal calibration
  -> BBN evidence value gate
  -> regime decision:
       single high-confidence label
       conformal label set
       unknown / transitional / abstain
```

## Feature Families to Encode

### A. Price path geometry

- log returns: 1, 3, 5, 10, 20 bars
- realized volatility
- ATR percentile
- range percentile
- directional efficiency ratio
- slope / rolling regression beta
- R2 of linear fit
- drawdown from local high / bounce from local low
- gap / jump score

Target labels:
- TrendExpansion
- Bull/Bear acceleration
- Tight/Wide range
- TrendFatigue

### B. Distribution shape

- skewness
- kurtosis
- entropy of returns
- realized range distribution
- tail ratio
- Wasserstein distance to archetype windows
- energy distance between current and historical regimes

Target labels:
- Choppy / Range / VolatilitySpike / ExtremeStress

### C. Volatility state

- ATR percentile 20/60/90/95
- realized vol vs historical vol
- vol-of-vol
- Bollinger width percentile
- volatility clustering score
- VIX/VIX3M/VVIX when available
- QQQ HV rank 252

Target labels:
- LowVol, NormalVol, ElevatedVol, CrisisVol
- VolatilitySpike
- ReversalBrewing if vol compression -> expansion

### D. Liquidity state

- volume percentile
- range / volume ratio
- spread proxy
- signed volume imbalance if available
- session / killzone flag
- slippage estimate
- Kyle lambda proxy
- liquidity void / gap score

Target labels:
- HighLiquidity, NormalLiquidity, ThinLiquidity
- LiquidityCrunch

### E. Structure / ICT

- ADX / DI spread
- FVG reclaim score
- liquidity sweep score
- BOS / CHOCH count
- higher-timeframe PDA alignment
- MTF resonance alignment / contradiction
- premium/discount zone
- range bound support/resistance touches

Target labels:
- Trending, MeanReverting, Ranging
- Accumulation, Distribution
- Breakout, Breakdown
- Bull/Bear acceleration

### F. Behavior / crowding

- RSI extreme + volume spike
- one-way return streak
- exhaustion divergence
- volume climax
- funding/open-interest if available
- VVIX/VIX panic ratio
- put/call or options hedging evidence if available

Target labels:
- Crowding, Exhaustion, FOMO, Capitulation, RiskOn, RiskOff
- PanicSelling, PanicBuying, SentimentExtreme

## Confidence Logic

### Point probability is not enough

A prediction can be accepted only if all gates pass:

```text
model_p(label) >= p_threshold
entropy <= entropy_threshold
margin(top1 - top2) >= margin_threshold
conformal_set_size == 1
class_conditional_coverage >= target_coverage
hmm_transition_consistent == true
wasserstein_agreement == true
sample_support >= min_samples
recent_drift_flag == false
```

### Target modes

95 mode:
- class-conditional coverage >= 0.95
- conformal singleton rate target >= 0.30
- abstain allowed
- min OOS samples per label >= 100 where possible

99 mode:
- class-conditional coverage >= 0.99
- singleton rate can be low
- abstain expected and acceptable
- use only for position sizing / no-trade gate unless coverage remains usable

### Unknown / Transitional is not failure

Unknown is the correct output when:
- entropy high
- conformal set size > 1
- HMM and Wasserstein disagree
- transition probability spikes
- regime duration violates learned persistence
- drift detector fires

## TODO Implementation Plan

### Slice R1: Research artifact capture

Create:
- `docs/plans/2026-05-09-regime-classifier-research-and-99-confidence-todo.md` (this doc)

Next create:
- `docs/research/regime-classification-source-notes.md`

Tasks:
- [ ] Add source table with paper/repo/title/method/label-set/features/usable-module.
- [ ] Snapshot README snippets from key repos.
- [ ] Record which ideas are directly implementable sidecar vs later Rust runtime.

### Slice R2: Regime ontology manifest

Create:
- `scripts/research/regime_ontology_manifest.py`
- `scripts/research/tests/test_regime_ontology_manifest.py`

Outputs:
- `regime_ontology_manifest.json`
- `regime_expert_bank_manifest.jsonl`

Fields:
- `label_id`
- `level`: primary / secondary / dimension / transition
- `parent_label`
- `positive_definition`
- `negative_definition`
- `required_features`
- `allowed_data_sources`
- `min_support`
- `target_coverage`
- `abstain_policy`

Acceptance:
- [ ] Emits 53 initial experts.
- [ ] Includes all current Rust enum labels.
- [ ] Marks `Unknown` / `Neutral` as abstain/fallback classes.

### Slice R3: Feature builder for regime experts

Create:
- `scripts/research/regime_feature_builder.py`
- tests

Inputs:
- OHLCV JSONL/CSV
- optional auxiliary evidence JSONL
- optional MTF PDA events JSONL

Outputs:
- `regime_features.parquet` if pandas/pyarrow present; else CSV/JSONL fallback
- `feature_quality_report.json`

Feature groups:
- price geometry
- volatility
- liquidity
- structure/ICT
- behavior/crowding
- distribution shape
- MTF resonance
- transition history

Acceptance:
- [ ] Zero config works with OHLCV only.
- [ ] Extra user fields pass through: `qqq_hv_level`, `nq_vs_200d_pct`, `vix3m_level`, `qqq_hv_pct_rank_252`, `vvix_over_vix`.
- [ ] Missing optional fields do not fail.

### Slice R4: Unsupervised regime discovery

Create:
- `scripts/research/regime_discovery_hmm.py`
- `scripts/research/regime_discovery_cluster.py`
- tests

Methods:
- Gaussian HMM over standardized features.
- KMeans / hierarchical clustering.
- Optional Wasserstein / energy distance clustering.

Outputs:
- `hmm_regime_discovery_report.json`
- `cluster_regime_discovery_report.json`

Acceptance:
- [ ] Evaluates `k=3..12`.
- [ ] Stores BIC/AIC/silhouette/transition persistence.
- [ ] Maps discovered states to candidate ICT labels by feature profile.
- [ ] Does not overwrite fixed ontology.

### Slice R5: One-vs-rest expert training

Create:
- `scripts/research/regime_expert_trainer.py`
- tests

Model stack:
- baseline logistic / calibrated linear model
- RandomForest / GradientBoosting fallback via sklearn if available
- pure Python threshold fallback for offline mode

Outputs:
- `regime_expert_scores.jsonl`
- `regime_expert_artifacts/`
- `regime_expert_training_report.json`

Acceptance:
- [ ] Trains one binary expert per ontology label.
- [ ] Supports per-label threshold search for precision-first mode.
- [ ] Reports precision/recall/F1/AUC/Brier/ECE per label.
- [ ] Uses purged CV and embargo.

### Slice R6: Conformal calibration layer

Create:
- `scripts/research/regime_conformal_calibration_report.py`
- tests

Modes:
- split conformal
- class-conditional conformal
- adaptive conformal rolling window

Outputs:
- `regime_conformal_report.json`

Acceptance:
- [ ] Reports coverage per label.
- [ ] Reports singleton rate and average set size.
- [ ] Supports target coverage `0.95` and `0.99`.
- [ ] Emits `confidence_95` / `confidence_99` only when coverage criteria pass.

### Slice R7: Distributional agreement layer

Create:
- `scripts/research/regime_distributional_agreement_report.py`
- tests

Methods:
- Wasserstein distance if scipy available.
- Energy distance / simple quantile distance fallback.

Outputs:
- `regime_distributional_agreement_report.json`

Acceptance:
- [ ] Compares current feature window to each label archetype.
- [ ] Emits agreement/disagreement with classifier top label.
- [ ] Emits `transitional_flag` for high-distance or mixed archetype cases.

### Slice R8: Transition persistence governor

Create:
- `scripts/research/regime_transition_governor.py`
- tests

Inputs:
- expert probabilities
- HMM transition matrix
- recent predicted label history
- drift/change-point rows

Outputs:
- `regime_transition_governor_report.json`

Acceptance:
- [ ] Enforces minimum duration / hysteresis.
- [ ] Penalizes flip-flop labels.
- [ ] Preserves true shock transitions when drift evidence is strong.
- [ ] Emits transition hazard into BBN evidence.

### Slice R9: High-confidence regime decision aggregator

Create:
- `scripts/research/regime_high_confidence_decision.py`
- tests

Inputs:
- expert scores
- conformal report
- distributional agreement
- transition governor
- BBN evidence value report

Outputs:
- `regime_high_confidence_decision.json`

Decision states:
- `single_label_95`
- `single_label_99`
- `label_set`
- `transitional`
- `unknown_abstain`

Acceptance:
- [ ] Single label only when all confidence gates pass.
- [ ] Otherwise returns label set or abstain.
- [ ] Emits machine-readable reasons for every rejection.

### Slice R10: BBN / execution-tree integration plan

Create/modify later, only after sidecar evidence passes:
- BBN evidence mapping for high-confidence regime states.
- Execution tree trace field for `regime_confidence_gate`.
- Path-ranker feature export includes `regime_high_confidence_label`, `conformal_set_size`, `transition_hazard`, `distributional_agreement`.

Acceptance:
- [ ] `analyze --human` can explain why regime was accepted/rejected.
- [ ] Execution tree can block low-confidence regime usage.
- [ ] BBN posterior update includes regime evidence value metrics.

## Label-by-Label Expert Plan

### Primary experts

| Label | Expert signal core | High-confidence gate |
|---|---|---|
| TrendExpansion | ADX, directional efficiency, slope R2, MTF alignment, volume confirmation | high margin vs Range/Reversal; persistent HMM state; low entropy |
| RangeConsolidation | low directional efficiency, bounded range, repeated touches, low vol expansion | Wasserstein range archetype agreement; no breakout drift |
| ExtremeStress | crisis ATR/HV rank, thin liquidity, panic behavior, VVIX/VIX, gap risk | fast drift allowed; conformal class-specific coverage |
| ReversalBrewing | exhaustion, divergence, failed breakout, sentiment extreme, structure weakness | transition hazard high but not stress; distributional agreement with reversal archetype |
| Unknown | high entropy, conformal set >1, low support, disagreement | abstain, not trade signal |

### Secondary experts

| Label | Factor family |
|---|---|
| BullTrendAcceleration | positive slope + ADX + volume + MTF bullish alignment |
| BearTrendAcceleration | negative slope + ADX + volume + MTF bearish alignment |
| BullTrendExhaustion | bullish trend + RSI extreme + momentum fade + volume climax |
| BearTrendExhaustion | bearish trend + oversold + momentum fade + capitulation/relief |
| TightRange | low ATR percentile + narrow Bollinger width + low entropy |
| WideRange | high realized range but low directional efficiency |
| Accumulation | range + rising volume on up moves + discount reclaim |
| Distribution | range + rising volume on down moves + premium rejection |
| VolatilitySpike | ATR/HV jump + vol-of-vol + range expansion |
| LiquidityCrunch | low volume percentile + wide range/spread proxy + slippage risk |
| PanicSelling | downside range expansion + volume spike + risk-off behavior |
| PanicBuying | upside range expansion + volume spike + FOMO behavior |
| TrendFatigue | slope deceleration + divergence + lower R2 |
| SentimentExtreme | RSI/VVIX/VIX/funding/crowding extremes |
| StructureBreakdown | BOS/CHOCH break + failed reclaim + MTF contradiction |
| Unknown | all ambiguity gates |

## Validation Standard

For every regime expert:

- [ ] Purged CV + embargo.
- [ ] OOS walk-forward by symbol/timeframe.
- [ ] Per-label calibration curve.
- [ ] Brier score and ECE.
- [ ] Class-conditional conformal coverage.
- [ ] Minimum support check.
- [ ] Payoff distribution distinctness check.
- [ ] BBN evidence value check: entropy/log-loss/contradiction lift.
- [ ] Execution-tree usefulness check: does accepted label improve high payoff/risk opportunity selection?

## Practical Acceptance Criteria

A regime factor is promoted only if:

```text
class_conditional_coverage >= 0.95
and singleton_precision >= 0.90
and brier_score improves over baseline
and ECE <= 0.05
and PBO <= 0.2
and BBN logloss_delta < 0
and payoff utility improves vs no-regime baseline
```

For 99 mode:

```text
class_conditional_coverage >= 0.99
and ECE <= 0.02
and singleton_precision >= 0.95
and abstain_rate accepted by strategy profile
```

## Immediate Next Slice

Start with `Slice R2: Regime ontology manifest`.

Reason:
- It converts current Rust enum labels into machine-readable expert specs.
- It prevents drift between docs, sidecars, and runtime enums.
- It creates the checklist for “one unbeatable confidence factor per regime.”

First files:
- `scripts/research/regime_ontology_manifest.py`
- `scripts/research/tests/test_regime_ontology_manifest.py`

First red tests:
- [ ] manifest emits 5 primary labels.
- [ ] manifest emits 16 secondary labels.
- [ ] manifest emits 24 dimension labels.
- [ ] manifest emits at least 8 transition experts.
- [ ] total expert count is 53.
- [ ] each active expert has `target_coverage` in `{0.95, 0.99}` and an `abstain_policy`.
