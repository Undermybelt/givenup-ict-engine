# Provider BTC Signal Canary v1

Run id: `20260512T102352+0800-codex-board-b-provider-btc-signal-canary-v1`

Gate result: `provider_btc_signal_canary_v1=precision_root_cause_confirmed_nonzero_after_tickfix_no_promotion`

## Readback

- Source provider CSV lineage: Binance `BTCUSDT` 1h provider CSV from `20260512T100419+0800-codex-board-b-provider-owned-aq-acquisition-v1`, copied through the earlier `101623` prepared BTC workspace.
- Diagnostic strategy: `ProviderBtcSignalCanary`.
- Before the run-local tick-size fix, the same provider BTC feathers and deterministic canary emitted `0` executed trades.
- Precision probe showed this local Freqtrade/Binance path uses ccxt `TICK_SIZE` mode. With the old synthetic market precision, `amount=8` is interpreted as an 8-unit amount tick, so a sample `9900 / 68600.29 = 0.14431425872981005` BTC stake rounded to `0.0`.
- After changing only this run-local harness to `amount=0.00000001`, the same sample rounded to `0.14431425`, and the canary backtest produced `40` executed trades.
- Canary result after fix: total profit `-3.9000%`, Sharpe `-2.2199`, win rate `45.0000%`, profit factor `0.7079`, average duration `6:00:00`.

## Decision

- The zero-trade behavior in the copied BTC TOMAC workspace was an execution-translation blocker, not proof that provider BTC data lacked signals.
- This is diagnostic evidence only. `ProviderBtcSignalCanary` is not a factor candidate, not selected-history evidence, not source/control evidence, and not downstream promotion evidence.
- Promotion allowed: `false`.
- `update_goal=false`.

## Artifacts

- Pre-fix canary stdout: `docs/experiments/actionable-regime-confidence/runs/20260512T102352+0800-codex-board-b-provider-btc-signal-canary-v1/command-output/00_run_provider_btc_signal_canary.out`
- Tick-fixed canary stdout: `docs/experiments/actionable-regime-confidence/runs/20260512T102352+0800-codex-board-b-provider-btc-signal-canary-v1/command-output/01_run_provider_btc_signal_canary_tickfix.out`
- Precision probe: `docs/experiments/actionable-regime-confidence/runs/20260512T102352+0800-codex-board-b-provider-btc-signal-canary-v1/command-output/02_precision_signal_translation_probe.out`
- Run-local harness: `docs/experiments/actionable-regime-confidence/runs/20260512T102352+0800-codex-board-b-provider-btc-signal-canary-v1/workspace/auto-quant-provider-btc-signal-canary/run_tomac.py`
- Strategy: `docs/experiments/actionable-regime-confidence/runs/20260512T102352+0800-codex-board-b-provider-btc-signal-canary-v1/workspace/auto-quant-provider-btc-signal-canary/user_data/strategies_external/ProviderBtcSignalCanary.py`
- JSON: `docs/experiments/actionable-regime-confidence/runs/20260512T102352+0800-codex-board-b-provider-btc-signal-canary-v1/provider-btc-signal-canary-v1/provider_btc_signal_canary_v1.json`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260512T102352+0800-codex-board-b-provider-btc-signal-canary-v1/checks/provider_btc_signal_canary_v1_assertions.out`
