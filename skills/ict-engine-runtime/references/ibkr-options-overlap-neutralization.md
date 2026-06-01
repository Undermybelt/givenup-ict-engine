# IBKR options overlap and HTF neutralization notes

Use with `references/ibkr-options-regime-rooted-aq-chain.md` when small-cycle option-factor mutations look profitable but may be duplicate signals.

## Session evidence

Run root:

```text
/tmp/ict-engine-ibkr-options-vol-gamma-iv-oi-greeks-qaq-v2
```

Artifacts:

```text
checks/signal_overlap_neutralization_v2.json
checks/iv_carry_dense_1m_htf_neutralized_report.json
experiments/iv_carry_dense_1m_htf_neutralized/
```

## Durable lesson

Before treating two positive 1m option-context factors as independent, compute entry-signal overlap on the same reconstructed feature frame.

Observed QQQ IBKR options case:

```text
iv_carry_dense_1m raw bars: 1230
vol_expansion_relaxed_1m raw bars: 1212
intersection: 1212
Jaccard: 98.54%
vol_expansion covered by iv_carry: 100.0%
```

Decision: keep `iv_carry_dense_1m` as parent; treat `vol_expansion_relaxed_1m` as child/ablation, not a separate factor.

## HTF hard-gate test

Tested gate:

```text
30m close > EMA55 and RSI 35..76
AND 1h close > EMA21 and RSI 35..76
```

Result vs baseline:

```text
baseline iv_carry_dense_1m: trades=40, profit=1.76%, Sharpe=53.4132, win=27.5%
HTF gated: trades=25, profit=0.88%, Sharpe=37.8329, win=28.0%, PF=2.4083
Delta: trades -15, profit -0.88%, Sharpe -15.5803
```

Decision: reject HTF hard gate for this short IBKR window. Keep HTF as diagnostic feature unless a longer rerun proves benefit.

## Reusable probe shape

1. Rebuild the same features used by strategy code from IBKR OHLCV/HV/IV/option premium CSVs.
2. Express each mutation's `enter_long` condition as a boolean Series.
3. Report:
   - raw signal bars and pct of bars
   - pairwise intersection
   - Jaccard
   - A-overlap and B-overlap
4. If one-way overlap is near-total, demote one branch to ablation.
5. Only after overlap audit, run hard neutralization as a real backtest, not just signal-count filtering.

## Pitfalls

- Do not infer independence from different factor names (`IV carry`, `vol expansion`) if entry predicates share the same call-ratio/trend/IV-rank core.
- Do not promote 30m/1h HTF gates from signal-count retention alone. A gate can retain many bars but still reduce executed trades and profit.
- In short windows, long HTF EMAs may warm up too late and produce zero trades. If testing HTF gate, try a relaxed diagnostic gate first and compare to baseline.
