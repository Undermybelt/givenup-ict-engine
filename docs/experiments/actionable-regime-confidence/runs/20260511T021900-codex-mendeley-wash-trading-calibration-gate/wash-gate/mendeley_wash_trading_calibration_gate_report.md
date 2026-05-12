# Mendeley Wash Trading Calibration Gate

Run id: `20260511T021900+0800-codex-mendeley-wash-trading-calibration-gate`

## Gate

- Active axis: MainRegimeV2.
- Candidate regime: direct-input-gated `Manipulation`.
- Split: row-order train 50%, calibration 25%, test 25%; acceptance only allowed when source script proves global chronological output order.
- Rule shape: train-selected single-feature threshold, held-out calibration/test Wilson95 lower bounds.
- Runtime code changed: false.
- Thresholds relaxed: false.
- Raw CSV committed: false.

## Results

- gox_ml_samples.csv: rows=5537252, positives=1902646, rule=`price_deviation <= -0.2989376`, cal_lcb=0.670258, test_lcb=0.270040, accepted_95_context=False, blocker=calibration_or_test_wilson_below_95_or_support_below_50
- LooksRare_ml_samples.csv: rows=401125, positives=163195, rule=`sellerFee_amount >= 4.47174e+20`, cal_lcb=0.994971, test_lcb=0.994049, accepted_95_context=False, blocker=source_order_not_global_chronological_for_public_ml_sample

## Decision

Gate result: `raw_wash_labels_calibration_failed_or_blocked`.
Accepted 95 root: `False`.
Blocker: No Mendeley wash-trading file produced an accepted active-root packet under the unchanged chronological 95% gate.

Next: Recover or stream source raw rows with timestamps for NFT marketplace samples, or run a second direct/event manipulation source so Manipulation has cross-context chronological evidence; keep Bull/Bear/Sideways on non-OHLCV signed-direction/sideways inputs.
