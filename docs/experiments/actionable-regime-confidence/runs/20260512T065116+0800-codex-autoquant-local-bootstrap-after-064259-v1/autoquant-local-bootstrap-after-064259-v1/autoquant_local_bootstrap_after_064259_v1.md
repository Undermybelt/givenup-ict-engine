# AutoQuant Local Bootstrap After 064259 v1

Run id: `20260512T065116+0800-codex-autoquant-local-bootstrap-after-064259-v1`

Gate result: `autoquant_local_bootstrap_after_064259_v1=bootstrap_ok_prepare_dns_blocked_data_missing_no_promotion`

## Result

- `auto-quant-bootstrap --repo-url /Users/thrill3r/Auto-Quant` exited `0`.
- `auto-quant-status` after bootstrap exited `0` and reported `dependency_ready_data_missing`.
- `auto-quant-prepare` exited `1`.
- `auto-quant-status` after prepare still reported `dependency_ready_data_missing`.

## Prepare Blocker

`auto-quant-prepare` failed while freqtrade/ccxt loaded Binance markets:

- Host: `api.binance.com`
- Failure class: DNS/network
- Error summary: `Could not contact DNS servers`, followed by `Markets were not loaded`.

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

- Bootstrap stdout: `docs/experiments/actionable-regime-confidence/runs/20260512T065116+0800-codex-autoquant-local-bootstrap-after-064259-v1/command-output/auto_quant_bootstrap_local.stdout`
- Prepare stderr: `docs/experiments/actionable-regime-confidence/runs/20260512T065116+0800-codex-autoquant-local-bootstrap-after-064259-v1/command-output/auto_quant_prepare.stderr`
- Status after prepare stdout: `docs/experiments/actionable-regime-confidence/runs/20260512T065116+0800-codex-autoquant-local-bootstrap-after-064259-v1/command-output/auto_quant_status_after_prepare.stdout`
- JSON: `docs/experiments/actionable-regime-confidence/runs/20260512T065116+0800-codex-autoquant-local-bootstrap-after-064259-v1/autoquant-local-bootstrap-after-064259-v1/autoquant_local_bootstrap_after_064259_v1.json`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260512T065116+0800-codex-autoquant-local-bootstrap-after-064259-v1/checks/autoquant_local_bootstrap_after_064259_v1_assertions.out`

## Next

Do not use this as promotion evidence. Continue from a valid source/control unlock first; separately, Auto-Quant prepare needs a DNS-safe or local-cache-safe data path before `data_ready` can become true.
