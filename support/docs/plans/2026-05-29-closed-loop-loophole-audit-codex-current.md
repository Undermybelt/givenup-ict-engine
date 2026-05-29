# Closed-Loop Loophole Audit - 2026-05-29 Codex

Status: active / objective not complete

## Scope

Track the current slice of the factor-training closed-loop objective: find and
fix loopholes that could make `ict-engine` claim practical factor readiness
without a same-tree closed-loop proof.

## Current Evidence

- 2026-05-29T16:12+0800 same-turn factor audit remains not complete and not
  launchable: compact audit reports `status=needs_attention`,
  `active_claims=6`, `fresh_active_claims_without_live_process=5`,
  `wait_only_active_claims_without_live_process=1`, `live_factor_processes=0`,
  `promotion_allowed_true=0`, `trade_usable_true=0`, and
  `same_tree_practical_closure=null`. None of those active claims is older than
  the one-hour stale-safe takeover threshold, so no takeover, sibling AQ launch,
  provider fetch, IBKR command, paper/sim/live command, or goal completion claim
  is allowed from this slice.
- 2026-05-29T16:10+0800 DailyDonchian RVOLAccelerationFilter source-local eval
  terminalized negative under
  `/tmp/ict-engine-tomac-daily-donchian-rvol-acceleration-filter-source-eval-20260529T160713+0800/`.
  `terminal_summary.json` reports `decision=reject_low_density`,
  `scan_exit=0`, `selected_component_count=1`, and 5bps stress
  `trades=219`, `trades_per_all_session=0.14074550128534705`,
  `net_ret=0.1363282320501346`, `profit_factor=1.1457619293820247`.
  This is positive but too sparse for practical cadence, so it is not
  `promotion_allowed` or `trade_usable` evidence.
- 2026-05-29T16:12+0800 high-frequency microburst local TOMAC-cache screen first
  readback showed a negative terminal summary under
  `/tmp/ict-engine-tomac-highfreq-microburst-liquidity-20260529T160425+0800/`.
  `terminal_summary.json` reports `candidate_rows=1860`,
  `highfreq_rows_20_to_800_per_day=563`, `positive_highfreq_5bps_rows=0`,
  `local_screen_survivors=0`, and
  `decision=drop_local_highfreq_no_5bps_survivor_in_20_to_800_per_day_band`.
  The data-resolution note is important: 1m OHLCV can only screen one entry
  decision per symbol per minute and cannot prove tick/order-book sub-minute HFT
  fills. This is Python-only negative evidence if the run root stays terminal.
  Superseding caution: 2026-05-29T16:15+0800 compact audit then saw the same
  run root live again with PID `82359` and `exit_file_state=stale_for_process`,
  so that terminal summary is not final authority while the process is alive.
- 2026-05-29T16:15+0800 latest compact audit moved back to runtime-blocked:
  `status=needs_attention`, `active_claims=6`, `active_claims_without_live_process=5`,
  `live_factor_processes=2`, `promotion_allowed_true=0`,
  `trade_usable_true=0`, and `same_tree_practical_closure=null`. Live roots were
  `/tmp/ict-engine-tomac-highfreq-microburst-liquidity-20260529T160425+0800`
  and
  `/tmp/ict-engine-tomac-high-frequency-microstructure-screen-20260529T160636+0800`.
  No stale-safe takeover or sibling launch is allowed while those owners are
  fresh/live.
- 2026-05-29T16:17+0800 final same-turn audit: the live roots above exited or
  terminalized, but the queue is still not launchable. Compact audit reports
  `status=needs_attention`, `active_claims=3`,
  `fresh_active_claims_without_live_process=3`, `live_factor_processes=0`,
  `promotion_allowed_true=0`, `trade_usable_true=0`, and
  `same_tree_practical_closure=null`. Fresh active claims are OTE/FVG/OB
  SessionDirectionalBias age 20m, HF micro-scalp prep age 12m, and NQ/YM
  lead-lag VWAP residual screen age 8m; all are below the one-hour stale-safe
  takeover rule.

- 2026-05-29T16:03+0800 continuation workdoc:
  `/tmp/ict-engine-closed-loop-loophole-audit-codex-20260529T160308+0800/workdoc.md`.
- 2026-05-29T16:03+0800 audit-only claim:
  `/tmp/ict-engine-agent-claims/board-b-factor-refinement/20260529T160308+0800-codex-closed-loop-loophole-audit.claim`.
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

