# Hot-Plug Personal Data + Factor Release Handoff TODO

Date: 2026-05-12

Purpose: continue the current factor/release lane without polluting the repo or
turning maintainer-local personal data into a mandatory public surface.

## Task Intent Draft

Requested outcome:
- Commit at reasonable checkpoints.
- Continue implementation after the factor-result/release readiness audit.
- Preserve zero-config behavior for normal consumers.
- Keep user-facing output token-friendly.
- Make personal data/material needs hot-pluggable and opt-in.
- Let users choose whether to adopt the maintainer profile/material defaults.
- Keep release artifacts clean enough to publish to the release mirror.

Non-goals:
- Do not make maintainer-local data required for first run.
- Do not commit generated dependency workspaces such as nested Auto-Quant clones.
- Do not promote local-only research evidence as release-ready trading proof.
- Do not rewrite Board A or Board B authority; this file is a handoff/checkpoint
  board only.

## Baseline Read Set Hint

- `AGENTS.md`
- `docs/plans/2026-05-09-factor-iteration-pre-bayes-bbn-catboost-execution-tree-todo.md`
- `docs/plans/2026-05-10-actionable-regime-confidence-todo.md`
- `docs/plans/2026-05-10-regime-conditional-auto-quant-profitability-todo.md`
- `src/application/auto_quant/`
- `src/application/orchestration/workflow_status.rs`
- `src/application/provider_catalog.rs`
- `src/main.rs`

## Impact Statement Draft

The next implementation slice should improve consumer ergonomics without
hard-wiring the maintainer's private research profile into the public CLI. The
public contract should stay generic: zero-config defaults work, optional profile
or material bundles can be inspected/adopted, and agent/human output remains
compact.

## Todo Checkpoint Draft

Status legend: `done`, `active`, `next`, `blocked`, `not_yet`.

| Status | Item | Evidence / Notes |
|---|---|---|
| done | Routing and repo baseline read | Read Hermes routers and repo `AGENTS.md`; primary route now `aegis/long-task-continuation`. |
| done | Initial release audit | Main is ahead of `origin/main`; release mirror latest tag seen as `v0.1.1`; GH CLI auth is invalid. |
| done | Pollution scan | `docs/experiments/actionable-regime-confidence` is about 27G and contains nested `.deps/auto-quant` workspaces; do not stage them blindly. |
| done | Repair release-blocking Clippy errors | Reworked test fixtures away from `field_reassign_with_default`, replaced one `vec!` with an array, and used `then_some`. |
| done | Re-run `cargo fmt --check` and `cargo clippy --all-targets -- -D warnings` | Both passed after the fix slice. |
| done | Identify hot-plug personal data surface already present | Existing surfaces: provider `--profile`, Auto-Quant `--auto-quant-profile`, read-only `--strategy-material-root`, provider profile JSON, and factor candidate profile JSON. |
| done | Implement smallest consumer-safe hot-plug improvement | `workflow-status` now exposes matching opt-in profile references for the current symbol without selecting or loading the profile. |
| done | Add focused tests for any code behavior change | `cargo test --test provider_neutral_cli -- --nocapture` passed, including new human/agent profile-choice tests. |
| done | Repair `workflow-status` branch-admission routing precedence | `cargo test application::orchestration::workflow_status::tests:: -- --nocapture` passed, 114 workflow-status tests. |
| done | Run full verification after route-precedence repair | `cargo test`, `cargo fmt --check`, and `cargo clippy --all-targets -- -D warnings` passed. |
| done | Final compile/targeted verification after path-literal cleanup and candidate-set field sync | `cargo fmt --check`, `cargo test --test provider_neutral_cli -- --nocapture`, `cargo test application::orchestration::workflow_status::tests:: -- --nocapture`, `cargo clippy --all-targets -- -D warnings`, and `cargo check --tests --quiet` passed. |
| done | Repair clean-export BBN fixture dependency | BBN tests now use tracked, path-redacted `tests/fixtures/policy_training/`; runtime user-state hot-plug path remains unchanged. |
| done | Clean release-export audit | Final `v0.1.2` clean export `/tmp/ict-engine-release-export.ueDk6B` passed fmt, Clippy, and full `cargo test` from committed `HEAD`. |
| done | Update this board after each slice | Current slice recorded here. |
| done | Commit safe slices | Checkpoint commit created for the intended source/docs/tests; nested dependency workspaces and active run state were excluded. |
| done | Prepare release-mirror export/audit | Local mirror clone `/tmp/ict-engine-release-mirror-v012.87caSH` was synced from clean export and committed locally; re-read its HEAD before any push; no tag/push/release created. |
| done | Prove/fix consumer closed-loop usability before release | Found and fixed workflow-status first-run provider summary mismatch; `provider-status` and `workflow-status` now both show yfinance as zero-config live fallback. |
| done | Add one-line `CLAUDE.md` redirect | Contains one line: `open AGENTS.md and read`. |
| done | Expand `AGENTS.md` into the authoritative agent usage contract | Covers zero-config commands, provider policy, privacy rules, closed-loop order, posterior requirements, TimesFM optionality, feedback loop, and release constraints. |
| done | Run fresh zero-config smoke in `/tmp` state | `/tmp/ict-engine-closed-loop-smoke-fixed.bmbPSO` ran provider/workflow/analyze/Pre-Bayes/policy-training/export/update checks with no profile and no private provider config. |
| done | Run focused verification for the closed-loop/docs slice | `cargo fmt --check`, provider-neutral CLI tests, workflow-status tests, and Clippy passed. |
| done | Commit the closed-loop/docs slice | This amended commit staged only `AGENTS.md`, `CLAUDE.md`, `workflow_status.rs`, and this handoff board. |
| blocked | Publish release mirror | Blocked on the new closed-loop/entrypoint/privacy gate and then explicit operator confirmation for `v0.1.2` tag/push/`gh release create`. GitHub auth was previously available and remote had no `v0.1.2` tag, but re-check before any publish. |

