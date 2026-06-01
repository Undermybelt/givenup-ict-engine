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

### L-007: Accepted execution-feedback marker spoofing

Severity: critical

Evidence: current-tree focused test
`test_rejects_spoofed_accepted_execution_feedback_substring` initially failed.
The same-tree closure helper accepted
`audit:not_paper_execution_feedback:factor_v1` because the accepted
`paper_execution_feedback` marker was matched as a substring.

Risk: a source label that explicitly says "not paper execution feedback" could
still satisfy the accepted-feedback stage, allowing policy/lifecycle or
same-tree closure proof to become `trade_usable=true` without real accepted
paper/live/broker feedback.

Solution: accepted paper/live/broker execution-feedback markers must match
source tokens exactly. Keep simulated markers conservatively rejected. Apply the
same repair to Python same-tree closure, Python accepted-feedback conversion,
Rust policy-training status, and Rust structural target export/readback.

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

## 2026-05-31T16:09+0800 Second-Pass Feedback-Collection Guard

Fresh compact claim audit before this source-only repair reported `status=pass`,
`active_claims=0`, `live_factor_processes=0`, `promotion_allowed_true=0`,
`trade_usable_true=0`, and `same_tree_practical_closure=null`.

Finding:

- The first feedback-collection guard still allowed legacy `ready/actionable`
  readback to stand in for an explicit feedback-collection flag.
- Structural branch admission could also mark feedback collection ready from
  ranker runtime and matured confirmation text without explicit 12/12/12
  validation rows.

Repair and verification:

- Removed the `ready/actionable` consumer fallback.
- Required structural branch admission to prove raw-scored mature, production
  validation, and observation validation rows each meet the 12-row feedback
  collection floor before emitting `paper_feedback_collection_ready=true`.
- Added and turned green:
  `workflow_factor_profitability_lifecycle_rejects_ready_actionable_without_feedback_collection_flag`
  and
  `structural_branch_admission_blocks_feedback_collection_without_validation_rows`.
- `cargo test workflow_factor_profitability_lifecycle -- --nocapture` passed
  `11` tests.
- `cargo test structural_branch_admission -- --nocapture` passed `8` tests.

Current practical flags still remain false; this is an admission-quality repair,
not a practical-promotion claim.

Post-terminalization readback:

- Compact claim audit after terminalizing this source-only claim reported
  `status=pass`, no active claims, no live factor processes, and no positive
  practical flags.
- Objective snapshot at
  `/tmp/ict-engine-goal-consumer-revalidation-audit-20260531T152928+0800/objective_snapshot_after_feedback_collection_consumer_guard/objective_closure_snapshot.json`
  returned `status=not_complete`, `completion_proven=false`,
  `same_tree_practical_closure=null`, `promotion_allowed_true=0`, and
  `trade_usable_true=0`.

## 2026-05-31T17:06+0800 Current-Head Recheck

Current HEAD: `6591a02294175dacdde8f0c482f038cf705580e6`
(`6591a022 Fix done proof count merge`).

Fresh current-state evidence:

- Compact claim/runtime audit:
  `python3 support/scripts/factor_claim_terminalization_audit.py --compact`
  returned `status=pass`, `active_claims=0`, `live_factor_processes=0`,
  `promotion_allowed_true=0`, `trade_usable_true=0`, and
  `same_tree_practical_closure=null`.
- Focused process scan showed no live factor/provider/AQ/IBKR process beyond
  the audit/readback commands themselves.
- Python verification passed:
  `python3 -m unittest support.scripts.research.tests.test_same_tree_practical_closure support.scripts.research.tests.test_real_trade_feedback_labels support.scripts.tests.test_factor_claim_terminalization_audit -v`
  ran `164` tests, `OK`.
- `python3 -m py_compile` passed for the touched Python closure/feedback
  scripts and tests.
- `rustfmt --edition 2021 --check` passed for the touched Rust closure,
  workflow, analyze, and profitability admission files.
