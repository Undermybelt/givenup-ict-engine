# Factor Training Root-Cause Continuation

- created_at: `2026-05-30T02:55:00+0800`
- owner: `codex`
- route: `sd/ict-engi-fact-rese-muta`
- repo: `/Users/thrill3r/projects-ict-engine/ict-engine`
- branch: `main`
- status: `in_progress`
- promotion_allowed: `false`
- trade_usable: `false`
- update_goal: `false`

## Current Truth

The full objective is not complete. Same-turn compact audit and objective
snapshot still report:

- `promotion_allowed_true=0`
- `trade_usable_true=0`
- `same_tree_practical_closure=null`
- active claim/runtime blockers remain in `/tmp`
- no truthful completion commit exists for full practical closure

## Root-Cause Split

The repeated "near practical but never trade usable" behavior is not one bug.
The current evidence splits it into three failure classes:

1. Gate-1 economics are often fake-near: raw or low-cost positives fail hard
   cost and density. Latest XAU full-session example was terminalized as
   `observation_gate1_no_practical_5bps_density_survivor` with zero 5bps
   survivors.
2. Lifecycle wrappers can still create readback surfaces that look closed while
   missing full staged command evidence. The canonical closure helper correctly
   rejects these, but the wrapper can obscure the real missing stage.
3. The shared runtime remains crowded by fresh claims and live processes, so new
   launches must wait or terminalize existing owners instead of colliding.

## Current Fix Boundary

Canonical practical closure requires explicit stages:

- `provider_data`
- `pre_bayes`
- `bbn_workflow`
- `path_ranker`
- `execution_tree`
- `feedback_update`
- `policy_training`

This slice targets one remaining loophole in
`run_tomac_nq_compound_trend_rrr_chopfilter_practical_lifecycle_v1.py`: its CLI
entrypoint currently passes a single synthetic `practical_lifecycle_readback`
command row instead of real staged evidence. That guarantees the canonical
helper rejects practical closure while making `all_command_exits_zero=true`,
which is misleading.

## Progress Log

- 2026-05-30T02:55+0800: Created tracking doc before production edits.
- 2026-05-30T02:58+0800: RED confirmed the practical-lifecycle CLI entrypoint
  did not write `summaries/same_tree_practical_closure.json` even when source
  metrics contained full staged command rows, because `main()` passed only one
  synthetic `practical_lifecycle_readback` row.
- 2026-05-30T03:02+0800: Fixed the wrapper to read staged command results from
  source/cross-engine terminal metrics or summaries. If no source contains all
  canonical stages, the wrapper now passes an empty command list, writes
  `all_command_exits_zero=false`, emits no closure packet, and exits nonzero.
- 2026-05-30T03:03+0800: Focused wrapper tests passed:
  `python3 -m unittest support.docs.experiments.actionable-regime-confidence.scripts.test_tomac_nq_compound_trend_rrr_chopfilter_practical_lifecycle_v1 -v`
  -> `Ran 5 tests`, `OK`.
- 2026-05-30T03:04+0800: Canonical closure/audit/objective unit regressions
  passed:
  `python3 -m unittest support.scripts.research.tests.test_same_tree_practical_closure support.scripts.tests.test_factor_claim_terminalization_audit support.scripts.tests.test_objective_closure_snapshot -v`
  -> `Ran 149 tests`, `OK`.
- 2026-05-30T03:05+0800: Current compact factor audit still returned
  `status=needs_attention`, `promotion_allowed_true=0`, `trade_usable_true=0`,
  and `same_tree_practical_closure=null`. Active blockers included fresh CL and
  MGC claims plus a live NQ regression-channel process. No new provider/AQ
  launch was started in this slice.
- 2026-05-30T03:06+0800: Runtime skill
  `~/.hermes/skills/software-development/ict-engi-fact-rese-muta/SKILL.md`
  updated with the reusable rule: practical-lifecycle wrappers must not
  synthesize one-row readback command evidence; missing staged evidence must
  fail closed.
- 2026-05-30T03:14+0800: `python3 support/scripts/objective_closure_snapshot.py
  --compact --timeout-seconds 240 --output-dir
  /tmp/ict-engine-goal-20260530-codex-after-nq-practical-command-fix`
  returned `status=not_complete`. Remaining blockers included skipped heavy
  done-definition gates, untracked practical-admission source debt, fresh CL
  wait-only claim `20260530T021420+0800-codex-cl-eth-inventory-shock-termstructure-vwap-reclaim-prep.claim`,
  dirty release worktree, and skipped remote release checks. Factor closure
  still had `promotion_allowed_true=0`, `trade_usable_true=0`, and
  `same_tree_practical_closure=null`.

## Terminal Decision For This Slice

This slice fixes one misleading readback/producer loophole. It does not produce
a trade-usable factor, does not clear active runtime/claim blockers, and does
not complete the broad objective. Keep `promotion_allowed=false`,
`trade_usable=false`, and `update_goal=false` until current audit surfaces a
validated same-tree practical closure packet and objective closure passes.
