# Fee Amnesty Adjudication - 20260530T135157+0800

## Purpose

Re-adjudicate candidates that previously failed advancement because futures
fees were judged with the old fixed `5bps/side` stress wall. The scope is
strict: rescue only fee-model false negatives into a replay queue, and keep
all candidates blocked when the evidence gap is not actually a fee-model error.

## Current State

- Route alias: `sd/ict-engi-fact-rese-muta`.
- Repo: `/Users/thrill3r/projects-ict-engine/ict-engine`.
- Runtime skill: `/Users/thrill3r/.hermes/skills/software-development/ict-engi-fact-rese-muta/SKILL.md`.
- Same-turn compact audit before this slice:
  - `status=needs_attention`.
  - `live_factor_processes=2`.
  - `valid_active_claims=2`.
  - `promotion_allowed_true=0`.
  - `trade_usable_true=0`.
- Live runtime roots avoided:
  - `/tmp/ict-engine-volatility-shock-absorption-exact-aqlaunch-20260530T134520+0800`.
  - `/tmp/ict-engine-hmm-tsmom-sideinfo-local-gate1-20260530T134150+0800`.

## Non-Collision Decision

This is a no-launch adjudication slice. It does not start AutoQuant, IBKR,
provider fetches, Freqtrade, paper trading, simulated/live execution, or any new
factor runtime while current claims and live roots are active.

## Judgment Policy

- Futures cost authority is `support/scripts/research/instrument_cost_model.py`.
- Legacy `5bps/side` is stress telemetry for futures, not the promotion fee
  model.
- `rescued` means old-fee false negative only. It is not a practical promotion.
- Keep `promotion_allowed=false`, `trade_usable=false`, and `update_goal=false`
  unless same-tree practical lifecycle evidence later passes.
- Keep candidates blocked when blockers are sample, density, ETH/session scope,
  year stability, missing price/trades/gross, unverified cost, or still-negative
  after current instrument cost.

## Inputs

- Prior fee reclassification root:
  `/tmp/ict-engine-fee-reclassification-audit-20260530T125516+0800`.
- Prior judgment ledger root:
  `/tmp/ict-engine-futures-fee-rescue-judgment-ledger-20260530T125732+0800`.
- Prior exact replay queue root:
  `/tmp/ict-engine-futures-fee-rescue-exact-replay-queue-20260530T132455+0800`.

## Artifacts

- Workdoc:
  `/tmp/ict-engine-fee-amnesty-adjudication-20260530T135157+0800/workdoc.md`
- Claim:
  `/tmp/ict-engine-agent-claims/board-b-factor-refinement/20260530T135157+0800-codex-fee-amnesty-adjudication.claim`
- Run root:
  `/tmp/ict-engine-fee-amnesty-adjudication-20260530T135157+0800`

## Initial Status

`active_no_launch_fee_amnesty_adjudication`. Practical flags are false.

## Terminal Results

- terminal_decision: `fee_false_negatives_rescued_only_when_current_fee_model_and_non_cost_gates_pass`
- terminal_status: `terminal_no_launch_fee_amnesty_adjudicated`
- reclassification_artifacts_scanned: `1297`
- candidate_rows_classified: `1022`
- revival_recheck_raw_count: `140`
- revival_recheck_unique_count: `94`
- rows_normalized: `13508`
- old_5bps_failure_rows: `11148`
- rescued_for_exact_replay_count: `6`
- blocked_after_fee_rejudgment_count: `34`
- strict_referee_split: `31 fee_cleared_but_blocked_non_cost + 3 needs_eth_full_session_replay`
- promotion_allowed: `false`
- trade_usable: `false`
- update_goal: `false`

## Terminal Artifacts

- terminal metrics:
  `/tmp/ict-engine-fee-amnesty-adjudication-20260530T135157+0800/checks/terminal_metrics.json`
- adjudication JSON:
  `/tmp/ict-engine-fee-amnesty-adjudication-20260530T135157+0800/materials/fee_amnesty_adjudication.json`
- rescued CSV:
  `/tmp/ict-engine-fee-amnesty-adjudication-20260530T135157+0800/summaries/rescued_for_exact_replay.csv`