## Resume State Hint

Active slice: closed-loop applicability, consumer zero-config/privacy audit, agent
entrypoint docs, and fresh `/tmp` smoke before release publication.

If resuming:
1. Re-run `git status --short --branch`.
2. Check for active processes writing under `docs/experiments/actionable-regime-confidence/runs`.
3. Re-run `cargo fmt --check`.
4. Re-run `cargo clippy --all-targets -- -D warnings`.
5. Read this file before staging anything.

## Drift Check Draft

- Scope: still aligned with factor-result release readiness plus optional personal-data hot-plug UX; release is now gated by fresh closed-loop applicability proof.
- Compatibility boundary: generic public CLI must not depend on maintainer-local ontology or data.
- Retirement track: generated dependency workspaces should remain untracked or be moved out of repo release artifacts; this board does not make them release evidence.
- Decision: continue.

## Evidence Bundle Draft

- `cargo fmt --check`: passed before this board was created.
- `cargo check --tests --quiet`: passed after repairing mismatched fixture initializer defaults.
- `cargo test --test provider_neutral_cli -- --nocapture`: passed, 19 tests.
- `cargo fmt --check`: passed after the hot-plug profile-choice slice.
- `cargo clippy --all-targets -- -D warnings`: passed after the Clippy repair and hot-plug profile-choice slice.
- `cargo test application::orchestration::workflow_status::tests::agent_workflow_status_empty_state_uses_explicit_no_state_contract -- --nocapture`: passed after branch-admission route gating.
- `cargo test application::orchestration::workflow_status::tests:: -- --nocapture`: passed, 114 tests after branch-admission route gating.
- `cargo fmt --check`: passed after branch-admission route gating.
- `cargo test`: passed after branch-admission route gating.
- `cargo clippy --all-targets -- -D warnings`: passed after branch-admission route gating.
- `cargo test --test provider_neutral_cli -- --nocapture`: passed after replacing the exact local-path negative assertion with a generic `/Users/` guard.
- `cargo test application::orchestration::workflow_status::tests:: -- --nocapture`: passed after syncing structural candidate-set fields into the path-plan artifact.
- `cargo check --tests --quiet`: passed after final staging candidate.
- `/tmp` clean export from `HEAD`: `cargo test --manifest-path <export>/Cargo.toml bbn::trading -- --nocapture` failed at compile time because the checkpoint omitted required `StructuralPathRankingTargetRow` branch segment fields from `src/belief_core/ranking_label.rs`.
- `/tmp` clean export after adding `ranking_label.rs`: same command progressed and then found one omitted `StructuralPathRankingTargetRow` test constructor in `src/application/entry_models/training_export.rs`.
- `/tmp` clean export after checkpoint commit: `cargo test --manifest-path /tmp/ict-engine-release-export.Fa3UTZ/Cargo.toml bbn::trading -- --nocapture` compiled but failed 3 tests because ignored `state/policy_training` fixtures were absent from the export.
- Local fixture repair: `cargo fmt --check` passed, `cargo test bbn::trading -- --nocapture` passed with 19 matching tests, and `cargo clippy --all-targets -- -D warnings` passed after moving test dependency to tracked fixtures.
- `/tmp` clean export from `f1a561a`: `cargo test --manifest-path /tmp/ict-engine-release-export.IWadVv/Cargo.toml bbn::trading -- --nocapture` passed with 19 matching tests.
- `/tmp` clean export from `f1a561a`: `cargo fmt --manifest-path /tmp/ict-engine-release-export.IWadVv/Cargo.toml --check` passed.
- `/tmp` clean export from `f1a561a`: `cargo clippy --manifest-path /tmp/ict-engine-release-export.IWadVv/Cargo.toml --all-targets -- -D warnings` failed on dead `StructuralRankedPathSelection.paths` and two unused `structural_ranked_paths*` wrappers that were still absent from the committed tree.
- `/tmp` clean export from `32858ad`: `/tmp/ict-engine-release-export.y6Pefh` passed `cargo fmt --manifest-path ... --check`, `cargo clippy --manifest-path ... --all-targets -- -D warnings`, targeted `cargo test --manifest-path ... bbn::trading -- --nocapture`, and full `cargo test --manifest-path ...`.
- `/tmp` clean export from `e6fca81`: `/tmp/ict-engine-release-export.ueDk6B` passed `cargo fmt --manifest-path ... --check`, `cargo clippy --manifest-path ... --all-targets -- -D warnings`, and full `cargo test --manifest-path ...` as the final `v0.1.2` release-candidate gate.
- Release mirror remote probe: `main` and `v0.1.1` still point at `5bc7bc74dfc2b6c88840b774c662d62c1d81cca1`; no `v0.1.2` tag exists yet.
- Local mirror prep: `/tmp/ict-engine-release-mirror-v012.87caSH` was cloned from `Undermybelt/ict-engine-release`, synced from `/tmp/ict-engine-release-export.ueDk6B`, scanned for large files/nested `.git`/state dirs/common secret patterns, and committed locally; re-read mirror HEAD before any push.
- GH CLI: `gh auth status` currently reports an active `Undermybelt` login with `repo`/`workflow` scopes.
- Release mirror remote probe via HTTPS showed `v0.1.1` exists at commit `5bc7bc74dfc2b6c88840b774c662d62c1d81cca1`.
- `cargo run --quiet -- workflow-status --symbol DEMO --state-dir /tmp/ict-engine-closed-loop-smoke-fixed.bmbPSO --agent`: passed after the provider-summary fix and now reports `live zero-config=yfinance` with `selected_profile_id=null`.
- `cargo run --quiet -- analyze --symbol DEMO --demo --state-dir /tmp/ict-engine-closed-loop-smoke-fixed.bmbPSO --human`: passed; produced Pre-Bayes `pass_neutralized`, execution `observe/transition_guardrail/guarded`, and persisted `execution_tree_trace.json`.
- `cargo run --quiet -- workflow-status --symbol DEMO --state-dir /tmp/ict-engine-closed-loop-smoke-fixed.bmbPSO --refresh --agent`: passed; exposes posterior distribution `trend=0.4550`, `range=0.3090`, `stress=0.1596`, `transition=0.0764`.
- `cargo run --quiet -- pre-bayes-status --symbol DEMO --state-dir /tmp/ict-engine-closed-loop-smoke-fixed.bmbPSO --refresh --output-format json`: passed; exposes the same canonical structural probabilities and `latest_uses_soft_evidence=true`.
- `jq ... execution_tree_trace.json`: passed; execution tree persisted `branch=transition_guardrail`, `gate_status=observe`, ranker visible/used flags false, and fail-closed validation notes.
- `cargo run --quiet -- export-structural-path-ranking-target --symbol DEMO --state-dir /tmp/ict-engine-closed-loop-smoke-fixed.bmbPSO`: passed; exported 3 structural path-ranking rows plus CSV/JSONL/history/manifest under `/tmp/.../policy_training/`.
- `cargo run --quiet -- update --symbol DEMO --outcome win --entry-signal strong_buy --state-dir /tmp/ict-engine-closed-loop-smoke-fixed.bmbPSO --pnl 1.0 --ensemble`: passed; consumed pending update/execution candidate artifacts and recorded feedback into update history.
- `cargo run --quiet -- policy-training-status --symbol DEMO --state-dir /tmp/ict-engine-closed-loop-smoke-fixed.bmbPSO --output-format agent`: passed after export/update; reports `analyze_runs=1`, `update_runs=1`, and structural path ranking target rows while keeping runtime disabled/fail-closed until a trainer artifact is explicitly registered.
- Privacy smoke: `workflow-status --agent | rg "/Users/|api[_-]?key|secret|token" -i` returned no matches for the zero-config smoke state.
- `cargo fmt --check`: passed after the closed-loop/docs slice.
- `cargo test --test provider_neutral_cli -- --nocapture`: passed, 19 tests.
- `cargo test application::orchestration::workflow_status::tests:: -- --nocapture`: passed, 114 tests.
- `cargo clippy --all-targets -- -D warnings`: passed.
- Commit checkpoint: this amended `Document closed-loop consumer gate` commit.

