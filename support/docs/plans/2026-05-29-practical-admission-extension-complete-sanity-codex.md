# Practical Admission Extension-Complete Sanity Tracking

- created_at: `2026-05-29T21:51:19+0800`
- owner: `codex`
- route: `sd/ict-engi-fact-rese-muta`
- repo: `/Users/thrill3r/projects-ict-engine/ict-engine`
- branch: `main`
- status: `terminal_fix_verified_broad_objective_not_complete`
- promotion_allowed: `false`
- trade_usable: `false`
- update_goal: `false`

## Current Answer

No. I do not have 100% confidence that the full objective is complete.

Latest same-turn evidence:

- `python3 support/scripts/factor_claim_terminalization_audit.py --compact`
  returned `status=needs_attention`.
- Current factor closure has two fresh active claims, no live factor process,
  `promotion_allowed_true=0`, `trade_usable_true=0`, and
  `same_tree_practical_closure=null`.
- `python3 support/scripts/objective_closure_snapshot.py --compact --check-remotes`
  returned `status=not_complete` with done-definition, factor-closure, and
  release-readiness blockers.

## Loophole Found

`support/scripts/research/downstream_practical_admission_source_check.py`
already blocks many unsafe practical flag assignments. It requires wrappers to
route `promotion_allowed`, `trade_usable`, and `update_goal` through
`practical_admission_flags(...)`, and that helper must combine
`branch_local_admitted` with `extension_complete`.

The remaining gap is that the static checker trusts any caller-provided
`extension_complete` argument. A downstream wrapper could pass
`extension_complete=True` or copy `bool(metrics.get("extension_complete"))`
from a prior local metrics file, then convert branch-local admission into
practical flags without proving same-tree practical closure.

That is not sufficient for the full objective. `extension_complete` is a
practical lifecycle proof, not a local wrapper convenience flag. Until a source
path proves the validated practical closure packet, wrapper-local positive
extension signals must fail closed.

## Fix Boundary

Canonical owner:

- `support/scripts/research/downstream_practical_admission_source_check.py`

Regression surface:

- `support/scripts/research/tests/test_downstream_practical_admission_source_check.py`

Required behavior:

- Omitted `extension_complete` remains safe because the helper default is
  `False`.
- Explicit `extension_complete=False` remains safe.
- `extension_complete=True` is unsafe.
- `extension_complete=bool(metrics.get("extension_complete"))` is unsafe
  because it reuses local wrapper output/readback instead of proving practical
  closure.
- Direct-return helper calls such as
  `return practical_admission_flags(..., extension_complete=True)` are unsafe;
  the checker must not only inspect assignment RHS calls.

## TDD Route

- Mode: `auto`
- Decision: `strict`
- Reason: shared static gate that protects practical/trade-use semantics.
- Verification: focused RED/GREEN unit tests, practical admission checker tests,
  done-definition consumer tests, and objective snapshot readback.

## Progress Log

- 2026-05-29T21:51:19+0800: Created tracking doc before production edits.
- 2026-05-29T21:52 +0800: RED confirmed two new tests failed because
  `downstream_practical_admission_source_check.py` accepted hardcoded
  `extension_complete=True` and
  `extension_complete=bool(metrics.get("extension_complete"))`.
- 2026-05-29T21:58 +0800: Implemented the static gate at the helper-call owner.
  `practical_admission_flags(...)` calls now allow omitted
  `extension_complete` and explicit `False`; any positive/local expression is
  flagged with
  `extension_complete_without_validated_practical_closure_source`.
- 2026-05-29T22:03 +0800: GREEN verification:
  `python3 -m unittest support.scripts.research.tests.test_downstream_practical_admission_source_check -v`
  -> `Ran 30 tests`, `OK`.
- 2026-05-29T22:03 +0800: Consumer regressions:
  `python3 -m unittest support.scripts.tests.test_done_definition_audit -v`
  -> `Ran 31 tests`, `OK`;
  `python3 -m unittest support.scripts.tests.test_objective_closure_snapshot -v`
  -> `Ran 42 tests`, `OK`.
