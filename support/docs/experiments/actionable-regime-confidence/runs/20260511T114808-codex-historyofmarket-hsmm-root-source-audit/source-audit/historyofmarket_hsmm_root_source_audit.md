# HistoryOfMarket / HSMM Root Source Audit

Run ID: `20260511T114808+0800-codex-historyofmarket-hsmm-root-source-audit`

## Scope

- Active taxonomy: `MainRegimeV2`.
- This is a targeted parent-root source acquisition audit, not a generic Kaggle/HF/public sweep.
- Candidates: History of Market S&P 500 Log YoY and Wang/Gupta/Zhang Bear/Bull/Sidewalk/Crash HSMM paper.

## History of Market

- Public JSON rows: `24705`.
- Date range: `1927-12-30` to `2026-05-08`.
- Page declares positive log-YoY as Bull and negative as Bear: `true`.
- Approx computed log-YoY rows: `24455`.
- Derived label counts: `Bull=17020`, `Bear=7435`.
- Approx zero crossings: `384`.
- Decision: `blocked_historyofmarket_formula_derived_price_only_two_root_spx_daily_source`.

Blockers:
- formula-derived S&P 500 price/log-YoY label, not an independent full-matrix source-label panel.
- no `Sideways` or `Crisis` root.
- daily S&P 500 only; no provider/instrument/timeframe/full-species coverage.
- circular if used as both detector and label.

## HSMM Paper

- Candidate title: `Identifying Bear, Bull, Sidewalk, and Crash Markets in the United States`.
- Public fetch statuses: `200:ok`, `404:blocked`, `404:blocked`.
- Four-state terms found in public pages: `true`.
- Row-level decoded-state export found: `true`.
- Decision: `blocked_hsmm_paper_methodology_no_materialized_row_export`.

Blockers:
- public pages expose methodology/paper, not row-level decoded state labels.
- model-inferred states are not attachable provider/instrument/timeframe source-label windows.
- no calibration/cross-context panel can be materialized from the public surface.

## Decision

- Accepted parent-root slots added: `0`.
- Accepted direct `Manipulation` rows added: `0`.
- Gate result: `blocked_historyofmarket_hsmm_no_attachable_full_matrix_mainregimev2_panel`.
- Runtime code changed: `false`.
- Thresholds relaxed: `false`.
- Raw data committed: `false`.
- Trade usable: `false`.

Acquire an exact provider/instrument/timeframe MainRegimeV2 label panel or explicit owner-approved crosswalk; do not count formula-derived price labels or paper-only HSMM states.
