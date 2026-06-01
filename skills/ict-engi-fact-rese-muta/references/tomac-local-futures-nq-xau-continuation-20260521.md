# TOMAC local futures NQ/XAU continuation (2026-05-21)

> 2026-05-24 schema note: `pda_hybrid_alignment` is historical telemetry only unless the current ict-engine source or readback contract still declares it active. Do not use old `pda_hybrid_alignment=true` or `false` lines in this reference as a current hard gate; classify with the live actionable/status/readiness/transition/ranker/mature-row fields.

Use under `ict-engi-fact-rese-muta` when continuing local TOMAC futures factor
training from `<private-tomac-data-cache>/* future 2021-2025` data.

## NQ two-leg exact survivor is Gate-1 only

- Exact AQ root:
  `/tmp/ict-engine-tomac-nq-bidir-opening-drive-twoleg-exact-aq-20260521T2015+0800`
- Branch:
  `TrendExpansion -> OpeningDrive -> BidirectionalIntradayTrendContinuation -> tomac_nq_bidir_opening_drive_twoleg_t15_x1080_exact_v1`
- Gate 1:
  `1720` trades, `1.3354` trades/session, raw `+665.58%`,
  `5bps/side=+493.58%`, `survives_5bps_density=true`.
- Clean downstream root:
  `/tmp/ict-engine-tomac-nq-bidir-opening-drive-twoleg-clean-downstream-20260521T2112+0800`
- Downstream verdict:
  `exact_downstream_fail_closed`.

Do not promote this NQ branch from Gate 1 alone. The clean downstream still had:

- seed analyze timeout: `03_analyze_seed=124`
- post-ranker analyze killed/interrupted: `12_analyze_after_ranker=-15`
- original ranker registration mismatch:
  `cli='catboost' source='weighted_feature_sum_v1'`
- weighted fallback registration succeeded as telemetry:
  `10b_register_trainer_weighted=0`
- Pre-Bayes posterior remained empty
- `execution_candidate_actionable=false`
- `execution_readiness=null`
- `transition_hazard=null`
- `pda_hybrid_alignment=null`
- ranker validation insufficient:
  `raw_scored_mature=1/30`, `production_validation=0/30`,
  `observation_validation=0/30`

Next NQ work should target materializing real downstream feedback/mature rows or
analyze-scale/runtime repair. Do not stack more entry overlays on the same root
as a substitute for the missing execution evidence.

## XAU wide-range breakout/retest is a Gate-1 negative

- Root:
  `/private/tmp/ict-engine-tomac-xau-local-gate1-20260521T205325+0800`
- Compact root:
  `support/docs/experiments/actionable-regime-confidence/runs/20260521T205325+0800-codex-tomac-xau-local-regime-rooted-mtf-gate1-v1`
- Source:
  `<private-tomac-data-cache>/xau future 2021-2025/glbx-mdp3-20210106-20260105.ohlcv-1m.csv`
- Selection:
  highest-volume positive outright `GC` row per timestamp; spread rows rejected.
- Staged rows:
  `1,769,524`
- Ladder:
  `1m` plus derived `5m/15m/30m/1h/4h/1d`.
- Branch family:
  `WideRange -> WeeklyRangeExpansion -> WideRangeBreakoutRetest`.

Exact AQ tranche results:

- dense: `1317` trades, `1.0273` trades/day, raw `-2.36%`,
  `1bps=-28.70%`, `2bps=-55.04%`, `5bps=-134.06%`
- balanced: `880` trades, `0.6864` trades/day, raw `-1.67%`,
  `5bps=-89.67%`
- quality: `466` trades, `0.3635` trades/day, raw `-1.06%`,
  `5bps=-47.66%`

Decision: `observation_gate1_no_practical_5bps_density_survivor`.

Do not downstream this XAU wide-range family. If revisiting XAU, pivot to a
materially different high-excursion mechanism instead of widening the same
breakout/retest parameters.

## TOD frontier exact replay and parity repair

