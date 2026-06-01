# TrendExpansion BOCPD 30m Density-Lift Candidates

Use this note after the 2026-05-31 strict TrendExpansion-only
BOCPD/dynamic-momentum/VHF-CHOP exact-AQ packet. It records the first successful
30m repair candidates and the remaining fail-closed boundary.

## Slice

- Date: 2026-06-01
- Repo: `<ict-engine-repo>`
- Repo packet: `support/docs/experiments/actionable-regime-confidence/20260601T000500+0800-codex-trendexpansion-bocpd-30m-split-repair.md`
- Run root: `/tmp/ict-engine-trendexpansion-bocpd-30m-split-repair-20260601T000500+0800`
- Metrics: `/tmp/ict-engine-trendexpansion-bocpd-30m-split-repair-20260601T000500+0800/checks/terminal_metrics.json`
- Claim: `/tmp/ict-engine-agent-claims/board-b-factor-refinement/20260601T000500+0800-codex-trendexpansion-bocpd-30m-split-repair.claim`

## Contract

- `entry_allowed_regimes=TrendExpansion` only.
- Other regimes are `reference_veto_only_no_entry`.
- Entry and exit signals use completed-bar evidence; entries are next bar or
  later.
- Realized future labels are not used for entry, exit, or regime admission.
- `session_scope=ETH/full_retained_session`; `rth_filter_applied=false`.
- Practical flags remain false until downstream lifecycle and accepted
  paper/live/broker execution feedback pass.

## Exact-AQ Result

The wrapper ran nine 30m repair variants after fixing a self-blocking launch
guard where the compact claim audit counted the parent runner PID as a live
`run_tomac` process. The guard now ignores only the current wrapper PID while
still respecting foreign live runtime roots.

Two variants passed the local exact-AQ repair gate after verified NQ IBKR
commission, split/year stability, and density review:

| Variant | Trades | Trades/day | NQ IBKR-fee net pct | Net PF | Splits | Years | Verdict |
|---|---:|---:|---:|---:|---|---|---|
| `bidir_density_lift` | 645 | 0.355372 | +41.399356 | 1.228874 | +13.172679 / +13.647338 / +14.579339 | 5/5 | repair_candidate_needs_downstream |
| `bidir_density_lift_fast_breakout` | 655 | 0.360882 | +36.341604 | 1.193007 | +9.111969 / +13.831995 / +13.397640 | 5/5 | repair_candidate_needs_downstream |

The previous best `bidir_strict_short` stayed fail-closed only on density:
553 trades, 0.304683 trades/day, +43.978946% net after NQ IBKR fee, PF
1.288958, all splits positive, and 5/5 years positive.

## Reusable Lesson

This is the first 30m child in this strict TrendExpansion BOCPD branch that
clears cost, split, year, and density at exact-AQ review, but it is not
trade-usable. Do not report it as `trade_usable=true`, `promotion_allowed=true`,
or same-tree practical closure. The next non-duplicative work is downstream
lifecycle preparation for `bidir_density_lift` first, then accepted paper/live or
broker execution feedback. Without that feedback and execution-tree/path-ranker
closure, stop at `repair_candidate_needs_downstream`.

## 2026-06-01 Downstream/Feedback Readback

The first `bidir_density_lift` downstream prep packet was created at:

- Prep root: `/tmp/ict-engine-trendexpansion-bocpd-30m-density-lift-downstream-prep-20260601T005757+0800`
- Strategy library: `/tmp/ict-engine-trendexpansion-bocpd-30m-density-lift-downstream-prep-20260601T005757+0800/materials/strategy_library.json`
- Rejected exact-AQ feedback: `/tmp/ict-engine-trendexpansion-bocpd-30m-density-lift-downstream-prep-20260601T005757+0800/feedback/bocpd_30m_density_lift_exact_aq_backtest_rejected_for_practical_closure.jsonl`
- Terminal metrics: `/tmp/ict-engine-trendexpansion-bocpd-30m-density-lift-downstream-prep-20260601T005757+0800/checks/terminal_metrics.json`

It preserved `entry_allowed_regimes=["TrendExpansion"]`, kept all non-TrendExpansion
states as `reference_veto_only_no_entry`, and confirmed retained-session coverage
from `NQ_USD-30m.feather` with `non_rth_row_count=42521`. It still stayed
`simulated_feedback_downstream_prep_fail_closed`: the 645 exact-AQ rows were
written only as rejected observation rows with `broker_realized=false`,
`broker_fill_evidence=false`, and `accepted_execution_feedback=false`.

