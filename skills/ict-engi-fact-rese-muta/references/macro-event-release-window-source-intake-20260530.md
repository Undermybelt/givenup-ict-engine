# Macro Event Release-Window Source Intake - 2026-05-30

Use this when a future ict-engine profitability-factor lane wants to add FOMC,
CPI, Employment Situation/NFP, CME holidays, or other scheduled macro-event
release windows as a sidecar for NQ/ES or related futures factors.

## Session Evidence

Waiting-window packet:

- repo packet: `support/docs/experiments/actionable-regime-confidence/20260530T030159+0800-codex-nq-es-macro-event-release-window-sidecar-source-intake.md`
- workdoc: `/tmp/ict-engine-nq-es-macro-event-release-window-sidecar-source-intake-20260530T030159+0800/workdoc.md`
- terminal metrics: `/tmp/ict-engine-nq-es-macro-event-release-window-sidecar-source-intake-20260530T030159+0800/checks/terminal_metrics.json`
- claim: `/tmp/ict-engine-agent-claims/board-b-factor-refinement/20260530T030159+0800-codex-nq-es-macro-event-release-window-sidecar-source-intake.claim`

The packet was created while compact audit reported fresh CL/WTI and NQ
overnight-inventory claims. No provider, IBKR, Auto-Quant, Freqtrade,
paper/sim/live, lifecycle, local screen, or downstream command was launched.
The claim was terminalized immediately as
`terminalized_no_launch_source_intake_only`.

## Source Checks

Crossref returned matching metadata for macro-announcement / price-discovery
work:

- Andersen, Bollerslev, Diebold, Vega, DOI `10.3386/w11312`.
- Andersen, Bollerslev, Diebold, Vega, DOI `10.3386/w8959`.
- Boyd, Hu, Jagannathan, DOI `10.3386/w8092`.

Official-data probes:

- Fed FOMC calendar returned HTTP `200`.
- BLS CPI and Employment Situation schedule pages returned HTTP `403` from this host.
- CME holiday calendar failed from this host with TLS EOF.

Therefore the official event-calendar data source remains incomplete. The paper
metadata is hypothesis support only; it is not a runtime data contract.

## Reusable Guardrail

Scheduled macro-event sidecars must use a verified historical event calendar
with timezone, release timestamp, event type, and data availability known before
the parent entry. Do not use actual/surprise values as if they were known before
the release. Do not infer event-window labels from price volatility alone. Do
not treat a reachable current calendar page as proof of historical coverage.

Treat the candidate as a sidecar only:

```text
TransitionRisk -> ScheduledMacroEvent -> ReleaseWindowVolatilityShock -> ParentEntrySkipOrThrottle -> nq_es_macro_event_release_window_sidecar_v1
```

It has no standalone entry. It may only skip, delay, size down, shorten hold,
or require stronger post-release confirmation for an already owned parent NQ/ES
trend, MIM, carryover, or reversal branch. If cadence rises after the sidecar,
reject the design.

## Admission Rule

Keep `promotion_allowed=false`, `trade_usable=false`, and `update_goal=false`
until all are true:

- compact claim audit is clear for the owned parent lane;
- a historical event calendar is verified with release timestamp and timezone
  availability before parent entry;
- parent futures cost model is verified;
- ETH/full retained-session rows outside RTH are proven for the parent data;
- event-window slippage/fill stress is evaluated instead of assuming normal
  fills through scheduled releases;
- same-root practical lifecycle evidence passes the normal ict-engine gates.
