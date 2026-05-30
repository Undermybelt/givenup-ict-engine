# Signal Decay Half-Life Admission Source Prep

- created_at: `2026-05-31T05:55:59+0800`
- route_alias: `sd/ict-engi-fact-rese-muta`
- owner: `codex-signal-decay-half-life-admission-source-prep-20260531T055559+0800`
- workdoc: `/tmp/ict-engine-signal-decay-half-life-admission-source-prep-20260531T055559+0800/workdoc.md`
- claim: `/tmp/ict-engine-agent-claims/board-b-factor-refinement/20260531T055559+0800-codex-signal-decay-half-life-admission-source-prep.claim`
- repo_run_root: `support/docs/experiments/actionable-regime-confidence/runs/20260531T055559+0800-codex-signal-decay-half-life-admission-source-prep-v1`
- factor_family: `signal_decay_half_life_admission`
- candidate_id: `signal_decay_half_life_admission_v1`
- branch_path: `ValidationMaturity -> SignalPersistence -> InformationCoefficientDecay -> HoldingHorizonAdmission -> signal_decay_half_life_admission_v1`
- session_scope: `ETH/full_retained_session_required_for_future_tests`
- rth_filter_applied: `false`
- status: `terminalized_source_prep_no_launch`
- promotion_allowed: `false`
- trade_usable: `false`
- update_goal: `false`

## Current-State Gate

The same-turn compact audit before this packet was blocked:

- `status=needs_attention`
- `active_claims=1`
- `valid_active_claims=1`
- `live_factor_processes=2`
- `trade_usable_true=0`
- `promotion_allowed_true=0`
- live runtime roots:
  - `/tmp/ict-engine-fisher-transform-trend-rejoin-local-screen-20260531T053901+0800`
  - `/tmp/ict-engine-hull-ma-slope-pullback-rejoin-local-screen-20260531T054042+0800`

No provider, IBKR historical, AutoQuant/Freqtrade/TOMAC backend, local screen,
local backtest, paper/sim/live, downstream lifecycle, feedback ingestion,
same-tree practical closure, or policy-training command was launched from this
packet.

## Why This Is Distinct

Focused local duplicate search returned no exact current packet for
`information coefficient`, `rank IC`, `IC decay`, `alpha decay`,
`signal decay`, `forecast decay`, or `signal half-life` over current claims,
top-level actionable-regime-confidence docs, scripts, and factor-source
references.

This is not the new information-imbalance-bar packet. That packet changes the
sampling/admission structure. This one is a validation sidecar: it asks whether
a parent signal's predictive correlation persists long enough for the planned
holding period before spending AQ/provider runtime.

It also must stay separate from existing DSR/SPA/PBO, regime-posterior
calibration, factor turnover, and practical lifecycle gates. Those measure
overfit, probability quality, churn, or full readiness. This packet measures
pre-entry forecast decay against the intended holding horizon.

## Source Basis

- Grinold, `The Fundamental Law of Active Management`, Journal of Portfolio
  Management, DOI `10.3905/jpm.1989.409211`.
- Clarke, de Silva, and Thorley, `The Fundamental Law of Active Portfolio
  Management`, Financial Analysts Journal, DOI `10.2469/faj.v58.n5.2478`.
- Alphalens documentation for factor information coefficient and factor rank
  autocorrelation:
  `https://alphalens.ml4trading.io/notebooks/overview.html`

Design inference: IC/rank-IC is the candidate forecast-vs-forward-return
quality surface; factor rank autocorrelation is a persistence/turnover proxy.
The proposed sidecar estimates a rolling IC half-life and admits only parent
signals whose decay horizon covers the planned hold, with all features shifted
to completed bars.

## Candidate Contract

- role: parent-admission sidecar, not standalone alpha.
- entry: no independent entry. Admit an already-owned trend, pullback,
  breakout, or carryover parent only when shifted rolling IC or rank-IC remains
  positive across the parent holding horizon and the IC half-life is not shorter
  than the expected hold.
- confirmation:
  - completed-bar shifted parent signal values
  - forward returns computed only after the signal timestamp
  - IC/rank-IC curve by horizon
  - estimated decay half-life by rolling window
  - parent signal still valid
  - ETH/full-retained coverage proof
  - exact instrument-cost model
  - no same-bar target leakage
- first future runtime shape: after compact audit clears, rescore one existing
  parent that already has trade rows. Compare parent-only versus
  parent-plus-signal-decay admission on instrument-cost return, trade count,
  trades/session, split/year stability, and downstream readiness.

## Future Gates

- Keep `promotion_allowed=false`, `trade_usable=false`, and `update_goal=false`
  until same-tree practical closure validates from the same run root.
- Do not use source prep, IC-only analysis, or local Python proxy evidence as
  trade readiness.
- Do not relax parent density, sample, split/year, instrument-cost, provider,
  accepted-feedback, or lifecycle gates.
- If the parent has too few trade labels for stable IC-by-horizon estimates,
  classify as `signal_decay_sample_blocked`, not practical.

## Evidence Files

- tmp source readback:
  `/tmp/ict-engine-signal-decay-half-life-admission-source-prep-20260531T055559+0800/materials/source_readback.json`
- tmp terminal metrics:
  `/tmp/ict-engine-signal-decay-half-life-admission-source-prep-20260531T055559+0800/checks/terminal_metrics.json`
- tmp terminal summary:
  `/tmp/ict-engine-signal-decay-half-life-admission-source-prep-20260531T055559+0800/summaries/terminal_no_launch_summary.json`
- repo source readback:
  `support/docs/experiments/actionable-regime-confidence/runs/20260531T055559+0800-codex-signal-decay-half-life-admission-source-prep-v1/materials/source_readback.json`
- repo terminal metrics:
  `support/docs/experiments/actionable-regime-confidence/runs/20260531T055559+0800-codex-signal-decay-half-life-admission-source-prep-v1/checks/terminal_metrics.json`
- repo terminal summary:
  `support/docs/experiments/actionable-regime-confidence/runs/20260531T055559+0800-codex-signal-decay-half-life-admission-source-prep-v1/summaries/terminal_no_launch_summary.json`
