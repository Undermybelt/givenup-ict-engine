# ZN Official Contract Spec Cost Reserve

created_at: 2026-05-30T01:36:19+0800
owner: codex
agent_name: codex-zn-official-contract-spec-cost-reserve
status: terminalized_cost_model_verified_ibkr_official
coordination_only: true
promotion_allowed: false
trade_usable: false
update_goal: false

## Scope

Low-collision waiting-window source reserve for CME/CBOT 10-Year T-Note futures
(`ZN`) contract specification and IBKR cost-model fields. Current compact audit
blocks provider, Auto-Quant, IBKR, paper, sim, live, and lifecycle launches, so
this packet only preserves official source evidence for future cost-survival
work.

It does not touch the active NQ session-breakout/VWAP screen or the fresh YM RTH
inventory/VWAP claim.

## Evidence Surfaces

- `/tmp` workdoc: `/tmp/ict-engine-zn-official-contract-spec-cost-reserve-20260530T013619+0800/workdoc.md`
- Claim: `/tmp/ict-engine-agent-claims/board-b-factor-refinement/20260530T013619+0800-codex-zn-official-contract-spec-cost-reserve.claim`
- Source directory: `/tmp/ict-engine-zn-official-contract-spec-cost-reserve-20260530T013619+0800/sources`
- Terminal metrics: `/tmp/ict-engine-zn-official-contract-spec-cost-reserve-20260530T013619+0800/checks/terminal_metrics.json`
- Terminal summary: `/tmp/ict-engine-zn-official-contract-spec-cost-reserve-20260530T013619+0800/summaries/terminal_summary.json`

## Plan

Use official IBKR futures commissions, CBOT fee recovery, and IBKR Products &
Exchanges contract-spec API evidence. Direct CME pages are preferred if they are
reachable, but IBKR broker-side contract specs are acceptable for an
IBKR-specific cost model when CME fetches fail.

## Terminal Decision

decision: terminalized_cost_model_verified_ibkr_official
cost_model_status: verified_ibkr_official

Verified from official IBKR pages/API responses in this slice:

- `ZN` maps through IBKR Products & Exchanges to `10 Year US Treasury Note -
  CBOT` with `FUT` sections for `JUN26`, `SEP26`, and `DEC26`.
- IBKR `webrest/search/contract-details` returned three futures conids, and
  `trsrv/secdef` returned `FUT` rows with `listingExchange=CBOT`,
  `currency=USD`, `ticker=ZN`, `multiplier=1000.0`, and tick increment
  `0.015625`.
- IBKR futures commission page shows the low-volume USD futures commission tier
  as `USD 0.85/contract`.
- IBKR CBOT fee-recovery page shows `U.S. Treasury Futures ZN, TN` with
  non-member exchange fee recovery `USD 0.80`, and regulatory fee recovery
  `All` non-member/IIP `USD 0.02`.

Component estimate under these assumptions:

```text
contract_multiplier=1000.0
tick_size=0.015625
tick_value_usd=15.625
commission_per_contract_per_side_usd=0.85
exchange_fee_recovery_per_contract_per_side_usd=0.80
regulatory_fee_recovery_per_contract_per_side_usd=0.02
estimated_all_in_per_contract_per_side_usd=1.67
estimated_all_in_round_turn_per_contract_usd=3.34
```

Direct CME contract-spec fetch failed twice from this host with
`curl_exit=35` / LibreSSL SSL syscall. For this packet, IBKR is the broker/cost
authority and provides both fee rows and broker-side FUT contract specs.

This remains coordination/source evidence only. It does not prove Gate 1
survival, promotion, trade usability, or objective completion.

promotion_allowed: false
trade_usable: false
update_goal: false
