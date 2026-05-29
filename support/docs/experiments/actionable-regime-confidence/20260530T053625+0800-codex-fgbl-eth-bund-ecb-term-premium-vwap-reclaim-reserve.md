# 2026-05-30 FGBL Bund ECB Term-Premium VWAP Reclaim Reserve

## Status

- owner: `codex-fgbl-eth-bund-ecb-term-premium-vwap-reclaim-reserve`
- created_at: `2026-05-30T05:36:25+0800`
- repo_tracking_doc: `support/docs/experiments/actionable-regime-confidence/20260530T053625+0800-codex-fgbl-eth-bund-ecb-term-premium-vwap-reclaim-reserve.md`
- workdoc: `/tmp/ict-engine-fgbl-eth-bund-ecb-term-premium-vwap-reclaim-reserve-20260530T053625+0800/workdoc.md`
- claim: `/tmp/ict-engine-agent-claims/board-b-factor-refinement/20260530T053625+0800-codex-fgbl-eth-bund-ecb-term-premium-vwap-reclaim-reserve.claim`
- run_root: `/tmp/ict-engine-fgbl-eth-bund-ecb-term-premium-vwap-reclaim-reserve-20260530T053625+0800`
- compact_root: `support/docs/experiments/actionable-regime-confidence/runs/20260530T053625+0800-codex-fgbl-eth-bund-ecb-term-premium-vwap-reclaim-reserve-v1`
- terminal_summary: `support/docs/experiments/actionable-regime-confidence/runs/20260530T053625+0800-codex-fgbl-eth-bund-ecb-term-premium-vwap-reclaim-reserve-v1/summaries/terminal_summary.json`
- status: `terminalized_source_cost_reserve_no_launch_cost_unverified`
- promotion_allowed: `false`
- trade_usable: `false`
- update_goal: `false`

## Candidate Identity

- branch_path: `FUTURES -> European rates -> Eurex Euro-Bund / FGBL -> ETH/full_retained_session -> 1m execution + shifted 5m/15m/30m/1h/4h/1d context -> MainRegime: ECBRatePathTermPremiumShock -> SubRegime: BundDurationFlightOrRelief -> ProfitFactor: SessionVwapReclaimAfterYieldImpulse -> ProfitFactorOverlay: AtrRiskManagedMtfContinuation -> fgbl_eth_bund_ecb_term_premium_vwap_reclaim_v1`
- factor_id: `fgbl_eth_bund_ecb_term_premium_vwap_reclaim_v1`
- market: `futures`
- product: `Eurex Euro-Bund futures`
- root_symbol: `FGBL`
- session_scope: `ETH/full_retained_session`
- rth_filter_applied: `false`
- origin_timeframe: `1m`
- context_timeframes: `5m/15m/30m/1h/4h/1d`

## Runtime Boundary

This is a no-launch reserve packet created while compact audit reported fresh active Board B claims:

- `20260530T053015+0800-codex-zl-eth-soybean-oil-biofuel-crush-vwap-reclaim-reserve.claim`
- `20260530T053156+0800-codex-m2k-es-riskon-rotation-vwap-adx-preflight.claim`

No provider-status, provider fetch, IBKR historical, AutoQuant, Freqtrade, local backtest, paper/sim/live, lifecycle, Pre-Bayes, BBN, CatBoost, path-ranker, execution-tree, feedback/update, or policy-training command was launched for this FGBL packet.

## Source Readback

- Duplicate search found no exact FGBL/Bund claim, repo packet, or wrapper in the active claim set or `support/docs/experiments/actionable-regime-confidence/scripts`.
- Eurex `find?query=FGBL` returned HTTP 200 content and exposed `FGBL` plus the Eurex long-term interest-rates path. The guessed direct Euro-Bund product URL redirected to an error/nocontext URL and ended HTTP 404, so contract specs are not rate-verified from the direct product page.
- IBKR EMEA futures commissions page returned HTTP 200 and showed Germany/EUR-denominated futures commission tiers, including low-volume `EUR 0.90/contract` and higher-volume tiers down to `EUR 0.25/contract`.
- IBKR guessed Eurex fee pages did not return a usable FGBL exchange/clearing/regulatory fee row in this turn.

## Terminal Decision

The packet is useful only as a future source/cost reserve. Contract specs, exact IBKR broker-side contract mapping, exchange/clearing/regulatory fees, retained-session provider rows, MTF coverage, slippage, roll rule, Gate 1 economics, and lifecycle evidence remain unverified.

Therefore:

- `cost_model_status=cost_model_unverified`
- `provider_rows=0`
- `ibkr_historical_rows=0`
- `autoquant_started=false`
- `promotion_allowed=false`
- `trade_usable=false`
- `update_goal=false`
