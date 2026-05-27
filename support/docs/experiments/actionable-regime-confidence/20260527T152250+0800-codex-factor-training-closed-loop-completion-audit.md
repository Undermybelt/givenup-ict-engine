# Factor Training Closed-Loop Completion Audit

- created_at: `2026-05-27T15:22:50+0800`
- owner: `codex`
- objective:
  `优化ict engine的因子训练方向并保证训练出来的盈利因子进入实战后也能正常作用于闭环中每一环节，且训练途中和进入闭环后能够优化闭环的各个环节`
- scope:
  current-turn evidence audit plus stale-claim cleanup; this document does not
  claim completion

## Deterministic Answer

No. Current evidence does not prove the objective is complete.

Fresh authoritative blockers:

- `python3 support/scripts/factor_claim_terminalization_audit.py --compact`
  at `2026-05-27 15:19 +0800` reported `active_claims=2`,
  `promotion_allowed_true=0`, `trade_usable_true=0`,
  `status=needs_attention`.
- No current same-root run root in this audit slice proves a factor has
  survived the full chain from training through
  provider -> regime -> pre-bayes -> BBN -> path-ranker -> execution tree ->
  feedback/update with live-plane admission true.
- The shared worktree is heavily dirty; there is no current-turn proof that all
  relevant code changes for this objective are isolated, committed, and
  verified as one coherent slice.

## Evidence Readback

### Stale claim cleanup

1. `tomac_tod_balanced_sparse_month_early2021_hour13_gapfill_v1`
   already had terminal artifacts:
   `.../summaries/terminal_decision_summary.md` and
   `.../checks/terminal_metrics.json`.
   Result: `12` rank rows, `0` trades, `0` `5bps` survivors,
   `promotion_allowed=false`, `trade_usable=false`, `update_goal=false`.

2. `tomac_idxfut_clean_prior_day_extreme_continuation_mtf_resonance_guard_participation_quality_guard_1m_v1`
   already had launch output in
   `.../summaries/terminal_summary.json`.
   Result: `status=launch_finished`, `scan_exit=0`, `target_row_count=0`,
   `leaderboard_preview=[]`, `promotion_allowed=false`,
   `trade_usable=false`, `update_goal=false`.

Both claims were still marked active despite no live factor process. This turn
terminalized those `/tmp` claims and synchronized the local workdocs/repo
packets.

## Loopholes Found

### 1. Claim terminalization drift

Problem:
run roots had terminal-grade artifacts, but the `/tmp` claims remained active.
That pollutes Board B occupancy and can block or confuse later lane selection.

Current proof:
the compact claim audit saw `active_claims=2` with `live_factor_processes=0`
before this cleanup.

Reasonable fix:

- make the wrapper/launcher write terminal claim state automatically whenever a
  same-root `terminal_summary.json` or `terminal_decision_summary.md` is
  produced and no child process remains
- add a regression test around `factor_claim_terminalization_audit.py` or the
  relevant wrapper to prove terminal summaries collapse active claims

### 2. No positive live-plane survivor

Problem:
the current evidence bundle proves many fail-closed behaviors, but not that a
profit factor actually survives into a live-usable closed-loop plane.

Current proof:

- Board B current explicitly says `promotion_allowed=false`,
  `trade_usable=false`.
- Fresh claim audit shows zero true counts for both.
- The two freshest same-root lanes in this turn both ended observe-only.

Reasonable fix:

- choose one provider-backed or retained-real same-root lane with clean
  provenance and no stale occupancy
- require a single evidence bundle that proves each transition:
  provider rows, regime posterior, pre-bayes pass, BBN feed, path-ranker
  consumption by execution tree, `fill_viable`, feedback/update writeback
- keep live flags false unless the same-root bundle proves all practical gates

### 3. Training-direction iteration can still die too late or too quietly

Problem:
one lane produced zero trades after four AQ rounds; another produced zero target
rows after a full clean-AQ launch. Those are useful negatives, but they still
consumed board occupancy until a manual audit synchronized the claim state.

Reasonable fix:

- treat `zero trades`, `zero 5bps survivors`, and `target_row_count=0` as
  explicit terminal classes with machine-readable summaries
- promote those classes into wrapper-level early-stop/terminalization helpers
  so they cannot sit as `active_launch_in_progress` after the fact

### 4. Code-level lifecycle guards are stronger than end-to-end proof

Problem:
the repo has lifecycle guard code and tests, but passing guard tests is not the
same as proving a real factor can travel through every live closed-loop stage.

Reasonable fix:

- keep the lifecycle unit/integration tests
- add one same-root end-to-end acceptance packet for the winning branch shape
  with current-turn artifacts, not chat-only reasoning
- gate any “completed” claim on that packet, not only on unit tests

### 5. Dirty-tree ambiguity

Problem:
the current worktree has extensive unrelated modifications/untracked files.
That makes it unsafe to infer which code actually belongs to the objective.

Reasonable fix:

- isolate the next coherent code slice
- verify only the touched owners with focused tests plus the exact closed-loop
  smoke/readback command chain
- commit only that verified slice

## Next Minimum Safe Actions

1. Re-run `python3 support/scripts/factor_claim_terminalization_audit.py --compact`
   and verify the stale active claims are gone.
2. Choose one unblocked same-root lane only after the refreshed occupancy read.
3. For that lane, demand one compact evidence packet that proves:
   provider rows, regime posterior, pre-bayes, BBN handoff, ranker consumed by
   execution tree, `fill_viable`, feedback/update artifact, and final practical
   flags.
4. If code changes are needed to automate stale-claim terminalization, do them
   with focused tests first and commit the isolated slice.

## 2026-05-27 Code Fix Slice

This loophole is no longer docs-only.

Implemented in:

- `support/scripts/factor_claim_terminalization_audit.py`
- `support/scripts/tests/test_factor_claim_terminalization_audit.py`

Behavior change:

- the audit now reads `summaries/terminal_summary.json` in addition to the
  existing terminal summary candidates
- if the run root already contains a terminal artifact that carries a terminal
  decision or a finished terminal status, the claim is treated as
  `terminalized` even when the claim file itself still says `status=active`

Why this is aligned:

- it does not invent trade readiness
- it only collapses stale active debt when the run root already proves the lane
  ended
- `live_factor_processes` still blocks closure independently, so active runtime
  work is not hidden by this inference

Verification:

- `python3 -m unittest support.scripts.tests.test_factor_claim_terminalization_audit.FactorClaimTerminalizationAuditTest.test_build_report_treats_run_root_terminal_artifacts_as_terminalized_even_if_claim_status_is_active -v`
  -> `OK`
- `python3 -m unittest support.scripts.tests.test_factor_claim_terminalization_audit -v`
  -> `Ran 43 tests`, `OK`
- `python3 support/scripts/factor_claim_terminalization_audit.py --compact`
  after the fix no longer resurfaced the two stale claims cleaned in the prior
  slice; attention moved to newer genuinely active claims/live processes

## Completion Standard For This Objective

Do not answer “completed” until current evidence proves all of the following in
the same rooted line:

- training direction is improved by current code/docs, not only proposed
- the selected profitability factor survives training under declared gates
- every closed-loop stage is materially exercised by current artifacts
- live practical flags are true only when all same-root live-plane gates pass
- the changes are isolated, verified, and committed when code was modified
