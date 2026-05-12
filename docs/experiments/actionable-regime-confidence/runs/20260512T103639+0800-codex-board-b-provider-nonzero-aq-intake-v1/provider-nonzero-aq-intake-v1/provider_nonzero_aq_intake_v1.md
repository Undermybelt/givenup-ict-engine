# Provider Nonzero AQ Intake v1

Run id: `20260512T103639+0800-codex-board-b-provider-nonzero-aq-intake-v1`

Mode: `append_only_unregistered_provider_nonzero_intake_non_promoting`

This packet consumes completed provider-owned Auto-Quant/TOMAC sidecars after the earlier zero-trade NQ/Yahoo lane. It counts only the unregistered `102812` NQ tick-precision result and the `103010` / `103114` BTC price-side canary repairs. The already-registered `102500` Yahoo crypto closeout and `102352/102928` BTC tick-size repair are context only and are not counted again. This packet does not edit the Board B cursor, does not approve selected history, does not approve source/control evidence, does not run Pre-Bayes/BBN/CatBoost/path-ranking/execution-tree promotion, does not promote a candidate, and does not call `update_goal`.

Current Board B hash observed before this writeback: `087ac45b3565118590eceb0079d27d0243357cb77aa5be5e69df219257ddf2fd`.

## Readback

### Context Only: Yahoo Crypto Momentum `102500`

- Provider requested: Yahoo/yfinance `BTC-USD`, `ETH-USD`, and `SOL-USD` 1h.
- Provider acquisition exited `0` for all three files: BTC `17007` rows, ETH `17004` rows, SOL `17006` rows.
- Signal-density precheck found nonzero entries before TOMAC.
- `ProviderCryptoMomentumStateV1`: `295` trades, `-18.73%` profit, `34.9153%` win rate, profit factor `0.7350`.
- `ProviderCryptoPullbackRevertV1`: `109` trades, `-7.08%` profit, `40.3670%` win rate, profit factor `0.6898`.
- Counting: already registered in the Board B `102500` closeout; not counted again here.

### Count Once: Yahoo NQ Tick Precision `102812`

- Provider requested: Yahoo/yfinance NQ long-history provider-provenanced workspace replay.
- The tick-precision capture exited `0` and changed the earlier NQ zero-trade surface.
- `ProviderNqSampledPulse`: `18` trades, `0.97%` profit, `33.3333%` win rate, profit factor `5.3246`.
- `ProviderNqTrendPulse`: `896` trades, `-38.10%` profit, `37.7232%` win rate, profit factor `0.5912`.
- Gate: one low-support positive sample and one mature negative strategy; fail-closed.

### Context Only: BTC Tick-Fix Factors `102928` / `103240`

- Provider requested: Binance `BTCUSDT` 1h provider-acquired source CSV.
- `102928` exited `0`; `103240` repeated the same precision-fixed measurement after an initial shell wrapper `127`.
- `ProviderBtcMomentumCross`: `9` trades, `2.14%` profit, `55.5556%` win rate, profit factor `1.7770`.
- `ProviderBtcMomentumPulse`: `57` trades, `-3.61%` profit, `38.5965%` win rate, profit factor `0.8418`.
- `ProviderBtcTrendPullback`: `16` trades, `-5.21%` profit, `31.2500%` win rate, profit factor `0.2877`.
- Counting: `102928` is already registered in the Board B `102352/102928` closeout; `103240` repeats the same precision-fixed measurement after a wrapper `127`; neither is counted again here.

### Count Once: BTC Canary Price-Side Repair `103010` / `103114`

- Provider requested: Binance `BTCUSDT` 1h provider-acquired source CSV.
- The first runs failed on Freqtrade market-order `price_side` configuration, then `price_sides_other` retries exited `0`.
- `ProviderBtcAlwaysEntryCanary`: `81` trades, `4.41%` profit, `53.0864%` win rate, profit factor `1.1993`.
- `ProviderBtcSignalCanary`: `80` trades, `3.19%` profit, `55.0000%` win rate, profit factor `1.1263`.
- Gate: positive provider-owned plumbing observations, but both are diagnostic canaries and not a Board-B-rooted non-canary recipe.

## Decision

Gate:

- `provider_nonzero_aq_intake_v1=unregistered_nonzero_provider_observations_found_non_promoting`
- `count_once:102812_provider_yf_nq_trendpulse_tick_precision`
- `count_once:103010_103114_provider_btc_price_side_canary_repair`
- `context_only_not_counted_again:102500_provider_yahoo_crypto_momentum_aq`
- `context_only_not_counted_again:102928_provider_btc_tickfix_factor`
- `pass:provider_owned_executed_trade_observations_present`
- `pass:btc_price_side_other_repair_produces_real_trades`
- `fail_closed:provider_crypto_momentum_negative_profit`
- `fail_closed:nq_tick_precision_mixed_low_support_or_negative_profit`
- `fail_closed:btc_tickfix_factor_mixed_low_support_or_negative_profit`
- `fail_closed:positive_btc_canaries_are_plumbing_diagnostics_not_branch_rooted_recipes`
- `fail_closed:no_pre_bayes_bbn_catboost_execution_tree_promotion_rerun`
- `promotion_allowed=false`
- `update_goal=false`

Next:

- Do not promote from the positive BTC canaries. Convert the price-side repair into a non-canary, Board-B-rooted recipe with adequate support, or find another provider-owned positive recipe with explicit `main_regime -> sub_regime -> sub_sub_regime_or_profit_factor -> profit_factor` before running Pre-Bayes/filter -> BBN -> CatBoost/path-ranker -> execution tree.
