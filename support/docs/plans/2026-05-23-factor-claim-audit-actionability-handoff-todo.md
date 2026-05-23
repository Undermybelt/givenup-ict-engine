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

## 2026-05-23 05:29 CST Superseding Single-Blocker Readback

Fresh factor-claim audit:

- `/tmp/ict-engine-factor-claims-refresh-20260523T0529-rerun.json` exited `1`.
- `summary.status=needs_attention`.
- `active_claims=1`.
- `terminalized_claims=65`.
- `total_claims=66`.
- `missing_run_roots=0`.
- `live_factor_processes=1`.
- `promotion_allowed_true=0`.
- `trade_usable_true=0`.
- `blocking_reasons=["active_claims","live_factor_processes"]`.

Superseding terminal claim readbacks:

- ASTS Gate 1 is no longer live. Its terminal metrics at
  `support/docs/experiments/actionable-regime-confidence/runs/20260523T051704+0800-codex-ibkr-asts-space-satellite-gap-continuation-1m-mtf-gate1-v1/checks/terminal_metrics.json`
  report `decision=provider_or_aq_blocked_no_gate1_verdict`,
  `promotion_allowed=false`, `trade_usable=false`,
  `extension_complete=false`, and `update_goal=false`.
- DASH Gate 1 is no longer live. Its terminal metrics at
  `support/docs/experiments/actionable-regime-confidence/runs/20260523T051716+0800-codex-ibkr-dash-delivery-platform-initial-balance-range-expansion-1m-mtf-gate1-v1/checks/terminal_metrics.json`
  report `decision=provider_or_aq_blocked_no_gate1_verdict`,
  `promotion_allowed=false`, `trade_usable=false`,
  `extension_complete=false`, and `update_goal=false`.
- FTNT 15m Gate 1 is terminalized under
  `support/docs/experiments/actionable-regime-confidence/runs/20260523T052155+0800-codex-ibkr-ftnt15m-cybersecurity-pda-mtf-template-transfer-gate1-v1/checks/terminal_metrics.json`.
  It has `downstream_allowed=true`, but still
  `promotion_allowed=false`, `trade_usable=false`,
  `extension_complete=false`, and `update_goal=false`.
- XOM readback is terminalized fail-closed in
  `/tmp/ict-engine-agent-claims/board-b-factor-refinement/20260523T052255+0800-codex-ibkr-xom-opening-drive-rvol-cost-stress-readback.claim`
  with `terminal_decision=drop_gate1_no_1m_2bps_or_5bps_survivor`,
  `downstream_allowed=false`, `promotion_allowed=false`, and
  `trade_usable=false`. The prior 05:24 audit caught this claim before the
  terminal append landed; the 05:29 rerun supersedes that transient row.
- The S 5m exact downstream rerun is terminalized fail-closed in
  `/tmp/ict-engine-agent-claims/board-b-factor-refinement/20260523T052500+0800-codex-ibkr-s5m-pda-mtf-template-transfer-exact-downstream.claim`;
  `execution_candidate_status=no_trade`, `transition_hazard=0.9508954331342251`,
  `pda_hybrid_alignment=false`, `promotion_allowed=false`, and
  `trade_usable=false`.

Remaining blocker:

- The only active claim is still
  `20260523T051745+0800-codex-tomac-psar-arooncci-repair-readback.claim`.
- The only live factor process is TOMAC PSAR/Aroon-CCI worker PID `93988`
  under parent PID `93976`, run root
  `/tmp/ict-engine-tomac-psar-arooncci-gate1-repair-20260523T0500+0800`.
- At 05:29 CST, `checks/01_full_repair.exit` was still missing. The durable
  stdout had advanced to `simulate-day YM day=500 date=2022-08-10
  candidates=11664`; no terminal metrics, scan results, or leaderboard files
  existed under the repair tree.

Actionability:

- Do not call the factor/audit objective complete while the TOMAC repair claim
  and process are still live.
- Do not promote FTNT from `downstream_allowed=true`; promotion and trade
  usability remain explicitly false.
- No current claim provides `promotion_allowed=true` or `trade_usable=true`.

## 2026-05-23 05:30 CST Final Live Readback

Fresh final audit after this doc sync:

- `/tmp/ict-engine-factor-claims-refresh-20260523T0530-final.json` exited `1`.
- `summary.status=needs_attention`.
- `active_claims=1`.
- `terminalized_claims=66`.
- `total_claims=67`.
- `missing_run_roots=0`.
- `live_factor_processes=1`.
- `promotion_allowed_true=0`.
- `trade_usable_true=0`.

The blocker shape is unchanged from the 05:29 readback: the only attention
claim is TOMAC PSAR/Aroon-CCI repair readback, and the only live process is
worker PID `93988` under
`/tmp/ict-engine-tomac-psar-arooncci-gate1-repair-20260523T0500+0800`.
`checks/01_full_repair.exit` is still missing.

## 2026-05-23 05:35 CST TOMAC Repair Terminalized, Claim Hygiene Pass

Fresh audit after TOMAC repair terminalization:

- `/tmp/ict-engine-factor-claims-refresh-20260523T0535-post-tomac-terminal.json`
  exited `0`.
- `summary.status=pass`.
- `active_claims=0`.
- `terminalized_claims=68`.
- `total_claims=68`.
- `missing_run_roots=0`.
- `live_factor_processes=0`.
- `promotion_allowed_true=0`.
- `trade_usable_true=0`.

TOMAC repair terminal evidence:

- Claim:
  `/tmp/ict-engine-agent-claims/board-b-factor-refinement/20260523T051745+0800-codex-tomac-psar-arooncci-repair-readback.claim`.
- Run root:
  `/tmp/ict-engine-tomac-psar-arooncci-gate1-repair-20260523T0500+0800`.
- `checks/01_full_repair.exit=143`.
- No `terminal_metrics.json`, `scan_results.json`, or `leaderboard.csv`
  materialized.
- Last durable stdout reached `simulate-day YM day=750 date=2023-05-31
  candidates=11664`; XAU was not reached.
- Decision:
  `tomac_psar_arooncci_repair_runtime_abort_no_terminal_metrics`,
  `downstream_allowed=false`, `promotion_allowed=false`,
  `trade_usable=false`, `extension_complete=false`, and `update_goal=false`.

Actionability:

- Current claim/process hygiene is clean.
- This is not practical-factor completion: current promotion/trade positives
  remain zero.
- Next valid work is a new or repaired same-root practical branch with
  provider-backed terminal metrics, hard-cost/density proof, downstream
  Pre-Bayes/BBN/CatBoost/execution-tree admission, and explicit
  `promotion_allowed=true` / `trade_usable=true` before any release claim.

## 2026-05-23 05:35 CST Release Readiness Remote Check Still Fails

Fresh release-readiness audit:

- `/tmp/ict-engine-release-readiness-goal-refresh2-20260523.json` exited `1`.
- `summary.status=needs_fix`.
- `fail_count=4`, `pass_count=1`, `skip_count=0`.
- `HEAD=e06ca1704af8ea6e9e6ee0ab85cfde6ec6fd9de4`.
- `origin/main=79d9579ea38685bd8c798dc80c1f5177e3c220b6`.
- Source is ahead of origin by `92` commits.
- Release mirror `main=ab6b1b55d516bcd0f6b88db1931cc40802e683bb`.
- `Cargo.toml` version is still `0.1.3`.
- Known release tags include `v0.1.3` and `v0.1.4`; suggested next patch is
  `0.1.5` / `v0.1.5`.

