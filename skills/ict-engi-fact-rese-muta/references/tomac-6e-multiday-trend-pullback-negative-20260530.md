# TOMAC 6E Multiday Trend Pullback Negative - 2026-05-30

This is a prep-only negative boundary from a waiting-window lane. It was created
while fresh Board B claims blocked shared provider/AQ launch, so no provider,
IBKR, Auto-Quant, Freqtrade, paper, or lifecycle command was launched.

## Lane

- Agent: `codex-6e-multiday-trend-pullback-reaccel-prep`
- Repo doc: `support/docs/experiments/actionable-regime-confidence/20260530T004615+0800-codex-6e-multiday-trend-pullback-reaccel-prep.md`
- Workdoc: `/tmp/ict-engine-6e-multiday-trend-pullback-reaccel-prep-20260530T004615+0800/workdoc.md`
- Terminal metrics: `/tmp/ict-engine-6e-multiday-trend-pullback-reaccel-prep-20260530T004615+0800/checks/terminal_metrics.json`
- Branch root: `TrendExpansion -> MultidayPullback -> Reacceleration`
- Factor root: `6e_multiday_trend_pullback_reaccel_v1`

## Data Truth

The local EUR/6E cleaned ladder used here is not a full 2021-2025 practical
window. Same-turn data readback showed:

- `1m`: 200224 rows, 2020-06-29 to 2023-12-18
- `5m`: 49557 rows, 2020-06-29 to 2023-12-18
- `15m`: 20177 rows, 2020-06-29 to 2023-12-18
- `30m`: synthesized from `15m`, 11569 rows
- `1h`: 6629 rows, 2020-06-29 to 2023-12-18
- `4h`: 2297 rows, 2020-06-29 to 2023-12-18
- `1d`: 618 rows, 2020-06-29 to 2023-12-18

Future agents must not claim this as full-window 2025 evidence. If revisiting
6E, first obtain a denser/current verified ladder or explicitly label the
retained data limitation.

## Cost Model

IBKR futures commission page was reachable, but exact all-in 6E cost was not
extracted. CME Euro FX contract/spec endpoints failed from this host with TLS
errors. Therefore the lane stayed `cost_model_unverified` and fail-closed.

Do not promote, paper-admit, or AQ-launch this branch until product-specific
6E multiplier, tick value, broker commission, exchange/regulatory fees, side
convention, account region/plan, and fee-effective date are verified from
official sources.

## Screen Result

The local wrapper `run_tomac_6e_multiday_trend_pullback_reaccel_prep_v1.py`
used shifted higher-timeframe context, synthesized missing `30m` bars from
`15m`, and tested three multiday trend-pullback variants. Focused unit tests
covered branch identity, ladder declaration, 30m synthesis, no-lookahead context
shift, and cost-unverified fail-closed classification.

Terminal readback:

- `candidate_count=3`
- `gate1_survivor_count=0`
- `cost_model_status=unverified`
- `promotion_allowed=false`
- `trade_usable=false`
- `update_goal=false`
- `terminal_decision=prep_only_cost_model_unverified_no_aq_launch`

Rows by 5bps/side stress:

| factor_id | trades | trades/session | 5bps/side % | decision |
|---|---:|---:|---:|---|
| `tomac_6e_15m_multiday_trend_pullback_reaccel_quality_gate1_v1` | 84 | 0.135922 | -9.153948 | prep_only_cost_model_unverified |
| `tomac_6e_30m_multiday_trend_pullback_reaccel_wide_hold_gate1_v1` | 70 | 0.113269 | -10.166785 | prep_only_cost_model_unverified |
| `tomac_6e_15m_multiday_trend_pullback_reaccel_balanced_gate1_v1` | 141 | 0.228155 | -12.302996 | prep_only_cost_model_unverified |

## Reuse Guidance

- Treat this exact 6E/EUR multiday trend-pullback reacceleration cell as a
  negative prep screen, not a positive AQ seed.
- Do not repeat the same three variants unchanged after claim pressure clears;
  they are already negative under the generic 5bps/side stress and cannot be
  promoted because the cost model is unverified.
- If 6E trend work continues, materially change the hypothesis: lower churn is
  not enough by itself; require verified costs, better/current data coverage,
  and a redesigned exit/risk or parent-filter relationship.
- Keep `promotion_allowed=false`, `trade_usable=false`, and `update_goal=false`
  until a future same-root run has verified costs, strict Gate 1 survival,
  Auto-Quant/provider or paper/sim lifecycle evidence, and the complete
  practical tuple.
