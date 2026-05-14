# Local Cache Seed v2 Settled Readback

Run id: `20260512T101221+0800-codex-board-b-093854-local-cache-seed-v2`

Mode: `append_only_settled_readback_non_promoting`

Gate result: `board_b_093854_local_cache_seed_v2=strategy_seeded_autoquant_run_attempted_binance_dns_failed_no_promotion`

## Result

- Source state copied from `docs/experiments/actionable-regime-confidence/runs/20260512T093854+0800-codex-board-b-htf-nursery-v1/state_htf_nursery_v1`.
- Local Auto-Quant cache seeded `15` feather files for `BTC_USDT`, `ETH_USDT`, `SOL_USDT`, `BNB_USDT`, and `AVAX_USDT` across `1h`, `4h`, and `1d`.
- Source and destination SHA-256 hash lists match.
- Status moved from `dependency_ready_data_missing` to `dependency_ready_seed_required`, then to `dependency_ready_data_ready` after strategy seed.
- Two active non-underscore strategy files are present and compile: `BNBMeanRevertSharp.py` and `CrashReboundVolume.py`.
- `run.py` was attempted through `uv run --with ta-lib` and exited `1`: `0` backtests succeeded and `8` failed.
- The failure class is unchanged from prior Auto-Quant attempts: Freqtrade/CCXT still tries to load Binance exchange metadata from `api.binance.com`, and DNS fails before local cached OHLCV can be backtested.

## Boundary

This is a settled-state correction for the already counted `101221` packet. It does not count `101221` again. It does not create an accepted regime packet, source/control unlock, explicit selected-history approval, canonical merge input, selected-data Auto-Quant promotion, BBN/CatBoost/path-ranking promotion, execution-tree promotion, trade evidence, or `update_goal` authorization.

## Board A Accounting

- Accepted rows added: `0`
- Every-regime 95%-99% objective: `false`
- Cross-context full validation: `false`
- Source/control evidence acquired: `false`
- Explicit user-selected history: `false`
- Canonical merge: `false`
- Selected-data AutoQuant promotion: `false`
- Downstream promotion: `false`
- Strict full objective: `false`
- Trade usable: `false`
- Promotion allowed: `false`
- `update_goal=false`

## Artifacts

- Status before seed: `docs/experiments/actionable-regime-confidence/runs/20260512T101221+0800-codex-board-b-093854-local-cache-seed-v2/command-output/00_auto_quant_status_before.out`
- Status after local-cache seed: `docs/experiments/actionable-regime-confidence/runs/20260512T101221+0800-codex-board-b-093854-local-cache-seed-v2/command-output/02_auto_quant_status_after.out`
- Status after strategy seed: `docs/experiments/actionable-regime-confidence/runs/20260512T101221+0800-codex-board-b-093854-local-cache-seed-v2/command-output/04_auto_quant_status_after_strategy_seed.out`
- Auto-Quant run stdout/stderr: `docs/experiments/actionable-regime-confidence/runs/20260512T101221+0800-codex-board-b-093854-local-cache-seed-v2/command-output/05_auto_quant_run.out`, `docs/experiments/actionable-regime-confidence/runs/20260512T101221+0800-codex-board-b-093854-local-cache-seed-v2/command-output/05_auto_quant_run.err`
- Seeded files: `docs/experiments/actionable-regime-confidence/runs/20260512T101221+0800-codex-board-b-093854-local-cache-seed-v2/command-output/01_seeded_files.out`
- Source/destination hashes: `docs/experiments/actionable-regime-confidence/runs/20260512T101221+0800-codex-board-b-093854-local-cache-seed-v2/checks/01_seed_source_sha256.out`, `docs/experiments/actionable-regime-confidence/runs/20260512T101221+0800-codex-board-b-093854-local-cache-seed-v2/checks/01_seed_dest_sha256.out`
- JSON: `docs/experiments/actionable-regime-confidence/runs/20260512T101221+0800-codex-board-b-093854-local-cache-seed-v2/local-cache-seed-v2/local_cache_seed_v2_settled_readback.json`
- Checklist: `docs/experiments/actionable-regime-confidence/runs/20260512T101221+0800-codex-board-b-093854-local-cache-seed-v2/local-cache-seed-v2/prompt_to_artifact_checklist_local_cache_seed_v2.csv`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260512T101221+0800-codex-board-b-093854-local-cache-seed-v2/checks/local_cache_seed_v2_settled_readback_assertions.out`

## Next

Do not repeat cache seeding or the same default Binance-backed `run.py` attempt. The next non-duplicative Auto-Quant slice needs either a DNS/market-metadata-free run path for the cached data, a provider-owned input that produces nonzero mature observations, or a source/control or selected-history change before downstream promotion can count.
