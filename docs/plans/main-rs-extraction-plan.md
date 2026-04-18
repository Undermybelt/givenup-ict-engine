# main.rs extraction plan

Status: release-adjacent structural debt, non-blocking.

Goals
- shrink `src/main.rs`
- move stable command surfaces into focused modules
- preserve CLI behavior and release output compatibility

Stage 1
- extract analyze output helpers
- target: `emit_analyze_output`, `emit_analyze_live_output`, human/compact/agent render assembly
- home: `src/application/reporting/` or `src/application/cli_output/`

Stage 2
- extract workflow-status output helpers
- target: compact/agent/human workflow views, redaction-print boundary
- home: `src/application/orchestration/`

Stage 3
- extract analyze/backtest/update command input parsing helpers
- move command-specific resolution logic out of main match arms
- keep clap enum in `main.rs` until later stage

Stage 4
- extract test helpers from `src/main.rs`
- move reusable fixtures like `sample_candles` and CLI fixture builders into dedicated test modules

Guardrails
- one surface at a time
- preserve serialized field names unless release note says otherwise
- after each extraction run `cargo check` and targeted tests first, then broader suite
- avoid mixing feature work with structural moves

Release note
- do not block current release on this plan alone
- if a post-release cleanup branch is opened, start with Stage 1 because analyze output logic is already conceptually grouped
