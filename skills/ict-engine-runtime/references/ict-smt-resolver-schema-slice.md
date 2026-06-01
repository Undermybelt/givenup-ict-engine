# ICT SMT resolver schema slice

Use this detail when Board B asks for SMT relationship resolver work or when SMT must become first-class runtime evidence rather than prose.

## Durable lesson

A resolver-schema slice is infrastructure, not promotion evidence. It should expose structured related-market candidates and provider-universe filtering, but it must not claim Auto-Quant, BBN, CatBoost, execution-tree, or trade-readiness closure unless those stages actually ran.

## Minimal runtime surface

For `smt_relationship_resolver`, prefer a first-class struct/function that emits:

- `symbol`
- `primary_related_symbols`
- `futures_peers`
- `cfd_proxies`
- `etf_proxies`
- `sector_or_industry_peers`
- `currency_macro_drivers`
- `session_leaders`
- `relationship_type`
- `confidence`
- `evidence_source`

The resolver should support at least:

- `NQ -> ES/YM/RTY/QQQ/SPY/DIA/IWM/NAS100/US500/US30/DXY/VIX`
- `EURUSD -> GBPUSD/DXY/EURGBP`
- `XAUUSD -> XAGUSD/DXY/US10Y/real_yield/GDX`
- `BTC -> ETH/SOL/TOTAL/QQQ/DXY`
- equity fallback: index ETF, sector ETF, futures/macro proxies

If `available_symbols` or provider universe is supplied, filter to that universe and do not invent absent symbols.

## TDD shape

1. RED: add tests that call the missing resolver and assert schema fields for index, FX, metals, crypto, equity fallback, and provider-universe filtering.
2. GREEN: add the smallest resolver and struct needed to pass.
3. Regression: run the broader SMT suite, not only the new resolver tests.

Useful test filters:

```bash
cargo test smt_relationship_resolver -- --nocapture
cargo test smt -- --nocapture
```

## Board B reporting

For schema-only resolver work:

- create a compact run-root summary under `support/docs/experiments/.../summaries/`
- append only a terminal Board B decision row
- decision should normally be `handoff`, not `keep` or `promotion`
- explicitly say existing strict SMT density/admission packets still control downstream promotion if strict pair/per-regime rows remain insufficient

## Pitfalls

- Do not call generic rolling correlation output SMT. Correlation is a relationship-stability gate only.
- Do not make SMT `actionable=true` by itself.
- Do not rerun or claim Auto-Quant/BBN/CatBoost/execution-tree for a schema-only slice.
- Do not use repo markdown as runtime input. Promote rules into typed structs, schemas, fixtures, or tests.
- In high-concurrency Board B work, claim outside the repo under `/tmp/ict-engine-agent-claims/board-b/` and only write terminal evidence to Board docs.
