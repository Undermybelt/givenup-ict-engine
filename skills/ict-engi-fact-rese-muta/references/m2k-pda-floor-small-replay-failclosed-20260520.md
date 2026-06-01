# M2K PDA-floor small replay fail-closed lesson - 2026-05-20

> 2026-05-24 schema note: `pda_hybrid_alignment` is historical telemetry only unless the current ict-engine source or readback contract still declares it active. Do not use old `pda_hybrid_alignment=true` or `false` lines in this reference as a current hard gate; classify with the live actionable/status/readiness/transition/ranker/mature-row fields.

Use this when continuing the IBKR `M2K/1m` liquidity-sweep reject-short
`RVOL/PDA consistency-floor` branch or when a same-root simulated-admission
wrapper falls back from a full replay to a small replay.

Evidence packet:
- Gate 1 root: `support/docs/experiments/actionable-regime-confidence/runs/20260520T100242+0800-codex-ibkr-m2k1m-rvol-pda-consistency-floor-7d-gate1-v1`
- Sim-admission root: `support/docs/experiments/actionable-regime-confidence/runs/20260520T100242+0800-codex-ibkr-m2k1m-rvol-pda-consistency-floor-7d-gate1-v1/simulated-trade-admission-m2k-1m-rvol-pda-consistency-floor-20260520T102522+0800`
- Branch: `FUTURES -> equity_index -> M2K -> 1m -> RangeReversion -> LiquiditySweepRejectShort -> ibkr_m2k1m_liquidity_sweep_reject_short_7d_gate1_v1 -> ibkr_m2k1m_liquidity_sweep_reject_short_rvol_pda_guard_pda_consistency_floor_v1`

Result:
- Gate 1 reconfirmed a real retained-IBKR cost survivor: `17` trades, raw
  `+2.79%`, `2bps=+2.11%`, `5bps=+1.09%`.
- Full simulated-admission replay imported AQ results and initialized priors,
  but full `7 D` seed analyze hung at `03_analyze_seed` and had to be
  terminated.
- The wrapper's diagnostic last-`3000`-row small replay survived exact branch
  identity but still failed closed: `execution_readiness=0.19681737339554`,
  `transition_hazard=0.9487494700457024`, `pda_hybrid_alignment=false`,
  ranker score not visible/used, PDA sequence consistency only `0.357`, and
  `pre_bayes_allowed=false`, `bbn_allowed=false`, `catboost_allowed=false`,
  `execution_tree_allowed=false`, `promotion_allowed=false`, `trade_usable=false`.

Rule:
- Treat this branch as a strong Gate 1 survivor and execution-repair lead, not
  as trade-usable alpha.
- Do not add another light RVOL/PDA/liquidity micro-filter or lower gates.
- Next same-root work must make the full replay complete, materialize exact-root
  execution admission, raise PDA sequence consistency, reduce
  `transition_hazard < 0.60`, flip `pda_hybrid_alignment=true`, and stabilize
  `execution_readiness >= 0.65`.
- A small replay is diagnostic only; it cannot replace full-window downstream
  proof for promotion.
