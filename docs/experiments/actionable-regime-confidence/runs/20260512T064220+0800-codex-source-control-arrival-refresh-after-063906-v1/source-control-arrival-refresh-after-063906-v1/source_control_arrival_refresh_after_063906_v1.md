# Source/Control Arrival Refresh After 063906 v1

Run id: `20260512T064220+0800-codex-source-control-arrival-refresh-after-063906-v1`

Gate result: `source_control_arrival_refresh_after_063906_v1=no_valid_required_unlock_no_downstream`

## Scope

Read-only arrival refresh after the `063906` current-objective audit. This packet checks required R6/R3/R5 roots, existing v5 dispatch drafts, and bounded local drop locations. It does not send mail, use a vendor portal, approve TSIE, mutate target roots, run canonical merge, rerun downstream promotion, make a trade claim, or call `update_goal`.

## Readback

- R6 owner-export root exists: `False`; accepted unlock: `False`.
- R3 native-subhour root exists: `True`; accepted unlock: `False`; quarantine reason: `tsie_proxy_policy_quarantined`.
- R5 recency root exists: `False`; accepted unlock: `False`.
- v5 dispatch drafts present: `2/2`; sent/ticket/export evidence in drafts: `False`.
- Bounded local drop hits: `0`.

## Decision

No valid required root is unlocked. The R3 path is present but remains TSIE-quarantined; R6 owner/export rows are absent; R5 recency rows are absent; no local ticket/export/license/order/support artifact was accepted. Canonical merge and downstream provider/AutoQuant -> filter/Pre-Bayes -> BBN -> CatBoost/path-ranking -> execution-tree promotion remain blocked.

Accounting:

- valid required unlock: `false`
- canonical merge allowed now: `false`
- downstream rerun allowed now: `false`
- strict full objective: `false`
- trade usable: `false`
- `update_goal=false`

## Artifacts

- JSON: `docs/experiments/actionable-regime-confidence/runs/20260512T064220+0800-codex-source-control-arrival-refresh-after-063906-v1/source-control-arrival-refresh-after-063906-v1/source_control_arrival_refresh_after_063906_v1.json`
- Required roots CSV: `docs/experiments/actionable-regime-confidence/runs/20260512T064220+0800-codex-source-control-arrival-refresh-after-063906-v1/source-control-arrival-refresh-after-063906-v1/source_control_arrival_refresh_required_roots_v1.csv`
- Dispatch assets CSV: `docs/experiments/actionable-regime-confidence/runs/20260512T064220+0800-codex-source-control-arrival-refresh-after-063906-v1/source-control-arrival-refresh-after-063906-v1/source_control_arrival_refresh_dispatch_assets_v1.csv`
- Local hits CSV: `docs/experiments/actionable-regime-confidence/runs/20260512T064220+0800-codex-source-control-arrival-refresh-after-063906-v1/source-control-arrival-refresh-after-063906-v1/source_control_arrival_refresh_local_hits_v1.csv`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260512T064220+0800-codex-source-control-arrival-refresh-after-063906-v1/checks/source_control_arrival_refresh_after_063906_v1_assertions.out`

## Next

Continue only from explicit source/control approval, verifier-native R6 owner-export rows with valid controls, source-owned R5 recency rows, verifier-native R3 MainRegimeV2 labels, or a genuinely new accepted cross-timeframe MainRegimeV2 source export before rerunning direct verifier, split calibration, canonical merge, provider/AutoQuant, filter/Pre-Bayes, BBN, CatBoost/path-ranking, and execution-tree readback.
