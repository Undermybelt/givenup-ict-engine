# Practical Admission Completion Gate Tracking - 2026-05-28

Owner: Codex
Status: active / objective not complete
Route: `sd/ict-engi-fact-rese-muta`

## Objective Slice

The broader objective asks whether factor-training direction and profitability
factor promotion are fully safe through the real `ict-engine` closed loop. This
slice addresses one concrete loophole found in the current tree: unsafe
downstream/gate wrapper surfaces could remain present while the done-definition
audit still reported only skipped heavy gates, leaving completion proof too
weak.

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
- Full practical-admission source scan over `913` `run_*.py` wrappers found
  `115` violating files and `193` violations:
  `practical_flag_without_extension_complete_guard=62`,
  `five_bps_survival_uses_trade_density_floor=82`, and
  `downstream_admission_uses_2bps_survivor_gate=49`.

## Loophole

The existing scanner
`support/scripts/research/downstream_practical_admission_source_check.py` could
find unsafe practical-admission wrappers, but `done_definition_audit.py` did not
run it. That allowed a future closure packet to look cleaner than the actual
wrapper surface: heavy gates could be the only visible done-definition gap while
historical wrappers still mapped local admission strings, 2bps survivors, or
trade-density predicates into practical downstream readiness.

## Implemented Fix

`support/scripts/done_definition_audit.py` now includes a lightweight
`practical_admission_source_surface` gate. It scans all
`support/docs/experiments/actionable-regime-confidence/scripts/run_*.py`
wrappers with the existing source checker and fails the done-definition audit
when unsafe practical-admission source patterns remain.

This intentionally does not mass-edit historical wrappers in one broad slice.
It makes the objective fail closed until those wrapper violations are retired or
quarantined by narrower verified fixes.

## Verification

- `python3 -m unittest support.scripts.tests.test_done_definition_audit -v`
  passed `18/18`.
- `python3 -m unittest support.scripts.research.tests.test_downstream_practical_admission_source_check -v`
  passed `12/12`.
- `python3 -m unittest support.scripts.tests.test_objective_closure_snapshot -v`
  passed `20/20` on rerun.
- `python3 support/scripts/done_definition_audit.py --compact --output /tmp/ict-engine-goal-20260528-done-after-admission-gate.json`
  failed closed as intended with unresolved
  `practical_admission_source_surface`, `scanned_files=913`,
  `violating_files=115`, and `violation_count=193`.
- `python3 support/scripts/objective_closure_snapshot.py --compact --check-remotes --output-dir /tmp/ict-engine-goal-20260528-after-practical-admission-gate`
  remained `summary.status=not_complete`. The done-definition child now reports
  `status=needs_fix`, `unresolved=[practical_admission_source_surface]`; the
  factor child is claim/process clear but still has `promotion_allowed_true=0`
  and `trade_usable_true=0`; release readiness still fails
  `worktree_clean_for_release`, `source_origin_matches_selected_source`, and
  `release_version_tag_available`.

## Current Verdict

The full objective is still not complete. The current improvement makes the
completion audit more truthful and prevents unsafe practical-admission wrappers
from being hidden behind partial/skipped done-definition evidence. Remaining
work is to retire or quarantine the `115` violating wrapper files, produce a
same-tree practical closure packet with a genuinely trade-usable factor, and
clear release/readiness gates from a clean selected source slice.
