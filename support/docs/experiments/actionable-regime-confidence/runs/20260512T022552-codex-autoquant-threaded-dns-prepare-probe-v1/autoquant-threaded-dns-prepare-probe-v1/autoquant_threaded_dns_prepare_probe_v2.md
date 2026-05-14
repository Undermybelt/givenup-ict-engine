# Auto-Quant Threaded DNS Prepare Probe v2

Run root: `docs/experiments/actionable-regime-confidence/runs/20260512T022552-codex-autoquant-threaded-dns-prepare-probe-v1`

Purpose: correct the v1 interpretation after the connector-level resolver patch and real `ict-engine auto-quant-prepare` completed in an isolated copied Auto-Quant state.

Scope:
- Source failed root for comparison: `/tmp/ict-engine-board-a-autoquant-bootstrap-20260512T021808`
- Isolated successful state: `/tmp/ict-engine-board-a-autoquant-threaded-dns-20260512T022552`
- Managed Auto-Quant checkout: `/tmp/ict-engine-board-a-autoquant-threaded-dns-20260512T022552/auto-quant/.deps/auto-quant`
- Resolver shim: `scripts/sitecustomize.py`
- Runtime code changed: false
- Shared intake/source roots changed: false

Command evidence:
- First shallow resolver probe: `command-output/00_threaded_dns_exchangeinfo_probe.*`, exit `1`, still used `aiodns`.
- Connector-level resolver probe: `command-output/01_threaded_dns_exchangeinfo_probe_connector_patch.*`, exit `0`, `http_status=200`, `connector_default=ThreadedResolver`.
- Status before prepare: `command-output/02_status_before_threaded_prepare.*`, status `dependency_ready_data_missing`.
- Real prepare with `PYTHONPATH` shim: `command-output/03_auto_quant_prepare_threaded_dns.*`, exit `0`.
- Status after prepare: `command-output/04_status_after_threaded_prepare.*`, status `dependency_ready_seed_required`, `healthy=true`, `data_ready=true`.

Result:
- Gate result: `autoquant_threaded_dns_prepare_probe_v2=threaded_connector_resolver_prepare_succeeded_data_ready_seed_required_no_promotion`.
- The first resolver-only attempt failed because patching `aiohttp.resolver.DefaultResolver` alone did not change `aiohttp.connector.DefaultResolver`.
- The connector-level patch succeeded against `https://api.binance.com/api/v3/exchangeInfo`.
- The real prepare produced all `15` expected Binance spot feather files for `BTC`, `ETH`, `SOL`, `BNB`, and `AVAX` across `1h`, `4h`, and `1d`; managed data size is about `7.5M`.
- Auto-Quant data readiness is now proven in the isolated state, but no active non-underscore strategies exist there, so the next Auto-Quant blocker is `auto_quant_seed_strategies_required`.

Board A decision:
- Accepted rows added: `0`
- New confidence gate: false
- Canonical merge allowed: false
- Downstream provider/Auto-Quant/filter/Pre-Bayes/BBN/CatBoost/path-ranking/execution-tree promotion rerun allowed: false
- Strict full objective achieved: false
- `update_goal=false`

Next:
- Preserve the R6 owner/export blocker. If continuing Auto-Quant before R6/source-label unlock, seed active strategies only inside an isolated `/tmp` workspace and keep outputs non-promoting until owner/export controls or approved source-owned `MainRegimeV2` labels are canonically merged.