## Dirty-Residue Packaging Decision - TOMAC Inventory/Coverage

Other agents left many untracked TOMAC scripts, top-level generated factor-name
files, and modified one-off IBKR/MGC Gate 1 wrappers in the shared worktree.
Those surfaces are not product-ready by themselves: several are loose launch
wrappers, local-provider scripts, repo-root scratch files, or Board docs with
large unrelated append-only edits.

Reusable slice selected for commit: add read-only TOMAC source organization
helpers under `support/scripts/research/` instead of committing the loose
training residue:

- `tomac_strategy_inventory.py` inventories a TOMAC source tree into structured
  family/symbol/timeframe/indicator/class/branch-hint rows.
- `tomac_factor_coverage_matrix.py` combines those rows with Board B `/tmp`
  claims to distinguish active claimed families from available-for-rotation
  families.
- `support/scripts/SCRIPTS.md` and `support/scripts/script_manifest.json`
  classify both helpers as read-only utilities and explicitly mark them as
  coordination/residue-cleanup evidence, not practical trading proof.

Current read-only evidence written outside the repo:

- `/tmp/ict-engine-tomac-strategy-inventory-20260529.json`:
  `total_files=49`, `branch_count=30`.
- `/tmp/ict-engine-tomac-factor-coverage-20260529.json` and `.csv`:
  `family_count=22`, `active_claimed=3`, `available_for_rotation=19`.

Decision: do not commit the modified MGC wrapper scripts, repo-root scratch
factor-name files, or broad Board doc edits in this slice. They either need
conversion into manifest-backed candidate packs or terminal evidence packets,
or should remain unstaged residue.

Release/publish decision: no release. Current factor audit still reports live
factor/runtime occupancy plus zero practical factors, and the worktree remains
dirty, so this is an internal maintenance commit only.

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
- `python3 -m unittest support.scripts.research.tests.test_tomac_strategy_inventory support.scripts.research.tests.test_tomac_factor_coverage_matrix -v`
  ran `30/30 OK` for the residue-inventory helpers.
- `python3 support/scripts/check_script_manifest.py` returned
  `script_manifest status=pass entries=31 required_public_entries=4 safe_required_public_entries=4`.
- `python3 support/scripts/ci/check_docs_runtime_isolation.py` returned
  `docs runtime isolation ok`.
- `python3 -m py_compile support/scripts/research/tomac_strategy_inventory.py support/scripts/research/tomac_factor_coverage_matrix.py support/scripts/research/tests/test_tomac_strategy_inventory.py support/scripts/research/tests/test_tomac_factor_coverage_matrix.py`
  passed.
- `git diff --check -- support/scripts/research/tomac_strategy_inventory.py support/scripts/research/tomac_factor_coverage_matrix.py support/scripts/research/tests/test_tomac_strategy_inventory.py support/scripts/research/tests/test_tomac_factor_coverage_matrix.py support/scripts/SCRIPTS.md support/scripts/script_manifest.json`
  returned clean.

## 2026-05-29T16:03+0800 Continuation Evidence

- Current workdoc:
  `/tmp/ict-engine-closed-loop-loophole-audit-codex-20260529T160308+0800/workdoc.md`.
- Current audit-only claim:
  `/tmp/ict-engine-agent-claims/board-b-factor-refinement/20260529T160308+0800-codex-closed-loop-loophole-audit.claim`.
- Initial compact claim audit showed the audit-only claim itself was invalid;
  the claim was repaired with `agent_name`, exact scope/task, non-goals,
  write surface, run/tmp root, and no-launch wording so it no longer pollutes
  factor closure as an active profitability owner.
- Focused practical-admission source check for the tracked QQQ wrapper passed:
  `python3 support/scripts/research/downstream_practical_admission_source_check.py support/docs/experiments/actionable-regime-confidence/scripts/run_ibkr_qqq_intraday_micro_trend_reclaim_density_1m_mtf_v1.py`.
  That wrapper was already dirty in the shared tree and is not staged by this
  audit slice.
- Done-definition readback after current source:
  `/tmp/ict-engine-closed-loop-loophole-audit-codex-20260529T160308+0800/done_definition_audit.after_current_read.compact.json`.
  It reported `status=pass`, `completion_ready=false`,
  `evidence_level=partial_skipped_gates`, tracked practical/await-launch
  violations `0`, but skipped `cargo_check_all_targets`,
  `cargo_clippy_all_targets_deny_warnings`, `cargo_test`, and
  `smoke_acceptance_tmp_state`.
