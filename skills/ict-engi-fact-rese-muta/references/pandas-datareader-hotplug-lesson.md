# pandas-datareader hotplug lesson — 2026-05-20

Reusable pattern for adding optional external data bridges to ict-engine without polluting zero-config or breaking consumer workflows.

## Pattern

1. Support script defaults to capability/demo JSON output; no network, no external package required.
2. `--capabilities` prints source metadata, personal default sets, and install hint in compact JSON.
3. `--demo` prints embedded fixture rows; proves bridge works without pandas-datareader installed.
4. `--source <src> --symbol <sym>` does real network fetch; requires explicit opt-in + optional dependency.
5. Every output has `trade_usable=false`, `data_grade`, and `provenance` with `network` and `dependency_required` booleans.
6. Error categories: `validation`, `config`, `api`, `rate_limit`, `parse`.
7. Output always goes to stdout (compact JSON) or explicit `--output` path; never writes to repo root.

## Provider-status integration

- Add new provider to `provider_filter_matches_domain` match arm.
- Add a dedicated `*_provider_item()` function returning `ProviderCatalogItem` with:
  - `selectable_by_user: true`
  - `adopted_by_default: false`
  - Probe `script_present`, `python_present`, `module_present` via timeout-guarded `Command` probes.
  - Report `ready` / `ready_degraded` / `install_required` based on script + python + module status.
  - `install_prompts` only for degraded/required; never block zero-config.
- Call `apply_provider_user_semantics(item)` if semantic override needed, or set fields inline.

## Gate rule

Every imported provider lands in observation/backtest/reference lane by default. Never bypass existing Gate 1 / cost / Pre-Bayes / BBN / CatBoost / execution-tree checks.

## Verification evidence

- Python tests: `python3 -m unittest support.scripts.research.tests.test_pandas_datareader_hotplug` → 4/4 pass
- Rust test: `cargo test provider_catalog::tests::tradingview_mcp_provider_filter_uses_market_data_catalog` → 1 pass
- Runtime: `provider-status --compact` shows `pandas_datareader` in market_data ready set
- Bridge: `--capabilities` → ok=True/zero_config=True/sources=4/defaults=5
- Bridge: `--demo` → ok=True/grade=fixture_only/rows=3/net=False