- Rust focused verification passed under
  `CARGO_TARGET_DIR=/tmp/ict-engine-cargo-target-closed-loop-current-20260531`:
  `cargo test -q --lib execution_feedback -- --nocapture` (`4` passed),
  `cargo test -q --lib workflow_factor_profitability_lifecycle -- --nocapture`
  (`11` passed),
  `cargo test -q --lib structural_branch_admission -- --nocapture` (`8`
  passed),
  `cargo test -q same_root_admission_practical_closure -- --nocapture` (`3`
  passed), and `cargo test -q evidence_validated_alias -- --nocapture` (`2`
  passed across lib/bin targets).
- `git diff --check` passed.

Current objective snapshot:

```bash
python3 support/scripts/objective_closure_snapshot.py \
  --compact \
  --check-remotes \
  --timeout-seconds 360 \
  --output-dir /tmp/ict-engine-objective-current-6591a022-codex-20260531T1658
```

Result:

- `summary.status=not_complete`
- `completion_proven=false`
- blockers:
  - `done_definition_not_completion_ready`
  - `same_tree_practical_closure_unproven`
  - `release_readiness_blocked`
- done-definition child at the same head passed light gates but skipped heavy
  gates: `cargo_check_all_targets`, `cargo_clippy_all_targets_deny_warnings`,
  `cargo_test`, and `smoke_acceptance_tmp_state`.
- practical-admission, await-launch, and fixed-bps source debts remain
  quarantined untracked debt; tracked violation counts are `0`.
- release readiness remains blocked by `worktree_clean_for_release` and
  `source_origin_matches_selected_source`, although remote readback passed for
  both origin and release mirror in this packet.

Decision:

- The accepted-feedback spoof and closure-packet/readback loopholes remain
  repaired under focused tests, including the separator form
  `not-paper_execution_feedback`.
- The full user objective is still not complete because there is no validated
  same-tree practical-closure packet and no proof that a profitable factor has
  passed every practical closed-loop stage.
- Current practical flags remain `promotion_allowed=false`,
  `trade_usable=false`, `update_goal=false`, and
  `same_tree_practical_closure=null`.

## 2026-05-31T17:34+0800 Negated Feedback Marker Window Repair

Current HEAD during final readback: `b59cf72ca89dbdb4f0107aa009fcf2e36d480924`
(`b59cf72c docs: record rsrs factor closure readback`).

No-launch workdoc:
`/tmp/ict-engine-closure-gap-source-audit-20260531T171900+0800/workdoc.md`.

Finding:

- The accepted execution-feedback source marker repairs still checked only the
  immediate previous token for negation.
- RED tests proved that `without-broker-paper_execution_feedback` could still
  pass Python same-tree closure, Python accepted-feedback conversion, Rust
  policy-training status, and Rust structural target export.
- This is a practical-closure proof spoof because the label explicitly negates
  broker/paper execution feedback while retaining an exact
  `paper_execution_feedback` token.

Repair:

- Python same-tree closure and accepted-feedback conversion now reject an
  accepted source marker when a negating token appears within the prior 3 source
  tokens.
- Rust policy-training and structural-playbook accepted-feedback checks use the
  same fail-closed lookback.
- Hermes runtime skill
  `/Users/thrill3r/.hermes/skills/software-development/ict-engi-fact-rese-muta/SKILL.md`
  was updated so the lesson is durable.

Verification:

- RED before fix:
  `test_rejects_negated_accepted_execution_feedback_token`,
  `test_build_accepted_paper_execution_feedback_requires_broker_fill_evidence`,
  `policy_training_status_rejects_spoofed_execution_feedback_substring`, and
  `target_export_does_not_mark_spoofed_aggregate_feedback_substring_as_live_trade_usable`
  failed on the `without-broker-paper_execution_feedback` shape.
- GREEN after fix:
  `python3 -m unittest support.scripts.research.tests.test_same_tree_practical_closure support.scripts.research.tests.test_real_trade_feedback_labels -v`
  passed `37` tests.
- `python3 -m py_compile` passed for touched Python files.
- `rustfmt --edition 2021 --check` passed after formatting touched Rust files.
- Rust focused filters passed under
  `/tmp/ict-engine-cargo-target-negation-window-20260531`:
  `policy_training_status_rejects_spoofed_execution_feedback_substring`,
  `target_export_does_not_mark_spoofed_aggregate_feedback_substring_as_live_trade_usable`,
  `execution_feedback`, `workflow_factor_profitability_lifecycle`, and
  `structural_branch_admission`.
