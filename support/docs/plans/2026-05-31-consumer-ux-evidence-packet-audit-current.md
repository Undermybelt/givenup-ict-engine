# Consumer UX And Evidence Packet Audit - 2026-05-31

Owner: Codex
Route: `sd/ict-engine-maintenance-loop`
Status: active / not complete
Repo: `/Users/thrill3r/projects-ict-engine/ict-engine`
Branch: `main`
Observed HEAD: `113a43299c27e91903072427debda0e1df582a00`

## Objective

Audit whether `ict-engine` is complete for consumer-user experience, evidence
packet lightness and reuse, cooperation between packets, and practical trading
effect. Find loopholes, propose reasonable fixes, repeat the loop until current
evidence is strong enough. Commit only when the verified slice is coherent.

## Completion Definition

This objective is complete only when current artifacts prove all of these:

- A fresh consumer can run the documented zero-config path without private
  paths, private data, provider credentials, repo pollution, or unclear next
  action.
- Evidence packets are compact enough for quick agent/operator readback while
  preserving blocker details needed to act without opening many child files.
- Packet cooperation is fail-closed: parent snapshots cannot hide stale,
  partial, skipped, stale-head, stale-remote, dirty-tree, or source-debt child
  failures.
- Practical/live-use claims are separated from demo, candidate, sparse-positive,
  prep-only, and observation-only evidence.
- Tracking documentation records current evidence, loopholes, fixes,
  verification commands, blockers, and next actions.
- A commit exists for the verified coherent slice, staged by explicit path only,
  with unrelated dirty work preserved.

## Initial Current-State Evidence

- `git status --short --branch --untracked-files=no` showed `main...origin/main
  [ahead 256]` plus many tracked modifications across docs, runtime, provider,
  lifecycle, TOMAC wrappers, and audit scripts.
- `git status --short --untracked-files=all` counted `3249` untracked entries.
  This blocks broad staging, release claims, and any "already complete" answer.
- Existing relevant tracking doc:
  `support/docs/plans/2026-05-28-practical-admission-completion-gate-tracking.md`
  is still `active / objective not complete` and contains repeated packet
  cooperation fixes plus unresolved completion blockers from prior loops.
- Repo entry contracts read in this turn require current-turn commands,
  `/tmp` state, no private path leakage, no docs-as-runtime inputs, and no
  trade-readiness claims from demos/candidate packs.
- Process readback showed many Codex sessions and at least one long `rg`
  readback over factor docs. Those are not proof of completion and reinforce
  that shared-worktree changes must be isolated.

## Answer To User Check

No. I am not 100 percent confident the requested audit/optimization/commit work
is complete. Current evidence contradicts completion because the tree is dirty,
untracked residue is large, prior objective tracking is still open, and no fresh
same-turn completion snapshot has yet proved all consumer, packet, practical,
release, and commit gates.

## Loophole Loop 1

Potential loopholes to audit first:

1. Consumer quickstart may be documented but not freshly smoke-tested in the
   current dirty tree.
2. `objective_closure_snapshot.py` may still report blockers, or may omit
   blocker detail needed for lightweight reuse.
3. `done_definition_audit.py` heavy proof reuse may be stale against current
   `HEAD` or tracked-worktree fingerprint.
4. `release_readiness_audit.py` may fail because this shared tree is dirty or
   because source/mirror remote checks are stale.
5. Practical admission may still be blocked by active factor claims, live
   factor processes, source debt, or missing same-tree practical closure.
6. Consumer docs may mention reusable factor packs without a current registry or
   manifest verification step that proves clone-safe reuse.
7. Existing dirty changes may contain useful fixes, but broad commit is unsafe
   until each slice is verified and staged by explicit path.

Planned current-turn audit commands:

```bash
support/scripts/smoke_acceptance.sh
python3 support/scripts/objective_closure_snapshot.py --compact --check-remotes --output-dir /tmp/ict-engine-consumer-ux-evidence-audit-20260531T-current
python3 support/scripts/done_definition_audit.py --compact
python3 support/scripts/release_readiness_audit.py --check-remotes --compact
python3 support/scripts/research/downstream_practical_admission_source_check.py --tracked-run-wrappers
python3 support/scripts/check_script_manifest.py
python3 support/scripts/ci/check_docs_runtime_isolation.py
git diff --check
```

