# Practical Admission Completion Gate Tracking - 2026-05-28

Owner: Codex
Status: active / objective not complete
Route: `sd/ict-engine-maintenance-loop`

## Objective Slice

The broader objective asks whether factor-training direction and profitability
factor promotion are fully safe through the real `ict-engine` closed loop. This
slice addresses one concrete loophole found in the current tree: unsafe tracked
downstream/gate wrapper surfaces could remain present while the done-definition
audit still reported only skipped heavy gates, leaving completion proof too
weak. Untracked wrapper residue is still reported separately and remains a
dirty-worktree/release-readiness risk, but it is not allowed to fail the tracked
source release gate by itself.

## Fresh Evidence

- `python3 support/scripts/factor_claim_terminalization_audit.py --compact`
  reported `status=pass`, `active_claims=0`, `live_factor_processes=0`,
  `promotion_allowed_true=0`, and `trade_usable_true=0`.
- `/tmp/ict-engine-goal-20260528-codex-current-snapshot/objective_closure_snapshot.json`
  reported `summary.status=not_complete` with blockers
  `done_definition_not_completion_ready`,
  `same_tree_practical_closure_unproven`, and `release_readiness_blocked`.
- `python3 support/scripts/release_readiness_audit.py --compact --check-remotes`
  still failed `worktree_clean_for_release`,
  `source_origin_matches_selected_source`, and `release_version_tag_available`.
- Earlier full practical-admission source scan over `913` `run_*.py` wrappers
  found `115` violating files and `193` violations:
  `practical_flag_without_extension_complete_guard=62`,
  `five_bps_survival_uses_trade_density_floor=82`, and
  `downstream_admission_uses_2bps_survivor_gate=49`.
- Current tracked-source readback from
  `/tmp/ict-engine-goal-20260528-codex-done-current-full.json` scanned `915`
  wrappers: `tracked_scanned_files=28`, `tracked_violation_count=0`,
  `untracked_scanned_files=887`, and `untracked_violation_count=193`. This
  means the committed-source gate is clean while untracked wrapper residue must
  still be handled by worktree isolation or explicit cleanup.

## Loophole

The existing scanner
`support/scripts/research/downstream_practical_admission_source_check.py` could
find unsafe practical-admission wrappers, but `done_definition_audit.py` did not
run it. That allowed a future closure packet to look cleaner than the tracked
source wrapper surface: heavy gates could be the only visible done-definition
gap while committed wrappers still mapped local admission strings, 2bps
survivors, or trade-density predicates into practical downstream readiness.

## Implemented Fix

`support/scripts/done_definition_audit.py` now includes a lightweight
`practical_admission_source_surface` gate. It scans
`support/docs/experiments/actionable-regime-confidence/scripts/run_*.py`
wrappers with the existing source checker, splits tracked versus untracked
files with `git ls-files`, and fails the done-definition audit only when unsafe
patterns remain in tracked source.

This intentionally does not mass-edit untracked historical wrappers in one
broad slice. It makes the committed-source objective fail closed if tracked
wrappers regress, while leaving untracked wrapper violations visible as residue
that must be excluded from release or cleaned in narrower verified fixes.

## Verification

- `python3 -m unittest support.scripts.tests.test_done_definition_audit -v`
  passed `19/19`.
- `python3 -m unittest support.scripts.research.tests.test_downstream_practical_admission_source_check -v`
  passed `12/12`.
- `python3 -m unittest support.scripts.tests.test_objective_closure_snapshot -v`
  passed `20/20` on rerun.
- `python3 support/scripts/done_definition_audit.py --output /tmp/ict-engine-goal-20260528-codex-done-current-full.json`
  reported `practical_admission_source_surface.status=pass` because
  `tracked_violation_count=0`; it still exposed `untracked_violation_count=193`.
- `python3 support/scripts/objective_closure_snapshot.py --compact --check-remotes --output-dir /tmp/ict-engine-goal-20260528-codex-after-tracked-practical`
  remained `summary.status=not_complete` with blockers
  `done_definition_not_completion_ready`, `factor_closure_blocked`, and
  `release_readiness_blocked`. The factor child had `active_claims=2`,
  `live_factor_processes=2`, `promotion_allowed_true=0`, and
  `trade_usable_true=0`; release readiness still failed
  `worktree_clean_for_release`, `source_origin_matches_selected_source`, and
  `release_version_tag_available`.

## Current Verdict

The full objective is still not complete. The current improvement makes the
completion audit more truthful for committed source and prevents tracked unsafe
practical-admission wrappers from being hidden behind partial/skipped
done-definition evidence. Remaining work is to keep untracked violating wrappers
out of release/source claims, produce a same-tree practical closure packet with
a genuinely trade-usable factor, clear live factor runtimes, and clear
release/readiness gates from a clean selected source slice.
