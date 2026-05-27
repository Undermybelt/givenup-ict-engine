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
- `python3 support/scripts/objective_closure_snapshot.py --compact --check-remotes --output-dir /tmp/ict-engine-goal-20260527-closure-snapshot`
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

- coordinated closure snapshot:
  `/private/tmp/ict-engine-goal-20260527-closure-snapshot/objective_closure_snapshot.json`
  now binds the canonical quickstart chain plus the current done/factor/release
  child audit outputs into one coordinated `/tmp` evidence bundle; it also
  records child report timestamps and exact unresolved gates so later prose does
  not need to hand-copy volatile counts
- done-definition light:
  `status=pass`, `completion_ready=false`, `quickstart_surface=pass`,
  `evidence_level=partial_skipped_gates`, heavy gates skipped by default
- factor closure:
  latest truth is snapshot-owned and time-variant; the stable current fact is
  `status=needs_attention` with unresolved active-claim debt, while precise
  counts and `blocking_reasons` must be read from the snapshot child
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
| Evidence packs coordinate correctly across surfaces | same-tree agreement between done/factor/release trackers and lifecycle semantics | `objective_closure_snapshot.py` now emits one coordinated `/tmp` bundle naming the canonical quickstart chain, child evidence paths, child report timestamps, and exact blocker surfaces. Because factor claims and release gates can change within minutes, the durable invariant is not any single copied count but the existence of one authoritative snapshot root that names the latest factor and release child truth. Practical closure is still fragmented across packet roots and no single green end-to-end closure packet exists on this tree | `partially_proven_but_not_complete` |
| Training-only positives are not misreported as live-ready | lifecycle/readiness tests plus factor audit practical flags | focused lifecycle test passed; fresh factor audit still shows `promotion_allowed_true=0`, `trade_usable_true=0` | `proven_for_current_fail_closed_state` |
| Execution-tree closed loop cannot bypass the live plane | focused execution-tree test + current practical flags | observe-only strict-trend-pullback test passed; current factor audit still has zero trade-usable lanes | `proven_for_tested_path`, `not_proven_end_to_end` |
| At least one rooted profitability-factor chain is currently proved end-to-end on this exact tree | fresh same-tree provider -> analyze -> pre-bayes -> BBN -> ranker -> execution -> feedback evidence packet with practical readiness verdict | no such current-turn green packet exists; the coordinated closure snapshot remains red on factor closure, and the strongest TOMAC rerun still fails on purged-CV plus downstream validation/readiness gates | `contradicted_by_current_state` |
| Release/commit readiness for a truthful completion commit | clean selected source slice + release audit + exact version/tag availability | release audit currently fails `worktree_clean_for_release` and `remote_readback`; the shared tree remains broad and dirty, and tag availability cannot be trusted until the release mirror readback works again | `contradicted_by_current_state` |
| Durable tracking doc exists and stays current | repo-local dated doc updated from fresh command truth | this matrix plus the two 2026-05-27 tracker docs exist and were refreshed in this continuation | `proven` |

## Strongest Current Contradictions

### C-001: practical closure is still blocked by unresolved active claims

- Evidence:
  the coordinated closure snapshot still shows factor closure blocked; exact
  counts are time-variant and should be read from the snapshot child rather
  than copied into this table
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

1. Re-run this matrix after the 10 active claims are reduced to a truthful
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

## Current Answer

No. I do not have 100% confidence that the objective is complete on the current
tree. Current evidence proves some fail-closed UX/readback properties, but it
also directly disproves practical closure and release/commit closure.
