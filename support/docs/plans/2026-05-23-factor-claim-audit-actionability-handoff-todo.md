# 2026-05-23 Factor Claim Audit Actionability Handoff TODO

Owner: Codex maintenance loop slice.
Scope: make factor-claim terminalization audit output more actionable without
editing claims, run roots, factor evidence, or Board state.

## Intent

The factor-claim audit should tell a downstream maintainer what blocks closure,
not only that the board needs attention. The compact output must stay
token-friendly and privacy-safe while making the next local action explicit.

## Current Todo Board

### Done

- [x] Add RED regression for summary-level actionability.
- [x] Add `blocking_reasons` to factor-claim audit summary.
- [x] Add `next_action` derived from active claims, missing run roots, and
  positive `trade_usable` / `promotion_allowed` flags.
- [x] Preserve fail-closed semantics: `needs_attention` remains exit `1`.
- [x] Preserve compact privacy boundary: no `claim_path`, raw `run_root`, or
  repo-local absolute path in compact attention claims.
- [x] Run targeted and full factor-claim audit tests.
- [x] Run py_compile and script manifest checks.
- [x] Run a real compact factor-claim audit readback.
- [x] Fix claim parsing for terminal Markdown bullets, `status=terminal*`, and
  `terminal_decision`.
- [x] Terminalized the stale TOMAC TOD execution-predicate readback claim after
  live-process and run-root readback.
- [x] Terminalized the Bybit MNT/HBAR CMF/OBV readback-only claim after
  confirming no matching live runner and reading terminal metrics.
- [x] Terminalized the stale VRT Bayesian-Markov Gate 1 claim after reading
  terminal metrics and confirming no matching live runner remained.
- [x] Terminalized or externalized the remaining active factor claims outside
  this repo-doc slice.
- [x] Re-ran the compact factor-claim audit after claim-board changes and
  confirmed zero-blocker states when no live drift was present.
- [x] Terminalized the TOMAC NQ two-leg source-discovery claim after the
  reconstruction probe failed strict parity and 5bps cost stress.
- [x] Terminalized the IBKR PWR KST/Coppock drift claim after AQ rank completed
  and the exact 1m root failed hard 5bps/density.
- [x] Terminalized the IBKR FIX range-expansion drift claim after AQ rank
  completed with no hard 5bps/density survivor.
- [x] Terminalized the IBKR DOV industrial-automation opening-drive RVOL drift
  claim after AQ rank completed and downstream/promotion/trade remained blocked.
- [x] Re-ran the compact factor-claim audit and confirmed that the board drifted
  again before commit with six fresh cybersecurity/WMT/CPB/ENPH/GLW/TOMAC-
  related active claims.

### Next

- [ ] If missing run roots appear again, restore evidence or terminalize those
  claims explicitly.
- [ ] If any `trade_usable=true` or `promotion_allowed=true` appears, review the
  positive flag against hard gates before any promotion language.
- [ ] Rerun the compact factor-claim audit immediately before staging, commit,
  release-readiness claims, or any publish/tag/push action because `/tmp` claims
  can drift.
- [ ] Keep release readiness separate: this factor-claim pass does not publish,
  tag, push, or prove release readiness.
- [ ] Keep practical factor promotion separate: this pass does not mark any
  factor trade-usable or promotion-allowed.

### Boundary Confirmed

- [x] `/tmp` TOMAC TOD claim file was edited only to add terminal readback.
- [x] `/tmp` Bybit MNT/HBAR readback-only claim file was edited only to add
  terminal readback.
- [x] `/tmp` VRT Bayesian-Markov Gate 1 claim file was edited only to add
  terminal fail-closed readback.
- [x] `/tmp` TOMAC NQ two-leg source-discovery claim file was edited only to add
  terminal fail-closed readback.
- [x] `/tmp` PWR KST/Coppock claim file was edited only to add terminal
  fail-closed readback.
- [x] `/tmp` FIX range-expansion claim file was edited only to add terminal
  fail-closed readback.
- [x] `/tmp` DOV industrial-automation claim file was edited only to add terminal
  fail-closed readback.
- [x] No factor run root was modified by this repo-doc sync.
- [x] No factor was promoted or marked trade-usable.
- [x] No Board A/B terminal decision was changed by this repo-doc sync.

## Evidence

- RED:
  `python3 -m unittest support.scripts.tests.test_factor_claim_terminalization_audit.FactorClaimTerminalizationAuditTest.test_summarize_marks_needs_attention_for_active_or_positive_claims -v`
  failed before implementation with `KeyError: 'blocking_reasons'`.
- GREEN targeted:
  the same test passed after adding `blocking_reasons` and `next_action`.
- Full factor-claim audit tests:
  `python3 -m unittest support.scripts.tests.test_factor_claim_terminalization_audit -v`
  passed `7` tests.
- Compile:
  `python3 -m py_compile support/scripts/factor_claim_terminalization_audit.py support/scripts/tests/test_factor_claim_terminalization_audit.py`
  passed.
- Script manifest:
  `python3 support/scripts/check_script_manifest.py`
  passed with `entries=21`.
- Real compact factor audit:
  `python3 support/scripts/factor_claim_terminalization_audit.py --compact --output /tmp/ict-engine-factor-claims-actionability-20260523.json`
  exited `1` as expected.
- Parser RED:
  `python3 -m unittest support.scripts.tests.test_factor_claim_terminalization_audit.FactorClaimTerminalizationAuditTest.test_build_report_treats_terminal_status_and_markdown_bullets_as_terminal -v`
  failed before implementation because `terminalized_claims` was `0` instead of
  `2`.
- Parser GREEN:
  the same targeted test passed after parsing Markdown bullet keys, treating
  `status=terminal*` as terminalized, and using `terminal_decision` as a
  decision fallback.
- Full factor-claim audit tests after parser fix:
  `python3 -m unittest support.scripts.tests.test_factor_claim_terminalization_audit -v`
  passed `8` tests.
- Compile after parser fix:
  `python3 -m py_compile support/scripts/factor_claim_terminalization_audit.py support/scripts/tests/test_factor_claim_terminalization_audit.py`
  passed.
- Script manifest after parser fix:
  `python3 support/scripts/check_script_manifest.py`
  passed with `entries=21`.
- Real compact factor audit after parser fix:
  `python3 support/scripts/factor_claim_terminalization_audit.py --compact --output /tmp/ict-engine-factor-claims-terminal-parser-20260523.json`
  exited `1` as expected, but active claims dropped from `8` to `3`.
