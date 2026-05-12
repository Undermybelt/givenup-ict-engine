# Missing Root Source Readiness Preflight

Run ID: `20260511T041508+0800-codex-missing-root-source-readiness`

Objective: find materially different evidence sources for the missing active MainRegimeV2 roots without repeating the Kaggle OHLCV/macro threshold loop.

## Active Roots Audited

| Root | Current State Before Slice | This Slice Result |
|---|---|---|
| `Bear` | missing 95 packet | no accepted packet; source-backed causal HMM/rolling-regime path is the next runnable gate |
| `Sideways` | missing 95 packet | no accepted packet; same causal HMM/rolling-regime path is the next runnable gate |
| `Manipulation` | missing_required_inputs | no accepted packet; direct L4/order-lifecycle source metadata is available, but labels and bounded raw extraction are still missing |

Accepted roots added by this slice: none.

Runtime code changed: false.
Thresholds relaxed: false.
Fresh calibration rerun: false.
Raw large provider data committed: false.

## Source Readiness

### Bear / Sideways

Useful source-backed method path:

- Hidden-regime style HMM regime modeling, including confidence/persistence outputs: `https://github.com/hidden-regime/hidden-regime`
- Recent regime-aware forecasting literature using causal rolling HMM/purged splits for bull/bear/sideways framing: `https://www.mdpi.com/1911-8074/18/11/613`
- Bitcoin / crypto HMM regime framing with three broad states including sideways/bear/bull: `https://link.springer.com/chapter/10.1007/978-981-97-9474-5_21`

Decision:

- These are candidate methods, not accepted evidence by themselves.
- The next valid packet must run a local chronological gate that emits active parent labels `Bear` and `Sideways`, not expanded child labels.
- The gate must report support, coverage, calibration/test Wilson95 LCB, ECE where applicable, instruments, timeframes, and abstain conditions.

### Manipulation

Direct input source path found:

- Hyperliquid L4/order-flow dataset: `https://zenodo.org/records/18184441`
- Metadata files downloaded only to `/private/tmp/ict-regime-missing-root-source-readiness/`:
  - `hyperliquid_README.md`
  - `hyperliquid_SCHEMA.md`
  - `hyperliquid_read_data.py`

Readiness facts from metadata:

- Order statuses include BTC/ETH/SOL accepted and rejected order lifecycle events for December 2025.
- Raw book diffs include visible book changes with user/order identifiers, order IDs, side, price, and size changes.
- The schema exposes order lifecycle fields including `ts`, `userId`, `statusId`, `isAsk`, `limitPx`, `sz`, `oid`, `timestampDiff`, `orderTypeId`, and `tifId`.
- The book-diff schema links visible book changes to order status data by `oid`.

Blocker:

- The source is direct order-lifecycle/L4 evidence, but it is not labeled for manipulation positives/negatives.
- The raw archives are large, so a blind download is not acceptable for this loop.
- This cannot complete `Manipulation` until a bounded sampler plus explicit event labeling strategy exists.

## Gate Decision

`blocked_source_readiness_only_no_new_95`.

This slice improves the next data path but does not satisfy any missing root. Active Board A accounting remains:

- accepted_95: `Bull`, `Crisis`
- missing: `Bear`, `Sideways`
- missing_required_inputs: `Manipulation`

## Next Action

Run one bounded source-backed causal HMM parent-root gate for `Bear` and `Sideways` first; keep `Manipulation` fail-closed until direct event/order-lifecycle labels can be paired with the Hyperliquid/L4-style source.