2026-05-31 loop-1 reproduction:

- Passed: `python3 support/scripts/check_script_manifest.py`.
- Passed: `python3 support/scripts/ci/check_docs_runtime_isolation.py`.
- Passed: `git diff --check`.
- Found loophole: the planned source-scan command used a nonexistent
  `--compact` option, and a shell-expanded newline file list in zsh was passed
  as one huge file name. This made the audit command easy to misuse and weak
  as reusable evidence.
- Fix in progress: add safe scanner inputs `--tracked-run-wrappers` and
  `--files-from`, plus tests and script docs.

## Loophole Loop 2

2026-05-31 current-turn reproduction:

- `python3 support/scripts/objective_closure_snapshot.py --compact --check-remotes --output-dir /tmp/ict-engine-consumer-ux-evidence-audit-20260531T-rerun`
  exited `2` with `summary.status=snapshot_failed`,
  `failed_audit=done_definition`, and `error=missing_json_output`.
- Root cause: parent snapshot default timeout was `90s`, while
  `done_definition_audit.py` could spend `180s` inside the practical-source
  scanner before emitting JSON. The parent packet therefore killed the child
  before blocker details were written.
- A standalone
  `python3 support/scripts/done_definition_audit.py --compact --output /tmp/ict-engine-consumer-ux-done-20260531T-rerun.json`
  eventually exited `1`, but its compact JSON contained the full scanner argv
  for `1066` arguments. That made the "compact" evidence packet too large and
  hard to reuse.

Fix:

- `support/scripts/objective_closure_snapshot.py` now passes bounded child
  timeouts to `done_definition_audit.py`. Current HEAD defaults the parent
  child-audit budget to `300s` and caps the done-definition source/help child
  timeout at `240s`, while still shrinking it for smaller explicit parent
  budgets (`90s -> 30s`, `180s -> 120s`).
- `support/scripts/done_definition_audit.py --compact` now summarizes large
  source-scan commands with `argv_head`, `arg_count`, `target_arg_count`,
  `sample_targets`, and `omitted_arg_count` instead of embedding every target
  path. Full non-compact reports still preserve raw command detail.

Verification:

- Passed:
  `python3 -m unittest support.scripts.tests.test_done_definition_audit -v`
  (`33/33`).
- Passed:
  `python3 -m unittest support.scripts.tests.test_objective_closure_snapshot -v`
  (`45/45`).
- Passed:
  `python3 support/scripts/check_script_manifest.py`.
- Passed:
  `python3 support/scripts/ci/check_docs_runtime_isolation.py`.
- Passed:
  `git diff --check -- support/scripts/done_definition_audit.py support/scripts/objective_closure_snapshot.py support/scripts/tests/test_done_definition_audit.py support/scripts/tests/test_objective_closure_snapshot.py support/docs/plans/2026-05-31-consumer-ux-evidence-packet-audit-current.md`.
- Fresh parent packet:
  `/tmp/ict-engine-consumer-ux-evidence-audit-20260531T-postfix/objective_closure_snapshot.json`
  exited `1` with `summary.status=not_complete`, not
  `snapshot_failed`. It preserved:
  `practical_admission_source_surface.scanner_error=timeout`,
  `scanner_timeout_seconds=30`, and command summary
  `arg_count=1066`, `target_arg_count=1064`, `omitted_arg_count=1059`.
- Packet size check:
  `objective_closure_snapshot.json=20153 bytes`,
  `done_definition_audit.compact.json=7329 bytes`.
