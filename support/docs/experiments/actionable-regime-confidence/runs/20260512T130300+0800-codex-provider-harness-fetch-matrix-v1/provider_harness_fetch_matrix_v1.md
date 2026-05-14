# Provider Harness Fetch Matrix v1

Run root: `docs/experiments/actionable-regime-confidence/runs/20260512T130300+0800-codex-provider-harness-fetch-matrix-v1`

Purpose: classify a settled provider-harness result under Board B's negative-evidence contract without turning infrastructure failures into market/factor labels.

## Request

- Market key: `board-b-provider-matrix-spy-1d-after-125425`
- Interval: `1d`
- Window: `2026-04-01T00:00:00Z` to `2026-05-09T00:00:00Z`
- Roles:
  - `yf_spy`: `yfinance` `SPY`
  - `tvr_spy`: `tradingview_mcp` `AMEX:SPY`
  - `ibkr_spy`: `ibkr` `SPY STK SMART USD primary_exchange=ARCA`

## Commands

| Step | Command output | Exit | Readback |
|---|---:|---:|---|
| Provider readiness | `command-output/00_provider_status_agent.out` | `0` | Completed |
| Harness plan | `command-output/01_market_data_harness_plan.out` | `0` | Completed |
| Harness fetch | `command-output/02_market_data_harness_fetch.out` | `1` | Partial provider success; IBKR failure |

## Provider Readback

| Provider | Role | Symbol | Result | Rows | Classification |
|---|---|---|---:|---:|---|
| `yfinance` | `yf_spy` | `SPY` | `ok=true` | `27` | provider_data_acquired |
| `tradingview_mcp` | `tvr_spy` | `AMEX:SPY` | `ok=true` | `27` | provider_data_acquired |
| `ibkr` | `ibkr_spy` | `SPY` | `ok=false` | `0` | infrastructure_negative_sample |

YF first candle: `2026-04-01T13:30:00Z` open `653.9000244140625`, high `658.52001953125`, low `653.0`, close `655.239990234375`, volume `97841500.0`.

YF last candle: `2026-05-08T13:30:00Z` open `734.9299926757812`, high `738.0800170898438`, low `734.5700073242188`, close `737.6199951171875`, volume `47227100.0`.

TVR first candle: `2026-04-01T13:30:00Z` open `653.9`, high `658.52`, low `653.0`, close `655.24`, volume `97841472.0`.

TVR last candle: `2026-05-08T13:30:00Z` open `734.93`, high `738.08`, low `734.57`, close `737.62`, volume `47227085.0`.

IBKR error: `fetch_failed: ibkr historical fetch failed for 'SPY'`, retryable `true`.

Underlying IBKR runtime failure: `ibkr-historical requires the ibkr_bridge package ... Underlying error: No module named 'redis'`.

Provider plan readback showed IBKR as `configured_runtime_unhealthy` with reachable gateway `IB Gateway paper:4002`, missing module `redis`, and install prompts to run the fetch runtime with `redis`, `ib_async`, and `pandas`.

## Evidence Classification

This run is not a profitability packet and not a market/factor negative sample.

- `evidence_class=provider_acquisition_positive_plus_infrastructure_negative_sample`
- `market_factor_learning_quality_weight=0`
- `provider_reliability_learning_quality_weight=1`
- `branch_path=not_applicable_provider_harness_only`
- `main_regime=null`
- `sub_regime=null`
- `sub_sub_regime_or_profit_factor=null`
- `profit_factor=null`
- `provider_provenance=yfinance:SPY:1d:27_rows;tradingview_mcp:AMEX:SPY:1d:27_rows;ibkr:SPY_STK_SMART_ARCA:fetch_failed_missing_redis`
- `pre_bayes_filter_status=not_run`
- `bbn_posterior=not_run`
- `catboost_path_ranker_label=not_run`
- `execution_tree_decision=not_run`
- `final_outcome=partial_provider_fetch_success_with_ibkr_runtime_dependency_failure`
- `failure_reason=ibkr_runtime_missing_redis`
- `allowed_feedback_targets=provider_reliability,evidence_quality_weight,data_authority_gate,workflow_readiness,human_next_repair_prompt`
- `disallowed_feedback_targets=bbn_likelihood_table,regime_conditioned_win_rate,path_ranker_market_label,execution_tree_market_branch_weight`

## Conclusion

The provider matrix is not globally blocked: YF and TVR both produced comparable SPY daily OHLCV rows for the same request window. IBKR did not fail because of market state, factor quality, or branch profitability; it failed at the local runtime dependency boundary before provider data acquisition. Treat the IBKR result as infrastructure evidence only until the fetch runtime can import `redis` and the exact IBKR contract request succeeds or fails again.

Promotion remains blocked. No Auto-Quant, Pre-Bayes/filter, BBN, CatBoost/path-ranker, or execution-tree closure was attempted from this provider harness packet.