- Objective snapshot before quarantine refresh:
  `/tmp/ict-engine-closed-loop-loophole-audit-codex-20260529T160308+0800/objective-snapshot-after-claimfix/`.
  It remained `not_complete` and required a `same_tree_practical_closure_packet`.
- The two untracked-debt quarantine manifests were refreshed to the current
  16:10 snapshot fingerprints. This is only an externalization of dirty
  shared-worktree wrapper residue; it is not practical-factor evidence.
- Verification for the quarantine/current-source slice:
  `python3 -m unittest support.scripts.tests.test_done_definition_audit support.scripts.tests.test_objective_closure_snapshot -v`
  ran `69/69 OK`.
- Done-definition readback after quarantine refresh:
  `/tmp/ict-engine-closed-loop-loophole-audit-codex-20260529T160308+0800/done_definition_audit.after_quarantine.compact.json`.
  Both source-debt quarantine checks matched, but completion remained unproven
  because heavy gates were skipped.
- Objective snapshot after quarantine refresh:
  `/tmp/ict-engine-closed-loop-loophole-audit-codex-20260529T160308+0800/objective-snapshot-after-quarantine/`.
  It remained `not_complete` with blockers
  `done_definition_not_completion_ready`, `factor_closure_blocked`,
  `release_readiness_blocked`, and `release_remote_checks_not_run`; manual
  requirements still included `same_tree_practical_closure_packet` and
  `truthful_completion_commit`.

## 2026-05-29T16:34+0800 Continuation Evidence

- Current no-launch audit workdoc:
  `/tmp/ict-engine-closed-loop-loophole-audit-codex-20260529T163426+0800/workdoc.md`.
- Current no-launch audit claim:
  `/tmp/ict-engine-agent-claims/board-b-factor-refinement/20260529T163426+0800-codex-closed-loop-loophole-audit.claim`.
- Refreshed objective snapshot:
  `/tmp/ict-engine-objective-refresh-codex-20260529T162900+0800/`.
  It remained `not_complete` with blockers
  `done_definition_not_completion_ready`, `factor_closure_blocked`,
  `release_readiness_blocked`, and `release_remote_checks_not_run`. Manual
  requirements remain `same_tree_practical_closure_packet` and
  `truthful_completion_commit`.
- Stale audit-only coordination claim
  `/tmp/ict-engine-agent-claims/board-b-factor-refinement/20260529T132716+0800-codex-closed-loop-loophole-audit.claim`
  was terminalized as superseded by the current audit-only packet. This was not
  a factor-lane terminalization and did not touch any provider/AQ/TOMAC owner.
- Compact factor audit after cleanup reports `status=needs_attention`,
  `active_claims=1`, `valid_active_claims=1`,
  `fresh_active_claims_without_live_process=1`, `live_factor_processes=0`,
  `promotion_allowed_true=0`, `trade_usable_true=0`, and
  `same_tree_practical_closure=null`. The remaining attention claim is
  `20260529T155611+0800-codex-tomac-ote-fvg-ob-session-directional-bias-launch.claim`,
  age 41m, still below the one-hour stale-safe takeover rule.
- 2026-05-29T16:50+0800 recheck after waiting showed new runtime occupancy
  before the OTE/FVG/OB claim became stale-safe. Compact audit reported
  `status=needs_attention`, `active_claims=5`, `valid_active_claims=5`,
  `fresh_active_claims_without_live_process=4`, `live_factor_processes=2`,
  `promotion_allowed_true=0`, `trade_usable_true=0`, and
  `same_tree_practical_closure=null`. Live roots were
  `/tmp/ict-engine-tomac-local-py-mtf-vwap-compression-breakout-20260529T164103+0800`
  and
  `/tmp/ict-engine-tomac-range-vwap-keltner-rrr-20260529T162731+0800`.
  No takeover, provider/AQ/TOMAC launch, factor terminalization, or practical
  promotion is legal from this audit slice.

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
- Same-turn compact audit on 2026-05-29T06:41Z reported
  `active_claims=2`, `fresh_active_claims_without_live_process=1`,
  `live_factor_processes=3`, `promotion_allowed_true=0`,
  `trade_usable_true=0`, and `same_tree_practical_closure=null`.

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

## 2026-05-29T17:15+0800 Continuation Evidence

