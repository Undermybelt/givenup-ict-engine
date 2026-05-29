# ict-engine Agent Skills

This directory contains optional agent-facing skills for `ict-engine`.
They are not Rust runtime inputs, not provider credentials, and not a
replacement for typed engine schemas or tests.

Use these files when an agent needs a compact, repo-local operating contract
before preparing provider data, factor material, Auto-Quant runs, or runtime
evidence packets.

## Active Intake Status

Status: Done
Owner: Codex
Date: 2026-05-14

Scope:
- Review the locally installed external finance skill packs.
- Keep only portable ideas that fit `ict-engine` provider and evidence rules.
- Add a small root `skills/` surface without copying untrusted installers,
  private endpoints, API keys, hooks, managed-agent deploy scripts, or market
  opinion prompts.

## Included Skills

| Skill | Purpose | Source Ideas Absorbed |
|---|---|---|
| `provider-selection` | Force provider choice before live or low-timeframe work; prefer IBKR for explicit low-timeframe broker data, but ask the user and fail closed if setup is missing. | Hubble's market-data routing idea, sanitized to remove hard-coded provider defaults. |
| `macro-regime-context` | Convert macro liquidity and cross-asset stress into structured regime evidence. | Day1Global macro/sentiment framework and financial-services rates context, sanitized to structured evidence only. |
| `options-dealer-context` | Convert options chain, IV, skew, gamma walls, and 0DTE pressure into structured evidence for regime and execution tree features. | financial-services option-vol-analysis workflow, adapted to `ict-engine` fail-closed provider policy. |
| `market-structure-context` | Convert ICT/SMC structural observations such as BOS, CHoCH, order blocks, fair value gaps, premium/discount, and liquidity sweeps into structured evidence. | OpenMobius-skill structural taxonomy and freshness discipline, sanitized to provider-backed evidence only. |
| `factor-source-intake` | Use blocked/waiting windows for interruptible paper, repository, strategy, and indicator intake that produces codeable regime-rooted candidates without launching shared runtime work. | ict-engine Board B factor-training contract plus public source-intake discipline. |

## External Skill Review

| Source | Verdict | Reason |
|---|---|---|
| `anthropics/financial-services` | Partial absorb, do not vendor wholesale. | Strong finance workflows, but many skills assume MCP data vendors, managed agents, Excel/PowerPoint tooling, Microsoft 365 install paths, or deployment scripts. Suitable as methodology, not runtime dependency. |
| `HubbleVision/hubble-data-service-skill` | Do not vendor raw. | The raw skills force a private Hubble API endpoint and fixed API key, forbid other providers, and make market-data source choices on behalf of the user. That conflicts with provider-neutral consumer behavior. |
| `star23/Day1Global-Skills` | Partial absorb, do not vendor raw. | Useful macro, sentiment, and BTC-cycle checklists, but raw skills rely on broad web search, contain recommendation language and promotional footer requirements, and are not structured runtime evidence. |
| `wbh604/UZI-Skill` | Do not vendor raw. | Heavy installer/scripts/hooks, A-share stock-analysis assumptions, social/report generation, local cache gates, and optional tunnel behavior are outside `ict-engine` runtime boundaries. Only the general risk-checklist pattern is reusable elsewhere. |
| `MobiusQuant/OpenMobius-skill` | Partial absorb, do not vendor raw. | Strong ICT/SMC structural taxonomy and freshness rules, but the raw runtime depends on Mobius API calls, local embeddings/index build, Playwright/browser assets, and chart/image flows outside `ict-engine` runtime boundaries. |

## Hard Boundaries

- Do not run external installers, hooks, MCP connectors, package managers, or
  managed-agent deploy scripts from reviewed repos as part of these skills.
- Do not copy hard-coded API endpoints, API keys, private paths, or local cache
  assumptions into `ict-engine`.
- Do not make `ict-engine` parse this directory at runtime. Promote any needed
  rule into typed config, command flags, schemas, fixtures, or tests first.
- Do not silently default generic market-data work to Binance, Hubble, IBKR, or
  any other single provider. Ask the user, inspect `provider-status`, and record
  the chosen provider in the evidence packet.
- SMT, FVG/IFVG, order-block, liquidity, options, and macro outputs remain
  confirmation/evidence fields until runtime gates promote them.
