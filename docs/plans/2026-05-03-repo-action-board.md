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
- [x] Workstream 1 has started with a concrete owner extraction: path-ranker runtime selection, artifact-row loading, data contracts, calibration math, and row IO/render helpers now live under `src/belief_core/ranking_label.rs`, and shared structural contracts for path / node / branch / scenario / playbook / history / feedback-template / feedback-submission have started moving into `src/belief_core/structural_state.rs`.
- [x] Workstream 1 now also has source-reliability / experience-prior shared contracts and panel/reliability / target-policy / delayed-reward accessor helper ownership starting to move into `src/belief_core/source_reliability.rs`.
- [x] Workstream 1 now also has shared Beta / pseudo-count update ownership starting to move into `src/belief_core/beta_dirichlet_update.rs`, with structural power-prior mass assembly, target-policy context posterior updates, source-reliability updates, transition support means, and path-ranking Beta summaries beginning to reuse that helper layer instead of open-coding the same math in `src/state/types.rs`.
- [x] Workstream 2 has also started at the owner level: node/branch transition posterior adjustment plus duration/branch blend helpers, temporal accessor math, and `structural-temporal-summary` assembly now live under `src/belief_core/regime_filter.rs`, with `application/belief/structural_temporal_adjustment.rs` reduced toward a thinner compatibility shell.
- [x] Workstream 2 now also has maintained transition-posterior refresh ownership beginning to move into `src/belief_core/regime_filter.rs`: the node/branch transition prior normalization, outcome-support recompute, posterior multiplier recompute, and normalized posterior rebuild no longer have to stay open-coded inside `rebuild_structural_sequence_priors(...)`.
- [x] Workstream 2 now also has explicit emission-conditioned transition support helpers in `src/belief_core/regime_filter.rs`, so maintained node/branch refresh no longer depends on a fixed prior/outcome scalar blend.
- [x] Workstream 2 now also has posterior-style emission-aware break and sequence-break updates in `src/belief_core/changepoint_gate.rs`, so BOCPD-derived break maintenance no longer depends only on fixed linear mixing weights.
- [x] Workstream 2 now also has BOCPD / sequence-break helper ownership starting to move into `src/belief_core/changepoint_gate.rs`, including discounted node-duration prior / temporal-posterior rebuild logic.
- [x] Workstream 3 now has two real opt-in runtime consumer paths for structural path ranking: a direct weighted-feature model artifact path and a declared external scoring-service path, both hanging off the existing `policy_training` registration/runtime-selection contract without changing the zero-config default.
- [x] Workstream 4 has started with a concrete source-reliability validation lane: EM diagnostics/readiness now carry a holdout-style train/eval summary in addition to the existing same-ledger leave-source-out calibration summary.
- [x] Workstream 4 now also has a concrete delayed-reward validation lane starting to surface through path experience-prior data: chronological train/eval replay summary for resolution and 1h/4h/24h horizon Brier checks now exists alongside the aggregate delayed-reward hazard/incidence metrics.
- [x] Workstream 1 now also has more of the experience-prior/path-validation accessor surface routed through `src/belief_core/source_reliability.rs`, with duplicate target-policy / SNIPS / delayed-reward helper logic removed from `src/application/orchestration/structural_playbook.rs`.
- [x] Workstream 1 now also has path experience-prior runtime metric assembly routed through `src/belief_core/source_reliability.rs`, so `structural_playbook.rs` no longer has to spell out the full path-level target-policy / delayed-reward metric block inline.
- [x] Workstream 1 now also has branch experience-prior runtime metric assembly routed through the same shared helper in `src/belief_core/source_reliability.rs`, further shrinking `structural_playbook.rs`.
- [x] Workstream 1 now also has scenario experience-prior runtime metric assembly routed through that same shared helper, further reducing duplicate field-by-field metric wiring in `structural_playbook.rs`.
- [x] Workstream 1 now also has node experience-prior runtime metric assembly routing through that same shared helper for the non-duration metrics, leaving only node-specific temporal/duration fields locally owned in `structural_playbook.rs`.
- [x] Workstream 1 now also has `workflow-status` structural branch/scenario/path/feedback-template phase rendering reusing the shared structural playbook bundle instead of rebuilding those subtrees separately per case.
- [x] Workstream 1 now also has `workflow-status` structural history phase rendering reusing the same shared playbook bundle/history artifacts instead of rebuilding those history subtrees independently per case.
- [x] Workstream 1 now also has `workflow-status` structural node and path-outcome phases reusing the shared playbook bundle instead of rebuilding those slices independently.
- [x] Workstream 1 now also has policy-training / structural path-ranker CLI dispatch moved out of the `main.rs` match-arm noise into a focused bin-side shell module, reducing entrypoint glue without changing the public command surface.
- [x] Workstream 1 now also has `workflow-status` / `pre-bayes-status` thin shell dispatch moved out of the `main.rs` match-arm body into a focused bin-side status command module, again without changing the public CLI contract.
- [x] Workstream 1 now also has `provider-status` / `artifact-status` thin shell dispatch moved into that same bin-side status command module, further reducing entrypoint glue in `main.rs`.
- [x] Workstream 1 now also has `pre-bayes-diff` / `artifact-diff` / `artifact-lineage` thin shell dispatch moved into the same bin-side status command module, so the related `main.rs` match arms are now thin command routing only.
- [x] Workstream 1 now also has release-closure CLI dispatch for `research-verdict` / `evidence-quality-breakdown` moved out of the `main.rs` match-arm body into a focused bin-side shell module.
- [x] Workstream 1 now also has `factor-mutation-status` / `factor-autoresearch-status` thin shell dispatch moved into that same bin-side status command module.
- [x] Workstream 1 now also has the thin `auto_quant` management/control wrappers (`status/bootstrap/update/adoption review/decision/seed evidence/promote canonical setup`) moved out of `main.rs` and into a focused bin-side command shell.
- [x] Workstream 1 now also has the remaining `auto_quant` batch/dispatch/import/ingest thin wrappers (`pda-unit`, `agent-material`, `results-import`, `prior-init`, `consume-live-signals`, `ingest-real-trades`) moved out of `main.rs` and into that same bin-side command shell.
- [x] Workstream 1 now also has `factor-backtest` / `factor-pipeline-debug` thin shell dispatch moved out of `main.rs` into a focused bin-side research/debug shell.
- [x] Workstream 1 now also has `factor-research` / `factor-autoresearch` bin-side shell dispatch moved out of the `main.rs` match-arm body, leaving the runtime closure logic owned by the dedicated research runtime module.
- [x] Workstream 1 now also has `clean-futures` / `futures-sop` / `market-data-harness` thin shell dispatch moved out of `main.rs` into a focused bin-side market-data shell.
- [x] Workstream 1 now also has `expansion-sop` thin shell dispatch moved into that same bin-side market-data shell, removing one of the last large wrapper-style match arms from `main.rs`.
- [x] Workstream 1 now also has `analyze-live` / `update` thin shell dispatch moved out of the `main.rs` match-arm body and into their existing bin-side command modules.
- [x] Workstream 1 now also has the `train` runtime shell moved out of `main.rs` into a focused bin-side module, taking the multi-timeframe HMM training path with it.

