---
name: ict-engine-surface-intgr
description: >
  Class-level umbrella for ict-engine feature/surface integration work: extending FrameFeatures,
  wiring timed PDA and BBN evidence, safely integrating new output surfaces into main.rs,
  and staged extraction/triage of monolithic integration paths.
tags:
  - ict-engine
  - integration
  - surfaces
  - mainrs
  - reporting
  - pda
  - bbn
version: 1
---

# ict-engine surface and integration

## Goal
- Provide one umbrella for the integration class of ict-engine work.
- Cover new feature insertion, output/reporting surface wiring, timed-PDA/BBN integration, and staged extraction from a monolithic `main.rs`.
- Keep incident-specific migration notes and special-case wiring details in references.

## Use when
- The user wants to add new features or fields to ict-engine’s data/reporting surfaces.
- The task is about wiring new outputs into `main.rs` or application/reporting surfaces.
- The task involves timed PDA / BBN evidence integration.
- The task involves safe staged extraction from a large, coupled integration surface.

## Class-level workflow
1. Identify the true integration layer:
   - feature struct / trace layer
   - reporting surface
   - BBN/pre-bayes surface
   - main.rs wiring layer
   - staged extraction boundary
2. Add or patch the smallest stable surface first.
3. Prefer helper/adaptor extraction before large implementation moves.
4. Verify after each slice with fmt/check/test.
5. Only report success once the real integration surface, not just a facade, has moved or been wired.

## Problem classes

### 0. Auto-Quant post-factor runtime closure
Use this class when a factor/regime candidate already has research evidence and must cross public runtime surfaces: strategy-library import, BBN prior/posterior update, artifact lineage, workflow/execution-tree evidence, and path-ranking readiness. See `references/auto-quant-runtime-closure.md` for the pandas-script bridge pattern and evidence bundle shape.

### 1. Feature-surface extension
Use this class when adding fields like FrameFeatures or similar structured signals and propagating them through traces, summaries, and report surfaces.

### 2. Timed-PDA / BBN / pre-bayes integration
Use this class when converting conceptual/state-machine ideas into durable typed data that must appear in analysis outputs, pre-bayes filters, workflow status, and trade evidence.

### 3. Safe output-surface wiring
Use this class when integrating new report bundles, output adapters, or printing surfaces into `main.rs` without breaking a large monolith.

### 4. Staged extraction / main.rs triage
Use this class when the task is not "add one field" but "reduce or relocate a coupled monolithic implementation safely in stages."

### 5. External data source hotplug provider integration
Use this class when adding an optional external data source (macro, reference, style-factor, corporate-action, etc.) as a hotplug provider in ict-engine without polluting zero-config or breaking consumer workflows. See `references/external-data-source-hotplug-provider.md`.

Typical sequence:
1. Write a Python bridge script under `support/scripts/research/` that defaults to capability/demo JSON output (zero network, zero optional dependency).
2. Add unit tests covering capability metadata, demo fixture, validation errors, and optional output-path writes.
3. Wire into `provider_catalog.rs`: add to `provider_filter_matches_domain`, add a `*_provider_item()` function with script/python/module probes, call `apply_provider_user_semantics` or set fields inline.
4. Update README/README.zh-CN.
5. Create a live handoff TODO under `support/docs/plans/` tracking each slice.
6. Commit only the coherent slice with explicit `git add` paths.

## Global rules
- Prefer unique helpers and narrow adapters over broad in-place rewrites.
- Do not confuse a facade or re-export with a true implementation migration.
- Verify type surfaces before attempting deep emit/wiring migrations.
- For post-factor closure, use public CLI surfaces in an isolated `/tmp/...` state before reopening Rust code.
- Prior-init alone is partial closure; posterior ingestion, artifact lineage, workflow/execution-tree surfaces, and path-ranking readiness still need evidence or explicit blockers.
- When in doubt, extract shared helpers first and leave workflow-heavy cores for later.

## What belongs in support files
- exact insertion points for FrameFeatures work
- timed PDA integration path and test strategy
- safe main.rs output wiring patterns
- staged extraction and recovery rules for coupled code paths
- workflow/handoff-specific integration guidance

## Verification
- `cargo fmt --all`
- `cargo check`
- targeted `cargo test` where appropriate
- full `cargo test` before claiming a significant integration slice is done
- graph rebuild if the repo workflow expects it

## See references
- `references/auto-quant-runtime-closure.md`
- `references/auto-quant-runtime-closure.md`
- `references/factor-signal-diagnostics-hotplug.md` — QuantInvestStrats-style signal diagnostics intake: zero-config support script first, optional hotplug profile/converters, candidate-pack `--demo`/`--signal-diagnostics-json`, compact stdout, `/tmp` artifacts, and `trade_usable=false` until downstream gates pass.
- `references/frame-feature-extension.md`
- `references/pda-bbn-integration.md`
- `references/safe-main-output-integration.md`
- `references/staged-mainrs-extraction.md`
- `references/workflow-handoff-blocking-truth.md`
- `references/market-state-design-principles.md` — 市场状态分类模块设计原则：零配置、热插拔、Token 友好、高置信度、无污染、无负债
- `references/pa-agent-intake-hotplug.md` — PA_Agent 价格行为/LLM trace 吸收为 ict-engine observation-only 热插拔 artifact 的模式
- `references/external-data-source-hotplug-provider.md` — 外部数据源热插拔 provider 集成：Python bridge 脚本三模式、provider_catalog.rs 探测/probe 模式、测试清单、pitfall 规则
