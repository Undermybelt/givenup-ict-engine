# Diagnostic feedback replay for regime-branch maturity

Session pattern:

- Original run state: `/tmp/ict-engine-runs/20260517T120055Z-ibkr-max-window-dense/state_htf`
- Safe replay state: copied to `state_htf_matured` before ingest
- Diagnostic trade file: `materials/htf_gate_diagnostic_trades.jsonl`
- Ingest command: `auto-quant-ingest-real-trades --source diagnostic_sample_trade_structural_feedback`

What worked:

- Preserve the canonical state directory; ingest into a copied state when replaying maturity evidence.
- Use diagnostic/sample-trade structural feedback only when no live fills exist; label it explicitly as replay/diagnostic, not live execution.
- The branch metadata must remain intact on every row:
  - `regime_profit_branch_path`
  - `main_regime`
  - `sub_regime`
  - `sub_sub_regime_or_profit_factor`
  - `profit_factor`
- After ingest, re-export `structural_path_ranking_target`, retrain CatBoost, then re-run `analyze`, `workflow-status`, and `policy-training-status` on the copied state.

Observed outcome pattern:

- `mature_rows` can rise from 0 to >0 after replay ingest.
- `raw_scored_mature`, `production_validation`, and `observation_validation` can cross threshold even while the execution tree remains `transition_guardrail`.
- `execution_tree_trace.json` may still block on `bridge_needs_confirmation` even after ranker readiness is true.

Pitfall:

- Do not infer live-trade promotion from mature-row recovery alone. Treat execution-tree gating as a separate final gate.
