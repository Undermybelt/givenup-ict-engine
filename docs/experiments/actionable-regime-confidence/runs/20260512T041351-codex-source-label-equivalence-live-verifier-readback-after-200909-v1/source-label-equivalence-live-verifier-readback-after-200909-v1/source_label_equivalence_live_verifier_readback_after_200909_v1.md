# Source-Label Equivalence Live Verifier Readback After 200909 v1

Run id: `20260512T041351-codex-source-label-equivalence-live-verifier-readback-after-200909-v1`

Gate result: `source_label_equivalence_live_verifier_readback_after_200909_v1=schema_ready_unscored_no_confidence_acceptance_no_promotion`

## Source

- Source command root: `docs/experiments/actionable-regime-confidence/runs/20260512T200909-codex-source-label-equivalence-live-verifier-v1`
- Verifier stdout: `docs/experiments/actionable-regime-confidence/runs/20260512T200909-codex-source-label-equivalence-live-verifier-v1/command-output/source_label_equivalence_verifier.stdout.txt`
- Verifier exit: `0`
- Rows SHA256: `337a2b26fb5c82a27be3548404532e2577017cbb7c26e46683628cafeaed0f25`
- Provenance SHA256: `a373b77b4a34041f15004faaccc3f1d629c9c05b946894db0ae741186853a56b`

## Readback

- Status: `schema_ready_unscored`.
- Row count: `248440`.
- Package count: `price_root_equivalence_us_index_futures=248440`.
- Source-label root files exist under `/tmp/ict-engine-source-label-equivalence-intake`.
- Provenance date range: `2000-01-03` through `2026-03-20`.
- Regime label counts: `Bull=104979`, `Sideways=57899`, `Bear=54939`, `Crisis=30623`.
- Market families: `us_single_stock=218769`, `us_index=26236`, `india_equity_index=3435`.
- Split counts: `calibration=148976`, `heldout_market=26236`, `heldout_time=45384`, `test=27844`.

## Existing Calibration Boundary

Existing calibration artifacts already classify this source-label family as no-acceptance:

- `docs/experiments/actionable-regime-confidence/runs/20260512T011056-codex-source-label-equivalence-calibration-after-root-poll-v1/source-label-equivalence-confidence-calibration/source_label_equivalence_confidence_calibration_v1.json`
- `docs/experiments/actionable-regime-confidence/runs/20260512T011954-codex-source-label-equivalence-arrival-calibration-v1/source-label-equivalence-arrival-calibration/source_label_equivalence_arrival_calibration_v1.json`

Both preserve `source_confidence_scored_no_acceptance`; schema readiness is not a confidence gate by itself. The verifier output itself says to rerun unchanged chronological and heldout-market/timeframe gates and not treat schema readiness as confidence acceptance.

## Decision

This is useful source-label schema evidence only. It does not close the active R6 owner/export root, R3 native-subhour root, or R5 source-panel recency-extension root. It does not create accepted `>=95%` regime-confidence evidence, canonical merge input, downstream promotion evidence, or trade evidence.

Promotion status remains unchanged: accepted rows added `0`, new confidence gate false, canonical merge false, downstream promotion rerun false, strict full objective false, trade usable false, and `update_goal=false`.
