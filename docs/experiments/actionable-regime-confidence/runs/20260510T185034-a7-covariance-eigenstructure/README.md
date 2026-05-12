# Board A A7 Covariance Eigenstructure Run

Purpose: add realized covariance and correlation eigenstructure evidence for `ExtremeStress` / `ReversalBrewing`.

Result: abstain. The probe generated 5003 rows and 39 features, but accepted_95_rule_count=0 and accepted_99_rule_count=0. Thresholds were not relaxed.

Key artifacts:
- `evidence_packet_a7_covariance_eigenstructure.json`
- `covariance-eigenstructure/covariance_eigenstructure_calibration_report.json`
- `covariance-eigenstructure/covariance_eigenstructure_features.csv`
- `downstream-readback/provider_status_compact.out`
- `downstream-readback/workflow_status_nq.json`
- `downstream-readback/policy_training_status_nq.json`

Next: A8 jump-model or persistence-penalty features for transition hazard.
