# Post-093937 Chain Readback v1

Run id: `20260512T100419+0800-codex-post-093937-chain-readback-v1`

Mode: `read_only_non_promoting`

## Scope

Fresh readback after the `093937` branch-preservation artifact, against:

`docs/experiments/actionable-regime-confidence/runs/20260512T000748-codex-board-b-agent-selected-historical-factor-research-v1/state_agent_selected_historical_factor_research_downstream_v1`

Symbol:

`SRC_ROOT_CARRY_LONG_220646`

This run does not select historical data, approve source/control evidence, mutate canonical intake, promote Auto-Quant output, make a trade claim, or call `update_goal`.

## Commands

All captured commands exited `0`:

- `provider-status --agent`
- `auto-quant-status --state-dir <state> --output-format json`
- `pre-bayes-status --symbol SRC_ROOT_CARRY_LONG_220646 --state-dir <state> --refresh --output-format json`
- `policy-training-status --symbol SRC_ROOT_CARRY_LONG_220646 --state-dir <state> --output-format agent`
- `workflow-status --phase structural-recommended-path-bundle --agent`
- `workflow-status --phase structural-feedback --agent`
- `workflow-status --phase execution-candidate --agent`
- `workflow-status --refresh --agent`

Command stdout/stderr/cmd files are in `command-output/`; exit codes and hashes are in `checks/`.

## Readback

- Provider summary: `entry_model:2/2 ready | live_runtime:1/3 ready | local_runtime:1/2 ready | market_data:1/7 ready`.
- Provider details: `yfinance` ready, `kraken_cli` ready, `tradingview_mcp` unhealthy with `tradingview_mcp_connectivity_probe_failed`, `ibkr_bridge` unhealthy because runtime dependencies are missing while gateway is reachable, and `kraken_public` blocked by missing Python provider modules.
- Auto-Quant dependency is healthy and bootstrapped, but `data_ready=false`; recommended next command remains `ict-engine auto-quant-prepare --state-dir <state>`.
- Pre-Bayes/BBN readback: latest gate is `pass_neutralized`; canonical structural active regime is `range` with confidence `0.5619249343265972`; read-only regime BBN application is `applied`, with label `primary::ExtremeStress` plus the preserved branch path.
- Policy/CatBoost readback: entry-model BBN/CatBoost tables are not ready (`matched_rows=0`), but structural path-ranking is ready with a CatBoost trainer artifact, `history_mature_rows=288`, production validation `286/30`, observation validation `48/30`, and runtime selection `enabled_candidate_set_ready`.
- Structural bundle path remains `Crisis -> CrisisReliefCarry -> StopManagedPanicRecovery -> SourceRootStopCarryLongHorizonV1:crisis_carry_h8_sl048_tp12`; posterior `0.5822884327025901`, prior `0.5605411065120474`, ranker raw score `0.65`, runtime source `history_path`.
- Execution candidate preserves the same branch path, but remains `execution_observe_only`, `review_status=observe`, `ready=false`, and `execution_readiness=0.4504361163104953`.
- Full workflow remains blocked by `user_selected_historical_data_missing`.

## Decision

Gate: `post_093937_chain_readback_v1=branch_preserved_readonly_observe_only_user_selected_history_and_autoquant_data_missing`.

This is useful evidence that the current recorded-MTF state still carries Auto-Quant, Pre-Bayes/BBN, CatBoost/path-ranking, and execution-candidate surfaces through the chain. It is not a promotion packet.

Accepted rows added: `0`.

Promotion: `false`.

`update_goal=false`.

