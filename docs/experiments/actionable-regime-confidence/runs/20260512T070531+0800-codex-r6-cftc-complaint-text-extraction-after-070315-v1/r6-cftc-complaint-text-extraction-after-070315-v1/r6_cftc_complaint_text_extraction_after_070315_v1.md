# R6 CFTC Complaint Text Extraction After 070315 v1

Run id: `20260512T070531+0800-codex-r6-cftc-complaint-text-extraction-after-070315-v1`

Gate result: `r6_cftc_complaint_text_extraction_after_070315_v1=official_counts_extracted_controls_not_acquired_no_unlock`

## Scope

This packet extracts official CFTC Oystacher complaint and consent-order text after the `070315` public exact-source route probe. It improves the R6 official-route fact base only. It does not acquire source-owned normal-control rows, does not populate `/tmp/ict-engine-board-a-r6-owner-export-v1`, does not mutate R3/R5/R6 target roots, does not run canonical merge, does not rerun downstream promotion, does not make a trade claim, and does not call `update_goal`.

## Readback

- `curl_cftc_consent_order.exit=0`.
- `extract_cftc_pdf_summaries.exit=0`.
- Complaint PDF pages: `36`.
- Consent-order PDF pages: `19`.
- Extracted official product groups: `6`.
- Extracted charged trading days: at least `51`.
- Extracted product/count/fill-rate facts cover COMEX copper, NYMEX crude oil, NYMEX natural gas, CFE VIX, and CME E-Mini S&P 500 windows.
- The extraction confirms official source-route context, product/date/count fields, and complaint/order text access. It does not include verifier-native row-level order-lifecycle controls, source-owned normal controls, delivery-ticket provenance, R5 post-cutoff regime rows, or R3 Crisis-capable `MainRegimeV2` labels.

## Decision

The official CFTC PDFs strengthen the R6 acquisition route but do not unlock Board B. The missing gate is still owner/export normal-control data with provenance, or another accepted R3/R5/R6 source/control unlock. Accepted rows added `0`; valid required-root unlock false; source/control evidence acquired false; canonical merge false; downstream promotion rerun false; strict full objective false; trade usable false; `update_goal=false`.

## Artifacts

- Summary JSON: `docs/experiments/actionable-regime-confidence/runs/20260512T070531+0800-codex-r6-cftc-complaint-text-extraction-after-070315-v1/r6-cftc-complaint-text-extraction-after-070315-v1/r6_cftc_complaint_text_extraction_after_070315_v1.json`
- Product counts CSV: `docs/experiments/actionable-regime-confidence/runs/20260512T070531+0800-codex-r6-cftc-complaint-text-extraction-after-070315-v1/r6-cftc-complaint-text-extraction-after-070315-v1/r6_cftc_complaint_product_counts_v1.csv`
- Consent-order PDF: `docs/experiments/actionable-regime-confidence/runs/20260512T070531+0800-codex-r6-cftc-complaint-text-extraction-after-070315-v1/command-output/enfoystacherorder122016.pdf`
- Extraction stdout/stderr/exit: `docs/experiments/actionable-regime-confidence/runs/20260512T070531+0800-codex-r6-cftc-complaint-text-extraction-after-070315-v1/command-output/`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260512T070531+0800-codex-r6-cftc-complaint-text-extraction-after-070315-v1/checks/r6_cftc_complaint_text_extraction_after_070315_v1_assertions.out`

## Next

Continue only from explicit source/control approval, verifier-native R6 owner-export rows with valid controls, source-owned post-`2026-01-30` R5 recency rows matching the source-panel schema, verifier-native Crisis-capable R3 `MainRegimeV2` labels, or a genuinely new accepted cross-timeframe `MainRegimeV2` source export before direct verifier, split calibration, canonical merge, provider/AutoQuant promotion, filter / Pre-Bayes, BBN, CatBoost/path-ranking, or execution-tree promotion.
