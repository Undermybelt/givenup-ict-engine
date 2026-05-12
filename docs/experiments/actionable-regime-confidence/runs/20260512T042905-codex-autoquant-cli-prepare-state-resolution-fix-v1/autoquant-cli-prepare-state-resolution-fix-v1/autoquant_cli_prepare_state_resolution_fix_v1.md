# Auto-Quant CLI Prepare State Resolution Fix v1

Timestamp: `2026-05-12T04:29:05+0800`

Scope: CLI plumbing repair for the Board B `032157/downstream-combined-v1` Auto-Quant prepare/status follow-up path. This is not a historical-data selection, not a profitability packet, not a downstream promotion check, and not a Current Cursor update.

## Root Cause

Two independent CLI issues were observed from the completed sidecar outputs:

- `auto-quant-prepare --state-dir <handoff-state>` resolved to `<handoff-state>/auto-quant` even when `<handoff-state>` already contained a factor-research handoff workspace at `.deps/auto-quant`.
- When the workspace state was forced back to the handoff state, `auto_quant_prepare_workspace_command` changed the child process working directory to the Auto-Quant repo root while still passing repo-root-relative script paths, so `uv` looked for a nested path and failed to spawn `prepare.py`.

## Code Changes

- `src/auto_quant_command.rs`: preserve an existing handoff state when `auto_quant_config.json` or `.deps/auto-quant` is present; keep the isolated `<state>/auto-quant` default for fresh states; keep `ICT_ENGINE_AUTO_QUANT_OUTPUT_DIR` override precedence.
- `src/application/auto_quant/command_entry.rs`: resolve the workspace root and prepare script path to absolute paths before changing the child process working directory.

## Verification

- `CARGO_TARGET_DIR=/tmp/ict-engine-codex-auto-quant-prepare-target cargo test aq_state_dir --bin ict-engine`
  - Result: `3 passed; 0 failed; 238 filtered out`.
- `CARGO_TARGET_DIR=/tmp/ict-engine-codex-auto-quant-prepare-target cargo test auto_quant_prepare --lib`
  - Result: `2 passed; 0 failed; 928 filtered out`.
- `CARGO_TARGET_DIR=/tmp/ict-engine-codex-auto-quant-prepare-target cargo build --bin ict-engine`
  - Result: build succeeded.
- `/tmp/ict-engine-codex-auto-quant-prepare-target/debug/ict-engine auto-quant-status --state-dir docs/experiments/actionable-regime-confidence/runs/20260512T032157-codex-board-b-nq-cost-crisis-repair-v3/downstream-combined-v1/state_combined_v1 --human`
  - Result: `dependency_ready_data_ready`, `dependency_healthy=true`, `data_ready=true`, with `auto_quant_profile=synthetic_ohlcv`.

## Gate

- `pass:cli_state_resolution_and_prepare_script_path_regression_covered`.
- `blocked:user_selected_historical_data_missing`.
- `not_started:no_new_factor_research_or_downstream_promotion_check`.

## Next

Keep `034002` as the fail-closed cursor. The next Board B move still requires explicit user selection of exactly one historical data option before running factor-research/Auto-Quant for promotion evidence.