The accepted-feedback readback root was:

- Readback root: `/tmp/ict-engine-trendexpansion-bocpd-30m-density-lift-accepted-feedback-readback-20260601T010000+0800`
- IBKR readback: `/tmp/ict-engine-trendexpansion-bocpd-30m-density-lift-accepted-feedback-readback-20260601T010000+0800/checks/ibkr_execution_readback_nq.json`
- Accepted feedback JSONL: `/tmp/ict-engine-trendexpansion-bocpd-30m-density-lift-accepted-feedback-readback-20260601T010000+0800/feedback/accepted_paper_execution_feedback.jsonl`
- Accepted feedback summary: `/tmp/ict-engine-trendexpansion-bocpd-30m-density-lift-accepted-feedback-readback-20260601T010000+0800/summaries/accepted_feedback_summary.json`

The same-turn read-only IBKR `reqExecutions` audit selected paper port `4002` but
returned `execution_rows_total=0`. Accepted-feedback conversion therefore had
`accepted_feedback_rows=0`, `broker_fill_evidence_rows=0`,
`broker_realized_rows=0`, and `terminal_decision=accepted_execution_feedback_missing`.

The guarded practical lifecycle root was:

- Lifecycle root: `/tmp/ict-engine-trendexpansion-bocpd-30m-density-lift-practical-lifecycle-20260601T010316+0800`
- Terminal metrics: `/tmp/ict-engine-trendexpansion-bocpd-30m-density-lift-practical-lifecycle-20260601T010316+0800/checks/terminal_metrics.json`

The lifecycle wrapper now fails on missing accepted feedback before running the
launch collision guard, so its own `--strategy-library` path cannot be
misclassified as a live factor process. It ended
`status=accepted_execution_feedback_missing`, `provider_or_downstream_launched=false`,
`same_tree_practical_closure=null`, `promotion_allowed=false`, and
`trade_usable=false`.

## 2026-06-01 Fast-Breakout Variant Prep

The sibling repair candidate `bidir_density_lift_fast_breakout` is now wired
through the same no-launch downstream and guarded lifecycle wrappers.

- Repo doc:
  `support/docs/experiments/actionable-regime-confidence/20260601T033639+0800-codex-trendexpansion-bocpd-30m-density-lift-fast-breakout-downstream-prep.md`
- Downstream prep root:
  `/tmp/ict-engine-trendexpansion-bocpd-30m-density-lift-fast-breakout-downstream-prep-20260601T033639+0800`
- Downstream terminal metrics:
  `/tmp/ict-engine-trendexpansion-bocpd-30m-density-lift-fast-breakout-downstream-prep-20260601T033639+0800/checks/terminal_metrics.json`
- Practical lifecycle root:
  `/tmp/ict-engine-trendexpansion-bocpd-30m-density-lift-fast-breakout-practical-lifecycle-20260601T033639+0800`
- Practical lifecycle terminal metrics:
  `/tmp/ict-engine-trendexpansion-bocpd-30m-density-lift-fast-breakout-practical-lifecycle-20260601T033639+0800/checks/terminal_metrics.json`

Current readback: `aq_trade_count=655`, NQ IBKR-fee net pct `+36.341604`,
net PF `1.193007`, retained-session coverage `pass`,
`non_rth_row_count=42521`, and exact branch root `TrendExpansion -> ... ->
tomac_nq_trendexpansion_bocpd_30m_split_repair_bidir_density_lift_fast_breakout_v1`.
The downstream prep remains `simulated_feedback_downstream_prep_fail_closed`;
the practical lifecycle remains `accepted_execution_feedback_missing` with
`accepted_feedback_rows=0`, `provider_or_downstream_launched=false`,
`same_tree_practical_closure=null`, `promotion_allowed=false`, and
`trade_usable=false`.

Implementation note: the downstream prep helper now supports
`--variant bidir_density_lift_fast_breakout`. A same-slice bug fix moved
variant-sensitive defaults out of Python default arguments; otherwise the fast
variant could silently reuse the parent `bidir_density_lift` class/slug/source
export and report `645` rows instead of the correct `655`. Focused tests:

```bash
python3 -m unittest support.docs.experiments.actionable-regime-confidence.scripts.test_tomac_trendexpansion_bocpd_30m_density_lift_downstream_prep_v1 -v
python3 -m unittest support.docs.experiments.actionable-regime-confidence.scripts.test_tomac_trendexpansion_bocpd_30m_density_lift_practical_lifecycle_v1 -v
```