- Current no-launch audit workdoc:
  `/tmp/ict-engine-closed-loop-loophole-audit-codex-20260529T165649+0800/workdoc.md`.
- Current no-launch audit claim:
  `/tmp/ict-engine-agent-claims/board-b-factor-refinement/20260529T165649+0800-codex-closed-loop-loophole-audit.claim`.
- Fresh factor-claim audit after the workdoc terminal-readback fix reports
  `status=pass`, `active_claims=0`, `live_factor_processes=0`,
  `promotion_allowed_true=0`, `trade_usable_true=0`, and
  `same_tree_practical_closure=null`. This proves only that claim/runtime
  blockers are clear; it is not practical-factor proof.
- Found and fixed a claim-audit loophole: a run-root `workdoc.md` with a
  non-terminal planning/TDD line such as `Decision: skipped` could be parsed as
  terminal evidence, causing an active `active_local_screen` claim to disappear
  from active-claim attention while its live Python process still occupied the
  run root. The fix restricts workdoc terminalization to `terminal_*` fields,
  terminal/final readback sections, or explicitly terminal decision/status
  names such as `terminalized_*`, `drop_*`, `reject_*`, `fail_closed`,
  `launch_blocked_*`, or `readback_complete`.
- Regression added:
  `test_build_report_keeps_active_workdoc_when_nonterminal_tdd_decision_present`.
- Runtime lesson synced to Hermes runtime skill:
  `/Users/thrill3r/.hermes/skills/software-development/ict-engi-fact-rese-muta/SKILL.md`.
- Proof-aware objective snapshot after the fix:
  `/tmp/ict-engine-closed-loop-loophole-audit-codex-20260529T165649+0800/objective-snapshot-after-workdoc-terminal-fix/objective_closure_snapshot.json`.
  It remained `not_complete` with blockers `done_definition_not_completion_ready`,
  `same_tree_practical_closure_unproven`, and `release_readiness_blocked`.
  The factor-closure child was `pass`, but `same_tree_practical_closure` stayed
  `null`; done-definition/release proofs were rejected as `proof_head_mismatch`
  after the current source edit.

## 2026-05-29T17:15+0800 Verification

- RED:
  `python3 -m unittest support.scripts.tests.test_factor_claim_terminalization_audit.FactorClaimTerminalizationAuditTest.test_build_report_keeps_active_workdoc_when_nonterminal_tdd_decision_present -v`
  failed before the implementation with `active_claims 0 != 1`.
- GREEN:
  `python3 -m unittest support.scripts.tests.test_factor_claim_terminalization_audit.FactorClaimTerminalizationAuditTest.test_build_report_keeps_active_workdoc_when_nonterminal_tdd_decision_present support.scripts.tests.test_factor_claim_terminalization_audit.FactorClaimTerminalizationAuditTest.test_build_report_treats_terminal_write_surface_workdoc_as_terminalized -v`
  ran `2/2 OK`.
- `python3 -m py_compile support/scripts/factor_claim_terminalization_audit.py support/scripts/tests/test_factor_claim_terminalization_audit.py`
  passed.
- `python3 -m unittest support.scripts.tests.test_factor_claim_terminalization_audit -v`
  ran `87/87 OK`.
- `python3 -m unittest support.scripts.tests.test_objective_closure_snapshot support.scripts.tests.test_done_definition_audit -v`
  ran `69/69 OK`.
- `python3 support/scripts/factor_claim_terminalization_audit.py --compact --portable-paths`
  returned factor closure `status=pass` with no active claims or live factor
  processes, but still `promotion_allowed_true=0`, `trade_usable_true=0`, and
  `same_tree_practical_closure=null`.
- Superseding current-occupancy recheck at 2026-05-29T17:19+0800 returned
  `status=needs_attention`, `active_claims=7`,
  `fresh_active_claims_without_live_process=5`,
  `wait_only_active_claims_without_live_process=1`, `live_factor_processes=1`,
  `promotion_allowed_true=0`, `trade_usable_true=0`, and
  `same_tree_practical_closure=null`. The live root was
  `/tmp/ict-engine-tomac-es-generic-mtf-regime-screen-20260529T171516+0800`
  with PID `39022`, started by another owner while this parser-fix slice was
  being closed. Do not launch a sibling provider/AQ/TOMAC lane until those fresh
  claims and live runtime terminalize.

## 2026-05-29T17:15+0800 Decision

