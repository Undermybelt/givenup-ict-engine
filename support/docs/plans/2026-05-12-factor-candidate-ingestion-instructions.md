# Factor Candidate Ingestion Instructions

Updated: `2026-05-25`

Purpose: replace the old May 10 append-only factor notes as the default agent
instruction surface. Agents must move useful factor results into repo-local
candidate-pack and admission artifacts, then remove inactive clutter from the
active loop. Do not append another long Markdown-only research block here.

Source logs retained for targeted lookup only:

- `support/docs/plans/2026-05-10-actionable-regime-confidence-todo.md`
- `support/docs/plans/2026-05-10-regime-conditional-auto-quant-profitability-todo.md`

Current compact authorities:

- `support/docs/plans/2026-05-12-board-a-regime-state-current.md`
- `support/docs/plans/2026-05-24-board-b-current.md`
- `support/docs/plans/2026-05-12-board-ab-cleanup-retention-plan.md`

## Operating Contract

This file is an instruction document, not a new evidence sink.

Agents may use the May 10 logs only for exact lookup by root id, heading, hash,
or artifact path. Any useful result found there must be extracted into the
current repo entrypoints below before it can affect training, ranking, or
follow-up work.

Markdown prose is not an active factor. A factor becomes active only when it is
visible through the candidate-pack loop or through a code/runtime path with
tests that prove the behavior.

## Active Entrypoints

Use these repo-local surfaces instead of historical planning prose:

```bash
cargo run -- factor-candidate-packs
cargo run -- factor-candidate-packs --symbol FACTOR_CANDIDATES --state-dir /tmp/ict-engine-candidates
cargo run -- factor-candidate-admission-targets --symbol FACTOR_CANDIDATES --state-dir /tmp/ict-engine-candidates
cargo run -- policy-training-status --symbol FACTOR_CANDIDATES --state-dir /tmp/ict-engine-candidates --output-format human
python3 support/scripts/research/factor_candidate_resolver.py --repo-root . --list-buildable --output-format human
```

Primary repo-local pack root:

```text
support/examples/factor_candidate_packs/curated-auto-quant-v1/
```

Each reusable candidate pack must contain:

- `factor_expression.json`
- `factor_eval_grid_summary.json`
- `transfer_score.json`

Current resolver baseline:

- `buildable_count=7`
- active pack root: `support/examples/factor_candidate_packs/curated-auto-quant-v1`
- admission export surface: `factor-candidate-admission-targets`
- runtime selection remains disabled until promotion gates pass

## Extraction Rule

When an agent finds a useful positive or negative result in old notes,
experiment roots, Auto-Quant output, or provider artifacts, it must classify and
move the result as follows:

- Positive reusable factor: create or update a candidate pack under
  `support/examples/factor_candidate_packs/curated-auto-quant-v1/`, then verify it is
  listed by `factor-candidate-packs`.
- Negative but useful result: preserve it as fail-closed evidence in a compact
  run packet or board status, with the exact reason it blocks promotion.
- Runtime/operator fix: land it in `src/`, `config/`, `support/scripts/`, or tests, not
  only in docs.
- Prose-only idea without artifacts: leave it inactive; do not add it to the
  active factor loop.

The minimum admission path for a factor candidate is:

```text
candidate evidence
-> candidate pack three-file contract with factor_profitability_lifecycle
-> factor-candidate-packs inventory
-> factor-candidate-admission-targets export
-> policy-training-status readback
-> learning/paper/live lifecycle gates
```

## Deletion And Cleanup Rule

Delete or archive inactive clutter only after it has been classified. Do not
delete sole evidence for a live gate.

Allowed cleanup target classes:

- duplicate scratch output already represented by a candidate pack, compact
  evidence packet, provider authority manifest, or admission target;
- prose-only factor notes that have no buildable artifact and no live gate;
- temporary Auto-Quant workspace output after the reusable evidence was moved;
- failed candidates whose negative value is captured as fail-closed evidence.

Blocked cleanup target classes:

- the two May 10 source logs before reference migration and parity pass;
- active roots or owner-protected roots named by Board A/B current docs;
- artifacts that are the only support for a live gate decision;
- source code, configs, or scripts modified by another active owner.

