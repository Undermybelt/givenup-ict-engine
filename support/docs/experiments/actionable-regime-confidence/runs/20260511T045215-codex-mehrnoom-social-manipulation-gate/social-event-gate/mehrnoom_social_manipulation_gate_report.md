# Mehrnoom Social Manipulation Gate

Run id: `20260511T045215+0800-codex-mehrnoom-social-manipulation-gate`

## Source

- Repository: `https://github.com/Mehrnoom/Cryptocurrency-Pump-Dump`
- Paper: `https://arxiv.org/abs/1902.03110`
- Commit inspected: `86e86b966806b3bf7a3f580f0d0427ab9195f5a5`
- Raw LFS cache: `/private/tmp/ict-regime-mehrnoom-pump-dump-lfs-cache`
- Raw data committed to repo: false.
- Runtime code changed: false.
- Thresholds relaxed: false.

## Dataset

- Selected channels: 80 bounded by 250 MiB / 80 channels.
- Downloaded raw message bytes: 262141102.
- Raw message rows: 241954.
- Positive pump-attempt message rows: 40565.
- Unclassified channel-message controls: 201389.
- Chronological range: 2017-06-15 12:36:32+00:00 to 2018-07-23 16:54:27+00:00.

## Gate

- Rule: `nb_score >= 9.11666`.
- Calibration Wilson95 / precision / support / coverage / ECE: `0.901875` / `0.909755` / `5474` / `0.090497` / `0.000000`.
- Test Wilson95 / precision / support / coverage / ECE: `0.881516` / `0.892492` / `3330` / `0.055051` / `0.017263`.
- Gate result: `blocked_mehrnoom_social_gate_below_95_coverage_or_ece`. Accepted 95 `Manipulation`: false. Trade usable: false.

## Notes

- Predictor policy: raw source label, channel id, message id, target coin, and timestamp identity were not used as predictors.
- Candidate rules used raw Telegram message text features only; selection was train-only, with chronological calibration/test holdout.
- `Manipulation` remains a direct-input-gated root or overlay. This packet does not change `Bull`, `Bear`, `Sideways`, or `Crisis` accounting.

Next: Acquire stronger direct event/order-lifecycle/L2/L3/MBO/social/on-chain Manipulation positives and negatives or broaden this source with additional explicit controls, then rerun the unchanged gate.
