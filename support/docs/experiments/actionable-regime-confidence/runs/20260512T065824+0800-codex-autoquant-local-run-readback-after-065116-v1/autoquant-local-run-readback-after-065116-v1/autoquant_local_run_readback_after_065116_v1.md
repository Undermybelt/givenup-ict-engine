# Auto-Quant Local Run Readback After 065116 v1

Run id: `20260512T065824+0800-codex-autoquant-local-run-readback-after-065116-v1`

Gate result: `autoquant_local_run_readback_after_065116_v1=status_data_ready_but_run_dns_blocked_no_promotion`

Board sha256 before artifact: `af1d64f37c9503ef8e10817bedb5b752d08e2bf6a02e5935a2a57fc016433c42`

## Scope

Read-only runtime follow-up after the `065116` Auto-Quant bootstrap/prepare reconciliation. This packet checks whether the currently prepared `064259` Auto-Quant state can actually execute `run.py`. It does not mutate source/control roots, run canonical merge, promote regime confidence, make a trade claim, or call `update_goal`.

## Findings

- Current `064259` Auto-Quant status exit `0` reports `dependency_ready_data_ready` with `data_ready=True`.
- Global local Auto-Quant status exit `0` reports `dependency_ready_seed_required` with `data_ready=True` and blocked reason `auto_quant_seed_strategies_required`.
- Current `064259` state has `1` active non-underscore strategy file(s): `TomacNQ_KillzoneBreakout.py` (`2` strategy-directory file(s) including templates).
- Bounded `/tmp` strategy inventory found `16` active strategy-file path(s).
- `run.py` exit code `1`; discovered strategy count `1`; backtests succeeded `0`, failed `1`.
- Run failure: `OperationalException` / `Could not load markets, therefore cannot start. Please investigate the above error for more details.`.
- DNS blocker observed: `dns_error_present=True`, `exchange_info_error_present=True`.

## Root Cause

Auto-Quant status can be data_ready=true from local feather files, but run.py constructs Freqtrade Backtesting with the Binance exchange config. Freqtrade loads Binance markets through CCXT before backtesting, so DNS failure to api.binance.com blocks run.py even when local OHLCV feathers and one active strategy are present.

## Board A Accounting

This is real Auto-Quant runtime evidence, but it is non-promoting. `data_ready=true` is not enough to prove executable Auto-Quant completion because the oracle still tries to load Binance market metadata before backtesting. The earlier `023312` seeded-strategy Auto-Quant run remains historical non-promoting evidence; this packet records the current `064259` state behavior.

Accepted rows added `0`; valid required-root unlock false; source/control evidence acquired false; canonical merge false; downstream promotion rerun false; strict full objective false; trade usable false; `update_goal=false`.

## Next

Do not treat this Auto-Quant run attempt as Board A promotion evidence. Continue from a valid source/control unlock first. Separately, if Auto-Quant runtime closure is needed, the next technical slice should use an offline-safe exchange/market-metadata path or a previously prepared seeded state known to complete `run.py`, then still keep it non-promoting until R3/R5/R6 source/control gates unlock.
