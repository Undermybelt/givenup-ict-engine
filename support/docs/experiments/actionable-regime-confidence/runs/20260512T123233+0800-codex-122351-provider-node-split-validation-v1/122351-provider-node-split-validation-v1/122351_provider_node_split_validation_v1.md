# 122351 Provider Node Split Validation v1

Run id: `20260512T123233+0800-codex-122351-provider-node-split-validation-v1`
Source scan: `20260512T122351+0800-codex-115700-provider-evidence-node-scan-v1`

## Result
- Rows validated: `237` across `6` providers and `2` branch paths.
- Feature priority order: `['provider_rv_median_24h', 'provider_return_dispersion_24h', 'provider_range_pos_median_24h']`.
- Gate: `122351_provider_node_split_validation_v1=provider_rv_internal_priority_but_external_validation_required_no_promotion`.

## Feature Decisions
- `provider_rv_median_24h`: source separation `0.463486`, internal high>low guard `True`, eligible split groups `14`, failed split groups `0`.
- `provider_return_dispersion_24h`: source separation `0.372418`, internal high>low guard `True`, eligible split groups `12`, failed split groups `0`.
- `provider_range_pos_median_24h`: source separation `0.343519`, internal high>low guard `False`, eligible split groups `14`, failed split groups `1`.

## Decision
- Best internal candidate: `provider_rv_median_24h`.
- This is still candidate-only. It is BTC-only, 1h-only, and execution remains observe-only.
- `bbn_likelihood_mutation_allowed=false`.
- `promotion_allowed=false`.
- `trade_usable=false`.
- `update_goal=false`.
