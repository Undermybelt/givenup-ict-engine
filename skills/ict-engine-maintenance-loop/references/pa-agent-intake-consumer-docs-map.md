# PA Agent intake consumer-docs pattern

Use when absorbing a local or external price-action / agent repo into ict-engine as optional evidence without making it runtime authority.

## Durable pattern

- Keep clean-checkout behavior zero-config by embedding safe defaults in the intake script.
- Make local source parsing explicit opt-in, for example `--pa-agent-root /path/to/source`.
- Make user-specific reuse explicit opt-in, for example `--profile support/examples/<name>.example.json`.
- Emit a compact `artifact_index.json` first-class consumer surface with:
  - `trade_usable=false`
  - promotion/observation state
  - counts and timeframe ladder
  - warnings
  - relative artifact names only
- Keep full bundles observation-only until ict-engine downstream gates promote them.
- Put generated artifacts under `/tmp/...` or an explicit output/state dir, never under repo examples by default.
- Link the intake from both `support/examples/README.md` and the top-level `support/docs/README.md` only after the compact index and examples exist.
- Update a live handoff TODO in the same slice so the next agent sees what is done, what was verified, and what remains.

## Verification checklist

Run focused verification before committing the docs/intake slice:

```bash
python3 -m unittest support.scripts.research.tests.test_pa_agent_intake
python3 support/scripts/research/pa_agent_intake.py --compact --output-dir /tmp/ict-engine-pa-agent-intake-smoke
rg -n '/Users/|Downloads' support/docs/README.md support/docs/plans/<handoff>.md support/examples/<intake>/README.md support/examples/README.md || true
git diff --check -- <explicit-current-slice-paths>
```

Inspect generated `artifact_index.json` and require:

- `trade_usable=false`
- artifact names are relative
- no `/Users/` or `Downloads` leakage

## Commit discipline

Stage only explicit intake/docs/handoff paths. Do not stage broad dirty Board A/B or unrelated experiment residue.
