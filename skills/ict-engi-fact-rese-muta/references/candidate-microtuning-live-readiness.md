# Candidate microtuning toward live-readiness

Use this when the user asks to turn all candidate factors into practical/live-ready profit factors.

## Durable lesson
Do not treat candidate microtuning as a single parameter sweep. Split candidates by blocker class and advance each by the gate it is missing:

1. `ranker_mature_but_execution_observe`
   - Example: `IBKR_QQQ_TSMOM_HTF_GATE` had `raw_scored_mature=117/30`, `production_validation=116/30`, `observation_validation=116/30`, and `quality_ready=true`.
   - It still stayed `execution_observe_only`, `actionable=false`, `ready=false`, `fail_closed`.
   - Next work is execution-readiness / PDA / hybrid-alignment diagnosis, not more factor parameter sweeps.

2. `thin_edge_cost_fragile`
   - Example: `IBKR_QQQ_TOD_SLOT_ALPHA_5M_TUNED` kept high win rate but edge vanished under realistic cost.
   - Best tuned rows: `cost_gate v2` profit `0.46%`, 7 trades, win `85.71%`, sharpe `3.8661`, but net_5bps `-0.24%`; `edge050 v2` profit `0.76%`, 18 trades, win `83.33%`, net_5bps `-1.04%`.
   - Downgrade to incubate or seek a wider-edge condition; do not spend downstream BBN/CatBoost/tree budget on cost-fragile micro-alpha.

3. `gate1_strong_validation_immature`
   - Example: `YF_SMH_KELTNER_MTF_5M_TUNED_V2` produced strong Gate 1 rows:
     - base_replay: profit `19.82%`, 29 trades, win `75.86%`, sharpe `4.058`, net_5bps `16.92%`
     - cost_tight: profit `17.02%`, 23 trades, win `60.87%`, sharpe `3.0066`, net_5bps `14.72%`
     - density_tuned: profit `17.19%`, 36 trades, win `75.0%`, sharpe `3.3282`, net_5bps `13.59%`
     - parity_strict: profit `10.5%`, 16 trades, win `62.5%`, sharpe `1.9207`, net_5bps `8.90%`
   - Downstream BBN may pass (`pre_bayes=pass_hard`, trend posterior around `0.8266`, workflow direction `execute_follow_through`), but if ranker is still `candidate_set_only` with `raw_scored_mature=1/30`, `production_validation=0/30`, `observation_validation=0/30`, and `execution_candidate candidate_status=no_trade`, it is not live-ready.
   - Next work: provider parity (IBKR/TradingView/YF as applicable), same rooted branch sibling rows, and >=30 mature/production/observation rows.

## Required sequence
1. Inventory candidates across repo and `/tmp/ict-engine-runs`, not only the latest run.
2. Classify each candidate into one blocker class above.
3. Only tune the missing gate:
   - execution blocker -> execution-readiness/PDA/hybrid diagnostics
   - cost blocker -> cost/turnover/hold-time filter or abandon
   - validation blocker -> provider parity + more same-branch mature rows
4. Preserve branch identity: `main_regime -> sub_regime -> ... -> candidate_factor -> profit_factor`.
5. Report `live-ready` only when all are true:
   - cost-stressed positive under realistic per-side bps
   - provider parity or explicitly native provider for execution venue
   - BBN/filter passes
   - CatBoost/path-ranker mature/production/observation gates pass
   - execution candidate/actionable gate passes without sibling-path pivot

## Pitfall
A candidate can be profitable, mature, or execution-follow-through in isolation and still not be live-ready. The final answer must name the blocker class instead of over-claiming readiness.