## Slice Notes

### 2026-05-12 hot-plug profile-choice slice

Changed:
- `src/application/orchestration/command_entry.rs`
- `tests/provider_neutral_cli.rs`

Behavior:
- `provider-status --agent` still hides opt-in profiles by default.
- `workflow-status --symbol NQ --human` can now show a matching optional profile reuse command without auto-adopting it.
- `workflow-status --symbol NQ --agent` now exposes a lightweight `available_opt_in_profiles` reference while `selected_profile_id` remains null.
- Personal path hints remain redacted/absent unless the user explicitly passes `--profile`.

Next:
- Run `cargo test` if local runtime pressure allows.
- Then stage only intended source/docs/test files and commit a safe checkpoint.

### 2026-05-12 workflow-status branch-admission precedence slice

Changed:
- `src/application/orchestration/workflow_status.rs`
- `docs/plans/2026-05-12-hotplug-personal-data-release-handoff-todo.md`
- `src/belief_core/structural_state.rs`
- `src/belief_core/ranking_label.rs`
- `src/application/entry_models/training_export.rs`
- `src/application/orchestration/structural_playbook.rs`
- `tests/provider_neutral_cli.rs`

Behavior:
- `closed_loop_branch_admission` can still fail closed for an exact latest
  structural feedback branch path.
