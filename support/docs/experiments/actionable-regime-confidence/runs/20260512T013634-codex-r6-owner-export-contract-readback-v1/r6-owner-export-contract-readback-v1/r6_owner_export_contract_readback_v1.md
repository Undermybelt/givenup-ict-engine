# R6 Owner Export Contract Readback v1

- Run id: `20260512T013634-codex-r6-owner-export-contract-readback-v1`.
- Current cursor observed: `20260512T010127+0800-codex-r6-owner-route-entitlement-readback-v1`; board state: `blocked`.
- Gate result: `r6_owner_export_contract_readback_v1=verifier_native_contract_confirmed_owner_export_absent_no_promotion`.
- This is a readback/registration packet only: it does not create an adapter, mutate the owner-export root, approve `FLIP` rows, or rerun downstream promotion.

## Result

- Target owner-export root: `/tmp/ict-engine-board-a-r6-owner-export-v1`; present: `false`.
- Verifier-native required files all present: `false`.
- Direct verifier exit code: `2`.
- Canonical filename contract is already resolved by the `003003` artifact: verifier-native files are canonical; owner-facing `direct_manipulation_*` names are aliases only and are not accepted by the unchanged verifier without explicit adapter/contract approval.
- Source-owned normal controls acquired: `0`.
- Same-exhibit `FLIP` approval acquired: `false`.
- Accepted rows added: `0`; new confidence gate: `false`; canonical merge allowed: `false`; downstream promotion rerun allowed: `false`; strict full objective achieved: `false`; `update_goal=false`.
- Runtime code changed: `false`. Shared intake mutated: `false`. Owner-export root mutated: `false`. Thresholds relaxed: `false`. Raw data committed: `false`. External requests sent: `false`. Trade usable: `false`.

## Provider / Auto-Quant Read-Only Commands

- `provider_status_agent` exit `0`; summary `entry_model:2/2 ready | live_runtime:1/3 ready | local_runtime:1/2 ready | market_data:1/7 ready`.
- `provider_status_yfinance` exit `0`; summary `live_runtime:1/1 ready | market_data:1/1 ready`.
- `provider_status_ibkr` exit `0`; summary `market_data:0/1 ready`.
- `provider_status_tradingview_mcp` exit `0`; summary `market_data:0/1 ready`.
- `provider_status_kraken_public` exit `0`; summary `market_data:0/1 ready`.
- `provider_status_kraken_cli` exit `0`; summary `local_runtime:1/1 ready`.
- `auto_quant_status_json` exit `0`; status `dependency_ready_seed_required`.

## Evidence

- JSON: `/Users/thrill3r/projects-ict-engine/ict-engine/docs/experiments/actionable-regime-confidence/runs/20260512T013634-codex-r6-owner-export-contract-readback-v1/r6-owner-export-contract-readback-v1/r6_owner_export_contract_readback_v1.json`
- Required-file CSV: `/Users/thrill3r/projects-ict-engine/ict-engine/docs/experiments/actionable-regime-confidence/runs/20260512T013634-codex-r6-owner-export-contract-readback-v1/r6-owner-export-contract-readback-v1/r6_owner_export_contract_required_files_v1.csv`
- Alias mapping CSV: `/Users/thrill3r/projects-ict-engine/ict-engine/docs/experiments/actionable-regime-confidence/runs/20260512T013634-codex-r6-owner-export-contract-readback-v1/r6-owner-export-contract-readback-v1/r6_owner_export_contract_alias_mapping_v1.csv`
- Provider/Auto-Quant command CSV: `/Users/thrill3r/projects-ict-engine/ict-engine/docs/experiments/actionable-regime-confidence/runs/20260512T013634-codex-r6-owner-export-contract-readback-v1/r6-owner-export-contract-readback-v1/provider_autoquant_readonly_commands_v1.csv`
- Direct verifier stdout/stderr: `/Users/thrill3r/projects-ict-engine/ict-engine/docs/experiments/actionable-regime-confidence/runs/20260512T013634-codex-r6-owner-export-contract-readback-v1/command-output/direct_verifier_owner_export_root.stdout.txt` / `/Users/thrill3r/projects-ict-engine/ict-engine/docs/experiments/actionable-regime-confidence/runs/20260512T013634-codex-r6-owner-export-contract-readback-v1/command-output/direct_verifier_owner_export_root.stderr.txt`
- Assertions: `/Users/thrill3r/projects-ict-engine/ict-engine/docs/experiments/actionable-regime-confidence/runs/20260512T013634-codex-r6-owner-export-contract-readback-v1/checks/r6_owner_export_contract_readback_v1_assertions.out`

## Next

- Satisfy the CME/Cboe owner-export requests with verifier-native files and provenance, or explicitly approve the same-exhibit FLIP-as-control exception; only then populate the owner-export root under shared lock and rerun direct verifier, calibration, provider, Auto-Quant, pre-Bayes/BBN, CatBoost/path-ranking, and execution-tree readback.
