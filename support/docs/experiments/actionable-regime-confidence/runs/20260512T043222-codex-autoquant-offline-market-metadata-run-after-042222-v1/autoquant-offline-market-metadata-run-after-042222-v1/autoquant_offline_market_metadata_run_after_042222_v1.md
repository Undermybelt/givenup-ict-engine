# AutoQuant Offline Market Metadata Run After 042222 v1

Run id: `20260512T043222-codex-autoquant-offline-market-metadata-run-after-042222-v1`

Gate result: `autoquant_offline_market_metadata_run_after_042222_v1=offline_metadata_backtests_succeeded_no_source_control_promotion`

## Result

- AutoQuant root: `/tmp/ict-engine-board-a-autoquant-local-cache-20260512T022826/auto-quant/.deps/auto-quant`.
- Mode: offline market metadata injected into Freqtrade Exchange; AutoQuant `run.py` and `config.json` were not edited.
- Successful backtests: `3`; failed backtests: `0`.
- This proves the prior Binance metadata/DNS blocker can be bypassed for local cached BTC strategies, but it is still non-promoting until source/control gates pass.
- Accepted rows added `0`; new confidence gate `false`; strict full objective `false`; trade usable `false`; `update_goal=false`.

## Strategies

| Strategy | Timerange | Status | Trades | Sharpe | Profit % | Win % |
|---|---|---|---:|---:|---:|---:|
| `BTCLeaderBreakV4BTCOnly` | `20210101-20251231` | `OK` | 116 | 0.2464 | 14.8100 | 35.3448 |
| `MTFTrendStackBTCOnly` | `20210101-20251231` | `OK` | 150 | -0.0796 | -4.2700 | 22.0000 |
| `MomentumMTFConfluenceBTCOnly` | `20210101-20251231` | `OK` | 169 | 0.0411 | 2.8600 | 30.7692 |

## Boundary

This is an AutoQuant runtime/readiness repair probe. It is not accepted regime-confidence evidence, source/control evidence, canonical merge input, downstream promotion evidence, or trade evidence.

## Artifacts

- JSON: `/Users/thrill3r/projects-ict-engine/ict-engine/docs/experiments/actionable-regime-confidence/runs/20260512T043222-codex-autoquant-offline-market-metadata-run-after-042222-v1/autoquant-offline-market-metadata-run-after-042222-v1/autoquant_offline_market_metadata_run_after_042222_v1.json`
- Command output: `/Users/thrill3r/projects-ict-engine/ict-engine/docs/experiments/actionable-regime-confidence/runs/20260512T043222-codex-autoquant-offline-market-metadata-run-after-042222-v1/command-output/offline_market_metadata_run.stdout.txt`
- Assertions: `/Users/thrill3r/projects-ict-engine/ict-engine/docs/experiments/actionable-regime-confidence/runs/20260512T043222-codex-autoquant-offline-market-metadata-run-after-042222-v1/checks/autoquant_offline_market_metadata_run_after_042222_v1_assertions.out`
