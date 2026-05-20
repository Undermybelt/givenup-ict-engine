# Support examples

These files are optional inputs and smoke fixtures. A clean checkout does not load
them unless the caller explicitly passes a path, copies one into a state dir, or
sets an opt-in environment variable.

Zero-config smoke fixtures:

- `demo/` — tiny synthetic candles for first-run CLI checks.
- `factor_signal_diagnostics/` — stdlib Python diagnostics and candidate-pack
  demo composition. Writes outputs to `/tmp/...` in examples and keeps
  `trade_usable=false` until downstream gates promote later.
- `pa_agent_intake/` — PA Agent price-action taxonomy intake. The consumer entry
  is the compact `artifact_index.json`; full bundles remain observation-only and
  `trade_usable=false`.

Hot-plug inputs:

- `factor_hotplug/` — optional detector/GA feature configs selected by explicit
  path or `ICT_ENGINE_FACTOR_HOTPLUG_CONFIG`.
- `pa_agent_intake_profile.example.json` — optional profile override for PA Agent
  intake; select with `--profile` only when you want to reuse that ladder/gate
  policy.
- `provider_profiles/` — optional provider profile examples; not default runtime
  input.

Generated artifacts should go under `/tmp/...` or an explicit `--state-dir`, not
inside this directory.