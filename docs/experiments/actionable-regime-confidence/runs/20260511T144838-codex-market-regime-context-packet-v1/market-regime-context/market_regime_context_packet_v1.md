# Market Regime Context Packet v1

Run id: `20260511T144838+0800-codex-market-regime-context-packet-v1`.

## Decision

- Gate result: `market_regime_context_packet_v1_price_roots4_context_ready_full_goal_still_blocked`
- Roots context-ready: `Bull, Bear, Sideways, Crisis`
- Scope: `market_regime_context`, not ticker-specific signal and not trade execution.
- Direct Manipulation gate: `partial_blocked`; route remains matched direct rows.
- Full objective achieved: `false`; `update_goal` must remain false.
- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; trade usable: `false`.

## Root Packets

| Root | Ready | Layer count | LCB floor | Layers |
|---|---:|---:|---:|---|
| Bull | true | 5 | 0.9797225384 | 1h_exact_source_panel_context, 1mo_source_consensus_context, 1w_source_consensus_context, daily_parent_root_factor, intraday_parent_day_context_attachment |
| Bear | true | 5 | 0.963920242 | 1h_exact_source_panel_context, 1mo_source_consensus_context, 1w_source_consensus_context, daily_parent_root_factor, intraday_parent_day_context_attachment |
| Sideways | true | 5 | 0.9529358324 | 1h_exact_source_panel_context, 1mo_source_consensus_context, 1w_source_consensus_context, daily_parent_root_factor, intraday_parent_day_context_attachment |
| Crisis | true | 4 | 0.9619059575 | 1h_exact_source_panel_context, 1mo_source_consensus_context, 1w_source_consensus_context, daily_parent_root_factor |

## Consumer Contract

- Downstream consumers may use this packet as regime context for gating, BBN evidence, path ranking, sizing, suppression, and audit fields.
- Downstream consumers must not use it as a ticker-specific alpha, intraday transition timer, direct Manipulation label, or full-cycle/full-species completion claim.

## Artifacts

- JSON: `docs/experiments/actionable-regime-confidence/runs/20260511T144838-codex-market-regime-context-packet-v1/market-regime-context/market_regime_context_packet_v1.json`
- Layers CSV: `docs/experiments/actionable-regime-confidence/runs/20260511T144838-codex-market-regime-context-packet-v1/market-regime-context/market_regime_context_packet_v1_layers.csv`
- Consumer contract CSV: `docs/experiments/actionable-regime-confidence/runs/20260511T144838-codex-market-regime-context-packet-v1/market-regime-context/market_regime_context_packet_v1_consumer_contract.csv`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260511T144838-codex-market-regime-context-packet-v1/checks/market_regime_context_packet_v1_assertions.out`
