# 115431 Layered Negative Evidence Validator v1

Run id: `20260512T120320+0800-codex-115431-layered-negative-evidence-validator-v1`

## Scope

This read-only validator checks whether the provider-rooted raw trade artifacts from `20260512T115431+0800-codex-six-provider-aq-first-class-ibkr-v1` satisfy the Board B layered negative-evidence minimum schema before any BBN, CatBoost/path-ranker, or execution-tree learning use.

It does not run `auto-quant-ingest-real-trades`, does not mutate ict-engine state, does not approve selected history/source-control evidence, does not promote a candidate, and does not call `update_goal`.

## Source Evidence

- Source run: `docs/experiments/actionable-regime-confidence/runs/20260512T115431+0800-codex-six-provider-aq-first-class-ibkr-v1`
- Source report: `docs/experiments/actionable-regime-confidence/runs/20260512T115431+0800-codex-six-provider-aq-first-class-ibkr-v1/six-provider-aq-first-class-ibkr-v1/six_provider_aq_first_class_ibkr_v1.md`
- Raw trade files checked: `12`
- Raw trade rows visible in workspace files: `185`
- Source report authority rows: `148` total trades, `8` strategies with metrics, `4` successful AQ provider runs

## Validator Findings

- The raw trade records contain exchange/backtest fields such as `open_date`, `close_date`, `profit_ratio`, `exit_reason`, `pair`, and order details.
- They do not carry row-level `branch_path`.
- They do not carry the four explicit branch fields: `main_regime`, `sub_regime`, `sub_sub_regime_or_profit_factor`, and `profit_factor`.
- They do not carry row-level `provider_provenance`, `pre_bayes_filter_state`, `bbn_posterior`, `catboost_path_ranker_label`, `execution_tree_decision`, `failure_reason`, or `quality_weight`.
- Provider and strategy identity can be inferred from directory/file names, but that is not enough for market-factor attribution under the Board B direction contract.
- The workspace contains raw trade files for yfinance and TVR paths even though the source report says yfinance fetch returned `0` rows / exit `2` and TVR fetch returned `0` rows / exit `1`. This is an artifact-authority mismatch and must not become market-factor evidence.

## Classification

- `market_factor_negative_sample`: `0` rows accepted.
- `chain_contract_negative_sample`: `185` workspace raw trade rows rejected from market-factor use because required branch and downstream attribution fields are absent.
- `infrastructure_negative_sample`: source packet remains provider-authority limited because yfinance and TVR failed inside the source report, while the workspace still has derived files for those lanes.

## Decision

The `115431` first-class IBKR raw trade files are useful AQ/runtime evidence, but they are not valid market-factor negative samples and must not be fed into BBN likelihoods, CatBoost/path-ranker labels, or execution-tree branch weights as-is.

They may be used only after an enrichment/ingestion step materializes the minimum observation schema:

- `branch_path`
- `main_regime`
- `sub_regime`
- `sub_sub_regime_or_profit_factor`
- `profit_factor`
- `provider_provenance`
- `pre_bayes_filter_state`
- `bbn_posterior`
- `catboost_path_ranker_label`
- `execution_tree_decision`
- `outcome`
- `failure_reason`
- `quality_weight`

## Gate

- `count_once:115431_layered_negative_evidence_validator_v1`.
- `pass:source_raw_trade_files_checked_12`.
- `pass:source_workspace_raw_trade_rows_visible_185`.
- `pass:source_report_authority_rows_148`.
- `fail_closed:accepted_market_factor_negative_rows_0`.
- `fail_closed:missing_branch_path_all_raw_rows`.
- `fail_closed:missing_four_part_branch_fields_all_raw_rows`.
- `fail_closed:missing_provider_provenance_all_raw_rows`.
- `fail_closed:missing_pre_bayes_bbn_catboost_execution_tree_fields_all_raw_rows`.
- `fail_closed:workspace_raw_rows_do_not_match_source_report_authority_rows`.
- `fail_closed:yfinance_and_tvr_provider_fetch_failures_not_market_factor_negatives`.
- `promotion_allowed=false`.
- `trade_usable=false`.
- `update_goal=false`.

## Next

Do not ingest these raw trade files as market-factor negative samples. The next valid downstream slice is an enrichment step that writes provider provenance and the complete regime branch path onto each trade row, then runs `auto-quant-ingest-real-trades` only after the validator can accept the row-level schema.
