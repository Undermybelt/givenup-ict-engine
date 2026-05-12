# Board A Multi-Regime Expansion

This run reuses durable local QQQ/NQ/provider artifacts and does not start new heavy Auto-Quant training.

- Calibration report: `docs/experiments/actionable-regime-confidence/runs/20260510T200229-hermes-multi-regime-expansion/multi-regime/multi_regime_calibration_report.json`
- Calibration script: `docs/experiments/actionable-regime-confidence/runs/20260510T200229-hermes-multi-regime-expansion/multi-regime/calibrate_multi_regime.py`
- Feature/label table: `docs/experiments/actionable-regime-confidence/runs/20260510T200229-hermes-multi-regime-expansion/multi-regime/multi_regime_features_and_labels.csv`
- Evidence packet: `docs/experiments/actionable-regime-confidence/runs/20260510T200229-hermes-multi-regime-expansion/evidence_packet_multi_regime_expansion.json`
- Existing accepted context: `docs/experiments/actionable-regime-confidence/runs/20260510T184532-codex-session-liquidity/session-liquidity/session_liquidity_regime_probe_report.json`
- Prompt-to-artifact audit: `docs/experiments/actionable-regime-confidence/runs/20260510T200229-hermes-multi-regime-expansion/completion_audit_prompt_to_artifact.json`
- Fresh assertion output: `docs/experiments/actionable-regime-confidence/runs/20260510T200229-hermes-multi-regime-expansion/checks/fresh_completion_assertions.out`

All five additional regimes abstained under unchanged chronological thresholds. `SessionLiquidityCoreViable` remains the only accepted 95% packet; no trade or execute promotion is claimed.
