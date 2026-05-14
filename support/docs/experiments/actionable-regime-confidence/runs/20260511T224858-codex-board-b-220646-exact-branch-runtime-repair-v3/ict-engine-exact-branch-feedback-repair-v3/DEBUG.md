# DEBUG v3

Phase 1 observations:
- v2 registration failed because the CLI attempted to read a binary `.cbm` as UTF-8 JSON.
- Working examples register a JSON trainer companion whose `artifact_uri` points at score CSV rows.
- v2 emitted only four exact branch observations, causing `4/30` production and observation validation.
- Existing B5 calibration selected 48 real branch feedback observations with exact `regime_profit_branch_path` values and wrote isolated state.
- v3 copies that isolated state, then re-exports it with the current binary so old artifacts are not mutated.

Hypotheses:
- Registering a JSON companion should retire `trainer_artifact=missing`.
- Replaying the 48 exact branch observations should satisfy the `30` row validation floor.
- Enabling runtime with `prefer_history` and exact branch scores should let the runtime select one of the four exact Board B paths.
