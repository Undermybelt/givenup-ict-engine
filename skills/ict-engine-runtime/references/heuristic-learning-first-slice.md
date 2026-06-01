# Heuristic Learning First Slice: Triple Barrier + Payoff Shape

Use when implementing the first heuristic-learning gate for `ict-engine`: prove whether a candidate has real trade value before regime/BBN/path-ranking work.

## Trigger

User asks to start with:

```text
labeling_triple_barrier.py + factor_payoff_shape_report.py
```

or asks to "钉死候选是否真的有交易价值".

## Files added in the reference implementation

```text
scripts/research/labeling_triple_barrier.py
scripts/research/factor_payoff_shape_report.py
scripts/research/tests/test_labeling_triple_barrier.py
scripts/research/tests/test_factor_payoff_shape_report.py
```

## TDD path used

1. Write tests first for missing modules.
2. Run:

```bash
python3 -m unittest scripts/research/tests/test_labeling_triple_barrier.py scripts/research/tests/test_factor_payoff_shape_report.py
```

Expected RED: `ModuleNotFoundError` for both modules.

3. Implement minimal scripts.
4. Fix logic bugs found by tests:
   - short stop-loss exit price must be `entry * (1 - side * sl_mult)`, not `entry * (1 + side * sl_mult)`.
   - payoff classification should prefer `trend_convexity` before generic `high_hit_rate_positive_skew` when `avg_win > 1.5 * abs(avg_loss)`.
   - `thin_density` should not be a hard reject for early probe reports; hard rejects are `under_trades`, `cost_blind_negative_edge`, `negative_edge`.
5. Add CLI smoke tests.
6. Run full research regression:

```bash
python3 -m unittest discover -s scripts/research/tests -p 'test_*.py'
```

Observed reference result: `Ran 28 tests ... OK`.

## Triple Barrier behavior

Input rows are OHLCV-like dicts with optional `side`:

```text
side = 1  -> long entry
side = -1 -> short entry
side = 0  -> no event
```

Outputs per non-zero side event:

```text
barrier_hit: take_profit | stop_loss | vertical
realized_R
mfe
mae
time_to_hit
meta_label
entry/exit index and timestamp
```

Conservative intrabar rule:

```text
If take-profit and stop-loss are both touched in one bar, stop_loss wins.
```

`realized_R` is net directional return divided by stop distance:

```text
gross_return = side * ((exit_price - entry_price) / entry_price)
net_return = gross_return - cost_bps / 10000
realized_R = net_return / sl_mult
meta_label = 1 if realized_R > 0 else 0
```

## Payoff-shape report behavior

Input trades can contain either:

```text
realized_R
```

or:

```text
gross_R + cost_R
```

Report fields:

```text
trade_count
nb_trials
gross_return_R
cost_total_R
net_return_R
hit_rate
avg_win
avg_loss
win_loss_ratio
sharpe
max_drawdown_R
skew
kurtosis
tail_loss_p95
payoff_shape
failure_tags
promotion_gate
```

Initial payoff shapes:

```text
trend_convexity
high_hit_rate_positive_skew
mean_reversion_snapback
carry_tail_risk
mixed
empty
```

Initial hard rejection tags:

```text
under_trades
cost_blind_negative_edge
negative_edge
```

`thin_density` is advisory/probe-stage, not immediate hard reject.

## Zero-config payoff pipeline

Second slice adds a consumer-friendly wrapper:

```text
scripts/research/heuristic_payoff_pipeline.py
scripts/research/tests/test_heuristic_payoff_pipeline.py
docs/plans/2026-05-09-heuristic-payoff-handoff-todo.md
```

Use it when the user asks for zero-config, token-friendly, non-polluting, hot-pluggable payoff truth artifacts.

Default behavior:
- requires only `--input-csv`, `--output-dir`, `--symbol`, `--candidate-id`
- writes only under caller-selected `--output-dir`
- emits compact consumer artifacts:
  - `labels.jsonl`
  - `payoff_report.json`
  - `handoff_summary.json`
- supports optional `--profile-json` to override barriers/costs/auxiliary fields
- supports profile disable: `{"enabled": false}` returns a skipped summary rather than mutating downstream state

User-specific default auxiliary fields for NQ/VRP work:

```text
qqq_hv_level
nq_vs_200d_pct
vix3m_level
qqq_hv_pct_rank_252
vvix_over_vix
```

Example:

```bash
python3 scripts/research/heuristic_payoff_pipeline.py \
  --input-csv /tmp/events.csv \
  --output-dir /tmp/ict-hl/NQ/demo/payoff \
  --symbol NQ \
  --candidate-id demo
```

Hot-plug profile example:

