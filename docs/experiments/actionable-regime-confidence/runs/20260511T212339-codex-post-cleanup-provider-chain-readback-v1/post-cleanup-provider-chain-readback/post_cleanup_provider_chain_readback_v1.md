# Post-Cleanup Provider Chain Readback v1

- Decision: `post_cleanup_provider_chain_readback_v1=providers_and_chain_checked_strict_confidence_still_blocked`.
- Direct verifier status: `schema_ready_unscored`; positives/matched negatives: `24` / `24`.
- State dir: `/tmp/ict-engine-board-a-post-cleanup-provider-chain-readback-v1`.
- Auto-Quant state dir: `/tmp/ict-engine-board-a-post-cleanup-autoquant-status-v1`.
- Accepted rows added: `0`; new confidence gate: `false`.
- Strict full objective achieved: `false`; `update_goal=false`.
- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; external requests sent: `false`; trade usable: `false`.

## Providers

| Provider | Ready | Domains | Status | Reason |
|---|---:|---|---|---|
| `ibkr` | `false` | `market_data` | `configured_runtime_unhealthy` | `ibkr_runtime_dependencies_missing_with_gateway_reachable` |
| `tradingview_mcp` | `true` | `market_data` | `ready` | `mcp_url_and_api_key_available` |
| `yfinance` | `true` | `live_runtime;market_data` | `ready` | `native_yfinance_runtime_available;public_yahoo_http_endpoints` |
| `kraken_public` | `false` | `market_data` | `configured_runtime_unhealthy` | `python3_provider_dependencies_missing` |
| `kraken_cli` | `true` | `local_runtime` | `ready` | `kraken_cli_config_detected` |

## Commands