- Commit the narrow claim-audit/workdoc-terminal parser fix plus regression and
  this tracker update.
- Do not claim objective completion. There is still no validated same-tree
  practical closure packet, no `trade_usable=true`, and no
  `promotion_allowed=true` evidence.
- Do not launch a new factor lane from this audit-only claim. Future work should
  start from a fresh compact claim audit and wait for the 17:19 fresh/live
  owners to clear before either producing a validated same-tree practical
  closure packet or fixing the next named source/readiness blocker. Do not reuse
  Python-only screen evidence as promotion proof.

## 2026-05-29T17:54+0800 Continuation Evidence

- Current no-launch audit workdoc:
  `/tmp/ict-engine-closed-loop-loophole-audit-codex-20260529T175446+0800/workdoc.md`.
- Current no-launch audit claim:
  `/tmp/ict-engine-agent-claims/board-b-factor-refinement/20260529T175446+0800-codex-closed-loop-loophole-audit.claim`.
- Fresh compact claim audit reports `status=pass`, `active_claims=0`,
  `valid_active_claims=0`, `invalid_active_claims=0`,
  `live_factor_processes=0`, `promotion_allowed_true=0`,
  `trade_usable_true=0`, and `same_tree_practical_closure=null`.
- Focused process scan for ict-engine/Auto-Quant/TOMAC/IBKR/factor commands
  returned no matching live process rows after excluding the scan commands.
- This clears runtime collision for source inspection only. It does not prove
  practical closure, promotion, or trade usability.

## 2026-05-29T20:12+0800 Continuation Evidence

- Current no-launch audit workdoc:
  `/tmp/ict-engine-closed-loop-loophole-audit-codex-20260529T200851+0800/workdoc.md`.
- Current no-launch audit claim:
  `/tmp/ict-engine-agent-claims/board-b-factor-refinement/20260529T200851+0800-codex-closed-loop-loophole-audit.claim`.
- Current HEAD:
  `a101b0ab7e5680bbf8e73972c88788d3067d2bb1`
  (`Require policy lifecycle for practical closure`).
- Fresh compact factor audit:
  `/tmp/ict-engine-current-factor-audit-after-auditclaim-20260529T201250+0800.json`.
  It reports `status=needs_attention`, `active_claims=1`,
  `valid_active_claims=1`, `invalid_active_claims=0`,
  `coordination_only_active_claims=3`, `live_factor_processes=1`,
  `promotion_allowed_true=0`, `trade_usable_true=0`, and
  `same_tree_practical_closure=null`. The audit-only claim from this slice is
  classified as coordination-only and does not pollute factor closure.
- Fresh done-definition readback:
  `/tmp/ict-engine-current-done-definition-20260529T201250+0800.json`.
  It reports `status=pass` but `completion_ready=false` with skipped heavy
  gates: `cargo_check_all_targets`, `cargo_clippy_all_targets_deny_warnings`,
  `cargo_test`, and `smoke_acceptance_tmp_state`.
- Fresh release-readiness readback:
  `/tmp/ict-engine-current-release-readiness-20260529T201250+0800.json`.
  It reports `status=needs_fix` with unresolved
  `worktree_clean_for_release` and `source_origin_matches_selected_source`.
- Fresh objective snapshot:
  `/tmp/ict-engine-objective-closure-current-20260529T201250+0800/objective_closure_snapshot.json`.
  It reports `summary.status=not_complete`, `completion_proven=false`,
  blockers `done_definition_not_completion_ready`, `factor_closure_blocked`,
  and `release_readiness_blocked`, plus manual requirements
  `same_tree_practical_closure_packet` and `truthful_completion_commit`.
- The factor-closure queue head is the live 15Y TOMAC external strategy mining
  runtime under
  `/tmp/ict-engine-tomac-15y-external-strategy-mining-20260529T192702+0800`;
  do not launch a sibling factor/provider/AQ lane while this live owner remains
  active.
- The snapshot correctly preserves quarantined untracked source debt instead of
  hiding it behind pass-state source gates:
  practical-admission untracked debt `153` files / `268` violations, and
  await-launch untracked debt `46` files / `46` violations. Tracked violation
  counts remain `0`, so this is dirty-worktree/release residue, not practical
  closure evidence.

## 2026-05-29T20:12+0800 Decision

