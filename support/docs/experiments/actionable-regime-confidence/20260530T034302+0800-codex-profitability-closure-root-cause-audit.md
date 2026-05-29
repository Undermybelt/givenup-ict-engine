# Profitability Closure Root-Cause Audit

created_at: 2026-05-30T03:43:02+0800
owner: codex
agent_name: codex-profitability-closure-root-cause-audit
repo: /Users/thrill3r/projects-ict-engine/ict-engine
branch: main
status: active_read_only_then_canonical_owner_fix
promotion_allowed: false
trade_usable: false
update_goal: false

## Objective

Find why ict-engine keeps producing near-practical factor packets but no
validated trade-usable profitability factor, then fix canonical completion or
admission owners where current evidence shows a system loophole.

## Current Hard Evidence

- `python3 support/scripts/factor_claim_terminalization_audit.py --compact`
  at 2026-05-30T03:40+0800 returned `status=needs_attention`.
- `trade_usable_true=0`.
- `promotion_allowed_true=0`.
- `same_tree_practical_closure=null`.
- Blocking runtime: `/tmp/ict-engine-eur-eth-donchian-tsmom-volcarry-prep-20260530T005133+0800`
  local Python screen process is still live.
- Blocking fresh claim: `20260530T033600+0800-codex-6b-eth-boe-rate-differential-london-stoprun-vwap-reclaim-gate1.claim`.

## Constraints

- Do not launch provider, IBKR, AutoQuant, Freqtrade, paper, lifecycle, or new
  local factor screening while compact claim audit reports active claims or live
  factor processes.
- Do not use Board/current docs for lane selection.
- Preserve unrelated dirty work.
- If source changes are needed, use TDD and commit only the verified slice.
- Do not mark the active goal complete without a validated same-tree practical
  closure packet and at least one `promotion_allowed=true` and
  `trade_usable=true` backed by full lifecycle evidence.

## Plan

1. Run a read-only objective-closure snapshot into `/tmp` to capture current
   gate failures.
2. Inspect canonical owners: `objective_closure_snapshot.py`,
   `done_definition_audit.py`, `factor_claim_terminalization_audit.py`,
   `same_tree_practical_closure.py`, and
   `downstream_practical_admission_source_check.py`.
3. If the current completion output only says "no pass packet" without naming
   broken lifecycle stages, add a source-owned blocker breakdown with tests.
4. Verify focused tests and compact audits.
5. Commit the verified slice if code changed.

## Progress

- 2026-05-30T03:43:02+0800: opened tracking doc after routing and current-state
  audit. Current action is read-only closure diagnosis; no new factor runtime
  launch is allowed.
- 2026-05-30T03:44:59+0800: baseline
  `python3 support/scripts/objective_closure_snapshot.py --compact --timeout-seconds 240 --output-dir /tmp/ict-engine-goal-20260530-codex-root-cause-034302`
  exited nonzero with `completion_proven=false`. The actionable source blocker
  was one tracked practical-admission violation in
  `run_tomac_index_futures_clean_aq_v1.py`: `survives_5bps_per_side` combined
  `trades >= 30` with positive 5bps cost survival, conflating sparse-positive
  economics with sample/density readiness.
- 2026-05-30T03:47:00+0800: RED test added:
  `test_cost_survival_is_separate_from_trade_sample_floor` failed because a
  sparse but strongly cost-positive row reported `survives_5bps_per_side=false`.
- 2026-05-30T03:48:00+0800: fixed clean-AQ scoring semantics. Cost-survival
  fields now represent cost economics only. New
  `minimum_trade_sample_floor_met` carries the `trades >= 30` sample floor, and
  `gate1_survivor` still requires sample floor, density, 5bps survival,
  instrument-cost survival, win/loss diversity, and direction consistency.
- 2026-05-30T03:49:18+0800: verification passed:
  `python3 -m unittest support.docs.experiments.actionable-regime-confidence.scripts.test_tomac_index_futures_clean_aq -v`
  ran 88 tests OK;
  `python3 support/scripts/research/downstream_practical_admission_source_check.py support/docs/experiments/actionable-regime-confidence/scripts/run_tomac_index_futures_clean_aq_v1.py`
  returned `practical_admission_source_ok`; `python3 -m py_compile ...` passed;
  `python3 support/scripts/done_definition_audit.py --compact --output /tmp/ict-engine-done-definition-after-cost-density-separation.json`
  returned `status=pass`, `tracked_violation_count=0`, `fail_count=0`, with
  heavy gates skipped because this was a compact pass.
- 2026-05-30T03:50:00+0800: updated Hermes runtime skill
  `software-development/ict-engi-fact-rese-muta/SKILL.md` with the durable rule:
  cost-survival fields must not include sample size, density, cadence, or
  validation readiness; those must be separate gates.
