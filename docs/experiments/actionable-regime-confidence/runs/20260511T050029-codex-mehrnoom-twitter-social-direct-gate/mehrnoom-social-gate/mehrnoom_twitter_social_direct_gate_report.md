# Mehrnoom Twitter Social Direct Manipulation Gate

Run: `20260511T050029+0800-codex-mehrnoom-twitter-social-direct-gate`

Source: sparse checkout of `Mehrnoom/Cryptocurrency-Pump-Dump`; raw sparse data stayed under `/private/tmp/ict-regime-mehrnoom-pumpdump-sparse` and was not committed.

Target: direct-input-gated `Manipulation` from classified Telegram pump attempts for `BTC` and `ADA`, with same-coin Twitter non-event timestamp controls outside +/-6h of classified attempts.

Panel rows: `35844`; positives `8961`; negatives `26883`.

Best rule:
- Rule: `sentiment_mean_24h le 0.16547428315412963`.
- Calibration Wilson95 / support / coverage: `0.937652` / `1497` / `0.208816`.
- Test Wilson95 / support / coverage: `0.815594` / `794` / `0.110755`.

Gate result: `blocked_mehrnoom_twitter_social_below_95`. Accepted 95: `false`. Runtime code changed: false. Thresholds relaxed: false. Trade usable: false.

