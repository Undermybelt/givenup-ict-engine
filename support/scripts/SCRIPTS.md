# ICT Engine Script Guide

This file classifies `support/scripts/**` so consumers and contributors can tell
stable helpers from research or local-operator utilities. It is descriptive
governance only; no script was moved or promoted by this document.

## Public Smoke And CI Helpers

| Path | Stability | Safe default | Verification |
|---|---|---|---|
| `support/scripts/smoke_acceptance.sh` | stable first-run smoke | yes, writes under `/tmp` by default; set `ICT_ENGINE_BIN=/path/to/ict-engine` to reuse an already-built binary instead of repeated `cargo run` probes | `bash -n support/scripts/smoke_acceptance.sh`; run script |
| `support/scripts/ci/check_docs_runtime_isolation.py` | CI guard | yes, read-only | CI / direct Python run |
| `support/scripts/help_audit.py` | audit helper | yes, read-only cargo help probes | `python3 support/scripts/help_audit.py` |
| `support/scripts/done_definition_audit.py` | audit helper | yes, lightweight read-only checks by default; `--compact` emits token-friendly JSON without repo-local absolute paths, marks skipped-heavy evidence as not completion-ready, preserves pass-state source debt, fails closed when unsafe practical-admission wrappers remain, surfaces await-launch wrappers that check `live_factor_processes` without active/fresh claim guards, and externalizes untracked fixed-bps cost-model debt without treating it as real-cost proof | `python3 -m unittest support.scripts.tests.test_done_definition_audit -v` |
| `support/scripts/release_readiness_audit.py` | audit helper | yes, read-only local checks; remote readback opt-in; `--compact` omits repo-local absolute paths | `python3 -m unittest support.scripts.tests.test_release_readiness_audit -v` |
| `support/scripts/release_privacy_audit.py` | audit helper | yes, read-only export-tree private path/secret classifier; `--compact` emits token-friendly JSON and separates release-blocking hits from tests/policy/historical docs | `python3 -m unittest support.scripts.tests.test_release_privacy_audit -v` |
| `support/scripts/factor_claim_terminalization_audit.py` | audit helper | yes, read-only `/tmp` claim scanner; `--compact` emits token-friendly attention summaries and grouped counts, recognizes terminal run-root summaries plus terminal claim `write_surface` workdocs, ignores diagnostic `tomac_*_probe/_audit/_diag*` helpers when classifying live factor processes, and supports `--portable-paths` for packet-safe `/tmp` / `/private/tmp` path labels | `python3 -m unittest support.scripts.tests.test_factor_claim_terminalization_audit -v` |
| `support/scripts/objective_closure_snapshot.py` | audit helper | yes, read-only aggregator for done-definition, factor-closure, and release-readiness; can optionally persist one coordinated `/tmp` evidence bundle via `--output-dir` | `python3 -m unittest support.scripts.tests.test_objective_closure_snapshot -v` |
| `support/scripts/check_factor_truth_map.py` | docs guard | yes, read-only | `python3 support/scripts/check_factor_truth_map.py` |
| `support/scripts/check_script_manifest.py` | docs guard | yes, read-only | `python3 support/scripts/check_script_manifest.py` |
| `support/scripts/script_manifest.json` | machine-readable manifest | yes, read-only data | checked by `check_script_manifest.py` |

## Public Wrappers And Read-Only Utilities

