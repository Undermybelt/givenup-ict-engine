# OTE Branch Continuation Contract v1

Run root:
`docs/experiments/actionable-regime-confidence/runs/20260512T155014+0800-codex-board-b-ote-branch-continuation-contract-v1`

Source seed:
`docs/experiments/actionable-regime-confidence/runs/20260512T150855+0800-codex-145809-aq-material-seed-dispatch-v1`

Purpose: preserve the user's OTE continuation-pullback idea as a Board B profitability-factor branch packet without mixing it into Board A market-state or regime-confidence work.

## Branch Leaves

- `ote_050` / `0.500`: `TrendExpansion -> NormalVolatility -> OTERetracement050 -> OTEContinuationLong`, IBKR seed trades `76`, pnl_ratio_sum `0.00951618`
- `ote_0618` / `0.618`: `TrendExpansion -> NormalVolatility -> OTERetracement0618 -> OTEContinuationLong`, IBKR seed trades `27`, pnl_ratio_sum `0.03758052`
- `ote_0705` / `0.705`: `TrendExpansion -> NormalVolatility -> OTERetracement0705 -> OTEContinuationLong`, IBKR seed trades `27`, pnl_ratio_sum `0.01995716`
- `ote_0786` / `0.786`: `TrendExpansion -> NormalVolatility -> OTERetracement0786 -> OTEContinuationLong`, IBKR seed trades `32`, pnl_ratio_sum `-0.00441210`

## Provider Authority Readback

- `IBKR`: requested=`True`, aq_invoked=`True`, acquired=`True`, unreachable=`False`, status=`completed_positive_seed`
- `TradingViewRemix/TVR`: requested=`True`, aq_invoked=`False`, acquired=`False`, unreachable=`True`, status=`provider_unreachable_current_rate_limited`
- `yfinance/YF`: requested=`True`, aq_invoked=`True`, acquired=`True`, unreachable=`False`, status=`completed_negative`
- `Kraken`: requested=`True`, aq_invoked=`True`, acquired=`True`, unreachable=`False`, status=`aq_job_failed`
- `Binance`: requested=`True`, aq_invoked=`True`, acquired=`True`, unreachable=`False`, status=`completed_zero_trades`
- `Bybit`: requested=`True`, aq_invoked=`True`, acquired=`True`, unreachable=`False`, status=`aq_job_failed`

## Gate

- `support_once:155014_ote_branch_continuation_contract_v1`.
- `evidence_class:ote_profitability_branch_contract_with_current_provider_blocker`.
- `pass:ote_levels_050_0618_0705_0786_encoded`.
- `pass:branch_paths_explicit`.
- `pass:ibkr_spy_positive_seed_162_trades`.
- `partial:yfinance_es_completed_negative`.
- `partial:binance_completed_zero_trades`.
- `fail_closed:kraken_xbtusd_no_data_found_in_seed`.
- `fail_closed:bybit_btcusdt_no_data_found_in_seed`.
- `fail_closed:tvr_current_rate_limited`.
- `fail_closed:not_six_provider_aq_authority`.
- `fail_closed:no_new_aq_dispatch_due_active_heavy_process_and_tvr_blocker`.
- `promotion_allowed=false`.
- `trade_usable=false`.
- `update_goal=false`.

## Next

Keep OTE as a Board B branch nursery factor, with four leaves under `TrendExpansion -> NormalVolatility`. The next valid continuation should wait for TVR recovery or another explicitly healthy TVR route, then rerun a new same-root six-provider OTE packet before any downstream handoff probes.
