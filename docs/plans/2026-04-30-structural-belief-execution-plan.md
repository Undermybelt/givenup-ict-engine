# Structural Belief Execution Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** stabilize canonical market-structure anchors, land the literature artifacts as repo truth, and then execute structural belief learning in the order required for `BBN -> structural prior/posterior -> CatBoost path ranking`.

**Architecture:** keep the public `node -> branch -> scenario -> path` contract and the existing zero-config / opt-in-profile boundary, but stop letting downstream workflow phases overwrite canonical market-structure lineage. Upgrade the current heuristic bootstrap into principled belief learning in three layers: evidence math, structural state transition math, and final path-ranking calibration.

**Tech Stack:** Rust, `serde_json`, existing `workflow-status` / `update` / `analyze` / `factor-research` / `factor-backtest` pipelines, persisted `LearningState.structural_prior_state`, repo docs under `docs/`.

---

## Current State

Already true in repo:
- structural consumer contract exists for `node / branch / scenario / path`
- `structural-feedback-v1` can round-trip through `update --feedback-file`
- `FeedbackRecord`, `UpdateRunRecord`, and `WorkflowSnapshot.latest_update` carry structural lineage
- `LearningState.structural_prior_state` exists and is fed by:
  - live structural feedback
  - analyze
  - research
  - backtest
  - mutation
  - artifact validation
- offline prior seeding already has source weighting and quality calibration

Current blocker:
- canonical market-structure anchor is not stable across downstream runs
- `research` / `backtest` surfaces can still leak workflow-phase or support-reason labels into structural lineage
- this blocks trustworthy `node` learning and pollutes the sample pool that should feed `BBN` and later `CatBoost`

Repo source-of-truth inputs for this plan:
- [2026-04-29-structural-playbook-belief-architecture-plan.md](/Users/thrill3r/projects-ict-engine/ict-engine/docs/plans/2026-04-29-structural-playbook-belief-architecture-plan.md:1)
- [2026-04-30-structural-belief-literature-ingestion-plan.md](/Users/thrill3r/projects-ict-engine/ict-engine/docs/plans/2026-04-30-structural-belief-literature-ingestion-plan.md:1)
- [structural-belief-learning-literature.md](/Users/thrill3r/projects-ict-engine/ict-engine/docs/structural-belief-learning-literature.md:1)
- [structural-belief-learning-repo-map.md](/Users/thrill3r/projects-ict-engine/ict-engine/docs/structural-belief-learning-repo-map.md:1)
- [docs/paper-code/structural_belief_learning/README.md](/Users/thrill3r/projects-ict-engine/ict-engine/docs/paper-code/structural_belief_learning/README.md:1)
- [docs/paper-code/bayesian_nonparametric_hidden_semi_markov_models/README.md](/Users/thrill3r/projects-ict-engine/ict-engine/docs/paper-code/bayesian_nonparametric_hidden_semi_markov_models/README.md:1)
- [docs/paper-code/self_calibrating_conformal_prediction/README.md](/Users/thrill3r/projects-ict-engine/ict-engine/docs/paper-code/self_calibrating_conformal_prediction/README.md:1)

## Acceptance Gates

The plan is only considered complete when all of these are true:

1. `workflow-status --phase structural-node` returns canonical node families and labels that describe market structure, not workflow phase or support-reason leakage.
2. Downstream `research` / `backtest` / `update` runs can add evidence without mutating the analyze-time canonical node anchor.
3. Literature docs and paper-code readmes are committed as repo truth.
4. Live feedback posterior updates use explicit pseudo-count logic instead of only heuristic score blending.
5. Offline evidence seeding uses explicit tempered source contribution logic instead of only ad hoc support mixing.
6. `structural_prior_state` carries enough state to support duration and transition learning.
7. CatBoost path ranking is designed as a consumer of structural candidates, not a generator of hidden structure.

## File Map

Primary code surfaces for execution:
- Modify: `src/application/orchestration/structural_playbook.rs`
- Modify: `src/application/orchestration/workflow_status.rs`
- Modify: `src/main.rs`
- Modify: `src/state/types.rs`
- Modify: `src/factors/weight_updater.rs`
- Modify: `src/analyze_shared.rs`
- Modify: `src/factor_research_runtime.rs`
- Modify: `src/factor_backtest_runtime.rs`

