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
| L3 | Training direction may overfit to zero-cost or fixed-bps AQ stress instead of verified instrument costs. | Fixed-bps source scan now separates tracked/current authority from active untracked experiment debt. Current tracked authority has zero fixed-bps cost-model violations; untracked debt is quarantined and remains non-promotional. | Keep final practical promotion tied to verified `cost_model`/instrument-cost packets; do not let quarantined untracked fixed-bps wrappers count as cost proof. | fixed for current authority; untracked debt quarantined |
| L4 | ETH/full retained session scope may be missing from factor workdocs or terminal packets. | Pending source/doc audit. | Require session-scope evidence or keep promotion false. | open |
| L5 | Closed-loop proof may omit accepted execution feedback while still reporting deploy/live readiness. | `policy_training_status_` tests require accepted paper/live/broker execution-feedback markers for live/trade-usable rows; simulated/backtest markers remain blocked. | Split `paper_feedback_collection_ready` from final live/trade usability; accepted execution feedback remains required for final promotion. | fixed in focused Rust surfaces |
| L6 | Done-definition may miss Python helper/report surfaces that can emit practical flags. | `done_definition_audit.py --compact` now covers practical-admission source, await-launch source, and fixed-bps cost-model source surfaces without timing out in the no-heavy path. | Keep scanner coverage in done-definition and objective-closure snapshot readbacks; tracked practical leakage remains fail-closed. | fixed for current no-heavy scanner coverage |
| L7 | Accepted execution-feedback source markers can be spoofed by substring labels such as `not_paper_execution_feedback`. | Current-tree focused test `test_rejects_spoofed_accepted_execution_feedback_substring` initially failed: `same_tree_practical_closure.py` built a pass packet from `audit:not_paper_execution_feedback:factor_v1`. The same substring pattern existed in `real_trade_feedback_labels.py`, `training_export.rs`, and `structural_playbook.rs`. | Require accepted paper/live/broker feedback markers to match source tokens exactly; keep simulated markers conservatively rejected. Add/keep spoof regression tests across same-tree closure, real-trade feedback conversion, policy-training status, and structural target export. | fixed and focused tests passed |
| L7 | Feedback/flywheel entry still treated real cost/session verification debt like final promotion debt, blocking otherwise clean candidates before they can collect feedback. | `paper_feedback_collection_ready` excluded accepted execution feedback but still used `retained_session_scope_verified` and `promotion_cost_verified` as feedback-collection blockers. | Move cost/session verification debt to final live blockers while keeping feedback collection gated by positive expectancy after declared friction, no leakage, mature validation rows, verified market-data provenance, execution readiness, Pre-Bayes, execution tree, and path-ranker evidence. | fixed and verified |
| L8 | Canonical same-tree practical-closure packets could pass Python metrics but fail Rust workflow validation because the packet did not write `evidence_packet_validated=true`. | `same_tree_practical_closure.py` built pass packets with an `evidence_packet` path but without the validation boolean required by `workflow_status.rs`, `analyze_shared.rs`, `objective_closure_snapshot.py`, and `factor_candidate_resolver.py`. | Add `evidence_packet_validated=true` to the canonical Python packet builder and assert it in `test_builds_pass_packet_from_full_practical_chain`; rerun Python and Rust closure-readback tests. | fixed and verified |
| L9 | The untracked practical-admission wrapper quarantine drifted, causing done-definition to fail even though tracked/current authority still had zero violations. | `done_definition_audit.py --compact --practical-admission-source-timeout-seconds 300` reported tracked violations `0`, but untracked debt drifted to `463` violations across `223` files with fingerprint `1bd52815cc90100bd42e84ecff2e0430e51723c79df24312f0c5fccba5f5c638`. | Refresh `support/docs/audits/practical-admission-source-debt-quarantine.json` to the reviewed current fingerprint while keeping the debt quarantined and explicitly non-promotional. This does not make the untracked wrappers release-ready, promotion-ready, or trade-usable. | fixed for audit classification; debt remains quarantined |

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
- 2026-05-31T12:44:19+08:00: no-launch source-debt split added. The fixed-bps
  cost-model scanner now reports tracked vs active-untracked violations. Current
  readback:
  `/tmp/ict-engine-factor-training-loop-audit-20260531T122038+0800/done_definition_audit.after_fixed_bps_quarantine.compact.json`
  returned `status=pass`, `pass_count=7`, `skip_count=4`,
  `practical_admission_source_surface.tracked_violation_count=0`,
  `fixed_bps_cost_model_source_surface.tracked_violation_count=0`, and matched
  quarantine for `1790` fixed-bps violations across `322` untracked experiment
  scripts. This lowers the false global blocker for quality candidates while
  preserving real-cost proof as a final promotion gate.
