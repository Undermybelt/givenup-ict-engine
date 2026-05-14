# R6 Candidate Consolidation and Missing Intake Readback v1

Run id: `20260511T234659-codex-r6-candidate-consolidation-intake-missing-v1`
Generated at UTC: `2026-05-11T15:49:06.203514+00:00`

## Result

- Canonical live intake exists now: `False`.
- Direct verifier blocked on missing files: `True`.
- V54 baseline positives/controls: `57/57`.
- Sarao proposed positives: `6`; Nowak/Smith proposed positives: `6`.
- Proposed positives without matched controls: `12`.
- What-if positives after both sidecars: `69`.
- What-if min Wilson95 LCB after both sidecars: `0.947260905856`.
- Additional all-correct positives still needed after both sidecars: `4`.
- Gate result: `r6_candidate_consolidation_intake_missing_v1=canonical_intake_missing_sidecar_positives_unaccepted_confidence_still_blocked`.
- Strict full objective achieved: `False`; `update_goal=False`.

## Provider And Chain Readback

- Provider focus: `{"ibkr@market_data": {"ready": false, "reason": "ibkr_runtime_dependencies_missing_with_gateway_reachable", "status": "configured_runtime_unhealthy"}, "ibkr_bridge@local_runtime": {"ready": false, "reason": "ibkr_bridge_runtime_dependencies_missing_with_gateway_reachable", "status": "configured_runtime_unhealthy"}, "kraken_cli@local_runtime": {"ready": true, "reason": "kraken_cli_config_detected", "status": "ready"}, "kraken_public@market_data": {"ready": false, "reason": "python3_provider_dependencies_missing", "status": "configured_runtime_unhealthy"}, "tradingview_mcp@market_data": {"ready": false, "reason": "tradingview_mcp_connectivity_probe_failed", "status": "configured_runtime_unhealthy"}, "yfinance@live_runtime": {"ready": true, "reason": "native_yfinance_runtime_available", "status": "ready"}, "yfinance@market_data": {"ready": true, "reason": "public_yahoo_http_endpoints", "status": "ready"}}`.
- Command outputs are under `command-output/`: provider status, Auto-Quant status, demo analyze, pre-Bayes, policy-training/CatBoost surface, workflow-status, and structural path-ranking export.

## Fail-Closed Decision

- No shared intake mutation was made because the canonical `/tmp` intake root is absent in this fresh readback.
- The two candidate sidecars remain proposed positives only; they do not include matched controls.
- Even treating all proposed positives as correct, pooled confidence remains below `0.95` before split support is considered.