Primary doc surfaces:
- Add/commit: `docs/plans/2026-04-30-structural-belief-literature-ingestion-plan.md`
- Add/commit: `docs/structural-belief-learning-literature.md`
- Add/commit: `docs/structural-belief-learning-repo-map.md`
- Add/commit: `docs/paper-code/structural_belief_learning/README.md`
- Add/commit: `docs/paper-code/bayesian_nonparametric_hidden_semi_markov_models/README.md`
- Add/commit: `docs/paper-code/self_calibrating_conformal_prediction/README.md`

Tests likely touched:
- `src/application/orchestration/workflow_status.rs` unit tests
- `src/main.rs` workflow snapshot / integration tests
- `src/state/types.rs` structural prior learning tests
- targeted command/integration tests around `analyze`, `factor-research`, `factor-backtest`, `update`

## Phases

### Phase 0: Repo Truth First

Purpose:
- turn the literature and repo-map docs into committed inputs before more code drift

Outcome:
- planning docs become canonical repo truth
- execution order is frozen before more implementation

### Phase 1: Structural Anchor Repair

Purpose:
- preserve an analyze-time canonical market-structure anchor
- prevent `research` / `backtest` / `support_reason` strings from becoming structural node identity

Outcome:
- `node_id`, `branch_id`, `scenario_id`, `path_id` remain structurally meaningful
- downstream runs enrich evidence, not ontology

### Phase 2: Principled Evidence Math

Purpose:
- replace remaining heuristic mixing with explicit formulas already selected in the literature docs

Outcome:
- offline evidence enters via tempered source contribution
- live feedback enters via explicit fractional pseudo-count posterior updates

### Phase 3: Structural State Math

Purpose:
- enrich `structural_prior_state` from “smoothed score bucket” into a real structural-state carrier

Outcome:
- node duration prior
- branch transition prior
- source-panel snapshots before canonical merge

### Phase 4: BBN Update Upgrade

Purpose:
- move node/branch posterior updates toward discounted dynamic Bayesian transition logic

Outcome:
- branch posterior updates stop being display-only summaries
- `BBN` becomes the actual structural transition engine

### Phase 5: CatBoost Target Design

Purpose:
- define the delayed-feedback, partial-compliance, calibrated path-ranking target after the structural state is trustworthy

Outcome:
- CatBoost consumes declared path candidates
- calibrated path probability and lower bound become gating surfaces

## Ordered TODO

### P0: Planning and Repo Truth

- [ ] Commit the literature ingestion artifacts listed above so execution references versioned docs instead of chat memory.
- [ ] Keep this execution plan and the older architecture plan aligned; if the scope changes, update both in the same slice.
- [ ] Freeze the execution order to `anchor -> evidence math -> structural state math -> BBN upgrade -> CatBoost target`.

### P1: Canonical Structural Anchor

- [ ] Audit `workflow_phase_snapshot_from_research_run(...)` in `src/main.rs` so downstream workflow snapshots carry evidence and execution metadata without redefining structural ontology.
- [ ] Audit `workflow_phase_snapshot_from_backtest_run(...)` in `src/main.rs` with the same rule.
- [ ] Refactor `build_structural_node_artifact_with_prior_state(...)` in `src/application/orchestration/structural_playbook.rs` so node family and label are chosen from canonical market-structure anchors first, not generic workflow phase or support strings.
- [ ] Add a persisted analyze-time structural anchor field if the current snapshot surface cannot preserve canonical structure across later phases.
- [ ] Add regression tests for real-world dirty inputs such as:
  - `posterior_active_regime = research_iteration`
  - `posterior_probabilities = { fallback, research_iteration }`
  - `blocking_truth.reason = market_policy=...`
- [ ] Add a smoke path that proves `workflow-status --phase structural-playbook --agent` returns canonical market-structure lineage after analyze + research + backtest.

### P2: Live Feedback Posterior Update

