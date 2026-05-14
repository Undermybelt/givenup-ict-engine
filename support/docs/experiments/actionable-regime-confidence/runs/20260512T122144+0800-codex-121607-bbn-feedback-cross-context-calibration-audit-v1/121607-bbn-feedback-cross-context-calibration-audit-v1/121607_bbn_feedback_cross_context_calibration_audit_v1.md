# 121607 BBN Feedback Cross-Context Calibration Audit v1

Run id: `20260512T122144+0800-codex-121607-bbn-feedback-cross-context-calibration-audit-v1`
Source feedback packet: `docs/experiments/actionable-regime-confidence/runs/20260512T121607+0800-codex-120630-bbn-negative-feedback-packet-v1/120630-bbn-negative-feedback-packet-v1/120630_bbn_negative_feedback_packet_v1.json`
Source enriched rows: `docs/experiments/actionable-regime-confidence/runs/20260512T121347+0800-codex-115700-enriched-downstream-chain-v1/derived/same_root_six_provider_1h_aq_real_trades.enriched_layer_contract.jsonl`

## Result
- Rows audited: `237`.
- Providers present: `6/6` (binance_public, bybit_public, ibkr_paxos_long_midpoint, kraken_public, tvr_default_binance, yfinance).
- Instruments present: `BTC`.
- Timeframes present: `1h`.
- Visible branch/regime paths: `2`.
- Max BBN probability: `0.747688`; max Pre-Bayes confidence: `0.525086`.
- Accepted branch/regime paths at 95%: `0/2`.
- Execution ready/actionable/promotional rows: `0/0/0`.
- Gate: `fail_closed:confidence_below_95,single_instrument_only,single_timeframe_only,chronological_buckets_below_95,execution_not_admissible,not_every_visible_regime_at_95`.

## Decision
- The exact `115700 -> 120630 -> 121607` packet is valid hard-negative candidate evidence, but it does not satisfy Board A acceptance.
- Provider coverage is present across the six required lanes, but market/instrument coverage is still BTC-only and timeframe coverage is still 1h-only.
- No visible branch/regime path reaches 95% confidence, chronological buckets remain below 95%, and execution remains observe/blocked.
- `promotion_allowed=false`.
- `trade_usable=false`.
- `update_goal=false`.

## Artifacts
- JSON: `docs/experiments/actionable-regime-confidence/runs/20260512T122144+0800-codex-121607-bbn-feedback-cross-context-calibration-audit-v1/121607-bbn-feedback-cross-context-calibration-audit-v1/121607_bbn_feedback_cross_context_calibration_audit_v1.json`
- Checklist: `docs/experiments/actionable-regime-confidence/runs/20260512T122144+0800-codex-121607-bbn-feedback-cross-context-calibration-audit-v1/121607-bbn-feedback-cross-context-calibration-audit-v1/prompt_to_artifact_checklist_121607_bbn_feedback_cross_context_calibration_audit_v1.csv`
- Chronological buckets: `docs/experiments/actionable-regime-confidence/runs/20260512T122144+0800-codex-121607-bbn-feedback-cross-context-calibration-audit-v1/121607-bbn-feedback-cross-context-calibration-audit-v1/chronological_buckets_121607_bbn_feedback_cross_context_calibration_audit_v1.csv`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260512T122144+0800-codex-121607-bbn-feedback-cross-context-calibration-audit-v1/checks/121607_bbn_feedback_cross_context_calibration_audit_v1_assertions.out`
