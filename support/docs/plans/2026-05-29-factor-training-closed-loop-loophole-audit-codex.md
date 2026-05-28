# Factor Training Closed-Loop Loophole Audit

- created_at: `2026-05-29T04:55:58+0800`
- owner: `codex`
- route: `sd/ict-engi-fact-rese-muta`
- repo: `/Users/thrill3r/projects-ict-engine/ict-engine`
- branch: `main`
- local workdoc: `/tmp/ict-engine-factor-training-closed-loop-loophole-audit-20260529T0456+0800/workdoc.md`
- claim: `/tmp/ict-engine-agent-claims/board-b-factor-refinement/20260529T045658+0800-codex-factor-training-closed-loop-loophole-audit.claim`
- status: `active_audit_only`
- promotion_allowed: `false`
- trade_usable: `false`
- update_goal: `false`

## Objective

Audit the current ict-engine factor-training direction and closed-loop admission
path for loopholes that could let an unproven profitability factor appear usable,
skip a required training/feedback/readiness gate, or fail to optimize/participate
in each closed-loop stage after admission. This slice is no-launch and does not
own any active profitability factor lane.

## Current Collision Readback

- `python3 support/scripts/factor_claim_terminalization_audit.py --compact --portable-paths` at `2026-05-29T04:55+0800`: `status=needs_attention`, `active_claims=5`, `valid_active_claims=5`, `live_factor_processes=0`, `stale_safe_takeover_candidates=0`, `promotion_allowed_true=0`, `trade_usable_true=0`.
- Focused process scan found no live TOMAC/AQ/provider writer.
- Decision: no provider, IBKR, Auto-Quant, TOMAC, factor-research, or materialization launch until active claims clear or become stale-safe.

## Non-Goals

- Do not touch active DonchianTurtleBreakout, CompressionBreakoutContinuation,
  DailyDonchian UncoveredSessionComplement, or OpeningDrive execution-window
  audit ownership while their claims are fresh.
- Do not lower cost, density, validation, ranker, execution, provider, paper,
  simulated-trade, or live-use gates.
- Do not infer trade readiness from demo, Gate 1 alone, sparse positive rows,
  simulated feedback, or ranker visibility alone.

## Loopholes Under Audit

1. Training helper surfaces may use stale or incomplete multi-timeframe replay
   windows, making execution materialization observe-only or non-comparable.
2. Practical-admission fields may still be set from branch-local/downstream
   checks before the complete live tuple is proven.
3. Blocker reports may classify retired telemetry as hard blockers, or miss
   current blockers because validation/readiness is only present in lineage text.
4. Structural feedback replay may accept simulated/backtest feedback as if it
   were production real-trade evidence.
5. Path-ranker direct/fallback artifacts may train/register/apply with mismatched
   model-family or stale gate floors.
6. Claim/runtime audits may miss active writers, nested terminal artifacts, or
   stale active claims that block or falsely clear closure.
7. Factor-training direction may keep reusing terminal/low-density families
   instead of rotating to source-backed, 1m-first, full-MTF, cost-aware branches.

## Evidence Log

- Created after routing through Hermes and repo contracts.
- Current compact audit blocks runtime lane work; this document is audit-only.
- `2026-05-29T05:08:33+0800`: audited `support/scripts/research/downstream_practical_admission_source_check.py` and found a static-check loophole: transition-hazard hard gates such as `transition_hazard < 0.60` were detected when directly assigned to `pass_exec`, but an intermediate boolean like `hazard_ok = transition_hazard < 0.60; pass_exec = branch_ok and hazard_ok` could reach `practical_admission_flags(pass_exec)` without a branch-local admission violation.
- Added regression coverage in `support/scripts/research/tests/test_downstream_practical_admission_source_check.py::test_flags_transition_hazard_taint_through_intermediate_guard` and patched the checker to propagate transition-hard-gate taint through intermediate names and helper-call arguments while preserving PDA-first reporting when both hard gates appear.
- Static readback confirmed the checker now flags a real existing unsafe wrapper pattern in `support/docs/experiments/actionable-regime-confidence/scripts/run_ibkr_strict_trend_root_mes15m_simulated_trade_admission_v1.py`: `pass_exec` is transition-gated and `promotion_allowed` / `trade_usable` are still direct `pass_exec` assignments.
- Verification: focused RED test failed before patch with `AssertionError: True is not false`; after patch `python3 -m unittest support.scripts.research.tests.test_downstream_practical_admission_source_check -v` passed `20/20`; `python3 -m unittest support.scripts.auto_quant_external.tests.test_next_slice_helpers -v` passed `21/21` on repeat after one transient materialization-state-copy failure passed in isolation.

## Terminal Decision

- `2026-05-29T05:12:40+0800`: terminalized this no-launch audit-code slice as
  `partial_loophole_fix_verified_full_objective_still_active`.
- This slice only closes the practical-admission checker loophole for
  transition-hard-gate taint through intermediate booleans. It does not prove
  practical factor usability.
- Keep `promotion_allowed=false`, `trade_usable=false`, and `update_goal=false`
  unless the full current-state objective is proven by provider/data, regime
  posterior, Pre-Bayes, BBN, ranker, execution tree, feedback/update, and
  training/refinement evidence.
