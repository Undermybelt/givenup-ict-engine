# CME Group Owner Export Request Message v1

Subject: Board A R6 Oystacher normal-control export request for CME/NYMEX/COMEX order-lifecycle data, 2011-2013

Hello CME Data Services team,

I need a source-owned export for compliance validation of normal/non-manipulation order-lifecycle controls related to the Oystacher R6 evidence lane. The requested output is not a trading signal request. It is a verifier input package for negative/control rows with durable provenance.

Requested source-owner route:

- CME DataMine Market Depth, Market by Order, FIX/FAST, or a licensed equivalent export.
- Please confirm product/date availability for the requested period before export.

Requested coverage:

- Venues/routes: CME Globex, NYMEX/CME Globex, COMEX/CME Globex.
- Products: Crude Oil futures, Natural Gas futures, High-Grade Copper futures, E-mini S&P 500 futures.
- Date scope: Oystacher Exhibit A coverage years 2011, 2012, and 2013.
- Required controls: at least 73 valid normal/non-manipulation order-lifecycle rows for each requested cell.
- Exclusion: rows should not be same-exhibit `FLIP` rows unless a separate explicit exception approval is supplied.

Requested cell coverage:

| Axis | Bucket |
|---|---|
| contract_family | energy |
| contract_family | equity_index |
| contract_family | metals |
| venue_exact | CME Globex |
| venue_exact | COMEX/CME Globex |
| venue_exact | NYMEX/CME Globex |
| symbol_exact | Crude Oil futures |
| symbol_exact | E-mini S&P 500 futures |
| symbol_exact | High-Grade Copper futures |
| symbol_exact | Natural Gas futures |
| chronological_year | 2011 |
| chronological_year | 2012 |
| chronological_year | 2013 |

Requested row fields:

- event or order timestamp
- trade timestamp when applicable
- venue
- product, contract, or instrument identifier
- side
- order event type or lifecycle action
- order count or stable row count field
- quantity
- price when available
- normal/non-manipulation control marker or source-owner control classification
- source owner
- export id, license id, or support ticket id
- provenance note sufficient to support verifier replay

Preferred delivery shape:

- `matched_negative_normal_activity_rows.csv` containing the normal-control rows.
- A provenance manifest or export metadata file identifying CME Group as source owner and the export route used.
- If fields must be masked, please preserve stable row identity, instrument, venue, date, side, event/action, quantity, and provenance fields.

The downstream verifier will not treat raw depth rows as accepted controls unless source-owner provenance and the normal/non-manipulation control basis are explicit.
