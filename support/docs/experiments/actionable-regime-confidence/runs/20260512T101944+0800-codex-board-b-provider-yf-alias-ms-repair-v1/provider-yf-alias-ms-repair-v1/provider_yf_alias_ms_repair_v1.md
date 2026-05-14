# Provider YF Alias/MS Repair v1

Run id: `20260512T101944+0800-codex-board-b-provider-yf-alias-ms-repair-v1`

Gate result: `provider_yf_alias_ms_repair_v1=alias_ms_repair_reached_measurement_zero_trades`

## Scope

This is an additive closeout for a completed provider-owned Yahoo NQ sidecar. It does not edit the Current Cursor, does not select history on behalf of the user, does not approve source/control evidence, does not run selected-data promotion, does not run Pre-Bayes/BBN/CatBoost/path-ranking/execution-tree promotion, does not promote a candidate, and does not call `update_goal`.

Source state:

`docs/experiments/actionable-regime-confidence/runs/20260512T100419+0800-codex-board-b-provider-owned-aq-acquisition-v1/state_provider_owned_aq_long_yf_v1`

Run-local state copy:

`docs/experiments/actionable-regime-confidence/runs/20260512T101944+0800-codex-board-b-provider-yf-alias-ms-repair-v1/state_provider_yf_alias_ms_repair_v1`

## Readback

The sidecar copied the provider-preseeded `B2R_NQ_PROVIDER_LONG_100419_USD` feathers into the standard `NQ_USD` alias expected by TOMAC/Freqtrade:

- `B2R_NQ_PROVIDER_LONG_100419_USD-1h.feather` -> `NQ_USD-1h.feather`
- `B2R_NQ_PROVIDER_LONG_100419_USD-4h.feather` -> `NQ_USD-4h.feather`
- `B2R_NQ_PROVIDER_LONG_100419_USD-1d.feather` -> `NQ_USD-1d.feather`

Feather probe exited `0` and confirmed:

- `1h`: `11086` rows, raw timestamp range `1717365600000 -> 1778540400000`, dtype `int64`
- `4h`: `3006` rows, raw timestamp range `1717358400000 -> 1778529600000`, dtype `int64`
- `1d`: `596` rows, raw timestamp range `1717286400000 -> 1778457600000`, dtype `int64`

TOMAC/Freqtrade exited `0` and reached measurement for three strategies:

| Strategy | Backtest Window | Trades | Profit % | Sharpe | Win % | Profit Factor |
|---|---:|---:|---:|---:|---:|---:|
| `TomacNQ_KillzoneBreakout` | `2024-06-13 08:00:00 -> 2025-12-31 00:00:00` | `0` | `0.0000` | `0.0000` | `0.0000` | `0.0000` |
| `TomacNQ_RegimePersistenceClusterDense` | `2024-06-12 02:00:00 -> 2025-12-31 00:00:00` | `0` | `0.0000` | `0.0000` | `0.0000` | `0.0000` |
| `TomacNQ_RegimeTrendPullbackDense` | `2024-06-12 22:00:00 -> 2025-12-31 00:00:00` | `0` | `0.0000` | `0.0000` | `0.0000` | `0.0000` |

The command ended with `Done: 3 succeeded, 0 failed`.

## Decision

This retires the local alias/MS timestamp wiring question for this provider-owned Yahoo NQ sidecar: the normalized `NQ/USD` data loaded and TOMAC ran. It still adds `0` mature rooted branch observations, `0` profitability rows, and no downstream promotion evidence.

Gate:

- `count_once:101944_provider_yf_alias_ms_repair`
- `provider_yf_alias_ms_repair_v1=alias_ms_repair_reached_measurement_zero_trades`
- `fail_closed:zero_trades_no_mature_rooted_branch_observations`
- `fail_closed:no_profitability_signal`
- `fail_closed:downstream_promotion_rerun_false`
- `promotion_allowed=false`
- `update_goal=false`

## Artifacts

- Alias copy log: `docs/experiments/actionable-regime-confidence/runs/20260512T101944+0800-codex-board-b-provider-yf-alias-ms-repair-v1/command-output/01_alias_copy.out`
- Feather probe: `docs/experiments/actionable-regime-confidence/runs/20260512T101944+0800-codex-board-b-provider-yf-alias-ms-repair-v1/command-output/02_alias_feather_probe.out`
- TOMAC stdout: `docs/experiments/actionable-regime-confidence/runs/20260512T101944+0800-codex-board-b-provider-yf-alias-ms-repair-v1/command-output/03_run_tomac_alias_ms_repair.out`
- TOMAC stderr: `docs/experiments/actionable-regime-confidence/runs/20260512T101944+0800-codex-board-b-provider-yf-alias-ms-repair-v1/command-output/03_run_tomac_alias_ms_repair.err`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260512T101944+0800-codex-board-b-provider-yf-alias-ms-repair-v1/checks/provider_yf_alias_ms_repair_v1_assertions.out`
- JSON: `docs/experiments/actionable-regime-confidence/runs/20260512T101944+0800-codex-board-b-provider-yf-alias-ms-repair-v1/provider-yf-alias-ms-repair-v1/provider_yf_alias_ms_repair_v1.json`

## Next

Do not rerun the same Yahoo NQ alias/MS repair shape. Continue only with a changed branch-specific strategy that can produce nonzero provider-owned observations, a different provider-provenanced market family, or explicit selected-history/source-control unlocks before any selected-data promotion chain.
