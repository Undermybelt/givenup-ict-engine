# Provider-Provenanced ETH Kraken MTF v1

Run id: `20260512T125753+0800-codex-provider-provenanced-eth-kraken-mtf-v1`

Gate result: `provider_provenanced_eth_kraken_mtf_v1=kraken_mtf_provider_data_ready_auto_quant_prepare_ready_tomac_pair_whitelist_fail_closed`

## Scope

This diagnostic checks one provider-provenanced ETH/Kraken MTF path before any six-provider downstream promotion claim.

- Provider: `kraken-spot`.
- Symbol/pair: `ETHUSD` source candles, `ETHKRAKEN/USD` Auto-Quant workspace pair.
- Timeframes fetched: source `1h`, `4h`, and `1d`.
- State roots: `state_eth_kraken_mtf/` and `state_ethkraken_mtf/`.
- This run does not mutate production BBN CPDs, CatBoost/path-ranker models, execution-tree gates, or the board cursor.

## Provider Evidence

- `1h`: `721` rows from `2026-04-12T04:00:00Z` to `2026-05-12T04:00:00Z`.
- `4h`: `721` rows from `2026-01-12T04:00:00Z` to `2026-05-12T04:00:00Z`.
- `1d`: `721` rows from `2024-05-22T00:00:00Z` to `2026-05-12T00:00:00Z`.
- All fetch and JSON conversion commands exited `0`.

## Runtime Evidence

- `analyze_ethkraken_mtf` and `analyze_kraken_eth_mtf` exited `0`.
- `factor_research_auto_quant`, `factor_research_auto_quant_after_prepare`, and `factor_research_ethkraken_before_prepare` exited `0`.
- `auto_quant_prepare` and `auto_quant_prepare_ethkraken` exited `0`.
- Auto-Quant dependency pin: `TraderAlice/Auto-Quant` commit `34ba6b6ee6aa69813a50a72158d4c089d97afb96`.
- Workspace profile was `synthetic_ohlcv`, source data `kraken_ethusd_1h.json`, pair `ETHKRAKEN/USD`, base timeframe `1h`, additional timeframes `4h` and `1d`.

## Fail-Closed Readback

- `auto_quant_run_tomac`, `auto_quant_run_tomac_workspace`, and `auto_quant_run_tomac_after_prepare` all exited `1`.
- Two Freqtrade runs failed with `OperationalException: No pair in whitelist`.
- One command used the wrong Python context and failed with `ModuleNotFoundError: No module named 'freqtrade'`.
- No TOMAC strategy metrics, signal export, real-trade rows, profitability packet, Pre-Bayes -> BBN -> CatBoost/path-ranker -> execution-tree downstream closure, or promotion evidence exists for this root.
- The analyze surface remained observe/no-trade: `pre_bayes_gate_status=pass_neutralized`, `candidate_status=no_trade`, `review_status=observe`, `execution_gate_status=execution_blocked`, and execution readiness `0.43776422616823835`.

## Decision

- Evidence class: `infrastructure_negative_sample`.
- Useful for provider/AQ readiness and pair-whitelist repair only.
- Market/factor learning quality weight: `0`.
- `promotion_allowed=false`.
- `trade_usable=false`.
- `update_goal=false`.

## Artifacts

- Provider data: `data/kraken_ethusd_1h.json`, `data/kraken_ethusd_4h.json`, `data/kraken_ethusd_1d.json`.
- Provider provenance: `data/kraken_ethusd_1h.json.provenance.json`, `data/kraken_ethusd_4h.json.provenance.json`, `data/kraken_ethusd_1d.json.provenance.json`.
- Command outputs: `command-output/`.
- Exit checks: `checks/`.
- Summary JSON: `provider-provenanced-eth-kraken-mtf-v1/provider_provenanced_eth_kraken_mtf_v1.json`.
- Checklist: `provider-provenanced-eth-kraken-mtf-v1/prompt_to_artifact_checklist_provider_provenanced_eth_kraken_mtf_v1.csv`.
- Assertions: `checks/provider_provenanced_eth_kraken_mtf_v1_assertions.out`.
