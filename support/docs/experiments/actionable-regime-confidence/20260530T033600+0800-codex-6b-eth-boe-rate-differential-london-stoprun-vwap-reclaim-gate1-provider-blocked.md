# 6B ETH BoE Rate Differential London Stop-Run VWAP Reclaim Gate 1 Provider Block

created_at: 2026-05-30T03:36:00+0800
terminalized_at: 2026-05-30T03:52:00+0800
owner: codex
agent_name: codex-6b-eth-boe-rate-differential-london-stoprun-vwap-reclaim-gate1
status: terminalized_provider_blocked_no_aq
promotion_allowed: false
trade_usable: false
update_goal: false
same_tree_practical_closure: null

## Scope

Guarded Gate 1 continuation for the prior 6B source-only prep packet. The branch stayed:

```text
FUTURES -> FXFutures -> CME British Pound / 6B -> ETH/full_retained_session -> 1m execution + shifted 5m/15m/30m/1h/4h/1d context -> BoE_FedRateDifferentialTransition -> LondonNYLiquidityStopRun -> VwapReclaimAfterSterlingPolicyShock -> AtrRiskManagedMtfContinuation -> 6b_eth_boe_rate_differential_london_stoprun_vwap_reclaim_v1
```

session_scope: `ETH/full_retained_session`
rth_filter_applied: false
origin_timeframe: `1m`
context_ladder: `5m/15m/30m/1h/4h/1d`

## Files

- Wrapper: `support/docs/experiments/actionable-regime-confidence/scripts/run_ibkr_6b1m_boe_rate_differential_london_stoprun_vwap_reclaim_gate1_v1.py`
- Focused test: `support/docs/experiments/actionable-regime-confidence/scripts/test_ibkr_6b1m_boe_rate_differential_london_stoprun_vwap_reclaim_gate1_identity.py`
- Workdoc: `/tmp/ict-engine-6b-eth-boe-rate-differential-london-stoprun-vwap-reclaim-gate1-20260530T033600+0800/workdoc.md`
- Claim: `/tmp/ict-engine-agent-claims/board-b-factor-refinement/20260530T033600+0800-codex-6b-eth-boe-rate-differential-london-stoprun-vwap-reclaim-gate1.claim`
- Terminal metrics: `/tmp/ict-engine-6b-eth-boe-rate-differential-london-stoprun-vwap-reclaim-gate1-20260530T033600+0800/checks/terminal_metrics.json`

## What Ran

Focused TDD:

```bash
python3 -m unittest support/docs/experiments/actionable-regime-confidence/scripts/test_ibkr_6b1m_boe_rate_differential_london_stoprun_vwap_reclaim_gate1_identity.py -v
```

Result: 8/8 passed after the RED wrapper-missing failure was observed.

Guarded launch command:

```bash
python3 support/docs/experiments/actionable-regime-confidence/scripts/run_ibkr_6b1m_boe_rate_differential_london_stoprun_vwap_reclaim_gate1_v1.py \
  --root /tmp/ict-engine-6b-eth-boe-rate-differential-london-stoprun-vwap-reclaim-gate1-20260530T033600+0800 \
  --timeframes 1m,5m,15m,30m,1h,4h,1d \
  --session-scope ETH/full_retained_session \
  --launch-aq
```

## Terminal Evidence

`provider-status --provider ibkr --agent` exited 0 but reported:

```text
configured_runtime_unhealthy / ibkr_gateway_unreachable
market_data:0/1 ready
```

Every same-turn `fetch_external.py ibkr-historical` probe for broker-side `GBP` / 6B CME futures exited 1 and returned zero rows for:

- `1m`, `7 D`, exact training origin
- `5m`, `1 M`
- `15m`, `1 M`
- `30m`, `1 M`
- `1h`, `1 M`
- `4h`, `1 M`
- `1d`, `6 M`

Representative stderr:

```text
ibkr-historical: no reachable local IBKR API port on 127.0.0.1; probed TWS paper:7497, TWS live:7496, IB Gateway paper:4002, IB Gateway live:4001. Launch TWS/IB Gateway with API enabled or pass --port explicitly.
```

No material files were generated, `08_strategy_py_compile` had no strategies to compile, and no AutoQuant batch, dispatch, rank, Freqtrade, paper/sim, live, Pre-Bayes, BBN, path-ranker, execution tree, feedback update, or policy training ran.

A later same-root rerun was stopped by the wrapper's claim-collision guard because a foreign runtime appeared under `/tmp/ict-engine-eur-eth-donchian-tsmom-volcarry-prep-20260530T005133+0800`. That prevented a relaunch and did not add evidence to the 6B branch.

## Decision

terminal_decision: `provider_blocked_ibkr_gateway_unreachable`

This is not a Gate 1 economic failure and not practical evidence. It is a provider/runtime blocker packet. Future rerun is allowed only after:

- IBKR TWS or Gateway is reachable on one of the standard API ports or an explicit reachable port is passed.
- Compact claim audit and focused process table show no foreign active claim or live factor process.
- Same-turn provider rows are nonzero for `1m` origin and the shifted `5m/15m/30m/1h/4h/1d` context ladder.

Practical flags remain false.
