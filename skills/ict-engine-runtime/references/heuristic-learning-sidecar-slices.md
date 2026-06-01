# Heuristic Learning sidecar slices

Use when continuing `docs/plans/2026-05-09-heuristic-learning-execution-todo.md` or similar ICT-Engine self-iteration work.

## Pattern

Keep the learning chain sidecar-first until an artifact proves consumer value:

1. Write a failing unittest under `scripts/research/tests/`.
2. Add a zero-config Python sidecar under `scripts/research/`.
3. Add a handoff TODO under `docs/plans/` with input/output contract and verification commands.
4. Run the target test, then full research tests:
   - `python3 -m unittest scripts/research/tests/<test_file>.py -v`
   - `python3 -m unittest discover -s scripts/research/tests -p 'test_*.py'`
5. Commit only the slice files; ignore unrelated dirty Rust/runtime files unless they directly block the slice.
6. If the master TODO needs the resulting commit hash, prefer a follow-up docs commit rather than amending.

## Completed sidecar modules from this chain

- `bbn_evidence_value_report.py`
  - Decides whether BBN edges deserve promotion by `posterior_entropy_delta`, `logloss_delta`, `contradiction_lift`, `accepted_edges`, `rejected_edges`.
  - Negative entropy/logloss deltas are improvements.
- `payoff_to_path_ranker_target.py` risk utility extension
  - Adds `risk_adjusted_path_utility = realized_R - mae_penalty - time_penalty + regime_confidence_bonus - slippage_penalty`.
  - Keeps raw `realized_R` for audit/fallback.
- `factor_formula_library.py`
  - Hot-pluggable seed pool with `seed_id`, `family`, `source`, `expression`, `required_fields`, `default_params`, `allowed_regimes`, `mutation_hints`, `hotplug_ready`.
  - Includes Qlib/Alpha101-style skeletons plus ICT/VRP/crowding seeds.
- `paper2code_adapters.py`
  - Sidecar reports for `rammstein_ou_reversion`, `crowded_trades_pressure`, `kyle_liquidity_slippage`, `red_queens_friction`.
  - Emits `execution_hint`, `max_risk_score`, and per-adapter `bbn_evidence_hint`.
- `heuristic_payoff_pipeline.py` sidecar closure integration
  - Runs formula library + paper2code adapter report from the zero-config payoff pipeline and returns `sidecar_closure`.
  - Optionally runs BBN evidence value when profile has `bbn_evidence_rows_jsonl`.
  - Writes `factor_formula_library.json`, `paper2code_adapter_report.json`, and optionally `bbn_evidence_value_report.json` into the caller-selected output dir.

## Closure audit pattern

After finishing independent sidecar slices, run a closure audit before claiming the chain is integrated:

1. Re-run `python3 -m unittest discover -s scripts/research/tests -p 'test_*.py'`.
2. Verify `python3 -m py_compile scripts/research/*.py`.
3. Check that the single user-facing entrypoint emits all new sidecar artifacts, not just that each module has its own CLI.
4. If the entrypoint is missing, add a failing pipeline test first, then integrate sidecars into `heuristic_payoff_pipeline.py` or the equivalent orchestrator.
5. Keep optional evidence inputs hot-pluggable through profile fields; do not force runtime/Rust changes until sidecar artifacts prove consumer value.

## Pitfalls

- Do not touch dirty Rust files for sidecar slices unless the sidecar cannot satisfy the consumer contract.
- Do not claim a sidecar is runtime-integrated just because it exists; prove the next consumer reads it.
- If `apply_patch` is not available in the shell, use Hermes `patch`; do not fall back to ad-hoc file rewrites.
- Keep output artifacts under caller-selected dirs; never write generated research state into repo root.