- TOMAC TOD terminalization readback:
  `python3 support/scripts/factor_claim_terminalization_audit.py --compact --output /tmp/ict-engine-factor-claims-after-tomac-tod-terminalization-20260523.json`
  exited `1` as expected, with active claims now held at `3` because new/live
  lanes still exist.
- Bybit MNT/HBAR terminalization readback:
  `python3 support/scripts/factor_claim_terminalization_audit.py --compact --output /tmp/ict-engine-factor-claims-after-bybit-terminalization-20260523.json`
  exited `1` as expected, with active claims reduced to `2`.
- Pre-commit drift readback:
  `python3 support/scripts/factor_claim_terminalization_audit.py --compact --output /tmp/ict-engine-factor-claims-precommit-active2-20260523.json`
  exited `1` as expected, with active claims back to `3` after a fresh MCL
  downstream claim appeared.
- Final pre-stage readback:
  `python3 support/scripts/factor_claim_terminalization_audit.py --compact --output /tmp/ict-engine-factor-claims-final-precommit-20260523.json`
  exited `1` as expected, with active claims reduced to `2` after MCL
  downstream terminalized externally.
- Final-stage drift readback:
  `python3 support/scripts/factor_claim_terminalization_audit.py --compact --output /tmp/ict-engine-factor-claims-final-stage-20260523.json`
  exited `1` as expected, with active claims reduced to `1` after TOMAC
  volume/mass terminalized externally.
- Commit readback:
  `python3 support/scripts/factor_claim_terminalization_audit.py --compact --output /tmp/ict-engine-factor-claims-commit-readback-20260523.json`
  exited `1` as expected, still with only the CEG claim active.
- Final zero-blocker readback:
  `python3 support/scripts/factor_claim_terminalization_audit.py --compact --output /tmp/ict-engine-factor-claims-before-commit-20260523.json`
  exited `0`, with no active factor claims.
- Verification rerun:
  `python3 support/scripts/factor_claim_terminalization_audit.py --compact --output /tmp/ict-engine-factor-claims-before-commit-verify-20260523.json`
  exited `0`, confirming the same zero-blocker state.
- VRT drift readback:
  `python3 support/scripts/factor_claim_terminalization_audit.py --compact --output /tmp/ict-engine-factor-claims-doc-sync-live2-20260523.json`
  exited `1` with `active_claims=1` after a fresh VRT Gate 1 claim appeared.
- VRT terminal evidence:
  `support/docs/experiments/actionable-regime-confidence/runs/20260523T033648+0800-codex-ibkr-vrt-bayesian-markov-trend-detector-1m-mtf-gate1-v1/checks/terminal_metrics.json`
  reported `decision=drop_gate1_no_exact_1m_5bps_density_survivor`,
  `promotion_allowed=false`, and `trade_usable=false`.
- Post-VRT verification:
  `python3 support/scripts/factor_claim_terminalization_audit.py --compact --output /tmp/ict-engine-factor-claims-doc-sync-post-vrt-verify-20260523.json`
  exited `0`, confirming the current zero-blocker state.
- Extension-complete admission audit drift:
  `python3 support/scripts/factor_claim_terminalization_audit.py --compact --output /tmp/ict-engine-factor-claims-doc-sync-precommit-final-20260523.json`
  exited `1` with `active_claims=1` for
  `20260523T034056+0800-codex-extension-complete-admission-audit.claim`.
- Extension-complete admission audit terminalization:
  the `/tmp` claim was marked fail-closed after reading the Board B practical
  extension completion gate, which says no current Board B packet satisfies
  `extension_complete=true`.
- Current TOMAC two-leg drift:
  `python3 support/scripts/factor_claim_terminalization_audit.py --compact --output /tmp/ict-engine-factor-claims-after-extension-terminalization-20260523.json`
  exited `1` with `active_claims=1` for
  `20260523T-current-codex-tomac-nq-twoleg-exact-replay-source-discovery.claim`.
- TOMAC source-discovery terminal evidence:
  `/private/tmp/ict-engine-tomac-nq-twoleg-reconstruction-probe-20260523T035059+0800/checks/terminal_metrics.json`
  reported `decision=reconstruction_parity_failed_do_not_ingest`, target
  `1720` trades / `+665.58%` vs actual `1255` trades / `+42.05%`,
  `strict_parity=false`, `5bps_per_side=-83.45%`,
  `promotion_allowed=false`, and `trade_usable=false`.
- PWR terminal evidence:
  `support/docs/experiments/actionable-regime-confidence/runs/20260523T035428+0800-codex-ibkr-pwr-kst-coppock-momentum-1m-mtf-gate1-v1/checks/terminal_metrics.json`
  reported `decision=drop_gate1_no_exact_1m_5bps_density_survivor`,
  `rank_rows=7`, `rank_total_trade_count=393`,
  `survivors_5bps_per_side=[]`, `promotion_allowed=false`, and
  `trade_usable=false`.
- FIX drift readback:
  `python3 support/scripts/factor_claim_terminalization_audit.py --compact --output /tmp/ict-engine-factor-claims-live-after-tomac-source-terminal-20260523.json`
  exited `1` with `active_claims=1` for
  `20260523T035607+0800-codex-ibkr-fix-infrastructure-range-expansion-1m-mtf-gate1.claim`.
- FIX terminal evidence:
  `support/docs/experiments/actionable-regime-confidence/runs/20260523T035708+0800-codex-ibkr-fix-infrastructure-range-expansion-continuation-1m-mtf-gate1-v1/checks/terminal_metrics.json`
  reported `decision=drop_gate1_cost_or_density_failed`, `rank_rows=7`,
  `rank_total_trade_count=87`, `survivors_5bps_per_side=[]`,
  `promotion_allowed=false`, and `trade_usable=false`.
- Current zero-blocker verification:
  `python3 support/scripts/factor_claim_terminalization_audit.py --compact --output /tmp/ict-engine-factor-claims-doc-sync-after-pwr-fix-tomac-terminalization-20260523.json`
  exited `0`; the output file exists and reports `active_claims=0`.
- Pre-commit final zero-blocker verification:
  `python3 support/scripts/factor_claim_terminalization_audit.py --compact --output /tmp/ict-engine-factor-claims-before-doc-commit-final-20260523.json`
  exited `0`; the output file exists and reports `active_claims=0`.
