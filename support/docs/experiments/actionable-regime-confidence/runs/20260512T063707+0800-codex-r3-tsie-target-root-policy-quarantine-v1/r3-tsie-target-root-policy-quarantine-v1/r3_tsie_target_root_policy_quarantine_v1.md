# R3 TSIE Target-Root Policy Quarantine v1

Run id: `20260512T063707+0800-codex-r3-tsie-target-root-policy-quarantine-v1`

Gate result: `r3_tsie_target_root_policy_quarantine_v1=target_root_present_but_proxy_policy_blocked_no_promotion`

## Scope

Read-only quarantine after the policy-blocked TSIE materializer created `/tmp/ict-engine-native-subhour-source-label-intake` while its writer process was still active. This packet does not delete or modify that root, does not kill another agent's process, does not approve TSIE, does not run direct verifier, does not run canonical merge, does not rerun downstream promotion, and does not call `update_goal`.

## Evidence

- Board SHA-256 before this artifact: `2f833ef82a10a7f8464ed0a8fbc7e2e3e6d7722bab741e3da81bc75974e00ba0`.
- Writer process observed active: `98181`, script `20260512T062902+0800-codex-r3-hf-tsie-native-intraday-intake-v1/scripts/r3_hf_tsie_native_intraday_intake_v1.py`.
- Target root observed present: `/tmp/ict-engine-native-subhour-source-label-intake`.
- Rows file observed present: `/tmp/ict-engine-native-subhour-source-label-intake/native_subhour_source_label_rows.csv`, size `2786719721` bytes.
- Provenance file observed present: `/tmp/ict-engine-native-subhour-source-label-intake/native_subhour_source_label_provenance.json`, size `2400` bytes.
- CSV header includes `source_confidence`, `native_timeframe_minutes`, `source_regime_label`, and `source_regime_name`.

## Policy Readback

The root path exists, but it is not accepted Board A evidence. Prior accepted ledger state still blocks TSIE:

- `062409`: TSIE and nearby R3/R5 public candidates selected for target-root materialization: `0`.
- `062657`: TSIE is negative evidence only because labels are rule/OHLCV-generated, single IDX context, no direct `Crisis`, no accepted `MainRegimeV2` equivalence, exact active R3 target cells absent, and prior full-parquet gates accepted `0` roots.
- `063215`: the `062902` materializer was explicitly preflight-blocked as `do_not_run_target_root_materializer_proxy_blocked`.

## Decision

Treat `/tmp/ict-engine-native-subhour-source-label-intake` as a tainted/proxy TSIE root until a later approved source/control policy explicitly accepts it or replaces it with verifier-native R3 labels. It must not unlock direct verifier, split calibration, canonical merge, provider/AutoQuant, filter/Pre-Bayes, BBN, CatBoost/path-ranking, or execution-tree promotion.

Accounting:

- required root path present: `true`
- required root accepted: `false`
- target root mutated by another active process: `true`
- accepted rows added: `0`
- source/control evidence acquired: `false`
- canonical merge: `false`
- downstream promotion rerun: `false`
- strict full objective: `false`
- trade usable: `false`
- `update_goal=false`

## Next

Do not consume this target root as an unlock. Wait for the active writer to finish before any file-level row-count/hash audit, and then either quarantine/count it as rejected TSIE proxy evidence or replace it with explicit source/control approval, verifier-native R6 owner-export rows with controls, source-owned R5 recency rows, verifier-native R3 `MainRegimeV2` rows, or a genuinely new accepted cross-timeframe `MainRegimeV2` source export.
