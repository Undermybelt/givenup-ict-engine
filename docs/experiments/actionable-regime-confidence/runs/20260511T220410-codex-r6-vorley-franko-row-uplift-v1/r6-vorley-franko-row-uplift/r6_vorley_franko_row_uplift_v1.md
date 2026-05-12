# R6 Vorley/Franco Row Uplift v1

- Decision: `r6_vorley_franko_row_uplift_v1=rows_added_calibration_still_blocked`.
- Positive rows: `46` -> `62`; added `7`.
- Matched negative rows: `46` -> `62`; added `7`.
- Direct verifier status: `schema_ready_unscored`.
- Wilson95 LCB positive/negative/min: `0.941656` / `0.941656` / `0.941656`.
- Support ok: `true`; broad normal sample: `false`.
- Provider summary: `entry_model:2/2 ready | live_runtime:1/3 ready | local_runtime:1/2 ready | market_data:2/7 ready`.
- Auto-Quant status: `missing_dependency`.
- Accepted rows added: `0`; new confidence gate: `false`; R6 direct species closed: `false`.
- Strict full objective achieved: `false`; `update_goal=false`.
- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; external requests sent: `false`; trade usable: `false`.

## Gate Rows

| Gate | Observed | Required | Pass |
|---|---|---|---:|
| `positive_support` | `62` | `50` | `true` |
| `matched_negative_support` | `62` | `50` | `true` |
| `wilson95_min_lcb` | `0.941656` | `>=0.95` | `false` |
| `broad_normal_sample` | `False` | `True` | `false` |
| `direct_verifier_returncode` | `0` | `0` | `true` |

## Boundary

This run materializes only source-described event/control pairs from official CFTC text already cached under `/tmp`. The added controls are still same-event genuine-order controls, not independent broad normal-market samples, so R6 remains fail-closed.

## Command Readback

