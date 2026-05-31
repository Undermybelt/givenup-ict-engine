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

## Same-Tree Practical Closure Readback - 2026-05-31T03:53Z

Retained for same-tree closure lookup evidence. Its factor-occupancy row is
superseded by the later Post-Commit Readback below, which observed
`factor_closure_blocked` with `live_factor_processes=1`. The
`same_tree_practical_closure=null` finding remains consistent with the later
parent snapshot.

Focused search:

```bash
rg --files support | rg 'same_tree_practical_closure.*\\.json$|same-tree-practical-closure.*\\.json$'
find /tmp -maxdepth 4 \( -name '*same_tree_practical_closure*.json' -o -name '*same-tree-practical-closure*.json' \) -type f
find /private/tmp -maxdepth 4 \( -name '*same_tree_practical_closure*.json' -o -name '*same-tree-practical-closure*.json' \) -type f
python3 support/scripts/factor_claim_terminalization_audit.py --compact --portable-paths --output /tmp/ict-engine-factor-closure-current-after-posttests.json
```

Result:

- No `same_tree_practical_closure*.json` or `same-tree-practical-closure*.json`
  file was found under tracked support paths or shallow `/tmp`/`/private/tmp`
  ict-engine run roots.
- `/tmp/ict-engine-factor-closure-current-after-posttests.json` reports:
  `summary.status=pass`, `active_claims=0`, `live_factor_processes=0`,
  `promotion_allowed_true=0`, `trade_usable_true=0`,
  `same_tree_practical_closure=null`.
- The factor-training current workdoc tail also still reports practical flags
  false and `same_tree_practical_closure=null`.

Interpretation:

- The current blocker is not a parent-packet lookup bug. There is no validated
  same-tree practical closure packet available to reuse.
- Creating a pass packet now would be fabrication. The canonical helper in
  `support/scripts/research/same_tree_practical_closure.py` requires the full
  lifecycle tuple plus explicit stage command rows, cost model proof,
  retained-session coverage, market-data provenance, path-ranker use, policy
  lifecycle counts, and accepted paper/live/broker execution feedback.
- Therefore the only honest solution path is to produce a real same-root
  provider/data -> Pre-Bayes -> BBN/workflow -> path-ranker -> execution-tree
  -> feedback/update -> policy-training packet, or keep completion false.

## Consumer Smoke Attempt - 2026-05-31T03:56Z

Command:

```bash
STATE_DIR=/tmp/ict-engine-consumer-ux-smoke-20260531T0356Z OUT_DIR=/tmp/ict-engine-consumer-ux-smoke-20260531T0356Z-out support/scripts/smoke_acceptance.sh
```

Result: incomplete, not a pass/fail proof. I stopped this smoke after it waited
on Cargo work already running in other sessions.

Evidence captured before stop:

- `/tmp/ict-engine-consumer-ux-smoke-20260531T0356Z-out/provider_status.out`
  exists and reports provider matrix readiness:
  `entry_model:3/3 ready`, `live_runtime:3/5 ready`,
  `local_runtime:2/2 ready`, `market_data:9/9 ready`.
- `/tmp/ict-engine-consumer-ux-smoke-20260531T0356Z-out/workflow_empty.out`
  exists and correctly reports `DEMO | workflow_status | no_workflow_state`
  with the next command `ict-engine analyze --symbol DEMO --demo --state-dir
  <local-path> --human`.
- `provider_status.err` and `workflow_empty.err` are empty.
- `analyze_demo.out` and `analyze_demo.err` are empty because the smoke was
  stopped during/just after the `analyze_demo` step.
- `/tmp/ict-engine-consumer-ux-smoke-20260531T0356Z/DEMO/workflow_snapshot.json`
  exists, but this partial artifact is not sufficient to mark smoke passed.

Concurrent blocker:

- Process readback showed other sessions running heavy done-definition audits:
  `done_definition_audit.py --compact --run-all-heavy`, with child
  `cargo check --all-targets` / `cargo test`.
- The smoke child `cargo run --quiet -- workflow-status --symbol DEMO ...` had
  been waiting under the smoke script for several minutes, consistent with Cargo
  lock contention rather than a validated consumer failure.

Conclusion:

- Do not count this smoke as completion evidence.
- Rerun `support/scripts/smoke_acceptance.sh` after the concurrent heavy Cargo
  jobs finish if the next goal turn wants to promote done-definition coverage.

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

## Current Readback After Source-Scope Commit - 2026-05-31T03:56Z

Current HEAD:

- `e7c6cf759f30472288f22accd21fbe72329a3eed`
  (`Preserve objective source scan proof`)

Fresh parent packet after that commit:

```bash
python3 support/scripts/objective_closure_snapshot.py --compact --check-remotes --output-dir /tmp/ict-engine-consumer-ux-evidence-audit-20260531T-post-source-scope-commit
```

Result:

- Exit code `1`; objective is still not complete.
- Parent packet:
  `/tmp/ict-engine-consumer-ux-evidence-audit-20260531T-post-source-scope-commit/objective_closure_snapshot.json`.
- Blockers:
  `done_definition_not_completion_ready`,
  `same_tree_practical_closure_unproven`,
  `release_readiness_blocked`.
- `done_definition.head=e7c6cf759f30472288f22accd21fbe72329a3eed`,
  `status=pass`, `completion_ready=false`, `evidence_level=partial_skipped_gates`.
- Heavy gates were skipped in that parent packet:
  `cargo_check_all_targets`, `cargo_clippy_all_targets_deny_warnings`,
  `cargo_test`, and `smoke_acceptance_tmp_state`.
- `factor_closure.status=pass`, `active_claims=0`,
  `live_factor_processes=0` in that parent packet.
- `same_tree_practical_closure=null`; missing stages remain provider/data,
  Pre-Bayes, BBN/workflow, path-ranker, execution tree, feedback/update, and
  policy-training.
- `release_readiness.status=needs_fix`; unresolved gates remain
  `worktree_clean_for_release` and `source_origin_matches_selected_source`;
  remote readback passed for both origin and release mirror.

Latest focused claim audit is time-variant and now blocks factor closure again:

```bash
python3 support/scripts/factor_claim_terminalization_audit.py --compact
```

Result at `2026-05-31T03:56:17Z`:

- Exit code `1`.
- `summary.status=needs_attention`.
- `live_factor_processes=1`; blocking reason `live_factor_processes`.
- Live run root:
  `/tmp/ict-engine-tomac-tsmom-vol-scaled-low-turnover-aq-20260531T115002+0800`.
- `promotion_allowed_true=0`, `trade_usable_true=0`,
  `same_tree_practical_closure=null`.

Heavy done-definition proof is not usable as completion evidence:

- File:
  `/tmp/ict-engine-closed-loop-loophole-audit-20260531T110505+0800/done_definition_audit_heavy.json`.
- It was produced against old `head=113a43299c27e91903072427debda0e1df582a00`,
  not current `e7c6cf759f30472288f22accd21fbe72329a3eed`.
- It also failed:
  `cargo_clippy_all_targets_deny_warnings`,
  `cargo_test`, and `smoke_acceptance_tmp_state`.

Decision: still not complete. Do not launch practical closure work while the
live factor process is active. Re-run heavy done-definition evidence only after
the current Rust/smoke processes and factor runtime have cleared, then compare
the proof `head` and tracked-worktree fingerprint before reusing it.

## Classifier Follow-Up - 2026-05-31T03:54Z

Additional loophole found during live audit readback:

- Symptom: while a parent/done-definition audit was running,
  `factor_claim_terminalization_audit.py --compact` could count
  `downstream_practical_admission_source_check.py` as
  `live_factor_processes=1` because the scanner command includes many
  `run_tomac_*.py` wrapper paths as arguments.
- Root cause: live-process classification searched the full command string for
  wrapper names before excluding this audit scanner.
- Fix in working tree: classify
  `downstream_practical_admission_source_check.py` as audit coordination and add
  regression
  `test_live_process_classifier_ignores_practical_source_scanner_with_wrapper_args`.
- Verification passed:
  `python3 -m unittest support.scripts.tests.test_factor_claim_terminalization_audit.FactorClaimTerminalizationAuditTest.test_live_process_classifier_ignores_practical_source_scanner_with_wrapper_args -v`
  and
  `python3 -m unittest support.scripts.tests.test_factor_claim_terminalization_audit -v`
  (`115/115 OK` in the focused run).
- Consumer smoke also passed:
  `support/scripts/smoke_acceptance.sh` wrote
  `/tmp/ict-engine-smoke-acceptance-20260531T032327Z/smoke-output` and ended
  with
  `smoke_acceptance: passed state_dir=/tmp/ict-engine-smoke-acceptance-20260531T032327Z`.

Fresh current-head parent readback:

```bash
python3 support/scripts/objective_closure_snapshot.py --compact --check-remotes --output-dir /tmp/ict-engine-consumer-ux-evidence-audit-20260531T115413+0800-codex-current-head
```

Result:

- HEAD: `e7c6cf759f30472288f22accd21fbe72329a3eed`.
- Exit code `1`; `summary.status=not_complete`.
- Blockers:
  `done_definition_not_completion_ready`,
  `factor_closure_blocked`,
  `same_tree_practical_closure_unproven`,
  `release_readiness_blocked`.
- `done_definition.status=pass`, but `completion_ready=false` because heavy
  gates remain skipped: `cargo_check_all_targets`,
  `cargo_clippy_all_targets_deny_warnings`, `cargo_test`,
  `smoke_acceptance_tmp_state`.
- `practical_admission_source_surface.status=pass` with
  `scan_scope=tracked_run_wrappers_plus_tracked_report_files`,
  `candidate_wrapper_files=1063`, `scanned_files=50`,
  `tracked_violation_count=0`, and `untracked_violation_count=0`.
- `factor_closure.status=needs_attention` because a real live process was
  present: pid `68325`, run root
  `ict-engine-tomac-tsmom-vol-scaled-low-turnover-aq-20260531T115002+0800`.
- `same_tree_practical_closure=null`; missing stages remain provider/data,
  Pre-Bayes, BBN/workflow, path-ranker, execution-tree, feedback/update, and
  policy training.
- `release_readiness.status=needs_fix`; unresolved gates remain
  `worktree_clean_for_release` and `source_origin_matches_selected_source`;
  origin and release-mirror remote readback passed.

Decision: still not complete and no completion commit should be made from this
state. Current staging contains broader concurrent changes in
`support/scripts/factor_claim_terminalization_audit.py` and its tests; do not
commit them as a completion slice without explicit staged-diff review.

## Post-Commit Readback - 2026-05-31T03:54Z

After commit `e7c6cf759f30472288f22accd21fbe72329a3eed`
(`Preserve objective source scan proof`), the same-turn objective snapshot is:

```bash
python3 support/scripts/objective_closure_snapshot.py --compact --check-remotes --output-dir /tmp/ict-engine-consumer-ux-evidence-audit-20260531T-post-commit-codex --timeout-seconds 180
```

Result:

- Exit code `1`.
- Parent packet:
  `/tmp/ict-engine-consumer-ux-evidence-audit-20260531T-post-commit-codex/objective_closure_snapshot.json`
- `summary.status=not_complete`, `completion_proven=false`.
- Blockers:
  `done_definition_not_completion_ready`,
  `factor_closure_blocked`,
  `same_tree_practical_closure_unproven`,
  `release_readiness_blocked`.
- `done_definition.head=e7c6cf759f30472288f22accd21fbe72329a3eed`,
  `status=pass`, `completion_ready=false`, `pass_count=6`,
  `fail_count=0`, `skip_count=4`.
- Skipped heavy gates:
  `cargo_check_all_targets`, `cargo_clippy_all_targets_deny_warnings`,
  `cargo_test`, `smoke_acceptance_tmp_state`.
