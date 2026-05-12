# Kaggle NFT Wash Direct Manipulation Gate

Run: `20260511T044214+0800-codex-kaggle-nft-wash-direct-gate`

Source: Kaggle public dataset `nikih94uni/ethereum-nfts-flagged-for-suspected-wash-trading`. Raw ZIP and extracted CSVs stayed under `/private/tmp/ict-regime-kaggle-nft-wash`; raw data was not committed.

Target: `Manipulation` as direct on-chain wash-trading evidence. Positive rows are tokens with `flagged_trades > 0`; negative rows are tokens with `flagged_trades == 0`.

Predictor policy:
- Used direct ownership/order-lifecycle features only: transfer counts, paid-trade counts, address reuse, reverse edges, repeated pairs, token lifetime, and account activity aggregates.
- Blocked `flagged_trades`, `target`, `token_id`, collection identifiers, `future_*`, `target_*`, `*_next`, and `next_*` predictors.

Panel:
- Rows: `145098` tokens.
- Positives: `28219`.
- Contexts: `11` NFT collections.
- Chronological split by token last observed ownership-trace timestamp: train `87058`, calibration `29020`, test `29020`.

Best high-precision candidate:
- Rule: `p_model(ManipulationOnchainWash) >= 0.957925`.
- Calibration Wilson95 / precision / support / coverage / contexts: `0.944055` / `0.971119` / `277` / `0.009545` / `10`.
- Test Wilson95 / precision / support / coverage / contexts: `0.940528` / `0.961864` / `472` / `0.016265` / `10`.
- Blocked by calibration/test Wilson95 below `0.95` and coverage below `0.03`.

Best coverage-eligible candidate:
- Rule: `p_model(ManipulationOnchainWash) >= 0.837883`.
- Calibration Wilson95 / precision / support / coverage / contexts: `0.876851` / `0.897959` / `931` / `0.032081` / `10`.
- Test Wilson95 / precision / support / coverage / contexts: `0.863879` / `0.881616` / `1436` / `0.049483` / `11`.
- Blocked by calibration/test Wilson95 below `0.95`.

Gate result: `blocked_kaggle_nft_wash_direct_gate_below_95_and_coverage`.

Accepted 95: false. Thresholds relaxed: false. Runtime code changed: false. Fresh calibration rerun: true. Trade usable: false.

Next action: do not repeat this Kaggle NFT wash structural-feature path as an acceptance attempt; acquire stronger direct event/order-lifecycle/L2/L3/MBO/social/on-chain positives and negatives with enough support to satisfy both Wilson95 >= `0.95` and coverage >= `0.03`.
