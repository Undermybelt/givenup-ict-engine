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
- the highest-value remaining work is belief-core / transition ownership closure plus validation hardening, not more surface proliferation or provider-profile polish

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
- [x] The opt-in provider-profile hot-plug lane is now materially closed for the current public workflow surfaces: `provider-status`, `provider-status --compact`, `workflow-status --agent|--human`, and agent bootstrap all preserve zero-config default behavior while exposing explicit `--profile` selection, token-friendlier selectors/provenance, direct selected-profile summary fields, and profile-scoped provider guidance only when the caller opts in.
- [x] `workflow-status` now exposes low-token structural validation and ranker-runtime summaries directly through `structural_validation_summary`, `path_ranker_summary`, `--phase structural-validation`, and `--phase structural-ranker-runtime`, so Workstream 4 readiness is no longer buried only inside deep structural payloads.
- [x] `workflow-status` ranker summaries now also expose runtime-enabled state plus applied/artifact/candidate/history match counts, so consumers can tell whether ranking is still baseline-only or is actually being driven by an opted-in registered artifact / model / service path without expanding the full structural bundle.
- [x] `policy-training-status` now also compresses the structural path-ranker runtime lane into explicit `runtime_source_kind` and `runtime_active_match_count` signals, and its summary line now states `runtime_mode`, `runtime_source`, and effective match count so training-side consumers can distinguish zero-config baseline from opted-in artifact/model/service/history reuse without re-parsing the full surface.
- [x] `policy-training-status` now also mirrors that structural path-ranker runtime lane at the top level through `structural_path_ranking_runtime_summary`, so token-limited consumers do not need to traverse the nested `structural_path_ranking_target` object just to answer “is runtime disabled, or is a chosen artifact/model/service actually being reused right now?”
- [x] `policy-training-status` now also exposes the same lane as a structured top-level object through `structural_path_ranking_runtime`, with explicit `enabled`, `ready`, `status`, `reuse_mode`, `source_kind`, `active_match_count`, and `model_family` fields; zero-config empty-state now reports a stable disabled contract instead of forcing consumers to infer it from missing nested state.
- [x] The zero-config empty-state contract on the training side is now explicit all the way down: when no structural path-ranking export exists yet, both the nested and top-level runtime summaries report `disabled` plus `runtime_source=none` / `runtime_matches=0` instead of leaving consumers to interpret empty strings.
- [x] `policy-training-status` now also exposes structural path-ranker validation as both a top-level summary string and a structured object, so token-limited consumers can read calibration / raw-scored-mature / production-validation readiness without traversing the full nested target-training status payload.
- [x] `policy-training-status --human` / `--compact` now work as true low-token aliases instead of JSON-only passthrough: in zero-config empty-state they emit the top-level status line plus the dedicated runtime and validation summary lines directly, which keeps the default JSON contract intact while giving contributors and agents a cheap read surface.
- [x] The human/agent analyze-output envelope now also forwards that structural path-ranker validation lane into the low-token executor summary area through `ranker_validation=...`, so downstream consumers can see calibration / production-validation readiness alongside the existing policy/runtime cues without a second status query.
- [x] That same analyze-output low-token surface now also forwards `structural_path_ranking_runtime_summary` through `ranker_runtime=...`, so downstream consumers can see both runtime reuse state and validation readiness in one place without separately querying `policy-training-status`.
- [x] `build_factor_research_output_payload(...)` now also forwards the top-level structural path-ranker runtime and validation summaries into the JSON payload itself, so non-human report consumers on the research path can reuse the same low-token runtime/validation contract without depending on the typed `WorkflowSnapshot` model carrying those fields.
- [x] The backtest/research command-entry layer now injects those same top-level structural path-ranker runtime and validation summaries into emitted structured payloads from the already-computed `policy-training-status` surface, so JSON/agent consumers on those paths no longer depend on typed `WorkflowSnapshot` carrying extra fields just to reuse the contract.
- [x] That payload-level contract now has direct bin-test coverage on both factor-backtest and factor-research payload builders, so the ranker runtime/validation summaries are verified on the real `src/main.rs` command/test harness rather than only through helper-level unit tests.
- [x] That command-entry injection layer is now directly unit-tested as a stable payload mutation boundary: the helper both inserts the two top-level ranker summary fields and preserves existing payload content, so this slice no longer depends on broad CLI/test-harness coverage to stay trustworthy.
- [x] The delayed-reward replay validation surfaces now expose observation counts for overall / 1h / 4h / 24h views in both JSON and low-token human/agent summary lines, so consumers can judge evidence size together with Brier scores instead of treating the score alone as sufficient.
- [x] The structural-validation JSON and human/agent summary surfaces now expose delayed-reward replay observation counts (`obs`, `obs_1h`, `obs_4h`, `obs_24h`) alongside the existing Brier metrics, so consumers can distinguish “good score with tiny evidence” from “good score with a real evaluation panel.”
- [x] The delayed-reward replay owner and surfaces now also expose the chronological train/eval boundary directly (`latest_training_recommended_at`, `first_evaluation_recommended_at`, `last_evaluation_recommended_at` / `train_until` + `eval_range`), so consumers can tell which slice of history actually produced the reported replay scores instead of treating them as timeless aggregates.
- [x] The source-reliability holdout/replay surfaces now also expose observation-coverage ratios (`holdout_cov`, `replay_cov`) alongside counts and scores, so consumers can see at a glance how close each validation lane is to its own minimum evidence threshold instead of reverse-engineering that from raw counts.
- [x] The sample/placeholder ensemble-policy lane now declares itself explicitly through `policy_runtime_sources` on the ensemble artifact, so artifact-level consumers no longer have to infer from vague executor labels whether they are still on placeholder/sample policy logic or a real loaded artifact-backed path.
- [x] The human/agent analyze-output envelope now forwards that artifact-level policy provenance into the executor summary lines through a compact `policy_runtime=...` line, so downstream consumers can see sample/placeholder vs artifact-backed policy context without parsing the full ensemble artifact blob.
- [x] `executor_summaries` themselves now carry `policy_source=...`, so even existing consumers that only read the legacy summary lines can distinguish placeholder/sample policy execution from loaded artifact-backed execution without any new parsing contract.
- [x] That `policy_source=...` executor signal is now executor-specific (`catboost_file:*`, `xgboost_file:*`) instead of only a generic engine-family label, so consumers can tell which leg of the weighted ensemble is still on placeholder/sample policy and which leg is reading a real artifact-backed policy file.
- [x] The executor-side policy provenance contract now distinguishes repo-shipped sample files from real artifact-backed policy files: `policy_source=*:*sample_file` is no longer mislabeled as `artifact`, so consumers can tell “sample file on disk” from “user/agent supplied real artifact” without guessing from filenames.
- [~] That provenance is not yet propagated through persisted `EnsembleVoteRecord` / workflow consumer surfaces. Attempting to force it through the persisted record immediately would currently touch a broad set of hand-written record initializers, so this slice intentionally stopped at the artifact boundary to avoid widening the worktree and creating structural debt.
- [x] Canonical `workflow-status` ensemble consumption now derives a low-token `policy_runtime_line` from the existing `executor_summaries`, so workflow consumers can still see sample/placeholder vs file-backed policy provenance without needing a persisted-schema expansion first.
- [~] That canonical workflow provenance is still asymmetric: the current ensemble surface and ensemble-history view can now derive `policy_runtime_line`, but persisted `EnsembleVoteRecord` still does not carry the same signal as a first-class field, so the remaining closure gap is now at the persisted-record boundary rather than the already-derived consumer lines.
- [x] Offline structural prior seeding now extends beyond `analyze` into adjacent lanes: `factor-research` writes `research_run_structural_prior_seed`, mutation evaluation writes `factor_mutation_structural_prior_seed`, and `factor-backtest` writes `backtest_run_structural_prior_seed`.

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
  - latest: source-reliability holdout now splits by `recommended_at`, and replay now surfaces an `expanding_window_recommended_at` summary instead of relying only on a single holdout slice
  - latest: top-level `workflow-status` human and agent surfaces now summarize those validation lanes directly instead of requiring deep playbook traversal
