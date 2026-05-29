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
  debt only. Latest reviewed quarantine is `260` violations across `145`
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
- This slice does not close the full user objective. Keep
  `promotion_allowed=false`, `trade_usable=false`, and `update_goal=false` until
  a same-tree practical closure packet, current heavy done-definition proof,
  clean release-readiness proof, and truthful completion commit all exist for
  the same current state.