- 2026-05-29T22:03 +0800: `python3 support/scripts/done_definition_audit.py --compact`
  returned `status=pass` but `completion_ready=false` because heavy gates were
  skipped. The stricter scanner surfaced `270` untracked practical-admission
  violations across `155` untracked files, including `2` new
  `extension_complete_without_validated_practical_closure_source` violations.
- 2026-05-29T22:06 +0800:
  `python3 support/scripts/objective_closure_snapshot.py --compact` returned
  `status=not_complete`. Blockers included
  `practical_admission_source_debt`, `factor_closure_blocked`,
  `release_readiness_blocked`, and `release_remote_checks_not_run`.
- 2026-05-29T22:28 +0800: After reviewing and updating the quarantine packet,
  `python3 support/scripts/objective_closure_snapshot.py --compact` still
  returned `status=not_complete`, now with
  `quarantined_practical_admission_source_debt` recorded instead of an
  unreviewed debt blocker. Remaining blockers were
  `done_definition_not_completion_ready`, `factor_closure_blocked`,
  `release_readiness_blocked`, and `release_remote_checks_not_run`.
- 2026-05-29T22:57 +0800: Follow-up audit found a second bypass: the helper
  argument check only ran when `practical_admission_flags(...)` appeared in an
  assignment or annotated assignment. RED:
  `python3 -m unittest support.scripts.research.tests.test_downstream_practical_admission_source_check.DownstreamPracticalAdmissionSourceCheckTests.test_flags_returned_true_extension_complete_helper_call -v`
  failed because direct-return `extension_complete=True` was accepted.
- 2026-05-29T22:58 +0800: Moved the extension argument check to generic
  `visit_Call`, so any helper-call location is scanned once. GREEN single-test
  rerun passed.
- 2026-05-29T22:59 +0800: Full focused verification after the follow-up fix:
  `python3 -m unittest support.scripts.research.tests.test_downstream_practical_admission_source_check -v`
  -> `Ran 31 tests`, `OK`; consumer regressions
  `python3 -m unittest support.scripts.tests.test_done_definition_audit support.scripts.tests.test_objective_closure_snapshot -v`
  -> `Ran 74 tests`, `OK`.
- 2026-05-29T23:00 +0800: `python3 support/scripts/done_definition_audit.py --compact`
  still reported `status=pass` with `completion_ready=false` because heavy
  gates were skipped. Tracked practical-admission violations remained `0`;
  quarantined untracked practical-admission debt remained `270` violations
  across `155` files and quarantined await-launch debt remained `46` violations
  across `46` files.
- 2026-05-29T22:58 +0800: Remote-checked parent snapshot at
  `/tmp/ict-engine-goal-20260529-codex-resume-current-remote/objective_closure_snapshot.json`
  returned `status=not_complete`. Remote gates were no longer skipped;
  release blockers were `worktree_clean_for_release` and
  `source_origin_matches_selected_source`.
- 2026-05-29T23:12 +0800: Follow-up scanner audit found that untracked fail-
  closed wrappers using module-level constants such as
  `PROMOTION_ALLOWED_DEFAULT = False` were being counted as practical-admission
  debt. RED/GREEN added coverage for module-level false aliases and
  reassignment invalidation. Verification:
  `python3 -m unittest support.scripts.research.tests.test_downstream_practical_admission_source_check -v`
  -> `Ran 34 tests`, `OK`; consumer regressions
  `python3 -m unittest support.scripts.tests.test_done_definition_audit support.scripts.tests.test_objective_closure_snapshot -v`
  -> `Ran 74 tests`, `OK`.
- 2026-05-29T23:12 +0800: `python3 support/scripts/done_definition_audit.py --compact`
  still reported tracked practical-admission violations `0` and
  `completion_ready=false` because heavy gates were skipped. After the false-
  alias fix, quarantined untracked practical-admission debt became `260`
  violations across `145` files with fingerprint
  `c2c70a41ab24da8ad9a621e0d130bc8e0ef0773b67e39eb497bdfbe35b7a9145`.
