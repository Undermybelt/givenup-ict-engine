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