- DOV terminal evidence:
  `support/docs/experiments/actionable-regime-confidence/runs/20260523T041020+0800-codex-ibkr-dov-industrial-automation-opening-drive-rvol-gate1-v1/summaries/ibkr_dov_industrial_automation_opening_drive_rvol_gate1_v1.json`
  reported `decision=keep_small_only`, `all_commands_ok=true`, `rank_rows=5`,
  `rank_total_trade_count=103`, `promotion_allowed=false`, and
  `trade_usable=false`.
- Live drift before doc commit:
  `python3 support/scripts/factor_claim_terminalization_audit.py --compact --output /tmp/ict-engine-factor-claims-live-drift-doc-snapshot-20260523.json`
  exited `1` with `active_claims=6` after fresh WMT/CBRE/CPB/TOMAC-related
  claims appeared.
- Pre-stage live drift readback:
  `python3 support/scripts/factor_claim_terminalization_audit.py --compact --output /tmp/ict-engine-factor-claims-prestage-current-20260523.json`
  exited `1` with `active_claims=7`, `terminalized_claims=42`, and
  `total_claims=49` after ENPH/GLW claims appeared and one prior CBRE duplicate
  left the active compact set.
- Final pre-stage live drift readback:
  `python3 support/scripts/factor_claim_terminalization_audit.py --compact --output /tmp/ict-engine-factor-claims-final-prestage-current-20260523.json`
  exited `1` with `active_claims=6`, `terminalized_claims=43`, and
  `total_claims=49`; CBRE no longer appears in the active compact set.

## Current Readback

Latest verified readback:
`/tmp/ict-engine-factor-claims-final-prestage-current-20260523.json`

- `summary.status=needs_attention`
- `total_claims=49`
- `terminalized_claims=43`
- `active_claims=6`
- `missing_run_roots=0`
- `trade_usable_true=0`
- `promotion_allowed_true=0`
- `blocking_reasons=["active_claims"]`
- `next_action="terminalize or externalize active claims"`

Current active compact claim:

- `20260523T041012+0800-codex-ibkr-cybersecurity-sibling-provider-preflight.claim`
- `20260523T041026+0800-codex-ibkr-wmt-defensive-retail-opening-drive-rvol-full-ladder-provider-retry.claim`
- `20260523T041029+0800-codex-ibkr-cpb-packaged-food-connors-rsi2-rebound-1m-mtf-gate1.claim`
- `20260523T041504+0800-codex-ibkr-enph-solar-gap-failure-reversal-1m-mtf-gate1.claim`
- `20260523T041850+0800-codex-ibkr-glw-optical-communications-keltner-reclaim-1m-mtf-gate1.claim`
- `20260523T0420+0800-codex-tomac-psar-arooncci-gate1.claim`

Historical drift sequence for handoff continuity:

- actionability baseline:
  `/tmp/ict-engine-factor-claims-actionability-20260523.json` exited `1` with
  `active_claims=8`.
- parser repair:
  `/tmp/ict-engine-factor-claims-terminal-parser-20260523.json` exited `1` with
  `active_claims=3`.
- staged terminalization drift:
  `/tmp/ict-engine-factor-claims-final-stage-20260523.json` exited `1` with
  `active_claims=1`.
- final pre-commit verification:
  `/tmp/ict-engine-factor-claims-before-commit-20260523.json` and
  `/tmp/ict-engine-factor-claims-before-commit-verify-20260523.json` exited `0`
  with `active_claims=0`.
- VRT live drift:
  `/tmp/ict-engine-factor-claims-doc-sync-live2-20260523.json` exited `1` with
  `active_claims=1`.
- post-VRT verification:
  `/tmp/ict-engine-factor-claims-after-vrt-terminalization-20260523.json` and
  `/tmp/ict-engine-factor-claims-doc-sync-post-vrt-verify-20260523.json` exited
  `0` with `active_claims=0`.
- extension audit drift then terminalization:
  `/tmp/ict-engine-factor-claims-doc-sync-precommit-final-20260523.json` exited
  `1` for the extension-complete admission audit claim; after terminalization,
  the active blocker moved to the TOMAC NQ two-leg source-discovery claim.
- TOMAC/PWR/FIX drift then terminalization:
  `/tmp/ict-engine-factor-claims-doc-sync-after-pwr-fix-tomac-terminalization-20260523.json`
  exited `0` after TOMAC source reconstruction, PWR KST/Coppock, and FIX
  range-expansion were terminalized fail-closed from concrete terminal metrics.
- DOV drift then terminalization:
  `/tmp/ict-engine-factor-claims-before-doc-commit-final2-20260523.json`
  exited `1` for a fresh DOV claim; after DOV terminal metrics were read and the
  claim was terminalized fail-closed, the board drifted again to six active
  claims in `/tmp/ict-engine-factor-claims-live-drift-doc-snapshot-20260523.json`.
- pre-stage live drift:
  `/tmp/ict-engine-factor-claims-prestage-current-20260523.json` exited `1` with
  `active_claims=7`, `terminalized_claims=42`, and `total_claims=49`.
- final pre-stage live drift:
  `/tmp/ict-engine-factor-claims-final-prestage-current-20260523.json` exited
  `1` with `active_claims=6`, `terminalized_claims=43`, and `total_claims=49`.

## Compatibility Boundary

- The audit script is read-only.
- Compact output remains token-friendly.
- Compact output continues to omit raw `claim_path` and `run_root`.
- This repo-doc slice is handoff/actionability only; TOMAC TOD was
  terminalized in `/tmp`, and the Bybit MNT/HBAR readback-only claim was
  terminalized in `/tmp`; VRT and extension-complete read-only claims were also
  terminalized in `/tmp` from terminal evidence. TOMAC source-discovery, PWR,
  FIX, and DOV drift claims were also terminalized in `/tmp` from terminal
  evidence.
  No factor run root, Board terminal row, factor promotion, or release-readiness
  state was changed by this doc sync.

## Resume State

Resume from this file plus
`/tmp/ict-engine-factor-claims-final-prestage-current-20260523.json`.
The current factor-claim terminalization audit needs attention because live
`/tmp` claims drifted again. The smallest next safe action is to let active
cybersecurity/WMT/CPB/ENPH/GLW/TOMAC-related lanes reach terminal metrics, then
terminalize or externalize only those claims from evidence. Keep release
readiness blocked until the dirty worktree, stale release docs, origin drift, and
version/tag reuse gates are resolved. Do not turn any factor-claim snapshot into
factor promotion, trade usability, tag, push, mirror publish, or release
readiness.

## 2026-05-23 Stale Positive Flag Review

