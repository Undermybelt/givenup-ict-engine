# Regime Downstream Consumer Contract v1

Run ID: `20260511T160441+0800-codex-regime-downstream-consumer-contract-v1`

## Decision

- Generated runtime-shape `regime-consumer-bundle/v1` templates for all `5/5` active lanes.
- Templates preserve `MainRegimeV2` and `DirectOverlay::Manipulation` labels; no old child/sub-regime labels are used.
- Current runtime can consume these templates as read-only trace/pre-Bayes diagnostics.
- BBN soft-evidence mutation is intentionally neutral because templates are `trade_usable=false` and the current adapter does not directly map `MainRegimeV2` labels.
- Full objective achieved: `false`; `update_goal=false`.

## Runtime Surfaces

| Consumer | Surface | Status | Limit |
|---|---|---|---|
| analyze/report trace | `RegimeConsumerBundleAdapter::trace_entries` | `supported_now` | trace/report context only; not a completion claim |
| pre-bayes diagnostics | `append_read_only_bbn_diagnostics` | `supported_now_read_only` | diagnostic assignments only |
| BBN soft evidence mutation | `apply_bbn_soft_evidence_to_pre_bayes_filter` | `intentionally_neutral` | do not enable BBN mutation from these templates until protocol maps MainRegimeV2 directly |
| execution tree | `execution_tree_hint trace` | `supported_as_transition_guardrail_hint` | does not force trade entry or path acceptance |
| CatBoost/path-ranker | `path_ranker_context` | `template_only_currently_unconsumed` | requires later runtime wiring before it can affect ranking |

## Templates

| Regime | Template | Label | Trade usable |
|---|---|---|---:|
| Bull | `docs/experiments/actionable-regime-confidence/runs/20260511T160441-codex-regime-downstream-consumer-contract-v1/downstream-consumer-contract/bundle-templates/bull_regime_consumer_bundle_template_v1.json` | `MainRegimeV2::Bull` | `false` |
| Bear | `docs/experiments/actionable-regime-confidence/runs/20260511T160441-codex-regime-downstream-consumer-contract-v1/downstream-consumer-contract/bundle-templates/bear_regime_consumer_bundle_template_v1.json` | `MainRegimeV2::Bear` | `false` |
| Sideways | `docs/experiments/actionable-regime-confidence/runs/20260511T160441-codex-regime-downstream-consumer-contract-v1/downstream-consumer-contract/bundle-templates/sideways_regime_consumer_bundle_template_v1.json` | `MainRegimeV2::Sideways` | `false` |
| Crisis | `docs/experiments/actionable-regime-confidence/runs/20260511T160441-codex-regime-downstream-consumer-contract-v1/downstream-consumer-contract/bundle-templates/crisis_regime_consumer_bundle_template_v1.json` | `MainRegimeV2::Crisis` | `false` |
| Manipulation | `docs/experiments/actionable-regime-confidence/runs/20260511T160441-codex-regime-downstream-consumer-contract-v1/downstream-consumer-contract/bundle-templates/manipulation_regime_consumer_bundle_template_v1.json` | `DirectOverlay::Manipulation` | `false` |

## Adapter Boundary

- Adapter: `src/application/regime/consumer_bundle_adapter.rs`
- Supports schema now: `true`
- Explicit MainRegimeV2 mapper present now: `false`
- Contract decision: keep these templates read-only until runtime supports MainRegimeV2 labels directly, without translating through old child/sub-regime labels.

## Artifacts

- JSON: `docs/experiments/actionable-regime-confidence/runs/20260511T160441-codex-regime-downstream-consumer-contract-v1/downstream-consumer-contract/regime_downstream_consumer_contract_v1.json`
- Surface CSV: `docs/experiments/actionable-regime-confidence/runs/20260511T160441-codex-regime-downstream-consumer-contract-v1/downstream-consumer-contract/regime_downstream_consumer_contract_v1_surfaces.csv`
- Template index: `docs/experiments/actionable-regime-confidence/runs/20260511T160441-codex-regime-downstream-consumer-contract-v1/downstream-consumer-contract/regime_consumer_bundle_template_index_v1.csv`
- Bundle templates: `docs/experiments/actionable-regime-confidence/runs/20260511T160441-codex-regime-downstream-consumer-contract-v1/downstream-consumer-contract/bundle-templates`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260511T160441-codex-regime-downstream-consumer-contract-v1/checks/regime_downstream_consumer_contract_v1_assertions.out`
