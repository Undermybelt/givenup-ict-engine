# ZO ETH Oats Crop Progress VWAP Reclaim Reserve

created_at: 2026-05-30T06:07:51+0800
agent_name: codex-zo-eth-oats-crop-progress-vwap-reclaim-reserve
owner: codex
run_root: /tmp/ict-engine-zo-eth-oats-crop-progress-vwap-reclaim-reserve-20260530T060751+0800
workdoc: /tmp/ict-engine-zo-eth-oats-crop-progress-vwap-reclaim-reserve-20260530T060751+0800/workdoc.md
claim: /tmp/ict-engine-agent-claims/board-b-factor-refinement/20260530T060751+0800-codex-zo-eth-oats-crop-progress-vwap-reclaim-reserve.claim
compact_root: support/docs/experiments/actionable-regime-confidence/runs/20260530T060751+0800-codex-zo-eth-oats-crop-progress-vwap-reclaim-reserve-v1

## Scope

Reserve a distinct oats futures profitability-factor branch while current fresh
Board B claims and a live MGC AutoQuant runtime block shared launches. This
packet is source/cost prep only. No provider fetch, IBKR historical pull,
AutoQuant, Freqtrade, TOMAC, paper, simulated, live, downstream lifecycle, or
local backtest command was launched for this ZO packet.

## Factor Identity

factor_id: zo_eth_oats_crop_progress_vwap_reclaim_v1

branch_path: FUTURES -> Agriculture -> CBOT Oats / ZO -> ETH/full_retained_session -> 1m execution + shifted 5m/15m/30m/1h/4h/1d context -> CropProgressSupplyShock -> ThinAgMarketLiquidityFlush -> OatsSessionVwapReclaim -> AtrRiskManagedContinuation -> zo_eth_oats_crop_progress_vwap_reclaim_v1

session_scope: ETH/full_retained_session
rth_filter_applied: false
coverage_evidence: not_validated_source_only

## Why This Is Distinct

This is not ZR rough rice, ZC corn, ZS soybeans, ZL soybean oil, ZW wheat, KC
coffee, CT cotton, OJ orange juice, livestock, metals, energy, rates, FX,
NQ/ES/YM, or TOMAC. It is a CBOT oats futures branch whose future test needs
ZO-specific retained session bars, contract/roll evidence, USDA/NASS sidecar
data, and an official all-in cost model.

## Candidate Shape

- Origin: ZO 1m execution bars from verified provider data.
- Context: shifted 5m/15m/30m/1h/4h/1d ZO bars, with optional USDA/NASS oats
  acreage, production, yield, stocks, or crop-progress sidecar data available
  without lookahead.
- Entry concept: a thin agricultural liquidity flush that reclaims session VWAP
  after oats-specific crop-progress or stocks stress confirms a non-generic grain
  move.
- Risk: ATR stop, lower turnover, and multi-hour hold target. The branch must
  survive actual CBOT/IBKR futures costs and slippage before any downstream use.

## Same-Turn Source Readback

- IBKR futures commissions page: HTTP 200. US USD-denominated futures schedule
  exposes USD 0.85 per contract for monthly volume <= 1,000 under both tiered
  and fixed columns. This is a broad USD futures row, not ZO-specific execution
  commission proof.
- IBKR CBOT fee recovery page: HTTP 200. It lists `Ags-Electronic Futures` with
  `ZC, ZL, ZM, ZO, ZR, ZS, ZW, KE`, exchange fee recovery USD 2.15.
- IBKR CBOT fee recovery page: regulatory fee recovery USD 0.02 and NFA note
  present.
- USDA NASS Statistics by Subject for OATS: HTTP 200. It exposes oats
  publications and county maps for acreage, yield, production, stocks, prices,
  and values. This is rationale/sidecar-source evidence only, not tradable proof.
- CME official oats product/spec pages: attempted same turn; curl returned exit
  35 / HTTP 000 from this host. Contract specs remain unverified.

## Terminal Decision

terminal_decision: terminalized_no_launch_prep_only_cost_source_reserve
cost_model_status: cost_model_unverified
provider_rows: 0
ibkr_historical_rows: 0
auto_quant_started: false
freqtrade_started: false
paper_or_sim_started: false
pre_bayes_allowed: false
bbn_allowed: false
catboost_allowed: false
execution_tree_allowed: false
feedback_update_allowed: false
policy_training_allowed: false
promotion_allowed: false
trade_usable: false
update_goal: false

## Preconditions For Any Future Launch

- Re-run `python3 support/scripts/factor_claim_terminalization_audit.py --compact`.
- Re-run focused provider/AQ/process `ps` guard.
- Prove retained ETH/full-session provider rows, including timestamps outside the
  approximate regular trading window.
- Verify ZO contract multiplier, tick value, commission, exchange fee,
  regulatory fee, currency, venue, broker/pricing plan, and fee-effective date
  from official source artifacts.
- Keep `promotion_allowed=false`, `trade_usable=false`, and `update_goal=false`
  until exact Gate 1, downstream lifecycle, paper/sim, and practical evidence all
  pass.
