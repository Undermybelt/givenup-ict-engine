# Compatible Live Context Readback v1

Run id: `20260511T234918+0800-codex-board-b-220646-compatible-live-context-readback-v1`

## Decision

The latest exact Crisis-branch live replay did not repeat `block_crowded`. It moved to `fill_viable` / `observe` / `passive` with execution readiness `0.4504`, but it is still not a promotion signal.

Promotion remains blocked.

## Branch

- Branch path: `Crisis -> CrisisReliefCarry -> StopManagedPanicRecovery -> SourceRootStopCarryLongHorizonV1:crisis_carry_h8_sl048_tp12`
- Upstream strict state: RC-SPA overall `85.7407`; Crisis branch `83.0`; price roots `4/4`; scoped Manipulation component pass
- Prior nursery packet: `block_crowded` was installed as `incubation_only` negative execution-admissibility feedback in `234513`

## Live Chain Readback

- `analyze-live` exit: `0`
- Pre-Bayes/filter: `pass_neutralized`, quality `0.5619`
- BBN soft evidence: `applied`; soft market distribution `{range: 0.65, bull: 0.175, bear: 0.175}`
- CatBoost/path-ranker: validation ready; ranker score visible to and used by execution tree
- Execution tree: `fill_viable`, gate `observe`, bias `passive`, execution score `0.5637`
- Runtime market state: `RangeConsolidation/WideRange`
- Workflow blocker: `user_selected_historical_data_missing`

This proves `block_crowded` is context-sensitive feedback. It did not repeat under the latest live data fingerprint, but the branch still only reached observe/passive and cannot be promoted.

## Provider Readback

- yfinance: ready; QQQ harness fetch exit `0`
- TradingViewRemix MCP: unhealthy; QQQ harness fetch exit `1`
- IBKR: gateway/deps recorded; harness fetch exit `1` because a full explicit IBKR contract is required and runtime dependencies remain missing
- Kraken CLI: ready; XBT/USD 1h OHLC exit `0`
- Kraken public: unhealthy due missing provider Python modules

## Interpretation

`234513` remains valid as a nursery feature packet: `block_crowded` should suppress or defer this Crisis leaf in crowded / wide-range conditions. `233426` adds the repeat evidence: when the live context becomes marginally compatible, the exact branch can pass execution-tree hard block, but it still lands in observe/passive with no closed-loop promotion.

Corrected nursery packet path: `docs/experiments/actionable-regime-confidence/runs/20260511T234513-codex-board-b-b2r-block-crowded-nursery-v1/b2r-block-crowded-nursery-v1/b2r_block_crowded_nursery_v1.md`

Do not turn either readback into a production claim. The next useful step is either a user/data-selection gated factor-research pass over the recorded `233426` historical paths, or a sibling Crisis leaf that makes `RangeConsolidation/WideRange` suppression explicit and then reruns the full nursery backtest plus Pre-Bayes/BBN/CatBoost/execution-tree probes.

## Artifacts

- JSON: `docs/experiments/actionable-regime-confidence/runs/20260511T234918-codex-board-b-220646-compatible-live-context-readback-v1/compatible-live-context-readback-v1/compatible_live_context_readback_v1.json`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260511T234918-codex-board-b-220646-compatible-live-context-readback-v1/checks/compatible_live_context_readback_v1_assertions.out`
- Live replay: `docs/experiments/actionable-regime-confidence/runs/20260511T233426-codex-board-b-220646-crisis-branch-live-replay-v1/logs/03_analyze_live_crisis_bundle.out`
- Provider harness: `docs/experiments/actionable-regime-confidence/runs/20260511T234653-codex-board-b-220646-b2r-block-crowded-live-context-v1/provider`
