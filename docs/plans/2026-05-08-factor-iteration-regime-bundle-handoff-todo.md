# 2026-05-08 Factor Iteration Regime Bundle Handoff Todo

## TaskIntentDraft

- Continue `docs/plans/2026-05-08-factor-iteration-filter-belief-catboost-execution-tree-board.md`.
- Keep the public surface zero-config and consumer-usable.
- Make user-specific regime benchmark evidence opt-in and hot-pluggable rather than default-coupled.
- Stay inside additive factor-iteration helper artifacts; do not reopen runtime ingestion.

## BaselineReadSetHint

- `docs/plans/2026-05-08-factor-iteration-filter-belief-catboost-execution-tree-board.md`
- `docs/factor-artifact-naming-contract.md`
- `config/factor_candidate_harness_presets.json`
- `examples/factor_candidate_profiles/thrill3r-nq-auto-quant-v1.json`
- `scripts/research/factor_candidate_resolver.py`
- `scripts/research/regime_artifact_bundle.py`

## ImpactStatementDraft

- The remaining gap is not factor-pack plumbing for execution candidates.
- The remaining gap is the regime-only lane: it needs a real artifact path that can reuse personal benchmark JSONs when explicitly selected, while the generic registry stays clean and reusable.

## TodoCheckpointDraft

- Current todo:
  - [x] Audit the board, resolver, preset, profile, and existing regime bundle script.
  - [x] Move concrete regime benchmark paths out of the generic preset surface.
  - [x] Teach resolver/build flow to emit regime artifact bundles from benchmark JSON inputs.
  - [x] Verify generic zero-config vs opt-in profile behavior with real commands.
  - [x] Update the authoritative board with verified regime-lane status.
  - [x] Make corrupted `freqtrade` reusable inputs fail closed instead of crashing the build flow.
  - [x] Continue the Family A breadth lane with one more real explicit candidate pack.
  - [x] Continue the Family A breadth lane with the first 5m timeframe-coverage pack.
  - [x] Continue the Family A breadth lane with the historical 15m and 1d-regime lanes.
  - [x] Continue the Family A breadth lane with the historical 1m lane.
  - [ ] Continue the Family A breadth lane with the next still-missing variant.
- Active slice:
  - regime bundle slice complete; next live slice is Family A breadth continuation
- Completed todos:
  - routing complete
  - isolated worktree selected
  - existing branch drift audited before edits
  - generic regime preset de-personalized
  - opt-in profile restored as the only owner of local benchmark JSON paths
  - resolver now emits regime artifact bundles from benchmark JSON inputs
  - board writeback complete
  - zip integrity now gates `artifact_ready` for `freqtrade_backtest_zip`
  - `family_a_fvg_retrace_1h_v1` is now a real profile-backed candidate pack, not a board-only idea
  - `family_a_fvg_retrace_5m_v1` is now a real profile-backed candidate pack, not a board-only idea
  - `strategy_library_json` is now a supported reusable input kind for old explicit evidence
  - `family_a_killzone_breakout_15m_v1` and `family_a_killzone_breakout_1d_regime_v1` are now real profile-backed candidate packs, not board-only notes
  - `family_a_killzone_breakout_1m_v1` is now a real profile-backed candidate pack, not a board-only note
- Next step:
  - choose the next still-missing Family A breadth variant that is not yet explicit in the registry, then either recover its historical artifact or generate fresh reusable evidence; current explicit Family A timeframe coverage is now `1m`, `5m`, `15m`, `1h`, plus a `1d` regime-filter lane

## EvidenceBundleDraft

- `git status` in isolated worktree already showed this line owns:
  - `config/factor_candidate_harness_presets.json`
  - `scripts/research/regime_artifact_bundle.py`
  - `scripts/research/tests/test_regime_artifact_bundle.py`
- Real local regime benchmark JSONs currently exist under:
  - `/tmp/ict-engine-ibkr-probe/regime_factor_benchmark.*.json`