### Next

- [ ] Extract the belief core out of the oversized files so the core learning math stops living inside `src/state/types.rs`, `src/application/orchestration/structural_playbook.rs`, `src/application/orchestration/workflow_status.rs`, and `src/main.rs`.
  - started: path-ranker runtime owner, contracts, calibration helpers, row IO extraction into `src/belief_core/ranking_label.rs`, shared structural contracts into `src/belief_core/structural_state.rs`, source-reliability / experience-prior contracts plus panel/reliability / target-policy / delayed-reward helper ownership into `src/belief_core/source_reliability.rs`, and shared Beta / pseudo-count update helpers into `src/belief_core/beta_dirichlet_update.rs`
  - latest: `structural_playbook.rs` no longer needs its own duplicate target-policy / SNIPS / delayed-reward accessor block for experience-prior/path surfaces
  - latest: path experience-prior runtime metric assembly now also routes through a shared `belief_core/source_reliability.rs` helper instead of an inline field-by-field block
  - latest: branch experience-prior runtime metric assembly now routes through that same shared helper
  - latest: scenario experience-prior runtime metric assembly now routes through that same shared helper
  - latest: node experience-prior runtime metrics now also route through that same shared helper, except for node-only duration/temporal fields
  - latest: `workflow_status.rs` structural branch/scenario/path/feedback-template phase cases now reuse the shared playbook bundle instead of rebuilding each subtree independently
  - latest: `workflow_status.rs` structural history phase cases now reuse the shared playbook bundle/history artifacts as well
  - latest: `workflow_status.rs` structural node and path-outcome phases now reuse that same shared bundle
  - latest: `main.rs` no longer owns the direct policy-training / structural path-ranker wrapper logic for those command arms
  - latest: `main.rs` no longer owns the direct `workflow-status` / `pre-bayes-status` thin shell wrapper logic either
  - latest: `main.rs` no longer owns the direct `provider-status` / `artifact-status` thin shell wrapper logic either
  - latest: `main.rs` no longer owns the direct `pre-bayes-diff` / `artifact-diff` / `artifact-lineage` thin shell wrapper logic either
  - latest: `main.rs` no longer owns the direct `research-verdict` / `evidence-quality-breakdown` thin shell wrapper logic either
  - latest: `main.rs` no longer owns the direct `factor-mutation-status` / `factor-autoresearch-status` thin shell wrapper logic either
  - latest: `main.rs` no longer owns the direct `auto_quant` management/control thin shell wrapper logic for that command cluster either
  - latest: `main.rs` no longer owns the direct `auto_quant` batch/dispatch/import/ingest thin shell wrapper logic for the rest of that command cluster either
  - latest: `main.rs` no longer owns the direct `factor-backtest` / `factor-pipeline-debug` thin shell wrapper logic either
  - latest: `main.rs` no longer owns the direct `factor-research` / `factor-autoresearch` bin-side shell wrapper logic either
  - latest: `main.rs` no longer owns the direct `clean-futures` / `futures-sop` / `market-data-harness` thin shell wrapper logic either
  - latest: `main.rs` no longer owns the direct `expansion-sop` thin shell wrapper logic either
  - latest: `main.rs` no longer owns the direct `analyze-live` / `update` thin shell wrapper logic either
  - latest: `main.rs` no longer owns the direct `train` runtime shell either
