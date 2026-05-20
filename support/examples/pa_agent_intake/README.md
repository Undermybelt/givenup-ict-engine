# PA Agent intake example

Purpose: convert PA Agent price-action taxonomy, router hints, and decision-trace
shape into ict-engine observation artifacts. This is not a trading signal by
itself.

Zero-config smoke:

```bash
python3 support/scripts/research/pa_agent_intake.py \
  --compact \
  --output-dir /tmp/ict-engine-pa-agent-intake
```

Consumer entrypoint:

```text
/tmp/ict-engine-pa-agent-intake/artifact_index.json
```

Read `artifact_index.json` first. It is the token-friendly surface: counts,
trade-usable state, timeframe ladder, warnings, and relative artifact names.

Opt in to a local PA Agent checkout only when you choose to:

```bash
python3 support/scripts/research/pa_agent_intake.py \
  --pa-agent-root /path/to/PA_Agent \
  --include-prompt-inventory \
  --compact \
  --output-dir /tmp/ict-engine-pa-agent-intake-pa
```

Opt in to a profile override only when you choose to:

```bash
python3 support/scripts/research/pa_agent_intake.py \
  --profile support/examples/pa_agent_intake_profile.example.json \
  --compact \
  --output-dir /tmp/ict-engine-pa-agent-intake-profile
```

Output contract:

- `trade_usable=false`
- `promotion_state=observation_only` for the bundle
- candidate template is `inactive_by_default` and `candidate_observation`
- generated artifact paths belong under `/tmp/...` or an explicit state dir
- no local PA Agent path is required for clean-checkout use
- PA Agent source read failures become `source_access_warnings`, not hard failures

Promotion still requires ict-engine downstream evidence: realistic costs,
trade density, AQ to downstream direction consistency, Pre-Bayes/BBN,
path-ranker/CatBoost, execution tree, and feedback/update gates.