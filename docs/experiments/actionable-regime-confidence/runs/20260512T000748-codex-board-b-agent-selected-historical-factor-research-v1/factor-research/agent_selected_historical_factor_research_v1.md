# Board B Agent-Selected Historical Factor Research V1

Run id: `20260512T000748-codex-board-b-agent-selected-historical-factor-research-v1`

Purpose: continue the active Board B cursor by testing Auto-Quant-backed factor research on the recorded MTF profile while preserving the parent branch lineage for `SourceRootStopCarryLongHorizonV1`.

## Evidence

- Provider readback: `provider/provider_status_agent.exit=0`.
- Initial ict-engine Auto-Quant handoff: `logs/02_factor_research_agent_selected_mtf.exit=0`, but the handoff stayed `dependency_ready_data_missing`.
- Managed Auto-Quant prepare attempts: `logs/03d_auto_quant_prepare_abs_config.exit=1` and `logs/05_auto_quant_prepare_nested.exit=1`; both failed at Binance market reload / DNS (`Could not contact DNS servers`), not at strategy discovery.
- Run-local recorded profile preparation:
  - `logs/09_prepare_external_recorded_json.exit=0`: `1,874` raw rows, `1,808` after cleaning, wrote `SRC_ROOT_CARRY_LONG_220646/USD` `1h/4h/1d` feathers.
  - `logs/10_prepare_external_recorded_nq_pair.exit=0`: `1,874` raw rows, no OHLCV drops, wrote `NQ/USD` `1h/4h/1d` feathers.
- Offline Auto-Quant/Freqtrade replay with synthetic market metadata:
  - `logs/11_auto_quant_run_recorded_nq_branch.exit=0`.
  - `RegimeRsiRelief`, `RegimeTrendCarry`, and `RegimeVolBreakout` all executed.
  - Each strategy produced `trade_count=0`, `total_profit_pct=0`, `win_rate_pct=0`, and `profit_factor=0`.

## Downstream Readback

Commands in `command-output/12_*` through `command-output/17_*` all exited `0`.

- Pre-Bayes: no policy, no gate, no bridge (`latest_gate_status=null`, `latest_policy=null`).
- BBN: no update was applied because the Auto-Quant factor research produced no accepted trade or structural-feedback candidate.
- CatBoost/path-ranker: target export exists but is not trainable (`rows=1`, `history_rows=1`, `mature_rows=0`, `raw_scored_mature=0/30`, `production_validation=0/30`, `observation_validation=0/30`, trainer artifact missing, runtime disabled).
- Execution tree: structural bundle stayed on `bootstrap_readiness` / `observe`; execution candidate returned `actionable=false`, `ready=false`, with review reason `structural_recommended_path_visible_but_execution_or_pre_bayes_gate_not_ready`.
- Workflow full status: blocking truth remained `insufficient_state` with reason `no workflow phase snapshots available`.

## Supersession

This artifact is an isolated-state NQ/USD readback only. A concurrent correction later reran the same `000748` recorded profile through a broader BTC/USDT-compatible offline Auto-Quant wrapper and found nonzero nursery trades, recorded on the board as `20260512T002813+0800-codex-board-b-000748-recorded-mtf-nonzero-replay-correction-v1`.

Use this file only as evidence that the exact NQ/USD isolated-state probe stayed fail-closed. Do not use it as the final `000748` factor-research result.

## Result

`partial_fail_closed:nq_usd_zero_trade_probe_only_superseded_by_nonzero_recorded_mtf_correction`.

This remains useful negative nursery evidence only. It does not supersede the prior `220646` source pass, does not promote the sibling no-trade overlay, and does not unblock Board B.
