# Source Control Provider Refresh After 065506 v1

Run id: `20260512T065822+0800-codex-source-control-provider-refresh-after-065506-v1`

Gate result: `source_control_provider_refresh_after_065506_v1=autoquant_ready_source_control_still_blocked_no_promotion`

## Scope

Read-only Board A refresh after the `065506` Auto-Quant local-cache seed. This run captures provider, Auto-Quant, analyze-live, Pre-Bayes, workflow, and path-ranking status, plus current source/control root presence. It does not mutate R3/R5/R6 target roots, approve controls, run canonical merge, rerun downstream promotion, make a trade claim, or call `update_goal`.

## Source/Control Readback

- R6 owner/export root exists: `false`.
- R5 recency root exists: `false`.
- R3 native-subhour root exists: `true` but remains TSIE-derived/quarantined and lacks `Crisis`.
- Bounded local candidates scanned: `500`; target R6 arrival candidates: `0`.

## Runtime Readback

- Provider summary: `entry_model:2/2 ready | live_runtime:1/3 ready | local_runtime:1/2 ready | market_data:1/7 ready`.
- Auto-Quant status: `dependency_ready_data_ready`, healthy `true`, data_ready `true`.
- analyze-live: rc `0`, decision `Observe only`, pre-Bayes `pass_neutralized`, execution `observe`.
- Pre-Bayes latest gate: `pass_neutralized`.
- Workflow: `blocked` / `user_selected_historical_data_missing`.
- Path-ranking: rows `1`, mature rows `0`, calibrated rows `0`.

## Accounting

- Accepted rows added: `0`.
- Valid required-root unlock: `false`.
- Source/control evidence acquired: `false`.
- Canonical merge: `false`.
- Downstream promotion rerun: `false`.
- Strict full objective: `false`.
- Trade usable: `false`.
- `update_goal=false`.

## Decision

Auto-Quant is dependency/data ready in the isolated runtime state after 065506, but the required Board A source/control roots remain blocked: R6 owner-export controls are absent, R5 post-cutoff recency root is absent, and R3 remains TSIE-derived/quarantined without Crisis.

## Next

Continue only from explicit source/control approval, verifier-native R6 owner-export rows with controls, source-owned post-2026-01-30 R5 recency rows, verifier-native Crisis-capable R3 MainRegimeV2 labels, or a genuinely new accepted cross-timeframe MainRegimeV2 source export.

## Artifacts

- JSON: `docs/experiments/actionable-regime-confidence/runs/20260512T065822+0800-codex-source-control-provider-refresh-after-065506-v1/source-control-provider-refresh-after-065506-v1/source_control_provider_refresh_after_065506_v1.json`
- Required-root CSV: `docs/experiments/actionable-regime-confidence/runs/20260512T065822+0800-codex-source-control-provider-refresh-after-065506-v1/source-control-provider-refresh-after-065506-v1/required_root_status_after_065506_v1.csv`
- Candidate CSV: `docs/experiments/actionable-regime-confidence/runs/20260512T065822+0800-codex-source-control-provider-refresh-after-065506-v1/source-control-provider-refresh-after-065506-v1/source_control_candidate_scan_after_065506_v1.csv`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260512T065822+0800-codex-source-control-provider-refresh-after-065506-v1/checks/source_control_provider_refresh_after_065506_v1_assertions.out`
- Command output: `docs/experiments/actionable-regime-confidence/runs/20260512T065822+0800-codex-source-control-provider-refresh-after-065506-v1/command-output/`
