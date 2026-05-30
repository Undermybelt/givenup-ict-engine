# Trade-Usable Factor Training Current State

- created_at: `2026-05-31T03:22:39+0800`
- owner: `codex`
- repo: `/Users/thrill3r/projects-ict-engine/ict-engine`
- branch: `main`
- route_alias: `sd/ict-engi-fact-rese-muta`
- objective: train toward `trade_usable=true` profitability factors without lowering gates, duplicating active lanes, or colliding with shared Board B runtime.
- session_scope_default: `ETH/full_retained_session`
- rth_filter_applied_for_success: `false_required`
- status: `blocked_for_runtime_launch_current_window`
- promotion_allowed: `false`
- trade_usable: `false`
- update_goal: `false`
- same_tree_practical_closure: `null`

## Current Verdict

No `trade_usable=true` factor was produced in this window.

The latest compact claim audit at `2026-05-31T03:21:15+0800` returned:

- `status=needs_attention`
- `trade_usable_true=0`
- `promotion_allowed_true=0`
- `same_tree_practical_closure=null`
- `live_factor_processes=0`
- `active_claims=3`
- `valid_active_claims=2`
- `invalid_active_claims=1`
- `fresh_active_claims_without_live_process=2`
- `fresh_wait_only_active_claims_without_live_process=1`

Blocking active claims:

- `20260531T022709+0800-codex-heikin-ashi-kama-trend-pullback-rejoin-local-screen.claim`
- `20260531T031303+0800-codex-volatility-quality-index-trend-rejoin-local-screen.claim`
- `20260531T031350+0800-codex-mann-kendall-theil-sen-trend-gate-aqprep.claim`

The active `volatility_quality_index_trend_rejoin` claim is currently invalid because the compact audit reports missing `progress_report_or_latest_report`. Do not repair or take it over unless the owner is stale-safe and no matching live process exists.

## Files Investigated

- `CLAUDE.md`, `AGENTS.md`, `AGENT.md`
- `~/.hermes/routing/skill-router.md`
- `~/.hermes/routing/project-router.md`
- `~/.hermes/skills/software-development/ict-engi-fact-rese-muta/SKILL.md`
- `~/.hermes/skills/software-development/ict-engi-fact-rese-muta/references/waiting-window-factor-research.md`
- `~/.hermes/skills/software-development/ict-engi-fact-rese-muta/references/2026-05-30-paper-strategy-reserve.md`
- `/tmp/ict-engine-heikin-ashi-kama-trend-pullback-rejoin-local-screen-20260531T022709+0800/workdoc.md`
- `/tmp/ict-engine-elder-thermometer-heat-rejoin-aqprep-20260531T030217+0800/workdoc.md`
- `/tmp/ict-engine-pgo-atr-trend-rejoin-aqprep-20260531T030608+0800/workdoc.md`
- `support/docs/experiments/actionable-regime-confidence/20260531T020836+0800-codex-nq-compound-practical-closure-gap-prep.md`
- `support/docs/experiments/actionable-regime-confidence/20260531T022035+0800-codex-nq-compound-feedback-preflight.md`
- `support/docs/experiments/actionable-regime-confidence/20260531T015807+0800-codex-nq-compound-ibkr-readback-converter-prep.md`
- `/tmp/ict-engine-tomac-eth-trend-ote-reacceleration-local-screen-20260531T031421+0800/checks/terminal_metrics.json`
- `/tmp/ict-engine-tomac-eth-trend-ote-reacceleration-local-screen-20260531T031421+0800/summaries/terminal_summary.json`

## Commands Run

```bash
python3 support/scripts/factor_claim_terminalization_audit.py --compact
ps -axo pid,ppid,etime,command | rg -i 'run_tomac|tomac|factor|auto.?quant|freqtrade|run_tomac_one|fetch_external|ibkr|provider-status|paper|real-trades|auto-quant-ingest-real-trades'
sed -n '1,240p' /tmp/ict-engine-tomac-eth-trend-ote-reacceleration-local-screen-20260531T031421+0800/checks/terminal_metrics.json
sed -n '1,220p' /tmp/ict-engine-tomac-eth-trend-ote-reacceleration-local-screen-20260531T031421+0800/summaries/terminal_summary.json
```

Additional focused duplicate/readback searches were run for Ehlers/Hilbert, Pettitt/Shiryaev-Roberts, VIDYA/CMO, ZLEMA/Laguerre/TEMA/T3, and McGinley. They showed those families already have existing local docs, claims, scripts, or negative/readback history and should not be opened as fresh unchanged lanes.

## Best Current Candidates

### 1. NQ Compound Practical Closure

Candidate:

- factor_id: `nq_compound_trend_rrr_chopfilter_v1`
- branch_path: `TrendExpansion -> HtfTrendRegime -> ChopFilter -> MomentumResonance -> CompoundTrendRrrBreadth -> nq_compound_trend_rrr_chopfilter_v1`

Current blockers from the readbacks:

- prior lifecycle had `exact_branch_survived=false`
- `execution_candidate_actionable=false`
- `path_ranker_score_used_by_execution_tree=false`
- validation counters were not mature enough
- prior IBKR paper execution readback converted to `accepted_feedback_rows=0`
- `feedback_file_preflight.status=no_rows`

Next legal step after audit clears: run a fresh readonly IBKR paper execution readback, convert it with `real_trade_feedback_labels.py`, and only continue lifecycle if accepted feedback JSONL has rows with broker/paper fill evidence.

### 2. ETH Trend OTE Reacceleration Local Candidate

New local-screen evidence:

- run_root: `/tmp/ict-engine-tomac-eth-trend-ote-reacceleration-local-screen-20260531T031421+0800`
- factor_family: `tomac_eth_trend_ote_reacceleration`
- best factor_id: `tomac_nq_15m_eth_trend_ote_reacceleration_long_qualityreclaim_v1`
- branch_path: `RegimeRoot -> TrendExpansion -> OteTrendPullback -> ReaccelerationConfirmation -> MtfSlopeResonanceGuard -> tomac_nq_15m_eth_trend_ote_reacceleration_long_qualityreclaim_v1`
- provider: `tomac_retained_local_cache`
- session_scope: `ETH/full_retained_session`
- rth_filter_applied: `false`
- trade_count: `2877`
- sessions: `1555`
- trades_per_session: `1.850161`
- raw_total_profit_pct: `48.451469`
- instrument_cost_total_profit_pct: `44.428661`
- instrument_cost_profit_factor: `1.136818`
- train/validation/test instrument-cost total profit pct: `27.103447 / 7.577617 / 9.747598`
- years_instrument_cost_positive: `5/5`
- promotion_cost_verified: `true`
- density_target_033_to_3_per_session: `true`
- decision: `local_instrument_cost_candidate_needs_exact_aq_downstream`
- promotion_allowed: `false`
- trade_usable: `false`

