# Factor Training Closed-Loop Certainty Audit - 2026-05-31

Owner: `codex`
Route: `local/ict-engi-fact-rese-muta`
Repo: `/Users/thrill3r/projects-ict-engine/ict-engine`
Branch at start: `main`
Run root: `/tmp/ict-engine-closed-loop-certainty-audit-20260531T110523+0800`
Claim: `/tmp/ict-engine-agent-claims/board-b-factor-refinement/20260531T110523+0800-codex-closed-loop-certainty-audit.claim`

## Goal

Answer the user's current objective without pretending certainty:

- determine whether `ict-engine` factor training direction is fully optimized;
- prove or disprove that trained profitability factors can safely enter and
  improve every closed-loop stage;
- find loopholes in training gates, practical admission, feedback, and readback;
- propose and apply reasonable fixes where current evidence supports a code or
  documentation change;
- commit only verified code changes for the current coherent slice.

## Current Verdict

Status: `not_proven_not_complete`

I do not have 100% confidence that the objective is complete.

Fresh evidence already contradicts a completion claim:

- compact claim audit at `2026-05-31T03:05:24Z` reported
  `status=pass`, `promotion_allowed_true=0`, `trade_usable_true=0`, and
  `same_tree_practical_closure=null`;
- focused process scan at `2026-05-31T11:05+0800` then showed new foreign
  runtime activity under
  `/tmp/ict-engine-volume-clock-relative-participation-autoquant-training-20260531T110428+0800`,
  plus a `cargo test workflow_factor_profitability_lifecycle` process;
- therefore no provider, IBKR, Auto-Quant/Freqtrade/TOMAC, paper/sim/live,
  downstream lifecycle, feedback-ingest, or practical-closure runtime launch is
  legal from this slice until a later same-turn claim/process guard clears.

Practical flags for this audit:

- `promotion_allowed=false`
- `trade_usable=false`
- `update_goal=false`
- `same_tree_practical_closure=null`
- `runtime_launch_allowed=false`

## Evidence Commands

Run so far:

```bash
git status --short --branch
python3 support/scripts/factor_claim_terminalization_audit.py --compact
ps -axo pid,ppid,etime,command | rg -i 'run_tomac|tomac|factor|auto.?quant|freqtrade|run_tomac_one|fetch_external|ibkr|provider-status|paper|real-trades|auto-quant-ingest-real-trades'
python3 support/scripts/done_definition_audit.py --compact --output /tmp/ict-engine-closed-loop-certainty-audit-20260531T110523+0800/done_definition_audit.json
```

The `done_definition_audit.py` command was still running when this document was
created; its result must be appended before relying on this audit.

## Loophole Ledger

### L-001: No current same-tree practical closure packet

Severity: critical

Evidence: compact claim audit reports `same_tree_practical_closure=null` and
zero positive `promotion_allowed` / `trade_usable` counts.

Risk: a training packet, local screen, exact-AQ replay, or lifecycle readback
could be mistaken for a real closed-loop proof.

Solution: completion must require a validated
`same_tree_practical_closure.json` produced by
`support/scripts/research/same_tree_practical_closure.py` and surfaced by the
claim audit with `evidence_packet_validated=true`.

### L-002: Runtime occupancy changed after a clean compact audit

Severity: high

Evidence: compact audit initially passed, but the later focused `ps` saw a
foreign local-gate factor process and a lifecycle cargo test.

Risk: a launcher could start between audit and execution, causing duplicate
ownership or shared backend collision.

Solution: any launch-capable wrapper must re-run a final in-process full audit
and focused process guard immediately before provider/AQ/runtime work, allowing
only its own exact run root/PID.

### L-003: Practical flags can be over-inferred from partial success

Severity: high

Evidence basis: current runtime skill forbids treating RTH-only evidence,
fixed-bps fields, Python-only/local-screen positives, path-ranker-visible but
not execution-used scores, simulated backtest rows, or local admission as
`trade_usable`.

Risk: `promotion_allowed=true`, `trade_usable=true`, or `update_goal=true`
could be set without ETH/full-session, official cost, accepted feedback, and
full lifecycle proof.

Solution: audit every practical-admission source and wrapper assignment. The
safe default is `practical_admission_flags(branch_local_admitted,
extension_complete=False)` unless a validated same-tree closure packet proves
the full lifecycle.

