# Board B 042448 Source Label HistGB Confidence Screen Readback v1

Append-only readback of the completed `042448` source-label HistGradientBoosting
confidence screen. This does not edit the Current Cursor, does not select
historical data, does not create trade-usable Board B profitability evidence,
and does not call `update_goal`.

## Evidence

- `docs/experiments/actionable-regime-confidence/runs/20260512T042448-codex-source-label-histgb-confidence-screen-v1/command-output/source_label_histgb_confidence_screen.exit`
- `docs/experiments/actionable-regime-confidence/runs/20260512T042448-codex-source-label-histgb-confidence-screen-v1/command-output/source_label_histgb_confidence_screen.stdout.json`
- `docs/experiments/actionable-regime-confidence/runs/20260512T042448-codex-source-label-histgb-confidence-screen-v1/command-output/source_label_histgb_confidence_screen.stderr.txt`
- `docs/experiments/actionable-regime-confidence/runs/20260512T042448-codex-source-label-histgb-confidence-screen-v1/command-output/source_label_equivalence_verifier.exit`
- `docs/experiments/actionable-regime-confidence/runs/20260512T042448-codex-source-label-histgb-confidence-screen-v1/command-output/source_label_equivalence_verifier.stdout.txt`

## Readback

- `source_label_histgb_confidence_screen.exit=0`; stderr was empty.
- The equivalence verifier exited `0` with `status=schema_ready_unscored`.
- The screen scored `248,440` source-label rows across roots
  `Bear`, `Bull`, `Crisis`, and `Sideways` using a
  `HistGradientBoostingClassifier` with `70` features.
- `accepted_histgb_confidence_95_labels=[]`.
- Every root label failed at least one required high-confidence split gate
  across `calibration`, `heldout_market`, `heldout_time`, and `test`.
- Promotion status explicitly reports `accepted_rows_added=0`,
  `new_confidence_gate=false`, `strict_full_objective=false`,
  `trade_usable=false`, and `update_goal=false`.

## Gate

- `diagnostic_only:source_label_histgb_confidence_scored_no_full_acceptance`.
- `fail_closed:no_histgb_confidence_95_labels_accepted`.
- `blocked:user_selected_historical_data_missing`.
- `promotion_allowed=false`.

## Next

Do not promote from schema readiness or source-label confidence diagnostics.
Keep `034002` as the fail-closed cursor. The next qualifying Board B move still
requires explicit user selection of exactly one of `HTF=1d`, `MTF=4h`, or
`LTF=1h`, followed by selected-data factor-research/Auto-Quant and downstream
continuation only if nonzero mature rooted branch observations preserve the
required regime branch path through Pre-Bayes/filter -> BBN ->
CatBoost/path-ranker -> execution tree.
