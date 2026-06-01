# Auto-Quant dispatch timeout + wrapper namespace pitfalls

Session context: regime-rooted profitability-factor training for ict-engine.

Observed pattern:
- A wrapper-based Gate 1 run can complete provider fetches and `auto-quant-agent-material-batch` with exit 0, then hang or time out in `auto-quant-agent-material-dispatch`.
- If dispatch exits 124 and no `auto_quant_agent_material_rank*.json` exists, the authoritative verdict is `provider_or_aq_runtime_blocked` / observation, not factor failure and not downstream admission.
- `rank_rows=0`, `total_trades=0`, and `branch_fields_preserved=false` in this shape are symptoms of missing rank output, not evidence that the alpha had zero trades.
- Continue only after rerun with a smaller material set, longer timeout, or corrected wrapper/material namespace. Do not run Pre-Bayes, BBN, CatBoost, or execution tree without a real rank artifact.

Wrapper namespace check:
- When copying a template runner, rewrite more than `FACTOR_ID`, `BRANCH_PATH`, and `package_id`.
- Inspect generated `agent_material_units/*` labels and material titles before dispatch.
- Stale labels such as an unrelated sector/family name in unit paths show template namespace leakage. Treat that as a provenance blocker or rerun with corrected titles/material metadata.

Provider nuance:
- Partial Yahoo/YF 429, SSL EOF, or unsupported `4h` failures should be stored as provider-window blockers for those lanes.
- If the 1m origin lanes fetched but dispatch/rank never completed, terminalize as AQ runtime blocker, not as a cost-density verdict.