- `practical_admission_source_surface.status=pass`,
  `scan_scope=tracked_run_wrappers_plus_tracked_report_files`,
  `tracked_violation_count=0`, `untracked_violation_count=0`.
- `await_launch_source_surface.status=pass`; quarantined untracked await-launch
  debt remains visible at `46` violations across `46` untracked files.
- `factor_closure.status=needs_attention`, `live_factor_processes=1`,
  queue head pid `68325`, run root
  `ict-engine-tomac-tsmom-vol-scaled-low-turnover-aq-20260531T115002+0800`.
- `same_tree_practical_closure=null`; missing practical-chain stages remain
  provider/data, Pre-Bayes, BBN/workflow, path-ranker, execution-tree,
  feedback/update, and policy-training.
- `release_readiness.status=needs_fix`; unresolved gates are
  `worktree_clean_for_release` and `source_origin_matches_selected_source`.
  Remote readback passed for both origin and release mirror.

Additional verification on the post-commit tree:

- Passed:
  `python3 -m unittest support.scripts.tests.test_done_definition_audit support.scripts.tests.test_objective_closure_snapshot support.scripts.research.tests.test_downstream_practical_admission_source_check -v`
  (`129/129`).
- Passed: `python3 support/scripts/check_script_manifest.py`.
- Passed: `python3 support/scripts/ci/check_docs_runtime_isolation.py`.
- Passed:
  `git diff --check -- support/docs/audits/practical-admission-source-debt-quarantine.json support/docs/plans/2026-05-31-consumer-ux-evidence-packet-audit-current.md support/scripts/done_definition_audit.py support/scripts/objective_closure_snapshot.py support/scripts/research/tests/test_downstream_practical_admission_source_check.py support/scripts/tests/test_done_definition_audit.py support/scripts/tests/test_objective_closure_snapshot.py`.

Decision: still not complete. The committed slice improves objective packet
readback and source-scan proof preservation, but current evidence still blocks
full completion, release readiness, and practical trade-use claims.

## Current-Head Resume Readback - 2026-05-31T04:05Z

Resume routing and local readback were repeated before acting. Current git
state changed during the readback, so the first fresh packet for
`8daaaa8988543206aeb05d0300e5c67406823bd4` was treated as stale and a second
packet was generated for the actual current head.

Current HEAD:

- `bc0f7beb85087a40d69c484db3d1785a6aa7e0a4`
  (`Reject marker-only practical closure in workflow status`).
- `git status --short --branch --untracked-files=no` shows
  `main...origin/main [ahead 263]` and `52` tracked dirty entries in the
  done-definition fingerprint.
- `git diff --cached --name-only` is empty at this readback point; earlier
  staged files were consumed by concurrent commits.

Commands:

```bash
git status --short --branch
git diff --cached --name-only
python3 support/scripts/factor_claim_terminalization_audit.py --compact
python3 support/scripts/objective_closure_snapshot.py --compact --check-remotes --output-dir /tmp/ict-engine-consumer-ux-evidence-audit-20260531T1208-current-codex
ps -p 68325 -o pid,ppid,etime,stat,command
```

Fresh packet:

- `/tmp/ict-engine-consumer-ux-evidence-audit-20260531T1208-current-codex/objective_closure_snapshot.json`
- Exit code `1`.
- `summary.status=not_complete`, `completion_proven=false`.
- Packet sizes remain lightweight enough for quick reuse:
  `objective_closure_snapshot.json` about `24K`,
  `done_definition_audit.compact.json` about `8K`,
  `factor_claim_terminalization_audit.compact.json` about `4K`,
  `release_readiness_audit.compact.json` about `8K`, and
  `await_launch_source_debt_manifest.json` about `20K`.

Current blocker details:

- `done_definition_not_completion_ready`: `done_definition.status=pass`, but
  `completion_ready=false` with skipped heavy gates
  `cargo_check_all_targets`, `cargo_clippy_all_targets_deny_warnings`,
  `cargo_test`, and `smoke_acceptance_tmp_state`.
- `practical_admission_source_surface.status=pass`:
  `tracked_violation_count=0`, `untracked_violation_count=0`.
- `await_launch_source_surface.status=pass`; known untracked await-launch debt
  is quarantined and still staged into the packet as
  `await_launch_source_debt_manifest.json` with `46` violations across `46`
  untracked files.
- `factor_closure_blocked`: `live_factor_processes=1`, pid `68325`, run root
  `ict-engine-tomac-tsmom-vol-scaled-low-turnover-aq-20260531T115002+0800`.
  The live command is the source-backed
  `tsmom_vol_scaled_low_turnover_rrr` clean-AQ family over NQ
  `1h,4h,1d`, with `--timeout 1200`.
- `same_tree_practical_closure_unproven`: no validated packet; missing stages
  remain provider/data, Pre-Bayes, BBN/workflow, path-ranker, execution-tree,
  feedback/update, and policy-training.
- `release_readiness_blocked`: remote readback now passes for origin and the
  release mirror, but `worktree_clean_for_release` and
  `source_origin_matches_selected_source` remain unresolved.

Decision: still not complete. Do not launch another overlapping factor lane
while pid `68325` owns the live AQ runtime, and do not claim practical or
release readiness from this packet. The next safe action is to wait for that
live process to finish, inspect its terminal artifacts, then rerun the compact
factor audit and parent objective snapshot before choosing heavy-gate,
same-tree-practical-closure, or clean-release work.

## Clean-AQ Terminal Runtime Classifier Fix - 2026-05-31T04:17Z

Observed loophole:

- The `20260531T1208-current-codex` parent packet reported
  `factor_closure_blocked` from pid `68325`/later pid `86048` under
  `/tmp/ict-engine-tomac-tsmom-vol-scaled-low-turnover-aq-20260531T115002+0800`
  even though the run root already had terminal clean-AQ evidence:
  `checks/run_tomac_1h.exit=0`, `summary.json`, and
  `summaries/autoquant_clean_1h_gate.json`.
- That terminal packet was observation-only:
  `decision=observation_no_autoquant_survivor_yet`,
  `promotion_allowed=false`, `trade_usable=false`, `update_goal=false`,
  `downstream_allowed=false`, `pre_bayes_allowed=false`, `bbn_allowed=false`,
  `catboost_allowed=false`, and `execution_tree_allowed=false`.
- Root cause: `factor_claim_terminalization_audit.py` already ignored
  terminalized loop artifacts with `terminal_metrics.json` /
  `terminal_decision_summary.md`, but not clean-AQ wrappers whose terminal
  evidence lives in `summary.json` plus `aq_commands` /
  `aq_gate_summaries`. A wrapper process could therefore briefly keep parent
  objective packets blocked after the factor economics had already terminalized
  as non-promotable.

Fix:

- `support/scripts/factor_claim_terminalization_audit.py` now treats a
  descendant-free process as non-live when its run root has terminal clean-AQ
  artifacts proving every AQ command exited `0` without timeout and every AQ
  gate summary is explicitly non-promotable:
  `promotion_allowed=false`, `trade_usable=false`, `update_goal=false`, with a
  nonempty decision.
- Added regression:
  `test_drop_stale_failed_tomac_prep_wrappers_drops_terminalized_clean_aq_wrapper_without_descendants`.

Verification:

- RED first:
  `python3 -m unittest support.scripts.tests.test_factor_claim_terminalization_audit.FactorClaimTerminalizationAuditTest.test_drop_stale_failed_tomac_prep_wrappers_drops_terminalized_clean_aq_wrapper_without_descendants -v`
  failed before the source change because the terminalized clean-AQ wrapper
  stayed in the live process list.
- GREEN:
  the same focused test passed after the fix.
- Passed:
  `python3 -m unittest support.scripts.tests.test_factor_claim_terminalization_audit -v`
  (`121/121 OK`).
- Passed:
  `python3 support/scripts/check_script_manifest.py`.
- Passed:
  `python3 support/scripts/ci/check_docs_runtime_isolation.py`.
- Passed:
  `git diff --check -- support/scripts/factor_claim_terminalization_audit.py support/scripts/tests/test_factor_claim_terminalization_audit.py support/docs/plans/2026-05-31-consumer-ux-evidence-packet-audit-current.md`.
- Direct compact factor audit after the fix:
  `python3 support/scripts/factor_claim_terminalization_audit.py --compact`
  reported `status=pass`, `live_factor_processes=0`,
  `active_claims=0`, `promotion_allowed_true=0`,
  `trade_usable_true=0`, and `same_tree_practical_closure=null`.

Fresh parent packet after the fix:

```bash
python3 support/scripts/objective_closure_snapshot.py --compact --check-remotes --output-dir /tmp/ict-engine-consumer-ux-evidence-audit-20260531T-after-clean-aq-classifier-fix
```

Result:

- Exit code `1`; still fail-closed, not complete.
- Parent packet:
  `/tmp/ict-engine-consumer-ux-evidence-audit-20260531T-after-clean-aq-classifier-fix/objective_closure_snapshot.json`.
- `summary.status=not_complete`, `completion_proven=false`.
- HEAD observed by the packet:
  `19771dc16d68eaf866526efe8175e5ff3a62be65`.
- Blockers after the classifier fix:
  `done_definition_not_completion_ready`,
  `same_tree_practical_closure_unproven`,
  `release_readiness_blocked`.
- The previous factor-closure blocker is gone in this packet:
  `factor_closure.status=pass`, `live_factor_processes=0`,
  `active_claims=0`, `blocking_reasons=[]`,
  `promotion_allowed_true=0`, `trade_usable_true=0`.
- Done-definition remains partial because the heavy gates are skipped:
  `cargo_check_all_targets`, `cargo_clippy_all_targets_deny_warnings`,
  `cargo_test`, and `smoke_acceptance_tmp_state`.
- Same-tree practical closure remains unproven; the missing stages remain
  provider/data, Pre-Bayes, BBN/workflow, path-ranker, execution-tree,
  feedback/update, and policy-training.
- Release readiness remains blocked. In this run, remote readback failed for
  both origin and release mirror, and `worktree_clean_for_release` is still
  unresolved.

Decision: still not complete. This slice fixes a parent/child packet
cooperation false blocker, but it is not heavy done-definition proof, not
same-tree practical closure, not release readiness, and not practical trade-use
evidence.

## Continuation Readback - 2026-05-31T12:16+0800

Current HEAD:

- `bc0f7beb85087a40d69c484db3d1785a6aa7e0a4`
  (`Reject marker-only practical closure in workflow status`).

Current-state checks repeated in this continuation:

```bash
git status --short --branch --untracked-files=no
python3 support/scripts/factor_claim_terminalization_audit.py --compact
ps -axo pid,ppid,etime,command | rg -i 'run_tomac|auto.?quant|freqtrade|fetch_external|ibkr|provider-status|objective_closure_snapshot|done_definition_audit|policy-training-status|cargo (check|clippy|test)|smoke_acceptance'
jq '{timestamp_utc, summary}' /tmp/ict-engine-consumer-ux-evidence-audit-20260531T1208-current-codex/objective_closure_snapshot.json
```

Current evidence:

- The `20260531T1208-current-codex` parent packet remains current for
  `bc0f7beb` until a newer packet is generated after runtime clears.
  It is not completion evidence: `summary.status=not_complete`.
- The ETH OTE AQ launch root
  `/tmp/ict-engine-tomac-eth-trend-ote-reacceleration-exact-aqlaunch-20260531T120650+0800`
  terminalized fail-closed:
  `decision=exact_aq_terminal_readback_practical_lifecycle_incomplete`,
  `status=exact_aq_completed_fail_closed`,
  `promotion_allowed=false`, `trade_usable=false`, `update_goal=false`,
  `same_tree_practical_closure=null`.
