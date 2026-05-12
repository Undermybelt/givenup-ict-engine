# 122616 Selected-History 1h Factor Research Unlock - Fail Closed

Run root: `docs/experiments/actionable-regime-confidence/runs/20260512T122616+0800-codex-115700-selected-history-1h-factor-research-unlock-v1`

Started: `2026-05-12T12:26:16+0800`

Finished marker: `2026-05-12T12:26:27+0800`

## Commands

- `01_factor_research_selected_1h`: exited `0`.
- `02_auto_quant_prepare`: exited `1`.

## Decision

This root does not unlock selected-history, Auto-Quant data readiness, BBN confidence, or execution promotion.

The factor-research command used the `121347` BTC 1h provider JSON and produced an Auto-Quant handoff, but the handoff remained `dependency_ready_data_missing` / `data_ready=false`. The workflow snapshot still reports `user_selected_historical_data_missing` and requires explicit historical data selection before reuse.

The Auto-Quant prepare command failed while loading Binance markets. The captured error includes `Could not contact DNS servers`, `Cannot connect to host api.binance.com:443`, and `Markets were not loaded`.

Downstream state remains unchanged:

- Pre-Bayes phase: `pre_bayes_neutralized_review`.
- Pre-Bayes quality / canonical structural confidence: `0.5250864595751618`.
- Max structural regime probability: range `0.7476877176681956`.
- Execution readiness: `0.32853919817900823`.
- Execution gate: `execution_blocked`.
- Execution candidate: `no_trade`, `actionable=false`, review `observe`.

## Board Effect

- Accepted Board A rows added: `0`.
- Selected-history/source-control unlock: `false`.
- Auto-Quant prepared data: `false`.
- Production BBN likelihood/CPD mutation: `false`.
- Execution promotion: `false`.
- Trade usable: `false`.
- `update_goal`: `false`.

## Next

Do not rerun this exact BTC-only 1h selected-history path as a promotion candidate. Continue with non-BTC instruments, non-1h timeframe/cycle evidence, explicit selected-history/source-control unlock, and execution-readiness unlock before any `>=95%` regime claim.
