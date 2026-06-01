# IBKR ORB/RVOL regime-rooted chain session note

Use when continuing Board B profitability-factor work where the operator wants public/source-backed factors to run through real provider data, Auto-Quant, BBN/prior/filter, CatBoost/path-ranker, and execution tree while preserving the branch path.

## Session pattern

Branch tested:

```text
TrendExpansion -> OpeningDrive -> opening_range_breakout_rvol -> ibkr_qqq_orb_rvol_mtf_v1
```

Source idea:
- Opening Range Breakout / ORB public strategy family.
- RVOL + VWAP trend filter.
- Lookahead guard: compute opening range from the completed opening window only, and allow entries only after the opening window ends.

## Provider behavior

- `provider-status --compact` can be fully green while a specific live IBKR request still fails or times out.
- If default TWS/Gateway paper port `7497` is refused, inspect active listening IBKR ports and retry the active one, commonly `4002` on this host.
- If a fresh symbol/window times out, classify it as `provider-window blocker`, not factor failure.
- Reusing prior verified provider CSVs is acceptable only if the material records provenance explicitly, e.g. `reused_prior_verified_ibkr_csv_after_live_timeout`.

## Verified run artifacts

Run root:

```text
/tmp/ict-engine-runs/20260518T084127+0800-hermes-ibkr-qqq-orb-rvol-mtf-chain-v1
```

Key artifacts:

```text
checks/terminal_metrics.json
summaries/terminal_decision_summary.md
state/auto-quant/IBKR_QQQ_ORB_RVOL_MTF_CHAIN/auto_quant_agent_material_rank.20260518T004143.881Z.json
```

AQ ladder result:

| timeframe | rows | trades | win_rate | total_profit | sharpe |
|---|---:|---:|---:|---:|---:|
| 1m | 6720 | 3 | 100.0% | +0.49% | 15.8853 |
| 5m | 4224 | 10 | 50.0% | +0.55% | 1.6275 |
| 15m | 1408 | 12 | 33.3333% | +0.52% | 0.8047 |
| 30m | 2016 | 17 | 35.2941% | -1.31% | -0.5665 |
| 1h | 1008 | 0 | 0.0% | 0.0% | 0.0 |

Downstream readback:

```text
path_ranker_score_visible_to_execution_tree=true
path_ranker_score_used_by_execution_tree=true
path_ranker_model_family=catboost
ranker_validation_ready=false
branch=transition_guardrail
gate_status=observe
execution_bias=guarded
```

Decision:

```text
incubate_gate1_needs_downstream_or_failclosed
```

Do not promote. The signal has 1m/5m/15m positive Gate 1 evidence, but HTF is mixed/weak and execution remains guarded because mature validation rows are missing.

## Provider quartet probe addendum

Same session confirmed provider-axis fetches can work for comparable 5m evidence:

```text
yfinance QQQ 5m: 781 rows after retry from HTTP 429
TradingViewMCP QQQ 5m: 300 rows via local stdio
Kraken XBTUSD 5m: 721 rows
IBKR QQQ ladder: reused prior verified IBKR CSVs after fresh XLE timeout
```

Probe root:

```text
/tmp/ict-engine-runs/provider-quartet-probes-20260518
```

## Future use

For the next sourced factor, prefer this order:

1. Research-backed candidate: Market Intraday Momentum, Overnight-vs-Intraday Reversal, or ORB/RVOL variant.
2. Build materials with `main_regime`, `sub_regime`, `sub_sub_regime_or_profit_factor`, `profit_factor`, `branch_path`, `regime_profit_branch_path`, and provider provenance.
3. Start at `1m`, then cover `5m`, `15m`, `30m`, `1h`.
4. If AQ is positive only on low frames, mark the low frame as candidate/timing and HTF as neutralization/confirmation, not co-equal profit proof.
5. Run BBN/prior/filter, CatBoost, execution-tree readback before claiming anything beyond Gate 1.
6. Fail closed if `ranker_validation_ready=false`, mature rows are zero, or execution tree stays `observe/guarded/transition_guardrail`.
