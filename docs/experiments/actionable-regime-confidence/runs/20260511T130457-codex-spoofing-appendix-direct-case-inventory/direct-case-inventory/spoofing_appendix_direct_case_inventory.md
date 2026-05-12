# Spoofing Appendix Direct Case Inventory

Run ID: `20260511T130457+0800-codex-spoofing-appendix-direct-case-inventory`

## Result

- Parsed positive direct spoofing case rows: `204`.
- By regulator: `{'CFTC': 62, 'CME Group': 115, 'ICE': 27}`.
- Variety tags: `{'algorithmic': 4, 'flash_spoofing': 2, 'flipping': 6, 'iceberg_context': 5, 'layering': 116, 'manual': 32, 'single_spoof_order': 78, 'spoofing_case_unspecified_pattern': 50, 'spread_squeezing': 4}`.
- Accepted 95 direct gate added: `0`.
- Full objective achieved: `false`.

## Boundary

- This is direct regulator/enforcement case evidence for `Manipulation`, not an OHLCV proxy.
- It is positive-only and case-level. There are no matched negative order-lifecycle rows, so no Wilson95 calibration gate is claimed.
- Raw `.xlsx` remains under `/private/tmp`; only compact CSV/JSON/MD artifacts are committed under the run directory.

## Sources

- Zenodo record: `https://zenodo.org/records/16629490`
- Downloaded file: `https://zenodo.org/records/16629490/files/Online%20Appendix%20C.xlsx?download=1`

## Next

Acquire matched negative order-lifecycle/order-book rows for spoofing/layering/quote-stuffing before any direct `Manipulation` 95 gate claim.