- The TSMOM root
  `/tmp/ict-engine-tomac-tsmom-vol-scaled-low-turnover-aq-20260531T115002+0800`
  completed `1h` and `4h` AQ reads but was relaunched for `30m`; latest
  factor audit still reported `summary.status=needs_attention`,
  `live_factor_processes=1`, `blocking_reasons=[live_factor_processes]`,
  and `same_tree_practical_closure=null`.
- Two heavy done-definition audits are still running and have not produced
  reusable JSON proof yet:
  `/tmp/ict-engine-done-definition-heavy-20260531T-after-source-scope-commit.json`
  and `/tmp/ict-engine-done-definition-heavy-20260531T-current-turn.json`.
- Current full-objective blockers therefore remain:
  `done_definition_not_completion_ready`,
  `factor_closure_blocked`,
  `same_tree_practical_closure_unproven`,
  and `release_readiness_blocked`.

Decision: still not complete. Do not mark `trade_usable=true`, do not claim
release readiness, and do not commit a completion slice. The next safe action is
still read-only: wait for the active AQ process and heavy done-definition
audits to finish, inspect their artifacts, then rerun compact factor audit and
the parent objective snapshot.

## Factor Runtime Wait Checkpoint - 2026-05-31T04:14Z

Current HEAD advanced again while this resume slice was running:

- `bc1b575787bc8fde00a2c821c8de52a359363011`
  (`Balance factor flywheel admission gates`).
- Branch status: `main...origin/main [ahead 264]`.

TSMOM low-turnover AQ root remains current runtime ownership:

- Root:
  `/tmp/ict-engine-tomac-tsmom-vol-scaled-low-turnover-aq-20260531T115002+0800`
- Current live pid:
  `98894`
- Command:
  `run_tomac_index_futures_clean_aq_v1.py --root /tmp/ict-engine-tomac-tsmom-vol-scaled-low-turnover-aq-20260531T115002+0800 --compact-root support/docs/experiments/actionable-regime-confidence/runs/20260531T115002+0800-codex-tomac-tsmom-vol-scaled-low-turnover-aq-v1 --symbols NQ --start 2021-01-01 --end 2025-12-31 --timeframes 5m,15m,30m,1h,4h,1d --families tsmom_vol_scaled_low_turnover_rrr --aq-smoke-timeframe 30m --aq-symbol-limit 1 --timeout 1200`

Readbacks:

- Earlier partial TSMOM gate files for `1h`, `4h`, and `1d` all reported
  `decision=observation_no_autoquant_survivor_yet`,
  `promotion_allowed=false`, `trade_usable=false`, `update_goal=false`,
  `survivors_instrument_cost=[]`, `downstream_allowed=false`, and
  `execution_tree_allowed=false`.
- The expanded current process is still live and must own final root
  interpretation until it exits.
- `python3 support/scripts/factor_claim_terminalization_audit.py --compact`
  at `2026-05-31T04:14Z` returned `status=needs_attention`,
  `live_factor_processes=1`, `promotion_allowed_true=0`,
  `trade_usable_true=0`, and `same_tree_practical_closure=null`.

Fresh current-head parent packet:

- `/tmp/ict-engine-consumer-ux-evidence-audit-20260531T1212-factor-clear-codex/objective_closure_snapshot.json`
- It was generated for `bc1b575787bc8fde00a2c821c8de52a359363011` but was
  not closure evidence because the expanded TSMOM process appeared during the
  child audits.
- `summary.status=not_complete`.
- Blockers remained:
  `done_definition_not_completion_ready`, `factor_closure_blocked`,
  `same_tree_practical_closure_unproven`, and `release_readiness_blocked`.
- Done definition was still partial with skipped heavy gates:
  `cargo_check_all_targets`, `cargo_clippy_all_targets_deny_warnings`,
  `cargo_test`, and `smoke_acceptance_tmp_state`.
- Release readiness was blocked by `worktree_clean_for_release` and a
  transient/current `remote_readback` failure for source origin while the
  release mirror passed.

Decision: still not complete. The only safe next factor-side action is to wait
for pid `98894` to exit, then inspect the same root's latest summaries and
rerun compact factor closure plus the parent objective snapshot. Do not commit
this tracking update as completion evidence.

## Continuation Readback - 2026-05-31T12:21+0800

Routing was repeated before this continuation:

- Route alias: `sd/ict-engine-maintenance-loop`.
- Files read:
  `~/.hermes/routing/skill-router.md`,
  `~/.hermes/routing/project-router.md`,
  `AGENTS.md`, `CLAUDE.md`, and `AGENT.md`.
- Runtime skill used:
  `~/.hermes/skills/software-development/ict-engine-maintenance-loop/SKILL.md`.

Current HEAD advanced again while resuming:

- `5d7b8717500ea9ef35c59db0bcec5950ac45a50b`
  (`Record closed-loop gate balance recheck`).
- Branch status:
  `main...origin/main [ahead 266]`.
- The worktree remains shared and dirty; preserve unrelated tracked and
  untracked files.

Fresh readbacks:

```bash
git status --short --branch
ps -axo pid,etime,command | rg "run_tomac|Auto-Quant|factor-research|done_definition_audit|smoke_acceptance" | rg -v rg
python3 support/scripts/factor_claim_terminalization_audit.py --compact --portable-paths --output /tmp/ict-engine-factor-closure-resume.json
python3 support/scripts/objective_closure_snapshot.py --compact --check-remotes --output-dir /tmp/ict-engine-consumer-ux-evidence-audit-resume
python3 support/scripts/factor_claim_terminalization_audit.py --compact --portable-paths --output /tmp/ict-engine-factor-closure-resume-2.json
```

Evidence:

- `/tmp/ict-engine-consumer-ux-evidence-audit-resume/objective_closure_snapshot.json`
  exited `1` with `summary.status=not_complete`, but it was for intermediate
  head `19771dc16d68eaf866526efe8175e5ff3a62be65`; it is now stale for
  current-head completion because HEAD advanced to `5d7b8717`.
- That stale parent packet still usefully confirms the same closure blockers:
  `done_definition_not_completion_ready`,
  `same_tree_practical_closure_unproven`, and `release_readiness_blocked`.
- Latest factor audit:
  `/tmp/ict-engine-factor-closure-resume-2.json`.
- Latest factor audit status:
  `summary.status=needs_attention`,
  `active_claims=1`, `fresh_active_claims_without_live_process=1`,
  `live_factor_processes=1`, `promotion_allowed_true=0`,
  `trade_usable_true=0`, and `same_tree_practical_closure=null`.
- Fresh active claim:
  `/tmp/ict-engine-agent-claims/board-b-factor-refinement/20260531T121851+0800-codex-ehlers-autocorr-periodogram-cycle-regime-30m-exact-aq.claim`.
  It claims
  `/tmp/ict-engine-ehlers-autocorr-periodogram-cycle-regime-exact-aq-20260531T121851+0800`
  with `promotion_allowed=false`, `trade_usable=false`,
  `update_goal=false`, and `same_tree_practical_closure=null`.
- Live TSMOM process remains under
  `/tmp/ict-engine-tomac-tsmom-vol-scaled-low-turnover-aq-20260531T115002+0800`.
  Latest observed pid was `11741`, running the same clean-AQ wrapper with
  `--reuse-clean --aq-smoke-timeframe 15m`.
- The TSMOM root has terminal fail-closed summaries for `1h`, `4h`, `1d`,
  and `30m`; `15m` was active at this checkpoint. Existing summaries keep
  `promotion_allowed=false`, `trade_usable=false`, `update_goal=false`, and
  `decision=observation_no_autoquant_survivor_yet`.
- Heavy done-definition audits and smoke commands were still visible in `ps`;
  do not treat skipped heavy gates as completion proof until their current
  artifacts are inspected and matched to the current head/fingerprint.

Decision: still not complete. Do not launch another AQ/provider lane. Do not
claim practical trade usability, release readiness, or objective completion.
The next safe action is to wait for the active AQ process and fresh Ehlers
claim to terminalize or become stale-safe, inspect their real artifacts, rerun
compact factor closure and a current-head objective snapshot, and only then
choose a narrow verified repair or commit slice.

## Current-Head Objective Snapshot - 2026-05-31T12:24+0800

Current-head parent packet:

- `/tmp/ict-engine-consumer-ux-evidence-audit-20260531T1224-current/objective_closure_snapshot.json`
- Exit code `1`.
- Head:
  `5d7b8717500ea9ef35c59db0bcec5950ac45a50b`
  (`Record closed-loop gate balance recheck`).
- `summary.status=not_complete`, `completion_proven=false`.
- Blockers:
  `done_definition_not_completion_ready`,
  `same_tree_practical_closure_unproven`, and
  `release_readiness_blocked`.

Done-definition child:

- `status=pass`, but `completion_ready=false`.
- `evidence_level=partial_skipped_gates`.
- `pass_count=6`, `fail_count=0`, `skip_count=4`, `total_gates=10`.
- Skipped heavy gates:
  `cargo_check_all_targets`, `cargo_clippy_all_targets_deny_warnings`,
  `cargo_test`, and `smoke_acceptance_tmp_state`.
- Tracked worktree fingerprint:
  `f74b0a541d8ef15d8dbe88cc915bf5f518f7321287cf41972aed20b87909c65e`,
  `status=dirty`, `tracked_status_entries=52`.

Factor closure child:

- `status=pass`.
- `active_claims=0`, `live_factor_processes=0`,
  `blocking_reasons=[]`.
- `promotion_allowed_true=0`, `trade_usable_true=0`,
  `same_tree_practical_closure=null`.
- This clears runtime collision as of the packet timestamp, but does not prove
  practical usefulness.

Runtime/artifact follow-up:

- `ps` after the snapshot showed no `run_tomac_index_futures_clean_aq_v1.py`
  process.
- The TSMOM root now has exit/gate artifacts for `1h`, `4h`, `1d`, `30m`,
  and `15m`; all observed gate summaries keep
  `promotion_allowed=false`, `trade_usable=false`, `update_goal=false`, and
  `decision=observation_no_autoquant_survivor_yet`.
- The same TSMOM root also wrote
  `/tmp/ict-engine-tomac-tsmom-vol-scaled-low-turnover-aq-20260531T115002+0800/summaries/terminal_no_launch_summary.json`
  from a later collision-guard rerun blocked by a foreign Kalman prep claim.
  It is not promotion or trade evidence.
- The Ehlers exact-AQ claim terminalized as
  `terminalized_no_launch_collision_guard`; no provider/AQ runtime launched,
  `promotion_allowed=false`, `trade_usable=false`, `update_goal=false`.
- The Kalman residual snapback claim terminalized as
  `terminalized_prepared_no_launch_exact_aqprep`; it produced prep materials
  only, with no provider/AQ/IBKR/paper/downstream launch.

Release-readiness child:

- `status=needs_fix`.
- Remote readback passed for origin and release mirror.
- Unresolved:
  `worktree_clean_for_release` and `source_origin_matches_selected_source`.

Concurrent no-launch audit claim:

- `/tmp/ict-engine-agent-claims/board-b-factor-refinement/20260531T122038+0800-codex-factor-training-loop-audit-cont.claim`
  is fresh and scoped to scanner coverage, practical-admission source checks,
  and fixed-bps/real-cost gate debt.
- Do not duplicate that audit-code lane unless it terminalizes or becomes
  stale-safe.

Decision: still not complete. The next safe non-colliding action is to monitor
the running heavy done-definition audits and smoke commands, inspect any
completed heavy packet against the current head/fingerprint, then rerun
`objective_closure_snapshot.py` with a valid proof only if the proof matches
the live child contract. Practical usefulness still requires a canonical
same-tree practical closure packet; none exists in the current factor audit.

