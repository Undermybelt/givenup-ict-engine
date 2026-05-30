# Fee Miscarriage Total Amnesty

- created_at: `2026-05-30T15:04:49+0800`
- owner: `codex`
- agent_name: `codex-fee-miscarriage-total-amnesty-20260530T150449+0800`
- repo: `/Users/thrill3r/projects-ict-engine/ict-engine`
- run_root: `/tmp/ict-engine-fee-miscarriage-total-amnesty-20260530T150449+0800`
- workdoc: `/tmp/ict-engine-fee-miscarriage-total-amnesty-20260530T150449+0800/workdoc.md`
- claim: `/tmp/ict-engine-agent-claims/board-b-factor-refinement/20260530T150449+0800-codex-fee-miscarriage-total-amnesty.claim`
- session_scope: `ETH/full_retained_session`
- rth_filter_applied: `false`
- status: `terminalized_fee_miscarriage_total_amnesty_fail_closed`
- promotion_allowed: `false`
- trade_usable: `false`
- update_goal: `false`

## Objective

Re-open historical profitability-factor rows that failed advancement because a
legacy fixed-bps fee wall was treated as futures commission authority. The slice
must rescue genuine fee false negatives into exact replay and keep non-profitable,
session-unverified, sparse, non-exported, or lifecycle-incomplete candidates
blocked.

## Current Collision Guard

Same-turn compact claim audit at start:

- `status=pass`
- `active_claims=0`
- `live_factor_processes=0`
- `trade_usable_true=0`
- `promotion_allowed_true=0`

This claim owns only the fee-miscarriage amnesty/replay lane above. It must not
take over unrelated factor claims and must not relax practical gates.

## Judgment Policy

- Futures fee authority is `support/scripts/research/instrument_cost_model.py`.
- Legacy `5bps/side` is diagnostic stress telemetry, not futures commission.
- A rescued row is only a rehearing/exact-replay candidate.
- `promotion_allowed`, `trade_usable`, and `update_goal` remain `false` unless
  current same-tree practical closure proves session, verified cost, exports,
  downstream lifecycle, and accepted paper/live/broker feedback.

## Planned Chain

1. Build a current all-amnesty scan over available Gate/AQ/rank artifacts.
2. Strictly classify old-fee false negatives, still-negative rows, and rows that
   need reprice/session replay.
3. If collision guard remains clear, run exact replay for rescued candidates.
4. Record positives separately from practical closure; no candidate is practical
   without the full lifecycle packet.

## Terminal Results

- terminal_decision: `old_fee_false_negatives_rescued_but_no_trade_usable_factor`
- terminal_status: `terminalized_fee_miscarriage_total_amnesty_fail_closed`
- source old fixed-5bps failure rows reheard: `11148`
- normalized rows in fee ledger: `13508`
- strict old-fee false negatives rescued to exact replay: `6`
- still blocked after fee rejudgment: `34`
- existing exact-AQ commands read back: `6`
- exact-AQ exit-zero commands: `6`
- exact-AQ positive rows: `2`
- exact-AQ negative rows: `4`
- requested trade-export JSON present: `0/6`
- `promotion_allowed=false`, `trade_usable=false`, `update_goal=false`
- `same_tree_practical_closure=null`

## Positive Exact-AQ Follow-Ups

1. `tomac_idxfut_volatility_shock_absorption_trend_continuation_15m_v1`
   NQ `15m` long `z2.4_abs0.5_h10_s1.6_t3_tr89`: AQ trades `599`,
   AQ total profit `+24.75%`, AQ PF `1.1609`.
2. `tomac_idxfut_volatility_shock_absorption_trend_continuation_5m_v1`
   NQ `5m` long `z1.8_abs0.38_h6_s1.2_t2_tr34`: AQ trades `2697`,
   AQ total profit `+22.56%`, AQ PF `1.0690`.

These two are fee-amnesty/exact-AQ positive follow-ups only. They are not
`trade_usable=true` because trade-export JSON is missing, downstream lifecycle
was not run in this slice, accepted paper/live/broker feedback is absent, and
same-tree practical closure is null.

