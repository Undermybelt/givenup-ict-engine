# Consumer UX And Evidence Packet Audit - 2026-05-31

Owner: Codex
Route: `sd/ict-engine-maintenance-loop`
Status: active / not complete
Repo: `/Users/thrill3r/projects-ict-engine/ict-engine`
Branch: `main`
Observed HEAD: `7e95b910061980f25d96b58dbc8820289cc5250d`

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

## Next Steps

1. Run the existing audits and capture exact blockers.
2. Pick the smallest real loophole that affects consumer UX, packet reuse, or
   practical-use evidence.
3. Fix it in source/tests/docs without touching unrelated dirty work.
4. Run focused regressions plus the relevant audit again.
5. Update this doc with evidence and repeat until no blocker remains or a real
   external/shared-worktree blocker is proven.
6. Commit only the coherent verified slice by explicit path.
