# SourceRootStopCarryLongHorizon B5 Live Readback v1

Run id: `20260511T220646+0800-codex-board-b-source-root-stop-carry-longhorizon-v1`

Purpose: read back the B5 downstream-consumption state for the exact rooted branch paths from `SourceRootStopCarryLongHorizonV1` without changing runtime code, relaxing gates, or forcing duplicate ingest.

## Fresh Commands Run

- `./target/debug/ict-engine provider-status --agent`
- `./target/debug/ict-engine workflow-status --symbol SRC_STOP_CARRY_LH_220646 --state-dir /tmp/ict-engine-board-b-source-root-stop-carry-longhorizon-220646 --phase bootstrap --agent`
- `./target/debug/ict-engine workflow-status --symbol SRC_STOP_CARRY_LH_220646 --state-dir /tmp/ict-engine-board-b-source-root-stop-carry-longhorizon-220646 --phase structural-recommended-path-bundle --agent`
- `./target/debug/ict-engine workflow-status --symbol SRC_STOP_CARRY_LH_220646 --state-dir /tmp/ict-engine-board-b-source-root-stop-carry-longhorizon-220646 --phase execution-candidate --agent`
- `./target/debug/ict-engine pre-bayes-status --symbol SRC_STOP_CARRY_LH_220646 --state-dir /tmp/ict-engine-board-b-source-root-stop-carry-longhorizon-220646 --refresh --output-format json`

## Coverage Readback

- Wire audit: `12329` records, `4` unique rooted branch paths, missing required wire fields `0`.
- Root counts: `Bull=4948`, `Bear=1349`, `Sideways=5500`, `Crisis=532`.
- Branch paths preserved:
  - `Bull -> RootCarryExpansion -> StopManagedRiskCarry -> SourceRootStopCarryLongHorizonV1:bull_carry_h12_sl040_tp12`
  - `Bear -> BearReliefCarry -> StopManagedRecoveryCarry -> SourceRootStopCarryLongHorizonV1:bear_carry_h20_sl048_tp12`
  - `Sideways -> RangeCarry -> StopManagedRangeCarry -> SourceRootStopCarryLongHorizonV1:sideways_carry_h8_sl040_tp12`
  - `Crisis -> CrisisReliefCarry -> StopManagedPanicRecovery -> SourceRootStopCarryLongHorizonV1:crisis_carry_h8_sl048_tp12`
- Existing downstream probe JSON: `downstream_probe_partial_fail_closed`; `branch_path_preserved=true`; `closed_loop_confidence_ready=false`; `promotion_allowed=false`.
- Existing dry-run ingest: exit `0`, `trades_invalid=0`, `wire_records=12329`.
- Existing apply ingest: exit `1`; runtime refused re-ingest because content hash `e313d6fefe0324dc` already exists as an auto-quant real-trades ingest entry. No `--force` was run.
- Pre-Bayes live readback: no latest bridge, no latest policy, no latest gate, no soft evidence; policy versions `0`.
- Workflow live readback: `no_workflow_state`; structural recommended path is bootstrap/readiness only; execution-candidate output is `null`.
- CatBoost/path-ranker live readback from existing probe: policy training not ready, matched rows `0`; structural path ranking target has no calibrated branch evidence and no mature validation rows.
- Provider readback: yfinance ready; Kraken CLI ready; IBKR gateway reachable but runtime/dependencies unhealthy; TradingView MCP/TradingViewRemix remains configured but unhealthy on the live probe, so it is not accepted as ready live OHLCV evidence for this slice.

## Decision

- B5 status: `partial_fail_closed`.
- Promotion allowed: `false`.
- Closed-loop confidence ready: `false`.
- Reason: the Auto-Quant / RC-SPA branch score is strong and the rooted branch-path wire is preserved, but the runtime stack has not consumed and re-emitted the same rooted branch paths through Pre-Bayes, BBN, CatBoost/path-ranker, and execution tree with a promotable `closed_loop_confidence`.
- Runtime code changed: `false`.
- Thresholds relaxed: `false`.
- Force ingest used: `false`.

## Next

Resolve the duplicate-ingest / `no_workflow_state` blocker without using blind `--force`: either locate and audit the existing ingest/BBN state for content hash `e313d6fefe0324dc`, or create a clean downstream state that can ingest the exact `220646` branch-path wire once. Then rerun Pre-Bayes -> BBN -> CatBoost/path-ranker -> execution tree and require `closed_loop_confidence` before any promotion claim.
