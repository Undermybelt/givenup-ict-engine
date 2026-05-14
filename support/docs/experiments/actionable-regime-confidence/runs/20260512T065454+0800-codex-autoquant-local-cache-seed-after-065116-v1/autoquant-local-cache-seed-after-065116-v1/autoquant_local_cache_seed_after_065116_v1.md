# AutoQuant Local Cache Seed After 065116 v1

Run id: `20260512T065454+0800-codex-autoquant-local-cache-seed-after-065116-v1`

Gate result: `autoquant_local_cache_seed_after_065116_v1=local_cache_seeded_data_ready_no_source_control_unlock_no_promotion`

## Result

- Local data source: `/Users/thrill3r/Auto-Quant/user_data/data`
- Local data files seen: `54`
- Managed data files after seed: `54`
- Managed strategy files after seed: `TomacNQ_KillzoneBreakout.py`
- `auto-quant-status` after local-cache seed exited `0`.
- Status after seed: `dependency_ready_data_ready`
- Healthy: `true`
- Data ready: `true`

## Board A Accounting

- Accepted rows added: `0`
- Valid required-root unlock: `false`
- Source/control evidence acquired: `false`
- Canonical merge: `false`
- Downstream promotion rerun: `false`
- Strict full objective: `false`
- Trade usable: `false`
- `update_goal=false`

## Artifacts

- Status stdout: `docs/experiments/actionable-regime-confidence/runs/20260512T065454+0800-codex-autoquant-local-cache-seed-after-065116-v1/command-output/auto_quant_status_after_local_cache_seed.stdout`
- Seed data command: `docs/experiments/actionable-regime-confidence/runs/20260512T065454+0800-codex-autoquant-local-cache-seed-after-065116-v1/command-output/seed_local_data_cache.cmd`
- Seed strategy command: `docs/experiments/actionable-regime-confidence/runs/20260512T065454+0800-codex-autoquant-local-cache-seed-after-065116-v1/command-output/seed_external_strategies.cmd`
- JSON: `docs/experiments/actionable-regime-confidence/runs/20260512T065454+0800-codex-autoquant-local-cache-seed-after-065116-v1/autoquant-local-cache-seed-after-065116-v1/autoquant_local_cache_seed_after_065116_v1.json`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260512T065454+0800-codex-autoquant-local-cache-seed-after-065116-v1/checks/autoquant_local_cache_seed_after_065116_v1_assertions.out`

## Next

Auto-Quant is data-ready in the isolated state, but Board A promotion remains blocked until a valid source/control unlock appears. After a valid unlock, rerun the required chain in order and include Auto-Quant `run.py` output as non-proxy evidence.
