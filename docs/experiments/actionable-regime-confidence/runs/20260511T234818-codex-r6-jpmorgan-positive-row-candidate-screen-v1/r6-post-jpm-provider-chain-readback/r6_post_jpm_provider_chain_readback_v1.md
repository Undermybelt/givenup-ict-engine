# R6 Post-JPM Provider Chain Readback v1

- Decision: `r6_post_jpm_provider_chain_readback_v1=runtime_chain_checked_candidate_gate_still_unaccepted`.
- Direct verifier status: `blocked`.
- State dir: `/tmp/ict-engine-board-a-r6-post-jpm-chain-readback-v1`.
- Auto-Quant state dir: `/tmp/ict-engine-board-a-r6-post-jpm-autoquant-status-v1`.
- Accepted rows added: `0`; new confidence gate: `false`.
- Strict full objective achieved: `false`; `update_goal=false`.
- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; trade usable: `false`.

## Providers

| Provider | Ready | Status | Reason |
|---|---:|---|---|
| `ibkr` | `false` | `configured_runtime_unhealthy` | `ibkr_runtime_dependencies_missing_with_gateway_reachable` |
| `tradingview_mcp` | `false` | `configured_runtime_unhealthy` | `tradingview_mcp_connectivity_probe_failed` |
| `yfinance` | `true` | `ready` | `native_yfinance_runtime_available;public_yahoo_http_endpoints` |
| `kraken_public` | `false` | `configured_runtime_unhealthy` | `python3_provider_dependencies_missing` |
| `kraken_cli` | `true` | `ready` | `kraken_cli_config_detected` |

## Commands

| Command | Exit | Output | Error |
|---|---:|---|---|
| `direct_manipulation_verifier` | `2` | `docs/experiments/actionable-regime-confidence/runs/20260511T234818-codex-r6-jpmorgan-positive-row-candidate-screen-v1/command-output/direct_manipulation_verifier.out` | `docs/experiments/actionable-regime-confidence/runs/20260511T234818-codex-r6-jpmorgan-positive-row-candidate-screen-v1/command-output/direct_manipulation_verifier.err` |
| `provider_status_agent` | `0` | `docs/experiments/actionable-regime-confidence/runs/20260511T234818-codex-r6-jpmorgan-positive-row-candidate-screen-v1/command-output/provider_status_agent.out` | `docs/experiments/actionable-regime-confidence/runs/20260511T234818-codex-r6-jpmorgan-positive-row-candidate-screen-v1/command-output/provider_status_agent.err` |
| `provider_status_ibkr_agent` | `0` | `docs/experiments/actionable-regime-confidence/runs/20260511T234818-codex-r6-jpmorgan-positive-row-candidate-screen-v1/command-output/provider_status_ibkr_agent.out` | `docs/experiments/actionable-regime-confidence/runs/20260511T234818-codex-r6-jpmorgan-positive-row-candidate-screen-v1/command-output/provider_status_ibkr_agent.err` |
| `provider_status_tradingview_mcp_agent` | `0` | `docs/experiments/actionable-regime-confidence/runs/20260511T234818-codex-r6-jpmorgan-positive-row-candidate-screen-v1/command-output/provider_status_tradingview_mcp_agent.out` | `docs/experiments/actionable-regime-confidence/runs/20260511T234818-codex-r6-jpmorgan-positive-row-candidate-screen-v1/command-output/provider_status_tradingview_mcp_agent.err` |
| `provider_status_yfinance_agent` | `0` | `docs/experiments/actionable-regime-confidence/runs/20260511T234818-codex-r6-jpmorgan-positive-row-candidate-screen-v1/command-output/provider_status_yfinance_agent.out` | `docs/experiments/actionable-regime-confidence/runs/20260511T234818-codex-r6-jpmorgan-positive-row-candidate-screen-v1/command-output/provider_status_yfinance_agent.err` |
| `provider_status_kraken_public_agent` | `0` | `docs/experiments/actionable-regime-confidence/runs/20260511T234818-codex-r6-jpmorgan-positive-row-candidate-screen-v1/command-output/provider_status_kraken_public_agent.out` | `docs/experiments/actionable-regime-confidence/runs/20260511T234818-codex-r6-jpmorgan-positive-row-candidate-screen-v1/command-output/provider_status_kraken_public_agent.err` |
| `provider_status_kraken_cli_agent` | `0` | `docs/experiments/actionable-regime-confidence/runs/20260511T234818-codex-r6-jpmorgan-positive-row-candidate-screen-v1/command-output/provider_status_kraken_cli_agent.out` | `docs/experiments/actionable-regime-confidence/runs/20260511T234818-codex-r6-jpmorgan-positive-row-candidate-screen-v1/command-output/provider_status_kraken_cli_agent.err` |
| `auto_quant_status` | `0` | `docs/experiments/actionable-regime-confidence/runs/20260511T234818-codex-r6-jpmorgan-positive-row-candidate-screen-v1/command-output/auto_quant_status.out` | `docs/experiments/actionable-regime-confidence/runs/20260511T234818-codex-r6-jpmorgan-positive-row-candidate-screen-v1/command-output/auto_quant_status.err` |
| `analyze_live_nq_yfinance` | `0` | `docs/experiments/actionable-regime-confidence/runs/20260511T234818-codex-r6-jpmorgan-positive-row-candidate-screen-v1/command-output/analyze_live_nq_yfinance.out` | `docs/experiments/actionable-regime-confidence/runs/20260511T234818-codex-r6-jpmorgan-positive-row-candidate-screen-v1/command-output/analyze_live_nq_yfinance.err` |
| `pre_bayes_status` | `0` | `docs/experiments/actionable-regime-confidence/runs/20260511T234818-codex-r6-jpmorgan-positive-row-candidate-screen-v1/command-output/pre_bayes_status.out` | `docs/experiments/actionable-regime-confidence/runs/20260511T234818-codex-r6-jpmorgan-positive-row-candidate-screen-v1/command-output/pre_bayes_status.err` |
| `policy_training_status` | `0` | `docs/experiments/actionable-regime-confidence/runs/20260511T234818-codex-r6-jpmorgan-positive-row-candidate-screen-v1/command-output/policy_training_status.out` | `docs/experiments/actionable-regime-confidence/runs/20260511T234818-codex-r6-jpmorgan-positive-row-candidate-screen-v1/command-output/policy_training_status.err` |
| `workflow_status_execution_candidate` | `0` | `docs/experiments/actionable-regime-confidence/runs/20260511T234818-codex-r6-jpmorgan-positive-row-candidate-screen-v1/command-output/workflow_status_execution_candidate.out` | `docs/experiments/actionable-regime-confidence/runs/20260511T234818-codex-r6-jpmorgan-positive-row-candidate-screen-v1/command-output/workflow_status_execution_candidate.err` |
| `export_structural_path_ranking_target` | `0` | `docs/experiments/actionable-regime-confidence/runs/20260511T234818-codex-r6-jpmorgan-positive-row-candidate-screen-v1/command-output/export_structural_path_ranking_target.out` | `docs/experiments/actionable-regime-confidence/runs/20260511T234818-codex-r6-jpmorgan-positive-row-candidate-screen-v1/command-output/export_structural_path_ranking_target.err` |