- `git diff --check` passed.

Objective recheck:

- Snapshot:
  `/tmp/ict-engine-closure-gap-source-audit-20260531T171900+0800/objective_snapshot_after_negated_feedback_window_fix/objective_closure_snapshot.json`
- Result: `status=not_complete`, `completion_proven=false`.
- Blockers: `done_definition_not_completion_ready`,
  `factor_closure_blocked`, `same_tree_practical_closure_unproven`, and
  `release_readiness_blocked`.
- Factor closure was blocked by a foreign Hurst exact-AQ runtime under
  `/tmp/ict-engine-hurst-efficiency-density-repair-exact-aq-20260531T172807+0800`.

Current practical flags remain `promotion_allowed=false`,
`trade_usable=false`, `update_goal=false`, and
`same_tree_practical_closure=null`.

## 2026-05-31T13:25+0800 Marker-Spoof Repair

Fresh compact claim audit before this source-only repair reported `status=pass`,
`active_claims=0`, `live_factor_processes=0`, `promotion_allowed_true=0`,
`trade_usable_true=0`, and `same_tree_practical_closure=null`. A separate
objective snapshot process completed with `status=not_complete`, blockers
`done_definition_not_completion_ready`,
`same_tree_practical_closure_unproven`, and `release_readiness_blocked`.

Repair applied:

- `support/scripts/research/same_tree_practical_closure.py` now checks accepted
  execution-feedback markers as exact source tokens.
- `support/scripts/research/real_trade_feedback_labels.py` uses the same exact
  token rule when accepting IBKR paper/broker feedback captures.
- `src/application/entry_models/training_export.rs` and
  `src/application/orchestration/structural_playbook.rs` use token matching for
  policy-training and structural target accepted-feedback gates.
- `support/scripts/research/tests/test_real_trade_feedback_labels.py` now has a
  spoofed `not_paper_execution_feedback` regression under accepted-feedback
  conversion.

Verification so far:

- `python3 -m unittest support.scripts.research.tests.test_same_tree_practical_closure -v`
  passed: `23` tests.
- `python3 -m unittest support.scripts.research.tests.test_real_trade_feedback_labels -v`
  passed: `12` tests.
- Rust filtered tests passed under isolated
  `CARGO_TARGET_DIR=/tmp/ict-engine-cargo-target-feedback-marker-20260531`:
  `policy_training_status_rejects_spoofed_execution_feedback_substring`,
  `policy_training_status_requires_accepted_execution_feedback_source_for_live_trade_usable`,
  `target_export_does_not_mark_spoofed_aggregate_feedback_substring_as_live_trade_usable`,
  and `target_export_marks_aggregate_paper_execution_feedback_as_live_trade_usable`.
- `rustfmt --edition 2021 --check` passed for
  `src/application/entry_models/training_export.rs` and
  `src/application/orchestration/structural_playbook.rs`.
- `python3 -m py_compile` passed for the touched Python scripts/tests.
- `git diff --check` passed for the current repair slice.
- Fresh compact claim audit after the repair reported `status=pass`,
  `active_claims=0`, `live_factor_processes=0`,
  `promotion_allowed_true=0`, `trade_usable_true=0`, and
  `same_tree_practical_closure=null`.
- Lightweight objective snapshot after the repair was written to
  `/tmp/ict-engine-objective-closure-after-feedback-marker-spoof-fix-20260531T1326-codex/objective_closure_snapshot.json`
  and remained `status=not_complete`, `completion_proven=false`. It reported
  `promotion_allowed_true=0`, `trade_usable_true=0`,
  `same_tree_practical_closure=null`, and missing practical chain stages
  `provider_data`, `pre_bayes`, `bbn_workflow`, `path_ranker`,
  `execution_tree`, `feedback_update`, and `policy_training`.
- The same snapshot saw a new foreign live factor process, PID `32378`, under
  `ict-engine-rsrs-high-low-regression-trend-admission-local-screen-20260531T131755+0800`,
  so runtime launch remains blocked until a later same-turn compact audit and
  focused process scan clear.

