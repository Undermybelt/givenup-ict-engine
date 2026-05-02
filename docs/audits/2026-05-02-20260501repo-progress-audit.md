# 20260501 Repo TODO Progress Audit

Status: active, not complete

Scope: audit progress against `docs/plans/20260501repo.md` and the active objective:
use the document as a TODO source, implement scoped repo changes with commits, keep
surfaces zero-config, consumer-usable, token-friendly, low-pollution, and avoid
loading user-specific data unless it is explicit and opt-in.

## Completion Criteria

| Criterion | Evidence | Status |
|---|---|---|
| Treat `docs/plans/20260501repo.md` as implementation input | P6 path-ranking rows and the later source-reliability, Dawid-Skene readiness, duration, BOCPD calibration, off-policy, target-policy variance, delayed-reward censoring, and compact delayed-reward competing-risk diagnostics all map to the document's CatBoost, Dawid-Skene, HSMM, BOCPD, delayed-feedback, and OPE sections | partial |
| Land decisions as versioned repo artifacts | Commits `acce819`, `2bb1c8e`, `bb57d73`, `2253bfe`, `05caf1d`, `45fc44c`, `05d4ca7`, `d9631fc`, `400b00c`, `983e622`, `3f67add`, `1cc6825`, `c494b60`, `0cbd46e`, `1cbf9fc`, `4cc3d66`, `0175b3c`, `fc04494`, `a880cb4`, `3fb108f`, `de0f1bb`, `eb3cff2`, `82594f6`, `aee6e83`, `ffae6fd`, `f5714d3`, `7c1dcf6`, `df0e14f`, `2a8e25f`, `afbc93b`, `f130def`, and `c5e0ec5` are committed on `green-baseline` | done for current slices |
| Preserve zero-config behavior | New path-ranking, source-reliability, duration, SNIPS/DR, target-policy, and delayed-reward censoring diagnostics are derived from existing structural state/export rows; no new required CLI flags or environment variables were added | done for current slices |
| Keep consumer surfaces token-friendly | `policy-training-status`, `structural-experience-priors`, and `structural-temporal-summary` expose compact booleans, counts, probabilities, scalar diagnostics, warnings, and paths rather than verbose model dumps | done for current slices |
| Avoid repo/runtime pollution | Verification used normal cargo targets and tempdirs in tests; final `git status --short` was clean after each committed slice | done for current slices |
| Keep user-specific data hot-pluggable/opt-in | No personal data path, account config, provider default, or environment auto-load was added | done for current slices |
| Do not claim complete without audit | This audit records remaining gaps and does not mark the active goal complete | done |

## Prompt-to-Artifact Checklist

