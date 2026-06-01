# SI 15m Turtle Soup downstream fail-closed, 2026-05-20

> 2026-05-24 schema note: `pda_hybrid_alignment` is historical telemetry only unless the current ict-engine source or readback contract still declares it active. Do not use old `pda_hybrid_alignment=true` or `false` lines in this reference as a current hard gate; classify with the live actionable/status/readiness/transition/ranker/mature-row fields.

Use this when an IBKR precious-metals Turtle Soup / false-breakout branch looks
good at Gate 1 and someone is tempted to call it practical after downstream
mechanics pass.

## Evidence

- Source Gate 1: `SI/15m` retained-cleaned IBKR ladder replay,
  `FUTURES -> precious_metals -> SI -> 15m -> FalseBreakoutReversal -> TurtleSoupReversal -> ibkr_si15m_turtle_soup_false_breakout_cleaned_gate1_v1`.
- Cost survivors: `SI/soup_balanced/15m` had `7` trades, raw `+2.39%`,
  `2bps=+2.11%`, `5bps=+1.69%`; `SI/soup_dense/15m` had `16` trades,
  raw `+1.91%`, `2bps=+1.27%`, `5bps=+0.31%`.
- Exact downstream completed steps `01-16` with exit `0`: Auto-Quant import,
  prior init, seed/final analyze, workflow, Pre-Bayes, structural target export,
  CatBoost train/apply/register, score writeback, runtime enable, policy readback,
  and final export.
- Final verdict: `exact_si15m_turtle_soup_downstream_fail_closed`.

## Blocking predicates

- `execution_candidate_status=fail_closed`
- `execution_candidate_actionable=false`
- `execution_readiness=0.4226170943776133`
- `transition_hazard=0.9658840155768782`
- `pda_hybrid_alignment=false`
- `mature_rows=0`, `history_mature_rows=0`, `raw_scored_mature=0/30`
- `production_validation=0/30`, `observation_validation=0/30`
- `fresh_provider_parity=false` because the packet used retained-cleaned replay.

## Rule

A public Turtle Soup branch with 5bps Gate 1 survivors and clean downstream
exits is still observation-only if PDA/transition/readiness/mature-validation
gates fail. Do not promote it, clone it as a practical factor, or add light
overlays. The next same-root work must directly reduce transition hazard, align
PDA with the reversal root, add mature same-root validation, and preferably
refresh provider parity.
