# TVR CRWD 1m full-ladder Gate 1 stop pattern

Session lesson from CRWD PDA/MTF soft-confirmation continuation.

Use when a same-root 5m/15m branch looked promising, but the user asks to continue from a 1m-origin ladder with full timeframe coverage.

Pattern:
- Preserve exact branch identity as `market -> product -> symbol -> base_timeframe -> main_regime -> sub_regime -> first_profit_factor -> overlays...`.
- Fetch the full feasible ladder as real provider rows when possible: `1m/5m/15m/30m/1h/4h/1d`.
- Treat each timeframe lane independently. A positive 5m sibling does not rescue a failed 1m root.
- Require the explicit 1m origin to be dense, positive, and cost-surviving before downstream.
- If `positive_origin_1m=[]` or cost gate says `cost_fragile_or_no_dense_origin`, stop before Pre-Bayes/BBN/CatBoost/execution tree.
- Do not add overlays to rescue a weak 1m root; pivot to a materially denser 1m entry family.

Concrete observed shape:
- Provider: TradingView MCP, fresh `NASDAQ:CRWD`, no cache replay.
- Covered: `1m/5m/15m/30m/1h/4h/1d`.
- 1m origin: 15 trades, 46.6667% win rate, 0.13% profit, Sharpe 1.5474.
- 5m sibling: 27 trades, 70.3704% win rate, 4.77% profit, Sharpe 11.8174.
- Gate: `expected_ladder_covered=true`, `branch_fields_preserved=true`, `positive_origin_1m=[]`, `cost_gate.pass=false`, `downstream_allowed=false`.

Decision rule:
- Terminalize as observation/drop for this root: `drop_or_block_gate1_practical`.
- Next action: choose a denser 1m entry family under a new exact rooted branch; do not grind the same PDA/MTF overlay.