- After the shared worktree advanced to HEAD `97f7e42d`, reran the current-file
  command:
  `python3 support/scripts/objective_closure_snapshot.py --compact --check-remotes --output-dir /tmp/ict-engine-consumer-ux-evidence-audit-20260531T-postfix-currentfile`.
  It exited `1` with `summary.status=not_complete` and no parent
  `snapshot_failed`. The source scanner completed under the bounded child
  timeout and reported `scanner_returncode=1`, `arg_count=1066`,
  `target_arg_count=1064`, `untracked_violation_count=461`,
  `untracked_violating_files=222`, and staged
  `practical_admission_source_debt_manifest.json`.

Current blockers after the fix:

- Done definition is no longer red on the current-file rerun, but it is still
  not completion proof because heavy gates remain skipped by default:
  `skipped_gates=["cargo_check_all_targets","cargo_clippy_all_targets_deny_warnings","cargo_test","smoke_acceptance_tmp_state"]`.
- Practical-source debt remains an objective blocker:
  `untracked_violation_count=461`, `untracked_violating_files=222`, with a
  mismatch against the existing practical-source quarantine.
- Factor claim terminalization is currently green for active claims, but it
  still proves no practical/live usable factor:
  `promotion_allowed_true=0`, `trade_usable_true=0`.
- Same-tree practical closure remains unproven:
  no validated packet covers provider/data, Pre-Bayes, BBN/workflow,
  path-ranker, execution-tree, feedback/update, and policy-training together.
- Release readiness remains red:
  `worktree_clean_for_release` and `source_origin_matches_selected_source`.
- Therefore the answer remains "not complete"; this slice only fixes one real
  evidence-packet cooperation and lightweight-readback loophole.

## Loophole Loop 3

2026-05-31T11:13-11:29+0800 follow-up:

- The Loop 2 `30s` bounded child scanner kept the parent packet from hard
  timing out, but it still downgraded the actionable source-debt manifest into
  `practical_admission_source_surface.scanner_error=timeout`.
- Repair: `support/scripts/objective_closure_snapshot.py` now uses a `300s`
  default parent child-audit timeout and derives a `240s` done-definition
  internal source/help scanner budget by default. Smaller explicit parent
  timeouts still bound the child scanner so tiny diagnostic runs fail closed.
- Regression coverage added:
  `test_effective_done_child_timeout_keeps_source_scan_inside_parent_budget`.

Verification:

- Passed:
  `python3 -m unittest support.scripts.tests.test_done_definition_audit -v`
  (`34/34`).
- Passed:
  `python3 -m unittest support.scripts.research.tests.test_downstream_practical_admission_source_check -v`
  (`46/46`).
- Passed:
  `python3 -m unittest support.scripts.tests.test_objective_closure_snapshot -v`
  (`46/46`).
- Passed:
  `python3 support/scripts/check_script_manifest.py`.
- Passed:
  `python3 support/scripts/ci/check_docs_runtime_isolation.py`.
- Passed:
  `git diff --check -- support/scripts/objective_closure_snapshot.py support/scripts/tests/test_objective_closure_snapshot.py support/docs/plans/2026-05-31-consumer-ux-evidence-packet-audit-current.md`.
- Fresh parent packet without explicit `--timeout-seconds`:
  `/tmp/ict-engine-consumer-ux-evidence-audit-20260531T-after-300s-timeout-fix/objective_closure_snapshot.json`
  exited `1` with `summary.status=not_complete`, not `snapshot_failed`.
  It preserved the full actionable manifests:
  `practical_admission_source_debt_manifest.json` and
  `await_launch_source_debt_manifest.json`.

Current blockers from that packet:

- `done_definition_not_completion_ready`: done-definition surface is only
  `partial_skipped_gates`; heavy gates still need `--run-all-heavy` before any
  completion proof.
- `practical_admission_source_debt`: untracked practical-admission debt is not
  quarantined by the current manifest fingerprint
  (`461` violations across `222` files).
- `same_tree_practical_closure_unproven`: no validated packet covers provider
  data, Pre-Bayes, BBN/workflow, path-ranker, execution-tree, feedback/update,
  and policy-training together.
- `release_readiness_blocked`: `worktree_clean_for_release` and
  `source_origin_matches_selected_source` remain unresolved.

Decision: still not complete. The current coherent repair only makes the
parent evidence packet reusable enough to expose the real blockers.