| Prompt requirement / TODO input | Concrete artifact evidence | Verification / gate | Status |
|---|---|---|---|
| Use `docs/plans/20260501repo.md` as a TODO source | `docs/structural-belief-learning-repo-map.md` maps plan sections to P2/P3/P4/P5/P6 status; this audit records TODO closure and remaining gaps | manual inspection of docs plus committed implementation slices | partial |
| Implement scoped slices and commit as appropriate | Recent code commits cover path-ranking target rows, source reliability/confusion, duration distributions, SNIPS/DR/target-policy diagnostics, target-policy probability variance/Brier/calibration-error diagnostics, EM readiness, fixed-iteration EM fit diagnostics, persisted EM source-confusion summaries, EM calibration diagnostics, EM reliability consumption, BOCPD calibration, compact empirical/recursive run-length diagnostics, delayed-reward censoring-adjusted diagnostics, and compact delayed-reward competing-risk diagnostics | `git log --oneline` on `green-baseline` | done for current slices |
| Preserve zero-config behavior | New surfaces derive from `StructuralPriorLearningState`, exported target rows, or workflow snapshots; no required CLI flag, env var, provider config, or state-dir default was added | code review of touched files and `cargo check --all-targets` | done for current slices |
| Keep consumer surfaces usable and token-friendly | `policy-training-status`, `structural-experience-priors`, and `structural-temporal-summary` expose compact scalar fields, booleans, counts, warnings, and paths | targeted workflow/status tests and JSON field assertions | done for current slices |
| Keep user-specific data explicit and hot-pluggable | No personal account/provider/default market data path was introduced; external trainer/service and live data remain explicit future inputs | code/doc inspection; no env auto-load added | done for current slices |
| Avoid pollution / debt | Verification used normal cargo targets; runtime/data generation was not run into repo-local `state/`; checkpoint `git status --short --branch` is clean after commits | `git diff --check`; `git status --short --branch` | done for current slices |
| CatBoost / path-ranker target from plan | Target rows, maturity fields, lower-bound gates, training weights, calibration evaluator, trainer manifest readiness, and optional external trainer artifact status boundary exist | `cargo test --lib structural_path_ranking_target`; `cargo test --lib structural_path_ranking_target_training_status` | partial: no real trained service/artifact or sufficient real raw-scored rows |
| Dawid-Skene / source reliability from plan | Source posterior, outcome-confusion likelihoods, panel tempering, EM-readiness counts, latent-label consensus/conflict diagnostics, compact fixed-iteration EM fit diagnostics, persisted source-specific EM confusion summaries, compact persisted-EM status fields, persisted leave-source-out EM calibration diagnostics, and persisted EM source-reliability consumption exist | `cargo test --lib source_reliability`; `cargo test --lib source_outcome_confusion`; `cargo test --lib source_reliability_em`; `cargo test --lib workflow_status_phase_structural_experience_priors_tracks_current_lineage` | partial: no real larger-panel or out-of-sample calibration validation yet |
| HSMM / BOCPD duration prior from plan | Empirical dwell distribution, hazard/survival, evidence-weighted BOCPD raw/calibrated break probability, compact empirical run-length mode/probability/tail/mass diagnostics, compact one-step recursive run-length reset/mode/expectation/entropy diagnostics, and temporal summary fields exist | `cargo test --lib duration`; `cargo test --lib test_structural_prior_seed_rebuilds_node_duration_priors`; `cargo test --lib workflow_status_phase_structural_temporal_summary_exposes_discounted_masses`; `cargo test --lib structural_temporal_summary_node_prefers_persisted_temporal_state_streak_count` | partial: no full changepoint filter over richer sequence history |
| Logged-bandit / OPE target-policy learning from plan | Behavior probability logging, logged probability variance/confidence/lower-bound/Brier/calibration-error diagnostics, IPS/SNIPS/DR, ESS, target-policy reward prior, variance penalty, conservative lower bound, compact maturity/censoring counters, smoothed delayed-reward resolution/censoring probabilities, censoring-adjusted reward prior/lower-bound diagnostics, and compact success/failure/invalidation/abandonment competing-risk diagnostics exist | `cargo test --lib test_structural_feedback_records_snips_and_dr_policy_priors`; `cargo test --lib structural_experience_prior`; `cargo test --lib structural_prior_maturity_diagnostics_count_unresolved_followed_feedback`; `cargo test --lib workflow_status_phase_structural_experience_priors_tracks_current_lineage` | partial: no learned/contextual target-policy probability model or full elapsed-time survival/competing-risk delayed-reward model |
| Hamilton / DBN recursive filtering from plan | Transition posterior state persists and downstream branch/candidate surfaces consume it | transition and structural workflow tests listed below | partial: no deeper Hamilton/DBN recursive filter |

## Implemented Evidence

Recent committed slices:

- `d9631fc feat: derive source confusion likelihoods`
- `400b00c feat: temper source panels by confusion likelihood`
- `983e622 feat: fit node duration distributions`
- `3f67add feat: expose snips effective sample diagnostics`
- `1cc6825 feat: surface duration distribution diagnostics`
- `c494b60 feat: add compact bocpd break telemetry`
- `0cbd46e feat: calibrate target policy feedback priors`
- `1cbf9fc feat: surface source reliability em readiness`
- `4cc3d66 feat: calibrate bocpd break probability`
- `0175b3c docs: audit bocpd calibration progress`
- `fc04494 feat: surface path ranker trainer manifest readiness`
- `a880cb4 feat: surface structural feedback maturity diagnostics`
- `3fb108f feat: surface path ranker trainer artifact status`
- `de0f1bb feat: surface source reliability consensus diagnostics`
- `eb3cff2 feat: surface bocpd run length diagnostics`
- `82594f6 feat: surface recursive bocpd run length diagnostics`
- `aee6e83 feat: surface source reliability em fit diagnostics`
- `ffae6fd feat: consume source reliability em fit`
- `f5714d3 feat: surface target policy probability diagnostics`
- `f130def feat: calibrate target policy probabilities`
- `7c1dcf6 feat: persist source reliability em summaries`
- `df0e14f feat: validate source reliability em calibration`
- `2a8e25f docs: audit source reliability em calibration`
- `afbc93b feat: surface delayed reward censoring diagnostics`
- `c5e0ec5 feat: surface delayed reward competing risk diagnostics`
- `acce819 feat: expose path ranking maturity fields`
- `2bb1c8e feat: weight path ranking calibration by propensity`
- `bb57d73 feat: add path ranking lower-bound gates`
- `2253bfe feat: export path ranking training weights`
- `05caf1d feat: gate path ranking production validation`
- `45fc44c feat: describe path ranking trainer handoff`
- `05d4ca7 docs: refresh path ranking contract map`

