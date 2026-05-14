# Readonly Runtime Chain After 053933 v1

Run id: `20260512T054116-codex-readonly-runtime-chain-after-053933-v1`

Gate result: `readonly_runtime_chain_after_053933_v1=runtime_readback_no_source_unlock_no_promotion`

Board hash before artifact: `bb8ea3bf6998fb27f6dde8577ecd3d3152252f6e12c332caa2a97d508bc93f01`

## Scope

This is a read-only callable-surface readback after the `053933` R5 board/artifact mismatch correction and the later R5/R6 source-acquisition notes. It records whether provider, Auto-Quant, filter/Pre-Bayes, policy/CatBoost-facing status, workflow, and structural path-ranking export surfaces can be called. It does not mutate any source/control target root, run canonical merge, rerun downstream promotion after a source unlock, make a trade claim, or call `update_goal`.

## Command Status

| Command | Exit |
|---|---:|
| `provider_status_agent` | 0 |
| `auto_quant_status_json` | 0 |
| `pre_bayes_status_nq_json` | 0 |
| `policy_training_status_nq_agent` | 0 |
| `workflow_status_structural_recommended_path_bundle_agent` | 0 |
| `workflow_status_structural_feedback_agent` | 0 |
| `workflow_status_execution_candidate_agent` | 0 |
| `export_structural_path_ranking_target` | 0 |

Raw outputs are under `command-output/`.

## Readback

- Provider surface is callable. Summary: `entry_model:2/2 ready | live_runtime:1/3 ready | local_runtime:1/2 ready | market_data:1/7 ready`.
- `yfinance` is ready and adopted by default for tradfi live runtime; `kraken_cli` is ready; `ibkr_bridge` remains configured but unhealthy because local runtime dependencies are missing.
- Auto-Quant status is callable but unhealthy in this isolated state: `status=missing_dependency`, `bootstrap_needed=true`, `auto_quant_not_bootstrapped`.
- Pre-Bayes status is callable and remains `observe_only`; latest filtered assignment includes `market_regime=range`, and no latest canonical structural active regime is present.
- Policy training / CatBoost-facing status is callable but not ready: both built-in entry models report `matched_rows=0`, and structural path-ranking runtime is disabled/not fitted.
- Workflow execution-candidate status is callable but not actionable: `ready=false`, `review_status=observe`, `trade_direction=observe`.
- Structural path-ranking export is callable: `rows=2`, `history_rows=2`, `mature_rows=0`, `rows_with_calibrated_path_prob=0`, and `rows_with_training_weight=0`.

## Decision

This root is callable-surface evidence only. It cannot satisfy Board A promotion because source/control target roots are still absent, approval is not present, canonical merge is false, downstream promotion rerun is false, strict full objective is false, trade usable is false, and `update_goal=false`.

## Next

Keep the active source/control unlock path: obtain explicit approval, verifier-native R6 owner/export rows plus source-owned normal controls, native sub-hour source-label rows, source-owned R5 recency-extension rows, or genuinely source-owned cross-timeframe `MainRegimeV2` exports before rerunning direct verifier, split calibration, canonical merge, provider/AutoQuant, filter/Pre-Bayes, BBN, CatBoost/path-ranking, and execution-tree readback in order.
