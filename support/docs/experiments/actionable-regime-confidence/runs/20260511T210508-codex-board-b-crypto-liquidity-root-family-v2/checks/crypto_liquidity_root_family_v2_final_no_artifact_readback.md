# CryptoLiquidityRootFamilyV2 Superseded No-Artifact Readback

Observed at: `20260511T211310+0800`

Superseded at: `20260511T211617+0800`

Status: `superseded:later_artifacts_appeared`

Run id: `20260511T210508+0800-codex-board-b-crypto-liquidity-root-family-v2`

Recipe: `CryptoLiquidityRootFamilyV2`

Declared run root:
`docs/experiments/actionable-regime-confidence/runs/20260511T210508-codex-board-b-crypto-liquidity-root-family-v2`

## Process Readback

- The earlier preliminary no-artifact readback was superseded because a later `uv run` scorer was still active.
- The later `uv run` / Python scorer for `crypto_liquidity_root_family_v2.py` was rechecked after exit.
- A subsequent run-root readback found completed branch RC-SPA artifacts. Do not use this file as rejection evidence.

## Correct Artifact Readback

Completed artifacts now present:

- `branch-rc-spa/crypto_liquidity_root_family_rc_spa_report_v2.md`
- `branch-rc-spa/crypto_liquidity_root_family_rc_spa_report_v2.json`
- `branch-rc-spa/crypto_liquidity_root_family_variant_rows_v2.csv`
- `branch-rc-spa/crypto_liquidity_root_family_selected_rows_v2.csv`
- `branch-rc-spa/crypto_liquidity_root_family_branch_summary_v2.csv`
- `branch-rc-spa/crypto_liquidity_root_family_panel_summary_v2.csv`
- `checks/crypto_liquidity_root_family_v2_assertions.out`
- `ict-engine-fail-closed/crypto_liquidity_root_family_fail_closed_summary_v2.md`

Final report summary:

- Variant rows: `33,059`
- Selected rows: `11,387`
- Stable profit score: `72.5000`
- Price-root paths passed: `0/4`
- Scoped Manipulation component pass consumed: `true`
- Gate: `fail:required_root_branch_hard_gates_failed`
- Downstream: `not_started:blocked_by_branch_rc_spa_hard_gates`

## Gate State

- `stable_profit_score`: `72.5000`
- `hard_gate_result`: `fail:required_root_branch_hard_gates_failed`
- `downstream_consumption`: `not_started:blocked_by_branch_rc_spa_hard_gates`
- `promotion_state`: `rejected_rc_spa_hard_gates`

## Board B Interpretation

This run did consume the `20260511T205047` scoped direct `Manipulation` component, but all price roots did not pass. The direct component remains component-only evidence. Full Board B promotion still requires Bull/Bear/Sideways/Crisis root branches to pass unchanged RC-SPA before any downstream Pre-Bayes -> BBN -> CatBoost/path-ranker -> execution-tree consumption.

## Next Action

Select a genuinely different root-branch family or provider panel for Bull/Bear/Sideways/Crisis. Do not promote downstream from this failed RC-SPA run.