- [ ] Replace score-only path posterior refresh with explicit Beta-Binomial-style fractional pseudo-count updates in `src/state/types.rs` and `src/factors/weight_updater.rs`.
- [ ] Split executed, not-followed, abandoned, invalidated, and delayed outcomes into explicit update semantics instead of one blended credit signal.
- [ ] Preserve zero-config CLI behavior: all new math must run behind existing flows, not new required flags.
- [ ] Add tests for:
  - followed profitable path
  - followed invalidated path
  - not-followed recommendation
  - delayed outcome that resolves later

### P3: Offline Evidence Tempering

- [ ] Replace remaining heuristic support blending in `src/analyze_shared.rs`, `src/factor_research_runtime.rs`, and `src/factor_backtest_runtime.rs` with explicit tempered source contribution rules from the literature repo-map.
- [ ] Carry source-panel snapshots into `structural_prior_state` before canonical merge so offline evidence is inspectable instead of irreversibly blended.
- [ ] Keep the current source ordering, but make the effect formula explicit and testable.
- [ ] Add tests that prove:
  - stronger source + good quality increases prior mass more than weaker source
  - break penalties and poor coverage reduce effective contribution
  - validation regression can reduce contribution rather than only cap it

### P4: Structural Prior State Upgrade

- [ ] Extend `LearningState.structural_prior_state` in `src/state/types.rs` with explicit node duration and branch transition fields suggested by the repo map.
- [ ] Separate node prior mass from branch/path prior mass so one noisy path does not mutate the whole node too aggressively.
- [ ] Store last offline seed snapshots and per-source summaries for later audit and recalibration.
- [ ] Add tests that prove duration and transition state survives persistence and is reused by structural orchestration.

### P5: BBN Node/Branch Posterior Update

- [ ] Identify the existing `BBN` update surfaces under `src/domain/belief/*` and `src/application/belief/*` that should consume discounted transition counts.
- [ ] Introduce discounted transition-count updates for branch posterior maintenance.
- [ ] Make sure `workflow-status` reads real node/branch posterior state from `BBN` outputs rather than assembling a parallel view-only belief model.
- [ ] Add tests that prove repeated evidence can strengthen one branch posterior without collapsing unrelated nodes.

### P6: CatBoost Path Ranking Target

- [ ] Define the training/eval target surface for path ranking only after P1-P5 are stable.
- [ ] Add explicit fields for:
  - `raw_path_score`
  - `calibrated_path_prob`
  - `path_prob_lower_bound`
  - `pending_reward_state`
  - `propensity_estimate`
  - `regime_calibration_bucket`
- [ ] Keep CatBoost inside the declared structural candidate set; it must not invent hidden nodes or branches.
- [ ] Add a design-only doc slice before implementation if the target math exceeds one coding session.

## Immediate Execution Backlog

Do these first, in order:

1. Commit the untracked literature and paper-code docs.
2. Fix the canonical structural anchor leak.
3. Add regression smoke coverage for analyze -> research -> backtest -> structural-playbook.
4. Replace live path posterior updates with explicit pseudo-count math.
5. Replace offline source blending with explicit tempered contribution math.
6. Extend `structural_prior_state` with duration and transition state.
7. Only then start CatBoost target design.

## Out of Scope For The Next Execution Slice

- no new provider defaults
- no new required CLI flags
- no consumer-visible ontology expansion beyond current `node / branch / scenario / path`
- no full paper reproduction bundles
- no CatBoost training changes before the structural anchor and posterior math are stable

## Verification Checklist For Future Execution

- [ ] `cargo test --lib workflow_status_phase_structural_ -- --nocapture`
- [ ] `cargo test --bin ict-engine test_analyze_command_persists_analyze_run -- --nocapture`
- [ ] `cargo test --bin ict-engine test_run_factor_research_persists_rankings_and_run_record -- --nocapture`
- [ ] `cargo test --bin ict-engine test_run_factor_backtest_persists_backtest_run_and_agent_bundle -- --nocapture`
- [ ] `cargo test --bin ict-engine test_update_command_accepts_structural_feedback_file -- --nocapture`
- [ ] `cargo clippy --all-targets -- -D warnings`
- [ ] one real smoke run proving canonical structural lineage survives downstream phases

## Handoff

Plan intent:
- stop surface drift
- repair the structural anchor first
- then execute the literature-backed belief upgrade in the order already documented

Execution should not start until the operator explicitly chooses the next slice from the ordered backlog above.
