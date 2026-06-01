# Board A/B handoff audit pattern

Use when another agent leaves ict-engine Board A/B or provider-runtime work half-done and the user asks to audit, continue, or commit it.

## Audit sequence

1. Route and read repo-local rules first.
2. Read the Board A/B plan files and any provider parity handoff docs before editing.
3. Run Rust verification before trusting written claims:
   - `cargo fmt --check && cargo check -q`
   - `cargo test -q`
4. If tests fail, treat stale assertions as likely drift from new evidence surfaces; patch assertions only after reading the runtime output and adjacent code path.
5. Run Python support tests with repo script paths on `PYTHONPATH` and ephemeral deps through `uv`, for example:
   - `PYTHONPATH=support/scripts:support/scripts/research:support/scripts/auto_quant_external uv run --with pytest --with pandas --with pyarrow python -m pytest -q support/scripts/research/tests support/scripts/auto_quant_external/tests`
6. Before staging, inventory untracked outputs by directory and size. Do not commit generated run trees.
7. If `support/docs/experiments/actionable-regime-confidence/runs/` contains large generated evidence, ignore or selectively archive summaries only.
8. Commit only a coherent slice: source, tests, curated docs/examples/scripts; leave huge run artifacts and unrelated multi-agent work unstaged.

## Reusable findings

- Board plan text can overstate achieved confidence. Distinguish evidence scaffold from proven 95% regime confidence.
- Provider `ready` status is not data parity. Require concrete fetch/backtest/readback evidence for practical trading claims.
- Regime-rooted profit-factor branching is valid only when branch path survives export, trainer artifact, workflow status, and execution-tree/readback tests.
- For abandoned multi-agent work, final claim should say what is production-usable, what is shadow/paper-only, and what remains unverified.
