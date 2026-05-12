# R6 Isolated Rehydration Split Readback v1

- Run id: `20260512T000038+0800-codex-r6-isolated-rehydration-split-readback-v1`
- Decision: `r6_isolated_rehydration_split_readback_v1=durable_v55_rehydrated_pooled95_pass_split_species_still_blocked`.
- Active board cursor root exists: `true`.
- Referenced preflight root exists: `true`.
- Isolated verifier status: `schema_ready_unscored`.
- Durable rehydrated rows: positives `73`, matched controls `73`, matched groups `70`.
- Pooled Wilson95 min LCB: `0.950006246616`; pooled gate `true`.
- Broad-normal sidecar rows: `80`; sidecar min LCB `0.950006246616`; sidecar gate `true`.
- Direct split gate: `false`; positive chronological split gate `false`; direct species closed `false`.
- Post-Thakkar candidates materialized in this snapshot: `15/34`; controls listed in latest consolidation: `2`.
- Accepted rows added to shared intake: `0`; new confidence gate: `false`; strict full objective achieved: `false`; `update_goal=false`.
- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; shared intake mutated: `false`; trade usable: `false`.

## Provider / Chain Readback

| Provider | Ready | Status | Reason |
|---|---:|---|---|
| `ibkr` | `false` | `configured_runtime_unhealthy` | `ibkr_runtime_dependencies_missing_with_gateway_reachable` |
| `tradingview_mcp` | `false` | `configured_runtime_unhealthy` | `tradingview_mcp_connectivity_probe_failed` |
| `yfinance` | `true` | `ready` | `native_yfinance_runtime_available;public_yahoo_http_endpoints` |
| `kraken_public` | `false` | `configured_runtime_unhealthy` | `python3_provider_dependencies_missing` |
| `kraken_cli` | `true` | `ready` | `kraken_cli_config_detected` |

| Command | Exit | Output | Error |
|---|---:|---|---|
| `direct_manipulation_row_intake_verifier_isolated` | `0` | `docs/experiments/actionable-regime-confidence/runs/20260512T000038-codex-r6-isolated-rehydration-split-readback-v1/command-output/direct_manipulation_row_intake_verifier_isolated.stdout.txt` | `docs/experiments/actionable-regime-confidence/runs/20260512T000038-codex-r6-isolated-rehydration-split-readback-v1/command-output/direct_manipulation_row_intake_verifier_isolated.stderr.txt` |
| `provider_status_agent` | `0` | `docs/experiments/actionable-regime-confidence/runs/20260512T000038-codex-r6-isolated-rehydration-split-readback-v1/command-output/provider_status_agent.stdout.txt` | `docs/experiments/actionable-regime-confidence/runs/20260512T000038-codex-r6-isolated-rehydration-split-readback-v1/command-output/provider_status_agent.stderr.txt` |
| `provider_status_ibkr_agent` | `0` | `docs/experiments/actionable-regime-confidence/runs/20260512T000038-codex-r6-isolated-rehydration-split-readback-v1/command-output/provider_status_ibkr_agent.stdout.txt` | `docs/experiments/actionable-regime-confidence/runs/20260512T000038-codex-r6-isolated-rehydration-split-readback-v1/command-output/provider_status_ibkr_agent.stderr.txt` |
| `provider_status_tradingview_mcp_agent` | `0` | `docs/experiments/actionable-regime-confidence/runs/20260512T000038-codex-r6-isolated-rehydration-split-readback-v1/command-output/provider_status_tradingview_mcp_agent.stdout.txt` | `docs/experiments/actionable-regime-confidence/runs/20260512T000038-codex-r6-isolated-rehydration-split-readback-v1/command-output/provider_status_tradingview_mcp_agent.stderr.txt` |
| `provider_status_yfinance_agent` | `0` | `docs/experiments/actionable-regime-confidence/runs/20260512T000038-codex-r6-isolated-rehydration-split-readback-v1/command-output/provider_status_yfinance_agent.stdout.txt` | `docs/experiments/actionable-regime-confidence/runs/20260512T000038-codex-r6-isolated-rehydration-split-readback-v1/command-output/provider_status_yfinance_agent.stderr.txt` |
| `provider_status_kraken_public_agent` | `0` | `docs/experiments/actionable-regime-confidence/runs/20260512T000038-codex-r6-isolated-rehydration-split-readback-v1/command-output/provider_status_kraken_public_agent.stdout.txt` | `docs/experiments/actionable-regime-confidence/runs/20260512T000038-codex-r6-isolated-rehydration-split-readback-v1/command-output/provider_status_kraken_public_agent.stderr.txt` |
| `provider_status_kraken_cli_agent` | `0` | `docs/experiments/actionable-regime-confidence/runs/20260512T000038-codex-r6-isolated-rehydration-split-readback-v1/command-output/provider_status_kraken_cli_agent.stdout.txt` | `docs/experiments/actionable-regime-confidence/runs/20260512T000038-codex-r6-isolated-rehydration-split-readback-v1/command-output/provider_status_kraken_cli_agent.stderr.txt` |
| `auto_quant_status` | `0` | `docs/experiments/actionable-regime-confidence/runs/20260512T000038-codex-r6-isolated-rehydration-split-readback-v1/command-output/auto_quant_status.stdout.txt` | `docs/experiments/actionable-regime-confidence/runs/20260512T000038-codex-r6-isolated-rehydration-split-readback-v1/command-output/auto_quant_status.stderr.txt` |
| `analyze_live_nq_yfinance` | `0` | `docs/experiments/actionable-regime-confidence/runs/20260512T000038-codex-r6-isolated-rehydration-split-readback-v1/command-output/analyze_live_nq_yfinance.stdout.txt` | `docs/experiments/actionable-regime-confidence/runs/20260512T000038-codex-r6-isolated-rehydration-split-readback-v1/command-output/analyze_live_nq_yfinance.stderr.txt` |
| `pre_bayes_status` | `0` | `docs/experiments/actionable-regime-confidence/runs/20260512T000038-codex-r6-isolated-rehydration-split-readback-v1/command-output/pre_bayes_status.stdout.txt` | `docs/experiments/actionable-regime-confidence/runs/20260512T000038-codex-r6-isolated-rehydration-split-readback-v1/command-output/pre_bayes_status.stderr.txt` |
| `policy_training_status` | `0` | `docs/experiments/actionable-regime-confidence/runs/20260512T000038-codex-r6-isolated-rehydration-split-readback-v1/command-output/policy_training_status.stdout.txt` | `docs/experiments/actionable-regime-confidence/runs/20260512T000038-codex-r6-isolated-rehydration-split-readback-v1/command-output/policy_training_status.stderr.txt` |
| `workflow_status_execution_candidate` | `0` | `docs/experiments/actionable-regime-confidence/runs/20260512T000038-codex-r6-isolated-rehydration-split-readback-v1/command-output/workflow_status_execution_candidate.stdout.txt` | `docs/experiments/actionable-regime-confidence/runs/20260512T000038-codex-r6-isolated-rehydration-split-readback-v1/command-output/workflow_status_execution_candidate.stderr.txt` |
| `export_structural_path_ranking_target` | `0` | `docs/experiments/actionable-regime-confidence/runs/20260512T000038-codex-r6-isolated-rehydration-split-readback-v1/command-output/export_structural_path_ranking_target.stdout.txt` | `docs/experiments/actionable-regime-confidence/runs/20260512T000038-codex-r6-isolated-rehydration-split-readback-v1/command-output/export_structural_path_ranking_target.stderr.txt` |