## Live-Process Classifier Repair - 2026-05-31T04:20Z

Loophole found while waiting on the TSMOM root:

- `ps` showed a live
  `run_tomac_index_futures_clean_aq_v1.py --root /tmp/ict-engine-tomac-tsmom-vol-scaled-low-turnover-aq-20260531T115002+0800`
  process.
- The compact factor audit simultaneously reported
  `live_factor_processes=0` and `status=pass`.
- Root cause: the current working diff added clean-AQ terminal artifact
  suppression in `_drop_stale_failed_tomac_prep_wrappers`. That suppression
  dropped a process whenever the root already had terminal clean-AQ artifacts,
  even when the inferred exit file predated the current process and therefore
  belonged to an earlier run on the same root.

Fix:

- `_drop_stale_failed_tomac_prep_wrappers` now keeps a process when
  `_exit_file_predates_live_process(process)` is true.
- Regression added:
  `test_terminalized_clean_aq_root_keeps_newer_live_wrapper_process`.
- Existing stale-wrapper behavior remains covered by
  `test_drop_stale_failed_tomac_prep_wrappers_drops_terminalized_clean_aq_wrapper_without_descendants`.

Verification:

- Red before fix:
  `python3 -m unittest support.scripts.tests.test_factor_claim_terminalization_audit.FactorClaimTerminalizationAuditTest.test_terminalized_clean_aq_root_keeps_newer_live_wrapper_process -v`
  failed because the live wrapper was dropped.
- Passed after fix:
  `python3 -m unittest support.scripts.tests.test_factor_claim_terminalization_audit.FactorClaimTerminalizationAuditTest.test_terminalized_clean_aq_root_keeps_newer_live_wrapper_process support.scripts.tests.test_factor_claim_terminalization_audit.FactorClaimTerminalizationAuditTest.test_drop_stale_failed_tomac_prep_wrappers_drops_terminalized_clean_aq_wrapper_without_descendants -v`.
- Passed full classifier suite:
  `python3 -m unittest support.scripts.tests.test_factor_claim_terminalization_audit -v`
  (`122/122`).
- Live compact audit after the fix no longer hid the runtime. It returned
  `status=needs_attention`, `live_factor_processes=1`, queue head pid `11741`,
  run root
  `/tmp/ict-engine-tomac-tsmom-vol-scaled-low-turnover-aq-20260531T115002+0800`,
  `promotion_allowed_true=0`, `trade_usable_true=0`, and
  `same_tree_practical_closure=null`.

Decision: coherent classifier/evidence-loop repair, but the full objective is
still not complete. Current factor closure is intentionally blocked by the live
TSMOM runtime, same-tree practical closure is still absent, and release/done
definition gates still need separate current proof.

## Post-Classifier-Commit Parent Readback - 2026-05-31T04:24Z

Committed narrow classifier repair:

- Commit: `b48b12eb90dbb051339c703fc1dbb4e983059dde`
  (`Fix clean AQ live process classification`).
- Staged files were only:
  `support/scripts/factor_claim_terminalization_audit.py` and
  `support/scripts/tests/test_factor_claim_terminalization_audit.py`.
- The tracking doc was not staged because it contains concurrent continuation
  edits and should not be committed wholesale as part of the classifier slice.

Verification before commit:

- Passed:
  `python3 -m unittest support.scripts.tests.test_factor_claim_terminalization_audit -v`
  (`122/122`).
- Passed:
  `python3 support/scripts/check_script_manifest.py`.
- Passed:
  `python3 support/scripts/ci/check_docs_runtime_isolation.py`.
- Passed:
  `git diff --check -- support/scripts/factor_claim_terminalization_audit.py support/scripts/tests/test_factor_claim_terminalization_audit.py support/docs/plans/2026-05-31-consumer-ux-evidence-packet-audit-current.md`.

Fresh parent packet after commit:

```bash
python3 support/scripts/objective_closure_snapshot.py --compact --check-remotes --output-dir /tmp/ict-engine-consumer-ux-evidence-audit-20260531T1225-post-classifier-commit-codex
```

Result:

- Exit code `1`.
- Packet:
  `/tmp/ict-engine-consumer-ux-evidence-audit-20260531T1225-post-classifier-commit-codex/objective_closure_snapshot.json`.
- `summary.status=not_complete`, `completion_proven=false`.
- `factor_closure.status=pass`, `active_claims=0`,
  `live_factor_processes=0`, `blocking_reasons=[]`,
  `promotion_allowed_true=0`, `trade_usable_true=0`,
  `same_tree_practical_closure=null`.
- Remaining blockers:
  `done_definition_not_completion_ready`,
  `same_tree_practical_closure_unproven`, and
  `release_readiness_blocked`.
- Done definition remains `partial_skipped_gates` with skipped heavy gates
  `cargo_check_all_targets`, `cargo_clippy_all_targets_deny_warnings`,
  `cargo_test`, and `smoke_acceptance_tmp_state`.
- Practical closure is still missing the full provider/data, Pre-Bayes,
  BBN/workflow, path-ranker, execution-tree, feedback/update, and
  policy-training chain.
- Release readiness remains blocked by `worktree_clean_for_release` and
  `source_origin_matches_selected_source`; origin and release mirror remote
  readback passed in this packet.

Decision: classifier slice is committed and verified. Full objective remains
not complete; do not claim practical trading usefulness or release readiness.

## Latest Current-Head Packet - 2026-05-31T04:30Z

Current HEAD advanced after the classifier commit:

- `a74576265a7f06b332155c95aae497df93b6dded`
  (`docs: record balanced factor gate flywheel slice`).

Fresh parent packet:

```bash
python3 support/scripts/objective_closure_snapshot.py --compact --check-remotes --output-dir /tmp/ict-engine-consumer-ux-evidence-audit-20260531T1229-latest-codex
```

Result:

- Exit code `1`.
- Packet:
  `/tmp/ict-engine-consumer-ux-evidence-audit-20260531T1229-latest-codex/objective_closure_snapshot.json`.
- `summary.status=not_complete`, `completion_proven=false`.
- Current blockers:
  `done_definition_not_completion_ready`,
  `practical_admission_source_debt`,
  `factor_closure_blocked`,
  `same_tree_practical_closure_unproven`, and
  `release_readiness_blocked`.
- Done-definition status regressed from partial pass to `needs_fix` because
  `practical_admission_source_surface.status=fail`.
- New tracked practical-admission source debt:
  `3` violations in
  `support/docs/experiments/actionable-regime-confidence/scripts/run_tomac_index_futures_clean_aq_v1.py`
  at the `promotion_allowed`, `trade_usable`, and `update_goal` reads. The
  scanner reports `practical_flag_without_extension_complete_guard`.
- Factor closure is blocked by a fresh active claim without a live process:
  `20260531T122333+0800-codex-ehlers-autocorr-periodogram-cycle-regime-30m-exact-aq.claim`,
  age about `5` minutes at packet time, `promotion_allowed_true=0`,
  `trade_usable_true=0`, `same_tree_practical_closure=null`.
- Release readiness is blocked by `worktree_clean_for_release` and
  `remote_readback`; both origin and release mirror remote checks failed in
  this packet.

Decision: still not complete. The classifier commit is valid, but the current
head has a new practical-source debt surface plus a fresh active claim. Next
safe actions are to inspect/fix the tracked practical-flag guard violation,
wait for or verify the fresh Ehlers claim, then rerun compact factor closure and
the parent objective snapshot.

## Classifier Recheck - 2026-05-31T04:18Z

Current HEAD advanced again:

- `19771dc1169342c9ed7a45990e20f574ab715e8d`
  (`Require accepted execution feedback for policy lifecycle`).
- Branch status: `main...origin/main [ahead 265]`.

The transient concern that compact factor audit might miss an active clean-AQ
wrapper was rechecked against the live pid:

```bash
ps -p 98894 -o pid,ppid,etime,stat,command
python3 support/scripts/factor_claim_terminalization_audit.py --compact --output /tmp/ict-engine-factor-audit-repro-20260531T1218.json
jq '{summary, live: .attention_live_processes}' /tmp/ict-engine-factor-audit-repro-20260531T1218.json
```

Result:

- The live process was still present:
  `run_tomac_index_futures_clean_aq_v1.py --root /tmp/ict-engine-tomac-tsmom-vol-scaled-low-turnover-aq-20260531T115002+0800 ... --aq-smoke-timeframe 30m --timeout 1200`.
- The focused repro correctly returned exit `1`,
  `summary.status=needs_attention`,
  `live_factor_processes=1`,
  `blocking_reasons=[live_factor_processes]`,
  and `same_tree_practical_closure=null`.
- Therefore the current actionable blocker remains real runtime occupancy, not
  a reproduced classifier miss.

Heavy proof status:

- Both current heavy done-definition audits are still running and have not
  written reusable JSON proof:
  `/tmp/ict-engine-done-definition-heavy-20260531T-after-source-scope-commit.json`
  and `/tmp/ict-engine-done-definition-heavy-20260531T-current-turn.json`.

Decision: still not complete. Next action remains read-only wait and then
rerun compact factor audit plus parent objective snapshot after pid `98894` and
the heavy audits exit.

## Readback Poller Classifier Fix - 2026-05-31T12:33+0800

Current repo state advanced again during this slice:

- HEAD: `5d7b8717500ea9ef35c59db0bcec5950ac45a50b`
  (`Record closed-loop gate balance recheck`).
- Branch status observed: `main...origin/main [ahead 269]`.
- Shared worktree remains dirty; stage only the explicit classifier slice paths.

Symptom:

- A compact factor audit briefly surfaced `live_factor_processes=1` for a
  shell readback poller whose command shape was `sleep; ps -p ...; ps -axo ...
  | awk ...; for f in .../*.exit; python3 - <<'PY' ...`.
- That command only inspected a TOMAC root and exit files; it was not a
  provider/AQ/factor writer.

Root cause:

- `_looks_like_readback_command()` intentionally avoided suppressing commands
  containing `python` so live Python wrappers would not be hidden.
- That guard was too broad for readback pollers that use `python3 - <<...` or
  similar inline Python only to parse local files. The final fallback marker
  check then saw `run_tomac` in the exit-file path and counted the shell as a
  live factor process.

Fix:

- Added `_has_python_script_invocation()` so readback suppression remains
  disabled for real Python `.py` script invocations, but still applies to
  shell-only readback pollers using inline Python.
- Regression added:
  `test_live_process_classifier_ignores_ps_awk_exit_file_readback_poller`.

TDD evidence:

- RED before production fix:
  `python3 -m unittest support.scripts.tests.test_factor_claim_terminalization_audit.FactorClaimTerminalizationAuditTest.test_live_process_classifier_ignores_ps_awk_exit_file_readback_poller -v`
  failed with `AssertionError: True is not false`.
- Focused GREEN after fix:
  `python3 -m unittest support.scripts.tests.test_factor_claim_terminalization_audit.FactorClaimTerminalizationAuditTest.test_live_process_classifier_ignores_ps_awk_exit_file_readback_poller support.scripts.tests.test_factor_claim_terminalization_audit.FactorClaimTerminalizationAuditTest.test_live_process_classifier_ignores_ps_escaped_shell_readback_poller support.scripts.tests.test_factor_claim_terminalization_audit.FactorClaimTerminalizationAuditTest.test_live_process_classifier_detects_custom_tomac_scanner_and_lane_root support.scripts.tests.test_factor_claim_terminalization_audit.FactorClaimTerminalizationAuditTest.test_live_process_classifier_detects_custom_tomac_postscan_and_lane_root -v`
  passed.
- Full classifier suite:
  `python3 -m unittest support.scripts.tests.test_factor_claim_terminalization_audit -v`
  passed (`123/123`).
