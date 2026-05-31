# Factor Training Closed-Loop Loophole Audit

- Created: 2026-05-31T11:10:50+08:00
- Owner: codex-factor-training-closed-loop-loophole-audit
- Repo: ict-engine checkout root
- Branch: main
- Workdoc: `/tmp/ict-engine-factor-training-closed-loop-loophole-audit-20260531T111050+0800/workdoc.md`
- Claim: `/tmp/ict-engine-agent-claims/board-b-factor-refinement/20260531T111050+0800-codex-factor-training-closed-loop-loophole-audit.claim`
- Status: terminalized no-launch duplicate/partial audit; no provider, IBKR historical, AutoQuant, Freqtrade/TOMAC, paper/sim/live, downstream lifecycle, or local backtest was launched.

## User Objective

Answer honestly whether there is 100% current evidence that ict-engine's factor-training direction is optimized and that any profitable factor entering practical use works through every closed-loop stage, while training and post-admission feedback can improve every stage. If not, find every plausible loophole, propose and implement reasonable fixes, repeat the audit, and commit verified code changes made for this slice.

## First-Principles Review

- First principle: a factor is not practically usable until the same rooted branch proves data, regime, Pre-Bayes, BBN, path ranker, execution tree, feedback/update, policy training, cost, session scope, validation, and paper/sim or accepted execution-feedback readiness with current artifacts.
- Non-negotiables: no lowered gates; no RTH-only substitution for the default ETH/full-retained target; no fixed-bps futures authority; no simulated/backtest feedback relabeled as paper/live/broker feedback; no board docs as active state; no collision with other agents' runtime.
- Assumptions to drop: positive Gate 1, zero-exit AutoQuant, route readiness, or a marker-only `trade_usable=true` field is not enough.
- Smallest sufficient path: create this audit surface, inspect current claim/runtime state, inspect canonical practical-closure and lifecycle gates, add focused tests for any proven loophole, patch only the canonical owner, then re-run the focused verifier.
- Escalation signal: if practical readiness has more than one canonical owner, or if a claim/audit surface can promote without the canonical same-tree closure helper validating the complete evidence packet, split owner repair before further factor training.

## Completion Requirements

- [ ] Current-state routing, repo instructions, worktree status, compact claim audit, and live process audit are recorded.
- [ ] A loophole matrix covers training direction, gate semantics, same-tree practical closure, provider/AutoQuant/paper feedback, cost/session scope, claim/runtime collisions, and feedback learning.
- [ ] Every confirmed code loophole has an owner, a focused failing test or source check, a minimal fix, and verification output.
- [ ] Any code changes from this slice are committed without staging unrelated dirty work.
- [ ] Final state says either `complete_with_evidence`, `partial_needs_more_evidence`, or `blocked_by_external_runtime`, with exact artifacts.

## Loophole Matrix

