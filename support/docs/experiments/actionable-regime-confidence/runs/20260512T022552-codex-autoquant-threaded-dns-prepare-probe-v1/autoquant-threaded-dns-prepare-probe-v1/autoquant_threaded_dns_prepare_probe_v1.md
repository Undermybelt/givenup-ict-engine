# Auto-Quant Threaded DNS Prepare Probe v1

Run root: `docs/experiments/actionable-regime-confidence/runs/20260512T022552-codex-autoquant-threaded-dns-prepare-probe-v1`

Purpose: test whether the `021808` Auto-Quant prepare blocker was specifically caused by aiohttp's async DNS resolver by forcing bounded probes to use `ThreadedResolver` through `PYTHONPATH` only.

Scope:
- Initial isolated Auto-Quant state: `/tmp/ict-engine-board-a-autoquant-bootstrap-20260512T021808`
- Settled threaded-DNS state: `/tmp/ict-engine-board-a-autoquant-threaded-dns-20260512T022552`
- Managed Auto-Quant checkout: `/tmp/ict-engine-board-a-autoquant-threaded-dns-20260512T022552/auto-quant/.deps/auto-quant`
- Probe shim: `scripts/sitecustomize.py`
- Runtime code changed: false
- Managed Auto-Quant checkout changed: false
- Shared intake/source roots changed: false

Command evidence:
- Initial exchange-info probe: `command-output/00_threaded_dns_exchangeinfo_probe.*`
- Connector-patched exchange-info probe: `command-output/01_threaded_dns_exchangeinfo_probe_connector_patch.*`
- Status before prepare: `command-output/02_status_before_threaded_prepare.*`
- Threaded-DNS prepare: `command-output/03_auto_quant_prepare_threaded_dns.*`
- Status after prepare: `command-output/04_status_after_threaded_prepare.*`

Result:
- Initial resolver-only probe exit: `1`; decisive error was `Cannot connect to host api.binance.com:443 ssl:default [Could not contact DNS servers]`.
- Connector-patched probe exit: `0`; HTTP status `200`; `resolver_default=ThreadedResolver`; `connector_default=ThreadedResolver`; `system_getaddrinfo=198.18.0.57`.
- Status before prepare: `dependency_ready_data_missing`, `healthy=false`, `data_ready=false`.
- Threaded-DNS prepare exit: `0`; status `prepared`; `data_ready=true`.
- Status after prepare: `dependency_ready_seed_required`, `healthy=true`, `dependency_healthy=true`, `data_ready=true`.
- Managed data files after prepare: `15` `.feather` files for `BTC/USDT`, `ETH/USDT`, `SOL/USDT`, `BNB/USDT`, and `AVAX/USDT` across `1h`, `4h`, and `1d`.

Gate:
- `autoquant_threaded_dns_prepare_probe_v1=threaded_resolver_connector_patch_prepared_seed_required_no_promotion`
- Accepted rows added: `0`
- New confidence gate: false
- Canonical merge allowed: false
- Downstream provider/Auto-Quant/filter/Pre-Bayes/BBN/CatBoost/path-ranking/execution-tree promotion rerun allowed: false
- Strict full objective achieved: false
- `update_goal=false`

Next:
- Preserve the R6 owner/export blocker. For Auto-Quant specifically, the DNS prepare blocker is resolved in this isolated state, but the next blocker is active seed strategies; do not promote until source/control roots and canonical merge pass.
