# Terminal Packet: MET Micro Ether Basis Unwind VWAP Reclaim Reserve

generated_at: 2026-05-30T04:44:47+0800
factor_id: met_microether_basis_unwind_vwap_reclaim_reserve_v1
branch_path: TrendExpansion -> CryptoFuturesBasis -> MicroEtherSpotFuturesBasisUnwind -> VwapReclaimContinuation -> AtrRiskManagedMtfContinuation -> met_microether_basis_unwind_vwap_reclaim_reserve_v1
session_scope: ETH/full_retained_session for tradable session coverage; product is CME Micro Ether futures
rth_filter_applied: false

## Decision

terminal_decision: terminalized_no_launch_prep_only_cost_source_reserve
cost_model_status: cost_model_unverified
promotion_allowed: false
trade_usable: false
update_goal: false

## Evidence

- Compact claim audit before lane work: `status=needs_attention`, `valid_active_claims=2`, `live_factor_processes=0`; runtime launches blocked by fresh active claims.
- IBKR futures commissions official page returned HTTP 200 and listed `CME Ethereum Micro Futures and Futures Options (MET)` with USD 0.20 per contract at monthly volume <= 1,000.
- IBKR CME fee recovery official page returned HTTP 200 and listed `Micro Ether Futures MET` exchange fee recovery USD 0.10 plus all-products regulatory fee recovery USD 0.02.
- CME official product/spec URLs and ProductSlate API attempts failed from this host with TLS EOF / curl exit 35, so contract unit, tick, trading hours, expiry, and settlement are not verified.

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

After active claim blockers clear, verify CME official specs and exact IBKR MET historical rows for a concrete contract month. Only then can a Gate 1 runner test 1m origin entries with shifted 5m/15m/30m/1h/4h/1d context and product-specific cost handling.
