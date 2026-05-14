# Bayi-Hu Market Feature Manipulation Gate

Run id: `20260511T023416+0800-codex-bayi-hu-market-feature-gate`

## Source

- Source: Bayi-Hu generated target-coin prediction archives from Google Drive links in the source README.
- Archive directory: `/private/tmp/ict-regime-bayi-gdrive`.
- Raw archives committed to repo: false; temp raw archives removed after hashing and compact report generation.
- Predictor rule: pre-event generated features only; identifiers, timestamps, labels, future/target/next fields blocked.
- Search shape: deterministic bounded train sample chooses candidate thresholds; full train/calibration/test archives score those candidates.

## Dataset

- Train partition rows: 99,230; positives: 612; negatives: 98,618.
- Calibration partition rows: 33,084; positives: 136; negatives: 32,948.
- Test rows: 64,299; positives: 200; negatives: 64,099.
- Candidate rules evaluated on full archives: 160.

## Best Full-Archive Rule

- Rule: `pre_6h_return >= 2.688568469663907`.
- Train Wilson95 LCB: 0.010716, support=993, precision=0.017120.
- Calibration Wilson95 LCB: 0.023196, support=1,271, precision=0.031471.
- Test Wilson95 LCB: 0.051905, support=803, precision=0.067248.

## Decision

- Accepted 95 `Manipulation` root: false.
- Gate: `blocked_bayi_hu_market_feature_gate_below_95`.
- Blocker: Best bounded-train-selected pre-event market-feature rule failed the unchanged held-out 95% Wilson/support/coverage gate.
- Thresholds relaxed: false.
- Runtime code changed: false.
- Trade usable: false.

Next: Use a second labeled direct manipulation context with explicit positives/negatives and timestamps; Bayi-Hu generated market features alone do not close Manipulation.