| ID | Area | Risk | Evidence | Decision | Fix |
|---|---|---|---|---|---|
| L1 | Current runtime ownership | Other agents may own live factor/AQ/provider work; duplicate launch would corrupt evidence. | `python3 support/scripts/factor_claim_terminalization_audit.py --compact` returned `needs_attention` with `live_factor_processes=2`, `active_claims=6`, `promotion_allowed_true=0`, `trade_usable_true=0`, `same_tree_practical_closure=null`; focused ps showed live `run_tomac_volume_clock_relative_participation...` and `run_tomac_eth_trend_ote_reacceleration...`. | Confirmed blocker for launches and overlapping repairs. | Do not launch. Re-audit immediately before any future runtime action. |
| L2 | Practical closure authority | Marker fields may claim `promotion_allowed`/`trade_usable` without canonical same-tree evidence validation. | `support/scripts/research/same_tree_practical_closure.py` requires staged command rows, lifecycle tuple, accepted feedback, session scope, and verified cost; `support/scripts/factor_claim_terminalization_audit.py` validates the evidence packet. `src/application/orchestration/workflow_status.rs` accepted marker booleans such as `same_tree_practical_closure_validated=true` through `practical_closure_validated_for_value(...)`. | Confirmed code loophole; repaired in follow-up doc `20260531T112201+0800-codex-workflow-status-marker-closure-repair.md`. | Rust workflow status now accepts only a structured validated `same_tree_practical_closure` packet for final practical promotion; marker-only regression fails closed. |
| L3 | Training direction | Gate-1 positive or source-backed ideas may not feed Pre-Bayes/BBN/path-ranker/execution-tree/feedback. | Canonical helper requires ordered stages: `provider_data`, `pre_bayes`, `bbn_workflow`, `path_ranker`, `execution_tree`, `feedback_update`, `policy_training`; current compact audit has no validated closure packet. | Not complete; no practical factor proven. | Keep training direction tied to same-root staged command rows; do not count source/Gate-1 only rows. |
| L4 | Cost/session scope | Old fixed bps, unverified futures cost, or RTH-only rows may leak into practical status. | Canonical helper currently requires `session_scope` ETH/full-retained, `rth_filter_applied=false`, non-RTH retained rows, `promotion_cost_verified=true`, complete cost model fields, and official source refs with HTTP 200/rate verification. | Helper appears guarded; still needs focused test run by active repair owner. | Keep as mandatory closure gate; do not promote fixed-bps or RTH-only evidence. |
| L5 | Paper/sim/live feedback | Simulated backtest rows may be relabeled as accepted paper/live/broker execution feedback. | Canonical helper allowlists paper/live/broker execution markers and rejects simulated/backtest/retained-label markers; NQ compound runtime claim terminalized with no promotion/trade use. | Helper appears guarded; current practical count remains zero. | Preserve strict allowlist; require real accepted feedback source for closure. |
| L6 | Learning feedback | `update` or policy feedback may ingest loose outcomes without structural linkage and look like loop optimization. | Pending workflow/status inspection. | Pending | Require structural linkage before learning/paper/live readiness counts. |
| L7 | Claim audit | Stale claims, workdoc terminalization, or same-tree packets may be misclassified. | Pending compact audit and tests. | Pending | Patch claim audit or tests if current classification leaks. |

## Evidence Log

- 2026-05-31T11:10:50+08:00: Tracking doc created. No completion claim. No runtime launch.
- 2026-05-31T11:12:45+08:00: Compact claim audit returned `needs_attention`, `active_claims=6`, `live_factor_processes=2`, `fresh_active_claims_without_live_process=4`, `promotion_allowed_true=0`, `trade_usable_true=0`, `same_tree_practical_closure=null`.
- 2026-05-31T11:15:00+08:00: Read overlapping workdocs. Fresh active owners already cover closed-loop certainty/gap audit and practical root-cause repair. This slice must not patch those same files unless those claims terminalize or are explicitly handed over.
- 2026-05-31T11:18:00+08:00: Source readback found canonical Python helper/audit validation is strict, but Rust workflow status still had a marker-boolean practical-closure path. Recorded as L2.
- 2026-05-31T11:20:00+08:00: Terminalized this claim as duplicate/no-launch. Completion is not proven.
- 2026-05-31T11:18:29+08:00: Verification compact audit no longer counts this slice as an active blocker. Remaining blocker is fresh `20260531T110523+0800-codex-closed-loop-certainty-audit.claim`; `live_factor_processes=0`, `promotion_allowed_true=0`, `trade_usable_true=0`, `same_tree_practical_closure=null`.
- 2026-05-31T11:56:45+08:00: L2 was repaired in `20260531T112201+0800-codex-workflow-status-marker-closure-repair.md`. Full objective remains incomplete because no validated same-tree practical closure packet or `trade_usable=true` factor exists in current compact audit.

## Current Terminal Status

- terminal_status: `partial_loophole_audit_with_l2_repaired`
- promotion_allowed=false
- trade_usable=false
- update_goal=false
- same_tree_practical_closure=null
- full_objective_complete=false
