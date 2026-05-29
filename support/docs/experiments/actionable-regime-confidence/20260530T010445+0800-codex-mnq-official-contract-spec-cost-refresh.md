# MNQ Official Contract Spec Cost Refresh

created_at: 2026-05-30T01:04:45+0800
owner: codex
agent_name: codex-mnq-official-contract-spec-cost-refresh
status: terminalized_cost_model_verified_ibkr_official
coordination_only: true
promotion_allowed: false
trade_usable: false
update_goal: false

## Scope

Low-collision source refresh for MNQ futures contract specification and IBKR
cost-model fields while fresh Board B factor claims block new launches or
takeovers. This packet only verifies source material; it does not modify active
NQ/ES local-screen lanes and does not launch provider, Auto-Quant, paper, sim,
or live runtime.

## Evidence Surfaces

- `/tmp` workdoc: `/tmp/ict-engine-mnq-official-contract-spec-cost-refresh-20260530T010445+0800/workdoc.md`
- Claim: `/tmp/ict-engine-agent-claims/board-b-factor-refinement/20260530T010445+0800-codex-mnq-official-contract-spec-cost-refresh.claim`
- Prior partial reserve: `support/docs/experiments/actionable-regime-confidence/20260530T005012+0800-codex-mnq-cost-model-evidence-reserve.md`
- Terminal metrics: `/tmp/ict-engine-mnq-official-contract-spec-cost-refresh-20260530T010445+0800/checks/terminal_metrics.json`
- Terminal summary: `/tmp/ict-engine-mnq-official-contract-spec-cost-refresh-20260530T010445+0800/summaries/terminal_summary.json`

## Findings

Verified from official IBKR pages fetched in this slice:

- MNQ is listed in the IBKR `Spot-Quoted Futures, E-micro Futures and Futures
  Options` group.
- IBKR execution commission for that group is `USD 0.25/contract` at the visible
  low-volume tier.
- IBKR CME fee recovery lists `Micro E-Mini Futures Products MES, MNQ, M2K,
  VOLQ` with `USD 0.35` exchange fee recovery.
- IBKR CME regulatory fee recovery lists `All Products` at `USD 0.02` for
  non-members and IIP.
- IBKR official Products & Exchanges API chain maps `MNQ` to `Micro E-Mini
  Nasdaq-100 Index - CME`, then to five `FUT` contract conids. The returned FUT
  secdef rows report `listingExchange=CME`, `currency=USD`, `assetClass=FUT`,
  `ticker=MNQ`, `multiplier=2.0`, and tick increment `0.25`.

Component estimate under these assumptions:

```text
contract_multiplier=2.0
tick_size=0.25
tick_value_usd=0.50
commission_per_contract_per_side_usd=0.25
exchange_fee_recovery_per_contract_per_side_usd=0.35
regulatory_fee_recovery_per_contract_per_side_usd=0.02
estimated_all_in_per_contract_per_side_usd=0.62
estimated_all_in_round_turn_per_contract_usd=1.24
```

`tick_value_usd=0.50` is computed from the official IBKR secdef
`multiplier=2.0` and `increment=0.25` fields.

CME official contract-spec and ProductSlate endpoints still failed with TLS EOF
in this environment across curl, Python urllib, and wget. The specification gap
was closed through IBKR official product search and secdef API responses.

## Terminal Decision

decision: terminalized_cost_model_verified_ibkr_official
cost_model_status: verified
reason: fee components, multiplier, and tick increment are verified from official
IBKR pages/API responses for MNQ futures. Direct CME fetch remains unavailable,
but IBKR is the broker/cost model authority for this packet.
next_gate: apply this model in a future MNQ cost-survival run only after fresh
claim/process audit permits runtime work. This packet alone does not establish
promotion or trade usability.

promotion_allowed: false
trade_usable: false
update_goal: false