- 2026-05-29T23:35 +0800: Root-cause review of the repeated "near practical but
  not trade usable" failure identified another leak class: retired telemetry
  fields such as `transition_hazard` / `hybrid_transition_hazard` and
  `pda_hybrid_alignment` were still being surfaced or templated as if they were
  practical gates in some readback/intake paths. The current fix removes those
  fields from execution-candidate and blocker-report practical surfaces, keeps
  PA intake from encoding them as strict gates, and extends the practical source
  checker to flag retired PDA/transition-hazard policy templates. Focused
  verification passed:
  `python3 -m unittest support.scripts.research.tests.test_downstream_practical_admission_source_check support.scripts.research.tests.test_pa_agent_intake support.scripts.research.tests.test_factor_lifecycle_migration_readback support.scripts.research.tests.test_regime_root_survivor_blocker_report -v`
  -> `Ran 64 tests`, `OK`; consumer regressions
  `python3 -m unittest support.scripts.tests.test_done_definition_audit support.scripts.tests.test_objective_closure_snapshot -v`
  -> `Ran 74 tests`, `OK`; `cargo test same_root_trace_admission_does_not_surface_retired_telemetry_as_candidate_gate -- --nocapture`
  -> `1 passed`. `git diff --check` passed. `python3 support/scripts/done_definition_audit.py --compact`
  still reported tracked practical-admission violations `0`, but the reviewed
  untracked practical-admission quarantine increased to `343` violations across
  `177` files with fingerprint
  `dfbbed2f538d37a573e872caeffc4b13ba31af8707b110e0c4c662433cab8669` because
  the scanner now catches more unsafe retired-field templates. This is not
  completion evidence; it is exposed untracked debt.

## Current Remaining Gaps

- The full objective remains unproven and active.
- No validated `same_tree_practical_closure` packet exists.
- Latest factor closure remains blocked by fresh active claims and has no
  `promotion_allowed=true` / `trade_usable=true` evidence. As of the latest
  objective snapshot in this slice, the fresh claims were
  `20260529T224418+0800-codex-micro-index-session-trendpullback-rvol-screen.claim`
  and
  `20260529T224555+0800-codex-nq-compound-rrr-chopfilter-practical-validation.claim`.
- The practical-admission source debt is quarantined as untracked unsafe wrapper
  debt only. Latest reviewed quarantine is `343` violations across `177`
  untracked files. It is not release-ready or trade-usable evidence.
- Heavy done-definition gates have not been run for this current `HEAD`.
- Remote release checks have now run and passed readback, but release readiness
  still fails on dirty selected source and source-origin mismatch.

## Terminal Slice Decision

- This slice closes one verified source-audit loophole: practical-admission
  wrappers can no longer pass hardcoded, locally read back, or direct-returned
  positive `extension_complete` into `practical_admission_flags(...)` without
  being flagged by the source checker.
- This slice also removes a false-positive class: fail-closed module-level
  aliases to literal `False` are safe unless reassigned, so the checker no
  longer inflates practical source debt for wrappers that only emit false
  practical flags.
- This slice also blocks stale retired PDA/transition policy templates from
  re-entering practical admission while preserving explicit false telemetry
  markers as observation-only fields.
- This slice does not close the full user objective. Keep
  `promotion_allowed=false`, `trade_usable=false`, and `update_goal=false` until
  a same-tree practical closure packet, current heavy done-definition proof,
  clean release-readiness proof, and truthful completion commit all exist for
  the same current state.

## 2026-05-30T00:15+0800 Canonical Closure Producer Slice

Root cause handled in this slice:

- The strict same-tree practical closure validator lived in
  `support/scripts/factor_claim_terminalization_audit.py`, but wrappers could
  still hand-write `same-tree-practical-closure/v1` packets. That kept producer
  semantics separate from validator semantics and allowed recurring "near
  practical" states to drift toward fake promotion surfaces.

Changes made:

- Added `support/scripts/research/same_tree_practical_closure.py` as the single
  canonical builder/validator for `same-tree-practical-closure/v1` packets.
- Changed `factor_claim_terminalization_audit.py` to validate evidence packets
  through `metrics_prove_same_tree_practical_closure(...)` from that helper.
- Extended `downstream_practical_admission_source_check.py` so manual
  same-tree practical closure packet writers are flagged as
  `manual_same_tree_practical_closure_packet_writer`; only the canonical helper
  source is allowed to construct the schema directly.
- Updated the NQ bidirectional opening-drive exact downstream wrapper to call
  `write_same_tree_practical_closure_packet(...)` and keep local readiness
  separate from practical flags. Branch-local admission can be true, but
  `promotion_allowed`, `trade_usable`, and `update_goal` remain false unless the
  full lifecycle packet passes the canonical helper.
- Added script inventory entries for the canonical helper in
  `support/scripts/SCRIPTS.md` and `support/scripts/script_manifest.json`.

Verification:

- `python3 -m unittest support.scripts.research.tests.test_same_tree_practical_closure support.scripts.tests.test_factor_claim_terminalization_audit support.scripts.research.tests.test_downstream_practical_admission_source_check -v`
  -> `Ran 134 tests`, `OK`.
- `python3 -m unittest support.docs.experiments.actionable-regime-confidence.scripts.test_tomac_nq_bidir_opening_drive_exact_downstream_v1 -v`
  -> `Ran 11 tests`, `OK`.
- `python3 support/scripts/check_script_manifest.py`
  -> `script_manifest status=pass entries=32`.
- `python3 -m py_compile support/scripts/research/same_tree_practical_closure.py support/scripts/factor_claim_terminalization_audit.py support/docs/experiments/actionable-regime-confidence/scripts/run_tomac_nq_bidir_opening_drive_exact_downstream_v1.py`
  -> pass.
- `python3 -m unittest support.scripts.tests.test_done_definition_audit support.scripts.tests.test_objective_closure_snapshot -v`
  -> `Ran 74 tests`, `OK`.
- `python3 support/scripts/done_definition_audit.py --compact --practical-admission-source-timeout-seconds 240`
  -> `status=pass`, `completion_ready=false`, heavy gates skipped. Tracked
  practical-admission violations remained `0`, but untracked debt drifted in
  the shared worktree while scanning.
- `python3 support/scripts/objective_closure_snapshot.py --compact --timeout-seconds 240 --output-dir /tmp/ict-engine-goal-20260530-codex-closure-producer-slice`
  -> `status=not_complete`. Blockers included skipped heavy done-definition
  gates, unquarantined/drifting untracked practical-admission debt, fresh active
  claims, dirty release worktree, and skipped remote release checks.
- `git diff --check` -> pass.

Current truth after this slice:

- No `same_tree_practical_closure` packet is validated.
- `promotion_allowed_true=0`, `trade_usable_true=0` in factor closure.
- Factor closure is blocked by fresh active claims with no live factor process;
  latest objective snapshot saw 3 fresh active claims.
- The full user objective remains incomplete. This slice removes a producer /
  validator drift class; it does not produce a practical/live-usable factor.

## 2026-05-30T00:40+0800 Canonical Helper Path Spoof Guard

Root cause handled in this slice:

- `support/scripts/research/downstream_practical_admission_source_check.py`
  treated any file named `same_tree_practical_closure.py` as the canonical
  closure helper. An arbitrary same-named file outside
  `support/scripts/research/` could hand-write a
  `same-tree-practical-closure/v1` packet and bypass the manual packet writer
  gate.

Changes made:

- Added an exact canonical helper path check for
  `support/scripts/research/same_tree_practical_closure.py`.
- Kept non-canonical same-named helpers fail-closed as
  `manual_same_tree_practical_closure_packet_writer`.
- Added regression coverage for a temporary external file named
  `same_tree_practical_closure.py` that tries to emit a pass packet manually.

Verification:

- RED before the fix: the new regression expected a violation but the checker
  returned `ok=true`.
