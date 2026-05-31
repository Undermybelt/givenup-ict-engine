# Anderson-Darling Tail-Shift Admission Source Prep

- owner: `codex-anderson-darling-tail-shift-admission-source-prep-20260531T104725+0800`
- run_root: `/tmp/ict-engine-anderson-darling-tail-shift-admission-source-prep-20260531T104725+0800`
- workdoc: `/tmp/ict-engine-anderson-darling-tail-shift-admission-source-prep-20260531T104725+0800/workdoc.md`
- claim: `/tmp/ict-engine-agent-claims/board-b-factor-refinement/20260531T104725+0800-codex-anderson-darling-tail-shift-admission-source-prep.claim`
- terminal_metrics: `/tmp/ict-engine-anderson-darling-tail-shift-admission-source-prep-20260531T104725+0800/checks/terminal_metrics.json`
- terminal_summary: `/tmp/ict-engine-anderson-darling-tail-shift-admission-source-prep-20260531T104725+0800/summaries/terminal_summary.json`
- factor_family: `anderson_darling_tail_shift_admission_filter`
- factor_id_template: `tomac_idxfut_clean_anderson_darling_tail_shift_admission_<timeframe>_v1`
- branch_path_template: `TrendExpansion -> DistributionShapeStability -> AndersonDarlingTailShift -> ParentSignalAdmissionFilter -> tomac_idxfut_clean_anderson_darling_tail_shift_admission_<timeframe>_v1`
- session_scope: `ETH/full_retained_session target`
- rth_filter_applied: `false` by future contract; no data was fetched in this packet
- promotion_allowed: `false`
- trade_usable: `false`
- update_goal: `false`

## Status

This is a terminalized source/prep no-launch packet. It was created because the
same-turn compact audit reported a foreign live exact-AQ owner:

- compact_audit_status: `needs_attention`
- valid_active_claims: `1`
- live_factor_processes: `1`
- live_runtime_root: `/tmp/ict-engine-range-compression-participation-trend-breakout-aq-nq-5m-20260531T103209+0800`
- promotion_allowed_true: `0`
- trade_usable_true: `0`

No provider-status, provider fetch, IBKR historical, AutoQuant, Freqtrade/TOMAC
runtime, local backtest, local screen, paper/sim/live, downstream lifecycle,
Pre-Bayes, BBN, CatBoost/path-ranker, execution-tree, feedback update, policy
training, or same-tree practical closure command was run.

## Source Basis

- Scholz and Stephens, `K-Sample Anderson-Darling Tests`, Journal of the
  American Statistical Association, 1987, DOI `10.1080/01621459.1987.10478517`.
  Source URL: `https://www.tandfonline.com/doi/abs/10.1080/01621459.1987.10478517`.
- SciPy `scipy.stats.anderson_ksamp` documentation. Source URL:
  `https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.anderson_ksamp.html`.

The signal idea is not that Anderson-Darling predicts direction. It is a
tail-weighted empirical-CDF distribution-shape gate. A future factor should
compare a completed-bar current pre-entry feature window against a train-split
reference window and only admit a parent continuation/rejoin entry if the
distribution shift is not adverse for that side.

## Duplicate Check

Focused local searches covered `/tmp/ict-engine-agent-claims/board-b-factor-refinement`,
top-level actionable-regime-confidence docs, and actionable-regime-confidence
scripts. Exact terms checked:

- `anderson-darling`
- `anderson_darling`
- `anderson_ksamp`
- `ad_ksamp`
- `k-sample Anderson`

The exact search returned zero hits before this packet was written.

Nearby occupied or terminalized families were explicitly rejected:

- Kalman/state-space and predictive-innovation lanes.
- Copula tail-dependence and cross-quantilogram tail-dependence lanes.
- Mass Index / Dorsey lanes.
- Kernel MMD, Wasserstein, Jensen-Shannon, distance correlation, and other
  distribution/dependency admission lanes.

This packet is distinct because it uses an Anderson-Darling k-sample statistic
for adverse tail-shape stability, not kernel distance, optimal transport,
histogram divergence, or correlation/dependence.

## Candidate Contract

- main_regime: `TrendExpansion`
- sub_regime: `DistributionShapeStability`
- sub_sub_regime_or_profit_factor: `AndersonDarlingTailShift`
- profit_factor: `ParentSignalAdmissionFilter`
- preferred origin/context: `1m` origin with shifted `5m/15m/30m/1h/4h/1d`
  context where retained data supports it
- independent candidate timeframes: `5m`, `15m`, `30m`, `1h`, `4h`, `1d`

Future implementation constraints:

- Use completed bars only and shift all admission features before entry assignment.
- Use train-split-only reference distributions; no reference window may be built
  from future winners or terminal labels.
- Treat the raw AD statistic as a non-directional distribution-change score.
- Add side-aware adverse-tail summaries before any long/short admission.
- Prefer midrank/tie-aware handling for rounded OHLCV-derived features.
- Use permutation p-values or conservative thresholds when sample size is small.
- Keep parent-only and parent-plus-AD results separate in readback.

## Next Clean-Window Plan

1. Re-run `python3 support/scripts/factor_claim_terminalization_audit.py --compact`.
2. Re-run focused `ps` for AQ/TOMAC/provider/IBKR/fetch/runtime.
3. If both are clear, add focused tests for candidate registration and shifted
   source generation in the clean-AQ wrapper.
4. Implement material prep/source generation only first.
5. Launch at most one guarded clean-AQ slice after an in-process full-audit
   collision guard passes.
6. Keep `promotion_allowed=false`, `trade_usable=false`, and `update_goal=false`
   unless full same-tree practical lifecycle evidence later exists.

## Terminal Decision

- decision: `terminalized_source_prep_no_launch_complete`
- source_prep_only: `true`
- provider_or_runtime_launched: `false`
- promotion_allowed: `false`
- trade_usable: `false`
- update_goal: `false`

