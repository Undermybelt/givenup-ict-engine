# External market-data repo intake — 2026-05-20

Scope: reviewed frankcash/Scala-Quant, hongtaocai/googlefinance, and pydata/pandas-datareader for ict-engine utility. Repos cloned read-only under /tmp; no package install or untrusted runtime execution.

Routing/security notes:
- Primary route: `sd/hermes-agent-sec-review` because task used external GitHub repos.
- Domain support: `ict-engi-fact-rese-muta` for ict-engine factor/provider relevance.
- Repo guidance support: `rece-repo-inta-read-rout` for README-first triage.

Findings:
- Scala-Quant: learn only. Useful as a small pattern for CSV-to-feature smoke fixtures and trivial baseline factors: moving average, average support/resistance by chunk, Fibonacci retracement. Do not import its Scala code; it is old, hard-codes local paths, uses Google Finance/IFTTT CSV assumptions, and has minimal factor rigor.
- hongtaocai/googlefinance: do not adopt as a provider. README itself says Google closed the endpoint; code uses deprecated plain HTTP Google Finance endpoints, Python 2-style print, demjson, and no resilient provider contract. Only reusable idea is a normalized quote/news field map and an explicit `provider_closed/deprecated_endpoint` failure category.
- pandas-datareader: strongest utility. Absorb provider-adapter design: many named readers behind one `DataReader` surface, shared retry/pause/session/timeout behavior, clean pandas table output, and broad public/macroeconomic/provider coverage: Yahoo, FRED, Fama-French, OECD, Eurostat, Nasdaq symbols, Stooq, MOEX, Tiingo, AlphaVantage, IEX, Quandl, Bank of Canada, Econdb, Naver. Some endpoints/API requirements may be stale; must be per-provider capability-checked.

ict-engine integration implications:
1. Keep existing native yfinance path as default zero-config; pandas-datareader should not replace it.
2. Add a `pandas-datareader` optional bridge as a batch historical/macro/reference provider, likely behind `market-data-harness`/external_http_runtime or a Python JSON subprocess.
3. Promote per-provider capability records: `kind`, `requires_api_key`, `interval_support`, `asset_class`, `freshness`, `adjustment_policy`, `actions/dividends/splits`, `rate_limit`, `staleness_status`.
4. Candidate high-value lanes:
   - FRED/OECD/Eurostat/Bank of Canada: macro regime covariates for Board A and transition-hazard context.
   - Fama-French: equity style-factor benchmarks and residual alpha diagnostics.
   - Stooq/MOEX/Naver/Nasdaq symbols: reference universes and cross-market coverage, not direct trade admission until freshness verified.
   - Yahoo actions/dividends/options: corporate-action adjustment and options/dealer evidence cross-checks; inspection-grade until coverage/freshness verified.
5. Gate rule: every imported provider is observation/backtest-grade until live runtime evidence plus existing Gate 1/cost/downstream/BBN/CatBoost/execution-tree checks pass.

Suggested next slice:
- Implement a minimal Python bridge command that calls pandas-datareader only for `fred`, `famafrench`, `stooq`, and `yahoo-actions` first, returns normalized JSON with provenance and error category, then register it as optional provider capability in ict-engine. Avoid `googlefinance` runtime adoption.