- 2026-05-31T12:48:29+08:00: compact claim audit passed with
  `active_claims=0`, `live_factor_processes=0`, `promotion_allowed_true=0`,
  `trade_usable_true=0`, and `same_tree_practical_closure=null`.
- 2026-05-31T12:52:43+08:00: objective snapshot readback staged the fixed-bps
  debt manifest as quarantined
  `quarantined_fixed_bps_cost_model_source_debt`, not an active source blocker.
  The snapshot still correctly remained `not_complete` because heavy
  done-definition gates were skipped, same-tree practical closure is absent,
  release readiness requires a clean slice, and a transient live-runtime readback
  was visible during the child factor audit.
- 2026-05-31T12:53:03+08:00: final standalone compact claim audit rechecked
  clean after the snapshot: `status=pass`, `active_claims=0`,
  `live_factor_processes=0`, `promotion_allowed_true=0`,
  `trade_usable_true=0`, and `same_tree_practical_closure=null`.
- 2026-05-31T12:56:47+08:00: post-commit compact claim audit saw a foreign live
  TOMAC wrapper under
  `/tmp/ict-engine-tomac-tsmom-vol-scaled-low-turnover-aq-20260531T115002+0800`,
  so runtime occupancy was `needs_attention` again. It still reported
  `active_claims=0`, `promotion_allowed_true=0`, `trade_usable_true=0`, and
  `same_tree_practical_closure=null`; this slice did not launch or promote a
  factor.
- 2026-05-31T13:25:20+08:00: found and repaired accepted-feedback marker
  spoofing. Before the fix,
  `python3 -m unittest support.scripts.research.tests.test_same_tree_practical_closure.SameTreePracticalClosureTests.test_rejects_spoofed_accepted_execution_feedback_substring -v`
  failed because `audit:not_paper_execution_feedback:factor_v1` still built a
  pass same-tree practical-closure packet. Python fixes now pass
  `test_same_tree_practical_closure` (`23` tests) and
  `test_real_trade_feedback_labels` (`12` tests). Rust marker spoof tests are
  passed under isolated cargo target
  `/tmp/ict-engine-cargo-target-feedback-marker-20260531`:
  `policy_training_status_rejects_spoofed_execution_feedback_substring`,
  `policy_training_status_requires_accepted_execution_feedback_source_for_live_trade_usable`,
  `target_export_does_not_mark_spoofed_aggregate_feedback_substring_as_live_trade_usable`,
  and `target_export_marks_aggregate_paper_execution_feedback_as_live_trade_usable`.
  `rustfmt --edition 2021 --check` passed for touched Rust files, Python
  `py_compile` passed for touched Python files, and `git diff --check` passed
  for the current repair slice.
- 2026-05-31T13:38:13+08:00: lightweight objective snapshot after the marker
  spoof repair stayed fail-closed:
  `/tmp/ict-engine-objective-closure-after-feedback-marker-spoof-fix-20260531T1326-codex/objective_closure_snapshot.json`
  returned `status=not_complete`, `completion_proven=false`,
  `promotion_allowed_true=0`, `trade_usable_true=0`, and
  `same_tree_practical_closure=null`. It also surfaced a new foreign live
  factor process, PID `32378`, under
  `ict-engine-rsrs-high-low-regression-trend-admission-local-screen-20260531T131755+0800`,
  so runtime launch remains blocked.

## Current Remaining Blockers

- Do not lower final `trade_usable=true`: the three tickets remain hard gates:
  same-root closed loop, accepted paper/live/broker execution feedback, and
  verified real cost/session evidence.
- The implemented balance point is the intermediate
  `paper_feedback_collection_ready` stage. This creates productive throughput
  into feedback collection without turning paper/sim/backtest evidence into
  practical usability.
- Broad fixed-bps debt still exists in untracked experiment scripts, but it is
  now classified as quarantined non-authority debt rather than a tracked
  current-path blocker. It cannot satisfy `promotion_allowed`, `trade_usable`,
  real-cost closure, or objective completion.
- Current post-commit compact claim audit has a foreign live runtime again, but
  no active claims and no practical flags. Launching or promoting a candidate
  still needs a fresh claim audit and the full evidence packet after runtime
  occupancy clears.

## 2026-05-31 13:02 +0800 Heavy Gate And Runtime Refresh