### L-004: Feedback source ambiguity can fake closed-loop learning

Severity: high

Evidence basis: accepted practical feedback must be paper/live/broker execution
feedback with broker/fill evidence. IBKR provider readiness, historical bars,
Auto-Quant backtests, retained-label simulations, and simulated feedback are
not accepted execution feedback.

Risk: policy training and posterior updates could learn from simulated labels
while the readback presents paper-ready/live-ready semantics.

Solution: require `broker_realized=true`, `broker_fill_evidence=true`, and an
accepted source marker before practical closure. Empty IBKR execution readbacks
must stop at preflight.

### L-005: Session and cost gates are still possible bypass points

Severity: high

Evidence basis: current skill requires `session_scope=ETH/full_retained_session`,
`rth_filter_applied=false`, retained non-RTH rows, and official instrument-cost
verification. Fixed bps labels are not current cost authority.

Risk: profitable-looking RTH-only or fixed-bps rows can be promoted into a
full-session objective.

Solution: every candidate packet and closure evidence packet must include
session coverage and official cost-model fields. Missing or stale cost/session
proof keeps practical flags false.

### L-006: Dirty worktree prevents broad completion confidence

Severity: high

Evidence: `git status --short --branch` shows a broad dirty tree with many
modified and untracked objective-adjacent files.

Risk: focused green tests may not cover all changed practical surfaces, so the
audited tree can still contain fail-open behavior.

Solution: only claim verified coherent slices. Preserve unrelated dirty work,
stage only current audited edits, and do not mark the full objective complete
until current-tree end-to-end evidence covers the actual changed surfaces.

## Next Steps

1. Wait for `done_definition_audit.py` and record its exact result.
2. Re-run compact claim audit and focused process scan before any runtime
   decision.
3. Inspect practical-admission source-scan failures, if any, and patch only
   current-tree fail-open code with focused tests.
4. Verify same-tree closure helper semantics and real-trade feedback labeling
   tests.
5. If runtime clears later, run only the next legal preflight for accepted
   broker/paper feedback before any lifecycle rerun.
6. Keep this document append-only for findings, fixes, commands, evidence, and
   commit status.

## 2026-05-31T11:36+0800 Continuation Readback

Continuation note: a platform-provided handoff summary was treated as degraded
context and rechecked against real local files, `/tmp` artifacts, and current
process/claim state before acting.

Fresh evidence:

- `done_definition_audit_after_scoped_parallel_scan.json` exists and reports
  `status=pass`, `completion_ready=false`, `pass_count=6`, `skip_count=4`, with
  heavy gates skipped: `cargo_check_all_targets`,
  `cargo_clippy_all_targets_deny_warnings`, `cargo_test`, and
  `smoke_acceptance_tmp_state`.
- `practical_admission_source_scan_current.json` exists with `49` scanned
  entries and `0` entries where `ok=false` or `violations` is non-empty.
- Current compact claim audit reports `status=needs_attention`,
  `promotion_allowed_true=0`, `trade_usable_true=0`,
  `same_tree_practical_closure=null`, `live_factor_processes=0`, and one fresh
  active overlapping claim:
  `/tmp/ict-engine-agent-claims/board-b-factor-refinement/20260531T113047+0800-codex-balanced-factor-gates.claim`.
- The fresh overlapping claim scope is
  `code-only balanced profitability factor gate adjustment`; its workdoc is
  `/tmp/ict-engine-balanced-factor-gates-20260531T113047+0800/workdoc.md`, with
  explicit non-goal `no gate lowering for trade_usable`.
- Focused process readback also showed a separate long-running heavy
  `done_definition_audit.py --run-all-heavy` under
  `/tmp/ict-engine-closed-loop-loophole-audit-20260531T110505+0800`.

Decision:

- Do not take over or duplicate the fresh `balanced-factor-gates` lane.
- Do not lower final `trade_usable` / `promotion_allowed` hard gates.
- Treat the user's product/quality flywheel request as a lifecycle separation
  problem: allow earlier `learning` / `calibration` / `shadow or paper`
  admissions to collect evidence, while keeping final practical closure blocked
  until same-tree closure, accepted paper/live/broker execution feedback,
  verified real cost, and ETH/full-retained session evidence all pass.

Current practical flags remain:

- `promotion_allowed=false`
- `trade_usable=false`
- `update_goal=false`
- `same_tree_practical_closure=null`

## 2026-05-31T11:52+0800 Goal Continuation Readback

Fresh routing was repeated for the persistent objective. Current route remains
`sd/ict-engi-fact-rese-muta`; installed runtime skill
`~/.hermes/skills/software-development/ict-engi-fact-rese-muta/SKILL.md` was
used.

Current claim/process state:

- `python3 support/scripts/factor_claim_terminalization_audit.py --compact`
  at `2026-05-31T11:41+0800` reported `status=needs_attention`,
  `live_factor_processes=0`, `promotion_allowed_true=0`,
  `trade_usable_true=0`, `same_tree_practical_closure=null`, and one fresh
  overlapping active claim:
  `/tmp/ict-engine-agent-claims/board-b-factor-refinement/20260531T113047+0800-codex-balanced-factor-gates.claim`.
- That claim's workdoc is
  `/tmp/ict-engine-balanced-factor-gates-20260531T113047+0800/workdoc.md`; its
  scope is `code-only balanced profitability factor gate adjustment` and its
  active task is separating flywheel learning admission from final
  `trade_usable` promotion.
- Several unrelated `done_definition_audit.py` / smoke commands were running;
  no provider/AQ/IBKR/Freqtrade/TOMAC live factor process was surfaced by the
  compact audit.

Verification readback:

- `cargo test -q --lib flywheel_learning_admits_moderate_regime_confidence_without_live_promotion -- --nocapture`
  passed: `1 passed; 0 failed; 1232 filtered out`.
- `cargo test -q --lib accepted_feedback_cannot_promote_below_strict_live_regime_floor -- --nocapture`
  passed: `1 passed; 0 failed; 1232 filtered out`.
- `cargo test -q --lib profitability_admission -- --nocapture` passed:
  `12 passed; 0 failed; 1221 filtered out`.

Observed current-tree progress from the active `balanced-factor-gates` lane:

- `src/application/factor_lifecycle/profitability_admission.rs` now separates
  `FLYWHEEL_REGIME_CONFIDENCE_FLOOR=0.75` from final live readiness checks.
- The live decision now keeps `promotion_allowed`, `trade_usable`, and
  `update_goal` false unless paper feedback collection is ready, accepted
  execution feedback exists, and the stricter live regime-confidence floor
  passes.

New loophole candidate found for later repair, not modified in this slice:

- `support/scripts/research/factor_candidate_pack.py` still computes
  `learning_admission` by comparing `regime_confidence` directly against
  `candidate_spec.get("regime_confidence_floor", 0.95)`.
- That means the Python candidate-pack/factor-intake surface may still be too
  binary for the requested flywheel: a candidate that should enter learning or
  calibration at the new flywheel floor can remain blocked at the old live
  floor, while final `live_trade` remains correctly fail-closed.
- Recommended follow-up after the fresh `balanced-factor-gates` owner
  terminalizes or becomes stale-safe: add a Python-side flywheel learning floor
  test to `support/scripts/research/tests/test_factor_candidate_pack.py`, then
  update `_factor_profitability_lifecycle(...)` so learning/calibration
  admission can use the flywheel floor without setting `promotion_allowed`,
  `trade_usable`, or `update_goal`.

Decision:

- Do not take over or edit the fresh `balanced-factor-gates` code lane.
- Keep the full objective active. The current evidence proves useful progress
  on threshold balance, but it does not prove full closed-loop completion.
- Practical flags remain `false` until a validated same-tree practical closure
  packet with accepted execution feedback, verified cost, and ETH/full-retained
  session evidence exists.

## 2026-05-31T12:02+0800 Candidate-Pack Flywheel Repair

The `balanced-factor-gates` claim was no longer surfaced as an active attention
claim in compact audit, but a live TOMAC/AQ runtime was active under
`/tmp/ict-engine-tomac-tsmom-vol-scaled-low-turnover-aq-20260531T115002+0800`.
Therefore this slice stayed code-only and did not launch provider/AQ/runtime.

TDD route:

- RED:
  `python3 -m unittest support.scripts.research.tests.test_factor_candidate_pack.FactorCandidatePackTests.test_candidate_pack_flywheel_learning_uses_lower_floor_without_trade_promotion -v`
  failed as expected because `learning_admission` was `blocked` for
  `regime_confidence=0.80` with live floor `0.95`.