- Branch admission no longer steals routing from no-state first-run guidance,
  Auto-Quant handoff, evidence review, selected-profile followups, or generic
  recommended-path execution contracts.
- Agent output only treats branch admission as a blocking/router owner when the
  latest update carries the same `structural_feedback.path_id`.
- Path-plan artifacts now carry their candidate set id and candidate paths so
  structural path-ranker runtime matching has a stable serialized contract.
- Structural path-ranker training rows now expose regime-profit branch segments
  as serialized/categorical fields so exact branch paths can feed external or
  direct path-ranker models.
- The new provider-neutral tests guard against local path leakage without
  embedding the maintainer's exact local Tomac path in the test source.

Evidence:
- `cargo test application::orchestration::workflow_status::tests::agent_workflow_status_empty_state_uses_explicit_no_state_contract -- --nocapture`
- `cargo test application::orchestration::workflow_status::tests:: -- --nocapture`
- `cargo test --test provider_neutral_cli -- --nocapture`
- `cargo check --tests --quiet`
- `/tmp` clean export compile gate before release mirror publish

Next:
- Stage only intended files and commit a safe checkpoint.

### 2026-05-12 A/B large-window provider-portability correction

Changed:
- Added `docs/experiments/actionable-regime-confidence/runs/20260512T144700+0800-codex-ab-large-window-provider-portability-correction-v2.md`.
- Appended matching direction-correction sections to Board A and Board B.