Additional verification after the source-gate repair:

- `/tmp/ict-engine-done-definition-heavy-20260531T-codex-closedloop-final.json`
  reports `completion_ready=true`, `status=pass`, `pass_count=11`,
  `skip_count=0`, and no unresolved done-definition gates.
- In that proof, `practical_admission_source_surface=pass` with
  `tracked_violation_count=0`; `fixed_bps_cost_model_source_surface=pass` with
  `tracked_violation_count=0` and matched quarantine for `1790` untracked
  fixed-bps violations across `322` untracked experiment scripts.
- Manual smoke acceptance also passed with
  `STATE_DIR=/tmp/ict-engine-smoke-acceptance-codex-20260531T1241` and
  `OUT_DIR=/tmp/ict-engine-smoke-acceptance-codex-20260531T1241-out`.
- The OTE calendar-guard exact-AQ packet at
  `/tmp/ict-engine-tomac-eth-trend-ote-reacceleration-calendar-guard-exact-aqlaunch-20260531T125313+0800`
  remained fail-closed: `decision=exact_aq_terminal_readback_practical_lifecycle_incomplete`,
  `promotion_allowed=false`, `trade_usable=false`, `update_goal=false`, and
  `same_tree_practical_closure=null`.
- Fresh compact claim audit at 2026-05-31 13:02 +0800 reports
  `status=needs_attention`, `live_factor_processes=1`, `active_claims=0`,
  `promotion_allowed_true=0`, `trade_usable_true=0`, and
  `same_tree_practical_closure=null`. The live root is the foreign TSMOM 5m AQ
  continuation under
  `/tmp/ict-engine-tomac-tsmom-vol-scaled-low-turnover-aq-20260531T115002+0800`.

This closes the current source-scan loophole slice, not the whole objective.
Final practical closure is still missing accepted paper/live/broker feedback and
a validated same-tree practical closure packet.

## 2026-05-31 15:16 +0800 Feedback Floor And ETH Evidence Tightening

Follow-up to the operator request that good candidates should pass into the
flywheel more easily without degrading factor quality:

- `paper_feedback_collection_ready` now has its own explicit row floor:
  `PAPER_FEEDBACK_COLLECTION_MIN_ROWS=12` for raw-scored mature, production,
  and observation validation rows.
- Full paper/live promotion still uses `PAPER_VALIDATION_MIN_ROWS=30`. A
  candidate under 30/30/30 can collect feedback only; live blockers include
  `paper_not_ready_for_live`, and `deploy_ready`, `promotion_allowed`,
  `trade_usable`, and `update_goal` remain false.
- Canonical same-tree practical closure now requires structured
  retained-session proof: pass status, non-RTH rows, positive row count, RTH
  window, timezone, and structured evidence reference/object. A prose-only
  assertion of non-RTH coverage is rejected.
- Verification passed:
  `python3 -m unittest support.scripts.research.tests.test_same_tree_practical_closure -v`
  (`25` tests),
  `python3 -m unittest support.scripts.tests.test_factor_claim_terminalization_audit -v`
  (`127` tests), `py_compile` for the touched Python files,
  `rustfmt --edition 2021 --check
  src/application/factor_lifecycle/profitability_admission.rs`,
  `cargo test profitability_admission::tests -- --nocapture` (`14` tests), and
  `cargo test workflow_factor_profitability_lifecycle -- --nocapture`
  (`9` tests).

Current practical flags remain false. This slice improves throughput into
feedback collection and tightens ETH/session proof; it does not create accepted
paper/live/broker feedback or a same-tree practical closure packet.

Post-terminalization readback:

- `python3 support/scripts/factor_claim_terminalization_audit.py --compact`
  reported `status=pass`, `active_claims=0`, `live_factor_processes=0`,
  `promotion_allowed_true=0`, `trade_usable_true=0`, and
  `same_tree_practical_closure=null`.
- `python3 support/scripts/objective_closure_snapshot.py --compact ...`
  wrote
  `/tmp/ict-engine-goal-source-loophole-audit-20260531T145700+0800/objective_snapshot_after_threshold_session_fix/objective_closure_snapshot.json`
  and returned nonzero because the objective remains `not_complete`.
  The snapshot kept `completion_proven=false`, with blockers including
  `same_tree_practical_closure_unproven` and `release_readiness_blocked`.

## 2026-05-31 13:11 +0800 Feedback Collection Threshold Split

No-launch gate adjustment for the operator request to let quality candidates
enter the flywheel before all three final tickets exist:

- `paper_feedback_collection_ready` no longer treats
  `retained_session_scope_verified=false` or `promotion_cost_verified=false` as
  feedback-collection blockers by themselves.
- Those debts remain final live blockers, and `deploy_ready`,
  `promotion_allowed`, `trade_usable`, and `update_goal` still require verified
  retained session scope, verified promotion cost, accepted execution feedback,
  strict live regime confidence, and the validated same-tree closure chain.
- Quality stays enforced before feedback collection: learning/paper admission,
  positive expectancy after declared friction, leakage pass, mature validation
  rows, verified market-data provenance, execution readiness, Pre-Bayes,
  execution-tree, and path-ranker evidence.
- Focused Rust verification passed under
  `/tmp/ict-engine-cargo-target-gate-threshold-20260531T1308`:
  `cargo test profitability_admission::tests -- --nocapture` (13 passed),
  `cargo test structural_branch_admission -- --nocapture` (7 passed), and
  `cargo test workflow_factor_profitability_lifecycle -- --nocapture`
  (8 passed).
- `rustfmt --edition 2021 --check
  src/application/factor_lifecycle/profitability_admission.rs` passed.
- `git diff --check` passed.
- Compact claim audit after terminalizing this no-promotion claim reports
  `status=pass`, `active_claims=0`, `live_factor_processes=0`,
  `promotion_allowed_true=0`, `trade_usable_true=0`, and
  `same_tree_practical_closure=null`; this slice did not launch or promote a
  factor.
- A later re-audit at 2026-05-31 13:26 +0800 saw new foreign active lanes
  (`MedRV/MinRV 30m` claim and `VHF/CHOP` exact-AQ prep live runtime), so the
  shared runtime returned to `status=needs_attention`. It still reported
  `promotion_allowed_true=0`, `trade_usable_true=0`, and
  `same_tree_practical_closure=null`.
- A fresh compact claim audit at 2026-05-31 13:38 +0800 reports no active
  claims but one RSRS high/low regression local-screen live runtime, so the
  shared runtime is still `status=needs_attention`. It still reports
  `promotion_allowed_true=0`, `trade_usable_true=0`, and
  `same_tree_practical_closure=null`.

## 2026-05-31 14:16 +0800 Closure Packet And Quarantine Refresh

- Canonical same-tree practical-closure packet compatibility was repaired.
  `support/scripts/research/same_tree_practical_closure.py` now writes
  `evidence_packet_validated=true` in pass packets, matching the Rust and
  objective-snapshot validators.
- Verification passed:
  `python3 -m unittest support.scripts.research.tests.test_same_tree_practical_closure -v`
  (`24` tests),
  `python3 -m unittest support.scripts.tests.test_factor_claim_terminalization_audit -v`
  (`127` tests), `py_compile` for the touched Python files, and Rust filters
  `same_root_admission_practical_closure_accepts_structured_packet`,
  `structural_branch_admission_accepts_validated_same_tree_closure_packet`, and
  `workflow_factor_profitability_lifecycle_exposes_paper_feedback_collection_stage`
  under `/tmp/ict-engine-cargo-target-closure-packet-20260531`.
- Done-definition source debt was rechecked after the closure-packet repair.
  The first compact rerun failed only because the untracked practical-admission
  quarantine fingerprint drifted. Tracked/current practical-admission
  violations remained `0`.
- Reviewed current untracked practical-admission debt is `463` violations across
  `223` files:
  `practical_flag_without_extension_complete_guard=120`,
  `branch_local_admission_uses_transition_hard_gate=105`,
  `downstream_admission_uses_fixed_bps_survivor_gate=79`,
  `five_bps_survival_uses_trade_density_floor=79`,
  `retired_field_used_as_practical_gate_template=78`,
  `extension_complete_without_validated_practical_closure_source=2`.
- After refreshing
  `support/docs/audits/practical-admission-source-debt-quarantine.json`,
  compact done-definition passed with `fail_count=0`, `skip_count=4`,
  `practical_admission_source_surface=pass`, `quarantine_matched=true`, and
  `completion_ready=false` because heavy gates were not run.
- This did not promote any factor. `promotion_allowed=false`,
  `trade_usable=false`, `update_goal=false`, and
  `same_tree_practical_closure=null` remain the current practical status.

## 2026-05-31 14:49 +0800 Legacy Evidence Alias Fail-Closed Repair

Finding:

- Rust practical-closure validators still accepted the legacy
  `evidence_validated=true` alias when canonical
  `evidence_packet_validated=true` was absent.