Before any real deletion, satisfy the dry-run conditions in
`support/docs/plans/2026-05-12-board-ab-cleanup-retention-plan.md`:

```text
active_owner=false
referenced_by_current_docs=false
referenced_by_scripts=false
extraction_packet_exists=true
parity_replay_pass=true
local_raw_dependency=false
not_sole_evidence_for_live_gate=true
```

## Promotion Boundary

Candidate-pack visibility is not promotion, and
`learning_admission.status=admitted` is not a trading claim.

A learning-admitted factor may continue training when regime fit, leakage,
provider/retained-real evidence, and positive expectancy after declared
friction are present. It remains observation-only until the later lifecycle
planes pass.

Paper/sim admission is a forward validation surface. IBKR historical data and
paper/sim fills should be used when available for replay, latency, slippage,
and execution-readiness evidence, but simulated fills do not imply live trade
usability.

Live trade usability remains fail-closed until the Board B chain passes:

```text
provider parity or retained-real provider truth
-> sufficient branch/trade density and instrument-aware friction
-> Pre-Bayes/filter
-> BBN learning/calibration
-> CatBoost/path-ranker
-> execution-tree non-Observe decision
-> feedback/update learning
```

If a learning blocker fails, record the candidate as invalid or blocked for
training. If a paper/live blocker fails, preserve it as useful negative or
repair evidence, keep runtime selection disabled, and keep
`promotion_allowed=false`, `trade_usable=false`, and `update_goal=false`.

## Priority Runtime-Evidence Backlog

When the operator asks for stronger factor training, the default answer is not
"write more prose." The target is first-class runtime evidence that can flow
into:

- `Structure`
- `Technicals`
- `SMT`
- `Regime` posterior evidence
- `Plan`
- Pre-Bayes/filter
- BBN
- CatBoost/path-ranker
- execution tree
- feedback/update learning

Default execution order for the next unclaimed factor-training slices:

1. `smt_relationship_resolver`
2. `liquidity_pool_texture`
3. `sweep_quality`
4. `fvg_ifvg_lifecycle`
5. `order_block_variant_classifier`
6. `market_structure_event_classifier`
7. `brooks_price_action_context`
8. `options_dealer_context`

These priorities may be adjusted only when current Board B evidence proves that
the same exact slice is already active, blocked, or decisively negative.

Current operator emphasis inside that order:

- first ship the quartet that most directly upgrades human/runtime read depth:
  `smt_relationship_resolver`, `liquidity_pool_texture`,
  `fvg_ifvg_lifecycle`, and `order_block_variant_classifier`
- `sweep_quality`, `market_structure_event_classifier`,
  `brooks_price_action_context`, and `options_dealer_context` remain in the
  backlog, but should not displace the quartet unless current Board B evidence
  shows the quartet slice is occupied, blocked, or already terminal

## Hard Contract For These Factors

- Zero-config default remains Yahoo/yfinance or other public data. Richer
  providers may be preferred only when the user opts in with provider/profile
  config or explicit provider choice.
- Outputs must be structured JSON/CSV and must carry exact levels such as
  `level`, `high`, `low`, `top`, `bottom`, `entry`, `stop`, `target`, or their
  factor-specific equivalent.
- Missing evidence must fail closed as `null`, `n/a`, `confidence=0`, or an
  explicit `fail_closed_reason`. Do not fabricate levels, pair relationships,
  regime fit, or provider coverage.
- Every factor must expose per-regime statistics for at least
  `trend/range/transition/stress/other`, plus trade count, sample window,
  instrument coverage, and confidence. Aggregate Sharpe alone is not enough.
- Board B still defaults to one factor plus one gate, optionally conditioned on
  one frozen root regime. Do not force every new factor through the full
  downstream chain before Gate 1 says it is worth keeping.
- Promotion to a generic factor still requires enough cross-market evidence.
  A single-market packet may be useful, but it must not be misreported as a
  universal factor.
- Minimum comparison coverage for cross-market factors should include the
  operator's current matrix unless a packet proves a narrower lane:
  `NQ/ES/YM`, `EURUSD/GBPUSD/DXY`, `XAUUSD/XAGUSD/DXY`, and `BTC/ETH`.

## Factor-Specific Contract

