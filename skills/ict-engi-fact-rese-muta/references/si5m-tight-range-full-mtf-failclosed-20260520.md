# SI 5m tight-range full-MTF fail-closed

> 2026-05-24 schema note: `pda_hybrid_alignment` is historical telemetry only unless the current ict-engine source or readback contract still declares it active. Do not use old `pda_hybrid_alignment=true` or `false` lines in this reference as a current hard gate; classify with the live actionable/status/readiness/transition/ranker/mature-row fields.

Session: 2026-05-20

Use this when an SI `5m` tight-range branch has already survived Gate 1 costs,
same-root simulated feedback, and a valid `30m/4h` MTF readback, but still fails
execution admission.

## Exact branch

`FUTURES -> precious_metals -> SI -> 5m -> RangeConsolidation -> TightRangeBandExpansionFade -> ibkr_si5m_tight_range_band_expansion_fade_1m_gate1_v1`

## Evidence packet

- Gate 1 root:
  `support/docs/experiments/actionable-regime-confidence/runs/20260520T070456+0800-codex-ibkr-si5m-tight-range-band-expansion-fade-1m-gate1-v1`
- Full-MTF simulated-admission root:
  `support/docs/experiments/actionable-regime-confidence/runs/20260520T070456+0800-codex-ibkr-si5m-tight-range-band-expansion-fade-1m-gate1-v1/simulated-trade-admission-si-5m-tight-range-band-expansion-fade-full-mtf-20260520T134019+0800`
- Metrics:
  `checks/simulated_trade_admission_metrics.json`
- Valid MTF subset manifest:
  `data/cleaned-mtf-analyze-valid/analyze-valid-mtf-subset-manifest.json`

## Result

- Selected Gate 1 row: `dense_fade`, `9` trades, win rate `77.7778%`, raw
  `+2.23%`.
- Same-workspace simulated trades: `9` rows, `7` wins, `2` losses.
- Commands `01_auto_quant_results_import` through `19_policy_after_ranker` all
  exited `0`; no timeouts.
- Runtime consumed `multi_timeframe_source=analyze_explicit_with_auto_fill
  covered_intervals=5m,15m,30m,1h,4h`.
- Valid subset rows: `5m=6047`, `15m=2016`, `30m=1008`, `1h=504`, `4h=136`.
- `1d` existed but had only `27` bars against a `29` bar minimum.
- True `1m` context was unavailable and was not fabricated from retained `5m`
  rows.
- `exact_branch_survived=true`.
- `ranker_validation_ready=true`.
- `path_ranker_score_visible_to_execution_tree=true`.
- `path_ranker_score_used_by_execution_tree=false`.
- `mature_rows=2`.
- `history_mature_rows=10`.
- `execution_candidate_status=no_trade`.
- `execution_readiness=0.2344186944501619`.
- `transition_hazard=0.9679827616849933`.
- `pda_hybrid_alignment=false`.
- `promotion_allowed=false`.
- `trade_usable=false`.
- `update_goal=false`.

## Operating rule

Do not treat full MTF coverage, CatBoost mechanics, or simulated feedback as a
promotion shortcut. This run proves that missing `30m/4h` context was not enough
to clear the hard execution predicates. The next useful same-root repair is one
of:

- fetch true lower-timeframe `1m` provider rows for SI and rerun the rooted
  readback without fabricating `1m` from `5m`;
- repair execution-tree score consumption so the visible path-ranker score is
  actually used;
- repair PDA/transition alignment until `transition_hazard < 0.60`,
  `pda_hybrid_alignment=true`, and `execution_readiness >= 0.65` all hold.

Do not repeat the same simulated-feedback replay, add another light
RVOL/VWAP/liquidity overlay, or lower promotion gates.
