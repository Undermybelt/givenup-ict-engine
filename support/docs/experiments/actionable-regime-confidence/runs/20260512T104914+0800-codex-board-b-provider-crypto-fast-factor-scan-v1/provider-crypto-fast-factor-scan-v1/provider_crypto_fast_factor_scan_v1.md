# Provider Crypto Fast Factor Scan v1

Run id: `20260512T104914+0800-codex-board-b-provider-crypto-fast-factor-scan-v1`

Closeout time: `2026-05-12T10:57:04+0800`

Gate: `104914_provider_crypto_fast_factor_scan_v1=diagnostic_killed_slow_scan_no_promotion`

## Scope

This run was a bounded local diagnostic pre-screen over copied provider crypto 1h feathers from:

`docs/experiments/actionable-regime-confidence/runs/20260512T103437+0800-codex-board-b-yahoo-crypto-momentum-market-aq-v1/workspace/auto-quant-yahoo-crypto-momentum/user_data/data`

It was intended only to search for a possible next Auto-Quant recipe candidate across BTC/ETH/SOL. It was not a provider acquisition packet, not a real Auto-Quant execution result, not a six-provider matrix proof, and not a downstream promotion candidate.

## Evidence

- First scan command: `command-output/00_fast_provider_crypto_scan.cmd`
- First scan exit marker: `checks/00_fast_provider_crypto_scan.exit`
- First scan stderr: `command-output/00_fast_provider_crypto_scan.err`
- First scan stdout: `command-output/00_fast_provider_crypto_scan.out`
- Reduced diagnostic script retained for replay: `workspace/fast_provider_crypto_scan.py`
- Reduced script SHA-256: `41ffd934823456d514154f6be37eb97a95c65977f8c3cc63997ead35c55e1b92`

## Readback

- The first diagnostic scan was manually stopped as `killed_slow_scan`.
- It produced no candidate JSON on stdout.
- The script was reduced afterward, but it was not rerun because concurrent Auto-Quant/TOMAC processes were already active and the latest Board B hard gate requires AQ execution plus provider-matrix provenance before an A/B claim.
- Rerunning this local screen would not satisfy the latest authority-provider gate by itself.

## Gate

- `count_once:104914_provider_crypto_fast_factor_scan`
- `pass:diagnostic_run_root_preserved`
- `pass:slow_scan_exit_marker_recorded`
- `fail_closed:first_scan_killed_slow_scan`
- `fail_closed:no_candidate_json_produced`
- `fail_closed:not_real_auto_quant_execution`
- `fail_closed:no_provider_matrix_invocation_rows`
- `fail_closed:no_mature_profitable_rooted_branch`
- `fail_closed:no_pre_bayes_bbn_catboost_execution_tree_chain`
- `promotion_allowed=false`
- `update_goal=false`

## Next

Do not promote from this diagnostic pre-screen. If the crypto lane continues, start from a real provider/AQ packet that records provider invocation/provenance rows and carries the exact `main_regime -> sub_regime -> sub_sub_regime_or_profit_factor -> profit_factor` branch through the ordered downstream chain.
