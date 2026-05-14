# SMT Training Contract Readback v1

Source evidence: `docs/experiments/actionable-regime-confidence/runs/20260512T215037+0800-codex-smt-provider-window-event-alignment-expansion-v1/`.

This readback does not promote SMT, start Auto-Quant, rerun provider fetches, or feed Pre-Bayes, BBN, CatBoost/path-ranker, execution tree, or feedback/update learning. It records the training contract that the next SMT sample-expansion run must satisfy.

## Definition Lock

SMT is sibling-market liquidity-sweep swing confirmation failure at the same timeframe, same overlapping session, and same swing/liquidity event window.

SMT is not ordinary correlation, not a loose related-market description, and not relative strength by itself. Recent correlation is only a relationship stability gate for choosing a comparable symbol.

For inverse relationships, the comparison symbol structure must be normalized before HH/LL logic is applied. The output must also carry `normalized_for_inverse_correlation=true` and the raw comparison structure fields so the normalization cannot hide the original event.

## Required Output Fields

Every row must carry:
- `base_symbol`
- `comparison_symbol`
- `relationship_type`
- `relationship_confidence`
- `timeframe`
- `session`
- `smt_signal`
- `base_swing_type`
- `base_level`
- `comparison_swing_type`
- `comparison_level`
- `swept_side`
- `normalized_for_inverse_correlation`
- raw comparison structure for inverse lanes
- `near_pd_array`
- `pd_array_type`
- `mss_or_cisd_confirmed`
- `displacement_confirmed`
- `confidence`
- `fail_closed_reason`

SMT rows must remain `confirmation_role=confirmation_only` and `actionable=false`.

## Current 215037 Readback

Current valid files:
- `materials/smt_provider_window_event_alignment_expansion_packet.json`
- `summaries/smt_provider_window_event_alignment_expansion_rows.csv`
- `summaries/smt_provider_window_event_alignment_expansion_per_regime.csv`
- `summaries/smt_provider_window_event_alignment_expansion_pair_summary.csv`

Current valid checks:
- `checks/01_py_compile.exit=0`
- `checks/02_build.exit=0`
- `checks/03_assert.exit=0`
- `checks/codex_local_01_py_compile.exit=0`
- `checks/codex_local_02_build.exit=0`
- `checks/codex_local_03_assert.exit=0`

Current counts:
- `rows=72`
- `smt_signal_rows=72`
- `strict_trade_count=15`
- `min_trade_count_for_learning=30`
- `inverse_normalized_signal_rows=7`
- `actionable_true_count=0`
- `pair_coverage_met=false`
- `aggregate_learning_floor_met=false`
- `per_regime_learning_floor_met=false`

Per-regime strict statistics:
- `trend`: `trade_count=5`, `win_rate=0.6`, `expectancy=-0.018098369090827494`, `fail_closed_reason=insufficient_per_regime_trade_count`
- `range`: `trade_count=3`, `win_rate=1.0`, `expectancy=-0.0010590821324696369`, `fail_closed_reason=insufficient_per_regime_trade_count`
- `transition`: `trade_count=7`, `win_rate=0.5714285714285714`, `expectancy=0.0010949474062277881`, `fail_closed_reason=insufficient_per_regime_trade_count`
- `stress`: `trade_count=0`, `win_rate=null`, `expectancy=null`, `fail_closed_reason=insufficient_per_regime_trade_count`
- `other`: `trade_count=0`, `win_rate=null`, `expectancy=null`, `fail_closed_reason=insufficient_per_regime_trade_count`

Pair strict statistics:
- `NQ/ES`: `relationship_type=positive`, `event_count=12`, `strict_trade_count=2`
- `NQ/YM`: `relationship_type=positive`, `event_count=0`, `strict_trade_count=0`
- `EURUSD/GBPUSD`: `relationship_type=positive`, `event_count=4`, `strict_trade_count=1`
- `EURUSD/DXY`: `relationship_type=negative`, `event_count=1`, `strict_trade_count=0`
- `XAUUSD/XAGUSD`: `relationship_type=positive`, `event_count=9`, `strict_trade_count=2`
- `XAUUSD/DXY`: `relationship_type=negative`, `event_count=6`, `strict_trade_count=2`
- `BTC/ETH`: `relationship_type=positive`, `event_count=40`, `strict_trade_count=8`

## Training Gate

The next SMT expansion may only become downstream-eligible if all of these are true:
- same timeframe and same session overlap are true for every signal row
- relationship stability gate passes for each comparison lane
- every signal row has both `base_level` and `comparison_level`
- inverse lanes preserve both normalized and raw comparison structure
- `mss_or_cisd_confirmed=true`
- `displacement_confirmed=true`
- `near_pd_array=true`
- strict forward outcome is present
- per-regime `trend/range/transition/stress/other` statistics are emitted
- required lanes include at least `NQ/ES/YM`, `EURUSD/GBPUSD/DXY`, `XAUUSD/XAGUSD/DXY`, and `BTC/ETH`
- single-market evidence is not promoted as a generic factor

Current gate result: fail closed.

## Next Sample Targets

The next SMT-specific run should not repeat a generic correlation scan. It should only add strict-entry-context-complete samples near the same liquidity event model:
- `NQ/YM`: needs event discovery first; current `event_count=0`
- `EURUSD/DXY`: needs inverse-normalized strict examples; current `strict_trade_count=0`
- `stress`: needs strict examples; current `trade_count=0`
- `other`: needs strict examples or an explicit reason this bucket is out of scope
- all pairs: need more rows where MSS/CISD, displacement, PDA, and forward outcome are complete

Downstream remains closed until those sample targets satisfy the gate.
