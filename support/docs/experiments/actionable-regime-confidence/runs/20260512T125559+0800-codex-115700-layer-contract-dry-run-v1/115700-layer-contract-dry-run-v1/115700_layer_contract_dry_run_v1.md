# 115700 Layer-Contract Dry-Run v1

Run id: `20260512T125559+0800-codex-115700-layer-contract-dry-run-v1`
Source root: `20260512T115700+0800-codex-same-root-six-provider-1h-aq-v1`

## Scope
Repair-preview for the settled same-root six-provider AQ rows. This enriches row-level branch/provider/downstream contract fields and runs `auto-quant-ingest-real-trades --dry-run` in an isolated state dir. It does not mutate production state and does not promote a candidate.

## Result
- Source files: `12`.
- Enriched rows: `237`.
- Contract-complete rows after enrichment: `237`.
- Market/factor trainable rows: `0` because every row keeps `quality_weight=0`.
- Dry-run exit: `0`.
- Dry-run status: `dry_run_preview`.
- Dry-run trades total/applied/invalid: `237` / `237` / `0`.
- Dry-run feedback records inserted: `0`.

## Decision
- The stale source id and stale symbol namespace blocker is repairable in a bounded artifact.
- The missing contract-field blocker is repairable at JSONL schema level.
- This is still not market/factor evidence because the downstream fields are explicit non-promotional placeholders and quality weight is zero.
- `promotion_allowed=false`.
- `trade_usable=false`.
- `update_goal=false`.

## Artifacts
- JSON: `docs/experiments/actionable-regime-confidence/runs/20260512T125559+0800-codex-115700-layer-contract-dry-run-v1/115700-layer-contract-dry-run-v1/115700_layer_contract_dry_run_v1.json`
- Combined enriched trades: `docs/experiments/actionable-regime-confidence/runs/20260512T125559+0800-codex-115700-layer-contract-dry-run-v1/enriched-real-trades/115700_layer_contract_enriched_all.real_trades.jsonl`
- Dry-run command output: `docs/experiments/actionable-regime-confidence/runs/20260512T125559+0800-codex-115700-layer-contract-dry-run-v1/command-output/01_auto_quant_ingest_real_trades_dry_run.out`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260512T125559+0800-codex-115700-layer-contract-dry-run-v1/checks/115700_layer_contract_dry_run_v1_assertions.out`
