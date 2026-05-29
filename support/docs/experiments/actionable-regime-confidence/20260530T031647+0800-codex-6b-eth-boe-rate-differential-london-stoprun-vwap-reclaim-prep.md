# 6B ETH BoE Rate Differential London Stop-Run VWAP Reclaim Prep

created_at: 2026-05-30T03:16:47+0800
owner: codex
agent_name: codex-6b-eth-boe-rate-differential-london-stoprun-vwap-reclaim-prep
status: terminalized_source_only_no_launch_runtime_blocked
promotion_allowed: false
trade_usable: false
update_goal: false
same_tree_practical_closure: null

## Scope

Source-only profitability-factor training packet for CME British Pound futures
(`6B`, broker-side `GBP`). Current Board B execution was blocked by a fresh
active ZS source/cost reserve claim, so this packet does not launch provider,
IBKR historical, AutoQuant, Freqtrade, paper, simulated, live, lifecycle, or
local backtest work.

## Evidence Surfaces

- `/tmp` workdoc: `/tmp/ict-engine-6b-eth-boe-rate-differential-london-stoprun-vwap-reclaim-prep-20260530T031647+0800/workdoc.md`
- Claim: `/tmp/ict-engine-agent-claims/board-b-factor-refinement/20260530T031647+0800-codex-6b-eth-boe-rate-differential-london-stoprun-vwap-reclaim-prep.claim`
- Cost model: `/tmp/ict-engine-6b-eth-boe-rate-differential-london-stoprun-vwap-reclaim-prep-20260530T031647+0800/source_evidence/6b_ibkr_cost_model_20260530T031647+0800.json`
- Terminal metrics: `/tmp/ict-engine-6b-eth-boe-rate-differential-london-stoprun-vwap-reclaim-prep-20260530T031647+0800/checks/terminal_metrics.json`
- Terminal summary: `/tmp/ict-engine-6b-eth-boe-rate-differential-london-stoprun-vwap-reclaim-prep-20260530T031647+0800/summaries/terminal_summary.json`
- Compact packet: `support/docs/experiments/actionable-regime-confidence/runs/20260530T031647+0800-codex-6b-eth-boe-rate-differential-london-stoprun-vwap-reclaim-prep-v1/summaries/prep_packet.md`

## Labels

market: FUTURES
product: FXFutures
symbol: 6B / British Pound futures
broker_symbol: GBP
exchange: CME
provider_target: IBKR historical first, then AutoQuant only if Gate 1 is earned
origin_timeframe: 1m
context_ladder: shifted 5m/15m/30m/1h/4h/1d
session_scope: ETH/full_retained_session
rth_filter_applied: false

## Canonical Branch

```text
BoE_FedRateDifferentialTransition -> LondonNYLiquidityStopRun -> VwapReclaimAfterSterlingPolicyShock -> AtrRiskManagedMtfContinuation -> 6b_eth_boe_rate_differential_london_stoprun_vwap_reclaim_v1
```

factor_id: `6b_eth_boe_rate_differential_london_stoprun_vwap_reclaim_v1`

## Duplicate Boundary

Targeted duplicate checks over `/tmp` Board B claims and
`support/docs/experiments/actionable-regime-confidence` found no exact
6B/GBP/sterling/BoE factor branch. This packet is separate from active or recent
ZS soybean, NQ, 6J/JPY, 6E/EUR, Treasury, metals, energy, VIX/VRP,
options-pressure, and TOMAC lanes. It is also not a reroot of the earlier 6J
packet; British Pound futures require their own contract, cost, data, and
policy sidecar evidence.

## Profit Hypothesis

British Pound futures may produce ETH/full-session continuation or reclaim after
BoE/Fed rate-differential repricing, UK macro surprise windows, and London/New
York liquidity stop-runs. A future runner should avoid the event bar itself,
require a stop-run or displacement followed by 1m VWAP reclaim, and demand
shifted 5m/15m confirmation with 30m/1h impulse agreement. The 4h/1d context
should veto stale range drift, raw roll gaps, and overextended single-session
moves.

Candidate predicates for a future runner:

- Main regime: BoE/Fed rate-differential transition or UK macro repricing.
- Origin: verified 6B/GBP futures 1m execution bars from retained/provider data.
- Context ladder: shifted 5m/15m/30m/1h/4h/1d context only from real rows.
- Entry: post-London or NY stop-run plus 1m VWAP reclaim; skip event bars and roll gaps.
- Confirmation: 5m/15m slope recovery, 30m/1h impulse agreement, 4h/1d trend not opposing.
- Sidecar: BoE/Fed rate-differential or UK-US yield spread only if real timestamped data exists; otherwise unknown and unscored.
- Exit: ATR bracket/trailing stop and time stop when 5m/15m slope breaks.

