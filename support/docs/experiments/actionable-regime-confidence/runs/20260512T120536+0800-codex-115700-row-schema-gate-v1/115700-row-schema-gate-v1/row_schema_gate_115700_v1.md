# 115700 Row Schema Gate v1

Run id: `20260512T120536+0800-codex-115700-row-schema-gate-v1`
Source root: `20260512T115700+0800-codex-same-root-six-provider-1h-aq-v1`

## Scope
Validate whether the settled 115700 same-root six-provider 1h AQ trade rows satisfy the Board B minimum observation schema before negative-evidence ingestion or downstream training use.

## Result
- Trade files checked: `12`.
- Total trade rows checked: `237`.
- Market/factor trainable rows accepted: `0`.
- Rows rejected from market/factor ingestion: `237`.
- Evidence class: `infrastructure_repair_candidate_plus_chain_contract_negative_sample`.
- Gate: `fail_closed:no_market_factor_negative_ingestion_rows`.

## Primary Rejection Reasons
- `missing_bbn_posterior`: `237` rows
- `missing_catboost_path_ranker_label`: `237` rows
- `missing_execution_tree_decision`: `237` rows
- `missing_failure_reason`: `237` rows
- `missing_pre_bayes_filter_state`: `237` rows
- `missing_provider_provenance`: `237` rows
- `missing_quality_weight`: `237` rows
- `stale_or_wrong_auto_quant_run_id`: `237` rows
- `stale_symbol_namespace`: `237` rows

## Source Id Readback
- `20260512T104902+0800-codex-board-b-yahoo-btc-pullback-precision-aq-v1`: `237` rows

## Decision
- 115700 is the strongest AQ-provider packet so far because all six provider fetches and all six AQ lanes succeeded on 1h-shaped data.
- Its emitted trade rows still cannot be used as market/factor negative samples because downstream attribution fields are absent and the row source ids remain stale.
- Feed the blocker to the exporter/enricher and chain-contract repair loop, not to BBN likelihood, CatBoost/path-ranker labels, or execution-tree branch weights.
- `promotion_allowed=false`.
- `trade_usable=false`.
- `update_goal=false`.

## Artifacts
- JSON: `docs/experiments/actionable-regime-confidence/runs/20260512T120536+0800-codex-115700-row-schema-gate-v1/115700-row-schema-gate-v1/row_schema_gate_115700_v1.json`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260512T120536+0800-codex-115700-row-schema-gate-v1/checks/row_schema_gate_115700_v1_assertions.out`