Current practical flags remain false; this repair closes a proof-spoof loophole
but does not create an accepted execution-feedback row or same-tree practical
closure packet.

## 2026-05-31T15:16+0800 Balanced Feedback Admission

Fresh source-only continuation kept the same route
`sd/ict-engi-fact-rese-muta`. A foreign live source screen was already present
under `/tmp/ict-engine-dynamic-bb-width-breakout-source-screen-20260531T144752+0800`,
so this slice did not launch provider, IBKR, Auto-Quant, TOMAC, paper, or live
runtime work.

Repair applied:

- Split feedback-collection admission from full paper/live promotion in
  `src/application/factor_lifecycle/profitability_admission.rs`.
- Added `PAPER_FEEDBACK_COLLECTION_MIN_ROWS=12`. Feedback collection may pass
  with 12/12/12 mature raw-scored, production, and observation rows when
  learning admission and the quality gates are clean.
- Kept `PAPER_VALIDATION_MIN_ROWS=30` for full paper/live promotion. Below the
  full floor, live blockers include `paper_not_ready_for_live`, and practical
  flags stay false.
- Tightened canonical ETH/full-session proof in
  `support/scripts/research/same_tree_practical_closure.py`: nonempty prose is
  no longer enough. The retained-session coverage packet must include status,
  non-RTH row presence, positive row count, exchange-local RTH window, timezone,
  and structured evidence.

Verification:

- `python3 -m unittest support.scripts.research.tests.test_same_tree_practical_closure -v`
  passed: `25` tests.
- `python3 -m unittest support.scripts.tests.test_factor_claim_terminalization_audit -v`
  passed: `127` tests.
- `python3 -m py_compile support/scripts/research/same_tree_practical_closure.py support/scripts/research/tests/test_same_tree_practical_closure.py support/scripts/tests/test_factor_claim_terminalization_audit.py`
  passed.
- `rustfmt --edition 2021 --check src/application/factor_lifecycle/profitability_admission.rs`
  passed.
- `cargo test profitability_admission::tests -- --nocapture` passed: `14`
  tests.
- `cargo test workflow_factor_profitability_lifecycle -- --nocapture` passed:
  `9` tests.

Current practical flags remain:

- `promotion_allowed=false`
- `trade_usable=false`
- `update_goal=false`
- `same_tree_practical_closure=null`

This raises throughput into the learning/feedback flywheel while preserving the
final practical gate. It does not prove the full objective complete.

Post-terminalization readback:

- Compact claim audit reported `status=pass`, `active_claims=0`,
  `live_factor_processes=0`, `promotion_allowed_true=0`,
  `trade_usable_true=0`, and `same_tree_practical_closure=null`.
- Objective closure snapshot under
  `/tmp/ict-engine-goal-source-loophole-audit-20260531T145700+0800/objective_snapshot_after_threshold_session_fix/`
  returned nonzero with `status=not_complete` and
  `completion_proven=false`. Remaining blockers include skipped heavy
  done-definition gates, missing same-tree practical closure, and release
  readiness blocked by the dirty worktree.

## 2026-05-31T13:38+0800 Marker-Spoof And Claim-Audit Recheck

Current-turn verification after adopting the marker-spoof and live-process
instance-count repairs:

- `python3 -m unittest support.scripts.research.tests.test_same_tree_practical_closure support.scripts.research.tests.test_real_trade_feedback_labels support.scripts.tests.test_factor_claim_terminalization_audit -v`
  passed: `162 tests`, `OK`.
- `rustfmt --edition 2021 --check src/application/entry_models/training_export.rs src/application/orchestration/structural_playbook.rs`
  passed after formatting the touched Rust files.
- `cargo test -q --lib policy_training_status_rejects_spoofed_execution_feedback_substring -- --nocapture`
  passed: `1 passed`.
- `cargo test -q --lib target_export_marks_aggregate_paper_execution_feedback_as_live_trade_usable -- --nocapture`
  passed: `1 passed`.
- `cargo test -q --lib target_export_does_not_mark_simulated_aggregate_feedback_as_live_trade_usable -- --nocapture`
  passed: `1 passed`.