## Source And Cost Status

source_status: ibkr_broker_side_contract_and_fee_capture_pass_cme_direct_contract_page_failed
cost_model_status: verified_ibkr_current_ordinary_outright_source_only

Captured source files under the run root:

- `source_evidence/ibkr_futures_commissions_20260530.html`
- `source_evidence/ibkr_cme_fee_recovery_20260530.html`
- `source_evidence/ibkr_secdef_search_6b_20260530.json`
- `source_evidence/ibkr_secdef_search_gbp_20260530.json`
- `source_evidence/ibkr_contract_details_gbp_fut_20260530.json`
- `source_evidence/ibkr_trsrv_secdef_gbp_fut_20260530.json`
- `source_evidence/cme_6b_contract_specs_20260530.fetch_error.txt`
- `source_evidence/6b_ibkr_cost_model_20260530T031647+0800.json`

Verified IBKR current ordinary outright assumption:

```text
instrument_class=future
strategy_root_symbol=6B
broker_symbol=GBP
market=CME
currency=USD
broker=IBKR
pricing_plan=tiered
account_fee_assumption=non_member_low_volume
contract_multiplier=62500.0
tick_size=0.0001
tick_value_usd=6.25
commission_per_contract_per_side=0.85
exchange_fee_per_contract_per_side=1.60
regulatory_fee_per_contract_per_side=0.02
all_in_per_contract_per_side=2.47
all_in_round_turn_per_contract=4.94
slippage_spread_model=separate explicit model required
```

IBKR `6B` search returned `No symbol found`, while `GBP` returned the British
pound CME/ICEUS FUT family. IBKR `contract-details` for `underConid=12087797`
returned 42 futures-family conids. IBKR `trsrv/secdef` returned 36 standard CME
`ticker=GBP` FUT rows with multiplier `62500.0` and tick increment `0.0001`.
Direct CME contract-spec capture failed from this host with curl exit `35`, so
this is broker-side IBKR proof for an IBKR-current ordinary outright assumption,
not direct CME page proof.

## Runtime Blocker

Same-turn compact audit before this packet showed:

```text
status=needs_attention
active_claims=1
valid_active_claims=1
fresh_active_claims_without_live_process=1
live_factor_processes=0
promotion_allowed_true=0
trade_usable_true=0
same_tree_practical_closure=null
```

Blocking fresh claim at entry time:

`/tmp/ict-engine-agent-claims/board-b-factor-refinement/20260530T025516+0800-codex-zs-eth-crop-weather-crush-termstructure-reserve.claim`

## Terminal Decision

terminal_status: terminalized_source_only_no_launch_runtime_blocked
terminal_decision: no_launch_due_fresh_active_claims_source_only_packet_preserved
provider_fetch_started: false
ibkr_historical_started: false
autoquant_started: false
freqtrade_started: false
paper_sim_live_started: false
local_backtest_started: false
downstream_allowed: false
promotion_allowed: false
trade_usable: false
update_goal: false
same_tree_practical_closure: null

This packet is only a future branch seed. It is not Gate 1 evidence and must
not be counted as practical, promotion-allowed, or trade-usable.

## Future Launch Plan

Only after a fresh compact audit and process table show no active/fresh blockers
and no live factor processes, create/adapt a runner with this shape:

```bash
python3 support/docs/experiments/actionable-regime-confidence/scripts/run_ibkr_6b1m_boe_rate_differential_london_stoprun_vwap_reclaim_gate1_v1.py \
  --root /tmp/ict-engine-6b-eth-boe-rate-differential-london-stoprun-vwap-reclaim-run-<timestamp> \
  --timeframes 1m,5m,15m,30m,1h,4h,1d \
  --session-scope ETH/full_retained_session \
  --launch-aq
```

Required before any promotion:

- Same-turn verified provider rows for 6B/British Pound futures with 1m origin
  and shifted `5m/15m/30m/1h/4h/1d` context.
- ETH/full retained-session coverage proof outside an RTH-only window.
- Contract-month mapping and roll handling.
- Cost survival against the verified IBKR 6B all-in model plus a separate
  slippage/spread model.
- AutoQuant Gate 1 and same-root downstream artifacts if economics survive.
- Valid same-tree practical closure before any `promotion_allowed=true`,
  `trade_usable=true`, or `update_goal=true`.

## Host Cleanup Note

This slice initially hit `No space left on device` while creating the run root.
Safe cleanup followed the host cleanup route: `uv cache prune` removed `206.1MiB`,
Hermes MCP stderr was tail-preserved and truncated, and two old untagged Hermes
pre-update snapshots were removed. Cleanup manifest:
`/Users/thrill3r/.hermes/logs/disk-cleanup-20260530-032114.json`.
