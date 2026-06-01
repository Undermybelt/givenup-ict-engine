# IBKR M2K PDA-floor admission and Auto-Quant runtime lessons (2026-05-20)

> 2026-05-24 schema note: `pda_hybrid_alignment` is historical telemetry only unless the current ict-engine source or readback contract still declares it active. Do not use old `pda_hybrid_alignment=true` or `false` lines in this reference as a current hard gate; classify with the live actionable/status/readiness/transition/ranker/mature-row fields.

## Context
Regime-rooted profitability-factor training continued under the strict path grammar:
`market -> product -> symbol -> timeframe -> main_regime -> sub_regime -> first_profit_factor -> overlay_profit_factor...`.

Primary candidates:
- MNQ 1m `LiquiditySweepReclaim`
- M2K 1m `LiquiditySweepRejectShort -> rvol_pda_guard -> pda_consistency_floor`

## Durable lessons

### 1. Auto-Quant trade extraction must run inside Auto-Quant's venv
A simulated/admission helper imported a generated `run_tomac.py` from the current Python process and failed when `freqtrade` was absent there, even though `<managed-auto-quant-checkout>/.venv/bin/python` had `freqtrade 2026.3`.

Reusable fix:
- Detect `AQ_PY = <managed-auto-quant-checkout>/.venv/bin/python` when present.
- Execute `run_tomac.py` extraction in a subprocess using `AQ_PY`, with JSON sentinel markers around the emitted trades.
- Treat this as an interpreter-selection bug, not as factor evidence or a reason to install dependencies globally.

### 2. Expanding a 1m futures window can destroy cost survival
MNQ liquidity-sweep root passed a short 2D slice with 7 trades and +0.14% after 2bps/side, but the 7D expansion produced 43-76 trades and all variants flipped negative after 1-2bps/side.

Rule:
- Max-window expansion is mandatory before confidence, but if the expanded real-provider 1m root fails cost survival, stop at Gate 1.
- Do not use the shorter passing slice to justify downstream or promotion.

### 3. Simulated feedback can improve one blocker while exposing another
MNQ simulated/admission after 7 simulated trades improved:
- `transition_hazard=0.5821` (<0.60)
- `pda_hybrid_alignment=true`

But still failed:
- `execution_readiness=0.4931` (<0.65)
- `mature_rows=2`, `history_mature_rows=8`

Rule:
- Do not promote just because transition/PDA gates improve; readiness and maturity gates remain binding.

### 4. Strong Gate 1 does not imply downstream readiness
M2K `rvol_pda_guard` was strong at Gate 1:
- 4/4 variants survived 2bps and 5bps
- best row: 31 trades, +2.13% after 2bps/side, +0.27% after 5bps/side

But simulated/admission stayed fail-closed:
- `execution_readiness=0.3181`
- `transition_hazard=0.9185`
- `pda_hybrid_alignment=false`

Rule:
- A strong cost-stressed Gate 1 branch should proceed to same-root blocker repair, not promotion.

### 5. PDA consistency floor is the correct next overlay shape when rvol_pda_guard fails PDA/transition
M2K `pda_consistency_floor` preserved enough edge:
- 17 trades
- raw +2.79%
- 2bps +2.11%
- 5bps +1.09%
- exact rooted branch preserved

Rule:
- When `rvol_pda_guard` has cost/density but fails current transition/readiness readback, try at most one same-root consistency-floor repair before broader factor rotation.
- Still require downstream admission under the live source/readback contract: active transition/readiness thresholds, exact branch survival, actionable execution materialization, ranker usage, and mature/validation row gates. Do not require retired `pda_hybrid_alignment`.

### 6. Downstream/admission scripts can silently point at stale Gate 1 roots
The M2K PDA-floor admission wrapper had a hardcoded `SOURCE` pointing to an older run root. Updating it to the latest Gate 1 run was required before admission was meaningful.

Rule:
- Before running an admission/downstream wrapper cloned from a previous candidate, assert `SOURCE` equals the latest chosen Gate 1 root and that `WORKSPACE`, `GATE1_AQ_SYMBOL`, `PACKAGE_ID`, and `BRANCH_PATH` match the same exact branch.