This is not a `trade_usable=true` factor because it is local retained-cache screening only. It needs exact-AQ/provider/downstream lifecycle, accepted feedback, same-tree practical closure, and final claim-audit validation.

## Do Not Touch

- Do not reset, clean, revert, or stage broad dirty worktree changes.
- Do not take over fresh Heikin-Ashi/KAMA, volatility-quality-index, Mann-Kendall/Theil-Sen, Elder Thermometer, PGO ATR, fractal-liquidity, or other active/recent lanes unless stale-safe rules are satisfied.
- Do not run provider, IBKR historical, AutoQuant, Freqtrade/TOMAC, paper/sim/live, downstream lifecycle, or feedback ingestion while compact audit reports active claims, invalid active claims, or live factor processes.
- Do not report RTH-only, local-screen-only, source-prep-only, or Python-only evidence as `trade_usable=true`.
- Do not use fixed bps labels as cost authority for promotion or trade usability.

## Next 7 Steps

1. Rerun `python3 support/scripts/factor_claim_terminalization_audit.py --compact` and focused `ps` before any launch.
2. If active claims remain fresh or invalid, do not launch; either wait for terminalization or do source/candidate intake only with false practical flags.
3. If audit clears, prioritize the NQ compound accepted-feedback path: run a fresh readonly IBKR paper execution readback and convert it to accepted feedback JSONL.
4. If accepted feedback rows remain zero, stop NQ compound at the preflight guard.
5. If accepted feedback rows exist, rerun the NQ compound practical lifecycle with the accepted JSONL, verified closure evidence, and canonical same-tree closure helper.
6. If NQ compound still fails, create a fresh exact-AQ launch claim for `tomac_nq_15m_eth_trend_ote_reacceleration_long_qualityreclaim_v1` and run exact-AQ/provider/downstream from the local candidate evidence.
7. After any run, inspect terminal metrics, retained-session proof, cost packet, accepted-feedback source, path-ranker execution-tree use, validation counters, and `same_tree_practical_closure` before changing any practical flags.

## 2026-05-31T03:32-03:36+0800 Current Readback

Fresh compact audits still block runtime launch. The latest observed state keeps
`trade_usable_true=0`, `promotion_allowed_true=0`, and
`same_tree_practical_closure=null`.

Runtime/current-claim blockers observed in this window:

- VQI local screen was live briefly under
  `/tmp/ict-engine-volatility-quality-index-trend-rejoin-local-screen-20260531T031303+0800`, then exited before the later audit.
- Gann HiLo ATR clean-AQ prep wrote terminal no-launch evidence under
  `/tmp/ict-engine-gann-hilo-atr-trend-rejoin-aqprep-20260531T032304+0800`, but
  the compact audit still reported active/invalid claim attention, so it remains
  a no-launch blocker until a later audit clears it.
- Fresh active/prep claims remained for Kairi YM 5m exact-AQ prep,
  trend-turtle-soup reacceleration local screen, current fee-amnesty rescue, and
  MMI trend-cleanliness local screen.

NQ compound accepted-feedback path is ready for the first legal runtime step
once compact audit and focused `ps` both clear. The next command must be a
fresh readonly IBKR paper execution readback, not a lifecycle rerun. The prior
IBKR readback at
`/tmp/ict-engine-nq-compound-accepted-feedback-readback-20260530T121826+0800/checks/ibkr_paper_execution_readback.json`
still had `execution_rows_total=0`, so the converted accepted-feedback JSONL had
zero rows.

Legal command sequence after audit clear:

```bash
STAMP=$(date +%Y%m%dT%H%M%S+0800)
ROOT=/tmp/ict-engine-nq-compound-accepted-feedback-runtime-${STAMP}
mkdir -p "$ROOT/checks"

python3 /tmp/ict-engine-nq-compound-accepted-feedback-readback-20260530T121826+0800/checks/ibkr_paper_execution_readback.py \
  --output "$ROOT/checks/ibkr_paper_execution_readback.json"

python3 support/scripts/research/real_trade_feedback_labels.py \
  --ibkr-execution-readback-json "$ROOT/checks/ibkr_paper_execution_readback.json" \
  --output-jsonl "$ROOT/checks/accepted_feedback.jsonl" \
  --symbol TOMAC_NQ_COMPOUND_TREND_RRR_CHOPFILTER_V1 \
  --strategy-name nq_compound_trend_rrr_chopfilter_v1 \
  --factor-id nq_compound_trend_rrr_chopfilter_v1 \
  --branch-path 'TrendExpansion -> HtfTrendRegime -> ChopFilter -> MomentumResonance -> CompoundTrendRrrBreadth -> nq_compound_trend_rrr_chopfilter_v1' \
  --auto-quant-run-id "ibkr-paper-execution-readback-${STAMP}" \
  --feedback-source auto_quant_real_trades:paper_execution_feedback:nq_compound_trend_rrr_chopfilter_v1 \
  --ibkr-contract-symbol NQ

python3 support/docs/experiments/actionable-regime-confidence/scripts/run_tomac_nq_compound_trend_rrr_chopfilter_practical_lifecycle_v1.py \
  --root "$ROOT/lifecycle" \
  --execute-driver \
  --feedback-file "$ROOT/checks/accepted_feedback.jsonl"
```

Stop at the feedback preflight if `accepted_feedback.jsonl` is empty or lacks
`broker_realized=true`, `broker_fill_evidence=true`, and an accepted
paper/live/broker feedback source. Do not create or report `trade_usable=true`
unless the canonical same-tree practical-closure packet validates from that
same run root.

## 2026-05-31T05:10-05:12+0800 Current Readback

Fresh audit and process readbacks still block any new runtime launch. The
current compact audit returned:

- `status=needs_attention`
- `trade_usable_true=0`
- `promotion_allowed_true=0`
- `same_tree_practical_closure=null`
- `active_claims=2`
- `valid_active_claims=2`
- `invalid_active_claims=0`
- `fresh_active_claims_without_live_process=0`
- `stale_safe_takeover_candidates=0`
- `live_factor_processes=2`

Live runtime owners:

- MMI trend-cleanliness local screen:
  `/tmp/ict-engine-mmi-trend-cleanliness-filter-local-screen-20260531T032939+0800`
  with observed PID `19270`; sibling PIDs `20384` and `22238` were also still
  present in the focused process table.