- Script inventory:
  `python3 support/scripts/check_script_manifest.py` passed.
- Docs/runtime isolation:
  `python3 support/scripts/ci/check_docs_runtime_isolation.py` passed.
- Whitespace:
  `git diff --check -- support/scripts/factor_claim_terminalization_audit.py support/scripts/tests/test_factor_claim_terminalization_audit.py support/docs/plans/2026-05-31-consumer-ux-evidence-packet-audit-current.md`
  passed.

Current compact factor audit after the fix:

```bash
python3 support/scripts/factor_claim_terminalization_audit.py --compact --output /tmp/ict-engine-factor-closure-after-ps-awk-readback-fix-20260531T0428Z.json
```

Result:

- Exit code `1` because factor closure is still blocked.
- `summary.status=needs_attention`.
- `live_factor_processes=0`; the readback-poller false live owner is gone.
- `active_claims=1`, `fresh_active_claims_without_live_process=1`.
- Blocking claim:
  `/tmp/ict-engine-agent-claims/board-b-factor-refinement/20260531T122333+0800-codex-ehlers-autocorr-periodogram-cycle-regime-30m-exact-aq.claim`.
- Claim age was about `8` minutes at audit time, with
  `promotion_allowed=false`, `trade_usable=false`, and
  `same_tree_practical_closure=null`.

Heavy done-definition status:

- Older heavy packet exists but is stale-head and failing:
  `/tmp/ict-engine-done-definition-heavy-20260531T-after-source-scope-commit.json`.
  It selected head `4126d761f94d7d68228c5bda4f90534db907ac45`,
  `completion_ready=false`, `status=needs_fix`, and unresolved
  `smoke_acceptance_tmp_state`.
- Newer isolated heavy audit is still running:
  `/tmp/ict-engine-done-definition-heavy-20260531T-codex-closedloop-reverify-isolated.json`.
  Do not start another heavy audit until this exits or becomes stale.

Decision: this is a coherent live-process/readback classifier repair, but the
full objective is still not complete. Current blockers remain a fresh active
Ehlers claim without live process, stale or in-flight done-definition proof,
same-tree practical closure missing, and release readiness blocked by dirty
worktree/remote readback. The active `ict-engine-maintenance-loop` skill already
warned that command-introspection and TOMAC diagnostic probes must not count as
live factor owners; the runtime skill was tightened in the later 04:31Z
readback section to name ps/awk pollers and exit-file Python-heredoc readbacks
explicitly.

## Readback Poller Classifier Repair - 2026-05-31T04:31Z

Current head during repair:

- `a74576265a7f06b332155c95aae497df93b6dded`
  (`docs: record balanced factor gate flywheel slice`).

Bug:

- A shell readback poller that combined `ps -p`, `ps -axo | awk`, exit-file
  `cat`, and a Python heredoc reading `checks/run_tomac_*.exit` was still
  classified as a live factor process because the command mentioned
  `/tmp/ict-engine-.../run_tomac_1h.exit`.

Fix:

- `support/scripts/factor_claim_terminalization_audit.py` now treats ps/readback
  shells as non-live unless they invoke a real Python factor runtime script.
- Regression added:
  `test_live_process_classifier_ignores_ps_awk_exit_file_readback_poller`.

Verification:

- RED:
  `python3 -m unittest support.scripts.tests.test_factor_claim_terminalization_audit.FactorClaimTerminalizationAuditTest.test_live_process_classifier_ignores_ps_awk_exit_file_readback_poller support.scripts.tests.test_factor_claim_terminalization_audit.FactorClaimTerminalizationAuditTest.test_terminalized_clean_aq_root_keeps_newer_live_wrapper_process -v`
  initially failed on the readback-poller test.
- GREEN focused:
  same command passed after the classifier fix.
- GREEN full suite:
  `python3 -m unittest support.scripts.tests.test_factor_claim_terminalization_audit -v`
  passed `123/123`.
- Live compact audit:
  `python3 support/scripts/factor_claim_terminalization_audit.py --compact --output /tmp/ict-engine-factor-audit-readback-poller-fix-20260531T1229.json`
  exited nonzero only because factor closure still needs attention. The packet
  reported `live_factor_processes=0`, `active_claims=1`,
  `fresh_active_claims_without_live_process=1`, `promotion_allowed_true=0`,
  `trade_usable_true=0`, and `same_tree_practical_closure=null`.

Skill update:

- Runtime maintenance skill updated at
  `/Users/thrill3r/.hermes/skills/software-development/ict-engine-maintenance-loop/SKILL.md`
  to include ps/awk process pollers and exit-file cat/Python-heredoc readbacks
  as non-live command-introspection probes.

## Post-Commit Classifier Readback - 2026-05-31T12:41+0800

The classifier code/test slice was committed while this continuation was
waiting on the heavy done-definition process:

- Commit: `3cff898db8b943588cc9d9044c7f31b79d145f81`
  (`Fix readback poller live-process classification`).
- Files in that commit:
  `support/scripts/factor_claim_terminalization_audit.py` and
  `support/scripts/tests/test_factor_claim_terminalization_audit.py`.

Heavy done-definition packet that was running in parallel completed:

- Path:
  `/tmp/ict-engine-done-definition-heavy-20260531T-codex-closedloop-reverify-isolated.json`.
- Selected head:
  `3cff898db8b943588cc9d9044c7f31b79d145f81`.
- `summary.status=needs_fix`, `completion_ready=false`,
  `evidence_level=failing_gates`.
- Gate counts:
  `pass_count=9`, `fail_count=1`, `skip_count=0`, `total_gates=10`.
- Unresolved gate:
  `smoke_acceptance_tmp_state`.
- Tracked worktree fingerprint:
  `sha256=d3f0606777a144930616cfcbee14d496368fbca10fbda67be72305c3218f0e2f`,
  `status=dirty`, `tracked_status_entries=55`.

Current factor closure after the classifier commit:

```bash
python3 support/scripts/factor_claim_terminalization_audit.py --compact --output /tmp/ict-engine-factor-closure-post-3cff-20260531T1241Z.json
```

Result:

- Exit code `1`.
- `summary.status=needs_attention`.
- `live_factor_processes=0`.
- `active_claims=1`, `fresh_active_claims_without_live_process=1`.
- Fresh blocker remains
  `20260531T122333+0800-codex-ehlers-autocorr-periodogram-cycle-regime-30m-exact-aq.claim`,
  age about `17` minutes at readback time.
- `promotion_allowed_true=0`, `trade_usable_true=0`,
  `same_tree_practical_closure=null`.

Decision: classifier false-live behavior is repaired on the committed head, but
the full objective remains blocked by the fresh Ehlers active claim,
`smoke_acceptance_tmp_state`, missing same-tree practical closure, and release
readiness. Do not take over the Ehlers claim until it is stale-safe or terminal
evidence appears.

Decision: coherent classifier false-positive repair. Full objective remains not
complete because Ehlers has a fresh active claim without live runtime,
same-tree practical closure is still absent, done-definition proof remains
blocked, and release readiness is still blocked by dirty/source/remote surfaces
in the current packets.

## Post-Commit Objective Snapshot - 2026-05-31T04:38Z

Committed slice:

- `3cff898db8b943588cc9d9044c7f31b79d145f81`
  (`Fix readback poller live-process classification`).

Fresh packet:

```bash
python3 support/scripts/objective_closure_snapshot.py --compact --check-remotes --output-dir /tmp/ict-engine-consumer-ux-evidence-audit-20260531T1235-post-readback-poller-commit-codex
```

Result:

- Exit code `1`.
- Packet:
  `/tmp/ict-engine-consumer-ux-evidence-audit-20260531T1235-post-readback-poller-commit-codex/objective_closure_snapshot.json`.
- `summary.status=not_complete`, `completion_proven=false`.
- `done_definition.head=3cff898db8b943588cc9d9044c7f31b79d145f81`.
- `done_definition.status=pass`, but `completion_ready=false` because heavy
  gates are still skipped: `cargo_check_all_targets`,
  `cargo_clippy_all_targets_deny_warnings`, `cargo_test`, and
  `smoke_acceptance_tmp_state`.
- `practical_admission_source_surface.status=pass` with zero tracked and
  untracked practical-admission violations.
- Objective blockers:
  `done_definition_not_completion_ready`,
  `fixed_bps_cost_model_source_debt`,
  `factor_closure_blocked`,
  `same_tree_practical_closure_unproven`, and
  `release_readiness_blocked`.
- Fixed-bps cost-model source debt is untracked-only in this packet:
  `untracked_violation_count=1790` across `322` untracked files, staged into
  `fixed_bps_cost_model_source_debt_manifest.json`.
- Factor closure remains blocked by the fresh Ehlers active claim:
  `live_factor_processes=0`, `active_claims=1`,
  `fresh_active_claims_without_live_process=1`, `promotion_allowed_true=0`,
  `trade_usable_true=0`, `same_tree_practical_closure=null`.
- Release readiness remote readback passed for origin and release mirror, but
  release still blocks on `worktree_clean_for_release` and
  `source_origin_matches_selected_source`.

Decision: commit `3cff898d` is a verified classifier slice only. It is not
completion evidence, not practical trade-use evidence, and not release
readiness.

## Continuation Readback - 2026-05-31T13:06+0800

Current HEAD during this readback:

- `57017b7816b12d843c081cbddda8c43e3ab2ef91`
  (`docs: record final balanced gate audit state`).

Fresh lightweight done-definition audit:

```bash
python3 support/scripts/done_definition_audit.py --compact --output /tmp/ict-engine-done-definition-current-light-20260531T-continuation.json
```

Result:

- Exit code `0`.
- `summary.status=pass`, but `completion_ready=false` and
  `evidence_level=partial_skipped_gates`.
- Skipped heavy gates remain:
  `cargo_check_all_targets`, `cargo_clippy_all_targets_deny_warnings`,
  `cargo_test`, and `smoke_acceptance_tmp_state`.
- `practical_admission_source_surface.status=pass` with
  `tracked_violation_count=0`.
- `fixed_bps_cost_model_source_surface.status=pass` with
  `tracked_violation_count=0`; the active untracked debt is quarantined by
  `support/docs/audits/fixed-bps-cost-model-source-debt-quarantine.json`.
- `await_launch_source_surface.status=pass`; the active untracked await-launch
  debt remains quarantined by
  `support/docs/audits/await-launch-source-debt-quarantine.json`.

Fresh parent objective snapshot:

```bash
python3 support/scripts/objective_closure_snapshot.py --compact --check-remotes --output-dir /tmp/ict-engine-consumer-ux-evidence-audit-20260531T-current-continuation-fresh
```

Result:

- Exit code `1`.
- `summary.status=not_complete`, `completion_proven=false`.
- Current blockers:
  `done_definition_not_completion_ready`,
  `factor_closure_blocked`,
  `same_tree_practical_closure_unproven`, and
  `release_readiness_blocked`.
- The old `fixed_bps_cost_model_source_debt` blocker is not current; it is now
  preserved as `quarantined_fixed_bps_cost_model_source_debt` with
  `1790` untracked violations across `322` active untracked experiment scripts
  and zero tracked violations.
- The factor blocker in this parent packet was time-variant: a focused factor
  audit immediately after the packet reported no active claims and no live
  processes, but later a real AQ/TOMAC process appeared. Treat parent factor
  closure as a live readback surface, not durable completion proof.

Live-process/action-queue packet cooperation repair:

- Current working tree already contained classifier fixes that ignore
  zero-config smoke children such as `ict-engine analyze --demo` and
  `workflow-status --symbol DEMO` under
  `/tmp/ict-engine-done-definition-audit-smoke-*`.
