# Derived Readback Summary v1

This addendum extracts the key nested fields from the raw command outputs for
`20260512T100422+0800-codex-board-a-readonly-gate-chain-refresh-after-092249-v1`.
It does not replace the raw outputs or promote the gate.

## Gate

- Gate result: `board_a_readonly_gate_chain_refresh_after_092249_v1=source_control_and_user_history_still_block_promotion`
- Source/control evidence acquired: `false`
- Explicit user-selected history: `false`
- Canonical merge: `false`
- Selected-data AutoQuant promotion: `false`
- Downstream promotion rerun: `false`
- Promotion allowed: `false`
- update_goal: `false`

## Provider / Auto-Quant

- `yfinance:live_runtime`: `ready`
- `yfinance:market_data`: `ready`
- `kraken_cli:local_runtime`: `ready`
- `tradingview_mcp:market_data`: `configured_runtime_unhealthy`
- `ibkr:market_data`: `configured_runtime_unhealthy`
- `kraken_public:market_data`: `configured_runtime_unhealthy`
- Auto-Quant dependency healthy: `true`
- Auto-Quant data ready: `false`
- Auto-Quant prepare: exit `1`, DNS/API access blocked.

## Chain

- `analyze-live`: exit `0`
- `pre-bayes-status`: exit `0`; gate `pass_neutralized`; canonical structural active regime `transition`; confidence `0.4011485769438987`
- `policy-training-status`: exit `0`; entry-model BBN/CatBoost pending with `matched_rows=0`; structural path-ranking target export missing/runtime disabled
- `export-structural-path-ranking-target`: exit `0`
- `workflow-status --phase execution-candidate`: exit `0`; `execution_gate_status=execution_blocked`; `execution_readiness=0.375134315318784`; `pre_bayes_gate_status=pass_neutralized`; `review_status=observe`

## Decision

This run proves the local surfaces can still be called, including Auto-Quant
status/prepare, yfinance live analysis, Pre-Bayes, BBN/CatBoost readiness,
structural path-ranking export, and execution-tree status. It does not satisfy
the strict Board A objective because there is no source/control unlock, no
explicit `HTF`/`MTF`/`LTF` user-selected history, no canonical merge, and no
promotion gate.
