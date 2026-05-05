# Structural Belief Repo Action Board

> Authoritative execution board for the remaining structural-belief / transition / path-ranking closure work. This file intentionally keeps only actionable remaining work and execution rules. Historical reconciliation notes and long landed-item ledgers do not belong here anymore.

**Goal:** close the remaining structural-belief / transition / path-ranking work without reopening already-good-enough profile polish and without breaking zero-config, consumer-usable, token-friendly, low-pollution behavior.

**Source Docs:** `docs/plans/20260501repo.md`, `docs/plans/2026-04-30-structural-belief-execution-plan.md`

**Do Not Reopen By Default:** provider-profile polish, wording-only surface cleanup, maintainer-local default reuse, or any repo-owned consumer stance that is not required by an unchecked item below.

---

## Hard Constraints

- Preserve the public `node -> branch -> scenario -> path` contract.
- Preserve zero-config default behavior. Any history/profile/runtime artifact reuse must remain explicit opt-in behavior.
- Keep consumer surfaces token-friendly and consumer-usable.
- Do not leak maintainer-local paths, maintainer-local state, or user-specific artifact URIs into default surfaces.
- Keep the repo low-pollution and low-debt. Prefer extraction and deletion of duplicate logic over adding one more wrapper layer.
- Do not spend the current closure slice on surface proliferation when owner closure or verification hardening is still open.

## Agent Contract

1. Read this file and the two source docs before changing code.
2. Treat this file as the implementation contract for the current slice. Do not renegotiate scope unless blocked by concrete repo evidence.
3. Pick exactly one unchecked item as the active slice. Do not mix multiple workstreams into one vague pass.
4. Before editing, identify the owner files and the exact verification commands for the chosen slice.
5. When touching shared files such as `src/state/types.rs`, `src/application/orchestration/workflow_status.rs`, `src/application/orchestration/structural_playbook.rs`, or `src/main.rs`, reduce ownership instead of adding more inline math or more glue.
6. Do not spend a slice on provider-profile polish, payload cosmetics, or wording cleanup unless an unchecked item explicitly requires it.
7. A slice is not done until code, targeted verification, and this markdown are all updated.
8. After a slice lands, update this same markdown and make a clean commit for that slice. Do not create a new board doc.
9. If the worktree is dirty in unrelated files, isolate your slice and work with the existing state. Do not revert others' changes.
10. If blocked, write a short blocker note into the `Blocked` section with exact file / function / test evidence.

## Agent Quick Start

- If no narrower instruction is given, start with `Workstream 1` and pick the first unchecked item.
- Default first slice: move remaining delayed-reward aggregate / hazard / censoring / competing-risk owner logic out of `src/state/types.rs` into `src/belief_core/source_reliability.rs`.
- Do not start in `Workstream 3` unless `Workstream 1`, `Workstream 2`, and `Workstream 4` are no longer the real blocker.
- Before editing, read the exact owner files and function anchors below. Do not guess the entry points.

### Default First Slice: Open These First

- `src/belief_core/source_reliability.rs`
  - `structural_source_reliability_em_diagnostics`
  - `structural_source_reliability_em_fit_from_state`
  - `refresh_structural_source_reliability_em_state`
  - `structural_delayed_reward_replay_validation`
  - `structural_experience_prior_runtime_metrics`
- `src/state/types.rs`
  - `structural_source_reliability_em_diagnostics`
  - `structural_source_reliability_em_fit_from_state`
  - `refresh_structural_source_reliability_em_state`
  - `rebuild_structural_sequence_priors`
- `src/application/orchestration/structural_playbook.rs`
  - `build_structural_experience_prior_surface_artifact_with_prior_state`
  - call sites of `structural_experience_prior_runtime_metrics(...)`
  - call site of `structural_delayed_reward_replay_validation(...)`

Locate them with:

```bash
rg -n 'structural_source_reliability_em_diagnostics|structural_source_reliability_em_fit_from_state|refresh_structural_source_reliability_em_state|structural_delayed_reward_replay_validation|structural_experience_prior_runtime_metrics|rebuild_structural_sequence_priors' \
  src/belief_core/source_reliability.rs \
  src/state/types.rs \
  src/application/orchestration/structural_playbook.rs
```