- Focused verification now completed:
  - `python3 -m unittest scripts.research.tests.test_regime_artifact_bundle scripts.research.tests.test_factor_candidate_resolver`
  - generic resolver run:
    - `python3 scripts/research/factor_candidate_resolver.py --repo-root . --output-dir /tmp/ict-engine-factor-candidate-registry-generic-20260508`
    - result: `selection_mode=generic_zero_config`, `buildable_count=0`, `built_pack_count=0`
  - opt-in resolver run:
    - `python3 scripts/research/factor_candidate_resolver.py --repo-root . --profile thrill3r_nq_auto_quant_v1 --build-packs --output-dir /tmp/ict-engine-factor-candidate-registry-profile-20260508`
    - result: `selection_mode=profile_opt_in`, `buildable_count=6`, `built_pack_count=6`
  - generated regime bundle snapshot:
    - `covered_markets=NQ,SPY,QQQ,GLD`
    - `best_market=GLD`
    - `best_eval_macro_f1=0.478629`
    - `average_eval_macro_f1=0.448097`
    - `best_transition_f1=0.074074`
  - new negative-path verification:
    - `python3 -m unittest scripts.research.tests.test_factor_candidate_resolver.FactorCandidateResolverTests.test_build_candidate_registry_marks_invalid_freqtrade_zip_unbuildable`
    - `python3 -m unittest scripts.research.tests.test_factor_candidate_resolver.FactorCandidateResolverTests.test_build_candidate_packs_skips_invalid_freqtrade_zip`
    - both now pass
  - real local proof point:
    - `/Users/thrill3r/Auto-Quant/user_data/backtest_results/backtest-result-2026-05-08_23-11-33.zip` fails `unzip -t`
    - this file would previously be misclassified as buildable; now it would be surfaced as `invalid_artifact:...`
  - Family A breadth inventory check:
    - scanned local `Auto-Quant/user_data/backtest_results/*.zip` for:
      - `TomacNQKillzoneBreakout5m`
      - `TomacNQKillzoneBreakout15m`
      - `TomacNQ_KillzoneBreakout1dRegime`
      - `TomacNQ_RegimeFVGRetrace`
      - `TomacNQ_RegimeFVGRetrace5m`
    - current result: no valid reusable backtest zips found for those variants
    - implication: the next Family A breadth slice is evidence-generation first, not registry-only bookkeeping
  - New Family A breadth evidence generated this turn:
    - `TomacNQ_RegimeFVGRetrace` base `NQ/USD` 8Y run:
      - command: `uv run --with ta-lib python .../run_tomac_one.py TomacNQ_RegimeFVGRetrace 1h /tmp/ict-engine-family-a-fvg-retrace-nq-export.json NQ/USD 20180101-20251231`
      - result: `12` trades, `sharpe=0.015`, `profit_factor=1.92`, `total_profit_pct=0.57`
      - reusable zip: `backtest-result-2026-05-08_23-46-20.zip`
    - `TomacNQ_RegimeFVGRetrace` cross-market 1Y run:
      - command: `uv run --with ta-lib python .../run_tomac_one.py TomacNQ_RegimeFVGRetrace 1h /tmp/ict-engine-family-a-fvg-retrace-cross-export.json SPY/USD,IWM/USD,GLD/USD 20250507-20251231`
      - result: `23` trades aggregate, `sharpe=0.075`, `profit_factor=1.10`
      - per-market:
        - `SPY/USD`: `11` trades, `sharpe=0.377`, `profit_factor=2.68`
        - `IWM/USD`: `2` trades, anecdotal
        - `GLD/USD`: `10` trades, `sharpe=-0.195`, `profit_factor=0.58`
      - reusable zip: `backtest-result-2026-05-08_23-47-45.zip`
    - registry/profile were updated and resolver now emits `family_a_fvg_retrace_1h_v1`
    - `TomacNQ_RegimeFVGRetrace5m` base `NQ/USD` 8Y run:
      - command: `uv run --with ta-lib python .../run_tomac_one.py TomacNQ_RegimeFVGRetrace5m 5m /tmp/ict-engine-family-a-fvg-retrace-5m-nq-export.json NQ/USD 20180101-20251231`
      - result: `82` trades, `aggregate_label=preferred_density`, `sharpe=-0.0199`, `profit_factor=0.8399`, `total_profit_pct=-0.47`
      - reusable zip: `backtest-result-2026-05-08_23-55-11.zip`
    - registry/profile were updated and resolver now emits `family_a_fvg_retrace_5m_v1`
  - Historical Family A strategy-library artifacts recovered this turn:
    - `strategy_library_json` reusable-input support added to resolver
    - `TomacNQKillzoneBreakout15m`
      - source artifact: `/tmp/ict-engine-family-a-nq-15m-profile/.deps/auto-quant/strategy_library_15m.json`
      - result: `22` trades, `aggregate_label=probe_only`, `sharpe=0.0746`, `profit_factor=1.1272`
      - registry/profile now emit `family_a_killzone_breakout_15m_v1`
    - `TomacNQ_KillzoneBreakout1dRegime`
      - source artifact: `/tmp/ict-engine-family-a-profile-1dregime-check/.deps/auto-quant/strategy_library_round3.json`
      - result: `2` trades, `aggregate_label=anecdotal`, `sharpe=0.4468`, `total_profit_pct=2.26`
      - registry/profile now emit `family_a_killzone_breakout_1d_regime_v1`
    - `TomacNQKillzoneBreakout1m`
      - source artifact: `/tmp/ict-engine-family-a-nq-1m-profile/.deps/auto-quant/strategy_library_1m.json`
      - result: `56` trades, `aggregate_label=thin`, `sharpe=-0.3518`, `profit_factor=0.6742`, `total_profit_pct=-8.2`
      - registry/profile now emit `family_a_killzone_breakout_1m_v1`

## DriftCheckDraft

- Scope:
  - still inside factor-iteration helper artifacts only
- Compatibility:
  - public default surface stays generic
  - personal data remains opt-in
- Retirement:
  - no new runtime fallback or compatibility alias introduced
- Decision:
  - continue
  - next safe action is still factor-iteration only; runtime closure remains out of scope

## ResumeStateHint

- Re-read this handoff todo plus the board before further edits.
- Re-run resolver in both modes:
  - generic zero-config
  - `--profile thrill3r_nq_auto_quant_v1 --build-packs`
- If the generic path still exposes concrete `/tmp` benchmark JSONs, the slice regressed.
- If a future profile selects a broken backtest zip, the lane must stay
  `artifact_ready=false`; do not "fix" this by catching the crash later in pack
  construction.
- If starting the next slice, begin from Family A breadth evidence generation rather than reopening the regime lane unless new shared benchmark artifacts appear.
- `family_a_fvg_retrace_1h_v1` already exists now; do not regenerate the same pack unless the underlying reusable zips are replaced.
- `family_a_fvg_retrace_5m_v1` already exists now; do not regenerate the same pack unless the underlying reusable zip is replaced.
- `family_a_killzone_breakout_15m_v1` and `family_a_killzone_breakout_1d_regime_v1` now exist; prefer fresh cross-market evidence or another missing variant instead of re-ingesting the same historical manifests again.
- `family_a_killzone_breakout_1m_v1` now exists; prefer another missing Family A variant over re-ingesting the same historical manifest again.
