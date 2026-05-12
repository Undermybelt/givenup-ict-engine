# Board A v2 Provider Agreement Calibration

Loop ID: `20260510T183512+0800-board-a-v2-provider-agreement-calibration-codex`

Result: `abstain_no_calibrated_release_rule`. No 95% or 99% Board A regime packet was emitted.

Key artifacts:
- `evidence_packet.json`
- `provider/provider_status_codex.json`
- `provider-agreement-v2/provider_agreement_v2_probe_report.json`
- `downstream-readback/pre_bayes_status_qqq.json`
- `downstream-readback/policy_training_status_qqq.json`
- `downstream-readback/workflow_status_qqq.json`
- `downstream-readback/execution_tree_trace_qqq.json`

Provider coverage:
- yfinance: QQQ 1h and NQ 15m CSV artifacts.
- IBKR: QQQ 1h CSV artifact.
- Kraken: PF_XBTUSD 15m CSV artifact.
- TradingViewRemix: status/fetch artifacts copied into this packet; live provider-status marks TradingView MCP connectivity unhealthy for this loop.
- Auto-Quant: local NQ feather cache was used for 15m/1h/4h/1d features.

Calibration readback:
- Board-eligible QQQ/NQ provider-agreement lane: best CatBoost-isotonic candidate was `target_release_long_h4`, test support `94`, test Wilson LCB `0.6032278520902813`, ECE `0.0771029471253517`, accepted `false`.
- NQ Auto-Quant multi-timeframe sidecar: test Wilson LCB `0.9704930122116464`, ECE `0.008790719375636136`, but board-ineligible as a single-cache sidecar and coverage `0.01785388959737657` is below the board threshold.

Downstream readback:
- Pre-Bayes gate: `pass_neutralized`, soft evidence present.
- BBN/policy surface: read through `pre_bayes_status_qqq.json`.
- CatBoost: v2 probe used CatBoost-isotonic calibration; policy-training status reports CatBoost external score runtime in the structural path-ranker surface.
- Execution tree: latest trace remains `observe / transition_guardrail / guarded`; Board B remains blocked because no accepted Board A packet exists.
