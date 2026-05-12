# Provider BTC Pulse AQ v1

Run id: `20260512T101623+0800-codex-board-b-provider-btc-pulse-aq-v1`

Gate result: `provider_btc_pulse_aq_v1=prepared_and_backtested_zero_trades_no_promotion`

## Readback

- Source provider CSV: `docs/experiments/actionable-regime-confidence/runs/20260512T100419+0800-codex-board-b-provider-owned-aq-acquisition-v1/provider-csv/binance_btcusdt_1h.csv`.
- Prepare command exited `0`.
- TOMAC/Freqtrade command exited `0`.
- Raw rows loaded: `985`; bad dates `0`; duplicate timestamps `0`; NaN OHLC rows `0`; after-load rows `985`.
- Provider range: `2026-04-01 00:00:00+00:00` to `2026-05-12 00:00:00+00:00`.
- Prepared bars: `985` 1h, `247` 4h, and `42` 1d for `BTC/USDT`.
- Strategy: `ProviderBtcTrendPullback`.
- Backtest window after startup candles: `2026-04-04 18:00:00` to `2026-05-12 00:00:00`.
- Trades: `0`; total profit percent `0.0000`; win rate `0.0000`; profit factor `0.0000`; Sharpe `0.0000`.

## Decision

- This proves a provider-owned Binance BTC slice can be prepared and passed into the TOMAC/Freqtrade workspace.
- It does not produce any nonzero trade observations, mature rooted branch observations, source/control unlock evidence, selected-history approval, canonical merge input, downstream promotion evidence, or trade-usable evidence.
- Accepted rows added: `0`.
- Every-regime 95%-99% objective: `false`.
- Cross-context full validation: `false`.
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

- Prepare stdout: `docs/experiments/actionable-regime-confidence/runs/20260512T101623+0800-codex-board-b-provider-btc-pulse-aq-v1/command-output/00_prepare_binance_btc_csv.out`
- TOMAC stdout: `docs/experiments/actionable-regime-confidence/runs/20260512T101623+0800-codex-board-b-provider-btc-pulse-aq-v1/command-output/01_run_provider_btc_pulse.out`
- TOMAC stderr: `docs/experiments/actionable-regime-confidence/runs/20260512T101623+0800-codex-board-b-provider-btc-pulse-aq-v1/command-output/01_run_provider_btc_pulse.err`
- Prepared workspace: `docs/experiments/actionable-regime-confidence/runs/20260512T101623+0800-codex-board-b-provider-btc-pulse-aq-v1/workspace/auto-quant-provider-btc`
- JSON: `docs/experiments/actionable-regime-confidence/runs/20260512T101623+0800-codex-board-b-provider-btc-pulse-aq-v1/provider-btc-pulse-aq-v1/provider_btc_pulse_aq_v1.json`
- Checklist: `docs/experiments/actionable-regime-confidence/runs/20260512T101623+0800-codex-board-b-provider-btc-pulse-aq-v1/provider-btc-pulse-aq-v1/prompt_to_artifact_checklist_provider_btc_pulse_v1.csv`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260512T101623+0800-codex-board-b-provider-btc-pulse-aq-v1/checks/provider_btc_pulse_aq_v1_assertions.out`

## Next

Do not repeat the same Binance BTC one-month TOMAC pulse shape. Continue only after changed source/control evidence, an explicit `HTF`/`MTF`/`LTF` selected-history choice, a provider/strategy input that yields nonzero mature observations, or a coordinated structural-feedback owner fix.
