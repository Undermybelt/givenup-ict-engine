# TOMAC NQ MSS/CISD Limit Reversal Gate 1 Negative - 2026-05-21

Context: Board B regime-rooted profitability factor training, isolated under
`/tmp/ict-engine-tomac-mss-cisd-limit-reversal-nq-only-20260521T1900`.

Branch family:
`Transition -> MarketStructureEvent -> mss_cisd_limit_reversal -> {mss_cisd_fvg_limit_reversal_v1,mss_cisd_ob_limit_reversal_v1,mss_cisd_rb_limit_reversal_v1}`.

Provider/source:
local TOMAC NQ 1m CSV
`<private-tomac-data-cache>/nq future 2021-2025/glbx-mdp3-20100606-20260403.ohlcv-1m.csv`.

Gate 1 result:

- processed `1,768,555` NQ 1m rows, window `2021-01-03` through `2025-12-31`
- total closed trades: `4,187`
- FVG: `1,205` trades, `1.775` trades/active day, raw `-1.9762%`, `5bps/side=-122.4762%`
- OB: `2,022` trades, `2.280` trades/active day, raw `-0.7183%`, `5bps/side=-202.9183%`
- RB: `960` trades, `1.798` trades/active day, raw `-1.3788%`, `5bps/side=-97.3788%`

Decision:
`observation_only_no_5bps_density_survivor`.
`downstream_allowed=false`, `pre_bayes_allowed=false`, `bbn_allowed=false`,
`catboost_allowed=false`, `execution_tree_allowed=false`,
`promotion_allowed=false`, `trade_usable=false`, `update_goal=false`.

Reusable lesson:
This exact MSS/CISD/FVG-OB-RB limit-reversal shape has acceptable NQ 1m density,
but the edge is raw-negative and collapses badly under 1/2/5bps stress. Do not
send this NQ branch to Auto-Quant downstream, simulated admission, Pre-Bayes,
BBN, CatBoost, or execution tree. If continuing the same market-structure
family, change the economic hypothesis materially toward wider excursion or a
different entry/exit structure before rerunning; otherwise rotate to a different
high-excursion 1m family or symbol.
