# 2026-05-27 Objective Requirement Evidence Matrix

Owner: Codex
Status: active
Route: `sd/ict-engine-maintenance-loop`

## Objective Under Audit

Audit whether `ict-engine` has actually completed all of the following on the
current tree:

1. optimize factor training direction;
2. ensure trained profitability factors still work through each closed-loop
   stage in practical runtime, not only in training;
3. ensure training-time and post-training changes improve the closed loop
   rather than bypassing or weakening it;
4. keep durable progress tracking;
5. commit only when completion is truthfully verified.

## Current-Turn Authority

Fresh readbacks gathered in this continuation:

- `python3 support/scripts/done_definition_audit.py --compact --output /tmp/ict-engine-goal-20260527-done-live.json`
- `python3 support/scripts/factor_claim_terminalization_audit.py --compact`
- `python3 support/scripts/release_readiness_audit.py --compact --check-remotes`
- `python3 support/scripts/objective_closure_snapshot.py --compact --check-remotes --output-dir /tmp/ict-engine-goal-20260527-closure-snapshot-current6`
- `python3 support/scripts/objective_closure_snapshot.py --compact --check-remotes --output-dir /tmp/ict-engine-goal-20260528-codex-live-snapshot`
- `python3 support/scripts/factor_claim_terminalization_audit.py --compact --portable-paths --output /tmp/ict-engine-goal-20260528-factor-before-claim-close.json`
- `python3 support/scripts/objective_closure_snapshot.py --compact --check-remotes --output-dir /tmp/ict-engine-goal-20260528-continuation-snapshot-after-multilive`
- `python3 -m unittest support.scripts.tests.test_factor_claim_terminalization_audit -v`
- `python3 -m unittest support.scripts.tests.test_objective_closure_snapshot -v`
- `python3 -m unittest support.scripts.tests.test_release_readiness_audit -v`
- `python3 -m unittest support/scripts/research/tests/test_purged_cv_backtest_guard.py support/scripts/research/tests/test_tomac_tod_balanced_trade_label_sidecar.py support/docs/experiments/actionable-regime-confidence/scripts/test_tomac_tod_balanced_practical_admission_prep_v1.py -v`
- `python3 -m unittest support/scripts/research/tests/test_simulated_feedback_admission_guard.py -v`
- `python3 support/scripts/research/tomac_tod_balanced_trade_label_sidecar.py --exact-root /tmp/ict-engine-tomac-tod-balanced-practical-repair-20260526T214903+0800/top1965_comp40_floor50_exact_suppressed --output-dir /tmp/ict-engine-tomac-practical-closure-20260527T165046+0800/sidecar-rerun`
- `cargo test --quiet workflow_factor_profitability_lifecycle -- --nocapture`
- `cargo test --quiet execution_tree_closed_loop_branch_admission_keeps_strict_trend_pullback_wait_for_reversion_observe_only -- --nocapture`
- `python3 -m unittest support.scripts.tests.test_release_readiness_audit -v`
- `python3 -m unittest support.scripts.research.tests.test_factor_candidate_pack -v`
- `python3 -m unittest support.scripts.research.tests.test_factor_candidate_resolver -v`
- `python3 support/scripts/research/factor_candidate_resolver.py --list-buildable --output-format json`
- `python3 support/scripts/research/factor_candidate_resolver.py --list-buildable --include-legacy-buildable --output-format json`

Current-turn command truth at the time this matrix was written:

- 2026-05-28 coordinated refresh:
  `/tmp/ict-engine-goal-20260528-closure-snapshot-current1/objective_closure_snapshot.json`
  supersedes the older same-day blocker counts below for live coordination.
  It reports `status=not_complete`, blockers
  `done_definition_not_completion_ready`, `factor_closure_blocked`, and
  `release_readiness_blocked`. The factor child reports
  `status=needs_attention`, `active_claims=2`, `live_factor_processes=0`,
  `active_claims_without_live_process=2`, `stale_safe_takeover_candidates=2`,
  `promotion_allowed_true=0`, and `trade_usable_true=0`. Release readiness
  still fails `worktree_clean_for_release` and `remote_readback`; the light
  done-definition audit still has `completion_ready=false` until heavy gates are
  rerun.
- 2026-05-28 immediate post-refresh drift check:
  `python3 support/scripts/factor_claim_terminalization_audit.py --compact`
  then reported `status=needs_attention`, `active_claims=5`,
  `live_factor_processes=3`, `active_claims_without_live_process=2`,
  `blocking_reasons=[active_claims, live_factor_processes]`,
  `promotion_allowed_true=0`, and `trade_usable_true=0`. Treat the coordinated
  snapshot as the packetized audit bundle, but treat this later compact audit as
  the current live-occupancy truth for collision decisions.

