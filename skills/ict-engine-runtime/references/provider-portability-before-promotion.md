# Provider portability before promotion

Use when a profitability factor looks good on one provider/timeframe ladder, but the user asks whether it can move toward practical promotion.

## Session lesson

A factor can look promising on an IBKR multi-timeframe ladder and still fail a provider-portability gate. Do not promote or run expensive downstream BBN/CatBoost/execution-tree steps for the portability variant if Auto-Quant returns no positive provider rows.

Concrete pattern from the session:

- `ibkr_qqq_intraday_momentum_mtf_v1` was promising on IBKR MTF:
  - `1m`: 25 trades, +0.29%, Sharpe 7.9974
  - `15m`: 14 trades, +0.22%, Sharpe 0.405
  - `30m`: 28 trades, +0.87%, Sharpe 0.4534
  - `1h`: 11 trades, +0.70%, Sharpe 0.4764
  - `5m`: 28 trades, -0.04%, Sharpe -0.1357
  - CatBoost was visible and used by execution tree, but `raw_scored_mature=0/30`, `ranker_validation_ready=false`, `branch=transition_guardrail`, `gate_status=observe`.
- The same formula as a provider-quartet `5m` portability test failed:
  - yfinance QQQ: 781 rows, 9 trades, -0.21%, Sharpe -3.2416
  - IBKR QQQ: 4224 rows, 28 trades, -0.04%, Sharpe -0.1357
  - TradingViewMCP QQQ: 500 rows, 8 trades, -0.26%, Sharpe -7.9498
  - Kraken XBTUSD: 721 rows, 0 trades
  - decision: `drop_no_positive_provider_rows`

## Operational rule

1. Preserve the exact branch fields in every material/rank row:
   - `main_regime`
   - `sub_regime`
   - `sub_sub_regime_or_profit_factor`
   - `profit_factor`
   - `branch_path`
   - `regime_profit_branch_path`
   - `provider_provenance`
2. If a provider-portability AQ rank has zero positive provider rows, stop before BBN/CatBoost/execution-tree for that portability variant.
3. Classify as provider-portability failure, not total factor failure, when the provider-specific ladder was separately positive.
4. Keep the original provider-specific branch as `incubate` only if its own downstream readback remains fail-closed.
5. For cross-market proxy rows such as Kraken BTC versus QQQ, label them as portability stress, not direct same-asset proof.

## Candidate ranking lesson

In this session, sourced candidates ranked:

1. `ibkr_qqq_intraday_momentum_mtf_v1` — best IBKR-specific incubate candidate, but provider-quartet 5m failed.
2. `ibkr_qqq_gap_fade_reclaim_mtf_v1` — weak positive reversal sample; 1h no trade; retain as ReversalBrewing evidence only.
3. `ibkr_qqq_orb_rvol_mtf_v1` — small-cycle positive but 30m negative and 1h no trade; retain as OpeningDrive evidence only.

## Fail-closed wording

Use:

```text
provider_portability_failed_stop_before_downstream
provider_specific_incubate_only
ranker_visible_used_but_validation_not_ready
```

Do not use:

```text
trade_ready
promotion
provider_quartet_passed
```

unless provider rows are positive and execution-tree maturity/readiness gates pass.