The broad all-history terminal-metrics sweep found historical positive flags
outside the current claim audit, but each reviewed positive is superseded by
cost or downstream fail-closed evidence:

- `binance_vwapdev_obvrsi_1m_strict_iteration_v2`: downstream clean readback is
  `no_trade`, ranker not used, ranker not ready, promotion/trade false.
- `tvr_kweb_orb_rvol_vwap_density_1m_mtf_v1`: corrected cost gate is
  `cost_fragile_stop_before_downstream`, promotion/trade false.
- `yf_cybersecurity_etf_opening_drive_rvol_vwap_1m_mtf_v1`: cost gate stops
  before downstream; use only as incubation/neutralization evidence.
- `tvr_arkk_orb_rvol_vwap_density_1m_mtf_v3`: downstream readbacks fail closed
  with no-trade / observe and promotion false.
- `tvr_xlb_orb_rvol_vwap_density_1m_mtf_v1`: downstream readback fails closed
  with no-trade / observe and promotion false.
- `binance_crypto_donchian_rvol_breakout_mtf_gate1_v1`: downstream readbacks
  are no-trade, ranker not used, ranker not ready, promotion false.
- `tvr_ibb_orb_rvol_vwap_density_1m_mtf_v1`: corrected cost gate and
  direct-fallback downstream readback remain fail-closed.

Actionability:

- No claim-board edit is required for these stale positives; they are historical
  run-root classification issues, not active claims.
- Keep future audit logic fail-closed: if a broad sweep sees raw
  `promotion_allowed=true` or `trade_usable=true`, first look for corrected
  summaries, cost-stress gates, and downstream readbacks before using that flag
  in release or practical-factor language.
- Current claim audit now has six active claims and zero current positive
  promotion/trade-usable claims.

## 2026-05-23 04:05 CST Fresh Compact Audit Readback

Historical zero-blocker artifact:

- `/tmp/ict-engine-factor-claims-after-fix-terminalized-20260523.json`.
- Result: `summary.status=pass`, `active_claims=0`,
  `terminalized_claims=40`, `total_claims=40`, `missing_run_roots=0`,
  `promotion_allowed_true=0`, `trade_usable_true=0`, and
  `next_action=no claim terminalization blockers found`.
- TOMAC NQ two-leg source-discovery remains terminalized fail-closed from
  `/tmp/ict-engine-tomac-nq-twoleg-reconstruction-probe-20260523T035059+0800/checks/terminal_metrics.json`
  with `decision=reconstruction_parity_failed_do_not_ingest`.
- FIX infrastructure range-expansion remains terminalized fail-closed from
  `support/docs/experiments/actionable-regime-confidence/runs/20260523T035708+0800-codex-ibkr-fix-infrastructure-range-expansion-continuation-1m-mtf-gate1-v1/checks/terminal_metrics.json`
  with `decision=drop_gate1_cost_or_density_failed`.

Actionability:

- The claim-terminalization blocker was clear in this readback but is no longer
  current after live `/tmp` drift.
- This is not practical-factor completion. Current claim-gated evidence still
  has zero promotion-allowed and zero trade-usable factors.
- Next valid factor work must prove a same-root branch through provider fetch,
  Auto-Quant, Pre-Bayes/filter, BBN, CatBoost/path-ranker, execution-tree
  consumption, promotion, and trade-plan ownership.

## 2026-05-23 04:24 CST Live Drift After DOV Terminalization

Historical live readback, superseded by the pre-stage compact audit above:

- DOV industrial-automation Gate 1 was terminalized from
  `support/docs/experiments/actionable-regime-confidence/runs/20260523T041020+0800-codex-ibkr-dov-industrial-automation-opening-drive-rvol-gate1-v1/summaries/ibkr_dov_industrial_automation_opening_drive_rvol_gate1_v1.json`.
  Decision: `keep_small_only`; `promotion_allowed=false`,
  `trade_usable=false`, and `update_goal=false`.
- Fresh compact audit after the DOV terminalization:
  `/tmp/ict-engine-factor-claims-after-dov-terminalized-live-20260523.json`.
- Result: `summary.status=needs_attention`, `active_claims=6`,
  `terminalized_claims=41`, `total_claims=47`, `missing_run_roots=0`,
  `promotion_allowed_true=0`, and `trade_usable_true=0`.
- Active claims at this readback:
  `20260523T-current-codex-ibkr-cbre-dmi-adx-pullback-1m-mtf-gate1.claim`,
  `20260523T0410+0800-codex-ibkr-cbre-dmi-adx-pullback-1m-mtf-gate1.claim`,
  `20260523T041012+0800-codex-ibkr-cybersecurity-sibling-provider-preflight.claim`,
  `20260523T041026+0800-codex-ibkr-wmt-defensive-retail-opening-drive-rvol-full-ladder-provider-retry.claim`,
  `20260523T041029+0800-codex-ibkr-cpb-packaged-food-connors-rsi2-rebound-1m-mtf-gate1.claim`,
  and `20260523T0420+0800-codex-tomac-psar-arooncci-gate1.claim`.

Actionability:

- The earlier 04:05 zero-active claim audit was a transient pass. The latest
  claim-board state needs attention again because new Board B claims appeared
  after that pass.
- Do not terminalize WMT, CBRE, CPB, cybersecurity sibling provider preflight,
  or TOMAC PSAR/Aroon-CCI by inference. Close each only from its own terminal
  evidence.
- The broader goal remains incomplete: zero current promotion-allowed and zero
  current trade-usable factors in the latest compact audit.

## 2026-05-23 04:32 CST Superseding Active-Claim Readback

Latest compact audit:

- `/tmp/ict-engine-factor-claims-after-cybersecurity-terminalized-20260523T0433.json`.
- `summary.status=needs_attention`.
- `active_claims=1`.
- `terminalized_claims=48`.
- `total_claims=49`.
- `missing_run_roots=0`.
- `promotion_allowed_true=0`.
- `trade_usable_true=0`.

Evidence-backed terminalizations completed after the 04:24 drift note:

- `20260523T041029+0800-codex-ibkr-cpb-packaged-food-connors-rsi2-rebound-1m-mtf-gate1.claim`
  from
  `support/docs/experiments/actionable-regime-confidence/runs/20260523T041446+0800-codex-ibkr-cpb-packaged-food-connors-rsi2-rebound-1m-mtf-gate1-v1/checks/terminal_metrics.json`.
  Decision: `drop_gate1_no_exact_1m_5bps_density_survivor`.
