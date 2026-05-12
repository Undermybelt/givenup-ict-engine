# Downstream Closure Readback v1

Run root:
`docs/experiments/actionable-regime-confidence/runs/20260512T032157-codex-board-b-nq-cost-crisis-repair-v3`

Source packet:
- Recipe: `NQRootAdaptiveCostCrisisRepairV3`
- Stable score: `90.0000`
- Price roots: `4/4` passed
- Scoped Manipulation `205047`: component-only pass
- Selected price-root trade rows: `15,415`

This source packet is upstream-strong but not promotable by itself. Promotion
depends on the ordered downstream chain consuming the same rooted branch paths:
Auto-Quant -> filter / Pre-Bayes -> BBN -> CatBoost / path-ranker -> execution
tree.

## Readback Summary

| Slice | Evidence | Result |
|---|---|---|
| `downstream-v1` | Import / prior / ingest / Pre-Bayes / BBN / CatBoost / workflow commands ran against the first generated artifacts | Fail-closed. Manifest version and duplicate-ingest issues appeared; Pre-Bayes stayed `observe_only`; path-ranker validation stayed `0/30`; execution remained blocked. |
| `downstream-chain-v1` | Commands `00-10` all exited `0`; fixed manifest imported; aggregate regime bundle preserved `5` exact rooted paths | Fail-closed. Real-trade ingest applied `11,425/15,415` and rejected `3,990`; structural target had `5` exact rows but `0` mature rows, no trainer artifact, runtime disabled, and workflow blocked on `user_selected_historical_data_missing`. |
| `cleanwire-apply-v2` | Commands `26-35` all exited `0`; wire-fixed ingest applied `15,415/15,415` with `0` invalid rows | Fail-closed. Structural target collapsed to `3` generic rows instead of the `5` exact regime-bundle paths; Pre-Bayes stayed `observe_only`; CatBoost was not trained; execution candidate stayed `execution_blocked`. |
| `bear-bundle-v1` | Commands `11-18` all exited `0`; Bear bundle BBN evidence applied to the exact Bear path | Supplemental only. It proves branch-specific BBN application for Bear, but path-ranker validation stayed `0/30`, runtime stayed disabled, Pre-Bayes stayed `observe_only`, and execution remained blocked. |

## Blocking State

The current blocker is downstream composition, not the upstream RC-SPA packet.
The two partial repairs have not yet been combined:

- `downstream-chain-v1` keeps exact aggregate regime-bundle branch paths but
  does not ingest all rows cleanly and has no mature CatBoost/runtime closure.
- `cleanwire-apply-v2` ingests all wire-fixed trades cleanly but loses the
  exact aggregate branch paths and falls back to generic structural rows.

Workflow and execution-candidate outputs continue to require explicit
historical-data selection before factor research or execution-tree admission:
`user_selected_historical_data_missing`.

## Next Closure Contract

Run one combined downstream closure pass in a clean state:

1. Import the fixed `manifest_version = "1.0"` strategy library.
2. Ingest `downstream-v2/nq_cost_crisis_repair_real_trades_v3_wire_fixed.jsonl`
   so `15,415/15,415` rows apply with `0` invalid rows.
3. Apply the aggregate regime bundle so the `5` exact branch paths remain
   visible in BBN and structural path-ranking targets.
4. Train / apply / register CatBoost only after target rows have mature,
   calibrated labels.
5. Rerun Pre-Bayes, workflow, and execution-candidate only after a concrete
   historical-data path is selected.

Promotion remains disallowed until the same exact branch path is ready,
actionable, and admitted through execution tree.