## Artifacts

- JSON: `docs/experiments/actionable-regime-confidence/runs/20260512T000038-codex-r6-isolated-rehydration-split-readback-v1/r6-isolated-rehydration-split-readback/r6_isolated_rehydration_split_readback_v1.json`
- Isolated positive rows: `docs/experiments/actionable-regime-confidence/runs/20260512T000038-codex-r6-isolated-rehydration-split-readback-v1/r6-isolated-rehydration-split-readback/isolated-direct-intake/positive_spoofing_layering_rows.csv`
- Isolated matched controls: `docs/experiments/actionable-regime-confidence/runs/20260512T000038-codex-r6-isolated-rehydration-split-readback-v1/r6-isolated-rehydration-split-readback/isolated-direct-intake/matched_negative_normal_activity_rows.csv`
- Isolated provenance: `docs/experiments/actionable-regime-confidence/runs/20260512T000038-codex-r6-isolated-rehydration-split-readback-v1/r6-isolated-rehydration-split-readback/isolated-direct-intake/provenance_manifest.json`
- Direct split metrics: `docs/experiments/actionable-regime-confidence/runs/20260512T000038-codex-r6-isolated-rehydration-split-readback-v1/r6-isolated-rehydration-split-readback/r6_isolated_rehydration_direct_split_metrics_v1.csv`
- Candidate materialization: `docs/experiments/actionable-regime-confidence/runs/20260512T000038-codex-r6-isolated-rehydration-split-readback-v1/r6-isolated-rehydration-split-readback/r6_isolated_rehydration_candidate_materialization_v1.csv`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260512T000038-codex-r6-isolated-rehydration-split-readback-v1/checks/r6_isolated_rehydration_split_readback_v1_assertions.out`

## Next
Materialize source-owned matched controls and split support for the unrehydrated sidecar positives, then rerun chronological/symbol/venue gates while keeping R5 blocked.
