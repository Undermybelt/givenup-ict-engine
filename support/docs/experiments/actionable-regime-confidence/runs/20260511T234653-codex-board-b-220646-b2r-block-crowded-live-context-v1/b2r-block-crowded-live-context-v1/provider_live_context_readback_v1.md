# Provider / Live-Context Readback v1

Run id: `20260511T234653+0800-codex-board-b-220646-b2r-block-crowded-live-context-v1`

## Scope

Additive provider and live-chain readback for the exact `220646` Crisis branch. This run does not supersede the active Board B cursor and does not promote `220646`.

Exact branch path:

`Crisis -> CrisisReliefCarry -> StopManagedPanicRecovery -> SourceRootStopCarryLongHorizonV1:crisis_carry_h8_sl048_tp12`

## Provider Readback

- yfinance provider status: ready; QQQ 1d harness fetch exit `0`.
- TradingViewRemix MCP provider status: `configured_runtime_unhealthy`; QQQ harness fetch exit `1` with MCP `get_ohlcv` failure.
- IBKR provider status: `configured_runtime_unhealthy`; local gateway/dependency state recorded; harness fetch exit `1` because a full explicit IBKR contract is required.
- Kraken CLI provider status: ready; `XBTUSD` 1h OHLC exit `0`.
- Kraken public provider status: `configured_runtime_unhealthy` because provider Python modules are missing.

## Live Chain Readback

- `analyze-live` exit: `0`.
- Auto-Quant status against the run-local managed state: `missing_dependency`; this run consumes the existing `220646` Auto-Quant artifacts instead of launching new heavy training.
- Pre-Bayes/filter: `pass_neutralized`; policy `318900600c5e8cf2`; quality `0.5554`.
- BBN soft evidence in this live run: skipped with `no_supported_label`; earlier accepted BBN repairs remain recorded in the `220646` downstream rows.
- CatBoost/path-ranker: trainer artifact ready; runtime selection ready; production validation `274/30`, observation validation `48/30`; exact Crisis branch score visible to and used by the execution tree.
- Execution tree: `block_crowded`; gate `blocked`; bias `skip`; readiness `0.4470 < 0.45`.
- Runtime market state: `RangeConsolidation/WideRange`.

## Interpretation

This run is repeat evidence for the `block_crowded` nursery feature, not a production signal. It preserves the exact Crisis branch path through the live chain and confirms the remaining failure is execution-admissibility under crowded / wide-range context.

The later `234918` compatible-context row should be treated as the active Board B cursor. This artifact only supplies the provider and live-context evidence referenced by that row.

## Artifacts

- Provider logs: `docs/experiments/actionable-regime-confidence/runs/20260511T234653-codex-board-b-220646-b2r-block-crowded-live-context-v1/provider`
- Live-chain logs: `docs/experiments/actionable-regime-confidence/runs/20260511T234653-codex-board-b-220646-b2r-block-crowded-live-context-v1/logs`
- Run-local state: `docs/experiments/actionable-regime-confidence/runs/20260511T234653-codex-board-b-220646-b2r-block-crowded-live-context-v1/state_b2r_block_crowded_live_context_v1`
