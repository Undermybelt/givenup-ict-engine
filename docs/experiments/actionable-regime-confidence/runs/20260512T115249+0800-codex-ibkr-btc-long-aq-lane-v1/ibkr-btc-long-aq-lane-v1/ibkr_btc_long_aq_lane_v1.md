# IBKR BTC Long AQ Lane v1

Run id: `20260512T115249+0800-codex-ibkr-btc-long-aq-lane-v1`
Source provider-matrix AQ repair: `20260512T113833+0800-codex-112904-provider-matrix-aq-date-contract-repair-v1`
Provider matrix root: `20260512T112315+0800-codex-board-b-six-provider-btc-matrix-probe-v1`
IBKR precheck root: `20260512T112030+0800-codex-btc-comparable-tvr-ibkr-provider-preflight-v1`

## Scope
This isolated run repairs only the thin IBKR BTC/PAXOS AQ lane by requesting a longer direct IBKR historical series.
It does not edit ict-engine runtime code, does not rewrite earlier run roots, and does not promote a candidate.

## Fetch Readback
- `ibkr-bulk` exit `0`.
- CSV rows `782` from `2026-03-31T20:01:00+00:00` through `2026-05-12T03:00:00+00:00`.
- CSV: `docs/experiments/actionable-regime-confidence/runs/20260512T115249+0800-codex-ibkr-btc-long-aq-lane-v1/derived/ibkr_btc_paxos_long/BTC_1h_midpoint.csv`

## AQ Readback
- Provider `ibkr_paxos_long_midpoint`: rows `782`, compile exit `0`, TOMAC exit `0`.
  - `ProviderCryptoMomentumStateV1`: trades `32`, profit_pct `0.98`, win_rate_pct `37.5`, profit_factor `1.1923059186034541`.
  - `ProviderCryptoPullbackRevertV1`: trades `12`, profit_pct `-0.27`, win_rate_pct `25.0`, profit_factor `0.8524420093984961`.

## Decision
- Gate result: `ibkr_btc_long_aq_lane=ibkr_provider_lane_repaired_but_same_root_downstream_chain_not_rerun`.
- Evidence class: `infrastructure_repair_candidate_ibkr_provider_aq_lane`.
- Mature rooted branch observations added: `44`.
- AQ run success: `1/1`.
- `promotion_allowed=false`.
- `trade_usable=false`.
- `update_goal=false`.

## Artifacts
- JSON: `docs/experiments/actionable-regime-confidence/runs/20260512T115249+0800-codex-ibkr-btc-long-aq-lane-v1/ibkr-btc-long-aq-lane-v1/ibkr_btc_long_aq_lane_v1.json`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260512T115249+0800-codex-ibkr-btc-long-aq-lane-v1/checks/ibkr_btc_long_aq_lane_v1_assertions.out`
- Command output and exits: `docs/experiments/actionable-regime-confidence/runs/20260512T115249+0800-codex-ibkr-btc-long-aq-lane-v1/command-output`, `docs/experiments/actionable-regime-confidence/runs/20260512T115249+0800-codex-ibkr-btc-long-aq-lane-v1/checks`
- AQ workspace: `docs/experiments/actionable-regime-confidence/runs/20260512T115249+0800-codex-ibkr-btc-long-aq-lane-v1/workspace`
