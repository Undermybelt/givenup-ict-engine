# Terminal Packet: ZO ETH Oats Crop Progress VWAP Reclaim Reserve

generated_at: 2026-05-30T06:07:51+0800
factor_id: zo_eth_oats_crop_progress_vwap_reclaim_v1
branch_path: FUTURES -> Agriculture -> CBOT Oats / ZO -> ETH/full_retained_session -> 1m execution + shifted 5m/15m/30m/1h/4h/1d context -> CropProgressSupplyShock -> ThinAgMarketLiquidityFlush -> OatsSessionVwapReclaim -> AtrRiskManagedContinuation -> zo_eth_oats_crop_progress_vwap_reclaim_v1
session_scope: ETH/full_retained_session
rth_filter_applied: false

## Decision

terminal_decision: terminalized_no_launch_prep_only_cost_source_reserve
cost_model_status: cost_model_unverified
promotion_allowed: false
trade_usable: false
update_goal: false

## Evidence

- Compact claim audit before lane work: `status=needs_attention`, `valid_active_claims=4`, `live_factor_processes=1`; runtime launches blocked by fresh active claims and a live MGC AutoQuant root.
- Focused process table showed `run_ibkr_mgc1m_kalman_vwap_slope_quality_hold_filter_full_ladder_gate1_v1.py --launch-aq`, `auto-quant-agent-material-dispatch`, and `run_tomac.py` under the MGC run root.
- IBKR futures commissions official page returned HTTP 200 and listed broad USD-denominated futures commission USD 0.85 per contract at monthly volume <= 1,000. This is not ZO-specific commission proof.
- IBKR CBOT fee recovery official page returned HTTP 200 and listed `Ags-Electronic Futures` including `ZO` with USD 2.15 exchange fee recovery plus USD 0.02 regulatory fee recovery.
- USDA NASS OATS Statistics by Subject returned HTTP 200 and supports only the crop-progress/stocks rationale sidecar.
- CME official oats product/spec URLs failed from this host with curl exit 35 / HTTP 000, so contract unit, tick, trading hours, expiry, and settlement are not verified.

## No-Launch Readback

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

## Next Gate

After active claim and live runtime blockers clear, verify CME/CBOT official specs and exact IBKR ZO historical rows for a concrete contract month. Only then can a Gate 1 runner test 1m origin entries with shifted 5m/15m/30m/1h/4h/1d context and product-specific cost handling.