| Path | Stability | Safe default | Notes |
|---|---|---|---|
| `support/scripts/search_local.py` | public wrapper | yes, shows help unless `--run` is passed | Refuses execution without a ready cleaned-data root |
| `support/scripts/search_cluster.py` | public wrapper | yes, shows help unless `--run` is passed | Refuses execution without a ready cleaned-data root |
| `support/scripts/evaluate_bottleneck.py` | public wrapper | yes, shows help unless `--run` is passed | Refuses execution without a ready cleaned-data root |
| `support/scripts/research_verdict.py` | read-only utility | yes, requires explicit paths | Emits compact JSON from result/state directories |
| `support/scripts/research/market_data_resolver.py` | read-only adoption utility | yes, requires explicit output path | Resolves generic zero-config market data lanes and optional profile selectors |
| `support/scripts/research/external_history_adoption.py` | adoption utility | yes, requires explicit input/output paths | Emits zero-config default commands plus opt-in profile reuse commands |
| `support/scripts/research/event_fundamentals_adoption.py` | adoption utility | yes, requires explicit input/output paths | Emits zero-config default commands plus opt-in event/fundamentals sidecar reuse commands |
| `support/scripts/research/factor_candidate_resolver.py` | adoption utility | yes, read-only list/verify modes are safe; writes still require explicit output path | Lists/builds explicit factor candidate packs without reading board docs; can also audit repo-native pack contract drift and backfill `pack_manifest.json` into example packs |
| `support/scripts/research/regime_factor_tree_normalizer.py` | read-only utility | yes, requires explicit metrics JSON paths | Normalizes legacy branch paths into `main_regime -> sub_regime -> profit_factor` trees and moves provider/market labels into provenance fields |
| `support/scripts/research/regime_branch_grammar_check.py` | read-only utility | yes, requires explicit metrics JSON paths | Fails Board B branch paths that do not start at the canonical main regime or that attach a regime segment after profit-factor overlays have started |
| `support/scripts/research/regime_root_survivor_blocker_report.py` | read-only utility | yes, requires explicit Gate 1/downstream artifact paths | Builds a compact blocker report for a real-cost survivor and classifies whether the next repair is MTF alignment, PDA evidence, execution admission, or a fresh factor rotation |
| `support/scripts/research/regime_root_metrics_contract_check.py` | read-only utility | yes, requires explicit metrics JSON paths | Fails stored Board B metrics whose `branch_path` is not canonical regime-rooted or whose downstream gates open without verified real/instrument-cost survival |
| `support/scripts/research/instrument_cost_model.py` | helper library | yes, import-only; no writes | Canonical verified futures instrument-cost helper; exposes per-contract IBKR cost profiles, USD-to-return conversion, fail-closed promotion checks, and no fixed-bps futures cost authority |
| `support/scripts/research/futures_bps_false_negative_revival.py` | read-only utility | yes, requires explicit artifact files or directories | Scans historical futures Gate-1/AQ artifacts for rows wrongly killed by retired fixed-bps stress; can write full rows plus a deduped `--output-unique-csv` rehearing queue while carrying session/RTH/density/year evidence forward |
| `support/scripts/research/futures_real_cost_rescue_audit.py` | read-only utility | yes, requires explicit CSV/JSON artifact paths | Normalizes futures rows into `rescued_for_exact_aq`, `fee_cleared_but_blocked_non_cost`, `needs_reprice_replay`, or non-rescue classes when legacy fixed-bps stress fields disagree with verified instrument-cost evidence; `--priority-csv` writes a no-promotion exact-recheck queue, while sample and density gates stay separate from fee survival |
| `support/scripts/research/fixed_bps_cost_model_source_check.py` | read-only utility | yes, scans source only | Fails source files that emit fixed-bps transaction-cost arguments, fields, or formulas; `--tracked` also reports tracked vs active-untracked debt so current authority can fail closed while legacy untracked debt stays visible but non-promotional |
| `support/scripts/research/ibkr_execution_readback.py` | read-only utility | yes, reads local IBKR `reqExecutions` only and writes caller-provided JSON | Captures paper/live broker execution and commissionReport evidence for accepted-feedback preflight; never places orders and leaves practical flags false |
| `support/scripts/research/same_tree_practical_closure.py` | helper library | yes, import-only; writes only to caller-provided packet path | Canonical builder/validator for `same-tree-practical-closure/v1`; wrappers should use this instead of hand-writing practical closure packets |
| `support/scripts/research/downstream_practical_admission_source_check.py` | read-only utility | yes, accepts explicit Python wrapper paths, `--files-from`, or `--tracked-run-wrappers` | Fails downstream wrappers that assign `promotion_allowed`, `trade_usable`, or `update_goal` from local admission variables instead of `practical_admission_flags(..., extension_complete=...)` |
| `support/scripts/research/tomac_strategy_inventory.py` | read-only utility | yes, requires explicit TOMAC root and output path | Inventories local TOMAC Python strategy/scan files into structured family, symbol, timeframe, indicator, class, and branch-hint rows; this is source organization evidence, not practical trading proof |
| `support/scripts/research/tomac_factor_coverage_matrix.py` | read-only utility | yes, requires explicit TOMAC root, claims dir, and output paths | Combines TOMAC inventory rows with active Board B claims to show claimed vs available branch families; use for coordination and residue cleanup, not promotion |

