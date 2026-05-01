# 20260501 Repo TODO Progress Audit

Status: active, not complete

Scope: audit progress against `docs/plans/20260501repo.md` and the active objective:
use the document as a TODO source, implement scoped repo changes with commits, keep
surfaces zero-config, consumer-usable, token-friendly, low-pollution, and avoid
loading user-specific data unless it is explicit and opt-in.

## Completion Criteria

| Criterion | Evidence | Status |
|---|---|---|
| Treat `docs/plans/20260501repo.md` as implementation input | P6 rows, calibration, maturity, propensity, lower-bound gate, validation, and trainer-handoff work all map to the document's CatBoost path-ranking target and ranking-label sections | partial |
| Land decisions as versioned repo artifacts | Commits `acce819`, `2bb1c8e`, `bb57d73`, `2253bfe`, `05caf1d`, `45fc44c`, and `05d4ca7` are committed on `green-baseline` | done for current slices |
| Preserve zero-config behavior | New path-ranking fields are derived from existing structural state/export rows; no new required CLI flags or environment variables were added | done for current slices |
| Keep consumer surfaces token-friendly | `policy-training-status` uses compact booleans, counts, scores, warnings, and paths rather than verbose model dumps | done for current slices |
| Avoid repo/runtime pollution | Verification used normal cargo targets and tempdirs in tests; final `git status --short` was clean after each committed slice | done for current slices |
| Keep user-specific data hot-pluggable/opt-in | No personal data path, account config, provider default, or environment auto-load was added | done for current slices |
| Do not claim complete without audit | This audit records remaining gaps and does not mark the active goal complete | done |

## Implemented Evidence

Recent committed slices:

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
- `docs/structural-belief-learning-repo-map.md`
- `docs/plans/2026-05-02-catboost-path-ranking-target-design.md`

Verified commands during this iteration line:

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
- `live feedback posterior update` still lacks deeper target-policy calibration beyond current clipped SNIPS/DR fields.
- `artifact-validation prior source` still lacks a full Dawid-Skene EM-style source confusion model.
- `structural_prior_state` still lacks a fitted HSMM-style duration distribution beyond current dwell/hazard fields.
- `BBN node/branch posterior update` still lacks deeper Hamilton/DBN recursive filtering beyond maintained transition posterior state.

## Next Concrete Options

1. Build an external ranker artifact ingestion boundary only after the artifact shape is decided.
2. Generate or collect enough raw-scored structural path-ranking rows in an isolated state dir, then validate the production gate.
3. Move to a non-P6 TODO slice: fitted duration priors, deeper target-policy calibration, or explicit source-reliability EM.

Do not call the active goal complete until one of those remaining lines is either implemented or explicitly descoped.
