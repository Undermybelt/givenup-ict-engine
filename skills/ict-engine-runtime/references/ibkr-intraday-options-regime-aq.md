# IBKR intraday/options regime + Auto-Quant closure

Use when Board A asks for denser K-lines (`1m/5m/15m/30m`), IBKR-backed validation, options/HV/IV context, or asks whether the chain actually used Auto-Quant.

## Durable lessons

- Prefer IBKR for dense TradFi evidence before calling a Board A lane data-poor. Fetch `1m`, `5m`, `15m`, `30m`, plus `1d` trades, `HISTORICAL_VOLATILITY`, and `OPTION_IMPLIED_VOLATILITY` when option context matters.
- `fetch_external.py ibkr-historical` may require `ib_async`, not only `ib_insync`. A robust one-off runner is:

```bash
uv run --with redis --with ib_async --with pandas python \
  scripts/auto_quant_external/fetch_external.py ibkr-historical \
  --symbol QQQ --sec-type STK --exchange SMART --currency USD \
  --primary-exchange NASDAQ --bar-size '5 mins' --duration '30 D' \
  --what-to-show TRADES --host 127.0.0.1 --port 4002 \
  --client-id 173 --output /tmp/ibkr_qqq_5m.csv
```

- IBKR CSVs emitted by the bridge can use `ts` as the timestamp column. ICT JSON conversion can accept `ts`, but Auto-Quant material dispatch expects one of `timestamp/time/datetime/ts_event/date`; normalize `ts -> timestamp` before feeding AQ.
- More rows do not imply 95% regime confidence. Report validator confidence, posterior confidence, coverage, and mature ranker status separately.
- If Auto-Quant batch/dispatch/rank exits `0` but ranked unit status is `failed`, say AQ was used but produced no usable performance metrics.

## Minimal sequence

1. Fetch dense IBKR candles and HV/IV with `uv run --with redis --with ib_async --with pandas python scripts/auto_quant_external/fetch_external.py ibkr-historical ...`.
2. Convert CSV to ICT candle JSON, accepting `ts` as timestamp.
3. Run `validate-market-state --profile high_confidence`; for dense but short 1m/5m samples use `--window-size 60`, for 15m/30m use `100` unless the sample is too short.
4. Run runtime chain: `analyze` using `30m/15m/5m` as HTF/MTF/LTF, then `workflow-status`, `pre-bayes-status`, `policy-training-status`, target export, CatBoost train/apply/register/enable, workflow readback.
5. Normalize IBKR CSV header for AQ (`ts` -> `timestamp`) and run `auto-quant-agent-material-batch`, `auto-quant-agent-material-dispatch`, `auto-quant-agent-material-rank`.
6. Terminal summary must explicitly state: provider row counts, validator best slice, posterior probabilities, Pre-Bayes status, CatBoost mature rows, AQ rank status, and whether 95% was actually reached.

## Pitfalls

- Do not stop after yfinance/Kraken if the user specifically says IBKR/options are richer.
- Do not treat AQ command exit `0` as strategy success; inspect rank JSON `ranking[].status`, `win_rate_pct`, `sharpe`, and `trade_count`.
- Do not call CatBoost presence a calibrated signal when `mature_rows=0`, `raw_scored_mature=0/30`, or `calibration=not_fitted`.
- Avoid saying every regime is covered unless all regime classes have nonzero samples or explicit evidence; compact validator top labels are not full coverage proof.
