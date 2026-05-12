# AutoQuant No-AioDNS Prepare Workaround After 033216 v1

Run id: `20260512T033524-codex-autoquant-noaiodns-prepare-workaround-after-033216-v1`

Gate result: `autoquant_noaiodns_prepare_workaround_after_033216_v1=prepare_succeeded_but_noaiodns_uninstall_failed_state_already_data_ready_no_promotion`

## Readback

- `uv pip uninstall aiodns -y` exit code: `2`; error was the unsupported `-y` argument.
- Import check exit code: `0`; `aiodns` still importable: `true`.
- `auto-quant-prepare` exit code: `0`; prepare status `prepared`; data ready `True`.
- Status after exit code: `0`; status `dependency_ready_seed_required`; healthy `True`; data ready `True`.

## Decision

The no-aiodns uninstall did not actually remove aiodns, but the prepare command exited 0 because the isolated Auto-Quant state was already data-ready/dependency_ready_seed_required. This is runtime-readiness corroboration only, not Board A acceptance.

- Accepted rows added: `0`
- New confidence gate: `false`
- Canonical merge allowed: `false`
- Downstream promotion rerun allowed: `false`
- Strict full objective achieved: `false`
- Trade usable: `false`
- `update_goal=false`

## Next

Continue Board A only from source/control unlock. Auto-Quant runtime follow-up may seed active strategies in isolated state, but cannot promote without verifier rerun and downstream chain.

## Artifacts

- JSON: `docs/experiments/actionable-regime-confidence/runs/20260512T033524-codex-autoquant-noaiodns-prepare-workaround-after-033216-v1/autoquant-noaiodns-prepare-workaround-after-033216-v1/autoquant_noaiodns_prepare_workaround_after_033216_v1.json`
- CSV: `docs/experiments/actionable-regime-confidence/runs/20260512T033524-codex-autoquant-noaiodns-prepare-workaround-after-033216-v1/autoquant-noaiodns-prepare-workaround-after-033216-v1/autoquant_noaiodns_prepare_workaround_after_033216_v1.csv`
