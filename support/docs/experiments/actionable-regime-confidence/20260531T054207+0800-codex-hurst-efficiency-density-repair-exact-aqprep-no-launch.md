# Hurst Efficiency Density Repair Exact-AQ Prep No-Launch

- created_at: `2026-05-31T05:42:07+0800`
- owner: `codex`
- agent_name: `codex-hurst-efficiency-density-repair-exact-aqprep-no-launch-20260531T054207+0800`
- route_alias: `sd/ict-engi-fact-rese-muta`
- runtime_skill: `~/.hermes/skills/software-development/ict-engi-fact-rese-muta/SKILL.md`
- run_root: `/tmp/ict-engine-hurst-efficiency-density-repair-exact-aqprep-20260531T054207+0800`
- claim: `/tmp/ict-engine-agent-claims/board-b-factor-refinement/20260531T054207+0800-codex-hurst-efficiency-density-repair-exact-aqprep-no-launch.claim`
- repo_run_root: `support/docs/experiments/actionable-regime-confidence/runs/20260531T054207+0800-codex-hurst-efficiency-density-repair-exact-aqprep-no-launch-v1`

## Objective

Prepare, but do not launch, the exact-AQ continuation for the terminalized
Hurst efficiency density-repair local screen. This keeps the previous
retained-cache candidate actionable while the shared backend is blocked.

## Parent Evidence

- parent_workdoc: `/tmp/ict-engine-hurst-efficiency-density-repair-local-screen-20260531T052423+0800/workdoc.md`
- parent_repo_packet: `support/docs/experiments/actionable-regime-confidence/runs/20260531T052423+0800-codex-hurst-efficiency-density-repair-local-screen-v1`
- parent_terminal_metrics: `support/docs/experiments/actionable-regime-confidence/runs/20260531T052423+0800-codex-hurst-efficiency-density-repair-local-screen-v1/checks/terminal_metrics.json`
- parent_local_gate1_candidates: `support/docs/experiments/actionable-regime-confidence/runs/20260531T052423+0800-codex-hurst-efficiency-density-repair-local-screen-v1/summaries/local_gate1_candidates.csv`

Parent result:

- `local_gate1_candidate_count=2`
- `survives_instrument_cost_count=5`
- `session_scope=ETH/full_retained_session`
- `rth_filter_applied=false`
- `promotion_allowed=false`
- `trade_usable=false`
- `update_goal=false`

Primary candidate:

| field | value |
|---|---:|
| symbol | `NQ` |
| timeframe | `5m` |
| context_timeframe | `15m` |
| variant | `nq5m_microbreak_fast` |
| trades | `589` |
| trades_per_day | `0.378778` |
| local_profit_factor | `1.275140` |
| raw_total_profit_pct | `14.413753` |
| instrument_cost_total_profit_pct | `13.552642` |
| years_positive | `5/5` |

## Same-Turn Guard

Fresh guard readback:

- `python3 support/scripts/factor_claim_terminalization_audit.py --compact`
- status: `needs_attention`
- `active_claims=2`
- `fresh_active_claims_without_live_process=2`
- `live_factor_processes=0`
- blockers:
  - `20260531T053342+0800-codex-polarized-fractal-efficiency-trend-acceptance-local-screen.claim`
  - `20260531T053433+0800-codex-andrews-pitchfork-median-rejoin-15m-aqlaunch.claim`

Focused process table found no true factor backend owner. The only match was a
separate `rg` command whose arguments included `auto-quant` as a glob pattern,
not an AutoQuant process.

Clean-AQ registration check:

```text
candidate_specs(families=["hurst_efficiency_density_repair"])
ValueError: unknown candidate families: hurst_efficiency_density_repair
```

## Deferred Command

Run only after fresh claims clear and `hurst_efficiency_density_repair` is
registered in the clean-AQ runner with focused tests:

```bash
python3 support/docs/experiments/actionable-regime-confidence/scripts/run_tomac_index_futures_clean_aq_v1.py \
  --root /tmp/ict-engine-hurst-efficiency-density-repair-exact-aq-<STAMP> \
  --compact-root support/docs/experiments/actionable-regime-confidence/runs/<STAMP>-codex-hurst-efficiency-density-repair-exact-aq-v1 \
  --symbols NQ \
  --timeframes 5m \
  --families hurst_efficiency_density_repair \
  --aq-smoke-timeframe 5m \
  --aq-symbol-limit 1
```

## Terminal Decision

- status: `terminalized_no_launch_prep_blocked`
- decision: `exact_aq_deferred_fresh_claims_and_missing_clean_aq_family_registration`
- provider_fetch_started: `false`
- ibkr_historical_started: `false`
- autoquant_launched: `false`
- freqtrade_backtest_launched: `false`
- downstream_lifecycle_started: `false`
- same_tree_practical_closure: `null`
- promotion_allowed: `false`
- trade_usable: `false`
- update_goal: `false`

## Post-Write Verification

- json_validation: `json_ok`
- post_write_compact_audit_status: `needs_attention`
- post_write_active_claims: `1`
- post_write_fresh_active_claims_without_live_process: `1`
- post_write_live_factor_processes: `0`
- post_write_blocking_claim: `20260531T053901+0800-codex-fisher-transform-trend-rejoin-local-screen.claim`
- no_launch_claim_active_after_write: `false`

Next steps:

1. Add a narrow clean-AQ registration/TDD slice for `hurst_efficiency_density_repair`.
2. Re-run compact audit and focused `ps` immediately before launch.
3. If clear, run the NQ 5m exact AQ command above.
4. Keep all practical flags false until same-tree lifecycle evidence passes.