- 2026-05-28 stale live-exit guard:
  the WPR/reference-Hurst live process had a current running PID but an older
  `checks/tomac_aq.exit=1` and stderr file from a prior failed attempt. Current
  source registration was proven by
  `python3 -m unittest support.docs.experiments.actionable-regime-confidence.scripts.test_tomac_index_futures_clean_aq.TomacIndexFuturesCleanAqTest.test_candidate_specs_can_select_reference_hurst_profile_range_compression_release_family -v`
  (`OK`), so the error artifact was stale rather than current-source truth.
  `support/scripts/factor_claim_terminalization_audit.py` now marks compact live
  process `exit_file_state=stale_for_process` when the inferred exit file
  predates the live process start. Verification:
  `python3 -m unittest support.scripts.tests.test_factor_claim_terminalization_audit -v`
  passed `60/60`, and `/tmp/ict-engine-goal-20260528-factor-staleexit-check.json`
  showed the WPR live root with `exit_file_state=stale_for_process`.

- 2026-05-28 live snapshot refresh:
  `/tmp/ict-engine-goal-20260528-codex-live-snapshot/objective_closure_snapshot.json`
  is the newest same-turn parent packet checked in this continuation. It is
  still `summary.status=not_complete` with the same blocker classes:
  `done_definition_not_completion_ready`, `factor_closure_blocked`, and
  `release_readiness_blocked`. It also proves the parent packet is now
  action-ready without nested child inspection: `child_report_age_seconds`
  showed fresh children (`done_definition=9s`, `factor_closure=8s`,
  `release_readiness=0s`), and `summary.prioritized_next_actions` named the
  stale-safe factor queue head plus the two release gates.

- 2026-05-28 factor child refresh:
  `/tmp/ict-engine-goal-20260528-factor-before-claim-close.json` reported
  `status=needs_attention`, `active_claims=2`, `live_factor_processes=0`,
  `active_claims_without_live_process=2`,
  `wait_only_active_claims_without_live_process=0`,
  `stale_safe_takeover_candidates=1`, `promotion_allowed_true=0`, and
  `trade_usable_true=0`. The later stale-safe queue head was
  `20260527T231100+0800-codex-tomac-wpr-adx-reference-hurst-profile-range-compression-release-launch.claim`.

- Collision readback:
  while inspecting the earlier liquidity-pool queue head, a concurrent codex
  process created a fresh takeover at
  `/tmp/ict-engine-agent-claims/board-b-factor-refinement/20260528T005835+0800-codex-tomac-liquidity-pool-context-practical-takeover.claim`.
  This continuation therefore did not terminalize the older liquidity-pool
  claim; the correct next action is to rerun the coordinated snapshot after the
  takeover terminalizes or inspect the remaining WPR/reference-Hurst queue head
  if it is still stale-safe.

- 2026-05-28 multi-live parent action refresh:
  `/tmp/ict-engine-goal-20260528-continuation-snapshot-after-multilive/objective_closure_snapshot.json`
  remains `summary.status=not_complete`, but it now proves the coordinated
  parent packet lists both live factor runtime heads directly in
  `summary.prioritized_next_actions`: liquidity-pool-context PID `35142` and
  WPR/reference-Hurst PID `35854`. The factor child still reports
  `active_claims=2`, `live_factor_processes=2`,
  `active_claims_without_live_process=0`, `promotion_allowed_true=0`, and
  `trade_usable_true=0`, so this is an evidence-pack coordination improvement,
  not completion proof.

- coordinated closure snapshot:
  `/tmp/ict-engine-goal-20260527-closure-snapshot-current6/objective_closure_snapshot.json`
  now binds the canonical quickstart chain plus the current done/factor/release
  child audit outputs into one coordinated `/tmp` evidence bundle; it also
  records child report timestamps and exact unresolved gates so later prose does
  not need to hand-copy volatile counts. The parent snapshot and the factor
  child compact payload are now both packet-safe for clone portability:
  `audit_commands[*][0]="python3"`, child evidence filenames are relative, and
  the factor child collapses local tmp runtime paths into labels such as
  `claims_dir="ict-engine-agent-claims/board-b-factor-refinement"` and
  `run_root="ict-engine-..."`
- done-definition light:
  `status=pass`, `completion_ready=false`, `quickstart_surface=pass`,
  `evidence_level=partial_skipped_gates`, heavy gates skipped by default
