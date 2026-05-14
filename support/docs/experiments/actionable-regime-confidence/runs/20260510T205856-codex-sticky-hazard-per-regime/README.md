# Sticky Hazard Per-Regime Search

Loop id: `20260510T205856+0800-codex-sticky-hazard-per-regime`

Purpose: correct the board-level failure mode where one accepted regime was
treated as sufficient. This run searches only the remaining required regimes
that lacked accepted packets after A8: `TrendExpansion`, `ExtremeStress`, and
`ReversalBrewing`.

Method:
- Uses NQ longspan OHLCV under `/private/tmp/ict-engine-regime-longspan-nq/`.
- Builds current/past-only sticky regime and transition-hazard features.
- Blocks `future_*` and `target_*` predictors.
- Selects candidate thresholds from train split only.
- Uses chronological calibration/test splits for Wilson/ECE/coverage gates.

Result:
- New accepted 95 packets: ['TrendExpansion', 'ExtremeStress', 'ReversalBrewing'].
- Per-regime coverage: `{'SessionLiquidityCoreViable': 'accepted_95_existing', 'TrendExpansion': 'accepted_95_new', 'RangeConsolidation': 'accepted_95_existing', 'ExtremeStress': 'accepted_95_new', 'ReversalBrewing': 'accepted_95_new', 'ThinLiquidity': 'accepted_95_existing_via_ThinLiquidityOffHoursPersistent'}`.
- Trade usable: false. This closes regime-confidence coverage only; execution
  promotion still requires non-observe release and path-specific edge gates.

Artifacts:
- `sticky-hazard/sticky_hazard_per_regime_search.py`
- `sticky-hazard/sticky_hazard_per_regime_report.json`
- `sticky-hazard/sticky_hazard_candidate_rules.csv`
- `evidence_packet_sticky_hazard_per_regime.json`
- `checks/sticky_hazard_assertions.out`
