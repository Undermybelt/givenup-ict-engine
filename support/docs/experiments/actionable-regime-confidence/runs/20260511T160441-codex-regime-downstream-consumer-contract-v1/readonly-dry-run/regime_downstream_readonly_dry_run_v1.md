# Regime Downstream Read-only Dry Run v1

Run ID: `20260511T160441+0800-codex-regime-downstream-readonly-dry-run-v1`

## Decision

- `ict-engine analyze --demo --human` strict-loaded the generated Bull bundle template.
- `MainRegimeV2::Bull` appeared in read-only regime diagnostics.
- BBN mutation stayed skipped; this dry-run did not convert the context into trade-usable evidence.
- Full objective achieved: `false`; `update_goal=false`.

## Probe Results

| Probe | Result |
|---|---:|
| `bundle_loaded` | `true` |
| `bundle_template_path_visible` | `true` |
| `mainregime_label_visible` | `true` |
| `read_only_bbn_label_visible` | `true` |
| `bbn_application_skipped` | `true` |
| `bbn_application_applied` | `false` |

## Artifacts

- JSON: `docs/experiments/actionable-regime-confidence/runs/20260511T160441-codex-regime-downstream-consumer-contract-v1/readonly-dry-run/regime_downstream_readonly_dry_run_v1.json`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260511T160441-codex-regime-downstream-consumer-contract-v1/checks/regime_downstream_readonly_dry_run_v1_assertions.out`
- Runtime state: `/tmp/ict-engine-regime-bundle-readonly-160441/DEMO`
