# Factor Training Closed-Loop Continuation - 2026-05-28 Current Readback

Owner: Codex
Status: active / objective not complete
Route: `sd/ict-engi-fact-rese-muta`

## Scope

This file tracks the current continuation of the user's full objective: optimize
`ict-engine` factor-training direction and prove that any trained profitability
factor can pass the real closed loop without weakening training-time or
post-training gates. This is not a completion claim.

## Current Evidence

- Routing completed through `~/.hermes/routing/skill-router.md`,
  `~/.hermes/routing/project-router.md`, repo `CLAUDE.md`, repo `AGENTS.md`,
  repo `AGENT.md`, and installed runtime skill
  `~/.hermes/skills/software-development/ict-engi-fact-rese-muta/SKILL.md`.
- Focused verification for the practical-admission debt packet work passed:
  `python3 -m unittest support.scripts.tests.test_done_definition_audit -v`
  ran `21/21 OK`.
- Focused verification for the objective closure snapshot work passed:
  `python3 -m unittest support.scripts.tests.test_objective_closure_snapshot -v`
  ran `21/21 OK`.
- `git diff --check` on the touched audit/script/test/tracker slice passed.
- `python3 support/scripts/objective_closure_snapshot.py --compact --output-dir /tmp/ict-engine-goal-20260528-codex-current-verification-no-remotes`
  intentionally exited red and wrote a packet with
  `summary.status=not_complete`.
- 2026-05-29T00:36+0800 current-state continuation created an audit-only
  factor workdoc and claim for this slice:
  `/tmp/ict-engine-closed-loop-loophole-audit-codex-20260529T003643+0800/workdoc.md`
  and
  `/tmp/ict-engine-agent-claims/board-b-factor-refinement/20260529T003643+0800-codex-closed-loop-loophole-audit.claim`.
  This claim launches no provider, IBKR, Auto-Quant, freqtrade, or TOMAC work
  and carries `promotion_allowed=false`, `trade_usable=false`, and
  `update_goal=false`.
- A claim-audit loophole was found and fixed: stale claims with
  `status=active` plus `decision=active_*` continued to block factor closure
  even after current terminal artifacts existed under the claim run root. The
  fix makes current terminal summaries/metrics take precedence over stale
  active decision text, without changing live-runtime or fresh-claim blocking.
  Focused verification passed:
  `python3 -m unittest support.scripts.tests.test_factor_claim_terminalization_audit -v`
  ran `68/68 OK`, and
  `python3 -m unittest support.scripts.tests.test_objective_closure_snapshot -v`
  ran `23/23 OK`.
- Post-fix compact claim audit still intentionally fails closed for real
  current blockers rather than the repaired stale-claim false positives:
  `active_claims=3`, `fresh_active_claims_without_live_process=2`,
  `live_factor_processes=1`, `promotion_allowed_true=0`,
  `trade_usable_true=0`. The live root reported by compact audit was
  `ict-engine-tomac-tod-balanced-predicate-density-expansion-autoquant-loop-20260529T004128+0800`.
- Post-fix objective snapshot at
  `/tmp/ict-engine-closed-loop-loophole-audit-codex-20260529T003643+0800/objective-snapshot-after-claim-fix/`
  intentionally exited `1` with `summary.status=not_complete`. It now names
  four blockers: `done_definition_not_completion_ready`,
  `practical_admission_source_debt`, `factor_closure_blocked`, and
  `release_readiness_blocked`.
- 2026-05-28T20:05+0800 TOMAC continuation stayed collision-safe while fresh
  active Board B claims existed. The distinct WPR/ADX Hurst MSS reclaim branch
  was prepared but not launched:
  `RangeReversion -> PdhPdlFractalLiquiditySweep -> WprAdxTrendAlignedReclaim -> HurstProfileMssReclaim -> tomac_idxfut_clean_wpr_adx_hurst_profile_mss_reclaim_1m_v1`.
  Evidence: `/tmp/ict-engine-tomac-wpr-adx-hurst-mss-prep-codex-20260528T200000+0800/workdoc.md`,
  `/tmp/ict-engine-tomac-wpr-adx-hurst-mss-prep-codex-20260528T200000+0800/summaries/terminal_summary.json`,
  and `support/docs/experiments/actionable-regime-confidence/runs/20260528T200000+0800-codex-tomac-wpr-adx-hurst-profile-mss-reclaim-prep-v1/summaries/prep_packet.md`.
  Verification: `python3 -m unittest support.docs.experiments.actionable-regime-confidence.scripts.test_tomac_wpr_adx_hurst_profile_mss_reclaim_prep_v1 -v`
  ran `3/3 OK`; help guard exited `0`; prep summary reports
  `source_prep_complete`, `coverage_exit=0`, `scan_executed=false`,
  `promotion_allowed=false`, `trade_usable=false`.
- The same-turn Aroon/CCI bounded clean-AQ readback under
  `/tmp/ict-engine-tomac-aroon-cci-cadence-lift-symbol-guard-wait-20260528T194353+0800/run/aq/`
  did not pass Gate 1: `decision=observation_no_autoquant_survivor_yet`,
  `survivors_5bps=[]`, `pre_bayes_allowed=false`, `bbn_allowed=false`,
  `catboost_allowed=false`, `execution_tree_allowed=false`,
  `promotion_allowed=false`, `trade_usable=false`. Its full-window run later
  became the active live runtime owner and blocks sibling launches until it
  exits or terminalizes.