## Loophole Loop 4

2026-05-31T11:45+0800 resume after concurrent commits:

- Current HEAD is `113a43299c27e91903072427debda0e1df582a00` on `main`.
- Concurrent commits already landed the source-scanner invocation and packet
  readback changes:
  `113a4329 Fix objective source scanner invocation` and
  `d332ad09 Improve objective closure packet readback`.
- The remaining coherent local slice is the refreshed practical-admission debt
  quarantine plus the multiline `expression_text()` regression test that
  covers cached source-line extraction.

Verification:

- Passed:
  `python3 -m unittest support.scripts.research.tests.test_downstream_practical_admission_source_check -v`
  (`47/47`).
- Passed:
  `python3 -m unittest support.scripts.tests.test_done_definition_audit support.scripts.tests.test_objective_closure_snapshot -v`
  (`82/82`).
- Passed:
  `python3 support/scripts/check_script_manifest.py`.
- Passed:
  `python3 support/scripts/ci/check_docs_runtime_isolation.py`.
- Passed:
  `git diff --check -- support/docs/audits/practical-admission-source-debt-quarantine.json support/scripts/research/tests/test_downstream_practical_admission_source_check.py`.
- Tracked source scanner proof:
  `/usr/bin/time -p python3 support/scripts/research/downstream_practical_admission_source_check.py --tracked-run-wrappers --jobs 4 > /tmp/ict-engine-tracked-practical-source-scan-20260531T-codex.json`
  exited `0` in `real 4.97s`; JSON summary was `49` reports,
  `ok=True`, `violations=0`.
- Fresh parent packet:
  `python3 support/scripts/objective_closure_snapshot.py --compact --check-remotes --output-dir /tmp/ict-engine-consumer-ux-evidence-audit-20260531T-rerun-codex --timeout-seconds 180`
  exited `1` with `summary.status=not_complete`, not `snapshot_failed`.
  Packet sizes were:
  `objective_closure_snapshot.json=19826 bytes`,
  `done_definition_audit.compact.json=6724 bytes`,
  `factor_claim_terminalization_audit.compact.json=2049 bytes`,
  `release_readiness_audit.compact.json=5244 bytes`.

Current blockers from
`/tmp/ict-engine-consumer-ux-evidence-audit-20260531T-rerun-codex/objective_closure_snapshot.json`:

- `done_definition_not_completion_ready`: done-definition surface is
  `status=pass`, but `completion_ready=false` because heavy gates are still
  skipped:
  `cargo_check_all_targets`, `cargo_clippy_all_targets_deny_warnings`,
  `cargo_test`, `smoke_acceptance_tmp_state`.
- `factor_closure_blocked`: `live_factor_processes=1`, blocking reason
  `live_factor_processes`; queue head is pid `57740` with run root
  `ict-engine-tomac-eth-trend-ote-reacceleration-exact-aqlaunch-20260531T114456+0800`.
- `same_tree_practical_closure_unproven`: no validated same-tree practical
  closure packet exists; missing stages are provider data, Pre-Bayes,
  BBN/workflow, path-ranker, execution-tree, feedback/update, and
  policy-training.
- `release_readiness_blocked`: unresolved gates are
  `worktree_clean_for_release` and `source_origin_matches_selected_source`;
  remote readback itself passed for both origin and release mirror.

Decision: still not complete. The current slice only refreshes reviewed
shared-worktree source-debt quarantine and preserves the scanner performance
regression; it is not release, trade-use, or objective-completion evidence.

## Next Steps

1. Run the existing audits and capture exact blockers.
2. Pick the smallest real loophole that affects consumer UX, packet reuse, or
   practical-use evidence.
3. Fix it in source/tests/docs without touching unrelated dirty work.
4. Run focused regressions plus the relevant audit again.
5. Update this doc with evidence and repeat until no blocker remains or a real
   external/shared-worktree blocker is proven.
6. Commit only the coherent verified slice by explicit path.

## Superseded Refresh - 2026-05-31T03:44Z

