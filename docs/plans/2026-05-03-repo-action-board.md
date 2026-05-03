# Repo Action Board From 20260501repo

> **For implementers:** use this as the execution board derived from `docs/plans/20260501repo.md` and the 2026-05-03 repo audit. Keep changes low-pollution, preserve the public `node -> branch -> scenario -> path` contract, and avoid introducing new repo-default stance into consumer surfaces.

**Goal:** turn the current structural-belief / transition / path-ranking work from “partly landed research plan” into an executable repo closure board that clearly separates what is done, what is still missing, and what should be done next.

**Architecture:** keep docs as repo truth, then execute in three layers: first reduce structural debt by extracting the belief core from oversized files, then replace heuristic temporal transition math with a more principled maintained filter, then connect the external path-ranking artifact boundary to a real runtime consumer.

**Tech Stack:** Rust, existing `LearningState.structural_prior_state`, `workflow-status`, `structural-playbook`, policy-training export surfaces, repo docs under `docs/plans/`.

---

## Current State

Repo truth already established:

- `docs/plans/20260501repo.md` now contains the research mapping plus a 2026-05-03 audit section.
- `structural-temporal-summary`, `structural-experience-priors`, and `policy-training-status` already exist as real surfaces in code.
- `src/state/types.rs` already persists:
  - duration priors
  - BOCPD-style temporal fields
  - source reliability EM summaries
  - target-policy context posteriors
- `src/application/orchestration/structural_playbook.rs` and `src/application/orchestration/workflow_status.rs` already expose the compact structural-learning status surfaces.
- the external trainer boundary for structural path ranking already exists as an opt-in artifact registration and status surface.

Current blocker shape:

- the repo is no longer blocked on “whether the structural learning direction exists”
- it is blocked on “the core math and runtime wiring are still fragmented, heuristic, or docs-only”
- the highest-value remaining work is architectural closure, not more surface proliferation

Primary source docs:

- [20260501repo.md](/Users/thrill3r/projects-ict-engine/ict-engine/docs/plans/20260501repo.md:1)
- [2026-04-30-structural-belief-execution-plan.md](/Users/thrill3r/projects-ict-engine/ict-engine/docs/plans/2026-04-30-structural-belief-execution-plan.md:1)

## Current Todo Board

### Done

- [x] Structural learning research and repo-target mapping are documented in repo.
- [x] Compact structural-learning status surfaces exist and are reachable from workflow/playbook code paths.
- [x] `LearningState.structural_prior_state` carries persisted state for duration, temporal posterior, source reliability, and target-policy posterior summaries.
- [x] The structural path-ranking export/status path exists, including trainer manifest checks and explicit external artifact registration.
- [x] A repo-local audit now states which parts of the long plan are real, partial, or still missing.
- [x] Structural path-ranking now has an opt-in runtime reuse contract for externally scored rows: zero-config default stays unchanged, while users can explicitly enable `candidate_set_only` or `prefer_history` reuse from `policy_training` state.
- [x] Registered trainer artifacts can now act as a direct runtime score source for structural path-ranking consumer surfaces when runtime reuse is explicitly enabled, for both local file-backed and remote scored-row feeds.
- [x] Workstream 1 has started with a concrete owner extraction: path-ranker runtime selection, artifact-row loading, data contracts, calibration math, and row IO/render helpers now live under `src/belief_core/ranking_label.rs`, and shared structural contracts for path / node / branch / scenario / playbook / history / feedback-template have started moving into `src/belief_core/structural_state.rs`.
- [x] Workstream 1 now also has source-reliability / experience-prior shared contracts starting to move into `src/belief_core/source_reliability.rs`.
- [x] Workstream 2 has also started at the owner level: node/branch transition posterior adjustment plus duration/branch blend helpers now live under `src/belief_core/regime_filter.rs`, with `application/belief/structural_temporal_adjustment.rs` reduced toward a thinner compatibility shell.

### Next

- [ ] Extract the belief core out of the oversized files so the core learning math stops living inside `src/state/types.rs`, `src/application/orchestration/structural_playbook.rs`, `src/application/orchestration/workflow_status.rs`, and `src/main.rs`.
  - started: path-ranker runtime owner, contracts, calibration helpers, row IO extraction into `src/belief_core/ranking_label.rs`, shared structural contracts into `src/belief_core/structural_state.rs`, and source-reliability / experience-prior contracts into `src/belief_core/source_reliability.rs`
- [ ] Replace the current heuristic transition/break mixing with a maintained, emission-aware regime transition core instead of only snapshot-time posterior reweighting.
  - started: transition posterior and blend-helper owner extraction into `src/belief_core/regime_filter.rs`
- [ ] Promote the new opt-in runtime path from scored-row feed consumption into model-native scoring for the structural path-ranker.
- [ ] Add stronger verification lanes for source reliability and delayed reward handling so the repo stops relying only on in-ledger compact calibration summaries.