- Low-volatility trend pullback exact-AQ:
  `/tmp/ict-engine-low-vol-trend-pullback-exact-aq-20260531T050524+0800`
  with observed PID `24341`.

Because `live_factor_processes=2`, this window did not run provider, IBKR
historical, AutoQuant, Freqtrade/TOMAC backend, paper/sim/live, downstream
lifecycle, feedback ingestion, or same-tree practical closure.

MMI local-screen terminal evidence is now readable but does not release the
runtime because live processes still exist. The terminal summary reports:

- decision: `drop_local_screen_no_instrument_cost_candidate`
- candidate_count: `108`
- instrument_cost_candidate_count: `0`
- gate1_survivor_count: `0`
- provider_or_aq_launched: `false`
- best NQ 15m row:
  `tomac_nq_15m_mmi_trend_cleanliness_filter_long_cleanquality_v1`,
  `trade_count=2754`, `trades_per_session=1.771061`,
  `instrument_cost_total_profit_pct=37.710195`,
  `instrument_cost_profit_factor=1.13295`, `years_instrument_cost_positive=5/5`,
  rejected by `reject_chronological_split_instability`.
- best NQ 4h row had split-positive economics but failed density:
  `trades_per_session=0.326045`,
  `instrument_cost_total_profit_pct=33.506363`,
  decision `reject_density_outside_033_to_3_per_session`.
- XAU rows remain unusable for promotion because the cost packet is
  `default_assumption_unverified` / `COMEX_XAU_alias_unverified_v1`.

This keeps MMI as terminal local-screen negative or near-miss evidence only:
`promotion_allowed=false`, `trade_usable=false`, and `update_goal=false`.

Waiting-window duplicate checks were run for likely source/prep alternatives:
transfer entropy, visibility graph/HVG, realized jump/bipower, cointegration
half-life, short-interest/borrow-fee, analyst revision dispersion, and
customer-supplier momentum. Each already has a source reserve, training prep,
wrapper prep, or explicit do-not-duplicate packet in the local docs/claims.
No new source claim was opened, to avoid adding another active blocker. The
waiting-window action is therefore this readback and tracking update only.

Next legal step remains unchanged: rerun compact audit plus focused `ps`. If
both live roots have exited or terminalized, first check whether the low-vol
exact-AQ owner produced a terminal verdict; then decide whether the next clear
window belongs to NQ compound accepted-feedback readback, low-vol exact-AQ
follow-through, or ETH Trend OTE exact-AQ. Do not launch a sibling runtime from
this document while any live owner remains.

## 2026-05-31T05:13+0800 Drift Refresh

The shared runtime changed again during readback. A later compact audit at
`2026-05-31T05:13:47+0800` reported:

- `status=needs_attention`
- `trade_usable_true=0`
- `promotion_allowed_true=0`
- `same_tree_practical_closure=null`
- `active_claims=2`
- `valid_active_claims=2`
- `invalid_active_claims=0`
- `live_factor_processes=1`
- `active_claims_without_live_process=1`
- `fresh_wait_only_active_claims_without_live_process=1`
- `stale_safe_takeover_candidates=0`

Current blockers at that audit:

- live owner: Kairi YM 5m clean-only staging,
  claim `20260531T050951+0800-codex-kairi-ym5m-clean-aq-staging.claim`,
  run root `/tmp/ict-engine-kairi-ym5m-clean-aq-staging-20260531T050951+0800`,
  observed PID `26864`.
- fresh wait-only claim without live process:
  `20260531T050524+0800-codex-low-vol-trend-pullback-exact-aq.claim`;
  audit action queue recommends externalizing or waiting for progress/stale-safe
  timeout, not taking it over now.

Focused `ps` at the same moment showed Kairi PID `26864` plus other agents'
sleeping monitor commands against MMI/low-vol roots. MMI had terminal local
screen evidence, but no practical flag. ETH Trend OTE exact-AQ claim files were
freshened by another agent during the window; this document did not touch them.

Therefore the current lane remains launch-blocked. No new factor claim or
runtime command was started from this tracking document.

## 2026-05-31T05:07-05:13+0800 Andrews Prep Packet

A separate no-launch prep packet was created after duplicate checks found no
exact `Andrews`, `Pitchfork`, `median line`, `median_line`, or `Schiff` lane in
current claims or actionable-regime-confidence docs/scripts.

- repo_tracking_doc:
  `support/docs/experiments/actionable-regime-confidence/20260531T050703+0800-codex-andrews-pitchfork-median-rejoin-aqprep.md`
- workdoc:
  `/tmp/ict-engine-andrews-pitchfork-median-rejoin-aqprep-20260531T050703+0800/workdoc.md`
- claim:
  `/tmp/ict-engine-agent-claims/board-b-factor-refinement/20260531T050703+0800-codex-andrews-pitchfork-median-rejoin-aqprep.claim`
- strategy_material:
  `/tmp/ict-engine-andrews-pitchfork-median-rejoin-aqprep-20260531T050703+0800/aq_workspace/user_data/strategies_external/TomacAndrewsPitchforkMedianRejoinPrepV1.py`
- factor_family: `andrews_pitchfork_median_rejoin`
- branch_path_template:
  `RegimeRoot -> TrendExpansion -> MedianLineChannel -> AndrewsPitchforkRejoin -> MtfSlopeResonance -> tomac_idxfut_andrews_pitchfork_median_rejoin_<timeframe>_v1`
- independent_timeframes: `5m/15m/30m/1h/4h/1d`
- session_scope: `ETH/full_retained_session`
- decision: `terminalized_prep_only_runtime_blocked_by_foreign_live_processes`
- promotion_allowed: `false`
- trade_usable: `false`
- update_goal: `false`

Verification:

- claim JSON parse passed.
- strategy material `py_compile` passed.
- follow-up compact audit at `2026-05-31T05:12:53+0800` reported
  `active_claims=2`, `live_factor_processes=3`,
  `coordination_only_active_claims=24`, `trade_usable_true=0`,
  `promotion_allowed_true=0`; this Andrews prep was not listed as an attention
  claim.

No provider, IBKR historical, AutoQuant/Freqtrade/TOMAC backtest, local screen,
paper/sim/live, downstream lifecycle, feedback ingestion, or policy training
command was launched from this packet.

## 2026-05-31T05:18+0800 Latest Audit

Post-prep compact audit reported:

- `status=needs_attention`
- `active_claims=0`
- `valid_active_claims=0`
- `invalid_active_claims=0`
- `live_factor_processes=1`
- `trade_usable_true=0`
- `promotion_allowed_true=0`
- `same_tree_practical_closure=null`

The remaining live process is the foreign low-vol trend pullback exact-AQ root:

- `/tmp/ict-engine-low-vol-trend-pullback-exact-aq-20260531T050524+0800`
- observed PID: `35094`
- exit marker present:
  `/tmp/ict-engine-low-vol-trend-pullback-exact-aq-20260531T050524+0800/checks/pre_aq_claim_collision_audit.exit`

Do not launch Andrews, ETH OTE, NQ compound, or any sibling AQ until a fresh
compact audit and focused `ps` both show no live factor process.

## 2026-05-31T05:19+0800 Low-Vol Exact-AQ Readback

Fresh compact audit at `2026-05-31T05:18:51+0800` still blocked any new runtime
launch:

- `status=needs_attention`
- `active_claims=0`
- `valid_active_claims=0`
- `invalid_active_claims=0`
- `live_factor_processes=1`
- `trade_usable_true=0`
- `promotion_allowed_true=0`
- `same_tree_practical_closure=null`

Focused `ps` immediately after the audit showed the low-vol exact-AQ root was
still active and had started an independent NQ `15m` exact-AQ iteration:

- PID `35094`: low-vol `NQ 30m` wrapper still live under
  `/tmp/ict-engine-low-vol-trend-pullback-exact-aq-20260531T050524+0800`
- PID `37229`: low-vol `NQ 15m` wrapper live under the same root

The low-vol workdoc and claim currently classify the lane as
`active_exact_aq_iterating`, not terminal. The readable NQ `30m` exact-AQ result
is fail-closed:

- gate file:
  `/tmp/ict-engine-low-vol-trend-pullback-exact-aq-20260531T050524+0800/summaries/autoquant_clean_30m_gate.json`
- command exit: `0`
- decision: `observation_realistic_cost_survivor_needs_non_cost_gate_repair`
- `rank_rows=2`
- `session_scope=ETH/full_retained_session`
- `rth_filter_applied=false`
- `eth_full_retained_session_evidence=true`
- best exact-AQ row: `NQ 30m`, `trade_count=107`,
  `trades_per_day=0.058856`, `raw_total_profit_pct=2.43`,
  `instrument_cost_total_profit_pct=1.850417`,
  `survives_instrument_cost=true`
- Gate-1 failure: `density_target_1_to_3_per_day=false`
- downstream gates remain false:
  `pre_bayes_allowed=false`, `bbn_allowed=false`,
  `catboost_allowed=false`, `execution_tree_allowed=false`
- `promotion_allowed=false`, `trade_usable=false`, `update_goal=false`

No provider, IBKR historical, paper/sim/live, downstream lifecycle, feedback
ingestion, or same-tree practical closure was launched from this readback.
Next legal action is another compact audit plus focused `ps`. If the NQ `15m`
iteration terminalizes, inspect its terminal metrics before choosing between
low-vol follow-through, NQ compound accepted-feedback readback, or ETH Trend OTE
exact-AQ.

## 2026-05-31T05:24-05:28+0800 No-Launch Prep And Low-Vol 15m Readback

Fresh compact audit at `2026-05-31T05:23:43+0800` still blocked runtime launch:

- `status=needs_attention`
- `live_factor_processes=1`
- live root:
  `/tmp/ict-engine-low-vol-trend-pullback-exact-aq-20260531T050524+0800`
- `trade_usable_true=0`
- `promotion_allowed_true=0`
- `same_tree_practical_closure=null`

Focused `ps` showed the low-vol `NQ 15m` wrapper and `run_tomac.py` child still
active, so no new AQ/IBKR/paper/lifecycle command was started from this tracking
doc.

Created a coordination-only candidate prep packet for a distinct
Savitzky-Golay local-polynomial trend-shape family:

- repo doc:
  `support/docs/experiments/actionable-regime-confidence/20260531T052435+0800-codex-savitzky-golay-slope-curvature-reacceleration-aqprep.md`
- workdoc:
  `/tmp/ict-engine-savitzky-golay-slope-curvature-reacceleration-aqprep-20260531T052435+0800/workdoc.md`
- claim:
  `/tmp/ict-engine-agent-claims/board-b-factor-refinement/20260531T052435+0800-codex-savitzky-golay-slope-curvature-reacceleration-aqprep.claim`
- factor_family: `savitzky_golay_slope_curvature_reacceleration`
- branch_path_template:
  `TrendExpansion -> LocalPolynomialTrendShape -> SlopeCurvatureReacceleration -> MtfSlopeAgreement -> tomac_idxfut_clean_savgol_slope_curvature_reacceleration_<timeframe>_v1`
- independent timeframes: `5m/15m/30m/1h/4h/1d`
- session_scope: `ETH/full_retained_session`
- decision: `prepared_source_backed_wrapper_packet_no_launch_runtime_blocked`
- `promotion_allowed=false`, `trade_usable=false`, `update_goal=false`

Duplicate check avoided Parkinson/Garman-Klass/range-estimator, CLV/BOP,
regression-channel, Ehlers/Fisher, KAMA/FRAMA, wavelet/SSA, low-vol, Kairi, and
other active/recent lanes. Claim JSON parse passed. Follow-up compact audit at
`2026-05-31T05:27:16+0800` classified the Savitzky-Golay packet as
coordination-only and did not list it as attention/blocking work.

Low-vol `NQ 15m` terminal readback then became available:

- gate file:
  `/tmp/ict-engine-low-vol-trend-pullback-exact-aq-20260531T050524+0800/summaries/autoquant_clean_15m_gate.json`
- command exit: `0`
- decision: `observation_realistic_cost_survivor_needs_non_cost_gate_repair`
- `rank_rows=2`
- `session_scope=ETH/full_retained_session`
- `rth_filter_applied=false`
- `eth_full_retained_session_evidence=true`
- best exact-AQ row: `tomac_idxfut_clean_low_volatility_trend_pullback_reacceleration_15m_v1`,
  `trade_count=217`, `trades_per_day=0.119231`,
  `raw_total_profit_pct=2.16`, `instrument_cost_total_profit_pct=0.984583`,
  `survives_instrument_cost=true`
- Gate-1 failure: `density_target_1_to_3_per_day=false`
- downstream gates remain false:
  `pre_bayes_allowed=false`, `bbn_allowed=false`,
  `catboost_allowed=false`, `execution_tree_allowed=false`
- `promotion_allowed=false`, `trade_usable=false`, `update_goal=false`

The latest compact audit at `2026-05-31T05:27:16+0800` reported a new active
live owner:

- Kairi YM5m exact-AQ launch claim:
  `/tmp/ict-engine-agent-claims/board-b-factor-refinement/20260531T052501+0800-codex-kairi-ym5m-exact-aq-launch.claim`