Minimum verification for this default first slice:

```bash
cargo check
cargo test source_reliability_em_readiness_requires_multi_source_overlap
cargo test source_reliability_em_fit_learns_lower_reliability_for_conflicting_source
cargo test test_structural_source_reliability_em_holdout_prefers_chronological_split
```

## Already Landed, Do Not Redo

- `belief_core::{structural_state, source_reliability, regime_filter, changepoint_gate, ranking_label, beta_dirichlet_update}` already exist. Do not waste time recreating modules.
- The opt-in structural path-ranker runtime already exists for scored-row reuse, direct weighted-feature models, and declared scoring services.
- `workflow-status` and `policy-training-status` already expose low-token structural validation and ranker-runtime summaries.
- The provider-profile hot-plug lane is good enough for now. Do not reopen it unless fixing a concrete regression.
- Starter source-reliability holdout/replay and delayed-reward replay validation already exist. The remaining work is to strengthen them, not merely restate them.

## Do Now

### Workstream 1: Belief-Core Extraction

**Objective:** remove the remaining structural-learning ownership from oversized mixed-purpose files.

**Done when:** `src/state/types.rs`, `src/application/orchestration/structural_playbook.rs`, `src/application/orchestration/workflow_status.rs`, and `src/main.rs` are consumers or shells rather than dominant owners of structural math.

- [ ] Move the remaining delayed-reward aggregate / hazard / censoring / competing-risk owner logic out of `src/state/types.rs` into `src/belief_core/source_reliability.rs`.
- [ ] Move the remaining temporal / duration rebuild ownership out of `src/state/types.rs` into `src/belief_core/{regime_filter, changepoint_gate}.rs`.
- [ ] Reduce `src/application/orchestration/structural_playbook.rs` to shared-bundle assembly only. Remove remaining duplicated experience-prior and validation math.
- [ ] Reduce `src/application/orchestration/workflow_status.rs` to phase selection and rendering only. No structural math ownership should remain there.
- [ ] Keep `src/main.rs` on thin dispatch only. Do not add new structural-learning math or new surface-specific structural glue there.

**Latest landed on this lane:**

- `7fadd58` moved source-reliability EM diagnostics / fit / persisted-refresh ownership into `src/belief_core/source_reliability.rs`, with `src/state/types.rs` reduced to thin public wrappers for that lane.

**Read first when working this lane:**

- `src/state/types.rs`: `rebuild_structural_sequence_priors(...)`
- `src/belief_core/source_reliability.rs`: EM / delayed-reward owner functions listed in `Agent Quick Start`
- `src/application/orchestration/structural_playbook.rs`: experience-prior surface assembly
- `src/application/orchestration/workflow_status.rs`: validation-summary and ranker-summary rendering only if a surface contract is touched

### Workstream 2: Transition And Changepoint Closure

**Objective:** replace heuristic transition and break blending with one maintained core.

**Done when:** transition refresh and break maintenance have one clear owner each, and snapshot-time reweighting is only a consumer of maintained state.

- [ ] Make `src/belief_core/regime_filter.rs` the single owner of maintained node / branch transition refresh.
- [ ] Make `src/belief_core/changepoint_gate.rs` the single owner of break / sequence-break maintenance.
- [ ] Remove fixed weighted blends from consumer layers. Snapshot-time reweighting must consume maintained filter state instead of acting as the main engine.
- [ ] Reduce `src/application/belief/structural_temporal_adjustment.rs` to compatibility-only usage of the maintained core.

**Read first when working this lane:**

- `src/state/types.rs`: `rebuild_structural_sequence_priors(...)`
- `src/belief_core/regime_filter.rs`
  - `refresh_node_transition_posteriors`
  - branch-temporal posterior refresh / recursive transition helpers
- `src/belief_core/changepoint_gate.rs`
  - `structural_bocpd_break_probability`
  - `structural_node_bocpd_sequence_break_probability`
  - duration-prior changepoint update block