- GREEN focused rerun:
  `python3 -m unittest support.scripts.research.tests.test_downstream_practical_admission_source_check.DownstreamPracticalAdmissionSourceCheckTests.test_flags_same_named_closure_helper_outside_canonical_path support.scripts.research.tests.test_downstream_practical_admission_source_check.DownstreamPracticalAdmissionSourceCheckTests.test_allows_canonical_same_tree_practical_closure_builder_call -v`
  -> `OK`.
- Broader focused rerun:
  `python3 -m unittest support.scripts.research.tests.test_downstream_practical_admission_source_check support.scripts.research.tests.test_same_tree_practical_closure -v`
  -> `Ran 46 tests`, `OK`.
- Current same-turn factor audit:
  `python3 support/scripts/factor_claim_terminalization_audit.py --compact`
  -> `status=needs_attention`, `active_claims=4`,
  `live_factor_processes=0`, `promotion_allowed_true=0`,
  `trade_usable_true=0`, `same_tree_practical_closure=null`.

Current truth after this slice:

- No new provider/AQ/IBKR/factor launch is safe while the four active claims
  are fresh.
- The full user objective remains incomplete. This slice closes another fake
  practical-closure producer bypass; it does not create a live-usable factor.

## 2026-05-30T00:36+0800 Deploy-Ready Contract Slice

Root cause handled in this slice:

- The canonical same-tree practical closure packet required the practical
  lifecycle tuple, but the schema did not explicitly separate deploy-ready
  evidence from funded live-fill evidence. That left a semantic drift path where
  a future wrapper could either require a funded live fill before `deploy_ready`
  or accept a packet whose practical closure depends on funded live execution
  rather than the backtest, Auto-Quant, provider, and paper/sim execution chain.

Changes made:

- Added the explicit readiness contract
  `deploy_ready_from_backtest_autoquant_provider_or_paper_sim_execution_chain_not_funded_fill`
  in `support/scripts/research/same_tree_practical_closure.py`.
- The canonical builder now emits `deploy_ready=true`,
  `funded_live_fill_required=false`, and the readiness contract string.
- The canonical validator now requires the same fields both at top level and in
  `policy_training_summary.factor_profitability_lifecycle`, including a positive
  `deploy_ready_count`.
- `factor_claim_terminalization_audit.py` now rejects otherwise-positive
  closure packets that require funded live fill.

Verification:

- `python3 -m unittest support.scripts.research.tests.test_same_tree_practical_closure -v`
  -> `Ran 6 tests`, `OK`.
- `python3 -m unittest support.scripts.tests.test_factor_claim_terminalization_audit -v`
  -> `Ran 92 tests`, `OK`.
- `python3 -m unittest support.scripts.research.tests.test_downstream_practical_admission_source_check -v`
  -> `Ran 40 tests`, `OK`.
- `python3 -m unittest support.scripts.tests.test_done_definition_audit support.scripts.tests.test_objective_closure_snapshot -v`
  -> `Ran 74 tests`, `OK`.
- `git diff --check` -> pass.
- `python3 support/scripts/objective_closure_snapshot.py --compact --check-remotes --output-dir /tmp/ict-engine-goal-20260530-codex-deploy-ready-contract-current --timeout-seconds 300`
  -> `status=not_complete`; evidence packet:
  `/tmp/ict-engine-goal-20260530-codex-deploy-ready-contract-current/objective_closure_snapshot.json`.

Current truth after this slice:

- No validated `same_tree_practical_closure` packet exists.
- Factor closure still reports `promotion_allowed_true=0`,
  `trade_usable_true=0`, and `same_tree_practical_closure=null`.
- Factor closure is blocked by three active claims and zero live factor
  processes. Latest objective snapshot named two fresh wait-only claims and one
  fresh active claim without live runtime.
- Done-definition remains `completion_ready=false` because heavy gates were
  skipped and current untracked practical-admission debt is not matched by the
  reviewed quarantine.
- Release readiness remains blocked by dirty selected source and release mirror
  `remote_readback` failure; origin remote readback passed.