## Active External Bridge

| Path | Stability | Safe default | Notes |
|---|---|---|---|
| `support/scripts/auto_quant_external/pandas_path_ranker_trainer.py` | active bridge contract | requires explicit input/output paths | External path-ranker training/scoring helper |
| `support/scripts/auto_quant_external/path_ranker_integration.py` | active bridge contract | requires explicit state/artifact paths | Rust/Python ranker integration helper |
| `support/scripts/auto_quant_external/structural_feedback_replay_harness.py` | active bridge contract | requires explicit state paths | Replay and feedback validation helper |
| `support/scripts/auto_quant_external/tomac_parquet_to_feather.py` | active bridge contract | requires explicit input/output paths | Converts retained TOMAC parquet cache into Auto-Quant/FreqTrade feather files without launching backtests |
| `support/scripts/auto_quant_external/tests/**` | test support | yes | Prefer `python3 -m unittest ...` if `pytest` is absent |

## Provider And Operator Bridges

| Path | Stability | Safe default | Notes |
|---|---|---|---|
| `support/scripts/ibkr_bridge/**` | opt-in operator bridge | no, requires local runtime/account context | Do not run against live broker context without explicit operator intent |
| `support/scripts/auto_quant_external/fetch_external.py` | opt-in data fetch bridge | network/provider dependent | Use only with explicit provider/source intent; includes `ibkr-contract-details` for no-historical-fetch IBKR secdef preflight |
| `support/scripts/research/pandas_datareader_hotplug.py` | optional hotplug bridge | dependency/network dependent | Not required for zero-config Rust CLI use |

## Research Helpers

| Path | Stability | Safe default | Notes |
|---|---|---|---|
| `support/scripts/research/**` | active research/prototype helpers | varies by script | Inspect arguments and expected inputs before running |
| `support/scripts/auto_quant_external/pandas_*.py` | research/backtest prototypes unless named above | varies by script | Treat outputs as research evidence, not product gates |
| `support/scripts/*bbn*.py`, `support/scripts/*tomac*.py`, `support/scripts/btc_ledger_*.py` | legacy/research utilities | varies by script | Use only when a plan references the exact script |

## Archived Scripts

| Path | Stability | Safe default | Notes |
|---|---|---|---|
| `support/scripts/archive/**` | archived | no product dependency | Do not build new flows on archived scripts |
| `support/scripts/__pycache__/**` | generated cache | not a script surface | Do not cite as evidence |

## Rules For New Scripts

- Put public, user-facing smoke or CI helpers at `support/scripts/`.
- Put active external trainer/bridge helpers under
  `support/scripts/auto_quant_external/`.
- Put exploratory analysis under `support/scripts/research/`.
- Put retired experiments under `support/scripts/archive/`.
- Default to help/read-only behavior unless the command name and arguments make
  writes or network access explicit.
- Accept explicit input/output paths; do not assume maintainer-local paths.
- Write generated state under `/tmp` by default.
- Add a test command or smoke command to this file when adding a new public
  helper.
- Add or update `support/scripts/script_manifest.json` and run
  `python3 support/scripts/check_script_manifest.py` when changing public script
  surfaces.
- Keep heavy compile/lint/test smoke checks opt-in behind explicit flags/env;
  public audit helpers should default to low-cost read-only probes.
