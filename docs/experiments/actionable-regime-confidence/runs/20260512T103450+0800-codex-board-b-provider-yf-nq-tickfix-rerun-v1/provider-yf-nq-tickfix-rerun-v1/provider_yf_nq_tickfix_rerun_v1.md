# Provider YF NQ Tickfix Rerun v1

Run id: `20260512T103450+0800-codex-board-b-provider-yf-nq-tickfix-rerun-v1`

Gate result: `provider_yf_nq_tickfix_rerun_v1=entry_wire_repaired_nonzero_trades_no_promotion`

## Readback

- Source workspace: copied from `20260512T102332+0800-codex-board-b-provider-yf-nq-trendpulse-aq-v1/workspace/auto-quant-yf-nq-trendpulse`.
- Source data: provider-owned Yahoo `NQ=F` long-history feathers already present in that workspace.
- Run-local harness repair: changed only the copied synthetic-market precision from whole-unit ticks to `amount=0.000001` and `price=0.01`.
- Run-local config repair: changed copied `exit_pricing.price_side` from `same` to `other` because Freqtrade rejects market exits with `same`.
- First precheck command captured the config failure; second command exited `0` and ran all three strategies.

## Results

| Strategy | Trades | Total Profit % | Sharpe | Win Rate % | Profit Factor | Gate |
|---|---:|---:|---:|---:|---:|---|
| `ProviderNqAlwaysInDiagnostic` | 2782 | -61.30 | -5.4536 | 29.3314 | 0.6067 | `fail_closed:diagnostic_always_in_unprofitable` |
| `ProviderNqSampledPulse` | 18 | 0.97 | 0.1898 | 33.3333 | 5.3246 | `fail_closed:profitable_but_probe_only_trade_count_18` |
| `ProviderNqTrendPulse` | 896 | -38.10 | -3.3038 | 37.7232 | 0.5912 | `fail_closed:dense_provider_nq_strategy_unprofitable` |

## Decision

- The copied NQ entry-wire blocker is confirmed as a tick-size / execution-translation issue, not absence of provider-owned Yahoo NQ signals.
- The only profitable strategy in this rerun has `18` trades, which is below the board's mature evidence threshold and remains probe-only.
- The dense strategies are unprofitable; no selected-history approval, source/control unlock, Pre-Bayes/BBN/CatBoost/path-ranking/execution-tree promotion rerun, or promotion claim is allowed.
- Promotion allowed: `false`.
- `update_goal=false`.

## Artifacts

- Failed precheck stdout: `docs/experiments/actionable-regime-confidence/runs/20260512T103450+0800-codex-board-b-provider-yf-nq-tickfix-rerun-v1/command-output/00_run_provider_yf_nq_tickfix_rerun.out`
- Failed precheck stderr: `docs/experiments/actionable-regime-confidence/runs/20260512T103450+0800-codex-board-b-provider-yf-nq-tickfix-rerun-v1/command-output/00_run_provider_yf_nq_tickfix_rerun.err`
- Successful rerun stdout: `docs/experiments/actionable-regime-confidence/runs/20260512T103450+0800-codex-board-b-provider-yf-nq-tickfix-rerun-v1/command-output/01_run_provider_yf_nq_tickfix_rerun_after_config_repair.out`
- Successful rerun stderr: `docs/experiments/actionable-regime-confidence/runs/20260512T103450+0800-codex-board-b-provider-yf-nq-tickfix-rerun-v1/command-output/01_run_provider_yf_nq_tickfix_rerun_after_config_repair.err`
- Successful rerun exit: `docs/experiments/actionable-regime-confidence/runs/20260512T103450+0800-codex-board-b-provider-yf-nq-tickfix-rerun-v1/checks/01_run_provider_yf_nq_tickfix_rerun_after_config_repair.exit`
- JSON: `docs/experiments/actionable-regime-confidence/runs/20260512T103450+0800-codex-board-b-provider-yf-nq-tickfix-rerun-v1/provider-yf-nq-tickfix-rerun-v1/provider_yf_nq_tickfix_rerun_v1.json`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260512T103450+0800-codex-board-b-provider-yf-nq-tickfix-rerun-v1/checks/provider_yf_nq_tickfix_rerun_v1_assertions.out`
