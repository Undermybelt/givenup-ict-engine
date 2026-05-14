# Agent-Selected Historical Factor Research v1

Run id: `20260512T000748+0800-codex-board-b-agent-selected-historical-factor-research-v1`

## Decision

This run is fail-closed nursery evidence. It does not promote `SourceRootStopCarryLongHorizonV1` or the Crisis sibling leaf.

The recorded MTF path reached the Auto-Quant handoff surface. Initial prepare/run attempts failed on dependency shape, pair wiring, and Binance market metadata/DNS, then later offline-compatible NQ/USD runs succeeded technically but produced zero trades for every seeded strategy. There is still no nonzero trade row set, branch-conditioned return series, or measured profitability factor to send through promotion checks.

## Auto-Quant Evidence

- `factor-research` exited `0` and emitted a handoff artifact for `SRC_ROOT_CARRY_LONG_220646`.
- Handoff artifact: `docs/experiments/actionable-regime-confidence/runs/20260512T000748-codex-board-b-agent-selected-historical-factor-research-v1/state_agent_selected_historical_factor_research_v1/SRC_ROOT_CARRY_LONG_220646/auto_quant_handoff.factor_research.json`
- Handoff status: `dependency_ready_data_missing`
- Dependency status: healthy, pinned Auto-Quant commit `34ba6b6ee6aa69813a50a72158d4c089d97afb96`
- Initial data readiness: `false`
- Initial active Auto-Quant strategy count: `0`
- Initial `auto-quant-prepare` attempts failed because the expected dependency/state shape was not ready.
- Nested bootstrap succeeded, but nested and direct prepare attempts failed while loading Binance markets: `ExchangeNotAvailable` / `Markets were not loaded`.
- Recorded MTF conversion wrote local feather files for `BTC/USDT`, `SRC_ROOT_CARRY_LONG_220646/USD`, and `NQ/USD` under the run-local Auto-Quant data directory.
- Offline-compatible direct/Tomac/profile runs later exited `0` for the seeded strategy set, but `RegimeRsiRelief`, `RegimeTrendCarry`, and `RegimeVolBreakout` each produced `0` trades, `0.0000` Sharpe, and `0.0000` total profit.

## Related Tomac Probe

The sibling `20260512T000440` Tomac attempts did not produce a usable result:

- `06_auto_quant_run_tomac.exit=1`: `No pair in whitelist`
- `07_auto_quant_run_tomac_nq_alias.exit=1`: `No data found. Terminating.`

These are data/pair-wire failures, not profitability rejections.

## Offline Repair Attempts

Later attempts in this same run root repaired enough of the local data/pair shape to execute Freqtrade without the Binance DNS blocker:

- `08_prepare_external_btc_compat.exit=0`
- `08_prepare_external_recorded_branch_pair.exit=0`
- `10_prepare_external_recorded_nq_pair.exit=0`
- `08_run_recorded_branch_offline.exit=0`
- `09_auto_quant_run_tomac_profile.exit=0`
- `10_run_tomac_agent_selected_mtf.exit=0`
- `11_auto_quant_run_recorded_nq_branch.exit=0`

Result: all three seeded strategies ran against the local NQ/USD path, but all three emitted zero trades. This is stronger than the earlier dependency blocker: the current blocker is `zero_trade_auto_quant_candidate`, not merely missing data.

## Provider Readback

Provider status command exited `0`.

- yfinance: ready
- Kraken CLI: ready
- IBKR: gateway/deps recorded but not ready
- TradingViewRemix MCP: not ready
- Kraken public: not ready

## Downstream State

No new nonzero-trade Auto-Quant candidate was available for downstream promotion. Copied downstream-state probes were callable, but they reflect existing branch-path runtime state rather than a newly measured Auto-Quant profitability candidate. A final primary-state workflow refresh was stricter: it reported `insufficient_state` / no workflow phase snapshots, and execution-candidate returned `ready=false` / `observe`.

```text
factor_research_handoff_only
auto_quant_data_ready_false
auto_quant_prepare_failed
no_measured_strategy_result
zero_trade_auto_quant_candidate
pre_bayes_pass_neutralized_existing_branch
execution_candidate_observe
primary_state_workflow_insufficient_state
primary_state_execution_candidate_ready_false
workflow_blocked_user_selected_historical_data_missing
promotion_allowed_false
```

## Next

Ask for or obtain an explicit user-selected historical dataset, or switch to a strategy/family that emits nonzero trades on the recorded path. Do not promote from this cursor.