- `20260523T041026+0800-codex-ibkr-wmt-defensive-retail-opening-drive-rvol-full-ladder-provider-retry.claim`
  from
  `support/docs/experiments/actionable-regime-confidence/runs/20260523T041250+0800-codex-ibkr-wmt-defensive-retail-opening-drive-rvol-gate1-v1/summaries/ibkr_wmt_defensive_retail_opening_drive_rvol_gate1_v1.json`.
  Decision: `keep_small_only_observation_fail_closed`; `all_commands_ok=false`
  because upper-window `1m 30D` and `5m 3M` fetches failed before smaller
  real-window retries succeeded.
- `20260523T041504+0800-codex-ibkr-enph-solar-gap-failure-reversal-1m-mtf-gate1.claim`
  from
  `support/docs/experiments/actionable-regime-confidence/runs/20260523T042314+0800-codex-ibkr-enph-solar-gap-failure-reversal-1m-mtf-gate1-v1/checks/terminal_metrics.json`.
  Decision: `drop_gate1_cost_or_density_failed`.
- `20260523T041850+0800-codex-ibkr-glw-optical-communications-keltner-reclaim-1m-mtf-gate1.claim`
  from
  `support/docs/experiments/actionable-regime-confidence/runs/20260523T042324+0800-codex-ibkr-glw-optical-communications-keltner-reclaim-1m-mtf-gate1-v1/checks/terminal_metrics.json`.
  Decision: `drop_gate1_cost_or_density_failed`.
- `20260523T041012+0800-codex-ibkr-cybersecurity-sibling-provider-preflight.claim`
  from
  `/tmp/ict-engine-ibkr-cybersecurity-sibling-provider-preflight-20260523T041012+0800/checks/provider_preflight_metrics.json`.
  Decision: `provider_preflight_full_ladder_available`; provider rows only,
  no Auto-Quant, no downstream, no promotion, and no trade.

Remaining active claim:

- `20260523T0420+0800-codex-tomac-psar-arooncci-gate1.claim`.
- Run root:
  `/tmp/ict-engine-tomac-psar-arooncci-gate1-20260523T0420+0800`.
- Live readback at 04:31 CST found the full scan process still running and
  `checks/02_full_scan.exit` still absent.

Actionability:

- The latest claim-board blocker is narrow but real: wait for TOMAC full-scan
  terminal evidence, then terminalize or externalize only from its own
  artifacts.
- Current positive practical-factor count is still zero. Do not convert
  provider-preflight availability, higher-timeframe sibling evidence, or
  `keep_small_only` rows into promotion/trade-usability language.
- Release remains blocked; no mirror/tag/GitHub Release action is authorized by
  this readback.

## 2026-05-23 04:45 CST Superseding Claim Pass After TOMAC/S/RPD Terminalization

Latest compact audit:

- `/tmp/ict-engine-factor-claims-after-cybersecurity-reread-20260523T044517+0800.json`.
- `summary.status=pass`.
- `active_claims=0`.
- `terminalized_claims=55`.
- `total_claims=55`.
- `missing_run_roots=0`.
- `promotion_allowed_true=0`.
- `trade_usable_true=0`.
- `next_action=no claim terminalization blockers found`.

Evidence-backed terminalizations after the 04:32 readback:

- `20260523T0420+0800-codex-tomac-psar-arooncci-gate1.claim` is
  `status: terminalized_runtime_abort`. The full scan exited `143`; no full
  terminal metrics were produced; the NQ smoke packet under
  `/tmp/ict-engine-tomac-psar-arooncci-gate1-20260523T0420+0800/smoke-nq`
  reports `drop_gate1_no_5bps_density_quality_survivor_no_downstream`,
  `gate1_survivors=0`, `promotion_allowed=false`, and `trade_usable=false`.
- `20260523T-current-codex-ibkr-s-cybersecurity-pda-mtf-template-transfer-5m-gate1.claim`
  is terminalized from
  `support/docs/experiments/actionable-regime-confidence/runs/20260523T044321+0800-codex-ibkr-s-cybersecurity-pda-mtf-template-transfer-5m-gate1-v1/checks/terminal_metrics.json`.
  Decision:
  `ibkr_s_cybersecurity_pda_mtf_5m_gate1_5bps_density_survivor_downstream_allowed`;
  `downstream_allowed=true`, but `promotion_allowed=false`,
  `trade_usable=false`, `extension_complete=false`, and `update_goal=false`.
- `20260523T043947+0800-codex-ibkr-rpd5m-cybersecurity-pda-mtf-template-transfer-gate1.claim`
  is terminalized from
  `support/docs/experiments/actionable-regime-confidence/runs/20260523T044255+0800-codex-ibkr-rpd5m-cybersecurity-pda-mtf-template-transfer-gate1-v1/checks/terminal_metrics.json`.
  Decision: `drop_gate1_no_exact_rpd5m_5bps_density_survivor`;
  promotion/trade false.

Actionability:

- Claim terminalization is clear at this readback.
- Do not promote the IBKR S Gate-1 survivor by implication. It is a same-root
  downstream candidate only; practical/live admission still requires the actual
  downstream chain and `extension_complete=true` / promotion / trade usability
  evidence.
- Claim-audit blind spot: a live unclaimed TOMAC repair scan exists outside the
  `/tmp` claim audit at
  `/tmp/ict-engine-tomac-psar-arooncci-gate1-repair-20260523T0500+0800`. At
  04:50 CST, PID `93988` was still running the full `NQ,YM,XAU` repair scan and
  no `checks/01_full_repair.exit` or terminal metrics existed. Do not infer
  terminalization, survivor state, or promotion/trade usability from this
  process until its own artifacts land.
- The broader active goal remains incomplete, and mirror release remains
  blocked.

## 2026-05-23 04:49 CST Live Recheck After User Status Question

Latest compact audit:

- `/tmp/ict-engine-factor-claims-next-20260523.json`.
- `summary.status=pass`.
- `active_claims=0`.
- `terminalized_claims=55`.
- `total_claims=55`.
- `missing_run_roots=0`.
- `promotion_allowed_true=0`.
- `trade_usable_true=0`.
- `next_action=no claim terminalization blockers found`.

Live process readback:

- New TOMAC PSAR/Aroon-CCI repair is still running:
  `/tmp/run_tomac_psar_arooncci_gate1.py`.
- Parent PID `93976`, child PID `93988`.
- Run root:
  `/tmp/ict-engine-tomac-psar-arooncci-gate1-repair-20260523T0500+0800`.
