# TOMAC MSS/CISD Limit-Reversal NQ Gate 1 (2026-05-21)

Use when continuing local TOMAC futures MSS/CISD/FVG/OB/RB limit-entry factor
training.

## Evidence

- Run root:
  `<ict-engine-repo>/support/docs/experiments/actionable-regime-confidence/runs/20260521T190000+0800-codex-tomac-mss-cisd-limit-reversal-gate1`
- Source: local TOMAC NQ 1m CSV
  `glbx-mdp3-20100606-20260403.ohlcv-1m.csv`
- Completed NQ window: `2021-01-03T23:00:00Z` to `2025-12-31T21:59:00Z`
- Processed retained rows: `1,768,555`
- Branch base: `Transition -> MarketStructureEvent -> mss_cisd_limit_reversal`

## Verdict

Decision: `observation_only_no_5bps_density_survivor`.

Rows had target-like trade frequency but failed 5bps/side cost stress:

- `mss_cisd_fvg_limit_reversal_v1`: `1205` trades, `1.775` trades/active day,
  raw `-1.9762%`, `5bps/side=-122.4762%`.
- `mss_cisd_ob_limit_reversal_v1`: `2022` trades, `2.280` trades/active day,
  raw `-0.7183%`, `5bps/side=-202.9183%`.
- `mss_cisd_rb_limit_reversal_v1`: `960` trades, `1.798` trades/active day,
  raw `-1.3788%`, `5bps/side=-97.3788%`.

Keep downstream gates false:

```text
downstream_allowed=false
pre_bayes_allowed=false
bbn_allowed=false
catboost_allowed=false
execution_tree_allowed=false
promotion_allowed=false
trade_usable=false
update_goal=false
```

## Reusable lesson

Large local TOMAC CSV scans must seek into the requested date window before
parsing rows. A full line-by-line prefilter from a 2010 source start can exceed
agent process limits before reaching a 2025 slice. The run-root script repaired
this with `TOMAC_START`/`TOMAC_END` and `mmap.find(start_day)` before
`csv.DictReader`.

Do not treat this NQ-only negative as full NQ/YM/XAU max-window closure. It is
enough to reject the NQ branch and to prevent downstream promotion of the exact
MSS/CISD FVG/OB/RB limit-entry shape until a variant materially improves
per-trade excursion after real costs. YM and XAU need their own captured terminal
metrics before classification.