- Exact AQ root:
  `/tmp/ict-engine-tomac-tod-balanced-portfolio-aq-frontier-exact-r2-20260522T094841+0800`
- Source vector root:
  `/tmp/ict-engine-tomac-tod-portfolio-density-repair-frontier-20260522`
- Branch:
  `SessionRhythm -> TimeOfDaySeasonality -> BalancedAdaptiveSlotPortfolio`
- Exact AQ result:
  `2054` AQ trades vs `2074` vector trades, `1.320051` trades/session,
  configured `5bps/side` total profit `+22.63%`, PF `1.1281`.
- Gate verdict:
  `signal_count_parity=false`, `gate1_survivor=false`,
  `downstream_allowed=false`.

Do not downstream or promote the wider TOD frontier from positive configured
cost/density alone. The next useful repair is a small exact parity diff or
suppression pass for the `20` missing trades. Also remember that
`tomac_tod_portfolio_aq.py --suppress-entry-diff` expects a JSON file path, not
a boolean flag.

The parity repair was completed in:

- diff artifact:
  `/tmp/ict-engine-tomac-tod-balanced-portfolio-aq-frontier-exact-r2-20260522T094841+0800/checks/parity_missing_vector_entries.json`
- suppression artifact:
  `/tmp/ict-engine-tomac-tod-balanced-portfolio-aq-frontier-exact-r2-20260522T094841+0800/checks/suppress_xau_nonexecutable_overlap_entries.json`
- repaired exact AQ root:
  `/tmp/ict-engine-tomac-tod-balanced-portfolio-aq-frontier-parity-repair-20260522T1016+0800`

Root cause: the `20` missing vector entries were all `XAU`, there were `0`
extra AQ trades, and every missing entry overlapped a still-open same-symbol AQ
trade after Freqtrade exit-timeout / delayed-close behavior. Suppressing only
those non-executable overlapping entries produced exact parity:

- `2054` AQ trades vs `2054` executable vector trades
- `1.320051` trades/session
- configured `5bps/side` total profit `+22.63%`
- PF `1.1281`
- `signal_count_parity=true`
- `survives_5bps_per_side=true`
- `density_target_1_to_3_per_session=true`
- `gate1_survivor=true`

This makes the wider TOD frontier a Gate-1 survivor only. It is still not a
practical/live factor because same-branch downstream evidence remains
fail-closed (`execution_readiness=0.4380310448028449`,
`transition_hazard=0.6390215249399245`, `pda_hybrid_alignment=true`,
`promotion_allowed=false`, `trade_usable=false`). Do not promote it until a
same-root downstream repair clears exact execution admission, validation
maturity, `transition_hazard < 0.60`, and `execution_readiness >= 0.65`.

## TOD frontier parity repair makes Gate 1 pass, not practical admission

- Diff artifact:
  `/tmp/ict-engine-tomac-tod-balanced-portfolio-aq-frontier-exact-r2-20260522T094841+0800/checks/parity_missing_vector_entries.json`
- Suppression artifact:
  `/tmp/ict-engine-tomac-tod-balanced-portfolio-aq-frontier-exact-r2-20260522T094841+0800/checks/suppress_xau_nonexecutable_overlap_entries.json`
- Repaired exact AQ root:
  `/tmp/ict-engine-tomac-tod-balanced-portfolio-aq-frontier-parity-repair-20260522T1016+0800`
- Repair result:
  `2054` AQ trades vs `2054` executable vector trades,
  `1.320051` trades/session, configured `5bps/side` total profit `+22.63%`,
  PF `1.1281`, `signal_count_parity=true`, `gate1_survivor=true`.

Root cause: the original `20` missing vector entries were all `XAU` and each
overlapped a prior same-symbol AQ trade that Freqtrade kept open beyond the
vector expected exit after exit-fill timeout behavior. Suppressing those
non-executable entries repairs exact parity without lowering cost/density gates.

