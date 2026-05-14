# Board A A-v2-2 Data-Binding Repair

Loop ID: `20260510T184555+0800-board-a-v2-2-autoquant-data-binding-repair-codex`

Result: partial progress, not an accepted Board A regime packet.

What changed in this run:
- Reproduced the prior Auto-Quant blocker from `20260510T183454`: the fresh runner used `QQQ/USD` at `15m`, but the data dir has no `QQQ_USD-15m.feather`.
- Ran an isolated patched copy with `NQ/USD` and the existing `NQ_USD-15m.feather`.
- Confirmed the fresh Freqtrade run now loads data and exits with zero runner errors.
- Probed TradingViewRemix `tools/list`; endpoint returned HTTP 429, so TV health remains blocked by rate limit.

Key artifacts:
- `evidence_packet_a_v2_2_data_binding_repair.json`
- `autoquant/config.tomac.nq-15m.json`
- `tmp-scripts/fresh_tomac_backtest_runner_nq.py`
- `autoquant/fresh_tomac_scratch_no_rsi_nq_2025.json`
- `autoquant/fresh_tomac_scratch_no_rsi_nq_2025_summary.json`
- `provider-tvremix-tools-list-health.json`

Fresh Auto-Quant readback:
- Strategy: `TomacNQ_ScratchNoRSINoConflict15m`
- Pair/timeframe: `NQ/USD` / `15m`
- Timerange: `20250101-20251231`
- Trades: `1081`
- Winrate: `0.3145235892691952`
- Profit total: `-0.10881613010630001`
- Profit factor: `0.9015821223976574`

Board A decision:
- Data binding is repaired.
- This fresh strategy is negative/no-edge and is not a profitability or regime-confidence acceptance.
- TradingViewRemix remains blocked by HTTP 429.
- Board B still receives no accepted regime packet.