- [ ] Keep the repo on the post-profile lane: stop spending the next closure slice on provider-profile payload polish and switch back to Workstream 1 / Workstream 2 owner extraction plus Workstream 4 validation hardening.

### Not Yet

- [ ] belief-core owner split completion proposed in `20260501repo.md`
  - partial: `structural_state.rs`, `source_reliability.rs`, `regime_filter.rs`, `changepoint_gate.rs`, `ranking_label.rs`, and `beta_dirichlet_update.rs` all exist, but the remaining learning / EM / temporal owner logic still sits largely in `src/state/types.rs`, `src/application/orchestration/workflow_status.rs`, and `src/application/orchestration/structural_playbook.rs`
- [ ] production-grade `regime_filter` with maintained transition logic and explicit emission-conditioned updates
  - partial: maintained transition refresh now uses explicit emission-conditioned support helpers, but the overall regime filter is still simpler than a fuller state-space/HMM-grade transition engine
- [ ] production-grade `changepoint_gate` instead of the current fixed-weight BOCPD-style heuristic blend
  - partial: BOCPD break and sequence-break maintenance now use posterior-style emission updates, but the overall gate is still simpler than a fuller competing-hypothesis changepoint engine
- [ ] broader model/service runtime coverage for structural path-ranking beyond the current weighted-feature direct-model path and row-scoring service contract
- [ ] deeper learned/contextual target-policy probability model beyond the current `symbol:regime:direction` bucket posterior
- [ ] out-of-sample / replay-grade source reliability validation beyond fixed-iteration leave-source-out summaries
  - partial: holdout and replay summaries now exist, with chronological `recommended_at` splits, but larger-panel and stronger out-of-sample validation are still missing
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

