# Mendeley Crypto Wash ML Sample Audit

Run ID: `20260511T100010+0800-codex-mendeley-crypto-wash-ml-sample-audit`

Source: `https://data.mendeley.com/datasets/4hyxfwzpgg/3`
GitHub: `https://github.com/niuniu-zhang/nft_wash_trading`
Related paper: `https://ssrn.com/abstract=4649565`

## Result

- Dataset: `Detecting Crypto Wash Trades via Machine Learning`.
- DOI: `10.17632/4hyxfwzpgg.3`.
- Published: `2026-04-23T20:46:40.054Z`.
- Licence: `CC BY 4.0`.
- Files inspected: `4`.
- Total listed CSV size bytes: `3497730752`.
- Files with label-like fields: `4`.
- Files with event timestamp fields: `0`.
- Files with row asset/instrument fields: `0`.
- Files with row venue/chain fields: `0`.
- Candidate is useful provenance because the source documents labeled ML samples from on-chain transactions.
- Candidate is not accepted as direct Manipulation rows because the released ML sample rows lack the Board A direct-row schema fields.
- Accepted parent-root slots added: `0`.
- Accepted direct Manipulation rows/windows added: `0`.

## File Header Audit

| File | Size Bytes | Label-Like Fields | Timestamp Field | Asset Field | Venue/Chain Field |
|---|---:|---|---|---|---|
| `Blur_ml_samples.csv` | 346004976 | `filter_1234` | `False` | `False` | `False` |
| `gox_ml_samples.csv` | 986063630 | `wash` | `False` | `False` | `False` |
| `LooksRare_ml_samples.csv` | 38651230 | `filter_1234` | `False` | `False` | `False` |
| `OpenSea_ml_samples.csv` | 2127010916 | `filter_1234` | `False` | `False` | `False` |

## Gate

`blocked_mendeley_crypto_wash_ml_samples_missing_required_direct_row_schema`

Runtime code changed: false. Thresholds relaxed: false. Raw data committed: false. Trade usable: false.
