# CRWD 5m PDA/MTF soft-confirmation exact downstream repair

> 2026-05-24 schema note: `pda_hybrid_alignment` is historical telemetry only unless the current ict-engine source or readback contract still declares it active. Do not use old `pda_hybrid_alignment=true` or `false` lines in this reference as a current hard gate; classify with the live actionable/status/readiness/transition/ranker/mature-row fields.

Use when a CRWD 5m PDA/MTF soft-confirmation branch has a good AQ Gate 1 row but downstream replay reports zero real trades or stops before CatBoost/execution-tree.

## Exact branch

```text
US_EQ -> single_stock -> CRWD -> 5m -> RangeReversion -> AiSecuritySoftwareOversoldReclaim -> rsi_vwap_reclaim_dense -> yf_ai_security_software_rsi_vwap_reclaim_crwd_5m_v1 -> session_liquidity_transition_stability_v1 -> pda_mtf_soft_confirmation_v1
```

## Durable lesson

If real-trade extraction fails with a missing `run_tomac.py`, first verify the Auto-Quant material unit name. The exact CRWD PDA/MTF branch uses:

```text
state/auto-quant/agent_material_units/AI-security_CRWD_5m_PDA_MTF_soft_confirmation_Gate_1_-_CRWD_5m/aq_workspace
```

not the older beauty/personal-care reclaim unit:

```text
state/auto-quant/agent_material_units/Beauty_personal-care_RSI_VWAP_reclaim_Gate_1_-_yfinance_YF_CRWD_5m/aq_workspace
```

The matching strategy file is:

```text
user_data/strategies_external/YfAiSecurityCrwd5mPdaMtfSoftConfirmationCrwd5MinV1.py
```

## Validation pattern

After patching the workspace/strategy path, rerun the exact downstream script and require all of these before treating it as more than observation:

- real Freqtrade trades exported and ingested
- Pre-Bayes/filter pass
- BBN/workflow pass
- CatBoost/path-ranker train/apply/register pass
- execution tree readback pass
- branch path preserved exactly
- `transition_hazard < 0.60`
- `pda_hybrid_alignment=true`
- `execution_readiness >= 0.65`
- `path_ranker_score_visible_to_execution_tree=true`
- `path_ranker_score_used_by_execution_tree=true`
- `ranker_validation_ready=true`
- `mature_rows >= 30`
- `history_mature_rows >= 30`

## Known readback shape from the repaired run

A repaired run produced:

```text
AQ: 43 trades, win_rate=62.7907, total_profit_pct=5.81, sharpe=6.0837
cost: net_after_2bps_per_side=4.09%, net_after_5bps_per_side=1.51%
real trades: 43 rows, 27 wins, 16 losses, 0 breakevens
execution: gate_status=ready, branch=fill_viable, execution_readiness=0.67
hazard/alignment: transition_hazard=0.5950369253623637, pda_hybrid_alignment=true
ranker: visible=true, used=true, validation_ready=true
maturity: mature_rows=3, history_mature_rows=46
```

Decision remains fail-closed because `mature_rows < 30`. Do not promote or mark trade-usable until current mature rows reach the floor; keep expanding exact-root evidence instead of lowering thresholds.
