# Gate 1 Positive, Downstream Fail-Closed Parity

> 2026-05-24 schema note: `pda_hybrid_alignment` is historical telemetry only unless the current ict-engine source or readback contract still declares it active. Do not use old `pda_hybrid_alignment=true` or `false` lines in this reference as a current hard gate; classify with the live actionable/status/readiness/transition/ranker/mature-row fields.

Use this when a regime-rooted profitability factor passes Auto-Quant Gate 1 on a scoped ladder but fails later in Pre-Bayes/BBN/CatBoost/execution-tree.

## Session pattern captured

Branch:

```text
TrendExpansion -> MaterialsSectorOpeningDrive -> one_minute_orb_rvol_vwap_density -> tvr_xlb_orb_rvol_vwap_density_1m_mtf_v1
```

Provider and ladder:

- Provider: TradingViewRemix / `tradingview_mcp`
- Symbol: `AMEX:XLB`
- Timeframes: `1m`, `5m`, `15m`, `30m`, `1h`
- Provider rows: `1m=2731`, `5m=1561`, `15m=521`, `30m=261`, `1h=141`

AQ Gate 1 result:

- `1m`: 26 trades, `+0.37%`, Sharpe `5.1313`
- `5m`: 38 trades, `+0.71%`, Sharpe `2.3356`
- `15m`: 25 trades, `-2.13%`
- `30m`: 17 trades, `-0.33%`
- `1h`: 0 trades
- Decision: `keep_gate1_observation_downstream_allowed`

Downstream result:

- Auto-Quant import: pass
- Auto-Quant prior init: pass
- analyze/workflow/pre-bayes/export target: pass
- Pre-Bayes gate: `pass_neutralized`
- Exact rooted branch survived into closed-loop branch admission
- CatBoost training failed with `All features are either constant or ignored`
- Path-ranker not visible/used by execution tree
- Execution stayed `execution_observe_only`, branch `transition_guardrail`
- Decision: `gate1_pass_downstream_fail_closed`

## Durable rule

A scoped Gate 1 positive is useful evidence, not live readiness. If the exact branch survives downstream but CatBoost/path-ranker lacks feature variance or mature labels, preserve the factor as a scoped candidate and classify the blocker as downstream maturity/feature-variance or execution fail-closed.

Do not discard the factor merely because execution is observe-only. Do not promote it merely because Gate 1 passed. The correct next slice is one of:

1. Add sibling rows for the same regime branch to create feature/label variance.
2. Use history-backed path-ranker training only when history has enough varied mature rows.
3. Diagnose execution-readiness shortfall for the exact branch.
4. Keep it as scoped evidence with `global_promotion_not_claimed`.

## Contrast cases from same loop

- IBKR XLF VWAP reclaim: all feasible-window fetches returned no rows/exit 3, so classify as `provider_window_blocked_no_gate1_verdict`, not a factor failure.
- YF XLF VWAP reclaim fallback: sparse/mixed ladder, classify as observation-only; no downstream.
- Kraken ATOM MTF resonance density: provider/AQ passed but no positive rows and no 1m origin trades; classify as Gate 1 practical failure; no downstream.

## 2026-05-23 VST exact same-root replay

Use the VST power-infrastructure VWAP/NR7 packet as the clean positive-Gate-1,
fail-closed downstream example when the exact branch, PDA alignment, and
path-ranker visibility all survive but execution still does not admit a trade.

Source Gate 1 root:

```text
support/docs/experiments/actionable-regime-confidence/runs/20260523T010722+0800-codex-ibkr-vst-power-infra-vwap-nr7-reclaim-1m-mtf-gate1-v1/
```

Dedicated downstream root:

```text
support/docs/experiments/actionable-regime-confidence/runs/20260523T013226+0800-codex-ibkr-vst-power-infra-vwap-nr7-reclaim-same-root-downstream-v1/
```

Branch:

```text
RangeConsolidation -> VolatilityCompressionExpansion -> vwap_nr7_reclaim -> ibkr_vst_power_infra_vwap_nr7_reclaim_1m_mtf_gate1_v1
```

Gate 1 replay inputs:

- `1m` dense: 19 trades over 10 days, 1.9 trades/day, raw `+3.34%`, `5bps/side=+1.44%`
- `1m` late_reclaim: 20 trades, 2.0 trades/day, raw `+3.29%`, `5bps/side=+1.29%`
- `1m` balanced: 15 trades, 1.5 trades/day, raw `+2.17%`, `5bps/side=+0.67%`

Downstream readback:

- `17/17` commands exited `0`
- exact branch survived
- exact ranker score was visible to the execution tree
- execution tree did not use the ranker score
- `execution_candidate_status=no_trade`
- `execution_candidate_actionable=false`
- `execution_readiness=0.5038501840345855`
- `transition_hazard=0.6267383509584497`
- `pda_hybrid_alignment=true`
- `mature_rows=0`
- `history_mature_rows=0`
- `promotion_allowed=false`
- `trade_usable=false`
- `extension_complete=false`

Durable rule:

A hard `5bps/side` and practical-density Gate 1 survivor is still
observation-only when the same-root downstream replay has no actionable execution
candidate, `transition_hazard >= 0.60`, `execution_readiness < 0.65`, zero
mature validation rows, or ranker visibility without execution-tree usage. Do
not rerun Gate 1 or relax predicates. The next same-root repair must directly
target transition hazard, execution candidate materialization, execution
readiness, and mature validation.
