# 115130 Downstream Layered Validator v1

Run id: `20260512T120432+0800-codex-115130-downstream-layered-validator-v1`
Source AQ root: `20260512T115130+0800-codex-113833-ibkr-longer-duration-six-provider-aq-v1`

## Scope
Read the settled `115130` six-provider AQ runtime packet and validate its provider-rooted real-trade JSONL rows before any BBN, CatBoost/path-ranker, or execution-tree learning use.

This artifact does not edit ict-engine runtime code, does not apply real trades to the BBN CPT, does not run promotion, and does not call `update_goal`.

## Readback
- Real-trade files: `12`.
- Real-trade rows parsed: `211`.
- Rows with complete four-part branch path: `211`.
- Rows with realized outcome/PnL: `211`.
- Rows accepted as market-factor negative samples: `0`.
- Rows quarantined as chain-contract negative samples: `211`.

## Validator Decision
The raw Auto-Quant trade rows are parseable and branch-carrying, but every row is missing the layered downstream contract fields required by Board B:

- provider provenance object with same-root authority key
- Pre-Bayes/filter state
- BBN posterior state
- CatBoost/path-ranker label
- execution-tree decision
- failure reason
- quality weight

Therefore the rows remain `chain_contract_negative_sample` evidence only. They are not eligible to update BBN likelihood tables, regime-conditioned win rate, CatBoost/path-ranker labels, or execution-tree branch weights.

## Gate
- `count_once:120432_115130_downstream_layered_validator_v1`.
- `pass:real_trade_rows_parsed_211`.
- `pass:branch_complete_rows_211`.
- `pass:outcome_rows_211`.
- `fail_closed:market_factor_rows_accepted_0`.
- `fail_closed:all_rows_missing_downstream_layered_contract`.
- `chain_contract_negative_sample_rows=211`.
- `promotion_allowed=false`.
- `trade_usable=false`.
- `update_goal=false`.

## Next
Repair the provider-rooted trade JSONL bridge so each row carries provider provenance and downstream readback fields, then rerun Pre-Bayes/filter -> BBN -> CatBoost/path-ranker -> execution tree before allowing any market/factor negative training use.
