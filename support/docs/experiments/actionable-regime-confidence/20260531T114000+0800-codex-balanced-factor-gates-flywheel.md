# Balanced Factor Gates Flywheel Slice - 2026-05-31

- created_at: `2026-05-31T11:40:00+0800`
- owner: `codex`
- agent_name: `codex-balanced-factor-gates`
- repo: `/Users/thrill3r/projects-ict-engine/ict-engine`
- branch: `main`
- route_alias: `sd/ict-engi-fact-rese-muta`
- workdoc: `/tmp/ict-engine-balanced-factor-gates-20260531T113047+0800/workdoc.md`
- claim: `/tmp/ict-engine-agent-claims/board-b-factor-refinement/20260531T113047+0800-codex-balanced-factor-gates.claim`
- status: `terminalized_verified_code_slice_no_runtime_launch`
- promotion_allowed: `false`
- trade_usable: `false`
- update_goal: `false`
- same_tree_practical_closure: `null`

## Objective

Balance throughput and quality in the profitability-factor gate stack by
separating learning/flywheel admission from final practical/live promotion.

This slice does not claim a trade-usable factor. It changes the admission
semantics so more candidates can enter evidence collection without weakening
`promotion_allowed`, `trade_usable`, or `update_goal`.

## Gate Decision

- Learning/flywheel admission may use a lower named regime-confidence floor.
- Final live promotion still uses the strict per-input `regime_confidence_floor`
  and the existing practical evidence tuple.
- Accepted paper/live/broker execution feedback is still required for live
  promotion.
- Verified retained-session scope, product cost, market-data provenance,
  Pre-Bayes, execution gate, execution tree, path-ranker consumption, and ranker
  validation remain live blockers.
- `funded_live_fill_required=false` remains the deploy-ready contract boundary;
  paper/sim/broker execution feedback can satisfy the accepted-feedback ticket,
  but Python-only, Gate-1-only, or backtest-only evidence cannot.

## Current Code Slice

Changed owner files:

- `src/application/factor_lifecycle/profitability_admission.rs`
- `src/application/factor_lifecycle/mod.rs`
- related dirty lifecycle readback surface already present in
  `src/application/entry_models/training_export.rs`

Behavior added in this slice:

- `FLYWHEEL_REGIME_CONFIDENCE_FLOOR=0.75` admits moderate-confidence positive
  candidates to learning/flywheel.
- Live promotion adds a separate strict blocker:
  `regime_confidence_below_live_floor`.
- A candidate with accepted execution feedback still cannot promote when its
  confidence is below the strict live floor.

## TDD Evidence

RED:

- `cargo test -q flywheel_learning_admits_moderate_regime_confidence_without_live_promotion -- --nocapture`
  - failed before implementation because learning status was `Blocked` rather
    than `Admitted`.

GREEN:

- `cargo test -q flywheel_learning_admits_moderate_regime_confidence_without_live_promotion -- --nocapture`
  - `1 passed`
- `cargo test -q accepted_feedback_cannot_promote_below_strict_live_regime_floor -- --nocapture`
  - `1 passed`
- `cargo test -q profitability_admission -- --nocapture`
  - `12 passed`
- `cargo test -q policy_training_status_ -- --nocapture`
  - first test binary: `12 passed`
  - second test binary: `2 passed`

## Remaining Objective Gap

The full user objective is still not complete:

- No current factor has `trade_usable=true`.
- No compact claim audit has `same_tree_practical_closure` validated.
- No current accepted same-root paper/live/broker execution feedback packet has
  been proven for an actual factor after this code slice.
- No provider/AQ/IBKR/paper/live runtime was launched by this slice.

Next strict step after commit: use the relaxed learning/flywheel admission to
feed more candidates into evidence collection, then require the unchanged live
hard gates before promotion.

## 2026-05-31T12:39:47+0800 Current-Turn Verification

Fresh claim audit after the committed code slice still reports no practical
factor:

- `promotion_allowed_true=0`
- `trade_usable_true=0`
- `same_tree_practical_closure=null`
- `live_factor_processes=0`
- one fresh active non-coordination claim blocks new runtime launch:
  `20260531T122333+0800-codex-ehlers-autocorr-periodogram-cycle-regime-30m-exact-aq.claim`

Current-turn verification passed:

- `CARGO_TARGET_DIR=/tmp/ict-engine-cargo-target-balanced-gates-verify cargo test -q --lib profitability_admission -- --nocapture`
  passed: `12 passed; 0 failed`.
- `CARGO_TARGET_DIR=/tmp/ict-engine-cargo-target-balanced-gates-verify cargo test -q --lib policy_training_status_ -- --nocapture`
  passed: `12 passed; 0 failed`.
- `python3 -m unittest support.scripts.research.tests.test_factor_candidate_pack -v`
  passed: `18 tests`.
- `python3 -m unittest support.scripts.research.tests.test_same_tree_practical_closure -v`
  passed: `22 tests`.
- `python3 -m unittest support.scripts.tests.test_objective_closure_snapshot -v`
  passed: `47 tests`.
- `python3 support/scripts/research/downstream_practical_admission_source_check.py --tracked-run-wrappers`
  returned all scanned tracked wrapper entries with `ok=true`.
- `python3 -m unittest support.scripts.tests.test_factor_claim_terminalization_audit.FactorClaimTerminalizationAuditTest.test_build_report_discovers_valid_same_tree_practical_closure_packet -v`
  passed.

One mistyped single-test command failed before the corrected test name was run:
`FactorClaimTerminalizationAuditTests` should be
`FactorClaimTerminalizationAuditTest`. This was an invocation error, not a
code failure.
