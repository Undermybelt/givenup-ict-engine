# Cboe/CFE Owner Export Request Message v1

Subject: Board A R6 Oystacher normal-control export request for 2014 CFE/VIX futures order-lifecycle data

Hello Cboe/CFE market data support team,

I need a source-owned export for compliance validation of normal/non-manipulation order-lifecycle controls related to the Oystacher R6 evidence lane. The requested output is not a trading signal request. It is a verifier input package for negative/control rows with durable provenance.

Requested source-owner route:

- Cboe/CFE DataShop, CFE Depth-of-Book, market-data support export, or a licensed equivalent export.
- Please confirm whether 2014 historical VIX futures depth/order-lifecycle rows are available before export.

Requested coverage:

- Venue/route: CFE/CBOE Futures Exchange.
- Product: VIX futures.
- Date scope: 2014 Oystacher Exhibit A coverage.
- Required controls: at least 73 valid normal/non-manipulation order-lifecycle rows for each requested cell.
- Exclusion: rows should not be same-exhibit `FLIP` rows unless a separate explicit exception approval is supplied.

Requested cell coverage:

| Axis | Bucket |
|---|---|
| contract_family | volatility_index |
| venue_exact | CFE/CBOE Futures Exchange |
| symbol_exact | VIX futures |
| chronological_year | 2014 |

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
- A provenance manifest or export metadata file identifying Cboe/CFE as source owner and the export route used.
- If fields must be masked, please preserve stable row identity, instrument, venue, date, side, event/action, quantity, and provenance fields.

The downstream verifier will not treat public summary pages or unlabeled raw data as accepted controls unless source-owner provenance and the normal/non-manipulation control basis are explicit.
