# Stock Regime Source-Panel Owner Request Template v1

Dataset target: `mafaqbhatti/stock-market-regimes-20002026`.
Dataset URL: `https://www.kaggle.com/datasets/mafaqbhatti/stock-market-regimes-20002026`.

Request:

Please provide a source-owned or owner-approved row package for the strict Board A target cells below:

| Symbol | MainRegimeV2 label | Split role | Minimum new source sessions |
|---|---|---|---:|
| `XOM` | `Sideways` | `heldout_time` | `5` |
| `UNH` | `Bear` | `calibration` | `7` |
| `^DJI` | `Sideways` | `calibration` | `7` |
| `AMD` | `Bear` | `calibration` | `10` |

Required files:

- `source_label_equivalence_rows.csv`
- `source_label_equivalence_provenance.json`

Required row fields:

package_id, source_owner, source_report_or_dataset, source_pull_date, market_family, symbol, source_symbol, equivalence_policy, event_species, timestamp_or_date, timeframe, main_regime_v2_label, direct_label, matched_negative_group_id, split_role, source_row_id, provenance_hash

The package will be checked locally with:

`python3 docs/experiments/actionable-regime-confidence/runs/20260511T182922-codex-source-label-equivalence-intake-verifier-v1/equivalence-intake-verifier/source_label_equivalence_intake_verifier_v1.py --intake-root /tmp/ict-engine-source-label-equivalence-intake`

Rows cannot be accepted if they are generated/model labels, future-return labels, provider OHLCV-only rows, forward-filled source labels, or duplicates of already-counted source-panel rows.
