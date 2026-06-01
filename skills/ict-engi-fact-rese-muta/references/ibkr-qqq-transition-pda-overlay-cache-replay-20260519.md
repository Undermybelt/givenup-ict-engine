# IBKR QQQ transition stability PDA overlay (2026-05-19)

## Context
Continuation after the IBKR-native QQQ micro trend reclaim density base factor:

```text
US -> equity_etf -> QQQ -> 1m -> Trend -> SessionLiquidity -> intraday_micro_trend_reclaim_density -> ibkr_qqq_intraday_micro_trend_reclaim_density_1m_mtf_v1 -> transition_stability_pda_alignment_overlay_v1
```

## Provider status
Fresh IBKR fetches failed because TWS/IB Gateway was not listening on `127.0.0.1:4002`:

```text
ConnectionRefusedError(61, "Connect call failed ('127.0.0.1', 4002)")
```

Per standing workflow, the run continued with retained real IBKR frames from the prior packet and marked:

```text
cache_replay_used=true
fresh_ibkr_live_ready=false
local_cache_replay=true
```

Retained rows used:

```text
1m=6720
5m=4032
15m=1344
30m=672
1h=336
4h=84
1d=251
```

## Gate 1 result
All AQ commands completed and branch fields were preserved:

```text
material_count=21
rank_rows=21
branch_fields_preserved=true
```

But the 1m origin did not survive real-cost stress:

```text
stable_balanced/QQQ/1m: trades=9 raw=+0.18%, 1bps=0.00%, 2bps=-0.18%
stable_dense/QQQ/1m: trades=13 raw=-0.01%, 2bps=-0.53%
pda_quality/QQQ/1m: trades=4 raw=-0.41%, 2bps=-0.57%
origin_survivors_2bps=[]
```

Some sibling lanes were positive, but cannot rescue the 1m root:

```text
stable_balanced/QQQ/1h: trades=6 raw=+0.91%, 2bps=+0.67%, 5bps=+0.31%
stable_balanced/QQQ/5m: trades=18 raw=+1.25%, 2bps=+0.53%
pda_quality/QQQ/5m: trades=11 raw=+0.91%, 2bps=+0.47%
```

Decision:

```text
decision=drop_gate1_no_ibkr_cost_density
pre_bayes_allowed=false
bbn_allowed=false
catboost_allowed=false
execution_tree_allowed=false
promotion_allowed=false
trade_usable=false
```

## Reusable lesson
A same-root transition/PDA overlay may improve 5m/1h sibling cost behavior while destroying the 1m origin edge. Under the user's branch grammar, this is not downstream material for the 1m root. Keep the overlay as negative/suppression evidence, and if the 5m or 1h rows are interesting, restart them under exact sibling timeframe roots instead of flattening them into the 1m branch.

When fresh IBKR is down, retained IBKR cache replay can exercise AQ/material plumbing only. It is not live-ready provider parity and must not open downstream promotion gates.