- run root:
  `/tmp/ict-engine-kairi-ym5m-exact-aq-launch-20260531T052501+0800`
- observed PID: `48345`
- `active_claims=1`, `valid_active_claims=1`, `live_factor_processes=1`
- `trade_usable_true=0`, `promotion_allowed_true=0`,
  `same_tree_practical_closure=null`

Next legal action remains compact audit plus focused `ps`. Do not launch NQ
compound, Savitzky-Golay, ETH OTE, Andrews, or any sibling runtime while Kairi
or another live owner remains active.

## 2026-05-31T05:22+0800 Runtime Recheck

Fresh compact audit still blocks every new runtime launch:

- `status=needs_attention`
- `active_claims=0`
- `valid_active_claims=0`
- `invalid_active_claims=0`
- `live_factor_processes=1`
- `trade_usable_true=0`
- `promotion_allowed_true=0`
- `same_tree_practical_closure=null`

Focused `ps` shows the live root is still the same low-vol exact-AQ ownership
root, with both the parent `30m` wrapper and the current `15m` iteration
visible:

- PID `35094`: original low-vol `NQ 30m` wrapper under
  `/tmp/ict-engine-low-vol-trend-pullback-exact-aq-20260531T050524+0800`.
- PID `37229`: low-vol `NQ 15m` wrapper under the same root, command
  `--timeframes 15m --families low_volatility_trend_pullback_reacceleration`.

The run root has not yet written `15m` terminal files under `summaries/` or
`checks/`; only the prior `autoquant_clean_30m_*` readback is present. Do not
launch NQ compound, ETH Trend OTE, Andrews, low-vol sibling timeframes, or any
new AQ/provider/paper/downstream command until a fresh audit and focused `ps`
show this live root has exited and its terminal metrics have been inspected.

## 2026-05-31T05:29+0800 Kairi Live Owner And Low-Vol Closure

Fresh compact audit and focused `ps` show the active runtime has moved to the
Kairi YM 5m exact-AQ launch:

- claim:
  `/tmp/ict-engine-agent-claims/board-b-factor-refinement/20260531T052501+0800-codex-kairi-ym5m-exact-aq-launch.claim`
- run root:
  `/tmp/ict-engine-kairi-ym5m-exact-aq-launch-20260531T052501+0800`
- observed PID: `48345`
- current status: `active_guarded_launch_attempt`
- in-wrapper collision guard:
  `/tmp/ict-engine-kairi-ym5m-exact-aq-launch-20260531T052501+0800/checks/pre_aq_claim_collision_guard.json`
  reports `decision=claim_collision_guard_pass`
- current artifacts present: clean `YM_USD-5m.feather`, generated Kairi strategy,
  and AQ workspace files; `run_tomac_5m` terminal gate output is not present yet.

Low-vol exact-AQ is now terminal evidence, not a live owner. Both exact-AQ
children exited `0`, but neither produced a Gate-1 survivor:

- `30m` gate:
  `/tmp/ict-engine-low-vol-trend-pullback-exact-aq-20260531T050524+0800/summaries/autoquant_clean_30m_gate.json`
  with decision `observation_realistic_cost_survivor_needs_non_cost_gate_repair`
  and `density_target_1_to_3_per_day=false`.
- `15m` gate:
  `/tmp/ict-engine-low-vol-trend-pullback-exact-aq-20260531T050524+0800/summaries/autoquant_clean_15m_gate.json`
  with decision `observation_realistic_cost_survivor_needs_non_cost_gate_repair`,
  `trade_count=217`, `trades_per_day=0.119231`,
  `instrument_cost_total_profit_pct=0.984583`,
  `survives_instrument_cost=true`, and
  `density_target_1_to_3_per_day=false`.

Both low-vol packets prove `session_scope=ETH/full_retained_session`,
`rth_filter_applied=false`, and retained rows outside RTH, but downstream
admission remains closed: `pre_bayes_allowed=false`, `bbn_allowed=false`,
`catboost_allowed=false`, `execution_tree_allowed=false`,
`promotion_allowed=false`, `trade_usable=false`, and `update_goal=false`.

No NQ compound accepted-feedback readback, ETH OTE exact-AQ, Savitzky-Golay,
Andrews, provider, IBKR historical, paper/sim/live, downstream lifecycle,
feedback ingestion, or same-tree practical-closure command was launched from
this readback. Next legal action is to keep reading the Kairi root until it
terminalizes, then classify its `run_tomac_5m` gate before selecting any next
runtime lane.

## 2026-05-31T05:31-05:33+0800 Kairi Terminal And NQ Compound Feedback Preflight

Kairi YM 5m exact-AQ terminalized:

- root:
  `/tmp/ict-engine-kairi-ym5m-exact-aq-launch-20260531T052501+0800`
- gate:
  `/tmp/ict-engine-kairi-ym5m-exact-aq-launch-20260531T052501+0800/summaries/autoquant_clean_5m_gate.json`
- command exit: `0`
- rows: `347` trades, `0.19045` trades/day
- raw_total_profit_pct: `1.82`
- instrument_cost_total_profit_pct: `-1.65`
- survives_instrument_cost: `false`
- density_target_1_to_3_per_day: `false`
- decision: `terminalized_exact_aq_no_survivor_cost_and_density_failed`
- `promotion_allowed=false`, `trade_usable=false`, `update_goal=false`

Follow-up compact audit cleared all blockers:

- `status=pass`
- `active_claims=0`
- `live_factor_processes=0`
- `trade_usable_true=0`
- `promotion_allowed_true=0`
- `same_tree_practical_closure=null`

NQ compound accepted-feedback runtime then ran under:

- root:
  `/tmp/ict-engine-nq-compound-accepted-feedback-runtime-20260531T053201+0800`
- repo doc:
  `support/docs/experiments/actionable-regime-confidence/20260531T053201+0800-codex-nq-compound-accepted-feedback-runtime.md`
- readonly IBKR readback:
  `/tmp/ict-engine-nq-compound-accepted-feedback-runtime-20260531T053201+0800/checks/ibkr_paper_execution_readback.json`
- selected_client_id: `9126`
- execution_rows_total: `0`
- nq_execution_rows: `0`
- accepted_feedback_jsonl_ready: `false`
- accepted feedback file:
  `/tmp/ict-engine-nq-compound-accepted-feedback-runtime-20260531T053201+0800/checks/accepted_feedback.jsonl`
- accepted_feedback_rows: `0`

Decision: `terminalized_accepted_execution_feedback_absent_no_lifecycle`.
The practical lifecycle was not launched because accepted broker/paper feedback
was absent. This keeps NQ compound at `promotion_allowed=false`,
`trade_usable=false`, and `update_goal=false`.

