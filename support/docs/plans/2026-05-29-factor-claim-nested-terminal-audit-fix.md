# Factor Claim Nested Terminal Audit Fix - 2026-05-29

## Goal

Keep the larger factor-training closed-loop objective honest by fixing one
claim-audit loophole: active Board B claims with wrapper-nested terminal
no-launch artifacts must not remain counted as fresh active ownership.

## Current Slice

- Repo: `/Users/thrill3r/projects-ict-engine/ict-engine`
- Branch: `main`
- Route: `sd/ict-engi-fact-rese-muta`
- Code owner touched: `support/scripts/factor_claim_terminalization_audit.py`
- Test touched: `support/scripts/tests/test_factor_claim_terminalization_audit.py`
- Runtime skill updated outside this repo:
  `/Users/thrill3r/.hermes/skills/software-development/ict-engi-fact-rese-muta/SKILL.md`

## Root Cause

The compact factor-claim audit read only top-level run-root terminal artifacts
such as `summaries/terminal_summary.json` and `checks/terminal_metrics.json`.
Some guarded TOMAC wrappers write terminal no-launch evidence under a nested
wrapper root, for example `run/summaries/terminal_summary.json`. When that
nested summary reported `status=launch_blocked_by_collision_guard`, the claim
could still be counted as a fresh active claim until manual terminalization or
stale timeout.

## Fix

- Added nested summary discovery for `run/summaries/terminal_summary.json` and
  `run/checks/terminal_metrics.json`.
- Classified `launch_blocked_by_collision_guard` as terminal no-verdict
  evidence.
- Propagated terminal-summary `status` into the compact claim `decision` when
  no explicit claim decision exists.
- Added regression coverage proving an active claim with nested collision-guard
  summary is terminalized, preserves the nested summary path, and keeps
  `promotion_allowed=false` / `trade_usable=false`.

## Verification

- RED observed:
  `python3 -m unittest support.scripts.tests.test_factor_claim_terminalization_audit.FactorClaimTerminalizationAuditTest.test_build_report_treats_nested_collision_guard_terminal_summary_as_terminalized -v`
  failed with `active_claims` still `1`.
- GREEN focused test:
  same command passed.
- Full targeted test:
  `python3 -m unittest support.scripts.tests.test_factor_claim_terminalization_audit -v`
  passed `73` tests.
- Docs/runtime isolation:
  `python3 support/scripts/ci/check_docs_runtime_isolation.py` passed.
- Whitespace check:
  `git diff --check -- support/scripts/factor_claim_terminalization_audit.py support/scripts/tests/test_factor_claim_terminalization_audit.py support/docs/plans/2026-05-28-factor-training-closed-loop-continuation-codex-current.md`
  passed.
- Objective snapshot:
  `python3 support/scripts/objective_closure_snapshot.py --compact --done-definition-proof /tmp/ict-engine-goal-20260529-codex-heavy-done-definition-015033.json --output-dir /tmp/ict-engine-closed-loop-snapshot-20260529T0436-codex-nested-terminal-audit-fix`
  remained red with `completion_proven=false`.

## Current Closure Status

The objective is still not complete. Current snapshot blockers include:

- `done_definition_not_completion_ready`
- `factor_closure_blocked`
- `release_readiness_blocked`
- `release_remote_checks_not_run`

The current factor-closure blocker is five fresh active claims with no live
runtime and no stale-safe takeover yet. Current readback still shows
`promotion_allowed_true=0` and `trade_usable_true=0`.

## Next Steps

1. Do not launch or take over while active claims are fresh.
2. Rerun `python3 support/scripts/factor_claim_terminalization_audit.py --compact --portable-paths` and focused `ps` after owner progress or stale-safe timeout.
3. Inspect any terminalized claim artifacts before choosing a new lane.
4. If a claim becomes stale-safe with no matching live owner, append takeover
   metadata and preserve `promotion_allowed=false`, `trade_usable=false`, and
   `update_goal=false` unless the full live tuple passes.
5. Continue searching for or producing one same-tree practical closure packet
   proving provider/training admission, Pre-Bayes, BBN, path-ranker
   consumption, execution tree, feedback, and live-use together.