- Do not mark the objective complete. Current evidence directly contradicts
  completion: there is no validated `same_tree_practical_closure` packet, no
  `promotion_allowed_true`, no `trade_usable_true`, live factor runtime remains
  active, heavy done-definition gates were skipped, and release readiness is
  blocked by dirty/source-origin gates.
- Do not launch provider, IBKR, Auto-Quant, TOMAC, paper/sim, or live runtime
  from this audit-only claim.
- Continue no-launch loophole review against evidence-packet cooperation,
  compact parent/child summaries, and source/readback validators while the live
  factor runtime is occupied.

## 2026-05-29T20:59+0800 Factor-Closure Blocker Detail Fix

- Current HEAD for this slice:
  `ce5e00ab1cb0857d15e567ec2154bb6895fd6fcf`
  (`Add Markov transition evidence aggregation`).
- Root cause: `objective_closure_snapshot.py` named the parent blocker
  `factor_closure_blocked`, but the parent `summary.blocker_details` did not
  preserve the compact child factor-closure details. A reader had to open the
  child factor audit to learn active/live counts, coordination-only count,
  action queue roots/claims, owner/actionability groups, and next action.
- Fix: added a compact `factor_closure_blocked` detail object to the parent
  objective snapshot. It carries `status`, active/coordination-only/invalid
  counts, live process count, blocking reasons, attention counts/groups,
  `action_queue`, and `next_action`.
- RED evidence: in a temporary detached worktree at
  `/tmp/ict-engine-redcheck-factor-detail-20260529T2102`, applying only the new
  regression on old `HEAD=ce5e00ab` and running
  `python3 -m unittest support.scripts.tests.test_objective_closure_snapshot.ObjectiveClosureSnapshotTest.test_summarize_snapshot_includes_factor_closure_blocker_details -v`
  failed with `KeyError: 'factor_closure_blocked'`.
- GREEN evidence before this doc update:
  `python3 -m unittest support.scripts.tests.test_objective_closure_snapshot.ObjectiveClosureSnapshotTest.test_summarize_snapshot_includes_factor_closure_blocker_details -v`
  passed.
- Related regression evidence before this doc update:
  `python3 -m unittest support.scripts.tests.test_objective_closure_snapshot -v`
  ran `41/41 OK`.
- Compile evidence before this doc update:
  `python3 -m py_compile support/scripts/objective_closure_snapshot.py support/scripts/tests/test_objective_closure_snapshot.py`
  passed.
- Live parent snapshot after the code fix:
  `/tmp/ict-engine-objective-closure-current-after-factor-blocker-detail-20260529T2054+0800/objective_closure_snapshot.json`.
  The command exited non-zero because the full objective is still not complete,
  which is the expected fail-closed state. Its `summary.blockers` are
  `done_definition_not_completion_ready`, `factor_closure_blocked`, and
  `release_readiness_blocked`; manual requirements remain
  `same_tree_practical_closure_packet` and `truthful_completion_commit`.
- The new parent `factor_closure_blocked` detail in that snapshot reports
  `active_claims=3`, `coordination_only_active_claims=3`,
  `invalid_active_claims=0`, `live_factor_processes=1`,
  `attention_by_actionability={fresh_active_without_live_process: 2,
  live_runtime_owner: 1}`, and queue head
  `pid=23959`, run root
  `ict-engine-tomac-ym-donchian-cadence-lift-20260529T204210+0800`.
- Runtime skill sync: updated
  `/Users/thrill3r/.hermes/skills/software-development/ict-engine-maintenance-loop/SKILL.md`
  so future objective snapshots that name `factor_closure_blocked` preserve
  compact reusable blocker detail in the parent packet.
- Scope guard: current dirty changes in
  `support/scripts/factor_claim_terminalization_audit.py` and
  `support/scripts/tests/test_factor_claim_terminalization_audit.py` are a
  separate market-data-provenance/return-sanity practical-closure gate slice and
  are not staged by this objective-snapshot blocker-detail commit.

## 2026-05-29T20:59+0800 Decision

- Commit only the parent objective-snapshot blocker-detail fix, its regression,
  and this tracking update.
- Do not mark the full objective complete. Current evidence still has no
  validated same-tree practical closure packet, no trade-usable factor count,
  skipped heavy done-definition gates, release readiness blockers, and live or
  fresh factor-closure owners.
- Do not launch provider, IBKR, Auto-Quant, TOMAC, paper/sim, live runtime, or
  sibling factor work from this audit-only claim.