### `smt_relationship_resolver`

- SMT is not generic correlation and not relative-strength prose. It is a
  comparable-symbol resolver plus same-event confirmation-failure detector.
- Use the ICT definition, not a looser "who is stronger or weaker" shortcut:
  SMT divergence means two related symbols fail to confirm the same
  swing/liquidity event in the same timeframe and overlapping session.
- Positive relationship rules:
  - `bullish_smt`: base sweeps sell-side or prints a lower low while the
    comparison symbol fails to print the lower low and holds a higher low
  - `bearish_smt`: base sweeps buy-side or prints a higher high while the
    comparison symbol fails to print the higher high and prints a lower high
- Negative relationship rules:
  - normalize the comparison symbol's structure direction first
  - emit both the normalized interpretation and the raw event to avoid inverse
    pair misreads
- `actionable=true` is forbidden when SMT is the only signal.
- Minimum input contract:
  - `base_symbol`
  - `timeframe`
  - candles for `base_symbol`
  - provider universe / available symbols
  - optional user profile or provider hint
  - optional session calendar
- Required comparable-symbol logic:
  - resolve futures peers, CFD proxies, ETF proxies, sector peers, and
    currency/macro drivers from the user symbol plus available provider universe
  - emit `session_leader` when the relationship has a consistent session-first
    driver
  - normalize inverse-correlation structure before applying HH/HL/LH/LL rules
  - emit both normalized and raw provenance for inverse pairs
- Baseline dynamic lookup examples:
  - indices: `NQ -> ES/YM/RTY/QQQ/SPY/DIA/IWM/NAS100/US500/US30/DXY/VIX`
  - index peers: `ES -> NQ/YM/RTY/SPY/QQQ/DIA/VIX/DXY`
  - forex: `EURUSD -> GBPUSD/DXY/EURGBP`
  - metals: `XAUUSD -> XAGUSD/DXY/US10Y/real_yield/GDX`
  - crypto: `BTC -> ETH/SOL/TOTAL/QQQ/DXY`
  - stocks: map to index ETF, sector ETF, top peers, and liquidity/options
    proxies when available
- Required fail-closed gates:
  - unstable recent relationship
  - non-overlapping session
  - mismatched timeframe
  - missing data
- Minimum output schema must include:
  - `base_symbol`
  - `comparison_symbol`
  - `relationship_type: positive | negative | uncertain`
  - `relationship_confidence`
  - `timeframe`
  - `session`
  - `driver_category`
  - `session_leader`
  - `smt_signal: bullish_smt | bearish_smt | none`
  - `base_swing_type`
  - `base_level`
  - `comparison_swing_type`
  - `comparison_level`
  - `raw_comparison_swing_type`
  - `raw_comparison_level`
  - `swept_side`
  - `normalized_for_inverse_correlation`
  - `near_pd_array`
  - `pd_array_type`
  - `mss_or_cisd_confirmed`
  - `displacement_confirmed`
  - `confidence`
  - `fail_closed_reason`
- Required fields include `base_level`, `comparison_level`,
  `relationship_type`, `relationship_confidence`,
  `normalized_for_inverse_correlation`, `swept_side`,
  `mss_or_cisd_confirmed`, `displacement_confirmed`, and
  `fail_closed_reason`.
- Minimum provider-backed coverage target before generic promotion:
  `NQ/ES/YM`, `EURUSD/GBPUSD/DXY`, `XAUUSD/XAGUSD/DXY`, and `BTC/ETH`.

### `liquidity_pool_texture`

- Train the pool, not only the sweep. Emit whether the pool is `smooth`,
  `jagged`, or mixed, with exact pool bounds and touch geometry.
- Required fields include `level`, `high`, `low`, `touch_count`,
  `spacing_consistency`, `clean_sweep_likelihood`, `confidence`, and
  `fail_closed_reason`.
- A runtime-only texture label is not enough for Board B promotion; Gate 1
  still needs a rooted packet with realized outcomes or explicit useful
  negative evidence.

### `sweep_quality`

- Distinguish true sweep, failed break, continuation sweep, and stop-run then
  reversal.
- Required fields include `sweep_level`, `wick_body_ratio`,
  `reclaim_speed_bars`, `continuation_vs_reversal`, `confidence`, and
  `fail_closed_reason`.