- blocked CSV:
  `/tmp/ict-engine-fee-amnesty-adjudication-20260530T135157+0800/summaries/blocked_after_fee_rejudgment.csv`
- terminal summary:
  `/tmp/ict-engine-fee-amnesty-adjudication-20260530T135157+0800/summaries/terminal_summary.md`

## Rescued For Exact Replay

1. `tomac_idxfut_volatility_shock_absorption_trend_continuation_30m_v1` NQ 30m short `z2_abs0.45_h8_s1.4_t2.4_tr55`: trades `462`, instrument-cost `+13.010348%`, old 5bps `-30.260114%`, PF `1.140022`, positive years `4/5`.
2. `tomac_idxfut_volatility_shock_absorption_trend_continuation_30m_v1` NQ 30m short `z1.8_abs0.38_h6_s1.2_t2_tr34`: trades `525`, instrument-cost `+12.631436%`, old 5bps `-36.546832%`, PF `1.142917`, positive years `4/5`.
3. `tomac_idxfut_volatility_shock_absorption_trend_continuation_5m_v1` NQ 5m long `z1.8_abs0.38_h6_s1.2_t2_tr34`: trades `2303`, instrument-cost `+4.243476%`, old 5bps `-211.63957%`, PF `1.021221`, positive years `4/5`.
4. `tomac_idxfut_volatility_shock_absorption_trend_continuation_15m_v1` NQ 15m long `z2.4_abs0.5_h10_s1.6_t3_tr89`: trades `443`, instrument-cost `+12.787945%`, old 5bps `-28.846657%`, PF `1.197519`, positive years `3/5`.
5. `tomac_idxfut_volatility_shock_absorption_trend_continuation_5m_v1` YM 5m long `z2.4_abs0.5_h10_s1.6_t3_tr89`: trades `437`, instrument-cost `+8.351408%`, old 5bps `-30.635911%`, PF `1.211091`, positive years `3/5`.
6. `tomac_idxfut_volatility_shock_absorption_trend_continuation_15m_v1` NQ 15m short `z2.4_abs0.5_h10_s1.6_t3_tr89`: trades `518`, instrument-cost `+1.788416%`, old 5bps `-46.813148%`, PF `1.01916`, positive years `3/5`.

## Corrected Referee Split

The strict corrected referee rerun against the judgment-ledger CSVs returned
`row_count=40`:

- `rescued_for_exact_aq=6`
- `fee_cleared_but_blocked_non_cost=31`
- `needs_eth_full_session_replay=3`
- `not_rescued_count=0`

Only the six strict rescues may go to exact-AQ replay. The 31 rows blocked by
non-fee gates and the 3 rows needing ETH/full-session replay remain blocked.
No row from this adjudication is `promotion_allowed` or `trade_usable`.

Strict split artifacts:

- `/tmp/ict-engine-fee-amnesty-adjudication-20260530T135157+0800/checks/futures_real_cost_rescue_audit_terminal.json`
- `/tmp/ict-engine-fee-amnesty-adjudication-20260530T135157+0800/summaries/rescued_for_exact_aq_terminal.csv`
- `/tmp/ict-engine-fee-rehearing-classification-referee-20260530T132959+0800/checks/futures_real_cost_rescue_audit_referee_corrected.json`

## Verification

- Prior queue JSON and terminal metrics parsed with `python3 -m json.tool`.
- Prior queue assertions passed: rescued `6`, blocked `34`, old 5bps failures
  `11148`, normalized rows `13508`, practical flags false.
- Bounded aggregate re-run returned zero row-level candidates because aggregate
  terminal JSON no longer contains raw candidate rows; this is recorded as a
  readback limitation, not a no-rescue verdict.
- Same-turn corrected referee rerun with `futures_real_cost_rescue_audit.py`
  returned `row_count=40`, `rescued_for_exact_aq=6`,
  `fee_cleared_but_blocked_non_cost=31`, `needs_eth_full_session_replay=3`,
  and practical flags false.
- Focused unit tests passed: `32` fee-rescue / false-negative revival /
  exact-aqprep tests.

## Final Decision

Six old-fee false negatives are rescued into exact replay only. Thirty-four
rows remain blocked after fee rejudgment because their blockers are not just the
old fee model. No factor is marked `promotion_allowed` or `trade_usable` from
this adjudication.
