# 115700 Selected-History Preflight v1

Run id: `20260512T123211+0800-codex-115700-selected-history-preflight-v1`
Source root: `20260512T121347+0800-codex-115700-enriched-downstream-chain-v1`

## Scope
This is a copied-state, non-promoting preflight for the three recorded historical data paths. It does not mutate the `121347` source state and does not count as user selection/source-control unlock.

## Results
- `1h` data `docs/experiments/actionable-regime-confidence/runs/20260512T121347+0800-codex-115700-enriched-downstream-chain-v1/provider-data-json/BTC_USD-1h.json`
  - exits: factor-research `0`, workflow `0`
  - structural ready/actionable/review: `False` / `False` / `observe`
  - structural gate/readiness: `execution_blocked` / `0.3`
  - latest candidate: `no_trade` direction `Neutral` review `observe`
- `4h` data `docs/experiments/actionable-regime-confidence/runs/20260512T121347+0800-codex-115700-enriched-downstream-chain-v1/provider-data-json/BTC_USD-4h.json`
  - exits: factor-research `0`, workflow `0`
  - structural ready/actionable/review: `False` / `False` / `observe`
  - structural gate/readiness: `execution_blocked` / `0.3`
  - latest candidate: `no_trade` direction `Neutral` review `observe`
- `1d` data `docs/experiments/actionable-regime-confidence/runs/20260512T121347+0800-codex-115700-enriched-downstream-chain-v1/provider-data-json/BTC_USD-1d.json`
  - exits: factor-research `0`, workflow `0`
  - structural ready/actionable/review: `False` / `False` / `observe`
  - structural gate/readiness: `execution_blocked` / `0.3`
  - latest candidate: `no_trade` direction `Neutral` review `observe`

## Decision
- Suggested user-selection default remains `1h`.
- Reason: 1h preserves the current 115700 same-root 1h AQ/runtime surface unless a preflight copy becomes ready/actionable.
- `promotion_allowed=false`.
- `trade_usable=false`.
- `update_goal=false`.

## Artifacts
- JSON: `docs/experiments/actionable-regime-confidence/runs/20260512T123211+0800-codex-115700-selected-history-preflight-v1/115700-selected-history-preflight-v1/115700_selected_history_preflight_v1.json`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260512T123211+0800-codex-115700-selected-history-preflight-v1/checks/115700_selected_history_preflight_v1_assertions.out`