- `src/application/belief/structural_temporal_adjustment.rs`: compatibility-shell call sites and tests

Locate them with:

```bash
rg -n 'rebuild_structural_sequence_priors|refresh_node_transition_posteriors|branch_temporal_posteriors|bocpd|sequence_break|break_probability' \
  src/state/types.rs \
  src/belief_core/regime_filter.rs \
  src/belief_core/changepoint_gate.rs \
  src/application/belief/structural_temporal_adjustment.rs
```

### Workstream 4: Validation Hardening

**Objective:** move from compact diagnostics to stronger evidence-bearing validation.

**Done when:** validation surfaces say not only `ready / not ready`, but also why, how much evidence exists, and what split or panel produced the status.

- [ ] Strengthen source-reliability validation beyond compact holdout / replay summaries into larger-panel or more explicit out-of-sample evaluation.
- [ ] Keep validation summaries low-token, but always expose panel size, coverage, split boundary, and failure reason.
- [ ] Strengthen delayed-reward validation beyond current horizon-only diagnostics. If full event-time competing-risk is not landed in the slice, leave a clearer intermediate owner and explicit remaining gap here.
- [ ] Keep the target-policy upgrade path explicit. Do not silently entrench the current `symbol:regime:direction` bucket-posterior model as the final state.

**Read first when working this lane:**

- `src/belief_core/source_reliability.rs`: holdout / replay / delayed-reward replay owner functions and tests
- `src/application/orchestration/workflow_status.rs`
  - `build_structural_validation_summary_value`
  - `build_path_ranker_summary_value`
- `src/application/orchestration/structural_playbook.rs`: experience-prior artifact assembly

Locate them with:

```bash
rg -n 'build_structural_validation_summary_value|build_path_ranker_summary_value|structural_validation_summary|path_ranker_summary|structural_delayed_reward_replay_validation|structural_source_reliability_em_diagnostics' \
  src/application/orchestration/workflow_status.rs \
  src/application/orchestration/structural_playbook.rs \
  src/belief_core/source_reliability.rs
```

Minimum verification for this lane:

```bash
cargo check
cargo test delayed_reward_replay_validation_scores_future_resolution_horizons
cargo test source_reliability_em_readiness_requires_multi_source_overlap
cargo test test_structural_source_reliability_em_holdout_prefers_chronological_split
```

## Later Only If Still Needed

### Workstream 3: Broader Runtime Closure

**Objective:** close remaining downstream runtime-consumer gaps only after Workstream 1, Workstream 2, and Workstream 4 stop being the main blocker.

- [ ] Decide the remaining downstream consumer closure boundary for structural path-ranking runtime beyond the current direct-model and scoring-service contract.
- [ ] Make artifact-backed behavior versus sample / placeholder behavior explicit at every remaining downstream consumer boundary.
- [ ] Do not expand this lane before Workstream 1, Workstream 2, and Workstream 4 unless a concrete failing consumer proves it is the current blocker.

### Deeper Model Work

- [ ] Land a deeper learned or contextual target-policy probability model beyond the current bucket posterior.
- [ ] Land a fuller elapsed-time competing-risk delayed-reward model if the stronger validation lane proves the compact model is no longer sufficient.

## Execution Order

1. Finish Workstream 1 owner extraction.
2. Land Workstream 2 on top of that extracted core.
3. Deepen Workstream 4 validation.
4. Only then reopen broader Workstream 3 runtime closure if it still blocks real usage.
5. After those land, run fake-real operator / contributor shakedown and fix the resulting bugs before cleanup-only work.

## Verification Gate For Every Slice

- Required: `cargo check`
- Required: targeted tests for the touched owner files or surfaces
- Required: if a CLI or status contract changes, verify the real surface, not just a helper
- Required: update this same markdown with the landed slice and the remaining gap
- Not sufficient: static inspection only
- Not sufficient: formatting-only diffs
- Not sufficient: green helper tests if the real CLI or surface contract is still unverified

## Blocked

- None currently.
