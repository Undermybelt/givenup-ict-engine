# Latest Provider Trade Readback v1

Run id: `20260512T103623+0800-codex-board-b-latest-provider-trade-readback-v1`

Gate result: `latest_provider_trade_readback_v1=provider_trade_plumbing_progress_incubation_only_no_promotion`

## Readback

- `102500` Yahoo crypto provider run fetched BTC/ETH/SOL 1h data for `2024-06-01 -> 2026-05-11` and reached TOMAC measurement. Signal density was nonzero (`1085` momentum candidates, `931` pullback candidates), but both measured strategies were unprofitable: `ProviderCryptoMomentumStateV1` `295` trades / `-18.73%` / Sharpe `-1.0287` / profit factor `0.7350`; `ProviderCryptoPullbackRevertV1` `109` trades / `-7.08%` / Sharpe `-0.4663` / profit factor `0.6898`.
- `102812` provider Yahoo NQ tick-precision repair converted the prior zero-trade `102332` entry-wire gap into executed trades. `ProviderNqSampledPulse` produced `18` trades / `0.97%` / Sharpe `0.1898` / profit factor `5.3246`; `ProviderNqTrendPulse` produced `896` trades / `-38.10%` / Sharpe `-3.3038` / profit factor `0.5912`.
- `102812` also materialized `18` JSONL real-trade rows for `Bull -> ProviderYfNq -> SampledPulseDiagnostic -> ProviderNqSampledPulse:provider_yf_nq_sampled_pulse_h48`, but its own packet marks the branch path as `diagnostic_not_board_a_contract`.
- `102928` provider BTC tickfix factor run reached nonzero provider-owned factor trades after the tick-size repair: `ProviderBtcMomentumCross` `9` trades / `2.14%` / Sharpe `1.2260` / profit factor `1.7770`; `ProviderBtcMomentumPulse` `57` trades / `-3.61%`; `ProviderBtcTrendPullback` `16` trades / `-5.21%`.
- `103010` and `103114` are signal-plumbing canaries, not factor promotion candidates. After both entry and exit `price_side=other` were applied, `ProviderBtcAlwaysEntryCanary` produced `81` trades / `4.41%` / Sharpe `2.5645` / profit factor `1.1993`, and `ProviderBtcSignalCanary` produced `80` trades / `3.19%` / Sharpe `1.7001` / profit factor `1.1263`.
- `103057` structural-feedback readback exited `0` for all four commands and now preserves the exact branch path `Crisis -> CrisisReliefCarry -> StopManagedPanicRecovery -> SourceRootStopCarryLongHorizonV1:crisis_carry_h8_sl048_tp12`, but workflow remains blocked on `user_selected_historical_data_missing` and execution remains observe-only.

## Decision

- The entry-to-trade blocker is narrowed: Freqtrade can execute provider-owned NQ/BTC trades when the run-local market precision and `price_side=other` constraints are satisfied.
- These runs are still `incubation_only`. They do not supply a mature profitable rooted branch: the profitable NQ pulse has only `18` trades, the profitable BTC factor has only `9` trades, the high-trade NQ/crypto factor surfaces are negative, and the BTC canaries are diagnostic plumbing probes.
- No selected-history approval, source/control unlock, canonical merge input, Pre-Bayes/filter promotion, BBN mutation, CatBoost/path-ranker promotion, execution-tree promotion, production trade claim, or `update_goal` authorization was produced.

## Artifacts

- `102500` raw outputs: `docs/experiments/actionable-regime-confidence/runs/20260512T102500+0800-codex-board-b-yahoo-crypto-momentum-aq-v1/command-output/`
- `102812` packet summary: `docs/experiments/actionable-regime-confidence/runs/20260512T102812+0800-codex-board-b-provider-yf-nq-trendpulse-tick-precision-v1/provider_yf_nq_tick_precision_packet_summary_v1.json`
- `102812` strategy library: `docs/experiments/actionable-regime-confidence/runs/20260512T102812+0800-codex-board-b-provider-yf-nq-trendpulse-tick-precision-v1/provider_yf_nq_tick_precision_strategy_library_v1.json`
- `102812` real trades: `docs/experiments/actionable-regime-confidence/runs/20260512T102812+0800-codex-board-b-provider-yf-nq-trendpulse-tick-precision-v1/provider_yf_nq_sampled_pulse_real_trades_v1.jsonl`
- `102928` report: `docs/experiments/actionable-regime-confidence/runs/20260512T102928+0800-codex-board-b-provider-btc-tickfix-factor-v1/provider-btc-tickfix-factor-v1/provider_btc_tickfix_factor_v1.md`
- `103010` raw outputs: `docs/experiments/actionable-regime-confidence/runs/20260512T103010+0800-codex-board-b-provider-btc-always-entry-canary-v1/command-output/`
- `103114` raw outputs: `docs/experiments/actionable-regime-confidence/runs/20260512T103114+0800-codex-board-b-btc-signal-consumption-diagnostic-v1/command-output/`
- `103057` assertions: `docs/experiments/actionable-regime-confidence/runs/20260512T103057+0800-codex-structural-feedback-branch-preservation-fix-v1/checks/structural_feedback_branch_preservation_fix_v1_assertions.out`