- [ ] Replace the current heuristic transition/break mixing with a maintained, emission-aware regime transition core instead of only snapshot-time posterior reweighting.
  - started: transition posterior, blend-helper, temporal accessor, temporal-summary builder extraction, maintained node/branch transition posterior refresh, and explicit emission-conditioned support helpers into `src/belief_core/regime_filter.rs`
- [ ] Replace the current heuristic temporal break logic with a clearer `changepoint_gate` owner instead of keeping BOCPD helpers inside `src/state/types.rs`.
  - started: BOCPD / sequence-break helper and duration-prior rebuild owner extraction into `src/belief_core/changepoint_gate.rs`
  - latest: posterior-style emission-aware break and sequence-break updates now live there instead of only fixed linear blends
- [x] Promote the new opt-in runtime path from scored-row feed consumption into model-native scoring for the structural path-ranker.
  - landed: registered trainer artifacts can now either score the current candidate-set rows directly through an opt-in weighted-feature model artifact family or call an explicit external row-scoring service, while existing scored-row feed reuse remains available and zero-config default behavior stays unchanged
- [ ] Add stronger verification lanes for source reliability and delayed reward handling so the repo stops relying only on in-ledger compact calibration summaries.
  - started: source reliability EM diagnostics now expose a holdout-style train/eval summary beside the older same-ledger leave-source-out calibration summary
  - started: delayed reward path experience-prior data now has a chronological replay summary for resolution and 1h/4h/24h horizon validation

### Not Yet

- [ ] belief-core module split proposed in `20260501repo.md`:
  - `structural_state.rs`
  - `source_reliability.rs`
  - `regime_filter.rs`
  - `changepoint_gate.rs`
  - `ranking_label.rs`
- [ ] production-grade `regime_filter` with maintained transition logic and explicit emission-conditioned updates
  - partial: maintained transition refresh now uses explicit emission-conditioned support helpers, but the overall regime filter is still simpler than a fuller state-space/HMM-grade transition engine
- [ ] production-grade `changepoint_gate` instead of the current fixed-weight BOCPD-style heuristic blend
  - partial: BOCPD break and sequence-break maintenance now use posterior-style emission updates, but the overall gate is still simpler than a fuller competing-hypothesis changepoint engine
- [x] model-native runtime consumption of the structural path-ranking trainer artifact beyond scored-row feed loading
  - current implementation: direct weighted-feature model artifact loading and declared external scoring service calls are both live
  - remaining gap: broader artifact-family coverage beyond the current direct weighted-feature model path and row-scoring service contract
- [ ] deeper learned/contextual target-policy probability model beyond the current `symbol:regime:direction` bucket posterior
- [ ] out-of-sample / replay-grade source reliability validation beyond fixed-iteration leave-source-out summaries
  - partial: an on-demand holdout-style EM summary now exists; larger-panel and true chronological replay validation are still missing
- [ ] full elapsed-time competing-risk delayed-reward censoring model rather than only compact aggregate hazard/incidence summaries
  - partial: chronological replay validation for delayed reward resolution has started, but the underlying model is still the compact aggregate hazard/incidence family rather than a fuller competing-risk censoring model

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
- direct-model inference and declared row-scoring service calls are both available; broader model/service runtime coverage is still missing

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
