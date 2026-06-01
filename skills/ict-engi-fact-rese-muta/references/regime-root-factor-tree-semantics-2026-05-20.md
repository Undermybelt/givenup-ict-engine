# Regime-root factor tree semantics (2026-05-20)

> 2026-05-24 schema note: `pda_hybrid_alignment` is historical telemetry only unless the current ict-engine source or readback contract still declares it active. Do not use old `pda_hybrid_alignment=true` or `false` lines in this reference as a current hard gate; classify with the live actionable/status/readiness/transition/ranker/mature-row fields.

## Durable correction

Do not express ict-engine profitability factor trees as:

```text
M2K -> 1m -> RangeReversion -> VwapNoiseBandRejectShort -> factor_id
```

That is wrong because market/product/symbol/timeframe are training or validation labels, not factor-tree parents. The trained factor should generalize across symbols and slices.

Correct tree shape:

```text
main_regime -> sub_regime... -> profit_factor -> overlay_profit_factor...
```

Example corrected expression:

```text
RangeReversion -> VwapNoiseBandRejectShort -> ibkr_m2k1m_vwap_noise_band_reject_short_7d_gate1_v1
```

Attach context separately as metadata:

```text
market=FUTURES
product=equity_index
symbol=M2K
timeframe=1m
provider=IBKR
window=7D
```

## Workflow rule

When training or reporting profitability factors:

1. Build the branch path from regime classes and factor nodes only.
2. Store market/product/symbol/timeframe/provider/window as labels or conditioning metadata.
3. Use labels for generalization matrices across symbols/timeframes, not as tree parents.
4. Downstream filter / Pre-Bayes / BBN / CatBoost / execution tree must preserve the same regime-rooted factor path and carry labels alongside it.
5. Never promote a factor because it works only on a single symbol label; require cross-label evidence when the goal is generic factor utility.

## Reporting pattern

Use:

```text
factor_path: RangeReversion -> VwapNoiseBandRejectShort -> <factor_id>
labels: market=FUTURES product=equity_index symbol=M2K timeframe=1m provider=IBKR window=7D
```

Avoid:

```text
FUTURES -> equity_index -> M2K -> 1m -> RangeReversion -> ...
```

## Gate implication

A candidate can be a 1m-origin candidate, but `1m` is not the tree root. It is a source/validation label. Continue to start from 1m when feasible, cover 5m/15m/30m/1h/4h/1d, and keep hard gates strict:

- real-cost density survives
- AQ -> Pre-Bayes / BBN / CatBoost / execution tree direction agrees
- `transition_hazard < 0.60`
- `pda_hybrid_alignment=true`
- stable `execution_readiness >= 0.65`
