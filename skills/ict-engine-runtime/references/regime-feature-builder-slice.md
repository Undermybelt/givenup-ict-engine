# Regime feature builder slice

Use when continuing high-confidence regime classifier work after ontology manifest (R2), especially Slice R3 / feature-builder sidecars.

Files added in repo:
- `scripts/research/regime_feature_builder.py`
- `scripts/research/tests/test_regime_feature_builder.py`

Contract:
- Input: OHLCV CSV or JSONL via `--ohlcv`.
- Optional input: auxiliary evidence JSONL via `--auxiliary-evidence`.
- Optional input: MTF PDA events JSONL via `--mtf-pda-events`.
- Output: feature table CSV via `--output-features`.
- Output: `feature_quality_report.json` via `--output-report`.

Required behavior:
- Zero-config OHLCV-only run must succeed.
- Missing optional inputs must not fail; report marks them `missing`.
- User VRP/NQ auxiliary fields pass through by timestamp:
  - `qqq_hv_level`
  - `nq_vs_200d_pct`
  - `vix3m_level`
  - `qqq_hv_pct_rank_252`
  - `vvix_over_vix`
- MTF rows can override/join:
  - `mtf_alignment`
  - `pda_event_count`

Current feature groups emitted:
- price geometry: return, range, body/wicks, range position
- volatility: ATR, ATR percentile, realized vol
- liquidity: volume percentile
- structure/proxy trend: directional efficiency, slope
- behavior/crowding proxy: RSI
- MTF resonance: alignment and PDA count
- report lists all feature groups, including future `distribution_shape` and `transition_history`

TDD / verification:
```bash
python3 -m unittest scripts/research/tests/test_regime_feature_builder.py -v
python3 -m unittest discover -s scripts/research/tests -p 'test_*.py'
```
Expected after R3: target tests 4 OK; research tests 61 OK.

Reporting pitfall:
- When RED fails because module is missing, immediately create the module and rerun tests before final response.
- Final summary should say the file is already created and verified, not just that RED failed.
