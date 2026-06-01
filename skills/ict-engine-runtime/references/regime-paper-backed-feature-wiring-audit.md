# Regime paper-backed feature wiring audit

Use when Board A asks whether regime labels are sufficient or whether paper-backed evidence is actually wired through ICT Engine.

## Durable lesson

Papers support a small stable regime taxonomy plus richer evidence/calibration, not endless new regime labels. For ict-engine, treat these as evidence layers that must map into existing fields:

- HMM / hierarchical HMM: state probabilities, label switching controls, persistence, duration survival.
- Change-point / quickest detection: transition hazard and structural-break confirmation.
- Directional Change event sampling: event-time volatility, overshoot ratio, directional-change frequency, trend persistence.
- Realized covariance / correlation regime: cross-asset correlation distance, correlation dispersion, stress/risk-off confirmation.
- Volatility/vol-of-vol: HV, IV, IV/HV, IV rank, VIX/VIX3M/VVIX-style context.

## Audit sequence

1. Claim a Board A feature-wiring lane under `/tmp/ict-engine-agent-claims/board-a/`; do not use repo docs as a lock table.
2. Build or locate a compact run root with `materials/`, `checks/`, `summaries/`.
3. Verify sidecar ingestion first:
   - Build timestamp-joined auxiliary CSV with `qqq_hv_level`, `nq_vs_200d_pct`, `vix3m_level`, `qqq_hv_pct_rank_252`, `vvix_over_vix`.
   - Run `scripts/research/regime_sidecar_pipeline.py --ohlcv ... --auxiliary-evidence ...`.
   - Check `feature_quality_report.json`, `regime_features.csv`, and `regime_consumer_bundle.json` for non-empty coverage and `consumer_hints.user_vrp_nq_context`.
4. Verify mainline propagation separately:
   - `analyze --help` currently shows `--regime-consumer-bundle` and `--apply-regime-bundle-bbn-soft-evidence`, not direct `--auxiliary-evidence`.
   - Scan `workflow_snapshot.json`, `execution_tree_trace.json`, `pre_bayes` output, and `structural_path_ranking_target.csv` for stable machine columns.
5. Verify factor-research propagation:
   - `factor-research --auxiliary-evidence <AuxiliaryMarketEvidence.json> --backend native` should record auxiliary path/symbols and activate `options_hedging` surfaces.
   - Do not assume raw HV/IV scalars became stable downstream columns unless they appear by name in artifacts.
6. Terminal decision format: state `sidecar_wired`, `mainline_wired`, `catboost_target_wired`, `execution_trace_wired`, and `blocked_reason`.

## Known current gap pattern

A successful sidecar auxiliary join does not imply Board A promotion. A past audit showed:
- sidecar auxiliary fields covered `5588/5588` rows and appeared in `consumer_hints.user_vrp_nq_context`;
- sidecar still returned `decision_state=transitional`, `trade_usable=false`, `confidence_95_failed`;
- `structural_path_ranking_target.csv` had no paper-backed feature columns;
- execution trace exposed `transition_hazard` and liquidity, but not HV/IV/VIX/VVIX, change-point, directional-change, or covariance/dispersion fields.

Conclusion for future runs: regime taxonomy can be sufficient while evidence wiring remains incomplete. Next engineering slice should add stable machine columns from sidecar/user auxiliary evidence into BBN soft evidence, structural path-ranking target, and execution-tree trace instead of adding new regime labels.
