# Profitability Closure Root-Cause Audit

created_at: 2026-05-30T03:43:02+0800
owner: codex
agent_name: codex-profitability-closure-root-cause-audit
repo: /Users/thrill3r/projects-ict-engine/ict-engine
branch: main
status: active_read_only_then_canonical_owner_fix
promotion_allowed: false
trade_usable: false
update_goal: false

## Objective

Find why ict-engine keeps producing near-practical factor packets but no
validated trade-usable profitability factor, then fix canonical completion or
admission owners where current evidence shows a system loophole.

## Current Hard Evidence

- `python3 support/scripts/factor_claim_terminalization_audit.py --compact`
  at 2026-05-30T03:40+0800 returned `status=needs_attention`.
- `trade_usable_true=0`.
- `promotion_allowed_true=0`.
- `same_tree_practical_closure=null`.
- Blocking runtime: `/tmp/ict-engine-eur-eth-donchian-tsmom-volcarry-prep-20260530T005133+0800`
  local Python screen process is still live.
- Blocking fresh claim: `20260530T033600+0800-codex-6b-eth-boe-rate-differential-london-stoprun-vwap-reclaim-gate1.claim`.

## Constraints

- Do not launch provider, IBKR, AutoQuant, Freqtrade, paper, lifecycle, or new
  local factor screening while compact claim audit reports active claims or live
  factor processes.
- Do not use Board/current docs for lane selection.
- Preserve unrelated dirty work.
- If source changes are needed, use TDD and commit only the verified slice.
- Do not mark the active goal complete without a validated same-tree practical
  closure packet and at least one `promotion_allowed=true` and
  `trade_usable=true` backed by full lifecycle evidence.

## Plan

1. Run a read-only objective-closure snapshot into `/tmp` to capture current
   gate failures.
2. Inspect canonical owners: `objective_closure_snapshot.py`,
   `done_definition_audit.py`, `factor_claim_terminalization_audit.py`,
   `same_tree_practical_closure.py`, and
   `downstream_practical_admission_source_check.py`.
3. If the current completion output only says "no pass packet" without naming
   broken lifecycle stages, add a source-owned blocker breakdown with tests.
4. Verify focused tests and compact audits.
5. Commit the verified slice if code changed.

## Progress

- 2026-05-30T03:43:02+0800: opened tracking doc after routing and current-state
  audit. Current action is read-only closure diagnosis; no new factor runtime
  launch is allowed.
- 2026-05-30T03:44:59+0800: baseline
  `python3 support/scripts/objective_closure_snapshot.py --compact --timeout-seconds 240 --output-dir /tmp/ict-engine-goal-20260530-codex-root-cause-034302`
  exited nonzero with `completion_proven=false`. The actionable source blocker
  was one tracked practical-admission violation in
  `run_tomac_index_futures_clean_aq_v1.py`: `survives_5bps_per_side` combined
  `trades >= 30` with positive 5bps cost survival, conflating sparse-positive
  economics with sample/density readiness.
- 2026-05-30T03:47:00+0800: RED test added:
  `test_cost_survival_is_separate_from_trade_sample_floor` failed because a
  sparse but strongly cost-positive row reported `survives_5bps_per_side=false`.
- 2026-05-30T03:48:00+0800: fixed clean-AQ scoring semantics. Cost-survival
  fields now represent cost economics only. New
  `minimum_trade_sample_floor_met` carries the `trades >= 30` sample floor, and
  `gate1_survivor` still requires sample floor, density, 5bps survival,
  instrument-cost survival, win/loss diversity, and direction consistency.
- 2026-05-30T03:49:18+0800: verification passed:
  `python3 -m unittest support.docs.experiments.actionable-regime-confidence.scripts.test_tomac_index_futures_clean_aq -v`
  ran 88 tests OK;
  `python3 support/scripts/research/downstream_practical_admission_source_check.py support/docs/experiments/actionable-regime-confidence/scripts/run_tomac_index_futures_clean_aq_v1.py`
  returned `practical_admission_source_ok`; `python3 -m py_compile ...` passed;
  `python3 support/scripts/done_definition_audit.py --compact --output /tmp/ict-engine-done-definition-after-cost-density-separation.json`
  returned `status=pass`, `tracked_violation_count=0`, `fail_count=0`, with
  heavy gates skipped because this was a compact pass.
- 2026-05-30T03:50:00+0800: updated Hermes runtime skill
  `software-development/ict-engi-fact-rese-muta/SKILL.md` with the durable rule:
  cost-survival fields must not include sample size, density, cadence, or
  validation readiness; those must be separate gates.
