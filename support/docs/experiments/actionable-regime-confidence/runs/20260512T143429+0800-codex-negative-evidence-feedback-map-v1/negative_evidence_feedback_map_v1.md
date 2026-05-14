# Negative Evidence Feedback Map v1

Root: `docs/experiments/actionable-regime-confidence/runs/20260512T143429+0800-codex-negative-evidence-feedback-map-v1`

Purpose: convert the already-registered Board A negative and partial results into typed feedback that can harden BBN likelihoods, CatBoost/path-ranker labels, execution-tree gates, provider selection, and Auto-Quant search priority without mutating production priors/CPDs.

This is a non-promoting feedback artifact. It does not count any accepted `>=0.95` regime context, does not alter production state, does not relax thresholds, does not make a trade claim, and does not call `update_goal`.

## Source Evidence

- `135257`: long-history ES/NQ TOMAC Auto-Quant measurement. Aggregate `224` trades, `58.03571428571429%` win rate, Sharpe `0.0192368176971445`, profit factor `1.057427255281844`. ES was weak/negative; NQ was stronger but still support-only.
- `140122`: regime/branch win-rate readback from `135257`. `224` exported trade rows and `7` branch summary rows, but not tied to Board A accepted regime labels and not through the full downstream chain.
- `141554`: provider long-span capability matrix. Useful candidates include Binance `BTCUSDT` `1h` full listing and IBKR `SPY` `1h` 5Y. Negative provider signals include yfinance long `1m` rejection, TradingViewRemix/TVR failure, Bybit capped paging, and Kraken capped or short server windows.
- `142321`: bounded NQ sliced downstream chain. Ordered import/prior/trade-ingest/analyze/Pre-Bayes/policy/export/workflow steps exited `0`, but the chain remained fail-closed.
- `141000`: full NQ/ES downstream root was still active at readback and is not counted here.

## Typed Feedback Events

Machine-readable events are in `negative_evidence_feedback_events_v1.jsonl`.

The event types are deliberately separated:

- `auto_quant_edge_shortfall`: updates strategy-family reliability and branch search priority, not Board A acceptance.
- `branch_screening_unqualified`: preserves branch hints but blocks promotion when regime labels or downstream layers are missing.
- `provider_capability_negative`: updates provider/context feasibility and prevents false six-provider authority claims.
- `ordered_chain_calibration_shortfall`: updates BBN/CatBoost/execution-tree calibration targets from a completed chain that still failed Board A gates.
- `inflight_unusable`: prevents active roots from being accidentally promoted or double counted.

## BBN Feedback Contract

Use the events as candidate training/calibration evidence, not as direct production prior overwrite.

Recommended BBN feedback nodes:

- `provider_reliability`: observed rows, time span, cap/failure mode, provider-owned acquisition status.
- `strategy_family_reliability`: TOMAC family edge by symbol and context.
- `regime_posterior_shortfall`: active regime, canonical confidence, max posterior, and distance to `0.95`.
- `bridge_ambiguity`: long/short probability gap and entry-quality ambiguity.
- `ranker_maturity`: mature rows, calibrated path probability presence, lower-bound presence, and runtime selection status.
- `execution_readiness`: `ready`, `actionable`, gate status, readiness score, and selected path probability.

The current strongest negative BBN signal is not "TOMAC never works"; it is narrower:

- TOMAC NQ may be a useful branch-search seed, but ES weakens cross-market generalization.
- The bounded NQ slice can complete the downstream command path, but BBN posterior confidence and path-ranker calibration are far below acceptance.
- Provider capability must be attached to future evidence; otherwise local replay can train/harden models but cannot become release evidence by itself.

## CatBoost / Path-Ranker Feedback Contract

Use these as explicit non-promoting labels:

- `label=0` for `execution_blocked`, `ready=false`, `actionable=false`.
- `label=0` or censored row for absent calibrated path probability or lower bound.
- `censor_reason=ranker_immature` when `mature_rows` is below the training floor.
- `context_weight=low` for local sliced replay without provider matrix coverage.
- `context_weight=provider_candidate` for Binance `BTCUSDT 1h` and IBKR `SPY 1h 5Y` as next acquisition lanes.

## Execution-Tree Feedback Contract

The execution tree should consume these as guardrail hardening:

- If posterior confidence is below `0.95`, keep the candidate at observe/block.
- If calibrated path probability or lower bound is absent, do not turn path probability into execution readiness.
- If provider authority is missing, allow model hardening but block promotion.
- If a run is active or only partially exited, it is `inflight_unusable` until separately classified.

## Next Non-Duplicative Action

Do not run another same-shape TOMAC/local-slice evidence loop. Let `141000` settle, then classify it separately. For a fresh provider-backed packet, prefer either:

- Binance `BTCUSDT 1h` full listing as a public crypto provider lane, or
- IBKR `SPY 1h` 5Y as a tradfi provider lane.

Either lane must still run through Auto-Quant -> filter/Pre-Bayes -> BBN -> CatBoost/path-ranker -> execution tree before it can affect Board A acceptance.

