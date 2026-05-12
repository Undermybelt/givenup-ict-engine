# 103437 / 103450 Provider Diagnostic Intake v1

Run id: `20260512T104920+0800-codex-103437-103450-provider-diagnostic-intake-v1`

Purpose: count-once intake for unregistered provider/AQ diagnostics without editing their source run roots.

## Source Roots

- `103437`: `docs/experiments/actionable-regime-confidence/runs/20260512T103437+0800-codex-board-b-yahoo-crypto-momentum-market-aq-v1`
- `103450`: `docs/experiments/actionable-regime-confidence/runs/20260512T103450+0800-codex-board-b-provider-yf-nq-tickfix-rerun-v1`

## Readback

`103437` completed the provider-owned Yahoo crypto TOMAC run with `2` succeeded strategies and `0` failed strategies. The two later scan commands were killed as slow scans and are not promotion evidence.

| Source | Strategy | Trades | Total Profit % | Sharpe | Win Rate % | Profit Factor | Gate |
|---|---|---:|---:|---:|---:|---:|---|
| `103437` | `ProviderCryptoMomentumStateV1` | 295 | -18.73 | -1.0287 | 34.9153 | 0.7350 | `fail_closed:unprofitable` |
| `103437` | `ProviderCryptoPullbackRevertV1` | 109 | -7.08 | -0.4663 | 40.3670 | 0.6898 | `fail_closed:unprofitable` |
| `103450` | `ProviderNqAlwaysInDiagnostic` | 2782 | -61.30 | -5.4536 | 29.3314 | 0.6067 | `fail_closed:diagnostic_always_in_unprofitable` |
| `103450` | `ProviderNqSampledPulse` | 18 | 0.97 | 0.1898 | 33.3333 | 5.3246 | `fail_closed:profitable_but_probe_only_trade_count_18` |
| `103450` | `ProviderNqTrendPulse` | 896 | -38.10 | -3.3038 | 37.7232 | 0.5912 | `fail_closed:dense_provider_nq_strategy_unprofitable` |

`103450` first captured the copied TOMAC config failure (`exit_pricing.price_side=same` with market exits), then repaired the run-local copied config to `other` and exited `0`. The repair confirms the NQ entry-wire issue was execution translation, not lack of signals, but the result remains diagnostic-only.

## Gates

- `103437`: `yahoo_crypto_momentum_market_aq_v1=nonzero_crypto_market_trades_unprofitable_slow_scans_killed_no_promotion`
- `103450`: `provider_yf_nq_tickfix_rerun_v1=entry_wire_repaired_nonzero_trades_no_promotion`

## Non-Promotion

- Accepted rows added: `0`
- Mature rooted branch observations added: `0`
- Source/control evidence acquired: `false`
- Explicit selected-history: `false`
- Canonical merge: `false`
- Selected-data AutoQuant promotion: `false`
- Downstream promotion: `false`
- Strict full objective: `false`
- Trade usable: `false`
- Promotion allowed: `false`
- `update_goal=false`

## Next

Do not repeat these provider crypto/NQ diagnostic shapes. Continue from source/control unlock, explicit selected-history approval, or a materially different provider-owned branch-specific recipe with enough mature rooted observations and ordered downstream readback.
