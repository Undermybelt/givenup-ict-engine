# R3 TSIE Native-Intraday Materializer Preflight v1

Run id: `20260512T063215+0800-codex-r3-tsie-native-intraday-materializer-preflight-v1`

Gate result: `r3_tsie_native_intraday_materializer_preflight_v1=do_not_run_target_root_materializer_proxy_blocked`

## Scope

Read-only preflight for the in-progress `062902` materializer script. This artifact does not execute that script, does not write `/tmp/ict-engine-native-subhour-source-label-intake`, does not approve TSIE, does not run canonical merge, does not rerun downstream promotion, and does not call `update_goal`.

## Decision

- The `062902` script is present but should not be treated as a target-root unlock.
- It contains a target-root materialization path and declares `target_root_mutated=true` if run.
- Its own metadata preserves the blockers: `crisis_no_direct_mapping`, `source_confidence_available=false`, `canonical_merge_allowed_now=false`, and `downstream_rerun_allowed_now=false`.
- Prior Board A TSIE packets already rejected TSIE as rule/OHLCV-derived, single-context, no direct `Crisis`, and accepted `0` roots.
- Required target roots remain absent in this preflight; accepted rows added `0`; source/control evidence acquired false; canonical merge false; downstream promotion rerun false; trade usable false; `update_goal=false`.

## Artifacts

- JSON: `docs/experiments/actionable-regime-confidence/runs/20260512T063215+0800-codex-r3-tsie-native-intraday-materializer-preflight-v1/r3-tsie-native-intraday-materializer-preflight-v1/r3_tsie_native_intraday_materializer_preflight_v1.json`
- Findings CSV: `docs/experiments/actionable-regime-confidence/runs/20260512T063215+0800-codex-r3-tsie-native-intraday-materializer-preflight-v1/r3-tsie-native-intraday-materializer-preflight-v1/r3_tsie_native_intraday_materializer_preflight_findings_v1.csv`
- Prior blockers CSV: `docs/experiments/actionable-regime-confidence/runs/20260512T063215+0800-codex-r3-tsie-native-intraday-materializer-preflight-v1/r3-tsie-native-intraday-materializer-preflight-v1/r3_tsie_native_intraday_prior_blockers_v1.csv`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260512T063215+0800-codex-r3-tsie-native-intraday-materializer-preflight-v1/checks/r3_tsie_native_intraday_materializer_preflight_v1_assertions.out`

## Next

Do not run or count `062902` as an R3 unlock unless the user or board explicitly changes the source/control policy. Continue from real R6 owner/export rows, source-owned R5 recency rows, verifier-native R3 labels, or explicit source/control approval.
