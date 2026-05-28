# Practical Admission Completion Gate Tracking - 2026-05-28

Owner: Codex
Status: active / objective not complete
Route: `sd/ict-engine-maintenance-loop`

## Objective Slice

The broader objective asks whether factor-training direction and profitability
factor promotion are fully safe through the real `ict-engine` closed loop. This
slice addresses one concrete loophole found in the current tree: unsafe tracked
downstream/gate wrapper surfaces could remain present while the done-definition
audit still reported only skipped heavy gates, leaving completion proof too
weak. Untracked wrapper residue is still reported separately and remains a
dirty-worktree/release-readiness risk, but it is not allowed to fail the tracked
source release gate by itself.

## Fresh Evidence

2026-05-29 active-inventory coordination readback:

- Fresh coordinated snapshot before this fix:
  `/tmp/ict-engine-goal-20260529-codex-cont-current-013026/objective_closure_snapshot.json`
  remained `summary.status=not_complete` with blockers
  `done_definition_not_completion_ready`, `factor_closure_blocked`, and
  `release_readiness_blocked`. The factor child also exposed one false action
  queue item: `false-negative-amnesty-20260529T013008.claim.json` was an
  `active_inventory` claim for artifact scanning with `promotion_allowed=false`,
  `trade_usable=false`, and explicit no-provider/AQ-launch language, but the
  compact audit treated it as wait-only factor debt.
- Implemented fix: `support/scripts/factor_claim_terminalization_audit.py` now
  classifies conservative `active_inventory` claims as coordination-only only
  when they also carry false practical flags plus audit/inventory/artifact-scan
  purpose text and no-launch/read-only language. This keeps real active factor
  claims blocking while preventing bookkeeping inventory scans from polluting
  compact factor action queues.
- RED/GREEN regression:
  `test_valid_inventory_claim_does_not_block_factor_closure` first failed with
  `summary.status='needs_attention'`, then passed after the classifier fix.
  Focused verification also passed the existing audit-only, wait-only, and fresh
  active-claim guard regressions.
- Fresh compact factor audit after the fix still intentionally exited red for
  real runtime ownership: `active_claims=1`, `live_factor_processes=1`,
  `wait_only_active_claims_without_live_process=0`, `promotion_allowed_true=0`,
  and `trade_usable_true=0`. The only queue head was the live
  SessionWindowSweepReclaim launch claim rooted at
  `/tmp/ict-engine-tomac-session-window-sweep-reclaim-prep-20260528T012234+0800`.
  This is current evidence against objective completion and against launching a
  sibling TOMAC/AQ lane.

2026-05-29 post-Camarilla terminalization refresh:

- Fresh coordinated snapshot:
  `/tmp/ict-engine-goal-20260529-codex-post-camarilla-terminal-011337/objective_closure_snapshot.json`
  remained `summary.status=not_complete`. Camarilla was terminalized
  fail-closed, but a different fresh SessionClusterCadenceRepair claim became
  the factor queue head:
  `20260529T004301+0800-codex-tomac-session-cluster-cadence-takeover.claim`.
  That claim was fresh-owned, so this slice did not terminalize, overwrite, or
  launch into that factor lane.
- Current practical-admission source scan still reports tracked source clean:
  `tracked_violation_count=0`. The untracked scratch-wrapper residue grew to
  `untracked_violation_count=229` across `untracked_violating_files=148`, all
  verified as Git-untracked existing files with `git ls-files --error-unmatch`.
  Violation type counts are
  `practical_flag_without_extension_complete_guard=62`,
  `five_bps_survival_uses_trade_density_floor=82`,
  `downstream_admission_uses_2bps_survivor_gate=49`, and
  `branch_local_admission_uses_transition_hard_gate=36`.
- The practical-admission debt quarantine was refreshed only for this reviewed
  untracked residue set. The stable signature fingerprint is now
  `cf3fdd92df9dc62b101fb8f47879f9a48147c12721e28025984e323799443f2e`. This
  does not make the objective complete or release-ready; it only externalizes
  the reviewed untracked scratch debt so tracked-source completion evidence can
  remain distinguishable from dirty shared-worktree residue.

2026-05-29 coordination/readback refresh:

- Fresh coordinated snapshot before this fix:
  `python3 support/scripts/objective_closure_snapshot.py --compact --check-remotes --output-dir /tmp/ict-engine-goal-20260529-codex-current`
  remained `summary.status=not_complete`. It also exposed a packet
  coordination loophole: the factor child counted the active audit-only claim
  `20260529T003643+0800-codex-closed-loop-loophole-audit.claim` as a fresh
  active factor blocker even though the claim explicitly forbids provider,
  IBKR, Auto-Quant, freqtrade, and `run_tomac` launches and has
  `promotion_allowed=false`, `trade_usable=false`, and `update_goal=false`.
