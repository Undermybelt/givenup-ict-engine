# Terminal Packet: LBR ETH Lumber Housing Starts VWAP Reclaim Reserve

generated_at: 2026-05-30T05:56:17+0800
factor_id: lbr_lumber_housing_starts_vwap_reclaim_reserve_v1
branch_path: FUTURES -> AgriculturalMaterials -> CME Lumber / LBR -> ETH/full_retained_session -> 1m execution + shifted 5m/15m/30m/1h/4h/1d context -> HousingCycleDemandShock -> BuildingMaterialsInventoryStress -> VwapReclaimContinuation -> AtrRiskManagedMtfContinuation -> lbr_lumber_housing_starts_vwap_reclaim_reserve_v1
session_scope: ETH/full_retained_session for tradable futures session coverage; product is CME Lumber futures
rth_filter_applied: false

## Decision

terminal_decision: terminalized_no_launch_prep_only_cost_source_reserve
cost_model_status: cost_model_unverified
promotion_allowed: false
trade_usable: false
update_goal: false

## Evidence

- Compact claim audit before lane work: `status=needs_attention`, `valid_active_claims=2`, `fresh_active_claims_without_live_process=2`, `live_factor_processes=0`; runtime launches blocked by fresh active claims.
- IBKR futures commissions official page returned HTTP 200 and listed the US USD-denominated futures commission schedule at USD 0.85 per contract for monthly volume <= 1,000. This is not a product-specific LBR row.
- IBKR CME fee recovery official page returned HTTP 200 and listed `CME Lumber Product`, `Lumber (Futures)`, code `LBR`, exchange fee recovery USD 1.50 plus all-products regulatory fee recovery USD 0.02.
- US Census New Residential Construction page returned HTTP 200 and supports the housing-cycle rationale only.
- CME official product/spec URLs and ProductSlate API attempts failed from this host with curl exit 35 / HTTP 000, so contract unit, tick, trading hours, expiry, and settlement are not verified.

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

After active claim blockers clear, verify CME official specs and exact IBKR LBR historical rows for a concrete contract month. Only then can a Gate 1 runner test 1m origin entries with shifted 5m/15m/30m/1h/4h/1d context and product-specific cost handling.