## Architecture Judgment

Current verdict:

- directionally correct: keep modularizing the repo monolith; do not pivot this work into distributed services
- still materially bloated at the implementation layer: the current checkout still has very large ownership files, including `src/main.rs` (~16860 lines), `src/state/types.rs` (~10006), `src/application/orchestration/workflow_status.rs` (~9544), and `src/application/orchestration/structural_playbook.rs` (~5222)
- therefore architecture cleanup is real work, but owner closure and validation hardening are still higher-priority blockers than another cleanup-only pass

Planning rule for this board:

- do not spend the current closure slice chasing architecture purity ahead of feature completion
- use the remaining architecture work as a last-mile consolidation pass after functionality, testing, and fake-real usage shakedown have stabilized behavior
- when that final pass happens, prefer extraction and ownership cleanup inside the current repo/module boundaries, not service splitting
  - target shape: thinner command shells, thinner orchestration renderers, smaller `state/types.rs`, and clearer `belief_core` ownership
  - non-goal: turning `ict-engine` into a distributed multi-service system just because some files are large

## Execution Order

1. Finish Workstream 1 first.
2. Then land Workstream 2 on top of the extracted core.
3. Then land Workstream 3 so runtime can consume real path-ranking artifacts.
4. Then land Workstream 4 so deeper validation surfaces exist and the remaining model gaps are explicit.
5. After the remaining functional items are closed, run the full verification lane: targeted tests first, then whole-flow checks.
6. After tests are green, do a fake-real usage shakedown from actual operator/contributor perspectives instead of only code-path validation.
7. Fix the bugs, UX drift, contract leaks, and workflow friction found in that shakedown before spending time on cleanup.
8. Only then do the final architecture/bloat optimization pass, using the now-stable behavior and test coverage as guardrails.

## Completion Standard

This action board is only complete when all of these are true:

- `Done / Next / Not Yet` can be updated without ambiguity from repo evidence alone
- belief-core ownership is no longer concentrated in the current oversized files
- transition math is maintained in one principled core instead of heuristic glue spread across state/orchestration layers
- structural path ranking has a real runtime consumer path, not only export + status + registration
- remaining “future work” items are either executed or explicitly broken into a follow-up plan

## 2026-05-04 Code Verification Snapshot

Scope of this pass:

- static repo inspection against the current `src/` tree and the linked plan docs
- ownership / runtime / CLI-surface verification in code
- no full `cargo test` or runtime smoke replay in this pass

### Confirmed Done

