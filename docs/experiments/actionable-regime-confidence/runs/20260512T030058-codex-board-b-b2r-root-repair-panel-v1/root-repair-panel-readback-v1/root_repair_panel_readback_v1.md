# Root Repair Panel Readback v1

Run id: `20260512T030058+0800-codex-board-b-b2r-root-repair-panel-v1`

## Result

- RC-SPA gate: `fail:required_root_branch_hard_gates_failed`
- Stable profit score: `31.2705`
- Rows: `20347` variant / `10444` selected
- Price roots passed: `0/4`
- Root counts: `{'Bull': 4365, 'Bear': 340, 'Sideways': 5722, 'Crisis': 17}`

## Provider Visibility

- `ibkr`: ready=`False` status=`configured_runtime_unhealthy` reason=`ibkr_runtime_dependencies_missing_with_gateway_reachable`
- `ibkr_bridge`: ready=`False` status=`configured_runtime_unhealthy` reason=`ibkr_bridge_runtime_dependencies_missing_with_gateway_reachable`
- `kraken_cli`: ready=`True` status=`ready` reason=`kraken_cli_config_detected`
- `kraken_public`: ready=`False` status=`configured_runtime_unhealthy` reason=`python3_provider_dependencies_missing`
- `tradingview_mcp`: ready=`False` status=`configured_runtime_unhealthy` reason=`tradingview_mcp_connectivity_probe_failed`
- `yfinance`: ready=`True` status=`ready` reason=`public_yahoo_http_endpoints`

## ict-engine Readback

- Auto-Quant import: exit `0`, strategies ok `4`
- Real-trade dry-run ingest: `10444/10444` applied, invalid `0`
- BBN prior-init dry-run: evidence_value_gate_passed=`True`, strategies `4`
- Pre-Bayes: `pass_neutralized`
- Policy/CatBoost/path-ranker: `entry-model training modules mixed: ready=[] pending=[cisd_rb_long_v1,breaker_rb_long_v1] | structural path ranking target export missing runtime_selection=disabled runtime_source=none runtime_matches=0`
- Execution candidate: `execution_blocked`, readiness `0.2882093916661374`, ready `False`, actionable `False`
- Structural target export: `structural_path_ranking_target rows=3 history_rows=3 candidate_set_size=3 mature_rows=0 history_mature_rows=0 propensity_rows=1 calibrated_rows=0 execution_gate_rows=0 training_weight_rows=0`
- Consumed-artifact gate: `no_consumed_validation` / `no_consumed_artifacts`

## Decision

Promotion remains blocked. Downstream promotion is not allowed because RC-SPA passed `0/4` price roots, Pre-Bayes is `pass_neutralized`, execution is `execution_blocked`, path-ranker has no mature target rows, and consumed validation is absent.
