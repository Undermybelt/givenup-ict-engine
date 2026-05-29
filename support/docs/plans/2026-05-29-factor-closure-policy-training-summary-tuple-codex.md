# Factor Closure Policy Training Summary Tuple Audit

- created_at: `2026-05-29T19:44:00+0800`
- owner: `codex`
- route: `sd/ict-engi-fact-rese-muta`
- repo: `/Users/thrill3r/projects-ict-engine/ict-engine`
- branch: `main`
- status: `partial_loophole_fix_verified_objective_not_complete`
- promotion_allowed: `false`
- trade_usable: `false`
- update_goal: `false`

## Objective

Close the same-tree practical-closure loophole where a nonempty
`policy_training_summary` could make a `same_tree_practical_closure` packet look
valid even when the policy-training lifecycle had not admitted learning, paper,
live readiness, and live trade usability.

## Loophole

Before this slice, `support/scripts/factor_claim_terminalization_audit.py`
validated the referenced closure evidence packet by requiring
`policy_training_summary` to be a nonempty dict. That was too weak: a packet
could say `promotion_allowed=true`, `trade_usable=true`, and
`live_trade_status=ready` at top level while the policy-training lifecycle still
had `live_ready_count=0` or `live_trade_usable_count=0`.

## Fix

`policy_training_summary` must now prove the lifecycle directly or under
`factor_profitability_lifecycle`:

- `learning_admitted_count > 0`
- `paper_ready_count > 0`
- `live_ready_count > 0`
- `live_trade_usable_count > 0`
- `promotion_allowed is true`
- `trade_usable is true`

If any field is missing, zero, false, or only present as a bool masquerading as a
count, the closure packet fails closed and is not surfaced as
`same_tree_practical_closure`.

## Verification

- `python3 -m unittest support.scripts.tests.test_factor_claim_terminalization_audit -v`
  ran `89/89 OK`.
- `python3 -m py_compile support/scripts/factor_claim_terminalization_audit.py support/scripts/tests/test_factor_claim_terminalization_audit.py`
  passed.
- `python3 -m unittest support.scripts.tests.test_objective_closure_snapshot -v`
  ran `40/40 OK`.
- `python3 -m unittest support.scripts.tests.test_factor_claim_terminalization_audit.FactorClaimTerminalizationAuditTest.test_build_report_discovers_valid_same_tree_practical_closure_packet support.scripts.tests.test_factor_claim_terminalization_audit.FactorClaimTerminalizationAuditTest.test_build_report_rejects_closure_packet_without_policy_training_live_tuple support.scripts.tests.test_factor_claim_terminalization_audit.FactorClaimTerminalizationAuditTest.test_build_report_rejects_closure_packet_without_full_lifecycle_tuple -v`
  ran `3/3 OK`.
- `git diff --check -- support/scripts/factor_claim_terminalization_audit.py support/scripts/tests/test_factor_claim_terminalization_audit.py support/docs/plans/2026-05-29-closed-loop-loophole-audit-codex-current.md`
  returned clean before this narrow tracking doc was added.

## Current State

Fresh compact audit at `2026-05-29T19:44+0800` still reported
`status=needs_attention`, `active_claims=2`, `valid_active_claims=1`,
`invalid_active_claims=1`, `live_factor_processes=1`,
`promotion_allowed_true=0`, `trade_usable_true=0`, and
`same_tree_practical_closure=null`.

The live process was an IBKR XLC fetch under
`support/docs/experiments/actionable-regime-confidence/runs/20260529T194114+0800-codex-ibkr-xlc-communication-services-keltner-reclaim-1m-mtf-gate1-v1`.
Therefore this slice does not allow a provider/AQ/TOMAC launch or objective
completion claim.

## Next Steps

1. Re-run `python3 support/scripts/factor_claim_terminalization_audit.py --compact`
   after the live IBKR XLC process exits or terminalizes.
2. Repair or avoid any invalid active claim unless it belongs to this exact lane
   and can be made explicit with `agent_name`, exact task, non-goals,
   `write_surface`, and run root.
3. Continue source-backed factor mining only while it does not launch a colliding
   provider, Auto-Quant, TOMAC, paper, simulated, or live runtime.
4. Do not mark the objective complete until a validated
   `same_tree_practical_closure` packet proves provider, training admission,
   paper readiness, live readiness, execution, and feedback in the same tree.