Unresolved gates:

- `worktree_clean_for_release`: current worktree readback saw `78` tracked
  dirty entries and `782` untracked entries.
- `release_docs_fresh_for_selected_tag`: release signoff and release notes are
  still marked historical/stale.
- `source_origin_matches_selected_source`: selected source commit is not on
  `origin/main`.
- `release_version_tag_available`: current `v0.1.3` tag is already used.

Actionability:

- No release, tag, push, or GitHub Release is authorized from this checkout.
- The next release-safe path is still a selected committed source slice, clean
  sanitized export, refreshed release docs for an unused tag, and a rerun of
  the full release gate set.
- The current audit question remains open despite claim hygiene passing,
  because release readiness and practical-factor proof both remain unproven.

## 2026-05-23 05:39 CST Resume Readback

Fresh resume factor-claim audit:

- `/tmp/ict-engine-factor-claims-resume.json` exited `0`.
- `summary.status=pass`.
- `active_claims=0`.
- `terminalized_claims=69`.
- `total_claims=69`.
- `missing_run_roots=0`.
- `live_factor_processes=0`.
- `promotion_allowed_true=0`.
- `trade_usable_true=0`.
- `next_action="no claim terminalization blockers found"`.

Fresh resume release-readiness audit:

- `/tmp/ict-engine-release-readiness-resume.json` exited `1`.
- `summary.status=needs_fix`.
- `fail_count=4`, `pass_count=1`, `skip_count=0`.
- `HEAD=e06ca1704af8ea6e9e6ee0ab85cfde6ec6fd9de4`.
- `origin/main=79d9579ea38685bd8c798dc80c1f5177e3c220b6`.
- Source is ahead of origin by `92` commits.
- Release mirror `main=ab6b1b55d516bcd0f6b88db1931cc40802e683bb`.
- `Cargo.toml` version remains `0.1.3`.
- Known release tags include `v0.1.3` and `v0.1.4`; suggested next patch is
  `0.1.5` / `v0.1.5`.

Unresolved release gates:

- `worktree_clean_for_release`: current worktree readback saw `78` tracked
  dirty entries and `782` untracked entries.
- `release_docs_fresh_for_selected_tag`: release signoff and release notes are
  still historical/stale for the selected tag/export.
- `source_origin_matches_selected_source`: selected source commit is not on
  `origin/main`.
- `release_version_tag_available`: current `v0.1.3` tag is already used.

Actionability:

- Claim/process hygiene is currently clean.
- This still does not close the full audit objective: no current evidence has
  `promotion_allowed=true` or `trade_usable=true`.
- No release, tag, push, or GitHub Release is authorized from this checkout.
- Next safe actions are either a release-readiness cleanup slice from a selected
  committed source export, or a fresh practical-factor proof lane with
  provider-backed terminal metrics and downstream gate admission.

## 2026-05-23 05:45 CST Live-Queue Drift After Clean Resume

Fresh factor-claim audit after the clean resume snapshot:

- `/tmp/ict-engine-factor-claims-handoff-drift-latest.json` exited `1`.
- `summary.status=needs_attention`.
- `active_claims=3`.
- `terminalized_claims=69`.
- `total_claims=72`.
- `missing_run_roots=0`.
- `live_factor_processes=5`.
- `promotion_allowed_true=0`.
- `trade_usable_true=0`.
- `blocking_reasons=["active_claims","live_factor_processes"]`.
- `next_action="terminalize or externalize active claims; wait for live factor
  processes to exit or claim them before closure"`.

Current active compact claims:

- `20260523T053853+0800-codex-ibkr-gbpjpy-fx-volatility-breakout-reclaim-1m-mtf-gate1.claim`
  is active with no terminal decision yet. It is an IBKR FX/CASH
  `GBPJPY` MIDPOINT Gate 1 lane after equity STK/TRADES preflight timeouts.
- `20260523T0540+0800-codex-ibkr-jpm-money-center-bank-dmi-adx-pullback-1m-mtf-gate1.claim`
  is active with no terminal decision yet. It targets JPM DMI/ADX
  pullback-continuation 1m-origin MTF Gate 1.
- `20260523T0545+0800-codex-tomac-kama-vortex-gate1.claim` is active with
  `promotion_allowed=false` and `trade_usable=false` in the claim body. Its
  run root is now present at
  `/tmp/ict-engine-tomac-kama-vortex-gate1-20260523T0545+0800`.

Current live process readback:

- JPM wrapper PID `60693` with active IBKR child fetches under the
  `20260523T054054+0800-codex-ibkr-jpm-money-center-bank-dmi-adx-pullback-1m-mtf-gate1-v1`
  run root.
- JPM wrapper PID `65615` with active IBKR child fetches under the
  `20260523T054412+0800-codex-ibkr-jpm-money-center-bank-dmi-adx-pullback-1m-mtf-gate1-v1`
  run root.
- TOMAC KAMA/Vortex worker PID `66220` writing to
  `/tmp/ict-engine-tomac-kama-vortex-gate1-20260523T0545+0800`.

Actionability:

- The earlier 05:39 clean factor-claim snapshot is superseded for closure
  claims by this live-queue drift readback.
- Do not call the factor/audit objective complete while these active claims or
  live factor processes remain unresolved.
- Do not infer promotion from any active claim. Promotion/trade positives remain
  zero in the latest audit.
- The useful next step is terminal readback for the GBPJPY, JPM, and TOMAC
  lanes after their wrappers exit, followed by claim terminalization or explicit
  externalization from their own evidence.

## 2026-05-23 05:47 CST Superseding Live-Queue Drift After TOMAC Smoke Terminalization

Fresh superseding factor-claim audit:

- `/tmp/ict-engine-factor-claims-refresh-20260523T054654+0800.json` exited `1`.
- `summary.status=needs_attention`.
- `active_claims=2`.
- `terminalized_claims=70`.
- `total_claims=72`.
- `missing_run_roots=0`.
- `live_factor_processes=5`.
- `promotion_allowed_true=0`.
- `trade_usable_true=0`.
- `blocking_reasons=["active_claims","live_factor_processes"]`.
- `next_action="terminalize or externalize active claims; wait for live factor
  processes to exit or claim them before closure"`.

Active claims now:

- `20260523T053853+0800-codex-ibkr-gbpjpy-fx-volatility-breakout-reclaim-1m-mtf-gate1.claim`
  remains active with no terminal decision.
- `20260523T0540+0800-codex-ibkr-jpm-money-center-bank-dmi-adx-pullback-1m-mtf-gate1.claim`
  remains active with no terminal decision. Two JPM wrappers are still live:
  PIDs `60693` and `65615`.

TOMAC KAMA/Vortex nuance:

- `20260523T0545+0800-codex-tomac-kama-vortex-gate1.claim` now has smoke
  terminal evidence at
  `/tmp/ict-engine-tomac-kama-vortex-gate1-smoke-20260523T0545+0800/terminal_metrics.json`.
- Smoke decision:
  `drop_gate1_no_hard_5bps_density_quality_survivor`.