- 2026-05-30T03:56:05+0800: post-commit objective snapshot on `355ce143`
  showed `done_definition.returncode=0`, `factor_closure.returncode=0`,
  `tracked_violation_count=0`, `active_claims=0`, and
  `live_factor_processes=0`. Remaining blockers were
  `same_tree_practical_closure_unproven`, heavy/remote release proof, and a
  stale practical-admission untracked-debt quarantine fingerprint.
- 2026-05-30T03:59:20+0800: refreshed
  `support/docs/audits/practical-admission-source-debt-quarantine.json` to the
  current reviewed untracked-debt fingerprint: `335` violations across `175`
  untracked files, sha256
  `a63ffa0e460234419a0635dc14ae154d60f4e3325f7266f1dbb4cf18d9760aa4`.
  Verification:
  `python3 support/scripts/done_definition_audit.py --compact --output /tmp/ict-engine-done-definition-after-quarantine-refresh-355ce143.json`
  returned `status=pass`, `tracked_violation_count=0`, and quarantine
  `matched=true`. This does not make the untracked wrappers release-ready or
  trade-usable; it only prevents reviewed untracked residue from being treated
  as new tracked source debt.
- 2026-05-30T04:23:46+0800: added objective-snapshot stage-gap diagnostics so
  the closure surface does not collapse every failure into a generic missing
  packet. `same_tree_practical_closure_unproven` now carries
  `missing_practical_chain_stages` and claim/runtime `blocking_context`, and is
  listed as a blocker even when `factor_closure_blocked` is also present.
  Current snapshot:
  `python3 support/scripts/objective_closure_snapshot.py --compact --timeout-seconds 240 --output-dir /tmp/ict-engine-goal-20260530-codex-after-stage-gap-blocker`
  still exits nonzero with `trade_usable_true=0`, `promotion_allowed_true=0`,
  `same_tree_practical_closure=null`, active claims blocking launch, and all
  required practical stages missing: `provider_data`, `pre_bayes`,
  `bbn_workflow`, `path_ranker`, `execution_tree`, `feedback_update`, and
  `policy_training`.
  Verification:
  `python3 -m unittest support.scripts.tests.test_objective_closure_snapshot -v`
  ran 45 tests OK;
  `python3 -m unittest support.scripts.research.tests.test_same_tree_practical_closure -v`
  ran 12 tests OK;
  `python3 -m py_compile support/scripts/objective_closure_snapshot.py support/scripts/tests/test_objective_closure_snapshot.py`
  passed.
- 2026-05-30T04:56:00+0800: identified a practical-lifecycle driver loophole
  in the NQ compound ChopFilter wrapper: explicit `--execute-driver` could be
  short-circuited by pre-existing staged command results, which made the
  wrapper summarize historical evidence instead of running the same-tree
  lifecycle driver. Added RED test
  `test_execute_driver_runs_even_when_staged_results_exist`, observed it fail
  because `run_lifecycle_driver` was not called, then changed `main()` so
  `--execute-driver` always builds and runs the lifecycle plan while default
  read-only mode still uses staged results. Also added a regression test proving
  a failed explicit driver run removes any stale same-tree closure packet rather
  than returning success from a leftover file. Verification passed:
  `python3 -m unittest support.docs.experiments.actionable-regime-confidence.scripts.test_tomac_nq_compound_trend_rrr_chopfilter_practical_lifecycle_v1 -v`
  ran 11 tests OK;
  `python3 -m py_compile support/docs/experiments/actionable-regime-confidence/scripts/run_tomac_nq_compound_trend_rrr_chopfilter_practical_lifecycle_v1.py support/docs/experiments/actionable-regime-confidence/scripts/test_tomac_nq_compound_trend_rrr_chopfilter_practical_lifecycle_v1.py`
  passed;
  `git diff --check -- support/docs/experiments/actionable-regime-confidence/scripts/run_tomac_nq_compound_trend_rrr_chopfilter_practical_lifecycle_v1.py support/docs/experiments/actionable-regime-confidence/scripts/test_tomac_nq_compound_trend_rrr_chopfilter_practical_lifecycle_v1.py`
  passed; targeted practical-admission source check returned
  `practical_admission_source_ok`.
- 2026-05-30T04:56:00+0800: current compact claim audit still blocks real
  lifecycle launch: `active_claims=1`, `fresh_active_claims_without_live_process=1`,
  `live_factor_processes=1`, `promotion_allowed_true=0`, `trade_usable_true=0`,
  and `same_tree_practical_closure=null`. Do not run the NQ practical lifecycle
  driver until the fresh CC claim and EUR/ETH live runtime clear.
