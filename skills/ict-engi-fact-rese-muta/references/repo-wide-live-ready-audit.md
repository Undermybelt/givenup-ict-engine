# Repo-wide live-ready factor audit

Use when the user asks whether there is any factor in the whole ict-engine repo/run corpus that can be used in real trading.

## Rule
Do not answer from the latest run only. Audit both the repo experiment tree and `/tmp/ict-engine-runs` for promotion/readiness evidence.

## Minimum evidence search
Search for these positive gates first:

- `"trade_usable": true`
- `"promotion_allowed": true`
- `read_only_regime_bbn_trade_usable=true`
- `trainer_status=runtime_eligible`
- `quality_ready=true`
- `production_validation=.../30` and `observation_validation=.../30` meeting gate
- `closed_loop_branch_admission.actionable=true`
- `execution_gate_status=execution_pass` or equivalent execution-tree pass

Then search for negative blockers around the same artifact:

- `candidate_set_only`
- `execution_observe_only`
- `gate_status=observe`
- `status=fail_closed`
- `actionable=false`
- `ready=false`
- `production_validation=0/30`
- `observation_validation=0/30`
- `promotion_allowed=false`
- `trade_usable=false`

## Classification
A factor is live-ready only if all of these hold together on the same rooted branch:

1. Auto-Quant/Gate evidence is positive after realistic cost stress.
2. Provider/provenance is acceptable for the target market, preferably IBKR for US equity intraday.
3. BBN/Pre-Bayes/filter did not neutralize or block it.
4. CatBoost/path-ranker validation is mature enough, not pseudo-label/fallback-only.
5. Execution tree closed-loop admission is actionable/pass, not observe-only.
6. The final `closed_loop_branch_admission.path_id` remains the tested rooted branch, not a sibling pivot.

If ranker gates pass but execution tree says `observe` or `fail_closed`, answer: mature candidate, not live-ready.
If AQ is strong but maturity rows are missing, answer: strong Gate1 candidate, not live-ready.
If provider is fallback/cache-only, answer: incubate/provider-parity pending, not live-ready.

## Session examples
- `IBKR_QQQ_TSMOM_HTF_GATE`: ranker maturity passed (`raw_scored_mature=117/30`, `production_validation=116/30`, `observation_validation=116/30`, `quality_ready=true`) but execution tree returned `execution_observe_only`, `actionable=false`, `ready=false`, `fail_closed`; classify not live-ready.
- `IBKR_QQQ_TOD_SLOT_ALPHA_MTF_CHAIN`: IBKR 5m AQ positive (`profit=1.03%`, `32` trades, `win=81.25%`, `sharpe=8.5004`) but decision was `tree_handoff_candidate_only`, `gate_status=observe`, and ranker production/observation validation was `0/30`; classify strong candidate, not live-ready.
- `YF_SMH_KELTNER_MTF`: YF 5m AQ strong (`profit=19.82%`, `29` trades, `win=75.86%`, `sharpe=4.058`) but provider parity and mature validation were missing and runtime was `candidate_set_only`; classify strong research candidate, not live-ready.

## Reporting
Answer bluntly:

- `暂无 live-ready 盈利因子。`
- Then list closest candidates and the exact blocker.
- Do not soften `observe` into `ready`.
- Do not call `candidate_set_only` practical.