Historical packet retained for drift context. It is superseded by Loophole
Loop 4 above, because the later
`/tmp/ict-engine-consumer-ux-evidence-audit-20260531T-rerun-codex/objective_closure_snapshot.json`
readback observed `factor_closure_blocked` with `live_factor_processes=1`.
Do not use this section as current completion evidence.

Earlier packet:

```bash
python3 support/scripts/objective_closure_snapshot.py --compact --check-remotes --output-dir /tmp/ict-engine-consumer-ux-evidence-audit-20260531T-after-head-113a4329
```

Output:

- Parent packet:
  `/tmp/ict-engine-consumer-ux-evidence-audit-20260531T-after-head-113a4329/objective_closure_snapshot.json`
- `summary.status=not_complete`
- `summary.blockers=[done_definition_not_completion_ready,
  same_tree_practical_closure_unproven, release_readiness_blocked]`
- `done_definition.head=113a43299c27e91903072427debda0e1df582a00`
- `done_definition.status=pass`, `completion_ready=false`,
  `evidence_level=partial_skipped_gates`
- `done_definition.practical_admission_source_surface.status=pass`,
  `scan_scope=tracked_run_wrappers_plus_tracked_report_files`,
  `candidate_wrapper_files=1063`, `tracked_scanned_files=50`,
  `tracked_violation_count=0`, `untracked_scanned_files=0`
- `await_launch_source_surface.status=pass`, with quarantined untracked await
  launch debt still visible: `46` violations across `46` untracked files,
  quarantine matched
- `factor_closure.status=pass`, `active_claims=0`,
  `live_factor_processes=0`, `blocking_reasons=[]`,
  `promotion_allowed_true=0`, `trade_usable_true=0`
- `same_tree_practical_closure=null`, so practical/live-use completion remains
  unproven even though claim terminalization blockers are clear
- `release_readiness.status=needs_fix`,
  `unresolved=[worktree_clean_for_release, source_origin_matches_selected_source]`
- `release_readiness.remote_details.enabled=true`,
  `origin_status=pass`, `release_mirror_status=pass`

Important drift during this turn:

- While auditing, concurrent repo work advanced HEAD from
  `7e95b910061980f25d96b58dbc8820289cc5250d` to
  `113a43299c27e91903072427debda0e1df582a00` with commits:
  `d332ad09 Improve objective closure packet readback` and
  `113a4329 Fix objective source scanner invocation`.
- Before that HEAD change, the parent packet still blocked on unmatched
  practical-admission untracked wrapper debt:
  `/tmp/ict-engine-consumer-ux-evidence-audit-20260531T-current-refresh/objective_closure_snapshot.json`
  reported `434` violations across `226` untracked files and
  `factor_closure.active_claims=5`.
- After the HEAD change, the practical-admission source gate is lightweight and
  deterministic for the completion packet: it scans tracked wrappers plus the
  tracked report file via `--tracked-run-wrappers --jobs 4`, and the parent no
  longer hides untracked await-launch residue because that debt remains
  separately quarantined and reported.

Answer to the 100% confidence question remains: no. The current evidence is
much better than the earlier packet, but completion is still disproven by:

1. heavy done-definition gates skipped in the current parent packet;
2. no validated same-tree practical closure packet covering provider/data,
   Pre-Bayes, BBN/workflow, path-ranker, execution tree, feedback/update, and
   policy-training stages;
3. release readiness failing on dirty worktree and selected-source origin
   alignment.

Next concrete steps:

1. Run focused regressions for `done_definition_audit` and
   `objective_closure_snapshot` after the source-scanner invocation change.
2. If focused tests pass, rerun the parent snapshot once more to check stability.
3. Locate or produce a validated `same_tree_practical_closure` packet; do not
   use `factor_closure.status=pass` or zero active claims as practical-use proof.
4. Only after practical closure and heavy done-definition evidence exist, build
   a clean selected export for release readiness instead of using this broad
   dirty worktree.
5. Stage only the verified coherent slice by explicit path; do not stage
   unrelated factor wrappers, run trees, or other agents' modified files.