| Command | Exit | Output | Error |
|---|---:|---|---|
| `direct_manipulation_verifier` | `0` | `docs/experiments/actionable-regime-confidence/runs/20260511T212339-codex-post-cleanup-provider-chain-readback-v1/command-output/direct_manipulation_verifier.out` | `docs/experiments/actionable-regime-confidence/runs/20260511T212339-codex-post-cleanup-provider-chain-readback-v1/command-output/direct_manipulation_verifier.err` |
| `provider_status_agent` | `0` | `docs/experiments/actionable-regime-confidence/runs/20260511T212339-codex-post-cleanup-provider-chain-readback-v1/command-output/provider_status_agent.out` | `docs/experiments/actionable-regime-confidence/runs/20260511T212339-codex-post-cleanup-provider-chain-readback-v1/command-output/provider_status_agent.err` |
| `provider_status_ibkr_agent` | `0` | `docs/experiments/actionable-regime-confidence/runs/20260511T212339-codex-post-cleanup-provider-chain-readback-v1/command-output/provider_status_ibkr_agent.out` | `docs/experiments/actionable-regime-confidence/runs/20260511T212339-codex-post-cleanup-provider-chain-readback-v1/command-output/provider_status_ibkr_agent.err` |
| `provider_status_tradingview_mcp_agent` | `0` | `docs/experiments/actionable-regime-confidence/runs/20260511T212339-codex-post-cleanup-provider-chain-readback-v1/command-output/provider_status_tradingview_mcp_agent.out` | `docs/experiments/actionable-regime-confidence/runs/20260511T212339-codex-post-cleanup-provider-chain-readback-v1/command-output/provider_status_tradingview_mcp_agent.err` |
| `provider_status_yfinance_agent` | `0` | `docs/experiments/actionable-regime-confidence/runs/20260511T212339-codex-post-cleanup-provider-chain-readback-v1/command-output/provider_status_yfinance_agent.out` | `docs/experiments/actionable-regime-confidence/runs/20260511T212339-codex-post-cleanup-provider-chain-readback-v1/command-output/provider_status_yfinance_agent.err` |
| `provider_status_kraken_public_agent` | `0` | `docs/experiments/actionable-regime-confidence/runs/20260511T212339-codex-post-cleanup-provider-chain-readback-v1/command-output/provider_status_kraken_public_agent.out` | `docs/experiments/actionable-regime-confidence/runs/20260511T212339-codex-post-cleanup-provider-chain-readback-v1/command-output/provider_status_kraken_public_agent.err` |
| `provider_status_kraken_cli_agent` | `0` | `docs/experiments/actionable-regime-confidence/runs/20260511T212339-codex-post-cleanup-provider-chain-readback-v1/command-output/provider_status_kraken_cli_agent.out` | `docs/experiments/actionable-regime-confidence/runs/20260511T212339-codex-post-cleanup-provider-chain-readback-v1/command-output/provider_status_kraken_cli_agent.err` |
| `auto_quant_status` | `0` | `docs/experiments/actionable-regime-confidence/runs/20260511T212339-codex-post-cleanup-provider-chain-readback-v1/command-output/auto_quant_status.out` | `docs/experiments/actionable-regime-confidence/runs/20260511T212339-codex-post-cleanup-provider-chain-readback-v1/command-output/auto_quant_status.err` |
| `analyze_live_nq_yfinance` | `0` | `docs/experiments/actionable-regime-confidence/runs/20260511T212339-codex-post-cleanup-provider-chain-readback-v1/command-output/analyze_live_nq_yfinance.out` | `docs/experiments/actionable-regime-confidence/runs/20260511T212339-codex-post-cleanup-provider-chain-readback-v1/command-output/analyze_live_nq_yfinance.err` |
| `pre_bayes_status` | `0` | `docs/experiments/actionable-regime-confidence/runs/20260511T212339-codex-post-cleanup-provider-chain-readback-v1/command-output/pre_bayes_status.out` | `docs/experiments/actionable-regime-confidence/runs/20260511T212339-codex-post-cleanup-provider-chain-readback-v1/command-output/pre_bayes_status.err` |
| `policy_training_status` | `0` | `docs/experiments/actionable-regime-confidence/runs/20260511T212339-codex-post-cleanup-provider-chain-readback-v1/command-output/policy_training_status.out` | `docs/experiments/actionable-regime-confidence/runs/20260511T212339-codex-post-cleanup-provider-chain-readback-v1/command-output/policy_training_status.err` |
| `workflow_status_execution_candidate` | `0` | `docs/experiments/actionable-regime-confidence/runs/20260511T212339-codex-post-cleanup-provider-chain-readback-v1/command-output/workflow_status_execution_candidate.out` | `docs/experiments/actionable-regime-confidence/runs/20260511T212339-codex-post-cleanup-provider-chain-readback-v1/command-output/workflow_status_execution_candidate.err` |
| `export_structural_path_ranking_target` | `0` | `docs/experiments/actionable-regime-confidence/runs/20260511T212339-codex-post-cleanup-provider-chain-readback-v1/command-output/export_structural_path_ranking_target.out` | `docs/experiments/actionable-regime-confidence/runs/20260511T212339-codex-post-cleanup-provider-chain-readback-v1/command-output/export_structural_path_ranking_target.err` |

## Interpretation

The provider/downstream chain can be exercised, but this readback is runtime evidence only. It does not promote R6 or any price-root regime to an accepted strict confidence gate.

## Artifacts

- JSON: `/Users/thrill3r/projects-ict-engine/ict-engine/docs/experiments/actionable-regime-confidence/runs/20260511T212339-codex-post-cleanup-provider-chain-readback-v1/post-cleanup-provider-chain-readback/post_cleanup_provider_chain_readback_v1.json`
- Assertions: `/Users/thrill3r/projects-ict-engine/ict-engine/docs/experiments/actionable-regime-confidence/runs/20260511T212339-codex-post-cleanup-provider-chain-readback-v1/checks/post_cleanup_provider_chain_readback_v1_assertions.out`
- Command outputs: `/Users/thrill3r/projects-ict-engine/ict-engine/docs/experiments/actionable-regime-confidence/runs/20260511T212339-codex-post-cleanup-provider-chain-readback-v1/command-output`