- factor closure:
  latest truth is snapshot-owned and time-variant; the stable current fact is
  `status=needs_attention` with unresolved active-claim debt, while precise
  counts and `blocking_reasons` must be read from the snapshot child. The
  latest focused factor audit now makes the debt shape explicit:
  `active_claims=5`, `live_factor_processes=1`,
  `active_claims_without_live_process=4`,
  `wait_only_active_claims_without_live_process=0`,
  `stale_safe_takeover_candidates=1`,
  `attention_by_actionability={active_claim_debt:3, live_runtime_owner:1,
  stale_safe_takeover_candidate:1}`
- release readiness:
  latest truth is snapshot-owned and time-variant; the stable current fact is
  `status=needs_fix`, while the exact unresolved gate set must be read from the
  snapshot child
- same-root TOMAC practical rerun:
  `label_count=1633`, `terminal_trade_count=1633`,
  `trade_count_parity=true`, `purged_cv_gate=reject`,
  bounded provider parity is now proven for `MNQ/MYM/MGC`, and the remaining
  downstream blockers are
  `frequency.max_gap_days_gt_allowed:350.00>3.00`,
  `raw_scored_mature_rows_lt_30`, `production_validation_rows_lt_30`,
  `observation_validation_rows_lt_30`,
  `execution_readiness_lt_0.65`,
  `transition_hazard_gte_0.60`,
  `actionable_false`
- focused TOMAC closure suites:
  sidecar/practical-prep bundle passed `10/10`;
  `test_simulated_feedback_admission_guard` passed `9/9`
- sidecar owner hydration fix:
  the balanced-TOD sidecar now hydrates downstream validation/readiness truth
  from sibling exact artifacts instead of hard-coding zero placeholders; the
  real rerun preserved the actual downstream state for this root
  (`raw_scored_mature_rows=1`, `production_validation_rows=1`,
  `observation_validation_rows=0`,
  `execution_readiness=0.4606046164602364`,
  `transition_hazard=0.6248959443126174`)
- bounded provider parity proof:
  `tomac_tod_balanced_provider_parity_probe.py --duration '1 D' --request-timeout 20`
  now writes `checks/provider_parity_probe.json` with
  `decision=bounded_provider_parity_recent_rows_present`
- frequency owner fix:
  the guard now evaluates daily trade-count caps per pair when `pair` is
  present; the aggregate `5/day` artifact is gone and only the real
  pair-scoped long-gap blocker remains
- heavy done-definition:
  not rerun in this continuation, so completion proof remains partial
- focused lifecycle tests:
  `workflow_factor_profitability_lifecycle` passed (`3` tests)
- focused execution-tree test:
  `execution_tree_closed_loop_branch_admission_keeps_strict_trend_pullback_wait_for_reversion_observe_only`
  passed (`1` test)
- focused Python suites:
  `test_factor_claim_terminalization_audit` passed (`59/59`);
  `test_objective_closure_snapshot` passed (`9/9`);
  `test_release_readiness_audit` passed (`17/17`);
  `test_factor_candidate_pack` passed (`17/17`);
  `test_factor_candidate_resolver` passed (`19/19`)
- training-direction list surface:
  default `--list-buildable` now returns `buildable_count=0`,
  `legacy_excluded_count=8`; the human surface now mirrors that exclusion count
  and prints an explicit opt-in hint; explicit
  `--include-legacy-buildable` returns `buildable_count=8`,
  `inspection_only_count=8`

## Requirement Matrix

