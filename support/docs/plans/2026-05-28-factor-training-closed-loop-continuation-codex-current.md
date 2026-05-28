# Factor Training Closed-Loop Continuation - 2026-05-28 Current Readback

Owner: Codex
Status: active / objective not complete
Route: `sd/ict-engi-fact-rese-muta`

## Scope

This file tracks the current continuation of the user's full objective: optimize
`ict-engine` factor-training direction and prove that any trained profitability
factor can pass the real closed loop without weakening training-time or
post-training gates. This is not a completion claim.

## Current Evidence

- Routing completed through `~/.hermes/routing/skill-router.md`,
  `~/.hermes/routing/project-router.md`, repo `CLAUDE.md`, repo `AGENTS.md`,
  repo `AGENT.md`, and installed runtime skill
  `~/.hermes/skills/software-development/ict-engi-fact-rese-muta/SKILL.md`.
- Focused verification for the practical-admission debt packet work passed:
  `python3 -m unittest support.scripts.tests.test_done_definition_audit -v`
  ran `21/21 OK`.
- Focused verification for the objective closure snapshot work passed:
  `python3 -m unittest support.scripts.tests.test_objective_closure_snapshot -v`
  ran `21/21 OK`.
- `git diff --check` on the touched audit/script/test/tracker slice passed.
- `python3 support/scripts/objective_closure_snapshot.py --compact --output-dir /tmp/ict-engine-goal-20260528-codex-current-verification-no-remotes`
  intentionally exited red and wrote a packet with
  `summary.status=not_complete`.

## Current Blockers

The latest no-remote objective snapshot at
`/tmp/ict-engine-goal-20260528-codex-current-verification-no-remotes/` reports:

- `done_definition_not_completion_ready`: heavy done-definition gates were not
  run in this quick verification packet.
- `practical_admission_source_debt`: the current worktree still contains
  `193` untracked practical-admission wrapper violations across `115` files,
  even though tracked violations are `0`.
- `factor_closure_blocked`: Board B still has fresh active claims without live
  runtimes, including the fresh greedy-filtered clean downstream repair claim
  and a wait-only Aroon/CCI cadence-lift claim.
- `release_readiness_blocked`: the worktree is not clean for release/source
  attribution.

## Decision

I cannot honestly answer yes to the full objective. The current code/test slice
improves the closure audit by making practical-admission debt packetized and
portable, but the full objective still requires a same-tree practical closure
packet with `promotion_allowed_true>0` and `trade_usable_true>0`, clean
attributable source, and fully run done-definition/release gates.

## Next Safe Actions

1. Do not launch another Board B TOMAC/AQ lane while fresh active claims exist.
2. Wait for or inspect the fresh active claims after owner progress or
   stale-safe timeout, then rerun
   `python3 support/scripts/factor_claim_terminalization_audit.py --compact`.
3. Retire, quarantine, or intentionally track the untracked practical-admission
   wrapper debt before any objective-closure or release claim.
4. Produce or locate one same-tree practical closure packet that proves the
   provider -> training/admission -> Pre-Bayes -> BBN -> path-ranker ->
   execution tree -> feedback path without promotion shortcuts.
