# Market-state threading into factor reports

Use when closing the `regime -> factor-research -> factor-backtest -> analyze/live -> recommendation` gap and the audit says `factor-research` / `factor-backtest` do not consume or report market-state primary/secondary regime.

## Runtime closure target

Both `factor-research` and `factor-backtest` should emit market-state evidence in:
- top-level `multi_timeframe_summary`
- `agent_context_bundle.multi_timeframe_summary`
- human output as one compact line (e.g. `Market State: RangeConsolidation/WideRange | bbn_regime=range | liquidity=favorable`)

Minimum fields:
- `market_state_primary_regime=<PrimaryMarketRegime>`
- `market_state_secondary_regime=<SecondaryMarketRegime>`
- `market_state_overall_confidence=<float>`
- `market_state_bbn_market_regime=<label|passthrough>`
- `market_state_bbn_liquidity_context=<label|passthrough>`
- `market_state_evidence=<line>` for the richer evidence lines

Use `passthrough` when `market_state_to_bbn_*` returns `None`; absence of the field looks like a broken report chain.

## Implementation shape

In the bin crate (`src/main.rs` helper area), add a reusable helper around the existing analyze-side functions:

```rust
fn build_market_state_summary_for_candles(candles: &[Candle]) -> Vec<String> {
    let snapshot = ict_engine::market_state::MarketStateClassifier::new().classify(candles);
    let mut summary = vec![
        format!("market_state_primary_regime={:?}", snapshot.primary_regime),
        format!("market_state_secondary_regime={:?}", snapshot.secondary_regime),
        format!("market_state_overall_confidence={:.3}", snapshot.overall_confidence),
    ];
    summary.push(format!(
        "market_state_bbn_market_regime={}",
        market_state_to_bbn_regime_label(&snapshot).unwrap_or("passthrough")
    ));
    summary.push(format!(
        "market_state_bbn_liquidity_context={}",
        market_state_to_bbn_liquidity_label(&snapshot).unwrap_or("passthrough")
    ));
    summary.extend(
        market_state_evidence_lines(&snapshot)
            .into_iter()
            .map(|line| format!("market_state_evidence={line}")),
    );
    summary
}
```

Then extend the summary before the PDA context line in both runtimes:
- `src/factor_research_runtime.rs`
- `src/factor_backtest_runtime.rs`

```rust
report
    .multi_timeframe_summary
    .extend(build_market_state_summary_for_candles(&candles));
```

`agent_context_bundle.multi_timeframe_summary` usually copies from `report.multi_timeframe_summary`; verify both top-level and bundle outputs.

Human reporting path:
- `src/application/reporting/backtest_output.rs`
- `render_factor_research_human_output(...)` and `render_factor_backtest_human_output(...)` should parse the same `multi_timeframe_summary` keys and emit a single short line:
  - `Market State: <primary>/<secondary> | bbn_regime=<label|passthrough> | liquidity=<label|passthrough>`
- Keep the rich key/value evidence in JSON; human output should not dump all `market_state_evidence=` lines.

## TDD / verification

RED:
```bash
cargo test --bin ict-engine test_market_state_summary_threads_primary_secondary_regime -- --nocapture
```
Expected initial failure: missing helper or missing BBN passthrough field.

GREEN:
```bash
cargo test --bin ict-engine test_market_state_summary_threads_primary_secondary_regime -- --nocapture
cargo test --bin ict-engine market_state_summary -- --nocapture
cargo test --bin ict-engine multi_timeframe -- --nocapture
cargo test --lib factor_research_human_output_is_short_text_not_json_dump -- --nocapture
cargo check
cargo build --bin ict-engine
```

Runtime smoke with isolated state:
```bash
BASE=/tmp/ict-mainline-regime-audit
STATE=$BASE/state-verify
./target/debug/ict-engine factor-research --symbol NQ \
  --data $BASE/cleaned-15m/nq.continuous-15m.json \
  --data-1m $BASE/cleaned-1m/nq.continuous-1m.json \
  --data-5m $BASE/cleaned-5m/nq.continuous-5m.json \
  --data-15m $BASE/cleaned-15m/nq.continuous-15m.json \
  --data-30m $BASE/cleaned-30m/nq.continuous-30m.json \
  --data-1h $BASE/cleaned-1h/nq.continuous-1h.json \
  --data-4h $BASE/cleaned-4h/nq.continuous-4h.json \
  --data-1d $BASE/cleaned-1d/nq.continuous-1d.json \
  --backend native --state-dir $STATE --output-format json > $BASE/factor-research-verify.json

./target/debug/ict-engine factor-backtest --symbol NQ \
  --data $BASE/cleaned-15m/nq.continuous-15m.json \
  --data-1m $BASE/cleaned-1m/nq.continuous-1m.json \
  --data-5m $BASE/cleaned-5m/nq.continuous-5m.json \
  --data-15m $BASE/cleaned-15m/nq.continuous-15m.json \
  --data-30m $BASE/cleaned-30m/nq.continuous-30m.json \
  --data-1h $BASE/cleaned-1h/nq.continuous-1h.json \
  --data-4h $BASE/cleaned-4h/nq.continuous-4h.json \
  --data-1d $BASE/cleaned-1d/nq.continuous-1d.json \
  --state-dir $STATE --output-format json > $BASE/factor-backtest-verify.json
```

Check both top-level and bundle summaries plus human output:
```bash
python3 - <<'PY'
import json
for name in ['factor-research-verify','factor-backtest-verify']:
    p=f'/tmp/ict-mainline-regime-audit/{name}.json'
    data=json.load(open(p))
    summary=data.get('multi_timeframe_summary') or data.get('report',{}).get('multi_timeframe_summary') or []
    bundle=data.get('agent_context_bundle') or data.get('report',{}).get('agent_context_bundle') or {}
    bsum=bundle.get('multi_timeframe_summary') or []
    keys=[x for x in summary if x.startswith('market_state_primary_regime=') or x.startswith('market_state_secondary_regime=') or x.startswith('market_state_bbn_')]
    bkeys=[x for x in bsum if x.startswith('market_state_primary_regime=') or x.startswith('market_state_secondary_regime=') or x.startswith('market_state_bbn_')]
    print(name, keys[:6], bkeys[:6])
PY
```

Human smoke:
```bash
./target/debug/ict-engine factor-research ... --human > $BASE/factor-research-market-state-human.txt
./target/debug/ict-engine factor-backtest ... --human > $BASE/factor-backtest-market-state-human.txt
rg "Market State:" $BASE/factor-*-market-state-human.txt
```

Expected evidence example:
- `market_state_primary_regime=RangeConsolidation`
- `market_state_secondary_regime=WideRange`
- `market_state_bbn_market_regime=range`
- `market_state_bbn_liquidity_context=favorable`

## Pitfalls

- Do not stop after adding source fields; prove runtime JSON emits them.
- If JSON already surfaces fields, still check `--human`; consumers need a compact readable line, not just machine keys.
- `cargo test --bin ict-engine <lib-module-test-name>` can compile but run `0 tests`; use `cargo test --lib <filter>` for tests under library modules like `application::reporting`.
- `TrendExpansion` can map to `None` for BBN market regime; output `passthrough` instead of dropping the field.
- Rebuild the binary before CLI smoke; `cargo check` alone is insufficient if running `./target/debug/ict-engine`.
- Dirty worktrees are normal in this repo; only stage touched files.