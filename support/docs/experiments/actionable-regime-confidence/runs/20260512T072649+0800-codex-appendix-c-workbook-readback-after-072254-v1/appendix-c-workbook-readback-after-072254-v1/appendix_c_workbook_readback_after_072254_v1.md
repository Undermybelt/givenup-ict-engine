# Appendix C Workbook Readback After 072254 v1

Run id: `20260512T072649+0800-codex-appendix-c-workbook-readback-after-072254-v1`

Gate result: `appendix_c_workbook_readback_after_072254_v1=public_case_summary_context_no_r6_owner_export_controls_no_unlock`

## Scope

Read-only parse of the workbook downloaded by `20260512T072254+0800-codex-zenodo-oystacher-appendix-source-route-after-071839-v1`.
The workbook is `Online Appendix C.xlsx` from Zenodo record `10.5281/zenodo.16629490`, described as an online appendix for a Capital Markets Law Journal article on spoofing in U.S. futures markets.

This readback does not mutate R3/R5/R6 roots, approve public case-summary rows as owner/export data, run canonical merge, rerun downstream promotion, select historical data, or call `update_goal`.

## Workbook Structure

- Source file: `docs/experiments/actionable-regime-confidence/runs/20260512T072254+0800-codex-zenodo-oystacher-appendix-source-route-after-071839-v1/command-output/Online Appendix C.xlsx`
- Workbook sheets: `Abbreviations`, `CFTC`, `ICE Futures U.S.`, `CME Group`
- Sheet dimensions:
  - `Abbreviations`: `A1:B3`, `3` XML rows
  - `CFTC`: `A1:AO64`, `64` XML rows
  - `ICE Futures U.S.`: `A1:M29`, `29` XML rows
  - `CME Group`: `A1:P117`, `117` XML rows
- Parse method: stdlib ZIP/XML text extraction. `openpyxl` was not installed, and Python XML expat loading failed in this shell, so parsing used direct XLSX shared-string and sheet XML extraction without modifying the workbook.

## Oystacher / 3 Red Row Readback

The CFTC sheet contains a row for `CFTC 15-cv-09196`, defendants `Igor B. Oystacher and 3 Red Trading LLC`.

Observed row fields:

- Relevant period/days: `December 2011 - January 2014`, at least `51` trading days.
- Instrument: futures.
- Market categories: metals, energy, equity index.
- Underlying products: copper, crude oil, natural gas, VIX, and E-mini S&P 500.
- Number of times spoofed in relevant period: total `1316`; copper `288`; crude oil `324`; natural gas `330`; VIX `59`; E-mini S&P 500 `285`.
- Spoofing type: single, layered, and flipping.
- Spoof orders in relevant period/days: total `5207` spoof orders and `359790` contracts, with product-level counts in the workbook row.
- Spoof-order size: copper mean `15`, crude oil mean `24`, natural gas mean `19`, VIX mean `133`, and E-mini S&P 500 range `176-501`.
- Price-level volume increase due to spoof orders: copper `1877%`, crude oil `991%`, natural gas `1710%`, VIX `1696%`, E-mini S&P 500 `880-996%`.
- Spoof cancellation rates: copper `99.11%`, crude oil `98.13%`, natural gas `99.49%`, VIX `99.06%`, E-mini S&P 500 `99.43%-99.83%`.
- Spoof cancellation time: overall `<1` second, with product values near `0.614-0.752` seconds.
- Hit-rate comparison in the workbook row reports low spoof-order hit rates and high genuine-order hit rates by product.

## Decision

This workbook materially improves public source-route context for R6-style spoofing/manipulation cases, including an Oystacher/3 Red aggregate row with product-level spoofing metrics.

It still does not satisfy the Board B source/control gate:

- It is public case-summary / academic appendix data, not verifier-native owner/export order-lifecycle rows.
- It does not provide matched normal-control rows.
- It does not provide row-level provenance tying every positive/control row to a source-owner export.
- It does not provide source-owned post-`2026-01-30` R5 `MainRegimeV2` source-panel rows.
- It does not provide verifier-native Crisis-capable R3 `MainRegimeV2` labels.

Accepted rows added: `0`.
R6 owner/export unlock: `false`.
R5 recency unlock: `false`.
R3 native-subhour unlock: `false`.
Valid required-root unlock: `false`.
Source/control evidence acquired: `false`.
Canonical merge: `false`.
Downstream promotion rerun: `false`.
Strict full objective: `false`.
Trade usable: `false`.
`update_goal=false`.

## Next

Continue source/control acquisition only. The strongest remaining R6 path is not this public appendix by itself; it is a source-owner or operator-approved export that supplies row-level positives, matched normal controls, and provenance for the same case/product family.
