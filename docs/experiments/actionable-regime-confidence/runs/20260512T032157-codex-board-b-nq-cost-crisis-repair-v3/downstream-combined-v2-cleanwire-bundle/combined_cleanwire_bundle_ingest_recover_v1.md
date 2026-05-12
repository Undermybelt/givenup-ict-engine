# Combined Cleanwire Bundle Ingest Recover v1

Run id: `20260512T034813+0800-codex-board-b-nq-cost-crisis-repair-v3-combined-ingest-recover-v1`

This is an additive recovery readback for the existing `downstream-combined-v2-cleanwire-bundle` state. It does not supersede the `034002` combined v1 closure row, does not edit the Board B Current Cursor, and is not a promotion claim.

## Objective Checklist

| Requirement | Evidence | Status |
|---|---|---|
| Use the named Board B markdown as the coordination surface | Evidence Ledger row added in `docs/plans/2026-05-10-regime-conditional-auto-quant-profitability-todo.md` | partial |
| Preserve regime-rooted branch paths | `00_validate_bundle.out` exposes 5 rooted paths: Bull, Bear, Sideways, Crisis, and scoped Manipulation | pass for bundle visibility |
| Use clean wire-fixed trades | `04_auto_quant_ingest_real_trades_recover.out` applied `15,415/15,415` with `0` invalid rows | pass for ingest |
| Exercise real ict-engine surfaces | `auto-quant-results-import`, `auto-quant-prior-init`, and `auto-quant-ingest-real-trades` exited `0` | partial |
| Continue through Pre-Bayes / BBN / CatBoost / execution tree | Not run in this recovery slice; the `034002` combined v1 row is the fuller closure readback and still fails closed | missing here |
| Avoid proxy promotion | Promotion remains disallowed; this only repairs a missing ingest step in a combined state | pass |

## Command Readback

| Command | Output | Exit |
|---|---|---|
| Validate aggregate regime bundle | `command-output/00_validate_bundle.out` | `0` |
| Import fixed strategy manifest | `command-output/01_auto_quant_results_import.out` | `0` |
| Apply Auto-Quant prior init | `command-output/02_auto_quant_prior_init.out` | `0` |
| Original ingest slot | `command-output/03_auto_quant_ingest_real_trades.*` | no exit file; empty output |
| Recovery ingest slot | `command-output/04_auto_quant_ingest_real_trades_recover.out` | `0` |

Recovery ingest facts:

```text
trades_total=15415
trades_applied=15415
trades_invalid=0
feedback_records_inserted=15415
content_hash=d2aec06adb0f4871
ledger_status=applied
source=board_b_032157_combined_cleanwire_bundle_v2_recover
```

State ledger now contains:

```text
auto_quant_strategy_library_validated
auto_quant_prior_init_applied
auto_quant_real_trades_ingested
```

## Blocking State

The combined v2 sidecar state now has the fixed manifest, prior init, aggregate regime-bundle visibility, and cleanwire trade ingest in one state. It is still not downstream-complete:

- Pre-Bayes was not rerun in this combined v2 state.
- BBN branch-path posterior was not rerun in this combined v2 state.
- CatBoost/path-ranker was not trained/applied/registered in this combined v2 state.
- Workflow/execution-tree admission was not rerun in this combined v2 state.
- The latest fuller combined closure row still fails closed on `user_selected_historical_data_missing`, `observe_only`, and insufficient mature path-ranker validation.

Promotion remains blocked until the same exact rooted branch paths pass the ordered chain: Pre-Bayes/filter -> BBN -> CatBoost/path-ranker -> execution tree.