- `cargo test -q --lib target_export_does_not_mark_spoofed_aggregate_feedback_substring_as_live_trade_usable -- --nocapture`
  passed: `1 passed`.
- `git diff --check` passed for the current marker-spoof and claim-audit repair
  files.

Fresh compact claim audit at `2026-05-31T13:38+0800` reports no active claims,
one RSRS high/low regression local-screen live runtime, `status=needs_attention`,
`promotion_allowed_true=0`, `trade_usable_true=0`, and
`same_tree_practical_closure=null`.

Decision:

- Commit the verified source-only gate repair separately from unrelated dirty
  factor scripts and runtime artifacts.
- Keep the full objective active. This closes a spoof/readback loophole and
  improves runtime occupancy visibility, but it does not prove practical
  closure.

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

## 2026-05-31T12:45+0800 Accepted-Feedback And Prior-Readback Gate Repair

Fresh routing was repeated before this slice. Current route remains
`sd/ict-engi-fact-rese-muta`; installed runtime skill
`~/.hermes/skills/software-development/ict-engi-fact-rese-muta/SKILL.md` was
used.

Current-state guard:

- `python3 support/scripts/factor_claim_terminalization_audit.py --compact`
  at `2026-05-31T12:36+0800` reported `status=needs_attention`,
  `live_factor_processes=0`, `promotion_allowed_true=0`,
  `trade_usable_true=0`, and `same_tree_practical_closure=null`.
- The only attention claim was a fresh Ehlers exact-AQ claim:
  `/tmp/ict-engine-agent-claims/board-b-factor-refinement/20260531T122333+0800-codex-ehlers-autocorr-periodogram-cycle-regime-30m-exact-aq.claim`.
- Focused `ps` still showed unrelated heavy `done_definition_audit.py` /
  `smoke_acceptance.sh` activity. This slice did not launch provider, IBKR,
  AQ, TOMAC, paper/live, or downstream lifecycle work.

Repairs verified in current tree:

- Accepted execution-feedback conversion now rejects a source such as
  `simulated_backtest:paper_execution_feedback:*`; accepted feedback requires
  an accepted paper/live/broker source marker plus broker fill and realized
  evidence.
- IBKR execution readback now records filtered-row diagnostics so rows removed
  for missing commission reports remain visible as diagnostics, not accepted
  broker feedback.
- TOMAC index-futures prior-AQ readback now fails closed for practical flags:
  legacy/prior gate practical claims are recorded only as prior-readback
  diagnostics, while the current no-launch summary keeps `promotion_allowed`,
  `trade_usable`, and `update_goal` false.

Verification:

- `python3 -m unittest support.scripts.research.tests.test_real_trade_feedback_labels -v`
  passed: `12 tests`, `OK`.
- `python3 -m unittest support.scripts.research.tests.test_ibkr_execution_readback -v`
  passed: `4 tests`, `OK`.
- `python3 support/scripts/research/downstream_practical_admission_source_check.py --tracked-run-wrappers --jobs 4 --pretty`
  passed: all tracked wrapper entries `ok=true`, `violations=[]`.
- `python3 -m unittest support.docs.experiments.actionable-regime-confidence.scripts.test_tomac_index_futures_clean_aq -v`
  passed: `321 tests`, `OK`.
- `git diff --check -- support/scripts/research/real_trade_feedback_labels.py support/scripts/research/tests/test_real_trade_feedback_labels.py support/scripts/research/ibkr_execution_readback.py support/scripts/research/tests/test_ibkr_execution_readback.py support/docs/experiments/actionable-regime-confidence/scripts/run_tomac_index_futures_clean_aq_v1.py support/docs/experiments/actionable-regime-confidence/scripts/test_tomac_index_futures_clean_aq.py`
  produced no whitespace errors.

Decision:

- This is a quality-preserving gate repair, not a practical promotion.
- The flywheel can admit more candidates into learning/calibration, but final
  practical closure still requires same-tree closure, accepted paper/live/broker
  execution feedback, verified real cost, and ETH/full-retained session
  evidence.
- Current practical flags remain false:
  `promotion_allowed=false`, `trade_usable=false`, `update_goal=false`,
  `same_tree_practical_closure=null`.

