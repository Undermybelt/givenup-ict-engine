# Factor Candidate Buildable Closed-Loop Audit

Updated: `2026-05-27`

## Scope

This audit tracks one verified loophole in the Python factor-candidate resolver
surface. It does not claim that the full `ict-engine` training-to-live closed
loop is complete.

## Verified Problem

Authoritative repo contract in `AGENT.md` says candidate packs are
inspection/admission surfaces until runtime gates explicitly promote them.

Before this fix, `python3 support/scripts/research/factor_candidate_resolver.py --list-buildable --output-format human`
reported only `buildable_count` and then listed repo-native candidate packs
without any explicit fail-closed closed-loop status.

Current repo-native packs demonstrate why that is unsafe:

- `family_f_vrp_compression_15m_v1` was listed as buildable while
  `learning_admission_status=blocked`.
- `order_block_mitigation_block_1h_v1` was listed as buildable while
  `learning_admission_status=blocked`.
- The pre-fix human output exposed expectancy and transfer labels, but not
  `promotion_allowed=false` or `trade_usable=false`.

That made `buildable` too easy to misread as downstream-consumable.

## Fix

`support/scripts/research/factor_candidate_resolver.py` now keeps `buildable`
strictly as an artifact-reuse signal, while also emitting explicit fail-closed
closed-loop fields for each listed candidate:

- `closed_loop_consumption_status`
- `learning_blockers`
- `promotion_allowed`
- `trade_usable`

The buildable summary now also reports:

- `promotion_ready_count`
- `trade_usable_count`
- `inspection_only_count`

The human output now prints the closed-loop consumption status per candidate.

## Verification

Commands run in this slice:

```bash
python3 -m unittest support.scripts.research.tests.test_factor_candidate_resolver.FactorCandidateResolverTests.test_list_buildable_candidates_surfaces_curated_pack_metrics -v
python3 -m unittest support.scripts.research.tests.test_factor_candidate_resolver -v
python3 support/scripts/research/factor_candidate_resolver.py --list-buildable --output-format human
```

Observed post-fix resolver surface:

```text
buildable_count=8 candidate_count=14 promotion_ready_count=0 trade_usable_count=0 inspection_only_count=8
family_f_vrp_compression_15m_v1 ... blocked inspection_only_learning_blocked ...
order_block_mitigation_block_1h_v1 ... blocked inspection_only_learning_blocked ...
```

This proves the resolver no longer presents current repo-native buildable packs
as implicitly promotable.

## Still Unproven

This slice does not prove any of the following:

- that any current candidate is promotion-ready;
- that any current candidate is trade-usable;
- that the Pre-Bayes, BBN, path-ranker, execution-tree, and feedback/update
  links are all green for a real factor lane;
- that Board B current active claims are terminalized enough for a fresh
  end-to-end training lane.

As of the same-turn `factor_claim_terminalization_audit.py --compact` readback,
Board B still reports `active_claims=14`, `promotion_allowed_true=0`, and
`trade_usable_true=0`.