### 7. Long admission readbacks should run in background and be polled by artifacts
M2K PDA-floor admission exceeded a foreground 600s budget while inside analyze/readback. A background process with artifact polling is better than killing the lane and losing partial state.

Rule:
- For admission scripts that run `analyze` after trade ingest/ranker enablement, use a background process or larger async orchestration.
- Poll `checks/*.exit`, `command-output/*.cmd`, and final `simulated_trade_admission_metrics.json`; classify incomplete runs as runtime timeout, not factor verdicts.

### 8. Clean mechanics can still prove only fail-closed parity
A clean same-root M2K PDA-floor admission rerun completed `19/19` commands with
exit `0`, ingested `17` same-Auto-Quant-workspace simulated trades, preserved the
exact branch, made CatBoost/ranker validation ready, and made the score visible
to the execution tree. It still failed practical gates:
- `execution_candidate_status=no_trade`
- `execution_readiness=0.3181`
- `transition_hazard=0.9185`
- `pda_hybrid_alignment=false`
- `path_ranker_score_used_by_execution_tree=false`
- `mature_rows=2`, `history_mature_rows=18`

Runtime MTF readback still used explicit `1m/15m/1h` frames and reported
`5m/30m/4h/1d` missing even though cleaned ladder files were generated as side
evidence. Generated ladder files are not proof that the execution runtime
consumed the full ladder.

Rule:
- Once all mechanics, branch identity, import/prior, CatBoost registration, and
  ranker visibility are clean, stop repeating simulation-only admission.
- The remaining same-root blocker is substantive PDA/hybrid disagreement,
  transition hazard, current mature validation, and score consumption by the
  execution tree.
- Next aligned work needs either longer real provider context that makes the
  higher frames mechanically valid, or an explicit runtime full-ladder subset
  contract that marks short legs insufficient before rerunning exact downstream.

### 9. Exact Auto-Quant seed material must use the profiled runtime strategy dir
The M2K exact-seed repair exposed two bridge bugs before factor measurement:
- standalone Freqtrade strategy material was previously converted into a generic
  long EMA/RSI scaffold instead of preserving `can_short`, `timeframe`, and
  `enter_short`/`exit_short`;
- synthetic Auto-Quant profile readiness/run uses `user_data/strategies_external`,
  while seed material evidence was initially written to the unprofiled
  `user_data/strategies` directory.

Reusable fix:
- For standalone `IStrategy` material, copy the source body as an exact seed and
  rewrite only the first strategy class name to the generated seed identity.
- In command-entry seed materialization, use the state/profile-adjusted
  `auto_quant_workspace_config_for_state`, not the unprofiled workspace config.
- Verify with both a unit test and live handoff readiness: `auto_quant_active_strategy_count=1`,
  `strategies_dir=user_data/strategies_external`, futures/isolated config, and
  `run_tomac.py` loading the exact short seed.

M2K proof after the bridge repair:
- `run_tomac.py` loaded the exact short seed from `strategies_external` under
  isolated futures mode.
- Result: `17` shorts, raw `+2.79%`, `1bps/side=+2.45%`,
  `2bps/side=+2.11%`, `5bps/side=+1.09%`, PF `8.4044`.
- This repairs seed/runtime parity only. It does not promote the branch while
  downstream still reports `no_trade`, high transition hazard, PDA disagreement,
  and readiness below gate.

### 10. Do not parse `quality_ready=true` as terminal ranker validation readiness
The exact-seed downstream readback exposed a reporting bug: execution-tree
lineage used substring matching for `ready=true`, so a validation line like
`quality_ready=true ... ready=false` was reported as `ranker_validation_ready=true`.

Reusable rule:
- Parse terminal `ready=` as an exact whitespace-delimited token, not a
  substring.
- If validation rows are short (`raw_scored_mature`, `production_validation`, or
  `observation_validation` below the gate), the path-ranker score may remain
  visible but must not be considered validation-ready or used by the execution
  tree.
- In M2K PDA-floor readbacks, corrected status is `ranker_validation_ready=false`
  with `raw_scored_mature=17/30`, `production_validation=16/30`, and
  `observation_validation=16/30`; the branch remains fail-closed.
