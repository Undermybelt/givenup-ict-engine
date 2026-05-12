# Provider Chain Intake Readback v37

Decision: `provider_chain_intake_readback_v37=intakes_absent_runtime_chain_readback_no_new_gate_blocked`.

## Result

- Provider status: `entry_model:2/2 ready | live_runtime:1/3 ready | local_runtime:1/2 ready | market_data:1/7 ready`.
- Ready intake roots: `0/4`.
- Real-chain artifact readback complete: `true`.
- Outbox v2 rows: `9`; request sent: `false`; rows acquired: `false`.
- Accepted rows added: `0`; new confidence gate: `false`.
- Strict full objective achieved: `false`; `update_goal=false`.
- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; trade usable: `false`.

## Named Providers

| Provider | Domain | Ready | Status | Reason |
|---|---|---:|---|---|
| `yfinance` | `live_runtime` | `true` | `ready` | `native_yfinance_runtime_available` |
| `ibkr_bridge` | `local_runtime` | `false` | `configured_runtime_unhealthy` | `ibkr_bridge_runtime_dependencies_missing_with_gateway_reachable` |
| `kraken_cli` | `local_runtime` | `true` | `ready` | `kraken_cli_config_detected` |
| `ibkr` | `market_data` | `false` | `configured_runtime_unhealthy` | `ibkr_runtime_dependencies_missing_with_gateway_reachable` |
| `kraken_public` | `market_data` | `false` | `configured_runtime_unhealthy` | `python3_provider_dependencies_missing` |
| `tradingview_mcp` | `market_data` | `false` | `configured_runtime_unhealthy` | `tradingview_mcp_connectivity_probe_failed` |
| `yfinance` | `market_data` | `true` | `ready` | `public_yahoo_http_endpoints` |

## Intake Roots

| Root | Ready | Missing Files |
|---|---:|---|
| `source_label_equivalence` | `false` | `source_label_equivalence_rows.csv;source_label_equivalence_provenance.json` |
| `native_subhour_source_label` | `false` | `native_subhour_source_label_rows.csv;native_subhour_source_label_provenance.json` |
| `source_panel_recency_extension` | `false` | `stock_market_regimes_2026_extension.csv;source_panel_recency_provenance.json` |
| `direct_manipulation_row_intake` | `false` | `matched_negative_normal_activity_rows.csv` |

## Full-Chain Readback

| Artifact | Exists |
|---|---:|
| `docs/experiments/actionable-regime-confidence/runs/20260510T201931-hermes-loop-real-chain/autoquant/03_auto_quant_results_import_nq.json` | `true` |
| `docs/experiments/actionable-regime-confidence/runs/20260510T201931-hermes-loop-real-chain/bbn/02_auto_quant_prior_init_nq_apply.json` | `true` |
| `docs/experiments/actionable-regime-confidence/runs/20260510T201931-hermes-loop-real-chain/ict-engine/06_pre_bayes_status_isolated_after_bbn.json` | `true` |
| `docs/experiments/actionable-regime-confidence/runs/20260510T201931-hermes-loop-real-chain/catboost/07_apply_structural_path_ranking_external_scores.json` | `true` |
| `docs/experiments/actionable-regime-confidence/runs/20260510T201931-hermes-loop-real-chain/ict-engine/07_policy_training_status_after_catboost_apply.json` | `true` |
| `docs/experiments/actionable-regime-confidence/runs/20260510T201931-hermes-loop-real-chain/execution/02_execution_tree_trace_after_catboost_apply_nq.json` | `true` |

## Next

Do not relax thresholds or promote public proxy labels. Populate one of the required /tmp intake roots with real source-owned or owner-approved rows/provenance, then rerun the relevant verifier.

## Artifacts

- JSON: `docs/experiments/actionable-regime-confidence/runs/20260511T205142-codex-provider-chain-intake-readback-v37/provider-chain-intake-readback/provider_chain_intake_readback_v37.json`
- Intake roots: `docs/experiments/actionable-regime-confidence/runs/20260511T205142-codex-provider-chain-intake-readback-v37/provider-chain-intake-readback/provider_chain_intake_readback_v37_intake_roots.csv`
- Named providers: `docs/experiments/actionable-regime-confidence/runs/20260511T205142-codex-provider-chain-intake-readback-v37/provider-chain-intake-readback/provider_chain_intake_readback_v37_named_providers.csv`
- Checklist: `docs/experiments/actionable-regime-confidence/runs/20260511T205142-codex-provider-chain-intake-readback-v37/provider-chain-intake-readback/provider_chain_intake_readback_v37_checklist.csv`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260511T205142-codex-provider-chain-intake-readback-v37/checks/provider_chain_intake_readback_v37_assertions.out`