- The compact factor action queue now preserves `command_excerpt` for
  `live_runtime_run_roots`, so a parent/objective packet can show what live
  runtime is occupying the lane without opening the child audit.
- I added parent snapshot regression coverage so
  `factor_closure_blocked.action_queue.live_runtime_run_roots[*].command_excerpt`
  remains part of the reusable blocker detail.
- Runtime maintenance skill updated:
  `/Users/thrill3r/.hermes/skills/software-development/ict-engine-maintenance-loop/SKILL.md`
  now records that zero-config smoke children are not factor owners and that
  compact factor queues should preserve command excerpts.

Verification:

- Passed:
  `python3 -m unittest support.scripts.tests.test_factor_claim_terminalization_audit -v`
  (`126/126`).
- Passed:
  `python3 -m unittest support.scripts.tests.test_objective_closure_snapshot -v`
  (`48/48`).
- Passed:
  `python3 support/scripts/check_script_manifest.py`.
- Passed:
  `python3 support/scripts/ci/check_docs_runtime_isolation.py`.
- Passed:
  `git diff --check -- support/scripts/factor_claim_terminalization_audit.py support/scripts/tests/test_factor_claim_terminalization_audit.py support/scripts/tests/test_objective_closure_snapshot.py support/docs/plans/2026-05-31-consumer-ux-evidence-packet-audit-current.md`.

Current focused factor audit after the action-queue/readback repair:

```bash
python3 support/scripts/factor_claim_terminalization_audit.py --compact --output /tmp/ict-engine-factor-closure-current-command-excerpt-20260531T-continuation.json
```

Result:

- Exit code `1`.
- `summary.status=needs_attention`.
- `active_claims=0`, `promotion_allowed_true=0`, `trade_usable_true=0`,
  `same_tree_practical_closure=null`.
- `live_factor_processes=1`, currently a real AQ/TOMAC runtime, not a smoke
  false positive.
- The action queue now includes the live command excerpt:
  `run_tomac_index_futures_clean_aq_v1.py --root ...` for run root
  `/tmp/ict-engine-tomac-tsmom-vol-scaled-low-turnover-aq-20260531T115002+0800`.

Concurrent state observed:

- Other sessions were running heavy done-definition audits:
  `/tmp/ict-engine-done-definition-heavy-20260531T-post-smoke-pass.json` and
  `/tmp/ict-engine-done-definition-heavy-20260531T-codex-closedloop-final.json`.
  Do not start another heavy audit until those exit or are proven stale.
- A real AQ process was active under a Board B `/tmp/ict-engine-*` root. Do not
  terminalize or claim factor closure while that process is live.

Decision: still not complete. The current slice improves evidence-packet
cooperation and makes live factor blockers more reusable/actionable, but the
full objective still lacks heavy done-definition proof, same-tree practical
closure, factor runtime clearance, clean release readiness, and a final
coherent completion commit.

## Heavy Proof And Proof-Reuse Readback - 2026-05-31T05:02Z

Current HEAD moved while the heavy audit was running:

- `a1ac23c8d34f0369ed810f9be80e441dcce2f86e`
  (`Balance fixed-bps source debt gates`).

Heavy done-definition packet:

- `/tmp/ict-engine-done-definition-heavy-20260531T-post-smoke-pass.json`.
- Exit code `0`.
- `summary.status=pass`, `completion_ready=true`,
  `evidence_level=full_enabled_gate_coverage`.
- `pass_count=11`, `fail_count=0`, `skip_count=0`.
- Heavy gates passed:
  `cargo_check_all_targets`, `cargo_clippy_all_targets_deny_warnings`,
  `cargo_test`, and `smoke_acceptance_tmp_state`.
- Manual smoke repro also passed earlier at
  `/tmp/ict-engine-smoke-acceptance-20260531T044023Z/smoke-output`.

Proof reuse attempt:

```bash
python3 support/scripts/objective_closure_snapshot.py --compact --check-remotes --done-definition-proof /tmp/ict-engine-done-definition-heavy-20260531T-post-smoke-pass.json --output-dir /tmp/ict-engine-consumer-ux-evidence-audit-20260531T1302-proof-reuse-codex
```

Result:

- Exit code `1`.
- Packet:
  `/tmp/ict-engine-consumer-ux-evidence-audit-20260531T1302-proof-reuse-codex/objective_closure_snapshot.json`.
- `summary.status=not_complete`.
- The heavy proof was rejected with
  `proof_rejected_reason=proof_worktree_fingerprint_mismatch`.
- Parent snapshot child done-definition surface had fingerprint
  `04ab2a799a05a9825158605e454d602df03afd9b09053bb4bbab5e2db9120bf6`;
  heavy proof had fingerprint
  `8cab6d4d786ebe7f88432e597b33295c12fecf08aebb16e77a804004fa4e99f1`.

Current objective blockers in that packet:

- `done_definition_not_completion_ready` because proof reuse rejected.
- `factor_closure_blocked` from live TSMOM runtime pid `80783` under
  `ict-engine-tomac-tsmom-vol-scaled-low-turnover-aq-20260531T115002+0800`.
- `same_tree_practical_closure_unproven`.
- `release_readiness_blocked` with remote readback passing, but
  `worktree_clean_for_release` and `source_origin_matches_selected_source`
  unresolved.
- Await-launch and fixed-bps cost-model source debt are quarantined in this
  packet, not completion or trade-use evidence.

Decision: the heavy gate run is valuable but cannot be used as current parent
proof until the tracked worktree fingerprint stabilizes or a new matching heavy
packet is generated. Do not claim completion or release readiness.

## Demo Smoke Classifier And Action-Queue Readback Fix - 2026-05-31T13:02+0800

Current HEAD while repairing:

- `a1ac23c8d34f0369ed810f9be80e441dcce2f86e`
  (`Balance fixed-bps source debt gates`).

Loopholes found:

- A parent objective snapshot briefly reported `factor_closure_blocked` from
  a done-definition smoke child:
  `.local-artifacts/cargo-target/debug/ict-engine workflow-status --symbol DEMO
  --state-dir ...ict-engine-done-definition-audit-smoke...`.
  This is zero-config consumer smoke/readback, not a Board B provider/AQ factor
  owner.
- Compact `attention_action_queue.live_runtime_run_roots` preserved pid, root,
  and exit state but omitted the short `command_excerpt`, making parent packets
  less actionable than `attention_live_processes`.

Fix:

- `support/scripts/factor_claim_terminalization_audit.py` now excludes direct
  `ict-engine` zero-config smoke commands from live factor ownership when the
  command has `--demo`, `--symbol DEMO`, or smoke state markers
  `ict-engine-done-definition-audit-smoke`, `ict-engine-smoke-acceptance`, or
  `ict-engine-first-run`.
- The compact factor action queue now keeps `command_excerpt` for live runtime
  queue heads.
- Runtime maintenance skill was updated at
  `/Users/thrill3r/.hermes/skills/software-development/ict-engine-maintenance-loop/SKILL.md`
  so future classifier work treats zero-config demo smoke children as non-live
  factor owners.

Verification:

- Passed focused classifier tests:
  `python3 -m unittest support.scripts.tests.test_factor_claim_terminalization_audit.FactorClaimTerminalizationAuditTest.test_live_process_classifier_ignores_demo_workflow_status_smoke_child support.scripts.tests.test_factor_claim_terminalization_audit.FactorClaimTerminalizationAuditTest.test_live_process_classifier_ignores_demo_analyze_smoke_state support.scripts.tests.test_factor_claim_terminalization_audit.FactorClaimTerminalizationAuditTest.test_live_process_classifier_detects_direct_ict_engine_board_b_cli_child -v`.
- Passed full classifier suite:
  `python3 -m unittest support.scripts.tests.test_factor_claim_terminalization_audit -v`
  (`126/126`).
- Passed:
  `python3 support/scripts/check_script_manifest.py`.
- Passed:
  `python3 support/scripts/ci/check_docs_runtime_isolation.py`.
- Passed:
  `python3 -m py_compile support/scripts/factor_claim_terminalization_audit.py support/scripts/tests/test_factor_claim_terminalization_audit.py`.
- Passed:
  `git diff --check -- support/scripts/factor_claim_terminalization_audit.py support/scripts/tests/test_factor_claim_terminalization_audit.py support/docs/plans/2026-05-31-consumer-ux-evidence-packet-audit-current.md`.
- Direct compact factor audit after the fix:
  `/tmp/ict-engine-factor-closure-after-demo-smoke-classifier-fix-20260531T1300.json`
  exited `1` because factor closure is still blocked by a real live process,
  not by smoke misclassification. It reported `live_factor_processes=1`,
  `active_claims=0`, `promotion_allowed_true=0`, `trade_usable_true=0`,
  and `same_tree_practical_closure=null`. The action queue now carries
  `command_excerpt` for pid `80783` under
  `/tmp/ict-engine-tomac-tsmom-vol-scaled-low-turnover-aq-20260531T115002+0800`.

Current-head parent packet:

```bash
python3 support/scripts/objective_closure_snapshot.py --compact --check-remotes --timeout-seconds 180 --output-dir /tmp/ict-engine-consumer-ux-evidence-audit-20260531T1301-demo-smoke-classifier-fix-codex
```

Result:

- Exit code `1`.
- Packet:
  `/tmp/ict-engine-consumer-ux-evidence-audit-20260531T1301-demo-smoke-classifier-fix-codex/objective_closure_snapshot.json`.
- `summary.status=not_complete`, `completion_proven=false`.
- Blockers:
  `done_definition_not_completion_ready`,
  `factor_closure_blocked`,
  `same_tree_practical_closure_unproven`, and
  `release_readiness_blocked`.
- Done-definition child is `status=pass`, but `completion_ready=false` because
  heavy gates are skipped:
  `cargo_check_all_targets`, `cargo_clippy_all_targets_deny_warnings`,
  `cargo_test`, and `smoke_acceptance_tmp_state`.
- Factor closure is blocked by a real live TSMOM clean-AQ runtime:
  pid `80783`, root
  `ict-engine-tomac-tsmom-vol-scaled-low-turnover-aq-20260531T115002+0800`,
  `exit_file_state=present`, with `command_excerpt` preserved in the parent
  action queue.
- Same-tree practical closure is still absent:
  `promotion_allowed_true=0`, `trade_usable_true=0`,
  `same_tree_practical_closure=null`; missing stages remain provider/data,
  Pre-Bayes, BBN/workflow, path-ranker, execution-tree, feedback/update, and
  policy-training.
- Release readiness remote readback passed for origin and release mirror, but
  `worktree_clean_for_release` and `source_origin_matches_selected_source`
  remain unresolved.

Decision: this is a coherent classifier/readback repair only. The full
objective remains not complete. Do not launch another AQ/provider lane while
the TSMOM runtime is live, and do not claim practical trade usefulness or
release readiness from this packet.

## Current Resume Readback - 2026-05-31T12:59+0800

Routing was repeated before this continuation:

- Route alias: `sd/ict-engine-maintenance-loop`.
- Files read:
  `~/.hermes/routing/skill-router.md`,
  `~/.hermes/routing/project-router.md`, repo `AGENTS.md`, `CLAUDE.md`,
  and `AGENT.md`.
- Runtime skill used:
  `~/.hermes/skills/software-development/ict-engine-maintenance-loop/SKILL.md`.

Current HEAD:

- `1606cb73163a3e2cdb7a49d5f952c66bf44ab8f4`
  (`Balance fixed-bps source debt gates`).
- Branch status observed during the continuation:
  `main...origin/main [ahead 276]`.
- The shared worktree remains dirty. Do not broad-stage or commit a completion
  slice from this state.

Fresh current-head parent packet after the ETH calendar-guard AQ runtime
terminalized fail-closed:

