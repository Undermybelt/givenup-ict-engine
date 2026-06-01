# SI 5m ATR simulated feedback direction/regime fail-closed

> 2026-05-24 schema note: `pda_hybrid_alignment` is historical telemetry only unless the current ict-engine source or readback contract still declares it active. Do not use old `pda_hybrid_alignment=true` or `false` lines in this reference as a current hard gate; classify with the live actionable/status/readiness/transition/ranker/mature-row fields.

Use when a futures branch has real cost-surviving Gate 1 evidence and the
same-root simulated-trade admission wrapper completes every downstream command,
but the execution tree still refuses action.

## Evidence packet

- Gate 1 root:
  `support/docs/experiments/actionable-regime-confidence/runs/20260520T042108+0800-codex-ibkr-si5m-atr-exhaustion-short-1m-gate1-v1`
- Simulated-admission root:
  `support/docs/experiments/actionable-regime-confidence/runs/20260520T042108+0800-codex-ibkr-si5m-atr-exhaustion-short-1m-gate1-v1/simulated-trade-admission-si-5m-atr-exhaustion-short-20260520T044928+0800`
- Branch path:
  `FUTURES -> precious_metals -> SI -> 5m -> TrendExpansion -> AtrExhaustionShort -> ibkr_si5m_atr_exhaustion_short_1m_gate1_v1`
- Best Gate 1 survivor: `SI/atr030_v125_hold30/5m_short`, `21` trades,
  raw `+2.53%`, `2bps=+1.69%`, `5bps=+0.43%`.
- Same-workspace simulated trades: `21` rows, `7` wins, `14` losses.
- Commands `01_auto_quant_results_import` through `19_policy_after_ranker` all
  exited `0` with no timeouts.
- `exact_branch_survived=true`.
- `ranker_validation_ready=true`.
- `path_ranker_score_visible_to_execution_tree=true`.
- `path_ranker_score_used_by_execution_tree=false`.

## Final readback

- `decision=si5m_atr_exhaustion_short_simulated_trade_admission_fail_closed`
- `mature_rows=2`
- `history_mature_rows=22`
- `execution_candidate_status=no_trade`
- `execution_candidate_actionable=false`
- `execution_gate_status=observe`
- `execution_readiness=0.2344186944501619`
- `transition_hazard=0.9679827616849933`
- `pda_hybrid_alignment=false`
- `promotion_allowed=false`
- `trade_usable=false`

## Root cause shape

This was not a CatBoost/trainer/bootstrap failure. The hard blocker was
direction and regime-family disagreement at execution admission:

- Gate 1 branch identity says `TrendExpansion -> AtrExhaustionShort` and the
  selected factor is explicitly short.
- `workflow_snapshot.json` / Pre-Bayes readback reports current market state as
  `RangeConsolidation/TightRange`, with canonical structural active regime
  `range`.
- Higher-timeframe direction bias is bearish, but `execution_candidate.json`
  selected `Bull` / `trade_direction=Bull`.
- Pre-Bayes filtered factor alignment to `mixed`, uncertainty to `high`, and
  gate status to `observe_only`.
- Conflict flags include `multi_timeframe_direction_conflict`,
  `pda_regime_family_disagreement`, `pda_sequence_cluster_weak`, and
  `pda_sequence_low_consistency`.
- PDA DTW/HMM consistency was only `0.436`, below the stability floor.
- Execution tree branch was `transition_guardrail` with hint
  `execution_guarded_due_to_pda_hybrid_disagreement`.

## Operating rule

Do not promote or relaunch this shape as another generic simulated-feedback
repair. The next same-root SI attempt must first make AQ, Pre-Bayes/BBN,
CatBoost/ranker, and execution candidate agree on the same short direction and
an honest regime root. If the live market state is actually range/choppy, either
re-root the factor as a range/exhaustion short with truthful metadata and rerun
Gate 1, or wait for a real TrendExpansion/AtrExhaustionShort context. Do not
lower `transition_hazard < 0.60`, `pda_hybrid_alignment=true`, or
`execution_readiness >= 0.65` gates.