### Not Yet

- [ ] belief-core module split proposed in `20260501repo.md`:
  - `structural_state.rs`
  - `beta_dirichlet_update.rs`
  - `source_reliability.rs`
  - `regime_filter.rs`
  - `changepoint_gate.rs`
  - `ranking_label.rs`
- [ ] production-grade `regime_filter` with maintained transition logic and explicit emission-conditioned updates
- [ ] production-grade `changepoint_gate` instead of the current fixed-weight BOCPD-style heuristic blend
- [ ] model-native runtime consumption of the structural path-ranking trainer artifact beyond scored-row feed loading
- [ ] deeper learned/contextual target-policy probability model beyond the current `symbol:regime:direction` bucket posterior
- [ ] out-of-sample / replay-grade source reliability validation beyond fixed-iteration leave-source-out summaries
- [ ] full elapsed-time competing-risk delayed-reward censoring model rather than only compact aggregate hazard/incidence summaries

## Ordered Work Items

### Workstream 1: Belief-Core Extraction

**Objective:** reduce structural debt and stop hiding core math in giant mixed-purpose files.

**Primary files:**

- Modify: `src/state/types.rs`
- Modify: `src/application/orchestration/structural_playbook.rs`
- Modify: `src/application/orchestration/workflow_status.rs`
- Modify: `src/main.rs`
- Create: `src/belief_core/mod.rs`
- Create: `src/belief_core/structural_state.rs`
- Create: `src/belief_core/beta_dirichlet_update.rs`
- Create: `src/belief_core/source_reliability.rs`
- Create: `src/belief_core/regime_filter.rs`
- Create: `src/belief_core/changepoint_gate.rs`
- Create: `src/belief_core/ranking_label.rs`

**Acceptance:**

- structural learning math is no longer primarily implemented in `src/state/types.rs`
- orchestration files call extracted helpers instead of duplicating math/surface glue
- public output stays stable while internal ownership becomes clearer

### Workstream 2: Transition And Changepoint Closure

**Objective:** replace the current heuristic temporal transition blend with a more principled maintained update core.

**Primary files:**

- Modify: `src/belief_core/regime_filter.rs`
- Modify: `src/belief_core/changepoint_gate.rs`
- Modify: `src/application/belief/structural_temporal_adjustment.rs`
- Modify: `src/state/types.rs`

**Current gap to close:**

- current break probability still depends on hand-tuned fixed mixing weights
- current node posterior adjustment still mostly consumes precomputed transition state instead of running a unified maintained filter

**Acceptance:**

- transition math has one clear owner
- emission/likelihood-conditioned update logic is explicit in code
- snapshot-time reweighting becomes a consumer of maintained filter state, not the main engine

### Workstream 3: Path-Ranker Runtime Wiring

**Objective:** make the external structural path-ranking artifact usable at runtime instead of only being registered and reported.

**Primary files:**

- Modify: `src/application/entry_models/training_export.rs`
- Modify: `src/application/orchestration/policy_engine.rs`
- Modify: `src/application/orchestration/ensemble_vote.rs`
- Modify: `src/main.rs`

**Current gap to close:**

- trainer artifact readiness is checked
- artifact URI presence is reported
- opt-in scored-row reuse is now available for current consumer surfaces
- local artifact-backed scored-row loading now works
- remote scored-row feed loading now works
- model-native inference is still missing

**Acceptance:**

- Rust can either load a validated external artifact directly or call a declared external scoring service
- runtime clearly distinguishes placeholder/sample behavior from real artifact-backed behavior
- workflow/status surfaces expose readiness without leaking user-specific artifact URIs

### Workstream 4: Validation Hardening

**Objective:** close the remaining “later slice” items that are currently only compact diagnostics.

**Primary files:**

- Modify: `src/state/types.rs`
- Modify: `src/application/orchestration/structural_playbook.rs`
- Modify: `src/application/orchestration/workflow_status.rs`
- Add/modify tests around structural replay and calibration surfaces

**Acceptance:**

- source reliability has a replay or holdout-style validation path
- delayed reward handling has a clearer time-to-resolution validation lane
- target-policy context learning has a documented upgrade path from bucket posterior to learned contextual model

## Execution Order

1. Finish Workstream 1 first.
2. Then land Workstream 2 on top of the extracted core.
3. Then land Workstream 3 so runtime can consume real path-ranking artifacts.
4. Only after that spend time on Workstream 4 deeper validation and model upgrades.

## Completion Standard

This action board is only complete when all of these are true:

- `Done / Next / Not Yet` can be updated without ambiguity from repo evidence alone
- belief-core ownership is no longer concentrated in the current oversized files
- transition math is maintained in one principled core instead of heuristic glue spread across state/orchestration layers
- structural path ranking has a real runtime consumer path, not only export + status + registration
- remaining “future work” items are either executed or explicitly broken into a follow-up plan
