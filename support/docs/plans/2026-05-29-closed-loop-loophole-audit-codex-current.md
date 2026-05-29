# Closed-Loop Loophole Audit - 2026-05-29 Codex

Status: active / objective not complete

## Scope

Track the current slice of the factor-training closed-loop objective: find and
fix loopholes that could make `ict-engine` claim practical factor readiness
without a same-tree closed-loop proof.

## Current Evidence

- Audit-only workdoc:
  `/tmp/ict-engine-closed-loop-loophole-audit-codex-20260529T132716+0800/workdoc.md`.
- Audit-only claim:
  `/tmp/ict-engine-agent-claims/board-b-factor-refinement/20260529T132716+0800-codex-closed-loop-loophole-audit.claim`.
- Fresh heavy done-definition proof:
  `/tmp/ict-engine-closed-loop-loophole-audit-codex-20260529T132716+0800/done-definition-heavy-current.json`.
  It passed full enabled coverage on `HEAD=652c4261928892b6f7800a2be6356df7c850cf69`:
  `completion_ready=true`, `pass_count=10`, `skip_count=0`, `fail_count=0`.
- Proof-aware objective snapshot:
  `/tmp/ict-engine-closed-loop-loophole-audit-codex-20260529T132716+0800/objective-snapshot-heavyproof-current/`.
  It accepted the heavy proof with `proof_applied=true` and remained
  `not_complete` on `factor_closure_blocked`, `release_readiness_blocked`, and
  `release_remote_checks_not_run`.
- Current practical factor count remains zero in same-turn audits:
  `promotion_allowed_true=0`, `trade_usable_true=0`, and no
  `same_tree_practical_closure` packet.

## Fixed Loophole

`support/scripts/factor_claim_terminalization_audit.py` could classify a shell
readback poller as a live factor process when macOS `ps` rendered embedded
newlines as `\\012` and the command mentioned `run_tomac` output files.

Fix: normalize the command text inside `_looks_like_readback_command()` before
checking `ps`/`rg`/`tail`/`find` readback markers, and include `ps -p` pollers.

Regression: `test_live_process_classifier_ignores_ps_escaped_shell_readback_poller`.

## Fixed Loophole - Same-Tree Evidence Packet Content

`support/scripts/factor_claim_terminalization_audit.py` accepted a
`same_tree_practical_closure.json` marker when it had pass flags and an
in-run-root `evidence_packet` path, but it only verified that the evidence file
existed. A marker-only JSON such as `{"chain":"provider_execution_feedback"}`
could therefore be discovered as practical closure without proving the actual
provider -> execution -> feedback chain.

Fix: require the referenced evidence JSON to carry the same terminal metrics
that the downstream producer writes for practical admission: true practical
flags, zero command exits, branch survival, actionable candidate, branch-local
admission, validation readiness, path-ranker use by execution tree, non-observe
candidate status, policy-training summary, and raw/production/observation
validation counters meeting their required ratios.

Regression: `test_build_report_rejects_closure_packet_with_marker_only_evidence`.

## Fixed Loophole - Objective Snapshot Closure Parity

`support/scripts/objective_closure_snapshot.py` independently checked
`same_tree_practical_closure` packet fields but did not require proof that the
factor audit had validated the referenced evidence JSON content. A summary-level
packet with pass markers could therefore make the snapshot surface-green if a
caller bypassed the stricter factor-audit discovery path.

Fix: `factor_claim_terminalization_audit.py` now marks discovered closure
packets with `evidence_packet_validated=true` only after validating the
referenced evidence JSON content, and `objective_closure_snapshot.py` requires
that flag before treating a packet as practical closure.

Regression: `test_summarize_snapshot_rejects_unvalidated_practical_closure_packet`.

## Verification

- RED: the new regression failed before the implementation because
  `_is_live_factor_command()` returned `True`.
- GREEN: the focused regression passed after the fix.
- `python3 -m py_compile support/scripts/factor_claim_terminalization_audit.py support/scripts/tests/test_factor_claim_terminalization_audit.py`
  passed.
- `python3 -m unittest support.scripts.tests.test_factor_claim_terminalization_audit support.scripts.tests.test_objective_closure_snapshot -v`
  ran `125/125 OK` after the same-tree evidence-content and snapshot-parity
  regressions were added.
- `python3 -m unittest support.docs.experiments.actionable-regime-confidence.scripts.test_tomac_nq_bidir_opening_drive_exact_downstream_v1 -v`
  ran `11/11 OK`, keeping the current closure packet producer behavior aligned
  with the stricter audit consumer.
- `git diff --check -- support/scripts/factor_claim_terminalization_audit.py support/scripts/tests/test_factor_claim_terminalization_audit.py support/docs/plans/2026-05-28-factor-training-closed-loop-continuation-codex-current.md`
  returned clean.

## Current Blockers

- Factor closure is still blocked by live/fresh Python-only prescreen lanes in
  the shared Board B queue. The latest current audit in this slice saw the real
  KST/Coppock PortfolioDensityLift prescreen root:
  `/tmp/ict-engine-tomac-kst-coppock-portfolio-density-lift-pybacktest-20260529T133157+0800`.
- Current compact audit after the same-tree validator fix still reports
  `status=needs_attention`, `active_claims=0`, `live_factor_processes=1`,
  `promotion_allowed_true=0`, `trade_usable_true=0`, and
  `same_tree_practical_closure=null`. The active Python-only PortfolioDensityLift
  prescreen terminalized fail-closed with `survivor_count=0`; the remaining
  blocker is a live Silver Bullet RSI Sniper AQ/prep process under
  `/tmp/ict-engine-tomac-silver-bullet-rsi-sniper-prep-20260529T134152+0800`, so
  factor closure must still wait before reevaluation.
- Lightweight objective snapshots after `2c1e9a4e` failed closed because
  `done_definition_audit.py --compact` exceeded both 90s and 180s child
  timeouts in the dirty/shared tree. A direct bounded child audit eventually
  returned `status=needs_fix` with `unresolved=[practical_admission_source_surface]`
  and skipped heavy gates, so there is no completion evidence from the snapshot
  path.
- Release readiness remains blocked by `worktree_clean_for_release`; remote
  gates were not run in the proof-aware snapshot.
- The objective still lacks a same-tree practical closure packet proving
  provider/training admission -> Pre-Bayes -> BBN -> path-ranker consumption ->
  execution tree -> feedback/live-use.

## Next Steps

1. Rerun `python3 support/scripts/factor_claim_terminalization_audit.py --compact`
   after the active prescreen lane terminalizes.
2. If factor closure is clear, rerun `objective_closure_snapshot.py` with the
   fresh heavy proof and `--check-remotes` when release evidence is in scope.
3. Do not launch a sibling factor lane while any fresh active claim or live
   process exists.
4. Do not count Python-only screens, trade CSVs, or raw positive rows as
   practical closure evidence.
5. Commit only coherent verified slices; preserve unrelated dirty and staged
   work from other agents.
