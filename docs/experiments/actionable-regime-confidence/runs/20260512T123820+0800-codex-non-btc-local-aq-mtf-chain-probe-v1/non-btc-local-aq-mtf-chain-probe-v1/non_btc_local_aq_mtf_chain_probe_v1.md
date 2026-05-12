# Non-BTC Local Auto-Quant MTF Chain Probe v1

Run id: `20260512T123820+0800-codex-non-btc-local-aq-mtf-chain-probe-v1`

## Scope
Use existing local Auto-Quant feather data for non-BTC / non-1h context checks, convert it to ict-engine candle JSON, then run ict-engine factor-research, analyze, Pre-Bayes/BBN workflow readback, policy training status, path-ranking export, and market-state validation.

This does not mutate production BBN CPDs, CatBoost models, execution-tree gates, or repo runtime code.

## Readback
- Markets: `ETH_USDT, NQ_USD`.
- Converted candle files: `6`.
- Max regime probability observed: `0.742080`.
- Accepted >=95% regime contexts: `0`.
- Execution-ready/actionable contexts: `0`.
- Gate: `non_btc_local_aq_mtf_chain_probe_fail_closed`.

## Market Summary
- `ETH_USDT` family `crypto_non_btc` active_regime `range` confidence `0.504871249965485` max_prob `0.7420795759662269` pre_bayes `pass_neutralized` execution_gate `execution_blocked` candidate `no_trade` actionable `False`.
- `NQ_USD` family `tradfi_futures` active_regime `range` confidence `0.14423512439311514` max_prob `0.32824868142013397` pre_bayes `observe_only` execution_gate `execution_blocked` candidate `no_trade` actionable `False`.

## Decision
- Candidate non-BTC / non-1h local Auto-Quant contexts were exercised through ict-engine, but they do not satisfy Board A acceptance.
- `production_likelihood_mutation=false`.
- `promotion_allowed=false`.
- `trade_usable=false`.
- `update_goal=false`.

## Artifacts
- JSON: `docs/experiments/actionable-regime-confidence/runs/20260512T123820+0800-codex-non-btc-local-aq-mtf-chain-probe-v1/non-btc-local-aq-mtf-chain-probe-v1/non_btc_local_aq_mtf_chain_probe_v1.json`
- Market summary CSV: `docs/experiments/actionable-regime-confidence/runs/20260512T123820+0800-codex-non-btc-local-aq-mtf-chain-probe-v1/non-btc-local-aq-mtf-chain-probe-v1/market_summary_v1.csv`
- Converted candle JSON root: `docs/experiments/actionable-regime-confidence/runs/20260512T123820+0800-codex-non-btc-local-aq-mtf-chain-probe-v1/provider-data-json`
- Command output root: `docs/experiments/actionable-regime-confidence/runs/20260512T123820+0800-codex-non-btc-local-aq-mtf-chain-probe-v1/command-output`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260512T123820+0800-codex-non-btc-local-aq-mtf-chain-probe-v1/checks/non_btc_local_aq_mtf_chain_probe_v1_assertions.out`
