# Provider BTC Momentum Cross Readback v1

Run id: `20260512T101623+0800-codex-board-b-provider-btc-pulse-aq-v1`

Addendum id: `20260512T102708+0800-codex-board-b-provider-btc-momentum-cross-readback-v1`

Gate result: `provider_btc_momentum_cross_readback_v1=retry_exit0_all_three_zero_trades_no_promotion`

## Readback

- Source provider CSV: `docs/experiments/actionable-regime-confidence/runs/20260512T100419+0800-codex-board-b-provider-owned-aq-acquisition-v1/provider-csv/binance_btcusdt_1h.csv`.
- Provider path: Binance `BTC/USDT` 1h provider-owned acquisition from `100419`, replayed through the `101623` run-local Auto-Quant/TOMAC workspace.
- Prepared bars from the parent `101623` slice: `985` 1h, `247` 4h, and `42` 1d for `BTC/USDT`.
- The first momentum-cross command record, `02_run_provider_btc_momentum_cross`, failed before measurement with shell invocation `exit=127`; it is recorded as a command-wrapper failure, not as strategy evidence.
- The retry, `03_run_provider_btc_momentum_cross`, exited `0`.
- The retry measured three strategies through Freqtrade and ended with `Done: 3 succeeded, 0 failed`.
- `ProviderBtcMomentumCross` backtested `2026-04-03 12:00:00 -> 2026-05-12 00:00:00`; trades `0`, total profit percent `0.0000`, win rate `0.0000`, profit factor `0.0000`, Sharpe `0.0000`.
- `ProviderBtcMomentumPulse` backtested `2026-04-03 12:00:00 -> 2026-05-12 00:00:00`; trades `0`, total profit percent `0.0000`, win rate `0.0000`, profit factor `0.0000`, Sharpe `0.0000`.
- `ProviderBtcTrendPullback` backtested `2026-04-04 18:00:00 -> 2026-05-12 00:00:00`; trades `0`, total profit percent `0.0000`, win rate `0.0000`, profit factor `0.0000`, Sharpe `0.0000`.

Provider fields for Board B authority correction:
- `aq_provider_invoked`: Auto-Quant/TOMAC invoked in the `101623` run-local workspace; live provider fetch was not re-invoked in this addendum.
- `provider_requested`: Binance BTCUSDT 1h via `100419` provider-owned acquisition sidecar.
- `provider_data_acquired`: `true`.
- `provider_unreachable`: `[]`.
- `local_cache_replay`: `true`, using the provider-acquired CSV and prepared feathers inside the run-local workspace.

## Decision

- This addendum closes the unregistered `101623` retry and records the third BTC provider strategy family without changing the earlier `101623` terminal closeout.
- The retry reached measurement, but all three BTC strategies produced zero trades.
- Accepted rows added: `0`.
- Mature rooted branch observations: `0`.
- Profitability signal: `false`.
- Source/control evidence acquired: `false`.
- Explicit selected-history choice: `false`.
- Canonical merge: `false`.
- Selected-data AutoQuant promotion: `false`.
- Downstream promotion: `false`.
- Strict full objective: `false`.
- Trade usable: `false`.
- Promotion allowed: `false`.
- `update_goal=false`.

## Artifacts

- Retry command: `docs/experiments/actionable-regime-confidence/runs/20260512T101623+0800-codex-board-b-provider-btc-pulse-aq-v1/command-output/03_run_provider_btc_momentum_cross.cmd`
- Retry stdout: `docs/experiments/actionable-regime-confidence/runs/20260512T101623+0800-codex-board-b-provider-btc-pulse-aq-v1/command-output/03_run_provider_btc_momentum_cross.out`
- Retry stderr: `docs/experiments/actionable-regime-confidence/runs/20260512T101623+0800-codex-board-b-provider-btc-pulse-aq-v1/command-output/03_run_provider_btc_momentum_cross.err`
- Retry exit: `docs/experiments/actionable-regime-confidence/runs/20260512T101623+0800-codex-board-b-provider-btc-pulse-aq-v1/checks/03_run_provider_btc_momentum_cross.exit`
- Failed wrapper attempt exit: `docs/experiments/actionable-regime-confidence/runs/20260512T101623+0800-codex-board-b-provider-btc-pulse-aq-v1/checks/02_run_provider_btc_momentum_cross.exit`
- Run-local strategy: `docs/experiments/actionable-regime-confidence/runs/20260512T101623+0800-codex-board-b-provider-btc-pulse-aq-v1/workspace/auto-quant-provider-btc/user_data/strategies_external/ProviderBtcMomentumCross.py`
- JSON: `docs/experiments/actionable-regime-confidence/runs/20260512T101623+0800-codex-board-b-provider-btc-pulse-aq-v1/provider-btc-momentum-cross-readback-v1/provider_btc_momentum_cross_readback_v1.json`
- Checklist: `docs/experiments/actionable-regime-confidence/runs/20260512T101623+0800-codex-board-b-provider-btc-pulse-aq-v1/provider-btc-momentum-cross-readback-v1/prompt_to_artifact_checklist_provider_btc_momentum_cross_v1.csv`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260512T101623+0800-codex-board-b-provider-btc-pulse-aq-v1/checks/provider_btc_momentum_cross_readback_v1_assertions.out`

## Next

Do not rerun the same one-month Binance BTC TOMAC strategy set. Continue only with longer provider-provenanced BTC history, a materially different branch-specific provider strategy likely to produce nonzero rooted observations, or explicit selected-history/source-control unlocks before any selected-data Auto-Quant -> Pre-Bayes/filter -> BBN -> CatBoost/path-ranker -> execution-tree promotion chain.
