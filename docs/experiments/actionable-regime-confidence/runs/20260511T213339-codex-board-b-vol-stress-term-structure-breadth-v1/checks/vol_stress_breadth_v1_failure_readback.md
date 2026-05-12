# VolStressTermStructureBreadthV1 Failure Readback

Run id: `20260511T213339+0800-codex-board-b-vol-stress-term-structure-breadth-v1`.

Result: operational failure before RC-SPA artifacts.

Evidence:
- `checks/vol_stress_breadth_v1_run.exit` contains `1`.
- `checks/vol_stress_breadth_v1_run.err` shows `KeyError: 'provider_dispersion'`.
- No branch rows, RC-SPA report, assertions, or fail-closed summary were present at readback.

Gate result: `fail:run_exited_before_report`.

Downstream consumption: `not_started:no_rc_spa_report`.

Promotion: not allowed. Do not combine this run with the `205047` scoped Manipulation component.