- No `checks/01_full_repair.exit` exists yet, and no terminal metrics were
  available at the readback.

Actionability:

- The claim-terminalization queue is currently clear, but this is not a
  practical-factor win. Promotion/trade counts are still zero.
- The in-flight repair is a separate live process; do not modify, kill,
  terminalize, or promote it without terminal evidence.
- Next valid step is to re-read the repair exit/artifacts when it finishes, or
  continue release-readiness work from a separate clean source slice. No mirror
  release, tag, or GitHub Release is authorized by this checkpoint.

## 2026-05-23 05:01 CST Live-Process Detection Repair

Problem:

- The compact factor-claim audit could report a clean claim-board pass while a
  live factor runner existed outside the claim files.
- The concrete reproducer was the TOMAC repair process under
  `/tmp/ict-engine-tomac-psar-arooncci-gate1-repair-20260523T0500+0800`: the
  claim board could be clear, but PID `93988` was still running and had no exit
  file or terminal metrics.

Implementation:

- `support/scripts/factor_claim_terminalization_audit.py` now reads live factor
  processes via `ps -axo pid,ppid,etime,command`.
- It reports unclaimed live factor work as `live_factor_processes` and includes
  compact `attention_live_processes` entries with PID, run-root state,
  exit-file state, and a command excerpt.
- `--skip-live-processes` preserves the previous claim-only behavior for
  deterministic tests or historical comparisons.

Verification:

- RED targeted unit:
  `python3 -m unittest support.scripts.tests.test_factor_claim_terminalization_audit.FactorClaimTerminalizationAuditTest.test_build_report_marks_unclaimed_live_factor_processes_attention -v`
  failed before implementation because `build_report` did not accept
  `live_processes`.
- GREEN targeted unit: same command passed.
- Full unit suite:
  `python3 -m unittest support.scripts.tests.test_factor_claim_terminalization_audit -v`
  passed `9` tests.
- Compile:
  `python3 -m py_compile support/scripts/factor_claim_terminalization_audit.py support/scripts/tests/test_factor_claim_terminalization_audit.py`
  passed.
- Script manifest:
  `python3 support/scripts/check_script_manifest.py` passed.

Fresh live audit:

- `/tmp/ict-engine-factor-claims-live-process-audit-20260523.json`.
- `summary.status=needs_attention`.
- `active_claims=2`.
- `live_factor_processes=1`.
- `terminalized_claims=58`.
- `total_claims=60`.
- `promotion_allowed_true=0`.
- `trade_usable_true=0`.
- `blocking_reasons=["active_claims","live_factor_processes"]`.

Claim-only control:

- `/tmp/ict-engine-factor-claims-skip-live-process-audit-20260523.json`.
- `active_claims=2`.
- `live_factor_processes=0`.

Current attention items:

- Active claim:
  `20260523T-current-codex-ibkr-axon-public-safety-ttm-squeeze-1m-mtf-gate1.claim`.
  No run root or terminal evidence was found in the readback.
- Active claim:
  `20260523T045720+0800-codex-ibkr-rpd1h-cybersecurity-pda-mtf-template-transfer-exact-downstream.claim`.
  No RPD 1h downstream run root or process was found in the readback.
- Live unclaimed process:
  TOMAC PSAR/Aroon-CCI repair PID `93988` under
  `/tmp/ict-engine-tomac-psar-arooncci-gate1-repair-20260523T0500+0800`;
  no `checks/01_full_repair.exit` exists yet.

Actionability:

- Do not treat a claim-only pass as closure evidence. Use the default
  live-process-aware audit before any closure, staging, or commit decision.
- Do not terminalize AXON, RPD 1h, or TOMAC repair by inference. Close only from
  their own terminal artifacts or explicit owner externalization.
- No promotion/trade-usable factor exists in the current compact audit.

## 2026-05-23 05:09 CST False-Positive Guard And Current Queue

Follow-up finding:

- A readback shell command of the form `sleep; ps -axo ... | rg ...` can contain
  factor runner markers in the regex itself.
- Without an explicit guard, the live-process detector can count that telemetry
  command as a live factor process even though it is only observing processes.

Repair:

- Added a regression test for `ps|rg` readback commands.
- Updated the live-process classifier so shell `ps -axo` pipelines are excluded
  from live factor runner counts while real Python/AQ runner commands remain
  eligible.

Fresh verification:

- RED:
  `python3 -m unittest support.scripts.tests.test_factor_claim_terminalization_audit.FactorClaimTerminalizationAuditTest.test_live_process_classifier_ignores_ps_rg_readback_commands -v`
  failed before the classifier repair because `_is_live_factor_command(...)`
  returned `True`.
- GREEN targeted:
  the same test passed after the classifier repair.
- Live-process attention regression:
  `python3 -m unittest support.scripts.tests.test_factor_claim_terminalization_audit.FactorClaimTerminalizationAuditTest.test_build_report_marks_unclaimed_live_factor_processes_attention -v`
  passed.
- Full unit suite:
  `python3 -m unittest support.scripts.tests.test_factor_claim_terminalization_audit -v`
  passed `10` tests.
- Compile:
  `python3 -m py_compile support/scripts/factor_claim_terminalization_audit.py support/scripts/tests/test_factor_claim_terminalization_audit.py`
  passed.
- Script manifest:
  `python3 support/scripts/check_script_manifest.py` passed with `entries=21`.

Fresh current readback:

- `/tmp/ict-engine-factor-claims-live-process-audit-final3-20260523.json` exited
  `1`, as expected for a fail-closed blocker state.
- `summary.status=needs_attention`.
- `active_claims=0`.
- `terminalized_claims=61`.
- `total_claims=61`.
- `missing_run_roots=0`.
- `live_factor_processes=1`.
- `promotion_allowed_true=0`.
- `trade_usable_true=0`.
- `blocking_reasons=["live_factor_processes"]`.
- Current live blocker is the TOMAC PSAR/Aroon-CCI repair PID `93988` under
  `/tmp/ict-engine-tomac-psar-arooncci-gate1-repair-20260523T0500+0800`; its
  `checks/01_full_repair.exit` is still missing.

Actionability:

- Claim-file terminalization is currently clear, but the full audit loop is not
  clear because one real live factor process remains.
- No current audit evidence supports promotion or trade usability.
- Next valid action is to wait for or read back the TOMAC repair exit/artifacts,
  then terminalize from its own evidence only.

## 2026-05-23 05:10 CST Superseding Live-Process-Aware Readback

