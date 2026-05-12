# AutoQuant Threaded Resolver Workaround Run v1

Run id: `20260512T033430-codex-autoquant-threaded-resolver-workaround-run-v1`

Gate result: `autoquant_threaded_resolver_workaround_run_v1=prepare_retry_failed_aiodns_loopback_no_promotion`

## Readback

- Inferred exit code: `1`.
- `aiodns` DNS failure observed: `true`.
- Binance exchange load failure observed: `true`.
- The prepare retry still did not make Auto-Quant data ready.

## Decision

The prepare retry still failed while loading Binance markets through the aiohttp/aiodns path. It does not make Auto-Quant data ready and cannot support Board A promotion while source/control gates remain closed.

- Accepted rows added: `0`
- New confidence gate: `false`
- Canonical merge allowed: `false`
- Downstream promotion rerun allowed: `false`
- Strict full objective achieved: `false`
- Trade usable: `false`
- `update_goal=false`

## Next

If this lane is reopened, test the resolver workaround inside the isolated environment more directly. Even if data prep succeeds later, Board A still needs source/control unlock and full downstream rerun before acceptance.

## Artifacts

- JSON: `docs/experiments/actionable-regime-confidence/runs/20260512T033430-codex-autoquant-threaded-resolver-workaround-run-v1/autoquant-threaded-resolver-workaround-run-v1/autoquant_threaded_resolver_workaround_run_v1.json`
- CSV: `docs/experiments/actionable-regime-confidence/runs/20260512T033430-codex-autoquant-threaded-resolver-workaround-run-v1/autoquant-threaded-resolver-workaround-run-v1/autoquant_threaded_resolver_workaround_run_v1.csv`