- Smoke metrics: `candidate_count=1296`, `gate1_survivor_count=0`,
  `downstream_allowed=false`, `promotion_allowed=false`,
  `trade_usable=false`, `extension_complete=false`, and `update_goal=false`.
- The full TOMAC worker PID `66220` is still live under
  `/tmp/ict-engine-tomac-kama-vortex-gate1-20260523T0545+0800`, so closure
  remains blocked by live process state even though the smoke claim evidence is
  fail-closed.

FTNT 15m downstream root-cause readback:

- Completed downstream root:
  `support/docs/experiments/actionable-regime-confidence/runs/20260523T052155+0800-codex-ibkr-ftnt15m-cybersecurity-pda-mtf-template-transfer-gate1-v1/downstream-exact-ibkr-ftnt-15m-pda-mtf-template-transfer-20260523T053112+0800`.
- FTNT is strong but still fail-closed:
  `all_command_exits_zero=true`, `exact_branch_survived=true`,
  `execution_candidate_status=execution_ready`, execution tree `ready` /
  `fill_viable`, path-ranker visible and used, and
  `ranker_validation_ready=true`.
- Root cause for non-promotion is deterministic in the exact downstream wrapper:
  base branch-local admission requires `mature_rows >= 30`, but FTNT current
  target has only `mature_rows=3`; the wrapper then applies
  `extension_complete=false`, so final `promotion_allowed=false` and
  `trade_usable=false`.
- Do not promote FTNT from `execution_ready`, `downstream_allowed=true`,
  `review_status=promote_latest`, or ranker visibility/use alone.

Actionability:

- The 05:39 clean snapshot and 05:45 drift snapshot are superseded for closure
  claims by this readback.
- Current blocker set is: two active claims, live JPM wrappers/fetches, one live
  full TOMAC process, zero promotion/trade positives, and release readiness still
  blocked.
- Next safe action is terminal readback for GBPJPY/JPM and the full TOMAC
  process after they exit; only then terminalize/externalize claims from their
  own artifacts.

## 2026-05-23 05:46 CST Precommit Handoff Readback

Fresh precommit factor-claim audit:

- `/tmp/ict-engine-factor-claims-precommit-handoff-final.json` exited `1`.
- `summary.status=needs_attention`.
- `active_claims=2`.
- `terminalized_claims=70`.
- `total_claims=72`.
- `missing_run_roots=0`.
- `live_factor_processes=5`.
- `promotion_allowed_true=0`.
- `trade_usable_true=0`.
- `blocking_reasons=["active_claims","live_factor_processes"]`.
- `next_action="terminalize or externalize active claims; wait for live factor
  processes to exit or claim them before closure"`.

Current active compact claims:

- `20260523T053853+0800-codex-ibkr-gbpjpy-fx-volatility-breakout-reclaim-1m-mtf-gate1.claim`.
- `20260523T0540+0800-codex-ibkr-jpm-money-center-bank-dmi-adx-pullback-1m-mtf-gate1.claim`.

Live process readback still includes:

- JPM wrapper PID `60693`.
- JPM wrapper PID `65615`.
- TOMAC KAMA/Vortex worker PID `66220` under
  `/tmp/ict-engine-tomac-kama-vortex-gate1-20260523T0545+0800`.
- Two active IBKR child fetches under the JPM wrapper processes.

Actionability:

- The 05:45 TOMAC active-claim row is superseded by this readback: TOMAC no
  longer appears in `attention_claims`, but its worker is still live.
- Claim hygiene is not clean while GBPJPY/JPM active claims and live processes
  remain.
- No factor is promotion-allowed or trade-usable in this readback.
- This checkpoint is handoff evidence only. It is not release readiness, not a
  practical-factor proof, and not a publish/tag/push authorization.

## 2026-05-23 05:56 CST GBPJPY Terminalized, JPM Still Live

Fresh factor-claim audit after GBPJPY terminal readback:

- `/tmp/ict-engine-factor-claims-after-gbpjpy-readback.json` exited `1`.
- `summary.status=needs_attention`.
- `active_claims=1`.
- `terminalized_claims=72`.
- `total_claims=73`.
- `missing_run_roots=0`.
- `live_factor_processes=2`.
- `promotion_allowed_true=0`.
- `trade_usable_true=0`.
- `blocking_reasons=["active_claims","live_factor_processes"]`.
- `next_action="terminalize or externalize active claims; wait for live factor
  processes to exit or claim them before closure"`.

GBPJPY terminal evidence:

- Claim:
  `/tmp/ict-engine-agent-claims/board-b-factor-refinement/20260523T053853+0800-codex-ibkr-gbpjpy-fx-volatility-breakout-reclaim-1m-mtf-gate1.claim`.
- Run root:
  `support/docs/experiments/actionable-regime-confidence/runs/20260523T054916+0800-codex-ibkr-gbpjpy-fx-volatility-breakout-reclaim-1m-mtf-gate1-v1`.
- Decision: `drop_gate1_no_exact_1m_5bps_density_survivor`.
- Provider data acquired for `7` ladder legs; `material_count=14`,
  `rank_rows=14`, and `rank_total_trade_count=1114`.
- The exact 1m best row had `16` trades, `1.333333/day`, raw `-0.29%`, and
  `5bps/side=-1.89%`.
- `downstream_allowed=false`, `promotion_allowed=false`,
  `trade_usable=false`, `extension_complete=false`, and `update_goal=false`.

Remaining active blocker:

- `20260523T0540+0800-codex-ibkr-jpm-money-center-bank-dmi-adx-pullback-1m-mtf-gate1.claim`
  remains active with no terminal decision.
- JPM wrapper PID `60693` is still live. Its latest observed child was an IBKR
  JPM daily fetch under
  `support/docs/experiments/actionable-regime-confidence/runs/20260523T054054+0800-codex-ibkr-jpm-money-center-bank-dmi-adx-pullback-1m-mtf-gate1-v1`.
- JPM fetch exits observed so far are still provider timeout/empty-data exits
  (`exit=3`) across the checked `1m/5m/15m/30m/1h/4h/1d` windows; no
  `terminal_metrics.json`, `terminal_decision_summary.md`, or cost-stress table
  has materialized yet.

Actionability:

- GBPJPY is fail-closed observation evidence only.
- The current factor-claim closure blocker is JPM plus its live process.
- Do not call factor-claim hygiene clean until JPM either terminalizes or is
  explicitly externalized from its own evidence.
- Release readiness remains separate and still blocked by the release audit.

## 2026-05-23 06:02 CST JPM Terminalized, TOMAC Choppiness Reopened Queue

Fresh factor-claim audit after JPM terminalization:

- `/tmp/ict-engine-factor-claims-after-jpm-terminalization-20260523T060019+0800.json`
  exited `1`.
- `summary.status=needs_attention`.
- `active_claims=1`.
- `terminalized_claims=73`.
- `total_claims=74`.
- `missing_run_roots=1`.
- `live_factor_processes=0`.
- `promotion_allowed_true=0`.
- `trade_usable_true=0`.
- `blocking_reasons=["active_claims","missing_run_roots"]`.
- `next_action="terminalize or externalize active claims; restore or
  terminalize missing run roots"`.

JPM terminal evidence:

- Claim:
  `/tmp/ict-engine-agent-claims/board-b-factor-refinement/20260523T0540+0800-codex-ibkr-jpm-money-center-bank-dmi-adx-pullback-1m-mtf-gate1.claim`.