- [x] Repo truth docs are real and present: `docs/plans/20260501repo.md` and `docs/plans/2026-04-30-structural-belief-execution-plan.md` both exist and already carry the structural-belief plan plus later repo-status notes.
- [x] `structural-temporal-summary`, `structural-experience-priors`, and `policy-training-status` are real code surfaces, not docs-only placeholders.
- [x] `LearningState.structural_prior_state` really persists duration priors, branch-transition priors, temporal posterior state, source-reliability EM summaries, and target-policy context posteriors.
- [x] The structural path-ranking export / status / registration path is real: trainer-manifest readiness, trainer-artifact readiness, runtime selection, and artifact registration all exist in code.
- [x] The opt-in runtime reuse contract is real: `candidate_set_only` and `prefer_history` are live runtime-selection modes and do not change the zero-config default.
- [x] Structural path-ranking runtime can already consume local file-backed and remote artifact rows, and can also use either a direct weighted-feature model artifact family or a declared row-scoring service when runtime reuse is enabled.
- [x] The “thin shell moved out of `main.rs`” milestones are real for the command groups called out in this board: status, release-closure, research/debug, market-data, update/analyze-live, and the `auto_quant` wrapper clusters all have dedicated shell modules now.
- [x] The Workstream 4 starter milestones are real: source-reliability EM diagnostics now include a holdout-style train/eval summary, and delayed-reward replay surfaces now expose chronological resolution validation plus `1h/4h/24h` Brier-style horizon checks.

### Confirmed Partial Or Board Wording Too Optimistic

- [~] `belief_core` is no longer “Not Yet” at the file-creation level. `src/belief_core/mod.rs`, `structural_state.rs`, `source_reliability.rs`, `regime_filter.rs`, `changepoint_gate.rs`, `ranking_label.rs`, and `beta_dirichlet_update.rs` already exist. The correct status is “started and partially routed”, not “unstarted module split”.
- [~] `workflow_status.rs` really does reuse the shared structural playbook bundle for many structural phases now, but the file is still large and still owns a lot of surface assembly.
- [~] `application/belief/structural_temporal_adjustment.rs` is now mostly a compatibility shell over `belief_core::regime_filter`, but the overall transition / changepoint engine is still not fully centralized.
- [~] Workstream 3 is partially closed in a real way: structural consumer surfaces can consume artifact-backed scores at runtime, but broader downstream runtime behavior still mixes “real artifact-backed path” and “sample / placeholder path” depending on which surface is being discussed.

### Still Not Done

- [ ] Workstream 1 acceptance is not yet met. Core learning math still primarily lives in oversized files, especially `src/state/types.rs`; `src/application/orchestration/structural_playbook.rs` and `src/application/orchestration/workflow_status.rs` are also still large owners rather than thin consumers.
- [ ] Workstream 2 acceptance is not yet met. Transition and break logic is better-factored than before, but still heuristic: maintained transition refresh is not yet a fuller unified state-space / HMM-grade engine, and break maintenance is not yet a fuller competing-hypothesis changepoint engine.
- [ ] The board’s “replace heuristic transition/break mixing with a maintained, emission-aware core” item is still open. Current code has explicit emission-conditioned helpers, but it still relies on fixed recursive discounts and fixed weighted blends in the current owner layer.
- [ ] A deeper learned/contextual target-policy probability model is still not landed. Current target-policy context learning remains the compact `symbol:regime:direction` bucket-posterior family.
- [ ] Replay-grade / out-of-sample source-reliability validation is still not landed. Holdout and replay summaries now exist, but they are still compact diagnostics rather than the larger-panel validation end-state.
- [ ] A full elapsed-time competing-risk delayed-reward censoring model is still not landed. Current code exposes compact hazard / incidence / horizon diagnostics, but not the fuller event-time competing-risk model described by the longer plan.

### What Needs To Be Done Next

1. Finish Workstream 1 for real: keep the new `belief_core` files, but move the remaining learning / EM / temporal update ownership out of `src/state/types.rs` so it stops being the dominant math owner.
2. Finish Workstream 2 immediately after that: make maintained transition refresh, emission-conditioned updates, and changepoint maintenance one clear core, with snapshot-time reweighting reduced to a consumer layer.
3. Narrow the remaining Workstream 3 gap explicitly: keep the current opt-in structural path-ranker runtime, but make the repo’s downstream runtime behavior clearly distinguish artifact-backed behavior from sample / placeholder behavior and decide whether `policy_engine.rs` is inside this closure slice or not.
4. Then deepen Workstream 4: keep the current holdout + replay summaries, but upgrade them into stronger out-of-sample / larger-panel validation and decide whether to stop at compact delayed-reward diagnostics or invest in the fuller competing-risk model the longer plan points to.