## 2026-05-31T05:36-05:38+0800 Current Blockers And Adjacent Readback

Fresh compact audits again report `status=needs_attention` because other fresh
claims appeared after the NQ compound preflight:

- PFE local-screen claim:
  `/tmp/ict-engine-agent-claims/board-b-factor-refinement/20260531T053342+0800-codex-polarized-fractal-efficiency-trend-acceptance-local-screen.claim`
- Andrews 15m AQ claim:
  `/tmp/ict-engine-agent-claims/board-b-factor-refinement/20260531T053433+0800-codex-andrews-pitchfork-median-rejoin-15m-aqlaunch.claim`
- latest observed audit shape:
  `active_claims=2`, `live_factor_processes=0`,
  `trade_usable_true=0`, `promotion_allowed_true=0`,
  `same_tree_practical_closure=null`.

The Andrews AQ root already has readable output:

- run root:
  `/tmp/ict-engine-andrews-pitchfork-median-rejoin-aq-20260531T053433+0800`
- trades export:
  `/tmp/ict-engine-andrews-pitchfork-median-rejoin-aq-20260531T053433+0800/checks/aq_trades_andrews_pitchfork_15m.json`
- result: `234` total trades, `0.13` daily avg trades,
  `total_profit_pct=-0.91`, `profit_factor=0.9815`.
- per-pair readback: `NQ/USD +3.13%` across `141` trades, `XAU/USD +0.39%`
  across `57` trades, `YM/USD -4.43%` across `36` trades.

This is negative or insufficient AQ screen evidence, not practical evidence.
Do not downstream Andrews unchanged. Also do not launch ETH OTE, NQ compound,
Savitzky-Golay, VolumeClock, or any new AQ/provider/IBKR/paper/lifecycle command
while these fresh claims remain active.

## 2026-05-31T05:24+0800 Runtime Drift Recheck

Another compact audit still reports `needs_attention` with:

- `active_claims=0`
- `live_factor_processes=1`
- `trade_usable_true=0`
- `promotion_allowed_true=0`
- `same_tree_practical_closure=null`

The remaining live process has shifted to the low-vol `NQ 15m` wrapper:

- PID `37229`
- run root:
  `/tmp/ict-engine-low-vol-trend-pullback-exact-aq-20260531T050524+0800`
- command includes
  `--symbols NQ --timeframes 15m --families low_volatility_trend_pullback_reacceleration`

Current root file readback shows `NQ_USD-15m.feather` and
`command-output/run_tomac_15m.cmd`, but no `autoquant_clean_15m_gate.json`,
terminal metrics, or same-tree closure packet yet. This is still an owned live
runtime root, not a free window.

## 2026-05-31T05:28+0800 Andrews Prep Completion

The Andrews/Pitchfork prep packet was missing launch-ready retained data links,
so I completed only isolated AQ workspace staging without launching backend
runtime:

- workdoc:
  `/tmp/ict-engine-andrews-pitchfork-median-rejoin-aqprep-20260531T050703+0800/workdoc.md`
- repo doc:
  `support/docs/experiments/actionable-regime-confidence/20260531T050703+0800-codex-andrews-pitchfork-median-rejoin-aqprep.md`
- data link dir:
  `/tmp/ict-engine-andrews-pitchfork-median-rejoin-aqprep-20260531T050703+0800/aq_workspace/user_data/data/futures`
- source summary:
  `/tmp/ict-engine-tomac-aq-data-stage-20260530T212321+0800/summary.json`
- retained feather links: `21`
- broken feather links: `0`
- symbols: `NQ/YM/XAU`
- retained timeframes: `1m/5m/15m/30m/1h/4h/1d`
- session_scope: `ETH/full_retained_session`
- `rth_filter_applied=false`

No provider fetch, IBKR historical, AutoQuant/Freqtrade/TOMAC runtime, local
screen, paper/sim/live, downstream lifecycle, feedback ingestion, or policy
training was launched. Practical flags remain `promotion_allowed=false`,
`trade_usable=false`, and `update_goal=false`.

## 2026-05-31T05:34+0800 Andrews 15m AQ Launch Claim

After Kairi terminalized negative, the same-turn compact audit at
`2026-05-31T05:31:39+0800` reported `status=pass`, `active_claims=0`,
`live_factor_processes=0`, `promotion_allowed_true=0`,
`trade_usable_true=0`, and `same_tree_practical_closure=null`.

Created the Andrews 15m isolated AQ launch packet:

- run_root:
  `/tmp/ict-engine-andrews-pitchfork-median-rejoin-aq-20260531T053433+0800`
- repo doc:
  `support/docs/experiments/actionable-regime-confidence/20260531T053433+0800-codex-andrews-pitchfork-median-rejoin-15m-aqlaunch.md`
- workdoc:
  `/tmp/ict-engine-andrews-pitchfork-median-rejoin-aq-20260531T053433+0800/workdoc.md`
- claim:
  `/tmp/ict-engine-agent-claims/board-b-factor-refinement/20260531T053433+0800-codex-andrews-pitchfork-median-rejoin-15m-aqlaunch.claim`
- strategy_class: `TomacAndrewsPitchforkMedianRejoin15mPrepV1`
- symbols: `NQ/YM/XAU`
- timeframe: `15m`
- retained feather links: `21`
- broken feather links: `0`

Caveat: this strategy is still `PrepV1` and uses a closed-bar median-line
proxy, so even a successful AQ run is screen evidence only until pivot
extraction and full same-tree lifecycle gates are validated.

## 2026-05-31T05:39+0800 Andrews 15m AQ Terminal

The Andrews 15m AQ screen emitted terminal metrics:

- terminal_metrics:
  `/tmp/ict-engine-andrews-pitchfork-median-rejoin-aq-20260531T053433+0800/checks/terminal_metrics.json`
- terminal_summary:
  `/tmp/ict-engine-andrews-pitchfork-median-rejoin-aq-20260531T053433+0800/summaries/terminal_summary.md`
- AQ export:
  `/tmp/ict-engine-andrews-pitchfork-median-rejoin-aq-20260531T053433+0800/checks/aq_trades_andrews_pitchfork_15m.json`
- decision: `terminalized_aq_screen_negative_no_gate_survivor`
- trade_count: `234`
- trades_per_day: `0.128713`
- total_profit_pct: `-0.91`
- profit_factor: `0.981542`
- sharpe: `-0.016311`
- per-pair: `NQ/USD +3.13%`, `XAU/USD +0.39%`, `YM/USD -4.43%`
- density_target_1_to_3_per_day: `false`
- aggregate_profit_positive: `false`
- `promotion_allowed=false`
- `trade_usable=false`
- `update_goal=false`