- That was a fail-open compatibility loophole: a marker using the old alias
  could satisfy final lifecycle/admission validation even though the current
  source-of-truth field was missing.

Repair:

- `src/application/orchestration/workflow_status.rs` now requires
  `evidence_packet_validated=true` in
  `same_tree_practical_closure_packet_validated`.
- `src/analyze_shared.rs` now requires `evidence_packet_validated=true` in
  `same_root_admission_practical_closure_validated`.
- Added regression tests on both surfaces that remove
  `evidence_packet_validated`, set legacy `evidence_validated=true`, and assert
  that final live/trade readiness remains blocked.

Verification:

- RED: `cargo test evidence_validated_alias -- --nocapture` first failed in
  `workflow_factor_profitability_lifecycle_rejects_legacy_evidence_validated_alias`
  because old code returned `live_trade_status=ready`.
- GREEN: `cargo test evidence_validated_alias -- --nocapture` passed.
- Positive acceptance still passes:
  `cargo test same_root_admission_practical_closure_accepts_structured_packet -- --nocapture`
  and
  `cargo test workflow_factor_profitability_lifecycle_marks_deploy_ready_without_funded_live_fill -- --nocapture`.
- Broader focused filters passed:
  `cargo test workflow_factor_profitability_lifecycle -- --nocapture` (`9`
  tests) and `cargo test same_root_admission_practical_closure -- --nocapture`
  (`3` tests).
- `rustfmt --edition 2021 --check
  src/application/orchestration/workflow_status.rs src/analyze_shared.rs`
  passed.
- Objective snapshot after the fix:
  `/tmp/ict-engine-closed-loop-loophole-audit-20260531T143419+0800/objective_snapshot_after_legacy_alias_fix/objective_closure_snapshot.json`
  remained `status=not_complete`, `completion_proven=false`,
  `promotion_allowed_true=0`, `trade_usable_true=0`, and
  `same_tree_practical_closure=null`.

Decision:

- This is not a threshold-lowering change. It closes an old compatibility path
  that could fake a final practical proof.
- The balance remains: lower-friction learning/paper feedback collection may
  feed the flywheel, but final `promotion_allowed`, `trade_usable`, and
  `update_goal` still require canonical same-tree closure, accepted
  paper/live/broker feedback, verified real cost, and ETH/full retained session
  proof.

## 2026-05-31T15:29+0800 Feedback-Collection Flag Consumer Guard

Finding:

- The workflow lifecycle consumer treated a naked
  `paper_feedback_collection_ready=true` flag as sufficient for feedback
  collection readiness.
- A producer could therefore bypass the learning/paper admission planes in the
  readback while still staying below live promotion.

Repair:

- `closed_loop_admission_paper_feedback_collection_ready` now requires the
  admission object to have both `learning_admission_status=admitted` and
  `paper_admission_status=ready` before it honors explicit
  `paper_feedback_collection_ready=true`.
- Later revalidation removed the legacy `ready && actionable` consumer fallback;
  feedback collection readiness must now be explicit.
- Added regression coverage in
  `workflow_factor_profitability_lifecycle_rejects_paper_feedback_collection_flag_without_learning_and_paper`.

Verification:

- RED before fix:
  `cargo test workflow_factor_profitability_lifecycle_rejects_paper_feedback_collection_flag_without_learning_and_paper -- --nocapture`
  failed because lifecycle readback returned `paper_feedback_collection_ready=true`.
- GREEN after fix: the same command passed.
- `cargo test workflow_factor_profitability_lifecycle -- --nocapture` passed
  `10` tests.

Decision:

- This preserves the intended balance: feedback collection is easier than final
  trade usability, but still requires the learning/paper quality planes.
- It does not create `promotion_allowed=true`, `trade_usable=true`, or
  `update_goal=true`.

## 2026-05-31T16:09+0800 Feedback-Collection Row-Floor Revalidation

Finding:

- The previous consumer guard still left two quality leaks:
  `workflow_factor_profitability_lifecycle_value` could infer feedback
  collection readiness from legacy `ready=true` / `actionable=true`, and
  `structural_closed_loop_branch_admission_value` could produce
  `paper_feedback_collection_ready=true` from ranker runtime plus matured
  confirmation text without proving the 12/12/12 feedback-collection row floor.

Repair:

- Removed the legacy `ready && actionable` fallback from
  `closed_loop_admission_paper_feedback_collection_ready`.
- Added structural validation-row parsing for candidate, lifecycle, policy
  summary, bundle, and lineage-style counters.
