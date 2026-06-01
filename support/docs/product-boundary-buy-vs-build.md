# Product Boundary: Buy, Adapt, Or Build

This repo should not grow weaker clones of mature quant, broker, data, or
orchestration tools just because an experiment needed a one-off helper.

## Default Decision

- Use existing tools for provider access, broker execution, backtesting,
  feature libraries, model training, and artifact packaging when they already
  have a maintained interface.
- Adapt by adding a narrow bridge, schema, manifest, fixture, or readback check
  when ict-engine needs inspectable evidence from an existing tool.
- Build inside ict-engine only when the behavior is part of the project contract:
  market-structure state, closed-loop evidence, runtime readback, fail-closed
  admission, or user-facing CLI surfaces.

## Repo Boundary

- Non-promoted training lanes, source-intake notes, generated wrappers, local
  model outputs, and trial run trees live in `/tmp`.
- Repo paths are allowed for tracked product surfaces, explicit evidence
  packets, clone-safe fixtures, docs that define durable contracts, and tests.
- A useful scratch artifact is not automatically a product artifact. Convert it
  to an established manifest-backed surface before committing it.

## Factor Work

Factor candidates from papers, repos, blogs, or local sweeps are idea evidence
until they pass current gates. Do not promote or commit loose strategy code
because a local screen was interesting. The candidate must either become a
structured pack/evidence packet, or stay outside the repo.

## Auto-Quant Boundary

Auto-Quant remains the strategy-generation/backtest harness. ict-engine should
consume its outputs through explicit handoff, evidence, and review packets. It
should not absorb Auto-Quant internals unless the behavior is needed for a
stable public contract and has focused tests.
