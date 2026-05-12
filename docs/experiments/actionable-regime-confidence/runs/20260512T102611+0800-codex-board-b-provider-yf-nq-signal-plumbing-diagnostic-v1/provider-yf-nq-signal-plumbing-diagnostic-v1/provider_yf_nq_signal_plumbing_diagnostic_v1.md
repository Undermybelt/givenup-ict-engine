# Provider YF NQ Signal Plumbing Diagnostic v1

Run id: `20260512T102611+0800-codex-board-b-provider-yf-nq-signal-plumbing-diagnostic-v1`

Scope: supporting diagnostic for the Board B provider-owned Yahoo NQ=F / `NQ/USD` TOMAC lane. This run does not approve selected history, source/control evidence, downstream promotion, or `update_goal`.

## Inputs

- Source workspace: `docs/experiments/actionable-regime-confidence/runs/20260512T102332+0800-codex-board-b-provider-yf-nq-trendpulse-aq-v1/workspace/auto-quant-yf-nq-trendpulse`
- Provider data: copied `NQ_USD-1h.feather`, `NQ_USD-4h.feather`, and `NQ_USD-1d.feather`
- Branch path under test: `Crisis -> CrisisReliefCarry -> StopManagedPanicRecovery -> ProviderYfNqRealRowSignalDiagnostic`

## Readback

- V1 method-level probe exited `0`: `223` entry labels, `230` exit labels, `0` entry/exit overlap.
- V1 TOMAC market-order run exposed required config guards:
  - `entry_pricing.price_side="other"` required for market entries.
  - `exit_pricing.price_side="other"` required for market exits.
- After those run-local config repairs, V1 TOMAC exited `0` but still produced `0` trades.
- V2 switched cadence from filled dataframe row position to provider-real-row index.
- V2 method-level probe exited `0`: `222` entry labels, `222` exit labels, `0` entry/exit overlap, `10691` provider-present rows.
- V2 TOMAC exited `0` and still produced `0` trades: `0.0000%` total profit, `0.0000%` win rate, `0.0000` profit factor.

## Interpretation

This proves the NQ zero-trade symptom is not caused by absent strategy entry labels, missing exit labels, same-candle entry/exit overlap, or the market-order price-side config guard alone. The later Board B BTC precision packet identified the stronger shared root cause: copied TOMAC synthetic market precision used `amount=8` under ccxt `TICK_SIZE`, which can round intended stake amounts to `0.0`. This NQ diagnostic should therefore be treated as supporting evidence for applying the copied-harness tick-size repair to NQ before judging NQ signal quality.

## Gate

- `count_once:102611_provider_yf_nq_signal_plumbing_diagnostic`
- `pass:method_level_nq_entry_labels_nonzero`
- `pass:method_level_nq_exit_labels_nonzero`
- `pass:entry_exit_overlap_zero`
- `pass:market_order_price_side_guards_identified_and_repaired_run_local`
- `fail_closed:tomac_executed_trades_zero_after_signal_and_price_side_repairs`
- `fail_closed:copied_harness_tick_size_precision_not_repaired_in_this_run`
- `fail_closed:no_mature_rooted_branch_observations`
- `fail_closed:no_profitability_signal`
- `fail_closed:no_downstream_promotion_rerun`
- `promotion_allowed=false`
- `update_goal=false`

## Next

Do not rerun this signal-plumbing diagnostic shape. Continue with the active copied-harness tick-size repair lane for NQ (`103414` / `103450`) or a broader six-provider AQ/profitability run that produces mature profitable rooted observations before Pre-Bayes/filter -> BBN -> CatBoost/path-ranker -> execution tree.
