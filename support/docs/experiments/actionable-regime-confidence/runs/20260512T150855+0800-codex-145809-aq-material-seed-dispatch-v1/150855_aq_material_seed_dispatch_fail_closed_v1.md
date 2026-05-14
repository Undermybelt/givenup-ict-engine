# 150855 AQ Material Seed Dispatch Fail-Closed v1

Run root:
`docs/experiments/actionable-regime-confidence/runs/20260512T150855+0800-codex-145809-aq-material-seed-dispatch-v1`

Source:
- Upstream selection surface: `20260512T145809+0800-codex-provider-backed-high-density-factor-screen-v1`.
- Candidate family: `ProviderOteTrendRetracementV1`.
- Branch intent: `TrendExpansion -> NormalVolatility -> OTERetracementLevel -> OTEContinuationLong`.
- This root dispatches AQ agent-material units for five provider contexts: Binance BTCUSDT 1h, IBKR SPY 1h, Yahoo/YF ES 1h, Kraken XBTUSD 1h, and Bybit BTCUSDT 1h.
- TradingViewRemix/TVR is absent from this root.

Command exits:
- `01_auto_quant_agent_material_batch.exit=0`
- `02_auto_quant_agent_material_dispatch.exit=0`
- `03_auto_quant_agent_material_rank.exit=0`

Provider material line counts:
- Binance BTCUSDT 1h CSV: `76430` lines.
- Bybit BTCUSDT 1h CSV: `1001` lines.
- IBKR SPY 1h CSV: `20035` lines.
- Kraken XBTUSD 1h CSV: `2001` lines.
- Yahoo/YF ES 1h CSV: `11384` lines.

AQ dispatch readback:
- Total AQ material jobs: `5`.
- Completed jobs: `3`.
- Failed jobs: `2`.
- Blocked jobs: `0`.
- Binance BTCUSDT 1h completed with `0` trades, win rate `0.0`, total profit `0.0%`, Sharpe `0.0`, and profit factor `0.0`.
- IBKR SPY 1h completed with `162` trades, win rate `34.5679%`, total profit `5.96%`, Sharpe `0.2471`, and profit factor `1.2609`.
- Yahoo/YF ES 1h completed with `103` trades, win rate `30.0971%`, total profit `-0.84%`, Sharpe `-0.0873`, and profit factor `0.927`.
- Kraken XBTUSD 1h failed with `OperationalException: No data found. Terminating.`
- Bybit BTCUSDT 1h failed with `OperationalException: No data found. Terminating.`

Acceptance decision:
- This is provider-backed AQ material dispatch evidence, not Board A acceptance.
- It does not satisfy same-root six-provider AQ/provider authority because TVR is absent and two of the five dispatched provider jobs failed.
- It does not run filter/Pre-Bayes, BBN, CatBoost/path-ranker, calibrated path lower-bound validation, or execution-tree admission.
- The best completed AQ unit, IBKR SPY 1h, is only a positive seed: win rate `34.5679%` and Sharpe `0.2471` are not regime-confidence evidence and are not sufficient for Board A promotion.
- Board A remains fail-closed: accepted `>=95%` contexts `0`, `promotion_allowed=false`, `trade_usable=false`, and `update_goal=false`.