- Run root:
  `support/docs/experiments/actionable-regime-confidence/runs/20260523T054054+0800-codex-ibkr-jpm-money-center-bank-dmi-adx-pullback-1m-mtf-gate1-v1`.
- Decision: `blocked_provider_runtime_no_candles`.
- Terminal metrics:
  `support/docs/experiments/actionable-regime-confidence/runs/20260523T054054+0800-codex-ibkr-jpm-money-center-bank-dmi-adx-pullback-1m-mtf-gate1-v1/checks/terminal_metrics.json`.
- Terminal summary:
  `support/docs/experiments/actionable-regime-confidence/runs/20260523T054054+0800-codex-ibkr-jpm-money-center-bank-dmi-adx-pullback-1m-mtf-gate1-v1/summaries/terminal_decision_summary.md`.
- Provider rows by timeframe are all zero:
  `1m=0`, `5m=0`, `15m=0`, `30m=0`, `1h=0`, `4h=0`, `1d=0`.
- Command exits are `00_provider_status_ibkr=0` and all selected fetch windows
  `=3`.
- `ranked_row_count=0`, `downstream_allowed=false`,
  `pre_bayes_allowed=false`, `bbn_allowed=false`, `catboost_allowed=false`,
  `execution_tree_allowed=false`, `promotion_allowed=false`,
  `trade_usable=false`, and `update_goal=false`.

New active blocker:

- `20260523T055929+0800-codex-tomac-choppiness-gate1.claim`.
- Scope: local TOMAC NQ/YM/XAU choppiness breakout and retest/reclaim Gate 1.
- Claimed roots:
  `/tmp/ict-engine-tomac-choppiness-gate1-20260523T055929+0800` and
  `/tmp/ict-engine-tomac-choppiness-gate1-smoke-20260523T055929+0800`.
- The compact audit marks the run root as missing and the claim as active.
- Targeted live-process readback at 06:01 CST found no matching TOMAC
  choppiness worker, but no terminal evidence exists in the claim yet.

Actionability:

- JPM is provider/runtime-blocked observation evidence, not a factor economics
  verdict and not promotion/trade evidence.
- The factor-claim queue is not clean because TOMAC choppiness is active with a
  missing run root in the current audit.
- Do not call the active goal complete: current promotion/trade positives remain
  zero, and release readiness remains blocked.

## 2026-05-23 06:04 CST Final Verification Drift Supersedes 06:02

Fresh final factor-claim audit:

- `/tmp/ict-engine-factor-claims-final-refresh-20260523T060423+0800.json`
  exited `1`.
- `summary.status=needs_attention`.
- `active_claims=2`.
- `terminalized_claims=74`.
- `total_claims=76`.
- `missing_run_roots=1`.
- `live_factor_processes=2`.
- `promotion_allowed_true=0`.
- `trade_usable_true=0`.
- `blocking_reasons=["active_claims","live_factor_processes","missing_run_roots"]`.
- `next_action="terminalize or externalize active claims; wait for live factor
  processes to exit or claim them before closure; restore or terminalize
  missing run roots"`.

Superseding attention claims:

- `20260523T055929+0800-codex-tomac-choppiness-gate1.claim` is now
  terminalized as
  `blocked_missing_run_root_self_test_failure_no_terminal_metrics`, but remains
  an attention item because its declared run root is missing. It has
  `promotion_allowed=false` and `trade_usable=false`.
- `20260523T055947+0800-codex-ibkr-eurusd-fx-london-orb-retest-1m-mtf-gate1.claim`
  is active/claimed, with `promotion_allowed=false` and
  `trade_usable=false` until Gate 1 proves otherwise.
- `20260523T0602+0800-codex-ibkr-usdjpy-fx-dmi-adx-pullback-1m-mtf-gate1.claim`
  is active. Live process readback shows USDJPY wrapper PID `95345` and IBKR
  child fetch PID `96849` under
  `support/docs/experiments/actionable-regime-confidence/runs/20260523T060301+0800-codex-ibkr-usdjpy-fx-dmi-adx-pullback-1m-mtf-gate1-v1`.

Actionability:

- The 06:02 queue state is superseded by the final verification drift above.
- Claim/process hygiene is not green.
- There is still no current `promotion_allowed=true` or `trade_usable=true`
  factor evidence, so the practical-factor diffusion objective remains open.

## 2026-05-23 05:59 CST JPM Terminalized, Claim Hygiene Pass

Fresh factor-claim audit after JPM terminalization:

- `/tmp/ict-engine-factor-claims-post-jpm-terminal.json` exited `0`.
- `summary.status=pass`.
- `active_claims=0`.
- `terminalized_claims=73`.
- `total_claims=73`.
- `missing_run_roots=0`.
- `live_factor_processes=0`.
- `promotion_allowed_true=0`.
- `trade_usable_true=0`.
- `next_action="no claim terminalization blockers found"`.

JPM terminal evidence:

- Claim:
  `/tmp/ict-engine-agent-claims/board-b-factor-refinement/20260523T0540+0800-codex-ibkr-jpm-money-center-bank-dmi-adx-pullback-1m-mtf-gate1.claim`.
- Run root:
  `support/docs/experiments/actionable-regime-confidence/runs/20260523T054054+0800-codex-ibkr-jpm-money-center-bank-dmi-adx-pullback-1m-mtf-gate1-v1`.
- Decision: `blocked_provider_runtime_no_candles`.
- Provider status exited `0`, but every JPM historical fetch window exited `3`
  and produced `0` rows across `1m/5m/15m/30m/1h/4h/1d`.
- `ranked_row_count=0`, `branch_fields_preserved=false`, and there are no
  `5bps+density` survivors.
- `downstream_allowed=false`, `pre_bayes_allowed=false`, `bbn_allowed=false`,
  `catboost_allowed=false`, `execution_tree_allowed=false`,
  `promotion_allowed=false`, `trade_usable=false`, and `update_goal=false`.

Fresh release-readiness audit:

- `/tmp/ict-engine-release-readiness-post-jpm-terminal.json` exited `1`.
- `summary.status=needs_fix`.
- `fail_count=4`, `pass_count=1`, `skip_count=0`.
- `HEAD=88ccea762ceefc764fdb31845adfa6d60f26b384`.
- Source is ahead of `origin/main` by `93` commits.
- Current version remains `0.1.3`; known release tags include `v0.1.3` and
  `v0.1.4`; suggested next patch is `0.1.5` / `v0.1.5`.

Unresolved release gates:

- `worktree_clean_for_release`: `78` tracked dirty entries and `782` untracked
  entries remain in the broad checkout.
- `release_docs_fresh_for_selected_tag`: release signoff and release notes are
  still historical/stale for the selected export.
- `source_origin_matches_selected_source`: selected source commit is not on
  `origin/main`.
- `release_version_tag_available`: `v0.1.3` is already used.

Actionability:

- Factor-claim/process hygiene is currently clean.
- This does not complete the full audit goal: promotion/trade positives remain
  zero, and release readiness still fails.
- No release, tag, push, GitHub Release, or trade/promotion language is
  authorized from this state.
- Next useful work is a release-readiness cleanup/export slice or a new
  practical-factor proof lane with explicit `promotion_allowed=true` and
  `trade_usable=true` from downstream gates.

