# IBKR options regime-rooted Auto-Quant chain

Use when a profitability factor must be anchored by real IBKR option/HV/IV data and then carried through provider portability, Auto-Quant material/rank, BBN prior, CatBoost/path-ranker, and execution-tree readback.

## Trigger

User asks for IBKR option data, options dealer context, HV/IV, or says not to infer from docs and to personally run Auto-Quant + ict-engine downstream.

Required branch fields at every handoff:

```text
main_regime
sub_regime
sub_sub_regime_or_profit_factor
profit_factor
branch_path
regime_profit_branch_path
provider_provenance
```

Example branch:

```text
RangeConsolidation -> OptionsDealerContext -> gamma_wall_premium_reclaim -> ibkr_option_premium_reclaim_v1
```

## Run pattern

1. Create external claim under `/tmp/ict-engine-agent-claims/board-b-factor-refinement/`; do not use board markdown as a scratch lock.
2. Read compact Board A/B current docs and repo `AGENT.md`; avoid editing another agent's lane.
3. Select an option contract from a real chain when possible. A robust shortcut is to use yfinance only to pick ATM expiry/strike, then fetch actual IBKR option premium/HV/IV through `fetch_external.py ibkr-historical`.
4. Fetch separate evidence rows:
   - IBKR option call/put premium `5 mins` or smaller (`sec-type OPT`, `last-trade-date`, `strike`, `right`).
   - IBKR `HISTORICAL_VOLATILITY` and `OPTION_IMPLIED_VOLATILITY` for the underlying.
   - yfinance and TradingViewRemix/tradingview_mcp OHLCV for tradfi portability.
   - Kraken public crypto OHLCV only as cross-market contrast, not proof of tradfi portability.
   - `fetch_external.py ibkr-historical` does **not** expose true option open interest or broker Greeks in the current contract. If the user asks for OI/Greeks, either fetch them through a separate option-chain surface or label the run explicitly as `option_volume_interest_proxy` + Black-Scholes delta/gamma proxy; do not call it true OI/Greeks.
5. Normalize every AQ material CSV to `timestamp,open,high,low,close,volume`; IBKR bridge may emit `date` or `ts`. Generic agent-material dispatch rejects raw `ts` headers before `prepare_external.py` runs.
6. Build Auto-Quant material JSON with a valid `YYYYMMDD-YYYYMMDD` timerange and the branch fields under `consumer_evidence_profile`.
7. Run `auto-quant-agent-material-batch`, `auto-quant-agent-material-dispatch`, and `auto-quant-agent-material-rank`.
8. Stop before BBN if rank rows lose branch fields.
9. Build/import a `strategy_library.json` preserving branch metadata, then run `auto-quant-results-import` and `auto-quant-prior-init --force` only in isolated state.
10. Run `analyze`, `pre-bayes-status`, `workflow-status`, `export-structural-path-ranking-target`.
11. For true CatBoost, invoke the trainer with deps even if local Python lacks catboost:

```bash
uv run --with pandas --with numpy --with catboost python \
  support/scripts/auto_quant_external/pandas_path_ranker_trainer.py \
  --target-csv <target.csv> --output-dir <model-dir> \
  --model-family catboost --allow-direct-fallback

uv run --with pandas --with numpy --with catboost python \
  support/scripts/auto_quant_external/pandas_path_ranker_trainer.py \
  --apply --model-dir <model-dir> --target-csv <target.csv> \
  --output-scores <scores.csv> --allow-direct-fallback
```

12. Apply/register/enable the ranker, rerun `analyze`, then inspect `execution_tree_trace.json` and `policy-training-status`.

## Acceptance readback

Minimum evidence:

- Provider matrix shows actual fetch row counts for IBKR option premium and IBKR HV/IV, not just provider readiness.
- AQ rank has `rank_rows_have_branch_fields=true` and nonzero trade rows.
- BBN prior reports `evidence_value_gate_passed=true` and nonempty `strategies_applied`.
- CatBoost model exists (`catboost_model.cbm`), scores exist, trainer artifact registered as `model_family=catboost`.
- Execution trace has `path_ranker_score_visible_to_execution_tree=true`, `path_ranker_score_used_by_execution_tree=true`, and `path_ranker_model_family=catboost`.

## Decision rules

- After a first seed finds low-density positives, the next useful move is a same-provider small-cycle density mutation (`1m` relaxed gates and one `5m` quality control) before medium/high confirmation. This can quickly distinguish `trade_count=0-2` artifacts from candidates with usable event density.
- Before promoting two positive small-cycle mutations as independent factors, audit entry-signal overlap. In the QQQ IBKR options run, `iv_carry_dense_1m` and `vol_expansion_relaxed_1m` had 98.54% Jaccard / 100% one-way overlap, so the relaxed variant is a child/ablation of IV carry, not a separate factor.
- Test 30m/1h neutralization as a hard gate before promoting it. Short IBKR windows may make long HTF EMAs unusable; relaxed `30m EMA55 + 1h EMA21` reduced `iv_carry_dense_1m` from 40 trades / 1.76% profit / 53.41 Sharpe to 25 trades / 0.88% profit / 37.83 Sharpe with no drawdown improvement, so keep HTF as diagnostic feature unless a rerun proves otherwise.
- For cross-asset futures/stocks runs, keep the data truth labels explicit: current `ibkr-historical` can fetch futures/stocks TRADES and stock HV/OPTION_IMPLIED_VOLATILITY, but not true futures OI/broker Greeks through this path. Label futures OI/Greeks as volume/count + Black-Scholes proxy; label stock IV/HV as true IBKR series.
- When a cross-asset aggregate is positive, isolate the apparent winners before refining. In the ES/GC follow-up, a harder GC/ES gamma-wall filter went negative (`-0.51%`, PF `0.58`), while isolated original ES improved to `1.53%`, PF `1.73`; isolated GC fell to `0.39%`, PF `1.07`. Treat ES as the next candidate and GC as portfolio-context only until a standalone edge is proven.
- If `raw_scored_mature=0/30`, `production_validation=0/30`, or `observation_validation=0/30`, decision is fail-closed (`incubate_fail_closed`), not promotion.
- If execution tree says `observe`, `transition_guardrail`, `guarded`, `not_ready`, or `bridge_needs_confirmation`, do not promote even when AQ/BBN/CatBoost all ran.
- If ranker training first falls back because `catboost not installed`, retry with `uv run --with pandas --with numpy --with catboost ...`; do not record “CatBoost unavailable” as durable unless the retry fails.
- A positive TVR/yfinance row does not prove an IBKR option factor unless IBKR option premium rows also have usable trade density.

## Compact example evidence shape

```json
{
  "provider_rows": {
    "IBKR_OPT_CALL_5m": 321,
    "IBKR_OPT_PUT_5m": 313,
    "IBKR_HV_1d": 251,
    "IBKR_IV_1d": 251,
    "yfinance_QQQ_5m": 1795,
    "tradingview_mcp_QQQ_5m": 1200,
    "kraken_XBTUSD_5m": 721
  },
  "rank_rows": 5,
  "rank_total_trades": 109,
  "rank_rows_have_branch_fields": true,
  "bbn_evidence_value_gate_passed": true,
  "catboost_model_exists": true,
  "execution_tree": {
    "path_ranker_score_visible_to_execution_tree": true,
    "path_ranker_score_used_by_execution_tree": true,
    "path_ranker_model_family": "catboost"
  },
  "decision": "incubate_fail_closed"
}
```