## Verification After Scanner Fix - 2026-05-31T03:47Z

Focused regressions:

```bash
python3 -m unittest support.scripts.tests.test_done_definition_audit support.scripts.tests.test_objective_closure_snapshot -v
```

Result: `82` tests ran in `9.016s`, all `OK`.

Post-test stability packet:

```bash
python3 support/scripts/objective_closure_snapshot.py --compact --check-remotes --output-dir /tmp/ict-engine-consumer-ux-evidence-audit-20260531T-post-tests
```

Output:

- Parent packet:
  `/tmp/ict-engine-consumer-ux-evidence-audit-20260531T-post-tests/objective_closure_snapshot.json`
- `summary.status=not_complete`
- Blockers remained stable:
  `done_definition_not_completion_ready`,
  `same_tree_practical_closure_unproven`,
  `release_readiness_blocked`
- `done_definition.practical_admission_source_surface.status=pass`,
  `scan_scope=tracked_run_wrappers_plus_tracked_report_files`,
  `tracked_violation_count=0`
- `factor_closure.status=pass`, `active_claims=0`,
  `live_factor_processes=0`
- `release_readiness.remote_details.origin_status=pass`,
  `release_mirror_status=pass`

Verified improvement:

- The packet is now lighter and more reusable for the practical-admission source
  surface: the parent preserves the exact tracked scan scope and command, while
  untracked await-launch debt remains visible through the quarantined child
  manifest instead of being hidden.

Still not completion:

- `completion_ready=false` because the heavy done-definition gates are skipped.
- `same_tree_practical_closure=null`; no packet proves the live/practical chain.
- Release readiness remains blocked by the dirty shared worktree and selected
  source origin alignment.

Commit decision for this slice: do not claim objective completion yet. A commit
is only appropriate for a coherent verified slice; full-objective commit must
wait until the same-tree practical closure and heavy/release gates are proven.

## Final Current Readback - 2026-05-31T03:50Z

The factor-closure surface is time-variant in this shared tree. A focused
factor compact audit briefly reported `status=pass`, `live_factor_processes=0`
at `2026-05-31T03:49Z`, but the later parent snapshot is the current objective
readback for this doc.

Command:

```bash
python3 support/scripts/objective_closure_snapshot.py --compact --check-remotes --output-dir /tmp/ict-engine-consumer-ux-evidence-audit-20260531T-final-codex --timeout-seconds 180
```

Result:

- Parent packet:
  `/tmp/ict-engine-consumer-ux-evidence-audit-20260531T-final-codex/objective_closure_snapshot.json`
- Exit code: `1`
- `summary.status=not_complete`
- `summary.blockers=[done_definition_not_completion_ready,
  factor_closure_blocked, same_tree_practical_closure_unproven,
  release_readiness_blocked]`
- `done_definition.status=pass`, `completion_ready=false`,
  `skip_count=4`; skipped heavy gates are `cargo_check_all_targets`,
  `cargo_clippy_all_targets_deny_warnings`, `cargo_test`, and
  `smoke_acceptance_tmp_state`.
- `practical_admission_source_surface.status=pass`,
  `tracked_violation_count=0`, `untracked_violation_count=0`.
- `await_launch_source_surface.status=pass`; quarantined untracked await-launch
  debt remains visible at `46` violations across `46` untracked files.
- `factor_closure.status=needs_attention`, `live_factor_processes=1`,
  queue head pid `63182`, run root
  `ict-engine-lbr-310-grail-pullback-exact-aq-20260531T114834+0800`.
- `same_tree_practical_closure=null`; no validated practical closure packet
  covers provider/data, Pre-Bayes, BBN/workflow, path-ranker, execution-tree,
  feedback/update, and policy-training.
- `release_readiness.status=needs_fix`; unresolved gates remain
  `worktree_clean_for_release` and `source_origin_matches_selected_source`.
  Remote readback itself passed for both origin and release mirror.

Decision: still not complete. Current evidence supports only a narrow verified
source-debt/readback slice, not objective completion, release readiness, or
practical trade usability.

