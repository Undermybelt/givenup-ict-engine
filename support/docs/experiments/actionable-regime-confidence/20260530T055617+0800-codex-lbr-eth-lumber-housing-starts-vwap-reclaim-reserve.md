# LBR ETH Lumber Housing Starts VWAP Reclaim Reserve

created_at: 2026-05-30T05:56:17+0800
owner: codex
agent_name: codex-lbr-eth-lumber-housing-starts-vwap-reclaim-reserve
run_root: support/docs/experiments/actionable-regime-confidence/runs/20260530T055617+0800-codex-lbr-eth-lumber-housing-starts-vwap-reclaim-reserve-v1
tmp_workdoc: /tmp/ict-engine-lbr-eth-lumber-housing-starts-vwap-reclaim-reserve-20260530T055617+0800/workdoc.md
claim: /tmp/ict-engine-agent-claims/board-b-factor-refinement/20260530T055617+0800-codex-lbr-eth-lumber-housing-starts-vwap-reclaim-reserve.claim
factor_id: lbr_lumber_housing_starts_vwap_reclaim_reserve_v1
session_scope: ETH/full_retained_session for tradable futures session coverage; product is CME Lumber futures
rth_filter_applied: false
promotion_allowed: false
trade_usable: false
update_goal: false

## Branch

FUTURES -> AgriculturalMaterials -> CME Lumber / LBR -> ETH/full_retained_session -> 1m execution + shifted 5m/15m/30m/1h/4h/1d context -> HousingCycleDemandShock -> BuildingMaterialsInventoryStress -> VwapReclaimContinuation -> AtrRiskManagedMtfContinuation -> lbr_lumber_housing_starts_vwap_reclaim_reserve_v1

## Decision

This is a no-launch, source/cost reserve packet. Same-turn compact claim audit showed two fresh active claims with no stale-safe takeover candidate, so provider, IBKR historical, Auto-Quant, Freqtrade, paper/sim, lifecycle, and Gate 1 launches were blocked. No provider rows, IBKR historical rows, Auto-Quant rows, Freqtrade rows, paper/sim fills, Pre-Bayes, BBN, path-ranker, execution-tree, feedback/update, or policy-training evidence exists for this factor.

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

- IBKR futures commissions official page returned HTTP 200 and exposes the US futures by-denomination schedule; the USD futures row showed USD 0.85 per contract for monthly volume `<= 1,000` under both tiered and fixed columns.
- IBKR CME fee recovery official page returned HTTP 200 and lists `CME Lumber Product`, `Lumber (Futures)`, code `LBR`, exchange fee recovery USD 1.50.
- IBKR CME fee recovery official page lists all-products regulatory fee recovery USD 0.02 and notes that regulatory fees are assessed by the National Futures Association.
- US Census New Residential Construction page returned HTTP 200 and describes national/regional housing permits, starts, construction, and completions data. This is rationale evidence only, not factor data or tradable proof.

Not verified in this slice:

- CME official lumber product/spec pages and ProductSlate API attempts failed from this host with curl exit 35 / HTTP 000.
- CME contract unit, tick size, tick value, trading hours, expiry, settlement, and exact official product spec remain unverified.
- No exact IBKR contract month, historical data row proof, roll rule, retained-session row coverage, or slippage model exists.
- The IBKR execution commission row used here is the broad USD futures by-denomination schedule, not a product-specific LBR commission row.

## Cost Reserve

Partial assumption only, not promotion evidence:

- commission_usd_per_contract_side_assumption: 0.85
- exchange_fee_recovery_usd_per_contract_side_assumption: 1.50
- regulatory_fee_recovery_usd_per_contract_side_assumption: 0.02
- partial_total_usd_per_contract_side_assumption: 2.37
- partial_round_turn_usd_per_contract_assumption: 4.74

The cost model remains `cost_model_unverified` until CME official specs, exact broker contract evidence, same-turn historical rows, retained-session coverage, and a slippage model are captured.

## Runtime And Duplicate Boundary

- Compact audit before packet creation: `status=needs_attention`, `valid_active_claims=2`, `fresh_active_claims_without_live_process=2`, `live_factor_processes=0`, `promotion_allowed_true=0`, `trade_usable_true=0`, `same_tree_practical_closure=null`.
- Fresh active blockers were HO/ULSD source reserve and MGC quality-hold-filter full-ladder training. This packet does not take over or overlap either branch.
- Focused process readback showed no `fetch_external.py`, IBKR historical, Auto-Quant/Freqtrade, TOMAC, provider-status IBKR, or lifecycle writer process for this LBR branch.
- Focused duplicate search found no exact LBR/lumber repo tracking doc or active claim; existing hits were unrelated product non-goals or already terminalized reserve families.

## Next Gate

After active claim blockers clear, verify CME official specs and exact IBKR LBR historical rows for a concrete contract month. Only then should a real Gate 1 runner test 1m origin entries with shifted 5m/15m/30m/1h/4h/1d context and product-specific cost handling.
