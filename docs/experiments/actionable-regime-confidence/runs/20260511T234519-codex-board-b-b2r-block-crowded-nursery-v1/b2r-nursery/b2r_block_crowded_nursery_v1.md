# B2R Block-Crowded Nursery v1

## Decision

`block_crowded` is retained as a negative execution-admissibility feature for the exact Crisis branch, but this packet is `incubation_only` and does not promote `220646`.

## Branch

- Branch path: `Crisis -> CrisisReliefCarry -> StopManagedPanicRecovery -> SourceRootStopCarryLongHorizonV1:crisis_carry_h8_sl048_tp12`
- Parent root: `Crisis`
- Recipe: `SourceRootStopCarryLongHorizonV1`
- Prior score: `85.7407` from strict RC-SPA; price roots stayed `4/4` passed in the source packet.

## Evidence

- Previous exact-branch readback: `block_crowded` / `blocked` with readiness `0.4433 < 0.45`.
- Fresh live replay: `fill_viable` / `observe` with execution score `0.5637`.
- Fresh Pre-Bayes gate: `pass_neutralized`.
- Fresh structural bundle path preserved: `True`.
- CatBoost/path-ranker runtime source remains `history_path` with status `using_history_scores`.
- Provider readback: `entry_model:2/2 ready | live_runtime:1/3 ready | local_runtime:1/2 ready | market_data:1/7 ready`.
- Local Auto-Quant readback: `dependency_ready_seed_required`, healthy `True`, data_ready `True`.

## Interpretation

The exact branch path reaches Pre-Bayes, BBN soft-evidence readback, CatBoost/path-ranker history, and execution-candidate surfaces. The prior blocked state and fresh observe state should be treated as branch-local execution-context feedback, not as a profitability rejection and not as a promotion signal.

The live replay changed `block_crowded` to `fill_viable`, but the execution tree still returned `observe` and the workflow asks for explicit historical-data selection before factor-research continuation. Therefore the correct state is nursery feedback only.

## Artifacts

- JSON: `/Users/thrill3r/projects-ict-engine/ict-engine/docs/experiments/actionable-regime-confidence/runs/20260511T234519-codex-board-b-b2r-block-crowded-nursery-v1/b2r-nursery/b2r_block_crowded_nursery_v1.json`
- Gates: `/Users/thrill3r/projects-ict-engine/ict-engine/docs/experiments/actionable-regime-confidence/runs/20260511T234519-codex-board-b-b2r-block-crowded-nursery-v1/b2r-nursery/b2r_block_crowded_nursery_v1_gates.csv`
- Assertions: `/Users/thrill3r/projects-ict-engine/ict-engine/docs/experiments/actionable-regime-confidence/runs/20260511T234519-codex-board-b-b2r-block-crowded-nursery-v1/b2r-nursery/b2r_block_crowded_nursery_v1_assertions.out`
- Logs: `docs/experiments/actionable-regime-confidence/runs/20260511T234519-codex-board-b-b2r-block-crowded-nursery-v1/logs/`
- Concurrent fresh replay consumed read-only: `docs/experiments/actionable-regime-confidence/runs/20260511T233426-codex-board-b-220646-crisis-branch-live-replay-v1/`

## Next

Keep `220646` blocked for promotion. Continue only after the exact branch reaches execution-tree admit, or after a predeclared historical-data continuation is selected and replayed through the same rooted branch path.
