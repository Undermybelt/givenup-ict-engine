# Source Taxonomy Strategy Reset v1

Run ID: `20260511T140304+0800-codex-source-taxonomy-strategy-reset-v1`

Cursor seen before final board write: `20260511T140042+0800-codex-positive-regime-factor-index-v1`.

This is a direction correction, not another broad negative sweep. The recent crosswalk work did extract useful positives: SPY/DIA Bull/Bear/Sideways and ES Bull 15m/1h. The mistake would be to keep re-running the remaining no-source or weak-crosswalk cells until the ledger fills with negatives.

## Decision

- Split Board A into three lanes:
  - parent action taxonomy: `BullExpansion`, `BearExpansion`, `ConsolidationBalance`, `CrisisDislocation`, and direct `ManipulationIntegrityEvent`;
  - source-label attachment/crosswalk: exact source labels first, then documented or owner-approved index/ETF/futures crosswalks;
  - direct manipulation: timestamped event/order-flow/order-lifecycle/social/on-chain positives with matched negatives.
- Treat existing `MainRegimeV2` labels as compatibility seed labels. They remain useful, but they should not force all future work into flat `Bull/Bear/Sideways/Crisis` availability bookkeeping.
- Stop promoting raw bars, HMM state IDs, change-point breaks, jump-model states, or OHLCV manipulation proxies as parent labels.
- Stop broad rescans of the same open matrix. After `140042`, `135908`, and `135932`, the next useful action is source relation acquisition, not another crosswalk calibration.

## Preserved Positives

- `140042` indexed the positive supply map instead of another negative source scan.
- `135908` accepted `36` SPY/DIA crosswalk source-attachment rows for `Bull/Bear/Sideways`.
- `135932` accepted `2` ES=F Bull source-label crosswalk rows at `15m` and `1h`.
- These do not complete the full objective, but they are not "nothing"; they should be kept and routed as scoped parent-day context evidence.

## Next Positive Slice

Acquire or document a Nasdaq-100-grade source-label relation before any more NQ/QQQ work:

- acceptable: source panel labels for `^NDX`, an authoritative QQQ/NQ label panel, or explicit owner-approved `^IXIC -> NQ/QQQ` relation with unchanged tracking and support gates;
- unacceptable: using NQ/QQQ provider bars, HMM states, future returns, or generated labels as labels;
- if no relation is obtained, NQ/QQQ remain abstained and the next evidence work should move to crisis support or direct manipulation rows.

## Guardrails

- `ManipulationIntegrityEvent` remains direct evidence only. Already accepted scoped direct slices stay useful, but spoofing/layering, quote stuffing, pinging, bear raid, and painting-the-tape remain open until row-level positives and matched negatives exist.
- `jump-models`, `ruptures`, HMMs, and directional-change features are useful features or boundary evidence. They are not independent label sources.
- This run adds no confidence gate and does not mark the full objective complete.

Gate result: `source_taxonomy_strategy_reset_no_new_confidence_gate_stop_broad_negative_sweeps`.
