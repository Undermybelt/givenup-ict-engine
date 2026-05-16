# 2026-05-16 Provider Parity Handoff TODO

Owner: Hermes GPT-5.5 CLI
Started: 2026-05-16 22:18 +0800

## Goal

Make Auto-Quant/backtest provider choice match realtime practical-advice provider choice, with zero-config public crypto lanes for Binance and Bybit. Keep the feature hot-pluggable: consumers can keep the yfinance default or explicitly select Binance/Bybit public providers.

## Scope

- Add explicit `binance_public_runtime` and `bybit_public_runtime` live backends.
- Add `binance_public` and `bybit_public` market-data harness provider requests.
- Reuse the existing no-key crypto public runtime path, but preserve the selected exchange as the default source.
- Keep default consumer behavior unchanged: yfinance remains the tradfi default; public exchange lanes are ready/selectable but opt-in.
- Avoid repo pollution: smoke state goes under `/tmp`; commit only this coherent slice.

## User-specific data lanes

- Crypto OHLCV for BTC/ETH/SOL-style symbols on Binance/Bybit public endpoints.
- Intraday intervals relevant to Board A/B and Auto-Quant: `1m`, `5m`, `15m`, `30m`, `1h`, `4h`, `1d`.
- Preserve optional richer lanes: IBKR/TradingView/Hubble/Kraken remain opt-in or provider-specific.

## TODO

- [x] Route and read repo/skill contracts.
- [x] Confirm dirty worktree is broad; stage nothing unrelated.
- [x] Implement exchange-selectable crypto public runtime defaults.
- [x] Add live backend aliases: `binance_public_runtime`, `bybit_public_runtime`.
- [x] Add market-data harness provider request support: `binance_public`, `bybit_public`.
- [x] Run focused unit tests for runtime parsing and harness planning.
- [x] Run provider-status focused checks for Binance/Bybit live and market-data visibility.
- [x] Run a tiny zero-config public fetch smoke if network allows.
- [x] Patch `ict-engine-maintenance-loop` / runtime skill with the provider parity lesson.
- [x] Commit decision recorded: not committed because `src/application/provider_catalog.rs` had pre-existing unrelated dirty hunks before this slice; staging the whole file would risk mixing agents' work.

## Verification

- `cargo test -q parse_crypto_public_source_defaults_to_selected_exchange` -> pass.
- `cargo test -q parse_crypto_public_source_honors_explicit_exchange_prefix` -> pass.
- `cargo test -q plan_supports_public_exchange_provider_symbols` -> pass.
- CLI plan smoke: `market-data-harness --action plan --provider cfd_reference=bybit_public --symbol-spec cfd_reference=BTCUSDT` -> task provider `bybit_public`, request provider `bybit_public`, symbol `BTCUSDT`.
- `cargo run --quiet -- provider-status --provider binance_public --agent` -> `market_data:1/1 ready`, no install prompts.
- `cargo run --quiet -- provider-status --provider bybit_public --agent` -> `market_data:1/1 ready`, no install prompts.
- `cargo run --quiet -- provider-status --provider bybit_public_runtime --agent` -> `live_runtime:1/1 ready`, no install prompts.
- Bybit public harness smoke: `BTCUSDT`, `1h`, `rows=1000`, `ok=True`.
- Binance public harness smoke: `ETHUSDT`, `1h`, `rows=1000`, `ok=True`.

## Design notes

- Backtest/provider harness and realtime advice can now use the same exchange family:
  - harness: `--provider cfd_reference=bybit_public --symbol-spec cfd_reference=BTCUSDT`
  - realtime: `--futures-backend bybit_public_runtime --futures-symbol BTCUSDT`
- Prefixes still override defaults: `bybit:BTCUSDT`, `binance:ETHUSDT`, `hyperliquid:BTC`.
- The public exchange runtime is no-login and no API key. It must not become a required default for tradfi users.

## Current blocker log

- Broad unrelated dirty worktree exists before this slice. Do not clean or revert it.
- `patch` lint invokes standalone `rustc` without Cargo edition and reports pre-existing `async fn` Rust 2015 errors for `crypto_public_runtime.rs`; use Cargo tests for real verification.