Latest compact audit:

- `/tmp/ict-engine-factor-claims-refresh-20260523T050944+0800.json`.
- `summary.status=needs_attention`.
- `active_claims=0`.
- `live_factor_processes=1`.
- `terminalized_claims=61`.
- `total_claims=61`.
- `missing_run_roots=0`.
- `promotion_allowed_true=0`.
- `trade_usable_true=0`.
- `next_action=wait for live factor processes to exit or claim them before closure`.

Evidence-backed terminalizations after the 05:01 readback:

- AXON public-safety TTM-squeeze Gate 1 is terminalized from
  `support/docs/experiments/actionable-regime-confidence/runs/20260523T050413+0800-codex-ibkr-axon-public-safety-ttm-squeeze-1m-mtf-gate1-v1/checks/terminal_metrics.json`.
  Decision: `drop_gate1_cost_or_density_failed`; `provider_data_acquired_count=7`,
  `material_count=7`, `rank_total_trade_count=71`,
  `origin_1m_survivors_5bps_density=[]`,
  `survivors_5bps_per_side=[]`, `promotion_allowed=false`, and
  `trade_usable=false`.
- RPD exact 1h downstream is terminalized from
  `support/docs/experiments/actionable-regime-confidence/runs/20260523T044255+0800-codex-ibkr-rpd5m-cybersecurity-pda-mtf-template-transfer-gate1-v1/downstream-exact-ibkr-rpd-1h-pda-mtf-template-transfer-20260523T050125+0800/checks/downstream_metrics.json`.
  Decision: `exact_rpd_1h_downstream_fail_closed`; `execution_candidate_status=no_trade`,
  `execution_readiness=0.37429404324066085`,
  `transition_hazard=0.9643304104686289`,
  `pda_hybrid_alignment=false`,
  `path_ranker_score_used_by_execution_tree=false`,
  `ranker_validation_ready=false`, `promotion_allowed=false`, and
  `trade_usable=false`.
- TENB cybersecurity PDA/MTF exact 5m Gate 1 is terminalized from
  `support/docs/experiments/actionable-regime-confidence/runs/20260523T050645+0800-codex-ibkr-tenb-cybersecurity-pda-mtf-template-transfer-5m-gate1-v1`.
  Claim decision: `drop_gate1_no_exact_5m_5bps_density_survivor`.

Remaining blocker:

- The only live factor process in the latest clean audit is the unclaimed TOMAC
  PSAR/Aroon-CCI repair PID `93988` under parent PID `93976`, run root
  `/tmp/ict-engine-tomac-psar-arooncci-gate1-repair-20260523T0500+0800`.
- At the 05:10 CST process readback, `checks/01_full_repair.exit` was still
  absent. Output had progressed through NQ scoring and into YM loading, with
  the latest NQ scoring line `score-progress NQ 11500/11664`.

Actionability:

- The claim board is terminalized, but live factor work still blocks closure.
- Do not promote AXON, RPD 1h, TENB, or TOMAC by implication. Each current
  terminalized claim remains `promotion_allowed=false` and
  `trade_usable=false`; TOMAC repair remains in-flight without terminal
  evidence.
- The active three-part goal remains incomplete, and no mirror release action
  is authorized by this readback.

## 2026-05-23 05:12 CST Pre-Commit Drift Check

Fresh audit:

- `/tmp/ict-engine-factor-claims-live-process-audit-final4-20260523.json`
  exited `1`.
- `summary.status=needs_attention`.
- `active_claims=0`.
- `terminalized_claims=61`.
- `total_claims=61`.
- `missing_run_roots=0`.
- `live_factor_processes=1`.
- `promotion_allowed_true=0`.
- `trade_usable_true=0`.
- `blocking_reasons=["live_factor_processes"]`.

Current blocker:

- The only live blocker remains TOMAC PSAR/Aroon-CCI repair PID `93988` under
  `/tmp/ict-engine-tomac-psar-arooncci-gate1-repair-20260523T0500+0800`.
- `checks/01_full_repair.exit` is still missing at this readback.

Actionability:

- This commit may cover only the audit-tooling fix and handoff evidence.
- The broader full-audit objective remains active until the TOMAC repair exits
  and is classified from terminal artifacts.

## 2026-05-23 05:17 CST Bare Search Readback Guard

Follow-up repair:

- A bare `rg`/`grep` process can also contain factor runner markers in its
  search pattern while it is only observing process state.
- The live-process classifier now treats commands starting with `rg`, `grep`,
  `egrep`, or `fgrep` as readback commands, not factor runners.

Fresh verification:

- Target regression:
  `python3 -m unittest support.scripts.tests.test_factor_claim_terminalization_audit.FactorClaimTerminalizationAuditTest.test_live_process_classifier_ignores_bare_search_readback_commands -v`
  passed.
- Full factor-claim audit tests:
  `python3 -m unittest support.scripts.tests.test_factor_claim_terminalization_audit -v`
  passed `11` tests.
- Compile:
  `python3 -m py_compile support/scripts/factor_claim_terminalization_audit.py support/scripts/tests/test_factor_claim_terminalization_audit.py`
  passed.
- Script manifest:
  `python3 support/scripts/check_script_manifest.py` passed with `entries=21`.
- Whitespace:
  `git diff --check -- support/scripts/factor_claim_terminalization_audit.py support/scripts/tests/test_factor_claim_terminalization_audit.py`
  passed.

Fresh post-commit audit:

- `/tmp/ict-engine-factor-claims-postcommit-20260523.json` exited `1`.
- `summary.status=needs_attention`.
- `active_claims=2`.
- `terminalized_claims=61`.
- `total_claims=63`.
- `missing_run_roots=0`.
- `live_factor_processes=1`.
- `promotion_allowed_true=0`.
- `trade_usable_true=0`.
- `blocking_reasons=["active_claims","live_factor_processes"]`.

Current blockers:

- Active claim:
  `20260523T-current-codex-ibkr-asts-space-satellite-gap-continuation-1m-mtf-gate1.claim`.
- Active claim:
  `20260523T051521+0800-codex-ibkr-dash-delivery-platform-initial-balance-range-expansion-1m-mtf-gate1.claim`.
- Live unclaimed process:
  TOMAC PSAR/Aroon-CCI repair PID `93988` under
  `/tmp/ict-engine-tomac-psar-arooncci-gate1-repair-20260523T0500+0800`;
  `checks/01_full_repair.exit` remains missing.

Actionability:

