# Read-Only Runtime Chain Refresh After 013042 v1

- Run id: `20260512T013533-codex-readonly-runtime-chain-refresh-after-013042-v1`.
- Gate result: `readonly_runtime_chain_refresh_after_013042_v1=commands_ran_non_promoting_roots_blocked`.
- Provider summary: `entry_model:2/2 ready | live_runtime:1/3 ready | local_runtime:1/2 ready | market_data:1/7 ready`.
- Auto-Quant status: `dependency_ready_seed_required`; healthy `true`; data ready `true`.
- Workflow execution direction: `None`; stop: `None`.
- Structural path-ranking export rows: `3`; mature rows: `0`.
- Accepted rows added: `0`; new confidence gate: `false`; canonical merge allowed: `false`; downstream promotion rerun allowed: `false`; strict full objective achieved: `false`; `update_goal=false`.
- Runtime code changed: `false`; shared intake mutated: `false`; R3/R5/R6 roots mutated: `false`; thresholds relaxed: `false`; raw data committed: `false`; trade usable: `false`.

## Commands

- `provider_status_agent` exit `0`: `/Users/thrill3r/projects-ict-engine/ict-engine/target/debug/ict-engine provider-status --agent`
- `auto_quant_status_json` exit `0`: `/Users/thrill3r/projects-ict-engine/ict-engine/target/debug/ict-engine auto-quant-status --state-dir /tmp/ict-engine-board-a-readonly-runtime-20260512T013533/auto-quant --output-format json`
- `analyze_demo_agent` exit `0`: `/Users/thrill3r/projects-ict-engine/ict-engine/target/debug/ict-engine analyze --symbol NQ --demo --state-dir /tmp/ict-engine-board-a-readonly-runtime-20260512T013533 --output-format agent`
- `pre_bayes_status_json` exit `0`: `/Users/thrill3r/projects-ict-engine/ict-engine/target/debug/ict-engine pre-bayes-status --symbol NQ --state-dir /tmp/ict-engine-board-a-readonly-runtime-20260512T013533 --refresh --output-format json`
- `policy_training_status_json` exit `0`: `/Users/thrill3r/projects-ict-engine/ict-engine/target/debug/ict-engine policy-training-status --symbol NQ --state-dir /tmp/ict-engine-board-a-readonly-runtime-20260512T013533 --output-format json`
- `workflow_status_execution_candidate_agent` exit `0`: `/Users/thrill3r/projects-ict-engine/ict-engine/target/debug/ict-engine workflow-status --symbol NQ --state-dir /tmp/ict-engine-board-a-readonly-runtime-20260512T013533 --refresh --phase execution-candidate --output-format agent`
- `workflow_status_structural_path_bundle_agent` exit `0`: `/Users/thrill3r/projects-ict-engine/ict-engine/target/debug/ict-engine workflow-status --symbol NQ --state-dir /tmp/ict-engine-board-a-readonly-runtime-20260512T013533 --refresh --phase structural-recommended-path-bundle --output-format agent`
- `export_structural_path_ranking_target` exit `0`: `/Users/thrill3r/projects-ict-engine/ict-engine/target/debug/ict-engine export-structural-path-ranking-target --symbol NQ --state-dir /tmp/ict-engine-board-a-readonly-runtime-20260512T013533`

## Provider Focus

- `yfinance`: ready `true`, status `ready`, reason `native_yfinance_runtime_available`
- `ibkr_bridge`: ready `false`, status `configured_runtime_unhealthy`, reason `ibkr_bridge_runtime_dependencies_missing_with_gateway_reachable`
- `kraken_cli`: ready `true`, status `ready`, reason `kraken_cli_config_detected`
- `kraken_public`: ready `false`, status `configured_runtime_unhealthy`, reason `python3_provider_dependencies_missing`
- `tradingview_mcp`: ready `false`, status `configured_runtime_unhealthy`, reason `tradingview_mcp_connectivity_probe_failed`
- `yfinance`: ready `true`, status `ready`, reason `public_yahoo_http_endpoints`

## Boundary

This packet proves the runtime surfaces can be queried in order, but it is not promotion evidence. R6 owner controls or explicit FLIP approval, canonical merge, source-native cross-timeframe labels, and R3/R5 source files remain prerequisites before any accepted downstream rerun.

Artifacts:
- JSON: `docs/experiments/actionable-regime-confidence/runs/20260512T013533-codex-readonly-runtime-chain-refresh-after-013042-v1/readonly-runtime-chain-refresh-after-013042-v1/readonly_runtime_chain_refresh_after_013042_v1.json`
- Selected provider CSV: `docs/experiments/actionable-regime-confidence/runs/20260512T013533-codex-readonly-runtime-chain-refresh-after-013042-v1/readonly-runtime-chain-refresh-after-013042-v1/readonly_runtime_selected_provider_status_v1.csv`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260512T013533-codex-readonly-runtime-chain-refresh-after-013042-v1/checks/readonly_runtime_chain_refresh_after_013042_v1_assertions.out`