- 2026-05-30T05:16:52+0800: fixed a canonical same-tree practical-closure
  validator loophole. Before this slice,
  `metrics_prove_same_tree_practical_closure()` required lifecycle and staged
  command evidence but did not require ETH/full retained session proof or a
  verified cost-model packet. A RTH-only packet, or a packet with only
  `promotion_cost_verified=true` plus a bare URL, could theoretically pass the
  canonical helper if all other booleans were true. Added strict TDD coverage
  and implementation so the helper now requires `session_scope` to normalize to
  ETH/full retained session, `rth_filter_applied=false`, retained non-RTH row
  coverage evidence, `promotion_cost_verified=true`, complete cost-model text
  fields, and structured official-source readbacks proving HTTP 200 plus
  `rate_verified`. Bare URL strings, unverified/unknown/not-rate-verified
  source markers, HTTP 403, and HTTP 404 fail closed. The helper also accepts
  common verified status text such as `verified_ibkr_official` and accepts
  `exchange` as a cost venue field when `venue_routing` is absent, avoiding an
  unnecessary false blocker for existing futures cost packets.
  Verification passed:
  `python3 -m unittest support.scripts.research.tests.test_same_tree_practical_closure -v`
  ran 16 tests OK;
  `python3 -m unittest support.scripts.tests.test_factor_claim_terminalization_audit -v`
  ran 94 tests OK;
  `python3 -m py_compile support/scripts/research/same_tree_practical_closure.py support/scripts/research/tests/test_same_tree_practical_closure.py support/scripts/factor_claim_terminalization_audit.py support/scripts/tests/test_factor_claim_terminalization_audit.py`
  passed;
  `git diff --check -- support/scripts/research/same_tree_practical_closure.py support/scripts/research/tests/test_same_tree_practical_closure.py support/scripts/tests/test_factor_claim_terminalization_audit.py`
  passed. Final same-turn compact claim audit still blocks new live/AQ
  lifecycle work: `status=needs_attention`, `active_claims=3`,
  `fresh_active_claims_without_live_process=3`, `live_factor_processes=1`,
  `promotion_allowed_true=0`, `trade_usable_true=0`, and
  `same_tree_practical_closure=null`. The live root was the MGC Kalman VWAP
  full-ladder Gate 1 run under
  `support/docs/experiments/actionable-regime-confidence/runs/20260530T051755+0800-codex-ibkr-mgc1m-kalman-vwap-slope-reclaim-full-ladder-gate1-v1`.
  Post-commit audit refreshed this to `active_claims=1`,
  `fresh_active_claims_without_live_process=1`, `live_factor_processes=1`,
  `promotion_allowed_true=0`, `trade_usable_true=0`, and
  `same_tree_practical_closure=null`; runtime launch remains blocked.
- 2026-05-30T05:40+0800: verified and retained the compact-audit live-process
  classifier fix for no-launch TOMAC prep wrappers. A `run_tomac_*_prep_v*.py`
  wrapper without `--launch` is prep/readback state, not a live factor runtime;
  counting it as live occupancy can falsely block the next safe launch window.
  Added regression coverage for the no-launch shape while preserving live
  detection for launched prep wrappers and child TOMAC/backtest/provider
  commands. Verification passed:
  `python3 -m unittest support.scripts.tests.test_factor_claim_terminalization_audit -v`
  ran 95 tests OK;
  `python3 -m py_compile support/scripts/factor_claim_terminalization_audit.py support/scripts/tests/test_factor_claim_terminalization_audit.py`
  passed;
  `git diff --check -- support/scripts/factor_claim_terminalization_audit.py support/scripts/tests/test_factor_claim_terminalization_audit.py`
  passed. Current compact claim audit still reports no practical factor:
  `promotion_allowed_true=0`, `trade_usable_true=0`, and
  `same_tree_practical_closure=null`. New launches remain blocked by fresh
  non-live active claims rather than live runtime occupancy.
