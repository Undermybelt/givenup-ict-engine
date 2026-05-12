# Agent-Selected MTF Factor-Research Readback v1

This is a non-promoting Board B readback for `034002/downstream-combined-v1`.
It does not edit the current cursor, does not satisfy `user_selected_historical_data`,
and does not promote the `032157` recipe.

## Scope

- Run root: `docs/experiments/actionable-regime-confidence/runs/20260512T041143+0800-codex-board-b-032157-agent-selected-mtf-factor-research-v1`
- State dir: `docs/experiments/actionable-regime-confidence/runs/20260512T041143+0800-codex-board-b-032157-agent-selected-mtf-factor-research-v1/state_agent_selected_mtf_v1`
- Selected path note: `agent-selected MTF diagnostic only; does not satisfy user_selected_historical_data gate`
- Primary data path: `docs/experiments/actionable-regime-confidence/runs/20260512T032157-codex-board-b-nq-cost-crisis-repair-v3/state_nq_cost_crisis_repair_v3/B2R_NQ_COST_CRISIS_REPAIR_032157/analyze_nq_mtf.json`

## Command Readback

| Command | Exit | Evidence | Readback |
|---|---:|---|---|
| `00_factor_research_mtf` | 0 | `command-output/00_factor_research_mtf.out` | Auto-Quant handoff emitted with `dependency_ready_data_missing`, `data_ready=false`, `auto_quant_active_strategy_count=0`, and `auto_quant_prepare_required_before_run`. |
| `01_auto_quant_prepare` | 1 | `command-output/01_auto_quant_prepare.err` | Prepare failed before data generation: `auto-quant dependency is missing; bootstrap first with ict-engine auto-quant-bootstrap --state-dir .../state_agent_selected_mtf_v1/auto-quant`. |

## Gate

- `fail_closed:agent_selected_mtf_prepare_failed`.
- `blocked:user_selected_historical_data_missing`.
- `not_started:no_auto_quant_backtest_no_mature_rows`.

## Decision

No downstream Pre-Bayes/filter, BBN, CatBoost/path-ranker, or execution-tree rerun should be started from this sidecar. It produced a handoff only, no prepared Auto-Quant market data, no backtest trades, no mature rooted branch observations, and no execution admission evidence.

Keep `034002/downstream-combined-v1` as the fail-closed cursor. The next valid Board B action remains explicit user selection among `HTF`, `MTF`, or `LTF`, followed by an isolated Auto-Quant path that avoids the prepare/bootstrap mismatch and carries forward only nonzero mature rooted branch observations.
