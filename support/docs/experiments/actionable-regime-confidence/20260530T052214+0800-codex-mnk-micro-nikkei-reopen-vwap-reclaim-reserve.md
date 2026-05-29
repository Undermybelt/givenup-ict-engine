# MNK/MNI Micro Nikkei Reopen VWAP Reclaim Reserve

created_at: 2026-05-30T05:22:14+0800
owner: codex
agent_name: codex-mnk-micro-nikkei-reopen-vwap-reclaim-reserve
run_root: support/docs/experiments/actionable-regime-confidence/runs/20260530T052214+0800-codex-mnk-micro-nikkei-reopen-vwap-reclaim-reserve-v1
tmp_workdoc: /tmp/ict-engine-mnk-micro-nikkei-reopen-vwap-reclaim-reserve-20260530T052214+0800/workdoc.md
claim: /tmp/ict-engine-agent-claims/board-b-factor-refinement/20260530T052214+0800-codex-mnk-micro-nikkei-reopen-vwap-reclaim-reserve.claim
factor_id: mnk_micro_nikkei_reopen_vwap_reclaim_reserve_v1
session_scope: ETH/full_retained_session for tradable session coverage; product family is CME Micro Nikkei futures MNK/MNI
rth_filter_applied: false
promotion_allowed: false
trade_usable: false
update_goal: false

## Branch

TrendExpansion -> AsiaEquityIndexReopen -> MicroNikkeiSessionReopenDislocation -> VwapReclaimContinuation -> KalmanFairValueSlopeFilter -> AtrRiskManagedMtfContinuation -> mnk_micro_nikkei_reopen_vwap_reclaim_reserve_v1

## Profit Hypothesis

Use Japan cash-session reopen dislocation after US risk carry and JPY policy shocks as the parent regime. The intended factor waits for the Micro Nikkei futures session to reclaim session VWAP after a failed extension, then requires fair-value slope alignment and higher-timeframe confirmation from shifted 5m/15m/30m/1h/4h/1d context. This is only a reserve packet; no Gate 1, provider rows, IBKR historical rows, Auto-Quant rows, or paper/sim evidence exists yet.

## Decision

This is a no-launch, prep-only source/cost reserve packet. Same-turn compact claim audit showed a fresh MGC Kalman/VWAP full-ladder active claim, so provider, IBKR historical, Auto-Quant, Freqtrade, paper/sim, and lifecycle launches were blocked. This package keeps the future branch distinct from the active MGC lane and records cost/source evidence for later training.

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
- IBKR futures commissions page returned HTTP 200 and lists MNK/MNI in the `Spot-Quoted Futures, E-micro Futures and Futures Options` section.
- IBKR MNK/MNI commission bucket at monthly volume `<= 1,000` is USD 0.25 per contract under both tiered and fixed columns.
- IBKR CME fee recovery page returned HTTP 200 and lists `Micro Nikkei Futures Products` / `MNK, MNI` exchange fee recovery USD 0.43.
- IBKR CME regulatory fee recovery is USD 0.02 for all products; notes state NFA assesses regulatory fees.

Not verified in this slice:
- CME official product/spec pages and CME ProductSlate API were attempted but failed from this host with TLS EOF / curl exit 35 and Python urllib `UNEXPECTED_EOF_WHILE_READING`.
- CME contract unit, tick, trading hours, expiry, settlement, and exact official product spec remain unverified.
- No exact broker contract month, roll rule, historical data row proof, ETH/full-session row coverage, or slippage model exists.

## Cost Reserve

Partial assumption only, not promotion evidence:
- commission_usd_per_contract_side_assumption: 0.25
- exchange_fee_recovery_usd_per_contract_side_assumption: 0.43
- regulatory_fee_recovery_usd_per_contract_side_assumption: 0.02
- partial_total_usd_per_contract_side_assumption: 0.70
- partial_round_turn_usd_per_contract_assumption: 1.40

The cost model remains `cost_model_unverified` until CME official specs, exact broker contract evidence, same-turn historical rows, ETH/full retained row coverage, and a slippage model are captured.

## Next Gate

After claim/runtime blockers clear, verify CME official specs and exact IBKR MNK or MNI historical rows for a concrete contract month. Only then should a real Gate 1 runner test 1m origin entries with shifted 5m/15m/30m/1h/4h/1d context and product-specific cost handling.