| Requirement | Authoritative proof target | Current evidence | Verdict |
|---|---|---|---|
| Consumer first-run path is coherent and token-friendly | repo docs + quickstart parity gate + first-run command order agreement | `AGENT.md` canonical order is aligned with current public docs; `done_definition_audit.py` light and heavy reports both keep `quickstart_surface=pass` under a fully green done-definition bundle | `proven_for_current_tree` |
| Consumer UX no longer overstates trade readiness | workflow/lifecycle tests plus live-plane semantics in source/readback | focused lifecycle test passed; current trackers still explicitly keep `promotion_allowed=false` and `trade_usable=false` unless live plane proves otherwise | `proven_for_fail_closed_semantics` |
| Evidence packs are lightweight and reusable | compact audit/doc surfaces plus minimal blocker set in trackers | current trackers are compact and current-turn blocker wording was refreshed; quickstart/doc parity is machine-checked; focused provenance/reusability suites for release readback and candidate-pack exports all passed in this continuation | `partially_proven_but_stronger` |
| Evidence packs coordinate correctly across surfaces | same-tree agreement between done/factor/release trackers and lifecycle semantics | `objective_closure_snapshot.py` now emits one coordinated `/tmp` bundle naming the canonical quickstart chain, child evidence paths, child report timestamps, exact blocker surfaces, child next actions, child age, and all current live factor heads up to the compact cap. The parent snapshot and factor child compact packet are both packet-safe for reuse, while `factor_claim_terminalization_audit.py` still exposes whether active-claim debt actually owns live runtime (`active_claims_without_live_process`) and how much of that debt is merely wait-only. Because factor claims and release gates can change within minutes, the durable invariant is not any single copied count but the existence of one authoritative snapshot root that names the latest factor and release child truth. Practical closure is still fragmented across packet roots and no single green end-to-end closure packet exists on this tree | `partially_proven_but_not_complete` |
| Training-only positives are not misreported as live-ready | lifecycle/readiness tests plus factor audit practical flags | focused lifecycle test passed; fresh factor audit still shows `promotion_allowed_true=0`, `trade_usable_true=0` | `proven_for_current_fail_closed_state` |
| Execution-tree closed loop cannot bypass the live plane | focused execution-tree test + current practical flags | observe-only strict-trend-pullback test passed; current factor audit still has zero trade-usable lanes | `proven_for_tested_path`, `not_proven_end_to_end` |
| At least one rooted profitability-factor chain is currently proved end-to-end on this exact tree | fresh same-tree provider -> analyze -> pre-bayes -> BBN -> ranker -> execution -> feedback evidence packet with practical readiness verdict | no such current-turn green packet exists; the coordinated closure snapshot remains red on factor closure, and the strongest TOMAC rerun still fails on purged-CV plus downstream validation/readiness gates | `contradicted_by_current_state` |
| Release/commit readiness for a truthful completion commit | clean selected source slice + release audit + exact version/tag availability | release audit currently fails `worktree_clean_for_release` and `remote_readback`; the shared tree remains broad and dirty, and tag availability cannot be trusted until the release mirror readback works again | `contradicted_by_current_state` |
| Durable tracking doc exists and stays current | repo-local dated doc updated from fresh command truth | this matrix plus the two 2026-05-27 tracker docs exist and were refreshed in this continuation | `proven` |

## Strongest Current Contradictions

### C-001: practical closure is still blocked by unresolved active claims

- Evidence:
  the coordinated closure snapshot still shows factor closure blocked; the
  latest focused factor audit after takeover drift makes the blocker shape explicit:
  `active_claims=5`, `live_factor_processes=3`,
  `active_claims_without_live_process=2`,
  `wait_only_active_claims_without_live_process=0`
- Consequence:
  there is no honest basis to say the repo has already closed the objective for
  real/practical use

### C-002: a completion commit would still be false

- Evidence:
  the coordinated closure snapshot still shows release readiness blocked; exact
  unresolved gate names are time-variant and should be read from the snapshot
  child rather than copied into this table
- Consequence:
  even if a narrow docs slice could be committed, it would not be the
  user-requested “finished and then commit” state

## Reasonable Next Actions

1. Re-run this matrix after the 5 active claims and 3 live factor processes are reduced to a truthful
   closure surface or explicitly externalized into their own evidence packets.
2. Only attempt a completion commit after a clean selected slice or clean export
   exists and the release audit turns green for the intended version/tag.
3. Keep treating current consumer/readback improvements as real but partial:
   they improve truthfulness and UX, but they do not yet prove full objective
   completion.
4. Keep the human `--list-buildable` surface aligned with the JSON surface so
   operators cannot mistake `buildable_count=0` for “no hidden exclusions”.
5. Keep distinguishing the now-green done-definition bundle from the still-red
   factor/release blockers; only the latter remain active contradictions.
6. Cite the coordinated closure snapshot for blocker names and timestamps before
   copying any factor/release numbers into follow-up prose.
7. Use the new factor-claim debt split to externalize or terminalize claims
   that are active but do not own live runtime before treating Board B closure
   as a runtime problem.
8. The current stale-safe queue heads are
   `20260527T231247+0800-codex-tomac-liquidity-sweep-adx-liquidity-pool-context-reopen-await-launch.claim`
   and
   `20260527T231100+0800-codex-tomac-wpr-adx-reference-hurst-profile-range-compression-release-launch.claim`;
   inspect those ownership packets before treating either as a real still-active
   lane.
9. Treat Board B closure as concurrently mutating state: externalizing old debt
   can still lose ground if new active claims or live runtimes appear in the
   same turn, so every closure claim needs a fresh rerun immediately before the
   assertion.

## Current Answer

No. I do not have 100% confidence that the objective is complete on the current
tree. Current evidence proves some fail-closed UX/readback properties, but it
also directly disproves practical closure and release/commit closure.
