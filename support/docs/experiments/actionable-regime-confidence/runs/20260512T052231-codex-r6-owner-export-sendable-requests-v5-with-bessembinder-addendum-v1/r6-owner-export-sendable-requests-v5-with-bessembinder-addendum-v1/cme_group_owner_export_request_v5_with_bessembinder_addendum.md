# CME Group R6 Owner Export Request v5 With Bessembinder Addendum

Use this with the existing CME Group request v4:

- Base request: `docs/experiments/actionable-regime-confidence/runs/20260512T015040-codex-r6-owner-export-sendable-requests-v4-current-routes-v1/r6-owner-export-sendable-requests-v4-current-routes-v1/cme_group_owner_export_request_v4.md`
- Delivery root after approval/export: `/tmp/ict-engine-board-a-r6-owner-export-v1`

## Add To The CME Request

Please also include, if available through CME DataMine, CME Market Depth, CFTC/court-source materials, or licensed exchange data systems, verifier-native Bessembinder/CFTC comparison-cohort rows for the same Oystacher CME/NYMEX/COMEX products and date windows requested in v4.

Requested cohort classes:
- Oystacher flip/spoof rows used in the analysis.
- Other flipping market participants in the same products, dates, sessions, and market contexts.
- Broader market-participant activity rows for the same products and windows.
- Non-flip order rows suitable for normal/non-manipulation controls.

Required fields when available:
- source system, export id, license/ticket id, and extraction timestamp
- product, exchange, instrument, contract, session, and trading date
- timestamp with exchange/source precision
- anonymized participant/account id or source-stable participant key
- order id, event/action type, side, price, size, displayed quantity, fill quantity, cancel quantity
- flip/spoof/control cohort marker assigned by the source owner or by the documented CFTC/Bessembinder analysis
- provenance link to the legal/source artifact or licensed export manifest

Boundary: this request text does not approve same-exhibit `FLIP` controls and does not authorize canonical merge or downstream promotion.
