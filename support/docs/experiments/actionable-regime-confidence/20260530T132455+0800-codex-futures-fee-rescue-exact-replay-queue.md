# Futures Fee-Rescue Exact-Replay Queue - 20260530T132455+0800

## Purpose

Re-open historical futures factor candidates that were rejected by the old fixed
`5bps/side` commission wall after the corrected futures cost model landed. The
goal is to rescue fee-model false negatives into an exact-replay queue while
leaving non-rescuable, sparse, session-unverified, or cost-unverified rows
blocked.

## Route and Current State

- Route alias: `sd/ict-engi-fact-rese-muta`.
- Repo: `/Users/thrill3r/projects-ict-engine/ict-engine`.
- Branch/head at claim creation: `main` / `ec8e52d7`.
- Runtime skill: `/Users/thrill3r/.hermes/skills/software-development/ict-engi-fact-rese-muta/SKILL.md`.
- Same-turn compact claim audit before this slice:
  - `status=needs_attention`.
  - `live_factor_processes=0`.
  - `active_claims=1`.
  - fresh active claim: `20260530T131450+0800-codex-realized-vol-1h-downstream-feedback.claim`.
  - `trade_usable_true=0`.
  - `promotion_allowed_true=0`.

## Non-Collision Decision

This is a no-launch local rehearing slice. It does not start AutoQuant, IBKR,
provider fetches, paper trading, or simulated/live execution while a fresh
active downstream-feedback claim exists. It only reads retained fee-rescue
artifacts and writes a queue packet for later exact replay.

## Judgment Policy

- Futures fee authority is `support/scripts/research/instrument_cost_model.py`.
- Legacy `5bps/side` is stress telemetry only, not a futures commission gate.
- `rescued_for_exact_replay` means old-fee false negative only; it is not a
  practical promotion.
- Keep `promotion_allowed=false`, `trade_usable=false`, and `update_goal=false`
  until exact AQ/provider/downstream lifecycle gates pass.
- Keep blocked rows blocked when the row is sparse, density-failed,
  session-unverified, RTH-only, positive-year weak, or cost-unverified.

## Artifacts

- Factor-local workdoc:
  `/tmp/ict-engine-futures-fee-rescue-exact-replay-queue-20260530T132455+0800/workdoc.md`
- Claim:
  `/tmp/ict-engine-agent-claims/board-b-factor-refinement/20260530T132455+0800-codex-futures-fee-rescue-exact-replay-queue.claim`
- Prior judgment ledger input:
  `/tmp/ict-engine-futures-fee-rescue-judgment-ledger-20260530T125732+0800/checks/terminal_metrics.json`

## Initial Status

`active_no_launch_fee_rescue_queue_recheck`. Practical flags are false.

## Terminal Results

- terminal_decision: `old_5bps_false_negatives_rescued_to_exact_replay_queue_only`
- terminal_status: `terminal_no_launch_fee_rescue_queue_ready`
- source_old_5bps_failure_rows: `11148`
- source_rows_normalized: `13508`
- rescued_for_exact_replay_count: `6`
- blocked_after_fee_rejudgment_count: `34`
- not_rescued_sample_count: `100`
- promotion_allowed: `false`
- trade_usable: `false`
- update_goal: `false`

## Terminal Artifacts

- terminal metrics:
  `/tmp/ict-engine-futures-fee-rescue-exact-replay-queue-20260530T132455+0800/checks/terminal_metrics.json`
- exact replay queue JSON:
  `/tmp/ict-engine-futures-fee-rescue-exact-replay-queue-20260530T132455+0800/materials/exact_replay_rescue_queue.json`
- rescued CSV:
  `/tmp/ict-engine-futures-fee-rescue-exact-replay-queue-20260530T132455+0800/summaries/rescued_for_exact_replay.csv`
- blocked CSV:
  `/tmp/ict-engine-futures-fee-rescue-exact-replay-queue-20260530T132455+0800/summaries/blocked_after_fee_rejudgment.csv`
- terminal summary:
  `/tmp/ict-engine-futures-fee-rescue-exact-replay-queue-20260530T132455+0800/summaries/terminal_summary.md`

## Exact-Replay Queue

1. `tomac_idxfut_volatility_shock_absorption_trend_continuation_30m_v1` NQ 30m short `z2_abs0.45_h8_s1.4_t2.4_tr55`: trades `462`, instrument-cost net `+13.010348%`, old 5bps net `-30.260114%`, PF `1.140022`, positive years `4/5`.
2. `tomac_idxfut_volatility_shock_absorption_trend_continuation_15m_v1` NQ 15m long `z2.4_abs0.5_h10_s1.6_t3_tr89`: trades `443`, instrument-cost net `+12.787945%`, old 5bps net `-28.846657%`, PF `1.197519`, positive years `3/5`.
3. `tomac_idxfut_volatility_shock_absorption_trend_continuation_30m_v1` NQ 30m short `z1.8_abs0.38_h6_s1.2_t2_tr34`: trades `525`, instrument-cost net `+12.631436%`, old 5bps net `-36.546832%`, PF `1.142917`, positive years `4/5`.
4. `tomac_idxfut_volatility_shock_absorption_trend_continuation_5m_v1` YM 5m long `z2.4_abs0.5_h10_s1.6_t3_tr89`: trades `437`, instrument-cost net `+8.351408%`, old 5bps net `-30.635911%`, PF `1.211091`, positive years `3/5`.
5. `tomac_idxfut_volatility_shock_absorption_trend_continuation_5m_v1` NQ 5m long `z1.8_abs0.38_h6_s1.2_t2_tr34`: trades `2303`, instrument-cost net `+4.243476%`, old 5bps net `-211.63957%`, PF `1.021221`, positive years `4/5`.
6. `tomac_idxfut_volatility_shock_absorption_trend_continuation_15m_v1` NQ 15m short `z2.4_abs0.5_h10_s1.6_t3_tr89`: trades `518`, instrument-cost net `+1.788416%`, old 5bps net `-46.813148%`, PF `1.01916`, positive years `3/5`.

## Verification

- Queue builder passed and wrote terminal metrics, exact replay queue JSON, and CSV ledgers.
- JSON readback passed for terminal metrics and queue JSON.
- Queue assertions passed: rescued `6`, blocked `34`, practical flags false.
- Focused unittest command passed: `25` fee-rescue / false-negative revival / exact-aqprep tests.

## Final Decision

`terminal_no_launch_fee_rescue_queue_ready`. Six old-fee false negatives are
rescued into the exact-replay queue. Nothing is marked practical from this
ledger; exact AQ and downstream lifecycle proof are still required.