Behavior:
- Local long-history data is allowed for training, hardening, and factor discovery.
- Maintainer-local files must not become required consumer inputs.
- Consumer paths must use provider-backed data recipes, built-in factors, or hot-pluggable agent material.
- `15y/1m` is not a rigid public requirement; the actual rule is to maximize feasible history, candle count, and trade observations.
- Tiny daily windows and low trade counts are diagnostics only, not promotion evidence.

Evidence:
- Board A hash before direction writeback: `f08375789ae362d3cbc25ebb0e8ffd316dafebbfd7425b64e996fba968732887`.
- Board B hash before direction writeback: `ea407181585e1b67fff830062b835fe2c886d09d917d2bfcc1c2305feeb19687`.
- Handoff hash before direction writeback: `452fb2afd0424100393119d03a7aaec87bd63b5e3c4dd92aaef7c9cd2aec8e14`.

Next:
- Keep any release/export work from depending on `/Users/thrill3r/Downloads/Tomac` or other maintainer-local data paths.
- For A/B evidence, prefer largest feasible provider-backed windows; if local training is used, require a portable factor/material/recipe before consumer-facing promotion.

### 2026-05-12 clean-export BBN fixture repair slice

Changed:
- `src/bbn/trading/cpt_init.rs`
- `src/bbn/trading/family_overlay.rs`
- `src/bbn/trading/topology.rs`
- `src/bbn/trading/update.rs`
- `tests/fixtures/policy_training/repo_bbn_trading_cpt_init.json`
- `tests/fixtures/policy_training/repo_bbn_trading_cpt_init_smoothed.json`
- `tests/fixtures/policy_training/repo_bbn_logic_family_overlays.json`

Behavior:
- Unit tests no longer depend on ignored repo-local `state/policy_training`
  files that disappear from a clean release export.
- New fixture files are small, tracked, and do not contain maintainer-local
  absolute paths.
- Runtime BBN CPT and logic-family overlays remain hot-pluggable via the
  existing user state search path; fixture files are test-only and are not
  selected as zero-config consumer defaults.

Evidence:
- `cargo test --manifest-path /tmp/ict-engine-release-export.Fa3UTZ/Cargo.toml bbn::trading -- --nocapture`: failed 3 tests from missing ignored `state/policy_training` fixtures.
- `cargo fmt --check`: passed after fixture repair formatting.
- `cargo test bbn::trading -- --nocapture`: passed, 19 matching tests.
- `cargo clippy --all-targets -- -D warnings`: passed.
- `/tmp` clean export `/tmp/ict-engine-release-export.IWadVv`:
  `cargo test --manifest-path ... bbn::trading -- --nocapture` passed,
  `cargo fmt --manifest-path ... --check` passed, and
  `cargo clippy --manifest-path ... --all-targets -- -D warnings` failed on
  committed-tree-only structural-playbook dead code.

Next:
- Commit the minimal structural-playbook cleanup already present in the working
  tree, then rebuild a clean `/tmp` export from `HEAD` and re-run Clippy there.

### 2026-05-12 clean-export structural-playbook lint slice

Changed:
- `src/application/orchestration/structural_playbook.rs`
- `docs/plans/2026-05-12-hotplug-personal-data-release-handoff-todo.md`

Behavior:
- Removed a stale `paths` duplicate from `StructuralRankedPathSelection`.
- Removed two unused wrapper functions that were absent from runtime callers.
- Runtime and tests use the existing `candidate_paths` field for ranked path
  material.

Evidence:
- `/tmp` clean export `/tmp/ict-engine-release-export.IWadVv` Clippy failed on
  the stale field/wrappers.
- Commit `32858ad` folded in the minimal cleanup.
- `/tmp` clean export `/tmp/ict-engine-release-export.y6Pefh` passed
  `cargo fmt --manifest-path ... --check`,
  `cargo clippy --manifest-path ... --all-targets -- -D warnings`,
  `cargo test --manifest-path ... bbn::trading -- --nocapture`, and
  full `cargo test --manifest-path ...`.

Next:
- Commit the `v0.1.2` release-prep docs/version update.
- Wait for explicit operator confirmation before mirror tag/push/release.

### 2026-05-12 v0.1.2 release-prep slice

