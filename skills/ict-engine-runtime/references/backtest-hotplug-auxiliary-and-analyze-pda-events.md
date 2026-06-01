# Backtest hotplug + auxiliary; analyze PDA event closure

Session learning from completing ICT-Engine runtime closure around factor backtest and analyze.

## Implementation pattern

### factor-backtest CLI/runtime

`factor-backtest` must not lag behind `factor-research` / `analyze` runtime surfaces.

Required wiring:
- CLI accepts all MTF paths already present in the enum: `--data-1m`, `--data-5m`, `--data-15m`, `--data-1h`, `--data-4h`, `--data-1d`.
- CLI accepts `--auxiliary-evidence <json>` using the same schema as factor-research:
  - direct `AuxiliaryMarketEvidence` JSON
  - wrapped analyze report JSON at `supporting.auxiliary` or `auxiliary`
  - ready `event-fundamentals-adoption/v1` sidecar bundle, only when
    `artifact_readiness.profile_contract_ready=true` and
    `downstream_handoff.allowed_use_modes` includes `factor_research_opt_in`;
    incomplete bundles must fail closed instead of becoming live bias input.
- `factor_backtest_shell` loads auxiliary once, then captures it in the runner closure passed to `factor_backtest_command`.
- `run_factor_backtest` signature should carry MTF paths and `Option<&AuxiliaryMarketEvidence>`.
- `run_factor_backtest` calls:
  - `resolve_multi_timeframe_inputs(data, data_1m, data_5m, data_15m, data_1h, data_4h, data_1d)`
  - `build_structure_ict_context_events(&resolved_multi_timeframe_inputs)`
  - `FactorHotplugConfig::apply_to_registry_if_present(state_dir, &mut registry)` before `FactorLab::new(registry)`
  - `FactorContext { paired_candles, h4_events, d1_events, w1_events, auxiliary, regime_v2_labels, ... }`

### analyze FactorContext PDA events

`analyze` cannot rely only on report-level PDA artifacts; `FactorContext` must receive structure ICT context too.

Pattern:
- Build `StructureIctContextEvents` from `AnalyzeNativeFrames` inside `build_analyze_report`.
- `h4_events`: `native_frames.h4` -> `build_pda_timeline(candles, compute_atr(candles, 14))`
- `d1_events`: `native_frames.d1` -> same
- `w1_events`: aggregate D1 candles to weekly, then build PDA timeline.
- Pass these into `FactorEngine::run(..., &FactorContext { h4_events, d1_events, w1_events, ... })`.

## Verification commands

Compile:
```bash
cargo check
```

Targeted tests that avoid known slow integration sweep:
```bash
cargo test --bin ict-engine test_run_factor_backtest -- --nocapture
cargo test --test execution_tree_axial_gate --test hard_gate_execution_first -- --nocapture
```

Behavior probes:
```bash
# Hotplug disabled: options_hedging must disappear from scorecards.
mkdir -p /tmp/ict-factor-backtest-hotplug
cat > /tmp/ict-factor-backtest-hotplug/factor_hotplug.yaml <<'YAML'
families:
  options_hedging: false
YAML
./target/debug/ict-engine factor-backtest \
  --symbol NQ \
  --data examples/demo/demo-15m.json \
  --data-4h examples/demo/demo-15m.json \
  --data-1d examples/demo/demo-15m.json \
  --auxiliary-evidence /tmp/ict-factor-backtest-aux.json \
  --state-dir /tmp/ict-factor-backtest-hotplug \
  --compact

# No hotplug: options_hedging should appear when auxiliary evidence is supplied.
rm -rf /tmp/ict-factor-backtest-aux-only
./target/debug/ict-engine factor-backtest \
  --symbol NQ \
  --data examples/demo/demo-15m.json \
  --data-4h examples/demo/demo-15m.json \
  --data-1d examples/demo/demo-15m.json \
  --auxiliary-evidence /tmp/ict-factor-backtest-aux.json \
  --state-dir /tmp/ict-factor-backtest-aux-only \
  --compact

# Analyze should expose market_state evidence and PDA artifact action summary.
./target/debug/ict-engine analyze \
  --symbol NQ \
  --data-htf examples/demo/demo-15m.json \
  --data-mtf examples/demo/demo-15m.json \
  --data-ltf examples/demo/demo-15m.json \
  --state-dir /tmp/ict-analyze-mtf-pda-json
```

## Pitfalls

- `cargo check` does not compile `#[cfg(test)]` paths. After changing public/test-initialized structs or function signatures, run targeted `cargo test --bin ...` and relevant `--test ...` suites.
- `cargo test test_run_factor_backtest` without `--bin ict-engine` can still launch unrelated integration tests; in this repo it may hang/time out in `hmm_recovery_regression` despite target unit tests passing.
- `cargo fmt --check` may fail due to existing repo-wide formatting drift; do not confuse this with a compile failure from the runtime closure patch.
- Adding fields to `ExecutionTreeInput` or `AnalyzeRunRecord` requires updating both unit tests and integration tests outside the touched module.
- When proving hotplug, compare scorecards with and without `<state-dir>/factor_hotplug.yaml`; compile success alone does not prove runtime closure.
