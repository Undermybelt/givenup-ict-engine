# Regime-rooted MTF provider ladder notes

> 2026-05-24 schema note: `pda_hybrid_alignment` is historical telemetry only unless the current ict-engine source or readback contract still declares it active. Do not use old `pda_hybrid_alignment=true` or `false` lines in this reference as a current hard gate; classify with the live actionable/status/readiness/transition/ranker/mature-row fields.

Use when continuing Board B / ict-engine profitability-factor training with many agents active.

## Durable workflow

1. Preserve the branch as first-class data before running Auto-Quant:
   `main_regime -> sub_regime -> sub_sub_regime_or_profit_factor -> profit_factor`.
2. Claim active work outside the repo, e.g. `/tmp/ict-engine-agent-claims/board-b-factor-refinement/`.
3. Before launching a heavy Auto-Quant lane, inspect active same-class processes conceptually (`run_*`, `auto-quant-agent-material-dispatch`, `run_tomac.py`) and avoid duplicating another agent's live lane.
4. Run provider fetch for real rows first. `provider-status ready` is not enough; direct fetch can still return no rows or exit nonzero.
5. Require the 1m origin to show real trade density before downstream. Positive sparse 5m/15m/30m/1h rows with zero or one 1m trade are subclass evidence only.
6. Stop before Pre-Bayes/BBN/CatBoost/execution-tree unless Gate 1 earns it. Do not use downstream machinery to rescue a sparse or no-origin Gate 1.
7. If Gate 1 passes but downstream later fails closed, preserve exact branch parity evidence and classify as scoped/incubate; do not claim live readiness.

## Classification patterns

- `provider_window_blocked_no_gate1_verdict`: provider-status ready, but direct fetch failed across requested/downgraded lanes. Not a factor failure.
- `keep_subclass_evidence_or_drop_gate1_no_downstream`: provider and AQ ran, but 1m origin is absent/sparse and higher-timeframe positives are too thin. Keep as negative/subclass evidence; no downstream.
- `keep_gate1_observation_downstream_allowed`: 1m origin has positive density and at least one sibling timeframe supports it. Downstream may run, but promotion still depends on exact branch survival and execution gates.
- `gate1_pass_downstream_fail_closed`: exact branch survives into Pre-Bayes/BBN/execution-tree, but CatBoost/path-ranker or execution readiness blocks actionability.

## Session examples captured

- Bybit GMTUSDT exact 5m RWI trend breakout: the earlier GALA/GMT 1m full
  ladder correctly stayed `higher_timeframe_subclass_only_origin_blocked`, then
  a separate exact `GMTUSDT/5m` claim preserved the new timeframe root and
  passed hard `5bps/side` Gate 1 (`7` trades, raw `+2.79%`, `5bps=+2.09%`).
  Same-root downstream mechanics all exited `0`, but final admission stayed
  observation-only: `execution_candidate_actionable=false`,
  `execution_readiness=0.612608379429279`, `transition_hazard=0.9791004474920019`,
  `pda_hybrid_alignment=false`, `ranker_validation_ready=false`, and
  `mature_rows=0`. Lesson: higher-timeframe subclass evidence may be restarted
  only as a fresh exact-timeframe branch; even a true hard-cost exact survivor is
  not practical until PDA/transition/readiness and mature validation gates pass.
- TVR/XLB ORB+RVOL+VWAP density: 1m and 5m positive, downstream exact branch survived, execution remained observe/fail-closed.
- IBKR XLF/ARKK ladders: provider-status ready but direct historical fetches returned no usable rows; classify as provider-window blocker.
- YF regional banks, low-beta defensive, robotics, defense industrial: provider/AQ completed over 1m/5m/15m/30m/1h but 1m origin had no density or only one trade; stop before downstream.
- Kraken ATOM/XLM/SUI/INJ style crypto ladders: useful as public-provider negatives when 1m origin or cost-stressed positives do not appear.
