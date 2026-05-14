# Branch-Leaf VWAP Reclaim AQ Terminal Readback v1

Root: `docs/experiments/actionable-regime-confidence/runs/20260512T190929+0800-codex-branch-leaf-vwap-reclaim-six-provider-aq-v1/`

Claim: `190929_branch_leaf_vwap_reclaim_six_provider_aq_replay_v1`

Branch path:

`Sideways -> SessionLiquidityMeanReversion -> VWAPReclaim -> session_vwap_reclaim_long_v1`

## Evidence

- Material generation exit: `checks/01_build_branch_leaf_materials.exit=0`.
- Material count: `6`.
- Provider count: `6`.
- Branch-keyed by construction: `true`.
- New provider fetch: `false`.
- Local cache replay: `true`.
- Cargo build exit: `checks/03_cargo_build.exit=0`.
- AQ batch exit: `checks/04_auto_quant_agent_material_batch.exit=0`.
- AQ dispatch exit: `checks/05_auto_quant_agent_material_dispatch.exit=0`.
- AQ rank exit: `checks/06_auto_quant_agent_material_rank.exit=0`.
- AQ rank artifact: `state/auto-quant/PROVIDER_BRANCH_LEAF_190929/auto_quant_agent_material_rank.20260512T112101.385Z.json`.

## AQ Rank Readback

| Provider unit | Trades | Win rate | Sharpe | Total profit |
|---|---:|---:|---:|---:|
| yfinance/YF SPY 1h | 128 | 45.3125% | 0.3273 | 5.24% |
| IBKR SPY 1h | 56 | 35.7143% | -0.3444 | -0.84% |
| Binance BTCUSDT 1h | 0 | 0.0% | 0.0 | 0.0% |
| Bybit BTCUSDT 1h | 0 | 0.0% | 0.0 | 0.0% |
| Kraken XBTUSD 1h | 0 | 0.0% | 0.0 | 0.0% |
| TradingViewRemix/TVR BTCUSD 1h | 0 | 0.0% | 0.0 | 0.0% |

## Classification

This packet is useful branch-attributed evidence, but it is not eligible for downstream market/factor learning yet.

- `evidence_class:cross_provider_disagreement_sample`
- `secondary_evidence_class:low_density_negative_sample`
- `branch_keyed_profitability_observation=true_by_material_construction`
- `adequate_cross_provider_trade_density=false`
- `provider_replay_only=true`
- `market_factor_negative_sample=false`
- `bbn_learning_allowed=false`
- `catboost_learning_allowed=false`
- `execution_tree_branch_weight_update_allowed=false`
- `promotion_allowed=false`
- `trade_usable=false`
- `update_goal=false`

## Contract Risk

The original material JSON and provider provenance matrix preserve `branch_path`, `main_regime`, `sub_regime`, `sub_sub_regime_or_profit_factor`, and `profit_factor`. The public AQ batch/rank artifact still emits provider-unit aggregate rows and does not itself carry the four branch fields in rank rows. Because each material package contains exactly one branch leaf, attribution is recoverable by material construction, but downstream handoff remains blocked until the branch fields are emitted or joined explicitly into the downstream observation rows.
