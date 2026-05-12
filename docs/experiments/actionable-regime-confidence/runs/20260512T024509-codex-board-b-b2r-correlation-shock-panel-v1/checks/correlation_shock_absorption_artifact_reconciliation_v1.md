# Correlation Shock Absorption Artifact Reconciliation v1

This check records the two `024509` packets and defers to the latest Board B ledger row for `024509`.

Latest `024509` ledger packet:

- Canonical readback: `checks/correlation_shock_absorption_canonical_readback_v3.json`
- Generic report: `branch-rc-spa/correlation_shock_absorption_rc_spa_report_v1.json`
- Result: `47,843` variant rows, `13,275` selected rows, stable score `75.8886`, required branch paths passed `0/5`, downstream `not_started:blocked_by_branch_rc_spa_hard_gates`.
- Status: authoritative for the latest `024509` evidence ledger row.

Shadow packet:

- Current artifact readback: `checks/correlation_shock_absorption_current_artifact_readback_v2.json`
- Result: `281` variant rows, `88` selected rows, stable score `72.1625`, price roots passed `0/4`, downstream `not_started:rc_spa_failed`.
- Status: retained as historical shadow evidence, not the latest `024509` ledger packet.

Action taken:

- Aligned `branch-rc-spa/correlation_shock_absorption_rc_spa_report_v1.{json,md}` and `checks/correlation_shock_absorption_v1_assertions.out` to the latest `024509` ledger packet.
