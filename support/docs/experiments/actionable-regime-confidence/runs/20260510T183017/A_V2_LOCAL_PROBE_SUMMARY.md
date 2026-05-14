# Board A A-v2 local probe summary

Loop ID: `20260510T183017+0800-board-a-v2-provider-agreement-calibration-local-probe`

Artifacts:
- Evidence packet: `evidence_packet_v2_local_probe.json`
- QQQ labels: `labels/provider_agreement_trend_expansion_labels_v2_local_probe.csv`
- NQ labels: `labels/nq_provider_disagreement_transition_guardrail_labels_v2_local_probe.csv`
- Calibration: `calibration/provider_agreement_calibration_v2_local_probe.json`
- CatBoost probe: `catboost/provider_agreement_catboost_probe_v2_local_probe.json`
- Consumer bundle: `regime_consumer_bundle_v2_local_probe.json`

Result: `abstain_no_calibrated_release_rule`.

Support:
- QQQ label rows: 43
- Chronological usable rows: 35
- Calibration rows: 9
- Test rows: 9
- Deterministic rule test support: 3
- CatBoost status: `skipped_catboost_support_or_class_gap`

Provider status:
- yfinance QQQ 1h rows: 43
- yfinance NQ 15m rows: 519
- IBKR QQQ 1h rows: 160
- Kraken PF_XBTUSD 15m rows: 865
- TradingViewRemix: current provider-status reports `tradingview_mcp_connectivity_probe_failed`.

Next action: A-v2-2: extend QQQ/NQ chronological support with longer yfinance+IBKR same-market windows and restore TradingViewRemix health before rerunning provider-agreement calibration.