## 2026-05-04 Provider-Profile Progress Addendum

Since the earlier code-verification snapshot, the repo landed a full opt-in provider-profile usability sweep as a sequence of checkpoint commits:

- `e56cf73` `feat: preserve opt-in provider profile guidance`
- `65e8fa9` `feat: surface selected profile workflow contracts`
- `fa5d454` `feat: summarize opt-in profile compact output`
- `06d9ee4` `feat: surface profile contracts in bootstrap input`
- `6d70cc2` `feat: narrow bootstrap profile access prompts`
- `0b63888` `refactor: slim agent profile payloads`
- `5361a62` `refactor: shrink jsonl profile payloads`
- `d87d54d` `refactor: trim agent profile provenance`
- `d3689cf` `refactor: normalize profile source provenance`
- `1a2275a` `refactor: dedupe workflow profile payloads`

What this now means in concrete repo behavior:

- zero-config default still does not auto-load personal data or maintainer profile state
- explicit `--profile` selection now carries through provider guidance instead of being dropped on the next command hint
- user-facing and agent-facing workflow surfaces expose direct selected-profile summary fields instead of forcing callers to inspect a buried blob
- compact and JSONL provider views now keep profile payloads lightweight while still exposing the selected data-contract / provider-track summary needed for action selection
- agent bootstrap live input now carries selected-profile id / summary / contract / track summaries, and its provider-access request list narrows to profile-scoped prompts when a profile is selected
- default zero-config surfaces now also advertise repo-example opt-in profiles without selecting them:
  - `provider-status --agent` and JSONL/compact surfaces expose `available_opt_in_profiles`
  - `workflow-status --human` emits a short `Profiles: opt-in only...` hint when no profile is selected
  - `workflow-status --agent` mirrors the same lightweight available-profile list for consumer agents that want to offer an explicit reuse choice
- fake-real bootstrap shakedown closed a remaining contract leak:
  - default `workflow-status --phase agent-bootstrap` no longer auto-reuses maintainer-local Tomac roots or cleaned-path commands
  - personal historical path hints now only flow into bootstrap commands/detected paths when the caller explicitly opts into a provider profile
- `workflow-status` top-level consumer surfaces now summarize existing validation lanes instead of burying them only inside deep structural payloads:
  - human output includes a compact `Validation: ...` line with source-reliability EM / holdout / replay and delayed-reward replay status
  - agent JSON includes a `structural_validation_summary` block derived from the existing experience-prior validation surfaces
  - source-reliability EM holdout now explicitly surfaces `split_strategy=chronological_recommended_at`
  - source-reliability EM replay now explicitly surfaces `split_strategy=expanding_window_recommended_at`
- Workstream 4 validation logic itself has now moved one step closer to real out-of-sample behavior:
  - source-reliability EM holdout is no longer implicitly keyed by map order; it now splits by `recommended_at`
  - source-reliability EM replay now exists as a separate expanding-window summary instead of relying only on the single holdout slice
- offline structural prior seeding now extends beyond `analyze` into adjacent research/backtest lanes:
  - `factor-research` writes `research_run_structural_prior_seed` after refreshing the workflow snapshot
  - mutation evaluations in that lane write `factor_mutation_structural_prior_seed`
  - `factor-backtest` writes `backtest_run_structural_prior_seed`
- `workflow-status` consumer surfaces now also expose a low-token path-ranker runtime summary:
  - human output includes a compact `Ranker: status=... source=...` line when a recommended path is present
  - agent JSON includes `path_ranker_summary`, so consumers can distinguish registered artifact/model/service-backed ranking from baseline-only behavior without traversing the full bundle
  - `workflow-status --phase structural-ranker-runtime` now exposes that same runtime/source summary directly for machine callers that only want ranker readiness/provenance

Verification for this lane is no longer just static inspection:

