# 112315 Bybit Momentum Downstream v1

Run id: `20260512T112904+0800-codex-112315-provider-matrix-aq-readback-v1`
Symbol: `B2R_PROVIDER_MATRIX_BYBIT_MOMENTUM_112315`
Source matrix: `20260512T112315+0800-codex-board-b-six-provider-btc-matrix-probe-v1`

## Scope
This carries the positive Bybit public-provider momentum branch through ingest, Pre-Bayes, policy export, structural bundle, execution candidate, and full workflow status.
It remains blocked by the same source provider gate: TVR failed and IBKR BTC returned zero rows in the source matrix.

## Trades
- Materialized trades: `34` from `docs/experiments/actionable-regime-confidence/runs/20260512T112904+0800-codex-112315-provider-matrix-aq-readback-v1/derived/bybit_provider_matrix_momentum_112315_real_trades.jsonl`.
- Branch path: `Bull -> ProviderCryptoMomentum -> RsiMidlineExpansion -> ProviderCryptoMomentumStateV1`.
- Wins/losses: `14` / `20`.

## Command Exits
- `20_ingest_real_trades_dry_run`: `0`
- `21_ingest_real_trades_force`: `0`
- `22_pre_bayes_status`: `0`
- `23_policy_training_status_before_export`: `0`
- `24_export_structural_path_ranking_target`: `0`
- `25_policy_training_status_after_export`: `0`
- `26_workflow_structural_bundle`: `0`
- `27_workflow_execution_candidate`: `0`
- `28_workflow_full`: `0`

## Readback
- Ingest applied: `34` / invalid `0`.
- Learning feedback count: `34`.
- Structural target rows: `2`, mature rows: `1`, history rows: `36`, history mature rows: `35`.
- Execution ready/actionable: `False` / `False`.
- Full workflow ready/actionable: `None` / `None`.

## Decision
- Gate result: `112315_bybit_momentum_downstream=ordered_chain_exercised_but_provider_authority_and_runtime_promotion_fail_closed`.
- The ordered chain ran on a positive public-provider branch, but this is not promotion evidence because source provider authority failed before AQ.
- `promotion_allowed=false`.
- `trade_usable=false`.
- `update_goal=false`.

## Artifacts
- JSON: `docs/experiments/actionable-regime-confidence/runs/20260512T112904+0800-codex-112315-provider-matrix-aq-readback-v1/112315-bybit-momentum-downstream-v1/112315_bybit_momentum_downstream_v1.json`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260512T112904+0800-codex-112315-provider-matrix-aq-readback-v1/checks/112315_bybit_momentum_downstream_v1_assertions.out`
- Command output: `docs/experiments/actionable-regime-confidence/runs/20260512T112904+0800-codex-112315-provider-matrix-aq-readback-v1/command-output`
- State dir: `docs/experiments/actionable-regime-confidence/runs/20260512T112904+0800-codex-112315-provider-matrix-aq-readback-v1/state_downstream_bybit`
