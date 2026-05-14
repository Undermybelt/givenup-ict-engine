# Board B 032157 Historical Data Selection Options v1

Scope: selection packet for `B2R_NQ_COST_CRISIS_REPAIR_032157` in `032157/downstream-combined-v1`.

This artifact is not a user selection, does not change the Board B cursor, and does not promote the candidate. It exists to make the current `user_selected_historical_data` blocker concrete for the next loop.

## Current Gate

Current Board B cursor:

- `last_loop_id`: `20260512T034002+0800-codex-board-b-nq-cost-crisis-repair-v3-downstream-combined-v1`
- `hard_gate_result`: `fail:downstream_closed_loop_not_promotable`
- `downstream_consumption`: `execution_tree:fail_closed`
- blocker: Pre-Bayes stayed `observe_only`, path-ranker validation stayed `0/30`, execution stayed `execution_blocked`, and workflow still requires explicit `user_selected_historical_data`.

`analyze_runs.json` records the runtime instruction:

```text
ask-user: Before using historical data for B2R_NQ_COST_CRISIS_REPAIR_032157 again, ask the user which dataset to use.
```

It also marks the research/backtest stages as:

```text
blocked_by:user_selected_historical_data
```

## Candidate Files

| Option | File | Interval | Candles | Window UTC | SHA-256 |
|---|---|---:|---:|---|---|
| `htf` | `docs/experiments/actionable-regime-confidence/runs/20260512T032157-codex-board-b-nq-cost-crisis-repair-v3/downstream-combined-v1/state_combined_v1/B2R_NQ_COST_CRISIS_REPAIR_032157/analyze_nq_htf.json` | `1d` | 260 | `2025-03-03T00:00:00Z` to `2025-12-31T00:00:00Z` | `9c737d7c9e198069ac2b91b8786d015912769e829167047901480d76043f6bb0` |
| `mtf` | `docs/experiments/actionable-regime-confidence/runs/20260512T032157-codex-board-b-nq-cost-crisis-repair-v3/downstream-combined-v1/state_combined_v1/B2R_NQ_COST_CRISIS_REPAIR_032157/analyze_nq_mtf.json` | `1h` | 260 | `2025-10-31T16:00:00Z` to `2025-12-31T20:00:00Z` | `807587969339bb879cd3bc6a72d57d53c84b75b501e1df9875e833c9b6d06752` |
| `ltf` | `docs/experiments/actionable-regime-confidence/runs/20260512T032157-codex-board-b-nq-cost-crisis-repair-v3/downstream-combined-v1/state_combined_v1/B2R_NQ_COST_CRISIS_REPAIR_032157/analyze_nq_ltf.json` | `15m` | 260 | `2025-12-15T12:00:00Z` to `2025-12-31T21:00:00Z` | `d38aea3d620ea56e12af08d11a22929daa076fcd8bdbe5e630f2b059acd244da` |

## Runtime Context Readback

From `analyze_runs.json`:

- multi-timeframe source: explicit frames covering `15m`, `1h`, and `1d`
- missing intervals: `1m`, `5m`, `30m`, and `4h`
- higher-timeframe direction bias: `bullish`
- higher-timeframe alignment score: `0.8691`
- lower-timeframe entry alignment score: `0.9938`
- canonical structural active regime: `range`
- canonical structural confidence: `0.39931857543136917`
- canonical probabilities: `range=0.3528704545302174`, `stress=0.1766356060961594`, `transition=0.23524696968681164`, `trend=0.23524696968681164`
- evidence says `pre_bayes_quality_score=0.399 gating_status=observe_only`
- read-only BBN label set preserves the rooted branch paths for Bull, Bear, Sideways, Crisis, and scoped Manipulation.

## Allowed Next Step

Only after the user explicitly selects one of `htf`, `mtf`, or `ltf`, the next non-promotional command shape is:

```bash
./target/debug/ict-engine factor-research \
  --symbol B2R_NQ_COST_CRISIS_REPAIR_032157 \
  --data <selected analyze_nq_*.json> \
  --state-dir docs/experiments/actionable-regime-confidence/runs/20260512T032157-codex-board-b-nq-cost-crisis-repair-v3/downstream-combined-v1/state_combined_v1
```

Do not treat agent-selected LTF runs as satisfying this gate. After selection, any factor-research or Auto-Quant output still must produce nonzero mature rooted branch observations before Pre-Bayes/filter -> BBN -> CatBoost/path-ranker -> execution tree can move.

## Provider Note

Prior rows already recorded visibility for yfinance, Kraken, IBKR, and TradingViewRemix, but provider visibility is not provider-complete evidence. After a user-selected historical data path produces usable observations, provider status should be refreshed before any new promotion check, and unhealthy IBKR or TradingViewRemix probes must stay visible instead of being counted as usable evidence.
