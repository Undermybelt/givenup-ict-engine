# User-Selected Historical Data Gate v1

This is a non-promoting selection pack for Board B `034002/downstream-combined-v1`.
It does not edit the current cursor and does not satisfy the `user_selected_historical_data` gate by itself.

## Current gate

The active Board B cursor remains `rejected` at `20260512T034002+0800-codex-board-b-nq-cost-crisis-repair-v3-downstream-combined-v1`.

`034002/downstream-combined-v1` mechanically closed the ordered chain with clean wire-fixed ingest, exact rooted branch paths, CatBoost registration/runtime, workflow readback, and execution-candidate readback. Promotion is still blocked because:

- Pre-Bayes stayed `observe_only`.
- BBN evidence was visible/read-only or skipped, not an accepted posterior.
- CatBoost/path-ranker validation had `0/30` production and `0/30` observation with no mature rows.
- Execution-candidate stayed blocked/not actionable.
- Workflow still requires explicit `user_selected_historical_data`.

The later `035139`, `035427`, `035511`, and `040232` LTF sidecars were agent-selected diagnostics. They ran real Auto-Quant/Freqtrade paths but produced zero trades and do not satisfy the user-selection gate.

## Candidate files

All candidates live under:

`docs/experiments/actionable-regime-confidence/runs/20260512T032157-codex-board-b-nq-cost-crisis-repair-v3/downstream-combined-v1/state_combined_v1/B2R_NQ_COST_CRISIS_REPAIR_032157/`

| Option | File | SHA-256 | Rows | Inferred cadence | Coverage | Total volume | Close range | Notes |
|---|---|---:|---:|---|---|---:|---|---|
| HTF | `analyze_nq_htf.json` | `9c737d7c9e198069ac2b91b8786d015912769e829167047901480d76043f6bb0` | 260 | 1d | 2025-03-03T00:00:00Z to 2025-12-31T00:00:00Z | 115987518 | 18850.25 to 28815.75 | Broadest calendar coverage; best candidate for mature chronological context, but only the user can select it. |
| MTF | `analyze_nq_mtf.json` | `807587969339bb879cd3bc6a72d57d53c84b75b501e1df9875e833c9b6d06752` | 260 | 4h | 2025-10-31T16:00:00Z to 2025-12-31T20:00:00Z | 23000551 | 26602.75 to 28735.50 | Balanced intraday/history window; useful if the user wants more bar-level structure than HTF. |
| LTF | `analyze_nq_ltf.json` | `d38aea3d620ea56e12af08d11a22929daa076fcd8bdbe5e630f2b059acd244da` | 260 | 1h | 2025-12-15T12:00:00Z to 2025-12-31T21:00:00Z | 4639574 | 27728.25 to 28739.25 | Shortest window. Agent-selected LTF sidecars already produced zero trades, so this is weakest unless the user explicitly wants the short intraday slice. |

## Required user input

Select exactly one:

- `HTF`: use `analyze_nq_htf.json`
- `MTF`: use `analyze_nq_mtf.json`
- `LTF`: use `analyze_nq_ltf.json`

Until one of these is explicitly selected by the user, further factor-research or structural-feedback runs remain diagnostics and must not be promoted as satisfying `user_selected_historical_data`.

## Next command shape after selection

After explicit selection, rerun factor-research/Auto-Quant in an isolated state and carry only nonzero, mature observations forward:

```bash
./target/debug/ict-engine factor-research \
  --symbol B2R_NQ_COST_CRISIS_REPAIR_032157 \
  --data <selected analyze_nq_*.json> \
  --state-dir <isolated state dir> \
  --backend auto-quant \
  --auto-quant-profile synthetic_ohlcv \
  --output-format json
```

Promotion remains blocked unless the selected run emits a measured rooted branch profitability packet with nonzero trade support and mature observations, then preserves the same `parent_regime_root` and `regime_profit_branch_path` through Pre-Bayes/filter, BBN, CatBoost/path-ranker, and execution tree.

## Interval Correction

Superseding correction: use `docs/experiments/actionable-regime-confidence/runs/20260512T041042-codex-board-b-032157-historical-data-selection-options-v1/selection-options/historical_data_selection_options_v1.md` as the authoritative candidate list for this selection gate.

Correct intervals:

- `htf`: `1d`
- `mtf`: `1h`
- `ltf`: `15m`

Older wording in this file that describes `mtf` as `4h` or `ltf` as `1h` is stale and must not be used for the next rerun.
