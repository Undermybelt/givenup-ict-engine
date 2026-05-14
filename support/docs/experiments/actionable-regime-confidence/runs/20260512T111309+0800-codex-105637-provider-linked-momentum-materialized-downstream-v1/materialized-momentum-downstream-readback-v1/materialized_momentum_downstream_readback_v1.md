# Materialized Momentum Downstream Readback v1

Run id: `20260512T111309+0800-codex-105637-provider-linked-momentum-materialized-downstream-v1`

Source root: `docs/experiments/actionable-regime-confidence/runs/20260512T105637+0800-codex-provider-linked-aq-provenance-probe-v1`

## Purpose

Repair only the missing downstream real-trades artifact from the already-registered `110627` readback, then rerun the ordered ict-engine downstream surfaces for the same `105637` provider-linked momentum branch.

This is not a new Auto-Quant/provider run. It materializes the pre-existing TOMAC-exported `ProviderCryptoMomentumStateV1.real_trades.jsonl` files from the `105637` provider workspaces into one downstream artifact with the correct Board A symbol and run id.

## Materialization

Input TOMAC trade files:

- `workspace/auto-quant-provider-linked-yfinance/derived/ProviderCryptoMomentumStateV1.real_trades.jsonl`
- `workspace/auto-quant-provider-linked-kraken_public_ccxt/derived/ProviderCryptoMomentumStateV1.real_trades.jsonl`
- `workspace/auto-quant-provider-linked-binance_public_ccxt/derived/ProviderCryptoMomentumStateV1.real_trades.jsonl`
- `workspace/auto-quant-provider-linked-bybit_public_ccxt/derived/ProviderCryptoMomentumStateV1.real_trades.jsonl`

Output artifact:

- `derived/provider_linked_momentum_105637_real_trades.jsonl`

The output contains `7` JSONL rows. The source TOMAC helper had stale `104902` values in `symbol`, `auto_quant_run_id`, and trade id prefixes, so this run normalized them to:

- `symbol=B2R_PROVIDER_LINKED_MOMENTUM_105637`
- `auto_quant_run_id=20260512T105637+0800-codex-provider-linked-aq-provenance-probe-v1`
- provider-qualified `trade_id` and `strategy_mutation_id`

## Command Results

All downstream command exits were `0`.

- `auto-quant-ingest-real-trades --dry-run`: `0`
- `auto-quant-ingest-real-trades --force`: `0`, `trades_applied=7`, `trades_invalid=0`
- `pre-bayes-status --refresh`: `0`
- `policy-training-status` before and after export: `0`
- `export-structural-path-ranking-target`: `0`
- `workflow-status` structural bundle, execution candidate, and full readback: `0`

## Downstream State

The missing-file blocker is repaired, but the branch remains fail-closed.

- Pre-Bayes/filter: still empty; no latest bridge, policy, filtered assignments, gate status, soft evidence, or posterior probabilities.
- Entry-model training: not ready; both entry models have `matched_rows=0`.
- Structural path-ranking target: `rows=2`, `history_rows=2`, `candidate_set_size=2`, `mature_rows=1`, `history_mature_rows=1`.
- Observation validation: `7/30` mature observations, with outcome distribution `loss=4`, `win=3`; still short by `23`.
- CatBoost/path-ranker: `raw_scored_mature=0/30`, `production_validation=0/30`, calibration `not_fitted`, trainer artifact `missing`, runtime selection `disabled`, runtime matches `0`.
- Execution tree: exact structural branch is visible with posterior `0.42857142857142855` and selected path probability `0.7407407407407408`, but `ready=false`, `actionable=false`, `review_status=observe`, and closed-loop branch admission `fail_closed`.

## Decision

Gate: `105637_materialized_momentum_downstream_v1=ingest_repaired_observation_7_of_30_but_pre_bayes_empty_path_ranker_unready_execution_fail_closed_no_promotion`

This root adds downstream observability for `105637`, not promotion. It does not satisfy the six-provider AQ matrix, does not repair TVRemix/IBKR AQ authority, does not create source/control approval, does not create selected-history or canonical merge approval, and does not authorize `update_goal`.

Accepted rows added: `0`. Mature rooted branch observations promoted: `0`. Source/control evidence acquired: `false`. Explicit selected history: `false`. Canonical merge: `false`. Six-provider AQ matrix satisfied: `false`. Selected-data AutoQuant promotion: `false`. Downstream promotion: `false`. Strict full objective: `false`. Trade usable: `false`. Promotion allowed: `false`. `update_goal=false`.

## Next

Do not repeat the missing-artifact rerun for `105637`. The remaining blocker is evidence volume and readiness: at minimum this branch needs enough same-root observations to clear the `30`-row floors, non-empty Pre-Bayes/filter state, a fitted path-ranker/CatBoost artifact, runtime selection enabled, and execution-tree readiness. It still also needs TVR/IBKR provider authority or explicit rescope before any provider-matrix claim.
