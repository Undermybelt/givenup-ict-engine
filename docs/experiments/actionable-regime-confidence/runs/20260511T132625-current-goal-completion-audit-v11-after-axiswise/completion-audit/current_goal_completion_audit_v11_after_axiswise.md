# Current Goal Completion Audit v11 After Axiswise

Run ID: `20260511T132625+0800-current-goal-completion-audit-v11-after-axiswise`

## Result

- Goal achieved: `false`.
- Same-source `1w/1mo` price-root cells: `8/8` accepted at 95 by axiswise validation.
- Daily parent-root stock/index cells: `4/4` accepted at 95.
- Scoped cross-context price-root floor: `pass`.
- Expanded full-cycle/full-species objective: `blocked`.
- Direct `Manipulation` full variety coverage: `false`.
- `update_goal`: `false`.

## Prompt-To-Artifact Checklist

| Requirement | Status | Evidence | Notes |
|---|---|---|---|
| Every active MainRegimeV2 price root has a 95% parent-root gate. | `pass` | `docs/experiments/actionable-regime-confidence/runs/20260511T125122-codex-stock-market-regimes-parent-root-abstain/parent-root-abstain/stock_market_regimes_parent_root_abstain.json` | Daily stock/index source-label panel accepts Bull/Bear/Sideways/Crisis. |
| Weekly and monthly same-source timeframe cells pass for every price root. | `pass` | `docs/experiments/actionable-regime-confidence/runs/20260511T131922-codex-source-consensus-axiswise-timeframe-gate-v1/source-consensus-axiswise/source_consensus_axiswise_timeframe_gate_v1.json` | Axiswise validation accepts 1w and 1mo cells for all four roots. |
| Other-market and other-timeframe evidence exists for all price roots. | `partial` | `docs/experiments/actionable-regime-confidence/runs/20260511T130102-current-goal-completion-audit-v10-cross-context/completion-audit/current_goal_completion_audit_v10_cross_context.json` | Scoped cross-context floor passes, but the expanded full-universe/full-cycle matrix is still incomplete. |
| Full-cycle/full-species coverage is accepted, not merely scoped. | `fail` | `docs/experiments/actionable-regime-confidence/runs/20260511T081715-codex-source-label-acquisition-package-v2/acquisition-package/source_label_acquisition_package_v2.json` | Unsupported intraday/full-species native source-label cells remain open; the older 612-slot package is stale for monthly counts but still proves label-coverage incompleteness. |
| Manipulation has complete direct-event/order-flow/order-lifecycle variety coverage with positive and matched negative controls. | `fail` | `docs/experiments/actionable-regime-confidence/runs/20260511T131311-codex-direct-manipulation-variety-matrix-v1/direct-manipulation/direct_manipulation_variety_matrix_v1.json` | Scoped pump/dump, DEX self-trade, and on-chain wash-maker slices pass; spoofing/layering matched negatives, quote stuffing, pinging, bear raid, and painting-the-tape remain open. |
| No child/sub-regime or OHLCV-only proxy is promoted to complete a parent root or Manipulation. | `pass` | `docs/plans/2026-05-10-actionable-regime-confidence-todo.md` | Current board keeps MainRegimeV2 roots active and records Manipulation as separate direct evidence. |

## Accepted Price-Root Coverage

| Layer | Coverage | Evidence |
|---|---:|---|
| Daily same-source parent roots | `4/4` | `docs/experiments/actionable-regime-confidence/runs/20260511T125122-codex-stock-market-regimes-parent-root-abstain/parent-root-abstain/stock_market_regimes_parent_root_abstain.json` |
| Weekly/monthly same-source axiswise roots | `8/8` | `docs/experiments/actionable-regime-confidence/runs/20260511T131922-codex-source-consensus-axiswise-timeframe-gate-v1/source-consensus-axiswise/source_consensus_axiswise_timeframe_gate_v1.json` |
| Scoped cross-market/timeframe floor | `pass` | `docs/experiments/actionable-regime-confidence/runs/20260511T130102-current-goal-completion-audit-v10-cross-context/completion-audit/current_goal_completion_audit_v10_cross_context.json` |

## Remaining Blockers

- Unsupported intraday/full-species native source-label cells remain open.
- The older 612-slot acquisition package is stale for monthly counts after the axiswise gate, but it still proves unresolved intraday/provider/full-species label requirements.
- Direct `Manipulation` is still missing spoofing/layering matched negatives, quote-stuffing rows, pinging rows, bear-raid rows, and painting-the-tape rows.
- No OHLCV/session/liquidity/sweep proxy can close direct `Manipulation`.

## Targeted Next Cells

CSV: `docs/experiments/actionable-regime-confidence/runs/20260511T132625-current-goal-completion-audit-v11-after-axiswise/completion-audit/targeted_unsupported_cell_targets_v11.csv`

| Lane | Target Scope | Blocker | Required Evidence |
|---|---|---|---|
| `price_root_source_labels` | native intraday MainRegimeV2 labels for index ETF/futures and liquid crypto/futures contexts | no accepted native intraday source-label panel covering all four price roots | independent timestamped parent-root labels, chronological calibration/test split, heldout instrument/context validation |
| `price_root_source_labels` | full-species MainRegimeV2 labels outside the same-source US stock/index panel | old acquisition request still shows non-yfinance, instrument, and provider/source-label gaps | exact-underlying or native source labels for crypto, futures, commodity, ETF, and single-stock contexts |
| `direct_manipulation` | spoofing/layering and quote-stuffing order-book/order-lifecycle controls | positive-only inventory cannot produce a Wilson95 positive/negative direct gate | matched negative normal-period rows from same venue/instrument/message schema |
| `direct_manipulation` | missing direct varieties | missing positive and negative rows | direct event/order-flow rows plus same-source non-event controls |

## Decision

- Gate result: `post_axiswise_same_source_timeframes_pass_full_matrix_and_direct_manipulation_still_blocked`.
- Runtime code changed: `false`.
- Thresholds relaxed: `false`.
- Raw data committed: `false`.
- Trade usable: `false`.