## 2026-05-31T13:29+0800 Practical-Admission Untracked Debt Gate Repair

User framing: balance throughput and quality. Current answer is still a
two-stage gate, not a final-gate relaxation:

- flywheel learning / calibration may use a lower admission floor and collect
  more evidence;
- final `promotion_allowed`, `trade_usable`, and `update_goal` still require
  same-tree practical closure, accepted paper/live/broker execution feedback,
  verified real cost, and ETH/full-retained session evidence.

Repair made in this slice:

- `support/scripts/done_definition_audit.py` now runs the practical-admission
  scanner across tracked run wrappers, tracked helper reports, and active
  untracked `run_*.py` wrappers.
- untracked practical-admission violations can no longer silently pass just
  because tracked violations are zero; they must either be zero or match
  `support/docs/audits/practical-admission-source-debt-quarantine.json`.
- matching untracked quarantine remains debt-only evidence. It does not make
  any untracked wrapper release-ready, promotion-ready, or trade-usable.

Verification:

- RED:
  `python3 -m unittest support.scripts.tests.test_done_definition_audit.DoneDefinitionAuditTest.test_practical_admission_source_gate_scans_untracked_wrappers_via_files_from support.scripts.tests.test_done_definition_audit.DoneDefinitionAuditTest.test_practical_admission_source_gate_fails_on_unquarantined_untracked_violations -v`
  failed as expected before implementation.
- GREEN focused:
  `python3 -m unittest support.scripts.tests.test_done_definition_audit.DoneDefinitionAuditTest.test_practical_admission_source_gate_scans_untracked_wrappers_via_files_from support.scripts.tests.test_done_definition_audit.DoneDefinitionAuditTest.test_practical_admission_source_gate_fails_on_unquarantined_untracked_violations support.scripts.tests.test_done_definition_audit.DoneDefinitionAuditTest.test_practical_admission_source_gate_passes_with_quarantined_untracked_violations -v`
  passed.
- Full focused suite:
  `python3 -m unittest support.scripts.tests.test_done_definition_audit -v`
  passed: `39 tests`, `OK`.
- Direct done-definition:
  `python3 support/scripts/done_definition_audit.py --compact --output /tmp/ict-engine-closed-loop-certainty-audit-20260531T110523+0800/done_definition_audit_current_head_post_snapshot.json`
  passed with `status=pass`, `completion_ready=false`, `pass_count=7`,
  `skip_count=4`, tracked practical-admission violations `0`, untracked
  practical-admission violations `461` across `222` files, and quarantine
  `matched=true`.
- `git diff --check -- support/scripts/done_definition_audit.py support/scripts/tests/test_done_definition_audit.py`
  passed with no whitespace errors.

Closure recheck:

- `python3 support/scripts/objective_closure_snapshot.py --compact --output-dir /tmp/ict-engine-closed-loop-certainty-audit-20260531T110523+0800/snapshot_after_practical_untracked_fix_retry --timeout-seconds 360`
  still returned `not_complete`. During that run the current head and
  quarantine fingerprint changed under concurrent work, and the child
  fixed-bps scan also timed out once. A later direct done-definition run passed,
  so this is recorded as concurrent-state verification noise, not as practical
  completion.
- Fresh compact claim audit at `2026-05-31T13:29+0800` reports
  `status=needs_attention`, one active VHF/CHOP live runtime root
  `/tmp/ict-engine-vhf-chop-trend-reacceleration-exact-aqprep-20260531T132517+0800`,
  `promotion_allowed_true=0`, `trade_usable_true=0`, and
  `same_tree_practical_closure=null`.

Decision:

- Do not lower the three final practical tickets.
- Do not launch provider/AQ/IBKR/paper/live from this slice while the VHF/CHOP
  owner is live.
- This slice improves the quality side of the flywheel by ensuring broader
  candidate throughput cannot hide current untracked practical-admission debt.

Commit:

- `48930e7c Require quarantined untracked practical admission debt`

## 2026-05-31T13:03+0800 Flywheel-Vs-Practical Resolver Gate Split

Fresh routing was repeated before this slice. Current route remains
`sd/ict-engi-fact-rese-muta`; installed runtime skill
`~/.hermes/skills/software-development/ict-engi-fact-rese-muta/SKILL.md` was
used.