Primary files now carrying the P6 contract:

- `src/application/orchestration/structural_playbook.rs`
- `src/application/entry_models/training_export.rs`
- `src/application/orchestration/workflow_status.rs`
- `src/state/types.rs`
- `docs/structural-belief-learning-repo-map.md`
- `docs/plans/2026-05-02-catboost-path-ranking-target-design.md`
- `docs/plans/20260501repo.md`

Verified commands during this iteration line:

- `cargo test --lib source_outcome_confusion`
- `cargo test --lib source_reliability`
- `cargo test --lib source_reliability_em`
- `cargo test --lib source_reliability_em_readiness_requires_multi_source_overlap`
- `cargo test --lib test_structural_prior_seed_persists_source_reliability_em_summaries`
- `cargo test --lib panel_derived_prior_uses_persisted_source_reliability_em_summary`
- `cargo test --lib panel_derived_prior_uses_source_confusion_concentration`
- `cargo test --lib structural_experience_prior_surface_prefers_panel_derived_prior_over_stale_aggregate_prior`
- `cargo test --lib test_structural_prior_seed_rebuilds_node_duration_priors`
- `cargo test --lib duration`
- `cargo test --lib test_structural_feedback_records_snips_and_dr_policy_priors`
- `cargo test --lib structural_experience_prior`
- `cargo test --lib structural_prior_maturity_diagnostics_count_unresolved_followed_feedback`
- `cargo test --lib workflow_status_phase_structural_experience_priors_tracks_current_lineage`
- `cargo check --all-targets`
- `git diff --check`
- `cargo test --lib workflow_status_phase_structural_temporal_summary_exposes_discounted_masses`
- `cargo test --lib structural_temporal_summary_node_prefers_persisted_temporal_state_streak_count`
- `cargo test --lib test_structural_node_duration_outcome_support_penalizes_recent_negative_streaks`
- `cargo test --lib structural_path_probability_calibration`
- `cargo test --lib structural_path_ranking_target`
- `cargo test --lib structural_path_ranking_target_training_status`
- `cargo test --lib policy_training_status_lists_registered_providers`
- `rustfmt --edition 2021 --check src/application/entry_models/training_export.rs`
- `cargo check --all-targets`
- `git diff --check`
- `git status --short`

## Remaining Gaps

The objective is not complete.

- P6 now has an opt-in external path-ranker artifact status boundary, but still lacks a real trained external path-ranker artifact/service.
- P6 still lacks real exported raw-scored rows sufficient for production validation.
- P6 production validation is now gated, but not satisfied by live historical data.
- `live feedback posterior update` now has logged behavior-policy probability variance/confidence/lower-bound/Brier/calibration-error diagnostics, ESS-weighted target-policy reward prior, variance penalty, conservative lower-bound diagnostics, compact maturity/censoring counters, smoothed delayed-reward resolution/censoring probabilities, censoring-adjusted reward prior/lower-bound diagnostics, and compact counter-derived competing-risk probabilities, but still lacks a learned/contextual target-policy probability model and a full elapsed-time survival/competing-risk delayed-reward model.
- `artifact-validation prior source` now has compact source-confusion likelihood cells, panel tempering, cross-source EM-readiness diagnostics, latent-label consensus telemetry, fixed-iteration EM fit diagnostics, persisted source-specific EM confusion summaries, compact persisted-EM status fields, persisted leave-source-out EM calibration diagnostics, and persisted EM source-reliability consumption, but still lacks real larger-panel and out-of-sample calibration validation.
- `structural_prior_state` now has empirical HSMM-style duration distributions plus compact evidence-weighted BOCPD-style raw/calibrated break/continue, empirical run-length telemetry, and one-step recursive reset/mode/expectation/entropy diagnostics, but still lacks full changepoint filtering over richer sequence history.
- `BBN node/branch posterior update` still lacks deeper Hamilton/DBN recursive filtering beyond maintained transition posterior state.

## Next Concrete Options

1. Generate or collect enough raw-scored structural path-ranking rows in an isolated state dir, then validate the production gate.
2. Move to a non-P6 TODO slice: learned/contextual target-policy probability modeling, elapsed-time survival/competing-risk delayed-reward modeling, full BOCPD changepoint filtering over richer sequence history, or real larger-panel source-reliability EM calibration validation once enough cross-source labels exist.
3. Build a real opt-in external path-ranker artifact/service that writes the already-defined trainer artifact file.

Do not call the active goal complete until one of those remaining lines is either implemented or explicitly descoped.
