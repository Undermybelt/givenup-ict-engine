# 2026-05-27 Objective Requirement Evidence Matrix

Owner: Codex
Status: active
Route: `sd/ict-engine-maintenance-loop`

## Objective Under Audit

Audit whether `ict-engine` has actually completed all of the following on the
current tree:

1. optimize consumer UX;
2. optimize evidence-pack lightness and reusability;
3. improve coordination between evidence packs;
4. prove whether the resulting closed loop can actually help practical/live use;
5. keep a durable tracking document;
6. commit only when completion is truthfully verified.

## Current-Turn Authority

Fresh readbacks gathered in this continuation:

- `python3 support/scripts/done_definition_audit.py --compact --output /tmp/ict-engine-goal-20260527-done-live.json`
- `python3 support/scripts/factor_claim_terminalization_audit.py --compact`
- `python3 support/scripts/release_readiness_audit.py --compact --check-remotes`
- `cargo test --quiet workflow_factor_profitability_lifecycle -- --nocapture`
- `cargo test --quiet execution_tree_closed_loop_branch_admission_keeps_strict_trend_pullback_wait_for_reversion_observe_only -- --nocapture`
- `python3 -m unittest support.scripts.tests.test_release_readiness_audit -v`
- `python3 -m unittest support.scripts.research.tests.test_factor_candidate_pack -v`
- `python3 -m unittest support.scripts.research.tests.test_factor_candidate_resolver -v`
- `python3 support/scripts/research/factor_candidate_resolver.py --list-buildable --output-format json`
- `python3 support/scripts/research/factor_candidate_resolver.py --list-buildable --include-legacy-buildable --output-format json`

Current-turn command truth at the time this matrix was written:

- done-definition light:
  `status=pass`, `completion_ready=false`, `quickstart_surface=pass`,
  heavy gates skipped by default
- factor closure:
  `status=needs_attention`, `active_claims=9`, `invalid_active_claims=0`,
  `live_factor_processes=1`, `promotion_allowed_true=0`,
  `trade_usable_true=0`
- release readiness:
  `status=needs_fix`, unresolved
  `worktree_clean_for_release`,
  `source_origin_matches_selected_source`,
  `release_version_tag_available`, with `source_ahead_of_origin=43` and local
  `Cargo.toml version=0.1.7` colliding with existing release tag `v0.1.7`
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
  `test_factor_candidate_resolver` passed (`18/18`)
- training-direction list surface:
  default `--list-buildable` now returns `buildable_count=0`,
  `legacy_excluded_count=8`; explicit
  `--include-legacy-buildable` returns `buildable_count=8`,
  `inspection_only_count=8`

## Requirement Matrix

| Requirement | Authoritative proof target | Current evidence | Verdict |
|---|---|---|---|
| Consumer first-run path is coherent and token-friendly | repo docs + quickstart parity gate + first-run command order agreement | `AGENT.md` canonical order is aligned with current public docs; `done_definition_audit.py` light and heavy reports both keep `quickstart_surface=pass` under a fully green done-definition bundle | `proven_for_current_tree` |
| Consumer UX no longer overstates trade readiness | workflow/lifecycle tests plus live-plane semantics in source/readback | focused lifecycle test passed; current trackers still explicitly keep `promotion_allowed=false` and `trade_usable=false` unless live plane proves otherwise | `proven_for_fail_closed_semantics` |
| Evidence packs are lightweight and reusable | compact audit/doc surfaces plus minimal blocker set in trackers | current trackers are compact and current-turn blocker wording was refreshed; quickstart/doc parity is machine-checked; focused provenance/reusability suites for release readback and candidate-pack exports all passed in this continuation | `partially_proven_but_stronger` |
| Evidence packs coordinate correctly across surfaces | same-tree agreement between done/factor/release trackers and lifecycle semantics | current trackers now agree on live blockers, and the default candidate-pack listing now fail-closes away from legacy synthesized lifecycle surfaces; practical closure is still fragmented across multiple packet roots and no single green end-to-end closure packet exists on this tree | `not_fully_proven` |
| Training-only positives are not misreported as live-ready | lifecycle/readiness tests plus factor audit practical flags | focused lifecycle test passed; fresh factor audit still shows `promotion_allowed_true=0`, `trade_usable_true=0` | `proven_for_current_fail_closed_state` |
| Execution-tree closed loop cannot bypass the live plane | focused execution-tree test + current practical flags | observe-only strict-trend-pullback test passed; current factor audit still has zero trade-usable lanes | `proven_for_tested_path`, `not_proven_end_to_end` |
| At least one rooted profitability-factor chain is currently proved end-to-end on this exact tree | fresh same-tree provider -> analyze -> pre-bayes -> BBN -> ranker -> execution -> feedback evidence packet with practical readiness verdict | no such current-turn green packet exists; factor audit is still red with 9 active claims, 1 live factor process, and zero `trade_usable_true` lanes | `contradicted_by_current_state` |
| Release/commit readiness for a truthful completion commit | clean selected source slice + release audit + exact version/tag availability | release audit currently fails `worktree_clean_for_release`, `source_origin_matches_selected_source`, `release_version_tag_available`; shared tree remains broad and dirty, `source_ahead_of_origin=43`, and `Cargo.toml version=0.1.7` collides with existing release tag `v0.1.7` | `contradicted_by_current_state` |
| Durable tracking doc exists and stays current | repo-local dated doc updated from fresh command truth | this matrix plus the two 2026-05-27 tracker docs exist and were refreshed in this continuation | `proven` |

## Strongest Current Contradictions

### C-001: practical closure is still blocked by unresolved active claims

- Evidence:
  `factor_claim_terminalization_audit.py --compact` currently reports
  `active_claims=9`, `invalid_active_claims=0`, `live_factor_processes=1`
- Consequence:
  there is no honest basis to say the repo has already closed the objective for
  real/practical use

### C-002: a completion commit would still be false

- Evidence:
  `release_readiness_audit.py --compact --check-remotes` currently fails
  `worktree_clean_for_release`,
  `source_origin_matches_selected_source`,
  `release_version_tag_available`
- Consequence:
  even if a narrow docs slice could be committed, it would not be the
  user-requested “finished and then commit” state

## Reasonable Next Actions

1. Re-run this matrix after the 9 active claims are reduced to a truthful
   closure surface or explicitly externalized into their own evidence packets.
2. Only attempt a completion commit after a clean selected slice or clean export
   exists and the release audit turns green for the intended version/tag.
3. Keep treating current consumer/readback improvements as real but partial:
   they improve truthfulness and UX, but they do not yet prove full objective
   completion.
4. Keep distinguishing the now-green done-definition bundle from the still-red
   factor/release blockers; only the latter remain active contradictions.

## Current Answer

No. I do not have 100% confidence that the objective is complete on the current
tree. Current evidence proves some fail-closed UX/readback properties, but it
also directly disproves practical closure and release/commit closure.