- GREEN:
  `support/scripts/research/factor_candidate_pack.py` now defines
  `DEFAULT_REGIME_CONFIDENCE_FLOOR=0.95` and
  `FLYWHEEL_REGIME_CONFIDENCE_FLOOR=0.75`. `_factor_profitability_lifecycle(...)`
  uses the flywheel floor for `learning_admission` only and records both
  learning and live floors in the learning packet. `live_trade` still stays
  `blocked` with false practical flags. The related Rust lifecycle surface also
  exports `FLYWHEEL_REGIME_CONFIDENCE_FLOOR` via
  `src/application/factor_lifecycle/mod.rs`.

Verification:

- RED command failed before implementation with
  `AssertionError: 'blocked' != 'admitted'`.
- After implementation, the new test passed.
- Existing lifecycle test
  `test_candidate_pack_emits_factor_profitability_lifecycle_for_regime_conditioned_edge`
  passed.
- Full Python suite passed:
  `python3 -m unittest support.scripts.research.tests.test_factor_candidate_pack -v`
  with `18 tests`, `OK`.

Skill sync:

- Updated
  `~/.hermes/skills/software-development/ict-engi-fact-rese-muta/SKILL.md`
  with the durable rule: lower flywheel learning floors may admit candidates for
  learning/calibration, but final `promotion_allowed`, `trade_usable`,
  `update_goal`, deploy-ready, and same-tree practical closure still require
  strict live gates, accepted execution feedback, verified cost,
  ETH/full-retained session, and downstream lifecycle proof.

Current practical flags remain:

- `promotion_allowed=false`
- `trade_usable=false`
- `update_goal=false`
- `same_tree_practical_closure=null`

## 2026-05-31T12:18+0800 Current-Tree Recheck

This recheck treated the platform handoff summary as stale until current repo,
claim, process, and source evidence was read again.

Fresh current-state evidence:

- `git log --oneline -6` shows the current HEAD is
  `19771dc1 Require accepted execution feedback for policy lifecycle`, after
  `bc1b5757 Balance factor flywheel admission gates`.
- `python3 support/scripts/factor_claim_terminalization_audit.py --compact`
  reported `status=needs_attention`, `live_factor_processes=1`,
  `promotion_allowed_true=0`, `trade_usable_true=0`, and
  `same_tree_practical_closure=null`.
- The live runtime root is
  `/tmp/ict-engine-tomac-tsmom-vol-scaled-low-turnover-aq-20260531T115002+0800`
  under `run_tomac_index_futures_clean_aq_v1.py`; runtime launch remains
  disallowed from this slice.
- Focused process scan also showed unrelated heavy done-definition/smoke
  commands still running. This slice did not start provider, IBKR, AQ, TOMAC,
  paper, live, or downstream lifecycle work.

Low-collision verification:

- `python3 -m unittest support.scripts.research.tests.test_factor_candidate_pack.FactorCandidatePackTests.test_candidate_pack_flywheel_learning_uses_lower_floor_without_trade_promotion -v`
  passed. This proves candidate-pack learning can admit a moderate-confidence
  flywheel candidate without setting practical flags.
- `python3 -m unittest support.scripts.research.tests.test_real_trade_feedback_labels.RealTradeFeedbackLabelsTests.test_ibkr_execution_readback_without_round_trip_writes_zero_rows -v`
  passed. This proves an incomplete execution readback terminalizes as
  `accepted_execution_feedback_missing` with false practical flags.
- `python3 support/scripts/research/downstream_practical_admission_source_check.py --tracked-run-wrappers --jobs 4 --pretty`
  completed with every tracked wrapper entry reporting `ok=true` and
  `violations=[]`.

Decision:

- The balanced gate design is correct for the user's throughput/quality request:
  lower-friction `learning` / calibration / paper-feedback collection stages can
  feed the flywheel, but final `promotion_allowed`, `trade_usable`, and
  `update_goal` remain false until same-tree practical closure, accepted
  paper/live/broker execution feedback, verified real cost, and ETH/full-retained
  session evidence all pass.
- Current practical flags remain false:
  `promotion_allowed=false`, `trade_usable=false`, `update_goal=false`,
  `same_tree_practical_closure=null`.