- Implemented fix: `support/scripts/factor_claim_terminalization_audit.py` now
  classifies conservative `active_audit_only` / `active_coordination_only`
  claims as `coordination_only` only when they also carry explicit false
  practical flags and no-launch/read-only audit language. These claims remain
  visible in the full report and are counted as
  `coordination_only_active_claims`, but they no longer pollute compact
  attention queues or `active_claims` factor-closure blockers.
- Parent packet reuse fix: `support/scripts/objective_closure_snapshot.py` now
  lifts `coordination_only_active_claims` into the factor surface so a reader
  can distinguish ignored coordination work from real factor debt without
  opening the child packet.
- Fresh factor audit after the fix:
  `/tmp/ict-engine-goal-20260529-factor-after-coordination-fix.json` reported
  `coordination_only_active_claims=1` while the real factor surface remained
  red: `active_claims=5`, `live_factor_processes=1`,
  `active_claims_without_live_process=5`, `stale_safe_takeover_candidates=4`,
  `promotion_allowed_true=0`, and `trade_usable_true=0`. The audit-only claim
  was no longer the queue head; the first fresh factor action was
  `20260529T004000+0800-codex-tomac-camarilla-pivot-reclaim-takeover.claim`.
- Fresh coordinated snapshot after the fix:
  `/tmp/ict-engine-goal-20260529-codex-after-coordination-fix/objective_closure_snapshot.json`
  remained `summary.status=not_complete`. The parent factor surface now showed
  `coordination_only_active_claims=1`, but practical closure was still blocked
  by real active factor claims and live runtime PID `11367` rooted at
  `ict-engine-tomac-tod-balanced-predicate-density-expansion-autoquant-loop-20260529T004128+0800`.
- The same snapshot found a separate source-debt quarantine drift: tracked
  practical-admission source was still clean
  (`tracked_violation_count=0`), but the untracked wrapper-debt fingerprint was
  line-sensitive and moved when an untracked wrapper shifted the same violation
  from one line to another. The fingerprint now hashes the stable violation
  signature (`file`, `key`, `value`, `violation`) and preserves duplicate
  signatures, but ignores incidental line/column churn. The refreshed quarantine
  hash is `35777afdfd203c1cc17bb995c487e8ac29866c39616b1e887c9acea80079b2e0`
  for the reviewed residue counts (`untracked_violation_count=193`,
  `untracked_violating_files=115`). If the signature set drifts again, the
  blocker reappears.
- Focused verification passed:
  `python3 -m unittest support.scripts.tests.test_done_definition_audit support.scripts.tests.test_factor_claim_terminalization_audit support.scripts.tests.test_objective_closure_snapshot -v`
  ran `114/114 OK`. The new regression first failed on
  `summary.status='needs_attention'` for a valid audit-only claim, then passed
  after the classifier fix. A second regression first failed on line-sensitive
  practical-admission debt fingerprints, then passed after the stable-signature
  fingerprint fix.

2026-05-28 continuation readback:

- `python3 support/scripts/objective_closure_snapshot.py --compact --check-remotes --output-dir /tmp/ict-engine-goal-20260528-codex-current-continuation-after-manifest`
  emitted a still-red coordinated packet with `summary.status=not_complete` and
  blockers `done_definition_not_completion_ready`,
  `practical_admission_source_debt`, `factor_closure_blocked`, and
  `release_readiness_blocked`.
- The factor child drifted again while this audit continued: `active_claims=2`,
  `live_factor_processes=0`, `active_claims_without_live_process=2`,
  `wait_only_active_claims_without_live_process=1`,
  `promotion_allowed_true=0`, and `trade_usable_true=0`. Both current factor
  claims are fresh, so this continuation did not terminalize or overwrite them.
- The staged packet now includes
  `practical_admission_source_debt_manifest.json` with direct top-level counts,
  not only nested `summary` counts: `scanned_files=915`,
  `tracked_scanned_files=28`, `tracked_violation_count=0`,
  `untracked_scanned_files=887`, `untracked_violation_count=193`, and
  `violations_by_type={practical_flag_without_extension_complete_guard:62,
  five_bps_survival_uses_trade_density_floor:82,
  downstream_admission_uses_2bps_survivor_gate:49}`.
- A follow-up live readback caught and fixed one more packet-portability
  loophole: `summary.blocker_details.practical_admission_source_debt` initially
  copied the child temp manifest path, while `evidence_files` was packet-safe.
  `/tmp/ict-engine-goal-20260528-codex-current-continuation-after-blockerdetails-fix/objective_closure_snapshot.json`
  now keeps the same blocker red but exposes
  `debt_manifest_file="practical_admission_source_debt_manifest.json"` directly
  in the parent summary.
- That same final snapshot shows the factor surface is still actively moving:
  `active_claims=4`, `live_factor_processes=1`,
  `active_claims_without_live_process=4`,
  `wait_only_active_claims_without_live_process=2`, one missing run-root claim,
  `promotion_allowed_true=0`, and `trade_usable_true=0`. This is current proof
  against objective completion, not a residual paperwork issue.