```json
{
  "profile_id": "tomac-nq-vrp",
  "pt_mult": 0.015,
  "sl_mult": 0.01,
  "max_holding_bars": 16,
  "cost_bps": 5,
  "auxiliary_fields": ["vvix_over_vix", "vix3m_level"],
  "enabled": true
}
```

## DSR/PSR guard

`factor_payoff_shape_report.py` now includes probabilistic and deflated Sharpe fields:

```text
psr
dsr
deflated_sharpe_benchmark
effective_trials
effective_sample_size
```

Use these as a guard against raw high-Sharpe hallucination. Treat raw `sharpe` as descriptive only; promotion logic should eventually require OOS/DSR/PBO evidence. Current formula is a lightweight no-dependency approximation suitable for sidecar research scripts.

## Payoff -> path-ranker target / BBN gate

Third slice connects payoff truth to downstream consumers without touching Rust runtime:

```text
scripts/research/payoff_to_path_ranker_target.py
scripts/research/tests/test_payoff_to_path_ranker_target.py
docs/plans/2026-05-09-payoff-to-path-ranker-handoff-todo.md
```

Use it when the user asks to route `reject/probe/promote + dsr/psr` into path ranking or to ensure regime/BBN only consume viable candidates.

Behavior:
- `probe` / `promote` payoff reports produce:
  - `path_ranker_target.csv`
  - `path_ranker_target.jsonl`
  - `bbn_gate.json`
  - `path_ranker_handoff_summary.json`
- `reject` payoff reports do NOT produce path-ranker targets.
- `reject` writes only:
  - `failure_memory.jsonl`
  - `bbn_gate.json`
  - `path_ranker_handoff_summary.json`
- `bbn_gate.json` is the explicit consumer contract:
  - `consume_by_regime_bbn: true` only for `probe` / `promote`
  - `consume_by_regime_bbn: false` for `reject`

The zero-config payoff pipeline should call this exporter after writing `labels.jsonl` and `payoff_report.json`, using the same isolated output dir. Do not write repo-root state.

Default path-ranker row fields include:

```text
schema_version
symbol
candidate_id
entry_index
entry_timestamp
side
realized_R
mfe
mae
time_to_hit
meta_label
calibrated_label
pending_reward_state
payoff_gate
dsr
psr
sharpe
payoff_shape
bbn_consume
qqq_hv_level
nq_vs_200d_pct
vix3m_level
qqq_hv_pct_rank_252
vvix_over_vix
```

`pending_reward_state` mapping:

```text
meta_label == 1 -> matured_success
meta_label == 0 -> matured_failure
```

CLI:

```bash
python3 scripts/research/payoff_to_path_ranker_target.py \
  --labels-jsonl /tmp/labels.jsonl \
  --payoff-report-json /tmp/payoff_report.json \
  --output-dir /tmp/ict-hl/NQ/demo/path_ranker \
  --symbol NQ
```

TDD sequence used:

```bash
python3 -m unittest scripts/research/tests/test_payoff_to_path_ranker_target.py
# RED: ModuleNotFoundError: No module named 'payoff_to_path_ranker_target'
python3 -m unittest scripts/research/tests/test_payoff_to_path_ranker_target.py scripts/research/tests/test_heuristic_payoff_pipeline.py
python3 -m unittest discover -s scripts/research/tests -p 'test_*.py'
```

Observed final reference result after this slice: `Ran 33 tests ... OK`.

Pitfalls:
- Do not let rejected candidates leak into regime/BBN/path-ranker consumers; they are failure-memory only.
- Do not require Rust runtime changes for this slice; the sidecar artifact contract is sufficient for consumer usability.
- Preserve user-specific auxiliary fields by default, but keep them hot-pluggable through profile/CLI field selection.
- If the target CSV has no rows, check `payoff_gate` first before debugging path-ranker training.

## CLI surfaces

Triple barrier:

```bash
python3 scripts/research/labeling_triple_barrier.py \
  --input-csv events.csv \
  --output-jsonl labels.jsonl \
  --pt-mult 0.02 \
  --sl-mult 0.01 \
  --max-holding-bars 16 \
  --cost-bps 1.0
```

Payoff report:

```bash
python3 scripts/research/factor_payoff_shape_report.py \
  --candidate-id <ID> \
  --trades-jsonl labels.jsonl \
  --output-json payoff_shape.json \
  --nb-trials <N>
```

## Pitfalls

- Do not let tests only cover longs; shorts catch the stop-price sign bug.
- Do not treat `thin_density` as a hard reject during early research slices.
- Do not let raw Sharpe alone promote a candidate; this first slice is a gate, not final validation. Later add DSR/PBO/OOS.
- Do not assume intrabar path ordering from OHLC. Use conservative stop-first unless tick data exists.
- Keep scripts in `scripts/research/` sidecar unless runtime closure proves they must move into Rust.
