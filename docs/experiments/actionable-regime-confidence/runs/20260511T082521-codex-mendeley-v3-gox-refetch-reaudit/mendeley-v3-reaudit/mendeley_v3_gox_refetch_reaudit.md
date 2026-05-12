# Mendeley v3 Gox Re-fetch Re-audit

Run id: `20260511T082521+0800-codex-mendeley-v3-gox-refetch-reaudit`

## Result

- Current Mendeley version: `3`
- Gox SHA-256 matches current Mendeley v3: `true`
- Gate result: `blocked_mendeley_gox_hgb_wash_below_95`
- Accepted direct `Manipulation` 95: `false`
- Blockers: `test_coverage_below_min, calibration_ece_above_max, test_ece_above_max`
- MainRegimeV2 root-label slots added: `0`
- Manipulation label slots added: `0`

## Metrics

- Calibration Wilson95 LCB: `0.976727954706`
- Test Wilson95 LCB: `0.985614662979`
- Calibration coverage: `0.030348999955`
- Test coverage: `0.008994528878`
- Calibration ECE: `0.081711972155`
- Test ECE: `0.115501381750`

## Accounting

- The current public v3 file hash matches the local raw Gox CSV, so the rerun used current source bytes.
- The unchanged gate still fails because coverage and ECE blockers remain.
- Raw data stayed under `/private/tmp` or `/tmp`; no raw rows were committed.
- Runtime code changed: false. Thresholds relaxed: false. Trade usable: false.
