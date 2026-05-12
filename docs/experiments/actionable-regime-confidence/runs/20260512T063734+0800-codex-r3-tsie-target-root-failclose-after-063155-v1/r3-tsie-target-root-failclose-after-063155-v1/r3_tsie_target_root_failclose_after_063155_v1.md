# R3 TSIE Target Root Fail-Close After 063155 v1

Run id: `20260512T063734+0800-codex-r3-tsie-target-root-failclose-after-063155-v1`

Gate result: `r3_tsie_target_root_failclose_after_063155_v1=target_root_present_but_tsie_policy_blocked_no_unlock`

## Readback

- Target root present: `true`.
- Target root mutated by `063155`: `true`.
- Rows from target provenance: `5032903`.
- Rows SHA-256 from target provenance: `72406e48b000f91ed2b3c3e132651537339afb2a8ed2e3ce43b5007abf38f62f`.
- Materializer claimed accepted rows: `5032903`.
- Audit accepted rows: `0`.

## Decision

- The required R3 target root exists, but it is logically quarantined and non-promoting.
- TSIE remains policy-blocked: rule/OHLCV-derived IDX labels, no direct `Crisis`, no source confidence, and prior TSIE gates were non-promoting.
- The `063155` materializer claim that Bull/Bear/Sideways rows are accepted is not counted for Board A promotion.
- Canonical merge is blocked; downstream provider/AutoQuant -> filter/Pre-Bayes -> BBN -> CatBoost/path-ranking -> execution-tree rerun is blocked.
- `update_goal=false`.

## Artifacts

- JSON: `docs/experiments/actionable-regime-confidence/runs/20260512T063734+0800-codex-r3-tsie-target-root-failclose-after-063155-v1/r3-tsie-target-root-failclose-after-063155-v1/r3_tsie_target_root_failclose_after_063155_v1.json`
- Required roots CSV: `docs/experiments/actionable-regime-confidence/runs/20260512T063734+0800-codex-r3-tsie-target-root-failclose-after-063155-v1/r3-tsie-target-root-failclose-after-063155-v1/r3_tsie_target_root_failclose_required_roots_v1.csv`
- Checklist CSV: `docs/experiments/actionable-regime-confidence/runs/20260512T063734+0800-codex-r3-tsie-target-root-failclose-after-063155-v1/r3-tsie-target-root-failclose-after-063155-v1/prompt_to_artifact_checklist_v1.csv`
- Process snapshot: `docs/experiments/actionable-regime-confidence/runs/20260512T063734+0800-codex-r3-tsie-target-root-failclose-after-063155-v1/command-output/process_snapshot.txt`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260512T063734+0800-codex-r3-tsie-target-root-failclose-after-063155-v1/checks/r3_tsie_target_root_failclose_after_063155_v1_assertions.out`

## Next

Treat /tmp/ict-engine-native-subhour-source-label-intake as TSIE-quarantined and non-promoting. Do not run canonical merge or downstream provider/AutoQuant/Pre-Bayes/BBN/CatBoost/execution-tree until explicit source/control approval or a verifier-native R3/R5/R6 target root unlock is available.
