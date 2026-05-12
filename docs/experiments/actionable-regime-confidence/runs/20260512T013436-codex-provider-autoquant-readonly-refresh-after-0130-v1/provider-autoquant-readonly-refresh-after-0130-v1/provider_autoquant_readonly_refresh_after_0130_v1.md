# Provider / Auto-Quant Read-Only Refresh After 0130 v1

Run id: `20260512T013436-codex-provider-autoquant-readonly-refresh-after-0130-v1`

Gate result: `provider_autoquant_readonly_refresh_after_0130_v1=readiness_refreshed_no_promotion_source_control_blocked_autoquant_data_missing`

## Scope

This packet refreshes provider and downstream readiness only. It does not accept labels, populate source/control roots, approve `FLIP` controls, mutate canonical intake, relax thresholds, or authorize downstream promotion.

State dirs:
- Runtime state: `/tmp/ict-engine-board-a-provider-autoquant-readonly-refresh-20260512T013436`
- Auto-Quant state: `/tmp/ict-engine-board-a-provider-autoquant-readonly-refresh-20260512T013436-autoquant`

## Command Status

| Command | Exit | Evidence |
|---|---:|---|
| `provider-status --agent` | `0` | `command-output/provider_status_agent.out` |
| `provider-status --provider ibkr --agent` | `0` | `command-output/provider_status_ibkr_agent.out` |
| `provider-status --provider tradingview_mcp --agent` | `0` | `command-output/provider_status_tradingview_mcp_agent.out` |
| `provider-status --provider yfinance --agent` | `0` | `command-output/provider_status_yfinance_agent.out` |
| `provider-status --provider kraken_public --agent` | `0` | `command-output/provider_status_kraken_public_agent.out` |
| `provider-status --provider kraken_cli --agent` | `0` | `command-output/provider_status_kraken_cli_agent.out` |
| `auto-quant-status` initial | `0` | `command-output/auto_quant_status.out` |
| `auto-quant-bootstrap` | `0` | `command-output/auto_quant_bootstrap.out` |
| `auto-quant-status` after bootstrap | `0` | `command-output/auto_quant_status_after_bootstrap.out` |
| `auto-quant-prepare` | `1` | `command-output/auto_quant_prepare.err` |
| `auto-quant-status` after prepare | `0` | `command-output/auto_quant_status_after_prepare.out` |
| `analyze-live` yfinance NQ | `143` | `command-output/analyze_live_nq_yfinance.exit` |
| `pre-bayes-status --refresh` | `0` | `command-output/pre_bayes_status.out` |
| `policy-training-status` | `0` | `command-output/policy_training_status.out` |
| `workflow-status --phase execution-candidate --agent` | `0` | `command-output/workflow_status_execution_candidate.out` |
| `export-structural-path-ranking-target` | `0` | `command-output/export_structural_path_ranking_target.out` |

## Result

- Provider catalog remains `entry_model:2/2 ready | live_runtime:1/3 ready | local_runtime:1/2 ready | market_data:1/7 ready`.
- `yfinance` is ready for live runtime and market data.
- `kraken_cli` is ready as a local runtime.
- `ibkr` is not ready for market data: `ibkr_runtime_dependencies_missing_with_gateway_reachable`.
- `tradingview_mcp` is not ready: `tradingview_mcp_connectivity_probe_failed`.
- `kraken_public` is not ready: `python3_provider_dependencies_missing`.
- Auto-Quant bootstrap succeeded into the run-local `/tmp` state and resolved commit `34ba6b6ee6aa69813a50a72158d4c089d97afb96`.
- Auto-Quant prepare failed while Freqtrade/CCXT tried to load Binance markets: `Could not contact DNS servers` for `api.binance.com`; status remains `dependency_ready_data_missing`.
- The yfinance `analyze-live` command produced no output before it was terminated after a long stall; exit code is `143`.
- Pre-Bayes status has no latest bridge, policy, gate status, soft evidence, or canonical structural regime in this state.
- Policy/CatBoost-adjacent training is not ready: `matched_rows=0` for both entry models and structural path-ranking runtime is disabled.
- Workflow execution-candidate is not actionable and remains a bootstrap observe path because no workflow snapshot exists.
- Structural path-ranking export produced `1` row and `1` history row, but `mature_rows=0`, `training_weight_rows=0`, and no calibrated rows.
- R6 owner-export root is absent; R3 native-subhour root is absent; R5 recency-extension root is absent; source-label root is present but confidence-blocked.

## Boundary

This refresh exercised the provider/Auto-Quant/status surfaces but did not satisfy the Board A prerequisites for promotion. No provider/Auto-Quant/Pre-Bayes/BBN/CatBoost/path-ranking/execution-tree promotion rerun is allowed until accepted source/control roots exist and canonical merge is approved.

Accepted rows added: `0`. New confidence gate: `false`. Canonical merge allowed: `false`. Downstream promotion allowed: `false`. Strict full objective achieved: `false`. `update_goal=false`.