## Verification After Source-Scope Preservation - 2026-05-31T03:48Z

Current coherent local slice:

- `done_definition_audit.py --compact` keeps practical/await-launch source
  scan details even when the gate status is `pass`, so parent packets can prove
  what was actually scanned instead of showing only a green surface.
- `objective_closure_snapshot.py` preserves the same source-scan coverage fields
  in the parent surface:
  `scan_scope`, `candidate_wrapper_files`, `scanned_files`,
  `tracked_scanned_files`, `untracked_scanned_files`, and
  `violations_by_type`.
- Tests now cover pass-state source proof retention, parent preservation, and
  multiline source-expression normalization in the downstream practical source
  scanner.

Focused verification:

- Passed:
  `python3 -m unittest support.scripts.tests.test_objective_closure_snapshot -v`
  (`47/47`).
- Passed:
  `python3 -m unittest support.scripts.tests.test_done_definition_audit -v`
  (`35/35`).
- Passed:
  `python3 -m unittest support.scripts.research.tests.test_downstream_practical_admission_source_check -v`
  (`47/47`).
- Passed:
  `python3 support/scripts/check_script_manifest.py`.
- Passed:
  `python3 support/scripts/ci/check_docs_runtime_isolation.py`.
- Passed:
  `git diff --check -- support/docs/audits/practical-admission-source-debt-quarantine.json support/scripts/done_definition_audit.py support/scripts/tests/test_done_definition_audit.py support/scripts/objective_closure_snapshot.py support/scripts/tests/test_objective_closure_snapshot.py support/scripts/research/tests/test_downstream_practical_admission_source_check.py support/docs/plans/2026-05-31-consumer-ux-evidence-packet-audit-current.md`.

Fresh parent packet:

```bash
python3 support/scripts/objective_closure_snapshot.py --compact --check-remotes --output-dir /tmp/ict-engine-consumer-ux-evidence-audit-20260531T-after-source-scope
```

Result:

- Exit code `1`, fail-closed because the full objective is still not proven.
- Parent packet:
  `/tmp/ict-engine-consumer-ux-evidence-audit-20260531T-after-source-scope/objective_closure_snapshot.json`.
- `summary.status=not_complete`.
- Blockers:
  `done_definition_not_completion_ready`,
  `same_tree_practical_closure_unproven`,
  `release_readiness_blocked`.
- `done_definition.head=113a43299c27e91903072427debda0e1df582a00`.
- `done_definition.status=pass`, `completion_ready=false`,
  `pass_count=6`, `fail_count=0`, `skip_count=4`, `total_gates=10`.
- Heavy gates still skipped:
  `cargo_check_all_targets`, `cargo_clippy_all_targets_deny_warnings`,
  `cargo_test`, `smoke_acceptance_tmp_state`.
- `practical_admission_source_surface.status=pass`,
  `scan_scope=tracked_run_wrappers_plus_tracked_report_files`,
  `candidate_wrapper_files=1063`, `scanned_files=50`,
  `tracked_scanned_files=50`, `untracked_scanned_files=0`,
  `tracked_violation_count=0`, `untracked_violation_count=0`,
  `violations_by_type={}`.
- `await_launch_source_surface.status=pass`, but quarantined untracked
  await-launch debt remains visible: `46` violations across `46` untracked
  files, quarantine matched.
- `factor_closure.status=pass`, `active_claims=0`,
  `live_factor_processes=0`, `blocking_reasons=[]`,
  `promotion_allowed_true=0`, `trade_usable_true=0`.
- `same_tree_practical_closure=null`; missing practical-chain stages remain
  provider/data, Pre-Bayes, BBN/workflow, path-ranker, execution-tree,
  feedback/update, and policy-training.
- `release_readiness.status=needs_fix`, unresolved gates are
  `worktree_clean_for_release` and `source_origin_matches_selected_source`.
  Remote readback passed for both origin and release mirror.

Decision: still not complete. This slice improves packet lightness/reuse by
keeping pass-state source-scan proof in compact parent packets. It is not
trade-use evidence, release evidence, or completion evidence.