- 2026-05-30T05:50+0800: fixed another compact-audit terminalization loophole.
  The NQ compound RV-stress provenance repair root already had
  `summaries/terminal_summary.json` and `checks/terminal_metrics.json` with
  `status=practical_lifecycle_fail_closed`, `promotion_allowed=false`, and
  `trade_usable=false`, but the claim stayed active because terminal-summary
  status parsing only recognized a small allowlist. Added a RED regression test
  for active claims backed by fail-closed terminal summaries, then changed the
  canonical terminal-status helper to treat non-active `*fail_closed*` terminal
  statuses as terminalized while preserving explicit `active_*`, `staged_*`,
  and `verified_*` claim states. Verification passed:
  `python3 -m unittest support.scripts.tests.test_factor_claim_terminalization_audit -v`
  ran 96 tests OK;
  `python3 -m py_compile support/scripts/factor_claim_terminalization_audit.py support/scripts/tests/test_factor_claim_terminalization_audit.py`
  passed;
  `git diff --check -- support/scripts/factor_claim_terminalization_audit.py support/scripts/tests/test_factor_claim_terminalization_audit.py`
  passed. Current compact audit no longer lists the NQ provenance-repair claim
  as active. It still reports no practical factor:
  `promotion_allowed_true=0`, `trade_usable_true=0`, and
  `same_tree_practical_closure=null`; launches remain blocked by fresh HO source
  reserve and MGC full-ladder training claims.
- 2026-05-30T06:04+0800: fixed a wrapper-stamped repo-run attribution loophole
  in the compact claim audit. The MGC quality-hold-filter claim kept
  `repo_run_root=pending_wrapper_launch_stamp` and a `/tmp` workdoc status of
  `active_created`, while the launched wrapper wrote terminal metrics under a
  stamped repo run root:
  `support/docs/experiments/actionable-regime-confidence/runs/20260530T055244+0800-codex-ibkr-mgc1m-kalman-vwap-slope-quality-hold-filter-full-ladder-gate1-v1/checks/terminal_metrics.json`.
  That terminal packet found one exact 1m cost-positive Gate 1 row,
  `ibkr-mgc-kalman-vwap-slope-quality-hold-filter-qhold-strict-1m-full-ladder-v1`,
  with `trade_count=4`, `5bps_per_side_total_profit_pct=0.01`, and
  `actual_ibkr_total_profit_pct=0.39298`, but it still correctly kept
  `promotion_allowed=false`, `trade_usable=false`, and `update_goal=false`
  because the full same-tree practical lifecycle was not proven. Added RED test
  `test_build_report_links_pending_repo_run_root_terminal_metrics_by_factor_id`,
  observed it fail with `active_claims=1`, then changed the audit to resolve
  pending `repo_run_root` sentinels to later repo run roots with matching
  terminal `factor_id` or normalized `branch_path`. Verification passed:
  `python3 -m unittest support.scripts.tests.test_factor_claim_terminalization_audit -v`
  ran 97 tests OK;
  `python3 -m py_compile support/scripts/factor_claim_terminalization_audit.py support/scripts/tests/test_factor_claim_terminalization_audit.py`
  passed; `git diff --check -- support/scripts/factor_claim_terminalization_audit.py support/scripts/tests/test_factor_claim_terminalization_audit.py`
  passed. Same-turn compact audit no longer lists the prior MGC claim as active,
  but still reports no practical factor: `promotion_allowed_true=0`,
  `trade_usable_true=0`, and `same_tree_practical_closure=null`. Runtime remains
  blocked by fresh PA/NQ/ZR/ZT source or cost reserve claims and a new live MGC
  AQ root.
- 2026-05-30T06:25+0800: fixed the next compact-audit ownership loophole:
  source/cost reserve and knowledge-reserve claims are non-runtime coordination
  work when they explicitly keep `promotion_allowed=false`,
  `trade_usable=false`, and state no provider, IBKR historical, AutoQuant,
  Freqtrade/TOMAC, paper/sim/live, downstream lifecycle, or local backtest
  launch. Before this fix, a valid low-collision reserve packet such as
  `20260530T060733+0800-codex-6l-eth-brl-selic-terms-vwap-reclaim-reserve.claim`
  was counted as `fresh_active_claims_without_live_process`, creating the loop
  `runtime blocked -> create reserve packet -> reserve packet blocks runtime`.
  Added RED/GREEN coverage for both explicit `active_source_cost_reserve` and
  generic `status: active` reserve claims, then extended the canonical
  coordination-only classifier. Verification passed:
  `python3 -m unittest support.scripts.tests.test_factor_claim_terminalization_audit -v`
  ran 99 tests OK;
  `python3 -m py_compile support/scripts/factor_claim_terminalization_audit.py support/scripts/tests/test_factor_claim_terminalization_audit.py`
  passed. Same-turn compact claim audit now reports `status=pass`,
  `active_claims=0`, `live_factor_processes=0`, `blocking_reasons=[]`, while
  still reporting no practical factor: `promotion_allowed_true=0`,
  `trade_usable_true=0`, and `same_tree_practical_closure=null`.
  A later 2026-05-30T06:27+0800 compact audit observed fresh external state
  drift after the fix: two new active claims appeared
  (`20260530T062401+0800-codex-nq-compound-rv-stress-lifecycle-driver.claim`
  and
  `20260530T062459+0800-codex-ym-eth-stoprun-compression-reclaim-local-aq-launch.claim`),
  so launch work is again blocked by current claim ownership. That newer
  blocker does not reclassify reserve packets as runtime owners, and practical
  counts remain zero.
