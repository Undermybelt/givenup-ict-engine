# R6 Owner Export Current Send-Channel Preflight v1

- Gate result: `r6_owner_export_current_send_channel_preflight_v1=current_send_channels_confirmed_no_request_sent_no_controls_acquired`.
- Current official web route lookup performed: `true`.
- Owner/vendor request submitted: `false`; ticket/export identifier received: `false`.
- Source-owned normal controls acquired: `0`; FLIP-as-control approved: `false`.
- This refresh confirms send channels only. It does not replace the v3 sendable request drafts and does not authorize owner-root population.

## Current Send Channels
- `CME Group` / `DataMine historical data`: `not_sent_needs_owner_or_operator_submission`; https://www.cmegroup.com/market-data/datamine-historical-data/index.html
- `CME Group` / `Market Depth Files FAQ`: `not_sent_supporting_reference_only`; https://www.cmegroup.com/market-data/files/cme-group-market-depth-faq.pdf
- `Cboe/CFE` / `Cboe U.S. Futures historical data`: `not_sent_needs_owner_or_operator_submission`; https://www.cboe.com/markets/us/futures/market-statistics/historical-data/oof/
- `Cboe/CFE` / `Cboe Market Data Services U.S. Futures`: `not_sent_supporting_reference_only`; https://res.cboe.com/market_data_services/us/futures/
- `Cboe/CFE` / `Cboe DataShop CFE futures trades`: `not_sent_needs_owner_or_operator_submission`; https://datashop.cboe.com/cfe-futures-trades

## Root Readback
- Source-label equivalence root ready: `true`.
- R6 owner-export root ready: `false`.
- R3 native-subhour root ready: `false`.
- R5 recency-extension root ready: `false`.

## Promotion Status
- Accepted rows added: `0`; new confidence gate: false; canonical merge allowed: false; downstream chain rerun allowed: false.
- Runtime code changed: false. Shared intake mutated: false. R3/R5/R6 roots mutated: false. Thresholds relaxed: false. Raw data committed: false. External contact submitted: false. Trade usable: false.

Artifacts:
- JSON: `docs/experiments/actionable-regime-confidence/runs/20260512T014300-codex-r6-owner-export-current-send-channel-preflight-v1/r6-owner-export-current-send-channel-preflight-v1/r6_owner_export_current_send_channel_preflight_v1.json`
- Send-channel CSV: `docs/experiments/actionable-regime-confidence/runs/20260512T014300-codex-r6-owner-export-current-send-channel-preflight-v1/r6-owner-export-current-send-channel-preflight-v1/r6_owner_export_current_send_channels_v1.csv`
- Tmp-root CSV: `docs/experiments/actionable-regime-confidence/runs/20260512T014300-codex-r6-owner-export-current-send-channel-preflight-v1/r6-owner-export-current-send-channel-preflight-v1/r6_owner_export_current_tmp_roots_v1.csv`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260512T014300-codex-r6-owner-export-current-send-channel-preflight-v1/checks/r6_owner_export_current_send_channel_preflight_v1_assertions.out`

Next:
- Submit the CME and Cboe/CFE request drafts through an owner/operator account, or record explicit FLIP-as-control approval. Only after ticket/export identifiers and verifier-native rows arrive should `/tmp/ict-engine-board-a-r6-owner-export-v1` be populated and the full chain rerun.
