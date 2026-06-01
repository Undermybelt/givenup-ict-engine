# Tomac short-reversal runtime timeout with no Gate 1 artifact (2026-05-21)

Use when a Tomac/Auto-Quant factor lane exits around its timeout boundary but
does not write `run_tomac` exit markers, stdout/stderr, backtest zips, rank
rows, or Gate 1 JSON.

## Classification rule

Do not classify the candidate factor as cost-positive or cost-negative from an
empty terminal surface. Mark the lane as:

```text
stopped_no_terminal_metrics_no_factor_verdict
```

and keep all downstream gates false:

```text
downstream_allowed=false
pre_bayes_allowed=false
bbn_allowed=false
catboost_allowed=false
execution_tree_allowed=false
promotion_allowed=false
trade_usable=false
update_goal=false
```

## Required evidence

Record:

- scratch root and compact run root
- configured timeout
- last observed parent/child elapsed times
- process state after timeout-boundary check
- files present: AQ config, data feathers, strategy files
- files missing: `checks/*.exit`, `checks/terminal_metrics.json`, rank rows,
  `summary.json`, stdout/stderr, backtest result zip

## Next action

Retry only after current AQ slots are free, and change the runtime shape before
rerunning:

- shard by symbol;
- reduce the window;
- run a single timeframe/family at a time;
- or repair the wrapper so it writes timeout diagnostics explicitly.

Do not run Pre-Bayes/BBN/CatBoost/execution-tree until a real Gate 1 rank
artifact exists.
