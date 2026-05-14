# HF TSIE Source Label Mapping Audit

Run id: `20260511T074300+0800-codex-hf-tsie-source-label-mapping-audit`

Goal achieved: `false`

## Source

- Dataset: `sujinwo/tsie-market-regime-dataset`
- Last modified: `2026-04-13T13:27:46.000Z`
- Train examples: `7193996`
- Full parquet downloaded: `false`
- Sample rows inspected: `10`
- Sample `regime_label` values: `1, 2, 3`

## Mapping Disposition

| TSIE Label | MainRegimeV2 Candidate | Status |
|---|---|---|
| `STRONG SELL / WEAK SELL` | `Bear` | `candidate_only_not_accepted` |
| `FLAT / NOISE` | `Sideways` | `candidate_only_not_accepted` |
| `WEAK BUY / STRONG BUY` | `Bull` | `candidate_only_not_accepted` |
| `BEAR TRAP / BULL TRAP` | `UnknownOrMixed or child/provenance` | `candidate_only_not_accepted` |
| `none` | `Crisis` | `missing` |
| `none` | `Manipulation` | `missing` |

## Decision

- This is not accepted as a MainRegimeV2 source-label panel.
- Labels are rule-based IDX signal classes, not independent labels attached to the yfinance/Kraken full matrix.
- `Crisis` and direct `Manipulation` labels are missing from the inspected source.
- Runtime code changed: false. Thresholds relaxed: false. Raw dataset committed: false. Trade usable: false.

Gate result: `blocked_hf_tsie_not_attachable_as_mainregimev2_source_label_panel`