Changed:
- `Cargo.toml`
- `Cargo.lock`
- `docs/release-notes-draft.md`
- `docs/audits/release-signoff.md`
- `docs/plans/2026-05-12-hotplug-personal-data-release-handoff-todo.md`

Behavior:
- Version is prepared as `0.1.2` because the release mirror already has
  `v0.1.1`.
- Release notes and signoff describe the hot-plug profile-choice work, clean
  fixture repair, structural-playbook lint cleanup, and clean-export gates.
- Mirror publication remains blocked on explicit operator confirmation for
  `v0.1.2` tag/push/`gh release create`.

Evidence:
- `cargo metadata --locked --format-version 1 --no-deps`: passed after version
  bump.
- `/tmp` clean export `/tmp/ict-engine-release-export.ueDk6B`:
  `cargo fmt --manifest-path ... --check` passed,
  `cargo clippy --manifest-path ... --all-targets -- -D warnings` passed, and
  full `cargo test --manifest-path ...` passed.

Next:
- If operator confirms `v0.1.2`, sync committed `HEAD` into the release mirror
  clone flow without force-push, then tag and create the GitHub release.

### 2026-05-12 local mirror-prep slice

Changed:
- Local clone only: `/tmp/ict-engine-release-mirror-v012.87caSH`
- Source handoff updated with mirror-prep evidence.

Behavior:
- Clean export was synced into a real clone of `Undermybelt/ict-engine-release`
  so the eventual push can be a normal mirror update, not a force push.
- Local mirror commit exists but no local/remote tag was created and nothing was
  pushed.

Evidence:
- `git ls-remote --heads --tags https://github.com/Undermybelt/ict-engine-release.git`: `v0.1.1` exists, no `v0.1.2`.
- `gh auth status`: active `Undermybelt` login with `repo`/`workflow`.
- `find . ... -size +1M`: no files over 1MB in mirror worktree.
- Nested `.git`/state scan: no nested `.git`; only tracked lightweight
  `docs/experiments` files and normal `src/state` source module appeared.
- Secret scan: only code/documentation literals such as env var names and test
  variable names matched; no concrete token/key value found.
- Local mirror commit exists in the mirror worktree; re-read `git -C /tmp/ict-engine-release-mirror-v012.87caSH rev-parse --short HEAD` before any push.

Next:
- After explicit `v0.1.2` confirmation, re-check remote is still at the probed
  base, then push mirror `main`, create tag `v0.1.2`, push tag, and run
  `gh release create`.

### 2026-05-12 closed-loop consumer gate slice

Changed:
- `CLAUDE.md`
- `AGENTS.md`
- `src/application/orchestration/workflow_status.rs`
- `docs/plans/2026-05-12-hotplug-personal-data-release-handoff-todo.md`

Behavior:
- `CLAUDE.md` is only a one-line redirect into `AGENTS.md`.
- `AGENTS.md` is now the shared agent contract for zero-config use, provider
  fallback/priority, privacy isolation, closed-loop order, regime posterior
  surfacing, TimesFM optionality, and release constraints.
- `workflow-status` first-run routing now treats ready default live runtimes as
  live zero-config providers, matching `provider-status`.
- `workflow-status --agent` now surfaces the resolved ensemble posterior active
  regime, posterior confidence, posterior probability map, normalization status,
  and short evidence tail.

Evidence:
- `cargo test application::orchestration::workflow_status::tests::agent_workflow_status_empty_state_uses_explicit_no_state_contract -- --nocapture`: passed.
- `cargo test application::orchestration::workflow_status::tests::agent_and_human_workflow_status_views_prefer_canonical_analyze_ensemble_surface -- --nocapture`: passed.
- `/tmp/ict-engine-closed-loop-smoke-fixed.bmbPSO` ran zero-config workflow/analyze/Pre-Bayes/policy-training/export/update checks listed in the evidence bundle above.
- `cargo fmt --check`, `cargo test --test provider_neutral_cli -- --nocapture`, `cargo test application::orchestration::workflow_status::tests:: -- --nocapture`, and `cargo clippy --all-targets -- -D warnings` passed.

Next:
- No release publish yet. Re-check remote/mirror and run a clean export only
  after the operator explicitly asks to resume release publication.
