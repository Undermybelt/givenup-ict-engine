# Post-Replay 190658 Readback

- Run root: `/Users/thrill3r/projects-ict-engine/ict-engine/docs/experiments/actionable-regime-confidence/runs/20260512T184330+0800-codex-board-a-mature-feedback-replay-maturity-probe-v1`
- Symbol: `BTCUSD`
- Replay observations: `32`
- CatBoost trained rows: `1120`
- Raw scored mature rows: `1120/30`
- Production validation rows: `1120/30`
- Observation validation rows: `32/30`
- Pre-Bayes confidence: `0.7873539660614577`
- Execution status: `execution_blocked` / `execution_blocked` / `observe`
- Promotion allowed: `false`

## Gate Matrix

| Gate | Status | Evidence |
|---|---|---|
| `commands_zero` | `pass` | exit_count=11 nonzero=[] |
| `replay_observations_min30` | `pass` | observations=32 |
| `catboost_trained_rows_min30` | `pass` | trained_rows=1120 |
| `path_ranker_runtime_ready` | `pass` | Ranker runtime: structural_path_ranking_target rows=1 history_rows=1130 mature_rows=1 history_mature_rows=1120 raw_scored_mature=1120/30 production_validation=1120/30 observation_validation=32/30 calibration=evaluated trainer_artifact=ready trainer_status=runtime_eligible runtime_selection=enabled_candidate_set_ready runtime_mode=candidate_set_only runtime_source=candidate_set score_model_family=catboost score_source=external_model runtime_matches=1 |
| `raw_scored_mature_min30` | `pass` | raw_scored_mature=1120/30 |
| `production_validation_min30` | `pass` | production_validation=1120/30 |
| `observation_validation_min30` | `pass` | observation_validation=32/30 |
| `current_pre_bayes_confidence_95` | `fail_closed` | confidence=0.7873539660614577 |
| `every_regime_95` | `fail_closed` | probabilities={'range': 1.0, 'stress': 0.0, 'transition': 0.0, 'trend': 0.0} |
| `independent_cross_market_validation` | `fail_closed` | replay used BTCUSD from the 172142 YF 1h candle file only |
| `independent_cross_timeframe_validation` | `fail_closed` | replay windows were generated from the same 1h source and passed as ltf/mtf/htf |
| `execution_tree_non_observe` | `fail_closed` | actionable=False ready=False gate=execution_blocked review=observe |
| `path_probability_95` | `fail_closed` | path_prob=0.3125 lower_bound=0.21821371337170056 |

## Readback

The replay produced enough structural-feedback observations and the CatBoost/path-ranker validation floor is now ready in this isolated BTCUSD replay state.

Board A still fails closed because the current Pre-Bayes confidence is below `0.95`, the evidence covers only the replayed BTCUSD/YF 1h source, not independent cross-market/cross-timeframe validation, and the execution candidate remains `execution_blocked` / `observe`.

Do not promote Board A from this packet.
