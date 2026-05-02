# 20260501 Repo TODO Progress Audit

Status: active, not complete

Scope: audit progress against `docs/plans/20260501repo.md` and the active objective:
use the document as a TODO source, implement scoped repo changes with commits, keep
surfaces zero-config, consumer-usable, token-friendly, low-pollution, and avoid
loading user-specific data unless it is explicit and opt-in.

## Completion Criteria

| Criterion | Evidence | Status |
|---|---|---|
| Treat `docs/plans/20260501repo.md` as implementation input | P6 path-ranking rows and the later source-reliability, duration, off-policy, and target-policy variance diagnostics all map to the document's CatBoost, Dawid-Skene, HSMM, and OPE sections | partial |
| Land decisions as versioned repo artifacts | Commits `acce819`, `2bb1c8e`, `bb57d73`, `2253bfe`, `05caf1d`, `45fc44c`, `05d4ca7`, `d9631fc`, `400b00c`, `983e622`, `3f67add`, `1cc6825`, `c494b60`, and `0cbd46e` are committed on `green-baseline` | done for current slices |
| Preserve zero-config behavior | New path-ranking, source-reliability, duration, SNIPS/DR, and target-policy diagnostics are derived from existing structural state/export rows; no new required CLI flags or environment variables were added | done for current slices |
| Keep consumer surfaces token-friendly | `policy-training-status`, `structural-experience-priors`, and `structural-temporal-summary` expose compact booleans, counts, probabilities, scalar diagnostics, warnings, and paths rather than verbose model dumps | done for current slices |
| Avoid repo/runtime pollution | Verification used normal cargo targets and tempdirs in tests; final `git status --short` was clean after each committed slice | done for current slices |
| Keep user-specific data hot-pluggable/opt-in | No personal data path, account config, provider default, or environment auto-load was added | done for current slices |
| Do not claim complete without audit | This audit records remaining gaps and does not mark the active goal complete | done |

## Implemented Evidence

Recent committed slices:

- `d9631fc feat: derive source confusion likelihoods`
- `400b00c feat: temper source panels by confusion likelihood`
- `983e622 feat: fit node duration distributions`
- `3f67add feat: expose snips effective sample diagnostics`
- `1cc6825 feat: surface duration distribution diagnostics`
- `c494b60 feat: add compact bocpd break telemetry`
- `0cbd46e feat: calibrate target policy feedback priors`
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
- `cargo test --lib panel_derived_prior_uses_source_confusion_concentration`
- `cargo test --lib structural_experience_prior_surface_prefers_panel_derived_prior_over_stale_aggregate_prior`
- `cargo test --lib test_structural_prior_seed_rebuilds_node_duration_priors`
- `cargo test --lib duration`
- `cargo test --lib test_structural_feedback_records_snips_and_dr_policy_priors`
- `cargo test --lib structural_experience_prior`
- `cargo test --lib structural_temporal_summary_node_prefers_persisted_temporal_state_streak_count`
- `cargo test --lib test_structural_node_duration_outcome_support_penalizes_recent_negative_streaks`
- `cargo test --lib structural_path_probability_calibration`
- `cargo test --lib structural_path_ranking_target`
- `cargo test --lib structural_path_ranking_target_training_status`
- `cargo check --all-targets`
- `git diff --check`
- `git status --short`

## Remaining Gaps

The objective is not complete.

- P6 still lacks a real trained external path-ranker artifact/service.
- P6 still lacks real exported raw-scored rows sufficient for production validation.
- P6 production validation is now gated, but not satisfied by live historical data.
- `live feedback posterior update` now has ESS-weighted target-policy reward prior, variance penalty, and conservative lower-bound diagnostics, but still lacks a fully calibrated target-policy probability model and richer maturity/censoring.
- `artifact-validation prior source` now has compact source-confusion likelihood cells and panel tempering, but still lacks a full Dawid-Skene EM-style latent truth model.
- `structural_prior_state` now has empirical HSMM-style duration distributions plus compact BOCPD-style break/continue telemetry, but still lacks richer calibrated change-point modeling.
- `BBN node/branch posterior update` still lacks deeper Hamilton/DBN recursive filtering beyond maintained transition posterior state.

## Next Concrete Options

1. Build an external ranker artifact ingestion boundary only after the artifact shape is decided.
2. Generate or collect enough raw-scored structural path-ranking rows in an isolated state dir, then validate the production gate.
3. Move to a non-P6 TODO slice: richer BOCPD calibration, full target-policy probability calibration, or explicit source-reliability EM.

Do not call the active goal complete until one of those remaining lines is either implemented or explicitly descoped.
