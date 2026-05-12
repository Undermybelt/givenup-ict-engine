# Board B Provider YF NQ Entry-Wire Addendum v1

Run id: `20260512T102332+0800-codex-board-b-provider-yf-nq-trendpulse-aq-v1`

Mode: `incubation_only`

## Scope

Addendum for the completed `04`, `05`, and `06` commands under the `102332` provider-owned Yahoo NQ TrendPulse run. This tests whether stronger entry-density or always-in diagnostics can turn offline entry labels into Freqtrade executed trades.

This addendum does not edit Current Cursor, does not approve selected history or source/control evidence, does not run selected-data promotion, does not advance Pre-Bayes/BBN/CatBoost/execution-tree promotion, does not promote a candidate, and does not call `update_goal`.

## Command Evidence

- `04_run_provider_yf_nq_trendpulse_with_sampled_pulse`: exited `0`.
- `05_run_provider_yf_nq_with_always_in_diagnostic`: exited `0`.
- `06_run_provider_yf_nq_always_in_instrumented`: exited `0`.

Raw command outputs:
- `command-output/04_run_provider_yf_nq_trendpulse_with_sampled_pulse.out`
- `command-output/05_run_provider_yf_nq_with_always_in_diagnostic.out`
- `command-output/06_run_provider_yf_nq_always_in_instrumented.out`

## Readback

The sampled and always-in diagnostics all reached Freqtrade measurement, but still executed zero trades.

- `ProviderNqAlwaysInDiagnostic` printed `enter_long_sum=16994` in the instrumented run, then Freqtrade reported `0` trades.
- `ProviderNqSampledPulse` exited `0` and reported `0` trades.
- `ProviderNqTrendPulse` exited `0` and reported `0` trades.
- The run did not add mature rooted branch observations or a profitability signal.

## Decision

Gate: `provider_yf_nq_entry_wire_addendum_v1=always_in_entries_present_but_freqtrade_zero_trades_no_promotion`.

This narrows the current blocker to the Freqtrade/Auto-Quant entry-wire or execution eligibility layer. Offline entry labels and even instrumented always-in labels are not trade evidence until Freqtrade executes trades.

Promotion allowed: `false`

`update_goal=false`

## Next

Do not promote from the `102332` TrendPulse/always-in diagnostics. The next non-duplicative slice should inspect or repair why Freqtrade reports zero entries/trades despite nonzero `enter_long` labels, or switch to a provider-owned market/strategy path that actually executes nonzero trades before downstream promotion.