- The full user objective remains incomplete. This slice hardens deploy-ready
  closure semantics; it does not create a practical/live-usable factor.

## 2026-05-30T00:47+0800 Practical Source Debt Quarantine Refresh

Root cause handled in this slice:

- Current scans reported the same untracked practical-admission wrapper debt as
  a reviewed alternative fingerprint, but the quarantine manifest still carried
  the older `343` violations across `177` files count. Because count/file totals
  are part of the quarantine contract, objective closure correctly treated the
  current `337` violations across `176` files scan as unquarantined debt.

Changes made:

- Refreshed `support/docs/audits/practical-admission-source-debt-quarantine.json`
  to the current reviewed untracked debt fingerprint:
  `9945631cb78ac92c5ec7037781c73c1e37a87eb791b03f80175ff1690b2e05f3`.
- Kept prior reviewed fingerprints as alternatives because the shared untracked
  wrapper residue has been drifting while tracked practical-admission violations
  remain zero.
- Preserved `promotion_allowed=false`, `trade_usable=false`, and
  `update_goal=false`; this quarantine externalizes untracked scratch debt only.

Verification:

- `python3 support/scripts/done_definition_audit.py --compact --output /tmp/ict-engine-done-definition-quarantine-match-af850fad.json`
  -> `status=pass`, `completion_ready=false`,
  practical-admission source quarantine `matched=true`,
  `tracked_violation_count=0`, `untracked_violation_count=337`,
  `untracked_violating_files=176`.
- `python3 support/scripts/objective_closure_snapshot.py --compact --check-remotes --output-dir /tmp/ict-engine-goal-20260530-codex-quarantine-match-after-af850fad --timeout-seconds 300`
  -> `status=not_complete`, blocker count `3`; practical-admission debt is now
  recorded under `quarantined_practical_admission_source_debt`, not as an active
  blocker.
- `git diff --check` -> pass.

Current truth after this slice:

- No validated `same_tree_practical_closure` packet exists.
- Factor closure remains blocked by fresh active claims; latest objective
  snapshot named two fresh active claims and zero live factor processes.
- Done-definition remains `completion_ready=false` because heavy gates were
  skipped.
- Release readiness remains blocked by dirty selected source and source-origin
  mismatch, though both remotes passed readback in the latest snapshot.
- The full user objective remains incomplete. This slice only makes the current
  untracked practical-admission debt quarantine internally consistent.

## 2026-05-30T01:00+0800 Timed-Out Command Result Closure Guard

Root cause handled in this slice:

- `same_tree_practical_closure` required `all_command_exits_zero=true`, but the
  canonical per-command proof only checked `exit == 0`. A command row such as
  `{\"exit\": 0, \"timed_out\": true}` could therefore satisfy the practical
  closure helper even though the underlying command did not complete cleanly.

Changes made:

- Added a regression test proving that a timed-out command result is rejected
  even when the recorded exit code is zero.
- Updated `support/scripts/research/same_tree_practical_closure.py` so every
  command result must have `exit == 0` and must not report `timed_out=true`.
- Updated the runtime factor-research skill so future practical-closure work
  treats timed-out command rows as failed evidence, not as zero-exit proof.

Verification:

- `python3 -m unittest support.scripts.research.tests.test_same_tree_practical_closure.SameTreePracticalClosureTests.test_rejects_timed_out_command_result_even_when_exit_zero -v`
  -> `OK`.
- `python3 -m unittest support.scripts.research.tests.test_same_tree_practical_closure support.scripts.tests.test_factor_claim_terminalization_audit -v`
  -> `Ran 99 tests`, `OK`.
- `python3 -m py_compile support/scripts/research/same_tree_practical_closure.py`
  -> pass.

Current truth after this slice:

- No validated `same_tree_practical_closure` packet exists.
- Latest compact factor audit still reports `promotion_allowed_true=0`,
  `trade_usable_true=0`, and `same_tree_practical_closure=null`.
