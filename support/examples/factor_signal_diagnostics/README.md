# Factor signal diagnostics hotplug

Purpose: turn a factor signal panel into compact Gate 1/2 diagnostic evidence, then optionally attach that evidence to a candidate pack.

Default path is zero-config and writes nothing into the repo:

```bash
python3 support/scripts/research/factor_signal_diagnostics.py --demo --compact
```

Write a JSON report outside the repo:

```bash
python3 support/scripts/research/factor_signal_diagnostics.py \
  --demo \
  --output /tmp/ict-engine-factor-signal-diagnostics/report.json \
  --compact
```

Use a personal ladder only when explicitly selected:

```bash
python3 support/scripts/research/factor_signal_diagnostics.py \
  --input /tmp/my_factor_panel.csv \
  --profile support/examples/factor_signal_diagnostics/personal_hotplug_profile.example.json \
  --cost-bps-side 2 \
  --output /tmp/ict-engine-factor-signal-diagnostics/report.json \
  --compact
```

Input CSV contract:

```text
timestamp,asset,horizon,regime,signal,forward_return
```

Attach diagnostics to a candidate pack only when chosen by the caller:

```bash
python3 support/scripts/research/factor_candidate_pack.py \
  --manifest-json /tmp/strategy_library_manifest.json \
  --strategy-name MyStrategy \
  --candidate-spec-json /tmp/candidate_spec.json \
  --signal-diagnostics-json /tmp/ict-engine-factor-signal-diagnostics/report.json \
  --output-dir /tmp/ict-engine-candidate-pack
```

Candidate-pack zero-config smoke:

```bash
python3 support/scripts/research/factor_candidate_pack.py \
  --demo \
  --output-dir /tmp/ict-engine-candidate-pack-demo
```

Output rule: `signal_diagnostics_evidence` is diagnostic-only metadata. It does not make a factor trade-usable. Promotion still requires Pre-Bayes, BBN, path-ranker/CatBoost, execution tree, feedback/update, and strict cost/density gates.
