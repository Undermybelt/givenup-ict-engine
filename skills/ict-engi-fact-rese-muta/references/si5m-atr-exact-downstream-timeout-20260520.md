# SI 5m ATR exact downstream same-file MTF timeout

> 2026-05-24 schema note: `pda_hybrid_alignment` is historical telemetry only unless the current ict-engine source or readback contract still declares it active. Do not use old `pda_hybrid_alignment=true` or `false` lines in this reference as a current hard gate; classify with the live actionable/status/readiness/transition/ranker/mature-row fields.

Date: 2026-05-20

Use this note when considering another exact downstream rerun for the IBKR
`SI/5m` `TrendExpansion -> AtrExhaustionShort` branch.

The exact downstream rerun at
`support/docs/experiments/actionable-regime-confidence/runs/20260520T042108+0800-codex-ibkr-si5m-atr-exhaustion-short-1m-gate1-v1/downstream-exact-si-5m-atr-exhaustion-short-20260520T140919+0800/`
kept the Gate 1 survivor context but did not improve admission:

- Auto-Quant import/prior, workflow, Pre-Bayes, export, CatBoost train/apply,
  ICT score apply, trainer registration, runtime enable, policy, and final
  export exited `0`
- both analyze calls timed out: `03_analyze_seed=124` and
  `12_analyze_after_ranker=124`
- final metrics: `all_commands_ok=false`, `exact_branch_survived=false`,
  `mature_rows=0`, `execution_readiness=0.0`, `transition_hazard=1.0`,
  `pda_hybrid_alignment=false`, `promotion_allowed=false`,
  `trade_usable=false`
- ranker validation was still absent:
  `raw_scored_mature=0/30`, `production_validation=0/30`,
  `observation_validation=0/30`

The wrapper used the same retained `5m` file as `ltf/mtf/htf`. Treat this as a
same-file MTF downstream timeout sample, not a factor promotion or a new negative
Gate 1 verdict. The better current evidence for this ATR branch is the earlier
valid-MTF probe
`analyze-valid-mtf-probe-si5m-atr-20260520T135401+0800`, which materialized
execution artifacts but still failed execution predicates.

Rule: do not repeat exact SI `5m` ATR downstream wrappers in same-file MTF form.
The next useful work must use a valid MTF subset and directly target PDA/regime
alignment, transition hazard, execution readiness, exact execution-candidate
materialization, or real/current validation rows.
