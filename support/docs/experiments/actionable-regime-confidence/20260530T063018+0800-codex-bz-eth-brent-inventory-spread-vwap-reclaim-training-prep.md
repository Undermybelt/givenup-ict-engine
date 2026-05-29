# BZ ETH Brent Inventory-Spread VWAP Reclaim Training Prep

- agent_name: `codex-bz-eth-brent-inventory-spread-vwap-reclaim-training-prep`
- created_at: `2026-05-30T06:30:18+0800`
- status: `terminalized_no_launch_training_prep_cost_model_unverified`
- factor_id: `bz_eth_brent_inventory_spread_vwap_reclaim_v1`
- session_scope: `ETH/full_retained_session`
- rth_filter_applied: `false`
- origin_timeframe: `1m`
- context_timeframes: `5m/15m/30m/1h/4h/1d`
- promotion_allowed: `false`
- trade_usable: `false`
- update_goal: `false`

## Objective

Create a distinct regime-rooted profitability-factor training packet for ICE
Brent crude futures while a fresh Board B claim blocks provider and AutoQuant
launches. This packet advances the objective by preserving the exact rooted
branch, official source readbacks, full-ladder training plan, and guarded
AutoQuant next command. It is not Gate 1 evidence and not practical promotion.

## Branch

`FUTURES -> EnergyFutures -> ICE Brent Crude / BZ -> ETH/full_retained_session -> 1m execution + shifted 5m/15m/30m/1h/4h/1d context -> AtlanticCrudeInventorySpreadTransition -> BrentWtiRefineryMarginShock -> LondonSessionLiquidityFlushVwapReclaim -> AtrRiskManagedMtfContinuation -> bz_eth_brent_inventory_spread_vwap_reclaim_v1`

## Profit Hypothesis

Brent often reprices around Atlantic Basin supply shocks, EIA petroleum storage
data, refinery margin expectations, and Brent-WTI spread transitions. The factor
should look for a liquidity flush below session VWAP during the London or early
New York energy window, then require a 1m reclaim only when higher-timeframe
context shows the flush is a transition/reclaim rather than trend continuation.

The training design uses 1m origin entries with shifted `5m/15m/30m/1h/4h/1d`
features:

- `5m/15m`: confirm reclaim persistence after sweep and reject one-bar spikes.
- `30m/1h`: filter by Brent-WTI spread impulse and crude-inventory regime.
- `4h/1d`: classify inventory shock, risk-on/off energy beta, and trend slope.
- Multi-cycle resonance target: only escalate candidates where 1m reclaim aligns
  with at least two higher context windows and cost-stressed density is not sparse.

## Current Collision State

Same-turn compact claim audit before writing this packet reported:

- `status=needs_attention`
- `active_claims=1`
- blocker: `20260530T062401+0800-codex-nq-compound-rv-stress-lifecycle-driver.claim`
- `live_factor_processes=0`
- `promotion_allowed_true=0`
- `trade_usable_true=0`
- `same_tree_practical_closure=null`

Because the blocker is a fresh active claim, this slice did not launch provider,
IBKR historical, AutoQuant, Freqtrade, TOMAC, paper/sim/live, lifecycle, or local
backtest work.

## Source Readback

Official source checks run in this turn:

- ICE Brent Crude Futures product page: HTTP `200`.
- IBKR futures commissions page: HTTP `200`.
- EIA petroleum weekly page: HTTP `200`.
- EIA weekly petroleum status report page: HTTP `200`.
- ICE fees page: HTTP `200`.

Blocked or incomplete source checks:

- ICE Futures Europe fees URL returned HTTP `404`.
- Guessed ICE futures fee-schedule PDF URLs returned HTTP `404`.
- Exact BZ/Brent exchange-fee recovery, broker product mapping, multiplier,
  tick size, tick value, routing/account applicability, and historical row
  coverage are not verified in this packet.

## Cost And Promotion Decision

Cost status is `cost_model_unverified`. The generic IBKR futures commission page
is not sufficient to promote this product because exact BZ/ICE Brent exchange
fees, regulatory/clearing components, unit convention, broker routing, and
fee-effective date are not fully rate-verified.

`promotion_allowed=false`, `trade_usable=false`, and `update_goal=false` remain
mandatory until exact cost, ETH/full retained-session row coverage, Gate 1,
AutoQuant, downstream Bayesian/BBN/path-ranker/execution-tree feedback, and
paper/sim lifecycle evidence all pass.

## Deferred AutoQuant Plan

When compact audit and focused process scan are clear, create a fresh launch
claim and run root, then fetch/prepare BZ retained-session data with no RTH-only
filter. The minimum launch plan is:

```bash
python3 support/docs/experiments/actionable-regime-confidence/scripts/run_tomac_index_futures_clean_aq_v1.py \
  --symbols BZ \
  --timeframes 1m,5m,15m,30m,1h,4h,1d \
  --families energy_inventory_spread_vwap_reclaim \
  --aq-smoke-timeframe 1m \
  --aq-symbol-limit 1 \
  --root /tmp/ict-engine-bz-eth-brent-inventory-spread-vwap-reclaim-training-launch-<stamp>/aq \
  --compact-root support/docs/experiments/actionable-regime-confidence/runs/<stamp>-codex-bz-eth-brent-inventory-spread-vwap-reclaim-training-launch-v1/aq \
  --timeout 1800
```

If the existing TOMAC family registry lacks `energy_inventory_spread_vwap_reclaim`,
add it with TDD in `candidate_specs()` and verify it before launch. Do not hand
roll a one-off practical packet or lower density/cost gates to manufacture a pass.

## Evidence

- `/tmp` workdoc: `/tmp/ict-engine-bz-eth-brent-inventory-spread-vwap-reclaim-training-prep-20260530T063018+0800/workdoc.md`
- Claim: `/tmp/ict-engine-agent-claims/board-b-factor-refinement/20260530T063018+0800-codex-bz-eth-brent-inventory-spread-vwap-reclaim-training-prep.claim`
- Source/cost readback JSON: `support/docs/experiments/actionable-regime-confidence/runs/20260530T063018+0800-codex-bz-eth-brent-inventory-spread-vwap-reclaim-training-prep-v1/checks/source_cost_readback_20260530T063018+0800.json`
- Terminal summary: `support/docs/experiments/actionable-regime-confidence/runs/20260530T063018+0800-codex-bz-eth-brent-inventory-spread-vwap-reclaim-training-prep-v1/summaries/terminal_summary.json`
