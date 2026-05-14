# OTE Same-Root Provider/AQ Packet Terminal Readback v1

Run root:
`docs/experiments/actionable-regime-confidence/runs/20260512T160734+0800-codex-ote-same-root-provider-aq-packet-v1`

Board B active claim:
`160734_ote_same_root_provider_aq_packet_v1`

Purpose: close the active Board B OTE provider/AQ packet without mixing this profitability-factor work into Board A market-state or regime-confidence acceptance.

## Branch Contract

Canonical profitability branches:

- `TrendExpansion -> NormalVolatility -> OTERetracement050 -> OTEContinuationLong`
- `TrendExpansion -> NormalVolatility -> OTERetracement0618 -> OTEContinuationLong`
- `TrendExpansion -> NormalVolatility -> OTERetracement0705 -> OTEContinuationLong`
- `TrendExpansion -> NormalVolatility -> OTERetracement0786 -> OTEContinuationLong`

The four OTE leaves remain useful Board B branch candidates. If the exact two upper OTE levels are corrected later, replace `0.705` / `0.786` in a new branch-contract root rather than rewriting this evidence.

## Provider And AQ Readback

Provider/material preparation:

- `IBKR`: acquired `1424` SPY 1h rows, `2026-01-02 09:00:00` to `2026-05-11 23:00:00`, AQ material created.
- `TradingViewRemix/TVR`: requested but unreachable from existing root `154536`; no new TVR request was made here.
- `yfinance/YF`: acquired `428` SPY 1h rows, `2026-02-12 14:30:00` to `2026-05-11 20:00:00`, AQ material created.
- `Kraken`: acquired `2000` PF_XBTUSD 1h rows, `2026-02-12 00:00:00` to `2026-05-06 07:00:00`, AQ material created.
- `Binance`: acquired `2137` BTCUSDT 1h rows, `2026-02-12 00:00:00` to `2026-05-12 00:00:00`, AQ material created.
- `Bybit`: acquired `1000` BTCUSDT linear 1h rows, `2026-03-31 09:00:00` to `2026-05-12 00:00:00`, AQ material created.

Command evidence:

- `00_prepare_ote_same_root_provider_aq_packet.exit=0`
- `06b_agent_material_batch_after_wrapper_fix.exit=0`
- `07b_repair_csv_headers.exit=0`
- `09b_repair_csv_timestamps.exit=0`
- `11b_set_material_timerange.exit=0`
- `12_agent_material_batch_after_timerange_repair.exit=0`
- `13_agent_material_dispatch_after_timerange_repair.exit=0`
- `14_agent_material_rank_after_timerange_repair.exit=0`

Final dispatch artifact:
`auto-quant-agent-material-dispatch:PROVIDER_OTE_160734:20260512T083428.378Z`

Final rank artifact:
`auto-quant-agent-material-rank:PROVIDER_OTE_160734:20260512T084257.774Z`

## Final AQ Metrics

- `yfinance/YF SPY 1h`: completed, `0` trades, `0.0%` total profit, win rate `0.0%`, profit factor `0.0`.
- `Binance BTCUSDT 1h`: completed, `0` trades, `0.0%` total profit, win rate `0.0%`, profit factor `0.0`.
- `Bybit BTCUSDT linear 1h`: completed, `0` trades, `0.0%` total profit, win rate `0.0%`, profit factor `0.0`.
- `Kraken PF_XBTUSD 1h`: completed, `0` trades, `0.0%` total profit, win rate `0.0%`, profit factor `0.0`.
- `IBKR SPY 1h`: completed, `14` trades, `-0.92%` total profit, win rate `21.4286%`, profit factor `0.5474`, Sharpe `-0.598`.

## Verdict

Evidence class:
`ote_same_root_provider_aq_packet_fail_closed`

This root closes the active OTE packet as a real provider/AQ execution, not as support. It does not satisfy same-root six-provider authority because TVR remained unreachable. It does not satisfy profitability because four completed non-TVR providers produced zero trades and IBKR produced a small negative sample. It does not satisfy sample adequacy because the only nonzero trade count is `14`.

No Pre-Bayes/filter, BBN, CatBoost/path-ranker, or execution-tree admission should be run from this packet as a promotion chain. Future OTE continuation should preserve the four OTE leaves as Board B branch candidates, repair the provider/AQ material path under a fresh visible claim, maximize provider-backed window size, and only then attempt downstream handoff probes.

## Gate

- `active_claim_closed:160734_ote_same_root_provider_aq_packet_v1`.
- `support_once:160734_ote_same_root_provider_aq_packet_v1`.
- `evidence_class:ote_same_root_provider_aq_packet_fail_closed`.
- `pass:provider_rows_6_emitted`.
- `pass:current_provider_data_acquired_yf_binance_bybit_kraken_ibkr`.
- `pass:agent_material_batch_exit0_after_repairs`.
- `pass:agent_material_dispatch_exit0_after_timerange_repair`.
- `pass:agent_material_rank_exit0_after_timerange_repair`.
- `pass:five_non_tvr_aq_jobs_completed`.
- `fail_closed:tvr_rate_limited_unreachable_from_154536`.
- `fail_closed:not_same_root_six_provider_aq_authority`.
- `fail_closed:yf_binance_bybit_kraken_zero_trades`.
- `fail_closed:ibkr_spy_negative_profit_factor_0_5474_trades_14`.
- `fail_closed:sample_adequacy_smoke_only`.
- `fail_closed:no_prebayes_bbn_catboost_execution_tree_promotion_chain`.
- `promotion_allowed=false`.
- `trade_usable=false`.
- `update_goal=false`.

## Next

Keep OTE as a Board B profitability-factor branch nursery with four retracement leaves. The next OTE attempt should be a fresh visible claim or explicitly reassigned repair root, use a healthy TVR/local-stdio route where available, preserve same-root provider/AQ authority, and use larger provider-backed windows before any support or promotion claim.