## 2026-05-23 06:25 CST Bybit Terminalized, Claim Hygiene Pass, Release Still Blocked

Fresh factor-claim audit after the live EURUSD, USDJPY, TOMAC Choppiness, and
Bybit public crypto lanes exited and were terminalized:

- `/tmp/ict-engine-factor-claims-after-bybit-vol-terminalization-20260523T062053+0800.json`
  exited `0`.
- `summary.status=pass`.
- `active_claims=0`.
- `terminalized_claims=78`.
- `total_claims=78`.
- `missing_run_roots=0`.
- `live_factor_processes=0`.
- `promotion_allowed_true=0`.
- `trade_usable_true=0`.
- `next_action="no claim terminalization blockers found"`.

Terminalized evidence since the 06:04 drift checkpoint:

- USDJPY:
  `support/docs/experiments/actionable-regime-confidence/runs/20260523T060301+0800-codex-ibkr-usdjpy-fx-dmi-adx-pullback-1m-mtf-gate1-v1`,
  decision `drop_gate1_no_exact_1m_5bps_density_survivor`.
- EURUSD:
  `support/docs/experiments/actionable-regime-confidence/runs/20260523T061001+0800-codex-ibkr-eurusd-fx-london-orb-retest-1m-mtf-gate1-v1`,
  decision `drop_gate1_no_exact_1m_5bps_density_survivor`.
- TOMAC Choppiness:
  `/tmp/ict-engine-tomac-choppiness-gate1-20260523T055929+0800`,
  decision `drop_gate1_no_hard_5bps_density_quality_survivor`.
- Bybit public crypto volatility pullback/reclaim:
  `support/docs/experiments/actionable-regime-confidence/runs/20260523T061432+0800-codex-bybit-crypto-vol-pullback-reclaim-1m-full-ladder-gate1-v1`,
  decision `higher_timeframe_subclass_only_origin_blocked`.

Bybit nuance:

- The Bybit run had high-timeframe/subclass rows that survived cost stress, for
  example SOLUSDT `1h` and `4h`, but the claimed 1m-origin branch did not meet
  the exact origin plus hard 5bps/density gate.
- The Bybit claim is therefore observation/subclass evidence only:
  `downstream_allowed=false`, `promotion_allowed=false`, `trade_usable=false`,
  and `update_goal=false`.

Fresh release-readiness audit:

- `/tmp/ict-engine-release-readiness-after-bybit-vol-terminalization-20260523T062053+0800.json`
  exited `1`.
- `summary.status=needs_fix`.
- `fail_count=4`, `pass_count=1`, `skip_count=0`.
- `HEAD=88ccea762ceefc764fdb31845adfa6d60f26b384`.
- Source is ahead of `origin/main` by `93` commits.
- Current version remains `0.1.3`; known release tags include `v0.1.3` and
  `v0.1.4`; suggested next patch remains `0.1.5` / `v0.1.5`.

Unresolved release gates remain unchanged:

- `worktree_clean_for_release`.
- `release_docs_fresh_for_selected_tag`.
- `source_origin_matches_selected_source`.
- `release_version_tag_available`.

Actionability:

- The superseding claim/process hygiene state is clean at 06:25 CST.
- The practical-factor objective is still open because
  `promotion_allowed_true=0` and `trade_usable_true=0`.
- Release is still blocked by readiness gates and broad dirty worktree state.
- Do not release, tag, push, promote, or describe any factor as trade-usable
  from this state.
- Next coherent slices are either release cleanup/export readiness or a new
  isolated practical-factor proof lane.

## 2026-05-23 07:13 CST SOUN/Bybit/TOMAC Alligator Terminalized, Claim Hygiene Pass

Fresh factor-claim audit after SOUN, AERO/ZRO, GMX/ZETA, DASH/ZEC, and TOMAC
Alligator/Fractal terminalization:

- `/tmp/ict-engine-factor-claims-final-current-20260523T071328+0800.json`
  exited `0`.
- `summary.status=pass`.
- `active_claims=0`.
- `terminalized_claims=93`.
- `total_claims=93`.
- `missing_run_roots=0`.
- `live_factor_processes=0`.
- `promotion_allowed_true=0`.
- `trade_usable_true=0`.
- `next_action="no claim terminalization blockers found"`.

Terminalized evidence since the 06:25 checkpoint:

- SOUN voice-AI momentum expansion:
  `support/docs/experiments/actionable-regime-confidence/runs/20260523T064857+0800-codex-ibkr-soun-voice-ai-momentum-expansion-1m-mtf-gate1-v1`,
  decision `provider_or_aq_blocked_no_gate1_verdict`. IBKR provider status
  passed, but all requested/retry OHLCV fetches returned zero rows with exit
  `3`; no material rows, no rank rows, no downstream.
- Bybit AERO/ZRO PPO histogram reclaim:
  `support/docs/experiments/actionable-regime-confidence/runs/20260523T070020+0800-codex-bybit-aero-zro-ppo-histogram-reclaim-1m-full-ladder-gate1-v1`,
  decision `higher_timeframe_subclass_only_exact_1m_blocked`.
- Bybit GMX/ZETA Schaff Trend Cycle:
  `support/docs/experiments/actionable-regime-confidence/runs/20260523T070409+0800-codex-bybit-gmx-zeta-schaff-trend-cycle-1m-full-ladder-gate1-v1`,
  decision `higher_timeframe_subclass_only_origin_blocked`.
- Bybit DASH/ZEC Awesome/Accelerator:
  `support/docs/experiments/actionable-regime-confidence/runs/20260523T070459+0800-codex-bybit-dash-zec-awesome-accelerator-1m-full-ladder-v1`,
  decision `drop_gate1_cost_or_density_failed`.
- TOMAC NQ/YM/XAU Alligator/Fractal:
  `/tmp/ict-engine-tomac-alligator-fractal-gate1-20260523T065631+0800`,
  decision `drop_gate1_no_hard_5bps_density_quality_survivor`,
  `candidate_count=1350`, `gate1_survivor_count=0`.

Actionability:

- Claim/process hygiene is clean in this snapshot.
- The practical-factor objective remains open because
  `promotion_allowed_true=0` and `trade_usable_true=0`.
- Release readiness is separate and still fails in the matching release audit.
- Do not release, tag, push, promote, or describe any factor as trade-usable
  from this state.

## 2026-05-23 07:28 CST Superseding Drift: Active Claims And Live Work Returned

Fresh factor-claim audit after terminalizing stale DUOL and DYDX/APE claim
metadata:

- `/tmp/ict-engine-factor-claims-resume-20260523T072855+0800.json`
  exited `1`.
- `summary.status=needs_attention`.
- `active_claims=5`.
- `terminalized_claims=98`.
- `total_claims=103`.
- `missing_run_roots=0`.
- `live_factor_processes=5`.
- `promotion_allowed_true=0`.
- `trade_usable_true=0`.

Current active blockers:

- XBI Williams/MFI reclaim remains claimed and waiting for IBKR contention to
  clear; no run root exists yet.
- TOMAC TOD BalancedAdaptiveSlotPortfolio rebuild remains active; the density
  repair scan is live under PID `14171`, with `portfolio_root` still in
  progress.
- NTNX Bayesian-Markov trend detector remains active; wrapper PID `10905` and
  child IBKR fetch PID `15620` were live against the `15m 3M` request.
