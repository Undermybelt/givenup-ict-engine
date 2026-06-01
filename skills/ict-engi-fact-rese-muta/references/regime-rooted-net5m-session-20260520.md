# Regime-rooted factor training notes

> 2026-05-24 schema note: `pda_hybrid_alignment` is historical telemetry only unless the current ict-engine source or readback contract still declares it active. Do not use old `pda_hybrid_alignment=true` or `false` lines in this reference as a current hard gate; classify with the live actionable/status/readiness/transition/ranker/mature-row fields.

Session takeaway:
- Treat factor training as a rooted branch tree: market -> product -> symbol -> timeframe -> main regime -> sub-regime(s) -> first profit factor -> later profit factors.
- Keep all later filter / belief network / CatBoost / execution-tree stages on the same rooted branch; do not let an overlay introduce a different root.
- Start from 1m when data allow, then test wider context windows across 5m / 15m / 30m / 1h / 4h / 1d.
- Keep hard gates strict: real-cost density, AQ -> Pre-Bayes -> BBN -> CatBoost -> execution-tree direction agreement, transition_hazard < 0.60, pda_hybrid_alignment=true, execution_readiness >= 0.65.
- If a candidate keeps cost-positive density but breaks PDA alignment or spikes transition hazard, classify it as observation-only rather than relaxing thresholds.

Observed NET 5m examples from this session:
- `pda_sequence_consistency_light_v1`: survived cost stress and retained PDA alignment, but hazard stayed at 0.63049, so it remains observation-only.
- `entry_window_trim_v1`: kept 31 trades and positive 5bps net, but broke PDA alignment and pushed hazard to 0.97944.
- `late_session_hazard_trim_v1`: kept 31 trades and positive 5bps net, but broke PDA alignment and pushed hazard to 0.97918.
- `soft_transition_stability_v1`: weak readiness and hazard near 0.98; observation-only.

Use this reference when extending the regime-rooted factor tree instead of flattening factors into a generic list.
