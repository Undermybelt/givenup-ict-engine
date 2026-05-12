# Negative Evidence BBN Feedback v1

Run root: `docs/experiments/actionable-regime-confidence/runs/20260512T112916+0800-codex-negative-evidence-bbn-feedback-v1`

Scope: classify already-registered fail-closed Board A evidence into BBN, Pre-Bayes, CatBoost/path-ranker, and execution-tree feedback classes. This artifact does not mutate runtime code, approve source/control evidence, approve selected history, promote a branch, or call `update_goal`.

## Decision

Gate: `negative_evidence_bbn_feedback_v1=structured_feedback_pack_created_no_promotion`.

Net Board A effect:

- accepted rows added: `0`
- mature rooted branch observations added: `0`
- source/control evidence acquired: `false`
- explicit selected-history approval: `false`
- canonical merge: `false`
- selected-data Auto-Quant promotion: `false`
- downstream promotion: `false`
- strict full objective: `false`
- trade usable: `false`
- promotion allowed: `false`
- update_goal: `false`

## Classification Rule

Negative evidence is usable, but only after layer typing:

- Market/strategy negative evidence may update `P(strategy_edge | regime, branch, provider_context)` with support weighting. It must not directly rewrite parent-regime priors from one short diagnostic.
- Provider/tool failures update provider reliability or observation-quality nodes. They do not imply the market regime is false.
- Maturity failures update sampling/gate nodes. They mean insufficient evidence, not negative market truth.
- Downstream fail-closed states update workflow-gate nodes such as Pre-Bayes availability, path-ranker maturity, runtime validity, and execution branch admission.

## Classified Evidence

### 105637 Provider-Linked AQ Probe

Read source: `provider_linked_aq_provenance_probe_v1.json`.

This is weak market/strategy negative evidence plus provider/tool and maturity evidence. YF, Kraken, Binance, and Bybit ran provider-linked AQ rows, but `ProviderCryptoMomentumStateV1` had only 1-2 trades per provider and negative total profit percentages. TradingView MCP failed in this root and the six-provider promotion matrix did not pass.

BBN use: weak negative likelihood for this strategy branch in this BTC 1h provider context only. Do not update the parent regime prior.

### 111309 Materialized Downstream Readback

Read source: `materialized_momentum_downstream_readback_v1.json`.

This is branch-specific negative outcome evidence plus downstream-gate evidence. The materialized branch had 7 rows, 3 wins, 4 losses, total PnL `-200.6922557`, Pre-Bayes remained empty, and execution stayed fail-closed.

BBN use: branch-fit negative evidence only after maturity support is sufficient. Current use remains fail-closed diagnostic.

### 111403 Ingest Bridge Fix

Read source: `105014_ingest_bridge_fix_v1.json`.

This is not market negative evidence. It proves ingestion/BBN persistence can hold 146 feedback rows, but Pre-Bayes stayed empty, raw scored mature stayed below promotion requirements, and execution remained fail-closed.

BBN use: workflow-gate evidence that BBN state presence is not enough without Pre-Bayes consumption and path-ranker maturity.

### 112303 Path-Ranker Direct Fallback

Read source: `111403_path_ranker_direct_fallback_v1.json`.

This is path-ranker maturity and runtime-validity evidence. The direct fallback artifact existed, but raw scored mature was `1/30`, production validation `0/30`, runtime status `enabled_registered_model_invalid`, and execution stayed fail-closed.

BBN use: maturity gate failure, not market negative evidence.

### 111602 / 111942 / 112030 Provider Readbacks

These are provider reliability evidence only:

- 111602: TradingView MCP QQQ rows present.
- 111942: IBKR QQQ daily rows present.
- 112030: TVR default BTC rows and IBKR PAXOS BTC rows present; TVR local-stdio route still unreliable for that BTC symbol.

BBN use: provider reliability and observation quality. They do not update market-regime priors until included in a same-root provider/AQ/downstream chain.

## Excluded Active Roots

`112315` and the follow-up work mutating `112900` were active at readback time. They are intentionally excluded until settled so this artifact does not classify half-written state.

## Next

The next safe BBN-facing step is to convert this JSON into either:

- soft-evidence candidates for provider reliability and workflow-gate nodes, or
- a same-root provider-matrix run after `112315` settles, followed by Auto-Quant -> Pre-Bayes/filter -> BBN -> CatBoost/path-ranker -> execution tree.

Do not promote from this feedback pack alone.