- USDCHF Bollinger squeeze mean-reclaim remains validated but pending launch
  until the active IBKR fetch clears.
- Bybit NEO/QTUM Mass Index remains active; wrapper PID `15006` and
  Auto-Quant dispatch/run_tomac descendants were live.

Terminalized since the 07:13 clean snapshot:

- DUOL Keltner/RSI reclaim:
  `support/docs/experiments/actionable-regime-confidence/runs/20260523T071951+0800-codex-ibkr-duol-language-learning-keltner-rsi-reclaim-1m-mtf-gate1-v1`,
  decision `provider_blocked_no_1m_origin_data_no_gate1_verdict`.
- Bybit DYDX/APE Elder Ray:
  `support/docs/experiments/actionable-regime-confidence/runs/20260523T072042+0800-codex-bybit-dydx-ape-elder-ray-power-1m-full-ladder-v1`,
  decision `higher_timeframe_subclass_only_origin_blocked`.

Actionability:

- The 07:13 clean claim/process checkpoint is superseded by this 07:28 drift.
- The factor objective remains open: zero `promotion_allowed=true`, zero
  `trade_usable=true`, five active claims, and five live factor processes.
- Do not release, tag, push, promote, describe any factor as trade-usable, or
  call `update_goal complete` from this state.

## 2026-05-23 07:39 CST Corrected Claim Hygiene Pass, No Practical Factor Yet

Fresh factor-claim audit after terminalizing/externalizing the post-07:13
active lanes:

- `/tmp/ict-engine-factor-claims-resume-20260523T073957+0800.json`
  exited `0`.
- `summary.status=pass`.
- `active_claims=0`.
- `terminalized_claims=103`.
- `total_claims=103`.
- `missing_run_roots=0`.
- `live_factor_processes=0`.
- `promotion_allowed_true=0`.
- `trade_usable_true=0`.
- `next_action="no claim terminalization blockers found"`.

Terminalized or externalized since the 07:28 drift checkpoint:

- Bybit NEO/QTUM Mass Index:
  `/tmp/ict-engine-bybit-neo-qtum-mass-index-reversal-1m-full-ladder-20260523T072137+0800`,
  decision `drop_gate1_no_hard_5bps_density_survivor`.
- TOMAC TOD BalancedAdaptiveSlotPortfolio prerequisite summary:
  `/tmp/ict-engine-tomac-tod-balanced-portfolio-rebuild-broad-20260523T071334+0800/portfolio_summary.json`
  had `2299` trades, `1.4775064267352185` trades/all-session, and
  `5bps` net return `0.5744555991316406`, but exact AQ/downstream was not run;
  decision `prerequisite_portfolio_summary_ready_exact_aq_pending_no_promotion`.
- NTNX Bayesian-Markov trend detector:
  `support/docs/experiments/actionable-regime-confidence/runs/20260523T072352+0800-codex-ibkr-ntnx-bayesian-markov-trend-detector-1m-mtf-gate1-v1`,
  decision `provider_or_aq_blocked_no_gate1_verdict`, with all provider retry
  legs exiting `3` and no rank rows.
- XBI Williams/MFI and USDCHF Bollinger squeeze were externalized as
  `externalized_pending_ibkr_contention_no_factor_verdict`; they were not
  launched and have no factor verdict.

Audit fix landed in this slice:

- `support/scripts/factor_claim_terminalization_audit.py` now detects TOMAC
  helper scans such as `tomac_tod_portfolio_density_repair_scan.py`.
- `python3 -m unittest support.scripts.tests.test_factor_claim_terminalization_audit`
  passed `18` tests.

Actionability:

- Claim/process hygiene is clean again in this snapshot.
- The practical-factor objective remains open because
  `promotion_allowed_true=0` and `trade_usable_true=0`.
- Do not release, tag, push, promote, describe any factor as trade-usable, or
  call `update_goal complete` from this state.

## 2026-05-23 10:12 CST Claim Hygiene Clean, Candidate-Pack Metadata Repair Is Release-Only

Fresh factor-claim audit:

- `/tmp/ict-engine-factor-claims-continuation-20260523T101244+0800.json`
  exited `0`.
- `summary.status=pass`.
- `active_claims=0`.
- `terminalized_claims=126`.
- `total_claims=126`.
- `missing_run_roots=0`.
- `live_factor_processes=0`.
- `promotion_allowed_true=0`.
- `trade_usable_true=0`.
- `next_action="no claim terminalization blockers found"`.

Candidate-pack metadata repair precheck:

- The dirty three-file JSON slice under
  `support/examples/factor_candidate_packs/curated-auto-quant-v1/family_d_liquidity_sweep_reclaim_15m_wide_v1/`
  adds `expected_regime`, `branch_path_contract`, `timeframe_ladder_evidence`,
  and `timeframe_ladder_transfer` metadata.
- The slice explicitly preserves `promotion_allowed=false` and
  `trade_usable=false`; this is release/source coherency repair evidence, not a
  practical-trading promotion.
- `cargo test cli_surface_tests::test_factor_candidate_admission_target_builder_lives_in_orchestration_owner -- --nocapture`
  passed in the dirty worktree.
- `cargo test tests::test_build_factor_candidate_pack_inventory_reads_curated_packs -- --nocapture`
  passed in the dirty worktree.

Actionability:

- Claim/process hygiene is clean again in this snapshot.
- The practical-factor objective remains open because
  `promotion_allowed_true=0`, `trade_usable_true=0`, and the metadata repair only
  fixes selected-source coherency for a candidate that remains observation-only.
- Do not release, tag, push, promote, describe any factor as trade-usable, or
  call `update_goal complete` from this state.

## 2026-05-23 09:58 CST Claim Hygiene Clean, Release Export Found Data-Slice Blocker

Fresh factor-claim audit:

- `/tmp/ict-engine-factor-claims-continuation-20260523T095813+0800.json`
  exited `0`.
- `summary.status=pass`.
- `active_claims=0`, `missing_run_roots=0`, `live_factor_processes=0`.
- `terminalized_claims=123`, `total_claims=123`.
- `promotion_allowed_true=0`, `trade_usable_true=0`.

Actionability:

- Claim/process hygiene remains clean, but the practical-factor objective is not
  complete because zero factors are promotable or trade-usable.
- The release side also found a concrete clean-export blocker: committed `HEAD`
  has tests expecting the Family D liquidity-sweep branch-path contract, while
  that candidate-pack metadata exists only in dirty working-tree JSON. This is a
  release-source-slice issue, not a practical-factor promotion.
- Do not release, tag, push, promote, describe any factor as trade-usable, or
  call `update_goal complete` from this state.

## 2026-05-23 09:30 CST Superseding Claim Hygiene Clean, Still No Trade-Usable Factor

Fresh factor-claim audit after the 09:26 checkpoint:

- `/tmp/ict-engine-factor-claims-continuation-20260523T093047+0800.json`
  exited `0`.
- `summary.status=pass`.
- `active_claims=0`, `missing_run_roots=0`, `live_factor_processes=0`.
- `terminalized_claims=123`, `total_claims=123`.
- `promotion_allowed_true=0`, `trade_usable_true=0`.

Fresh process probe:

- A transient TOMAC cap65 `policy-training-status` process was visible at the
  first 09:30 readback, but a focused `ps -p` readback immediately afterward
  found no such PID. No live factor process blocker remained in the compact
  factor audit.