| Command | Exit | Output | Error |
|---|---:|---|---|
| `direct_manipulation_row_intake_verifier` | `0` | `docs/experiments/actionable-regime-confidence/runs/20260511T220410-codex-r6-vorley-franko-row-uplift-v1/command-output/direct_manipulation_row_intake_verifier.out` | `docs/experiments/actionable-regime-confidence/runs/20260511T220410-codex-r6-vorley-franko-row-uplift-v1/command-output/direct_manipulation_row_intake_verifier.err` |
| `provider_status_agent` | `0` | `docs/experiments/actionable-regime-confidence/runs/20260511T220410-codex-r6-vorley-franko-row-uplift-v1/command-output/provider_status_agent.out` | `docs/experiments/actionable-regime-confidence/runs/20260511T220410-codex-r6-vorley-franko-row-uplift-v1/command-output/provider_status_agent.err` |
| `provider_status_ibkr_agent` | `0` | `docs/experiments/actionable-regime-confidence/runs/20260511T220410-codex-r6-vorley-franko-row-uplift-v1/command-output/provider_status_ibkr_agent.out` | `docs/experiments/actionable-regime-confidence/runs/20260511T220410-codex-r6-vorley-franko-row-uplift-v1/command-output/provider_status_ibkr_agent.err` |
| `provider_status_tradingview_mcp_agent` | `0` | `docs/experiments/actionable-regime-confidence/runs/20260511T220410-codex-r6-vorley-franko-row-uplift-v1/command-output/provider_status_tradingview_mcp_agent.out` | `docs/experiments/actionable-regime-confidence/runs/20260511T220410-codex-r6-vorley-franko-row-uplift-v1/command-output/provider_status_tradingview_mcp_agent.err` |
| `provider_status_yfinance_agent` | `0` | `docs/experiments/actionable-regime-confidence/runs/20260511T220410-codex-r6-vorley-franko-row-uplift-v1/command-output/provider_status_yfinance_agent.out` | `docs/experiments/actionable-regime-confidence/runs/20260511T220410-codex-r6-vorley-franko-row-uplift-v1/command-output/provider_status_yfinance_agent.err` |
| `provider_status_kraken_public_agent` | `0` | `docs/experiments/actionable-regime-confidence/runs/20260511T220410-codex-r6-vorley-franko-row-uplift-v1/command-output/provider_status_kraken_public_agent.out` | `docs/experiments/actionable-regime-confidence/runs/20260511T220410-codex-r6-vorley-franko-row-uplift-v1/command-output/provider_status_kraken_public_agent.err` |
| `provider_status_kraken_cli_agent` | `0` | `docs/experiments/actionable-regime-confidence/runs/20260511T220410-codex-r6-vorley-franko-row-uplift-v1/command-output/provider_status_kraken_cli_agent.out` | `docs/experiments/actionable-regime-confidence/runs/20260511T220410-codex-r6-vorley-franko-row-uplift-v1/command-output/provider_status_kraken_cli_agent.err` |
| `auto_quant_status` | `0` | `docs/experiments/actionable-regime-confidence/runs/20260511T220410-codex-r6-vorley-franko-row-uplift-v1/command-output/auto_quant_status.out` | `docs/experiments/actionable-regime-confidence/runs/20260511T220410-codex-r6-vorley-franko-row-uplift-v1/command-output/auto_quant_status.err` |
| `analyze_live_nq_yfinance` | `0` | `docs/experiments/actionable-regime-confidence/runs/20260511T220410-codex-r6-vorley-franko-row-uplift-v1/command-output/analyze_live_nq_yfinance.out` | `docs/experiments/actionable-regime-confidence/runs/20260511T220410-codex-r6-vorley-franko-row-uplift-v1/command-output/analyze_live_nq_yfinance.err` |
| `pre_bayes_status` | `0` | `docs/experiments/actionable-regime-confidence/runs/20260511T220410-codex-r6-vorley-franko-row-uplift-v1/command-output/pre_bayes_status.out` | `docs/experiments/actionable-regime-confidence/runs/20260511T220410-codex-r6-vorley-franko-row-uplift-v1/command-output/pre_bayes_status.err` |
| `policy_training_status` | `0` | `docs/experiments/actionable-regime-confidence/runs/20260511T220410-codex-r6-vorley-franko-row-uplift-v1/command-output/policy_training_status.out` | `docs/experiments/actionable-regime-confidence/runs/20260511T220410-codex-r6-vorley-franko-row-uplift-v1/command-output/policy_training_status.err` |
| `workflow_status_execution_candidate` | `0` | `docs/experiments/actionable-regime-confidence/runs/20260511T220410-codex-r6-vorley-franko-row-uplift-v1/command-output/workflow_status_execution_candidate.out` | `docs/experiments/actionable-regime-confidence/runs/20260511T220410-codex-r6-vorley-franko-row-uplift-v1/command-output/workflow_status_execution_candidate.err` |
| `export_structural_path_ranking_target` | `0` | `docs/experiments/actionable-regime-confidence/runs/20260511T220410-codex-r6-vorley-franko-row-uplift-v1/command-output/export_structural_path_ranking_target.out` | `docs/experiments/actionable-regime-confidence/runs/20260511T220410-codex-r6-vorley-franko-row-uplift-v1/command-output/export_structural_path_ranking_target.err` |

## Artifacts

- JSON: `docs/experiments/actionable-regime-confidence/runs/20260511T220410-codex-r6-vorley-franko-row-uplift-v1/r6-vorley-franko-row-uplift/r6_vorley_franko_row_uplift_v1.json`
- Gate CSV: `docs/experiments/actionable-regime-confidence/runs/20260511T220410-codex-r6-vorley-franko-row-uplift-v1/r6-vorley-franko-row-uplift/r6_vorley_franko_row_uplift_v1_gates.csv`
- Intake summary CSV: `docs/experiments/actionable-regime-confidence/runs/20260511T220410-codex-r6-vorley-franko-row-uplift-v1/r6-vorley-franko-row-uplift/r6_vorley_franko_row_uplift_v1_intake_summary.csv`
- Direct verifier stdout: `docs/experiments/actionable-regime-confidence/runs/20260511T220410-codex-r6-vorley-franko-row-uplift-v1/command-output/direct_manipulation_row_intake_verifier.out`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260511T220410-codex-r6-vorley-franko-row-uplift-v1/checks/r6_vorley_franko_row_uplift_v1_assertions.out`
