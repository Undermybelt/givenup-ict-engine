# M2K 1m PDA consistency floor fail-closed — 2026-05-20

> 2026-05-24 schema note: `pda_hybrid_alignment` is historical telemetry only unless the current ict-engine source or readback contract still declares it active. Do not use old `pda_hybrid_alignment=true` or `false` lines in this reference as a current hard gate; classify with the live actionable/status/readiness/transition/ranker/mature-row fields.

Exact root:
`FUTURES -> equity_index -> M2K -> 1m -> RangeReversion -> LiquiditySweepRejectShort -> ibkr_m2k1m_liquidity_sweep_reject_short_7d_gate1_v1 -> ibkr_m2k1m_liquidity_sweep_reject_short_rvol_pda_guard_pda_consistency_floor_v1`

Source Gate 1 context:
- Real retained IBKR M2K 202606 1m 7D rows.
- Prior direct Freqtrade-style futures probe showed the base RVOL/PDA short can survive cost stress: 19 shorts, 63.1579% win rate, raw +2.60%, 5bps/side +0.70%.
- This is cost-density evidence only, not execution readiness.

Admission replay:
- Full 7D downstream replay timed out at `03_analyze_seed` after Auto-Quant import and prior init completed.
- Diagnostic small replay used retained real last-3000 1m rows with resampled 15m/1h context.
- Small replay preserved the exact rooted branch, so the issue is not path flattening.

Terminal metrics:
- `pre_bayes_gate_status=observe_only`
- `pda_sequence_consistency=0.357`
- `transition_hazard=0.9487`
- `pda_hybrid_alignment=false`
- `execution_readiness=0.1968`
- `path_ranker_score_visible_to_execution_tree=false`
- `path_ranker_score_used_by_execution_tree=false`
- `ranker_validation_ready=false`
- closed loop: `status=fail_closed`, `ready=false`, `actionable=false`, `candidate_status=execution_observe_only`

Decision:
- Observation-only.
- Do not stack more PDA-floor overlays under this exact M2K root.
- Next same-root hypothesis must directly repair PDA/hybrid alignment and path-ranker validation readiness; otherwise rotate to a new 1m dense family/root.

Evidence artifacts:
- `<ict-engine-repo>/support/docs/experiments/actionable-regime-confidence/runs/20260520T100242+0800-codex-ibkr-m2k1m-rvol-pda-consistency-floor-7d-gate1-v1/simulated-trade-admission-m2k-1m-rvol-pda-consistency-floor-20260520T102522+0800/checks/small_replay_terminal_metrics.json`
- `<ict-engine-repo>/support/docs/experiments/actionable-regime-confidence/runs/20260520T100242+0800-codex-ibkr-m2k1m-rvol-pda-consistency-floor-7d-gate1-v1/simulated-trade-admission-m2k-1m-rvol-pda-consistency-floor-20260520T102522+0800/summaries/small_replay_terminal_decision_summary.md`

## Exact-seed bridge and futures rerun addendum

Readback time: `2026-05-20 13:32:29 +0800`.

Updated evidence:

- Exact-seed repair run root: `<ict-engine-repo>/support/docs/experiments/actionable-regime-confidence/runs/20260520T132108+0800-codex-m2k-exact-seed-class-parity-rerun-v1/`.
- Exact-seed metrics: `checks/exact_seed_after_patch_metrics.json`.
- Same-root downstream readback: `<ict-engine-repo>/support/docs/experiments/actionable-regime-confidence/runs/20260520T093302+0800-codex-ibkr-m2k1m-rvol-pda-consistency-floor-7d-gate1-v1/simulated-trade-admission-m2k-1m-rvol-pda-consistency-floor-20260520T132502+0800/`.

Lesson:

- For exact-root futures short seeds, preserving Freqtrade source semantics is necessary but not sufficient. The local Auto-Quant/Tomac probe also needs the seed copied into the `strategies_external` lookup path, `config.tomac.json` set to `trading_mode=futures` and `margin_mode=isolated`, and retained OHLCV bridged into `user_data/data/futures/<PAIR>-<tf>-futures.feather`.
- After that repair, the M2K exact seed preserved source semantics (`timeframe=1m`, `can_short=True`, `enter_short`, `exit_short`, no generic long scaffold) and produced a real cost survivor: `17` shorts, raw `+2.79%`, `1bps=+2.45%`, `2bps=+2.11%`, `5bps=+1.09%`, PF `8.4044`.
- The same-root downstream path still failed closed after all `01-19` commands exited `0`: `execution_candidate_status=no_trade`, `execution_readiness=0.3211044072278747`, `transition_hazard=0.9184975817511946`, `pda_hybrid_alignment=false`, and `path_ranker_score_used_by_execution_tree=false`.

Decision:

- Treat this as a repaired exact-seed cost-survivor and execution-repair lead only. Do not promote, do not lower gates, and do not stack another light liquidity/RVOL/VWAP overlay. The next M2K action must make the execution tree consume the visible ranker score and directly improve PDA/transition alignment.

## Branch-direction repair addendum — 2026-05-22

Fresh rerun:

- Admission run root: `<ict-engine-repo>/support/docs/experiments/actionable-regime-confidence/runs/20260520T191436+0800-codex-ibkr-m2k1m-rvol-pda-consistency-floor-canonical-gate1-v1/simulated-trade-admission-m2k-1m-rvol-pda-consistency-floor-canonical-20260522T005042+0800`.
- Same rooted branch: `RangeReversion -> LiquiditySweepRejectShort -> ibkr_m2k1m_liquidity_sweep_reject_short_7d_gate1_v1 -> ibkr_m2k1m_liquidity_sweep_reject_short_rvol_pda_guard_pda_consistency_floor_v1`.
- Pre-run evidence: rebuilt `.local-artifacts/cargo-target/debug/ict-engine`; branch-direction regression tests passed; IBKR provider status was ready.
- Replay evidence: all 19 admission commands exited `0`; both analyze passes exited `0`; `17` same-workspace simulated trades were ingested.
- Final metrics: `exact_branch_survived=true`, `mature_rows=2`, `history_mature_rows=18`, `ranker_validation_ready=false`, execution candidate `no_trade`, `execution_readiness=0.4313563048804659`, `transition_hazard=0.9184975817511946`, `pda_hybrid_alignment=false`, path-ranker score visible but not used by execution tree.

Reusable lesson:

- Fixing branch-direction context can restore exact-root survival and avoid a false MTF conflict, but it does not by itself repair trade admission.
- Once a same-root M2K RVOL/PDA replay has clean command exits, exact-root survival, and visible ranker score, stop repeating simulated-feedback loops. The remaining blocker is substantive: too few current mature rows, PDA/regime-family disagreement, high transition hazard, readiness below `0.65`, and execution-tree non-use of the score.
- Next same-root M2K work must add acceptable real/current mature validation and directly lower transition hazard while aligning PDA/hybrid state. Otherwise rotate to a materially different `1m` root; do not add another light RVOL/PDA/liquidity overlay and do not lower gates.
