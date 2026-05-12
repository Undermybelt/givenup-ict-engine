# QQQ/NQ Daily Cross-Market Attachment v1

Run ID: `20260511T170714+0800-codex-qqq-nq-daily-crossmarket-attachment-v1`

## Decision

- Accepted daily source-label attachment from `^IXIC` to `QQQ` and `NQ=F`.
- This validates cross-market tracking for Nasdaq ETF/futures daily parent-root context; it does not generate target-side regime labels.
- `Bull`, `Bear`, `Sideways`, and `Crisis` are all present on both target markets in the target-available source interval.
- Full objective achieved: `false`; `update_goal=false`.

## Target Metrics

| Target | Role | First date | Last date | Interval coverage | Min root support | Min split corr | Accepted |
|---|---|---|---|---:|---:|---:|---|
| QQQ | nasdaq_100_etf_crossmarket | 2000-01-03 | 2026-01-30 | 1.000000 | 462 | 0.954401 | true |
| NQ=F | nasdaq_100_futures_crossmarket | 2000-09-18 | 2026-01-30 | 0.999687 | 382 | 0.953384 | true |

## Guardrails

- Same-source `MainRegimeV2` labels come from `^IXIC`; target prices are used only to validate tracking/attachment.
- No child/sub-regime labels are promoted.
- No raw yfinance rows are committed.
- Native sub-hour, crypto/FX source labels, and full direct `Manipulation` species coverage remain open.

## Artifacts

- JSON: `docs/experiments/actionable-regime-confidence/runs/20260511T170714-codex-qqq-nq-daily-crossmarket-attachment-v1/crossmarket-attachment/qqq_nq_daily_crossmarket_attachment_v1.json`
- Target metrics CSV: `docs/experiments/actionable-regime-confidence/runs/20260511T170714-codex-qqq-nq-daily-crossmarket-attachment-v1/crossmarket-attachment/qqq_nq_daily_crossmarket_attachment_v1_targets.csv`
- Split metrics CSV: `docs/experiments/actionable-regime-confidence/runs/20260511T170714-codex-qqq-nq-daily-crossmarket-attachment-v1/crossmarket-attachment/qqq_nq_daily_crossmarket_attachment_v1_splits.csv`
- Root support CSV: `docs/experiments/actionable-regime-confidence/runs/20260511T170714-codex-qqq-nq-daily-crossmarket-attachment-v1/crossmarket-attachment/qqq_nq_daily_crossmarket_attachment_v1_root_support.csv`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260511T170714-codex-qqq-nq-daily-crossmarket-attachment-v1/checks/qqq_nq_daily_crossmarket_attachment_v1_assertions.out`