- `CARGO_BUILD_JOBS=1 cargo check --tests`
- `provider_status_agent_command_is_profile_aware_only_when_opted_in`
- `agent_surface_selected_profile_omits_heavy_contract_and_track_details`
- `compact_surface_summarizes_selected_profile_contracts_and_tracks`
- `jsonl_summary_uses_lightweight_selected_profile_shape`
- `human_workflow_status_view_keeps_selected_profile_in_provider_command`
- `human_workflow_status_view_surfaces_opt_in_profile_hint_when_unselected`
- `agent_workflow_status_view_surfaces_selected_profile_summary_contracts`
- `agent_bootstrap_live_input_surfaces_selected_profile_contracts`
- `provider_status_agent_lists_available_opt_in_profiles_without_selecting_one`
- `workflow_status_agent_accepts_opt_in_profile_path`
- `workflow_status_human_surfaces_opt_in_profile_hint_without_selecting_one`
- `agent_bootstrap_without_profile_does_not_reuse_detected_personal_paths`
- `bootstrap_output_does_not_auto_reuse_personal_tomac_paths_without_profile`
- `agent_and_human_workflow_status_views_expose_experience_prior_surface`
- `agent_workflow_status_prefers_registered_artifact_scores_when_present`
- `agent_and_human_workflow_status_views_expose_recommended_path_bundle`
- `workflow_status_phase_structural_ranker_runtime_summarizes_runtime_source`
- `test_structural_source_reliability_em_holdout_prefers_chronological_split`
- `workflow_status_structural_ranker_runtime_phase_is_available`
- `test_run_factor_research_persists_rankings_and_run_record`
- `test_run_factor_backtest_persists_backtest_run_and_agent_bundle`

Priority change after this sweep:

- the provider-profile hot-plug lane is now in a good enough state that further polish there is lower value
- the next highest-value work should switch back to broader runtime closure or validation hardening rather than more profile payload tuning

## 2026-05-04 Repo-State Reconciliation Update

Scope of this pass:

- current inspected `HEAD`: `9fcec9e`
- recent landed checkpoints verified from `git log`
- current dirty-worktree diff reviewed so this board does not accidentally credit uncommitted formatting drift as finished implementation

### Reconciled Done

- [x] The provider-profile lane is materially closed for the current public workflow surfaces, and zero-config default no longer auto-reuses maintainer-local Tomac roots without explicit `--profile`.
- [x] `workflow-status` now surfaces validation and ranker-readiness status at the top level through `structural_validation_summary`, `path_ranker_summary`, `--phase structural-validation`, and `--phase structural-ranker-runtime`.
- [x] Source-reliability holdout now uses a chronological `recommended_at` split, and replay now has its own `expanding_window_recommended_at` summary instead of being implied only by the holdout slice.
- [x] Offline structural prior seeding now lands in the adjacent research/backtest lanes through `research_run_structural_prior_seed`, `factor_mutation_structural_prior_seed`, and `backtest_run_structural_prior_seed`.

### Reconciled Not Done

- [ ] Workstream 1 acceptance is still open: the new `belief_core` owners exist, but `src/state/types.rs`, `src/application/orchestration/workflow_status.rs`, `src/main.rs`, and `src/application/orchestration/structural_playbook.rs` remain oversized owners.
- [ ] Workstream 2 acceptance is still open: `regime_filter.rs` and `changepoint_gate.rs` exist and own more logic, but the engine is still heuristic rather than a fuller maintained filter / changepoint core.
- [ ] Workstream 3 closure is still open beyond the current direct weighted-feature model path and row-scoring service contract.
- [ ] Workstream 4 closure is still open beyond the current compact holdout / replay diagnostics and delayed-reward horizon summaries.

### Current Worktree Note

- [~] This checkout still has 11 modified files in `git status --short`, but the diffs inspected in this pass are formatting / reflow / export-order cleanup only, including the current `src/application/orchestration/structural_playbook.rs` diff.
- [~] This pass therefore does not credit any additional uncommitted functionality beyond `HEAD`.

### Next Actual Work

1. Keep extracting the remaining structural learning / EM / temporal ownership out of `src/state/types.rs` so Workstream 1 stops being only a partial owner split.
2. Finish unifying maintained transition refresh and break maintenance in `belief_core::{regime_filter, changepoint_gate}` so snapshot-time reweighting becomes a consumer layer instead of the main engine.
3. Deepen Workstream 4 with stronger out-of-sample / replay validation before opening another surface-polish slice.
4. Return to broader path-ranker runtime expansion only if a concrete downstream consumer gap remains after validation hardening.