- The audit tool should not count readback/search commands as factor runners.
- The broader objective is still not complete: active claims and one real TOMAC
  process remain, with zero promotion/trade-usable evidence.

## 2026-05-23 05:19 CST Post-Guard Drift Readback

Fresh audit after the bare-search guard:

- `/tmp/ict-engine-factor-claims-post-bare-search-guard-20260523.json` exited
  `1`.
- `summary.status=needs_attention`.
- `active_claims=4`.
- `terminalized_claims=61`.
- `total_claims=65`.
- `missing_run_roots=1`.
- `live_factor_processes=5`.
- `promotion_allowed_true=0`.
- `trade_usable_true=0`.
- `blocking_reasons=["active_claims","live_factor_processes","missing_run_roots"]`.

Current active claims:

- `20260523T-current-codex-ibkr-asts-space-satellite-gap-continuation-1m-mtf-gate1.claim`.
- `20260523T-current-codex-ibkr-ftnt15m-cybersecurity-pda-mtf-template-transfer-gate1.claim`
  has a missing run root in the audit.
- `20260523T051521+0800-codex-ibkr-dash-delivery-platform-initial-balance-range-expansion-1m-mtf-gate1.claim`.
- `20260523T051745+0800-codex-tomac-psar-arooncci-repair-readback.claim`.

Current live processes:

- ASTS Gate 1 runner.
- DASH Gate 1 runner.
- Two child `fetch_external.py` provider processes.
- TOMAC PSAR/Aroon-CCI repair PID `93988`, still missing
  `checks/01_full_repair.exit`.

Actionability:

- The bare-search/readback guard is valid, but the live board moved while this
  slice was being committed.
- Treat the latest blocker set as active work by other/current agents. Do not
  terminalize or promote ASTS, FTNT, DASH, or TOMAC from this audit alone.

## 2026-05-23 05:21 CST Superseding Live Queue Readback

Latest compact audit:

- `/tmp/ict-engine-factor-claims-refresh-20260523T052140+0800.json` exited `1`.
- `summary.status=needs_attention`.
- `active_claims=4`.
- `terminalized_claims=61`.
- `total_claims=65`.
- `missing_run_roots=1`.
- `live_factor_processes=5`.
- `promotion_allowed_true=0`.
- `trade_usable_true=0`.
- `blocking_reasons=["active_claims","live_factor_processes","missing_run_roots"]`.

Current active claims:

- `20260523T-current-codex-ibkr-asts-space-satellite-gap-continuation-1m-mtf-gate1.claim`.
  Run root is present:
  `support/docs/experiments/actionable-regime-confidence/runs/20260523T051704+0800-codex-ibkr-asts-space-satellite-gap-continuation-1m-mtf-gate1-v1`.
  The wrapper is still live; fetch exits observed so far are
  `01/02/03/04=3`, so no terminal metrics or Gate-1 decision exists yet.
- `20260523T051521+0800-codex-ibkr-dash-delivery-platform-initial-balance-range-expansion-1m-mtf-gate1.claim`.
  Run root is present:
  `support/docs/experiments/actionable-regime-confidence/runs/20260523T051716+0800-codex-ibkr-dash-delivery-platform-initial-balance-range-expansion-1m-mtf-gate1-v1`.
  The wrapper is still live; fetch exits observed so far are `01/02/03=3`,
  so no terminal metrics or Gate-1 decision exists yet.
- `20260523T-current-codex-ibkr-ftnt15m-cybersecurity-pda-mtf-template-transfer-gate1.claim`.
  It remains `status=active` with `run_root=pending`; the audit reports
  `run_root_state=missing`.
- `20260523T051745+0800-codex-tomac-psar-arooncci-repair-readback.claim`.
  It watches the TOMAC repair run
  `/tmp/ict-engine-tomac-psar-arooncci-gate1-repair-20260523T0500+0800`,
  which is still live.

Current live processes:

- ASTS Gate-1 wrapper PID `34449`.
- DASH Gate-1 wrapper PID `34651`.
- Active ASTS/DASH `fetch_external.py` children.
- TOMAC PSAR/Aroon-CCI worker PID `93988` under parent PID `93976`.

TOMAC repair status:

- At the 05:21 CST readback, `checks/01_full_repair.exit` was still absent.
- No terminal TOMAC artifacts were found under the repair `full/` tree.
- Stdout remains at YM simulation start after NQ full scoring:
  latest durable lines include `score-progress NQ 11500/11664`, then
  `load YM`, `indicators YM rows=1754351`, `simulate YM`, and
  `simulate-day YM day=1`.

Actionability:

- Do not count this queue as closure or practical-factor proof.
- Do not promote ASTS, DASH, FTNT, or TOMAC by inference from provider-status,
  partial fetch failures, live processes, or existing older sibling evidence.
- Next valid action is to re-read terminal artifacts after the live wrappers
  exit, then terminalize or externalize each claim from its own evidence.

## 2026-05-23 05:25 CST Final Readback Before Handoff

Fresh factor-claim audit:

- `/tmp/ict-engine-factor-claims-final-readback-20260523.json` exited `1`.
- `summary.status=needs_attention`.
- `active_claims=1`.
- `terminalized_claims=65`.
- `total_claims=66`.
- `missing_run_roots=0`.
- `live_factor_processes=1`.
- `promotion_allowed_true=0`.
- `trade_usable_true=0`.
- `blocking_reasons=["active_claims","live_factor_processes"]`.

Current remaining factor blocker:

- The only active claim is
  `20260523T051745+0800-codex-tomac-psar-arooncci-repair-readback.claim`.
- The only live factor process is TOMAC PSAR/Aroon-CCI worker PID `93988`
  under parent PID `93976`, run root
  `/tmp/ict-engine-tomac-psar-arooncci-gate1-repair-20260523T0500+0800`.
- `checks/01_full_repair.exit` is still missing.

Release readiness readback:

- `/tmp/ict-engine-release-readiness-final-readback-20260523.json` exited `1`.
- `summary.status=needs_fix`.
- Unresolved gates:
  `worktree_clean_for_release`,
  `release_docs_fresh_for_selected_tag`.
- Worktree readback reported `77` tracked dirty entries and `782` untracked
  entries; no release/tag/push is authorized from this checkout.

Actionability:

- The audit-tooling repair slice is committed.
- The full objective is not complete: wait for or read the TOMAC terminal
  artifacts, then terminalize from its own evidence only.
- No current evidence supports `promotion_allowed=true` or `trade_usable=true`.
