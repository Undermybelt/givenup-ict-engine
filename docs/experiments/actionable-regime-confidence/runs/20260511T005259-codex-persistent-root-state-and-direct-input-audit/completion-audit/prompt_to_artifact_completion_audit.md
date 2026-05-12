# Prompt To Artifact Completion Audit

Loop id: `20260511T005259+0800-codex-persistent-root-state-and-direct-input-audit`

Objective restatement:
- Every active regime must reach calibrated 95% confidence.
- The accepted packet must validate on other markets and other timeframes.
- Results must be written back to the named board before reporting completion.

Checklist:

| Requirement | Evidence | State |
|---|---|---|
| Current root axis evaluated | `docs/experiments/actionable-regime-confidence/runs/20260511T005259-codex-persistent-root-state-and-direct-input-audit/root-v2-persistent/persistent_root_state_report.json` | done |
| Cross-market validation | persistent report test instruments/contexts; source table `docs/experiments/actionable-regime-confidence/runs/20260510T224014-codex-cross-timeframe-regime-validation/cross_timeframe_regime_features.csv` | done for evaluated packet, still blocked for missing roots |
| Cross-timeframe validation | persistent report test timeframes | done for evaluated packet, still blocked for missing roots |
| 95% calibrated confidence for every root | current-run accepted roots `none`; retained prior roots `Crisis`; effective missing roots `Bull, Bear, Sideways, Manipulation` | blocked |
| Direct Manipulation inputs | `docs/experiments/actionable-regime-confidence/runs/20260511T005259-codex-persistent-root-state-and-direct-input-audit/input-inventory/direct_manipulation_input_inventory.json` usable=False | blocked |
| Thresholds not relaxed | `thresholds_relaxed=false` | done |
| Runtime code unchanged | `runtime_code_changed=false` | done |

Conclusion:

Not complete. The persistent root-state probe does not add a new accepted Bull/Bear/Sideways root, the prior accepted Crisis root is retained separately, and the local inventory does not contain a usable chronological direct-input set for Manipulation.