```bash
python3 support/scripts/objective_closure_snapshot.py --compact --check-remotes --output-dir /tmp/ict-engine-consumer-ux-evidence-audit-20260531T-after-eth-terminal-codex --timeout-seconds 180
```

Result:

- Exit code `1`.
- Packet:
  `/tmp/ict-engine-consumer-ux-evidence-audit-20260531T-after-eth-terminal-codex/objective_closure_snapshot.json`.
- `summary.status=not_complete`, `completion_proven=false`.
- Blockers:
  `done_definition_not_completion_ready`,
  `same_tree_practical_closure_unproven`, and
  `release_readiness_blocked`.
- `done_definition.status=pass`, but `completion_ready=false` because heavy
  gates were skipped in the light child:
  `cargo_check_all_targets`, `cargo_clippy_all_targets_deny_warnings`,
  `cargo_test`, and `smoke_acceptance_tmp_state`.
- `factor_closure.status=pass`, `active_claims=0`,
  `live_factor_processes=0`, `promotion_allowed_true=0`,
  `trade_usable_true=0`, and `same_tree_practical_closure=null`.
- Fixed-bps source debt is no longer an objective blocker in this packet:
  tracked violations are `0`; untracked fixed-bps debt remains quarantined
  and staged as `fixed_bps_cost_model_source_debt_manifest.json`
  (`1790` violations across `322` untracked files).
- Await-launch untracked debt also remains quarantined and visible
  (`46` violations across `46` untracked files).
- Release readiness remote readback passed for origin and release mirror, but
  release remains blocked by `worktree_clean_for_release` and
  `source_origin_matches_selected_source`.

Heavy done-definition packet that finished in parallel:

- Path:
  `/tmp/ict-engine-done-definition-heavy-20260531T-codex-closedloop-final.json`.
- Head:
  `1606cb73163a3e2cdb7a49d5f952c66bf44ab8f4`.
- Summary:
  `completion_ready=true`, `status=pass`, `pass_count=11`,
  `fail_count=0`, `skip_count=0`.
- The heavy packet proves all enabled done-definition gates for its recorded
  dirty-worktree fingerprint
  `64d2211f7f5be61907b3f8ccb05384d5afaa921fa0e553fa223a5f9d35b3891c`.

Proof-reuse attempt:

```bash
python3 support/scripts/objective_closure_snapshot.py --compact --check-remotes --done-definition-proof /tmp/ict-engine-done-definition-heavy-20260531T-codex-closedloop-final.json --output-dir /tmp/ict-engine-consumer-ux-evidence-audit-20260531T-with-heavy-proof-codex --timeout-seconds 180
```

Result:

- Exit code `1`.
- Packet:
  `/tmp/ict-engine-consumer-ux-evidence-audit-20260531T-with-heavy-proof-codex/objective_closure_snapshot.json`.
- The heavy proof was correctly rejected:
  `proof_rejected_reason=proof_worktree_fingerprint_mismatch`.
- Current light child fingerprint had drifted to
  `b883f51339bcce1129ce34594a3a2843cfe9e306d4761c05a9f93428b2f62271`.
- At the same time, a new live TSMOM 5m clean-AQ process appeared:
  pid `80783`, run root
  `/tmp/ict-engine-tomac-tsmom-vol-scaled-low-turnover-aq-20260531T115002+0800`.
- Therefore the proof-reuse packet still blocks on:
  `done_definition_not_completion_ready`,
  `factor_closure_blocked`,
  `same_tree_practical_closure_unproven`, and
  `release_readiness_blocked`.

Current process state during this checkpoint:

- Still running:
  `/tmp/ict-engine-done-definition-heavy-20260531T-post-smoke-pass.json`
  producer, with child `cargo test`.
- Still running:
  TSMOM 5m clean-AQ wrapper under
  `/tmp/ict-engine-tomac-tsmom-vol-scaled-low-turnover-aq-20260531T115002+0800`.
- Still running:
  a focused `cargo test -q --lib profitability_admission -- --nocapture`.

Decision: still not complete. The heavy proof is valuable, but it cannot clear
the current parent done-definition blocker after tracked-worktree fingerprint
drift. The current safe next action is to wait for the active TSMOM 5m runtime
and the remaining heavy proof to finish, inspect their real artifacts, then
rerun a compact factor audit and parent objective snapshot. Do not claim
practical trade usability: there is still no validated same-tree practical
closure packet, and `promotion_allowed_true=0` / `trade_usable_true=0` remain
the current factor readback.

## Proof Reuse Drift - 2026-05-31T13:04+0800

Current HEAD advanced again during proof reuse:

- `43b765d7d3b9bb6bf51317580eb031fbfa1a244e`
  (`Fix demo smoke factor closure classification`).

The `post-smoke-pass` heavy packet remains useful historical evidence:

- `/tmp/ict-engine-done-definition-heavy-20260531T-post-smoke-pass.json`
- Head: `a1ac23c8d34f0369ed810f9be80e441dcce2f86e`.
- Summary: `completion_ready=true`, `pass_count=11`, `fail_count=0`,
  `skip_count=0`.

But the current parent proof reuse correctly rejected it after HEAD advanced:

```bash
python3 support/scripts/objective_closure_snapshot.py --compact --check-remotes --done-definition-proof /tmp/ict-engine-done-definition-heavy-20260531T-post-smoke-pass.json --output-dir /tmp/ict-engine-consumer-ux-evidence-audit-20260531T-with-post-smoke-proof-codex --timeout-seconds 180
```

Result:

- Exit code `1`.
- Packet:
  `/tmp/ict-engine-consumer-ux-evidence-audit-20260531T-with-post-smoke-proof-codex/objective_closure_snapshot.json`.
- `summary.status=not_complete`.
- `proof_rejected_reason=proof_head_mismatch`.
- Current blockers in that packet:
  `done_definition_not_completion_ready`,
  `factor_closure_blocked`,
  `same_tree_practical_closure_unproven`, and
  `release_readiness_blocked`.
- Factor closure remained blocked by the TSMOM 5m clean-AQ runtime under
  `/tmp/ict-engine-tomac-tsmom-vol-scaled-low-turnover-aq-20260531T115002+0800`.
- At this checkpoint, `pgrep` still showed pid `85785` running the same 5m
  wrapper. Do not start another overlapping factor lane.

Decision: stop chasing moving HEAD in this shared worktree. The next agent
should first wait for the TSMOM 5m runtime to exit and then rerun current-head
factor closure plus objective snapshot. A fresh heavy proof must match the
current `HEAD` and tracked-worktree fingerprint before it can clear
`done_definition_not_completion_ready`.

## Current-Head Refresh - 2026-05-31T04:53Z

Current HEAD:

- `33bf1fc8cb0dc3d0b7254ab287d7d46909f4c4c1`
  (`Fix material prep claim classification`).

Fresh factor closure:

```bash
python3 support/scripts/factor_claim_terminalization_audit.py --compact --portable-paths --output /tmp/ict-engine-factor-closure-resume-5.json
```

Result:

- `summary.status=pass`.
- `active_claims=0`, `live_factor_processes=0`,
  `blocking_reasons=[]`.
- `promotion_allowed_true=0`, `trade_usable_true=0`,
  `same_tree_practical_closure=null`.

Smoke-only wrapper recheck:

```bash
python3 support/scripts/done_definition_audit.py --compact --run-smoke --heavy-timeout-seconds 1200 --output /tmp/ict-engine-done-definition-smoke-only-20260531T1245.json
```

Result:

- Exit code `0`.
- `smoke_acceptance_tmp_state=pass`.
- Because this used `--run-smoke` only, cargo check, clippy, and test were
  skipped; it cannot serve as full done-definition completion proof.
- The earlier full-heavy packet for `3cff898d` failed smoke with
  `/Users/thrill3r/projects-ict-engine/ict-engine/support/scripts/smoke_acceptance.sh: line 59: engine: command not found`,
  while a direct current smoke run also passed at
  `/tmp/ict-engine-smoke-acceptance-20260531T044442Z/smoke-output`.
  Current evidence points to shared-worktree/head drift during long heavy runs,
  not a stable current smoke script failure.

Fresh parent snapshot:

```bash
python3 support/scripts/objective_closure_snapshot.py --compact --check-remotes --timeout-seconds 300 --output-dir /tmp/ict-engine-consumer-ux-evidence-audit-20260531T1251-current-head
```

Result:

- Exit code `1`.
- Packet:
  `/tmp/ict-engine-consumer-ux-evidence-audit-20260531T1251-current-head/objective_closure_snapshot.json`.
- `summary.status=not_complete`, `completion_proven=false`.
- `done_definition.head=33bf1fc8cb0dc3d0b7254ab287d7d46909f4c4c1`.
- `done_definition.status=pass`, but `completion_ready=false` because heavy
  gates are skipped in the light child:
  `cargo_check_all_targets`, `cargo_clippy_all_targets_deny_warnings`,
  `cargo_test`, and `smoke_acceptance_tmp_state`.
- `factor_closure.status=pass`, with no active or live runtime blockers.
- `release_readiness.status=needs_fix`; origin and release mirror remote
  readback passed, but `worktree_clean_for_release` and
  `source_origin_matches_selected_source` remain unresolved.
- `same_tree_practical_closure=null`; missing stages remain provider/data,
  Pre-Bayes, BBN/workflow, path-ranker, execution-tree, feedback/update, and
  policy-training.
- Fixed-bps debt is quarantined untracked-only:
  `1790` violations across `322` untracked files, with no tracked violations.

Decision: still not complete. The current factor side is clear, and current
smoke can pass, but there is no same-tree practical closure packet, no
same-head full-heavy proof, and no release-ready clean/source-aligned state. Do
not commit completion or claim practical trade usefulness.

## Demo Smoke Live-Process False Blocker - 2026-05-31T12:58+0800

Loophole found in the `current-continuation-fresh` parent packet:

- Packet:
  `/tmp/ict-engine-consumer-ux-evidence-audit-20260531T-current-continuation-fresh/objective_closure_snapshot.json`.
- It reported `factor_closure_blocked` even though the queue head was a
  zero-config smoke child, not a profitability-factor runtime:
  `.local-artifacts/cargo-target/debug/ict-engine workflow-status --symbol DEMO
  --state-dir /tmp/ict-engine-done-definition-audit-smoke-20260531T044717479780Z-57656
  --refresh --agent`.
- Root cause: direct `ict-engine workflow-status/analyze/...` commands under
  `/tmp/ict-engine-*` were broad enough to catch consumer smoke state dirs.

Repair in the current worktree:

- `factor_claim_terminalization_audit.py` now filters zero-config smoke /
  DEMO ict-engine commands before classifying direct ict-engine Board B CLI
  commands as live factor owners.
- Regressions cover both:
  `test_live_process_classifier_ignores_demo_workflow_status_smoke_child`
  and `test_live_process_classifier_ignores_demo_analyze_smoke_state`.
- Existing positive coverage still proves real TOMAC direct CLI children stay
  live:
  `test_live_process_classifier_detects_direct_ict_engine_board_b_cli_child`
  and
  `test_live_process_classifier_detects_auto_quant_ingest_real_trades_board_b_cli_child`.

Verification:

- Focused classifier tests passed:
  `python3 -m unittest support.scripts.tests.test_factor_claim_terminalization_audit.FactorClaimTerminalizationAuditTest.test_live_process_classifier_ignores_demo_workflow_status_smoke_child support.scripts.tests.test_factor_claim_terminalization_audit.FactorClaimTerminalizationAuditTest.test_live_process_classifier_ignores_demo_analyze_smoke_state support.scripts.tests.test_factor_claim_terminalization_audit.FactorClaimTerminalizationAuditTest.test_live_process_classifier_detects_direct_ict_engine_board_b_cli_child support.scripts.tests.test_factor_claim_terminalization_audit.FactorClaimTerminalizationAuditTest.test_live_process_classifier_detects_auto_quant_ingest_real_trades_board_b_cli_child -v`.
