# Board B Selection Readiness Inventory v1

Run root: `docs/experiments/actionable-regime-confidence/runs/20260512T061318+0800-codex-board-b-selection-readiness-inventory-v1`

Scope: append-only inventory for the three still-required user-selectable paths:
`HTF=1d`, `MTF=4h`, and `LTF=1h`.

This artifact does not select a path, does not edit the Current Cursor, does
not run selected-data Auto-Quant, does not promote any candidate, and does not
call `update_goal`.

## Local Data Inventory

Evidence source: `/Users/thrill3r/Auto-Quant/.venv/bin/python` reading local
Auto-Quant feathers under `/Users/thrill3r/Auto-Quant/user_data/data`.

| Option | Representative Files | Rows / Range | Readiness |
|---|---|---:|---|
| `HTF=1d` | `NQ_USD-1d.feather`, `QQQ_USD-1d.feather` | NQ: `4651` rows, `2011-01-02` to `2025-12-31`; QQQ: `397` rows, `2024-06-03` to `2026-05-08` | local files present; not user-selected |
| `MTF=4h` | `NQ_USD-4h.feather`, `QQQ_USD-4h.feather` | NQ: `23879` rows, `2011-01-02 20:00` to `2025-12-31 20:00`; QQQ: `913` rows, `2024-06-03 12:00` to `2026-05-08 20:00` | local files present; not user-selected |
| `LTF=1h` | `NQ_USD-1h.feather`, `QQQ_USD-1h.feather` | NQ: `89250` rows, `2011-01-02 23:00` to `2025-12-31 21:00`; QQQ: `2755` rows, `2024-06-03 13:00` to `2026-05-08 20:00` | local files present; not user-selected |

The file presence/readability check is readiness evidence only. It is not the
explicit user selection required by the Board B gate.

## Prior Attempt Readback

| Path Shape | Artifact | Result | Gate |
|---|---|---|---|
| prior explicit history profile | `20260512T004649-codex-board-b-220646-explicit-history-selection-v1/measured-explicit-history/explicit_history_tomac_readback_v1.md` | `9` trades, `66.6667%` win rate, `5.28%` total profit, Sharpe `4.1966`; Pre-Bayes blocked and workflow promotion held | `incubation_only_explicit_history_thin_support` |
| agent-selected `LTF=1h` | `20260512T032157-codex-board-b-nq-cost-crisis-repair-v3/downstream-ltf-tomac-normalized-20260512T040232+0800/normalized_tomac_zero_trade_readback_v1.md` | pairlist repaired, Tomac ran, `0` trades, short backtestable window | fail-closed |
| agent-selected `MTF=4h` | `20260512T041143+0800-codex-board-b-032157-agent-selected-mtf-factor-research-v1/sanitized_pair_tomac_readback_v1.md` | sanitized pair ran, `0` trades, no mature rooted observations | fail-closed |

These prior attempts are useful pre-selection readiness and failure-shape
evidence. They do not satisfy `user_selected_historical_data` because the
board explicitly requires an external user choice of exactly one recorded path.

## Prompt-to-Artifact Checklist

| Requirement | Evidence | Status |
|---|---|---|
| Preserve regime-rooted branch path shape | The current board already records `055412`/`054651` branch-segment CatBoost and direct-model contract passes. | partial_contract_only |
| Use real local artifacts, not speculation | This inventory read real local feathers and prior run artifacts. | pass_inventory |
| Do not disturb concurrent Board B work | This run is append-only, creates a new artifact root, and does not rewrite prior rows. | pass |
| Do not self-select `HTF/MTF/LTF` | No option is selected here. | pass_gate_respect |
| Start selected-data Auto-Quant only after explicit selection | Not started. | blocked |
| Require nonzero mature rooted observations before downstream promotion | Prior LTF/MTF attempts had `0` trades; explicit-history had only `9` trades and stayed incubation-only. | blocked |

## Decision

- `selection_readiness_inventory_v1=pass_non_selecting_inventory`.
- `candidate_options_present=HTF_1d,MTF_4h,LTF_1h`.
- `explicit_user_selection_present=false`.
- `selected_data_auto_quant_started=false`.
- `nonzero_mature_rooted_observations=false`.
- `promotion_allowed=false`.
- `update_goal=false`.

Next: keep `034002` as the fail-closed cursor. The next qualifying Board B
action still requires an explicit user reply selecting exactly one of
`HTF=1d`, `MTF=4h`, or `LTF=1h`, then a selected-data Auto-Quant/factor-research
run that produces nonzero mature rooted observations before
Pre-Bayes/filter -> BBN -> CatBoost/path-ranker -> execution tree promotion
checks can advance.