The wrapper exit capture failed because zsh treats variable name `status` as
read-only, so no `checks/run_tomac_one_15m.exit` exists. The AQ export and
metrics are present, but the lane stays fail-closed and no downstream lifecycle
step is allowed.

Follow-up compact audit at `2026-05-31T05:42:16+0800` no longer lists Andrews
as active. It still reports `status=needs_attention` from other owners:

- live root:
  `/tmp/ict-engine-polarized-fractal-efficiency-trend-acceptance-local-screen-20260531T053342+0800`
- fresh active claim:
  `/tmp/ict-engine-agent-claims/board-b-factor-refinement/20260531T053901+0800-codex-fisher-transform-trend-rejoin-local-screen.claim`
- `active_claims=2`
- `live_factor_processes=1`
- `promotion_allowed_true=0`
- `trade_usable_true=0`

Do not start another sibling AQ/provider/local-screen runtime until these clear.

## 2026-05-31T05:45+0800 Final Collision Recheck

Latest compact audit before handoff reports:

- `status=needs_attention`
- `active_claims=1`
- `live_factor_processes=0`
- `promotion_allowed_true=0`
- `trade_usable_true=0`
- blocker claim:
  `/tmp/ict-engine-agent-claims/board-b-factor-refinement/20260531T053901+0800-codex-fisher-transform-trend-rejoin-local-screen.claim`
- blocker decision: `local_screen_in_progress_no_backend_launch`

Andrews is no longer an attention claim. The current blocker is a fresh Fisher
local-screen claim, so no new sibling runtime should start until a fresh audit
clears it or it terminalizes.

## 2026-05-31T05:31-05:35+0800 Kairi/NQ Feedback Closure And New Blockers

Fresh local readback after degraded handoff re-verification changed the state
again. Kairi YM 5m exact-AQ is now terminal, not a live owner:

- claim:
  `/tmp/ict-engine-agent-claims/board-b-factor-refinement/20260531T052501+0800-codex-kairi-ym5m-exact-aq-launch.claim`
- workdoc:
  `/tmp/ict-engine-kairi-ym5m-exact-aq-launch-20260531T052501+0800/workdoc.md`
- terminal metrics:
  `/tmp/ict-engine-kairi-ym5m-exact-aq-launch-20260531T052501+0800/checks/terminal_metrics.json`
- decision: `terminalized_exact_aq_no_survivor_cost_and_density_failed`
- command_exit: `0`
- trade_count: `347`
- trades_per_day: `0.19045`
- raw_total_profit_pct: `1.82`
- instrument_cost_total_profit_pct: `-1.65`
- profit_factor: `1.0439`
- promotion_cost_verified: `true`
- survives_instrument_cost: `false`
- density_target_1_to_3_per_day: `false`
- session_scope: `ETH/full_retained_session`
- rth_filter_applied: `false`
- retained session coverage: `verified_retained_rows_outside_rth_all_symbols`
- downstream_allowed: `false`
- promotion_allowed: `false`
- trade_usable: `false`
- update_goal: `false`

A follow-up compact audit at `2026-05-31T05:32:07+0800` briefly cleared:

- `status=pass`
- `active_claims=0`
- `live_factor_processes=0`
- `trade_usable_true=0`
- `promotion_allowed_true=0`
- `same_tree_practical_closure=null`

The NQ compound accepted-feedback runtime was then created by another active
owner and terminalized fail-closed before I launched anything duplicate:

- repo doc:
  `support/docs/experiments/actionable-regime-confidence/20260531T053201+0800-codex-nq-compound-accepted-feedback-runtime.md`
- workdoc:
  `/tmp/ict-engine-nq-compound-accepted-feedback-runtime-20260531T053201+0800/workdoc.md`
- claim:
  `/tmp/ict-engine-agent-claims/board-b-factor-refinement/20260531T053201+0800-codex-nq-compound-accepted-feedback-runtime.claim`
- IBKR readback:
  `/tmp/ict-engine-nq-compound-accepted-feedback-runtime-20260531T053201+0800/checks/ibkr_paper_execution_readback.json`
- accepted feedback JSONL:
  `/tmp/ict-engine-nq-compound-accepted-feedback-runtime-20260531T053201+0800/checks/accepted_feedback.jsonl`
- ibkr_readback_exit: `0`
- selected_client_id: `9126`
- readonly: `true`
- execution_rows_total: `0`
- nq_execution_rows: `0`
- exact_contract_execution_rows: `0`
- broker_realized_feedback_rows: `0`
- broker_fill_evidence_rows: `0`
- accepted_feedback_rows: `0`
- decision: `terminalized_accepted_execution_feedback_absent_no_lifecycle`

No NQ compound lifecycle was launched because the accepted feedback file was
empty. This keeps `promotion_allowed=false`, `trade_usable=false`, and
`update_goal=false`.

The next compact audit at `2026-05-31T05:34:56+0800` is blocked again by fresh
non-coordination claims, not by Kairi or NQ:

- `status=needs_attention`
- `active_claims=2`
- `valid_active_claims=2`
- `live_factor_processes=0`
- `trade_usable_true=0`
- `promotion_allowed_true=0`
- `same_tree_practical_closure=null`
- active claim:
  `20260531T053321+0800-codex-volume-clock-exact-aq.claim`
- active claim:
  `20260531T053342+0800-codex-polarized-fractal-efficiency-trend-acceptance-local-screen.claim`

No duplicate NQ compound root, provider fetch, IBKR historical, AutoQuant,
Freqtrade/TOMAC, paper/sim/live, downstream lifecycle, feedback ingestion, or
same-tree practical-closure command was launched from this readback. The next
legal step is another compact audit plus focused process readback; if these
fresh claims remain active, continue only no-launch source/prep work with
practical flags false.

## 2026-05-31T05:36+0800 Final Recheck Before Stop

`git diff --check` passed for this tracking document.

A final compact audit at `2026-05-31T05:36:14+0800` still reports no practical
factor and no validated same-tree closure:

- `status=needs_attention`
- `active_claims=2`
- `valid_active_claims=2`
- `live_factor_processes=0`
- `trade_usable_true=0`
- `promotion_allowed_true=0`
- `same_tree_practical_closure=null`

The fresh non-coordination blockers rotated again:

- `20260531T053342+0800-codex-polarized-fractal-efficiency-trend-acceptance-local-screen.claim`
- `20260531T053433+0800-codex-andrews-pitchfork-median-rejoin-15m-aqlaunch.claim`

