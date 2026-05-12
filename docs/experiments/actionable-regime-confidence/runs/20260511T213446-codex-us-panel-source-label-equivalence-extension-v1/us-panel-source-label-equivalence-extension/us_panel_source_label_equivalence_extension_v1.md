# US Panel Source Label Equivalence Extension v1

Decision: `us_panel_source_label_equivalence_extension_v1=schema_ready_all_price_roots_confidence_unaccepted`.

Result:
- Previous shared rows retained: `493445`.
- US panel rows added: `245005`.
- Merged shared row count: `738450`.
- US label counts: `{'Bear': 54939, 'Bull': 103766, 'Crisis': 29632, 'Sideways': 56668}`.
- Merged label counts: `{'Bear': 164817, 'Bull': 312511, 'Crisis': 89887, 'Sideways': 171235}`.
- Date range: `2000-01-03` to `2026-01-30`; tickers `39`.
- Source confidence >=0.95 rows: `17766`; accepted confidence gate: `false`.
- Verifier status: `blocked`; return code `2`.
- Accepted rows added: `0`; new confidence gate: `false`; strict full objective achieved: `false`; `update_goal=false`.
- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; external requests sent: `false`; trade usable: `false`.

Interpretation:
The shared source-label equivalence root now has schema rows for Bull, Bear, Sideways, and Crisis across the local US daily equity panel plus the prior NIFTY rows. This closes a schema gap only. It does not provide owner-approved >=95 confidence, native sub-hour validation, R5 recency extension, or R6 direct Manipulation confidence.

Artifacts:
- JSON: `docs/experiments/actionable-regime-confidence/runs/20260511T213446-codex-us-panel-source-label-equivalence-extension-v1/us-panel-source-label-equivalence-extension/us_panel_source_label_equivalence_extension_v1.json`
- Report: `docs/experiments/actionable-regime-confidence/runs/20260511T213446-codex-us-panel-source-label-equivalence-extension-v1/us-panel-source-label-equivalence-extension/us_panel_source_label_equivalence_extension_v1.md`
- Counts CSV: `docs/experiments/actionable-regime-confidence/runs/20260511T213446-codex-us-panel-source-label-equivalence-extension-v1/us-panel-source-label-equivalence-extension/us_panel_source_label_equivalence_counts_v1.csv`
- Shared verifier stdout: `docs/experiments/actionable-regime-confidence/runs/20260511T213446-codex-us-panel-source-label-equivalence-extension-v1/command-output/source_label_equivalence_verifier.stdout.txt`
- Reproduction script: `docs/experiments/actionable-regime-confidence/runs/20260511T213446-codex-us-panel-source-label-equivalence-extension-v1/scripts/us_panel_source_label_equivalence_extension_v1.py`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260511T213446-codex-us-panel-source-label-equivalence-extension-v1/checks/us_panel_source_label_equivalence_extension_v1_assertions.out`
