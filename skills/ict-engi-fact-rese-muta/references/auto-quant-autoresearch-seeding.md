# Auto-Quant autoresearch seeding guard

Use when `ict-engine factor-autoresearch --backend auto-quant` returns preparation guidance instead of real iterations.

## Trigger evidence

Typical output notes:

```text
auto_quant_prepare_required_before_run
auto_quant_seed_strategies_required
auto_quant_active_strategy_count=0
```

This means ict-engine prepared or located the managed Auto-Quant workspace, but Auto-Quant did not evaluate active strategies yet.

## Required handling

1. Do not claim automatic iteration completed.
2. Inspect the actual managed workspace under the run state `.deps/auto-quant/`.
3. Verify the workspace data matches the requested handoff. An existing requested
   `data_path` plus unrelated workspace feathers is not data-ready: the managed
   Auto-Quant workspace must contain the requested file stem or satisfy an
   explicit profile `expected_data_files` contract. If the request was
   `yf_crwd_5m.csv` but the workspace only has unrelated `BTC/ETH/SOL/BNB/AVAX`
   `1h/4h/1d` feathers, classify it as `dependency_ready_data_missing` and run
   or repair `auto-quant-prepare` before any oracle run.
4. Use the template path that exists in that checkout. In observed v0.4.1 workspaces it was:
   `user_data/strategies/_template.py.example`
   even though the generated agent prompt mentioned `strategies_external`.
5. Seed 1-3 active strategy files, each non-underscore and with class name matching filename.
6. Keep paradigms diverse: e.g. mean-reversion, trend-following, volatility, breakout.
7. Run only the workspace oracle described by that checkout (commonly `uv run run.py`; some prompts may mention `run_tomac.py` if present).
8. When importing results back into ict-engine, preserve the exact rooted branch identity:
   `market -> product -> symbol -> timeframe -> main_regime -> sub_regime -> candidate/profit_factor`.
9. If the workspace uses synthetic/collapsed symbols or timeframes, mark output as seed/incubate evidence, not live-provider parity.

## Classification

- Preparation only: `auto_quant_active_strategy_count=0` or missing active strategies.
- Data-preparation blocker: active strategies exist, but workspace data does not
  match the requested provider/symbol/timeframe handoff; classify as
  `dependency_ready_data_missing`, not as a factor verdict.
- Seed/incubate: Auto-Quant oracle ran on synthetic/collapsed workspace but exact provider/symbol/timeframe parity is absent.
- Gate candidate: exact branch metadata and real provider artifacts survive AQ Gate 1.
- Downstream candidate: Gate 1 plus cost survives and branch is allowed into Pre-Bayes/BBN/CatBoost/execution-tree.
