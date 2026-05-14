# Source Control Arrival Refresh After 063906 v2

Run id: `20260512T064309+0800-codex-source-control-arrival-refresh-after-063906-v2`

Gate result: `source_control_arrival_refresh_after_063906_v2=only_tsie_quarantine_present_no_valid_unlock_no_downstream`

Board sha256 before artifact: `f154812aa9e9c5d47d8d79b009a9e7ae6cb3f6ac6d0a4537782be1b24114102b`

## Scope

Bounded read-only refresh after the `063906` current-objective audit. It checks exact required roots, nearby `/tmp/ict-engine*` files, and repo experiment artifacts for newly arrived source/control evidence. It does not send requests, approve controls, mutate target roots, run canonical merge, rerun downstream promotion, make a trade claim, or call `update_goal`.

## Required Roots

| Root ID | Exists | Complete | Accepted For Promotion | Notes |
|---|---:|---:|---:|---|
| `r6_owner_export` | `False` | `False` | `False` | n/a |
| `r3_native_subhour` | `True` | `True` | `False` | TSIE root is complete on disk but policy-quarantined, Crisis absent |
| `r5_recency_extension` | `False` | `False` | `False` | n/a |

## Decision

No valid source/control unlock arrived. R6 owner/export and R5 recency roots remain absent. The R3 native-subhour path exists only as the TSIE-quarantined root and remains non-promoting.

Promotion remains blocked: accepted rows added `0`, source/control evidence acquired false, canonical merge false, downstream promotion rerun false, strict full objective false, trade usable false, and `update_goal=false`.

## Artifacts

- JSON: `docs/experiments/actionable-regime-confidence/runs/20260512T064309+0800-codex-source-control-arrival-refresh-after-063906-v2/source-control-arrival-refresh-after-063906-v2/source_control_arrival_refresh_after_063906_v2.json`
- Required roots CSV: `docs/experiments/actionable-regime-confidence/runs/20260512T064309+0800-codex-source-control-arrival-refresh-after-063906-v2/source-control-arrival-refresh-after-063906-v2/source_control_arrival_required_roots_v2.csv`
- Candidate files CSV: `docs/experiments/actionable-regime-confidence/runs/20260512T064309+0800-codex-source-control-arrival-refresh-after-063906-v2/source-control-arrival-refresh-after-063906-v2/source_control_arrival_candidate_files_v2.csv`
- Active processes CSV: `docs/experiments/actionable-regime-confidence/runs/20260512T064309+0800-codex-source-control-arrival-refresh-after-063906-v2/source-control-arrival-refresh-after-063906-v2/source_control_arrival_active_processes_v2.csv`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260512T064309+0800-codex-source-control-arrival-refresh-after-063906-v2/checks/source_control_arrival_refresh_after_063906_v2_assertions.out`

## Next

Continue only from explicit source/control approval, verifier-native R6 owner-export rows with valid controls, source-owned R5 recency rows, verifier-native R3 `MainRegimeV2` labels, or a genuinely new accepted cross-timeframe `MainRegimeV2` source export before rerunning direct verifier, split calibration, canonical merge, provider/AutoQuant, filter/Pre-Bayes, BBN, CatBoost/path-ranking, and execution-tree readback.
