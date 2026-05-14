# Completion Audit After AutoQuant Cache Seed v1

Run id: `20260512T065658+0800-codex-completion-audit-after-autoquant-cache-seed-v1`

Gate result: `completion_audit_after_autoquant_cache_seed_v1=not_complete_autoquant_ready_source_control_unlock_absent`

## Objective Restatement

The objective requires every active regime to reach `>=95%` confidence, be validated on other markets and cycles/timeframes, and then pass the real local chain in order: source/control unlock, direct verifier, split calibration, canonical merge, provider/AutoQuant, filter/Pre-Bayes, BBN, CatBoost/path-ranking, and execution-tree readback. Provider surfaces include IBKR, TradingViewRemix, yfinance, and Kraken where available.

## Checklist Result

- Met: `2`
- Partial: `3`
- Not met: `4`
- Not applicable because blocked: `2`

Checklist CSV: `docs/experiments/actionable-regime-confidence/runs/20260512T065658+0800-codex-completion-audit-after-autoquant-cache-seed-v1/completion-audit-after-autoquant-cache-seed-v1/prompt_to_artifact_checklist_after_autoquant_cache_seed_v1.csv`

## Current Evidence

- R6 owner/export root: absent.
- R5 recency root: absent; latest `064908` redownload has `0` rows after `2026-01-30`.
- R3 native-subhour root: physically present with `5,032,903` TSIE rows for `Bear`, `Bull`, and `Sideways`, but policy-quarantined and `Crisis` absent.
- Auto-Quant: latest `065454` local-cache seed makes the isolated managed workspace `dependency_ready_data_ready`, `healthy=true`, and `data_ready=true`.
- Downstream chain: latest `064259` provider/analyze-live/Pre-Bayes/policy-training/workflow/path-ranking readback is read-only and non-promoting.

## Decision

The objective is not complete. Auto-Quant readiness improved, but the strict Board A gate remains blocked by missing valid source/control unlocks. Accepted rows added `0`; canonical merge false; downstream promotion false; strict full objective false; trade usable false; `update_goal=false`.

## Next

Continue source/control acquisition. Do not run direct verifier, split calibration, canonical merge, or downstream promotion until R6 owner-export controls, R5 post-`2026-01-30` source-owned recency rows, verifier-native Crisis-capable R3 labels, explicit source/control approval, or a genuinely new accepted cross-timeframe source export exists.