- `sweep_quality` should remain coupled to pool context, structure transition,
  or PDA ordering rather than acting as a free-floating trigger.

### `fvg_ifvg_lifecycle`

- Treat lifecycle state as first-class evidence: `open`, `partial_fill`,
  `full_fill`, `inverted`, `respected`, `failed`.
- Required fields include `top`, `bottom`, `midpoint`, `fill_ratio`,
  `inverted`, `respected`, `confidence`, and `fail_closed_reason`.
- A negative standalone packet is still useful context evidence. Do not rerun
  the same negative FVG slice and pretend it is a new promotable seed; change
  the variant, branch, or evidence basis first.

### `order_block_variant_classifier`

- Required variants include `order_block`, `mitigation_block`,
  `breaker_block`, `rejection_block`, and `failed_mitigation`.
- Required fields include `high`, `low`, `midpoint`, `validation_state`,
  `mitigation_count`, `breaker_confirmed`, `rejection_confirmed`,
  `confidence`, and `fail_closed_reason`.
- Rows missing the exact block bounds or the confirming structure/displacement
  context must fail closed.

### `market_structure_event_classifier`

- Normalize the structure vocabulary across `swing_high`, `swing_low`, `BOS`,
  `CHoCH`, `MSS`, and `CISD`.
- Required fields include `event_type`, `direction`, `level`, `candle_time`,
  `source_timeframe`, `confidence`, and `invalidation_level`.
- Do not keep structure rows as generic unlabeled targets if the branch claims
  a factor-specific path. Branch-path survival is part of the contract.

### `brooks_price_action_context`

- Context fields must stay price-action specific: `trend_day`,
  `trading_range`, `second_entry`, `wedge`, `failed_breakout`,
  `micro_channel`, `climax_reversal`.
- Required fields include `brooks_context`, `direction`, `trigger_level`,
  `invalidation_level`, `confidence`, and `regime_conditioned_win_rate`.

### `options_dealer_context`

- Use it only where options evidence is real. Otherwise fail closed.
- Required fields include `gamma_wall`, `put_wall`, `call_wall`,
  `dealer_gamma_regime`, `expected_pin_or_acceleration`, `confidence`, and
  `evidence_source`.

## Current Repo-State Adjustment

Cross-check `support/docs/plans/2026-05-23-board-b-current.md`
before starting a slice. Current evidence already changes the practical meaning
of some priorities:

- `smt_relationship_resolver`: first-class runtime schema already exists; the
  next useful slice is stronger pair-admission evidence, inverse-normalization
  parity, or real per-regime strict rows, not another schema-only rewrite.
- `liquidity_pool_texture`: runtime fields, an observation-only candidate
  pack, one rooted directional XLF outcome bridge, and an explicit-root native
  carry on the existing XLF retained pack already exist; the next useful slice
  is support expansion on that existing pack until it stops being
  `single_market_only` / `anecdotal`, not another first bridge, sibling-pack
  creation, or sideways observation packet.
- `fvg_ifvg_lifecycle`: one standalone provider-backed packet is already a
  decisive negative classifier; treat it as context evidence unless a materially
  different variant or branch is being tested.
- `order_block_variant_classifier`: current packet is incubate/context-only;
  next useful work is explicit breaker/rejection confirmation plus broader
  instrument coverage.
- `market_structure_event_classifier`: Gate 1 is already positive; the next gap
  is live branch-path propagation and structural-feedback survival, not
  retraining the same generic packet.
- `brooks_price_action_context`: schema/material preflight exists; next useful
  work is provider-backed rows with trigger/invalidation levels and per-regime
  statistics.
- `options_dealer_context`: still needs provider-backed evidence and zero-config
  fallback discipline.

## Consumer Mapping Requirement

Each retained factor packet should declare how its fields map into:

- `Structure`
- `Technicals`
- `SMT`
- `Regime` posterior evidence
- execution-tree features
- feedback/update learning fields

If a factor cannot yet map to those consumers, keep it as observation-only or
fail-closed evidence and do not overclaim downstream readiness.

Minimum mapping discipline for the current priority set:

