# 172142 OB/FVG Timerange Repair AQ Rerun Terminal Readback

Run root: `docs/experiments/actionable-regime-confidence/runs/20260512T165122+0800-codex-ob-fvg-branch-matrix-six-provider-aq-v1/`

Scope: close `active_claim:172142_165122_ob_fvg_timerange_repair_aq_rerun_v1` only. This is not a support count, not a promotion, and not downstream Pre-Bayes/BBN/CatBoost/execution-tree evidence.

## Evidence

- `10_py_compile_timerange_repair.exit=0`
- `11_set_material_timerange.exit=0`
- `checks/material_timerange_assertions.out`: `materials_seen_6=6`, `timerange_updated_6=6`, `timerange=20260101-20260512`
- `12_auto_quant_agent_material_batch_after_timerange_repair.exit=1`; superseded because the shell invocation included an empty first material argument
- `12b_auto_quant_agent_material_batch_after_timerange_repair.exit=0`
- `13b_auto_quant_agent_material_dispatch_after_timerange_repair.exit=0`
- `14b_auto_quant_agent_material_rank_after_timerange_repair.exit=0`

Latest artifacts:
- Batch: `state/auto-quant/PROVIDER_OB_FVG_165122/auto_quant_agent_material_batch.20260512T092844.510Z.json`
- Dispatch: `state/auto-quant/PROVIDER_OB_FVG_165122/auto_quant_agent_material_dispatch.20260512T092905.117Z.json`
- Rank: `state/auto-quant/PROVIDER_OB_FVG_165122/auto_quant_agent_material_rank.20260512T092907.246Z.json`

## AQ Readback

Dispatch totals: `total_jobs=6`, `completed_jobs=6`, `blocked_jobs=0`, `failed_jobs=0`.

Rank:
- yfinance/YF SPY 1h: `trade_count=9`, `win_rate_pct=44.4444`, `sharpe=0.5564`, `total_profit_pct=2.54`, `profit_factor=3.4267`
- IBKR SPY 1h: `trade_count=43`, `win_rate_pct=27.907`, `sharpe=-2.4024`, `total_profit_pct=-6.38`, `profit_factor=0.4018`
- Binance BTCUSDT 1h: `trade_count=0`
- Bybit BTCUSDT 1h: `trade_count=0`
- Kraken XBTUSD 1h: `trade_count=0`
- TVR BTC-USD 1h: `trade_count=0`

## Gate

- `active_claim_closed:172142_165122_ob_fvg_timerange_repair_aq_rerun_v1`
- `fail_closed:thin_positive_yfinance_trade_count9`
- `fail_closed:negative_ibkr_trade_count43`
- `fail_closed:four_zero_trade_provider_units`
- `fail_closed:no_downstream_prebayes_bbn_catboost_execution_tree`
- `promotion_allowed=false`
- `trade_usable=false`
- `update_goal=false`
