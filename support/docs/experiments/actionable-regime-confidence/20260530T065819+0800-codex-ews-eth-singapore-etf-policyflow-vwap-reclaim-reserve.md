# EWS ETH Singapore ETF Policyflow VWAP Reclaim Reserve

- agent_name: `codex-ews-eth-singapore-etf-policyflow-vwap-reclaim-reserve`
- created_at: `2026-05-30T06:58:19+0800`
- status: `terminalized_no_launch_source_cost_reserve_cost_model_unverified`
- factor_id: `ews_eth_singapore_etf_policyflow_vwap_reclaim_v1`
- instrument: `EWS` / iShares MSCI Singapore ETF
- session_scope: `ETH/full_retained_session`
- rth_filter_applied: `false`
- origin_timeframe: `1m`
- context_timeframes: `5m/15m/30m/1h/4h/1d`
- promotion_allowed: `false`
- trade_usable: `false`
- update_goal: `false`

## Objective

Create a distinct no-launch profitability-factor reserve packet for a US-listed
Singapore single-country ETF while Board B runtime is occupied by a fresh TOMAC
Aroon/CCI cadence-volume persistence retest claim. This packet preserves the
rooted branch, verified product identity, source/cost blockers, and a later
Gate 1 plan. It is not provider-row evidence, Gate 1 evidence, AutoQuant
evidence, or practical promotion evidence.

## Current Blocker

Same-turn compact audit before this packet reported:

- `status=needs_attention`
- `active_claims=1`
- blocking claim: `20260530T064801+0800-codex-tomac-aroon-cci-cadence-volume-persistence-retest-training-prep.claim`
- claim status: `active`; latest workdoc/claim says `autoquant_started=true` and `status=active_aq_launch`
- `live_factor_processes=0` in compact audit, but the fresh active claim is enough to block new launches
- `promotion_allowed_true=0`
- `trade_usable_true=0`
- `same_tree_practical_closure=null`

Because the active claim is fresh and owns a separate TOMAC/AQ branch, this
slice did not start provider-status, IBKR historical, AutoQuant, Freqtrade,
TOMAC, local backtest, paper/sim/live, Pre-Bayes, BBN, path-ranker, execution
tree, feedback/update, or policy lifecycle work.

## Branch

`US_ETF -> SingaporeSingleCountryETF -> iShares MSCI Singapore ETF / EWS -> ETH/full_retained_session -> 1m execution + shifted 5m/15m/30m/1h/4h/1d context -> MASPolicyflowAndBankingBeta -> SGDAsiaRiskTransfer -> USSessionLiquidityFlushVwapReclaim -> AtrRiskManagedMtfContinuation -> ews_eth_singapore_etf_policyflow_vwap_reclaim_v1`

This is distinct from the active TOMAC Aroon/CCI branch, MGC/NQ lanes, prior
EWW/MXN packets, 6J/JPY, FESX/FDAX, KRE/XLF, INDA/EPI, uranium, and solar lanes.

## Source Readback

- Correct iShares product page `https://www.ishares.com/us/products/239678/ishares-msci-singapore-etf` returned HTTP `200` and exposed title `iShares MSCI Singapore ETF | EWS`, `adobe_ticker='ews'`, and `productTicker='ews'`.
- The product-id scan around neighboring iShares country ETFs found nearby tickers such as EWW, ENZL, EPP, EPOL, EZA, EWD, EWT, THD, EWU, and SUSA; only `239678` identified EWS/Singapore.
- IBKR stocks/ETFs commission page returned HTTP `200`, but this packet does not parse or rate-verify the exact account/pricing/routing/regulatory tuple.
- SEC fee page fetch returned HTTP `403` from this host.
- FINRA rule URL fetch returned HTTP `404` from this host.

## Cost And Promotion Decision

Cost status is `cost_model_unverified`. The packet does not prove exact IBKR
contract mapping, account region, pricing plan, routing/venue, SEC/FINRA fee
treatment, exchange/local fees, borrow/financing, spread/slippage, or
fee-effective date. It also does not prove retained-session provider rows outside
the NYSE/Nasdaq regular session window.

Therefore `promotion_allowed=false`, `trade_usable=false`, and
`update_goal=false` remain mandatory.

## Deferred Gate Plan

Only after compact audit and focused process scan are clear:

1. Create a fresh launch claim for this exact EWS branch.
2. Resolve the IBKR contract as US ETF/STK with exact primary exchange/routing
   and account pricing plan.
3. Fetch verified retained-session rows for `1m` origin plus
   `5m/15m/30m/1h/4h/1d` context without an RTH-only filter.
4. Prove retained rows outside `09:30-16:00 America/New_York` before any ETH
   promotion discussion.
5. Run Gate 1 and downstream lifecycle only if the exact cost model is verified
   and no collision guard blocks launch.

## Evidence

- `/tmp` workdoc: `/tmp/ict-engine-ews-eth-singapore-etf-policyflow-vwap-reclaim-reserve-20260530T065819+0800/workdoc.md`
- Claim: `/tmp/ict-engine-agent-claims/board-b-factor-refinement/20260530T065819+0800-codex-ews-eth-singapore-etf-policyflow-vwap-reclaim-reserve.claim`
- Source/cost readback JSON: `support/docs/experiments/actionable-regime-confidence/runs/20260530T065819+0800-codex-ews-eth-singapore-etf-policyflow-vwap-reclaim-reserve-v1/checks/source_cost_readback_20260530T065819+0800.json`
- Terminal summary: `support/docs/experiments/actionable-regime-confidence/runs/20260530T065819+0800-codex-ews-eth-singapore-etf-policyflow-vwap-reclaim-reserve-v1/summaries/terminal_summary.json`