- Structural branch admission now emits
  `paper_feedback_collection_ready=true` only when raw-scored mature,
  production validation, and observation validation are each at least `12`.
- The admission readback now includes
  `paper_feedback_collection_validation_rows` for inspection.

Verification:

- RED before fix:
  `cargo test workflow_factor_profitability_lifecycle_rejects_ready_actionable_without_feedback_collection_flag -- --nocapture`
  failed with `paper_feedback_collection_ready=true`.
- RED before fix:
  `cargo test structural_branch_admission_blocks_feedback_collection_without_validation_rows -- --nocapture`
  failed with `paper_feedback_collection_ready=true`.
- GREEN after fix: both commands passed.
- `cargo test workflow_factor_profitability_lifecycle -- --nocapture` passed
  `11` tests.
- `cargo test structural_branch_admission -- --nocapture` passed `8` tests.

Decision:

- This tightens the quality floor for the easy feedback flywheel without moving
  the final practical tickets. Final `promotion_allowed`, `trade_usable`, and
  `update_goal` still require validated same-tree practical closure, accepted
  paper/live/broker feedback, verified cost, and ETH/full retained session
  proof.

Post-terminalization readback:

- Compact claim audit reported `status=pass`, `active_claims=0`,
  `live_factor_processes=0`, `promotion_allowed_true=0`,
  `trade_usable_true=0`, and `same_tree_practical_closure=null`.
- Objective snapshot under
  `/tmp/ict-engine-goal-consumer-revalidation-audit-20260531T152928+0800/objective_snapshot_after_feedback_collection_consumer_guard/`
  returned nonzero with `status=not_complete` and
  `completion_proven=false`. Remaining blockers are expected: skipped heavy
  done-definition gates, missing same-tree practical closure, dirty-worktree
  release readiness, and skipped remote release checks.

## 2026-05-31T17:06+0800 Current Loop Re-Audit

Current HEAD: `6591a02294175dacdde8f0c482f038cf705580e6`
(`6591a022 Fix done proof count merge`).

What changed in the loophole ledger:

- The accepted-feedback spoof fix was rechecked against both
  `not_paper_execution_feedback` and separator-token
  `not-paper_execution_feedback` forms.
- The canonical same-tree closure helper still emits
  `evidence_packet_validated=true` only when all practical evidence is present.
- Rust workflow/analyze validators still reject the legacy
  `evidence_validated=true` alias when `evidence_packet_validated=true` is
  absent.
- Feedback collection remains separate from practical promotion. Intermediate
  collection may be ready only when learning and paper admission are ready; it
  does not imply `deploy_ready`, `promotion_allowed`, or `trade_usable`.

Verification:

- `python3 -m unittest support.scripts.research.tests.test_same_tree_practical_closure support.scripts.research.tests.test_real_trade_feedback_labels support.scripts.tests.test_factor_claim_terminalization_audit -v`
  passed: `164` tests.
- `python3 -m py_compile support/scripts/research/same_tree_practical_closure.py support/scripts/research/real_trade_feedback_labels.py support/scripts/research/tests/test_same_tree_practical_closure.py support/scripts/research/tests/test_real_trade_feedback_labels.py`
  passed.
- `rustfmt --edition 2021 --check` passed for touched Rust files.
- Rust focused filters passed under
  `/tmp/ict-engine-cargo-target-closed-loop-current-20260531`:
  `execution_feedback`, `workflow_factor_profitability_lifecycle`,
  `structural_branch_admission`, `same_root_admission_practical_closure`, and
  `evidence_validated_alias`.
- `git diff --check` passed.
- Current compact claim audit passed with `active_claims=0`,
  `live_factor_processes=0`, `promotion_allowed_true=0`,
  `trade_usable_true=0`, and `same_tree_practical_closure=null`.
- Light done-definition passed with `completion_ready=false`, skipped heavy
  gates, tracked practical-admission/source debt `0`, and quarantined
  untracked debt still matching manifests.
- Current objective snapshot at
  `/tmp/ict-engine-objective-current-6591a022-codex-20260531T1658/objective_closure_snapshot.json`
  returned `status=not_complete`.

Remaining blockers:

- No validated same-tree practical-closure packet exists.
- Heavy done-definition gates were not run in the parent packet.
- Release/source alignment remains blocked by the shared dirty worktree.

Decision: continue the full objective. The current repair closes concrete
fail-open proof/readback loopholes, but it still produces no practical factor
and no `trade_usable=true` claim.
