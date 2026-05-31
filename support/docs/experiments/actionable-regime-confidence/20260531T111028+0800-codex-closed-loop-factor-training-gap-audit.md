# Closed-Loop Factor Training Gap Audit - 2026-05-31

- created_at: `2026-05-31T11:10:28+0800`
- owner: `codex`
- agent_name: `codex-closed-loop-gap-audit`
- repo: `/Users/thrill3r/projects-ict-engine/ict-engine`
- branch: `main`
- route_alias: `sd/ict-engi-fact-rese-muta`
- runtime_skill: `~/.hermes/skills/software-development/ict-engi-fact-rese-muta/SKILL.md`
- workdoc: `/tmp/ict-engine-closed-loop-factor-training-gap-audit-20260531T111028+0800/workdoc.md`
- claim: `/tmp/ict-engine-agent-claims/board-b-factor-refinement/20260531T111028+0800-codex-closed-loop-factor-training-gap-audit.claim`
- status: `active_gap_audit`
- promotion_allowed: `false`
- trade_usable: `false`
- update_goal: `false`
- same_tree_practical_closure: `null`

## Objective

Determine whether there is airtight current evidence that the optimized
`ict-engine` factor-training direction can train profitability factors that
enter the practical closed loop and keep every stage useful. If not, enumerate
the loopholes, repair the reasonable ones with strict evidence, and repeat
until remaining uncertainty is explicitly bounded by current artifacts.

This is not a completion claim.

## Entry Evidence

- Routing completed through `sd/ict-engi-fact-rese-muta`.
- Repo instructions read: `AGENTS.md`, `CLAUDE.md`, `AGENT.md`.
- Current compact factor-claim audit returned `status=pass`,
  `active_claims=0`, `live_factor_processes=0`, `promotion_allowed_true=0`,
  `trade_usable_true=0`, and `same_tree_practical_closure=null`.
- Focused process scan found no foreign factor/AQ/IBKR/TOMAC runtime.
- The worktree already contains many modified and untracked files. This slice
  must not revert, clean, or stage unrelated work.

## First-Principles Review

First Principle: practical factor training is complete only when same-tree
current evidence proves the full lifecycle, not when a candidate looks
profitable in one screen.

Non-negotiables: ETH/full-retained session proof, verified exact instrument
costs, real stage-by-stage closed-loop command evidence, accepted
paper/live/broker feedback for practical closure, collision-safe ownership, and
no relaxed gates.

Assumptions to Drop: old Board docs, marker-only JSON, RTH-only positives,
local retained-cache screens, simulated feedback, fixed-bps labels, and wrapper
claims of lifecycle completion are not proof by themselves.

Smallest Sufficient Path: audit and align the canonical practical-closure
producer, audit validator, lifecycle wrappers, feedback labeler, and claim
guards; only then run factor-specific AutoQuant iteration.

Escalation Signal: if any wrapper can still emit `promotion_allowed=true`,
`trade_usable=true`, or a pass closure packet without the canonical staged
evidence tuple, the training direction is not safe.

## Loopholes To Check

1. Wrapper-level command-result spoofing can report all stages complete without
   explicit provider, pre-Bayes, BBN, path-ranker, execution-tree, feedback, and
   policy-training rows.
2. Same-tree practical-closure producer and claim-audit validator can diverge.
3. Practical lifecycle wrappers can synthesize `extension_complete` or promote
   local wrapper state instead of validated lifecycle proof.
4. Feedback labels can confuse simulated, retained-label, or backtest feedback
   with accepted paper/live/broker execution evidence.
5. ETH/full-retained session coverage can be missing or RTH-only while the
   factor is still presented as practical.
6. Verified cost packets can be incomplete while positive economics remain
   visible.
7. Claim/workdoc/live-process parsing can miss a fresh owner and allow duplicate
   agent work.
8. Multi-timeframe data staging can be mistaken for proof of factor training
   and closed-loop readiness.

## Verification Plan

- Inspect the current dirty diffs in the canonical practical-closure helper,
  claim audit, lifecycle wrappers, and feedback labeler.
- Run focused tests covering any edited semantics.
- If code changes are made in this slice, stage and commit only the relevant
  files after tests pass.
- Keep `promotion_allowed=false`, `trade_usable=false`, and `update_goal=false`
  unless the canonical same-tree practical-closure packet validates from the
  same run root.

## Iteration 1 Result - 2026-05-31T11:21+0800

Result: not complete, but one concrete closure loophole was repaired.

Repairs:

- `support/scripts/research/same_tree_practical_closure.py` now requires broker
  fill/realized evidence in the metrics evidence chain, not just an accepted
  feedback source marker.
- `run_tomac_nq_compound_trend_rrr_chopfilter_practical_lifecycle_v1.py` now
  carries the current explicit accepted-feedback preflight into closure metrics
  as `trade_summary`, so legal paper/broker feedback is not masked by stale
  staged source summaries.

Verification:

- `python3 -m unittest support.scripts.research.tests.test_same_tree_practical_closure -v`
  - `Ran 22 tests`, `OK`
- `python3 support/docs/experiments/actionable-regime-confidence/scripts/test_tomac_nq_compound_trend_rrr_chopfilter_practical_lifecycle_v1.py -v`
  - `Ran 24 tests`, `OK`
- `python3 support/scripts/research/downstream_practical_admission_source_check.py --tracked-run-wrappers --pretty`
  - tracked wrappers passed, no violations
- all-workspace wrapper scan artifact:
  `/tmp/ict-engine-closed-loop-factor-training-gap-audit-20260531T111028+0800/downstream_source_check_all_wrappers.json`
  - scanned `1063`
  - violations `222`
  - all violations are untracked files
- `python3 -m unittest support.scripts.research.tests.test_downstream_practical_admission_source_check -v`
  - `Ran 45 tests`, `OK`
- `python3 -m unittest support.scripts.research.tests.test_real_trade_feedback_labels -v`
  - `Ran 10 tests`, `OK`
- `python3 -m unittest support.scripts.tests.test_factor_claim_terminalization_audit -v`
  - `Ran 117 tests`, `OK`
- `python3 support/scripts/factor_claim_terminalization_audit.py --compact`
  - `status=pass`
  - `attention_claim_count=0`
  - `live_factor_processes=0`
  - `promotion_allowed_true=0`
  - `trade_usable_true=0`
  - `same_tree_practical_closure=null`
- `git diff --check` on this slice exited `0`.

Remaining loopholes:

1. The worktree still has `222` untracked run-wrapper source-check violations.
   They are not current tracked authority, but they are still local files that
   an agent could run by mistake.
2. There is still no current accepted IBKR paper/broker feedback row for NQ
   compound.
3. There is still no validated same-tree practical closure packet.
4. There is still no `trade_usable=true` or `promotion_allowed=true` factor.

Next strict path:

1. Commit this verified closure-feedback evidence slice.
2. Keep untracked violating wrappers quarantined as non-authority until fixed or
   removed by their owners.
3. After fresh claim/process guards clear, run the NQ compound accepted-feedback
   readback/conversion preflight.
4. If accepted feedback rows are zero, stop there. If rows exist, run practical
   lifecycle with same-root session, cost, market-data, stage, policy, and
   closure evidence.
