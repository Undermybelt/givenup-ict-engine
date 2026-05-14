# Local Owner Export Candidate Scan v1

- Decision: `local_owner_export_candidate_scan_v1=tomac_databento_ohlcv_only_no_r6_controls`.
- Candidate archive: `/Users/thrill3r/Downloads/Tomac/gc future 2021-2025/databento.rar`.
- Archive SHA-256: `60daf9e15e42a8c1884c7dbe36629dcea06fd13f0e20ec0ed0c9d1a74ee51112`.
- Metadata dataset: `GLBX.MDP3`; schema: `ohlcv-1m`; symbols: `['GC.FUT']`.
- Archive files: `['gc_201101_202604.csv', 'nq_201101_202604.csv']`.
- Manifest files: `['condition.json', 'metadata.json', 'symbology.json', 'symbology.csv', 'glbx-mdp3-20210106-20260105.ohlcv-1m.csv']`.
- Has depth/order-lifecycle evidence: `false`.
- Has only OHLCV/symbology headers in extracted CSVs: `true`.
- R6 owner-control contract satisfied: `false`.
- Canonical merge allowed now: `false`; downstream rerun allowed now: `false`.
- Accepted rows added: `0`; strict full objective achieved: `false`; `update_goal=false`.

## Classification

The local Tomac/Databento candidate is useful market-data context but cannot be promoted as R6 source-owned normal controls. It is `ohlcv-1m` CSV material, not verifier-native Market Depth/Market by Order/order-lifecycle data, and it carries no approved normal/non-manipulation labels.

## Artifacts

- JSON: `docs/experiments/actionable-regime-confidence/runs/20260512T011812-codex-local-owner-export-candidate-scan-v1/local-owner-export-candidate-scan-v1/local_owner_export_candidate_scan_v1.json`
- File CSV: `docs/experiments/actionable-regime-confidence/runs/20260512T011812-codex-local-owner-export-candidate-scan-v1/local-owner-export-candidate-scan-v1/local_owner_export_candidate_files_v1.csv`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260512T011812-codex-local-owner-export-candidate-scan-v1/checks/local_owner_export_candidate_scan_v1_assertions.out`
- Reproduction script: `/Users/thrill3r/projects-ict-engine/ict-engine/docs/experiments/actionable-regime-confidence/runs/20260512T011812-codex-local-owner-export-candidate-scan-v1/scripts/local_owner_export_candidate_scan_v1.py`