- Fresh active claims still block new provider/AQ/lifecycle launches; this slice
  hardens a false-positive closure path and does not create a practical/live
  usable factor.

## 2026-05-30T01:17+0800 Explicit Non-Timeout Command Proof Guard

Root cause handled in this slice:

- The previous timed-out command guard rejected `timed_out=true`, but a command
  row with `exit == 0` and no `timed_out` field still satisfied the canonical
  practical-closure helper. That left a weaker marker path where missing timeout
  evidence could be mistaken for completed command evidence.

Changes made:

- Added producer-level and audit-consumer regression tests for command rows that
  omit explicit non-timeout proof.
- Updated `support/scripts/research/same_tree_practical_closure.py` so every
  command result must have `exit == 0` and explicit `timed_out=false`.
- Updated the runtime factor-research skill so future practical-closure work
  requires explicit non-timeout command proof rather than merely the absence of
  `timed_out=true`.

Verification:

- `python3 -m unittest support.scripts.research.tests.test_same_tree_practical_closure.SameTreePracticalClosureTests.test_rejects_command_result_without_explicit_non_timeout_proof -v`
  -> failed before the fix, then `OK` after the fix.
- `python3 -m unittest support.scripts.tests.test_factor_claim_terminalization_audit.FactorClaimTerminalizationAuditTest.test_build_report_rejects_closure_packet_without_explicit_non_timeout_proof -v`
  -> failed before the fix, then `OK` after the fix.

Current truth after this slice:

- No validated `same_tree_practical_closure` packet exists.
- Latest compact factor audit still reports `promotion_allowed_true=0`,
  `trade_usable_true=0`, and `same_tree_practical_closure=null`.
- The remaining active claim has not yet crossed the one-hour stale-takeover
  window, so this slice only closes another false-positive practical-closure
  path and does not create a practical/live usable factor.

## 2026-05-30T01:22+0800 Live-Process Readback Classifier Guard

Root cause handled in this slice:

- The factor claim audit live-process classifier treated a bare readback command
  such as `find ... -name run_tomac_*ym*py -print` as a live factor process
  because the command referenced a `run_tomac_*.py` filename before the
  readback filter rejected search-only commands.
- This could create a false `live_factor_processes > 0` blocker and obscure the
  real factor-closure state.

Changes made:

- Updated `support/scripts/factor_claim_terminalization_audit.py` so bare
  `find` readbacks are filtered with `rg`/`grep` before factor wrapper matching.
- Added
  `FactorClaimTerminalizationAuditTest.test_live_process_classifier_ignores_bare_find_readback_commands`.
- Updated the local ict-engine maintenance runtime skill so future agents treat
  grep/sed/rg/find readbacks as non-owner command-introspection probes.

Verification:

- `python3 -m unittest support.scripts.tests.test_factor_claim_terminalization_audit.FactorClaimTerminalizationAuditTest.test_live_process_classifier_ignores_bare_find_readback_commands -v`
  -> failed before the fix with `AssertionError: True is not false`, then `OK`
  after the fix.
- `python3 -m unittest support.scripts.tests.test_factor_claim_terminalization_audit -v`
  -> `Ran 94 tests`, `OK`.
- `python3 support/scripts/factor_claim_terminalization_audit.py --compact`
  -> `live_factor_processes=0`, `fresh_active_claims_without_live_process=1`,
  `promotion_allowed_true=0`, `trade_usable_true=0`,
  `same_tree_practical_closure=null`.

Current truth after this slice:

- No validated `same_tree_practical_closure` packet exists.
- Factor closure is still not complete: one active NQ screen claim remains fresh
  and unterminalized, with `promotion_allowed_true=0`, `trade_usable_true=0`,
  and `same_tree_practical_closure=null`.
- This slice removes a false live-runtime blocker; it does not create a
  practical/live usable factor.

## 2026-05-30T01:24+0800 Closure Command Stage Coverage Guard

Root cause handled in this slice:

