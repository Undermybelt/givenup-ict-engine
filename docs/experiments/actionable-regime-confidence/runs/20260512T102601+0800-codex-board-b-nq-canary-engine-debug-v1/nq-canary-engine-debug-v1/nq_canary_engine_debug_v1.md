# NQ Canary Engine Debug v1

Run root: `docs/experiments/actionable-regime-confidence/runs/20260512T102601+0800-codex-board-b-nq-canary-engine-debug-v1`

## Scope

This packet diagnoses why provider-owned NQ/USD Auto-Quant strategies keep backtesting with zero trades even when strategy methods report entry signals. It is diagnostic evidence only. It does not accept a regime packet, approve source/control evidence, select history, mutate canonical intake, promote Auto-Quant, promote BBN/CatBoost/path-ranking/execution-tree output, make a trade claim, or authorize `update_goal`.

## Inputs

- Source workspace copied from `docs/experiments/actionable-regime-confidence/runs/20260512T102332+0800-codex-board-b-provider-yf-nq-trendpulse-aq-v1/workspace/auto-quant-yf-nq-trendpulse`
- Pair: `NQ/USD`
- Data: provider-owned Yahoo NQ 1h/4h/1d feathers from the copied workspace
- Added diagnostic strategy: `ProviderNqModuloCanary.py`

## Evidence

| Check | Exit | Finding |
| --- | ---: | --- |
| `00_run_modulo_canary` | 0 | default TOMAC/Freqtrade config ran 4 strategies; all had `0` trades |
| `01_run_modulo_canary_market_orders` | 1 | market-order config was rejected until `entry_pricing.price_side="other"` |
| `02_run_modulo_canary_market_orders_price_side_other` | 0 | market-order config ran 4 strategies; all still had `0` trades |
| `05_direct_strategy_signal_counts` | 0 | direct strategy method calls emit entry signals on the same data |

Direct strategy signal counts on `11,086` rows:

| Strategy | Enter Signals | Exit Signals | Overlap | Entries After 2024-06-10 |
| --- | ---: | ---: | ---: | ---: |
| `ProviderNqAlwaysInDiagnostic` | 11,086 | 0 | 0 | 10,969 |
| `ProviderNqModuloCanary` | 450 | 443 | 0 | 445 |
| `ProviderNqSampledPulse` | 130 | 4,435 | 0 | 128 |
| `ProviderNqTrendPulse` | 3,080 | 5,011 | 0 | 3,069 |

## Diagnosis

Fact:

- The provider-owned NQ data is readable and spans `2024-06-02 22:00:00+00:00` to `2026-05-11 23:00:00+00:00`.
- Strategy method calls produce nonzero `enter_long` signals, including a forced-entry diagnostic strategy with `11,086` entries.
- Freqtrade/TOMAC backtesting reports `0` trades and `0` enter-tag entries under both the original limit-order config and a validator-corrected market-order config.

Current root-cause boundary:

- The blocker is not insufficient NQ provider data.
- The blocker is not the high-level factor condition being too strict.
- The blocker is between TOMAC/Freqtrade signal handoff and Freqtrade trade-entry execution for synthetic `NQ/USD` provider data.

## Decision

Gate result: `nq_canary_engine_debug_v1=signals_exist_freqtrade_entry_execution_zero_trade_no_promotion`.

Accepted rows added `0`; mature rooted branch observations added `0`; every-regime 95%-99% objective false; cross-context full validation false; explicit selected-history false; source/control evidence acquired false; canonical merge false; selected-data AutoQuant promotion false; downstream promotion false; strict full objective false; trade usable false; promotion allowed false; and `update_goal=false`.

## Next

Do not spend another loop merely tightening NQ entry conditions. The next useful slice is a targeted TOMAC/Freqtrade wrapper diagnostic or fix for synthetic `NQ/USD` entry execution, or a different provider-owned input/strategy that can prove nonzero mature observations without the synthetic-NQ execution path.
