# Provider Readiness Source-Label Gap Readback v1

Run ID: `20260511T195935-codex-provider-readiness-source-label-gap-readback-v1`

- Gate result: `provider_readiness_source_label_gap_readback_v1=providers_checked_source_labels_still_blocked`
- Provider compact status: `entry_model:2/2 ready | live_runtime:1/3 ready | local_runtime:1/2 ready | market_data:2/7 ready`
- yfinance: ready.
- TradingView MCP: ready.
- IBKR: configured runtime unhealthy; gateway reachable but runtime dependencies missing.
- Kraken public: configured runtime unhealthy; Python provider dependencies missing.
- Source-label gap remains: strict exact-target ready sources `0`, native sub-hour ready sources `0`, exact intake filename hits `0`.
- Accepted rows added: `0`; new confidence gate: `false`.
- Strict full objective achieved: `false`; `update_goal=false`.
- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; trade usable: `false`.

## Artifacts

- JSON: `/Users/thrill3r/projects-ict-engine/ict-engine/docs/experiments/actionable-regime-confidence/runs/20260511T195935-codex-provider-readiness-source-label-gap-readback-v1/provider-readiness-source-label-gap/provider_readiness_source_label_gap_readback_v1.json`
- Command CSV: `/Users/thrill3r/projects-ict-engine/ict-engine/docs/experiments/actionable-regime-confidence/runs/20260511T195935-codex-provider-readiness-source-label-gap-readback-v1/provider-readiness-source-label-gap/provider_readiness_source_label_gap_readback_v1_commands.csv`
- Assertions: `/Users/thrill3r/projects-ict-engine/ict-engine/docs/experiments/actionable-regime-confidence/runs/20260511T195935-codex-provider-readiness-source-label-gap-readback-v1/checks/provider_readiness_source_label_gap_readback_v1_assertions.out`
