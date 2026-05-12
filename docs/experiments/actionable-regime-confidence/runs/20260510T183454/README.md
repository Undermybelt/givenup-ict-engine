# Board A Run 20260510T183454

Purpose: A-v2-1 provider-agreement / transition-guardrail calibration loop.

Key result: abstain. No leak-safe chronological provider-aware or forward-payoff probe produced an accepted 95% actionable release rule.

Important evidence:

- Provider status: `provider/provider-status-agent.json`, `provider/provider-status-market-data.json`
- yfinance QQQ 1h: `provider/yf_QQQ_1h_20240601_20260509.csv` (3369 rows)
- IBKR QQQ 1h: `provider/ibkr_QQQ_1h.csv` (4007 rows)
- Kraken PF_XBTUSD 1h: `provider/kraken_PF_XBTUSD_1h_2024_2025.csv` (2000 rows)
- TradingViewRemix current attempt: `provider/tv_qqq_harness.json` (failed; durable prior success remains in previous run)
- Auto-Quant tmp strategy probe: `autoquant/fresh_tomac_scratch_no_rsi_2025.json` (strategy found, fresh runner blocked by no data)
- Provider-aware CatBoost calibration: `calibration/catboost-regime-provider-aware-binary-fast-20k.json` (pass_count=0)
- Forward-payoff calibration: `calibration/forward-payoff-confidence-probe-20k.json` (pass_count=0)
- ict-engine analyze-live: `ict-engine/analyze-live-nq-yfinance-agent.json`
- BBN prior dry-run: `ict-engine/auto-quant-prior-init-qqq-dry-run.json`
- Execution-tree 512 readback copy: `ict-engine/legacy_entry_scan_512_summary.json`

Decision: `abstain_no_calibrated_release_rule`; thresholds were not relaxed.