## Rejected After Exact-AQ

- NQ `30m` short `z2_abs0.45_h8_s1.4_t2.4_tr55`: AQ trades `537`, total
  profit `-15.13%`, PF `0.9167`.
- NQ `30m` short `z1.8_abs0.38_h6_s1.2_t2_tr34`: AQ trades `631`, total
  profit `-25.22%`, PF `0.8625`.
- YM `5m` long `z2.4_abs0.5_h10_s1.6_t3_tr89`: AQ trades `1098`, total
  profit `-12.57%`, PF `0.9158`.
- NQ `15m` short `z2.4_abs0.5_h10_s1.6_t3_tr89`: AQ trades `602`, total
  profit `-2.89%`, PF `0.9846`.

## Terminal Artifacts

- terminal metrics:
  `/tmp/ict-engine-fee-miscarriage-total-amnesty-20260530T150449+0800/checks/terminal_metrics.json`
- terminal summary:
  `/tmp/ict-engine-fee-miscarriage-total-amnesty-20260530T150449+0800/summaries/terminal_summary.json`
- final adjudication packet:
  `/tmp/ict-engine-fee-miscarriage-total-amnesty-20260530T150449+0800/materials/fee_amnesty_final_adjudication.json`
- exact-AQ adjudication CSV:
  `/tmp/ict-engine-fee-miscarriage-total-amnesty-20260530T150449+0800/summaries/exact_aq_final_adjudication.csv`
- source fee replay queue:
  `/tmp/ict-engine-futures-fee-rescue-exact-replay-queue-20260530T132455+0800/checks/terminal_metrics.json`
- exact-AQ readback source:
  `/tmp/ict-engine-volatility-shock-absorption-exact-aqlaunch-20260530T144325+0800/checks/exact_aq_terminal_readback.json`

## Verification

- JSON terminal packet write/readback passed.
- Existing exact-AQ readback confirmed `2` positive and `4` negative rows.
- Requested trade-export files were checked and remained missing at `0/6`.
- Current compact audit later reported fresh foreign claims, so this slice did
  not launch new AutoQuant/provider/IBKR work after the initial no-blocker
  window closed.

## Classifier Repair Verification

- root cause repaired: old futures artifacts with positive gross PnL and
  negative legacy fixed-bps net were all classified as `needs_reprice_replay`
  when explicit instrument-cost net was absent. That let zero-edge
  high-frequency churn enter the rehearing queue even when verified futures
  all-in cost still made it negative.
- red test added:
  `test_high_frequency_churn_with_tiny_gross_edge_is_not_reprice_replay`; it
  first failed because the NQ `26304` trade / `8.52%` gross row classified as
  `needs_reprice_replay`.
- fix: `support/scripts/research/futures_real_cost_rescue_audit.py` now uses
  the canonical `instrument_cost_model` for legacy reprice rows when symbol,
  trade count, gross PnL, verified futures cost profile, and representative
  price are present. If gross edge is below real all-in cost, the row becomes
  `not_rescued_zero_edge_churn_realistic_cost_negative` with reason
  `gross_edge_below_realistic_all_in_cost`.
- compatibility: `stress_5bps_total_pct` is accepted as a legacy fixed-bps wall
  alias for ledger rows that otherwise prove real instrument-cost survival.
- verification commands passed: focused red/green test, full
  `test_futures_real_cost_rescue_audit`, 45-test instrument-cost/rescue/
  simulated-admission regression, fixed-bps source-check tests, targeted
  fixed-bps source check for touched source files, `check_script_manifest.py`,
  and `git diff --check` for touched files.
- flags remain `promotion_allowed=false`, `trade_usable=false`, and
  `update_goal=false`.

## Final Decision

`terminalized_fee_miscarriage_total_amnesty_fail_closed`. The old fee wall did
create six strict false negatives, and two of those remain positive after exact
AQ. None is promoted to practical use: `promotion_allowed=false`,
`trade_usable=false`, `update_goal=false`.
