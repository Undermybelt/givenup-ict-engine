# MNQ 1m Compression Breakout VWAP Persistence Simulated Feedback Fail-Closed

> 2026-05-24 schema note: `pda_hybrid_alignment` is historical telemetry only unless the current ict-engine source or readback contract still declares it active. Do not use old `pda_hybrid_alignment=true` or `false` lines in this reference as a current hard gate; classify with the live actionable/status/readiness/transition/ranker/mature-row fields.

## Case
- Date: 2026-05-20
- Source Gate 1 root: `support/docs/experiments/actionable-regime-confidence/runs/20260520T012135+0800-codex-ibkr-mnq1m-compression-breakout-vwap-persistence-transition-guard-7d-gate1-v1`
- Simulated-admission root: `support/docs/experiments/actionable-regime-confidence/runs/20260520T012135+0800-codex-ibkr-mnq1m-compression-breakout-vwap-persistence-transition-guard-7d-gate1-v1/simulated-trade-admission-mnq-1m-compression-breakout-vwap-persistence-transition-guard-20260520T022917+0800`
- Exact branch: `FUTURES -> equity_index -> MNQ -> 1m -> TrendExpansion -> CompressionBreakout -> ibkr_mnq1m_compression_breakout_7d_gate1_v1 -> ibkr_mnq1m_compression_breakout_vwap_persistence_transition_guard_7d_gate1_v1`

## Evidence
- Same Auto-Quant workspace replay exported `6` simulated trades: `5` wins and `1` loss.
- `auto-quant-results-import`, prior init, seed analyze, workflow, Pre-Bayes, target export, simulated-trade ingest, CatBoost train/apply/register, runtime enable, ranker-enabled analyze, workflow, Pre-Bayes, and policy readbacks all exited `0`.
- Exact branch survived and the ranker score was visible to the execution tree.
- Final readback still failed closed: `mature_rows=2`, `history_mature_rows=7`, `execution_candidate_status=no_trade`, `execution_readiness=0.2313332974`, `transition_hazard=0.9110342275`, `pda_hybrid_alignment=false`, `path_ranker_score_used_by_execution_tree=false`.

## Rule
- Same-root simulated-trade admission is a readback/maturity repair probe, not a promotion shortcut.
- If the replay yields only a small feedback sample, classify as observation even when all mechanics exit `0` and CatBoost registers cleanly.
- Do not stack another light VWAP/compression overlay after this shape fails execution predicates. The next useful move is either a denser same-root feedback sample or a different `1m` root that naturally reduces transition hazard and aligns PDA.
- Promotion still requires exact-root cost survival, sufficient mature rows, execution candidate materialization, live transition/readiness gates, and path-ranker score actually used by execution. Do not require retired `pda_hybrid_alignment` unless current source reintroduces it.
