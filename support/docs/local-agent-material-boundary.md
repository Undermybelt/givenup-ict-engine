# Local Agent Material Boundary

Date: 2026-05-22

Purpose: keep public `ict-engine` source, release exports, and consumer
defaults free of local agent workspace material while preserving useful local
references for operators who explicitly choose to use them.

## Boundary

- Versioned project documentation belongs under `support/docs/`.
- Root `docs/` is reserved for local Aegis/spec workspace material and is not a
  public runtime or release source by default.
- Root `skills/` is reserved for optional agent-facing skill drafts and is not a
  Rust runtime input.
- If a rule must affect `ict-engine` behavior, promote it into typed config,
  command flags, schemas, fixtures, or tests before relying on it.
- If a reference should become public contributor documentation, migrate the
  durable summary into `support/docs/` first.

## Current Local Roots

- `docs/aegis/**`
  - Local Aegis workspace with baseline, spec, and work evidence files.
  - Useful as operator context, but not a release/default input.
- `skills/**`
  - Optional agent-facing contracts for provider selection, macro regime
    context, and options dealer context.
  - `skills/manifest.json` declares `runtime_consumed_by_ict_engine=false`.

## Release And Consumer Rules

- Do not copy root `docs/` or root `skills/` into sanitized release exports by
  default.
- Do not make zero-config consumer flows depend on these roots.
- Do not parse these roots from Rust or Python runtime paths.
- Users may choose to reuse the local material explicitly, but public defaults
  remain zero-config and provider-neutral.

## Migration Rule

When a local agent note becomes durable project policy:

1. Copy only the distilled policy or evidence summary into `support/docs/`.
2. Replace private paths, local profile names, and operator-specific details
   with public-safe wording.
3. Add tests or typed config when behavior changes.
4. Leave the root local workspace ignored unless it is intentionally promoted
   as versioned project source.