Current-state guard:

- `python3 support/scripts/factor_claim_terminalization_audit.py --compact`
  at `2026-05-31T13:00+0800` reported `status=needs_attention` because a
  foreign TOMAC/AQ runtime was live under
  `/tmp/ict-engine-tomac-tsmom-vol-scaled-low-turnover-aq-20260531T115002+0800`.
  This slice did not launch provider, IBKR, AQ, TOMAC, paper/live, downstream,
  or local backtest work.
- Objective closure artifact
  `/tmp/ict-engine-objective-closure-20260531T125432/objective_closure_snapshot.json`
  still reported `completion_proven=false` with
  `same_tree_practical_closure_unproven`; all seven practical chain stages were
  missing from validated closure evidence.

Repair:

- `support/scripts/research/factor_candidate_resolver.py` now exposes
  `flywheel_learning_ready` and `flywheel_learning_ready_count` so lower-floor
  learning/flywheel candidates are visible as productive training input.
- The same resolver no longer treats `live_trade.promotion_allowed=true` /
  `live_trade.trade_usable=true` as sufficient by itself. Promotion/trade-use
  counting now also requires a validated `same_tree_practical_closure` packet
  with `status=pass`, true practical flags, and
  `evidence_packet_validated=true`.

Verification:

- `python3 -m unittest support.scripts.research.tests.test_factor_candidate_resolver -v`
  passed: `22 tests`, `OK`.
- `python3 -m unittest support.scripts.research.tests.test_factor_candidate_pack -v`
  passed: `18 tests`, `OK`.
- `python3 support/scripts/research/downstream_practical_admission_source_check.py --tracked-run-wrappers --jobs 4 --pretty`
  passed: all tracked wrapper entries `ok=true`, `violations=[]`.
- `git diff --check -- support/scripts/research/factor_candidate_resolver.py support/scripts/research/tests/test_factor_candidate_resolver.py`
  produced no whitespace errors.
- A follow-up `python3 support/scripts/factor_claim_terminalization_audit.py --compact`
  at `2026-05-31T13:07+0800` reported `status=pass`,
  `promotion_allowed_true=0`, `trade_usable_true=0`,
  `same_tree_practical_closure=null`, and the code-only coordination claim did
  not block closure.

Decision:

- Yes, balance belongs in the learning/flywheel plane, not by weakening the
  three final practical tickets.
- This slice improves throughput visibility while preserving final quality
  gates. It produces no `trade_usable=true` factor and no practical promotion.

## 2026-05-31T14:16+0800 Closure Packet Validator Compatibility

Finding:

- The canonical same-tree practical-closure Python builder was stricter than
  ordinary wrapper metrics but still incompatible with downstream validators:
  it generated `status=pass` packets without `evidence_packet_validated=true`,
  while Rust workflow/analyze readback and objective-closure code require that
  field before accepting a packet as practical closure.

Repair:

- `support/scripts/research/same_tree_practical_closure.py` now writes
  `evidence_packet_validated=true` in canonical pass packets.
- `support/scripts/research/tests/test_same_tree_practical_closure.py` asserts
  the field.
- `support/docs/audits/practical-admission-source-debt-quarantine.json` was
  refreshed to the reviewed current untracked practical-admission debt
  fingerprint: `463` violations across `223` untracked wrapper files, tracked
  practical-admission violations still `0`.

Verification:

- `python3 -m unittest support.scripts.research.tests.test_same_tree_practical_closure -v`
  passed: `24 tests`, `OK`.
- `python3 -m unittest support.scripts.tests.test_factor_claim_terminalization_audit -v`
  passed: `127 tests`, `OK`.
- `python3 -m py_compile support/scripts/research/same_tree_practical_closure.py support/scripts/research/tests/test_same_tree_practical_closure.py`
  passed.
- Rust filters under `/tmp/ict-engine-cargo-target-closure-packet-20260531`
  passed:
  `same_root_admission_practical_closure_accepts_structured_packet`,
  `structural_branch_admission_accepts_validated_same_tree_closure_packet`,
  and `workflow_factor_profitability_lifecycle_exposes_paper_feedback_collection_stage`.
