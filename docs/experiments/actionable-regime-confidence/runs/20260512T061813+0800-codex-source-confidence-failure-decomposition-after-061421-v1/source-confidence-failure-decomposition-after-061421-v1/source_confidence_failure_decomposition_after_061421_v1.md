# Source Confidence Failure Decomposition After 061421 v1

- Run id: `20260512T061813+0800-codex-source-confidence-failure-decomposition-after-061421-v1`
- Decision: `source_confidence_failure_decomposition_after_061421_v1=all_regimes_blocked_by_confidence_distribution_required_roots_absent_no_promotion`
- Source run: `docs/experiments/actionable-regime-confidence/runs/20260512T061421+0800-codex-source-label-equivalence-current-calibration-after-061229-v1/source-label-equivalence-current-calibration-after-061229-v1`
- Intake has source confidence column: `False`
- Accepted labels: `0/4`
- Required roots unlocked: `False`
- Canonical merge allowed now: `false`
- Downstream rerun allowed now: `false`
- Trade usable: `false`
- `update_goal=false`

## Label Failure Summary

| Label | Worst split | Worst Wilson95 LCB | Best required split | Best required LCB | Best market | Best market LCB | Extra high-confidence rows needed |
|---|---|---:|---|---:|---|---:|---:|
| `Bear` | `heldout_time` | `0.0` | `calibration` | `0.0011242749` | `us_single_stock` | `0.0007369389` | `52328` |
| `Bull` | `heldout_market` | `0.0581218497` | `heldout_time` | `0.119416014` | `india_equity_index` | `0.663432665` | `89800` |
| `Crisis` | `heldout_market` | `0.0` | `test` | `0.0173592424` | `india_equity_index` | `0.2514935801` | `28948` |
| `Sideways` | `test` | `0.1075825871` | `heldout_market` | `0.2056385432` | `india_equity_index` | `0.2425074687` | `46512` |

## Readback

- All four active labels remain blocked by the required Wilson95 lower-bound gate across calibration, heldout-market, heldout-time, and test splits.
- The closest visible market slice is still far below the `0.95` lower-bound threshold, so this is not a narrow threshold-margin failure.
- The intake root is schema-ready but has no embedded `source_confidence` column; the `061421` calibration joins source confidence from upstream source files and still fails.
- Required promotion roots remain absent, so this packet cannot unlock direct verifier, canonical merge, provider/AutoQuant, Pre-Bayes, BBN, CatBoost/path-ranking, or execution-tree promotion.

## Required Roots

| Root | Status | File count |
|---|---|---:|
| `/tmp/ict-engine-board-a-r6-owner-export-v1` | `missing` | `0` |
| `/tmp/ict-engine-native-subhour-source-label-intake` | `missing` | `0` |
| `/tmp/ict-engine-source-panel-recency-extension` | `missing` | `0` |

## Artifacts

- JSON: `docs/experiments/actionable-regime-confidence/runs/20260512T061813+0800-codex-source-confidence-failure-decomposition-after-061421-v1/source-confidence-failure-decomposition-after-061421-v1/source_confidence_failure_decomposition_after_061421_v1.json`
- Split deficits CSV: `docs/experiments/actionable-regime-confidence/runs/20260512T061813+0800-codex-source-confidence-failure-decomposition-after-061421-v1/source-confidence-failure-decomposition-after-061421-v1/source_confidence_failure_split_deficits_v1.csv`
- Label summary CSV: `docs/experiments/actionable-regime-confidence/runs/20260512T061813+0800-codex-source-confidence-failure-decomposition-after-061421-v1/source-confidence-failure-decomposition-after-061421-v1/source_confidence_failure_label_summary_v1.csv`
- Required roots CSV: `docs/experiments/actionable-regime-confidence/runs/20260512T061813+0800-codex-source-confidence-failure-decomposition-after-061421-v1/source-confidence-failure-decomposition-after-061421-v1/source_confidence_failure_required_roots_v1.csv`