Because those claims are fresh and not coordination-only, this slice stops
without creating a duplicate runtime claim. Current verified count remains
`trade_usable_true=0`.

## 2026-05-31T05:40-05:41+0800 Resume Recheck

After degraded handoff state, I re-ran the required compact audit and focused
process table before doing any lane work.

Compact claim audit:

- command:
  `python3 support/scripts/factor_claim_terminalization_audit.py --compact`
- generated_at: `2026-05-30T21:40:41.758034+00:00`
- `status=needs_attention`
- `active_claims=2`
- `valid_active_claims=2`
- `invalid_active_claims=0`
- `live_factor_processes=0`
- `fresh_active_claims_without_live_process=2`
- `stale_safe_takeover_candidates=0`
- `trade_usable_true=0`
- `promotion_allowed_true=0`
- `same_tree_practical_closure=null`

Focused process readback:

- command:
  `ps -axo pid,ppid,etime,stat,command | rg -i "run_tomac|auto.?quant|fetch_external|ibkr|paper|freqtrade|volume-clock|polarized-fractal|andrews|bop|turtle-soup|nq-compound|accepted-feedback"`
- observed only the readback command and macOS Wallpaper processes; no active
  TOMAC, AutoQuant, Freqtrade, IBKR, paper, feedback, or provider child process
  was visible from this focused filter.

Fresh non-coordination blockers:

- `20260531T053342+0800-codex-polarized-fractal-efficiency-trend-acceptance-local-screen.claim`
  - status: `active_local_screen_no_backend_launch_runtime_busy`
  - age at audit: `6` minutes
  - workdoc:
    `/tmp/ict-engine-polarized-fractal-efficiency-trend-acceptance-local-screen-20260531T053342+0800/workdoc.md`
  - scope: retained TOMAC local screen for
    `polarized_fractal_efficiency_trend_acceptance`, independent
    `NQ/YM/XAU` `5m/15m/30m/1h/4h/1d`
  - `session_scope=ETH/full_retained_session`
  - `rth_filter_applied=false`
  - `promotion_allowed=false`
  - `trade_usable=false`
  - `update_goal=false`
- `20260531T053901+0800-codex-fisher-transform-trend-rejoin-local-screen.claim`
  - status: `active_local_screen_no_backend_launch_runtime_busy`
  - decision: `local_screen_in_progress_no_backend_launch`
  - age at audit: `1` minute
  - workdoc:
    `/tmp/ict-engine-fisher-transform-trend-rejoin-local-screen-20260531T053901+0800/workdoc.md`
  - scope: retained TOMAC local screen for `fisher_transform_trend_rejoin`,
    independent `NQ/YM/XAU` `5m/15m/30m/1h/4h/1d`
  - `session_scope=ETH/full_retained_session`
  - `rth_filter_applied=false`
  - `promotion_allowed=false`
  - `trade_usable=false`
  - `update_goal=false`

Decision: no provider fetch, IBKR historical, AutoQuant/Freqtrade/TOMAC backend,
paper/sim/live, downstream lifecycle, feedback ingestion, same-tree closure, or
takeover is legal while these claims are fresh active non-coordination lanes.
Only no-launch source/prep work with false practical flags is allowed until the
next same-turn compact audit clears.

## 2026-05-31T05:43+0800 Recheck And PFE Terminal Readback

A later compact audit at `2026-05-31T05:43:09+0800` shows one fresh active
claim remains:

- `status=needs_attention`
- `active_claims=1`
- `valid_active_claims=1`
- `invalid_active_claims=0`
- `live_factor_processes=0`
- `fresh_active_claims_without_live_process=1`
- `stale_safe_takeover_candidates=0`
- `trade_usable_true=0`
- `promotion_allowed_true=0`
- `same_tree_practical_closure=null`

The remaining blocker is:

- `20260531T053901+0800-codex-fisher-transform-trend-rejoin-local-screen.claim`
  - status: `active_local_screen_no_backend_launch_runtime_busy`
  - decision: `local_screen_in_progress_no_backend_launch`
  - age at audit: `4` minutes
  - workdoc:
    `/tmp/ict-engine-fisher-transform-trend-rejoin-local-screen-20260531T053901+0800/workdoc.md`

The earlier PFE local-screen claim dropped out of the attention queue because
terminal artifacts are now present. PFE remains local-screen evidence only:

- run_root:
  `/tmp/ict-engine-polarized-fractal-efficiency-trend-acceptance-local-screen-20260531T053342+0800`
- terminal_summary:
  `/tmp/ict-engine-polarized-fractal-efficiency-trend-acceptance-local-screen-20260531T053342+0800/summaries/terminal_summary.json`
- decision: `local_instrument_cost_candidate_needs_exact_aq_downstream`
- candidate_count: `108`
- instrument_cost_candidate_count: `7`
- gate1_survivor_count: `0`
- provider_or_aq_launched: `false`
- promotion_allowed: `false`
- trade_usable: `false`
- update_goal: `false`

Best PFE local candidates:

| rank | symbol | timeframe | factor_id | trades | trades/session | instrument-cost net % | instrument PF | year stability |
|---:|---|---|---|---:|---:|---:|---:|---|
| 1 | NQ | 5m | `tomac_nq_5m_polarized_fractal_efficiency_trend_acceptance_short_fastacceptance_v1` | 3486 | 2.241801 | 32.036508 | 1.124948 | 5/5 positive |
| 2 | NQ | 30m | `tomac_nq_30m_polarized_fractal_efficiency_trend_acceptance_short_fastacceptance_v1` | 898 | 0.577492 | 28.424259 | 1.207694 | terminal packet positive |
| 3 | NQ | 15m | `tomac_nq_15m_polarized_fractal_efficiency_trend_acceptance_long_fastacceptance_v1` | 2014 | 1.295177 | 27.914196 | 1.169291 | 5/5 positive |
| 4 | NQ | 30m | `tomac_nq_30m_polarized_fractal_efficiency_trend_acceptance_long_fastacceptance_v1` | 1264 | 0.812862 | 25.798834 | 1.201752 | terminal packet positive |
| 5 | NQ | 5m | `tomac_nq_5m_polarized_fractal_efficiency_trend_acceptance_long_qualityacceptance_v1` | 976 | 0.627653 | 14.107217 | 1.248181 | 5/5 positive |

Next legal action remains gated by the active Fisher claim. If the next compact
audit clears, PFE is now a launch-queue candidate for exact-AQ/downstream after
NQ compound accepted-feedback preflight and the already-prepared exact-AQ
packets are considered. Do not launch PFE, Fisher, NQ compound, ETH OTE, Volume
Zone, or any sibling runtime while Fisher remains fresh active.