Actionability:

- The 09:26 checkpoint is superseded by the 09:30 checkpoint, not by a
  completion signal.
- Claim/process hygiene remains clean in this snapshot.
- The practical-factor objective remains open because zero factors are
  promotable or trade-usable.
- Do not release, tag, push, promote, describe any factor as trade-usable, or
  call `update_goal complete` from this state.

## 2026-05-23 09:54 CST Resume Readback: Claim Hygiene Clean, No Practical Factor

Fresh factor-claim audit after interruption/resume:

- `/tmp/ict-engine-factor-claims-continuation-20260523T095449+0800.json`
  exited `0`.
- `summary.status=pass`.
- `active_claims=0`, `missing_run_roots=0`, `live_factor_processes=0`.
- `terminalized_claims=123`, `total_claims=123`.
- `promotion_allowed_true=0`, `trade_usable_true=0`.

Fresh process probe:

- The only matches were the `ps | rg` probe itself. No live factor training,
  Auto-Quant, provider fetch, or downstream `ict-engine` process was visible.

Actionability:

- The 09:33 checkpoint is superseded by the 09:54 checkpoint, not by a
  completion signal.
- Claim/process hygiene remains clean in this snapshot.
- The practical-factor objective remains open because zero factors are
  promotable or trade-usable.
- Do not release, tag, push, promote, describe any factor as trade-usable, or
  call `update_goal complete` from this state.

## 2026-05-23 09:33 CST Superseding Claim Hygiene Clean, Factor Objective Still Open

Fresh factor-claim audit after the 09:30 checkpoint:

- `/tmp/ict-engine-factor-claims-continuation-20260523T093348+0800.json`
  exited `0`.
- `summary.status=pass`.
- `active_claims=0`, `missing_run_roots=0`, `live_factor_processes=0`.
- `terminalized_claims=123`, `total_claims=123`.
- `promotion_allowed_true=0`, `trade_usable_true=0`.

Fresh process probe:

- The only matches were the `ps | rg` probe itself. No live factor training,
  Auto-Quant, provider fetch, or downstream `ict-engine` process was visible.

Actionability:

- The 09:30 checkpoint is superseded by the 09:33 checkpoint, not by a
  completion signal.
- Claim/process hygiene remains clean in this snapshot.
- The practical-factor objective remains open because zero factors are
  promotable or trade-usable.
- Do not release, tag, push, promote, describe any factor as trade-usable, or
  call `update_goal complete` from this state.

## 2026-05-23 09:26 CST Superseding Clean Claim Hygiene, TOMAC Downstream Fail-Closed

Fresh factor-claim audit after the BOME/TURBO, SMR, EURGBP, and TOMAC cap65
downstream readbacks were normalized into terminal/externalized claim metadata:

- `/tmp/ict-engine-factor-claims-continuation-20260523T092617+0800.json`
  exited `0`.
- `summary.status=pass`.
- `active_claims=0`.
- `terminalized_claims=123`.
- `total_claims=123`.
- `missing_run_roots=0`.
- `live_factor_processes=0`.
- `promotion_allowed_true=0`.
- `trade_usable_true=0`.
- `next_action="no claim terminalization blockers found"`.

Terminalized or externalized since the 08:23 checkpoint:

- TOMAC TOD BalancedAdaptiveSlotPortfolio cap65 downstream:
  `/tmp/ict-engine-tomac-tod-cap65-downstream-20260523T083547+0800`,
  decision `cap65_downstream_fail_closed_or_incomplete`; real trade rows `1638`,
  command `09_ingest_real_trades.exit=124`, `mature_rows=3`,
  `history_mature_rows=1641`, `execution_candidate_actionable=false`,
  `execution_candidate_status=no_trade`, `execution_readiness=0.37842405925447914`,
  `pda_hybrid_alignment=false`, path-ranker visible/used/validation-ready all
  `false`, and `promotion_allowed=false` / `trade_usable=false`.
- Bybit BOME/TURBO Darvas box breakout:
  `support/docs/experiments/actionable-regime-confidence/runs/20260523T084135+0800-codex-bybit-bome-turbo-darvas-box-breakout-1m-full-ladder-v1`,
  decision `drop_gate1_no_hard_5bps_density_survivor`; BOME provider rows were
  fetched, TURBO was invalid on the Bybit linear path, AQ rank rows had zero
  trades, and all downstream/promotion/trade gates remain `false`.
- IBKR SMR small-modular-nuclear initial-balance range-expansion:
  claim externalized as `externalized_prelaunch_no_run_root_no_factor_evidence`;
  no run root or live process was found, so this is claim hygiene only and not a
  factor result.
- IBKR EURGBP FX volatility breakout/reclaim:
  `support/docs/experiments/actionable-regime-confidence/runs/20260523T085036+0800-codex-ibkr-eurgbp-fx-volatility-breakout-reclaim-1m-mtf-gate1-v1`,
  decision `drop_gate1_no_exact_1m_5bps_density_survivor`; `14` AQ rank rows,
  exact `1m` rows had `5-6` trades but negative after hard `5bps/side`, and
  downstream remains forbidden.

Actionability:

- Claim/process hygiene is clean again in this snapshot.
- TOMAC cap65 remains useful negative downstream evidence: the prior Gate 1
  survivor did not become promotable or trade-usable.
- The practical-factor objective remains open because
  `promotion_allowed_true=0` and `trade_usable_true=0`.
- Do not release, tag, push, promote, describe any factor as trade-usable, or
  call `update_goal complete` from this state.

## 2026-05-23 08:23 CST Superseding Clean Claim Hygiene, Gate 1 Evidence Still Not Promotion

Fresh factor-claim audit after the post-07:58 USDCAD/CADJPY/BONK-FLOKI/GALA-GMT
drift and the TOMAC cap65 suppressed AQ run:

- `/tmp/ict-engine-factor-claims-continuation-20260523T082357+0800.json`
  exited `0`.
- `summary.status=pass`.
- `active_claims=0`.
- `terminalized_claims=114`.
- `total_claims=114`.
- `missing_run_roots=0`.
- `live_factor_processes=0`.
- `promotion_allowed_true=0`.
- `trade_usable_true=0`.
- `next_action="no claim terminalization blockers found"`.

Terminalized or reclassified since the 07:58 checkpoint:

- IBKR CADJPY FX Donchian/Turtle breakout-retest:
  `support/docs/experiments/actionable-regime-confidence/runs/20260523T080227+0800-codex-ibkr-cadjpy-fx-donchian-turtle-breakout-retest-1m-mtf-gate1-v1`,
  decision `drop_gate1_no_exact_1m_5bps_density_survivor`; `6` provider legs,
  `12` rank rows, `1312` ranked trades, no `1/2/5bps` survivors, and no
  downstream.
- IBKR USDCAD FX Donchian/Turtle retest:
  `support/docs/experiments/actionable-regime-confidence/runs/20260523T080304+0800-codex-ibkr-usdcad-fx-donchian-turtle-retest-1m-mtf-gate1-v1`,
  decision `drop_gate1_no_exact_1m_5bps_density_survivor`; `7` provider legs,
  `14` rank rows, `655` ranked trades, some `1/2bps` non-practical survivors,
  no `5bps` or exact-origin survivor, and no downstream.