- 2026-05-30T06:36+0800: extended the same coordination-only fix to
  no-launch source/cost prep packets. The EWZ Brazil policyflow packet
  `20260530T063159+0800-codex-ewz-brazil-policyflow-vwap-reclaim-prep.claim`
  explicitly had `status=active_source_cost_prep_no_launch`, false practical
  flags, and non-goals forbidding provider, IBKR historical, AutoQuant,
  Freqtrade/TOMAC, paper/sim/live, downstream lifecycle, and local backtest, but
  it was still counted as a fresh active runtime blocker. Added RED/GREEN
  coverage for that exact shape and extended the canonical classifier without
  changing real lifecycle-driver ownership semantics. Verification passed:
  `python3 -m unittest support.scripts.tests.test_factor_claim_terminalization_audit -v`
  ran 100 tests OK;
  `python3 -m py_compile support/scripts/factor_claim_terminalization_audit.py support/scripts/tests/test_factor_claim_terminalization_audit.py`
  passed. Same-turn compact claim audit returned `status=pass`,
  `active_claims=0`, `live_factor_processes=0`, `blocking_reasons=[]`, while
  practical counts remain zero: `promotion_allowed_true=0`,
  `trade_usable_true=0`, and `same_tree_practical_closure=null`.
- 2026-05-30T06:58+0800: fixed the next compact-audit coordination loop.
  A TOMAC Aroon/CCI child wrapper-prep claim explicitly had
  `status=active_wrapper_prep_no_launch`, false practical flags, and non-goals
  forbidding provider fetch, IBKR historical, AutoQuant, Freqtrade, paper/sim/
  live, Pre-Bayes, BBN, CatBoost, execution-tree, and promotion, but it was
  still counted as `active_claims=1`. Added RED/GREEN coverage for this exact
  wrapper/training prep no-launch shape and extended the canonical
  coordination-only classifier. Verification passed:
  `python3 -m unittest support.scripts.tests.test_factor_claim_terminalization_audit -v`
  ran 101 tests OK; `python3 -m py_compile support/scripts/factor_claim_terminalization_audit.py support/scripts/tests/test_factor_claim_terminalization_audit.py`
  passed; `git diff --check -- support/scripts/factor_claim_terminalization_audit.py support/scripts/tests/test_factor_claim_terminalization_audit.py support/docs/experiments/actionable-regime-confidence/20260530T064134+0800-codex-nq-compound-rv-stress-lifecycle-exec.md`
  passed. Same-turn compact audit then showed the no-launch prep claim no
  longer blocked closure (`active_claims=0`, `fresh_active_claims_without_live_process=0`),
  but runtime launch remained blocked by a live local YM smoke process under
  `/tmp/ict-engine-ym-minprice-smoke-20260530T0656`. Practical counts are still
  zero: `promotion_allowed_true=0`, `trade_usable_true=0`, and
  `same_tree_practical_closure=null`.

## Root Cause Readback

The current failure is not that a hidden practical factor exists and the count
misses it. Same-turn factor closure still reports `trade_usable_true=0`,
`promotion_allowed_true=0`, and no validated same-tree practical closure packet.

The repeated near-practical pattern has two separate causes:

1. Gate1 and source/prep packets can accumulate provider, cost, or screen
   evidence while fresh claims/runtime occupancy prevents safe downstream
   launch.
2. Even when a candidate is promising, the objective completion owner only
   accepts a same-tree packet proving the full practical chain:
   provider/data -> Pre-Bayes -> BBN/workflow -> path-ranker -> execution tree
   -> feedback/update -> policy training. The current tree has no validated
   packet proving any of those stages for a trade-usable factor.

This slice fixes the observability failure, not the profitability target. The
next executable repair must either resume an unblocked exact candidate through
the full same-tree lifecycle or add a canonical promotion driver that turns a
Gate1 survivor into that lifecycle evidence without spoofing the packet.
