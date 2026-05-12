# 115700 Provider Evidence Node Cross-Context Gate v1

Run id: `20260512T122933+0800-codex-115700-provider-evidence-node-cross-context-gate-v1`
Source scan: `20260512T122351+0800-codex-115700-provider-evidence-node-scan-v1`
Source enriched chain: `20260512T121347+0800-codex-115700-enriched-downstream-chain-v1`

## Scope
Validate the top provider evidence-node candidates from `122351` across feature bins, providers, chronology, branches, instrument family, and timeframe.
This is read-only candidate validation. It does not mutate BBN CPDs, CatBoost models, or execution-tree gates.

## Readback
- Rows checked: `237`.
- Features checked: `['provider_rv_median_24h', 'provider_return_dispersion_24h', 'provider_range_pos_median_24h', 'provider_return_median_abs_1h', 'provider_return_dispersion_4h']`.
- Best candidate remains `provider_rv_median_24h` best bin `high` with rows `78`, win rate `0.615385`, Wilson lower `0.504426`.
- Instrument families after strict normalization: `['BTC']`.
- Timeframes: `['1h']`.
- Pre-Bayes gates: `{'pass_neutralized': 237}`.
- Execution reviews: `{'observe': 237}`.
- Max BBN probability: `0.747688`.

## Decision
- Gate: `provider_evidence_node_cross_context_gate_fail_closed`.
- Candidate provider evidence nodes are useful for the next BBN feature design queue, but none is an accepted Board A regime gate.
- `production_likelihood_mutation=false`.
- `promotion_allowed=false`.
- `trade_usable=false`.
- `update_goal=false`.

## Artifacts
- JSON: `docs/experiments/actionable-regime-confidence/runs/20260512T122933+0800-codex-115700-provider-evidence-node-cross-context-gate-v1/115700-provider-evidence-node-cross-context-gate-v1/115700_provider_evidence_node_cross_context_gate_v1.json`
- Feature bins: `docs/experiments/actionable-regime-confidence/runs/20260512T122933+0800-codex-115700-provider-evidence-node-cross-context-gate-v1/115700-provider-evidence-node-cross-context-gate-v1/feature_bin_summary_v1.csv`
- Best-bin contexts: `docs/experiments/actionable-regime-confidence/runs/20260512T122933+0800-codex-115700-provider-evidence-node-cross-context-gate-v1/115700-provider-evidence-node-cross-context-gate-v1/feature_best_bin_contexts_v1.csv`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260512T122933+0800-codex-115700-provider-evidence-node-cross-context-gate-v1/checks/115700_provider_evidence_node_cross_context_gate_v1_assertions.out`