- Full factor-claim audit suite passed:
  `python3 -m unittest support.scripts.tests.test_factor_claim_terminalization_audit -v`
  (`126/126`).
- `python3 support/scripts/check_script_manifest.py` passed.
- `python3 support/scripts/ci/check_docs_runtime_isolation.py` passed.
- `git diff --check -- support/scripts/factor_claim_terminalization_audit.py support/scripts/tests/test_factor_claim_terminalization_audit.py support/docs/plans/2026-05-31-consumer-ux-evidence-packet-audit-current.md`
  passed.
- Current compact factor closure after this filter:
  `/tmp/ict-engine-factor-closure-after-demo-smoke-filter-20260531T-now.json`
  returned exit `0`, `summary.status=pass`, `active_claims=0`,
  `live_factor_processes=0`, `blocking_reasons=[]`,
  `promotion_allowed_true=0`, `trade_usable_true=0`, and
  `same_tree_practical_closure=null`.
- A later same-turn rerun after a real TOMAC process started returned a real
  blocker, not the DEMO-smoke false owner:
  `/tmp/ict-engine-factor-closure-after-demo-smoke-filter-live-tomac-20260531T-now.json`
  exited `1` with `live_factor_processes=1`, pid `80783`, run root
  `/tmp/ict-engine-tomac-tsmom-vol-scaled-low-turnover-aq-20260531T115002+0800`,
  and a command excerpt from
  `run_tomac_index_futures_clean_aq_v1.py --root ...`.

Runtime skill update:

- `/Users/thrill3r/.hermes/skills/software-development/ict-engine-maintenance-loop/SKILL.md`
  now explicitly says DEMO / zero-config smoke `ict-engine` commands are not
  Board B live factor ownership.

Decision: this removes another false objective-packet blocker and improves
evidence packet cooperation. The full objective remains incomplete because
same-tree practical closure is still absent, same-head full-heavy proof is not
available, and release readiness still requires clean/source-aligned state.

## Runtime Drift Recheck - 2026-05-31T04:58Z

Fresh recheck after the current-head refresh:

```bash
ps -axo pid,ppid,etime,command | rg "done_definition_audit|objective_closure_snapshot|smoke_acceptance|run_tomac_one|run_tomac_index_futures_clean_aq" | rg -v rg
python3 support/scripts/factor_claim_terminalization_audit.py --compact --portable-paths --output /tmp/ict-engine-factor-closure-resume-6.json
```

Result:

- A new live TSMOM `5m` clean-AQ process appeared:
  pid `80783`, root
  `/tmp/ict-engine-tomac-tsmom-vol-scaled-low-turnover-aq-20260531T115002+0800`,
  command includes `--timeframes 5m --reuse-clean --aq-smoke-timeframe 5m`.
- A full-heavy done-definition process is also running:
  `/tmp/ict-engine-done-definition-heavy-20260531T-post-smoke-pass.json`.
- Factor audit returned `summary.status=needs_attention`,
  `live_factor_processes=1`, `blocking_reasons=[live_factor_processes]`,
  `promotion_allowed_true=0`, `trade_usable_true=0`,
  `same_tree_practical_closure=null`.

Decision: the immediately prior factor-clear snapshot is already stale for
closure. Wait for pid `80783` and the full-heavy done-definition process to
finish before another parent closure snapshot. Do not launch another factor
lane or claim completion while this runtime owns the shared AQ root.

## Post-TSMOM Runtime Clear Readback - 2026-05-31T13:10+0800

The TSMOM `5m` clean-AQ runtime exited before this readback. Terminal artifact
summary:

- Root:
  `/tmp/ict-engine-tomac-tsmom-vol-scaled-low-turnover-aq-20260531T115002+0800`.
- `checks/run_tomac_5m.exit` exists and the `summary.json` command row has
  `exit=0`, `timed_out=false`.
- `summaries/autoquant_clean_5m_gate.json` reports
  `decision=observation_no_autoquant_survivor_yet`,
  `promotion_allowed=false`, `trade_usable=false`, `update_goal=false`,
  `downstream_allowed=false`, `pre_bayes_allowed=false`, `bbn_allowed=false`,
  `catboost_allowed=false`, `execution_tree_allowed=false`, and
  `survivors_instrument_cost=[]`.
- `summaries/terminal_summary.json` reports
  `decision=terminalized_aq_partial_no_survivor_5m_blocked_by_foreign_claim`
  with the same practical flags false.

Fresh compact factor closure:

```bash
python3 support/scripts/factor_claim_terminalization_audit.py --compact --portable-paths --output /tmp/ict-engine-factor-closure-post-tsmom-5m-exit-20260531T1309.json
```

Result:

- Exit code `0`.
- `summary.status=pass`.
- `active_claims=0`, `live_factor_processes=0`,
  `blocking_reasons=[]`.
- `promotion_allowed_true=0`, `trade_usable_true=0`,
  `same_tree_practical_closure=null`.

Current-head parent snapshot:

```bash
python3 support/scripts/objective_closure_snapshot.py --compact --check-remotes --timeout-seconds 180 --output-dir /tmp/ict-engine-consumer-ux-evidence-audit-20260531T1310-post-tsmom-clear-codex
```

Result:

- Exit code `1`.
- Packet:
  `/tmp/ict-engine-consumer-ux-evidence-audit-20260531T1310-post-tsmom-clear-codex/objective_closure_snapshot.json`.
- Head:
  `43b765d7d3b9bb6bf51317580eb031fbfa1a244e`
  (`Fix demo smoke factor closure classification`).
- `summary.status=not_complete`, `completion_proven=false`.
- Current blockers:
  `done_definition_not_completion_ready`,
  `practical_admission_source_debt`,
  `same_tree_practical_closure_unproven`, and
  `release_readiness_blocked`.
- Factor closure is now clear in the parent packet:
  `factor_closure.status=pass`, `active_claims=0`,
  `live_factor_processes=0`.
- Done-definition child is `status=needs_fix` because
  `practical_admission_source_surface.status=fail`; the active untracked
  practical-admission wrapper set has `461` violations across `222` untracked
  files, with no tracked violations, and the existing quarantine no longer
  matches that untracked set.
- Same-tree practical closure is still absent:
  `promotion_allowed_true=0`, `trade_usable_true=0`,
  `same_tree_practical_closure=null`; missing stages remain provider/data,
  Pre-Bayes, BBN/workflow, path-ranker, execution-tree, feedback/update, and
  policy-training.
- Release readiness remote readback passed for origin and release mirror, but
  `worktree_clean_for_release` and `source_origin_matches_selected_source`
  remain unresolved.

Decision: still not complete. The demo-smoke classifier fix and the TSMOM
terminalization cleared false/live-runtime factor blockers, but objective
closure is now blocked by untracked practical-admission source debt, missing
same-tree practical closure, and release readiness. Do not claim practical
trade usability or release readiness from this state.

## Practical-Admission Quarantine Refresh - 2026-05-31T13:15+0800

Current HEAD advanced during this slice:

- `6929d5b3344ecfc66cdc12bc8339c050a0fbdcfb`
  (`Split flywheel learning from practical promotion`).

Narrow repair:

- Refreshed
  `support/docs/audits/practical-admission-source-debt-quarantine.json`
  to the current shared-worktree untracked practical-admission debt set.
- The refreshed quarantine records `461` violations across `222` untracked
  files, with fingerprint
  `d9397e66617c7515234e2436b846cd052b98940e6af73d370358c4d0e5497e44`.
- Tracked practical-admission violations remain zero. This quarantine is only
  an externalization of shared untracked wrapper residue; it is not release,
  promotion, trade-use, or completion evidence.

Verification:

```bash
python3 support/scripts/done_definition_audit.py --compact --practical-admission-source-timeout-seconds 120 --help-audit-timeout-seconds 120 --output /tmp/ict-engine-done-definition-after-practical-quarantine-refresh-20260531T-now.json
```

Result:

- Exit code `0`.
- `summary.status=pass`, `completion_ready=false`.
- `pass_count=7`, `fail_count=0`, `skip_count=4`.
- `practical_admission_source_surface.status=pass`.
- Quarantine matched as primary with `untracked_violation_count=461`,
  `untracked_violating_files=222`, and the fingerprint above.
- Heavy gates remain skipped:
  `cargo_check_all_targets`, `cargo_clippy_all_targets_deny_warnings`,
  `cargo_test`, and `smoke_acceptance_tmp_state`.

Current-head parent snapshot:

```bash
python3 support/scripts/objective_closure_snapshot.py --compact --check-remotes --timeout-seconds 180 --output-dir /tmp/ict-engine-consumer-ux-evidence-audit-20260531T-current-after-practical-quarantine-refresh-codex
```

Result:

- Exit code `1`.
- Packet:
  `/tmp/ict-engine-consumer-ux-evidence-audit-20260531T-current-after-practical-quarantine-refresh-codex/objective_closure_snapshot.json`.
- `summary.status=not_complete`, `completion_proven=false`.
- Current blockers are now:
  `done_definition_not_completion_ready`,
  `same_tree_practical_closure_unproven`, and
  `release_readiness_blocked`.
- `practical_admission_source_debt` is no longer a blocker; the packet carries
  it under `quarantined_practical_admission_source_debt`.
- Factor closure remains clear:
  `factor_closure.status=pass`, `active_claims=0`,
  `live_factor_processes=0`, `promotion_allowed_true=0`,
  `trade_usable_true=0`, and `same_tree_practical_closure=null`.
- Same-tree practical closure is still absent and missing provider/data,
  Pre-Bayes, BBN/workflow, path-ranker, execution-tree, feedback/update, and
  policy-training stages.
- Release readiness still fails on `worktree_clean_for_release` and
  `source_origin_matches_selected_source`; remote readback for origin and
  release mirror passed.

Decision: this is a packet-cooperation/source-debt externalization slice only.
The full objective is still not complete, no factor is practical-trade usable,
and no release readiness claim is allowed from this evidence.

## Post-Commit Practical Quarantine Fingerprint Drift - 2026-05-31T13:24+0800

Committed slice:

- `efe765e4b1976d79673f7d8fe6ab5566516103c0`
  (`Refresh practical admission debt quarantine`).

Post-commit retry evidence from another active audit:

- Packet:
  `/tmp/ict-engine-closed-loop-certainty-audit-20260531T110523+0800/snapshot_after_practical_untracked_fix_retry/objective_closure_snapshot.json`.
- Head:
  `efe765e4b1976d79673f7d8fe6ab5566516103c0`.
- Factor closure remained clear:
  `active_claims=0`, `live_factor_processes=0`,
  `promotion_allowed_true=0`, `trade_usable_true=0`,
  `same_tree_practical_closure=null`.
- Practical-admission untracked count and file count stayed stable at
  `461` violations across `222` untracked files, but the fingerprint changed to
  `b854587048cc9fdaabfd530027c8f290ab857bdf159c5d7a9ca30398532ec74c`.
- The quarantine manifest now records that digest under
  `reviewed_alternative_untracked_violations_sha256`, preserving the primary
  reviewed packet while avoiding false fail-closed churn for the same count/file
  surface.
- That retry did not produce a clean objective snapshot: it skipped remote
  checks and timed out in `fixed_bps_cost_model_source_surface`, so it is not
  completion evidence.

Decision: this is a same-count/same-file-count quarantine fingerprint drift
refresh only. It does not change practical readiness: no same-tree practical
closure packet exists, and no `trade_usable=true` factor is proven.
