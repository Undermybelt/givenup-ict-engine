# IBKR cross-asset large-sample factor sweep notes

Use for ict-engine factor-research runs where the user asks to push multiple vol / gamma / IV / OI / Greeks-style factors through the full closed-loop surfaces without fabricating unavailable data.

## Durable workflow

1. Use an isolated `/tmp/...` run root and copy any prior state before mutation.
2. Fetch the longest practical observed series first; record exact start/end.
3. Score only factors whose required historical inputs exist.
4. If only a current options-chain snapshot exists, record it as `current_snapshot_only`; do not backtest OI / gamma / Greeks / expiry-magnet logic from it.
5. Build candidate packs under a run-local `candidate_packs_*` root and emit `strategy_library.json` for Auto-Quant import.
6. Run `factor-asset-closure-intake` to push packs into structural-path admission surfaces.
7. Before replaying `auto-quant-prior-init` on a copied state, remove stale single-apply artifacts from both locations when present:
   - `<state>/<SYMBOL>/bbn_network.json`
   - `<state>/auto-quant/<SYMBOL>/bbn_network.json`
   - `<state>/<SYMBOL>/artifact_ledger.json`
   - `<state>/auto-quant/<SYMBOL>/artifact_ledger.json`
   - both `auto_quant_prior_init_history.json` files
   - both `auto_quant_prior_init_<SYMBOL>_*.json` globs
8. Re-run import, prior init, target export, policy-training-status, and workflow-status.
9. Keep final language fail-closed: candidate/ranker readiness is not live execution readiness.

## Intraday regime-refinement ladder

When the operator asks for more IBKR evidence for regime/sub-regime factors,
prefer an IBKR-first multi-timeframe ladder instead of a cheap yfinance-only
packet:

- start from `1m` and fetch the largest practical window (`7 D` is a proven
  stable ceiling in current local IBKR runs);
- add `5m` for about `30 D`;
- add `15m` for about `60 D`;
- add `30m` for about `3 M`;
- add `1h` for about `3 M` to `6 M` when IBKR accepts it.

Interpretation rule: if `1m/5m/15m` support a trend or sub-regime but `30m/1h`
neutralize into range/stress, keep the packet as useful negative or
neutralization evidence. Do not promote it until Pre-Bayes, BBN/workflow,
CatBoost/path-ranker, and execution tree agree with mature observations.

Session-proven example: `IBKR ITA` fetched `1m=2730`, `5m=2340`, `15m=1560`,
`30m=819`, `1h=862`; low timeframes showed
`TrendExpansion/BullTrendAcceleration`, while `30m/1h` neutralized into
`RangeConsolidation/WideRange`, Pre-Bayes stayed `range@0.5105 pass_neutralized`,
and path-ranker remained `0/30`.

## Session-proven pattern

A 2014-01-01 -> 2026-05-18 daily sweep was run for:

- `iv_rv_compression_break_1d_v1`
  - observed inputs: OHLCV + vol-index proxy (`^VIX`, `^VXN`, `^GVZ`, `^MOVE` when available)
  - aggregate: 272 trades, 52.573529% win rate, PF 1.2776, Sharpe 1.52364
  - strongest markets: GLD, TLT, GC=F
  - weak markets: SPY, ES=F, NQ=F
  - `IWM` was unknown because `^RVX` was unavailable

- `cross_asset_vol_lead_lag_1d_v1`
  - observed inputs: OHLCV leader/target z-score shock and lag
  - aggregate: 93 trades, 52.688172% win rate, PF 1.25304, Sharpe 1.198053
  - strongest pair: `GC=F -> GLD`
  - second: `QQQ -> SPY`

Factors kept `unknown` because the historical sources were missing:

- `dealer_pin_release`
- `oi_migration_momentum`
- `greeks_skew_stress`
- `expiry_magnet_to_impulse`

## Exact evidence artifacts from that run

- Summary: `/tmp/ict-engine-ibkr-crossasset-vol-gamma-iv-oi-greeks-20260517/summary/factor_run_summary.json`
- Strategy library: `/tmp/ict-engine-ibkr-crossasset-vol-gamma-iv-oi-greeks-20260517/strategy_library.json`
- Candidate packs: `/tmp/ict-engine-ibkr-crossasset-vol-gamma-iv-oi-greeks-20260517/candidate_packs_round2/`
- Clean state: `/tmp/ict-engine-ibkr-crossasset-vol-gamma-iv-oi-greeks-20260517/state_round3_clean_bbn`

These paths are evidence examples, not reusable defaults.
