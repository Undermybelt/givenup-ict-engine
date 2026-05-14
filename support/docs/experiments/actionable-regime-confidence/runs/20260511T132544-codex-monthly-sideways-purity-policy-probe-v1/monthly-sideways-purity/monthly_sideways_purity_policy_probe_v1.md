# Monthly Sideways Purity Policy Probe v1

Run ID: `20260511T132544+0800-codex-monthly-sideways-purity-policy-probe-v1`

## Result

- The remaining `1mo:Sideways` blocker is narrow: under the prior split, pure `label_share == 1.0` months have perfect agreement but only `60` non-heldout post-2022 source-days, so Wilson95 LCB is `0.939828`.
- Wilson95 needs `73` all-agreeing days to reach `0.95`; the prior cross-product split is short by `13` all-agreeing non-heldout post-2022 Sideways source-days.
- A stricter pure-month policy with two-axis validation passes 95: calibration non-heldout `0.985921`, heldout-time all-tickers `0.973294`, heldout-ticker `0.993659`.
- This is not a threshold relaxation: source-consensus threshold moves from `0.95` to `1.00`.
- Full objective achieved: `false`; direct `Manipulation` and unsupported full-matrix cells remain separate.

## Policy Comparison

| Policy | Accepted 95 | Calibration LCB | Heldout-Time LCB | Heldout-Ticker LCB | Blockers |
|---|---:|---:|---:|---:|---|
| baseline_0_95_prior_cross_product_split | `false` | 0.959409 | 0.931307 | 0.966575 | heldout_time_nonheldout_2022_plus_source_consensus_wilson95_below_0_95 |
| pure_month_1_00_prior_cross_product_split | `false` | 0.985921 | 0.939828 | 0.993659 | heldout_time_nonheldout_2022_plus_source_consensus_wilson95_below_0_95 |
| pure_month_1_00_two_axis_validation_split | `true` | 0.985921 | 0.973294 | 0.993659 | none |

## Interpretation

- Stop treating `1mo:Sideways` as a generic negative-result loop. The local data already shows a clean pure-month signal; the open decision is validation policy versus adding a small amount of new pure monthly Sideways support.
- If the board keeps the prior non-heldout chronological cross-product split, the next acquisition target is only more post-2022 non-heldout pure monthly Sideways source-days, not another broad data sweep.
- If the board accepts two-axis validation for rare monthly cells, this run can be used as the policy-relock candidate for the last same-source monthly Sideways cell.
- Direct `Manipulation` remains a separate direct-event/order-lifecycle/social/on-chain track and is not affected by this Sideways result.

## Web Direction Refresh

- `hidden-regime`: keep `Sideways` as a distinct root state rather than a complement of Bull/Bear/Crisis.
- `hmmlearn`: use posterior/persistence features if rebuilding root-state confidence.
- `ruptures`: use change-point proximity to abstain months that straddle boundaries.
- FINRA potential-manipulation reporting: keep manipulation on direct surveillance/order-lifecycle evidence, not OHLCV proxies.

## Guardrails

- No runtime code changed.
- No raw data committed.
- No threshold relaxed.
- No trade usability claimed.
- No full-objective completion claimed.
