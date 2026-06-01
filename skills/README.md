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
| `auto-quant-handoff-harness` | Keep Auto-Quant handoffs lane-isolated and reviewable with Life-Harness lifecycle layers, plan/work/review artifacts, and regime feedback evidence packets before adoption review. | Life-Harness four-layer runtime adaptation, TraderAlice/Auto-Quant README/program usage contract, and Claude Code Harness plan/work/review pattern, absorbed without plugin installers, hooks, MCP setup, or bundled binaries. |
| `ict-engine-runtime` | Mirror the Hermes ict-engine runtime pipeline skill for factor-to-filter-to-BBN-to-path-ranker-to-execution-tree work. | Local Hermes runtime skill, copied into the repo with private paths redacted. |
| `ict-engi-fact-rese-muta` | Mirror the Hermes factor research, mutation, cost, session-scope, and repo-hygiene skill for profitability-factor work. | Local Hermes factor-training skill, copied into the repo with private paths redacted. |
| `ict-engine-maintenance-loop` | Mirror the Hermes maintenance, commit hygiene, provider/runtime repair, done-definition, and skill-update loop. | Local Hermes maintenance skill, copied into the repo with private paths redacted. |
| `ict-engine-release-mirror-ci` | Mirror the Hermes release mirror and cross-OS CI correction skill for publication work. | Local Hermes release skill, copied into the repo with private paths redacted. |
| `ict-engine-surface-intgr` | Mirror the Hermes surface integration skill for FrameFeatures, PDA/BBN wiring, reporting surfaces, and staged extraction. | Local Hermes integration skill, copied into the repo with private paths redacted. |
| `mark-spec-fram-feat-fork` | Mirror the Hermes market-specific FrameFeatures fork skill for pre-Bayes label repair when factor evidence is strong. | Local Hermes label-repair skill, copied into the repo with private paths redacted. |

The `ict-engine-*`, `ict-engi-*`, and `mark-spec-fram-feat-fork` entries are
repo-local mirrors of installed Hermes skills. They are useful for clone-local
agent context, but the live router still loads the installed `~/.hermes` skill
unless an operator explicitly uses this repo copy. Keep the repo mirrors
portable: replace maintainer home paths, private data roots, local Python
venvs, and raw cache paths with placeholders such as `<ict-engine-repo>`,
`<managed-auto-quant-checkout>`, `<provider-python>`, or
`<private-tomac-data-cache>`.

Do not use this directory as a place to preserve failed factor-training residue.
Temporary plans, scratch runners, local screen output, AQ/Freqtrade state,
caches, model output, and non-promoted run trees stay under `/tmp` unless they
are deliberately tracked or force-added as an evidence packet, product
surface, test fixture, or reviewed durable reference. The done-definition gate
`repo_training_scratch_surface` is the enforcement point for this boundary.

`factor-source-intake` includes `references/waiting-window-factor-research.md`
for productive claim/runtime waiting windows. It keeps all source-intake output
as candidate material only; no practical flags or runtime launches are allowed
from that work.
`references/paper-strategy-reserve-20260530.md` is the current compact reserve
of paper, strategy, and indicator seeds gathered for future factor candidates.
`references/crossasset-carry-risk-reserve-20260530.md` captures lower-turnover
cross-asset, carry, commodity term-structure, and variance-risk gate reserves
for later owned Gate 1 slices.
`auto-quant-handoff-harness` is the companion for `factor-research` and
`factor-autoresearch` handoff payloads. It requires `agent_workflow` fields,
lane-local `AUTO_QUANT_WORKSPACE` usage, measured review artifacts, and an
explicit boundary that Auto-Quant success is candidate evidence only. Completed
AQ/exact-AQ runs must also emit
`checks/regime_feedback_evidence_packet.json` so cost-positive or failed
regime-root evidence feeds regime observation/calibration without becoming
accepted paper/live feedback. That packet must name the pending belief-network
and execution-tree placement targets; those targets remain pending until
accepted paper/live feedback, BBN readback, execution-tree readback, same-tree
practical closure, and terminal `trade_usable=true` all pass.
The skill also absorbs TraderAlice/Auto-Quant's core harness rule: `prepare.py`,
`run.py`, `config.json`, shared data, and templates are the read-only evaluation
contract, while each factor iteration must modify the matching strategy file,
measure through `run.py`, update `results.tsv`, and write lane-local
`plan.md`/`review.md` evidence before returning to ict-engine.
It also absorbs Life-Harness as a runtime-interface method: handoff payloads
must expose environment contract, procedural skill, action realization, and
trajectory regulation layers; mine measured failures into `failure_patterns.md`;
return layer assignments, safety rationale, regression review, and remaining
failures; and freeze returned artifacts before ict-engine adoption evaluation.
`auto-quant-adoption-review` must surface `life_harness_review` so external
execution readiness stays separate from adoption/practical-readiness allowance.
`auto-quant-status` must keep that boundary visible through a fail-closed
`life_harness_hint` when a Life-Harness handoff exists.
Do not apply Life-Harness layer language to non-LLM-agent harnesses such as
`market-data-harness`, `structural_feedback_replay_harness.py`, or
`factor_candidate_harness_presets.json`; those remain governed by their native
provider/data, replay, and preset contracts unless a future agent loop is added.
Release-clone agents must also be reminded to bootstrap the managed checkout
from `https://github.com/undermybelt/Auto-Quant`; maintainer-local paths are
not part of the public startup contract.

## External Skill Review

| Source | Verdict | Reason |
|---|---|---|
| `anthropics/financial-services` | Partial absorb, do not vendor wholesale. | Strong finance workflows, but many skills assume MCP data vendors, managed agents, Excel/PowerPoint tooling, Microsoft 365 install paths, or deployment scripts. Suitable as methodology, not runtime dependency. |
| `HubbleVision/hubble-data-service-skill` | Do not vendor raw. | The raw skills force a private Hubble API endpoint and fixed API key, forbid other providers, and make market-data source choices on behalf of the user. That conflicts with provider-neutral consumer behavior. |
| `star23/Day1Global-Skills` | Partial absorb, do not vendor raw. | Useful macro, sentiment, and BTC-cycle checklists, but raw skills rely on broad web search, contain recommendation language and promotional footer requirements, and are not structured runtime evidence. |
| `wbh604/UZI-Skill` | Do not vendor raw. | Heavy installer/scripts/hooks, A-share stock-analysis assumptions, social/report generation, local cache gates, and optional tunnel behavior are outside `ict-engine` runtime boundaries. Only the general risk-checklist pattern is reusable elsewhere. |
| `MobiusQuant/OpenMobius-skill` | Partial absorb, do not vendor raw. | Strong ICT/SMC structural taxonomy and freshness rules, but the raw runtime depends on Mobius API calls, local embeddings/index build, Playwright/browser assets, and chart/image flows outside `ict-engine` runtime boundaries. |
| `TraderAlice/Auto-Quant` | Partial absorb, do not vendor raw. | Strong autoresearch harness contract: agent-owned strategy files, read-only `prepare.py`/`run.py`/`config.json`, `results.tsv` event log, and repeated measured backtests. ict-engine keeps those mechanics but leaves promotion to its own adoption, feedback, and practical-readiness gates. |
| `Tianshi-Xu/Life-Harness` | Methodology absorb, do not vendor raw. | Useful four-layer runtime adaptation and failure-mining loop; raw benchmark runtimes, Docker/uv setup, model/provider calls, and evaluation harnesses stay outside ict-engine. |

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
