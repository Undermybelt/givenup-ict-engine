# 112954 Pre-Bayes Provider Data Rerun v1

Run id: `20260512T114101+0800-codex-112954-prebayes-provider-data-rerun-v1`

## Scope

This isolated rerun copies the settled `112954` symbol-normalized path-ranker state, derives analyze-ready BTC JSON from the registered `112315` yfinance provider rows, runs `analyze` to populate Pre-Bayes/filter fields, then reruns structural target export, CatBoost/path-ranker training/application, runtime enablement, and workflow readbacks.

## Evidence

- Source path-ranker state: `docs/experiments/actionable-regime-confidence/runs/20260512T112954+0800-codex-111403-symbol-normalized-path-ranker-bridge-v1`
- Provider data source: `docs/experiments/actionable-regime-confidence/runs/20260512T112315+0800-codex-board-b-six-provider-btc-matrix-probe-v1`
- State dir: `docs/experiments/actionable-regime-confidence/runs/20260512T114101+0800-codex-112954-prebayes-provider-data-rerun-v1/state_prebayes_provider_data_v1`
- Provider JSON rows: 1h `983`, 4h `246`, 1d `41` from `2026-04-01T00:00:00Z` to `2026-05-11T23:00:00Z`
- Pre-Bayes policy present: `True`; gate `pass_neutralized`; canonical regime `range`; confidence `0.523311097658614`
- Raw scored mature: `293/30`
- Production validation: `292/30`
- Observation validation: `146/30`
- Trainer artifact ready: `True` `catboost`
- Runtime enabled/ready/status: `True` / `True` / `enabled_candidate_set_ready`
- Closed-loop status: `fail_closed`; ready `False`; actionable `False`; review `observe`; reason `exact_structural_branch_visible_but_not_ready_or_actionable`
- Command-shape correction: initial binary `.cbm` artifact registration failed with `Error: stream did not contain valid UTF-8`; corrected score CSV registration succeeded in `08b`.

## Decision

This closes the immediate same-branch Pre-Bayes-empty blocker for the copied `112954` state: Pre-Bayes policy/gate fields are now present on the same symbol and rooted branch context. It is still not a Board A promotion packet: provider data came from a prior registered provider-layer root, not a same-root six-provider Auto-Quant authority packet; selected-history/source-control gates remain false unless separately proven; and execution remains fail-closed unless the workflow output says actionable.