- Bybit BONK/FLOKI VWAPDEV/OBVRSI:
  `support/docs/experiments/actionable-regime-confidence/runs/20260523T080742+0800-codex-bybit-bonk-floki-vwapdev-obvrsi-reclaim-1m-full-ladder-v1`,
  decision `drop_gate1_no_hard_5bps_density_survivor`; `14` provider rows,
  `14` rank rows, `19` ranked trades, no origin or any hard `5bps` density
  survivor.
- Bybit GALA/GMT RWI trend breakout:
  `support/docs/experiments/actionable-regime-confidence/runs/20260523T081826+0800-codex-bybit-gala-gmt-rwi-trend-breakout-1m-full-ladder-v1`,
  decision `higher_timeframe_subclass_only_origin_blocked`; `GMTUSDT 5m`
  survived hard `5bps` as subclass evidence, but exact `1m` origin survivors
  were empty and downstream remained forbidden.
- TOMAC TOD BalancedAdaptiveSlotPortfolio cap65 suppressed AQ:
  `/tmp/ict-engine-tomac-tod-balanced-portfolio-cap65-aq-suppressed-20260523T0816+0800`,
  decision `gate1_autoquant_cost_density_survivor_downstream_required`;
  vector trades `1644`, executable vector trades `1638`, suppressed entries
  `6`, signal rows `3282`, `5bps` survivor
  `tomac_tod_balanced_adaptive_slot_portfolio_exact_v1`, but
  `promotion_allowed=false`, `trade_usable=false`, `catboost_allowed=false`,
  and `execution_tree_allowed=false`.

Verification in this slice:

- `python3 -m unittest support.scripts.tests.test_factor_claim_terminalization_audit`
  passed `18` tests.
- `git diff --check -- support/scripts/factor_claim_terminalization_audit.py support/scripts/tests/test_factor_claim_terminalization_audit.py support/docs/plans/2026-05-23-factor-claim-audit-actionability-handoff-todo.md support/docs/plans/2026-05-22-done-definition-audit-handoff-todo.md support/docs/plans/2026-05-12-hotplug-personal-data-release-handoff-todo.md`
  exited `0` before this append; rerun after append is required for the final
  verification bundle.

Actionability:

- Claim/process hygiene is clean again in this snapshot.
- The practical-factor objective remains open because
  `promotion_allowed_true=0`, `trade_usable_true=0`, and the only fresh
  positive Gate 1 result explicitly requires downstream proof.
- Do not release, tag, push, promote, describe any factor as trade-usable, or
  call `update_goal complete` from this state.

## 2026-05-23 07:58 CST Superseding Clean Claim Hygiene, Still No Practical Factor

Fresh factor-claim audit after post-07:39 APE/USDCHF/XBI/TOMAC/Bybit drift was
terminalized from artifacts:

- `/tmp/ict-engine-factor-claims-resume-20260523T075832+0800.json`
  exited `0`.
- `summary.status=pass`.
- `active_claims=0`.
- `terminalized_claims=109`.
- `total_claims=109`.
- `missing_run_roots=0`.
- `live_factor_processes=0`.
- `promotion_allowed_true=0`.
- `trade_usable_true=0`.
- `next_action="no claim terminalization blockers found"`.

Terminalized or reclassified since the 07:39 checkpoint:

- APEUSDT exact 5m Elder Ray:
  `support/docs/experiments/actionable-regime-confidence/runs/20260523T074059+0800-codex-bybit-apeusdt-5m-elder-ray-power-exact-gate1-v1`,
  decision `keep_exact_5m_gate1_cost_survivor_downstream_fail_closed`.
  Gate 1 kept a tiny exact 5m survivor (`6` trades, `5bps/side=+0.12%`,
  density `1.73/day`), but downstream stayed fail-closed:
  `execution_candidate_actionable=false`, `execution_candidate_status=no_trade`,
  `execution_readiness=0.487050812943753`,
  `transition_hazard=0.9875370421259952`,
  `pda_hybrid_alignment=false`, path-ranker visible but not used, and
  `promotion_allowed=false` / `trade_usable=false`.
- USDCHF FX Bollinger squeeze:
  `support/docs/experiments/actionable-regime-confidence/runs/20260523T074020+0800-codex-ibkr-usdchf-fx-bollinger-squeeze-mean-reclaim-1m-mtf-gate1-v1`,
  decision `drop_gate1_no_exact_1m_5bps_density_survivor`; `7` provider legs,
  `14` material/rank rows, `58` ranked trades, but zero 1/2/5bps survivors and
  no downstream.
- XBI Williams/MFI:
  `support/docs/experiments/actionable-regime-confidence/runs/20260523T074037+0800-codex-ibkr-xbi-biotech-etf-williams-mfi-reclaim-1m-mtf-gate1-v1`,
  decision `provider_or_aq_blocked_no_gate1_verdict`; provider/material/AQ did
  not produce rank rows, so this is infrastructure-blocked evidence only.
- TOMAC TOD broad exact AQ:
  `/tmp/ict-engine-tomac-tod-balanced-portfolio-exact-aq-broad-20260523T074209+0800`,
  decision `exact_autoquant_replay_no_parity_or_5bps_density_survivor`;
  compile/run exited `0`, vector trades `2299`, executable trades `2299`,
  signal sidecar rows `4598`, and `5bps survivors=[]`.
- TOMAC TOD cap65 exact AQ:
  `/tmp/ict-engine-tomac-tod-balanced-portfolio-cap65-aq-20260523T074346+0800`,
  decision `exact_autoquant_replay_no_parity_or_5bps_density_survivor`;
  compile/run exited `0`, vector trades `1644`, executable trades `1644`,
  signal sidecar rows `3288`, and `5bps survivors=[]`.
- Bybit ALGO/XTZ Choppiness:
  `support/docs/experiments/actionable-regime-confidence/runs/20260523T074908+0800-codex-bybit-algo-xtz-choppiness-breakout-reclaim-1m-full-ladder-v1`,
  decision `higher_timeframe_subclass_only_origin_blocked`; non-origin
  subclass rows exist, but exact 1m origin survivors are empty and downstream is
  forbidden.
- Bybit WOO/CFX PGO:
  `support/docs/experiments/actionable-regime-confidence/runs/20260523T075214+0800-codex-bybit-woo-cfx-pgo-reclaim-1m-full-ladder-v1`,
  decision `drop_gate1_no_hard_5bps_density_survivor`; `14` provider rows,
  `14` rank rows, `9` ranked trades, and no hard 5bps density survivor.

Verification in this slice:

- `python3 -m unittest support.scripts.tests.test_factor_claim_terminalization_audit`
  passed `18` tests.
- `git diff --check -- support/scripts/factor_claim_terminalization_audit.py support/scripts/tests/test_factor_claim_terminalization_audit.py support/docs/plans/2026-05-23-factor-claim-audit-actionability-handoff-todo.md support/docs/plans/2026-05-22-done-definition-audit-handoff-todo.md support/docs/plans/2026-05-12-hotplug-personal-data-release-handoff-todo.md`
  exited `0`.

Actionability:

- Claim/process hygiene is clean again in this snapshot.
- The practical-factor objective remains open because
  `promotion_allowed_true=0` and `trade_usable_true=0`.
- Do not release, tag, push, promote, describe any factor as trade-usable, or
  call `update_goal complete` from this state.
