# Board A provider matrix fail-closed pattern

Use when Board A asks for provider-backed regime confidence across markets/timeframes and the chain must run through provider fetch, ICT Engine posterior, Pre-Bayes/BBN, CatBoost/path-ranker, execution tree, and Auto-Quant without taking over Board B.

## Durable lessons

- `provider-status ready` is only a prerequisite. It does not prove the provider can return the requested instrument/window. Always run the concrete fetch and record row count, time range, and exit status.
- A mixed provider request can stop after the first failed role. If that hides later roles, rerun critical providers as single-role requests so the terminal summary distinguishes `not executed` from `executed and failed`.
- Treat TradingViewRemix / IBKR / Kraken / yfinance as separate evidence rows: health, request shape, rows, and runtime contribution are different facts.
- Board A must not seed Auto-Quant strategies just to unblock `run.py`; active non-underscore strategy seed work belongs to a Board B/profit-factor lane unless the user explicitly opens that lane.
- Auto-Quant `data_ready=true` is not promotion evidence. `dependency_ready_seed_required` still blocks execution; record it as a boundary, not as progress toward 95% regime confidence.
- 95% regime claims require current posterior confidence and cross-provider/cross-period validation, not merely successful fetches or aggregate downstream artifacts.

## Minimal run shape

1. Provider readiness:
   - `cargo run --quiet -- provider-status --compact`
   - focused provider checks for `tradingview_mcp`, `ibkr`, `kraken_public`, `yfinance` when relevant.
2. Provider fetch matrix:
   - use `market-data-harness --action fetch --request-json <request>` for yfinance/TVR/IBKR roles.
   - if one failed role aborts the command, rerun later roles independently.
   - use `scripts/auto_quant_external/fetch_external.py kraken-kline` for Kraken futures/spot rows.
3. Runtime chain:
   - `analyze-live ... --state-dir <run-root>/state --human`
   - `workflow-status --refresh --agent`
   - `pre-bayes-status --refresh --output-format json`
   - `policy-training-status --output-format agent`
   - `export-structural-path-ranking-target`
4. Auto-Quant boundary:
   - run `factor-research`; if it says `dependency_ready_data_missing`, run `auto-quant-prepare`.
   - rerun `factor-research` after prepare.
   - stop at `dependency_ready_seed_required` in Board A unless Board B ownership is explicit.
5. Terminal summary:
   - state `keep/drop/incubate/blocked/handoff`.
   - include rows/time ranges, posterior probabilities, path-ranker maturity counts, AQ status, and exact artifact paths.
   - write only the terminal decision into the Board A current doc.

## Acceptance blocker wording

Use fail-closed language such as:

- `not promotable: provider fetch failed/timeout/empty`
- `posterior confidence below target`
- `path-ranker immature: mature_rows=0, training_weight_rows=0`
- `Auto-Quant boundary: dependency_ready_seed_required; no Board B seed created`

Do not soften this into “partial success” when the user asked for 95% portable confidence.
