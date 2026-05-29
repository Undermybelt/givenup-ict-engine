# Factor Closure Data Provenance Sanity Tracking

- created_at: `2026-05-29T20:46:00+0800`
- owner: `codex`
- route: `sd/ict-engi-fact-rese-muta`
- repo: `/Users/thrill3r/projects-ict-engine/ict-engine`
- branch: `main`
- status: `active_fix_data_provenance_sanity_gate`
- promotion_allowed: `false`
- trade_usable: `false`
- update_goal: `false`

## Current Answer

No. I do not have 100% confidence that the full objective is complete.

Current same-turn evidence:

- `python3 support/scripts/factor_claim_terminalization_audit.py --compact`
  returned `status=needs_attention`.
- Current factor closure surface has `promotion_allowed_true=0`,
  `trade_usable_true=0`, and `same_tree_practical_closure=null`.
- There is an active live process under
  `/tmp/ict-engine-tomac-15y-external-strategy-mining-20260529T192702+0800`.
- The latest source-backed TOMAC 15Y screen remained Python/TOMAC-only
  discovery evidence and did not pass Gate 1.

## Loophole Found

The practical-closure evidence validator already rejects marker-only packets,
missing lifecycle tuples, and missing policy-training lifecycle counts. It still
does not explicitly require the evidence packet to prove that the market data
used by the practical factor came from a verified usable provenance class and
passed return-sanity checks.

That matters because this same lane produced raw CSV discovery rows with
absurd total returns and nonzero `extreme_abs_gross_gt_10pct_count`. Those rows
were correctly rejected by lane-local readback, but the repo-level
`same_tree_practical_closure` validator should fail closed on the same class of
evidence even if a future packet sets all other practical booleans true.

## Fix Boundary

Canonical owner:

- `support/scripts/factor_claim_terminalization_audit.py`

Regression surface:

- `support/scripts/tests/test_factor_claim_terminalization_audit.py`

Required behavior:

- A practical closure evidence packet must include market-data provenance and
  sanity evidence.
- Allowed provenance must be explicitly verified, such as roll-adjusted clean
  feather, verified provider historical data, or paper/live execution feedback.
- Raw contract stitching and raw local CSV stitching must not be practical
  closure proof.
- Extreme gross-return sanity failures or parse-bad rows must fail closed.

## Verification Plan

1. Add RED tests showing the current validator accepts missing or raw/extreme
   data provenance evidence.
2. Add the smallest validator check at the evidence-packet owner.
3. Run focused tests for `factor_claim_terminalization_audit.py`.
4. Re-run `objective_closure_snapshot.py` tests that consume the closure field.
5. Update the factor-research runtime skill/reference if the gate semantics
   changed.
6. Commit only this verified slice.

## Implementation Readback

- Added closure evidence checks in
  `support/scripts/factor_claim_terminalization_audit.py`.
- Added RED/GREEN regression coverage in
  `support/scripts/tests/test_factor_claim_terminalization_audit.py`.
- `same_tree_practical_closure` evidence packets now require
  `market_data_provenance.status=pass`, an allowed source class, and clean
  `return_sanity`.
- Allowed source classes include verified provider historical data,
  roll-adjusted clean feather, and paper/live broker execution feedback.
- Disallowed source classes include raw contract stitching, raw local CSV
  stitching, raw Databento contract stitching, and raw TOMAC CSV evidence.
- Return-sanity fails closed on nonzero `extreme_abs_gross_gt_10pct_count`,
  nonzero `parse_bad_rows`, or `max_abs_gross_return_pct > 10.0`.

## Verification Readback

- RED:
  `python3 -m unittest support.scripts.tests.test_factor_claim_terminalization_audit.FactorClaimTerminalizationAuditTest.test_build_report_discovers_valid_same_tree_practical_closure_packet support.scripts.tests.test_factor_claim_terminalization_audit.FactorClaimTerminalizationAuditTest.test_build_report_rejects_closure_packet_without_market_data_provenance support.scripts.tests.test_factor_claim_terminalization_audit.FactorClaimTerminalizationAuditTest.test_build_report_rejects_closure_packet_with_raw_stitching_extreme_return_sanity_failure -v`
  failed on the two new rejection tests before implementation.
- GREEN focused:
  same command passed after implementation.
- Regression:
  `python3 -m unittest support.scripts.tests.test_factor_claim_terminalization_audit -v`
  -> `Ran 91 tests`, `OK`.
- Consumer regression:
  `python3 -m unittest support.scripts.tests.test_objective_closure_snapshot -v`
  -> `Ran 41 tests`, `OK`.
- Combined regression:
  `python3 -m unittest support.scripts.tests.test_factor_claim_terminalization_audit support.scripts.tests.test_objective_closure_snapshot`
  -> `Ran 132 tests`, `OK`.
- Compile:
  `python3 -m py_compile support/scripts/factor_claim_terminalization_audit.py support/scripts/objective_closure_snapshot.py`
  -> exit `0`.
- Current live closure state:
  `python3 support/scripts/factor_claim_terminalization_audit.py --compact`
  returned `status=needs_attention`, `active_claims=2`,
  `live_factor_processes=1`, `promotion_allowed_true=0`,
  `trade_usable_true=0`, and `same_tree_practical_closure=null`.

## Remaining Gaps

- The full user objective remains incomplete.
- Current active Board B claims and the live ES clean-feather Python process
  still block a truthful completion claim.
- No same-tree practical closure packet currently exists.
- There are still no currently verified `trade_usable=true` or
  `promotion_allowed=true` factors.
