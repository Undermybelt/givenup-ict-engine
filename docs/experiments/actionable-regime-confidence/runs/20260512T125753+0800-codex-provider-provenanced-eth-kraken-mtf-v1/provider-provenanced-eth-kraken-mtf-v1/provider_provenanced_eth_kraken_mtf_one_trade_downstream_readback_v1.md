# Provider-Provenanced ETH Kraken MTF One-Trade Downstream Readback v1

Generated: 2026-05-12T13:45:10+0800

Run id: `20260512T125753+0800-codex-provider-provenanced-eth-kraken-mtf-v1`

Gate result: `fail_closed:one_trade_not_mature_no_execution_candidate`

## Scope

This is an append-only correction/readback for the settled `125753` root after a later pair-alias timerange retry exported and ingested one ETHKRAKEN TOMAC trade.

It does not count `125753` again, does not satisfy the six-provider lock, does not mutate production BBN CPDs, CatBoost/path-ranker models, or execution-tree gates, does not promote a candidate, does not make a live-trade claim, and does not call `update_goal`.

## Auto-Quant and Provider Evidence

- Required provider authority for Board B is not met: this root is Kraken-only, not same-root six-provider.
- Kraken spot ETHUSD provider candles remain provider-provenanced with `local_cache_replay=false`.
- `auto_quant_run_tomac_pair_alias_timerange` exited `0` for `ETHKRAKEN/USD`.
- TOMAC metrics: `1` trade, total profit `0.77%`, win rate `100%`, Sharpe `-100.0000`, Sortino `-100.0000`, Calmar `-100.0000`, profit factor `0.0000`, max drawdown `0.00%`.
- PFETHUSD futures retry also exited `0`, but produced `0` trades and `0.00%` total profit. It is not a profitability packet.

## Real-Trade Ingest

- Export command: `export_eth_kraken_tomac_real_trades.exit=0`.
- Ingest command: `ingest_eth_kraken_tomac_real_trades.exit=0`.
- Ledger artifact id: `auto_quant_real_trades_ETH_KRAKEN_20260512T052029.670414000Z`.
- Ingest result: `trades_applied=1`, `trades_invalid=0`, `feedback_records_inserted=1`, content hash `e35aebcd068f00c6`.
- Rooted branch path in the ingested row:
  `TrendExpansion -> BullTrendAcceleration -> MultiTimeframeIntradayResonance -> TomacNQ_KillzoneBreakout`.

## Downstream Readback

Commands were run against isolated state root `state_eth_kraken_mtf/`:

- `pre_bayes_status_eth_kraken_after_one_trade_ingest.exit=0`.
- `policy_training_status_eth_kraken_after_one_trade_ingest.exit=0`.
- `export_structural_path_ranking_target_eth_kraken_after_one_trade_ingest.exit=0`.
- `workflow_status_execution_candidate_eth_kraken_after_one_trade_ingest.exit=0`.
- `workflow_status_full_eth_kraken_after_one_trade_ingest.exit=0`.

Readback:

- Pre-Bayes/filter stayed `pass_neutralized`.
- Canonical structural confidence was `0.5574970918447152`, below the Board B acceptance band.
- Selected path probability remained absent.
- Policy training stayed unusable for BBN/CatBoost entry models: both listed entry models had `ready=false` and `matched_rows=0`.
- Structural path-ranking export wrote `3` current rows, `mature_rows=1`, `rows_with_calibrated_path_prob=0`, `rows_with_path_prob_lower_bound=0`, and `rows_with_execution_gate_status=0`.
- The current structural export preserved the exact rooted profitability branch path in row rank `1`.
- Workflow execution candidate remained absent/null; the latest analyze surface stayed `promotion_status=observe`, `execution_gate_status=execution_blocked`, and `execution_readiness=0.43776422616823835`.
- BBN structure existed in the isolated state (`7` nodes, `8` edges), but no Auto-Quant prior/posterior mutation was applied from this one-trade packet.

## Decision

- `support_once:125753_eth_kraken_one_trade_downstream_readback_v1`.
- `evidence_class:single_provider_aq_reachability_plus_runtime_negative_sample`.
- `pass:auto_quant_tomac_pair_alias_timerange_exit0`.
- `pass:one_real_trade_exported_and_ingested`.
- `pass:regime_profit_branch_path_preserved_in_trade_row`.
- `pass:structural_path_export_preserved_branch_path`.
- `fail_closed:single_provider_only_kraken`.
- `fail_closed:trade_count_1_below_maturity_floor`.
- `fail_closed:pfethusd_trade_count_0`.
- `fail_closed:pre_bayes_pass_neutralized`.
- `fail_closed:canonical_confidence_0.5574970918447152_below_0.95`.
- `fail_closed:selected_path_probability_absent`.
- `fail_closed:catboost_entry_model_matched_rows_0`.
- `fail_closed:path_prob_lower_bound_absent`.
- `fail_closed:execution_candidate_null`.
- `fail_closed:execution_gate_status_execution_blocked`.
- `promotion_allowed=false`.
- `trade_usable=false`.
- `update_goal=false`.

## Next

Do not repeat this one-trade Kraken-only shape. A useful continuation should either:

- continue the stronger same-root six-provider ETH line where provider authority and CatBoost runtime already exist but Pre-Bayes/BBN/execution admission remain fail-closed, or
- rebuild ETHKRAKEN with enough provider-owned TOMAC observations before feeding likelihoods, CatBoost/path-ranker labels, or execution-tree branch weights.
