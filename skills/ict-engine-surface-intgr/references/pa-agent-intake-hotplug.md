# PA Agent intake hotplug pattern

> 2026-05-24 schema note: `pda_hybrid_alignment` is historical telemetry only unless the current ict-engine source or readback contract still declares it active. Do not use old `pda_hybrid_alignment=true` or `false` lines in this reference as a current hard gate; classify with the live actionable/status/readiness/transition/ranker/mature-row fields.

Use when absorbing PA_Agent-style price-action / LLM decision traces into ict-engine.

## Durable pattern
- Do not install, run, or embed PA_Agent as a runtime authority.
- Treat PA_Agent outputs as untrusted observation evidence, never trade proof.
- Add a zero-config artifact generator with embedded defaults so clean-checkout consumers can run it without PA_Agent present.
- Support explicit opt-in source parsing via `--pa-agent-root`.
- Support explicit user profile overrides via `--profile`.
- Emit both:
  - compact one-line status for agents and terminals;
  - JSON artifacts for downstream consumers.
- Keep all generated evidence `trade_usable=false`, `inactive_by_default`, and `candidate_observation` until ict-engine downstream gates promote it.

## Artifact shape
Recommended outputs:
- `artifact_index.json` — token-friendly index; first file consumers/agents should read.
- `pa_agent_intake_bundle.json` — full bundle.
- `regime_taxonomy.json` — PA_Agent cycle-position to ict-engine regime/subregime map.
- `decision_trace_schema.json` — gate/decision trace field contract.
- `router_rules.json` — source-inspired observation router rules.
- `candidate_pack_template.json` — inactive candidate-pack scaffold for opt-in use.

`artifact_index.json` should contain only relative artifact names, counts, warning flags, `trade_usable=false`, and compact profile facts. Do not put absolute maintainer paths in it.

## Personal default profile for this user
Encode as defaults where appropriate, without requiring private data:
- `base_timeframe`: `1m`
- `context_timeframes`: `5m`, `15m`, `30m`, `1h`, `4h`, `1d`
- daily trade target: `1-3`
- strict downstream gates:
  - realistic costs required
  - sufficient density for daily 1-3 trades
  - AQ to downstream direction consistency
  - `transition_hazard < 0.60`
  - `pda_hybrid_alignment=true`
  - `execution_readiness >= 0.65`

## Privacy and no-pollution rules
- Default output directory should be under `/tmp/...`.
- Generated public artifacts must not contain `/Users/`, `Downloads`, local source roots, API keys, tokens, broker accounts, or provider secrets.
- If `--pa-agent-root` is blocked by macOS/TCC or permission issues, record source-access warnings in the artifact and fall back to embedded defaults.
- Do not import `support/docs/plans/*.md` into runtime code; handoff docs are not runtime inputs.
- Preserve broad dirty worktrees; stage only the coherent current-slice files.

## Verification pattern
Run:
```bash
python3 -m unittest support.scripts.research.tests.test_pa_agent_intake
python3 support/scripts/research/pa_agent_intake.py --compact --output-dir /tmp/ict-engine-pa-agent-intake-zero
python3 support/scripts/research/pa_agent_intake.py --compact --pa-agent-root <PA_AGENT_ROOT> --include-prompt-inventory --output-dir /tmp/ict-engine-pa-agent-intake-optin
python3 -m py_compile support/scripts/research/pa_agent_intake.py support/scripts/research/tests/test_pa_agent_intake.py
```

Then inspect generated JSON:
- `trade_usable=false` in bundle, candidate template, and artifact index.
- `artifact_index.json` has relative artifact names only.
- no `/Users/` or `Downloads` in generated JSON.
- taxonomy and router-rule counts match expectations.

## Concrete repo slice from 2026-05-20
Implemented files:
- `support/scripts/research/pa_agent_intake.py`
- `support/scripts/research/tests/test_pa_agent_intake.py`
- `support/examples/pa_agent_intake_profile.example.json`
- `support/docs/plans/2026-05-20-pa-agent-intake-handoff-todo.md`

Commits:
- `f8df4683 Add PA Agent intake artifacts`
- `70dcab53 Add PA Agent intake artifact index`