Do not promote this as practical. It is a Gate 1 survivor only. Existing
same-branch full-ladder downstream remains fail-closed:
`execution_readiness=0.4380310448028449`,
`transition_hazard=0.6390215249399245`, `pda_hybrid_alignment=true`,
`promotion_allowed=false`, and `trade_usable=false`. Next useful work is a
concrete same-root execution-tree readiness / transition-hazard repair, not
another broad TOD scan or relaxed gate.

## TOD weekly IBKR NQ provider history resolves readiness but fails signal parity

- Weekly explicit-contract IBKR root:
  `/tmp/ict-engine-tomac-tod-rolling-ibkr-history-build-20260522T1731+0800`
- Terminal readback:
  `/tmp/ict-engine-agent-claims/board-b-factor-refinement/20260522T1805+0800-codex-tomac-tod-weekly-nq-rolling-provider-parity-terminal-readback.md`
- Branch:
  `SessionRhythm -> TimeOfDaySeasonality -> BalancedAdaptiveSlotPortfolio ->
  tomac_tod_balanced_adaptive_slot_portfolio_exact_v1`
- Fetch mode:
  `weekly_RTH_expired_roll_contracts`
- Provider result:
  `76/76` weekly NQ fetches succeeded across
  `NQU4/NQZ4/NQH5/NQM5/NQU5/NQZ5/NQH6`, producing `159075` rows, `136611` RTH
  rows, and `356` RTH sessions from `2024-07-31T13:30:00+00:00` through
  `2025-12-31T21:59:00+00:00`.
- Readiness:
  all `20/20` NQ TOD component streams became history-ready.
- Parity failure:
  provider recomputation produced `492` sidecar rows / `246` entries versus the
  existing NQ sidecar's `16` rows / `8` entries, with only `4` matching signal
  keys, `12` missing existing keys, and `488` extra recomputed keys.
- Decision:
  `nq_weekly_provider_recomputed_signal_parity_mismatch_other_symbols_not_attempted`;
  `promotion_allowed=false`; `trade_usable=false`; `extension_complete=false`.

Do not treat extended provider history as enough for the TOD practical-extension
gate. Weekly expired-contract IBKR history is a viable data-construction method,
but the current NQ provider-recomputed signal signature does not match the
existing sidecar. Do not spend provider budget on YM/XAU, exact AQ replay, or
downstream gates for this same packet until a specific parity-repair hypothesis
explains the extra and missing signal keys.

## Swing-volatility Gate 1 remains observation-only

- Claim:
  `/tmp/ict-engine-agent-claims/board-b-factor-refinement/20260523T000545+0800-codex-tomac-swing-volatility-gate1.claim`
- Inputs:
  corrected local TOMAC `NQ`, `YM`, and `XAU` continuous `1m` rows with
  dominant contract per NY session, timestamp de-duplication, back-adjusted roll
  boundaries, and no synthetic fill.
- Families:
  `VolatilityCompressionExpansion -> DailyAtrSqueezeBreakout ->
  SwingBreakoutContinuation` and `TrendExpansion ->
  DailyDonchianTrendContinuation -> SwingBreakoutContinuation`.
- Per-symbol full-window roots:
  `/tmp/ict-engine-tomac-swing-volatility-gate1-nq-full-20260523T000545+0800`,
  `/tmp/ict-engine-tomac-swing-volatility-gate1-ym-full-20260523T000545+0800`,
  and
  `/tmp/ict-engine-tomac-swing-volatility-gate1-xau-full-20260523T000545+0800`.

Per-symbol verdict:

- NQ: `1476` candidates, `0` strict Gate 1 survivors. Best row was positive
  but too sparse: `219` trades, `0.140745501285347` trades/session,
  `5bps_net=+0.1363282320501346`, PF `1.1457619293820247`.
- YM: `1260` candidates, `0` strict Gate 1 survivors. Best row stayed below
  density and negative at `5bps`: `206` trades, `0.1323907455012853`
  trades/session, `5bps_net=-0.1143528098328719`, PF
  `0.8293679131696283`.
- XAU: `1152` candidates, `0` strict Gate 1 survivors. Best row was positive
  but too sparse and below PF floor: `151` trades,
  `0.0972938144329896` trades/session, `5bps_net=+0.0417494874739977`,
  PF `1.095075677093743`.

