# CFTC Complaint PDF Parse After 070315 v1

Run id: `20260512T070801+0800-codex-cftc-complaint-pdf-parse-after-070315-v1`

Gate result: `cftc_complaint_pdf_parse_after_070315_v1=official_complaint_parsed_no_r6_owner_export_controls_no_unlock`

## Scope

This packet closes the `070315` gap where the official CFTC Oystacher complaint PDF had been downloaded and hashed, but `pdftotext` and `pdfinfo` were unavailable. It parses the already downloaded PDF with a temporary `/tmp` UV cache and `pypdf`.

This run does not mutate `/tmp/ict-engine-board-a-r6-owner-export-v1`, `/tmp/ict-engine-source-panel-recency-extension`, or `/tmp/ict-engine-native-subhour-source-label-intake`; does not approve same-exhibit FLIP rows as controls; does not run direct verifier, split calibration, canonical merge, provider/AutoQuant promotion, filter / Pre-Bayes, BBN, CatBoost/path-ranking, or execution-tree promotion; does not make a trade claim; and does not call `update_goal`.

## Source

- PDF: `/tmp/ict-engine-board-a-public-exact-source-route-probe-after-065820-v1/enfigorcomplnt101915.pdf`
- SHA-256: `6a2a951e3c02285cb1df085e314c7ae2a2a0c089f283998641ea66fce5ce8591`
- Parser command shape: `UV_CACHE_DIR=/tmp/ict-engine-uv-cache-pdf uv run --no-project --with pypdf python ...`

## Parsed Facts

- Pages parsed: `36`.
- Extracted text characters: `59020`.
- Complaint route context: alleged spoofing across COMEX copper, NYMEX crude oil, NYMEX natural gas, CFE VIX, and CME E-mini S&P 500 futures.
- Parsed appendix/date support by product:
  - COMEX copper: `14` charged dates.
  - NYMEX crude oil: `4` charged dates.
  - NYMEX natural gas: `3` charged dates.
  - CFE VIX: `19` charged dates.
  - CME E-mini S&P 500: `11` charged dates.
  - Total charged dates represented: `51`.
- Term counts from extracted text:
  - `spoof`: `93`
  - `flip`: `41`
  - `market depth`: `17`
  - `cancel`: `57`
  - `normal`: `0`
  - `order lifecycle`: `0`
  - `top-of-book`: `0`
  - `market by order`: `0`
  - `non-manipulation`: `0`

## Decision

The parsed complaint materially improves official route/date/product context for the R6 Oystacher path, but it still does not provide the Board A R6 unlock packet.

It does not include source-owned normal/non-manipulation control rows, order-lifecycle rows, top-of-book/depth export rows, MBO/L3 rows, a provenance manifest with ticket/export/license identifiers, or any verifier-native file set under `/tmp/ict-engine-board-a-r6-owner-export-v1`.

## Gate

- R6 owner/export unlock: `false`
- R5 recency unlock: `false`
- R3 native-subhour unlock: `false`
- Valid required-root unlock: `false`
- Source/control evidence acquired: `false`
- Accepted rows added: `0`
- Canonical merge: `false`
- Downstream promotion rerun: `false`
- Strict full objective: `false`
- Trade usable: `false`
- `update_goal=false`

## Next

Continue only from explicit source/control approval, verifier-native R6 owner/export rows with valid controls, source-owned post-`2026-01-30` R5 rows matching the source-panel schema, verifier-native Crisis-capable R3 `MainRegimeV2` labels, or a genuinely new accepted cross-timeframe `MainRegimeV2` source export before direct verifier, split calibration, canonical merge, provider/AutoQuant selected-data research, filter / Pre-Bayes, BBN, CatBoost/path-ranking, or execution-tree promotion.
