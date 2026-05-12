# 120630 / 115700 Layered Post-Chain Validator v1

Run id: `20260512T121542+0800-codex-120630-115700-layered-postchain-validator-v1`
Source chain: `20260512T120630+0800-codex-115700-six-provider-1h-downstream-chain-v1`
Source AQ packet: `20260512T115700+0800-codex-same-root-six-provider-1h-aq-v1`

## Result
- Rows read from source chain: `237`.
- Layer-contract complete rows emitted: `237`.
- Promotion-quality market/factor rows accepted: `0`.
- CatBoost score paths joined: `2`.
- Gate: `fail_closed:execution_observe_and_user_selected_history_missing`.

## Failure Counts
- `blocking_truth_user_selected_historical_data_missing`: `237`
- `execution_not_ready_or_actionable`: `237`
- `execution_review_not_promotional`: `237`

## Decision
- `120630` is valid same-root downstream-chain evidence for the effective `115700` AQ packet.
- The post-chain row contract is complete enough for audit readback, but the rows are not promotion-quality market/factor negatives because execution stayed observe-only and workflow still blocks on explicit historical-data selection.
- Do not feed these rows into production likelihood/ranker/execution weighting as accepted market-factor evidence until the execution-tree release gate and selected-history/source-control gate are unlocked.
- `promotion_allowed=false`.
- `trade_usable=false`.
- `update_goal=false`.

## Artifacts
- JSON: `docs/experiments/actionable-regime-confidence/runs/20260512T121542+0800-codex-120630-115700-layered-postchain-validator-v1/120630-115700-layered-postchain-validator-v1/120630_115700_layered_postchain_validator_v1.json`
- Layered rows: `docs/experiments/actionable-regime-confidence/runs/20260512T121542+0800-codex-120630-115700-layered-postchain-validator-v1/derived/115700_layered_postchain_rows.jsonl`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260512T121542+0800-codex-120630-115700-layered-postchain-validator-v1/checks/120630_115700_layered_postchain_validator_v1_assertions.out`
