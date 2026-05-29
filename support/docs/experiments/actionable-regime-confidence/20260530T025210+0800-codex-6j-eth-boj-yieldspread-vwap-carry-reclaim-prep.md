# 6J ETH BoJ Yield-Spread VWAP Carry Reclaim Prep

created_at: 2026-05-30T02:52:10+0800
owner: codex
agent_name: codex-6j-eth-boj-yieldspread-vwap-carry-reclaim-prep
status: terminalized_source_only_no_launch_runtime_blocked
promotion_allowed: false
trade_usable: false
update_goal: false
same_tree_practical_closure: null

## Scope

New prep-only profitability-factor training packet for CME Japanese Yen futures
(`6J`, broker-side `JPY`). It exists because current Board B execution remains
blocked by fresh claims and a foreign NQ regression-channel prescreen runtime.

No provider fetch, IBKR historical query, AutoQuant, Freqtrade, paper, sim,
live, lifecycle, or local backtest was launched for this packet.

## Evidence Surfaces

- `/tmp` workdoc: `/tmp/ict-engine-6j-eth-boj-yieldspread-vwap-carry-reclaim-prep-20260530T025210+0800/workdoc.md`
- Claim: `/tmp/ict-engine-agent-claims/board-b-factor-refinement/20260530T025210+0800-codex-6j-eth-boj-yieldspread-vwap-carry-reclaim-prep.claim`
- Cost model: `/tmp/ict-engine-6j-eth-boj-yieldspread-vwap-carry-reclaim-prep-20260530T025210+0800/source_evidence/6j_ibkr_cost_model_20260530T025821+0800.json`
- Terminal metrics: `/tmp/ict-engine-6j-eth-boj-yieldspread-vwap-carry-reclaim-prep-20260530T025210+0800/checks/terminal_metrics.json`
- Terminal summary: `/tmp/ict-engine-6j-eth-boj-yieldspread-vwap-carry-reclaim-prep-20260530T025210+0800/summaries/terminal_summary.json`
- Compact packet: `support/docs/experiments/actionable-regime-confidence/runs/20260530T025210+0800-codex-6j-eth-boj-yieldspread-vwap-carry-reclaim-prep-v1/summaries/prep_packet.md`

## Labels

market: FUTURES
product: FXFutures
symbol: 6J / Japanese Yen futures
broker_symbol: JPY
exchange: CME
provider_target: IBKR historical first, then AutoQuant only if Gate 1 is earned
origin_timeframe: 1m
context_ladder: shifted 5m/15m/30m/1h/4h/1d
session_scope: ETH/full_retained_session
rth_filter_applied: false

## Canonical Branch

```text
BoJFedYieldSpreadShockTransition -> CarryUnwindRiskOffContinuation -> PostTokyoLondonLiquidityFlushVwapReclaim -> AtrRiskManagedMtfContinuation -> 6j_eth_boj_yieldspread_vwap_carry_reclaim_v1
```

factor_id: `6j_eth_boj_yieldspread_vwap_carry_reclaim_v1`

## Duplicate Boundary

Bounded duplicate checks found no active or terminal 6J/JPY/Yen Board B claim,
no `/tmp` top-level 6J/JPY/Yen run root, and no repo markdown packet under this
experiment directory for this branch.

This exact branch is separate from:

- fresh CL/WTI inventory-shock term-structure VWAP reclaim prep claim
- fresh MGC ETH MTF VWAP trend-pullback low-turnover screen claim
- existing 6E/EUR FX futures packets and screens
- NG/HG source-only reserve packets
- NQ regression-channel TOMAC prescreen runtime
- XAU/GC full-session TOMAC terminal packets

Do not reroot this packet into 6E, 6A, 6B, 6C, J7, MJY, FX spot, ETF JPY
exposure, or a generic dollar factor without fresh claim/audit and
instrument-specific cost evidence.

## Profit Hypothesis

Japanese Yen futures may produce ETH/full-session continuation after BoJ/Fed
yield-spread shocks, carry-unwind bursts, or risk-off liquidity flushes. A
future runner should avoid the event bar itself, require a Tokyo or London
liquidity flush plus 1m VWAP reclaim, and demand shifted 5m/15m slope agreement
with 30m/1h momentum. The 4h/1d context should veto stale range drift and
single-session overextension.

Candidate predicates for a future runner:

- Main regime: BoJ/Fed yield-spread shock transition or risk-off carry unwind.
- Entry: post-flush 1m VWAP reclaim with 5m/15m slope recovery.
- Context: 30m/1h impulse agreement; 4h/1d trend or yield-spread sidecar does
  not veto.
- Filters: reject holiday liquidity, raw roll gaps, stale overnight drift, and
  extreme-return sanity failures.
- Exit: ATR bracket or trailing stop plus time stop when 5m/15m slope breaks.

## Source And Cost Status

source_status: ibkr_broker_side_contract_and_fee_capture_pass_cme_direct_contract_page_failed
cost_model_status: verified_ibkr_current_ordinary_outright_source_only

Captured source files under the run root:

- `source_evidence/ibkr_futures_commissions_20260530.html`
- `source_evidence/ibkr_cme_fee_recovery_20260530.html`
- `source_evidence/ibkr_secdef_search_6j_20260530.json`
- `source_evidence/ibkr_secdef_search_jpy_20260530.json`
- `source_evidence/ibkr_contract_details_jpy_fut_20260530.json`
- `source_evidence/ibkr_trsrv_secdef_jpy_fut_20260530.json`
- `source_evidence/cme_6j_contract_specs_20260530.fetch_error.txt`
- `source_evidence/6j_ibkr_cost_model_20260530T025821+0800.json`

Verified IBKR current ordinary outright assumption:

```text
instrument_class=future
strategy_root_symbol=6J
broker_symbol=JPY
market=CME
currency=USD
broker=IBKR
pricing_plan=tiered
account_fee_assumption=non_member_low_volume
contract_multiplier=12500000.0
tick_size=0.0000005
tick_value_usd=6.25
commission_per_contract_per_side=0.85
exchange_fee_per_contract_per_side=1.60
regulatory_fee_per_contract_per_side=0.02
all_in_per_contract_per_side=2.47
all_in_round_turn_per_contract=4.94
slippage_spread_model=separate explicit model required
```

IBKR `6J` search returned `No symbol found`, but `JPY` returned the CME FUT
Japanese yen family. The secdef chain returned 36 standard `ticker=JPY` FUT rows
with the expected multiplier and tick value. Direct CME contract-spec capture
failed from this host with `LibreSSL SSL_connect: SSL_ERROR_SYSCALL`, so this is
broker-side IBKR proof for an IBKR-current ordinary outright assumption, not
direct CME page proof.

## Runtime Blocker

Same-turn compact audit before this packet showed:

```text
status=needs_attention
active_claims=2
valid_active_claims=2
fresh_active_claims_without_live_process=1
fresh_wait_only_active_claims_without_live_process=1
live_factor_processes=0
promotion_allowed_true=0
trade_usable_true=0
same_tree_practical_closure=null
```

Focused process readback also showed an NQ regression-channel signal-quality
prescreen writing under
`/tmp/ict-engine-tomac-regression-channel-r2-slope-breadth-continuation-20260530T003603+0800`.

## Terminal Decision

terminal_status: terminalized_source_only_no_launch_runtime_blocked
terminal_decision: no_launch_due_fresh_claims_and_foreign_nq_runtime
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

This packet is only a future branch seed. It is not Gate 1 evidence and must not
be counted as practical, promotion-allowed, or trade-usable.

## Future Launch Plan

Only after a fresh compact audit and process table show no active/fresh blockers
and no live factor processes, create/adapt a runner with this shape:

```bash
python3 support/docs/experiments/actionable-regime-confidence/scripts/run_ibkr_6j1m_boj_yieldspread_vwap_carry_reclaim_gate1_v1.py \
  --root /tmp/ict-engine-6j-eth-boj-yieldspread-vwap-carry-reclaim-run-<timestamp> \
  --timeframes 1m,5m,15m,30m,1h,4h,1d \
  --session-scope ETH/full_retained_session \
  --launch-aq
```

Required before any promotion:

- Same-turn verified provider rows for 6J/Japanese Yen futures with 1m origin
  and shifted `5m/15m/30m/1h/4h/1d` context.
- ETH/full retained-session coverage proof outside an RTH-only window.
- Contract-month mapping and roll handling.
- Cost survival against the verified IBKR 6J/Japanese Yen all-in model plus a
  separate slippage/spread model.
- AutoQuant Gate 1 and same-root downstream artifacts if economics survive.
- Valid same-tree practical closure before any `promotion_allowed=true`,
  `trade_usable=true`, or `update_goal=true`.
