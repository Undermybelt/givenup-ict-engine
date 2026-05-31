# 2026-05-31 Factor Training Closed-Loop Loophole Audit

## Goal

Answer the current operator question with evidence: whether I can be certain
that ict-engine factor-training direction is optimized and that trained
profitable factors enter and improve the closed loop correctly. If not, find
all observable loopholes, propose and apply reasonable fixes, then repeat the
audit until the evidence is strong enough or the remaining blockers are explicit.

## Current Slice

- Owner: codex
- Started: 2026-05-31T11:08:04+08:00
- Repo: `/Users/thrill3r/projects-ict-engine/ict-engine`
- Branch: `main` ahead of origin; dirty shared worktree
- Runtime workdoc: `/tmp/ict-engine-factor-training-loop-audit-20260531T110804+0800/workdoc.md`
- Claim: `/tmp/ict-engine-agent-claims/board-b-factor-refinement/20260531T110804+0800-codex-factor-training-loop-audit.claim`
- Scope: closed-loop/training-direction loophole audit and focused repairs only
- Non-goals: no provider fetch, no IBKR historical fetch, no AutoQuant/Freqtrade/TOMAC launch, no paper/sim/live launch, no downstream lifecycle launch unless this doc is updated with a new collision audit and exact command scope

## Initial Evidence

- `python3 support/scripts/factor_claim_terminalization_audit.py --compact`
  at 2026-05-31T11:08:04+08:00 reported `status=pass`,
  `active_claims=0`, `live_factor_processes=0`,
  `promotion_allowed_true=0`, `trade_usable_true=0`, and
  `same_tree_practical_closure=null`.
- `ps` scan for ict-engine / TOMAC / AutoQuant / IBKR / provider processes
  returned no matching live runtime process.
- `git status --short --branch` shows a heavily dirty shared worktree. This
  audit must not revert unrelated edits and must stage only its own slice if a
  commit becomes justified.

## Completion Requirements Under Audit

1. A profitable factor cannot be called practical unless current artifacts prove
   the full lifecycle tuple, including data provenance, ETH/full retained session
   scope, verified product cost model, provider/AQ or paper/sim evidence,
   Pre-Bayes, BBN, path ranker, execution tree, feedback update, policy
   training, and accepted execution-feedback source.
2. Training direction must preserve regime-rooted factor grammar and independent
   timeframe treatment while allowing multi-timeframe context/resonance only as
   evidence, not as a shortcut around the exact-origin gate.
3. Gates must fail closed: no sparse positives, Python-only screens, zero-cost
   AQ output, stale Board docs, stale claims, old telemetry, or copied lifecycle
   booleans may promote `promotion_allowed`, `trade_usable`, or `update_goal`.
4. Closed-loop surfaces must expose enough readback for the training loop to
   feed evidence back into Bayes/ranker/policy learning without fabricating
   paper/live/broker execution feedback.
5. Done-definition and source scanners must cover the practical-admission
   surfaces that can emit or validate promotion flags.

## Loophole Ledger

| ID | Loophole | Evidence | Fix / Decision | Status |
| --- | --- | --- | --- | --- |
| L1 | Completion may be inferred from partial green tests or backtest/AQ positives. | Focused workflow tests now reject marker-only same-tree closure and require a validated closure packet for `deploy_ready`/`trade_usable`. | Keep final practical promotion tied to validated same-tree practical closure evidence, not isolated pass rows. | fixed in code; broader scan still open |
| L2 | Runtime docs or source may still allow branch-local admission to leak into promotion flags. | Pending source scanner. | Run practical-admission source audit and patch any fail-open surface. | open |
| L3 | Training direction may overfit to zero-cost or fixed-bps AQ stress instead of verified instrument costs. | Pending source/doc audit. | Verify canonical cost helper and fail-closed fields are enforced. | open |
| L4 | ETH/full retained session scope may be missing from factor workdocs or terminal packets. | Pending source/doc audit. | Require session-scope evidence or keep promotion false. | open |
| L5 | Closed-loop proof may omit accepted execution feedback while still reporting deploy/live readiness. | `policy_training_status_` tests require accepted paper/live/broker execution-feedback markers for live/trade-usable rows; simulated/backtest markers remain blocked. | Split `paper_feedback_collection_ready` from final live/trade usability; accepted execution feedback remains required for final promotion. | fixed in focused Rust surfaces |
| L6 | Done-definition may miss Python helper/report surfaces that can emit practical flags. | Pending `done_definition_audit.py`. | Patch scanner coverage or add tests if a miss is found. | open |

## Verification Log

- 2026-05-31T11:08:04+08:00: claim/runtime compact audit passed with no live runtime blockers and no practical factors surfaced.
- 2026-05-31T12:08:42+08:00: gate-balancing decision implemented:
  keep `trade_usable=true` hard-gated on validated same-tree practical closure
  and accepted paper/live/broker execution feedback, but expose
  `paper_feedback_collection_ready=true` for candidates that are good enough to
  enter paper-feedback collection and train the Bayes/ranker/policy flywheel.
- 2026-05-31T12:08:42+08:00: focused verification passed with isolated target
  `/tmp/ict-engine-cargo-target-closed-loop-balance-20260531T1130`:
  `cargo test profitability_admission::tests -- --nocapture` (12 passed),
  `cargo test workflow_factor_profitability_lifecycle -- --nocapture`
  (8 passed), `cargo test structural_branch_admission -- --nocapture`
  (7 passed), and `cargo test policy_training_status_ -- --nocapture`
  (14 passed across lib/main filters).
- 2026-05-31T12:08:42+08:00: `rustfmt --edition 2021 --check` passed for the
  touched Rust files.
- 2026-05-31T12:08:42+08:00: compact claim audit now reports
  `status=needs_attention` because a foreign live TOMAC/AQ process is running
  under `/tmp/ict-engine-tomac-eth-trend-ote-reacceleration-exact-aqlaunch-20260531T120650+0800`.
  It still reports `promotion_allowed_true=0`, `trade_usable_true=0`, and
  `same_tree_practical_closure=null`; no full objective or practical factor is
  claimed from this slice.
- 2026-05-31T12:10:49+08:00: after terminalizing this no-promotion claim and
  rechecking compact audit, `status=pass`, `active_claims=0`,
  `live_factor_processes=0`, `promotion_allowed_true=0`,
  `trade_usable_true=0`, and `same_tree_practical_closure=null`.

## Current Remaining Blockers

- Do not lower final `trade_usable=true`: the three tickets remain hard gates:
  same-root closed loop, accepted paper/live/broker execution feedback, and
  verified real cost/session evidence.
- The implemented balance point is the intermediate
  `paper_feedback_collection_ready` stage. This creates productive throughput
  into feedback collection without turning paper/sim/backtest evidence into
  practical usability.
- `done_definition_audit.py` previously timed out in the practical-admission
  scanner path; that scanner coverage remains unresolved in this slice.
- Broad fixed-bps debt remains outside the touched Rust core surfaces; broad
  wrapper cleanup is still required before claiming the whole training system is
  loophole-complete.
- Current compact claim audit is clear, but this slice still did not produce a
  practical factor; launching or promoting a candidate still needs a fresh claim
  audit and the full evidence packet.
