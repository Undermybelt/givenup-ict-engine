# Forward watchlist provider parity for regime-rooted factors

Use this note when a regime-rooted factor has already passed an earlier Auto-Quant/BBN/CatBoost/execution-tree handoff, but the next step is forward observation on fresh bars.

## Durable pattern

1. Keep the exact regime-rooted branch path from the matured candidate:

`main_regime -> sub_regime -> candidate_factor -> profit_factor`

2. Try the preferred provider first, usually IBKR for US equities/ETFs.
3. If IBKR provider-status says ready but historical fetch times out or returns empty, record the fetch as a provider-window/runtime blocker for that lane, not as a factor failure.
4. Retry a smaller real IBKR window for at least one representative symbol before falling back.
5. TradingViewMCP or yfinance may update a watchlist, but classify it as provider fallback only:
   - not IBKR parity;
   - not live-ready evidence;
   - not a reason to promote through execution tree.
6. For provider fallback bars, audit the latest regular session bar separately from synthetic/end-of-session zero-volume bars. Signal checks should report both:
   - `latest_bar`;
   - `latest_regular_bar` where `volume > 0`.
7. Preserve downstream truth from execution-tree readback. If the exact branch is visible but `gate_status=observe`, `closed_loop_actionable=false`, or `execution_tree_branch=transition_guardrail`, conclude `continue_observe` / `fail_closed`.

## Compact artifact shape

Write a small `current_step_summary.json` with:

- route alias and skill path used;
- primary and guarded branch paths;
- provider probe results by provider/window;
- fallback watchlist artifact paths;
- latest regular bar timestamp;
- per-symbol recent signal counts;
- execution-tree readback fields;
- final decision.

## Example verdict language

Correct:

`IBKR fresh fetch blocked; TradingViewMCP watchlist updated; exact branch remains visible; execution tree still transition_guardrail/observe; no live promotion.`

Incorrect:

`TradingViewMCP produced rows, so the factor is forward validated.`

## Session evidence pattern

Observed during a high-window reclaim 30m branch:

- IBKR 30m 30D all-symbol fetch timed out.
- IBKR QQQ 30m 7D retry timed out.
- yfinance 7D fetched rows but latest probe had zero volume, so fallback only.
- TradingViewMCP 30D fetched usable 30m rows with nonzero regular bars, so it was acceptable for watchlist telemetry only.
- Execution-tree remained exact-branch visible but `transition_guardrail/observe`, `closed_loop_actionable=false`.