- Focused verification for this packet-shape/readback improvement passed:
  `python3 -m unittest support.scripts.tests.test_done_definition_audit -v`
  ran `21/21 OK`, and
  `python3 -m unittest support.scripts.tests.test_objective_closure_snapshot -v`
  ran `21/21 OK`.

- `python3 support/scripts/factor_claim_terminalization_audit.py --compact`
  reported `status=pass`, `active_claims=0`, `live_factor_processes=0`,
  `promotion_allowed_true=0`, and `trade_usable_true=0`.
- `/tmp/ict-engine-goal-20260528-codex-current-snapshot/objective_closure_snapshot.json`
  reported `summary.status=not_complete` with blockers
  `done_definition_not_completion_ready`,
  `same_tree_practical_closure_unproven`, and `release_readiness_blocked`.
- `python3 support/scripts/release_readiness_audit.py --compact --check-remotes`
  still failed `worktree_clean_for_release`,
  `source_origin_matches_selected_source`, and `release_version_tag_available`.
- Earlier full practical-admission source scan over `913` `run_*.py` wrappers
  found `115` violating files and `193` violations:
  `practical_flag_without_extension_complete_guard=62`,
  `five_bps_survival_uses_trade_density_floor=82`, and
  `downstream_admission_uses_2bps_survivor_gate=49`.
- Current tracked-source readback from
  `/tmp/ict-engine-goal-20260528-codex-done-current-full.json` scanned `915`
  wrappers: `tracked_scanned_files=28`, `tracked_violation_count=0`,
  `untracked_scanned_files=887`, and `untracked_violation_count=193`. This
  means the committed-source gate is clean while untracked wrapper residue must
  still be handled by worktree isolation or explicit cleanup.

## Loophole

The existing scanner
`support/scripts/research/downstream_practical_admission_source_check.py` could
find unsafe practical-admission wrappers, but `done_definition_audit.py` did not
run it. That allowed a future closure packet to look cleaner than the tracked
source wrapper surface: heavy gates could be the only visible done-definition
gap while committed wrappers still mapped local admission strings, 2bps
survivors, or trade-density predicates into practical downstream readiness.

## Implemented Fix

`support/scripts/done_definition_audit.py` now includes a lightweight
`practical_admission_source_surface` gate. It scans
`support/docs/experiments/actionable-regime-confidence/scripts/run_*.py`
wrappers with the existing source checker, splits tracked versus untracked
files with `git ls-files`, and fails the done-definition audit only when unsafe
patterns remain in tracked source.

The debt manifest emitted by that gate now mirrors the core scan counts at the
top level (`tracked_violation_count`, `untracked_violation_count`,
`violations_by_type`, and related file counts) while preserving the original
nested `summary` block. This keeps the evidence packet lightweight for simple
readers and still backward-compatible for existing consumers.

This intentionally does not mass-edit untracked historical wrappers in one
broad slice. It makes the committed-source objective fail closed if tracked
wrappers regress, while leaving untracked wrapper violations visible as residue
that must be excluded from release or cleaned in narrower verified fixes.

## Verification

- `python3 -m unittest support.scripts.tests.test_done_definition_audit -v`
  passed `19/19`.
- `python3 -m unittest support.scripts.research.tests.test_downstream_practical_admission_source_check -v`
  passed `12/12`.
- `python3 -m unittest support.scripts.tests.test_objective_closure_snapshot -v`
  passed `20/20` on rerun.
- `python3 support/scripts/done_definition_audit.py --output /tmp/ict-engine-goal-20260528-codex-done-current-full.json`
  reported `practical_admission_source_surface.status=pass` because
  `tracked_violation_count=0`; it still exposed `untracked_violation_count=193`.
- `python3 support/scripts/objective_closure_snapshot.py --compact --check-remotes --output-dir /tmp/ict-engine-goal-20260528-codex-after-tracked-practical`
  remained `summary.status=not_complete` with blockers
  `done_definition_not_completion_ready`, `factor_closure_blocked`, and
  `release_readiness_blocked`. The factor child had `active_claims=2`,
  `live_factor_processes=2`, `promotion_allowed_true=0`, and
  `trade_usable_true=0`; release readiness still failed
  `worktree_clean_for_release`, `source_origin_matches_selected_source`, and
  `release_version_tag_available`.

## Current Verdict

The full objective is still not complete. The current improvement makes the
completion audit more truthful for committed source and prevents tracked unsafe
practical-admission wrappers from being hidden behind partial/skipped
done-definition evidence. Remaining work is to keep untracked violating wrappers
out of release/source claims, produce a same-tree practical closure packet with
a genuinely trade-usable factor, clear live factor runtimes, and clear
release/readiness gates from a clean selected source slice.
