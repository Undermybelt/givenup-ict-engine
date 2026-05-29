# EWW ETH Mexico ETF Policyflow VWAP Reclaim Reserve

- agent_name: `codex-eww-eth-mexico-etf-policyflow-vwap-reclaim-reserve`
- created_at: `2026-05-30T06:46:21+0800`
- status: `terminalized_no_launch_source_cost_reserve_cost_model_unverified`
- factor_id: `eww_eth_mexico_etf_policyflow_vwap_reclaim_v1`
- instrument: `EWW` / iShares MSCI Mexico ETF
- session_scope: `ETH/full_retained_session`
- rth_filter_applied: `false`
- origin_timeframe: `1m`
- context_timeframes: `5m/15m/30m/1h/4h/1d`
- promotion_allowed: `false`
- trade_usable: `false`
- update_goal: `false`

## Objective

Create a distinct no-launch profitability-factor reserve packet for a US-listed
Mexico single-country ETF while Board B runtime is blocked by fresh active
claims. This packet preserves the rooted branch, source readbacks, known product
identity, and exact blockers. It is not provider-row evidence, Gate 1 evidence,
or practical promotion evidence.

## Current Blocker

Same-turn compact audit after the BZ prep commit reported:

- `status=needs_attention`
- `active_claims=2`
- fresh claims: `20260530T064134+0800-codex-nq-compound-rv-stress-lifecycle-exec.claim` and `20260530T064148+0800-codex-mgc-eth-asia-stoprun-vwap-compression-reclaim-full-ladder-training.claim`
- `live_factor_processes=0`
- `promotion_allowed_true=0`
- `trade_usable_true=0`
- `same_tree_practical_closure=null`

Because fresh active claims still block launches, this slice did not start
provider-status, IBKR historical, AutoQuant, Freqtrade, TOMAC, local backtest,
paper/sim/live, Pre-Bayes, BBN, path-ranker, execution tree, feedback/update, or
policy lifecycle work.

## Branch

`US_ETF -> MexicoSingleCountryETF -> iShares MSCI Mexico ETF / EWW -> ETH/full_retained_session -> 1m execution + shifted 5m/15m/30m/1h/4h/1d context -> BanxicoFiscalPolicyflow -> PesoEquityBetaRiskTransfer -> USSessionLiquidityFlushVwapReclaim -> AtrRiskManagedMtfContinuation -> eww_eth_mexico_etf_policyflow_vwap_reclaim_v1`

This is distinct from the existing MXN futures Banxico/remittance lane and does
not touch KRE/XLF, India ETF, uranium, solar, FESX/FDAX, 6J/JPY, MGC, NQ, or
TOMAC lanes.

## Source Readback

- Correct iShares product page `https://www.ishares.com/us/products/239670/ishares-msci-mexico-etf` returned HTTP `200` and exposed title `iShares MSCI Mexico ETF | EWW`, `adobe_ticker='eww'`, `productName='iShares MSCI Mexico ETF'`, and `productTicker='eww'`.
- The earlier guessed iShares URL with product id `239681` returned HTTP `200` but exposed `adobe_ticker='ewy'` and title `iShares MSCI South Korea ETF | EWY`; it was rejected as EWW evidence.
- IBKR stocks/ETFs commission page returned HTTP `200`, but this packet does not parse or rate-verify the exact account/pricing-plan fee tuple.
- SEC fee page fetch returned HTTP `403` from this host.
- FINRA rule URL fetch returned HTTP `404` from this host.

## Cost And Promotion Decision

Cost status is `cost_model_unverified`. The packet does not prove exact IBKR
account region, pricing plan, routing/venue, regulatory/TAF/SEC fee treatment,
exchange/local fee applicability, borrow/financing, spread/slippage, or
fee-effective date. It also does not prove retained-session provider rows outside
the NYSE/Nasdaq regular session window.

Therefore `promotion_allowed=false`, `trade_usable=false`, and
`update_goal=false` remain mandatory.

## Deferred Gate Plan

Only after compact audit and focused process scan are clear:

1. Create a fresh launch claim for this exact EWW branch.
2. Resolve the IBKR contract as US ETF/STK with exact primary exchange/routing
   and account pricing plan.
3. Fetch verified retained-session rows for `1m` origin plus
   `5m/15m/30m/1h/4h/1d` context without an RTH-only filter.
4. Prove retained rows outside `09:30-16:00 America/New_York` before any ETH
   promotion discussion.
5. Run Gate 1 and downstream lifecycle only if the exact cost model is verified
   and no collision guard blocks launch.

## Evidence

- `/tmp` workdoc: `/tmp/ict-engine-eww-eth-mexico-etf-policyflow-vwap-reclaim-reserve-20260530T064621+0800/workdoc.md`
- Claim: `/tmp/ict-engine-agent-claims/board-b-factor-refinement/20260530T064621+0800-codex-eww-eth-mexico-etf-policyflow-vwap-reclaim-reserve.claim`
- Source/cost readback JSON: `support/docs/experiments/actionable-regime-confidence/runs/20260530T064621+0800-codex-eww-eth-mexico-etf-policyflow-vwap-reclaim-reserve-v1/checks/source_cost_readback_20260530T064621+0800.json`
- Terminal summary: `support/docs/experiments/actionable-regime-confidence/runs/20260530T064621+0800-codex-eww-eth-mexico-etf-policyflow-vwap-reclaim-reserve-v1/summaries/terminal_summary.json`
