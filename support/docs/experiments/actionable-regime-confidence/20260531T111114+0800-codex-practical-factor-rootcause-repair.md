# Practical Factor Root-Cause Repair Tracker

- created_at: `2026-05-31T11:11:14+0800`
- owner: `codex`
- route: `sd/ict-engi-fact-rese-muta`
- tmp_workdoc: `/tmp/ict-engine-practical-factor-rootcause-repair-20260531T111114+0800/workdoc.md`
- claim: `/tmp/ict-engine-agent-claims/board-b-factor-refinement/20260531T111114+0800-codex-practical-factor-rootcause-repair.claim`
- objective: explain why current practical factor count is zero, then repair the highest-impact code or gate issue without lowering practical thresholds.
- non_goals: do not lower gates, do not claim local/AQ/simulated rows as paper/live feedback, do not collide with active AutoQuant/TOMAC owners, do not use Board docs as active state.

## Current Baseline

- `python3 support/scripts/factor_claim_terminalization_audit.py --compact`
  at `2026-05-31T11:10:35+0800` returned:
  - `trade_usable_true=0`
  - `promotion_allowed_true=0`
  - `same_tree_practical_closure=null`
  - `live_factor_processes=1`
  - live owner root: `/tmp/ict-engine-volume-clock-relative-participation-autoquant-training-20260531T110428+0800`
- Current live owner claim:
  `/tmp/ict-engine-agent-claims/board-b-factor-refinement/20260531T110428+0800-codex-volume-clock-relative-participation-autoquant-training.claim`
- This repair tracker is diagnostic/code-oriented until that live owner exits or terminalizes.

## Working Hypotheses

1. Practical count is zero because no current claim has a validated
   `same_tree_practical_closure` packet with `promotion_allowed=true`,
   `trade_usable=true`, verified ETH/full-retained session scope, verified
   instrument cost, and accepted paper/live/broker execution feedback.
2. Some candidate lanes may have local or AQ-positive economics, but remain
   blocked by at least one of: sparse density, missing downstream staged command
   rows, incomplete market-data provenance, unverified cost model, simulated
   feedback only, no policy-training lifecycle admission, or active runtime
   collision.
3. A code or gate bug may still exist if the current producer and validator
   disagree about practical-closure evidence semantics. This slice will first
   compare the canonical producer/validator and focused tests before editing.

## Iteration Log

- `2026-05-31T11:11:14+0800`: Tracker created. Next: inspect compact audit,
  active live root, same-tree closure helper/tests, and practical lifecycle
  wrappers for producer/validator drift.
- `2026-05-31T11:16:30+0800`: The broad root-cause claim was terminalized as
  duplicate scope because fresh closed-loop/gap audit claims already exist.
  Narrowed this slice to a concrete claim-audit blocker classification defect:
  no-launch diagnostic/audit claims with explicit no-runtime intent should not
  count as active runtime blockers.
- `2026-05-31T11:51:31+0800`: Current compact audit is clear:
  `active_claims=0`, `live_factor_processes=0`, `promotion_allowed_true=0`,
  `trade_usable_true=0`, `same_tree_practical_closure=null`.
- Repo-native NQ compound readonly IBKR readback succeeded against IB Gateway
  paper port `4002` but returned `execution_rows_total=0`; converter wrote
  `accepted_feedback_rows=0` and
  `terminal_decision=accepted_execution_feedback_missing`. Evidence:
  `/tmp/ict-engine-nq-compound-repo-readback-preflight-20260531T114632+0800/summaries/accepted_feedback_conversion_summary.json`.
- Code repairs in this slice: no-launch/code-only claim classification in
  `factor_claim_terminalization_audit.py`, repo-native
  `ibkr_execution_readback.py`, stricter accepted-feedback conversion requiring
  explicit broker evidence flags, and conversion summary/metrics outputs.
