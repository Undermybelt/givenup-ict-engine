# 2026-05-27 stock-screener intake for ict-engine

## Target

External repo reviewed: `https://github.com/xang1234/stock-screener`

Question: can it provide a useful new data source for `ict-engine`?

## Verdict

Yes, but only as a **narrow source-intake reference**, not as a repo/runtime
dependency.

Directly adopting the project would add a large FastAPI/Celery/Postgres/Redis
application surface to solve a problem that `ict-engine` already solves with a
smaller read-only provider bridge in
`support/scripts/auto_quant_external/fetch_external.py`.

The reusable value is in a few provider ideas that are not first-class in
`ict-engine` today:

1. `Finviz` fundamentals / quarterly growth sidecar
2. `SEC EDGAR` filings / document text sidecar
3. `Alpha Vantage` as an opt-in keyed equity/fundamental backup source

The repo is **not** a meaningful source of new OHLCV coverage for `ict-engine`
because its price-history path still leans heavily on `yfinance`, which
`ict-engine` already supports directly.

## Why the repo is not an integration target

Observed repo shape from README / architecture docs:

- full platform stack: FastAPI + Celery + Postgres + Redis
- multiple background workers and caching/rate-limit layers
- screening / ranking / notification surfaces mixed with data-fetch concerns
- provider mix includes `yfinance`, `finvizfinance`, Alpha Vantage, SEC EDGAR,
  and TradingView-style symbol/technical surfaces

For `ict-engine`, importing that stack would violate current adapter boundaries:

- current external adapter scope is read-only market data and research support
- `fetch_external.py` already holds the source-of-truth fetch surface
- new sources should arrive as small provider subcommands, not as a second app

## What is actually new for ict-engine

### Worth considering

#### Finviz

Most distinct signal from the repo.

Potential use in `ict-engine`:

- lagged equity fundamentals sidecar
- quarterly growth metadata
- universe prefilter for U.S. equities

Caveat:

- the reviewed repo uses `finvizfinance`, so copying its exact implementation
  would add a third-party scraping dependency
- if we ever intake this, prefer a clearly opt-in sidecar with isolated schema
  and explicit rate-limit handling

#### SEC EDGAR

Useful as a document / filing context source rather than a bar-data source.

Potential use in `ict-engine`:

- filing-event context
- text extraction for research-side factors
- earnings / filing recency features

Caveat:

- separate schema from OHLCV
- should remain read-only and offline-consumable after fetch

#### Alpha Vantage

Possible fallback / enrichment source, but lower priority.

Potential use in `ict-engine`:

- opt-in keyed backup for U.S. equity history / indicators / fundamentals

Caveat:

- overlaps with existing `yahoo` and `polygon` coverage
- API limits and key requirement make it less attractive than Finviz/EDGAR for
  a first intake slice

### Not worth adopting from this repo

- `yfinance` price history: already present in `ict-engine`
- full screening/ranking application logic: wrong boundary for this repo
- background task / cache / DB stack: unnecessary debt for the fetch layer

## Recommended ict-engine path

If this source family is pursued, the best slice is:

1. keep `stock-screener` as a reviewed reference only
2. add one new opt-in sidecar source to `fetch_external.py`
3. start with `finviz` or `sec-edgar`, not Alpha Vantage OHLCV
4. keep output schema explicit and separate from canonical OHLCV rows
5. avoid importing the external app, worker model, or database assumptions

## Integration shape if implemented later

Preferred pattern:

- new subcommand under `support/scripts/auto_quant_external/fetch_external.py`
- write a standalone CSV/JSON artifact
- no repo-default market assumptions
- no background daemon requirement
- tests alongside existing `support/scripts/auto_quant_external/tests/*`

## Risk rating

`MEDIUM`

Why:

- public open-source repo with readable docs and provider boundaries
- but it is a much larger runtime than `ict-engine` needs
- and several useful features are wrappers over third-party services rather than
  unique upstream market feeds

## Decision

Accepted as a **reviewed idea source**.

Rejected as a **direct dependency / embedded subsystem**.
