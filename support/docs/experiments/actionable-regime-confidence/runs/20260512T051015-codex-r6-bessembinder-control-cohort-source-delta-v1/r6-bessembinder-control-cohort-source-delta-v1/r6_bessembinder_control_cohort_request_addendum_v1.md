# R6 Bessembinder Control Cohort Request Addendum v1

Purpose: add a Bessembinder/CFTC comparison-cohort clause to the existing R6 owner-export request. This addendum is request text only; it is not acquired data, approval, source/control evidence, or a canonical merge.

## Addendum Text

Please include, if available from the CFTC/CME/Court-source Bessembinder analysis or licensed exchange data systems, verifier-native comparison cohort rows for the same products and date windows as the Oystacher R6 lane.

Requested cohort classes:
- Oystacher flip/spoof rows used in the analysis.
- Other flipping market participants in the same products, dates, sessions, and market contexts.
- Broader market-participant activity rows for the same products and windows.
- Non-flip order rows suitable for normal/non-manipulation controls.

Required fields, when available:
- source system, export id, license/ticket id, and extraction timestamp
- product, exchange, instrument, contract, session, and trading date
- timestamp with exchange/source precision
- anonymized participant/account id or source-stable participant key
- order id, event/action type, side, price, size, displayed quantity, fill quantity, cancel quantity
- flip/spoof/control cohort marker assigned by the source owner or by the documented CFTC/Bessembinder analysis
- provenance link to the legal/source artifact or licensed export manifest

Board A verifier constraint:
- Normal/control rows must be source-owned or explicitly source-approved.
- Same-exhibit `FLIP` rows remain invalid as controls unless the user or board explicitly approves that exception.
- The target delivery root remains `/tmp/ict-engine-board-a-r6-owner-export-v1`, with provenance beside the row files.

## Boundary

This addendum sharpens the request only. It does not create rows, does not approve controls, and does not authorize downstream verifier, calibration, provider/AutoQuant, filter/Pre-Bayes, BBN, CatBoost, or execution-tree promotion.
