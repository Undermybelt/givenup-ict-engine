# MET Micro Ether Basis Unwind VWAP Reclaim Reserve

created_at: 2026-05-30T04:44:47+0800
owner: codex
agent_name: codex-met-microether-basis-unwind-vwap-reclaim-reserve
run_root: support/docs/experiments/actionable-regime-confidence/runs/20260530T044447+0800-codex-met-microether-basis-unwind-vwap-reclaim-reserve-v1
tmp_workdoc: /tmp/ict-engine-met-microether-basis-unwind-vwap-reclaim-reserve-20260530T044447+0800/workdoc.md
claim: /tmp/ict-engine-agent-claims/board-b-factor-refinement/20260530T044447+0800-codex-met-microether-basis-unwind-vwap-reclaim-reserve.claim
factor_id: met_microether_basis_unwind_vwap_reclaim_reserve_v1
session_scope: ETH/full_retained_session for tradable session coverage; product is CME Micro Ether futures
rth_filter_applied: false
promotion_allowed: false
trade_usable: false
update_goal: false

## Branch

TrendExpansion -> CryptoFuturesBasis -> MicroEtherSpotFuturesBasisUnwind -> VwapReclaimContinuation -> AtrRiskManagedMtfContinuation -> met_microether_basis_unwind_vwap_reclaim_reserve_v1

## Decision

This is a no-launch, prep-only source/cost reserve packet. Same-turn compact claim audit showed fresh active claims and no live factor process, so runtime launches were blocked. No provider rows, IBKR historical rows, Auto-Quant rows, Freqtrade rows, paper/sim fills, Pre-Bayes, BBN, path-ranker, execution-tree, feedback/update, or policy-training evidence exists for this factor.

terminal_decision: terminalized_no_launch_prep_only_cost_source_reserve
cost_model_status: cost_model_unverified
provider_rows: 0
ibkr_historical_rows: 0
auto_quant_started: false
downstream_allowed: false
pre_bayes_allowed: false
bbn_allowed: false
catboost_allowed: false
execution_tree_allowed: false
promotion_allowed: false
trade_usable: false
update_goal: false

## Official Source Readback

Verified in this slice:
- IBKR futures commissions page returned HTTP 200 and lists `CME Ethereum Micro Futures and Futures Options (MET)`.
- IBKR MET commission at monthly volume `<= 1,000` is USD 0.20 per contract under both tiered and fixed columns.
- IBKR CME fee recovery page returned HTTP 200 and lists `Micro Ether Futures MET` with USD 0.10 exchange fee recovery.
- IBKR CME regulatory fee recovery is USD 0.02 for all products; notes state NFA assesses regulatory fees.

Not verified in this slice:
- CME official product/spec pages and CME ProductSlate API were attempted but failed from this host with TLS EOF / curl exit 35.
- CME contract unit, tick, trading hours, expiry, settlement, and official product page fields are therefore not source-verified here.
- No exact broker contract month, roll rule, or historical data row proof exists.

## Cost Reserve

Partial assumption only, not promotion evidence:
- commission_usd_per_contract_side_assumption: 0.20
- exchange_fee_recovery_usd_per_contract_side_assumption: 0.10
- regulatory_fee_recovery_usd_per_contract_side_assumption: 0.02
- partial_total_usd_per_contract_side_assumption: 0.32
- partial_round_turn_usd_per_contract_assumption: 0.64

The cost model remains `cost_model_unverified` until CME official specs and broker exact-contract evidence are captured in the same turn as a real row proof.

## Next Gate

After claim/runtime blockers clear, verify CME official specs and exact IBKR MET historical rows for a concrete contract month. Only then should a real Gate 1 runner test 1m origin entries with shifted 5m/15m/30m/1h/4h/1d context and product-specific cost handling.