- `python3 support/scripts/done_definition_audit.py --compact --practical-admission-source-timeout-seconds 300 --output /tmp/ict-engine-closed-loop-certainty-audit-20260531T1400-done-definition-after-quarantine-refresh.json`
  passed with `fail_count=0`, `skip_count=4`,
  `practical_admission_source_surface=pass`, `tracked_violation_count=0`, and
  `quarantine_matched=true`; `completion_ready=false` because heavy gates were
  not run.

Decision:

- This is a closed-loop proof compatibility fix, not gate lowering.
- Final practical tickets remain required: validated same-root closure,
  accepted paper/live/broker execution feedback, and verified real
  cost/session evidence.
- Current practical flags remain `promotion_allowed=false`,
  `trade_usable=false`, `update_goal=false`, and
  `same_tree_practical_closure=null`.

## 2026-05-31T14:49+0800 Legacy Alias Rejection

Finding:

- A second compatibility loophole remained after the Python packet-builder fix:
  Rust workflow/analyze validators accepted legacy `evidence_validated=true`
  when canonical `evidence_packet_validated=true` was absent.
- This could let a stale alias masquerade as final same-tree practical closure.

Repair:

- Removed the legacy alias fallback from
  `src/application/orchestration/workflow_status.rs` and
  `src/analyze_shared.rs`.
- Added producer/consumer regression coverage:
  `workflow_factor_profitability_lifecycle_rejects_legacy_evidence_validated_alias`
  and
  `same_root_admission_practical_closure_rejects_legacy_evidence_validated_alias`.

Verification:

- RED then GREEN:
  `cargo test evidence_validated_alias -- --nocapture`.
- Positive structured packet tests still pass:
  `cargo test same_root_admission_practical_closure_accepts_structured_packet -- --nocapture`
  and
  `cargo test workflow_factor_profitability_lifecycle_marks_deploy_ready_without_funded_live_fill -- --nocapture`.
- Broader focused filters pass:
  `cargo test workflow_factor_profitability_lifecycle -- --nocapture` and
  `cargo test same_root_admission_practical_closure -- --nocapture`.
- `rustfmt --edition 2021 --check
  src/application/orchestration/workflow_status.rs src/analyze_shared.rs`
  passed.
- The post-fix objective snapshot at
  `/tmp/ict-engine-closed-loop-loophole-audit-20260531T143419+0800/objective_snapshot_after_legacy_alias_fix/objective_closure_snapshot.json`
  still reports `status=not_complete`, `completion_proven=false`,
  `promotion_allowed_true=0`, `trade_usable_true=0`, and
  `same_tree_practical_closure=null`.

Decision:

- Keep the final practical tickets strict.
- The flywheel balance point remains the intermediate feedback-collection
  plane, not legacy marker acceptance or final gate relaxation.

## 2026-05-31T15:29+0800 Feedback-Collection Quality Guard

Fresh compact claim audit before this source-only repair reported `status=pass`
with no live factor process and no active claims. The shared worktree remained
dirty, so this slice preserved unrelated changes and did not launch provider,
IBKR, Auto-Quant, TOMAC, paper, or live runtime work.

Finding:

- The workflow lifecycle readback honored
  `paper_feedback_collection_ready=true` without checking that learning and
  paper admission were actually ready.
- That could move weak candidates into the feedback flywheel readback, weakening
  the "easy but quality acceptable" threshold split.

Repair and verification:

- Added a failing regression test for `not_evaluated` learning/paper status plus
  `paper_feedback_collection_ready=true`.
- Patched the workflow consumer so feedback collection readiness now requires
  `learning_admission_status=admitted` and `paper_admission_status=ready`.
- `cargo test workflow_factor_profitability_lifecycle_rejects_paper_feedback_collection_flag_without_learning_and_paper -- --nocapture`
  failed before the fix and passed after it.
- `cargo test workflow_factor_profitability_lifecycle -- --nocapture` passed
  `10` tests after the fix.

Current practical flags remain:

- `promotion_allowed=false`
- `trade_usable=false`
- `update_goal=false`
- `same_tree_practical_closure=null`
