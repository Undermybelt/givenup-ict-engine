# TOMAC NQ VWAP Washout Clean-AQ Negative, 2026-06-01

## Context

This was a fee-model rescue audit follow-up for an NQ row that old fixed-cost
logic had likely killed too harshly:

- Prior label: `tomac_nq_vwap_sweep_reclaim_1m_v1`
- Clean-AQ factor id: `tomac_idxfut_clean_vwap_washout_reclaim_1m_v1`
- Branch: `RangeReversion -> VwapStretch -> VwapWashoutReclaim`
- Prior fixed-cost readback: `legacy_fixed_cost_total_profit_pct=-195.11`
- Prior current instrument-cost repricing: `instrument_cost_total_profit_pct=4.36625`
- Prior density: `trade_count=2109`, `trades_per_day=1.355398`
- Prior blocker: session scope unverified.

The continuation created a clean retained-session material packet, then launched
only after compact claim audit cleared.

## Clean Material

- Run root:
  `/tmp/ict-engine-nq-vwap-sweep-reclaim-regime-root-aq-prep-20260601T023452+0800`
- Repo packet:
  `support/docs/experiments/actionable-regime-confidence/20260601T023452+0800-codex-nq-vwap-sweep-reclaim-regime-root-aq-prep-current.md`
- Source CSV:
  `<private-tomac-data-cache>/nq future 2021-2025/glbx-mdp3-20100606-20260403.ohlcv-1m.csv`
- Session scope: `ETH/full_retained_session`
- RTH filter: `false`
- Outside-RTH 1m rows: `1198633`

Clean retained rows:

- `1m`: `1768555`
- `3m`: `589570`
- `5m`: `353742`
- `15m`: `117914`
- `30m`: `59024`
- `1h`: `29519`
- `4h`: `8001`

## AQ Result

Command:

```bash
python3 support/docs/experiments/actionable-regime-confidence/scripts/run_tomac_index_futures_clean_aq_v1.py \
  --root /tmp/ict-engine-nq-vwap-sweep-reclaim-regime-root-aq-prep-20260601T023452+0800/aq \
  --compact-root support/docs/experiments/actionable-regime-confidence/runs/20260601T023452+0800-codex-nq-vwap-sweep-reclaim-regime-root-aq-v1/aq \
  --symbols NQ \
  --timeframes 1m,3m,5m,15m,30m,1h,4h \
  --families vwap_washout_reclaim \
  --aq-smoke-timeframe 1m \
  --aq-symbol-limit 1 \
  --timeout 1800 \
  --reuse-clean
```

Evidence:

- Gate JSON:
  `/tmp/ict-engine-nq-vwap-sweep-reclaim-regime-root-aq-prep-20260601T023452+0800/aq/summaries/autoquant_clean_1m_gate.json`
- Gate rows:
  `/tmp/ict-engine-nq-vwap-sweep-reclaim-regime-root-aq-prep-20260601T023452+0800/aq/summaries/autoquant_clean_1m_rows.csv`
- Terminal summary:
  `/tmp/ict-engine-nq-vwap-sweep-reclaim-regime-root-aq-prep-20260601T023452+0800/aq/summaries/terminal_summary.json`

Result:

- `run_tomac_1m.exit=0`
- `decision=observation_no_autoquant_survivor_yet`
- `rank_rows=2`
- `trade_count=82`
- `trades_per_day=0.045005`
- `total_profit_pct=-0.22`
- `profit_factor=0.9048`
- `gross_edge_bps_per_trade=-0.268293`
- `instrument_cost_total_profit_pct=-0.664167`
- `survives_instrument_cost=false`
- `gate1_survivor=false`
- `promotion_allowed=false`
- `trade_usable=false`
- `update_goal=false`

## Lesson

Fee-model amnesty is only a reason to replay through current clean-AQ with
verified cost and ETH/full-session evidence. It is not a survivor by itself.
When the clean-AQ replay is gross-negative before instrument-cost rescue can
matter, terminalize the factor as no Gate 1 survivor and do not feed it into
Pre-Bayes, BBN, path-ranker, execution-tree, paper/sim/live, or same-tree
closure.

The run also exposed efficiency debt: the generated single-family strategy
computed broad shared feature blocks, including rolling regression /
`np.linalg` work and many fragmented DataFrame inserts. Treat that as wrapper
performance debt for future clean-AQ iteration. It does not change the factor
verdict, but future full-window AQ launches should avoid computing unrelated
family feature blocks when `--families` selects one family.
