# External data source hotplug provider integration

Reusable pattern for adding optional external data sources to ict-engine as hotplug providers.

## Bridge script pattern (`support/scripts/research/<name>_hotplug.py`)

Three modes, zero-config by default:

| Mode | Flags | Network | Dependency | Output |
|---|---|---|---|---|
| Capability | `--capabilities` | No | No | source metadata, personal defaults, install hint |
| Demo | `--demo` | No | No | embedded fixture rows |
| Fetch | `--source <src> --symbol <sym>` | Yes | Yes | real provider data |

Every output JSON carries:
- `ok: bool`
- `bridge: "<name>_hotplug"`
- `trade_usable: false`
- `data_grade`: `"fixture_only"` | `"observation_or_backtest_reference"`
- `provenance`: `{provider, network: bool, dependency_required: bool}`
- `capability`: source-specific metadata
- Error: `{category, message, retryable}` with categories: `validation`, `config`, `api`, `rate_limit`, `parse`

Output contract: stdout compact JSON always; optional `--output <path>` for file write; never writes to repo root.

## Provider-status wiring (`provider_catalog.rs`)

1. Add provider ID to `provider_filter_matches_domain` match arm for the target domain.
2. Add `fn <name>_provider_item() -> ProviderCatalogItem`:
   - Probe `script_present` (file exists at CARGO_MANIFEST_DIR path)
   - Probe `python_present` (python3_exists)
   - Probe `module_present` (optional importlib.util.find_spec via command_output_with_timeout)
   - `ready = script_present && python_present`
   - Status: `ready` (module present), `ready_degraded` (module optional missing), `install_required` (script/python missing)
   - `selectable_by_user: true`, `adopted_by_default: false`
   - `install_prompts` only for degraded/required states
3. Extend `collect_items()` in `MarketDataProviderCatalogSource` to include the new item.
4. Set `market_fit`, `fallback_priority`, `capabilities`, `notes` inline.

## Tests

Python side:
- `test_capabilities_are_zero_config_and_opt_in` — capability bundle has ok/zero_config/trade_usable false/sources/defaults
- `test_demo_mode_returns_embedded_rows_without_dependency` — demo fixture, no network
- `test_fetch_mode_without_symbol_fails_as_validation` — missing symbol = validation error
- `test_main_writes_explicit_output_path_only` — --output writes file + stdout

Rust side:
- Verify provider-filter test covers the new ID in MarketData domain
- Verify `provider-status --provider <id> --agent` returns correct surface

## Verification checklist

```bash
python3 -m unittest support.scripts.research.tests.test_<name>_hotplug
cargo test provider_catalog::tests
cargo run --quiet -- provider-status --compact 2>/dev/null | grep <provider_id>
cargo run --quiet -- provider-status --provider <provider_id> --agent 2>/dev/null | head -5
```

## Pitfalls

- Do not make the bridge a required dependency or adopted_by_default.
- Do not let fetch mode run without explicit --source; capability/demo must work without the package.
- Do not write output to repo root; stdout or explicit --output only.
- Do not skip the provenance/network/dependency_required fields — downstream gates depend on them.
- Do not claim trade_usable=true for any bridge output; observation/reference only until ict-engine gates pass.
