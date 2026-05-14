# Negative Sweep Pivot v1

Run ID: `20260511T155150+0800-codex-negative-sweep-pivot-v1`

## Decision

The latest negative readiness runs are useful, but they are not the next thing to optimize. The current positive state is already represented by `regime_factor_consumer_map_v1`: all active lanes have a 95% consumer factor, while the full objective remains incomplete.

Gate result: `negative_sweep_pivot_v1=consumer_contract_kept_stop_broad_negative_sweeps`.

## What Changes

- Keep `regime_factor_consumer_map_v1.csv` as the downstream consumer contract.
- Treat spoofing/layering as a missing direct `Manipulation` species expansion, not as proof that the scoped direct `Manipulation` overlay has no accepted factor.
- Stop broad OHLCV/proxy/source sweeps for direct `Manipulation`.
- Reopen Board A only when there is a source-owned row export with positive rows, matched negatives, and a provenance manifest, or when there is an approved exact source-label panel extension.

## External Refresh

The refreshed paper/GitHub/source check supports this pivot:

- `hidden-regime` is useful for HMM posterior, persistence, and temporal-isolation workflow design, but inferred HMM states are not source labels.
- `hmmlearn` remains an HMM implementation reference, not a labeling authority.
- `ruptures` remains useful for change-point boundary features, not a tradable label by itself.
- `Learning the Spoofability of Limit Order Books` supports direct order-flow feature design for spoofing, but it is not a source-owned positive/negative row export.
- `lobflow` is a detector/probe reference; its heuristic detections and synthetic examples cannot be accepted as labels.
- `0xArchive` L4/TP-SL order lifecycle data may be a useful acquisition path for direct order-lifecycle rows and matched negatives if an approved export is available, but it is not a public positive spoofing/layering label source by itself.

## Sources

- https://github.com/hidden-regime/hidden-regime
- https://github.com/hmmlearn/hmmlearn
- https://github.com/deepcharles/ruptures
- https://arxiv.org/abs/2504.15908
- https://pypi.org/project/lobflow/
- https://www.0xarchive.io/blog/l4-tpsl-data/

## Next

Hand off `docs/experiments/actionable-regime-confidence/runs/20260511T153637-codex-regime-factor-consumer-map-v1/regime-factor-map/regime_factor_consumer_map_v1.csv` as the consumer contract. Open a new Board A loop only for source-owned direct rows with matched negatives or an approved exact source-label panel extension.

## Assertions

- Accepted lanes preserved: `true`
- New confidence gate claimed: `false`
- Full objective achieved: `false`
- `update_goal=false`
- Runtime code changed: `false`
- Thresholds relaxed: `false`
- Raw data committed: `false`
- Trade usable: `false`
