# CRWD 5m PDA/MTF downstream exact fail-closed pattern

> 2026-05-24 schema note: `pda_hybrid_alignment` is historical telemetry only unless the current ict-engine source or readback contract still declares it active. Do not use old `pda_hybrid_alignment=true` or `false` lines in this reference as a current hard gate; classify with the live actionable/status/readiness/transition/ranker/mature-row fields.

Use this as a replay target for regime-rooted live-ready factor training when a branch looks economically good but promotion remains blocked by mature-row gating.

## Exact branch

```text
US_EQ -> single_stock -> CRWD -> 5m -> RangeReversion -> AiSecuritySoftwareOversoldReclaim -> rsi_vwap_reclaim_dense -> yf_ai_security_software_rsi_vwap_reclaim_crwd_5m_v1 -> session_liquidity_transition_stability_v1 -> pda_mtf_soft_confirmation_v1
```

## Evidence shape

Run directory observed:

```text
support/docs/experiments/actionable-regime-confidence/runs/20260519T102243+0800-codex-yf-ai-security-crwd5m-pda-mtf-soft-confirmation-gate1-v1/downstream-exact-crwd-5m-pda-mtf-soft-confirmation-20260519T140310+0800
```

Decisive metrics:

- `decision=exact_crwd_5m_downstream_fail_closed`
- `promotion_allowed=false`
- `trade_usable=false`
- `update_goal=false`
- `exact_branch_survived=true`
- `all_command_exits_zero=true`
- Gate 1: `trades=43`, `win_rate=62.7907%`, `total_profit=5.81%`, `sharpe=6.0837`
- Cost stress survives: `2bps=4.09%`, `5bps=1.51%`
- `mature_rows=3` fail; `history_mature_rows=46` pass
- `transition_hazard=0.5950369253623637` pass
- `pda_hybrid_alignment=true` pass
- `execution_readiness=0.67` pass

## Workflow lesson

When a branch has positive real-cost economics and passes transition/PDA/readiness but `mature_rows < 30`, do not mutate thresholds or claim live-ready. Keep the exact root/overlay path intact, label it observation/incubate, and prioritize obtaining or replaying legitimate mature feedback rows for that same branch.

Check both top-level and nested execution-tree fields. In this session, compacted summary showed path-ranker visibility/usage/validation ready as true, while a later narrow JSON probe against `downstream_metrics.json` returned `None` for top-level `path_ranker_*`. Future audits should inspect `execution_tree_trace.json` and nested `output.*` before concluding ranker evidence is absent.
