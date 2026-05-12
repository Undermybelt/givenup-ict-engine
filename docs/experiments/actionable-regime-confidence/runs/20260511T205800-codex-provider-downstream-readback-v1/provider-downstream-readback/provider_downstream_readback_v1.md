# Provider Downstream Readback v1

- Decision: `provider_downstream_readback_v1=live_status_recorded_strict_source_rows_still_blocked`
- State dir: `/tmp/ict-engine-board-a-provider-downstream-readback-v1`
- Auto-Quant state dir: `/tmp/ict-engine-board-a-autoquant-status-v1`
- yfinance live chain started: `true`
- Accepted rows added: `0`; new confidence gate: `false`.
- Strict full objective achieved: `false`; `update_goal=false`.
- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; trade usable: `false`.

## Providers

| Provider | Ready | Domains | Status | Reason |
|---|---:|---|---|---|
| `ibkr` | `false` | `market_data` | `configured_runtime_unhealthy` | `ibkr_runtime_dependencies_missing_with_gateway_reachable` |
| `tradingview_mcp` | `false` | `market_data` | `configured_runtime_unhealthy` | `tradingview_mcp_connectivity_probe_failed` |
| `yfinance` | `true` | `live_runtime;market_data` | `ready` | `native_yfinance_runtime_available;public_yahoo_http_endpoints` |
| `kraken_public` | `false` | `market_data` | `configured_runtime_unhealthy` | `python3_provider_dependencies_missing` |
| `kraken_cli` | `true` | `local_runtime` | `ready` | `kraken_cli_config_detected` |

## Downstream Commands

| Command | Exit | Output | Error |
|---|---:|---|---|
| `provider_status_agent` | `0` | `docs/experiments/actionable-regime-confidence/runs/20260511T205800-codex-provider-downstream-readback-v1/command-output/provider_status_agent.out` | `docs/experiments/actionable-regime-confidence/runs/20260511T205800-codex-provider-downstream-readback-v1/command-output/provider_status_agent.err` |
| `provider_status_ibkr_agent` | `0` | `docs/experiments/actionable-regime-confidence/runs/20260511T205800-codex-provider-downstream-readback-v1/command-output/provider_status_ibkr_agent.out` | `docs/experiments/actionable-regime-confidence/runs/20260511T205800-codex-provider-downstream-readback-v1/command-output/provider_status_ibkr_agent.err` |
| `provider_status_tradingview_mcp_agent` | `0` | `docs/experiments/actionable-regime-confidence/runs/20260511T205800-codex-provider-downstream-readback-v1/command-output/provider_status_tradingview_mcp_agent.out` | `docs/experiments/actionable-regime-confidence/runs/20260511T205800-codex-provider-downstream-readback-v1/command-output/provider_status_tradingview_mcp_agent.err` |
| `provider_status_yfinance_agent` | `0` | `docs/experiments/actionable-regime-confidence/runs/20260511T205800-codex-provider-downstream-readback-v1/command-output/provider_status_yfinance_agent.out` | `docs/experiments/actionable-regime-confidence/runs/20260511T205800-codex-provider-downstream-readback-v1/command-output/provider_status_yfinance_agent.err` |
| `provider_status_kraken_public_agent` | `0` | `docs/experiments/actionable-regime-confidence/runs/20260511T205800-codex-provider-downstream-readback-v1/command-output/provider_status_kraken_public_agent.out` | `docs/experiments/actionable-regime-confidence/runs/20260511T205800-codex-provider-downstream-readback-v1/command-output/provider_status_kraken_public_agent.err` |
| `provider_status_kraken_cli_agent` | `0` | `docs/experiments/actionable-regime-confidence/runs/20260511T205800-codex-provider-downstream-readback-v1/command-output/provider_status_kraken_cli_agent.out` | `docs/experiments/actionable-regime-confidence/runs/20260511T205800-codex-provider-downstream-readback-v1/command-output/provider_status_kraken_cli_agent.err` |
| `auto_quant_status` | `0` | `docs/experiments/actionable-regime-confidence/runs/20260511T205800-codex-provider-downstream-readback-v1/command-output/auto_quant_status.out` | `docs/experiments/actionable-regime-confidence/runs/20260511T205800-codex-provider-downstream-readback-v1/command-output/auto_quant_status.err` |
| `analyze_live_nq_yfinance` | `0` | `docs/experiments/actionable-regime-confidence/runs/20260511T205800-codex-provider-downstream-readback-v1/command-output/analyze_live_nq_yfinance.out` | `docs/experiments/actionable-regime-confidence/runs/20260511T205800-codex-provider-downstream-readback-v1/command-output/analyze_live_nq_yfinance.err` |
| `pre_bayes_status` | `0` | `docs/experiments/actionable-regime-confidence/runs/20260511T205800-codex-provider-downstream-readback-v1/command-output/pre_bayes_status.out` | `docs/experiments/actionable-regime-confidence/runs/20260511T205800-codex-provider-downstream-readback-v1/command-output/pre_bayes_status.err` |
| `policy_training_status` | `0` | `docs/experiments/actionable-regime-confidence/runs/20260511T205800-codex-provider-downstream-readback-v1/command-output/policy_training_status.out` | `docs/experiments/actionable-regime-confidence/runs/20260511T205800-codex-provider-downstream-readback-v1/command-output/policy_training_status.err` |
| `workflow_status_execution_candidate` | `0` | `docs/experiments/actionable-regime-confidence/runs/20260511T205800-codex-provider-downstream-readback-v1/command-output/workflow_status_execution_candidate.out` | `docs/experiments/actionable-regime-confidence/runs/20260511T205800-codex-provider-downstream-readback-v1/command-output/workflow_status_execution_candidate.err` |
| `export_structural_path_ranking_target` | `0` | `docs/experiments/actionable-regime-confidence/runs/20260511T205800-codex-provider-downstream-readback-v1/command-output/export_structural_path_ranking_target.out` | `docs/experiments/actionable-regime-confidence/runs/20260511T205800-codex-provider-downstream-readback-v1/command-output/export_structural_path_ranking_target.err` |

## Result

Provider and downstream chain readback was captured, but no strict Board A intake row was acquired. This run therefore cannot promote confidence or replace the v35/v37 source-owned row blocker.

## Artifacts

- JSON: `/Users/thrill3r/projects-ict-engine/ict-engine/docs/experiments/actionable-regime-confidence/runs/20260511T205800-codex-provider-downstream-readback-v1/provider-downstream-readback/provider_downstream_readback_v1.json`
- Assertions: `/Users/thrill3r/projects-ict-engine/ict-engine/docs/experiments/actionable-regime-confidence/runs/20260511T205800-codex-provider-downstream-readback-v1/checks/provider_downstream_readback_v1_assertions.out`
- Command outputs: `/Users/thrill3r/projects-ict-engine/ict-engine/docs/experiments/actionable-regime-confidence/runs/20260511T205800-codex-provider-downstream-readback-v1/command-output`