- `smt_relationship_resolver`
  - `SMT`: comparable-symbol universe, relationship type/confidence,
    normalized divergence event, liquidity side, PDA/MSS/CISD confirmation
  - `Regime`: confirmation-only context weight, never standalone regime closure
  - execution tree: same-session confirmation and post-sweep confirmation fields
  - feedback/update: per-regime labeled SMT outcomes by pair family
- `liquidity_pool_texture`
  - `Structure`: pool side, pool bounds, touch geometry, smooth/jagged texture
  - `Regime`: pool behavior inside `range/transition/stress`
  - execution tree: clean-sweep likelihood and trap-risk features
- `sweep_quality`
  - `Structure`: sweep level, wick/body shape, reclaim speed,
    continuation-versus-reversal state
  - execution tree: stop-run versus continuation bias
  - feedback/update: realized outcome labels after sweep events
- `fvg_ifvg_lifecycle`
  - `Structure`: gap bounds, fill ratio, inversion direction, respect/failure state
  - `Plan`: PDA target / mitigation context
  - execution tree: continuation-versus-failure lifecycle features
- `order_block_variant_classifier`
  - `Structure`: block bounds, variant, validation state,
    mitigation/breaker/rejection flags
  - execution tree: PDA support / invalidation context
  - feedback/update: variant-conditioned realized outcomes
- `market_structure_event_classifier`
  - `Structure`: normalized `swing/BOS/CHoCH/MSS/CISD` event stream
  - `Regime`: event-conditioned transition evidence
  - execution tree: branch-path features keyed to event direction and level

## Runtime Owner Map For The Next Slice

Before claiming a runtime implementation slice, start from these current owner
files instead of inventing new parallel carriers:

- SMT resolver + human/runtime schema:
  - `src/analyze/smt_correlation_section.rs`
  - `src/application/reporting/analyze_output.rs`
  - `src/analyze/human_output.rs`
- Factor-side SMT scoring:
  - `src/factor_lab/factor_definition.rs`
  - `src/application/belief/pipeline_shared.rs`
- Runtime evidence carriers:
  - `src/analyze_shared.rs`
  - `src/state/types.rs`
  - `src/state/persistence.rs`
- Structure / PDA primitives already in-tree:
  - `src/ict/mss.rs`
  - `src/ict/cisd.rs`
  - `src/ict/bos_choch.rs`
  - `src/ict/ob.rs`
  - `src/pda_timeline/builder.rs`
  - `src/pda_timeline/setups.rs`
- Existing observation-pattern reference:
  - `support/scripts/research/liquidity_pool_texture_observation_packet.py`

If a proposed slice cannot name its owner files from this map, it is probably
still prose-level and should not be treated as an active runtime-evidence task.

## Factor-Training Prompt Contract

When an agent is asked to train these factors, the prompt should preserve these
operator rules:

- the goal is runtime-consumable structured factors, not explanatory prose
- each factor should land as one isolated training or strategy file with one
  schema and one fail-closed gate story
- outputs must stay JSON/CSV-first, carry exact price levels, and include
  per-regime win rate, trade count, sample window, instrument coverage, and
  confidence
- zero-config must remain public-data friendly; richer providers are opt-in
- branch-path and consumer mapping must be explicit for `Structure`,
  `Technicals`, `SMT`, `Regime`, execution-tree features, and
  feedback/update learning
- SMT must dynamically resolve comparable symbols from the user symbol and the
  available provider universe. Do not reduce it back to a fixed static pair
  table or to relative-strength prose.
- insufficient sample size, low trade count, unstable cross-market behavior, or
  missing evidence must stay fail-closed instead of being misreported as
  trade-ready

## Required Closeout For Any Agent Slice

Every agent slice touching factor candidates must close with evidence for each
applicable item:

- candidate pack path added, updated, or intentionally left unchanged;
- stale factor notes, scratch output, or old references classified as keep,
  archive, delete-later, or deletion-blocked;
- `factor-candidate-packs` output checked;
- `factor-candidate-admission-targets` checked when the active pack set changes;
- `policy-training-status` checked when admission artifacts are written;
- tests or verifier commands listed with pass/fail status;
- explicit statement that no new dependency on the May 10 logs was introduced.

If the slice cannot satisfy these items, it is incomplete and must not mark the
goal complete.