- The canonical practical-closure helper still accepted an aggregate command row
  such as `{"name": "all", "exit": 0, "timed_out": false}`. That row proves
  only a summary flag, not that provider/data, Pre-Bayes, BBN/workflow,
  CatBoost/path-ranker, execution tree, feedback/update, and policy training
  each executed successfully in the same rooted branch.
- A single command name containing every stage keyword could also satisfy a
  naive substring coverage check, so each required stage must be backed by a
  distinct command result row.

Changes made:

- Added producer-level regression tests rejecting aggregate command evidence
  and single-row keyword spoofing.
- Added stage coverage requirements to
  `support/scripts/research/same_tree_practical_closure.py`: command evidence
  must contain distinct zero-exit, `timed_out=false` rows covering provider/data,
  Pre-Bayes, BBN/workflow, CatBoost/path-ranker, execution tree,
  feedback/update, and policy training.
- Updated the audit-consumer valid fixture to use stage-level command evidence
  instead of `name=all`.

Verification:

- `python3 -m unittest support.scripts.research.tests.test_same_tree_practical_closure.SameTreePracticalClosureTests.test_rejects_aggregate_command_result_without_step_coverage -v`
  -> failed before the fix, then `OK` after the fix.
- `python3 -m unittest support.scripts.research.tests.test_same_tree_practical_closure.SameTreePracticalClosureTests.test_rejects_single_command_name_spoofing_every_required_stage -v`
  -> failed before the second-stage fix, then `OK` after the fix.
- `python3 -m unittest support.scripts.research.tests.test_same_tree_practical_closure support.scripts.tests.test_factor_claim_terminalization_audit -v`
  -> `Ran 104 tests`, `OK`.
- `git diff --check -- support/scripts/research/same_tree_practical_closure.py support/scripts/research/tests/test_same_tree_practical_closure.py support/scripts/factor_claim_terminalization_audit.py support/scripts/tests/test_factor_claim_terminalization_audit.py support/docs/plans/2026-05-29-practical-admission-extension-complete-sanity-codex.md`
  -> pass.

Current truth after this slice:

- No validated `same_tree_practical_closure` packet exists.
- Practical closure remains blocked by current `/tmp` claim/runtime state. The
  latest compact audit reported `active_claims=3`,
  `fresh_active_claims_without_live_process=2`, `live_factor_processes=1`,
  `promotion_allowed_true=0`, `trade_usable_true=0`, and
  `same_tree_practical_closure=null`.
- Release readiness remains blocked by `worktree_clean_for_release` and
  `remote_readback`.
- This slice closes another false-positive practical-closure path; it does not
  create a practical/live usable factor.

## 2026-05-30T01:41+0800 Explicit Command Stage Schema Guard

Root cause handled in this slice:

- The prior stage-coverage guard required distinct command rows, but still
  inferred lifecycle stage coverage from command-name keywords.
- Seven successful rows with good-looking names and no explicit stage field
  could therefore pass the canonical same-tree practical closure validator.
- Command names are readback labels, not structured proof of which lifecycle
  stage ran.

Changes made:

- `support/scripts/research/same_tree_practical_closure.py` now requires every
  practical closure `command_results` row to carry one explicit `stage` value
  from this exact set: `provider_data`, `pre_bayes`, `bbn_workflow`,
  `path_ranker`, `execution_tree`, `feedback_update`, and `policy_training`.
- The validator still requires one row for each stage, `exit == 0`, explicit
  `timed_out=false`, and a nonempty command name for readback.
- Updated producer and consumer test fixtures to use explicit stage values.
- Updated the runtime factor-research skill so future packet producers do not
  rely on command-name inference.

TDD evidence:

- Added a failing regression test proving that seven command rows with names
  covering the lifecycle but no explicit `stage` field were previously accepted.
- After the fix, the same regression rejects the packet and the producer helper
  suite passes.

Current truth after this slice:

- No validated `same_tree_practical_closure` packet exists.
- Current compact factor audit still reports `promotion_allowed_true=0`,
  `trade_usable_true=0`, and `same_tree_practical_closure=null`.
- This slice closes another false-positive practical-closure path; it does not
  create a practical/live usable factor.
