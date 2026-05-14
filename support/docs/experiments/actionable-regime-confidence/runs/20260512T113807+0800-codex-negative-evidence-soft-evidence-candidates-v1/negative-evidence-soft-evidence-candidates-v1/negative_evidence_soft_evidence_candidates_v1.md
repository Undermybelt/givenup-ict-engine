# Negative Evidence Soft Evidence Candidates v1

Run root: `docs/experiments/actionable-regime-confidence/runs/20260512T113807+0800-codex-negative-evidence-soft-evidence-candidates-v1`

Source feedback pack: `docs/experiments/actionable-regime-confidence/runs/20260512T112916+0800-codex-negative-evidence-bbn-feedback-v1/negative-evidence-bbn-feedback-v1/negative_evidence_bbn_feedback_v1.json`

## Decision

Gate: `negative_evidence_soft_evidence_candidates_v1=candidate_soft_evidence_pack_created_no_runtime_injection_no_promotion`.

This artifact converts the previous negative-evidence classification into candidate BBN soft-evidence nodes. It does not inject evidence into runtime state, mutate priors, promote any branch, approve selected history, approve source/control evidence, or call `update_goal`.

## Candidate Nodes

- `provider_reliability.tradingview_mcp.default_credentials`: mixed evidence, degraded-biased.
- `provider_reliability.tradingview_mcp.local_stdio`: degraded-biased because BTC local-stdio routing is unreliable.
- `provider_reliability.ibkr.historical_rows`: healthy-biased but still blocked from default provider authority.
- `workflow_gate.pre_bayes_available`: empty-biased from repeated fail-closed readbacks.
- `workflow_gate.path_ranker_mature_support.111403_direct_fallback`: insufficient-biased.
- `workflow_gate.path_ranker_mature_support.104703_exact_branch`: ready-biased locally, but only for copied-state path-ranker readiness.
- `strategy_regime_fit.ProviderCryptoMomentumStateV1.Bull`: weak negative branch-fit likelihood, not parent-regime prior evidence.
- `execution_tree.branch_admission`: fail-closed-biased.

## Runtime Guard

Before runtime use:

- map every candidate `node_id` to concrete BBN nodes and state ordering;
- verify vector cardinality against the runtime node;
- run `EvidenceManager` validation from `src/bbn/evidence.rs`;
- keep provider/tool, maturity, and execution-gate evidence out of parent regime priors;
- add tests that fail if any distribution does not sum to `1.0`.

## Net Effect

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

## Next

Use this only as a candidate map for a later implementation/test slice. The active provider-matrix AQ readback remains separate and should settle before any same-root AQ/downstream promotion claim.