Portfolio-density repair:

- Mixed-root repair root:
  `/tmp/ict-engine-tomac-swing-portfolio-density-repair-20260523T000545+0800`
  selected `11` components and produced `517` trades, `0.33226221079691515`
  trades/session, `5bps_net=+0.2010436543875409`, PF `1.1011959649109626`,
  but decision was `reject_mixed_root_portfolio` because it combined
  `TrendExpansion` and `VolatilityCompressionExpansion`; 2021 and 2022 were
  also negative.
- Donchian-only same-root repair root:
  `/tmp/ict-engine-tomac-swing-portfolio-density-repair-donchian-only-20260523T000545+0800`
  stayed single-root `TrendExpansion` but failed density: `479` trades,
  `0.307840616966581` trades/session, `5bps_net=+0.259925369690389`,
  PF `1.1370768034059835`, decision `reject_low_density`.
- ATR-squeeze-only same-root repair root:
  `/tmp/ict-engine-tomac-swing-portfolio-density-repair-squeeze-only-20260523T000545+0800`
  stayed single-root `VolatilityCompressionExpansion` but failed density:
  `190` trades, `0.12210796915167095` trades/session,
  `5bps_net=+0.17283493321347174`, PF `1.2723483857102016`, decision
  `reject_low_density`.

Decision:
`drop_gate1_no_practical_density_survivor`; `pre_bayes_allowed=false`,
`bbn_allowed=false`, `catboost_allowed=false`,
`execution_tree_allowed=false`, `promotion_allowed=false`,
`trade_usable=false`, and `update_goal=false`.

Do not downstream this swing-volatility family, do not promote the mixed-root
portfolio, and do not lower the density/PF/year-stability gates. Future TOMAC
work should rotate to a materially different futures family or repair existing
TOD/NQ downstream execution predicates.

## VWAP Reclaim Persistence source-scan positives did not survive exact AQ

- Prep-only packet:
  `/private/tmp/ict-engine-tomac-vwap-reclaim-persistence-prep-only-20260528T174510+0800`
- Exact AQ root:
  `/private/tmp/ict-engine-tomac-vwap-reclaim-persistence-exact-aq-20260528T175021+0800`
- Branch:
  `RangeTransition -> VWAPMeanReclaim -> VwapReclaimPersistence -> tomac_idxfut_clean_vwap_reclaim_persistence_1m_v1`
- Source-scan attraction:
  retained TOMAC scan rows such as `VWAP_reclaim_persist_h120_z0.55_p8_rv0.8`
  showed `2141` trades, `1.7841666666666667` trades/session,
  `5bps net_ret=0.33234322232538666`, and PF `1.0638459795517186`, but the
  2024 year bucket was negative and this was not exact AQ evidence.
- Exact AQ configuration:
  NQ, `1m` origin with `5m/15m/30m/1h/4h/1d` context ladder, `max_rows=300000`,
  corrected retained local TOMAC source, no future lookahead.
- Exact AQ terminal evidence:
  `run_tomac_1m.exit=0`, `rank_rows=2`, `trade_count=110`,
  `trades_per_day=0.497738`, raw total profit `-1.34%`,
  `5bps_per_side_total_profit_pct=-12.34`, PF `0.577`,
  `survivors_5bps=[]`, `gate1_survivor=false`.
- Decision:
  `terminalized_exact_aq_gate1_reject_no_5bps_survivor`;
  `downstream_allowed=false`, `pre_bayes_allowed=false`, `bbn_allowed=false`,
  `catboost_allowed=false`, `execution_tree_allowed=false`,
  `promotion_allowed=false`, `trade_usable=false`, `update_goal=false`.

Do not promote or downstream VWAP Reclaim Persistence from source-scan dense
positives. If revisiting this branch, start from a new structural hypothesis such
as year-stability/2024-regime isolation or a different VWAP mean-reclaim child;
do not rerun the same NQ exact AQ packet unchanged.
