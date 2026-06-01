# 2026-05 regime-rooted factor training lessons

> 2026-05-24 schema note: `pda_hybrid_alignment` is historical telemetry only unless the current ict-engine source or readback contract still declares it active. Do not use old `pda_hybrid_alignment=true` or `false` lines in this reference as a current hard gate; classify with the live actionable/status/readiness/transition/ranker/mature-row fields.

Session class: ict-engine Auto-Quant profitability search with strict downstream admission.

## Durable lessons

- Keep the branch identity rooted as: market -> product -> symbol -> base timeframe -> main regime -> sub-regime(s) -> first profit factor -> overlay profit factor(s).
- Do not treat a strong sibling timeframe as a pass for the declared root. If the 1m root is requested, the exact 1m row must survive costs and density; a strong 5m sibling is only context unless the branch root is explicitly 5m.
- Stop entry/exit/wick micro-tuning after repeated downstream failures where cost/density survive but `pda_hybrid_alignment` flips false or `transition_hazard` worsens. That pattern means the next step is downstream regime/PDA admission diagnosis or a sibling-family search, not another threshold tweak.
- Full ladder coverage matters, but provenance must be explicit:
  - fresh provider fetch is preferred for live-readiness;
  - cache replay can support structural diagnosis only when labelled `local_cache_replay=true` and `fresh_provider_parity=false`;
  - provider-window timeouts are blockers, not evidence.
- Kraken/crypto full-ladder fetches can exceed 600s before closing the loop. If this happens, mark the run as `provider_window_blocker`, list completed fetch intervals, and do not infer Gate/downstream status from partial files.
- For Yahoo/YF, 4h may be unavailable through the fetch path; record `actual_4h_coverage=false` instead of pretending full coverage. For TVR/IBKR/Kraken, include 4h when provider path supports it.

## Gate interpretation pattern

A candidate remains observation-only unless all hold at downstream readback:

- real cost after fees remains positive with enough trade density;
- AQ -> Pre-Bayes/BBN/CatBoost/path-ranker -> execution tree direction stays consistent on the same rooted path;
- `transition_hazard < 0.60`;
- `pda_hybrid_alignment=true`;
- stable `execution_readiness >= 0.65`;
- execution candidate is actionable/trade-ready, not just visible/observe/no_trade.

## Session examples

- NET 5m `pda_sequence_consistency_light_v1`: good observation candidate (`32` trades, 5bps positive, `execution_readiness=0.67`, `pda_hybrid_alignment=true`) but failed strict admission because `transition_hazard=0.63049` and execution remained observe/no_trade.
- NET 5m overlays (`entry_window_trim`, `late_session_hazard_trim`, `hazard_micro_trim`, `soft_transition_stability`) preserved or partly preserved cost/density but broke PDA alignment and worsened hazard; do not keep stacking these threshold overlays.
- TVR CRWD 5m trend-reclaim full ladder had strong Gate 1 cost/density (`23` trades, 5bps positive), but downstream failed with low readiness, high hazard, PDA=false, and cache replay provenance; not live-ready.
- CRWD 1m trend-reclaim full ladder failed the exact 1m root despite stronger 5m sibling; do not promote sibling success to a 1m-root branch.
- IBKR UUP dollar ETF Keltner reclaim exposed two reusable guardrails: keep the
  symbol out of the branch id (`dollar_etf_keltner_reclaim_v1`, not
  `uup_dollar_etf...`) and do not downstream sparse higher-timeframe survivors.
  The retained-real ladder had clean AQ exits and a `1h` 5bps survivor
  (`9` trades, `5bps=+0.43%`), but the `1m` origin failed (`19` trades,
  `2bps=-0.83%`, `5bps=-1.97%`) and density was far below target, so classify
  as `gate1_higher_timeframe_cost_survivor_observation`.
