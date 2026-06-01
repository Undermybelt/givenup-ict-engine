# Local NQ full-window cost-density screen (2026-05-21)

Use under `ict-engi-fact-rese-muta` when continuing NQ/Tomac-style regime-rooted factor training from local historical `1m` data.

## Run evidence

- Run root: `/tmp/ict-engine-local-nq-regime-rooted-mtf-gate1-20260521T1415`
- Source: `<private-tomac-data-cache>/nq future 2021-2025/NQ_1min_Continuous_Shifted_2836.csv`
- Filter: `contract_prefix=NQ`, `outright_only=true`, `positive_prices_only=true`
- Rows: `1,770,523`
- Window: `2021-01-03T23:00:00+00:00` to `2025-12-31T21:59:00+00:00`
- Ladder covered: `1m`, `5m`, `15m`, `30m`, `1h`, `4h`, `1d`
- Families screened: `84` regime-rooted rows across TrendExpansion, RangeReversion, RangeConsolidation, and Transition branches.

Command shape:

```bash
python3 support/docs/experiments/actionable-regime-confidence/scripts/run_local_nq_csv_regime_rooted_mtf_gate1_v1.py \
  --run-root /tmp/ict-engine-local-nq-regime-rooted-mtf-gate1-20260521T1415 \
  --screen-selected-aq \
  --skip-aq \
  --start 2021-01-01 \
  --end 2025-12-31 \
  --contract-prefix NQ \
  --outright-only \
  --positive-prices-only
```

## Terminal decision

Decision: `drop_gate1_density_below_target_no_aq`.

The screen found `2` rows that survived `5bps/side`, but both were far below the user's target of roughly `1-3` trades/day:

- `Transition -> LiquiditySweep -> StopRunVwapReclaim -> local_nq_csv_transition_stoprun_vwap_reclaim_v1`, `1d/dense`: `12` trades over `1556` days, `0.007712` trades/day, raw `+12.091842%`, `5bps/side=+10.891842%`.
- `RangeReversion -> VwapStretch -> VwapWashoutReclaim -> local_nq_csv_range_reversion_vwap_washout_reclaim_v1`, `30m/balanced`: `10` trades over `1556` days, `0.006427` trades/day, raw `+1.482286%`, `5bps/side=+0.482286%`.

Dense lower-timeframe rows did not survive realistic cost:

- Best `1m` dense positives were high-trade-count but deeply negative after `5bps/side`; for example `TrendExpansion/OpeningDriveRvolVwapContinuation/quality` had `10,827` trades, raw `+57.009750%`, but `5bps/side=-1025.690250%`.
- Best `5m` dense-ish rows also failed `5bps/side`; for example `RangeConsolidation/CompressionBreakoutContinuation/quality` had `1,188` trades, raw `-0.376895%`, `5bps/side=-119.176895%`.

No Auto-Quant material was dispatched because no row satisfied both real-cost survival and practical density.

## Gate interpretation

Keep all downstream gates false:

```text
downstream_allowed=false
pre_bayes_allowed=false
bbn_allowed=false
catboost_allowed=false
execution_tree_allowed=false
promotion_allowed=false
trade_usable=false
update_goal=false
```

Do not use sparse `30m/1d` cost-positive siblings to rescue the failed `1m` origin objective. Do not send sparse high-timeframe rows to Pre-Bayes/BBN/CatBoost/execution-tree just because they are positive after costs.

## Next executable bias

For NQ full-window local history, avoid repeating generic VWAP reclaim, opening-drive RVOL, and squeeze-breakout parameter sweeps unless the hypothesis directly increases per-trade excursion while preserving `1m/5m` density.

Next candidates should be materially different and execution-facing:

- OR15/OR30 continuation or rejection with a density-preserving filter, not the current sparse execution-filter variant.
- Volatility-expansion reversal or failed-breakout/fakeout with explicit minimum excursion.
- Cross-instrument relative-value dislocation using NQ/ES/YM legs if synchronized full-window local data is available.
- Analyze/materialization repair for the already strong Tomac `NQ/1m OR15` survivor before more same-root Gate 1 replays.

Preserve canonical factor paths as regime/factor-only, with market/product/symbol/timeframe stored as labels.