- The Aroon/CCI full-window run later terminalized fail-closed at
  `/tmp/ict-engine-tomac-aroon-cci-cadence-lift-symbol-guard-wait-20260528T194353+0800/run/aq-fullwindow/`:
  `run_tomac_1m.exit=0`, `survivors_5bps=[]`, ES `trade_count=948`,
  `trades_per_day=0.520307`, `profit_factor=0.9983`, `total_profit_pct=-0.22`,
  and NQ `trade_count=1674`, `trades_per_day=0.918771`,
  `profit_factor=0.9286`, `total_profit_pct=-16.27`. All downstream booleans
  remained false.
- The WPR/ADX Hurst MSS branch had multiple collision-aborted launch attempts
  while other fresh TOMAC owners appeared. The locally owned collision-aborted
  claims are terminalized with `promotion_allowed=false`, `trade_usable=false`,
  and no Gate 1 verdict. A separate fresh owner remains active on the same
  prepared root: claim
  `/tmp/ict-engine-agent-claims/board-b-factor-refinement/20260528T203325+0800-codex-tomac-wpr-adx-hurst-mss-relaunch.claim`,
  process `PID 67243` with child `run_tomac.py` `PID 70270`, root
  `/tmp/ict-engine-tomac-wpr-adx-hurst-mss-prep-codex-20260528T200000+0800/aq`.
  As of 2026-05-28T20:40+0800 no `autoquant_clean_1m_gate.json`, row CSV, or
  `run_tomac_1m.exit` existed under that root, so no WPR/ADX factor verdict can
  be claimed yet.

## Current Blockers

The latest no-remote objective snapshot at
`/tmp/ict-engine-goal-20260528-codex-current-verification-no-remotes/` reports:

- `done_definition_not_completion_ready`: heavy done-definition gates were not
  run in this quick verification packet.
- `practical_admission_source_debt`: the current worktree still contains
  `193` untracked practical-admission wrapper violations across `115` files,
  even though tracked violations are `0`.
- `factor_closure_blocked`: Board B still has fresh active claims without live
  runtimes, including the fresh greedy-filtered clean downstream repair claim
  and a wait-only Aroon/CCI cadence-lift claim.
- `factor_closure_blocked`: after the stale-active terminal-artifact fix, the
  closure audit still reports real current blockers: fresh Camarilla/session
  cluster takeover claims and a live Balanced TOD predicate-density AutoQuant
  process. Do not launch a sibling provider/AQ lane until those terminalize or
  become stale-safe with no live owner.
- `practical_admission_source_debt`: the current untracked practical-admission
  wrapper quarantine no longer matches the scanner fingerprint
  (`untracked_violation_count=193`, `untracked_violating_files=115`), so the
  debt is not externalized for objective closure. This must be retired,
  quarantined with the current fingerprint, or tracked deliberately before any
  completion claim.
- `tomac_runtime_blocked`: latest compact audit showed the Aroon/CCI
  CadenceLiftSymbolGuard full-window clean-AQ process live under
  `/tmp/ict-engine-tomac-aroon-cci-cadence-lift-symbol-guard-wait-20260528T194353+0800/run/aq-fullwindow`,
  so no additional TOMAC/AQ launch is allowed in the same turn.
- `tomac_runtime_blocked`: after Aroon/CCI terminalized, WPR/ADX Hurst MSS was
  claimed by another fresh owner and is live under the prepared root above. Do
  not relaunch or duplicate this branch until that owner terminalizes or becomes
  stale-safe by the one-hour rule and no live process remains.
- `release_readiness_blocked`: the worktree is not clean for release/source
  attribution.

## Decision

I cannot honestly answer yes to the full objective. The current code/test slice
improves the closure audit by making practical-admission debt packetized and
portable, but the full objective still requires a same-tree practical closure
packet with `promotion_allowed_true>0` and `trade_usable_true>0`, clean
attributable source, and fully run done-definition/release gates.

## Next Safe Actions

1. Do not launch another Board B TOMAC/AQ lane while fresh active claims or live
   TOMAC/AQ runtime roots exist.
2. Wait for or inspect the fresh active claims after owner progress or
   stale-safe timeout, then rerun
   `python3 support/scripts/factor_claim_terminalization_audit.py --compact`.
3. Read back the active Balanced TOD predicate-density AutoQuant root and fresh
   Camarilla/session-cluster takeover claims after they terminalize. Classify
   fail-closed unless a current artifact proves full downstream/live readiness.
4. Read back the active WPR/ADX Hurst MSS owner root after it terminalizes. If
   it has no Gate 1 survivor, classify fail-closed and rotate; if it survives,
   proceed to Pre-Bayes/BBN/CatBoost/execution-tree without lowering gates.
5. Retire, quarantine, or intentionally track the untracked practical-admission
   wrapper debt before any objective-closure or release claim.
6. Produce or locate one same-tree practical closure packet that proves the
   provider -> training/admission -> Pre-Bayes -> BBN -> path-ranker ->
   execution tree -> feedback path without promotion shortcuts.
