# Board B Prompt-to-Artifact Checkpoint

Run root: `docs/experiments/actionable-regime-confidence/runs/20260512T141000+0800-codex-135318-real-trades-downstream-v1`
Source root: `docs/experiments/actionable-regime-confidence/runs/20260512T135318+0800-codex-long-history-es-nq-aq-staging-v1`

## Objective Restatement

Board B profitability evidence must be rooted by regime branch before factor training and must preserve the same branch through Auto-Quant, Pre-Bayes/filter, BBN, CatBoost/path-ranker, and execution-tree readbacks. The branch identity is:

```text
main_regime -> sub_regime -> sub_sub_regime_or_profit_factor -> profit_factor
```

This checkpoint is additive only. It does not edit Board B, does not claim promotion, and does not call `update_goal`.

## Prompt-to-Artifact Checklist

| Requirement | Current artifact | Status |
|---|---|---|
| Use the named Board B plan without disturbing other agents | Board B was read; no Board B write from this checkpoint | partial/read-only |
| Base profitability factor evidence on regime root and branch path | `derived/tomac_real_trades_nq.jsonl`, `derived/tomac_real_trades_es.jsonl` include `regime_profit_branch_path`, `main_regime`, `sub_regime`, `sub_sub_regime_or_profit_factor`, and `profit_factor` | partial |
| Run Auto-Quant first | Source root `135318` measured TOMAC; this root exported `192` real trades from that packet | done/support-only |
| Feed ict-engine real trades | `05_nq_ingest_real_trades.exit=0`; NQ applied `77/77`, invalid `0` | partial |
| Run Pre-Bayes/filter | Waiting on NQ analyze exit before `07_nq_pre_bayes_status` | not complete |
| Run BBN / policy-training | Waiting on NQ analyze exit before `08_nq_policy_training_status` | not complete |
| Run CatBoost/path-ranker target/export | Waiting on NQ analyze exit before `09_nq_export_structural_path_target` | not complete |
| Run execution-tree workflow | Waiting on NQ analyze exit before `10-12_nq_workflow_*` and ES sequence | not complete |
| Include provider context: IBKR, TradingViewRemix, YF, Kraken | Latest separate provider-capability work is still active in another root; this checkpoint does not count it as complete | not complete |
| Avoid aggregate-Sharpe promotion | Current evidence is support-only; promotion remains false until branch-conditioned downstream chain survives | done |

## Current Readback

- `01_export_tomac_real_trades.exit=0`.
- `02_build_symbol_manifests.exit=0`.
- `03_nq_results_import.exit=0`.
- `04_nq_prior_init.exit=0`.
- `05_nq_ingest_real_trades.exit=0`.
- NQ real-trade ingest applied `77/77` rows with `0` invalid rows.
- Real-trade export summary: `192` total trades, `NQ/USD=77`, `ES/USD=115`.
- Branch path present in NQ rows: `TrendExpansion -> LongHistoryTomacBreakout -> KillzoneContinuation -> TomacNQ_KillzoneBreakout`.
- `06_nq_analyze_15m_1h_1d` was still in progress at this checkpoint; stdout/stderr were not yet flushed.

## Classification

Current status is `partial_chain_support_only`. It is not yet a `market_factor_negative_sample` or promotion packet because the ordered downstream chain has not completed. If the analyze step or later workflow loses branch fields, classify the result as `chain_contract_negative_sample`. If provider acquisition fails, classify that part as `infrastructure_negative_sample`.

## Next Safe Action

Wait for `06_nq_analyze_15m_1h_1d` to settle, then read `07-12` NQ outputs and `13-22` ES outputs before any Board B ledger append.
