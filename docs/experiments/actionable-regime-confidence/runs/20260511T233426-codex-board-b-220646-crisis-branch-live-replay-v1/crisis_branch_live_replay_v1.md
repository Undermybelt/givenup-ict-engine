# Crisis Branch Live Replay v1

Run id: `20260511T233426+0800-codex-board-b-220646-crisis-branch-live-replay-v1`

Purpose: complete the partial `233426` replay root after the `220646` exact Crisis branch was blocked by `block_crowded` in `231800` and classified as execution-admissibility feedback in `233358`.

## Context

- Accepted Board A context: `BoardA_regime_factor_consumer_map_MainRegimeV2_roots_plus_scoped_manipulation`.
- Recipe: `SourceRootStopCarryLongHorizonV1`.
- Branch path: `Crisis -> CrisisReliefCarry -> StopManagedPanicRecovery -> SourceRootStopCarryLongHorizonV1:crisis_carry_h8_sl048_tp12`.
- Upstream RC-SPA: `85.7407`, price roots `4/4` passed, scoped direct Manipulation component pass unchanged from `205047`.
- Runtime code changed: false.
- Thresholds relaxed: false.
- Promotion claim: false.

## Commands

- `cargo build --quiet --bin ict-engine`
- `./target/debug/ict-engine provider-status --agent`
- `./target/debug/ict-engine auto-quant-status --state-dir <run_root>/state_crisis_branch_live_replay_v1/auto-quant --output-format json`
- `./target/debug/ict-engine analyze-live --symbol SRC_ROOT_CARRY_LONG_220646 --futures-symbol NQ=F --spot-symbol QQQ --options-symbol QQQ --spot-kind etf --state-dir <run_root>/state_crisis_branch_live_replay_v1 --agent --regime-consumer-bundle <220646>/downstream-chain/regime-bundles/crisis_regime_consumer_bundle_v1.json --regime-consumer-bundle-strict --apply-regime-bundle-bbn-soft-evidence`
- `./target/debug/ict-engine pre-bayes-status --symbol SRC_ROOT_CARRY_LONG_220646 --state-dir <run_root>/state_crisis_branch_live_replay_v1 --refresh --output-format json`
- `./target/debug/ict-engine workflow-status --symbol SRC_ROOT_CARRY_LONG_220646 --state-dir <run_root>/state_crisis_branch_live_replay_v1 --refresh --phase structural-recommended-path-bundle --output-format json`
- `./target/debug/ict-engine workflow-status --symbol SRC_ROOT_CARRY_LONG_220646 --state-dir <run_root>/state_crisis_branch_live_replay_v1 --refresh --phase execution-candidate --output-format json`
- `./target/debug/ict-engine policy-training-status --symbol SRC_ROOT_CARRY_LONG_220646 --state-dir <run_root>/state_crisis_branch_live_replay_v1 --output-format json`
- `./target/debug/ict-engine workflow-status --symbol SRC_ROOT_CARRY_LONG_220646 --state-dir <run_root>/state_crisis_branch_live_replay_v1 --refresh --output-format json`

All command exits were `0`.

## Provider Readback

- yfinance live runtime: ready, `native_yfinance_runtime_available`.
- yfinance market data: ready, `public_yahoo_http_endpoints`.
- TradingView MCP: ready, `mcp_url_and_api_key_available`.
- Kraken CLI: ready, `kraken_cli_config_detected`.
- Kraken public market-data adapter: unhealthy, `python3_provider_dependencies_missing`.
- IBKR market data: unhealthy, `ibkr_runtime_dependencies_missing_with_gateway_reachable`.
- IBKR bridge: unhealthy, `ibkr_bridge_runtime_dependencies_missing_with_gateway_reachable`.

Auto-Quant status in this isolated replay state is `missing_dependency/bootstrap_needed`; this replay consumed existing `220646` recipe/backtest artifacts and refreshed downstream ict-engine surfaces only.

## Downstream Readback

- Analyze-live exit: `0`.
- Analyze-live decision: `Observe only`.
- Pre-Bayes gate: `pass_neutralized`.
- Pre-Bayes policy version: `318900600c5e8cf2`.
- Pre-Bayes canonical structural regime: `range`, confidence `0.5619249343265972`.
- BBN soft evidence remained keyed to the loaded bundle context: `market_regime={range:0.65,bull:0.175,bear:0.175}`.
- Structural bundle selected exact path: `Crisis -> CrisisReliefCarry -> StopManagedPanicRecovery -> SourceRootStopCarryLongHorizonV1:crisis_carry_h8_sl048_tp12`.
- Path-ranker runtime: `using_history_scores`; raw score `0.5372559832604725`.
- Ranker validation ready: production `274/30`, observation `48/30`, raw scored mature `275/30`.
- Execution candidate: `ready`, actionable `true`.
- Execution candidate review: `observe`, reason `candidate_not_comparable_same_data_factor_required`.
- Full workflow latest promotable artifact: `null`.

## Delta From 231800

`231800` blocked the same exact branch with `block_crowded` and readiness `0.4433 < 0.45` under `RangeConsolidation/WideRange`.

This replay kept the same exact branch identity but returned `fill_viable` / `observe` under the same broad `RangeConsolidation/WideRange` context:

- execution branch: `fill_viable`
- gate: `observe`
- bias: `passive`
- execution score: `0.5637168720248323`
- reason: `market_state=RangeConsolidation/WideRange | execution=observe/fill_viable/passive | ranker=history_path/unknown/ready`

The change is useful execution-admissibility feedback, but it is not a promotion. The review layer rejected direct comparability with `candidate_not_comparable_same_data_factor_required`.

## Result

Gate result: `crisis_branch_live_replay_v1=exact_branch_preserved_execution_observe_not_promoted`.

Promotion allowed: false.

Next action: use the `block_crowded -> fill_viable` context delta as B2R nursery execution-admissibility feedback for the exact Crisis branch, and only rerun promotion after same-data comparability or explicit dataset selection closes the review blocker.
